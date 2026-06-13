import frappe


def execute():
    if not frappe.db.table_exists("tabNexus Tenant Configuration"):
        return

    if frappe.db.has_column("tabNexus Tenant Configuration", "ecosystem_name"):
        frappe.db.sql(
            "ALTER TABLE `tabNexus Tenant Configuration` "
            "CHANGE `ecosystem_name` `configuration_name` VARCHAR(140)"
        )

    if frappe.db.has_column("tabNexus Tenant Configuration", "ecosystem_type"):
        frappe.db.sql(
            "ALTER TABLE `tabNexus Tenant Configuration` "
            "CHANGE `ecosystem_type` `configuration_type` VARCHAR(140)"
        )

    frappe.db.commit()
