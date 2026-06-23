# NEXUS AI — Public Chat Knowledge Source

This document is prepared as a public knowledge source for the Website Public Chat category:

`Ask Anything About Nexus AI`

It is written for website visitors, prospects, customers, partners, and business decision makers. It explains Nexus AI at a product and business level. It intentionally avoids internal configuration records, deployment credentials, private tenant details, debugging procedures, and restricted administrative runbooks.

## Recommended Manual Setup

| Field | Recommended Value |
| --- | --- |
| Tenant | NEXUS-AI |
| Chat Category | Ask Anything About Nexus AI |
| Access Policy | Public |
| Source Type | Manual |
| Status | Approved / Published after review |
| Audience | Website visitors and public enquiries |
| Purpose | Public product explanation, platform positioning, component overview, capabilities, governance, access model, and visitor chat answers |

---

# What Is Nexus AI?

Nexus AI is a governed AI platform that turns approved business knowledge into safe, identity-aware AI experiences — across chat, Q&A, workflow apps, autonomous agents, and role-based AI operators.

The core idea is that a business should be able to use AI confidently across its website, customer support, internal teams, and operational workflows — while keeping full control over what the AI knows, who is allowed to access that knowledge, and when a human must take over.

Nexus AI is not a chatbot. A chatbot is one thing the platform can deliver. Nexus AI is better understood as a governed intelligence operating layer for business knowledge. It helps organizations prepare knowledge, classify it, approve it, make it AI-ready, enforce access rules, route conversations to the right AI behavior, and deliver answers through the right channel — with a complete audit trail.

The platform is structured into three major components:

- **Nexus Orbit** — the governed intelligence layer at the core of every Nexus AI deployment.
- **Nexus Agentic** — the autonomous workflow runtime built on top of Nexus Orbit.
- **Nexy** — the role-based AI operator and agentic candidate that runs on both.

Understanding Nexus AI means understanding these three components and how they work together.

---

# The Three Pillars Of Nexus AI

## Nexus Orbit — The Governed Intelligence Layer

Nexus Orbit is the foundation. Every Nexus AI deployment runs on Orbit. It provides the knowledge management, governance, identity model, access control, channel routing, live operations, and configuration infrastructure that everything else depends on.

Orbit is where a business builds its AI experiences, governs its knowledge, and operates its live conversations.

## Nexus Agentic — The Autonomous Workflow Runtime

Nexus Agentic is the autonomous agent layer. It runs on top of Nexus Orbit and uses Orbit's knowledge, governance, identity, and messaging infrastructure to power AI agents that can reason across multiple steps, select tools, draft outputs, and pause for human approval before any external action is taken.

Nexus Agentic is for goal-oriented AI work — not just answering questions, but helping complete business tasks within controlled boundaries.

## Nexy — The Role-Based AI Operator

Nexy is the role-based AI operator and the primary named agentic candidate in Nexus AI. Nexy begins as a Visitor Companion — using Nexus Orbit's governed knowledge to hold intelligent, guided conversations with website visitors. As a business grows, Nexy expands into a Business Growth Orchestrator, connecting CRM signals, customer personas, and engagement behavior into coordinated outreach and follow-up actions through Nexus Agentic.

Nexy's role is configuration, not code. The same underlying architecture supports Sales, Customer Success, HR Onboarding, Partner Management, Vendor Qualification, and any other role a business needs to configure.

---

# Nexus Orbit — The Platform Your Business Controls

## What Nexus Orbit Is

Nexus Orbit is the governed intelligence layer at the core of every Nexus AI deployment. It is described on the platform website as: Knowledge. Governance. Interaction.

Orbit is structured around three purpose-built workspaces:

- **Nexus Studio** — Build and Configure.
- **Nexus Live** — Operate and Monitor.
- **Nexus Administration** — Govern and Comply.

These three workspaces cover the complete lifecycle of a governed AI deployment — from the first knowledge upload, to live operations, to platform-wide compliance.

## Nexus Studio — Build and Configure

Nexus Studio is the authoring workspace. It is where business teams design chat bots, build Q&A experiences, configure workflow apps, manage knowledge, and publish to any channel — without writing code.

Key capabilities of Nexus Studio:

**Chat Bot Builder:** Define the bot's purpose, persona, greeting behavior, response style, knowledge scope, confidence threshold, memory mode, audience assignment, and channel binding. Multiple bots can be deployed independently per tenant, each serving a different audience or business function.

**Knowledge Source Management:** Business knowledge is loaded into Studio through document upload (PDF, DOCX, TXT, HTML, and more), URL-based ingestion, or manual content entry for structured Q&A and SOPs. Every piece of content goes through a structured import, review, and approval lifecycle: Draft → Processing → Testing → Validated → Published. Backward testing is included — the platform generates synthetic questions from content and verifies the AI produces accurate answers before any real user can query it.

**Identity Rules and User Category Configuration:** Studio is where identity types are defined, verification modes are set per chat category, access categories are assigned per identity type, and the Identity Registry SafeGuard ceiling is configured. These rules are applied at the conversation level — the AI checks who is asking before deciding what it can share.

**Q&A Flow Designer:** Build structured Q&A experiences with their own topic scope, answer boundaries, confidence thresholds, and out-of-scope handling — distinct from open chat.

**Workflow App Configuration:** Configure purpose-built apps for specific business functions — onboarding guides, support desks, HR helpdesks, ERP assistants, training workflows — each with its own knowledge binding, role-based access, and embedding code.

**Escalation Trigger Design:** Define exactly which conditions cause the AI to hand over to a human agent — low confidence, no approved knowledge, user-requested human, sales lead signal, sensitive topic, repeated fallback. Escalation is opt-in per chat category and carries a full context package to the human agent.

**Test, Preview, and Deployment Controls:** Before anything goes live, Studio provides an interactive preview environment where teams can simulate conversations, test identity scenarios, verify escalation behavior, and check response accuracy. Deployment follows a staged pipeline: Draft → Review → Approved → Published.

## Nexus Live — Operate and Monitor

Nexus Live is the real-time operations centre. It gives operations teams visibility and control over every live conversation, escalation, support case, and agent interaction across all tenants.

Key capabilities of Nexus Live:

**Live Conversation Monitor:** Watch every active chat session across all tenants in real time. Status indicators show whether a conversation is Active, Waiting, Escalated, Resolved, or Abandoned. Each session shows the AI handling it, the user identity category, and time elapsed. Any session can be opened for a full thread view.

**Escalation Queue and Agent Console:** When the AI reaches a defined escalation trigger, the conversation moves to the right human agent through a structured queue. Agents claim conversations with the full AI thread already loaded, the AI-generated summary, and the recommended next action. Agents can reply, add internal notes, and update ticket status without leaving the console.

**Support Ticket Management:** Every escalated or unresolved interaction can be converted into a tracked support ticket. Tickets carry the full conversation thread, user context, escalation reason, and priority classification. The ticket lifecycle moves through: Open → In Progress → Pending → Resolved → Closed. SLA timers run per ticket based on priority and tenant configuration.

**Performance Dashboards and Analytics:** Nexus Live tracks total conversations, auto-resolution rate, escalation rate by trigger type, average response time, average resolution time, SLA compliance rate, knowledge coverage gaps, agent performance, and volume trends by period.

**Multi-Tenant Visibility and Isolation:** Administrators can view activity across all tenants in aggregate or switch to a per-tenant view. Tenant data, conversations, and tickets remain isolated at all times by design.

**Alerts, Anomaly Detection, and SLA Warnings:** Nexus Live monitors for SLA breach risk, escalation surges, knowledge failure rates above threshold, and session abandonment spikes. Alerts can route to in-console notifications, email, or webhook.

## Nexus Administration — Govern and Comply

Nexus Administration is the governance backbone of the entire platform. It is where multi-tenant isolation is enforced, user roles and permissions are defined, knowledge policies are managed, and every AI action is recorded for audit.

Key capabilities of Nexus Administration:

**Multi-Tenant Workspace Management:** Each tenant is a fully isolated business workspace with its own knowledge base, bots, users, agents, channels, and settings. Administrators can provision new tenants, manage tenant status (Active, Suspended, Trial, Archived), set resource quotas, configure feature flags per tenant, and view tenant health in one dashboard.

**User Management, Roles, and Permissions:** Platform roles include Super Admin, Tenant Admin, Studio Author, Knowledge Manager, Live Agent, Operations Viewer, and Read-Only Auditor. Permissions can be scoped per workspace, per tenant, per bot, or per knowledge set. Session management, IP restrictions, two-factor authentication enforcement, and role change audit trails are included.

**Knowledge Governance and Content Policy:** Administration sets the platform-level content policy — what content categories are permitted, who can approve which content types, how long content remains valid, and what happens when it expires or is disputed. The approval authority matrix defines which roles can publish which content.

**Audit Trail and Compliance Reporting:** Every action by the AI or a human is recorded in a tamper-evident audit log — every query, every retrieval source, every response, every agent action, every configuration change. The log is searchable, filterable, and exportable to CSV, JSON, or PDF. Compliance report templates are included for GDPR, data access, content governance, and user activity reviews.

**Platform Security and Integration Settings:** Administration manages API key generation, webhook configuration, SSO/SAML integration, data residency settings, CORS policy for widget embedding, rate limiting, and platform health monitoring.

**Subscription, Licensing, and Usage Management:** For businesses operating Nexus as a managed or multi-client platform, Administration tracks usage against entitlement by tenant, manages billing tiers, configures quota alerts, and provides usage reports for cost allocation or client invoicing.

---

# Products Delivered On Nexus Orbit

Nexus Orbit delivers three distinct AI product types. Each is configured in Studio, operated through Live, and governed by Administration.

## Nexus Chat Bot

