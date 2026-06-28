# DIGITZ AI Nexus — Complete Implementation Architecture

> Last updated: 2026-06-28 (business companion controller, companion_milestone field, realtime dashboard, Nexus Sales Playbook removed). Source of truth for all five Nexus apps.

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
| `nexus_companion` | Controller-led LLM conversion engine — business milestones, external intent classification, journey stages, signal classification, enquiry lifecycle, persona matching, reference matching, realtime desk dashboard |

### 2.2 DocTypes

#### nexus_core

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Tenant` | `tenant_name`, `tenant_code`, `disabled` | Multi-tenant root — every entity is scoped to a tenant |
| `Nexus Settings` | (Single) `nexy_email_verification_mandatory` | Global platform settings. The `nexy_email_verification_mandatory` Check enforces that every "Use for Nexy" category must have identity verification configured before a Nexy handover can proceed. |
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
| `Nexus Knowledge Gap` | `query`, `tenant`, `channel`, `gap_type`, `access_status`, `confidence`, `frequency`, `semantic_key`, `status`, `detection_mode`, `llm_assessment_status`, `is_relevant`, `suggested_context`, `suggested_topic`, `llm_summary`, `suggested_knowledge_source`, `visitor_email`, `visitor_email_status`, `sample_queries_json` | Records questions the AI could not answer; drives the gap review workflow and visitor email follow-up |

#### nexus_access

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Access Policy` | `policy_name`, `tenant`, `access_level`, `sensitivity`, `allowed_roles`, `allowed_designations` | Governs which users/roles may access knowledge |
| `Nexus Access Category` | `category_name`, `tenant`, `description` | Named grouping of access policies |
| `Nexus Access Category Policy` | (child) `category`, `policy` | Many-to-many: links policies to categories |
| `Knowledge Profile` | `profile_name`, `tenant`, `enabled`, `access_categories` (Table) | Defines a context profile with a set of allowed access categories |
| `Knowledge Profile Access Category` | (child) `access_category`, `disabled` | Child row of Knowledge Profile. `disabled` (Check, default 0) — unchecked by default so rows are active; check to exclude a category without deleting the row. Only rows with `disabled=0` are included in policy resolution. |

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

