# Access Governance

This document describes how the system decides which knowledge a user or channel may retrieve.

---

## Core Principle

Access is **profile-driven**. Every query resolves to exactly one `Nexus AI Agent Profile`. That profile is the single access authority — it determines what knowledge the AI may retrieve and deliver, regardless of whether the requester is a website guest, a customer, a partner, or an internal employee.

```
Any request  →  Agent Profile  →  Access Category  →  [Policies]  →  chunk filter
```

---

## The Invariant Chain

```
Nexus AI Agent Profile
    ↓  (via Nexus AI Agent Profile Access Category)
Nexus Access Category
    = named bundle of permitted policies
    ↓  (child table: Nexus Access Category Policy)
[Nexus Access Policy, Nexus Access Policy, ...]
    ↓
chunk.access_policy IN [policy_names]  →  allowed chunks returned
```

**Nothing else participates in runtime access resolution.** Channel membership and Frappe roles do not produce access policies at runtime. They are inputs to profile selection only.

---

## DocTypes

### Nexus Access Policy

The atomic classification label. Stamped on every knowledge chunk (`access_policy` field, Link, required). One policy per chunk.

| Field | Notes |
|---|---|
| policy_name | Primary key and enforcement identifier |
| is_primitive | Only `Public` is primitive; all others are user-defined |
| disabled | Excluded from all access calculations when disabled |
| access_level, sensitivity | Optional metadata — never used for enforcement |

**Default policies:**

| policy_name | Intended Use |
|---|---|
| PUBLIC | Public-facing content, website Q&A |
| CUSTOMER_RESTRICTED | Customer-only knowledge |
| INTERNAL_EMPLOYEE | General internal / employee content |
| ROLE_RESTRICTED | Knowledge requiring specific access grants |
| FINANCE_RESTRICTED | Finance and accounting knowledge |
| HR_CONFIDENTIAL | HR and payroll knowledge |
| ADMIN_ONLY | System administrator knowledge |

---

### Nexus Access Category

A named bundle of access policies. This is what profiles point to.

| Field | Notes |
|---|---|
| category_name | Primary key |
| allowed_policies | Child table of `Nexus Access Category Policy` rows |
| priority | Ordering when multiple categories are displayed |
| disabled | Excluded when disabled |

Example:

```
category_name: Finance Access
allowed_policies:
    - Public
    - Internal Employee
    - Finance Restricted
```

A profile assigned this category may retrieve chunks classified as any of these three policies.

---

### Nexus Access Category Policy

Child table row inside `Nexus Access Category`. Maps one category to one policy.

| Field | Notes |
|---|---|
| access_policy | Link to Nexus Access Policy |

---

### Nexus AI Agent Profile Access Category

Maps a `Nexus AI Agent Profile` to a `Nexus Access Category`. This is the sole runtime access mapping.

| Field | Notes |
|---|---|
| ai_agent_profile | Link to Nexus AI Agent Profile |
| access_category | Link to Nexus Access Category |
| enabled | Excludes from resolution when disabled |
| priority | Ordering |

One profile may be assigned multiple categories. The resolved policy set is the **union** of all enabled categories assigned to the profile.

---

## Profile Resolution — How the Profile Is Selected

The profile must be resolved before access can be checked. Three paths exist:

### External users — Chat Category + Identity Route

The user selects a `Nexus Chat Category` in the chat window. Runtime derives an `identity_type` from the request/session, then resolves a `Nexus Category Identity Route`.

```
User selects "Customer Support"
    ↓
Resolve identity_type:
    Public | Customer | Prospect | Partner | Internal | Admin
    ↓
Nexus Category Identity Route:
    channel = Website Chat
    chat_category = Customer Support
    identity_type = Customer
    ai_agent_profile = "Customer Support Bot"
    ↓
Profile loaded → access resolution proceeds
```

The category does not own access directly. The resolved profile owns access through `Nexus AI Agent Profile Access Category`.

### Internal / desk users — Direct assignment

An admin assigns a profile via `Nexus User Profile Assignment`. The system loads the active assignment for the authenticated user.

