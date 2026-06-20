# System Setup Guide

Complete step-by-step guide to bring DIGITZ AI Nexus from a fresh install to a working chat and Q&A system.

---

## Overview

The system must be configured in this order. Each phase depends on the previous one.

```
Phase 1 — Core Settings       API key, LLM, embedding model
Phase 2 — Seed Defaults        Run once to create base records (core + live + agentic)
Phase 3 — Tenant               Tenant + Tenant Configuration
Phase 4 — Access Governance    Policies → Categories → AI Agent Profile
Phase 5 — Live Infrastructure  Website Chat Channel(s) → Chat Categories → Identity Routes → Agent
Phase 6 — Desk User Access     Profile Assignment for internal users
Phase 7 — Knowledge            Source → Chunks → Embeddings → Publish
Phase 8 — Verify               Workflow Tester → Live Console Chat
Phase 9 — Agentic Runtime      (optional) Nexy agent candidate + capability packs
```

---

## Phase 1 — Core Settings

**DocType:** `Nexus Settings` (Single — one record for the whole installation)

Navigate to: **Nexus Settings** in the desk search bar.

| Field | Value | Notes |
|---|---|---|
| LLM Provider | `OpenAI` | |
| LLM Model | `gpt-4o-mini` | Default; change to `gpt-4o` for higher quality |
| API Key | `sk-...` | Your OpenAI API key |
| Embedding Provider | `OpenAI` | |
| Embedding Model | `text-embedding-3-small` | |
| Chunk Size | `800` | Characters per chunk |
| Chunk Overlap | `120` | Overlap between consecutive chunks |
| Top K | `5` | Chunks passed to the LLM per query |
| Minimum Confidence | `0.20` | Below this score returns fallback answer |
| Enable Multi Query | ✓ | Expands query into variants for better recall |
| Enable Reranking | ✓ | Re-ranks candidates for precision |

Save.

---

## Phase 2 — Seed Defaults

Run the seed commands once. Each is idempotent — safe to re-run.

```bash
bench --site digitz_ai_nexus.site execute digitz_ai_nexus.setup.install.seed_defaults
bench --site digitz_ai_nexus.site execute digitz_ai_nexus_live.setup.install.seed_defaults
bench --site digitz_ai_nexus.site execute digitz_ai_nexus_agentic.setup.install.after_install
```

The third command seeds the agentic runtime: Nexy agent candidate, default safety profile (9 do-not-do rules), Sales capability pack, 18 goal types, and 27 registered tools. Skip this if `digitz_ai_nexus_agentic` is not installed.

**What gets created:**

| Record | DocType | Name |
|---|---|---|
| Default tenant | Nexus Tenant | `DIGITZ-NEXUS` |
| Default business unit | Nexus Business Unit | `Default` |
| Default public context | Nexus Public Context | `Website Chat` |
| Tenant configuration | Nexus Tenant Configuration | `Default Live` |
| Public access policy | Nexus Access Policy | `Public` |
| Access categories | Nexus Access Category | `Public Access`, `Internal Access`, `Restricted Access` |
| Website chat channel | Nexus Live Channel | `WEBSITE-CHAT` |
| Default chat category | Nexus Chat Category | `GENERAL-SUPPORT` |
| Identity types | Nexus Identity Type | Public, Customer, Prospect, Partner, Internal, Admin |
| Default AI agent | Nexus Live Agent | `PUBLIC-AI-ASSISTANT` |
| Default AI profile | Nexus AI Agent Profile | linked to `PUBLIC-AI-ASSISTANT` |
| Default route | Nexus Category Identity Route | `WEBSITE-CHAT + GENERAL-SUPPORT + Public → PUBLIC-AI-ASSISTANT profile` |

---

## Phase 3 — Tenant

### 3.1 Verify the tenant exists

Navigate to: **Nexus Tenant** list → confirm `DIGITZ-NEXUS` exists and is not disabled.

To create a new tenant (optional):

| Field | Value |
|---|---|
| Tenant Name | `DIGITZ AI Nexus` |
| Tenant Code | `DIGITZ-NEXUS` |
| Disabled | unchecked |

### 3.2 Verify Tenant Configuration

Navigate to: **Nexus Administration** page → select the tenant.

The **Tenant Configuration** section must have:

