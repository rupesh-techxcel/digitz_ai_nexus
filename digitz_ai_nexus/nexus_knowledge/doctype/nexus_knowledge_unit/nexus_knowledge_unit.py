import hashlib

import frappe
from frappe.model.document import Document

class NexusKnowledgeUnit(Document):
    def validate(self):
        self.set_context_path()
        self.set_content_hash()

    def set_context_path(self):
        parts = [
            self.context,
            self.sub_context,
            self.entity_type,
            self.entity,
            self.topic,
        ]
        self.context_path = "/".join([p.strip() for p in parts if p and str(p).strip()])

    def set_content_hash(self):
        if self.content:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()
        else:
            self.content_hash = None


# -------------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------------

def _has_field(doctype: str, fieldname: str) -> bool:
    """Return True if field exists in the DocType metadata."""
    try:
        return frappe.get_meta(doctype).has_field(fieldname)
    except Exception:
        return False


def _set_if_exists(doc, fieldname: str, value):
    """Set field only if it exists on the DocType."""
    if _has_field(doc.doctype, fieldname):
        doc.set(fieldname, value)


def _get_if_exists(doc, fieldname: str, default=None):
    """Get field value only if it exists on the DocType."""
    if _has_field(doc.doctype, fieldname):
        return doc.get(fieldname)
    return default


def _get_chunk_count(knowledge_unit_name: str) -> int:
    """
    Count chunks linked to this knowledge unit.

    This is intentionally defensive because the exact link field
    in Nexus Knowledge Chunk may vary depending on your current schema.
    """
    if not frappe.db.exists("DocType", "Nexus Knowledge Chunk"):
        return 0

    possible_link_fields = [
        "knowledge_unit",
        "knowledge_unit_id",
        "nexus_knowledge_unit",
        "source_knowledge_unit",
    ]

    chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")

    for fieldname in possible_link_fields:
        if chunk_meta.has_field(fieldname):
            return frappe.db.count(
                "Nexus Knowledge Chunk",
                {
                    fieldname: knowledge_unit_name,
                    "docstatus": ["!=", 2],
                },
            )

    return 0


def _get_embedded_chunk_count(knowledge_unit_name: str) -> int:
    """
    Count chunks that appear to have embeddings.

    Supports common embedding field names defensively.
    """
    if not frappe.db.exists("DocType", "Nexus Knowledge Chunk"):
        return 0

    chunk_meta = frappe.get_meta("Nexus Knowledge Chunk")

    possible_link_fields = [
        "knowledge_unit",
        "knowledge_unit_id",
        "nexus_knowledge_unit",
        "source_knowledge_unit",
    ]

    possible_embedding_fields = [
        "embedding",
        "embedding_json",
        "vector",
        "vector_json",
    ]

    link_field = None
    embedding_field = None

    for fieldname in possible_link_fields:
        if chunk_meta.has_field(fieldname):
            link_field = fieldname
            break

    for fieldname in possible_embedding_fields:
        if chunk_meta.has_field(fieldname):
            embedding_field = fieldname
            break

    if not link_field or not embedding_field:
        return 0

    return frappe.db.count(
        "Nexus Knowledge Chunk",
        {
            link_field: knowledge_unit_name,
            embedding_field: ["not in", ["", None]],
            "docstatus": ["!=", 2],
        },
    )


def _required_readiness_fields():
    """
    Minimum fields expected before a knowledge unit can be considered ready.

    These are aligned with the Nexus Studio knowledge lifecycle.
    The helper only evaluates fields that actually exist on the current DocType.
    """
    return [
        "tenant",
        "business_unit",
        "context",
        "content",
    ]


def _build_readiness_payload(doc):
    missing_fields = []

    for fieldname in _required_readiness_fields():
        if _has_field(doc.doctype, fieldname):
            value = doc.get(fieldname)
            if value in (None, ""):
                missing_fields.append(fieldname)

    chunk_count = _get_chunk_count(doc.name)
    embedded_chunk_count = _get_embedded_chunk_count(doc.name)

    disabled = bool(_get_if_exists(doc, "disabled", 0))
    published = bool(_get_if_exists(doc, "published", 0))
    needs_review = bool(_get_if_exists(doc, "needs_review", 0))

    approval_status = _get_if_exists(doc, "approval_status")
    status = _get_if_exists(doc, "status")

    is_approved = (
        str(approval_status or "").strip().lower() == "approved"
        or str(status or "").strip().lower() in ["approved", "chunked", "embedded", "tested", "ready to publish", "published"]
    )

    is_chunked = chunk_count > 0
    is_embedded = embedded_chunk_count > 0 and embedded_chunk_count == chunk_count if chunk_count else False

    ready_for_chunking = (
        not disabled
        and not needs_review
        and not missing_fields
        and bool(doc.get("content"))
    )

    ready_to_publish = (
        not disabled
        and not needs_review
        and not missing_fields
        and is_approved
        and is_chunked
        and is_embedded
    )

    return {
        "success": True,
        "name": doc.name,
        "status": status,
        "approval_status": approval_status,
        "disabled": disabled,
        "published": published,
        "needs_review": needs_review,
        "missing_fields": missing_fields,
        "chunk_count": chunk_count,
        "embedded_chunk_count": embedded_chunk_count,
        "is_approved": is_approved,
        "is_chunked": is_chunked,
        "is_embedded": is_embedded,
        "ready_for_chunking": ready_for_chunking,
        "ready_to_publish": ready_to_publish,
    }


