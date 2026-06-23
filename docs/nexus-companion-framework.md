# Nexus Companion Framework

> Last updated: 2026-06-23
> Module: `nexus_companion` inside `digitz_ai_nexus`
> App spans: `digitz_ai_nexus`, `digitz_ai_nexus_live`

---

## 1. Overview

The Nexus Companion Framework turns Nexy into an **intent-driven conversation engine** whose default purpose is to guide visitors toward a positive outcome — an enquiry captured, a meeting booked, a subscription initiated, or a purchase completed. The LLM is the intelligence that drives the conversion process itself, not a rule engine sitting on top of it.

**Fundamental design principle:** The LLM is the sales engine. Every rule, every stage transition, every decision about what to say next is an LLM judgment — made with precise, structured context the platform provides. The platform's job is to give the LLM a clear objective, full situational awareness, an action arsenal, and strict language rules — then get out of the way.

**Companion Intent:** The framework is built around a configurable intent. The default and currently supported intent is **Sales** — guide visitors to a completed conversion. The architecture is designed to support additional intents (Support, Onboarding, Retention) as future extensions without structural changes.

**Language rule (absolute):** The words "sales", "selling", and "sell" must never appear in UI labels, system prompts, DocType names, code variables, or any visitor-facing text. Equivalent terms:

| Avoided term | Used term |
|---|---|
| Sales / selling | Advising / guiding |
| Lead | Enquiry |
| Pitching | Presenting |
| CTA | Next Step |
| Sales Profile | Companion Playbook |
| Qualified | Ready for next step |

---

## 2. Architecture

The companion is a horizontal layer across the existing chat pipeline. Per-turn flow:

```
Visitor message arrives
        │
        ▼
live_chat_service.continue_live_chat()
        │
        ▼
_process_ai_response()  [background job]
        │
        ├── build_core_chat_payload()
        │        └── _build_ai_profile_dict() — includes companion_mode,
        │                                        companion_playbook
        │
        ├── Nexy enrichment (digitz_ai_nexus_nexy — existing)
        │
        ├── Companion enrichment (new):
        │        if companion_mode:
        │            companion_context = build_companion_context()
        │            core_payload["companion_context"] = companion_context
        │            core_payload["response_mode"] = "companion_advisor"
        │
        ├── answer_query(core_payload)
        │        └── prompt.py → _build_companion_block()
        │               Injects NEXY COMPANION ENGINE block into the system prompt
        │               (OBJECTIVE → SITUATION → ARSENAL → DIRECTIVE → RULES)
        │
        └── Post-response (companion mode only):
                 ├── classify_signal(visitor_message) — LLM signal classification
                 ├── update_enquiry(signal, discovery_delta) — persist + re-score
                 ├── advance_journey_stage_from_signal() — signal-driven stage machine
                 ├── advance_journey_stage() — score-based fallback
                 └── check_escalation_threshold() + check_trigger_keywords()
```

---

## 3. Module Structure

```
digitz_ai_nexus/nexus_companion/
├── __init__.py
├── services/
│   ├── companion_context_service.py   ← context assembly for each AI turn
│   ├── enquiry_service.py             ← stage machine, scoring, enquiry lifecycle
│   ├── signal_classifier.py           ← LLM-powered buying signal classification (new)
│   ├── persona_matching_service.py    ← keyword scoring for persona identification
│   └── reference_matching_service.py ← story/testimonial/outcome retrieval
├── api/
│   └── companion_dashboard.py         ← dashboard data endpoints
├── page/
│   └── nexus_companion_dashboard/     ← Frappe Page for the companion dashboard
└── doctype/
    ├── nexus_companion_product/
    ├── nexus_companion_product_persona/      (child)
    ├── nexus_companion_service/
    ├── nexus_companion_service_persona/      (child)
    ├── nexus_companion_persona/
    ├── nexus_companion_persona_product/      (child)
    ├── nexus_companion_persona_service/      (child)
    ├── nexus_companion_playbook/
    ├── nexus_companion_story/
    ├── nexus_companion_story_product/        (child)
    ├── nexus_companion_story_persona/        (child)
    ├── nexus_companion_testimonial/
    ├── nexus_companion_case_study/
    ├── nexus_companion_case_study_persona/   (child)
    ├── nexus_companion_outcome/
    ├── nexus_companion_outcome_product/      (child)
    ├── nexus_companion_outcome_persona/      (child)
    ├── nexus_companion_enquiry/
    ├── nexus_companion_enquiry_product/      (child)
    └── nexus_companion_enquiry_service/      (child)
```

---

## 4. DocType Reference

### 4.1 Nexus Companion Product
*Autoname: `NCP-.#####`*

Everything Nexy needs to discuss a product — what it solves, who it fits, what outcomes to expect, how to handle objections, and how the sales cycle completes.

**Core fields:**

