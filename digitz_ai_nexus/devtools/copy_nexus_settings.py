"""
Copy Nexus Settings (including encrypted API key) from one site to another.

Usage — run from the TARGET site:

    bench --site digitz_ai_nexus_live_test.site execute \
        digitz_ai_nexus.devtools.copy_nexus_settings.copy_from_site \
        --kwargs '{"source_site": "digitz_ai_nexus.site"}'
"""

import frappe


def get_settings_snapshot():
    """
    Returns all Nexus Settings field values for the current site,
    including the decrypted api_key.

    Call from the SOURCE site:
        bench --site digitz_ai_nexus.site execute \
            digitz_ai_nexus.devtools.copy_nexus_settings.get_settings_snapshot
    """
    from frappe.utils.password import get_decrypted_password

    doc = frappe.get_doc("Nexus Settings", "Nexus Settings")

    snapshot = {}
    skip = {"name", "owner", "creation", "modified", "modified_by",
             "docstatus", "idx", "doctype"}

    for f in doc.meta.fields:
        fn = f.fieldname
        if fn in skip or f.fieldtype in ("Section Break", "Column Break", "HTML"):
            continue
        snapshot[fn] = doc.get(fn)

    # Decrypt the password field
    try:
        snapshot["api_key"] = get_decrypted_password(
            "Nexus Settings", "Nexus Settings", "api_key"
        )
    except Exception as e:
        snapshot["api_key"] = None
        snapshot["_api_key_error"] = str(e)

    return snapshot


def copy_from_site(source_site):
    """
    Reads Nexus Settings from *source_site* and writes them to the current site.

    Run from the TARGET site:
        bench --site digitz_ai_nexus_live_test.site execute \
            digitz_ai_nexus.devtools.copy_nexus_settings.copy_from_site \
            --kwargs '{"source_site": "digitz_ai_nexus.site"}'
    """
    import os
    from frappe.utils.password import set_encrypted_password

    sites_path = frappe.utils.get_bench_path() + "/sites"
    source_db_path = os.path.join(sites_path, source_site)

    if not os.path.exists(source_db_path):
        frappe.throw(f"Source site path not found: {source_db_path}")

    # Connect to source site, read settings, then reconnect to target
    target_site = frappe.local.site

    frappe.destroy()
    frappe.init(site=source_site, sites_path=sites_path)
    frappe.connect()

    source_snap = get_settings_snapshot()

    frappe.destroy()
    frappe.init(site=target_site, sites_path=sites_path)
    frappe.connect()

    # Apply to target
    doc = frappe.get_doc("Nexus Settings", "Nexus Settings")

    plain_fields = [f.fieldname for f in doc.meta.fields
                    if f.fieldtype not in ("Password", "Section Break",
                                           "Column Break", "HTML")]
    skip = {"name", "owner", "creation", "modified", "modified_by",
            "docstatus", "idx", "doctype"}

    for fn in plain_fields:
        if fn in skip:
            continue
        if fn in source_snap and source_snap[fn] is not None:
            doc.set(fn, source_snap[fn])

    doc.save(ignore_permissions=True)

    # Set the encrypted api_key separately
    api_key = source_snap.get("api_key")
    if api_key:
        set_encrypted_password("Nexus Settings", "Nexus Settings", api_key, "api_key")

    frappe.db.commit()

    print(f"Nexus Settings copied from {source_site} → {target_site}")
    print(f"  Model: {doc.get('llm_model') or doc.get('model') or '-'}")
    print(f"  API key copied: {'yes' if api_key else 'no'}")

    return {"status": "success", "source": source_site, "target": target_site}
