"""
DIGITZ AI Nexus — Website Knowledge Seed
=========================================
Standalone, idempotent seed for the DIGITZ AI Nexus public website chat.

Creates:
  - Tenant:           DIGITZ-AI-NEXUS
  - Business Unit:    DIGITZ AI NEXUS
  - Live Channel:     NEXUS-WEBSITE-CHAT
  - Q&A Channel:      NEXUS-WEBSITE-QA
  - Chat Category:    NEXUS-PLATFORM-KNOW-HOW
  - AI Agent Profile: NEXUS-PUBLIC-ASSISTANT  (public website assistant)
  - Access governance scoped to DIGITZ-AI-NEXUS tenant
  - Category Identity Route for Public visitors
  - Tenant Configuration
  - 16 knowledge sources derived from the public website (index.html + nexus-platform.html)

NOT called during installation.  Run manually via bench console:

    from digitz_ai_nexus.devtools.seed_digitz_nexus_homepage_knowledge import seed_nexus_website_knowledge
    seed_nexus_website_knowledge()

Or to create the foundation only (no knowledge processing):

    seed_nexus_website_knowledge(process_sources=False)
"""

import frappe

from digitz_ai_nexus.setup.access_seed import seed_default_access_governance
from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source


# ── Identity constants ─────────────────────────────────────────────────────────

TENANT_CODE       = "DIGITZ-AI-NEXUS"
TENANT_NAME       = "DIGITZ AI Nexus"
BUSINESS_UNIT     = "DIGITZ AI NEXUS"
PUBLIC_CONTEXT    = "DIGITZ AI NEXUS WEBSITE"
CHANNEL_CODE      = "NEXUS-WEBSITE-CHAT"
QA_CHANNEL_CODE   = "NEXUS-WEBSITE-QA"
CATEGORY_CODE     = "NEXUS-PLATFORM-KNOW-HOW"
CATEGORY_LABEL    = "Nexus Platform Know-How"
AGENT_CODE        = "NEXUS-PUBLIC-ASSISTANT"
AGENT_NAME        = "Nexus Public Assistant"
AGENT_DISPLAY     = "Nexus Assistant"
CONFIG_NAME       = "DIGITZ AI Nexus Website"


# ── Knowledge source definitions ───────────────────────────────────────────────
# 16 sources covering the full public website content.
# Co-Founder and Co-Worker are noted as in production but not yet released.