| Field | Type | Description |
|---|---|---|
| `product_name` | Data | Display name |
| `category` | Data | Product category |
| `tenant` | Link → Nexus Tenant | Tenant isolation |
| `enabled` | Check | Active in companion context |
| `chat_category` | Link → Nexus Chat Category | Knowledge routing — Nexy retrieves factual product knowledge through this category's knowledge engine |
| `description` | Long Text | Plain description |
| `features` | Long Text | Key features |
| `benefits` | Long Text | Visitor-facing benefits |
| `unique_value_propositions` | Long Text | What makes this different |
| `competitive_differentiators` | Long Text | Why choose this over alternatives |
| `challenges_solved` | Long Text | Visitor problems this addresses |
| `qualification_criteria` | Long Text | Signals the visitor is a strong fit |
| `disqualification_criteria` | Long Text | When NOT to recommend — Nexy must not pitch when these conditions apply |
| `typical_outcomes` | Long Text | What results look like |
| `success_metrics` | Long Text | How success is measured |
| `objection_responses` | Long Text | Common concerns and how to address them (format: Concern | Response) |
| `next_step` | Select | Default Next Step: Learn More / Evaluation Request / Consultation Request / Direct Meeting |
| `target_personas` | Table → Nexus Companion Product Persona | Which personas this product suits |

**Conversion Configuration fields:**

| Field | Type | Description |
|---|---|---|
| `conversion_type` | Select | How the cycle completes: Lead Capture / Meeting Booking / Direct Purchase / Subscription / Trial Activation / Download Gate / Human Handoff / Webhook |
| `conversion_threshold_score` | Int (default 65) | Enquiry score at which Nexy should guide toward conversion |
| `conversion_config` | Code (JSON) | Mechanism-specific params: payment URL, calendar link, webhook endpoint, form URL |
| `conversion_message` | Long Text | What Nexy says when guiding the visitor to the conversion step |
| `conversion_fallback` | Long Text | Shown if the conversion action cannot be completed |
| `post_conversion_action` | Select | After conversion: Close Conversation / Continue Conversation / Escalate to Human |

### 4.2 Nexus Companion Service
*Autoname: `NCS-.#####`*

Identical structure to Product. Uses `service_name` as primary label. Returned alongside products in the companion context. Includes the same Conversion Configuration section.

### 4.3 Nexus Companion Persona
*Autoname: `NCPE-.#####`*

A visitor archetype. Persona matching runs on every discovery update and shapes how Nexy communicates and what it recommends.

| Field | Type | Description |
|---|---|---|
| `persona_name` | Data | Archetype name |
| `tenant` | Link → Nexus Tenant | Tenant isolation |
| `enabled` | Check | Active for matching |
| `customer_type` | Select | B2B / B2C / Both |
| `company_size` | Select | Solo / Micro / SME / Mid-Market / Enterprise |
| `business_maturity` | Select | Startup / Growing / Established / Scaling |
| `industry` | Data | Target industry |
| `challenges` | Long Text | Known pain points |
| `pain_points` | Long Text | Specific friction points |
| `goals` | Long Text | What they are trying to achieve |
| `desired_outcomes` | Long Text | What success looks like |
| `buying_triggers` | Long Text | Labelled "Engagement Triggers" |
| `common_objections` | Long Text | Labelled "Common Concerns" |
| `communication_style` | Long Text | How to speak to this persona |
| `recommended_messaging` | Long Text | Angle and framing to take |
| `recommended_products` | Table → Nexus Companion Persona Product | Suggested products |
| `recommended_services` | Table → Nexus Companion Persona Service | Suggested services |

### 4.4 Nexus Companion Playbook
*Autoname: `NCPB-.#####`*

Governs how Nexy behaves for a given channel. One playbook can be shared across multiple AI Agent Profiles. Mark one as `is_default` per tenant as a fallback.

| Field | Type | Description |
|---|---|---|
| `playbook_name` | Data | Name |
| `tenant` | Link → Nexus Tenant | Tenant isolation |
| `enabled` | Check | Active |
| `is_default` | Check | Fallback when no playbook is linked on the profile |
| `discovery_questions` | Long Text | One per line — Nexy draws from these during DISCOVERY stage |
| `communication_guidelines` | Long Text | Behavioural rules injected into the prompt |
| `objection_responses` | Long Text | Labelled "Concern Responses" — injected in PRESENTING and OBJECTION_HANDLING stages |
| `reference_usage_rules` | Long Text | When and how to surface customer references |
| `escalation_score_threshold` | Int (default 70) | Score above which Nexy recommends escalation |
| `escalation_triggers` | Long Text | Keywords/phrases that force escalation regardless of score |
| `next_step_options` | Long Text | Available next steps for this playbook |

### 4.5 Nexus Companion Story
*Autoname: `NCST-.#####`*

Approved customer success stories surfaced by Nexy to build trust and demonstrate real-world impact.

