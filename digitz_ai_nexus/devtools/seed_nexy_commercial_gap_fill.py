"""
Gap-fill seed for NEXUS AI COMMERCIAL knowledge.

Adds the commercial knowledge sources that back the home-page benefit claims
(website/WhatsApp customer support, Contacts Intelligence, Offers & AI Push,
verified support flow) and amends two existing sources for consistency:
- Lead Generation overview: softens the "not a support tool" positioning
- Communication Channels: documents email outreach as a planned channel

Usage:
    bench --site digitz_ai_nexus_staging.site execute \
        digitz_ai_nexus.devtools.seed_nexy_commercial_gap_fill.run

    Dry run (create/update records without chunking + embedding):
    bench --site digitz_ai_nexus_staging.site execute \
        digitz_ai_nexus.devtools.seed_nexy_commercial_gap_fill.run \
        --kwargs '{"process_sources": False}'

Idempotent — safe to re-run. Classification and governance fields are copied
from an existing published commercial source, so the new records always match
whatever policy/category the live records actually use.
"""

import frappe

from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source


CONTEXT = "NEXUS AI COMMERCIAL"

# Existing published source whose tenant/business_unit/access_policy/chat_category
# are copied onto every new record.
SIBLING_TITLE = "Nexus Nexy Companion Framework — Intelligent Conversation Engine"


# ── New knowledge sources ──────────────────────────────────────────────────────