HOMEPAGE_SOURCES = [

    # 1 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Platform Overview and Value Proposition",
        "entity_type": "Platform",
        "entity": "DIGITZ AI Nexus",
        "topic": "Platform Overview and Value Proposition",
        "priority": 10,
        "manual_content": """
DIGITZ AI Nexus is a governed AI knowledge and chat platform built by Techxcel Technologies. It turns approved business knowledge into controlled AI experiences for websites, customers, employees, support teams, training programmes, SOP guidance, and ERP-aware business operations.

The core positioning of DIGITZ AI Nexus is: Your Business Context Powered by Intelligent AI Workflows.

DIGITZ AI Nexus is not a generic AI assistant. It is a purpose-built platform that ensures every AI response is sourced from knowledge that the business has approved, classified, and published. The platform does not allow the AI to answer from unverified or out-of-scope content.

The primary problem Nexus solves is safe and governed AI adoption for organisations. Businesses can make their knowledge available through public website chat, internal desk chat, Q&A widgets, support workflows, and future AI assistant experiences — without losing control over what the AI says.

The three AI products available on the Nexus platform are Nexus AI Chat Bot, Nexus AI Q&A, and Nexus AI Apps. Every product runs on the same governed knowledge pipeline, identity layer, and multi-tenant architecture.

DIGITZ AI Nexus is designed for multi-tenant deployment. Each tenant on the platform is a fully isolated business workspace with its own knowledge base, AI agents, channels, users, and settings. There is no cross-tenant data exposure by design.

The platform is 100% no-code for business configuration. Business teams can define chat bots, Q&A experiences, knowledge sources, identity rules, access policies, and escalation workflows without requiring engineering resources.

The platform is built and operated by Techxcel Technologies. Organisations interested in deploying DIGITZ AI Nexus can request a demo or contact the Nexus team through the website.

DIGITZ AI Nexus is suitable for any organisation that needs to make approved knowledge available through conversational AI — including businesses in professional services, enterprise software, manufacturing, financial services, education, healthcare operations, and government-adjacent sectors.

The value chain of the platform is: approved knowledge is loaded, classified, and processed in Nexus Studio; governance and compliance are enforced through Nexus Administration; live conversations, escalations, and support operations are managed through Nexus Live.
""",
    },

    # 2 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Nexus AI Chat Bot Product",
        "entity_type": "Product",
        "entity": "Nexus AI Chat Bot",
        "topic": "Chat Bot Capabilities and Commercial Use Cases",
        "priority": 9,
        "manual_content": """
Nexus AI Chat Bot is a governed conversational AI product on the DIGITZ AI Nexus platform. It enables organisations to deploy AI-powered chat experiences on their website, customer portal, or internal tools — all controlled by approved knowledge and identity-based access rules.

The core value of Nexus AI Chat Bot is governed conversational AI. Every chat response is sourced from knowledge the business has explicitly approved. Visitors always receive answers within the approved knowledge boundary. The AI does not invent responses or answer from unapproved content.

Nexus AI Chat Bot is not a generic AI chatbot. Each chat bot deployed on Nexus is a designated AI agent — named, behaviourally configured, and assigned to a specific audience and business role. A bot deployed for public website visitors behaves differently from one deployed for verified customers or internal employees.

The Chat Bot can be deployed on public websites to answer visitor questions about products and services. It can be deployed on customer portals to give verified customers account-specific support. It can be deployed on internal intranets to help employees access approved internal knowledge.

Multiple chat bots can run simultaneously on the same tenant. Each bot is independently configured with its own audience, knowledge scope, response style, and escalation rules.

The Chat Bot integrates with the Nexus identity and access layer. Before the bot responds to any question, it resolves who the user is. The user's identity category — Public Visitor, Verified Customer, Business Partner, Internal Employee, or Training Participant — determines which knowledge the bot is permitted to retrieve and use.

Chat Bot conversations are fully auditable. Every query, retrieved knowledge source, and AI response is logged in the Nexus platform. Conversation logs are available for quality review, compliance checks, and operational improvement.

The Chat Bot supports human escalation. When a conversation reaches a defined trigger point — such as a complex query, a request requiring approval, a sensitive topic, or customer frustration — the bot hands the conversation to a human agent. The full conversation thread and an AI-generated summary are passed to the agent on handover, so the human does not need to ask the customer to repeat themselves.

Typical commercial use cases for Nexus AI Chat Bot include public product enquiries, website visitor qualification, customer support conversations, internal HR and policy Q&A, employee onboarding guidance, and sales lead engagement.
""",
    },

    # 3 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Designated Chat Bot Configuration and Chat Categories",
        "entity_type": "Product Feature",
        "entity": "Nexus AI Chat Bot",
        "topic": "Designated Bot Configuration and Chat Categories",
        "priority": 9,
        "manual_content": """
A Nexus AI Chat Bot is a designated AI agent — purpose-built, behaviourally defined, and configured for a specific audience and business role. It is not a generic assistant that answers all questions from all people.

Each designated bot on the Nexus platform is configured with eight core traits:

Persona: The bot is given a business name and identity. It presents itself consistently as a defined agent, not an anonymous AI.

Tone and Behaviour: The communication style, language formality, and response boundaries are configured to match the business context. A public sales bot can be conversational and welcoming. An internal compliance assistant can be formal and precise.

Knowledge Scope: Each bot is assigned to specific knowledge sources and access categories. The bot only retrieves knowledge from the content it has been configured to use.

Access Policy: Identity-level gating is applied. The bot enforces access boundaries so that users can only receive information appropriate to their verified identity category.

Escalation Rules: Conditions that trigger a handover to a human agent are defined per bot. The business controls when the AI stops handling a conversation and passes it to a person.

Tool Permissions: The actions a bot is permitted to take — such as querying data, raising a ticket, or accessing ERP information — are controlled by role-based permissions configured per bot.

Brand Voice: The bot communicates consistently in the brand tone defined for it. Every conversation response reflects the business identity, not a generic AI voice.

Performance Tracking: Each bot has its own analytics and performance review so the business can monitor response quality, resolution rate, escalation frequency, and knowledge gaps specific to that bot.

Multiple designated bots can run simultaneously on a single tenant. This allows a business to deploy separate bots for public visitors, verified customers, internal employees, and partner portals — all running in parallel on the same platform.

Nexus supports eight pre-defined chat categories covering the most common business conversation types:

Sales Enquiry: For handling product or service interest, pricing context, availability questions, and lead qualification from public or partner audiences.

Customer Support: For resolving customer issues, answering account questions, tracking requests, and escalating unresolved cases to support agents.

Partner Portal: For business partner interactions including deal support, programme details, co-sell materials, and partner-specific pricing conversations.

HR and People: For employee questions about policies, leave, benefits, payroll, and workplace matters — governed by internal access policies.

Training and Learning: For guiding employees through learning content, onboarding sequences, assessments, and role-specific training material.

SOPs and Process: For operational staff who need step-by-step guidance from approved Standard Operating Procedures and process documents.

ERP Assistance: For users who need to perform or query ERP-related tasks through an AI interface — governed by business tool permissions and approval workflows.

IT Helpdesk: For internal technology support — troubleshooting, access requests, software guidance, and IT policy questions.

Any of these categories can be enabled and assigned to specific audience types per tenant. The same bot can serve multiple categories, or separate bots can be configured for each.
""",
    },

    # 4 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Human Escalation",
        "entity_type": "Product Feature",
        "entity": "DIGITZ AI Nexus",
        "topic": "Human Escalation System",
        "priority": 9,
        "manual_content": """
Human escalation is a core capability of DIGITZ AI Nexus. It ensures that when a conversation reaches a point where human judgement, authority, or empathy is required, the AI hands the conversation over to the right human agent — with complete context intact.

Escalation in Nexus is not a failure state. It is a designed handoff point built into the platform from the start. Businesses define the conditions that trigger escalation, and the platform enforces those rules automatically in every conversation.

Nexus AI Chat Bot supports eight escalation trigger types:

Complex Query: The user's question cannot be answered from approved knowledge, or the question involves nuance, multiple conditions, or expert judgement beyond the bot's configured scope.

Approval Required: The request involves an action, decision, or commitment that requires human authorisation. The bot recognises this and hands off rather than acting without approval.

Policy Exception: The user's situation falls outside standard policy. A human agent is better positioned to assess exceptions and decide on appropriate responses.

Identity Verification: The user's claimed identity cannot be confirmed through automated means. A human agent can complete the verification or decide how to proceed.

Sensitive Topic: The conversation involves a sensitive, emotional, legal, financial, or confidential matter that requires human care and judgement.

Tool Limitation: The AI agent reaches the boundary of its permitted tool access and cannot complete the requested action without human intervention.

Customer Frustration: The platform detects signals that the user is dissatisfied, upset, or has expressed frustration with AI responses. A human agent takes over to manage the experience.

Out of Scope: The user's request falls entirely outside the knowledge domain or permitted actions of the configured bot. Rather than attempting an out-of-scope response, the bot escalates cleanly.

When escalation is triggered, the human agent receives the full AI conversation thread, an AI-generated summary of the issue, the escalation reason, and the recommended action. The agent does not need to ask the customer to explain themselves again. Context is complete from the moment the agent picks up the conversation.

Escalation routing can be configured per trigger type. Different trigger types can route to different agent teams or queues — for example, approval requests going to a manager queue while frustration escalations go to a senior support team.

The escalation system is visible in Nexus Live, where agents monitor the escalation queue, pick up conversations, take over from the AI, and resolve or close cases. Resolution analytics track escalation rates, trigger distribution, agent response times, and resolution outcomes.
""",
    },

    # 5 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Identity and Access Categories",
        "entity_type": "Product Feature",
        "entity": "DIGITZ AI Nexus",
        "topic": "Identity and Access Categories",
        "priority": 9,
        "manual_content": """
DIGITZ AI Nexus uses an identity and access category system to ensure every user receives the right AI experience — and only the right AI experience. The platform resolves who a user is before determining what knowledge they can access and which AI agent handles their conversation.

The identity layer is not bolted on after AI responses are generated. It is built into the knowledge retrieval model. The AI agent checks user identity before selecting knowledge to retrieve, so access boundaries are enforced at the source — not as a post-generation filter.

Nexus supports five standard identity categories out of the box. Custom categories can also be configured per tenant.

Public Visitor: A user who has not authenticated and whose identity has not been verified. Public visitors can access product information, service overviews, pricing context, and general enquiries. They cannot access account-specific, internal, or restricted knowledge. A public visitor on the DIGITZ AI Nexus website can ask about the product, its features, how it works, and how to request a demo.

Verified Customer: A user who has authenticated as an existing customer. Verified customers can access account information, order history, support resolution, and status updates relevant to their account. They receive more specific and detailed responses than public visitors, limited to their own account context.

Business Partner: A user who has been identified as an authorised business partner. Partners can access partner pricing information, deal support materials, programme details, co-sell content, and partner-specific guidance. This category allows the platform to serve partner portals with controlled access to commercially sensitive information.

Internal Employee: An authenticated employee of the organisation. Internal employees can access HR policies, Standard Operating Procedures, IT helpdesk guidance, operational reference materials, and internal knowledge that is not appropriate for public or customer audiences.

Training Participant: A user engaged in a learning or onboarding programme. Training participants can access course content, onboarding guides, assessments, and role-specific SOP materials. The training identity category allows the platform to deliver structured learning experiences from approved training knowledge.

Identity is resolved through configured rules per tenant. Resolution methods include session token validation, authenticated login state, domain-based identification, IP range, or explicit verification steps initiated by the bot during the conversation. The bot can also prompt a user to verify their identity mid-conversation if a question requires a higher access level than their current confirmed identity.

If identity cannot be confirmed, the platform applies an identity fallback rule — typically defaulting to public visitor access with a prompt to verify before proceeding with sensitive queries.

The identity and access system means that the same chat bot or Q&A experience can serve multiple audience types. The platform determines what each user can see based on who they are — not based on which page they landed on.
""",
    },

    # 6 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Nexus AI Q&A Product",
        "entity_type": "Product",
        "entity": "Nexus AI Q&A",
        "topic": "Q&A Capabilities and Use Cases",
        "priority": 9,
        "manual_content": """
Nexus AI Q&A is a structured knowledge access product on the DIGITZ AI Nexus platform. It gives visitors and customers a self-service knowledge layer that delivers instant, accurate answers sourced directly from the business's published and approved knowledge — without requiring a full chat conversation.

The core value of Nexus AI Q&A is instant knowledge access. A user submits a question, and the platform retrieves the answer from the approved knowledge base and presents it in a clear, structured format. There are no hallucinations and no out-of-scope responses. Every answer is sourced from content the business has explicitly approved.

Nexus AI Q&A is distinct from the Chat Bot. Chat Bot is a conversational experience with dialogue flow, context memory, and escalation. Q&A is a focused, question-and-answer experience designed for users who want a direct answer from a specific knowledge domain. Both products run on the same governed knowledge pipeline — there is no duplication of content management.

Q&A experiences are topic-bounded. Each Q&A deployment is configured to answer within a defined knowledge scope — for example, product features, pricing context, return policies, support procedures, or HR policies. The Q&A experience does not attempt to answer outside that scope. If a question falls outside the approved knowledge, the platform provides a clear out-of-scope response rather than guessing.

The platform supports suggested question sets in Q&A experiences. These guide users towards the most valuable queries within the configured knowledge domain, making the experience more productive and reducing the likelihood of unanswered questions.

Source citation can be configured per Q&A deployment. The business can choose to show users which approved document or content item provided the answer, supporting transparency and trust.

Answer confidence thresholds are configurable. If the platform's confidence in a retrieved answer falls below the configured threshold, the Q&A experience will indicate that the question could not be answered with sufficient confidence, rather than presenting a low-quality response.

Nexus AI Q&A runs on the same multi-tenant, identity-aware infrastructure as Chat Bot. A verified customer accessing a Q&A experience receives answers calibrated to their identity category. A public visitor receives answers limited to public knowledge only.

Typical commercial use cases for Nexus AI Q&A include self-service product knowledge bases, public FAQ experiences on websites, internal policy reference tools for employees, partner knowledge portals, and post-sale customer support knowledge libraries.
""",
    },

    # 7 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Knowledge Classification and Governance",
        "entity_type": "Platform Capability",
        "entity": "DIGITZ AI Nexus",
        "topic": "Knowledge Classification Hierarchy and Governance",
        "priority": 8,
        "manual_content": """
DIGITZ AI Nexus uses a five-level knowledge classification hierarchy to ensure structured knowledge retrieval. The hierarchy is designed so that the right knowledge reaches the right person, and nothing else does.

The five levels of the knowledge classification hierarchy are:

Tenant: The top-level business entity. Every piece of knowledge belongs to a tenant. Tenants are fully isolated from each other — each tenant has its own knowledge base, AI agents, channels, and settings. No knowledge from one tenant can be accessed by another.

Context: The broad topic domain within a tenant. Context represents the major business areas the AI agents operate within. Examples include Sales, Support, HR, and Operations. Context helps the platform narrow retrieval to the relevant subject area before applying more specific filters.

Sub-Context: The specific topic within a context domain. Sub-context enables precise retrieval by narrowing further to exactly the right subject. Examples include Pricing, Returns, Leave Policy, and SLA. A question about leave policy retrieves only knowledge classified under Leave Policy within HR context — not all HR knowledge.

Business Unit: The organisational division within a tenant. Business unit allows the same context and sub-context to contain different answers for different teams or regions. For example, UK Sales and APAC Support can hold different pricing and support content that remains separated and correctly served to the right audience.

Project: A time-bounded initiative with its own scoped knowledge. Project-level knowledge is used for specific campaigns, launches, onboarding cohorts, or events. Project knowledge can be archived when the project closes, keeping the knowledge base clean and current.

This five-level classification system means that when a user asks a question, the platform retrieves knowledge that matches the user's tenant, the relevant context domain, the specific sub-context topic, the user's assigned business unit scope, and any active project scope. The intersection of these filters produces a precise retrieval result that is accurate to the user's actual situation.

From a governance perspective, knowledge classification serves as the foundation of access control. Access policies are applied at the knowledge level, not at the response level. This means the AI cannot retrieve knowledge it is not permitted to retrieve — regardless of how a question is phrased.

For businesses, this means: knowledge entered into the system is automatically scoped to the right audience before any AI response is generated. A question asked by a public visitor can only retrieve public knowledge, even if the knowledge base also contains internal or restricted content. There is no risk of information leaking to the wrong audience through the AI.
""",
    },

    # 8 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — The Three Platform Workspaces",
        "entity_type": "Platform",
        "entity": "Nexus Platform",
        "topic": "Platform Workspaces Overview",
        "priority": 8,
        "manual_content": """
The DIGITZ AI Nexus platform is structured around three purpose-built workspaces: Nexus Studio, Nexus Administration, and Nexus Live. Every chat bot, Q&A experience, and workflow app deployed on the platform is built, governed, and operated through these three workspaces.

The Nexus Platform is described by its headline: Build. Govern. Operate. AI Your Business Controls.

Key platform facts: 3 platform workspaces, 100% no-code configuration, multi-tenant architecture isolated by design.

Before any chat bot responds, any Q&A answers, or any workflow app runs — the three platform workspaces work together to configure, govern, and monitor every AI experience the business deploys.

Nexus Studio is the authoring workspace. It is where AI experiences are designed and built. Studio is used to create and configure chat bots, define knowledge sources, set identity rules, design escalation logic, and test everything before deployment. Studio is a no-code environment that business teams — not engineering teams — operate.

Nexus Administration is the governance workspace. It manages tenants, users, platform-wide rules, and compliance across every deployment. Administration is where multi-tenant isolation is enforced, user permissions are defined, knowledge governance policies are set, and the audit trail is maintained.

Nexus Live is the operations workspace. It is where the platform operates in real time once AI experiences are live. Live provides visibility into every active conversation, escalation queue management, support ticket handling, performance dashboards, SLA tracking, and anomaly alerts.

The three workspaces are complementary and interdependent. Studio creates the AI experiences. Administration governs and secures them. Live operates and monitors them. A business deploying Nexus gains access to all three from day one.

The flow between workspaces is: Studio configures, Administration governs, Live operates. When Nexus Live surfaces a knowledge gap through analytics, the business uses Studio to add or improve knowledge sources. When Administration detects a policy breach, Studio can be updated to enforce the corrected rules. The workspaces reinforce each other continuously.

Organisations interested in understanding how these workspaces would serve their specific deployment scenario are encouraged to request a demo through the DIGITZ AI Nexus website.
""",
    },

    # 9 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Nexus Studio Workspace",
        "entity_type": "Platform Workspace",
        "entity": "Nexus Studio",
        "topic": "Studio Features and Capabilities",
        "priority": 8,
        "manual_content": """
Nexus Studio is the authoring workspace of the DIGITZ AI Nexus platform. It is the complete environment where every AI experience deployed on the platform is designed, configured, tested, and published. Studio is a no-code workspace — business teams configure everything without engineering support.

Nexus Studio provides seven key capabilities:

Chat Bot Builder: Studio enables the design and configuration of multi-purpose chat bots without writing any code. Business teams define the bot's name and persona, greeting message, fallback response for unanswerable questions, response tone (formal, conversational, technical, or custom), and audience assignment. Bots are bound to specific channels — website widget, customer portal, internal intranet, or embedded iframe. Multiple bots can be configured per tenant and deployed concurrently. A bot preview and test console is available before publishing.

Knowledge Source Management: Studio is where business knowledge is loaded, structured, and approved before the AI is allowed to use it. Supported import formats include PDF, DOCX, TXT, XLSX, and HTML. URL-based ingestion allows approved web pages to be scraped and indexed. Manual content entry supports structured Q&A pairs, FAQs, and SOP documents. All content goes through a review and approval workflow. Version control retains previous content versions. Content expiry and scheduled review dates can be configured. A knowledge coverage report identifies gaps before going live.

Identity Rules and User Category Configuration: Studio is where identity resolution rules are defined. Business teams configure which user categories are served, how identity is resolved (session token, login state, domain, IP, or explicit verification), what knowledge each category can access, and what the bot is permitted to say to each category. The bot can prompt users to verify identity mid-conversation when a higher-access question is asked.

Q&A Flow Designer: Studio enables the design of dedicated Q&A experiences separate from chat. Q&A flows are topic-bounded and knowledge-scoped. Studio allows configuration of suggested question sets, answer confidence thresholds, out-of-scope handling, and source citation behaviour.

Workflow App Configuration: Nexus Apps are purpose-built AI experiences for specific business functions — and they are configured entirely in Studio. Each app has its own workflow design, knowledge scope, access policy, user path, and output format. Available app types include Onboarding Guide, SOP Navigator, Training Assistant, Support Desk, HR Helpdesk, ERP Assistant, Knowledge Portal, and Process Workflow.

Escalation Trigger Design: Studio is where escalation behaviour is defined. Business teams configure which conditions cause the AI to hand over to a human agent — including trigger types, routing rules, trigger sensitivity controls, the context package passed to the agent on handover, the message shown to the user when escalation happens, and re-escalation rules when the agent queue is unavailable.

Test, Preview, and Deployment Controls: Before any bot, Q&A experience, or app goes live, Studio provides a comprehensive testing environment. Teams can simulate conversations as any user category, test which knowledge sources are used in responses, trigger each escalation type to verify routing, and check identity scenario behaviour. Publishing is one-click. Rollback to a previous published version is supported. Deployment follows a staged pipeline: Draft, Review, Approved, Published.
""",
    },

    # 10 ────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Nexus Live Workspace",
        "entity_type": "Platform Workspace",
        "entity": "Nexus Live",
        "topic": "Live Operations Monitoring and Escalation Features",
        "priority": 8,
        "manual_content": """
Nexus Live is the operations workspace of the DIGITZ AI Nexus platform. It is the real-time operations centre where every live conversation, escalation, support ticket, and agent interaction across all tenants is visible and managed. Nexus Live gives business operations teams the visibility and control needed to run AI communication at enterprise scale.

Nexus Live provides six key capabilities:

Live Conversation Monitor: The monitor shows every active chat session across all tenants in real time. For each session, the monitor displays conversation status (Active, Waiting, Escalated, Resolved, Abandoned), the current stage of the conversation, the bot handling it, the user identity category, and the time elapsed. Operations managers see a live pulse of the entire platform without opening individual sessions. Any live conversation can be drilled into instantly. The view can be filtered per tenant or shown across all tenants.

Escalation Queue and Agent Console: When the AI reaches a defined escalation trigger, the conversation is handed to a human agent through a structured queue. The escalation queue is prioritised by trigger type and SLA status. When an agent picks up a conversation, the full AI conversation thread is already loaded in the agent console. An AI-generated summary and recommended action are provided. Agent assignment can be manual or automatic based on team availability. Agents can reply in-console, add internal notes, and update ticket status in one view. Escalation reasons are tagged for reporting and audit purposes.

Support Ticket Management: Every unresolved or escalated interaction can be converted into a tracked support ticket directly from Nexus Live. Tickets carry the full AI conversation, user context, escalation reason, and priority classification. Auto-ticket creation can be triggered on escalation or by agent request. Priority levels are Critical, High, Medium, and Low — set by AI or the agent. The ticket lifecycle follows: Open, In Progress, Pending, Resolved, Closed. SLA clocks run per ticket based on priority. Agents can add notes, attachments, and internal comments. Resolution confirmation and customer satisfaction capture are supported.

Performance Dashboards and Analytics: Nexus Live includes real-time and historical dashboards tracking platform performance. Metrics include total conversations, sessions, and active users across tenants; auto-resolution rate; escalation rate by trigger type, bot, tenant, and time period; average first response time and resolution time; SLA compliance rate per priority tier; knowledge coverage gap analysis showing questions the AI could not answer; agent performance metrics including pickup time, resolution time, and customer satisfaction score; and volume trends by hour, day, week, and month.

Multi-Tenant Visibility and Isolation: Nexus Live supports full multi-tenant operations. Administrators can view activity across all tenants in aggregate or switch to a focused single-tenant view. Tenant data, conversations, and tickets remain isolated at all times. Per-tenant health scores track conversation volume, resolution rate, and SLA health. Cross-tenant comparison is available for multi-business deployments.

Alerts, Anomaly Detection, and SLA Breach Warnings: Nexus Live actively monitors the platform for conditions requiring attention. Configurable alerts include SLA breach warnings before the deadline, escalation surge alerts when volume exceeds a defined threshold, knowledge failure alerts when the AI cannot resolve above a set rate, and session abandonment spike detection. Alert routing options include in-console notification, email, or webhook. Alert history and acknowledgment logs are maintained.
""",
    },

    # 11 ────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Nexus Administration Workspace",
        "entity_type": "Platform Workspace",
        "entity": "Nexus Administration",
        "topic": "Governance, Compliance, and Platform Control Features",
        "priority": 8,
        "manual_content": """
Nexus Administration is the governance workspace of the DIGITZ AI Nexus platform. It is the governance backbone that enforces multi-tenant isolation, defines user roles and permissions, manages knowledge policies, records every AI action in an audit trail, and controls the technical security and integration layer. If Nexus Studio is where AI experiences are built, Nexus Administration is where they are controlled and kept safe.

Nexus Administration provides six key capabilities:

Multi-Tenant Workspace Management: Each tenant on the Nexus platform is a fully isolated business workspace. Administration enables tenant provisioning — a new tenant workspace can be configured in minutes. Each tenant profile stores the business name, type, industry, contact, and deployment region. Tenant status is managed through states: Active, Suspended, Maintenance, Trial, and Archived. Per-tenant feature flags allow specific platform capabilities to be enabled or disabled per tenant. Tenant resource quotas control conversation limits, storage allocation, agent seats, and API call limits. Tenant-level domain and channel binding is managed from Administration. A tenant health overview tracks usage, performance, SLA status, and knowledge coverage for each tenant.

User Management, Roles, and Permissions: Administration manages every user on the platform. Platform roles include Super Admin, Tenant Admin, Studio Author, Knowledge Manager, Live Agent, Operations Viewer, and Read-Only Auditor. Permissions are scoped per workspace, per tenant, per bot, and per knowledge set. User invitation workflows support role pre-assignment. Two-factor authentication enforcement is configurable per role or tenant. Session management supports active session review, forced logout, and login history. IP restriction and access time window controls are available per user group. All role changes are recorded in an audit trail.

Knowledge Governance and Content Policy: Administration sets the platform-level rules for all knowledge. Platform-wide content policy defines what content categories are permitted. An approval authority matrix specifies which roles can approve which content types. Content expiry enforcement ensures expired content is automatically withheld from AI responses. Sensitive topic classification flags content that requires additional access control. A content dispute workflow enables knowledge accuracy issues to be raised, reviewed, and resolved. Cross-tenant knowledge sharing rules control what platform-level content individual tenants can access.

Audit Trail and Compliance Reporting: Every action on the Nexus platform — by AI or human — is recorded in a tamper-evident audit trail. The audit log includes the full AI decision log covering every query, retrieval source, and response; the human action log covering every agent interaction, ticket update, and console action; and the admin action log covering every configuration change, role update, and policy edit. The audit log is searchable and filterable by user, tenant, action type, date range, and outcome. Exports are available in CSV, JSON, and PDF formats for regulatory submission. Immutable log retention is configurable per compliance requirement. Compliance report templates are available for GDPR, data access, content governance, and user activity reporting.

Platform Security and Integration Settings: Administration controls the security and connectivity layer of the platform. This includes API key generation and lifecycle management per tenant or integration, webhook configuration for event-driven integration with external systems, SSO and SAML integration for enterprise identity provider binding, data residency settings specifying storage region per tenant, allowed origin and CORS policy for widget embedding, rate limiting and abuse protection configuration, platform health monitoring covering uptime, response latency, and API error rates, and scheduled maintenance mode per tenant.

Subscription, Licensing, and Usage Management: For organisations deploying Nexus as a managed service or multi-client platform, Administration provides subscription and licence management. Subscription tier assignment per tenant covers Trial, Starter, Professional, and Enterprise tiers. Usage tracking covers conversations, active users, knowledge storage, agent seats, and API calls. Quota alert thresholds notify tenant administrators before a limit is reached. Overage policies can be configured for graceful degradation or hard stop at the limit. Billing period and renewal management, and usage reports for internal cost allocation or client invoicing, are also supported.
""",
    },

    # 12 ────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Nexus Co-Founder (Coming Soon)",
        "entity_type": "Product",
        "entity": "Nexus Co-Founder",
        "topic": "Leadership AI for Founders and Business Owners",
        "priority": 7,
        "manual_content": """
Nexus Co-Founder is a purpose-built AI experience on the DIGITZ AI Nexus platform designed for business founders, owners, and senior leaders. It acts as an AI business partner for strategy, policy alignment, growth tracking, and decision intelligence.

Nexus Co-Founder is currently in production and will be publicly released soon. It is not yet generally available. Visitors interested in early access or in learning more about Nexus Co-Founder are encouraged to contact the DIGITZ AI Nexus team to register their interest.

The positioning of Nexus Co-Founder is: Your AI business partner for strategy, policy, growth, and decision intelligence. It helps founders and owners keep the business aligned with its goals by making approved business context available through a governed AI experience built specifically for leadership.

Nexus Co-Founder is designed to help business leadership ask questions such as: Is the business moving in the right direction? Where is money, time, or focus being lost? Which policies are drifting from their defined intent? Which opportunities or risks need founder-level attention?

The key capabilities being built into Nexus Co-Founder include:
Tracks goals and growth direction — helps leadership stay connected to business objectives and measure progress against them.
Monitors policy alignment — surfaces when operational practice diverges from defined policy, so leadership can intervene early.
Identifies risks and bottlenecks — draws on approved business knowledge to highlight operational, financial, or strategic risks before they escalate.
Preserves decisions and reasoning — captures and stores leadership decisions with their rationale, creating an accessible record of business direction over time.
Summarises business health — produces structured summaries of business state from approved data and knowledge sources, reducing the time leaders spend gathering context.
Supports strategic planning — helps founders and owners work through planning questions with context-grounded AI assistance.

The core value of Nexus Co-Founder is business success alignment. It is designed to make approved business knowledge and strategic context available to leadership in a governed, conversational format — so the people responsible for the business can ask informed questions and receive grounded answers without searching across systems and reports.

As with all Nexus products, Nexus Co-Founder will run on the same governed knowledge pipeline, identity layer, and multi-tenant architecture as the rest of the platform.
""",
    },

    # 13 ────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Nexus Co-Worker (Coming Soon)",
        "entity_type": "Product",
        "entity": "Nexus Co-Worker",
        "topic": "Employee AI Productivity and Daily Work Assistance",
        "priority": 7,
        "manual_content": """
Nexus Co-Worker is a purpose-built AI experience on the DIGITZ AI Nexus platform designed for employees and operational teams. It acts as an AI-powered work companion that helps staff complete daily work faster, more accurately, and with better access to approved business knowledge.

Nexus Co-Worker is currently in production and will be publicly released soon. It is not yet generally available. Organisations interested in understanding how Nexus Co-Worker could support their teams are encouraged to contact the DIGITZ AI Nexus team to discuss their requirements.

The positioning of Nexus Co-Worker is: Your AI-powered work companion for everyday business tasks. It supports employees across functions — sales, support, HR, accounts, operations, and more — by putting approved knowledge at their fingertips during their normal working day.

Nexus Co-Worker is designed to help employees ask questions such as: How do I complete this task correctly? What is the approved process for this situation? What does the policy say? Can you summarise this customer or project information? What should I do next?

The key capabilities being built into Nexus Co-Worker include:
Answers internal process questions — employees can ask how to complete specific tasks and receive step-by-step guidance sourced from approved internal SOPs and procedures.
Guides daily tasks and workflows — structured workflow guidance helps staff follow the correct sequence for complex or multi-step business processes.
Retrieves approved knowledge — employees access the relevant internal knowledge for their role without searching across systems, documents, or shared drives.
Drafts replies and summaries — Nexus Co-Worker can assist with drafting email responses, case summaries, customer communications, and internal reports using approved context.
Supports cross-functional teams — applicable across sales, customer support, HR, accounts, operations, and other departments where staff need consistent, policy-aligned guidance.
Escalates when human action is needed — when a question or task requires human authority, approval, or specialist judgement, Nexus Co-Worker escalates with full context, just as the Chat Bot does.

The core value of Nexus Co-Worker is daily work productivity. It reduces the time employees spend searching for information, chasing approvals, and re-reading policy documents — and replaces that friction with governed, instant, AI-assisted answers sourced from content the organisation has explicitly approved.

Nexus Co-Worker will run on the same governed knowledge pipeline, identity layer, and access control architecture as all other Nexus products. Knowledge available to an employee through Nexus Co-Worker is exactly what they are permitted to access based on their role and identity category — no more, no less.
""",
    },

    # 14 ────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Commercial Value and Solutions Summary",
        "entity_type": "Commercial",
        "entity": "DIGITZ AI Nexus",
        "topic": "Commercial Value, Solutions, and Deployment Scenarios",
        "priority": 8,
        "manual_content": """
DIGITZ AI Nexus is a commercially deployable AI platform that combines public website communication, verified customer support, internal knowledge access, ERP-aware automation, and training enablement in one business-ready solution.

The commercial summary of the platform is: One governed platform. Chat Bots, Q&A, and Apps — all in one. One platform. Three powerful AI experiences. Governed by identity, knowledge, and access from day one.

The platform is positioned for organisations that need to deploy AI responsibly. Instead of letting AI answer freely from uncontrolled sources, Nexus ensures every AI response is grounded in knowledge the business has approved, classified, and published. This makes AI deployment safe, auditable, and commercially credible.

Six core commercial capabilities delivered by DIGITZ AI Nexus:

AI Chat Bots for public, customer, and internal audiences: Multi-tenant chat bots handle public website visitors, verified customers, and internal staff. Each audience receives responses governed by its own identity category, knowledge scope, and access policy. A single platform deployment can serve all three audiences simultaneously.

Governed Q&A driven by approved business knowledge: Q&A experiences deliver verified answers from the curated knowledge base. There are no hallucinations and no out-of-scope responses. The Q&A product is suitable for public FAQs, customer knowledge bases, partner portals, and internal policy reference tools.

Purpose-built workflow apps across every business function: Nexus Apps are deployed for specific functions — onboarding guides, training assistants, SOP navigators, support desks, HR helpdesks, and ERP assistants. Each app is configured for its specific role, workflow, and knowledge set.

Nexus Support with AI triage, routing, and escalation: Incoming support queries are auto-resolved when approved knowledge is sufficient. When not, they are intelligently routed and escalated to the right human agent with full AI context attached. Support teams spend less time on repetitive queries and more time on genuinely complex cases.

Role-based identity and access control across all products: Every product on the platform — Chat Bot, Q&A, Apps — enforces identity-based access. The right information reaches the right person. Sensitive or internal knowledge is never accessible to public visitors or unverified users.

Multi-tenant deployment on a single managed infrastructure: Organisations deploying Nexus for multiple business units, brands, or clients benefit from fully isolated tenant workspaces on shared managed infrastructure. Each tenant has its own knowledge, agents, users, and settings. Platform administration is centralised.

The DIGITZ AI Nexus platform is delivered through Techxcel Technologies. Deployment begins with a structured onboarding process covering knowledge upload, bot configuration, identity setup, and testing. Businesses can request a demo to walk through the platform and explore how it applies to their specific operational context.
""",
    },

    # 15 ────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Frequently Asked Questions",
        "entity_type": "FAQ",
        "entity": "DIGITZ AI Nexus",
        "topic": "Common Visitor Questions and Answers",
        "priority": 9,
        "manual_content": """
Frequently asked questions from public visitors about DIGITZ AI Nexus:

Question: What is DIGITZ AI Nexus?
Answer: DIGITZ AI Nexus is a governed AI knowledge and chat platform built by Techxcel Technologies. It helps organisations deploy AI chat bots, Q&A experiences, and workflow apps that answer from approved business knowledge — with access controls, identity management, and human escalation built in.

Question: What problem does DIGITZ AI Nexus solve?
Answer: Nexus solves the problem of uncontrolled AI adoption. Many organisations want to use AI for customer communication and internal support, but they cannot afford to let AI answer freely from unverified sources. Nexus ensures every AI response comes from knowledge the business has approved, making AI deployment safe, auditable, and commercially credible.

Question: What AI products does DIGITZ AI Nexus offer?
Answer: The platform offers three AI products: Nexus AI Chat Bot for governed conversational AI, Nexus AI Q&A for instant structured answers from approved knowledge, and Nexus AI Apps for purpose-built workflow applications. Additionally, Nexus Co-Founder (AI for business leaders) and Nexus Co-Worker (AI for employees) are in production and will be released soon.

Question: What is Nexus AI Chat Bot?
Answer: Nexus AI Chat Bot is a designated AI agent deployed on websites, portals, or internal tools. Each bot is configured with a persona, tone, knowledge scope, access policy, escalation rules, and brand voice. Multiple bots can run simultaneously per tenant, each serving a different audience with its own knowledge and access rules.

Question: What is Nexus AI Q&A?
Answer: Nexus AI Q&A is a structured self-service knowledge product. Users ask a question and receive a direct, sourced answer from the approved knowledge base. Q&A is topic-bounded, with no hallucinations and no out-of-scope responses. It runs on the same governed knowledge pipeline as Chat Bot.

Question: How does Nexus keep AI responses accurate and controlled?
Answer: Nexus enforces a governed knowledge pipeline. All knowledge is loaded, classified, reviewed, and approved before the AI can use it. The platform retrieves only approved content, and the retrieval is filtered by the user's identity category and access policy before any response is generated. The AI cannot answer from unapproved sources.

Question: Can different users get different answers based on who they are?
Answer: Yes. DIGITZ AI Nexus uses an identity and access category system. Public visitors, verified customers, business partners, internal employees, and training participants each receive responses scoped to their identity category. Sensitive or internal knowledge is only accessible to users who have been verified and are permitted to access it.

Question: What happens when the AI cannot answer a question?
Answer: If the AI cannot find an answer within approved knowledge, it provides a clear fallback response. If the question falls into a configured escalation trigger — such as a complex query, a sensitive topic, or a request requiring approval — the conversation is handed to a human agent with the full conversation thread and an AI-generated summary already loaded.

Question: What is human escalation and how does it work?
Answer: Human escalation is the designed handoff from AI to a human agent. Eight trigger types are supported: Complex Query, Approval Required, Policy Exception, Identity Verification, Sensitive Topic, Tool Limitation, Customer Frustration, and Out of Scope. When triggered, the human agent receives the full AI conversation and a context summary. The customer does not need to repeat themselves.

Question: How is Nexus different from general-purpose AI tools like ChatGPT?
Answer: General-purpose AI tools answer from broad training data without business-specific controls. DIGITZ AI Nexus answers only from knowledge the business has approved and published. It enforces identity-based access, applies tenant isolation, supports human escalation, and maintains a full audit trail. It is built for safe enterprise deployment, not general public use.

Question: What are the three platform workspaces?
Answer: Nexus Studio is the authoring workspace where AI experiences are built and configured. Nexus Administration is the governance workspace where tenants, users, knowledge policies, and compliance are managed. Nexus Live is the operations workspace where live conversations, escalations, support tickets, and platform analytics are monitored and managed in real time.

Question: Is DIGITZ AI Nexus a multi-tenant platform?
Answer: Yes. Each tenant on the Nexus platform is a fully isolated business workspace with its own knowledge base, bots, users, agents, channels, and settings. There is no cross-tenant data exposure. Organisations deploying Nexus for multiple business units, brands, or clients benefit from tenant isolation on shared managed infrastructure.

Question: Does Nexus require engineering resources to configure?
Answer: No. Nexus is a 100% no-code configuration platform. Business teams can define chat bots, Q&A experiences, knowledge sources, identity rules, access policies, and escalation workflows through the Nexus Studio workspace without writing any code.

Question: What is Nexus Co-Founder?
Answer: Nexus Co-Founder is an upcoming AI experience for founders, owners, and business leaders. It will act as an AI business partner for strategy, policy alignment, goal tracking, and decision intelligence. It is currently in production and will be publicly released soon.

Question: What is Nexus Co-Worker?
Answer: Nexus Co-Worker is an upcoming AI experience for employees and operational teams. It will serve as an AI-powered work companion for daily business tasks — answering process questions, guiding workflows, retrieving approved knowledge, drafting replies and summaries, and supporting cross-functional teams. It is currently in production and will be publicly released soon.

Question: How can I request a demo of DIGITZ AI Nexus?
Answer: Visitors can request a demo through the DIGITZ AI Nexus website using the Request Demo or Talk to Us contact options. The Nexus team is available to walk through the platform, explain how it applies to a specific business scenario, and discuss deployment requirements.
""",
    },

    # 16 ────────────────────────────────────────────────────────────────────────
    {
        "title": "DIGITZ AI Nexus — Contact, Demo, and Getting Started",
        "entity_type": "Support",
        "entity": "DIGITZ AI Nexus",
        "topic": "Contact Information, Demo Request, and Onboarding Path",
        "priority": 8,
        "manual_content": """
Organisations and visitors who want to explore DIGITZ AI Nexus, request a demonstration, or discuss deployment options can contact the Nexus team through the official website.

The two primary contact actions available on the DIGITZ AI Nexus website are Request Demo and Talk to Us. Both options connect visitors with the Nexus team at Techxcel Technologies.

Requesting a demo is the recommended first step for organisations evaluating the platform. The demo provides a hands-on walkthrough of the Nexus platform covering the three AI products (Chat Bot, Q&A, and Apps), the three platform workspaces (Studio, Administration, and Live), how the identity and access system works, how knowledge is loaded and governed, and how human escalation operates. The demo is tailored to the visitor's specific industry and deployment scenario.

Visitors can use Talk to Us for more open-ended conversations — including questions about commercial suitability, integration with existing systems, pricing context, multi-tenant deployment, compliance requirements, or upcoming products such as Nexus Co-Founder and Nexus Co-Worker.

DIGITZ AI Nexus is built and delivered by Techxcel Technologies. The company can be reached through the website contact path for all commercial, product, implementation, and partnership enquiries.

For visitors who want to understand whether DIGITZ AI Nexus fits their business before contacting the team, the public website provides detailed information about all products, platform workspaces, identity and access capabilities, escalation, knowledge governance, and commercial use cases. The website chat assistant can also answer questions about the platform using approved public knowledge.

Getting started with DIGITZ AI Nexus typically follows a structured path: initial discovery and demo, followed by a scoping discussion to identify deployment requirements, followed by onboarding which covers knowledge preparation, bot configuration, identity setup, access policy design, and testing. The platform's no-code configuration means business teams can take ownership of the platform once initial setup is complete.

If a visitor's question cannot be answered from the available public knowledge on the website or through the chat assistant, the assistant will acknowledge this and guide the visitor to contact the Nexus team directly for personalised assistance.
""",
    },

]


