import frappe
import unittest
from unittest.mock import patch

from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source
from digitz_ai_nexus.nexus_knowledge.doctype.nexus_knowledge_source.nexus_knowledge_source import (
    get_source_quality_panel,
)


TEST_EMBEDDING_JSON = "[0.0, 1.0, 0.0]"


class TestKnowledgeSourceQualityPanel(unittest.TestCase):
    def setUp(self):
        self.source_title = "Nexus Quality Panel Test Source"

        self.cleanup_test_records()

        self.source = frappe.get_doc({
            "doctype": "Nexus Knowledge Source",
            "title": self.source_title,
            "source_type": "Manual",
            "manual_content": """
                DIGITZ AI Nexus quality panel validates extracted text,
                generated chunks, embedding status, and knowledge source readiness.

                The quality panel helps administrators verify whether the uploaded
                or manual knowledge source was processed correctly before publishing
                it to public Q&A or website chat widgets.
            """,
            "tenant": "TEST-NEXUS",
            "business_unit": "Nexus QA",
            "context": "Nexus",
            "sub_context": "Knowledge",
            "entity_type": "Feature",
            "entity": "Quality Panel",
            "topic": "Knowledge Source Quality",
            "status": "Draft"
        }).insert(ignore_permissions=True)

        frappe.db.commit()

    def tearDown(self):
        self.cleanup_test_records()
        frappe.db.commit()

    def cleanup_test_records(self):
        sources = frappe.get_all(
            "Nexus Knowledge Source",
            filters={"title": self.source_title},
            pluck="name",
        )

        for source_name in sources:
            frappe.delete_doc(
                "Nexus Knowledge Source",
                source_name,
                force=True,
                ignore_permissions=True,
            )

        units = frappe.get_all(
            "Nexus Knowledge Unit",
            filters={"title": self.source_title},
            pluck="name",
        )

        for unit_name in units:
            chunks = frappe.get_all(
                "Nexus Knowledge Chunk",
                filters={"knowledge_unit": unit_name},
                pluck="name",
            )

            for chunk_name in chunks:
                frappe.delete_doc(
                    "Nexus Knowledge Chunk",
                    chunk_name,
                    force=True,
                    ignore_permissions=True,
                )

            frappe.delete_doc(
                "Nexus Knowledge Unit",
                unit_name,
                force=True,
                ignore_permissions=True,
            )

    @patch(
        "digitz_ai_nexus.services.ingestion.processor.generate_embedding_json",
        return_value=TEST_EMBEDDING_JSON,
    )
    def test_process_source_updates_quality_fields(self, mock_embedding):
        result = process_knowledge_source(self.source.name)

        self.assertEqual(result.get("status"), "success")
        self.assertTrue(result.get("knowledge_unit"))
        self.assertGreater(result.get("chunk_count"), 0)
        self.assertEqual(result.get("embedding_status"), "Completed")

        source = frappe.get_doc("Nexus Knowledge Source", self.source.name)

        self.assertEqual(source.processing_status, "Processed")
        self.assertEqual(source.embedding_status, "Completed")
        self.assertTrue(source.generated_knowledge_unit)
        self.assertGreater(source.chunk_count, 0)
        self.assertTrue(source.last_processed_on)
        self.assertTrue(source.extracted_text_preview)

    @patch(
        "digitz_ai_nexus.services.ingestion.processor.generate_embedding_json",
        return_value=TEST_EMBEDDING_JSON,
    )
    def test_process_source_syncs_knowledge_unit_embedding_status(self, mock_embedding):
        result = process_knowledge_source(self.source.name)

        unit_name = result.get("generated_knowledge_unit")
        self.assertTrue(unit_name)

        unit = frappe.get_doc("Nexus Knowledge Unit", unit_name)

        if unit.meta.has_field("embedding_status"):
            self.assertEqual(unit.embedding_status, "Completed")

        if unit.meta.has_field("chunk_count"):
            self.assertGreater(unit.chunk_count, 0)

        if unit.meta.has_field("last_processed_on"):
            self.assertTrue(unit.last_processed_on)

    @patch(
        "digitz_ai_nexus.services.ingestion.processor.generate_embedding_json",
        return_value=TEST_EMBEDDING_JSON,
    )
    def test_quality_panel_returns_generated_chunks(self, mock_embedding):
        process_knowledge_source(self.source.name)

        panel = get_source_quality_panel(self.source.name)

        self.assertEqual(panel.get("source"), self.source.name)
        self.assertEqual(panel.get("processing_status"), "Processed")
        self.assertEqual(panel.get("embedding_status"), "Completed")
        self.assertTrue(panel.get("generated_knowledge_unit"))
        self.assertGreater(panel.get("chunk_count"), 0)
        self.assertTrue(panel.get("extracted_text_preview"))

        chunks = panel.get("chunks") or []

        self.assertGreater(len(chunks), 0)
        self.assertTrue(chunks[0].get("name"))
        self.assertTrue(chunks[0].get("content"))

    def test_quality_panel_works_before_processing(self):
        panel = get_source_quality_panel(self.source.name)

        self.assertEqual(panel.get("source"), self.source.name)        
        self.assertEqual(panel.get("active_chunk_count"), 0)
        self.assertEqual(panel.get("retrieval_ready"), 0)
        self.assertFalse(panel.get("generated_knowledge_unit"))
        
        active_chunks = [
            row for row in (panel.get("chunks") or [])
            if row.get("is_active")
        ]
        self.assertEqual(active_chunks, [])

    @patch(
        "digitz_ai_nexus.services.ingestion.processor.extract_source_text",
        side_effect=Exception("Synthetic extraction failure"),
    )
    def test_failed_processing_updates_source_status_and_error_log(self, mock_extract):
        with self.assertRaises(Exception):
            process_knowledge_source(self.source.name)

        source = frappe.get_doc("Nexus Knowledge Source", self.source.name)

        self.assertEqual(source.processing_status, "Failed")
        self.assertEqual(source.embedding_status, "Failed")
        self.assertTrue(source.error_log)
        self.assertTrue(source.last_processed_on)