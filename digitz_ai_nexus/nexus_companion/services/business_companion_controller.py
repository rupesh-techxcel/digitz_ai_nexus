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

    update_enquiry(
        conversation=conversation,
        discovery_delta=discovery_delta,
        signal=signal,
    )

    advance_journey_stage_from_signal(
        conversation,
        signal.get("signal_type", "CURIOUS"),
    )

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

    if not isinstance(response, dict):
        response = {}

    if steering.get("decision") == "offer_escalation":
        response["user_requested_human"] = True
        response["intent_action"] = "escalate"

    response["companion_controller"] = True
    response["conversion_action"] = None

    _maybe_advance_milestone(conversation)

    return response    
  
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
            "Acknowledge what the visitor shared and ask the next best onboarding question."
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
    
    if decision == "answer_solution_fit":
        return (
            "Explain how Nexus can help with the visitor's stated problem without jumping to demo. "
            "For lead generation or ads, do not claim direct ad-platform optimization unless confirmed. "
            "Frame the answer around customer profile, lead capture, enquiry qualification, response speed, "
            "follow-up, tracking, and conversion improvement. Ask one diagnostic question at the end."
        )
    
    if decision == "explain_solution_method":
        return (
            "Explain practically how the suggested solution area can be approached. "
            "Use the visitor's business context. Do not claim confirmed automation, Facebook API integration, "
            "or direct ad-platform control unless permitted knowledge confirms it. "
            "For customer profiling, explain identifying customer segments, service areas, property types, "
            "lead quality patterns, and conversion patterns. For lead capture, explain capturing ad enquiries, "
            "structuring them, qualifying them, assigning follow-up, and tracking conversion. "
            "Ask one clear diagnostic question at the end."
        )

    return "Continue the companion conversation naturally while following the current milestone."

def _get_current_milestone(conversation):
    """
    Resolve controller milestone from conversation state.

    IMPORTANT:
    companion_journey_stage is a funnel/reporting stage.
    intent is currently being used as the controller milestone.

    Later, replace this with a dedicated companion_milestone field.
    """

    intent = (getattr(conversation, "intent", None) or "").strip()

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

    if intent in business_milestones:
        return intent

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

Return ONLY valid JSON.
Allowed keys:
company_name, industry, company_size, team_size, business_type,
business_maturity, current_challenges, goals, existing_systems,
budget_range, timeline, decision_maker

If nothing is found, return {{}}.
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

def _decide_steering(
    conversation,
    visitor_message,
    current_milestone,
    signal,
    discovery_delta,
    external_intent,
    pending_action=None,
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
    Initial basic milestone advancement rule.
    Later move to Milestone Engine.
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
            frappe.db.set_value(
                "Nexus Live Conversation",
                conversation.name,
                "intent",
                "business_discovery",
                update_modified=False,
            )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: milestone advancement failed",
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