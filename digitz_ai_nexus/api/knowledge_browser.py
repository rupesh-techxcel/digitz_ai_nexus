import json
import re

import frappe


# ---------------------------------------------------------------------------
# Tenant resolution
# ---------------------------------------------------------------------------

def _resolve_browser_tenant(requested_tenant=None):
    """
    Priority: caller-supplied → browser_default_tenant → default_tenant.
    """
    if requested_tenant:
        if frappe.db.exists("Nexus Tenant", requested_tenant):
            return requested_tenant
    try:
        settings = frappe.get_single("Nexus Settings")
        return (
            settings.get("browser_default_tenant")
            or settings.get("default_tenant")
            or None
        )
    except Exception:
        return None


def _get_primitive_public_policies(tenant):
    """Return names of all is_primitive=1, non-disabled Access Policies for the tenant."""
    filters = {"is_primitive": 1, "disabled": 0}
    if tenant:
        filters["tenant"] = tenant
    return [r.name for r in frappe.get_all("Nexus Access Policy", filters=filters, fields=["name"])]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_browser_context():
    """Returns the resolved browser tenant and its display label."""
    tenant = _resolve_browser_tenant()
    if not tenant:
        return {"success": False, "tenant": None, "tenant_label": None,
                "message": "No default tenant configured for the Knowledge Browser."}
    label = frappe.db.get_value("Nexus Tenant", tenant, "tenant_name") or tenant
    return {"success": True, "tenant": tenant, "tenant_label": label}


@frappe.whitelist(allow_guest=True)
def get_public_knowledge_feed(search=None, context=None, topic=None,
                               page=1, page_size=20, tenant=None,
                               search_mode="text"):
    """
    Returns public Knowledge Units for the browser listing.

    search_mode:
      "text"   — SQL LIKE substring match on title / content / context / topic
      "vector" — Semantic cosine similarity over public Knowledge Chunks,
                 grouped back to parent Knowledge Units. Falls back to text
                 search if no embeddings are available or embedding generation
                 fails.
    """
    resolved_tenant = _resolve_browser_tenant(tenant)
    if not resolved_tenant:
        return {"success": False, "tenant": None, "items": [], "total": 0,
                "message": "No tenant configured for the Knowledge Browser."}

    public_policies = _get_primitive_public_policies(resolved_tenant)
    if not public_policies:
        return {"success": True, "tenant": resolved_tenant, "items": [], "total": 0,
                "contexts": [], "topics": [], "search_mode": search_mode}

    try:
        page = max(1, int(page))
        page_size = min(50, max(1, int(page_size)))
    except (TypeError, ValueError):
        page, page_size = 1, 20

    # Base filters for filter-pill dropdowns (always from units)
    base_unit_filters = {"access_policy": ["in", public_policies], "status": "Active"}
    if context:
        base_unit_filters["context"] = context
    if topic:
        base_unit_filters["topic"] = topic

    # ── Vector search ────────────────────────────────────────────────────────
    if search_mode == "vector" and search:
        result = _vector_search(
            query=search,
            public_policies=public_policies,
            context=context,
            topic=topic,
            page=page,
            page_size=page_size,
        )

        if result is not None:
            contexts = _get_distinct_field_values("Nexus Knowledge Unit", "context", base_unit_filters)
            topics   = _get_distinct_field_values("Nexus Knowledge Unit", "topic",   base_unit_filters)
            return {
                "success": True,
                "tenant": resolved_tenant,
                "search_mode": "vector",
                "items": result["items"],
                "total": result["total"],
                "page": page,
                "page_size": page_size,
                "contexts": contexts,
                "topics": topics,
            }
        # Fall through to text search if vector search failed
        search_mode = "text"

    # ── Text (SQL LIKE) search ────────────────────────────────────────────────
    db_filters = dict(base_unit_filters)
    or_filters = []
    if search:
        q = f"%{search}%"
        for field in ["title", "context", "sub_context", "topic", "content"]:
            or_filters.append(["Nexus Knowledge Unit", field, "like", q])

    rows = frappe.get_all(
        "Nexus Knowledge Unit",
        fields=["name", "title", "content", "context", "sub_context",
                "entity_type", "entity", "topic", "context_path",
                "sensitivity", "access_policy", "chunk_count", "modified"],
        filters=db_filters,
        or_filters=or_filters or None,
        order_by="modified desc",
        start=(page - 1) * page_size,
        page_length=page_size,
    )

    total = frappe.db.count("Nexus Knowledge Unit", filters=db_filters)

    items = []
    for row in rows:
        items.append({
            "name": row.name,
            "title": row.title or row.name,
            "snippet": _make_snippet(row.get("content") or "", 200),
            "breadcrumb": _make_breadcrumb(row),
            "context": row.context,
            "sub_context": row.sub_context,
            "entity_type": row.entity_type,
            "entity": row.entity,
            "topic": row.topic,
            "sensitivity": row.sensitivity,
            "chunk_count": row.chunk_count or 0,
            "modified": str(row.modified) if row.modified else None,
        })

    contexts = _get_distinct_field_values("Nexus Knowledge Unit", "context", base_unit_filters)
    topics   = _get_distinct_field_values("Nexus Knowledge Unit", "topic",   base_unit_filters)

    return {
        "success": True,
        "tenant": resolved_tenant,
        "search_mode": search_mode,
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "contexts": contexts,
        "topics": topics,
    }


