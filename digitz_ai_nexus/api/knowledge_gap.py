import re

import frappe
from frappe.utils import now_datetime

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
_GAP_OTP_TEMPLATE = "nexus-gap-otp-verification"
_GAP_OTP_VALIDITY_MINUTES = 10


@frappe.whitelist()
def get_gap_summary(tenant=None, status=None, gap_type=None, limit=100):
    """
    Return knowledge gaps for the admin review page.

    Optional filters: tenant, status, gap_type.
    Results ordered by frequency desc so the most-asked unanswered questions
    surface first.
    """
    filters = {}
    if tenant:
        filters["tenant"] = tenant
    if status:
        filters["status"] = status
    if gap_type:
        filters["gap_type"] = gap_type

    rows = frappe.get_all(
        "Nexus Knowledge Gap",
        filters=filters,
        fields=[
            "name", "query", "tenant", "channel", "gap_type", "access_status",
            "confidence", "frequency", "first_seen_on", "last_seen_on", "status",
            "llm_assessment_status", "is_relevant", "relevance_confidence",
            "suggested_context", "suggested_topic", "llm_summary",
            "suggested_knowledge_unit", "suggested_knowledge_source",
            "detection_mode", "visitor_email", "visitor_email_status",
        ],
        order_by="frequency desc, last_seen_on desc",
        limit_page_length=int(limit),
    )

    # Count by status for the summary header
    all_rows = frappe.get_all(
        "Nexus Knowledge Gap",
        filters={"tenant": tenant} if tenant else {},
        fields=["status", "gap_type", "is_relevant", "visitor_email_status"],
    )
    counts = {"total": len(all_rows), "new": 0, "relevant": 0, "no_context": 0, "low_confidence": 0, "pending_followup": 0}
    for r in all_rows:
        if r.status == "New":
            counts["new"] += 1
        if r.is_relevant:
            counts["relevant"] += 1
        if r.gap_type == "No Context":
            counts["no_context"] += 1
        if r.gap_type == "Low Confidence":
            counts["low_confidence"] += 1
        if r.visitor_email_status == "Pending":
            counts["pending_followup"] += 1

    return {"gaps": rows, "counts": counts}


@frappe.whitelist()
def update_gap_status(gap_name, status, action_notes=None):
    """Set status on a gap and record who actioned it."""
    if not gap_name:
        frappe.throw("Gap name is required.")
    valid = ("New", "Under Review", "Watching", "Actioned", "Dismissed")
    if status not in valid:
        frappe.throw(f"Status must be one of: {', '.join(valid)}")

    updates = {"status": status}
    if status in ("Actioned", "Dismissed"):
        updates["actioned_by"] = frappe.session.user
        updates["actioned_on"] = now_datetime()
    if action_notes:
        updates["action_notes"] = action_notes

    frappe.db.set_value("Nexus Knowledge Gap", gap_name, updates)
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist()
def link_knowledge_unit(gap_name, knowledge_unit_name):
    """Link a knowledge unit to a gap and mark it Actioned."""
    if not gap_name or not knowledge_unit_name:
        frappe.throw("Gap name and Knowledge Unit name are required.")
    frappe.db.set_value("Nexus Knowledge Gap", gap_name, {
        "suggested_knowledge_unit": knowledge_unit_name,
        "status": "Actioned",
        "actioned_by": frappe.session.user,
        "actioned_on": now_datetime(),
    })
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist()
def create_knowledge_unit_from_gap(gap_name, title=None, context=None, topic=None, content=None):
    """
    Create a Nexus Knowledge Unit draft from a gap record using admin-provided content.
    The LLM suggestion (suggested_topic, suggested_context, llm_summary) is available
    on the gap record for reference, but the actual content must be supplied by the admin.
    Returns the new unit name so the UI can navigate to it.
    """
    if not content or not content.strip():
        frappe.throw("Knowledge content is required. Please write the content before creating the unit.")

    gap = frappe.get_doc("Nexus Knowledge Gap", gap_name)

    unit = frappe.new_doc("Nexus Knowledge Unit")
    unit.title = (title or gap.suggested_topic or gap.query[:80]).strip()
    unit.tenant = gap.tenant or None
    unit.context = (context or gap.suggested_context or "").strip()
    unit.topic = (topic or gap.suggested_topic or "").strip()
    unit.status = "Draft"
    unit.source_type = "Manual"
    unit.content = content.strip()
    unit.insert(ignore_permissions=True)

    frappe.db.set_value("Nexus Knowledge Gap", gap_name, {
        "suggested_knowledge_unit": unit.name,
        "status": "Under Review",
    })
    frappe.db.commit()

    return {"unit_name": unit.name}


