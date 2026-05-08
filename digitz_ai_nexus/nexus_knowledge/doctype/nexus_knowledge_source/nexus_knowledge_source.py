import frappe
from frappe.model.document import Document
class NexusKnowledgeSource(Document):
    def validate(self):
        if not self.title:
            frappe.throw("Title is required")

        if not self.source_type:
            frappe.throw("Source Type is required")

        if self.source_type in ["PDF", "DOCX", "TXT"] and not self.source_file:
            frappe.throw("Source File is required for uploaded documents")

        if self.source_type == "Manual" and not self.manual_content:
            frappe.throw("Manual Content is required for manual knowledge")

        if not self.status:
            self.status = "Draft"

        if not self.processing_status:
            self.processing_status = "Pending"

        if not self.embedding_status:
            self.embedding_status = "Pending"


@frappe.whitelist()
def get_source_quality_panel(source_name):
    if not source_name:
        frappe.throw("Source name is required")

    source = frappe.get_doc("Nexus Knowledge Source", source_name)

    chunks = []

    if source.generated_knowledge_unit:
        chunks = frappe.get_all(
            "Nexus Knowledge Chunk",
            filters={
                "knowledge_unit": source.generated_knowledge_unit
            },
            fields=[
                "name",
                "knowledge_unit",
                "chunk_index",
                "content",
                "embedding",
                "creation",
                "modified"
            ],
            order_by="chunk_index asc",
            limit_page_length=100
        )

    embedded_count = 0

    for chunk in chunks:
        if chunk.get("embedding"):
            embedded_count += 1

    if chunks:
        if embedded_count == len(chunks):
            embedding_status = "Completed"
        elif embedded_count > 0:
            embedding_status = "Pending"
        else:
            embedding_status = "Pending"
    else:
        embedding_status = source.embedding_status or "Pending"

    return {
        "source": source.name,
        "title": source.title,
        "processing_status": source.processing_status,
        "embedding_status": embedding_status,
        "chunk_count": len(chunks) if chunks else (source.chunk_count or 0),
        "last_processed_on": source.last_processed_on,
        "generated_knowledge_unit": source.generated_knowledge_unit,
        "extracted_text_preview": source.extracted_text_preview,
        "error_log": source.error_log,
        "chunks": chunks
    }