import frappe

from digitz_ai_nexus.services.tenant_context import (
    get_user_context,
    resolve_tenant_context,
)


# ---------------------------------------------------------------------
# Nexus Administration Snapshot
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_administration_snapshot(tenant=None):
    """
    Main snapshot for Nexus Administration page.

    Final model:
        Tenant → Tenant Configuration

    Returns:
    - selected tenant
    - tenant configuration
    - selector options
    - readiness summary
    """
    from digitz_ai_nexus.services.tenant_context import get_user_context

    selectors = get_selector_options()

    user_ctx = get_user_context()
    user_context_data = None
    if user_ctx:
        user_context_data = {
            "active_tenant": user_ctx.active_tenant,
            "active_tenant_configuration": get_tenant_configuration_name(user_ctx.active_tenant),
            "active_business_unit": user_ctx.active_business_unit,
            "active_project": user_ctx.active_project,
            "active_channel": user_ctx.active_channel,
        }

    if not tenant:
        saved_tenant = user_ctx.active_tenant if user_ctx else None
        tenant = saved_tenant or get_first_tenant_name(selectors.get("tenants"))

    tenant_doc = get_tenant_summary(tenant)

    tenant_configurations = get_tenant_configurations_for_tenant(tenant) if tenant else []
    tenant_configuration = resolve_selected_tenant_configuration(
        tenant=tenant,
        ecosystems=tenant_configurations,
    )

    return {
        "tenant": tenant_doc,
        "tenant_configuration": tenant_configuration,
        "tenant_configurations": tenant_configurations,
        "user_context": user_context_data,
        "resolved_context": {
            "tenant": tenant,
            "tenant_configuration": tenant_configuration.get("name") if tenant_configuration else None,
        },
        "selectors": selectors,
        "readiness": get_readiness_summary(
            tenant=tenant,
            ecosystem=tenant_configuration,
        ) if tenant else get_empty_readiness(),
    }


def get_first_tenant_name(tenants):
    tenants = tenants or []
    return tenants[0].get("name") if tenants else None


