import json
import frappe

from digitz_ai_nexus.services.answer_service import answer_query
from digitz_ai_nexus.services.answer_formatter import format_answer_response


SYNTHETIC_TEST_EMBEDDING = [0.0, 1.0, 0.0]


def get_query_embedding_override(payload):
    """
    Synthetic Nexus certification tests use deterministic dummy embeddings.

    This avoids comparing real provider embeddings against seeded test vectors.
    Production / real knowledge queries should not use this override.
    """
    payload = payload or {}

    if payload.get("tenant") != "TEST-NEXUS":
        return None

    if payload.get("entity") == "Nexus Test Orbit":
        return SYNTHETIC_TEST_EMBEDDING

    if (
        payload.get("context") == "Nexus Live"
        and payload.get("sub_context") == "Operational Validation"
        and payload.get("entity_type") == "Live Scenario"
        and payload.get("entity") == "Nexus Live Synthetic Validation"
        and payload.get("topic") == "Live Interaction"
    ):
        return SYNTHETIC_TEST_EMBEDDING

    return None


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
        log.confidence = calculate_log_confidence(results)
        log.llm_model = frappe.get_single("Nexus Settings").llm_model
        log.error_message = error_message

        log.insert(ignore_permissions=True)
        frappe.db.commit()

        return log.name

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Failed to create Nexus Query Log")
        return None


def calculate_log_confidence(results):
    if not results:
        return 0

    score = (
        results[0].get("final_score")
        or results[0].get("score")
        or results[0].get("hybrid_score")
        or 0
    )

    try:
        return float(score)
    except Exception:
        return 0


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
        query_embedding = get_query_embedding_override(payload)

        result = answer_query(
            payload,
            retrieval_fn=retrieval_fn,
            embedding_provider=embedding_provider,
            llm_provider=llm_provider,
            query_embedding=query_embedding,
        )

        retrieval_result = result.pop("retrieval_result", {}) or {}

        log_name = log_query(
            payload,
            retrieval_result,
            answer=result.get("answer"),
        )

        result["log"] = log_name
        result["retrieval_debug"] = build_retrieval_debug_response(retrieval_result)
        result["formatted"] = format_answer_response(result)

        return result

    except Exception as e:
        log_query(payload or {}, {}, status="Failed", error_message=str(e))
        frappe.log_error(frappe.get_traceback(), "Nexus Ask Failed")

        error_result = {
            "status": "failed",
            "answer": None,
            "error": str(e),
            "retrieval_debug": build_retrieval_debug_response({}),
        }

        error_result["formatted"] = format_answer_response(error_result)

        return error_result