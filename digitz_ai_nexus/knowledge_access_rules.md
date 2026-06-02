# DIGITZ AI Nexus Chat, Agent Profile, Access Governance, and Knowledge Retrieval Design Notes

**Document purpose:**  
This document consolidates the current design decisions and corrections discussed for the next phase of DIGITZ AI Nexus Chat implementation. It is intended to be used before applying DocType, API, engine, and runtime corrections one by one.

**Current implementation priority:**  
The Nexus Commercial / Customer Registration module is intentionally held for now. The current priority is to implement the Nexus Chat system, including chat runtime, AI response, escalation, continuity, website/customer interaction, access-safe knowledge retrieval, and agent profile routing.

---

## 1. High-Level Product Direction

DIGITZ AI Nexus is not only a chatbot or Q&A tool. It is becoming a governed intelligence platform that can support many future agentic capabilities. Chat is the first major live interaction layer, but the platform should remain open for future agents such as:

- Chat support agents
- Public Q&A agents
- Knowledge ingestion agents
- Source validation agents
- Workflow automation agents
- Document analysis agents
- Sales agents
- Customer onboarding agents
- ERP operation agents
- Testing agents
- Monitoring agents
- Data extraction agents
- Decision/recommendation agents

Because of this, the current chat implementation should not consume or overload the broad meaning of "Agent" for the entire Nexus platform.

---

## 2. App-Level Organization

The preferred architecture is to continue using the existing app family rather than creating a new chat app.

### 2.1 `digitz_ai_nexus`

This remains the governed AI core.

Responsibilities:

- RAG / retrieval engine
- Knowledge source, unit, and chunk management
- Access governance
- Access policy/category resolution
- AI answer service
- Prompt building
- LLM and embedding provider abstraction
- Query logging and traceability
- Source validation and testing
- Cost-control answer path later

Meaning:

```text
digitz_ai_nexus = AI brain + governed knowledge + access + answer engine
```

### 2.2 `digitz_ai_live`

This owns the live conversation runtime.

Responsibilities:

- Conversations
- Conversation messages
- AI/human participation
- Live agent state
- Escalation queue
- Handover
- Agent availability
- Continuity summary
- Live console APIs
- Runtime chat services

Meaning:

```text
digitz_ai_live = live conversation runtime
```

### 2.3 `digitz_ai_experience`

This owns the user-facing experience.

Responsibilities:

- Website widget
- Public Q&A interface
- Public chat interface
- Visitor/session handling
- Embed scripts
- Public/customer-facing API wrappers

Meaning:

```text
digitz_ai_experience = website/customer interaction layer
```

### 2.4 No New Chat App Now

A separate chat app is not recommended at this stage because Nexus Chat depends heavily on:

- Nexus knowledge
- Access governance
- AI profile and behaviour
- Live conversation runtime
- Website/customer experience
- Human escalation
- Query logging
- Future cost control

Creating another app now would add fragmentation before the core system becomes stable.

---

## 3. Nexus Chat as a Designated System Layer

Nexus Chat is not a simple widget. It is a designated live interaction layer.

It is responsible for:

- Starting conversations
- Receiving messages
- Persisting messages
- Calling the AI answer engine
- Applying conversation continuity
- Checking confidence and fallback conditions
- Escalating when needed
- Allowing human agents to take over
- Closing conversations
- Preserving summary and traceability

Clean mental model:

```text
Nexus Knowledge tells what the system knows.
Nexus Access controls what may be used.
Nexus AI Agent Profile controls how the AI responder behaves.
Nexus Live controls the conversation lifecycle.
Nexus Experience exposes it to users.
```

---

## 4. Q&A vs Chat

Q&A and Chat should remain separate response modes.

### 4.1 Q&A

Q&A is retrieval-first, answer-focused, and usually stateless.

Typical flow:

```text
Question → resolve channel → resolve AI profile via route → force Public-only → retrieve allowed approved chunks → grounded answer → query log
```

For public website Q&A:

```text
Allowed policy = Public only
```

### 4.2 Chat

Chat is conversational and supports follow-ups, continuity, escalation, and handover.

Typical flow:

```text
Start conversation
→ user sends message
→ message saved
→ runtime builds query contract
→ resolved profile behaviour is applied
→ access-safe retrieval
→ AI response saved
→ escalation if required
→ human handover if needed
```

---

## 5. Terminology and Agent Concept

### 5.1 Avoid Generic `Nexus Agent` for Chat

The term `Nexus Agent` should be protected for possible future platform-wide agentic capabilities. Chat should not consume the broad term.

Current existing terminology is better:

- `Nexus Live Agent`
- `Nexus AI Agent Profile`
- `Nexus Human Agent Profile`
- `Nexus Agent Queue`
- `Nexus Agent Activity Log`
- `Nexus Agent Onboarding`

### 5.2 Correct Current Meanings

#### Nexus Live Agent

Represents live operational identity.

It can represent:

- AI live responder
- Human live support participant

It is related to:

- agent identity
- type: AI/Human
- status
- availability
- capacity
- current active sessions
- display/avatar
- operational routing metadata

#### Nexus AI Agent Profile

Represents the AI responder configuration used by chat/Q&A runtime.

It should include:

- linked live agent
- response mode
- behaviour prompt
- tone
- response style
- welcome message
- fallback message
- do-not-answer rules
- confidence threshold
- escalation settings
- memory mode
- knowledge scope / access scope intent
- model/provider settings later if needed

This is the main runtime configuration object for AI responses.

#### Nexus Human Agent Profile

Represents a human support profile for escalation/handover.

It may include:

- linked user
- department
- skills
- queue membership
- availability/capacity
- handover capability

---

## 6. Agent Behaviour as a Subset of Agent Profile

A key correction was made:

```text
Agent Behaviour is a subset/part of Nexus AI Agent Profile.
```

The runtime should not treat `Nexus AI Behaviour` as the primary selector competing with the profile.

The runtime should ask:

```text
Which AI Agent Profile should handle this query?
```

Then it should derive behaviour from that profile.

### 6.1 Final Concept

```text
Nexus AI Agent Profile
    contains behaviour configuration
```

Behaviour-related fields may include:

- `behavior_prompt`
- `tone`
- `response_style`
- `welcome_message`
- `fallback_message`
- `do_not_answer_rules`
- `confidence_threshold`
- `escalation_enabled`
- `memory_mode`

### 6.2 Role of `Nexus AI Behaviour`

If retained, `Nexus AI Behaviour` should be treated as an optional reusable template or preset, not as the primary runtime selector.

Possible use:

```text
Nexus AI Behaviour = reusable preset
Nexus AI Agent Profile = actual runtime profile
```

But for runtime simplicity, profile must remain the main object.

---

## 7. Nexus Channel Concept

A major correction was made regarding `Nexus Channel`.

### 7.1 Channel Is Broad

`Nexus Channel` should represent a broad service or entry lane.

Examples:

- Website
- Customer Portal
- Internal Portal
- API
- Simulation
- Desk Console
- Mobile App

It should not be narrowly tied to one profile or one access policy.

### 7.2 Do Not Add Direct Single Profile Field to Channel

Avoid a direct field like:

```text
Nexus Channel.default_ai_agent_profile
```

because one channel can serve many profiles.

Example:

```text
Website Channel
    Public Q&A Profile
    Website Support Chat Profile
    Sales Enquiry Profile
    Product Recommendation Profile
```

### 7.3 Do Not Link Channel Directly to Access Policy

Avoid:

```text
Nexus Channel → Access Policy
```

Correct model:

```text
Nexus Channel
    → Nexus Channel Access Category
    → Nexus Access Category
    → Nexus Access Category Policy
    → Nexus Access Policy
```

### 7.4 Channel as Guardrail and Routing Context

The channel should participate in:

- service lane identification
- public/internal/API distinction
- access guardrail
- profile routing context
- public endpoint enforcement
- widget/site origin logic later

But the channel alone should not decide retrieval or profile selection.

---

## 8. Dynamic AI Agent Profile Resolution

The AI Agent Profile should be resolved dynamically by runtime.

### 8.1 Why Dynamic Resolution Is Needed

A query enters through a channel, but the channel may support many services.

