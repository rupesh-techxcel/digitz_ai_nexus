import os
import json
import frappe
from frappe.utils import now

from digitz_ai_nexus.engine.chunking import chunk_text
from digitz_ai_nexus.engine.embedding import generate_embedding


def process_knowledge_source(source_name):
    source = frappe.get_doc("Nexus Knowledge Source", source_name)

    try:
        source.db_set("processing_status", "Processing")
        source.db_set("error_log", "")

        text = extract_source_text(source)

        if not text or not text.strip():
            frappe.throw("No readable text found in knowledge source")

        delete_existing_chunks(source.name)

        chunks = chunk_text(text)

        created_count = 0
        
        knowledge_unit = get_or_create_knowledge_unit(source,text)
        
        for index, chunk in enumerate(chunks, start=1):
            chunk_content = chunk.get("text") if isinstance(chunk, dict) else str(chunk)

            if not chunk_content.strip():
                continue

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
            doc.embedding = json.dumps(embedding)
            doc.embedding_status = "Completed"
            doc.access_policy = source.access_policy
            doc.priority = source.priority or 0
            doc.disabled = 0 if source.status == "Published" else 1
            doc.insert(ignore_permissions=True)

            created_count += 1

        source.db_set("chunk_count", created_count)
        source.db_set("embedding_status", "Completed")
        source.db_set("processing_status", "Processed")
        source.db_set("last_processed_on", now())

        frappe.db.commit()

        return {
            "status": "success",
            "source": source.name,
            "chunk_count": created_count,
        }

    except Exception as e:
        source.db_set("processing_status", "Failed")
        source.db_set("embedding_status", "Failed")
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


def delete_existing_chunks(source_name):
    existing = frappe.get_all(
        "Nexus Knowledge Chunk",
        filters={"knowledge_source": source_name},
        pluck="name",
    )

    for name in existing:
        frappe.delete_doc(
            "Nexus Knowledge Chunk",
            name,
            ignore_permissions=True,
            force=True,
        )


def build_context_path(source):
    parts = [
        source.context,
        source.sub_context,
        source.entity_type,
        source.entity,
        source.topic,
    ]

    return "/".join([p for p in parts if p])

def get_or_create_knowledge_unit(source, content):
    existing = frappe.get_all(
        "Nexus Knowledge Unit",
        filters={
            "title": source.title
        },
        pluck="name",
        limit_page_length=1,
    )

    if existing:
        return existing[0]

    doc = frappe.new_doc("Nexus Knowledge Unit")
    doc.title = source.title
    doc.content = content
    doc.default_access_policy = source.access_policy

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