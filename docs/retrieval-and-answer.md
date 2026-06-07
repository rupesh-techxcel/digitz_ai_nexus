# Retrieval and Answer Engine

This document covers the full pipeline from receiving a query to producing an answer — retrieval, scoring, re-ranking, prompt construction, LLM call, and response packaging.

---

## Overview

The pipeline is orchestrated by `services/answer_service.py` → `answer_query()`.

### Chat Mode Pipeline

In chat mode (`response_mode = "chat"` or `"live chat"`), two pre-checks run before the RAG pipeline:

```
Query arrives (chat mode)
    │
    ▼
1. Length Guard
    If message > 500 characters:
        → LLM generates friendly nudge to shorten the question
        → Return immediately
    │
    ▼
2. Intent Router  (single LLM call)
    LLM receives: user message + conversation context + resolved intent handlers
    │
    ├── ACTION:ESCALATE
    │       → access_status: "intent_handled", user_requested_human: True
    │       → caller (live_chat_service) handles escalation
    │
    ├── ACTION:PREDEFINED:<name>
    │       → access_status: "intent_handled"
    │       → answer: configured response_template for that handler
    │
    ├── ACTION:DECLINED:<name>
    │       → access_status: "intent_handled"
    │       → answer: configured decline_response for that handler
    │
    ├── Conversational response
    │       → access_status: "conversational"
    │       → answer: LLM-generated 1-2 sentence social response
    │
    └── ROUTE_TO_KNOWLEDGE → continue to RAG pipeline
```

### RAG Pipeline (all modes)

```
Query arrives
    │
    ▼
Guard: allowed_access_policies must not be empty
    │
    ▼
Retrieve chunks  (engine/retrieval.py)
    │
    ├── access_status = "restricted" → return restricted response
    ├── question-first produced no/weak usable context → retry broad content retrieval
    ├── no chunks found → return fallback (chat: LLM Host; Q&A: safe string)
    │
    ▼
Calculate confidence
    │
    ├── below minimum threshold → return fallback (chat: LLM Host; Q&A: safe string)
    │
    ▼
Build prompt  (engine/prompt.py)
    │
    ▼
Call LLM  (engine/llm.py)
    │
    ├── empty or fallback answer → return fallback (chat: LLM Host; Q&A: safe string)
    │
    ▼
Build sources and citations
    │
    ▼
Return success response
```

### Chat Fallback vs Q&A Fallback

| Mode | Fallback behaviour |
|---|---|
| `chat` / `live chat` | LLM Host generates a warm, graceful response. No facts stated. May ask a clarifying question. Does NOT offer to connect with team — that is handled by the Intent Handler system. |
| All other modes | Hard fallback string: `"I do not have enough approved knowledge to answer this."` |

---

## Retrieval Engine

`engine/retrieval.py` → `retrieve_allowed_chunks(query_contract, query_embedding, embedding_provider)`

### Inputs

The `query_contract` dict must include:

| Key | Required | Purpose |
|---|---|---|
| query | Yes | The user's query text |
| allowed_access_policies | Yes (if using policy model) | Pre-resolved list of permitted policy names |
| tenant | No | Narrow retrieval to a tenant |
| business_unit | No | Narrow by business unit |
| context | No | Narrow by context |
| project | No | Narrow by project |
| project_scope_mode | No | `with_general` (default) or `strict` |
| top_k | No | Override top-K setting |
| chat_category | No | Narrows semantic index lookup for routed chat/Q&A |
| disable_question_first | No | Internal retry flag; bypasses question-first narrowing |
| user.roles | No | Used by legacy role-based check |
| is_public / force_public_only | No | Forces Public-only filter |

### Step 1: Query Expansion

If `enable_multi_query = 1` in Nexus Settings, the original query is expanded into multiple variants using `engine/retrieval_engine/query_expansion.py`. The original query is always included as the first variant.

Multiple variants increase recall: a chunk that matches one variant but not another is still retrieved.

### Step 2: Fetch Candidate Chunks

`build_context_filters(query_contract)` builds database filters:

```python
filters = {
    "disabled": 0,
    "embedding_status": "Completed",
    "access_policy": ["in", allowed_access_policies],  # if provided
    # plus any context/tenant/project fields present in the contract
}
```

Chunks are fetched from `Nexus Knowledge Chunk`. Role fields are then enriched from the parent `Nexus Knowledge Unit` (for legacy role-based checks).

### Step 3: Question-First Semantic Index

Before broad chunk scoring, retrieval checks `Nexus Knowledge Index Entry` rows with `entry_type = "User Question"`.

If one or more possible questions match the user query above `QUESTION_FIRST_THRESHOLD` (`0.68`), retrieval narrows candidate chunks to the linked `knowledge_chunk` values, capped by `QUESTION_FIRST_CANDIDATE_LIMIT` (`5`).

