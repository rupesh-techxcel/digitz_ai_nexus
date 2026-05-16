import frappe

from digitz_ai_nexus.services.tenant_context import (
    get_user_context,
    resolve_tenant_context,
)


# ---------------------------------------------------------------------
# Nexus Administration Snapshot
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_administration_snapshot():
    """
    Main snapshot for Nexus Administration page.

    Final model:
        Tenant → Ecosystem → Defaults

    Returns:
    - current user's default context
    - active/selected ecosystem
    - all configured ecosystems for the active tenant
    - resolved runtime context
    - selector options
    - readiness summary
    """
    user_context = get_user_context_snapshot()

    resolved = resolve_tenant_context(require_tenant=False)
    resolved_dict = safe_dict(resolved)

    tenant = (
        resolved_dict.get("tenant")
        or (user_context or {}).get("active_tenant")
    )

    active_ecosystem = (user_context or {}).get("active_ecosystem")

    ecosystems = get_ecosystem_snapshots_for_tenant(tenant) if tenant else []
    selected_ecosystem = resolve_selected_ecosystem(
        tenant=tenant,
        active_ecosystem=active_ecosystem,
        ecosystems=ecosystems,
    )

    resolved_context = build_administration_resolved_context(
        tenant=tenant,
        user_context=user_context,
        selected_ecosystem=selected_ecosystem,
        base_resolved=resolved_dict,
    )

    return {
        "user_context": user_context,
        "resolved_context": resolved_context,
        "ecosystem": selected_ecosystem,
        "ecosystems": ecosystems,
        "selectors": get_selector_options(),
        "readiness": get_readiness_summary(
            tenant=tenant,
            ecosystem=selected_ecosystem,
        ) if tenant else get_empty_readiness(),
    }


def build_administration_resolved_context(
    tenant=None,
    user_context=None,
    selected_ecosystem=None,
    base_resolved=None,
):
    """
    Builds a UI-friendly resolved context for Nexus Administration.

    Priority:
        explicit resolver/base values
        user context
        selected ecosystem defaults
    """
    user_context = user_context or {}
    selected_ecosystem = selected_ecosystem or {}
    base_resolved = base_resolved or {}

    return {
        "tenant": (
            base_resolved.get("tenant")
            or user_context.get("active_tenant")
            or tenant
        ),
        "ecosystem": (
            user_context.get("active_ecosystem")
            or selected_ecosystem.get("name")
        ),
        "ecosystem_name": selected_ecosystem.get("ecosystem_name"),
        "ecosystem_type": selected_ecosystem.get("ecosystem_type"),
        "business_unit": (
            base_resolved.get("business_unit")
            or user_context.get("active_business_unit")
            or selected_ecosystem.get("default_business_unit")
        ),
        "project": (
            base_resolved.get("project")
            or user_context.get("active_project")
            or selected_ecosystem.get("default_project")
        ),
        "channel": (
            base_resolved.get("channel")
            or user_context.get("active_channel")
            or selected_ecosystem.get("default_chat_channel")
            or selected_ecosystem.get("default_qa_channel")
        ),
        "context": (
            base_resolved.get("context")
            or selected_ecosystem.get("default_public_context")
        ),
        "default_top_k": (
            base_resolved.get("default_top_k")
            or selected_ecosystem.get("default_top_k")
        ),
    }


# ---------------------------------------------------------------------
# User Context
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_user_context_snapshot():
    """
    Returns current user's active Nexus User Context.
    """
    context = get_user_context()

    if not context:
        return None

    return {
        "name": context.name,
        "user": context.user,
        "enabled": context.enabled,
        "is_default": context.is_default,
        "active_tenant": context.active_tenant,
        "active_ecosystem": get_doc_value(context, "active_ecosystem"),
        "active_business_unit": context.active_business_unit,
        "active_project": context.active_project,
        "active_channel": context.active_channel,
        "last_used_on": context.last_used_on,
        "notes": context.notes,
    }