Nexus Chat Bot is a multi-tenant, identity-aware conversational AI. It can serve public website visitors, verified customers, internal employees, and business partners — each governed by its own identity type, knowledge scope, and access policy. Multiple bots can be deployed independently per tenant.

## Nexus Q&A

Nexus Q&A delivers structured answers sourced directly from approved knowledge. It is designed for scenarios where the user needs precise, auditable answers from a bounded knowledge set — with no hallucinations, no out-of-scope replies, and every answer traceable to a source document.

## Nexus Apps

Nexus Apps are purpose-built AI workflow experiences for specific business functions — onboarding guides, support desks, HR helpdesks, ERP assistants, training workflows, and more. Each app is configured for a specific role, process, knowledge set, and user category. Apps are embeddable in any portal, intranet, or website.

---

# The Knowledge System In Nexus AI

## How Knowledge Is Structured

Knowledge in Nexus AI is organized as a three-level hierarchy that moves from the whole document down to the smallest retrievable piece:

**Knowledge Source** — the root record for a piece of business content. A source can be a PDF, DOCX, TXT, or HTML document, a web page ingested by URL, or content entered manually as structured text, Q&A pairs, or SOPs. Each source belongs to a specific tenant, a business unit, and an access policy. The access policy controls which audiences are allowed to retrieve from this source. The source also carries a readiness status that gates whether the AI is permitted to use it.

**Knowledge Unit** — a logical section within a source. A unit represents a coherent topic or concept block — a chapter, a product description, a support topic, a policy section. Breaking content into units keeps retrieval focused: rather than retrieving a whole document, the engine can pinpoint the relevant unit.

**Knowledge Chunk** — the smallest retrievable fragment, produced by splitting units into passages of a size suitable for the LLM context window. Each chunk carries an embedding vector — a numerical representation of its semantic meaning — that enables similarity search. Chunks are what the retrieval engine actually scores and ranks.

Supporting records:

**Knowledge Index Entry** — keyword-based index records built from each chunk. These power the keyword scoring half of hybrid retrieval (BM25), ensuring exact term matches are captured even when semantic similarity alone would miss them.

**Knowledge Context Summary** — a source-level summary generated during processing and stored separately. When a query spans multiple chunks from the same source, the context summary can be injected into the prompt to give the LLM a higher-level view of the document, improving answer coherence.

## How Knowledge Gets Into The Platform — Ingestion

Nexus AI supports multiple ways to bring knowledge in:

**Document upload** — PDF, DOCX, TXT, XLSX, and HTML files. The ingestion engine parses the document structure, extracts text, identifies logical sections, and creates units and chunks automatically.

**URL ingestion** — web pages from approved domains can be scraped and indexed. The platform extracts the meaningful text, strips navigation and boilerplate, and processes the content as a knowledge source.

**Manual entry** — teams can type or paste content directly. This is useful for structured Q&A pairs, SOPs written specifically for the AI, short policy statements, or content that does not exist in a document file.

In all cases, once a source is submitted, the processing pipeline runs automatically — no manual chunking or embedding is needed. The platform handles parsing, splitting, embedding generation, and keyword indexing without human intervention.

## The Knowledge Lifecycle — From Upload To AI-Ready

Every knowledge source passes through a strictly ordered lifecycle. The AI is never allowed to use content that has not completed this sequence.

**Draft** — the source has been created but not yet submitted for processing. Teams can edit, annotate, and classify the source at this stage. Nothing is sent to the AI.

**Processing** — the platform ingests the source: parses the document into units, splits units into chunks, generates embedding vectors for each chunk, builds keyword index entries, and creates a context summary. This happens automatically after submission.

**Testing** — this is the quality gate. The platform automatically generates a set of test questions from the content of the source and runs them through the AI retrieval pipeline. For each synthetic question, a Knowledge Test Case is created and a Knowledge Test Run is executed — recording which chunk was retrieved, the confidence score, and whether the AI produced an accurate, useful answer. If a chunk consistently fails to retrieve correctly, or the AI's answer does not align with the source content, the test run records a failure.

**Validated** — the source has passed the automated tests and is staged for human review. A knowledge manager or approver reviews the source, the test results, and the coverage before approving it for publication.

**Published** — the source is approved and live. Only published chunks are eligible for retrieval in chat responses, Q&A sessions, or agentic runs. Unpublished or expired content is automatically withheld regardless of query relevance.

If content fails testing or fails the review, it returns to Draft for revision. This prevents low-quality, incomplete, or inaccurate content from ever reaching a live user.

## Backward Testing And Automated Question Generation

Backward testing is one of the most commercially important capabilities in the knowledge pipeline. The concept is simple but powerful: rather than waiting for real users to discover gaps in the AI's knowledge, the platform proactively tests the content before anyone can query it.

When a knowledge source enters the Testing stage, the platform generates synthetic questions from the content automatically. These questions are designed to represent what a real user might ask if they wanted information from that specific piece of content. The questions are not hand-written — they are generated by the LLM from the content itself, covering different angles, phrasings, and levels of specificity.

Each synthetic question becomes a **Knowledge Test Case**. The test case records the question, the chunk the question was generated from, the expected answer context, and a reference to the source.

For each test case, a **Knowledge Test Run** is executed: the question is run through the full retrieval pipeline as if a real user asked it. The run records:

- Which chunks were retrieved and their confidence scores.
- Whether the expected chunk ranked highly enough.
- Whether the AI's generated answer accurately reflects the source content.
- The overall pass or fail status of the test.

If a source consistently fails its test runs — because the content is ambiguous, the chunking produced poor fragments, or the phrasing makes retrieval difficult — the source returns to Draft. The knowledge team can revise the content, adjust the structure, or split the source differently before resubmitting.

**Correlated question sets:** The Knowledge Test Cases generated during backward testing serve a dual purpose. In addition to being run as retrieval tests, they form a set of correlated question phrasings — multiple angles and synonym variations of the same underlying question, all mapped to the same source. These correlated sets are retained and used by the retrieval engine to understand what a source is likely to answer well. When a visitor asks a question, the engine can match it against correlated question sets as a fast-path signal before running the full hybrid retrieval pipeline. Correlated sets are also re-evaluated whenever the source content is updated, keeping retrieval quality current without manual re-indexing.

**Auto-generated useful questions and the Question-First search path:** Separate from the correlated question sets, the processing step generates a compact set of "useful questions" for each knowledge source — the questions that source is most precisely equipped to answer. Each useful question is stored as a Knowledge Index Entry of type User Question, embedded, and indexed alongside the source content. These entries are what enable Nexus AI's Question-First search path, which reduces retrieval cost significantly.

When a visitor asks a question, the retrieval engine first searches only the User Question index — a much smaller, focused index — using the same embedding as the visitor's query. If any User Question entry matches above the confidence threshold, the engine already knows exactly which chunk to retrieve. It fetches only those specific chunks and skips the full corpus scan entirely. No scanning of thousands of chunk embeddings, no full hybrid ranking pass over the complete knowledge base. Only when no high-confidence User Question match is found does the engine fall back to the full hybrid retrieval pipeline across all chunks.

This means: a well-populated User Question index reduces embedding search cost, database fetch volume, and re-ranking workload for the majority of common queries. The more queries that match through the Question-First path, the lower the per-conversation compute cost.

**What this means for a business:** A business can upload a product guide, support document, or SOP and know that the AI has been automatically stress-tested against it before any customer or employee ever asks a question. The testing stage is not a manual QA process — it runs automatically as part of the lifecycle. If the AI cannot reliably answer questions from a piece of content, that content is blocked from going live until the team fixes it.

## FAQ Questions And Category-Level Answers

In addition to full knowledge sources, each Chat Category can carry a set of pre-built FAQ entries — structured question and answer pairs that are specific to that category. These are configured directly in Nexus Studio when setting up the category.

FAQ entries serve as instant, deterministic answers for the most common and predictable questions in that category. They do not go through embedding or retrieval — they are matched directly. A well-configured FAQ set reduces retrieval load for high-frequency questions and ensures the most important answers are always precise, consistent, and immediate.

## How Retrieval Works — RAG In Practice

When a visitor asks a question, the following happens before the AI generates a response:

**Query expansion** — the engine expands the visitor's query with related phrasings and synonyms to improve recall. A visitor asking a question one way may be asking the same thing as content phrased differently.

**Hybrid scoring** — the expanded query runs through two parallel scoring passes: semantic vector similarity (using the chunk embeddings) and BM25 keyword scoring (using the keyword index). These scores are combined into a hybrid rank.

**Re-ranking** — the top candidates from the hybrid pass are re-ranked using a cross-encoder model that scores each candidate against the full query for precise relevance. This improves precision for ambiguous or multi-part questions.

**Access filtering** — before any chunk is passed to the LLM, the engine checks that the chunk's source is covered by an access policy the current user is allowed. Chunks outside the allowed policies are removed from the candidate set regardless of their relevance score.

**Confidence threshold check** — if no remaining candidate exceeds the configured confidence threshold for the current AI agent profile, the engine does not fabricate an answer. It falls back to the configured fallback message.

**Context summary injection** — if the top-ranked chunks span a single source, the source-level context summary may be injected alongside the chunks to give the LLM broader document context.

**Answer generation** — the LLM receives the behavior prompt (role, tone, boundaries), the retrieved chunks, the context summary if applicable, the conversation history, and the visitor's question. It generates an answer grounded in the retrieved evidence.

## Knowledge Gap Detection And Continuous Improvement

When the AI cannot answer a question — either because no relevant approved knowledge was found or because the confidence threshold was not met — Nexus AI records a **Knowledge Gap**.

**Reactive gap detection:** Every fallback response triggers a gap record. The platform deduplicates gaps by semantic hash — multiple visitors asking semantically similar questions are grouped into the same gap record, with a frequency count and sample queries stored. This shows the knowledge team which topics come up repeatedly without an adequate answer.