# ── Foundation helpers ─────────────────────────────────────────────────────────

def _ensure_tenant():
    existing = frappe.db.get_value("Nexus Tenant", {"tenant_code": TENANT_CODE}, "name")
    if existing:
        doc = frappe.get_doc("Nexus Tenant", existing)
    else:
        doc = frappe.new_doc("Nexus Tenant")
        doc.tenant_code = TENANT_CODE

    doc.tenant_name = TENANT_NAME
    doc.disabled    = 0
    doc.description = "Tenant for the DIGITZ AI Nexus public website chat and Q&A."
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_business_unit(tenant):
    if frappe.db.exists("Nexus Business Unit", BUSINESS_UNIT):
        return BUSINESS_UNIT

    doc = frappe.new_doc("Nexus Business Unit")
    doc.business_unit_name = BUSINESS_UNIT
    if doc.meta.has_field("tenant"):
        doc.tenant = tenant
    if doc.meta.has_field("enabled"):
        doc.enabled = 1
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_channel(tenant, code, name, channel_type):
    existing = frappe.db.get_value(
        "Nexus Live Channel", {"channel_code": code, "tenant": tenant}, "name"
    )
    if existing:
        doc = frappe.get_doc("Nexus Live Channel", existing)
    else:
        doc = frappe.new_doc("Nexus Live Channel")
        doc.channel_code = code
        doc.tenant       = tenant

    doc.channel_name           = name
    doc.channel_type           = channel_type
    doc.enabled                = 1
    doc.public_access          = 1
    doc.requires_visitor_email = 0
    doc.agent_based            = 0
    doc.description            = f"DIGITZ AI Nexus website {channel_type} channel."
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_chat_category(tenant, channel):
    existing = frappe.db.get_value(
        "Nexus Chat Category", {"category_code": CATEGORY_CODE, "tenant": tenant}, "name"
    )
    if existing:
        doc = frappe.get_doc("Nexus Chat Category", existing)
    else:
        doc = frappe.new_doc("Nexus Chat Category")
        doc.category_code = CATEGORY_CODE
        if doc.meta.has_field("tenant"):
            doc.tenant = tenant

    doc.category_label             = CATEGORY_LABEL
    doc.channel                    = channel
    doc.enabled                    = 1
    doc.requires_authentication    = 0
    doc.identity_verification_mode = "None"
    doc.allow_public_fallback      = 0
    doc.display_order              = 10
    doc.description = (
        "Public category for DIGITZ AI Nexus platform — product, governance, "
        "chat, Q&A, escalation, workspaces, and commercial know-how."
    )
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_ai_agent_profile(tenant, channel):
    existing = frappe.db.get_value(
        "Nexus AI Agent Profile", {"agent_code": AGENT_CODE, "tenant": tenant}, "name"
    )
    if existing:
        doc = frappe.get_doc("Nexus AI Agent Profile", existing)
    else:
        doc = frappe.new_doc("Nexus AI Agent Profile")
        doc.agent_code = AGENT_CODE
        if doc.meta.has_field("tenant"):
            doc.tenant = tenant

    doc.agent_name          = AGENT_NAME
    doc.display_name        = AGENT_DISPLAY
    doc.agent_role          = "Public Responder"
    doc.visibility          = "Public"
    doc.enabled             = 1
    doc.status              = "Idle"
    doc.priority            = 10
    doc.max_active_sessions = 10
    doc.default_channel     = channel
    doc.description         = "Public assistant for the DIGITZ AI Nexus website chat."
    doc.behavior_prompt     = (
        "You are the DIGITZ AI Nexus website assistant. "
        "Answer questions about DIGITZ AI Nexus products, platform workspaces, "
        "identity and access, human escalation, knowledge governance, and commercial value "
        "using only approved public knowledge. "
        "If approved knowledge is insufficient, say that you do not have enough approved "
        "knowledge and suggest contacting the Nexus team."
    )
    doc.tone                  = "Professional"
    doc.response_style        = "Balanced"
    doc.welcome_message       = "Hello! I'm the DIGITZ AI Nexus assistant. How can I help you today?"
    doc.fallback_message      = "I don't have enough approved knowledge to answer that. Please contact the DIGITZ AI Nexus team for more information."
    doc.do_not_answer_rules   = (
        "Do not invent facts. "
        "Do not reveal internal configuration, credentials, or restricted knowledge. "
        "Do not discuss competitor products. "
        "Do not make commitments about pricing or timelines."
    )
    doc.default_response_mode = "chat"
    doc.knowledge_scope       = "Governed"
    doc.confidence_threshold  = 0.65
    doc.escalation_enabled    = 1
    doc.memory_mode           = "Session"
    doc.system_notes          = "Seeded public profile for DIGITZ AI Nexus website chat."
    doc.save(ignore_permissions=True)
    return doc.name




