# Chat Agent Loop — Design Document

**App:** `digitz_ai_nexus`  
**Status:** Design (not yet implemented)  
**Parent module:** `digitz_ai_nexus/engine/chat/`  
**Planned file:** `digitz_ai_nexus/engine/chat/chat_agent_loop.py`

---

## 1. The Problem With the Current System

The existing chat pipeline uses two sequential LLM calls:

```
User message
    │
    ▼ LLM Call #1 — route_intent()
    │  Determines: "ROUTE_TO_KNOWLEDGE" or conversational answer
    │
    ├── If conversational: return LLM #1's answer directly
    │
    └── If ROUTE_TO_KNOWLEDGE:
            ▼ retrieve_allowed_chunks()
              (access_resolver → filter by allowed_access_policies → vector search)
            ▼ LLM Call #2 — generate_answer()
            ▼ Return answer
```

This is a solid single-topic pipeline. It breaks down in specific cases:

| Scenario | Problem |
|---|---|
| Question spans two topics | Single vector search retrieves chunks for one topic only |
| Follow-up needs different source | Router already committed to one retrieval path |
| "Summarise X and compare with Y" | Only X's chunks retrieved, Y's policy ignored |
| Question is factual + conversational | Two round-trips, but the router answer is thrown away |
| Router uncertain about whether to retrieve | Retrieves anyway (fail-safe), causing noise |

The current dual-call design also wastes the router's answer. On conversational turns, LLM #1 produces a good reply — but if it also routes, that reply is discarded and LLM #2 starts fresh.

---

## 2. What the Chat Agent Loop Does Differently

Instead of a fixed pipeline (route then retrieve then answer), the LLM is given tools and decides its own retrieval strategy:

```
User message
    │
    ▼ LLM Call #1
      System: knowledge tools + access constraints + persona
      Tools available:
        - search_knowledge(query, topic_hint)   ← retrieves and filters
        - request_escalation(reason)            ← hands off to human
        - answer_complete(answer_text)          ← signals done
    │
    ├── finish_reason="tool_calls" → execute tool(s), append result, loop
    │
    └── finish_reason="stop" → answer is in message.content
```

For a single-topic query, the LLM calls `search_knowledge` once, receives chunks, then responds — exactly 2 LLM calls, same as today. For a multi-concept query, it calls `search_knowledge` twice with different queries, each scoped to the permitted chunks, then synthesises — 3 LLM calls, but a substantially better answer.

---

## 3. Access Governance — The Non-Negotiable Constraint

**The access policy list must be resolved before the loop starts. The LLM cannot see, modify, or bypass it.**

Current path:
```python
allowed_access_policies = access_resolver.resolve(visitor, tenant)
chunks = retrieve_allowed_chunks(query, allowed_access_policies)
```

In the tool loop, the same resolution happens before entering the loop, and the resolved list is bound inside the tool wrapper:

```python
# Before loop — outside LLM control
allowed_policies = access_resolver.resolve(visitor, tenant)

# The tool the LLM calls — only accepts a query string
def search_knowledge(query: str, topic_hint: str = None) -> list[dict]:
    return retrieve_allowed_chunks(query, allowed_policies, topic_hint=topic_hint)
    #                                      ^^^^^^^^^^^^^^^ bound closure — LLM can't touch it
```

The LLM sees the tool signature:
```json
{
  "name": "search_knowledge",
  "parameters": {
    "query": "string",
    "topic_hint": "string (optional)"
  }
}
```

It cannot pass an `access_policies` parameter because the schema does not define one. The implementation ignores any extra fields. The resolved policy list is an immutable closure around the tool function.

**What the LLM controls:** the search query text and optional topic hint.  
**What the LLM does not control:** which knowledge bases it can search, which chunks are returned, which contacts are suppressed.

---

## 4. The Three Tools

### 4.1 `search_knowledge`

Wraps the existing `retrieve_allowed_chunks()` function. The LLM provides a natural-language query; the tool runs vector search restricted to the pre-resolved access policies and returns the top-k chunks.

```json
{
  "name": "search_knowledge",
  "description": "Search the permitted knowledge base for information relevant to the user's question. You may call this multiple times for different aspects of a complex question.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query — rephrase the user's question as a clear retrieval query"
      },
      "topic_hint": {
        "type": "string",
        "description": "Optional topic area to narrow the search (e.g. 'pricing', 'returns policy')"
      }
    },
    "required": ["query"]
  }
}
```

The tool returns a list of chunk dicts:
```json
[
  {"content": "...", "source": "KB-0012", "confidence": 0.87},
  ...
]
```

If no permitted chunks exist (`allowed_policies` is empty), the tool returns `[]` and the LLM must acknowledge it cannot answer from knowledge.