```
Desk user raises query
    ↓
Nexus User Profile Assignment: user = rupesh@company.com
    ai_agent_profile = "Finance Internal Bot"
    ↓
Profile loaded → access resolution proceeds
```

### API / non-chat channels

Direct integrations should use an explicit agent/profile context or the channel's configured agent path. The active runtime model does not use a separate channel-level profile route.

---

## Runtime Query Contract Requirement

Any Live or external caller that expects profile-based knowledge access must build the core query contract in this order:

```
resolve chat category + identity_type
    → resolve Nexus AI Agent Profile
    → build query_contract.ai_profile.name
    → call resolve_allowed_policies(query_contract)
    → set query_contract.allowed_access_policies
    → call retrieval / answer service
```

If `resolve_allowed_policies()` is called before `query_contract.ai_profile.name` exists, it returns an empty policy list for profiled requests. Retrieval then fails closed.

---

## Access Resolution

`engine/access_resolver.py` → `resolve_allowed_policies(query_contract)`

### Public requests

If `force_public_only = True` or `is_public = True`:

```python
return {"allowed_access_policies": ["Public"], "force_public_only": True}
```

This overrides all profile, category, and policy configuration. Cannot be bypassed.

### Authenticated / profiled requests

```python
ai_profile_name = query_contract["ai_profile"]["name"]
profile_policies = resolve_profile_policy_names(ai_profile_name)
return {"allowed_access_policies": list(profile_policies)}
```

Single scope. No intersection. No channel ceiling. No role ceiling.

`resolve_profile_policy_names(profile_name)` traverses:

```
Nexus AI Agent Profile Access Category (all enabled records for this profile)
    → collect access_category names
    → Nexus Access Category Policy (child rows of those categories)
    → collect access_policy names
    → return as set
```

---

## Retired from Runtime

These DocTypes are retained but no longer called during runtime access resolution:

| DocType | Previous Role | Current Status |
|---|---|---|
| `Nexus Channel Access Category` | Runtime channel policy ceiling | Kept, not called at runtime |
| `Nexus Role Access Category` | Runtime role policy enforcement | Kept, not called at runtime |

Frappe roles may inform which profile an admin assigns to a user. They do not directly produce access policies at query time.

---

## Fail-Closed Rule

| Situation | Result |
|---|---|
| Profile has no Access Category configured | `allowed_policies = []` → retrieval denied |
| No profile resolved for the request | Request rejected before reaching retrieval |
| Profile categories produce empty policy set | Retrieval denied |
| `force_public_only = True` | Only Public chunks, no exceptions |

```python
# retrieval.py
if allowed_policies is not None and len(allowed_policies) == 0:
    frappe.throw("Access policy resolution produced no permitted policies. Retrieval denied.")
```

---

## Restricted vs No Context

These two outcomes must never be merged:

| Situation | `access_status` | Answer |
|---|---|---|
| Chunks exist but profile cannot access them | `restricted` | "You do not have permission to access this information." |
| No relevant chunks found | `no_context` | Profile fallback message |
| Answer successfully generated | `allowed` | Grounded answer with sources |

---

## Access vs Business Context

| Purpose | Fields |
|---|---|
| **Access control** (who can see it) | `access_policy` on chunks |
| **Business relevance** (what is it about) | `business_unit`, `project`, `context`, `sub_context`, `entity_type`, `entity`, `topic` |

Business context fields drive retrieval relevance (filtering and scoring). They never substitute for access policy. A chunk scoped to `project = "Alpha"` is retrieved only if its `access_policy` is in the allowed set.

---

## Admin Configuration Checklist

For every profile that will be used at runtime:

```
[ ] At least one Nexus AI Agent Profile Access Category record with enabled = 1
[ ] The linked Access Category has at least one Access Policy in its child table
[ ] Knowledge chunks exist with access_policy values matching those policies
```

For every channel accepting external users:

```
[ ] Nexus Chat Category records configured per identity type
[ ] Each category has a valid ai_agent_profile assigned
[ ] That profile has Access Category configured
```

For every internal desk user:

```
[ ] Active Nexus User Profile Assignment exists
[ ] Assigned profile has Access Category configured
```
