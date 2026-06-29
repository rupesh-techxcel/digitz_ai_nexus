# digitz_ai_nexus/nexus_companion/services/business_companion_controller.py

import json
import frappe

from digitz_ai_nexus.engine.llm import generate_answer
from digitz_ai_nexus.services.answer_service import answer_query
from digitz_ai_nexus.nexus_companion.services.enquiry_service import (
    get_or_create_enquiry,
    update_enquiry,
    advance_journey_stage_from_signal,
)
from digitz_ai_nexus.nexus_companion.services.signal_classifier import classify_signal
from digitz_ai_nexus.nexus_companion.services.companion_intent_service import (
    classify_external_intent,
)

def handle_companion_turn(conversation, agent, payload, core_payload):
    """
    Controller-led companion runtime.

    The controller owns:
    - milestone
    - steering  
    - enquiry/memory update
    - when to use Nexus Orbit knowledge

    The LLM only helps classify, extract, and draft.
    """

    visitor_message = payload.get("message") or core_payload.get("query") or ""
    conversation_context = core_payload.get("conversation_context") or ""
    current_milestone = _get_current_milestone(conversation)
    pending_action = _detect_pending_action(conversation_context)

    enquiry_name = get_or_create_enquiry(conversation)

    signal = classify_signal(
        visitor_message,
        core_payload.get("conversation_context") or "",
    )
        
    try:
                
        external_intent = classify_external_intent(
            visitor_message=visitor_message,
            current_milestone=current_milestone,
            conversation_context=conversation_context,
            pending_action=pending_action,
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: external intent classification failed",
        )
        external_intent = {
            "intent": "unknown",
            "confidence": 0,
        }

    discovery_delta = _extract_discovery_data(
        visitor_message=visitor_message,
        current_milestone=current_milestone,
        conversation=conversation,
    )

    accumulated_discovery = update_enquiry(
        conversation=conversation,
        discovery_delta=discovery_delta,
        signal=signal,
    )

    advance_journey_stage_from_signal(
        conversation,
        signal.get("signal_type", "CURIOUS"),
    )

    _publish_progress_update(conversation)

    # conversation.reload()
    # advance_journey_stage(conversation)

    steering = _decide_steering(
        conversation=conversation,
        visitor_message=visitor_message,
        current_milestone=current_milestone,
        signal=signal,
        discovery_delta=discovery_delta,
        external_intent=external_intent,
        pending_action=pending_action,
        accumulated_discovery=accumulated_discovery,
    )
    
    steering = _apply_grounding_policy(steering)
    
    print("\n\n========== COMPANION CONTROLLER DEBUG ==========")
    print("visitor_message:", visitor_message)
    print("conversation_context:", conversation_context)
    print("current_milestone:", current_milestone)
    print("pending_action:", pending_action)
    print("external_intent:", json.dumps(external_intent, indent=2, default=str))
    print("steering:", json.dumps(steering, indent=2, default=str))
    print("grounding_mode:", steering.get("grounding_mode"))
    print("knowledge_needed:", steering.get("knowledge_needed"))
    print("===============================================\n\n")
    
    frappe.logger("nexus_debug").info({
        "visitor_message": visitor_message,
        "external_intent": external_intent,
        "steering": steering,
        "pending_action": pending_action,
    })

    from digitz_ai_nexus.engine.chat_agent_loop import run_controlled_companion_loop
    
    allowed_tools = _build_allowed_tools(steering)

    loop_payload = dict(core_payload)
    loop_payload["query"] = visitor_message
    loop_payload["original_query"] = visitor_message
    loop_payload["conversation_name"] = conversation.name

    controller_plan = {
        "mode": "controlled_companion",
        "current_milestone": current_milestone,
        "pending_action": pending_action,

        "steering_decision": steering.get("decision"),
        "external_intent": steering.get("visitor_external_intent"),
        "external_intent_confidence": steering.get("external_intent_confidence"),
        "internal_intent": steering.get("internal_intent"),
        "milestone_policy": steering.get("milestone_policy"),

        "knowledge_needed": bool(steering.get("knowledge_needed")),
        "grounding_mode": steering.get("grounding_mode") or "controller_only",
        "knowledge_query": _build_companion_knowledge_query(
            visitor_message=visitor_message,
            current_milestone=current_milestone,
            steering=steering,
            discovery_delta=discovery_delta,
            conversation_context=conversation_context,
        ),
        "allowed_tools": allowed_tools,
        "allow_escalation": "request_escalation" in allowed_tools,

        # Important: controller owns conversion/CTA permission
        "allow_conversion_action": steering.get("decision") == "confirm_demo_request",

        "max_tool_calls": 1,
        "response_goal": _response_goal_for_steering(steering),
        "discovery_delta": discovery_delta,
        "visitor_signal": signal,
        "pain_point_challenges": (
            ", ".join(str(c) for c in v if c)
            if isinstance((v := steering.get("pain_point_challenges") or ""), list)
            else str(v)
        ),
        "current_methodology": (
            ", ".join(str(m) for m in mv if m)
            if isinstance((mv := steering.get("current_methodology") or ""), list)
            else str(mv)
        ),
        "lead_entry_point": steering.get("lead_entry_point") or "",
    }
    
    print("\n\n========== CONTROLLER PLAN DEBUG ==========")
    print(json.dumps(controller_plan, indent=2, default=str))
    print("===========================================\n\n")
    
    if steering.get("decision") == "confirm_demo_request":
        return _handle_demo_confirmation(conversation)

    if steering.get("decision") == "demo_rejected":
        return _handle_demo_rejection(conversation)

    if steering.get("decision") == "answer_next_step":
        return _handle_next_step_question(conversation, pending_action)

    response = run_controlled_companion_loop(
        payload=loop_payload,
        controller_plan=controller_plan,
    )

    # When the methodology knowledge check finds no Nexus Orbit knowledge for the named
    # methodology, transparently pivot to a second search for approved alternatives.
    # The visitor never sees the intermediate "checking" step.
    if (
        steering.get("decision") == "check_methodology_knowledge"
        and isinstance(response, dict)
        and response.get("access_status") == "controlled_no_context"
    ):
        response = _orchestrate_alternative_solution_search(
            conversation=conversation,
            steering=steering,
            visitor_message=visitor_message,
            current_milestone=current_milestone,
            discovery_delta=discovery_delta,
            conversation_context=conversation_context,
            loop_payload=loop_payload,
            controller_plan=controller_plan,
        )

    if not isinstance(response, dict):
        response = {}

    if steering.get("decision") == "offer_escalation":
        response["user_requested_human"] = True
        response["intent_action"] = "escalate"

    response["companion_controller"] = True
    response["conversion_action"] = None

    _maybe_advance_milestone(conversation)

    return response    
  
def _sanitize_alternative_answer(answer):
    """
    Strips duplicate boundary text and LLM-generated final questions from the
    alternative-solution paragraph. The controller owns the boundary statement
    and the final entry-point drive question; the LLM should only provide a short
    grounded alternative capability paragraph.
    """
    answer = (answer or "").strip()
    if not answer:
        return ""

    remove_markers = [
        "i don't have confirmed nexus orbit knowledge",
        "confirmed nexus orbit knowledge",
        "knowledge for google ads was not found",
        "knowledge for google ad was not found",
        "knowledge for facebook ads was not found",
        "knowledge for facebook ad was not found",
        "i can't provide specific information about",
        "i cannot provide specific information about",
        "i should not drill into",
        "i won't drill into",
        "i will not drill into",
        "directly works with",
        "optimizes that methodology",
        "optimises that methodology",
        "does not directly support",
        "not directly support",
    ]

    paragraphs = [p.strip() for p in answer.split("\n\n") if p.strip()]
    cleaned = []

    for p in paragraphs:
        lower = p.lower()

        if any(marker in lower for marker in remove_markers):
            continue

        # Controller owns the final question — strip any paragraph that ends with "?"
        if p.rstrip().endswith("?"):
            continue

        cleaned.append(p)

    return "\n\n".join(cleaned).strip()


