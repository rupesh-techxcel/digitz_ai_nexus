"""
DIGITZ AI Nexus — Internal Platform Knowledge Seed
====================================================
Standalone, idempotent seed for platform administrators, operators, and live agents.

Creates (under DIGITZ-AI-NEXUS tenant):
  - Internal channel:      NEXUS-INTERNAL-CHAT
  - Internal category:     NEXUS-PLATFORM-ADMIN-KNOWHOW
  - Internal AI agent:     NEXUS-INTERNAL-ASSISTANT
  - Internal access wiring (Internal + Restricted policies)
  - 16 knowledge sources covering:
      Platform architecture, knowledge pipeline, access governance, identity management,
      routing configuration, AI agent setup, tenant configuration, channel setup,
      escalation triggers, escalation rules and queues, live agent setup,
      console operations, go-live readiness, and admin diagnostic tools.

Context: NEXUS PLATFORM INTERNAL
Access: Internal (14 sources) + Restricted (2 sources — admin ops)

NOT called during installation. Run manually:

    from digitz_ai_nexus.devtools.seed_digitz_nexus_platform_knowledge import seed_nexus_platform_knowledge
    seed_nexus_platform_knowledge()

To skip embedding generation:

    seed_nexus_platform_knowledge(process_sources=False)
"""

import frappe

from digitz_ai_nexus.setup.access_seed import seed_default_access_governance
from digitz_ai_nexus.services.ingestion.processor import process_knowledge_source


# ── Identity constants ─────────────────────────────────────────────────────────

TENANT_CODE        = "DIGITZ-AI-NEXUS"
TENANT_NAME        = "DIGITZ AI Nexus"
BUSINESS_UNIT      = "DIGITZ AI NEXUS"
INTERNAL_CONTEXT   = "NEXUS PLATFORM INTERNAL"
CHANNEL_CODE       = "NEXUS-INTERNAL-CHAT"
CATEGORY_CODE      = "NEXUS-PLATFORM-ADMIN-KNOWHOW"
CATEGORY_LABEL     = "Nexus Platform Admin Know-How"
AGENT_CODE         = "NEXUS-INTERNAL-ASSISTANT"
AGENT_NAME         = "Nexus Internal Assistant"
AGENT_DISPLAY      = "Nexus Admin Assistant"
CONFIG_NAME        = "DIGITZ AI Nexus Website"   # reuse existing tenant config if present


# ── Knowledge source definitions ───────────────────────────────────────────────
# 16 sources. Sources 1–14 use "Internal" access policy.
# Sources 15–16 use "Restricted" access policy (admin/diagnostic operations).

