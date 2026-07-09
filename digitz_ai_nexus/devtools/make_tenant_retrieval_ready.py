"""
Make every Knowledge Source of a tenant retrieval-ready
========================================================
Runs the canonical per-source readiness pipeline
(digitz_ai_nexus.devtools.prepare_knowledge_source.run) for every Nexus Knowledge
Source of a tenant. The pipeline, in order, does:

  1. Process        — chunk + embed
  2. Index          — generate Intellectual Summaries + User Questions
  3. Approve answers — LLM validates each answer, then (bulk_approve) approves the
                       remaining Pending-Review answers so the whole set is retrievable
  4. Validate source — confirm retrieval works
  5. Test cases     — generate test cases
  6. Run tests      — execute them (retrieval_ready=1 only if all pass)
  7. Publish        — activate chunks, set status=Published + retrieval_ready=1

Before looping it switches the running user's ACTIVE TENANT to `tenant`, otherwise
the Studio validate/test/publish steps reject the sources with
"... is outside the active tenant context."

Idempotent: sources already Published + retrieval_ready are skipped
(skip_if_published), so re-running only finishes what isn't live yet.

Run (staging):
  bench --site digitz_ai_nexus_staging.site execute \
    digitz_ai_nexus.devtools.make_tenant_retrieval_ready.run \
    --kwargs "{'tenant':'DIGITZ-PRIME'}"

Production:
  bench --site nexusailive.com execute \
    digitz_ai_nexus.devtools.make_tenant_retrieval_ready.run \
    --kwargs "{'tenant':'DIGITZ-PRIME'}"

Force re-run of already-live sources:  add 'skip_if_published': False
Limit for a smoke test:                add 'limit': 1
"""

import frappe


def run(
    tenant="DIGITZ-PRIME",
    approve_all=True,
    test_count=8,
    generation_method="Heuristic",
    skip_if_published=True,
    min_pass_rate=0.8,
    limit=None,
):
    from digitz_ai_nexus.api.nexus_administration import set_active_user_context
    from digitz_ai_nexus.devtools.prepare_knowledge_source import run as prepare_source

    # Switch the running user's active tenant so Studio tenant guards pass.
    set_active_user_context(tenant=tenant)

    names = frappe.get_all(
        "Nexus Knowledge Source",
        filters={"tenant": tenant},
        pluck="name",
        order_by="name asc",
        limit_page_length=limit or 0,
    )
    if not names:
        print(f"No Nexus Knowledge Source found for tenant {tenant!r}")
        return {"tenant": tenant, "total": 0}

    prepared, skipped, failed = [], [], []
    for name in names:
        try:
            res = prepare_source(
                name,
                test_count=test_count,
                generation_method=generation_method,
                auto_publish=True,
                skip_if_published=skip_if_published,
                bulk_approve=approve_all,
                min_pass_rate=min_pass_rate,
            )
            if res.get("skipped"):
                skipped.append(name)
            elif res.get("success"):
                prepared.append(name)
            else:
                failed.append(
                    {"name": name, "step_failed": res.get("step_failed"), "error": res.get("error")}
                )
        except Exception as exc:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(), f"make_tenant_retrieval_ready: {name}")
            failed.append({"name": name, "error": str(exc)})
        finally:
            frappe.db.commit()

    processed = len(names)
    tenant_total = frappe.db.count("Nexus Knowledge Source", {"tenant": tenant})
    ready = frappe.db.count("Nexus Knowledge Source", {"tenant": tenant, "retrieval_ready": 1})
    print(
        f"\nTenant {tenant}: processed={processed} prepared={len(prepared)} "
        f"skipped={len(skipped)} failed={len(failed)} | "
        f"retrieval_ready={ready}/{tenant_total}"
    )
    return {
        "tenant": tenant,
        "processed": processed,
        "total": tenant_total,
        "prepared": len(prepared),
        "skipped": len(skipped),
        "failed": failed,
        "retrieval_ready_total": ready,
    }
