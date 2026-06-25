# Nexy Companion — Strategy Engine

## Overview

The Nexy Companion Strategy Engine gives the LLM two capabilities it previously lacked:

1. **Strategic awareness** — what to collect before advancing, tracked in real time via discovery progress injection
2. **Off-track detection** — visitor resistance and disengagement signals are now visible to the LLM, with adaptive directives that override the default stage behaviour

Without this engine, Nexy kept repeating the same discovery question even when a visitor had deflected three times. Now it detects the pattern, adapts its approach, and executes a structured re-engagement arc before gracefully closing.

---

## Core Concepts

### Engagement Mode

Every turn, the engine reads the last 5 signals from the enquiry's `signal_log` and classifies the visitor's engagement state:

| Mode | Condition | Behaviour |
|---|---|---|
| **PROGRESSING** | Fewer than 2 resistance signals in last 5 | Default — normal stage directive |
| **RESISTANT** | 2 or 3 resistance signals in last 5 | Pivots to insight-sharing; stops pushing |
| **DISENGAGING** | 4 or 5 resistance signals in last 5 | Activates the re-engagement arc |

**Resistance signals**: `HESITATING`, `DEFLECTING`, `DISENGAGING`, `OBJECTING`

These signals were always being classified and stored — the engine now makes them visible to the LLM and acts on them.

### Stage × Mode Directive Matrix

The flat `_STAGE_FOCUS` dict is replaced by a 2D matrix: every journey stage has **three** directives — one per engagement mode. The LLM receives exactly one directive per turn.

Examples:

| Stage | PROGRESSING | RESISTANT | DISENGAGING |
|---|---|---|---|
| DISCOVERY | Ask one discovery question; priority: industry, company_size, current_challenges, goals | Pivot to insight-sharing; share a pattern you see and invite reaction | Pause discovery; share one compelling outcome for their apparent profile |
| PRESENTING | Present specifically; surface a customer story; invite questions | Ask "What would I need to show you for this to feel like a fit?" — stop presenting | Stop presenting; offer specialist or simpler format |
| CONVERTING | One clear CTA; reduce all friction | Surface last remaining concern; re-introduce CTA after | Offer a lower-commitment option to keep them engaged |

Full matrix covers all 11 stages × 3 modes. See `companion_context_service.py:_STAGE_DIRECTIVES`.

### Discovery Progress

In `DISCOVERY` and `ENGAGED` stages, the LLM prompt includes a structured status block showing exactly what has been collected and what to ask next:

```
DISCOVERY PROGRESS (2 of 10 fields collected):
✓ Priority collected: industry, company_size
○ Priority still needed: current_challenges, goals
→ Ask about: current_challenges (one question this turn)
```

**Priority fields** (minimum required before advancing to `ENGAGED`):
- `industry`
- `company_size`
- `current_challenges`
- `goals`

When all four are collected, the block changes to:
```
DISCOVERY PROGRESS: All priority fields collected — begin connecting their situation to relevant solutions.
```

### Disengagement Re-Engagement Arc

When `engagement_mode = DISENGAGING`, a **3-step arc** overrides the stage directive entirely. The step is determined by counting consecutive resistance signals from the tail of the signal log:

| Turn | Name | What Nexy Does |
|---|---|---|
| **1** | **Acknowledgment Pivot** | Stops current approach. Calmly calls out the disconnect: *"I get the sense this might not be what you were looking for — am I off base? No pressure at all."* Gives the visitor permission to redirect. No agenda. |
| **2** | **Value Flash** | Delivers one specific, compelling insight or outcome relevant to their apparent profile. No ask. No question. No CTA. Gives them something worth staying for. |
| **3+** | **Exit Offer** | Offers a specialist connection or a graceful close. Sets `escalation_recommended = 1` on the enquiry (desk agent sees this flag). No further pitch or discovery attempts. |

The arc step repeats at step 3 if the visitor continues to disengage — `escalation_recommended` is set once and stays.

---

## How It Works — Turn by Turn

```
Visitor sends message
        ↓
signal_classifier.py classifies signal → appended to signal_log
        ↓
update_enquiry() runs:
  • merges discovery delta
  • re-scores enquiry
  • checks consecutive resistance signals → sets escalation_recommended if ≥ 3
  • saves enquiry
        ↓
advance_journey_stage_from_signal() updates stage if needed
        ↓
build_companion_context() runs:
  • reads signal_log from enquiry
  • _compute_engagement_mode(last 5 signals) → PROGRESSING / RESISTANT / DISENGAGING
  • _count_consecutive_disengaging() → disengagement_turn (0 when PROGRESSING)
  • _get_discovery_status() → priority fields collected / missing / next_focus
  • _get_recent_signals() → last 3 signal types for display
  • resolves stage_directive:
      - DISENGAGING → _DISENGAGEMENT_SEQUENCE[min(turn, 3)]
      - RESISTANT   → _STAGE_DIRECTIVES[stage]["RESISTANT"]
      - PROGRESSING → _STAGE_DIRECTIVES[stage]["PROGRESSING"]
        ↓
_build_companion_block() renders companion prompt section:
  • Adds VISITOR ENGAGEMENT + RECENT SIGNALS section (only when off-track)
  • Adds DISCOVERY PROGRESS block (DISCOVERY/ENGAGED stages only)
  • Injects resolved directive as "YOUR DIRECTIVE FOR THIS TURN"
        ↓
LLM receives full prompt → responds with adapted strategy
```

---

## Prompt Sections Added by the Engine

### When PROGRESSING (clean)

No extra sections. The prompt shows only the normal companion context — no engagement warning, clean discovery block when in DISCOVERY stage.

### When RESISTANT

