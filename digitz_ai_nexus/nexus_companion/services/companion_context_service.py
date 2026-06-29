"""
Companion context service — assembles the full structured context block that is
injected into the AI system prompt on every companion-mode conversation turn.

Key design principle: this service gives the LLM a precise, directive context
(objective + situation + arsenal + rules) rather than a generic advisory persona.
The LLM IS the sales/conversion intelligence — this context is its brief.
"""

import json
import frappe

from digitz_ai_nexus.nexus_companion.services.reference_matching_service import get_relevant_references


# ── Strategy Engine constants ──────────────────────────────────────────────────

# Signals that indicate visitor resistance or disengagement
_RESISTANCE_SIGNALS = {"HESITATING", "DEFLECTING", "DISENGAGING", "OBJECTING"}

# Minimum priority fields to collect before advancing from DISCOVERY
_PRIORITY_DISCOVERY_FIELDS = ["industry", "company_size", "current_challenges", "goals"]

# All 10 discovery fields (mirrors enquiry_service._DISCOVERY_FIELDS)
_ALL_DISCOVERY_FIELDS = [
    "industry", "company_size", "team_size", "business_maturity",
    "current_challenges", "goals", "existing_systems", "budget_range",
    "timeline", "decision_maker",
]


# ── Stage × Engagement Mode directive matrix ───────────────────────────────────
# Each stage has three directives: PROGRESSING (default), RESISTANT, DISENGAGING.
# The LLM receives exactly one directive per turn based on computed engagement mode.