This is an optimization, not a guarantee:

- It is used only when confidence is high.
- It only identifies candidate chunks.
- It does not answer from the stored question text.
- If no strong possible-question match exists, retrieval continues with the normal broader content search.
- If answer service later finds that the narrowed result is missing or below confidence, it retries retrieval with `disable_question_first = 1`.

`Nexus Knowledge Index Entry` can also contain `entry_type = "Intellectual Summary"`. These entries are scored as semantic retrieval signals and boost linked chunks, but they do not by themselves narrow the candidate set.

### Step 4: Context Summary Signal

Retrieval also scores matching `Nexus Knowledge Context Summary` records. These summaries are grouped by tenant/business unit/context/sub-context/entity/topic/access policy.

The context summary:

- boosts chunks that belong to the same classification group,
- helps broad routing toward the right knowledge area,
- is not answer evidence,
- is not passed to the LLM as approved factual knowledge.

### Step 5: Project Scope Modes

| Mode | Behavior |
|---|---|
| `with_general` (default) | Returns chunks from the requested project AND general chunks (no project) |
| `strict` | Returns only chunks from the exact requested project |

### Step 6: Hybrid Scoring

For each query variant and each candidate chunk, a composite score is calculated:

```
hybrid_score =
    (vector_score  × 0.75)
  + (keyword_score × 0.20)
  + (priority_score × 0.05)
```

**Vector score:** Cosine similarity between the query embedding and the chunk embedding.

```python
dot = sum(a * b for a, b in zip(vec1, vec2))
cosine_similarity = dot / (norm(vec1) * norm(vec2))
```

**Keyword score:** Token overlap between query and chunk text + context path, with a phrase boost if the full query string appears verbatim.

```python
base_score = matched_tokens / total_query_tokens
phrase_boost = 0.25 if full_query found in chunk_text else 0
keyword_score = min(base_score + phrase_boost, 1.0)
```

Stop words are removed before tokenizing. Current stop word list:

```
what, is, are, the, a, an, of, to, in, on, for, and, or, with, about, how,
why, when, where, does, do, can, you, me, explain, tell
```

**Priority score:** Normalized chunk priority (`chunk.priority / 10`, capped at 1.0).

Semantic index and context summary scores can add bounded boosts to `hybrid_score` after the base chunk score is calculated. The final answer still uses the linked chunk's `chunk_text` as the grounded source.

### Step 7: Multi-Query Merge

Across all query variants, the best score for each chunk is kept. `matched_queries` accumulates which variants each chunk matched.

### Step 8: Sort and Limit

Candidates are sorted descending by `(hybrid_score, retrieval_stability_score, keyword_score, vector_score, priority_score)`. The list is then trimmed to `retrieval_candidate_limit` (default 30).

### Step 9: Restricted Check

Before re-ranking, the engine compares the best-scoring denied chunk against the best-scoring allowed chunk. If the denied chunk scores higher, the result is `access_status: restricted` — meaning the system has relevant knowledge but the user cannot access it.

### Step 10: Re-ranking

If `enable_reranking = 1`, `engine/retrieval_engine/reranker.py` re-ranks candidates. It applies bonus scores based on secondary signals (exact match, project alignment, semantic quality). Re-ranking adjusts `rank_after_rerank`, `rerank_bonus`, and `rerank_score` on each candidate.

### Step 11: Scope Balance

`apply_scope_balance()` ensures the final top-K results include at least one project-specific chunk and one general chunk when both exist. This prevents project-scoped queries from returning only generic knowledge.

### Step 12: Return

```python
{
    "results": [top-K final chunks with all scores],
    "debug": [...],               # populated if enable_retrieval_debug = 1
    "denied": [...],              # denied chunks with reasons
    "query_variants": [...],
    "candidate_count": N,
    "original_candidate_count": N,
    "allowed_count": N,
    "denied_count": N,
    "retrieval_mode": "hybrid_grounded_rag",
    "project_scope_mode": "with_general",
    "access_status": "allowed" | "no_context" | "restricted",
    "weights": {...},
    "features": {...},
    "question_first": {
        "applied": true | false,
        "threshold": 0.68,
        "matched_chunks": ["NKC-..."],
        "match_count": N,
    },
}
```

### Scoring Stability Score

Each candidate also gets a `retrieval_stability_score` computed with slightly different weights than `hybrid_score`. This is used for tie-breaking and debug consistency:

```
stable_final_score =
    vector_score  × 0.45
  + keyword_score × 0.25
  + priority_score × 0.10
  + project_boost × 0.10
  + rerank_score  × 0.10
```

Semantic index and context summary boosts are also included in the pre-rerank stability score so the linked chunk remains visible in diagnostics.

---

## Confidence Calculation

`answer_service.py` → `calculate_confidence(chunks)`