#### nexus_companion

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Companion Product` | `product_name`, `tenant`, `enabled`, `chat_category`, `challenges_solved`, `objection_responses`, `disqualification_criteria`, `conversion_type`, `conversion_threshold_score`, `conversion_config`, `conversion_message`, `post_conversion_action` | Product intelligence profile — what Nexy knows about a product, how to present it, and how its conversion cycle completes |
| `Nexus Companion Product Persona` | (child) `persona` | Links a product to target personas |
| `Nexus Companion Service` | (same as Product) `service_name`, … | Service-level equivalent of Product |
| `Nexus Companion Service Persona` | (child) `persona` | Links a service to target personas |
| `Nexus Companion Persona` | `persona_name`, `tenant`, `enabled`, `industry`, `company_size`, `business_maturity`, `customer_type`, `challenges`, `goals`, `communication_style` | Visitor archetype — drives matching, message framing, and product recommendation |
| `Nexus Companion Persona Product` | (child) `product` | Persona → Product recommendation |
| `Nexus Companion Persona Service` | (child) `service` | Persona → Service recommendation |
| `Nexus Companion Playbook` | `playbook_name`, `tenant`, `enabled`, `is_default`, `discovery_questions`, `communication_guidelines`, `escalation_score_threshold`, `escalation_triggers`, `next_step_options` | Per-channel engagement playbook — discovery flow, guidelines, escalation thresholds |
| `Nexus Companion Story` | `title`, `tenant`, `approved`, `visibility`, `industry`, `challenge`, `solution`, `outcomes`, `summary` | Approved customer success story for trust-building |
| `Nexus Companion Story Product` | (child) `product` | Links story to products |
| `Nexus Companion Story Persona` | (child) `persona` | Links story to personas |
| `Nexus Companion Testimonial` | `tenant`, `approved`, `rating`, `testimonial`, `linked_product`, `linked_service` | Short customer testimonial (name/company optional) |
| `Nexus Companion Case Study` | `title`, `tenant`, `approved`, `visibility`, `customer_profile`, `initial_situation`, `outcomes`, `metrics` | Detailed case study for deeper social proof |
| `Nexus Companion Case Study Persona` | (child) `persona` | Links case study to personas |
| `Nexus Companion Outcome` | `outcome_label`, `outcome_category`, `tenant`, `approved`, `detail` | Discrete reusable outcome statement |
| `Nexus Companion Outcome Product` | (child) `product` | Links outcome to products |
| `Nexus Companion Outcome Persona` | (child) `persona` | Links outcome to personas |
| `Nexus Companion Enquiry` | `visitor`, `visitor_email`, `verification_status`, `web_session`, `conversation`, `tenant`, `enquiry_stage`, `companion_milestone`, `enquiry_score`, `matched_persona`, `stage_signal`, `signal_log`, `discovery_data`, `recommended_next_step`, `escalation_recommended` | Full journey record for a visitor — created automatically when companion mode is active; updated in real time. `companion_milestone` synced from the conversation each turn. |
| `Nexus Companion Enquiry Product` | (child) `product`, `product_name`, `fit_score` | Recommended product rows on an enquiry |
| `Nexus Companion Enquiry Service` | (child) `service`, `service_name`, `fit_score` | Recommended service rows on an enquiry |

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
| `answer_service.py` | End-to-end: retrieval → prompt → LLM → format answer. On fallback, calls `gap_detection_service.record_gap()` and enriches response with `email_followup_offer` flag when enabled. |
| `answer_formatter.py` | Formats raw LLM output per response mode |
| `semantic_index.py` | Maintains keyword index on chunk upsert |
| `knowledge_source_processor.py` | Parses source files → units → chunks |
| `tenant_context.py` | Resolves active tenant + ecosystem configuration |
| `gap_detection_service.py` | Records reactive and proactive Knowledge Gaps; deduplicates by semantic hash; enqueues LLM relevance assessment; provides scheduled jobs `detect_proactive_gaps` and `reassess_pending_gaps` |
| `gap_notification_service.py` | Sends visitor follow-up emails for resolved gaps. Provides `send_visitor_notification(gap_name)` (idempotent — commits status before sending to prevent duplicates) and `on_knowledge_source_published(doc, method)` (doc event handler that auto-fires on Knowledge Source status → Published) |
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
| `knowledge_gap.py` | **Gap Review (admin):** `get_gap_summary(tenant, status, gap_type, limit)`, `update_gap_status(gap_name, status)`, `create_knowledge_source_from_gap(gap_name, ...)`, `trigger_reassessment(gap_name)`, `trigger_proactive_detection(tenant)`, `notify_gap_visitor(gap_name)`, `get_sample_queries(gap_name)` · **Visitor email OTP (guest):** `request_gap_email_otp(gap_name, email)` — rate-limited, sends OTP via `nexus-gap-otp-verification` template · `verify_gap_email_otp(gap_name, challenge_token, otp)` — verifies OTP, saves email on gap · `submit_gap_visitor_email(gap_name, email, conversation_id)` — trusted path for already-verified visitors (no OTP) |

### 2.6 Frappe Pages

| Page | Route | Workspace |
|---|---|---|
| `nexus_studio_page` | `/nexus-studio` | **Nexus Studio** — knowledge authoring and indexing |
| `nexus_admin` | `/nexus-admin` | **Nexus Admin** — tenant/configuration/governance dashboard |

### 2.7 Nexus Companion Framework

The companion is a horizontal capability layered across the existing chat pipeline. Full documentation: `apps/digitz_ai_nexus/docs/nexus-companion-framework.md`.

**Purpose:** Intent-driven LLM conversion engine. Default intent is Sales — guide visitors from discovery to a completed conversion (enquiry captured, meeting booked, subscription activated). The LLM itself drives the conversion process; the platform supplies structured context, not a rule engine.

**Activation:** Set `companion_mode = 1` on a `Nexus AI Agent Profile`. All conversations on that profile enter companion mode automatically.

**Architecture — Controller-Led Mode**

The companion has two operating modes, selected per turn:

| Mode | Trigger | Description |
|---|---|---|
| `controlled_companion` | `business_companion_controller.handle_companion_turn()` | Controller owns all decisions; LLM only drafts within controller constraints. Active when the controller is invoked. |
| `companion_advisor` (prompt-injection) | Legacy path via `_build_companion_block()` in `prompt.py` | LLM drives the conversation guided by a structured context block. Used when the controller is not in the call path. |

**Services:**

| File | Responsibility |
|---|---|
| `nexus_companion/services/business_companion_controller.py` | **Controller** — owns milestone, steering, grounding, and response goal every turn. Classifies external intent, extracts discovery data, updates enquiry, advances journey stage, decides whether the LLM may use knowledge/tools/escalation. Three decisions bypass the LLM entirely (demo confirm, demo reject, next-step explain). |
| `nexus_companion/services/companion_intent_service.py` | LLM-powered **external intent** classification per message (15 intent types; fast keyword rules first, LLM as fallback). Returns `{intent, confidence, reason}`. |
| `nexus_companion/services/companion_context_service.py` | Assembles full companion context dict per AI turn (stage, persona, products block, references block, playbook guidelines) |
| `nexus_companion/services/enquiry_service.py` | Enquiry lifecycle — create/update/score/stage advance; signal-driven stage machine + score-based fallback. Also syncs `companion_milestone` from conversation to enquiry each turn and emits `companion_progress_update` realtime on stage change. |
| `nexus_companion/services/signal_classifier.py` | LLM-powered per-message **buying signal** classification (14 signal types; falls back to CURIOUS on failure). Distinct from external intent — signals describe visitor behaviour, intents describe what the visitor wants to do. |
| `nexus_companion/services/persona_matching_service.py` | Keyword/weighted scoring against persona fields to identify visitor archetype |
| `nexus_companion/services/reference_matching_service.py` | Retrieves relevant Stories, Testimonials, and Outcomes based on industry and persona |

**Controller Milestones (8) — written to `companion_milestone`:**
`onboarding_business → business_discovery → pain_discovery → solution_mapping → evidence_building → demo_arrangement → quotation → conversion`

Milestones are the controller's current objective. They are independent from journey stages (which are the funnel/reporting state). The controller reads `companion_milestone` directly; falls back to deriving from `companion_journey_stage` for conversations started before the field was introduced.

**Journey Stages (11) — written to `companion_journey_stage`:**
`ARRIVED → GREETING → DISCOVERY → ENGAGED → PRESENTING ⇌ OBJECTION_HANDLING → INTERESTED → CONVERTING → CONVERTED / DECLINED / ESCALATED`

Stage transitions are signal-driven. Every visitor message is classified as one of 14 signal types by the LLM. The signal type determines stage transition. Score-based advancement (0–100 composite score) is retained as a safety-net fallback.

**Grounding modes (set by `_apply_grounding_policy`):**

| Mode | Meaning |
|---|---|
| `nexus_knowledge_only` | Knowledge is fetched before LLM call; LLM must answer from confirmed chunks only |
| `controller_only` | LLM drafts freely within controller steering and response_goal |
| `no_llm_direct` | Controller returns a fixed hardcoded response — LLM not called |

**Prompt injection:** `engine/prompt.py` → `_build_companion_block()` injects a `--- NEXY COMPANION ENGINE ---` block after APPROVED KNOWLEDGE. Block structure: IDENTITY → OBJECTIVE → CURRENT SITUATION → AVAILABLE SOLUTIONS → REFERENCES → GUIDELINES → DIRECTIVE → LANGUAGE RULES.

**Key invariant:** The words "sales", "selling", "sell", "pitch", "lead" must not appear in any visitor-facing output, system prompt, DocType label, or code variable within the companion module. Use: advising, guiding, enquiry, companion, next step.

**API endpoints:** `nexus_companion/api/companion_dashboard.py` — `get_dashboard_data()`, `get_enquiry_detail()`, `get_tenants()`

**Dashboard page:** `nexus_companion/page/nexus_companion_dashboard/` — stage funnel (11 stages), milestone column, conversion stats, enquiry list, persona frequency, config summary. Subscribes to `companion_progress_update` realtime events for live badge and funnel updates without page refresh.

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
| `Nexus Live Channel` | `channel_code`, `tenant`, `channel_name`, `channel_type`, `enabled`, `default_agent`, `requires_visitor_email` | Logical entry point/context — website chat, mobile, desk, API, campaign, support surface |
| `Nexus Chat Category` | `category_code`, `category_label`, `channel`, `tenant`, `enabled`, `published`, `visibility`, `identity_verification_mode`, `allow_public_fallback`, `enable_escalation`, `use_for_nexy`, `faq_questions` | Visitor-facing topic/service. Belongs to one channel, so selecting the category implies the channel. `use_for_nexy` flags this as a Nexy-exclusive category — must have identity verification and a published route (validated on save). |
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
| `Nexus Category Identity Route` | `channel`, `chat_category`, `ai_agent_profile`, `identity_profiles`, `public_knowledge_profile`, `enabled`, `published`, `priority` | Routes a selected chat category and visitor identity context to the AI behavior profile and identity/knowledge access chain. Channel is derived from the category context and retained for filtering/reporting. `public_knowledge_profile` (Link → Knowledge Profile) — the knowledge boundary granted to Public (unverified) visitors who reach this route. When set, the resolver uses exactly the access policies inside that profile for retrieval; nothing outside those policies is visible. When blank, the system falls back to the AI Agent Profile's own knowledge profiles. See §14.1 for the full resolution chain. |
| `Nexus Route Identity Profile` | (child) `identity_type`, `identity_profile` | Per-identity profiles within a route |
| `Nexus Identity Verification Challenge` | `conversation`, `challenge_type`, `status`, `challenge_sent_at` | Active identity challenge in progress |
| `Nexus Website Widget` | `widget_name`, `tenant`, `position`, `primary_color` | Embeddable chat widget configuration. The widget may load all published External/Both categories under enabled Website Chat channels for the tenant; visitors select categories, not channels. |

#### nexus_live_conversations

| DocType | Key Fields | Purpose |
|---|---|---|
| `Nexus Live Conversation` | `conversation_id`, `conversation_type`, `channel`, `chat_category`, `resolved_identity_type`, `identity_registry`, `visitor_name`, `visitor_email`, `user_type`, `assigned_agent`, `assigned_ai_agent_profile`, `status`, `intent`, `confidence`, `escalation_status`, `escalated_at`, `human_agent`, `started_on`, `nexy_handover_category`, `companion_journey_stage`, `companion_milestone`, `companion_persona`, `companion_enquiry` | Central session record for every chat. `companion_milestone` is written by the Business Companion Controller each turn (8 milestones). `nexy_handover_category` is set during Nexy handover detection and cleared once the handover completes. |
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
| `nexy_handover_service.py` | Nexy intent detection and handover orchestration. `detect_nexy_intent(message)` — keyword scan (price, demo, consultancy, etc.). `get_nexy_category(channel, tenant)` — resolves the active Nexy category for the channel. `validate_nexy_routing(channel, tenant)` — preflight check used by admins. `initiate_nexy_handover(conversation, payload)` — stores pending category, switches intent to `await_nexy_verification` when email verification is required. `complete_nexy_handover(conversation, payload)` — resolves Nexy AI profile, rewrites conversation's category + agent snapshot. |
| `visitor_tracking_service.py` | `get_or_create_visitor()`, `get_or_create_session()`, `start_page_visit()` — propagate `tenant` from widget → channel → tracking records |
| `conversation_service.py` | CRUD for conversations and messages; `stamp_email_on_web_visitor()` — writes OTP-verified email to `Nexus Web Visitor` |

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

### 4.4 Sales DocTypes (12 DocTypes)

`Nexus Sales Strategy`, `Nexus Sales Campaign`, `Nexus Sales Audience Segment`, `Nexus Sales Lead Source`, `Nexus Sales Lead Score`, `Nexus Sales Outreach Draft`, `Nexus Sales Outreach Event`, `Nexus Sales Follow Up Rule`, `Nexus Sales Reply Classification`, `Nexus Sales Objection Library`, `Nexus Sales Notification Rule`, `Nexus Sales Suppression List`

> `Nexus Sales Playbook` was removed 2026-06-28 — zero records, `build_outreach_context` was never implemented, and no code outside the agentic app referenced it.

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
| `companion_progress_update` | `business_companion_controller._publish_progress_update()` and `enquiry_service._set_stage()` | Companion Dashboard page | `{enquiry, conversation, stage, milestone}` — emitted after every journey stage change and every controller milestone advance. Dashboard JS patches table row badges and funnel counts in-place without a full reload. |

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

### 10.1 Conversation Intent States

The `intent` field on `Nexus Live Conversation` drives branching in `continue_live_chat()`:

| Intent Value | Meaning | Next Transition |
|---|---|---|
| `await_category` | Visitor has not yet selected a chat category | Set on conversation start; cleared when visitor sends `__cat__:<code>` |
| `await_verification` | Category requires email OTP before chat starts | Cleared once `Nexus Identity Verification Challenge` is verified |
| `await_nexy_verification` | Nexy handover pending — waiting for email OTP | Cleared once challenge verified → `complete_nexy_handover()` runs |
| `await_name` | Widget is collecting visitor's display name | Cleared once name captured, category picker shown |
| `await_close_confirm` | AI asked "anything else?" — waiting for close confirmation | Cleared on yes (conversation closed) or no (resume normal flow) |
| `post_escalation` | First visitor message after human agent resolved | One-shot flag cleared immediately; triggers post-escalation AI response |
| *(empty)* | Normal conversational flow | `detect_nexy_intent()` checked; `_enqueue_ai_response()` called |

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

**Prerequisites — must all be true before desk chat works:**

| Requirement | Detail |
|---|---|
| Live Channel | Channel Type must be **`Desk`** (not `Website Chat`). The widget only loads categories from Desk-type channels for logged-in users. |
| Chat Category | Must be **Enabled AND Published**. Unpublished categories are not returned to the widget regardless of enabled status. |
| Category Identity Route | Must be **Enabled AND Published**. An unpublished route will not resolve the AI Agent Profile and chat fails with "No active AI Agent Profile route". |
| User Profile Assignment | A `Nexus User Profile Assignment` linking the Frappe user to an AI Agent Profile must exist and be active. |

```
Desk user (logged in) triggers NexusChatWidget.open()
    │
    ▼
