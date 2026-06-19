# Access Governance

This document describes how the system decides which knowledge a person or channel may retrieve.

---

## Core Principle

Access is **identity-driven**. Knowledge access is configured on the person, not on the AI agent.
The AI Agent Profile controls how the AI responds (behavior); the Identity Profile controls
what the person can retrieve (knowledge).

```
Person → Identity Registry → Identity Profile → Knowledge Profile → Access Category → [Policies] → chunk filter
```

---

## The Access Chain

```
Nexus Identity Registry  (person)
    ↓  identity_profiles (assigned Identity Profiles)
Nexus Identity Profile
    ↓  identity_mappings  (per identity type)
Knowledge Profile         (reusable bundle of access categories)
    ↓  access_categories  (child table)
Nexus Access Category     (named group of policies)
    ↓  allowed_policies   (child table)
[Nexus Access Policy, Nexus Access Policy, ...]
    ↓
chunk.access_policy IN [policy_names]  →  allowed chunks returned
```

**The AI Agent Profile is not in this chain.** It owns behavior (tone, fallback, escalation
settings, confidence thresholds) — not access.

---

## DocTypes — Knowledge Layer

### Nexus Access Policy

The atomic classification label. Stamped on every knowledge chunk (`access_policy` field, Link,
required). One policy per chunk.

| Field | Notes |
|---|---|
| `name` | Primary key and enforcement identifier |
| `is_primitive` | Only `Public` is primitive; all others are user-defined |
| `disabled` | Excluded from all access calculations when disabled |
| `access_level`, `sensitivity` | Optional metadata — not used for enforcement |

**Starter policies:**

| Policy | Intended Use |
|---|---|
| `Public` | Public-facing content (the primitive system policy) |
| `Internal` | General internal / employee content |
| `Restricted` | Restricted knowledge requiring explicit access grants |

---

### Nexus Access Category

A named bundle of access policies. Knowledge Profiles point to these.

| Field | Notes |
|---|---|
| `category_name` | Primary key |
| `allowed_policies` | Child table of `Nexus Access Category Policy` rows |
| `priority` | Display ordering |
| `disabled` | Excluded when disabled |

---

### Nexus Access Category Policy

Child table row inside `Nexus Access Category`. Maps one policy into one category.

---

### Knowledge Profile

A reusable bundle of `Nexus Access Category` records. Assigned to Identity Profiles through
identity type mappings.

| Field | Notes |
|---|---|
| `name` | Primary key |
| `title` | Display label |
| `enabled` | Disabled profiles are excluded from access resolution |
| `access_categories` | Child table of `Knowledge Profile Access Category` rows |

---

## DocTypes — Identity Layer

### Nexus Identity Type

Represents the class of identity (Public, Customer, Partner, Internal, Admin, etc.).

| Field | Notes |
|---|---|
| `title` | Identity class name (also the Link value) |
| `enabled` | Disabled types are excluded from routing |
| `sort_order` | Display ordering |
| `safeguard_access_categories` | Child table → hard cap for all holders of this type |

The **safeguard** is a class-level ceiling applied uniformly to every person who resolves
as that identity type. It cannot be overridden per person. This is intentional — it prevents
any misconfiguration at the person level from exceeding the class-level boundary.

---

### Nexus Identity Profile

A reusable bundle that maps identity types to Knowledge Profiles. One profile can be assigned
to many people in the Identity Registry.

| Field | Notes |
|---|---|
| `profile_name` | Primary key |
| `title` | Display label |
| `enabled` | Excluded from resolution when disabled |
| `identity_mappings` | Child table — one row per `(identity_type, knowledge_profile)` pair |

A single Identity Profile can carry multiple rows. This allows one profile to represent a person
who may be verified as both Customer and Partner — different rows for different identity types.

---

### Nexus Identity Registry

The individual person record. Every visitor, desk user, or human agent that needs knowledge
access must have an entry here.

| Field | Notes |
|---|---|
| `email` | Primary identifier (unique) |
| `full_name` | Display name |
| `user` | Optional: Frappe desk/portal user; used to find the registry from a Frappe session |
| `enabled` | Disabled registries are ignored |
| `verification_status` | Unverified / Verified / Blocked |
| `identity_profiles` | Child table of assigned `Nexus Identity Profile` records |
| `reference_doctype` / `reference_name` | Optional link to a CRM or ERP record |

**Desk users** — found by matching `registry.user = frappe.session.user`. No OTP required.

**Registered visitors** — found by email after OTP verification.

**Public visitors** — no registry. The Public bypass path applies (see Section below).

---

## Profile Resolution — How Profiles Are Selected

### Visitor Chat (Chat Category + Route)

The visitor selects a `Nexus Chat Category`. Runtime resolves a `Nexus Category Identity Route`.

```
Route lookup
    ↓
open_to_all? (derived: not bool(identity_profiles))
    YES → force_public_only: knowledge_profile_names = []
              → allowed_access_policies = ["Public"]

    NO  → find visitor's Identity Registry
              → get active identity profiles
              → intersect with route's permitted identity_profiles
              → collect knowledge_profile for matching identity_type rows
              → union → knowledge_profile_names
```

