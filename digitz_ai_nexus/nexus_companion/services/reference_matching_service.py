"""
Reference matching service — retrieves relevant customer stories, testimonials,
and outcomes for a visitor based on their discovery profile and matched persona.

Only returns approved, publicly-visible records.
"""

import frappe


def get_relevant_references(
    discovery_data: dict,
    matched_persona: str | None,
    tenant: str,
    limit: int = 3,
) -> list:
    """
    Returns a ranked list of reference snippets suitable for Nexy to use in conversation.

    Each item: {"type": str, "title": str, "summary": str, "industry": str}
    """
    results = []
    industry = _extract_industry(discovery_data)

    # Stories
    stories = _get_stories(tenant, industry, matched_persona, limit)
    results.extend(stories)

    # Testimonials (fill remaining slots)
    remaining = limit - len(results)
    if remaining > 0:
        testimonials = _get_testimonials(tenant, remaining)
        results.extend(testimonials)

    # Outcomes (always append a couple for social proof)
    outcomes = _get_outcomes(tenant, matched_persona, 2)
    results.extend(outcomes)

    return results[:limit + 2]  # allow a slightly larger pool for the prompt


def _get_stories(tenant, industry, matched_persona, limit):
    filters = {"tenant": tenant, "approved": 1, "visibility": "Public"}
    if industry:
        filters["industry"] = ["like", f"%{industry}%"]

    stories = frappe.get_all(
        "Nexus Companion Story",
        filters=filters,
        fields=["title", "industry", "summary", "challenge", "outcomes"],
        order_by="modified desc",
        limit_page_length=limit,
    )

    results = []
    for s in stories:
        summary = s.get("summary") or ""
        if not summary and s.get("outcomes"):
            summary = (s.get("outcomes") or "")[:200]
        results.append({
            "type": "story",
            "title": s.title,
            "industry": s.industry or "",
            "summary": summary,
        })
    return results


def _get_testimonials(tenant, limit):
    testimonials = frappe.get_all(
        "Nexus Companion Testimonial",
        filters={"tenant": tenant, "approved": 1},
        fields=["customer_name", "company_name", "testimonial", "rating"],
        order_by="rating desc",
        limit_page_length=limit,
    )
    results = []
    for t in testimonials:
        name = t.customer_name or "A customer"
        company = f" from {t.company_name}" if t.company_name else ""
        results.append({
            "type": "testimonial",
            "title": f"Testimonial — {name}{company}",
            "industry": "",
            "summary": (t.testimonial or "")[:200],
        })
    return results


def _get_outcomes(tenant, matched_persona, limit):
    filters = {"tenant": tenant, "approved": 1}
    outcomes = frappe.get_all(
        "Nexus Companion Outcome",
        filters=filters,
        fields=["outcome_label", "outcome_category", "detail"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    return [
        {
            "type": "outcome",
            "title": o.outcome_label,
            "industry": o.outcome_category or "",
            "summary": o.detail or "",
        }
        for o in outcomes
    ]


def _extract_industry(discovery_data: dict) -> str:
    for key in ("industry", "sector", "business_type", "company_type"):
        val = discovery_data.get(key)
        if val and isinstance(val, str):
            return val.strip()
    return ""
