# Knowledge Lifecycle

This document covers how knowledge enters the system, how it is processed into retrievable chunks, and what states it moves through.

---

## Knowledge Storage Model

Approved content is stored across the source/unit/chunk hierarchy, then supported by two semantic layers:

```
Nexus Knowledge Source
    └── Nexus Knowledge Unit
            └── Nexus Knowledge Chunk (retrievable)

Nexus Knowledge Index Entry       (chunk-linked semantic retrieval metadata)
Nexus Knowledge Context Summary   (group-level human-readable summary)
```

| Layer | Purpose | Autoname |
|---|---|---|
| Knowledge Source | Top-level entry; holds source file or manual content | field:title |
| Knowledge Unit | Parsed and versioned content unit; created from a source | NKU-.##### |
| Knowledge Chunk | Smallest retrievable unit; carries embedding and access policy | NKC-.##### |
| Knowledge Index Entry | Chunk-linked possible questions and intellectual summaries used for retrieval | NKIE-.##### |
| Knowledge Context Summary | Consolidated summary for a tenant/classification group | NKCS-.##### |

**Access policy propagates downward:**

```
Source.access_policy → Unit.access_policy → Chunk.access_policy
```

Retrieval filters are applied at the **chunk level** — this is the runtime enforcement point.

The source is provenance. The chunk is the grounded answer content. The context summary is not owned by a single source; it is owned by the tenant/classification group and can consolidate many sources that describe the same aspect.

---

## Knowledge Source

`Nexus Knowledge Source` is the entry point for all knowledge. A source can be:

| source_type | Content |
|---|---|
| PDF | Uploaded PDF file |
| DOCX | Uploaded Word document |
| TXT | Uploaded plain text file |
| Manual | Content typed directly into `manual_content` |

### Key Fields

| Field | Type | Purpose |
|---|---|---|
| title | Data (unique) | Human name for the source |
| source_type | Select | PDF / DOCX / TXT / Manual |
| source_file | Attach | Uploaded file |
| manual_content | Long Text | For Manual type |
| access_policy | Link → Nexus Access Policy | **Required before publishing** |
| status | Select | Draft / Pending Review / Processed / Ready to Publish / Published / Disabled |
| priority | Int | Boosts retrieval score for this source's chunks |
| chat_category | Link → Nexus Chat Category | Optional category used by chat/Q&A routing |
| processing_status | Select | Tracks ingestion progress |
| embedding_status | Select | Tracks embedding generation progress |
| diagnostics_status | Select | Quality check status |
| validation_status | Select | Pending / Passed / Failed |
| retrieval_ready | Check | Set to 1 only when Published + all answers approved + embedding complete + chunks present |
| generated_knowledge_unit | Link | Points to the active unit |

### Business Classification Fields

These are metadata for filtering relevance (not access enforcement):

- `tenant`, `business_unit`, `project`
- `context`, `sub_context`
- `entity_type`, `entity`, `topic`

### Status Flow

```
Draft
  → [Process] → Processed
                  → [Approve Answers] → (strict_ready satisfied)
                  → [Validate]        → Ready to Publish   (validation passed + all answers approved)
                                      → Processed          (validation passed but answers not all approved)
                                      → Pending Review     (missing required fields)
                  → [Publish]         → Published
  → [Disable]   → Disabled
```

- A source without `access_policy` cannot be published.
- `Pending Review` is set when validation detects missing required fields; a human must correct and re-validate.
- `Ready to Publish` requires both validation passing **and** all `User Question` index entries being `Approved` (strict_ready).
- `retrieval_ready` is set to `1` only after: `status = Published`, at least one active chunk with `embedding_status = Completed`, `diagnostics_status` complete, and **all User Question index entries Approved** (`strict_ready = 1`).
- `retrieval_ready` resets to `0` if the source is unpublished, re-ingested, or its access policy changes.

---

## Ingestion Pipeline

Triggered by `services/knowledge_source_processor.py` → `process_knowledge_source(source_name)`.

### Step-by-Step

