# Nexus Platform — Complete Knowledge Guide for Nexy

> Purpose: Knowledge source for Nexy to draw from when advising visitors about the Nexus Platform.  
> Tone: Confident, clear, honest. Never use "sales", "selling", or "pitch". Advise and guide.  
> Last updated: 2026-06-23

---

## 1. What Is the Nexus Platform?

The Nexus Platform is a governed AI interaction platform that lets businesses deploy AI-powered chat bots, Q&A experiences, workflow apps, and autonomous agents — while remaining in complete control of what the AI knows, who it serves, and what it is allowed to say.

The platform is built around a single principle: **every AI response must be earned**. Knowledge is approved before the AI can use it. Access is defined before the AI can retrieve it. Identity is verified before access is granted. Nothing reaches a visitor or employee that has not passed through that governed chain.

Nexus is not a generic AI wrapper. It is a structured, multi-tenant platform with its own knowledge engine, access control model, identity verification system, conversation runtime, human escalation infrastructure, and autonomous agent framework — deployed as a unified product that business teams configure without writing code.

**The platform is organised into two layers:**

- **NEXUS ORBIT** — the governed intelligence and interaction layer. Three workspaces: Nexus Studio (build), Nexus Live (operate), Nexus Administration (govern).
- **NEXUS AGENTIC** — the autonomous agent layer that inherits all of ORBIT's governance and extends it with autonomous reasoning, multi-step action, and human approval gates.

---

## 2. The Problems Nexus Solves

### For businesses deploying AI to customers or employees:

| Problem | What Nexus does about it |
|---|---|
| AI responses include incorrect or hallucinated information | All responses are grounded in approved, validated knowledge only. The AI never draws from the open internet. |
| The same AI sees information it shouldn't | Knowledge is isolated by tenant, by access category, and by identity type. What the AI retrieves depends on who is asking. |
| AI can't be trusted without human oversight | Every AI decision is logged in a tamper-evident audit trail. Human escalation is a designed handoff, not an afterthought. |
| Building AI experiences requires an engineering team | Nexus Studio is entirely no-code. Business teams configure bots, knowledge, identity rules, and escalation paths without any code. |
| Knowledge gaps are invisible until a customer complains | Nexus automatically detects unanswered queries, logs them as Knowledge Gaps, and provides a one-action workflow to turn any gap into new content. |
| AI deployed to customers is different from AI used internally | Nexus supports any number of audiences on the same deployment — each with their own identity type, knowledge scope, and behaviour profile. |
| Multiple clients or business units need separate AI environments | Nexus is fully multi-tenant by design. Each tenant is completely isolated — separate knowledge, bots, users, agents, and settings. |

---

## 3. The Seven Governance Layers

Every AI response on the Nexus Platform travels through seven governed layers before reaching the user. This is the NEXUS ORBIT routing chain.

```
Knowledge Foundation
      ↓
Access Governance
      ↓
Identity & Verification
      ↓
Intelligent Routing
      ↓
AI Behaviour Profile
      ↓
Governed Delivery
      ↓
Human Escalation (when required)
```

**Layer 1 — Knowledge Foundation**  
All knowledge is tenant-isolated and uploaded by your team. It moves through a structured pipeline: Upload → Processing → Backward Testing → Validation → Published. Only published, validated content can ever be retrieved by the AI.

**Layer 2 — Access Governance**  
Knowledge is grouped into Access Categories. Each AI Agent Profile is assigned a set of categories — the AI can only retrieve from those categories, no matter what the user asks. Access Policies add additional conditions (verification required, channel-specific, sensitivity-restricted).

**Layer 3 — Identity & Verification**  
Before retrieval begins, Nexus determines who is asking. Identity types (Public Visitor, Verified Customer, Internal Employee, Business Partner, custom types) carry their own access ceiling through the Identity Registry SafeGuard. A verified customer sees more than a public visitor on the same channel.

**Layer 4 — Intelligent Routing**  
The combination of Channel + Chat Category + Identity Type maps to a specific AI Agent Profile through a Category Identity Route. Different users on the same channel receive different AI behaviour, knowledge scope, and tone — automatically, without code.

**Layer 5 — AI Behaviour Profile**  
The Agent Profile defines the AI's persona, tone, system instructions, confidence threshold, do-not-answer rules, memory mode, and escalation settings. This is where the AI's character and limits are configured.

**Layer 6 — Governed Delivery**  
Responses are delivered through real-time channels (website widget, customer portal, internal intranet, embedded iframe). The delivery channel is bound to the AI configuration — no response escapes governance to reach the wrong channel.

**Layer 7 — Human Escalation**  
When the AI reaches a defined trigger point — low confidence, restricted topic, user request, frustration, complexity — the conversation is handed to a human agent with the full AI thread, identity context, and escalation reason. No context is lost. No repeat questioning.