@frappe.whitelist()
def set_active_user_context(
    tenant,
    ecosystem=None,
    active_ecosystem=None,
    business_unit=None,
    project=None,
    channel=None,
):
    """
    Sets the current user's default tenant/ecosystem context.

    Final model:
        User Context = My Default Tenant + My Active Ecosystem + working defaults
    """
    if not tenant:
        frappe.throw("Tenant is required.")

    selected_ecosystem = active_ecosystem or ecosystem

    if selected_ecosystem:
        validate_ecosystem_belongs_to_tenant(
            ecosystem=selected_ecosystem,
            tenant=tenant,
        )
    else:
        selected_ecosystem_doc = get_default_or_first_ecosystem_for_tenant(tenant)
        selected_ecosystem = selected_ecosystem_doc.name if selected_ecosystem_doc else None

    doc = get_or_create_user_context_doc()

    doc.user = frappe.session.user
    doc.enabled = 1
    doc.is_default = 1
    doc.active_tenant = tenant

    if has_field("Nexus User Context", "active_ecosystem"):
        doc.active_ecosystem = selected_ecosystem

    doc.active_business_unit = business_unit
    doc.active_project = project
    doc.active_channel = channel
    doc.last_used_on = frappe.utils.now_datetime()

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "success",
        "context": doc.name,
        "tenant": doc.active_tenant,
        "ecosystem": get_doc_value(doc, "active_ecosystem"),
        "business_unit": doc.active_business_unit,
        "project": doc.active_project,
        "channel": doc.active_channel,
    }


def get_or_create_user_context_doc():
    """
    Gets current user's default Nexus User Context or creates one.
    """
    existing = frappe.db.get_value(
        "Nexus User Context",
        {
            "user": frappe.session.user,
            "is_default": 1,
        },
        "name",
    )

    if not existing:
        existing = frappe.db.get_value(
            "Nexus User Context",
            {
                "user": frappe.session.user,
            },
            "name",
        )

    if existing:
        return frappe.get_doc("Nexus User Context", existing)

    doc = frappe.new_doc("Nexus User Context")
    doc.user = frappe.session.user
    doc.enabled = 1
    doc.is_default = 1
    return doc


# ---------------------------------------------------------------------
# Selectors
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_selector_options():
    """
    Returns options needed by the administration page selectors.

    Business Unit is not a Link DocType in the current implementation.
    It is collected from existing values across Nexus records.
    """
    tenants = []
    projects = []
    channels = []
    ecosystems = []

    if frappe.db.exists("DocType", "Nexus Tenant"):
        tenants = frappe.get_all(
            "Nexus Tenant",
            fields=get_existing_fields(
                "Nexus Tenant",
                ["name", "tenant_name", "tenant_code", "enabled"],
            ),
            order_by="modified desc",
            limit_page_length=500,
        )

    if frappe.db.exists("DocType", "Nexus Ecosystem"):
        ecosystems = frappe.get_all(
            "Nexus Ecosystem",
            fields=get_existing_fields(
                "Nexus Ecosystem",
                [
                    "name",
                    "tenant",
                    "ecosystem_name",
                    "ecosystem_type",
                    "enabled",
                    "is_default",
                ],
            ),
            order_by="modified desc",
            limit_page_length=500,
        )

    business_units = get_business_unit_options()

    if frappe.db.exists("DocType", "Nexus Project"):
        projects = frappe.get_all(
            "Nexus Project",
            fields=get_existing_fields(
                "Nexus Project",
                ["name", "project_name", "project", "tenant", "business_unit", "enabled"],
            ),
            order_by="modified desc",
            limit_page_length=500,
        )

    if frappe.db.exists("DocType", "Nexus Live Channel"):
        channels = frappe.get_all(
            "Nexus Live Channel",
            fields=get_existing_fields(
                "Nexus Live Channel",
                [
                    "name",
                    "channel_name",
                    "channel_code",
                    "channel_type",
                    "public_access",
                    "enabled",
                ],
            ),
            order_by="modified desc",
            limit_page_length=500,
        )

    return {
        "tenants": tenants,
        "ecosystems": ecosystems,
        "business_units": business_units,
        "projects": projects,
        "channels": channels,
    }