```
1. Load source document from Frappe
2. Extract text:
   - PDF  → services/ingestion/parser_pdf.py
   - DOCX → services/ingestion/parser_docx.py
   - TXT  → services/ingestion/parser_txt.py
   - Manual → use manual_content field directly
3. Create new Nexus Knowledge Unit
   - Copy access_policy, tenant, business_unit, project, context etc. from source
   - Set version (increment if re-processing)
   - Status: Active
4. Archive existing chunks for this source
   - Mark old chunks as archived so they are no longer retrieved
5. Disable previous knowledge units for this source
6. Chunk the extracted text
   - Default: 800 characters per chunk, 120 character overlap
   - Smart paragraph-aware splitting
7. For each chunk:
   a. Normalize text (whitespace, encoding)
   b. Compute SHA-256 hash for deduplication
   c. Run diagnostics:
      - too_short: chunk is below minimum viable size
      - duplicate: hash matches a chunk already seen in this run
      - no_embedding: embedding generation failed
   d. Generate embedding via OpenAI text-embedding-3-small
   e. Create Nexus Knowledge Chunk record
      - Copy access_policy, tenant, context, etc. from source/unit
      - Store embedding as JSON in embedding field
      - Set embedding_status = Completed
8. Update source status flags:
   - processing_status, embedding_status, diagnostics_status
   - Source status moves to `Processed`
   - retrieval_ready remains 0 until answer approval and validation are complete
9. Generate `Nexus Knowledge Index Entry` rows for each new chunk:
   - `Intellectual Summary`: intent-oriented meaning labels, e.g. "what a cat is"
   - `User Question`: likely questions that the chunk can answer
   - Each entry links to the source, unit, chunk, chat category, access policy, and classification fields
10. Refresh `Nexus Knowledge Context Summary` for each affected tenant/classification group:
   - Uses all active completed chunks in the same group
   - Updates `source_count`, `chunk_count`, `generated_from_sources`, summary text, and embedding
```

### Chunking Algorithm

`engine/chunking.py` and `services/ingestion/chunker.py`:

- Text is first split on paragraph boundaries (double newlines)
- Headings are detected and kept with the following block
- If a block exceeds `chunk_size`, it is split on word boundaries
- `overlap_chars` of the previous chunk is prepended to the next for context continuity
- Defaults: `chunk_size = 800`, `chunk_overlap = 120` (configurable in Nexus Settings)

### Deduplication

Each chunk gets a SHA-256 hash of its normalized content. If a hash is seen twice within the same ingestion run, the second chunk is flagged as a duplicate and skipped. This prevents redundant embeddings from inflating retrieval results.

### Context Path

Each chunk inherits a `context_path` string built from its classification metadata:

```
{context}/{sub_context}/{entity_type}/{entity}/{topic}
```

Example: `Operations/Procurement/Vendor/ACME Corp/Payment Terms`

This is used in keyword scoring during retrieval.

---

## Answer Approval

After processing, each `User Question` index entry generated for the source must be reviewed before the source can reach `Ready to Publish`.

### Why It Exists

Processing generates candidate questions the AI believes the chunk can answer. A human reviews these to confirm they are accurate — approving correct ones and rejecting misleading ones. Only when every `User Question` entry for the source is either `Approved` (none `Rejected` or `Pending Review`) does the source satisfy `strict_ready`. Without `strict_ready`, the source cannot move to `Ready to Publish`, and even if Published, `retrieval_ready` stays `0`.

### Answer Review Fields on Index Entry

| Field | Values | Purpose |
|---|---|---|
| `answer_review_status` | Pending Review / Approved / Rejected | Per-entry review decision |
| `answer_review_notes` | Small Text | Reviewer notes |
| `answer_reviewed_by` | Link → User | Who reviewed |
| `answer_reviewed_on` | Datetime | When reviewed |

Only `User Question` entries require review. `Intellectual Summary` entries are excluded from the `strict_ready` calculation.

### strict_ready Condition

```
strict_ready = 1  when:
    total User Question entries > 0
    AND all entries have answer_review_status = "Approved"
    AND none are "Rejected" or "Pending Review"
```

---

## Knowledge Unit

`Nexus Knowledge Unit` is the intermediate layer between a source and its chunks.

### Key Fields