_STAGE_DIRECTIVES = {
    "ARRIVED": {
        "PROGRESSING": (
            "This visitor has just arrived. Warmly greet them. Ask one open question "
            "to understand what brought them here. Do not pitch anything yet."
        ),
        "RESISTANT": (
            "This visitor has just arrived but seems hesitant. Keep the greeting warm "
            "and low-pressure. Ask one simple, open question. Do not pitch."
        ),
        "DISENGAGING": (
            "This visitor arrived but is already disengaged. Give a brief, genuine "
            "greeting. Ask only 'What brought you here today?' — nothing more."
        ),
    },
    "GREETING": {
        "PROGRESSING": (
            "The visitor has just chosen to connect. Skip the platform introduction — "
            "do not describe what Nexus Orbit or Nexy is. Ask one direct, focused question: "
            "what does their business do, and what's the main challenge they want to solve? "
            "Be brief and genuine."
        ),
        "RESISTANT": (
            "The visitor seems hesitant. Shift from asking questions to briefly sharing "
            "what you help companies like theirs with — make it feel relevant, not like "
            "a pitch. Invite a reaction, not a direct answer."
        ),
        "DISENGAGING": (
            "The visitor appears disengaged this early. Acknowledge it gently: "
            "'I sense this might not be what you were looking for — am I off base?' "
            "Give them full permission to redirect. Do not push forward."
        ),
    },
    "DISCOVERY": {
        "PROGRESSING": (
            "You are in discovery. When the visitor shares context about themselves "
            "(their business, team size, industry, challenges), acknowledge it with a brief "
            "relevant insight — connect it to a pattern you see for businesses like theirs. "
            "Then ask ONE follow-up question to learn the next most important thing. "
            "Priority fields still needed: see DISCOVERY PROGRESS below. "
            "Do not ask multiple questions. Do not recommend solutions yet. "
            "If the visitor shares something like their industry or team size, do not ask "
            "them to repeat or clarify it — record it and move forward."
        ),
        "RESISTANT": (
            "The visitor is not engaging with direct questions. Pivot from questioning to "
            "insight-sharing — share a pattern you see with companies in their apparent "
            "situation and invite their reaction. Do not ask another discovery question yet."
        ),
        "DISENGAGING": (
            "Pause discovery entirely. Lead with the most compelling outcome you can offer "
            "for their apparent profile. No questions. No asks. Give them something worth "
            "staying for — one specific, concrete result."
        ),
    },
    "ENGAGED": {
        "PROGRESSING": (
            "You have a solid picture of their situation. Begin connecting their challenges "
            "to relevant solutions naturally — frame it as insight, not a pitch. "
            "Introduce the most relevant product or service in the context of their problem."
        ),
        "RESISTANT": (
            "The visitor is not engaging with the solution angle. Revisit their core stated "
            "challenge and confirm your understanding is correct before introducing solutions. "
            "Rebuild connection before continuing."
        ),
        "DISENGAGING": (
            "Stop introducing solutions. Share one specific outcome that companies with their "
            "profile have achieved. One sentence. No ask. No question. Let it land."
        ),
    },
    "PRESENTING": {
        "PROGRESSING": (
            "You are presenting a solution. Be specific about how it addresses their "
            "stated challenges. Surface a relevant customer story or outcome to build "
            "confidence. Invite questions. Listen for objections or interest signals."
        ),
        "RESISTANT": (
            "The current presentation approach is not landing. Acknowledge it directly — "
            "ask 'What would I need to show you for this to feel like a fit for you?' "
            "Stop presenting until they respond."
        ),
        "DISENGAGING": (
            "Stop the presentation. Offer to connect with a specialist or step back to "
            "a simpler format. Ask if there is a better way you can help them explore this."
        ),
    },
    "OBJECTION_HANDLING": {
        "PROGRESSING": (
            "The visitor has raised a concern. Acknowledge it genuinely — never dismiss it. "
            "Address it specifically using the objection responses below. After handling, "
            "bridge back to the value with a question or a different angle. "
            "Avoid repeating the same reframe twice."
        ),
        "RESISTANT": (
            "Multiple concerns are surfacing. Slow down — acknowledge that there are real "
            "questions here and that you want to address them properly. Ask which concern "
            "matters most to them right now. Handle one at a time."
        ),
        "DISENGAGING": (
            "The visitor is withdrawing from the objection discussion. Do not push further. "
            "Offer to share a brief written summary they can review at their own pace, or "
            "offer to connect them with a specialist who can address their concerns directly."
        ),
    },
    "INTERESTED": {
        "PROGRESSING": (
            "The visitor has signalled genuine interest. Reinforce the fit with a specific "
            "outcome or metric. Suggest a clear, low-friction next step that matches the "
            "available conversion mechanism. Make it easy to say yes."
        ),
        "RESISTANT": (
            "The visitor has shown interest but is pulling back. Revisit their core goal "
            "before pushing a next step. Ask what would make taking that step feel right "
            "for them right now. Rebuild connection first."
        ),
        "DISENGAGING": (
            "The visitor is at risk of dropping off despite earlier interest. Make a direct, "
            "honest ask — acknowledge the opportunity and ask if they would like to take a "
            "simple next step before the conversation closes."
        ),
    },
    "CONVERTING": {
        "PROGRESSING": (
            "This visitor is ready to take action. Guide them clearly and simply through "
            "the next step. Use the conversion prompt below if configured. "
            "Reduce all friction. One clear action — not a menu of options."
        ),
        "RESISTANT": (
            "The visitor is hesitating at the conversion point. Surface the remaining "
            "concern by asking 'Is there anything giving you pause before we take this "
            "next step?' Address it, then re-introduce the CTA once."
        ),
        "DISENGAGING": (
            "Offer a lower-commitment alternative — suggest a brief overview or a follow-up "
            "resource they can review before committing. Keep the door open without pressure."
        ),
    },
    "CONVERTED": {
        "PROGRESSING": (
            "The visitor has taken the next step. Confirm it warmly. Set expectations for "
            "what happens next. Offer a warm close or invite any final questions."
        ),
        "RESISTANT": (
            "The visitor has converted but seems uncertain. Reassure them warmly — confirm "
            "what happens next and what they can expect from your team. Be brief and clear."
        ),
        "DISENGAGING": (
            "The visitor has converted but is withdrawing. Give a warm, brief close. "
            "Confirm what happens next in one clear sentence. No further asks."
        ),
    },
    "DECLINED": {
        "PROGRESSING": (
            "The visitor has decided not to proceed at this time. Respect that fully. "
            "Leave the door open without pressure. Thank them for their time and invite "
            "them to return whenever the timing is right."
        ),
        "RESISTANT": (
            "The visitor has declined. Respect their decision completely. Give a brief, "
            "gracious close. Do not attempt to re-engage."
        ),
        "DISENGAGING": (
            "The visitor has declined. Close warmly and briefly. Make it easy to leave."
        ),
    },
    "ESCALATED": {
        "PROGRESSING": (
            "This conversation is being handed to a specialist. Wrap up your part helpfully. "
            "Confirm the handoff and reassure the visitor that they are in good hands."
        ),
        "RESISTANT": (
            "This conversation is being escalated. Reassure the visitor that their concerns "
            "will be addressed by the right person. Close your part warmly and briefly."
        ),
        "DISENGAGING": (
            "The visitor is being escalated. Keep your close brief and reassuring. "
            "Let them know a specialist will follow up soon."
        ),
    },
}