def get_business_unit_options():
    """
    Business Unit is currently not a separate DocType.
    Collect distinct values from existing Nexus data.
    """
    values = set()

    source_doctypes = [
        "Nexus Knowledge Unit",
        "Nexus Knowledge Chunk",
        "Nexus Ecosystem",
        "Nexus User Context",
        "Nexus Test Case",
    ]

    candidate_fields = [
        "business_unit",
        "default_business_unit",
        "active_business_unit",
    ]

    for doctype in source_doctypes:
        if not frappe.db.exists("DocType", doctype):
            continue

        for fieldname in candidate_fields:
            if not has_field(doctype, fieldname):
                continue

            rows = frappe.get_all(
                doctype,
                fields=[fieldname],
                limit_page_length=500,
            )

            for row in rows:
                value = row.get(fieldname)

                if value:
                    values.add(value)

    return [
        {
            "name": value,
            "business_unit_name": value,
        }
        for value in sorted(values)
    ]


# ---------------------------------------------------------------------
# Ecosystem Read / Save
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_ecosystem_snapshot(tenant=None, ecosystem=None):
    """
    Returns selected ecosystem configuration.

    If ecosystem is provided, returns that ecosystem.
    Otherwise returns default/first ecosystem for tenant.
    """
    doc = None

    if ecosystem:
        doc = frappe.get_doc("Nexus Ecosystem", ecosystem)
    else:
        if not tenant:
            user_context = get_user_context_snapshot()
            tenant = (user_context or {}).get("active_tenant")

        if not tenant:
            resolved = resolve_tenant_context(require_tenant=False)
            tenant = safe_dict(resolved).get("tenant")

        if not tenant:
            return None

        doc = get_default_or_first_ecosystem_for_tenant(tenant)

    if not doc:
        return None

    return ecosystem_doc_to_dict(doc)


def get_ecosystem_snapshots_for_tenant(tenant):
    """
    Returns all ecosystem profiles for a tenant.
    """
    if not tenant or not frappe.db.exists("DocType", "Nexus Ecosystem"):
        return []

    fields = get_existing_fields(
        "Nexus Ecosystem",
        get_ecosystem_field_list(),
    )

    rows = frappe.get_all(
        "Nexus Ecosystem",
        filters={"tenant": tenant},
        fields=fields,
        order_by="is_default desc, modified desc",
        limit_page_length=500,
    )

    return [normalize_ecosystem_row(row) for row in rows]


def get_default_or_first_ecosystem_for_tenant(tenant):
    """
    Returns tenant default ecosystem first, else first enabled ecosystem, else first ecosystem.
    """
    if not tenant:
        return None

    existing = frappe.db.get_value(
        "Nexus Ecosystem",
        {
            "tenant": tenant,
            "is_default": 1,
            "enabled": 1,
        },
        "name",
    )

    if not existing:
        existing = frappe.db.get_value(
            "Nexus Ecosystem",
            {
                "tenant": tenant,
                "enabled": 1,
            },
            "name",
            order_by="modified desc",
        )

    if not existing:
        existing = frappe.db.get_value(
            "Nexus Ecosystem",
            {
                "tenant": tenant,
            },
            "name",
            order_by="modified desc",
        )

    return frappe.get_doc("Nexus Ecosystem", existing) if existing else None


def resolve_selected_ecosystem(tenant=None, active_ecosystem=None, ecosystems=None):
    """
    Resolves selected ecosystem for UI snapshot.
    """
    ecosystems = ecosystems or []

    if active_ecosystem:
        for row in ecosystems:
            if row.get("name") == active_ecosystem:
                return row

    for row in ecosystems:
        if row.get("is_default"):
            return row

    if ecosystems:
        return ecosystems[0]

    doc = get_default_or_first_ecosystem_for_tenant(tenant)
    return ecosystem_doc_to_dict(doc) if doc else None


