import frappe


def reset_sources_for_strict_answer_approval(tenant=None):
    """
    Backfill generated-answer approval fields and move existing processed
    sources into the new strict approval workflow.

    Existing data is not deleted:
    - User Question index entries become Pending Review.
    - Intellectual Summary entries are marked Approved because they do not
      require generated-answer approval.
    - Source retrieval readiness is cleared.
    - Active chunks are disabled until the source is approved/published again.
    """

    if not frappe.db.exists("DocType", "Nexus Knowledge Index Entry"):
        return {
            "success": False,
            "message": "Nexus Knowledge Index Entry doctype does not exist.",
        }

    index_meta = frappe.get_meta("Nexus Knowledge Index Entry")
    index_fields = {df.fieldname for df in index_meta.fields}

    source_filters = {}
    if tenant:
        source_filters["tenant"] = tenant

    sources = frappe.get_all(
        "Nexus Knowledge Source",
        filters=source_filters,
        pluck="name",
        limit_page_length=1000,
    )

    index_filters = {}
    if tenant and "tenant" in index_fields:
        index_filters["tenant"] = tenant

    entries = frappe.get_all(
        "Nexus Knowledge Index Entry",
        filters=index_filters,
        fields=[
            "name",
            "entry_type",
            "answer_preview",
            "canonical_text",
            "display_summary",
            "knowledge_source",
        ],
        limit_page_length=5000,
    )

    updated_entries = 0

    for entry in entries:
        updates = {}

        if "generated_answer" in index_fields:
            updates["generated_answer"] = (
                entry.get("answer_preview")
                or entry.get("display_summary")
                or entry.get("canonical_text")
                or ""
            )

        if "answer_review_status" in index_fields:
            updates["answer_review_status"] = (
                "Pending Review"
                if entry.get("entry_type") == "User Question"
                else "Approved"
            )

        if "answer_review_notes" in index_fields:
            updates["answer_review_notes"] = (
                "Backfilled for strict generated-answer approval workflow."
                if entry.get("entry_type") == "User Question"
                else "No generated-answer approval required for intellectual summaries."
            )

        if "answer_reviewed_by" in index_fields:
            updates["answer_reviewed_by"] = None

        if "answer_reviewed_on" in index_fields:
            updates["answer_reviewed_on"] = None

        if updates:
            frappe.db.set_value("Nexus Knowledge Index Entry", entry.get("name"), updates, update_modified=True)
            updated_entries += 1

    source_meta = frappe.get_meta("Nexus Knowledge Source")
    source_fields = {df.fieldname for df in source_meta.fields}
    updated_sources = 0

    for source_name in sources:
        updates = {}

        if "status" in source_fields:
            updates["status"] = "Processed"

        if "published" in source_fields:
            updates["published"] = 0

        if "ready_to_publish" in source_fields:
            updates["ready_to_publish"] = 0

        if "retrieval_ready" in source_fields:
            updates["retrieval_ready"] = 0

        if "review_reason" in source_fields:
            updates["review_reason"] = "Generated possible-question answers require manual approval."

        if updates:
            frappe.db.set_value("Nexus Knowledge Source", source_name, updates, update_modified=True)
            updated_sources += 1

    disabled_chunks = 0

    if frappe.db.exists("DocType", "Nexus Knowledge Chunk"):
        chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")
        chunk_fields = {df.fieldname for df in chunk_meta.fields}

        if "knowledge_source" in chunk_fields and "disabled" in chunk_fields:
            chunk_filters = {"knowledge_source": ["in", sources]} if sources else {}
            chunks = frappe.get_all(
                "Nexus Knowledge Chunk",
                filters=chunk_filters,
                pluck="name",
                limit_page_length=5000,
            )

            for chunk_name in chunks:
                frappe.db.set_value("Nexus Knowledge Chunk", chunk_name, "disabled", 1, update_modified=True)
                disabled_chunks += 1

    frappe.db.commit()

    return {
        "success": True,
        "tenant": tenant,
        "sources_reset": updated_sources,
        "index_entries_backfilled": updated_entries,
        "chunks_disabled": disabled_chunks,
    }


def delete_archived_generated_validation_tests(tenant=None):
    """
    Remove obsolete archived generated validation tests.

    Validation tests are generated artifacts. The current Studio workflow
    replaces generated tests instead of archiving old ones.
    """

    if not frappe.db.exists("DocType", "Nexus Knowledge Test Case"):
        return {
            "success": False,
            "message": "Nexus Knowledge Test Case doctype does not exist.",
        }

    test_meta = frappe.get_meta("Nexus Knowledge Test Case")
    test_fields = {df.fieldname for df in test_meta.fields}

    filters = {}

    if "status" in test_fields:
        filters["status"] = "Archived"

    if "generated_by_ai" in test_fields:
        filters["generated_by_ai"] = 1

    if tenant and "tenant" in test_fields:
        filters["tenant"] = tenant

    rows = frappe.get_all(
        "Nexus Knowledge Test Case",
        filters=filters,
        pluck="name",
        limit_page_length=5000,
    )

    deleted_runs = 0

    if rows and frappe.db.exists("DocType", "Nexus Knowledge Test Run"):
        run_meta = frappe.get_meta("Nexus Knowledge Test Run")
        run_fields = {df.fieldname for df in run_meta.fields}

        if "test_case" in run_fields:
            runs = frappe.get_all(
                "Nexus Knowledge Test Run",
                filters={"test_case": ["in", rows]},
                pluck="name",
                limit_page_length=10000,
            )

            for run_name in runs:
                frappe.delete_doc(
                    "Nexus Knowledge Test Run",
                    run_name,
                    ignore_permissions=True,
                    force=True,
                )
                deleted_runs += 1

    deleted_tests = 0

    for test_name in rows:
        frappe.delete_doc(
            "Nexus Knowledge Test Case",
            test_name,
            ignore_permissions=True,
            force=True,
        )
        deleted_tests += 1

    frappe.db.commit()

    return {
        "success": True,
        "tenant": tenant,
        "deleted_validation_tests": deleted_tests,
        "deleted_validation_runs": deleted_runs,
    }
