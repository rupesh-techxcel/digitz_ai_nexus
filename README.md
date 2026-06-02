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

- **Knowledge lifecycle** — ingest, chunk, embed, and manage knowledge sources (PDF, DOCX, TXT, manual)
- **Access governance** — classify knowledge with policies and resolve who can access what
- **Retrieval engine** — hybrid vector + keyword search with re-ranking and scope balancing
- **Answer service** — orchestrate retrieval, prompt building, LLM call, and response packaging
- **Query logging** — trace every query for governance and debugging

---

## Key Concepts

### Knowledge

Knowledge flows through three layers:

```
Nexus Knowledge Source  →  Nexus Knowledge Unit  →  Nexus Knowledge Chunk
```

Access policy is set at the source and propagates down to chunks. Retrieval filters at the **chunk level**.

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

Public endpoints always force `["Public"]`, regardless of other configuration.

### Retrieval

Queries are scored with a hybrid algorithm:

```
hybrid_score = (vector × 0.75) + (keyword × 0.20) + (priority × 0.05)
```

Query expansion, re-ranking, and scope balancing are all configurable via `Nexus Settings`.

### Security

The system **fails closed**. An empty `allowed_access_policies` list immediately denies retrieval. Restricted knowledge (exists but access denied) returns a distinct response from "no context found".

---

## Documentation

| Document | Contents |
|---|---|
| [Architecture](docs/architecture.md) | App family, system data flow, security model, multi-tenancy, design principles |
| [Knowledge Lifecycle](docs/knowledge-lifecycle.md) | Ingestion pipeline, chunking, deduplication, source/unit/chunk model |
| [Access Governance](docs/access-governance.md) | Access policies, categories, role/channel mappings, resolver logic |
| [Retrieval and Answer Engine](docs/retrieval-and-answer.md) | Hybrid scoring, re-ranking, prompt builder, LLM provider, response structure |
| [DocType Reference](docs/doctypes.md) | All DocTypes with fields, autoname, and purpose |
| [Configuration](docs/configuration.md) | Nexus Settings, default policies, provider setup, development commands |
| [API Reference](docs/api-reference.md) | All whitelisted endpoints, query contract structure |

---

## Installation

```bash
bench get-app digitz_ai_nexus
bench --site your-site.local install-app digitz_ai_nexus
bench --site your-site.local migrate
```

Requires Frappe Framework v15+.

After install, seven default access policies are created automatically. Configure an OpenAI API key in `Nexus Settings` before processing knowledge sources.

---

## Development

```bash
# After DocType JSON changes
bench --site digitz_ai_nexus.site migrate
bench --site digitz_ai_nexus.site clear-cache

# Run tests (uses fake LLM and embedding providers; no API key needed)
bench --site digitz_ai_nexus.site run-tests --app digitz_ai_nexus
```

---

## License

See [license.txt](license.txt). Built by [Techxcel Technologies](mailto:info@techxceltech.com).
