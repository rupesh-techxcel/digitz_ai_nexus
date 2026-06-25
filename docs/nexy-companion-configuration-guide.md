# Nexy Companion — Configuration Guide

Nexy is the AI sales companion embedded in NEXUS AI chat categories. When fully configured, Nexy qualifies visitors, adapts its persona to each buyer type, presents the right product at the right moment, and triggers a conversion action (demo booking, meeting request, etc.) when the visitor is ready — all without human intervention.

This guide covers every configurable element, what each field does at runtime, and the exact order to configure them.

---

## Architecture Overview

Nexy has two independent configuration chains that merge at the conversation level:

```
Chat Category
│   internal_drive_mode = "Companion Connect"    ← master switch
│
├── BEHAVIOR CHAIN (who Nexy is)
│     Nexy Companion Assignment
│       └── Nexy Role Profile + Sales Extension
│
└── CONTEXT CHAIN (what Nexy knows and does)
      AI Agent Profile
        ├── companion_playbook → Nexus Companion Playbook
        ├── companion_mode = 1
        Nexus Companion Product  (linked via chat_category)
        Nexus Companion Persona  (matched by tenant + visitor data)
```

At runtime:
- The **behavior chain** shapes Nexy's communication style, selling approach, and escalation rules.
- The **context chain** gives Nexy knowledge of the products, playbook guidelines, and visitor persona so it can guide conversations and trigger the conversion CTA card.

---

## Step-by-Step Configuration

Configure in this order. Each step depends on the one above it.

---

### Step 1 — Chat Category

**DocType:** `Nexus Chat Category`
**Path in Desk:** Live Channels → Chat Categories

The category is the entry point. Visitors select it from the chat widget. All companion configuration is scoped to a category.

| Field | Value for Companion Mode | Notes |
|---|---|---|
| `use_for_nexy` | ✓ Checked | Marks this category as a Nexy companion category |
| `internal_drive_mode` | `Companion Connect` | **Master switch** — activates the full companion pipeline. Without this, companion mode does not activate regardless of other settings |
| `enabled` | ✓ Checked | Category must be live |
| `published` | ✓ Checked | Must be published to appear in widget |
| `identity_verification_mode` | Usually `None` for public Nexy | Set `Email OTP` to require verified identity before companion activates |

> **Important:** `internal_drive_mode = "Companion Connect"` is what activates companion mode in the conversation snapshot. Without it, `companion_mode` stays `0` and the entire journey pipeline — enquiry creation, scoring, persona matching, stage advancement — never runs.

---

### Step 2 — Nexy Role Profile

**DocType:** `Nexy Role Profile`
**App:** `digitz_ai_nexus_nexy`
**Path in Desk:** Nexy → Role Profiles

The Role Profile defines **who Nexy is** — its communication style, selling rules, and what it will and won't say. One role profile can serve multiple categories via assignments (Step 4).

#### Identity

| Field | Purpose |
|---|---|
| `profile_name` | Internal identifier used in assignments |
| `tenant` | Must match the tenant of the chat category |
| `role_type` | `Sales` for a commercial companion; options: Sales, Customer Success, HR Onboarding, Partner Management |
| `enabled` | Must be checked for the assignment to activate |
| `role_description` | Internal note on this profile's purpose |

#### Communication Behavior

| Field | Options | Runtime Effect |
|---|---|---|
| `engagement_objective` | Free text | Injected as the opening directive in Nexy's system prompt. Tells the LLM *why* this conversation exists and what the primary goal is. Keep it concise (1-2 sentences). |
| `tone` | Professional, Consultative, Friendly, Direct, Empathetic | Colors all of Nexy's phrasing. `Consultative` is recommended for B2B sales. |
| `communication_style` | Concise, Detailed, Question-led, Empathetic, Structured | Shapes response length and format. `Question-led` makes Nexy ask discovery questions naturally. |
| `cta_style` | Soft, Direct, Invitation, Question, Next-step | How Nexy frames the conversion moment ("Would you like to…" vs "Let's book your demo now"). |
| `followup_style` | Gentle, Persistent, Value-reminder, Process-reminder | How Nexy follows up if the visitor goes quiet mid-conversation. |

#### Rules