**Proactive gap detection:** A scheduled job can analyse recent query logs to detect topics where the AI is consistently retrieving low-confidence results or where queries are clustering around topics not well covered by existing sources. This surfaces gaps before they accumulate into visible fallback patterns.

**LLM relevance assessment:** Each recorded gap goes through an automated LLM assessment to determine whether the gap represents a genuinely relevant business topic or a noise query. The assessment records whether the gap should be acted on, suggests a topic and context for the missing knowledge, and can recommend which existing knowledge source to update or what new source to create.

**Gap-to-source workflow:** From the Knowledge Gap review interface, an administrator can directly create a new Knowledge Source from the gap record. The suggested topic, context, and sample queries from the gap become the starting point for the new source. Once the source is authored, tested, and published, the gap is closed.

**Visitor follow-up:** When a visitor receives a fallback response, they can optionally provide their email. If the relevant knowledge gap is later resolved — a matching knowledge source is published — Nexus AI can automatically send a follow-up email to that visitor with an updated answer. The email follow-up is idempotent: it sends once per resolved gap per visitor email.

**What this means for a business:** The knowledge base does not need to be perfect at launch. Knowledge gaps discovered through real visitor questions — or detected proactively — create a direct, structured workflow to close them. The platform helps the business discover exactly what knowledge is missing, prioritize what to fix first, and then verify the fix works before publishing.

---

# Access Control And Information Security

## The Access Model

Nexus AI is built on the principle that not every user should see every piece of knowledge. The access model has four levels that work together:

**Access Policy:** The most granular unit. Each policy defines a sensitivity level, allowed roles, and allowed designations. Policies are assigned to knowledge sources.

**Access Category:** A named grouping of access policies. Categories make it easier to manage what a class of users can reach — for example, a "Public Website" category groups policies for all content that public visitors are allowed to access.

**Knowledge Profile:** A configuration that defines a context profile with a set of allowed access categories. Profiles are assigned to identity types and routes to determine the knowledge ceiling for a given conversation.

**Access Resolution:** At query time, the engine resolves the allowed access policies for the current conversation by intersecting the knowledge profile's categories with the Identity Registry SafeGuard ceiling. The narrower set always wins. Only knowledge chunks whose source is covered by an allowed policy are eligible for retrieval.

This means the AI cannot return content it is not explicitly permitted to retrieve for the current user and context — regardless of what the LLM might otherwise be capable of.

## Identity Types And Verification

Nexus AI recognizes different identity types for users who interact with the platform:

- **Public Visitor** — unauthenticated website visitor. Accesses only public knowledge. No login required.
- **Verified Customer** — a known customer whose identity has been confirmed through an email OTP or registered email check. May access customer-level knowledge if the channel and route allow it.
- **Internal Employee** — authenticated desk user. Accesses internal knowledge through authenticated internal channels.
- **Business Partner** — a verified partner identity. Access scope defined by the business.
- **Training Participant** — a participant in a structured training or onboarding flow.
- **Custom types** — organizations can define additional identity types with their own verification modes and access rules.

Identity types are intentionally global across the platform — not scoped per tenant — so the same named types can be referenced consistently across tenants.

## Verification Modes

Each chat category can require a different level of identity verification before the AI responds:

- **None** — no verification required. The visitor is treated as a public visitor and receives the default public knowledge scope.
- **Email OTP** — the visitor is asked to provide their email address, receives a one-time code, and must verify before accessing knowledge above the public scope.
- **Registered Email OTP** — the visitor's email is checked against the Identity Registry. If the email matches a registered identity, the verified identity type and its associated knowledge profile are applied to the conversation.

## The Identity Registry SafeGuard

The Identity Registry SafeGuard is a hard ceiling that caps what any holder of a given identity type can access, regardless of what the AI Agent Profile or route configuration might allow. The effective access scope for any conversation is always the intersection of the route's knowledge profile and the SafeGuard ceiling. If the intersection is empty, the system fails closed — no retrieval proceeds.

## Category Identity Routes

A Category Identity Route maps a specific combination of Chat Category and Identity Type to an AI Agent Profile, a Knowledge Profile, and an Identity Profile. Routes are what connect the visitor's conversation choice to the correct AI behavior, knowledge access, and escalation policy — without exposing any of that routing logic to the visitor.

Routes must be explicitly enabled and published before they take effect. An unpublished route means the conversation cannot proceed.

## Identity Profiles

An Identity Profile is a named identity context within a tenant that bridges an Identity Type to a specific Knowledge Profile. It is the tenant-scoped configuration record that determines exactly which knowledge scope a person with a given identity type receives in this deployment.

Identity Profiles matter because a single Identity Type can have multiple profiles within one tenant. For example, a business may configure:

- **Standard Customer** — a Verified Customer profile that grants access to general support knowledge and standard product documentation.
- **Premium Customer** — a second Verified Customer profile that additionally grants access to priority support guides, early-access feature documentation, and account management materials.

Both profiles map to the Verified Customer identity type, but they give different knowledge ceilings. The Category Identity Route selects the correct profile for the conversation based on the chat category and the verified identity.

Identity Profiles must be explicitly enabled and published to take effect. If no matching profile is active for the resolved identity type and category, the conversation fails closed — no retrieval proceeds.

---

# Serving Different Business Audiences — The Commercial Perspective

## Why Identity Types And Knowledge Profiles Matter For A Business

Most businesses have more than one audience. A website visitor exploring the product is a different person from a paying customer needing account support. A new employee asking about HR policy is different from a business partner needing co-sell material. A training participant has different needs from a senior manager reviewing SOPs.

The problem with most AI platforms is that they treat every user the same. Either the AI has access to everything and risks exposing the wrong content to the wrong person, or it is locked down for everyone and becomes too restricted to be genuinely useful.

Nexus AI solves this with identity types and knowledge profiles. The platform can serve all of a business's audiences through one governed system — with each audience seeing exactly the knowledge they are entitled to, nothing more and nothing less.

## The Business Audience Tiers

### Public Visitor — Prospects, Enquiries, Website Traffic

Public visitors are unauthenticated people arriving at the website. They may be prospects researching the product, partners exploring a collaboration, or anyone with a general enquiry. They have no established business relationship yet.

What they can access: only knowledge the business has explicitly tagged as public. Product information, feature overviews, use case guides, pricing direction, demo guidance, public FAQs, and marketing content.

What they cannot access: customer support documents, internal SOPs, pricing agreements, account information, partner-confidential material, or anything tagged for a more qualified audience.

Business value: A public visitor gets immediate, accurate, always-on answers about the product without any sales rep involvement. The business protects its sensitive content because the AI is physically incapable of returning it to this audience tier.

### Verified Customer — Active Customers Seeking Support Or Account Help

A verified customer is someone whose identity has been confirmed against the business's customer registry — typically through a registered email check. They have an active business relationship.

What they can access: everything the public visitor can access, plus customer-level knowledge. This may include support guides, product documentation, troubleshooting steps, onboarding materials, account setup instructions, product-specific SOPs, and other content the business has designated for verified customers only.

What they cannot access: internal employee content, partner-confidential pricing, admin procedures, or content above the customer knowledge ceiling.

Business value: Verified customers get richer, more precise answers that are relevant to their actual relationship with the business — without the business having to maintain a separate support portal or knowledge base system. Verification happens through a built-in email OTP or registered email check, not a manual login flow.

### Business Partner — Channel Partners, Resellers, Integration Partners

A business partner identity type is used for verified channel partners, resellers, referral partners, or integration partners. They have a different relationship than a customer — they may need co-sell material, partner programme documentation, pricing structures, commission guides, or joint go-to-market resources.

What they can access: the knowledge profile assigned to the partner identity type. This is configured by the business and may include materials completely invisible to customers or public visitors.

What they cannot access: internal employee content or any tier above their defined ceiling.

Business value: A partner portal can serve a large partner network with instant, accurate answers about the programme — reducing partner management overhead and removing the need for constant partner enablement calls.

### Internal Employee — Teams, Departments, Operations Staff

An internal employee is an authenticated desk user — someone logged into the business's internal system. They interact with Nexus AI through internal channels and desk-type workspaces, not the public website.

What they can access: the full scope of knowledge assigned to their knowledge profile. This may include internal SOPs, HR policies, finance procedures, IT guides, compliance documents, procurement workflows, ERP process guides, and any operational knowledge the business has organized for internal use.

What they cannot access: other tenants' knowledge, or tiers above their profile ceiling.

Business value: Employees get instant, accurate answers for internal questions without searching multiple systems, emailing colleagues, or waiting for a response from a specific team. The same governed knowledge base that powers customer chat can power internal help — with the access boundaries ensuring each audience only reaches what is relevant to them.

### Training Participant — Onboarding, Courses, Certification Learners

A training participant identity type is used for people going through a structured learning or onboarding journey. This may be a new employee, a newly onboarded customer, a partner going through a certification programme, or any user engaged in a defined learning flow.

What they can access: the knowledge profile assigned to training participants, which can be scoped to specific training materials, learning modules, process guides, and assessment-relevant content.

Business value: A training assistant powered by Nexus AI can answer trainee questions conversationally, guide them through steps, confirm understanding, and flag gaps — replacing static PDF manuals and reducing trainer workload for common onboarding questions.

## What A Knowledge Profile Means In Practice

A Knowledge Profile is not a technical permission record. In commercial terms, a Knowledge Profile is the answer to the question: what view of the business's knowledge should this type of person receive?

A business might define profiles like:

- **Public Product Profile** — everything the business has approved for public consumption: product pages, feature guides, use case descriptions, public FAQs, pricing direction, demo options.
- **Customer Support Profile** — includes the public product profile plus support documentation, troubleshooting guides, setup instructions, and product-specific help content.
- **Partner Enablement Profile** — includes public content plus co-sell materials, partner programme documentation, reseller pricing guidance, and joint go-to-market resources.
- **Employee Operational Profile** — includes internal SOPs, HR policies, finance workflows, IT procedures, compliance documents, and management guides that are never visible to external audiences.
- **Training Profile** — scoped to a specific learning curriculum, module content, and process documentation relevant to the current onboarding or training programme.