# -------------------------------------------------------------------------
# Studio workflow methods
# -------------------------------------------------------------------------

@frappe.whitelist()
def get_knowledge_unit_readiness(name: str):
    """
    Returns readiness information for a Nexus Knowledge Unit.

    Used by Nexus Studio to understand whether a knowledge unit is:
    - complete enough for chunking
    - already chunked
    - already embedded
    - ready to publish
    - blocked by missing fields or review status
    """
    if not name:
        return {
            "success": False,
            "message": "Knowledge Unit name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Unit", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Unit not found: {name}",
        }

    doc = frappe.get_doc("Nexus Knowledge Unit", name)
    return _build_readiness_payload(doc)


@frappe.whitelist()
def approve_knowledge_unit(name: str):
    """
    Approves a Nexus Knowledge Unit for AI preparation.

    This does not chunk or embed the content.
    It only moves the knowledge unit into an approved/readiness state.
    """
    if not name:
        return {
            "success": False,
            "message": "Knowledge Unit name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Unit", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Unit not found: {name}",
        }

    doc = frappe.get_doc("Nexus Knowledge Unit", name)

    readiness = _build_readiness_payload(doc)
    if readiness.get("missing_fields"):
        return {
            "success": False,
            "message": "Knowledge Unit cannot be approved because required fields are missing.",
            "missing_fields": readiness.get("missing_fields"),
            "readiness": readiness,
        }

    if not doc.get("content"):
        return {
            "success": False,
            "message": "Knowledge Unit cannot be approved without content.",
            "readiness": readiness,
        }

    _set_if_exists(doc, "approval_status", "Approved")
    _set_if_exists(doc, "status", "Approved")
    _set_if_exists(doc, "needs_review", 0)
    _set_if_exists(doc, "review_reason", None)
    _set_if_exists(doc, "approved_on", frappe.utils.now())
    _set_if_exists(doc, "approved_by", frappe.session.user)

    doc.save(ignore_permissions=False)

    return {
        "success": True,
        "message": "Knowledge Unit approved successfully.",
        "readiness": _build_readiness_payload(doc),
    }


@frappe.whitelist()
def mark_knowledge_unit_needs_review(name: str, reason: str = None):
    """
    Marks a Nexus Knowledge Unit as needing review.

    This is useful when tests fail, source content becomes stale,
    or knowledge quality is not trusted for publishing.
    """
    if not name:
        return {
            "success": False,
            "message": "Knowledge Unit name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Unit", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Unit not found: {name}",
        }

    doc = frappe.get_doc("Nexus Knowledge Unit", name)

    _set_if_exists(doc, "needs_review", 1)
    _set_if_exists(doc, "review_reason", reason or "Marked for review from Nexus Studio.")
    _set_if_exists(doc, "status", "Needs Review")
    _set_if_exists(doc, "published", 0)

    doc.save(ignore_permissions=False)

    return {
        "success": True,
        "message": "Knowledge Unit marked as Needs Review.",
        "readiness": _build_readiness_payload(doc),
    }


@frappe.whitelist()
def mark_knowledge_unit_ready_to_publish(name: str):
    """
    Marks a Nexus Knowledge Unit as Ready to Publish if readiness checks pass.

    This does not publish to Live/Q&A directly.
    It only confirms Studio readiness.
    """
    if not name:
        return {
            "success": False,
            "message": "Knowledge Unit name is required.",
        }

    if not frappe.db.exists("Nexus Knowledge Unit", name):
        return {
            "success": False,
            "message": f"Nexus Knowledge Unit not found: {name}",
        }

    doc = frappe.get_doc("Nexus Knowledge Unit", name)
    readiness = _build_readiness_payload(doc)

    if not readiness.get("ready_to_publish"):
        return {
            "success": False,
            "message": "Knowledge Unit is not ready to publish.",
            "readiness": readiness,
        }

    _set_if_exists(doc, "status", "Ready to Publish")
    _set_if_exists(doc, "ready_to_publish", 1)

    doc.save(ignore_permissions=False)

    return {
        "success": True,
        "message": "Knowledge Unit marked as Ready to Publish.",
        "readiness": _build_readiness_payload(doc),
    }