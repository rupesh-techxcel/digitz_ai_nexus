# Nexus Platform — Companion Content Pack
### Value-First Documentation for Nexy Companion Configuration

> This document is the canonical source for filling in all Nexy Companion DocTypes for Nexus Platform's own website chat.
> It is written entirely from the visitor's perspective — the value they receive, the problems they solve, and the decisions they face.
> Never use the words "selling" or "sales" in AI interactions — use "advising", "guiding", "exploring fit", "recommending".

---

## Part 1 — Platform Value Narrative

### What Nexus Is (in one paragraph for a visitor)

Nexus is a governed AI platform that lets your business put its actual knowledge — your documents, processes, policies, and expertise — into an AI that talks to your visitors and team. Unlike generic AI tools, Nexus enforces who can ask what, ensures every answer is grounded in content you approved, knows when to hand a conversation to a real person, and tells you exactly what visitors asked that your AI couldn't answer. It is designed for businesses that cannot afford AI that makes things up.

### The Core Problem Nexus Solves

Most businesses exploring AI chat hit the same wall: generic AI tools are confident and fast but dangerously unpredictable — they hallucinate, they share confidential information indiscriminately, they can't be scoped to what your business actually knows, and they offer no path to a human when the visitor genuinely needs one.

Nexus exists to close that gap. Every response is retrieval-grounded. Every knowledge asset goes through an approval workflow before the AI can use it. Every visitor's access level determines what they can ask. And when the AI isn't the right answer, a human agent steps in — without the visitor having to start over.

---

## Part 2 — Products (Nexus Companion Product records)

---

### PRODUCT 1 — Nexus Live AI Chat

**Category:** Conversational AI  
**Target:** Any business wanting an AI-powered chat on their website, portal, or application

#### What it does for the visitor's business
Deploys an AI chat assistant on any channel — website, internal portal, customer portal, support surface — that answers visitor questions using only your approved, governed knowledge. The AI never invents facts. It knows when it doesn't know, tells the visitor honestly, and either records the gap for your team to fill or offers a follow-up.

#### Key capabilities (value framing)
- **Always-on, zero-fatigue responses** — visitors get answered at any hour without a support team member involved
- **Grounded answers only** — every response is traced back to a knowledge chunk you approved; no hallucination risk
- **Channel awareness** — one platform, multiple surfaces: your website, your internal tools, a support widget, a mobile app
- **Category-based visitor routing** — visitors self-select the topic they need help with; the AI adapts to that context instantly
- **Persona continuity** — the AI remembers the conversation and builds on it, no repetitive re-explaining
- **Gap detection built in** — every question the AI couldn't answer is recorded as a knowledge gap, giving your team a precise list of what to write next

#### Features
- Embeddable chat widget (copy-paste installation)
- Multi-channel: website, internal desk, API
- Configurable greeting, tone, fallback message per AI profile
- Response modes: concise, detailed, structured, bullet format
- Visitor feedback rating after each session
- Full conversation log with confidence scores
- FAQ pre-built answers per topic category

#### Qualification signals (visitor is a good fit when)
- Currently using a generic chatbot that gives inconsistent or inaccurate answers
- Has a support team spending significant time on repetitive questions
- Has documents, policies, or knowledge that the team knows but visitors can't easily find
- Runs a 24/7 or international operation where response time matters
- Has been burned by an AI hallucinating something they didn't say

#### Challenges solved
- "Our current chatbot just pulls from Google or makes things up"
- "We don't have the budget to staff 24/7 live support"
- "Visitors can't find answers on our website and we lose them"
- "We don't know what questions our visitors are actually asking"

#### Typical outcomes
- 60–80% reduction in repeat support queries handled by the team
- Sub-second response to common visitor questions
- Complete audit trail of every conversation with confidence evidence
- Weekly knowledge gap report to fill content systematically

#### Next step options
- Request a live demo on your own content
- Start a free trial with a sample knowledge base
- Book a configuration workshop

---

### PRODUCT 2 — Nexus Knowledge Studio

**Category:** Knowledge Management & Governance  
**Target:** Businesses that want AI to draw on their internal documents, policies, or expertise — governed and auditable

#### What it does for the visitor's business
Nexus Knowledge Studio is the content layer behind the AI. You import your documents — PDFs, Word files, pasted text, or manually authored content — and the platform processes them into searchable, retrievable knowledge chunks. You review and approve what goes in. You control what each audience can access. The AI only uses what you explicitly approved.

