"""
Companion Dashboard API — data endpoints for the Nexus Companion Dashboard page.
"""

import frappe
from frappe.utils import nowdate, add_days


@frappe.whitelist()
def get_dashboard_data(tenant=None):
    """
    Return all data needed to render the Companion Dashboard in one call.
    """
    tenant = tenant or _resolve_default_tenant()

    return {
        "tenant": tenant,
        "stage_funnel": _get_stage_funnel(tenant),
        "stats": _get_stats(tenant),
        "recent_enquiries": _get_recent_enquiries(tenant, limit=20),
        "top_personas": _get_top_personas(tenant),
        "config_summary": _get_config_summary(tenant),
    }


@frappe.whitelist()
def get_enquiry_detail(name):
    """Return full detail for a single Nexus Companion Enquiry."""
    if not frappe.db.exists("Nexus Companion Enquiry", name):
        frappe.throw("Enquiry not found", frappe.DoesNotExistError)

    enq = frappe.get_doc("Nexus Companion Enquiry", name)

    conversation_id = None
    visitor_name = None
    if enq.conversation:
        row = frappe.db.get_value(
            "Nexus Live Conversation",
            enq.conversation,
            ["conversation_id", "visitor_name"],
            as_dict=True,
        )
        if row:
            conversation_id = row.conversation_id
            visitor_name = row.visitor_name

    persona_name = None
    if enq.matched_persona:
        persona_name = frappe.db.get_value(
            "Nexus Companion Persona", enq.matched_persona, "persona_name"
        )

    return {
        "name": enq.name,
        "enquiry_stage": enq.enquiry_stage,
        "companion_milestone": enq.companion_milestone or "",
        "enquiry_score": enq.enquiry_score,
        "escalation_recommended": enq.escalation_recommended,
        "recommended_next_step": enq.recommended_next_step,
        "matched_persona": enq.matched_persona,
        "persona_name": persona_name,
        "persona_confidence": enq.persona_confidence,
        "discovery_data": enq.discovery_data,
        "stage_signal": enq.stage_signal,
        "signal_log": enq.signal_log,
        "visitor_email": enq.visitor_email,
        "verification_status": enq.verification_status,
        "conversation": enq.conversation,
        "conversation_id": conversation_id,
        "visitor_name": visitor_name,
        "created_on": str(enq.created_on) if enq.created_on else None,
        "recommended_products": [
            {"product": r.product, "product_name": r.product_name, "fit_score": r.fit_score}
            for r in (enq.recommended_products or [])
        ],
        "recommended_services": [
            {"service": r.service, "service_name": r.service_name, "fit_score": r.fit_score}
            for r in (enq.recommended_services or [])
        ],
    }


@frappe.whitelist()
def get_tenants():
    """Return available tenants for the tenant selector."""
    return frappe.get_all("Nexus Tenant", fields=["name", "tenant_name"], filters={"disabled": 0})


@frappe.whitelist()
def get_conversation_transcript(conversation):
    """
    Read-only transcript for the dashboard chat viewer.
    `conversation` is the Nexus Live Conversation docname
    (Nexus Companion Enquiry.conversation).
    """
    if not conversation or not frappe.db.exists("Nexus Live Conversation", conversation):
        frappe.throw("Conversation not found", frappe.DoesNotExistError)

    conv = frappe.db.get_value(
        "Nexus Live Conversation",
        conversation,
        [
            "name", "conversation_id", "visitor_name", "visitor_email",
            "status", "chat_category", "started_on", "last_message_at", "human_agent",
        ],
        as_dict=True,
    )

    conv["human_agent_name"] = (
        frappe.db.get_value("User", conv.human_agent, "full_name") if conv.human_agent else None
    )

    messages = frappe.get_all(
        "Nexus Live Message",
        filters={"conversation": conversation},
        fields=["name", "sender_type", "sender_agent", "message", "confidence", "message_time"],
        order_by="message_time asc, creation asc",
        limit_page_length=500,
    )

    for m in messages:
        m["message_time"] = str(m["message_time"]) if m["message_time"] else None
    conv["started_on"] = str(conv.started_on) if conv.started_on else None
    conv["last_message_at"] = str(conv.last_message_at) if conv.last_message_at else None

    return {"conversation": conv, "messages": messages}


# ── Internal helpers ──────────────────────────────────────────────────────────

_STAGE_ORDER = [
    "ARRIVED", "GREETING", "DISCOVERY", "ENGAGED",
    "PRESENTING", "OBJECTION_HANDLING", "INTERESTED",
    "CONVERTING", "CONVERTED", "DECLINED", "ESCALATED",
]

_STAGE_LABELS = {
    "ARRIVED": "Arrived",
    "GREETING": "Greeting",
    "DISCOVERY": "Discovery",
    "ENGAGED": "Engaged",
    "PRESENTING": "Presenting",
    "OBJECTION_HANDLING": "Objection",
    "INTERESTED": "Interested",
    "CONVERTING": "Converting",
    "CONVERTED": "Converted",
    "DECLINED": "Declined",
    "ESCALATED": "Escalated",
}