@frappe.whitelist()
def save_ecosystem_configuration(values):
    """
    Creates or updates Nexus Ecosystem.

    Final model:
        Save selected ecosystem by:
            1. values.name / values.ecosystem
            2. tenant + ecosystem_name
            3. create new ecosystem
    """
    values = frappe.parse_json(values) if isinstance(values, str) else values
    values = values or {}

    tenant = values.get("tenant")
    if not tenant:
        frappe.throw("Tenant is required.")

    doc = get_or_create_ecosystem_from_values(values)

    allowed_fields = {
        "tenant",
        "ecosystem_name",
        "ecosystem_type",
        "enabled",
        "is_default",
        "activation_status",
        "default_business_unit",
        "default_project",
        "default_public_context",
        "require_approved_knowledge",
        "strict_tenant_mode",
        "default_top_k",
        "qa_enabled",
        "default_qa_channel",
        "qa_fallback_message",
        "source_citation_required",
        "live_chat_enabled",
        "default_chat_channel",
        "default_live_channel",
        "default_public_agent",
        "default_public_escalation_queue",
        "default_escalation_enabled",
        "website_widget_enabled",
        "widget_title",
        "widget_welcome_message",
        "widget_brand_color",
        "testing_required_before_activation",
        "last_certified_on",
        "certification_status",
        "notes",
    }

    for fieldname in allowed_fields:
        if fieldname in values and has_field("Nexus Ecosystem", fieldname):
            doc.set(fieldname, values.get(fieldname))

    if not doc.ecosystem_name:
        doc.ecosystem_name = make_default_ecosystem_name(
            tenant=tenant,
            ecosystem_type=values.get("ecosystem_type"),
        )

    if not doc.ecosystem_type:
        doc.ecosystem_type = "Sandbox"

    if doc.enabled is None:
        doc.enabled = 1

    if not doc.activation_status:
        doc.activation_status = "Configured"

    apply_ecosystem_defaults_if_missing(doc)

    if doc.get("is_default"):
        unset_other_default_ecosystems(
            tenant=doc.tenant,
            current_name=doc.name if not doc.is_new() else None,
        )

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    if doc.get("is_default"):
        unset_other_default_ecosystems(
            tenant=doc.tenant,
            current_name=doc.name,
        )

    frappe.db.commit()

    return {
        "status": "success",
        "ecosystem": doc.name,
        "ecosystem_name": doc.ecosystem_name,
        "tenant": doc.tenant,
    }


def get_or_create_ecosystem_from_values(values):
    """
    Finds an ecosystem by docname first, then by tenant + ecosystem_name.
    Creates a new document if none is found.
    """
    docname = values.get("name") or values.get("ecosystem")

    if docname and frappe.db.exists("Nexus Ecosystem", docname):
        return frappe.get_doc("Nexus Ecosystem", docname)

    tenant = values.get("tenant")
    ecosystem_name = values.get("ecosystem_name")

    if tenant and ecosystem_name:
        existing = frappe.db.get_value(
            "Nexus Ecosystem",
            {
                "tenant": tenant,
                "ecosystem_name": ecosystem_name,
            },
            "name",
        )

        if existing:
            return frappe.get_doc("Nexus Ecosystem", existing)

    doc = frappe.new_doc("Nexus Ecosystem")
    doc.tenant = tenant
    return doc


def unset_other_default_ecosystems(tenant, current_name=None):
    """
    Ensures only one Tenant Default Ecosystem per tenant.
    """
    if not tenant or not has_field("Nexus Ecosystem", "is_default"):
        return

    rows = frappe.get_all(
        "Nexus Ecosystem",
        filters={
            "tenant": tenant,
            "is_default": 1,
        },
        fields=["name"],
        limit_page_length=500,
    )

    for row in rows:
        if current_name and row.name == current_name:
            continue

        frappe.db.set_value(
            "Nexus Ecosystem",
            row.name,
            "is_default",
            0,
            update_modified=False,
        )