#### Key capabilities (value framing)
- **Bring your own knowledge** — any document format, any source; the platform handles chunking and indexing
- **Approval workflow** — nothing enters the AI's knowledge base without being reviewed; prevents accidental exposure of drafts or outdated content
- **Access-layered content** — a Customer can ask about your public offer; a verified Partner gets pricing details; an internal Employee gets process documentation — same platform, completely separate knowledge access
- **Knowledge gap-driven content creation** — the platform tells you exactly what visitors asked that no knowledge asset could answer; create new content to fill those gaps directly from the gap record
- **Retrieval quality testing** — run regression tests against specific queries to validate that retrieval stays accurate as you add content
- **Context-aware search** — hybrid vector + keyword search ensures relevant answers even when visitors phrase questions differently

#### Features
- Source types: PDF, DOCX, TXT, manual text, knowledge unit authoring
- Semantic chunking with configurable overlap
- Embedding generation (OpenAI or pluggable provider)
- Hybrid retrieval: BM25 keyword + vector similarity + cross-encoder reranking
- Approval status: Draft → Review → Published → Archived
- Access policies with sensitivity levels and role-based access
- Knowledge profiles: named sets of allowed access categories
- Knowledge context summaries for source-level injection
- Knowledge gap review workflow with LLM-assisted relevance assessment
- Test cases and test runs for retrieval regression testing
- Visitor email follow-up when a gap is later resolved

#### Qualification signals
- Has existing internal documentation not yet accessible to visitors or the AI
- Worried about AI sharing the wrong content with the wrong audience
- Wants to know what content gaps exist in their knowledge base
- Has multiple audiences (public, partners, employees) needing different access levels
- Regularly updates content and needs to ensure AI stays current

#### Challenges solved
- "We have hundreds of PDFs but no one reads them"
- "We can't let an AI access everything — some content is confidential"
- "We keep getting asked questions we know we've documented somewhere"
- "We don't know if the AI is actually using our latest policy or an old one"

#### Typical outcomes
- Single organised knowledge repository powering the AI, support team, and internal search
- Documented content coverage with automatic gap identification
- Access-separated AI: public visitors, verified customers, and internal staff all using the same platform but with appropriate knowledge boundaries
- Zero manual content routing — policy determines access, not configuration per question

#### Next step options
- See a live document ingestion demo
- Explore what access governance looks like for your team structure
- Start a pilot with your top 20 documents

---

### PRODUCT 3 — Nexus Companion (Nexy Advisor Mode)

**Category:** Conversational Business Advisory  
**Target:** Businesses that want their website AI to actively guide visitors toward the right solution — without pushy engagement

#### What it does for the visitor's business
Nexus Companion activates Nexy's advisory layer on top of the live AI chat. Instead of simply answering questions, Nexy guides visitors through a discovery journey: understanding their situation, matching them to a relevant visitor profile (persona), surfacing contextual product and service information, sharing relevant customer stories, and identifying when they are ready for a human conversation. Every interaction is grounded in your approved knowledge — Nexy never invents.

#### Key capabilities (value framing)
- **Guided discovery** — Nexy asks contextual questions to understand the visitor's industry, team size, challenges, and goals, building a qualification picture naturally through conversation
- **Persona matching** — as the conversation progresses, Nexy automatically identifies which of your defined visitor archetypes the visitor matches, and adapts tone and recommendations accordingly
- **Contextual product guidance** — at the right moment in the journey, Nexy surfaces the most relevant product or service information for that specific visitor profile — not a generic brochure dump
- **Reference-backed trust-building** — Nexy cites relevant customer stories, testimonials, outcomes, and case studies in context, giving visitors evidence grounded in real experience
- **Journey stage tracking** — every conversation is tracked through stages (Arrived → Greeting → Discovery → Engaged → Solution Fit → Interested → Qualified → Escalated), giving your team visibility into where visitors are in their decision journey
- **Automatic qualification scoring** — Nexy continuously scores the visitor (0–100) based on discovery completeness, persona confidence, and qualification signals; when the score crosses your configured threshold, a human agent is automatically notified
- **Smart escalation** — configured trigger keywords or score thresholds automatically route the visitor to a human, complete with the full discovery context already collected

#### Features
- Companion Playbooks: configure discovery questions, communication guidelines, objection responses, next-step options, and escalation thresholds per tenant
- Persona library: define visitor archetypes by industry, company size, maturity, challenges, and goals
- Product & service intelligence profiles: features, benefits, outcomes, objection responses, qualification criteria
- Reference library: stories, testimonials, case studies, outcome statements — matched contextually by industry and persona
- Enquiry pipeline: auto-created qualification records per companion conversation
- Companion Dashboard: live funnel view, stage counts, top personas, enquiry scores, escalation flags
- Journey stage machine: 8 stages with automatic advancement logic
- Composite enquiry score: discovery completeness (40pts) + persona confidence (30pts) + qualification signals (30pts)

