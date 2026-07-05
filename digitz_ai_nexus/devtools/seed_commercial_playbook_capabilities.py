"""
Seed the capability-summary items on the Nexus Companion Playbook used by the
Nexy commercial agent profile.

The capability summary (decision: present_nexy_capability_visibility) renders
deterministically from these rows — identical in every conversation. Edit the
rows on the playbook in desk to change the pitch; no reprocessing needed.

Usage:
    bench --site digitz_ai_nexus_staging.site execute \
        digitz_ai_nexus.devtools.seed_commercial_playbook_capabilities.run

Idempotent — capability rows are replaced wholesale on every run.
"""

import frappe

AGENT_PROFILE = "NEXY-COMPANION-NEXUS-AI"
DEFAULT_PLAYBOOK_NAME = "Nexy Commercial Playbook"

# The reconciled commercial capability list (user-approved 2026-07-04).
# These rows ARE the pitch: rendered verbatim by the capability summary and
# the no-match capability menu.
CAPABILITY_ITEMS = [
    {
        "capability_area": "website_sales_presentation",
        "display_title": "Website Products & Services Presentation",
        "short_description": (
            "Present products and services through intelligent website conversations — "
            "understand the visitor's need, clarify doubts, and guide interested "
            "visitors toward a demo, enquiry, or booked meeting."
        ),
    },
    {
        "capability_area": "website_customer_support",
        "display_title": "AI Website Customer Support",
        "short_description": (
            "Instant support on your website from approved business knowledge — "
            "answer questions, clarify service details, collect issue information, "
            "and escalate when human attention is needed."
        ),
    },
    {
        "capability_area": "whatsapp_lead_generation",
        "display_title": "WhatsApp AI Lead Generation",
        "short_description": (
            "Generate and qualify leads through WhatsApp conversations — including "
            "proactive outreach to imported prospect lists — and move interested "
            "leads toward the next business action."
        ),
    },
    {
        "capability_area": "whatsapp_customer_support",
        "display_title": "WhatsApp AI Customer Support",
        "short_description": (
            "Customer support through WhatsApp — customers ask questions, share "
            "issues, receive guided responses, and reach a human when the situation "
            "requires it."
        ),
    },
    {
        "capability_area": "contact_intelligence",
        "display_title": "Centralised Contact Intelligence",
        "short_description": (
            "One central intelligence layer for contacts, leads, customers, and "
            "prospects — contact profiles, product-fit matching, and systematic "
            "messaging over time."
        ),
    },
    {
        "capability_area": "offers_management",
        "display_title": "Offers Management & AI Push",
        "short_description": (
            "Manage business offers and promote them through WhatsApp — Nexy pushes "
            "relevant offers, explains benefits, answers queries, and guides "
            "interested contacts toward action."
        ),
    },
    {
        "capability_area": "human_escalation",
        "display_title": "Human Escalation",
        "short_description": (
            "Sensitive cases, high-value opportunities, complex questions, or "
            "low-confidence answers are routed to the right human team member "
            "with full context."
        ),
    },
]


def run():
    print("\n" + "=" * 70)
    print("  Commercial Playbook Capability Seed")
    print("=" * 70)

    profile = frappe.get_doc("Nexus AI Agent Profile", AGENT_PROFILE)
    playbook_name = (getattr(profile, "companion_playbook", None) or "").strip()

    if playbook_name and frappe.db.exists("Nexus Companion Playbook", playbook_name):
        playbook = frappe.get_doc("Nexus Companion Playbook", playbook_name)
        print(f"  Playbook (existing)  : {playbook.name} — {playbook.playbook_name}")
    else:
        existing = frappe.db.get_value(
            "Nexus Companion Playbook",
            {"playbook_name": DEFAULT_PLAYBOOK_NAME},
            "name",
        )
        if existing:
            playbook = frappe.get_doc("Nexus Companion Playbook", existing)
        else:
            playbook = frappe.new_doc("Nexus Companion Playbook")
            playbook.playbook_name = DEFAULT_PLAYBOOK_NAME
            playbook.tenant = profile.tenant if hasattr(profile, "tenant") else "NEXUS-AI"
            playbook.enabled = 1
            playbook.description = (
                "Playbook for the Nexy commercial companion. Owns the capability "
                "summary pitch shown to website visitors."
            )
            playbook.insert(ignore_permissions=True)
        # Link it to the profile
        profile.db_set("companion_playbook", playbook.name, update_modified=False)
        print(f"  Playbook (linked)    : {playbook.name} — {playbook.playbook_name}")

    if not (playbook.get("capability_summary_heading") or "").strip():
        playbook.capability_summary_heading = "Nexy Capability Summary"

    playbook.enabled = 1
    playbook.set("capability_items", [])
    for item in CAPABILITY_ITEMS:
        playbook.append("capability_items", {**item, "enabled": 1})

    playbook.save(ignore_permissions=True)
    frappe.db.commit()

    print(f"  Heading              : {playbook.capability_summary_heading}")
    print(f"  Capability items     : {len(playbook.capability_items)}")
    for row in playbook.capability_items:
        print(f"    - [{row.capability_area}] {row.display_title}")
    print("=" * 70 + "\n")

    return {
        "playbook": playbook.name,
        "items": len(playbook.capability_items),
        "agent_profile": AGENT_PROFILE,
    }