Widget loads categories
    → finds enabled Nexus Live Channels where channel_type = Desk
    → returns published categories from those channels (Enabled AND Published)
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
    → Falls back to published Category Identity Route for the selected category
    → Normal AI pipeline
    ▲
    │
Note: Desk User conversations are EXCLUDED from the Live Console
(filtered by user_type != 'Desk User')
```

### 12.1 Public Access Mode (Admin Desk Chat)

Public Access Mode lets a System Manager or admin desk user simulate exactly what a real public visitor sees — same AI agent (Nexy Companion), same knowledge boundary, same access policies — without leaving the Frappe desk.

**Activation:** The chat widget header contains a globe button (`ncw-pub-mode-btn`). Clicking it:
1. Toggles `S.public_access_mode = true` in widget state
2. Shows an amber strip (`ncw-pub-mode-strip`) below the header as a persistent visual indicator
3. Restarts the conversation (calls `start_new_chat()`) so the new mode takes effect immediately

**How it propagates:**

| Call site | What changes |
|---|---|
| `start_new_chat()` | `base.force_public_only = true` added to the start payload |
| `send_message()` | `msg_payload.force_public_only = true` added to every message payload |
| `select_category()` | `cat_payload.force_public_only = true` added to category selection |

The widget's `render_category_picker()` also hides the Nexy sticky row for desk users **unless** `S.public_access_mode` is true — so the "Connect with Nexy" option only appears in the category picker when Public Access Mode is active.

**Server-side effect of `force_public_only = true`:**

| Stage | Behaviour |
|---|---|
| `start_live_chat()` — category picker | `picker_is_internal = false`; queries for External/Both categories (Nexy) instead of Internal/Both |
| `continue_live_chat()` — category selection | `identity_type` forced to `"Public"`, `_is_authenticated = false` — routes through `resolve_behavior_from_chat_category` as a public visitor |
| `continue_live_chat()` — nudge re-picker | Does NOT treat the desk user as internal; re-sends the public category picker |
| `build_core_chat_payload()` | `force_public_only` computed as `True`; passed into `resolve_allowed_policies()` |
| `resolve_allowed_policies()` | Short-circuits **before** the System Manager bypass; returns primitive public policies only (`['Public', 'Public-NEXUS-AI']`) |
| `_process_ai_response()` | Clears `core_payload["chat_history"]` when `force_public_only=True` and `user_type="Desk User"` — prevents desk intro messages (e.g. "I'm Raju On Desk") from anchoring the LLM in a desk persona |

**Key invariant:** `force_public_only=True` is checked **first** in `resolve_allowed_policies()`, before the System Manager bypass check. This means even a user with `System Manager` role receives only public-policy knowledge in this mode — the admin cannot accidentally see private or internal knowledge while testing the public visitor experience.

**Conversation fields frozen at category selection (Public Access Mode):**

| Field | Value set |
|---|---|
| `resolved_identity_type` | `"Public"` |
| `assigned_ai_agent_profile` | Nexy Companion profile name |
| `ai_profile_snapshot_json` | Frozen Nexy behavior snapshot (knowledge profile names, behavior prompt, etc.) |

All subsequent turns in the conversation read behavior from the frozen snapshot via `resolve_behavior_from_conversation()`, so the public simulation is consistent across the full conversation even if config changes mid-session.

---

## 13. Core Data Flow — Nexy Handover

Nexy is the platform's premium AI operator. Regular chat categories can hand off to a Nexy-flagged category when the visitor signals a high-value intent (pricing, demo, consultancy, etc.).

### 13.1 Setup Requirements

For Nexy handover to work on a channel, ALL of the following must be true:

| Requirement | Where Configured |
|---|---|
| At least one `Nexus Chat Category` with `use_for_nexy = 1`, `enabled = 1`, `published = 1` | Chat Category form |
| That category has `identity_verification_mode` ≠ None (if global setting requires it) | Chat Category form |
| That category has at least one `Nexus Category Identity Route` that is `enabled = 1`, `published = 1` | Category Profile Routes page |
| `Nexus Settings → nexy_email_verification_mandatory` determines whether verification is globally enforced | Nexus Settings (Single) |

The `Nexus Chat Category` controller (`nexus_chat_category.py`) validates these constraints on save and warns via `frappe.msgprint`.

### 13.2 Intent Trigger Keywords (hardcoded, `nexy_handover_service.py`)

```
price, pricing, cost, costs, how much, rates, fee, fees,
subscription, plan, plans, package, packages, quote, quotation,
demo, demonstration, trial, show me,
consultancy, consultation, consult, consulting,
proposal, enterprise, custom solution,
buy, purchase, get started, sign up
```

### 13.3 Handover State Machine

```
Visitor sends message (normal AI flow)
    │
    ▼
