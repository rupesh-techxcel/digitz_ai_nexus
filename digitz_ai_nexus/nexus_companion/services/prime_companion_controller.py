# digitz_ai_nexus/nexus_companion/services/prime_companion_controller.py
#
# DIGITZ PRIME product-enquiry companion (still spoken as "Nexy").
#
# This is a STANDALONE controller: it carries its own copies of the brand-neutral
# machinery (milestones, discovery, pending-action, email/identity verification,
# meeting-booking card) that also live in business_companion_controller.py. It is
# intentionally decoupled from that module — fixes to shared machinery must be
# applied in BOTH files. Shared *services* (enquiry_service, signal_classifier,
# companion_intent_service, persona_matching_service, chat_agent_loop) are reused
# by import, not copied.
#
# Journey (reuses the same 8-state companion_milestone enum):
#   onboarding_business -> business_discovery -> pain_discovery (requirement
#   understanding) -> solution_mapping (PRODUCT FIT) -> evidence_building ->
#   demo_arrangement (book demo/consultation) -> quotation -> conversion.
#
# Selected per Nexus Chat Category.companion_controller_type == "prime_companion".

import json
import frappe

from digitz_ai_nexus.engine.llm import generate_answer
from digitz_ai_nexus.nexus_companion.services.enquiry_service import (
    get_or_create_enquiry,
    update_enquiry,
    advance_journey_stage_from_signal,
)
from digitz_ai_nexus.nexus_companion.services.signal_classifier import (
    classify_signal,
    is_conversion_signal,
)
from digitz_ai_nexus.nexus_companion.services.companion_intent_service import (
    classify_external_intent,
)


# Brand block — Nexy persona is retained across tenants; only the represented
# team and product catalogue differ for DIGITZ PRIME.
COMPANION_NAME = "Nexy"
REP_LABEL = "DIGITZ Prime specialist"


# ---------------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------------

def _companion_flow_debug(stage, data=None):
    try:
        print("\n\n========== PRIME COMPANION:", stage, "==========")
        if data is not None:
            print(json.dumps(data, indent=2, default=str))
        print("=========================================\n\n")
        try:
            frappe.logger("nexus_debug").info({"prime_stage": stage, "data": data})
        except Exception:
            pass
    except Exception:
        print("\n\n===== PRIME COMPANION DEBUG FAILED =====", stage)


def _preview_text(value, limit=350):
    value = str(value or "").strip()
    return value[:limit] + "..." if len(value) > limit else value


# ---------------------------------------------------------------------------
# Conversation / agent helpers  (copied verbatim — brand-neutral)
# ---------------------------------------------------------------------------

def _get_conversation_assigned_agent(conversation):
    try:
        agent_name = (getattr(conversation, "assigned_agent", None) or "").strip()
        if agent_name:
            return agent_name
    except Exception:
        pass
    try:
        return (
            frappe.db.get_value("Nexus Live Conversation", conversation.name, "assigned_agent")
            or ""
        ).strip()
    except Exception:
        return ""


def _safe_get_existing_field_value(doctype, docname, fieldnames):
    try:
        meta = frappe.get_meta(doctype)
        existing_fields = {df.fieldname for df in meta.fields}
        for fieldname in fieldnames:
            if fieldname not in existing_fields:
                continue
            if docname:
                value = frappe.db.get_value(doctype, docname, fieldname) or ""
            else:
                value = frappe.db.get_single_value(doctype, fieldname) or ""
            value = str(value or "").strip()
            if value:
                return value
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: field read failed")
    return ""


# ---------------------------------------------------------------------------
# Milestone helpers  (copied verbatim — same 8-state enum)
# ---------------------------------------------------------------------------

_BUSINESS_MILESTONES = (
    "onboarding_business",
    "business_discovery",
    "pain_discovery",
    "solution_mapping",
    "evidence_building",
    "demo_arrangement",
    "quotation",
    "conversion",
)


def _get_current_milestone(conversation):
    milestone = (getattr(conversation, "companion_milestone", None) or "").strip()
    if milestone in _BUSINESS_MILESTONES:
        return milestone

    stage = (getattr(conversation, "companion_journey_stage", None) or "").strip()
    stage_to_milestone = {
        "ARRIVED": "onboarding_business",
        "GREETING": "onboarding_business",
        "DISCOVERY": "onboarding_business",
        "ENGAGED": "business_discovery",
        "PRESENTING": "solution_mapping",
        "OBJECTION_HANDLING": "solution_mapping",
        "INTERESTED": "evidence_building",
        "QUALIFIED": "demo_arrangement",
        "CONVERTING": "demo_arrangement",
        "CONVERTED": "conversion",
        "DECLINED": "conversion",
        "ESCALATED": "conversion",
    }
    return stage_to_milestone.get(stage) or "onboarding_business"


