import frappe
from frappe import _
from digitz_ai_nexus.engine.chunking import split_text_into_chunks


@frappe.whitelist()
def generate_chunks(knowledge_unit: str, replace_existing: int = 1):
    """
    Generate Nexus Knowledge Chunk records from a Nexus Knowledge Unit.
    This does NOT generate embeddings yet.
    """

    if not knowledge_unit:
        frappe.throw(_("Knowledge Unit is required."))

    unit = frappe.get_doc("Nexus Knowledge Unit", knowledge_unit)

    if unit.status not in ["Approved", "Active"]:
        frappe.throw(_("Only Approved or Active Knowledge Units can be chunked."))

    if replace_existing:
        existing_chunks = frappe.get_all(
            "Nexus Knowledge Chunk",
            filters={"knowledge_unit": unit.name},
            pluck="name",
        )

        for chunk_name in existing_chunks:
            frappe.delete_doc("Nexus Knowledge Chunk", chunk_name, force=True)

    settings = frappe.get_single("Nexus Settings")

    chunk_size = settings.chunk_size or 800
    chunk_overlap = settings.chunk_overlap or 120

    chunks = split_text_into_chunks(
        unit.content,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    created = []

    for idx, chunk_text in enumerate(chunks, start=1):
        chunk = frappe.new_doc("Nexus Knowledge Chunk")

        chunk.knowledge_unit = unit.name
        chunk.tenant = unit.tenant
        chunk.business_unit = unit.business_unit
        chunk.project = unit.project
        chunk.disabled = 0
        chunk.chunk_index = idx
        chunk.priority = 0
        chunk.chunk_text = chunk_text

        chunk.context = unit.context
        chunk.sub_context = unit.sub_context
        chunk.entity_type = unit.entity_type
        chunk.entity = unit.entity
        chunk.topic = unit.topic
        chunk.context_path = unit.context_path

        chunk.access_policy = unit.default_access_policy
        chunk.sensitivity = unit.sensitivity

        chunk.embedding_status = "Pending"

        chunk.insert(ignore_permissions=True)
        created.append(chunk.name)

    unit.chunk_count = len(created)
    unit.embedding_status = "Pending" if created else "Failed"
    unit.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "knowledge_unit": unit.name,
        "chunks_created": len(created),
        "chunks": created,
    }