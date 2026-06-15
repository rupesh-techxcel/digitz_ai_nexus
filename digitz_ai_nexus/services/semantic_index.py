import hashlib
import json
import re

import frappe

from digitz_ai_nexus.engine.llm import generate_answer
from digitz_ai_nexus.services.ingestion.embeddings import (
    generate_embedding_json,
    get_embedding_model,
)


INDEX_DOCTYPE = "Nexus Knowledge Index Entry"
CONTEXT_SUMMARY_DOCTYPE = "Nexus Knowledge Context Summary"


def has_semantic_index_doctype():
    return frappe.db.exists("DocType", INDEX_DOCTYPE)


def has_context_summary_doctype():
    return frappe.db.exists("DocType", CONTEXT_SUMMARY_DOCTYPE)


def normalize_space(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def get_entry_hash(entry_type, canonical_text, source, unit, chunk):
    value = "||".join([
        entry_type or "",
        canonical_text or "",
        source or "",
        unit or "",
        chunk or "",
    ])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def split_sentences(text, limit=6):
    text = normalize_space(text)
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    clean = []

    for sentence in sentences:
        sentence = normalize_space(sentence)
        if len(sentence) < 25:
            continue
        clean.append(sentence)
        if len(clean) >= limit:
            break

    return clean


def compact_text(text, limit=260):
    text = normalize_space(text)
    if len(text) <= limit:
        return text

    clipped = text[:limit].rsplit(" ", 1)[0].strip()
    return f"{clipped}."


def clean_context_summary_text(summary):
    summary = normalize_space(summary)
    summary = re.sub(r"^(summary|overview)\s*:\s*", "", summary, flags=re.I).strip()
    summary = summary.strip("\"'` ")

    if not summary:
        return ""

    first_alpha = next((char for char in summary if char.isalpha()), "")
    if first_alpha and first_alpha.islower():
        summary = f"This knowledge area covers {summary}"

    if summary and summary[-1] not in ".!?":
        summary = f"{summary}."

    return summary


def extract_subject_from_definition(sentence):
    match = re.match(
        r"^([A-Z][A-Za-z0-9 '&/-]{2,80}?)\s+(is|are|means|provides|supports|can)\b",
        sentence,
    )
    if not match:
        return None

    return normalize_space(match.group(1))


def make_human_summary(chunk_text):
    sentences = split_sentences(chunk_text, limit=3)
    if not sentences:
        return compact_text(chunk_text)

    return compact_text(" ".join(sentences[:2]), limit=320)


def make_intellectual_summaries(chunk_doc):
    chunk_text = chunk_doc.get("chunk_text") or ""
    sentences = split_sentences(chunk_text, limit=5)

    entity = normalize_space(chunk_doc.get("entity"))
    topic = normalize_space(chunk_doc.get("topic"))
    context = normalize_space(chunk_doc.get("context"))
    sub_context = normalize_space(chunk_doc.get("sub_context"))

    summaries = []

    if entity and topic:
        summaries.append(f"{topic.lower()} of {entity}")
        summaries.append(f"how {entity} relates to {topic.lower()}")

    if context:
        context_parts = [context, sub_context, topic]
        summaries.append(" / ".join([p for p in context_parts if p]))

    for sentence in sentences:
        subject = extract_subject_from_definition(sentence)
        lowered = sentence.lower()

        if subject:
            if " is " in lowered or " are " in lowered or " means " in lowered:
                summaries.append(f"what {subject} is")
                summaries.append(f"definition of {subject}")
            elif " can " in lowered or " supports " in lowered:
                summaries.append(f"what {subject} can do")

        if "public" in lowered and "knowledge" in lowered:
            summaries.append("public knowledge access boundary")
        if "verified" in lowered and ("access" in lowered or "identity" in lowered):
            summaries.append("verified identity access boundary")
        if "ticket" in lowered or "escalat" in lowered:
            summaries.append("support ticket and human escalation flow")
        if "erp" in lowered and ("tool" in lowered or "transaction" in lowered):
            summaries.append("controlled ERP tool and transaction integration")
        if "approved knowledge" in lowered:
            summaries.append("approved knowledge grounding")

    return unique_ordered([compact_text(item, limit=180) for item in summaries if item])


def make_user_questions(chunk_doc):
    chunk_text = chunk_doc.get("chunk_text") or ""
    entity = normalize_space(chunk_doc.get("entity")) or "DIGITZ AI Nexus"
    topic = normalize_space(chunk_doc.get("topic"))

    questions = []

    for question in re.findall(r"[^.!?\n]*\?", chunk_text):
        question = normalize_space(question)
        if len(question) >= 12:
            questions.append(question)

    if entity:
        questions.append(f"What is {entity}?")

    if topic:
        questions.append(f"How does {entity} support {topic.lower()}?")
        questions.append(f"What should I know about {topic.lower()} in {entity}?")

    lowered = chunk_text.lower()
    if "public website chat" in lowered or "public chat" in lowered:
        questions.append("How does Nexus keep public website chat limited to approved public knowledge?")
    if "verified" in lowered or "identity" in lowered:
        questions.append("How does Nexus decide what a verified user can access?")
    if "support" in lowered and ("ticket" in lowered or "escalation" in lowered):
        questions.append("How does Nexus support tickets and human escalation?")
    if "erp" in lowered:
        questions.append("Can Nexus connect AI chat with ERP tools and business systems?")
    if "sop" in lowered or "onboarding" in lowered or "training" in lowered:
        questions.append("How can Nexus support SOP guidance, onboarding, and training?")

    return unique_ordered([compact_text(item, limit=220) for item in questions if item])[:6]


def parse_llm_json(text):
    text = (text or "").strip()
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
    if fenced:
        text = fenced.group(1).strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None

    return None


def build_llm_prompt(chunk_doc):
    return f"""
You are preparing retrieval index entries for DIGITZ AI Nexus.

    Create retrieval index artifacts from the approved knowledge chunk:
    1. intellectual_summaries: technical meaning labels that describe what the facts are about.
       Example: "Cat is an animal" -> "what a cat is"; "Delhi belongs to India" -> "the location of Delhi".
2. human_summary: a short orientation summary used only as display context for generated entries.
3. user_questions: realistic public questions users may ask that this chunk can answer.

Rules:
- Use only the supplied approved knowledge.
- Do not invent product claims.
- Keep intellectual summaries concise and intent-oriented.
- Keep user questions answerable from the chunk.
- Return only valid JSON with keys: intellectual_summaries, human_summary, user_questions.

Context Path: {chunk_doc.get("context_path") or ""}
Entity: {chunk_doc.get("entity") or ""}
Topic: {chunk_doc.get("topic") or ""}

Approved Knowledge Chunk:
{chunk_doc.get("chunk_text") or ""}
""".strip()


def make_llm_payloads(chunk_doc):
    response = generate_answer(build_llm_prompt(chunk_doc))
    data = parse_llm_json(response)

    if not isinstance(data, dict):
        return []

    human_summary = compact_text(data.get("human_summary") or "", limit=320)
    payloads = []

    for summary in unique_ordered(data.get("intellectual_summaries") or []):
        summary = compact_text(summary, limit=180)
        if summary:
            payloads.append({
                "entry_type": "Intellectual Summary",
                "canonical_text": summary,
                "display_summary": human_summary,
            })

    for question in unique_ordered(data.get("user_questions") or []):
        question = compact_text(question, limit=220)
        if question:
            payloads.append({
                "entry_type": "User Question",
                "canonical_text": question,
                "display_summary": human_summary,
            })

    for payload in payloads:
        payload["generation_method"] = "LLM"

    return payloads


def unique_ordered(items):
    seen = set()
    result = []

    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)

    return result


