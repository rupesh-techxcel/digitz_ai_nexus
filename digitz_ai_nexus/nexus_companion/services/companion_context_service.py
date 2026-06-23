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


# ── Per-stage directive (what the LLM should do this turn) ────────────────────

_STAGE_FOCUS = {
    "ARRIVED": (
        "This visitor has just arrived. Warmly greet them. Ask one open question "
        "to understand what brought them here. Do not pitch anything yet."
    ),
    "GREETING": (
        "You are building the first connection. Invite the visitor to share their "
        "business context. Ask about their role, their team, or what they are "
        "working on. One conversational question only."
    ),
    "DISCOVERY": (
        "You are in discovery. Your goal is to understand their situation, challenges, "
        "and what a good outcome looks like. Draw from the discovery questions below. "
        "Ask one question at a time. Do not recommend solutions yet."
    ),
    "ENGAGED": (
        "You have a solid picture of their situation. Begin connecting their challenges "
        "to relevant solutions naturally — frame it as insight, not a pitch. "
        "Introduce the most relevant product or service in the context of their problem."
    ),
    "PRESENTING": (
        "You are presenting a solution. Be specific about how it addresses their "
        "stated challenges. Surface a relevant customer story or outcome to build "
        "confidence. Invite questions. Listen for objections or interest signals."
    ),
    "OBJECTION_HANDLING": (
        "The visitor has raised a concern. Acknowledge it genuinely — never dismiss it. "
        "Address it specifically using the objection responses below. After handling, "
        "bridge back to the value with a question or a different angle. "
        "Avoid repeating the same reframe twice."
    ),
    "INTERESTED": (
        "The visitor has signalled genuine interest. Reinforce the fit with a specific "
        "outcome or metric. Suggest a clear, low-friction next step that matches the "
        "available conversion mechanism. Make it easy to say yes."
    ),
    "CONVERTING": (
        "This visitor is ready to take action. Guide them clearly and simply through "
        "the next step. Use the conversion prompt below if configured. "
        "Reduce all friction. One clear action — not a menu of options."
    ),
    "CONVERTED": (
        "The visitor has taken the next step. Confirm it warmly. Set expectations for "
        "what happens next. Offer a warm close or invite any final questions."
    ),
    "DECLINED": (
        "The visitor has decided not to proceed at this time. Respect that fully. "
        "Leave the door open without pressure. Thank them for their time and invite "
        "them to return whenever the timing is right."
    ),
    "ESCALATED": (
        "This conversation is being handed to a specialist. Wrap up your part helpfully. "
        "Confirm the handoff and reassure the visitor that they are in good hands."
    ),
}


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

    return {
        "companion_stage": stage,
        "companion_persona_name": persona_name,
        "companion_persona_confidence": persona_confidence,
        "companion_discovery_summary": _format_discovery(discovery_data),
        "companion_products_block": products_block,
        "companion_references_block": references_block,
        "companion_playbook_name": playbook.get("name") if playbook else None,
        "companion_guidelines": playbook.get("communication_guidelines", "") if playbook else "",
        "companion_stage_focus": _STAGE_FOCUS.get(stage, ""),
        "companion_discovery_questions": playbook.get("discovery_questions", "") if playbook else "",
        "companion_objection_responses": playbook.get("objection_responses", "") if playbook else "",
        "companion_next_step_options": playbook.get("next_step_options", "") if playbook else "",
        "companion_email_verified": email_verified,
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