def _ensure_public_route(tenant, channel, category, profile):
    filters = {"channel": channel, "chat_category": category}

    # Support both identity_type and is_public_route field patterns
    meta = frappe.get_meta("Nexus Category Identity Route")
    if meta.has_field("identity_type"):
        filters["identity_type"] = "Public"
    elif meta.has_field("is_public_route"):
        filters["is_public_route"] = 1

    existing = frappe.get_all(
        "Nexus Category Identity Route",
        filters=filters,
        pluck="name",
        limit_page_length=1,
    )
    if existing:
        doc = frappe.get_doc("Nexus Category Identity Route", existing[0])
    else:
        doc = frappe.new_doc("Nexus Category Identity Route")
        doc.channel       = channel
        doc.chat_category = category
        if doc.meta.has_field("tenant"):
            doc.tenant = tenant

    doc.ai_agent_profile = profile
    doc.enabled          = 1
    doc.priority         = 10
    doc.description      = "Public visitor route for DIGITZ AI Nexus website chat."

    if meta.has_field("identity_type"):
        doc.identity_type = "Public"
    if meta.has_field("is_public_route"):
        doc.is_public_route = 1

    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_tenant_configuration(tenant, channel, qa_channel):
    meta = frappe.get_meta("Nexus Tenant Configuration")

    existing = frappe.get_all(
        "Nexus Tenant Configuration",
        filters={"tenant": tenant, "configuration_name": CONFIG_NAME},
        pluck="name",
        limit_page_length=1,
    )
    if existing:
        doc = frappe.get_doc("Nexus Tenant Configuration", existing[0])
    else:
        doc = frappe.new_doc("Nexus Tenant Configuration")
        doc.tenant = tenant
        doc.configuration_name = CONFIG_NAME

    doc.configuration_type                 = "Production"
    doc.enabled                            = 1
    doc.is_default                         = 1
    doc.activation_status                  = "Configured"
    doc.default_business_unit              = BUSINESS_UNIT
    doc.require_approved_knowledge         = 1
    doc.strict_tenant_mode                 = 1
    doc.default_top_k                      = 5
    doc.qa_enabled                         = 1
    doc.default_qa_channel                 = qa_channel
    doc.live_chat_enabled                  = 1
    doc.default_chat_channel               = channel
    doc.website_widget_enabled             = 0
    doc.widget_title                       = "DIGITZ AI Nexus Assistant"
    doc.widget_welcome_message             = "Hello! How can I help you today?"
    doc.testing_required_before_activation = 1
    doc.certification_status               = "Not Certified"
    doc.notes = "Tenant configuration for the DIGITZ AI Nexus public website chat."
    doc.save(ignore_permissions=True)
    return doc.name