Each profile is configured in Nexus Orbit's access model. The AI's retrieval is bounded by whichever profile applies to the current visitor — the AI does not decide what to share; the profile decides what the AI is allowed to retrieve.

## How The Audience Tier Is Determined At Runtime

When a visitor starts a conversation, the platform determines their audience tier through the following chain:

1. The visitor selects a chat category on the website widget.
2. The category has a configured identity verification mode — None, Email OTP, or Registered Email OTP.
3. If verification is required, the visitor goes through the verification step. Their email is checked against the Identity Registry.
4. The resolved identity type — Public Visitor, Verified Customer, Partner, Employee, or custom — is matched to the Category Identity Route for that category.
5. The route maps the identity type to an AI Agent Profile and a Knowledge Profile.
6. The Identity Registry SafeGuard applies its ceiling as a hard cap.
7. The AI retrieves only from knowledge within the intersection of the Knowledge Profile and the SafeGuard ceiling.

The visitor experiences this as a natural conversation. The audience tier determination, knowledge boundary enforcement, and access resolution happen in the background before any retrieval begins.

## Commercial Scenarios

**Scenario: Software company with a public website and a customer support portal**

The same Nexus AI deployment handles both. Public visitors on the website ask about features, pricing, and use cases — they receive public product knowledge and are guided toward a demo or signup. Verified customers in the support portal enter their email, receive an OTP, and are recognized as customers — they now receive support documentation, troubleshooting guides, and account-level help that the public visitor cannot access.

**Scenario: SaaS business with a partner programme**

Public visitors get product information. Verified customers get support content. Verified partners get an additional layer — co-sell playbooks, reseller pricing, partner enablement guides, and programme documentation — all from the same platform, with partner content completely invisible to customers and the public.

**Scenario: Enterprise deploying AI for internal teams**

HR, finance, IT, and operations each have their own knowledge profile. A new employee going through onboarding receives the training profile — learning modules and process guides. An operations manager receives the operational employee profile — SOPs, compliance documents, and workflow guides. A finance team member receives the finance profile — expense procedures, budget processes, and approval workflows. One platform, multiple audience tiers, each governed independently.

**Scenario: Managed service provider running multiple clients**

Each client is a separate tenant. Within each tenant, the provider configures the client's own identity types, knowledge profiles, and knowledge sources. A visitor at Client A's website can never reach Client B's knowledge. Each client's public visitors, verified customers, and employees each receive the knowledge tier appropriate to their identity — all through the same platform instance.

---

# Multi-Tenancy In Nexus AI

A tenant is a fully isolated business workspace inside the Nexus AI platform. Every knowledge source, chat bot, channel, category, conversation, access policy, user, and operational record belongs to a specific tenant. Tenant data cannot leak to another tenant by design.

Multi-tenancy means one Nexus AI deployment can serve multiple independent business contexts. Examples:

- A service provider operating one platform for multiple client organizations, each with their own knowledge, bots, and access rules.
- A group company running separate tenants for different brands or subsidiaries.
- A large organization separating public website chat, internal employee knowledge, customer support, and training into different tenant spaces.
- A business maintaining separate production and staging environments in different tenants.

Each tenant controls its own:

- Knowledge sources, units, and chunks.
- Access policies, categories, and knowledge profiles.
- Chat bots, channels, and chat categories.
- Identity types, identity registry entries, and route configurations.
- Conversation history, query logs, and escalation records.
- LLM and embedding provider configuration.
- Website widget settings.
- Business unit groupings.
- Tenant configuration defaults.

Two entities are intentionally global and not scoped per tenant: **Identity Types** and the **Identity Registry**. These are shared across tenants so the same named identity classes can be referenced consistently, with each tenant controlling which registry entries and profiles apply within its own context.

---

# Channels And Chat Categories

## Channels

A channel is the logical entry point for a conversation — website chat widget, customer portal, internal intranet, mobile app, API, or embedded business application. Each channel has a type (Website Chat, Desk, API) and belongs to a tenant. Channels define the default AI agent, whether a visitor email is required, and other surface-level settings.

Channels are an infrastructure and governance layer. Website visitors do not need to select or understand channels. The website widget collects and displays the published chat categories from all enabled website-type channels for the active tenant, and the visitor simply selects a topic.

## Chat Categories

A chat category tells Nexus AI what kind of conversation the user wants to have. For a public website, categories are the visitor-facing choices — topics like "Ask Anything About Nexus AI", "Customer Support", "Partner Enquiry", or "Book a Demo."

Each category belongs to a channel internally. Selecting a category implies the channel, which tells the routing layer which identity routes, AI profiles, and knowledge profiles apply.

Categories can be enabled or disabled, and published or unpublished, independently. Only published categories are visible to visitors. Categories can carry pre-built FAQ answers for common questions that do not require retrieval.

Categories can also define their identity verification mode — so one category may serve public visitors with no verification while another requires email OTP before the AI responds.

## The Widget

The Nexus AI website chat widget is an embeddable JavaScript component. When a visitor opens the widget, it fetches the published categories from all enabled website-type channels for the active tenant and presents them as the visitor's topic choices. The visitor selects a category, and the conversation begins. The widget handles real-time message display, typing indicators, escalation messages, and human agent responses — all without requiring a page reload.

---

# AI Agent Behavior Configuration

## What Behavior Configuration Is

An AI Agent Profile is the complete behavioral contract for a specific AI experience. It answers every question about how the AI should conduct itself in a conversation: how it introduces itself, what tone it uses, what it is explicitly not allowed to discuss, how confident it needs to be before answering, what it says when it cannot answer, and when it should stop and hand the conversation to a person.

Behavior configuration is separate from knowledge access. A business can change the tone, welcome message, and response style of an AI without changing what knowledge it retrieves. Equally, a business can change the knowledge scope — allowing access to more content for verified customers — without altering the assistant's personality or guardrails.

This separation matters commercially: a customer support assistant and a public product assistant can be grounded in completely different knowledge profiles, behave differently, and escalate on different triggers — while both running on the same platform.

## Persona And Identity

**Agent name and display name** — what the AI calls itself in conversation. A business can name the assistant anything that suits its brand. The display name is what visitors see in the chat widget.

**Nickname pool** — a configured set of names the assistant can use when introducing itself informally. This allows variation without the assistant always giving the same fixed greeting phrasing.

**Agent role** — a short statement of the assistant's purpose. This is visible in the system prompt and shapes how the LLM frames its responses. A role like "Product Enquiry Assistant" produces different conversational posture than "Customer Support Specialist" or "HR Onboarding Guide."

## Behavior Prompt — The System Instruction Layer

The behavior prompt is the core instruction set that governs the AI's conduct throughout the entire conversation. It is never shown to the visitor — it operates as the AI's standing brief.

A behavior prompt can include:

- The assistant's stated purpose and scope: what it is there to help with.
- Topics the assistant should address confidently and prioritize.
- Explicit restrictions: topics the assistant must refuse or redirect, regardless of whether knowledge exists.
- Tone and communication style: formal, warm, concise, technical, consultative.
- Audience awareness: how to communicate with a public visitor versus a verified customer versus a partner.
- Escalation guidance: cues that suggest the visitor needs a human, even if the AI could technically answer.
- Grounding requirements: whether every claim must be explicitly supported by retrieved knowledge before the AI states it.
- Confidentiality instructions: topics the AI must not discuss, acknowledge, or speculate about.

The behavior prompt is set in Nexus Studio per profile. Different chat categories — and different audience tiers on the same channel — can use different profiles with different behavior prompts. The visitor always experiences the behavior defined for their specific context.

## Do-Not-Answer Rules And Guardrails

Do-not-answer rules are explicit restrictions configured per profile. They define what the AI must never discuss, commit to, or speculate about — regardless of whether knowledge exists in the approved base and regardless of how the question is phrased.

Examples of do-not-answer rules a business might configure:

- Never state or imply a price, discount, or commercial commitment without directing the visitor to the sales team.
- Never discuss a competitor's product, pricing, or weaknesses.
- Never speculate about product roadmap or unannounced features.
- Never make claims about SLAs or response time guarantees.
- Never discuss legal, regulatory, or compliance matters — direct to the legal team.
- Never provide account-specific information to an unverified visitor.
- Never engage with off-topic personal or political questions.

Do-not-answer rules operate at the behavior prompt level. They are enforced by the LLM's instruction-following behavior within the system prompt. They complement the access model — the access model prevents the AI from retrieving restricted content, while do-not-answer rules prevent the AI from making restricted statements even when it might otherwise construct one from general knowledge.

## Welcome Message And Fallback Message

**Welcome message** — the first thing a visitor sees when they start a conversation. The welcome message sets the tone, introduces the assistant, and signals what the visitor can ask about. It is configured per profile and can differ significantly between a public product assistant ("Hello, I'm here to help you understand what Nexus AI can do for your business") and a customer support assistant ("Hi, I'm your support assistant. Tell me what you're working through and I'll find the right guidance for you.").

**Fallback message** — what the AI says when it cannot find sufficient approved knowledge to answer the question. A well-configured fallback message does not make the visitor feel dismissed. It acknowledges the question, explains that the AI does not have an approved answer for this specific topic, and directs the visitor to the right next step — contacting the team, requesting a demo, or waiting for a follow-up if they provided an email.

The fallback message is distinct from an escalation message. A fallback fires when knowledge is absent. An escalation message fires when the conversation is handed to a human agent.

## Confidence Threshold

The confidence threshold is the minimum retrieval confidence score that the AI requires before using a retrieved chunk to construct an answer. It is set per profile.