---

## 4. How Knowledge Works

### 4.1 Knowledge Ingestion Pipeline

When your team uploads a document, FAQ, SOP, policy, or any other content into Nexus Studio, it moves through this pipeline before the AI can use it:

1. **Upload** — Your team uploads content and assigns it to a Knowledge Profile and Access Category.
2. **Processing** — The system automatically chunks, embeds, and classifies the content. Metadata, sensitivity level, and access categories are resolved.
3. **Backward Testing** — Nexus generates synthetic questions from the processed content and tests whether the knowledge produces accurate, useful answers. This happens before any real user ever asks.
4. **Validation** — Your team reviews the backward testing results. Content that passes moves to Validated; content that fails returns to Draft for revision.
5. **Published** — Validated content goes live and is immediately available to the AI. Unpublished or failed content is never exposed to any query.

**Readiness states:** Draft → Processing → Testing → Validated → Published (or Failed → Draft)

### 4.2 Knowledge Quality & Gap Intelligence

Publishing content is not the end. Nexus continuously monitors how knowledge performs and provides two mechanisms for ongoing quality:

**Auto-generated Useful Questions** — During processing, Nexus automatically generates the questions each knowledge source is best equipped to answer. These are indexed alongside the content to improve retrieval precision beyond simple keyword matching.

**Correlated Question Sets (Knowledge Test Cases)** — Backward testing produces multiple phrasings of the same question, testing whether the source retrieves reliably under paraphrasing and synonym variation. These sets are re-evaluated whenever content is updated.

**Reactive Gap Detection** — When a live query falls below the confidence threshold, the system automatically logs a Knowledge Gap record — capturing the visitor's question, session context, and searched categories. Gaps accumulate a frequency count so high-volume gaps rise to the top of the review queue.

**Gap-to-Source Workflow** — Any Knowledge Gap can be converted directly into a new Knowledge Source draft in one action. Nexus pre-populates the draft with the gap's question cluster, category assignment, and suggested access classification. When the new source is published, the related gaps close automatically.

### 4.3 What kinds of content become knowledge?

- Product and service documentation
- Customer-facing FAQs and support articles
- Internal SOPs, policies, and HR handbooks
- ERP operational guides and business rules
- Partner onboarding and training material
- Compliance and regulatory reference content
- Sales enablement materials (product benefits, outcomes, objection responses)
- Custom Q&A pairs

---

## 5. The Three Products

### 5.1 Nexus Chat Bot

A governed, identity-aware conversational AI for any audience — public visitors, verified customers, internal employees, or business partners. Each chat bot is independently configured with its own knowledge scope, persona, tone, behaviour rules, and escalation settings. Multiple bots can serve different audiences on the same channel simultaneously.

**Key capabilities:**
- Identity-aware retrieval — what the AI shares depends on who is asking
- Confidence threshold — the AI falls back rather than guessing when below threshold
- Do-not-answer rules — explicit topic restrictions the AI must refuse regardless of knowledge
- Memory mode — session-only, cross-conversation, or no memory
- Escalation integration — human handoff when the AI reaches a defined trigger
- Multi-channel deployment — website widget, customer portal, internal intranet, embedded iframe
- Real-time delivery with typing indicators and message hold during escalation

### 5.2 Nexus Q&A

Structured knowledge sessions where users ask specific questions and receive precise, sourced answers from your approved content. Q&A experiences are topic-bounded and source-cited — visitors can see which document answered their question.

**Key capabilities:**
- Topic-bounded — the Q&A session only uses content assigned to it
- Confidence threshold — minimum confidence before the AI responds
- Out-of-scope handling — defined behaviour when questions fall outside approved knowledge
- Source citation — show or suppress which document answered the question
- Suggested question sets — guide users to the most valuable queries
- No hallucinations — if the answer is not in approved knowledge, the AI says so

### 5.3 Nexus Apps

Purpose-built workflow AI experiences for specific business functions — configured in Nexus Studio and deployed to any portal without code. Each app has its own workflow design, knowledge scope, access policy, user path, and output format.

**App types include:**
- Onboarding Guide
- SOP Navigator
- Training Assistant
- Support Desk
- HR Helpdesk
- ERP Assistant
- Knowledge Portal
- Process Workflow

**Key capabilities:**
- Role-based access per app — restrict to specific user categories or departments
- Workflow step definition — structured task and response flow
- Per-app knowledge binding — each app only uses its assigned content
- App embedding — generate widget code for any portal or site
- App preview and workflow simulation before deployment

---

## 6. The Three Workspaces

### 6.1 Nexus Live — Real-Time Operations Centre

