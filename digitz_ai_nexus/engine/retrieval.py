import json
import math
import re

import frappe

from digitz_ai_nexus.engine.embedding import generate_embedding
from digitz_ai_nexus.engine.access import can_access_chunk

from digitz_ai_nexus.engine.retrieval_engine.query_expansion import expand_query
from digitz_ai_nexus.engine.retrieval_engine.scoring import (
    build_scored_candidate,
    get_retrieval_weights,
)
from digitz_ai_nexus.engine.retrieval_engine.reranker import rerank_candidates
from digitz_ai_nexus.engine.retrieval_engine.retrieval_debug import (
    build_retrieval_debug_payload,
)


STOP_WORDS = {
    "what", "is", "are", "the", "a", "an", "of", "to", "in", "on", "for",
    "and", "or", "with", "about", "how", "why", "when", "where", "does",
    "do", "can", "you", "me", "explain", "tell",
}

VECTOR_WEIGHT = 0.75
KEYWORD_WEIGHT = 0.20
PRIORITY_WEIGHT = 0.05

CHUNK_FIELDS = [
    "name",
    "knowledge_unit",
    "tenant",
    "business_unit",
    "project",
    "chunk_text",
    "embedding",
    "access_policy",
    "sensitivity",
    "context",
    "sub_context",
    "entity_type",
    "entity",
    "topic",
    "context_path",
    "priority",
]


def normalize_project(value):
    return (value or "").strip()


def tokenize(text):
    if not text:
        return []

    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

def apply_scope_balance(scored, top_k, requested_project, scope_mode):
    if not requested_project or scope_mode == "strict" or top_k <= 1:
        return scored[:top_k]

    top_results = scored[:top_k]

    has_project = any(row.get("scope_type") == "project" for row in top_results)
    has_general = any(row.get("scope_type") == "general" for row in top_results)

    if has_project and has_general:
        return top_results

    best_project = next((row for row in scored if row.get("scope_type") == "project"), None)
    best_general = next((row for row in scored if row.get("scope_type") == "general"), None)

    if not best_project or not best_general:
        return top_results

    balanced = []

    if best_project["score"] >= best_general["score"]:
        balanced = [best_project, best_general]
    else:
        balanced = [best_general, best_project]

    seen = {row["chunk"] for row in balanced}

    for row in scored:
        if row["chunk"] not in seen:
            balanced.append(row)
            seen.add(row["chunk"])

        if len(balanced) >= top_k:
            break

    return balanced[:top_k]

def cosine_similarity(vec1, vec2):
    if not vec1 or not vec2:
        return 0

    if len(vec1) != len(vec2):
        return 0

    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if not norm1 or not norm2:
        return 0

    return dot / (norm1 * norm2)


def keyword_score(query, chunk_text, context_path=None):
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0

    searchable_text = f"{chunk_text or ''} {context_path or ''}".lower()

    matched = 0
    for token in query_tokens:
        if token in searchable_text:
            matched += 1

    base_score = matched / len(query_tokens)

    query_clean = (query or "").lower().strip()
    phrase_boost = 0.0

    if query_clean and query_clean in searchable_text:
        phrase_boost = 0.25

    return min(base_score + phrase_boost, 1.0)


def priority_score(priority):
    try:
        priority = int(priority or 0)
    except Exception:
        priority = 0

    if priority <= 0:
        return 0

    return min(priority / 10, 1.0)


def build_context_filters(query_contract):
    filters = {
        "disabled": 0,
        "embedding_status": "Completed",
    }

    for field in [
        "tenant",
        "business_unit",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
    ]:
        if query_contract.get(field):
            filters[field] = query_contract.get(field)

    return filters


def fetch_chunks(filters):
    return frappe.get_all(
        "Nexus Knowledge Chunk",
        filters=filters,
        fields=CHUNK_FIELDS,
        limit_page_length=500,
    )


def get_candidate_chunks(query_contract):
    filters = build_context_filters(query_contract)

    project = normalize_project(query_contract.get("project"))
    scope_mode = query_contract.get("project_scope_mode") or "with_general"

    base_chunks = fetch_chunks(filters)

    if not project:
        return [
            row for row in base_chunks
            if not normalize_project(row.get("project"))
        ]

    if scope_mode == "strict":
        return [
            row for row in base_chunks
            if normalize_project(row.get("project")) == project
        ]

    return [
        row for row in base_chunks
        if normalize_project(row.get("project")) in ("", project)
    ]


def hybrid_final_score(vector_score, keyword_score_value, priority_score_value):
    return (
        (vector_score * VECTOR_WEIGHT)
        + (keyword_score_value * KEYWORD_WEIGHT)
        + (priority_score_value * PRIORITY_WEIGHT)
    )


