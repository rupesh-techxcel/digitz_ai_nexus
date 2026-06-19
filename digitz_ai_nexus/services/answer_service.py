import frappe

from digitz_ai_nexus.engine.retrieval import retrieve_allowed_chunks
from digitz_ai_nexus.engine.prompt import (
    build_prompt,
    build_router_prompt,
    build_query_too_long_prompt,
    SAFE_FALLBACK_ANSWER,
    ROUTE_TO_KNOWLEDGE_TOKEN,
)
from digitz_ai_nexus.engine.llm import generate_answer
from digitz_ai_nexus.services.question_correlation import get_correlated_questions_for_answer


RESTRICTED_ANSWER = "You do not have permission to access this information."

MAX_QUERY_CHARS = 500


def _is_chat_mode(response_mode_key):
    return str(response_mode_key or "").lower() in ("chat", "live chat")


def _resolve_chat_mode(payload):
    """
    Return the chat_mode for this request: "rag" (default) or "agent_loop".

    Set chat_mode in the query payload or in ai_profile to activate the agent loop.
    The right place to configure this is in the AI Agent Profile or session config.
    """
    return (
        payload.get("chat_mode")
        or (payload.get("ai_profile") or {}).get("chat_mode")
        or "rag"
    )


def route_intent(payload, llm_provider=None):
    """
    Combined router + conversational responder for chat mode.

    Returns a dict with an "action" key:
      {"action": "conversational",  "answer": "..."}
      {"action": "knowledge_seeking"}
      {"action": "escalate",        "answer": "..."}
      {"action": "predefined",      "answer": "..."}
      {"action": "declined",        "answer": "..."}
    """
    resolved_intents = payload.get("resolved_intents") or []
    prompt = build_router_prompt(payload, resolved_intents=resolved_intents)
    response = (generate_answer(prompt, provider=llm_provider) or "").strip()

    if not response or response.startswith(ROUTE_TO_KNOWLEDGE_TOKEN):
        return {"action": "knowledge_seeking"}

    if response.startswith("ACTION:ESCALATE"):
        escalate_intent = next(
            (i for i in resolved_intents if i.get("action_type") == "escalate" and i.get("active")),
            None,
        )
        answer = (escalate_intent or {}).get("response_template") or "I'll connect you with our team shortly."
        return {"action": "escalate", "answer": answer}

    if response.startswith("ACTION:PREDEFINED:"):
        handler_name = response[len("ACTION:PREDEFINED:"):].strip()
        intent = next((i for i in resolved_intents if i.get("name") == handler_name), None)
        answer = (intent or {}).get("response_template") or ""
        return {"action": "predefined", "answer": answer}

    if response.startswith("ACTION:DECLINED:"):
        handler_name = response[len("ACTION:DECLINED:"):].strip()
        intent = next((i for i in resolved_intents if i.get("name") == handler_name), None)
        answer = (intent or {}).get("decline_response") or "That option is not available in this context."
        return {"action": "declined", "answer": answer}

    return {"action": "conversational", "answer": response}


