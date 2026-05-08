import unittest
from unittest.mock import patch

import frappe

from digitz_ai_nexus.services.ingestion.normalizer import normalize_text
from digitz_ai_nexus.services.ingestion.chunker import chunk_text
from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source


TEST_EMBEDDING_JSON = "[0.1, 0.2, 0.3]"


def set_if_field(doc, fieldname, value):
    if value is None:
        return

    if not doc.meta.has_field(fieldname):
        return

    table_columns = frappe.db.get_table_columns(doc.doctype)

    if fieldname not in table_columns:
        return

    doc.set(fieldname, value)


class TestKnowledgeIngestion(unittest.TestCase):
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

    def create_manual_source(self, manual_content=None):
        source = frappe.new_doc("Nexus Knowledge Source")

        title = "Nexus Ingestion Unit Test"

        set_if_field(source, "title", title)
        set_if_field(source, "source_name", title)
        set_if_field(source, "source_type", "Manual")
        set_if_field(source, "manual_content", manual_content)
        set_if_field(source, "raw_text", manual_content)

        set_if_field(source, "tenant", "TEST-NEXUS")
        set_if_field(source, "business_unit", "ERP Product")
        set_if_field(source, "project", "ABC Implementation")

        set_if_field(source, "context", "ERP")
        set_if_field(source, "sub_context", "General")
        set_if_field(source, "entity_type", "Product")
        set_if_field(source, "entity", "DIGITZ ERP")
        set_if_field(source, "topic", "Ingestion Test")
        set_if_field(source, "context_path", "ERP/General/Product/DIGITZ ERP/Ingestion Test")
        set_if_field(source, "scope_type", "general")

        set_if_field(source, "default_access_policy", "Public")
        set_if_field(source, "access_policy", "Public")        
        set_if_field(source, "processing_status", "Pending")
        set_if_field(source, "embedding_status", "Pending")

        source.insert(ignore_permissions=True, ignore_mandatory=True)
        frappe.db.commit()

        self.source_name = source.name
        return source

    def test_normalize_text_removes_extra_spaces_and_blank_lines(self):
        text = "DIGITZ   ERP\r\n\r\n\r\n   Nexus\t\tKnowledge   "
        normalized = normalize_text(text)

        self.assertEqual(normalized, "DIGITZ ERP\n\nNexus Knowledge")

    def test_chunk_text_creates_chunks_with_overlap(self):
        text = " ".join([f"word{i}" for i in range(1, 21)])

        chunks = chunk_text(text, chunk_size=10, overlap=3)

        self.assertEqual(len(chunks), 3)
        self.assertTrue(chunks[0].startswith("word1"))
        self.assertIn("word8", chunks[1])
        self.assertIn("word15", chunks[2])

    @patch(
        "digitz_ai_nexus.services.ingestion.processor.generate_embedding_json",
        return_value=TEST_EMBEDDING_JSON,
    )
    def test_manual_source_processing_creates_unit_and_chunk(self, mock_embedding):
        source = self.create_manual_source(
            manual_content=(
                "DIGITZ ERP supports hire return valuation through governed knowledge retrieval. "
                "Nexus should extract this content, create chunks, generate embeddings, and make it "
                "available for approved Q&A."
            )
        )

        result = process_knowledge_source(source.name)

        self.assertEqual(result.get("status"), "success")
        self.assertTrue(result.get("knowledge_unit"))
        self.assertEqual(result.get("chunk_count"), 1)
        self.assertEqual(len(result.get("chunks")), 1)

        self.created_units.append(result.get("knowledge_unit"))
        self.created_chunks.extend(result.get("chunks"))

        unit = frappe.get_doc("Nexus Knowledge Unit", result.get("knowledge_unit"))
        chunk = frappe.get_doc("Nexus Knowledge Chunk", result.get("chunks")[0])

        self.assertEqual(chunk.get("knowledge_unit"), unit.name)
        self.assertIn("hire return valuation", (chunk.get("chunk_text") or chunk.get("content") or "").lower())
        self.assertEqual(chunk.get("embedding"), TEST_EMBEDDING_JSON)

        if chunk.meta.has_field("embedding_status"):
            self.assertEqual(chunk.get("embedding_status"), "Completed")

        mock_embedding.assert_called_once()

    @patch(
        "digitz_ai_nexus.services.ingestion.processor.generate_embedding_json",
        side_effect=Exception("Synthetic embedding failure"),
    )
    def test_embedding_failure_still_creates_chunk_safely(self, mock_embedding):
        source = self.create_manual_source(
            manual_content="This content should still create a chunk even if embedding generation fails."
        )

        result = process_knowledge_source(source.name)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("chunk_count"), 1)

        self.created_units.append(result.get("knowledge_unit"))
        self.created_chunks.extend(result.get("chunks"))

        chunk = frappe.get_doc("Nexus Knowledge Chunk", result.get("chunks")[0])

        if chunk.meta.has_field("embedding_status"):
            self.assertEqual(chunk.get("embedding_status"), "Failed")

        mock_embedding.assert_called_once()

    def test_empty_manual_source_fails_safely(self):
        with self.assertRaises(Exception):
            self.create_manual_source(manual_content="")

    @patch(
        "digitz_ai_nexus.services.ingestion.processor.generate_embedding_json",
        return_value=TEST_EMBEDDING_JSON,
    )
    def test_metadata_propagates_to_created_chunk(self, mock_embedding):
        source = self.create_manual_source(
            manual_content="Metadata propagation test for tenant, business unit, context, topic and access policy."
        )

        result = process_knowledge_source(source.name)

        self.created_units.append(result.get("knowledge_unit"))
        self.created_chunks.extend(result.get("chunks"))

        chunk = frappe.get_doc("Nexus Knowledge Chunk", result.get("chunks")[0])

        self.assertEqual(chunk.get("tenant"), "TEST-NEXUS")
        self.assertEqual(chunk.get("business_unit"), "ERP Product")

        if chunk.meta.has_field("context"):
            self.assertEqual(chunk.get("context"), "ERP")

        if chunk.meta.has_field("topic"):
            self.assertEqual(chunk.get("topic"), "Ingestion Test")

        if chunk.meta.has_field("access_policy"):
            self.assertEqual((chunk.get("access_policy") or "").lower(), "public")