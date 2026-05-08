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

    # Role fields
    "allowed_roles",
    "roles",
    "user_roles",

    # Deny fields
    "denied_roles",
    "excluded_roles",
    "deny_roles",

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


def enrich_chunk_roles_from_unit(rows):
    if not rows:
        return rows

    unit_names = list({
        row.get("knowledge_unit")
        for row in rows
        if row.get("knowledge_unit")
    })

    if not unit_names:
        return rows

    unit_meta = frappe.get_meta("Nexus Knowledge Unit")

    role_fields = [
        "allowed_roles",
        "denied_roles",
        "excluded_roles",
        "deny_roles",
    ]

    valid_unit_fields = [
        field for field in role_fields
        if unit_meta.has_field(field)
    ]

    if not valid_unit_fields:
        return rows

    units = frappe.get_all(
        "Nexus Knowledge Unit",
        filters={"name": ["in", unit_names]},
        fields=["name"] + valid_unit_fields,
        limit_page_length=500,
    )

    unit_map = {unit.name: unit for unit in units}

    for row in rows:
        unit = unit_map.get(row.get("knowledge_unit"))
        if not unit:
            continue

        for field in role_fields:
            if field not in row or not row.get(field):
                row[field] = unit.get(field)

    return rows


def fetch_chunks(filters):
    meta = frappe.get_meta("Nexus Knowledge Chunk")

    valid_fields = [
        field for field in CHUNK_FIELDS
        if field == "name" or meta.has_field(field)
    ]

    rows = frappe.get_all(
        "Nexus Knowledge Chunk",
        filters=filters,
        fields=valid_fields,
        limit_page_length=500,
    )

    return enrich_chunk_roles_from_unit(rows)


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


def row_value(row, fieldname):
    if isinstance(row, dict):
        return row.get(fieldname)

    return getattr(row, fieldname, None)


def build_restricted_response(
    denied,
    query_variants,
    candidate_chunks,
    scope_mode,
    weights,
    enable_multi_query,
    enable_reranking,
    enable_retrieval_debug,
    strongest_denied,
):
    return {
        "results": [],
        "debug": [],
        "denied": denied,
        "query_variants": query_variants,
        "candidate_count": len(candidate_chunks),
        "allowed_count": 0,
        "denied_count": len(denied),
        "retrieval_mode": "hybrid_grounded_rag",
        "project_scope_mode": scope_mode,
        "access_status": "restricted",
        "access_reason": strongest_denied.get("reason") or "Restricted",
        "restricted_chunk": strongest_denied,
        "weights": {
            "vector": weights.get("vector_weight"),
            "keyword": weights.get("keyword_weight"),
            "business_keyword": weights.get("business_term_weight"),
            "project_boost": weights.get("project_boost_weight"),
            "stability_vector": 0.45,
            "stability_keyword": 0.25,
            "stability_priority": 0.10,
            "stability_project": 0.10,
            "stability_rerank": 0.10,
        },
        "features": {
            "multi_query": bool(enable_multi_query),
            "reranking": bool(enable_reranking),
            "retrieval_debug": bool(enable_retrieval_debug),
        },
    }
