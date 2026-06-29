"""
Batch: generate + run test cases for all published sources that have none.
"""
import frappe

from digitz_ai_nexus.api.nexus_knowledge_studio import (
    generate_source_test_cases,
    run_source_test_cases,
)

# All published sources with 0 test cases
sources = frappe.db.sql("""
    SELECT ks.name
    FROM `tabNexus Knowledge Source` ks
    WHERE ks.status = 'Published'
      AND ks.retrieval_ready = 1
      AND ks.active_chunk_count > 0
      AND (
          SELECT COUNT(*) FROM `tabNexus Knowledge Test Case` tc
          WHERE tc.knowledge_source = ks.name
      ) = 0
    ORDER BY ks.name
""", pluck="name")

print(f"\nSources needing test cases: {len(sources)}")
print("=" * 64)

results = []
for i, src_name in enumerate(sources, 1):
    print(f"\n[{i}/{len(sources)}] {src_name}")

    # Generate
    try:
        gen = generate_source_test_cases(
            src_name,
            test_count=8,
            use_case="Q&A",
            include_boundary_tests=1,
            include_followup_tests=1,
            auto_enable=1,
            replace_existing=1,
        )
        frappe.db.commit()
        created = gen.get("created_count", len(gen.get("created", [])))
        print(f"  Generated: {created} test cases")
    except Exception as exc:
        print(f"  GENERATE FAILED: {exc}")
        results.append({"source": src_name, "generated": 0, "passed": 0, "failed": 0, "error": str(exc)})
        continue

    if created == 0:
        print("  No test cases generated — skipping run")
        results.append({"source": src_name, "generated": 0, "passed": 0, "failed": 0})
        continue

    # Run
    try:
        run = run_source_test_cases(src_name)
        frappe.db.commit()
        passed = run.get("passed", 0)
        failed = run.get("failed", 0)
        total = run.get("total", 0)
        print(f"  Tests:     {passed}/{total} passed | {failed} failed")
        results.append({"source": src_name, "generated": created, "passed": passed, "failed": failed, "total": total})
    except Exception as exc:
        print(f"  RUN FAILED: {exc}")
        results.append({"source": src_name, "generated": created, "passed": 0, "failed": 0, "error": str(exc)})

# Summary
print("\n" + "=" * 64)
print("SUMMARY")
print("=" * 64)
total_pass = sum(r["passed"] for r in results)
total_fail = sum(r["failed"] for r in results)
total_gen = sum(r["generated"] for r in results)
no_cases = sum(1 for r in results if r["generated"] == 0)

print(f"  Sources processed : {len(results)}")
print(f"  Test cases created: {total_gen}")
print(f"  No cases generated: {no_cases}")
print(f"  Tests passed      : {total_pass}")
print(f"  Tests failed      : {total_fail}")

if total_fail > 0:
    print("\nFailed sources:")
    for r in results:
        if r["failed"] > 0:
            print(f"  {r['source']}: {r['failed']} failed")

print("=" * 64)