def archive_existing_index_entries(source_name):
    if not source_name or not has_semantic_index_doctype():
        return 0

    names = frappe.get_all(
        INDEX_DOCTYPE,
        filters={"knowledge_source": source_name, "disabled": 0},
        pluck="name",
    )

    for name in names:
        frappe.db.set_value(
            INDEX_DOCTYPE,
            name,
            {
                "disabled": 1,
                "status": "Archived",
            },
            update_modified=False,
        )

    return len(names)


def build_index_payloads(chunk_doc, generation_method="Heuristic"):
    if generation_method == "LLM":
        try:
            payloads = make_llm_payloads(chunk_doc)
            if payloads:
                return payloads
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Nexus Semantic Index LLM Generation Failed")

    human_summary = make_human_summary(chunk_doc.get("chunk_text"))
    payloads = []

    for summary in make_intellectual_summaries(chunk_doc):
        payloads.append({
            "entry_type": "Intellectual Summary",
            "canonical_text": summary,
            "display_summary": human_summary,
        })

    for question in make_user_questions(chunk_doc):
        payloads.append({
            "entry_type": "User Question",
            "canonical_text": question,
            "display_summary": human_summary,
        })

    for payload in payloads:
        payload["generation_method"] = generation_method

    return payloads


def create_index_entry(chunk_doc, payload):
    doc = frappe.new_doc(INDEX_DOCTYPE)

    doc.entry_type = payload.get("entry_type")
    doc.status = "Active"
    doc.canonical_text = payload.get("canonical_text")
    doc.display_summary = payload.get("display_summary")
    doc.answer_preview = compact_text(chunk_doc.get("chunk_text"), limit=320)

    if doc.meta.has_field("generated_answer"):
        doc.generated_answer = doc.answer_preview

    if doc.meta.has_field("answer_review_status"):
        doc.answer_review_status = (
            "Pending Review"
            if doc.entry_type == "User Question"
            else "Approved"
        )

    doc.knowledge_source = chunk_doc.get("knowledge_source")
    doc.knowledge_unit = chunk_doc.get("knowledge_unit")
    doc.knowledge_chunk = chunk_doc.name

    for fieldname in [
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
        "source_version",
    ]:
        if doc.meta.has_field(fieldname):
            doc.set(fieldname, chunk_doc.get(fieldname))

    doc.disabled = 0
    doc.generation_method = payload.get("generation_method") or "Heuristic"
    doc.generation_notes = "Generated from approved knowledge chunk during source processing."

    text_for_embedding = "\n".join([
        doc.entry_type or "",
        doc.canonical_text or "",
        doc.display_summary or "",
        doc.context_path or "",
    ]).strip()

    try:
        doc.embedding = generate_embedding_json(text_for_embedding)
        doc.embedding_model = get_embedding_model()
        doc.embedding_status = "Completed"
    except Exception:
        doc.embedding_status = "Failed"
        doc.generation_notes = frappe.get_traceback()

    doc.entry_hash = get_entry_hash(
        doc.entry_type,
        doc.canonical_text,
        doc.knowledge_source,
        doc.knowledge_unit,
        doc.knowledge_chunk,
    )

    if frappe.db.exists(INDEX_DOCTYPE, {"entry_hash": doc.entry_hash}):
        return None

    doc.insert(ignore_permissions=True)
    return doc.name