| Field | Type | Purpose |
|---|---|---|
| title | Data | Auto-generated from source |
| tenant | Link → Nexus Tenant | Tenant scope |
| access_policy | Link → Nexus Access Policy | Inherited from source |
| status | Select | Draft / Review / Approved / Active / Archived |
| version | Int | Incremented on re-ingestion |
| content | Long Text | Full extracted text |
| content_hash | Data | SHA-256 of full content |
| chunk_count | Int | Number of chunks generated |
| embedding_status | Select | Pending / Completed / Failed |

---

## Knowledge Chunk

`Nexus Knowledge Chunk` is the atomic unit for retrieval. Every embedding query resolves against chunks.

### Key Fields

| Field | Type | Purpose |
|---|---|---|
| knowledge_unit | Link (reqd) | Parent unit |
| knowledge_source | Link | Parent source |
| tenant | Link (reqd) | Tenant scope |
| **access_policy** | Link → Nexus Access Policy (reqd) | **Runtime enforcement key** |
| chunk_index | Int | Position within the unit |
| chunk_text | Long Text | The actual text content |
| chunk_hash | Data | SHA-256 for deduplication |
| disabled | Check | Set to 1 to exclude from retrieval |
| priority | Int | Boosted in scoring (0 = normal) |
| embedding | Long Text | JSON array of floats |
| embedding_model | Data | e.g. `text-embedding-3-small` |
| embedding_status | Select | Pending / Completed / Failed |
| context, sub_context, entity_type, entity, topic | Data | Business classification |
| context_path | Data | Pre-built `context/sub_context/…` string |

### Retrieval Filter

A chunk is included in retrieval candidates only when:

```
chunk.access_policy IN allowed_access_policies
AND chunk.disabled = 0
AND chunk.embedding_status = "Completed"
```

The source's `retrieval_ready` flag is also checked at a higher level before fetching candidates.

---

## Knowledge Index Entry

`Nexus Knowledge Index Entry` stores retrieval-friendly semantic metadata. It is **chunk-owned** and exists to find the correct approved chunk faster.

### Entry Types

| Entry Type | Purpose |
|---|---|
| Intellectual Summary | Technical intent label describing what the fact is about |
| User Question | Likely user question that can be answered by the linked chunk |

### Ownership

```
Tenant / Classification / Access Policy
    └── Knowledge Source
            └── Knowledge Unit
                    └── Knowledge Chunk
                            └── Knowledge Index Entry
```

Every index entry carries:

- `knowledge_source`, `knowledge_unit`, `knowledge_chunk`
- `tenant`, `business_unit`, `project`
- `context`, `sub_context`, `entity_type`, `entity`, `topic`, `context_path`
- `access_policy`, `sensitivity`, `priority`
- `chat_category`
- `embedding`, `embedding_model`, `embedding_status`

The index entry is never treated as answer evidence. It is a retrieval shortcut that points back to the approved chunk.

---

## Knowledge Context Summary

`Nexus Knowledge Context Summary` stores a consolidated human-readable summary for a tenant/classification group. It is **group-owned**, not source-owned.

### Group Key

The summary is grouped by:

```
tenant
business_unit
project
context
sub_context
entity_type
entity
topic
access_policy
```

This allows multiple sources about the same business aspect to contribute to one summary.

### Coverage Fields

| Field | Purpose |
|---|---|
| source_count | Number of active contributing sources |
| chunk_count | Number of active completed chunks in the group |
| generated_from_sources | JSON list of source names |
| summary_text | Human-readable group summary |
| embedding | Vector used as a broad retrieval signal |

The context summary can be shown in Q&A popup summary sections and can boost retrieval toward the right group. It is not used as factual answer text unless the same facts are present in approved chunks.

---

## Test Cases and Test Runs

`Nexus Knowledge Test Case` and `Nexus Knowledge Test Run` support pre-publish validation.

- A test case defines a query, expected result, and pass conditions (presence/absence of text in the answer)
- A test run records the execution result for a test case against a source
- Sources can require validation before being marked `retrieval_ready`

---

## Re-Ingesting a Source

When a source is re-processed:

1. The old knowledge unit is disabled
2. Old chunks are archived (`disabled = 1`)
3. A new unit is created with an incremented version number
4. New chunks are generated and embedded
5. Old index entries for that source are archived
6. New chunk-linked index entries are generated
7. Affected grouped context summaries are refreshed
8. `retrieval_ready` is reset and recalculated

The old data is kept in the database for traceability. Only the new chunks participate in retrieval.
