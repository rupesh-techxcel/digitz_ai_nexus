import frappe


def execute():
    if frappe.db.table_exists("tabNexus Role Access Category"):
        frappe.db.sql("DROP TABLE `tabNexus Role Access Category`")

    if frappe.db.exists("DocType", "Nexus Role Access Category"):
        frappe.delete_doc("DocType", "Nexus Role Access Category", ignore_missing=True, force=True)

    frappe.db.commit()