def _apply_alternative_response_boundary(response, current_methodology, context_area):
    """
    Deterministic composition for the unsupported-methodology response.

    Ownership:
    - Controller: boundary statement, Nexy bridge, entry-point drive question
    - LLM: one short grounded alternative paragraph (sanitized before use)
    """

    if not isinstance(response, dict):
        response = {}

    answer = _sanitize_alternative_answer(response.get("answer") or "")
    mref = current_methodology or "that approach"

    boundary = (
        f"I don't have confirmed Nexus Orbit knowledge showing that Nexy directly works with {mref} "
        f"or optimizes that methodology, so I should not drill into {mref} strategy."
    )

    if context_area == "lead_generation":
        nexy_bridge = (
            "So the focus is not the ad campaign itself, but the conversion journey after the enquiry arrives."
        )
        drive_question = (
            f"To show where Nexy can fit into your lead conversion flow, "
            f"where do those {mref} enquiries usually reach you first — "
            "website chat, WhatsApp, contact form, phone call, or somewhere else?"
        )
    else:
        nexy_bridge = (
            "So the focus is not the unsupported method itself, but the request journey after the enquiry arrives."
        )
        drive_question = (
            "To show where Nexy can fit, where do those enquiries or requests usually come in today?"
        )

    # If the LLM answer was entirely stripped (all boundary/question text),
    # insert a safe generic capability summary so the response is not bare.
    if not answer and context_area == "lead_generation":
        answer = (
            "Nexy can support the post-enquiry journey by helping structure visitor conversations, "
            "understand requirements, qualify enquiries, preserve discovery context, and guide the lead "
            "toward a meaningful next step."
        )

    parts = [boundary]
    if answer:
        parts.append(answer)
    parts.append(nexy_bridge)
    parts.append(drive_question)

    response["answer"] = "\n\n".join(p.strip() for p in parts if p and p.strip())
    response["methodology_boundary_applied"] = True
    response["nexy_entry_drive_applied"] = True
    return response


def _orchestrate_alternative_solution_search(
    conversation,
    steering,
    visitor_message,
    current_milestone,
    discovery_delta,
    conversation_context,
    loop_payload,
    controller_plan,
):
    """
    Called when check_methodology_knowledge returns controlled_no_context.
    Persists 'unsupported' status, then runs a second search for approved Nexus
    alternatives for the visitor's broader challenge area.
    """
    from digitz_ai_nexus.engine.chat_agent_loop import run_controlled_companion_loop

    current_methodology = (steering.get("current_methodology") or "").strip()
    meth_context_area = (steering.get("methodology_context_area") or "general_business").strip()
    challenge_text = (steering.get("pain_point_challenges") or "").strip()

    # Persist 'unsupported' so future turns skip the check and go straight to alternatives
    status_fact = {
        "context_area": meth_context_area,
        "fact_type": "methodology_knowledge_status",
        "fact_value": "unsupported",
        "related_value": current_methodology,
        "source_message": "nexus_orbit_search_result",
    }
    update_enquiry(conversation, {"discovery_facts": [status_fact]}, signal=None)

    alt_steering = {
        "decision": "present_alternative_solution",
        "knowledge_needed": True,
        "redirect_to_milestone": False,
        "visitor_external_intent": steering.get("visitor_external_intent"),
        "external_intent_confidence": steering.get("external_intent_confidence"),
        "internal_intent": "present_nexus_approved_alternatives_for_challenge",
        "milestone_policy": "pain_discovery",
        "current_methodology": current_methodology,
        "methodology_context_area": meth_context_area,
        "pain_point_challenges": challenge_text,
    }
    alt_steering = _apply_grounding_policy(alt_steering)

    alt_controller_plan = {
        **controller_plan,
        "steering_decision": "present_alternative_solution",
        "grounding_mode": "nexus_knowledge_only",
        "knowledge_needed": True,
        "knowledge_query": _build_companion_knowledge_query(
            visitor_message=visitor_message,
            current_milestone=current_milestone,
            steering=alt_steering,
            discovery_delta=discovery_delta,
            conversation_context=conversation_context,
        ),
        "response_goal": _response_goal_for_steering(alt_steering),
        "current_methodology": current_methodology,
        "pain_point_challenges": challenge_text,
        "allowed_tools": [],
    }

    alt_response = run_controlled_companion_loop(
        payload=loop_payload,
        controller_plan=alt_controller_plan,
    )

    if (
        isinstance(alt_response, dict)
        and alt_response.get("access_status") != "controlled_no_context"
    ):
        bounded = _apply_alternative_response_boundary(
            response=alt_response,
            current_methodology=current_methodology,
            context_area=meth_context_area,
        )
        # Persist that the boundary + fit-check have been presented so the next
        # turn can skip re-showing the full alternative explanation.
        boundary_fact = {
            "context_area": meth_context_area,
            "fact_type": "alternative_boundary_presented",
            "fact_value": "yes",
            "related_value": current_methodology,
            "source_message": "alternative_solution_search",
        }
        update_enquiry(conversation, {"discovery_facts": [boundary_fact]}, signal=None)
        return bounded

    return _no_alternative_fallback(current_methodology, challenge_text)


def _no_alternative_fallback(current_methodology, challenge):
    mref = current_methodology or "that approach"
    cref = challenge or "your business challenge"
    return {
        "status": "success",
        "access_status": "controlled_no_context",
        "answer": (
            f"I don't have confirmed Nexus Orbit knowledge for {mref}, "
            f"and I also don't have an approved alternative workflow for {cref} in my current knowledge base. "
            "I should not guide you further without confirmed information. "
            "I can note your requirement and route it to the right team for a confirmed answer — "
            "would you like me to do that?"
        ),
        "confidence": 0.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 1,
        "chat_mode": "controlled_companion_loop",
        "companion_controller": True,
        "conversion_action": None,
    }


