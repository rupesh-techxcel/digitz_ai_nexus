import frappe

from digitz_ai_nexus.services.knowledge_source_defaults import (
    DEFAULT_KNOWLEDGE_SOURCE_ENTITY_TYPE,
)

# Classification constants — match existing tenant/BU/access configuration
TENANT = "NEXUS-AI"
BU = "NEXUS-AI-BU"
CONTEXT = "Website Public Chat"
SUB_CONTEXT = "Ask Anything About Nexus AI"
ACCESS_POLICY = "Public-NEXUS-AI"
SOURCE_TYPE = "Manual"
STATUS = "Draft"

# DocTypes that carry knowledge data — cleaned in dependency order
_CLEAN_DOCTYPES = [
    "Nexus Knowledge Index Entry",
    "Nexus Knowledge Chunk",
    "Nexus Knowledge Unit",
    "Nexus Knowledge Context Summary",
    "Nexus Knowledge Source",
]


# ---------------------------------------------------------------------------
# 10 knowledge sources extracted from nexus-ai-public-chat-knowledge-source.md
# ---------------------------------------------------------------------------

KNOWLEDGE_SOURCES = [

    {
        "title": "NEXUS AI — Platform Overview And Value",
        "topic": "Platform Overview And Value",
        "content": """\
# What Is NEXUS AI?

NEXUS AI is a governed AI knowledge and chat platform for organizations that want AI to answer from approved business knowledge rather than uncontrolled or improvised information.

The core concept is simple: a business should be able to use AI safely across website chat, customer support, internal knowledge, training, Q&A, and operational workflows while keeping control over what the AI can know, who can access it, and when a human should take over.

NEXUS AI is not only a chatbot. A chatbot is one use of the platform. NEXUS AI is better understood as a controlled AI operating layer for business knowledge. It helps organizations collect knowledge, classify it, approve it, make it searchable by AI, apply access rules, route conversations to the right AI behavior, and deliver answers through the right channel.

For public website visitors, NEXUS AI can act as a product assistant that explains what the platform does, how it helps organizations, what features are available, how public chat works, and how a visitor can request a demo or contact the team.

For businesses, NEXUS AI provides a way to turn approved knowledge into reliable AI experiences without allowing public visitors or unverified users to see private or internal content.

# Why NEXUS AI Exists

Many organizations want to use AI, but they face practical risks:

- General AI tools may answer from broad public training data rather than approved company knowledge.
- Employees and customers may receive inconsistent answers from different people or systems.
- Internal documents, policies, SOPs, product guides, and support knowledge are often scattered across files, portals, email threads, and individual experts.
- Public chatbots can become risky if they answer beyond approved public content.
- AI support tools may fail when they cannot escalate to a human with useful context.
- Multi-business or multi-tenant deployments need strong separation between one tenant's knowledge and another tenant's knowledge.

NEXUS AI addresses these problems by creating a governed knowledge foundation. The platform helps a business decide what knowledge is approved, who is allowed to access it, which AI experience may use it, and how answers should be delivered.

The result is AI that is useful, bounded, auditable, and aligned with business control.

# The Business Value Of NEXUS AI

NEXUS AI adds value by making approved business knowledge available through natural conversation while preserving governance.

The major value areas are:

1. Faster answers for website visitors — Public visitors can ask product, platform, capability, and demo-related questions through website chat and receive immediate answers from public approved knowledge.

2. Safer enterprise AI adoption — The AI does not need to rely on unapproved sources. It retrieves from a curated knowledge base and applies access rules before answering.

3. Reduced support workload — Common questions can be answered automatically. When the AI cannot answer, the conversation can be prepared for human follow-up with useful context.

4. Consistent product and policy messaging — Sales teams, support teams, customers, partners, and website visitors can receive consistent answers based on the same approved knowledge set.

5. Knowledge reuse across channels — The same governed knowledge foundation can support website chat, customer portal chat, internal user chat, Q&A, training assistants, and future workflow apps.

6. Better control over sensitive information — Public users receive public information. Verified customers, partners, employees, or administrators can be routed to different knowledge levels only when their identity and access rules permit it.

7. Continuous improvement — Unanswered questions, repeated questions, escalation patterns, and knowledge gaps can help the business improve its public content, support material, training documents, and operating procedures.

# Where NEXUS AI Is Positioned In The Industry

NEXUS AI is positioned in the enterprise AI platform category, with a specific focus on governed knowledge, controlled chat, identity-aware access, and operational AI experiences.

It sits between three familiar categories:

- Public AI chat tools, which are powerful but not always bounded to approved company knowledge.
- Traditional knowledge bases, which store documents but often require users to search manually.
- Customer support or helpdesk chat tools, which handle conversations but may not provide deep knowledge governance.

NEXUS AI combines these ideas into a governed AI platform. It is designed for organizations that want AI assistants, public website chat, internal Q&A, support automation, training, and ERP-style workflow assistance, but need stronger control than a general chatbot can provide.

The platform is especially relevant for businesses that care about approved and traceable answers, public and internal knowledge separation, customer and employee identity awareness, multi-tenant or multi-business deployments, human escalation when AI should not decide alone, business-owned configuration rather than heavy engineering dependency, and safe expansion from chat into workflow and operational assistance.

# Short Positioning Statement

NEXUS AI helps businesses build, govern, and operate AI experiences from approved knowledge. It combines public chat, governed knowledge retrieval, identity-aware access control, channel-based routing, configurable behavior, human escalation, agentic business assistance, Nexy Companion experiences, and extensible integration capabilities in one platform.

# One-Line Summary

NEXUS AI is a governed AI platform that turns approved business knowledge into safe, identity-aware chat, Q&A, support, training, workflow, agentic, and Nexy Companion experiences.
""",
    },

    {
        "title": "NEXUS AI — Platform Architecture And Workspaces",
        "entity": "Platform Architecture",
        "topic": "Platform Architecture And Workspaces",
        "content": """\
# NEXUS AI As A Platform

NEXUS AI is a platform because it provides reusable foundations for multiple AI experiences, not just one assistant.

The platform can support website public chat, product enquiry assistants, public Q&A, internal knowledge assistants, customer support assistants, training and onboarding assistants, SOP and policy guidance, ERP or business workflow assistants, human escalation and support handoff, and future agentic or task-oriented AI experiences.

The platform model matters because a business should not need separate, disconnected AI systems for every use case. NEXUS AI allows the same knowledge governance, access control, identity model, channel model, and behavior configuration to support different experiences.

For example, a public visitor may ask what NEXUS AI does through website chat. A verified customer may later ask a support question through a support channel. An internal employee may ask about an SOP through an internal assistant. These are different experiences, but they can all use the same governed platform principles.

# NEXUS Studio, NEXUS Administration, And NEXUS Live

NEXUS AI is organized around three major platform workspaces.

NEXUS Studio is the authoring workspace. It is where teams prepare knowledge, configure assistants, set chat categories, define behavior, test responses, and publish AI experiences. It helps business teams build AI experiences without writing code.

NEXUS Administration is the governance workspace. It helps manage tenants, users, access rules, knowledge policies, security settings, and audit controls. It is where the organization keeps the AI platform controlled and compliant.

NEXUS Live is the operations workspace. It is where live conversations, escalation queues, support handoffs, interaction outcomes, and platform performance can be monitored. It helps the organization operate AI experiences after they go live.

Together, these workspaces support the platform lifecycle: Build in Studio. Govern in Administration. Operate in Live.

# Main Features Included In NEXUS AI

NEXUS AI includes a wide set of platform capabilities:

- Public website chat powered by approved knowledge.
- Governed knowledge source management.
- AI-ready knowledge processing and retrieval.
- Public and internal Q&A experiences.
- Chat categories for routing topics.
- Channel configuration for website, portal, internal, API, and embedded experiences.
- Identity-aware access control.
- Public, customer, partner, employee, and admin knowledge boundaries.
- AI behavior profiles for tone, fallback, and escalation.
- Human escalation for complex or sensitive queries.
- Multi-tenant isolation for multiple businesses, brands, clients, or departments.
- Tenant-specific public chat, knowledge, channels, behavior, and operational logs.
- Query and conversation logging for review and improvement.
- Knowledge gap discovery from unanswered questions.
- Support for training, onboarding, SOP guidance, and operational assistance.
- Extensible integration model for ERP, CRM, helpdesk, and business workflow tools.
- Agentic AI capability for controlled business goals, drafts, approvals, and action assistance.
- Nexy Companion concept for role-based, guided, knowledge-grounded business conversations.

# Extensibility

NEXUS AI is designed to grow from public knowledge chat into broader business AI experiences.

Its extensibility can support additional website chat categories, separate assistants for different departments, verified customer support flows, internal employee assistants, training and onboarding modules, ERP and CRM data lookups through authorized tools, ticket creation and support handoff, workflow guidance and draft business actions, API-based AI experiences, multi-tenant service delivery, agentic capability packs for specific business domains, and Nexy Companion roles for sales, support, onboarding, partner, vendor, and custom journeys.

The platform approach means organizations can start with public website chat and later expand into customer support, internal knowledge, training, and operational assistance without rebuilding the governance model from scratch.
""",
    },

    {
        "title": "NEXUS AI — Knowledge Governance And RAG",
        "topic": "Knowledge Governance And RAG",
        "content": """\
# NEXUS AI As A Knowledge Repository

NEXUS AI acts as a governed repository for business knowledge.

A business can organize knowledge such as product information, public website content, frequently asked questions, support guides, standard operating procedures, HR policies, training guides, customer onboarding material, ERP process guides, compliance and governance notes, internal manuals, and troubleshooting documents.

Knowledge is not simply dumped into the AI. It is prepared, classified, reviewed, and made AI-ready. This helps ensure that the assistant answers from approved content and that public chat does not accidentally expose internal or restricted information.

From a visitor perspective, this means the website chat assistant can answer about NEXUS AI using published public information. If the approved public knowledge does not contain an answer, the assistant should say it does not have enough approved knowledge and suggest contacting the NEXUS AI team.

# Governed Knowledge And RAG

NEXUS AI can use retrieval augmented generation, commonly called RAG, as part of its answer process.

In simple terms, RAG means the AI first searches the approved knowledge base for relevant information and then generates an answer using that retrieved knowledge. This is different from asking an AI model to answer freely from general training data.

For public visitors, the benefit is that answers can stay grounded in the official public knowledge about NEXUS AI.

For businesses, the benefit is stronger control:

- The AI searches approved knowledge.
- The system applies tenant and access boundaries.
- Public chat can be limited to public knowledge.
- Answers can be based on retrieved content rather than speculation.
- If knowledge is missing, the assistant can fall back safely instead of guessing.

NEXUS AI may combine semantic search, keyword matching, context classification, and confidence checks to improve answer quality. These technologies are used behind the scenes to help retrieve the right information, but the visitor-facing promise is simple: the assistant should answer from approved knowledge and avoid unsupported claims.

# Safe Public Chat Boundaries

The public website assistant should answer only from public approved knowledge. It should avoid:

- Internal configuration details.
- Credentials, API keys, secrets, or infrastructure details.
- Private customer data.
- Account-specific support information.
- Restricted admin procedures.
- Debug logs, migration steps, or troubleshooting runbooks.
- Unapproved pricing commitments.
- Unsupported product timelines.
- Claims that are not present in approved public knowledge.

If a visitor asks for something outside public knowledge, the assistant should respond politely and direct the visitor to the official contact or support path.
""",
    },

    {
        "title": "NEXUS AI — Access Control And Identity",
        "topic": "Access Control And Identity",
        "content": """\
# Access Control And Information Security

NEXUS AI is designed around the principle that not every user should see every piece of knowledge.

The platform can separate knowledge by access level, identity type, tenant, business unit, context, and chat purpose. Public content can be served publicly. Internal content can be reserved for verified employees. Customer support content can be reserved for verified customers. Restricted or sensitive content can require stronger authorization.

For public website chat, the assistant should only use knowledge marked as public. It should not expose private customer data, internal procedures, credentials, restricted configuration, or admin-only information.

Access control in NEXUS AI is applied before an answer is generated. That means the AI should retrieve only the knowledge the current user and current chat route are allowed to access. If a public visitor asks for internal information, the assistant should not reveal it. It can politely explain that it can answer only from approved public knowledge.

This makes NEXUS AI suitable for organizations that need AI with business governance, not just conversational ability.

# Identity Types And Public Chat

NEXUS AI can serve different identity types through the same platform.

Examples of identity types include public visitor, verified customer, partner, internal employee, support agent, administrator, and training participant. Each identity type can receive a different level of knowledge access and a different chat experience.

A public visitor does not need authentication for general product information. Public website chat can answer questions about the NEXUS AI concept, capabilities, governance, use cases, public positioning, and demo direction.

A verified customer may be able to access additional support content if the business enables a verified support flow.

An internal employee may access internal SOPs, policies, training material, or operational knowledge through an authenticated internal channel.

The important point is that identity does not automatically unlock everything. Identity helps route the user to the right knowledge boundary and the right assistant behavior. The narrower approved boundary always wins.

# Authentication And Verification Mechanisms

NEXUS AI can support multiple authentication and verification patterns depending on the channel and use case.

Common patterns include no authentication for public website chat when only public knowledge is allowed, logged-in user sessions for internal employees or portal users, email-based verification for known customers or visitors who need a verified support flow, registered email checks for customer, partner, or training access, and enterprise identity integration such as SSO where required by the organization.

Public chat should remain simple and low-friction. A visitor can ask public questions without logging in. When a question requires private or account-specific information, the assistant should direct the visitor to a secure verified support or contact process.
""",
    },

    {
        "title": "NEXUS AI — Channel System And Chat Categories",
        "entity": "Channel System",
        "topic": "Channel System And Chat Categories",
        "content": """\
# Channel System In NEXUS AI

The channel system defines where a conversation comes from and how it should be handled.

Examples of channels include website chat widget, website Q&A, customer portal, internal desk or intranet, mobile app, API-based assistant, and embedded business application.

Each channel can have its own purpose, audience, behavior, and available chat categories. A website public chat channel is usually designed for product information, public FAQs, demo guidance, and visitor enquiry. An internal channel may be designed for employee help, SOPs, policies, or operational workflows.

Channels help the platform deliver the right AI experience in the right place while keeping governance consistent.

For public website visitors, channels are usually a logical backend mechanism rather than a visitor-facing choice. A visitor does not need to understand or select a channel. The website chat widget can gather the published chat categories from all enabled website-chat channels for the active tenant, then show those categories as simple visitor options.

This keeps the visitor experience clean. The visitor selects a topic such as Ask Anything About Nexus AI, while NEXUS AI uses the selected category to understand the related channel, routing context, identity behavior, and knowledge boundary.

In this model, a channel can have multiple chat categories. A tenant can also have multiple website-chat channels, for example separate logical channels for product enquiries, sales conversations, support, partner discussions, or future campaign-specific experiences. The widget can still present the visitor with one category list instead of asking the visitor to choose a channel first.

Channels may become useful later for richer intent handling, analytics, business reporting, campaign separation, or channel-specific behavior. Even when hidden from visitors, they remain valuable as a logical configuration and governance layer.

# Chat Categories

A chat category tells NEXUS AI what kind of conversation the user wants to have.

For the public website, the category Ask Anything About Nexus AI can be used as the visitor-facing category for general product and platform questions.

This category can cover what NEXUS AI is, how NEXUS AI adds value, website public chat capabilities, knowledge governance, access control, identity-aware chat, human escalation, platform features, business use cases, and demo and contact direction.

In a broader deployment, other categories could be configured for Customer Support, Pricing Enquiry, Partner Onboarding, HR Help, ERP Assistance, Training, or Internal Operations. Each category can route to a different assistant behavior and knowledge boundary.

A chat category belongs to a channel internally. That relationship lets NEXUS AI know the logical context of the category without asking the visitor to choose the channel directly. For example, a public widget may show Ask Anything About Nexus AI, Book a Demo, and Partner Enquiry as categories. Behind the scenes, those categories may belong to one or more website-chat channels for the same tenant.

When a visitor selects a category, NEXUS AI can infer the channel from the category. The routing layer can then decide which AI profile, identity profile, and knowledge access should apply.

# Category And Identity Routing

NEXUS AI uses category and identity routing to decide how a selected conversation should be handled.

The public idea is simple: the visitor sees and selects a chat category, the selected category implies the logical channel, the visitor's identity type is resolved such as public visitor or verified user, and NEXUS AI uses the category and identity context to select the right assistant behavior and knowledge boundary.

This allows the same public widget to remain simple while still supporting governed routing behind the scenes.

For example, a public visitor selects Ask Anything About Nexus AI and NEXUS AI routes the conversation to a public product assistant that uses public NEXUS AI knowledge. A verified customer selects a support-related category and NEXUS AI routes the conversation to a customer support assistant with a different knowledge boundary, if that verified flow is enabled. An internal user can use internal categories through authenticated channels and receive access only to the knowledge allowed for their role and identity profile.

The route is not meant to expose technical complexity to the visitor. Its purpose is to connect a selected category and identity context to the correct AI behavior, knowledge profile, access policies, and escalation rules.
""",
    },

    {
        "title": "NEXUS AI — AI Behavior And Human Escalation",
        "entity": "AI Behavior",
        "topic": "AI Behavior And Human Escalation",
        "content": """\
# Behavior Attributes

NEXUS AI supports behavior attributes so each assistant can respond in a way that fits its purpose.

Behavior attributes can include assistant role and persona, tone such as professional, warm, concise, technical, or explanatory, welcome message, fallback message when approved knowledge is missing, response style, confidence threshold, escalation behavior, do-not-answer rules, and instructions about what topics are out of scope.

For public website chat, the behavior should be helpful, clear, professional, and careful. The assistant should answer visitor questions using approved public knowledge, avoid private or unsupported claims, and guide users to contact the NEXUS AI team when a topic needs human follow-up.

Behavior configuration is separate from knowledge access. The assistant's tone can change without changing what knowledge it is allowed to retrieve.

# Human Escalation

NEXUS AI can hand a conversation to a human when AI should not continue alone.

Escalation can be useful when the visitor asks for a demo, pricing discussion, partnership conversation, or implementation consultation, when the question is outside approved public knowledge, when the visitor needs account-specific or private support, when the topic is sensitive or requires approval, when the visitor explicitly asks to speak with a person, or when the assistant cannot answer confidently.

In a support scenario, escalation can pass the conversation thread and a summary to a human team so the visitor does not need to repeat everything. For public website chat, escalation should guide the visitor to the official contact path or support process.

Escalation is a planned part of the NEXUS AI platform design. The system does not attempt to answer every question. It recognizes when a human is the better path and prepares the handoff with relevant context.
""",
    },

    {
        "title": "NEXUS AI — Multi-Tenancy",
        "topic": "Multi-Tenancy",
        "content": """\
# Multi-Tenancy In NEXUS AI

NEXUS AI can accommodate multiple tenants in one governed platform.

A tenant is an isolated business space inside NEXUS AI. A tenant can represent a customer, company, brand, department, website, business unit, implementation environment, or managed-service client. Each tenant can have its own knowledge, channels, chat categories, public context, business defaults, users, access boundaries, widget settings, and operational records.

The purpose of multi-tenancy is to let one platform serve many independent business contexts without mixing their knowledge or conversations.

For example, a service provider can operate one Nexus platform for multiple client organizations. A group company can run separate tenants for different brands or subsidiaries. A large organization can separate public website chat, internal employee help, customer support, and training into different tenant spaces. A deployment can keep production, trial, demo, or test environments separate.

In a multi-tenant Nexus setup, each tenant can maintain its own public website knowledge, internal knowledge, support knowledge, training and onboarding content, chat channels, chat categories, AI behavior profiles, access policies, default public context and business unit, query logs and conversation history, escalation and support routing preferences, and widget configuration for website chat.

Multi-tenancy is important because the same question may require different answers for different organizations or business contexts. For example, one tenant's support policy, pricing explanation, onboarding guide, escalation route, or product configuration may be different from another tenant's. NEXUS AI keeps those contexts separated so the answer is based on the active tenant's approved knowledge and rules.

Tenant isolation works together with access control. The tenant defines the business space. Access control defines what a specific user or identity type may retrieve inside that space. A public visitor in one tenant should not retrieve another tenant's knowledge. A verified customer should not automatically see internal employee content. An employee in one tenant should not see another tenant's private knowledge unless the platform has been deliberately configured for a controlled shared scenario.

Tenant configuration can also define safe defaults. For example, a tenant can have a default website chat channel, a default Q&A channel, a default public context, a default business unit, a fallback message, and a requirement that only approved knowledge should be used. These defaults help the platform behave consistently when a conversation starts.

For website public chat, multi-tenancy means each website or brand can have its own public assistant. The assistant can answer from that tenant's public knowledge, show the tenant's published website chat categories, and follow that tenant's public behavior rules. If the same Nexus platform serves multiple websites, each website can still have its own knowledge boundary and visitor experience.

For internal or customer support scenarios, multi-tenancy allows each tenant to keep its own customer knowledge, SOPs, escalation rules, and support history. Support teams can manage conversations without cross-tenant data exposure.

The public value of multi-tenancy in NEXUS AI is simple: one platform can support many business environments, but each environment remains governed, separated, and controlled.

Question: How does NEXUS AI support multi-tenancy?

Answer: NEXUS AI can separate the platform into tenant spaces. Each tenant can have its own knowledge, channels, chat categories, public context, behavior rules, access boundaries, widget settings, query logs, and conversation history. This allows one Nexus platform to serve multiple companies, brands, departments, or websites while keeping their knowledge and conversations separated.

Question: Can different companies or brands use the same Nexus platform separately?

Answer: Yes. NEXUS AI can support a managed multi-tenant model where each company, brand, business unit, or client has its own isolated tenant space. Public website chat, support knowledge, internal knowledge, and agentic or Nexy companion behavior can be configured per tenant so each business context receives the right answers and governance.
""",
    },

    {
        "title": "NEXUS AI — Agentic AI And Nexy Companion",
        "topic": "Agentic AI And Nexy Companion",
        "content": """\
# Agentic AI Capabilities In NEXUS AI

NEXUS AI is designed to move beyond answering questions into controlled agentic assistance.

Agentic AI means the system can help pursue a business goal, not only respond to a single question. An agentic assistant can understand an objective, gather relevant context, choose from approved capabilities, prepare a draft action, request approval when needed, and record what happened.

In NEXUS AI, agentic capability is still governed by the same platform principles. The agent works within a tenant and business context. It uses approved knowledge and configured capability rules. It can use only registered tools or approved action paths. Sensitive, customer-facing, vendor-facing, or business-impacting actions can require human approval. Actions and decisions can be logged for review. The agent does not get uncontrolled access to every system or every piece of data.

This makes NEXUS AI suitable for business assistance where AI needs to help with a process, not merely answer a question.

Examples of agentic capabilities include preparing outreach drafts for sales campaigns, scoring or qualifying a lead from approved criteria, suggesting the next action for a prospect or customer conversation, checking whether a contact should not be approached, preparing supplier or vendor follow-up drafts, helping coordinate purchase-related communication, creating ticket-ready or task-ready summaries, and notifying the right team when a meaningful business signal appears.

The public message is that NEXUS AI can support controlled business agents. These agents can assist with work, but they remain bounded by knowledge, identity, access rules, approval gates, and auditability.

# Nexy: The NEXUS AI Companion

Nexy is the role-based AI companion concept built on the NEXUS AI platform.

Nexy is best understood as a business companion that can be configured for a specific role. The role defines how Nexy communicates, what objective it supports, what knowledge it may use, when it should escalate, and what it must never claim or do.

Nexy is not a generic free-form bot. It is a controlled companion that works inside the Nexus governance model.

Nexy can be configured for different business roles, such as Sales Companion, Customer Success Companion, HR Onboarding Companion, Partner Management Companion, Vendor Qualification Companion, Field Service Companion, Support Proactive Companion, and custom business companion.

The first practical concept is Nexy as a Sales Companion. In that role, Nexy acts as a consultative guide for visitors or prospects. It helps understand the visitor's needs, connects those needs to relevant product or service information, handles common concerns from approved knowledge, and invites the next step without pressuring the visitor.

Nexy as Companion is useful because business conversations are not only about answering facts. A visitor may be exploring a problem, comparing options, asking whether NEXUS AI fits their organization, or deciding whether to request a demo. Nexy can support that journey with a guided, helpful, knowledge-grounded conversation.

As a companion, Nexy can listen to the visitor's question and business context, answer from approved knowledge, ask clarifying questions when the user's need is unclear, explain relevant capabilities and use cases, keep the tone aligned with the configured role, avoid prohibited claims and unsupported commitments, escalate when the visitor needs a human specialist, and preserve conversation context for better handoff.

For public website chat, Nexy can be positioned as a helpful companion for understanding NEXUS AI. It can guide visitors through the platform concept, features, governance, use cases, and demo path. It should not make private commitments, expose internal settings, or discuss restricted implementation details.

# Nexy And Agentic AI Together

Nexy and the Agentic AI capability complement each other.

Nexy is the role-based companion experience: the personality, role, communication style, objective, guardrails, and conversation behavior.

Agentic AI is the controlled action capability: the ability to work toward goals through approved capability packs, tools, drafts, approvals, memory, and decision logs.

Together, they allow NEXUS AI to support a business assistant that can both converse and help move work forward.

For example, a website visitor asks whether NEXUS AI can help reduce repetitive support work. Nexy explains the relevant support and knowledge capabilities from public knowledge, then suggests a demo if the visitor wants to explore the fit. A prospect asks a sales-related question. Nexy answers consultatively, handles concerns using approved knowledge, and can route the conversation to a human when needed. A support user describes a problem. A companion can collect the right context, provide approved guidance, and prepare a structured handoff when the issue needs a person. In an internal setting, an agentic assistant can help prepare drafts, tasks, follow-ups, or summaries, while approval rules prevent unsafe direct action.

This is the direction of NEXUS AI: from governed answers, to guided conversations, to controlled business assistance.

Question: What is Nexy?

Answer: Nexy is the role-based AI companion concept built on the NEXUS AI platform. Nexy can be configured for a business role, such as a Sales Companion, Customer Success Companion, HR Onboarding Companion, Partner Companion, or Support Companion. Its role controls how it communicates, what objective it supports, what knowledge it can use, and when it should escalate.

Question: How does Nexy work as a companion?

Answer: Nexy works as a guided companion rather than a generic bot. It listens to the visitor's question, answers from approved knowledge, asks clarifying questions when useful, connects the visitor's needs to relevant capabilities, avoids unsupported claims, and can escalate to a human specialist when needed.

Question: Is Nexy the same as a chatbot?

Answer: No. A chatbot usually focuses on conversation. Nexy is designed as a role-based companion on top of the Nexus platform. It can use the same governed knowledge and access model as Nexus chat, but its purpose is broader: to guide a business conversation or goal with configured behavior, role rules, and escalation boundaries.

Question: What are Agentic AI capabilities in NEXUS AI?

Answer: Agentic AI capabilities allow NEXUS AI to help with business goals, not only answer questions. For example, the platform can support controlled assistance for drafting outreach, preparing follow-ups, classifying replies, creating task-ready summaries, or coordinating business actions. These capabilities remain governed by approved tools, access rules, approval gates, and audit logs.
""",
    },

    {
        "title": "NEXUS AI — Use Cases And Business Applications",
        "entity": "Use Cases",
        "topic": "Use Cases And Business Applications",
        "content": """\
# How NEXUS AI Can Be Utilized

NEXUS AI can be utilized in many business scenarios.

Website product assistant: A company can use NEXUS AI on its website to answer visitor questions about products, features, use cases, demos, and contact options.

Customer support assistant: A support team can use NEXUS AI to answer common customer questions, collect issue details, suggest next steps, and prepare unresolved cases for a human agent.

Internal knowledge assistant: Employees can ask questions about SOPs, HR policies, finance processes, procurement workflows, IT support, or training material. Access can be scoped by employee identity and role.

Training assistant: New employees, partners, or customers can ask questions from approved training content. NEXUS AI can explain steps, provide checklists, and help users learn business processes conversationally.

ERP assistant: NEXUS AI can support ERP users by explaining workflows, helping locate information, preparing draft actions, or guiding users through approved processes when integrations are enabled.

Agentic business assistant: NEXUS AI can support goal-oriented assistance such as drafting outreach, preparing follow-ups, classifying replies, identifying next actions, and creating approval-ready business outputs. Human approval can be required before sensitive or external-facing actions happen.

Nexy Companion: Nexy can act as a role-based companion for public visitors, sales conversations, customer success journeys, onboarding, partner management, vendor qualification, or support follow-up. The companion experience can be configured by role, tone, objective, escalation policy, and knowledge boundary.

Compliance and policy assistant: Teams can ask policy questions and receive controlled answers from approved compliance documents. Sensitive cases can be routed to human review.

Multi-tenant managed platform: Service providers or larger organizations can operate separate knowledge spaces for different clients, brands, business units, or departments while maintaining platform-level governance.

Question: Can NEXUS AI support customer service?

Answer: Yes. NEXUS AI can answer common customer questions from approved knowledge, collect issue details, suggest next steps, and prepare unresolved cases for a human agent through the escalation flow.

Question: Can NEXUS AI support internal employee knowledge?

Answer: Yes. Employees can ask questions about SOPs, HR policies, finance processes, and training material through an authenticated internal channel. Access is scoped to what the employee's identity and role is permitted to retrieve.

Question: Can NEXUS AI be used for training?

Answer: Yes. New employees, partners, or customers can ask questions from approved training content. NEXUS AI can explain steps, provide checklists, and help users learn business processes conversationally.

Question: Can NEXUS AI integrate with ERP or business systems?

Answer: Yes. NEXUS AI is designed to be extensible. It can be connected with ERP, CRM, helpdesk, reporting, and workflow systems when authorized integrations are configured. Public chat can explain these capabilities, while private data access should require authentication and permission.
""",
    },

    {
        "title": "NEXUS AI — Public Visitor Q&A And Demo Guidance",
        "entity": "Visitor QA",
        "topic": "Public Visitor Q&A And Demo Guidance",
        "content": """\
# Example Public Visitor Questions

The public website assistant should be able to answer questions such as what is NEXUS AI, how does NEXUS AI work, how is NEXUS AI different from a normal chatbot, what business problems does NEXUS AI solve, can NEXUS AI power website chat, can NEXUS AI answer only from approved knowledge, what is RAG and how does NEXUS AI use it, how does NEXUS AI protect internal knowledge, can different users receive different answers, can public visitors see internal content, what are chat categories, what are channels in NEXUS AI, what are behavior attributes, what happens when the AI cannot answer, can NEXUS AI escalate to a human, can NEXUS AI support customer service, can NEXUS AI support internal employee knowledge, can NEXUS AI be used for training, what are Agentic AI capabilities in NEXUS AI, what is Nexy, how is Nexy used as a companion, is Nexy the same as a chatbot, can NEXUS AI integrate with ERP or business systems, how does NEXUS AI support multi-tenancy, can different companies or brands use the same Nexus platform separately, what are NEXUS Studio, NEXUS Administration, and NEXUS Live, and how can I request a demo.

# Example Answers For Public Chat

Question: What is NEXUS AI?

Answer: NEXUS AI is a governed AI knowledge and chat platform. It helps organizations deliver AI assistants that answer from approved business knowledge, apply access controls, support public and internal chat, and escalate to humans when needed.

Question: How is NEXUS AI different from a normal chatbot?

Answer: A normal chatbot may answer from a fixed script or from broad AI knowledge. NEXUS AI is built around governed knowledge. It retrieves from approved sources, applies access rules, respects user identity, and can support multiple channels such as website chat, internal Q&A, customer support, and workflow assistance.

Question: Can public website visitors use NEXUS AI?

Answer: Yes. NEXUS AI can power public website chat. Public visitors can ask about products, features, use cases, governance, demo options, and other public information. Public chat should use only approved public knowledge.

Question: Can public visitors see private information?

Answer: No. Public chat should be limited to public knowledge. Internal, restricted, customer-specific, or admin-only information should require the appropriate verified route and access permission.

Question: What happens if NEXUS AI does not know the answer?

Answer: If the answer is not available in approved knowledge, the assistant should not guess. It should explain that it does not have enough approved information and guide the visitor to contact the NEXUS AI team or use the appropriate support path.

Question: Can NEXUS AI support multiple types of users?

Answer: Yes. NEXUS AI can serve public visitors, verified customers, partners, employees, support agents, and administrators. Each identity type can have its own knowledge boundary and chat behavior.

Question: What is the role of access control?

Answer: Access control decides which knowledge the assistant is allowed to retrieve for the current user and chat purpose. This helps ensure that public users receive public information while private or restricted knowledge remains protected.

Question: What is the channel system?

Answer: A channel is the place where a conversation happens, such as a website chat widget, customer portal, internal desk, mobile app, or API. Channels help NEXUS AI deliver the right assistant experience in the right environment.

Question: What are behavior attributes?

Answer: Behavior attributes define how an assistant should respond. They can include tone, role, welcome message, fallback message, confidence threshold, escalation rules, and do-not-answer rules.

Question: What business problems does NEXUS AI solve?

Answer: NEXUS AI helps organizations reduce scattered knowledge, inconsistent answers, repetitive support work, and the risk of exposing information to the wrong audience. It turns approved business content into governed answers for public visitors, customers, and employees while preserving access boundaries and human escalation paths.

Question: What is RAG and how does NEXUS AI use it?

Answer: RAG means retrieval-augmented generation. Before producing an answer, NEXUS AI retrieves relevant chunks from approved knowledge that the current user is allowed to access. The retrieved evidence grounds the response, and when suitable approved evidence is unavailable the assistant should use a safe fallback instead of guessing.

Question: What are chat categories?

Answer: Chat categories describe the purpose of a conversation, such as product enquiry, customer support, internal help, or training. NEXUS AI uses the selected category with the channel and identity route to choose the appropriate assistant behavior, knowledge access boundary, and escalation path.

Question: What are NEXUS Studio, NEXUS Administration, and NEXUS Live?

Answer: NEXUS Studio is the authoring workspace for preparing knowledge, configuring assistants, testing answers, and publishing AI experiences. NEXUS Administration is the governance workspace for tenants, identities, access policies, and security controls. NEXUS Live is the operations workspace for live conversations, escalation queues, human handoff, and service monitoring.

Question: What are Agentic AI capabilities in NEXUS AI?

Answer: Agentic AI capabilities allow NEXUS AI to help with business goals, not only answer questions. The platform can support controlled assistance for drafting outreach, preparing follow-ups, classifying replies, creating task-ready summaries, or coordinating business actions. These capabilities remain governed by approved tools, access rules, approval gates, and audit logs.

Question: What is Nexy?

Answer: Nexy is the role-based AI companion concept built on the NEXUS AI platform. Nexy can be configured for a business role such as a Sales Companion, Customer Success Companion, HR Onboarding Companion, Partner Companion, or Support Companion. Its role controls how it communicates, what objective it supports, what knowledge it can use, and when it should escalate.

Question: How is Nexy used as a companion?

Answer: Nexy works as a guided companion rather than a generic bot. It listens to the visitor's question, answers from approved knowledge, asks clarifying questions when useful, connects the visitor's needs to relevant capabilities, avoids unsupported claims, and can escalate to a human specialist when needed.

# Demo And Contact Guidance

Visitors who want to evaluate NEXUS AI should request a demo or contact the NEXUS AI team through the website.

A demo can cover how public website chat works, how knowledge is prepared and governed, how access control protects private information, how chat categories and channels are configured, how NEXUS AI can support customer support, training, internal knowledge, and ERP-style workflows, how human escalation can be handled, and how the platform can fit a visitor's industry, business model, or operational context.

When a visitor asks for a demo, the assistant can suggest sharing name and organization, business email, main use case, preferred channel such as website chat, internal assistant, support, training, or ERP assistance, and any current challenge with knowledge, support, or AI adoption.

Question: How can I request a demo?

Answer: You can request a demo by contacting the NEXUS AI team through the website. It helps to share your name and organization, business email, main use case, and any current challenge you are trying to solve with AI. The team can then show you how the platform fits your specific context.
""",
    },

]


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def clean_knowledge_data():
    """Delete all knowledge sources and related records. Preserves tenant, BU, access policy."""
    deleted = {}
    for dt in _CLEAN_DOCTYPES:
        names = frappe.get_all(dt, pluck="name")
        deleted[dt] = len(names)
        for name in names:
            frappe.delete_doc(dt, name, ignore_permissions=True, force=True)
    frappe.db.commit()
    return {"deleted": deleted}


