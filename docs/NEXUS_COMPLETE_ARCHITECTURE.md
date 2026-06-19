# DIGITZ AI Nexus — Complete Implementation Architecture

> Last updated: 2026-06-17. Source of truth for all five Nexus apps.

---

## 1. App Family

```
digitz_ai_nexus           → AI Core (governed knowledge, retrieval, access, answer engine)
digitz_ai_nexus_live      → Live Runtime (chat sessions, routing, escalation, human handover)
digitz_ai_nexus_nexy      → Role-Based AI Operator (outbound campaigns + inbound Sales Companion live chat)
digitz_ai_nexus_experience → Validation (test cases, governance smoke tests)
digitz_ai_nexus_agentic   → Agentic Runtime (autonomous agents, Sales + Purchase capability packs)
```

**Key rules:**
- `digitz_ai_nexus_live` calls into `digitz_ai_nexus` services — never duplicates retrieval, access resolution, or prompt building.
- `digitz_ai_nexus_nexy` is a thin operator layer over `digitz_ai_nexus` and `digitz_ai_nexus_live` — never reimplements identity resolution, access governance, or retrieval.
- `digitz_ai_nexus_agentic` consumes `digitz_ai_nexus` knowledge/access infrastructure for context resolution — never reimplements it.
- `digitz_ai_nexus_experience` is read-only testing.
- No agent in `digitz_ai_nexus_agentic` writes to the database or calls external APIs directly — all actions go through registered tools and the approval engine.

---

## 2. App: `digitz_ai_nexus` — AI Core

**Root path:** `apps/digitz_ai_nexus/digitz_ai_nexus/`

### 2.1 Modules

| Module | Responsibility |
|---|---|
| `nexus_core` | Tenant, settings, business keywords |
| `nexus_knowledge` | Knowledge source lifecycle, chunks, embeddings, test runs |
| `nexus_access` | Access policies, categories, knowledge profile mapping |
| `nexus_ai` | LLM provider configuration |
| `nexus_operations` | Tenant configuration, query logging, user context |
| `nexus_security` | Security utilities (no DocTypes) |

### 2.2 DocTypes

#### nexus_core

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Tenant` | `tenant_name`, `tenant_code`, `disabled` | Multi-tenant root — every entity is scoped to a tenant |
| `Nexus Settings` | (Single) | Global platform settings |
| `Nexus Business Unit` | `name`, `tenant` | Organisational grouping of knowledge |
| `Nexus Business Keyword` | `keyword`, `category` | Topic classification vocabulary |
| `Nexus Keyword Category` | `category_name` | Groups keywords by domain |

#### nexus_knowledge

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Knowledge Source` | `title`, `source_type`, `tenant`, `business_unit`, `access_policy`, `status`, `retrieval_ready`, `chunk_count`, `embedding_status` | Root document for a knowledge asset (PDF, DOCX, manual text) |
| `Nexus Knowledge Unit` | `unit_name`, `tenant`, `source`, `content` | Individual logical unit within a source |
| `Nexus Knowledge Chunk` | `chunk_text`, `unit`, `source`, `tenant`, `embedding_vector`, `embedding_status` | Smallest retrievable fragment; embedding stored here |
| `Nexus Knowledge Index Entry` | `chunk`, `tenant`, `keyword_index` | Keyword index for hybrid search |
| `Nexus Knowledge Context Summary` | `source`, `tenant`, `summary_text` | Source-level summary for context injection |
| `Nexus Knowledge Test Case` | `query`, `expected_chunk`, `tenant` | Regression test for retrieval quality |
| `Nexus Knowledge Test Run` | `test_case`, `status`, `confidence`, `ran_on` | Execution record for a test case |

#### nexus_access

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Access Policy` | `policy_name`, `tenant`, `access_level`, `sensitivity`, `allowed_roles`, `allowed_designations` | Governs which users/roles may access knowledge |
| `Nexus Access Category` | `category_name`, `tenant`, `description` | Named grouping of access policies |
| `Nexus Access Category Policy` | (child) `category`, `policy` | Many-to-many: links policies to categories |
| `Knowledge Profile` | `profile_name`, `tenant`, `enabled`, `access_categories` (Table) | Defines a context profile with a set of allowed access categories |
| `Knowledge Profile Access Category` | (child) `access_category` | Child row of Knowledge Profile |

#### nexus_ai

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus LLM Provider` | `provider_name`, `model`, `api_key`, `embedding_model`, `tenant` | LLM and embedding endpoint configuration |

#### nexus_operations

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Tenant Configuration` | `tenant`, `ecosystem`, `llm_provider`, `is_default` | Active LLM/embedding configuration per tenant |
| `Nexus Query Log` | `tenant`, `query`, `answer`, `confidence`, `retrieval_count`, `status` | Audit log for every query |
| `Nexus User Context` | `user`, `tenant`, `business_unit`, `knowledge_profile` | Tracks active Studio context for a desk user |

### 2.3 Engine Layer (`engine/`)

```
engine/
├── access.py              Access resolution entry point
├── access_resolver.py     Computes final allowed policies from profile scope
├── retrieval.py           Orchestrates vector + keyword retrieval
├── embedding.py           Generates and stores embeddings
├── embeding.py            (legacy alias)
├── chunking.py            Document → chunk splitting
├── llm.py                 LLM call abstraction (OpenAI + pluggable)
├── prompt.py              Behavior-driven prompt construction
├── response_mode.py       Controls answer verbosity/format
└── retrieval_engine/
    ├── query_expansion.py     Expands user queries for broader recall
    ├── scoring.py             Hybrid BM25 + vector scoring
    ├── reranker.py            Cross-encoder re-ranking pass
    └── retrieval_debug.py     Debug payload builder
