"""
Knowledge Gap Detection Service

Records queries that the system could not answer (or answered with low confidence)
as Nexus Knowledge Gap documents. Deduplicates by a semantic key derived from the
normalised query + tenant so repeated identical questions increment a frequency
counter rather than creating duplicate rows.

Each new gap triggers an async LLM assessment job that evaluates whether the
question is in-domain and should be added to the knowledge base.
"""

import hashlib
import json
import re

import frappe
from frappe.utils import now_datetime


# Confidence at or below this value qualifies as a gap even when an answer
# was returned (i.e. not a full fallback but below review threshold).
GAP_CONFIDENCE_THRESHOLD = 0.55

# Maximum sample queries stored per gap record (rotating FIFO).
MAX_SAMPLES = 5


# ── Public entry point ─────────────────────────────────────────────────────────

def record_gap(payload, access_status, confidence):
    """
    Called from answer_service after every fallback or low-confidence result.

    payload       — the query payload passed into answer_query()
    access_status — "no_context", "low_confidence", or "restricted"
    confidence    — float confidence score (0.0–1.0)

    Runs synchronously but the LLM assessment is enqueued as a background job.
    Errors are swallowed so a gap-recording failure never breaks the chat flow.
    Returns the gap name so callers can include it in the response payload.
    """
    try:
        return _record(payload, access_status, confidence)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Nexus Knowledge Gap: record_gap failed")
    return None


# ── Internal implementation ────────────────────────────────────────────────────

def _normalise(query):
    """Lowercase, collapse whitespace, strip punctuation for dedup hashing."""
    text = (query or "").lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _semantic_key(normalised_query, tenant):
    raw = f"{tenant or ''}::{normalised_query}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _gap_type(access_status, confidence):
    if access_status == "restricted":
        return "Restricted Access"
    if access_status == "no_context" or confidence == 0.0:
        return "No Context"
    return "Low Confidence"


def _record(payload, access_status, confidence):
    query = (payload.get("query") or payload.get("message") or "").strip()
    if not query:
        return

    tenant = payload.get("tenant") or payload.get("_resolved_tenant_context", {}).get("tenant") or ""
    channel = payload.get("channel") or ""

    normalised = _normalise(query)
    key = _semantic_key(normalised, tenant)
    now = now_datetime()

    existing_name = frappe.db.get_value("Nexus Knowledge Gap", {"semantic_key": key}, "name")

    if existing_name:
        return _update_existing(existing_name, query, confidence, now)

    gap = frappe.new_doc("Nexus Knowledge Gap")
    gap.semantic_key = key
    gap.query = query
    gap.normalized_query = normalised
    gap.tenant = tenant or None
    gap.channel = channel or None
    gap.gap_type = _gap_type(access_status, confidence)
    gap.access_status = access_status
    gap.confidence = round(float(confidence or 0), 2)
    gap.frequency = 1
    gap.first_seen_on = now
    gap.last_seen_on = now
    gap.status = "New"
    gap.llm_assessment_status = "Pending"
    gap.sample_queries_json = json.dumps([query])
    gap.detection_mode = "Reactive"
    gap.insert(ignore_permissions=True)
    frappe.db.commit()

    # Enqueue LLM assessment as a background job so it doesn't block the response
    frappe.enqueue(
        "digitz_ai_nexus.services.gap_detection_service._assess_gap",
        gap_name=gap.name,
        tenant=tenant,
        queue="long",
        timeout=120,
    )
    return gap.name


def _update_existing(gap_name, query, confidence, now):
    doc = frappe.get_doc("Nexus Knowledge Gap", gap_name)

    doc.frequency = (doc.frequency or 1) + 1
    doc.last_seen_on = now

    # Keep best (lowest) confidence so the worst-case scenario is shown
    if confidence and (doc.confidence == 0 or confidence < doc.confidence):
        doc.confidence = round(float(confidence), 2)

    # Rotate sample queries (up to MAX_SAMPLES unique examples)
    try:
        samples = json.loads(doc.sample_queries_json or "[]")
    except Exception:
        samples = []
    if query not in samples:
        samples.append(query)
    doc.sample_queries_json = json.dumps(samples[-MAX_SAMPLES:])

    # Re-open dismissed/actioned gaps that keep recurring
    if doc.status in ("Dismissed",) and doc.frequency % 10 == 0:
        doc.status = "New"
        doc.llm_assessment_status = "Pending"

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return gap_name


# ── LLM assessment background job ─────────────────────────────────────────────

