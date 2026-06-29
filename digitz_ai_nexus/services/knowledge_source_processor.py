import os
import json
import hashlib
import frappe
from frappe.utils import now

from digitz_ai_nexus.engine.chunking import chunk_text
from digitz_ai_nexus.engine.embedding import generate_embedding


def process_knowledge_source(source_name):
    source = frappe.get_doc("Nexus Knowledge Source", source_name)

    try:
        source.db_set("processing_status", "Processing")
        source.db_set("embedding_status", "Pending")
        source.db_set("diagnostics_status", "Pending")
        source.db_set("retrieval_ready", 0)
        source.db_set("error_log", "")

        text = extract_source_text(source)

        if not text or not text.strip():
            frappe.throw("No readable text found in knowledge source")

        next_version = int(source.processing_version or 0) + 1

        archive_existing_chunks(source.name)

        chunks = chunk_text(text)

        created_count = 0
        embedded_count = 0
        warning_count = 0
        critical_count = 0
        seen_hashes = set()

        knowledge_unit = create_new_knowledge_unit(source, text, next_version)

        for index, chunk in enumerate(chunks, start=1):
            chunk_content = chunk.get("text") if isinstance(chunk, dict) else str(chunk)

            if not chunk_content or not chunk_content.strip():
                continue

            chunk_content = chunk_content.strip()
            chunk_hash = get_text_hash(chunk_content)

            diagnostics_status, diagnostics_message = diagnose_chunk(
                chunk_content=chunk_content,
                chunk_hash=chunk_hash,
                seen_hashes=seen_hashes,
            )

            if diagnostics_status == "Critical":
                critical_count += 1
            elif diagnostics_status == "Warning":
                warning_count += 1

            seen_hashes.add(chunk_hash)

            embedding = generate_embedding(chunk_content)

            doc = frappe.new_doc("Nexus Knowledge Chunk")
            doc.knowledge_source = source.name
            doc.knowledge_unit = knowledge_unit
            doc.chunk_index = index

            if hasattr(doc, "title"):
                doc.title = f"{source.title} - Chunk {index}"

            if hasattr(doc, "chunk_title"):
                doc.chunk_title = f"{source.title} - Chunk {index}"

            doc.tenant = source.tenant
            doc.business_unit = source.business_unit
            doc.project = source.project
            doc.context = source.context
            doc.sub_context = source.sub_context
            doc.entity_type = source.entity_type
            doc.entity = source.entity
            doc.topic = source.topic
            doc.context_path = build_context_path(source)

            doc.chunk_text = chunk_content
            doc.chunk_hash = chunk_hash
            doc.character_count = len(chunk_content)
            doc.source_version = next_version

            doc.embedding = json.dumps(embedding)
            doc.embedding_status = "Completed"

            doc.diagnostics_status = diagnostics_status
            doc.diagnostics_message = diagnostics_message

            doc.access_policy = source.access_policy
            doc.priority = source.priority or 0

            doc.archived = 0
            doc.disabled = 0 if source.status == "Published" else 1

            doc.insert(ignore_permissions=True)

            created_count += 1
            embedded_count += 1

        final_embedding_status = "Completed" if created_count and embedded_count == created_count else "Pending"

        if critical_count > 0:
            final_diagnostics_status = "Critical"
        elif warning_count > 0:
            final_diagnostics_status = "Warning"
        elif created_count > 0:
            final_diagnostics_status = "Healthy"
        else:
            final_diagnostics_status = "Critical"

        # Processing invalidates any previous retrieval_ready state — tests must be
        # re-run after new chunks/embeddings are created. The full gate is enforced
        # via _sync_source_retrieval_ready_from_answer_approvals (called from
        # run_source_test_cases and publish_knowledge_source).
        retrieval_ready = False

        source.db_set("processing_version", next_version)
        source.db_set("generated_knowledge_unit", knowledge_unit)
        source.db_set("chunk_count", created_count)
        source.db_set("active_chunk_count", created_count if source.status == "Published" else 0)
        source.db_set("embedding_status", final_embedding_status)
        source.db_set("diagnostics_status", final_diagnostics_status)
        source.db_set("retrieval_ready", 0)
        source.db_set("processing_status", "Processed")
        source.db_set("last_processed_on", now())
        source.db_set("extracted_text_preview", text[:5000])

        frappe.db.commit()

        return {
            "status": "success",
            "source": source.name,
            "processing_version": next_version,
            "knowledge_unit": knowledge_unit,
            "chunk_count": created_count,
            "active_chunk_count": created_count if source.status == "Published" else 0,
            "embedding_status": final_embedding_status,
            "diagnostics_status": final_diagnostics_status,
            "retrieval_ready": 1 if retrieval_ready else 0,
        }

    except Exception as e:
        source.db_set("processing_status", "Failed")
        source.db_set("embedding_status", "Failed")
        source.db_set("diagnostics_status", "Critical")
        source.db_set("retrieval_ready", 0)
        source.db_set("error_log", frappe.get_traceback())
        frappe.db.commit()

        return {
            "status": "failed",
            "source": source.name,
            "error": str(e),
        }


