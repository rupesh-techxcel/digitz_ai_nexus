"""
NEXUS AI — Nexy Commercial Configuration Seed
==============================================
Standalone, idempotent seed that wires the complete Nexy Commercial
configuration for the NEXUS-AI tenant.

Creates or updates:
  - Access Policy        : NEXUS-COMMERCIAL-ACCESS  (Public level — commercial visitor knowledge)
  - Access Category      : NEXUS-COMMERCIAL  (scoped to NEXUS-COMMERCIAL-ACCESS policy)
  - Knowledge Profile    : NEXUS-COMMERCIAL-KNOWLEDGE-PROFILE  (title: Nexus Commercial Knowledge Profile)
  - Chat Channel         : NEXUS-AI-WEBSITE-CHAT  (reused if already present)
  - Chat Category        : NEXUS-COMMERCIAL  (label "Commercial Enquiry")
  - Nexy Role Profile    : NEXY-COMMERCIAL  (Sales, consultative companion)
  - Nexy Sales Extension : linked to NEXY-COMMERCIAL profile
  - Nexy Companion Assignment : wires NEXUS-COMMERCIAL → NEXY-COMMERCIAL
  - 6 Nexus Knowledge Sources covering:
      Plans & Pricing, Nexy Companion Framework, WhatsApp Outreach,
      Onboarding & Getting Started, Demo Request Process,
      Custom Engagement (CRM + Business Orchestration)

NOT called during installation. Run manually:

    bench --site digitz_ai_nexus_staging.site execute \
        digitz_ai_nexus.devtools.seed_nexy_commercial.run

To skip embedding generation:

    bench --site digitz_ai_nexus_staging.site execute \
        digitz_ai_nexus.devtools.seed_nexy_commercial.run \
        --kwargs '{"process_sources": False}'
"""

import frappe

from digitz_ai_nexus.setup.access_seed import ensure_access_policy, ensure_access_category
from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source


# ── Identity constants ─────────────────────────────────────────────────────────

TENANT                   = "NEXUS-AI"
POLICY_NAME              = "NEXUS-COMMERCIAL-ACCESS"
ACCESS_CATEGORY          = "NEXUS-COMMERCIAL"
KNOWLEDGE_PROFILE_CODE   = "NEXUS-COMMERCIAL-KNOWLEDGE-PROFILE"
KNOWLEDGE_PROFILE_TITLE  = "Nexus Commercial Knowledge Profile"
CHANNEL_CODE             = "NEXUS-AI-WEBSITE-CHAT"
CHAT_CATEGORY_CODE       = "NEXUS-COMMERCIAL"
CHAT_CATEGORY_LABEL      = "Nexus Companion"
ROLE_PROFILE_CODE        = "NEXY-COMMERCIAL"
CONTEXT                  = "NEXUS AI COMMERCIAL"


# ── Knowledge source definitions ───────────────────────────────────────────────

