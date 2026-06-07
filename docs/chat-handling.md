# Chat Handling — End-to-End Flow

This document describes exactly what happens when a user sends a message in chat mode (`response_mode = "chat"` or `"live chat"`). It covers every decision point, every LLM call, and every exit path, in the order they occur.

The entry point is `services/answer_service.py` → `answer_query()`.

---

## The Story

### Step 1 — Message arrives

The chat widget submits a message. The payload reaching `answer_query()` contains at minimum:

| Field | Purpose |
|---|---|
| `query` | The raw user message |
| `original_query` | Same as query in most cases; preserved for display |
| `response_mode` | `"chat"` or `"live chat"` — triggers chat-specific behaviour |
| `conversation_context` | Prior turns, formatted as a text block |
| `resolved_intents` | List of configured Intent Handlers for this AI Agent Profile |
| `ai_profile` | Tone, behaviour prompt, fallback message, do-not-answer rules |
| `allowed_access_policies` | Pre-resolved list of access policies the user is permitted to query |

---

### Step 2 — Length guard

Before any LLM call, the query length is checked.

```
len(query.strip()) > 500 characters?
    YES → handle_query_too_long()
            LLM generates a friendly nudge asking the user to shorten the question.
            Response returned immediately. Pipeline stops here.
    NO  → continue
```

This prevents oversized inputs from reaching the router or the RAG pipeline.

---

### Step 3 — Intent Router (first LLM call)

`route_intent()` makes the **first and only guaranteed LLM call** in every chat turn.

**What the LLM receives:**

```
You are the Nexus Conversation Router — the first contact point in this enterprise chat assistant.

PURPOSE:
Decide whether this message is a casual conversational exchange, matches a special case,
or requires a knowledge lookup.

SPECIAL CASES (evaluate BEFORE routing rules, in priority order):
[1] <intent_name>
    Trigger: <trigger_description>
    If matched: respond with exactly: ACTION:PREDEFINED:<name>
          — or —
    If matched: respond with exactly: ACTION:ESCALATE

UNAVAILABLE:
- <intent_name>
  If matched: respond with exactly: ACTION:DECLINED:<name>

ROUTING RULES:
1. Check special cases first. If matched, return the exact action token.
2. Greeting / farewell / small talk → respond naturally in 1-2 sentences.
3. Any topic, product, policy, procedure, price, or feature → ROUTE_TO_KNOWLEDGE
4. Uncertain → ROUTE_TO_KNOWLEDGE
5. Never generate factual information.

CONVERSATION SO FAR:
<prior turns>

USER MESSAGE:
<query>
```

**What the LLM returns — and what happens next:**

---

#### Exit A — Conversational response

The LLM returns a short, natural sentence (e.g. "Hello! How can I help you today?").

```python
{
    "access_status": "conversational",
    "answer": "<LLM response>",
    "confidence": 1.0,
    "fallback_used": 0,
}
```

No RAG. No second LLM call. Done.

This covers: greetings, farewells, thank-you messages, short social exchanges. The LLM is permitted to generate these freely because no factual claim is being made.

---

#### Exit B — ACTION:ESCALATE

The LLM matched an escalation intent (e.g. "I want to speak to someone").

The response template configured on that Intent Handler is returned directly. No LLM generation.

```python
{
    "access_status": "intent_handled",
    "answer": "<configured response_template>",
    "confidence": 1.0,
    "user_requested_human": True,
    "intent_action": "escalate",
    "fallback_used": 0,
}
```

`user_requested_human: True` is the signal read by `live_chat_service` to hand the conversation to a human agent.

---

#### Exit C — ACTION:PREDEFINED:\<name\>

The LLM matched a predefined answer intent (e.g. "What are your opening hours?").

The response template configured on that Intent Handler is returned directly. No LLM generation, no RAG.

```python
{
    "access_status": "intent_handled",
    "answer": "<configured response_template>",
    "confidence": 1.0,
    "intent_action": "predefined",
    "fallback_used": 0,
}
```

This is how known, repeated questions are handled without hitting the knowledge base every time.

---

#### Exit D — ACTION:DECLINED:\<name\>

The LLM matched an intent that is configured but marked inactive for this profile (e.g. "What is the price?" where pricing is turned off).