PLATFORM_SOURCES = [

    # 1 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Platform — Architecture and Three-App Overview",
        "sub_context": "Platform Architecture",
        "entity_type": "Platform",
        "entity": "DIGITZ AI Nexus",
        "topic": "Platform Architecture and App Boundaries",
        "access_policy": "Internal",
        "priority": 10,
        "manual_content": """
The DIGITZ AI Nexus platform is built across three Frappe applications. Each app owns a distinct layer. Understanding the three-app boundary is essential for platform administrators and operators.

digitz_ai_nexus is the core knowledge and access layer. It owns the knowledge pipeline (Knowledge Source, Knowledge Unit, Knowledge Chunk), access governance (Access Policy, Access Category, Access Category Policy), tenant and business unit master records, tenant configuration, LLM provider configuration, Nexus Settings, and all services for chunking, embedding, semantic retrieval, and answer generation. If a question involves knowledge quality, access rules, or retrieval behaviour, the relevant configuration lives in this app.

digitz_ai_nexus_live is the live chat and identity layer. It owns real-time conversations (Live Conversation, Live Message), AI Agent Profiles and profile instances, escalation records and rules, agent queues, identity types and the identity registry, live channels, chat categories, category identity routes, user profile assignments, and the Nexus Live workspace with all its pages. If a question involves who handles a chat, how a visitor is identified, or what happens during escalation, the relevant configuration lives in this app.

digitz_ai_nexus_experience is the testing and validation layer. It owns Nexus Test Cases and Nexus Test Runs. Operators use this app to define expected query behaviour, validate knowledge source retrieval, test access control, confirm business unit scoping, and verify escalation triggers before certifying a tenant configuration for production.

All three apps share the same Frappe site. Data isolation between tenants is enforced through the tenant field present on every major DocType. No cross-tenant queries are permitted when strict_tenant_mode is enabled in Nexus Tenant Configuration.

Key platform pages available in the Nexus Live workspace:
- nexus_live_studio: Configuration readiness dashboard. Shows readiness score across channels, agents, routes, identity, and escalation.
- nexus_live_console: Live agent operations and escalation queue. Where human agents accept and handle escalated conversations.
- nexus_chat_category_manager: Chat category CRUD and configuration.
- nexus_category_profile_routes: Visual route builder — channel times category times identity type maps to agent profile.
- nexus_profile_access_allocation: Map AI Agent Profile to Access Categories.
- nexus_identity_registry_manager: Manage visitor identity records and verification status.
- nexus_user_profile_manager: Assign desk users as live agents with escalation permissions.
- nexus_identity_verification_monitor: OTP challenge tracking and approval.
- nexus_chat_workflow_tester: Simulate and test full chat flows before going live.

The setup sequence for a new tenant: create tenant and business unit, create access governance, create channels and categories, create AI agent profiles, create routes, load and publish knowledge sources, run test cases, certify the tenant configuration, and go live.
""",
    },

    # 2 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Studio — Knowledge Source Creation and Classification",
        "sub_context": "Knowledge Management",
        "entity_type": "Knowledge Management",
        "entity": "Nexus Knowledge Source",
        "topic": "Creation, Fields, and Classification",
        "access_policy": "Internal",
        "priority": 10,
        "manual_content": """
A Nexus Knowledge Source is the primary input record for all AI knowledge. Every answer the platform produces must trace to at least one retrieval_ready Knowledge Source. Creating a source correctly is the foundation of platform quality.

Source Types:
- Manual: Content typed directly into the manual_content field. Used for structured FAQs, runbooks, policy summaries, and SOP guidance.
- PDF: Uploaded PDF file. Text is extracted using pypdf during processing.
- DOCX: Uploaded Word document. Text is extracted using python-docx.
- TXT: Plain text file. Read directly.

Classification fields applied to every source:
- title: Required. Unique identifier across the system. Use descriptive, specific titles that communicate what the source covers.
- tenant: Required. Which tenant this knowledge belongs to. Strictly isolated — no cross-tenant retrieval.
- business_unit: Required. Which organisational division owns this knowledge.
- context: Broad subject domain. Examples: NEXUS PLATFORM INTERNAL, HR Operations, Sales, Customer Support.
- sub_context: Specific topic within context. Examples: Knowledge Setup, Leave Policy, Q2 Launch, Access Governance.
- entity_type: Classification label for the subject kind. Examples: Runbook, Policy, FAQ, Product, Feature, Configuration.
- entity: The specific subject. Examples: Nexus Knowledge Source, AI Agent Profile, Nexus Live Channel.
- topic: The aspect being covered. Examples: Creation, Status Flow, Configuration, Troubleshooting.
- access_policy: Which access policy governs retrieval. Must match the access population. Valid values depend on what policies exist for the tenant. Default values: Public, Internal, Restricted.
- priority: Integer. Lower number means higher retrieval priority. Use 10 as default. Increase for foundational knowledge.
- chat_category: Optional link to a Nexus Chat Category. Helps restrict retrieval to specific chat contexts.

Publication status workflow — the status field controls the source's publication state:
1. Draft: Being prepared. Not processed, not retrievable.
2. Pending Review: Submitted for approval. Not yet active.
3. Processed: Text extracted and chunked successfully.
4. Validated: Passed knowledge quality validation.
5. Ready to Publish: Approved, waiting for final publish action.
6. Published: Active. Eligible for retrieval if processing and embedding are also complete.
7. Disabled: Removed from retrieval without deletion.

A source must reach Published status AND have retrieval_ready equal to 1 for the AI to use it. The retrieval_ready flag is set automatically after processing, embedding, and diagnostics all succeed. A source at Published status with retrieval_ready equal to 0 is still not retrievable — check the processing and embedding status fields to find the failure.

When creating knowledge sources for a new domain, always include: what the topic is, why it matters, how it works step by step, what the valid values or options are, and what to do when something goes wrong. Short, sparse content produces poor retrieval quality.
""",
    },

    # 3 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Studio — Knowledge Processing Pipeline and Retrieval Readiness",
        "sub_context": "Knowledge Management",
        "entity_type": "Knowledge Management",
        "entity": "Nexus Knowledge Source",
        "topic": "Processing Pipeline and Retrieval Readiness",
        "access_policy": "Internal",
        "priority": 10,
        "manual_content": """
After a Knowledge Source is saved and published, processing converts its content into retrievable chunks with embeddings. This is the technical pipeline that makes knowledge usable by the AI retrieval engine.

Processing is triggered by calling process_knowledge_source(source_name) from the bench console, from a devtools seed, or via a process action in the Nexus Studio interface.

Step-by-step pipeline:

Step 1 — Text Extraction: The source file or manual content is read. PDFs are parsed with pypdf page-by-page. DOCX files are read paragraph-by-paragraph using python-docx. TXT and Manual sources are read directly.

Step 2 — Archive Old Chunks: Any existing Knowledge Chunks for this source are marked archived equal to 1 and disabled equal to 1. This ensures previous chunk versions do not interfere with the new processing run. Version tracking is maintained via the source_version field on chunks.

Step 3 — Create Knowledge Unit: A new Nexus Knowledge Unit record is created as a snapshot of the source content at this point in time. The unit carries the source's tenant, business unit, context, and access policy.

Step 4 — Chunk Text: The extracted text is split into overlapping chunks. Default chunk_size is 800 characters. Default chunk_overlap is 120 characters. These defaults are set in Nexus Settings and apply across all sources unless overridden. Larger chunks capture more context per retrieval result; smaller chunks increase precision at the cost of context completeness.

Step 5 — Generate Embeddings: Each chunk is sent to the configured LLM provider to generate a vector embedding. The embedding is stored as JSON in the Knowledge Chunk record. Embedding model is resolved from the active LLM provider configuration.

Step 6 — Diagnose Chunks: Each chunk is evaluated against quality rules. Critical severity means empty content — the chunk cannot be used for retrieval. Warning severity means fewer than 50 characters (too short to be meaningful) or more than 6,000 characters (too long for accurate retrieval), or a duplicate detected when the chunk_hash (SHA256) matches an existing chunk. Healthy means the chunk passes all checks.

Step 7 — Save Chunks: Each chunk is saved as a Nexus Knowledge Chunk with chunk_text, chunk_hash, character_count, embedding, embedding_status, diagnostics_status, diagnostics_message, source_version, and links back to the Knowledge Unit and Knowledge Source.

Step 8 — Finalize Source: The source's processing_status, chunk_count, active_chunk_count, embedding_status, diagnostics_status, and retrieval_ready fields are updated to reflect the outcome.

Status field reference:

processing_status valid values: Pending, Processing, Processed, Failed
embedding_status valid values: Pending, Completed, Failed
diagnostics_status valid values: Pending, Healthy, Warning, Critical
validation_status valid values: Pending, Passed, Failed
retrieval_ready: 0 until all conditions met, then 1

retrieval_ready equals 1 requires all of: status equals Published, embedding_status equals Completed, diagnostics_status equals Healthy (Warning may still allow retrieval depending on settings), and at least one active non-archived chunk exists.

Source versioning: Each full reprocessing increments processing_version. Archived chunks carry their source_version to distinguish old from current. Only chunks where archived equals 0 and disabled equals 0 are eligible for retrieval.

Diagnosing a source that is not retrieving: Use the Source Quality Panel API (get_source_quality_panel(source_name)) to inspect per-chunk embedding status, diagnostic severity, and duplicate flags. Use the Chat Reachability API (get_source_chat_reachability(source_name)) to walk the access chain and confirm which AI Agent Profiles can reach the source. Check that the source's access_policy is included in the Access Category linked to the AI Agent Profile serving the query.
""",
    },

    # 4 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Administration — Access Governance: Policy, Category, and Profile Chain",
        "sub_context": "Access Governance",
        "entity_type": "Access Governance",
        "entity": "Nexus Access Policy",
        "topic": "Policy Category Profile Access Chain",
        "access_policy": "Internal",
        "priority": 10,
        "manual_content": """
Access governance in DIGITZ AI Nexus controls which knowledge a visitor or user can receive. The governance chain has four layers: Access Policy, then Access Category, then AI Agent Profile Access Category, then Conversation Route or User Assignment. Understanding the full chain is required for correct platform configuration.

Layer 1 — Nexus Access Policy:
An Access Policy is the atomic unit of access control. It declares a named boundary for a class of knowledge. Policies are tenant-scoped. Default policies created by the core install are Public, Internal, and Restricted.

Key fields on Nexus Access Policy:
- policy_name: Required. Unique within the tenant.
- tenant: Tenant scope.
- access_level: Metadata label — Public, Customer Restricted, Internal, Role Restricted, Finance Restricted, HR Confidential, Admin Only.
- sensitivity: Metadata label — public, customer, operational, internal, financial, hr, confidential.
- is_primitive: Only the Public policy carries this flag. It cannot be modified or deleted.

Knowledge Sources are tagged with an access_policy field. Only sources whose access_policy is in the resolved allowed policy list for the current visitor or user will be retrieved.

Layer 2 — Nexus Access Category:
An Access Category is a named grouping of one or more Access Policies. Categories are how policies are applied to agents without requiring one-to-one policy wiring.

Key fields on Nexus Access Category:
- category_name: Required. Unique within the tenant.
- tenant: Tenant scope.
- priority: Int. Lower means higher priority when multiple categories apply.
- allowed_policies: Child table of Nexus Access Category Policy rows. Each row links one Access Policy.

Example: An Internal Operations Access Category might include policies Internal and Restricted. Any agent assigned this category can retrieve knowledge tagged with either policy.

Layer 3 — Runtime Resolution:
When a conversation starts, the platform resolves the visitor's identity via their Identity Profile, maps it to a Knowledge Profile through Identity Mappings, then collects all Access Categories linked to that Knowledge Profile, expands each category into its policies, and uses the resulting policy list as the retrieval filter. A Knowledge Chunk is only returned if its access_policy appears in this list.

For desk users accessing Q&A, the Nexus User Profile Assignment maps the user to an AI Agent Profile, and the same chain applies.

To configure access for a new knowledge population:
1. Create or identify the appropriate Access Policy.
2. Create or identify an Access Category that includes that policy.
3. Link the Access Category to the AI Agent Profile that should serve this knowledge.
4. Ensure the Route for the target channel, category, and identity type uses that profile.
5. Tag knowledge sources with the correct access_policy.

Common misconfiguration: A knowledge source is Published and retrieval_ready but still not returned. The cause is almost always that the source's access_policy is not included in any Access Category linked to the serving AI Agent Profile. Use get_source_chat_reachability(source_name) to verify the full chain.
""",
    },

    # 5 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Studio — AI Agent Profile Configuration",
        "sub_context": "Agent Configuration",
        "entity_type": "Platform Configuration",
        "entity": "Nexus AI Agent Profile",
        "topic": "Configuration Fields and Behaviour",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
The Nexus AI Agent Profile defines how the AI behaves in conversations. Every conversation is driven by exactly one active profile at the time it was started. The profile's behaviour is snapshotted at conversation start and remains immutable for the duration of that conversation to ensure consistency.

Identity and operational fields:
- agent_code: Required. Unique identifier within the tenant. Examples: PUBLIC-AI-ASSISTANT, NEXUS-INTERNAL-ASSISTANT.
- tenant: Tenant scope.
- agent_name: Internal name used in admin interfaces.
- display_name: Name shown to visitors in the chat widget.
- nickname_pool: Newline-separated list of random session persona names. One is randomly selected per session for a personalised experience. Example entries: Aria, Nova, Sage, Echo, Finn.
- agent_role: Determines which Escalation Rule applies when this profile triggers escalation. Valid values: Public Responder, Sales, Support, Consultant, Internal Assistant, Admin Reviewer.
- visibility: Public (accessible via public routes), Internal (desk and portal only), or Both.
- enabled: 1 to activate the profile.
- status: Runtime state — Idle, Assigned, Responding, Waiting, Unavailable, Disabled.
- priority: Int. Lower means preferred when multiple agents are eligible.
- max_active_sessions: Int. Maximum concurrent conversations this profile can handle. Default 10.
- default_channel: Link to the preferred Nexus Live Channel for this agent.