# ── Disengagement re-engagement arc ───────────────────────────────────────────
# When engagement_mode = DISENGAGING, this 3-step arc overrides the stage directive.
# Step is determined by counting consecutive resistance signals from the signal_log tail.

_DISENGAGEMENT_SEQUENCE = {
    1: (
        "ACKNOWLEDGMENT PIVOT — The visitor has been consistently deflecting or disengaging. "
        "Stop your current approach entirely. Calmly acknowledge the disconnect: say something "
        "like 'I get the sense this might not be what you were looking for — am I off base? "
        "No pressure at all.' Give them full permission to be honest. "
        "Do NOT ask a discovery question or push any agenda. Let them redirect."
    ),
    2: (
        "VALUE FLASH — The visitor is still disengaged. Share ONE compelling insight or "
        "real-world outcome that is genuinely relevant to their apparent situation. "
        "No ask. No question. No CTA. No follow-up request. Just give them something worth "
        "staying for. Example: 'Companies in your space typically achieve [outcome] within "
        "[timeframe] — without [common pain].' Then stop. Let it land."
    ),
    3: (
        "EXIT OFFER — The visitor has not re-engaged despite two attempts. Ask for their "
        "consent to connect with a specialist. Say something like: 'It sounds like speaking "
        "directly with one of our specialists might serve you better than I can right now. "
        "Would that be helpful? Just say yes and I will arrange it, or no problem at all if "
        "you would prefer to leave it here.' "
        "Do NOT call request_escalation this turn — offer first and wait for their response. "
        "If they say yes in their next message, you may then call request_escalation. "
        "If they say no, close warmly with no further asks."
    ),
}


# ── Strategy Engine helpers ────────────────────────────────────────────────────

def _compute_engagement_mode(signal_log_json: str) -> str:
    """Return PROGRESSING, RESISTANT, or DISENGAGING based on the last 5 signals."""
    try:
        log = json.loads(signal_log_json or "[]")
    except Exception:
        return "PROGRESSING"
    recent = [e.get("signal_type") for e in log[-5:] if e.get("signal_type")]
    resistance_count = sum(1 for s in recent if s in _RESISTANCE_SIGNALS)
    if resistance_count >= 4:
        return "DISENGAGING"
    if resistance_count >= 2:
        return "RESISTANT"
    return "PROGRESSING"


def _count_consecutive_disengaging(signal_log_json: str) -> int:
    """Count consecutive resistance signals from the END of the signal log."""
    try:
        log = json.loads(signal_log_json or "[]")
    except Exception:
        return 0
    count = 0
    for entry in reversed(log):
        if entry.get("signal_type") in _RESISTANCE_SIGNALS:
            count += 1
        else:
            break
    return count


def _get_discovery_status(discovery_data: dict) -> dict:
    """Return a structured discovery progress dict for prompt injection."""
    collected = [f for f in _ALL_DISCOVERY_FIELDS if discovery_data.get(f)]
    priority_collected = [f for f in _PRIORITY_DISCOVERY_FIELDS if discovery_data.get(f)]
    priority_missing = [f for f in _PRIORITY_DISCOVERY_FIELDS if not discovery_data.get(f)]
    return {
        "collected": collected,
        "total": len(_ALL_DISCOVERY_FIELDS),
        "priority_collected": priority_collected,
        "priority_missing": priority_missing,
        "next_focus": priority_missing[0] if priority_missing else None,
        "priority_complete": len(priority_missing) == 0,
    }