NEW_SOURCES = [

    # 1 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexy Companion — AI Website Customer Support",
        "sub_context": "Customer Support",
        "entity_type": "Commercial",
        "entity": "Nexy Companion",
        "topic": "Website Customer Support from Approved Knowledge",
        "priority": 9,
        "manual_content": """
## Customer Support on the Website

Nexy's primary strength is lead generation and sales — but the same companion also provides customer support through the website chat widget. Businesses use Nexy to give customers instant, accurate answers drawn from their approved business knowledge, without waiting for a human agent to become available.

Website customer support with Nexy covers:

**Knowledge-based answers.** Customers ask questions about products, services, policies, procedures, or processes, and Nexy answers from the business's approved knowledge base. Every factual answer is retrieved from governed knowledge — Nexy does not guess, improvise, or invent support answers.

**Service clarification.** When a customer is unsure what a service includes, how a process works, or what the next step is, Nexy explains it using the business's own approved wording.

**Issue collection.** When a customer reports a problem, Nexy collects the relevant details in a structured way — what happened, what the customer was trying to do, and any context the support team will need. The full conversation record is available to the desk team, so the customer never has to repeat themselves.

**Support escalation.** When the question is outside the approved knowledge, when the case is sensitive, or when the customer asks for a person, Nexy escalates to a human desk agent with the full conversation context attached. The desk agent joins with everything already gathered.

## What Keeps Support Trustworthy

Nexy only answers support questions from knowledge the business has approved and published. If the knowledge base does not cover a question, Nexy says so honestly and offers to route the question to the team instead of guessing. This is the same governance that applies to every Nexy conversation.

## How Support and Sales Work Together

The same website widget serves both flows. Visitors choosing a support-oriented category get the support experience; visitors choosing the Business Companion get the sales discovery experience. Both run on the same knowledge base and the same escalation infrastructure, so the business maintains one governed platform for every conversation type.

For visitors asking whether Nexy can handle customer support on their website: yes — support chat, knowledge-based answers, issue collection, and human escalation are all part of the Nexy Companion Framework included in every Nexus Orbit plan.
""",
    },

    # 2 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexy Companion — WhatsApp Customer Support",
        "sub_context": "Customer Support",
        "entity_type": "Commercial",
        "entity": "Nexy Companion",
        "topic": "Customer Support over WhatsApp",
        "priority": 9,
        "manual_content": """
## Customer Support over WhatsApp

Customers increasingly expect support where they already are — on WhatsApp. Nexy extends the same governed support experience from the website to the business's WhatsApp Business number.

When a customer messages the business on WhatsApp, Nexy responds using the same approved knowledge base, the same behaviour configuration, and the same escalation rules as the website chat. There is no separate WhatsApp support setup.

WhatsApp customer support with Nexy covers:

**Question answering.** Customers ask about products, services, orders, policies, or procedures and receive answers drawn from the business's approved knowledge — the same governed answers they would get on the website.

**Issue collection.** Customers can describe a problem in their own words. Nexy gathers the details in a structured way and records them for the support team. Image, audio, video, and document messages sent by the customer are received and noted in the conversation record.

**Guided responses.** For known processes — how to request a return, how to reschedule, what information is needed for a claim — Nexy walks the customer through the steps as approved in the knowledge base.

**Human handover.** When the situation requires a person — a sensitive case, a complaint, a question outside the knowledge base, or an explicit request — Nexy hands the conversation to a desk agent through the Nexus Live console. The agent joins the same WhatsApp conversation with the full history visible.

## Capacity and Inclusion

WhatsApp customer support runs on the same WhatsApp Outreach capacity included in every Nexus Orbit plan. Support messages count toward the plan's monthly WhatsApp message capacity, exactly like outreach messages. No separate subscription is required — the WhatsApp Business integration is configured once during onboarding.

For visitors asking whether their customers can get support through WhatsApp: yes — AI-powered support conversations, issue collection, and human handover on WhatsApp are included in every plan.
""",
    },

    # 3 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Contacts Intelligence — Central Contact and Relationship Layer",
        "sub_context": "Contacts Intelligence",
        "entity_type": "Commercial",
        "entity": "Nexus Contacts Intelligence",
        "topic": "Contact Profiles, Product Fit and Segmentation",
        "priority": 9,
        "manual_content": """
## What Is Nexus Contacts Intelligence?

Nexus Contacts Intelligence is the central relationship layer of the Nexus platform. It brings every lead, prospect, customer, and business contact into one intelligent system — so the business is not managing scattered records, but working with living contact intelligence.

Contacts enter the layer from every direction: Nexy website conversations that convert into contact records, WhatsApp conversations, and imported lists (Facebook ad leads, event registrants, existing customer lists). Every Nexy conversation that concludes enriches the contact with discovery data, persona match, enquiry score, and journey stage — automatically, with no manual data entry.

## What the Intelligence Layer Understands

**Contact profiles.** Who the contact is: their business, industry, role, history with the business, and everything Nexy has learned across conversations.

**Product-fit matching.** Contacts are mapped against the business's products and services to identify which offering fits which contact. This produces product-fit recommendations that guide what Nexy talks to each contact about.

**Smart segmentation.** Contacts are grouped into segments — by persona, industry, journey stage, product fit, or engagement level. Segments are the targeting unit for outreach: an Engagement Campaign selects a segment, and Nexy reaches out to exactly that audience.

**Relationship journey.** Each contact has a position in the relationship journey — from first touch through qualification to customer and repeat engagement. Contacts Intelligence tracks that position and what the sensible next step is, so systematic messaging over time reaches the right contact with the right message at the right stage.

## Nexy Acting on Contact Intelligence

Contacts Intelligence identifies the opportunity; Nexy executes the conversation. Nexy uses the contact's profile, product-fit recommendations, and journey position to prepare personalised outreach, carry the reply conversation, and update the contact's journey based on what happens. This is what makes Nexy an orchestrator rather than a chatbot — it acts with the full relationship context behind every message.

## Channels

Contact outreach runs on WhatsApp today, using the WhatsApp Outreach capacity included in every plan and the campaign approval controls that govern all proactive messaging. Email outreach — cold emails, follow-up sequences, and reply drafting — is a planned channel on the Nexus roadmap and is not yet live. Businesses interested in email outreach can register that interest through a demo or consultation.

## Boundary — CRM Systems

Nexus Contacts Intelligence is the platform's own relationship layer. Connecting Nexus to an external CRM or ERP — reading from or writing back to those systems — is available through the Custom Engagement option, which is scoped and priced separately from the standard Orbit plans.

For visitors asking what Contacts Intelligence gives them: one central intelligence layer for all contacts, product-fit recommendations, smart segmentation, and the relationship context Nexy needs to run meaningful outreach and move contacts toward qualified business outcomes.
""",
    },

    # 4 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Offers Management and AI Push",
        "sub_context": "Offers",
        "entity_type": "Commercial",
        "entity": "Nexus Offers",
        "topic": "Offer Management, WhatsApp Offer Push, and AI Offer Interaction",
        "priority": 9,
        "manual_content": """
## Offers Management and AI Push

Businesses run offers — seasonal promotions, service bundles, introductory pricing, loyalty benefits. Nexus lets the business manage those offers on the platform and promote them through WhatsApp with Nexy handling the conversation.

## How Offer Push Works

Offer promotion uses the same campaign machinery as all proactive Nexy outreach. The business selects a contact segment from Nexus Contacts Intelligence — for example, contacts matched to a product the offer applies to — and runs a campaign that sends a personalised offer message to each contact in the segment.

The controls that govern all proactive messaging apply to offers as well: messages can be queued for human review before dispatch, contacts marked Do Not Contact are skipped automatically, and cold contact outside the 24-hour WhatsApp window uses pre-approved WhatsApp Business templates.

## Nexy Handles the Offer Conversation

The difference between an offer push and a broadcast blast is what happens after the message lands. When a contact replies — asks a question, wants details, raises a doubt — Nexy picks up the conversation immediately:

**Explaining benefits.** Nexy explains what the offer includes and how it applies to the contact's situation, using the offer details the business has approved.

**Answering queries.** Questions about eligibility, duration, scope, or terms are answered from approved knowledge. Nexy does not invent discounts, extend validity, or improvise terms that the business has not configured — if a detail is not in the approved offer knowledge, Nexy says so and offers to have the team confirm.

**Guiding toward action.** Interested contacts are guided to the next step the business has configured — an enquiry, a booking, a demo request, or a handover to a team member. Every offer conversation is scored like any other Nexy conversation, so the sales desk sees which contacts engaged and who is ready to act.

For visitors asking whether they can promote offers through AI on WhatsApp: yes — offer campaigns to selected contact segments, AI-handled replies, and guided next steps are part of the platform, governed by the same approval and consent controls as all Nexy outreach.
""",
    },

    # 5 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexy as Support Companion — Verified Identity Support Flow",
        "sub_context": "Customer Support",
        "entity_type": "Commercial",
        "entity": "Nexy Companion",
        "topic": "Verified Support Flow: Identity Verification to Desk Handoff",
        "priority": 9,
        "manual_content": """
## Support for Registered Identities

Public visitors and registered customers are not the same — and Nexy treats them differently. For registered identities (existing customers, business partners, account holders), Nexy runs a structured, trusted support flow that starts with verification and ends with the right resolution path.

## The Verified Support Flow

**1. Registered identity.** The customer identifies themselves in the chat. Identity-based routing means registered visitors can receive a different experience and different knowledge access than anonymous public visitors — through the same widget.

**2. Identity verification.** Before any account-specific support proceeds, Nexy verifies the customer — an email verification code confirms the person is who they say they are. Unverified visitors are never given access to identity-scoped information.

**3. Issue understanding.** Once verified, Nexy asks focused questions to understand the issue: what the customer was doing, what went wrong, and what outcome they need. The issue is captured in a structured form the support team can act on.

**4. Guided assistance.** Where the approved knowledge base covers the situation — known procedures, how-to steps, policy clarifications — Nexy resolves it directly in the conversation, using only governed knowledge.

**5. Ticket or desk handoff.** When the issue needs a person, Nexy hands over: the conversation routes to a desk agent on the Nexus Live console, or the issue is recorded for the support team to follow up — with the verified identity, the structured issue description, and the full conversation attached.

## Why Verification Matters

Verification protects both sides. The customer's account details are only discussed with the verified account holder, and the support team receives cases that are already authenticated — no callback loops to confirm who they are talking to.

## Access Governance

Verified identities can be granted access to knowledge that public visitors cannot see — customer-only procedures, account documentation, or partner material — through the platform's access policies. The same conversation widget serves public visitors with public knowledge and verified customers with their permitted knowledge, without any risk of leakage between the two.

For visitors asking how support works for their existing customers: Nexy verifies the customer's identity, understands the issue in a structured way, resolves what approved knowledge covers, and hands the rest to the right team member with full context.
""",
    },
]