The workspace where AI-powered conversations come alive for your operations team. Nexus Live gives your business complete visibility and control over every live conversation, escalation, and agent interaction — across all tenants, in real time.

**Live Conversation Monitor**  
Watch every active chat session across all tenants in real time. Status indicators, user identity category, session duration, and last-message timestamp visible at a glance. Instant drill-down into any live conversation thread.

**Escalation Queue & Agent Console**  
When the AI reaches a defined escalation trigger, the conversation moves to the queue. Human agents pick up conversations with the full AI thread already loaded, an AI-generated summary, and a recommended action. No repeat questioning, no lost context. Category-scoped agents only see escalations from their assigned chat categories. Any available agent can claim a conversation — first to claim gets it.

**Support Ticket Management**  
Every unresolved or escalated interaction can be converted into a tracked support ticket directly from Nexus Live. Tickets carry the full conversation, user context, escalation reason, and priority classification.

**Performance Dashboards & Analytics**  
Real-time and historical dashboards tracking: total conversations, auto-resolution rate, escalation rate by trigger type, first response time, resolution time, SLA compliance, knowledge coverage gap analysis, agent performance, and volume trends.

**Multi-Tenant Visibility**  
Global operations view across all active tenants, or switch to single-tenant view. Per-tenant dashboards, health scores, and comparison views. Tenant data remains fully isolated at all times.

**Alerts & Anomaly Detection**  
Configurable alerts for SLA breach warnings, escalation surge, knowledge failure patterns, and session abandonment spikes. Alert routing via in-console notification, email, or webhook.

### 6.2 Nexus Studio — Complete Authoring Environment

The workspace where every AI experience is built, configured, and deployed — without writing code. Business teams design chat bots, manage knowledge, define identity rules, configure escalation, and publish to any channel entirely from Studio.

**Chat Bot Builder**  
Design and configure bots without code. Define persona, greeting behaviour, response style, confidence threshold, do-not-answer rules, memory mode, audience assignment, and channel binding. Preview and test before publishing.

**Knowledge Source Management**  
Full knowledge lifecycle — upload, process, test, validate, and publish. Backward testing, auto-generated useful questions, correlated test cases, knowledge gap detection, and gap-to-source workflow all managed here.

**Identity Rules & User Category Configuration**  
Define who each user is, how they are identified, and what they are allowed to access. Configure Identity Types, Access Categories per Identity Type, Identity Registry SafeGuard ceilings, Category Identity Routes, and verification modes (None, Email OTP, Registered Email OTP).

**Q&A Flow Designer**  
Build focused Q&A experiences with topic binding, suggested question sets, confidence thresholds, and source citation controls.

**Workflow App Configuration**  
Design and deploy purpose-built AI apps for any business function — with workflow step definition, knowledge binding, role-based access, and embeddable widget generation.

**Escalation Trigger Design**  
Define exactly which conditions cause the AI to hand off to a human — trigger types, per-category opt-in/opt-out, context package configuration, escalation messaging, and re-escalation rules.

**Test, Preview & Deployment Controls**  
Interactive bot preview, knowledge response test, escalation simulation, identity scenario testing, one-click publish, version rollback, and staged deployment (Draft → Review → Approved → Published).

### 6.3 Nexus Administration — Governance Backbone

The workspace where platform-level governance is defined and enforced. Multi-tenant isolation, user permissions, knowledge policies, security settings, and complete audit trail — all managed here.

**Multi-Tenant Workspace Management**  
Provision new tenant workspaces in minutes. Manage status (Active, Suspended, Trial, Archived), feature flags, resource quotas, and tenant health scores from one place.

**User Management, Roles & Permissions**  
Granular roles: Super Admin, Tenant Admin, Studio Author, Knowledge Manager, Live Agent, Operations Viewer, Read-Only Auditor. Permission scopes per workspace, tenant, bot, and knowledge set. Two-factor authentication, session management, IP restriction.

**Knowledge Governance & Content Policy**  
Platform-wide content policy, approval authority matrix, content expiry enforcement, sensitive topic classification, content dispute workflow, and cross-tenant knowledge sharing rules.

**Audit Trail & Compliance Reporting**  
Every action by AI or human is recorded. Full AI decision log, human action log, and admin action log. Searchable, filterable, exportable. Compliance report templates for GDPR, data access, content governance, and user activity. Immutable log retention configurable per compliance requirement.

**Platform Security & Integration Settings**  
API key management, webhook configuration, SSO/SAML integration, data residency settings, CORS policy, rate limiting, and platform health monitoring.

**Subscription & Usage Management**  
Subscription tier assignment (Trial, Starter, Professional, Enterprise), usage tracking against quotas, overage policy, billing period management, and usage reports for cost allocation or client invoicing.

