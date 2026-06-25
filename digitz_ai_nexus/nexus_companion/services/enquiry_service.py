"""
Enquiry service — creates, updates, and scores Nexus Companion Enquiry records.

An Enquiry is the full sales cycle record. It is created the moment a companion-
mode conversation begins and tracks every signal, discovery datum, and stage
transition through to conversion or exit.

Stage advancement is driven by LLM-classified visitor signals, not message count
or score thresholds alone — see advance_journey_stage_from_signal().
"""

import json
from frappe.utils import now_datetime

import frappe

from digitz_ai_nexus.nexus_companion.services.persona_matching_service import match_persona


# ── Stage definitions ──────────────────────────────────────────────────────────

_STAGE_ORDER = [
    "ARRIVED",
    "GREETING",
    "DISCOVERY",
    "ENGAGED",
    "PRESENTING",
    "OBJECTION_HANDLING",
    "INTERESTED",
    "CONVERTING",
    "CONVERTED",
    "DECLINED",
    "ESCALATED",
]

# Terminal stages — once reached, the journey does not advance further.
_TERMINAL_STAGES = {"CONVERTED", "DECLINED", "ESCALATED"}

# Minimum score floor for score-based fallback advancement (used as a safety net
# when signal classification is unavailable — not the primary mechanism).
_STAGE_SCORE_FLOOR = {
    "ARRIVED": 0,
    "GREETING": 5,
    "DISCOVERY": 15,
    "ENGAGED": 30,
    "PRESENTING": 40,
    "OBJECTION_HANDLING": 40,
    "INTERESTED": 55,
    "CONVERTING": 70,
    "CONVERTED": 90,
    "DECLINED": 0,
    "ESCALATED": 80,
}

# Signal → minimum stage the signal implies
# None means no automatic stage change (stage stays; LLM handles it contextually)
_SIGNAL_STAGE_MAP = {
    "SHARING_CONTEXT": "DISCOVERY",
    "ANSWERING_QUESTION": "DISCOVERY",
    "CURIOUS": "DISCOVERY",
    "EVALUATING": "ENGAGED",
    "INTERESTED": "INTERESTED",
    "READY": "CONVERTING",
    "ASKING_PRICE": "CONVERTING",
    "ASKING_NEXT_STEP": "INTERESTED",
    "OBJECTING": None,        # handled contextually below
    "HESITATING": None,
    "DISENGAGING": None,
    "DEFLECTING": None,
    "REQUESTING_HUMAN": "ESCALATED",
    "DECLINING": "DECLINED",
}


# ── Public API ─────────────────────────────────────────────────────────────────

def get_or_create_enquiry(conversation) -> str:
    """Return the Enquiry name linked to this conversation, creating it if needed.

    Stamps visitor identity fields from the conversation when creating.
    """
    if conversation.companion_enquiry:
        return conversation.companion_enquiry

    # Resolve web_session from conversation if available
    web_session = _resolve_web_session(conversation)

    # Resolved verified email from the conversation (set by identity verification flow)
    visitor_email = getattr(conversation, "visitor_email", None) or None
    verification_status = "OTP Verified" if visitor_email else "Unverified"

    enquiry = frappe.new_doc("Nexus Companion Enquiry")
    enquiry.conversation = conversation.name
    enquiry.visitor = getattr(conversation, "web_visitor", None) or None
    enquiry.visitor_email = visitor_email
    enquiry.verification_status = verification_status
    enquiry.web_session = web_session
    enquiry.tenant = getattr(conversation, "tenant", None) or _resolve_tenant(conversation)
    enquiry.enquiry_stage = conversation.companion_journey_stage or "ARRIVED"
    enquiry.enquiry_score = 0
    enquiry.created_on = now_datetime()
    enquiry.discovery_data = "{}"
    enquiry.signal_log = "[]"
    enquiry.insert(ignore_permissions=True)

    conversation.db_set("companion_enquiry", enquiry.name, update_modified=False)
    return enquiry.name


