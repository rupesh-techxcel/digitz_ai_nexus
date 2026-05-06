# Copyright (c) 2026, DIGITZ
# For license information, please see license.txt

import re


def normalize_text(value):
    return (value or "").strip().lower()


def tokenize(text):
    text = normalize_text(text)
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text) if len(t) > 2]


def safe_float(value, default=0.0):
    try:
        return float(value or default)
    except Exception:
        return default


def compute_exact_phrase_bonus(query, chunk_text):
    query_l = normalize_text(query)
    text_l = normalize_text(chunk_text)

    if not query_l or not text_l:
        return 0.0, None

    if query_l in text_l:
        return 0.15, "Exact query phrase matched"

    return 0.0, None


def compute_token_overlap_bonus(query, chunk_text):
    query_terms = tokenize(query)
    text_l = normalize_text(chunk_text)

    if not query_terms or not text_l:
        return 0.0, None

    matched = [term for term in query_terms if term in text_l]

    if not matched:
        return 0.0, None

    ratio = len(matched) / len(query_terms)

    if ratio >= 0.80:
        return 0.08, "Strong query term overlap"

    if ratio >= 0.50:
        return 0.04, "Moderate query term overlap"

    return 0.0, None


def compute_project_match_bonus(candidate, requested_project=None):
    if not requested_project:
        return 0.0, None

    candidate_project = normalize_text(candidate.get("project"))
    requested_project = normalize_text(requested_project)

    if candidate_project and candidate_project == requested_project:
        return 0.10, "Requested project matched"

    return 0.0, None


def compute_entity_topic_bonus(query, candidate):
    query_l = normalize_text(query)

    topic = normalize_text(candidate.get("topic"))
    entity = normalize_text(candidate.get("entity"))
    entity_type = normalize_text(candidate.get("entity_type"))

    bonus = 0.0
    reasons = []

    if topic and topic in query_l:
        bonus += 0.05
        reasons.append("Topic matched query")

    if entity and entity in query_l:
        bonus += 0.05
        reasons.append("Entity matched query")

    if entity_type and entity_type in query_l:
        bonus += 0.03
        reasons.append("Entity type matched query")

    return bonus, reasons


def compute_chunk_length_bonus(chunk_text):
    """
    Prefer reasonably focused chunks.
    Avoid giving bonus to extremely long chunks.
    """

    length = len(chunk_text or "")

    if 150 <= length <= 1500:
        return 0.03, "Chunk length suitable"

    if length > 3000:
        return -0.03, "Chunk too long"

    return 0.0, None


def rerank_candidates(query, candidates, requested_project=None, limit=None):
    """
    Re-ranks hybrid-scored candidates using deterministic business rules.

    Input:
        candidates: list of dict candidates with hybrid_score

    Output:
        candidates sorted by final_score desc
    """

    if not candidates:
        return []

    pool = candidates[:limit] if limit else candidates

    reranked = []

    for index, candidate in enumerate(pool, start=1):
        candidate = dict(candidate)
        candidate["rank_before_rerank"] = index

        base_score = safe_float(candidate.get("hybrid_score"))
        chunk_text = candidate.get("text") or ""

        bonus = 0.0
        reasons = []

        exact_bonus, exact_reason = compute_exact_phrase_bonus(query, chunk_text)
        if exact_reason:
            bonus += exact_bonus
            reasons.append(exact_reason)

        overlap_bonus, overlap_reason = compute_token_overlap_bonus(query, chunk_text)
        if overlap_reason:
            bonus += overlap_bonus
            reasons.append(overlap_reason)

        project_bonus, project_reason = compute_project_match_bonus(candidate, requested_project)
        if project_reason:
            bonus += project_bonus
            reasons.append(project_reason)

        entity_topic_bonus, entity_topic_reasons = compute_entity_topic_bonus(query, candidate)
        if entity_topic_reasons:
            bonus += entity_topic_bonus
            reasons.extend(entity_topic_reasons)

        length_bonus, length_reason = compute_chunk_length_bonus(chunk_text)
        if length_reason:
            bonus += length_bonus
            reasons.append(length_reason)

        if safe_float(candidate.get("business_keyword_boost")) > 0:
            bonus += 0.05
            reasons.append("Business keyword matched")

        final_score = base_score + bonus

        if final_score < 0:
            final_score = 0.0

        if final_score > 1:
            final_score = 1.0

        candidate["rerank_bonus"] = round(bonus, 6)
        candidate["rerank_score"] = round(final_score, 6)
        candidate["final_score"] = round(final_score, 6)
        candidate["rerank_reasons"] = reasons

        reranked.append(candidate)

    reranked = sorted(
        reranked,
        key=lambda x: (
            safe_float(x.get("final_score")),
            safe_float(x.get("hybrid_score")),
            safe_float(x.get("keyword_score")),
            safe_float(x.get("vector_score")),
        ),
        reverse=True,
    )

    for index, candidate in enumerate(reranked, start=1):
        candidate["rank_after_rerank"] = index

    return reranked