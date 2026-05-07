# Copyright (c) 2026, DIGITZ
# For license information, please see license.txt


def safe_float(value, default=0.0):
    try:
        return float(value or default)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(value or default)
    except Exception:
        return default


def build_candidate_debug_row(candidate):
    """
    Builds one explainable retrieval debug row for Testing Lab.
    """

    return {
        "chunk": candidate.get("chunk"),
        "knowledge_unit": candidate.get("knowledge_unit"),
        "business_unit": candidate.get("business_unit"),
        "project": candidate.get("project"),
        "topic": candidate.get("topic"),
        "entity_type": candidate.get("entity_type"),
        "entity": candidate.get("entity"),

        "vector_score": safe_float(candidate.get("vector_score")),
        "keyword_score": safe_float(candidate.get("keyword_score")),
        "business_keyword_boost": safe_float(candidate.get("business_keyword_boost")),
        "project_boost": safe_float(candidate.get("project_boost")),
        "hybrid_score": safe_float(candidate.get("hybrid_score")),
        "rerank_bonus": safe_float(candidate.get("rerank_bonus")),
        "rerank_score": safe_float(candidate.get("rerank_score")),
        "final_score": safe_float(candidate.get("final_score")),

        "rank_before_rerank": safe_int(candidate.get("rank_before_rerank")),
        "rank_after_rerank": safe_int(candidate.get("rank_after_rerank")),

        "matched_queries": candidate.get("matched_queries") or [],
        "rerank_reasons": candidate.get("rerank_reasons") or [],
        "selected": 1 if candidate.get("selected") else 0,
        "debug_reason": candidate.get("debug_reason") or "",
        # Retrieval stability visibility
        "retrieval_stability_score": safe_float(candidate.get("retrieval_stability_score")),
        "stable_final_score": safe_float(candidate.get("stable_final_score")),
        "stable_vector_score": safe_float(candidate.get("stable_vector_score")),
        "stable_keyword_score": safe_float(candidate.get("stable_keyword_score")),
        "stable_priority_score": safe_float(candidate.get("stable_priority_score")),
        "stable_project_score": safe_float(candidate.get("stable_project_score")),
        "stable_rerank_score": safe_float(candidate.get("stable_rerank_score")),
    }


def build_retrieval_debug_payload(candidates):
    """
    Builds complete debug rows for ranked/re-ranked candidates.
    """

    if not candidates:
        return []

    return [build_candidate_debug_row(candidate) for candidate in candidates]


def build_denied_debug_row(row, reason=None):
    """
    Builds denied chunk debug info.
    """

    return {
        "chunk": getattr(row, "name", None),
        "knowledge_unit": getattr(row, "knowledge_unit", None),
        "business_unit": getattr(row, "business_unit", None),
        "project": getattr(row, "project", None),
        "access_policy": getattr(row, "access_policy", None),
        "denied_reason": reason or "Access denied",
    }


def build_denied_payload(denied_rows):
    """
    denied_rows expected format:
    [
        {"row": row, "reason": "..."}
    ]
    """

    if not denied_rows:
        return []

    result = []

    for item in denied_rows:
        row = item.get("row")
        reason = item.get("reason")
        result.append(build_denied_debug_row(row, reason))

    return result