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
        meta = frappe.get_meta("Nexus Knowledge Source")

        if meta.has_field("diagnostics_status") and not getattr(self, "diagnostics_status", None):
            self.diagnostics_status = "Pending"

        if meta.has_field("processing_version") and not getattr(self, "processing_version", None):
            self.processing_version = 0

        if meta.has_field("chunk_count") and not getattr(self, "chunk_count", None):
            self.chunk_count = 0

        if meta.has_field("active_chunk_count") and not getattr(self, "active_chunk_count", None):
            self.active_chunk_count = 0

        if meta.has_field("retrieval_ready") and getattr(self, "retrieval_ready", None) is None:
            self.retrieval_ready = 0


@frappe.whitelist()
def get_source_quality_panel(source_name):
    if not source_name:
        frappe.throw("Source name is required")

    source = frappe.get_doc("Nexus Knowledge Source", source_name)

    chunks = []
    chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")

    chunk_fields = [
        "name",
        "knowledge_unit",
        "knowledge_source",
        "chunk_index",
        "chunk_hash",
        "embedding",
        "embedding_status",
        "creation",
        "modified"
    ]

    optional_fields = [
        "chunk_text",
        "content",
        "text",
        "source_version",
        "archived",
        "disabled",
        "character_count",
        "diagnostics_status",
        "diagnostics_message",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
        "context_path"
    ]

    for fieldname in optional_fields:
        if chunk_meta.has_field(fieldname):
            chunk_fields.append(fieldname)

    filters = {}

    if chunk_meta.has_field("knowledge_source"):
        filters["knowledge_source"] = source.name
    elif source.generated_knowledge_unit:
        filters["knowledge_unit"] = source.generated_knowledge_unit

    if filters:
        chunks = frappe.get_all(
            "Nexus Knowledge Chunk",
            filters=filters,
            fields=chunk_fields,
            order_by="source_version desc, chunk_index asc",
            limit_page_length=500
        )

    active_chunks = []
    archived_chunks = []

    for chunk in chunks:
        content = (
            chunk.get("chunk_text")
            or chunk.get("content")
            or chunk.get("text")
            or ""
        )

        chunk["content"] = content
        chunk["preview"] = content[:220]
        chunk["character_count"] = chunk.get("character_count") or len(content or "")
        chunk["has_embedding"] = bool(chunk.get("embedding"))

        is_archived = bool(chunk.get("archived"))
        is_disabled = bool(chunk.get("disabled"))

        chunk["is_active"] = not is_archived and not is_disabled

        if chunk["is_active"]:
            active_chunks.append(chunk)
        else:
            archived_chunks.append(chunk)

    embedded_count = 0
    missing_embedding_count = 0
    warning_count = 0
    critical_count = 0
    duplicate_count = 0
    seen_hashes = set()

    for chunk in active_chunks:
        if chunk.get("has_embedding"):
            embedded_count += 1
        else:
            missing_embedding_count += 1

        chunk_hash = chunk.get("chunk_hash")

        if chunk_hash:
            if chunk_hash in seen_hashes:
                duplicate_count += 1
                chunk["duplicate_chunk"] = 1
            else:
                seen_hashes.add(chunk_hash)
                chunk["duplicate_chunk"] = 0
        else:
            chunk["duplicate_chunk"] = 0

        diagnostics_status = chunk.get("diagnostics_status") or "Pending"
        chunk["diagnostics_status"] = diagnostics_status

        if diagnostics_status == "Critical":
            critical_count += 1
        elif diagnostics_status == "Warning":
            warning_count += 1

    for chunk in archived_chunks:
        chunk["duplicate_chunk"] = 0
        chunk["diagnostics_status"] = chunk.get("diagnostics_status") or "Archived"

    active_chunk_count = len(active_chunks)

    if active_chunk_count:
        if embedded_count == active_chunk_count:
            embedding_status = "Completed"
        elif embedded_count > 0:
            embedding_status = "Pending"
        else:
            embedding_status = "Failed"
    else:
        embedding_status = source.embedding_status or "Pending"

    if critical_count > 0 or missing_embedding_count > 0:
        diagnostics_status = "Critical"
    elif warning_count > 0 or duplicate_count > 0:
        diagnostics_status = "Warning"
    elif active_chunk_count > 0:
        diagnostics_status = "Healthy"
    else:
        diagnostics_status = source.diagnostics_status or "Pending"

    retrieval_ready = (
        source.status == "Published"
        and embedding_status == "Completed"
        and diagnostics_status == "Healthy"
        and active_chunk_count > 0
    )

    return {
        "source": source.name,
        "title": source.title,
        "processing_status": source.processing_status,
        "processing_version": getattr(source, "processing_version", 0) or 0,
        "embedding_status": embedding_status,
        "diagnostics_status": diagnostics_status,
        "retrieval_ready": 1 if retrieval_ready else 0,

        "chunk_count": len(chunks),
        "active_chunk_count": active_chunk_count,
        "archived_chunk_count": len(archived_chunks),

        "embedded_count": embedded_count,
        "missing_embedding_count": missing_embedding_count,
        "duplicate_count": duplicate_count,
        "warning_count": warning_count,
        "critical_count": critical_count,

        "last_processed_on": source.last_processed_on,
        "generated_knowledge_unit": source.generated_knowledge_unit,
        "extracted_text_preview": source.extracted_text_preview,
        "error_log": source.error_log,

        "chunks": active_chunks + archived_chunks
    }