def create_knowledge_sources():
    """Create 10 classified knowledge sources from the NEXUS AI public chat content."""
    created = []
    for ks in KNOWLEDGE_SOURCES:
        doc = frappe.get_doc({
            "doctype": "Nexus Knowledge Source",
            "title": ks["title"],
            "source_type": SOURCE_TYPE,
            "tenant": TENANT,
            "business_unit": BU,
            "context": CONTEXT,
            "sub_context": SUB_CONTEXT,
            "entity": ks.get("entity") or "",
            "entity_type": DEFAULT_KNOWLEDGE_SOURCE_ENTITY_TYPE,
            "topic": ks["topic"],
            "access_policy": ACCESS_POLICY,
            "status": STATUS,
            "project": "",
            "manual_content": ks["content"].strip(),
        })
        doc.insert(ignore_permissions=True)
        created.append({"name": doc.name, "topic": ks["topic"]})
    frappe.db.commit()
    return {"created": created}


def sync_knowledge_source_content(source_name):
    """Refresh one existing source from its maintained seed definition."""
    source_data = next(
        (item for item in KNOWLEDGE_SOURCES if item["title"] == source_name),
        None,
    )
    if not source_data:
        frappe.throw(f"Seed content not found for Knowledge Source: {source_name}")
    if not frappe.db.exists("Nexus Knowledge Source", source_name):
        frappe.throw(f"Knowledge Source not found: {source_name}")

    doc = frappe.get_doc("Nexus Knowledge Source", source_name)
    doc.manual_content = source_data["content"].strip()
    doc.entity_type = DEFAULT_KNOWLEDGE_SOURCE_ENTITY_TYPE
    doc.entity = source_data.get("entity") or ""
    doc.topic = source_data["topic"]
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {
        "source": doc.name,
        "content_length": len(doc.manual_content or ""),
        "status": doc.status,
        "processing_status": doc.processing_status,
    }