If the top-ranked retrieved chunks do not meet the threshold, the AI treats the question as unanswerable from approved knowledge and uses the fallback message instead of guessing.

A lower threshold allows the AI to answer with less-certain matches — appropriate for a general product assistant where broad guidance is acceptable. A higher threshold restricts the AI to only answering when it has strong, clearly relevant evidence — appropriate for support or compliance contexts where precision is essential.

## Response Modes

Response mode controls how the AI structures and sizes its answers. A profile can configure a default response mode that fits the context:

- **Concise** — short, direct answers. Best for FAQ-style interactions where the visitor needs a quick answer and does not want to read a paragraph.
- **Standard** — moderate length, structured where useful. The default for most product and support conversations.
- **Detailed** — longer, more comprehensive answers with context, examples, and related points. Best for technical or educational contexts where depth matters.
- **Guided** — the AI asks clarifying questions before answering, to understand the visitor's specific situation. Best for complex support or consultative scenarios.

Response mode is a default per profile, not a hard lock. The AI adjusts based on the nature of the question within the configured mode.

## Intent Handlers — Structured Overrides

Beyond the general behavior prompt, specific conversation intents can be handled with structured overrides. An Intent Handler is a configured rule that fires when the AI detects a specific user intent and replaces or augments the AI's normal retrieval-and-answer flow with a predefined response or action.

Examples of intent overrides a business might configure:

- Intent: visitor asks to book a demo → structured response with a direct link or contact prompt, bypassing knowledge retrieval for this specific intent.
- Intent: visitor asks for pricing → structured redirect to the sales team, with a specific message, bypassing general product retrieval.
- Intent: visitor asks to speak to a human → immediate escalation trigger, regardless of whether knowledge exists.
- Intent: visitor greets or thanks the AI → a warm, contextually appropriate response without retrieval.

Intent handlers let businesses configure predictable, consistent responses for high-value or sensitive intents without relying on the AI to construct those responses dynamically from knowledge.

## Multiple Profiles Per Tenant

A tenant can deploy multiple AI Agent Profiles simultaneously. Each profile serves a different audience or purpose:

- A public product assistant profile for unauthenticated website visitors.
- A customer support profile for verified customers with a different tone, richer knowledge scope, and escalation enabled.
- A partner enquiry profile for verified partners with co-sell positioning and partner-relevant Q&A.
- An internal desk profile for employees with internal SOPs and a more direct, less explanatory tone.
- A Nexy companion profile for guided sales conversations with a consultative persona and CTA-oriented behavior.

All profiles are configured in Nexus Studio and assigned through category identity routes. A visitor on the same website widget can receive completely different AI behavior depending on which category they select and which identity type they are resolved to — without any visible change to the widget interface.

---

# Human Escalation

## When Escalation Happens

Escalation is a designed handoff point, not a failure state. The AI is configured to escalate on seven distinct trigger conditions — each independently enabled or disabled per AI Agent Profile:

- **Low Confidence** — The retrieval score falls below the configured confidence threshold and the query cannot be answered reliably.
- **No Approved Knowledge** — No published knowledge was found within the permitted access scope for this question.
- **User Requested Human** — The visitor explicitly asks to speak with a person; the intent is detected automatically.
- **Sales Lead Detected** — The query intent is a buying signal or pricing enquiry that warrants a sales handoff.
- **Support Required** — The conversation indicates a support issue that exceeds AI resolution scope.
- **Restricted Topic** — The topic is explicitly flagged in the behaviour profile as requiring mandatory human review.
- **Repeated Fallback** — The AI has fallen back on the same or similar question multiple times within the session.

Custom triggers can also be defined per business deployment.

Escalation is opt-in per chat category. Information-only categories can run AI-only with no escalation path. Support or sales categories can require human availability.

## What Happens During Escalation

When escalation triggers, Nexus Live receives an alert routed to the human agents assigned to the relevant category. Agents claim the conversation from the escalation queue. On pickup, the agent sees the full AI conversation thread, an AI-generated summary, and the escalation reason. The visitor does not need to repeat anything.

The agent replies directly through the Nexus Live agent console. The visitor's widget shows the agent's responses in a distinct style. When the agent resolves the conversation, the AI can be handed back automatically with a reconnection message.

Human agents are scoped by category — each agent is assigned to specific chat categories and only sees escalations from those categories.

---

# Nexus Agentic — Autonomous Workflow Runtime

## What Nexus Agentic Is

Nexus Agentic is the autonomous workflow runtime built on top of Nexus Orbit. It is described on the platform as: The Core AI Layer. Built on Nexus Orbit.

Nexus Agentic lets AI agents reason across multiple steps, select from a registered set of tools, draft outputs, and pause for human approval before any external or customer-facing action is taken. Every decision is logged. Every tool call is audited. Nothing is sent without explicit sign-off.

Nexus Agentic uses Orbit's knowledge, governance, identity, and messaging infrastructure as its operating foundation. It does not reimplement retrieval, access resolution, or identity resolution — it consumes those services from Orbit.

## The Six Pillars Of Nexus Agentic

**Capability Packs:** Modular domain bundles that define the goal types, registered tools, approval rules, and memory configuration for a specific business domain. Two capability packs are currently available: Sales Outreach and Purchase Coordination. Each pack can be assigned to an agent candidate at a priority level. Adding a pack gives the agent the full workflow contract for that domain.

**LLM Agent Loop:** The runtime operates as an iterative reasoning loop. The LLM selects which tools to call, processes results, decides the next step, and continues until the goal is resolved or a human approval gate is reached. Runs support up to 25 reasoning steps. The agent operates within the boundaries of its assigned capability packs and approved tool registry.

**Human Approval Gates:** Every outbound action — customer emails, vendor messages, follow-up drafts, or external communications — is drafted by the agent and paused for human review. The agent resumes only after explicit approval, with full context preserved across the wait. Outreach drafts are created with a Draft status and cannot be sent without moving through the approval workflow. The suppression list is always checked before any outreach attempt.

**Governed Tool Registry:** All agent actions are pre-registered as typed tools — read-only, draft-only, internal-write, or customer-facing. The LLM cannot write to the database directly. Every state change flows through a registered, type-safe, audited tool handler. Customer-facing tools raise a controlled block until called through an approved Approval Request.

**Persistent Agent Memory:** Agents store and retrieve key-value state across runs, scoped per agent candidate, per capability pack, and per tenant. Conversation history is persisted through approval pauses so agents resume mid-reasoning exactly where they left off.

**Full Audit Trail:** Every decision, tool call, and approval event is written to structured log records — reasoning text, outcome, tool inputs and outputs, timestamps. A complete, queryable history of what the agent did and why, for every run, for every tenant.

## Current Capability Packs

**Sales Outreach (CAP-SALES):** Supports goal types including outreach draft creation, lead qualification, reply classification, follow-up scheduling, suppression checks, objection handling, and sales campaign management. Contains 15 registered tools.

**Purchase Coordination (CAP-PURCHASE-COORDINATION):** Supports supplier follow-up, RFQ drafting, vendor message drafts, purchase coordination task management, and reply classification. Contains 12 registered tools. This pack is installed but disabled by default.

## Nexus Agentic And Nexus Orbit

Nexus Agentic is not a standalone system. It relies on Nexus Orbit for:

- Knowledge retrieval and access resolution — agents use Orbit's retrieval pipeline to ground responses in approved content.
- Tenant isolation — all agent state is tenant-scoped through Orbit's tenant model.
- Messaging infrastructure — agent-initiated conversations route through Orbit's live chat service.
- Identity resolution — the agent candidate's access scope is resolved through Orbit's access model.

The callout on the Nexus platform website states it clearly: "The knowledge, governance, identity, and messaging infrastructure of Nexus Orbit is the backbone that Nexus Agentic agents rely on — to reason, act, and seek human approval safely."

---

# Nexy — The Role-Based AI Operator

## What Nexy Is

Nexy is the primary named agentic candidate in Nexus AI. Nexy is a generic role-based AI operator — the role it plays is determined by configuration, not code. The same underlying architecture of DocTypes, service layers, and data flows handles every role.

Nexy starts as a Visitor Companion on the website. It uses Nexus Orbit's governed knowledge to hold intelligent, guided conversations with visitors. As a business grows and the platform is configured further, Nexy can expand into a Business Growth Orchestrator — connecting CRM signals, prospect personas, and engagement behavior into coordinated outreach and follow-up actions through Nexus Agentic.

The platform website describes Nexy as: "Nexus Agentic Candidate."

## Nexy As A Visitor Companion

In Visitor Companion mode, Nexy operates through Nexus Live's live chat system. When a visitor starts a conversation on a chat category that has a Nexy Companion Assignment configured, Nexy's companion service enriches the AI response process with a role-specific system prompt built from seven layers:

1. The platform governance layer — base rules all Nexus AI responses follow.
2. The Nexy role profile — tone, communication style, CTA approach, do/don't rules, escalation policy.
3. The knowledge profile — what knowledge is in scope for this visitor and category.
4. The engagement persona — the type of visitor Nexy is designed to engage.
5. The product and service context — Nexus Orbit knowledge the visitor is enquiring about.
6. The conversation history — what has been said so far.
7. The visitor's current message.

In Visitor Companion mode, Nexy:

- Listens to the visitor's question and business context.
- Answers from approved Nexus Orbit knowledge.
- Asks clarifying questions when the visitor's need is not clear.
- Connects the visitor's needs to relevant platform capabilities and use cases.
- Maintains the tone and objective configured in the role profile.
- Avoids prohibited claims and unsupported commitments as defined in the do-not-do rules.
- Escalates to a human when the conversation requires it — sales lead handoff, complex question, or visitor request.

Nexy as Visitor Companion is not a generic bot. It is a role-bound companion operating inside Nexus Orbit's governance model, using approved knowledge, within configured boundaries.