#### Qualification signals
- Currently has no structured way to qualify website visitors before handing them to the team
- Has defined customer types or ideal customer profiles but no way to apply them in chat
- Wants to reduce unqualified meeting requests
- Has customer success stories that aren't being used in the awareness/evaluation phase
- Team spends time repeating the same discovery questions in first calls

#### Challenges solved
- "Visitors come to our website, browse, and leave — we have no idea who they were or what they needed"
- "Our team wastes time on discovery calls with people who weren't a good fit"
- "We have great customer success stories but they never reach visitors at the right moment"
- "We don't know if a visitor is ready to talk to us or just curious"

#### Typical outcomes
- Structured qualification data collected before the first human conversation
- Reduction in low-fit meeting requests
- Visitor journey visibility: know which stage each visitor reached and why
- Reference content surfaced contextually — not left in a case study library no one finds

#### Next step options
- See a Companion conversation flow demo
- Review the Companion Dashboard with sample data
- Configure a pilot playbook for your primary visitor type

---

### PRODUCT 4 — Nexus Human Escalation

**Category:** AI-to-Human Handoff  
**Target:** Businesses that want AI to handle the majority of interactions but need a seamless path to a real person when it matters

#### What it does for the visitor's business
Nexus Human Escalation bridges the AI and the human support or advisory team. When a visitor needs a real person — because they asked for one, because the AI couldn't answer with sufficient confidence, or because the Companion detected a qualified buying signal — the conversation is handed to a human agent without the visitor having to repeat themselves. The agent sees the full conversation history, the visitor's identity context, and all collected qualification data.

#### Key capabilities (value framing)
- **Zero-repeat handoff** — the human agent opens the conversation and already has full context; the visitor continues, not restarts
- **Agent-specific view** — human agents only see conversations in their assigned categories; no irrelevant noise
- **First-claim assignment** — when an escalation appears, any eligible agent can claim it; the system prevents double-handling
- **Real-time escalation alerts** — agents receive instant browser notifications when a new escalation arrives in their category
- **Full history in the agent panel** — chat panel shows every message with clear visual separation between AI responses and human agent messages
- **Resolve or close** — agents can resolve the escalation (returning the visitor to AI assistance) or close the conversation with a farewell

#### Features
- Role-based access: `Nexus Live Agent` role gates agent console access
- Category-scoped agents: each agent handles only their configured categories
- Escalation reasons: Low Confidence, No Approved Knowledge, User Requested Human, Support Required, Restricted Topic, Repeated Fallback
- Real-time escalation panel with claim/release/resolve/close controls
- Visitor conversation held with a holding message while awaiting agent
- Escalation rules: configurable triggers per profile and per category
- Human agent performance snapshots (conversations handled, response time, resolution rate)

#### Qualification signals
- Has a support or advisory team that handles escalations manually today
- Visitors currently drop off when the chatbot fails them
- Wants one platform for both AI and human interaction, not two separate tools
- Needs an audit trail of when and why escalations occurred

#### Challenges solved
- "Visitors give up when the bot can't help and there's no way to reach a person"
- "Our agents spend time figuring out what the visitor already explained to the bot"
- "We have no visibility into escalation volume or agent response time"

#### Typical outcomes
- Zero context loss at handoff — agent has full conversation and qualification data
- Measurable escalation rate with reason classification
- Human team focused on high-value interactions; AI handles the volume

#### Next step options
- See a live escalation demo
- Discuss how escalation categories align to your team structure
- Review agent performance reporting

---

### PRODUCT 5 — Nexus Platform (Enterprise Multi-Tenant)

**Category:** Platform Infrastructure  
**Target:** Agencies, SaaS businesses, enterprises with multiple brands or departments needing isolated AI environments

#### What it does for the visitor's business
Nexus is built multi-tenant from the foundation. Every tenant — a brand, a department, a client — operates with completely isolated knowledge, access policies, AI profiles, conversations, and analytics. One platform installation can serve multiple businesses or business units, each with their own content, their own visitor profiles, and their own AI behaviour, with no cross-contamination.

#### Key capabilities (value framing)
- **Tenant-isolated architecture** — every entity (knowledge, conversation, escalation, visitor record) is scoped to a tenant; no data bleeds between tenants
- **Per-tenant LLM configuration** — each tenant can use a different LLM provider, model, or embedding configuration
- **Access governance at every layer** — access policies, knowledge profiles, identity registries, and safe guards all cascade down from tenant to visitor interaction
- **Pluggable identity** — integrate with your existing identity provider; verified identities unlock richer knowledge access
- **Configurable at every level** — global defaults, tenant overrides, AI profile overrides, and per-conversation overrides cascade in priority order
- **Agency-ready** — one platform can serve multiple clients; each client's Nexus environment is invisible to others