def _assess_gap(gap_name, tenant):
    """
    Background job: uses the LLM to evaluate whether the gap query is in-domain
    and what knowledge area it belongs to.

    Writes is_relevant, relevance_confidence, suggested_context, suggested_topic,
    and llm_summary back to the Nexus Knowledge Gap record.
    """
    try:
        doc = frappe.get_doc("Nexus Knowledge Gap", gap_name)
        if doc.llm_assessment_status == "Completed":
            return

        knowledge_topics = _get_knowledge_topics(tenant)
        result = _run_llm_assessment(doc.query, knowledge_topics, tenant)

        frappe.db.set_value("Nexus Knowledge Gap", gap_name, {
            "llm_assessment_status": "Completed",
            "is_relevant": 1 if result.get("is_relevant") else 0,
            "relevance_confidence": round(float(result.get("relevance_confidence") or 0), 2),
            "suggested_context": (result.get("suggested_context") or "")[:140],
            "suggested_topic": (result.get("suggested_topic") or "")[:140],
            "llm_summary": (result.get("summary") or "")[:500],
        })
        frappe.db.commit()

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Nexus Knowledge Gap LLM Assessment Failed: {gap_name}")
        try:
            frappe.db.set_value("Nexus Knowledge Gap", gap_name, "llm_assessment_status", "Failed")
            frappe.db.commit()
        except Exception:
            pass


def _get_knowledge_topics(tenant):
    """
    Return a compact summary of what's currently in the knowledge base for this
    tenant — used as context for the LLM relevance assessment.
    """
    filters = {"status": "Active"}
    if tenant:
        filters["tenant"] = tenant

    units = frappe.get_all(
        "Nexus Knowledge Unit",
        filters=filters,
        fields=["title", "context", "sub_context", "entity_type", "entity", "topic"],
        limit_page_length=100,
        order_by="modified desc",
    )

    if not units:
        return "No knowledge units exist yet."

    lines = []
    seen = set()
    for u in units:
        parts = [p for p in [u.context, u.sub_context, u.entity_type, u.entity, u.topic] if p]
        label = f"{u.title}" + (f" [{'/'.join(parts)}]" if parts else "")
        if label not in seen:
            seen.add(label)
            lines.append(f"- {label}")
        if len(lines) >= 60:
            break

    return "\n".join(lines)


def _run_llm_assessment(query, knowledge_topics, tenant):
    """
    Ask the LLM whether the gap query is in-domain and what area it belongs to.
    Returns a dict: is_relevant, relevance_confidence, suggested_context,
                    suggested_topic, summary
    """
    from digitz_ai_nexus.engine.llm import generate_answer

    prompt = f"""You are a knowledge management assistant for a tenant's AI knowledge base.

A user asked a question that the system could NOT answer (no relevant knowledge found or very low confidence).

User question:
"{query}"

Current knowledge base topics for this tenant:
{knowledge_topics}

Your task: evaluate whether this question is something that SHOULD be added to the knowledge base.

Consider:
1. Is this question likely relevant to the organisation's domain (based on the existing topics)?
2. Would adding knowledge about this topic meaningfully improve the system?
3. What knowledge area / context does it belong to?
4. Is it a one-off personal question, or a topic that many users would benefit from?

Respond with ONLY a valid JSON object — no markdown, no code fences:
{{
  "is_relevant": true or false,
  "relevance_confidence": 0.0 to 1.0,
  "suggested_context": "short area name e.g. HR / Finance / Product / Support",
  "suggested_topic": "concise topic label e.g. Leave Policy / Pricing / Returns",
  "summary": "1-2 sentence explanation of your assessment"
}}"""

    try:
        raw = (generate_answer(prompt) or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`").lstrip("json").strip()
        result = json.loads(raw)
        return {
            "is_relevant": bool(result.get("is_relevant")),
            "relevance_confidence": float(result.get("relevance_confidence") or 0),
            "suggested_context": str(result.get("suggested_context") or ""),
            "suggested_topic": str(result.get("suggested_topic") or ""),
            "summary": str(result.get("summary") or ""),
        }
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Nexus Gap: LLM assessment JSON parse failed")
        return {
            "is_relevant": False,
            "relevance_confidence": 0.0,
            "suggested_context": "",
            "suggested_topic": "",
            "summary": "Assessment could not be completed.",
        }


# ── Scheduled re-assessment ────────────────────────────────────────────────────

def detect_proactive_gaps():
    """
    Weekly scheduler: scan Nexus Query Log for uncaptured poor-performing queries
    per tenant, cluster them with the LLM, and create Proactive gap records for
    topic areas that are not covered in the knowledge base.
    """
    tenants = frappe.get_all("Nexus Tenant", filters={"disabled": 0}, pluck="name")
    for tenant in tenants:
        try:
            _run_proactive_detection(tenant)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Nexus Proactive Gap Detection failed for tenant: {tenant}",
            )


def _run_proactive_detection(tenant):
    from frappe.utils import add_days, now_datetime

    since = add_days(now_datetime(), -30)

    logs = frappe.get_all(
        "Nexus Query Log",
        filters={
            "tenant": tenant,
            "creation": [">=", since],
            "access_status": ["in", ["no_context", "low_confidence"]],
        },
        fields=["query", "access_status", "confidence"],
        limit_page_length=200,
        order_by="creation desc",
    )

    if len(logs) < 5:
        return

    existing_keys = set(
        frappe.get_all("Nexus Knowledge Gap", filters={"tenant": tenant}, pluck="semantic_key")
    )

    uncaptured = []
    for log in logs:
        q = (log.query or "").strip()
        if not q:
            continue
        key = _semantic_key(_normalise(q), tenant)
        if key not in existing_keys:
            uncaptured.append(q)

    if len(uncaptured) < 3:
        return

    kb_topics = _get_knowledge_topics(tenant)
    clusters = _run_proactive_llm_analysis(uncaptured[:50], kb_topics, tenant)

    for cluster in clusters:
        if not cluster.get("is_covered"):
            _create_proactive_gap(cluster, tenant)


def _run_proactive_llm_analysis(queries, kb_topics, tenant):
    from digitz_ai_nexus.engine.llm import generate_answer

    query_list = "\n".join(f"- {q}" for q in queries)

    prompt = f"""You are a knowledge gap analyst for a governed AI knowledge platform.

The knowledge base currently covers these topics:
{kb_topics}

Users have asked the following questions that the system could NOT answer (no matching knowledge found):
{query_list}

Your task:
1. Group these queries into distinct topic clusters (maximum 10 clusters).
2. For each cluster, determine if it is meaningfully covered by the existing knowledge base topics above.
3. Return ONLY clusters that are NOT covered (is_covered = false).
4. Focus on actionable topic areas that would genuinely help if added to the knowledge base.

Respond with ONLY a valid JSON array — no markdown, no code fences:
[
  {{
    "topic_label": "Concise topic name e.g. Annual Leave Policy",
    "context_area": "Domain area e.g. HR / Finance / Product / Support",
    "is_covered": false,
    "sample_queries": ["exact query 1", "exact query 2"],
    "priority": "high or medium or low",
    "summary": "1-2 sentences on why this should be added to the knowledge base"
  }}
]

If all queries are already covered or you cannot identify meaningful clusters, return an empty array: []"""

    try:
        raw = (generate_answer(prompt) or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`").lstrip("json").strip()
        result = json.loads(raw)
        if not isinstance(result, list):
            return []
        valid = []
        for item in result:
            if isinstance(item, dict) and item.get("topic_label"):
                valid.append(item)
        return valid
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Nexus Proactive Gap: LLM cluster analysis JSON parse failed",
        )
        return []