```

### 2.4 Services Layer (`services/`)

| File | Responsibility |
|---|---|
| `answer_service.py` | End-to-end: retrieval → prompt → LLM → format answer |
| `answer_formatter.py` | Formats raw LLM output per response mode |
| `semantic_index.py` | Maintains keyword index on chunk upsert |
| `knowledge_source_processor.py` | Parses source files → units → chunks |
| `tenant_context.py` | Resolves active tenant + ecosystem configuration |
| `ingestion/` | Document parsers (PDF, DOCX, TXT, manual) |

### 2.5 API Endpoints (`api/`)

| File | Whitelisted Functions |
|---|---|
| `query.py` | `ask()` — core RAG query (internal) |
| `knowledge.py` | `generate_chunks()` — trigger chunking for a Knowledge Unit |
| `retrieval.py` | Internal retrieval helpers |
| `embedding.py` | Internal embedding trigger |
| `nexus_knowledge_studio.py` | `get_administration_snapshot()`, `get_user_context_snapshot()`, `set_active_user_context()`, `get_selector_options()`, `get_tenant_configuration_snapshot()`, `save_ecosystem_configuration()`, `save_tenant_configuration()` |
| `nexus_administration.py` | `get_administration_snapshot()`, `get_user_context_snapshot()`, `set_active_user_context()`, `get_selector_options()`, `get_tenant_configuration_snapshot()`, `save_ecosystem_configuration()`, `save_tenant_configuration()` |
| `nexus_knowledge_source_assist.py` | `get_knowledge_source_fields()` — Studio source listing/detail helpers |
| `setup.py` | `create_default_access_policies()` — install-time seed |

### 2.6 Frappe Pages

| Page | Route | Workspace |
|---|---|---|
| `nexus_studio_page` | `/nexus-studio` | **Nexus Studio** — knowledge authoring and indexing |
| `nexus_admin` | `/nexus-admin` | **Nexus Admin** — tenant/configuration/governance dashboard |

---

## 3. App: `digitz_ai_nexus_live` — Live Chat Runtime

**Root path:** `apps/digitz_ai_nexus_live/digitz_ai_nexus_live/`

### 3.1 Modules

| Module | Responsibility |
|---|---|
| `nexus_live_agents` | AI agent profiles, human agents, intent handlers |
| `nexus_live_channels` | Channels, chat categories, identity types & registry |
| `nexus_live_conversations` | Sessions, messages, feedback |
| `nexus_live_escalations` | Escalation rules, queues, assignment |
| `nexus_live_analytics` | Outcome logging, performance snapshots, lead capture |
| `digitz_ai_nexus_live` (root) | AI behaviour global config (Single DocType) |

### 3.2 DocTypes

#### nexus_live_agents

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus AI Agent Profile` | `agent_code`, `tenant`, `agent_name`, `display_name`, `nickname_pool`, `agent_role`, `enabled`, `status`, `max_active_sessions`, `confidence_threshold`, `behavior_prompt`, `welcome_message`, `fallback_message`, `default_response_mode` | AI chatbot configuration — one per business purpose |
| `Nexus AI Agent Profile Instance` | `profile`, `tenant`, `status`, `current_sessions` | Stateful runtime instance of an agent profile |
| `Nexus Live Agent` | `agent_name`, `user` (→ Frappe User), `nickname`, `enabled`, `chat_categories` (Table) | Human support agent record; gates access to agent console |
| `Nexus Live Agent Chat Category` | (child) `chat_category` | Categories a human agent handles |
| `Nexus Agent Activity Log` | `agent`, `action`, `conversation_id`, `timestamp` | Audit trail for human agent actions |
| `Nexus User Profile Assignment` | `user`, `ai_agent_profile`, `tenant` | Assigns a specific AI profile to a desk user |
| `Nexus Chat Category Link` | (child) `category` | Links chat categories to a profile |
| `Nexus Intent Handler` | `intent_code`, `profile`, `handler_type`, `action` | Structured response overrides per intent |
| `Nexus Profile Intent Override` | (child) `intent`, `handler` | Maps intents to handlers within a profile |