def generate_index_entries_for_chunks(chunk_names, generation_method="Heuristic"):
    if not chunk_names or not has_semantic_index_doctype():
        return {
            "created": [],
            "failed": [],
            "skipped": len(chunk_names or []),
        }

    created = []
    failed = []

    for chunk_name in chunk_names:
        try:
            chunk_doc = frappe.get_doc("Nexus Knowledge Chunk", chunk_name)
            for payload in build_index_payloads(
                chunk_doc,
                generation_method=generation_method,
            ):
                name = create_index_entry(chunk_doc, payload)
                if name:
                    created.append(name)
        except Exception:
            failed.append({
                "chunk": chunk_name,
                "error": frappe.get_traceback(),
            })

    return {
        "created": created,
        "failed": failed,
        "skipped": 0,
    }



# Confidence thresholds for LLM auto-decisions
LLM_CONFIDENCE_AUTO_APPROVE = 80   # >= 80 → auto-approved
LLM_CONFIDENCE_AUTO_REJECT  = 40   # <  40 → auto-rejected
                                    # 40–79 → Pending Review (human checks)


def build_question_validation_prompt(question, chunk_text):
    return f"""You are a knowledge quality validator for an enterprise knowledge base.

Given a knowledge chunk and a candidate question, your job is to:
1. Attempt to answer the question using ONLY the chunk content.
2. Rate how well the chunk answers the question with a confidence score from 0 to 100.

Return your response as valid JSON with exactly these keys:
- "answer": the answer text (2–4 sentences from the chunk), or "" if the chunk cannot answer.
- "confidence": integer 0–100 — how well the chunk answers the question.
  Use: 80–100 for direct, complete answers; 40–79 for partial or indirect answers; 0–39 if the chunk does not address the question.
- "reason": one short sentence explaining the confidence score.

Rules:
- Use only content from the chunk — never add outside knowledge.
- If the chunk cannot answer, set answer to "" and confidence below 40.
- Return only the JSON object, no extra text.

Knowledge Chunk:
{chunk_text}

Question: {question}

JSON Response:""".strip()


