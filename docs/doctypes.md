# DocType Reference

All DocTypes in `digitz_ai_nexus`, grouped by module. Each entry lists key fields and their purpose.

---

## nexus_core

### Nexus Tenant

Multi-tenant support. Identifies a tenant by a short code.

| Field | Type | Notes |
|---|---|---|
| tenant_name | Data | Display name |
| tenant_code | Data (unique) | Primary identifier used across all other DocTypes |
| disabled | Check | Excluded from context resolution when disabled |
| description | Small Text | |

Autoname: `field:tenant_code`

---

### Nexus Settings *(Single)*

Global system configuration. One record for the entire installation.

| Field | Type | Default | Notes |
|---|---|---|---|
| default_tenant | Link → Nexus Tenant | | |
| **LLM** | | | |
| llm_provider | Select | OpenAI | |
| llm_model | Data | gpt-4o-mini | |
| api_key | Password | | OpenAI API key |
| openai_project_id | Data | | |
| **Embedding** | | | |
| embedding_provider | Select | OpenAI | |
| embedding_model | Data | text-embedding-3-small | |
| **Chunking** | | | |
| chunk_size | Int | 800 | Characters per chunk |
| chunk_overlap | Int | 120 | Overlap chars between chunks |
| **Retrieval** | | | |
| top_k | Int | 5 | Final chunks returned to LLM |
| retrieval_candidate_limit | Int | 30 | Pre-reranking candidate pool |
| rerank_candidate_limit | Int | 20 | Candidates passed to re-ranker |
| minimum_confidence | Float | 0.20 | Threshold below which fallback is returned |
| **Scoring Weights** | | | |
| vector_weight | Float | 0.75 | |
| keyword_weight | Float | 0.20 | |
| business_term_weight | Float | | Boost for matching business keywords |
| project_boost_weight | Float | | Boost for project-scoped chunks |
| **Feature Flags** | | | |
| enable_multi_query | Check | 1 | Enable query expansion |
| enable_reranking | Check | 1 | Enable re-ranking pass |
| enable_retrieval_debug | Check | 0 | Include debug info in retrieval result |
| strict_mode | Check | | Enables strict tenant/project scoping |

---

### Nexus Business Keyword

Business-domain keywords used to boost retrieval scoring when a query contains known terms.

| Field | Type | Notes |
|---|---|---|
| keyword | Data | |
| category | Link → Nexus Keyword Category | |
| priority | Int | |
| description | Small Text | |

---

### Nexus Keyword Category

Groups business keywords into categories.

| Field | Type | Notes |
|---|---|---|
| category_name | Data | |
| description | Small Text | |
| priority | Int | |

---

## nexus_knowledge

### Nexus Knowledge Source

Top-level knowledge entry. A source is a document or piece of content to be ingested.

| Field | Type | Notes |
|---|---|---|
| title | Data (unique, reqd) | Human name |
| source_type | Select | PDF / DOCX / TXT / Manual |
| source_file | Attach | For file-based types |
| manual_content | Long Text | For Manual type |
| **Governance** | | |
| access_policy | Link → Nexus Access Policy | Required before publishing; propagates to chunks |
| **Classification** | | |
| tenant | Link → Nexus Tenant | |
| business_unit | Data | |
| project | Data | |
| context | Data | |
| sub_context | Data | |
| entity_type | Data | |
| entity | Data | |
| topic | Data | |
| **Status** | | |
| status | Select | Draft / Ready to Publish / Published / Archived |
| priority | Int | Boosts chunks in retrieval scoring |
| processing_status | Select | Ingestion pipeline state |
| embedding_status | Select | Embedding generation state |
| diagnostics_status | Select | Quality check state |
| validation_status | Select | |
| retrieval_ready | Check | 1 = safe to retrieve from |
| **Validation** | | |
| validation_query | Data | Test query for pre-publish validation |
| validation_confidence | Float | Last validation score |
| validated_on | Datetime | |
| validated_by | Link → User | |
| review_reason | Small Text | |
| **Output** | | |
| generated_knowledge_unit | Link → Nexus Knowledge Unit | Active unit |
| extracted_text_preview | Long Text | Preview of extracted content |
| generated_chunks_html | HTML | Rendered chunk preview |

Autoname: `field:title`. Permissions: System Manager only.

---

### Nexus Knowledge Unit

Parsed content unit created from a source. One source has one active unit at a time.

| Field | Type | Notes |
|---|---|---|
| title | Data (reqd) | |
| tenant | Link → Nexus Tenant (reqd) | |
| business_unit, project | Data | |
| status | Select | Draft / Review / Approved / Active / Archived |
| version | Int (default 1) | Incremented on re-ingestion |
| source_type | Select | Manual / Document / ERP / Website / Support / Training |
| source_reference | Data | |
| content | Long Text | Full extracted text |
| **Classification** | | |
| context, sub_context, entity_type, entity, topic | Data | |
| context_path | Data | Pre-built path string |
| **Governance** | | |
| access_policy | Link → Nexus Access Policy | Inherited from source |
| sensitivity | Select | Optional metadata (not enforcement) |
| **Processing** | | |
| content_hash | Data | SHA-256 of full content |
| chunk_count | Int | Number of chunks generated |
| embedding_status | Select | |
| approved_by, approved_on | Link/Datetime | |