def _build_companion_knowledge_query(
    visitor_message,
    current_milestone,
    steering,
    discovery_delta,
    conversation_context,
):
    """
    Build controller-owned Nexus Orbit search query.
    Do not leave important knowledge retrieval query design to the LLM.
    """

    steering = steering or {}
    decision = steering.get("decision")
    intent = steering.get("visitor_external_intent")

    discovery_text = json.dumps(discovery_delta or {}, default=str)

    if intent == "solution_fit_question":
        return (
            "Nexus capability for visitor business problem. "
            f"Visitor question: {visitor_message}. "
            f"Business context: {discovery_text}. "
            "Find approved knowledge about lead generation, Facebook ads, customer profiling, "
            "lead capture, enquiry qualification, follow-up, tracking, conversion improvement, "
            "business growth support, and Nexus/Nexy capability limitations."
        )

    if intent == "solution_method_question":
        return (
            "How Nexus performs or supports the mentioned solution method. "
            f"Visitor question: {visitor_message}. "
            f"Conversation context: {conversation_context}. "
            "Find approved knowledge about implementation method, workflow, feature, capability, "
            "process, limitations, lead capture, customer profiling, qualification, follow-up, "
            "tracking, and conversion improvement."
        )

    if intent == "pricing_question":
        return (
            "Nexus pricing, package, quotation, subscription, payment, commercial policy, "
            f"or pricing limitation. Visitor question: {visitor_message}."
        )

    if intent == "product_question":
        return (
            "Nexus product, service, feature, module, capability, benefit, limitation, "
            f"or implementation detail. Visitor question: {visitor_message}."
        )

    if intent == "technical_how_it_works_question":
        return (
            "Nexus technical workflow, implementation method, integration, automation, routing, "
            f"or knowledge-based process. Visitor question: {visitor_message}. "
            f"Conversation context: {conversation_context}."
        )

    if decision == "answer_solution_fit":
        methodology = (steering.get("current_methodology") or "").strip()
        _raw_challenges = steering.get("pain_point_challenges") or discovery_delta.get("current_challenges") or ""
        if isinstance(_raw_challenges, list):
            _raw_challenges = ", ".join(str(c) for c in _raw_challenges if c)
        challenges = str(_raw_challenges).strip()

        if methodology:
            return (
                f"Does Nexus Orbit have capabilities for {methodology}? "
                f"Nexus integration, support, or confirmed features for {methodology}. "
                f"Nexus approach to {challenges or 'the visitor challenge'} using or related to {methodology}. "
                f"Business context: {discovery_text}."
            )
        if challenges:
            return (
                f"How Nexus Orbit helps with: {challenges}. "
                f"Nexus capabilities, confirmed approach, and features for: {challenges}. "
                f"Business context: {discovery_text}."
            )
        return (
            "How Nexus Orbit helps with the visitor's business challenge. "
            f"Visitor context: {visitor_message}. Business context: {discovery_text}."
        )

    if decision == "check_methodology_knowledge":
        methodology = (steering.get("current_methodology") or "").strip()
        challenges = (steering.get("pain_point_challenges") or "").strip()
        mlow = methodology.lower()
        if "facebook" in mlow or "meta" in mlow:
            return (
                "Approved Nexus Orbit knowledge specifically about Facebook Ads, Facebook Lead Ads, "
                "Meta Ads, Meta Lead Ads, Facebook campaign leads, or Facebook/Meta integration. "
                f"Visitor methodology: {methodology}. "
                f"Visitor challenge: {challenges}. "
                "Find only explicit confirmed Nexus/Nexy capability, limitation, integration, workflow, "
                "or support related to Facebook/Meta Ads. "
                "Do not use broad lead generation, business growth, structured conversation, website chat, "
                "or WhatsApp knowledge as proof of Facebook Ads capability."
            )
        return (
            f"Approved Nexus Orbit knowledge specifically about the visitor's current methodology: {methodology}. "
            f"Visitor challenge: {challenges}. "
            "Find only explicit confirmed Nexus/Nexy capability, limitation, integration, workflow, "
            "or support related to this exact methodology. "
            "Do not use broad business growth or generic process knowledge as proof."
        )

    if decision == "present_alternative_solution":
        methodology = (steering.get("current_methodology") or "").strip()
        challenges = (steering.get("pain_point_challenges") or "").strip()
        context_area = (steering.get("methodology_context_area") or "general_business").strip()
        area_label = {
            "lead_generation": "lead generation and sales enquiry handling",
            "recruitment": "recruitment and talent acquisition",
            "operations": "operations and service delivery",
            "general_business": "business management",
        }.get(context_area, context_area.replace("_", " "))
        return (
            f"Approved Nexus Orbit alternative capabilities for {area_label}. "
            f"The visitor's current methodology is {methodology}, but methodology-specific knowledge was not confirmed. "
            f"Visitor challenge: {challenges or area_label}. "
            "Find only confirmed Nexus/Nexy alternatives for the broader challenge. "
            "Do not rely on the unsupported methodology. "
            "Do not include Facebook Ads, Meta Ads, campaign management, targeting, creative optimization, "
            "ad budget optimization, or ad-platform automation unless explicitly present in the knowledge."
        )

    if decision == "present_nexy_capability_summary":
        methodology = (steering.get("current_methodology") or "").strip()
        challenges = (steering.get("pain_point_challenges") or "").strip()
        entry_point = (steering.get("lead_entry_point") or "").strip()
        return (
            "Approved Nexus Orbit knowledge about Nexy Companion capabilities for lead enquiry handling. "
            f"Visitor challenge: {challenges}. "
            f"Visitor current traffic source or methodology: {methodology}, but direct methodology support was not confirmed. "
            f"Lead entry point: {entry_point}. "
            "Find confirmed Nexy capabilities for handling enquiries after they arrive, including visitor conversation, "
            "requirement discovery, enquiry qualification, discovery data capture, conversation transcript, "
            "guided next step, human handoff, routing, CRM/enquiry update, or structured lead journey. "
            "Do not include ad campaign management, ad targeting, budget optimization, creative optimization, "
            "or ad-platform automation unless explicitly present in the knowledge."
        )

    return visitor_message or ""