#### nexus_live_channels

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Live Channel` | `channel_code`, `tenant`, `channel_name`, `channel_type`, `enabled`, `default_agent`, `public_access`, `requires_visitor_email` | Logical entry point/context — website chat, mobile, desk, API, campaign, support surface |
| `Nexus Chat Category` | `category_code`, `category_label`, `channel`, `tenant`, `enabled`, `published`, `visibility`, `identity_verification_mode`, `allow_public_fallback`, `enable_escalation`, `faq_questions` | Visitor-facing topic/service. Belongs to one channel, so selecting the category implies the channel. |
| `Nexus Chat Category FAQ` | (child) `question`, `answer` | Pre-built FAQ answers for a category |
| `Nexus Identity Type` | `type_code`, `type_label`, `description` | Named identity classes (e.g. Employee, Customer, Partner) — intentionally global, not tenant-scoped |
| `Nexus Identity Registry` | `registry_name`, `description`, `enabled` | Registry of verified identities — intentionally global |
| `Nexus Registered Identity` | `identity_value`, `registry`, `identity_type` | One verified entity in a registry |
| `Nexus Registry Identity Profile` | (child) `identity_type`, `knowledge_profile` | Maps an identity type → Knowledge Profile within a registry |
| `Nexus Identity Profile` | `profile_name`, `tenant`, `enabled` | Named identity context within a tenant |
| `Nexus Identity Profile Mapping` | `identity_profile`, `knowledge_profile` | Maps identity profile → Knowledge Profile for access resolution |
| `Nexus Identity Knowledge Rule` | `identity_type`, `knowledge_profile`, `rule_label` | Directly links identity type to knowledge profile |
| `Nexus Identity Safe Guard Access Category` | (child) `access_category` | Access categories allowed for an identity type as a safety cap |
| `Nexus Identity Type Safe Guard Category` | (child) `access_category` | Second child for safe guard limits |
| `Nexus Category Identity Route` | `channel`, `chat_category`, `ai_agent_profile`, `identity_profiles`, `enabled`, `published`, `priority` | Routes a selected chat category and visitor identity context to the AI behavior profile and identity/knowledge access chain. Channel is derived from the category context and retained for filtering/reporting. |
| `Nexus Route Identity Profile` | (child) `identity_type`, `identity_profile` | Per-identity profiles within a route |
| `Nexus Identity Verification Challenge` | `conversation`, `challenge_type`, `status`, `challenge_sent_at` | Active identity challenge in progress |
| `Nexus Website Widget` | `widget_name`, `tenant`, `position`, `primary_color` | Embeddable chat widget configuration. The widget may load all published External/Both categories under enabled Website Chat channels for the tenant; visitors select categories, not channels. |

#### nexus_live_conversations

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Live Conversation` | `conversation_id`, `conversation_type`, `channel`, `chat_category`, `resolved_identity_type`, `identity_registry`, `visitor_name`, `visitor_email`, `user_type`, `assigned_agent`, `assigned_ai_agent_profile`, `status`, `intent`, `confidence`, `escalation_status`, `escalated_at`, `human_agent`, `started_on` | Central session record for every chat |
| `Nexus Live Message` | `conversation`, `sender_type`, `sender_name`, `message`, `response_type`, `sent_at` | Individual message within a conversation |
| `Nexus Conversation Feedback` | `conversation`, `rating`, `comment`, `submitted_at` | Visitor satisfaction rating |
| `Nexus Conversation Participant` | (child) `user`, `role` | Tracks multiple participants in a session |

#### nexus_live_escalations

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Live Escalation` | `conversation`, `reason`, `status`, `created_at`, `resolved_at` | Active or resolved escalation record |
| `Nexus Escalation Rule` | `rule_name`, `trigger`, `priority`, `action`, `tenant` | Configurable rules that trigger escalation |
| `Nexus Agent Queue` | `queue_name`, `tenant`, `categories` | Named queue of human agents |
| `Nexus Queue Assignment` | `queue`, `human_agent`, `active` | Assigns a human agent to a queue |

#### nexus_live_analytics

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Live Interaction Log` | `conversation`, `event_type`, `payload`, `logged_at` | Fine-grained interaction events |
| `Nexus Conversation Outcome` | `conversation`, `outcome_type`, `resolved_by`, `notes` | Final outcome classification per conversation |
| `Nexus Agent Performance Snapshot` | `agent`, `period`, `conversations_handled`, `avg_response_time`, `resolution_rate` | Periodic human agent performance summary |
| `Nexus Lead Capture` | `conversation`, `name_value`, `email`, `phone`, `captured_at` | Lead extracted from chat session |

#### Root module (Single DocType)

| DocType | Purpose |
|---|---|
| `Nexus AI Behaviour` | (Single) — global AI behaviour defaults used when no profile-level config exists |

### 3.3 Services Layer (`services/`)

| File | Responsibility |
|---|---|
| `live_chat_service.py` | `start_live_chat()`, `continue_live_chat()`, `_process_ai_response()` background job |
| `live_qa_service.py` | Desk Q&A (non-session AI query for internal users) |
| `conversation_service.py` | CRUD for conversations and messages, `mark_escalated()` |
| `escalation_service.py` | `create_escalation()`, `should_escalate()`, escalation trigger rules |
| `chat_realtime.py` | All `publish_*` realtime event helpers |
| `agent_router.py` | `assign_agent()` — selects right AI agent profile for a conversation |
| `agent_service.py` | `set_agent_status()`, `get_agent_behavior()` |
| `profile_resolver.py` | Behavior resolution priority chain; `_is_desk_user()`, `_is_nexus_live_agent_only()` |
| `identity_resolver.py` | Resolves identity type from conversation context |
| `identity_verification.py` | Challenge/response identity verification flow |
| `conversation_context_service.py` | Enriches query payload with conversation history |
| `intent_handler_service.py` | Checks for and executes structured intent overrides |

### 3.4 API Endpoints (`api/`)

#### Public / Guest-accessible

| Endpoint | Function | Access |
|---|---|---|
| `api/live.py` | `get_channel_categories(channel, visitor_email)` | Guest |
| `api/live.py` | `get_widget_tenant()` | Guest |
| `api/live.py` | `ask_question(payload)` | Guest |
| `api/live.py` | `start_chat(payload)` | Guest |
| `api/live.py` | `send_chat_message(conversation_id, payload)` | Guest |

#### Authenticated (desk users / admins)

