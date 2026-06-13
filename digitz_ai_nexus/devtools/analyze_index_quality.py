"""Analyze the quality and diversity of generated index entries."""
import frappe


def run():
    rows = frappe.db.sql(
        """SELECT entry_type, canonical_text, knowledge_source
           FROM `tabNexus Knowledge Index Entry`
           WHERE entry_type = 'User Question'
           ORDER BY knowledge_source, canonical_text
           LIMIT 60""",
        as_dict=True,
    )

    print(f"=== Sample User Questions ({len(rows)} rows) ===")
    for r in rows:
        print(f"  [{r.knowledge_source[:40]}] {r.canonical_text}")

    # Check uniqueness
    all_q = frappe.db.sql(
        "SELECT canonical_text FROM `tabNexus Knowledge Index Entry` WHERE entry_type = 'User Question'",
        pluck="canonical_text",
    )
    unique = set(all_q)
    print(f"\n=== Uniqueness ===")
    print(f"  Total User Questions: {len(all_q)}")
    print(f"  Unique questions:     {len(unique)}")
    print(f"  Duplicates:           {len(all_q) - len(unique)}")

    # Top repeated questions
    from collections import Counter
    counts = Counter(all_q)
    repeated = [(q, c) for q, c in counts.most_common(15) if c > 1]
    if repeated:
        print(f"\n=== Most Repeated Questions ===")
        for q, c in repeated:
            print(f"  (x{c}) {q}")

    # Intellectual summaries sample
    summaries = frappe.db.sql(
        """SELECT DISTINCT canonical_text FROM `tabNexus Knowledge Index Entry`
           WHERE entry_type = 'Intellectual Summary'
           LIMIT 20""",
        pluck="canonical_text",
    )
    print(f"\n=== Sample Intellectual Summaries ===")
    for s in summaries:
        print(f"  {s}")

    # Check answer_review_status breakdown
    review_rows = frappe.db.sql(
        """SELECT entry_type, answer_review_status, COUNT(*) as cnt
           FROM `tabNexus Knowledge Index Entry`
           GROUP BY entry_type, answer_review_status""",
        as_dict=True,
    )
    print(f"\n=== answer_review_status breakdown ===")
    for r in review_rows:
        print(f"  type={r.entry_type} status={r.answer_review_status} count={r.cnt}")