def _response_goal_for_steering(steering):
    decision = steering.get("decision")

    if decision == "brief_answer_then_redirect":
        return (
            "Briefly acknowledge the visitor's question, do not go deep yet, "
            "then guide them back to the current business onboarding question."
        )

    if decision == "answer_and_continue_onboarding":
        return (
            "Answer the visitor's operational question briefly, then continue business onboarding naturally."
        )

    if decision == "continue_milestone":
        return (
            "Reference the visitor's industry or business type in one concise sentence — their sector or operational context. "
            "Do NOT open with 'It\\'s [adjective]', 'That\\'s [adjective]', 'How [adjective]', or 'I appreciate'. "
            "Do NOT repeat back or comment on the visitor's specific tool, platform, or methodology. "
            "Then ask the next most relevant discovery question about their business challenge or goals."
        )

    if decision == "offer_escalation":
        return (
            "Acknowledge that the visitor wants a representative and prepare for handoff. "
            "Do not ask unrelated discovery questions."
        )

    if decision == "redirect_to_milestone":
        return (
            "Gently redirect the visitor back to the current milestone without sounding restrictive."
        )
        
    if decision == "acknowledge_then_redirect":
        return (
            "Briefly acknowledge the visitor's request, do not move to demo or meeting yet, "
            "then guide them back to the current onboarding question."
        )

    if decision == "answer_with_orbit":
        return (
            "Use permitted knowledge if needed, answer the visitor's product question accurately, "
            "then keep the conversation aligned with the companion journey."
        )

    if decision == "answer_with_orbit_or_policy":
        return (
            "Use permitted knowledge or configured policy to answer safely. "
            "Do not invent pricing, commitments, discounts, timelines, or guarantees."
        )

    if decision == "consider_next_step":
        return (
            "Acknowledge interest in a next step, but do not trigger a booking or handoff unless "
            "the controller explicitly allows conversion_action."
        )
    
    if decision == "discover_current_methodology":
        return (
            "Name the specific challenge the visitor shared in one short sentence — "
            "do NOT open with 'It\\'s [adjective]', 'That\\'s [adjective]', or any hollow affirmation. "
            "State it directly, e.g.: 'Lead generation is a key challenge for service businesses.' "
            "Then ask one focused, visitor-friendly question about what they are currently using "
            "for that challenge — use plain wording, not the word 'methodology'. "
            "For example: 'What are you currently using to generate leads — "
            "Facebook ads, Google ads, referrals, website enquiries, WhatsApp, or something else?' "
            "Do not suggest Nexus solutions or imply Nexus can help yet."
        )

    if decision == "discover_current_result":
        methodology = (steering.get("visitor_current_methodology") or "").strip()
        methodology_ref = f"from {methodology}" if methodology else "from that approach"
        return (
            f"The visitor has shared their current approach ({methodology or 'noted'}). "
            f"Ask ONE question to understand what results they are getting {methodology_ref} now. "
            "Do not explain Nexus capability. "
            "Do not ask about ad targeting, creatives, budget, campaign setup, or ad optimization. "
            f"Keep it direct — e.g.: 'What kind of results are you getting {methodology_ref} right now?'"
        )

    if decision == "discover_conversion_bottleneck":
        return (
            "The visitor mentioned that leads or results are coming in but conversion is low. "
            "Ask ONE question to identify where the conversion drop happens after the lead arrives. "
            "Mention possible stages: first response, qualification, quotation, follow-up, "
            "appointment booking, or closing. "
            "Do not give Facebook ads advice. "
            "Do not discuss targeting, ad creatives, campaign optimization, or offers. "
            "Do not claim Nexus capability yet."
        )

    if decision == "drive_to_nexy_entry_point":
        methodology = (steering.get("current_methodology") or "").strip()
        mref = methodology or "that approach"
        context_area = (steering.get("methodology_context_area") or "lead_generation").strip()
        if context_area == "lead_generation":
            return (
                "The unsupported methodology boundary and Nexy alternative have already been explained. "
                "Do NOT repeat the full alternative explanation. "
                "Briefly drive the visitor toward where Nexy fits in the lead journey. "
                f"Ask: 'To show where Nexy can fit into your lead conversion flow, "
                f"where do those {mref} enquiries usually reach you first — website chat, WhatsApp, "
                "contact form, phone call, or somewhere else?'"
            )
        return (
            "The unsupported methodology boundary and Nexy alternative have already been explained. "
            "Do NOT repeat the full alternative explanation. "
            "Briefly ask where Nexy can enter the current request or enquiry flow."
        )

    if decision == "present_nexy_capability_summary":
        entry_point = (steering.get("lead_entry_point") or "the enquiry channel").strip()
        challenges = (steering.get("pain_point_challenges") or "lead generation").strip()
        methodology = (steering.get("current_methodology") or "").strip()
        mref = methodology or "that approach"
        return (
            "Explain how Nexy can help only from permitted Nexus Orbit knowledge. "
            f"Frame the answer around what happens after the enquiry arrives through {entry_point}. "
            f"Connect the explanation to the visitor's challenge: {challenges}. "
            f"If relevant, clarify that Nexy is not replacing or optimizing {mref}; "
            "it supports the conversion journey after the enquiry arrives. "
            "Summarize Nexy capabilities in a concise capability summary, not a long essay. "
            "Do not claim ad campaign optimization, direct ad-platform support, or unconfirmed integrations. "
            "End by offering to map the visitor's actual lead journey into a simple Nexy flow."
        )

    if decision == "continue_discovery":
        return (
            "Ask the next most relevant discovery question based on what is already known about "
            "the visitor's business, challenge, current approach, and results. "
            "Do not explain Nexus capability unless the visitor explicitly asks how Nexus can help."
        )

    if decision == "check_methodology_knowledge":
        methodology = (steering.get("current_methodology") or "").strip()
        mref = methodology or "the visitor methodology"
        return (
            f"Check whether permitted Nexus Orbit knowledge specifically confirms support for {mref}. "
            "Do not ask any visitor-facing methodology drill-down question in this turn. "
            f"Do not claim direct support, integration, optimization, or automation for {mref} "
            "unless explicitly confirmed in the permitted knowledge. "
            "If no specific knowledge is available, the controller will move to approved alternative search."
        )

    if decision == "present_alternative_solution":
        challenges = (steering.get("pain_point_challenges") or "the visitor's challenge").strip()
        methodology = (steering.get("current_methodology") or "").strip()
        mref = methodology or "that approach"
        return (
            "Write only ONE short paragraph summarizing the approved Nexy/Nexus alternative "
            "from the permitted Nexus Orbit knowledge. "
            "Do NOT state that methodology-specific knowledge was not found; the controller will add that boundary. "
            "Do NOT write any final question; the controller will add the final entry-point question. "
            f"Frame the alternative around the broader challenge: {challenges}. "
            "Position Nexy around the post-enquiry journey: visitor conversation, requirement understanding, "
            "qualification, discovery context, and guided next step — only if confirmed in the permitted knowledge. "
            f"Do not say or imply that Nexus manages, optimizes, integrates with, or improves {mref}. "
            "Keep it concise. One paragraph only."
        )

    if decision == "answer_solution_fit":
        return (
            "Answer only from the permitted Nexus Orbit knowledge provided in this turn. "
            "Do not infer or create capabilities. Do not claim Facebook ads support, customer profiling, "
            "lead capture, enquiry qualification, follow-up, routing, tracking, automation, dashboards, "
            "or conversion improvement unless those are clearly present in the permitted knowledge. "
            "If grounded, connect each capability directly to the visitor's stated challenge and context. "
            "End with ONE open-ended question — do NOT present a menu of options."
        )

    if decision == "explain_solution_method":
        return (
            "Explain the method only from permitted Nexus Orbit knowledge provided in this turn. "
            "If the knowledge does not specifically describe the requested method, workflow, or capability, "
            "do not infer or create a method. "
            "Do not give Facebook ads advice or marketing optimization advice unless explicitly confirmed "
            "by permitted knowledge. "
            "If specific grounding is not available, do not answer from assumption."
        )

    return "Continue the companion conversation naturally while following the current milestone."

def _get_current_milestone(conversation):
    """
    Resolve controller milestone from the dedicated companion_milestone field.
    Falls back to deriving from journey stage for conversations started before
    the field was introduced.
    """

    milestone = (getattr(conversation, "companion_milestone", None) or "").strip()

    business_milestones = {
        "onboarding_business",
        "business_discovery",
        "pain_discovery",
        "solution_mapping",
        "evidence_building",
        "demo_arrangement",
        "quotation",
        "conversion",
    }

    if milestone in business_milestones:
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

def _build_allowed_tools(steering):
    """
    Controller decides which tools the LLM may use in this turn.
    """

    tools = []

    if steering.get("knowledge_needed"):
        tools.append("search_knowledge")

    if steering.get("decision") == "offer_escalation":
        tools.append("request_escalation")

    return tools

