from pathlib import Path

import frappe

from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source


SOURCE_TITLE = "NEXUS AI Public Chat Knowledge"
TENANT = "NEXUS-AI"
BUSINESS_UNIT = "NEXUS-AI-BU"
ACCESS_POLICY = "Public-NEXUS-AI"
CONTENT_PATH = Path(frappe.get_app_path("digitz_ai_nexus")).parent / "docs" / "nexus-ai-public-chat-knowledge-source.md"


def _set_if_field(doc, fieldname, value):
    if doc.meta.has_field(fieldname):
        doc.set(fieldname, value)


@frappe.whitelist()
def insert_or_update(process=1):
    content = CONTENT_PATH.read_text(encoding="utf-8")

    if frappe.db.exists("Nexus Knowledge Source", SOURCE_TITLE):
        doc = frappe.get_doc("Nexus Knowledge Source", SOURCE_TITLE)
        action = "updated"
    else:
        doc = frappe.new_doc("Nexus Knowledge Source")
        doc.title = SOURCE_TITLE
        action = "inserted"

    doc.source_type = "Manual"
    doc.manual_content = content
    doc.tenant = TENANT
    doc.business_unit = BUSINESS_UNIT
    doc.project = "Public Website"
    doc.context = "Website Public Chat"
    doc.sub_context = "Ask Anything About Nexus AI"
    doc.entity_type = "Product"
    doc.entity = "NEXUS AI"
    doc.topic = "Public Platform Knowledge"
    doc.access_policy = ACCESS_POLICY
    doc.priority = 100
    doc.status = "Published"

    _set_if_field(doc, "processing_status", "Pending")
    _set_if_field(doc, "embedding_status", "Pending")
    _set_if_field(doc, "diagnostics_status", "Pending")
    _set_if_field(doc, "validation_status", "Pending")
    _set_if_field(doc, "retrieval_ready", 0)
    _set_if_field(doc, "ready_to_publish", 0)
    _set_if_field(doc, "needs_review", 0)
    _set_if_field(doc, "review_reason", "")

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    frappe.db.commit()

    process_result = None
    if int(process or 0):
        process_result = process_knowledge_source(doc.name)

    refreshed = frappe.get_doc("Nexus Knowledge Source", doc.name)
    return {
        "action": action,
        "source": refreshed.name,
        "tenant": refreshed.get("tenant"),
        "business_unit": refreshed.get("business_unit"),
        "access_policy": refreshed.get("access_policy"),
        "status": refreshed.get("status"),
        "processing_status": refreshed.get("processing_status"),
        "embedding_status": refreshed.get("embedding_status"),
        "diagnostics_status": refreshed.get("diagnostics_status"),
        "chunk_count": refreshed.get("chunk_count"),
        "active_chunk_count": refreshed.get("active_chunk_count"),
        "retrieval_ready": refreshed.get("retrieval_ready"),
        "process_result": process_result,
    }