def update_enquiry(conversation, discovery_delta: dict, signal: dict | None = None) -> None:
    """
    Merge new discovery data, record the signal, re-run persona matching and scoring.

    Args:
        conversation: Nexus Live Conversation doc (reloaded)
        discovery_delta: Dict of {field: value} pairs to merge into discovery_data
        signal: Dict from signal_classifier.classify_signal() — optional
    """
    enquiry_name = get_or_create_enquiry(conversation)
    enquiry = frappe.get_doc("Nexus Companion Enquiry", enquiry_name)
    tenant = enquiry.tenant

    # Stamp visitor email if not yet recorded (email may have been verified this turn)
    if not enquiry.visitor_email:
        live_email = getattr(conversation, "visitor_email", None)
        if live_email:
            enquiry.visitor_email = live_email
            enquiry.verification_status = "OTP Verified"

    # Merge discovery data
    try:
        existing = json.loads(enquiry.discovery_data or "{}")
    except Exception:
        existing = {}
    existing.update({k: v for k, v in (discovery_delta or {}).items() if v})
    enquiry.discovery_data = json.dumps(existing)

    # Record the signal
    if signal:
        _append_signal_log(enquiry, signal)
        enquiry.stage_signal = signal.get("signal_type", "")

        # Flag escalation_recommended when visitor has been consistently disengaging
        consecutive = _count_consecutive_resistance_signals(enquiry.signal_log or "[]")
        if consecutive >= 3 and not enquiry.escalation_recommended:
            enquiry.escalation_recommended = 1

    # Re-run persona matching
    match = match_persona(existing, tenant)
    if match["persona"]:
        enquiry.matched_persona = match["persona"]
        enquiry.persona_confidence = match["confidence"]
        conversation.db_set("companion_persona", match["persona"], update_modified=False)
        conversation.db_set("companion_persona_confidence", match["confidence"], update_modified=False)

    # Recalculate score
    enquiry.enquiry_score = calculate_score(existing, match["confidence"])

    # Determine recommended next step
    enquiry.recommended_next_step = _recommended_next_step(enquiry.enquiry_score)

    # Resolve and record recommended products from the chat category
    _resolve_recommended_products(enquiry, conversation)

    enquiry.save(ignore_permissions=True)


def advance_journey_stage_from_signal(conversation, signal_type: str) -> str:
    """
    Advance the companion journey stage based on a classified visitor signal.

    This is the primary stage machine — signal-driven, not score-driven.
    Falls back to score-based advancement when signal is ambiguous.

    Returns the new (or unchanged) stage name.
    """
    current = conversation.companion_journey_stage or "ARRIVED"

    if current in _TERMINAL_STAGES:
        return current

    # ── Hard-coded signal transitions ─────────────────────────────────────────

    if signal_type == "REQUESTING_HUMAN":
        _set_stage(conversation, "ESCALATED")
        _promote_to_nexus_contact(conversation, "ESCALATED")
        return "ESCALATED"

    if signal_type == "DECLINING":
        return _set_stage(conversation, "DECLINED")

    # OBJECTING while PRESENTING → OBJECTION_HANDLING
    if signal_type == "OBJECTING" and current == "PRESENTING":
        return _set_stage(conversation, "OBJECTION_HANDLING")

    # Positive signals while in OBJECTION_HANDLING → back to PRESENTING
    if current == "OBJECTION_HANDLING" and signal_type in (
        "INTERESTED", "EVALUATING", "ASKING_NEXT_STEP", "CURIOUS"
    ):
        return _set_stage(conversation, "PRESENTING")

    # First message from an ARRIVED visitor → GREETING
    if current == "ARRIVED":
        return _set_stage(conversation, "GREETING")

    # ── Signal map advancement ────────────────────────────────────────────────

    min_stage = _SIGNAL_STAGE_MAP.get(signal_type)
    if not min_stage:
        return current  # ambiguous signal — keep current stage

    current_idx = _stage_idx(current)
    target_idx = _stage_idx(min_stage)

    if target_idx > current_idx:
        return _set_stage(conversation, min_stage)

    return current


def advance_journey_stage(conversation, enquiry_score: int = None) -> str:
    """
    Score-based fallback stage advancement.

    Used when signal classification is unavailable (e.g., the LLM call failed)
    or as a secondary guard to ensure score-based promotion still occurs.
    """
    current = conversation.companion_journey_stage or "ARRIVED"
    if current in _TERMINAL_STAGES:
        return current

    if enquiry_score is None:
        if conversation.companion_enquiry:
            enquiry_score = frappe.db.get_value(
                "Nexus Companion Enquiry", conversation.companion_enquiry, "enquiry_score"
            ) or 0
        else:
            enquiry_score = 0

    current_idx = _stage_idx(current)
    next_stage = current

    # Walk forward through stages (excluding terminal stages)
    for stage in _STAGE_ORDER[current_idx + 1:]:
        if stage in _TERMINAL_STAGES:
            break
        floor = _STAGE_SCORE_FLOOR.get(stage, 100)
        if enquiry_score >= floor:
            next_stage = stage
        else:
            break

    if next_stage != current:
        _set_stage(conversation, next_stage)

    return next_stage


