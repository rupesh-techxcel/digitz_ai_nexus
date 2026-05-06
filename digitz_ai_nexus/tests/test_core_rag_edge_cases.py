import json
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from digitz_ai_nexus.engine.access import can_access_policy
from digitz_ai_nexus.engine.prompt import SAFE_FALLBACK_ANSWER, build_prompt
from digitz_ai_nexus.engine.retrieval import retrieve_allowed_chunks


class TestNexusCoreRAGEdgeCases(FrappeTestCase):
    TENANT = "TEST-NEXUS-EDGE"
    BUSINESS_UNIT = "ERP Product"
    OTHER_BUSINESS_UNIT = "Other Product"

    def setUp(self):
        self.create_tenant()
        self.create_policies()
        self.create_units_and_chunks()

    def create_tenant(self):
        if frappe.db.exists("Nexus Tenant", self.TENANT):
            doc = frappe.get_doc("Nexus Tenant", self.TENANT)
        else:
            doc = frappe.new_doc("Nexus Tenant")
            doc.tenant_code = self.TENANT

        doc.tenant_name = "Test Nexus Edge Tenant"
        doc.disabled = 0
        doc.save(ignore_permissions=True)

    def create_policies(self):
        self.upsert_policy(
            name="TEST_EDGE_PUBLIC",
            access_level="Public",
            sensitivity="public",
            allowed_roles="[]",
            excluded_roles="[]",
            allowed_designations="[]",
            excluded_designations="[]",
            disabled=0,
        )

        self.upsert_policy(
            name="TEST_EDGE_DISABLED",
            access_level="Role Restricted",
            sensitivity="internal",
            allowed_roles='["Accounts Manager"]',
            excluded_roles="[]",
            allowed_designations="[]",
            excluded_designations="[]",
            disabled=1,
        )

        self.upsert_policy(
            name="TEST_EDGE_DENY_WINS",
            access_level="Role Restricted",
            sensitivity="internal",
            allowed_roles='["Accounts Manager"]',
            excluded_roles='["Accounts Manager"]',
            allowed_designations="[]",
            excluded_designations="[]",
            disabled=0,
        )

        self.upsert_policy(
            name="TEST_EDGE_DESIGNATION_ALLOWED",
            access_level="Role Restricted",
            sensitivity="internal",
            allowed_roles="[]",
            excluded_roles="[]",
            allowed_designations='["Finance Head"]',
            excluded_designations="[]",
            disabled=0,
        )

        self.upsert_policy(
            name="TEST_EDGE_DESIGNATION_DENIED",
            access_level="Role Restricted",
            sensitivity="internal",
            allowed_roles="[]",
            excluded_roles="[]",
            allowed_designations='["Finance Head"]',
            excluded_designations='["Finance Head"]',
            disabled=0,
        )

    def upsert_policy(
        self,
        name,
        access_level,
        sensitivity,
        allowed_roles,
        excluded_roles,
        allowed_designations,
        excluded_designations,
        disabled,
    ):
        if frappe.db.exists("Nexus Access Policy", name):
            doc = frappe.get_doc("Nexus Access Policy", name)
        else:
            doc = frappe.new_doc("Nexus Access Policy")
            doc.name = name
            doc.policy_name = name

        doc.access_level = access_level
        doc.sensitivity = sensitivity
        doc.allowed_roles = allowed_roles
        doc.excluded_roles = excluded_roles
        doc.allowed_designations = allowed_designations
        doc.excluded_designations = excluded_designations
        doc.disabled = disabled
        doc.save(ignore_permissions=True)

    def create_units_and_chunks(self):
        unit_general = self.upsert_unit(
            name="TEST-EDGE-UNIT-GENERAL",
            title="TEST EDGE General",
            business_unit=self.BUSINESS_UNIT,
            project="",
            topic="Overview",
            policy="TEST_EDGE_PUBLIC",
            content="DIGITZ ERP is an enterprise resource planning system.",
        )

        unit_other_bu = self.upsert_unit(
            name="TEST-EDGE-UNIT-OTHER-BU",
            title="TEST EDGE Other BU",
            business_unit=self.OTHER_BUSINESS_UNIT,
            project="",
            topic="Overview",
            policy="TEST_EDGE_PUBLIC",
            content="Other Product should not leak into ERP Product retrieval.",
        )

        unit_no_embedding = self.upsert_unit(
            name="TEST-EDGE-UNIT-NO-EMBEDDING",
            title="TEST EDGE No Embedding",
            business_unit=self.BUSINESS_UNIT,
            project="",
            topic="No Embedding",
            policy="TEST_EDGE_PUBLIC",
            content="This chunk intentionally has no embedding.",
        )

        self.general_chunk = self.upsert_chunk(
            name="TEST-EDGE-CHUNK-GENERAL",
            unit=unit_general,
            business_unit=self.BUSINESS_UNIT,
            project="",
            topic="Overview",
            policy="TEST_EDGE_PUBLIC",
            chunk_text="DIGITZ ERP is an enterprise resource planning system.",
            embedding=[1.0, 0.0, 0.0],
        )

        self.upsert_chunk(
            name="TEST-EDGE-CHUNK-OTHER-BU",
            unit=unit_other_bu,
            business_unit=self.OTHER_BUSINESS_UNIT,
            project="",
            topic="Overview",
            policy="TEST_EDGE_PUBLIC",
            chunk_text="Other Product should not leak into ERP Product retrieval.",
            embedding=[1.0, 0.0, 0.0],
        )

        self.upsert_chunk(
            name="TEST-EDGE-CHUNK-NO-EMBEDDING",
            unit=unit_no_embedding,
            business_unit=self.BUSINESS_UNIT,
            project="",
            topic="No Embedding",
            policy="TEST_EDGE_PUBLIC",
            chunk_text="This chunk intentionally has no embedding.",
            embedding=None,
        )

    def upsert_unit(self, name, title, business_unit, project, topic, policy, content):
        if frappe.db.exists("Nexus Knowledge Unit", name):
            doc = frappe.get_doc("Nexus Knowledge Unit", name)
        else:
            doc = frappe.new_doc("Nexus Knowledge Unit")
            doc.name = name

        doc.tenant = self.TENANT
        doc.business_unit = business_unit
        doc.project = project or ""
        doc.title = title
        doc.status = "Active"
        doc.version = 1
        doc.source_type = "Manual"
        doc.content = content
        doc.context = "ERP"
        doc.sub_context = "General"
        doc.entity_type = "Product"
        doc.entity = "DIGITZ ERP"
        doc.topic = topic
        doc.default_access_policy = policy
        doc.sensitivity = "public"
        doc.save(ignore_permissions=True)

        return doc.name

    def upsert_chunk(self, name, unit, business_unit, project, topic, policy, chunk_text, embedding):
        if frappe.db.exists("Nexus Knowledge Chunk", name):
            doc = frappe.get_doc("Nexus Knowledge Chunk", name)
        else:
            doc = frappe.new_doc("Nexus Knowledge Chunk")
            doc.name = name

        doc.knowledge_unit = unit
        doc.tenant = self.TENANT
        doc.business_unit = business_unit
        doc.project = project or ""
        doc.disabled = 0
        doc.chunk_index = 1
        doc.priority = 0
        doc.chunk_text = chunk_text
        doc.chunk_hash = f"{name.lower()}-hash"
        doc.context = "ERP"
        doc.sub_context = "General"
        doc.entity_type = "Product"
        doc.entity = "DIGITZ ERP"
        doc.topic = topic
        doc.context_path = f"ERP/General/Product/DIGITZ ERP/{topic}"
        doc.access_policy = policy
        doc.sensitivity = "public"

        if embedding is None:
            doc.embedding = None
            doc.embedding_status = "Pending"
        else:
            doc.embedding = json.dumps(embedding)
            doc.embedding_status = "Completed"

        doc.embedding_model = "fake-test-model"
        doc.save(ignore_permissions=True)

        return doc.name

    def base_payload(self, topic="Overview", query="What is DIGITZ ERP?", top_k=5):
        return {
            "tenant": self.TENANT,
            "business_unit": self.BUSINESS_UNIT,
            "context": "ERP",
            "sub_context": "General",
            "entity_type": "Product",
            "entity": "DIGITZ ERP",
            "topic": topic,
            "query": query,
            "top_k": top_k,
            "user": {
                "roles": ["Guest"],
            },
        }

    def test_missing_access_policy_is_denied(self):
        allowed, reason = can_access_policy({"roles": ["Guest"]}, None)

        self.assertFalse(allowed)
        self.assertEqual(reason, "Missing access policy")

    def test_disabled_access_policy_is_denied(self):
        allowed, reason = can_access_policy(
            {"roles": ["Accounts Manager"]},
            "TEST_EDGE_DISABLED",
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "Access policy is disabled")

    def test_excluded_role_overrides_allowed_role(self):
        allowed, reason = can_access_policy(
            {"roles": ["Accounts Manager"]},
            "TEST_EDGE_DENY_WINS",
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "Denied by excluded role")

    def test_allowed_designation_is_allowed(self):
        allowed, reason = can_access_policy(
            {
                "roles": [],
                "designation": "Finance Head",
            },
            "TEST_EDGE_DESIGNATION_ALLOWED",
        )

        self.assertTrue(allowed)
        self.assertEqual(reason, "Allowed")

    def test_excluded_designation_overrides_allowed_designation(self):
        allowed, reason = can_access_policy(
            {
                "roles": [],
                "designation": "Finance Head",
            },
            "TEST_EDGE_DESIGNATION_DENIED",
        )

        self.assertFalse(allowed)
        self.assertEqual(reason, "Denied by excluded designation")

    def test_prompt_contains_exact_safe_fallback_instruction(self):
        prompt = build_prompt(
            {
                "query": "Unknown question",
                "use_case": "qa",
            },
            [],
        )

        self.assertIn(SAFE_FALLBACK_ANSWER, prompt)
        self.assertIn("APPROVED KNOWLEDGE:", prompt)
        self.assertIn("USER QUESTION:", prompt)

    def test_prompt_handles_missing_optional_chunk_metadata(self):
        prompt = build_prompt(
            {
                "query": "What is DIGITZ ERP?",
                "use_case": "qa",
            },
            [
                {
                    "chunk_text": "DIGITZ ERP is an enterprise resource planning system.",
                }
            ],
        )

        self.assertIn("DIGITZ ERP is an enterprise resource planning system.", prompt)
        self.assertIn("Chunk ID:", prompt)
        self.assertIn("Context Path:", prompt)
        self.assertIn("Business Unit:", prompt)
        self.assertIn("Project:", prompt)
        self.assertIn("Scope Type:", prompt)

    def test_prompt_does_not_hide_response_mode_when_use_case_is_invalid(self):
        prompt = build_prompt(
            {
                "query": "What is DIGITZ ERP?",
                "use_case": "invalid_mode",
            },
            [],
        )

        self.assertIn("RESPONSE BEHAVIOR:", prompt)
        self.assertIn("Mode:", prompt)
        self.assertIn("Tone:", prompt)
        self.assertIn("Instructions:", prompt)

    def test_empty_query_raises_error(self):
        payload = self.base_payload(query="")

        with self.assertRaises(Exception):
            retrieve_allowed_chunks(payload, query_embedding=[1.0, 0.0, 0.0])

    def test_top_k_limit_is_respected(self):
        payload = self.base_payload(top_k=1)

        res = retrieve_allowed_chunks(payload, query_embedding=[1.0, 0.0, 0.0])

        self.assertLessEqual(len(res["results"]), 1)

    def test_business_unit_isolation_prevents_cross_bu_leakage(self):
        payload = self.base_payload(
            topic="Overview",
            query="What is DIGITZ ERP?",
        )

        res = retrieve_allowed_chunks(payload, query_embedding=[1.0, 0.0, 0.0])

        self.assertGreater(len(res["results"]), 0)

        for row in res["results"]:
            self.assertEqual(row.get("business_unit"), self.BUSINESS_UNIT)
            self.assertNotEqual(row.get("business_unit"), self.OTHER_BUSINESS_UNIT)
            self.assertNotIn("Other Product should not leak", row.get("chunk_text") or "")

    def test_chunk_without_embedding_is_skipped_safely(self):
        payload = self.base_payload(
            topic="No Embedding",
            query="This chunk intentionally has no embedding.",
        )

        res = retrieve_allowed_chunks(payload, query_embedding=[1.0, 0.0, 0.0])

        self.assertEqual(len(res["results"]), 0)

    def test_query_embedding_is_generated_when_not_supplied(self):
        payload = self.base_payload(
            topic="Overview",
            query="What is DIGITZ ERP?",
        )

        with patch(
            "digitz_ai_nexus.engine.retrieval.generate_embedding",
            return_value=[1.0, 0.0, 0.0],
        ) as mocked_generate_embedding:
            res = retrieve_allowed_chunks(payload, query_embedding=None)

        mocked_generate_embedding.assert_called_once()
        self.assertGreater(len(res["results"]), 0)

    def test_retrieval_result_contains_required_metadata(self):
        payload = self.base_payload(
            topic="Overview",
            query="What is DIGITZ ERP?",
        )

        res = retrieve_allowed_chunks(payload, query_embedding=[1.0, 0.0, 0.0])

        self.assertGreater(len(res["results"]), 0)

        row = res["results"][0]

        self.assertIn("chunk", row)
        self.assertIn("chunk_text", row)
        self.assertIn("context_path", row)
        self.assertIn("business_unit", row)
        self.assertIn("project", row)
        self.assertIn("scope_type", row)
        self.assertIn("keyword_score", row)

    def test_results_are_sorted_by_score_when_score_field_exists(self):
        payload = self.base_payload(
            topic="Overview",
            query="What is DIGITZ ERP?",
            top_k=5,
        )

        res = retrieve_allowed_chunks(payload, query_embedding=[1.0, 0.0, 0.0])

        score_keys = [
            "score",
            "final_score",
            "combined_score",
            "similarity_score",
            "vector_score",
        ]

        scores = []

        for row in res["results"]:
            for key in score_keys:
                if key in row:
                    scores.append(row[key])
                    break

        if len(scores) > 1:
            self.assertEqual(scores, sorted(scores, reverse=True))

    def test_tenant_isolation_prevents_cross_tenant_leakage(self):
        payload = self.base_payload(
            topic="Overview",
            query="What is DIGITZ ERP?",
        )

        payload["tenant"] = "NON-EXISTING-TENANT"

        res = retrieve_allowed_chunks(payload, query_embedding=[1.0, 0.0, 0.0])

        self.assertEqual(len(res["results"]), 0)

    def test_disabled_chunk_is_ignored(self):
        chunk = frappe.get_doc("Nexus Knowledge Chunk", self.general_chunk)
        chunk.disabled = 1
        chunk.save(ignore_permissions=True)

        payload = self.base_payload(
            topic="Overview",
            query="What is DIGITZ ERP?",
        )

        res = retrieve_allowed_chunks(payload, query_embedding=[1.0, 0.0, 0.0])

        returned_chunks = {row.get("chunk") for row in res["results"]}

        self.assertNotIn(self.general_chunk, returned_chunks)

        chunk.disabled = 0
        chunk.save(ignore_permissions=True)
      
    