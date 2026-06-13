import frappe


TENANT_CODE = "DIGITZ-AI-NEXUS"


def reset_nexus_knowledge(tenant_code=None):
    """
    Wipes all knowledge pipeline records (Sources, Units, Chunks, Semantic Index)
    for the DIGITZ AI Nexus seed tenant, then reruns both seeds fresh.

    Run from bench console:
        from digitz_ai_nexus.devtools.reset_and_reseed_nexus_knowledge import reset_nexus_knowledge
        reset_nexus_knowledge()
    """
    tenant_code = tenant_code or TENANT_CODE

    tenant = frappe.db.get_value("Nexus Tenant", {"tenant_code": tenant_code}, "name")
    if not tenant:
        print(f"Tenant with code '{tenant_code}' not found. Nothing to reset.")
        return

    print(f"Resetting knowledge pipeline for tenant: {tenant}")

    # 1. Delete Semantic Index Entries
    _delete_linked("Nexus Knowledge Index Entry", "tenant", tenant)

    # 2. Delete Context Summaries
    _delete_linked("Nexus Context Summary", "tenant", tenant)

    # 3. Delete Knowledge Chunks
    _delete_linked("Nexus Knowledge Chunk", "tenant", tenant)

    # 4. Delete Knowledge Units
    _delete_linked("Nexus Knowledge Unit", "tenant", tenant)

    # 5. Delete Knowledge Sources
    _delete_linked("Nexus Knowledge Source", "tenant", tenant)

    frappe.db.commit()
    print("Wipe complete. Running seeds...")

    # 6. Run homepage seed
    from digitz_ai_nexus.devtools.seed_digitz_nexus_homepage_knowledge import (
        seed_nexus_website_knowledge,
    )
    result_home = seed_nexus_website_knowledge(process_sources=True)
    print(f"Homepage seed: {len(result_home.get('sources', []))} sources seeded.")

    # 7. Run platform seed
    from digitz_ai_nexus.devtools.seed_digitz_nexus_platform_knowledge import (
        seed_nexus_platform_knowledge,
    )
    result_platform = seed_nexus_platform_knowledge(process_sources=True)
    print(f"Platform seed: {len(result_platform.get('sources', []))} sources seeded.")

    frappe.db.commit()
    print("Reset and reseed complete.")
    return {"homepage": result_home, "platform": result_platform}


def _delete_linked(doctype, field, value):
    if not frappe.db.exists("DocType", doctype):
        return
    meta = frappe.get_meta(doctype)
    if not meta.has_field(field):
        return
    names = frappe.get_all(doctype, filters={field: value}, pluck="name", limit_page_length=10000)
    count = len(names)
    for name in names:
        frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
    if count:
        print(f"  Deleted {count} {doctype} records.")