def _parse_validation_response(response_text):
    """Parse LLM JSON validation response. Returns (answer, confidence, reason)."""
    data = parse_llm_json(response_text)
    if not isinstance(data, dict):
        return "", 0, "Could not parse LLM response."

    answer = str(data.get("answer") or "").strip()
    reason = str(data.get("reason") or "").strip()
    try:
        confidence = max(0, min(100, int(data.get("confidence") or 0)))
    except (ValueError, TypeError):
        confidence = 0

    return answer, confidence, reason


def validate_question_with_llm(entry_name):
    """
    Uses LLM to generate a scored answer for a User Question index entry.

    Confidence thresholds:
    - >= 80 → auto-approved (LLM can answer directly from chunk)
    - 40–79 → Pending Review (partial answer, human decides)
    -  < 40 → auto-rejected (chunk doesn't address the question)

    Stores the LLM answer and confidence note in the entry.
    Returns a result dict with status: 'approved' | 'pending' | 'rejected' | 'skipped' | 'error'.
    """
    if not has_semantic_index_doctype():
        return {"status": "skipped", "reason": "DocType not found"}

    doc = frappe.get_doc(INDEX_DOCTYPE, entry_name)

    if doc.entry_type != "User Question":
        return {"status": "skipped", "reason": "Not a User Question entry"}

    question = doc.get("canonical_text") or ""
    if not question:
        return {"status": "skipped", "reason": "No question text"}

    chunk_name = doc.get("knowledge_chunk")
    if not chunk_name or not frappe.db.exists("Nexus Knowledge Chunk", chunk_name):
        return {"status": "skipped", "reason": "Associated chunk not found"}

    chunk_doc = frappe.get_doc("Nexus Knowledge Chunk", chunk_name)
    chunk_text = chunk_doc.get("chunk_text") or ""
    if not chunk_text:
        return {"status": "skipped", "reason": "Chunk has no text"}

    try:
        raw = generate_answer(build_question_validation_prompt(question, chunk_text))
        raw = (raw or "").strip()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Nexus Question LLM Validation Failed")
        return {"status": "error", "reason": "LLM call failed"}

    answer, confidence, reason = _parse_validation_response(raw)

    if confidence >= LLM_CONFIDENCE_AUTO_APPROVE:
        review_status = "Approved"
        status = "approved"
    elif confidence < LLM_CONFIDENCE_AUTO_REJECT:
        review_status = "Rejected"
        status = "rejected"
    else:
        review_status = "Pending Review"
        status = "pending"

    confidence_note = f"AI Confidence: {confidence}% — {reason}"

    now = frappe.utils.now_datetime()
    updates = {
        "answer_review_status": review_status,
        "answer_reviewed_by": "System (LLM)",
        "answer_reviewed_on": now,
    }
    if doc.meta.has_field("generated_answer"):
        updates["generated_answer"] = answer or doc.get("answer_preview") or ""
    if doc.meta.has_field("answer_review_notes"):
        updates["answer_review_notes"] = confidence_note

    frappe.db.set_value(INDEX_DOCTYPE, entry_name, updates, update_modified=False)

    return {
        "status": status,
        "entry": entry_name,
        "question": question,
        "answer": answer,
        "confidence": confidence,
        "reason": reason,
        "review_status": review_status,
    }