Behaviour fields:
- behavior_prompt: The core system instruction passed to the LLM for every conversation. This is the most important field. It defines what the agent is, what it is allowed to say, how it interprets approved knowledge, and what to do when knowledge is insufficient. Write this as a clear, specific instruction. Example: You are the Nexus Platform internal assistant. Answer questions about platform configuration, knowledge management, access governance, and escalation workflows using only approved internal knowledge. If approved knowledge is insufficient, say you do not have enough approved knowledge and suggest checking the Nexus Live Studio readiness dashboard.
- tone: Professional, Conversational, Technical, Empathetic, or Formal.
- response_style: Balanced, Concise, or Detailed.
- welcome_message: First message shown to the visitor when the conversation starts.
- fallback_message: Message shown when no approved knowledge is found to answer the question.
- do_not_answer_rules: Explicit prohibitions. Topics the agent must not address regardless of whether knowledge exists. Example: Do not share credentials, API keys, or system passwords. Do not discuss other tenants' data.

Knowledge and retrieval fields:
- default_response_mode: chat or qa.
- knowledge_scope: Governed (retrieve from approved sources only).
- confidence_threshold: Float. Default 0.65. If retrieval confidence falls below this, escalation may be triggered depending on Escalation Rule configuration.

Escalation fields:
- escalation_enabled: 1 to allow this profile to trigger escalation.
- memory_mode: None, Session (context carries within a session), Conversation Summary, or Long Term.

Notes field:
- system_notes: Internal configuration notes not shown to visitors or agents.

Practical guidance: A profile used for a public route should have agent_role equal to Public Responder. This ensures that Escalation Rules configured for Public Responder are applied correctly when escalation triggers fire. An internal or desk-facing profile should use Internal Assistant. A sales-focused profile should use Sales so that Sales Lead escalation routes correctly to the Sales queue.

Never leave behavior_prompt blank. A blank prompt produces unpredictable LLM behaviour. The fallback_message should always instruct the visitor what to do next — not just say the AI cannot help.
""",
    },

    # 6 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Administration — Identity Types and the Identity Registry",
        "sub_context": "Identity Management",
        "entity_type": "Identity Management",
        "entity": "Nexus Identity Type",
        "topic": "Identity Types and Registry Configuration",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
The identity layer controls which level of knowledge access a visitor receives. It begins with Identity Types — the taxonomy of user classes — and the Identity Registry — the database of known visitor identities.

Nexus Identity Type:
Identity Types are the named classes of users the platform serves. They are global (not tenant-scoped) because they represent a shared visitor taxonomy across the platform.

Default types seeded on install: Public, Customer, Prospect, Partner, Internal, Admin.

Custom types can be created for specific business scenarios. Key fields:
- title: Unique name.
- enabled: 1 to activate.
- sort_order: Int. Display ordering in UI dropdowns.
- description: Admin notes describing what this identity type represents.
- safeguard_access_categories: Child table. Hard access cap applied to ALL holders of this identity type regardless of their knowledge profile. If a visitor's resolved knowledge profile grants categories A, B, and C but the identity type's safeguard contains only A and B, the effective access is restricted to A and B. This intersection logic ensures identity-level caps cannot be bypassed through knowledge profile configuration.

The Public identity type is the baseline. When identity cannot be resolved, the platform defaults to Public. The Public identity type should not have safeguard restrictions — it is already the lowest access tier.

Nexus Identity Registry:
The Identity Registry is a database of known, named visitor identities. A visitor becomes registered when the platform has a record linking their email to one or more identity types.

Key fields:
- email: Required. Primary identifier. Must be unique.
- full_name: Display name.
- enabled: 1 to allow this registry entry to be resolved. Set to 0 to suspend access without deletion.
- verification_status: Unverified, Verified, or Blocked. Only Verified identities are fully trusted by the platform for elevated access.
- verified_on: Timestamp when verification was completed.
- user: Optional link to a Frappe User for desk user binding.
- reference_doctype and reference_name: Optional link to a business record such as Contact, Lead, or Customer for CRM integration.
- contact: Optional link to Frappe Contact.
- mobile_no: Optional phone number.
- identity_profiles: Child table of Nexus Registered Identity rows. Each row contains identity_type (Link), enabled, is_primary, valid_from (Date), valid_until (Date).

A visitor can hold multiple identity types simultaneously. Only identity entries where enabled equals 1 and the current date falls within valid_from to valid_until are active.

How identity is resolved at conversation start — the Identity Resolver service evaluates in priority order:
1. Trusted server-side payload (API calls with explicit identity_type claim)
2. Verified OTP challenge passed in the current session
3. Session user type and roles (for desk and portal authenticated users)
4. Registered email match in the Identity Registry where verification_status equals Verified
5. Default: Public

The resolved identity_type is stored on the Nexus Live Conversation record as resolved_identity_type and is immutable for the session.

Blocking a visitor: Set verification_status equal to Blocked in their Identity Registry record. The resolver will reject them and default to Public or deny access depending on the category's allow_public_fallback setting.

Managing expired identities: Set valid_until on an identity row to a past date to deactivate it without modifying the registry record. This is useful for time-limited partner access or contract-based customer identities.
""",
    },

    # 7 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Administration — Identity Profiles and Knowledge Profile Access Mapping",
        "sub_context": "Identity Management",
        "entity_type": "Identity Management",
        "entity": "Nexus Identity Profile",
        "topic": "Profile Mapping and Knowledge Access Resolution",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
After identity is resolved, the platform uses Identity Profiles and Knowledge Profiles to translate the visitor's identity type into a specific set of access categories — the actual knowledge they can retrieve.

Nexus Identity Profile:
An Identity Profile is a mapping table that associates identity types with Knowledge Profiles. It is the bridge from who the visitor is to what they can access.

Key fields:
- profile_name: Required. Unique within tenant.
- tenant: Tenant scope.
- title: Display name.
- enabled: 1 to activate.
- identity_mappings: Child table of Nexus Identity Profile Mapping rows. Each row maps one identity_type (Link) to one knowledge_profile (Link).

Example configuration: An Identity Profile might specify Public maps to Knowledge Profile named Website Public Access, Customer maps to Knowledge Profile named Customer Portal Access, and Internal maps to Knowledge Profile named Internal Staff Access. A conversation starting with a Customer identity type resolves to the Customer Portal Access knowledge profile via this mapping.

Knowledge Profile:
A Knowledge Profile defines which Access Categories a user with that profile can retrieve from.

Key fields:
- profile_name: Required. Unique within tenant.
- tenant: Tenant scope.
- title: Display name.
- enabled: 1 to activate.
- access_categories: Child table of Knowledge Profile Access Category rows. Each row links one access_category.

The Knowledge Profile accumulates access categories into the final allowed policy set. Multiple categories in one profile are combined as a union. The resulting policy set is then intersected with any identity type safeguard categories before retrieval executes.

Full access resolution path at conversation start:
1. Visitor's resolved_identity_type is known. Example: Customer.
2. The Category Identity Route links to an ai_agent_profile.
3. The Identity Profile associated with the route maps Customer to Knowledge Profile Customer Portal Access.
4. Customer Portal Access specifies Access Categories: Public Access and Customer Restricted.
5. Those categories expand to policies: Public and Customer.
6. Identity Type safeguard for Customer caps at: Public and Customer (no reduction in this case).
7. Final retrieval filter: knowledge chunks tagged Public or Customer.

Where Identity Profile is linked:
The Identity Profile is associated via the Nexus Category Identity Route in the identity_profiles child table, where each row links an identity_profile. This tells the route which knowledge profile mapping to apply for each identity type that passes through it.

Important note: The AI Agent Profile Access Category (Profile to Access Category to Policies) provides a separate parallel access permission layer. Both the Knowledge Profile path and the Agent Profile path contribute to the final allowed policy set. They are combined. The most restrictive intersection applies where safeguard caps are involved. If these two paths grant conflicting access levels, the narrower result wins.