## Nexy As A Business Growth Orchestrator

Beyond inbound companion conversations, Nexy operates as a Business Growth Orchestrator through the Nexus Agentic runtime. In this mode, Nexy:

- Identifies and qualifies prospects through the Sales Outreach capability pack.
- Matches prospects to customer personas using LLM-generated persona match scores.
- Generates personalized outreach messages — grounded in approved knowledge and aligned with the configured selling style and persuasion approach.
- Applies guardrails to every generated message before it can proceed, checking against role profile do-not-do rules and the grounding requirement.
- Sends the message draft to a human for explicit approval before any communication token or chat invitation is created.
- Classifies inbound replies for sentiment, intent, buying signals, and escalation flags.
- Schedules follow-up actions based on engagement rules.
- Links any resulting live chat conversation back to the originating campaign and target record for a complete engagement audit trail.

The suppression list is checked at every outreach attempt. Any target marked do-not-contact is blocked from all Nexy processing without exception.

## Nexy Roles

The generic Nexy architecture supports multiple role types. The same DocTypes, services, and data flows handle every role — only the role profile configuration and role extension records differ. Current and planned roles:

| Role | Engages With | Topic | Status |
| --- | --- | --- | --- |
| Sales | Prospect | Product and Service | Active (MVP) |
| Customer Success | Customer | Renewal, Upsell, Health | Planned |
| HR Onboarding | Candidate | Job Role and Onboarding | Planned |
| Partner Management | Partner | Programme and Activation | Planned |
| Vendor Qualification | Vendor | Procurement and Assessment | Planned |
| Field Service | Site Contact | Visit and Maintenance | Planned |
| Support Proactive | Customer | Support Case and Follow-up | Planned |
| Custom | Any | Configurable | Planned |

## Nexy Governance Rules

- **Do-not-contact flag:** If a target has the do-not-contact flag set, all Nexy processing for that target is blocked unconditionally.
- **Knowledge grounding:** When `requires_grounding` is enabled on the role profile, every claim in a generated message must be traceable to a retrieved knowledge source.
- **Human approval for outbound:** When `requires_human_approval_for_outbound` is set, the outreach message waits for explicit human approval before any chat invitation or external communication is generated.
- **Access scope intersection:** The effective knowledge scope for any Nexy conversation is the intersection of the identity-resolved scope and the campaign's configured knowledge profile. If the intersection is empty, the system fails closed.
- **LLM cannot see allowed access policies:** The LLM does not have visibility into the internal access policy names or structures. Access resolution happens outside the model boundary.

---

# How The Platform Components Relate

Nexus Orbit is the foundation. It provides knowledge management, governance, identity, access control, live chat, channel routing, and operational infrastructure.

Nexus Agentic runs on top of Orbit. It uses Orbit's retrieval, access, tenant, and messaging services to power autonomous multi-step agent runs. Agentic does not reimplement any Orbit service.

Nexy is an agent candidate that runs on both. As a Visitor Companion, Nexy uses Orbit's live chat and knowledge services directly. As a Business Growth Orchestrator, Nexy submits goals to the Agentic runtime, which uses Orbit services as its operating foundation.

The hierarchy is:

```
Nexus AI
├── Nexus Orbit (governed intelligence layer)
│   ├── Nexus Studio (build and configure)
│   ├── Nexus Live (operate and monitor)
│   └── Nexus Administration (govern and comply)
│   └── Delivers: Chat Bot, Q&A, Apps
│
├── Nexus Agentic (autonomous workflow runtime, built on Orbit)
│   ├── Capability Packs (Sales Outreach, Purchase Coordination)
│   ├── LLM Agent Loop
│   ├── Human Approval Gates
│   ├── Governed Tool Registry
│   ├── Persistent Agent Memory
│   └── Full Audit Trail
│
└── Nexy (role-based AI operator, runs on Orbit + Agentic)
    ├── Visitor Companion (inbound — via Orbit Live Chat)
    └── Business Growth Orchestrator (outbound — via Agentic)
```

---

# Example Questions And Answers For Public Chat

## About The Platform

Question: What is Nexus AI?

Answer: Nexus AI is a governed AI platform that turns approved business knowledge into safe, identity-aware AI experiences across chat, Q&A, workflow apps, and autonomous agents. It is built around three components: Nexus Orbit (the governed intelligence layer), Nexus Agentic (the autonomous workflow runtime), and Nexy (the role-based AI operator). The platform gives organizations full control over what the AI knows, who can access it, and when a human must take over.

---

Question: What are the main components of Nexus AI?

Answer: Nexus AI has three main components. Nexus Orbit is the core governed platform — it includes Nexus Studio for building and configuring AI experiences, Nexus Live for operating and monitoring live conversations, and Nexus Administration for multi-tenant governance and compliance. Nexus Agentic is the autonomous workflow runtime that runs on top of Orbit — it powers multi-step AI agents with human approval gates. Nexy is the role-based AI operator that uses both — starting as a Visitor Companion in live chat and expanding into a Business Growth Orchestrator for outbound campaigns.

---

Question: How is Nexus AI different from a normal chatbot?

Answer: A chatbot typically answers from a fixed script or from broad AI training data. Nexus AI is built around governed knowledge — the AI retrieves from approved sources, applies access rules based on who is asking, respects identity boundaries, supports multiple deployment channels, and provides a complete audit trail. It also goes beyond chat: the same platform powers Q&A experiences, workflow apps, autonomous agentic runs, and role-based operators like Nexy.

---

Question: What is Nexus Orbit?

Answer: Nexus Orbit is the governed intelligence layer at the core of every Nexus AI deployment. It provides three purpose-built workspaces: Nexus Studio for building and configuring chat bots, Q&A experiences, and workflow apps; Nexus Live for real-time conversation monitoring, escalation management, and human handoff; and Nexus Administration for multi-tenant governance, user management, knowledge policy, and audit trails. Orbit also delivers the knowledge management, access control, identity model, and channel routing that Nexus Agentic and Nexy depend on.

---

Question: What are the three Nexus Orbit workspaces?

Answer: The three Nexus Orbit workspaces are Nexus Studio, Nexus Live, and Nexus Administration. Nexus Studio is where you build and configure — create chat bots, manage knowledge, define identity rules, design escalation triggers, and publish AI experiences without code. Nexus Live is where you operate and monitor — watch live conversations, handle escalations, manage support tickets, and track platform performance. Nexus Administration is where you govern and comply — manage tenants, enforce user permissions, set knowledge policies, and maintain a full audit trail.

---

Question: What products does Nexus Orbit deliver?

Answer: Nexus Orbit delivers three AI product types: Nexus Chat Bot (a multi-tenant, identity-aware conversational AI that can serve public visitors, verified customers, and internal employees each within their own knowledge and access scope), Nexus Q&A (structured knowledge-driven answers with no hallucinations and full auditability), and Nexus Apps (purpose-built workflow AI experiences for onboarding, support, HR, ERP, training, and more).

---

## About Knowledge And Quality

Question: How does knowledge work in Nexus AI?

Answer: Knowledge in Nexus AI goes through a governed lifecycle before the AI can use it. Content is uploaded or entered as a Knowledge Source, broken into logical Knowledge Units, and split into Knowledge Chunks that carry embedding vectors. The platform processes chunks through vector and keyword indexing. Before publishing, the platform automatically runs backward tests — generating synthetic questions from the content and verifying the AI produces accurate answers for each one. Only content that reaches Published status is available for retrieval. Unpublished or expired content is automatically withheld.

---

Question: What is backward testing and how does it work?

Answer: Backward testing is the quality assurance step built into the Nexus AI knowledge lifecycle. When a knowledge source reaches the Testing stage, the platform automatically generates synthetic questions from the content — questions that represent what a real user might ask. Each question becomes a Knowledge Test Case, and a Knowledge Test Run is executed: the question goes through the full retrieval pipeline and the system records which chunks were retrieved, confidence scores, and whether the AI's answer accurately reflects the source. These test cases also form correlated question sets — multiple phrasings of the same question, testing retrieval robustness under paraphrasing and synonym variation. Beyond testing, the processing step generates useful questions stored as Knowledge Index Entries of type User Question, embedded alongside the content. These power the Question-First search path: when a visitor asks something, the retrieval engine first searches only the User Question index. If a match scores above the confidence threshold, the engine retrieves exactly the linked chunk and skips the full corpus scan. This reduces embedding search cost, database fetch volume, and re-ranking workload for common queries — only falling back to the full hybrid pipeline when no question-first match is found. Content that fails its test runs returns to Draft before any real user can query it.

---

Question: Does the platform generate test questions automatically or does someone have to write them?

Answer: Automatically. When a knowledge source enters the Testing stage, the platform uses the LLM to generate synthetic test questions directly from the content. No manual question writing is needed. The generated questions cover different angles, phrasings, and levels of specificity based on what is in the source. This means a business team can upload a 50-page product guide and the platform will automatically stress-test it across dozens of generated questions before the content goes live.

---

Question: How do useful questions help reduce the cost of answering visitor queries?

Answer: When the platform processes a knowledge source, it automatically generates a set of useful questions — the questions that source is best equipped to answer. Each useful question is embedded and stored as a Knowledge Index Entry of type User Question, linked to the specific chunk that answers it. When a visitor sends a message, the retrieval engine runs what is called the Question-First path: it searches only the User Question index first, using the same embedding as the visitor's query. If a User Question entry matches above the confidence threshold, the engine already knows exactly which chunk to retrieve and fetches only that chunk — skipping the full embedding scan across the entire knowledge base. This is significantly cheaper than searching all chunks for every query. For the most common questions in a deployment, the majority of answers are served through the Question-First path, which reduces embedding distance computations, database row fetches, and re-ranking workload. Only when no high-confidence User Question match is found does the engine fall back to the full hybrid retrieval pipeline. The more comprehensive the useful question index — which grows automatically as sources are processed and tested — the higher the proportion of queries served through the efficient Question-First path.