def get_tenant_summary(tenant):
    if not tenant or not frappe.db.exists("Nexus Tenant", tenant):
        return None

    fields = get_existing_fields(
        "Nexus Tenant",
        ["name", "tenant_name", "tenant_code", "disabled", "description"],
    )
    values = frappe.db.get_value("Nexus Tenant", tenant, fields, as_dict=True)
    return dict(values) if values else None


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
        selected tenant configuration defaults
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
            selected_ecosystem.get("name")
        ),
        "configuration_name": selected_ecosystem.get("configuration_name"),
        "configuration_type": selected_ecosystem.get("configuration_type"),
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
        ),
        "context": base_resolved.get("context"),
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
        "active_tenant_configuration": get_tenant_configuration_name(context.active_tenant),
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
    active_tenant_configuration=None,
    business_unit=None,
    project=None,
    channel=None,
):
    """
    Sets the current user's default tenant working context.

    Final model:
        User Context = My Default Tenant + working defaults
    """
    if not tenant:
        frappe.throw("Tenant is required.")

    selected_ecosystem_doc = get_default_tenant_configuration(tenant)
    selected_ecosystem = selected_ecosystem_doc.name if selected_ecosystem_doc else None

    doc = get_or_create_user_context_doc()

    doc.user = frappe.session.user
    doc.enabled = 1
    doc.is_default = 1
    doc.active_tenant = tenant

    ensure_master_value("Nexus Business Unit", business_unit, tenant=tenant)

    if has_field("Nexus User Context", "active_tenant_configuration"):
        doc.active_tenant_configuration = selected_ecosystem

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
        "ecosystem": get_doc_value(doc, "active_tenant_configuration"),
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
    """
    tenants = []
    projects = []
    channels = []
    ecosystems = []
    tenant_configurations = []

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

    if frappe.db.exists("DocType", "Nexus Tenant Configuration"):
        ecosystems = frappe.get_all(
            "Nexus Tenant Configuration",
            filters={"enabled": 1},
            fields=get_existing_fields(
                "Nexus Tenant Configuration",
                [
                    "name",
                    "tenant",
                    "configuration_name",
                    "configuration_type",
                    "enabled",
                    "is_default",
                ],
            ),
            order_by="modified desc",
            limit_page_length=500,
        )
        tenant_configurations = ecosystems

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
        "tenant_configurations": tenant_configurations,
        "business_units": business_units,
        "projects": projects,
        "channels": channels,
    }


def get_business_unit_options():
    """
    Returns Business Unit master options. Falls back to legacy text values when
    the master DocType has not been synced yet.
    """
    if frappe.db.exists("DocType", "Nexus Business Unit"):
        return frappe.get_all(
            "Nexus Business Unit",
            fields=get_existing_fields(
                "Nexus Business Unit",
                ["name", "business_unit_name", "tenant", "enabled"],
            ),
            filters={"enabled": 1} if has_field("Nexus Business Unit", "enabled") else {},
            order_by="business_unit_name asc",
            limit_page_length=500,
        )

    return get_legacy_business_unit_options()


def get_legacy_business_unit_options():
    values = set()

    source_doctypes = [
        "Nexus Knowledge Unit",
        "Nexus Knowledge Chunk",
        "Nexus Tenant Configuration",
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


def ensure_master_value(doctype, value, tenant=None):
    """
    Ensures legacy string values become valid Link targets during transition.
    """
    value = (value or "").strip() if isinstance(value, str) else value

    if not value or not frappe.db.exists("DocType", doctype):
        return

    if frappe.db.exists(doctype, value):
        return

    doc = frappe.new_doc(doctype)

    if doctype == "Nexus Business Unit":
        doc.business_unit_name = value
    else:
        return

    if tenant and has_field(doctype, "tenant"):
        doc.tenant = tenant

    if has_field(doctype, "enabled"):
        doc.enabled = 1

    doc.insert(ignore_permissions=True)


# ---------------------------------------------------------------------
# Ecosystem Read / Save
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_tenant_configuration_snapshot(tenant=None, ecosystem=None):
    """
    Returns selected tenant configuration.

    If tenant_config is provided, returns that configuration.
    Otherwise returns default/first configuration for tenant.
    """
    doc = None

    if ecosystem:
        doc = frappe.get_doc("Nexus Tenant Configuration", ecosystem)
    else:
        if not tenant:
            user_context = get_user_context_snapshot()
            tenant = (user_context or {}).get("active_tenant")

        if not tenant:
            resolved = resolve_tenant_context(require_tenant=False)
            tenant = safe_dict(resolved).get("tenant")

        if not tenant:
            return None

        doc = get_default_tenant_configuration(tenant)

    if not doc:
        return None

    return tenant_config_to_dict(doc)


def get_tenant_configurations_for_tenant(tenant):
    """
    Returns enabled configurations for a tenant.
    """
    if not tenant or not frappe.db.exists("DocType", "Nexus Tenant Configuration"):
        return []

    fields = get_existing_fields(
        "Nexus Tenant Configuration",
        get_configuration_field_list(),
    )

    rows = frappe.get_all(
        "Nexus Tenant Configuration",
        filters={
            "tenant": tenant,
            "enabled": 1,
        },
        fields=fields,
        order_by="is_default desc, modified desc",
        limit_page_length=500,
    )

    return [normalize_configuration_row(row) for row in rows]


def get_default_tenant_configuration(tenant):
    """
    Returns the single enabled configuration for a tenant.
    """
    if not tenant or not frappe.db.exists("DocType", "Nexus Tenant Configuration"):
        return None

    rows = frappe.get_all(
        "Nexus Tenant Configuration",
        filters={
            "tenant": tenant,
            "enabled": 1,
        },
        fields=["name"],
        order_by="is_default desc, modified desc",
        limit_page_length=2,
    )

    if len(rows) > 1:
        frappe.throw(
            (
                "Multiple enabled Tenant Configurations exist for this tenant. "
                "Keep one enabled configuration and disable the rest."
            )
        )

    return frappe.get_doc("Nexus Tenant Configuration", rows[0].name) if rows else None


def resolve_selected_tenant_configuration(tenant=None, ecosystems=None):
    """
    Resolves the tenant runtime profile for the UI snapshot.
    """
    ecosystems = ecosystems or []
    enabled_configurations = [
        row for row in ecosystems
        if int(row.get("enabled") if row.get("enabled") is not None else 1)
    ]

    for row in enabled_configurations:
        if row.get("is_default"):
            return row

    if enabled_configurations:
        return enabled_configurations[0]

    doc = get_default_tenant_configuration(tenant)
    return tenant_config_to_dict(doc) if doc else None


@frappe.whitelist()
def save_ecosystem_configuration(values):
    """
    Creates or updates Nexus Tenant Configuration.

    Final model:
        Save selected tenant configuration by:
            1. values.name / values.ecosystem
            2. tenant + configuration_name
            3. create new ecosystem
    """
    values = frappe.parse_json(values) if isinstance(values, str) else values
    values = values or {}

    tenant = values.get("tenant")
    if not tenant:
        frappe.throw("Tenant is required.")

    doc = get_or_create_tenant_configuration(values)

    ensure_master_value("Nexus Business Unit", values.get("default_business_unit"), tenant=tenant)

    allowed_fields = {
        "tenant",
        "configuration_name",
        "configuration_type",
        "enabled",
        "is_default",
        "activation_status",
        "default_business_unit",
        "default_project",
        "require_approved_knowledge",
        "strict_tenant_mode",
        "default_top_k",
        "qa_enabled",
        "default_qa_channel",
        "qa_fallback_message",
        "source_citation_required",
        "live_chat_enabled",
        "default_chat_channel",
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
        if fieldname in values and has_field("Nexus Tenant Configuration", fieldname):
            doc.set(fieldname, values.get(fieldname))

    if not doc.configuration_name:
        doc.configuration_name = make_default_configuration_name(
            tenant=tenant,
            configuration_type=values.get("configuration_type"),
        )

    if not doc.configuration_type:
        doc.configuration_type = "Sandbox"

    if doc.enabled is None:
        doc.enabled = 1

    if not doc.activation_status:
        doc.activation_status = "Configured"

    apply_configuration_defaults(doc)

    if doc.get("is_default"):
        unset_other_default_configurations(
            tenant=doc.tenant,
            current_name=doc.name if not doc.is_new() else None,
        )

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    if doc.get("is_default"):
        unset_other_default_configurations(
            tenant=doc.tenant,
            current_name=doc.name,
        )

    frappe.db.commit()

    return {
        "status": "success",
        "ecosystem": doc.name,
        "configuration_name": doc.configuration_name,
        "tenant": doc.tenant,
    }


@frappe.whitelist()
def save_tenant_configuration(values):
    """
    Public admin API for tenant configuration.

    The current storage DocType remains Nexus Tenant Configuration for compatibility,
    but callers should treat this as the tenant's configuration record.
    """
    return save_ecosystem_configuration(values)


def get_or_create_tenant_configuration(values):
    """
    Finds a tenant configuration by docname first, then by tenant + configuration_name.
    Creates a new document if none is found.
    """
    docname = values.get("name") or values.get("ecosystem")

    if docname and frappe.db.exists("Nexus Tenant Configuration", docname):
        return frappe.get_doc("Nexus Tenant Configuration", docname)

    tenant = values.get("tenant")
    configuration_name = values.get("configuration_name")

    if tenant and configuration_name:
        existing = frappe.db.get_value(
            "Nexus Tenant Configuration",
            {
                "tenant": tenant,
                "configuration_name": configuration_name,
            },
            "name",
        )

        if existing:
            return frappe.get_doc("Nexus Tenant Configuration", existing)

    if tenant:
        existing_doc = get_default_tenant_configuration(tenant)
        if existing_doc:
            return existing_doc

    doc = frappe.new_doc("Nexus Tenant Configuration")
    doc.tenant = tenant
    return doc


def get_tenant_configuration_name(tenant):
    """
    Returns the tenant-owned runtime profile name for legacy UI fields.
    """
    doc = get_default_tenant_configuration(tenant)
    return doc.name if doc else None


def unset_other_default_configurations(tenant, current_name=None):
    """
    Ensures only one tenant runtime profile is marked as default.
    """
    if not tenant or not has_field("Nexus Tenant Configuration", "is_default"):
        return

    rows = frappe.get_all(
        "Nexus Tenant Configuration",
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
            "Nexus Tenant Configuration",
            row.name,
            "is_default",
            0,
            update_modified=False,
        )


def apply_configuration_defaults(doc):
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
        "website_widget_enabled": 0,
        "testing_required_before_activation": 1,
        "certification_status": "Not Certified",
        "widget_brand_color": "#214dbb",
        "qa_fallback_message": "I do not have enough approved knowledge to answer this.",
    }

    for fieldname, value in default_values.items():
        if has_field("Nexus Tenant Configuration", fieldname) and not doc.get(fieldname):
            doc.set(fieldname, value)


def ensure_tenant_configuration(
    tenant,
    business_unit=None,
    project=None,
    configuration_name=None,
    configuration_type=None,
    is_default=1,
):
    """
    Ensures a tenant configuration exists for a tenant.

    The simplified model allows one enabled configuration per tenant.
    This creates it when missing, otherwise updates the existing one.
    """
    if not tenant:
        frappe.throw("Tenant is required.")

    configuration_name = configuration_name or make_default_configuration_name(
        tenant=tenant,
        configuration_type=configuration_type,
    )

    values = {
        "tenant": tenant,
        "configuration_name": configuration_name,
        "configuration_type": configuration_type or "Sandbox",
        "enabled": 1,
        "is_default": is_default,
        "activation_status": "Configured",
        "default_business_unit": business_unit,
        "default_project": project,
    }

    ensure_master_value("Nexus Business Unit", business_unit, tenant=tenant)

    doc = get_or_create_tenant_configuration(values)

    for fieldname, value in values.items():
        if value is not None and has_field("Nexus Tenant Configuration", fieldname):
            doc.set(fieldname, value)

    apply_configuration_defaults(doc)

    if doc.get("is_default"):
        unset_other_default_configurations(
            tenant=tenant,
            current_name=doc.name if not doc.is_new() else None,
        )

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    if doc.get("is_default"):
        unset_other_default_configurations(
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
    configuration_name=None,
    configuration_type=None,
):
    """
    Quick tenant onboarding entry point.

    Creates:
    - Nexus Tenant
    - Initial Nexus Tenant Configuration
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

    ecosystem = ensure_tenant_configuration(
        tenant=tenant.name,
        business_unit=business_unit_name,
        configuration_name=configuration_name,
        configuration_type=configuration_type or "Sandbox",
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
        "tenant_configuration": ecosystem.name,
        "configuration_name": ecosystem.configuration_name,
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

    if has_field("Nexus Tenant", "disabled"):
        doc.disabled = 0

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
        ecosystem = get_tenant_configuration_snapshot(tenant=tenant)

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

    category_route_count = count_records_safely(
        doctype="Nexus Category Identity Route",
        extra_filters={
            "enabled": 1,
        },
    )

    registered_identity_route_count = count_registered_identity_routes()
    identity_registry_count = count_records_safely(
        doctype="Nexus Identity Registry",
        extra_filters={
            "enabled": 1,
            "verification_status": "Verified",
        },
    )
    identity_safeguard_count = count_records_safely(
        doctype="Nexus Identity Safe Guard Access Category",
        extra_filters={
            "parenttype": "Nexus Identity Registry",
        },
    )
    identity_safeguard_ready = bool(
        registered_identity_route_count == 0
        or identity_safeguard_count > 0
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
        and ai_agent_count > 0
        and category_route_count > 0
        and identity_safeguard_ready
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
        "tenant_configuration": ecosystem.get("name") if ecosystem else None,
        "configuration_name": ecosystem.get("configuration_name") if ecosystem else None,
        "knowledge_count": knowledge_count,
        "chunk_count": chunk_count,
        "channel_count": channel_count,
        "ai_agent_count": ai_agent_count,
        "category_route_count": category_route_count,
        "registered_identity_route_count": registered_identity_route_count,
        "identity_registry_count": identity_registry_count,
        "identity_safeguard_count": identity_safeguard_count,
        "identity_safeguard_ready": identity_safeguard_ready,
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
        "configuration_name": None,
        "knowledge_count": 0,
        "chunk_count": 0,
        "channel_count": 0,
        "ai_agent_count": 0,
        "category_route_count": 0,
        "registered_identity_route_count": 0,
        "identity_registry_count": 0,
        "identity_safeguard_count": 0,
        "identity_safeguard_ready": False,
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


def count_registered_identity_routes():
    """
    Count enabled category routes that depend on a registered/non-public identity.
    A route is "registered" when it has at least one Nexus Route Identity Profile child row.
    Public routes (no identity_profiles) do not require an Identity Registry Safe Guard.
    """
    doctype = "Nexus Category Identity Route"

    if not frappe.db.exists("DocType", doctype):
        return 0

    try:
        all_route_names = frappe.get_all(
            doctype,
            filters={"enabled": 1},
            pluck="name",
        )
        if not all_route_names:
            return 0
        routes_with_profiles = set(
            frappe.get_all(
                "Nexus Route Identity Profile",
                filters={"parent": ["in", all_route_names]},
                pluck="parent",
            )
        )
        return len(routes_with_profiles)
    except Exception:
        return 0


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def validate_configuration_belongs_to_tenant(ecosystem, tenant):
    if not ecosystem:
        return

    if not frappe.db.exists("Nexus Tenant Configuration", ecosystem):
        frappe.throw(f"Tenant Configuration {ecosystem} does not exist.")

    ecosystem_tenant = frappe.db.get_value(
        "Nexus Tenant Configuration",
        ecosystem,
        "tenant",
    )

    if ecosystem_tenant != tenant:
        frappe.throw("Selected tenant configuration does not belong to the selected tenant.")


def tenant_config_to_dict(doc):
    if not doc:
        return None

    return normalize_configuration_row(
        {
            fieldname: get_doc_value(doc, fieldname)
            for fieldname in get_configuration_field_list()
            if fieldname == "name" or has_field("Nexus Tenant Configuration", fieldname)
        }
    )


def normalize_configuration_row(row):
    row = frappe._dict(row or {})

    if not row.get("configuration_name"):
        row["configuration_name"] = row.get("name")

    if row.get("enabled") is None:
        row["enabled"] = 0

    if row.get("is_default") is None:
        row["is_default"] = 0

    if not row.get("configuration_type"):
        row["configuration_type"] = "Sandbox"

    return dict(row)


def get_configuration_field_list():
    return [
        "name",
        "tenant",
        "configuration_name",
        "configuration_type",
        "enabled",
        "is_default",
        "activation_status",
        "default_business_unit",
        "default_project",
        "require_approved_knowledge",
        "strict_tenant_mode",
        "default_top_k",
        "qa_enabled",
        "default_qa_channel",
        "qa_fallback_message",
        "source_citation_required",
        "live_chat_enabled",
        "default_chat_channel",
        "website_widget_enabled",
        "widget_title",
        "widget_welcome_message",
        "widget_brand_color",
        "testing_required_before_activation",
        "last_certified_on",
        "certification_status",
        "notes",
    ]


def make_default_configuration_name(tenant, configuration_type=None):
    configuration_type = configuration_type or "Sandbox"

    tenant_label = frappe.db.get_value(
        "Nexus Tenant",
        tenant,
        "tenant_name",
    ) if has_field("Nexus Tenant", "tenant_name") else tenant

    tenant_label = tenant_label or tenant

    return f"{tenant_label} {configuration_type} Configuration"


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

@frappe.whitelist()
def get_business_keyword_controls():
    """
    Returns keyword categories and business keywords for Nexus Administration.

    This is an Administration control surface for retrieval relevance signals.
    It does not manage knowledge content.
    """

    categories = []
    keywords = []

    if frappe.db.exists("DocType", "Nexus Keyword Category"):
        categories = frappe.get_all(
            "Nexus Keyword Category",
            fields=[
                "name",
                "category_name",
                "category_code",
                "weight",
                "priority_level",
                "enabled",
                "description",
            ],
            order_by="modified desc",
            limit_page_length=500,
        )

    if frappe.db.exists("DocType", "Nexus Business Keyword"):
        keywords = frappe.get_all(
            "Nexus Business Keyword",
            fields=[
                "name",
                "keyword",
                "category",
                "priority_level",
                "boost_weight",
                "enabled",
                "synonyms",
                "description",
            ],
            order_by="modified desc",
            limit_page_length=500,
        )

    return {
        "categories": categories,
        "keywords": keywords,
    }


@frappe.whitelist()
def save_business_keyword(values):
    """
    Creates or updates a Nexus Business Keyword.

    Expected values:
    {
        "name": optional existing docname,
        "keyword": required,
        "category": optional Nexus Keyword Category,
        "priority_level": High / Medium / Low,
        "boost_weight": float,
        "enabled": 0/1,
        "synonyms": optional text,
        "description": optional text
    }
    """

    values = frappe.parse_json(values) if isinstance(values, str) else values
    values = values or {}

    keyword = (values.get("keyword") or "").strip()
    if not keyword:
        frappe.throw("Business Keyword is required.")

    docname = values.get("name")

    if docname and frappe.db.exists("Nexus Business Keyword", docname):
        doc = frappe.get_doc("Nexus Business Keyword", docname)
    else:
        # Avoid duplicate keyword/category combinations where possible.
        existing_name = frappe.db.get_value(
            "Nexus Business Keyword",
            {
                "keyword": keyword,
                "category": values.get("category"),
            },
            "name",
        )

        if existing_name:
            doc = frappe.get_doc("Nexus Business Keyword", existing_name)
        else:
            doc = frappe.new_doc("Nexus Business Keyword")

    doc.keyword = keyword
    doc.category = values.get("category") or None
    doc.priority_level = values.get("priority_level") or "Medium"
    doc.boost_weight = float(values.get("boost_weight") or 0)
    doc.enabled = 1 if int(values.get("enabled") or 0) else 0
    doc.synonyms = values.get("synonyms") or None
    doc.description = values.get("description") or None

    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "name": doc.name,
        "keyword": doc.keyword,
        "category": doc.category,
        "priority_level": doc.priority_level,
        "boost_weight": doc.boost_weight,
        "enabled": doc.enabled,
    }


@frappe.whitelist()
def set_business_keyword_enabled(name, enabled):
    """
    Enables or disables a Nexus Business Keyword.
    """

    if not name:
        frappe.throw("Business Keyword name is required.")

    if not frappe.db.exists("Nexus Business Keyword", name):
        frappe.throw(f"Nexus Business Keyword not found: {name}")

    frappe.db.set_value(
        "Nexus Business Keyword",
        name,
        "enabled",
        1 if int(enabled or 0) else 0,
    )
    frappe.db.commit()

    return {
        "name": name,
        "enabled": 1 if int(enabled or 0) else 0,
    }

@frappe.whitelist()
def get_access_governance_overview():
    """
    Returns Access Governance overview for Nexus Administration.

    Administration reviews governance coverage and policy masters.
    Actual knowledge-level assignment belongs to Nexus Studio / knowledge metadata.
    """

    def doctype_exists(doctype):
        return bool(frappe.db.exists("DocType", doctype))

    def field_exists(doctype, fieldname):
        if not doctype_exists(doctype):
            return False

        return bool(
            frappe.db.exists(
                "DocField",
                {
                    "parent": doctype,
                    "fieldname": fieldname,
                },
            )
        )

    def count_all(doctype, filters=None):
        if not doctype_exists(doctype):
            return 0

        return frappe.db.count(doctype, filters or {})

    def count_non_empty(doctype, fieldname):
        if not doctype_exists(doctype):
            return 0

        if not field_exists(doctype, fieldname):
            return 0

        return frappe.db.sql(
            f"""
            SELECT COUNT(*)
            FROM `tab{doctype}`
            WHERE IFNULL(`{fieldname}`, '') != ''
            """,
            as_list=True,
        )[0][0] or 0

    def sensitivity_distribution(doctype):
        if not doctype_exists(doctype):
            return []

        if not field_exists(doctype, "sensitivity"):
            return [
                {
                    "sensitivity": "Not Available",
                    "count": count_all(doctype),
                }
            ]

        rows = frappe.db.sql(
            f"""
            SELECT
                CASE
                    WHEN IFNULL(sensitivity, '') = '' THEN 'Not Set'
                    ELSE sensitivity
                END AS sensitivity,
                COUNT(*) AS count
            FROM `tab{doctype}`
            GROUP BY
                CASE
                    WHEN IFNULL(sensitivity, '') = '' THEN 'Not Set'
                    ELSE sensitivity
                END
            ORDER BY count DESC
            """,
            as_dict=True,
        )

        return rows or []

    policies = []

    if doctype_exists("Nexus Access Policy"):
        policies = frappe.get_all(
            "Nexus Access Policy",
            fields=[
                "name",
                "policy_name",
                "disabled",
                "access_level",
                "sensitivity",
                "allowed_roles",
                "excluded_roles",
                "allowed_designations",
                "excluded_designations",
                "description",
            ],
            order_by="modified desc",
            limit_page_length=500,
        )

    overview = {
        "access_policy_count": len(policies),
        "enabled_policy_count": len(
            [p for p in policies if not int(p.get("disabled") or 0)]
        ),
        "disabled_policy_count": len(
            [p for p in policies if int(p.get("disabled") or 0)]
        ),

        "knowledge_sources_total": count_all("Nexus Knowledge Source"),
        "knowledge_sources_with_policy": count_non_empty(
            "Nexus Knowledge Source",
            "access_policy",
        ),

        "knowledge_units_total": count_all("Nexus Knowledge Unit"),
        "knowledge_units_with_policy": count_non_empty(
            "Nexus Knowledge Unit",
            "default_access_policy",
        ),

        "knowledge_chunks_total": count_all("Nexus Knowledge Chunk"),
        "knowledge_chunks_with_policy": count_non_empty(
            "Nexus Knowledge Chunk",
            "access_policy",
        ),
        "knowledge_chunks_with_allowed_roles": count_non_empty(
            "Nexus Knowledge Chunk",
            "allowed_roles",
        ),
        "knowledge_chunks_with_denied_roles": count_non_empty(
            "Nexus Knowledge Chunk",
            "denied_roles",
        ),

        # Source does not currently have sensitivity field.
        # This now safely returns Not Available instead of failing.
        "source_sensitivity_distribution": sensitivity_distribution(
            "Nexus Knowledge Source"
        ),
        "unit_sensitivity_distribution": sensitivity_distribution(
            "Nexus Knowledge Unit"
        ),
        "chunk_sensitivity_distribution": sensitivity_distribution(
            "Nexus Knowledge Chunk"
        ),
    }

    return {
        "overview": overview,
        "policies": policies,
    }