def run_retrieval_pipeline(
    payload,
    retrieval_fn=None,
    embedding_provider=None,
    query_embedding=None,
):
    """
    Run the full retrieval pipeline with all governance rules applied.

    This is the shared retrieval core used by both the RAG pipeline (answer_query)
    and the agent loop's search_knowledge tool. Both paths must go through the same
    rules — access enforcement, restricted access handling, question-first retry,
    and confidence threshold checks.

    Returns: (chunks, retrieval_result, confidence, access_status)

    access_status values:
      "allowed"       — chunks found above confidence threshold, safe to use
      "restricted"    — knowledge exists but caller cannot access it
      "no_context"    — no relevant knowledge found
      "low_confidence"— knowledge found but below minimum confidence threshold
    """
    retrieval_fn = retrieval_fn or retrieve_allowed_chunks

    retrieval_result = retrieval_fn(
        payload,
        query_embedding=query_embedding,
        embedding_provider=embedding_provider,
    )

    chunks = retrieval_result.get("results") or []
    denied = retrieval_result.get("denied") or []

    # Restricted: relevant knowledge exists but caller cannot access it.
    # Never convert this to no_context — keep the distinction.
    if retrieval_result.get("access_status") == "restricted" or denied:
        return [], retrieval_result, 0.0, "restricted"

    # No results but question-first narrowing was applied — retry with broader search
    if not chunks and (retrieval_result.get("question_first") or {}).get("applied"):
        retry_result = retry_without_question_first(
            payload,
            retrieval_fn=retrieval_fn,
            embedding_provider=embedding_provider,
            query_embedding=query_embedding,
            reason="question_first_no_context",
        )
        retry_chunks = retry_result.get("results") or []
        retry_denied = retry_result.get("denied") or []

        if retry_result.get("access_status") == "restricted" or retry_denied:
            return [], retry_result, 0.0, "restricted"

        if retry_chunks:
            retrieval_result = retry_result
            chunks = retry_chunks
        else:
            return [], retry_result, 0.0, "no_context"

    if not chunks:
        return [], retrieval_result, 0.0, "no_context"

    confidence = calculate_confidence(chunks)
    minimum_confidence = get_minimum_confidence()

    if confidence < minimum_confidence:
        # If question-first was applied, retry with broader search before giving up
        if (retrieval_result.get("question_first") or {}).get("applied"):
            retry_result = retry_without_question_first(
                payload,
                retrieval_fn=retrieval_fn,
                embedding_provider=embedding_provider,
                query_embedding=query_embedding,
            )
            retry_chunks = retry_result.get("results") or []
            retry_denied = retry_result.get("denied") or []
            retry_confidence = calculate_confidence(retry_chunks)

            if retry_result.get("access_status") == "restricted" or retry_denied:
                return [], retry_result, 0.0, "restricted"

            if retry_chunks and retry_confidence >= minimum_confidence:
                return retry_chunks, retry_result, retry_confidence, "allowed"

            best_confidence = max(confidence, retry_confidence)
            best_result = retry_result if retry_chunks else retrieval_result
            return [], best_result, best_confidence, "low_confidence"

        return [], retrieval_result, confidence, "low_confidence"

    return chunks, retrieval_result, confidence, "allowed"


def handle_host_fallback(payload, llm_provider=None):
    """
    Fallback for chat mode when retrieval finds no usable knowledge.
    Uses the profile's configured fallback_message if set.
    fallback_used=1 is preserved so the escalation signal still fires.
    """
    ai_profile = payload.get("ai_profile") or {}
    answer = (
        ai_profile.get("fallback_message")
        or payload.get("agent_fallback_message")
        or "I don't currently have confirmed information on that topic."
    )
    return {
        "status": "success",
        "access_status": "no_context",
        "answer": answer,
        "confidence": 0.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 1,
    }