The runtime should resolve profile based on:

- channel
- use case
- context
- sub-context
- intent
- public vs authenticated state
- route priority
- configured defaults
- possibly business unit/project later

### 8.2 Recommended Routing DocType

Add a mapping/routing DocType such as:

```text
Nexus Channel AI Profile Route
```

Alternative names:

- `Nexus Channel Profile Route`
- `Nexus Channel Service Profile`
- `Nexus AI Profile Route`

Recommended meaning:

```text
For a given channel + use case/context/intent, resolve the suitable Nexus AI Agent Profile.
```

Suggested fields:

```text
route_name
channel
use_case
context
sub_context
intent
auth_scope
ai_agent_profile
priority
is_default
enabled
description
```

Possible `auth_scope` values:

```text
Public
Authenticated
Any
```

Example records:

```text
Website / Q&A / Public / default → Public Q&A Profile
Website / Chat / Public / default → Website Support Chat Profile
Website / Chat / Public / sales → Sales Enquiry Profile
Internal Portal / Chat / Authenticated / finance → Finance Assistant Profile
```

### 8.3 Profile Resolution Fallback

When resolving a profile via `Nexus Channel AI Profile Route`:

```text
1. Match on channel + use_case + context + intent + auth_scope (most specific first, ordered by priority).
2. If no specific match, fall back to the route with is_default = 1 for the channel.
3. If still no match, reject the request with an explicit error.
```

Silent fallback to any profile must never happen. A missing route configuration should surface as an explicit error, not cause an unexpected profile to handle the query.

---

## 9. Access Governance Model

The current access structure is correct in concept.

### 9.1 Core DocTypes

- `Nexus Access Policy`
- `Nexus Access Category`
- `Nexus Access Category Policy`
- `Nexus Channel Access Category`
- `Nexus Role Access Category`

### 9.2 Meaning

#### Nexus Access Policy

Actual classification attached to knowledge.

Examples:

- Public
- Internal
- Finance
- HR
- Support
- Legal
- Partner Confidential
- Project Alpha

Only `Public` should be primitive/system-defined. Everything else should be user-defined.

#### Nexus Access Category

A group of access policies.

Example:

```text
Public Website Category
    Public

Internal Support Category
    Public
    Internal
    Support

Finance Category
    Public
    Internal
    Finance
```

#### Nexus Access Category Policy

Mapping between category and policies.

```text
Access Category → Access Policy
```

#### Nexus Channel Access Category

Channel-side access boundary.

```text
Channel → Access Category
```

#### Nexus Role Access Category

Role-side access boundary.

```text
Role → Access Category
```

### 9.3 Final Access Rule

For authenticated/internal users:

```text
Final Allowed Policies =
    Profile intended policies/categories
    ∩ User/Role allowed policies/categories
    ∩ Channel/public guardrail policies
```

For public endpoints:

```text
Final Allowed Policies = ["Public"]
```

Public-only enforcement must override any wrong route/profile configuration.

#### Fail-Closed Rule

If the intersection produces an empty set, retrieval must be denied entirely.

```text
If final_allowed_policies = {} → deny retrieval, do not proceed.
```

Access must always fail closed, never fail open. An empty policy set must never be interpreted as "no filter" or "allow all".

---

## 10. Concern with Hard-Coded Select Values

The `Nexus Access Policy` DocType had hard-coded Select options such as:

- Public
- Customer Restricted
- Internal
- Role Restricted
- Finance Restricted
- HR Confidential
- Admin Only

and sensitivity values such as:

- public
- customer
- operational
- internal
- financial
- hr
- confidential

The concern is valid.

### 10.1 Correction Principle

Access concepts should be configurable, not hard-coded.

Final principle:

```text
Only Public is primitive.
All other access policies are user-defined.
```

### 10.2 Recommended Correction

In `Nexus Access Policy`, use:

- `policy_name`
- `disabled`
- `is_primitive`
- `description`

Avoid required hard-coded fields for `access_level` and `sensitivity`.

If retained, they must be optional metadata only and must not drive enforcement.

### 10.3 Enforcement Key

The enforcement key should be:

```text
policy_name
```

not:

```text
access_level
sensitivity
```

---

## 11. Knowledge Source and Access Relationship

The uploaded `Nexus Knowledge Source` JSON already has a meaningful access relationship.

It includes:

```text
access_policy → Link to Nexus Access Policy
```

This is correctly placed under the Governance section.

### 11.1 Meaning

```text
Nexus Knowledge Source.access_policy
    = source-level access classification
```

The source also includes business classification fields:

- tenant
- business_unit
- project
- context
- sub_context
- entity_type
- entity
- topic

These are business/retrieval metadata, not direct access enforcement.

### 11.2 Correct Propagation

Access should propagate through the knowledge lifecycle:

```text
Nexus Knowledge Source.access_policy
    ↓ copied to
Nexus Knowledge Unit.access_policy
    ↓ copied to
Nexus Knowledge Chunk.access_policy
```

Runtime retrieval should filter at chunk level because chunks are the actual retrievable records.

Correct retrieval rule:

```text
Nexus Knowledge Chunk.access_policy in final_allowed_access_policies
```

### 11.3 Source-Level Access Is Not Enough

The source-level policy is important for governance and lifecycle management, but retrieval needs chunk-level policy for safe, fast filtering.

### 11.4 Publishing Rule

Access policy should be required before publish, not necessarily during draft.

Suggested validation rule:

```python
if doc.status in ("Ready to Publish", "Published") and not doc.access_policy:
    frappe.throw("Access Policy is required before publishing this Knowledge Source.")
```

### 11.5 Retrieval Readiness

A chunk/source should not be retrievable just because it has an access policy.

Retrieval should also require:

- source published or retrieval-ready
- chunk active
- embedding completed
- validation passed where required
- not disabled

Possible retrieval condition:

```text
chunk.access_policy in allowed_policies
AND chunk.is_active = 1
AND source.status = Published
AND source.retrieval_ready = 1
```

#### When `retrieval_ready` Is Set

`source.retrieval_ready` must be set to `1` only after all of the following conditions are met:

```text
1. source.status = Published
2. At least one active chunk exists for this source with embedding_status = Completed
3. Source-level validation has passed (if validation is required for this source type)
```

It must be reset to `0` if the source is unpublished, re-ingested, or its access policy changes, until the above conditions are satisfied again.

---

## 12. Retrieval Should Be Profile-Driven, Not Channel-Driven

A key architectural decision:

```text
Knowledge retrieval should be driven by the dynamically resolved AI Agent Profile/service profile, not directly by Nexus Channel alone.
```

### 12.1 Correct Flow

```text
Request comes through channel
    ↓
Runtime identifies use case/context/intent/user state
    ↓
Runtime resolves AI Agent Profile
    ↓
Runtime resolves profile intended access scope
    ↓
Runtime resolves actual user/role access scope
    ↓
Runtime resolves channel/public guardrail
    ↓
Final allowed policies are calculated
    ↓
Retrieval filters chunks by final allowed policy names
```

### 12.2 Why This Is Correct

The channel is only the entry lane. The profile represents the designated AI responder/service capability.

However, the profile must not bypass security.

Therefore:

```text
Resolved profile scope
∩ User/role scope
∩ Channel/public guardrail
= Final retrieval boundary
```

---

## 13. Query Contract Direction

The query contract should eventually include enough resolved information so the retrieval and answer engine do not guess.

Suggested shape:

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

    "profile_access_categories": profile_access_categories,
    "channel_access_categories": channel_access_categories,
    "role_access_categories": role_access_categories,

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

Retrieval should depend mainly on:

```python
query_contract["allowed_access_policies"]
```

Prompting should depend mainly on:

```python
query_contract["ai_profile"]
```

#### Guard: Never Allow Empty Policy List

Before passing the contract to retrieval, validate:

```python
if not query_contract.get("allowed_access_policies"):
    frappe.throw("Access policy resolution failed. Retrieval cannot proceed.")
```

An empty list must never reach the retrieval layer. Some query builders silently treat `IN []` as "match nothing" while others may raise an error or behave unexpectedly. Failing explicitly here prevents silent data leaks or broken responses.