def retrieve_allowed_chunks(query_contract, query_embedding=None, embedding_provider=None):
    query = query_contract.get("query")
    if not query:
        frappe.throw("Query is required")

    settings = frappe.get_single("Nexus Settings")

    top_k = int(query_contract.get("top_k") or settings.top_k or 5)

    retrieval_candidate_limit = int(
        getattr(settings, "retrieval_candidate_limit", None) or 30
    )

    rerank_candidate_limit = int(
        getattr(settings, "rerank_candidate_limit", None) or 20
    )

    enable_multi_query = int(
        getattr(settings, "enable_multi_query", 1) or 0
    )

    enable_reranking = int(
        getattr(settings, "enable_reranking", 1) or 0
    )

    enable_retrieval_debug = int(
        getattr(settings, "enable_retrieval_debug", 1) or 0
    )

    user_context = query_contract.get("user") or {}

    requested_project = normalize_project(query_contract.get("project"))
    scope_mode = query_contract.get("project_scope_mode") or "with_general"

    if enable_multi_query:
        query_variants = expand_query(query)
    else:
        query_variants = [query]

    if not query_variants:
        query_variants = [query]

    candidate_chunks = get_candidate_chunks(query_contract)

    weights = get_retrieval_weights()

    merged_candidates = {}
    denied = []

    for variant_query in query_variants:
        variant_embedding = query_embedding

        if variant_embedding is None or variant_query != query:
            variant_embedding = generate_embedding(
                variant_query,
                provider=embedding_provider
            )

        for row in candidate_chunks:
            allowed, reason = can_access_chunk(user_context, row)

            if not allowed:
                already_denied = any(d.get("chunk") == row.name for d in denied)
                if not already_denied:
                    denied.append({
                        "chunk": row.name,
                        "reason": reason,
                        "access_policy": row.access_policy,
                    })
                continue

            if not row.embedding:
                continue

            row_project = normalize_project(row.get("project"))

            candidate = build_scored_candidate(
                row=row,
                query=variant_query,
                query_embedding=variant_embedding,
                requested_project=requested_project,
                project_scope=scope_mode,
                weights=weights,
            )

            # Preserve old keys expected by existing Ask API / Testing Lab
            candidate["score"] = candidate.get("hybrid_score") or 0
            candidate["priority_score"] = priority_score(row.priority)
            candidate["chunk_text"] = row.chunk_text
            candidate["sensitivity"] = row.sensitivity
            candidate["context_path"] = row.context_path
            candidate["scope_type"] = "project" if row_project else "general"
            candidate["priority"] = row.priority or 0
            candidate["project"] = row_project

            chunk_name = candidate.get("chunk")
            if not chunk_name:
                continue

            if chunk_name not in merged_candidates:
                merged_candidates[chunk_name] = candidate
                continue

            existing = merged_candidates[chunk_name]

            # Keep strongest scores across multi-query variants
            for score_key in [
                "vector_score",
                "keyword_score",
                "business_keyword_boost",
                "project_boost",
                "hybrid_score",
                "final_score",
            ]:
                existing[score_key] = max(
                    float(existing.get(score_key) or 0),
                    float(candidate.get(score_key) or 0),
                )

            existing["score"] = existing["hybrid_score"]

            matched_queries = existing.get("matched_queries") or []
            matched_queries.extend(candidate.get("matched_queries") or [])
            existing["matched_queries"] = list(dict.fromkeys(matched_queries))

    scored = sorted(
        merged_candidates.values(),
        key=lambda x: (
            float(x.get("hybrid_score") or 0),
            float(x.get("keyword_score") or 0),
            float(x.get("vector_score") or 0),
        ),
        reverse=True,
    )

    scored = scored[:retrieval_candidate_limit]

    for index, candidate in enumerate(scored, start=1):
        candidate["rank_before_rerank"] = index

    if enable_reranking:
        reranked = rerank_candidates(
            query=query,
            candidates=scored,
            requested_project=requested_project,
            limit=rerank_candidate_limit,
        )
    else:
        reranked = scored
        for index, candidate in enumerate(reranked, start=1):
            candidate["rank_after_rerank"] = index
            candidate["rerank_bonus"] = 0.0
            candidate["rerank_score"] = candidate.get("hybrid_score") or 0
            candidate["final_score"] = candidate.get("hybrid_score") or 0
            candidate["rerank_reasons"] = []

    # Preserve your existing scope balance logic
    final_results = apply_scope_balance(
        scored=reranked,
        top_k=top_k,
        requested_project=requested_project,
        scope_mode=scope_mode,
    )

    final_names = {r.get("chunk") for r in final_results}

    for row in reranked:
        row["selected"] = row.get("chunk") in final_names
        row["score"] = row.get("final_score") or row.get("hybrid_score") or 0

    for row in final_results:
        row["selected"] = True
        row["score"] = row.get("final_score") or row.get("hybrid_score") or row.get("score") or 0

    return {
        "results": final_results,
        "debug": build_retrieval_debug_payload(reranked) if enable_retrieval_debug else [],
        "denied": denied,
        "query_variants": query_variants,
        "candidate_count": len(candidate_chunks),
        "allowed_count": len(scored),
        "denied_count": len(denied),
        "retrieval_mode": "hybrid_grounded_rag",
        "project_scope_mode": scope_mode,
        "weights": {
            "vector": weights.get("vector_weight"),
            "keyword": weights.get("keyword_weight"),
            "business_keyword": weights.get("business_term_weight"),
            "project_boost": weights.get("project_boost_weight"),
        },
        "features": {
            "multi_query": bool(enable_multi_query),
            "reranking": bool(enable_reranking),
            "retrieval_debug": bool(enable_retrieval_debug),
        },
    }