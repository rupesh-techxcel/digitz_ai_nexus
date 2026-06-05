# Tenant and Tenant Configuration

Nexus Administration is intentionally simple:

```text
Nexus Tenant
    -> Tenant Configuration
        -> default business unit, public context, channels, safety flags, widget defaults
```

`Nexus Tenant` is the isolation boundary. Use one tenant for each customer, website, internal platform, or environment that must keep knowledge and query logs separate.

Tenant configuration stores only tenant-wide defaults used when a runtime request does not pass those values explicitly. It is not a routing mechanism. Routing for chat, Q&A, API, and future channels must resolve through:

```text
Chat Category -> Identity -> AI Agent Profile -> Access Category -> Access Policy
```

## Tenant Configuration Fields

Keep tenant configuration bare minimum:

| Field | Purpose |
|---|---|
| Default Business Unit | Tenant-wide business unit scope |
| Default Public Context | Tenant-wide public context scope |
| Default Top K | Retrieval count default |
| Q&A Enabled | Enables Q&A for the tenant |
| Default Q&A Channel | Q&A channel when no explicit Q&A channel is passed |
| Live Chat Enabled | Enables chat for the tenant |
| Default Chat Channel | Chat channel when no explicit chat channel is passed |
| Require Approved Knowledge | Uses only approved knowledge |
| Strict Tenant Mode | Keeps runtime scoped to the tenant |
| Source Citation Required | Requests grounded answers with citations |
| Widget Settings | Public website widget defaults |
| Q&A Fallback Message | Safe no-answer text |

Channel defaults are purpose-aware and do not cross-fallback. Chat uses only the tenant default chat channel, and Q&A uses only the tenant default Q&A channel.

## Admin Page

The Nexus Admin page is now only:

- Tenant selection
- Tenant configuration
- Tenant readiness summary

It does not manage user context, runtime context, knowledge authoring, access policy assignment, business keyword tuning, or validation. Those belong to their own runtime, Studio, governance, or validation flows.

## Persistence

Persist:

- Real tenants
- Real business units and public contexts
- Tenant configuration for real runtime behavior

Remove after validation:

- Synthetic tenants such as `TEST-NEXUS`
- Synthetic master values
- Synthetic Live channels, agents, knowledge, and test data

Implementation note: older code still stores tenant configuration in the existing `Nexus Ecosystem` DocType for compatibility. Treat that DocType as internal storage until a dedicated schema migration moves these fields onto a tenant configuration DocType or the tenant itself.