def _publish_progress_update(conversation, new_milestone=None):
    try:
        enquiry_name = getattr(conversation, "companion_enquiry", None)
        stage = frappe.db.get_value(
            "Nexus Live Conversation", conversation.name, "companion_journey_stage"
        ) or ""
        milestone = new_milestone or frappe.db.get_value(
            "Nexus Live Conversation", conversation.name, "companion_milestone"
        ) or ""
        frappe.publish_realtime(
            "companion_progress_update",
            {
                "enquiry": enquiry_name,
                "conversation": conversation.name,
                "stage": stage,
                "milestone": milestone,
            },
            doctype="Nexus Companion Enquiry",
            docname=enquiry_name,
            after_commit=True,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: realtime publish failed")


def _maybe_advance_milestone(conversation):
    """Advance onboarding_business -> business_discovery once industry + a challenge
    are captured. Later transitions are driven by steering/journey-stage."""
    try:
        if _get_current_milestone(conversation) != "onboarding_business":
            return
        enquiry_name = getattr(conversation, "companion_enquiry", None)
        if not enquiry_name:
            return
        discovery_raw = frappe.db.get_value(
            "Nexus Companion Enquiry", enquiry_name, "discovery_data"
        ) or "{}"
        try:
            discovery = json.loads(discovery_raw)
        except Exception:
            discovery = {}
        if all(discovery.get(k) for k in ("industry", "current_challenges")):
            new_milestone = "business_discovery"
            frappe.db.set_value(
                "Nexus Live Conversation", conversation.name,
                "companion_milestone", new_milestone, update_modified=False,
            )
            frappe.db.set_value(
                "Nexus Companion Enquiry", enquiry_name,
                "companion_milestone", new_milestone, update_modified=False,
            )
            _publish_progress_update(conversation, new_milestone=new_milestone)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: milestone advance failed")


def _set_milestone(conversation, milestone):
    if milestone not in _BUSINESS_MILESTONES:
        return
    try:
        frappe.db.set_value(
            "Nexus Live Conversation", conversation.name,
            "companion_milestone", milestone, update_modified=False,
        )
        enquiry_name = getattr(conversation, "companion_enquiry", None)
        if enquiry_name:
            frappe.db.set_value(
                "Nexus Companion Enquiry", enquiry_name,
                "companion_milestone", milestone, update_modified=False,
            )
        conversation.companion_milestone = milestone
        _publish_progress_update(conversation, new_milestone=milestone)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: set milestone failed")


# ---------------------------------------------------------------------------
# Discovery fact helpers  (copied verbatim)
# ---------------------------------------------------------------------------

def _get_discovery_facts(discovery):
    facts = (discovery or {}).get("discovery_facts") or []
    return facts if isinstance(facts, list) else []


def _get_fact_value(discovery, context_area, fact_type):
    for fact in _get_discovery_facts(discovery):
        if str(fact.get("context_area") or "").strip() != context_area:
            continue
        if str(fact.get("fact_type") or "").strip() != fact_type:
            continue
        val = str(fact.get("fact_value") or "").strip()
        if val:
            return val
    return ""


# ---------------------------------------------------------------------------
# Product-enquiry discovery extraction  (adapted prompt; product domains)
# ---------------------------------------------------------------------------

def _extract_discovery_data(visitor_message, current_milestone, conversation):
    prompt = f"""
Extract business discovery information from a visitor asking about DIGITZ Prime
business software products (ERP, CRM, HR/Payroll, Inventory, Accounting, etc.).

Current milestone: {current_milestone}

Visitor message:
{visitor_message}

Return ONLY valid JSON. Use these keys when clearly present:
company_name, industry, company_size, team_size, business_type,
business_maturity, current_challenges, goals, existing_systems,
budget_range, timeline, decision_maker

Also include a "discovery_facts" array for specific facts found. Each fact:
  "context_area": one of "erp_accounting", "crm_sales", "inventory",
                  "hr_payroll", "operations", "general_business"
  "fact_type": one of "current_tool", "existing_system", "bottleneck",
               "process_gap", "goal", "module_interest", "volume", "urgency",
               "decision_role"
  "fact_value": the extracted value (non-empty string)
  "source_message": the original phrase

Examples:
- "We use Tally but stock tracking is a mess" -> {{"existing_systems": "Tally", "current_challenges": "stock tracking", "discovery_facts": [{{"context_area": "inventory", "fact_type": "bottleneck", "fact_value": "stock tracking is a mess", "source_message": "stock tracking is a mess"}}, {{"context_area": "erp_accounting", "fact_type": "current_tool", "fact_value": "Tally", "source_message": "We use Tally"}}]}}
- "We run a 20-branch pharmacy chain" -> {{"industry": "pharmacy retail", "company_size": "20 branches", "business_type": "retail chain", "discovery_facts": []}}
- "Need to manage leads and follow-ups" -> {{"current_challenges": "lead management and follow-up", "discovery_facts": [{{"context_area": "crm_sales", "fact_type": "goal", "fact_value": "manage leads and follow-ups", "source_message": "manage leads and follow-ups"}}]}}
- "Payroll takes us days every month" -> {{"current_challenges": "payroll processing time", "discovery_facts": [{{"context_area": "hr_payroll", "fact_type": "bottleneck", "fact_value": "payroll takes days each month", "source_message": "Payroll takes us days every month"}}]}}

Only extract facts clearly stated. Do not infer. If nothing found, return {{}}.
"""
    try:
        raw = (generate_answer(prompt) or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json", "", 1).strip()
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: discovery extraction failed")
        return {}


# ---------------------------------------------------------------------------
# Pending-action helpers  (copied verbatim)
# ---------------------------------------------------------------------------

def _get_companion_pending_action(conversation):
    try:
        val = frappe.db.get_value(
            "Nexus Live Conversation", conversation.name, "companion_pending_action"
        )
        return (val or "").strip()
    except Exception:
        return (getattr(conversation, "companion_pending_action", None) or "").strip()


def _get_companion_pending_context(conversation):
    try:
        val = frappe.db.get_value(
            "Nexus Live Conversation", conversation.name, "companion_pending_context_json"
        )
        return json.loads(val) if val and isinstance(val, str) else {}
    except Exception:
        return {}


def _set_companion_pending_action(conversation, action, context=None):
    try:
        update_data = {"companion_pending_action": action or ""}
        if context is not None:
            update_data["companion_pending_context_json"] = json.dumps(context or {}, default=str)
        frappe.db.set_value(
            "Nexus Live Conversation", conversation.name, update_data, update_modified=False
        )
        frappe.db.commit()
        try:
            conversation.companion_pending_action = action or ""
            if context is not None:
                conversation.companion_pending_context_json = json.dumps(context or {}, default=str)
        except Exception:
            pass
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: set pending action failed")


def _clear_companion_pending_action(conversation):
    _set_companion_pending_action(conversation, "", None)


# ---------------------------------------------------------------------------
# Email / identity verification  (copied verbatim — brand-neutral)
# ---------------------------------------------------------------------------

def send_companion_email_verification(conversation, email):
    import hashlib as _hashlib
    import secrets as _secrets

    otp = str(_secrets.randbelow(900000) + 100000)
    otp_hash = _hashlib.sha256(otp.encode()).hexdigest()
    expires_on = frappe.utils.add_to_date(frappe.utils.now_datetime(), minutes=10)
    try:
        frappe.db.set_value(
            "Nexus Live Conversation", conversation.name,
            {
                "companion_email_verification_hash": otp_hash,
                "companion_email_verification_expires_on": expires_on,
                "companion_email_verification_retry_count": 0,
                "visitor_email": email,
            },
            update_modified=False,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: verification save failed")
        return {"status": "error", "reason": "save_failed"}
    try:
        frappe.sendmail(
            recipients=[email],
            subject=f"Your {COMPANION_NAME} Verification Code",
            message=(
                f"<p>Your email verification code for {COMPANION_NAME} is:</p>"
                f"<h2 style='letter-spacing:4px'>{otp}</h2>"
                "<p>This code expires in 10 minutes.</p>"
            ),
            now=True,
        )
        return {"status": "sent", "email": email}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: verification send failed")
        return {"status": "error", "reason": "send_failed"}


def verify_companion_email_code(conversation, code):
    import hashlib as _hashlib
    try:
        result = frappe.db.get_value(
            "Nexus Live Conversation", conversation.name,
            [
                "companion_email_verification_hash",
                "companion_email_verification_expires_on",
                "companion_email_verification_retry_count",
            ],
            as_dict=True,
        ) or {}
        stored_hash = (result.get("companion_email_verification_hash") or "").strip()
        expires_on = result.get("companion_email_verification_expires_on")
        retry_count = int(result.get("companion_email_verification_retry_count") or 0)
        if not stored_hash:
            return {"verified": False, "reason": "no_pending_verification"}
        if retry_count >= 5:
            return {"verified": False, "reason": "max_retries_exceeded"}
        frappe.db.set_value(
            "Nexus Live Conversation", conversation.name,
            "companion_email_verification_retry_count", retry_count + 1, update_modified=False,
        )
        if expires_on:
            try:
                if frappe.utils.now_datetime() > frappe.utils.get_datetime(str(expires_on)):
                    return {"verified": False, "reason": "code_expired"}
            except Exception:
                pass
        if _hashlib.sha256(str(code).encode()).hexdigest() == stored_hash:
            frappe.db.set_value(
                "Nexus Live Conversation", conversation.name,
                {"companion_email_verification_hash": "", "companion_email_verified": 1},
                update_modified=False,
            )
            return {"verified": True}
        return {"verified": False, "reason": "invalid_code"}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: verification check failed")
        return {"verified": False, "reason": "error"}


def _is_booking_email_verified(conversation):
    try:
        row = frappe.db.get_value(
            "Nexus Live Conversation", conversation.name,
            ["visitor_email", "companion_email_verified", "companion_pending_action",
             "companion_pending_context_json"],
            as_dict=True,
        ) or {}
        if bool(row.get("companion_email_verified")):
            return True
        visitor_email = (row.get("visitor_email") or "").strip()
        pending_action = (row.get("companion_pending_action") or "").strip()
        try:
            ctx = json.loads(row.get("companion_pending_context_json") or "{}")
        except Exception:
            ctx = {}
        return bool(
            visitor_email
            and pending_action == "collect_representative_note"
            and (ctx.get("verified_via") or "").strip() in {"idv_challenge", "email_code"}
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: email-verified check failed")
        return False


def _decorate_email_collection_response(response, conversation, purpose="demo_or_consultation_booking"):
    response = response or {}
    response["requires_email_verification"] = True
    response["identity_verification_offer"] = True
    response["verification_prompt_allowed"] = True
    response["verification_stage"] = "collect_email"
    response["verification_purpose"] = purpose
    response["pending_action"] = "collect_email_for_consultancy"
    response["booking_blocked_until_verified"] = True
    response["access_status"] = "awaiting_verification"
    return response


# ---------------------------------------------------------------------------
# Meeting booking  (copied verbatim; rep label parameterised)
# ---------------------------------------------------------------------------

def _resolve_meeting_booking_link(conversation):
    agent_name = _get_conversation_assigned_agent(conversation)
    scheduling_link = ""
    if agent_name:
        scheduling_link = _safe_get_existing_field_value(
            "Nexus AI Agent Profile", agent_name,
            ["calendly_link", "calendly_url", "meeting_scheduling_link",
             "meeting_booking_link", "booking_link", "appointment_link"],
        )
    if not scheduling_link:
        scheduling_link = _safe_get_existing_field_value(
            "Nexus Settings", None,
            ["meeting_scheduling_link", "calendly_link", "calendly_url",
             "meeting_booking_link", "booking_link", "appointment_link"],
        )
    return scheduling_link


def _build_meeting_booking_response(conversation, scheduling_link):
    if not scheduling_link:
        return _handle_create_consultancy_request(conversation)
    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": (
            f"Your email has been verified. You can now choose a suitable time to meet with a "
            f"{REP_LABEL} using the booking link below.\n\n{scheduling_link}\n\n"
            "Thank you for your time — we look forward to speaking with you!\n\n"
            "If you would like to discuss another product, please refresh this page to start a new chat."
        ),
        "confidence": 1.0,
        "sources": [], "citations": [], "retrieval_result": {}, "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": {
            "type": "meeting_booking",
            "status": "ready",
            "title": "Book a Demo / Consultation",
            "button_label": "Book a Meeting",
            "description": f"Choose a suitable time with a {REP_LABEL}.",
            "booking_url": scheduling_link,
            "url": scheduling_link,
        },
        "booking_url": scheduling_link,
    }


def _handle_show_meeting_booking_card(conversation, accumulated_discovery=None):
    scheduling_link = _resolve_meeting_booking_link(conversation)
    _companion_flow_debug("BOOKING LINK CHECK", {
        "conversation": getattr(conversation, "name", None),
        "assigned_agent": _get_conversation_assigned_agent(conversation),
        "scheduling_link_found": bool(scheduling_link),
    })
    return _build_meeting_booking_response(conversation, scheduling_link)


def _handle_create_consultancy_request(conversation, accumulated_discovery=None):
    try:
        enquiry_name = getattr(conversation, "companion_enquiry", None)
        if enquiry_name:
            frappe.db.set_value(
                "Nexus Companion Enquiry", enquiry_name,
                "recommended_next_step", "consultancy_request", update_modified=False,
            )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: consultancy update failed")
    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": (
            f"Thanks. I've saved your request for a {REP_LABEL}. "
            "They can review your note and follow up using your verified email."
        ),
        "confidence": 1.0,
        "sources": [], "citations": [], "retrieval_result": {}, "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": {
            "type": "consultancy_request",
            "status": "created",
            "title": "Consultation request saved",
            "message": f"A {REP_LABEL} will follow up using the visitor's verified email.",
        },
    }