def _create_proactive_gap(cluster, tenant):
    topic_label = (cluster.get("topic_label") or "").strip()
    if not topic_label:
        return

    representative_query = f"[Topic] {topic_label}"
    normalised = _normalise(representative_query)
    key = _semantic_key(normalised, tenant)
    now = now_datetime()

    existing_name = frappe.db.get_value("Nexus Knowledge Gap", {"semantic_key": key}, "name")
    if existing_name:
        doc = frappe.get_doc("Nexus Knowledge Gap", existing_name)
        doc.frequency = (doc.frequency or 1) + len(cluster.get("sample_queries") or [])
        doc.last_seen_on = now
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return

    samples = (cluster.get("sample_queries") or [])[:MAX_SAMPLES]

    gap = frappe.new_doc("Nexus Knowledge Gap")
    gap.semantic_key = key
    gap.query = representative_query
    gap.normalized_query = normalised
    gap.tenant = tenant or None
    gap.gap_type = "No Context"
    gap.access_status = "no_context"
    gap.confidence = 0.0
    gap.frequency = len(samples) or 1
    gap.first_seen_on = now
    gap.last_seen_on = now
    gap.status = "New"
    gap.detection_mode = "Proactive"
    gap.llm_assessment_status = "Completed"
    gap.is_relevant = 1
    gap.relevance_confidence = 0.9
    gap.suggested_context = (cluster.get("context_area") or "")[:140]
    gap.suggested_topic = topic_label[:140]
    gap.llm_summary = (cluster.get("summary") or "")[:500]
    gap.sample_queries_json = json.dumps(samples)
    gap.insert(ignore_permissions=True)
    frappe.db.commit()


def reassess_pending_gaps():
    """
    Scheduled job (daily): re-run LLM assessment on gaps that are still Pending
    or previously Failed, and on high-frequency gaps that haven't been actioned.
    """
    pending = frappe.get_all(
        "Nexus Knowledge Gap",
        filters={
            "llm_assessment_status": ["in", ["Pending", "Failed"]],
            "status": ["not in", ["Dismissed", "Actioned"]],
        },
        fields=["name", "tenant"],
        limit_page_length=50,
    )
    for row in pending:
        frappe.enqueue(
            "digitz_ai_nexus.services.gap_detection_service._assess_gap",
            gap_name=row.name,
            tenant=row.tenant or "",
            queue="long",
            timeout=120,
        )
