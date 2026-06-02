# Architecture Overview

DIGITZ AI Nexus is a governed AI platform built on Frappe Framework. It is the core intelligence engine for the DIGITZ AI suite — not a standalone chatbot, but a multi-tenant, access-aware knowledge management and retrieval system that can power Q&A, live chat, and future agentic capabilities.

---

## App Family

The platform is deliberately split across three apps. Each app has a single, bounded responsibility. Do not mix these responsibilities or create a fourth app without an explicit reason.

| App | Role |
|---|---|
| `digitz_ai_nexus` | AI core: knowledge, access governance, retrieval, answer engine |
| `digitz_ai_nexus_live` | Live conversation runtime: chat sessions, escalation, human handover |
| `digitz_ai_experience` | User-facing layer: website widgets, public chat UI, embed scripts |

**Mental model:**

```
digitz_ai_nexus        = governed AI brain
digitz_ai_nexus_live   = live conversation runtime
digitz_ai_experience   = website/customer experience layer
```

The live and experience apps call into `digitz_ai_nexus` services. They must not duplicate retrieval logic, access resolution, or prompt building.

---

## What `digitz_ai_nexus` Owns

This app contains and maintains:

- Knowledge source ingestion pipeline (PDF, DOCX, TXT, manual)
- Knowledge chunking, embedding generation, and deduplication
- Access policy and access category definitions
- Role-to-category and channel-to-category access mappings
- Access resolution engine (calculates final allowed policies per request)
- Retrieval engine (hybrid vector + keyword scoring, re-ranking)
- Prompt builder (behavior-driven, mode-aware)
- LLM and embedding provider abstraction (OpenAI today, extensible)
- Answer service (orchestrates full query → answer pipeline)
- Query logging and audit trail
- Multi-tenant context resolution
- Knowledge test cases and test runs

---

## Top-Level Module Layout

```
digitz_ai_nexus/
├── api/                  Whitelisted Frappe API endpoints
├── engine/               Core RAG and access resolution logic
│   ├── retrieval_engine/ Query expansion, scoring, re-ranking, debug
├── services/             Business orchestration services
│   └── ingestion/        Document parsers and chunking pipeline
├── setup/                Install-time access seeding
├── nexus_core/           Tenant, settings, and keyword DocTypes
├── nexus_knowledge/      Knowledge source, unit, chunk, test DocTypes
├── nexus_access/         Access policy, category, channel, role DocTypes
├── nexus_ai/             LLM provider DocType
├── nexus_operations/     Ecosystem, query log, user context DocTypes
├── nexus_security/       Security utilities
├── public/               CSS and JS assets
└── tests/                Test suite with fake providers
```

---

## System Data Flow

```
Request (query + context)
    │
    ▼
Resolve tenant context
(services/tenant_context.py)
    │
    ▼
Resolve allowed access policies
(engine/access_resolver.py)
─ public? → ["Public"] only
─ authenticated? → profile ∩ role ∩ channel
    │
    ▼
Expand query variants
(engine/retrieval_engine/query_expansion.py)
    │
    ▼
Generate query embedding
(engine/embedding.py → OpenAI text-embedding-3-small)
    │
    ▼
Fetch candidate chunks from DB
(filters: access_policy IN allowed, disabled=0, embedding_status=Completed)
    │
    ▼
Score candidates — hybrid
(vector 75% + keyword 20% + priority 5%)
(engine/retrieval_engine/scoring.py)
    │
    ▼
Re-rank candidates
(engine/retrieval_engine/reranker.py)
    │
    ▼
Apply scope balance (project vs general)
    │
    ▼
Check confidence threshold
(answer_service.py → min 0.20 default)
    │
    ├── Below threshold → safe fallback response
    │
    ▼
Build prompt
(engine/prompt.py — behavior-driven, mode-aware)
    │
    ▼
Call LLM
(engine/llm.py → OpenAI gpt-4o-mini)
    │
    ▼
Format and package response
(services/answer_formatter.py)
    │
    ▼
Log query
(api/query.py → Nexus Query Log)
    │
    ▼
Return answer with sources, confidence, citations
```

---

## Security Model

### Fail-Closed

The system fails closed on access errors. An empty `allowed_access_policies` list is never interpreted as "allow all". It immediately denies retrieval.

```python
# In answer_service.py and retrieval.py
if allowed_policies is not None and len(allowed_policies) == 0:
    frappe.throw("Access policy resolution produced no permitted policies. Retrieval denied.")
```

### Public Override

Public endpoints always force `allowed_access_policies = ["Public"]`, regardless of any profile, role, or channel configuration. This cannot be bypassed.

```python
# In access_resolver.py
if force_public_only or is_public:
    return {"allowed_access_policies": ["Public"], "force_public_only": True, ...}
```

### Restricted vs No Context

If the retrieval engine finds relevant chunks that the user cannot access, it returns `access_status: "restricted"` with the answer `"You do not have permission to access this information."` — not a generic "no context" fallback. These two states are always kept distinct.

---

## Multi-Tenancy

Every significant operation can be scoped to a tenant:

- `Nexus Tenant` — defines a tenant by code
- `Nexus Ecosystem` — per-tenant configuration (defaults, channels, features)
- `Nexus User Context` — stores a user's active tenant/ecosystem selection
- Knowledge sources, units, and chunks carry a `tenant` field
- Query logs capture `tenant`

Tenant resolution priority in `services/tenant_context.py`:

1. Explicit `tenant` in the request payload
2. User's active `Nexus User Context`
3. Default ecosystem for the tenant

---

## Design Principles

1. **Category-based access** — roles map to access categories, not directly to policies. This keeps access rules reusable and composable.
2. **Chunk-level enforcement** — access policy is stored on each chunk and checked at retrieval time, not at source level.
3. **Profile-driven behavior** — tone, style, fallback, and do-not-answer rules come from `Nexus AI Agent Profile`, not hard-coded strings.
4. **Hybrid retrieval** — combines vector similarity with keyword matching and priority boosting for better recall and precision.
5. **Configurable, not hard-coded** — only `Public` is a primitive policy. All others are user-defined. Chunk size, scoring weights, and model choices are settings.
6. **App isolation** — retrieval logic, access resolution, and prompt building live only in this app. The live and experience apps call these services; they do not reimplement them.
