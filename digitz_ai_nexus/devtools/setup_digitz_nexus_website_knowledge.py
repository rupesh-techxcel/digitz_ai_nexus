import frappe

from digitz_ai_nexus.services.knowledge_source_processor import process_knowledge_source


TENANT = "DIGITZ-NEXUS"
BUSINESS_UNIT = "DIGITZ AI NEXUS"
PUBLIC_CONTEXT = "DIGITZ AI NEXUS WEBSITE"
INTERNAL_CONTEXT = "DIGITZ AI NEXUS INTERNAL"
CHANNEL = "WEBSITE-CHAT"
CHAT_CATEGORY = "Nexus Platform Know-How"
PUBLIC_AGENT = "PUBLIC-AI-ASSISTANT"
INTERNAL_AGENT = "INTERNAL-AI-ASSISTANT"


PUBLIC_SOURCES = [
    {
        "title": "DIGITZ AI Nexus - Nexus Platform Know-How",
        "context": PUBLIC_CONTEXT,
        "sub_context": "Public Website",
        "entity_type": "Product Knowledge",
        "entity": "DIGITZ AI Nexus",
        "topic": "Nexus Platform Know-How",
        "chat_category": CHAT_CATEGORY,
        "access_policy": "Public",
        "priority": 10,
        "manual_content": """
DIGITZ AI Nexus is a governed AI knowledge and chat platform for organizations that need controlled answers from approved knowledge.

DIGITZ AI Nexus helps a business make approved knowledge available through public website chat, Q&A widgets, internal chat, support workflows, and future AI assistant experiences.

Nexus does not treat AI as an uncontrolled answering tool. Nexus organizes approved knowledge, applies tenant and access boundaries, retrieves only permitted content, and prepares grounded answers.

The primary business problem solved by Nexus is safe enterprise AI adoption. Organizations can let visitors, customers, and employees ask natural language questions while keeping answers limited to approved and permitted knowledge.

The core value of Nexus is governed enterprise AI. Approved knowledge is managed before use. Knowledge is classified by tenant, business unit, public context, topic, and access policy. Runtime retrieval checks those boundaries before an answer is produced.

Public website chat in Nexus is limited to public knowledge. A public visitor can ask about the product, features, high-level governance model, public support direction, demo interest, and contact guidance.

Public website chat must not expose internal configuration, customer-private information, credentials, restricted runbooks, admin operations, internal routing details, or account-specific content.

If approved public knowledge is insufficient, Nexus should not guess. The assistant should explain that it does not have enough approved knowledge and guide the visitor to contact the DIGITZ AI Nexus team.

Nexus supports different chat access levels by combining the channel, selected chat category, and verified identity level. The resolved route selects the correct AI Agent Profile and access boundary.

Verification does not unlock all knowledge. Verification selects the right profile and the right access boundary. Public users remain limited to public knowledge. Verified users can receive additional knowledge only when their identity, chat purpose, profile, and access policy allow it.

Nexus can support public website visitors, verified customers, support users, internal employees, and future API-based assistant calls through the same governed knowledge model.

Nexus Studio is used to feed, classify, process, validate, and publish knowledge. Knowledge can be entered manually or through supported document sources, then converted into retrievable chunks with embeddings.

Nexus Administration manages tenant configuration and runtime defaults. Nexus Live supports public website chat and internal chat operations. Nexus Platform supports diagnostics, validation, access checks, and readiness evidence.

Nexus Support is a customer support experience powered by DIGITZ AI Nexus. It can answer from approved support knowledge, ask clarifying questions, prepare ticket-ready summaries, and escalate unresolved or policy-sensitive requests to human teams.

Nexus Support should be understood as a support enablement layer, not only as a chatbot. It improves first response, issue intake, repetitive support handling, and handoff quality.

A ticket-ready support handoff can include customer identity or verified contact path, affected product or workflow, issue summary, steps already attempted, AI guidance already given, priority, attachments when available, and recommended next action.

DIGITZ AI Nexus can evolve beyond knowledge answers into controlled ERP AI tool integration. Authorized users can ask for business outcomes in natural language while Nexus uses permitted ERP tools, APIs, workflows, reports, and transaction services.

ERP AI tool integration must remain governed. Public chat can explain ERP capabilities from public knowledge. Internal staff can use ERP tools only when identity, profile, role, and access policies allow it.

ERP database queries, document lookups, reports, and transactions must be authenticated, authorized, validated, and auditable. Sensitive operations should require confirmation, approval, or workflow handoff before execution.

Nexus can support SOP implementation by turning approved procedures into conversational guidance. Employees can ask process questions, follow step-by-step workflows, understand required documents and approvals, and escalate exceptions with context.

Nexus can support employee onboarding by answering approved questions about policies, departments, tools, workflows, responsibilities, checklists, support channels, and training paths.

Nexus can support customer support and ticketing by answering common questions, collecting issue context, creating structured ticket summaries, suggesting next steps, escalating unresolved issues, and giving support agents conversation context.

Nexus can support training by turning approved product knowledge, SOPs, onboarding material, policy documents, and process manuals into role-aware conversational assistance.

Nexus answers should preserve approved facts and avoid invented claims. The system should provide citations when required and keep query logs for traceability, quality review, audit, and operational improvement.

Nexus Platform Know-How is the public chat category for explaining DIGITZ AI Nexus at a product and commercial level. It should cover what Nexus is, what it does, how governed knowledge works, how public chat and Q&A work, how verification protects access, how support escalation works, and how ERP or business systems can be connected safely.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Public Overview",
        "context": PUBLIC_CONTEXT,
        "sub_context": "Public Website",
        "entity_type": "Product",
        "entity": "DIGITZ AI Nexus",
        "topic": "Overview",
        "chat_category": CHAT_CATEGORY,
        "access_policy": "Public",
        "priority": 8,
        "manual_content": """
DIGITZ AI Nexus is a governed AI knowledge and chat platform for organizations that need controlled answers from approved knowledge.

Nexus is designed to power public website chat, internal desk chat, Q&A, and future AI assistant workflows. It combines tenant-aware context, knowledge-source management, access governance, retrieval, prompt construction, and answer generation.

For public website visitors, Nexus answers only from approved public knowledge. If approved knowledge is not available, the assistant should say that it does not have enough approved knowledge to answer. Public website users should not receive internal, restricted, financial, HR, or administrator-only knowledge.

The core value of Nexus is safe enterprise AI: knowledge is organized, chunked, embedded, and retrieved only when access policy and runtime context allow it.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Website Chat Capabilities",
        "context": PUBLIC_CONTEXT,
        "sub_context": "Public Website",
        "entity_type": "Feature",
        "entity": "Website Chat",
        "topic": "Capabilities",
        "chat_category": CHAT_CATEGORY,
        "access_policy": "Public",
        "priority": 8,
        "manual_content": """
The DIGITZ AI Nexus public website chat can answer visitor questions using approved public knowledge sources.

Supported public chat capabilities include product overview answers, common FAQ responses, high-level feature explanations, support direction, contact guidance, and safe fallback responses when the knowledge base does not contain an approved answer.

The public assistant is intentionally governed. It should not invent facts, quote private implementation details, expose internal configuration, or answer from restricted knowledge. It uses the public chat category and public identity route to reach a public AI profile whose access category allows only public knowledge.

Visitors can ask questions such as: What is DIGITZ AI Nexus? What can the website chat do? How does Nexus keep answers governed? How do I contact the team for a demo or support?
""",
    },
    {
        "title": "DIGITZ AI Nexus - Public FAQ",
        "context": PUBLIC_CONTEXT,
        "sub_context": "Public Website",
        "entity_type": "FAQ",
        "entity": "DIGITZ AI Nexus",
        "topic": "Frequently Asked Questions",
        "chat_category": CHAT_CATEGORY,
        "access_policy": "Public",
        "priority": 7,
        "manual_content": """
Frequently asked public questions about DIGITZ AI Nexus:

Question: What is DIGITZ AI Nexus?
Answer: DIGITZ AI Nexus is a governed AI knowledge and chat platform that helps organizations answer questions from approved knowledge with access controls.

Question: Can Nexus be used for a public website assistant?
Answer: Yes. Nexus can power public website chat through a public channel, public chat category, public identity route, and public knowledge sources.

Question: Can Nexus also support internal users?
Answer: Yes. Internal desk users can use profile assignment and internal access categories so they can retrieve internal knowledge when permitted.

Question: What happens when Nexus does not have enough approved knowledge?
Answer: The assistant should use a safe fallback and say it does not have enough approved knowledge to answer.

Question: Does public chat expose internal content?
Answer: No. Public chat is routed through public-only access and should retrieve only knowledge marked with the Public access policy.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Contact Support and Escalation",
        "context": PUBLIC_CONTEXT,
        "sub_context": "Public Website",
        "entity_type": "Support",
        "entity": "DIGITZ AI Nexus",
        "topic": "Contact and Escalation",
        "chat_category": CHAT_CATEGORY,
        "access_policy": "Public",
        "priority": 6,
        "manual_content": """
Public website visitors who need help with DIGITZ AI Nexus can ask the website assistant for product information, demo guidance, and support direction.

If a visitor asks for details that are not available in approved public knowledge, the assistant should not guess. It should explain that it does not have enough approved knowledge and suggest contacting the DIGITZ AI Nexus team through the official website contact path.

For sales or partnership interest, visitors should be guided to request a demo or contact the team. For product support, visitors should provide a clear description of the issue, the affected workflow, and any relevant tenant or channel context if they have it.

Escalation should be used when a visitor needs human assistance, when the question is outside approved public knowledge, or when the request requires private account-specific investigation.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Privacy and Data Usage Summary",
        "context": PUBLIC_CONTEXT,
        "sub_context": "Public Website",
        "entity_type": "Governance",
        "entity": "DIGITZ AI Nexus",
        "topic": "Privacy and Data Usage",
        "chat_category": CHAT_CATEGORY,
        "access_policy": "Public",
        "priority": 6,
        "manual_content": """
DIGITZ AI Nexus is designed for governed answers from approved knowledge. The public website assistant should use only public knowledge sources and should not reveal internal system configuration, credentials, private customer data, or restricted operational procedures.

The assistant should avoid collecting sensitive personal information in public chat. If a support request requires private details, the visitor should be directed to an appropriate secure support or contact channel.

Public chat should not claim access to private systems unless the visitor is routed through an authenticated or verified workflow. Public responses should remain high level, accurate, and grounded in approved public content.
""",
    },
]