Autoname: `NKU-.#####`. Permissions: System Manager only.

---

### Nexus Knowledge Chunk

Smallest retrievable unit. Holds the chunk text, embedding, and access policy.

| Field | Type | Notes |
|---|---|---|
| knowledge_unit | Link → Nexus Knowledge Unit (reqd) | Parent |
| knowledge_source | Link → Nexus Knowledge Source | Grandparent (for direct joins) |
| tenant | Link → Nexus Tenant (reqd) | |
| business_unit, project | Data | |
| **Access** | | |
| **access_policy** | Link → Nexus Access Policy (reqd) | **Runtime retrieval enforcement key** |
| sensitivity | Select | Optional metadata only |
| disabled | Check (default 0) | 1 = excluded from retrieval |
| **Content** | | |
| chunk_index | Int (reqd) | Position within the unit |
| chunk_text | Long Text (reqd) | The actual text |
| chunk_hash | Data | SHA-256 for deduplication |
| priority | Int (default 0) | Boost in scoring |
| **Classification** | | |
| context, sub_context, entity_type, entity, topic | Data | |
| context_path | Data | Pre-built path string |
| **Embedding** | | |
| embedding | Long Text | JSON array of floats |
| embedding_model | Data | e.g. text-embedding-3-small |
| embedding_status | Select | Pending / Completed / Failed |
| **Legacy Role Fields** | | |
| allowed_roles | Long Text | Legacy direct role rules (kept for compatibility) |
| denied_roles | Long Text | |

Autoname: `NKC-.#####`. Permissions: System Manager only.

**Retrieval filter:** `access_policy IN allowed_policies AND disabled = 0 AND embedding_status = "Completed"`

---

### Nexus Knowledge Test Case

Defines a query-based test for validating knowledge source content.

| Field | Type | Notes |
|---|---|---|
| knowledge_source | Link → Nexus Knowledge Source | |
| query | Data | Test query |
| expected_result | Small Text | Expected answer fragment |
| pass_on_presence | Check | Pass if expected_result found in answer |
| pass_on_absence | Check | Pass if expected_result NOT found |

---

### Nexus Knowledge Test Run

Records a test case execution result.

| Field | Type | Notes |
|---|---|---|
| knowledge_source | Link | |
| test_case | Link → Nexus Knowledge Test Case | |
| result | Long Text | Answer produced |
| passed | Check | Whether the test passed |
| executed_at | Datetime | |

---

## nexus_access

### Nexus Access Policy

Knowledge classification label. The atomic unit of access governance.

| Field | Type | Notes |
|---|---|---|
| policy_name | Data (unique, reqd) | **Primary enforcement key** |
| disabled | Check | Excluded from all resolution |
| is_primitive | Check (read_only) | Only `Public` is primitive |
| access_level | Select | Optional metadata only (not enforcement) |
| sensitivity | Select | Optional metadata only (not enforcement) |
| description | Small Text | |

Autoname: `field:policy_name`. Permissions: System Manager only.

---

### Nexus Access Category

Named group of access policies. Runtime AI profiles map to categories, not directly to policies.

| Field | Type | Notes |
|---|---|---|
| category_name | Data (unique, reqd) | Primary key |
| title | Data | Display name |
| disabled | Check | Excluded from resolution |
| priority | Int (default 10) | |
| description | Small Text | |
| allowed_policies | Child Table (Nexus Access Category Policy) | Policies in this category |

Autoname: `field:category_name`. Permissions: System Manager only.

---

### Nexus Access Category Policy *(Child Table)*

One row inside `Nexus Access Category.allowed_policies`. Maps a category to one policy.

| Field | Type | Notes |
|---|---|---|
| parent | Link → Nexus Access Category | |
| parentfield | `allowed_policies` | |
| access_policy | Link → Nexus Access Policy | |

---

### Nexus Channel

Service entry lane. Kept broad and minimal.

| Field | Type | Notes |
|---|---|---|
| channel_name | Data (unique, reqd) | |
| channel_type | Select | Q&A / Chat / Internal / Simulation / API |
| disabled | Check | |
| description | Small Text | |

Autoname: `field:channel_name`. Permissions: System Manager only.

Do not add `default_ai_agent_profile`, `access_policy`, or `default_access_policy` to this DocType. A channel serves many profiles and must not be hard-wired to one.

---

### Nexus Channel Access Category

Maps a channel to an access category. Retained for admin reporting and backward compatibility. It is not called by the current runtime access resolver; runtime retrieval access is governed by the resolved `Nexus AI Agent Profile`.