| Field | Type | Description |
|---|---|---|
| `title` | Data | Story title |
| `industry` | Data | Industry of the customer |
| `customer_type` | Select | B2B / B2C |
| `company_size` | Select | Size |
| `tenant` | Link → Nexus Tenant | Tenant isolation |
| `approved` | Check | Must be checked before the story appears |
| `visibility` | Select | Public / Internal / Restricted |
| `challenge` | Long Text | What problem the customer faced |
| `solution` | Long Text | How it was solved |
| `outcomes` | Long Text | Results achieved |
| `summary` | Long Text | Short version for prompt injection |
| `linked_products` | Table → Nexus Companion Story Product | Products referenced |
| `linked_personas` | Table → Nexus Companion Story Persona | Personas this story suits |

### 4.6 Nexus Companion Testimonial
*Autoname: `NCTM-.#####`*

Short customer testimonials. Customer name and company are optional for anonymity.

| Field | Type | Description |
|---|---|---|
| `tenant` | Link → Nexus Tenant | Tenant isolation |
| `approved` | Check | Must be checked to appear |
| `rating` | Int | 1–5 |
| `customer_name` | Data | Optional — blank for anonymity |
| `company_name` | Data | Optional |
| `testimonial` | Long Text | The testimonial text |
| `linked_product` | Link → Nexus Companion Product | Associated product |
| `linked_service` | Link → Nexus Companion Service | Associated service |

### 4.7 Nexus Companion Case Study
*Autoname: `NCCS-.#####`*

Detailed case studies for deeper social proof, intended for later journey stages.

| Field | Type | Description |
|---|---|---|
| `title` | Data | Case study title |
| `industry` | Data | Customer industry |
| `tenant` | Link → Nexus Tenant | Tenant isolation |
| `approved` | Check | Must be checked to appear |
| `visibility` | Select | Public / Internal |
| `customer_profile` | Long Text | Anonymised customer description |
| `initial_situation` | Long Text | Situation before the engagement |
| `solution_provided` | Long Text | What was implemented |
| `outcomes` | Long Text | Results achieved |
| `metrics` | Long Text | Quantified improvements |
| `linked_personas` | Table → Nexus Companion Case Study Persona | Relevant personas |

### 4.8 Nexus Companion Outcome
*Autoname: `NCOUT-.#####`*

Discrete, reusable outcome statements Nexy can cite to demonstrate value without naming a specific customer.

| Field | Type | Description |
|---|---|---|
| `outcome_label` | Data | e.g. "Reduced manual follow-up by 60%" |
| `outcome_category` | Select | Efficiency / Revenue / Customer Experience / Cost Reduction / Other |
| `tenant` | Link → Nexus Tenant | Tenant isolation |
| `approved` | Check | Must be checked to appear |
| `detail` | Long Text | Extended explanation |
| `linked_products` | Table → Nexus Companion Outcome Product | Products this outcome relates to |
| `linked_personas` | Table → Nexus Companion Outcome Persona | Personas this resonates with |

### 4.9 Nexus Companion Enquiry
*Autoname: `NCENQ-.#####`*

The full sales cycle record for a visitor. Created automatically when companion mode is active on a conversation. Updated in real time as Nexy discovers information, classifies signals, and advances the journey.

**Identity fields:**

| Field | Type | Description |
|---|---|---|
| `visitor` | Link → Nexus Web Visitor | Linked visitor record |
| `visitor_email` | Data (Email) | Collected/verified email address |
| `verification_status` | Select | Unverified / OTP Verified |
| `web_session` | Link → Nexus Web Session | Active session for tracking continuity |
| `conversation` | Link → Nexus Live Conversation | Source conversation (required) |
| `tenant` | Link → Nexus Tenant | Tenant isolation (required) |

**Journey fields:**

| Field | Type | Description |
|---|---|---|
| `enquiry_stage` | Select | Current stage (mirrors `companion_journey_stage` on the conversation) |
| `enquiry_score` | Int (0–100) | Composite qualification score |
| `escalation_recommended` | Check | Set when score ≥ playbook threshold |
| `created_on` | Datetime | When the enquiry was created |

**Persona fields:**

| Field | Type | Description |
|---|---|---|
| `matched_persona` | Link → Nexus Companion Persona | Best-matched persona (set by service) |
| `persona_confidence` | Float | Matching confidence 0–100 |

**Qualification fields:**

| Field | Type | Description |
|---|---|---|
| `recommended_next_step` | Data | Derived from score |
| `product_fit_json` | Code (JSON) | Product → fit score map |

**Discovery and signal fields:**

| Field | Type | Description |
|---|---|---|
| `discovery_data` | Code (JSON) | Accumulated visitor profile collected during conversation |
| `stage_signal` | Data | Most recent LLM-classified visitor buying signal |
| `signal_log` | Code (JSON) | Chronological array of all classified signals (analytics backbone, capped at 50 entries) |

**Recommendation and summary fields:**

| Field | Type | Description |
|---|---|---|
| `recommended_products` | Table → Nexus Companion Enquiry Product | Top product fits |
| `recommended_services` | Table → Nexus Companion Enquiry Service | Top service fits |
| `conversation_summary` | Long Text | Summary for handover to human agent |

---

## 5. Extended DocTypes

### 5.1 Nexus AI Agent Profile (in `digitz_ai_nexus_live`)

