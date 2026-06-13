import frappe


def count_all():
    """Quick diagnostic for index entry counts and processing logs."""
    # Count index entries
    index_count = frappe.db.count("Nexus Knowledge Index Entry") if frappe.db.exists("DocType", "Nexus Knowledge Index Entry") else -1
    chunk_count = frappe.db.count("Nexus Knowledge Chunk") if frappe.db.exists("DocType", "Nexus Knowledge Chunk") else -1
    source_count = frappe.db.count("Nexus Knowledge Source") if frappe.db.exists("DocType", "Nexus Knowledge Source") else -1

    print(f"Knowledge Sources: {source_count}")
    print(f"Knowledge Chunks:  {chunk_count}")
    print(f"Index Entries:     {index_count}")

    # Show sample source data via raw SQL (avoids missing column issues)
    if source_count and source_count > 0:
        sources = frappe.db.sql(
            "SELECT name, processing_status, chunk_count FROM `tabNexus Knowledge Source` LIMIT 3",
            as_dict=True,
        )
        for s in sources:
            print(f"\nSource: {s.name}")
            print(f"  processing_status: {s.processing_status}")
            print(f"  chunk_count: {s.chunk_count}")

    # Count entries per type
    if index_count and index_count > 0:
        rows = frappe.db.sql(
            "SELECT entry_type, status, disabled, COUNT(*) as cnt FROM `tabNexus Knowledge Index Entry` GROUP BY entry_type, status, disabled",
            as_dict=True,
        )
        print("\nIndex entry breakdown:")
        for r in rows:
            print(f"  type={r.entry_type} status={r.status} disabled={r.disabled} count={r.cnt}")

    # Check for failed log entries
    failed_logs = frappe.get_all(
        "Error Log",
        filters={"method": ("like", "%Semantic Index%")},
        fields=["name", "method", "error"],
        limit=3,
        order_by="creation desc",
    )
    if failed_logs:
        print("\nRecent Semantic Index errors:")
        for log in failed_logs:
            print(f"  [{log.name}] {log.method}: {(log.error or '')[:200]}")

    return {
        "source_count": source_count,
        "chunk_count": chunk_count,
        "index_count": index_count,
    }