def validate_source_questions_with_llm(source_name):
    """
    Run LLM confidence-scored validation for all Pending Review User Question
    entries of a source. Returns counts per outcome.
    """
    if not has_semantic_index_doctype():
        return {"approved": 0, "pending": 0, "rejected": 0, "skipped": 0, "errors": 0}

    pending = frappe.get_all(
        INDEX_DOCTYPE,
        filters={
            "knowledge_source": source_name,
            "entry_type": "User Question",
            "answer_review_status": "Pending Review",
        },
        pluck="name",
        limit_page_length=10000,
    )

    approved = pending_count = rejected = skipped = errors = 0

    for entry_name in pending:
        result = validate_question_with_llm(entry_name)
        status = result.get("status")
        if status == "approved":
            approved += 1
        elif status == "pending":
            pending_count += 1
        elif status == "rejected":
            rejected += 1
        elif status == "error":
            errors += 1
        else:
            skipped += 1

    frappe.db.commit()

    return {
        "approved": approved,
        "pending": pending_count,
        "rejected": rejected,
        "skipped": skipped,
        "errors": errors,
        "total": len(pending),
    }


def get_context_group_key_from_doc(doc):
    return {
        "tenant": doc.get("tenant"),
        "business_unit": doc.get("business_unit"),
        "project": doc.get("project"),
        "context": doc.get("context"),
        "sub_context": doc.get("sub_context"),
        "entity_type": doc.get("entity_type"),
        "entity": doc.get("entity"),
        "topic": doc.get("topic"),
        "context_path": doc.get("context_path"),
        "access_policy": doc.get("access_policy"),
        "sensitivity": doc.get("sensitivity") or "public",
    }


def get_group_filter(group):
    filters = {
        "disabled": 0,
        "embedding_status": "Completed",
    }

    for fieldname in [
        "tenant",
        "business_unit",
        "project",
        "context",
        "sub_context",
        "entity_type",
        "entity",
        "topic",
        "access_policy",
    ]:
        value = group.get(fieldname)
        if value:
            filters[fieldname] = value
        else:
            filters[fieldname] = ["in", ["", None]]

    return filters


def make_summary_title(group):
    parts = [
        group.get("tenant"),
        group.get("context"),
        group.get("sub_context"),
        group.get("topic") or group.get("entity"),
    ]
    return " / ".join([str(part) for part in parts if part]) or "Knowledge Context Summary"


def build_context_summary_prompt(group, chunks):
    source_text = "\n\n---\n\n".join([
        chunk.get("chunk_text") or ""
        for chunk in chunks[:12]
        if chunk.get("chunk_text")
    ])

    return f"""
You are preparing a tenant-level human-readable knowledge summary for DIGITZ AI Nexus.

Create a concise documentation summary for the grouped knowledge area. The summary is for Q&A popup browsing and broad retrieval.

Rules:
- Use only the approved knowledge chunks supplied.
- Summarize the group, not a single source.
- Mention what the group covers and what users can ask about.
- Do not invent claims.
- Keep it between 70 and 140 words.
- Return only the summary text.

Group:
Tenant: {group.get("tenant") or ""}
Business Unit: {group.get("business_unit") or ""}
Context: {group.get("context") or ""}
Sub Context: {group.get("sub_context") or ""}
Entity Type: {group.get("entity_type") or ""}
Entity: {group.get("entity") or ""}
Topic: {group.get("topic") or ""}
Access Policy: {group.get("access_policy") or ""}

Approved Knowledge Chunks:
{source_text}
""".strip()


def make_context_summary_text(group, chunks, generation_method="LLM"):
    if generation_method == "LLM":
        try:
            summary = generate_answer(build_context_summary_prompt(group, chunks))
            summary = compact_text(clean_context_summary_text(summary), limit=900)
            if summary:
                return summary, "LLM"
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Nexus Context Summary LLM Generation Failed")

    text = " ".join([
        chunk.get("chunk_text") or ""
        for chunk in chunks[:4]
    ])
    return compact_text(make_human_summary(text), limit=700), "Heuristic"