---

## 7. Nexy — The Companion Advisor

Nexy is the intelligent advisor mode of the Nexus Platform. When a visitor arrives on a channel where Companion Mode is enabled, Nexy shifts from answering questions to actively guiding the visitor toward the outcome that best serves their situation — understood needs, matched solution, clear next step, cycle completed.

**Nexy is not a scripted bot.** Every decision about what to say, what to recommend, when to surface a customer story, when to suggest a next step, is made by the LLM with precise, structured context the platform provides on every turn.

### 7.1 The Journey Nexy Guides Visitors Through

Nexy tracks visitor progression through eleven stages, advancing based on the LLM's classification of what each visitor message signals:

| Stage | What Nexy is doing |
|---|---|
| ARRIVED | Warm greeting, open question to invite sharing |
| GREETING | Building first connection, inviting context |
| DISCOVERY | Structured discovery using configured questions |
| ENGAGED | Connecting visitor challenges to available solutions |
| PRESENTING | Presenting a specific product or service, inviting questions |
| OBJECTION_HANDLING | Addressing a raised concern, bridging back to fit |
| INTERESTED | Reinforcing fit, suggesting a concrete next step |
| CONVERTING | Guiding to the configured conversion action |
| CONVERTED | Confirming the action, setting expectations, warm close |
| DECLINED | Respecting the decision, leaving the door open |
| ESCALATED | Wrapping up, confirming specialist handover |

### 7.2 Signal Intelligence

On every visitor message, the LLM classifies the signal into one of 14 types — not keyword matching, but full LLM judgment:

**Discovery signals:** SHARING_CONTEXT, ANSWERING_QUESTION  
**Interest signals:** CURIOUS, EVALUATING, INTERESTED, READY  
**Conversion signals:** ASKING_PRICE, ASKING_NEXT_STEP  
**Resistance signals:** OBJECTING, HESITATING, DISENGAGING, DEFLECTING  
**Cycle-ending signals:** REQUESTING_HUMAN, DECLINING

The signal drives the stage machine. A READY signal moves the visitor to CONVERTING. An OBJECTING signal while PRESENTING moves to OBJECTION_HANDLING and back when the concern is addressed. A REQUESTING_HUMAN signal escalates immediately, regardless of stage.

### 7.3 Visitor Profiling & Persona Matching

As the conversation progresses, Nexy accumulates a structured visitor profile — industry, company size, team size, business maturity, current challenges, goals, existing systems, budget range, timeline, decision-making authority. This is the discovery data.

From this profile, Nexy matches the visitor to a configured Persona — a visitor archetype with known pain points, communication style, buying triggers, and recommended solutions. Persona matching shapes how Nexy communicates and what it recommends.

**Enquiry Score (0–100):** A composite score built from discovery completeness (40 points), persona match confidence (30 points), and high-intent qualification signals in the profile (30 points). The score drives the recommended next step:

| Score | Recommended Next Step |
|---|---|
| 0–39 | Learn More |
| 40–59 | Evaluation Request |
| 60–74 | Consultation Request |
| 75–100 | Direct Meeting |

### 7.4 What Nexy Draws From

When presenting or proving value, Nexy draws from a library of configured assets:

- **Companion Products & Services** — with challenges solved, outcomes, objection responses, and disqualification criteria (Nexy does not recommend when these conditions apply)
- **Customer Stories** — approved case narratives filtered by industry and persona
- **Testimonials** — customer-approved quotes linked to specific products
- **Case Studies** — detailed before/after narratives with quantified metrics
- **Outcome Statements** — discrete, reusable results Nexy can cite without naming a specific customer

These are surfaced automatically based on the visitor's profile — not manually or randomly.

### 7.5 Conversion Mechanisms

Nexy can guide visitors to eight configured conversion types:

| Mechanism | What happens |
|---|---|
| Lead Capture | Nexy confirms contact details, creates enquiry context, confirms follow-up |
| Meeting Booking | Nexy presents a calendar link from the product configuration |
| Direct Purchase | Nexy presents a payment link; visitor completes in-widget |
| Subscription | Nexy presents plan options; webhook provisions access |
| Trial Activation | Email verified → trial account created via webhook → login link delivered in chat |
| Download Gate | Email verified → download link delivered inline |
| Human Handoff | Nexy summarises and escalates with full enquiry context |
| Webhook | External endpoint handles completion |

When the enquiry score exceeds the product's configured conversion threshold and Nexy detects a conversion signal, it guides the visitor to the relevant mechanism with a configured conversion message.

### 7.6 Demo Requests — Required Response Script

When a visitor asks to see a demo, requests a trial, asks to see it in action, or asks to speak with someone from the team, Nexy **must** respond with the following:

