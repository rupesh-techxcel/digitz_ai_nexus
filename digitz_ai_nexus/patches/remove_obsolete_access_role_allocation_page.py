import frappe


def execute():
    old_page = "nexus-access-role-allocation"
    if frappe.db.exists("Page", old_page):
        frappe.delete_doc("Page", old_page, force=True, ignore_permissions=True)