def upsert_context_summary(group, chunks, generation_method="LLM"):
    if not group or not chunks or not has_context_summary_doctype():
        return None

    summary_text, used_method = make_context_summary_text(
        group,
        chunks,
        generation_method=generation_method,
    )

    if not summary_text:
        return None

    source_names = unique_ordered([
        chunk.get("knowledge_source")
        for chunk in chunks
        if chunk.get("knowledge_source")
    ])

    existing = frappe.get_all(
        CONTEXT_SUMMARY_DOCTYPE,
        filters={
            "tenant": group.get("tenant") or ["in", ["", None]],
            "business_unit": group.get("business_unit") or ["in", ["", None]],
            "project": group.get("project") or ["in", ["", None]],
            "context": group.get("context") or ["in", ["", None]],
            "sub_context": group.get("sub_context") or ["in", ["", None]],
            "entity_type": group.get("entity_type") or ["in", ["", None]],
            "entity": group.get("entity") or ["in", ["", None]],
            "topic": group.get("topic") or ["in", ["", None]],
            "access_policy": group.get("access_policy"),
        },
        pluck="name",
        limit_page_length=1,
    )

    if existing:
        doc = frappe.get_doc(CONTEXT_SUMMARY_DOCTYPE, existing[0])
    else:
        doc = frappe.new_doc(CONTEXT_SUMMARY_DOCTYPE)

    doc.summary_title = make_summary_title(group)
    doc.status = "Active"
    doc.summary_text = summary_text
    doc.coverage_notes = f"Grouped summary across {len(source_names)} source(s) and {len(chunks)} chunk(s)."

    for fieldname, value in group.items():
        if doc.meta.has_field(fieldname):
            doc.set(fieldname, value)

    doc.priority = max([int(chunk.get("priority") or 0) for chunk in chunks] or [0])
    doc.disabled = 0
    doc.source_count = len(source_names)
    doc.chunk_count = len(chunks)
    doc.generated_from_sources = json.dumps(source_names)
    doc.generation_method = used_method
    doc.generation_notes = "Generated from active approved chunks in the same tenant/context/topic group."
    doc.generated_on = frappe.utils.now()

    text_for_embedding = "\n".join([
        doc.summary_title or "",
        doc.summary_text or "",
        doc.context_path or "",
    ]).strip()

    try:
        doc.embedding = generate_embedding_json(text_for_embedding)
        doc.embedding_model = get_embedding_model()
        doc.embedding_status = "Completed"
    except Exception:
        doc.embedding_status = "Failed"
        doc.generation_notes = frappe.get_traceback()

    doc.save(ignore_permissions=True) if doc.name else doc.insert(ignore_permissions=True)
    return doc.name


def refresh_context_summaries_for_chunks(chunk_names, generation_method="LLM"):
    if not chunk_names or not has_context_summary_doctype():
        return {
            "updated": [],
            "failed": [],
            "skipped": len(chunk_names or []),
        }

    groups = {}

    for chunk_name in chunk_names:
        try:
            chunk_doc = frappe.get_doc("Nexus Knowledge Chunk", chunk_name)
            group = get_context_group_key_from_doc(chunk_doc)
            key = json.dumps(group, sort_keys=True)
            groups[key] = group
        except Exception:
            continue

    updated = []
    failed = []

    for group in groups.values():
        try:
            chunks = frappe.get_all(
                "Nexus Knowledge Chunk",
                filters=get_group_filter(group),
                fields=[
                    "name",
                    "knowledge_source",
                    "knowledge_unit",
                    "chunk_text",
                    "priority",
                ],
                order_by="priority desc, modified desc",
                limit_page_length=50,
            )
            name = upsert_context_summary(
                group,
                chunks,
                generation_method=generation_method,
            )
            if name:
                updated.append(name)
        except Exception:
            failed.append({
                "group": group,
                "error": frappe.get_traceback(),
            })

    return {
        "updated": updated,
        "failed": failed,
        "skipped": 0,
    }
