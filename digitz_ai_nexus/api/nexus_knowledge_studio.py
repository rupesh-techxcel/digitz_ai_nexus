import frappe


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
            "sync_status": sync_status,
            "processing_status": processing_status,
            "quality_status": quality_status,
            "validation_status": validation_status,
            "last_error": row.get("last_error"),
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
    sync_failed = 0
    stale = 0
    disabled = 0

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
            "sync_failed": sync_failed,
            "stale": stale,
            "disabled": disabled,
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

        sources.append({
            "name": row.get("name"),
            "source_title": row.get("source_title") or row.get("name"),
            "source_type": row.get("source_type"),
            "tenant": row.get("tenant"),
            "ecosystem": row.get("ecosystem"),
            "business_unit": row.get("business_unit"),
            "project": row.get("project"),
            "channel": row.get("channel"),
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
            **readiness,
        })

    return {
        "success": True,
        "active_tenant": active_context.get("tenant"),
        "active_context": active_context,
        "applied_filters": db_filters,
        "sources": sources,
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
# Public API methods - Source Publishing
# -------------------------------------------------------------------------

def _publish_generated_unit_and_chunks(source_doc):
	"""
	Publish/activate the generated Knowledge Unit and generated chunks
	for a Nexus Knowledge Source.

	Important:
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

	_set_if_exists(unit_doc, "status", "Published")
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

		_set_if_exists(unit_doc, "status", "Ready to Publish")
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