| Endpoint | Function | Notes |
|---|---|---|
| `api/live.py` | `get_available_categories_for_tenant(tenant)` | — |
| `api/live.py` | `get_active_conversations(limit, tenant)` | Agent mode: Escalated only; Admin: all statuses |
| `api/live.py` | `get_conversation_detail(conversation_id)` | — |
| `api/agent_console.py` | `get_agent_context()` | Returns `{is_agent, agent, nickname, categories[]}` |
| `api/agent_console.py` | `claim_conversation(conversation_id)` | Human agent takes ownership |
| `api/agent_console.py` | `agent_send_message(conversation_id, message)` | Human agent reply |
| `api/agent_console.py` | `resolve_escalation(conversation_id)` | Returns to AI |
| `api/agent_console.py` | `close_conversation_by_agent(conversation_id)` | Hard close |
| `api/live_studio.py` | `get_live_studio_snapshot()` | Dashboard metrics |
| `api/live_studio.py` | `get_overview_metrics()` | Stats (open/escalated/etc.) |
| `api/live_studio.py` | `get_workforce_agents()` | Human agent list |
| `api/live_studio.py` | `get_channels()` | Channel list |
| `api/live_studio.py` | `get_escalation_rules()` | Escalation rules |
| `api/nexus_live_config.py` | `get_config_readiness()` | Health check (channels/agents/routes/identity/escalation) |
| `api/nexus_ai_agent_profile_manager.py` | `get_page_data()`, `get_profiles()`, `get_profile()`, `save_profile()`, `delete_profile()`, `toggle_profile()` | AI profile CRUD |
| `api/nexus_chat_category_manager.py` | `get_page_data()`, `get_channel_categories()`, `get_category_chain()`, `save_category()`, `delete_category()`, `toggle_category()`, `toggle_published()`, `test_chat_connectivity()` | Category management |
| `api/nexus_identity_registry.py` | `get_page_data()`, `get_registry()`, `save_registry()`, `toggle_registry()` | Registry CRUD |
| `api/nexus_category_profile_router.py` | `get_page_data()`, `get_channel_categories()`, `get_category_routes()`, `create_identity_profile()`, `get_route()`, `save_route()`, `toggle_route()`, `delete_route()`, `get_route_chain()` | Route management |
| `api/nexus_profile_access_allocation.py` | `get_page_data()`, `get_available_tenants()`, `get_profile_detail()`, `save_knowledge_profile_categories()`, `get_available_identity_types()`, `create_identity_knowledge_rule()`, `delete_identity_knowledge_rule()`, `create_knowledge_profile()`, `get_category_policies()` | Profile-to-category assignment |
| `api/nexus_channel_setup_wizard.py` | `get_wizard_data()`, `get_categories_for_channel()`, `save_category()`, `save_agent_profile()`, `save_route()` | Guided channel setup |
| `api/nexus_identity_profile_manager.py` | Identity profile page CRUD |
| `api/nexus_identity_verification_monitor.py` | `get_challenges()` — view active verification challenges |
| `api/nexus_knowledge_explorer.py` | Knowledge search/browse for desk users |
| `api/nexus_user_profile_manager.py` | `get_page_data()`, `get_user_data()`, `deactivate_assignment()` |
| `api/nexus_chat_workflow_tester.py` | End-to-end chat workflow tester for admins |
| `api/identity_verification.py` | Identity challenge management API |

### 3.5 Frappe Pages (Workspaces)

| Page | Route | Purpose |
|---|---|---|
| `nexus_live_console` | `/nexus-live-console` | **Nexus Live** — real-time conversation monitor + human handover panel |
| `nexus_live_studio` | `/nexus-live-studio` | Overview dashboard (metrics, agents, channels) |
| `nexus_ai_agent_profile_manager` | `/nexus-ai-agent-profile-manager` | Manage AI agent profiles |
| `nexus_chat_category_manager` | `/nexus-chat-category-manager` | Manage chat categories and FAQ |
| `nexus_category_profile_routes` | `/nexus-category-profile-routes` | View configured routing chains |
| `nexus_category_route_editor` | `/nexus-category-route-editor` | Edit identity routing rules |
| `nexus_channel_setup_wizard` | `/nexus-channel-setup-wizard` | Guided channel + agent + route setup |
| `nexus_identity_profile_manager` | `/nexus-identity-profile-manager` | Manage identity profiles |
| `nexus_identity_registry_manager` | `/nexus-identity-registry-manager` | Manage identity registries |
| `nexus_identity_verification_monitor` | `/nexus-identity-verification-monitor` | Monitor live verification challenges |
| `nexus_knowledge_explorer` | `/nexus-knowledge-explorer` | Browse knowledge chunks (desk users) |
| `nexus_profile_access_allocation` | `/nexus-profile-access-allocation` | Assign access categories to knowledge profiles |
| `nexus_user_profile_manager` | `/nexus-user-profile-manager` | Assign AI profiles to desk users |
| `nexus_chat_workflow_tester` | `/nexus-chat-workflow-tester` | Test full chat flows end-to-end |

### 3.6 Public Assets

| Asset | Purpose |
|---|---|
| `public/js/nexus_chat_widget.bundle.js` | Source for the embeddable chat widget (minified + bundled via `bench build --app digitz_ai_nexus_live`) |
| Current bundle hash | `DN5UMGH2` — update in all three `www/*.html` pages after every build |

---

## 4. App: `digitz_ai_nexus_agentic` — Agentic Runtime

**Root path:** `apps/digitz_ai_nexus_agentic/digitz_ai_nexus_agentic/`  
**Full reference:** `apps/digitz_ai_nexus_agentic/docs/AGENTIC_ARCHITECTURE.md`

### 4.1 Modules

| Module | Purpose |
|---|---|
| `nexus_agentic_core` | Generic runtime: candidates, capability packs, goals, tools, runs, approvals, memory, decision logs |
| `nexus_agentic_business` | Cross-capability services: capability resolution, channel adapters, context building |
| `nexus_agentic_sales` | Sales Outreach capability: campaigns, outreach drafts, reply classification, suppression |
| `nexus_agentic_purchase` | Purchase Coordination capability: supplier follow-up, RFQ drafting, vendor message drafts |

### 4.2 Core DocTypes (Nexus Agentic Core — 16 DocTypes)

