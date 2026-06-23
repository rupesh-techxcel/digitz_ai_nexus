"""
Full lifecycle refresh for the NEXUS AI Public Chat Knowledge source.

Steps:
  1. Insert / update the source from the md file and process it
     (chunking + embeddings + LLM User Question index entries)
  2. Approve all User Question index entries (bulk approve)
  3. Build question correlations across all approved User Question entries
  4. Validate the source (LLM confidence-scored test query)
  5. Publish the source (activate chunks, set retrieval_ready=1)

Run via:
  bench --site digitz_ai_nexus_staging.site execute \
    digitz_ai_nexus.devtools.refresh_nexus_public_knowledge.run
"""

import frappe

SOURCE_TITLE = "NEXUS AI Public Chat Knowledge"


def _step(label, fn, *args, **kwargs):
    print(f"\n>>> {label}")
    try:
        result = fn(*args, **kwargs)
        print(f"    OK: {result}")
        return result, None
    except Exception as exc:
        print(f"    FAILED: {exc}")
        return None, str(exc)


def run():
    # ── Step 1: insert / update + process ────────────────────────────────────
    from digitz_ai_nexus.devtools.insert_nexus_ai_public_knowledge import insert_or_update

    insert_result, err = _step("Insert / update + process", insert_or_update, 1)
    if err:
        return {"status": "FAILED", "step": "insert_or_update", "error": err}

    source_name = insert_result.get("source") or SOURCE_TITLE
    print(f"    Source: {source_name}")
    print(f"    Chunks: {insert_result.get('chunk_count')}")
    print(f"    Processing status: {insert_result.get('processing_status')}")
    print(f"    Embedding status: {insert_result.get('embedding_status')}")

    # ── Step 2: approve all User Question index entries ───────────────────────
    from digitz_ai_nexus.api.nexus_knowledge_studio import bulk_approve_source_answers

    approve_result, err = _step(
        "Bulk approve User Question index entries",
        bulk_approve_source_answers,
        source_name,
    )
    if err:
        print(f"    WARNING: approve step failed — {err}")

    # ── Step 3: build question correlations ───────────────────────────────────
    from digitz_ai_nexus.services.question_correlation import build_question_correlations_for_source

    corr_result, err = _step(
        "Build question correlations",
        build_question_correlations_for_source,
        source_name,
    )
    if err:
        print(f"    WARNING: correlation step failed — {err}")

    # ── Step 4: validate ──────────────────────────────────────────────────────
    from digitz_ai_nexus.api.nexus_knowledge_studio import validate_knowledge_source

    val_result, err = _step("Validate source", validate_knowledge_source, source_name)
    if err:
        print(f"    WARNING: validation failed — {err}")

    # ── Step 5: publish ───────────────────────────────────────────────────────
    from digitz_ai_nexus.api.nexus_knowledge_studio import publish_knowledge_source

    pub_result, err = _step("Publish source", publish_knowledge_source, source_name)
    if err:
        print(f"    WARNING: publish failed — {err}")

    # ── Final status ──────────────────────────────────────────────────────────
    refreshed = frappe.get_doc("Nexus Knowledge Source", source_name)
    print("\n" + "=" * 60)
    print(f"  Source            : {source_name}")
    print(f"  Status            : {refreshed.get('status')}")
    print(f"  Processing status : {refreshed.get('processing_status')}")
    print(f"  Embedding status  : {refreshed.get('embedding_status')}")
    print(f"  Validation status : {refreshed.get('validation_status')}")
    print(f"  Chunk count       : {refreshed.get('chunk_count')}")
    print(f"  Active chunks     : {refreshed.get('active_chunk_count')}")
    print(f"  Retrieval ready   : {refreshed.get('retrieval_ready')}")
    print(f"  Correlations      : {(corr_result or {}).get('created', 'N/A')}")
    print("=" * 60)

    return {
        "source": source_name,
        "status": refreshed.get("status"),
        "retrieval_ready": refreshed.get("retrieval_ready"),
        "chunk_count": refreshed.get("chunk_count"),
        "active_chunk_count": refreshed.get("active_chunk_count"),
        "correlations_created": (corr_result or {}).get("created"),
        "validation": (val_result or {}).get("message"),
        "publish": (pub_result or {}).get("message"),
    }