@frappe.whitelist(allow_guest=True)
def get_knowledge_unit_detail(name, tenant=None):
    """Returns full content of a single public Knowledge Unit for the detail panel."""
    resolved_tenant = _resolve_browser_tenant(tenant)
    if not resolved_tenant:
        frappe.throw("No tenant configured for the Knowledge Browser.", frappe.PermissionError)

    public_policies = _get_primitive_public_policies(resolved_tenant)
    if not public_policies:
        frappe.throw("No public knowledge available.", frappe.PermissionError)

    doc = frappe.get_value(
        "Nexus Knowledge Unit",
        {"name": name, "access_policy": ["in", public_policies], "status": "Active"},
        ["name", "title", "content", "context", "sub_context",
         "entity_type", "entity", "topic", "context_path",
         "sensitivity", "access_policy", "chunk_count",
         "approved_by", "approved_on", "modified"],
        as_dict=True,
    )
    if not doc:
        frappe.throw("Knowledge item not found or not publicly accessible.", frappe.DoesNotExistError)

    return {
        "success": True,
        "item": {
            "name": doc.name,
            "title": doc.title or doc.name,
            "content": doc.content or "",
            "breadcrumb": _make_breadcrumb(doc),
            "context": doc.context,
            "sub_context": doc.sub_context,
            "entity_type": doc.entity_type,
            "entity": doc.entity,
            "topic": doc.topic,
            "context_path": doc.context_path,
            "sensitivity": doc.sensitivity,
            "chunk_count": doc.chunk_count or 0,
            "approved_by": doc.approved_by,
            "approved_on": str(doc.approved_on) if doc.approved_on else None,
            "modified": str(doc.modified) if doc.modified else None,
        },
    }


# ---------------------------------------------------------------------------
# Vector search
# ---------------------------------------------------------------------------

_CHUNK_FIELDS = [
    "name", "knowledge_unit", "chunk_text", "embedding",
    "context", "sub_context", "entity_type", "entity",
    "topic", "sensitivity", "access_policy",
]

_SCORE_THRESHOLD = 0.28