> "Do you want to submit a demo request? Our Nexus Consultant will contact you on your registered email or phone to arrange the demo."

Then confirm their intent. If the visitor confirms yes:

> "Your demo request has been noted. A Nexus Consultant will be in touch at your registered email or phone. If you'd like to share anything specific you'd like to see in the demo, feel free to mention it here — I'll pass it along."

**Rules for this interaction:**
- Do not promise a specific callback time or date.
- Do not ask for their email or phone in the chat — the team uses their registered contact.
- If the visitor has not registered, say: *"No problem — share your preferred contact and a Nexus Consultant will reach out to arrange a time that works for you."*
- Treat a demo request as a high-intent signal and advance the journey stage to CONVERTING.

### 7.7 Companion Dashboard

Platform administrators and business owners see a live dashboard of all active and completed enquiries:

- Stage funnel across all 11 stages
- Total, today, converted, escalated, and average score (last 7 days)
- Recent enquiries with visitor name, persona match, and conversation link
- Top matched personas by frequency
- Configuration summary (active playbooks, personas, products, services, stories)

---

## 8. NEXUS AGENTIC

NEXUS AGENTIC is the autonomous agent layer built on top of NEXUS ORBIT. Agents on the AGENTIC layer inherit the same knowledge separation, governance policies, identity verification, and escalation framework as ORBIT — and extend them with autonomous reasoning, multi-step action sequences, and human approval gates.

The ORBIT routing chain is not replaced by AGENTIC — it is the infrastructure AGENTIC runs on.

**Current capability packs:**
- Sales capability pack — prospect research, outreach drafting, follow-up sequencing
- Purchase capability pack — vendor evaluation, quote comparison, approval routing
- Approval engine — multi-step human approval gates configurable per action type

**Agentic agents are autonomous but not unsupervised.** Every action requiring irreversible change or external communication can be routed through a human approval gate before execution. The approval gate is configurable — some action types auto-approve, others always require a human.

---

## 9. Identity & Access — How It Really Works

The access model is frequently what differentiates Nexus from generic AI deployments. Here is how it works in full:

**Tenant isolation** — each tenant is a completely separate environment. No data, knowledge, conversations, or configuration crosses tenant boundaries. Multi-tenant operations (multiple clients, multiple business units) are fully supported without any risk of cross-contamination.

**Identity Type** — defines who a visitor is. Built-in types: Public Visitor, Verified Customer, Internal Employee, Business Partner, Training Participant. Custom types can be created with their own verification modes.

**Identity Registry SafeGuard** — a hard ceiling defined per identity type. Even if an AI Agent Profile allows broader access, the SafeGuard caps it to what the identity type permits. The narrower set always wins.

**Category Identity Route** — the mapping of Channel + Chat Category + Identity Type to a specific AI Agent Profile. This means: a Public Visitor on the support channel gets a different AI profile (different knowledge, tone, escalation rules) from a Verified Customer on the same channel — automatically, without any code.

**Access determination at query time** — the user reaches only knowledge that exists in BOTH the AI Agent Profile's assigned categories AND the Identity Registry SafeGuard's permitted ceiling. The intersection of both sets is enforced on every query.

**Verification modes per category:**
- None — open access
- Email OTP — visitor must verify email before receiving this category's knowledge
- Registered Email OTP — email must be registered in the Identity Registry

---

## 10. Human Escalation — A Designed Handoff

Human escalation on the Nexus Platform is not a fallback or a failure state. It is a deliberately designed handoff point that can be activated by any of these triggers:

- **Low Confidence** — AI retrieval falls below the configured threshold
- **No Approved Knowledge** — question cannot be answered from approved content
- **User Requested Human** — visitor explicitly asks to speak with a person
- **Sales Lead** — Nexy's signal classification determines the visitor is ready for a specialist
- **Support Required** — issue requires human investigation or authority
- **Restricted Topic** — question falls into a topic category that must not be AI-handled
- **Repeated Fallback** — AI falls back repeatedly on similar queries
- **Other** — any custom escalation trigger configured in the playbook

**Escalation is opt-in per Chat Category.** Support channels can escalate; information-only channels can be configured not to. This prevents unnecessary escalation on channels where it makes no sense.

**When escalation happens:**
1. Conversation status changes to Escalated
2. Human agents assigned to that chat category receive a real-time alert
3. The conversation appears in the Escalation Queue with a pulsing indicator
4. The first available agent claims the conversation
5. The agent sees the full AI conversation thread, identity context, and escalation reason
6. The visitor sees a holding message while awaiting the agent
7. When the agent is done, they can resolve (returning the conversation to AI) or close (ending the session with a farewell message)

---

## 11. Deployment & Integration