Confidence is a weighted combination of the top chunk score and the average across all returned chunks:

```python
confidence = (top_score * 0.7) + (avg_score * 0.3)
```

`final_score` is preferred, falling back to `score`, then `hybrid_score`.

The minimum confidence threshold defaults to **0.20** and is configurable in `Nexus Settings.minimum_confidence`.

If retrieved chunks fail to meet the threshold and question-first narrowing was applied, `answer_query()` retries retrieval with `disable_question_first = 1`. This ensures a possible-question match cannot suppress broader content search. If the retry finds restricted knowledge, the response remains restricted. If the retry still cannot produce grounded context, a safe fallback response is returned.

---

## Prompt Builder

`engine/prompt.py` → `build_prompt(query_contract, retrieved_chunks)`

### Behavior Resolution

Profile fields are extracted from `query_contract["ai_profile"]` (structured) or from legacy flat fields (`agent_behavior_prompt`, `agent_tone`, etc.):

| Field | Effect |
|---|---|
| behavior_prompt | Injected as `AGENT BEHAVIOUR:` block |
| tone | Overrides response mode tone |
| response_style | Added as `Response Style:` line |
| fallback_message | Replaces default fallback text |
| do_not_answer_rules | Injected as `DO NOT ANSWER RULES:` block |

### Response Modes

`engine/response_mode.py` provides mode templates:

| Mode Key | Label | Default Tone |
|---|---|---|
| `qa` | Q&A | Clear, factual, direct |
| `chat` | Chat | Friendly, conversational, helpful |
| `support` | Support | Polite, careful, customer-support oriented |
| `training` | Training | Educational, patient, step-by-step |
| `erp_assistant` | ERP Assistant | Precise, operational, action-oriented |
| `sales_advisor` | Sales Advisor | Professional, consultative, value-focused |

Mode is determined by `query_contract["response_mode"]` or `query_contract["use_case"]`. Falls back to `qa`.

### Chat vs Q&A Rules

When `response_mode` is `chat` or `live chat`:

- Response is limited to a configurable sentence count (default 6)
- Conversation context is injected as a separate block with rules that prevent it from being treated as factual knowledge
- Rules enforce conversational, concise answers

When `response_mode` is anything else (Q&A mode):

- No sentence limit
- No conversation context injected
- Rules enforce direct, detailed answers

### Prompt Structure

The built prompt follows this structure:

```
You are DIGITZ AI Nexus, a controlled enterprise knowledge assistant.

CORE RULES:
1. Answer ONLY using the approved knowledge provided below.
2. Do NOT guess, invent, or add outside knowledge.
3. Do NOT expose restricted or hidden information.
4. Preserve exact named labels, policies, codes, and identifiers from the knowledge.
5. Retrieval index entries, possible questions, intellectual summaries, context summaries, scores, and routing metadata are only search signals.
6. The only factual evidence the LLM may use is the text inside each Source's Knowledge section.
7. If approved knowledge is insufficient, return the configured safe fallback exactly.

RESPONSE BEHAVIOR:
Mode: {mode_label}
Tone: {tone}
Response Style: {style}

Instructions: {mode_instructions}

AGENT BEHAVIOUR: (if profile has behavior_prompt)
...

DO NOT ANSWER RULES: (if profile has do_not_answer_rules)
...

CONVERSATION CONTEXT: (chat mode only)
...

CHAT RESPONSE RULES: (chat mode only)
...

Q&A RESPONSE RULES: (q&a mode only)
...

APPROVED KNOWLEDGE:
[Source 1]
Chunk ID: ...
Context Path: ...
Business Unit: ...
Project: ...
Scope Type: ...
Knowledge:
...

[Source 2]
...

CURRENT USER MESSAGE:
{original_query}

RETRIEVAL QUERY USED:
{query}

FOLLOW-UP DETECTED:
{bool}

ANSWER:
```

### Safe Fallback Answer

```
"I do not have enough approved knowledge to answer this."
```

This exact string is returned when:
- No chunks retrieved
- Confidence below threshold
- Question-first and broad retry cannot produce usable approved context
- LLM returns empty response
- LLM echoes back the fallback phrase verbatim

---

## LLM Provider

`engine/llm.py` → `generate_answer(prompt, provider)`

- Default model: `gpt-4o-mini`
- Temperature: `0.2` (low, deterministic outputs)
- System message: `"You are DIGITZ AI Nexus, a controlled enterprise knowledge assistant."`
- Reads API key from `Nexus Settings.api_key`

An `OpenAILLMProvider` class wraps the OpenAI client. Custom providers can be passed via the `provider` argument to `generate_answer()`.

---

## Embedding Provider

`engine/embedding.py` → `generate_embedding(text, provider)`

- Default model: `text-embedding-3-small`
- Returns a list of floats (the embedding vector)
- Reads API key from `Nexus Settings.api_key`