live_chat_service.continue_live_chat()
    → detect_nexy_intent(message) [nexy_handover_service.py]
    → _is_already_nexy(conversation) → skip if already in a Nexy category
    │
    ├─ No trigger → normal _enqueue_ai_response()
    │
    └─ Trigger detected
           │
           ▼
       initiate_nexy_handover(conversation, payload)
           → get_nexy_category(channel, tenant) → find use_for_nexy category
           → db_set nexy_handover_category on conversation
           │
           ├─ Category requires email verification AND visitor not yet verified
           │       → db_set intent = "await_nexy_verification"
           │       → AI message: "I can connect you to Nexy — please verify your identity…"
           │       → publish_chat_response(status=await_nexy_verification, identity_verification_offer=True)
           │       → return {status: await_nexy_verification}
           │
           └─ No verification needed (or already verified)
                   → complete_nexy_handover(conversation, payload)
                   → AI message: "You've been connected to [Nexy Category]…"
                   → return {status: nexy_handover_complete}

    ──── on next message from visitor (intent = "await_nexy_verification") ────

    live_chat_service.continue_live_chat()
        → intent == "await_nexy_verification"
        → get_verified_challenge(identity_verification_challenge, chat_category=nexy_handover_category)
        │
        ├─ No valid challenge → nudge: "Please verify your identity…"
        │       → publish_chat_response(status=await_nexy_verification, identity_verification_offer=True)
        │
        └─ Challenge verified
               → db_set visitor_email, resolved_identity_type, identity_registry
               → stamp_email_on_web_visitor(conversation, email, verified=True)
               → complete_nexy_handover(conversation, payload)
                     → resolve_behavior_from_chat_category(nexy_cat, identity_type, …)
                     → get Nexus AI Agent Profile from route
                     → db_set chat_category, assigned_agent, ai_profile_snapshot_json
                     → db_set intent = "", nexy_handover_category = None
                     → conversation.reload()
               → AI message: "Identity verified. You're now connected to [Nexy]…"
               → publish_chat_response(status=nexy_handover_complete)
               → return {status: nexy_handover_complete}
