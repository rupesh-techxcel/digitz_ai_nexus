# DIGITZ AI Nexus — Access and Profile Resolution Redesign Plan

**Status:** In Progress
**Last Updated:** 2026-06-03

---

## 1. Executive Summary

This plan documents the architectural redesign of how access governance and AI profile resolution work across the DIGITZ AI Nexus platform.

**The problem with the previous design:**
- Access was resolved through a three-way intersection: channel scope ∩ role scope ∩ profile scope
- Role-based access only works for Frappe desk users — external users (guests, customers, partners) have no Frappe roles
- Behaviour fields (tone, response style, etc.) were incorrectly treated as belonging to `Nexus AI Behaviour` rather than `Nexus AI Agent Profile`
- No clean, unified chain from identity to knowledge

**The new design in one sentence:**
Every query — from any person, through any channel — resolves to exactly one Agent Profile, and that profile is the single access authority.

```
Any person  →  predefined record  →  Agent Profile  →  Access Category  →  [Policies]  →  Knowledge
```

---

## 2. Core Design Decisions

### Decision 1 — Profile is the sole runtime access authority

`Nexus AI Agent Profile` → `Nexus AI Agent Profile Access Category` → `Nexus Access Category` → `[Nexus Access Policy]`

`Nexus Channel Access Category` and `Nexus Role Access Category` are **retired from the runtime enforcement path**. Their DocTypes are kept but `access_resolver.py` no longer calls them during a query.

### Decision 2 — Channel is transport only

A channel defines the communication medium (Chat, Q&A, WhatsApp, API, Portal). It does not set access policy ceilings. Knowledge access is entirely governed by the profile.

### Decision 3 — Two profile resolution paths

| User type | Resolution mechanism |
|---|---|
| External user (guest, customer, partner) | Selects a **Chat Category** in the chat window → category resolves the profile |
| Internal / desk user | Admin directly assigns a profile via **Nexus User Profile Assignment** |

Both paths converge at the same profile chain. There is no difference in access enforcement once the profile is resolved.

### Decision 4 — No query proceeds without a resolved profile

If no profile can be resolved for a given request, the system rejects the request cleanly. There is no silent default, no fallthrough to public. A missing profile record is a governance gap that must be fixed by the admin, not papered over at runtime.

### Decision 5 — Chat Category is the identity declaration point for external users

The user declares their **intent** by selecting a chat category (Customer Support, Product Enquiry, Connect to Sales). Runtime derives or accepts the user's `identity_type`, then resolves a `Nexus Category Identity Route` to find the linked profile. This works for both authenticated and unauthenticated external users.

### Decision 6 — Roles inform profile assignment, not access enforcement

For internal users, Frappe roles can be used by the admin as a guide when assigning profiles in bulk. At runtime, roles play no part in access resolution — the directly assigned profile is always used.

---

## 3. New DocTypes Required

### 3.1 `Nexus Chat Category`

**Purpose:** Pre-defined options displayed in the chat window. A category declares intent. The Agent Profile is resolved through `Nexus Category Identity Route`.

**Module:** `nexus_live_channels`
**App:** `digitz_ai_nexus_live`

| Field | Type | Notes |
|---|---|---|
| category_code | Data (unique) | Primary key |
| category_label | Data | What the user sees in the chat window (e.g. "Customer Support") |
| channel | Link → Nexus Live Channel | Which channel this category appears on |
| requires_authentication | Check | Whether guests may use this category |
| display_order | Int | Sort order in the chat window |
| enabled | Check | Controls visibility in chat window |
| description | Small Text | Admin notes |

**Runtime behaviour:**
- Chat window loads all enabled `Nexus Chat Category` records for its channel, sorted by `display_order`
- User selects a category
- Runtime resolves `identity_type`
- `Nexus Category Identity Route` resolves `channel + chat_category + identity_type` to `ai_agent_profile`
- The resolved profile is snapshotted and used for the conversation
- Profile → Access Category → Policies → Knowledge

**Admin requirement:** Every selectable category must have at least one enabled route for every identity type it will serve. A category with no matching route cannot start a conversation for that identity.

---

### 3.2 `Nexus User Profile Assignment`

**Purpose:** Direct assignment of an Agent Profile to a specific internal/desk user. The sole profile resolution mechanism for internal users.

**Module:** `nexus_live_agents`
**App:** `digitz_ai_nexus_live`

| Field | Type | Notes |
|---|---|---|
| user | Link → User | The Frappe/desk user (unique — one active assignment per user) |
| ai_agent_profile | Link → Nexus AI Agent Profile | The assigned profile |
| assigned_by | Link → User | Admin who made the assignment |
| assigned_on | Datetime | |
| active | Check | Only one active record per user is used at runtime |
| notes | Small Text | Admin notes on the assignment |

