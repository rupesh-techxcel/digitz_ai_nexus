import frappe


KNOWLEDGE_DOCTYPES = [
    "Nexus Knowledge Test Run",
    "Nexus Knowledge Test Case",
    "Nexus Knowledge Chunk",
    "Nexus Knowledge Source",
    "Nexus Knowledge Unit",
]


PROCESSING_DOCTYPES = [
    "Nexus Knowledge Test Run",
    "Nexus Knowledge Test Case",
    "Nexus Question Correlation",
    "Nexus Knowledge Index Entry",
    "Nexus Knowledge Chunk",
    "Nexus Knowledge Unit",
    "Nexus Knowledge Context Summary",
]

SOURCE_DRAFT_DEFAULTS = {
    "status": "Draft",
    "processing_status": "Pending",
    "processing_version": 0,
    "chunk_count": 0,
    "active_chunk_count": 0,
    "embedding_status": "Pending",
    "diagnostics_status": "Pending",
    "validation_status": "Pending",
    "ready_to_publish": 0,
    "needs_review": 0,
    "review_reason": None,
    "validation_query": None,
    "validation_confidence": 0,
    "validated_on": None,
    "validated_by": None,
    "retrieval_ready": 0,
    "last_processed_on": None,
    "generated_knowledge_unit": None,
    "error_log": None,
}


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


def reset_all_sources_to_draft(dry_run=True, confirm=None):
    """Delete generated knowledge data while preserving source documents and content."""
    source_names = frappe.get_all(
        "Nexus Knowledge Source", pluck="name", limit_page_length=0
    )
    before = {
        "sources": len(source_names),
        "processing_records": _get_counts(PROCESSING_DOCTYPES),
    }

    if dry_run:
        return {"dry_run": True, "before": before}

    if confirm != "RESET_ALL_SOURCES_TO_DRAFT":
        frappe.throw(
            "Pass confirm='RESET_ALL_SOURCES_TO_DRAFT' to clear processing data "
            "and preserve the Knowledge Source documents as drafts."
        )

    source_meta = frappe.get_meta("Nexus Knowledge Source")
    reset_values = {
        fieldname: value
        for fieldname, value in SOURCE_DRAFT_DEFAULTS.items()
        if source_meta.has_field(fieldname)
    }

    # Remove references to generated units before those units are deleted.
    if frappe.db.exists("DocType", "Nexus Knowledge Gap"):
        gap_meta = frappe.get_meta("Nexus Knowledge Gap")
        if gap_meta.has_field("suggested_knowledge_unit"):
            frappe.db.sql(
                """update `tabNexus Knowledge Gap`
                   set suggested_knowledge_unit = null
                   where coalesce(suggested_knowledge_unit, '') != ''"""
            )

    for source_name in source_names:
        frappe.db.set_value(
            "Nexus Knowledge Source",
            source_name,
            reset_values,
            update_modified=False,
        )

    deleted = {}
    for doctype in PROCESSING_DOCTYPES:
        if not frappe.db.exists("DocType", doctype):
            deleted[doctype] = 0
            continue

        names = frappe.get_all(doctype, pluck="name", limit_page_length=0)
        deleted[doctype] = len(names)
        for name in names:
            frappe.delete_doc(
                doctype,
                name,
                force=True,
                ignore_permissions=True,
                delete_permanently=True,
            )

    frappe.db.commit()
    return {
        "dry_run": False,
        "sources_preserved_as_draft": len(source_names),
        "deleted": deleted,
        "after": {
            "sources": frappe.db.count("Nexus Knowledge Source"),
            "draft_sources": frappe.db.count(
                "Nexus Knowledge Source", {"status": "Draft"}
            ),
            "processing_records": _get_counts(PROCESSING_DOCTYPES),
        },
    }


def _get_counts(doctypes):
    return {
        doctype: frappe.db.count(doctype)
        if frappe.db.exists("DocType", doctype)
        else None
        for doctype in doctypes
    }