```

### 13.4 Key Invariants

- `detect_nexy_intent` is only called when `conversation.chat_category` is set (i.e. visitor has already selected a category) and `nexy_handover_category` is not already pending.
- `_is_already_nexy(conversation)` prevents double-handover: if the current `chat_category` already has `use_for_nexy = 1`, the trigger is a no-op.
- The `ai_profile_snapshot_json` is fully rewritten on handover completion — the Nexy profile's behavior prompt, tone, and knowledge profile replace the original category's snapshot.
- `nexy_handover_category` is cleared (set to None) on both successful completion and on any failure path where `complete_nexy_handover` returns None.
- Email stamping on `Nexus Web Visitor` uses the same `stamp_email_on_web_visitor()` path as normal `await_verification`, so visitor analytics stay consistent.

---

## 14. Identity Resolution Chain

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

### 14.1 Public Visitor Knowledge Resolution (`public_knowledge_profile`)

When a visitor resolves as `Public` identity type (including admin desk users in Public Access Mode), `profile_resolver.resolve_behavior_from_chat_category()` reads the `public_knowledge_profile` field from the matched route and stores it as `knowledge_profile_names` in the behavior dict, which is then frozen into `ai_profile_snapshot_json`.

```
profile_resolver.resolve_behavior_from_chat_category()
    │
    ▼
