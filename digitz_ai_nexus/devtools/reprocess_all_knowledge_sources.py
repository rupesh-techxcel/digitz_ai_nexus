"""
Reprocess all existing knowledge sources through the full ingestion pipeline.

This recreates chunks, embeddings, semantic index entries (questions), LLM
validation, question correlations (Nexus Question Correlation), and context
summaries for every source in the system.

Run via:
    bench --site <site> execute \
        digitz_ai_nexus.devtools.reprocess_all_knowledge_sources.run

Optional keyword args:
    status      — only process sources with this status (default: all)
    tenant_code — restrict to a single tenant
    dry_run     — print what would be processed without actually running
    source_name — reprocess a single source by name

Examples:
    # All sources
    bench --site mysite.local execute \
        digitz_ai_nexus.devtools.reprocess_all_knowledge_sources.run

    # Published sources only
    bench --site mysite.local execute \
        digitz_ai_nexus.devtools.reprocess_all_knowledge_sources.run \
        --kwargs '{"status": "Published"}'

    # Dry run first
    bench --site mysite.local execute \
        digitz_ai_nexus.devtools.reprocess_all_knowledge_sources.run \
        --kwargs '{"dry_run": true}'
"""
import frappe


def run(status=None, tenant_code=None, dry_run=False, source_name=None):
    from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source

    filters = {}

    if source_name:
        filters["name"] = source_name
    else:
        if status:
            filters["status"] = status

        if tenant_code:
            tenant = frappe.db.get_value("Nexus Tenant", {"tenant_code": tenant_code}, "name")
            if not tenant:
                print(f"Tenant not found for code: {tenant_code}")
                return
            filters["tenant"] = tenant

    sources = frappe.get_all(
        "Nexus Knowledge Source",
        filters=filters,
        fields=["name", "title", "status", "processing_status"],
        order_by="modified asc",
        limit_page_length=1000,
    )

    if not sources:
        print("No knowledge sources found matching the given filters.")
        return

    print(f"\nFound {len(sources)} knowledge source(s) to reprocess.")
    if dry_run:
        print("\n[DRY RUN] The following sources would be reprocessed:\n")
        for s in sources:
            print(f"  [{s.status}] {s.name} — {s.title}")
        return

    print("")

    success_count = 0
    failed_count = 0
    failed_sources = []

    for i, s in enumerate(sources, start=1):
        label = f"({i}/{len(sources)}) {s.name} — {s.title}"
        print(f"  Processing {label} ...", end=" ", flush=True)

        try:
            result = process_knowledge_source(s.name)

            chunks = result.get("chunk_count") or 0
            entries = len(result.get("semantic_index_entries") or [])
            correlations_raw = result.get("question_correlations") or {}
            correlations = correlations_raw.get("created") if isinstance(correlations_raw, dict) else 0

            print(
                f"OK  chunks={chunks}  index_entries={entries}  "
                f"correlations={correlations or 0}"
            )
            success_count += 1

        except Exception as e:
            print(f"FAILED — {str(e)[:120]}")
            failed_count += 1
            failed_sources.append({"name": s.name, "title": s.title, "error": str(e)})

    print(f"\n{'='*60}")
    print(f"Reprocessing complete.")
    print(f"  Succeeded : {success_count}")
    print(f"  Failed    : {failed_count}")

    if failed_sources:
        print("\nFailed sources:")
        for f in failed_sources:
            print(f"  {f['name']} — {f['title']}")
            print(f"    Error: {f['error'][:200]}")

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_sources": failed_sources,
    }