def apply_ecosystem_defaults_if_missing(doc):
    """
    Applies safe defaults to a newly created or partially configured ecosystem.
    """
    default_values = {
        "enabled": 1,
        "activation_status": "Configured",
        "require_approved_knowledge": 1,
        "strict_tenant_mode": 1,
        "default_top_k": 5,
        "qa_enabled": 1,
        "source_citation_required": 1,
        "live_chat_enabled": 1,
        "default_escalation_enabled": 1,
        "website_widget_enabled": 0,
        "testing_required_before_activation": 1,
        "certification_status": "Not Certified",
        "widget_brand_color": "#214dbb",
        "qa_fallback_message": "I do not have enough approved knowledge to answer this.",
    }

    for fieldname, value in default_values.items():
        if has_field("Nexus Ecosystem", fieldname) and not doc.get(fieldname):
            doc.set(fieldname, value)


def ensure_ecosystem_for_tenant(
    tenant,
    business_unit=None,
    project=None,
    ecosystem_name=None,
    ecosystem_type=None,
    is_default=1,
):
    """
    Ensures an ecosystem exists for a tenant.

    This no longer enforces one ecosystem per tenant.
    It creates or updates a specific ecosystem profile.
    """
    if not tenant:
        frappe.throw("Tenant is required.")

    ecosystem_name = ecosystem_name or make_default_ecosystem_name(
        tenant=tenant,
        ecosystem_type=ecosystem_type,
    )

    values = {
        "tenant": tenant,
        "ecosystem_name": ecosystem_name,
        "ecosystem_type": ecosystem_type or "Sandbox",
        "enabled": 1,
        "is_default": is_default,
        "activation_status": "Configured",
        "default_business_unit": business_unit,
        "default_project": project,
    }

    doc = get_or_create_ecosystem_from_values(values)

    for fieldname, value in values.items():
        if value is not None and has_field("Nexus Ecosystem", fieldname):
            doc.set(fieldname, value)

    apply_ecosystem_defaults_if_missing(doc)

    if doc.get("is_default"):
        unset_other_default_ecosystems(
            tenant=tenant,
            current_name=doc.name if not doc.is_new() else None,
        )

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    if doc.get("is_default"):
        unset_other_default_ecosystems(
            tenant=tenant,
            current_name=doc.name,
        )

    return doc


# ---------------------------------------------------------------------
# Tenant Onboarding
# ---------------------------------------------------------------------

@frappe.whitelist()
def create_tenant_onboarding(
    tenant_name,
    tenant_code=None,
    business_unit_name=None,
    ecosystem_name=None,
    ecosystem_type=None,
):
    """
    Quick tenant onboarding entry point.

    Creates:
    - Nexus Tenant
    - Initial Nexus Ecosystem
    - Nexus User Context

    Final model:
        Tenant → Ecosystem → Defaults
    """
    if not tenant_name:
        frappe.throw("Tenant Name is required.")

    tenant = get_or_create_tenant(
        tenant_name=tenant_name,
        tenant_code=tenant_code,
    )

    ecosystem = ensure_ecosystem_for_tenant(
        tenant=tenant.name,
        business_unit=business_unit_name,
        ecosystem_name=ecosystem_name,
        ecosystem_type=ecosystem_type or "Sandbox",
        is_default=1,
    )

    user_context = set_active_user_context(
        tenant=tenant.name,
        ecosystem=ecosystem.name,
        business_unit=business_unit_name,
    )

    return {
        "status": "success",
        "tenant": tenant.name,
        "business_unit": business_unit_name,
        "ecosystem": ecosystem.name,
        "ecosystem_name": ecosystem.ecosystem_name,
        "user_context": user_context.get("context"),
    }