_find_any_route(channel, category, tenant)
    → first enabled+published Nexus Category Identity Route for this category
    │
    ▼
public_knowledge_profile field on the route
    │
    ├─ Set  → knowledge_profile_names = [public_knowledge_profile]
    └─ Blank → knowledge_profile_names = []
    │
    ▼
Stored in behavior dict → frozen in ai_profile_snapshot_json
```

At query time, `build_core_chat_payload()` sets `force_public_only=True` (because `resolved_identity_type == "Public"`) and calls `resolve_allowed_policies()`, which now applies the profile as a scope:

```
resolve_allowed_policies()  [access_resolver.py]
    │
    ▼
force_public_only = True
    │
    ▼
primitive_public_policies = resolve_primitive_public_policies(tenant)
    → all Nexus Access Policy records where is_primitive=1
    → e.g. {'Public', 'Public-NEXUS-AI'}
    │
    ├─ knowledge_profile_names is EMPTY (no profile on route)
    │       → allowed = primitive_public_policies          (all public knowledge for tenant)
    │       → access_cap_applied = "force_public_only"
    │
    └─ knowledge_profile_names is SET
            │
            ▼
        resolve_knowledge_profiles_policy_names(kp_names)
            → Knowledge Profile Access Category child rows (disabled=0 only)
            → each row → Nexus Access Category → its Access Policies
            → e.g. profile_policies = {'Public-NEXUS-AI'}
            │
            ▼
        scoped = primitive_public_policies ∩ profile_policies
            e.g. {'Public', 'Public-NEXUS-AI'} ∩ {'Public-NEXUS-AI'} = {'Public-NEXUS-AI'}
            │
            ├─ scoped non-empty → allowed = scoped
            │       → access_cap_applied = "force_public_only+profile_scoped"
            │
            └─ scoped empty (profile has no public-type policies → misconfigured)
                    → allowed = primitive_public_policies  (safe fallback)
                    → access_cap_applied = "force_public_only"
    │
    ▼