INTERNAL_SOURCES = [
    {
        "title": "DIGITZ AI Nexus - Internal Admin Guide",
        "context": INTERNAL_CONTEXT,
        "sub_context": "Internal Operations",
        "entity_type": "Runbook",
        "entity": "Nexus Administration",
        "topic": "Admin Guide",
        "access_policy": "Internal",
        "priority": 8,
        "manual_content": """
Internal administrators use Nexus Admin to manage tenants, tenant configuration, and readiness.

Tenant configuration stores only tenant-wide defaults such as business unit, public context, Q&A channel, chat channel, safety flags, and widget defaults. It is not a routing mechanism.

Before testing chat or Q&A for a tenant, confirm the tenant exists, the default business unit and public context are valid master records, and Q&A or Live Chat is enabled in tenant configuration.

For DIGITZ-NEXUS website chat, the expected foundation is tenant DIGITZ-NEXUS, business unit DIGITZ AI NEXUS, public context DIGITZ AI NEXUS WEBSITE, and channel WEBSITE-CHAT.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Tenant Configuration Operations",
        "context": INTERNAL_CONTEXT,
        "sub_context": "Internal Operations",
        "entity_type": "Runbook",
        "entity": "Tenant Configuration",
        "topic": "Runtime Defaults",
        "access_policy": "Internal",
        "priority": 8,
        "manual_content": """
Tenant configuration controls tenant runtime defaults.

Tenant resolution priority is explicit payload tenant, then an error if tenant is required.

Business unit is resolved from payload, then tenant configuration default. Public context is resolved from payload, then tenant configuration default. Channel is resolved from payload, then the purpose-specific tenant configuration channel.

Chat runtime uses default_chat_channel. Q&A runtime uses default_qa_channel. These defaults do not fall back to each other.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Knowledge Source Lifecycle",
        "context": INTERNAL_CONTEXT,
        "sub_context": "Internal Operations",
        "entity_type": "Runbook",
        "entity": "Knowledge Source",
        "topic": "Lifecycle",
        "access_policy": "Internal",
        "priority": 8,
        "manual_content": """
Knowledge enters Nexus through Nexus Knowledge Source records. Manual sources store content in manual_content. File sources use uploaded PDF, DOCX, or TXT files.

Each source must have a tenant, business unit, context, access policy, source type, and content. When processed, Nexus extracts text, creates a Nexus Knowledge Unit, splits content into chunks, generates embeddings, and creates Nexus Knowledge Chunk records.

Retrieval happens at chunk level. A chunk is retrievable only when it is not disabled, has embedding_status Completed, and its access_policy is allowed by the resolved access policies.

A published source becomes retrieval ready only when processing succeeds, embeddings are completed, diagnostics are healthy, and at least one active chunk exists.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Access Governance and Profile Assignment",
        "context": INTERNAL_CONTEXT,
        "sub_context": "Internal Operations",
        "entity_type": "Runbook",
        "entity": "Access Governance",
        "topic": "Profiles and Policies",
        "access_policy": "Internal",
        "priority": 8,
        "manual_content": """
Nexus access is profile driven. A runtime request resolves one Nexus AI Agent Profile. That profile is mapped to one or more Nexus Access Categories through Nexus AI Agent Profile Access Category records.

Access categories contain allowed policies through Nexus Access Category Policy child rows. The final allowed policies determine which knowledge chunks may be retrieved.

For internal desk users, Nexus User Profile Assignment is the normal assignment point. It maps a Frappe user to an AI Agent Profile. One active assignment per user is allowed.

Authenticated System Manager sessions have an admin bypass for policy narrowing unless the request is explicitly public-only. Public-only routes always remain public-only.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Troubleshooting Runbook",
        "context": INTERNAL_CONTEXT,
        "sub_context": "Internal Operations",
        "entity_type": "Runbook",
        "entity": "Troubleshooting",
        "topic": "Chat and Knowledge",
        "access_policy": "Internal",
        "priority": 7,
        "manual_content": """
When public chat does not answer, verify these items in order:

1. The tenant exists and is enabled.
2. Tenant configuration has live_chat_enabled or qa_enabled enabled as needed.
3. The default channel exists and is enabled.
4. The chat category exists and points to the channel.
5. The category identity route exists for the visitor identity type.
6. The route points to an AI Agent Profile.
7. The AI Agent Profile has at least one enabled access category.
8. The access category contains the expected access policy.
10. At least one published knowledge source has processed chunks with completed embeddings.

If access resolution returns an empty policy list, retrieval fails closed. If chunks exist but are marked with a policy not allowed to the resolved profile, the answer should be restricted or fallback depending on retrieval result.
""",
    },
]