**Runtime behaviour:**
- When an internal desk user raises a query, `resolve_profile_for_user(user)` loads this record
- If no active assignment exists → request rejected with clear message
- Profile → Access Category → Policies → Knowledge

**Admin requirement:** Every internal user who will use the system must have an active profile assignment. Admin-managed, not self-service.

---

## 4. Modified DocTypes

### 4.1 `Nexus Channel AI Profile Route`

**Current field:** `auth_scope` — Select (Public / Authenticated / Any)
**Change:** Replace with `identity_type` — Link to `Nexus Identity Type`

**New role of this DocType:** Fallback routing for non-chat channels (API, direct integrations) where no chat window exists. For chat channels, `Nexus Chat Category` is the primary resolution mechanism.

| Field | Change |
|---|---|
| `auth_scope` | Rename to `identity_type`, expand options |
| `use_case` | Retained — can still narrow routing by use case |
| `context`, `sub_context`, `intent` | Retained |
| `priority`, `is_default` | Retained |

---

### 4.2 `Nexus Live Agent`

**Already changed (previous session):**
- `behaviour` field: removed `mandatory_depends_on`. Now optional legacy template field only.
- Description updated to clarify it is not the primary runtime source.

---

### 4.3 `Nexus Live Conversation`

**Already changed (previous session):**
- `assigned_ai_agent_profile` (Link → Nexus AI Agent Profile) — added
- `ai_profile_snapshot_json` (Code/JSON) — added

Snapshot is written at conversation creation time and preserves the resolved profile behaviour for the life of the conversation. Profile changes after conversation start do not affect in-progress conversations.

---

### 4.4 `Nexus AI Behaviour`

**Already changed (previous session):**
- `tone` converted from `Select` to `Data`
- `response_style` converted from `Select` to `Data`

**Demoted status:** `Nexus AI Behaviour` is now an optional reusable behaviour template only. It is not the primary runtime object. `Nexus AI Agent Profile` is the primary runtime behaviour and access configuration.

---

## 5. Retired from Runtime Enforcement

These DocTypes are **kept** (no deletion) but are no longer called during runtime access resolution.

| DocType | Previous Role | New Status |
|---|---|---|
| `Nexus Channel Access Category` | Runtime channel policy ceiling | Retained as DocType, removed from `access_resolver.py` runtime path |
| `Nexus Role Access Category` | Runtime role policy enforcement | Retained as DocType, removed from `access_resolver.py` runtime path |

**Migration note:** Existing records in these DocTypes are preserved. If a future use case requires them (e.g. admin UI policy reporting), they can be re-read without modifying the runtime path.

---

## 6. Code Changes

### 6.1 `engine/access_resolver.py` — Simplify to profile-only

**Current:** Three-way intersection (channel ∩ role ∩ profile)
**New:** Profile scope only

```python
def resolve_allowed_policies(query_contract):

    force_public_only = bool(
        query_contract.get("force_public_only") or query_contract.get("is_public")
    )

    if force_public_only:
        return {
            "allowed_access_policies": ["Public"],
            "force_public_only": True,
        }

    ai_profile_name = (query_contract.get("ai_profile") or {}).get("name")
    if not ai_profile_name:
        return {"allowed_access_policies": []}

    profile_policies = resolve_profile_policy_names(ai_profile_name)

    return {
        "allowed_access_policies": list(profile_policies),
        "force_public_only": False,
        "profile_policy_names": list(profile_policies),
    }
```

`resolve_channel_policy_names()` and `resolve_role_policy_names()` are retained as functions (for potential future admin reporting) but are no longer called in `resolve_allowed_policies()`.

---

### 6.2 New — `services/identity_resolver.py` (digitz_ai_nexus_live)

**Purpose:** Resolves the identity type of an external user from request signals.

```python
def resolve_identity_type(payload):
    """
    Derive identity type from request auth signals.

    Returns one of: Public, Customer, Prospect, Partner, Internal, Admin
    """
    user = payload.get("user") or {}
    user_type = payload.get("user_type") or "Guest"

    if user_type == "Guest" or not user:
        return "Public"

    if user_type == "Website User":
        return "Customer"

    if user_type == "Desk User":
        roles = set(user.get("roles") or [])
        if "System Manager" in roles:
            return "Admin"
        return "Internal"

    api_scope = payload.get("api_scope")
    if api_scope == "partner":
        return "Partner"

    return "Public"
```

---

### 6.3 New — `services/profile_resolver.py` (digitz_ai_nexus_live)

**Purpose:** Unified profile resolution — chat category for external users, direct assignment for internal users.