| DocType | Autoname | Purpose |
|---|---|---|
| `Nexus Agent Candidate` | `CAND-{code}` | Agent identity (Nexy = `CAND-NEXY`), type, approval policy |
| `Nexus Agent Candidate Profile` | `CANDPROF-{#####}` | Behaviour prompt, strategy prompt, do-not-do rules |
| `Nexus Agent Capability Pack` | `CAP-{code}` | Domain-scoped bundle of goals, tools, workflows, approval rules |
| `Nexus Candidate Capability Assignment` | `CCA-{#####}` | Links candidate to capability pack with priority and goal routing |
| `Nexus Capability Goal Type` | `CGT-{#####}` | Supported goal type within a pack with risk and approval flag |
| `Nexus Capability Tool Assignment` | `CTA-{#####}` | Tool registered to a capability pack |
| `Nexus Capability Workflow` | `CWF-{#####}` | State transition rules for goals |
| `Nexus Capability Approval Rule` | `CAR-{#####}` | Per-action approval configuration with approver role/user |
| `Nexus Capability Memory Rule` | `CMR-{#####}` | Memory type retention and sensitivity rules per pack |
| `Nexus Agent Goal` | `GOAL-{#####}` | A single goal instance submitted to an agent |
| `Nexus Agent Tool` | `TOOL-{code}` | Registry of all executable tools with handler module |
| `Nexus Agent Run` | `RUN-{#####}` | One execution session: status, timing, input/output |
| `Nexus Agent Approval Request` | `APR-{#####}` | Human sign-off gate — `Pending → Approved/Rejected/Expired` |
| `Nexus Agent Tool Call` | `TCL-{#####}` | Audit record for every tool invocation |
| `Nexus Agent Memory` | `MEM-{#####}` | Persistent key-value memory per candidate/pack/tenant |
| `Nexus Agent Decision Log` | `DEC-{#####}` | Structured reasoning log with outcome |

### 4.3 Seeded Data (installed via `after_install`)

| Entity | Count | Details |
|---|---|---|
| Candidates | 1 | Nexy (`CAND-NEXY`) — Business Operator |
| Candidate Profiles | 1 | Nexy Default Profile — includes 9 do-not-do rules |
| Capability Packs | 2 | `CAP-SALES` (enabled), `CAP-PURCHASE_COORDINATION` (disabled) |
| Capability Assignments | 2 | Nexy → Sales (priority 10), Nexy → Purchase (priority 20) |
| Goal Types | 18 | 9 per pack |
| Agent Tools | 27 | 15 Sales + 12 Purchase |

### 4.4 Sales DocTypes (13 DocTypes)

`Nexus Sales Strategy`, `Nexus Sales Campaign`, `Nexus Sales Audience Segment`, `Nexus Sales Lead Source`, `Nexus Sales Lead Score`, `Nexus Sales Outreach Draft`, `Nexus Sales Outreach Event`, `Nexus Sales Follow Up Rule`, `Nexus Sales Reply Classification`, `Nexus Sales Objection Library`, `Nexus Sales Playbook`, `Nexus Sales Notification Rule`, `Nexus Sales Suppression List`

### 4.5 Purchase DocTypes (6 DocTypes)

`Nexus Purchase Coordination Strategy`, `Nexus Purchase Coordination Task`, `Nexus Purchase Vendor Message Draft`, `Nexus Purchase Coordination Event`, `Nexus Purchase Reply Classification`, `Nexus Purchase Follow Up Rule`

### 4.6 Safety Constraints

- No direct LLM → database writes — all state changes through registered `Nexus Agent Tool` records
- No direct LLM → external API calls — customer/vendor-facing tools raise `NotImplementedError` until called through an `Approved` `Nexus Agent Approval Request`
- All outreach drafts created with `approval_status = Draft` — sending requires explicit human approval
- Suppression list checked before any outreach attempt

---

## 5. App: `digitz_ai_nexus_nexy` — Role-Based AI Operator

**Root path:** `apps/digitz_ai_nexus_nexy/digitz_ai_nexus_nexy/`  
**Full reference:** `apps/digitz_ai_nexus_nexy/docs/NEXY_MVP_DESIGN.md`

### 5.1 Modules

| Module | Purpose |
|---|---|
| `nexus_nexy` | Generic interface layer — DocTypes that apply to every role |
| `nexus_nexy_sales` | Sales role implementation (MVP) |

### 5.2 Generic DocTypes (10 DocTypes, `nexus_nexy` module)

| DocType | Autoname | Purpose |
|---|---|---|
| `Nexy Role Profile` | `{profile_name}-{tenant}` | Behaviour contract for any role (tone, CTA style, do/dont rules, escalation policy) |
| `Nexy Engagement Persona` | `{persona_name}-{tenant}` | Target profile for any role (industry, org size, known needs) |
| `Nexy Engagement Target` | `NTARGET-.YYYY.-.#####` | Identity + lifecycle + consent for any target — links to role extension via Dynamic Link |
| `Nexy Persona Match` | `NPMATCH-.YYYY.-.#####` | LLM-generated match result: score, level, detected needs, recommended strategy |
| `Nexy Engagement Campaign` | `NCAMPAIGN-.YYYY.-.#####` | Campaign: links role profile, persona, knowledge profile, channel, approval mode |
| `Nexy Engagement Message` | `NMSG-.YYYY.-.#####` | Generated outreach message with chat invitation token, approval status, lifecycle |
| `Nexy Engagement Event` | `NEVT-.YYYY.-.#####` | Append-only audit timeline for any campaign/target/message |
| `Nexy Engagement Feedback` | `NFEEDBACK-.YYYY.-.#####` | Role-neutral classified response: sentiment, intent, engagement level, escalation flag |
| `Nexy Conversation Link` | `NCONVLINK-.YYYY.-.#####` | Links a Nexus Live Conversation back to a campaign/target/message |
| `Nexy Companion Assignment` | `NCA-{chat_category}` | Maps a Nexus Chat Category → Nexy Role Profile; enables Sales Companion mode for inbound live chat |

