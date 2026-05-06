import json
import frappe
from digitz_ai_nexus.engine.embedding import generate_embedding


@frappe.whitelist()
def generate_embeddings_for_unit(knowledge_unit: str):
    if not knowledge_unit:
        frappe.throw("Knowledge Unit is required")

    chunks = frappe.get_all(
        "Nexus Knowledge Chunk",
        filters={
            "knowledge_unit": knowledge_unit,
            "disabled": 0
        },
        fields=["name", "chunk_text"]
    )

    updated = []

    for row in chunks:
        chunk = frappe.get_doc("Nexus Knowledge Chunk", row.name)

        try:
            embedding = generate_embedding(chunk.chunk_text)

            chunk.embedding = json.dumps(embedding)
            chunk.embedding_model = frappe.get_single("Nexus Settings").embedding_model
            chunk.embedding_status = "Completed"

            chunk.save(ignore_permissions=True)
            updated.append(chunk.name)

        except Exception as e:
            chunk.embedding_status = "Failed"
            chunk.save(ignore_permissions=True)

            frappe.log_error(f"Embedding failed for {chunk.name}: {str(e)}")

    frappe.db.commit()

    return {
        "updated": len(updated),
        "chunks": updated
    }