---

Question: What is RAG and how does Nexus AI use it?

Answer: RAG stands for retrieval-augmented generation. Before producing an answer, the engine retrieves relevant knowledge chunks from the approved knowledge base that the current user and conversation are allowed to access. Retrieval uses hybrid scoring — combining semantic vector similarity with BM25 keyword scoring, followed by a re-ranking pass using a cross-encoder model. Query expansion improves recall. Access filtering removes any chunks outside the current user's allowed policies. Only if the top candidates meet the configured confidence threshold does the AI use them to construct a response. Otherwise it uses the configured fallback message rather than guessing.

---

Question: What is a Knowledge Gap and what happens when one is detected?

Answer: A Knowledge Gap is recorded when the AI cannot answer a question — because no relevant approved knowledge was found or the confidence threshold was not met. Gaps are deduplicated by semantic hash, so multiple visitors asking about the same topic are grouped into one gap with a frequency count. Each gap goes through an automated LLM assessment to determine whether it represents a genuine business topic worth addressing. Administrators can review gaps, see sample queries, and create a new knowledge source directly from the gap record. Once the source is authored, tested, and published, the gap is resolved. Visitors who provided their email when they received a fallback can be automatically notified with an updated answer when the gap is closed.

---

Question: Can public visitors access internal or private content?

Answer: No. Public chat is limited to knowledge covered by public access policies. The access model resolves the allowed policies for the current user and context before retrieval begins. Internal, customer-specific, partner-only, or admin-level content is not accessible to a public visitor regardless of how the question is phrased. The access boundary is enforced at the retrieval layer — the AI never sees restricted content in the first place.

---

Question: What happens when the AI cannot answer a question?

Answer: When the AI cannot find relevant approved knowledge above the configured confidence threshold, it uses the fallback message configured for that AI agent profile rather than guessing. The question may be recorded as a Knowledge Gap. If the visitor provides their email, Nexus AI can notify them when a matching knowledge source is published later. The visitor is guided to the appropriate contact or support path.

---

## About AI Behavior

Question: Can the AI's personality and tone be configured?

Answer: Yes. Each AI Agent Profile carries a complete behavioral configuration — persona name and role, behavior prompt with tone and style instructions, welcome message, fallback message, response mode (concise, standard, detailed, or guided), and explicit do-not-answer rules. A public product assistant can be warm and exploratory in tone while a customer support assistant is precise and direct, and an internal employee assistant is efficient and assumes domain familiarity. All three can run on the same platform with entirely different personas.

---

Question: What are do-not-answer rules?

Answer: Do-not-answer rules are explicit restrictions configured in an AI Agent Profile that tell the AI what it must never discuss, commit to, or speculate about — regardless of whether knowledge exists in the approved base and regardless of how the question is phrased. Examples include: never quote a price without directing to the sales team; never discuss a competitor; never speculate about unannounced features; never provide account-specific information to an unverified visitor; never engage with off-topic personal questions. These rules operate at the system instruction level and complement the access model — the access model restricts what content the AI retrieves, while do-not-answer rules restrict what statements the AI can make.

---

Question: What is the confidence threshold?

Answer: The confidence threshold is the minimum retrieval score the AI requires before using a retrieved chunk to answer a question. It is set per AI Agent Profile. If no retrieved chunk meets the threshold, the AI treats the question as unanswerable from approved knowledge and uses the fallback message instead of guessing. A higher threshold means the AI only answers when it has clearly relevant evidence — appropriate for support or compliance contexts. A lower threshold is more permissive — appropriate for general product information where broad guidance is acceptable.

---

Question: Can different audiences on the same website receive different AI behavior?

Answer: Yes. Multiple AI Agent Profiles can be deployed per tenant. A public visitor on the website chat can receive the public product assistant profile. A verified customer on the same widget — after email verification — can be routed to the customer support profile with a different tone, a richer knowledge scope, and escalation enabled. A verified partner can receive the partner enablement profile. Each audience tier gets the behavior configured for their identity type and selected category, with no visible change to the widget interface.

---

Question: What is an intent handler?

Answer: An Intent Handler is a structured override configured for a specific user intent. When the AI detects a particular intent — such as a request to book a demo, ask for pricing, or speak to a person — the intent handler fires a predefined response or action instead of the normal retrieval-and-answer flow. This ensures that high-value or sensitive intents always receive a consistent, controlled response regardless of what knowledge is available. Intent handlers are configured per AI Agent Profile in Nexus Studio.

---

## About Access And Identity

Question: How does access control work in Nexus AI?

Answer: Access control in Nexus AI operates through a chain: Access Policies group knowledge sources by sensitivity level. Access Categories group policies by audience. Knowledge Profiles define a set of allowed access categories for a given context. Identity Types are resolved at the conversation level. An Identity Registry SafeGuard applies a hard ceiling on what any holder of a given identity type can ever access. The effective scope for any conversation is the intersection of the Knowledge Profile and the SafeGuard ceiling — the narrower set always wins. This resolution happens before retrieval, so the AI only searches knowledge it is explicitly permitted to return.

---

Question: Who can use Nexus AI?

Answer: Nexus AI is designed to serve different identity types within the same platform: Public Visitors (unauthenticated, public knowledge only), Verified Customers (email-verified, customer knowledge scope if configured), Internal Employees (authenticated desk users, internal knowledge scope), Business Partners (verified partner identities), Training Participants, and custom identity types an organization defines. Each identity type has its own knowledge boundary, verification mode, and allowed access scope.

---

Question: How does identity verification work?

Answer: Identity verification mode is set per chat category. A public category requires no verification — the visitor is treated as a public visitor. A category with Email OTP mode asks the visitor to provide their email, sends a one-time code, and requires verification before access expands beyond the public scope. A category with Registered Email OTP checks the visitor's email against the Identity Registry — if matched, the verified identity type and its associated knowledge profile are applied to the conversation.

---

Question: What is the Identity Registry SafeGuard?

Answer: The Identity Registry SafeGuard is a hard ceiling configured per identity type that caps the maximum knowledge scope any holder of that type can ever access — regardless of what the AI Agent Profile or route configuration might allow. It is a safety guarantee, not a default. The effective knowledge scope for any conversation is always the intersection of the route's knowledge profile and the SafeGuard ceiling. If the intersection is empty, the system fails closed.

---

## About Channels And Routing

Question: What is a channel in Nexus AI?

Answer: A channel is the logical entry point for a conversation — a website chat widget, customer portal, internal intranet, mobile app, or API. Each channel has a type (Website Chat, Desk, API), belongs to a tenant, and defines the default AI agent and surface-level settings. Channels are a governance and routing layer. Website visitors do not need to select a channel — they select a chat category, and the category implies the channel behind the scenes.

---

Question: What are chat categories?

Answer: Chat categories are the visitor-facing topic choices in the chat widget — for example, "Ask Anything About Nexus AI", "Customer Support", or "Partner Enquiry." Each category belongs to a channel internally. Selecting a category tells Nexus AI what kind of conversation the visitor wants, which the routing layer uses to determine the correct AI behavior, knowledge scope, identity rules, and escalation policy. Categories can carry pre-built FAQ answers and define their own identity verification mode.

---

Question: What is a Category Identity Route?

Answer: A Category Identity Route maps a combination of Chat Category and Identity Type to a specific AI Agent Profile, Knowledge Profile, and Identity Profile. It is the mechanism that connects a visitor's conversation choice and resolved identity to the correct AI behavior and knowledge access — without exposing any routing logic to the visitor. Routes must be enabled and published before they take effect.

---

## About Human Escalation

Question: Can Nexus AI hand a conversation to a human?

Answer: Yes. Human escalation is a core capability of Nexus AI. Escalation is opt-in per chat category — it is configured in Nexus Studio and operates through Nexus Live. Seven trigger conditions are available, each configurable independently per AI Agent Profile: Low Confidence (retrieval score below threshold), No Approved Knowledge (no published content in scope for the question), User Requested Human (visitor explicitly asks for a person), Sales Lead Detected (buying signal or pricing enquiry), Support Required (issue exceeds AI resolution scope), Restricted Topic (topic flagged as mandatory human-review), and Repeated Fallback (same question has fallen back multiple times in the session). When a trigger fires, the conversation moves to the escalation queue in Nexus Live. Human agents claim conversations with the full AI thread, an AI-generated summary, and the escalation reason already loaded. The visitor does not need to repeat anything. After the human resolves the issue, the AI can be handed back automatically.

---

## About Nexus Agentic

Question: What is Nexus Agentic?

Answer: Nexus Agentic is the autonomous workflow runtime built on top of Nexus Orbit. It lets AI agents reason across multiple steps, select tools from a registered tool library, draft outputs, and pause for explicit human approval before any external action is taken. Every decision and tool call is logged in a structured audit trail. Nexus Agentic runs on Orbit's knowledge, governance, identity, and messaging infrastructure — it does not operate independently.

---

Question: How does the Nexus Agentic agent loop work?

Answer: The Nexus Agentic runtime operates as an iterative LLM reasoning loop. The agent receives a goal, selects which registered tools to call, processes results, and decides the next step — continuing until the goal is resolved or a human approval gate is required. Runs support up to 25 reasoning steps. The agent operates strictly within its assigned capability pack's goal types and registered tools. No direct database writes or external API calls are made outside the governed tool registry.

---

Question: What are Capability Packs in Nexus Agentic?

Answer: Capability Packs are modular domain bundles that define the goal types, registered tools, approval rules, and memory configuration for a specific business domain. Nexus Agentic currently ships with two: Sales Outreach (15 tools, 9 goal types including outreach draft, lead qualification, reply classification, and follow-up scheduling) and Purchase Coordination (12 tools, 9 goal types including supplier follow-up, RFQ drafting, and vendor message drafts). Assigning a pack to an agent candidate gives the agent the full workflow contract for that domain.