def _vector_search(query, public_policies, context=None, topic=None, page=1, page_size=20):
    """
    Semantic search over public Knowledge Chunks.

    Steps:
      1. Embed the query.
      2. Fetch all public chunks that have a completed embedding.
      3. Score each chunk via cosine similarity.
      4. Group by parent Knowledge Unit — keep the best-scoring chunk per unit.
      5. Filter by threshold, sort descending, paginate.
      6. Hydrate unit metadata (title, chunk_count, modified) for display.

    Returns a dict {items, total} on success, or None if embedding fails
    (caller falls back to text search).
    """
    try:
        from digitz_ai_nexus.engine.embedding import generate_embedding
        query_embedding = generate_embedding(query)
    except Exception:
        return None

    if not query_embedding:
        return None

    chunk_filters = {
        "access_policy": ["in", public_policies],
        "disabled": 0,
        "embedding_status": "Completed",
    }
    if context:
        chunk_filters["context"] = context
    if topic:
        chunk_filters["topic"] = topic

    chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")
    valid_fields = [f for f in _CHUNK_FIELDS if f == "name" or chunk_meta.has_field(f)]

    chunks = frappe.get_all(
        "Nexus Knowledge Chunk",
        filters=chunk_filters,
        fields=valid_fields,
        limit_page_length=3000,
    )

    if not chunks:
        return {"items": [], "total": 0}

    # Score and group by unit
    unit_best = {}   # unit_name → {score, snippet, metadata}

    for chunk in chunks:
        raw = chunk.get("embedding")
        if not raw:
            continue
        try:
            vec = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            continue

        score = _cosine_similarity(query_embedding, vec)
        unit_name = chunk.get("knowledge_unit")
        if not unit_name:
            continue

        existing = unit_best.get(unit_name)
        if existing is None or score > existing["score"]:
            unit_best[unit_name] = {
                "score": score,
                "snippet": (chunk.get("chunk_text") or "")[:300],
                "context": chunk.get("context"),
                "sub_context": chunk.get("sub_context"),
                "entity_type": chunk.get("entity_type"),
                "entity": chunk.get("entity"),
                "topic": chunk.get("topic"),
                "sensitivity": chunk.get("sensitivity"),
            }

    # Filter by threshold and sort
    ranked = sorted(
        [(name, data) for name, data in unit_best.items() if data["score"] >= _SCORE_THRESHOLD],
        key=lambda x: x[1]["score"],
        reverse=True,
    )

    total = len(ranked)
    start = (page - 1) * page_size
    page_slice = ranked[start : start + page_size]

    if not page_slice:
        return {"items": [], "total": total}

    # Hydrate with unit-level metadata
    unit_names = [name for name, _ in page_slice]
    unit_rows = frappe.get_all(
        "Nexus Knowledge Unit",
        filters={"name": ["in", unit_names]},
        fields=["name", "title", "chunk_count", "modified"],
        limit_page_length=len(unit_names),
    )
    unit_map = {u.name: u for u in unit_rows}

    items = []
    for unit_name, data in page_slice:
        unit = unit_map.get(unit_name, frappe._dict())
        snippet = _make_snippet(data["snippet"], 200)
        items.append({
            "name": unit_name,
            "title": unit.get("title") or unit_name,
            "snippet": snippet,
            "breadcrumb": _make_breadcrumb(data),
            "context": data.get("context"),
            "sub_context": data.get("sub_context"),
            "entity_type": data.get("entity_type"),
            "entity": data.get("entity"),
            "topic": data.get("topic"),
            "sensitivity": data.get("sensitivity"),
            "chunk_count": unit.get("chunk_count") or 0,
            "modified": str(unit.get("modified")) if unit.get("modified") else None,
            "score": round(data["score"], 4),
        })

    return {"items": items, "total": total}


def _cosine_similarity(vec1, vec2):
    """Pure-Python cosine similarity — avoids importing the full retrieval module."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    import math
    dot   = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if not norm1 or not norm2:
        return 0.0
    return dot / (norm1 * norm2)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_snippet(content: str, max_len: int) -> str:
    if not content:
        return ""
    plain = re.sub(r"<[^>]+>", " ", content)
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) <= max_len:
        return plain
    return plain[:max_len].rsplit(" ", 1)[0] + "…"


def _make_breadcrumb(row) -> str:
    parts = []
    for val in [row.get("context"), row.get("sub_context"), row.get("topic")]:
        if val and str(val).strip():
            parts.append(str(val).strip())
    return " › ".join(parts) if parts else "General"


def _get_distinct_field_values(doctype, fieldname, base_filters):
    try:
        rows = frappe.get_all(
            doctype,
            fields=[fieldname],
            filters=base_filters,
            group_by=fieldname,
            limit_page_length=200,
        )
        return sorted({r[fieldname] for r in rows if r.get(fieldname)})
    except Exception:
        return []
