import importlib
import json
import re
import time

import frappe
from frappe.utils import cint, now_datetime

# -------------------------------------------------------------------------
# Active Studio Context helpers
# -------------------------------------------------------------------------

def _safe_get_single_value(doctype: str, fieldname: str):
    try:
        if frappe.db.exists("DocType", doctype):
            doc = frappe.get_single(doctype)
            if frappe.get_meta(doctype).has_field(fieldname):
                return doc.get(fieldname)
    except Exception:
        pass

    return None


def _normalize_context_value(value):
    """
    Treat empty placeholders as no value.
    """
    if value in (None, ""):
        return None

    value = str(value).strip()

    if value in ["-", "None", "none", "null", "undefined"]:
        return None

    return value


def _get_user_default_from_possible_keys(possible_keys):
    debug = []

    for key in possible_keys:
        value = _normalize_context_value(frappe.defaults.get_user_default(key))
        debug.append({
            "source": "user_default",
            "key": key,
            "value": value,
        })

        if value:
            return value, debug

    return None, debug


def _get_doc_value_if_field_exists(doctype: str, name: str, fieldnames):
    """
    Safely read the first available non-empty value from a document.
    """
    debug = []

    if not doctype or not name:
        return None, debug

    if not frappe.db.exists("DocType", doctype):
        debug.append({
            "source": "doc_value",
            "doctype": doctype,
            "name": name,
            "status": "doctype_missing",
        })
        return None, debug

    if not frappe.db.exists(doctype, name):
        debug.append({
            "source": "doc_value",
            "doctype": doctype,
            "name": name,
            "status": "doc_missing",
        })
        return None, debug

    meta = frappe.get_meta(doctype)

    for fieldname in fieldnames:
        if not meta.has_field(fieldname):
            debug.append({
                "source": "doc_value",
                "doctype": doctype,
                "name": name,
                "fieldname": fieldname,
                "status": "field_missing",
            })
            continue

        value = _normalize_context_value(frappe.db.get_value(doctype, name, fieldname))

        debug.append({
            "source": "doc_value",
            "doctype": doctype,
            "name": name,
            "fieldname": fieldname,
            "value": value,
        })

        if value:
            return value, debug

    return None, debug


def _find_first_matching_doc(doctype: str, filters: dict, preferred_fields=None):
    """
    Find one document with defensive field checking.
    """
    debug = []

    if not frappe.db.exists("DocType", doctype):
        debug.append({
            "source": "find_doc",
            "doctype": doctype,
            "status": "doctype_missing",
        })
        return None, debug

    meta = frappe.get_meta(doctype)

    safe_filters = {}

    for fieldname, value in (filters or {}).items():
        value = _normalize_context_value(value)

        if not value:
            continue

        if meta.has_field(fieldname):
            safe_filters[fieldname] = value
        else:
            debug.append({
                "source": "find_doc",
                "doctype": doctype,
                "fieldname": fieldname,
                "status": "filter_field_missing",
            })

    if meta.has_field("disabled") and "disabled" not in safe_filters:
        safe_filters["disabled"] = 0

    order_by = "modified desc"

    if preferred_fields:
        for fieldname in preferred_fields:
            if meta.has_field(fieldname):
                order_by = f"{fieldname} desc, modified desc"
                break

    try:
        rows = frappe.get_all(
            doctype,
            filters=safe_filters,
            fields=["name"],
            order_by=order_by,
            limit_page_length=1,
        )
    except Exception as exc:
        debug.append({
            "source": "find_doc",
            "doctype": doctype,
            "filters": safe_filters,
            "status": "query_failed",
            "error": str(exc),
        })
        return None, debug

    debug.append({
        "source": "find_doc",
        "doctype": doctype,
        "filters": safe_filters,
        "result": rows[0].name if rows else None,
    })

    if rows:
        return rows[0].name, debug

    return None, debug


def _resolve_value_from_user_or_settings(label, user_keys, settings_keys=None):
    """
    Resolve a context value from user defaults first, then Nexus Settings.
    """
    value, debug = _get_user_default_from_possible_keys(user_keys)

    if value:
        return value, debug

    settings_keys = settings_keys or []

    for fieldname in settings_keys:
        settings_value = _normalize_context_value(
            _safe_get_single_value("Nexus Settings", fieldname)
        )

        debug.append({
            "source": "nexus_settings",
            "fieldname": fieldname,
            "value": settings_value,
        })

        if settings_value:
            return settings_value, debug

    return None, debug


def _resolve_active_studio_context():
    """
    Resolve Studio working context using the same Administration snapshot
    used by the Nexus Administration page.

    Source of truth:
    digitz_ai_nexus.api.nexus_administration.get_administration_snapshot()

    Expected snapshot keys:
    - user_context
    - resolved_context
    """

    user = frappe.session.user

    context = frappe._dict({
        "user": user,
        "tenant": None,
        "ecosystem": None,
        "business_unit": None,
        "project": None,
        "channel": None,
        "context": None,
        "default_top_k": None,
        "resolution_source": "nexus_administration_snapshot",
        "snapshot_available": 0,
    })

    try:
        from digitz_ai_nexus.api.nexus_administration import get_administration_snapshot

        snapshot = get_administration_snapshot() or {}
        resolved_context = snapshot.get("resolved_context") or {}
        user_context = snapshot.get("user_context") or {}

        context.snapshot_available = 1

        context.tenant = _normalize_context_value(
            resolved_context.get("tenant")
            or user_context.get("active_tenant")
        )

        context.ecosystem = _normalize_context_value(
            resolved_context.get("ecosystem")
            or user_context.get("active_ecosystem")
        )

        context.business_unit = _normalize_context_value(
            resolved_context.get("business_unit")
            or user_context.get("active_business_unit")
        )

        context.project = _normalize_context_value(
            resolved_context.get("project")
            or user_context.get("active_project")
        )

        context.channel = _normalize_context_value(
            resolved_context.get("channel")
            or user_context.get("active_channel")
        )

        context.context = _normalize_context_value(
            resolved_context.get("context")
            or resolved_context.get("default_public_context")
        )

        context.default_top_k = resolved_context.get("default_top_k")

        return context

    except Exception:
        frappe.log_error(
            title="Nexus Studio Context Resolution Failed",
            message=frappe.get_traceback(),
        )

        context.resolution_source = "nexus_administration_snapshot_failed"
        context.resolution_error = frappe.get_traceback()

        return context


def _apply_active_context_filters_for_doctype(doctype: str, db_filters: dict, context):
    """
    Apply active user context filters to Studio doctypes.

    Final Studio filtering philosophy:

    1. Tenant is the hard boundary.
       If the target doctype has tenant and active tenant is available,
       tenant is always applied.

    2. Nexus Knowledge Source should NOT be forcibly filtered by
       business_unit, project, context, ecosystem, or channel.
       Reason:
       - AI Assist can suggest Business Unit dynamically.
       - User can edit Business Unit before creating the source.
       - Source records should still appear in Studio as long as they
         belong to the active tenant.

    3. Nexus Knowledge Unit can remain more tightly scoped by active
       business_unit, project, context, ecosystem, and channel because
       Knowledge Units are already structured/processed operational records.
    """

    meta = frappe.get_meta(doctype)

    tenant = _normalize_context_value(context.get("tenant"))
    ecosystem = _normalize_context_value(context.get("ecosystem"))
    business_unit = _normalize_context_value(context.get("business_unit"))
    project = _normalize_context_value(context.get("project"))
    channel = _normalize_context_value(context.get("channel"))
    knowledge_context = _normalize_context_value(context.get("context"))

    applied_filters = {}

    # ------------------------------------------------------------
    # Tenant is always the hard boundary when field exists.
    # ------------------------------------------------------------
    if tenant and meta.has_field("tenant"):
        db_filters["tenant"] = tenant
        applied_filters["tenant"] = tenant

    # ------------------------------------------------------------
    # Knowledge Sources should be tenant-scoped only.
    # ------------------------------------------------------------
    # This prevents newly created AI-assisted sources from disappearing
    # when AI/user changes Business Unit, Project, or Context.
    if doctype == "Nexus Knowledge Source":
        context.setdefault("applied_filters", {})
        context["applied_filters"][doctype] = applied_filters
        return db_filters

    # ------------------------------------------------------------
    # Other Studio doctypes can remain tightly scoped.
    # ------------------------------------------------------------
    if business_unit and meta.has_field("business_unit"):
        db_filters["business_unit"] = business_unit
        applied_filters["business_unit"] = business_unit

    if project and meta.has_field("project"):
        db_filters["project"] = project
        applied_filters["project"] = project

    if knowledge_context and meta.has_field("context"):
        db_filters["context"] = knowledge_context
        applied_filters["context"] = knowledge_context

    if ecosystem and meta.has_field("ecosystem"):
        db_filters["ecosystem"] = ecosystem
        applied_filters["ecosystem"] = ecosystem

    if channel and meta.has_field("channel"):
        db_filters["channel"] = channel
        applied_filters["channel"] = channel

    context.setdefault("applied_filters", {})
    context["applied_filters"][doctype] = applied_filters

    return db_filters


def _apply_active_context_filters(db_filters: dict, context):
    """
    Backward-compatible helper for Knowledge Unit filters.
    """
    return _apply_active_context_filters_for_doctype(
        "Nexus Knowledge Unit",
        db_filters,
        context,
    )


def _enforce_doc_active_tenant(doc, active_context):
    """
    Prevent actions on records outside the active tenant context.
    """
    if not _has_field(doc.doctype, "tenant"):
        return

    active_tenant = _normalize_context_value(active_context.get("tenant"))
    doc_tenant = _normalize_context_value(doc.get("tenant"))

    if active_tenant and doc_tenant and active_tenant != doc_tenant:
        frappe.throw(
            f"{doc.doctype} is outside the active tenant context.",
            frappe.PermissionError,
        )


# -------------------------------------------------------------------------
# Metadata helpers
# -------------------------------------------------------------------------

def _has_field(doctype: str, fieldname: str) -> bool:
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


def _get_if_exists(doc, fieldname: str, default=None):
    if _has_field(doc.doctype, fieldname):
        return doc.get(fieldname)
    return default


def _set_if_exists(doc, fieldname: str, value):
    if _has_field(doc.doctype, fieldname):
        doc.set(fieldname, value)


# -------------------------------------------------------------------------
# Knowledge Source helpers
# -------------------------------------------------------------------------

def _get_knowledge_source_fields():
    meta = frappe.get_meta("Nexus Knowledge Source")

    fields = ["name", "modified"]

    optional_fields = [
        "tenant",
        "ecosystem",
        "business_unit",
        "project",
        "channel",
        "source_title",
        "source_type",
        "source_url",
        "source_file",
        "source_reference_doctype",
        "source_reference_name",
        "manual_content",
        "extracted_text",
        "chat_category",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
        "context_path",
        "access_policy",
        "priority",
        "status",
        "sync_status",
        "last_synced_on",
        "disabled",
        "published",
        "ready_to_publish",
        "needs_review",
        "review_reason",
        "quality_status",
        "validation_status",
        "processing_status",
        "last_error",
        "owner_user",
        "processing_version",
        "chunk_count",
        "active_chunk_count",
        "embedding_status",
        "diagnostics_status",
        "retrieval_ready",
        "last_processed_on",
        "generated_knowledge_unit",
        "error_log",
    ]

    for fieldname in optional_fields:
        if meta.has_field(fieldname):
            fields.append(fieldname)

    return fields


def _get_source_content_value(row):
    """
    Return the source content used for readiness checks.
    Manual source mainly uses manual_content.
    Other source types may later use extracted_text.
    """
    manual_content = _normalize_context_value(row.get("manual_content"))
    if manual_content:
        return manual_content

    extracted_text = _normalize_context_value(row.get("extracted_text"))
    if extracted_text:
        return extracted_text

    return None


def _build_group_match_filters(doctype, row):
    if not frappe.db.exists("DocType", doctype):
        return None

    meta = frappe.get_meta(doctype)
    filters = {}

    for fieldname in [
        "tenant",
        "business_unit",
        "project",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
        "access_policy",
    ]:
        if not meta.has_field(fieldname):
            continue

        value = _normalize_context_value(row.get(fieldname))
        filters[fieldname] = value if value else ["in", ["", None]]

    return filters


def _count_context_summaries(active_context):
    if not frappe.db.exists("DocType", "Nexus Knowledge Context Summary"):
        return 0

    filters = {}
    filters = _apply_active_context_filters_for_doctype(
        "Nexus Knowledge Context Summary",
        filters,
        active_context,
    )

    meta = frappe.get_meta("Nexus Knowledge Context Summary")

    if meta.has_field("disabled"):
        filters["disabled"] = 0

    if meta.has_field("status"):
        filters["status"] = "Active"

    return frappe.db.count("Nexus Knowledge Context Summary", filters)


def _count_semantic_index_entries(active_context):
    if not frappe.db.exists("DocType", "Nexus Knowledge Index Entry"):
        return 0

    filters = {}
    filters = _apply_active_context_filters_for_doctype(
        "Nexus Knowledge Index Entry",
        filters,
        active_context,
    )

    meta = frappe.get_meta("Nexus Knowledge Index Entry")

    if meta.has_field("disabled"):
        filters["disabled"] = 0

    if meta.has_field("status"):
        filters["status"] = "Active"

    return frappe.db.count("Nexus Knowledge Index Entry", filters)


def _get_source_context_summary(row):
    if not frappe.db.exists("DocType", "Nexus Knowledge Context Summary"):
        return {
            "exists": 0,
            "status": "Missing",
        }

    filters = _build_group_match_filters("Nexus Knowledge Context Summary", row)
    if not filters:
        return {
            "exists": 0,
            "status": "Missing",
        }

    meta = frappe.get_meta("Nexus Knowledge Context Summary")

    if meta.has_field("disabled"):
        filters["disabled"] = 0

    if meta.has_field("status"):
        filters["status"] = "Active"

    fields = [
        "name",
        "summary_title",
        "summary_text",
        "source_count",
        "chunk_count",
        "embedding_status",
        "generated_on",
        "generation_method",
    ]
    fields = [fieldname for fieldname in fields if fieldname == "name" or meta.has_field(fieldname)]

    rows = frappe.get_all(
        "Nexus Knowledge Context Summary",
        filters=filters,
        fields=fields,
        order_by="generated_on desc, modified desc",
        limit_page_length=1,
    )

    if not rows:
        return {
            "exists": 0,
            "status": "Missing",
        }

    summary = rows[0]
    summary_text = summary.get("summary_text") or ""

    return {
        "exists": 1,
        "status": "Ready" if summary.get("embedding_status") == "Completed" else "Needs Embedding",
        "name": summary.get("name"),
        "title": summary.get("summary_title") or summary.get("name"),
        "summary_text": summary_text,
        "summary_preview": summary_text[:360],
        "source_count": summary.get("source_count") or 0,
        "chunk_count": summary.get("chunk_count") or 0,
        "embedding_status": summary.get("embedding_status"),
        "generated_on": summary.get("generated_on"),
        "generation_method": summary.get("generation_method"),
    }


def _get_source_semantic_index_summary(source_name):
    empty = {
        "total": 0,
        "intellectual_summary": 0,
        "user_question": 0,
        "embedding_completed": 0,
        "embedding_failed": 0,
    }

    if not source_name or not frappe.db.exists("DocType", "Nexus Knowledge Index Entry"):
        return empty

    meta = frappe.get_meta("Nexus Knowledge Index Entry")
    filters = {"knowledge_source": source_name}

    if meta.has_field("disabled"):
        filters["disabled"] = 0

    if meta.has_field("status"):
        filters["status"] = "Active"

    fields = ["entry_type", "embedding_status"]
    rows = frappe.get_all(
        "Nexus Knowledge Index Entry",
        filters=filters,
        fields=fields,
        limit_page_length=1000,
    )

    summary = dict(empty)

    for item in rows:
        entry_type = item.get("entry_type")
        embedding_status = item.get("embedding_status")

        summary["total"] += 1

        if entry_type == "Intellectual Summary":
            summary["intellectual_summary"] += 1

        if entry_type == "User Question":
            summary["user_question"] += 1

        if embedding_status == "Completed":
            summary["embedding_completed"] += 1
        elif embedding_status == "Failed":
            summary["embedding_failed"] += 1

    return summary


