# API Reference

All endpoints are whitelisted Frappe API functions. Call them via:

```
POST /api/method/{dotted.module.path}
Content-Type: application/json
X-Frappe-CSRF-Token: {token}

{ ...payload... }
```

---

## Query

### `digitz_ai_nexus.api.query.log_query`

Logs a completed query to the `Nexus Query Log`. Called internally by the answer pipeline; can also be called externally by live/experience apps after they execute a query.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| payload | dict | The query contract used for the query |
| retrieval_result | dict | Return value from `retrieve_allowed_chunks` |
| answer | str | The answer text |
| status | str | `"Success"` or `"Failed"` |
| error_message | str | Error details on failure |

**Logged Fields:**

`tenant`, `business_unit`, `project`, `caller_system`, `use_case`, `query`, `context`, `sub_context`, `entity_type`, `entity`, `topic`, `user_id`, `user_roles`, `access_status`, `retrieved_chunks`, `answer`, `confidence`, `llm_model`, `error_message`

---

## Knowledge Source

### `digitz_ai_nexus.api.knowledge_source.create_knowledge_source`

Creates a new `Nexus Knowledge Source` record.

### `digitz_ai_nexus.api.knowledge_source.upload_source_file`

Handles file upload and attaches it to a knowledge source.

### `digitz_ai_nexus.api.knowledge_source.process_source`

Triggers the full ingestion pipeline for a knowledge source (text extraction → chunking → embedding).

---

## Knowledge (Chunks)

### `digitz_ai_nexus.api.knowledge.generate_chunks`

Generates `Nexus Knowledge Chunk` records from a `Nexus Knowledge Unit`.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| knowledge_unit | str | Name of the Nexus Knowledge Unit |
| replace_existing | bool | Archive old chunks before generating new ones |

Propagates `access_policy`, `context`, `entity`, and other classification fields from the unit to each chunk.

---

## Embedding

### `digitz_ai_nexus.api.embedding.generate_embedding`

Generates and stores an embedding for a knowledge chunk.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| chunk_name | str | Name of the Nexus Knowledge Chunk |

Returns the embedding vector. Updates `chunk.embedding`, `chunk.embedding_model`, and `chunk.embedding_status`.

---

## Retrieval

### `digitz_ai_nexus.api.retrieval.test_retrieval`

Executes the retrieval engine against a query for testing and debugging.

**Parameters:**

| Name | Type | Description |
|---|---|---|
| query | str | The test query |
| tenant | str | Tenant code |
| channel | str | Channel name |
| is_public | bool | Whether to force public-only access |
| ... | | Other query contract fields |

Returns the full retrieval result including `results`, `denied`, `debug`, `access_status`, and scoring details. Useful for debugging why a chunk is or is not being retrieved.

Current retrieval diagnostics can include:

| Field | Meaning |
|---|---|
| features.semantic_index | Whether semantic index entries were available for the query |
| features.context_summary | Whether grouped context summaries were available |
| features.question_first | Whether question-first narrowing was applied |
| original_candidate_count | Candidate chunk count before question-first narrowing |
| candidate_count | Candidate chunk count after narrowing/fallback path |
| question_first | Matched chunks, threshold, and match count for the possible-question shortcut |
| question_first_retry | Present when answer service retried broad content search after question-first no/low context |

---

## Setup

### `digitz_ai_nexus.api.setup.create_default_access_policies`

Creates the seven default `Nexus Access Policy` records. Called automatically during `after_install`. Safe to re-run — it uses `get_or_create` logic.

---

## Administration

### `digitz_ai_nexus.api.nexus_administration.*`

A set of admin APIs used by the Nexus Admin page. Covers system health checks, tenant configuration, and operational utilities.

Key endpoints:

| Function | Purpose |
|---|---|
| `get_administration_snapshot` | Returns selected tenant, tenant configuration, selectors, and readiness summary |
| `save_tenant_configuration` | Creates or updates tenant configuration and ensures linked master values exist |
| `get_selector_options` | Returns tenants, business units, public contexts, projects, and channels for the admin UI |

---

## Knowledge Studio

### `digitz_ai_nexus.api.nexus_knowledge_studio.*`

APIs used by the Knowledge Studio UI (`nexus_knowledge/page/nexus_studio_page/`). Supports browsing, searching, and interacting with knowledge sources and chunks from the desk interface.

