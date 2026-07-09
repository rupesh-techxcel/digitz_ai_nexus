"""
DIGITZ Prime Docs — public Q&A widget/channel seed
==================================================
Creates the minimal wiring so the docs "Ask Nexus AI" box can call the guest
endpoint `digitz_ai_nexus_live.api.live.ask_question` and get answers grounded in
the DIGITZ-PRIME public documentation knowledge:

  Nexus Live Channel   DIGITZ-PRIME-DOCS-QA   (Website Q&A, agent_based=0 — direct RAG)
  Nexus Website Widget DIGITZ-PRIME-DOCS      (allowed origins for the docs site)

Public (guest) Q&A resolves the tenant's public access categories, which map to the
Public policy — the same policy the docs Knowledge Sources carry — so retrieval is
scoped to the docs knowledge.

Idempotent. Run:
  bench --site <site> execute digitz_ai_nexus.devtools.seed_digitz_prime_docs_widget.run
Add/adjust allowed origins:
  ... .run --kwargs "{'origins':['https://digitzprime.com','http://127.0.0.1:8512']}"
"""

import json

import frappe

TENANT = "DIGITZ-PRIME"
CHANNEL_CODE = "DIGITZ-PRIME-DOCS-QA"
WIDGET_CODE = "DIGITZ-PRIME-DOCS"

DEFAULT_ORIGINS = [
	"https://digitzprime.com",
	"https://www.digitzprime.com",
	"https://nexusailive.com",
	"http://127.0.0.1:8512",
	"http://localhost:8512",
]


def _ensure_channel():
	name = frappe.db.get_value(
		"Nexus Live Channel", {"channel_code": CHANNEL_CODE, "tenant": TENANT}, "name"
	)
	doc = frappe.get_doc("Nexus Live Channel", name) if name else frappe.new_doc("Nexus Live Channel")
	if not name:
		doc.channel_code = CHANNEL_CODE
		doc.tenant = TENANT
	doc.channel_name = "DIGITZ Prime Docs Q&A"
	doc.channel_type = "Website Q&A"
	doc.enabled = 1
	doc.agent_based = 0
	doc.requires_visitor_email = 0
	if doc.meta.has_field("description"):
		doc.description = "Public Q&A channel for the DIGITZ Prime documentation hub."
	doc.save(ignore_permissions=True)
	return doc.name


def _ensure_widget(channel, origins):
	doc = (
		frappe.get_doc("Nexus Website Widget", WIDGET_CODE)
		if frappe.db.exists("Nexus Website Widget", WIDGET_CODE)
		else frappe.new_doc("Nexus Website Widget")
	)
	if not doc.get("widget_code"):
		doc.widget_code = WIDGET_CODE
	doc.widget_name = "DIGITZ Prime Docs"
	doc.channel = channel
	doc.enabled = 1
	doc.knowledge_delivery_enabled = 1
	doc.allowed_domains_json = json.dumps(origins)
	# Also fill the child table when present so the desk UI shows the origins.
	if doc.meta.has_field("allowed_domains"):
		doc.set("allowed_domains", [])
		for o in origins:
			doc.append("allowed_domains", {"domain": o})
	doc.save(ignore_permissions=True)
	return doc.name


def run(origins=None):
	origins = origins or DEFAULT_ORIGINS
	if isinstance(origins, str):
		origins = frappe.parse_json(origins)

	if not frappe.db.exists("Nexus Tenant", TENANT):
		frappe.throw(f"Tenant {TENANT} not found — run the docs knowledge seed first.")

	channel = _ensure_channel()
	widget = _ensure_widget(channel, origins)
	frappe.db.commit()

	print(f"Channel: {channel}\nWidget : {widget} (code={WIDGET_CODE})\nOrigins: {origins}")
	return {"channel": channel, "widget": widget, "widget_code": WIDGET_CODE, "origins": origins}