The decline response configured on that Intent Handler is returned directly.

```python
{
    "access_status": "intent_handled",
    "answer": "<configured decline_response>",
    "confidence": 1.0,
    "intent_action": "declined",
    "fallback_used": 0,
}
```

The user is told gracefully that this topic is not available through this assistant.

---

#### Continue — ROUTE_TO_KNOWLEDGE

The LLM returns exactly `ROUTE_TO_KNOWLEDGE` (or an empty/unrecognised response). This means the message is knowledge-seeking and cannot be answered conversationally.

The pipeline continues to the RAG stage.

---

### Step 4 — Access policy guard

Before retrieval begins, the system checks `allowed_access_policies`.

If the list was resolved but came back empty, retrieval is blocked with a hard error. An empty list is never treated as "allow everything" — it means policy resolution failed and the system fails closed.

---

### Step 5 — RAG retrieval

`retrieve_allowed_chunks()` in `engine/retrieval.py` is called.

Retrieval runs the full hybrid pipeline: query expansion, semantic and keyword scoring, question-first narrowing (if applicable), context summary signals, re-ranking, and scope balancing. The full details are in [retrieval-and-answer.md](retrieval-and-answer.md).

The result is one of three outcomes:

| Outcome | What happens |
|---|---|
| `access_status: restricted` | Knowledge exists but the user has no access. Return `restricted` response immediately. |
| No chunks found | Go to fallback (Step 6). |
| Chunks found | Continue to confidence check (Step 7). |

---

### Step 6 — Fallback (no usable knowledge)

This exit is reached when:
- No chunks were retrieved, or
- Confidence fell below the minimum threshold (default 0.20, configurable in Nexus Settings), or
- The RAG LLM call returned empty or the exact safe fallback phrase.

**There is no second LLM call here.** The fallback message is returned directly.

```python
answer = (
    ai_profile.get("fallback_message")          # configured on the AI Agent Profile
    or payload.get("agent_fallback_message")     # legacy flat field
    or "I don't currently have confirmed information on that topic."
)
```

```python
{
    "access_status": "no_context",
    "answer": "<fallback_message>",
    "confidence": 0.0,
    "fallback_used": 1,
}
```

**Why no LLM here:** When the knowledge base has no information on a topic, asking the LLM to generate a "warm" response risks producing clarifying questions that imply the system might know something more specific — which it does not. The fallback must be honest and final. A more specific follow-up question from the user will go through the same pipeline and reach the same conclusion.

The `fallback_used: 1` flag is preserved so the escalation signal can still fire on the caller side if configured.

---

### Step 7 — Confidence check and question-first retry

After retrieval returns chunks, their scores are combined into a single confidence value:

```python
confidence = (top_score * 0.7) + (avg_score * 0.3)
```

If confidence is below the minimum threshold:

- **And** question-first narrowing was applied: retry retrieval with `disable_question_first = 1` (broader search). If the retry produces chunks above threshold, continue. Otherwise, go to fallback (Step 6).
- **And** question-first was not applied: go to fallback (Step 6) directly.

This retry exists because question-first narrowing can over-constrain the candidate set. Retrying without it gives the broader content index a chance to surface a relevant chunk.

---

### Step 8 — Answer generation (second LLM call)

If chunks passed the confidence check, `build_prompt()` assembles the full prompt and `generate_answer()` calls the LLM.

**What the LLM receives:**

```
You are DIGITZ AI Nexus, a controlled enterprise knowledge assistant.

CORE RULES:
1. Answer ONLY using the approved knowledge provided below.
2. Do NOT guess, invent, or add outside knowledge.
3. Do NOT expose restricted or hidden information.
4. Preserve exact named labels, policies, codes, and identifiers from the knowledge.
5. If approved knowledge is insufficient, answer exactly: "<safe_fallback>"

RESPONSE BEHAVIOR:
Mode: Chat
Tone: <profile tone or mode default>

AGENT BEHAVIOUR: (if configured on profile)
...

DO NOT ANSWER RULES: (if configured on profile)
...

CONVERSATION CONTEXT:
<prior turns>

CONVERSATION CONTEXT RULES:
1. Use context only to understand follow-up.
2. Do NOT treat conversation context as approved factual knowledge.
3. Final answer must come only from APPROVED KNOWLEDGE.

CHAT RESPONSE RULES:
1. Keep the answer conversational and natural.
2. Limit to a maximum of <N> sentences.
3. If approved knowledge is insufficient, answer exactly: "<safe_fallback>"

APPROVED KNOWLEDGE:
[Source 1]
Chunk ID: ...
Context Path: ...
Knowledge:
<chunk_text>

[Source 2]
...

CURRENT USER MESSAGE:
<original_query>

RETRIEVAL QUERY USED:
<query>

FOLLOW-UP DETECTED:
True / False

ANSWER:
```

