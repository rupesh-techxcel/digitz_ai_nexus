"""
Create the Nexy Companion Assignment for the NEXUS-AI tenant.

Links the public 'Ask Anything About Nexus AI' chat category to the
Sales Companion Nexy Role Profile so Nexy is activated as Visitor Companion.

Run via:
  bench --site digitz_ai_nexus_staging.site execute \
    digitz_ai_nexus.devtools.seed_nexy_nexus_ai_companion.run
"""

import frappe

CHAT_CATEGORY = "ASK-ME-NEXUS-AI-NEXUS-AI"
ROLE_PROFILE  = "DEFAULT-SALES-COMPANION-NEXUS-AI"
TENANT        = "NEXUS-AI"


def run():
    name = f"NCA-{CHAT_CATEGORY}"

    # Verify dependencies exist
    if not frappe.db.exists("Nexus Chat Category", CHAT_CATEGORY):
        raise ValueError(f"Chat Category not found: {CHAT_CATEGORY}")
    if not frappe.db.exists("Nexy Role Profile", ROLE_PROFILE):
        raise ValueError(f"Nexy Role Profile not found: {ROLE_PROFILE}")
    if not frappe.db.exists("Nexus Tenant", TENANT):
        raise ValueError(f"Nexus Tenant not found: {TENANT}")

    if frappe.db.exists("Nexy Companion Assignment", name):
        doc = frappe.get_doc("Nexy Companion Assignment", name)
        doc.nexy_role_profile = ROLE_PROFILE
        doc.tenant = TENANT
        doc.enabled = 1
        doc.assignment_notes = (
            "NEXUS-AI public chat companion — activates Nexy as Sales Companion "
            "for the 'Ask Anything About Nexus AI' category."
        )
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"Updated existing: {name}")
    else:
        doc = frappe.get_doc({
            "doctype": "Nexy Companion Assignment",
            "chat_category": CHAT_CATEGORY,
            "nexy_role_profile": ROLE_PROFILE,
            "tenant": TENANT,
            "enabled": 1,
            "assignment_notes": (
                "NEXUS-AI public chat companion — activates Nexy as Sales Companion "
                "for the 'Ask Anything About Nexus AI' category."
            ),
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Created: {doc.name}")

    rec = frappe.db.get_value(
        "Nexy Companion Assignment",
        name,
        ["name", "chat_category", "nexy_role_profile", "tenant", "enabled"],
        as_dict=True,
    )
    print("\n" + "=" * 60)
    print(f"  Name              : {rec.name}")
    print(f"  Chat Category     : {rec.chat_category}")
    print(f"  Nexy Role Profile : {rec.nexy_role_profile}")
    print(f"  Tenant            : {rec.tenant}")
    print(f"  Enabled           : {rec.enabled}")
    print("=" * 60)
    return rec