An `OpenAIEmbeddingProvider` class wraps the client. Fake providers are used in tests (`tests/providers/fake_embedding.py`).

---

## Answer Service Response Structure

`services/answer_service.py` → `answer_query()` returns one of the following shapes.

### `access_status` values

| Value | When |
|---|---|
| `allowed` | RAG found usable knowledge; answer is grounded |
| `conversational` | Router handled the turn directly (social exchange) |
| `intent_handled` | A special case intent was matched (escalate / predefined / declined) |
| `no_context` | RAG found no usable knowledge; fallback response returned |
| `restricted` | Knowledge exists but the user lacks access |

---

### RAG Success

```python
{
    "status": "success",
    "access_status": "allowed",
    "answer": "...",
    "confidence": 0.72,
    "sources": [
        {
            "chunk": "NKC-00001",
            "knowledge_unit": "NKU-00001",
            "knowledge_title": "...",
            "context_path": "Operations/Finance/...",
            "business_unit": "Finance",
            "project": "Alpha",
            "score": 0.81,
            "final_score": 0.77,
            "vector_score": 0.85,
            "keyword_score": 0.60,
            "rerank_score": 0.79,
            "chunk_preview": "First 300 chars of chunk text...",
            ...
        }
    ],
    "citations": [{"source_no": 1, "chunk": "NKC-00001", "knowledge_title": "...", ...}],
    "retrieval_result": {...},
    "fallback_used": 0,
}
```

### Conversational (router handled directly)

```python
{
    "status": "success",
    "access_status": "conversational",
    "answer": "Hi! How can I help you today?",
    "confidence": 1.0,
    "sources": [],
    "citations": [],
    "retrieval_result": {},
    "fallback_used": 0,
}
```

### Intent Handled — Escalate

```python
{
    "status": "success",
    "access_status": "intent_handled",
    "answer": "I'll connect you with our team shortly.",
    "confidence": 1.0,
    "sources": [],
    "citations": [],
    "retrieval_result": {},
    "fallback_used": 0,
    "user_requested_human": True,
    "intent_action": "escalate",
}
```

`user_requested_human: True` is read by `live_chat_service` to trigger escalation.

### Intent Handled — Predefined Answer

```python
{
    "status": "success",
    "access_status": "intent_handled",
    "answer": "Our support team is available Monday–Friday, 9am–6pm.",
    "confidence": 1.0,
    "sources": [],
    "citations": [],
    "retrieval_result": {},
    "fallback_used": 0,
    "intent_action": "predefined",
}
```

### Intent Handled — Declined

```python
{
    "status": "success",
    "access_status": "intent_handled",
    "answer": "Pricing information is not available through this assistant.",
    "confidence": 1.0,
    "sources": [],
    "citations": [],
    "retrieval_result": {},
    "fallback_used": 0,
    "intent_action": "declined",
}
```

### Fallback (no usable knowledge)

```python
{
    "status": "success",
    "access_status": "no_context",
    "answer": "I do not have enough approved knowledge to answer this.",
    # In chat mode: LLM Host generates a warm, graceful version of this
    "confidence": 0.0,
    "sources": [],
    "citations": [],
    "retrieval_result": {...},
    "denied": [...],
    "fallback_used": 1,
}
```

### Restricted (knowledge exists but access denied)

```python
{
    "status": "success",
    "access_status": "restricted",
    "answer": "You do not have permission to access this information.",
    "confidence": 0,
    "sources": [],
    "citations": [],
    "retrieval_result": {...},
    "denied": [...],
    "fallback_used": 1,
}
```

---

## Answer Formatter

`services/answer_formatter.py` → `format_answer_response(raw_response)`

Wraps the raw answer service output into a UI-friendly format:

- `display_answer`: formatted answer text with source citations appended
- `confidence_label`: "High" / "Medium" / "Low" / "None" based on score thresholds
- `grounded`: boolean — True when `access_status = "allowed"` and `fallback_used = 0`
- `source_count`: number of sources used
- `source_summary`: human-readable source list

---

## Query Logging

`api/query.py` → `log_query(payload, retrieval_result, answer, status, error_message)`

Every query writes a `Nexus Query Log` record containing:

- `tenant`, `business_unit`, `project`
- `caller_system`, `use_case`
- `query`, `context`, `sub_context`, `entity_type`, `entity`, `topic`
- `user_id`, `user_roles` (JSON)
- `access_status` (allowed / restricted / no_context)
- `retrieved_chunks` (JSON array of chunk IDs)
- `answer` (first 2000 chars)
- `confidence`
- `llm_model`
- `error_message` (on failure)
- `status` (Success / Failed)

This log is the primary governance and debugging tool. It shows exactly what the system retrieved, what it denied, and what it answered.