def build_denied_debug_row(row, query, reason, vector_score=0):
    return {
        "chunk": row_value(row, "name"),
        "knowledge_unit": row_value(row, "knowledge_unit"),
        "reason": reason,
        "access_policy": row_value(row, "access_policy"),
        "keyword_score": keyword_score(
            query,
            row_value(row, "chunk_text"),
            row_value(row, "context_path"),
        ),
        "vector_score": float(vector_score or 0),
        "chunk_text": row_value(row, "chunk_text"),
        "context_path": row_value(row, "context_path"),
    }


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
    denied_relevance = {}

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
                denied_vector_score = 0

                try:
                    if row.embedding and variant_embedding:
                        denied_vector_score = cosine_similarity(
                            variant_embedding,
                            json.loads(row.embedding)
                        )
                except Exception:
                    denied_vector_score = 0

                denied_row = build_denied_debug_row(
                    row,
                    variant_query,
                    reason,
                    denied_vector_score,
                )

                denied_chunk = denied_row.get("chunk")

                if denied_chunk:
                    existing = denied_relevance.get(denied_chunk) or {}

                    existing_score = max(
                        float(existing.get("keyword_score") or 0),
                        float(existing.get("vector_score") or 0),
                    )

                    new_score = max(
                        float(denied_row.get("keyword_score") or 0),
                        float(denied_row.get("vector_score") or 0),
                    )

                    if new_score >= existing_score:
                        denied_relevance[denied_chunk] = denied_row

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

            candidate["score"] = candidate.get("hybrid_score") or 0
            candidate["priority_score"] = priority_score(row.priority)
            candidate["chunk_text"] = row.chunk_text
            candidate["sensitivity"] = row.sensitivity
            candidate["context_path"] = row.context_path
            candidate["knowledge_unit"] = row.knowledge_unit
            candidate["business_unit"] = row.business_unit
            candidate["tenant"] = row.tenant
            candidate["context"] = row.context
            candidate["sub_context"] = row.sub_context
            candidate["entity_type"] = row.entity_type
            candidate["entity"] = row.entity
            candidate["topic"] = row.topic
            candidate["scope_type"] = "project" if row_project else "general"
            candidate["priority"] = row.priority or 0
            candidate["project"] = row_project

            candidate["stable_vector_score"] = float(candidate.get("vector_score") or 0)
            candidate["stable_keyword_score"] = float(candidate.get("keyword_score") or 0)
            candidate["stable_priority_score"] = float(candidate.get("priority_score") or 0)
            candidate["stable_project_score"] = float(candidate.get("project_boost") or 0)
            candidate["stable_rerank_score"] = 0.0

            candidate["stable_final_score"] = round(
                (
                    candidate["stable_vector_score"] * 0.45
                    + candidate["stable_keyword_score"] * 0.25
                    + candidate["stable_priority_score"] * 0.10
                    + candidate["stable_project_score"] * 0.10
                    + candidate["stable_rerank_score"] * 0.10
                ),
                6,
            )

            candidate["retrieval_stability_score"] = candidate["stable_final_score"]

            chunk_name = candidate.get("chunk")
            if not chunk_name:
                continue

            if chunk_name not in merged_candidates:
                merged_candidates[chunk_name] = candidate
                continue

            existing = merged_candidates[chunk_name]

            for score_key in [
                "vector_score",
                "keyword_score",
                "business_keyword_boost",
                "project_boost",
                "hybrid_score",
                "final_score",
                "stable_vector_score",
                "stable_keyword_score",
                "stable_priority_score",
                "stable_project_score",
                "stable_rerank_score",
                "stable_final_score",
                "retrieval_stability_score",
            ]:
                existing[score_key] = max(
                    float(existing.get(score_key) or 0),
                    float(candidate.get(score_key) or 0),
                )

            existing["score"] = existing.get("hybrid_score") or 0

            matched_queries = existing.get("matched_queries") or []
            matched_queries.extend(candidate.get("matched_queries") or [])
            existing["matched_queries"] = list(dict.fromkeys(matched_queries))

    scored = sorted(
        merged_candidates.values(),
        key=lambda x: (
            float(x.get("hybrid_score") or 0),
            float(x.get("retrieval_stability_score") or 0),
            float(x.get("keyword_score") or 0),
            float(x.get("vector_score") or 0),
            float(x.get("priority_score") or 0),
        ),
        reverse=True,
    )

    scored = scored[:retrieval_candidate_limit]

    strongest_denied_score = 0.0
    strongest_denied = None

    for denied_row in denied_relevance.values():
        denied_score = max(
            float(denied_row.get("keyword_score") or 0),
            float(denied_row.get("vector_score") or 0),
        )

        if denied_score >= strongest_denied_score:
            strongest_denied_score = denied_score
            strongest_denied = denied_row

    restricted_threshold = 0.01

    if strongest_denied and strongest_denied_score >= restricted_threshold:
        return build_restricted_response(
            denied=denied,
            query_variants=query_variants,
            candidate_chunks=candidate_chunks,
            scope_mode=scope_mode,
            weights=weights,
            enable_multi_query=enable_multi_query,
            enable_reranking=enable_reranking,
            enable_retrieval_debug=enable_retrieval_debug,
            strongest_denied=strongest_denied,
        )

    for index, candidate in enumerate(scored, start=1):
        candidate["rank_before_rerank"] = index

    if enable_reranking:
        reranked = rerank_candidates(
            query=query,
            candidates=scored,
            requested_project=requested_project,
            limit=rerank_candidate_limit,
        )

        for index, candidate in enumerate(reranked, start=1):
            candidate["rank_after_rerank"] = candidate.get("rank_after_rerank") or index
            candidate["stable_rerank_score"] = float(candidate.get("rerank_bonus") or 0)

            candidate["stable_final_score"] = round(
                (
                    float(candidate.get("stable_vector_score") or candidate.get("vector_score") or 0) * 0.45
                    + float(candidate.get("stable_keyword_score") or candidate.get("keyword_score") or 0) * 0.25
                    + float(candidate.get("stable_priority_score") or candidate.get("priority_score") or 0) * 0.10
                    + float(candidate.get("stable_project_score") or candidate.get("project_boost") or 0) * 0.10
                    + float(candidate.get("stable_rerank_score") or 0) * 0.10
                ),
                6,
            )

            candidate["retrieval_stability_score"] = candidate["stable_final_score"]

            candidate["final_score"] = (
                candidate.get("final_score")
                or candidate.get("rerank_score")
                or candidate.get("retrieval_stability_score")
                or candidate.get("hybrid_score")
                or 0
            )
    else:
        reranked = scored

        for index, candidate in enumerate(reranked, start=1):
            candidate["rank_after_rerank"] = index
            candidate["rerank_bonus"] = 0.0
            candidate["rerank_score"] = candidate.get("hybrid_score") or 0
            candidate["stable_rerank_score"] = 0.0

            candidate["stable_final_score"] = round(
                (
                    float(candidate.get("stable_vector_score") or candidate.get("vector_score") or 0) * 0.45
                    + float(candidate.get("stable_keyword_score") or candidate.get("keyword_score") or 0) * 0.25
                    + float(candidate.get("stable_priority_score") or candidate.get("priority_score") or 0) * 0.10
                    + float(candidate.get("stable_project_score") or candidate.get("project_boost") or 0) * 0.10
                    + float(candidate.get("stable_rerank_score") or 0) * 0.10
                ),
                6,
            )

            candidate["retrieval_stability_score"] = candidate["stable_final_score"]
            candidate["final_score"] = candidate.get("hybrid_score") or candidate["stable_final_score"]
            candidate["rerank_reasons"] = []

    final_results = apply_scope_balance(
        scored=reranked,
        top_k=top_k,
        requested_project=requested_project,
        scope_mode=scope_mode,
    )

    final_names = {r.get("chunk") for r in final_results}

    for row in reranked:
        row["selected"] = row.get("chunk") in final_names
        row["score"] = (
            row.get("final_score")
            or row.get("retrieval_stability_score")
            or row.get("hybrid_score")
            or 0
        )

    for row in final_results:
        row["selected"] = True
        row["score"] = (
            row.get("final_score")
            or row.get("retrieval_stability_score")
            or row.get("hybrid_score")
            or row.get("score")
            or 0
        )

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
            "stability_vector": 0.45,
            "stability_keyword": 0.25,
            "stability_priority": 0.10,
            "stability_project": 0.10,
            "stability_rerank": 0.10,
        },
        "features": {
            "multi_query": bool(enable_multi_query),
            "reranking": bool(enable_reranking),
            "retrieval_debug": bool(enable_retrieval_debug),
        },
    }

def clamp_score(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value or 0)
    except Exception:
        value = 0.0

    return max(minimum, min(value, maximum))


def calculate_retrieval_final_score(
    vector_score=0,
    keyword_score=0,
    priority_score=0,
    project_score=0,
    rerank_score=0,
):
    vector_score = clamp_score(vector_score)
    keyword_score = clamp_score(keyword_score)
    priority_score = clamp_score(priority_score)
    project_score = clamp_score(project_score)
    rerank_score = clamp_score(rerank_score)

    final_score = (
        vector_score * 0.45
        + keyword_score * 0.25
        + priority_score * 0.10
        + project_score * 0.10
        + rerank_score * 0.10
    )

    return {
        "vector_score": vector_score,
        "keyword_score": keyword_score,
        "priority_score": priority_score,
        "project_score": project_score,
        "rerank_score": rerank_score,
        "final_score": round(final_score, 6),
    }