| Field | Value |
|---|---|
| Default Chat Channel | `WEBSITE-CHAT` |
| Default Q&A Channel | `WEBSITE-CHAT` |
| Live Chat Enabled | ✓ |
| Q&A Enabled | ✓ |
| Default Top K | `5` |

Click **Save Tenant Configuration**.

---

## Phase 4 — Access Governance

### 4.1 Access Policies

Navigate to: **Nexus Access Policy** list.

The seed creates these. Verify they exist and none are disabled:

| Policy Name | Purpose |
|---|---|
| `Public` | Public knowledge — **must always exist** |
| `Internal` | Internal staff knowledge |
| `Restricted` | Restricted knowledge |

To create a custom policy: New → set `policy_name`, save.

### 4.2 Access Categories

Navigate to: **Nexus Access Category** list.

Each category is a named bundle of policies. Verify:

| Category | Contains Policies |
|---|---|
| `Public Access` | `Public` |
| `Internal Access` | `Public`, `Internal` |
| `Restricted Access` | `Public`, `Internal`, `Restricted` |

To create a new category: New → add policy rows in the **Allowed Policies** child table → save.

### 4.3 AI Agent Profile

Navigate to: **Nexus AI Agent Profile** list.

The seed creates one profile linked to `PUBLIC-AI-ASSISTANT`. Open it and verify:

| Field | Value |
|---|---|
| Agent | `PUBLIC-AI-ASSISTANT` |
| Default Response Mode | `chat` |
| Confidence Threshold | `0.65` |
| Escalation Enabled | as needed |
| Fallback Message | `I do not have enough approved knowledge to answer this.` |

**Smart Fallback & Email Follow-up fields** (below Fallback Message):

| Field | Default | Description |
|---|---|---|
| **Fallback Topic** | *(blank)* | Short domain label included in the fallback message, e.g. `"Nexus AI platform configuration"`. When set, the visitor sees *"You've asked something related to [Fallback Topic]…"* instead of the generic fallback. |
| **Offer Email Follow-up on Fallback** | ✓ On | When enabled, every fallback response offers the visitor an email notification when the gap is resolved. Disable only if you want the old plain-text fallback for a specific agent. |

> **This is default behaviour.** Both public and verified-identity visitors are offered email follow-up automatically. Desk users are never shown the email prompt.

**Access Categories tab** — must have at least one row:

| Access Category | Enabled |
|---|---|
| `Public Access` | ✓ |

For an internal/admin profile add `Internal Access` here as well.

Save.

---

## Phase 5 — Live Infrastructure

### 5.1 Live Channel

Navigate to: **Nexus Live Channel** list → confirm `WEBSITE-CHAT` exists.

Channels are logical backend contexts. The **Channel Type** determines which users see the channel's categories:

| Channel Type | Who sees its categories |
|---|---|
| `Website Chat` | Anonymous / public visitors via the website widget |
| `Desk` | Logged-in Frappe desk users via the desk chat widget |

> **Important:** A `Website Chat` channel is for the public website widget only. Desk users require a separate channel with Channel Type = `Desk` — see Phase 6.1.

Key fields for the public website channel:

| Field | Value |
|---|---|
| Channel Code | `WEBSITE-CHAT` |
| Channel Name | `Website Chat` |
| Channel Type | `Website Chat` |
| Enabled | ✓ |
| Public Access | ✓ |

### 5.2 Chat Category

Navigate to: **Nexus Chat Category** list → confirm `GENERAL-SUPPORT` exists.

| Field | Value |
|---|---|
| Category Code | `GENERAL-SUPPORT` |
| Category Label | `General Support` |
| Channel | `WEBSITE-CHAT` |
| Enabled | ✓ |
| Published | ✓ |
| Visibility | `External` or `Both` |
| Identity Verification Mode | `None` |

The category belongs to one channel. Selecting the category in the widget implies the channel behind the scenes.

> **A category must be both Enabled AND Published to appear in the chat widget.** An enabled but unpublished category is invisible to visitors and desk users.

### 5.3 Category Identity Route

Navigate to: **Nexus Category Identity Route** list.

Verify or create this route:

| Field | Value |
|---|---|
| Channel | `WEBSITE-CHAT` |
| Chat Category | `GENERAL-SUPPORT` |
| Identity Type | `Public` |
| AI Agent Profile | *(the seeded profile linked to PUBLIC-AI-ASSISTANT)* |
| Enabled | ✓ |
| Published | ✓ |

