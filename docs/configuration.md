# Configuration

This document covers all configurable settings, installation defaults, and provider setup.

---

## Nexus Settings

`Nexus Settings` is a Frappe Single DocType — one record for the entire installation. Configure it via the Frappe desk interface.

### LLM Settings

| Setting | Default | Description |
|---|---|---|
| llm_provider | OpenAI | LLM provider type |
| llm_model | `gpt-4o-mini` | Model used for answer generation |
| api_key | *(password)* | OpenAI API key |
| openai_project_id | | Optional OpenAI project ID |

The LLM is called with `temperature = 0.2` for deterministic, factual outputs. The system message is fixed:

```
"You are DIGITZ AI Nexus, a controlled enterprise knowledge assistant."
```

### Embedding Settings

| Setting | Default | Description |
|---|---|---|
| embedding_provider | OpenAI | Embedding provider type |
| embedding_model | `text-embedding-3-small` | Model used for chunk and query embeddings |

Embeddings are stored as JSON arrays in `Nexus Knowledge Chunk.embedding`.

### Chunking Settings

| Setting | Default | Description |
|---|---|---|
| chunk_size | `800` | Maximum characters per chunk |
| chunk_overlap | `120` | Overlap characters between consecutive chunks |

Chunks are split on paragraph boundaries where possible. Overlap maintains context continuity across chunk boundaries.

### Retrieval Settings

| Setting | Default | Description |
|---|---|---|
| top_k | `5` | Number of chunks passed to the LLM prompt |
| retrieval_candidate_limit | `30` | Maximum candidates evaluated before re-ranking |
| rerank_candidate_limit | `20` | Candidates passed into the re-ranker |
| minimum_confidence | `0.20` | Score below which a fallback answer is returned |

`top_k` can be overridden per-request via `query_contract["top_k"]` or per-tenant via tenant configuration.

### Hybrid Scoring Weights

| Setting | Default | Description |
|---|---|---|
| vector_weight | `0.75` | Weight for cosine similarity score |
| keyword_weight | `0.20` | Weight for keyword overlap score |
| business_term_weight | | Boost for matching business keywords |
| project_boost_weight | | Boost for project-scoped chunk match |

These produce the `hybrid_score`. A separate `retrieval_stability_score` uses fixed weights (vector 45%, keyword 25%, priority 10%, project 10%, rerank 10%) for tie-breaking.

### Feature Flags

| Setting | Default | Description |
|---|---|---|
| enable_multi_query | `1` | Expand query into multiple variants before retrieval |
| enable_reranking | `1` | Apply re-ranking pass after initial scoring |
| enable_retrieval_debug | `0` | Include per-candidate debug data in retrieval result |
| strict_mode | | Enable strict tenant/project isolation across all queries |

---

## Default Access Policies

Created automatically during `bench install-app` via `install.py` → `create_default_access_policies()`.

| policy_name | access_level | sensitivity | Purpose |
|---|---|---|---|
| PUBLIC | Public | public | Public-facing endpoints; forced for all public channels |
| CUSTOMER_RESTRICTED | Customer Restricted | customer | Customer-portal knowledge |
| INTERNAL_EMPLOYEE | Internal | internal | General internal/employee content |
| ROLE_RESTRICTED | Role Restricted | operational | Fine-grained role-based access |
| FINANCE_RESTRICTED | Finance Restricted | financial | Finance and accounting content |
| HR_CONFIDENTIAL | HR Confidential | hr | HR and payroll content |
| ADMIN_ONLY | Admin Only | confidential | System administrator content |

These are starting points. All policies except `PUBLIC` can be renamed, disabled, or replaced with user-defined ones. `PUBLIC` is the only primitive policy — it must always exist and must not be disabled.

---

## LLM Provider Registry

`Nexus LLM Provider` allows registering multiple provider configurations. The active provider and model are selected from `Nexus Settings`.

A provider record stores:

- `provider_name` — identifier
- `provider_type` — OpenAI or Other
- `base_url` — for custom or self-hosted endpoints
- `api_key` — per-provider key (overrides global key when used directly)
- `default_llm_model` — default model for this provider
- `default_embedding_model` — default embedding model for this provider

