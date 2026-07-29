# Copyright (c) 2026, Techxcel Technologies
"""Migrate-safe completion of the readiness pipeline for the DIGITZ docs knowledge.

`seed_digitz_docs_knowledge` creates, classifies and processes the Knowledge Sources for
the product documentation. That leaves them retrievable but `retrieval_ready = 0`: the
flag is only set once a source has been through the governance pipeline — semantic index
→ answer approval → source validation → test-case generation → test run → publish. The
canonical tool for that is `make_tenant_retrieval_ready`, which runs
`prepare_knowledge_source` over every source of a tenant.

That pipeline is LLM-billed and takes tens of minutes for a full docs set, so it cannot
run inline on `bench migrate`. This wrapper makes it deployable anyway:

  * it no-ops when every source of the tenant is already retrieval-ready — the normal
    case on a repeat migrate, and one cheap query;
  * otherwise it enqueues the work on the long queue, so the migrate returns immediately
    and the site finishes preparing itself in the background;
  * it saves and restores the running user's Studio working context, because
    `make_tenant_retrieval_ready` switches the *persisted* active tenant to reach the
    sources and would otherwise leave an admin pointed at DIGITZ-PRIME with their
    business unit, project and channel cleared.

Wired into `hooks.after_migrate`. Manual runs:

    # foreground (watch it work, e.g. on staging)
    bench --site <site> execute \\
        digitz_ai_nexus.devtools.ensure_docs_retrieval_ready.run \\
        --kwargs "{'enqueue': False}"

    # re-prepare everything, including sources that are already live
    bench --site <site> execute \\
        digitz_ai_nexus.devtools.ensure_docs_retrieval_ready.run \\
        --kwargs "{'force': True, 'enqueue': False}"
"""

import frappe

TENANT_CODE = "DIGITZ-PRIME"

# A full docs set is ~30 sources x 7 pipeline steps, each with LLM calls.
JOB_TIMEOUT = 7200
JOB_ID = "digitz-docs-retrieval-ready"

CONTEXT_FIELDS = (
	"active_tenant",
	"active_tenant_configuration",
	"active_business_unit",
	"active_project",
	"active_channel",
)


def pending_sources(tenant=TENANT_CODE):
	"""Sources of `tenant` that have not completed the readiness pipeline."""
	if not frappe.db.exists("DocType", "Nexus Knowledge Source"):
		return []
	return frappe.get_all(
		"Nexus Knowledge Source",
		filters={"tenant": tenant, "retrieval_ready": 0},
		pluck="name",
		order_by="name asc",
	)


def _saved_context():
	"""Current user's persisted Studio context, so the run can put it back."""
	name = frappe.db.get_value("Nexus User Context", {"user": frappe.session.user}, "name")
	if not name:
		return None
	values = frappe.db.get_value("Nexus User Context", name, CONTEXT_FIELDS, as_dict=True)
	return {"name": name, "values": values}


def _restore_context(saved):
	if not saved:
		return
	frappe.db.set_value(
		"Nexus User Context", saved["name"], dict(saved["values"]), update_modified=False
	)
	frappe.db.commit()


def prepare_tenant(tenant=TENANT_CODE, skip_if_published=True):
	"""Run the canonical readiness pipeline, leaving the Studio context as we found it."""
	from digitz_ai_nexus.devtools.make_tenant_retrieval_ready import run as make_ready

	saved = _saved_context()
	try:
		return make_ready(tenant=tenant, skip_if_published=skip_if_published)
	finally:
		_restore_context(saved)


def run(tenant=TENANT_CODE, enqueue=True, force=False):
	"""after_migrate entry point. Never raises — a migrate must not fail over this."""
	try:
		if not frappe.db.exists("Nexus Tenant", tenant):
			return {"tenant": tenant, "skipped": "tenant not found"}

		pending = pending_sources(tenant)
		if not pending and not force:
			return {"tenant": tenant, "pending": 0, "queued": False}

		if enqueue:
			frappe.enqueue(
				"digitz_ai_nexus.devtools.ensure_docs_retrieval_ready.prepare_tenant",
				queue="long",
				timeout=JOB_TIMEOUT,
				job_id=JOB_ID,
				deduplicate=True,
				tenant=tenant,
				skip_if_published=not force,
			)
			frappe.logger().info(
				f"DIGITZ docs readiness: queued {len(pending)} source(s) for tenant {tenant}."
			)
			return {"tenant": tenant, "pending": len(pending), "queued": True}

		result = prepare_tenant(tenant, skip_if_published=not force)
		return {"tenant": tenant, "pending": len(pending), "queued": False, "result": result}

	except Exception:
		frappe.log_error(frappe.get_traceback(), "DIGITZ docs retrieval-readiness failed")
		return {"error": True}