### 5.3 Sales Role DocTypes (Phase 2, `nexus_nexy_sales` module)

| DocType | Extends | Key additional fields |
|---|---|---|
| `Nexy Prospect` | `Nexy Engagement Target` | company_name, contact_person, industry, deal_stage, estimated_value |
| `Nexy Customer Persona` | `Nexy Engagement Persona` | pain_points, buying_triggers, budget_indicators, objection_patterns |
| `Nexy Sales Profile Extension` | `Nexy Role Profile` | selling_style, persuasion_style, objection_handling_style, pricing_policy |
| `Nexy Sales Feedback` | `Nexy Engagement Feedback` | asked_pricing, asked_demo, buying_signal, recommended_sales_action |

### 5.4 Services Layer

```
services/
├── nexy_identity_service.py       Thin adapter over identity_resolver + access_resolver
├── nexy_context_service.py        Builds context dicts for LLM (generic + role extension)
├── nexy_knowledge_service.py      Calls run_retrieval_pipeline (no new retrieval code)
├── nexy_persona_match_service.py  Dispatcher → role persona_handler
├── nexy_message_generation_service.py Dispatcher → role message_handler
├── nexy_guardrail_service.py      Validates messages against role_profile rules
├── nexy_engagement_service.py     Token/invitation lifecycle, event recording
├── nexy_chat_activation_service.py Token resolution → live_chat_service hook
├── nexy_companion_service.py      Builds 7-layer Sales Companion system prompt (Phase SC-1)
├── nexy_live_response_service.py  Companion enrichment + campaign context hook in _process_ai_response
├── nexy_feedback_service.py       Dispatcher → role feedback_handler
├── nexy_import_service.py         Creates generic + role extension records from CSV/data
└── roles/
    ├── default/                   Fallback handlers for unknown role types
    └── sales/                     Sales role handlers (MVP): context_builder, persona_handler,
                                   message_handler, feedback_handler
```

### 5.5 Extension Pattern

Every role-specific DocType follows the same FK pattern:

```
Nexy Engagement Target (generic)
  └── role_extension_doctype = "Nexy Prospect"
  └── role_extension_name = "NPROSPECT-2026-00001"

Nexy Prospect (sales extension)
  └── engagement_target = Link → Nexy Engagement Target
```

Adding a new role = 4 DocTypes + 4 handler files + 1 line in `_load_handler()` dispatcher.

### 5.6 Key Governance Rules

- `do_not_contact = 1` on any target → blocks all Nexy processing, no exceptions
- Final knowledge scope = identity scope ∩ campaign scope. Empty = fail closed.
- LLM cannot see or modify `allowed_access_policies`
- `requires_grounding = 1` → every claim must have a retrieved source
- `requires_human_approval_for_outbound = 1` → message waits for human before chat link is generated

### 5.7 Implementation Status (as of 2026-06-18)

**Outbound Campaign Track:**

| Phase | Scope | Status |
|---|---|---|
| Phase 1 | App scaffold + 9 generic DocTypes + `nexy_identity_service.py` | ✅ Complete |
| Phase 2 | Sales role DocTypes (Prospect, CustomerPersona, SalesProfileExt, SalesFeedback) | Planned |
| Phase 3 | Persona matching (context_service, knowledge_service, persona_match_service, sales persona_handler) | Planned |
| Phase 4 | Message generation + guardrails | Planned |
| Phase 5 | Chat invitation + activation | Planned |
| Phase 6 | Live response enrichment (campaign context path) | Planned |
| Phase 7 | Feedback + status updates | Planned |
| Phase 8 | Import + dashboard | Planned |

**Sales Companion Track:**

| Phase | Scope | Status |
|---|---|---|
| Phase SC-1 | `Nexy Companion Assignment` DocType, `nexy_companion_service.py`, companion path in `nexy_live_response_service.py`, 3-line hook in `live_chat_service._process_ai_response()` | ✅ Complete |
| Phase SC-2 | `Nexy Conversation Link` creation for companion conversations | ✅ Complete |
| Phase SC-3 | Buy-signal feedback classification per response turn | Planned |
| Phase SC-4 | Visitor identity resolution during companion conversation | Planned |

**Installed on:** `digitz_ai_nexus.site`  
**Note:** `digitz_ai_nexus_nexy` must appear in `sites/apps.txt` for Frappe's module
map to include `nexus_nexy` and `nexus_nexy_sales` — confirmed required and fixed (2026-06-18).

---

## 6. App: `digitz_ai_nexus_experience` — Validation

**Root path:** `apps/digitz_ai_nexus_experience/digitz_ai_nexus_experience/`

| Module | Purpose |
|---|---|
| `nexus_testing` | `Nexus Test Case` DocType — structured test definitions |
| `nexus_governance` | Governance validation (no DocTypes yet) |
| `nexus_insights` | Analytics insights (no DocTypes yet) |
| `nexus_experience` | Experience validation (no DocTypes yet) |
| `nexus_widgets` | Widget config (no DocTypes yet) |

---

## 7. Public Website (`www/`)

All pages are in `apps/digitz_ai_nexus/digitz_ai_nexus/www/` — no bench build needed for inline `<style>` changes.

| File | URL | Purpose |
|---|---|---|
| `index.html` | `/` | Marketing home page (hero, governance animation, Know More Banner) |
| `nexus-platform.html` | `/nexus-platform` | Platform workspaces deep-dive (Studio, Live, Admin) |
| `how-nexus-works.html` | `/how-nexus-works` | 7-layer architecture documentation (Knowledge→Escalation) |

Nav links: `Home | Experience | Nexus Platform | Apps | Nexus Architecture | Chat with Us`

---

## 8. Frappe Roles

