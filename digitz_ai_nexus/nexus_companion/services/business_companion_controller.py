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


def _companion_flow_debug(stage, data=None):
    """
    Compact debug for Nexy Companion flow.
    Shows intent, steering, decision reason, and response state only.
    """
    try:
        print("\n\n========== NEXY FLOW:", stage, "==========")
        if data is not None:
            print(json.dumps(data, indent=2, default=str))
        print("=========================================\n\n")

        try:
            frappe.logger("nexus_debug").info({
                "stage": stage,
                "data": data,
            })
        except Exception:
            pass

    except Exception:
        print("\n\n========== NEXY FLOW DEBUG FAILED ==========")
        print(stage)
        print(str(data))
        print("===========================================\n\n")


def _preview_text(value, limit=350):
    value = str(value or "").strip()
    if len(value) > limit:
        return value[:limit] + "..."
    return value


def _summarise_discovery(discovery):
    discovery = discovery or {}
    facts = discovery.get("discovery_facts") or []

    fact_summary = []
    if isinstance(facts, list):
        for fact in facts[:8]:
            fact_summary.append({
                "context_area": fact.get("context_area"),
                "fact_type": fact.get("fact_type"),
                "fact_value": fact.get("fact_value"),
                "related_value": fact.get("related_value"),
            })

    return {
        "company_name": discovery.get("company_name"),
        "industry": discovery.get("industry"),
        "business_type": discovery.get("business_type"),
        "current_challenges": discovery.get("current_challenges"),
        "goals": discovery.get("goals"),
        "existing_systems": discovery.get("existing_systems"),
        "timeline": discovery.get("timeline"),
        "fact_summary": fact_summary,
    }


def _explain_steering_reason(
    visitor_message,
    current_milestone,
    pending_action,
    signal,
    external_intent,
    steering,
):
    """
    Human-readable reason for why the controller selected a decision.
    This is debug-only and should not affect runtime behaviour.
    """
    external_intent = external_intent or {}
    steering = steering or {}
    signal = signal or {}

    decision = steering.get("decision")
    ext_intent = external_intent.get("intent")
    ext_conf = external_intent.get("confidence")
    signal_type = signal.get("signal_type")

    if pending_action:
        reason = (
            f"Existing pending_action='{pending_action}' influenced the next move. "
            f"External intent was '{ext_intent}' with confidence {ext_conf}."
        )
    elif ext_intent and ext_intent != "unknown":
        reason = (
            f"External intent classifier detected '{ext_intent}' with confidence {ext_conf}. "
            f"Controller mapped it to decision='{decision}'."
        )
    else:
        reason = (
            f"No strong external intent. Controller continued based on milestone='{current_milestone}', "
            f"signal='{signal_type}', and discovery state."
        )

    return {
        "reason": reason,
        "visitor_message": visitor_message,
        "current_milestone": current_milestone,
        "pending_action": pending_action,
        "signal_type": signal_type,
        "external_intent": ext_intent,
        "external_intent_confidence": ext_conf,
        "steering_decision": decision,
        "internal_intent": steering.get("internal_intent"),
        "milestone_policy": steering.get("milestone_policy"),
        "knowledge_needed": steering.get("knowledge_needed"),
        "grounding_mode": steering.get("grounding_mode"),
    }

def _get_companion_db_status(conversation):
    """
    Reads current DB state directly, so we can confirm whether conversation doc cache is stale.
    Does not print OTP/hash value directly.
    """
    try:
        row = frappe.db.get_value(
            "Nexus Live Conversation",
            conversation.name,
            [
                "visitor_email",
                "companion_email_verified",
                "companion_pending_action",
                "companion_pending_context_json",
                "companion_email_verification_hash",
                "companion_email_verification_expires_on",
                "companion_email_verification_retry_count",
                "companion_milestone",
                "companion_journey_stage",
                "chat_category",
                "assigned_agent",
            ],
            as_dict=True,
        ) or {}

        return {
            "conversation": conversation.name,
            "visitor_email": row.get("visitor_email"),
            "companion_email_verified": row.get("companion_email_verified"),
            "companion_pending_action": row.get("companion_pending_action"),
            "companion_pending_context_json": row.get("companion_pending_context_json"),
            "has_email_verification_hash": bool((row.get("companion_email_verification_hash") or "").strip()),
            "companion_email_verification_expires_on": row.get("companion_email_verification_expires_on"),
            "companion_email_verification_retry_count": row.get("companion_email_verification_retry_count"),
            "companion_milestone": row.get("companion_milestone"),
            "companion_journey_stage": row.get("companion_journey_stage"),
            "chat_category": row.get("chat_category"),
            "assigned_agent": row.get("assigned_agent"),
        }
    except Exception:
        return {
            "conversation": getattr(conversation, "name", None),
            "db_status_error": frappe.get_traceback(),
        }


def _is_nexy_companion_conversation(conversation, agent=None):
    """
    Strong check to identify Nexy Companion flow.
    Do not depend only on the in-memory conversation object.
    """
    try:
        if bool(getattr(agent, "companion_mode", 0)):
            return True
    except Exception:
        pass

    agent_name = _get_conversation_assigned_agent(conversation)
    agent_key = agent_name.upper()

    return (
        agent_name == "NEXY-COMPANION-NEXUS-AI"
        or "NEXY-COMPANION" in agent_key
    )

def _identity_verified_system_message(message):
    """
    Detect system/frontend verification callback messages.

    These messages only mean verification completed.
    They are not the visitor's representative note.
    """
    msg = (message or "").lower().strip()

    if not msg:
        return False

    return (
        "identity verified" in msg
        or "preparing your booking" in msg
        or "verification completed" in msg
        or msg in {
            "verified",
            "email verified",
            "identity verified",
        }
    )
    