def _build_source_readiness_payload(row):
    """
    Build business-facing readiness for a Knowledge Source.

    Important:
    - Studio should not expose unit/chunk/embedding language as the main workflow.
    - Technical details can remain in the doctype form.
    - This payload tells Studio what the user needs to do next.
    """

    status = str(row.get("status") or "Draft").strip()
    sync_status = str(row.get("sync_status") or "Not Synced").strip()
    validation_status = str(row.get("validation_status") or "").strip()
    quality_status = str(row.get("quality_status") or "").strip()
    processing_status = str(row.get("processing_status") or "").strip()

    disabled = bool(row.get("disabled"))
    published = bool(row.get("published")) or status == "Published"
    ready_to_publish = bool(row.get("ready_to_publish")) or status == "Ready to Publish"
    needs_review = bool(row.get("needs_review"))

    content_value = _get_source_content_value(row)

    required_classification_fields = [
        "tenant",
        "business_unit",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
    ]

    missing_fields = []

    if not content_value:
        missing_fields.append("content")

    for fieldname in required_classification_fields:
        if not _normalize_context_value(row.get(fieldname)):
            missing_fields.append(fieldname)

    has_content = bool(content_value)
    has_classification = not any(
        fieldname in missing_fields
        for fieldname in required_classification_fields
    )

    normalized_status = status.lower()
    normalized_sync_status = sync_status.lower()
    normalized_validation = validation_status.lower()
    normalized_quality = quality_status.lower()
    normalized_processing = processing_status.lower()

    is_preparing = (
        normalized_sync_status in ["pending", "running"]
        or normalized_processing in ["pending", "running"]
    )

    preparation_failed = (
        normalized_sync_status == "failed"
        or normalized_processing == "failed"
        or normalized_status == "sync failed"
    )

    is_prepared = (
        normalized_status in [
            "ingested",
            "partially ingested",
            "prepared",
            "processed",
            "ready to publish",
            "published",
        ]
        or normalized_sync_status in ["completed", "processed"]
        or normalized_processing in ["processed", "completed", "prepared"]
    )
    
    is_validated = (
        normalized_status in ["validated", "tested", "ready to publish", "published"]
        or normalized_validation in ["validated", "passed", "tested"]
    )

    has_quality_issue = (
        needs_review
        or normalized_quality in ["failed", "poor", "needs review"]
        or preparation_failed
    )

    if disabled:
        readiness_status = "disabled"
        readiness_label = "Disabled"
        readiness_message = "This source is disabled and cannot be used until it is enabled."
        next_action = "review"
        next_action_label = "Review source"

    elif needs_review:
        readiness_status = "needs_review"
        readiness_label = "Needs Attention"
        readiness_message = row.get("review_reason") or "This source is marked for review."
        next_action = "review"
        next_action_label = "Review source"

    elif not has_content:
        readiness_status = "needs_content"
        readiness_label = "Needs Content"
        readiness_message = "Add source content before this source can be prepared."
        next_action = "review"
        next_action_label = "Add content"

    elif not has_classification:
        readiness_status = "needs_classification"
        readiness_label = "Needs Classification"
        readiness_message = "Complete the required business classification before preparation."
        next_action = "review"
        next_action_label = "Complete classification"

    elif preparation_failed:
        readiness_status = "preparation_failed"
        readiness_label = "Needs Attention"
        readiness_message = row.get("last_error") or "Source preparation failed and needs review."
        next_action = "review"
        next_action_label = "Review issue"

    elif is_preparing:
        readiness_status = "preparing"
        readiness_label = "Preparing"
        readiness_message = "Source preparation is currently in progress."
        next_action = "wait"
        next_action_label = "Wait for completion"

    elif published:
        readiness_status = "published"
        readiness_label = "Published"
        readiness_message = "This source is available for AI answers."
        next_action = "none"
        next_action_label = "No action needed"

    elif ready_to_publish or is_validated:
        readiness_status = "ready_to_publish"
        readiness_label = "Ready to Publish"
        readiness_message = "This source is validated and ready to be published."
        next_action = "publish"
        next_action_label = "Publish source"

    elif is_prepared:
        readiness_status = "ready_for_validation"
        readiness_label = "Ready for Validation"
        readiness_message = "This source is prepared and ready for validation."
        next_action = "validate"
        next_action_label = "Validate source"

    elif has_quality_issue:
        readiness_status = "needs_attention"
        readiness_label = "Needs Attention"
        readiness_message = "This source needs review before it can move forward."
        next_action = "review"
        next_action_label = "Review source"

    else:
        readiness_status = "ready"
        readiness_label = "Ready"
        readiness_message = "This source has content and required classification."
        next_action = "prepare"
        next_action_label = "Prepare source"

    can_prepare = readiness_status == "ready"
    can_validate = readiness_status == "ready_for_validation"
    can_publish = readiness_status == "ready_to_publish"
    can_unpublish = readiness_status == "published"

    return {
        "readiness_status": readiness_status,
        "readiness_label": readiness_label,
        "readiness_message": readiness_message,
        "next_action": next_action,
        "next_action_label": next_action_label,
        "can_prepare": 1 if can_prepare else 0,
        "can_validate": 1 if can_validate else 0,
        "can_publish": 1 if can_publish else 0,
        "can_unpublish": 1 if can_unpublish else 0,
        "is_published": 1 if published else 0,
        "missing_fields": missing_fields,
        "has_content": 1 if has_content else 0,
        "has_classification": 1 if has_classification else 0,
        "technical_status": {
        "status": status,
        "processing_status": processing_status,
        "embedding_status": row.get("embedding_status"),
        "diagnostics_status": row.get("diagnostics_status"),
        "processing_version": row.get("processing_version"),
        "chunk_count": row.get("chunk_count"),
        "active_chunk_count": row.get("active_chunk_count"),
        "retrieval_ready": row.get("retrieval_ready"),
        "generated_knowledge_unit": row.get("generated_knowledge_unit"),
        "last_processed_on": row.get("last_processed_on"),
        "validation_status": validation_status,
        "last_error": row.get("last_error") or row.get("error_log"),
    },
        
    }


# -------------------------------------------------------------------------
# Chunk / embedding helpers
# -------------------------------------------------------------------------

def _get_chunk_link_field():
    if not frappe.db.exists("DocType", "Nexus Knowledge Chunk"):
        return None

    meta = frappe.get_meta("Nexus Knowledge Chunk")

    possible_fields = [
        "knowledge_unit",
        "knowledge_unit_id",
        "nexus_knowledge_unit",
        "source_knowledge_unit",
    ]

    for fieldname in possible_fields:
        if meta.has_field(fieldname):
            return fieldname

    return None


def _get_embedding_field():
    if not frappe.db.exists("DocType", "Nexus Knowledge Chunk"):
        return None

    meta = frappe.get_meta("Nexus Knowledge Chunk")

    possible_fields = [
        "embedding",
        "embedding_json",
        "vector",
        "vector_json",
    ]

    for fieldname in possible_fields:
        if meta.has_field(fieldname):
            return fieldname

    return None


def _get_chunk_count(knowledge_unit_name: str) -> int:
    link_field = _get_chunk_link_field()

    if not link_field:
        return 0

    return frappe.db.count(
        "Nexus Knowledge Chunk",
        {
            link_field: knowledge_unit_name,
            "docstatus": ["!=", 2],
        },
    )


def _get_embedded_chunk_count(knowledge_unit_name: str) -> int:
    link_field = _get_chunk_link_field()
    embedding_field = _get_embedding_field()

    if not link_field or not embedding_field:
        return 0

    return frappe.db.count(
        "Nexus Knowledge Chunk",
        {
            link_field: knowledge_unit_name,
            embedding_field: ["not in", ["", None]],
            "docstatus": ["!=", 2],
        },
    )


# -------------------------------------------------------------------------
# Knowledge Unit readiness helpers
# -------------------------------------------------------------------------

def _required_readiness_fields():
    """
    Minimum fields expected before a Knowledge Unit can move forward.
    """
    return [
        "tenant",
        "business_unit",
        "context",
        "content",
    ]


def _build_readiness_payload(doc):
    missing_fields = []

    for fieldname in _required_readiness_fields():
        if _has_field(doc.doctype, fieldname):
            value = doc.get(fieldname)
            if value in (None, ""):
                missing_fields.append(fieldname)

    chunk_count = _get_chunk_count(doc.name)
    embedded_chunk_count = _get_embedded_chunk_count(doc.name)

    disabled = bool(_get_if_exists(doc, "disabled", 0))
    published = bool(_get_if_exists(doc, "published", 0))
    needs_review = bool(_get_if_exists(doc, "needs_review", 0))

    approval_status = _get_if_exists(doc, "approval_status")
    status = _get_if_exists(doc, "status")

    normalized_status = str(status or "").strip().lower()
    normalized_approval = str(approval_status or "").strip().lower()

    is_approved = (
        normalized_approval == "approved"
        or normalized_status in [
            "approved",
            "chunked",
            "embedded",
            "tested",
            "ready to publish",
            "published",
        ]
    )

    is_chunked = chunk_count > 0
    is_embedded = bool(
        chunk_count
        and embedded_chunk_count > 0
        and embedded_chunk_count == chunk_count
    )

    ready_for_chunking = (
        not disabled
        and not needs_review
        and not missing_fields
        and bool(doc.get("content"))
    )

    ready_to_publish = (
        not disabled
        and not needs_review
        and not missing_fields
        and is_approved
        and is_chunked
        and is_embedded
    )

    return {
        "success": True,
        "name": doc.name,
        "title": doc.get("title") or doc.name,
        "tenant": doc.get("tenant") if _has_field(doc.doctype, "tenant") else None,
        "ecosystem": doc.get("ecosystem") if _has_field(doc.doctype, "ecosystem") else None,
        "business_unit": doc.get("business_unit") if _has_field(doc.doctype, "business_unit") else None,
        "project": doc.get("project") if _has_field(doc.doctype, "project") else None,
        "channel": doc.get("channel") if _has_field(doc.doctype, "channel") else None,
        "context": doc.get("context") if _has_field(doc.doctype, "context") else None,
        "sub_context": doc.get("sub_context") if _has_field(doc.doctype, "sub_context") else None,
        "entity_type": doc.get("entity_type") if _has_field(doc.doctype, "entity_type") else None,
        "entity": doc.get("entity") if _has_field(doc.doctype, "entity") else None,
        "topic": doc.get("topic") if _has_field(doc.doctype, "topic") else None,
        "context_path": doc.get("context_path") if _has_field(doc.doctype, "context_path") else None,
        "status": status,
        "approval_status": approval_status,
        "disabled": disabled,
        "published": published,
        "needs_review": needs_review,
        "missing_fields": missing_fields,
        "chunk_count": chunk_count,
        "embedded_chunk_count": embedded_chunk_count,
        "is_approved": is_approved,
        "is_chunked": is_chunked,
        "is_embedded": is_embedded,
        "ready_for_chunking": ready_for_chunking,
        "ready_to_publish": ready_to_publish,
    }


def _get_knowledge_unit_fields():
    meta = frappe.get_meta("Nexus Knowledge Unit")

    fields = ["name", "modified"]

    optional_fields = [
        "title",
        "tenant",
        "ecosystem",
        "business_unit",
        "project",
        "channel",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
        "context_path",
        "status",
        "approval_status",
        "needs_review",
        "content",
        "disabled",
        "published",
    ]

    for fieldname in optional_fields:
        if meta.has_field(fieldname):
            fields.append(fieldname)

    return fields


# -------------------------------------------------------------------------
# Public API methods - Diagnostics
# -------------------------------------------------------------------------

@frappe.whitelist()
def get_active_studio_context():
    """
    Diagnostic method for verifying Studio filter resolution from console.
    """
    active_context = _resolve_active_studio_context()

    source_filters = {}
    unit_filters = {}

    if frappe.db.exists("DocType", "Nexus Knowledge Source"):
        source_filters = _apply_active_context_filters_for_doctype(
            "Nexus Knowledge Source",
            {},
            active_context,
        )

    if frappe.db.exists("DocType", "Nexus Knowledge Unit"):
        unit_filters = _apply_active_context_filters_for_doctype(
            "Nexus Knowledge Unit",
            {},
            active_context,
        )

    return {
        "success": True,
        "active_tenant": active_context.get("tenant"),
        "active_context": active_context,
        "source_filters": source_filters,
        "unit_filters": unit_filters,
    }


# -------------------------------------------------------------------------
# Public API methods - Knowledge Source
# -------------------------------------------------------------------------

@frappe.whitelist()
def get_knowledge_source_summary():
    """
    Returns tenant/user-context scoped Knowledge Source summary counters.
    """

    if not frappe.db.exists("DocType", "Nexus Knowledge Source"):
        return {
            "success": False,
            "message": "Nexus Knowledge Source doctype does not exist.",
        }

    if not frappe.has_permission("Nexus Knowledge Source", "read"):
        frappe.throw("Not permitted to read Nexus Knowledge Source", frappe.PermissionError)

    active_context = _resolve_active_studio_context()

    base_filters = {}
    base_filters = _apply_active_context_filters_for_doctype(
        "Nexus Knowledge Source",
        base_filters,
        active_context,
    )

    total_sources = frappe.db.count("Nexus Knowledge Source", base_filters)

    approved_for_ingestion = 0
    ingested = 0
    partially_ingested = 0
    published = 0
    sync_failed = 0
    stale = 0
    disabled = 0
    context_summary_count = _count_context_summaries(active_context)
    semantic_index_entry_count = _count_semantic_index_entries(active_context)

    rows = frappe.get_all(
        "Nexus Knowledge Source",
        fields=_get_knowledge_source_fields(),
        filters=base_filters,
        limit_page_length=500,
        order_by="modified desc",
    )

    for row in rows:
        status = str(row.get("status") or "").strip()
        sync_status = str(row.get("sync_status") or "").strip()

        if status == "Approved for Ingestion":
            approved_for_ingestion += 1

        if status == "Ingested":
            ingested += 1

        if status == "Partially Ingested":
            partially_ingested += 1

        if status == "Published" or row.get("published"):
            published += 1

        if status == "Stale":
            stale += 1

        if status == "Sync Failed" or sync_status == "Failed":
            sync_failed += 1

        if row.get("disabled"):
            disabled += 1

    return {
        "success": True,
        "active_tenant": active_context.get("tenant"),
        "active_context": active_context,
        "applied_filters": base_filters,
        "summary": {
            "active_tenant": active_context.get("tenant"),
            "active_ecosystem": active_context.get("ecosystem"),
            "active_business_unit": active_context.get("business_unit"),
            "active_project": active_context.get("project"),
            "active_channel": active_context.get("channel"),
            "active_context": active_context.get("context"),
            "total_sources": total_sources,
            "approved_for_ingestion": approved_for_ingestion,
            "ingested": ingested,
            "partially_ingested": partially_ingested,
            "published": published,
            "sync_failed": sync_failed,
            "stale": stale,
            "disabled": disabled,
            "context_summaries": context_summary_count,
            "semantic_index_entries": semantic_index_entry_count,
        },
    }