def calculate_score(discovery_data: dict, persona_confidence: float) -> int:
    """
    Compute a 0-100 composite enquiry score.

    Factors:
      - Discovery completeness  (up to 40 pts)
      - Persona confidence      (up to 30 pts)
      - Qualification signals   (up to 30 pts)
    """
    completeness = _discovery_completeness_score(discovery_data)      # 0-40
    persona_pts = min((persona_confidence or 0) * 0.30, 30)           # 0-30
    qualification_pts = _qualification_signal_score(discovery_data)   # 0-30
    return min(int(completeness + persona_pts + qualification_pts), 100)


def check_escalation_threshold(conversation, playbook=None) -> bool:
    """Return True if the enquiry score exceeds the playbook's escalation threshold."""
    if not conversation.companion_enquiry:
        return False

    score = frappe.db.get_value(
        "Nexus Companion Enquiry", conversation.companion_enquiry, "enquiry_score"
    ) or 0

    threshold = 70
    if playbook:
        t = frappe.db.get_value("Nexus Companion Playbook", playbook, "escalation_score_threshold")
        if t:
            threshold = int(t)

    return score >= threshold


def check_trigger_keywords(message: str, playbook: str) -> bool:
    """Return True if any playbook escalation trigger keyword appears in the message."""
    if not playbook:
        return False
    triggers_raw = frappe.db.get_value(
        "Nexus Companion Playbook", playbook, "escalation_triggers"
    ) or ""
    triggers = [t.strip().lower() for t in triggers_raw.splitlines() if t.strip()]
    msg_lower = message.lower()
    return any(trigger in msg_lower for trigger in triggers)


def mark_converted(conversation, product_name: str = None) -> None:
    """Mark the enquiry as CONVERTED and record the product if known."""
    if not conversation.companion_enquiry:
        return
    frappe.db.set_value("Nexus Companion Enquiry", conversation.companion_enquiry, {
        "enquiry_stage": "CONVERTED",
    })
    conversation.db_set("companion_journey_stage", "CONVERTED", update_modified=False)
    _promote_to_nexus_contact(conversation, "CONVERTED")


def _promote_to_nexus_contact(conversation, stage: str) -> None:
    """
    Auto-create a Nexus Contact from a companion enquiry when a visitor reaches
    CONVERTED or ESCALATED.  Idempotent — skips if a contact already exists for
    this visitor or email.
    """
    try:
        import frappe as _frappe

        tenant = getattr(conversation, "tenant", None)
        if not tenant:
            return

        visitor_name = getattr(conversation, "web_visitor", None)
        visitor_email = getattr(conversation, "visitor_email", None) or ""
        visitor_phone = getattr(conversation, "visitor_phone", None) or ""

        # Match by visitor link first
        if visitor_name and _frappe.db.exists("Nexus Contact", {"linked_visitor": visitor_name, "tenant": tenant}):
            _update_contact_stage(
                _frappe.db.get_value("Nexus Contact", {"linked_visitor": visitor_name, "tenant": tenant}, "name"),
                conversation, stage
            )
            return

        # Match by email
        if visitor_email and _frappe.db.exists("Nexus Contact", {"email": visitor_email, "tenant": tenant}):
            _update_contact_stage(
                _frappe.db.get_value("Nexus Contact", {"email": visitor_email, "tenant": tenant}, "name"),
                conversation, stage
            )
            return

        # Build display name from enquiry data
        discovery = {}
        if conversation.companion_enquiry:
            raw = _frappe.db.get_value("Nexus Companion Enquiry", conversation.companion_enquiry, "discovery_data") or "{}"
            try:
                discovery = __import__("json").loads(raw)
            except Exception:
                discovery = {}

        display_name = visitor_email or visitor_phone or "Unknown"

        enquiry_score = 0
        matched_persona = None
        persona_confidence = 0.0
        if conversation.companion_enquiry:
            eq = _frappe.db.get_value(
                "Nexus Companion Enquiry",
                conversation.companion_enquiry,
                ["enquiry_score", "matched_persona", "persona_confidence"],
                as_dict=True
            ) or {}
            enquiry_score = eq.get("enquiry_score") or 0
            matched_persona = eq.get("matched_persona")
            persona_confidence = eq.get("persona_confidence") or 0.0

        contact = _frappe.get_doc({
            "doctype": "Nexus Contact",
            "tenant": tenant,
            "display_name": display_name,
            "email": visitor_email,
            "phone": visitor_phone,
            "whatsapp_number": visitor_phone,
            "source": "Inbound Companion",
            "consent_status": "Opted In",
            "status": "Active",
            "linked_visitor": visitor_name,
            "matched_persona": matched_persona,
            "persona_confidence": persona_confidence,
            "last_enquiry_score": enquiry_score,
            "last_journey_stage": stage,
            "last_contact_date": _frappe.utils.now_datetime(),
            "total_conversations": 1,
        })
        contact.insert(ignore_permissions=True)
        _frappe.db.commit()

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Companion: auto-promote to Nexus Contact failed")