COMMERCIAL_SOURCES = [

    # 1 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Orbit Plans — Pricing, Capacity, and Annual Subscription Overview",
        "sub_context": "Pricing and Plans",
        "entity_type": "Commercial",
        "entity": "Nexus Orbit Plans",
        "topic": "Plans Overview, Pricing, and Capacity Limits",
        "priority": 10,
        "manual_content": """
NEXUS AI offers four Orbit subscription plans — Orbit Lite, Orbit, Orbit Pro, and Orbit Command. All plans are billed annually and include the Nexy Companion Framework and WhatsApp Outreach capacity as standard. Every plan runs on the same governed platform; the difference is capacity, scale, and team size.

Orbit Lite — $1,400 per year ($117 per month equivalent)
One-time onboarding: $750
Users: up to 4
Knowledge Sources: up to 200
Conversations per month: 2,000 (overage: +$25 per 2,000 conversations)
WhatsApp Messages per month: 2,000 (overage: +$25 per 2,000 messages)
Conversation Playbooks: 2
AI Personas: 2
Best for: small businesses wanting governed AI for their website and WhatsApp with minimal overhead.

Orbit — $3,600 per year ($300 per month equivalent)
One-time onboarding: $1,500
Users: up to 10
Knowledge Sources: up to 200
Conversations per month: 5,000 (overage: +$25 per 2,000 conversations)
WhatsApp Messages per month: 5,000 (overage: +$25 per 2,000 messages)
Conversation Playbooks: 4
AI Personas: 5
Best for: growing businesses ready to deploy AI across sales, support, and WhatsApp engagement at scale.

Orbit Pro — $6,600 per year ($550 per month equivalent)
One-time onboarding: $2,500
Users: up to 30
Knowledge Sources: up to 500
Conversations per month: 12,000 (overage: +$20 per 1,000 conversations)
WhatsApp Messages per month: 12,000 (no WhatsApp overage on Pro)
Conversation Playbooks: 6
AI Personas: 10
Best for: established businesses with high conversation volume, multiple AI personas, and advanced playbook automation.

Orbit Command — $10,800 per year ($900 per month equivalent)
One-time onboarding: $4,000
Users: Unlimited
Knowledge Sources: Unlimited
Conversations per month: Unlimited
WhatsApp Messages per month: Unlimited
Conversation Playbooks: Unlimited
AI Personas: Unlimited
Best for: enterprises and large teams that need full capacity, unlimited scale, and complete control over the platform.

All showcase prices reflect a 30% saving on the standard rate. The crossed-out price shown is the standard rate before the current pricing applies.

If a visitor asks which plan is right for them: ask about their team size, monthly conversation volume, and whether they need WhatsApp integration — then match to the plan capacity that fits without recommending an upgrade beyond what they need.

For demo requests or further commercial discussions, offer to submit a demo request so a Nexus Consultant can contact the visitor directly.
""",
    },

    # 2 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Nexy Companion Framework — Intelligent Conversation Engine",
        "sub_context": "Nexy Companion",
        "entity_type": "Platform Feature",
        "entity": "Nexy Companion Framework",
        "topic": "What Nexy Is, How It Works, Personas and Playbooks",
        "priority": 10,
        "manual_content": """
The Nexy Companion Framework is the intelligent conversation engine included in every Nexus Orbit plan. It is not a simple chatbot. Nexy is a multi-stage companion that classifies visitor intent, matches the right persona, guides the conversation through structured playbooks, and scores enquiries — all powered by governed knowledge retrieval.

How Nexy works — the 11-stage journey:
Every conversation Nexy handles moves through up to 11 defined stages. Each stage represents a natural point in the visitor's engagement arc, from first contact to confirmed next step. The stages are: Opening, Exploring, Qualifying, Presenting, Handling Concerns, Recommending, Confirming, Escalating, Nurturing, Summarising, and Closing.

Nexy does not jump stages randomly. It reads where the visitor is in their journey — from the context of their messages — and advances the conversation appropriately.

14-signal LLM classification:
Before deciding how to respond, Nexy evaluates 14 signals from the conversation to understand the visitor's current state: intent type, urgency, sentiment, knowledge gap, decision stage, identity type, topic domain, escalation readiness, persona match, playbook relevance, response tone, confidence level, grounding requirement, and CTA readiness. This multi-signal classification produces a structured assessment that drives Nexy's next response — grounded in retrieved knowledge, not in invented answers.

AI Personas:
Each plan allows a defined number of AI Personas. A persona is a named, behaviourally distinct version of Nexy configured for a specific audience, tone, or business context. For example, a business might configure one persona for public website visitors using a warm, conversational tone, and a second persona for returning customers using a more concise, action-oriented style.

Orbit Lite: 2 personas
Orbit: 5 personas
Orbit Pro: 10 personas
Orbit Command: Unlimited personas

Conversation Playbooks:
Playbooks are structured conversation scripts that Nexy follows for specific scenarios. A playbook defines the sequence of questions, the information to present, and the conditions that trigger each step. Common playbooks include: product enquiry flow, demo request flow, pricing walkthrough, objection handling, and escalation to human.

Orbit Lite: 2 playbooks
Orbit: 4 playbooks
Orbit Pro: 6 playbooks
Orbit Command: Unlimited playbooks

Enquiry scoring:
Nexy scores every conversation against the business's defined qualification criteria. The score reflects how well the visitor's need matches the business's offering and how ready the visitor is for a next step. High-scoring enquiries can be routed to a human consultant or escalated automatically.

Grounded knowledge:
Every factual claim Nexy makes during a conversation is retrieved from the approved knowledge base — not generated from training data. If no approved knowledge covers the visitor's question, Nexy acknowledges this honestly rather than inventing an answer.

Nexy is the same across all plans — the platform capability is identical. What varies is the number of personas, playbooks, and conversation volume you can deploy.
""",
    },

    # 3 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus WhatsApp Outreach — Capacity, Overage, and What Is Included",
        "sub_context": "WhatsApp Outreach",
        "entity_type": "Platform Feature",
        "entity": "WhatsApp Outreach",
        "topic": "WhatsApp Capacity Per Plan, Overage Pricing, and Feature Scope",
        "priority": 9,
        "manual_content": """
WhatsApp Outreach is a standard capability included in every Nexus Orbit plan. It extends the Nexy Companion Framework to WhatsApp, allowing businesses to engage visitors, customers, and prospects through WhatsApp conversations governed by the same knowledge, personas, and playbooks as the website chat.

WhatsApp message capacity per plan:

Orbit Lite: 2,000 messages per month
Overage: +$25 per additional 2,000 messages

Orbit: 5,000 messages per month
Overage: +$25 per additional 2,000 messages

Orbit Pro: 12,000 messages per month
No WhatsApp overage on Orbit Pro — messages above 12,000 are included

Orbit Command: Unlimited messages per month
No overage applies

What counts as a WhatsApp message:
Each individual message sent or received through the WhatsApp Outreach channel counts toward the monthly capacity. A conversation between Nexy and a visitor involving 10 exchanges counts as 10 messages.

What WhatsApp Outreach includes:
- Nexy-powered WhatsApp conversations governed by the same knowledge base as website chat
- All configured personas and playbooks apply to WhatsApp sessions
- Same 11-stage journey and 14-signal classification as website chat
- Escalation to human agent directly from WhatsApp if configured
- Conversation logs and enquiry scoring for every WhatsApp session

WhatsApp Outreach on Orbit Pro does not carry an overage charge. If a business expects high WhatsApp volume — more than 5,000 messages per month — Orbit Pro removes the per-message uncertainty and is the recommended plan.

For visitors asking whether WhatsApp Outreach requires a separate setup or subscription: it is included in all plans at no additional charge. The WhatsApp Business account integration is configured during the onboarding process.
""",
    },

    # 4 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Orbit — Onboarding Process and Getting Started",
        "sub_context": "Onboarding",
        "entity_type": "Commercial",
        "entity": "Nexus Orbit Onboarding",
        "topic": "Onboarding Fees, Process, and What Is Included",
        "priority": 9,
        "manual_content": """
Every Nexus Orbit plan includes a structured onboarding process to get the business live. Onboarding is a one-time engagement and is priced separately from the annual subscription. It ensures the platform is correctly configured for the business's specific use case before going live.

One-time onboarding fees per plan:
Orbit Lite: $750
Orbit: $1,500
Orbit Pro: $2,500
Orbit Command: $4,000

Onboarding covers the following:
1. Platform configuration — setting up the tenant, business unit, channels, chat categories, and access governance for the specific deployment.
2. Knowledge base setup — loading the initial knowledge sources into the platform, classifying them, processing and embedding content, and confirming retrieval readiness.
3. Nexy Companion configuration — configuring personas, playbooks, escalation rules, and conversation stage logic specific to the business's sales and support workflows.
4. WhatsApp Outreach integration — connecting the WhatsApp Business account and configuring it for the plan's capacity.
5. Identity and access governance — configuring identity types, access policies, and access categories appropriate to the business's visitor audiences.
6. Testing and validation — running test conversations across key scenarios before going live, confirming that Nexy responds correctly and escalates as expected.
7. Go-live handover — activating the live configuration and confirming readiness scores across all platform components.

Onboarding scope scales with the plan. Orbit Lite onboarding is scoped for a focused, single-use-case deployment. Orbit Command onboarding covers a full enterprise deployment with multiple channels, personas, playbooks, and a comprehensive knowledge base.

The subscription and onboarding are separate payments. The annual subscription renews automatically. The onboarding fee is paid once at the start of the engagement.

If a visitor asks how quickly they can go live: typical onboarding for Orbit Lite and Orbit takes 2 to 3 weeks. Orbit Pro typically takes 3 to 5 weeks. Orbit Command timelines depend on deployment scope and are discussed during the initial consultation.

For businesses that already have their knowledge base prepared and a clear deployment brief, onboarding may be faster. For businesses starting from scratch with no content ready, the Nexus team recommends beginning with a structured knowledge preparation phase before committing to a go-live date.
""",
    },

    # 5 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Orbit — Demo Request and Consultation Process",
        "sub_context": "Demo and Consultation",
        "entity_type": "Commercial",
        "entity": "Nexus Orbit Demo",
        "topic": "Demo Request Process and What the Demo Covers",
        "priority": 10,
        "manual_content": """
Visitors interested in seeing how the Nexus Orbit platform works can request a demo. A Nexus Consultant will contact the visitor through their registered email or phone to arrange the demonstration.

Demo request process:
When a visitor asks for a demo, Nexy will ask: "Do you want to submit a demo request? Our Nexus Consultant will contact you on your registered email or phone to arrange the demo."

If the visitor confirms yes, Nexy will acknowledge the request and confirm it has been submitted. The Nexus team will follow up through the contact details on file.

If the visitor is not yet registered, Nexy will let them know that a Nexus Consultant will reach out via the available contact information and can collect any additional details at that stage.

What the demo covers:
The demonstration is tailored to the visitor's specific industry and use case. It typically covers:
- A walkthrough of the Nexus Studio — how knowledge is loaded, classified, and approved
- A live conversation with Nexy showing intent classification, persona matching, and playbook execution
- WhatsApp Outreach demonstration showing how the same Nexy configuration extends to WhatsApp
- The Nexus Live workspace — how conversations, escalations, and enquiry scores are monitored
- A discussion of which plan fits the visitor's team size, conversation volume, and use case

The demo is not a generic product presentation. It is a configured walkthrough that shows how the platform would work for the visitor's specific business scenario.

For visitors comparing plans before the demo: the Nexus team recommends requesting the demo first. The consultant will recommend the right plan based on the business's actual requirements rather than a self-service comparison.

Visitors can also use the Talk to Us option on the website for open questions about suitability, integration, pricing context, or the difference between plans before committing to a demo.

Demo requests submitted through Nexy are logged and confirmed. A Nexus Consultant will respond within 1 business day during standard working hours.
""",
    },

    # 6 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Custom Engagement — CRM Integration and Business Orchestration",
        "sub_context": "Custom Engagement",
        "entity_type": "Commercial",
        "entity": "Nexus Custom Engagement",
        "topic": "Custom CRM Integration and Business Orchestration Option",
        "priority": 8,
        "manual_content": """
For businesses that need Nexus to connect with their CRM, ERP, or broader business operations, a Custom Engagement option is available. This goes beyond the standard Orbit plans and is designed for organisations where AI-assisted conversations need to read from or write back to their business systems.

What Custom Engagement covers:
Custom Engagement combines two elements — CRM Integration and Business Orchestration. Together, they allow Nexy to work as an active participant in business processes rather than a standalone conversation layer.

CRM Integration:
Nexy can be connected to the business's CRM system to pull live context during conversations. When a visitor interacts with Nexy, it can retrieve relevant account information, open opportunities, service history, or qualification data from the CRM to personalise the conversation and improve response quality. Post-conversation, Nexy can push conversation summaries, enquiry scores, and intent classifications back to the CRM so sales and support teams have a complete activity record without manual entry.

Business Orchestration:
Nexus Business Orchestration extends Nexy's role from a conversation assistant to a workflow participant. Configured actions can trigger downstream business processes — creating a lead record when an enquiry is scored above a threshold, initiating an approval workflow when a visitor requests a specific commitment, or flagging a high-priority contact to the sales team based on conversation signals.

Who Custom Engagement is for:
Custom Engagement is designed for businesses where the gap between a visitor conversation and a business action needs to be closed automatically. It is suitable for businesses using Frappe, ERPNext, or other connected business systems where Nexus data should flow directly into operational records without manual handoff.

Custom Engagement is priced and scoped separately from the Orbit plan subscription. It is not a self-service addition — it requires a scoping call with the Nexus team to design the integration correctly.

Visitors interested in Custom Engagement should request a demo and mention CRM integration or business orchestration. A Nexus Consultant will scope the requirements and provide a tailored proposal.
""",
    },

]