---

## 14. API Corrections Needed

### 14.1 Public Q&A API

Should not directly use channel as the source of profile or access.

Correct flow:

```text
resolve site/widget
resolve channel
resolve profile through route
force Public-only
build query contract
call answer service
```

Public Q&A must always force:

```python
allowed_access_policies = ["Public"]
force_public_only = True
```

### 14.2 Public Chat `start_chat`

Correct flow:

```text
resolve site/widget
resolve broad channel
resolve AI profile through Channel AI Profile Route
resolve public guardrail
create conversation
store assigned_ai_agent_profile
store assigned_live_agent if applicable
store access/profile snapshots if needed
```

### 14.3 Public Chat `send_chat_message`

Correct flow:

```text
load conversation
do not re-resolve profile from channel every message
use conversation.assigned_ai_agent_profile
build query contract
resolve final access
call answer service
save AI response
check confidence/escalation
```

The assigned profile should be stored in the conversation so behaviour does not change accidentally if routing configuration changes later.

### 14.4 Internal Chat

Correct flow:

```text
resolve channel
resolve profile through route
resolve logged-in user roles
resolve profile access scope
resolve role access scope
resolve channel guardrail
final allowed policies = intersection
retrieve and answer
```

---

## 15. Engine Corrections Needed

### 15.1 `access_resolver.py`

Should calculate final allowed policy names.

Expected output:

```python
{
    "allowed_access_policies": ["Public", "Internal"],
    "profile_policy_names": [...],
    "channel_policy_names": [...],
    "role_policy_names": [...],
    "force_public_only": False,
}
```

For public endpoints:

```python
{
    "allowed_access_policies": ["Public"],
    "force_public_only": True,
}
```

It should use:

- `Nexus Channel Access Category`
- `Nexus Role Access Category`
- `Nexus Access Category Policy`
- `Nexus Access Policy`
- profile access category mapping if added

It should not use hard-coded `access_level` or `sensitivity` for enforcement.

### 15.2 `retrieval.py`

Must filter chunks by final allowed policy names.

Correct principle:

```python
allowed_policies = query_contract.get("allowed_access_policies") or []
```

Then:

```text
chunk.access_policy in allowed_policies
```

Avoid using:

- channel name as access filter
- access_level for permission
- sensitivity for permission
- business unit/project as security substitute

Business unit/project/context can help relevance, but not replace access policy.

### 15.3 `answer_service.py`

Should accept the resolved query contract and avoid deciding raw permissions itself.

It should orchestrate:

- access resolver
- retrieval
- prompt builder
- LLM call
- answer packaging
- query log

### 15.4 `prompt.py`

Should build instructions from `Nexus AI Agent Profile` behaviour fields.

Use:

- behavior_prompt
- tone
- response_style
- fallback_message
- do_not_answer_rules
- memory_mode
- response mode

Do not treat `Nexus AI Behaviour` as a separate primary runtime selector unless it is only used as a template to populate profile fields.

### 15.5 Cost-Control Service Later

If a query matches a validated known question/source trace, Nexus can use lower-cost paths:

- cached approved answer
- approved short template
- known chunk shortlist
- reduced context
- smaller model

But cost control must still enforce:

```text
final allowed access policies
source version validity
profile route validity
public guardrail
```

---

## 16. Conversation Runtime Corrections

`Nexus Conversation` should store the resolved runtime configuration.

Recommended fields to verify/add:

```text
channel
use_case
conversation_type
assigned_ai_agent_profile
assigned_live_agent
assigned_human_agent_profile
force_public_only
access_policy_snapshot_json
ai_profile_snapshot_json
status
escalation_status
continuity_context
last_message_at
closed_at
closure_summary
```

Important reason:

```text
A conversation should preserve which profile and access snapshot was used when it started.
```

If route configuration changes later, existing conversations should not unexpectedly change behaviour midway.

---

## 17. Knowledge DocTypes to Verify

### 17.1 Nexus Knowledge Source

Already has:

```text
access_policy → Nexus Access Policy
```

Good.

### 17.2 Nexus Knowledge Unit

Should have:

```text
access_policy → Nexus Access Policy
source → Nexus Knowledge Source
```

It should inherit from source during processing.

### 17.3 Nexus Knowledge Chunk

Should have:

```text
access_policy → Nexus Access Policy
knowledge_source
knowledge_unit
is_active
status/retrieval_ready
embedding fields
```

It should inherit from unit/source and be the actual object used in retrieval filtering.

---

## 18. DocType Corrections Summary

### 18.1 `Nexus Channel`

Keep broad/minimal.

Do not add:

```text
default_ai_agent_profile
access_policy
default_access_policy
```

Possible future safe fields:

```text
is_public_endpoint
requires_login
rate_limit_profile
allowed_origin/domain
```

But not required now.

### 18.2 `Nexus Access Policy`

Simplify.

Recommended core:

```text
policy_name
disabled
is_primitive
description
```

Make any hard-coded `access_level` or `sensitivity` optional metadata only, or remove them.

### 18.3 `Nexus AI Agent Profile`

Main runtime AI responder profile.

Behaviour is a subset of profile.

Should include or retain:

```text
agent
behavior_prompt
tone
response_style
welcome_message
fallback_message
do_not_answer_rules
default_response_mode
confidence_threshold
escalation_enabled
escalation_policy
memory_mode
system_notes
```

Need to verify whether knowledge scope should be converted from hard-coded JSON fields to profile access category mappings.

### 18.4 `Nexus AI Behaviour`

Optional template only.

Do not make it the primary routing object.

### 18.5 New: `Nexus Channel AI Profile Route`

Needed to avoid direct channel-profile coupling.

### 18.6 Possible New: `Nexus AI Agent Profile Access Category`

Needed if profile scope is to be governed through access categories rather than hard-coded JSON fields.

Purpose:

```text
AI Agent Profile → Access Category
```

This allows:

```text
Profile intended scope ∩ Role scope ∩ Channel/public guardrail
```

---

## 19. Recommended New Profile Access Mapping

Because retrieval should be driven by profile but access-safe, the profile should have intended access categories.

Recommended new mapping DocType:

```text
Nexus AI Agent Profile Access Category
```

Suggested fields:

```text
ai_agent_profile
access_category
enabled
priority
description
```

Meaning:

```text
This profile is intended to use knowledge from these categories.
```

Final access still intersects with role and channel guardrail.

---

## 20. Correct Final Retrieval Boundary

The final retrieval boundary should be:

```text
final_allowed_policies =
    profile_allowed_policies
    ∩ role_allowed_policies
    ∩ channel_guardrail_policies
```

For public:

```text
final_allowed_policies = {"Public"}
```

For authenticated:

```text
final_allowed_policies = profile ∩ role ∩ channel
```

Retrieval must use:

```text
chunk.access_policy IN final_allowed_policies
```

---

## 21. Testing Requirements

Tests should verify:

### 21.1 Public Q&A

- Public Q&A retrieves only `Public`.
- Internal/restricted chunks are not retrieved.
- Wrong profile route cannot bypass public-only guardrail.

### 21.2 Public Chat

- Website chat resolves public chat profile.
- Conversation stores assigned AI profile.
- Public chat retrieves only `Public`.
- Low confidence escalates if profile allows escalation.

### 21.3 Internal Chat

- Internal profile route is selected correctly.
- Final policies are profile ∩ role ∩ channel.
- User without Finance role cannot retrieve Finance even if profile is Finance.
- User with Finance role can retrieve Finance only if channel/profile also allow it.

### 21.4 Profile Behaviour

- Different profiles produce different tone/response style.
- Behaviour is derived from profile fields.
- Fallback message comes from profile.
- Do-not-answer rules are included in prompt.

### 21.5 Knowledge Access Propagation

- Source access policy copies to unit.
- Unit access policy copies to chunks.
- Retrieval filters chunks by chunk access policy.
- Published/retrieval-ready state is enforced.

---

## 22. Code Search Checklist Before Corrections

Run searches before modifying code.