Three fields under a **Companion Settings** section:

| Field | Type | Description |
|---|---|---|
| `companion_mode` | Check | Activates the companion engine for all conversations on this profile |
| `companion_playbook` | Link → Nexus Companion Playbook | Governs discovery questions and escalation behaviour |
| `companion_discovery_style` | Select | Conversational / Structured / Minimal |

When `companion_mode = 1`:
- Companion context is built and injected into every AI turn
- Response mode switches to `companion_advisor`
- Signal classification runs after every AI response
- Journey stage advances on every turn
- Escalation is checked on every turn

### 5.2 Nexus Live Conversation (in `digitz_ai_nexus_live`)

Five fields under a **Companion Journey** section:

| Field | Type | Description |
|---|---|---|
| `companion_journey_stage` | Select | Current stage (see section 6 for full stage list) |
| `companion_persona` | Link → Nexus Companion Persona | Best-matched persona (set by service, read only) |
| `companion_persona_confidence` | Float | Matching confidence 0–100 (read only) |
| `companion_enquiry` | Link → Nexus Companion Enquiry | Linked enquiry record (read only) |
| `companion_discovery_json` | Code (JSON) | Accumulated visitor profile data (read only) |

---

## 6. Journey Stages

The companion tracks visitor progression through eleven stages. Stage transitions are **signal-driven** — the LLM classifies each visitor message as a buying signal, and the signal determines whether and how the stage advances. Score-based advancement is retained as a safety net.

```
ARRIVED → GREETING → DISCOVERY → ENGAGED → PRESENTING ⇌ OBJECTION_HANDLING
                                                    ↓
                                              INTERESTED → CONVERTING → CONVERTED
                                                                      ↘ DECLINED
                                              (any stage) → ESCALATED
```

| Stage | What Nexy does | Entry condition |
|---|---|---|
| ARRIVED | Warm greeting, open question | Session start |
| GREETING | Build first connection, invite context sharing | First visitor message |
| DISCOVERY | Structured discovery using playbook questions | SHARING_CONTEXT or ANSWERING_QUESTION signal |
| ENGAGED | Connect challenges to solutions, begin introducing products | EVALUATING signal |
| PRESENTING | Present a specific product or service, invite questions | Any positive signal from ENGAGED |
| OBJECTION_HANDLING | Handle a raised concern specifically and bridge back | OBJECTING signal while PRESENTING |
| INTERESTED | Reinforce fit, suggest concrete next step | INTERESTED or ASKING_NEXT_STEP signal |
| CONVERTING | Guide to the specific conversion action configured on the product | ASKING_PRICE or READY signal |
| CONVERTED | Confirm the action, set expectations, warm close | Conversion action completed |
| DECLINED | Respect the decision, leave door open | DECLINING signal |
| ESCALATED | Wrap up, confirm specialist handover | REQUESTING_HUMAN signal or score/keyword threshold |

**Terminal stages:** CONVERTED, DECLINED, ESCALATED. Once reached, the journey does not advance further.

---

## 7. Signal Classification

**File:** `digitz_ai_nexus/nexus_companion/services/signal_classifier.py`

Every visitor message is classified by the LLM into one of 14 buying signal types. This is not keyword matching — it is full LLM judgment with confidence score and reasoning.

### Signal taxonomy

**Discovery signals**
- `SHARING_CONTEXT` — Describing their situation or business background
- `ANSWERING_QUESTION` — Responding to a question Nexy asked

**Interest signals**
- `CURIOUS` — Exploring, asking general questions
- `EVALUATING` — Comparing, asking deeper questions
- `INTERESTED` — Positive engagement, expressing genuine fit
- `READY` — Clear intent to proceed (buy, subscribe, book, start)

**Conversion signals**
- `ASKING_PRICE` — Asking about cost, pricing, or plans
- `ASKING_NEXT_STEP` — "How do I get started?", "what's next?"

**Resistance signals**
- `OBJECTING` — Raising a concern (price, timing, need, trust)
- `HESITATING` — Non-committal, vague, slowing down
- `DISENGAGING` — Short or dismissive replies, losing interest
- `DEFLECTING` — Changing subject or avoiding

**Cycle-ending signals**
- `REQUESTING_HUMAN` — Wants to speak with a person
- `DECLINING` — Explicitly not interested, wants to exit

### Signal → stage mapping

| Signal | Stage transition |
|---|---|
| `SHARING_CONTEXT`, `ANSWERING_QUESTION`, `CURIOUS` | → DISCOVERY (if before) |
| `EVALUATING` | → ENGAGED (if before) |
| `INTERESTED`, `ASKING_NEXT_STEP` | → INTERESTED (if before) |
| `READY`, `ASKING_PRICE` | → CONVERTING (if before) |
| `OBJECTING` while PRESENTING | → OBJECTION_HANDLING |
| Positive signal while OBJECTION_HANDLING | → PRESENTING |
| First message while ARRIVED | → GREETING |
| `REQUESTING_HUMAN` | → ESCALATED (always) |
| `DECLINING` | → DECLINED (always) |
| `HESITATING`, `DISENGAGING`, `DEFLECTING` | No stage change — LLM handles contextually |