def handle_query_too_long(payload, llm_provider=None):
    """
    Friendly LLM response when the user message exceeds MAX_QUERY_CHARS.
    """
    prompt = build_query_too_long_prompt(payload)
    answer = (generate_answer(prompt, provider=llm_provider) or "").strip()
    if not answer:
        answer = (
            "Your message is quite long — could you summarise your question in a few words? "
            "I work best with focused questions."
        )
    return {
        "status": "success",
        "access_status": "conversational",
        "answer": answer,
        "confidence": 1.0,
        "sources": [],
        "citations": [],
        "retrieval_result": {},
        "fallback_used": 0,
    }


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

    response_mode_key = payload.get("response_mode") or payload.get("use_case")
    is_chat = _is_chat_mode(response_mode_key)

    if is_chat:
        # 1. Length guard
        if len(query.strip()) > MAX_QUERY_CHARS:
            return handle_query_too_long(payload, llm_provider=llm_provider)

        # 2. Agent loop mode — LLM drives retrieval strategy
        if _resolve_chat_mode(payload) == "agent_loop":
            from digitz_ai_nexus.engine.chat_agent_loop import run_chat_agent_loop
            return run_chat_agent_loop(payload, retrieval_fn=retrieval_fn)

        # 3. Intent router — special cases, conversational, or knowledge-seeking
        route = route_intent(payload, llm_provider=llm_provider)
        action = route.get("action")

        if action == "escalate":
            return {
                "status": "success",
                "access_status": "intent_handled",
                "answer": route.get("answer") or "I'll connect you with our team shortly.",
                "confidence": 1.0,
                "sources": [],
                "citations": [],
                "retrieval_result": {},
                "fallback_used": 0,
                "user_requested_human": True,
                "intent_action": "escalate",
            }

        if action in ("predefined", "declined"):
            return {
                "status": "success",
                "access_status": "intent_handled",
                "answer": route.get("answer") or "",
                "confidence": 1.0,
                "sources": [],
                "citations": [],
                "retrieval_result": {},
                "fallback_used": 0,
                "intent_action": action,
            }

        if action == "conversational":
            return {
                "status": "success",
                "access_status": "conversational",
                "answer": route.get("answer"),
                "confidence": 1.0,
                "sources": [],
                "citations": [],
                "retrieval_result": {},
                "fallback_used": 0,
            }
        # action == "knowledge_seeking" — fall through to retrieval pipeline

    # Guard: empty allowed_access_policies means access resolution failed — deny
    allowed_policies = payload.get("allowed_access_policies")
    if allowed_policies is not None and len(allowed_policies) == 0:
        frappe.throw("Access policy resolution failed. Retrieval cannot proceed.")

    chunks, retrieval_result, confidence, access_status = run_retrieval_pipeline(
        payload,
        retrieval_fn=retrieval_fn,
        embedding_provider=embedding_provider,
        query_embedding=query_embedding,
    )

    if access_status == "restricted":
        return build_restricted_response(
            retrieval_result=retrieval_result,
            denied=retrieval_result.get("denied") or [],
        )

    if access_status in ("no_context", "low_confidence") or not chunks:
        return _fallback(
            is_chat, payload, llm_provider,
            retrieval_result=retrieval_result,
            denied=retrieval_result.get("denied") or [],
            confidence=confidence,
        )

    prompt = build_prompt(payload, chunks)
    answer = (generate_answer(prompt, provider=llm_provider) or "").strip()

    if not answer or is_fallback_answer(answer):
        return _fallback(
            is_chat, payload, llm_provider,
            retrieval_result=retrieval_result,
            denied=retrieval_result.get("denied") or [],
            confidence=confidence,
        )

    sources = build_sources(chunks)
    correlated_questions = get_correlated_questions_for_answer(payload, chunks)

    return {
        "status": "success",
        "access_status": "allowed",
        "answer": answer,
        "confidence": confidence,
        "sources": sources,
        "citations": build_citation_summary(sources),
        "correlated_questions": correlated_questions,
        "retrieval_result": retrieval_result,
        "fallback_used": 0,
    }


def _fallback(is_chat, payload, llm_provider, retrieval_result=None, denied=None, confidence=0.0):
    """Single point of control for all fallback paths."""
    if is_chat:
        return handle_host_fallback(payload, llm_provider=llm_provider)
    return build_safe_fallback(
        retrieval_result=retrieval_result,
        denied=denied,
        confidence=confidence,
    )


def retry_without_question_first(
    payload,
    retrieval_fn,
    embedding_provider=None,
    query_embedding=None,
    reason="question_first_low_confidence",
):
    retry_payload = dict(payload or {})
    retry_payload["disable_question_first"] = 1

    retry_result = retrieval_fn(
        retry_payload,
        query_embedding=query_embedding,
        embedding_provider=embedding_provider,
    )
    retry_result["question_first_retry"] = {
        "reason": reason,
        "used_broader_content_search": True,
    }
    return retry_result


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
            "semantic_index_entry": row.get("semantic_index_entry"),
            "semantic_index_type": row.get("semantic_index_type"),
            "semantic_index_score": row.get("semantic_index_score"),
            "semantic_index_boost": row.get("semantic_index_boost"),
            "context_summary": row.get("context_summary"),
            "context_summary_title": row.get("context_summary_title"),
            "context_summary_score": row.get("context_summary_score"),
            "context_summary_boost": row.get("context_summary_boost"),
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