def _update_contact_stage(contact_name, conversation, stage):
    """Update an existing Nexus Contact's stage and score from the latest enquiry."""
    try:
        updates = {"last_journey_stage": stage, "last_contact_date": frappe.utils.now_datetime()}
        if conversation.companion_enquiry:
            eq = frappe.db.get_value(
                "Nexus Companion Enquiry",
                conversation.companion_enquiry,
                ["enquiry_score", "matched_persona", "persona_confidence"],
                as_dict=True,
            ) or {}
            if eq.get("enquiry_score"):
                updates["last_enquiry_score"] = eq["enquiry_score"]
            if eq.get("matched_persona"):
                updates["matched_persona"] = eq["matched_persona"]
            if eq.get("persona_confidence"):
                updates["persona_confidence"] = eq["persona_confidence"]
        frappe.db.set_value("Nexus Contact", contact_name, updates)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Companion: contact stage update failed")


# ── Internal helpers ───────────────────────────────────────────────────────────

_DISCOVERY_FIELDS = [
    "industry", "company_size", "team_size", "business_maturity",
    "current_challenges", "goals", "existing_systems", "budget_range",
    "timeline", "decision_maker",
]

_QUALIFICATION_SIGNALS = [
    "demo", "proposal", "pricing", "budget", "timeline", "decision",
    "purchase", "implement", "evaluate", "trial", "interested",
    "schedule", "meeting", "call", "next step",
]


def _stage_idx(stage: str) -> int:
    try:
        return _STAGE_ORDER.index(stage)
    except ValueError:
        return 0


def _set_stage(conversation, stage: str) -> str:
    """Write the new stage to the conversation and the linked enquiry."""
    conversation.db_set("companion_journey_stage", stage, update_modified=False)
    if conversation.companion_enquiry:
        frappe.db.set_value(
            "Nexus Companion Enquiry",
            conversation.companion_enquiry,
            "enquiry_stage",
            stage,
        )
    return stage


def _append_signal_log(enquiry, signal: dict) -> None:
    """Append one classified signal entry to the enquiry's signal_log JSON array."""
    try:
        log = json.loads(enquiry.signal_log or "[]")
    except Exception:
        log = []

    log.append({
        "signal_type": signal.get("signal_type"),
        "confidence": signal.get("confidence"),
        "reason": signal.get("reason"),
        "ts": str(now_datetime()),
    })

    # Cap at 50 entries to keep the field size manageable
    if len(log) > 50:
        log = log[-50:]

    enquiry.signal_log = json.dumps(log)


def _discovery_completeness_score(discovery_data: dict) -> float:
    filled = sum(1 for f in _DISCOVERY_FIELDS if discovery_data.get(f))
    return (filled / len(_DISCOVERY_FIELDS)) * 40


def _qualification_signal_score(discovery_data: dict) -> float:
    text = " ".join(str(v) for v in discovery_data.values() if v).lower()
    matched = sum(1 for sig in _QUALIFICATION_SIGNALS if sig in text)
    return min((matched / max(len(_QUALIFICATION_SIGNALS), 1)) * 60, 30)


def _recommended_next_step(score: int) -> str:
    if score >= 75:
        return "Direct Meeting"
    if score >= 60:
        return "Consultation Request"
    if score >= 40:
        return "Evaluation Request"
    return "Learn More"