This maps: **anonymous visitor selecting GENERAL-SUPPORT under its Website Chat channel → PUBLIC-AI-ASSISTANT profile**.

> **The route must also be Published.** An enabled but unpublished route is not active — the system will return "No active AI Agent Profile route" when trying to start a chat.

The route should not be used to move a category to a different channel. The category establishes the channel; the route establishes which identity/profile/knowledge path handles that category.

### 5.4 Live Agent

Navigate to: **Nexus Live Agent** list → open `PUBLIC-AI-ASSISTANT`.

Verify:

| Field | Required Value |
|---|---|
| Agent Type | `AI` |
| Enabled | ✓ |
| Status | `Idle` |
| Max Active Sessions | `10` (or any number > 0) |
| Visibility | `Both` |

### 5.5 Agent Onboarding

Navigate to: **Nexus Agent Onboarding** list → find the record linked to `PUBLIC-AI-ASSISTANT`.

| Field | Required Value |
|---|---|
| Agent | `PUBLIC-AI-ASSISTANT` |
| Onboarding Status | `Approved` |

If no onboarding record exists, create one manually and set status to `Approved`.

> The agent **will not be assigned to any conversation** until its onboarding record exists and is Approved.

---

## Phase 6 — Desk User Access (for internal chat)

Logged-in Frappe desk users use the **Nexus Chat Widget** embedded in the desk interface. They need a dedicated **Desk-type** Live Channel, a **published** Chat Category, a **published** Category Identity Route, an AI Agent Profile, and a User Profile Assignment.

> **Common mistake:** Using a `Website Chat` channel type for desk users. The desk widget only loads categories from channels with Channel Type = `Desk`. A Website Chat channel will not appear in the desk widget even if it is enabled and published.

### 6.1 Create a Desk Live Channel

Navigate to: **Nexus Live Channel** → New.

| Field | Value |
|---|---|
| Channel Code | `WEBSITE-INTERNAL-CHAT` |
| Channel Name | `Website Internal Chat` |
| Channel Type | **`Desk`** |
| Tenant | *(your tenant)* |
| Enabled | ✓ |
| Public Access | unchecked |

Save.

### 6.2 Create a Desk Chat Category

Navigate to: **Nexus Chat Category** → New.

| Field | Value |
|---|---|
| Category Code | `INTERNAL-SUPPORT` |
| Category Label | `Internal Support` |
| Channel | `WEBSITE-INTERNAL-CHAT` |
| Enabled | ✓ |
| Published | ✓ |
| Visibility | `Internal` or `Both` |

Save.

> The category must be **Published** (not just Enabled) to appear in the desk chat widget. Unpublished categories are never loaded by the widget regardless of their enabled status.

### 6.3 Create a Category Identity Route for Desk

Navigate to: **Nexus Category Identity Route** → New.

| Field | Value |
|---|---|
| Channel | `WEBSITE-INTERNAL-CHAT` |
| Chat Category | `INTERNAL-SUPPORT` |
| Identity Type | `Desk User` |
| AI Agent Profile | `Internal User Profile` *(see 6.4)* |
| Enabled | ✓ |
| Published | ✓ |

Save.

> The route must also be **Published**. An enabled but unpublished route will not resolve the profile and the chat will fail with "No active AI Agent Profile route".

### 6.4 Create an Internal AI Agent Profile

Create a new **Nexus AI Agent Profile**:

| Field | Value |
|---|---|
| Profile Name | e.g. `Internal User Profile` |
| Default Response Mode | `chat` |
| Confidence Threshold | `0.50` |
| Behavior Prompt | e.g. `You are an internal knowledge assistant for staff.` |

**Access Categories tab:**

| Access Category | Enabled |
|---|---|
| `Internal Access` | ✓ |

### 6.5 Assign the Profile to the Desk User

Navigate to: **Nexus User Profile Assignment** → New.

| Field | Value |
|---|---|
| User | *(your Frappe user, e.g. Administrator)* |
| AI Agent Profile | `Internal User Profile` |
| Active | ✓ |

Save.

> Without this, the desk user gets a "no profile assignment" error when starting a chat.

---

## Phase 7 — Knowledge