### API

```python
classify_signal(message: str, conversation_context: str = "") -> dict
# Returns: {signal_type: str, confidence: float, reason: str}
# Never throws — falls back to CURIOUS/0.5 on LLM failure

is_conversion_signal(signal_type: str) -> bool
# True for READY, ASKING_PRICE, ASKING_NEXT_STEP

is_resistance_signal(signal_type: str) -> bool
# True for OBJECTING, HESITATING, DISENGAGING, DEFLECTING

is_exit_signal(signal_type: str) -> bool
# True for REQUESTING_HUMAN, DECLINING
```

---

## 8. Enquiry Scoring

The enquiry score (0–100) is a composite, recalculated on every `update_enquiry()` call:

| Factor | Max points | Source |
|---|---|---|
| Discovery completeness | 40 | How many of 10 key fields are filled: `industry`, `company_size`, `team_size`, `business_maturity`, `current_challenges`, `goals`, `existing_systems`, `budget_range`, `timeline`, `decision_maker` |
| Persona confidence | 30 | Persona match confidence scaled to 30 pts |
| Qualification signals | 30 | High-intent keywords in discovery data: demo, pricing, budget, timeline, decision, evaluate, etc. |

**Score → recommended next step:**

| Score | Recommended Next Step |
|---|---|
| 0–39 | Learn More |
| 40–59 | Evaluation Request |
| 60–74 | Consultation Request |
| 75–100 | Direct Meeting |

---

## 9. Persona Matching

Keyword/pattern scoring — no machine learning. Runs on every `update_enquiry()` call.

**Algorithm:**
1. Load all enabled `Nexus Companion Persona` records for the tenant
2. Flatten all visitor discovery data into a single searchable string
3. For each persona, extract meaningful tokens (≥3 chars, stop-words removed) from six weighted fields:

| Field | Weight |
|---|---|
| `industry` | 30 |
| `company_size` | 20 |
| `challenges` | 20 |
| `pain_points` | 15 |
| `business_maturity` | 10 |
| `goals` | 5 |

4. Count persona tokens that appear in the visitor string; normalise to 0–100
5. Return the best-scoring persona if confidence ≥ 20

**File:** `digitz_ai_nexus/nexus_companion/services/persona_matching_service.py`

---

## 10. Services Reference

### 10.1 `companion_context_service.py`

**Entry point:** `build_companion_context(conversation, ai_profile_doc, tenant) → dict`

Called once per AI turn in `_process_ai_response()`. Returns:

| Key | Content |
|---|---|
| `companion_stage` | Current journey stage string |
| `companion_persona_name` | Matched persona display name |
| `companion_persona_confidence` | Confidence float |
| `companion_discovery_summary` | Formatted bullet list of collected visitor data |
| `companion_products_block` | Formatted string of enabled products/services (deep in PRESENTING+ stages: includes conversion_type, objection_responses, disqualification_criteria) |
| `companion_references_block` | Formatted string of relevant stories/testimonials |
| `companion_playbook_name` | Playbook name for display |
| `companion_guidelines` | `communication_guidelines` from playbook |
| `companion_stage_focus` | Stage-specific directive for the LLM |
| `companion_discovery_questions` | Discovery questions from playbook |
| `companion_objection_responses` | Concern responses from playbook |
| `companion_next_step_options` | Available next steps from playbook |
| `companion_email_verified` | Bool — whether visitor email is on the conversation |

### 10.2 `enquiry_service.py`

| Function | Signature | Description |
|---|---|---|
| `get_or_create_enquiry` | `(conversation) → str` | Returns Enquiry name; creates if needed, stamps identity fields from conversation |
| `update_enquiry` | `(conversation, discovery_delta, signal=None)` | Merges discovery data, records signal in signal_log, re-runs persona matching, recalculates score |
| `advance_journey_stage_from_signal` | `(conversation, signal_type) → str` | Primary stage machine — signal-driven transitions (see signal → stage mapping) |
| `advance_journey_stage` | `(conversation, enquiry_score=None) → str` | Score-based fallback advancement (safety net) |
| `calculate_score` | `(discovery_data, persona_confidence) → int` | Returns composite 0–100 score |
| `check_escalation_threshold` | `(conversation, playbook=None) → bool` | True if score ≥ playbook threshold (default 70) |
| `check_trigger_keywords` | `(message, playbook) → bool` | True if any escalation trigger keyword appears in message |
| `mark_converted` | `(conversation, product_name=None)` | Sets enquiry_stage to CONVERTED |

### 10.3 `signal_classifier.py`

| Function | Description |
|---|---|
| `classify_signal(message, conversation_context)` | LLM signal classification; returns `{signal_type, confidence, reason}` |
| `is_conversion_signal(signal_type)` | True for READY, ASKING_PRICE, ASKING_NEXT_STEP |
| `is_resistance_signal(signal_type)` | True for OBJECTING, HESITATING, DISENGAGING, DEFLECTING |
| `is_exit_signal(signal_type)` | True for REQUESTING_HUMAN, DECLINING |

