import json

import frappe
from frappe.tests.utils import FrappeTestCase

from digitz_ai_nexus.api.query import ask
from digitz_ai_nexus.engine.retrieval import retrieve_allowed_chunks


class FakeLLMProvider:
    def generate(self, prompt: str):
        return "DIGITZ ERP is an enterprise resource planning system."


class ExplodingLLMProvider:
    def generate(self, prompt: str):
        raise AssertionError("LLM should not be called when no approved context is available.")


class TestNexusCoreRAG(FrappeTestCase):
    BUSINESS_UNIT = "ERP Product"
    TEST_PROJECT = "ABC Implementation"

    def setUp(self):
        self.create_tenant()
        self.create_policies()
        self.create_knowledge_units()
        self.create_chunks()

    def create_tenant(self):
        if frappe.db.exists("Nexus Tenant", "TEST-NEXUS"):
            doc = frappe.get_doc("Nexus Tenant", "TEST-NEXUS")
        else:
            doc = frappe.new_doc("Nexus Tenant")
            doc.tenant_code = "TEST-NEXUS"

        doc.tenant_name = "Test Nexus Tenant"
        doc.disabled = 0
        doc.save(ignore_permissions=True)

    def create_policies(self):
        self.upsert_policy("TEST_PUBLIC", "Public", "public", "[]", "[]", 0)
        self.upsert_policy(
            "TEST_FINANCE_RESTRICTED",
            "Finance Restricted",
            "financial",
            '["Accounts Manager"]',
            '["Sales User"]',
            0,
        )

    def upsert_policy(self, name, access_level, sensitivity, allowed_roles, excluded_roles, disabled):
        if frappe.db.exists("Nexus Access Policy", name):
            doc = frappe.get_doc("Nexus Access Policy", name)
        else:
            doc = frappe.new_doc("Nexus Access Policy")
            doc.policy_name = name
            doc.name = name

        doc.access_level = access_level
        doc.sensitivity = sensitivity
        doc.allowed_roles = allowed_roles
        doc.excluded_roles = excluded_roles
        doc.disabled = disabled
        doc.save(ignore_permissions=True)

    def create_knowledge_units(self):
        self.public_unit = self.upsert_unit(
            name="TEST-NKU-DIGITZ-ERP-OVERVIEW",
            title="TEST DIGITZ ERP Overview",
            topic="Overview",
            policy="TEST_PUBLIC",
            sensitivity="public",
            content="DIGITZ ERP is an enterprise resource planning system.",
            project="",
        )

        self.finance_unit = self.upsert_unit(
            name="TEST-NKU-HIRE-RETURN-VALUATION",
            title="TEST Hire Return Valuation",
            topic="Valuation",
            policy="TEST_FINANCE_RESTRICTED",
            sensitivity="financial",
            content="Hire Return valuation uses internal financial cost rules.",
            project="",
        )

        self.project_unit = self.upsert_unit(
            name="TEST-NKU-ABC-HIRE-RETURN-VALUATION",
            title="TEST ABC Hire Return Valuation",
            topic="Valuation",
            policy="TEST_FINANCE_RESTRICTED",
            sensitivity="financial",
            content="ABC Implementation uses a project-specific Hire Return valuation exception.",
            project=self.TEST_PROJECT,
        )

    def upsert_unit(self, name, title, topic, policy, sensitivity, content, project=None):
        if frappe.db.exists("Nexus Knowledge Unit", name):
            doc = frappe.get_doc("Nexus Knowledge Unit", name)
        else:
            doc = frappe.new_doc("Nexus Knowledge Unit")
            doc.name = name

        doc.tenant = "TEST-NEXUS"
        doc.business_unit = self.BUSINESS_UNIT
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
        doc.sensitivity = sensitivity
        doc.save(ignore_permissions=True)

        return doc.name

    def create_chunks(self):
        self.upsert_chunk(
            name="TEST-NKC-DIGITZ-ERP-OVERVIEW",
            unit=self.public_unit,
            chunk_hash="test-core-rag-digitz-erp-overview",
            chunk_text="DIGITZ ERP is an enterprise resource planning system.",
            topic="Overview",
            policy="TEST_PUBLIC",
            sensitivity="public",
            embedding=[1.0, 0.0, 0.0],
            project="",
        )

        self.upsert_chunk(
            name="TEST-NKC-HIRE-RETURN-VALUATION",
            unit=self.finance_unit,
            chunk_hash="test-core-rag-hire-return-valuation",
            chunk_text="Hire Return valuation uses internal financial cost rules.",
            topic="Valuation",
            policy="TEST_FINANCE_RESTRICTED",
            sensitivity="financial",
            embedding=[0.0, 1.0, 0.0],
            project="",
        )

        self.upsert_chunk(
            name="TEST-NKC-ABC-HIRE-RETURN-VALUATION",
            unit=self.project_unit,
            chunk_hash="test-core-rag-abc-hire-return-valuation",
            chunk_text="ABC Implementation uses a project-specific Hire Return valuation exception.",
            topic="Valuation",
            policy="TEST_FINANCE_RESTRICTED",
            sensitivity="financial",
            embedding=[0.0, 1.0, 0.0],
            project=self.TEST_PROJECT,
        )

    def upsert_chunk(self, name, unit, chunk_hash, chunk_text, topic, policy, sensitivity, embedding, project=None):
        if frappe.db.exists("Nexus Knowledge Chunk", name):
            doc = frappe.get_doc("Nexus Knowledge Chunk", name)
        else:
            doc = frappe.new_doc("Nexus Knowledge Chunk")
            doc.name = name

        doc.knowledge_unit = unit
        doc.tenant = "TEST-NEXUS"
        doc.business_unit = self.BUSINESS_UNIT
        doc.project = project or ""
        doc.disabled = 0
        doc.chunk_index = 1
        doc.priority = 0
        doc.chunk_text = chunk_text
        doc.chunk_hash = chunk_hash
        doc.context = "ERP"
        doc.sub_context = "General"
        doc.entity_type = "Product"
        doc.entity = "DIGITZ ERP"
        doc.topic = topic
        doc.context_path = f"ERP/General/Product/DIGITZ ERP/{topic}"
        doc.access_policy = policy
        doc.sensitivity = sensitivity
        doc.embedding = json.dumps(embedding)
        doc.embedding_model = "fake-test-model"
        doc.embedding_status = "Completed"
        doc.save(ignore_permissions=True)

        return doc.name

    def test_public_knowledge_is_retrieved_by_guest(self):
        payload = self.base_payload(topic="Overview", query="What is DIGITZ ERP?", roles=["Guest"])

        res = retrieve_allowed_chunks(payload, query_embedding=[1.0, 0.0, 0.0])

        self.assertEqual(res["retrieval_mode"], "hybrid_grounded_rag")
        self.assertGreater(len(res["results"]), 0)
        self.assertEqual(res["results"][0]["context_path"], "ERP/General/Product/DIGITZ ERP/Overview")
        self.assertEqual(res["results"][0]["business_unit"], self.BUSINESS_UNIT)
        self.assertGreater(res["results"][0]["keyword_score"], 0)

    def test_restricted_knowledge_is_denied_for_sales_user(self):
        payload = self.base_payload(topic="Valuation", query="Hire Return valuation", roles=["Sales User"])

        res = retrieve_allowed_chunks(payload, query_embedding=[0.0, 1.0, 0.0])

        self.assertEqual(len(res["results"]), 0)
        self.assertGreater(res["denied_count"], 0)

    def test_restricted_knowledge_is_allowed_for_accounts_manager(self):
        payload = self.base_payload(topic="Valuation", query="Hire Return valuation", roles=["Accounts Manager"])

        res = retrieve_allowed_chunks(payload, query_embedding=[0.0, 1.0, 0.0])

        self.assertGreater(len(res["results"]), 0)
        self.assertEqual(res["results"][0]["context_path"], "ERP/General/Product/DIGITZ ERP/Valuation")

    def test_project_with_general_fallback_does_not_leak_other_projects(self):
        payload = self.base_payload(
            topic="Valuation",
            query="Hire Return valuation",
            roles=["Accounts Manager"],
            project=self.TEST_PROJECT,
            project_scope_mode="with_general",
        )

        payload["top_k"] = 10

        res = retrieve_allowed_chunks(payload, query_embedding=[0.0, 1.0, 0.0])

        self.assertGreater(len(res["results"]), 0)

        for row in res["results"]:
            self.assertIn(row.get("project") or "", ["", self.TEST_PROJECT])

    def test_project_strict_returns_only_project_chunks(self):
        payload = self.base_payload(
            topic="Valuation",
            query="Hire Return valuation",
            roles=["Accounts Manager"],
            project=self.TEST_PROJECT,
            project_scope_mode="strict",
        )

        res = retrieve_allowed_chunks(payload, query_embedding=[0.0, 1.0, 0.0])

        self.assertGreater(len(res["results"]), 0)

        for row in res["results"]:
            self.assertEqual(row.get("project"), self.TEST_PROJECT)
            self.assertEqual(row.get("scope_type"), "project")

    def test_ask_api_returns_structured_response_without_real_llm(self):
        payload = self.base_payload(
            topic="Overview",
            query="What is DIGITZ ERP?",
            roles=["Guest"],
            caller_system="Unit Test",
            use_case="qa",
            user_id="unit-test-user",
        )

        res = ask(
            payload,
            llm_provider=FakeLLMProvider(),
            retrieval_fn=lambda payload, embedding_provider=None: retrieve_allowed_chunks(
                payload,
                query_embedding=[1.0, 0.0, 0.0],
            ),
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["access_status"], "allowed")
        self.assertIn("DIGITZ ERP", res["answer"])
        self.assertGreater(len(res["sources"]), 0)
        self.assertEqual(res["sources"][0]["business_unit"], self.BUSINESS_UNIT)
        self.assertTrue(frappe.db.exists("Nexus Query Log", res["log"]))

    def test_no_context_returns_safe_fallback(self):
        payload = self.base_payload(
            topic="Missing Topic",
            query="Unknown question",
            roles=["Guest"],
            caller_system="Unit Test",
            use_case="qa",
            user_id="unit-test-user",
        )

        res = ask(
            payload,
            llm_provider=FakeLLMProvider(),
            retrieval_fn=lambda payload, embedding_provider=None: {
                "results": [],
                "denied": [],
                "candidate_count": 0,
                "allowed_count": 0,
                "denied_count": 0,
                "retrieval_mode": "hybrid_grounded_rag",
            },
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["access_status"], "no_context")
        self.assertIn("not have enough approved knowledge", res["answer"])
        self.assertEqual(len(res["sources"]), 0)

    def test_prompt_changes_by_response_mode(self):
        from digitz_ai_nexus.engine.prompt import build_prompt

        chunks = [
            {
                "chunk": "TEST-CHUNK",
                "context_path": "ERP/General/Product/DIGITZ ERP/Overview",
                "business_unit": self.BUSINESS_UNIT,
                "project": "",
                "scope_type": "general",
                "chunk_text": "DIGITZ ERP is an enterprise resource planning system.",
            }
        ]

        qa_prompt = build_prompt(
            {
                "query": "What is DIGITZ ERP?",
                "use_case": "qa",
            },
            chunks,
        )

        chat_prompt = build_prompt(
            {
                "query": "What is DIGITZ ERP?",
                "use_case": "chat",
            },
            chunks,
        )

        self.assertIn("Q&A", qa_prompt)
        self.assertIn("Chatbot", chat_prompt)
        self.assertNotEqual(qa_prompt, chat_prompt)

    def test_no_context_does_not_call_llm(self):
        payload = self.base_payload(
            topic="Missing Topic",
            query="Unknown question",
            roles=["Guest"],
            caller_system="Unit Test",
            use_case="qa",
            user_id="unit-test-user",
        )

        res = ask(
            payload,
            llm_provider=ExplodingLLMProvider(),
            retrieval_fn=lambda payload, embedding_provider=None: {
                "results": [],
                "denied": [],
                "candidate_count": 0,
                "allowed_count": 0,
                "denied_count": 0,
                "retrieval_mode": "hybrid_grounded_rag",
            },
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["access_status"], "no_context")
        self.assertIn("not have enough approved knowledge", res["answer"])
        self.assertEqual(len(res["sources"]), 0)

    def base_payload(
        self,
        topic,
        query,
        roles,
        caller_system=None,
        use_case=None,
        user_id=None,
        project=None,
        project_scope_mode=None,
    ):
        payload = {
            "tenant": "TEST-NEXUS",
            "business_unit": self.BUSINESS_UNIT,
            "context": "ERP",
            "sub_context": "General",
            "entity_type": "Product",
            "entity": "DIGITZ ERP",
            "topic": topic,
            "query": query,
            "top_k": 5,
            "user": {
                "roles": roles,
            },
        }

        if project:
            payload["project"] = project

        if project_scope_mode:
            payload["project_scope_mode"] = project_scope_mode

        if caller_system:
            payload["caller_system"] = caller_system

        if use_case:
            payload["use_case"] = use_case

        if user_id:
            payload["user"]["user_id"] = user_id

        return payload