### 7.1 Create a Knowledge Source

Navigate to: **Nexus Knowledge Source** → New.

| Field | Value |
|---|---|
| Title | e.g. `Company FAQ` |
| Source Type | `Manual` (or PDF/DOCX if uploading) |
| Manual Content | Paste your content here |
| Tenant | `DIGITZ-NEXUS` |
| Access Policy | `Public` |
| Status | `Draft` |

Save.

### 7.2 Process the Source

Click **Process** on the source form. This:
1. Extracts and chunks the content
2. Generates embeddings via OpenAI
3. Creates `Nexus Knowledge Chunk` records
4. Generates `Nexus Knowledge Index Entry` rows (User Questions + Intellectual Summaries)
5. Sets source status to `Processed`

> **Requires a running background worker:**
> ```bash
> bench worker --queue short
> ```

### 7.3 Approve Index Entries (User Questions)

Navigate to: **Nexus Knowledge Index Entry** list → filter by your source → filter `entry_type = User Question`.

For each entry, open it and set:

| Field | Value |
|---|---|
| Answer Review Status | `Approved` |

All User Question entries must be Approved before the source can reach `Ready to Publish`.

> Intellectual Summary entries do not need approval.

### 7.4 Publish the Source

Back on the Knowledge Source form:
1. Click **Validate** — source moves to `Ready to Publish` if all answers are approved
2. Click **Publish** — source status becomes `Published`, `retrieval_ready` = 1

Chunks are now live for retrieval.

> **Auto-notification trigger:** If this source was created from a Knowledge Gap (via **+ KS** on the Gap Review page) and the visitor left their email, publishing the source automatically sends the visitor a follow-up email using the `nexus-gap-visitor-followup` template — no manual action required. See Phase 10.

---

## Phase 8 — Verify

### 8.1 Chat Workflow Tester

Navigate to: `/nexus-chat-workflow-tester`

Enter:

| Input | Value |
|---|---|
| Channel | `WEBSITE-CHAT` |
| Chat Category | `GENERAL-SUPPORT` |
| Identity Type | `Public` |

Expected result:

```
Resolved Identity Type:  Public
AI Agent Profile:        [seeded public profile]
Access Categories:       Public Access
Access Policies:         Public
Warnings:                none
```

### 8.2 Test Retrieval

Navigate to: **Nexus Administration** → **Test Retrieval** (or `/nexus-retrieval-tester`).

Type a question that matches your knowledge source content. Verify:
- `access_status: allowed`
- At least one chunk returned with `embedding_status: Completed`
- `confidence` above 0.20

### 8.3 Live Console Chat (Desk User)

Navigate to: `/nexus-live-console`

Click the **chat-bubble-with-plus icon** (top of sidebar) → type a question → press Enter.

Expected sequence:
1. Message appears immediately on the right
2. Typing indicator appears
3. AI answer arrives via realtime event

If it fails, check:

| Error | Fix |
|---|---|
| "Tenant is required" | No active tenant in user context — ensure Nexus Tenant Configuration exists and `get_administration_snapshot` returns a tenant |
| "No approved idle AI agent" | Check Nexus Live Agent: enabled=1, status=Idle, agent_type=AI; check Nexus Agent Onboarding: onboarding_status=Approved |
| "No active AI Agent Profile route" | Missing Nexus Category Identity Route for the selected category and identity context |
| "No profile assignment" | Create Nexus User Profile Assignment for the logged-in user |
| Answer is fallback only | No Published knowledge with matching access policy; check Nexus Knowledge Source: status=Published, retrieval_ready=1, chunks have embedding_status=Completed |
| Typing indicator stuck | Background worker not running — run `bench worker --queue short` |

---

## Phase 9 — Agentic Runtime (optional)

Only needed if `digitz_ai_nexus_agentic` is installed.

### 9.1 Install the app

```bash
# If not already installed
/home/rupesh/frappe-bench/env/bin/pip install -e apps/digitz_ai_nexus_agentic --quiet
bench --site digitz_ai_nexus.site install-app digitz_ai_nexus_agentic
```

### 9.2 Verify seeded records

The `after_install` hook seeds all base records automatically. Verify in the desk:

