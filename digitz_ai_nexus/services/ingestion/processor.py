import os
import hashlib
import frappe

from digitz_ai_nexus.services.ingestion.parser_pdf import extract_pdf_text
from digitz_ai_nexus.services.ingestion.parser_docx import extract_docx_text
from digitz_ai_nexus.services.ingestion.parser_txt import extract_txt_text
from digitz_ai_nexus.services.ingestion.normalizer import normalize_text
from digitz_ai_nexus.services.ingestion.chunker import chunk_text
from digitz_ai_nexus.services.ingestion.embeddings import generate_embedding_json
from digitz_ai_nexus.services.semantic_index import (
    archive_existing_index_entries,
    generate_index_entries_for_chunks,
    refresh_context_summaries_for_chunks,
)
from digitz_ai_nexus.services.question_correlation import (
    build_question_correlations_for_source,
)


def set_if_field(doc, fieldname, value):
    if value is None:
        return

    if not doc.meta.has_field(fieldname):
        return

    table_columns = frappe.db.get_table_columns(doc.doctype)

    if fieldname not in table_columns:
        return

    doc.set(fieldname, value)


def get_text_hash(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def diagnose_chunk(chunk_text_value, chunk_hash, seen_hashes):
    text = (chunk_text_value or "").strip()
    length = len(text)

    if not text:
        return "Critical", "Empty chunk content"

    if length < 50:
        return "Warning", "Chunk is too small"

    if length > 6000:
        return "Warning", "Chunk is too large"

    if chunk_hash in seen_hashes:
        return "Warning", "Duplicate chunk content"

    return "Healthy", "Chunk passed diagnostics"


def archive_existing_chunks(source_name):
    existing = frappe.get_all(
        "Nexus Knowledge Chunk",
        filters={"knowledge_source": source_name},
        pluck="name",
    )

    for chunk_name in existing:
        chunk_doc = frappe.get_doc("Nexus Knowledge Chunk", chunk_name)

        set_if_field(chunk_doc, "archived", 1)
        set_if_field(chunk_doc, "disabled", 1)
        set_if_field(chunk_doc, "is_active", 0)
        set_if_field(chunk_doc, "enabled", 0)

        chunk_doc.save(ignore_permissions=True)


def disable_existing_knowledge_units(source_doc):
    old_unit = source_doc.get("generated_knowledge_unit") or source_doc.get("knowledge_unit")

    if not old_unit:
        return

    if not frappe.db.exists("Nexus Knowledge Unit", old_unit):
        return

    unit_doc = frappe.get_doc("Nexus Knowledge Unit", old_unit)

    set_if_field(unit_doc, "disabled", 1)
    set_if_field(unit_doc, "is_active", 0)
    set_if_field(unit_doc, "enabled", 0)
    set_if_field(unit_doc, "status", "Archived")

    unit_doc.save(ignore_permissions=True)


def get_file_path(file_url):
    if not file_url:
        return None

    file_doc = frappe.get_doc("File", {"file_url": file_url})
    return file_doc.get_full_path()


def detect_source_type(source_doc):
    source_type = (
        source_doc.get("source_type")
        or source_doc.get("file_type")
        or ""
    ).strip().lower()

    file_url = source_doc.get("source_file") or source_doc.get("file") or ""

    if source_type:
        return source_type

    ext = os.path.splitext(file_url)[1].lower()

    if ext == ".pdf":
        return "pdf"

    if ext == ".docx":
        return "docx"

    if ext == ".txt":
        return "txt"

    if source_doc.get("manual_content") or source_doc.get("raw_text"):
        return "manual"

    return ""


def extract_source_text(source_doc):
    source_type = detect_source_type(source_doc)

    if source_type in ["manual", "text", "manual text"]:
        return source_doc.get("manual_content") or source_doc.get("raw_text") or ""

    file_url = source_doc.get("source_file") or source_doc.get("file")

    if not file_url:
        frappe.throw("No source file found for this Knowledge Source.")

    file_path = get_file_path(file_url)

    if not file_path or not os.path.exists(file_path):
        frappe.throw("Uploaded source file could not be found on disk.")

    if source_type == "pdf":
        return extract_pdf_text(file_path)

    if source_type == "docx":
        return extract_docx_text(file_path)

    if source_type == "txt":
        return extract_txt_text(file_path)

    frappe.throw(f"Unsupported source type: {source_type}")


def create_knowledge_unit(source_doc, normalized_text, processing_version):
    unit = frappe.new_doc("Nexus Knowledge Unit")

    base_title = source_doc.get("title") or source_doc.get("source_name") or source_doc.name
    title = f"{base_title} - v{processing_version}"

    context = source_doc.get("context") or "General"
    sub_context = source_doc.get("sub_context") or "General"
    entity_type = source_doc.get("entity_type") or "Knowledge Source"
    entity = source_doc.get("entity") or base_title
    topic = source_doc.get("topic") or base_title

    access_policy = (
        source_doc.get("default_access_policy")
        or source_doc.get("access_policy")
        or "Public"
    )

    set_if_field(unit, "title", title)
    set_if_field(unit, "tenant", source_doc.get("tenant"))
    set_if_field(unit, "business_unit", source_doc.get("business_unit"))
    set_if_field(unit, "project", source_doc.get("project"))

    set_if_field(unit, "source", source_doc.name)
    set_if_field(unit, "knowledge_source", source_doc.name)

    set_if_field(unit, "content", normalized_text)
    set_if_field(unit, "raw_text", normalized_text)
    set_if_field(unit, "status", "Approved")

    set_if_field(unit, "context", context)
    set_if_field(unit, "sub_context", sub_context)
    set_if_field(unit, "entity_type", entity_type)
    set_if_field(unit, "entity", entity)
    set_if_field(unit, "topic", topic)

    set_if_field(
        unit,
        "context_path",
        source_doc.get("context_path") or f"{context}/{sub_context}/{entity_type}/{entity}/{topic}",
    )

    set_if_field(unit, "scope_type", source_doc.get("scope_type") or "general")
    set_if_field(unit, "default_access_policy", access_policy)
    set_if_field(unit, "access_policy", access_policy)
    set_if_field(unit, "priority", source_doc.get("priority") or 0)
    set_if_field(unit, "allowed_roles", source_doc.get("allowed_roles"))
    set_if_field(unit, "denied_roles", source_doc.get("denied_roles"))
    set_if_field(unit, "disabled", 0 if source_doc.get("status") == "Published" else 1)

    unit.insert(ignore_permissions=True)
    return unit


def create_knowledge_chunks(source_doc, unit_doc, chunks, processing_version):
    created = []
    embedded_count = 0
    warning_count = 0
    critical_count = 0
    seen_hashes = set()

    title = unit_doc.get("title") or unit_doc.name

    context = source_doc.get("context") or unit_doc.get("context") or "General"
    sub_context = source_doc.get("sub_context") or unit_doc.get("sub_context") or "General"
    entity_type = source_doc.get("entity_type") or unit_doc.get("entity_type") or "Knowledge Source"
    entity = source_doc.get("entity") or unit_doc.get("entity") or title
    topic = source_doc.get("topic") or unit_doc.get("topic") or title

    context_path = (
        source_doc.get("context_path")
        or unit_doc.get("context_path")
        or f"{context}/{sub_context}/{entity_type}/{entity}/{topic}"
    )

    access_policy = (
        source_doc.get("default_access_policy")
        or source_doc.get("access_policy")
        or unit_doc.get("default_access_policy")
        or unit_doc.get("access_policy")
        or "Public"
    )

    scope_type = source_doc.get("scope_type") or unit_doc.get("scope_type") or "general"
    priority = source_doc.get("priority") or unit_doc.get("priority") or 0

    for index, chunk in enumerate(chunks, start=1):
        chunk_text_value = str(chunk or "").strip()

        if not chunk_text_value:
            continue

        chunk_hash = get_text_hash(chunk_text_value)

        diagnostics_status, diagnostics_message = diagnose_chunk(
            chunk_text_value,
            chunk_hash,
            seen_hashes,
        )

        if diagnostics_status == "Critical":
            critical_count += 1
        elif diagnostics_status == "Warning":
            warning_count += 1

        seen_hashes.add(chunk_hash)

        chunk_doc = frappe.new_doc("Nexus Knowledge Chunk")

        set_if_field(chunk_doc, "title", f"{title} - Chunk {index}")
        set_if_field(chunk_doc, "knowledge_unit", unit_doc.name)
        set_if_field(chunk_doc, "source", source_doc.name)
        set_if_field(chunk_doc, "knowledge_source", source_doc.name)

        set_if_field(chunk_doc, "chunk_index", index)
        set_if_field(chunk_doc, "chunk_no", index)
        set_if_field(chunk_doc, "chunk_text", chunk_text_value)
        set_if_field(chunk_doc, "content", chunk_text_value)
        set_if_field(chunk_doc, "text", chunk_text_value)
        set_if_field(chunk_doc, "chunk_hash", chunk_hash)
        set_if_field(chunk_doc, "character_count", len(chunk_text_value))
        set_if_field(chunk_doc, "source_version", processing_version)
        set_if_field(chunk_doc, "priority", priority)

        set_if_field(chunk_doc, "tenant", source_doc.get("tenant") or unit_doc.get("tenant"))
        set_if_field(chunk_doc, "business_unit", source_doc.get("business_unit") or unit_doc.get("business_unit"))
        set_if_field(chunk_doc, "project", source_doc.get("project") or unit_doc.get("project"))

        set_if_field(chunk_doc, "context", context)
        set_if_field(chunk_doc, "sub_context", sub_context)
        set_if_field(chunk_doc, "entity_type", entity_type)
        set_if_field(chunk_doc, "entity", entity)
        set_if_field(chunk_doc, "topic", topic)
        set_if_field(chunk_doc, "context_path", context_path)
        set_if_field(chunk_doc, "scope_type", scope_type)

        set_if_field(chunk_doc, "default_access_policy", access_policy)
        set_if_field(chunk_doc, "access_policy", access_policy)

        set_if_field(chunk_doc, "allowed_roles", source_doc.get("allowed_roles") or unit_doc.get("allowed_roles"))
        set_if_field(chunk_doc, "denied_roles", source_doc.get("denied_roles") or unit_doc.get("denied_roles"))

        set_if_field(chunk_doc, "status", "Approved")
        set_if_field(chunk_doc, "archived", 0)
        set_if_field(chunk_doc, "disabled", 0 if source_doc.get("status") == "Published" else 1)
        set_if_field(chunk_doc, "is_active", 1 if source_doc.get("status") == "Published" else 0)
        set_if_field(chunk_doc, "enabled", 1 if source_doc.get("status") == "Published" else 0)

        set_if_field(chunk_doc, "diagnostics_status", diagnostics_status)
        set_if_field(chunk_doc, "diagnostics_message", diagnostics_message)

        try:
            embedding_json = generate_embedding_json(chunk_text_value)
            set_if_field(chunk_doc, "embedding", embedding_json)
            set_if_field(chunk_doc, "embedding_status", "Completed")
            embedded_count += 1
        except Exception:
            set_if_field(chunk_doc, "embedding_status", "Failed")
            set_if_field(chunk_doc, "embedding_error", frappe.get_traceback())

        chunk_doc.insert(ignore_permissions=True)
        created.append(chunk_doc.name)

    return {
        "created_chunks": created,
        "embedded_count": embedded_count,
        "warning_count": warning_count,
        "critical_count": critical_count,
    }


def get_embedding_status_for_chunks(chunk_names):
    if not chunk_names:
        return "Pending"

    chunks = frappe.get_all(
        "Nexus Knowledge Chunk",
        filters={"name": ["in", chunk_names]},
        fields=["name", "embedding"]
    )

    if not chunks:
        return "Pending"

    embedded_count = len([row for row in chunks if row.get("embedding")])

    if embedded_count == len(chunks):
        return "Completed"

    if embedded_count > 0:
        return "Pending"

    return "Failed"


@frappe.whitelist()
def process_knowledge_source(source_name):
    if not source_name:
        frappe.throw("Knowledge Source is required.")

    source_doc = frappe.get_doc("Nexus Knowledge Source", source_name)

    try:
        set_if_field(source_doc, "processing_status", "Processing")
        set_if_field(source_doc, "embedding_status", "Pending")
        set_if_field(source_doc, "diagnostics_status", "Pending")
        set_if_field(source_doc, "retrieval_ready", 0)
        set_if_field(source_doc, "error_log", "")
        set_if_field(source_doc, "processing_log", "")
        source_doc.save(ignore_permissions=True)
        frappe.db.commit()

        raw_text = extract_source_text(source_doc)
        normalized_text = normalize_text(raw_text)

        if not normalized_text:
            frappe.throw("No readable text could be extracted from this source.")

        next_version = int(source_doc.get("processing_version") or 0) + 1

        archive_existing_chunks(source_doc.name)
        archived_index_count = archive_existing_index_entries(source_doc.name)
        disable_existing_knowledge_units(source_doc)

        chunks = chunk_text(normalized_text, chunk_size=650, overlap=100)

        if not chunks:
            frappe.throw("No chunks could be generated from this source.")

        unit_doc = create_knowledge_unit(source_doc, normalized_text, next_version)
        chunk_result = create_knowledge_chunks(source_doc, unit_doc, chunks, next_version)

        created_chunks = chunk_result["created_chunks"]
        embedded_count = chunk_result["embedded_count"]
        warning_count = chunk_result["warning_count"]
        critical_count = chunk_result["critical_count"]
        index_result = generate_index_entries_for_chunks(
            created_chunks,
            generation_method="LLM",
        )

        # LLM validates each generated question by attempting to answer it from
        # the chunk. Auto-approves if answerable, auto-rejects if not.
        from digitz_ai_nexus.services.semantic_index import validate_source_questions_with_llm
        validate_source_questions_with_llm(source_doc.name)

        question_correlation_result = build_question_correlations_for_source(source_doc.name)

        context_summary_result = refresh_context_summaries_for_chunks(
            created_chunks,
            generation_method="LLM",
        )

        embedding_status = get_embedding_status_for_chunks(created_chunks)
        processed_time = frappe.utils.now()

        if critical_count > 0:
            diagnostics_status = "Critical"
        elif warning_count > 0:
            diagnostics_status = "Warning"
        elif created_chunks:
            diagnostics_status = "Healthy"
        else:
            diagnostics_status = "Critical"

        # Strict governance: newly generated possible-question answers must be
        # manually approved before a processed source becomes retrieval-ready.
        retrieval_ready = False

        set_if_field(unit_doc, "embedding_status", embedding_status)
        set_if_field(unit_doc, "chunk_count", len(created_chunks))
        set_if_field(unit_doc, "last_processed_on", processed_time)
        set_if_field(unit_doc, "processed_on", processed_time)
        unit_doc.save(ignore_permissions=True)

        preview_text = normalized_text[:5000] if normalized_text else ""

        set_if_field(source_doc, "raw_text", normalized_text)
        set_if_field(source_doc, "extracted_text_preview", preview_text)

        set_if_field(source_doc, "knowledge_unit", unit_doc.name)
        set_if_field(source_doc, "generated_knowledge_unit", unit_doc.name)

        set_if_field(source_doc, "processing_version", next_version)
        set_if_field(source_doc, "chunk_count", len(created_chunks))
        set_if_field(source_doc, "active_chunk_count", len(created_chunks) if source_doc.get("status") == "Published" else 0)
        set_if_field(source_doc, "processing_status", "Processed")
        set_if_field(source_doc, "embedding_status", embedding_status)
        set_if_field(source_doc, "diagnostics_status", diagnostics_status)
        set_if_field(source_doc, "retrieval_ready", 1 if retrieval_ready else 0)

        set_if_field(source_doc, "processed_on", processed_time)
        set_if_field(source_doc, "last_processed_on", processed_time)
        set_if_field(source_doc, "processed_by", frappe.session.user)

        success_log = (
            f"Processed successfully. Created Knowledge Unit {unit_doc.name} "
            f"and {len(created_chunks)} chunks. Created "
            f"{len(index_result.get('created') or [])} semantic index entries. "
            f"Created {question_correlation_result.get('created') or 0} question correlations. "
            f"Updated {len(context_summary_result.get('updated') or [])} grouped context summaries. "
            f"Archived {archived_index_count} old semantic index entries. "
            f"Version {next_version}."
        )

        set_if_field(source_doc, "processing_log", success_log)
        set_if_field(source_doc, "error_log", "")

        source_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "source": source_doc.name,
            "knowledge_unit": unit_doc.name,
            "generated_knowledge_unit": unit_doc.name,
            "processing_version": next_version,
            "chunk_count": len(created_chunks),
            "active_chunk_count": len(created_chunks) if source_doc.get("status") == "Published" else 0,
            "embedding_status": embedding_status,
            "diagnostics_status": diagnostics_status,
            "retrieval_ready": 1 if retrieval_ready else 0,
            "chunks": created_chunks,
            "semantic_index_entries": index_result.get("created") or [],
            "semantic_index_failed": index_result.get("failed") or [],
            "context_summaries": context_summary_result.get("updated") or [],
            "context_summary_failed": context_summary_result.get("failed") or [],
        }

    except Exception as e:
        frappe.db.rollback()

        source_doc = frappe.get_doc("Nexus Knowledge Source", source_name)
        traceback = frappe.get_traceback()

        set_if_field(source_doc, "processing_status", "Failed")
        set_if_field(source_doc, "embedding_status", "Failed")
        set_if_field(source_doc, "diagnostics_status", "Critical")
        set_if_field(source_doc, "retrieval_ready", 0)
        set_if_field(source_doc, "processing_log", traceback)
        set_if_field(source_doc, "error_log", traceback)
        set_if_field(source_doc, "last_processed_on", frappe.utils.now())

        source_doc.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.throw(str(e))
