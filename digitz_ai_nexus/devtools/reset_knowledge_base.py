import frappe


KNOWLEDGE_DOCTYPES = [
    "Nexus Knowledge Test Run",
    "Nexus Knowledge Test Case",
    "Nexus Knowledge Chunk",
    "Nexus Knowledge Source",
    "Nexus Knowledge Unit",
]


def get_knowledge_inventory():
    inventory = {}
    for doctype in KNOWLEDGE_DOCTYPES:
        if not frappe.db.exists("DocType", doctype):
            inventory[doctype] = {
                "exists": False,
                "count": 0,
                "names": [],
            }
            continue

        names = frappe.get_all(doctype, pluck="name", limit_page_length=0)
        inventory[doctype] = {
            "exists": True,
            "count": len(names),
            "names": names,
        }

    return inventory


def clear_all_knowledge(dry_run=True, confirm=None):
    """
    Remove all runtime knowledge records while preserving tenant, routing,
    channel, profile, access, and configuration masters.
    """
    before = get_knowledge_inventory()

    if dry_run:
        return {
            "dry_run": True,
            "deleted": {},
            "before": before,
            "after": before,
        }

    if confirm != "CLEAR_ALL_NEXUS_KNOWLEDGE":
        frappe.throw(
            "Pass confirm='CLEAR_ALL_NEXUS_KNOWLEDGE' to delete all Nexus knowledge records."
        )

    deleted = {}
    for doctype in KNOWLEDGE_DOCTYPES:
        if not before.get(doctype, {}).get("exists"):
            deleted[doctype] = []
            continue

        names = list(before[doctype]["names"])
        deleted[doctype] = []

        for name in names:
            if frappe.db.exists(doctype, name):
                frappe.delete_doc(
                    doctype,
                    name,
                    force=True,
                    ignore_permissions=True,
                    delete_permanently=True,
                )
                deleted[doctype].append(name)

    frappe.db.commit()
    after = get_knowledge_inventory()

    return {
        "dry_run": False,
        "deleted": deleted,
        "before": before,
        "after": after,
    }