def _handle_verified_representative_note_message(conversation, visitor_message, accumulated_discovery):
    """
    Handles the visitor's representative note after email/identity is verified.
    The visitor may type an actual note or 'skip'.
    """
    if _is_note_ack_only(visitor_message):
        return {
            "status": "success",
            "access_status": "intent_handled",
            "answer": (
                'Sure. Please type the note or question you want the representative to see, '
                'or type "skip" to proceed without one.'
            ),
            "confidence": 1.0,
            "sources": [],
            "citations": [],
            "retrieval_result": {},
            "fallback_used": 0,
            "chat_mode": "controlled_companion_direct",
            "companion_controller": True,
            "conversion_action": None,
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

    return _handle_show_meeting_booking_card(
        conversation=conversation,
        accumulated_discovery=accumulated_discovery,
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
    # Stored pending action always wins over text scanning — prevents false
    # demo_request detection when old conversation text contains legacy markers.
    _stored_pending = _get_companion_pending_action(conversation)

    _payload_pending = (
        payload.get("pending_action")
        or payload.get("companion_pending_action")
        or core_payload.get("pending_action")
        or core_payload.get("companion_pending_action")
        or ""
    ).strip()

    _detected_pending = _detect_pending_action(conversation_context)

    _ctx_low = (conversation_context or "").lower()

    _note_stage_hint = (
        _payload_pending == "collect_representative_note"
        or _detected_pending == "collect_representative_note"
        or (
            "would you like to add a note or question" in _ctx_low
            and (
                'type "skip"' in _ctx_low
                or "type 'skip'" in _ctx_low
                or "type skip" in _ctx_low
                or "skip" in _ctx_low
            )
        )
    )

    _stale_email_pending = _stored_pending in {
        "collect_email_for_consultancy",
        "verify_email_for_consultancy",
        "collect_email_for_appointment",
        "verify_email_for_appointment",
    }

    # If the user is clearly replying to the representative-note prompt,
    # do not let stale email pending action hijack the meaning of "skip".
    if _note_stage_hint and _stale_email_pending:
        pending_action = "collect_representative_note"
    else:
        pending_action = _stored_pending or _payload_pending or _detected_pending
    _companion_flow_debug("01 TURN START", {
        "conversation": getattr(conversation, "name", None),
        "visitor_message": visitor_message,
        "current_milestone": current_milestone,
        "stored_pending_action": _stored_pending,
        "detected_pending_action": _detect_pending_action(conversation_context),
        "pending_action_used": pending_action,
        "conversation_context_tail": _preview_text(conversation_context[-1000:], 1000),
    })
    
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
    
    # IDV HANDOFF:
    # If frontend sends verified identity challenge token, stamp the Companion booking state first.
    # This must run before representative-note guard because stale DB may still say collect_email_for_consultancy.
    _idv_challenge_token = (
        payload.get("identity_verification_challenge")
        or payload.get("identity_verification_token")
        or payload.get("identity_challenge_token")
        or payload.get("verification_challenge")
        or payload.get("verified_challenge_token")
        or payload.get("challenge_token")
        or core_payload.get("identity_verification_challenge")
        or core_payload.get("identity_verification_token")
        or core_payload.get("identity_challenge_token")
        or core_payload.get("verification_challenge")
        or core_payload.get("verified_challenge_token")
        or core_payload.get("challenge_token")
        or ""
    ).strip()

    if _idv_challenge_token and pending_action in {
        "collect_email_for_consultancy",
        "verify_email_for_consultancy",
        "collect_email_for_appointment",
        "verify_email_for_appointment",
        "collect_representative_note",
    }:
        try:
            from digitz_ai_nexus_live.services.identity_verification import get_verified_challenge

            _idv_challenge = get_verified_challenge(
                challenge_token=_idv_challenge_token,
                chat_category=getattr(conversation, "chat_category", None),
            )

            if _idv_challenge:
                _verified_context = {
                    "email": _idv_challenge.email,
                    "verified_via": "idv_challenge",
                }

                frappe.db.set_value(
                    "Nexus Live Conversation",
                    conversation.name,
                    {
                        "visitor_email": _idv_challenge.email,
                        "companion_email_verified": 1,
                        "companion_pending_action": "collect_representative_note",
                        "companion_pending_context_json": json.dumps(_verified_context, default=str),
                    },
                    update_modified=False,
                )

                # Mirror DB state to current in-memory doc also.
                try:
                    conversation.visitor_email = _idv_challenge.email
                    conversation.companion_email_verified = 1
                    conversation.companion_pending_action = "collect_representative_note"
                    conversation.companion_pending_context_json = json.dumps(_verified_context, default=str)
                except Exception:
                    pass

                update_enquiry(
                    conversation,
                    {"discovery_facts": [{
                        "context_area": "general_business",
                        "fact_type": "email_verification_status",
                        "fact_value": "verified",
                        "source_message": _idv_challenge.email,
                    }]},
                    signal=None,
                )

                pending_action = "collect_representative_note"

                _set_companion_pending_action(
                    conversation,
                    "collect_representative_note",
                    {
                        "email": _idv_challenge.email,
                        "verified_via": "idv_challenge",
                    },
                )

                frappe.db.commit()

                # If this request is only the frontend/system verification callback,
                # show the note prompt.
                if _identity_verified_system_message(visitor_message):
                    return {
                        "status": "success",
                        "access_status": "intent_handled",
                        "answer": (
                            'Before I proceed, would you like to add a note or question for the Nexy representative? '
                            'This helps them understand what you want reviewed. You can also type "skip".'
                        ),
                        "confidence": 1.0,
                        "sources": [],
                        "citations": [],
                        "retrieval_result": {},
                        "fallback_used": 0,
                        "chat_mode": "controlled_companion_direct",
                        "companion_controller": True,
                        "conversion_action": None,
                        "verification_stage": "verified",
                        "pending_action": "collect_representative_note",
                        "companion_email_verified": True,
                    }

                # If this request contains the actual visitor note/skip,
                # process it immediately instead of asking again.
                return _handle_verified_representative_note_message(
                    conversation=conversation,
                    visitor_message=visitor_message,
                    accumulated_discovery=accumulated_discovery,
                )

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "Companion: challenge token verification failed",
            )
    
    # HARD GUARD:
    # If email is already verified and we are in the representative-note stage,
    # do not allow old demo_request / legacy confirmation routing.
    # This must run before normal steering.
    if (
        _is_booking_email_verified(conversation)
        and _is_verified_note_turn(
            conversation=conversation,
            conversation_context=conversation_context,
            pending_action=pending_action,
            payload=payload,
            core_payload=core_payload,
        )
    ):
        if _is_note_ack_only(visitor_message):
            return {
                "status": "success",
                "access_status": "intent_handled",
                "answer": (
                    'Sure. Please type the note or question you want the representative to see, '
                    'or type "skip" to proceed without one.'
                ),
                "confidence": 1.0,
                "sources": [],
                "citations": [],
                "retrieval_result": {},
                "fallback_used": 0,
                "chat_mode": "controlled_companion_direct",
                "companion_controller": True,
                "conversion_action": None,
                "pending_action": "collect_representative_note",
            }

        _note_value = "skipped" if _is_skip_note(visitor_message) else visitor_message[:500]

        update_enquiry(
            conversation,
            {"discovery_facts": [{
                "context_area": "general_business",
                "fact_type": "representative_note_collected",
                "fact_value": _note_value,
                "source_message": visitor_message,
            }]},
            signal=None,
        )

        _clear_companion_pending_action(conversation)

        return _handle_show_meeting_booking_card(
            conversation=conversation,
            accumulated_discovery=accumulated_discovery,
        )
    
    # _companion_flow_debug("03 DISCOVERY + SIGNAL", {
    #     "signal": signal,
    #     "discovery_delta": _summarise_discovery(discovery_delta),
    #     "accumulated_discovery": _summarise_discovery(accumulated_discovery),
    # })

    
    if _idv_challenge_token and pending_action in (
        "collect_email_for_consultancy",
        "verify_email_for_consultancy",
    ):
        try:
            from digitz_ai_nexus_live.services.identity_verification import get_verified_challenge
            _idv_challenge = get_verified_challenge(
                challenge_token=_idv_challenge_token,
                chat_category=getattr(conversation, "chat_category", None),
            )
            if _idv_challenge:
                _verified_context = {
                    "email": _idv_challenge.email,
                    "verified_via": "idv_challenge",
                }

                frappe.db.set_value(
                    "Nexus Live Conversation",
                    conversation.name,
                    {
                        "visitor_email": _idv_challenge.email,
                        "companion_email_verified": 1,
                        "companion_pending_action": "collect_representative_note",
                        "companion_pending_context_json": json.dumps(_verified_context, default=str),
                    },
                    update_modified=False,
                )
                update_enquiry(
                    conversation,
                    {"discovery_facts": [{
                        "context_area": "general_business",
                        "fact_type": "email_verification_status",
                        "fact_value": "verified",
                        "source_message": _idv_challenge.email,
                    }]},
                    signal=None,
                )
                
                pending_action = "collect_representative_note"
                _set_companion_pending_action(
                    conversation,
                    "collect_representative_note",
                    {"email": _idv_challenge.email, "verified_via": "idv_challenge"},
                )
                frappe.db.commit()
                
                return {
                    "status": "success",
                    "access_status": "intent_handled",
                    "answer": (
                        'Before I proceed, would you like to add a note or question for the Nexy representative? '
                        'This helps them understand what you want reviewed. You can also type "skip".'
                    ),
                    "confidence": 1.0,
                    "sources": [],
                    "citations": [],
                    "retrieval_result": {},
                    "fallback_used": 0,
                    "chat_mode": "controlled_companion_direct",
                    "companion_controller": True,
                    "conversion_action": None,
                    "verification_stage": "verified",
                    "pending_action": "collect_representative_note",
                    "companion_email_verified": True,
                }
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "Companion: challenge token verification failed",
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
    
    # Defensive override:
    # Once email is verified and note stage is active, never allow legacy demo_request.
    if (        
        _is_booking_email_verified(conversation)
            and _is_verified_note_turn(
                conversation=conversation,
                conversation_context=conversation_context,
                pending_action=pending_action,
                payload=payload,
                core_payload=core_payload,
            )
            and steering.get("decision") in {
            "confirm_demo_request",
            "collect_email_for_consultancy",
            "collect_email_for_appointment",
            "verify_email_for_consultancy",
            "verify_email_for_appointment",
            "close_conversation",
        }
    ):
        steering["decision"] = "show_meeting_booking_card"
        steering["knowledge_needed"] = False
        steering["grounding_mode"] = "controller_only"
        steering["internal_intent"] = "force_booking_card_after_verified_note_stage"
        steering["milestone_policy"] = "appointment_booking"
    
    _companion_flow_debug("04 STEERING DECISION", {
    "decision_reason": _explain_steering_reason(
        visitor_message=visitor_message,
        current_milestone=current_milestone,
        pending_action=pending_action,
        signal=signal,
        external_intent=external_intent,
        steering=steering,
    ),
    "steering": {
        "decision": steering.get("decision"),
        "visitor_external_intent": steering.get("visitor_external_intent"),
        "external_intent_confidence": steering.get("external_intent_confidence"),
        "internal_intent": steering.get("internal_intent"),
        "milestone_policy": steering.get("milestone_policy"),
        "knowledge_needed": steering.get("knowledge_needed"),
        "grounding_mode": steering.get("grounding_mode"),
        "current_methodology": steering.get("current_methodology"),
        "methodology_context_area": steering.get("methodology_context_area"),
        "pain_point_challenges": steering.get("pain_point_challenges"),
        "lead_entry_point": steering.get("lead_entry_point"),
        "selected_capability_area": steering.get("selected_capability_area"),
        "check_matching_capability_reason": steering.get("internal_intent"),
        "capability_fit_context_area": steering.get("methodology_context_area"),
        "capability_fit_challenge": steering.get("pain_point_challenges"),
    },
})
    
    frappe.logger("nexus_debug").info({
        "visitor_message": visitor_message,
        "external_intent": external_intent,
        "steering": steering,
        "pending_action": pending_action,
    })

    if steering.get("decision") == "show_meeting_booking_card":
        _clear_companion_pending_action(conversation)
        return _handle_show_meeting_booking_card(conversation, accumulated_discovery)

    from digitz_ai_nexus.engine.chat_agent_loop import run_controlled_companion_loop
    
    
    if steering.get("decision") == "confirm_demo_request":
        # Nexy Companion must never use the old legacy demo confirmation flow.
        # If email is already verified, show the Calendly booking card directly.
        # If not verified, continue with email verification.
       
        if _is_nexy_companion_conversation(conversation, agent):
            if _is_booking_email_verified(conversation):
                _clear_companion_pending_action(conversation)
                return _handle_show_meeting_booking_card(conversation, accumulated_discovery)

            steering["decision"] = "collect_email_for_consultancy"
            steering["knowledge_needed"] = False
            steering["grounding_mode"] = "controller_only"

        elif pending_action == "collect_representative_note":
            steering["decision"] = "collect_representative_note"
            steering["knowledge_needed"] = False
            steering["grounding_mode"] = "controller_only"

        elif pending_action in {
            "collect_email_for_consultancy",
            "verify_email_for_consultancy",
        }:
            steering["decision"] = "collect_email_for_consultancy"
            steering["knowledge_needed"] = False
            steering["grounding_mode"] = "controller_only"

        elif pending_action in {
            "ask_more_clarification_or_consultancy",
            "appointment_declined_collect_note",
            "email_declined_collect_note",
            "capture_closing_feedback",
        }:
            steering["decision"] = "collect_email_for_consultancy"
            steering["knowledge_needed"] = False
            steering["grounding_mode"] = "controller_only"

        else:
            return _handle_demo_confirmation(conversation)

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
        "current_methodology_status": steering.get("current_methodology_status") or "",
        "lead_entry_point": steering.get("lead_entry_point") or "",
        "selected_capability_area": steering.get("selected_capability_area") or "",
        "methodology_context_area": steering.get("methodology_context_area") or "",
        "business_context": steering.get("business_context") or "",
    }
    
    # _companion_flow_debug("05 CONTROLLER PLAN", {
    #     "steering_decision": controller_plan.get("steering_decision"),
    #     "external_intent": controller_plan.get("external_intent"),
    #     "external_intent_confidence": controller_plan.get("external_intent_confidence"),
    #     "internal_intent": controller_plan.get("internal_intent"),
    #     "milestone_policy": controller_plan.get("milestone_policy"),
    #     "knowledge_needed": controller_plan.get("knowledge_needed"),
    #     "grounding_mode": controller_plan.get("grounding_mode"),
    #     "allowed_tools": controller_plan.get("allowed_tools"),
    #     "allow_escalation": controller_plan.get("allow_escalation"),
    #     "allow_conversion_action": controller_plan.get("allow_conversion_action"),
    #     "knowledge_query": _preview_text(controller_plan.get("knowledge_query"), 700),
    #     "response_goal": _preview_text(controller_plan.get("response_goal"), 700),
    # })
    
    if steering.get("decision") == "demo_rejected":
        return _handle_demo_rejection(conversation)

    if steering.get("decision") == "answer_next_step":
        return _handle_next_step_question(conversation, pending_action)

    if steering.get("decision") == "capability_menu_declined":
        _clear_companion_pending_action(conversation)

        _companion_flow_debug("CAPABILITY MENU DECLINED", {
            "conversation": conversation.name,
            "visitor_message": visitor_message,
            "challenge": steering.get("pain_point_challenges"),
            "context_area": steering.get("methodology_context_area"),
            "pending_action_cleared": True,
        })

        return {
            "status": "success",
            "access_status": "intent_handled",
            "answer": (
                "Understood. I do not want to force a fit where there is none.\n\n"
                "I will stop here for now. If you later want help with visitor conversation, "
                "requirement discovery, enquiry qualification, or representative handoff, I can assist."
            ),
            "confidence": 1.0,
            "sources": [],
            "citations": [],
            "retrieval_result": {},
            "fallback_used": 0,
            "chat_mode": "controlled_companion_direct",
            "companion_controller": True,
            "conversion_action": None,
            "pending_action": "",
        }

    # Unclear capability-menu selection — repeat the controller-owned menu
    # deterministically instead of letting the LLM improvise. The stored
    # pending action stays select_nexy_capability_area.
    if (
        steering.get("decision") == "bounce_back_to_nexy_capabilities"
        and steering.get("internal_intent") == "visitor_selection_unclear"
    ):
        return _handle_no_matching_capability_menu(
            steering.get("pain_point_challenges"),
            repeat=True,
            playbook=_get_companion_playbook_doc(conversation, agent),
        )

    # Persist collect_current_methodology BEFORE the LLM responds so the next
    # visitor turn always reads it from DB, even if the response path is async.
    if steering.get("decision") == "discover_current_methodology":
        _set_companion_pending_action(
            conversation,
            "collect_current_methodology",
            {
                "decision": "discover_current_methodology",
                "context_area": steering.get("methodology_context_area")
                or _infer_context_area_from_challenge(steering.get("pain_point_challenges") or ""),
                "expected_slot": "current_methodology",
                "challenge": steering.get("pain_point_challenges") or "",
                "asked_by_decision": "discover_current_methodology",
            },
        )

    # Playbook-owned capability summary: the primary pitch renders
    # deterministically from the playbook's capability items — identical in
    # every conversation, no LLM. Falls back to the knowledge-grounded LLM
    # path when no playbook items are configured. Knowledge sources remain
    # the grounding for drill-down clarification questions.
    _pcs_playbook = None
    if steering.get("decision") == "present_nexy_capability_visibility":
        _pcs_playbook = _get_companion_playbook_doc(conversation, agent)

    if _pcs_playbook and _get_playbook_capability_items(_pcs_playbook):
        response = _build_playbook_capability_summary(steering, _pcs_playbook)
        _companion_flow_debug("CAPABILITY SUMMARY FROM PLAYBOOK", {
            "conversation": conversation.name,
            "playbook": _pcs_playbook.name,
            "item_count": len(_get_playbook_capability_items(_pcs_playbook)),
            "methodology": steering.get("current_methodology"),
            "methodology_status": steering.get("current_methodology_status"),
        })
    else:
        response = run_controlled_companion_loop(
            payload=loop_payload,
            controller_plan=controller_plan,
        )

        if steering.get("decision") == "present_nexy_capability_visibility":
            response = _ensure_nexy_capability_visibility_response(response, steering)

    _companion_flow_debug("06 CONTROLLED LOOP RESPONSE", {
        "steering_decision": steering.get("decision"),
        "answer": _preview_text(response.get("answer") if isinstance(response, dict) else None, 700),
        "access_status": response.get("access_status") if isinstance(response, dict) else None,
        "fallback_used": response.get("fallback_used") if isinstance(response, dict) else None,
        "chat_mode": response.get("chat_mode") if isinstance(response, dict) else None,
        "companion_controller": response.get("companion_controller") if isinstance(response, dict) else None,
    })
    
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

    # When the capability-fit check finds no confirmed matching capability,
    # never let the LLM improvise — return the controller-owned capability menu
    # and wait for the visitor to pick a supported area.
    if (
        steering.get("decision") == "check_matching_capability"
        and isinstance(response, dict)
        and response.get("access_status") in {"controlled_no_context", "no_context", "low_confidence", "restricted"}
    ):
        _set_companion_pending_action(
            conversation,
            "select_nexy_capability_area",
            {
                "reason": "no_matching_capability",
                "challenge": steering.get("pain_point_challenges") or "",
                "context_area": steering.get("methodology_context_area") or "general_business",
            },
        )

        _companion_flow_debug("CAPABILITY FIT NO MATCH", {
            "conversation": conversation.name,
            "challenge": steering.get("pain_point_challenges"),
            "context_area": steering.get("methodology_context_area"),
            "access_status": response.get("access_status"),
            "pending_action": "select_nexy_capability_area",
        })

        return _handle_no_matching_capability_menu(
            steering.get("pain_point_challenges"),
            playbook=_get_companion_playbook_doc(conversation, agent),
        )

    if not isinstance(response, dict):
        response = {}

    if steering.get("decision") == "offer_escalation":
        response["user_requested_human"] = True
        response["intent_action"] = "escalate"

    # Persist nexy_capability_summary_presented fact after a grounded capability visibility response
    if (
        steering.get("decision") == "present_nexy_capability_visibility"
        and response.get("access_status") not in ("controlled_no_context", "restricted")
        and response.get("answer")
    ):
        _cap_context_area = steering.get("methodology_context_area") or "general_business"
        _cap_methodology = steering.get("current_methodology") or ""
        update_enquiry(
            conversation,
            {"discovery_facts": [{
                "context_area": _cap_context_area,
                "fact_type": "nexy_capability_summary_presented",
                "fact_value": "yes",
                "related_value": _cap_methodology,
                "source_message": "controller",
            }]},
            signal=None,
        )
        response["nexy_capability_visibility"] = True
        response["capability_summary_presented"] = True

    # Persist capability_clarification_count after each grounded clarification response
    if (
        steering.get("decision") == "answer_nexy_capability_clarification"
        and response.get("access_status") not in ("controlled_no_context", "restricted")
        and response.get("answer")
    ):
        _clr_ctx = steering.get("methodology_context_area") or "general_business"
        _clr_count = int(
            _get_fact_value(accumulated_discovery or {}, _clr_ctx, "capability_clarification_count") or "0"
        )
        update_enquiry(
            conversation,
            {"discovery_facts": [{
                "context_area": _clr_ctx,
                "fact_type": "capability_clarification_count",
                "fact_value": str(_clr_count + 1),
                "source_message": "controller",
            }]},
            signal=None,
        )

    if steering.get("decision") == "collect_email_for_consultancy":
        response = _decorate_email_collection_response(response, conversation)

        _companion_flow_debug("07 EMAIL COLLECTION DECORATED", {
        "answer": _preview_text(response.get("answer"), 700),
        "access_status": response.get("access_status"),
        "requires_email_verification": response.get("requires_email_verification"),
        "identity_verification_offer": response.get("identity_verification_offer"),
        "verification_prompt_allowed": response.get("verification_prompt_allowed"),
        "verification_stage": response.get("verification_stage"),
        "verification_purpose": response.get("verification_purpose"),
        "pending_action": response.get("pending_action"),
    })
        
    response["companion_controller"] = True
    response["conversion_action"] = None

    # For present_nexy_capability_visibility, only set confirm_nexy_companion_interest
    # when the LLM actually returned a value response. If the response was a
    # knowledge-gap fallback (controlled_no_context), set ask_more_clarification_or_consultancy
    # instead so a later "yes" is not misrouted as a confirmed booking interest.
    _sync_decision = steering.get("decision")
    if (
        _sync_decision == "present_nexy_capability_visibility"
        and isinstance(response, dict)
        and response.get("access_status") == "controlled_no_context"
    ):
        _sync_decision = "ask_more_clarification_or_consultancy"

    _sync_pending_action_from_decision(conversation, _sync_decision, steering)

    _maybe_advance_milestone(conversation)
    
    _companion_flow_debug("08 FINAL COMPANION RESPONSE", {
        "decision": steering.get("decision"),
        "external_intent": steering.get("visitor_external_intent"),
        "internal_intent": steering.get("internal_intent"),
        "answer": _preview_text(response.get("answer") if isinstance(response, dict) else None, 900),
        "access_status": response.get("access_status") if isinstance(response, dict) else None,
        "verification_stage": response.get("verification_stage") if isinstance(response, dict) else None,
        "pending_action_response": response.get("pending_action") if isinstance(response, dict) else None,
        "companion_controller": response.get("companion_controller") if isinstance(response, dict) else None,
        "conversion_action": response.get("conversion_action") if isinstance(response, dict) else None,
    })

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

    # If the LLM answer was entirely stripped, emit a knowledge-gap message rather
    # than a hardcoded capability claim. Capability claims must come from Nexus knowledge.
    if not answer:
        answer = (
            "I don't have enough confirmed Nexus knowledge to present a detailed capability "
            "summary for this situation yet."
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


_NEXY_CAPABILITY_MENU = (
    "- Visitor conversation\n"
    "- Requirement discovery\n"
    "- Enquiry qualification\n"
    "- Lead context capture\n"
    "- Guided next step\n"
    "- Representative handoff\n"
    "- Appointment readiness"
)


def _get_companion_playbook_doc(conversation, agent=None):
    """
    Resolve the enabled Nexus Companion Playbook for this conversation:
    the agent profile passed into handle_companion_turn first, then the
    assigned agent profile from the conversation record.
    """
    playbook_name = ""
    if agent is not None:
        playbook_name = (getattr(agent, "companion_playbook", None) or "").strip()

    if not playbook_name:
        agent_name = _get_conversation_assigned_agent(conversation)
        if agent_name:
            playbook_name = (
                frappe.db.get_value(
                    "Nexus AI Agent Profile", agent_name, "companion_playbook"
                )
                or ""
            ).strip()

    if not playbook_name:
        return None

    try:
        playbook = frappe.get_doc("Nexus Companion Playbook", playbook_name)
        if not int(getattr(playbook, "enabled", 0) or 0):
            return None
        return playbook
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: playbook resolution failed",
        )
        return None


def _get_playbook_capability_items(playbook):
    """Enabled capability rows with a display title, in configured order."""
    if not playbook:
        return []
    return [
        row for row in (playbook.get("capability_items") or [])
        if int(getattr(row, "enabled", 0) or 0)
        and (getattr(row, "display_title", "") or "").strip()
    ]


def _build_playbook_capability_summary(steering, playbook):
    """
    Deterministic capability summary rendered from the playbook's capability
    items — the primary pitch moment. No LLM involved, so the pitch is
    identical in every conversation and editable by admins on the playbook.
    Knowledge sources remain the grounding for drill-down questions.
    """
    items = _get_playbook_capability_items(playbook)
    heading = (playbook.get("capability_summary_heading") or "Nexy Capability Summary").strip()

    methodology = (steering.get("current_methodology") or "").strip()
    status = (steering.get("current_methodology_status") or "known").strip()
    lead_context = (
        (steering.get("methodology_context_area") or "lead_generation").strip()
        == "lead_generation"
    )

    # Acknowledgement line — same phrasing rules as the LLM response goal used.
    if status == "none":
        ack = (
            "Got it — you do not have a clear lead source in place yet."
            if lead_context
            else "Got it — you do not have a set approach in place for this yet."
        )
    elif status == "unclear":
        ack = (
            "Got it — your current lead source is not clearly defined yet."
            if lead_context
            else "Got it — your current approach is not clearly defined yet."
        )
    elif status == "unknown":
        mref = methodology or "that approach"
        ack = (
            f"Got it — {mref} is currently part of how leads come in for you."
            if lead_context
            else f"Got it — {mref} is what you are currently using for this."
        )
    else:
        mref = methodology or "your current source"
        ack = (
            f"Got it — {mref} is how you are currently bringing people in."
            if lead_context
            else f"Got it — {mref} is how you are currently handling this."
        )

    transition = (
        "From here, I can focus on what happens after an enquiry comes in: "
        "understanding the visitor, capturing the requirement, qualifying the "
        "opportunity, and guiding the next step."
    )

    bullet_lines = []
    for row in items:
        title = (row.display_title or "").strip()
        desc = (getattr(row, "short_description", "") or "").strip()
        bullet_lines.append(f"- **{title}:** {desc}" if desc else f"- **{title}**")
    bullets = "\n".join(bullet_lines)

    parts = [ack, transition, f"**{heading}:**\n{bullets}"]

    # Positioning boundary — same conditions as _apply_nexy_summary_guard.
    if methodology and status not in ("none", "unclear", "not_disclosed"):
        if lead_context:
            parts.append(
                f"To be clear, Nexy does not replace or manage {methodology}. "
                f"{methodology} may bring people in — Nexy focuses on the conversation "
                "after someone contacts your business."
            )
        else:
            parts.append(f"To be clear, Nexy does not replace or manage {methodology}.")

    parts.append(
        "Would you like to explore this further or book a short session with a Nexy representative?"
    )

    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": "\n\n".join(parts),
        "confidence": 1.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": None,
        "nexy_capability_visibility": True,
        "capability_summary_presented": True,
        "nexy_capability_source": "playbook",
    }