| Field | Purpose |
|---|---|
| `do_rules` | Bullet list of behaviors Nexy must follow. Example: "Always tie product capabilities to the visitor's stated challenges." These are injected verbatim into the system prompt. |
| `dont_rules` | Bullet list of behaviors Nexy must avoid. Example: "Do not quote prices from memory." |
| `prohibited_claims` | Hard prohibitions. Example: "Do not claim guaranteed ROI figures." These are formatted as STRICT rules in the prompt. |

#### Escalation

| Field | Purpose |
|---|---|
| `escalation_policy` | Tells Nexy exactly when to call the `request_escalation` tool. **Be specific.** Vague policies cause premature escalation. Good example: "Only escalate when the visitor explicitly requests a human agent. Do not escalate for product questions or demo interest — the system handles demo booking automatically." |
| `requires_grounding` | When **checked**: Nexy must run `search_knowledge` before every product claim, and says "I don't have details" if the knowledge base returns nothing. Recommended **unchecked** for commercial companions where product details come from the Companion Product DocType (which is already injected into the AI context). When unchecked, a softer rule applies: search the KB for policy or case-study questions, but use companion context directly for product details. |

#### Role Extension (Sales-specific)

| Field | Value |
|---|---|
| `role_extension_doctype` | `Nexy Sales Profile Extension` — link this when `role_type = Sales` |

---

### Step 3 — Nexy Sales Profile Extension

**DocType:** `Nexy Sales Profile Extension`
**App:** `digitz_ai_nexus_nexy`
**Path in Desk:** Nexy → Sales Extensions

One extension per Role Profile. Adds commercial selling behavior on top of the base role.

| Field | Options | Runtime Effect |
|---|---|---|
| `role_profile` | Link to Nexy Role Profile | Identifies which profile this extends |
| `selling_style` | Value-led, Feature-led, Story-led, Problem-led, Consultative | Frames how Nexy positions the product. `Problem-led` leads with the visitor's pain before the solution. |
| `persuasion_style` | Logical, Social, Urgency, Authority, Empathy | Shapes objection responses. `Logical` uses ROI data; `Social` uses peer examples. |
| `objection_handling_style` | Acknowledge-Reframe, Evidence, Empathy-Bridge, Escalate | How Nexy responds to pushback. `Acknowledge-Reframe` is recommended for first-touch sales. |
| `urgency_style` | None, Availability, Deadline, Social-proof | Whether and how Nexy creates urgency. Use `None` for consultative selling. |
| `pricing_policy` | Free text | Nexy's instructions around pricing discussions. Example: "Always direct price questions to the pricing page; never quote a number from memory." |
| `discount_policy` | Free text | Example: "Nexy does not have authority to offer discounts. If pressed, acknowledge and offer to connect with the sales team." |
| `competitive_policy` | Free text | Example: "Do not compare us directly against named competitors. Instead, focus on our unique value." |

---

### Step 4 — Nexy Companion Assignment

**DocType:** `Nexy Companion Assignment`
**App:** `digitz_ai_nexus_nexy`
**Path in Desk:** Nexy → Companion Assignments

The assignment links a Chat Category to a Role Profile. This is the connector between the behavior chain (Steps 2-3) and the category (Step 1).

| Field | Value |
|---|---|
| `chat_category` | The Chat Category from Step 1 |
| `nexy_role_profile` | The Role Profile from Step 2 |
| `tenant` | Must match both |
| `enabled` | ✓ Checked |
| `assignment_notes` | Internal note (e.g., "Primary commercial companion for NEXUS-AI website visitors") |

> One category can have only one active assignment. If multiple assignments are enabled for the same category, the system picks the first one returned.

---

### Step 5 — Nexus Companion Playbook

**DocType:** `Nexus Companion Playbook`
**App:** `digitz_ai_nexus`
**Path in Desk:** Nexus Companion → Playbooks

The playbook provides **conversation structure** — the questions Nexy asks during discovery, how it handles objections, and when it escalates. Unlike the Role Profile (which defines character), the playbook defines **process**.

> The playbook is linked to the **AI Agent Profile** (Step 6), not to the Assignment or Category directly.

| Field | Purpose |
|---|---|
| `playbook_name` | Identifier |
| `tenant` | Must match |
| `enabled` | ✓ |
| `is_default` | Mark one playbook per tenant as default (used as fallback) |
| `description` | Internal note |