def _get_recent_signals(signal_log_json: str, n: int = 3) -> list:
    """Return the last N signal_type values from the signal log."""
    try:
        log = json.loads(signal_log_json or "[]")
    except Exception:
        return []
    return [e.get("signal_type") for e in log[-n:] if e.get("signal_type")]


def build_companion_context(conversation, ai_profile_doc, tenant: str) -> dict:
    """
    Build the full companion context dict for prompt injection.

    Returns a dict consumed by _build_companion_block() in prompt.py.
    """
    stage = conversation.companion_journey_stage or "ARRIVED"
    discovery_data = _load_discovery(conversation)
    playbook = _load_playbook(ai_profile_doc)

    persona_name = None
    persona_confidence = 0
    if conversation.companion_persona:
        persona_name = frappe.db.get_value(
            "Nexus Companion Persona", conversation.companion_persona, "persona_name"
        )
        persona_confidence = conversation.companion_persona_confidence or 0

    products_block = _build_products_block(tenant, conversation.companion_persona, stage)
    references_block = _build_references_block(discovery_data, conversation.companion_persona, tenant)

    # Verification awareness — tell the LLM when email is not yet collected
    email_verified = bool(getattr(conversation, "visitor_email", None))

    # ── Strategy Engine — read signal_log from enquiry ────────────────────────
    signal_log_json = "[]"
    enquiry_name = getattr(conversation, "companion_enquiry", None)
    if enquiry_name:
        signal_log_json = frappe.db.get_value(
            "Nexus Companion Enquiry", enquiry_name, "signal_log"
        ) or "[]"

    engagement_mode = _compute_engagement_mode(signal_log_json)
    recent_signals = _get_recent_signals(signal_log_json, n=3)
    discovery_status = _get_discovery_status(discovery_data)

    # Capability reveal window: visitor has shared context but discovery is still underway.
    # Fires once when 1-2 priority fields are known — enough to personalise a teaser,
    # early enough that the visitor hasn't heard it yet.
    priority_collected_list = discovery_status.get("priority_collected") or []
    show_capability_reveal = (
        stage == "DISCOVERY"
        and engagement_mode == "PROGRESSING"
        and 1 <= len(priority_collected_list) <= 2
    )

    # Count consecutive resistance signals to determine re-engagement arc step
    disengagement_turn = 0
    if engagement_mode == "DISENGAGING":
        disengagement_turn = max(1, _count_consecutive_disengaging(signal_log_json))

    # Resolve the turn directive: disengagement arc overrides stage × mode matrix
    if engagement_mode == "DISENGAGING":
        arc_step = min(disengagement_turn, 3)
        stage_directive = _DISENGAGEMENT_SEQUENCE.get(arc_step, _DISENGAGEMENT_SEQUENCE[3])
    else:
        stage_directives_for_stage = _STAGE_DIRECTIVES.get(stage, {})
        stage_directive = stage_directives_for_stage.get(
            engagement_mode,
            stage_directives_for_stage.get("PROGRESSING", ""),
        )

    return {
        "companion_stage": stage,
        "companion_persona_name": persona_name,
        "companion_persona_confidence": persona_confidence,
        "companion_discovery_summary": _format_discovery(discovery_data),
        "companion_products_block": products_block,
        "companion_references_block": references_block,
        "companion_playbook_name": playbook.get("name") if playbook else None,
        "companion_guidelines": playbook.get("communication_guidelines", "") if playbook else "",
        "companion_stage_focus": stage_directive,  # kept for backward compatibility
        "companion_stage_directive": stage_directive,
        "companion_discovery_questions": playbook.get("discovery_questions", "") if playbook else "",
        "companion_objection_responses": playbook.get("objection_responses", "") if playbook else "",
        "companion_next_step_options": playbook.get("next_step_options", "") if playbook else "",
        "companion_email_verified": email_verified,
        # Strategy engine keys
        "companion_engagement_mode": engagement_mode,
        "companion_disengagement_turn": disengagement_turn,
        "companion_discovery_status": discovery_status,
        "companion_recent_signals": recent_signals,
        # Capability reveal
        "companion_show_capability_reveal": show_capability_reveal,
        "companion_capability_context": {f: discovery_data.get(f) for f in priority_collected_list},
    }