def _handle_no_matching_capability_menu(challenge=None, repeat=False, playbook=None):
    """
    Controller-owned response when the capability-fit check finds no confirmed
    matching Nexy capability. Deterministic — never LLM-generated — so the
    system cannot invent capability it does not have.

    When the playbook defines capability items, the menu lists exactly those —
    keeping the menu consistent with the playbook-rendered capability summary.
    """
    challenge = (challenge or "your requirement").strip()

    playbook_items = _get_playbook_capability_items(playbook)
    if playbook_items:
        menu = "\n".join(f"- {row.display_title.strip()}" for row in playbook_items)
    else:
        menu = _NEXY_CAPABILITY_MENU

    if repeat:
        answer = (
            "Here are the areas I can currently help with:\n\n"
            f"{menu}\n\n"
            "Which of these would you like help with?"
        )
    else:
        answer = (
            f"I do not have a confirmed Nexy capability specifically matching {challenge} in my current knowledge base, "
            "so I should not claim that I can solve it directly.\n\n"
            "Here are the areas I can currently help with:\n\n"
            f"{menu}\n\n"
            "Which of these would you like help with?"
        )

    return {
        "status": "success",
        "access_status": "controlled_no_context",
        "answer": answer,
        "confidence": 0.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 1,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": None,
        "pending_action": "select_nexy_capability_area",
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

    if decision == "present_nexy_capability_visibility":
        methodology = (steering.get("current_methodology") or "").strip()
        challenges = (steering.get("pain_point_challenges") or "").strip()
        business_context = (steering.get("business_context") or "").strip()
        return (
            "Approved Nexus commercial knowledge about Nexy Companion capabilities. "
            "Prefer Context: NEXUS AI COMMERCIAL and Sub Context: Nexy Companion. "
            "Find confirmed Nexy capabilities, use cases, limitations, demo direction, meeting booking, "
            "email verification, and representative handoff. "
            f"Visitor business context: {business_context}. "
            f"Visitor challenge: {challenges}. "
            f"Visitor current source or approach: {methodology}. "
            "Treat the current source only as context. "
            "Do not answer ad campaign strategy, targeting, budget, creative optimization, or platform management. "
            "Do not invent industry-specific workflows. "
            "Return only confirmed Nexy capability areas such as structured conversation, intelligence engine, "
            "milestones, journey stages, buying signals, visitor profiling, persona matching, enquiry scoring, "
            "website chat, WhatsApp outreach, human escalation, email verification, meeting booking, "
            "and grounded knowledge."
        )

    if decision == "answer_nexy_capability_clarification":
        selected_area = (steering.get("selected_capability_area") or "").strip()
        challenges = (steering.get("pain_point_challenges") or "").strip()
        methodology = (steering.get("current_methodology") or "").strip()
        business_context = (steering.get("business_context") or "").strip()
        return (
            "Approved Nexus commercial knowledge for a Nexy Companion capability clarification. "
            "Prefer Context: NEXUS AI COMMERCIAL and Sub Context: Nexy Companion. "
            f"Selected capability area: {selected_area}. "
            f"Visitor business context: {business_context}. "
            f"Visitor challenge: {challenges}. "
            f"Visitor current source or approach: {methodology}. "
            "Use visitor business type only as light context. "
            "Do not invent industry-specific examples, quote processes, service categories, or operational workflows. "
            "Answer only from confirmed Nexus knowledge. "
            "If no knowledge confirms the clarification, return a safe knowledge-gap response and offer "
            "to save the question for a Nexy representative."
        )

    if decision == "knowledge_gap_offer_consultant":
        selected_area = (steering.get("selected_capability_area") or "").strip()
        challenges = (steering.get("pain_point_challenges") or "").strip()
        return (
            "The visitor asked for clarification that is not sufficiently covered by approved Nexus knowledge. "
            f"Selected area or question: {selected_area or challenges}. "
            "Do not guess or invent an answer. "
            "Return only confirmed Nexus knowledge about what IS confirmed, if anything. "
            "The response must acknowledge the gap and offer to save the question for a Nexy representative. "
            "Also offer to book a short consultation."
        )

    if decision == "check_matching_capability":
        challenges = (steering.get("pain_point_challenges") or "").strip()
        business_context = (steering.get("business_context") or "").strip()
        context_area = (steering.get("methodology_context_area") or "general_business").strip()
        return (
            "Find confirmed Nexy or Nexus capability that directly matches the visitor's business need. "
            f"Visitor business context: {business_context}. "
            f"Visitor challenge or requirement: {challenges}. "
            f"Context area: {context_area}. "
            "Look only for confirmed capability, workflow, use case, limitation, or supported business outcome. "
            "Do not use generic marketing language as proof. "
            "Return capability only if the knowledge clearly supports this specific need."
        )

    if decision == "drill_nexy_capability_area":
        selected_area = (steering.get("selected_capability_area") or "").strip()
        challenges = (steering.get("pain_point_challenges") or "").strip()
        return (
            f"Confirmed Nexy/Nexus capability details for capability area: {selected_area}. "
            f"Visitor challenge/context: {challenges}. "
            "Find only approved knowledge about what this capability does, how it helps, limits, and next step. "
            "Return all confirmed workflow, process, data capture, routing, or outcome details "
            "for this specific capability area only. "
            "Do not invent capability details."
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

    if decision == "present_nexy_capability_visibility":
        methodology = (steering.get("current_methodology") or "your current source").strip()
        methodology_status = (steering.get("current_methodology_status") or "known").strip()
        _lead_context = (steering.get("methodology_context_area") or "lead_generation").strip() == "lead_generation"

        if methodology_status == "none":
            ack_example = (
                "Got it — you do not have a clear lead source in place yet."
                if _lead_context
                else "Got it — you do not have a set approach in place for this yet."
            )
        elif methodology_status == "unclear":
            ack_example = (
                "Got it — your current lead source is not clearly defined yet."
                if _lead_context
                else "Got it — your current approach is not clearly defined yet."
            )
        elif methodology_status == "unknown":
            ack_example = (
                f"Got it — {methodology} is currently part of how people come in for you."
                if _lead_context
                else f"Got it — {methodology} is what you are currently using for this."
            )
        else:
            ack_example = (
                f"Got it — {methodology} is how people are currently coming in."
                if _lead_context
                else f"Got it — {methodology} is how you are currently handling this."
            )

        return (
            "The visitor has already answered the current source/current approach question. "
            "Do NOT ask how effective it is. "
            "Do NOT ask what results they are getting. "
            "Do NOT ask which area they want to improve as a discovery question. "
            f"Start with a short natural acknowledgement, for example: '{ack_example}' "
            "Then explain in visitor-facing language that your support starts after someone contacts the business. "
            "Do NOT write 'From here, I can focus...' because it sounds like internal planning. "
            "Use first person only: 'I can...', 'I help...', 'I do not replace...'. "
            "Do NOT say 'Nexy is designed to', 'Nexy helps', 'Nexy can', or 'Nexy is'. "
            "Do NOT use the heading 'Nexy Capability Summary'. "
            "Use the heading: 'How I can help after the enquiry'. "
            f"Do NOT say you improve, enhance, optimize, streamline, or boost {methodology}, "
            "ads, campaigns, targeting, budget, creatives, or the visitor's current lead source. "
            "List only capabilities found in permitted Nexus knowledge. "
            "Use 2 to 5 concise first-person bullets. "
            "If no confirmed capability knowledge is available, say there is not enough confirmed information yet. "
            "End with this CTA only: 'Would you like to explore this further or book a short session with a Nexy representative?' "
            "Do NOT ask which area they want to understand better. "
            "Do NOT ask for email directly in this turn."
        )

    if decision == "answer_nexy_capability_clarification":
        selected_area = (steering.get("selected_capability_area") or "that area").strip()
        return (
            f"Explain {selected_area} in simple, plain business language using ONLY the permitted Nexus knowledge. "
            "Do NOT use technical or internal phrases such as: 'grounding', 'retrieval', 'qualification journey', "
            "'methodology', 'enquiry channel', 'controlled flow', 'permitted knowledge', or 'confirmed role'. "
            "Speak directly to a business owner or manager — keep it natural and easy to follow. "
            "Do NOT invent industry-specific examples, service categories, quote processes, consultation steps, "
            "CRM behavior, dashboards, integrations, marketing strategy outcomes, or follow-up automation "
            "unless explicitly present in the permitted Nexus knowledge or stated by the visitor. "
            "Use the visitor's industry or business type only as light context — for example: "
            "'For visitors asking about your service…' or 'After someone contacts your business…'. "
            "Do NOT invent specifics like regular maintenance, repairs, installation services, quotation flow, "
            "consultation for the visitor's service, maintenance packages, or similar. "
            "If the permitted knowledge is not enough to explain this area clearly, say clearly and simply that "
            "this specific point is not confirmed in the available Nexus knowledge, offer to save the question "
            "for a Nexy representative, and suggest a short consultation. "
            "After answering, ask: 'Would you like me to explain another Nexy area, or would you prefer to book "
            "a short demo/consultation with a Nexy representative to review this for your business?'"
        )

    if decision == "check_matching_capability":
        challenges = (steering.get("pain_point_challenges") or "the visitor's challenge").strip()
        return (
            "Answer only from permitted Nexus Orbit knowledge. "
            "If a matching Nexy capability is clearly confirmed, briefly explain the match in the visitor's business context. "
            f"Connect the capability to this challenge: {challenges}. "
            "Do not ask about current methodology. "
            "Do not treat the visitor's requirement statement as their current lead source or current approach. "
            "Do not claim implementation, automation, integration, software delivery, dashboards, or operational "
            "capability unless confirmed in the permitted knowledge. "
            "End with one simple next-step question."
        )

    if decision == "drill_nexy_capability_area":
        selected_area = (steering.get("selected_capability_area") or "that area").strip().replace("_", " ")
        return (
            f"Explain the Nexy capability area '{selected_area}' in simple, plain business language using ONLY "
            "the permitted Nexus knowledge. "
            "Do NOT use technical or internal phrases such as: 'grounding', 'retrieval', 'methodology', "
            "'enquiry channel', 'controlled flow', 'permitted knowledge', or 'confirmed role'. "
            "Do NOT invent industry-specific examples, service categories, quote processes, CRM behavior, "
            "dashboards, integrations, or automation unless explicitly present in the permitted Nexus knowledge. "
            "If the permitted knowledge is not enough to explain this area clearly, say so simply and offer to "
            "save the question for a Nexy representative. "
            "After answering, ask: 'Would you like me to explain another Nexy area, or would you prefer to book "
            "a short demo/consultation with a Nexy representative to review this for your business?'"
        )

    if decision == "ask_more_clarification_or_consultancy":
        return (
            "Give the visitor room to continue clarification or move to a consultation. "
            "Ask: 'Would you like me to explain another Nexy area, or would you prefer to book a short "
            "demo/consultation with a Nexy representative to review this for your business?' "
            "Do not pressure the visitor. "
            "Do not introduce new capability claims. "
            "Do not ask for email yet."
        )

    if decision == "offer_demo_or_consultancy":
        return (
            "Invite the visitor to book a short demo or consultation with a Nexy representative. "
            "Explain simply that the representative can review the visitor's business context and show "
            "how Nexy can fit their situation. "
            "Do not create new product claims. "
            "Do not ask for email yet — wait for the visitor to say they want to proceed."
        )

    if decision == "knowledge_gap_offer_consultant":
        return (
            "Do not guess or invent an answer. "
            "Say clearly and simply that this specific point is not confirmed in the available Nexus knowledge. "
            "Offer to save the question for a Nexy representative. "
            "Also offer a short demo or consultation so the representative can review the visitor's case directly. "
            "Example: 'I don\\'t have enough confirmed Nexus knowledge to answer that specific point safely. "
            "I can save it as a question for a Nexy representative and help you book a short consultation if you\\'d like.' "
            "Do not ask for email unless the visitor agrees to proceed."
        )

    if decision == "bounce_back_to_nexy_capabilities":
        return (
            "Briefly acknowledge the visitor's off-path question. "
            "Do not answer outside the confirmed Nexy capability path. "
            "Do not add any new capability claim. "
            "Bounce back to Nexy capability clarification or consultation offer. "
            "Ask which Nexy capability area they want to understand better."
        )

    if decision == "collect_email_for_consultancy":
        return (
            "Ask the visitor to share their email address. "
            "Explain that email verification is required before booking the meeting. "
            "Keep it simple and reassuring. "
            "Do not say a verification code has been sent until the system actually sends it. "
            "Example: 'Sure. Please share your email address so I can verify it before booking the meeting.'"
        )

    if decision == "collect_email_for_appointment":
        return (
            "Ask the visitor to share their email address so it can be verified before appointment booking. "
            "Explain that appointment booking requires email verification. "
            "Do not claim that verification has been sent until the system actually sends it."
        )

    if decision == "verify_email_for_consultancy":
        _verify_internal = (steering.get("internal_intent") or "").strip()

        if _verify_internal == "resent_verification_code":
            return (
                "A new verification code has just been emailed to the visitor. "
                "Tell them clearly that a fresh code was sent and that the previous code no longer works. "
                "Ask them to enter the new code, and suggest checking the spam folder if it does not arrive shortly."
            )
        if _verify_internal == "resend_verification_failed":
            return (
                "Sending a new verification code failed. "
                "Apologize briefly and ask the visitor to type 'resend code' again in a moment. "
                "Do not claim that a code was sent."
            )
        if _verify_internal == "resend_limit_reached":
            return (
                "The visitor has requested too many verification codes. "
                "Explain politely that no more codes can be sent right now. "
                "Offer to leave a note or question for the Nexy representative instead."
            )
        if _verify_internal == "verification_code_invalid":
            return (
                "The code the visitor entered did not match. "
                "Tell them plainly that the code was incorrect and ask them to re-check and enter it again. "
                "Mention they can type 'resend code' to receive a new one."
            )
        if _verify_internal == "verification_code_expired":
            return (
                "The visitor's verification code has expired or is no longer valid. "
                "Tell them clearly and ask them to type 'resend code' so a fresh code can be emailed."
            )
        if _verify_internal == "verification_max_retries":
            return (
                "The visitor entered the wrong code too many times. "
                "Tell them clearly and ask them to type 'resend code' to receive a fresh code and try again."
            )

        return (
            "A verification code has been sent to the visitor's email address. "
            "Ask them to enter the verification code to confirm their email. "
            "If the visitor cannot find the code, suggest checking their spam folder. "
            "If they did not receive it, tell them they can type 'resend code' to get a new one. "
            "If the visitor does not want to continue, offer to collect a note or question for the Nexy representative."
        )

    if decision == "verify_email_for_appointment":
        return (
            "A verification code has been sent to the visitor's email. "
            "Ask them to enter the verification code to confirm their email address. "
            "Do not proceed with appointment booking until verification is confirmed."
        )

    if decision == "collect_representative_note":
        if steering.get("internal_intent") == "re_ask_for_note_after_acknowledgment":
            return (
                "The visitor said yes to leaving a note. "
                "Ask them to type it now. Keep it brief. "
                "Example: 'Sure. Please type the note or question you want the representative to see, "
                "or type \"skip\" to proceed without one.'"
            )
        return (
            "Ask the visitor to leave a note, question, or context for the Nexy representative before the "
            "meeting request is finalised. "
            "Tell them this helps the representative understand what they want reviewed. "
            "Tell them they can also type 'skip' if they prefer not to leave a note. "
            "Keep it brief and friendly. "
            "Example: 'Before I proceed, would you like to add a note or question for the Nexy representative? "
            "This helps them understand what you want reviewed. You can also type \\'skip\\'.'"
        )

    if decision == "show_meeting_booking_card":
        return (
            "The visitor's email has been verified and a representative note has been captured or skipped. "
            "Confirm clearly that the meeting request has been saved. "
            "If a booking link is available, tell the visitor they can choose a suitable time below. "
            "If no booking link is available, tell the visitor that a Nexy representative will follow up "
            "using their verified email. "
            "Do not claim a meeting is confirmed unless an actual booking has been made."
        )

    if decision == "create_consultancy_request":
        return (
            "A consultancy request has been created for the visitor. "
            "Tell them clearly that a Nexy representative will review their note and follow up "
            "using the verified email address. "
            "Do not claim the meeting is booked or confirmed. "
            "Close warmly."
        )

    if decision == "appointment_declined_collect_note":
        return (
            "The visitor declined the meeting or demo. Respond without pressure. "
            "Before closing, ask if they would like to leave a note, question, or feedback for the Nexy "
            "representative to review. "
            "Example: 'No problem. Before we close, would you like to leave a note, question, or feedback "
            "for the Nexy representative to review? You can also type \\'skip\\'.'"
        )

    if decision == "email_declined_collect_note":
        return (
            "The visitor declined to provide their email address. "
            "Acknowledge clearly that booking requires email verification. "
            "Still offer to save a note or question for the Nexy representative. "
            "Example: 'No problem. I can\\'t book a meeting without email verification, but I can still save "
            "a note or question for the Nexy representative. Would you like to leave one?'"
        )

    if decision == "collect_appointment_slot":
        return (
            "The visitor's email has been verified. "
            "Ask them to suggest a preferred date and time for the appointment. "
            "Keep the request simple — just date, time, and timezone if needed."
        )

    if decision == "capture_closing_feedback":
        return (
            "The visitor appears to be leaving or declining. "
            "Before closing, ask if they would like to leave a note, question, or feedback "
            "for the Nexy representative to review. "
            "Say they can type 'skip' if they prefer not to. "
            "Do not push for appointment or email."
        )

    if decision == "close_conversation":
        return (
            "Close the conversation politely and warmly. "
            "Thank the visitor for their time. "
            "Let them know they can return whenever they are ready to explore further. "
            "Do not ask any more questions."
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

def _repair_lead_entry_as_methodology(data, visitor_message):
    """
    If the LLM extracted a lead_entry_point fact but no current_methodology fact,
    promote the entry point to current_methodology so the methodology slot is filled.
    This covers WhatsApp, website, contact form, phone call, etc.
    """
    data = data or {}
    facts = data.get("discovery_facts") or []
    if not isinstance(facts, list):
        facts = []

    has_lead_methodology = any(
        str(f.get("context_area") or "").strip() == "lead_generation"
        and str(f.get("fact_type") or "").strip() in {
            "current_methodology", "current_approach", "current_tool",
        }
        and str(f.get("fact_value") or "").strip()
        for f in facts
    )

    lead_entry_fact = next(
        (
            f for f in facts
            if str(f.get("context_area") or "").strip() == "lead_generation"
            and str(f.get("fact_type") or "").strip() == "lead_entry_point"
            and str(f.get("fact_value") or "").strip()
        ),
        None,
    )

    if not has_lead_methodology and lead_entry_fact:
        value = str(lead_entry_fact.get("fact_value") or "").strip()
        facts.append({
            "context_area": "lead_generation",
            "fact_type": "current_methodology",
            "fact_value": value,
            "source_message": lead_entry_fact.get("source_message") or visitor_message,
        })
        facts.append({
            "context_area": "lead_generation",
            "fact_type": "current_methodology_status",
            "fact_value": "known",
            "related_value": value,
            "source_message": "lead_entry_repair",
        })

    data["discovery_facts"] = facts
    return data


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
- "Mostly WhatsApp" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "current_methodology", "fact_value": "WhatsApp", "source_message": "Mostly WhatsApp"}}, {{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "WhatsApp", "source_message": "Mostly WhatsApp"}}]}}
- "They come to our website" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "current_methodology", "fact_value": "Website enquiries", "source_message": "They come to our website"}}, {{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "Website", "source_message": "They come to our website"}}]}}
- "They fill a contact form" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "current_methodology", "fact_value": "Website enquiries", "source_message": "They fill a contact form"}}, {{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "Contact form", "source_message": "They fill a contact form"}}]}}
- "Mostly calls" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "current_methodology", "fact_value": "Phone call", "source_message": "Mostly calls"}}, {{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "Phone call", "source_message": "Mostly calls"}}]}}
- "WhatsApp and website" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "current_methodology", "fact_value": "WhatsApp and website", "source_message": "WhatsApp and website"}}, {{"context_area": "lead_generation", "fact_type": "lead_entry_point", "fact_value": "WhatsApp and website", "source_message": "WhatsApp and website"}}]}}
- "Referrals" → {{"discovery_facts": [{{"context_area": "lead_generation", "fact_type": "current_methodology", "fact_value": "Referrals", "source_message": "Referrals"}}]}}

