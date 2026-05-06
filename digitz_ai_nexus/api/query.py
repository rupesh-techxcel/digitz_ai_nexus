import json
import frappe

from digitz_ai_nexus.engine.retrieval import retrieve_allowed_chunks
from digitz_ai_nexus.engine.llm import generate_answer
from digitz_ai_nexus.engine.prompt import build_prompt, SAFE_FALLBACK_ANSWER


SAFE_FALLBACK_ANSWER = "I do not have enough approved knowledge to answer this."

def log_query(payload, retrieval_result, answer=None, status="Success", error_message=None):
    try:
        user = payload.get("user") or {}

        log = frappe.new_doc("Nexus Query Log")
        log.tenant = payload.get("tenant")
        log.business_unit = payload.get("business_unit")
        log.project = payload.get("project")
        log.caller_system = payload.get("caller_system")
        log.use_case = payload.get("use_case")
        log.status = status

        log.query = payload.get("query")
        log.context = payload.get("context")
        log.sub_context = payload.get("sub_context")
        log.entity_type = payload.get("entity_type")
        log.entity = payload.get("entity")
        log.topic = payload.get("topic")

        log.user_id = user.get("user_id")
        log.user_roles = json.dumps(user.get("roles") or [])

        results = retrieval_result.get("results") if retrieval_result else []
        denied = retrieval_result.get("denied") if retrieval_result else []

        if results:
            log.access_status = "allowed"
        elif denied:
            log.access_status = "restricted"
        else:
            log.access_status = "no_context"

        log.retrieved_chunks = json.dumps([r.get("chunk") for r in results])
        log.answer = answer
        log.confidence = results[0].get("score") if results else 0
        log.llm_model = frappe.get_single("Nexus Settings").llm_model
        log.error_message = error_message

        log.insert(ignore_permissions=True)
        frappe.db.commit()

        return log.name

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to create Nexus Query Log")
        return None

def build_retrieval_debug_response(retrieval_result):
    retrieval_result = retrieval_result or {}

    return {
        "query_variants": retrieval_result.get("query_variants") or [],
        "ranked_chunks": retrieval_result.get("debug") or [],
        "denied_chunks": retrieval_result.get("denied") or [],
        "features": retrieval_result.get("features") or {},
        "weights": retrieval_result.get("weights") or {},
        "candidate_count": retrieval_result.get("candidate_count") or 0,
        "allowed_count": retrieval_result.get("allowed_count") or 0,
        "denied_count": retrieval_result.get("denied_count") or 0,
        "retrieval_mode": retrieval_result.get("retrieval_mode"),
        "project_scope_mode": retrieval_result.get("project_scope_mode"),
    }
    
@frappe.whitelist()
def ask(payload=None, retrieval_fn=None, embedding_provider=None, llm_provider=None):
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not payload:
        payload = dict(frappe.local.form_dict)

    try:
        retrieval_fn = retrieval_fn or retrieve_allowed_chunks

        retrieval_result = retrieval_fn(
            payload,
            embedding_provider=embedding_provider
        )

        results = retrieval_result.get("results") or []
        denied = retrieval_result.get("denied") or []

        if not results:
            if denied:
                answer = "You do not have permission to access this information."
                access_status = "restricted"
            else:
                answer = SAFE_FALLBACK_ANSWER
                access_status = "no_context"

            log_name = log_query(payload, retrieval_result, answer=answer)
 
            return {
                "status": "success",
                "access_status": access_status,
                "answer": answer,
                "confidence": 0,
                "sources": [],
                "log": log_name,
                "retrieval_debug": build_retrieval_debug_response(retrieval_result)
                }
        prompt = build_prompt(payload, results)
        answer = generate_answer(prompt, provider=llm_provider)

        log_name = log_query(payload, retrieval_result, answer=answer)

        return {
                "status": "success",
                "access_status": "allowed",
                "answer": answer,
                "confidence": results[0].get("score"),
                "sources": [
                    {
                        "chunk": r.get("chunk"),
                        "knowledge_unit": r.get("knowledge_unit"),
                        "context_path": r.get("context_path"),
                        "business_unit": r.get("business_unit"),
                        "project": r.get("project"),
                        "scope_type": r.get("scope_type"),
                        "score": r.get("score"),
                        "vector_score": r.get("vector_score"),
                        "keyword_score": r.get("keyword_score"),
                        "priority_score": r.get("priority_score"),
                        "business_keyword_boost": r.get("business_keyword_boost"),
                        "project_boost": r.get("project_boost"),
                        "hybrid_score": r.get("hybrid_score"),
                        "rerank_bonus": r.get("rerank_bonus"),
                        "final_score": r.get("final_score"),
                    }
                    for r in results
                ],
                "log": log_name,
                "retrieval_debug": build_retrieval_debug_response(retrieval_result)
            }

    except Exception as e:
        log_query(payload or {}, {}, status="Failed", error_message=str(e))
        frappe.log_error(frappe.get_traceback(), "Nexus Ask Failed")

        return {
            "status": "failed",
            "answer": None,
            "error": str(e),
            "retrieval_debug": build_retrieval_debug_response({})
        }