| Role | Purpose |
|---|---|
| `System Manager` | Full admin — sees all conversations, all modes in console |
| `Nexus Live Agent` | Human support agent — restricted console (Escalated only, assigned categories) |

**Role check pattern:** `_is_nexus_live_agent_only()` — True when user has `Nexus Live Agent` but NOT `System Manager`.

---

## 9. Realtime Events (Redis → Socket.IO)

| Event | Publisher | Subscriber | Payload |
|---|---|---|---|
| `nexus_chat_response` | `chat_realtime.publish_chat_response()` | Chat widget, Escalation panel | `{response_type, message, sender_type, conversation_id, ...}` |
| `nexus_chat_typing` | `chat_realtime.publish_chat_typing()` | Chat widget | Typing indicator before AI reply |
| `nexus_escalation_alert` | `chat_realtime.publish_escalation_alert()` | Live console (global) | Alerts assigned human agents of new escalation |
| `nexus_escalation_claimed` | `agent_console.claim_conversation()` | Live console (global) | Notifies other agents a conversation was claimed |

**Room:** All events broadcast to the `all` room (site room). Only System Users join `all`. Visitors receive via their own socket connection.

**`after_commit=True`** pattern: All `publish_*` calls in the background AI job use `after_commit=True` so realtime fires only after the DB commit, ensuring data visibility.

---

## 10. Core Data Flow — Visitor Chat

```
Visitor opens widget
    │
    ▼
GET widget categories for tenant
    → find enabled Nexus Live Channels where channel_type = Website Chat
    → return published External/Both Nexus Chat Categories from those channels
    │
    ▼
Visitor selects category → POST start_chat(payload)
    → selected category implies channel via Nexus Chat Category.channel
    → Creates Nexus Live Conversation (status: Open)
    → Resolves: Chat Category → implied Channel → Identity Type → Category Identity Route → AI Profile → Knowledge Profile
    → Launches background job: _process_ai_response()
    │
    ▼
Background job (_process_ai_response)
    1. get_conversation → get assigned AI agent profile
    2. _resolve_behavior() — priority: conversation profile > user assignment > category route > agent default
    3. set_agent_status("Responding") → publish_chat_typing [after_commit]
    4. build_core_chat_payload → answer_query (engine/answer_service.py)
       └─ access_resolver → allowed policies
       └─ retrieval_engine → scored chunks
       └─ prompt builder → LLM call → answer
    5. add_message(sender_type=AI) → DB commit → typing event fires
    6. set_agent_status("Waiting")
    7. Check escalation: user_requested_human AND profile.escalation_enabled AND category.enable_escalation
       └─ if true: create_escalation() → mark_escalated() → publish_escalation_alert()
    8. publish_chat_response [after_commit] → widget receives answer
```

---

## 11. Core Data Flow — Human Escalation

```
Escalation triggered (Low Confidence / User Requested / etc.)
    │
    ▼
escalation_service.create_escalation(reason)
    → Creates Nexus Live Escalation record
    → conversation_service.mark_escalated()
       → sets conversation.status = Escalated, escalated_at = now()
    → chat_realtime.publish_escalation_alert(conversation)
       → finds human agents for the category (Nexus Live Agent Chat Category child table)
       → publishes nexus_escalation_alert per agent user
    │
    ▼
Human Agent receives browser notification (console page)
    → Claims via agent_console.claim_conversation(conversation_id)
       → sets conversation.human_agent, escalation_status = Accepted
       → fires nexus_escalation_claimed → other agents see "Taken by [nickname]"
    │
    ▼
Agent replies via agent_console.agent_send_message()
    → Inserts Nexus Live Message (sender_type = Human Agent)
    → publish_chat_response with sender_type = "Human Agent"
    → Widget shows green agent bubble
    │
    ▼
Visitor messages while escalated → live_chat_service.continue_live_chat()
    → Stores message, sends holding response (AI skipped)
    → publish_chat_response(response_type = visitor_message) → agent panel appends it
    │
    ▼
Agent resolves → agent_console.resolve_escalation()
    → status = Responding, escalation_status = Resolved, human_agent cleared
    → resolves all pending Nexus Live Escalation records
    → sends system message: "You've been reconnected with our AI assistant…"
    → publish_chat_response(response_type = escalation_resolved)
    → Widget unlocks input, resumes AI path
```

---

## 12. Core Data Flow — Desk User Chat

```
Desk user (logged in) triggers NexusChatWidget.open()
    │
    ▼
POST start_chat — no channel, no guest roles
    → is_desk() = True (frappe.boot.user.name != 'Guest')
    → Conversation created with user_type = Desk User
    → Greeting returned in HTTP response (NOT realtime) to avoid race condition
    │
    ▼
Messages via send_chat_message
    → profile_resolver checks for Nexus User Profile Assignment
    → Falls back to category route or agent default
    → Normal AI pipeline
    ▲
    │
Note: Desk User conversations are EXCLUDED from the Live Console
(filtered by user_type != 'Desk User')
```

---

## 13. Identity Resolution Chain

```
Chat Category (identity_verification_mode)
    │
    ├─ None → use default identity type
    ├─ Email Lookup → check Nexus Identity Registry
    └─ Challenge → issue Nexus Identity Verification Challenge
         │
         ▼
Resolved Identity Type
    │
    ▼
Nexus Category Identity Route (chat category + implied channel + identity context)
    │
    ▼
AI Agent Profile + Knowledge Profile access chain
    │
    ▼
Access Categories → Access Policies → Knowledge Chunks

Identity Registry Safeguard:
    Nexus Identity Safe Guard Access Category caps allowed categories
    for verified identities BEFORE the route resolution intersects them.
```

---

## 14. Tenant Isolation Rules