Only extract facts clearly stated. Do not infer. If nothing found, return {{}}.
"""

    try:
        raw = (generate_answer(prompt) or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json", "", 1).strip()
        data = json.loads(raw)
        if isinstance(data, dict):
            return _repair_lead_entry_as_methodology(data, visitor_message)
        return {}
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

def _is_verified_note_turn(conversation, conversation_context, pending_action, payload=None, core_payload=None):
    payload = payload or {}
    core_payload = core_payload or {}

    if pending_action == "collect_representative_note":
        return True

    try:
        db_pending = (
            frappe.db.get_value(
                "Nexus Live Conversation",
                conversation.name,
                "companion_pending_action",
            )
            or ""
        ).strip()

        if db_pending == "collect_representative_note":
            return True
    except Exception:
        pass

    payload_pending = (
        payload.get("pending_action")
        or payload.get("companion_pending_action")
        or core_payload.get("pending_action")
        or core_payload.get("companion_pending_action")
        or ""
    ).strip()

    if payload_pending == "collect_representative_note":
        return True

    return _is_representative_note_stage(conversation_context, pending_action)

def _is_booking_email_verified(conversation):
    """
    Strong verification check used before showing the booking card.

    Primary source:
    - companion_email_verified = 1

    Defensive fallback:
    - visitor_email exists
    - pending context says verified_via idv_challenge/email_code

    This avoids closing the booking flow when the previous verification turn
    saved context but the conversation doc/cache is stale.
    """
    try:
        row = frappe.db.get_value(
            "Nexus Live Conversation",
            conversation.name,
            [
                "visitor_email",
                "companion_email_verified",
                "companion_pending_action",
                "companion_pending_context_json",
            ],
            as_dict=True,
        ) or {}

        if bool(row.get("companion_email_verified")):
            return True

        visitor_email = (row.get("visitor_email") or "").strip()
        pending_action = (row.get("companion_pending_action") or "").strip()
        raw_ctx = row.get("companion_pending_context_json") or "{}"

        try:
            ctx = json.loads(raw_ctx) if isinstance(raw_ctx, str) else (raw_ctx or {})
        except Exception:
            ctx = {}

        verified_via = (ctx.get("verified_via") or "").strip()

        if (
            visitor_email
            and pending_action == "collect_representative_note"
            and verified_via in {"idv_challenge", "email_code"}
        ):
            return True

        return False

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: booking email verification check failed",
        )
        return False

def _is_representative_note_stage(conversation_context, pending_action=None):
    text = str(conversation_context or "").lower()

    if pending_action == "collect_representative_note":
        return True

    markers = [
        "add a note or question for the nexy representative",
        "note or question for the nexy representative",
        "this helps them understand what you want reviewed",
        "you can also type \"skip\"",
        "you can also type 'skip'",
        "type \"skip\"",
        "type 'skip'",
        "type skip",
    ]

    return any(marker in text for marker in markers)


def _is_note_ack_only(visitor_message):
    text = str(visitor_message or "").strip().lower()
    return text in {
        "yes",
        "y",
        "sure",
        "ok",
        "okay",
        "yep",
        "yeah",
        "alright",
        "go ahead",
        "proceed",
    }


def _is_skip_note(visitor_message):
    text = str(visitor_message or "").strip().lower()
    return (
        text in {"skip", "no", "no thanks", "no thank you", "nope", "pass", "not now"}
        or "skip" in text
    )

def _looks_like_methodology_answer(visitor_message):
    text = str(visitor_message or "").lower().strip()
    keywords = [
        "google ads", "google ad", "adwords",
        "facebook ads", "facebook ad", "meta ads", "instagram ads",
        "referrals", "referral",
        "seo",
        "website enquiries", "website inquiries", "website leads",
        "website", "contact form",
        "whatsapp", "whats app",
        "phone call", "phone calls", "calls",
        "cold calling", "cold call",
        "social media",
        "walk in", "walk-in", "other", "custom", "none", "not sure", "unclear", "unknown",
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
    accumulated = accumulated or {}
    mfact = (
        _find_fact(accumulated, context_area, "current_methodology")
        or _find_fact(accumulated, context_area, "current_approach")
        or _find_fact(accumulated, context_area, "current_tool")
    )
    # For lead generation, the visitor's channel/source answer (WhatsApp, website,
    # contact form, calls) also satisfies the current-methodology slot.
    if not mfact and context_area == "lead_generation":
        mfact = _find_fact(accumulated, context_area, "lead_entry_point")
    if mfact:
        return str(mfact.get("fact_value") or "").strip()
    raw_sys = accumulated.get("existing_systems") or ""
    return (
        ", ".join(str(s) for s in raw_sys if s)
        if isinstance(raw_sys, list)
        else str(raw_sys)
    ).strip()


def _get_current_methodology_status(accumulated, context_area):
    status = _get_fact_value(accumulated or {}, context_area, "current_methodology_status")
    return status or "known"

def _is_leaving_signal(visitor_message):
    text = str(visitor_message or "").lower().strip()
    signals = [
        "bye", "goodbye", "good bye", "see you", "talk later", "talk to you later",
        "i'll check later", "i will check later", "check back later",
        "not interested", "no thanks", "no thank you", "thanks bye",
        "i'm leaving", "i am leaving", "have to go", "gotta go",
    ]
    return any(s in text for s in signals)


def _looks_like_appointment_interest(visitor_message):
    text = str(visitor_message or "").lower().strip()
    terms = [
        "book", "booking", "appointment", "schedule", "meeting",
        "yes", "sure", "ok", "okay", "let's do it", "let us do it",
        "i'm interested", "i am interested", "would like to", "i'd like",
        "go ahead", "proceed",
    ]
    return any(t in text for t in terms)


def _asks_about_methodology_support(visitor_message):
    text = str(visitor_message or "").lower()
    methodology_terms = [
        "google ads", "google ad", "adwords",
        "facebook ads", "facebook ad", "meta ads", "instagram ads",
        "seo", "referrals", "referral", "whatsapp", "website",
        "cold calling", "social media",
    ]
    support_terms = [
        "support", "integrate", "integration", "connect", "manage", "optimize",
        "optimise", "improve", "run", "automate", "handle", "campaign",
        "targeting", "budget", "creative", "ad platform", "work with",
    ]
    return any(m in text for m in methodology_terms) and any(s in text for s in support_terms)


def _capability_summary_presented(accumulated, context_area):
    return _has_fact(accumulated, context_area, "nexy_capability_summary_presented")


def _looks_like_capability_clarification(visitor_message):
    text = str(visitor_message or "").lower().strip()
    terms = [
        "visitor conversation", "conversation",
        "requirement", "discovery",
        "qualification", "qualify",
        "context", "capture", "transcript",
        "next step", "appointment", "handoff", "hand off",
        "routing", "crm", "website", "whatsapp",
        "how", "explain", "more", "details", "all",
        "tell me", "what about", "elaborate",
    ]
    return any(t in text for t in terms)


def _normalise_capability_area(visitor_message):
    text = str(visitor_message or "").lower()
    if "requirement" in text or "discovery" in text:
        return "requirement_discovery"
    if "qualif" in text:
        return "enquiry_qualification"
    if "context" in text or "capture" in text or "transcript" in text:
        return "context_capture"
    if "appointment" in text:
        return "appointment_readiness"
    if "handoff" in text or "hand off" in text:
        return "representative_handoff"
    if "routing" in text or "crm" in text:
        return "routing_or_crm_update"
    if "website" in text:
        return "website_visitor_flow"
    if "whatsapp" in text:
        return "whatsapp_enquiry_flow"
    if "conversation" in text:
        return "visitor_conversation"
    if "all" in text or "everything" in text:
        return "all_capabilities"
    return "general_nexy_capability"


def _looks_like_meeting_decline(visitor_message):
    text = str(visitor_message or "").lower().strip()
    decline_terms = [
        "no thanks", "no thank you", "not interested", "not now",
        "don't want", "do not want", "maybe later", "not yet",
        "skip meeting", "no meeting", "no demo", "no consultation",
        "not ready", "decline", "won't book", "will not book",
        "don't need", "do not need",
    ]
    return any(t in text for t in decline_terms)


def _looks_like_consultancy_interest(visitor_message):
    """More specific than _looks_like_appointment_interest — requires explicit booking/demo intent."""
    text = str(visitor_message or "").lower().strip()
    terms = [
        "book", "booking", "schedule a", "meeting", "demo",
        "consultation", "consultancy", "speak to", "talk to",
        "nexy representative", "yes book", "yes please",
        "let's book", "let us book", "i'd like to book",
        "i would like to book", "set up a meeting", "arrange a meeting",
    ]
    return any(t in text for t in terms)


def _is_capability_menu_declined(message):
    """
    Detect visitor rejection after the controller-owned Nexy capability menu.

    This is different from meeting decline. The visitor is saying the listed
    capability areas are not relevant, so we should stop politely instead of
    repeating the menu or collecting a note.
    """
    text = str(message or "").lower().strip()

    if not text:
        return False

    # Handles phrasings like "None of this I am interested"
    if "none" in text and "interested" in text:
        return True

    # Bare closers match only as the whole message — substring matching would
    # false-positive on words like "send", "closely", or "stopped".
    if text.rstrip(".!?,") in {"stop", "close", "end", "leave it"}:
        return True

    decline_markers = [
        "none of this",
        "none of these",
        "none of them",
        "nothing here",
        "nothing from this",
        "nothing in this",
        "not relevant",
        "not useful",
        "not suitable",
        "not matching",
        "doesn't match",
        "does not match",
        "no match",
        "irrelevant",
        "i am not interested",
        "i'm not interested",
        "not interested",
        "no interest",
        "no thanks",
        "no thank you",
        "that's all",
        "that is all",
    ]

    return any(marker in text for marker in decline_markers)


# ---------------------------------------------------------------------------
# Methodology slot classifier helpers
# ---------------------------------------------------------------------------

def _is_generic_confirmation(text):
    return str(text or "").strip().lower() in {
        "yes", "y", "yeah", "yep", "ok", "okay", "sure", "please", "alright", "fine",
    }


def _looks_like_new_question(text):
    t = str(text or "").strip().lower()
    return "?" in t or t.startswith((
        "what ", "how ", "why ", "can ", "do ", "does ", "is ", "are ",
        "will ", "would ", "could ", "should ", "when ", "where ", "who ",
    ))


def _looks_like_new_non_methodology_intent(text):
    """
    Returns True only when the message is clearly a new non-methodology intent
    (pricing, demo, booking, human request, product question) rather than an
    answer to "what are you currently using?"

    Narrower than _looks_like_new_question so that answers such as
    "I think we use people outreach, is that what you mean?" still pass as
    methodology answers.
    """
    t = str(text or "").strip().lower()
    markers = [
        "price", "pricing", "cost", "how much", "package", "subscription", "plan",
        "demo", "meeting", "book a", "appointment", "schedule a",
        "human", "person", "representative", "team member", "speak to",
        "what is nexy", "how does nexy", "what can you do", "how can you help",
        "what do you do", "tell me about nexy", "what nexy",
    ]
    return any(m in t for m in markers)


def _looks_like_no_methodology(text):
    t = str(text or "").strip().lower()
    markers = [
        "nothing", "none", "no system", "not using", "don't use",
        "dont use", "no idea", "not sure", "i don't know", "i dont know",
        "not currently", "haven't started", "have not started", "not yet",
        "no method", "no process", "nothing yet", "nothing in place",
    ]
    return any(m in t for m in markers)


def _looks_like_resend_code_request(visitor_message):
    """True when the visitor asks for the verification code to be sent again."""
    text = str(visitor_message or "").lower().strip()
    markers = [
        "resend", "re-send", "re send",
        "send again", "send it again", "send the code again",
        "send a new code", "send new code", "send code again",
        "new code", "another code", "one more code", "fresh code",
        "didn't get", "did not get", "didnt get",
        "didn't receive", "did not receive", "didnt receive",
        "haven't received", "have not received", "havent received",
        "not received", "never got", "never received",
        "no email came", "nothing in my inbox",
    ]
    return any(m in text for m in markers)


def _looks_like_solution_need(message):
    """
    True when the visitor states a requirement / solution need
    ("we need software solution", "looking for a system", "nothing yet")
    rather than describing what they currently use.
    """
    text = str(message or "").lower().strip()

    need_markers = [
        "need",
        "looking for",
        "want",
        "require",
        "required",
        "solution",
        "software solution",
        "automation",
        "platform",
        "system",
        "implementation support",
        "we need",
        "we want",
        "we are looking",
        "nothing",
        "not using",
        "don't have",
        "do not have",
        "dont have",
        "no system",
        "no software",
        "need help",
    ]

    return any(marker in text for marker in need_markers)


def _looks_like_current_methodology(message):
    """
    True when the message plausibly describes a current tool/channel/approach.
    Negated statements ("not using anything", "we don't have a system") are
    solution needs, not current methodology.
    """
    text = str(message or "").lower().strip()

    negation_markers = [
        "not using", "don't use", "do not use", "dont use",
        "don't have", "do not have", "dont have",
        "no system", "no software", "nothing",
    ]
    if any(marker in text for marker in negation_markers):
        return False

    current_markers = [
        "using",
        "we use",
        "currently",
        "facebook",
        "google",
        "whatsapp",
        "excel",
        "crm",
        "erp",
        "manual",
        "vendor",
        "third party",
        "in-house",
        "website",
        "contact form",
        "phone",
        "email",
        "hubspot",
        "zoho",
        "salesforce",
        "referral",
        "seo",
    ]

    return any(marker in text for marker in current_markers)


def _infer_context_area_from_challenge(challenge):
    """
    Infer the business context area from the discovered challenge text.
    Unlike _detect_context_area_from_challenge (used for fact storage), this
    covers solution-need areas so requirements are not assumed to be
    lead-generation related.
    """
    text = str(challenge or "").lower()

    if any(k in text for k in ["lead", "sales", "enquiry", "inquiry", "follow up", "conversion", "customer acquisition"]):
        return "lead_generation"

    if any(k in text for k in ["implementation", "software", "system", "deployment", "integration", "customization", "configuration", "saas"]):
        return "system_implementation"

    if any(k in text for k in ["operation", "workflow", "process", "delivery", "service"]):
        return "operations"

    if any(k in text for k in ["support", "ticket", "customer support", "helpdesk"]):
        return "customer_support"

    return "general_business"


def _detect_selected_nexy_capability_area(message):
    """Map the visitor's reply to one of the controller-owned capability menu areas."""
    text = str(message or "").lower().strip()

    mapping = {
        "requirement_discovery": ["requirement", "requirement discovery", "discovery"],
        "enquiry_qualification": ["qualification", "qualify", "enquiry", "inquiry", "lead qualification"],
        "lead_context_capture": ["context", "capture", "lead context"],
        "guided_next_step": ["next step", "guided", "guide"],
        "representative_handoff": ["handoff", "hand off", "representative", "human", "team member"],
        "appointment_readiness": ["appointment", "booking", "schedule", "meeting"],
        "visitor_conversation": ["visitor conversation", "chat", "conversation"],
    }

    for key, terms in mapping.items():
        if any(term in text for term in terms):
            return key

    return None


def _get_current_challenge_value(accumulated_discovery, context_area):
    discovery = accumulated_discovery or {}
    challenge = discovery.get("current_challenges") or ""
    if isinstance(challenge, list):
        challenge = ", ".join(str(c) for c in challenge if c)
    return str(challenge).strip()


