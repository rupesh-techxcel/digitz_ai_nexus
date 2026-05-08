import json
import unittest
from unittest.mock import patch

import frappe

from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source
from digitz_ai_nexus.engine.retrieval import retrieve_allowed_chunks


TEST_EMBEDDING_JSON = "[0.0, 1.0, 0.0]"
TEST_QUERY_EMBEDDING = [0.0, 1.0, 0.0]


def set_if_field(doc, fieldname, value):
    if value is None:
        return

    if not doc.meta.has_field(fieldname):
        return

    table_columns = frappe.db.get_table_columns(doc.doctype)

    if fieldname not in table_columns:
        return

    doc.set(fieldname, value)


def extract_result_chunks(result):
    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        return (
            result.get("chunks")
            or result.get("allowed_chunks")
            or result.get("retrieved_chunks")
            or result.get("sources")
            or result.get("results")
            or result.get("data")
            or []
        )

    return []


def row_chunk_name(row):
    return row.get("name") or row.get("chunk") or row.get("chunk_name")


class TestIngestedRetrieval(unittest.TestCase):
    def setUp(self):
        self.source_name = None
        self.created_units = []
        self.created_chunks = []

    def tearDown(self):
        frappe.db.rollback()

        if self.source_name and frappe.db.exists("Nexus Knowledge Source", self.source_name):
            frappe.delete_doc("Nexus Knowledge Source", self.source_name, force=True)

        for chunk_name in self.created_chunks:
            if frappe.db.exists("Nexus Knowledge Chunk", chunk_name):
                frappe.delete_doc("Nexus Knowledge Chunk", chunk_name, force=True)

        for unit_name in self.created_units:
            if frappe.db.exists("Nexus Knowledge Unit", unit_name):
                frappe.delete_doc("Nexus Knowledge Unit", unit_name, force=True)

        frappe.db.commit()

    def create_manual_source(
        self,
        manual_content,
        title="Nexus Ingested Retrieval Test",
        tenant="TEST-NEXUS",
        business_unit="ERP Product",
        project="ABC Implementation",
        access_policy="Public",
        allowed_roles=None,
        denied_roles=None,
    ):
        source = frappe.new_doc("Nexus Knowledge Source")

        set_if_field(source, "title", title)
        set_if_field(source, "source_name", title)
        set_if_field(source, "source_type", "Manual")
        set_if_field(source, "manual_content", manual_content)
        set_if_field(source, "raw_text", manual_content)

        set_if_field(source, "tenant", tenant)
        set_if_field(source, "business_unit", business_unit)
        set_if_field(source, "project", project)

        set_if_field(source, "context", "ERP")
        set_if_field(source, "sub_context", "General")
        set_if_field(source, "entity_type", "Product")
        set_if_field(source, "entity", "DIGITZ ERP")
        set_if_field(source, "topic", "Ingested Retrieval")
        set_if_field(source, "context_path", "ERP/General/Product/DIGITZ ERP/Ingested Retrieval")
        set_if_field(source, "scope_type", "general")

        set_if_field(source, "default_access_policy", access_policy)
        set_if_field(source, "access_policy", access_policy)

        if isinstance(allowed_roles, list):
            allowed_roles = json.dumps(allowed_roles)

        if isinstance(denied_roles, list):
            denied_roles = json.dumps(denied_roles)

        set_if_field(source, "allowed_roles", allowed_roles)
        set_if_field(source, "denied_roles", denied_roles)

        set_if_field(source, "processing_status", "Pending")
        set_if_field(source, "embedding_status", "Pending")

        source.insert(ignore_permissions=True, ignore_mandatory=True)
        frappe.db.commit()

        self.source_name = source.name
        return source

    def process_source_with_mock_embedding(self, source):
        with patch(
            "digitz_ai_nexus.services.ingestion.processor.generate_embedding_json",
            return_value=TEST_EMBEDDING_JSON,
        ):
            result = process_knowledge_source(source.name)

        self.created_units.append(result.get("knowledge_unit"))
        self.created_chunks.extend(result.get("chunks") or [])

        return result

    def align_created_chunks_for_retrieval(
        self,
        access_policy="Public",
        allowed_roles=None,
        denied_roles=None,
    ):
        for chunk_name in self.created_chunks:
            chunk = frappe.get_doc("Nexus Knowledge Chunk", chunk_name)

            set_if_field(chunk, "tenant", "TEST-NEXUS")
            set_if_field(chunk, "business_unit", "ERP Product")
            set_if_field(chunk, "project", "ABC Implementation")
            set_if_field(chunk, "scope_type", "general")

            set_if_field(chunk, "context", "ERP")
            set_if_field(chunk, "sub_context", "General")
            set_if_field(chunk, "entity_type", "Product")
            set_if_field(chunk, "entity", "DIGITZ ERP")
            set_if_field(chunk, "topic", "Ingested Retrieval")
            set_if_field(chunk, "context_path", "ERP/General/Product/DIGITZ ERP/Ingested Retrieval")

            set_if_field(chunk, "access_policy", access_policy)
            set_if_field(chunk, "default_access_policy", access_policy)

            if isinstance(allowed_roles, list):
                allowed_roles = json.dumps(allowed_roles)

            if isinstance(denied_roles, list):
                denied_roles = json.dumps(denied_roles)

            set_if_field(chunk, "allowed_roles", allowed_roles)
            set_if_field(chunk, "denied_roles", denied_roles)

            set_if_field(chunk, "status", "Approved")
            set_if_field(chunk, "is_active", 1)
            set_if_field(chunk, "enabled", 1)
            set_if_field(chunk, "embedding", TEST_EMBEDDING_JSON)

            chunk.save(ignore_permissions=True)

        frappe.db.commit()

    def base_payload(
        self,
        query,
        tenant="TEST-NEXUS",
        business_unit="ERP Product",
        project="ABC Implementation",
        roles=None,
    ):
        return {
            "tenant": tenant,
            "business_unit": business_unit,
            "project": project,
            "project_scope_mode": "with_general",
            "caller_system": "Unit Test",
            "use_case": "Ingested Retrieval Test",
            "context": "ERP",
            "sub_context": "General",
            "entity_type": "Product",
            "entity": "DIGITZ ERP",
            "topic": "Ingested Retrieval",
            "query": query,
            "top_k": 5,
            "user": {
                "id": "test-user@example.com",
                "roles": roles or ["Accounts Manager"],
            },
        }

    def test_ingested_public_chunk_is_retrievable(self):
        source = self.create_manual_source(
            manual_content=(
                "DIGITZ ERP supports hire return valuation through governed retrieval. "
                "This ingested content must be retrievable for approved public Q&A."
            )
        )

        self.process_source_with_mock_embedding(source)
        self.align_created_chunks_for_retrieval(access_policy="Public")

        result = retrieve_allowed_chunks(
            self.base_payload("How does hire return valuation work?"),
            query_embedding=TEST_QUERY_EMBEDDING,
        )

        chunks = extract_result_chunks(result)
        chunk_text = " ".join([(row.get("chunk_text") or row.get("content") or row.get("text") or "") for row in chunks]).lower()

        self.assertTrue(chunks)
        self.assertIn("hire return valuation", chunk_text)

    def test_ingested_chunk_respects_tenant_isolation(self):
        source = self.create_manual_source(
            manual_content="Tenant isolation test content for DIGITZ ERP valuation knowledge."
        )

        self.process_source_with_mock_embedding(source)
        self.align_created_chunks_for_retrieval(access_policy="Public")

        result = retrieve_allowed_chunks(
            self.base_payload(
                query="valuation knowledge",
                tenant="OTHER-TENANT",
            ),
            query_embedding=TEST_QUERY_EMBEDDING,
        )

        chunks = extract_result_chunks(result)
        names = {row_chunk_name(row) for row in chunks}

        self.assertFalse(set(self.created_chunks).intersection(names))

    def test_ingested_chunk_respects_business_unit_isolation(self):
        source = self.create_manual_source(
            manual_content="Business unit isolation test content for DIGITZ ERP valuation knowledge."
        )

        self.process_source_with_mock_embedding(source)
        self.align_created_chunks_for_retrieval(access_policy="Public")

        result = retrieve_allowed_chunks(
            self.base_payload(
                query="valuation knowledge",
                business_unit="Other Business Unit",
            ),
            query_embedding=TEST_QUERY_EMBEDDING,
        )

        chunks = extract_result_chunks(result)
        names = {row_chunk_name(row) for row in chunks}

        self.assertFalse(set(self.created_chunks).intersection(names))

    def test_ingested_restricted_chunk_allows_matching_role(self):
        source = self.create_manual_source(
            manual_content="Restricted ingested payroll valuation knowledge for Accounts Manager only.",
            access_policy="Role Based",
            allowed_roles=["Accounts Manager"],
        )

        self.process_source_with_mock_embedding(source)
        self.align_created_chunks_for_retrieval(
            access_policy="Role Based",
            allowed_roles=["Accounts Manager"],
        )

        result = retrieve_allowed_chunks(
            self.base_payload(
                query="payroll valuation knowledge",
                roles=["Accounts Manager"],
            ),
            query_embedding=TEST_QUERY_EMBEDDING,
        )

        chunks = extract_result_chunks(result)
        names = {row_chunk_name(row) for row in chunks}

        self.assertTrue(set(self.created_chunks).intersection(names))

    def test_ingested_restricted_chunk_blocks_non_matching_role(self):
        source = self.create_manual_source(
            manual_content="Restricted ingested margin knowledge for Accounts Manager only.",
            access_policy="Role Based",
            allowed_roles=["Accounts Manager"],
        )

        self.process_source_with_mock_embedding(source)
        self.align_created_chunks_for_retrieval(
            access_policy="Role Based",
            allowed_roles=["Accounts Manager"],
        )

        result = retrieve_allowed_chunks(
            self.base_payload(
                query="restricted margin knowledge",
                roles=["Sales User"],
            ),
            query_embedding=TEST_QUERY_EMBEDDING,
        )

        chunks = extract_result_chunks(result)
        names = {row_chunk_name(row) for row in chunks}

        self.assertFalse(set(self.created_chunks).intersection(names))

    def test_ingested_chunk_participates_in_keyword_retrieval(self):
        source = self.create_manual_source(
            manual_content=(
                "Keyword retrieval test: scaffold hire return inspection and valuation "
                "must be found through business terms."
            )
        )

        self.process_source_with_mock_embedding(source)
        self.align_created_chunks_for_retrieval(access_policy="Public")

        result = retrieve_allowed_chunks(
            self.base_payload("scaffold hire return inspection valuation"),
            query_embedding=TEST_QUERY_EMBEDDING,
        )

        chunks = extract_result_chunks(result)
        chunk_text = " ".join([(row.get("chunk_text") or row.get("content") or row.get("text") or "") for row in chunks]).lower()

        self.assertTrue(chunks)
        self.assertIn("scaffold hire return inspection", chunk_text)

    def test_ingested_chunk_missing_embedding_does_not_crash_retrieval(self):
        source = self.create_manual_source(
            manual_content="Missing embedding safety test for ingested retrieval."
        )

        self.process_source_with_mock_embedding(source)
        self.align_created_chunks_for_retrieval(access_policy="Public")

        for chunk_name in self.created_chunks:
            chunk = frappe.get_doc("Nexus Knowledge Chunk", chunk_name)
            set_if_field(chunk, "embedding", "")
            set_if_field(chunk, "embedding_status", "Failed")
            chunk.save(ignore_permissions=True)

        frappe.db.commit()

        result = retrieve_allowed_chunks(
            self.base_payload("missing embedding safety"),
            query_embedding=TEST_QUERY_EMBEDDING,
        )

        chunks = extract_result_chunks(result)

        self.assertIsInstance(chunks, list)