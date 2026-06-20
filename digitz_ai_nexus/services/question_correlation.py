import re

import frappe


INDEX_DOCTYPE = "Nexus Knowledge Index Entry"
CORRELATION_DOCTYPE = "Nexus Question Correlation"
QUESTION_ENTRY_TYPE = "User Question"

STOP_WORDS = {
    "a", "an", "and", "are", "about", "can", "do", "does", "for", "from",
    "how", "i", "in", "is", "it", "me", "of", "on", "or", "should", "the",
    "to", "what", "when", "where", "which", "with", "you",
}

QUESTION_FIELDS = [
    "name",
    "canonical_text",
    "knowledge_source",
    "knowledge_unit",
    "knowledge_chunk",
    "tenant",
    "business_unit",
    "project",
    "context",
    "sub_context",
    "entity_type",
    "entity",
    "topic",
    "context_path",
    "access_policy",
    "sensitivity",
    "priority",
]


def has_question_correlation_doctype():
    return frappe.db.exists("DocType", CORRELATION_DOCTYPE)


def normalize_question(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def tokenize(value):
    return {
        token
        for token in re.findall(r"[a-z0-9]+", normalize_question(value))
        if len(token) > 2 and token not in STOP_WORDS
    }


def jaccard_score(left, right):
    if not left or not right:
        return 0.0

    overlap = len(left.intersection(right))
    union = len(left.union(right))
    return overlap / union if union else 0.0


def same_value(left, right, fieldname):
    left_value = (left.get(fieldname) or "").strip()
    right_value = (right.get(fieldname) or "").strip()
    return bool(left_value and right_value and left_value == right_value)


def compatible_scope(left, right):
    for fieldname in ("tenant", "access_policy"):
        left_value = (left.get(fieldname) or "").strip()
        right_value = (right.get(fieldname) or "").strip()
        if left_value and right_value and left_value != right_value:
            return False

    return True


def score_question_pair(source, candidate):
    if source.get("name") == candidate.get("name"):
        return 0.0, None

    source_text = normalize_question(source.get("canonical_text"))
    candidate_text = normalize_question(candidate.get("canonical_text"))
    if not source_text or not candidate_text or source_text == candidate_text:
        return 0.0, None

    if not compatible_scope(source, candidate):
        return 0.0, None

    score = 0.0
    correlation_type = "Semantic Similarity"

    if same_value(source, candidate, "knowledge_chunk"):
        score += 0.65
        correlation_type = "Same Chunk"
    elif same_value(source, candidate, "context_path"):
        score += 0.34
        correlation_type = "Same Context"
    elif same_value(source, candidate, "topic"):
        score += 0.28
        correlation_type = "Same Topic"

    for fieldname, weight in (
        ("context", 0.12),
        ("sub_context", 0.10),
        ("entity", 0.10),
        ("topic", 0.10),
        ("business_unit", 0.06),
        ("project", 0.04),
    ):
        if same_value(source, candidate, fieldname):
            score += weight

    score += min(jaccard_score(tokenize(source_text), tokenize(candidate_text)) * 0.45, 0.45)

    return min(score, 1.0), correlation_type


def get_active_source_questions(source_name):
    if not source_name or not frappe.db.exists("DocType", INDEX_DOCTYPE):
        return []

    filters = {
        "knowledge_source": source_name,
        "entry_type": QUESTION_ENTRY_TYPE,
        "status": "Active",
        "disabled": 0,
    }

    if frappe.get_meta(INDEX_DOCTYPE).has_field("answer_review_status"):
        filters["answer_review_status"] = "Approved"

    return frappe.get_all(
        INDEX_DOCTYPE,
        filters=filters,
        fields=QUESTION_FIELDS,
        limit_page_length=10000,
    )


def clear_source_correlations(source_name):
    names = frappe.get_all(
        CORRELATION_DOCTYPE,
        filters={"knowledge_source": source_name},
        pluck="name",
        limit_page_length=10000,
    )

    for name in names:
        frappe.delete_doc(CORRELATION_DOCTYPE, name, ignore_permissions=True)

    return len(names)


def insert_correlation(source, related, score, correlation_type):
    doc = frappe.new_doc(CORRELATION_DOCTYPE)
    doc.source_question = source.get("name")
    doc.related_question = related.get("name")
    doc.question_text = related.get("canonical_text")
    doc.correlation_type = correlation_type
    doc.correlation_score = round(score, 4)
    doc.status = "Active"
    doc.disabled = 0

    for fieldname in (
        "tenant",
        "business_unit",
        "project",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
        "context_path",
        "access_policy",
        "sensitivity",
        "knowledge_source",
        "knowledge_unit",
        "knowledge_chunk",
    ):
        doc.set(fieldname, related.get(fieldname))

    doc.generation_notes = "Generated from approved User Question index entries during source processing."
    doc.insert(ignore_permissions=True)
    return doc.name


def build_question_correlations_for_source(source_name, max_related=5, minimum_score=0.35):
    if not has_question_correlation_doctype():
        return {"created": 0, "cleared": 0, "skipped": True, "reason": "DocType not found"}

    questions = get_active_source_questions(source_name)
    cleared = clear_source_correlations(source_name)

    if len(questions) < 2:
        return {"created": 0, "cleared": cleared, "skipped": True, "reason": "Not enough approved questions"}

    created = 0

    for source in questions:
        scored = []

        for candidate in questions:
            score, correlation_type = score_question_pair(source, candidate)
            if score >= minimum_score:
                scored.append((score, correlation_type, candidate))

        scored.sort(key=lambda row: row[0], reverse=True)

        for score, correlation_type, candidate in scored[:max_related]:
            try:
                insert_correlation(source, candidate, score, correlation_type)
                created += 1
            except frappe.UniqueValidationError:
                continue

    frappe.db.commit()
    return {"created": created, "cleared": cleared, "skipped": False}


def _chunk_name(row):
    if hasattr(row, "get"):
        return row.get("chunk") or row.get("name") or row.get("knowledge_chunk")
    return None


def _allowed_filter_values(values):
    return [value for value in (values or []) if value]


def _base_question_filters(payload, chunk_names):
    filters = {
        "entry_type": QUESTION_ENTRY_TYPE,
        "status": "Active",
        "disabled": 0,
        "knowledge_chunk": ["in", chunk_names],
    }

    tenant = (payload or {}).get("tenant")
    if tenant:
        filters["tenant"] = tenant

    allowed_policies = _allowed_filter_values((payload or {}).get("allowed_access_policies"))
    if allowed_policies:
        filters["access_policy"] = ["in", allowed_policies]

    if frappe.get_meta(INDEX_DOCTYPE).has_field("answer_review_status"):
        filters["answer_review_status"] = "Approved"

    return filters


def _related_question_filters(payload, related_names):
    filters = {
        "name": ["in", related_names],
        "entry_type": QUESTION_ENTRY_TYPE,
        "status": "Active",
        "disabled": 0,
    }

    tenant = (payload or {}).get("tenant")
    if tenant:
        filters["tenant"] = tenant

    allowed_policies = _allowed_filter_values((payload or {}).get("allowed_access_policies"))
    if allowed_policies:
        filters["access_policy"] = ["in", allowed_policies]

    if frappe.get_meta(INDEX_DOCTYPE).has_field("answer_review_status"):
        filters["answer_review_status"] = "Approved"

    return filters


_DEDUP_SIMILARITY_THRESHOLD = 0.75


def _append_question(result, seen, seen_tokens, query_text, question, score=0.0, correlation_type=None):
    normalized = normalize_question(question)
    if not normalized or normalized == query_text or normalized in seen:
        return

    tokens = tokenize(question)
    for existing in seen_tokens:
        if jaccard_score(tokens, existing) >= _DEDUP_SIMILARITY_THRESHOLD:
            return

    seen.add(normalized)
    seen_tokens.append(tokens)
    result.append({
        "question": question,
        "correlation_score": score,
        "correlation_type": correlation_type,
    })


def get_correlated_questions_for_answer(payload, chunks, limit=5):
    if not has_question_correlation_doctype() or not frappe.db.exists("DocType", INDEX_DOCTYPE):
        return []

    chunk_names = sorted({
        chunk_name for chunk_name in (_chunk_name(row) for row in (chunks or [])) if chunk_name
    })
    if not chunk_names:
        return []

    base_questions = frappe.get_all(
        INDEX_DOCTYPE,
        filters=_base_question_filters(payload, chunk_names),
        fields=["name", "canonical_text", "priority"],
        limit_page_length=100,
    )
    if not base_questions:
        return []

    base_names = [row.name for row in base_questions]
    correlations = frappe.get_all(
        CORRELATION_DOCTYPE,
        filters={
            "source_question": ["in", base_names],
            "status": "Active",
            "disabled": 0,
        },
        fields=["related_question", "correlation_score", "correlation_type"],
        order_by="correlation_score desc",
        limit_page_length=100,
    )

    result = []
    seen = set()
    seen_tokens = []
    query_text = normalize_question((payload or {}).get("query"))

    if correlations:
        related_names = [row.related_question for row in correlations if row.related_question]
        related_entries = {
            row.name: row
            for row in frappe.get_all(
                INDEX_DOCTYPE,
                filters=_related_question_filters(payload, related_names),
                fields=["name", "canonical_text"],
                limit_page_length=100,
            )
        }

        for row in correlations:
            related = related_entries.get(row.related_question)
            if not related:
                continue

            _append_question(
                result,
                seen,
                seen_tokens,
                query_text,
                related.canonical_text,
                score=row.correlation_score,
                correlation_type=row.correlation_type,
            )
            if len(result) >= limit:
                return result

    for row in sorted(base_questions, key=lambda item: item.get("priority") or 0, reverse=True):
        _append_question(
            result,
            seen,
            seen_tokens,
            query_text,
            row.canonical_text,
            score=0.25,
            correlation_type="Same Chunk",
        )
        if len(result) >= limit:
            break

    return result