---

Question: Does Nexus Agentic send messages automatically?

Answer: No. Every outbound action — customer emails, vendor messages, follow-up drafts, or external communications — is drafted by the agent and paused for human review. The agent cannot send anything until a human explicitly approves the Approval Request. Outreach drafts are always created with a Draft status. The suppression list is checked before every outreach attempt. Any target marked do-not-contact is blocked unconditionally.

---

## About Nexy

Question: What is Nexy?

Answer: Nexy is the primary named agentic candidate in Nexus AI. Nexy is a role-based AI operator — the role it plays is determined by configuration. It starts as a Visitor Companion on the website, using Nexus Orbit's governed knowledge to hold intelligent, guided inbound conversations with visitors. As a business grows, Nexy expands into a Business Growth Orchestrator, running outbound campaigns through the Nexus Agentic runtime. The same underlying architecture handles every role — only the role profile and role extension configuration differ.

---

Question: What does Nexy do as a Visitor Companion?

Answer: As a Visitor Companion, Nexy operates through Nexus Live's live chat system. When a visitor starts a conversation on a chat category with a Nexy companion assignment, Nexy enriches the AI response with a role-specific system prompt that combines platform governance rules, the configured role profile (tone, CTA style, do/don't rules), the knowledge scope for that visitor, the engagement persona, product context, conversation history, and the visitor's current message. Nexy listens to the visitor's needs, answers from approved knowledge, asks clarifying questions when useful, connects needs to relevant capabilities, and escalates to a human when appropriate.

---

Question: Is Nexy the same as a chatbot?

Answer: No. A chatbot focuses on conversation. Nexy is a role-based AI operator built on Nexus Orbit's governed platform. As a Visitor Companion, Nexy uses governed knowledge retrieval, identity-aware access, and configured role rules — it is not a free-form responder. As a Business Growth Orchestrator, Nexy can submit multi-step goals to the Nexus Agentic runtime, generate outreach through approval-gated workflows, and link campaign and engagement history to live chat conversations. The depth of governance, role configuration, and agentic integration is what distinguishes Nexy from a standard chatbot.

---

Question: What roles can Nexy play?

Answer: Nexy can be configured for any business role where an AI operator is needed. The current active role is Sales, where Nexy engages with prospects on product and service topics. Planned roles include Customer Success (customer renewal and health), HR Onboarding (candidate job role and onboarding), Partner Management (partner programme and activation), Vendor Qualification (vendor procurement and assessment), Field Service (site contact and visit), Support Proactive (customer support case follow-up), and custom roles. The same architecture handles every role — only the role profile and role extension configuration change.

---

## About Audiences And Knowledge Profiles

Question: Can Nexus AI serve different types of users — visitors, customers, employees, partners — on the same platform?

Answer: Yes. Nexus AI is built specifically for this. The platform recognizes different identity types — Public Visitor, Verified Customer, Business Partner, Internal Employee, Training Participant, and custom types — and assigns each a different knowledge profile. Each profile defines exactly which knowledge that audience can access. Public visitors get public product information. Verified customers get support content. Partners get partner programme material. Employees get internal operational knowledge. All from the same governed platform, each audience bounded by their profile, with no cross-audience leakage.

---

Question: What is a knowledge profile and why does it matter commercially?

Answer: A Knowledge Profile is the answer to the question — what view of the business's knowledge should this type of person receive? In commercial terms, it defines the knowledge boundary for a specific audience tier. A public product profile might include marketing content, feature guides, and public FAQs. A customer support profile adds troubleshooting guides and account setup documentation. A partner profile adds co-sell playbooks and reseller pricing material. An employee profile adds internal SOPs, HR policies, and operational procedures. Each profile ensures the AI only retrieves what that audience is entitled to see — the profile enforces the boundary, not the AI's judgment.

---

Question: How does a customer get access to more content than a public visitor?

Answer: Through identity verification. When a chat category is configured with email OTP or registered email verification, the platform asks the visitor for their email and sends a one-time code. Once verified, the platform checks the visitor's email against the Identity Registry. If matched to a verified customer record, the conversation is routed through the customer identity type with the customer knowledge profile applied. The AI can now retrieve from the richer customer knowledge set — support guides, product documentation, account help — that is invisible to unverified public visitors.

---

Question: Can a partner see content that customers cannot?

Answer: Yes. The partner identity type can be assigned its own knowledge profile that includes content the customer profile does not. Co-sell materials, reseller pricing guides, partner programme documentation, and joint go-to-market resources can be scoped to the partner profile only. When a verified partner interacts with the platform — through a partner-specific chat category or portal — the partner knowledge profile is applied and the AI retrieves from that enriched scope. Customers and public visitors are served from their own profiles and cannot reach partner content.

---

Question: Can employees use Nexus AI for internal questions?

Answer: Yes. Internal employees interact with Nexus AI through desk channels and authenticated workspaces — not the public website widget. They are recognized as internal employees through their logged-in session. Their knowledge profile includes internal content: SOPs, HR policies, finance procedures, IT guides, compliance documents, and operational workflows. This is entirely separate from what the public website chat delivers. One platform powers both external and internal AI experiences, with the audience tier determining what each person can access.

---

Question: Can Nexus AI support a training or onboarding programme?

Answer: Yes. The Training Participant identity type is designed for this. A business can configure a knowledge profile scoped to specific training modules, learning materials, process guides, and assessment-relevant content. New employees, onboarding customers, or partners going through a certification programme can ask questions conversationally and receive precise, approved answers from the training knowledge set. This works alongside the same platform serving public chat, customer support, and internal operations — each audience in its own governed knowledge lane.

---

Question: What is the Identity Registry SafeGuard and why does it exist?

Answer: The Identity Registry SafeGuard is a hard ceiling on what any person holding a given identity type can access — regardless of what the AI agent profile or route configuration might allow. It exists as a safety guarantee for the business. Even if a route is misconfigured or a knowledge profile is accidentally set too broadly, the SafeGuard ensures the maximum possible scope for any given identity type cannot be exceeded. The effective knowledge scope for any conversation is always the narrower of the route's profile and the SafeGuard ceiling. It is a fail-safe that prevents escalation of access beyond what the business has explicitly authorized for each audience tier.

---

Question: What stops a public visitor from accessing internal or customer content?

Answer: The access model. Before the AI retrieves anything, the engine resolves the allowed access policies for the current conversation. For a public visitor, that resolution produces only the policies assigned to the public knowledge profile — no customer, partner, employee, or internal policies are included. Only knowledge sources covered by those allowed policies are eligible for retrieval. The AI cannot return content outside those policies regardless of how the question is phrased. This is enforced at the retrieval layer, not the response layer — the AI never sees the restricted content in the first place.

---

## About Multi-Tenancy

Question: Can Nexus AI serve multiple companies on one platform?

Answer: Yes. Nexus AI is fully multi-tenant. Each tenant is a completely isolated business workspace with its own knowledge, bots, channels, categories, users, agents, conversations, and settings. One Nexus AI deployment can serve multiple client organizations, multiple brands, multiple business units, or multiple environments — with no cross-tenant data exposure by design. Nexus Administration provides full visibility and control over all tenants from one governance dashboard.

---

## About Security

Question: Is Nexus AI secure for public website use?

Answer: Yes. Public chat is restricted to knowledge covered by public access policies. The access model resolves allowed policies before retrieval begins. Internal, customer-specific, restricted, or admin-level content cannot be returned in a public conversation. Identity verification can be required for any category that needs to go beyond public scope. Every AI action is logged in the audit trail. The platform supports SSO/SAML integration, two-factor authentication enforcement, IP restrictions, and configurable data residency.

---

# Safe Public Chat Boundaries

The public website assistant answers only from public approved knowledge. It avoids:

- Internal configuration details, deployment records, or platform administration procedures.
- Credentials, API keys, secrets, or infrastructure information.
- Private customer, partner, or employee data.
- Account-specific support information.
- Restricted admin procedures or debugging runbooks.
- Unapproved pricing commitments or product timeline claims.
- Claims not present in approved public knowledge.

If a visitor asks for something outside public knowledge, the assistant responds politely and directs the visitor to the official contact or support path.

---

# Demo And Contact Guidance

Visitors who want to evaluate Nexus AI should request a demo or contact the Nexus AI team through the website.

A demo can cover:

- How Nexus Orbit works — Studio, Live, and Administration workspaces in practice.
- How knowledge is prepared, tested, and governed before the AI uses it.
- How access control protects internal and restricted information from public visitors.
- How chat categories, channels, and identity routes are configured.
- How Nexus Chat Bot, Q&A, and Apps are deployed and managed.
- How human escalation is designed and operated through Nexus Live.
- How Nexus Agentic enables controlled autonomous workflows with human approval gates.
- How Nexy operates as a Visitor Companion and how it can expand into outbound campaigns.
- How the multi-tenant model can support a visitor's specific organization, brand, or deployment context.

When a visitor asks for a demo, the assistant can suggest sharing:

- Name and organization.
- Business email.
- Main use case — website chat, customer support, internal knowledge, agentic workflows, or Nexy.
- Any current challenge with knowledge management, support automation, or AI adoption.

---

# Positioning Summary

Nexus AI is a governed AI platform built for organizations that need more than a chatbot. It combines a governed knowledge layer, identity-aware access control, multi-tenant isolation, live operations, and autonomous agentic capabilities in one platform — structured into Nexus Orbit, Nexus Agentic, and Nexy.

Orbit is the foundation: governed knowledge, three workspaces, three AI product types.
Agentic is the action layer: multi-step agents, registered tools, human approval gates.
Nexy is the operator: role-based, knowledge-grounded, companion and orchestrator.

One platform. Governed from knowledge to action.