# ── Foundation helpers ─────────────────────────────────────────────────────────

def _get_tenant():
    name = frappe.db.get_value("Nexus Tenant", {"tenant_code": TENANT}, "name")
    if not name:
        raise ValueError(
            f"Nexus Tenant '{TENANT}' not found. "
            "Ensure the NEXUS-AI tenant is created before running this seed."
        )
    return name


def _get_or_create_website_chat_channel(tenant):
    existing = frappe.db.get_value(
        "Nexus Live Channel",
        {"channel_code": CHANNEL_CODE, "tenant": tenant},
        "name",
    )
    if existing:
        return existing

    # Try any existing Website Chat channel for this tenant
    fallback = frappe.db.get_value(
        "Nexus Live Channel",
        {"tenant": tenant, "channel_type": "Website Chat", "enabled": 1},
        "name",
    )
    if fallback:
        return fallback

    # Create one
    doc = frappe.new_doc("Nexus Live Channel")
    doc.channel_code  = CHANNEL_CODE
    doc.tenant        = tenant
    doc.channel_name  = "Nexus AI Website Chat"
    doc.channel_type  = "Website Chat"
    doc.enabled       = 1
    doc.requires_visitor_email = 0
    doc.agent_based   = 0
    doc.description   = "Primary website chat channel for the NEXUS-AI tenant."
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_chat_category(tenant, channel):
    existing = frappe.db.get_value(
        "Nexus Chat Category",
        {"category_code": CHAT_CATEGORY_CODE, "tenant": tenant},
        "name",
    )
    if existing:
        doc = frappe.get_doc("Nexus Chat Category", existing)
    else:
        doc = frappe.new_doc("Nexus Chat Category")
        doc.category_code = CHAT_CATEGORY_CODE
        if doc.meta.has_field("tenant"):
            doc.tenant = tenant

    doc.category_label             = CHAT_CATEGORY_LABEL
    doc.channel                    = channel
    doc.enabled                    = 1
    doc.identity_verification_mode = "None"
    doc.allow_public_fallback      = 1
    doc.display_order              = 20
    doc.published                  = 1
    doc.enable_escalation          = 1
    doc.description = (
        "Commercial enquiry category — handles pricing, plan comparisons, "
        "demo requests, onboarding questions, and WhatsApp outreach enquiries "
        "for the NEXUS AI Orbit plans."
    )
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_role_profile(tenant):
    existing = frappe.db.get_value(
        "Nexy Role Profile",
        {"profile_name": ROLE_PROFILE_CODE, "tenant": tenant},
        "name",
    )
    if existing:
        doc = frappe.get_doc("Nexy Role Profile", existing)
    else:
        doc = frappe.new_doc("Nexy Role Profile")
        doc.profile_name = ROLE_PROFILE_CODE
        doc.tenant = tenant

    doc.role_type            = "Sales"
    doc.enabled              = 1
    doc.role_description     = (
        "Nexy Commercial — the consultative companion for Nexus Orbit commercial enquiries. "
        "Advises visitors on plans, pricing, capacity, and the demo process. "
        "Grounded entirely in approved commercial knowledge."
    )
    doc.engagement_objective = (
        "Guide the visitor to a clear understanding of which Nexus Orbit plan fits "
        "their business. Recommend a demo request as the natural next step when the "
        "visitor is ready to explore further. Never pressure — advise, clarify, and assist."
    )
    doc.tone                 = "Consultative"
    doc.communication_style  = "Question-led"
    doc.cta_style            = "Invitation"
    doc.followup_style       = "Gentle"
    doc.do_rules             = (
        "- Always retrieve from approved knowledge before making any claim about plans, "
        "pricing, capacity, or features.\n"
        "- Ask about the visitor's team size and conversation volume before recommending "
        "a plan — recommend the plan that fits, not the highest tier.\n"
        "- Offer a demo request when the visitor signals readiness to explore further.\n"
        "- Acknowledge honestly when a question falls outside your approved knowledge.\n"
        "- Refer WhatsApp-specific questions to the WhatsApp Outreach knowledge.\n"
        "- Treat demo requests seriously — confirm using the required response script."
    )
    doc.dont_rules           = (
        "- Do not quote prices from memory — always retrieve the current pricing knowledge.\n"
        "- Do not recommend an upgrade beyond what the visitor's stated needs require.\n"
        "- Do not make commitments about delivery timelines, custom pricing, or discounts.\n"
        "- Do not compare NEXUS AI products against competitor offerings.\n"
        "- Do not continue answering if no approved knowledge covers the question.\n"
        "- Do not use the words 'sell', 'selling', 'sales pitch', or 'close the deal'."
    )
    doc.prohibited_claims    = (
        "- Specific discounts or promotional pricing not in the approved knowledge\n"
        "- Custom or negotiated pricing\n"
        "- Delivery or implementation timelines not confirmed in approved knowledge\n"
        "- Feature capabilities not documented in the approved knowledge base\n"
        "- Any claim about competitor products"
    )
    doc.escalation_policy    = (
        "If the visitor asks for a demo, requests to speak with a person, raises a "
        "complex technical integration requirement, or asks for a custom quote — "
        "offer the demo request immediately using the required script. "
        "Do not attempt to resolve commercial commitments through conversation alone."
    )
    doc.requires_grounding                  = 1
    doc.requires_human_approval_for_outbound = 0
    doc.role_extension_doctype              = "Nexy Sales Profile Extension"

    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_sales_extension(role_profile_name):
    existing = frappe.db.get_value(
        "Nexy Sales Profile Extension",
        {"role_profile": role_profile_name},
        "name",
    )
    if existing:
        doc = frappe.get_doc("Nexy Sales Profile Extension", existing)
    else:
        doc = frappe.new_doc("Nexy Sales Profile Extension")
        doc.role_profile = role_profile_name

    doc.selling_style             = "Consultative"
    doc.persuasion_style          = "Logical"
    doc.objection_handling_style  = "Acknowledge-Reframe"
    doc.urgency_style             = "None"
    doc.pricing_policy            = (
        "Present only the pricing available in approved knowledge. "
        "If the visitor asks about discounts or custom pricing, acknowledge the question "
        "and offer a demo request so a Nexus Consultant can discuss their requirements directly."
    )
    doc.discount_policy           = (
        "Do not offer, suggest, or imply any discount. "
        "All pricing shown is the current approved rate. "
        "Direct discount enquiries to the Nexus Consultant via a demo request."
    )
    doc.competitive_policy        = (
        "Do not reference, compare, or comment on any competitor or alternative product. "
        "Focus only on communicating the value of NEXUS AI Orbit plans using "
        "retrieved, approved knowledge."
    )

    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_companion_assignment(chat_category, role_profile, tenant):
    name = f"NCA-{chat_category}"

    if frappe.db.exists("Nexy Companion Assignment", name):
        doc = frappe.get_doc("Nexy Companion Assignment", name)
        doc.nexy_role_profile = role_profile
        doc.tenant            = tenant
        doc.enabled           = 1
        doc.assignment_notes  = (
            "Nexy Commercial — wires the Commercial Enquiry category to the "
            "NEXY-COMMERCIAL role profile. Handles Orbit plan enquiries, "
            "pricing questions, demo requests, and WhatsApp outreach questions."
        )
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"  Updated companion assignment: {name}")
    else:
        doc = frappe.get_doc({
            "doctype":          "Nexy Companion Assignment",
            "chat_category":    chat_category,
            "nexy_role_profile": role_profile,
            "tenant":           tenant,
            "enabled":          1,
            "assignment_notes": (
                "Nexy Commercial — wires the Commercial Enquiry category to the "
                "NEXY-COMMERCIAL role profile. Handles Orbit plan enquiries, "
                "pricing questions, demo requests, and WhatsApp outreach questions."
            ),
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  Created companion assignment: {doc.name}")

    return frappe.db.get_value("Nexy Companion Assignment", name, "name")


def _ensure_knowledge_profile(tenant, access_category_name):
    existing = frappe.db.get_value(
        "Knowledge Profile",
        {"profile_name": KNOWLEDGE_PROFILE_CODE, "tenant": tenant},
        "name",
    )
    if existing:
        kp = frappe.get_doc("Knowledge Profile", existing)
    else:
        kp = frappe.new_doc("Knowledge Profile")
        kp.profile_name = KNOWLEDGE_PROFILE_CODE
        kp.tenant = tenant

    kp.title       = KNOWLEDGE_PROFILE_TITLE
    kp.enabled     = 1
    kp.description = (
        "Knowledge profile for Nexus Commercial enquiries. "
        "Grants access to the NEXUS-COMMERCIAL access category — "
        "covering Orbit plans, pricing, WhatsApp, onboarding, demo, "
        "and custom engagement knowledge."
    )

    existing_cats = {row.access_category for row in (kp.get("access_categories") or [])}
    if access_category_name not in existing_cats:
        kp.append("access_categories", {
            "access_category": access_category_name,
            "enabled": 1,
        })

    kp.save(ignore_permissions=True)
    return kp.name


def _get_business_unit(tenant):
    return (
        frappe.db.get_value("Nexus Business Unit", {"tenant": tenant}, "name")
        or frappe.db.get_value("Nexus Business Unit", {}, "name")
    )


def _upsert_knowledge_source(source, tenant, category_name, policy_name, business_unit):
    title = source["title"]

    if frappe.db.exists("Nexus Knowledge Source", title):
        doc = frappe.get_doc("Nexus Knowledge Source", title)
    else:
        doc = frappe.new_doc("Nexus Knowledge Source")
        doc.title = title

    doc.source_type        = "Manual"
    doc.manual_content     = source["manual_content"].strip()
    doc.tenant             = tenant
    doc.business_unit      = business_unit or ""
    doc.project            = ""
    doc.context            = CONTEXT
    doc.sub_context        = source["sub_context"]
    doc.entity_type        = source["entity_type"]
    doc.entity             = source["entity"]
    doc.topic              = source["topic"]
    doc.access_policy      = policy_name
    doc.status             = "Draft"
    doc.priority           = source.get("priority", 9)
    doc.processing_status  = "Pending"
    doc.embedding_status   = "Pending"
    doc.diagnostics_status = "Pending"
    doc.retrieval_ready    = 0

    if doc.meta.has_field("chat_category"):
        doc.chat_category = category_name

    doc.save(ignore_permissions=True)
    return doc


# ── Main entry point ───────────────────────────────────────────────────────────

def run(process_sources=True):
    """
    Idempotent seed for the Nexy Commercial configuration on the NEXUS-AI tenant.
    All steps are safe to re-run — existing records are updated, not duplicated.

    Args:
        process_sources (bool): If True, runs knowledge chunking and embedding
                                after creating each source. Set to False for a
                                faster dry run that creates records without processing.
    """

    print("\n" + "=" * 70)
    print("  Nexy Commercial Seed — NEXUS-AI Tenant")
    print("=" * 70)

    result = {"foundation": {}, "sources": []}

    # ── 1. Tenant ──────────────────────────────────────────────────────────────
    tenant = _get_tenant()
    result["foundation"]["tenant"] = tenant
    print(f"\n  Tenant               : {tenant}")

    # ── 2. Access Policy ───────────────────────────────────────────────────────
    policy = ensure_access_policy(
        policy_name=POLICY_NAME,
        access_level="Public",
        sensitivity="public",
        description=(
            "Nexus commercial knowledge policy. "
            "Governs public-facing commercial content: plans, pricing, "
            "WhatsApp capacity, onboarding, demo, and custom engagement."
        ),
        primitive=False,
        tenant=tenant,
    )
    result["foundation"]["access_policy"] = policy
    print(f"  Access Policy        : {policy}")

    # ── 3. Access Category ─────────────────────────────────────────────────────
    access_cat = ensure_access_category(
        category_name=ACCESS_CATEGORY,
        title="Nexus Commercial",
        policies=[policy],
        description=(
            "Access category for Nexy Commercial enquiries. "
            "Grants access to commercial knowledge: Orbit plans, pricing, "
            "onboarding, WhatsApp, demo, and custom engagement."
        ),
        priority=10,
        tenant=tenant,
    )
    result["foundation"]["access_category"] = access_cat
    print(f"  Access Category      : {access_cat}")

    # ── 4. Knowledge Profile ───────────────────────────────────────────────────
    knowledge_profile = _ensure_knowledge_profile(tenant, access_cat)
    result["foundation"]["knowledge_profile"] = knowledge_profile
    print(f"  Knowledge Profile    : {knowledge_profile}")

    frappe.db.commit()

    # ── 5. Website Chat Channel ────────────────────────────────────────────────
    channel = _get_or_create_website_chat_channel(tenant)
    result["foundation"]["channel"] = channel
    print(f"  Channel              : {channel}")

    # ── 5. Chat Category ───────────────────────────────────────────────────────
    chat_category = _ensure_chat_category(tenant, channel)
    result["foundation"]["chat_category"] = chat_category
    print(f"  Chat Category        : {chat_category}")

    frappe.db.commit()

    # ── 6. Nexy Role Profile ───────────────────────────────────────────────────
    role_profile = _ensure_role_profile(tenant)
    result["foundation"]["role_profile"] = role_profile
    print(f"  Nexy Role Profile    : {role_profile}")

    # ── 7. Nexy Sales Profile Extension ───────────────────────────────────────
    sales_ext = _ensure_sales_extension(role_profile)
    result["foundation"]["sales_extension"] = sales_ext
    print(f"  Sales Extension      : {sales_ext}")

    frappe.db.commit()

    # ── 8. Nexy Companion Assignment ───────────────────────────────────────────
    assignment = _ensure_companion_assignment(chat_category, role_profile, tenant)
    result["foundation"]["companion_assignment"] = assignment
    print(f"  Companion Assignment : {assignment}")

    frappe.db.commit()

    # ── Resolve policy doc name for knowledge source link ──────────────────────
    resolved_policy = (
        frappe.db.get_value("Nexus Access Policy", {"policy_name": POLICY_NAME, "tenant": tenant}, "name")
        or frappe.db.get_value("Nexus Access Policy", {"policy_name": POLICY_NAME}, "name")
        or policy
    )

    # ── 9. Business Unit ───────────────────────────────────────────────────────
    business_unit = _get_business_unit(tenant)

    # ── 10. Knowledge Sources ──────────────────────────────────────────────────
    print(f"\n  Knowledge Sources ({len(COMMERCIAL_SOURCES)} total):")
    for source in COMMERCIAL_SOURCES:
        doc = _upsert_knowledge_source(
            source,
            tenant,
            category_name=chat_category,
            policy_name=resolved_policy,
            business_unit=business_unit,
        )
        entry = {
            "name":         doc.name,
            "title":        doc.title,
            "sub_context":  doc.sub_context,
            "access_policy": doc.access_policy,
            "status":       doc.status,
        }

        if process_sources:
            try:
                processing_result = process_knowledge_source(doc.name)
                entry["processing"] = processing_result
                flag = "OK" if processing_result else "?"
            except Exception as e:
                entry["processing_error"] = str(e)
                flag = "ERR"
        else:
            flag = "SKIP"

        print(f"    [{flag}] {doc.title[:65]}")
        result["sources"].append(entry)

    frappe.db.commit()

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  Nexy Commercial Seed Complete")
    print("=" * 70)
    print(f"  Tenant               : {result['foundation']['tenant']}")
    print(f"  Access Policy        : {result['foundation']['access_policy']}")
    print(f"  Access Category      : {result['foundation']['access_category']}")
    print(f"  Knowledge Profile    : {result['foundation']['knowledge_profile']}")
    print(f"  Chat Category        : {result['foundation']['chat_category']}")
    print(f"  Nexy Role Profile    : {result['foundation']['role_profile']}")
    print(f"  Companion Assignment : {result['foundation']['companion_assignment']}")
    print(f"  Knowledge Sources    : {len(result['sources'])}")
    print("=" * 70 + "\n")

    frappe.logger().info(
        "Nexy Commercial seed completed. Tenant: %s. Sources: %d.",
        tenant,
        len(result["sources"]),
    )

    return result
