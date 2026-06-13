"""
Generate semantic index entries for all existing knowledge chunks
that don't already have index entries.

Run via:
    bench --site digitz_ai_nexus_live_test.site execute \
        digitz_ai_nexus.devtools.generate_all_index_entries.run
"""
import frappe


def run(generation_method="Heuristic", tenant_code=None):
    """
    Generate index entries for all chunks that have no existing index entry.
    Uses Heuristic mode by default (no LLM cost/latency).
    Set generation_method="LLM" to use the LLM for richer questions.
    """
    from digitz_ai_nexus.services.semantic_index import (
        generate_index_entries_for_chunks,
        has_semantic_index_doctype,
    )

    if not has_semantic_index_doctype():
        print("Nexus Knowledge Index Entry DocType not found. Aborting.")
        return

    # Find chunks with no existing index entry
    filters = {"archived": 0}
    if tenant_code:
        tenant = frappe.db.get_value("Nexus Tenant", {"tenant_code": tenant_code}, "name")
        if tenant:
            filters["tenant"] = tenant
        else:
            print(f"Tenant not found for code: {tenant_code}")
            return

    all_chunks = frappe.get_all(
        "Nexus Knowledge Chunk",
        filters=filters,
        pluck="name",
        limit_page_length=10000,
    )

    # Find chunks that already have index entries
    indexed_chunks = set()
    if frappe.db.exists("DocType", "Nexus Knowledge Index Entry"):
        existing = frappe.db.sql(
            "SELECT DISTINCT knowledge_chunk FROM `tabNexus Knowledge Index Entry`",
            pluck="knowledge_chunk",
        )
        indexed_chunks = set(existing)

    unindexed = [c for c in all_chunks if c not in indexed_chunks]

    print(f"Total chunks: {len(all_chunks)}")
    print(f"Already indexed: {len(indexed_chunks)}")
    print(f"Chunks to index: {len(unindexed)}")

    if not unindexed:
        print("All chunks already have index entries.")
        return {"created": 0, "failed": 0, "skipped": 0}

    result = generate_index_entries_for_chunks(
        unindexed,
        generation_method=generation_method,
    )

    frappe.db.commit()

    created = len(result.get("created", []))
    failed = len(result.get("failed", []))
    skipped = result.get("skipped", 0)

    print(f"\nDone.")
    print(f"  Index entries created: {created}")
    print(f"  Failed chunks:         {failed}")
    print(f"  Skipped:               {skipped}")

    if result.get("failed"):
        print("\nFailed chunks:")
        for f in result["failed"][:5]:
            print(f"  chunk={f.get('chunk')}: {str(f.get('error') or '')[:200]}")

    return result