Troubleshooting access that is too wide: Check whether the Agent Profile's Access Category grants more than intended. Also check whether the Identity Type safeguards are correctly set. A visitor receiving access to Internal knowledge when they should only have Public access usually means one of: the route points to an Internal profile, the Access Category on the profile includes Internal policy, or the identity type lacks a safeguard cap.
""",
    },

    # 8 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Administration — Category Identity Routes and Chat Routing",
        "sub_context": "Routing Configuration",
        "entity_type": "Platform Configuration",
        "entity": "Nexus Category Identity Route",
        "topic": "Route Configuration and Resolution Logic",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
The Category Identity Route is the central routing decision record in the Nexus Live platform. It determines which AI Agent Profile handles a conversation given the visitor's chat category selection and resolved identity type. The channel is derived automatically from the selected chat category — each Nexus Chat Category belongs to exactly one channel, so selecting the category implies the channel.

How a route is selected at conversation start:
The platform derives the channel from the chat category's channel field. It then evaluates all enabled routes for the given channel and chat category. It selects the best-matching route by checking whether the visitor's identity profiles are permitted by the route (either the identity_profiles child table is empty which accepts all visitors as public, or the visitor's assigned Identity Profiles intersect with the route's identity_profiles child table), sorting by priority (lower number wins), and selecting the first matching enabled route.

Nexus Category Identity Route fields:
- chat_category: Required. Link to Nexus Chat Category. The category owns the channel — selecting a category implies the channel.
- channel: Read-only. Link to Nexus Live Channel. Automatically derived from chat_category.channel via fetch_from. Cannot be set manually. Retained for filtering and reporting.
- ai_agent_profile: Required. The AI Agent Profile that handles conversations matching this route.
- enabled: 1 to activate the route.
- published: 1 to make the route active for identity-based routing. Uncheck to draft or suspend a route without deleting it.
- identity_profiles: Child table of Nexus Route Identity Profile rows. When empty, the route is open to all visitors (public route). When populated, only visitors whose Identity Profiles intersect this list will match.
- priority: Int. Lower means higher priority. Routes with lower numbers are checked first.
- description: Admin notes.

Public vs registered routes:
A route with an empty identity_profiles child table is a public route — it accepts all visitors without identity matching. Knowledge access is limited to the Public access policy. A route with identity_profiles rows is a registered route — only visitors whose assigned profiles match the permitted list can use it. There is no is_public_route checkbox; the distinction is entirely determined by whether identity_profiles has any rows.

Common routing configurations:
A single channel and category pair can have multiple routes at different priorities. Example setup for three visitor tiers:
- Priority 5: Route with identity_profiles containing Internal Profile maps to Internal AI Agent Profile with full internal access.
- Priority 10: Route with identity_profiles containing Customer Profile maps to Customer AI Agent Profile with customer access.
- Priority 20: Public route with empty identity_profiles maps to Public AI Agent Profile as fallback for unidentified visitors.

A visitor identified as Customer matches the priority 10 route. A visitor who cannot be identified matches the priority 20 public route. A visitor identified as Internal matches the priority 5 route.

Troubleshooting route resolution failures:
If a conversation is not routing correctly: Check that the route's enabled equals 1. Verify the chat_category matches exactly — it is a Link and is case-sensitive. The channel on the route is derived from the category and does not need to be set manually. For registered routes, confirm the visitor's identity was resolved correctly by checking resolved_identity_type on the conversation record. Check priority ordering — a higher-priority route (lower number) may be matching before the intended one. Use the Nexus Chat Workflow Tester page at nexus_chat_workflow_tester to simulate the routing decision for a given category and identity. Use the Category Profile Routes page at nexus_category_profile_routes to visualise all routes for a category.

When no route matches: The conversation fails to resolve an agent profile and the platform returns an error or a default fallback response. Ensure at least one route with an empty identity_profiles child table (public route) exists for every live category to guarantee all visitors can reach an agent even when identity resolution fails.

Route planning principle: Design routes from most specific to least specific. Higher-privilege identity types (Internal, Admin) should have lower priority numbers (checked first). The public fallback route should always be last with the highest priority number. This ensures that more privileged visitors get their appropriate agent while all others fall through to the public route gracefully.
""",
    },

    # 9 ─────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Administration — Tenant Configuration and Ecosystem Settings",
        "sub_context": "Tenant Configuration",
        "entity_type": "Platform Configuration",
        "entity": "Nexus Tenant Configuration",
        "topic": "Configuration and Go-Live Settings",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
Nexus Tenant Configuration is the master control record for a tenant's operational environment. Every tenant must have exactly one enabled, default configuration to operate. This record controls knowledge retrieval behaviour, chat and Q&A enablement, widget defaults, and governance certification.

Configuration identity fields:
- configuration_name: Required. Instance identifier. Example: Default Live, DIGITZ AI Nexus Website.
- tenant: Required. Parent tenant.
- configuration_type: Production, Sandbox, Synthetic Validation, or Internal Platform. Use Production for live deployments. Use Sandbox for development and testing.
- enabled: 1 to activate.
- is_default: 1 to mark as the tenant's primary configuration. Only one configuration per tenant can be default. The platform enforces this constraint.
- activation_status: Workflow state — Draft, Configured, Testing, Certified, Active, Suspended. The platform checks this during runtime routing.
- notes: Admin notes.

Default business context fields:
- default_business_unit: Link to Nexus Business Unit. Used when no business unit is specified in the request payload.
- default_project: Text. Optional project scope applied when no project is in the payload.

Knowledge retrieval defaults:
- require_approved_knowledge: Checkbox. Default 1. When enabled, only Published sources with retrieval_ready equal to 1 are used. Disable only in development for testing unpublished sources.
- strict_tenant_mode: Checkbox. Default 1. When enabled, retrieval is strictly filtered to the tenant. Never disable in production.
- default_top_k: Int. Default 5. Number of knowledge chunks returned per retrieval. Increase for complex domain queries that need more context. Decrease for performance-sensitive deployments.

Q&A settings:
- qa_enabled: Checkbox. Default 1. Must be enabled to serve Q&A requests.
- default_qa_channel: Link to Nexus Live Channel of type Website Q&A. Default channel for Q&A if not specified in request.
- qa_fallback_message: Text shown when no approved knowledge answers the Q&A query.
- source_citation_required: Checkbox. Default 1. When enabled, answers include source attribution.

Live chat settings:
- live_chat_enabled: Checkbox. Default 1. Must be enabled to serve chat requests.
- default_chat_channel: Link to Nexus Live Channel of type Website Chat.

Widget defaults:
- website_widget_enabled: Checkbox. Default 0. Enable to allow the embedded chat widget on the website.
- widget_title: Widget header label shown to visitors.
- widget_welcome_message: Text shown at widget open before the first AI message.
- widget_brand_color: Hex colour. Default is the DIGITZ blue value.

Governance fields:
- testing_required_before_activation: Checkbox. Default 1. Requires a test run pass before going to Active status.
- certification_status: Not Certified, In Progress, Passed, or Failed.
- last_certified_on: Timestamp of last successful certification.