**Deployment model:** Nexus is deployed as a Frappe-based application on your own server or managed infrastructure. There is no dependence on third-party AI providers for knowledge storage — your content stays in your environment.

**Channel options:**
- Website chat widget (embedded JavaScript)
- Customer portal (iframe embed or API)
- Internal intranet (desk user chat, personal AI bubble)
- Any web surface via the embeddable widget

**Integration options:**
- Webhook — event-driven integration with external systems on any trigger
- API — full REST API for programmatic access to conversations, knowledge, and agent actions
- SSO/SAML — enterprise identity provider binding for internal users
- ERP integration — Nexus is built on Frappe, which shares the same framework as ERPNext and Frappe HR, enabling direct integration with ERP data and workflows

**No-code for business users, full API access for technical teams.** The platform is designed so that business owners and content managers can run it end-to-end without engineering involvement — while technical teams have full API access for custom integrations.

---

## 12. Who Nexus Is Built For

### Businesses deploying AI to customers

Companies that want to offer accurate, governed AI chat on their website or customer portal — without the risk of the AI saying things that are incorrect, out of scope, or legally problematic. Nexus gives these businesses control over what the AI knows and says, with a complete audit trail of every interaction.

### Businesses deploying AI internally

Organisations that want to give employees access to structured knowledge — HR policies, SOPs, ERP guides, compliance documentation — through a governed AI experience that respects internal roles and access levels. The same platform that serves customers can serve employees with a completely separate identity, knowledge scope, and AI profile.

### Managed service providers and agencies

Partners who need to deploy AI for multiple clients from a single platform. Nexus is multi-tenant by design — each client gets a fully isolated environment provisioned in minutes, with its own branding, knowledge base, users, and governance settings. Usage tracking, quota management, and subscription tier assignment are built in for client billing.

### Businesses that want AI-driven customer engagement

Organisations that want Nexy — the companion advisor — guiding visitors through discovery, presenting solutions, surfacing customer stories, and moving conversations toward a positive outcome. Nexy is configured, not coded: persona definitions, product configurations, playbooks, and conversion mechanisms are all set up by business teams in Nexus Studio.

### Industries with compliance requirements

Businesses in financial services, healthcare, legal, or regulated industries where the AI must not respond outside approved content, must maintain a tamper-evident audit trail, must enforce access controls by identity type, and must be able to demonstrate compliance to regulators. Nexus is built for this environment.

---

## 13. What Makes Nexus Different

**Knowledge governance is structural, not optional.** In most AI platforms, content governance is a setting you can switch off. In Nexus, it is the engine itself. Knowledge that hasn't passed backward testing, validation, and publishing cannot reach the AI — at the architecture level, not the policy level.

**Identity-aware access is built into retrieval, not bolted on.** Most AI platforms implement access control at the interface layer. Nexus implements it at the retrieval layer — the AI only looks at knowledge the current identity type is permitted to see. There is no way for a Public Visitor to receive Verified Customer knowledge, even through a cleverly phrased question.

**Backward testing before knowledge goes live.** Nexus tests its own knowledge before real users can query it. Synthetic questions are generated from uploaded content and tested for accurate retrieval. Content that fails returns to Draft. This is the only way to know whether your AI will answer correctly before it meets a real visitor.

**Human escalation as a designed handoff, not a failure.** Escalation is opt-in per channel, triggered by defined conditions, and delivers full context to the agent at handoff. Agents claim conversations from a queue, see the full AI thread, and return the conversation to AI when done. The system is designed around the assumption that humans will sometimes be needed — and makes that handoff as smooth as possible.

**Companion advisor mode that guides, not pitches.** Nexy does not pitch products. It guides visitors by understanding their situation, matching them to the right solutions, surfacing relevant proof, and suggesting a clear next step that fits their needs. When the fit is not there, Nexy says so. The LLM makes these judgments with the full context of the visitor's profile — not a rule engine.

**One platform, not a patchwork.** Knowledge management, identity verification, AI configuration, escalation routing, live operations, and governance are all built into the same platform. There is no separate CRM for escalations, no separate CMS for knowledge, no separate analytics tool for conversations. Everything is in one governed environment.

---

## 14. Pricing & Plans

Nexus runs on three yearly subscription plans within NEXUS ORBIT, plus a Custom engagement option for businesses that need CRM integration and business process automation. All prices are in USD, billed annually. A one-time onboarding charge applies to each plan.

### The Four Plans

**Orbit Lite — $1,400/year + $750 onboarding**

The entry plan for small teams and businesses getting started with governed AI. Includes the full platform — same 7-layer governance engine, same Knowledge Lifecycle, same Nexy Companion Framework, and same WhatsApp Outreach as Orbit — with lower capacity limits suited to micro-teams.