#### Conversation Structure Fields

| Field | Content Guidance |
|---|---|
| `discovery_questions` | List of questions Nexy should work through naturally — not as a rigid survey. Cover: industry, company size, team size, current challenges, goals, existing tools, budget, timeline, and decision-maker status. Mark which 3-4 are highest priority. Nexy adapts order based on context. |
| `qualification_questions` | A checklist that defines what "qualified" means. Example: "Company has 10+ employees AND has articulated at least one specific challenge AND timeline is within 6 months." Nexy uses this to determine when to push toward conversion vs. continue nurturing. |
| `communication_guidelines` | Tone, pacing, and format rules specific to this playbook. Example: "Keep responses to 3-5 sentences. Always use the visitor's name. Never paste feature lists unprompted." |
| `objection_responses` | Named objection handling scripts. Format: `"[Objection]": "Response…"`. Cover at least: price, existing tools, no time to implement, need to think. |
| `reference_usage_rules` | When Nexy should cite knowledge base articles vs. answer from context. Example: "Always cite the pricing page for price questions; never state a number from memory." |

#### Escalation Control

| Field | Purpose | Notes |
|---|---|---|
| `escalation_score_threshold` | Integer 0-100 | When the visitor's enquiry score reaches this value AND an escalation trigger matches, Nexy escalates to a human agent. Lower = escalates sooner. Recommended: 55-70. If no playbook is linked, the system uses a hardcoded threshold of 70. |
| `escalation_triggers` | Multi-line list of keywords/phrases | If any of these appear in the visitor's message AND score ≥ threshold, escalation fires. One phrase per line. Examples: "speak to someone", "account manager", "custom contract", "enterprise agreement". |
| `next_step_options` | Text | Instructions for what Nexy offers after conversion (demo booked), after a declined demo, or when the visitor is not yet qualified. Used by the AI as post-conversion guidance. |

---

### Step 6 — AI Agent Profile

**DocType:** `Nexus AI Agent Profile`
**App:** `digitz_ai_nexus_live`
**Path in Desk:** Live Agents → Agent Profiles

The AI Agent Profile is the core AI configuration for this category. It must have companion mode enabled and be linked to the playbook from Step 5.

#### Companion-specific fields

| Field | Value | Notes |
|---|---|---|
| `companion_mode` | ✓ Checked | **Required.** This is stored in the conversation snapshot on first message. If unchecked, the entire companion journey — enquiry creation, stage tracking, persona matching, conversion CTA — never runs. |
| `companion_playbook` | Link → Nexus Companion Playbook | The playbook from Step 5. Its discovery questions, communication guidelines, and escalation threshold are injected into the AI context on every turn. |
| `companion_discovery_style` | Conversational, Structured, Minimal | How Nexy weaves discovery questions into conversation. `Conversational` integrates questions naturally into dialogue. `Structured` asks them more directly. `Minimal` limits discovery to what the visitor volunteers. |

#### Other key fields (affects all category visitors)

| Field | Notes |
|---|---|
| `behavior_prompt` | Base system prompt. The Nexy companion enrichment appends Role Profile behavior on top of this. Keep it brief — detailed behavior belongs in the Role Profile. |
| `welcome_message` | First message Nexy sends when a visitor selects this category. |
| `fallback_message` | Shown when Nexy cannot answer. For companion mode, write this as an offer to continue the conversation: "I can connect you with more details — what aspect would you like to explore?" |
| `escalation_enabled` | Must be ✓ for the `request_escalation` agent tool to fire. |
| `confidence_threshold` | Float 0.0-1.0. Answers below this confidence get a hedging preamble. `0.65` is a reasonable default. |

---

### Step 7 — Nexus Companion Persona

**DocType:** `Nexus Companion Persona`
**App:** `digitz_ai_nexus`
**Path in Desk:** Nexus Companion → Personas

Personas represent the **types of buyers** Nexy expects to encounter. On every conversation turn, Nexy scores the visitor's discovery data against all active personas for the tenant and sets the best match on the enquiry. This influences how Nexy frames the product and which objections it anticipates.

> Personas are matched by **tenant**, not by category. All personas for a tenant are candidates for every conversation in that tenant.