# ---------------------------------------------------------------------------
# Representative-note step  (copied verbatim)
# ---------------------------------------------------------------------------

def _is_note_ack_only(visitor_message):
    text = str(visitor_message or "").strip().lower()
    return text in {"yes", "y", "sure", "ok", "okay", "yep", "yeah", "alright", "go ahead", "proceed"}


def _is_skip_note(visitor_message):
    text = str(visitor_message or "").strip().lower()
    return text in {"skip", "no", "no thanks", "no thank you", "nope", "pass", "not now"} or "skip" in text


def _identity_verified_system_message(message):
    msg = (message or "").lower().strip()
    if not msg:
        return False
    return (
        "identity verified" in msg
        or "preparing your booking" in msg
        or "verification completed" in msg
        or msg in {"verified", "email verified"}
    )


def _handle_verified_representative_note_message(conversation, visitor_message, accumulated_discovery):
    if _is_note_ack_only(visitor_message):
        return {
            "status": "success",
            "access_status": "intent_handled",
            "answer": (
                'Sure. Please type the note or question you want the specialist to see, '
                'or type "skip" to proceed without one.'
            ),
            "confidence": 1.0, "sources": [], "citations": [], "retrieval_result": {},
            "fallback_used": 0, "chat_mode": "controlled_companion_direct",
            "companion_controller": True, "conversion_action": None,
            "pending_action": "collect_representative_note",
        }
    note_value = "skipped" if _is_skip_note(visitor_message) else visitor_message[:500]
    update_enquiry(
        conversation,
        {"discovery_facts": [{
            "context_area": "general_business",
            "fact_type": "representative_note_collected",
            "fact_value": note_value,
            "source_message": visitor_message,
        }]},
        signal=None,
    )
    _clear_companion_pending_action(conversation)
    return _handle_show_meeting_booking_card(conversation, accumulated_discovery)