def reset_and_seed_knowledge():
    """Full reset: clean all knowledge data then seed 10 classified sources."""
    clean_result = clean_knowledge_data()
    seed_result = create_knowledge_sources()
    return {
        "cleaned": clean_result["deleted"],
        "seeded": len(seed_result["created"]),
        "sources": seed_result["created"],
    }


def _approve_all_source_answers(source_name):
    """Approve all User Question index entries for a source (Pending Review + Rejected)."""
    pending = frappe.get_all(
        "Nexus Knowledge Index Entry",
        filters={
            "knowledge_source": source_name,
            "entry_type": "User Question",
            "answer_review_status": ["in", ["Pending Review", "Rejected"]],
        },
        pluck="name",
    )
    if pending:
        now = frappe.utils.now_datetime()
        user = frappe.session.user
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
        frappe.db.commit()
    return len(pending)


def seed_and_process():
    """
    Clean → Seed (Draft) → Process each source.
    Stops after processing. Approve answers, validate, and publish are done manually.
    """
    from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source

    clean_result = clean_knowledge_data()
    seed_result = create_knowledge_sources()

    results = []
    for source_info in seed_result["created"]:
        source_name = source_info["name"]
        try:
            proc = process_knowledge_source(source_name)
            results.append({
                "name": source_name,
                "status": proc.get("status"),
                "chunks": proc.get("chunk_count", 0),
                "index_entries": proc.get("index_entry_count", 0),
            })
        except Exception as exc:
            results.append({"name": source_name, "status": "FAILED", "error": str(exc)})

    succeeded = sum(1 for r in results if r.get("status") == "success")
    failed = [r["name"] for r in results if r.get("status") != "success"]

    return {
        "cleaned": clean_result["deleted"],
        "seeded": len(seed_result["created"]),
        "processed": succeeded,
        "failed": failed,
        "details": results,
    }


