You are working inside the DIGITZ AI Nexus codebase. Before making any code or DocType changes, carefully understand the app isolation and architecture described below.

# DIGITZ AI Nexus App Architecture Context

DIGITZ AI Nexus is not a single chatbot app. It is a governed AI platform split across multiple existing Frappe apps. Each app has a different responsibility. Do not mix responsibilities unless explicitly instructed.

The current apps are:

```text
digitz_ai_nexus
digitz_ai_nexus_live
digitz_ai_experience
```

A new chat app should NOT be created unless explicitly requested. The current design is to use the existing app family and keep responsibilities isolated.

---

# 1. `digitz_ai_nexus`

## Purpose

`digitz_ai_nexus` is the core AI governance and knowledge intelligence app.

It owns the AI brain, access governance, knowledge lifecycle, retrieval engine, answer service, prompt construction, and query logging.

Think of this app as:

```text
digitz_ai_nexus = governed AI core + knowledge + access + answer engine
```

## What belongs here

This app should contain:

```text
Knowledge Source
Knowledge Unit
Knowledge Chunk
Access Policy
Access Category
Access Category Policy
Role Access Category
Channel Access Category
Access Resolver
Retrieval Engine
Answer Service
Prompt Builder
LLM / Embedding integration
Query Log
Knowledge testing / validation
Source lifecycle
```

## What should NOT belong here

This app should not directly own:

```text
Website widget UI
Visitor chat widget frontend
Live agent console UI
Human agent queue runtime
Conversation handover UI
Public website embed script
```

Those belong to the live/experience apps.

---

# 2. `digitz_ai_nexus_live`

## Purpose

`digitz_ai_nexus_live` owns live interaction and conversation runtime.

It handles chat conversations, live agents, AI/human handover, escalation, message persistence, and chat runtime services.

Think of this app as:

```text
digitz_ai_nexus_live = live conversation runtime
```

## What belongs here

This app should contain:

```text
Nexus Live Agent
Nexus AI Agent Profile
Nexus Human Agent Profile
Nexus Live Channel
Nexus Conversation
Nexus Conversation Message
Nexus Agent Queue
Nexus Agent Activity Log
Nexus Escalation Rule
Nexus Chat Category
Nexus Category Identity Route
Nexus AI Agent Profile Access Category
live_chat_service.py
live_qa_service.py
handover_service.py
escalation_service.py
agent routing
availability logic
conversation continuity
```

## What should NOT belong here

This app should not duplicate:

```text
RAG retrieval logic
Access policy/category enforcement logic
Knowledge chunking
Embedding generation
Knowledge source lifecycle
Prompt construction rules already in core
```

Those should stay in `digitz_ai_nexus`.

`digitz_ai_nexus_live` should call the core answer/access services instead of reimplementing them.

---

# 3. `digitz_ai_experience`

## Purpose

`digitz_ai_experience` owns user-facing and website/customer-facing interaction surfaces.

It exposes the Nexus system to website visitors, customer portal users, public Q&A users, and embedded widgets.

Think of this app as:

```text
digitz_ai_experience = public/customer-facing experience layer
```

## What belongs here

This app should contain:

```text
Website chat widget
Public Q&A widget
Embed scripts
Visitor session logic
Website/customer interaction APIs
Widget configuration
Public experience pages
Customer-facing UI wrappers
```

## What should NOT belong here

This app should not own:

```text
Access resolver
Retrieval engine
Knowledge chunk DB logic
Core AI answer generation
Live handover business rules
Access category enforcement
```

It should call `digitz_ai_nexus_live` or `digitz_ai_nexus` services.

---

# 4. Important Design Boundaries

## 4.1 Channel must remain broad

A channel is a service/entry lane.

Examples:

```text
Website
Customer Portal
Internal Portal
API
Simulation
Desk Console
Mobile App
```

Do NOT treat channel as one fixed agent or one fixed access policy.

Avoid direct fields like:

```text
Nexus Channel.default_ai_agent_profile
Nexus Channel.access_policy
Nexus Channel.default_access_policy
```

The better model is:

```text
Channel = broad entry/service lane
Profile Route = resolves which AI profile should respond
Channel Access Category = guardrail for what the channel may expose
```