def _build_business_context(accumulated_discovery):
    discovery = accumulated_discovery or {}
    return (
        discovery.get("industry")
        or discovery.get("business_type")
        or ""
    )


def _classify_current_methodology_slot_answer(visitor_message, pending_context=None):
    """
    Decide whether the visitor message is a valid answer to:
    'What are you currently using for this business challenge?'

    Returns:
    {
        "is_methodology_answer": bool,
        "methodology_value": str,
        "methodology_status": "known" | "unknown" | "none" | "unclear",
        "reason": str
    }
    """
    text = str(visitor_message or "").strip()
    low = text.lower()

    if not text:
        return {
            "is_methodology_answer": False,
            "methodology_value": "",
            "methodology_status": "unclear",
            "reason": "empty message",
        }

    # Generic confirmation (yes, ok, sure) — not a methodology answer
    if _is_generic_confirmation(text):
        return {
            "is_methodology_answer": False,
            "methodology_value": "",
            "methodology_status": "unclear",
            "reason": "generic confirmation, not a methodology answer",
        }

    # Clear non-methodology intent (pricing, demo, booking, human handoff, product question)
    # Use the narrower check so "I think we use outreach, is that what you mean?" still passes.
    if _looks_like_new_non_methodology_intent(text):
        return {
            "is_methodology_answer": False,
            "methodology_value": "",
            "methodology_status": "unclear",
            "reason": "visitor expressed a new non-methodology intent instead of answering the slot",
        }

    # No current method stated
    if _looks_like_no_methodology(text):
        return {
            "is_methodology_answer": True,
            "methodology_value": "None currently",
            "methodology_status": "none",
            "reason": "visitor indicated they have no current methodology",
        }

    # Known platforms — deterministic match
    _known_map = [
        (["facebook ads", "facebook ad", "meta ads", "meta ad"], "Facebook Ads"),
        (["google ads", "google ad", "adwords"], "Google Ads"),
        (["instagram ads", "instagram ad"], "Instagram Ads"),
        (["whatsapp"], "WhatsApp"),
        (["seo"], "SEO"),
        (["referral", "referrals", "word of mouth", "word-of-mouth"], "Referrals"),
        (["website enquir", "website inquir", "website lead", "contact form", "web form"], "Website enquiries"),
        (["cold call", "cold calling"], "Cold calling"),
        (["social media"], "Social media"),
        (["walk in", "walk-in", "walkin", "footfall"], "Walk-ins"),
        (["linkedin"], "LinkedIn"),
        (["email campaign", "email marketing", "newsletter"], "Email marketing"),
        (["youtube"], "YouTube"),
        (["telegram"], "Telegram"),
        (["twitter", "x.com"], "Twitter/X"),
        (["tiktok"], "TikTok"),
        # Unknown / custom but valid — stored as-is
        (["broker", "brokers", "agent ", "agents "], None),
        (["sales team", "sales person", "salesperson", "sales rep"], None),
        (["marketing team", "marketing person"], None),
        (["old customer", "existing customer", "repeat customer", "past customer"], None),
        (["flyer", "flyers", "brochure", "pamphlet", "poster"], None),
        (["event", "exhibition", "trade show", "expo"], None),
        (["radio", "newspaper", "print ad", "billboard", "outdoor ad"], None),
    ]
    for keywords, canonical in _known_map:
        if any(k in low for k in keywords):
            value = canonical if canonical else text
            return {
                "is_methodology_answer": True,
                "methodology_value": value,
                "methodology_status": "known" if canonical else "unknown",
                "reason": "matched known or custom methodology keyword",
            }

    # Informal / vague / custom methodology phrases
    _informal_map = [
        (["connect with people", "talk to people", "meeting people", "meet people"], "Direct people outreach", "informal"),
        (["other strategies", "other strategy", "different strategies", "different strategy"], "Other strategies", "informal"),
        (["something else", "other things", "other stuff"], "Other / unspecified strategy", "unknown"),
        (["networking", "network with"], "Networking", "informal"),
        (["old customers", "existing customers", "past customers", "current customers"], "Existing customer referrals", "informal"),
        (["local agents", "local agent"], "Local agents", "informal"),
        (["brokers", "broker"], "Brokers", "informal"),
        (["word of mouth", "word-of-mouth"], "Word of mouth", "informal"),
        (["direct outreach", "outreach"], "Direct outreach", "informal"),
        (["friends", "family", "personal contacts", "personal network"], "Personal network", "informal"),
        (["door to door", "door-to-door"], "Door-to-door", "informal"),
    ]
    for _inf_keywords, _inf_value, _inf_status in _informal_map:
        if any(k in low for k in _inf_keywords):
            return {
                "is_methodology_answer": True,
                "methodology_value": _inf_value,
                "methodology_status": _inf_status,
                "reason": "matched informal/custom methodology answer",
            }

    # Visitor declined to disclose — store politely, proceed to Nexy value without pressure
    _private_markers = [
        "not to mention", "prefer not to say", "don't want to say", "dont want to say",
        "can't say", "cannot say", "confidential", "private", "not disclose",
    ]
    if any(k in low for k in _private_markers):
        return {
            "is_methodology_answer": True,
            "methodology_value": "Not disclosed",
            "methodology_status": "not_disclosed",
            "reason": "visitor declined to disclose methodology",
        }

    # Broad ads / advertising without specifying the platform
    if low in {"ads", "ad", "advertising", "advertisements", "advertisement"}:
        return {
            "is_methodology_answer": True,
            "methodology_value": "Ads / advertising",
            "methodology_status": "broad_known",
            "reason": "broad ads methodology answer — do not ask what type",
        }
    if "online ads" in low or "digital ads" in low or "paid ads" in low or "online advertising" in low:
        return {
            "is_methodology_answer": True,
            "methodology_value": "Online ads",
            "methodology_status": "broad_known",
            "reason": "broad online ads methodology answer",
        }

    # Short answers (1-4 words) while slot is active — treat as methodology answer
    word_count = len(text.split())
    if word_count <= 4:
        return {
            "is_methodology_answer": True,
            "methodology_value": text,
            "methodology_status": "unknown",
            "reason": "short answer while methodology slot is active — treated as current approach",
        }

    # Longer ambiguous messages — use LLM classifier
    try:
        _llm_prompt = f"""You are classifying whether the visitor message answers the current question:
"What are you currently using for this business challenge?"

Visitor message: {text}

Return JSON only:
{{
  "is_methodology_answer": true/false,
  "methodology_value": "...",
  "methodology_status": "known" | "unknown" | "none" | "unclear",
  "reason": "short reason"
}}

Classify as true if the visitor gives any tool, source, process, person, channel, platform, or current approach.
Classify as true even if the method is unknown or informal.
Classify as true for "nothing", "none", "not sure", or "I don't know"; use methodology_status "none" or "unknown".
Classify as false for generic confirmation like "yes", "ok", "sure".
Classify as false for a new question like pricing, demo request, human handoff, or "what is Nexy?"
"""
        _raw = (generate_answer(_llm_prompt) or "").strip()
        if _raw.startswith("```"):
            _raw = _raw.strip("`").replace("json", "", 1).strip()
        _result = json.loads(_raw)
        if isinstance(_result, dict) and "is_methodology_answer" in _result:
            return {
                "is_methodology_answer": bool(_result.get("is_methodology_answer")),
                "methodology_value": str(_result.get("methodology_value") or text).strip(),
                "methodology_status": str(_result.get("methodology_status") or "unknown").strip(),
                "reason": str(_result.get("reason") or "llm_classified").strip(),
            }
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: methodology slot LLM classifier failed",
        )

    # Fallback: treat as methodology when slot is active and no clear disqualifier
    return {
        "is_methodology_answer": True,
        "methodology_value": text,
        "methodology_status": "unknown",
        "reason": "slot active, no disqualifier found — stored as current approach",
    }


_CAPABILITY_MENU_AREA_KEYS = {
    "requirement_discovery",
    "enquiry_qualification",
    "lead_context_capture",
    "guided_next_step",
    "representative_handoff",
    "appointment_readiness",
    "visitor_conversation",
}


def _classify_capability_menu_reply(visitor_message, menu_items=None):
    """
    Semantic classifier for the visitor's reply to the controller-owned Nexy
    capability menu ("Which of these would you like help with?").

    Keyword lists cannot cover every rejection phrasing ("None of the above",
    "these don't help me", ...), so the routing decision is made by the LLM.

    menu_items: optional list of playbook capability rows — when provided, the
    prompt lists the exact display titles the visitor saw, so a reply echoing a
    playbook title maps to the right canonical area key.

    Returns a dict:
        {"reply_type": "area_selection" | "declined" | "consultancy_interest" | "unclear",
         "selected_area": "<area key or None>",
         "reason": "short reason"}
    or None on any LLM/parse failure — the caller falls back to the
    deterministic keyword chain.
    """
    text = str(visitor_message or "").strip()
    if not text:
        return None

    if menu_items:
        area_lines = "\n".join(
            f"- {row.capability_area} ({(row.display_title or '').strip()})"
            for row in menu_items
            if (getattr(row, "capability_area", "") or "").strip()
        )
    else:
        area_lines = (
            "- visitor_conversation (Visitor conversation)\n"
            "- requirement_discovery (Requirement discovery)\n"
            "- enquiry_qualification (Enquiry qualification)\n"
            "- lead_context_capture (Lead context capture)\n"
            "- guided_next_step (Guided next step)\n"
            "- representative_handoff (Representative handoff)\n"
            "- appointment_readiness (Appointment readiness)"
        )

    prompt = f"""You are classifying a visitor's reply in a business chat.

Context: the assistant just told the visitor it has NO confirmed capability matching their
specific need, listed the capability areas it CAN help with, and asked:
"Which of these would you like help with?"

The listed areas (with their keys) are:
{area_lines}

Visitor reply: {text}

Classify the reply as exactly one of:
- "declined": the visitor indicates none of the listed areas match their need, is not
  interested in them, or wants to stop/close the conversation — in ANY phrasing
  (e.g. "None of the above", "none of this I am interested", "these don't help me",
  "this isn't what I need", "forget it", "no thanks", "stop").
- "area_selection": the visitor picks one of the listed areas. A negated mention
  ("I'm not interested in requirement discovery") is NOT a selection — that is "declined".
- "consultancy_interest": the visitor asks to book a meeting/demo/consultation or to
  speak with a human/representative.
- "unclear": vague or ambiguous replies like "maybe", "what", "not sure", "explain more".

Return JSON only:
{{"reply_type": "declined" | "area_selection" | "consultancy_interest" | "unclear",
 "selected_area": "<area key from the list above, or null>",
 "reason": "short reason"}}"""

    try:
        raw = (generate_answer(prompt) or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json", "", 1).strip()
        result = json.loads(raw)
        if not isinstance(result, dict):
            return None

        reply_type = str(result.get("reply_type") or "").strip()
        if reply_type not in {"declined", "area_selection", "consultancy_interest", "unclear"}:
            return None

        selected_area = result.get("selected_area")
        selected_area = str(selected_area).strip() if selected_area else None
        # Valid keys are the ones actually shown to the visitor: the playbook's
        # capability areas when configured, otherwise the canonical set.
        valid_keys = (
            {
                (getattr(row, "capability_area", "") or "").strip()
                for row in menu_items
            }
            if menu_items
            else _CAPABILITY_MENU_AREA_KEYS
        )
        if reply_type == "area_selection" and selected_area not in valid_keys:
            # Selection without a valid area key cannot be routed — repeat the menu.
            reply_type = "unclear"
            selected_area = None

        return {
            "reply_type": reply_type,
            "selected_area": selected_area,
            "reason": str(result.get("reason") or "llm_classified").strip(),
        }
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: capability menu reply classifier failed",
        )
        return None


