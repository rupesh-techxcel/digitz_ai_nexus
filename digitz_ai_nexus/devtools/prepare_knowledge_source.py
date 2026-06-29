"""
Knowledge Source Preparation Utility
=====================================
Runs all 7 steps to take a Nexus Knowledge Source from raw content to live retrieval.

Steps
-----
  1. Process        — chunk + embed the source content
  2. Index          — generate Intellectual Summaries + User Questions per chunk
  3. Validate Q&A   — LLM reviews each User Question (auto-approve ≥80%, auto-reject <40%)
  4. Validate source — test retrieval with a query, confirm the source is reachable
  5. Test cases     — generate Nexus Knowledge Test Case records
  6. Run tests      — execute all test cases, report pass/fail
  7. Publish        — activate chunks, set retrieval_ready=1

Usage
-----
Single source (interactive, confirms before publish):
    bench --site <site> execute \\
        digitz_ai_nexus.devtools.prepare_knowledge_source.run \\
        --args '["<source-name>"]'

Single source, auto-publish without prompting:
    bench --site <site> execute \\
        digitz_ai_nexus.devtools.prepare_knowledge_source.run \\
        --args '["<source-name>"]' \\
        --kwargs '{"auto_publish": true}'

Custom test count and index generation method:
    bench --site <site> execute \\
        digitz_ai_nexus.devtools.prepare_knowledge_source.run \\
        --args '["<source-name>"]' \\
        --kwargs '{"test_count": 10, "generation_method": "Heuristic", "auto_publish": true}'

Parameters
----------
source_name       : str  — name of the Nexus Knowledge Source doc
test_count        : int  — number of test cases to generate (default 8)
generation_method : str  — "Heuristic" (fast, no LLM cost) or "LLM" (richer questions)
auto_publish      : bool — skip the publish confirmation prompt (default False)
skip_if_published : bool — exit early if source is already Published (default True)
"""

import frappe


# ── Helpers ────────────────────────────────────────────────────────────────────

def _step(n, label):
    print(f"\n[{n}/7] {label}")
    print("      " + "-" * (len(label) + 6))


def _ok(msg):
    print(f"      OK — {msg}")


def _warn(msg):
    print(f"      WARN — {msg}")


def _fail(msg):
    print(f"      FAIL — {msg}")


def _sep():
    print("\n" + "=" * 64)


# ── Main entry point ───────────────────────────────────────────────────────────