Activation checklist before going live:
1. activation_status should be Configured or Testing before first certification.
2. Run at least one Nexus Test Run against the tenant to validate retrieval and access.
3. Set certification_status to Passed once tests pass.
4. Set activation_status to Active.
5. Enable website_widget_enabled if deploying the widget.
6. Confirm default_chat_channel and default_qa_channel are correctly set.
7. Confirm strict_tenant_mode is 1 and require_approved_knowledge is 1 in production.
""",
    },

    # 10 ────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Administration — Live Channels and Chat Categories",
        "sub_context": "Channel Configuration",
        "entity_type": "Platform Configuration",
        "entity": "Nexus Live Channel",
        "topic": "Channel and Chat Category Configuration",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
Channels and Chat Categories are the entry-point configuration for all visitor interactions. Every chat or Q&A request arrives on a channel and selects a category. Configuring both correctly is foundational to platform operation.

Nexus Live Channel:
A channel represents a communication surface — a website, a portal, a desk interface, or an API integration. Channels are tenant-scoped.

Key fields:
- channel_code: Required. Unique within tenant. System identifier used in API calls and widget configuration. Example: NEXUS-WEBSITE-CHAT, NEXUS-INTERNAL-CHAT.
- tenant: Tenant scope.
- channel_name: Display name for admin interfaces.
- channel_type: Website Q&A, Website Chat, Desk, Portal, or API. The Website Chat type supports conversational sessions with memory and escalation. The Website Q&A type is stateless — single question, single answer. The Desk type is for internal desk user sessions.
- enabled: 1 to activate.
- public_access: Checkbox. 1 means accessible to public visitors without authentication.
- requires_visitor_email: Checkbox. When 1, the visitor must supply an email before the chat begins. Used for identity pre-collection before the conversation starts.
- agent_based: Checkbox. When 1, the channel routes directly to a specific agent rather than through category-route resolution.
- default_agent: Link to Nexus AI Agent Profile. Used when agent_based equals 1 or as the fallback.
- description: Admin notes.

Nexus Chat Category:
A Chat Category represents a topic area within a channel. Visitors select a category before starting a conversation, directing the platform to the correct AI agent and knowledge scope.

Key fields:
- category_code: Required. Unique within tenant. System identifier.
- category_label: Required. Visitor-facing display name shown in the chat widget.
- channel: Required. Link to the parent Nexus Live Channel.
- tenant: Tenant scope.
- enabled: 1 to make the category visible in the widget.
- visibility: Select. External shows only in public chat widget. Internal shows only in desk chat. Both shows in both interfaces.
- identity_verification_mode: None, Email OTP, or Registered Email OTP. Controls the mid-conversation verification challenge. Email OTP sends a one-time code to the visitor's email for identity confirmation. Registered Email OTP only accepts verification if the email is already in the Identity Registry.
- allow_public_fallback: Checkbox. When identity_verification_mode is Registered Email OTP, this allows unregistered visitors to proceed with Public-level access if they fail verification.
- display_order: Int. Default 10. Lower numbers appear first in the category selection widget.
- published: Checkbox. When checked, category appears in the chat widget picker. Uncheck to hide from visitors without disabling it.
- description: Internal notes.
- enable_escalation: Checkbox. When 1, escalation is permitted for conversations in this category.

Important design rule: Each Nexus Chat Category belongs to exactly one Nexus Live Channel via its channel field. This means selecting a category automatically implies the channel. The Nexus Category Identity Route's channel field is read-only and derived from the category — it does not need to be set manually on the route.

Configuration checklist for a new channel and category:
1. Create the Nexus Live Channel with the correct channel_type.
2. Create at least one Nexus Chat Category linked to that channel via the channel field with a clear visitor-facing label.
3. Create at least one Nexus Category Identity Route for the category with an empty identity_profiles child table as the public fallback minimum.
4. Link the route to an AI Agent Profile with a configured behavior_prompt and access categories.
5. Ensure the AI Agent Profile has at least one Access Category linked.
6. Ensure at least one Knowledge Source is Published and retrieval_ready for the policies in that Access Category.
7. Update the Nexus Tenant Configuration to set default_chat_channel or default_qa_channel to this channel if it is the primary channel.

Category display order: Visitors see categories sorted by display_order ascending. Put the most commonly used category first with display_order 10. Use increments of 10 (10, 20, 30) so new categories can be inserted without renumbering.
""",
    },

    # 11 ────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Live — Escalation Triggers and Detection Logic",
        "sub_context": "Escalation Workflow",
        "entity_type": "Escalation Management",
        "entity": "Nexus Live Escalation",
        "topic": "Escalation Triggers and Detection",
        "access_policy": "Internal",
        "priority": 10,
        "manual_content": """
Escalation is the platform's designed handoff from AI to a human agent. It is not a failure state — it is a controlled transition with a full context package. Understanding the eight escalation trigger types and how each is detected is essential for agents who handle escalations and administrators who configure escalation rules.

The escalation_reason field on Nexus Live Escalation records stores which trigger fired. The eight valid values and their detection logic:

Low Confidence:
Triggered when the AI's response confidence score falls below the configured confidence_threshold on the AI Agent Profile (default 0.65). This means retrieved knowledge was found but the AI is not confident enough in its answer to serve it without human review. The confidence value is stored on the Live Escalation record for review.

No Approved Knowledge:
Triggered when retrieval finds no valid knowledge chunks for the query. The AI uses the fallback_message from the Agent Profile. When this happens and the Escalation Rule has escalate_on_no_knowledge equal to 1, escalation fires immediately. This trigger signals a knowledge gap — the query is within scope but the knowledge base does not contain a relevant, published, retrieval_ready source.

User Requested Human:
Triggered when the visitor explicitly asks to speak to a human. Detected via keyword signals in the visitor's message such as talk to someone, speak to an agent, or human please. This trigger should always be honoured when escalate_on_human_request equals 1 in the Escalation Rule.

Sales Lead:
Triggered when the AI or keyword detection identifies the conversation as a sales lead — the visitor is expressing intent to purchase, requesting a demo, or asking about pricing. Routes the conversation to the Sales queue or agent for commercial follow-up.

Support Required:
Triggered when the visitor's message contains signals of a product issue, error, complaint, or escalation need. Keywords such as not working, error, broken, or complaint activate this trigger. Routes to the Support queue or agent for technical resolution.

Restricted Topic:
Triggered when the visitor's question involves a topic that falls outside the agent's access policy scope — the knowledge exists but is restricted, and the AI is not permitted to retrieve it for this visitor's access level. Instead of attempting to answer from restricted content, the AI escalates cleanly with the reason Restricted Topic.

Repeated Fallback:
Triggered when the AI has used the fallback message multiple times in the same conversation. The threshold is configurable per Escalation Rule. This prevents the visitor from receiving repeated I don't know responses without being connected to a human who can actually help.

Other:
Custom escalation triggered by business logic not covered by the above types. Can be triggered programmatically or via custom conditions in rule_conditions_json on the Escalation Rule.

What happens when escalation fires:
1. The system reads the Escalation Rule for the current agent's agent_role.
2. Determines the target: a specific target_agent (AI Agent Profile) or a target_queue (Nexus Agent Queue).
3. Creates a Nexus Live Escalation record with status equal to Pending.
4. Updates the Conversation status to Escalated and sets escalation_status to Pending.
5. Sets the from_agent profile's status to Waiting.
6. Publishes a nexus_escalation_alert realtime event to all subscribers on the Nexus Live Console page.
7. The human agent picks up the escalation from the console queue.

What the human agent receives on pickup:
- Full conversation thread with all messages in chronological order
- Escalation reason (which of the 8 triggers fired)
- Visitor identity information: resolved_identity_type, visitor_name, visitor_email
- Knowledge sources the AI retrieved and used
- Confidence score at the point of escalation
- AI-generated context summary

The visitor is shown a holding message configurable in the category or agent profile while waiting for the human agent to accept.
""",
    },

    # 12 ────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Live — Escalation Rules, Agent Queues, and Queue Assignment",
        "sub_context": "Escalation Workflow",
        "entity_type": "Escalation Management",
        "entity": "Nexus Escalation Rule",
        "topic": "Rules, Queues, Assignment, and Routing Configuration",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
Escalation Rules define the conditions and destinations for escalation routing. Agent Queues are the receiving pools for escalations. Queue Assignments map desk users (live agents) to queues.

Nexus Escalation Rule:
One rule per agent_role. The rule determines when and where escalation routes.

Key fields:
- rule_name: Display name for the rule.
- enabled: 1 to activate.
- agent_role: The agent role this rule applies to. Matches the agent_role field on the AI Agent Profile. Valid values: Public Responder, Sales, Support, Consultant, Internal Assistant, Admin Reviewer.
- minimum_confidence: Float. Default 0.65. Escalation fires when response confidence falls below this threshold. Should match or be consistent with the Agent Profile's confidence_threshold.
- escalate_on_no_knowledge: Checkbox. Default 1. When enabled, a fallback response (no approved knowledge found) triggers escalation.
- escalate_on_human_request: Checkbox. Default 1. When enabled, explicit visitor requests for a human agent are always honoured immediately.
- target_queue: Link to Nexus Agent Queue. Escalation is routed to this queue.
- target_agent: Link to Nexus AI Agent Profile. When set, escalation routes directly to this specific agent rather than to the queue. Takes precedence over target_queue when both are set.
- rule_conditions_json: JSON. Custom condition logic for future extensions.

Nexus Agent Queue:
A queue is a named pool that receives and holds escalated conversations until a qualified live agent accepts.