#### Features
- Multi-tenant data isolation (all queries filtered by tenant)
- Per-tenant: Knowledge Sources, AI Agent Profiles, Chat Categories, Channels, Escalation Rules, Analytics
- Nexus Tenant and Nexus Business Unit hierarchy
- LLM provider configuration per tenant
- Admin workspace with full governance visibility
- API-first: authenticated API endpoints for custom integrations
- Frappe-native: roles, permissions, workflows, and audit log inherited from Frappe framework

#### Qualification signals
- Agency managing AI chat for multiple clients
- Enterprise with multiple departments needing separate AI contexts
- SaaS business wanting to offer branded AI chat to their own customers
- Compliance-sensitive organisation needing documented access governance

---

## Part 3 — Services (Nexus Companion Service records)

---

### SERVICE 1 — Platform Onboarding & Setup

**What's included:**
Initial tenant configuration, LLM provider setup, first AI Agent Profile configuration, first Chat Category and Channel setup, widget installation support, and first Knowledge Source ingestion walkthrough.

**Outcome:** Platform is live with a functional AI chat responding to visitor questions within your first knowledge base.

**Typical duration:** 1–2 weeks

**Who it suits:** Businesses deploying Nexus for the first time.

---

### SERVICE 2 — Knowledge Migration & Structuring

**What's included:**
Audit of existing documentation (PDFs, Word files, website content, policies), content structuring into Knowledge Sources and Units, chunk strategy review, access policy mapping to content sensitivity, and first retrieval quality test run.

**Outcome:** Existing knowledge base is imported, approved, and retrievable by the AI within the appropriate access boundaries.

**Typical duration:** 2–4 weeks depending on content volume.

**Who it suits:** Businesses with existing documentation wanting it accessible through AI without building from scratch.

---

### SERVICE 3 — Companion Playbook Configuration

**What's included:**
Discovery interview to define visitor personas, playbook drafting (discovery questions, communication guidelines, objection responses, next-step options), persona configuration, product and service intelligence profile creation, reference library population (stories, testimonials, outcomes), escalation threshold calibration, and Companion Dashboard setup.

**Outcome:** Nexy is configured as a knowledgeable business advisor for your specific visitor types, with a full discovery and qualification flow from first message to human handoff.

**Typical duration:** 1 week (workshop-based)

**Who it suits:** Businesses enabling Companion mode on their Nexus Live deployment.

---

### SERVICE 4 — Ongoing Platform Management

**What's included:**
Monthly knowledge gap review and content creation, AI profile tuning based on conversation analytics, escalation rule optimisation, and knowledge retrieval quality spot checks.

**Outcome:** The platform stays current with your business as it evolves; knowledge gaps are closed systematically; AI quality improves over time.

**Who it suits:** Businesses without internal capacity to manage the platform post-launch.

---

## Part 4 — Visitor Personas (Nexus Companion Persona records)

---

### PERSONA 1 — The Scaling Founder

**Industry:** Technology, Professional Services, E-Commerce, B2B SaaS  
**Customer Type:** B2B  
**Company Size:** SME (10–50 people)  
**Business Maturity:** Growing to Scaling

**Challenges:**
- Support team is overwhelmed with repetitive questions as the customer base grows
- Can't afford to hire more support staff; need to automate without sacrificing quality
- Has tried generic chatbots that gave wrong answers and damaged trust
- Has lots of internal knowledge (documents, processes) but it's not accessible to visitors

**Pain Points:**
- Time wasted by founders and senior team on questions that should be self-served
- No visibility into what visitors are asking or why they leave without converting
- Worried AI will say something factually wrong or embarrassing

**Goals:**
- Reduce repetitive support load by 70%+ without hiring
- Have a professional, knowledgeable AI presence 24/7
- Know exactly what knowledge gaps exist so content can be prioritised
- Hand qualified visitors to the team with context already collected

**Buying Triggers:**
- Recent bad experience with a generic AI tool
- About to hire a support person (AI as an alternative)
- Launching a new product or market and expecting inbound volume
- Just raised funding, now scaling systems

**Common Objections:**
- "Will it actually answer correctly?" → Address with grounded retrieval and approval workflow
- "We're too small for a platform like this" → Address with fast onboarding and SME pricing
- "We've tried chatbots before and they disappointed us" → Address with knowledge grounding and gap detection

**Communication Style:**
Direct, evidence-based. Skip the category buzzwords. Show real outcomes and honest product scope. Respect their time — they've heard pitches before.