| Record | DocType | Name |
|---|---|---|
| Nexy agent candidate | Nexus Agent Candidate | `CAND-NEXY` |
| Default safety profile | Nexus Agent Safety Profile | `NEXY-DEFAULT` |
| Sales capability pack | Nexus Capability Pack | `CAP-SALES` |
| Sales pack assignment | Nexus Capability Pack Assignment | enabled, priority 1 |
| Goal types | Nexus Agent Goal Type | 18 records |
| Tool registry | Nexus Agent Tool | 27 records |

### 9.3 Capability packs

`CAP-SALES` is enabled by default and handles all outreach/lead/suppression goal types.

`CAP-PURCHASE_COORDINATION` is seeded but **disabled** — enable it only when purchase coordination workflows are ready.

### 9.4 Safety constraints

All Nexy actions are governed by the safety profile. Do-not-do rules are enforced before any action executes:

- No customer/vendor-facing actions without an approved `Nexus Agent Approval Request`
- No direct database writes — all writes go through registered tools
- No direct LLM-to-external-API calls — all communication goes through channel adapters

See `apps/digitz_ai_nexus_agentic/docs/AGENTIC_ARCHITECTURE.md` for the full runtime architecture.

---

## Phase 10 — Knowledge Gap Review & Visitor Email Follow-up

### Overview

When a visitor asks a question that has no matching knowledge, the system:

1. Records a **Nexus Knowledge Gap** (reactive detection)
2. Responds with a contextual fallback message referencing the configured **Fallback Topic**
3. Offers the visitor an **email notification** for when the information becomes available
4. Validates the visitor's email with a **one-time OTP** before saving it
5. When an admin **publishes a Knowledge Source** that resolves the gap, the visitor is **automatically notified** by email

---

### 10.1 How the Visitor Experience Works

**Widget chat flow when a fallback occurs:**

```
AI cannot answer → fallback message shown:

  With Fallback Topic set:
  "Our knowledge base is continuously being fine-tuned based on user
   queries and interactions. Your question on [Fallback Topic] has been
   noted and is a valuable input to this process. We would be happy to
   revert back to you once this topic is covered in our knowledge base.
   Would you like us to respond to you via email?"

  Without Fallback Topic:
  "Our knowledge base is continuously being fine-tuned based on user
   queries and interactions. Your query has been noted and is a valuable
   input to this process. We would be happy to revert back to you once
   this is covered in our knowledge base.
   Would you like us to respond to you via email?"

→ Visitor types email → OTP sent via nexus-gap-otp-verification template
→ Visitor enters OTP code → email saved on the Knowledge Gap (status: Pending)
```

**If the visitor already verified their identity** (identity verification OTP already done in the same session), the system skips the OTP and shows a simple confirmation:
> *"We'll notify you at [email] when we have this information. Would you like to proceed?"*

**Desk users** never see the email prompt — it is suppressed automatically.

---

### 10.2 Knowledge Gap Review Page

Navigate to: `/app/nexus-knowledge-gap-review`

The page is also accessible from the **Nexus Studio workspace** under the **Knowledge Workbench** section.

**Summary bar chips:**

| Chip | Meaning |
|---|---|
| Total | All gap records |
| New | Gaps not yet actioned |
| Relevant | LLM assessed as in-domain |
| No Context | Queries with no matching knowledge |
| Low Confidence | Queries answered below confidence threshold |
| **Pending Follow-up** | Visitor emails saved, notification not yet sent |

**Table columns:**

| Column | Content |
|---|---|
| Query | Visitor's question, suggested topic, tenant |
| Type | No Context / Low Confidence / Restricted Access |
| Freq | Times the same question has been asked |
| Conf | Answer confidence (0–100%) |
| LLM | LLM relevance assessment and summary |
| Status | New / Under Review / Watching / Actioned / Dismissed |
| **Follow-up** | Visitor email + status; **Notify Visitor** button when pending |
| Last Seen | Date of most recent occurrence |
| Actions | Review, +KS, Reassess, Dismiss, ↗ |

---

### 10.3 Admin Workflow — Resolving a Gap

1. Open **Knowledge Gap Review** → find a relevant gap
2. Click **+ KS** → fill in the Knowledge Source form → click **Create Knowledge Source**
3. The gap records `suggested_knowledge_source` pointing to the new source
4. Work the source through the normal pipeline: **Process → Validate → Publish**
5. On **Publish**, the system auto-sends the follow-up email to the visitor (if email was captured)