---

# 5. Channel and Profile Routing

A channel may serve many AI profiles.

Example:

```text
Website Channel
    Public Q&A Profile
    Website Support Chat Profile
    Sales Enquiry Profile
    Product Recommendation Profile
```

Therefore chat profile selection happens through the chat category identity route, not by hardcoding a single profile into the channel.

Active routing purpose:

```text
Resolve the correct Nexus AI Agent Profile based on:
    channel
    chat_category
    identity_type
    route priority
```

Example:

```text
Website / Q&A / Public Visitor
    → Public Q&A Profile

Website / Support Chat / Customer
    → Website Support Chat Profile

Website / Sales Chat / Prospect
    → Sales Enquiry Profile

Internal Portal / Finance Chat / Employee
    → Finance Assistant Profile
```

---

# 6. AI Agent Profile and Behaviour

## 6.1 Agent Profile is the main runtime AI responder configuration

`Nexus AI Agent Profile` is the main runtime AI profile.

It controls:

```text
linked live agent
default response mode
behaviour prompt
tone
response style
welcome message
fallback message
do-not-answer rules
confidence threshold
escalation setting
memory mode
system notes
```

## 6.2 Behaviour is a subset of Agent Profile

Do NOT treat `Nexus AI Behaviour` as the primary runtime selector competing with the profile.

Correct concept:

```text
AI Agent Profile = complete runtime AI responder configuration
Agent Behaviour = behaviour section/subset of the profile
```

If `Nexus AI Behaviour` exists, treat it only as an optional reusable template/preset.

Runtime should use:

```text
query_contract["ai_profile"]
```

not random flat fields like:

```text
agent_tone
agent_response_style
agent_behavior_prompt
```

---

# 7. Access Governance Model

Access governance is category-based, not direct role-to-policy.

Do NOT implement this as the primary model:

```text
Role → Access Policy
```

Correct model:

```text
Role → Nexus Access Category → Nexus Access Policy
```

Meaning:

```text
Nexus Access Policy
    = knowledge classification

Nexus Access Category
    = group of access policies

Nexus Role Access Category
    = maps Frappe Role to Nexus Access Category

Nexus Channel Access Category
    = maps Channel to Nexus Access Category

Nexus AI Agent Profile Access Category
    = maps AI Agent Profile to Nexus Access Category
```

---

# 8. Access Policy Meaning

`Nexus Access Policy` is a classification of knowledge, not an audience.

Example:

```text
Finance
```

does NOT mean:

```text
Only Finance department can access this.
```

It means:

```text
This is Finance-classified knowledge.
```

Accounts, Management, Finance, or other roles/profiles can access Finance-classified knowledge if their assigned access categories include the `Finance` policy.

Example:

```text
Nexus Access Policy:
    Finance

Nexus Access Category:
    Accounts Access
        includes Finance

Nexus Access Category:
    Management Access
        includes Finance

Nexus Role Access Category:
    Accounts User → Accounts Access
    Management User → Management Access
```

So the same Finance-classified source can be accessible to Accounts and Management through categories.

---

# 9. Final Access Calculation

The final allowed access policies should be calculated as:

```text
final_allowed_policies =
    profile_allowed_policies
    ∩ role_allowed_policies
    ∩ channel_guardrail_policies
```

For public/guest users:

```text
final_allowed_policies = ["Public"]
force_public_only = True
```

Public routes must never depend on role mappings.

Public Q&A and public chat must always force Public-only access even if a wrong AI profile route is configured.

---

# 10. Knowledge Source Access

`Nexus Knowledge Source.access_policy` is the source-level classification key.

It should propagate through the knowledge lifecycle:

```text
Nexus Knowledge Source.access_policy
    ↓
Nexus Knowledge Unit.access_policy
    ↓
Nexus Knowledge Chunk.access_policy
```

Runtime retrieval must filter at chunk level:

```text
Nexus Knowledge Chunk.access_policy IN final_allowed_policies
```

Source-level access is the origin. Chunk-level access is the runtime enforcement key.

---

# 11. Access Policy vs Context

Do not confuse access with business relevance.

Access fields:

```text
access_policy
allowed_access_policies
access_category
```