def send_companion_email_verification(conversation, email):
    """
    Generate a 6-digit OTP, store its SHA-256 hash with a 10-minute expiry, and
    send the plain OTP to the visitor via Frappe email queue.
    Returns {"status": "sent"} on success or {"status": "error", "reason": ...} on failure.
    """
    import hashlib as _hashlib
    import secrets as _secrets

    otp = str(_secrets.randbelow(900000) + 100000)
    otp_hash = _hashlib.sha256(otp.encode()).hexdigest()
    expires_on = frappe.utils.add_to_date(frappe.utils.now_datetime(), minutes=10)

    try:
        frappe.db.set_value(
            "Nexus Live Conversation",
            conversation.name,
            {
                "companion_email_verification_hash": otp_hash,
                "companion_email_verification_expires_on": expires_on,
                "companion_email_verification_retry_count": 0,
                "visitor_email": email,
            },
            update_modified=False,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Companion Controller: verification data save failed")
        return {"status": "error", "reason": "save_failed"}

    try:
        frappe.sendmail(
            recipients=[email],
            subject="Your Nexy Verification Code",
            message=(
                "<p>Your email verification code for Nexy is:</p>"
                f"<h2 style='letter-spacing:4px'>{otp}</h2>"
                "<p>This code expires in 10 minutes.</p>"
                "<p>If you did not request this, please ignore this email.</p>"
            ),
            now=True,
        )
        frappe.logger("nexus_debug").info(
            f"Companion email verification sent to {email} for conversation {conversation.name}"
        )
        return {"status": "sent", "email": email}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Companion Controller: email verification send failed")
        return {"status": "error", "reason": "send_failed"}


def verify_companion_email_code(conversation, code):
    """
    Verify the OTP the visitor entered.
    Checks hash, expiry, and retry limit.
    Clears the hash and sets companion_email_verified=1 on success.
    Returns {"verified": True} or {"verified": False, "reason": ...}.
    """
    import hashlib as _hashlib

    try:
        result = frappe.db.get_value(
            "Nexus Live Conversation",
            conversation.name,
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
            "Nexus Live Conversation",
            conversation.name,
            "companion_email_verification_retry_count",
            retry_count + 1,
            update_modified=False,
        )

        if expires_on:
            try:
                exp_dt = frappe.utils.get_datetime(str(expires_on))
                if frappe.utils.now_datetime() > exp_dt:
                    return {"verified": False, "reason": "code_expired"}
            except Exception:
                pass

        code_hash = _hashlib.sha256(str(code).encode()).hexdigest()
        if code_hash == stored_hash:
            frappe.db.set_value(
                "Nexus Live Conversation",
                conversation.name,
                {
                    "companion_email_verification_hash": "",
                    "companion_email_verified": 1,
                },
                update_modified=False,
            )
            frappe.logger("nexus_debug").info(
                f"Email verified for conversation {conversation.name}"
            )
            return {"verified": True}

        return {"verified": False, "reason": "invalid_code"}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Companion Controller: email verification check failed")
        return {"verified": False, "reason": "error"}


# ---------------------------------------------------------------------------
# Companion pending action helpers
# These replace fragile text scanning with explicit DB-stored state.
# The stored value always wins over text-scanned fallback.
# ---------------------------------------------------------------------------

def _get_companion_pending_action(conversation):
    """Read the stored pending action from the conversation record."""
    try:
        val = frappe.db.get_value(
            "Nexus Live Conversation",
            conversation.name,
            "companion_pending_action",
        )
        return (val or "").strip()
    except Exception:
        return (getattr(conversation, "companion_pending_action", None) or "").strip()


def _get_companion_pending_context(conversation):
    """Read the stored pending context JSON from the conversation record."""
    try:
        val = frappe.db.get_value(
            "Nexus Live Conversation",
            conversation.name,
            "companion_pending_context_json",
        )
        if not val:
            return {}
        return json.loads(val) if isinstance(val, str) else {}
    except Exception:
        return {}


def _set_companion_pending_action(conversation, action, context=None):
    """Persist the current pending action to the conversation record."""
    try:
        update_data = {"companion_pending_action": action or ""}
        if context is not None:
            update_data["companion_pending_context_json"] = json.dumps(context or {}, default=str)
        frappe.db.set_value(
            "Nexus Live Conversation",
            conversation.name,
            update_data,
            update_modified=False,
        )
        # Commit immediately so the next visitor turn (which may arrive via a separate
        # realtime/background worker request) reads the stored pending action from DB.
        frappe.db.commit()
        # Mirror to the in-memory object so same-request reads stay consistent.
        try:
            conversation.companion_pending_action = action or ""
            if context is not None:
                conversation.companion_pending_context_json = json.dumps(context or {}, default=str)
        except Exception:
            pass
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Companion Controller: set pending action failed")
        return

    _companion_flow_debug("PENDING ACTION SET", {
        "conversation": getattr(conversation, "name", None),
        "action": action,
        "context": context,
        "db_status": _get_companion_db_status(conversation),
    })


def _clear_companion_pending_action(conversation):
    """Clear the stored pending action (conversation reached a terminal state)."""
    _set_companion_pending_action(conversation, "", None)


def _sync_pending_action_from_decision(conversation, decision, steering=None):
    """
    After each turn, persist the pending action that the controller decision implies.
    Decisions that expect visitor input → store specific action string.
    Terminal decisions → clear.
    Neutral decisions → leave unchanged.
    """
    action_map = {
        "collect_email_for_consultancy": "collect_email_for_consultancy",
        "collect_email_for_appointment": "collect_email_for_appointment",
        "verify_email_for_consultancy": "verify_email_for_consultancy",
        "verify_email_for_appointment": "verify_email_for_appointment",
        "collect_representative_note": "collect_representative_note",
        "ask_more_clarification_or_consultancy": "ask_more_clarification_or_consultancy",
        "capture_closing_feedback": "capture_closing_feedback",
        "appointment_declined_collect_note": "appointment_declined_collect_note",
        "email_declined_collect_note": "email_declined_collect_note",
        # After a grounded capability-area explanation, offer another area or a
        # consultation — the existing pending handler covers both routes.
        "drill_nexy_capability_area": "ask_more_clarification_or_consultancy",
    }
    clear_decisions = {
        "show_meeting_booking_card",
        "confirm_consultancy_request",
        "close_conversation",
        "demo_rejected",
        "capability_menu_declined",
    }

    if decision in action_map:
        action = action_map[decision]
        ctx = {
            "decision": decision,
            "methodology_context_area": (steering or {}).get("methodology_context_area"),
            "current_methodology": (steering or {}).get("current_methodology"),
        }
        # Keep the verification resend counter across verify-stage turns so the
        # resend limit cannot be bypassed by sending another message. A fresh
        # email-collection stage naturally resets it.
        if action in ("verify_email_for_consultancy", "verify_email_for_appointment"):
            _existing_ctx = _get_companion_pending_context(conversation)
            if _existing_ctx.get("resend_count"):
                ctx["resend_count"] = _existing_ctx.get("resend_count")
        _set_companion_pending_action(conversation, action, ctx)
    elif decision in clear_decisions:
        _clear_companion_pending_action(conversation)
    elif decision == "discover_current_methodology":
        ctx = {
            "decision": decision,
            "context_area": (steering or {}).get("methodology_context_area")
            or _infer_context_area_from_challenge((steering or {}).get("pain_point_challenges") or ""),
            "expected_slot": "current_methodology",
            "challenge": (steering or {}).get("pain_point_challenges") or "",
            "asked_by_decision": "discover_current_methodology",
        }
        _set_companion_pending_action(conversation, "collect_current_methodology", ctx)
    elif decision == "check_matching_capability":
        # A grounded capability match was confirmed (the no-match path returns
        # earlier with pending select_nexy_capability_area). Expect interest,
        # clarification, or decline next — same as after capability visibility.
        ctx = {
            "decision": decision,
            "methodology_context_area": (steering or {}).get("methodology_context_area"),
            "pain_point_challenges": (steering or {}).get("pain_point_challenges"),
        }
        _set_companion_pending_action(conversation, "confirm_nexy_companion_interest", ctx)
    elif decision == "present_nexy_capability_visibility":
        ctx = {
            "decision": decision,
            "methodology_context_area": (steering or {}).get("methodology_context_area"),
            "current_methodology": (steering or {}).get("current_methodology"),
            "pain_point_challenges": (steering or {}).get("pain_point_challenges"),
        }
        _set_companion_pending_action(conversation, "confirm_nexy_companion_interest", ctx)


def _decorate_email_collection_response(response, conversation, purpose="demo_or_consultancy_booking"):
    """Attach the metadata keys that trigger the existing frontend email verification dialog."""
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

def _capability_presentation_steering(
    intent,
    confidence,
    challenge,
    current_methodology,
    methodology_status,
    business_context,
    fact_context_area,
    internal_intent="present_nexy_value_after_methodology_capture",
):
    """
    After the methodology slot is filled, decide how Nexy value is presented.

    Lead-generation / enquiry handling is Nexy's confirmed home domain, so those
    challenges get the full capability-visibility summary. Any other challenge
    area (system implementation, operations, customer support, general) must
    first pass the challenge-specific capability-fit check — Nexy must never
    present a capability summary that implies it can solve a challenge outside
    its confirmed knowledge (e.g. "Hospital Management System Implementation").
    """
    fit_area = _infer_context_area_from_challenge(challenge)

    if fit_area == "lead_generation":
        return {
            "decision": "present_nexy_capability_visibility",
            "knowledge_needed": True,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": internal_intent,
            "milestone_policy": "solution_mapping",
            "methodology_context_area": fact_context_area,
            "current_methodology": current_methodology,
            "current_methodology_status": methodology_status,
            "pain_point_challenges": challenge,
            "business_context": business_context,
            "grounding_mode": "nexus_knowledge_only",
        }

    return {
        "decision": "check_matching_capability",
        "knowledge_needed": True,
        "redirect_to_milestone": False,
        "visitor_external_intent": intent,
        "external_intent_confidence": confidence,
        "internal_intent": "check_capability_fit_for_non_lead_challenge",
        "milestone_policy": "capability_fit_check",
        "pain_point_challenges": challenge,
        "current_methodology": current_methodology,
        "current_methodology_status": methodology_status,
        "methodology_context_area": fit_area,
        "business_context": business_context,
    }


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
    
    # Legacy demo hard-interrupts — blocked when the new consultancy flow is active.
    _consultancy_pending = pending_action in {
        "collect_email_for_consultancy",
        "verify_email_for_consultancy",
        "collect_representative_note",
        "ask_more_clarification_or_consultancy",
        "appointment_declined_collect_note",
        "email_declined_collect_note",
        "capture_closing_feedback",
    }

    # ------------------------------------------------------------------
    # High-priority guard: collect_representative_note
    # Runs before all other routing to prevent visitor replies such as
    # "Yes" from being misrouted to demo confirmation or other intents.
    # Replaces B1 below — do not duplicate processing there.
    # ------------------------------------------------------------------
    if pending_action == "collect_representative_note":
        _nf_g = _accumulated or {}
        _nf_g_challenge = _nf_g.get("current_challenges") or ""
        if isinstance(_nf_g_challenge, list):
            _nf_g_challenge = ", ".join(str(c) for c in _nf_g_challenge if c)
        _nf_g_context_area = _detect_context_area_from_challenge(_nf_g_challenge)

        _msg_low_g = visitor_message.lower().strip()
        _skip_words_g = ["skip", "no thanks", "no thank you", "nope", "pass", "not now", "maybe later"]
        _is_skip_g = any(w in _msg_low_g for w in _skip_words_g) or _msg_low_g in {"no", "skip"}
        _ack_only_g = {"yes", "y", "sure", "ok", "okay", "yep", "yeah", "alright", "go ahead", "proceed"}
        _is_ack_g = _msg_low_g in _ack_only_g

        if _is_ack_g:
            return {
                "decision": "collect_representative_note",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "re_ask_for_note_after_acknowledgment",
                "milestone_policy": "conversion_preparation",
            }

        update_enquiry(
            conversation,
            {"discovery_facts": [{
                "context_area": _nf_g_context_area,
                "fact_type": "representative_note_collected",
                "fact_value": "skipped" if _is_skip_g else visitor_message[:500],
                "source_message": visitor_message,
            }]},
            signal=None,
        )
        
        _nf_g_email_verified = _is_booking_email_verified(conversation)
        
        print(f"DEBUG: _decide_steering: representative_note_collected, email_verified={_nf_g_email_verified}")
        
        if _nf_g_email_verified:
            return {
                "decision": "show_meeting_booking_card",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "show_booking_card_after_note",
                "milestone_policy": "appointment_booking",
            }
        return {
            "decision": "collect_email_for_consultancy",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "collect_email_after_note_collected",
            "milestone_policy": "appointment_booking",
        }

    if intent == "demo_confirmation" and pending_action == "demo_request" and not _consultancy_pending:
        return {
            "decision": "confirm_demo_request",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "create_or_prepare_demo_request",
            "milestone_policy": "conversion_confirmed",
        }

    if intent == "demo_rejection" and pending_action == "demo_request" and not _consultancy_pending:
        return {
            "decision": "demo_rejected",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "continue_discovery_without_demo",
            "milestone_policy": "conversion_declined",
        }

    # ==================================================================
    # NEW MAIN FLOW: Nexy Capability Visibility
    # ==================================================================
    # Runs regardless of intent classification, after hard interrupts.
    # Priority order:
    #   A. Leaving signals → capture feedback / close
    #   B. Pending action handlers (note, email, verification)
    #   C. Explicit methodology-support question → check_methodology_knowledge (exception)
    #   D. Capability summary shown → clarification / appointment / bounce
    #   E. Challenge + methodology known → present_nexy_capability_visibility
    #   F. Challenge known, methodology unknown → discover_current_methodology
    # ==================================================================

    _nf = _accumulated or {}

    _nf_challenge_text = (
        _nf.get("current_challenges")
        or discovery_delta.get("current_challenges")
        or ""
    )
    if isinstance(_nf_challenge_text, list):
        _nf_challenge_text = ", ".join(str(c) for c in _nf_challenge_text if c)

    _nf_context_area = _detect_context_area_from_challenge(_nf_challenge_text)
    _nf_methodology = _get_current_methodology_value(_nf, _nf_context_area)

    # Normalise from raw message if extraction missed it
    if _nf_challenge_text and not _nf_methodology and _looks_like_methodology_answer(visitor_message):
        _nf_methodology = _normalise_methodology_answer(visitor_message)
        update_enquiry(
            conversation,
            {
                "discovery_facts": [{
                    "context_area": _nf_context_area,
                    "fact_type": "current_methodology",
                    "fact_value": _nf_methodology,
                    "source_message": visitor_message,
                }]
            },
            signal=None,
        )

    _nf_methodology_known = bool(_nf_methodology)
    _nf_methodology_status = _get_current_methodology_status(_nf, _nf_context_area)
    _nf_capability_summary_shown = _capability_summary_presented(_nf, _nf_context_area)
    _nf_representative_note_collected = _has_fact(_nf, _nf_context_area, "representative_note_collected")

    # ------------------------------------------------------------------
    # A. Leaving signal
    # ------------------------------------------------------------------
    if _nf_challenge_text and _is_leaving_signal(visitor_message):
        if not _nf_representative_note_collected:
            return {
                "decision": "capture_closing_feedback",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "capture_feedback_before_close",
                "milestone_policy": "closing",
                "pain_point_challenges": _nf_challenge_text,
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
            }
        return {
            "decision": "close_conversation",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "close_politely",
            "milestone_policy": "closing",
        }

    # ------------------------------------------------------------------
    # B1a. Pending: select Nexy capability area
    # The controller showed the capability menu after a failed capability-fit
    # check and is waiting for the visitor to pick an area. Consultancy
    # interest and declines still route to the existing booking/note flows.
    # ------------------------------------------------------------------
    if pending_action == "select_nexy_capability_area":
        _sel_pctx = _get_companion_pending_context(conversation)
        _sel_challenge = _sel_pctx.get("challenge") or _nf_challenge_text or ""

        # Route the menu reply semantically — hardcoded phrase lists cannot cover
        # every rejection phrasing ("None of the above", "these don't help me", ...).
        # The keyword helpers below act only as the fallback when the classifier
        # call fails, so the turn still routes safely without the LLM.
        # Pass the playbook capability rows so the classifier sees the exact menu
        # titles the visitor was shown.
        _menu_cls = _classify_capability_menu_reply(
            visitor_message,
            menu_items=_get_playbook_capability_items(
                _get_companion_playbook_doc(conversation)
            ),
        )

        if _menu_cls:
            _menu_route = _menu_cls["reply_type"]
            _menu_area = _menu_cls.get("selected_area")
        elif _is_capability_menu_declined(visitor_message):
            _menu_route, _menu_area = "declined", None
        elif _looks_like_consultancy_interest(visitor_message):
            _menu_route, _menu_area = "consultancy_interest", None
        elif _looks_like_meeting_decline(visitor_message):
            _menu_route, _menu_area = "meeting_decline", None
        else:
            _menu_area = _detect_selected_nexy_capability_area(visitor_message)
            _menu_route = "area_selection" if _menu_area else "unclear"

        _companion_flow_debug("CAPABILITY MENU REPLY ROUTE", {
            "classifier_used": bool(_menu_cls),
            "route": _menu_route,
            "selected_area": _menu_area,
            "reason": (_menu_cls or {}).get("reason"),
        })

        if _menu_route == "declined":
            return {
                "decision": "capability_menu_declined",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "visitor_declined_available_nexy_capability_areas",
                "milestone_policy": "closing",
                "pain_point_challenges": _sel_challenge,
                "methodology_context_area": _infer_context_area_from_challenge(_sel_challenge),
            }

        if _menu_route == "consultancy_interest":
            return {
                "decision": "collect_email_for_consultancy",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_email_after_consultancy_interest",
                "milestone_policy": "appointment_booking",
                "pain_point_challenges": _sel_challenge,
                "methodology_context_area": _infer_context_area_from_challenge(_sel_challenge),
            }

        if _menu_route == "meeting_decline":
            return {
                "decision": "appointment_declined_collect_note",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_note_after_meeting_declined",
                "milestone_policy": "note_collection",
            }

        if _menu_route == "area_selection" and _menu_area:
            return {
                "decision": "drill_nexy_capability_area",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": "capability_area_selection",
                "external_intent_confidence": 1.0,
                "internal_intent": "explain_selected_nexy_capability_area",
                "milestone_policy": "capability_explanation",
                "selected_capability_area": _menu_area,
                "pain_point_challenges": _sel_challenge,
                "methodology_context_area": _infer_context_area_from_challenge(_sel_challenge),
                "business_context": _build_business_context(_nf),
            }

        return {
            "decision": "bounce_back_to_nexy_capabilities",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": "unclear_capability_selection",
            "external_intent_confidence": 0.5,
            "internal_intent": "visitor_selection_unclear",
            "milestone_policy": "capability_menu",
            "pain_point_challenges": _sel_challenge,
        }

    # ------------------------------------------------------------------
    # B1. Pending: collect current methodology slot
    # The controller asked "what are you currently using?" and is waiting
    # for the visitor's answer. Classify the reply and fill the slot.
    # Falls through to normal intent routing if the visitor asked a new
    # question (pricing, demo, product) instead of answering the slot.
    # ------------------------------------------------------------------
    if pending_action == "collect_current_methodology":
        _pctx = _get_companion_pending_context(conversation)
        _cm_context_area = _pctx.get("context_area") or _nf_context_area or "lead_generation"
        _cm_challenge = _pctx.get("challenge") or _nf_challenge_text or ""

        # Requirement / solution-need statements ("we need software solution",
        # "nothing yet", "looking for a system") are NOT a current methodology.
        # Verify capability fit against Nexus Orbit before making any claim,
        # instead of storing the requirement as the visitor's lead source.
        if _looks_like_solution_need(visitor_message) and not _looks_like_current_methodology(visitor_message):
            _cf_challenge = _cm_challenge or visitor_message
            _cf_context_area = _infer_context_area_from_challenge(_cf_challenge)

            return {
                "decision": "check_matching_capability",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "visitor_needs_solution_not_current_methodology",
                "milestone_policy": "capability_fit_check",
                "pain_point_challenges": _cf_challenge,
                "current_methodology": "",
                "methodology_context_area": _cf_context_area,
                "business_context": _build_business_context(_nf),
            }

        # Deterministic fast path for common source/method answers.
        # This prevents "Facebook ads" from falling into result-discovery.
        if _looks_like_methodology_answer(visitor_message):
            _cm_value = _normalise_methodology_answer(visitor_message)
            _cm_status = "known"

            update_enquiry(
                conversation,
                {
                    "discovery_facts": [
                        {
                            "context_area": _cm_context_area,
                            "fact_type": "current_methodology",
                            "fact_value": _cm_value,
                            "source_message": visitor_message,
                        },
                        {
                            "context_area": _cm_context_area,
                            "fact_type": "current_methodology_status",
                            "fact_value": _cm_status,
                            "related_value": _cm_value,
                            "source_message": "deterministic_methodology_match",
                        },
                    ]
                },
                signal=None,
            )

            _clear_companion_pending_action(conversation)

            return _capability_presentation_steering(
                intent="methodology_answer",
                confidence=1.0,
                challenge=_cm_challenge,
                current_methodology=_cm_value,
                methodology_status=_cm_status,
                business_context=_nf.get("industry") or _nf.get("business_type") or "",
                fact_context_area=_cm_context_area,
                internal_intent="present_nexy_value_after_methodology_capture",
            )

        slot = _classify_current_methodology_slot_answer(
            visitor_message=visitor_message,
            pending_context=_pctx,
        )

        if slot.get("is_methodology_answer"):
            _cm_value = (slot.get("methodology_value") or visitor_message).strip()
            _cm_status = slot.get("methodology_status") or "unknown"
            update_enquiry(
                conversation,
                {
                    "discovery_facts": [
                        {
                            "context_area": _cm_context_area,
                            "fact_type": "current_methodology",
                            "fact_value": _cm_value,
                            "source_message": visitor_message,
                        },
                        {
                            "context_area": _cm_context_area,
                            "fact_type": "current_methodology_status",
                            "fact_value": _cm_status,
                            "related_value": _cm_value,
                            "source_message": "slot_classifier",
                        },
                    ]
                },
                signal=None,
            )
            _clear_companion_pending_action(conversation)
            return _capability_presentation_steering(
                intent="methodology_answer",
                confidence=1.0,
                challenge=_cm_challenge,
                current_methodology=_cm_value,
                methodology_status=_cm_status,
                business_context=_nf.get("industry") or _nf.get("business_type") or "",
                fact_context_area=_cm_context_area,
                internal_intent="present_nexy_value_after_methodology_capture",
            )

        # Not a methodology answer — handle recognised intents directly so the
        # E/F challenge-methodology routing cannot intercept and re-ask methodology.
        # The pending action stays stored so the next substantive reply fills the slot.
        if intent == "pricing_question":
            return {
                "decision": "answer_with_orbit_or_policy",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "handle_pricing_question_during_methodology_collection",
                "milestone_policy": "allowed",
            }

        if intent == "human_request":
            return {
                "decision": "offer_escalation",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "offer_human_assistance_during_methodology_collection",
                "milestone_policy": "hard_interrupt",
            }

        if intent == "product_question":
            return {
                "decision": "answer_with_orbit",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "answer_product_question_during_methodology_collection",
                "milestone_policy": "allowed",
            }

        if intent == "demo_interest":
            return {
                "decision": "consider_next_step",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "acknowledge_demo_interest_during_methodology_collection",
                "milestone_policy": "allowed",
            }

        # Unknown or ambiguous — fall through to re-ask / unknown-and-proceed logic
        else:
            # Re-ask once; if already re-asked, store as unknown and proceed.
            _cm_ask_count = int(
                _get_fact_value(_nf, _cm_context_area, "methodology_slot_ask_count") or "0"
            )
            if _cm_ask_count >= 1:
                # Asked twice — store as unknown and show Nexy value anyway
                _cm_value_fb = "Unknown current methodology"
                update_enquiry(
                    conversation,
                    {
                        "discovery_facts": [
                            {
                                "context_area": _cm_context_area,
                                "fact_type": "current_methodology",
                                "fact_value": _cm_value_fb,
                                "source_message": visitor_message,
                            },
                            {
                                "context_area": _cm_context_area,
                                "fact_type": "current_methodology_status",
                                "fact_value": "unclear",
                                "related_value": _cm_value_fb,
                                "source_message": "slot_classifier",
                            },
                        ]
                    },
                    signal=None,
                )
                _clear_companion_pending_action(conversation)
                return _capability_presentation_steering(
                    intent="methodology_answer",
                    confidence=0.5,
                    challenge=_cm_challenge,
                    current_methodology=_cm_value_fb,
                    methodology_status="unclear",
                    business_context=_nf.get("industry") or _nf.get("business_type") or "",
                    fact_context_area=_cm_context_area,
                    internal_intent="present_nexy_value_after_unclear_methodology",
                )
            # First unclear — re-ask the methodology question once
            update_enquiry(
                conversation,
                {
                    "discovery_facts": [{
                        "context_area": _cm_context_area,
                        "fact_type": "methodology_slot_ask_count",
                        "fact_value": str(_cm_ask_count + 1),
                        "source_message": "slot_classifier",
                    }]
                },
                signal=None,
            )
            return {
                "decision": "discover_current_methodology",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "re_ask_current_methodology_slot",
                "milestone_policy": "pain_discovery",
                "pain_point_challenges": _cm_challenge,
                "methodology_context_area": _cm_context_area,
            }

    # ------------------------------------------------------------------
    # B2. Pending: collect email for appointment
    # ------------------------------------------------------------------
    if pending_action == "collect_email_for_appointment":
        import re as _re
        _email_match = _re.search(r'[\w.\-+]+@[\w.\-]+\.[a-zA-Z]{2,}', visitor_message)
        if _email_match:
            _collected_email = _email_match.group(0)
            try:
                frappe.db.set_value(
                    "Nexus Live Conversation", conversation.name,
                    "visitor_email", _collected_email, update_modified=False,
                )
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Companion Controller: visitor_email set failed")
            send_companion_email_verification(conversation, _collected_email)
            update_enquiry(
                conversation,
                {"discovery_facts": [{
                    "context_area": _nf_context_area,
                    "fact_type": "email_verification_status",
                    "fact_value": "pending",
                    "source_message": _collected_email,
                }]},
                signal=None,
            )
            return {
                "decision": "verify_email_for_appointment",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "verify_email_before_appointment",
                "milestone_policy": "appointment_booking",
                "collected_email": _collected_email,
            }
        _msg_low = visitor_message.lower().strip()
        if any(w in _msg_low for w in ["skip", "no ", "later", "don't want", "prefer not", "not now"]):
            if not _nf_representative_note_collected:
                return {
                    "decision": "collect_representative_note",
                    "knowledge_needed": False,
                    "redirect_to_milestone": False,
                    "visitor_external_intent": intent,
                    "external_intent_confidence": confidence,
                    "internal_intent": "collect_note_when_email_declined",
                    "milestone_policy": "note_collection",
                }
            return {
                "decision": "close_conversation",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "close_after_email_declined",
                "milestone_policy": "closing",
            }
        return {
            "decision": "collect_email_for_appointment",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "ask_valid_email_again",
            "milestone_policy": "appointment_booking",
        }

    # ------------------------------------------------------------------
    # B3. Pending: verify email (appointment or consultancy flow)
    # ------------------------------------------------------------------
    if pending_action in ("verify_email_for_appointment", "verify_email_for_consultancy"):
        import re as _re

        # Resend request — issue a fresh code. send_companion_email_verification
        # overwrites the stored hash and resets the retry counter, so the
        # previous code stops validating the moment the new one is sent.
        if _looks_like_resend_code_request(visitor_message):
            _vp_ctx = _get_companion_pending_context(conversation)
            _resend_count = int(_vp_ctx.get("resend_count") or 0)
            _resend_email = (
                frappe.db.get_value(
                    "Nexus Live Conversation", conversation.name, "visitor_email"
                ) or ""
            ).strip()

            if not _resend_email:
                return {
                    "decision": "collect_email_for_consultancy",
                    "knowledge_needed": False,
                    "redirect_to_milestone": False,
                    "visitor_external_intent": intent,
                    "external_intent_confidence": confidence,
                    "internal_intent": "re_collect_email_for_resend",
                    "milestone_policy": "appointment_booking",
                }

            if _resend_count >= 3:
                return {
                    "decision": "verify_email_for_consultancy",
                    "knowledge_needed": False,
                    "redirect_to_milestone": False,
                    "visitor_external_intent": intent,
                    "external_intent_confidence": confidence,
                    "internal_intent": "resend_limit_reached",
                    "milestone_policy": "appointment_booking",
                }

            _resend_result = send_companion_email_verification(conversation, _resend_email)
            _set_companion_pending_action(
                conversation,
                pending_action,
                {**_vp_ctx, "resend_count": _resend_count + 1},
            )

            _companion_flow_debug("VERIFICATION CODE RESENT", {
                "conversation": conversation.name,
                "email": _resend_email,
                "resend_count": _resend_count + 1,
                "send_status": _resend_result.get("status"),
            })

            return {
                "decision": "verify_email_for_consultancy",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": (
                    "resent_verification_code"
                    if _resend_result.get("status") == "sent"
                    else "resend_verification_failed"
                ),
                "milestone_policy": "appointment_booking",
                "collected_email": _resend_email,
            }

        _code_match = _re.search(r'\b\d{4,8}\b', visitor_message)
        if _code_match:
            _verify_result = verify_companion_email_code(conversation, _code_match.group(0))
            if _verify_result.get("verified"):
                update_enquiry(
                    conversation,
                    {"discovery_facts": [{
                        "context_area": _nf_context_area,
                        "fact_type": "email_verification_status",
                        "fact_value": "verified",
                        "source_message": _code_match.group(0),
                    }]},
                    signal=None,
                )
                # Always collect representative note before booking
                if not _nf_representative_note_collected:
                    return {
                        "decision": "collect_representative_note",
                        "knowledge_needed": False,
                        "redirect_to_milestone": False,
                        "visitor_external_intent": intent,
                        "external_intent_confidence": confidence,
                        "internal_intent": "collect_note_after_email_verified",
                        "milestone_policy": "note_collection",
                    }
                return {
                    "decision": "show_meeting_booking_card",
                    "knowledge_needed": False,
                    "redirect_to_milestone": False,
                    "visitor_external_intent": intent,
                    "external_intent_confidence": confidence,
                    "internal_intent": "show_booking_card_after_verification",
                    "milestone_policy": "appointment_booking",
                }

            # Code entered but validation failed — tell the visitor why and
            # how to recover (re-enter or ask for a fresh code) instead of
            # silently repeating "enter the code".
            _vfail_reason = (_verify_result.get("reason") or "invalid_code").strip()
            _vfail_intent = {
                "code_expired": "verification_code_expired",
                "max_retries_exceeded": "verification_max_retries",
                # No hash stored — the old code cannot validate; a fresh one is needed.
                "no_pending_verification": "verification_code_expired",
            }.get(_vfail_reason, "verification_code_invalid")

            return {
                "decision": "verify_email_for_consultancy",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": _vfail_intent,
                "milestone_policy": "appointment_booking",
            }
        _msg_low_verify = visitor_message.lower().strip()
        if any(w in _msg_low_verify for w in ["skip", "cancel", "no code", "don't have", "not interested"]):
            if not _nf_representative_note_collected:
                return {
                    "decision": "collect_representative_note",
                    "knowledge_needed": False,
                    "redirect_to_milestone": False,
                    "visitor_external_intent": intent,
                    "external_intent_confidence": confidence,
                    "internal_intent": "collect_note_when_verification_skipped",
                    "milestone_policy": "note_collection",
                }
            return {
                "decision": "close_conversation",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "close_after_verification_declined",
                "milestone_policy": "closing",
            }
        return {
            "decision": "verify_email_for_consultancy",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "ask_verification_code_again",
            "milestone_policy": "appointment_booking",
        }

    # ------------------------------------------------------------------
    # B4. Pending: collect email for consultancy
    # ------------------------------------------------------------------
    if pending_action == "collect_email_for_consultancy":
        import re as _re
        _email_match = _re.search(r'[\w.\-+]+@[\w.\-]+\.[a-zA-Z]{2,}', visitor_message)
        if _email_match:
            _collected_email = _email_match.group(0)
            try:
                frappe.db.set_value(
                    "Nexus Live Conversation", conversation.name,
                    "visitor_email", _collected_email, update_modified=False,
                )
            except Exception:
                frappe.log_error(frappe.get_traceback(), "Companion Controller: visitor_email set failed")
            send_companion_email_verification(conversation, _collected_email)
            update_enquiry(
                conversation,
                {"discovery_facts": [{
                    "context_area": _nf_context_area,
                    "fact_type": "email_verification_status",
                    "fact_value": "pending",
                    "source_message": _collected_email,
                }]},
                signal=None,
            )
            return {
                "decision": "verify_email_for_consultancy",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "verify_email_before_consultancy",
                "milestone_policy": "appointment_booking",
                "collected_email": _collected_email,
            }
        _msg_low_ce = visitor_message.lower().strip()
        if any(w in _msg_low_ce for w in ["skip", "no ", "later", "don't want", "prefer not", "not now", "decline"]):
            update_enquiry(
                conversation,
                {"discovery_facts": [{
                    "context_area": _nf_context_area,
                    "fact_type": "meeting_interest",
                    "fact_value": "email_declined",
                    "source_message": visitor_message,
                }]},
                signal=None,
            )
            if not _nf_representative_note_collected:
                return {
                    "decision": "email_declined_collect_note",
                    "knowledge_needed": False,
                    "redirect_to_milestone": False,
                    "visitor_external_intent": intent,
                    "external_intent_confidence": confidence,
                    "internal_intent": "collect_note_when_email_declined",
                    "milestone_policy": "note_collection",
                }
            return {
                "decision": "close_conversation",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "close_after_email_declined",
                "milestone_policy": "closing",
            }
        # No valid email and no skip — ask again
        return {
            "decision": "collect_email_for_consultancy",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "ask_valid_email_again",
            "milestone_policy": "appointment_booking",
        }

    # ------------------------------------------------------------------
    # B5. Pending: closing note / declined-meeting feedback / closing feedback
    # Visitor is responding to "leave a note or skip" after declining
    # a meeting or after email was declined.
    # ------------------------------------------------------------------
    if pending_action in (
        "appointment_declined_collect_note",
        "email_declined_collect_note",
        "capture_closing_feedback",
    ):
        _msg_low_fb = visitor_message.lower().strip()
        _skip_words_fb = ["skip", "no thanks", "no thank you", "nope", "pass", "not now", "none", "nothing"]
        _is_skip_fb = any(w in _msg_low_fb for w in _skip_words_fb) or _msg_low_fb in {"no", "skip"}
        if not _is_skip_fb and visitor_message.strip():
            update_enquiry(
                conversation,
                {"discovery_facts": [{
                    "context_area": _nf_context_area,
                    "fact_type": "closing_feedback",
                    "fact_value": visitor_message[:500],
                    "source_message": visitor_message,
                }]},
                signal=None,
            )
        return {
            "decision": "close_conversation",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "close_after_feedback_collected",
            "milestone_policy": "closing",
        }

    # ------------------------------------------------------------------
    # B6. Pending: ask more clarification or consultancy
    # ------------------------------------------------------------------
    if pending_action == "ask_more_clarification_or_consultancy":
        # Route based on visitor's response to "another area or demo/consultation?"
        if _looks_like_consultancy_interest(visitor_message):
            return {
                "decision": "collect_email_for_consultancy",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_email_after_consultancy_interest",
                "milestone_policy": "appointment_booking",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
                "pain_point_challenges": _nf_challenge_text,
            }
        if _looks_like_meeting_decline(visitor_message):
            return {
                "decision": "appointment_declined_collect_note",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_note_after_meeting_declined",
                "milestone_policy": "note_collection",
            }
        if _looks_like_capability_clarification(visitor_message):
            _selected_area = _normalise_capability_area(visitor_message)
            update_enquiry(
                conversation,
                {"discovery_facts": [{
                    "context_area": _nf_context_area,
                    "fact_type": "selected_capability_area",
                    "fact_value": _selected_area,
                    "source_message": visitor_message,
                }]},
                signal=None,
            )
            return {
                "decision": "answer_nexy_capability_clarification",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "answer_capability_clarification_from_nexus_knowledge",
                "milestone_policy": "solution_mapping",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
                "pain_point_challenges": _nf_challenge_text,
                "selected_capability_area": _selected_area,
                "business_context": _nf.get("industry") or _nf.get("business_type") or "",
            }
        # Ambiguous — repeat the question
        return {
            "decision": "ask_more_clarification_or_consultancy",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "repeat_clarification_or_consultancy_offer",
            "milestone_policy": "solution_mapping",
        }

    # ------------------------------------------------------------------
    # B0. Pending: confirm Nexy companion interest
    # Set after present_nexy_capability_visibility is shown.
    # Generic "yes" or explicit booking interest → collect email.
    # Capability question → clarification path.
    # Decline → note collection.
    # ------------------------------------------------------------------
    if pending_action == "confirm_nexy_companion_interest":
        _msg_low_ci = visitor_message.lower().strip()
        _generic_yes_ci = {"yes", "y", "yeah", "yep", "ok", "okay", "sure", "alright", "go ahead", "proceed"}
        if _msg_low_ci in _generic_yes_ci or _looks_like_consultancy_interest(visitor_message):
            return {
                "decision": "collect_email_for_consultancy",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_email_after_nexy_interest_confirmed",
                "milestone_policy": "appointment_booking",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
                "pain_point_challenges": _nf_challenge_text,
            }
        if _looks_like_meeting_decline(visitor_message):
            return {
                "decision": "appointment_declined_collect_note",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_note_after_meeting_declined",
                "milestone_policy": "note_collection",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
            }
        if _looks_like_capability_clarification(visitor_message):
            _selected_area_ci = _normalise_capability_area(visitor_message)
            update_enquiry(
                conversation,
                {"discovery_facts": [{
                    "context_area": _nf_context_area,
                    "fact_type": "selected_capability_area",
                    "fact_value": _selected_area_ci,
                    "source_message": visitor_message,
                }]},
                signal=None,
            )
            return {
                "decision": "answer_nexy_capability_clarification",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "answer_capability_clarification_from_nexus_knowledge",
                "milestone_policy": "solution_mapping",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
                "pain_point_challenges": _nf_challenge_text,
                "selected_capability_area": _selected_area_ci,
                "business_context": _nf.get("industry") or _nf.get("business_type") or "",
            }
        # Unclear response — bounce back and repeat the CTA
        return {
            "decision": "bounce_back_to_nexy_capabilities",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "bounce_back_after_unclear_interest_response",
            "milestone_policy": "solution_mapping",
            "current_methodology": _nf_methodology,
            "methodology_context_area": _nf_context_area,
            "pain_point_challenges": _nf_challenge_text,
        }

    # ------------------------------------------------------------------
    # C. Explicit methodology-support question → check_methodology_knowledge (exception path only)
    # Normal "Google Ads" answers do NOT go here.
    # ------------------------------------------------------------------
    if _nf_challenge_text and _nf_methodology_known and _asks_about_methodology_support(visitor_message):
        _nf_meth_checked = _has_fact(
            _nf, _nf_context_area, "methodology_knowledge_status",
            related_value=_nf_methodology,
        )
        if not _nf_meth_checked:
            return {
                "decision": "check_methodology_knowledge",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "check_explicit_methodology_support_question",
                "milestone_policy": "solution_mapping",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
                "pain_point_challenges": _nf_challenge_text,
            }

    # ------------------------------------------------------------------
    # D. Capability summary already shown → clarification / consultancy / bounce
    #
    # Rule: Do NOT rush to meeting after first summary.
    # After summary: ask which area to understand better (done via E-branch ending).
    # After 1+ clarification answered: ask "another area or consultation?"
    # Meeting email collection only when visitor explicitly expresses interest.
    # ------------------------------------------------------------------
    if _nf_challenge_text and _nf_methodology_known and _nf_capability_summary_shown:

        _nf_clarification_count = int(
            _get_fact_value(_nf, _nf_context_area, "capability_clarification_count") or "0"
        )

        # D1. Visitor wants to book / demo / consultation
        if _looks_like_consultancy_interest(visitor_message):
            return {
                "decision": "collect_email_for_consultancy",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_email_after_consultancy_interest",
                "milestone_policy": "appointment_booking",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
                "pain_point_challenges": _nf_challenge_text,
            }

        # D2. Visitor declines meeting / not interested
        if _looks_like_meeting_decline(visitor_message):
            return {
                "decision": "appointment_declined_collect_note",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "collect_note_after_meeting_declined",
                "milestone_policy": "note_collection",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
            }

        # D3. Visitor asks for capability clarification
        if _looks_like_capability_clarification(visitor_message):
            _selected_area = _normalise_capability_area(visitor_message)
            update_enquiry(
                conversation,
                {"discovery_facts": [{
                    "context_area": _nf_context_area,
                    "fact_type": "selected_capability_area",
                    "fact_value": _selected_area,
                    "source_message": visitor_message,
                }]},
                signal=None,
            )
            return {
                "decision": "answer_nexy_capability_clarification",
                "knowledge_needed": True,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "answer_capability_clarification_from_nexus_knowledge",
                "milestone_policy": "solution_mapping",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
                "pain_point_challenges": _nf_challenge_text,
                "selected_capability_area": _selected_area,
                "business_context": _nf.get("industry") or _nf.get("business_type") or "",
            }

        # D4. After at least one clarification was answered — gently offer consultation
        if _nf_clarification_count >= 1:
            return {
                "decision": "ask_more_clarification_or_consultancy",
                "knowledge_needed": False,
                "redirect_to_milestone": False,
                "visitor_external_intent": intent,
                "external_intent_confidence": confidence,
                "internal_intent": "offer_consultancy_after_clarification",
                "milestone_policy": "solution_mapping",
                "current_methodology": _nf_methodology,
                "methodology_context_area": _nf_context_area,
                "pain_point_challenges": _nf_challenge_text,
            }

        # D5. No clarification yet, no clear intent → bounce and re-ask which area
        return {
            "decision": "bounce_back_to_nexy_capabilities",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "bounce_back_after_off_path_question",
            "milestone_policy": "solution_mapping",
            "current_methodology": _nf_methodology,
            "methodology_context_area": _nf_context_area,
            "pain_point_challenges": _nf_challenge_text,
        }

    # ------------------------------------------------------------------
    # E. Challenge + methodology known → main value moment
    # ------------------------------------------------------------------
    if _nf_challenge_text and _nf_methodology_known:
        return _capability_presentation_steering(
            intent=intent,
            confidence=confidence,
            challenge=_nf_challenge_text,
            current_methodology=_nf_methodology,
            methodology_status=_nf_methodology_status,
            business_context=_nf.get("industry") or _nf.get("business_type") or "",
            fact_context_area=_nf_context_area,
            internal_intent="present_nexy_capability_visibility_after_methodology",
        )

    # ------------------------------------------------------------------
    # F. Challenge known, methodology unknown → ask methodology
    # ------------------------------------------------------------------
    if _nf_challenge_text and not _nf_methodology_known:
        return {
            "decision": "discover_current_methodology",
            "knowledge_needed": False,
            "redirect_to_milestone": False,
            "visitor_external_intent": intent,
            "external_intent_confidence": confidence,
            "internal_intent": "understand_current_approach_before_capability_summary",
            "milestone_policy": "pain_discovery",
            "pain_point_challenges": _nf_challenge_text,
        }

    if intent == "pain_context_answer":
        # The new main flow (E/F above) handles challenge+methodology routing.
        # This block fires only when challenge extraction failed for the current message.
        # It serves as a backstop: if somehow we have methodology but no challenge in
        # accumulated, route to capability visibility; otherwise continue discovery.
        accumulated = _accumulated
        challenge_text = accumulated.get("current_challenges") or discovery_delta.get("current_challenges") or ""
        if isinstance(challenge_text, list):
            challenge_text = ", ".join(str(c) for c in challenge_text if c)
        context_area = _detect_context_area_from_challenge(challenge_text)

        methodology_known = (
            _has_fact(accumulated, context_area, "current_methodology")
            or _has_fact(accumulated, context_area, "current_approach")
            or _has_fact(accumulated, context_area, "current_tool")
            or bool(accumulated.get("existing_systems") or discovery_delta.get("existing_systems"))
        )

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

        mfact = (
            _find_fact(accumulated, context_area, "current_methodology")
            or _find_fact(accumulated, context_area, "current_approach")
            or _find_fact(accumulated, context_area, "current_tool")
        )
        if mfact:
            current_methodology_value = str(mfact.get("fact_value") or "").strip()
        else:
            raw_sys = accumulated.get("existing_systems") or discovery_delta.get("existing_systems") or ""
            current_methodology_value = (
                ", ".join(str(s) for s in raw_sys if s)
                if isinstance(raw_sys, list)
                else str(raw_sys)
            ).strip()

        return _capability_presentation_steering(
            intent=intent,
            confidence=confidence,
            challenge=challenge_text,
            current_methodology=current_methodology_value,
            methodology_status=_get_current_methodology_status(accumulated, context_area),
            business_context=accumulated.get("industry") or accumulated.get("business_type") or "",
            fact_context_area=context_area,
            internal_intent="present_nexy_capability_visibility_after_methodology",
        )

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
            # The new main flow (E/F) intercepts when challenge+methodology are already known.
            # If we're here, business context was shared but challenge/methodology routing
            # was not triggered. Continue onboarding.
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


