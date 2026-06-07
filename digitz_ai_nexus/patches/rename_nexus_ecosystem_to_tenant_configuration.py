import frappe


def execute():
    # Rename the database table
    if frappe.db.table_exists("tabNexus Ecosystem") and not frappe.db.table_exists(
        "tabNexus Tenant Configuration"
    ):
        frappe.db.sql("RENAME TABLE `tabNexus Ecosystem` TO `tabNexus Tenant Configuration`")

    # Remove the old DocType metadata record
    if frappe.db.exists("DocType", "Nexus Ecosystem"):
        frappe.delete_doc("DocType", "Nexus Ecosystem", force=True, ignore_missing=True)

    # Rename the active_ecosystem column in tabNexus User Context
    if frappe.db.table_exists("tabNexus User Context") and frappe.db.has_column(
        "tabNexus User Context", "active_ecosystem"
    ):
        frappe.db.sql(
            "ALTER TABLE `tabNexus User Context` "
            "CHANGE `active_ecosystem` `active_tenant_configuration` VARCHAR(140)"
        )

    frappe.db.commit()
