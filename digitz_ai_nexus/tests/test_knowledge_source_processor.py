import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch

from digitz_ai_nexus.services.knowledge_source_processor import process_knowledge_source


def fake_embedding(text, provider=None):
    return [0.1, 0.2, 0.3]


def fake_chunk_text(text):
    return [
        {
            "index": 1,
            "text": text,
        }
    ]


class TestNexusKnowledgeSourceProcessor(FrappeTestCase):

    def setUp(self):
        self.title = "TEST DIGITZ ERP Overview"
        self.source_name = None

    def tearDown(self):
        chunks = []

        if self.source_name:
            chunks = frappe.get_all(
                "Nexus Knowledge Chunk",
                filters={"knowledge_source": self.source_name},
                pluck="name",
            )

        for chunk in chunks:
            frappe.delete_doc("Nexus Knowledge Chunk", chunk, force=True)

        units = frappe.get_all(
            "Nexus Knowledge Unit",
            filters={"title": self.title},
            pluck="name",
        )

        for unit in units:
            frappe.delete_doc("Nexus Knowledge Unit", unit, force=True)

        if self.source_name and frappe.db.exists("Nexus Knowledge Source", self.source_name):
            frappe.delete_doc("Nexus Knowledge Source", self.source_name, force=True)

        frappe.db.commit()

    def create_source(self):
        source = frappe.new_doc("Nexus Knowledge Source")
        source.title = self.title
        source.source_type = "Manual"
        source.manual_content = (
            "DIGITZ ERP is an enterprise ERP platform. "
            "It supports accounting, inventory, HR, payroll, and operational workflows."
        )

        source.tenant = "DIGITZ-ERP"
        source.business_unit = "ERP Product"
        source.project = ""
        source.context = "ERP"
        source.sub_context = "Product Overview"
        source.entity_type = "Product"
        source.entity = "DIGITZ ERP"
        source.topic = "Platform Overview"

        source.access_policy = "PUBLIC"
        source.priority = 0
        source.status = "Published"

        source.insert(ignore_permissions=True)
        frappe.db.commit()

        self.source_name = source.name
        return source.name

    @patch("digitz_ai_nexus.services.knowledge_source_processor.generate_embedding", fake_embedding)
    @patch("digitz_ai_nexus.services.knowledge_source_processor.chunk_text", fake_chunk_text)
    def test_manual_source_process_creates_unit_and_chunk(self):
        source_name = self.create_source()

        result = process_knowledge_source(source_name)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["chunk_count"], 1)

        source = frappe.get_doc("Nexus Knowledge Source", source_name)

        self.assertEqual(source.processing_status, "Processed")
        self.assertEqual(source.embedding_status, "Completed")
        self.assertEqual(source.chunk_count, 1)

        unit = frappe.get_all(
            "Nexus Knowledge Unit",
            filters={"title": self.title},
            fields=["name", "title", "business_unit", "context_path"],
            limit_page_length=1,
        )

        self.assertEqual(len(unit), 1)
        self.assertEqual(unit[0].business_unit, "ERP Product")

        chunks = frappe.get_all(
            "Nexus Knowledge Chunk",
            filters={"knowledge_source": source_name},
            fields=[
                "name",
                "knowledge_source",
                "knowledge_unit",
                "chunk_index",
                "chunk_text",
                "embedding_status",
                "business_unit",
                "context_path",
                "disabled",
            ],
        )

        self.assertEqual(len(chunks), 1)

        chunk = chunks[0]

        self.assertEqual(chunk.knowledge_source, source_name)
        self.assertEqual(chunk.knowledge_unit, unit[0].name)
        self.assertEqual(chunk.chunk_index, 1)
        self.assertEqual(chunk.embedding_status, "Completed")
        self.assertEqual(chunk.business_unit, "ERP Product")
        self.assertEqual(chunk.disabled, 0)
        self.assertIn("DIGITZ ERP", chunk.chunk_text)