def _looks_like_wrong_nexy_capability_visibility_answer(answer):
    text = str(answer or "").lower()

    wrong_markers = [
        "from here, i can focus",
        "nexy capability summary",
        "how effective",
        "how effective have you found",
        "what kind of results",
        "what results",
        "are you getting from",
        "how are your ads performing",
        "ad performance",
        "campaign performance",
        "specific aspects of your lead generation process",
        "what could be improved",
        "what do you feel could be improved",
        "nexy is designed",
        "nexy helps",
        "nexy can",
        "nexy focuses",
        "nexy works",
        "nexy supports",
    ]

    return any(marker in text for marker in wrong_markers)


def _build_safe_nexy_capability_visibility_answer(steering):
    
    methodology = (steering.get("current_methodology") or "your current lead source").strip()
    methodology_status = (steering.get("current_methodology_status") or "known").strip()

    if methodology_status == "none":
        opening = "Got it — you do not have a clear lead source in place yet."
        clarifier = "I can support the conversation once someone contacts your business."
    elif methodology_status == "unclear":
        opening = "Got it — your current lead source is not clearly defined yet."
        clarifier = "I can support the conversation once someone contacts your business."
    else:
        opening = f"Got it — {methodology} is how people are currently coming in."
        clarifier = (
            f"To be clear, I do not replace or manage {methodology}. "
            f"{methodology} may bring people in; I support what happens after someone contacts your business."
        )

    return (
        f"{opening}\n\n"
        "Once an enquiry comes in, I help structure the conversation, understand the requirement, "
        "qualify the opportunity, and guide the visitor toward the right next step.\n\n"
        "**How I can help after the enquiry:**\n"
        "- **Visitor conversation:** I can guide the visitor through a focused conversation instead of leaving the chat open-ended.\n"
        "- **Requirement discovery:** I can capture what the visitor is looking for, their challenge, and their business context.\n"
        "- **Buying signal understanding:** I can identify useful signals from the conversation so the team can see which enquiries need attention.\n"
        "- **Guided next step:** I can guide interested visitors toward a demo, consultation, or representative handoff when appropriate.\n"
        "- **Knowledge-based answers:** I answer from approved Nexus knowledge instead of guessing product or service details.\n\n"
        f"{clarifier}\n\n"
        "Would you like to explore this further or book a short session with a Nexy representative?"
    )
    