def get_or_create_tenant(tenant_name, tenant_code=None):
    """
    Creates a Nexus Tenant if not already existing.
    Uses tenant_name / tenant_code as stable lookup.
    """
    existing = None

    if has_field("Nexus Tenant", "tenant_name"):
        existing = frappe.db.get_value(
            "Nexus Tenant",
            {"tenant_name": tenant_name},
            "name",
        )

    if not existing and tenant_code and has_field("Nexus Tenant", "tenant_code"):
        existing = frappe.db.get_value(
            "Nexus Tenant",
            {"tenant_code": tenant_code},
            "name",
        )

    if existing:
        return frappe.get_doc("Nexus Tenant", existing)

    doc = frappe.new_doc("Nexus Tenant")

    if has_field("Nexus Tenant", "tenant_name"):
        doc.tenant_name = tenant_name

    if tenant_code and has_field("Nexus Tenant", "tenant_code"):
        doc.tenant_code = tenant_code

    if has_field("Nexus Tenant", "enabled"):
        doc.enabled = 1

    doc.insert(ignore_permissions=True)
    return doc


# ---------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_readiness_summary(tenant=None, ecosystem=None):
    if not tenant:
        user_context = get_user_context_snapshot()
        tenant = (user_context or {}).get("active_tenant")

    if not tenant:
        resolved = resolve_tenant_context(require_tenant=False)
        tenant = safe_dict(resolved).get("tenant")

    if not tenant:
        return get_empty_readiness()

    if not ecosystem:
        ecosystem = get_ecosystem_snapshot(tenant=tenant)

    knowledge_count = count_records_safely(
        doctype="Nexus Knowledge Unit",
        tenant=tenant,
    )

    chunk_count = count_records_safely(
        doctype="Nexus Knowledge Chunk",
        tenant=tenant,
    )

    channel_count = count_records_safely(
        doctype="Nexus Live Channel",
        extra_filters={
            "enabled": 1,
        },
    )

    ai_agent_count = count_records_safely(
        doctype="Nexus Live Agent",
        extra_filters={
            "enabled": 1,
            "agent_type": "AI",
        },
    )

    qa_ready = bool(
        ecosystem
        and ecosystem.get("qa_enabled")
        and ecosystem.get("default_qa_channel")
        and knowledge_count > 0
        and chunk_count > 0
    )

    live_ready = bool(
        ecosystem
        and ecosystem.get("live_chat_enabled")
        and ecosystem.get("default_chat_channel")
        and ecosystem.get("default_public_agent")
        and ai_agent_count > 0
    )

    testing_ready = bool(
        ecosystem
        and ecosystem.get("certification_status") == "Passed"
    )

    production_ready = bool(
        ecosystem
        and ecosystem.get("activation_status") == "Active"
        and (
            not ecosystem.get("testing_required_before_activation")
            or testing_ready
        )
    )

    return {
        "tenant": tenant,
        "ecosystem": ecosystem.get("name") if ecosystem else None,
        "ecosystem_name": ecosystem.get("ecosystem_name") if ecosystem else None,
        "knowledge_count": knowledge_count,
        "chunk_count": chunk_count,
        "channel_count": channel_count,
        "ai_agent_count": ai_agent_count,
        "qa_ready": qa_ready,
        "live_ready": live_ready,
        "testing_ready": testing_ready,
        "production_ready": production_ready,
        "activation_status": ecosystem.get("activation_status") if ecosystem else None,
        "certification_status": ecosystem.get("certification_status") if ecosystem else None,
    }


def get_empty_readiness():
    return {
        "tenant": None,
        "ecosystem": None,
        "ecosystem_name": None,
        "knowledge_count": 0,
        "chunk_count": 0,
        "channel_count": 0,
        "ai_agent_count": 0,
        "qa_ready": False,
        "live_ready": False,
        "testing_ready": False,
        "production_ready": False,
        "activation_status": None,
        "certification_status": None,
    }


