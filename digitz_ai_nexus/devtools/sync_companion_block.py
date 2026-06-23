"""One-shot: sync the companion workspace HTML block CSS to the database."""
import json
import frappe


def sync_companion_workspace_block():
    FIXTURE_PATH = (
        "/home/rupesh/frappe-bench/apps/digitz_ai_nexus"
        "/digitz_ai_nexus/fixtures/custom_html_block.json"
    )
    block_name = "nexus-nexy-companion-workspace-html-block"

    with open(FIXTURE_PATH) as f:
        data = json.load(f)

    block_data = next((b for b in data if b["name"] == block_name), None)
    if not block_data:
        frappe.throw(f"Block {block_name} not found in fixture file")

    if not frappe.db.exists("Custom HTML Block", block_name):
        frappe.throw(f"Custom HTML Block {block_name} not in database — run bench migrate first")

    doc = frappe.get_doc("Custom HTML Block", block_name)
    doc.html = block_data["html"]
    doc.style = block_data["style"]
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "block": block_name,
        "html_len": len(doc.html or ""),
        "style_len": len(doc.style or ""),
    }