The LLM answers strictly from the approved knowledge blocks. It may not use the conversation context as a factual source — only as context for interpreting follow-up questions.

**If the LLM response is empty or matches the safe fallback phrase exactly:** go to fallback (Step 6). This is the final safety net.

---

### Step 9 — Response returned

```python
{
    "status": "success",
    "access_status": "allowed",
    "answer": "<grounded answer>",
    "confidence": 0.72,
    "sources": [...],           # chunk-level source records with scores
    "citations": [...],         # summary citation list
    "retrieval_result": {...},  # full retrieval diagnostics
    "fallback_used": 0,
}
```

---

## Decision Map

```
User message
    │
    ▼
Length > 500 chars? ──YES──► nudge to shorten (LLM) → DONE
    │
    NO
    ▼
Intent Router (LLM call #1)
    │
    ├── Conversational ──────────────────────────────► 1-2 sentence reply → DONE
    ├── ACTION:ESCALATE ─────────────────────────────► configured template, human handoff → DONE
    ├── ACTION:PREDEFINED:<name> ────────────────────► configured template → DONE
    ├── ACTION:DECLINED:<name> ──────────────────────► decline message → DONE
    └── ROUTE_TO_KNOWLEDGE
            │
            ▼
        Access policy guard
            │
            ▼
        RAG retrieval
            │
            ├── restricted ──────────────────────────► "You do not have permission..." → DONE
            ├── no chunks ───────────────────────────► fallback message → DONE
            └── chunks found
                    │
                    ▼
                Confidence check
                    │
                    ├── below threshold
                    │       ├── question-first applied? ──YES──► retry broad retrieval
                    │       │                                        │
                    │       │                            still low? ─┤
                    │       │                                        └──► fallback → DONE
                    │       └── no question-first ────────────────► fallback → DONE
                    │
                    └── above threshold
                            │
                            ▼
                        LLM answer generation (LLM call #2)
                            │
                            ├── empty or safe fallback phrase ────► fallback → DONE
                            └── grounded answer
                                    │
                                    ▼
                                Return answer with sources → DONE
```

---

## Key Design Principles

**The router never states facts.** Its only job is to classify intent and return a token or a social acknowledgement. All factual grounding happens in the RAG stage.

**The fallback never uses the LLM.** When no knowledge exists, an LLM call would risk generating clarifying questions that imply the system might know something more specific. It does not. The fallback message is returned directly — either the one configured on the AI Agent Profile, or the system default.

**Conversation context is not a knowledge source.** Prior turns are injected so the LLM can understand follow-up phrasing, but the prompt explicitly prevents treating them as approved facts. Every factual answer must come from the retrieved chunks in that turn.

**Confidence gates access, not retrieval.** The system retrieves broadly and then decides whether the result is trustworthy enough to send to the LLM. Below-threshold results go straight to fallback — they are not passed to the LLM to "interpret" at lower confidence.

**Escalation is never LLM-generated in-flight.** The response the user sees when escalating is the template configured by the administrator. There is no risk of the LLM deviating from the intended escalation message.

---

## Files

| File | Role |
|---|---|
| `services/answer_service.py` | Orchestrator — `answer_query()`, `route_intent()`, `handle_host_fallback()` |
| `engine/prompt.py` | Prompt builders — `build_router_prompt()`, `build_prompt()`, `build_query_too_long_prompt()` |
| `engine/retrieval.py` | RAG retrieval pipeline |
| `engine/llm.py` | LLM call wrapper — `generate_answer()` |
| `engine/response_mode.py` | Mode-specific tone and instruction templates |