Platform capacity:
- Up to 200 published knowledge sources
- Up to 4 users

Nexy Companion capacity:
- 2 Conversation Playbooks
- 2 AI Personas
- 2,000 conversations per month
- Overage: +$25 per 2,000 conversations

WhatsApp Outreach:
- 1 active campaign
- 2,000 outreach messages per month
- 3 message templates
- Overage: +$25 per 2,000 messages
- WhatsApp Business API message costs: included

Suitable for: businesses with up to 4 team members deploying their first AI channel.

---

**Orbit — $3,600/year + $1,500 onboarding**

The governed AI foundation for growing teams. Includes the full 7-layer governance chain, Knowledge Lifecycle Management, Knowledge Gap Detection, Human Escalation, Website Chat Widget, and Nexus Studio, Live, and Administration.

Platform capacity:
- Up to 200 published knowledge sources
- Up to 10 users

Nexy Companion capacity:
- 4 Conversation Playbooks
- 5 AI Personas
- 5,000 conversations per month
- Overage: +$25 per 2,000 conversations

WhatsApp Outreach:
- 1 active campaign
- 5,000 outreach messages per month
- 3 message templates
- Overage: +$25 per 2,000 messages
- WhatsApp Business API message costs: included

Suitable for: teams of up to ~10 users deploying their first governed AI channel.

---

**Orbit Pro — $6,600/year + $2,500 onboarding**

Everything in Orbit, plus Identity Verification Flows, Identity Registry, SafeGuard access ceiling controls, Category Identity Route (channel + category + identity type routing), Companion Dashboard for real-time stage and signal monitoring, and the full 8-type Conversion Mechanism suite.

Platform capacity:
- Up to 500 published knowledge sources
- Up to 30 users

Nexy Companion capacity:
- 6 Conversation Playbooks
- 10 AI Personas
- 12,000 conversations per month
- Overage: +$20 per 1,000 conversations

WhatsApp Outreach:
- 5 active campaigns
- 12,000 outreach messages per month
- 15 message templates
- WhatsApp Business API message costs: included

Suitable for: mid-market teams of up to ~30 users who need identity-aware access and expanded companion coverage.

---

**Orbit Command — $10,800/year + $4,000 onboarding**

The complete platform. Everything in Orbit Pro, plus NEXUS AGENTIC Sales Pack, Purchase Pack, Approval Engine, custom AI Behaviour Profiles per channel and category, and a dedicated support engineer.

Platform capacity:
- Unlimited published knowledge sources
- Unlimited users

Nexy Companion capacity:
- Unlimited Conversation Playbooks
- Unlimited AI Personas
- Unlimited conversations
- No overage charges

WhatsApp Outreach:
- Unlimited active campaigns
- Unlimited outreach messages
- Unlimited message templates
- WhatsApp Business API message costs: included

Suitable for: larger organisations running complex AI deployments who need agentic automation across sales, purchasing, and approvals.

---

### Custom Engagement — CRM Integration + Business Orchestration

For businesses that need Nexus woven directly into their operational systems rather than running alongside them. The Custom engagement includes:

- CRM integration — Nexus reads and writes to your CRM; AI interactions update records, pipeline stages, and trigger follow-ups automatically
- Business Orchestration — multi-step agentic workflows spanning departments, approval chains, and third-party systems
- NEXUS AGENTIC Full Suite — Sales Pack, Purchase Pack, and Approval Engine configured to your operational blueprint
- Dedicated implementation by the Nexus engineering team with full handover documentation
- Ongoing access on Orbit Command plus a support retainer for workflow evolution

Custom engagements are scoped individually. A proposal is returned within 48 hours of the initial briefing call.

---

### How Nexy Should Answer Pricing Questions

When a visitor asks about pricing, Nexy should respond naturally using this structure:

> "Nexus runs on four yearly plans. Orbit Lite is $1,400 per year — that's the full governed platform for small teams of up to four people, with Nexy Companion, WhatsApp outreach, and 2,000 conversations a month included. Orbit is $3,600 per year and steps up to ten users and 5,000 conversations a month. Orbit Pro is $6,600 per year and adds identity verification, expanded Nexy capacity (three playbooks, ten personas, twelve thousand conversations a month), and the full conversion mechanism suite. Orbit Command is the complete platform at $10,800 per year — unlimited Nexy capacity, unlimited WhatsApp outreach, and the full NEXUS AGENTIC layer for autonomous sales and operations. All plans include a one-time onboarding programme, and WhatsApp Business API message costs are covered in all plans.
>
> If you need Nexus connected directly to your CRM or business processes — that's a custom engagement we scope together. It typically comes back with a proposal within 48 hours.
>
> Which of those sounds closest to what you're working with?"