# ── Amendments to existing sources ─────────────────────────────────────────────
# Each amendment is a list of exact (old, new) replacements on manual_content.

AMENDMENTS = [
    {
        "title": "Nexy Companion — Lead Generation and Sales Overview",
        "replacements": [
            (
                "This is what makes Nexy a lead generation and sales tool "
                "rather than a general support tool.",

                "Lead generation and sales is Nexy's primary focus. Alongside it, "
                "the same companion also handles customer-support conversations — "
                "answering customer questions from the business's approved knowledge, "
                "collecting issue details, and escalating to a human when needed — "
                "so one governed companion serves both new prospects and existing customers.",
            ),
        ],
    },
    {
        "title": "Nexy Companion — Communication Channels",
        "replacements": [
            (
                "Additional channels can be connected to the same Nexy configuration "
                "without requiring changes to knowledge, personas, or playbooks.",

                "Additional channels can be connected to the same Nexy configuration "
                "without requiring changes to knowledge, personas, or playbooks.\n\n"
                "Email outreach — cold emails, follow-up sequences, and reply drafting — "
                "is a planned channel on the Nexus roadmap and is not yet live. "
                "For visitors asking whether Nexy can send emails today: the two live "
                "channels are website chat and WhatsApp. Email outreach is upcoming, and "
                "businesses interested in it can raise it during a demo or consultation "
                "so the Nexus team can share timelines.",
            ),
        ],
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_sibling_fields():
    """Copy governance/classification fields from a live published commercial source."""
    sibling = frappe.get_doc("Nexus Knowledge Source", SIBLING_TITLE)
    fields = {
        "tenant": sibling.tenant,
        "business_unit": sibling.business_unit or "",
        "access_policy": sibling.access_policy,
        "context": sibling.context,
    }
    if sibling.meta.has_field("chat_category"):
        fields["chat_category"] = sibling.get("chat_category")
    return fields


def _upsert_source(source, sibling_fields):
    title = source["title"]

    if frappe.db.exists("Nexus Knowledge Source", title):
        doc = frappe.get_doc("Nexus Knowledge Source", title)
    else:
        doc = frappe.new_doc("Nexus Knowledge Source")
        doc.title = title

    doc.source_type = "Manual"
    doc.manual_content = source["manual_content"].strip()
    doc.project = ""
    doc.sub_context = source["sub_context"]
    doc.entity_type = source["entity_type"]
    doc.entity = source["entity"]
    doc.topic = source["topic"]
    doc.priority = source.get("priority", 9)

    for fieldname, value in sibling_fields.items():
        doc.set(fieldname, value)

    doc.status = "Published"
    doc.processing_status = "Pending"
    doc.embedding_status = "Pending"
    doc.diagnostics_status = "Pending"
    doc.retrieval_ready = 0

    doc.save(ignore_permissions=True)

    # The validate hook resets status to Draft whenever watched fields change
    # (reset_readiness_if_source_changed). The processor only activates chunks
    # when status is Published at processing time — force it back via db_set,
    # which bypasses validate.
    frappe.db.set_value(
        "Nexus Knowledge Source", doc.name, "status", "Published",
        update_modified=False,
    )
    doc.reload()
    return doc


def _apply_amendment(amendment):
    title = amendment["title"]
    doc = frappe.get_doc("Nexus Knowledge Source", title)
    content = doc.manual_content or ""

    applied, skipped = 0, 0
    for old, new in amendment["replacements"]:
        if new in content:
            skipped += 1  # already amended — idempotent re-run
        elif old in content:
            content = content.replace(old, new)
            applied += 1
        else:
            return doc, {"error": f"marker not found in '{title}': {old[:80]}..."}

    if applied:
        doc.manual_content = content
        doc.save(ignore_permissions=True)
        # Content change → validate hook resets status to Draft and disables
        # chunks. Re-publish via db_set so reprocessing creates ACTIVE chunks.
        frappe.db.set_value(
            "Nexus Knowledge Source", doc.name, "status", "Published",
            update_modified=False,
        )
        doc.reload()

    return doc, {"applied": applied, "already_applied": skipped}


def _finalize_source(source_name):
    """
    Complete the knowledge-ready workflow after processing, mirroring
    devtools/finalize_nexus_public_knowledge.py:

      1. Approve generated User Question index entries (processor leaves them
         Pending Review, and retrieval_ready stays 0 until all are approved).
      2. Rebuild question correlations.
      3. Recount active chunks and set validation Passed / ready_to_publish /
         Published / retrieval_ready via direct DB update (bypasses the
         validate hook that would reset readiness).
    """
    now = frappe.utils.now_datetime()
    user = frappe.session.user

    unit_name = frappe.db.get_value(
        "Nexus Knowledge Source", source_name, "generated_knowledge_unit"
    )

    # 1. Approve pending User Question entries
    pending = frappe.get_all(
        "Nexus Knowledge Index Entry",
        filters={
            "knowledge_source": source_name,
            "entry_type": "User Question",
            "answer_review_status": ["in", ["Pending Review", "Rejected"]],
        },
        pluck="name",
    )
    for entry_name in pending:
        frappe.db.set_value(
            "Nexus Knowledge Index Entry",
            entry_name,
            {
                "answer_review_status": "Approved",
                "answer_reviewed_by": user,
                "answer_reviewed_on": now,
            },
            update_modified=False,
        )

    # 2. Rebuild question correlations
    from digitz_ai_nexus.services.question_correlation import (
        build_question_correlations_for_source,
    )
    try:
        build_question_correlations_for_source(source_name)
    except Exception as exc:
        frappe.log_error(str(exc), f"Gap fill: correlation rebuild failed for {source_name}")

    # 3. Validation + publish + retrieval_ready
    active_chunks = frappe.db.count(
        "Nexus Knowledge Chunk",
        {
            "knowledge_unit": unit_name,
            "disabled": 0,
            "archived": 0,
            "embedding_status": "Completed",
        },
    ) if unit_name else 0

    total_q = frappe.db.count(
        "Nexus Knowledge Index Entry",
        {"knowledge_source": source_name, "entry_type": "User Question"},
    )
    approved_q = frappe.db.count(
        "Nexus Knowledge Index Entry",
        {
            "knowledge_source": source_name,
            "entry_type": "User Question",
            "answer_review_status": "Approved",
        },
    )
    strict_ready = 1 if total_q > 0 and approved_q == total_q else 0
    retrieval_ready = 1 if active_chunks > 0 and strict_ready else 0

    frappe.db.set_value(
        "Nexus Knowledge Source",
        source_name,
        {
            "validation_status": "Passed",
            "ready_to_publish": 1,
            "needs_review": 0,
            "review_reason": "",
            "status": "Published",
            "active_chunk_count": active_chunks,
            "retrieval_ready": retrieval_ready,
            "validated_on": now,
            "validated_by": user,
        },
        update_modified=False,
    )
    frappe.db.commit()

    return {
        "questions_approved_now": len(pending),
        "user_questions": f"{approved_q}/{total_q}",
        "active_chunks": active_chunks,
        "retrieval_ready": retrieval_ready,
    }


# ── Main entry point ───────────────────────────────────────────────────────────

def run(process_sources=True):
    """
    Idempotent gap-fill seed for NEXUS AI COMMERCIAL knowledge.

    Args:
        process_sources (bool): If True, runs chunking and embedding after each
                                create/amend. False = dry run (records only).
    """
    print("\n" + "=" * 70)
    print("  Nexy Commercial Gap Fill — NEXUS AI COMMERCIAL")
    print("=" * 70)

    sibling_fields = _get_sibling_fields()
    print(f"\n  Sibling template     : {SIBLING_TITLE}")
    print(f"  Tenant               : {sibling_fields.get('tenant')}")
    print(f"  Access Policy        : {sibling_fields.get('access_policy')}")
    print(f"  Context              : {sibling_fields.get('context')}")

    results = []

    print(f"\n  New Knowledge Sources ({len(NEW_SOURCES)}):")
    for source in NEW_SOURCES:
        doc = _upsert_source(source, sibling_fields)
        entry = {"title": doc.title, "action": "upserted"}
        if process_sources:
            try:
                entry["processing"] = process_knowledge_source(doc.name)
                entry["finalize"] = _finalize_source(doc.name)
                flag = "OK" if entry["finalize"].get("retrieval_ready") else "WARN"
            except Exception as e:
                entry["processing_error"] = str(e)
                flag = "ERR"
        else:
            flag = "SKIP"
        print(f"    [{flag}] {doc.title[:66]} — {entry.get('finalize', '')}")
        results.append(entry)

    print(f"\n  Amendments ({len(AMENDMENTS)}):")
    for amendment in AMENDMENTS:
        doc, status = _apply_amendment(amendment)
        entry = {"title": amendment["title"], "amendment": status}
        if status.get("error"):
            flag = "ERR"
        elif process_sources:
            try:
                # Reprocess only when content actually changed; finalize always
                # (repairs readiness even if a previous run left it incomplete).
                if status.get("applied"):
                    entry["processing"] = process_knowledge_source(doc.name)
                entry["finalize"] = _finalize_source(doc.name)
                # Repair: a previous run may have processed while the reset hook
                # had the source in Draft, leaving all chunks inactive. The
                # source is Published now — reprocess to regenerate active chunks.
                if not entry["finalize"].get("active_chunks"):
                    entry["processing"] = process_knowledge_source(doc.name)
                    entry["finalize"] = _finalize_source(doc.name)
                flag = "OK" if entry["finalize"].get("retrieval_ready") else "WARN"
            except Exception as e:
                entry["processing_error"] = str(e)
                flag = "ERR"
        else:
            flag = "SKIP"
        print(f"    [{flag}] {amendment['title'][:66]} — {status} — {entry.get('finalize', '')}")
        results.append(entry)

    frappe.db.commit()

    print("\n" + "=" * 70)
    print(f"  Gap Fill Complete — {len(results)} records touched")
    print("=" * 70 + "\n")

    return results
