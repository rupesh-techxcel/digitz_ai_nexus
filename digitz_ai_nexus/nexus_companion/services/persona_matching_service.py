"""
Persona matching service — scores visitor discovery data against configured personas.

Uses keyword/pattern matching weighted across key persona fields. No ML required;
the LLM in the prompt handles nuanced understanding; this service produces a
structured confidence score for stage tracking and escalation decisions.
"""

import re
import frappe


_FIELD_WEIGHTS = {
    "industry": 30,
    "company_size": 20,
    "business_maturity": 10,
    "challenges": 20,
    "pain_points": 15,
    "goals": 5,
}


def match_persona(discovery_data: dict, tenant: str) -> dict:
    """
    Score discovery_data against all enabled personas for the tenant.

    Returns:
        {
            "persona": str | None,
            "persona_name": str | None,
            "confidence": float,   # 0-100
            "score_breakdown": dict
        }
    """
    if not discovery_data or not tenant:
        return _no_match()

    personas = frappe.get_all(
        "Nexus Companion Persona",
        filters={"tenant": tenant, "enabled": 1},
        fields=[
            "name", "persona_name", "industry", "customer_type",
            "company_size", "business_maturity", "challenges",
            "pain_points", "goals", "desired_outcomes",
        ],
        limit_page_length=50,
    )

    if not personas:
        return _no_match()

    best_persona = None
    best_score = 0.0
    best_breakdown = {}

    for persona in personas:
        score, breakdown = _score_persona(persona, discovery_data)
        if score > best_score:
            best_score = score
            best_persona = persona
            best_breakdown = breakdown

    if best_persona and best_score >= 20:
        return {
            "persona": best_persona.name,
            "persona_name": best_persona.persona_name,
            "confidence": round(min(best_score, 100.0), 1),
            "score_breakdown": best_breakdown,
        }

    return _no_match()


def _score_persona(persona, discovery_data: dict) -> tuple:
    """Score a single persona against discovery_data. Returns (score, breakdown)."""
    total_weight = sum(_FIELD_WEIGHTS.values())
    earned = 0
    breakdown = {}

    visitor_text = _flatten_discovery(discovery_data).lower()

    for field, weight in _FIELD_WEIGHTS.items():
        persona_value = (persona.get(field) or "").lower().strip()
        if not persona_value:
            continue

        # Tokenise persona field into meaningful keywords (3+ chars, skip stopwords)
        keywords = _extract_keywords(persona_value)
        if not keywords:
            continue

        matched = sum(1 for kw in keywords if kw in visitor_text)
        field_score = (matched / len(keywords)) * weight if keywords else 0
        earned += field_score
        breakdown[field] = round(field_score, 1)

    normalised = (earned / total_weight) * 100 if total_weight else 0
    return normalised, breakdown


def _flatten_discovery(discovery_data: dict) -> str:
    """Flatten all discovery values into a single searchable string."""
    parts = []
    for v in discovery_data.values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts.extend(str(i) for i in v)
    return " ".join(parts)


_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "are", "our",
    "we", "to", "of", "in", "a", "an", "is", "it", "or", "on",
}


def _extract_keywords(text: str) -> list:
    """Extract meaningful lowercase tokens from a text field."""
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def _no_match() -> dict:
    return {
        "persona": None,
        "persona_name": None,
        "confidence": 0.0,
        "score_breakdown": {},
    }
