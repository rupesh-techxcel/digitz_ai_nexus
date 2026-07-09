"""
DIGITZ Prime Docs — Public Knowledge Seed
=========================================
Idempotent seed that turns the exported DIGITZ product documentation into retrievable
Nexus Knowledge Sources, so the docs "Ask Nexus AI" box can answer from them.

Content origin: `App Documentation` on digitz_prime.site is flattened (one entry per
doc section) by `digitz_prime.devtools.export_docs_knowledge.run` into
`digitz_ai_nexus/data/digitz_docs_knowledge.json`, which is committed to this app.
This seed reads that file — it does NOT need the digitz_prime site.

Taxonomy created (all under the DIGITZ-PRIME tenant):
    Nexus Tenant        DIGITZ-PRIME
    Nexus Business Unit DIGITZ Prime
    Nexus Access Policy Public  (via seed_default_access_governance)
    Nexus Access Category  Public Docs  -> Public policy
    Nexus Knowledge Source (one per doc section, Public, Published)

Safe to run on every migrate: create-if-missing for the foundation, content-guarded
upsert for sources (never deletes, never clobbers human classification edits), and
processing is only (re)triggered when a section's text actually changed.

Wired into hooks.after_migrate. Manual run:
    bench --site <site> execute digitz_ai_nexus.devtools.seed_digitz_docs_knowledge.run
    # synchronous processing (see chunks/embeddings immediately):
    bench --site <site> execute digitz_ai_nexus.devtools.seed_digitz_docs_knowledge.run --kwargs "{'enqueue': False}"
"""

import json
import os

import frappe

from digitz_ai_nexus.setup.access_seed import (
	ensure_access_category,
	seed_default_access_governance,
)
from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source

TENANT_CODE = "DIGITZ-PRIME"
TENANT_NAME = "DIGITZ Prime"
BUSINESS_UNIT = "DIGITZ Prime"
DOCS_CATEGORY = "Public Docs"
ENTITY_TYPE = "Feature"
DATA_REL = ("data", "digitz_docs_knowledge.json")


def _ensure_tenant():
	existing = frappe.db.get_value("Nexus Tenant", {"tenant_code": TENANT_CODE}, "name")
	if existing:
		doc = frappe.get_doc("Nexus Tenant", existing)
	else:
		doc = frappe.new_doc("Nexus Tenant")
		doc.tenant_code = TENANT_CODE
	doc.tenant_name = TENANT_NAME
	doc.disabled = 0
	doc.description = "Tenant for DIGITZ Prime public product documentation knowledge."
	doc.save(ignore_permissions=True)
	return doc.name


def _ensure_business_unit(tenant):
	if frappe.db.exists("Nexus Business Unit", BUSINESS_UNIT):
		return BUSINESS_UNIT
	doc = frappe.new_doc("Nexus Business Unit")
	doc.business_unit_name = BUSINESS_UNIT
	if doc.meta.has_field("tenant"):
		doc.tenant = tenant
	if doc.meta.has_field("enabled"):
		doc.enabled = 1
	doc.insert(ignore_permissions=True)
	return doc.name


def _load_entries():
	path = frappe.get_app_path("digitz_ai_nexus", *DATA_REL)
	if not os.path.exists(path):
		frappe.logger().warning(f"DIGITZ docs seed: data file not found at {path}")
		return []
	with open(path) as f:
		return (json.load(f) or {}).get("entries", [])


def _upsert_source(entry, tenant, policy):
	"""Create or content-update one Knowledge Source. Returns (doc, changed)."""
	title = entry["title"]
	content = (entry.get("content") or "").strip()

	if frappe.db.exists("Nexus Knowledge Source", title):
		doc = frappe.get_doc("Nexus Knowledge Source", title)
		# Preserve any human edits to classification — only refresh the body when the
		# source docs actually changed, and re-publish so processing re-activates chunks.
		if (doc.manual_content or "").strip() == content:
			return doc, False
		doc.manual_content = content
		doc.status = "Published"
		doc.save(ignore_permissions=True)
		return doc, True

	doc = frappe.new_doc("Nexus Knowledge Source")
	doc.title = title
	doc.source_type = "Manual"
	doc.manual_content = content
	doc.tenant = tenant
	doc.business_unit = BUSINESS_UNIT
	doc.context = entry.get("context") or ""
	doc.sub_context = entry.get("sub_context") or ""
	doc.entity_type = ENTITY_TYPE
	doc.entity = entry.get("entity") or ""
	doc.topic = entry.get("topic") or ""
	doc.intent = f"What is / how to use {entry.get('topic') or title}"
	doc.access_policy = policy
	doc.status = "Published"
	doc.priority = 5
	doc.save(ignore_permissions=True)
	return doc, True


def run(enqueue=True, process_sources=True):
	"""Seed DIGITZ docs knowledge. Defensive: never aborts a migrate.

	enqueue=True   -> processing runs in a background job (migrate-safe default).
	enqueue=False  -> process synchronously (useful for local verification).
	process_sources=False -> create/update sources but skip embedding entirely.
	"""
	try:
		tenant = _ensure_tenant()
		seed_default_access_governance(tenant=tenant)
		_ensure_business_unit(tenant)

		# Access Policy autoname is "Public-<tenant>", so resolve the real doc name.
		public_policy = (
			frappe.db.get_value("Nexus Access Policy", {"policy_name": "Public", "tenant": tenant}, "name")
			or frappe.db.get_value("Nexus Access Policy", {"policy_name": "Public"}, "name")
			or "Public"
		)
		ensure_access_category(
			DOCS_CATEGORY,
			[public_policy],
			title="Public Docs",
			description="DIGITZ product documentation — public knowledge for the docs Ask Nexus AI.",
			tenant=tenant,
		)
		frappe.db.commit()

		entries = _load_entries()
		upserted = 0
		pending_sources = []
		for entry in entries:
			doc, changed = _upsert_source(entry, tenant, public_policy)
			upserted += 1
			# Process when the body changed OR the source was never fully embedded
			# (self-heals sources created with process_sources=False or a failed job).
			if changed or (doc.get("embedding_status") or "Pending") != "Completed":
				pending_sources.append(doc.name)
		frappe.db.commit()

		processed = 0
		if process_sources:
			for name in pending_sources:
				try:
					if enqueue:
						frappe.enqueue(
							"digitz_ai_nexus.services.ingestion.processor.process_knowledge_source",
							queue="long",
							source_name=name,
						)
					else:
						process_knowledge_source(name)
					processed += 1
				except Exception:
					frappe.log_error(
						frappe.get_traceback(), f"DIGITZ docs seed: processing failed for {name}"
					)
			frappe.db.commit()

		frappe.logger().info(
			f"DIGITZ docs knowledge seed: {upserted} sources, {processed} "
			f"{'enqueued' if enqueue else 'processed'}, tenant {tenant}."
		)
		return {
			"tenant": tenant,
			"upserted": upserted,
			"pending": len(pending_sources),
			"processed": processed,
			"total_entries": len(entries),
		}
	except Exception:
		# after_migrate must never break the migrate over documentation seeding.
		frappe.log_error(frappe.get_traceback(), "DIGITZ docs knowledge seed failed")
		return {"error": True}
