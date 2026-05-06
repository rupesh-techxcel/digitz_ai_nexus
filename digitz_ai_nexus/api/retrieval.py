import json
import frappe

from digitz_ai_nexus.engine.retrieval import retrieve_allowed_chunks

@frappe.whitelist()
def test_retrieval(payload=None):
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not payload:
        payload = frappe.local.form_dict

    return retrieve_allowed_chunks(payload)