| DocType | Isolation |
|---|---|
| Nexus Tenant, Nexus Settings, Business Unit, Keywords | Explicit `tenant` field |
| Knowledge Source, Unit, Chunk, Index Entry | Explicit `tenant` field |
| Access Policy, Access Category, Knowledge Profile | Explicit `tenant` field |
| Nexus Tenant Configuration, Query Log, User Context | Explicit `tenant` field |
| Nexus Live Channel, Chat Category | Explicit `tenant` field |
| Nexus AI Agent Profile, Live Agent | Explicit `tenant` field |
| Live Conversation, Message | Implicit via Channel → Tenant FK |
| Live Escalation, Feedback | Implicit via Conversation FK |
| **Nexus Identity Type** | **Intentionally GLOBAL** — not tenant-scoped |
| **Nexus Identity Registry** | **Intentionally GLOBAL** — shared across tenants |

---

## 15. Build & Deployment Notes

| Action | Command |
|---|---|
| Rebuild chat widget (JS changes) | `bench build --app digitz_ai_nexus_live` |
| Rebuild platform CSS (digitz_ai_nexus_site.css changes) | `bench build --app digitz_ai_nexus` |
| Apply DocType schema changes | `bench migrate` |
| Update bundle hash in www pages | Update `nexus_chat_widget.bundle.XXXXXXXX.js` in `index.html`, `nexus-platform.html`, `how-nexus-works.html` |
| www HTML inline `<style>` changes | Live immediately — no build needed |

---

## 16. File Map Quick Reference

```
digitz_ai_nexus/
├── docs/NEXUS_COMPLETE_ARCHITECTURE.md   ← this document
├── docs/architecture.md                  (partial — superseded by this file)
├── digitz_ai_nexus/
│   ├── nexus_core/doctype/               Tenant, Settings, BusinessUnit, Keywords
│   ├── nexus_knowledge/doctype/          KnowledgeSource, Unit, Chunk, Index, Tests
│   ├── nexus_access/doctype/             AccessPolicy, AccessCategory, KnowledgeProfile
│   ├── nexus_ai/doctype/                 NexusLLMProvider
│   ├── nexus_operations/doctype/         TenantConfig, QueryLog, UserContext
│   ├── engine/                           Access + Retrieval + Embedding + LLM + Prompt
│   ├── services/                         AnswerService, Ingestion, TenantContext
│   ├── api/                              query.py, knowledge.py, nexus_knowledge_studio.py
│   └── www/                              index.html, nexus-platform.html, how-nexus-works.html

digitz_ai_nexus_live/
├── docs/NEXUS_COMPLETE_ARCHITECTURE.md   (same doc — symlink or cross-reference)
├── digitz_ai_nexus_live/
│   ├── nexus_live_agents/doctype/        AIAgentProfile, LiveAgent, IntentHandler
│   ├── nexus_live_channels/doctype/      Channel, ChatCategory, IdentityType, Registry
│   ├── nexus_live_conversations/doctype/ Conversation, Message, Feedback
│   ├── nexus_live_escalations/doctype/   LiveEscalation, EscalationRule, AgentQueue
│   ├── nexus_live_analytics/doctype/     InteractionLog, Outcome, LeadCapture
│   ├── digitz_ai_nexus_live/doctype/     NexusAIBehaviour (Single)
│   ├── services/                         LiveChatService, EscalationService, Realtime
│   ├── api/                              live.py, agent_console.py, live_studio.py, ...
│   └── public/js/                        nexus_chat_widget.bundle.js (source)

digitz_ai_nexus_experience/
└── digitz_ai_nexus_experience/
    └── nexus_testing/doctype/            NexusTestCase

digitz_ai_nexus_nexy/
├── docs/NEXY_MVP_DESIGN.md               ← full Nexy reference (canonical)
└── digitz_ai_nexus_nexy/
    ├── nexus_nexy/doctype/               9 generic DocTypes: RoleProfile, EngagementPersona,
    │                                     EngagementTarget, PersonaMatch, EngagementCampaign,
    │                                     EngagementMessage, EngagementEvent, EngagementFeedback,
    │                                     ConversationLink
    ├── nexus_nexy_sales/doctype/         4 sales DocTypes: Prospect, CustomerPersona,
    │                                     SalesProfileExtension, SalesFeedback
    ├── nexus_nexy/workspace/             Nexus Nexy workspace (Frappe v15 desk visibility)
    └── services/
        ├── nexy_identity_service.py      Identity resolution adapter (Phase 1 — complete)
        └── roles/                        Role handler modules (sales/, default/)

digitz_ai_nexus_agentic/
├── docs/AGENTIC_ARCHITECTURE.md          ← full agentic reference (canonical)
└── digitz_ai_nexus_agentic/
    ├── nexus_agentic_core/doctype/       16 DocTypes: Candidate, CapabilityPack, Goal, Tool,
    │                                     Run, ApprovalRequest, ToolCall, Memory, DecisionLog, ...
    ├── nexus_agentic_business/           capability_service, communication_service,
    │                                     business_context_service, tools
    ├── nexus_agentic_sales/doctype/      13 DocTypes: Strategy, Campaign, Segment, OutreachDraft,
    │                                     OutreachEvent, ReplyClassification, Suppression, ...
    ├── nexus_agentic_sales/              strategy_service, lead_service, outreach_service,
    │                                     reply_service, suppression_service, notification_service
    ├── nexus_agentic_purchase/doctype/   6 DocTypes: CoordinationStrategy, CoordinationTask,
    │                                     VendorMessageDraft, CoordinationEvent, ReplyClassification
    ├── nexus_agentic_purchase/           strategy_service, supplier_service, document_service,
    │                                     message_service, reply_service, notification_service
    └── setup/install.py                  Seeds Nexy + 2 packs + 18 goal types + 27 tools
```