@frappe.whitelist()
def get_knowledge_sources(filters=None):
    """
    Returns tenant/user-context scoped Knowledge Sources for the Studio page.
    """

    if not frappe.db.exists("DocType", "Nexus Knowledge Source"):
        return {
            "success": False,
            "message": "Nexus Knowledge Source doctype does not exist.",
            "sources": [],
        }

    if not frappe.has_permission("Nexus Knowledge Source", "read"):
        frappe.throw("Not permitted to read Nexus Knowledge Source", frappe.PermissionError)

    filters = frappe.parse_json(filters) if filters else {}
    filters = frappe._dict(filters)

    active_context = _resolve_active_studio_context()

    meta = frappe.get_meta("Nexus Knowledge Source")

    db_filters = {}
    db_filters = _apply_active_context_filters_for_doctype(
        "Nexus Knowledge Source",
        db_filters,
        active_context,
    )

    if filters.get("status") and meta.has_field("status"):
        db_filters["status"] = filters.get("status")

    if filters.get("sync_status") and meta.has_field("sync_status"):
        db_filters["sync_status"] = filters.get("sync_status")

    if filters.get("access_policy") and meta.has_field("access_policy"):
        db_filters["access_policy"] = filters.get("access_policy")

    if filters.get("disabled") in ["0", "1"] and meta.has_field("disabled"):
        db_filters["disabled"] = int(filters.get("disabled"))

    or_filters = []

    if filters.get("search"):
        search = f"%{filters.get('search')}%"

        or_filters.append(["Nexus Knowledge Source", "name", "like", search])

        for fieldname in [
            "source_title",
            "source_type",
            "source_url",
            "source_reference_name",
            "context",
            "topic",
            "entity",
        ]:
            if meta.has_field(fieldname):
                or_filters.append(["Nexus Knowledge Source", fieldname, "like", search])

    rows = frappe.get_all(
        "Nexus Knowledge Source",
        fields=_get_knowledge_source_fields(),
        filters=db_filters,
        or_filters=or_filters if or_filters else None,
        order_by="modified desc",
        limit_page_length=100,
    )

    sources = []

    for row in rows:
        readiness = _build_source_readiness_payload(row)
        test_case_summary = _get_source_test_case_summary(row.get("name"))
        context_summary = _get_source_context_summary(row)
        semantic_index_summary = _get_source_semantic_index_summary(row.get("name"))

        sources.append({
            "name": row.get("name"),
            "source_title": row.get("source_title") or row.get("name"),
            "source_type": row.get("source_type"),
            "tenant": row.get("tenant"),
            "ecosystem": row.get("ecosystem"),
            "business_unit": row.get("business_unit"),
            "project": row.get("project"),
            "channel": row.get("channel"),
            "chat_category": row.get("chat_category"),
            "context": row.get("context"),
            "sub_context": row.get("sub_context"),
            "entity_type": row.get("entity_type"),
            "entity": row.get("entity"),
            "topic": row.get("topic"),
            "access_policy": row.get("access_policy"),
            "priority": row.get("priority"),
            "status": row.get("status"),
            "sync_status": row.get("sync_status"),
            "last_synced_on": row.get("last_synced_on"),
            "disabled": row.get("disabled"),
            "published": row.get("published"),
            "ready_to_publish": row.get("ready_to_publish"),
            "needs_review": row.get("needs_review"),
            "review_reason": row.get("review_reason"),
            "quality_status": row.get("quality_status"),
            "validation_status": row.get("validation_status"),
            "processing_status": row.get("processing_status"),
            "last_error": row.get("last_error"),
            "owner_user": row.get("owner_user"),
            "processing_version": row.get("processing_version"),
            "chunk_count": row.get("chunk_count"),
            "active_chunk_count": row.get("active_chunk_count"),
            "embedding_status": row.get("embedding_status"),
            "diagnostics_status": row.get("diagnostics_status"),
            "retrieval_ready": row.get("retrieval_ready"),
            "last_processed_on": row.get("last_processed_on"),
            "generated_knowledge_unit": row.get("generated_knowledge_unit"),
            "error_log": row.get("error_log"),

            "test_case_summary": test_case_summary,
            "test_case_count": test_case_summary.get("total"),
            "generated_test_case_count": test_case_summary.get("generated"),
            "active_test_case_count": test_case_summary.get("active"),
            "draft_test_case_count": test_case_summary.get("draft"),
            "context_summary": context_summary,
            "context_summary_exists": context_summary.get("exists"),
            "context_summary_status": context_summary.get("status"),
            "semantic_index_summary": semantic_index_summary,
            "semantic_index_count": semantic_index_summary.get("total"),

            **readiness,
        })

    return {
        "success": True,
        "active_tenant": active_context.get("tenant"),
        "active_context": active_context,
        "applied_filters": db_filters,
        "sources": sources,
    }


@frappe.whitelist()
def get_access_policy_options():
    """
    Return active Nexus Access Policy names for Studio source filtering.
    """

    if not frappe.db.exists("DocType", "Nexus Access Policy"):
        return {
            "success": True,
            "access_policies": [],
        }

    if not frappe.has_permission("Nexus Access Policy", "read"):
        return {
            "success": True,
            "access_policies": [],
        }

    meta = frappe.get_meta("Nexus Access Policy")
    filters = {}

    if meta.has_field("disabled"):
        filters["disabled"] = 0

    fields = ["name"]

    if meta.has_field("policy_name"):
        fields.append("policy_name")

    rows = frappe.get_all(
        "Nexus Access Policy",
        fields=fields,
        filters=filters,
        order_by="policy_name asc" if meta.has_field("policy_name") else "name asc",
        limit_page_length=500,
    )

    policies = []

    for row in rows:
        policy = _normalize_context_value(row.get("policy_name") or row.get("name"))

        if policy and policy not in policies:
            policies.append(policy)

    return {
        "success": True,
        "access_policies": policies,
    }

# -------------------------------------------------------------------------
# Public API methods - Knowledge Unit / Studio Overview
# -------------------------------------------------------------------------

@frappe.whitelist()
def get_studio_summary():
    """
    Returns tenant/user-context scoped summary counters for the Nexus Studio page.
    """

    if not frappe.has_permission("Nexus Knowledge Unit", "read"):
        frappe.throw("Not permitted to read Nexus Knowledge Unit", frappe.PermissionError)

    active_context = _resolve_active_studio_context()

    base_filters = {}
    base_filters = _apply_active_context_filters(base_filters, active_context)

    total_units = frappe.db.count("Nexus Knowledge Unit", base_filters)

    approved_units = 0
    needs_review_units = 0
    ready_for_chunking_units = 0
    ready_to_publish_units = 0
    missing_required_units = 0
    chunked_units = 0
    embedded_units = 0

    rows = frappe.get_all(
        "Nexus Knowledge Unit",
        fields=_get_knowledge_unit_fields(),
        filters=base_filters,
        limit_page_length=500,
        order_by="modified desc",
    )

    for row in rows:
        doc = frappe._dict(row)
        doc.doctype = "Nexus Knowledge Unit"

        readiness = _build_readiness_payload(doc)

        if readiness.get("is_approved"):
            approved_units += 1

        if readiness.get("needs_review"):
            needs_review_units += 1

        if readiness.get("ready_for_chunking"):
            ready_for_chunking_units += 1

        if readiness.get("ready_to_publish"):
            ready_to_publish_units += 1

        if readiness.get("missing_fields"):
            missing_required_units += 1

        if readiness.get("is_chunked"):
            chunked_units += 1

        if readiness.get("is_embedded"):
            embedded_units += 1

    return {
        "success": True,
        "active_tenant": active_context.get("tenant"),
        "active_context": active_context,
        "applied_filters": base_filters,
        "summary": {
            "active_tenant": active_context.get("tenant"),
            "active_ecosystem": active_context.get("ecosystem"),
            "active_business_unit": active_context.get("business_unit"),
            "active_project": active_context.get("project"),
            "active_channel": active_context.get("channel"),
            "active_context": active_context.get("context"),
            "total_units": total_units,
            "approved_units": approved_units,
            "needs_review_units": needs_review_units,
            "ready_for_chunking_units": ready_for_chunking_units,
            "ready_to_publish_units": ready_to_publish_units,
            "missing_required_units": missing_required_units,
            "chunked_units": chunked_units,
            "embedded_units": embedded_units,
        },
    }


@frappe.whitelist()
def get_knowledge_units(filters=None):
    """
    Returns tenant/user-context scoped Knowledge Units with readiness details.
    """

    if not frappe.has_permission("Nexus Knowledge Unit", "read"):
        frappe.throw("Not permitted to read Nexus Knowledge Unit", frappe.PermissionError)

    filters = frappe.parse_json(filters) if filters else {}
    filters = frappe._dict(filters)

    active_context = _resolve_active_studio_context()

    meta = frappe.get_meta("Nexus Knowledge Unit")

    db_filters = {}
    db_filters = _apply_active_context_filters(db_filters, active_context)

    if filters.get("status") and meta.has_field("status"):
        db_filters["status"] = filters.get("status")

    if filters.get("needs_review") in ["0", "1"] and meta.has_field("needs_review"):
        db_filters["needs_review"] = int(filters.get("needs_review"))

    or_filters = []

    if filters.get("search"):
        search = f"%{filters.get('search')}%"

        or_filters.append(["Nexus Knowledge Unit", "name", "like", search])

        for fieldname in ["title", "context", "topic", "content"]:
            if meta.has_field(fieldname):
                or_filters.append(["Nexus Knowledge Unit", fieldname, "like", search])

    rows = frappe.get_all(
        "Nexus Knowledge Unit",
        fields=_get_knowledge_unit_fields(),
        filters=db_filters,
        or_filters=or_filters if or_filters else None,
        order_by="modified desc",
        limit_page_length=100,
    )

    units = []

    for row in rows:
        doc = frappe._dict(row)
        doc.doctype = "Nexus Knowledge Unit"

        readiness = _build_readiness_payload(doc)

        if filters.get("only_missing"):
            if not readiness.get("missing_fields"):
                continue

        if filters.get("only_ready_for_chunking"):
            if not readiness.get("ready_for_chunking"):
                continue

        if filters.get("only_ready_to_publish"):
            if not readiness.get("ready_to_publish"):
                continue

        units.append(readiness)

    return {
        "success": True,
        "active_tenant": active_context.get("tenant"),
        "active_context": active_context,
        "applied_filters": db_filters,
        "units": units,
    }


@frappe.whitelist()
def get_knowledge_unit_readiness(name: str):
    """
    Returns readiness details for one Knowledge Unit.
    """

    if not name:
        return {
            "success": False,
            "message": "Knowledge Unit name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Unit", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Unit not found: {name}",
        }

    if not frappe.has_permission("Nexus Knowledge Unit", "read", doc=name):
        frappe.throw("Not permitted to read this Knowledge Unit", frappe.PermissionError)

    doc = frappe.get_doc("Nexus Knowledge Unit", name)
    active_context = _resolve_active_studio_context()
    _enforce_doc_active_tenant(doc, active_context)

    return _build_readiness_payload(doc)


@frappe.whitelist()
def approve_knowledge_unit(name: str):
    """
    Approves a Knowledge Unit for Studio preparation.
    """

    if not name:
        return {
            "success": False,
            "message": "Knowledge Unit name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Unit", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Unit not found: {name}",
        }

    doc = frappe.get_doc("Nexus Knowledge Unit", name)

    if not frappe.has_permission("Nexus Knowledge Unit", "write", doc=doc):
        frappe.throw("Not permitted to update this Knowledge Unit", frappe.PermissionError)

    active_context = _resolve_active_studio_context()
    _enforce_doc_active_tenant(doc, active_context)

    readiness = _build_readiness_payload(doc)

    if readiness.get("missing_fields"):
        return {
            "success": False,
            "message": "Knowledge Unit cannot be approved because required fields are missing.",
            "missing_fields": readiness.get("missing_fields"),
            "readiness": readiness,
        }

    if not doc.get("content"):
        return {
            "success": False,
            "message": "Knowledge Unit cannot be approved without content.",
            "readiness": readiness,
        }

    _set_if_exists(doc, "approval_status", "Approved")
    _set_if_exists(doc, "status", "Approved")
    _set_if_exists(doc, "needs_review", 0)
    _set_if_exists(doc, "review_reason", None)
    _set_if_exists(doc, "approved_on", frappe.utils.now())
    _set_if_exists(doc, "approved_by", frappe.session.user)

    doc.save(ignore_permissions=False)

    return {
        "success": True,
        "message": "Knowledge Unit approved successfully.",
        "readiness": _build_readiness_payload(doc),
    }


@frappe.whitelist()
def mark_knowledge_unit_needs_review(name: str, reason: str = None):
    """
    Marks a Knowledge Unit as needing review.
    """

    if not name:
        return {
            "success": False,
            "message": "Knowledge Unit name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Unit", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Unit not found: {name}",
        }

    doc = frappe.get_doc("Nexus Knowledge Unit", name)

    if not frappe.has_permission("Nexus Knowledge Unit", "write", doc=doc):
        frappe.throw("Not permitted to update this Knowledge Unit", frappe.PermissionError)

    active_context = _resolve_active_studio_context()
    _enforce_doc_active_tenant(doc, active_context)

    _set_if_exists(doc, "needs_review", 1)
    _set_if_exists(doc, "review_reason", reason or "Marked for review from Nexus Studio.")
    _set_if_exists(doc, "status", "Needs Review")
    _set_if_exists(doc, "published", 0)
    _set_if_exists(doc, "ready_to_publish", 0)

    doc.save(ignore_permissions=False)

    return {
        "success": True,
        "message": "Knowledge Unit marked as Needs Review.",
        "readiness": _build_readiness_payload(doc),
    }


@frappe.whitelist()
def clear_knowledge_unit_review(name: str):
    """
    Clears Needs Review state.
    """

    if not name:
        return {
            "success": False,
            "message": "Knowledge Unit name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Unit", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Unit not found: {name}",
        }

    doc = frappe.get_doc("Nexus Knowledge Unit", name)

    if not frappe.has_permission("Nexus Knowledge Unit", "write", doc=doc):
        frappe.throw("Not permitted to update this Knowledge Unit", frappe.PermissionError)

    active_context = _resolve_active_studio_context()
    _enforce_doc_active_tenant(doc, active_context)

    _set_if_exists(doc, "needs_review", 0)
    _set_if_exists(doc, "review_reason", None)

    if str(_get_if_exists(doc, "status", "") or "").strip() == "Needs Review":
        _set_if_exists(doc, "status", "Draft")

    doc.save(ignore_permissions=False)

    return {
        "success": True,
        "message": "Review status cleared.",
        "readiness": _build_readiness_payload(doc),
    }


@frappe.whitelist()
def mark_knowledge_unit_ready_to_publish(name: str):
    """
    Marks a Knowledge Unit as Ready to Publish if readiness checks pass.
    """

    if not name:
        return {
            "success": False,
            "message": "Knowledge Unit name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Unit", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Unit not found: {name}",
        }

    doc = frappe.get_doc("Nexus Knowledge Unit", name)

    if not frappe.has_permission("Nexus Knowledge Unit", "write", doc=doc):
        frappe.throw("Not permitted to update this Knowledge Unit", frappe.PermissionError)

    active_context = _resolve_active_studio_context()
    _enforce_doc_active_tenant(doc, active_context)

    readiness = _build_readiness_payload(doc)

    if not readiness.get("ready_to_publish"):
        return {
            "success": False,
            "message": "Knowledge Unit is not ready to publish.",
            "readiness": readiness,
        }

    _set_if_exists(doc, "status", "Ready to Publish")
    _set_if_exists(doc, "ready_to_publish", 1)

    doc.save(ignore_permissions=False)

    return {
        "success": True,
        "message": "Knowledge Unit marked as Ready to Publish.",
        "readiness": _build_readiness_payload(doc),
    }

# -------------------------------------------------------------------------
# Public API methods - Source Scoped Validation
# -------------------------------------------------------------------------

def _get_doc_text_field(doc, possible_fields):
    for fieldname in possible_fields:
        if _has_field(doc.doctype, fieldname):
            value = _normalize_context_value(doc.get(fieldname))
            if value:
                return value
    return None


def _strip_source_text(value):
    value = value or ""

    try:
        from frappe.utils.html_utils import clean_html
        value = clean_html(value)
    except Exception:
        pass

    try:
        from frappe.utils import strip_html
        value = strip_html(value)
    except Exception:
        pass

    return str(value or "").strip()


def _tokenize_validation_text(value):
    import re

    value = (value or "").lower()
    tokens = re.findall(r"[a-z0-9]+", value)

    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "what", "which",
        "who", "whom", "where", "when", "why", "how", "in", "on", "of",
        "for", "to", "from", "by", "with", "and", "or", "as", "this",
        "that", "these", "those", "explain", "describe", "summarize",
        "overview", "module"
    }

    return [token for token in tokens if token and token not in stop_words]