**Recommended Messaging:**
Lead with knowledge grounding (not hallucination). Show the gap detection feature early — it resonates strongly with founders who know they have content blind spots. Offer a fast path to a working demo on their own content.

**Recommended Products:** Nexus Live AI Chat, Nexus Knowledge Studio, Platform Onboarding Service  
**Escalation when:** Asks about pricing, mentions team size specifically, or asks "how quickly can we get started?"

---

### PERSONA 2 — The Customer Experience Manager

**Industry:** Financial Services, Insurance, Healthcare, Hospitality, E-Commerce  
**Customer Type:** B2C or B2B  
**Company Size:** Mid-Market (50–500 people)  
**Business Maturity:** Established

**Challenges:**
- Support team handling high volume of repetitive tier-1 queries
- CSAT scores affected by slow response times, especially outside business hours
- Inconsistent answers from different support agents
- Escalation rate too high — AI tools keep sending everything to humans

**Pain Points:**
- No single source of truth for support agents (they answer from memory)
- AI tools that hand off too aggressively — no real reduction in support load
- Cannot let AI access sensitive customer account data
- Management pressure to reduce cost per contact

**Goals:**
- Deflect 60%+ of tier-1 queries to AI without sacrificing quality
- Ensure AI only accesses and shares content appropriate for each customer type
- Seamless handoff to agents when AI genuinely can't help — not for every question
- Visibility into what's being asked vs. what AI can answer

**Buying Triggers:**
- Support team headcount freeze
- New regulatory requirement for documented knowledge governance
- CSAT score drop attributed to support quality
- Planning a new self-service portal

**Common Objections:**
- "We have compliance requirements around what data the AI can access" → Address with access governance and policy layering
- "Our previous AI handed off too much" → Address with configurable escalation thresholds and confidence tuning
- "We need it to integrate with our CRM" → Address with API-first architecture

**Communication Style:**
Process-oriented. Wants to understand the workflow, not just the feature list. Respond to compliance concerns directly. Show governance and audit trail early.

**Recommended Products:** Nexus Live AI Chat, Nexus Knowledge Studio, Nexus Human Escalation  
**Escalation when:** Mentions compliance, integration requirements, or team headcount numbers.

---

### PERSONA 3 — The Technical Evaluator

**Industry:** Any  
**Customer Type:** B2B  
**Company Size:** Mid-Market to Enterprise  
**Business Maturity:** Established to Scaling

**Challenges:**
- Evaluating AI platforms and needs to understand the architecture before recommending
- Concerned about data sovereignty, security, and integration complexity
- Previous vendors couldn't explain how the AI actually works
- Needs to understand how it fits with existing infrastructure

**Pain Points:**
- Black-box AI tools with no explainability
- Vendor lock-in on proprietary embeddings or models
- Integration effort underestimated by vendors
- No clear answer on where data is stored and processed

**Goals:**
- Understand the technical architecture before making a recommendation
- Know what integrations exist (API, webhooks, SSO)
- Confirm the embedding/LLM is pluggable (not vendor-locked)
- Evaluate the access governance model against their security requirements

**Buying Triggers:**
- Business stakeholder has asked them to evaluate AI chat options
- Existing tool contract is expiring
- Security audit has flagged current AI tool

**Common Objections:**
- "We use Azure OpenAI — does it support that?" → Yes, pluggable LLM providers per tenant
- "Where is the data?" → Self-hosted Frappe installation; data sovereignty under your control
- "What's the integration surface?" → REST API, whitelisted endpoints, webhook-ready event system

**Communication Style:**
Technical, specific, low on marketing language. Respond with architecture facts, not benefits. They will appreciate being told what the platform does NOT do. Link to documentation or offer a technical deep-dive call.

**Recommended Products:** Nexus Platform (Enterprise), Nexus Knowledge Studio  
**Escalation when:** Asks about specific integration points, security model, or data residency.

---

### PERSONA 4 — The Operations or Process Owner

**Industry:** Manufacturing, Logistics, Professional Services, Education  
**Customer Type:** B2B  
**Company Size:** SME to Mid-Market  
**Business Maturity:** Established

**Challenges:**
- Internal knowledge is locked in documents and the heads of experienced staff
- New staff onboarding takes too long because knowledge isn't self-serve
- Process documentation exists but isn't accessible when staff need it
- Inconsistency in how policies are applied because staff interpret documents differently

**Pain Points:**
- Knowledge walks out the door when experienced staff leave
- Training costs driven by inability to self-serve process knowledge
- Time wasted by managers answering questions that are already documented

