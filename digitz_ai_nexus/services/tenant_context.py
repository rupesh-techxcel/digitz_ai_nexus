import frappe
from frappe.utils import now_datetime


def get_current_user(user=None):
    return user or frappe.session.user


def get_user_context(user=None):
    """
    Returns the active Nexus User Context for the given user.

    Priority:
    1. enabled + is_default
    2. enabled latest modified
    """
    user = get_current_user(user)

    if not user or user == "Guest":
        return None

    context_name = frappe.db.get_value(
        "Nexus User Context",
        {
            "user": user,
            "enabled": 1,
            "is_default": 1,
        },
        "name",
    )

    if not context_name:
        contexts = frappe.get_all(
            "Nexus User Context",
            filters={
                "user": user,
                "enabled": 1,
            },
            fields=["name"],
            order_by="modified desc",
            limit_page_length=1,
        )

        context_name = contexts[0].name if contexts else None

    if not context_name:
        return None

    return frappe.get_doc("Nexus User Context", context_name)


def get_ecosystem_for_tenant(tenant):
    """
    Returns the active Nexus Ecosystem configuration for a tenant.

    Priority:
    1. enabled + tenant default
    2. latest enabled ecosystem
    """
    if not tenant:
        return None

    ecosystem_name = frappe.db.get_value(
        "Nexus Ecosystem",
        {
            "tenant": tenant,
            "enabled": 1,
            "is_default": 1,
        },
        "name",
    )

    if not ecosystem_name:
        ecosystem_name = frappe.db.get_value(
            "Nexus Ecosystem",
            {
                "tenant": tenant,
                "enabled": 1,
            },
            "name",
            order_by="modified desc",
        )

    if not ecosystem_name:
        return None

    return frappe.get_doc("Nexus Ecosystem", ecosystem_name)


def resolve_tenant_context(payload=None, user=None, require_tenant=True):
    """
    Central resolver for tenant-aware platform behaviour.

    Resolution priority:
    1. Explicit payload values
    2. Current user's Nexus User Context
    3. Nexus Ecosystem defaults
    4. Error if tenant is required
    """
    payload = payload or {}
    user = get_current_user(user)

    user_context = get_user_context(user)

    tenant = (
        payload.get("tenant")
        or payload.get("active_tenant")
        or (user_context.active_tenant if user_context else None)
    )

    if require_tenant and not tenant:
        frappe.throw(
            "Tenant is required. Please select an active tenant in Nexus Administration."
        )

    ecosystem = get_ecosystem_for_tenant(tenant)

    business_unit = (
        payload.get("business_unit")
        or payload.get("active_business_unit")
        or (user_context.active_business_unit if user_context else None)
        or (ecosystem.default_business_unit if ecosystem else None)
    )

    project = (
        payload.get("project")
        or payload.get("active_project")
        or (user_context.active_project if user_context else None)
        or (ecosystem.default_project if ecosystem else None)
    )

    channel = (
        payload.get("channel")
        or payload.get("active_channel")
        or (user_context.active_channel if user_context else None)
        or (ecosystem.default_live_channel if ecosystem else None)
        or (ecosystem.default_chat_channel if ecosystem else None)
        or (ecosystem.default_qa_channel if ecosystem else None)
    )

    context = (
        payload.get("context")
        or (ecosystem.default_public_context if ecosystem else None)
    )

    resolved = frappe._dict({
        "user": user,
        "tenant": tenant,
        "business_unit": business_unit,
        "project": project,
        "channel": channel,
        "context": context,
        "user_context": user_context.name if user_context else None,
        "ecosystem": ecosystem.name if ecosystem else None,
        "ecosystem_activation_status": ecosystem.activation_status if ecosystem else None,
        "qa_enabled": ecosystem.qa_enabled if ecosystem else None,
        "live_chat_enabled": ecosystem.live_chat_enabled if ecosystem else None,
        "default_qa_channel": ecosystem.default_qa_channel if ecosystem else None,
        "default_chat_channel": ecosystem.default_chat_channel if ecosystem else None,
        "default_public_agent": ecosystem.default_public_agent if ecosystem else None,
        "default_public_escalation_queue": ecosystem.default_public_escalation_queue if ecosystem else None,
        "default_top_k": ecosystem.default_top_k if ecosystem else None,
        "require_approved_knowledge": ecosystem.require_approved_knowledge if ecosystem else None,
        "strict_tenant_mode": ecosystem.strict_tenant_mode if ecosystem else None,
    })

    return resolved


def apply_tenant_context_to_payload(payload=None, user=None, require_tenant=True):
    """
    Returns a payload enriched with resolved tenant context.
    This should be used before Q&A, Live Chat, testing, and widget runtime calls.
    """
    payload = payload or {}
    resolved = resolve_tenant_context(
        payload=payload,
        user=user,
        require_tenant=require_tenant,
    )

    enriched = dict(payload)

    enriched["tenant"] = enriched.get("tenant") or resolved.tenant
    enriched["business_unit"] = enriched.get("business_unit") or resolved.business_unit
    enriched["project"] = enriched.get("project") or resolved.project
    enriched["channel"] = enriched.get("channel") or resolved.channel
    enriched["context"] = enriched.get("context") or resolved.context

    if not enriched.get("top_k") and resolved.default_top_k:
        enriched["top_k"] = resolved.default_top_k

    enriched["_resolved_tenant_context"] = {
        "user_context": resolved.user_context,
        "ecosystem": resolved.ecosystem,
        "tenant": resolved.tenant,
        "business_unit": resolved.business_unit,
        "project": resolved.project,
        "channel": resolved.channel,
        "context": resolved.context,
    }

    return enriched


def set_user_context(
    user=None,
    tenant=None,
    business_unit=None,
    project=None,
    channel=None,
    is_default=1,
):
    """
    Creates or updates the active Nexus User Context for a user.
    """
    user = get_current_user(user)

    if not user or user == "Guest":
        frappe.throw("A logged-in user is required to set Nexus User Context.")

    if not tenant:
        frappe.throw("Tenant is required.")

    existing = frappe.db.get_value(
        "Nexus User Context",
        {
            "user": user,
            "active_tenant": tenant,
        },
        "name",
    )

    if existing:
        doc = frappe.get_doc("Nexus User Context", existing)
    else:
        doc = frappe.new_doc("Nexus User Context")
        doc.user = user
        doc.active_tenant = tenant

    doc.enabled = 1
    doc.is_default = is_default
    doc.active_business_unit = business_unit
    doc.active_project = project
    doc.active_channel = channel
    doc.last_used_on = now_datetime()

    doc.save(ignore_permissions=True)

    if is_default:
        clear_other_default_contexts(user=user, keep=doc.name)

    frappe.db.commit()

    return doc


def clear_other_default_contexts(user, keep):
    contexts = frappe.get_all(
        "Nexus User Context",
        filters={
            "user": user,
            "is_default": 1,
            "name": ["!=", keep],
        },
        pluck="name",
    )

    for name in contexts:
        frappe.db.set_value(
            "Nexus User Context",
            name,
            "is_default",
            0,
            update_modified=True,
        )


def touch_user_context(user=None):
    context = get_user_context(user)

    if not context:
        return None

    context.last_used_on = now_datetime()
    context.save(ignore_permissions=True)

    return context.name