Currently `engine/llm.py` and `engine/embedding.py` read directly from `Nexus Settings`. The provider registry is the extensibility point for future multi-provider support.

---

## Tenant and Ecosystem Configuration

See [Tenant and Tenant Configuration](tenant-ecosystem.md) for the admin model.

### Nexus Tenant

Create one tenant record per customer, division, or isolated deployment:

```
bench frappe make --doctype "Nexus Tenant" --values '{"tenant_name": "Acme Corp", "tenant_code": "ACME"}'
```

Or create from the desk. `tenant_code` is the primary identifier referenced across all DocTypes.

### Business Unit and Public Context Masters

Create `Nexus Business Unit` and `Nexus Public Context` records before assigning tenant defaults or knowledge classification values. These values are Link fields across the platform, so selectors and validation use master records rather than ad hoc text.

### Tenant Configuration

Tenant configuration stores the bare minimum defaults needed for runtime:

- Which channels are used for Q&A and chat
- Default business unit and public context for queries
- Widget display settings (title, welcome message, brand color)
- Feature flags (`qa_enabled`, `live_chat_enabled`, `website_widget_enabled`)

Channel defaults are purpose-aware and do not cross-fallback. Chat runtime uses `default_chat_channel`, and Q&A runtime uses `default_qa_channel` when no explicit channel is passed. Routing still belongs to category, identity, agent profile, access category, and access policy.

Implementation note: older code still stores these values in `Nexus Ecosystem` for compatibility. Treat it as internal tenant-configuration storage until the schema is fully migrated.

---

## Access Category Setup

Before users can retrieve knowledge, access categories must be assigned to the AI Agent Profile that will handle the request. For registered identities, the person-level `Nexus Identity Registry` Safe Guard is also intersected with the routed profile access. The minimum setup for a public Q&A or public chat profile:

1. **Create an Access Category:**
   - `category_name`: Public Website Access
   - `allowed_policies`: PUBLIC

2. **Assign the Access Category to the AI Agent Profile:**
   - `ai_agent_profile`: Website Public Bot
   - `access_category`: Public Website Access
   - `enabled`: 1

For internal authenticated users:

1. **Create an Access Category** and Knowledge Profile containing the relevant policies
2. **Create a Nexus Identity Profile** with an identity_mapping row: `identity_type = "Internal"` → your Knowledge Profile
3. **Create a Nexus Identity Registry** for the desk user with `user = frappe_username` and assign the Identity Profile
4. **Configure the safeguard** on `Nexus Identity Type "Internal"` to cap the maximum permitted categories

For registered chat visitors:

1. **Create a Nexus Identity Registry** entry with the verified email
2. **Assign Identity Profiles** with mappings for the visitor's identity type (e.g. "Customer")
3. **Ensure Nexus Identity Type** has appropriate `safeguard_access_categories` configured

Runtime access resolution is identity-driven. `Nexus Role Access Category` records are retained for admin/reporting compatibility but are not used by the query resolver.

---

## Test Tenant Override

For automated tests, requests with `tenant = "TEST-NEXUS"` receive synthetic query embeddings instead of calling OpenAI. This is controlled in `api/query.py` → `get_query_embedding_override()` and allows the test suite to run without an API key or network access.

---

## Development Commands

After DocType JSON changes:

```bash
bench --site digitz_ai_nexus.site migrate
bench --site digitz_ai_nexus.site clear-cache
```

Useful grep patterns when auditing access behavior:

```bash
grep -R "allowed_access_policies" apps/digitz_ai_nexus
grep -R "resolve_allowed_policies" apps/digitz_ai_nexus
grep -R "force_public_only" apps/digitz_ai_nexus
grep -R "access_policy" apps/digitz_ai_nexus
grep -R "access_level" apps/digitz_ai_nexus   # should only be metadata, not enforcement
grep -R "sensitivity" apps/digitz_ai_nexus     # same
```