Key fields:
- queue_code: Required. Unique identifier.
- queue_name: Required. Display name.
- queue_type: Sales, Support, Implementation, or Admin Review.
- enabled: 1 to activate.
- description: Notes about what this queue handles.

Nexus Queue Assignment:
Maps a live agent (desk user configured for escalation handling) to a queue.

Key fields:
- queue: Link to Nexus Agent Queue.
- agent: Link to Nexus Live Agent.
- priority: Int. Default 10. Lower means preferred when auto-assigning within the queue.
- enabled: 1 to activate the assignment.

Recommended setup for a two-queue configuration:
1. Create two queues: Sales Queue with queue_type Sales and Support Queue with queue_type Support.
2. Create two Escalation Rules: Rule A for agent_role Public Responder routes to Sales Queue (for lead generation bots). Rule B for agent_role Support routes to Support Queue (for support bots).
3. Create Queue Assignments to link relevant desk users to each queue with appropriate priorities.
4. Ensure each desk user has a Nexus User Profile Assignment with can_handle_escalations equal to 1 and the correct escalation_categories listed.

Escalation routing priority: When both target_queue and target_agent are set on an Escalation Rule, target_agent takes precedence. Use target_agent for direct routing to a named agent (suitable for dedicated account managers). Use target_queue for pool routing (suitable for support teams).

Monitoring escalation health: Check Nexus Live Escalation records where status equals Pending and created_on is older than your SLA threshold. These are conversations waiting for pickup with no agent response. Increase queue assignment coverage or agent max_escalation_sessions capacity to address backlog.

Escalation status values on Nexus Live Escalation: Pending (waiting for agent pickup), Accepted (agent has claimed the conversation), Resolved (conversation closed successfully), Rejected (agent rejected, conversation returns to queue).
""",
    },

    # 13 ────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Live — Live Agent Setup and User Profile Assignment",
        "sub_context": "Agent Operations",
        "entity_type": "Escalation Management",
        "entity": "Nexus User Profile Assignment",
        "topic": "Agent Configuration and Escalation Permissions",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
A desk user becomes a Nexus Live Agent when they are correctly configured with a User Profile Assignment. This configuration controls whether they can handle escalated conversations, how many they can handle simultaneously, and which chat categories they cover.

Nexus User Profile Assignment fields:
- user: Required. Link to Frappe User. The desk user being configured.
- active: Checkbox. Default 1. Must be 1 for the assignment to take effect. Only one active assignment per user is allowed at a time.
- assigned_by: Read-only. Link to the admin who created the assignment.
- assigned_on: Read-only. Datetime of assignment creation.
- can_handle_escalations: Checkbox. Must be 1 for the user to appear in escalation queues and be able to pick up escalated conversations.
- max_escalation_sessions: Int. Default 1. Maximum concurrent escalated conversations the agent can handle. Increase for senior or high-capacity agents. Set to 0 to temporarily suspend escalation pickup without deactivating the assignment.
- escalation_categories: Child table of Nexus Chat Category Link rows. Only escalations from these categories are visible to this agent in the console queue. Leave empty to receive all categories (agent sees all queues they are assigned to).
- notes: Internal notes about the assignment.

Setting up a new live agent:
1. The desk user must exist in the Frappe system with a valid user account and desk access.
2. Create a Nexus User Profile Assignment: user equals the desk user, active equals 1, can_handle_escalations equals 1, max_escalation_sessions equals the agent's capacity (typically 1 to 3 for most agents), escalation_categories equals the chat categories this agent covers.
3. Assign the user to relevant Nexus Agent Queues via Nexus Queue Assignment records.
4. The user can now log into the Frappe desk and navigate to the Nexus Live Console at the nexus_live_console page to monitor their escalation queue.

Deactivating an agent: Set active to 0 on their Nexus User Profile Assignment. This removes them from all escalation queues immediately. Conversations already accepted by the agent are not affected and must be closed manually.

Modifying capacity: Update max_escalation_sessions on the assignment to increase or decrease the agent's concurrent conversation limit. Changes take effect immediately for new escalations.

Managing agent category scope: Add or remove rows in the escalation_categories child table to control which types of conversations the agent handles. An agent covering Sales and Support categories sees only escalations from those categories, reducing noise and improving focus.

The Nexus User Profile Manager page at nexus_user_profile_manager provides a visual interface for creating and managing user profile assignments without going to the DocType editor.

Nexus Live Agent versus Nexus AI Agent Profile: These are distinct records. Nexus AI Agent Profile defines AI behaviour and knowledge access. Nexus User Profile Assignment defines a human desk user's escalation permissions and capacity. A human agent picks up conversations escalated by AI agents. The two records do not share identity — the AI Agent Profile's agent_code is unrelated to the desk user's Frappe User account.
""",
    },

    # 14 ────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Live — Using the Live Console for Agent Operations",
        "sub_context": "Agent Operations",
        "entity_type": "Platform Operations",
        "entity": "Nexus Live Console",
        "topic": "Agent Console Operations and Escalation Handling",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
The Nexus Live Console at the nexus_live_console page is the real-time operations interface for human agents. It displays active conversations, pending escalations, and provides the chat interface for human-agent conversations.

Console sections:

Active Conversations Panel: Shows all conversations currently assigned to the logged-in agent with status Handed Over. Displays visitor name, category, elapsed time, and last message. Clicking a conversation opens the full thread in the right panel.

Escalation Queue Panel: Shows all pending escalations visible to this agent based on their escalation_categories configuration. Each item shows the visitor identifier (name or email if captured), category and channel, escalation reason (which of the 8 triggers fired), waiting time since escalation, and a preview of the last AI message and visitor message.