# ---------------------------------------------------------------------------
# Product catalogue + fit matching  (NEW)
# ---------------------------------------------------------------------------

def _load_products(conversation):
    """Enabled DIGITZ Prime products for this conversation's chat_category + tenant."""
    chat_category = getattr(conversation, "chat_category", None)
    tenant = getattr(conversation, "tenant", None)
    filters = {"enabled": 1}
    if chat_category:
        filters["chat_category"] = chat_category
    elif tenant:
        filters["tenant"] = tenant
    else:
        return []
    try:
        return frappe.get_all(
            "Nexus Companion Product",
            filters=filters,
            fields=["name", "product_name", "category", "description", "features",
                    "benefits", "challenges_solved", "typical_outcomes", "next_step"],
            order_by="creation asc",
            limit_page_length=20,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: load products failed")
        return []


import re as _re

# Very common words carry no product signal — ignore them when matching so short
# generic tokens don't inflate the fit score across every product.
_STOPWORDS = {
    "with", "that", "this", "your", "from", "have", "need", "want", "help", "using",
    "used", "some", "them", "they", "will", "would", "about", "into", "when", "what",
    "which", "there", "their", "been", "were", "also", "just", "like", "more", "most",
    "over", "than", "then", "make", "made", "does", "doing", "much", "many", "very",
    "business", "company", "system", "systems", "software", "manage", "managing",
}


def _tokenize(text):
    """Lowercase alphanumeric tokens (split on any non-word char, incl. - and _),
    length > 3, minus stopwords."""
    return {
        t for t in _re.split(r"[^a-z0-9]+", str(text or "").lower())
        if len(t) > 3 and t not in _STOPWORDS
    }


def _discovery_text(discovery):
    parts = []
    d = discovery or {}
    for key in ("current_challenges", "goals", "industry", "business_type", "existing_systems"):
        if d.get(key):
            parts.append(str(d.get(key)))
    for fact in _get_discovery_facts(d):
        # Both the stated value and its domain (context_area) help route to a product.
        if fact.get("fact_value"):
            parts.append(str(fact.get("fact_value")))
        if fact.get("context_area"):
            parts.append(str(fact.get("context_area")))
    return " ".join(parts)


def _match_products(discovery, products):
    """Rank products by keyword overlap between the visitor's stated needs and each
    product's challenges_solved / category / name. Returns products sorted best-first
    with a fit_score. Keyword-based so it never fails on an LLM error."""
    if not products:
        return []
    need_tokens = _tokenize(_discovery_text(discovery))
    if not need_tokens:
        return [dict(p, fit_score=0) for p in products]

    ranked = []
    for p in products:
        haystack = " ".join(str(p.get(k) or "") for k in
                            ("challenges_solved", "category", "product_name", "benefits"))
        ranked.append(dict(p, fit_score=len(_tokenize(haystack) & need_tokens)))
    ranked.sort(key=lambda x: x["fit_score"], reverse=True)
    return ranked


def _build_product_menu(products):
    if not products:
        return ""
    return "\n".join(f"- **{p.get('product_name')}**" for p in products if p.get("product_name"))


# ---------------------------------------------------------------------------
# Multi-product catalogue summary  (mirrors business_companion's playbook
# capability summary — rendered deterministically from a Playbook child table)
# ---------------------------------------------------------------------------

def _get_playbook(conversation, agent=None):
    """Resolve the enabled Nexus Companion Playbook for this conversation:
    the agent's companion_playbook first, then the tenant's enabled/default playbook."""
    playbook_name = ""
    if agent is not None:
        playbook_name = (getattr(agent, "companion_playbook", None) or "").strip()

    if not playbook_name:
        agent_name = _get_conversation_assigned_agent(conversation)
        if agent_name:
            playbook_name = (
                frappe.db.get_value("Nexus AI Agent Profile", agent_name, "companion_playbook") or ""
            ).strip()

    if not playbook_name:
        tenant = getattr(conversation, "tenant", None)
        if tenant:
            playbook_name = (
                frappe.db.get_value(
                    "Nexus Companion Playbook",
                    {"tenant": tenant, "enabled": 1, "is_default": 1}, "name",
                )
                or frappe.db.get_value(
                    "Nexus Companion Playbook", {"tenant": tenant, "enabled": 1}, "name"
                )
                or ""
            )

    if not playbook_name:
        return None
    try:
        playbook = frappe.get_doc("Nexus Companion Playbook", playbook_name)
        if not int(getattr(playbook, "enabled", 0) or 0):
            return None
        return playbook
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: playbook resolution failed")
        return None


def _get_playbook_product_items(playbook):
    """Enabled product rows with a display title, in configured order."""
    if not playbook:
        return []
    return [
        row for row in (playbook.get("product_items") or [])
        if int(getattr(row, "enabled", 0) or 0)
        and (getattr(row, "display_title", "") or "").strip()
    ]


def _build_product_catalogue_summary(playbook, ranked=None):
    """Deterministic multi-product summary rendered from the playbook's product_items —
    the product analogue of _build_playbook_capability_summary. No LLM, so the catalogue
    is identical every conversation and editable by admins on the Playbook. All enabled
    rows are shown, ordered best-fit first using the _match_products scores when available."""
    items = _get_playbook_product_items(playbook)
    if not items:
        return None

    heading = (playbook.get("capability_summary_heading") or "DIGITZ Prime Products").strip()

    # Fit lookup from the ranked _match_products output, keyed by product name and title.
    fit_by_name, fit_by_title = {}, {}
    for p in (ranked or []):
        if p.get("name"):
            fit_by_name[p["name"]] = p.get("fit_score", 0)
        if p.get("product_name"):
            fit_by_title[str(p["product_name"]).strip().lower()] = p.get("fit_score", 0)

    def _row_fit(row):
        prod = (getattr(row, "product", "") or "").strip()
        if prod and prod in fit_by_name:
            return fit_by_name[prod]
        return fit_by_title.get((getattr(row, "display_title", "") or "").strip().lower(), 0)

    # Best-fit first; configured order (idx) breaks ties.
    ordered = sorted(enumerate(items), key=lambda t: (-_row_fit(t[1]), t[0]))

    bullet_lines = []
    for _idx, row in ordered:
        title = (row.display_title or "").strip()
        desc = (getattr(row, "short_description", "") or "").strip()
        bullet_lines.append(f"- **{title}** — {desc}" if desc else f"- **{title}**")

    answer = (
        f"**{heading}:**\n" + "\n".join(bullet_lines) + "\n\n"
        "Which of these fits what you're working on — or tell me the challenge you're "
        "trying to solve and I'll point you to the right one."
    )
    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": answer,
        "confidence": 1.0,
        "sources": [], "citations": [], "retrieval_result": {}, "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": None,
        "product_catalogue_presented": True,
        "product_catalogue_source": "playbook",
        "pending_action": "select_product_area",
    }


