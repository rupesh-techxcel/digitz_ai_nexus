import frappe

from digitz_ai_nexus.services.knowledge_source_defaults import (
    DEFAULT_KNOWLEDGE_SOURCE_ENTITY_TYPE,
)


def execute():
    if not frappe.db.exists("DocType", "Nexus Knowledge Source"):
        return
    if not frappe.get_meta("Nexus Knowledge Source").has_field("entity_type"):
        return

    frappe.db.sql(
        """update `tabNexus Knowledge Source`
           set entity_type = %s
           where coalesce(trim(entity_type), '') = ''""",
        DEFAULT_KNOWLEDGE_SOURCE_ENTITY_TYPE,
    )

    if frappe.get_meta("Nexus Knowledge Source").has_field("entity"):
        frappe.db.sql(
            """update `tabNexus Knowledge Source`
               set entity = coalesce(nullif(trim(title), ''), name)
               where coalesce(trim(entity), '') = ''"""
        )