def _upsert_knowledge_source(source, tenant, category_name=None, public_policy_name=None):
    title = source["title"]

    if frappe.db.exists("Nexus Knowledge Source", title):
        doc = frappe.get_doc("Nexus Knowledge Source", title)
    else:
        doc = frappe.new_doc("Nexus Knowledge Source")
        doc.title = title

    doc.source_type      = "Manual"
    doc.manual_content   = source["manual_content"].strip()
    doc.tenant           = tenant
    doc.business_unit    = BUSINESS_UNIT
    doc.project          = ""
    doc.context          = PUBLIC_CONTEXT
    doc.sub_context      = "Public Website"
    doc.entity_type      = source["entity_type"]
    doc.entity           = source["entity"]
    doc.topic            = source["topic"]
    doc.access_policy    = public_policy_name or "Public"
    doc.status           = "Draft"
    doc.priority         = source.get("priority", 7)
    doc.processing_status  = "Pending"
    doc.embedding_status   = "Pending"
    doc.diagnostics_status = "Pending"
    doc.retrieval_ready    = 0

    if doc.meta.has_field("chat_category"):
        doc.chat_category = category_name or CATEGORY_CODE

    doc.save(ignore_permissions=True)
    return doc


# ── Main entry point ───────────────────────────────────────────────────────────