def _present_product_fit_response(top_product, challenge, products):
    """Deterministic, admin-authored product presentation (grounded in the product
    record, no LLM hallucination), ending with a demo/consultation drive question."""
    name = top_product.get("product_name") or "this product"
    desc = (top_product.get("description") or "").strip()
    benefits = (top_product.get("benefits") or top_product.get("features") or "").strip()

    parts = []
    if challenge:
        parts.append(f"Based on what you've shared about {challenge}, **{name}** looks like the closest fit.")
    else:
        parts.append(f"**{name}** looks like a strong fit for your requirement.")
    if desc:
        parts.append(_preview_text(desc, 400))
    if benefits:
        bullet_lines = [
            f"- {ln.strip().lstrip('-').strip()}"
            for ln in benefits.replace("•", "\n").split("\n")
            if ln.strip()
        ][:4]
        if bullet_lines:
            parts.append("Here's how it helps:\n" + "\n".join(bullet_lines))
    parts.append(
        f"Would you like a quick walkthrough of **{name}** with a {REP_LABEL}, "
        "or should I tell you more about how it fits your setup first?"
    )
    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": "\n\n".join(parts),
        "confidence": 1.0,
        "sources": [], "citations": [], "retrieval_result": {}, "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": None,
        "matched_product": top_product.get("name"),
        "product_fit_presented": True,
    }


