import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch

from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source


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
        self.title = f"TEST DIGITZ ERP Overview {frappe.generate_hash(length=8)}"
        self.source_name = None
        business_units = frappe.get_all(
            "Nexus Business Unit", pluck="name", limit_page_length=1
        )
        self.business_unit = business_units[0] if business_units else None
        tenants = frappe.get_all("Nexus Tenant", pluck="name", limit_page_length=1)
        self.tenant = tenants[0] if tenants else None

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
            filters={"title": ["like", f"{self.title}%"]},
            pluck="name",
        )

        for unit in units:
            frappe.delete_doc("Nexus Knowledge Unit", unit, force=True)

        if self.source_name and frappe.db.exists("Nexus Knowledge Source", self.source_name):
            frappe.delete_doc("Nexus Knowledge Source", self.source_name, force=True)

        frappe.db.commit()

    def create_source(self, entity_type="Product", entity="DIGITZ ERP"):
        source = frappe.new_doc("Nexus Knowledge Source")
        source.title = self.title
        source.source_type = "Manual"
        source.manual_content = (
            "DIGITZ ERP is an enterprise ERP platform. "
            "It supports accounting, inventory, HR, payroll, and operational workflows."
        )

        source.tenant = self.tenant
        source.business_unit = self.business_unit
        source.project = ""
        source.context = "ERP"
        source.sub_context = "Product Overview"
        source.entity_type = entity_type
        source.entity = entity
        source.topic = "Platform Overview"

        source.access_policy = "PUBLIC"
        source.priority = 0
        source.status = "Published"

        source.insert(ignore_permissions=True)
        frappe.db.commit()

        self.source_name = source.name
        return source.name

    @patch("digitz_ai_nexus.services.gap_notification_service.on_knowledge_source_published")
    def test_standard_source_feed_defaults_blank_entity_type(self, mock_publish_hook):
        source_name = self.create_source(entity_type=None, entity=None)

        source = frappe.get_doc("Nexus Knowledge Source", source_name)

        self.assertEqual(source.entity_type, "Knowledge Source")
        self.assertEqual(source.entity, self.title)
    
    @patch("digitz_ai_nexus.services.gap_notification_service.on_knowledge_source_published")
    @patch("digitz_ai_nexus.services.ingestion.processor.generate_embedding_json", return_value="[0.1, 0.2, 0.3]")
    @patch("digitz_ai_nexus.services.ingestion.processor.chunk_text", return_value=["DIGITZ ERP is an enterprise ERP platform. It supports accounting, inventory, HR, payroll, and operational workflows."])

    def test_manual_source_process_creates_unit_and_chunk(
        self, mock_chunk_text, mock_embedding, mock_publish_hook
    ):
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
            filters={"title": ["like", f"{self.title} - v%"]},
            fields=["name", "title", "business_unit", "context_path"],
            limit_page_length=1,
        )

        self.assertEqual(len(unit), 1)
        self.assertEqual(unit[0].business_unit, self.business_unit)

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
        self.assertEqual(chunk.knowledge_unit, result["knowledge_unit"])
        self.assertEqual(chunk.chunk_index, 1)
        self.assertEqual(chunk.embedding_status, "Completed")
        self.assertEqual(chunk.business_unit, self.business_unit)
        self.assertEqual(chunk.disabled, 0)
        self.assertIn("DIGITZ ERP", chunk.chunk_text)