| Field | Type | Notes |
|---|---|---|
| channel | Link → Nexus Channel (reqd) | |
| access_category | Link → Nexus Access Category (reqd) | |
| disabled | Check | |
| tenant, business_unit, project | Data | Optional scope narrowing |
| description | Small Text | |

Autoname: `NCAC-.#####`. Permissions: System Manager only.

---

### Nexus Role Access Category

Maps a Frappe system role to an access category. Retained for admin reporting and backward compatibility. Frappe roles do not directly produce runtime retrieval policies in the current profile-first model.

| Field | Type | Notes |
|---|---|---|
| role | Link → Role (reqd) | Frappe system role |
| access_category | Link → Nexus Access Category (reqd) | |
| disabled | Check | |
| tenant, business_unit, project | Data | Optional scope narrowing |
| description | Small Text | |

Autoname: `NRAC-.#####`. Permissions: System Manager only.

---

## nexus_ai

### Nexus LLM Provider

Registry of LLM and embedding provider configurations.

| Field | Type | Notes |
|---|---|---|
| provider_name | Data (unique, reqd) | |
| provider_type | Select (default OpenAI) | OpenAI / Other |
| disabled | Check | |
| base_url | Data | For custom/self-hosted endpoints |
| api_key | Password | |
| default_llm_model | Data (default gpt-4o-mini) | |
| default_embedding_model | Data (default text-embedding-3-small) | |
| description | Small Text | |

Autoname: `field:provider_name`. Permissions: System Manager only.

---

## nexus_operations

### Nexus Ecosystem

Per-tenant operational configuration. Defines defaults, feature flags, and widget settings for a tenant.

| Field | Type | Notes |
|---|---|---|
| tenant | Link → Nexus Tenant (reqd) | |
| ecosystem_name | Data (reqd) | |
| ecosystem_type | Select | Production / Sandbox / Synthetic Validation / Internal Platform |
| enabled | Check (default 1) | |
| is_default | Check | Default ecosystem for this tenant |
| activation_status | Select | Draft / Configured / Testing / Certified / Active / Suspended |
| **Defaults** | | |
| default_business_unit | Data | |
| default_project | Data | |
| default_public_context | Data | |
| **Knowledge Rules** | | |
| require_approved_knowledge | Check | Only allow knowledge in Approved status |
| strict_tenant_mode | Check | Strict tenant isolation |
| default_top_k | Int | Override global top_k for this tenant |
| **Q&A** | | |
| qa_enabled | Check | |
| default_qa_channel | Link → Nexus Channel | |
| qa_fallback_message | Small Text | |
| source_citation_required | Check | |
| **Live Chat** | | |
| live_chat_enabled | Check | |
| default_chat_channel | Link → Nexus Channel | |
| default_live_channel | Data | |
| default_public_agent | Data | |
| default_public_escalation_queue | Data | |
| default_escalation_enabled | Check | |
| **Widget** | | |
| website_widget_enabled | Check | |
| widget_title | Data | |
| widget_welcome_message | Small Text | |
| widget_brand_color | Color | |
| **Governance** | | |
| testing_required_before_activation | Check | Requires test runs before retrieval_ready |
| last_certified_on | Date | |
| certification_status | Select | |
| notes | Long Text | |

Autoname: `NECO-.#####`. Permissions: System Manager only.

---

### Nexus Query Log

Audit trail for every query processed by the system.

| Field | Type | Notes |
|---|---|---|
| tenant | Link → Nexus Tenant | |
| business_unit, project | Data | |
| caller_system | Data | Which app/system made the call |
| use_case | Data | qa / chat / internal / etc. |
| status | Select | Success / Failed |
| **Query** | | |
| query | Long Text | The user's query |
| context, sub_context, entity_type, entity, topic | Data | |
| **User** | | |
| user_id | Data | |
| user_roles | Long Text | JSON array of roles |
| **Result** | | |
| access_status | Select | allowed / restricted / no_context |
| retrieved_chunks | Long Text | JSON array of chunk IDs used |
| answer | Long Text | First ~2000 chars of answer |
| confidence | Float | |
| llm_model | Data | |
| error_message | Long Text | On failure |

Autoname: `NQL-.#####`. Permissions: System Manager only.

---

### Nexus User Context

Stores a user's active tenant and ecosystem selection. Resolved during query context setup.

| Field | Type | Notes |
|---|---|---|
| user | Link → User (reqd) | |
| enabled | Check (default 1) | |
| is_default | Check (default 1) | Used as fallback if no explicit context in request |
| active_tenant | Link → Nexus Tenant (reqd) | |
| active_ecosystem | Link → Nexus Ecosystem | |
| active_business_unit | Data | |
| active_project | Data | |
| active_channel | Link → Nexus Live Channel | |
| last_used_on | Datetime | Updated on each request |
| notes | Long Text | |

Autoname: `NUC-.#####`. Permissions: System Manager only.