def _ensure_nexy_capability_visibility_response(response, steering):
    if not isinstance(response, dict):
        response = {}

    if response.get("access_status") in ("controlled_no_context", "restricted"):
        return response

    answer = response.get("answer") or ""

    if (
        "nexy capability summary" not in answer.lower()
        or _looks_like_wrong_nexy_capability_visibility_answer(answer)
    ):
        response["answer"] = _build_safe_nexy_capability_visibility_answer(steering)
        response["access_status"] = response.get("access_status") or "intent_handled"
        response["fallback_used"] = 0
        response["nexy_capability_visibility_guard_applied"] = True

    return response


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
        "present_nexy_capability_visibility",
        "present_nexy_capability_summary",
        "answer_nexy_capability_clarification",
        "drill_nexy_capability_area",
        "knowledge_gap_offer_consultant",
        "answer_solution_fit",
        "explain_solution_method",
        "check_methodology_knowledge",
        "check_matching_capability",
        "present_alternative_solution",
    }
    if decision in nexus_knowledge_decisions:
        steering["grounding_mode"] = "nexus_knowledge_only"
        steering["knowledge_needed"] = True
        return steering

    controller_only_decisions = {
        "discover_current_methodology",
        "ask_more_clarification_or_consultancy",
        "offer_demo_or_consultancy",
        "bounce_back_to_nexy_capabilities",
        "capability_menu_declined",
        "collect_email_for_consultancy",
        "verify_email_for_consultancy",
        "collect_email_for_appointment",
        "verify_email_for_appointment",
        "collect_representative_note",
        "show_meeting_booking_card",
        "create_consultancy_request",
        "confirm_consultancy_request",
        "appointment_declined_collect_note",
        "email_declined_collect_note",
        "collect_appointment_slot",
        "confirm_appointment_booking",
        "capture_closing_feedback",
        "close_conversation",
    }
    if decision in controller_only_decisions:
        steering["grounding_mode"] = "controller_only"
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
    Detect whether Nexy already offered a next action like demo request or appointment flow step.
    """

    text = (conversation_context or "").lower()

    # Current-methodology slot: Nexy asked what the visitor is currently using.
    # Must be checked before any other marker so the answer is routed correctly.
    if any(marker in text for marker in [
        "what are you currently using to generate leads",
        "what are you currently using for lead generation",
        "what are you using to generate leads",
        "currently using to get leads",
        "currently using for that challenge",
        "facebook ads, google ads, referrals, website enquiries, whatsapp, or something else",
        "facebook ads, google ads, referrals, website enquiries, or something else",
        "referrals, website enquiries, whatsapp, or something else",
    ]):
        return "collect_current_methodology"

    # Consultancy flow: ask more clarification or book
    if any(marker in text for marker in [
        "explain another nexy area",
        "another nexy area",
        "book a short demo",
        "book a short consultation",
        "another area or demo",
        "another area or consultation",
        "another area or would you prefer",
    ]):
        return "ask_more_clarification_or_consultancy"

    # Consultancy flow: email collection awaited (must check before generic email markers)
    if any(marker in text for marker in [
        "email verification is required before booking",
        "required before booking the meeting",
        "verify your email before booking",
        "verify it before booking",
        "verify it before we can book",
    ]):
        return "collect_email_for_consultancy"

    # Consultancy / appointment flow: email verification code awaited
    if any(marker in text for marker in [
        "enter the verification code",
        "verification code",
        "confirm your email",
        "code has been sent",
        "code was sent",
        "code sent to your email",
    ]):
        return "verify_email_for_consultancy"

    # Appointment flow: email collection awaited (legacy)
    if any(marker in text for marker in [
        "share your email address",
        "please share your email",
        "email address so it can be verified",
        "appointment booking requires email",
        "provide your email",
    ]):
        return "collect_email_for_appointment"

    # Appointment flow: slot collection awaited
    if any(marker in text for marker in [
        "preferred date and time",
        "suggest a date",
        "pick a time",
        "available slot",
        "appointment slot",
    ]):
        return "collect_appointment_slot"

    # Representative note collection awaited
    if any(marker in text for marker in [
        "leave a note",
        "leave a question",
        "note for the nexy representative",
        "note for our representative",
        "add a note or question for the nexy representative",
        "type 'skip'",
        "type skip",
    ]):
        return "collect_representative_note"

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

def _get_conversation_assigned_agent(conversation):
    """
    Resolve assigned agent from object first, then DB.
    Avoids stale/incomplete conversation doc issues.
    """
    try:
        agent_name = (getattr(conversation, "assigned_agent", None) or "").strip()
        if agent_name:
            return agent_name
    except Exception:
        pass

    try:
        return (
            frappe.db.get_value(
                "Nexus Live Conversation",
                conversation.name,
                "assigned_agent",
            )
            or ""
        ).strip()
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: failed to read assigned_agent from conversation",
        )
        return ""


def _safe_get_existing_field_value(doctype, docname, fieldnames):
    """
    Reads the first available field from a DocType safely.
    Works even if some candidate fields do not exist.
    """
    try:
        meta = frappe.get_meta(doctype)
        existing_fields = {df.fieldname for df in meta.fields}

        for fieldname in fieldnames:
            if fieldname not in existing_fields:
                continue

            value = ""
            if docname:
                value = frappe.db.get_value(doctype, docname, fieldname) or ""
            else:
                value = frappe.db.get_single_value(doctype, fieldname) or ""

            value = str(value or "").strip()
            if value:
                return value

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            f"Companion Controller: failed to read booking link from {doctype}",
        )

    return ""


def _resolve_meeting_booking_link(conversation):
    """
    Resolve the meeting booking link from:
    1. Assigned Nexus AI Agent Profile
    2. Nexus Settings
    3. Emergency configured fallback
    """

    agent_name = _get_conversation_assigned_agent(conversation)

    scheduling_link = ""

    if agent_name:
        scheduling_link = _safe_get_existing_field_value(
            "Nexus AI Agent Profile",
            agent_name,
            [
                "calendly_link",
                "calendly_url",
                "meeting_scheduling_link",
                "meeting_booking_link",
                "booking_link",
                "appointment_link",
            ],
        )

    if not scheduling_link:
        scheduling_link = _safe_get_existing_field_value(
            "Nexus Settings",
            None,
            [
                "meeting_scheduling_link",
                "calendly_link",
                "calendly_url",
                "meeting_booking_link",
                "booking_link",
                "appointment_link",
            ],
        )

    # Emergency fallback to stop the broken demo-request path.
    # Later you can remove this after confirming settings/agent lookup is stable.
    if not scheduling_link:
        scheduling_link = "https://calendly.com/rupesh-techxcel/nexus-ai-consultancy"

    return scheduling_link


def _build_meeting_booking_response(conversation, scheduling_link):
    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": (
            "Your email has been verified. You can now choose a suitable time to meet with "
            "a Nexy representative using the booking link below.\n\n"
            f"{scheduling_link}\n\n"
            "Thank you for your time — we look forward to speaking with you!\n\n"
            "If you would like to discuss another topic, please refresh this page to start a new chat."
        ),
        "confidence": 1.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": {
            "type": "meeting_booking",
            "status": "ready",
            "title": "Book a Demo / Consultation",
            "button_label": "Book a Meeting",
            "description": "Choose a suitable time with a Nexy representative.",
            "booking_url": scheduling_link,
            "url": scheduling_link,
        },
        "booking_url": scheduling_link,
    }


def _handle_show_meeting_booking_card(conversation, accumulated_discovery=None):
    """
    Fires after email verified + representative note captured/skipped.

    Important:
    This function must NEVER fall back to legacy demo request wording for Nexy Companion.
    It must either show a booking link/card or clearly expose a booking-link configuration issue.
    """

    scheduling_link = _resolve_meeting_booking_link(conversation)

    _companion_flow_debug("09 BOOKING LINK CHECK", {
        "conversation": getattr(conversation, "name", None),
        "assigned_agent": _get_conversation_assigned_agent(conversation),
        "scheduling_link_found": bool(scheduling_link),
        "scheduling_link_preview": scheduling_link[:120] if scheduling_link else "",
    })

    return _build_meeting_booking_response(conversation, scheduling_link)

def _handle_create_consultancy_request(conversation, accumulated_discovery=None):
    """
    No scheduling link available — create a consultancy request record and notify the visitor.
    """
    try:
        enquiry_name = getattr(conversation, "companion_enquiry", None)
        if enquiry_name:
            frappe.db.set_value(
                "Nexus Companion Enquiry",
                enquiry_name,
                "recommended_next_step",
                "consultancy_request",
                update_modified=False,
            )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Controller: consultancy request update failed",
        )

    return {
        "status": "success",
        "access_status": "intent_handled",
        "answer": (
            "Thanks. I've saved your request for a Nexy representative. "
            "They can review your note and follow up using your verified email."
        ),
        "confidence": 1.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 0,
        "chat_mode": "controlled_companion_direct",
        "companion_controller": True,
        "conversion_action": {
            "type": "consultancy_request",
            "status": "created",
            "title": "Consultancy request saved",
            "message": "A Nexy representative will follow up using the visitor's verified email.",
        },
    }


def _handle_demo_confirmation(conversation):
    """
    Demo accepted. Do not ask again.
    """
    
    # Final safety: Nexy Companion must not use the legacy demo confirmation path.
    if _is_nexy_companion_conversation(conversation):
        if _is_booking_email_verified(conversation):
            _clear_companion_pending_action(conversation)
            return _handle_show_meeting_booking_card(conversation, {})

        response = {
            "status": "success",
            "access_status": "intent_handled",
            "answer": (
                "Sure. Please share your email address so I can verify it before booking the meeting."
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
        return _decorate_email_collection_response(response, conversation)

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