@frappe.whitelist()
def create_knowledge_source_from_gap(gap_name, title=None, business_unit=None, context=None,
                                      sub_context=None, topic=None, access_policy=None, manual_content=None):
    """
    Create a Nexus Knowledge Source (Manual type) from a gap record.
    The source goes through the normal pipeline: classify → chunks → embeddings → publish.
    """
    if not manual_content or not manual_content.strip():
        frappe.throw("Knowledge content is required. Please write the content before creating the source.")

    gap = frappe.get_doc("Nexus Knowledge Gap", gap_name)

    source = frappe.new_doc("Nexus Knowledge Source")
    source.title = (title or gap.suggested_topic or gap.query[:80]).strip()
    source.source_type = "Manual"
    source.tenant = gap.tenant or None
    source.business_unit = business_unit or None
    source.context = (context or gap.suggested_context or "").strip()
    source.sub_context = (sub_context or "").strip()
    source.topic = (topic or gap.suggested_topic or "").strip()
    source.access_policy = access_policy or None
    source.manual_content = manual_content.strip()
    source.status = "Draft"
    source.insert(ignore_permissions=True, ignore_mandatory=True)

    frappe.db.set_value("Nexus Knowledge Gap", gap_name, {
        "suggested_knowledge_source": source.name,
        "status": "Under Review",
    })
    frappe.db.commit()

    return {"source_name": source.name}


@frappe.whitelist()
def trigger_reassessment(gap_name):
    """Manually re-trigger the LLM assessment for a gap."""
    gap = frappe.get_doc("Nexus Knowledge Gap", gap_name)
    frappe.db.set_value("Nexus Knowledge Gap", gap_name, "llm_assessment_status", "Pending")
    frappe.db.commit()
    frappe.enqueue(
        "digitz_ai_nexus.services.gap_detection_service._assess_gap",
        gap_name=gap_name,
        tenant=gap.tenant or "",
        queue="long",
        timeout=120,
    )
    return {"queued": True}


@frappe.whitelist()
def trigger_proactive_detection(tenant=None):
    """
    Manually trigger proactive gap detection. Enqueued as a background job
    so it does not block the browser. If tenant is provided, runs only for
    that tenant; otherwise runs for all active tenants.
    """
    if tenant:
        frappe.enqueue(
            "digitz_ai_nexus.services.gap_detection_service._run_proactive_detection",
            tenant=tenant,
            queue="long",
            timeout=300,
        )
    else:
        frappe.enqueue(
            "digitz_ai_nexus.services.gap_detection_service.detect_proactive_gaps",
            queue="long",
            timeout=600,
        )
    return {"queued": True}


