import json
import frappe

from digitz_ai_nexus.engine.llm import generate_answer


_ALLOWED_INTENTS = {
    "business_context_answer",
    "business_scale_question",
    "pain_context_answer",
    "pricing_question",
    "demo_interest",
    "demo_confirmation",
    "demo_rejection",
    "next_step_question",
    "human_request",
    "product_question",
    "technical_how_it_works_question",
    "off_topic",
    "greeting",
    "solution_fit_question",
    "solution_method_question",
    "unknown",
}


def classify_external_intent(
    visitor_message,
    current_milestone=None,
    conversation_context=None,
    pending_action=None,
):
    """
    Classify the visitor's external intent for controller steering.

    Returns:
    {
        "intent": "...",
        "confidence": 0.0-1.0,
        "reason": "..."
    }
    """

    message = (visitor_message or "").strip()

    if not message:
        return {
            "intent": "unknown",
            "confidence": 0,
            "reason": "empty message",
        }

    # ------------------------------------------------------------
    # Fast controller-owned rules before LLM classification
    # ------------------------------------------------------------
    text = message.lower()
    context = (conversation_context or "").lower()
    pending_action = (pending_action or "").strip()

    positive_confirmations = {
        "yes",
        "yeah",
        "yep",
        "ok",
        "okay",
        "ok good",
        "sure",
        "please",
        "go ahead",
        "proceed",
        "interested",
        "i am interested",
        "that would be interesting",
        "that would be interested",
    }

    negative_confirmations = {
        "no",
        "not now",
        "later",
        "no thanks",
        "not interested",
    }

    if pending_action == "demo_request" and text in positive_confirmations:
        return {
            "intent": "demo_confirmation",
            "confidence": 0.95,
            "reason": "positive confirmation for pending demo request",
        }

    if pending_action == "demo_request" and text in negative_confirmations:
        return {
            "intent": "demo_rejection",
            "confidence": 0.95,
            "reason": "negative confirmation for pending demo request",
        }

    if (
        text in positive_confirmations
        and (
            "submit a demo request" in context
            or "arrange the demo" in context
            or "arrange a demo" in context
            or "would you like to proceed" in context
            or "nexus consultant will contact" in context
        )
    ):
        return {
            "intent": "demo_confirmation",
            "confidence": 0.9,
            "reason": "positive confirmation after demo offer",
        }

    if any(
        k in text
        for k in [
            "next step",
            "what next",
            "how to proceed",
            "what do you propose",
            "what is the next step",
        ]
    ):
        return {
            "intent": "next_step_question",
            "confidence": 0.9,
            "reason": "visitor asked for next step",
        }

    if any(
        k in text
        for k in [
            "how exactly you do",
            "how exactly do you",
            "how do you do",
            "how you do",
            "how exactly",
            "explain how",
            "customer profiling",
            "lead capture optimization",
            "lead capture",
            "capture optimization",
        ]
    ) and any(
        k in text or k in context
        for k in [
            "customer profiling",
            "lead capture",
            "lead generation",
            "facebook ads",
            "target audience",
            "qualification",
            "follow-up",
            "tracking",
        ]
    ):
        return {
            "intent": "solution_method_question",
            "confidence": 0.95,
            "reason": "visitor asked how the previously suggested solution approach would be done",
        }
    if any(
        k in text
        for k in [
            "how exactly",
            "how does",
            "how it works",
            "workflow",
            "knowledge based",
            "knowledge-based",
            "whatsapp outreach",
            "integration",
        ]
    ):
        return {
            "intent": "technical_how_it_works_question",
            "confidence": 0.85,
            "reason": "technical workflow question",
        }

    if any(
        k in text
        for k in [
            "representative",
            "human",
            "person",
            "consultant",
            "team member",
            "connect me",
            "talk to someone",
            "speak to someone",
        ]
    ):
        return {
            "intent": "human_request",
            "confidence": 0.9,
            "reason": "visitor asked for human/representative",
        }

    if any(k in text for k in ["demo", "walkthrough", "meeting", "call", "presentation"]):
        return {
            "intent": "demo_interest",
            "confidence": 0.85,
            "reason": "demo interest keyword",
        }

    if any(
        k in text
        for k in [
            "price",
            "pricing",
            "cost",
            "charge",
            "charges",
            "quote",
            "quotation",
            "fee",
            "subscription",
        ]
    ):
        return {
            "intent": "pricing_question",
            "confidence": 0.85,
            "reason": "pricing keyword",
        }

    if "how much" in text and any(
        k in text for k in ["run", "daily", "per day", "basis", "volume"]
    ):
        return {
            "intent": "business_scale_question",
            "confidence": 0.8,
            "reason": "business scale phrasing",
        }
        
    if any(
        k in text
        for k in [
            "challenges with",
            "challenge with",
            "struggling with",
            "struggle with",
            "issues with",
            "issue with",
            "problem with",
            "problems with",
            "difficulty with",
            "difficulties with",
            "pain point",
            "facing challenges",
            "facing issues",
            "facing problem",
            "have trouble with",
            "trouble with",
        ]
    ):
        return {
            "intent": "pain_context_answer",
            "confidence": 0.9,
            "reason": "visitor sharing a specific business challenge or pain point",
        }

    if any(
        k in text
        for k in [
            "how can you help",
            "how you can help",
            "how nexus can help",
            "how nexy can help",
            "can you guide me",
            "guide me how",
            "help me in lead generation",
            "help me with lead generation",
            "help me in targeting",
            "targeting the right audience",
            "right audience",
            "are you suggesting",
            "new methodology",
            "new methodologies",
            "what methodology",
            "what approach",
            "how will this help",
        ]
    ):
        return {
            "intent": "solution_fit_question",
            "confidence": 0.95,
            "reason": "visitor asked how Nexus/Nexy can help with their business problem",
        }

    # ------------------------------------------------------------
    # LLM classification fallback
    # ------------------------------------------------------------
    prompt = f"""
Classify the visitor message for a business companion controller.

Current milestone:
{current_milestone or ""}

Pending action:
{pending_action or ""}

Conversation context:
{conversation_context or ""}

Visitor message:
{message}

Choose exactly one intent:

- business_context_answer
  The visitor is answering about their business, company, industry, work, services, current situation, or goal — without stating a specific pain or challenge.

- pain_context_answer
  The visitor is sharing a specific challenge, pain point, problem, or difficulty they are currently facing in their business operations (e.g. "we have challenges with lead generation", "struggling with customer retention").

- business_scale_question
  The visitor is asking about scale, volume, size, daily operations, how many customers/jobs/users/transactions/businesses are handled, or asking "how much do you run" in an operational sense.

- pricing_question
  The visitor is asking about price, pricing, cost, charges, quotation, subscription fee, payment, package rate, or budget.

- demo_interest
  The visitor wants a demo, meeting, presentation, call, consultation, walkthrough, or appointment.

- demo_confirmation
  The visitor confirms a previously offered demo/request/next step.
  Examples: yes, ok good, sure, proceed, go ahead, interested.
  Use this especially when pending_action is demo_request.

- demo_rejection
  The visitor declines a previously offered demo/request/next step.

- next_step_question
  The visitor asks what to do next, what you propose, or how to proceed.

- human_request
  The visitor wants to talk to a human, representative, agent, consultant, support person, or team member.

- product_question
  The visitor asks about product/service features, modules, capabilities, integrations, implementation, support, security, or platform details.

- solution_method_question
  The visitor asks how exactly Nexus/Nexy would perform or support a previously mentioned solution area, such as customer profiling, lead capture, qualification, follow-up, tracking, or lead generation improvement.

- technical_how_it_works_question
  The visitor asks how a workflow technically works, such as WhatsApp outreach, knowledge-based chat, routing, automation, integration, data flow, or implementation method.

- off_topic
  The visitor message is unrelated to the business conversation.

- greeting
  The visitor is only greeting.

- unknown
  Use only if unclear.

Important distinctions:
- "How much you run on a daily basis?" usually means business scale or operational volume, NOT pricing, unless the visitor clearly mentions price/cost/charges.
- "yes" after a demo offer means demo_confirmation.
- "What is the next step you propose?" means next_step_question.
- "How exactly WhatsApp outreach working? Is it a knowledge based chat?" means technical_how_it_works_question.

Return ONLY valid JSON:
{{
  "intent": "one of the intents above",
  "confidence": 0.0,
  "reason": "short reason"
}}
"""

    try:
        raw = (generate_answer(prompt) or "").strip()

        if raw.startswith("```"):
            raw = raw.strip("`").replace("json", "", 1).strip()

        data = json.loads(raw)

        intent = (data.get("intent") or "unknown").strip()

        if intent not in _ALLOWED_INTENTS:
            intent = "unknown"

        try:
            confidence = float(data.get("confidence") or 0)
        except Exception:
            confidence = 0

        confidence = max(0, min(confidence, 1))

        return {
            "intent": intent,
            "confidence": confidence,
            "reason": data.get("reason") or "",
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Companion Intent: classify_external_intent failed",
        )

        return {
            "intent": "unknown",
            "confidence": 0,
            "reason": "classification failed",
        }