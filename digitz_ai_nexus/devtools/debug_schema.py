import frappe


def check_schema():
    """Test creating index entries from existing chunks to find the root cause."""
    # Get first 3 chunk names
    chunk_names = frappe.db.sql(
        "SELECT name FROM `tabNexus Knowledge Chunk` LIMIT 3",
        pluck="name",
    )
    print(f"Testing with chunks: {chunk_names}")

    from digitz_ai_nexus.services.semantic_index import (
        generate_index_entries_for_chunks,
        create_index_entry,
        build_index_payloads,
    )

    # Test the full function
    result = generate_index_entries_for_chunks(
        chunk_names,
        generation_method="Heuristic",
    )
    print(f"\ngenerate_index_entries_for_chunks result:")
    print(f"  created: {len(result.get('created', []))}")
    print(f"  skipped: {result.get('skipped', 0)}")
    failed = result.get("failed", [])
    print(f"  failed:  {len(failed)}")
    for f in failed:
        print(f"  FAILED chunk={f.get('chunk')}")
        print(f"    error: {str(f.get('error') or '')[:400]}")

    # Manually test create_index_entry for 1 chunk
    if chunk_names:
        chunk_doc = frappe.get_doc("Nexus Knowledge Chunk", chunk_names[0])
        payloads = build_index_payloads(chunk_doc, generation_method="Heuristic")
        print(f"\nManual create_index_entry test (chunk={chunk_names[0]}):")
        print(f"  payloads: {len(payloads)}")
        if payloads:
            try:
                name = create_index_entry(chunk_doc, payloads[0])
                print(f"  created entry: {name}")
            except Exception:
                print(f"  EXCEPTION: {frappe.get_traceback()}")

    frappe.db.commit()
