"""
Rebuild Nexus Question Correlation records for all knowledge sources
using their existing approved Nexus Knowledge Index Entry questions.

This is the fast, non-destructive alternative to full reprocessing.
It does NOT re-chunk, re-embed, or regenerate questions — it only
clears old correlation records and rebuilds them from currently
approved User Question index entries.

Run via:
    bench --site <site> execute \
        digitz_ai_nexus.devtools.rebuild_question_correlations.run

Optional keyword args:
    tenant_code   — restrict to a single tenant
    source_name   — rebuild for a single source by name
    minimum_score — minimum Jaccard/field score to create a correlation (default 0.35)
    max_related   — max related questions per source question (default 5)
    dry_run       — report approved question counts without writing correlations

Examples:
    bench --site mysite.local execute \
        digitz_ai_nexus.devtools.rebuild_question_correlations.run

    bench --site mysite.local execute \
        digitz_ai_nexus.devtools.rebuild_question_correlations.run \
        --kwargs '{"source_name": "KS-00001"}'
"""
import frappe


def run(
    tenant_code=None,
    source_name=None,
    minimum_score=0.35,
    max_related=5,
    dry_run=False,
):
    from digitz_ai_nexus.services.question_correlation import (
        has_question_correlation_doctype,
        get_active_source_questions,
        build_question_correlations_for_source,
    )

    if not has_question_correlation_doctype():
        print("Nexus Question Correlation DocType not found. Aborting.")
        return

    filters = {}

    if source_name:
        filters["name"] = source_name
    elif tenant_code:
        tenant = frappe.db.get_value("Nexus Tenant", {"tenant_code": tenant_code}, "name")
        if not tenant:
            print(f"Tenant not found for code: {tenant_code}")
            return
        filters["tenant"] = tenant

    sources = frappe.get_all(
        "Nexus Knowledge Source",
        filters=filters,
        fields=["name", "title", "status"],
        order_by="modified asc",
        limit_page_length=1000,
    )

    if not sources:
        print("No knowledge sources found matching the given filters.")
        return

    print(f"\nFound {len(sources)} knowledge source(s).")

    if dry_run:
        print("\n[DRY RUN] Approved question counts per source:\n")
        for s in sources:
            questions = get_active_source_questions(s.name)
            print(f"  {s.name} — {s.title}  approved_questions={len(questions)}")
        return

    print("")

    total_created = 0
    total_cleared = 0
    skipped = 0

    for i, s in enumerate(sources, start=1):
        label = f"({i}/{len(sources)}) {s.name} — {s.title}"
        print(f"  {label} ...", end=" ", flush=True)

        result = build_question_correlations_for_source(
            s.name,
            max_related=max_related,
            minimum_score=minimum_score,
        )

        if result.get("skipped"):
            reason = result.get("reason") or "skipped"
            print(f"SKIPPED ({reason})")
            skipped += 1
        else:
            created = result.get("created") or 0
            cleared = result.get("cleared") or 0
            total_created += created
            total_cleared += cleared
            print(f"OK  created={created}  cleared={cleared}")

    print(f"\n{'='*60}")
    print(f"Correlation rebuild complete.")
    print(f"  Sources processed : {len(sources) - skipped}")
    print(f"  Sources skipped   : {skipped}")
    print(f"  Old records cleared: {total_cleared}")
    print(f"  New correlations  : {total_created}")

    return {
        "sources_processed": len(sources) - skipped,
        "sources_skipped": skipped,
        "total_cleared": total_cleared,
        "total_created": total_created,
    }