def _resolve_tenant(conversation) -> str:
    channel = frappe.db.get_value("Nexus Live Conversation", conversation.name, "channel")
    if channel:
        return frappe.db.get_value("Nexus Live Channel", channel, "tenant") or ""
    return ""


def _resolve_web_session(conversation) -> str | None:
    """Return the web_session linked to this conversation, if any."""
    try:
        return frappe.db.get_value(
            "Nexus Live Conversation", conversation.name, "web_session"
        ) or None
    except Exception:
        return None


def _count_consecutive_resistance_signals(signal_log_json: str) -> int:
    """Count consecutive resistance signals from the end of the signal log."""
    _RESISTANCE = {"HESITATING", "DEFLECTING", "DISENGAGING", "OBJECTING"}
    try:
        log = json.loads(signal_log_json or "[]")
    except Exception:
        return 0
    count = 0
    for entry in reversed(log):
        if entry.get("signal_type") in _RESISTANCE:
            count += 1
        else:
            break
    return count


def _resolve_recommended_products(enquiry, conversation) -> None:
    """
    Populate enquiry.recommended_products from the Nexus Companion Products
    configured for the conversation's chat_category. Runs on every update_enquiry
    call so the list stays current as the visitor's profile clarifies.

    Products are matched by chat_category (exact) with a tenant safety filter.
    Existing rows are replaced only when the product list has changed to avoid
    unnecessary DB churn.
    """
    try:
        chat_category = getattr(conversation, "chat_category", None)
        if not chat_category:
            return

        tenant = enquiry.tenant
        products = frappe.get_all(
            "Nexus Companion Product",
            filters={"chat_category": chat_category, "tenant": tenant, "enabled": 1},
            fields=["name", "product_name", "conversion_threshold_score"],
            order_by="creation asc",
            limit_page_length=5,
        )
        if not products:
            return

        existing_names = {row.product for row in (enquiry.recommended_products or [])}
        new_names = {p.name for p in products}

        if existing_names == new_names:
            return

        enquiry.recommended_products = []
        score = enquiry.enquiry_score or 0
        for p in products:
            threshold = p.get("conversion_threshold_score") or 0
            fit = min(int(score * 1.1) if score >= threshold else int(score * 0.8), 100)
            enquiry.append("recommended_products", {
                "product": p.name,
                "product_name": p.product_name,
                "fit_score": fit,
            })
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Companion: _resolve_recommended_products failed")


# ── Conversion action ──────────────────────────────────────────────────────────

def get_conversion_action(conversation) -> dict | None:
    """
    Return a conversion action dict when the conversation is in CONVERTING stage
    and the top recommended product has a conversion mechanism configured.

    Called just before publish_chat_response() so the widget can render an
    inline CTA card alongside the AI answer.

    Returns None when:
    - Stage is not CONVERTING
    - No enquiry exists on the conversation
    - No recommended products on the enquiry
    - Product has no conversion_type configured

    Return shape:
    {
        "type":       str,   # conversion_type value
        "message":    str,   # conversion_message (Nexy's guide phrase)
        "url":        str,   # primary action URL (calendar / payment / form)
        "product":    str,   # product display name
        "post_action": str,  # post_conversion_action
    }
    """
    try:
        stage = frappe.db.get_value(
            "Nexus Live Conversation", conversation.name, "companion_journey_stage"
        )
        if stage != "CONVERTING":
            return None

        enquiry_name = frappe.db.get_value(
            "Nexus Live Conversation", conversation.name, "companion_enquiry"
        )
        if not enquiry_name:
            return None

        products = frappe.get_all(
            "Nexus Companion Enquiry Product",
            filters={"parent": enquiry_name},
            fields=["product", "product_name", "fit_score"],
            order_by="fit_score desc",
            limit=1,
        )
        if not products:
            return None

        product_doc = frappe.get_doc("Nexus Companion Product", products[0].product)
        if not product_doc.conversion_type:
            return None

        config = {}
        try:
            config = json.loads(product_doc.conversion_config or "{}")
        except Exception:
            pass

        url = (
            config.get("calendar_url")
            or config.get("payment_url")
            or config.get("form_url")
            or config.get("url")
            or ""
        )

        return {
            "type": product_doc.conversion_type,
            "message": product_doc.conversion_message or "",
            "url": url,
            "product": product_doc.product_name or products[0].product,
            "post_action": product_doc.post_conversion_action or "Continue Conversation",
        }
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Companion: get_conversion_action failed")
        return None