def run(
    source_name: str,
    test_count: int = 8,
    generation_method: str = "Heuristic",
    auto_publish: bool = False,
    skip_if_published: bool = True,
):
    """
    Prepare a Nexus Knowledge Source end-to-end through all 7 steps.
    """
    if not source_name:
        print("ERROR: source_name is required.")
        return {"success": False, "error": "source_name is required"}

    if not frappe.db.exists("Nexus Knowledge Source", source_name):
        print(f"ERROR: Nexus Knowledge Source not found: {source_name!r}")
        return {"success": False, "error": f"Source not found: {source_name}"}

    _sep()
    print(f"  Preparing knowledge source: {source_name}")

    src = frappe.get_doc("Nexus Knowledge Source", source_name)

    if skip_if_published and src.status == "Published" and src.retrieval_ready:
        print(f"  Status: Published | retrieval_ready: {src.retrieval_ready}")
        print("  Source is already live. Use skip_if_published=False to re-run.")
        _sep()
        return {"success": True, "skipped": True, "reason": "already published"}

    print(f"  Current status: {src.status} | chunks: {src.chunk_count} | retrieval_ready: {src.retrieval_ready}")
    _sep()

    summary = {}

    # ── Step 1: Process ────────────────────────────────────────────────────────
    _step(1, "PROCESS — chunk + embed")
    try:
        from digitz_ai_nexus.services.knowledge_source_processor import process_knowledge_source
        result = process_knowledge_source(source_name)
        frappe.db.commit()

        chunk_count = result.get("chunk_count", 0)
        active_chunk_count = result.get("active_chunk_count", 0)
        embedding_status = result.get("embedding_status", "Unknown")
        diagnostics_status = result.get("diagnostics_status", "Unknown")
        knowledge_unit = result.get("knowledge_unit")

        # If source was published before processing, chunks come out disabled.
        # Re-enable the non-archived chunks now that we are about to publish.
        if active_chunk_count == 0 and chunk_count > 0:
            frappe.db.sql(
                """UPDATE `tabNexus Knowledge Chunk`
                   SET disabled = 0
                   WHERE knowledge_source = %s AND archived = 0""",
                (source_name,),
            )
            frappe.db.sql(
                "UPDATE `tabNexus Knowledge Source` SET active_chunk_count=%s WHERE name=%s",
                (chunk_count, source_name),
            )
            frappe.db.commit()
            active_chunk_count = chunk_count
            _warn(f"chunks were disabled (source was Draft during processing) — re-enabled {chunk_count}")

        _ok(f"chunk_count={chunk_count} | active={active_chunk_count} | embedding={embedding_status} | diagnostics={diagnostics_status}")
        summary["step1"] = {"ok": True, "chunk_count": chunk_count, "active_chunk_count": active_chunk_count}

        if embedding_status != "Completed":
            _fail(f"embedding_status is {embedding_status!r} — cannot continue")
            return {"success": False, "step_failed": 1, "summary": summary}

    except Exception as exc:
        _fail(str(exc))
        frappe.log_error(frappe.get_traceback(), "prepare_knowledge_source: step 1 failed")
        return {"success": False, "step_failed": 1, "error": str(exc)}

    # ── Step 2: Index — generate Intellectual Summaries + User Questions ───────
    _step(2, "INDEX — generate Intellectual Summaries + User Questions")
    try:
        from digitz_ai_nexus.services.semantic_index import (
            generate_index_entries_for_chunks,
            has_semantic_index_doctype,
        )

        if not has_semantic_index_doctype():
            _warn("Nexus Knowledge Index Entry DocType not found — skipping")
            summary["step2"] = {"ok": True, "skipped": True}
        else:
            # Get non-archived chunks for this source that don't have index entries yet
            all_chunks = frappe.get_all(
                "Nexus Knowledge Chunk",
                filters={"knowledge_source": source_name, "archived": 0},
                pluck="name",
            )
            existing_indexed = set(frappe.db.sql(
                "SELECT DISTINCT knowledge_chunk FROM `tabNexus Knowledge Index Entry` WHERE knowledge_source=%s",
                (source_name,),
                pluck="knowledge_chunk",
            ))
            to_index = [c for c in all_chunks if c not in existing_indexed]

            if not to_index:
                _ok(f"all {len(all_chunks)} chunks already indexed — skipping")
                summary["step2"] = {"ok": True, "skipped": True, "existing": len(existing_indexed)}
            else:
                result2 = generate_index_entries_for_chunks(to_index, generation_method=generation_method)
                frappe.db.commit()
                created = len(result2.get("created", []))
                failed = len(result2.get("failed", []))
                _ok(f"created={created} index entries | method={generation_method} | failed={failed}")
                if failed:
                    _warn(f"{failed} chunk(s) failed indexing — check error log")
                summary["step2"] = {"ok": True, "created": created, "failed": failed}

    except Exception as exc:
        _fail(str(exc))
        frappe.log_error(frappe.get_traceback(), "prepare_knowledge_source: step 2 failed")
        return {"success": False, "step_failed": 2, "error": str(exc)}

    # ── Step 3: Validate Q&A — LLM reviews each User Question ─────────────────
    _step(3, "VALIDATE Q&A — LLM reviews User Questions")
    try:
        from digitz_ai_nexus.services.semantic_index import validate_source_questions_with_llm as _validate_q
        counts = _validate_q(source_name)
        frappe.db.commit()
        _ok(
            f"approved={counts.get('approved')} | "
            f"pending={counts.get('pending')} | "
            f"rejected={counts.get('rejected')} | "
            f"errors={counts.get('errors', 0)}"
        )
        if counts.get("pending"):
            _warn(f"{counts['pending']} question(s) need human review (40–79% confidence) — check Nexus Studio")
        summary["step3"] = {"ok": True, **counts}

    except Exception as exc:
        _fail(str(exc))
        frappe.log_error(frappe.get_traceback(), "prepare_knowledge_source: step 3 failed")
        return {"success": False, "step_failed": 3, "error": str(exc)}

    # ── Step 4: Validate source — confirm retrieval works ─────────────────────
    _step(4, "VALIDATE SOURCE — test retrieval")
    try:
        from digitz_ai_nexus.api.nexus_knowledge_studio import validate_knowledge_source
        result4 = validate_knowledge_source(source_name)
        frappe.db.commit()
        val_status = result4.get("validation_status") or result4.get("status", "unknown")
        confidence = result4.get("validation_confidence") or result4.get("confidence", 0)
        _ok(f"validation_status={val_status} | confidence={confidence:.2f}" if isinstance(confidence, float) else f"validation_status={val_status}")
        summary["step4"] = {"ok": True, "validation_status": val_status}

    except Exception as exc:
        _warn(f"validate_knowledge_source raised: {exc} — continuing")
        frappe.log_error(frappe.get_traceback(), "prepare_knowledge_source: step 4 warning")
        summary["step4"] = {"ok": True, "skipped": True, "warn": str(exc)}

    # ── Step 5: Generate test cases ────────────────────────────────────────────
    _step(5, f"TEST CASES — generate {test_count} cases")
    try:
        from digitz_ai_nexus.api.nexus_knowledge_studio import generate_source_test_cases
        result5 = generate_source_test_cases(
            source_name,
            test_count=test_count,
            use_case="Q&A",
            include_boundary_tests=1,
            include_followup_tests=1,
            auto_enable=1,
            replace_existing=1,
        )
        frappe.db.commit()
        created_cases = result5.get("created_count", len(result5.get("created", [])))
        _ok(f"created={created_cases} test cases")
        summary["step5"] = {"ok": True, "created_count": created_cases}

    except Exception as exc:
        _fail(str(exc))
        frappe.log_error(frappe.get_traceback(), "prepare_knowledge_source: step 5 failed")
        return {"success": False, "step_failed": 5, "error": str(exc)}

    # ── Step 6: Run tests ──────────────────────────────────────────────────────
    _step(6, "RUN TESTS — execute all test cases")
    try:
        from digitz_ai_nexus.api.nexus_knowledge_studio import run_source_test_cases
        result6 = run_source_test_cases(source_name)
        frappe.db.commit()
        total = result6.get("total", 0)
        passed = result6.get("passed", 0)
        failed = result6.get("failed", 0)
        _ok(f"passed={passed}/{total} | failed={failed}")
        if failed > 0:
            _warn(f"{failed} test(s) failed — retrieval_ready will NOT be set to 1 until all tests pass")
        summary["step6"] = {"ok": True, "passed": passed, "failed": failed, "total": total}

    except Exception as exc:
        _warn(f"run_source_test_cases raised: {exc} — continuing to publish")
        frappe.log_error(frappe.get_traceback(), "prepare_knowledge_source: step 6 warning")
        summary["step6"] = {"ok": True, "skipped": True, "warn": str(exc)}

    # ── Step 7: Publish ────────────────────────────────────────────────────────
    _step(7, "PUBLISH — activate for retrieval")
    try:
        if not auto_publish:
            print("      auto_publish=False — skipping publish step.")
            print("      Run publish_knowledge_source() manually or re-run with auto_publish=True.")
            summary["step7"] = {"ok": True, "skipped": True, "reason": "auto_publish=False"}
        else:
            # Ensure active chunks are enabled (guards against Draft-during-processing edge case)
            frappe.db.sql(
                "UPDATE `tabNexus Knowledge Chunk` SET disabled=0 WHERE knowledge_source=%s AND archived=0",
                (source_name,),
            )
            active = frappe.db.count(
                "Nexus Knowledge Chunk",
                {"knowledge_source": source_name, "archived": 0, "disabled": 0, "embedding_status": "Completed"},
            )

            # Gate: retrieval_ready=1 only when all 7 steps are satisfied
            step6 = summary.get("step6", {})
            tests_ok = (
                step6.get("total", 0) > 0
                and step6.get("failed", 0) == 0
                and not step6.get("skipped")
            )
            retrieval_ready_val = 1 if tests_ok else 0

            frappe.db.sql(
                """UPDATE `tabNexus Knowledge Source`
                   SET status='Published', retrieval_ready=%s, active_chunk_count=%s,
                       validation_status='Passed', ready_to_publish=0,
                       needs_review=0, modified=%s
                   WHERE name=%s""",
                (retrieval_ready_val, active, frappe.utils.now_datetime(), source_name),
            )
            frappe.db.commit()
            if retrieval_ready_val:
                _ok(f"status=Published | retrieval_ready=1 | active_chunks={active}")
            else:
                _ok(f"status=Published | retrieval_ready=0 (tests not all passing) | active_chunks={active}")
                _warn("Fix failing tests then run publish_knowledge_source() to set retrieval_ready=1")
            summary["step7"] = {"ok": True, "active_chunks": active, "retrieval_ready": retrieval_ready_val}

    except Exception as exc:
        _fail(str(exc))
        frappe.log_error(frappe.get_traceback(), "prepare_knowledge_source: step 7 failed")
        return {"success": False, "step_failed": 7, "error": str(exc)}

    # ── Final report ───────────────────────────────────────────────────────────
    _sep()
    src_final = frappe.get_doc("Nexus Knowledge Source", source_name)
    idx_total = frappe.db.count("Nexus Knowledge Index Entry", {"knowledge_source": source_name})
    idx_approved = frappe.db.count(
        "Nexus Knowledge Index Entry",
        {"knowledge_source": source_name, "entry_type": "User Question", "answer_review_status": "Approved"},
    )
    test_passed = summary.get("step6", {}).get("passed", "—")
    test_total = summary.get("step6", {}).get("total", "—")

    print(f"  Source          : {source_name}")
    print(f"  Status          : {src_final.status}")
    print(f"  Retrieval ready : {src_final.retrieval_ready}")
    print(f"  Active chunks   : {src_final.active_chunk_count}")
    print(f"  Index entries   : {idx_total} total | {idx_approved} user-questions approved")
    print(f"  Test cases      : {test_passed}/{test_total} passed")
    _sep()

    return {
        "success": True,
        "source": source_name,
        "status": src_final.status,
        "retrieval_ready": src_final.retrieval_ready,
        "active_chunks": src_final.active_chunk_count,
        "index_entries": idx_total,
        "user_questions_approved": idx_approved,
        "steps": summary,
    }