def _build_default_source_validation_query(doc):
    source_title = _normalize_context_value(
        doc.get("source_title") or doc.get("title") or doc.name
    )
    topic = _normalize_context_value(doc.get("topic")) if _has_field(doc.doctype, "topic") else None
    entity = _normalize_context_value(doc.get("entity")) if _has_field(doc.doctype, "entity") else None
    context = _normalize_context_value(doc.get("context")) if _has_field(doc.doctype, "context") else None
    business_unit = _normalize_context_value(doc.get("business_unit")) if _has_field(doc.doctype, "business_unit") else None

    if topic and context:
        return f"Explain {topic} in {context}."

    if topic and business_unit:
        return f"Explain {topic} in {business_unit}."

    if entity and context:
        return f"Explain {entity} in {context}."

    if source_title:
        return f"What is {source_title}?"

    return "Summarize this knowledge source."


def _is_source_prepared_for_validation(doc):
    status = str(doc.get("status") or "").strip().lower()
    sync_status = str(doc.get("sync_status") or "").strip().lower() if _has_field(doc.doctype, "sync_status") else ""
    processing_status = str(doc.get("processing_status") or "").strip().lower() if _has_field(doc.doctype, "processing_status") else ""

    return (
        status in ["processed", "prepared", "ingested", "ready to publish", "published"]
        or sync_status in ["processed", "completed"]
        or processing_status in ["processed", "completed", "prepared"]
    )


def _safe_set_select_value(doc, fieldname, value):
    """
    Set a Select field only if the option exists.
    Prevents Frappe validation errors when lifecycle labels are not yet
    available in the doctype options.
    """
    if not _has_field(doc.doctype, fieldname):
        return False

    meta = frappe.get_meta(doc.doctype)
    df = meta.get_field(fieldname)

    if not df:
        return False

    if df.fieldtype != "Select":
        doc.set(fieldname, value)
        return True

    options = []
    if df.options:
        options = [x.strip() for x in str(df.options).split("\n") if x.strip()]

    if value in options:
        doc.set(fieldname, value)
        return True

    return False


def _get_source_validation_text_blocks(source_doc):
    """
    Build source-scoped validation context.

    This intentionally does not use the public retrieval route.
    It validates the selected source itself, even before publishing.
    """
    blocks = []

    source_content = _get_doc_text_field(
        source_doc,
        [
            "manual_content",
            "extracted_text",
            "content",
            "source_text",
            "preview_text",
        ],
    )

    if source_content:
        blocks.append({
            "source": source_doc.name,
            "source_type": "Knowledge Source",
            "title": source_doc.get("source_title") or source_doc.name,
            "text": _strip_source_text(source_content),
        })

    # Optional: try to include generated Knowledge Unit content if the schema has a source link.
    if frappe.db.exists("DocType", "Nexus Knowledge Unit"):
        ku_meta = frappe.get_meta("Nexus Knowledge Unit")

        possible_source_link_fields = [
            "knowledge_source",
            "source",
            "source_name",
            "nexus_knowledge_source",
            "source_reference_name",
        ]

        matching_filters = []
        for fieldname in possible_source_link_fields:
            if ku_meta.has_field(fieldname):
                matching_filters.append({fieldname: source_doc.name})

        unit_names = []

        for filters in matching_filters:
            try:
                rows = frappe.get_all(
                    "Nexus Knowledge Unit",
                    filters=filters,
                    fields=["name"],
                    limit_page_length=20,
                )
                unit_names.extend([row.name for row in rows])
            except Exception:
                pass

        # fallback: match by title if no explicit link exists
        if not unit_names and ku_meta.has_field("title"):
            title = source_doc.get("source_title") or source_doc.name
            try:
                rows = frappe.get_all(
                    "Nexus Knowledge Unit",
                    filters={"title": title},
                    fields=["name"],
                    limit_page_length=20,
                )
                unit_names.extend([row.name for row in rows])
            except Exception:
                pass

        unit_names = list(dict.fromkeys(unit_names))

        for unit_name in unit_names:
            try:
                unit_doc = frappe.get_doc("Nexus Knowledge Unit", unit_name)
                unit_content = _get_doc_text_field(
                    unit_doc,
                    ["content", "answer", "body", "description"],
                )

                if unit_content:
                    blocks.append({
                        "source": unit_doc.name,
                        "source_type": "Knowledge Unit",
                        "title": unit_doc.get("title") or unit_doc.name,
                        "text": _strip_source_text(unit_content),
                    })
            except Exception:
                pass

    return [block for block in blocks if block.get("text")]


def _build_source_validation_answer(test_query, blocks):
    """
    Deterministic source-scoped validation.

    This is intentionally not public Q&A.
    It verifies whether the selected source has enough relevant content
    to answer the validation question.

    Later this can be upgraded to LLM-based source-scoped answer generation.
    """
    query_tokens = set(_tokenize_validation_text(test_query))

    best_block = None
    best_score = 0

    for block in blocks:
        block_tokens = set(_tokenize_validation_text(block.get("text")))
        if not block_tokens:
            continue

        overlap = query_tokens.intersection(block_tokens)
        score = len(overlap)

        if score > best_score:
            best_score = score
            best_block = block

    if not best_block and blocks:
        best_block = blocks[0]

    if not best_block:
        return {
            "passed": False,
            "confidence": 0,
            "answer": "No source-scoped validation content was available for this source.",
            "sources": [],
            "reason": "No validation context found.",
        }

    text = best_block.get("text") or ""
    answer = text[:1200].strip()

    if len(text) > 1200:
        answer += "..."

    query_token_count = max(len(query_tokens), 1)
    overlap_ratio = min(best_score / query_token_count, 1)

    confidence = round(0.45 + (overlap_ratio * 0.5), 2)

    passed = confidence >= 0.55 and bool(answer)

    return {
        "passed": passed,
        "confidence": confidence,
        "answer": answer,
        "sources": [
            {
                "name": best_block.get("source"),
                "type": best_block.get("source_type"),
                "title": best_block.get("title"),
            }
        ],
        "reason": "Source-scoped validation completed.",
    }


@frappe.whitelist()
def validate_knowledge_source(name: str, test_query: str = None):
    """
    Validate one prepared Knowledge Source before publishing.

    Important:
    - This does not use the normal public Q&A route.
    - This does not require the source to be published.
    - This validates only the selected source.
    - If validation passes, the source is marked Ready to Publish.
    """

    if not name:
        return {
            "success": False,
            "message": "Knowledge Source name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Source", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Source not found: {name}",
        }

    doc = frappe.get_doc("Nexus Knowledge Source", name)

    if not frappe.has_permission("Nexus Knowledge Source", "read", doc=doc):
        frappe.throw("Not permitted to read this Knowledge Source", frappe.PermissionError)

    if not frappe.has_permission("Nexus Knowledge Source", "write", doc=doc):
        frappe.throw("Not permitted to update this Knowledge Source", frappe.PermissionError)

    active_context = _resolve_active_studio_context()
    _enforce_doc_active_tenant(doc, active_context)

    test_query = _normalize_context_value(test_query) or _build_default_source_validation_query(doc)

    readiness = _build_source_readiness_payload(doc)

    if readiness.get("missing_fields"):
        _set_if_exists(doc, "validation_status", "Failed")
        _set_if_exists(doc, "ready_to_publish", 0)
        _set_if_exists(doc, "needs_review", 1)
        _set_if_exists(doc, "review_reason", "Source validation failed because required fields are missing.")

        _safe_set_select_value(doc, "status", "Pending Review")
        doc.save(ignore_permissions=False)

        return {
            "success": False,
            "message": "Source validation failed because required fields are missing.",
            "test_query": test_query,
            "readiness": _build_source_readiness_payload(doc),
            "missing_fields": readiness.get("missing_fields"),
        }

    if not _is_source_prepared_for_validation(doc):
        return {
            "success": False,
            "message": "Source is not prepared yet. Please process/prepare the source before validation.",
            "test_query": test_query,
            "readiness": readiness,
        }

    blocks = _get_source_validation_text_blocks(doc)
    validation = _build_source_validation_answer(test_query, blocks)

    if validation.get("passed"):
        _set_if_exists(doc, "validation_status", "Passed")
        _set_if_exists(doc, "ready_to_publish", 1)
        _set_if_exists(doc, "needs_review", 0)
        _set_if_exists(doc, "review_reason", None)

        _safe_set_select_value(doc, "status", "Ready to Publish")

        if _has_field(doc.doctype, "validated_on"):
            doc.set("validated_on", frappe.utils.now())

        if _has_field(doc.doctype, "validated_by"):
            doc.set("validated_by", frappe.session.user)

        if _has_field(doc.doctype, "validation_query"):
            doc.set("validation_query", test_query)

        if _has_field(doc.doctype, "validation_confidence"):
            doc.set("validation_confidence", validation.get("confidence"))

        doc.save(ignore_permissions=False)

        return {
            "success": True,
            "message": "Source validation passed. Source is ready to publish.",
            "test_query": test_query,
            "answer": validation.get("answer"),
            "confidence": validation.get("confidence"),
            "sources": validation.get("sources"),
            "readiness": _build_source_readiness_payload(doc),
        }

    _set_if_exists(doc, "validation_status", "Failed")
    _set_if_exists(doc, "ready_to_publish", 0)
    _set_if_exists(doc, "needs_review", 1)
    _set_if_exists(
        doc,
        "review_reason",
        "Source validation failed. The validation question did not sufficiently match the prepared source content.",
    )

    _safe_set_select_value(doc, "status", "Pending Review")

    if _has_field(doc.doctype, "validation_query"):
        doc.set("validation_query", test_query)

    if _has_field(doc.doctype, "validation_confidence"):
        doc.set("validation_confidence", validation.get("confidence"))

    doc.save(ignore_permissions=False)

    return {
        "success": False,
        "message": "Source validation failed. Review the source content or validation question.",
        "test_query": test_query,
        "answer": validation.get("answer"),
        "confidence": validation.get("confidence"),
        "sources": validation.get("sources"),
        "readiness": _build_source_readiness_payload(doc),
    }

# -------------------------------------------------------------------------
# Public API methods - AI Suggested Knowledge Test Cases
# -------------------------------------------------------------------------

def _is_source_published_for_test_generation(source_doc) -> bool:
    """
    Return whether a Knowledge Source is in published/live state.
    """

    status = str(source_doc.get("status") or "").strip().lower()

    return bool(
        status == "published"
        or cint(source_doc.get("published") or 0)
        or cint(source_doc.get("is_published") or 0)
    )


def _get_source_chunk_text_for_test_generation(source_name: str, generated_unit: str = None) -> str:
    """
    Build representative chunk text from Nexus Knowledge Chunk.

    This is defensive because the chunk schema can evolve. It supports either
    knowledge_source/source fields or generated Knowledge Unit link fields.
    """

    if not frappe.db.exists("DocType", "Nexus Knowledge Chunk"):
        return ""

    meta = frappe.get_meta("Nexus Knowledge Chunk")
    fields = {df.fieldname for df in meta.fields}

    text_field = None
    for candidate in ["chunk_text", "content", "text", "chunk_content"]:
        if candidate in fields:
            text_field = candidate
            break

    if not text_field:
        return ""

    filter_candidates = []

    if source_name:
        for candidate in ["knowledge_source", "source", "source_name", "nexus_knowledge_source"]:
            if candidate in fields:
                filter_candidates.append({candidate: source_name})

    if generated_unit:
        for candidate in ["knowledge_unit", "knowledge_unit_id", "nexus_knowledge_unit", "source_knowledge_unit"]:
            if candidate in fields:
                filter_candidates.append({candidate: generated_unit})

    texts = []
    seen_names = set()

    for filters in filter_candidates:
        safe_filters = dict(filters)

        if "disabled" in fields:
            safe_filters["disabled"] = 0

        try:
            rows = frappe.get_all(
                "Nexus Knowledge Chunk",
                filters=safe_filters,
                fields=["name", text_field],
                order_by="creation asc",
                limit_page_length=20,
            )
        except Exception:
            continue

        for row in rows:
            if row.name in seen_names:
                continue

            seen_names.add(row.name)

            value = row.get(text_field)
            if value:
                texts.append(str(value))

    return "\n\n".join(texts)


def _build_source_test_generation_context(source_doc) -> dict:
    """
    Build source metadata and source text used for AI suggested test case generation.

    Preferred content order:
    1. Source text/content fields
    2. Generated Knowledge Unit content
    3. Active chunk text
    """

    content_parts = []

    for fieldname in [
        "manual_content",
        "extracted_text",
        "content",
        "source_content",
        "prepared_content",
        "description",
        "source_text",
        "preview_text",
    ]:
        if _has_field(source_doc.doctype, fieldname):
            value = source_doc.get(fieldname)
            if value:
                content_parts.append(str(value))

    generated_unit = _normalize_context_value(
        source_doc.get("generated_knowledge_unit")
        if _has_field(source_doc.doctype, "generated_knowledge_unit")
        else None
    )

    if generated_unit and frappe.db.exists("Nexus Knowledge Unit", generated_unit):
        try:
            unit_doc = frappe.get_doc("Nexus Knowledge Unit", generated_unit)
            for fieldname in ["content", "knowledge_text", "body", "description", "summary", "answer"]:
                if _has_field(unit_doc.doctype, fieldname):
                    value = unit_doc.get(fieldname)
                    if value:
                        content_parts.append(str(value))
        except Exception:
            frappe.log_error(
                title="Failed reading generated Knowledge Unit for test generation",
                message=frappe.get_traceback(),
            )

    chunk_text = _get_source_chunk_text_for_test_generation(source_doc.name, generated_unit)
    if chunk_text:
        content_parts.append(chunk_text)

    compact_content = _compact_test_generation_text(
        "\n\n".join([str(part).strip() for part in content_parts if str(part).strip()])
    )

    return {
        "source_name": source_doc.name,
        "source_title": source_doc.get("source_title") or source_doc.name,
        "source_type": source_doc.get("source_type") or "",
        "tenant": source_doc.get("tenant") if _has_field(source_doc.doctype, "tenant") else "",
        "ecosystem": source_doc.get("ecosystem") if _has_field(source_doc.doctype, "ecosystem") else "",
        "business_unit": source_doc.get("business_unit") if _has_field(source_doc.doctype, "business_unit") else "",
        "project": source_doc.get("project") if _has_field(source_doc.doctype, "project") else "",
        "channel": source_doc.get("channel") if _has_field(source_doc.doctype, "channel") else "",
        "context": source_doc.get("context") if _has_field(source_doc.doctype, "context") else "",
        "sub_context": source_doc.get("sub_context") if _has_field(source_doc.doctype, "sub_context") else "",
        "entity_type": source_doc.get("entity_type") if _has_field(source_doc.doctype, "entity_type") else "",
        "entity": source_doc.get("entity") if _has_field(source_doc.doctype, "entity") else "",
        "topic": source_doc.get("topic") if _has_field(source_doc.doctype, "topic") else "",
        "access_policy": (
            source_doc.get("access_policy")
            if _has_field(source_doc.doctype, "access_policy")
            else source_doc.get("access_level")
            if _has_field(source_doc.doctype, "access_level")
            else ""
        ),
        "generated_knowledge_unit": generated_unit,
        "content": compact_content[:12000],
    }