| Field | Options | Notes |
|---|---|---|
| `persona_name` | Free text | Descriptive. Example: "SMB Tech Leader", "Enterprise Decision Maker" |
| `tenant` | Link | Must match the tenant |
| `enabled` | ✓ | |
| `customer_type` | B2B, B2C, Both | |
| `company_size` | Solo / Micro (2-10) / SME (11-50) / Mid-Market (51-200) / Enterprise (200+) | Matched against visitor's stated company size |
| `business_maturity` | Startup, Growing, Established, Scaling | |
| `industry` | Free text | Comma-separated list. Example: "Technology, SaaS, Consulting" |

#### Persona context fields (all Long Text — written as if describing this buyer type to Nexy)

| Field | What to write |
|---|---|
| `challenges` | Operational or strategic problems this type faces. These are matched against what the visitor describes as their challenges. |
| `pain_points` | Day-to-day frustrations. More specific than challenges. |
| `goals` | What they want to achieve — outcomes, not features. |
| `desired_outcomes` | Measurable results they'd consider success. |
| `buying_triggers` | Events that cause this persona to start evaluating solutions. Example: "Just raised funding", "Hiring a new sales lead", "Lost a deal due to slow response." |
| `common_objections` | Objections this persona typically raises. Nexy uses these to anticipate pushback. |
| `communication_style` | How this persona prefers to communicate. Example: "Direct and results-oriented; responds to concrete numbers over theory." |
| `recommended_messaging` | What messaging resonates. Example: "Lead with ROI and time saved. Emphasize quick setup." |

**Matching algorithm:** The persona matching service scores each persona against the visitor's accumulated discovery data using weighted field matching (industry: 30pts, company_size: 20pts, challenges: 20pts, pain_points: 15pts, business_maturity: 10pts, goals: 5pts). The highest-scoring persona above a confidence threshold is stored on the enquiry and injected into the AI context.

> **Recommended minimum:** 2-3 personas per tenant. Too few personas reduce matching accuracy; too many (10+) increase noise. 3-5 well-defined personas covering your main buyer types is ideal.

---

### Step 8 — Nexus Companion Product

**DocType:** `Nexus Companion Product`
**App:** `digitz_ai_nexus`
**Path in Desk:** Nexus Companion → Products

The product is what Nexy is selling. Products serve two roles:

1. **AI context** — All enabled products for the tenant are injected into Nexy's prompt so it can discuss and compare options.
2. **Conversion CTA card** — Products linked to a specific `chat_category` are used to trigger the conversion action (demo booking form, calendar link, etc.) when the visitor's score reaches the threshold.

> Products are linked to `chat_category` (not to a playbook or assignment). The `chat_category` link scopes which product triggers the conversion CTA for visitors entering through that category.

#### Identity

| Field | Notes |
|---|---|
| `product_name` | Display name used in the AI context and CTA card |
| `category` | Internal grouping. Example: "AI Business Platform" |
| `tenant` | Must match |
| `enabled` | ✓ |
| `chat_category` | Links this product to a specific entry point for CTA triggering |
| `next_step` | Learn More / Evaluation Request / Consultation Request / Direct Meeting — shown as the suggested next step before conversion threshold is reached |

#### Knowledge fields (injected into AI context — write as if briefing a sales rep)

