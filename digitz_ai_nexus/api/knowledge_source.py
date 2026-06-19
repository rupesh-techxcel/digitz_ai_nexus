import frappe

from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source


@frappe.whitelist()
def process(source_name):
    if not source_name:
        frappe.throw("Source Name is required")

    return process_knowledge_source(source_name)