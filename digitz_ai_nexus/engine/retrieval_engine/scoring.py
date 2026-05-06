# Copyright (c) 2026, DIGITZ
# For license information, please see license.txt

import json
import math
import re

import frappe


def safe_float(value, default=0.0):
    try:
        return float(value or default)
    except Exception:
        return default


def normalize_text(value):
    return (value or "").strip().lower()


def tokenize(text):
    text = normalize_text(text)
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text) if len(t) > 2]


def parse_embedding(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        return []

    return []


def compute_vector_score(query_embedding, chunk_embedding):
    """
    Calculates cosine similarity between query embedding and chunk embedding.
    Returns score between 0 and 1.
    """

    query_vector = parse_embedding(query_embedding)
    chunk_vector = parse_embedding(chunk_embedding)

    if not query_vector or not chunk_vector:
        return 0.0

    if len(query_vector) != len(chunk_vector):
        return 0.0

    dot = sum(float(a) * float(b) for a, b in zip(query_vector, chunk_vector))
    query_norm = math.sqrt(sum(float(a) * float(a) for a in query_vector))
    chunk_norm = math.sqrt(sum(float(b) * float(b) for b in chunk_vector))

    if not query_norm or not chunk_norm:
        return 0.0

    score = dot / (query_norm * chunk_norm)

    if score < 0:
        score = 0.0

    return round(min(score, 1.0), 6)


def compute_keyword_score(query, chunk_text, metadata=None):
    """
    Basic keyword score based on query terms, exact phrase match, and metadata match.
    This works even when Nexus Business Keyword seed data is not available.
    """

    query_l = normalize_text(query)
    text_l = normalize_text(chunk_text)

    if not query_l or not text_l:
        return 0.0

    score = 0.0

    if query_l in text_l:
        score += 0.40

    query_terms = tokenize(query_l)

    if query_terms:
        matched_terms = [term for term in query_terms if term in text_l]
        score += (len(matched_terms) / len(query_terms)) * 0.40

    if metadata and query_terms:
        meta_text = normalize_text(
            " ".join(
                [
                    str(metadata.get("topic") or ""),
                    str(metadata.get("entity") or ""),
                    str(metadata.get("entity_type") or ""),
                    str(metadata.get("business_unit") or ""),
                    str(metadata.get("project") or ""),
                ]
            )
        )

        if meta_text:
            meta_matches = [term for term in query_terms if term in meta_text]
            score += (len(meta_matches) / len(query_terms)) * 0.20

    return round(min(score, 1.0), 6)


def get_enabled_business_keywords():
    """
    Reads configured high-priority business keywords.
    Safe when DocType exists but no seed records are available.
    """

    if not frappe.db.exists("DocType", "Nexus Business Keyword"):
        return []

    rows = frappe.get_all(
        "Nexus Business Keyword",
        filters={"enabled": 1},
        fields=[
            "name",
            "keyword",
            "category",
            "boost_weight",
            "priority_level",
            "synonyms",
        ],
        limit_page_length=500,
    )

    return rows or []


def get_category_weight(category):
    """
    Reads category weight from Nexus Keyword Category.
    Safe fallback = 1.0.
    """

    if not category:
        return 1.0

    if not frappe.db.exists("DocType", "Nexus Keyword Category"):
        return 1.0

    weight = frappe.db.get_value("Nexus Keyword Category", category, "weight")

    return safe_float(weight, 1.0)


def compute_business_keyword_boost(query, chunk_text):
    """
    Boosts chunks when configured business keywords match both:
    - user query
    - documentation chunk

    If no keyword seed exists, returns 0.0 safely.
    """

    query_l = normalize_text(query)
    text_l = normalize_text(chunk_text)

    if not query_l or not text_l:
        return 0.0

    boost = 0.0
    keywords = get_enabled_business_keywords()

    for row in keywords:
        terms = []

        if row.get("keyword"):
            terms.append(row.get("keyword"))

        synonyms = row.get("synonyms") or ""
        for line in synonyms.splitlines():
            if line.strip():
                terms.append(line.strip())

        matched = False

        for term in terms:
            term_l = normalize_text(term)

            if term_l and term_l in query_l and term_l in text_l:
                matched = True
                break

        if not matched:
            continue

        keyword_weight = safe_float(row.get("boost_weight"), 0.20)
        category_weight = get_category_weight(row.get("category"))

        boost += keyword_weight * category_weight

    return round(min(boost, 1.0), 6)


def compute_project_boost(chunk_project, requested_project, project_scope=None):
    """
    Project boost is only a ranking signal.
    It must never override access control or project scope filtering.
    """

    chunk_project = normalize_text(chunk_project)
    requested_project = normalize_text(requested_project)
    project_scope = normalize_text(project_scope)

    if not requested_project:
        return 0.0

    if chunk_project == requested_project:
        return 1.0

    if project_scope in ("fallback", "project_with_general_fallback", "project + general fallback"):
        if not chunk_project:
            return 0.30

    return 0.0


def get_retrieval_weights():
    """
    Reads scoring weights from Nexus Settings.
    Uses safe defaults if fields are missing.
    """

    settings = frappe.get_single("Nexus Settings")

    return {
        "vector_weight": safe_float(getattr(settings, "vector_weight", None), 0.50),
        "keyword_weight": safe_float(getattr(settings, "keyword_weight", None), 0.25),
        "business_term_weight": safe_float(getattr(settings, "business_term_weight", None), 0.15),
        "project_boost_weight": safe_float(getattr(settings, "project_boost_weight", None), 0.10),
    }


def compute_hybrid_score(
    vector_score,
    keyword_score,
    business_keyword_boost,
    project_boost,
    weights=None,
):
    """
    Final hybrid score used for initial ranking.
    """

    weights = weights or get_retrieval_weights()

    score = (
        safe_float(vector_score) * safe_float(weights.get("vector_weight"), 0.50)
        + safe_float(keyword_score) * safe_float(weights.get("keyword_weight"), 0.25)
        + safe_float(business_keyword_boost) * safe_float(weights.get("business_term_weight"), 0.15)
        + safe_float(project_boost) * safe_float(weights.get("project_boost_weight"), 0.10)
    )

    return round(min(score, 1.0), 6)


def build_scored_candidate(
    row,
    query,
    query_embedding,
    requested_project=None,
    project_scope=None,
    weights=None,
):
    """
    Converts a Knowledge Chunk row into a scored retrieval candidate.
    """

    chunk_text = (
        getattr(row, "chunk_text", None)
        or getattr(row, "content", None)
        or getattr(row, "text", None)
        or ""
    )

    chunk_embedding = getattr(row, "embedding", None)

    candidate = {
        "chunk": getattr(row, "name", None),
        "knowledge_unit": getattr(row, "knowledge_unit", None),
        "business_unit": getattr(row, "business_unit", None),
        "project": getattr(row, "project", None),
        "topic": getattr(row, "topic", None),
        "entity_type": getattr(row, "entity_type", None),
        "entity": getattr(row, "entity", None),
        "access_policy": getattr(row, "access_policy", None),
        "text": chunk_text,
        "matched_queries": [query],
    }

    candidate["vector_score"] = compute_vector_score(query_embedding, chunk_embedding)
    candidate["keyword_score"] = compute_keyword_score(query, chunk_text, candidate)
    candidate["business_keyword_boost"] = compute_business_keyword_boost(query, chunk_text)
    candidate["project_boost"] = compute_project_boost(
        candidate.get("project"),
        requested_project,
        project_scope,
    )

    candidate["hybrid_score"] = compute_hybrid_score(
        candidate["vector_score"],
        candidate["keyword_score"],
        candidate["business_keyword_boost"],
        candidate["project_boost"],
        weights=weights,
    )

    candidate["final_score"] = candidate["hybrid_score"]

    return candidate