| Field | What to write |
|---|---|
| `description` | 2-3 sentence product summary. The first thing Nexy reads to understand what it's selling. |
| `features` | Bullet list of capabilities. Keep each item one line. |
| `benefits` | Outcomes and value — what the customer gains, not what the product does. |
| `unique_value_propositions` | What makes this product different from alternatives. |
| `competitive_differentiators` | Specific comparison points. Use "vs [Category]" format rather than naming competitors directly. |
| `challenges_solved` | List of specific problems this product addresses. Nexy matches these against visitor challenges during the PRESENTING stage. |
| `qualification_criteria` | Who is a good fit. Nexy uses this to validate whether to push toward conversion. |
| `disqualification_criteria` | Who is NOT a fit. Prevents Nexy from wasting conversion moments on unsuitable visitors. |
| `typical_outcomes` | What customers experience at 30 / 90 / 180 days. Nexy uses these when building urgency. |
| `success_metrics` | Measurable KPIs. Example: "Lead response time < 2 minutes." |
| `objection_responses` | Product-specific objection handling (supplements the playbook's generic handling). Format: `"[Objection]": "Response…"` |

#### Conversion configuration

| Field | Options / Format | Notes |
|---|---|---|
| `conversion_type` | Lead Capture, Meeting Booking, Direct Purchase, Subscription, Trial Activation, Download Gate, Human Handoff, Webhook | Determines what the CTA card renders. `Meeting Booking` shows a calendar link. `Lead Capture` shows a form. |
| `conversion_threshold_score` | Integer 0-100 | The visitor's enquiry score must reach this value before the CTA card is shown. Recommended: 60-75 for B2B sales (below 60 the visitor isn't qualified enough; above 75 you may lose them before the ask). |
| `post_conversion_action` | Close Conversation, Continue Conversation, Escalate to Human | What happens after the visitor completes the CTA. `Continue Conversation` keeps Nexy active to handle post-booking questions. |
| `conversion_message` | Long Text | The message Nexy delivers when presenting the CTA. Written in first person as Nexy. Example: "Based on everything you've shared, I think a personalized demo would be the clearest way to see exactly how this fits your situation. Ready to book 30 minutes with the team?" |
| `conversion_fallback` | Long Text | If the CTA action fails or the visitor declines, Nexy uses this as a softer ask. Example: "Could you share your email so we can follow up directly?" |
| `conversion_config` | JSON | Configuration for the CTA action. Keys depend on `conversion_type`: |

**`conversion_config` JSON by type:**

```json
// Meeting Booking
{
  "calendar_url": "https://calendly.com/your-link/demo",
  "booking_label": "Book a 30-minute Demo",
  "success_message": "Your demo is booked! Check your email for the confirmation."
}

// Lead Capture
{
  "form_url": "https://your-site.com/contact",
  "form_fields": ["name", "email", "company", "phone"],
  "success_message": "Thanks! Our team will reach out within 1 business day."
}

// Direct Purchase
{
  "payment_url": "https://checkout.your-site.com/plan/pro",
  "success_message": "You're all set! Check your email for onboarding details."
}

// Webhook (custom backend action)
{
  "url": "https://your-api.com/nexus/lead-captured",
  "success_message": "All set — our team will be in touch shortly."
}
```

> **`target_personas` child table:** You can link specific personas to a product (Table field on the product). This is used in future matching logic to boost products that match the visitor's persona. Currently informational — the active matching uses `chat_category` scoping.

---

## How the Journey Works at Runtime

Once all 8 steps are configured, here is what happens on every visitor message:

```
Visitor sends message
        ↓
1. Behavior enrichment
   Nexy Companion Assignment → Role Profile + Sales Extension
   → replaces AI behavior_prompt with companion system prompt
   → forces chat_mode = "agent_loop" (enables tool calling)

2. Context injection
   AI Agent Profile → Playbook (discovery questions, guidelines, thresholds)
   Nexus Companion Product (for tenant) → injected into AI context
   Current stage, persona, discovery summary → injected into AI context

3. AI responds using agent loop
   Tools available: record_discovery, get_product_detail,
   get_relevant_reference, search_knowledge, request_escalation

4. Post-response: companion journey update
   Signal classifier reads visitor message → classifies signal
   (SHARING_CONTEXT, INTERESTED, READY, REQUESTING_HUMAN, etc.)

   update_enquiry():
   → merges new discovery data
   → re-runs persona matching across all tenant personas
   → recalculates enquiry score (0-100)
   → resolves recommended products from chat_category

   advance_journey_stage_from_signal():
   → advances stage based on signal
   (ARRIVED → GREETING → DISCOVERY → ENGAGED →
    PRESENTING → INTERESTED → CONVERTING → CONVERTED)

5. Conversion check
   If stage = CONVERTING:
   → get_conversion_action() reads top recommended_product
   → if product has conversion_type configured
   → returns CTA card data: {type, url, message, product}
   → widget renders the demo booking / purchase card

6. Escalation check
   If score ≥ playbook.escalation_score_threshold
   AND trigger keyword in visitor message:
   → stage → ESCALATED
   → human agent notified via desk
```

---