### 4.2 `request_escalation`

Replaces the current escalation state machine call inside the pipeline. The LLM calls this when it cannot find a satisfactory answer or recognises the query needs a human agent.

```json
{
  "name": "request_escalation",
  "description": "Request escalation to a human agent when you cannot answer from available knowledge or the user is expressing frustration/urgency. This ends the current turn.",
  "parameters": {
    "type": "object",
    "properties": {
      "reason": {
        "type": "string",
        "enum": ["no_knowledge_match", "complex_query", "user_request", "sentiment_trigger"],
        "description": "Why escalation is being requested"
      },
      "summary": {
        "type": "string",
        "description": "One-sentence summary of the user's issue for the human agent"
      }
    },
    "required": ["reason"]
  }
}
```

Calling `request_escalation` is a terminal tool — the loop exits with `status=escalated` regardless of `finish_reason`.

### 4.3 `answer_complete` (optional)

Allows the LLM to signal completion without relying on `finish_reason="stop"`. Useful for multi-call sequences where the LLM retrieves in iteration 1 and wants to explicitly close in iteration 2.

In practice, `finish_reason="stop"` handles this naturally. The tool is available but not required.

---

## 5. Latency Analysis

Counter-intuitively, the tool loop is not slower than the current pipeline for the common case:

| Scenario | Current pipeline | Tool loop |
|---|---|---|
| Conversational turn | 1 LLM call (router sees no retrieval needed, returns directly) | 1 LLM call (LLM responds directly without calling tools) |
| Single-topic knowledge query | 2 LLM calls (router + answer) | 2 LLM calls (initial + after search) |
| Multi-concept query | 2 LLM calls (only one topic retrieved, poor answer) | 3 LLM calls (two searches + synthesis) — intentionally more, for a correct answer |
| Sentiment/escalation trigger | 2 LLM calls (router identifies intent → escalation path) | 1 LLM call (LLM calls `request_escalation` directly) |

**The tool loop is faster for conversational turns** because the current router call is wasted overhead when no retrieval is needed. On knowledge queries the call count is the same. Multi-concept queries cost one extra call — this is correct behaviour, not overhead.

Chunk retrieval latency (vector search) is identical because the tool wraps the same `retrieve_allowed_chunks()` function.

---

## 6. What Does Not Change

The following are unchanged and reused without modification:

| Component | Location | Status |
|---|---|---|
| `access_resolver.resolve()` | `engine/access_resolver.py` | Unchanged |
| `retrieve_allowed_chunks()` | `engine/retrieval.py` | Unchanged — called inside tool wrapper |
| Chunk-level filters (suppression, sensitivity) | `engine/retrieval.py` | Unchanged |
| Escalation state machine | `engine/escalation.py` | Called by `request_escalation` tool handler |
| `Nexus Session` state | DocType | Unchanged |
| `Nexus Chat Message` storage | DocType | Unchanged |
| Knowledge Profile access policies | DocType | Unchanged |
| Tenant and visitor isolation | `access_resolver.py` | Unchanged |

The tool loop is an additive path, not a replacement. The existing `route_intent()` + `generate_answer()` pipeline remains intact.

---

## 7. When to Use Which Path

The chat API or session handler picks the path based on a flag on the `Nexus Knowledge Profile` or `Nexus Session`:

| Flag | Path | Suitable for |
|---|---|---|
| `chat_mode = "rag"` (default) | Current pipeline | Simple single-topic Q&A, fast responses, well-defined knowledge domains |
| `chat_mode = "agent_loop"` | Tool loop | Complex queries, multi-concept synthesis, tenants with multiple knowledge domains |

The paths are not mutually exclusive. A tenant can have `chat_mode = "agent_loop"` configured on one session type and `rag` on another. No data migration needed.

---

## 8. Conversation History

The current pipeline does not maintain multi-turn conversation history — each message is handled independently. The tool loop naturally supports it because the message list carries prior turns:

```python
messages = [
    {"role": "system",    "content": system_prompt},
    {"role": "user",      "content": "What's your returns policy?"},
    {"role": "assistant", "content": "Returns are accepted within 30 days..."},
    {"role": "user",      "content": "What about electronics?"},  ← current turn
]
```

The LLM receives prior turns and can answer follow-ups without the user repeating context. The last N turns (suggested: 10) are included to prevent token bloat.

Message history is loaded from `Nexus Chat Message` records for the active session, filtered by `session_name`, ordered by `creation`.

---

## 9. System Prompt

The chat agent loop system prompt is simpler than the agentic loop because it has no approval requirements:

```
You are {persona_name}, a helpful assistant for {tenant_name}.
Answer questions accurately using the search_knowledge tool when needed.
If you cannot find relevant information after searching, say so clearly — do not guess.
If the user needs help beyond what you can provide, use request_escalation.
Keep answers concise and relevant.

Access constraint: You may only retrieve and cite information from the knowledge base.
Do not state facts not supported by a search_knowledge result.
```

The persona name and tenant name come from `Nexus Session` and `Nexus Tenant` respectively.

---

## 10. Implementation Plan

### Phase 1 — Tool wrapper and loop

**New file:** `digitz_ai_nexus/engine/chat/chat_agent_loop.py`

```python
def run_chat_agent_loop(
    user_message: str,
    session_name: str,
    visitor,
    tenant: str,
    history: list[dict]  # last N turns from Nexus Chat Message
) -> dict:
    # 1. Resolve access — before anything LLM-related
    allowed_policies = access_resolver.resolve(visitor, tenant)

    # 2. Build tools with policy closure
    tools = _build_tools(allowed_policies, tenant)

    # 3. Build messages
    messages = history + [{"role": "user", "content": user_message}]

    # 4. Loop (max 5 iterations for chat — much lower than agentic)
    for _ in range(MAX_CHAT_ITERATIONS):
        response = client.chat.completions.create(model=..., messages=messages, tools=tools)
        choice = response.choices[0]

        if choice.finish_reason == "stop":
            return {"status": "answered", "answer": choice.message.content}

        if choice.finish_reason == "tool_calls":
            messages.append(_serialise_assistant_message(choice.message))
            for tc in choice.message.tool_calls:
                result, is_terminal = _execute_chat_tool(tc, session_name, tenant)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
                if is_terminal:
                    return {"status": "escalated", "reason": result.get("reason")}

    return {"status": "no_answer", "answer": "I wasn't able to find a complete answer. Would you like to speak with a team member?"}
```

`MAX_CHAT_ITERATIONS = 5` — chat sessions are short-lived; the agentic 25-iteration limit does not apply.

### Phase 2 — Session handler switch

In the existing `chat_api.py` or `session_handler.py`:

```python
profile = frappe.get_cached_doc("Nexus Knowledge Profile", session.knowledge_profile)
if profile.chat_mode == "agent_loop":
    from digitz_ai_nexus.engine.chat.chat_agent_loop import run_chat_agent_loop
    result = run_chat_agent_loop(user_message, session.name, visitor, tenant, history)
else:
    result = _rag_pipeline(user_message, visitor, tenant)  # existing path
```

### Phase 3 — Knowledge Profile field

Add `chat_mode` Select field to `Nexus Knowledge Profile`:
- Options: `rag` (default) / `agent_loop`

No schema change to `Nexus Chat Message` or `Nexus Session`.

---

## 11. What Improves

| Problem (§1) | How the tool loop fixes it |
|---|---|
| Single-topic constraint | LLM calls `search_knowledge` twice for different topics |
| Router answer wasted | No router — LLM answers directly on conversational turns |
| Router uncertainty | Removed — LLM decides whether to search based on the question |
| Multi-concept synthesis | LLM aggregates results from two searches before answering |
| Escalation delay | LLM calls `request_escalation` in 1 call instead of 2 |

---

## 12. What Does Not Improve

| Limitation | Why |
|---|---|
| Vector search quality | Not changed — same embedding model, same index |
| Knowledge base gaps | Tool loop cannot retrieve what isn't indexed |
| Per-chunk access policy | Unchanged — same chunk-level filter in `retrieve_allowed_chunks()` |
| Response latency on simple queries | Same 2 LLM calls as current for single-topic queries |

The tool loop makes the retrieval strategy smarter. It does not make the retrieval engine faster or more knowledgeable.

---

## 13. Relationship to Agentic Loop

The chat agent loop (`chat_agent_loop.py`) is a separate, simpler implementation from the agentic loop (`agent_loop.py`). They share the same OpenAI tool-calling protocol but differ on:

| Dimension | Agentic loop | Chat agent loop |
|---|---|---|
| Approval gates | Yes — `create_approval_request` pauses run | No — read-only tools only |
| Conversation persistence | Across days/approval cycles | Within a session only |
| Max iterations | 25 | 5 |
| Tools | Domain tools + built-ins | `search_knowledge`, `request_escalation`, `answer_complete` |
| Background execution | Yes — Frappe queue | No — synchronous, in the web request |
| DocType writes | Nexus Agent Run, Tool Call, Decision Log | Nexus Chat Message only |
| System prompt source | Candidate Profile (behaviour + strategy + do-not-do) | Knowledge Profile (persona + tenant context) |

They do not share code. The agentic loop is not a dependency of the chat loop.
