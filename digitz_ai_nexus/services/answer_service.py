import frappe

from digitz_ai_nexus.engine.retrieval import retrieve_allowed_chunks
from digitz_ai_nexus.engine.prompt import build_prompt, SAFE_FALLBACK_ANSWER
from digitz_ai_nexus.engine.llm import generate_answer


RESTRICTED_ANSWER = "You do not have permission to access this information."


def answer_query(payload, retrieval_fn=None, embedding_provider=None, llm_provider=None):
    """
    Main Nexus answer pipeline.

    Flow:
    query contract
    -> retrieve allowed chunks
    -> build grounded prompt
    -> generate LLM answer
    -> return answer + confidence + sources
    """

    if not payload:
        frappe.throw("Payload is required")

    query = payload.get("query")
    if not query:
        frappe.throw("Query is required")

    retrieval_fn = retrieval_fn or retrieve_allowed_chunks

    retrieval_result = retrieval_fn(
        payload,
        embedding_provider=embedding_provider,
    )

    chunks = retrieval_result.get("results") or []
    denied = retrieval_result.get("denied") or []

    if not chunks:
        if denied:
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

    return {
        "status": "success",
        "access_status": "allowed",
        "answer": answer,
        "confidence": confidence,
        "sources": build_sources(chunks),
        "retrieval_result": retrieval_result,
        "fallback_used": 0,
    }


def build_sources(chunks):
    """
    Build source citation contract from retrieved chunks.
    """

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
            "context_path": row.get("context_path"),
            "business_unit": row.get("business_unit"),
            "project": row.get("project"),
            "scope_type": row.get("scope_type"),
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
        })

    return sources


def calculate_confidence(chunks):
    """
    Basic MVP confidence calculation from retrieval scores.
    """

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
    """
    Read minimum confidence from Nexus Settings if available.
    Defaults to 0.20.
    """

    settings = frappe.get_single("Nexus Settings")

    value = getattr(settings, "minimum_confidence", None)

    if value is None:
        return 0.20

    try:
        return float(value)
    except Exception:
        return 0.20


def is_fallback_answer(answer):
    """
    Detect model-generated fallback and normalize it.
    """

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
        "retrieval_result": retrieval_result or {},
        "denied": denied or [],
        "fallback_used": 1,
    }