## Enquiry Score Breakdown

The enquiry score (0-100) drives stage advancement and conversion timing.

| Factor | Max Points | How it's calculated |
|---|---|---|
| Discovery completeness | 40 pts | Points per field filled in discovery_data. Fields: industry, company_size, team_size, business_maturity, current_challenges, goals, existing_systems, budget_range, timeline, decision_maker |
| Persona confidence | 30 pts | `persona_match.confidence × 0.30` |
| Qualification signals | 30 pts | Budget mentioned (+10), timeline within 6 months (+10), decision maker confirmed (+10) |

**Stage score floors** (score-based fallback when signal is ambiguous):

| Stage | Minimum Score |
|---|---|
| GREETING | 5 |
| DISCOVERY | 15 |
| ENGAGED | 30 |
| PRESENTING | 40 |
| INTERESTED | 55 |
| CONVERTING | 70 |

> Signal-driven advancement is always preferred over score-based. A READY signal jumps directly to CONVERTING regardless of score. Score-based advancement is a safety net.

---

## Troubleshooting

### Nexy is not responding as a companion (no persona, no journey tracking)

Check that ALL of the following are true:
- `Nexus Chat Category.internal_drive_mode = "Companion Connect"` ✓
- `Nexus AI Agent Profile.companion_mode = 1` ✓
- A `Nexy Companion Assignment` exists for this category, is enabled ✓
- The `Nexy Role Profile` linked in the assignment is enabled ✓

Start a **fresh conversation** after fixing any of the above — existing conversations have the old settings baked into their snapshot.

### Nexy says "I don't have specific details" about the product

- Check `Nexy Role Profile.requires_grounding` — if checked, Nexy must find product info in the knowledge base. For companions using `Nexus Companion Product` DocType data, uncheck this.
- Verify the `Nexus Companion Product` is enabled and has `tenant` set correctly.
- Verify `AI Agent Profile.companion_mode = 1` (otherwise `build_companion_context` never runs and no product data is injected).

### Nexy escalates immediately on the first message

- Check `escalation_policy` in the Role Profile. It must NOT include "offer demo request" language — demo booking is handled by the CTA card, not `request_escalation`.
- Check `escalation_score_threshold` in the Playbook — if too low (below 40), it fires before the visitor is qualified.
- The `request_escalation` tool should only be triggered by: explicit request for a human agent, unanswerable complex queries, or sentiment triggers.

### The conversion CTA card never appears

1. Verify `Nexus Companion Product.conversion_type` is set.
2. Verify `Nexus Companion Product.chat_category` matches the category exactly.
3. Verify `conversion_config` JSON has the right key: `calendar_url` (not `booking_url`) for Meeting Booking, `form_url` for Lead Capture, `payment_url` for Direct Purchase.
4. Check that the visitor's enquiry score has reached `conversion_threshold_score` — view the enquiry in **Nexus Companion Dashboard**.
5. Check that `companion_mode = 1` is in the conversation snapshot (visible in the Dashboard's enquiry detail panel).

### Persona is never matched

- Verify at least 2-3 `Nexus Companion Persona` records are enabled for the tenant.
- Verify the `challenges`, `industry`, and `company_size` fields are populated — these carry the most scoring weight.
- The match requires the visitor to have shared discovery data. Check the enquiry's `discovery_data` field — if it's `{}`, the `record_discovery` agent tool is not being called (may indicate companion mode is not active).

---

## Quick Reference: What Links to What

| From | To | Via |
|---|---|---|
| Chat Category | Nexy Role Profile | Nexy Companion Assignment |
| Chat Category | Nexus Companion Product | `product.chat_category` field |
| AI Agent Profile | Nexus Companion Playbook | `profile.companion_playbook` field |
| Nexy Role Profile | Nexy Sales Extension | `extension.role_profile` field |
| Conversation snapshot | All of the above | Set at conversation start from category + profile |
| Nexus Companion Enquiry | Persona | `enquiry.matched_persona` (auto-matched by score) |
| Nexus Companion Enquiry | Product | `enquiry.recommended_products` (auto-filled from category) |

---

*Last updated: 2026-06-25*
*Covers: digitz_ai_nexus, digitz_ai_nexus_nexy, digitz_ai_nexus_live*