def _build_test_case_generation_prompt(
    source_context: dict,
    test_count: int,
    use_case: str,
    include_boundary_tests: int,
    include_followup_tests: int,
) -> str:
    return f"""
Generate {test_count} validation test cases for this published Knowledge Source.

Return JSON only in this exact shape:
{{
  "test_cases": [
    {{
      "title": "short validation title",
      "question": "realistic user-facing question",
      "test_type": "direct|follow_up|boundary|fallback|access",
      "expected_behavior": "what the AI should do",
      "expected_result_type": "grounded_answer|safe_fallback|escalation",
      "expected_fallback": false,
      "minimum_confidence": 0.7,
      "required_keywords": ["keyword1", "keyword2"],
      "forbidden_keywords": []
    }}
  ]
}}

Rules:
- Generate realistic questions a real user may ask.
- Validate retrieval and answer quality from this published source.
- Prefer direct answer tests.
- Include follow-up style questions only if requested.
- Include fallback/boundary tests only if requested.
- Do not invent source facts.
- Do not expose or request confidential content for public sources.
- Questions must be useful for {use_case}.

Include boundary tests: {"yes" if include_boundary_tests else "no"}
Include follow-up tests: {"yes" if include_followup_tests else "no"}

Source Metadata:
- Source Name: {source_context.get("source_name")}
- Source Title: {source_context.get("source_title")}
- Source Type: {source_context.get("source_type")}
- Tenant: {source_context.get("tenant")}
- Ecosystem: {source_context.get("ecosystem")}
- Business Unit: {source_context.get("business_unit")}
- Project: {source_context.get("project")}
- Channel: {source_context.get("channel")}
- Context: {source_context.get("context")}
- Sub Context: {source_context.get("sub_context")}
- Entity Type: {source_context.get("entity_type")}
- Entity: {source_context.get("entity")}
- Topic: {source_context.get("topic")}
- Access Policy: {source_context.get("access_policy")}

Source Content:
{source_context.get("content")}
"""


def _generate_test_case_suggestions_with_llm(
    source_context: dict,
    test_count: int,
    use_case: str,
    include_boundary_tests: int,
    include_followup_tests: int,
) -> list:
    """
    LLM-based generation. Falls back safely when the LLM provider/settings
    are unavailable.
    """

    try:
        settings = frappe.get_single("Nexus Settings")
    except Exception:
        return []

    try:
        api_key = settings.get_password("api_key")
    except Exception:
        api_key = None

    if not api_key:
        return []

    model = (
        getattr(settings, "llm_model", None)
        or getattr(settings, "default_llm_model", None)
        or "gpt-4o-mini"
    )

    try:
        from openai import OpenAI
    except Exception:
        return []

    client_kwargs = {"api_key": api_key}

    project_id = getattr(settings, "openai_project_id", None)
    if project_id:
        client_kwargs["project"] = project_id

    prompt = _build_test_case_generation_prompt(
        source_context=source_context,
        test_count=test_count,
        use_case=use_case,
        include_boundary_tests=include_boundary_tests,
        include_followup_tests=include_followup_tests,
    )

    try:
        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate validation test cases for an enterprise RAG knowledge system. "
                        "Return only valid JSON. Do not include markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        content = response.choices[0].message.content or ""
        return _parse_llm_test_case_json(content)

    except Exception:
        frappe.log_error(
            title="LLM Test Case Generation Failed",
            message=frappe.get_traceback(),
        )
        return []


def _parse_llm_test_case_json(content: str) -> list:
    if not content:
        return []

    cleaned = str(content or "").strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        data = json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return []

        try:
            data = json.loads(match.group(0))
        except Exception:
            return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict) and isinstance(data.get("test_cases"), list):
        return data.get("test_cases")

    return []


def _generate_deterministic_source_test_cases(
    source_context: dict,
    test_count: int,
    use_case: str,
    include_boundary_tests: int,
    include_followup_tests: int,
) -> list:
    """
    Deterministic fallback. This ensures the Studio action still works
    when the LLM provider is not configured.

    Important:
    - Direct/follow-up tests expect grounded answers with source evidence.
    - Boundary/fallback tests expect safe fallback behavior and should not
      require source evidence or high confidence.

    MVP confidence calibration:
    - Current answer service confidence for correct grounded answers is commonly around 0.35–0.45.
    - Therefore grounded tests use 0.35 for now.
    - Fallback tests use 0.30.
    """

    DIRECT_MIN_CONFIDENCE = 0.35
    FOLLOWUP_MIN_CONFIDENCE = 0.35
    FALLBACK_MIN_CONFIDENCE = 0.30

    source_title = (
        source_context.get("source_title")
        or source_context.get("topic")
        or source_context.get("entity")
        or "this knowledge source"
    )

    topic = source_context.get("topic") or source_context.get("entity") or source_title
    context = source_context.get("context") or source_context.get("business_unit") or ""
    access_policy = _normalize_access_level(source_context.get("access_policy") or "Public")

    suggestions = []

    if topic and context:
        suggestions.append({
            "title": f"Explain {topic}",
            "question": f"Explain {topic} in {context}.",
            "test_type": "direct",
            "expected_behavior": "Answer from the published source using grounded information.",
            "expected_result_type": "grounded_answer",
            "expected_fallback": False,
            "expected_source_required": True,
            "minimum_confidence": DIRECT_MIN_CONFIDENCE,
            "required_keywords": _keywords_from_test_generation_text(f"{topic} {context}"),
            "forbidden_keywords": [],
        })

    suggestions.append({
        "title": f"Summarize {source_title}",
        "question": f"What is {source_title}?",
        "test_type": "direct",
        "expected_behavior": "Provide a concise grounded answer from the published source.",
        "expected_result_type": "grounded_answer",
        "expected_fallback": False,
        "expected_source_required": True,
        "minimum_confidence": DIRECT_MIN_CONFIDENCE,
        "required_keywords": _keywords_from_test_generation_text(str(source_title)),
        "forbidden_keywords": [],
    })

    suggestions.append({
        "title": f"Business use of {topic}",
        "question": f"How is {topic} useful in business operations?",
        "test_type": "direct",
        "expected_behavior": "Explain the business relevance using only approved source knowledge.",
        "expected_result_type": "grounded_answer",
        "expected_fallback": False,
        "expected_source_required": True,
        "minimum_confidence": DIRECT_MIN_CONFIDENCE,
        "required_keywords": _keywords_from_test_generation_text(str(topic)),
        "forbidden_keywords": [],
    })

    if include_followup_tests:
        suggestions.append({
            "title": f"Follow-up on {topic}",
            "question": f"Can you explain that with more details about {topic}?",
            "test_type": "follow_up",
            "expected_behavior": "Handle the follow-up while staying grounded in the same published source.",
            "expected_result_type": "grounded_answer",
            "expected_fallback": False,
            "expected_source_required": True,
            "minimum_confidence": FOLLOWUP_MIN_CONFIDENCE,
            "required_keywords": _keywords_from_test_generation_text(str(topic)),
            "forbidden_keywords": [],
        })

    if include_boundary_tests:
        suggestions.append({
            "title": f"Boundary test for {source_title}",
            "question": f"What confidential internal pricing or private implementation details are available for {source_title}?",
            "test_type": "boundary",
            "expected_behavior": (
                "Do not expose unavailable or restricted information. "
                "Use safe fallback if the source does not contain the answer."
            ),
            "expected_result_type": "safe_fallback",
            "expected_fallback": True,
            "expected_source_required": False,
            "minimum_confidence": FALLBACK_MIN_CONFIDENCE,
            "required_keywords": [],
            "forbidden_keywords": ["secret", "private key", "api key"],
        })

    return suggestions[:test_count]

def _generate_test_case_suggestions(
    source_context: dict,
    test_count: int,
    use_case: str,
    include_boundary_tests: int,
    include_followup_tests: int,
) -> list:
    llm_suggestions = _generate_test_case_suggestions_with_llm(
        source_context=source_context,
        test_count=test_count,
        use_case=use_case,
        include_boundary_tests=include_boundary_tests,
        include_followup_tests=include_followup_tests,
    )

    if llm_suggestions:
        return llm_suggestions[:test_count]

    return _generate_deterministic_source_test_cases(
        source_context=source_context,
        test_count=test_count,
        use_case=use_case,
        include_boundary_tests=include_boundary_tests,
        include_followup_tests=include_followup_tests,
    )


def _split_test_generation_keywords(value: str) -> list:
    if not value:
        return []

    return [
        item.strip()
        for item in re.split(r"[,;\n]", str(value))
        if item and item.strip()
    ]


def _keywords_from_test_generation_text(value: str) -> list:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]+", str(value or "").lower())

    stop_words = {
        "the", "and", "for", "with", "from", "this", "that", "what",
        "how", "why", "when", "where", "into", "about", "explain",
        "use", "used", "using", "business", "operations",
    }

    keywords = []
    for word in words:
        if word in stop_words:
            continue

        if word not in keywords:
            keywords.append(word)

        if len(keywords) >= 5:
            break

    return keywords


def _normalize_test_case_suggestion(
    suggestion: dict,
    use_case: str,
    source_content: str = "",
) -> dict:
    """
    Normalize AI/deterministic suggested test case into the Test Case schema.

    Rules:
    - Direct/follow_up tests expect grounded answers and source evidence.
    - Fallback/boundary/access tests expect safe fallback and should not require source evidence.
    - If the LLM wrongly marks an answerable source question as fallback/boundary/access,
      correct it back to direct.
    - Broad/general questions about the source itself are direct, not fallback.
    - Questions asking policy/rule details not present in the source must remain fallback.

    MVP confidence calibration:
    - Current answer service confidence for correct grounded answers is commonly around 0.35–0.45.
    - Therefore grounded tests use 0.35 for now.
    - Fallback tests use 0.30.
    """

    DIRECT_MIN_CONFIDENCE = 0.35
    FALLBACK_MIN_CONFIDENCE = 0.30

    if not isinstance(suggestion, dict):
        return {}

    title = (
        suggestion.get("title")
        or suggestion.get("test_title")
        or suggestion.get("case_title")
        or suggestion.get("name")
        or ""
    )

    question = (
        suggestion.get("question")
        or suggestion.get("query")
        or suggestion.get("test_query")
        or ""
    )

    test_type = str(suggestion.get("test_type") or "direct").strip().lower()
    expected_result_type = str(
        suggestion.get("expected_result_type") or "grounded_answer"
    ).strip().lower()

    source_text = str(source_content or "").lower()
    question_text = f"{title} {question}".lower()

    source_subject_signals = [
        "purchase invoice",
        "purchase invoices",
    ]

    broad_question_signals = [
        "tell me about",
        "what is",
        "overview",
        "general overview",
        "explain",
        "describe",
        "summarize",
        "how does",
        "what happens",
        "what are",
        "purpose",
        "functionality",
    ]

    mentions_source_subject = any(
        signal in source_text and signal in question_text
        for signal in source_subject_signals
    )

    is_broad_answerable_question = (
        mentions_source_subject
        and any(signal in question_text for signal in broad_question_signals)
    )

    answerable_signal_groups = [
        {
            "source_signals": [
                "purchase invoice",
                "record supplier bills",
                "financial ledgers",
                "expenses",
                "taxes",
                "payables",
                "accounts payable",
                "financial recognition",
            ],
            "question_signals": [
                "purpose",
                "purchase invoice",
                "supplier bill",
                "payable",
                "expense",
                "liability",
                "financial recognition",
            ],
        },
        {
            "source_signals": [
                "supplier",
                "posting date",
                "items / services",
                "taxability",
                "line item discount",
                "rate includes tax",
                "project / cost center",
            ],
            "question_signals": [
                "key fields",
                "fields",
                "supplier",
                "posting date",
                "taxability",
                "rate includes tax",
                "project",
                "cost center",
            ],
        },
        {
            "source_signals": [
                "default company purchase price list",
                "supplier does not have a specific price list assigned",
                "specific price list assigned",
                "price list assigned",
                "use supplier last price",
                "supplier price lists",
            ],
            "question_signals": [
                "supplier",
                "price list",
                "assigned",
                "default company purchase price list",
                "last price",
                "pricing",
            ],
        },
        {
            "source_signals": [
                "service billing",
                "service-type items",
                "without affecting stock",
                "expense entries",
                "do not involve inventory",
                "maintenance",
                "consultancy",
                "professional services",
            ],
            "question_signals": [
                "service billing",
                "service",
                "stock",
                "inventory",
                "expense",
                "maintenance",
                "consultancy",
            ],
        },
        {
            "source_signals": [
                "purchase receipt handles the physical movement of stock",
                "purchase invoice handles the financial posting",
                "financial posting",
                "physical movement of stock",
                "while the purchase receipt handles the physical movement of stock",
            ],
            "question_signals": [
                "purchase receipt",
                "purchase invoice",
                "stock movement",
                "financial posting",
                "difference",
                "physical movement",
            ],
        },
        {
            "source_signals": [
                "on submission",
                "accounting entries",
                "accounts payable",
                "payment mode",
                "expense and tax accounts",
                "rate includes tax",
                "perpetual inventory",
                "cash or bank",
            ],
            "question_signals": [
                "submitted",
                "submission",
                "posting",
                "accounting entries",
                "accounts payable",
                "payment mode",
                "tax",
                "cash",
                "bank",
            ],
        },
        {
            "source_signals": [
                "supplier ledger",
                "purchase receipt",
                "accounting reports",
                "tax reports",
                "project / cost center",
                "price lists and supplier records",
                "profit & loss",
                "trial balance",
                "general ledger",
            ],
            "question_signals": [
                "integration",
                "integrates",
                "supplier ledger",
                "reports",
                "purchase receipt",
                "tax reports",
                "general ledger",
                "trial balance",
            ],
        },
    ]

    looks_answerable_from_source = is_broad_answerable_question

    if not looks_answerable_from_source:
        for group in answerable_signal_groups:
            source_has_signal = any(
                signal in source_text
                for signal in group.get("source_signals") or []
            )

            question_has_signal = any(
                signal in question_text
                for signal in group.get("question_signals") or []
            )

            if source_has_signal and question_has_signal:
                looks_answerable_from_source = True
                break

    unanswered_policy_question_signals = [
        "future date",
        "future posting date",
        "posted with a future date",
        "posting with a future date",
        "allowed or not",
        "is allowed",
        "not allowed",
        "can a purchase invoice be posted",
        "can it be posted",
        "without a recognized supplier",
        "without a valid supplier",
        "non-existent supplier",
        "unrecognized supplier",
        "missing supplier",
        "supplier master record is missing",
        "internal approval matrix",
        "approval matrix",
        "confidential",
        "internal pricing",
        "private implementation",
    ]

    source_contains_policy_answer_signals = [
        "future date is allowed",
        "future posting date is allowed",
        "future date is not allowed",
        "cannot be posted with a future date",
        "can be posted with a future date",
        "recognized supplier",
        "valid supplier",
        "unrecognized supplier",
        "supplier master record",
        "approval matrix",
        "internal approval",
    ]

    asks_unanswered_policy_question = any(
        signal in question_text
        for signal in unanswered_policy_question_signals
    )

    source_has_policy_answer = any(
        signal in source_text
        for signal in source_contains_policy_answer_signals
    )

    if asks_unanswered_policy_question and not source_has_policy_answer:
        looks_answerable_from_source = False
        test_type = "fallback"
        expected_result_type = "safe_fallback"
        suggestion["expected_fallback"] = True
        suggestion["minimum_confidence"] = FALLBACK_MIN_CONFIDENCE
        suggestion["required_keywords"] = []

    if looks_answerable_from_source:
        if test_type in ["fallback", "boundary", "access"]:
            test_type = "direct"

        expected_result_type = "grounded_answer"
        suggestion["expected_fallback"] = False

    if test_type == "boundary" and expected_result_type == "grounded_answer":
        test_type = "direct"

    is_fallback_style_test = (
        test_type in ["fallback", "boundary", "access"]
        or expected_result_type == "safe_fallback"
    )

    expected_fallback = suggestion.get("expected_fallback")

    if expected_fallback is None:
        expected_fallback = is_fallback_style_test

    required_keywords = suggestion.get("required_keywords") or []
    forbidden_keywords = suggestion.get("forbidden_keywords") or []

    if isinstance(required_keywords, str):
        required_keywords = _split_test_generation_keywords(required_keywords)

    if isinstance(forbidden_keywords, str):
        forbidden_keywords = _split_test_generation_keywords(forbidden_keywords)

    if is_fallback_style_test:
        required_keywords = []

    # Important:
    # Do not trust the LLM suggested threshold for MVP.
    # We use calibrated platform thresholds instead.
    minimum_confidence = (
        FALLBACK_MIN_CONFIDENCE
        if is_fallback_style_test
        else DIRECT_MIN_CONFIDENCE
    )

    return {
        "title": str(title or question or "Suggested Knowledge Test Case").strip(),
        "question": str(question or "").strip(),
        "test_type": test_type or "direct",
        "expected_behavior": str(suggestion.get("expected_behavior") or "").strip(),
        "expected_result_type": expected_result_type or "grounded_answer",
        "expected_fallback": 1 if expected_fallback else 0,
        "expected_source_required": 0 if is_fallback_style_test else 1,
        "minimum_confidence": minimum_confidence,
        "required_keywords": required_keywords,
        "forbidden_keywords": forbidden_keywords,
        "use_case": use_case or "Q&A",
    }
                   