def _resolve_default_tenant():
    try:
        settings = frappe.get_single("Nexus Settings")
        return getattr(settings, "default_tenant", None) or ""
    except Exception:
        return ""


def _get_stage_funnel(tenant):
    filters = {}
    if tenant:
        filters["tenant"] = tenant

    rows = frappe.get_all(
        "Nexus Companion Enquiry",
        filters=filters,
        fields=["enquiry_stage", "count(*) as count"],
        group_by="enquiry_stage",
    )

    count_map = {r.enquiry_stage: r.count for r in rows}

    return [
        {
            "stage": stage,
            "label": _STAGE_LABELS.get(stage, stage),
            "count": count_map.get(stage, 0),
        }
        for stage in _STAGE_ORDER
    ]


def _get_stats(tenant):
    today = nowdate()
    week_ago = add_days(today, -7)

    base_filters = {}
    if tenant:
        base_filters["tenant"] = tenant

    total = frappe.db.count("Nexus Companion Enquiry", filters=base_filters)

    today_filters = dict(base_filters)
    today_filters["creation"] = [">=", today]
    today_count = frappe.db.count("Nexus Companion Enquiry", filters=today_filters)

    converted_filters = dict(base_filters)
    converted_filters["enquiry_stage"] = "CONVERTED"
    qualified_count = frappe.db.count("Nexus Companion Enquiry", filters=converted_filters)

    escalated_filters = dict(base_filters)
    escalated_filters["enquiry_stage"] = "ESCALATED"
    escalated_count = frappe.db.count("Nexus Companion Enquiry", filters=escalated_filters)

    week_filters = dict(base_filters)
    week_filters["creation"] = [">=", week_ago]
    week_rows = frappe.get_all(
        "Nexus Companion Enquiry",
        filters=week_filters,
        fields=["avg(enquiry_score) as avg_score"],
    )
    avg_score = round(float((week_rows[0].avg_score or 0) if week_rows else 0), 1)

    return {
        "total": total,
        "today": today_count,
        "converted": qualified_count,
        "escalated": escalated_count,
        "avg_score_7d": avg_score,
    }


def _get_recent_enquiries(tenant, limit=20):
    filters = {}
    if tenant:
        filters["tenant"] = tenant

    rows = frappe.get_all(
        "Nexus Companion Enquiry",
        filters=filters,
        fields=[
            "name", "enquiry_stage", "companion_milestone", "enquiry_score",
            "matched_persona", "persona_confidence", "recommended_next_step",
            "conversation", "escalation_recommended", "creation",
        ],
        order_by="creation desc",
        limit_page_length=limit,
    )

    # Enrich with visitor name and persona name
    for row in rows:
        row["persona_name"] = None
        if row.matched_persona:
            row["persona_name"] = frappe.db.get_value(
                "Nexus Companion Persona", row.matched_persona, "persona_name"
            )

        row["visitor_name"] = None
        row["conversation_id"] = None
        if row.conversation:
            conv = frappe.db.get_value(
                "Nexus Live Conversation",
                row.conversation,
                ["visitor_name", "conversation_id"],
                as_dict=True,
            )
            if conv:
                row["visitor_name"] = conv.visitor_name
                row["conversation_id"] = conv.conversation_id

        row["creation"] = str(row.creation) if row.creation else None

    return rows


def _get_top_personas(tenant):
    filters = {"tenant": tenant} if tenant else {}
    rows = frappe.get_all(
        "Nexus Companion Enquiry",
        filters={**filters, "matched_persona": ["is", "set"]},
        fields=["matched_persona", "count(*) as count"],
        group_by="matched_persona",
        order_by="count desc",
        limit_page_length=5,
    )
    result = []
    for r in rows:
        persona_name = frappe.db.get_value(
            "Nexus Companion Persona", r.matched_persona, "persona_name"
        )
        result.append({"persona": r.matched_persona, "persona_name": persona_name, "count": r.count})
    return result


def _get_config_summary(tenant):
    filters = {"tenant": tenant, "enabled": 1} if tenant else {"enabled": 1}
    return {
        "playbooks": frappe.db.count("Nexus Companion Playbook", filters=filters),
        "personas": frappe.db.count("Nexus Companion Persona", filters=filters),
        "products": frappe.db.count("Nexus Companion Product", filters=filters),
        "services": frappe.db.count("Nexus Companion Service", filters=filters),
        "stories": frappe.db.count("Nexus Companion Story", filters={"tenant": tenant, "approved": 1} if tenant else {"approved": 1}),
        "testimonials": frappe.db.count("Nexus Companion Testimonial", filters={"tenant": tenant, "approved": 1} if tenant else {"approved": 1}),
        "outcomes": frappe.db.count("Nexus Companion Outcome", filters={"tenant": tenant, "approved": 1} if tenant else {"approved": 1}),
    }
