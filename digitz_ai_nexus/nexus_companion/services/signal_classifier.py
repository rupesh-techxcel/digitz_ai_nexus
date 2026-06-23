"""
LLM-powered buying signal classifier for Nexus Companion conversations.

Every visitor message is classified into a signal type that directly drives
the companion journey stage machine. No keyword matching — full LLM judgment.
"""

import json
import frappe

from digitz_ai_nexus.engine.llm import generate_answer


# ── Signal taxonomy ────────────────────────────────────────────────────────────

SIGNAL_TYPES = frozenset({
    # Discovery signals
    "SHARING_CONTEXT",       # Describing their situation / background
    "ANSWERING_QUESTION",    # Responding to a Nexy question
    # Interest signals
    "CURIOUS",               # Exploring, asking general questions
    "EVALUATING",            # Comparing, asking deeper questions
    "INTERESTED",            # Positive engagement, expressing genuine fit
    "READY",                 # Explicit intent to proceed (buy, subscribe, book)
    # Conversion signals
    "ASKING_PRICE",          # Asking about cost, pricing, plans
    "ASKING_NEXT_STEP",      # "How do I get started?", "what's the next step?"
    # Resistance signals
    "OBJECTING",             # Raising a concern (price, timing, need, trust)
    "HESITATING",            # Non-committal, vague, slowing down
    "DISENGAGING",           # Short/dismissive replies, losing interest
    "DEFLECTING",            # Changing subject, avoiding the question
    # Cycle-ending signals
    "REQUESTING_HUMAN",      # Wants to speak with a person
    "DECLINING",             # Explicitly not interested, wants to exit
})

_PROMPT = """\
Classify the visitor's message in the context of a business enquiry conversation.

Conversation so far:
{context}

Visitor's message: "{message}"

Signal type definitions:
SHARING_CONTEXT    — Describing their situation or business background
ANSWERING_QUESTION — Responding to a question the advisor asked
CURIOUS            — Exploring, asking general questions
EVALUATING         — Comparing options, asking deeper questions
INTERESTED         — Expressing genuine interest or positive engagement
READY              — Clear intent to proceed (buy, subscribe, book, start)
ASKING_PRICE       — Asking about cost, pricing, or plans
ASKING_NEXT_STEP   — Asking how to proceed ("what's next?", "how do I get started?")
OBJECTING          — Raising a concern about price, timing, need, or trust
HESITATING         — Non-committal, vague, or slowing down
DISENGAGING        — Short or dismissive replies, losing interest
DEFLECTING         — Changing subject or avoiding
REQUESTING_HUMAN   — Wants to speak with a real person
DECLINING          — Explicitly not interested, wants to end the conversation

Respond with only a JSON object — no explanation, no markdown, no code fences:
{{"signal": "SIGNAL_TYPE", "confidence": 0.85, "reason": "one short sentence"}}"""


def classify_signal(message: str, conversation_context: str = "") -> dict:
    """
    Classify one visitor message as a buying signal.

    Returns:
        {signal_type: str, confidence: float, reason: str}

    Falls back gracefully to CURIOUS on any failure — never throws.
    """
    if not (message or "").strip():
        return {"signal_type": "SHARING_CONTEXT", "confidence": 0.5, "reason": "Empty message"}

    prompt = _PROMPT.format(
        context=(conversation_context or "No prior context")[:600],
        message=(message or "")[:400],
    )

    try:
        raw = (generate_answer(prompt) or "").strip()

        # Strip any markdown fences the LLM may add
        if raw.startswith("```"):
            raw = raw.strip("`").lstrip("json").strip()

        parsed = json.loads(raw)
        signal = str(parsed.get("signal") or "CURIOUS").upper()

        if signal not in SIGNAL_TYPES:
            signal = "CURIOUS"

        return {
            "signal_type": signal,
            "confidence": float(parsed.get("confidence") or 0.7),
            "reason": str(parsed.get("reason") or ""),
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Nexus Companion: Signal classification failed")
        return {"signal_type": "CURIOUS", "confidence": 0.5, "reason": "Classification failed — default"}


def is_conversion_signal(signal_type: str) -> bool:
    """True when the signal indicates conversion readiness."""
    return signal_type in ("READY", "ASKING_PRICE", "ASKING_NEXT_STEP")


def is_resistance_signal(signal_type: str) -> bool:
    """True when the signal indicates resistance."""
    return signal_type in ("OBJECTING", "HESITATING", "DISENGAGING", "DEFLECTING")


def is_exit_signal(signal_type: str) -> bool:
    """True when the signal indicates the visitor wants to exit."""
    return signal_type in ("REQUESTING_HUMAN", "DECLINING")