def extract_source_text(source):
    if source.source_type == "Manual":
        return source.manual_content or ""

    if not source.source_file:
        frappe.throw("Source File is required")

    file_doc = frappe.get_doc("File", {"file_url": source.source_file})
    file_path = file_doc.get_full_path()

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    if ext == ".pdf":
        return extract_pdf_text(file_path)

    if ext == ".docx":
        return extract_docx_text(file_path)

    frappe.throw(f"Unsupported file type: {ext}")


def extract_pdf_text(file_path):
    try:
        from pypdf import PdfReader
    except Exception:
        frappe.throw("pypdf is required. Install with: pip install pypdf")

    reader = PdfReader(file_path)
    text_parts = []

    for page in reader.pages:
        text_parts.append(page.extract_text() or "")

    return "\n\n".join(text_parts)


def extract_docx_text(file_path):
    try:
        from docx import Document
    except Exception:
        frappe.throw("python-docx is required. Install with: pip install python-docx")

    doc = Document(file_path)

    return "\n".join([p.text for p in doc.paragraphs if p.text])


def archive_existing_chunks(source_name):
    existing = frappe.get_all(
        "Nexus Knowledge Chunk",
        filters={"knowledge_source": source_name},
        pluck="name",
    )

    for name in existing:
        frappe.db.set_value(
            "Nexus Knowledge Chunk",
            name,
            {
                "archived": 1,
                "disabled": 1,
            },
            update_modified=True,
        )


def create_new_knowledge_unit(source, content, processing_version):
    doc = frappe.new_doc("Nexus Knowledge Unit")
    doc.title = f"{source.title} - v{processing_version}"
    doc.content = content
    doc.access_policy = source.access_policy

    doc.tenant = source.tenant
    doc.business_unit = source.business_unit
    doc.project = source.project
    doc.context = source.context
    doc.sub_context = source.sub_context
    doc.entity_type = source.entity_type
    doc.entity = source.entity
    doc.topic = source.topic
    doc.context_path = build_context_path(source)
    doc.priority = source.priority or 0
    doc.disabled = 0 if source.status == "Published" else 1

    doc.insert(ignore_permissions=True)

    return doc.name


def build_context_path(source):
    parts = [
        source.context,
        source.sub_context,
        source.entity_type,
        source.entity,
        source.topic,
    ]

    return "/".join([p for p in parts if p])


def get_text_hash(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def diagnose_chunk(chunk_content, chunk_hash, seen_hashes):
    character_count = len(chunk_content or "")

    if not chunk_content or not chunk_content.strip():
        return "Critical", "Empty chunk content"

    if character_count < 50:
        return "Warning", "Chunk is too small"

    if character_count > 6000:
        return "Warning", "Chunk is too large"

    if chunk_hash in seen_hashes:
        return "Warning", "Duplicate chunk content"

    return "Healthy", "Chunk passed diagnostics"