Knowledge Studio uses the active tenant from the Nexus Admin page. Tenant configuration is resolved automatically from that tenant through `get_administration_snapshot()`.

Key context behavior:

| Function | Purpose |
|---|---|
| `get_active_studio_context` | Diagnostic endpoint showing the resolved Admin-derived Studio context plus the exact source/unit filters |
| `get_knowledge_source_summary` / `get_knowledge_sources` | Tenant-scoped Source Library data for the active Admin tenant |
| `get_studio_summary` / `get_knowledge_units` | Knowledge Unit data filtered by active tenant and any active business unit/project/context/ecosystem/channel fields available on the DocType |

---

## Knowledge Source Assist

### `digitz_ai_nexus.api.nexus_knowledge_source_assist.*`

APIs used by the source assistant interface. Supports guided knowledge source creation and metadata enrichment.

---

## Query Contract Reference

The `query_contract` dictionary is the primary input passed through the answer pipeline. All services consume it.

```python
query_contract = {
    # Core
    "query": "What is the leave encashment policy?",
    "original_query": "What is the leave encashment policy?",  # kept unmodified
    "use_case": "qa",                   # qa / chat / support / training / erp_assistant / sales_advisor
    "response_mode": "qa",              # matches use_case unless overridden

    # Routing
    "channel": "Website",
    "is_public": True,
    "force_public_only": True,          # set True for any public endpoint

    # Resolved AI profile (from live app)
    "ai_profile": {
        "name": "Public Q&A Profile",
        "behavior_prompt": "...",
        "tone": "clear, factual, direct",
        "response_style": "...",
        "welcome_message": "...",
        "fallback_message": "...",
        "do_not_answer_rules": "...",
        "confidence_threshold": 0.30,
        "escalation_enabled": False,
        "memory_mode": "...",
        "default_response_mode": "qa",
    },

    # User context
    "user": {
        "user_id": "guest",
        "roles": [],
    },
    "user_id": "guest",
    "user_roles": [],

    # Access (pre-resolved by access_resolver)
    "allowed_access_policies": ["Public"],

    # Tenant context
    "tenant": "ACME",
    "business_unit": "Operations",
    "project": "Alpha",
    "context": "HR",
    "sub_context": "Leave",
    "entity_type": "Policy",
    "entity": "Leave Encashment",
    "topic": "",

    # Retrieval options
    "top_k": 5,
    "project_scope_mode": "with_general",  # with_general | strict

    # Chat-specific
    "conversation_id": "NCV-00001",
    "conversation_context": "User previously asked about annual leave.",
    "is_follow_up": False,
    "response_sentence_limit": 6,
}
```

### Required Fields by Pipeline Stage

| Stage | Required Fields |
|---|---|
| Access resolution | `channel`, `is_public` / `force_public_only`, `user.roles`, `ai_profile.name` |
| Retrieval | `query`, `allowed_access_policies` (after resolution) |
| Prompt building | `query`, `original_query`, `response_mode`, `ai_profile` |
| Query logging | `tenant`, `query`, `use_case`, `user_id` |

### Guard Rule

Before calling retrieval or answer service, validate:

```python
if not query_contract.get("allowed_access_policies"):
    frappe.throw("Access policy resolution failed. Retrieval cannot proceed.")
```

An empty list means access resolution found no permitted policies. Never treat this as "allow all".

---

## Agentic Runtime

`digitz_ai_nexus_agentic` has no whitelisted Frappe API endpoints today. All agentic operations are invoked internally via Python service calls:

| Service | Module | Purpose |
|---|---|---|
| `capability_service` | `nexus_agentic_business` | Resolve capability pack, check approval requirements |
| `communication_service` | `nexus_agentic_business` | Dispatch approved messages via channel adapters |
| `tools` | `nexus_agentic_business` | Create approval requests, log decisions, store/get memory |
| `suppression_service` | `nexus_agentic_sales` | Check, add, remove contact suppression |
| `tools` | `nexus_agentic_sales` | 15 sales tools (read-only, draft, customer-facing stubs) |
| `tools` | `nexus_agentic_purchase` | 12 purchase tools (read-only, draft, vendor-facing stubs) |

All tool calls go through the registered `Nexus Agent Tool` registry and the approval policy engine. No tool writes to the database or calls external APIs directly.
