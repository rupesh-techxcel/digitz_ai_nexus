# Access Governance

This document describes how the system decides which knowledge a user or channel may retrieve. Understanding this model is essential before modifying any DocType or service that touches access.

---

## Core Principle

Access is **classification-based**, not audience-based. An access policy is a label applied to knowledge, not a list of users who can see it.

**Wrong mental model:**

> "Finance policy means only the Finance department can see this."

**Correct mental model:**

> "Finance policy means this knowledge is classified as Finance. Any role or profile whose access categories include the Finance policy may retrieve it."

---

## The Four-Layer Model

```
Knowledge Chunk
    └── access_policy (e.g. "Finance")

Nexus Access Policy
    = classification label ("Finance")

Nexus Access Category
    = reusable group of policies
      (e.g. "Finance Access" includes: Public, Internal, Finance)

Nexus Role Access Category       → maps Frappe Role → Access Category
Nexus Channel Access Category    → maps Channel → Access Category
Nexus AI Agent Profile Access Category → maps AI Profile → Access Category
```

---

## DocTypes

### Nexus Access Policy

The atomic classification label. Applied to knowledge sources, units, and chunks.

| Field | Notes |
|---|---|
| policy_name | Primary key and enforcement identifier |
| is_primitive | Only `Public` is primitive (system-defined); all others are user-defined |
| disabled | Excluded from all access calculations when disabled |
| access_level, sensitivity | Optional metadata only — never used for enforcement |
| description | Human notes |

**Default policies created on install:**

| policy_name | Intended Use |
|---|---|
| PUBLIC | Website Q&A, public-facing content |
| CUSTOMER_RESTRICTED | Customer-only knowledge |
| INTERNAL_EMPLOYEE | General internal/employee content |
| ROLE_RESTRICTED | Knowledge requiring specific role grants |
| FINANCE_RESTRICTED | Finance and accounting knowledge |
| HR_CONFIDENTIAL | HR and payroll knowledge |
| ADMIN_ONLY | System administrator knowledge |

### Nexus Access Category

A named group of access policies. This is what roles and channels point to.

| Field | Notes |
|---|---|
| category_name | Primary key |
| allowed_policies | Child table of `Nexus Access Category Policy` rows |
| priority | Used for ordering when multiple categories match |
| disabled | Excluded from access calculations when disabled |

Example:

```
category_name: Finance Access
allowed_policies:
    - Public
    - Internal
    - Finance Restricted
```

### Nexus Access Category Policy

Child table row inside `Nexus Access Category`. Maps one category to one policy.

| Field | Notes |
|---|---|
| access_policy | Link to Nexus Access Policy |

### Nexus Role Access Category

Maps a Frappe system role to an access category. This is how user roles gain knowledge access.

| Field | Notes |
|---|---|
| role | Link to Frappe Role |
| access_category | Link to Nexus Access Category |
| disabled | Excludes this mapping from resolution |
| tenant, business_unit, project | Optional scope narrowing |

Example:

```
role: Accounts User
access_category: Finance Access
```

→ Accounts Users can retrieve Finance-classified knowledge (because "Finance Access" includes the Finance policy).

### Nexus Channel Access Category

Maps a channel (service lane) to an access category. This acts as a guardrail: even if a user's roles grant broad access, the channel limits what the AI can expose through that entry point.

| Field | Notes |
|---|---|
| channel | Link to Nexus Channel |
| access_category | Link to Nexus Access Category |
| disabled | Excludes from resolution |
| tenant, business_unit, project | Optional scope narrowing |

Example:

```
channel: Website
access_category: Public Website Category  (contains only "Public")
```

→ No matter what roles a user has, queries through the Website channel can only retrieve Public chunks.

### Nexus Channel

A service lane. Kept broad and minimal by design.

| Field | Notes |
|---|---|
| channel_name | Primary key |
| channel_type | Q&A / Chat / Internal / Simulation / API |
| disabled | Excluded from routing |

A channel must not hold a direct link to an access policy or a single AI profile. It participates in routing and guardrail resolution only.

---

## Access Resolution

`engine/access_resolver.py` → `resolve_allowed_policies(query_contract)`

### Public Endpoints

If `force_public_only = True` or `is_public = True` in the query contract:

```python
return {
    "allowed_access_policies": ["Public"],
    "force_public_only": True,
    ...
}
```

This overrides all other configuration. No channel, role, or profile setting can expand this beyond `Public`.

### Authenticated Endpoints

The resolver collects policy sets from each configured scope and intersects them:

```python
channel_policies = resolve_channel_policy_names(channel_name)
role_policies    = resolve_role_policy_names(user_roles)
profile_policies = resolve_profile_policy_names(ai_agent_profile_name)

# Only intersect scopes that have explicit configuration.
# An unconfigured scope is treated as "no restriction from this scope".
non_empty_scopes = [s for s in [channel_policies, role_policies, profile_policies] if s]

final = non_empty_scopes[0]
for scope in non_empty_scopes[1:]:
    final = final.intersection(scope)
```

**Important nuance:** An unconfigured scope (e.g. no channel access categories set up yet) does not deny everything — it is simply skipped in the intersection. This allows new deployments to work before all categories are configured.

### Resolution Functions

| Function | Source DocType |
|---|---|
| `resolve_channel_policy_names(channel)` | Nexus Channel Access Category → Nexus Access Category → Nexus Access Category Policy |
| `resolve_role_policy_names(roles)` | Nexus Role Access Category → Nexus Access Category → Nexus Access Category Policy |
| `resolve_profile_policy_names(profile)` | Nexus AI Agent Profile Access Category → Nexus Access Category → Nexus Access Category Policy |

All three ultimately call `_policies_from_categories(category_names)` which fetches from `Nexus Access Category Policy`.

### Fail-Closed Rule

If all scopes are unconfigured and produce empty sets, the intersection returns an empty list. The caller (answer service or retrieval engine) must then deny retrieval:

```python
# answer_service.py
if allowed_policies is not None and len(allowed_policies) == 0:
    frappe.throw("Access policy resolution failed. Retrieval cannot proceed.")

# retrieval.py
if allowed_policies is not None and len(allowed_policies) == 0:
    frappe.throw("Access policy resolution produced no permitted policies. Retrieval denied.")
```

---

## Query Contract Access Fields

The query contract passed to the answer service and retrieval engine must include:

```python
query_contract = {
    "query": "...",
    "channel": "Website",               # Used for channel policy resolution
    "is_public": True,                  # Forces Public-only if True
    "force_public_only": True,          # Explicit public override

    "user": {
        "user_id": "user@example.com",
        "roles": ["Accounts User", "Employee"],
    },

    "ai_profile": {
        "name": "Website Support Profile",
        ...
    },

    # Pre-resolved (set by access_resolver.resolve_allowed_policies):
    "allowed_access_policies": ["Public", "Internal", "Finance Restricted"],
}
```

The retrieval engine applies this as a database filter:

```python
filters["access_policy"] = ["in", allowed_access_policies]
```

---

## Restricted Response vs No Context

These two cases must never be merged:

| Situation | `access_status` | Answer |
|---|---|---|
| Relevant chunks found but user cannot access them | `restricted` | "You do not have permission to access this information." |
| No relevant chunks found (or confidence too low) | `no_context` | "I do not have enough approved knowledge to answer this." |
| Answer successfully generated | `allowed` | Grounded answer with sources |

The retrieval engine determines "restricted" when the highest-scoring denied chunk scores higher than the best allowed chunk. This ensures that "I don't know" is not returned when the system actually has the answer but is protecting it.

---

## Access vs Business Context

These are different things. Do not confuse them.

| Purpose | Fields |
|---|---|
| **Access control** (who can see it) | `access_policy` on chunks and sources |
| **Business relevance** (what is it about) | `business_unit`, `project`, `context`, `sub_context`, `entity_type`, `entity`, `topic` |

Business context fields help with retrieval relevance (filtering and scoring) but never substitute for access policy. A chunk scoped to `project = "Alpha"` is still retrieved only if its `access_policy` is in the allowed set.

---

## Admin UI: Role Allocation Page

`nexus_access/page/nexus_access_role_allocation/`

This page allows administrators to:

- Select a Frappe role
- View its currently assigned access categories
- Assign or unassign access categories
- Preview the effective access policies resulting from the assignment
- View access category details

This UI writes to `Nexus Role Access Category`. It does not modify `Nexus Access Policy` directly.