### 10.4 `persona_matching_service.py`

| Function | Description |
|---|---|
| `match_persona(discovery_data, tenant)` | Returns `{persona, persona_name, confidence, score_breakdown}` |
| `_score_persona(persona, discovery_data)` | Scores one persona; returns `(float, dict)` |
| `_flatten_discovery(discovery_data)` | Flattens discovery dict to searchable string |
| `_extract_keywords(text)` | Extracts meaningful ≥3-char tokens, removes stop-words |

### 10.5 `reference_matching_service.py`

| Function | Description |
|---|---|
| `get_relevant_references(discovery_data, matched_persona, tenant, limit=3)` | Returns list of `{type, title, industry, summary}` dicts |
| `_get_stories(tenant, industry, matched_persona, limit)` | Approved public Stories filtered by industry/persona |
| `_get_testimonials(tenant, limit)` | Top-rated approved Testimonials |
| `_get_outcomes(tenant, matched_persona, limit)` | Approved Outcomes ordered by modification date |

---

## 11. Prompt Injection

**File:** `digitz_ai_nexus/engine/prompt.py` — `_build_companion_block()`

When `query_contract.get("companion_context")` is present, a **NEXY COMPANION ENGINE** block is injected into the system prompt **after the APPROVED KNOWLEDGE block** and before the current user message.

The block structure (IDENTITY → OBJECTIVE → SITUATION → ARSENAL → DIRECTIVE → RULES):

```
APPROVED KNOWLEDGE:
{retrieved chunks}

--- NEXY COMPANION ENGINE ---

IDENTITY:
You are Nexy — an intelligent advisor built into this platform.
You combine product knowledge (from APPROVED KNOWLEDGE above) with
conversation intelligence to guide visitors toward the outcome that
best serves their situation.

OBJECTIVE:
Move this conversation toward a positive outcome for the visitor:
understood needs → matched solution → clear next step → cycle completed.
A positive outcome is not a pitch — it is the visitor leaving better
informed, with a concrete path forward that fits their situation.

CURRENT SITUATION:
Journey Stage: PRESENTING
Matched Visitor Persona: Growing SME Owner (74% confidence)

VISITOR PROFILE COLLECTED:
- Industry: Retail
- Company Size: SME
- Current Challenges: manual order tracking, slow fulfilment
- Goals: streamline operations before peak season

AVAILABLE SOLUTIONS (use APPROVED KNOWLEDGE for factual details):
Nexus Order Manager [Operations]
  Addresses: manual order process, fulfilment delays, warehouse sync
  Outcomes: 40% reduction in processing time, real-time stock visibility
  Guide phrase: "If streamlining your fulfilment is the priority, the
                 next step is a 30-minute walkthrough — I can arrange that."
  Next step type: Meeting Booking

RELEVANT REFERENCES:
[STORY] Retail SME reduces fulfilment time by 40%: ...

CONVERSATION GUIDELINES — Retail Growth Playbook:
{communication_guidelines from playbook}

YOUR DIRECTIVE FOR THIS TURN:
You are presenting a solution. Be specific about how it addresses their
stated challenges. Surface a relevant customer story or outcome to build
confidence. Invite questions. Listen for objections or interest signals.

OBJECTION LIBRARY:
{objection_responses from playbook}

LANGUAGE RULES (non-negotiable):
- Never use the words 'sell', 'sales', 'selling', or 'pitch'
- Use: advise, guide, recommend, explore, progress, take the next step
- One question per response maximum during discovery
- Be specific — use their stated challenges in your response
- Only recommend when there is genuine fit; be honest when there is not
- Do not invent pricing, timelines, or guarantees not in APPROVED KNOWLEDGE

--- END COMPANION ENGINE ---

CURRENT USER MESSAGE:
{visitor_message}
```

The block returns an empty string when companion mode is off — zero overhead on non-companion calls.

---

## 12. Response Mode

**File:** `digitz_ai_nexus/engine/response_mode.py`

The `companion_advisor` response mode is activated when companion mode is on:

```python
"companion_advisor": {
    "label": "Nexy Companion",
    "tone": "warm, confident, genuinely interested in the visitor's situation",
    "instruction": """
You are Nexy — an intelligent advisor, not a generic chatbot.
Follow the NEXY COMPANION ENGINE directives exactly — stage focus, objective, and language rules.
Ground all factual claims in APPROVED KNOWLEDGE. Do not invent details.
Be specific to the visitor's stated situation — not generic.
Drive the conversation forward; do not simply answer and wait.
One question per response in discovery mode. In presenting mode, surface relevant proof.
In converting mode, provide one clear, low-friction next step.
"""
}
```

---

## 13. Live Chat Integration

**File:** `digitz_ai_nexus_live/digitz_ai_nexus_live/services/live_chat_service.py`

### Activation

