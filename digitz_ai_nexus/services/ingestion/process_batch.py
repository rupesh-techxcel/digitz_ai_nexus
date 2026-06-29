import frappe
from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source


def process_pending_nexy_sources():
    names = frappe.db.sql("""
        SELECT name FROM `tabNexus Knowledge Source`
        WHERE processing_status IN ('Failed', 'Pending')
        AND context = 'NEXUS AI COMMERCIAL'
        AND sub_context = 'Nexy Companion'
        ORDER BY name
    """, pluck="name")

    results = []
    for name in names:
        r = process_knowledge_source(name)
        frappe.db.commit()
        results.append({
            "name": name,
            "embedding_status": r.get("embedding_status"),
            "chunk_count": r.get("chunk_count"),
            "retrieval_ready": r.get("retrieval_ready"),
        })

    return results


def sync_nexy_retrieval_ready():
    """Sync retrieval_ready on all already-validated Nexy Companion sources."""
    from digitz_ai_nexus.api.nexus_knowledge_studio import (
        _sync_source_retrieval_ready_from_answer_approvals,
    )

    names = frappe.db.sql("""
        SELECT name FROM `tabNexus Knowledge Source`
        WHERE sub_context = 'Nexy Companion'
        AND context = 'NEXUS AI COMMERCIAL'
        AND processing_status = 'Processed'
        AND embedding_status = 'Completed'
        AND status = 'Published'
        ORDER BY name
    """, pluck="name")

    results = []
    for name in names:
        r = _sync_source_retrieval_ready_from_answer_approvals(name)
        frappe.db.commit()
        results.append({"name": name, "retrieval_ready": r.get("retrieval_ready", 0)})

    return results


def govern_nexy_sources():
    """
    Run the full governance chain on all Nexy Companion sources:
    1. validate_knowledge_source — content validation + validation_status
    2. validate_source_questions_with_llm — LLM auto-approves high-confidence questions
    3. bulk_approve_source_answers — approves remaining answers
    4. _sync_source_retrieval_ready — sets retrieval_ready=1 when all conditions met
    """
    from digitz_ai_nexus.api.nexus_knowledge_studio import (
        validate_knowledge_source,
        validate_source_questions_with_llm,
        bulk_approve_source_answers,
        _sync_source_retrieval_ready_from_answer_approvals,
    )

    names = frappe.db.sql("""
        SELECT name FROM `tabNexus Knowledge Source`
        WHERE sub_context = 'Nexy Companion'
        AND context = 'NEXUS AI COMMERCIAL'
        AND processing_status = 'Processed'
        AND embedding_status = 'Completed'
        ORDER BY name
    """, pluck="name")

    summary = []
    for name in names:
        row = {"name": name}

        # Step 1 — content validation
        v = validate_knowledge_source(name)
        row["validation"] = v.get("success")
        row["validation_confidence"] = v.get("confidence")
        frappe.db.commit()

        # Step 2 — LLM validates auto-generated questions
        q = validate_source_questions_with_llm(name)
        row["llm_auto_approved"] = q.get("auto_approved_count", 0)
        row["llm_pending"] = q.get("pending_count", 0)
        frappe.db.commit()

        # Step 3 — bulk approve any remaining pending answers
        a = bulk_approve_source_answers(name)
        row["bulk_approved"] = a.get("approved_count", 0)
        frappe.db.commit()

        # Step 4 — explicit sync (bulk_approve_source_answers skips sync when no pending)
        sync = _sync_source_retrieval_ready_from_answer_approvals(name)
        frappe.db.commit()
        row["retrieval_ready"] = sync.get("retrieval_ready", 0)

        summary.append(row)

    return summary
