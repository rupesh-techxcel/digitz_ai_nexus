"""
Gap Notification Service

Handles automatic visitor email notifications when a Knowledge Source linked
to a Knowledge Gap is published. Also provides the shared send logic used by
the manual API endpoint.
"""

import frappe

_GAP_FOLLOWUP_TEMPLATE = "nexus-gap-visitor-followup"


def send_visitor_notification(gap_name):
    """
    Send follow-up email to the visitor recorded on a Knowledge Gap and
    mark the gap as Notified. Safe to call from both manual and automatic
    paths — idempotent by design.

    The status is committed to "Notified" BEFORE the email is dispatched so
    that any concurrent caller (e.g. manual Notify button fired at the same
    moment as the auto-publish trigger) reads the updated status and exits
    immediately, preventing duplicate emails.

    Returns True if email was sent, False if skipped.
    """
    # Read the freshest state directly from the DB (not ORM cache) so a
    # concurrent call that already committed "Notified" is visible here.
    current = frappe.db.get_value(
        "Nexus Knowledge Gap",
        gap_name,
        ["visitor_email", "visitor_email_status", "query", "suggested_topic", "tenant"],
        as_dict=True,
    )

    if not current or not current.visitor_email or current.visitor_email_status != "Pending":
        return False

    # Claim the notification slot before sending — any concurrent path that
    # reads after this commit will see "Notified" and exit.
    frappe.db.set_value("Nexus Knowledge Gap", gap_name, "visitor_email_status", "Notified")
    frappe.db.commit()

    tenant_name = (
        frappe.db.get_value("Nexus Tenant", current.tenant, "tenant_name") if current.tenant else None
    ) or current.tenant or "Support"

    frappe.sendmail(
        recipients=[current.visitor_email],
        template=_GAP_FOLLOWUP_TEMPLATE,
        args={
            "gap_query": current.query,
            "gap_topic": current.suggested_topic or current.query[:80],
            "tenant_name": tenant_name,
        },
        delayed=False,
    )
    return True


def on_knowledge_source_published(doc, method):
    """
    Document event handler: Nexus Knowledge Source → on_update.

    When a source transitions TO Published status, find all Knowledge Gaps
    that reference it via suggested_knowledge_source and have a pending
    visitor email, then auto-send the notification for each.
    """
    if doc.status != "Published":
        return

    # Only act on the transition, not on repeated saves in Published state
    before = doc.get_doc_before_save()
    if before and before.status == "Published":
        return

    pending_gaps = frappe.get_all(
        "Nexus Knowledge Gap",
        filters={
            "suggested_knowledge_source": doc.name,
            "visitor_email_status": "Pending",
        },
        pluck="name",
    )

    if not pending_gaps:
        return

    for gap_name in pending_gaps:
        try:
            sent = send_visitor_notification(gap_name)
            if sent:
                frappe.logger().info(
                    "Auto-notified gap visitor: gap=%s source=%s", gap_name, doc.name
                )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Auto-notify gap visitor failed: gap={gap_name} source={doc.name}",
            )
