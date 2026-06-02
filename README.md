# DIGITZ AI Nexus

**Governed AI core for the DIGITZ AI platform** — built on [Frappe Framework](https://frappeframework.com).

This app is the AI brain of the platform. It owns knowledge management, access governance, retrieval, prompt construction, and answer generation. It is **not** a standalone chatbot — it is the core engine that powers the broader DIGITZ AI app family.

---

## App Family

The platform is split across three apps with isolated responsibilities:

| App | Role |
|---|---|
| `digitz_ai_nexus` | AI core: knowledge, access governance, retrieval, answer engine |
| `digitz_ai_nexus_live` | Live conversation runtime: chat, escalation, human handover |
| `digitz_ai_experience` | User-facing layer: website widgets, public chat, embed scripts |

---

## What This App Does

`digitz_ai_nexus` is responsible for:

- **Knowledge lifecycle** — ingest, chunk, embed, and manage knowledge sources
- **Access governance** — classify knowledge with policies and resolve who can access what
- **Retrieval engine** — fetch access-safe knowledge chunks relevant to a query
- **Answer service** — orchestrate retrieval, prompt building, LLM call, and response packaging
- **Query logging** — trace every query for governance and debugging

---

## Key Concepts

### Knowledge

Knowledge flows through three layers:

```
Nexus Knowledge Source  →  Nexus Knowledge Unit  →  Nexus Knowledge Chunk
```

Access policy is set at the source and propagates down to chunks. Retrieval filters at the chunk level.

### Access Governance

Access is category-based, not direct role-to-policy:

```
Role → Access Category → Access Policy → Knowledge Chunks
```

- **Nexus Access Policy** — classifies knowledge (e.g. `Finance`, `HR`, `Public`)
- **Nexus Access Category** — groups policies into reusable bundles
- **Nexus Role Access Category** — maps a Frappe role to an access category
- **Nexus Channel Access Category** — applies a guardrail per channel

Final allowed policies are always the intersection of profile scope, role scope, and channel guardrail:

```
final_allowed_policies = profile ∩ role ∩ channel
```

Public endpoints always force `Public`-only, regardless of other configuration.

### AI Agent Profile

`Nexus AI Agent Profile` is the runtime AI responder configuration. It controls tone, response style, behaviour prompt, fallback message, confidence threshold, escalation settings, and knowledge scope intent.

Profiles are resolved dynamically per request via `Nexus Channel AI Profile Route` — a channel can serve many profiles.

---

## Important DocTypes

| DocType | Purpose |
|---|---|
| Nexus Knowledge Source | Top-level knowledge entry point |
| Nexus Knowledge Unit | Parsed unit within a source |
| Nexus Knowledge Chunk | Smallest retrievable unit; carries access policy |
| Nexus Access Policy | Knowledge classification label |
| Nexus Access Category | Reusable group of access policies |
| Nexus Access Category Policy | Maps category ↔ policy |
| Nexus Role Access Category | Maps Frappe role → access category |
| Nexus Channel Access Category | Maps channel → access category (guardrail) |
| Nexus Query Log | Audit trail for every query |

---

## Installation

```bash
bench get-app digitz_ai_nexus
bench --site your-site.local install-app digitz_ai_nexus
bench --site your-site.local migrate
```

Requires Frappe Framework v15+.

---

## Development

```bash
# After DocType changes
bench --site digitz_ai_nexus.site migrate
bench --site digitz_ai_nexus.site clear-cache
```

See [`digitz_ai_nexus/ai_nexus_architecture_context.md`](digitz_ai_nexus/ai_nexus_architecture_context.md) for full architecture and design rules.

---

## License

See [license.txt](license.txt). Built by [Techxcel Technologies](mailto:info@techxceltech.com).