```python
def resolve_profile_from_chat_category(category_code):
    """Resolve ai_agent_profile from a selected chat category."""
    if not category_code:
        frappe.throw("Chat category is required.")

    category = frappe.get_doc("Nexus Chat Category", category_code)

    if not category.enabled:
        frappe.throw("Selected chat category is not active.")

    if not category.ai_agent_profile:
        frappe.throw(f"Chat category '{category_code}' has no profile configured.")

    return frappe.get_doc("Nexus AI Agent Profile", category.ai_agent_profile)


def resolve_profile_for_user(user):
    """Resolve ai_agent_profile for an internal desk user via direct assignment."""
    if not user:
        frappe.throw("User is required.")

    assignment_name = frappe.db.get_value(
        "Nexus User Profile Assignment",
        {"user": user, "active": 1},
        "name",
    )

    if not assignment_name:
        frappe.throw(f"No active profile assignment found for user '{user}'.")

    assignment = frappe.get_doc("Nexus User Profile Assignment", assignment_name)
    return frappe.get_doc("Nexus AI Agent Profile", assignment.ai_agent_profile)


def resolve_profile_for_external(channel, identity_type):
    """
    Fallback profile resolution for non-chat channels (API, direct integration).
    Uses Nexus Channel AI Profile Route with identity_type.
    """
    route = frappe.db.get_value(
        "Nexus Channel AI Profile Route",
        {
            "channel": channel,
            "identity_type": identity_type,
            "enabled": 1,
        },
        "ai_agent_profile",
        order_by="priority asc",
    )

    if not route:
        route = frappe.db.get_value(
            "Nexus Channel AI Profile Route",
            {"channel": channel, "is_default": 1, "enabled": 1},
            "ai_agent_profile",
        )

    if not route:
        frappe.throw(
            f"No profile route configured for channel '{channel}' "
            f"with identity type '{identity_type}'."
        )

    return frappe.get_doc("Nexus AI Agent Profile", route)
```

---

### 6.4 `services/live_chat_service.py` — Use chat category for profile resolution

**Current:** Calls `get_agent_behavior(agent)` then builds `ai_profile` from behavior object.
**New:** Accepts `chat_category` in payload. Loads profile via `resolve_profile_from_chat_category()`. Behavior fields come directly from the profile.

Key change to `start_live_chat()` and `build_core_chat_payload()`:

```python
# Resolve profile from chat category
category_code = payload.get("chat_category")
if category_code:
    profile = resolve_profile_from_chat_category(category_code)
else:
    # Internal user or API — use existing resolution
    profile = resolve_profile_for_user(payload.get("user", {}).get("user_id"))

ai_profile = build_ai_profile_dict(profile)
```

---

### 6.5 `services/live_qa_service.py` — Same pattern

Accepts `chat_category` in payload. Resolves profile from category or user assignment.

---

### 6.6 `services/agent_service.py`

**Already changed (previous session):** `get_agent_behavior()` now uses `Nexus AI Agent Profile` as primary source. `Nexus AI Behaviour` is a field-level fallback template only.

---

## 7. New Service: `services/profile_builder.py` (digitz_ai_nexus_live)

Utility to build the standardised `ai_profile` dict from a `Nexus AI Agent Profile` document. Both `live_chat_service` and `live_qa_service` call this.

```python
def build_ai_profile_dict(profile, default_response_mode="chat"):
    if not profile:
        return {}
    return {
        "name": profile.name,
        "agent": profile.agent,
        "behavior_prompt": profile.behavior_prompt,
        "tone": profile.tone,
        "response_style": profile.response_style,
        "welcome_message": profile.welcome_message,
        "fallback_message": profile.fallback_message,
        "do_not_answer_rules": profile.do_not_answer_rules,
        "confidence_threshold": profile.confidence_threshold,
        "escalation_enabled": profile.escalation_enabled,
        "escalation_policy": profile.escalation_policy,
        "memory_mode": profile.memory_mode,
        "default_response_mode": default_response_mode,
    }
```

---

## 8. Implementation Phases

### Phase 1 — Access resolver simplification ✅
- [x] `agent_service.py` — profile-first priority in `get_agent_behavior()`
- [x] `live_chat_service.py` — `ai_profile` dict from profile
- [x] `live_qa_service.py` — chat_category + identity resolution wired
- [x] `access_resolver.py` — profile-only scope; channel and role functions retained but not called in runtime path

### Phase 2 — Nexus Chat Category DocType ✅
- [x] Create `Nexus Chat Category` DocType JSON
- [x] Create `nexus_chat_category.py` controller (warns when no enabled identity routes exist)
- [x] Add to `Nexus Live Channels` module

### Phase 3 — Nexus User Profile Assignment DocType ✅
- [x] Create `Nexus User Profile Assignment` DocType JSON
- [x] Create `nexus_user_profile_assignment.py` controller
- [x] Validation: enforce one active assignment per user