Note: `open_to_all` is derived at runtime from whether `identity_profiles` is empty.
There is no stored `is_public_route` field on `Nexus Category Identity Route`.

The route's `ai_agent_profile` provides behavior (prompts, tone, escalation). It has no
bearing on what knowledge the person may access.

### Desk Users

```
frappe.session.user
    ↓
Nexus Identity Registry (registry.user = session_user)
    ↓
Active identity profiles on the registry
    ↓
Identity Profile mappings where identity_type = "Internal" | "Admin"
    ↓
knowledge_profile_names
```

If no registry entry exists, internal users without a registry entry are denied access
(unless they are `System Manager` — see below).

### System Manager Sessions

Authenticated desk users with the Frappe role `System Manager` bypass all profile/category
policy narrowing. `resolve_allowed_policies()` returns all enabled access policies.

This is evaluated **after** `force_public_only`, so public routes cannot be widened by an
admin session.

---

## Runtime Query Contract

Any Live or external caller that expects identity-based knowledge access must build the core
query contract in this order:

```
resolve chat category + identity_type
    → resolve route → behavior (ai_agent_profile) + knowledge_profile_names
    → build query_contract.ai_profile including knowledge_profile_names
    → call resolve_allowed_policies(query_contract)
    → set query_contract.allowed_access_policies
    → call retrieval / answer service
```

If `resolve_allowed_policies()` receives an `ai_profile` with no `knowledge_profile_names`,
it returns `[]`. Retrieval fails closed.

---

## Access Resolution

`engine/access_resolver.py` → `resolve_allowed_policies(query_contract)`

### Public requests

If `force_public_only = True` or `is_public = True`:

```python
return {"allowed_access_policies": ["Public"], "force_public_only": True}
```

Cannot be bypassed.

### Registered / profiled requests

```python
profile_policies = resolve_knowledge_profiles_policy_names(knowledge_profile_names)
# profile_policies = union of policies from all knowledge profiles

safe_guard       = resolve_access_categories_policy_names(identity_safeguard_access_categories)
# identity_safeguard_access_categories comes from Nexus Identity Type (class-level cap)

identity_cap     = resolve_identity_policy_cap(identity_type)  # {"Public"} or None
effective_cap    = _intersect_caps(safe_guard, identity_cap)
allowed_policies = profile_policies.intersection(effective_cap) if effective_cap else profile_policies
```

`resolve_knowledge_profiles_policy_names(names)` unions policies across all listed Knowledge Profiles:

```
Knowledge Profile names
    → for each: Knowledge Profile Access Category (enabled child rows) → access_category names
    → Nexus Access Category Policy (child rows of those categories) → access_policy names
    → union all → return as set
```

The safeguard and identity cap are intersected together before being applied to profile policies.
Either may be `None` (no restriction from that layer).

### System Manager requests

```python
if is_system_manager_session_user():
    allowed_policies = resolve_all_policy_names()
```

Evaluated after `force_public_only` — public routes cannot be widened.

---

## Fail-Closed Rule

| Situation | Result |
|---|---|
| `knowledge_profile_names` is empty, no profile name | `allowed_policies = []` → retrieval denied |
| Knowledge Profiles have no enabled Access Categories | `allowed_policies = []` → retrieval denied |
| Safeguard intersection produces empty set | `allowed_policies = []` → retrieval denied |
| `force_public_only = True` | Only `["Public"]` — no exceptions |
| No registry entry for registered user (non-SM) | Route matching returns no knowledge profiles → denied |
| Registry is Blocked | Throws before reaching access resolution |

---

## Access vs Business Context

| Purpose | Fields |
|---|---|
| **Access control** (who can see it) | `access_policy` on chunks |
| **Business relevance** (what is it about) | `business_unit`, `project`, `context`, `entity_type`, `topic` |

Business context fields drive retrieval relevance. They never substitute for access policy.
A chunk scoped to `project = "Alpha"` is only retrieved if its `access_policy` is in the
allowed set.

---

## Admin Configuration Checklist

For every registered identity type that will serve knowledge:

```
[ ] Nexus Identity Type record exists and is enabled
[ ] safeguard_access_categories configured (leave empty only if no cap is intended)
[ ] Nexus Identity Profile records created for each access pattern
[ ] Identity Profile has identity_mappings rows linking identity_type → Knowledge Profile
[ ] Knowledge Profile has at least one enabled Access Category
[ ] Access Category has at least one Access Policy in its allowed_policies child table
[ ] Knowledge chunks exist with access_policy values matching those policies
```

For every category route serving registered visitors:

```
[ ] Nexus Category Identity Route: permitted identity_profiles child table populated
[ ] All listed Identity Profiles are enabled and have valid identity_mappings
```

For every internal desk user needing knowledge access:

```
[ ] Nexus Identity Registry entry exists with registry.user = frappe_username
[ ] Registry verification_status = Verified
[ ] Identity Profiles assigned with rows for "Internal" or "Admin" identity type
```