def _set_first_available_test_case_field(doc, fields, value):
    for fieldname in fields:
        if _has_field(doc.doctype, fieldname):
            doc.set(fieldname, value)
            return fieldname
    return None

def _normalize_access_level(value):
	"""
	Normalize source access policy into Nexus Knowledge Test Case Select options.

	Test Case JSON options:
	- Public
	- Internal
	- Restricted
	"""

	value = str(value or "").strip()

	if not value:
		return "Public"

	normalized = value.lower().replace("_", " ").replace("-", " ").strip()

	if normalized in ["public", "pub"]:
		return "Public"

	if normalized in ["internal", "private", "company internal"]:
		return "Internal"

	if normalized in ["restricted", "role based", "role based access", "protected"]:
		return "Restricted"

	return "Public"

def _apply_test_case_values(doc, source_doc, normalized: dict, use_case: str, auto_enable: int):
    """
    Apply generated values to Nexus Knowledge Test Case using defensive field mapping.
    """

    def normalize_access_level(value):
        value = str(value or "").strip()

        if not value:
            return "Public"

        normalized_value = value.lower().replace("_", " ").replace("-", " ").strip()

        if normalized_value in ["public", "pub"]:
            return "Public"

        if normalized_value in ["internal", "private", "company internal"]:
            return "Internal"

        if normalized_value in ["restricted", "role based", "role based access", "protected"]:
            return "Restricted"

        return "Public"

    title = normalized.get("title") or "Suggested Knowledge Test Case"
    question = normalized.get("question") or ""

    _set_first_available_test_case_field(doc, ["test_title", "title", "case_title"], title)
    _set_first_available_test_case_field(doc, ["question", "query", "test_query"], question)

    for fieldname in [
        "tenant",
        "ecosystem",
        "business_unit",
        "project",
        "channel",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
    ]:
        if _has_field(source_doc.doctype, fieldname):
            _set_if_exists(doc, fieldname, source_doc.get(fieldname))

    _set_first_available_test_case_field(
        doc,
        ["knowledge_source", "source", "linked_knowledge_source", "expected_source"],
        source_doc.name,
    )

    _set_first_available_test_case_field(
        doc,
        ["source_title", "expected_source_title"],
        source_doc.get("source_title") or source_doc.name,
    )

    _set_first_available_test_case_field(
        doc,
        ["use_case", "response_mode", "expected_response_mode"],
        use_case or "Q&A",
    )

    raw_access_policy = (
        source_doc.get("access_policy")
        if _has_field(source_doc.doctype, "access_policy")
        else source_doc.get("access_level")
        if _has_field(source_doc.doctype, "access_level")
        else "Public"
    )

    access_policy = normalize_access_level(raw_access_policy)

    _set_first_available_test_case_field(
        doc,
        ["expected_access_level", "access_policy", "access_level"],
        access_policy,
    )

    _set_first_available_test_case_field(
        doc,
        ["test_type", "case_type"],
        normalized.get("test_type") or "direct",
    )

    _set_first_available_test_case_field(
        doc,
        ["expected_behavior", "expected_answer_behavior"],
        normalized.get("expected_behavior"),
    )

    _set_first_available_test_case_field(
        doc,
        ["expected_result_type", "result_type"],
        normalized.get("expected_result_type") or "grounded_answer",
    )

    _set_first_available_test_case_field(
        doc,
        ["minimum_confidence", "min_confidence", "expected_min_confidence"],
        normalized.get("minimum_confidence") or 0.7,
    )

    _set_first_available_test_case_field(
        doc,
        ["expected_fallback", "fallback_expected"],
        1 if normalized.get("expected_fallback") else 0,
    )
    
    _set_first_available_test_case_field(
        doc,
        ["expected_source_required"],
        1 if normalized.get("expected_source_required", 1) else 0,
    )

    _set_first_available_test_case_field(
        doc,
        ["generated_by_ai", "ai_generated"],
        1,
    )

    _set_first_available_test_case_field(
        doc,
        ["generated_from_source", "source_generated"],
        1,
    )

    _set_first_available_test_case_field(
        doc,
        ["enabled", "is_enabled"],
        1 if auto_enable else 0,
    )

    _set_first_available_test_case_field(
        doc,
        ["status", "test_status"],
        "Active" if auto_enable else "Draft",
    )

    _set_first_available_test_case_field(
        doc,
        ["review_status"],
        "Approved" if auto_enable else "Pending Review",
    )

    _set_first_available_test_case_field(
        doc,
        ["required_keywords", "expected_keywords"],
        json.dumps(normalized.get("required_keywords") or []),
    )

    _set_first_available_test_case_field(
        doc,
        ["forbidden_keywords"],
        json.dumps(normalized.get("forbidden_keywords") or []),
    )

    _set_first_available_test_case_field(
        doc,
        ["generation_notes", "notes", "description"],
        "AI-generated suggested test case from published Knowledge Source. Review before final validation use.",
    )

    _set_first_available_test_case_field(
        doc,
        ["generated_on"],
        now_datetime(),
    )

def _fill_missing_mandatory_test_case_fields(doc, source_doc, normalized: dict):
    """
    Best-effort fill for required fields in the Test Case DocType.

    This prevents avoidable validation failures when the DocType contains
    mandatory generic fields.
    """

    title = normalized.get("title") or "Suggested Knowledge Test Case"
    question = normalized.get("question") or title

    meta = frappe.get_meta(doc.doctype)

    link_defaults = {
        "Nexus Knowledge Source": source_doc.name,
        "Nexus Tenant": source_doc.get("tenant") if _has_field(source_doc.doctype, "tenant") else None,
        "Nexus Business Unit": source_doc.get("business_unit") if _has_field(source_doc.doctype, "business_unit") else None,
        "Nexus Project": source_doc.get("project") if _has_field(source_doc.doctype, "project") else None,
    }

    for df in meta.fields:
        if not df.reqd:
            continue

        if doc.get(df.fieldname) not in (None, ""):
            continue

        if df.fieldtype in ["Data", "Small Text", "Text", "Long Text", "Code"]:
            doc.set(df.fieldname, question if "question" in df.fieldname else title)
            continue

        if df.fieldtype == "Select":
            options = [x.strip() for x in str(df.options or "").split("\n") if x.strip()]
            if "Draft" in options:
                doc.set(df.fieldname, "Draft")
            elif "Active" in options:
                doc.set(df.fieldname, "Active")
            elif options:
                doc.set(df.fieldname, options[0])
            continue

        if df.fieldtype in ["Check"]:
            doc.set(df.fieldname, 0)
            continue

        if df.fieldtype in ["Int", "Float", "Currency", "Percent"]:
            doc.set(df.fieldname, 0)
            continue

        if df.fieldtype == "Link":
            value = link_defaults.get(df.options)
            if value:
                doc.set(df.fieldname, value)
            continue


def _find_existing_source_test_case(source_name: str, question: str):
    if not frappe.db.exists("DocType", "Nexus Knowledge Test Case"):
        return None

    meta = frappe.get_meta("Nexus Knowledge Test Case")
    fields = {df.fieldname for df in meta.fields}

    source_field = None
    for candidate in ["knowledge_source", "source", "linked_knowledge_source", "expected_source"]:
        if candidate in fields:
            source_field = candidate
            break

    question_field = None
    for candidate in ["question", "query", "test_query"]:
        if candidate in fields:
            question_field = candidate
            break

    if not source_field or not question_field:
        return None

    existing = frappe.get_all(
        "Nexus Knowledge Test Case",
        filters={
            source_field: source_name,
            question_field: question,
        },
        pluck="name",
        limit_page_length=1,
    )

    return existing[0] if existing else None


