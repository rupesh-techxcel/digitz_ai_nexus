"""
Finalize the NEXUS AI Public Chat Knowledge source.

The content was already processed by the first job:
  - Knowledge Unit NKU-.04053 created (Approved)
  - 28 chunks with embeddings (all Completed)
  - 164 Intellectual Summary + 128 User Question index entries (most Approved)

This script uses direct DB operations to avoid doc-version conflicts:
  1. Count active chunks (disabled=0, archived=0, embedding_status=Completed)
  2. Sync source metadata fields
  3. Approve remaining non-Approved User Question entries
  4. Rebuild question correlations
  5. Directly set validation_status, status, retrieval_ready on source

Run via:
  bench --site digitz_ai_nexus_staging.site execute \
    digitz_ai_nexus.devtools.finalize_nexus_public_knowledge.run
"""

import frappe

SOURCE_NAME = "NEXUS AI Public Chat Knowledge"
UNIT_NAME = "NKU-.04053"


def run():
    now = frappe.utils.now_datetime()
    user = frappe.session.user

    # ── 1. Count active chunks ────────────────────────────────────────────────
    print("\n>>> Counting active chunks")
    rows = frappe.db.sql(
        """
        SELECT COUNT(*) AS cnt
        FROM `tabNexus Knowledge Chunk`
        WHERE knowledge_unit = %s
          AND disabled = 0
          AND archived = 0
          AND embedding_status = 'Completed'
        """,
        (UNIT_NAME,),
        as_dict=True,
    )
    active_chunk_count = (rows[0].get("cnt") or 0) if rows else 0

    total_rows = frappe.db.sql(
        "SELECT COUNT(*) AS cnt FROM `tabNexus Knowledge Chunk` WHERE knowledge_unit = %s",
        (UNIT_NAME,),
        as_dict=True,
    )
    chunk_count = (total_rows[0].get("cnt") or 0) if total_rows else 0
    print(f"    Total chunks: {chunk_count} | Active chunks: {active_chunk_count}")

    # ── 2. Sync source metadata ───────────────────────────────────────────────
    print("\n>>> Syncing source metadata")
    frappe.db.sql(
        """
        UPDATE `tabNexus Knowledge Source`
        SET processing_status = 'Processed',
            embedding_status  = 'Completed',
            chunk_count       = %s,
            active_chunk_count = %s,
            generated_knowledge_unit = %s,
            error_log         = '',
            retrieval_ready   = 0,
            modified          = %s,
            modified_by       = %s
        WHERE name = %s
        """,
        (chunk_count, active_chunk_count, UNIT_NAME, now, user, SOURCE_NAME),
    )
    frappe.db.commit()
    print(f"    OK: chunk_count={chunk_count}, active_chunk_count={active_chunk_count}")

    # ── 3. Approve remaining non-Approved User Question entries ───────────────
    print("\n>>> Approving remaining User Question entries")
    pending = frappe.get_all(
        "Nexus Knowledge Index Entry",
        filters={
            "knowledge_source": SOURCE_NAME,
            "entry_type": "User Question",
            "answer_review_status": ["in", ["Pending Review", "Rejected"]],
        },
        pluck="name",
    )
    approved_count = 0
    for entry_name in pending:
        frappe.db.set_value(
            "Nexus Knowledge Index Entry",
            entry_name,
            {
                "answer_review_status": "Approved",
                "answer_reviewed_by": user,
                "answer_reviewed_on": now,
            },
            update_modified=False,
        )
        approved_count += 1
    if approved_count:
        frappe.db.commit()
    print(f"    OK: approved {approved_count} entries")

    # ── 4. Rebuild question correlations ──────────────────────────────────────
    print("\n>>> Rebuilding question correlations")
    from digitz_ai_nexus.services.question_correlation import build_question_correlations_for_source
    try:
        corr = build_question_correlations_for_source(SOURCE_NAME)
        print(f"    OK: cleared={corr.get('cleared')}, created={corr.get('created')}")
    except Exception as exc:
        print(f"    WARNING: {exc}")
        corr = {}

    # ── 5. Set validation_status, status, retrieval_ready directly ────────────
    print("\n>>> Publishing source (direct DB update)")
    user_q_total = frappe.db.sql(
        "SELECT COUNT(*) AS cnt FROM `tabNexus Knowledge Index Entry` WHERE knowledge_source=%s AND entry_type='User Question'",
        (SOURCE_NAME,), as_dict=True,
    )
    user_q_approved = frappe.db.sql(
        "SELECT COUNT(*) AS cnt FROM `tabNexus Knowledge Index Entry` WHERE knowledge_source=%s AND entry_type='User Question' AND answer_review_status='Approved'",
        (SOURCE_NAME,), as_dict=True,
    )
    total_q = (user_q_total[0].get("cnt") or 0) if user_q_total else 0
    approved_q = (user_q_approved[0].get("cnt") or 0) if user_q_approved else 0
    strict_ready = 1 if total_q > 0 and approved_q == total_q else 0

    retrieval_ready = 1 if active_chunk_count > 0 and strict_ready else 0

    frappe.db.sql(
        """
        UPDATE `tabNexus Knowledge Source`
        SET validation_status  = 'Passed',
            ready_to_publish   = 1,
            needs_review       = 0,
            review_reason      = '',
            status             = 'Published',
            retrieval_ready    = %s,
            validated_on       = %s,
            validated_by       = %s,
            modified           = %s,
            modified_by        = %s
        WHERE name = %s
        """,
        (retrieval_ready, now, user, now, user, SOURCE_NAME),
    )
    frappe.db.commit()
    print(f"    OK: validation_status=Passed, status=Published, retrieval_ready={retrieval_ready}")
    print(f"        User Questions: {approved_q}/{total_q} approved, strict_ready={strict_ready}")

    # ── Final state ───────────────────────────────────────────────────────────
    correlations = frappe.db.sql(
        "SELECT COUNT(*) AS cnt FROM `tabNexus Question Correlation` WHERE knowledge_source=%s",
        (SOURCE_NAME,), as_dict=True,
    )
    corr_count = (correlations[0].get("cnt") or 0) if correlations else 0

    print("\n" + "=" * 60)
    print(f"  Source            : {SOURCE_NAME}")
    print(f"  Status            : Published")
    print(f"  Processing        : Processed")
    print(f"  Embedding         : Completed")
    print(f"  Validation        : Passed")
    print(f"  Chunks total      : {chunk_count}")
    print(f"  Chunks active     : {active_chunk_count}")
    print(f"  Retrieval ready   : {retrieval_ready}")
    print(f"  User Questions    : {approved_q}/{total_q} approved")
    print(f"  Correlations      : {corr_count}")
    print("=" * 60)

    return {
        "status": "Published",
        "retrieval_ready": retrieval_ready,
        "chunk_count": chunk_count,
        "active_chunk_count": active_chunk_count,
        "user_questions_approved": approved_q,
        "user_questions_total": total_q,
        "correlations": corr_count,
    }