def _persist_product_fit(conversation, ranked):
    """Store the ranked fit on the enquiry (product_fit_json + recommended_next_step)."""
    try:
        enquiry_name = getattr(conversation, "companion_enquiry", None)
        if not enquiry_name or not ranked:
            return
        payload = [
            {"product": p.get("name"), "product_name": p.get("product_name"),
             "fit_score": p.get("fit_score", 0)}
            for p in ranked[:5]
        ]
        updates = {"product_fit_json": json.dumps(payload, default=str)}
        top_next_step = (ranked[0].get("next_step") or "").strip()
        if top_next_step:
            updates["recommended_next_step"] = top_next_step
        frappe.db.set_value("Nexus Companion Enquiry", enquiry_name, updates, update_modified=False)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: persist product fit failed")


# ---------------------------------------------------------------------------
# Steering  (product variant)
# ---------------------------------------------------------------------------

def _decide_steering(conversation, visitor_message, current_milestone, signal,
                     discovery, external_intent, pending_action, products, ranked):
    """Product-enquiry steering. Booking/verification/note stages are handled earlier
    in handle_companion_turn, so this focuses on the discovery -> product-fit -> demo arc."""
    ext = (external_intent or {}).get("intent") or "unknown"
    sig = (signal or {}).get("signal_type") or "CURIOUS"

    def _d(decision, **extra):
        base = {
            "decision": decision,
            "visitor_external_intent": ext,
            "external_intent_confidence": (external_intent or {}).get("confidence"),
            "signal_type": sig,
            "knowledge_needed": False,
            "grounding_mode": "controller_only",
        }
        base.update(extra)
        return base

    has_fit = bool(ranked and ranked[0].get("fit_score", 0) > 0)

    # Human handoff
    if ext == "human_request" or sig == "REQUESTING_HUMAN":
        return _d("offer_escalation")

    # Ready to move forward / booking intent -> demo confirmation
    if ext in {"demo_request", "demo_interest", "demo_confirmation"} or is_conversion_signal(sig):
        return _d("confirm_demo_request", milestone_policy="conversion_preparation")

    # Explicit product / fit / capability questions -> present fit or menu
    if ext in {"product_question", "product_fit_question", "product_capability_question",
               "module_interest", "integration_question", "technical_how_it_works_question"}:
        if has_fit:
            return _d("present_product_fit", milestone_policy="product_fit_check",
                      knowledge_needed=True, grounding_mode="nexus_knowledge_only")
        if products:
            return _d("present_product_catalogue", milestone_policy="product_menu")
        return _d("answer_product_clarification", knowledge_needed=True,
                  grounding_mode="nexus_knowledge_only")

    if ext == "pricing_question":
        return _d("answer_product_clarification", milestone_policy="next_step_guidance",
                  knowledge_needed=True, grounding_mode="nexus_knowledge_or_policy")

    # Milestone-driven discovery until solution_mapping, then present matched product.
    if current_milestone in ("onboarding_business", "business_discovery", "pain_discovery"):
        if current_milestone == "pain_discovery" and has_fit:
            return _d("present_product_fit", milestone_policy="solution_mapping",
                      knowledge_needed=True, grounding_mode="nexus_knowledge_only")
        return _d("continue_milestone", milestone_policy="pain_discovery",
                  knowledge_needed=True, grounding_mode="nexus_knowledge_or_policy")

    if current_milestone == "solution_mapping":
        if has_fit:
            return _d("present_product_fit", milestone_policy="solution_mapping",
                      knowledge_needed=True, grounding_mode="nexus_knowledge_only")
        return _d("present_product_catalogue", milestone_policy="product_menu")

    if current_milestone == "evidence_building":
        return _d("answer_product_clarification", milestone_policy="product_explanation",
                  knowledge_needed=True, grounding_mode="nexus_knowledge_only")

    return _d("normal_companion", knowledge_needed=True, grounding_mode="nexus_knowledge_or_policy")