Companion mode activates when the resolved `ai_profile` dict has `companion_mode = 1`. This is populated from `Nexus AI Agent Profile.companion_mode` via `_build_ai_profile_dict()`.

### Per-turn flow inside `_process_ai_response()`

```
1. build_core_chat_payload()
       └── _build_ai_profile_dict() includes companion_mode, companion_playbook

2. Nexy enrichment (existing — digitz_ai_nexus_nexy)

3. Companion enrichment:
   if companion_mode:
       companion_context = build_companion_context(conversation, agent, tenant)
       core_payload["companion_context"] = companion_context
       core_payload["response_mode"] = "companion_advisor"

4. answer_query(core_payload)
       └── prompt.py injects NEXY COMPANION ENGINE block
       └── response_mode uses companion_advisor instruction

5. AI answer stored (add_message)

6. Post-response companion pipeline:
   a. signal = classify_signal(visitor_message, conversation_context)
   b. update_enquiry(conversation, discovery_delta={}, signal=signal)
      └── merges discovery, records signal, re-scores, re-matches persona
   c. advance_journey_stage_from_signal(conversation, signal.signal_type)
      └── signal-driven stage machine (primary)
   d. advance_journey_stage(conversation)
      └── score-based fallback (safety net)
   e. if check_escalation_threshold() or check_trigger_keywords():
          set companion_journey_stage = "ESCALATED"
          set enquiry_stage = "ESCALATED"
```

### `conversation_name` in payload

`core_payload["conversation_name"]` is always set so companion tool handlers in the agent loop can load the conversation for discovery writes.

---

## 14. Conversion Mechanisms

The conversion mechanism is configured per product/service. When Nexy detects a conversion signal (ASKING_PRICE, READY, or ASKING_NEXT_STEP) and the enquiry score exceeds `conversion_threshold_score`, Nexy guides the visitor to the configured mechanism.

| Mechanism | What happens |
|---|---|
| `Lead Capture` | Nexy confirms contact details, creates lead context, confirms follow-up timeline |
| `Meeting Booking` | Nexy presents the calendar link from `conversion_config`, visitor selects a time |
| `Direct Purchase` | Nexy presents payment link from `conversion_config`, visitor completes in-widget |
| `Subscription` | Nexy presents plan options, webhook in `conversion_config` provisions access |
| `Trial Activation` | Email verified → trial account created via webhook → login link delivered in chat |
| `Download Gate` | Email verified → download link delivered inline |
| `Human Handoff` | Nexy summarises and escalates with full enquiry context |
| `Webhook` | External endpoint in `conversion_config` handles completion |

On successful conversion: `mark_converted(conversation)` → enquiry stage → CONVERTED → `post_conversion_action` determines next state.

---

## 15. Dashboard

**File:** `digitz_ai_nexus/nexus_companion/api/companion_dashboard.py`
**Page:** `digitz_ai_nexus/nexus_companion/page/nexus_companion_dashboard/`

### `get_dashboard_data(tenant=None) → dict`

Returns in one call:
- `stage_funnel` — counts across all 11 stages
- `stats` — total, today, converted (CONVERTED stage), escalated, avg_score_7d
- `recent_enquiries` — last 20 with visitor name, persona, conversation ID
- `top_personas` — top 5 matched personas by frequency
- `config_summary` — counts of active playbooks, personas, products, services, stories, testimonials, outcomes

### `get_enquiry_detail(name) → dict`

Full detail for a single enquiry including recommended products/services, visitor name, persona name, conversation ID.

### `get_tenants() → list`

Available tenants for the tenant selector.

---

## 16. Configuration Guide

### Step 1 — Create a Companion Playbook

In **Nexus Companion Playbook → New**:
- Set `tenant`, enable it, optionally mark as `is_default`
- Write `discovery_questions` (one per line):
  ```
  What industry does your business operate in?
  How large is your team?
  What are your main operational challenges right now?
  What does a good outcome look like for you in the next 12 months?
  Are you currently evaluating alternatives?
  ```
- Write `communication_guidelines` — Nexy's behavioural rules for this deployment
- Set `escalation_score_threshold` (default 70 is fine to start)
- Optionally add `escalation_triggers` (one per line): `pricing`, `demo`, `proposal`, `quote`, `meet`

### Step 2 — Create Personas

