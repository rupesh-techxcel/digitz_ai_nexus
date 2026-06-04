import frappe

from digitz_ai_nexus.setup.access_seed import seed_default_access_governance


def after_install():
    seed_defaults()


def seed_defaults():
    result = seed_default_access_governance()
    frappe.db.commit()
    frappe.logger().info("Nexus Core defaults seeded.")
    return result