def _extract_discovery_data(visitor_message, current_milestone, conversation):
    prompt = f"""
Extract business discovery information from the visitor message.

Current milestone: {current_milestone}

Visitor message:
{visitor_message}

Return ONLY valid JSON. Use these keys:

Standard keys (only if clearly present):
company_name, industry, company_size, team_size, business_type,
business_maturity, current_challenges, goals, existing_systems,
budget_range, timeline, decision_maker

Also include a "discovery_facts" array for any specific contextual facts found.
Each discovery fact must have:
  "context_area": one of "lead_generation", "recruitment", "operations", "general_business"
  "fact_type": one of "current_methodology", "current_approach", "current_tool",
               "current_result", "bottleneck", "conversion_bottleneck_stage",
               "process_gap", "goal", "volume", "urgency", "responsible_person",
               "follow_up_process", "lead_entry_point"
  "fact_value": the extracted value (non-empty string)
  "source_message": the original phrase

Examples:
- "We do Facebook ads" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "current_methodology", "fact_value": "Facebook ads", "source_message": "We do Facebook ads"}}]}}
- "Facebook ads are doing well but conversion is low" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "current_result", "fact_value": "Facebook ads doing well but conversion is low", "source_message": "Facebook ads are doing well but conversion is low"}}]}}
- "We are lagging with lead generation" → {{"current_challenges": "lead generation", "discovery_facts": []}}
- "We do Google ads and also get referrals" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "current_methodology", "fact_value": "Google ads and referrals", "source_message": "We do Google ads and also get referrals"}}]}}
- "Mostly WhatsApp" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "WhatsApp", "source_message": "Mostly WhatsApp"}}]}}
- "They come to our website" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "Website", "source_message": "They come to our website"}}]}}
- "They fill a contact form" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "Contact form", "source_message": "They fill a contact form"}}]}}
- "Mostly calls" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "Phone call", "source_message": "Mostly calls"}}]}}
- "WhatsApp and website" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "WhatsApp and website", "source_message": "WhatsApp and website"}}]}}

Only extract facts clearly stated. Do not infer. If nothing found, return {{}}.
"""

    try:
        raw = (generate_answer(prompt) or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json", "", 1).strip()
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Companion Controller: discovery extraction failed")
        return {}

# ---------------------------------------------------------------------------
# Discovery fact helpers
# ---------------------------------------------------------------------------

def _get_discovery_facts(discovery):
    facts = discovery.get("discovery_facts") or []
    return facts if isinstance(facts, list) else []

def _find_fact(discovery, context_area, fact_type, related_value=None):
    related_value_str = str(related_value or "").strip().lower()
    for fact in _get_discovery_facts(discovery):
        if str(fact.get("context_area") or "").strip() != context_area:
            continue
        if str(fact.get("fact_type") or "").strip() != fact_type:
            continue
        if not str(fact.get("fact_value") or "").strip():
            continue
        if related_value_str:
            candidate = str(fact.get("related_value") or "").strip().lower()
            if candidate != related_value_str:
                continue
        return fact
    return None

def _has_fact(discovery, context_area, fact_type, related_value=None):
    return bool(_find_fact(discovery, context_area, fact_type, related_value=related_value))

def _get_fact_value(discovery, context_area, fact_type):
    fact = _find_fact(discovery, context_area, fact_type)
    return str((fact or {}).get("fact_value") or "").strip()

def _detect_context_area_from_challenge(challenge_text):
    text = str(challenge_text or "").lower()
    if "lead" in text or "enquir" in text or "inquir" in text or "prospect" in text:
        return "lead_generation"
    if "recruit" in text or "hiring" in text or "candidate" in text or "talent" in text:
        return "recruitment"
    if "operation" in text or "schedule" in text or "delivery" in text or "dispatch" in text:
        return "operations"
    return "general_business"


def _looks_like_methodology_answer(visitor_message):
    text = str(visitor_message or "").lower().strip()
    keywords = [
        "google ads", "google ad", "adwords",
        "facebook ads", "facebook ad", "meta ads", "instagram ads",
        "referrals", "referral",
        "seo",
        "website enquiries", "website inquiries", "website leads",
        "cold calling", "cold call",
        "social media",
        "walk in", "walk-in",
    ]
    return any(k in text for k in keywords)


def _normalise_methodology_answer(visitor_message):
    text = str(visitor_message or "").strip()
    low = text.lower()

    if "google" in low and ("ads" in low or "adwords" in low):
        return "Google Ads"
    if "facebook" in low:
        return "Facebook Ads"
    if "meta" in low:
        return "Meta Ads"
    if "instagram" in low:
        return "Instagram Ads"
    if "seo" in low:
        return "SEO"
    if "referral" in low or "reference" in low:
        return "Referrals"
    if "website" in low and ("enquir" in low or "inquir" in low or "lead" in low):
        return "Website enquiries"
    if "cold" in low and "call" in low:
        return "Cold calling"
    if "social media" in low:
        return "Social media"

    return text


def _get_current_methodology_value(accumulated, context_area):
    mfact = (
        _find_fact(accumulated, context_area, "current_methodology")
        or _find_fact(accumulated, context_area, "current_approach")
        or _find_fact(accumulated, context_area, "current_tool")
    )
    if mfact:
        return str(mfact.get("fact_value") or "").strip()
    raw_sys = accumulated.get("existing_systems") or ""
    return (
        ", ".join(str(s) for s in raw_sys if s)
        if isinstance(raw_sys, list)
        else str(raw_sys)
    ).strip()

def _result_mentions_conversion_issue(result_value):
    text = str(result_value or "").lower()
    return any(kw in text for kw in [
        "conversion", "convert", "closing", "close rate", "close ratio",
        "not booking", "not converting", "low close", "dropping off",
        "follow up", "follow-up", "not following", "low conversion",
    ])

def _load_accumulated_discovery(conversation):
    try:
        enquiry_name = getattr(conversation, "companion_enquiry", None)
        if not enquiry_name:
            return {}
        enquiry = frappe.get_doc("Nexus Companion Enquiry", enquiry_name)
        return json.loads(enquiry.discovery_data or "{}")
    except Exception:
        return {}

def _decide_steering(
    conversation,
    visitor_message,
    current_milestone,
    signal,
    discovery_delta,
    external_intent,
    pending_action=None,
    accumulated_discovery=None,
):
    """
    Simple controller-owned steering policy.

    The controller decides the business move.
    The LLM only helps classify external_intent and draft the final response.

    Later this should be replaced by Playbook-driven milestone configuration.
    """

    external_intent = external_intent or {}
    intent = (external_intent.get("intent") or "unknown").strip()
    confidence = float(external_intent.get("confidence") or 0)
    # Use the freshly-merged discovery dict passed from handle_companion_turn
    # (avoids Frappe doc-cache reading stale data from the DB).
    _accumulated = accumulated_discovery if accumulated_discovery is not None else _load_accumulated_discovery(conversation)

    # ------------------------------------------------------------------
    # Hard interrupts
    # These are allowed to break the current milestone.
    # ------------------------------------------------------------------
    
    if intent == "demo_confirmation" and pending_action == "demo_request":
        return {
            "decision": "confirm_demo_request",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "create_or_prepare_demo_request",
            "milestone_policy": "conversion_confirmed",
        }

    if intent == "demo_rejection" and pending_action == "demo_request":
        return {
            "decision": "demo_rejected",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "continue_discovery_without_demo",
            "milestone_policy": "conversion_declined",
        }

    # ------------------------------------------------------------------
    # EARLY METHODOLOGY GUARD
    # Runs regardless of intent classification. If the visitor has stated
    # a methodology (or their message looks like a methodology answer) and
    # Nexus Orbit has not yet been checked for it, always gate on
    # check_methodology_knowledge before any drill-down or discovery.
    # ------------------------------------------------------------------
    _eg_accumulated = _accumulated or {}

    _eg_challenge_text = (
        _eg_accumulated.get("current_challenges")
        or discovery_delta.get("current_challenges")
        or ""
    )
    if isinstance(_eg_challenge_text, list):
        _eg_challenge_text = ", ".join(str(c) for c in _eg_challenge_text if c)

    _eg_context_area = _detect_context_area_from_challenge(_eg_challenge_text)

    _eg_methodology = _get_current_methodology_value(_eg_accumulated, _eg_context_area)

    # If the LLM extraction missed it but the message clearly names a methodology,
    # normalise it and persist it so the check can proceed.
    if (
        _eg_challenge_text
        and not _eg_methodology
        and _looks_like_methodology_answer(visitor_message)
    ):
        _eg_methodology = _normalise_methodology_answer(visitor_message)
        update_enquiry(
            conversation,
            {
                "discovery_facts": [
                    {
                        "context_area": _eg_context_area,
                        "fact_type": "current_methodology",
                        "fact_value": _eg_methodology,
                        "source_message": visitor_message,
                    }
                ]
            },
            signal=None,
        )

    _eg_methodology_known = bool(_eg_methodology)

    _eg_methodology_checked = _eg_methodology_known and _has_fact(
        _eg_accumulated,
        _eg_context_area,
        "methodology_knowledge_status",
        related_value=_eg_methodology,
    )

    _eg_status_fact = (
        _find_fact(
            _eg_accumulated,
            _eg_context_area,
            "methodology_knowledge_status",
            related_value=_eg_methodology,
        )
        if _eg_methodology_known
        else None
    )

    _eg_methodology_unsupported = bool(
        _eg_status_fact
        and str(_eg_status_fact.get("fact_value") or "").lower()
        in ["unsupported", "unconfirmed", "not_found"]
    )

    _eg_boundary_shown = _eg_methodology_known and _has_fact(
        _eg_accumulated,
        _eg_context_area,
        "alternative_boundary_presented",
        related_value=_eg_methodology,
    )

    _eg_lead_entry_point = _get_fact_value(_eg_accumulated, _eg_context_area, "lead_entry_point")

    # Gate: challenge known + methodology known + not yet checked → always check first
    if _eg_challenge_text and _eg_methodology_known and not _eg_methodology_checked:
        return {
            "decision": "check_methodology_knowledge",
            "knowledge_needed": True,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "verify_methodology_in_nexus_orbit_before_drill_down",
            "milestone_policy": "pain_discovery",
            "current_methodology": _eg_methodology,
            "methodology_context_area": _eg_context_area,
            "pain_point_challenges": _eg_challenge_text,
        }

    # Methodology already confirmed unsupported → drive Nexy flow
    if _eg_challenge_text and _eg_methodology_known and _eg_methodology_unsupported:
        if _eg_boundary_shown and _eg_lead_entry_point:
            return {
                "decision": "present_nexy_capability_summary",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "explain_nexy_capability_for_confirmed_entry_point",
                "milestone_policy": "solution_mapping",
                "current_methodology": _eg_methodology,
                "methodology_context_area": _eg_context_area,
                "pain_point_challenges": _eg_challenge_text,
                "lead_entry_point": _eg_lead_entry_point,
            }
        return {
            "decision": "drive_to_nexy_entry_point" if _eg_boundary_shown else "present_alternative_solution",
            "knowledge_needed": not _eg_boundary_shown,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "drive_to_nexy_entry_point" if _eg_boundary_shown else "present_nexus_approved_alternatives_for_challenge",
            "milestone_policy": "pain_discovery",
            "current_methodology": _eg_methodology,
            "methodology_context_area": _eg_context_area,
            "pain_point_challenges": _eg_challenge_text,
        }

    if intent == "pain_context_answer":
        accumulated = _accumulated

        # Resolve context area from known challenge
        challenge_text = accumulated.get("current_challenges") or discovery_delta.get("current_challenges") or ""
        if isinstance(challenge_text, list):
            challenge_text = ", ".join(str(c) for c in challenge_text if c)
        context_area = _detect_context_area_from_challenge(challenge_text)

        # Methodology known = discovery_fact OR legacy existing_systems
        methodology_known = (
            _has_fact(accumulated, context_area, "current_methodology")
            or _has_fact(accumulated, context_area, "current_approach")
            or _has_fact(accumulated, context_area, "current_tool")
            or bool(accumulated.get("existing_systems"))
        )

        # Current result known
        result_known = (
            _has_fact(accumulated, context_area, "current_result")
            or _has_fact(accumulated, context_area, "bottleneck")
        )

        # Conversion bottleneck stage known
        conversion_bottleneck_known = _has_fact(accumulated, context_area, "conversion_bottleneck_stage")

        if not methodology_known:
            return {
                "decision": "discover_current_methodology",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "understand_current_approach_before_solution",
                "milestone_policy": "pain_discovery",
            }

        # Extract current methodology value for status check and response goals
        mfact = (
            _find_fact(accumulated, context_area, "current_methodology")
            or _find_fact(accumulated, context_area, "current_approach")
            or _find_fact(accumulated, context_area, "current_tool")
        )
        if mfact:
            current_methodology_value = str(mfact.get("fact_value") or "").strip()
        else:
            raw_sys = accumulated.get("existing_systems") or ""
            current_methodology_value = (
                ", ".join(str(s) for s in raw_sys if s)
                if isinstance(raw_sys, list)
                else str(raw_sys)
            ).strip()

        # Methodology known but Nexus Orbit check not yet done → check it
        methodology_checked = _has_fact(
            accumulated, context_area, "methodology_knowledge_status",
            related_value=current_methodology_value,
        )

        if not methodology_checked:
            return {
                "decision": "check_methodology_knowledge",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "verify_methodology_in_nexus_orbit_before_drill_down",
                "milestone_policy": "pain_discovery",
                "current_methodology": current_methodology_value,
                "methodology_context_area": context_area,
                "pain_point_challenges": challenge_text,
            }

        # Methodology confirmed unsupported → present approved alternatives
        status_fact = _find_fact(
            accumulated, context_area, "methodology_knowledge_status",
            related_value=current_methodology_value,
        )
        methodology_unsupported = bool(
            status_fact
            and str(status_fact.get("fact_value") or "").lower() in [
                "unsupported", "unconfirmed", "not_found",
            ]
        )

        if methodology_unsupported:
            boundary_already_shown = _has_fact(
                accumulated, context_area, "alternative_boundary_presented",
                related_value=current_methodology_value,
            )
            lead_entry_point = _get_fact_value(accumulated, context_area, "lead_entry_point")

            # Boundary shown + entry point known → present grounded Nexy capability summary
            if boundary_already_shown and lead_entry_point:
                return {
                    "decision": "present_nexy_capability_summary",
                    "knowledge_needed": True,
                    "redirect_to_milestone": False,
                    "visitor_external_intent": intent,
                    "external_intent_confidence": confidence,
                    "internal_intent": "explain_nexy_capability_for_confirmed_entry_point",
                    "milestone_policy": "solution_mapping",
                    "current_methodology": current_methodology_value,
                    "methodology_context_area": context_area,
                    "pain_point_challenges": challenge_text,
                    "lead_entry_point": lead_entry_point,
                }

            return {
                "decision": "drive_to_nexy_entry_point" if boundary_already_shown else "present_alternative_solution",
                "knowledge_needed": not boundary_already_shown,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "drive_to_nexy_entry_point" if boundary_already_shown else "present_nexus_approved_alternatives_for_challenge",
                "milestone_policy": "pain_discovery",
                "current_methodology": current_methodology_value,
                "methodology_context_area": context_area,
                "pain_point_challenges": challenge_text,
            }

        # Methodology is supported — proceed with result discovery
        if not result_known:
            return {
                "decision": "discover_current_result",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "understand_current_results_before_solution",
                "milestone_policy": "pain_discovery",
                "visitor_current_methodology": current_methodology_value,
            }

        if not conversion_bottleneck_known:
            rfact = (
                _find_fact(accumulated, context_area, "current_result")
                or _find_fact(accumulated, context_area, "bottleneck")
            )
            rval = str(rfact.get("fact_value") or "") if rfact else ""
            if _result_mentions_conversion_issue(rval):
                return {
                    "decision": "discover_conversion_bottleneck",
                    "knowledge_needed": False,
                    "redirect_to_milestone": False,
                    "visitor_external_intent": intent,
                    "external_intent_confidence": confidence,
                    "internal_intent": "identify_conversion_drop_stage",
                    "milestone_policy": "pain_discovery",
                }

        return {
            "decision": "continue_discovery",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "continue_discovery_before_value_delivery",
            "milestone_policy": "pain_discovery",
        }

    if intent == "solution_fit_question":
        return {
            "decision": "answer_solution_fit",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "explain_solution_fit_without_premature_demo",
            "milestone_policy": "solution_mapping",
        }

    if intent == "next_step_question":
        return {
            "decision": "answer_next_step",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "explain_next_step",
            "milestone_policy": "next_step_guidance",
        }

    if intent == "solution_method_question":
        return {
            "decision": "explain_solution_method",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "explain_practical_solution_method_without_overclaiming",
            "milestone_policy": "solution_mapping",
        }
        
    if intent == "technical_how_it_works_question":
        return {
            "decision": "answer_with_orbit",
            "knowledge_needed": True,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "answer_technical_workflow_question",
            "milestone_policy": "knowledge_required",
        }

    if intent == "human_request":
        return {
            "decision": "offer_escalation",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "offer_human_assistance",
            "milestone_policy": "hard_interrupt",
        }

    # ------------------------------------------------------------------
    # Business onboarding milestone
    # Goal: understand the visitor's business before deeper solution,
    # pricing, demo, quotation, or product mapping.
    # ------------------------------------------------------------------

    if current_milestone == "onboarding_business":

        if intent == "business_context_answer":
            accumulated = _accumulated
            challenge_text = accumulated.get("current_challenges") or ""
            if isinstance(challenge_text, list):
                challenge_text = ", ".join(str(c) for c in challenge_text if c)
            context_area = _detect_context_area_from_challenge(challenge_text)

            has_pain = bool(challenge_text)
            methodology_known = (
                _has_fact(accumulated, context_area, "current_methodology")
                or _has_fact(accumulated, context_area, "current_approach")
                or _has_fact(accumulated, context_area, "current_tool")
                or bool(accumulated.get("existing_systems"))
            )

            # Pain known but methodology not yet asked → ask methodology
            if has_pain and not methodology_known:
                return {
                    "decision": "discover_current_methodology",
                    "knowledge_needed": False,
                    "redirect_to_milestone": False,
                    "visitor_external_intent": intent,
                    "external_intent_confidence": confidence,
                    "internal_intent": "understand_current_approach_before_solution",
                    "milestone_policy": "pain_discovery",
                }

            # Pain known AND methodology known — check Nexus Orbit before drilling deeper
            if has_pain and methodology_known:
                biz_mfact = (
                    _find_fact(accumulated, context_area, "current_methodology")
                    or _find_fact(accumulated, context_area, "current_approach")
                    or _find_fact(accumulated, context_area, "current_tool")
                )
                if biz_mfact:
                    biz_methodology_value = str(biz_mfact.get("fact_value") or "").strip()
                else:
                    raw_sys = accumulated.get("existing_systems") or ""
                    biz_methodology_value = (
                        ", ".join(str(s) for s in raw_sys if s)
                        if isinstance(raw_sys, list)
                        else str(raw_sys)
                    ).strip()

                biz_methodology_checked = _has_fact(
                    accumulated, context_area, "methodology_knowledge_status",
                    related_value=biz_methodology_value,
                )

                if not biz_methodology_checked:
                    return {
                        "decision": "check_methodology_knowledge",
                        "knowledge_needed": True,
                        "redirect_to_milestone": False,
                        "visitor_external_intent": intent,
                        "external_intent_confidence": confidence,
                        "internal_intent": "verify_methodology_in_nexus_orbit_before_drill_down",
                        "milestone_policy": "pain_discovery",
                        "current_methodology": biz_methodology_value,
                        "methodology_context_area": context_area,
                        "pain_point_challenges": challenge_text,
                    }

                biz_status_fact = _find_fact(
                    accumulated, context_area, "methodology_knowledge_status",
                    related_value=biz_methodology_value,
                )
                if (
                    biz_status_fact
                    and str(biz_status_fact.get("fact_value") or "").lower()
                    in ["unsupported", "unconfirmed", "not_found"]
                ):
                    return {
                        "decision": "present_alternative_solution",
                        "knowledge_needed": True,
                        "redirect_to_milestone": False,
                        "visitor_external_intent": intent,
                        "external_intent_confidence": confidence,
                        "internal_intent": "present_nexus_approved_alternatives_for_challenge",
                        "milestone_policy": "pain_discovery",
                        "current_methodology": biz_methodology_value,
                        "methodology_context_area": context_area,
                        "pain_point_challenges": challenge_text,
                    }

            return {
                "decision": "continue_milestone",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "complete_business_onboarding",
                "milestone_policy": "accept_and_continue",
            }

        if intent == "business_scale_question":
            return {
                "decision": "answer_and_continue_onboarding",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "complete_business_onboarding",
                "milestone_policy": "supports_current_milestone",
            }

        if intent == "pricing_question":
            return {
                "decision": "brief_answer_then_redirect",
                "knowledge_needed": False,
                "redirect_to_milestone": True,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_business_context_before_pricing",
                "milestone_policy": "soft_deferral",
            }

        if intent == "demo_interest":
            return {
                "decision": "acknowledge_then_redirect",
                "knowledge_needed": False,
                "redirect_to_milestone": True,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_business_context_before_demo",
                "milestone_policy": "soft_deferral",
            }

        if intent == "product_question":
            return {
                "decision": "brief_answer_then_redirect",
                "knowledge_needed": True,
                "redirect_to_milestone": True,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "answer_lightly_then_return_to_business_onboarding",
                "milestone_policy": "allowed_interruption",
            }

        if intent == "off_topic":
            return {
                "decision": "redirect_to_milestone",
                "knowledge_needed": False,
                "redirect_to_milestone": True,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "keep_business_onboarding_on_track",
                "milestone_policy": "redirect",
            }

        return {
            "decision": "continue_milestone",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "complete_business_onboarding",
            "milestone_policy": "default_continue",
        }

    # ------------------------------------------------------------------
    # Other milestones / normal companion mode
    # ------------------------------------------------------------------

    if intent == "pricing_question":
        return {
            "decision": "answer_with_orbit_or_policy",
            "knowledge_needed": True,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "handle_pricing_question",
            "milestone_policy": "allowed",
        }

    if intent == "demo_interest":
        return {
            "decision": "consider_next_step",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "evaluate_demo_readiness",
            "milestone_policy": "allowed",
        }

    if intent == "product_question":
        return {
            "decision": "answer_with_orbit",
            "knowledge_needed": True,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "answer_product_question",
            "milestone_policy": "allowed",
        }

    return {
        "decision": "normal_companion",
        "knowledge_needed": _looks_like_product_or_policy_question(visitor_message),
        "redirect_to_milestone": False,
        "visitor_external_intent": intent,
        "external_intent_confidence": confidence,
        "internal_intent": "continue_companion_conversation",
        "milestone_policy": "default",
    }

def _apply_grounding_policy(steering):
    """
    Apply mandatory grounding mode for every controller decision.

    grounding_mode meanings:
    - nexus_knowledge_only: search Nexus Orbit and answer only from confirmed knowledge.
    - controller_only: LLM may draft wording, but only within controller/playbook guidance.
    - no_llm_direct: controller returns fixed response directly.
    """

    steering = steering or {}

    intent = steering.get("visitor_external_intent") or "unknown"
    decision = steering.get("decision") or ""

    nexus_knowledge_intents = {
        "solution_fit_question",
        "solution_method_question",
        "pricing_question",
        "product_question",
        "technical_how_it_works_question",
    }

    no_llm_direct_decisions = {
        "confirm_demo_request",
        "demo_rejected",
    }

    if decision in no_llm_direct_decisions:
        steering["grounding_mode"] = "no_llm_direct"
        steering["knowledge_needed"] = False
        return steering

    nexus_knowledge_decisions = {
        "answer_solution_fit",
        "explain_solution_method",
        "check_methodology_knowledge",
        "present_alternative_solution",
        "present_nexy_capability_summary",
    }
    if decision in nexus_knowledge_decisions:
        steering["grounding_mode"] = "nexus_knowledge_only"
        steering["knowledge_needed"] = True
        return steering

    if intent in nexus_knowledge_intents:
        steering["grounding_mode"] = "nexus_knowledge_only"
        steering["knowledge_needed"] = True
        return steering

    steering["grounding_mode"] = "controller_only"
    steering["knowledge_needed"] = False
    return steering

def _looks_like_product_or_policy_question(message):
    text = (message or "").lower()
    keywords = [
        "feature", "module", "policy", "process", "implementation",
        "integration", "support", "security", "pricing", "price",
        "service", "product", "capability",
    ]
    return any(k in text for k in keywords)


def _answer_with_orbit(core_payload, visitor_message, steering):
    """
    Uses existing Nexus Orbit answer pipeline only when controller decides.
    """
    orbit_payload = dict(core_payload)
    orbit_payload["query"] = visitor_message
    orbit_payload["original_query"] = visitor_message
    orbit_payload["response_mode"] = "chat"

    response = answer_query(orbit_payload)

    answer = response.get("answer") or ""

    if steering.get("redirect_to_milestone"):
        answer = (
            f"{answer}\n\n"
            "To guide you properly, could you also tell me a little about your business "
            "and the main challenge you are trying to solve?"
        )

    response["chat_mode"] = "companion_controller_orbit"
    return response


def _draft_companion_response(
    conversation,
    agent,
    visitor_message,
    current_milestone,
    steering,
    discovery_delta,
    signal,
):
    prompt = f"""
You are Nexy, a business companion.

You are NOT answering from external knowledge.
You must not invent product facts, pricing, policies, or guarantees.

Current milestone:
{current_milestone}

Controller decision:
{json.dumps(steering, indent=2)}

Visitor message:
{visitor_message}

New business information extracted:
{json.dumps(discovery_delta, indent=2)}

Visitor signal:
{json.dumps(signal, indent=2)}

Response rules:
- Be warm, natural, and concise.
- Respect the visitor's message.
- Keep the conversation aligned with the current milestone.
- If the visitor asked pricing/demo before business context is known, acknowledge briefly and guide back.
- Ask only ONE question.
- Do not mention "milestone", "controller", "internal intent", or "steering".

Draft the next response.
"""

    answer = (generate_answer(prompt) or "").strip()

    if not answer:
        answer = (
            "Thanks for sharing that. To guide you properly, could you tell me what your "
            "business does and what challenge you are mainly trying to solve?"
        )

    return answer


def _maybe_advance_milestone(conversation):
    """
    Advance companion_milestone when discovery criteria are met.
    Writes companion_milestone on the conversation (and syncs to enquiry via
    _publish_progress_update so the desk reflects it immediately).
    """
    try:
        current_milestone = _get_current_milestone(conversation)

        if current_milestone != "onboarding_business":
            return

        enquiry_name = getattr(conversation, "companion_enquiry", None)
        if not enquiry_name:
            return

        discovery_raw = frappe.db.get_value(
            "Nexus Companion Enquiry",
            enquiry_name,
            "discovery_data",
        ) or "{}"

        try:
            discovery = json.loads(discovery_raw)
        except Exception:
            discovery = {}

        required = ["industry", "current_challenges"]

        if all(discovery.get(k) for k in required):
            new_milestone = "business_discovery"
            frappe.db.set_value(
                "Nexus Live Conversation",
                conversation.name,
                "companion_milestone",
                new_milestone,
                update_modified=False,
            )
            if enquiry_name:
                frappe.db.set_value(
                    "Nexus Companion Enquiry",
                    enquiry_name,
                    "companion_milestone",
                    new_milestone,
                    update_modified=False,
                )
            _publish_progress_update(conversation, new_milestone=new_milestone)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: milestone advancement failed",
        )