def _build_controller_plan(core_payload, conversation, visitor_message, steering, current_milestone):
    plan = dict(core_payload)
    plan["query"] = visitor_message
    plan["original_query"] = visitor_message
    plan["conversation_name"] = conversation.name
    plan["mode"] = "controlled_companion"
    plan["current_milestone"] = current_milestone
    plan["steering_decision"] = steering.get("decision")
    plan["knowledge_needed"] = bool(steering.get("knowledge_needed"))
    plan["grounding_mode"] = steering.get("grounding_mode") or "controller_only"
    plan["allowed_tools"] = ["search_knowledge"] if steering.get("knowledge_needed") else []
    plan["allow_conversion_action"] = False
    plan["max_tool_calls"] = 1
    plan["knowledge_query"] = visitor_message
    return plan


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def handle_companion_turn(conversation, agent, payload, core_payload):
    """Controller-led DIGITZ PRIME product-enquiry runtime (Nexy persona)."""
    from digitz_ai_nexus.engine.chat_agent_loop import run_controlled_companion_loop

    visitor_message = payload.get("message") or core_payload.get("query") or ""
    conversation_context = core_payload.get("conversation_context") or ""
    current_milestone = _get_current_milestone(conversation)

    stored_pending = _get_companion_pending_action(conversation)
    payload_pending = (
        payload.get("pending_action")
        or payload.get("companion_pending_action")
        or core_payload.get("pending_action")
        or ""
    ).strip()
    pending_action = stored_pending or payload_pending

    _companion_flow_debug("01 TURN START", {
        "conversation": getattr(conversation, "name", None),
        "visitor_message": visitor_message,
        "current_milestone": current_milestone,
        "pending_action": pending_action,
    })

    get_or_create_enquiry(conversation)

    signal = classify_signal(visitor_message, conversation_context)

    try:
        external_intent = classify_external_intent(
            visitor_message=visitor_message,
            current_milestone=current_milestone,
            conversation_context=conversation_context,
            pending_action=pending_action,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: intent classification failed")
        external_intent = {"intent": "unknown", "confidence": 0}

    discovery_delta = _extract_discovery_data(visitor_message, current_milestone, conversation)
    accumulated_discovery = update_enquiry(
        conversation=conversation, discovery_delta=discovery_delta, signal=signal
    ) or {}

    # ── Identity-verification handoff (frontend verification dialog callback) ──
    idv_token = (
        payload.get("identity_verification_challenge")
        or payload.get("identity_verification_token")
        or payload.get("challenge_token")
        or core_payload.get("identity_verification_challenge")
        or core_payload.get("challenge_token")
        or ""
    ).strip()

    if idv_token and pending_action in {
        "collect_email_for_consultancy", "verify_email_for_consultancy",
        "collect_email_for_appointment", "verify_email_for_appointment",
        "collect_representative_note",
    }:
        try:
            from digitz_ai_nexus_live.services.identity_verification import get_verified_challenge
            idv = get_verified_challenge(
                challenge_token=idv_token,
                chat_category=getattr(conversation, "chat_category", None),
            )
            if idv:
                verified_ctx = {"email": idv.email, "verified_via": "idv_challenge"}
                frappe.db.set_value(
                    "Nexus Live Conversation", conversation.name,
                    {
                        "visitor_email": idv.email,
                        "companion_email_verified": 1,
                        "companion_pending_action": "collect_representative_note",
                        "companion_pending_context_json": json.dumps(verified_ctx, default=str),
                    },
                    update_modified=False,
                )
                conversation.visitor_email = idv.email
                conversation.companion_email_verified = 1
                pending_action = "collect_representative_note"
                _set_companion_pending_action(conversation, "collect_representative_note", verified_ctx)
                frappe.db.commit()
                if _identity_verified_system_message(visitor_message):
                    return {
                        "status": "success",
                        "access_status": "intent_handled",
                        "answer": (
                            f"Before I proceed, would you like to add a note or question for the "
                            f"{REP_LABEL}? This helps them prepare. You can also type \"skip\"."
                        ),
                        "confidence": 1.0, "sources": [], "citations": [],
                        "retrieval_result": {}, "fallback_used": 0,
                        "chat_mode": "controlled_companion_direct",
                        "companion_controller": True, "conversion_action": None,
                        "verification_stage": "verified",
                        "pending_action": "collect_representative_note",
                        "companion_email_verified": True,
                    }
                return _handle_verified_representative_note_message(
                    conversation, visitor_message, accumulated_discovery
                )
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Prime Companion: challenge verify failed")

    # ── Verified representative-note stage ──
    if pending_action == "collect_representative_note" and _is_booking_email_verified(conversation):
        return _handle_verified_representative_note_message(
            conversation, visitor_message, accumulated_discovery
        )

    advance_journey_stage_from_signal(conversation, signal.get("signal_type", "CURIOUS"))
    _publish_progress_update(conversation)

    # ── Product fit ranking (drives presentation) ──
    products = _load_products(conversation)
    ranked = _match_products(accumulated_discovery, products)
    if ranked:
        _persist_product_fit(conversation, ranked)

    steering = _decide_steering(
        conversation=conversation,
        visitor_message=visitor_message,
        current_milestone=current_milestone,
        signal=signal,
        discovery=accumulated_discovery,
        external_intent=external_intent,
        pending_action=pending_action,
        products=products,
        ranked=ranked,
    )

    _companion_flow_debug("04 STEERING", {
        "decision": steering.get("decision"),
        "external_intent": external_intent,
        "signal": signal.get("signal_type"),
        "milestone": current_milestone,
        "top_product": (ranked[0].get("product_name") if ranked else None),
        "top_fit": (ranked[0].get("fit_score") if ranked else None),
    })

    decision = steering.get("decision")

    # ── Deterministic, controller-owned decisions ──
    if decision == "offer_escalation":
        return {
            "status": "success",
            "access_status": "intent_handled",
            "answer": (
                f"Of course — I can connect you with a {REP_LABEL}. "
                "Could you share your email so they can follow up?"
            ),
            "confidence": 1.0, "sources": [], "citations": [], "retrieval_result": {},
            "fallback_used": 0, "chat_mode": "controlled_companion_direct",
            "companion_controller": True, "conversion_action": None,
            "user_requested_human": True, "intent_action": "escalate",
        }

    if decision == "show_meeting_booking_card":
        _clear_companion_pending_action(conversation)
        return _handle_show_meeting_booking_card(conversation, accumulated_discovery)

    if decision == "confirm_demo_request":
        if _is_booking_email_verified(conversation):
            _clear_companion_pending_action(conversation)
            return _handle_show_meeting_booking_card(conversation, accumulated_discovery)
        response = {
            "status": "success",
            "access_status": "intent_handled",
            "answer": (
                "Great — a short walkthrough is the best next step. "
                "Please share your email so I can verify it before booking the session."
            ),
            "confidence": 1.0, "sources": [], "citations": [], "retrieval_result": {},
            "fallback_used": 0, "chat_mode": "controlled_companion_direct",
            "companion_controller": True, "conversion_action": None,
        }
        _set_companion_pending_action(conversation, "collect_email_for_consultancy",
                                      {"decision": "confirm_demo_request"})
        _set_milestone(conversation, "demo_arrangement")
        return _decorate_email_collection_response(response, conversation)

    if decision == "present_product_fit" and ranked:
        top = ranked[0]
        challenge = (accumulated_discovery.get("current_challenges") or "").strip()
        _set_milestone(conversation, "solution_mapping")
        _set_companion_pending_action(conversation, "confirm_product_interest",
                                      {"product": top.get("name")})
        return _present_product_fit_response(top, challenge, products)

    if decision in ("present_product_catalogue", "present_product_menu"):
        _set_companion_pending_action(conversation, "select_product_area", {})
        # Preferred: the deterministic multi-product summary from the Playbook's
        # product_items child table (admin-authored, rendered directly).
        playbook = _get_playbook(conversation, agent)
        catalogue = _build_product_catalogue_summary(playbook, ranked)
        if catalogue:
            return catalogue
        # Fallback: plain names-only menu when no product_items are configured.
        menu = _build_product_menu(products)
        return {
            "status": "success",
            "access_status": "intent_handled",
            "answer": (
                "Here are the DIGITZ Prime products I can help you explore:\n\n"
                f"{menu}\n\n"
                "Which one fits what you're looking for — or tell me the challenge you're "
                "trying to solve and I'll point you to the right one."
            ),
            "confidence": 1.0, "sources": [], "citations": [], "retrieval_result": {},
            "fallback_used": 0, "chat_mode": "controlled_companion_direct",
            "companion_controller": True, "conversion_action": None,
            "pending_action": "select_product_area",
        }

    # ── Knowledge-grounded LLM decisions (continue_milestone / clarification / normal) ──
    controller_plan = _build_controller_plan(
        core_payload, conversation, visitor_message, steering, current_milestone
    )
    loop_payload = dict(core_payload)
    loop_payload["query"] = visitor_message
    loop_payload["conversation_name"] = conversation.name

    try:
        response = run_controlled_companion_loop(payload=loop_payload, controller_plan=controller_plan)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Prime Companion: controlled loop failed")
        response = {}

    if not isinstance(response, dict):
        response = {}

    response["companion_controller"] = True
    response.setdefault("conversion_action", None)

    _maybe_advance_milestone(conversation)

    _companion_flow_debug("08 FINAL", {
        "decision": decision,
        "answer": _preview_text(response.get("answer"), 500),
        "access_status": response.get("access_status"),
    })
    return response
