import frappe

from digitz_ai_nexus.engine.retrieval import retrieve_allowed_chunks
from digitz_ai_nexus.engine.prompt import build_prompt, SAFE_FALLBACK_ANSWER
from digitz_ai_nexus.engine.llm import generate_answer


RESTRICTED_ANSWER = "You do not have permission to access this information."


def answer_query(
    payload,
    retrieval_fn=None,
    embedding_provider=None,
    llm_provider=None,
    query_embedding=None,
):
    if not payload:
        frappe.throw("Payload is required")

    query = payload.get("query")
    if not query:
        frappe.throw("Query is required")

    retrieval_fn = retrieval_fn or retrieve_allowed_chunks

    retrieval_result = retrieval_fn(
        payload,
        query_embedding=query_embedding,
        embedding_provider=embedding_provider,
    )

    chunks = retrieval_result.get("results") or []
    denied = retrieval_result.get("denied") or []
    
    if retrieval_result.get("access_status") == "restricted":
        return build_restricted_response(
            retrieval_result=retrieval_result,
            denied=denied,
        )

    if not chunks:
        if retrieval_result.get("access_status") == "restricted":
            return build_restricted_response(
                retrieval_result=retrieval_result,
                denied=denied,
            )

        return build_safe_fallback(
            retrieval_result=retrieval_result,
            denied=denied,
        )

    confidence = calculate_confidence(chunks)
    minimum_confidence = get_minimum_confidence()

    if confidence < minimum_confidence:
        return build_safe_fallback(
            retrieval_result=retrieval_result,
            denied=denied,
            confidence=confidence,
        )

    prompt = build_prompt(payload, chunks)

    answer = generate_answer(prompt, provider=llm_provider)
    answer = (answer or "").strip()

    if not answer:
        return build_safe_fallback(
            retrieval_result=retrieval_result,
            denied=denied,
            confidence=confidence,
        )

    if is_fallback_answer(answer):
        return build_safe_fallback(
            retrieval_result=retrieval_result,
            denied=denied,
            confidence=confidence,
        )

    sources = build_sources(chunks)

    return {
        "status": "success",
        "access_status": "allowed",
        "answer": answer,
        "confidence": confidence,
        "sources": sources,
        "citations": build_citation_summary(sources),
        "retrieval_result": retrieval_result,
        "fallback_used": 0,
    }
    
def build_sources(chunks):
    sources = []
    seen = set()

    for row in chunks:
        chunk_id = row.get("chunk") or row.get("name")

        key = (
            chunk_id,
            row.get("knowledge_unit"),
            row.get("context_path"),
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append({
            "chunk": chunk_id,
            "knowledge_unit": row.get("knowledge_unit"),
            "knowledge_title": (
                row.get("knowledge_title")
                or row.get("unit_title")
                or row.get("knowledge_unit")
            ),
            "context_path": row.get("context_path"),
            "business_unit": row.get("business_unit"),
            "project": row.get("project"),
            "tenant": row.get("tenant"),
            "context": row.get("context"),
            "sub_context": row.get("sub_context"),
            "entity_type": row.get("entity_type"),
            "entity": row.get("entity"),
            "topic": row.get("topic"),
            "scope_type": row.get("scope_type"),
            "sensitivity": row.get("sensitivity"),
            "chunk_preview": row.get("chunk_preview") or (row.get("chunk_text") or "")[:300],

            "score": row.get("score"),
            "vector_score": row.get("vector_score"),
            "keyword_score": row.get("keyword_score"),
            "priority_score": row.get("priority_score"),
            "business_keyword_boost": row.get("business_keyword_boost"),
            "project_boost": row.get("project_boost"),
            "hybrid_score": row.get("hybrid_score"),
            "rerank_bonus": row.get("rerank_bonus"),
            "rerank_score": row.get("rerank_score"),
            "final_score": row.get("final_score"),
            "rank_before_rerank": row.get("rank_before_rerank"),
            "rank_after_rerank": row.get("rank_after_rerank"),
            "rerank_reason": row.get("rerank_reason"),
            "rerank_reasons": row.get("rerank_reasons") or [],
        })

    return sources


def build_citation_summary(sources):
    if not sources:
        return []

    citation_summary = []

    for idx, source in enumerate(sources, start=1):
        citation_summary.append({
            "source_no": idx,
            "chunk": source.get("chunk"),
            "knowledge_unit": source.get("knowledge_unit"),
            "knowledge_title": source.get("knowledge_title"),
            "context_path": source.get("context_path"),
            "business_unit": source.get("business_unit"),
            "project": source.get("project"),
            "topic": source.get("topic"),
            "scope_type": source.get("scope_type"),
            "score": source.get("score"),
        })

    return citation_summary

def calculate_confidence(chunks):
    if not chunks:
        return 0.0

    scores = []

    for row in chunks:
        score = (
            row.get("final_score")
            or row.get("score")
            or row.get("hybrid_score")
            or 0
        )

        try:
            scores.append(float(score))
        except Exception:
            scores.append(0.0)

    if not scores:
        return 0.0

    top_score = max(scores)
    avg_score = sum(scores) / len(scores)

    confidence = (top_score * 0.7) + (avg_score * 0.3)

    return round(confidence, 2)


def get_minimum_confidence():
    settings = frappe.get_single("Nexus Settings")
    value = getattr(settings, "minimum_confidence", None)

    if value is None:
        return 0.20

    try:
        return float(value)
    except Exception:
        return 0.20


def is_fallback_answer(answer):
    normalized = (answer or "").strip().lower()
    fallback = SAFE_FALLBACK_ANSWER.strip().lower()

    return normalized == fallback


def build_safe_fallback(retrieval_result=None, denied=None, confidence=0.0):
    return {
        "status": "success",
        "access_status": "no_context",
        "answer": SAFE_FALLBACK_ANSWER,
        "confidence": round(float(confidence or 0), 2),
        "sources": [],
        "citations": [],
        "retrieval_result": retrieval_result or {},
        "denied": denied or [],
        "fallback_used": 1,
    }


def build_restricted_response(retrieval_result=None, denied=None):
    return {
        "status": "success",
        "access_status": "restricted",
        "answer": RESTRICTED_ANSWER,
        "confidence": 0,
        "sources": [],
        "citations": [],
        "retrieval_result": retrieval_result or {},
        "denied": denied or [],
        "fallback_used": 1,
    }