def _publish_progress_update(conversation, new_milestone=None):
    """
    Push a realtime event to the desk so the Companion Dashboard can update
    the funnel count and enquiry row without a full page refresh.
    """
    try:
        enquiry_name = getattr(conversation, "companion_enquiry", None)
        stage = frappe.db.get_value(
            "Nexus Live Conversation",
            conversation.name,
            "companion_journey_stage",
        ) or ""
        milestone = new_milestone or frappe.db.get_value(
            "Nexus Live Conversation",
            conversation.name,
            "companion_milestone",
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
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: realtime publish failed",
        )
        
def _detect_pending_action(conversation_context):
    """
    Detect whether Nexy already offered a next action like demo request.
    """

    text = (conversation_context or "").lower()

    demo_confirmed_markers = [
        "i'll go ahead and arrange",
        "i will go ahead and arrange",
        "demo request has been",
        "demo request is confirmed",
        "consultant will reach out",
        "consultant will contact you",
    ]

    if any(marker in text for marker in demo_confirmed_markers):
        return "demo_already_confirmed"

    demo_offer_markers = [
        "submit a demo request",
        "would you like to proceed",
        "would you like to submit a demo",
        "arrange the demo",
        "arrange a demo",
        "nexus consultant will contact",
        "comprehensive demo",
        "detailed walkthrough",
    ]

    if any(marker in text for marker in demo_offer_markers):
        return "demo_request"

    handoff_markers = [
        "connect you with our team",
        "connect with a representative",
        "speak with someone",
        "human agent",
        "team member",
    ]

    if any(marker in text for marker in handoff_markers):
        return "human_handoff"

    return None