def full_lifecycle_pipeline():
    """
    Complete governed lifecycle for all 10 knowledge sources:
      1. Clean existing knowledge data
      2. Seed 10 sources as Draft
      3. Process each source (chunking + embedding + LLM index entries + LLM auto-validation)
      4. Approve remaining User Question answers (Pending Review or auto-Rejected)
      5. Validate each source (LLM test query — sets validation_status=Passed, status=Ready to Publish)
      6. Publish each source (activates chunks, sets retrieval_ready=1)

    This follows the documented lifecycle exactly:
      Draft → Processed → [Approve Answers] → [Validate] → Ready to Publish → Published
    """
    from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source
    from digitz_ai_nexus.api.nexus_knowledge_studio import (
        validate_knowledge_source,
        publish_knowledge_source,
    )

    # Step 1 + 2: Clean and seed as Draft
    clean_result = clean_knowledge_data()
    seed_result = create_knowledge_sources()

    results = []

    for source_info in seed_result["created"]:
        source_name = source_info["name"]
        entry = {"name": source_name, "steps": {}}

        # Step 3: Process (chunks + embeddings + LLM index entries + auto-validation of questions)
        try:
            proc = process_knowledge_source(source_name)
            entry["steps"]["process"] = proc.get("status", "unknown")
            if proc.get("status") != "success":
                entry["steps"]["process"] = f"FAILED: {proc.get('error', proc)}"
                results.append(entry)
                continue
        except Exception as exc:
            entry["steps"]["process"] = f"FAILED: {exc}"
            results.append(entry)
            continue

        # Step 4: Approve any remaining answers not auto-approved by LLM
        approved_count = _approve_all_source_answers(source_name)
        entry["steps"]["approve_answers"] = f"Approved {approved_count} remaining entries"

        # Step 5: Validate (LLM test query against source content; must pass to reach Ready to Publish)
        try:
            val = validate_knowledge_source(source_name)
            entry["steps"]["validate"] = val.get("message", "unknown")
            if not val.get("success"):
                entry["steps"]["validate"] = f"FAILED: {val.get('message')}"
                results.append(entry)
                continue
        except Exception as exc:
            entry["steps"]["validate"] = f"FAILED: {exc}"
            results.append(entry)
            continue

        # Step 6: Publish (activates chunks, sets retrieval_ready=1)
        try:
            pub = publish_knowledge_source(source_name)
            entry["steps"]["publish"] = pub.get("message", "unknown")
            entry["retrieval_ready"] = pub.get("retrieval_ready", 0)
            if not pub.get("success"):
                entry["steps"]["publish"] = f"FAILED: {pub.get('message')}"
        except Exception as exc:
            entry["steps"]["publish"] = f"FAILED: {exc}"

        results.append(entry)

    succeeded = sum(1 for r in results if r.get("retrieval_ready"))
    failed = [r["name"] for r in results if "FAILED" in str(r.get("steps", {}))]

    return {
        "cleaned": clean_result["deleted"],
        "seeded": len(seed_result["created"]),
        "retrieval_ready": succeeded,
        "failed": failed,
        "details": results,
    }