**Goals:**
- Internal AI that answers process and policy questions accurately
- Make institutional knowledge accessible to all staff, not just those who know who to ask
- Reduce onboarding time and increase consistency

**Buying Triggers:**
- Recent staff departure created a knowledge gap
- Scaling team and onboarding costs are rising
- Planning a digital transformation or ERP rollout

**Common Objections:**
- "Our staff won't trust an AI to answer process questions" → Address with approval workflow; staff know what was approved
- "We'd need to keep it internal only" → Internal channel configuration with identity verification

**Communication Style:**
Practical. Show how the knowledge lifecycle works — from document to approved chunk to AI answer. The approval workflow is a trust-builder for this persona.

**Recommended Products:** Nexus Knowledge Studio, Nexus Live AI Chat (internal channel)  
**Escalation when:** Mentions staff count, specific departments, or asks about internal deployment.

---

### PERSONA 5 — The Agency or Platform Builder

**Industry:** Digital Agency, SaaS, Consultancy  
**Customer Type:** B2B  
**Company Size:** Any  
**Business Maturity:** Any

**Challenges:**
- Building or reselling AI chat solutions for multiple clients
- Needs one platform that can serve multiple clients without cross-contamination
- Each client has different content, branding, and access rules
- Managing multiple separate AI tools is unsustainable

**Pain Points:**
- Deploying a separate AI infrastructure for each client is expensive
- Generic chatbot resale products don't allow enough configuration
- Client confidentiality between tenants is non-negotiable

**Goals:**
- One platform, multiple isolated client environments
- Branded AI chat per client
- Predictable per-tenant configuration model
- White-label or API-first delivery to embed in their own product

**Buying Triggers:**
- Client is asking for an AI chat capability
- Evaluating a platform to standardise their AI service offering
- Current tooling doesn't support multi-tenant isolation

**Communication Style:**
Commercial and architectural. They want to understand the business model as much as the technical model. Show the tenant isolation architecture and the per-tenant configuration surface early.

**Recommended Products:** Nexus Platform (Enterprise), Nexus Knowledge Studio  
**Escalation when:** Mentions number of clients, resale intent, or white-label requirements.

---

## Part 5 — Companion Playbook (Configuration Reference)

### Playbook Name: Nexus Platform Advisor Playbook

**Tenant:** (your Nexus Platform tenant)  
**Description:** Discovery and advisory playbook for visitors exploring the Nexus AI platform. Guides visitors from initial curiosity through problem discovery, product fit assessment, and qualified handoff to the Nexus team.

---

### Discovery Questions

Use these questions naturally across the conversation — never fire all of them at once. Pick contextually.

**Current situation:**
- What does your current visitor engagement or support setup look like — do you have any AI or chatbot tools running today?
- Who typically handles inbound questions from visitors or customers in your business?
- Roughly how many support or enquiry interactions does your team handle per week?

**Pain and motivation:**
- What prompted you to look at AI chat solutions right now?
- What's not working well with what you have today?
- Has inaccurate or unhelpful AI output caused a problem for your business?

**Fit discovery:**
- What type of knowledge would you want the AI to draw on — internal documents, product information, policies?
- Do you have different audiences who should see different information — public visitors vs. logged-in customers vs. internal staff?
- Is there a human support or advisory team that would need to step in for complex conversations?

**Readiness:**
- Are you evaluating this for a specific project or timeline?
- Who else in your organisation would be involved in a decision like this?
- Have you looked at other platforms in this category?

---

### Communication Guidelines

1. **Ground everything in evidence.** Never make claims the knowledge base doesn't support. If you don't have specifics, say so and offer to connect the visitor with the team.
2. **Listen more than you guide.** Understand the visitor's situation before recommending anything. The first 2–3 exchanges should be discovery, not product pitch.
3. **Be honest about fit.** If the visitor's situation doesn't match what Nexus does well, say so. A well-qualified conversation is worth more than a misleading one.
4. **Use concrete outcomes.** Avoid vague benefit language. Prefer "reduces tier-1 support volume" to "improves efficiency".
5. **Never invent numbers.** Do not fabricate pricing, timelines, or outcome percentages unless they appear in approved knowledge.
6. **Surface references contextually.** When a visitor describes a challenge, surface the most relevant customer story or outcome — but only if it genuinely matches.
7. **Language rules:** Never use "sales", "selling", or "sell". Use: advising, guiding, exploring fit, recommending, helping you decide.

---

### Objection Responses

**"We've tried chatbots before and they didn't work."**
That's one of the most common reasons businesses come to Nexus. Most chatbot tools either use scripted flows that break on anything unexpected, or they use general AI that makes up answers. Nexus takes a different approach: every answer the AI gives is traced back to a knowledge chunk your team explicitly approved. The AI can only say what's in your approved knowledge base. And when it can't answer, it records the gap so your team knows exactly what to add. Would it help to walk through a quick demo with some of your actual content?