**Manual notification:** If you want to notify the visitor before publishing (e.g. to tell them a partial answer), click **Notify Visitor** in the Follow-up column while status is Pending.

> Once notified (manually or automatically), `visitor_email_status` is set to `Notified` and the button disappears. The email will **not** fire again — the status flag prevents duplicates from both paths.

---

### 10.4 Email Templates

Two templates are loaded via fixtures on installation:

| Template Name | Used When | Variables |
|---|---|---|
| `nexus-gap-otp-verification` | OTP sent to verify visitor email | `{{ otp }}`, `{{ validity_minutes }}` |
| `nexus-gap-visitor-followup` | Follow-up sent when gap is resolved | `{{ gap_query }}`, `{{ gap_topic }}`, `{{ tenant_name }}` |

Customise these via **Email Template** list in the desk. Variable placeholders use Jinja2 syntax.

---

### 10.5 Proactive Gap Detection

In addition to reactive gaps (created on each fallback), the system can scan query logs for uncovered topic clusters.

- **Scheduled:** Runs weekly (`detect_proactive_gaps` scheduler job)
- **Manual trigger:** Click **Detect Gaps Now** on the Knowledge Gap Review page

Proactive gaps appear with a purple **Proactive** badge in the Query column.

---

### 10.6 Configuration Checklist for Email Follow-up

```
[ ] Nexus AI Agent Profile — Offer Email Follow-up on Fallback = checked (default)
[ ] Nexus AI Agent Profile — Fallback Topic set (e.g. "Company HR policies")
[ ] Email Template nexus-gap-otp-verification — exists (loaded via fixtures)
[ ] Email Template nexus-gap-visitor-followup — exists (loaded via fixtures)
[ ] Outgoing email configured in Frappe (Email Account → Outgoing)
[ ] Nexus Tenant — tenant_name set (used as sign-off in follow-up email)
```

---

## Quick-Start Checklist

```
[ ] Nexus Settings — API key saved
[ ] Seed defaults run (both apps)
[ ] Nexus Tenant — DIGITZ-NEXUS exists, not disabled
[ ] Nexus Tenant Configuration — chat channel set, live_chat_enabled=1
[ ] Nexus Access Policy — Public exists, not disabled
[ ] Nexus Access Category — Public Access → Public policy
[ ] Nexus AI Agent Profile — linked to agent, Public Access category assigned

# Public website chat
[ ] Nexus Live Channel — WEBSITE-CHAT, channel_type=Website Chat, enabled
[ ] Nexus Chat Category — GENERAL-SUPPORT, channel=WEBSITE-CHAT, enabled AND published
[ ] Nexus Category Identity Route — GENERAL-SUPPORT + Public identity → profile, enabled AND published
[ ] Nexus Live Agent — PUBLIC-AI-ASSISTANT, type=AI, status=Idle, enabled=1
[ ] Nexus Agent Onboarding — PUBLIC-AI-ASSISTANT, status=Approved

# Desk user (internal) chat
[ ] Nexus Live Channel — WEBSITE-INTERNAL-CHAT, channel_type=Desk, enabled
[ ] Nexus Chat Category — INTERNAL-SUPPORT, channel=WEBSITE-INTERNAL-CHAT, enabled AND published
[ ] Nexus Category Identity Route — INTERNAL-SUPPORT + Desk User identity → profile, enabled AND published
[ ] Nexus AI Agent Profile — Internal User Profile, Internal Access category assigned
[ ] Nexus User Profile Assignment — for each desk user who needs internal chat

# Knowledge
[ ] Nexus Knowledge Source — at least one Published source with access_policy=Public
[ ] Knowledge Chunks — embedding_status=Completed, disabled=0
[ ] Background worker running — bench worker --queue short

# Knowledge Gap & Email Follow-up
[ ] Nexus AI Agent Profile — Offer Email Follow-up on Fallback = checked
[ ] Nexus AI Agent Profile — Fallback Topic set (optional but recommended)
[ ] Email Template nexus-gap-otp-verification — exists (auto-loaded via fixtures)
[ ] Email Template nexus-gap-visitor-followup — exists (auto-loaded via fixtures)
[ ] Outgoing email configured in Frappe Email Account
[ ] Nexus Tenant — tenant_name set
```