In **Nexus Companion Persona → New** for each visitor archetype:
- Fill `industry`, `company_size`, `business_maturity`, `challenges`, `pain_points`, `goals`
- The more specific and verbose these fields are, the better persona matching performs
- Link recommended products and services (these inform Nexy's recommendations for this persona)

### Step 3 — Create Products and Services

In **Nexus Companion Product → New** (and Service):
- `challenges_solved` and `typical_outcomes` are most important — Nexy references these most heavily
- Fill `objection_responses` with specific concern/response pairs
- Fill `disqualification_criteria` — this prevents Nexy from recommending when it shouldn't
- Set `conversion_type` and configure `conversion_config` (JSON):
  ```json
  {
    "calendar_url": "https://cal.com/your-team/30min",
    "form_url": "https://your-site.com/enquiry"
  }
  ```
- Write a `conversion_message` — what Nexy says at the conversion moment
- Link `chat_category` — Nexy uses this to retrieve factual knowledge about the product
- Link to relevant `target_personas`

### Step 4 — Add References

- Create approved **Stories** with `visibility = Public`
- Create approved **Testimonials** and **Outcomes** (min: `approved = 1`)
- These surface automatically based on visitor industry and persona match

### Step 5 — Enable on AI Agent Profile

On the **Nexus AI Agent Profile** used by the target channel:
- Enable **Companion Mode**
- Select the **Companion Playbook**
- Set **Discovery Style** (Conversational recommended for website chat)

### Step 6 — Verify

1. Start a chat on the channel that uses this profile
2. On `Nexus Live Conversation`, observe `companion_journey_stage` advancing turn by turn
3. Open the linked `Nexus Companion Enquiry` — check `stage_signal`, `signal_log`, `discovery_data`, `enquiry_score`
4. After 4–5 exchanges, `matched_persona` and `persona_confidence` should populate

---

## 17. Language Compliance

Enforced at multiple layers:

| Layer | Enforcement |
|---|---|
| System prompt | `_build_companion_block()` includes non-negotiable LANGUAGE RULES: "Never use the words 'sell', 'sales', 'selling', or 'pitch'" |
| Response mode | `companion_advisor` instruction reinforces the same rule |
| Stage focus | All 11 stage focus instructions use advising/guiding language |
| DocType naming | All types and labels use Companion, Enquiry, Next Step, Concern, Outcome |
| Code | No variable, function, or field name contains "sales" or "sell" in the companion module |

---

## 18. Files Changed

| File | Change |
|---|---|
| `digitz_ai_nexus/modules.txt` | Added `Nexus Companion` |
| `digitz_ai_nexus/nexus_companion/` | New module — all DocTypes and services |
| `digitz_ai_nexus/nexus_companion/services/signal_classifier.py` | New — LLM signal classification |
| `digitz_ai_nexus/nexus_companion/doctype/nexus_companion_enquiry/*.json` | Added identity fields, signal fields, 5 new stages |
| `digitz_ai_nexus/nexus_companion/doctype/nexus_companion_product/*.json` | Added conversion config fields, chat_category, disqualification_criteria |
| `digitz_ai_nexus/nexus_companion/doctype/nexus_companion_service/*.json` | Same as Product |
| `digitz_ai_nexus/nexus_companion/services/enquiry_service.py` | Rewritten — signal-driven stage machine, update_enquiry with signal param |
| `digitz_ai_nexus/nexus_companion/services/companion_context_service.py` | Updated — 11 stage focus entries, richer products block, email verification awareness |
| `digitz_ai_nexus/nexus_companion/api/companion_dashboard.py` | Updated — 11 stages, converted count instead of qualified |
| `digitz_ai_nexus/engine/prompt.py` | Redesigned `_build_companion_block()` — directive NEXY COMPANION ENGINE framing |
| `digitz_ai_nexus/engine/response_mode.py` | Updated `companion_advisor` instruction |
| `digitz_ai_nexus_live/.../nexus_ai_agent_profile.json` | Added companion settings section |
| `digitz_ai_nexus_live/.../nexus_live_conversation.json` | Added companion journey section |
| `digitz_ai_nexus_live/services/live_chat_service.py` | Signal classification, update_enquiry with signal, signal-driven + score-based stage advancement |

---

## 19. Future Expansion

- **WhatsApp OTP verification**: The `verification_status` field on Enquiry is ready for a second channel. The widget-level OTP flow will route to `request_verification()` with a WhatsApp channel once supported.
- **Conversion UX in widget**: The chat widget needs inline components for Direct Purchase (payment form), Meeting Booking (calendar picker), and Trial Activation (account creation). The `conversion_config` JSON already carries the necessary URLs.
- **Agent loop conversion tools**: `chat_agent_loop.py` can be extended with `attempt_conversion(product_name)` and `confirm_conversion(outcome)` tools that make the conversion moment explicit in the agent's action trace.
- **Knowledge bridge**: Each product/service now has a `chat_category` link. The next step is updating `_build_products_block()` to retrieve factual product knowledge through the Nexus retrieval engine (vector + BM25 + reranker) rather than raw DB fields, so product knowledge benefits from the same governance as all other knowledge.
- **Enquiry analytics**: The `signal_log` field is the backbone for conversion funnel analytics — which signals precede CONVERTED, where do most visitors drop off, which objections are most common.
- **Human handover enrichment**: Extending `nexy_handover_service.py` to pass `companion_enquiry`, `matched_persona`, `discovery_data`, `signal_log`, and `enquiry_score` as a structured handover package for human agents.
- **Companion intent extensions**: Customer Support intent (intent = resolve, success = ticket closed), Onboarding intent (intent = activate, success = feature used), Retention intent (intent = reengage, success = renewal confirmed) — all follow the same engine structure with different stage focus entries and conversion mechanisms.