### Phase 4 — Identity and Profile Resolver Services
- [x] Create `services/identity_resolver.py`
- [x] Create `services/profile_resolver.py`
- [ ] Create shared `services/profile_builder.py` or consolidate current local builders

### Phase 5 — Update `Nexus Channel AI Profile Route` ✅
- [x] Replace `auth_scope` field with `identity_type` (Public/Customer/Prospect/Partner/Internal/Admin)
- [x] Update DocType JSON
- [ ] Write migration patch for existing records (auth_scope → identity_type mapping)

### Phase 6 — Wire live services to new resolution ⚠️
- [x] `live_chat_service.py` — chat_category + identity_type drives profile resolution
- [x] `live_qa_service.py` — chat_category + identity_type drives profile resolution
- [x] `live.py` — `get_channel_categories` filters by identity and route existence
- [ ] Ensure Live builds `ai_profile` before calling `resolve_allowed_policies()`
- [ ] Ensure `resolve_allowed_policies()` receives `query_contract.ai_profile.name`

### Phase 7 — Channel sync (deferred)
- [ ] `Nexus Live Channel` controller: auto-create/sync `Nexus Channel` record on save
- [ ] Ensures access governance identity is always consistent with operational channel

### Phase 8 — Documentation and cleanup ✅ (partially)
- [x] `agent-management.md` — updated
- [x] `doctypes.md` (live) — updated (Chat Category, User Profile Assignment, Conversation snapshot fields, AI Agent Profile Access Category)
- [x] `architecture.md` (live) — updated (module layout includes new pages and APIs)
- [x] `access-governance.md` (core) — rewritten for profile-only model
- [x] `architecture.md` (core) — updated
- [x] `configuration.md` — rewritten with new setup flow and admin pages table
- [ ] `knowledge_access_rules.md` — update to reflect new model
- [ ] `ai_nexus_architecture_context.md` — update

---

## 9. Admin Configuration Checklist

Before a channel goes live, admin must ensure:

**For external (chat window) channels:**
```
[ ] At least one Nexus Chat Category configured per channel
[ ] Each category has an enabled Nexus Category Identity Route for every served identity_type
[ ] Each route points to a valid Nexus AI Agent Profile
[ ] That profile has at least one Nexus AI Agent Profile Access Category record
[ ] The Access Category contains at least one Access Policy
[ ] Knowledge chunks exist with matching access_policy values
```

**For internal/desk users:**
```
[ ] Every user who will query the system has an active Nexus User Profile Assignment
[ ] Assigned profile has Access Category configured
```

**For API / non-chat channels:**
```
[ ] Nexus Channel AI Profile Route records exist for each identity_type that will call this channel
```

---

## 10. Test Checklist

```
[ ] External guest selects chat category → correct profile resolved → correct policies applied
[ ] External customer selects chat category → customer profile resolved → broader policies than guest
[ ] Core payload contains ai_profile.name before allowed_access_policies is resolved
[ ] Internal desk user raises query → profile resolved from direct assignment
[ ] Internal desk user with no assignment → hard reject with clear error
[ ] Chat category with no identity route configured → hard reject
[ ] Channel with no chat categories → chat window does not start
[ ] access_resolver.py → only profile scope used → channel/role resolution not called
[ ] Profile with no Access Category → allowed_policies = [] → retrieval denied
[ ] Profile snapshot written to Nexus Live Conversation at creation
[ ] Changing profile config after conversation starts → does not affect in-progress conversation (snapshot used)
[ ] Nexus AI Behaviour still works as field-level fallback template when profile fields are empty
```

---

## 11. What Stays Unchanged

- `Nexus Access Policy` — atomic classification label on chunks. Unchanged.
- `Nexus Access Category` — reusable policy bundle. Unchanged.
- `Nexus Access Category Policy` — child table row. Unchanged.
- `Nexus AI Agent Profile Access Category` — the sole runtime access mapping. Unchanged.
- Retrieval filter: `chunk.access_policy IN allowed_policies`. Unchanged.
- Fail-closed rule: empty `allowed_access_policies` → retrieval denied. Unchanged.
- `force_public_only` override — Public-only for unauthenticated requests. Unchanged.
- `prompt.py` — already prioritises `query_contract["ai_profile"]`. Unchanged.
- Multi-tenancy model. Unchanged.
- Escalation service. Unchanged.

---

## 12. Key Invariants

These must always hold after the redesign:

1. Every resolved profile has at least one Access Category configured, or retrieval is denied.
2. Every conversation document stores a profile snapshot at creation time.
3. No runtime code calls `resolve_channel_policy_names()` or `resolve_role_policy_names()` for access enforcement.
4. The `ai_profile` dict in every query contract is built from `Nexus AI Agent Profile` fields, not from `Nexus AI Behaviour` fields directly.
5. `Nexus AI Behaviour` is never the primary runtime selector — it is a template only.