```bash
grep -R "default_ai_agent_profile" apps/digitz_ai_nexus apps/digitz_ai_live apps/digitz_ai_experience
grep -R "access_level" apps/digitz_ai_nexus apps/digitz_ai_live apps/digitz_ai_experience
grep -R "sensitivity" apps/digitz_ai_nexus apps/digitz_ai_live apps/digitz_ai_experience
grep -R "Nexus AI Behaviour" apps/digitz_ai_nexus apps/digitz_ai_live apps/digitz_ai_experience
grep -R "behaviour" apps/digitz_ai_nexus apps/digitz_ai_live apps/digitz_ai_experience
grep -R "Nexus Channel" apps/digitz_ai_nexus apps/digitz_ai_live apps/digitz_ai_experience
grep -R "allowed_access" apps/digitz_ai_nexus apps/digitz_ai_live apps/digitz_ai_experience
grep -R "force_public_only" apps/digitz_ai_nexus apps/digitz_ai_live apps/digitz_ai_experience
grep -R "access_policy" apps/digitz_ai_nexus apps/digitz_ai_live apps/digitz_ai_experience
```

Look specifically for:

- direct channel → profile logic
- direct channel → access policy logic
- retrieval based on access_level
- retrieval based on sensitivity
- behaviour resolved outside profile
- public routes missing force_public_only
- chunks missing access_policy filter
- source access not propagated to chunks

---

## 23. Practical Correction Order

Recommended order:

1. Finalize `Nexus Access Policy` simplification.
2. Keep `Nexus Channel` broad and minimal.
3. Add `Nexus Channel AI Profile Route`.
4. Add `Nexus AI Agent Profile Access Category` DocType to map profiles to access categories (design decided in Section 19).
5. Verify `Nexus AI Agent Profile` remains main behaviour holder.
6. Update `start_chat()` to resolve profile through route.
7. Update `send_chat_message()` to use conversation assigned profile.
8. Update public Q&A route to resolve profile and force Public-only.
9. Update access resolver to calculate final allowed policy names.
10. Update retrieval to filter by chunk access policy only.
11. Update source processing to propagate source access policy to unit/chunk.
12. Update prompt builder to use AI Agent Profile behaviour fields.
13. Add tests for public/internal/profile/access combinations.
14. Add query log/access trace for debugging and governance.

---

## 24. Final Architecture Snapshot

```text
Request
    ↓
Channel
    = broad entry/service lane
    ↓
Runtime route resolver
    = resolves AI Agent Profile by channel + use case + context + intent + auth state
    ↓
AI Agent Profile
    = behaviour + response configuration + intended knowledge scope
    ↓
Access resolver
    = profile scope ∩ user/role scope ∩ channel/public guardrail
    ↓
Final allowed policies
    ↓
Retrieval
    = active/published chunks where chunk.access_policy in final allowed policies
    ↓
Prompt builder
    = uses Agent Profile behaviour fields
    ↓
LLM answer
    ↓
Conversation/message/query log
    ↓
Escalation/handover if needed
```

---

## 25. Final Design Principles

1. **Do not make Channel too narrow.**  
   Channel is a broad service lane, not one profile or one policy.

2. **Do not use hard-coded access Selects for enforcement.**  
   `policy_name` is the access identity.

3. **Only Public is primitive.**  
   Every non-public access policy is configurable.

4. **Agent Profile is the runtime AI responder configuration.**  
   Behaviour is a subset of profile.

5. **Profile drives intended retrieval scope.**  
   But profile cannot bypass user/channel/public guardrails.

6. **Final retrieval is policy-name based.**  
   Retrieval filters chunks by final allowed access policy names.

7. **Public endpoints always force Public-only.**

8. **Source access must propagate to chunks.**

9. **Conversation should store resolved profile and access snapshots.**

10. **Future agentic platform should remain open.**  
    Do not overload current chat-specific terms into universal platform agent concepts.

---

## 26. Immediate Next Implementation Target

The next practical implementation step should be:

```text
Correction 1: Clean up Nexus Access Policy hard-coded Select usage.
```

Then:

```text
Correction 2: Add Channel AI Profile Route.
```

Then:

```text
Correction 3: Add/verify profile access category mapping and update access resolver.
```

Only after these structural corrections should chat runtime code be finalized.