def seed_nexus_website_knowledge(process_sources=True):
    """
    Idempotent seed for the DIGITZ AI Nexus public website chat.

    Creates the DIGITZ-AI-NEXUS tenant, all required foundation records,
    and 16 knowledge sources derived from the public website.

    This function is NOT called during installation.
    Run it manually from bench console when deploying the Nexus website chat:

        from digitz_ai_nexus.devtools.seed_digitz_nexus_homepage_knowledge import seed_nexus_website_knowledge
        seed_nexus_website_knowledge()

    Pass process_sources=False to skip embedding generation (useful for staging):

        seed_nexus_website_knowledge(process_sources=False)
    """

    result = {
        "foundation": {},
        "sources":    [],
        "processing": [],
    }

    # ── 1. Tenant ──────────────────────────────────────────────────────────────
    tenant = _ensure_tenant()
    result["foundation"]["tenant"] = tenant

    # ── 2. Access governance scoped to this tenant ─────────────────────────────
    result["foundation"]["access_governance"] = seed_default_access_governance(tenant=tenant)

    # ── 3. Business Unit ───────────────────────────────────────────────────────
    result["foundation"]["business_unit"] = _ensure_business_unit(tenant)

    # ── 4. Channels ────────────────────────────────────────────────────────────
    channel    = _ensure_channel(tenant, CHANNEL_CODE,    "Website Chat",  "Website Chat")
    qa_channel = _ensure_channel(tenant, QA_CHANNEL_CODE, "Website Q&A",   "Website Q&A")
    result["foundation"]["chat_channel"] = channel
    result["foundation"]["qa_channel"]   = qa_channel

    # ── 5. Chat Category ───────────────────────────────────────────────────────
    category = _ensure_chat_category(tenant, channel)
    result["foundation"]["chat_category"] = category

    # ── 6. AI Agent Profile ────────────────────────────────────────────────────
    profile = _ensure_ai_agent_profile(tenant, channel)
    result["foundation"]["ai_agent_profile"] = profile

    # ── 7. Wire profile → Public Access category ───────────────────────────────
    # ── 8. Public visitor route ────────────────────────────────────────────────
    result["foundation"]["public_route"] = _ensure_public_route(tenant, channel, category, profile)

    # ── 9. Tenant Configuration ────────────────────────────────────────────────
    result["foundation"]["tenant_configuration"] = _ensure_tenant_configuration(
        tenant, channel, qa_channel
    )

    frappe.db.commit()

    # ── Resolve actual doc names for link fields (autoname includes tenant suffix) ──
    public_policy_name = frappe.db.get_value(
        "Nexus Access Policy",
        {"policy_name": "Public", "tenant": tenant},
        "name",
    ) or frappe.db.get_value(
        "Nexus Access Policy",
        {"policy_name": "Public"},
        "name",
    )

    # ── 10. Knowledge sources ──────────────────────────────────────────────────
    for source in HOMEPAGE_SOURCES:
        doc = _upsert_knowledge_source(
            source, tenant,
            category_name=category,
            public_policy_name=public_policy_name,
        )
        source_entry = {
            "name":          doc.name,
            "title":         doc.title,
            "entity_type":   doc.entity_type,
            "entity":        doc.entity,
            "topic":         doc.topic,
            "access_policy": doc.access_policy,
            "status":        doc.status,
        }

        if process_sources:
            try:
                processing_result = process_knowledge_source(doc.name)
                source_entry["processing"] = processing_result
            except Exception as e:
                source_entry["processing_error"] = str(e)

        result["sources"].append(source_entry)

    frappe.db.commit()

    frappe.logger().info(
        f"DIGITZ AI Nexus website knowledge seed completed. "
        f"Tenant: {tenant}. Sources: {len(result['sources'])}."
    )

    return result
