import frappe

from digitz_ai_nexus.setup.access_seed import seed_default_access_governance


def after_install():
    seed_defaults()


def seed_defaults(tenant=None):
    """
    Seed core Nexus access governance records.

    When called standalone (no tenant), records are created without a tenant —
    suitable for core-only installations. When called by digitz_ai_nexus_live
    install, the tenant is passed so records are properly scoped.
    """
    result = seed_default_access_governance(tenant=tenant)
    frappe.db.commit()
    frappe.logger().info("Nexus Core defaults seeded.")
    return result