# ── Internal helpers ───────────────────────────────────────────────────────────

def _load_discovery(conversation) -> dict:
    try:
        raw = conversation.companion_discovery_json or "{}"
        return json.loads(raw)
    except Exception:
        return {}


def _load_playbook(ai_profile_doc) -> dict | None:
    playbook_name = getattr(ai_profile_doc, "companion_playbook", None)
    if not playbook_name:
        return None
    try:
        pb = frappe.get_doc("Nexus Companion Playbook", playbook_name)
        return {
            "name": pb.playbook_name,
            "communication_guidelines": pb.communication_guidelines or "",
            "discovery_questions": pb.discovery_questions or "",
            "objection_responses": pb.objection_responses or "",
            "next_step_options": pb.next_step_options or "",
            "reference_usage_rules": pb.reference_usage_rules or "",
        }
    except Exception:
        return None


def _build_products_block(tenant: str, matched_persona: str | None, stage: str) -> str:
    """
    Build the products/services context block.

    In PRESENTING and CONVERTING stages, include full product detail + conversion config.
    In earlier stages, include a summary to help the LLM identify relevance.
    """
    filters = {"tenant": tenant, "enabled": 1}
    is_deep_stage = stage in ("PRESENTING", "OBJECTION_HANDLING", "INTERESTED", "CONVERTING")

    products = frappe.get_all(
        "Nexus Companion Product",
        filters=filters,
        fields=[
            "name", "product_name", "category", "description",
            "challenges_solved", "typical_outcomes", "qualification_criteria",
            "disqualification_criteria", "objection_responses",
            "conversion_type", "conversion_threshold_score",
            "conversion_message", "conversion_config",
        ],
        limit_page_length=6,
    )
    services = frappe.get_all(
        "Nexus Companion Service",
        filters=filters,
        fields=[
            "name", "service_name as product_name", "category", "description",
            "challenges_solved", "typical_outcomes", "qualification_criteria",
            "disqualification_criteria", "objection_responses",
            "conversion_type", "conversion_threshold_score",
            "conversion_message", "conversion_config",
        ],
        limit_page_length=6,
    )

    all_items = products + services
    if not all_items:
        return "No products or services configured yet."

    lines = []
    for item in all_items:
        name = item.get("product_name") or item.get("service_name") or "(unnamed)"
        cat = f" [{item.category}]" if item.get("category") else ""
        lines.append(f"\n{name}{cat}")

        if item.get("challenges_solved"):
            lines.append(f"  Addresses: {item['challenges_solved'][:180]}")

        if item.get("typical_outcomes"):
            lines.append(f"  Outcomes: {item['typical_outcomes'][:120]}")

        if is_deep_stage:
            if item.get("qualification_criteria"):
                lines.append(f"  Qualify when: {item['qualification_criteria'][:120]}")
            if item.get("disqualification_criteria"):
                lines.append(f"  Do NOT recommend when: {item['disqualification_criteria'][:120]}")
            if item.get("objection_responses"):
                lines.append(f"  Objections: {item['objection_responses'][:200]}")
            if item.get("conversion_type"):
                lines.append(f"  Next step type: {item['conversion_type']}")
            if item.get("conversion_message"):
                lines.append(f"  Guide phrase: {item['conversion_message'][:150]}")

    return "\n".join(lines)


def _build_references_block(discovery_data: dict, matched_persona: str | None, tenant: str) -> str:
    refs = get_relevant_references(discovery_data, matched_persona, tenant, limit=3)
    if not refs:
        return ""
    lines = []
    for r in refs:
        lines.append(f"[{r['type'].upper()}] {r['title']}: {r['summary'][:150]}")
    return "\n".join(lines)


def _format_discovery(discovery_data: dict) -> str:
    if not discovery_data:
        return "No visitor profile collected yet."
    lines = [f"- {k.replace('_', ' ').title()}: {v}" for k, v in discovery_data.items() if v]
    return "\n".join(lines) if lines else "No visitor profile collected yet."