def count_records_safely(doctype, tenant=None, extra_filters=None):
    """
    Counts records without assuming optional fields exist.
    """
    if not frappe.db.exists("DocType", doctype):
        return 0

    filters = {}

    if tenant and has_field(doctype, "tenant"):
        filters["tenant"] = tenant

    if has_field(doctype, "disabled"):
        filters["disabled"] = 0

    extra_filters = extra_filters or {}

    for fieldname, value in extra_filters.items():
        if has_field(doctype, fieldname):
            filters[fieldname] = value

    return frappe.db.count(
        doctype,
        filters,
    )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def validate_ecosystem_belongs_to_tenant(ecosystem, tenant):
    if not ecosystem:
        return

    if not frappe.db.exists("Nexus Ecosystem", ecosystem):
        frappe.throw(f"Ecosystem {ecosystem} does not exist.")

    ecosystem_tenant = frappe.db.get_value(
        "Nexus Ecosystem",
        ecosystem,
        "tenant",
    )

    if ecosystem_tenant != tenant:
        frappe.throw("Selected ecosystem does not belong to the selected tenant.")


def ecosystem_doc_to_dict(doc):
    if not doc:
        return None

    return normalize_ecosystem_row(
        {
            fieldname: get_doc_value(doc, fieldname)
            for fieldname in get_ecosystem_field_list()
            if fieldname == "name" or has_field("Nexus Ecosystem", fieldname)
        }
    )


def normalize_ecosystem_row(row):
    row = frappe._dict(row or {})

    if not row.get("ecosystem_name"):
        row["ecosystem_name"] = row.get("name")

    if row.get("enabled") is None:
        row["enabled"] = 0

    if row.get("is_default") is None:
        row["is_default"] = 0

    if not row.get("ecosystem_type"):
        row["ecosystem_type"] = "Sandbox"

    return dict(row)


def get_ecosystem_field_list():
    return [
        "name",
        "tenant",
        "ecosystem_name",
        "ecosystem_type",
        "enabled",
        "is_default",
        "activation_status",
        "default_business_unit",
        "default_project",
        "default_public_context",
        "require_approved_knowledge",
        "strict_tenant_mode",
        "default_top_k",
        "qa_enabled",
        "default_qa_channel",
        "qa_fallback_message",
        "source_citation_required",
        "live_chat_enabled",
        "default_chat_channel",
        "default_live_channel",
        "default_public_agent",
        "default_public_escalation_queue",
        "default_escalation_enabled",
        "website_widget_enabled",
        "widget_title",
        "widget_welcome_message",
        "widget_brand_color",
        "testing_required_before_activation",
        "last_certified_on",
        "certification_status",
        "notes",
    ]


def make_default_ecosystem_name(tenant, ecosystem_type=None):
    ecosystem_type = ecosystem_type or "Sandbox"

    tenant_label = frappe.db.get_value(
        "Nexus Tenant",
        tenant,
        "tenant_name",
    ) if has_field("Nexus Tenant", "tenant_name") else tenant

    tenant_label = tenant_label or tenant

    return f"{tenant_label} {ecosystem_type} Ecosystem"


def get_doc_value(doc, fieldname):
    if not doc:
        return None

    if fieldname == "name":
        return doc.name

    try:
        return doc.get(fieldname)
    except Exception:
        return getattr(doc, fieldname, None)


def safe_dict(value):
    if not value:
        return {}

    try:
        return dict(value)
    except Exception:
        result = {}

        for key in [
            "tenant",
            "business_unit",
            "project",
            "channel",
            "context",
            "default_top_k",
        ]:
            if hasattr(value, key):
                result[key] = getattr(value, key)

        return result


def get_existing_fields(doctype, fields):
    """
    Returns only fields that exist on the doctype.
    Always allows name.
    """
    if not frappe.db.exists("DocType", doctype):
        return ["name"]

    meta_fields = {
        field.fieldname
        for field in frappe.get_meta(doctype).fields
    }

    valid_fields = []

    for fieldname in fields:
        if fieldname == "name" or fieldname in meta_fields:
            valid_fields.append(fieldname)

    return valid_fields or ["name"]


def has_field(doctype, fieldname):
    if not frappe.db.exists("DocType", doctype):
        return False

    return fieldname in {
        field.fieldname
        for field in frappe.get_meta(doctype).fields
    }