RESTRICTED_SOURCES = [
    {
        "title": "DIGITZ AI Nexus - System Manager Operations",
        "context": INTERNAL_CONTEXT,
        "sub_context": "Restricted Operations",
        "entity_type": "Runbook",
        "entity": "System Manager",
        "topic": "Privileged Operations",
        "access_policy": "Restricted",
        "priority": 9,
        "manual_content": """
System Manager operations include migration, seed cleanup, master data repair, and runtime diagnostics.

System Managers can verify tenant records, inspect access routing, review query logs, and confirm knowledge readiness. They may bypass profile/category policy narrowing for authenticated admin use, but public-only requests always remain public-only.

Use privileged operations carefully. Do not delete tenant, context, business unit, channel, agent, route, profile, or knowledge records unless their dependencies have been checked.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Seed Data and Cleanup Procedures",
        "context": INTERNAL_CONTEXT,
        "sub_context": "Restricted Operations",
        "entity_type": "Runbook",
        "entity": "Seed Data",
        "topic": "Cleanup",
        "access_policy": "Restricted",
        "priority": 9,
        "manual_content": """
Synthetic seed data is used only for validation. It should not remain as a production runtime dependency.

Use clear_synthetic_dataset to remove synthetic runtime records while preserving seeded test definitions. Use clear_seeded_test_data when seeded test definitions must also be removed so linked master records can be deleted.

Before cleanup, check links from knowledge test cases, tenant configuration, live agents, live channels, access categories, and public contexts. Frappe will prevent deletion when linked documents still exist.
""",
    },
    {
        "title": "DIGITZ AI Nexus - Runtime Diagnostics and Logs",
        "context": INTERNAL_CONTEXT,
        "sub_context": "Restricted Operations",
        "entity_type": "Runbook",
        "entity": "Diagnostics",
        "topic": "Logs",
        "access_policy": "Restricted",
        "priority": 8,
        "manual_content": """
Runtime diagnostics should inspect the resolved tenant context, resolved AI Agent Profile, allowed access policies, retrieved chunks, fallback usage, confidence score, and query log.

Nexus Query Log stores tenant, business unit, project, context, query, access status, retrieved chunks, answer preview, confidence, model, and error message. It should be used to confirm whether failures are caused by missing knowledge, missing embeddings, access filtering, tenant mismatch, or LLM errors.

When troubleshooting a public website chat failure, confirm that the query is routed through the public profile and that only Public policies are allowed. For internal failures, confirm the user profile assignment or System Manager admin bypass behavior.
""",
    },
]


def setup_digitz_nexus_website_knowledge(process_sources=True):
    """Idempotently create DIGITZ-NEXUS chat foundation and knowledge sources."""
    result = {
        "foundation": {},
        "sources": [],
        "processing": [],
    }

    ensure_foundation(result)

    for source in PUBLIC_SOURCES + INTERNAL_SOURCES + RESTRICTED_SOURCES:
        doc = upsert_knowledge_source(source)
        result["sources"].append({
            "name": doc.name,
            "title": doc.title,
            "access_policy": doc.access_policy,
            "status": doc.status,
        })

        if process_sources:
            result["processing"].append(process_knowledge_source(doc.name))

    frappe.db.commit()
    return result


def ensure_foundation(result):
    ensure_tenant()
    result["foundation"]["tenant"] = TENANT

    result["foundation"]["business_unit"] = ensure_master(
        "Nexus Business Unit",
        BUSINESS_UNIT,
        "business_unit_name",
        tenant=TENANT,
    )
    result["foundation"]["channel"] = ensure_live_channel()
    result["foundation"]["chat_category"] = ensure_chat_category()
    result["foundation"]["public_agent"] = ensure_live_agent(PUBLIC_AGENT, "Public AI Assistant", "Public Responder")
    result["foundation"]["internal_agent"] = ensure_live_agent(INTERNAL_AGENT, "Internal AI Assistant", "Internal Assistant")
    result["foundation"]["public_profile"] = ensure_profile(PUBLIC_AGENT, "Public website assistant.", "Public Access")
    result["foundation"]["internal_profile"] = ensure_profile(INTERNAL_AGENT, "Internal desk assistant.", "Internal Access")
    result["foundation"]["public_route"] = ensure_public_route(result["foundation"]["public_profile"])
    result["foundation"]["tenant_configuration"] = ensure_ecosystem()

    ensure_administrator_assignment(result["foundation"]["internal_profile"])


def ensure_tenant():
    if frappe.db.exists("Nexus Tenant", TENANT):
        doc = frappe.get_doc("Nexus Tenant", TENANT)
    else:
        doc = frappe.new_doc("Nexus Tenant")
        doc.tenant_code = TENANT

    doc.tenant_name = "DIGITZ AI Nexus"
    doc.disabled = 0
    doc.description = "Tenant for DIGITZ AI Nexus public website and internal chat."
    doc.save(ignore_permissions=True)
    return doc.name


def ensure_master(doctype, name, fieldname, tenant=None):
    if frappe.db.exists(doctype, name):
        doc = frappe.get_doc(doctype, name)
    else:
        doc = frappe.new_doc(doctype)
        doc.set(fieldname, name)

    if doc.meta.has_field("tenant"):
        doc.tenant = tenant
    if doc.meta.has_field("enabled"):
        doc.enabled = 1
    if doc.meta.has_field("description") and not doc.get("description"):
        doc.description = f"Master record for {name}."

    doc.save(ignore_permissions=True)
    return doc.name


def ensure_live_channel():
    if frappe.db.exists("Nexus Live Channel", CHANNEL):
        doc = frappe.get_doc("Nexus Live Channel", CHANNEL)
    else:
        doc = frappe.new_doc("Nexus Live Channel")
        doc.channel_code = CHANNEL

    doc.channel_name = "Website Chat"
    doc.channel_type = "Website Chat"
    doc.enabled = 1
    doc.public_access = 1
    doc.requires_visitor_email = 0
    doc.agent_based = 0
    doc.description = "Public website chat channel for DIGITZ AI Nexus."
    doc.save(ignore_permissions=True)
    return doc.name


def ensure_chat_category():
    if frappe.db.exists("Nexus Chat Category", CHAT_CATEGORY):
        doc = frappe.get_doc("Nexus Chat Category", CHAT_CATEGORY)
    else:
        doc = frappe.new_doc("Nexus Chat Category")
        doc.category_code = CHAT_CATEGORY

    doc.category_label = "Nexus Platform Know-How"
    doc.channel = CHANNEL
    doc.enabled = 1
    doc.requires_authentication = 0
    doc.identity_verification_mode = "None"
    doc.allow_public_fallback = 0
    doc.display_order = 10
    doc.description = "Public website category for DIGITZ AI Nexus product, platform, governance, Q&A, chat, support, and ERP know-how."
    doc.save(ignore_permissions=True)
    return doc.name


def ensure_live_agent(agent_code, agent_name, agent_role):
    if frappe.db.exists("Nexus Live Agent", agent_code):
        doc = frappe.get_doc("Nexus Live Agent", agent_code)
    else:
        doc = frappe.new_doc("Nexus Live Agent")
        doc.agent_code = agent_code

    doc.agent_name = agent_name
    doc.display_name = agent_name
    doc.agent_type = "AI"
    doc.agent_role = agent_role
    doc.status = "Idle"
    doc.enabled = 1
    doc.visibility = "Public" if agent_code == PUBLIC_AGENT else "Internal"
    doc.default_channel = CHANNEL
    doc.priority = 10
    doc.max_active_sessions = 10
    doc.description = f"{agent_name} for DIGITZ AI Nexus chat."
    doc.save(ignore_permissions=True)
    return doc.name


def ensure_profile(agent, purpose, access_category):
    existing = frappe.get_all(
        "Nexus AI Agent Profile",
        filters={"agent": agent},
        pluck="name",
        limit_page_length=1,
    )

    if existing:
        doc = frappe.get_doc("Nexus AI Agent Profile", existing[0])
    else:
        doc = frappe.new_doc("Nexus AI Agent Profile")
        doc.agent = agent

    doc.behavior_prompt = (
        "You are DIGITZ AI Nexus assistant. Answer only from approved knowledge. "
        "If approved knowledge is insufficient, say that you do not have enough approved knowledge."
    )
    doc.tone = "Professional"
    doc.response_style = "Balanced"
    doc.welcome_message = "Hello. How can I help you today?"
    doc.fallback_message = "I do not have enough approved knowledge to answer this."
    doc.do_not_answer_rules = "Do not invent facts. Do not reveal restricted knowledge to public users."
    doc.default_response_mode = "chat"
    doc.knowledge_scope = "Governed"
    doc.confidence_threshold = 0.65
    doc.escalation_enabled = 1
    doc.memory_mode = "Session"
    doc.system_notes = purpose
    doc.save(ignore_permissions=True)

    ensure_profile_access_category(doc.name, access_category)
    return doc.name


def ensure_profile_access_category(profile, access_category):
    existing = frappe.db.get_value(
        "Nexus AI Agent Profile Access Category",
        {"ai_agent_profile": profile, "access_category": access_category},
        "name",
    )

    if existing:
        doc = frappe.get_doc("Nexus AI Agent Profile Access Category", existing)
    else:
        doc = frappe.new_doc("Nexus AI Agent Profile Access Category")
        doc.ai_agent_profile = profile
        doc.access_category = access_category

    doc.enabled = 1
    doc.priority = 10
    doc.description = f"{access_category} for {profile}."
    doc.save(ignore_permissions=True)
    return doc.name


def ensure_public_route(profile):
    existing = frappe.db.get_value(
        "Nexus Category Identity Route",
        {
            "channel": CHANNEL,
            "chat_category": CHAT_CATEGORY,
            "identity_type": "Public",
        },
        "name",
    )

    if existing:
        doc = frappe.get_doc("Nexus Category Identity Route", existing)
    else:
        doc = frappe.new_doc("Nexus Category Identity Route")
        doc.channel = CHANNEL
        doc.chat_category = CHAT_CATEGORY
        doc.identity_type = "Public"

    doc.ai_agent_profile = profile
    doc.enabled = 1
    doc.priority = 10
    doc.description = "Public website route for DIGITZ AI Nexus."
    doc.save(ignore_permissions=True)
    return doc.name


def ensure_ecosystem():
    existing = frappe.db.get_value(
        "Nexus Tenant Configuration",
        {"tenant": TENANT, "ecosystem_name": "DIGITZ AI Nexus Website"},
        "name",
    )

    if existing:
        doc = frappe.get_doc("Nexus Tenant Configuration", existing)
    else:
        doc = frappe.new_doc("Nexus Tenant Configuration")
        doc.tenant = TENANT
        doc.ecosystem_name = "DIGITZ AI Nexus Website"

    doc.ecosystem_type = "Production"
    doc.enabled = 1
    doc.is_default = 1
    doc.activation_status = "Configured"
    doc.default_business_unit = BUSINESS_UNIT
    doc.require_approved_knowledge = 1
    doc.strict_tenant_mode = 1
    doc.default_top_k = 5
    doc.qa_enabled = 1
    doc.default_qa_channel = CHANNEL
    doc.live_chat_enabled = 1
    doc.default_chat_channel = CHANNEL
    doc.website_widget_enabled = 0
    doc.widget_title = "DIGITZ AI Nexus Assistant"
    doc.widget_welcome_message = "Hello. How can I help you today?"
    doc.testing_required_before_activation = 1
    doc.certification_status = "Not Certified"
    doc.notes = "Tenant configuration for DIGITZ AI Nexus public website and internal chat."
    doc.save(ignore_permissions=True)
    return doc.name


def ensure_administrator_assignment(profile):
    if not frappe.db.exists("User", "Administrator"):
        return None

    existing = frappe.db.get_value(
        "Nexus User Profile Assignment",
        {"user": "Administrator", "active": 1},
        "name",
    )

    if existing:
        return existing

    doc = frappe.new_doc("Nexus User Profile Assignment")
    doc.user = "Administrator"
    doc.ai_agent_profile = profile
    doc.active = 1
    doc.notes = "Default internal profile assignment for DIGITZ AI Nexus setup."
    doc.insert(ignore_permissions=True)
    return doc.name


def upsert_knowledge_source(source):
    if frappe.db.exists("Nexus Knowledge Source", source["title"]):
        doc = frappe.get_doc("Nexus Knowledge Source", source["title"])
    else:
        doc = frappe.new_doc("Nexus Knowledge Source")
        doc.title = source["title"]

    doc.source_type = "Manual"
    doc.manual_content = source["manual_content"].strip()
    doc.tenant = TENANT
    doc.business_unit = BUSINESS_UNIT
    doc.project = ""
    doc.context = source["context"]
    doc.sub_context = source["sub_context"]
    doc.entity_type = source["entity_type"]
    doc.entity = source["entity"]
    doc.topic = source["topic"]
    if doc.meta.has_field("chat_category"):
        doc.chat_category = source.get("chat_category") or CHAT_CATEGORY
    doc.access_policy = source["access_policy"]
    doc.status = "Published"
    doc.priority = source.get("priority", 0)
    doc.processing_status = "Pending"
    doc.embedding_status = "Pending"
    doc.diagnostics_status = "Pending"
    doc.retrieval_ready = 0
    doc.save(ignore_permissions=True)
    return doc
