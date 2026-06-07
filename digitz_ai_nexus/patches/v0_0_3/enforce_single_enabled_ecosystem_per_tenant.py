import frappe


def execute():
    if not frappe.db.exists("DocType", "Nexus Tenant Configuration"):
        return

    tenants = frappe.get_all(
        "Nexus Tenant Configuration",
        filters={"enabled": 1},
        pluck="tenant",
        distinct=True,
    )

    for tenant in tenants:
        if not tenant:
            continue

        ecosystems = frappe.get_all(
            "Nexus Tenant Configuration",
            filters={
                "tenant": tenant,
                "enabled": 1,
            },
            fields=["name", "is_default", "modified"],
            order_by="is_default desc, modified desc",
            limit_page_length=500,
        )

        if len(ecosystems) <= 1:
            if ecosystems and not int(ecosystems[0].get("is_default") or 0):
                frappe.db.set_value(
                    "Nexus Tenant Configuration",
                    ecosystems[0].name,
                    "is_default",
                    1,
                    update_modified=False,
                )
            continue

        keep = ecosystems[0].name

        frappe.db.set_value(
            "Nexus Tenant Configuration",
            keep,
            "is_default",
            1,
            update_modified=False,
        )

        for row in ecosystems[1:]:
            frappe.db.set_value(
                "Nexus Tenant Configuration",
                row.name,
                {
                    "enabled": 0,
                    "is_default": 0,
                },
                update_modified=False,
            )