**"We're not sure if our content is ready to put into an AI."**
That's a very common starting point. The Nexus Knowledge Studio is specifically designed for businesses whose content is scattered — PDFs, Word docs, internal wikis, policies. You bring what you have; the platform processes it, lets you review the chunks, and only activates content you approve. Many businesses start with their top 20 most-asked questions and build from there. Would you like to talk about what a realistic first content set looks like for your situation?

**"How do we ensure the AI doesn't share confidential information?"**
This is built into the architecture, not bolted on. Every piece of content in Nexus has an access policy. You define what roles or identity types can access what content. A public website visitor sees the public knowledge layer. A verified customer sees the customer layer. An internal staff member sees the internal layer. The AI enforces this at query time — there's no manual filtering required.

**"What does this cost?"**
I'd want to make sure we're talking about the right configuration before quoting anything — the setup varies quite a bit depending on content volume, number of tenants, and whether you need the Companion advisory layer. What I can do is connect you with the team who can put together a specific scope based on what we've discussed. Would that work?

---

### Escalation Threshold

**Score threshold:** 65 (out of 100)  
**Escalate immediately when visitor says any of these (trigger keywords):**
- "pricing", "price", "cost", "how much"
- "demo", "demonstration", "see it live"
- "pilot", "trial", "get started", "next step"
- "meet", "call", "talk to someone", "speak to your team"
- "proposal", "quote"

---

### Next Step Options

1. **Request a live demo** — "I can flag you to the Nexus team for a live demo on your content — usually 30 minutes. Would that work?"
2. **Documentation deep-dive** — "I can point you to the technical architecture documentation if you'd like to evaluate the platform in more detail before talking to the team."
3. **Content audit conversation** — "The team can do a quick content audit call — you share what you have, they tell you how long onboarding would take. No commitment required."
4. **Workshop booking** — "For teams wanting to configure the Companion Playbook, there's a structured workshop. I can connect you with the team to schedule one."

---

## Part 6 — Reference Library

### STORY 1 — Internal Knowledge Made Accessible

**Industry:** Professional Services  
**Challenge:** A growing consultancy had years of process documentation, proposal templates, and methodology guides scattered across SharePoint folders. New staff spent weeks in onboarding just finding relevant documents, and senior staff were constantly interrupted with "where is the…?" questions.  
**Solution:** Nexus Knowledge Studio was used to ingest and approve ~200 documents. An internal AI chat channel was configured with identity verification so only staff could query it. The AI was trained on the methodology guides and process documentation.  
**Outcomes:** New staff self-served answers during onboarding without needing a senior colleague. Time spent by managers on routine process questions dropped significantly in the first month. The gap detection report surfaced 14 questions staff were asking that had no documented answer — turning those into new knowledge assets.  
**Linked Personas:** Operations/Process Owner, Scaling Founder

---

### STORY 2 — Support Deflection Without Sacrificing Quality

**Industry:** E-Commerce / B2C  
**Challenge:** A mid-size e-commerce operation was handling ~300 repetitive support queries per week — returns policy, delivery times, product specifications — through a human support team. Costs were high and response times inconsistent outside business hours.  
**Solution:** Nexus Live AI Chat was deployed with a product knowledge base covering FAQs, policies, and product specifications. The AI was configured with a concise response mode for common questions and a detailed mode for specification queries. The Human Escalation module was configured for queries the AI couldn't answer above a confidence threshold.  
**Outcomes:** AI deflected the majority of tier-1 queries within the first two weeks. Human escalation rate settled at a targeted level — only genuine complex queries reaching the team. 24/7 coverage without any additional staff.  
**Linked Personas:** Customer Experience Manager

---

### STORY 3 — Multi-Tenant AI for an Agency

**Industry:** Digital Agency  
**Challenge:** A digital agency had begun building AI chat for multiple clients but was maintaining separate tool subscriptions and configurations for each client. Every client deployment was a bespoke project, with no shared infrastructure and no knowledge transfer between deployments.  
**Solution:** The agency deployed Nexus on a shared infrastructure using the multi-tenant architecture. Each client was configured as a separate tenant with isolated knowledge, AI profiles, chat categories, and analytics. The agency manages all deployments from a single Nexus administration workspace.  
**Outcomes:** Time-to-deploy for a new client dropped from weeks to days. Full knowledge isolation between clients. Consolidated billing and management. The agency now offers AI chat as a standard service tier.  
**Linked Personas:** Agency/Platform Builder

---

