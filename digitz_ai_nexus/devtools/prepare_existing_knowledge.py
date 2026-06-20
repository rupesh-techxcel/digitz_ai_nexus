import frappe


CONFIRM_TOKEN = "PREPARE_EXISTING_KNOWLEDGE"
COMPLETE_CONFIRM_TOKEN = "COMPLETE_PROCESSED_KNOWLEDGE"


def _source_inventory(source_names):
    return frappe.get_all(
        "Nexus Knowledge Source",
        filters={"name": ["in", source_names]},
        fields=[
            "name",
            "status",
            "processing_status",
            "processing_version",
            "chunk_count",
            "validation_status",
            "retrieval_ready",
        ],
        order_by="name asc",
        limit_page_length=0,
    )


def _archive_unverified_questions(source_name):
    """Exclude questions that did not pass high-confidence same-chunk validation."""
    names = frappe.get_all(
        "Nexus Knowledge Index Entry",
        filters={
            "knowledge_source": source_name,
            "entry_type": "User Question",
            "disabled": 0,
            "answer_review_status": ["!=", "Approved"],
        },
        pluck="name",
        limit_page_length=0,
    )

    for name in names:
        frappe.db.set_value(
            "Nexus Knowledge Index Entry",
            name,
            {
                "status": "Archived",
                "disabled": 1,
                "generation_notes": (
                    "Archived by automated preparation because the question did not "
                    "pass high-confidence same-chunk validation."
                ),
            },
            update_modified=False,
        )

    frappe.db.commit()
    return len(names)


def prepare_existing_sources(
    source_names=None,
    dry_run=True,
    publish=True,
    confirm=None,
):
    """Prepare existing sources through reset, processing, validation, and publish."""
    from digitz_ai_nexus.api.nexus_knowledge_studio import (
        publish_knowledge_source,
        reset_knowledge_source,
        validate_knowledge_source,
    )
    from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source

    if source_names:
        source_names = frappe.parse_json(source_names) if isinstance(source_names, str) else source_names
    else:
        source_names = frappe.get_all(
            "Nexus Knowledge Source",
            pluck="name",
            order_by="name asc",
            limit_page_length=0,
        )

    source_names = list(dict.fromkeys(source_names or []))
    missing = [
        name for name in source_names
        if not frappe.db.exists("Nexus Knowledge Source", name)
    ]
    if missing:
        frappe.throw(f"Knowledge Source not found: {', '.join(missing)}")

    before = _source_inventory(source_names)
    if dry_run:
        return {
            "dry_run": True,
            "source_count": len(source_names),
            "publish": bool(publish),
            "sources": before,
        }

    if confirm != CONFIRM_TOKEN:
        frappe.throw(f"Pass confirm='{CONFIRM_TOKEN}' to run the lifecycle.")

    results = {name: {"name": name, "steps": {}} for name in source_names}

    # Reset every source first so later resets cannot remove summaries generated
    # by sources that have already completed this run.
    for source_name in source_names:
        try:
            reset_result = reset_knowledge_source(
                source_name,
                confirm="RESET_KNOWLEDGE_SOURCE",
            )
            results[source_name]["steps"]["reset"] = reset_result.get("deleted") or {}
        except Exception as exc:
            results[source_name]["steps"]["reset_error"] = str(exc)

    for source_name in source_names:
        entry = results[source_name]
        if entry["steps"].get("reset_error"):
            continue

        try:
            process_result = process_knowledge_source(source_name)
            entry["steps"]["process"] = {
                "status": process_result.get("status"),
                "chunks": process_result.get("chunk_count", 0),
                "index_entries": len(process_result.get("semantic_index_entries") or []),
            }

            entry["steps"]["archived_unverified_questions"] = (
                _archive_unverified_questions(source_name)
            )

            validation_result = validate_knowledge_source(source_name)
            entry["steps"]["validate"] = {
                "success": bool(validation_result.get("success")),
                "message": validation_result.get("message"),
                "confidence": validation_result.get("confidence"),
            }
            if not validation_result.get("success"):
                continue

            if publish:
                publish_result = publish_knowledge_source(source_name)
                entry["steps"]["publish"] = {
                    "success": bool(publish_result.get("success")),
                    "message": publish_result.get("message"),
                    "retrieval_ready": publish_result.get("retrieval_ready", 0),
                }
        except Exception as exc:
            frappe.db.rollback()
            entry["steps"]["error"] = str(exc)
        finally:
            frappe.db.commit()

    after = _source_inventory(source_names)
    ready = [row.name for row in after if row.get("retrieval_ready")]
    failed = [
        name for name, entry in results.items()
        if entry["steps"].get("error")
        or entry["steps"].get("reset_error")
        or not (
            entry["steps"].get("publish", {}).get("success")
            if publish
            else entry["steps"].get("validate", {}).get("success")
        )
    ]

    return {
        "dry_run": False,
        "source_count": len(source_names),
        "retrieval_ready_count": len(ready),
        "retrieval_ready_sources": ready,
        "failed_sources": failed,
        "details": list(results.values()),
        "after": after,
    }


def complete_processed_sources(source_names=None, publish=True, confirm=None):
    """Retry validation/publication for already processed sources without reprocessing."""
    from digitz_ai_nexus.api.nexus_knowledge_studio import (
        publish_knowledge_source,
        validate_knowledge_source,
    )

    if source_names:
        source_names = frappe.parse_json(source_names) if isinstance(source_names, str) else source_names
    else:
        source_names = frappe.get_all(
            "Nexus Knowledge Source",
            filters={"processing_status": "Processed", "retrieval_ready": 0},
            pluck="name",
            order_by="name asc",
            limit_page_length=0,
        )

    if confirm != COMPLETE_CONFIRM_TOKEN:
        frappe.throw(f"Pass confirm='{COMPLETE_CONFIRM_TOKEN}' to complete processed sources.")

    results = []
    for source_name in source_names or []:
        entry = {"name": source_name}
        try:
            entry["archived_unverified_questions"] = _archive_unverified_questions(source_name)
            validation = validate_knowledge_source(source_name)
            entry["validation"] = {
                "success": bool(validation.get("success")),
                "message": validation.get("message"),
                "confidence": validation.get("confidence"),
            }
            if validation.get("success") and publish:
                publication = publish_knowledge_source(source_name)
                entry["publication"] = {
                    "success": bool(publication.get("success")),
                    "message": publication.get("message"),
                    "retrieval_ready": publication.get("retrieval_ready", 0),
                }
        except Exception as exc:
            frappe.db.rollback()
            entry["error"] = str(exc)
        finally:
            frappe.db.commit()
        results.append(entry)

    return {
        "source_count": len(source_names or []),
        "details": results,
        "after": _source_inventory(source_names or []),
    }