Retrieval filter on Nexus Knowledge Chunk:
    access_policy IN [allowed]  AND  tenant = '<tenant>'
```

**What this means in plain terms:**

Only chunks whose `access_policy` field exactly matches one of the policies inside the configured Access Category are retrieved. Any knowledge source tagged with a policy from a *different* Access Category — even if that policy is also "public type" — is excluded. Different category routes can therefore have different public knowledge scopes:

| Route | public_knowledge_profile | Retrieval scope |
|---|---|---|
| Connect with Nexy | `NEXUS-COMMERCIAL-KNOWLEDGE-PROFILE-NEXUS-AI` | Only `Public-NEXUS-AI` (commercial) chunks |
| General FAQ (hypothetical) | *(blank)* | All primitive public chunks for tenant |

**Safety ceiling — intersection prevents privilege escalation:**

The intersection with `primitive_public_policies` is unconditional. If a profile's Access Category is accidentally configured with a non-public policy (e.g. `Internal-NEXUS-AI`), that policy is not in `primitive_public_policies` and is stripped from `scoped` before the return. A misconfigured profile cannot expose non-public knowledge to public visitors.

**Configuration requirement — `Disabled` checkbox on child rows:**

`resolve_knowledge_profiles_policy_names` filters child rows with `disabled=0`. Access Category rows inside the Knowledge Profile are active by default (Disabled unchecked). Check **Disabled** on a row to temporarily exclude that Access Category from resolution without deleting it. If all rows are disabled, `profile_policies` comes back empty → `scoped` is empty → falls back to all primitive public policies for the tenant.

---

## 15. Tenant Isolation Rules

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

## 16. Build & Deployment Notes

| Action | Command |
|---|---|
| Rebuild chat widget (JS changes) | `bench build --app digitz_ai_nexus_live` |
| Rebuild platform CSS (digitz_ai_nexus_site.css changes) | `bench build --app digitz_ai_nexus` |
| Apply DocType schema changes | `bench migrate` |
| Update bundle hash in www pages | Update `nexus_chat_widget.bundle.XXXXXXXX.js` in `index.html`, `nexus-platform.html`, `how-nexus-works.html` |
| www HTML inline `<style>` changes | Live immediately — no build needed |

---

## 17. File Map Quick Reference

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
│   ├── services/                         LiveChatService, EscalationService, Realtime,
│   │                                     NexyHandoverService, ConversationService,
│   │                                     VisitorTrackingService
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