### TESTIMONIALS (starter content)

**Testimonial 1 (Founder):**
"We had tried two other AI chatbot tools before Nexus. Both made up answers that directly contradicted our actual documentation. Nexus is the first tool where I felt safe putting our knowledge in — the approval workflow means nothing goes live I haven't reviewed, and the gap report tells us exactly what to write next."  
— *Founder, B2B SaaS, 25-person team*

**Testimonial 2 (Operations):**
"The knowledge gap detection feature alone was worth it. Within two weeks we had a list of 22 questions our visitors were asking that we hadn't documented. We turned those into knowledge articles and our AI coverage jumped significantly."  
— *Head of Operations, Professional Services*

**Testimonial 3 (Technical Evaluator):**
"What sold me was the architecture — specifically that the LLM provider is pluggable and the data stays in our infrastructure. Most tools in this category make you dependent on their cloud. Nexus runs on our own server and we configure our own Azure OpenAI endpoint."  
— *Technical Lead, Enterprise, Financial Services*

---

## Part 7 — Outcome Library

### Outcomes (Nexus Companion Outcome records)

| Outcome Label | Category | Detail |
|---|---|---|
| Reduced tier-1 support queries by 60–80% | Efficiency | AI handles repetitive questions without human involvement; team handles complex and relationship-requiring queries only |
| 24/7 visitor coverage with zero additional staff | Efficiency | AI responds at any hour without fatigue, error, or response time variation |
| Knowledge gaps identified automatically within the first 2 weeks | Efficiency | Gap detection surfaces every question the AI couldn't answer; team gets a precise content backlog |
| New staff onboarding time reduced | Efficiency | Internal AI allows staff to self-serve process and policy questions without senior colleague interruption |
| Qualified visitor context collected before the first human call | Revenue | Companion gathers discovery data; first human conversation starts informed, not from scratch |
| Inconsistent agent answers eliminated | Experience | One approved knowledge base means every visitor gets the same accurate answer regardless of who or what answers |
| Visitor trust increased through evidence-backed responses | Experience | AI cites grounded knowledge; visitors can see answers are traceable, not invented |
| Access-separated content for multiple audiences | Cost | One platform serves public visitors, verified customers, and internal staff with appropriate knowledge boundaries; no separate tools |
| Reduced cost per support interaction | Cost | AI handles volume; cost per resolved query drops as deflection rate rises |
| Content audit completed as a by-product of knowledge ingestion | Efficiency | Ingestion process reveals which documentation is current, which is outdated, and what's missing |

---

## Part 8 — Configuration Checklist

Use this checklist when configuring the Nexy Companion for Nexus Platform's own website chat.

### Nexus Companion Playbook
- [ ] Create playbook: "Nexus Platform Advisor Playbook"
- [ ] Copy discovery questions from Part 5
- [ ] Copy communication guidelines from Part 5
- [ ] Copy objection responses from Part 5
- [ ] Set escalation score threshold: 65
- [ ] Copy trigger keywords from Part 5
- [ ] Copy next step options from Part 5
- [ ] Set `is_default: Yes`, `enabled: Yes`

### Nexus Companion Personas (5 records)
- [ ] Scaling Founder
- [ ] Customer Experience Manager
- [ ] Technical Evaluator
- [ ] Operations/Process Owner
- [ ] Agency/Platform Builder

### Nexus Companion Products (5 records)
- [ ] Nexus Live AI Chat
- [ ] Nexus Knowledge Studio
- [ ] Nexus Companion (Nexy Advisor Mode)
- [ ] Nexus Human Escalation
- [ ] Nexus Platform (Enterprise Multi-Tenant)

### Nexus Companion Services (4 records)
- [ ] Platform Onboarding & Setup
- [ ] Knowledge Migration & Structuring
- [ ] Companion Playbook Configuration
- [ ] Ongoing Platform Management

### Reference Library
- [ ] 3 Companion Stories (from Part 6)
- [ ] 3 Companion Testimonials (from Part 6)
- [ ] 10 Companion Outcomes (from Part 7)
- [ ] Add `approved: Yes` to all reference records

### Nexus AI Agent Profile (existing profile for website chat)
- [ ] Enable `companion_mode: 1`
- [ ] Link `companion_playbook` → Nexus Platform Advisor Playbook
- [ ] Set `companion_discovery_style` → Conversational

### Verification
- [ ] Open website chat → "Connect with Nexy" category
- [ ] Confirm Nexy asks a discovery question in the first or second response
- [ ] Send a message about pricing → confirm escalation fires
- [ ] Check Companion Dashboard → confirm Enquiry record created
- [ ] Check enquiry score advances after 3–4 exchanges