def _handle_demo_confirmation(conversation):
    """
    Demo accepted. Do not ask again.
    """

    try:
        frappe.db.set_value(
            "Nexus Live Conversation",
            conversation.name,
            "intent",
            "demo_arrangement",
            update_modified=False,
        )

        if getattr(conversation, "companion_enquiry", None):
            frappe.db.set_value(
                "Nexus Companion Enquiry",
                conversation.companion_enquiry,
                "recommended_next_step",
                "demo_request_confirmed",
                update_modified=False,
            )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: demo confirmation update failed",
        )

    if not getattr(conversation, "visitor_email", None):
        answer = (
            "Great. The next step is to arrange a focused demo around your requirement. "
            "Could you please share your email address so we can verify it and create the demo request?"
        )

        return {
            "status": "success",
            "access_status": "intent_handled",
            "answer": answer,
            "confidence": 1.0,
            "sources": [],
            "citations": [],
            "retrieval_result": {},
            "fallback_used": 0,
            "chat_mode": "controlled_companion_direct",
            "companion_controller": True,
            "conversion_action": None,
            "email_followup_offer": True,
        }

    answer = (
        "Great. I’ll create the demo request now. Our Nexus Consultant will contact you "
        "using your registered details to arrange a focused walkthrough."
    )

    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": answer,
        "confidence": 1.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": {
            "type": "demo_request",
            "status": "confirmed",
            "title": "Demo request confirmed",
            "message": "A Nexus Consultant will contact the visitor to arrange the demo.",
        },
    }