```
VISITOR ENGAGEMENT: RESISTANT
RECENT SIGNALS: SHARING_CONTEXT → HESITATING → DEFLECTING
Standard discovery/presentation approach is NOT working — adapt immediately.
```

Directive changes to the RESISTANT version for the current stage (e.g., insight-sharing instead of questioning).

### When DISENGAGING (turn 1)

```
VISITOR ENGAGEMENT: DISENGAGING  (re-engagement turn 1)
RECENT SIGNALS: DEFLECTING → HESITATING → DISENGAGING
Standard discovery/presentation approach is NOT working — adapt immediately.

YOUR DIRECTIVE FOR THIS TURN:
ACKNOWLEDGMENT PIVOT — The visitor has been consistently deflecting or disengaging.
Stop your current approach entirely. Calmly acknowledge the disconnect: say something
like 'I get the sense this might not be what you were looking for — am I off base?
No pressure at all.' Give them full permission to be honest. Do NOT ask a discovery
question or push any agenda. Let them redirect.
```

### Discovery Progress Block (DISCOVERY stage, early in conversation)

```
DISCOVERY PROGRESS (1 of 10 fields collected):
✓ Priority collected: industry
○ Priority still needed: company_size, current_challenges, goals
→ Ask about: company_size (one question this turn)
```

---

## Files Changed

| File | Change |
|---|---|
| `nexus_companion/services/companion_context_service.py` | Replaced `_STAGE_FOCUS` with `_STAGE_DIRECTIVES` matrix; added `_DISENGAGEMENT_SEQUENCE`, `_RESISTANCE_SIGNALS`, `_PRIORITY_DISCOVERY_FIELDS`, `_ALL_DISCOVERY_FIELDS`; added `_compute_engagement_mode()`, `_count_consecutive_disengaging()`, `_get_discovery_status()`, `_get_recent_signals()`; updated `build_companion_context()` return dict |
| `engine/prompt.py` | Updated `_build_companion_block()` to render engagement mode warning, recent signals, discovery progress block, and mode-aware directive |
| `nexus_companion/services/enquiry_service.py` | Added `_count_consecutive_resistance_signals()` helper; `update_enquiry()` now sets `escalation_recommended = 1` when consecutive resistance signals ≥ 3 |

No DocType schema changes. No new DB fields. No changes to the signal classifier, chat agent loop, or live chat service.

---

## Configuration Notes

### No setup required

The engine activates automatically for all companion-mode conversations. No new fields to configure on the AI Agent Profile, Playbook, or Product DocTypes.

### Tuning engagement mode thresholds

The thresholds (RESISTANT at 2+, DISENGAGING at 4+ out of last 5) are constants in `companion_context_service.py`:

```python
# In _compute_engagement_mode():
if resistance_count >= 4:   # → DISENGAGING
    return "DISENGAGING"
if resistance_count >= 2:   # → RESISTANT
    return "RESISTANT"
return "PROGRESSING"
```

Adjust these if your visitor base tends to be naturally hesitant (lower thresholds) or if false positives are causing premature disengagement detection (raise thresholds).

### Tuning escalation_recommended threshold

The consecutive signal count before `escalation_recommended` is set:

```python
# In enquiry_service.update_enquiry():
if consecutive >= 3 and not enquiry.escalation_recommended:
    enquiry.escalation_recommended = 1
```

---

## Verification

### Flow A — Cooperative visitor (PROGRESSING)

1. Start a fresh companion conversation and share context naturally over 3–4 messages
2. In bench console: `frappe.db.get_value("Nexus Companion Enquiry", "<name>", ["signal_log", "enquiry_stage"], as_dict=True)` — confirm positive signals and stage advancing
3. Confirm "VISITOR ENGAGEMENT" section is absent from the LLM prompt (PROGRESSING = clean)
4. Confirm discovery progress block shows fields filling as visitor shares context

### Flow B — Resistant visitor (RESISTANT mode)

1. Reply with "maybe", "not sure", "I'll think about it" twice in a row
2. Confirm Nexy stops asking discovery questions and shifts to insight-sharing
3. In bench console check signal_log — should show HESITATING or DEFLECTING entries
4. Confirm "VISITOR ENGAGEMENT: RESISTANT" appears in the companion context dict

### Flow C — Disengaging visitor (full re-engagement arc)

1. Deflect 4+ consecutive messages: "not interested", "just browsing", "probably not", "maybe later"
2. **Turn 1 of DISENGAGING**: Nexy should say something like *"I get the sense this might not be what you were looking for — am I off base?"*
3. Continue deflecting: **Turn 2**: Nexy delivers a single value insight with no question or CTA
4. Continue deflecting: **Turn 3+**: Nexy offers specialist connection or graceful close
5. Check enquiry: `frappe.db.get_value("Nexus Companion Enquiry", "<name>", "escalation_recommended")` → should be `1`
6. Confirm `disengagement_turn` increments correctly in the companion context dict

### Bench console inspection

```python
# After a conversation, inspect the context that was built
import json
conv = frappe.get_doc("Nexus Live Conversation", "<conversation_name>")
enq_name = conv.companion_enquiry
signal_log = json.loads(frappe.db.get_value("Nexus Companion Enquiry", enq_name, "signal_log") or "[]")
escalation_rec = frappe.db.get_value("Nexus Companion Enquiry", enq_name, "escalation_recommended")
print("Signals:", [s["signal_type"] for s in signal_log])
print("Escalation recommended:", escalation_rec)
```

---

## Related Documentation

- [Nexy Companion Configuration Guide](nexy-companion-configuration-guide.md) — how to set up the full companion system
- [Nexus Complete Architecture](NEXUS_COMPLETE_ARCHITECTURE.md) — system-wide architecture reference
