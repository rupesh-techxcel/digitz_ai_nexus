# Copyright (c) 2026, DIGITZ
# For license information, please see license.txt

import frappe


def normalize_text(value):
    return (value or "").strip()


def normalize_key(value):
    return (value or "").strip().lower()


def unique_keep_order(values):
    seen = set()
    result = []

    for value in values:
        clean_value = normalize_text(value)
        key = normalize_key(clean_value)

        if not clean_value or key in seen:
            continue

        seen.add(key)
        result.append(clean_value)

    return result


def get_enabled_business_keywords():
    """
    Reads Nexus Business Keyword records.
    Safe when the DocType exists but has no records.
    """

    if not frappe.db.exists("DocType", "Nexus Business Keyword"):
        return []

    return frappe.get_all(
        "Nexus Business Keyword",
        filters={"enabled": 1},
        fields=[
            "keyword",
            "synonyms",
            "priority_level",
            "category",
        ],
        limit_page_length=500,
    ) or []


def get_keyword_terms(row):
    terms = []

    keyword = row.get("keyword")
    if keyword:
        terms.append(keyword)

    synonyms = row.get("synonyms") or ""
    for line in synonyms.splitlines():
        line = line.strip()
        if line:
            terms.append(line)

    return unique_keep_order(terms)


def expand_from_business_keywords(query):
    """
    Expands query using configured business keywords and synonyms.

    Example:
    Query: stock pricing issue
    Keyword/Synonym Records:
        Valuation Rate → synonyms: stock pricing, incoming rate, outgoing rate

    Output:
        stock pricing issue
        Valuation Rate
        incoming rate
        outgoing rate
    """

    query_l = normalize_key(query)
    expansions = []

    if not query_l:
        return expansions

    rows = get_enabled_business_keywords()

    for row in rows:
        terms = get_keyword_terms(row)

        matched = False
        for term in terms:
            term_l = normalize_key(term)

            if term_l and term_l in query_l:
                matched = True
                break

        if not matched:
            continue

        expansions.extend(terms)

    return unique_keep_order(expansions)


def expand_query(query, max_variants=8):
    """
    Main query expansion function.

    Safe behavior:
    - If no seed exists, returns only the original query.
    - If seed exists, returns original query + matching business keyword variants.
    """

    original = normalize_text(query)

    if not original:
        return []

    variants = [original]

    keyword_variants = expand_from_business_keywords(original)
    variants.extend(keyword_variants)

    variants = unique_keep_order(variants)

    if max_variants and len(variants) > max_variants:
        variants = variants[:max_variants]

    return variants