Business/retrieval metadata fields:

```text
business_unit
project
context
sub_context
entity_type
entity
topic
```

Correct rule:

```text
Access controls whether a chunk is eligible.
Context/topic/project controls whether an eligible chunk is relevant.
```

Never use `business_unit`, `project`, `context`, `topic`, `sensitivity`, or `access_level` as the final access permission.

---

# 12. Hard-Coded Select Fields

Avoid using hard-coded Select options as enforcement rules.

In `Nexus Access Policy`, fields like:

```text
access_level
sensitivity
```

should be optional metadata only, not enforcement keys.

The enforcement key is:

```text
policy_name
```

Only `Public` is primitive/system-defined. All other policies are user-defined.

---

# 13. Retired Role Access Allocation UI

The custom role access allocation page has been removed from the active product. Runtime access enforcement is profile-first:

```text
Nexus AI Agent Profile → Nexus Access Category → Nexus Access Policy
```

`Nexus Role Access Category` can remain as a legacy/reporting DocType, but it must not be treated as the runtime source of retrieval access.

Do not edit legacy fields like:

```text
allowed_roles
excluded_roles
allowed_designations
excluded_designations
```

inside `Nexus Access Policy`.

---

# 14. Important DocTypes by App

## In `digitz_ai_nexus`

Important DocTypes:

```text
Nexus Knowledge Source
Nexus Knowledge Unit
Nexus Knowledge Chunk
Nexus Access Policy
Nexus Access Category
Nexus Access Category Policy
Nexus Role Access Category
Nexus Channel Access Category
Nexus Query Log
```

Important services/modules:

```text
access_resolver.py
retrieval.py
answer_service.py
prompt.py
embedding service
knowledge source processing
query logging
```

## In `digitz_ai_nexus_live`

Important DocTypes:

```text
Nexus Live Agent
Nexus AI Agent Profile
Nexus Human Agent Profile
Nexus Live Channel
Nexus Chat Category
Nexus Category Identity Route
Nexus AI Agent Profile Access Category
Nexus Conversation
Nexus Conversation Message
Nexus Agent Queue
Nexus Escalation Rule
```

Important services/modules:

```text
live_chat_service.py
live_qa_service.py
conversation_service.py
handover_service.py
escalation_service.py
agent routing / profile resolution
```

## In `digitz_ai_experience`

Likely responsibilities:

```text
Website widget
Public Q&A widget
Visitor session
Public chat frontend
Embed scripts
Experience/customer APIs
```

---

# 15. Runtime Flow

## 15.1 Public Q&A

```text
Website/Public Q&A request
    ↓
Resolve channel
    ↓
Resolve AI Agent Profile through route
    ↓
force_public_only = True
    ↓
allowed_access_policies = ["Public"]
    ↓
Call answer_service
    ↓
Retrieval filters Public chunks only
```

## 15.2 Public Chat

```text
Website chat starts
    ↓
Resolve live channel
    ↓
Resolve AI profile through route
    ↓
Create conversation
    ↓
Store assigned AI profile
    ↓
User sends message
    ↓
Resolve allowed policies with Public-only guardrail
    ↓
Call answer_service
    ↓
Save AI response
    ↓
Escalate if confidence/fallback rules require
```

## 15.3 Authenticated/Internal Chat

```text
Authenticated user asks question
    ↓
Resolve AI Agent Profile
    - internal user: Nexus User Profile Assignment
    - chat user: Nexus Chat Category + Identity Route
    - direct integration: explicit profile/agent context
    ↓
Resolve profile access categories
    ↓
Resolve Access Policies from those categories
    ↓
final_allowed_policies = profile policies
    ↓
Retrieve chunks where access_policy is allowed
    ↓
Answer using AI profile behaviour
```

---

# 16. Query Contract Expectations

A good query contract should include:

```python
query_contract = {
    "query": message,
    "original_query": message,
    "use_case": "chat",
    "response_mode": "chat",

    "channel": channel,
    "resolved_ai_agent_profile": ai_profile.name,

    "conversation_id": conversation_id,
    "conversation_context": continuity_context,

    "user_id": user_id,
    "user_roles": user_roles,
    "is_public": is_public,
    "force_public_only": is_public,

    "allowed_access_policies": final_allowed_policy_names,

    "ai_profile": {
        "name": ai_profile.name,
        "agent": ai_profile.agent,
        "behavior_prompt": ai_profile.behavior_prompt,
        "tone": ai_profile.tone,
        "response_style": ai_profile.response_style,
        "welcome_message": ai_profile.welcome_message,
        "fallback_message": ai_profile.fallback_message,
        "do_not_answer_rules": ai_profile.do_not_answer_rules,
        "confidence_threshold": ai_profile.confidence_threshold,
        "escalation_enabled": ai_profile.escalation_enabled,
        "memory_mode": ai_profile.memory_mode,
        "default_response_mode": ai_profile.default_response_mode,
    }
}
```

Retrieval should use:

```python
query_contract["allowed_access_policies"]
```

Prompt should use:

```python
query_contract["ai_profile"]
```

---

# 17. Fail-Closed Rules

Access must fail closed.

If:

```python
allowed_access_policies == []
```

then retrieval/answer generation must stop.

Do not silently retrieve all chunks.

If public:

```python
force_public_only = True
allowed_access_policies = ["Public"]
```

If role/profile/channel mappings are missing for authenticated users, do not accidentally allow all knowledge.

---

# 18. Code Change Rules

When modifying code:

1. Do not mix app responsibilities.
2. Do not create a new app unless explicitly instructed.
3. Do not directly assign policies to roles.
4. Do not directly bind one profile to a broad channel unless legacy/fallback only.
5. Do not use `access_level` or `sensitivity` for enforcement.
6. Do not use business context as security.
7. Do not bypass public-only rules.
8. Do not duplicate retrieval logic in live/experience apps.
9. Do not remove existing legacy fields unless explicitly asked.
10. Prefer minimal, safe changes.
11. Preserve existing working behaviour unless it conflicts with the access governance model.
12. Always explain files changed and why.

---

# 19. Useful Verification Commands

Before and after changes, search:

```bash
grep -R "allowed_access_policies" apps/digitz_ai_nexus apps/digitz_ai_nexus_live apps/digitz_ai_experience
grep -R "resolve_allowed_policies" apps/digitz_ai_nexus apps/digitz_ai_nexus_live apps/digitz_ai_experience
grep -R "Nexus Role Access Category" apps/digitz_ai_nexus apps/digitz_ai_nexus_live apps/digitz_ai_experience
grep -R "Nexus AI Agent Profile Access Category" apps/digitz_ai_nexus apps/digitz_ai_nexus_live apps/digitz_ai_experience
grep -R "Nexus Category Identity Route" apps/digitz_ai_nexus apps/digitz_ai_nexus_live apps/digitz_ai_experience
grep -R "access_level" apps/digitz_ai_nexus apps/digitz_ai_nexus_live apps/digitz_ai_experience
grep -R "sensitivity" apps/digitz_ai_nexus apps/digitz_ai_nexus_live apps/digitz_ai_experience
grep -R "default_agent" apps/digitz_ai_nexus apps/digitz_ai_nexus_live apps/digitz_ai_experience
grep -R "access_policy" apps/digitz_ai_nexus apps/digitz_ai_nexus_live apps/digitz_ai_experience
```

After DocType changes:

```bash
bench --site digitz_ai_nexus.site migrate
bench --site digitz_ai_nexus.site clear-cache
```

Use this site name when site-specific bench commands are needed:

```text
digitz_ai_nexus.site
```

---

# 20. Final Mental Model

Keep this model:

```text
Channel
    = where the query enters

AI Agent Profile
    = how the AI responder behaves and what scope it is intended to serve

Access Category
    = reusable grouping of policies

Access Policy
    = knowledge classification

Role Access Category
    = what a role can consume

Channel Access Category
    = channel guardrail

Profile Access Category
    = profile intended knowledge scope

Knowledge Source.access_policy
    = source classification

Knowledge Chunk.access_policy
    = runtime retrieval enforcement key

Final allowed policies
    = profile scope ∩ role scope ∩ channel guardrail

Retrieval
    = chunks where chunk.access_policy is in final allowed policies
```

This architecture must be preserved.