def _handle_demo_rejection(conversation):
    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": (
            "No problem. We can continue exploring your requirement first. "
            "What would you like to understand better — recruitment outreach, candidate follow-up, "
            "or how Nexus can support your operations?"
        ),
        "confidence": 1.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": None,
    }


def _handle_next_step_question(conversation, pending_action=None):
    if pending_action == "demo_already_confirmed":
        if not getattr(conversation, "visitor_email", None):
            answer = (
                "The next step is to collect and verify your email so the demo request can be created. "
                "Could you please share your email address?"
            )
        else:
            answer = (
                "The next step is for our Nexus Consultant to contact you and arrange the demo. "
                "The walkthrough should focus on your requirement and the challenge you shared."
            )

        return {
            "status": "success",
            "access_status": "intent_handled",
            "answer": answer,
            "confidence": 1.0,
            "sources": [],
            "citations": [],
            "retrieval_result": {},
            "fallback_used": 0,
            "chat_mode": "controlled_companion_direct",
            "companion_controller": True,
            "conversion_action": None,
        }

    if pending_action == "demo_request":
        return _handle_demo_confirmation(conversation)

    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": (
            "The next practical step is to understand your requirement a little more clearly, "
            "then decide whether a focused demo is useful. For your case, we should look at "
            "your current process, where the difficulty is happening, and what outcome you want first."
        ),
        "confidence": 1.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": None,
    }