@frappe.whitelist(allow_guest=True)
def submit_gap_visitor_email(gap_name, email, conversation_id=None):
    """
    Trusted path: visitor already has a verified email (from identity verification).
    Saves the email directly without OTP. Validates against the conversation record
    when conversation_id is provided so a guest cannot substitute someone else's email.
    """
    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        frappe.throw("Invalid email address.")
    if not frappe.db.exists("Nexus Knowledge Gap", gap_name):
        frappe.throw("Gap not found.")

    if conversation_id:
        conv_email = frappe.db.get_value(
            "Nexus Live Conversation",
            {"conversation_id": conversation_id},
            "visitor_email",
        )
        if conv_email and conv_email.strip().lower() != email:
            frappe.throw("Email does not match the verified conversation email.")

    frappe.db.set_value("Nexus Knowledge Gap", gap_name, {
        "visitor_email": email,
        "visitor_email_status": "Pending",
    })
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist(allow_guest=True)
def request_gap_email_otp(gap_name, email):
    """Send a 6-digit OTP to the visitor's email so they can verify it before being saved."""
    import hashlib
    import random
    from digitz_ai_nexus_live.services.rate_limit import check_rate_limit, get_caller_ip

    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        frappe.throw("Invalid email address.")
    if not frappe.db.exists("Nexus Knowledge Gap", gap_name):
        frappe.throw("Gap not found.")

    check_rate_limit(
        f"gap_otp_req:{email}",
        max_calls=5, window_seconds=600,
        throw_message="Too many OTP requests for this email. Please wait before trying again.",
    )
    check_rate_limit(
        f"gap_otp_req_ip:{get_caller_ip()}",
        max_calls=10, window_seconds=60,
        throw_message="Too many OTP requests. Please slow down.",
    )

    otp = f"{random.SystemRandom().randint(100000, 999999)}"
    challenge_token = frappe.generate_hash(length=32)
    otp_hash = hashlib.sha256(f"{challenge_token}:{otp}".encode()).hexdigest()

    frappe.cache().set_value(
        f"gap_email_otp:{challenge_token}",
        {"gap_name": gap_name, "email": email, "otp_hash": otp_hash, "attempts": 0},
        expires_in_sec=600,
    )

    try:
        # frappe.sendmail(template=) looks for a file, not an Email Template doc.
        # Render the doctype record manually then send with explicit subject/message.
        tmpl = frappe.get_doc("Email Template", _GAP_OTP_TEMPLATE)
        ctx  = {"otp": otp, "validity_minutes": _GAP_OTP_VALIDITY_MINUTES}
        frappe.sendmail(
            recipients=[email],
            subject=frappe.render_template(tmpl.subject, ctx),
            message=frappe.render_template(tmpl.response, ctx),
            delayed=True,
        )
    except Exception:
        import traceback as _tb
        frappe.log_error(
            title="Nexus Gap OTP (email not configured)",
            message=f"OTP for {email}: {otp}\n\n{_tb.format_exc()}",
        )

    return {"status": "sent", "challenge_token": challenge_token, "email": email}


@frappe.whitelist(allow_guest=True)
def verify_gap_email_otp(gap_name, challenge_token, otp):
    """Verify the OTP and save the visitor email on the gap record."""
    import hashlib

    cache_key = f"gap_email_otp:{challenge_token}"
    data = frappe.cache().get_value(cache_key)

    if not data:
        frappe.throw("Verification code has expired or is invalid. Please request a new one.")
    if data.get("gap_name") != gap_name:
        frappe.throw("Invalid verification request.")

    attempts = int(data.get("attempts") or 0)
    if attempts >= 5:
        frappe.cache().delete_value(cache_key)
        frappe.throw("Maximum verification attempts exceeded. Please request a new code.")

    data["attempts"] = attempts + 1
    frappe.cache().set_value(cache_key, data, expires_in_sec=600)

    otp_hash = hashlib.sha256(f"{challenge_token}:{str(otp).strip()}".encode()).hexdigest()
    if otp_hash != data.get("otp_hash"):
        remaining = 5 - data["attempts"]
        msg = "Invalid code."
        if remaining > 0:
            msg += f" {remaining} attempt(s) remaining."
        frappe.throw(msg)

    email = data["email"]
    frappe.db.set_value("Nexus Knowledge Gap", gap_name, {
        "visitor_email": email,
        "visitor_email_status": "Pending",
    })
    frappe.db.commit()
    frappe.cache().delete_value(cache_key)
    return {"success": True, "email": email}


@frappe.whitelist()
def notify_gap_visitor(gap_name):
    """Manually send follow-up email to visitor and mark gap as Notified."""
    from digitz_ai_nexus.services.gap_notification_service import send_visitor_notification

    gap = frappe.get_doc("Nexus Knowledge Gap", gap_name)
    if not gap.visitor_email:
        frappe.throw("No visitor email recorded for this gap.")
    if gap.visitor_email_status != "Pending":
        frappe.throw("Visitor has already been notified or no notification is pending.")

    send_visitor_notification(gap_name)
    return {"success": True}


@frappe.whitelist()
def get_sample_queries(gap_name):
    """Return the stored sample queries for a gap."""
    import json
    raw = frappe.db.get_value("Nexus Knowledge Gap", gap_name, "sample_queries_json") or "[]"
    try:
        return {"samples": json.loads(raw)}
    except Exception:
        return {"samples": []}