def _compact_test_generation_text(value: str) -> str:
    value = str(value or "")
    value = re.sub(r"\r\n", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = re.sub(r"[ \t]{2,}", " ", value)
    return value.strip()

def _get_existing_generated_test_cases_for_source(source_name: str):
    """
    Return existing AI-generated test cases for a Knowledge Source.

    This prevents repeated clicks on Generate Test Cases from creating
    duplicate draft validation scenarios for the same published source.
    """

    if not source_name:
        return []

    if not frappe.db.exists("DocType", "Nexus Knowledge Test Case"):
        return []

    meta = frappe.get_meta("Nexus Knowledge Test Case")
    fields = {df.fieldname for df in meta.fields}

    source_field = None

    for candidate in ["knowledge_source", "source", "linked_knowledge_source", "expected_source"]:
        if candidate in fields:
            source_field = candidate
            break

    if not source_field:
        return []

    filters = {
        source_field: source_name,
    }

    if "generated_by_ai" in fields:
        filters["generated_by_ai"] = 1

    if "generated_from_source" in fields:
        filters["generated_from_source"] = 1

    result_fields = ["name"]

    for fieldname in ["test_title", "title", "question", "status", "enabled"]:
        if fieldname in fields:
            result_fields.append(fieldname)

    return frappe.get_all(
        "Nexus Knowledge Test Case",
        filters=filters,
        fields=result_fields,
        order_by="creation desc",
        limit_page_length=100,
    )
    
def _get_source_test_case_summary(source_name: str):
    """
    Return Knowledge Test Case counts for a Knowledge Source.
    Used by Source Dashboard to show whether generated tests already exist.
    """

    summary = {
        "total": 0,
        "generated": 0,
        "draft": 0,
        "active": 0,
        "enabled": 0,
        "pending_review": 0,
        "approved": 0,
        "latest_test_case": None,
        "has_test_cases": 0,
    }

    if not source_name:
        return summary

    if not frappe.db.exists("DocType", "Nexus Knowledge Test Case"):
        return summary

    meta = frappe.get_meta("Nexus Knowledge Test Case")
    fields = {df.fieldname for df in meta.fields}

    source_field = None
    for candidate in ["knowledge_source", "source", "linked_knowledge_source", "expected_source"]:
        if candidate in fields:
            source_field = candidate
            break

    if not source_field:
        return summary

    result_fields = ["name", "creation"]

    for fieldname in [
        "test_title",
        "status",
        "enabled",
        "generated_by_ai",
        "generated_from_source",
        "review_status",
    ]:
        if fieldname in fields:
            result_fields.append(fieldname)

    rows = frappe.get_all(
        "Nexus Knowledge Test Case",
        filters={source_field: source_name},
        fields=result_fields,
        order_by="creation desc",
        limit_page_length=500,
    )

    summary["total"] = len(rows)
    summary["has_test_cases"] = 1 if rows else 0

    if rows:
        latest = rows[0]
        summary["latest_test_case"] = {
            "name": latest.get("name"),
            "test_title": latest.get("test_title") or latest.get("name"),
            "status": latest.get("status"),
            "review_status": latest.get("review_status"),
        }

    for row in rows:
        status = str(row.get("status") or "").strip().lower()
        review_status = str(row.get("review_status") or "").strip().lower()

        if row.get("generated_by_ai") or row.get("generated_from_source"):
            summary["generated"] += 1

        if status == "draft":
            summary["draft"] += 1

        if status == "active":
            summary["active"] += 1

        if row.get("enabled"):
            summary["enabled"] += 1

        if review_status == "pending review":
            summary["pending_review"] += 1

        if review_status == "approved":
            summary["approved"] += 1

    return summary

@frappe.whitelist()
def generate_source_test_cases(
    name: str,
    test_count: int = 5,
    use_case: str = "Q&A",
    include_boundary_tests: int = 1,
    include_followup_tests: int = 1,
    auto_enable: int = 0,
):
    """
    Generate suggested Nexus Knowledge Test Case records from a published Knowledge Source.

    Design:
    - Invoked after a Knowledge Source is published.
    - Test cases are generated as draft suggestions by default.
    - Created test cases are linked back to the Knowledge Source when the Test Case schema supports it.
    """

    if not name:
        return {
            "success": False,
            "message": "Knowledge Source name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Source", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Source not found: {name}",
        }

    if not frappe.db.exists("DocType", "Nexus Knowledge Test Case"):
        return {
            "success": False,
            "message": "Nexus Knowledge Test Case doctype does not exist.",
        }

    source_doc = frappe.get_doc("Nexus Knowledge Source", name)

    if not frappe.has_permission("Nexus Knowledge Source", "read", doc=source_doc):
        frappe.throw("Not permitted to read this Knowledge Source", frappe.PermissionError)

    if not frappe.has_permission("Nexus Knowledge Test Case", "create"):
        frappe.throw("Not permitted to create Nexus Knowledge Test Case", frappe.PermissionError)

    active_context = _resolve_active_studio_context()
    _enforce_doc_active_tenant(source_doc, active_context)

    if not _is_source_published_for_test_generation(source_doc):
        return {
            "success": False,
            "message": "Suggested test cases can be generated only after the Knowledge Source is published.",
        }

    test_count = cint(test_count or 5)

    if test_count <= 0:
        test_count = 5

    if test_count > 20:
        test_count = 20

    include_boundary_tests = cint(include_boundary_tests)
    include_followup_tests = cint(include_followup_tests)
    auto_enable = cint(auto_enable)

    source_context = _build_source_test_generation_context(source_doc)

    if not source_context.get("content"):
        return {
            "success": False,
            "message": "No source content or active chunk content found for generating test cases.",
        }
    
    existing_generated = _get_existing_generated_test_cases_for_source(source_doc.name)

    if existing_generated:
        return {
            "success": True,
            "message": (
                f"{len(existing_generated)} AI-generated Knowledge Test Case(s) already exist "
                "for this Knowledge Source. No duplicate test cases were created."
            ),
            "created": [],
            "skipped": [
                {
                    "name": row.get("name"),
                    "title": row.get("test_title") or row.get("title") or row.get("name"),
                    "reason": "AI-generated test case already exists for this source.",
                }
                for row in existing_generated
            ],
            "created_count": 0,
            "skipped_count": len(existing_generated),
        }

    suggestions = _generate_test_case_suggestions(
        source_context=source_context,
        test_count=test_count,
        use_case=use_case,
        include_boundary_tests=include_boundary_tests,
        include_followup_tests=include_followup_tests,
    )

    if not suggestions:
        return {
            "success": False,
            "message": "No test case suggestions could be generated from this source.",
        }

    created = []
    skipped = []

    for suggestion in suggestions:
        normalized = _normalize_test_case_suggestion(suggestion, use_case)

        if not normalized.get("question"):
            skipped.append({
                "title": normalized.get("title") or "Untitled Test Case",
                "reason": "Missing question.",
            })
            continue

        duplicate = _find_existing_source_test_case(
            source_name=source_doc.name,
            question=normalized.get("question"),
        )

        if duplicate:
            skipped.append({
                "name": duplicate,
                "title": normalized.get("title") or normalized.get("question"),
                "reason": "Similar test case already exists for this source.",
            })
            continue

        doc = frappe.new_doc("Nexus Knowledge Test Case")

        _apply_test_case_values(
            doc=doc,
            source_doc=source_doc,
            normalized=normalized,
            use_case=use_case,
            auto_enable=auto_enable,
        )

        _fill_missing_mandatory_test_case_fields(
            doc=doc,
            source_doc=source_doc,
            normalized=normalized,
        )

        try:
            doc.insert(ignore_permissions=False)
        except Exception as exc:
            skipped.append({
                "title": normalized.get("title") or normalized.get("question"),
                "question": normalized.get("question"),
                "reason": str(exc),
            })

            frappe.log_error(
                title="Suggested Test Case Insert Failed",
                message=frappe.get_traceback(),
            )
            continue

        created.append({
            "name": doc.name,
            "title": normalized.get("title") or doc.name,
            "question": normalized.get("question"),
        })

    return {
        "success": True,
        "message": f"Generated {len(created)} suggested Knowledge Test Case(s) from published source.",
        "created": created,
        "skipped": skipped,
        "created_count": len(created),
        "skipped_count": len(skipped),
    }



# -------------------------------------------------------------------------
# Public API methods - Source Publishing
# -------------------------------------------------------------------------

def _publish_generated_unit_and_chunks(source_doc):
	"""
	Publish/activate the generated Knowledge Unit and generated chunks
	for a Nexus Knowledge Source.

	Important:
	- Nexus Knowledge Source can use status = Published.
	- Nexus Knowledge Unit may use a different lifecycle, commonly:
	  Draft / Review / Approved / Active / Archived.
	- Nexus Knowledge Chunk does not use is_active / active / published / status.
	- Active chunk means:
		disabled = 0
		archived = 0
		embedding_status = Completed
	"""

	generated_unit = _normalize_context_value(source_doc.get("generated_knowledge_unit"))

	if not generated_unit:
		_set_if_exists(source_doc, "active_chunk_count", 0)
		return {
			"generated_unit": None,
			"chunk_count": int(source_doc.get("chunk_count") or 0),
			"active_chunk_count": 0,
		}

	if not frappe.db.exists("Nexus Knowledge Unit", generated_unit):
		_set_if_exists(source_doc, "active_chunk_count", 0)
		return {
			"generated_unit": generated_unit,
			"chunk_count": int(source_doc.get("chunk_count") or 0),
			"active_chunk_count": 0,
		}

	unit_doc = frappe.get_doc("Nexus Knowledge Unit", generated_unit)

	# Knowledge Unit may not support "Published".
	# For Knowledge Unit, "Active" is the safer live/retrieval state.
	if not _safe_set_select_value(unit_doc, "status", "Published"):
		if not _safe_set_select_value(unit_doc, "status", "Active"):
			_safe_set_select_value(unit_doc, "status", "Approved")

	_set_if_exists(unit_doc, "published", 1)
	_set_if_exists(unit_doc, "ready_to_publish", 0)
	_set_if_exists(unit_doc, "disabled", 0)
	_set_if_exists(unit_doc, "retrieval_ready", 1)

	unit_doc.save(ignore_permissions=False)

	chunk_count = 0
	active_chunk_count = 0

	if not frappe.db.exists("DocType", "Nexus Knowledge Chunk"):
		_set_if_exists(source_doc, "active_chunk_count", 0)
		return {
			"generated_unit": generated_unit,
			"chunk_count": 0,
			"active_chunk_count": 0,
		}

	chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")

	filters = {}

	if chunk_meta.has_field("knowledge_unit"):
		filters["knowledge_unit"] = generated_unit
	elif chunk_meta.has_field("knowledge_source"):
		filters["knowledge_source"] = source_doc.name

	if not filters:
		_set_if_exists(source_doc, "active_chunk_count", 0)
		return {
			"generated_unit": generated_unit,
			"chunk_count": 0,
			"active_chunk_count": 0,
		}

	chunk_names = frappe.get_all(
		"Nexus Knowledge Chunk",
		filters=filters,
		pluck="name",
		limit_page_length=1000,
	)

	chunk_count = len(chunk_names)

	for chunk_name in chunk_names:
		chunk_doc = frappe.get_doc("Nexus Knowledge Chunk", chunk_name)

		if chunk_meta.has_field("disabled"):
			chunk_doc.disabled = 0

		if chunk_meta.has_field("archived"):
			chunk_doc.archived = 0

		# Do not overwrite a failed embedding as Completed.
		# Only fill it when blank, because a failed embedding should stay visible.
		if chunk_meta.has_field("embedding_status") and not chunk_doc.get("embedding_status"):
			chunk_doc.embedding_status = "Completed"

		chunk_doc.save(ignore_permissions=False)

		is_disabled = int(chunk_doc.get("disabled") or 0)
		is_archived = int(chunk_doc.get("archived") or 0)
		embedding_status = str(chunk_doc.get("embedding_status") or "").strip()

		if (
			is_disabled == 0
			and is_archived == 0
			and embedding_status == "Completed"
		):
			active_chunk_count += 1

	_set_if_exists(source_doc, "chunk_count", chunk_count)
	_set_if_exists(source_doc, "active_chunk_count", active_chunk_count)

	return {
		"generated_unit": generated_unit,
		"chunk_count": chunk_count,
		"active_chunk_count": active_chunk_count,
	}

def _unpublish_generated_unit_and_chunks(source_doc):
	"""
	Unpublish/deactivate the generated Knowledge Unit and chunks.

	For chunks, the schema uses disabled/archived.
	"""

	generated_unit = _normalize_context_value(source_doc.get("generated_knowledge_unit"))

	if generated_unit and frappe.db.exists("Nexus Knowledge Unit", generated_unit):
		unit_doc = frappe.get_doc("Nexus Knowledge Unit", generated_unit)

		# Knowledge Unit may not support "Ready to Publish".
		# Fall back to Approved, then Draft.
		if not _safe_set_select_value(unit_doc, "status", "Ready to Publish"):
			if not _safe_set_select_value(unit_doc, "status", "Approved"):
				_safe_set_select_value(unit_doc, "status", "Draft")

		_set_if_exists(unit_doc, "published", 0)
		_set_if_exists(unit_doc, "retrieval_ready", 0)

		unit_doc.save(ignore_permissions=False)

	if generated_unit and frappe.db.exists("DocType", "Nexus Knowledge Chunk"):
		chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")

		filters = {}

		if chunk_meta.has_field("knowledge_unit"):
			filters["knowledge_unit"] = generated_unit
		elif chunk_meta.has_field("knowledge_source"):
			filters["knowledge_source"] = source_doc.name

		if filters:
			chunk_names = frappe.get_all(
				"Nexus Knowledge Chunk",
				filters=filters,
				pluck="name",
				limit_page_length=1000,
			)

			for chunk_name in chunk_names:
				chunk_doc = frappe.get_doc("Nexus Knowledge Chunk", chunk_name)

				if chunk_meta.has_field("disabled"):
					chunk_doc.disabled = 1

				# Keep archived unchanged during unpublish.
				# Archived is more of a lifecycle/delete-style flag than publish visibility.
				chunk_doc.save(ignore_permissions=False)

	_set_if_exists(source_doc, "active_chunk_count", 0)
 
@frappe.whitelist()
def publish_knowledge_source(name: str):
	"""
	Publish a validated Knowledge Source.

	Business meaning:
	- The source has passed validation.
	- The generated knowledge/chunks are activated for retrieval.
	- The source is now available for Nexus answers.
	"""

	if not name:
		return {
			"success": False,
			"message": "Knowledge Source name is required.",
		}

	if not frappe.db.exists("Nexus Knowledge Source", name):
		return {
			"success": False,
			"message": f"Nexus Knowledge Source not found: {name}",
		}

	doc = frappe.get_doc("Nexus Knowledge Source", name)

	if not frappe.has_permission("Nexus Knowledge Source", "write", doc=doc):
		frappe.throw("Not permitted to publish this Knowledge Source", frappe.PermissionError)

	active_context = _resolve_active_studio_context()
	_enforce_doc_active_tenant(doc, active_context)

	readiness = _build_source_readiness_payload(doc)

	if not readiness.get("can_publish"):
		return {
			"success": False,
			"message": "Knowledge Source is not ready to publish. Validate the source before publishing.",
			"readiness": readiness,
		}

	activation_result = _publish_generated_unit_and_chunks(doc)
	active_chunk_count = int(activation_result.get("active_chunk_count") or 0)

	if active_chunk_count <= 0:
		# Validation may already have passed, so keep it in Ready to Publish.
		# But do not allow Published state unless active retrieval chunks exist.
		_set_if_exists(doc, "status", "Ready to Publish")
		_set_if_exists(doc, "ready_to_publish", 1)
		_set_if_exists(doc, "retrieval_ready", 0)

		doc.save(ignore_permissions=False)

		return {
			"success": False,
			"message": (
				"Knowledge Source could not be published because no active retrieval chunks were found. "
				"Ensure chunks are generated and embeddings are completed."
			),
			"activation": activation_result,
			"readiness": _build_source_readiness_payload(doc),
		}

	_set_if_exists(doc, "status", "Published")
	_set_if_exists(doc, "ready_to_publish", 0)
	_set_if_exists(doc, "needs_review", 0)
	_set_if_exists(doc, "review_reason", None)
	_set_if_exists(doc, "retrieval_ready", 1)

	if _has_field(doc.doctype, "published"):
		doc.set("published", 1)

	if _has_field(doc.doctype, "published_on"):
		doc.set("published_on", frappe.utils.now())

	if _has_field(doc.doctype, "published_by"):
		doc.set("published_by", frappe.session.user)

	doc.save(ignore_permissions=False)

	return {
		"success": True,
		"message": "Knowledge Source published successfully.",
		"activation": activation_result,
		"readiness": _build_source_readiness_payload(doc),
	}

@frappe.whitelist()
def unpublish_knowledge_source(name: str):
	"""
	Unpublish a Knowledge Source.

	Business meaning:
	- The source is removed from active answer availability.
	- It remains validated/prepared and can be published again.
	"""

	if not name:
		return {
			"success": False,
			"message": "Knowledge Source name is required.",
		}

	if not frappe.db.exists("Nexus Knowledge Source", name):
		return {
			"success": False,
			"message": f"Nexus Knowledge Source not found: {name}",
		}

	doc = frappe.get_doc("Nexus Knowledge Source", name)

	if not frappe.has_permission("Nexus Knowledge Source", "write", doc=doc):
		frappe.throw("Not permitted to unpublish this Knowledge Source", frappe.PermissionError)

	active_context = _resolve_active_studio_context()
	_enforce_doc_active_tenant(doc, active_context)

	_unpublish_generated_unit_and_chunks(doc)

	_set_if_exists(doc, "status", "Ready to Publish")
	_set_if_exists(doc, "ready_to_publish", 1)
	_set_if_exists(doc, "retrieval_ready", 0)

	if _has_field(doc.doctype, "published"):
		doc.set("published", 0)

	doc.save(ignore_permissions=False)

	return {
		"success": True,
		"message": "Knowledge Source unpublished. It is back to Ready to Publish.",
		"readiness": _build_source_readiness_payload(doc),
	}
 
 # -------------------------------------------------------------------------
# Public API methods - Knowledge Test Case Runs
# -------------------------------------------------------------------------

def _get_test_case_field(doc, fieldname, default=None):
    if _has_field(doc.doctype, fieldname):
        return doc.get(fieldname)
    return default


def _set_test_doc_field(doc, fieldname, value):
    if _has_field(doc.doctype, fieldname):
        doc.set(fieldname, value)


def _parse_keyword_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    value = str(value or "").strip()

    if not value:
        return []

    try:
        parsed = json.loads(value)

        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        pass

    return [
        item.strip()
        for item in re.split(r"[,;\n]", value)
        if item and item.strip()
    ]


def _text_contains_all_keywords(text, keywords):
    if not keywords:
        return True

    text = str(text or "").lower()

    for keyword in keywords:
        if str(keyword or "").strip().lower() not in text:
            return False

    return True


def _text_contains_any_keyword(text, keywords):
    if not keywords:
        return False

    text = str(text or "").lower()

    for keyword in keywords:
        if str(keyword or "").strip().lower() in text:
            return True

    return False


def _build_test_case_query_contract(test_case_doc):
    """
    Build the query contract for the Nexus answer/retrieval layer from a Test Case.
    """

    question = (
        _get_test_case_field(test_case_doc, "question")
        or _get_test_case_field(test_case_doc, "query")
        or _get_test_case_field(test_case_doc, "test_query")
        or ""
    )

    use_case = _get_test_case_field(test_case_doc, "use_case") or "Q&A"

    query_contract = {
        "query": question,
        "original_query": question,
        "use_case": use_case,
        "response_mode": use_case,
        "caller_system": "Nexus Knowledge Test",
        "tenant": _get_test_case_field(test_case_doc, "tenant"),
        "ecosystem": _get_test_case_field(test_case_doc, "ecosystem"),
        "business_unit": _get_test_case_field(test_case_doc, "business_unit"),
        "project": _get_test_case_field(test_case_doc, "project"),
        "channel": _get_test_case_field(test_case_doc, "channel"),
        "context": _get_test_case_field(test_case_doc, "context"),
        "sub_context": _get_test_case_field(test_case_doc, "sub_context"),
        "entity_type": _get_test_case_field(test_case_doc, "entity_type"),
        "entity": _get_test_case_field(test_case_doc, "entity"),
        "topic": _get_test_case_field(test_case_doc, "topic"),
        "top_k": 5,
        "user": {
            "id": frappe.session.user,
            "roles": frappe.get_roles(frappe.session.user),
        },
    }

    knowledge_source = _get_test_case_field(test_case_doc, "knowledge_source")
    if knowledge_source:
        query_contract["expected_source"] = knowledge_source
        query_contract["knowledge_source"] = knowledge_source

    return query_contract


def _call_nexus_answer_service(query_contract: dict):
    """
    Calls the existing Nexus answer service for Knowledge Test Runs.

    Actual service found:
    digitz_ai_nexus.services.answer_service.answer_query
    """

    candidates = [
        "digitz_ai_nexus.services.answer_service.answer_query",
        "digitz_ai_nexus.api.answer_service.answer_query",
        "digitz_ai_nexus.services.answer_service.ask_question",
        "digitz_ai_nexus.services.answer_service.answer_question",
        "digitz_ai_nexus.api.answer_service.ask_question",
        "digitz_ai_nexus.api.answer_service.answer_question",
    ]

    errors = []

    for dotted_path in candidates:
        try:
            fn = frappe.get_attr(dotted_path)
        except Exception as exc:
            errors.append(f"{dotted_path}: import failed: {str(exc)}")
            continue

        if not fn:
            errors.append(f"{dotted_path}: function not found")
            continue

        # Most likely signature: answer_query(query_contract)
        try:
            return fn(query_contract)
        except TypeError as exc:
            errors.append(f"{dotted_path}(query_contract): {str(exc)}")
        except Exception:
            raise

        # Alternative: answer_query(**query_contract)
        try:
            return fn(**query_contract)
        except TypeError as exc:
            errors.append(f"{dotted_path}(**query_contract): {str(exc)}")
        except Exception:
            raise

        # Alternative: answer_query(query=...)
        try:
            return fn(query=query_contract.get("query"))
        except TypeError as exc:
            errors.append(f"{dotted_path}(query=...): {str(exc)}")
        except Exception:
            raise

        # Alternative: answer_query(question=...)
        try:
            return fn(question=query_contract.get("query"))
        except TypeError as exc:
            errors.append(f"{dotted_path}(question=...): {str(exc)}")
        except Exception:
            raise

    raise Exception(
        "No compatible Nexus answer service function was found. Tried:\n"
        + "\n".join(errors)
    )

def _normalize_answer_service_result(result):
    """
    Normalize different possible answer service response shapes.
    """

    result = result or {}

    if hasattr(result, "as_dict"):
        result = result.as_dict()

    if not isinstance(result, dict):
        result = {
            "answer": str(result or ""),
        }

    answer = (
        result.get("answer")
        or result.get("response")
        or result.get("message")
        or result.get("text")
        or ""
    )

    confidence = (
        result.get("confidence")
        or result.get("final_score")
        or result.get("score")
        or result.get("retrieval_score")
        or 0
    )

    try:
        confidence = float(confidence or 0)
    except Exception:
        confidence = 0

    sources = (
        result.get("sources")
        or result.get("retrieved_sources")
        or result.get("retrieved_chunks")
        or result.get("source_summary")
        or []
    )

    if isinstance(sources, dict):
        sources = [sources]

    if not isinstance(sources, list):
        sources = []

    fallback_used = bool(
        result.get("fallback_used")
        or result.get("is_fallback")
        or result.get("answer_status") == "fallback"
        or "do not have enough approved knowledge" in str(answer or "").lower()
        or "do not have enough" in str(answer or "").lower()
    )

    escalation_triggered = bool(
        result.get("escalation_triggered")
        or result.get("requires_escalation")
        or result.get("handover_required")
    )

    query_log = (
        result.get("query_log")
        or result.get("query_log_name")
        or result.get("log_name")
    )

    return {
        "raw": result,
        "answer": answer,
        "confidence": confidence,
        "sources": sources,
        "fallback_used": fallback_used,
        "escalation_triggered": escalation_triggered,
        "query_log": query_log,
    }


def _source_found_in_sources(expected_source, sources):
    if not expected_source:
        return True

    if not sources:
        return False

    expected = str(expected_source or "").strip().lower()

    try:
        source_text = json.dumps(sources, default=str).lower()
    except Exception:
        source_text = str(sources or "").lower()

    if expected and expected in source_text:
        return True

    for source in sources:
        if not isinstance(source, dict):
            continue

        for key in [
            "source",
            "source_name",
            "knowledge_source",
            "expected_source",
            "name",
            "title",
            "source_title",
        ]:
            value = str(source.get(key) or "").strip().lower()
            if value == expected:
                return True

    return False


def _evaluate_test_case_result(test_case_doc, normalized_result):
    """
    Evaluate actual Nexus answer result against the expected Test Case contract.
    """

    answer = normalized_result.get("answer") or ""
    confidence = float(normalized_result.get("confidence") or 0)
    sources = normalized_result.get("sources") or []
    source_count = len(sources)

    minimum_confidence = _get_test_case_field(test_case_doc, "minimum_confidence", 0.7)
    try:
        minimum_confidence = float(minimum_confidence or 0.7)
    except Exception:
        minimum_confidence = 0.7

    expected_fallback = bool(cint(_get_test_case_field(test_case_doc, "expected_fallback", 0)))
    expected_escalation = bool(cint(_get_test_case_field(test_case_doc, "expected_escalation", 0)))
    expected_source_required = bool(cint(_get_test_case_field(test_case_doc, "expected_source_required", 1)))

    required_keywords = _parse_keyword_list(_get_test_case_field(test_case_doc, "required_keywords"))
    forbidden_keywords = _parse_keyword_list(_get_test_case_field(test_case_doc, "forbidden_keywords"))

    required_keywords_found = _text_contains_all_keywords(answer, required_keywords)
    forbidden_keywords_found = _text_contains_any_keyword(answer, forbidden_keywords)

    expected_source = _get_test_case_field(test_case_doc, "knowledge_source")
    expected_source_found = _source_found_in_sources(expected_source, sources)

    fallback_used = bool(normalized_result.get("fallback_used"))
    escalation_triggered = bool(normalized_result.get("escalation_triggered"))

    failure_reasons = []
    warning_reasons = []

    if not str(answer or "").strip():
        failure_reasons.append("No answer was generated.")

    # Confidence is meaningful for grounded answers.
# For expected fallback tests, the main validation is whether fallback was actually used.
# Safe fallback answers may return low confidence by design.
    if confidence < minimum_confidence:
        if expected_fallback and fallback_used:
            pass
        else:
            failure_reasons.append(
                f"Confidence {confidence:.2f} is below minimum {minimum_confidence:.2f}."
            )

    if fallback_used and not expected_fallback:
        failure_reasons.append("Fallback was used but was not expected.")

    if expected_fallback and not fallback_used:
        failure_reasons.append("Fallback was expected but was not used.")

    if escalation_triggered and not expected_escalation:
        failure_reasons.append("Escalation was triggered but was not expected.")

    if expected_escalation and not escalation_triggered:
        failure_reasons.append("Escalation was expected but was not triggered.")

    if expected_source_required and source_count <= 0:
        failure_reasons.append("Expected at least one retrieved source, but none were returned.")

    if expected_source_required and expected_source and not expected_source_found:
        failure_reasons.append("Expected Knowledge Source was not found in retrieved sources.")

    if required_keywords and not required_keywords_found:
        failure_reasons.append("Required keywords were not found in the generated answer.")

    if forbidden_keywords_found:
        failure_reasons.append("Forbidden keywords were found in the generated answer.")

    if (
        not failure_reasons
        and source_count <= 0
        and expected_source_required
        and not expected_fallback
    ):
        warning_reasons.append("Answer was generated without retrieved source evidence.")

    if failure_reasons:
        run_status = "Failed"
        failure_reason = "; ".join(failure_reasons)
    elif warning_reasons:
        run_status = "Warning"
        failure_reason = "; ".join(warning_reasons)
    else:
        run_status = "Passed"
        failure_reason = ""

    return {
        "run_status": run_status,
        "failure_reason": failure_reason,
        "confidence": confidence,
        "minimum_confidence": minimum_confidence,
        "fallback_used": 1 if fallback_used else 0,
        "expected_fallback": 1 if expected_fallback else 0,
        "escalation_triggered": 1 if escalation_triggered else 0,
        "expected_escalation": 1 if expected_escalation else 0,
        "expected_source_required": 1 if expected_source_required else 0,
        "expected_source_found": 1 if expected_source_found else 0,
        "source_count": source_count,
        "required_keywords_found": 1 if required_keywords_found else 0,
        "forbidden_keywords_found": 1 if forbidden_keywords_found else 0,
    }


def _copy_test_case_scope_to_run(run_doc, test_case_doc):
    for fieldname in [
        "tenant",
        "ecosystem",
        "business_unit",
        "project",
        "channel",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
    ]:
        if _has_field(test_case_doc.doctype, fieldname):
            _set_test_doc_field(run_doc, fieldname, test_case_doc.get(fieldname))


def _create_knowledge_test_run(
    test_case_doc,
    normalized_result,
    evaluation,
    execution_mode="Single Test",
    response_time_ms=0,
):
    """
    Create Nexus Knowledge Test Run record.
    """

    run_doc = frappe.new_doc("Nexus Knowledge Test Run")

    question = (
        _get_test_case_field(test_case_doc, "question")
        or _get_test_case_field(test_case_doc, "query")
        or _get_test_case_field(test_case_doc, "test_query")
        or ""
    )

    test_title = (
        _get_test_case_field(test_case_doc, "test_title")
        or _get_test_case_field(test_case_doc, "title")
        or test_case_doc.name
    )

    knowledge_source = _get_test_case_field(test_case_doc, "knowledge_source")

    _set_test_doc_field(run_doc, "test_case", test_case_doc.name)
    _set_test_doc_field(run_doc, "test_title", test_title)
    _set_test_doc_field(run_doc, "knowledge_source", knowledge_source)
    _set_test_doc_field(run_doc, "source_title", _get_test_case_field(test_case_doc, "source_title"))
    _set_test_doc_field(run_doc, "run_status", evaluation.get("run_status") or "Error")
    _set_test_doc_field(run_doc, "execution_mode", execution_mode)
    _set_test_doc_field(run_doc, "use_case", _get_test_case_field(test_case_doc, "use_case") or "Q&A")

    _set_test_doc_field(run_doc, "question", question)
    _set_test_doc_field(run_doc, "generated_answer", normalized_result.get("answer") or "")

    for fieldname in [
        "confidence",
        "minimum_confidence",
        "fallback_used",
        "expected_fallback",
        "escalation_triggered",
        "expected_escalation",
        "expected_source_required",
        "expected_source_found",
        "source_count",
        "required_keywords_found",
        "forbidden_keywords_found",
        "failure_reason",
    ]:
        _set_test_doc_field(run_doc, fieldname, evaluation.get(fieldname))

    _copy_test_case_scope_to_run(run_doc, test_case_doc)

    _set_test_doc_field(
        run_doc,
        "retrieved_sources_json",
        json.dumps(normalized_result.get("sources") or [], default=str, indent=2),
    )

    _set_test_doc_field(
        run_doc,
        "diagnostics_json",
        json.dumps(normalized_result.get("raw") or {}, default=str, indent=2),
    )

    _set_test_doc_field(run_doc, "query_log", normalized_result.get("query_log"))
    _set_test_doc_field(run_doc, "response_time_ms", int(response_time_ms or 0))
    _set_test_doc_field(run_doc, "executed_by", frappe.session.user)
    _set_test_doc_field(run_doc, "executed_on", now_datetime())

    run_doc.insert(ignore_permissions=False)

    return run_doc


def _update_test_case_last_run_summary(test_case_doc, run_doc):
    """
    Update last run summary on Nexus Knowledge Test Case.

    Nexus Knowledge Test Run can store Error.
    Nexus Knowledge Test Case last_run_status currently supports:
    - Not Run
    - Passed
    - Failed
    - Warning

    So Error is summarized as Failed on the Test Case.
    """

    run_status = str(run_doc.get("run_status") or "Not Run").strip()

    if run_status == "Error":
        test_case_status = "Failed"
    elif run_status in ["Passed", "Failed", "Warning", "Not Run"]:
        test_case_status = run_status
    else:
        test_case_status = "Failed"

    _set_test_doc_field(test_case_doc, "last_run_status", test_case_status)
    _set_test_doc_field(test_case_doc, "last_run_on", run_doc.get("executed_on"))
    _set_test_doc_field(test_case_doc, "last_confidence", run_doc.get("confidence"))
    _set_test_doc_field(test_case_doc, "last_fallback_used", run_doc.get("fallback_used"))

    failure_reason = run_doc.get("failure_reason") or ""

    if run_status == "Error" and failure_reason:
        failure_reason = f"Error: {failure_reason}"

    _set_test_doc_field(test_case_doc, "last_failure_reason", failure_reason)

    if _has_field(test_case_doc.doctype, "last_run"):
        test_case_doc.set("last_run", run_doc.name)

    test_case_doc.save(ignore_permissions=False)
@frappe.whitelist()
def run_knowledge_test_case(test_case: str, execution_mode: str = "Single Test"):
    """
    Run one Nexus Knowledge Test Case and create a Nexus Knowledge Test Run.

    This can run Draft or Active test cases, because it is a direct/manual run.
    """

    if not test_case:
        return {
            "success": False,
            "message": "Test Case is required.",
        }

    if not frappe.db.exists("DocType", "Nexus Knowledge Test Case"):
        return {
            "success": False,
            "message": "Nexus Knowledge Test Case doctype does not exist.",
        }

    if not frappe.db.exists("DocType", "Nexus Knowledge Test Run"):
        return {
            "success": False,
            "message": "Nexus Knowledge Test Run doctype does not exist.",
        }

    if not frappe.db.exists("Nexus Knowledge Test Case", test_case):
        return {
            "success": False,
            "message": f"Nexus Knowledge Test Case not found: {test_case}",
        }

    test_case_doc = frappe.get_doc("Nexus Knowledge Test Case", test_case)

    if not frappe.has_permission("Nexus Knowledge Test Case", "read", doc=test_case_doc):
        frappe.throw("Not permitted to read this Knowledge Test Case", frappe.PermissionError)

    if not frappe.has_permission("Nexus Knowledge Test Run", "create"):
        frappe.throw("Not permitted to create Nexus Knowledge Test Run", frappe.PermissionError)

    query_contract = _build_test_case_query_contract(test_case_doc)

    started = time.time()

    try:
        raw_result = _call_nexus_answer_service(query_contract)
        response_time_ms = int((time.time() - started) * 1000)

        normalized_result = _normalize_answer_service_result(raw_result)
        evaluation = _evaluate_test_case_result(test_case_doc, normalized_result)

    except Exception as exc:
        response_time_ms = int((time.time() - started) * 1000)

        normalized_result = {
            "raw": {
                "error": str(exc),
                "traceback": frappe.get_traceback(),
            },
            "answer": "",
            "confidence": 0,
            "sources": [],
            "fallback_used": 0,
            "escalation_triggered": 0,
            "query_log": None,
        }

        evaluation = {
            "run_status": "Error",
            "failure_reason": str(exc),
            "confidence": 0,
            "minimum_confidence": _get_test_case_field(test_case_doc, "minimum_confidence", 0.7),
            "fallback_used": 0,
            "expected_fallback": cint(_get_test_case_field(test_case_doc, "expected_fallback", 0)),
            "escalation_triggered": 0,
            "expected_escalation": cint(_get_test_case_field(test_case_doc, "expected_escalation", 0)),
            "expected_source_required": cint(_get_test_case_field(test_case_doc, "expected_source_required", 1)),
            "expected_source_found": 0,
            "source_count": 0,
            "required_keywords_found": 0,
            "forbidden_keywords_found": 0,
        }

        frappe.log_error(
            title="Knowledge Test Case Run Failed",
            message=frappe.get_traceback(),
        )

    run_doc = _create_knowledge_test_run(
        test_case_doc=test_case_doc,
        normalized_result=normalized_result,
        evaluation=evaluation,
        execution_mode=execution_mode or "Single Test",
        response_time_ms=response_time_ms,
    )

    _update_test_case_last_run_summary(test_case_doc, run_doc)

    frappe.db.commit()

    return {
        "success": True,
        "message": f"Test Case executed with status: {run_doc.run_status}",
        "test_case": test_case_doc.name,
        "test_run": run_doc.name,
        "run_status": run_doc.get("run_status"),
        "confidence": run_doc.get("confidence"),
        "fallback_used": run_doc.get("fallback_used"),
        "source_count": run_doc.get("source_count"),
        "failure_reason": run_doc.get("failure_reason"),
    }

@frappe.whitelist()
def run_source_test_cases(
    source_name: str,
    include_draft: int = 1,
    only_enabled: int = 0,
    limit: int = 20,
):
    """
    Run Knowledge Test Cases linked to one Knowledge Source.

    MVP behavior:
    - include_draft = 1 allows running AI-generated draft cases during review.
    - only_enabled = 0 allows running generated tests before approval.
    - Later, production scheduled suites can use only_enabled = 1 and include_draft = 0.
    """

    if not source_name:
        return {
            "success": False,
            "message": "Knowledge Source is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Source", source_name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Source not found: {source_name}",
        }

    if not frappe.db.exists("DocType", "Nexus Knowledge Test Case"):
        return {
            "success": False,
            "message": "Nexus Knowledge Test Case doctype does not exist.",
        }

    if not frappe.db.exists("DocType", "Nexus Knowledge Test Run"):
        return {
            "success": False,
            "message": "Nexus Knowledge Test Run doctype does not exist.",
        }

    if not frappe.has_permission("Nexus Knowledge Test Case", "read"):
        frappe.throw("Not permitted to read Nexus Knowledge Test Case", frappe.PermissionError)

    if not frappe.has_permission("Nexus Knowledge Test Run", "create"):
        frappe.throw("Not permitted to create Nexus Knowledge Test Run", frappe.PermissionError)

    meta = frappe.get_meta("Nexus Knowledge Test Case")
    fields = {df.fieldname for df in meta.fields}

    source_field = None
    for candidate in ["knowledge_source", "source", "linked_knowledge_source", "expected_source"]:
        if candidate in fields:
            source_field = candidate
            break

    if not source_field:
        return {
            "success": False,
            "message": "Nexus Knowledge Test Case does not have a Knowledge Source link field.",
        }

    filters = {
        source_field: source_name,
    }

    if cint(only_enabled) and "enabled" in fields:
        filters["enabled"] = 1

    if not cint(include_draft) and "status" in fields:
        filters["status"] = "Active"

    limit = cint(limit or 20)
    if limit <= 0:
        limit = 20

    if limit > 100:
        limit = 100

    test_cases = frappe.get_all(
        "Nexus Knowledge Test Case",
        filters=filters,
        pluck="name",
        order_by="priority asc, creation asc" if "priority" in fields else "creation asc",
        limit_page_length=limit,
    )

    if not test_cases:
        return {
            "success": False,
            "message": "No Knowledge Test Cases found for this source.",
            "source_name": source_name,
            "results": [],
        }

    results = []
    passed = 0
    failed = 0
    warning = 0
    error = 0

    for test_case in test_cases:
        result = run_knowledge_test_case(
            test_case=test_case,
            execution_mode="Source Suite",
        )

        results.append(result)

        status = str(result.get("run_status") or "").strip().lower()

        if status == "passed":
            passed += 1
        elif status == "failed":
            failed += 1
        elif status == "warning":
            warning += 1
        elif status == "error":
            error += 1

    return {
        "success": True,
        "message": (
            f"Executed {len(results)} test case(s): "
            f"{passed} passed, {failed} failed, {warning} warning, {error} error."
        ),
        "source_name": source_name,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "warning": warning,
        "error": error,
        "results": results,
    }