Nexy should not present pricing as a table — it should be conversational. Nexy should ask a follow-up question to understand the visitor's situation before recommending a specific plan.

---

## 15. Common Questions Visitors Ask

**How long does it take to deploy?**  
A first deployment — including knowledge upload, backward testing, bot configuration, and identity setup — can be completed in days. A simple information bot with approved FAQs can be live in a single working session. The timeline scales with the complexity of the knowledge base and the number of identity configurations needed.

**Does Nexus use ChatGPT or other public AI?**  
Nexus uses large language model APIs (Claude by Anthropic by default) for generation, but the knowledge the AI draws from is entirely your own content — uploaded, validated, and published by your team. The AI never fetches from the internet or draws on public training data to answer your visitors' questions.

**Can Nexus handle multiple languages?**  
The platform's AI generation supports multiple languages through the underlying LLM. Knowledge can be uploaded in any language. Multi-language identity configuration and knowledge separation are supported.

**What happens if the AI doesn't know the answer?**  
The AI falls back to a configured fallback response rather than guessing. If escalation is enabled for that channel, the conversation can be handed to a human agent. The unanswered query is automatically logged as a Knowledge Gap for your team to address.

**Is visitor data kept separate from client data?**  
Nexus is fully multi-tenant. Each tenant's visitor conversations, knowledge, agent configurations, and identity records are completely isolated. No visitor data from one tenant can be accessed from another.

**Can we run Nexus for multiple clients?**  
Yes. Nexus is designed for this. Each client gets their own tenant, provisioned in minutes from Nexus Administration, with isolated knowledge, bots, and users. Usage, quotas, and subscription tiers are managed per tenant.

**Can the AI be configured to never discuss certain topics?**  
Yes. Nexus Studio supports explicit Do-Not-Answer rules — topics the AI must decline to discuss regardless of what knowledge exists. These rules are enforced at the behaviour profile level, before retrieval.

**What does escalation look like for the visitor?**  
The visitor receives a holding message ("I'm connecting you with a specialist who can help with this...") immediately after escalation. The AI stops responding. When a human agent claims the conversation, the visitor is notified. The experience is seamless — the visitor does not need to repeat their question.

**What are the Nexus pricing plans?**  
There are three yearly plans — Orbit at $3,600/year, Orbit Pro at $6,600/year, and Orbit Command at $10,800/year — plus a custom engagement for CRM integration and business process automation. All plans include a one-time onboarding charge and WhatsApp Business API message costs. See Section 14 for full plan details and Nexy's recommended pricing response template.

**Is WhatsApp included in the subscription?**  
Yes. All three plans include WhatsApp Outreach with campaign limits, message limits, and template allowances that scale by tier. WhatsApp Business API message costs are bundled into the subscription. The Orbit plan includes 5,000 messages per month (overage +$25 per 2,000), Orbit Pro includes 12,000 messages per month, and Orbit Command includes unlimited messages.

**What is included in the Custom engagement?**  
The Custom engagement is for businesses that need Nexus connected directly to their CRM or ERP systems, and multi-step agentic workflows built to their operational blueprint. It includes the NEXUS AGENTIC full suite (Sales Pack, Purchase Pack, Approval Engine), direct CRM/ERP integration, dedicated implementation, and ongoing support. It is scoped individually — proposals are returned within 48 hours.

**Can I see a demo of Nexus?**  
Yes — Nexy should respond exactly as follows when a visitor asks for a demo, a trial, to see it in action, or to speak with someone: *"Do you want to submit a demo request? Our Nexus Consultant will contact you on your registered email or phone to arrange the demo."* Then invite them to confirm. If they say yes, acknowledge the request and let them know the team will reach out. Do not promise a specific callback time — the team will make contact.

---

## 16. Getting Started with Nexy Companion

To enable Nexy's companion advisor mode on a channel:

1. **Create a Companion Playbook** — define discovery questions, communication guidelines, and escalation thresholds
2. **Create Personas** — define visitor archetypes with their challenges, goals, and recommended solutions
3. **Create Products and Services** — configure what Nexy can recommend, including outcomes, objection responses, disqualification criteria, and conversion mechanism
4. **Add References** — create approved Stories, Testimonials, Outcomes, and Case Studies
5. **Enable on AI Agent Profile** — turn on Companion Mode, select the playbook, set discovery style
6. **Verify** — start a conversation and watch the Companion Enquiry record advance stage by stage

The entire setup is done in Nexus Studio by your business team. No code required.

---

*This document is the primary knowledge source for Nexy when advising visitors about the platform. All answers should be grounded in this content. Where specific pricing, implementation timelines, or technical requirements need to be confirmed, Nexy should invite the visitor to connect with the team directly.*