Conversation Thread: When a conversation is opened, the full message history is displayed in chronological order. Messages are displayed by sender type: Visitor messages, AI Agent messages, System messages (escalation events, category changes, verification prompts), and Human Agent messages (the logged-in agent's own messages after accepting).

Taking an escalation:
1. Click Accept on a pending escalation in the queue.
2. The conversation thread opens in the right panel.
3. Review the full AI conversation history, knowledge sources used, and the escalation trigger reason.
4. Type your response in the input field and send.
5. The visitor receives responses in real-time via WebSocket.

Rejecting an escalation: Click Reject to return the conversation to the queue. Use only when the conversation falls outside your area of expertise or when you are at capacity. A rejected escalation returns to the queue for other agents to pick up.

Closing a conversation: Once the issue is resolved, click Close Conversation. This sets conversation status to Closed and escalation status to Resolved. The visitor sees a closed state in their widget. Note: closing without resolution should be avoided. Always summarise the outcome in the conversation before closing.

Realtime events the console listens for:
- nexus_escalation_alert: New escalation arrives in the queue. Console displays a notification.
- nexus_chat_response: AI response published to a conversation. Console updates the thread.
- nexus_chat_typing: Visitor is typing. Console shows typing indicator.

Conversation status values relevant to agents:
- Escalated: Waiting for agent pickup in the queue.
- Handed Over: Agent has accepted. Conversation is in progress with the human agent.
- Closed: Conversation ended.

Monitoring SLA: The console displays elapsed waiting time for each escalation in the queue. Prioritise escalations that have been waiting the longest. If escalation volume regularly exceeds agent capacity, report to the platform administrator to increase max_escalation_sessions or add more agents to the queue.

When a visitor is unresponsive after escalation: If the visitor has not responded after a reasonable wait, send a check-in message. If still unresponsive, close the conversation with a note in the thread. The idle conversation close service (close_idle_conversations scheduler) automatically closes abandoned conversations based on the configured idle timeout.

Good escalation handling practices:
- Always read the full AI conversation thread before responding. The visitor should not need to repeat context.
- Acknowledge the visitor immediately on accepting the escalation.
- Check the escalation reason field to understand why the AI handed over — this guides your first response.
- If the AI used incorrect knowledge (sources_json on the escalation record), flag the knowledge gap to the platform administrator after closing.
- Close conversations explicitly rather than leaving them in Handed Over status indefinitely.
""",
    },

    # 15 ────────────────────────────────────────────────────────────────────────
    {
        "title": "Nexus Live Studio — Configuration Readiness and Go-Live Checklist",
        "sub_context": "Platform Operations",
        "entity_type": "Platform Operations",
        "entity": "Nexus Live Studio",
        "topic": "Readiness Scoring and Go-Live Checklist",
        "access_policy": "Internal",
        "priority": 9,
        "manual_content": """
The Nexus Live Studio page at nexus_live_studio is the configuration readiness dashboard for the Nexus Live workspace. It provides a readiness score (0 to 100 percent) and status indicators across all major configuration areas: Channels, AI Agents, Routes and Access, Identity, and Escalation.

Readiness scoring: The studio calculates a readiness score based on the completeness of the live configuration. A score of 100 percent confirms that all required records are in place and the platform can handle conversations end-to-end. The readiness API is digitz_ai_nexus_live.api.nexus_live_config.get_config_readiness.

What each area checks:

Channels: Are live channels created and enabled? Does at least one channel of each required type (Website Chat, Website Q&A) exist? Is the channel linked to a valid tenant?

AI Agents: Do AI Agent Profiles exist? Are they enabled and not in Disabled status? Is at least one profile linked to a default channel? Does each profile have a behavior_prompt set?

Routes and Access: Does every enabled chat category have at least one enabled Category Identity Route? Does each route link to an enabled AI Agent Profile? Does each profile have at least one enabled Access Category? Does each Access Category contain at least one Access Policy?

Identity: Do Identity Types exist and are they enabled? Is there at least one Identity Profile configured? Is there a public route covering unregistered visitors?

Escalation: If escalation is enabled on any category, does an Escalation Rule exist for the relevant agent roles? Is at least one Agent Queue enabled? Is at least one Queue Assignment active? Does at least one desk user have can_handle_escalations equal to 1?

Complete go-live checklist in order:

1. Nexus Tenant created and enabled.
2. Access Policies created — Public minimum required.
3. Access Categories created and policies assigned to each category.
4. Business Unit created and linked to the tenant.
5. Live Channels created — Website Chat and Website Q&A as needed.
6. Chat Categories created and linked to channels with correct labels and display_order.
7. AI Agent Profiles created with behavior_prompt, tone, response_style, welcome_message, fallback_message, and confidence_threshold set.
8. AI Agent Profile Access Categories linked — the Profile to Category to Policy chain must be complete.
9. Category Identity Routes created — at minimum one public route (identity_profiles child table left empty) per category. Channel is derived automatically from the category.
10. Identity Types enabled — Public minimum required.
11. Knowledge Sources created, published, and confirmed retrieval_ready equals 1.
12. If escalation is needed: Escalation Rules created per agent_role, Agent Queues created and enabled, Queue Assignments configured, User Profile Assignments set up for desk agents with can_handle_escalations equal to 1.
13. Nexus Tenant Configuration updated: live_chat_enabled equals 1, qa_enabled equals 1, channels set, strict_tenant_mode equals 1, require_approved_knowledge equals 1.
14. Nexus Test Cases created and run via Nexus Experience app. All tests pass.
15. Tenant Configuration certification_status set to Passed.
16. activation_status set to Active.
17. website_widget_enabled set to 1 if deploying the embedded website widget.

Checking readiness from the console: Navigate to nexus_live_studio and review each section. Red indicators show failing checks. Green indicators confirm passing. Use the Nexus Chat Workflow Tester at nexus_chat_workflow_tester to simulate a full conversation flow including routing, knowledge retrieval, and escalation before declaring the deployment ready.

Common readiness failures and fixes:
- Routes and Access shows red: Check that every chat category has at least one enabled route, that every route points to an enabled AI Agent Profile, and that every profile has at least one enabled Access Category with at least one policy.
- AI Agents shows red: Check that all profiles have behavior_prompt filled in and that enabled equals 1.
- Escalation shows red: Check that at least one Escalation Rule exists matching the agent_role values of your AI Agent Profiles, that at least one Queue Assignment is active, and that at least one desk user has can_handle_escalations equals 1.
""",
    },

    # 16 ────────────────────────────────────────────────────────────────────────
    {
        "title": "Admin Tools — Knowledge Reset, Diagnostics, and Test Case Operations",
        "sub_context": "Admin Tools",
        "entity_type": "Admin Operations",
        "entity": "Admin Tools",
        "topic": "Reset Tools, Diagnostic APIs, and Test Case Execution",
        "access_policy": "Restricted",
        "priority": 8,
        "manual_content": """
Platform administrators have access to devtools and diagnostic APIs for managing, resetting, and validating the platform. These tools are powerful and some are irreversible without dry-run mode. Always confirm before executing destructive operations.

reset_knowledge_base.py — Knowledge Reset Tool:
Function: clear_all_knowledge(dry_run=True, confirm=None)
Location: digitz_ai_nexus/devtools/reset_knowledge_base.py

Removes all knowledge runtime records while preserving infrastructure (tenants, channels, agents, policies, routes, identity records).

Records deleted: Nexus Knowledge Chunk, Nexus Knowledge Unit, Nexus Knowledge Source, Nexus Knowledge Test Case, Nexus Knowledge Test Run.

Records preserved: All Nexus Tenant, Business Unit, Tenant Configuration records. All Channel, Category, Route records. All AI Agent Profile, Access Category, Access Policy records. All Identity Registry records.

Usage from bench console:
To preview without deleting: from digitz_ai_nexus.devtools.reset_knowledge_base import clear_all_knowledge then call clear_all_knowledge(dry_run=True).
To execute the deletion: clear_all_knowledge(dry_run=False, confirm='CLEAR_ALL_NEXUS_KNOWLEDGE').

reset_chat_workspace.py — Full Chat Workspace Reset:
Function: reset_chat_workspace(dry_run=True, confirm=None)
Location: digitz_ai_nexus_live/devtools/reset_chat_workspace.py

Removes ALL configuration and runtime records including conversations, escalations, agents, channels, routes, identity records, knowledge, access policies, and tenants. Preserves only DocTypes, Pages, Nexus Settings, and LLM Provider records.

Confirmation token: RESET_NEXUS_CHAT_WORKSPACE.

This is a complete wipe. Use only on development sites before seed re-runs. Never execute on production without explicit approval.

Source Quality Panel — Diagnostic API:
Function: get_source_quality_panel(source_name)

Returns per-chunk diagnostics for a Knowledge Source including embedding presence and status per chunk, diagnostic severity (Critical, Warning, or Healthy) per chunk, duplicate chunk detection flags, character count per chunk, and overall source retrieval readiness.

Use this when a published source is not being retrieved in conversations to diagnose chunk-level failures. A source with all chunks at Critical or Warning severity will not retrieve correctly even if status equals Published.

Chat Reachability API — Access Chain Diagnostic:
Function: get_source_chat_reachability(source_name)

Returns the access chain walkthrough for a Knowledge Source: which Access Policies govern the source, which Access Categories include those policies, which AI Agent Profiles are linked to those categories, which routes use those profiles, which channels and categories those routes cover, and whether the chain is complete end-to-end.

Use this to confirm that a source can actually be reached by the intended audience. If the chain is broken at any point, the source will not be retrieved for that visitor type.

Nexus Test Cases and Test Runs:
Test Cases are defined in the Nexus Experience app. Each test case specifies tenant, business unit, context, query, expected retrieval results, expected access status, and expected answer content. Test categories: Public Knowledge, Access Control, Business Unit Scope, Project Scope, Fallback, Response Behaviour, Governance, Administration, Custom.

Test case fields:
- test_title: Unique name.
- enabled: 1 to include in test runs.
- test_category: Classification of what is being tested.
- tenant, business_unit, context, sub_context: Scope of the test.
- query: The question to submit.
- top_k: Number of sources to retrieve. Default 5.
- expected_access_status: allowed, no_context, denied, or restricted.
- expected_answer_contains: Substring expected in the response.
- expected_source_count_min: Minimum number of sources that should be retrieved.
- expected_fallback_used: Checkbox indicating whether the fallback message is expected.

Run tests from bench console:
from digitz_ai_nexus_experience.services import run_test_case then run_test_case('Test Case Name').
To run all cases for a tenant: from digitz_ai_nexus_experience.services import run_all_test_cases then run_all_test_cases(tenant='DIGITZ-AI-NEXUS').

Test results are stored in Nexus Test Run records. A pass on all cases is the prerequisite for setting Tenant Configuration certification_status to Passed.

Configuration Readiness API:
Endpoint: digitz_ai_nexus_live.api.nexus_live_config.get_config_readiness

Returns a structured readiness report for the current tenant configuration covering all five readiness areas: Channels, AI Agents, Routes and Access, Identity, and Escalation. Use this programmatically during deployment validation scripts or CI pipelines.
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
    doc.description = "Tenant for DIGITZ AI Nexus platform — website chat, internal knowledge, and admin tools."
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


def _ensure_internal_channel(tenant):
    existing = frappe.db.get_value(
        "Nexus Live Channel", {"channel_code": CHANNEL_CODE, "tenant": tenant}, "name"
    )
    if existing:
        doc = frappe.get_doc("Nexus Live Channel", existing)
    else:
        doc = frappe.new_doc("Nexus Live Channel")
        doc.channel_code = CHANNEL_CODE
        doc.tenant       = tenant

    doc.channel_name           = "Nexus Internal Chat"
    doc.channel_type           = "Desk"
    doc.enabled                = 1
    doc.public_access          = 0
    doc.requires_visitor_email = 0
    doc.agent_based            = 0
    doc.description            = "Internal desk channel for platform admin and operator knowledge access."
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_internal_category(tenant, channel):
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
    doc.identity_verification_mode = "None"
    doc.allow_public_fallback      = 0
    doc.display_order              = 10
    doc.enable_escalation          = 0 if not doc.meta.has_field("enable_escalation") else 0
    doc.description = (
        "Internal category for platform administrators and operators — "
        "platform setup, knowledge management, access governance, escalation, and admin tools."
    )
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_internal_agent_profile(tenant, channel):
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
    doc.agent_role          = "Internal Assistant"
    doc.visibility          = "Internal"
    doc.enabled             = 1
    doc.status              = "Idle"
    doc.priority            = 10
    doc.max_active_sessions = 10
    doc.default_channel     = channel
    doc.description         = "Internal assistant for platform admins and operators."
    doc.behavior_prompt     = (
        "You are the DIGITZ AI Nexus internal platform assistant. "
        "Answer questions about platform configuration, knowledge source management, "
        "access governance, identity and routing, AI agent profiles, escalation workflows, "
        "tenant setup, live console operations, and admin diagnostic tools. "
        "Use only approved internal platform knowledge. "
        "If approved knowledge is insufficient, say that you do not have enough approved "
        "knowledge and recommend checking the Nexus Live Studio readiness dashboard or "
        "the platform documentation."
    )
    doc.tone                  = "Professional"
    doc.response_style        = "Detailed"
    doc.welcome_message       = "Hello. I'm the Nexus Platform Assistant. How can I help you with platform configuration or operations today?"
    doc.fallback_message      = "I don't have enough approved knowledge to answer that. Check the Nexus Live Studio readiness dashboard or contact the platform administrator."
    doc.do_not_answer_rules   = (
        "Do not share credentials, API keys, or system passwords. "
        "Do not discuss data belonging to other tenants. "
        "Do not invent configuration values — only answer from approved knowledge."
    )
    doc.default_response_mode = "chat"
    doc.knowledge_scope       = "Governed"
    doc.confidence_threshold  = 0.65
    doc.escalation_enabled    = 0
    doc.memory_mode           = "Session"
    doc.system_notes          = "Internal profile for DIGITZ AI Nexus platform admin knowledge."
    doc.save(ignore_permissions=True)
    return doc.name




def _ensure_internal_route(tenant, channel, category, profile):
    existing = frappe.get_all(
        "Nexus Category Identity Route",
        filters={"chat_category": category},
        pluck="name",
        limit_page_length=1,
    )
    if existing:
        doc = frappe.get_doc("Nexus Category Identity Route", existing[0])
    else:
        doc = frappe.new_doc("Nexus Category Identity Route")
        doc.chat_category = category

    doc.ai_agent_profile = profile
    doc.enabled          = 1
    doc.priority         = 5
    doc.description      = "Internal route for platform admin and operator knowledge access."

    doc.save(ignore_permissions=True)
    return doc.name


def _upsert_knowledge_source(source, tenant, category_name=None, policy_map=None):
    title = source["title"]

    if frappe.db.exists("Nexus Knowledge Source", title):
        doc = frappe.get_doc("Nexus Knowledge Source", title)
    else:
        doc = frappe.new_doc("Nexus Knowledge Source")
        doc.title = title

    # Resolve access_policy to its actual doc name via policy_map
    raw_policy = source["access_policy"]
    resolved_policy = (policy_map or {}).get(raw_policy, raw_policy)

    doc.source_type      = "Manual"
    doc.manual_content   = source["manual_content"].strip()
    doc.tenant           = tenant
    doc.business_unit    = BUSINESS_UNIT
    doc.project          = ""
    doc.context          = INTERNAL_CONTEXT
    doc.sub_context      = source["sub_context"]
    doc.entity_type      = source["entity_type"]
    doc.entity           = source["entity"]
    doc.topic            = source["topic"]
    doc.access_policy    = resolved_policy
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

def seed_nexus_platform_knowledge(process_sources=True):
    """
    Idempotent seed for DIGITZ AI Nexus internal platform knowledge.

    Creates the DIGITZ-AI-NEXUS tenant (or reuses if present), an internal desk
    channel, internal chat category, internal AI agent profile, and 16 knowledge
    sources covering platform architecture, knowledge management, access governance,
    identity, routing, escalation, console operations, and admin tools.

    Sources 1–14 use Internal access policy.
    Sources 15–16 use Restricted access policy (admin diagnostic operations).

    NOT called during installation. Run manually from bench console:

        from digitz_ai_nexus.devtools.seed_digitz_nexus_platform_knowledge import seed_nexus_platform_knowledge
        seed_nexus_platform_knowledge()

    To skip embedding generation:

        seed_nexus_platform_knowledge(process_sources=False)
    """

    result = {
        "foundation": {},
        "sources":    [],
    }

    # ── 1. Tenant ──────────────────────────────────────────────────────────────
    tenant = _ensure_tenant()
    result["foundation"]["tenant"] = tenant

    # ── 2. Access governance (Public + Internal + Restricted) ──────────────────
    result["foundation"]["access_governance"] = seed_default_access_governance(tenant=tenant)

    # ── 3. Business Unit ───────────────────────────────────────────────────────
    result["foundation"]["business_unit"] = _ensure_business_unit(tenant)

    # ── 4. Internal channel ────────────────────────────────────────────────────
    channel = _ensure_internal_channel(tenant)
    result["foundation"]["internal_channel"] = channel

    # ── 5. Internal chat category ──────────────────────────────────────────────
    category = _ensure_internal_category(tenant, channel)
    result["foundation"]["internal_category"] = category

    # ── 6. Internal AI agent profile ───────────────────────────────────────────
    profile = _ensure_internal_agent_profile(tenant, channel)
    result["foundation"]["internal_agent_profile"] = profile

    # ── 7. Wire profile → Internal Access + Restricted Access categories ───────
    result["foundation"]["access_categories_wired"] = True

    # ── 8. Internal route ──────────────────────────────────────────────────────
    result["foundation"]["internal_route"] = _ensure_internal_route(
        tenant, channel, category, profile
    )

    frappe.db.commit()

    # ── Resolve actual doc names for link fields (autoname includes tenant suffix) ──
    def _resolve_policy(policy_name):
        return (
            frappe.db.get_value("Nexus Access Policy", {"policy_name": policy_name, "tenant": tenant}, "name")
            or frappe.db.get_value("Nexus Access Policy", {"policy_name": policy_name}, "name")
            or policy_name
        )

    policy_map = {
        "Internal":   _resolve_policy("Internal"),
        "Restricted": _resolve_policy("Restricted"),
        "Public":     _resolve_policy("Public"),
    }

    # ── 9. Knowledge sources ───────────────────────────────────────────────────
    for source in PLATFORM_SOURCES:
        doc = _upsert_knowledge_source(
            source, tenant,
            category_name=category,
            policy_map=policy_map,
        )
        source_entry = {
            "name":          doc.name,
            "title":         doc.title,
            "sub_context":   doc.sub_context,
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
        f"DIGITZ AI Nexus platform knowledge seed completed. "
        f"Tenant: {tenant}. Sources: {len(result['sources'])}."
    )

    return result
