# Nexy Companion Intelligence — Milestones, Stages, Signals and Strategic Drive

> Document type: Knowledge Article — intended for publication in Nexus Orbit knowledge source
> Audience: Business stakeholders, Nexus partners, Nexy trainers, system administrators
> Last updated: 2026-06-28

---

## 1. What Is Nexy Companion?

Nexy Companion is the intelligent, conversation-led engagement layer of Nexus Orbit. When a visitor opens a chat, Nexy does not simply answer questions — it actively guides the visitor through a structured discovery journey, understands their business situation, identifies their challenges, and helps them move toward the right confirmed outcome.

Nexy operates on three independent intelligence layers running simultaneously in every conversation:

| Layer | Name | Purpose |
|---|---|---|
| **Layer 1** | Controller Milestones | What Nexy is working toward in this conversation |
| **Layer 2** | Journey Stages | Where the visitor sits in the conversion funnel |
| **Layer 3** | Buying Signals | How the visitor is engaging emotionally and behaviourally |

These three layers are not the same thing. They work together to give Nexy a complete picture of the visitor at every moment.

---

## 2. Controller Milestones — What Nexy Is Working Toward

### Definition

A milestone is the **current objective of the conversation**. It tells Nexy what it is trying to accomplish right now. Milestones progress in sequence — Nexy does not move to the next milestone until the current one is satisfied.

There are **8 milestones** in the business companion journey:

---

### Milestone 1: Onboarding Business

**Goal:** Understand who the visitor is and what their business does.

Nexy opens by learning the visitor's company type, industry, and role before anything else. No solution, pricing, or capability discussion happens here. Nexy is listening and building context.

**What Nexy asks:** "What does your company do?" / "Could you tell me a little about your business?"

**How it advances:** When the visitor has shared their industry and stated at least one business challenge, the milestone advances.

---

### Milestone 2: Business Discovery

**Goal:** Understand the business context deeply — size, maturity, goals, existing systems.

With the basic identity known, Nexy deepens its understanding. It wants to know the scale of the business, how established it is, what tools they currently use, and what they are trying to achieve.

**What Nexy asks:** "How large is your team?", "What systems are you using today?", "What are you hoping to achieve in the next 12 months?"

---

### Milestone 3: Pain Discovery

**Goal:** Understand the specific pain, challenge, or problem the visitor is trying to solve.

Nexy moves from general business understanding to the specific issue. It asks the visitor to describe their current approach to the problem and where it is breaking down. This is critical — Nexy must understand the pain before it can responsibly suggest anything.

**What Nexy asks:** "What kind of methodologies are you using now for lead generation?", "Where is your current process breaking down?", "What have you already tried?"

---

### Milestone 4: Solution Mapping

**Goal:** Match the visitor's confirmed pain to what Nexus Orbit can genuinely address.

Only when pain is clearly understood does Nexy begin mapping the visitor's needs to confirmed Nexus capabilities. Nexy does not claim capability that is not confirmed in the knowledge base. This milestone is where grounding becomes mandatory — every solution claim must be backed by confirmed Nexus Orbit knowledge.

**What Nexy does:** Searches for specific capability knowledge, explains how Nexus addresses the confirmed pain, asks one diagnostic question to refine the fit.

---

### Milestone 5: Evidence Building

**Goal:** Build confidence and trust through proof — stories, outcomes, and real results.

Once a solution fit is established, the visitor typically needs evidence before committing. Nexy shares relevant case studies, testimonials, and outcome data specific to the visitor's industry and persona.

**What Nexy does:** Surfaces relevant stories and testimonials, frames outcomes in terms relevant to the visitor's stated goals.

---

### Milestone 6: Demo Arrangement

**Goal:** Guide the visitor toward a confirmed demonstration or consultation appointment.

When interest is established and evidence has been shared, Nexy moves toward securing a next step. The most common next step is a confirmed demo request. Nexy collects the required contact details and submits the demo request.

**What Nexy does:** Offers a demo, waits for explicit confirmation, collects contact details, submits the demo record.

---

### Milestone 7: Quotation

**Goal:** Address commercial questions with confirmed pricing or quotation guidance.

When a visitor is ready to discuss investment, Nexy handles pricing discussions using confirmed Nexus Orbit pricing knowledge. Nexy never guesses prices or makes commercial commitments without confirmed knowledge.

---

### Milestone 8: Conversion

**Goal:** Complete the conversion action — the visitor has taken the intended next step.

This milestone is reached when the visitor has completed the conversion — demo booked, enquiry submitted, subscription initiated, or meeting confirmed. The conversation enters a resolution state.

---

### Milestone Progression Summary

```
Onboarding Business
    → Business Discovery
        → Pain Discovery
            → Solution Mapping
                → Evidence Building
                    → Demo Arrangement
                        → Quotation
                            → Conversion
```

Each milestone is sequential. Nexy will not move to Solution Mapping before Pain Discovery is complete. This prevents premature pitching — a structural safeguard built into the architecture.

---

## 3. Journey Stages — Where the Visitor Is in the Funnel

### Definition

A journey stage is the **funnel position** of the visitor — used for reporting, dashboard tracking, and understanding the overall pipeline health. Stages are driven by how the visitor is *behaving*, not by what Nexy has accomplished. A visitor can be `ENGAGED` while Nexy is still on the `business_discovery` milestone.

There are **11 journey stages**:

| Stage | Meaning |
|---|---|
| `ARRIVED` | Visitor has opened the chat — not yet interacted |
| `GREETING` | Visitor has sent their first message |
| `DISCOVERY` | Visitor is sharing information about themselves |
| `ENGAGED` | Visitor is actively participating and responding |
| `PRESENTING` | Visitor is receiving and considering solution information |
| `OBJECTION_HANDLING` | Visitor has raised a concern or resistance |
| `INTERESTED` | Visitor has shown positive signals toward a next step |
| `CONVERTING` | Visitor is in the process of completing a conversion action |
| `CONVERTED` | Conversion completed successfully |
| `DECLINED` | Visitor has chosen not to proceed |
| `ESCALATED` | Visitor has been handed to a human agent |

### Stage Transitions

Stage transitions are **signal-driven** — every visitor message is analysed and classified as a buying signal. The signal type determines whether and how the stage advances. For example:

- `SHARING_CONTEXT` → advances toward `DISCOVERY`
- `INTERESTED` → advances toward `INTERESTED` stage
- `READY` → advances toward `CONVERTING`
- `OBJECTING` → moves to `OBJECTION_HANDLING`
- `REQUESTING_HUMAN` → moves to `ESCALATED`

### Milestone vs Stage — Key Distinction

| | Controller Milestone | Journey Stage |
|---|---|---|
| **Driven by** | Discovery criteria met | Visitor buying signal |
| **Owned by** | Nexy's controller (internal) | Signal classifier |
| **Purpose** | What Nexy works toward next | Funnel position for reporting |
| **Visible to** | Desk operators, dashboard | Desk operators, dashboard |
| **Example** | `solution_mapping` | `PRESENTING` |

A visitor can be at `PRESENTING` stage (they are receiving solution information) while Nexy's milestone is still `pain_discovery` (Nexy is still refining the pain understanding before confirming a fit). The two systems serve different purposes and are intentionally independent.

---

## 4. Buying Signals — How the Visitor Is Engaging

### Definition

A buying signal is a real-time classification of the visitor's **emotional and behavioural state** in their latest message. Every single message is classified into one of 14 signal types using AI judgment — not keyword matching. This gives Nexy a live reading of how the visitor is feeling and what they are likely to do next.

Signals are grouped into four categories:

---

### Discovery Signals — The Visitor Is Sharing

| Signal | What It Means |
|---|---|
| `SHARING_CONTEXT` | The visitor is describing their business situation, background, or current challenge |
| `ANSWERING_QUESTION` | The visitor is responding to a question Nexy asked |

These signals confirm the visitor is engaged in the discovery process. Nexy should acknowledge and continue gathering context.

---

### Interest Signals — The Visitor's Engagement Level

| Signal | What It Means |
|---|---|
| `CURIOUS` | Exploring, asking general questions — low commitment, early stage |
| `EVALUATING` | Comparing options, asking deeper questions — genuine consideration |
| `INTERESTED` | Expressing positive engagement or fit recognition |
| `READY` | Clear intent to proceed — buy, subscribe, book, start |

These signals tell Nexy how far the visitor has moved from initial curiosity toward commitment. `READY` is the clearest positive signal in the taxonomy.

---

### Conversion Signals — The Visitor Is Moving Toward a Decision

| Signal | What It Means |
|---|---|
| `ASKING_PRICE` | The visitor is asking about cost, pricing, or packages |
| `ASKING_NEXT_STEP` | The visitor is asking how to proceed or what comes next |

These signals indicate the visitor is close to a decision. Nexy should handle these with care — confirm fit before introducing pricing, and guide next step only when the controller milestone permits.

---

### Resistance Signals — The Visitor Is Pulling Back

| Signal | What It Means |
|---|---|
| `OBJECTING` | Raising a specific concern about price, timing, need, or trust |
| `HESITATING` | Non-committal, vague, or slowing down without a clear reason |
| `DISENGAGING` | Short or dismissive replies — losing interest |
| `DEFLECTING` | Changing the subject or actively avoiding Nexy's questions |

Resistance signals do not mean the visitor is lost. They mean Nexy must shift approach — address the concern (objection), re-engage with empathy (hesitation), re-establish relevance (disengaging), or acknowledge and gently redirect (deflecting).

---

### Cycle-Ending Signals — The Conversation Is About to Close

| Signal | What It Means |
|---|---|
| `REQUESTING_HUMAN` | The visitor wants to speak with a real person |
| `DECLINING` | The visitor is explicitly not interested and wants to exit |

`REQUESTING_HUMAN` triggers the escalation path — Nexy prepares a handover. `DECLINING` closes the conversation gracefully with a door left open for future contact.

---

## 5. The Strategic Drive of Nexy

### How the Three Layers Work Together

Every visitor message triggers this sequence:

```
Visitor message
       ↓
1. Classify Buying Signal     → How is the visitor engaging?
2. Classify External Intent   → What does the visitor want to do?
3. Extract Discovery Data     → What facts did the visitor share?
4. Update Enquiry             → Record and score the conversation
5. Advance Journey Stage      → Move the funnel position based on signal
6. Decide Steering            → What should Nexy do next?
7. Apply Grounding Policy     → Can Nexy use confirmed knowledge? Or discovery only?
8. Generate Response          → Draft within controller constraints
```

This sequence runs **on every message** without exception. Nexy never operates from assumption or general LLM knowledge — every response is shaped by the current milestone, the current stage, and the live signal reading.

### The Non-Premature-Pitch Rule

Nexy is architecturally prevented from mentioning solutions, capabilities, pricing, or demos before the controller's milestone permits it. A visitor who asks "how can you help us with Facebook ads?" in the very first message will not receive a capability claim — they will receive a controlled, grounded response that either:

1. Searches confirmed Nexus Orbit knowledge and answers only from that, or
2. Returns a safe fallback: "I don't have confirmed knowledge for that specific capability yet" — if no specific knowledge is found

This means Nexy will never make up or imply product capabilities. It only states what is confirmed.

### Grounding Modes — Three Ways Nexy Responds

| Mode | When Used | What Nexy Can Do |
|---|---|---|
| `nexus_knowledge_only` | Visitor asks about Nexus capabilities, pricing, or how-it-works | Answer only from confirmed Nexus Orbit knowledge. If no knowledge found, state clearly that confirmed information is not available. |
| `controller_only` | Discovery questions, onboarding, general exploration | Ask discovery questions and draft natural wording within the controller's plan. No product, pricing, or capability claims. |
| `no_llm_direct` | Demo confirmed or rejected by visitor | Controller returns a fixed, hardcoded response without calling the LLM at all. |

---

## 6. The De-Diversion Mechanism — Keeping the Visitor on Track

### The Problem

In real conversations, visitors frequently go off-track. They ask unrelated questions, jump ahead to pricing before their situation is understood, request demos before fit is confirmed, or try to discuss topics outside the current milestone. A passive chatbot would follow wherever the visitor leads — losing the structure that makes conversion possible.

### How Nexy Handles Diversion

Every visitor message is classified for **external intent** — what the visitor is trying to do — independently of what milestone Nexy is on. When the intent is misaligned with the current milestone, the steering decision controls how Nexy responds.

#### Steering Decision Types

| Situation | Steering Decision | What Nexy Does |
|---|---|---|
| Visitor answers onboarding question | `continue_milestone` | Acknowledge and ask the next natural discovery question |
| Visitor shares a pain/challenge | `discover_current_methodology` | Ask what current approach they use for that challenge |
| Visitor asks how Nexus can help (general) | `answer_solution_fit` | Search confirmed knowledge; answer only from confirmed grounding |
| Visitor asks about pricing too early | `brief_answer_then_redirect` | Acknowledge briefly, redirect to current milestone |
| Visitor asks for a demo too early | `acknowledge_then_redirect` | Acknowledge the interest, explain that understanding their situation comes first |
| Visitor asks about Nexus product specifics | `answer_with_orbit` | Retrieve and answer from confirmed Nexus knowledge, then continue |
| Visitor asks something off-topic | `redirect_to_milestone` | Acknowledge briefly, steer back without sounding restrictive |
| Visitor asks for a human agent | `offer_escalation` | Prepare handoff, do not ask unrelated discovery questions |

#### The Pending Action Tracker

If Nexy has already offered a demo or handoff in a previous message, it marks that as a **pending action**. If the visitor's next message is a confirmation, Nexy confirms the action immediately. If it is a rejection, Nexy handles it gracefully and continues the conversation. Nexy never re-asks for something the visitor has already confirmed.

#### The Fallback Guard

If a visitor asks about a specific Nexus capability and no confirmed Nexus Orbit knowledge exists for it, Nexy does not guess. It does not infer from general AI knowledge. It returns a controlled fallback:

> "I don't have confirmed Nexus Orbit knowledge available for that specific capability yet, so I should not claim exactly how Nexus handles it. I can capture your requirement clearly and help route it for the right confirmed guidance."

This prevents hallucinated capability claims, which are the most damaging failure mode for a business companion.

### The Re-engagement Flow

When a visitor starts disengaging (`DISENGAGING` or `DEFLECTING` signal), Nexy does not persist with the same line of questioning. It shifts to re-engagement — acknowledging the visitor's apparent hesitation and offering an easier entry point, typically returning to an earlier discovery question or offering to answer any question they have first.

### The Escalation Gate

`REQUESTING_HUMAN` is treated as a **hard interrupt** — it overrides the current milestone immediately. Nexy does not continue discovery questions when a visitor has asked for a human. It moves directly to the escalation path, acknowledges the request, verifies identity if needed, and prepares the handover. The milestone state and enquiry record are preserved so the human agent can see the full conversation context.

---

## 7. Customer Persona Handling

### What Is a Persona?

A persona is a **predefined visitor archetype** — a profile of a typical customer that the business has identified and configured. Examples might be "Growing SME in Services", "Enterprise IT Decision Maker", or "Owner-Managed Retail Business". Each persona captures the industry, company size, business maturity, common challenges, pain points, and goals that characterise that type of visitor.

Personas are configured per tenant in the `Nexus Companion Persona` DocType and are entirely business-specific — Nexus does not impose archetypes.

---

### How Persona Matching Works

Persona matching runs **on every visitor message** — it is not a one-time assessment. As Nexy learns more about the visitor through discovery, the persona match is continuously recalculated and refined.

#### The Matching Engine

The persona matcher scores visitor discovery data against all enabled personas for the tenant. It uses a weighted keyword matching approach across six discovery fields:

| Discovery Field | Weight | What It Captures |
|---|---|---|
| `industry` | 30% | The sector the visitor's business operates in |
| `company_size` | 20% | Number of employees, team size, or operational scale |
| `challenges` | 20% | Business problems the visitor has described |
| `pain_points` | 15% | Specific friction areas the visitor has mentioned |
| `business_maturity` | 10% | How established the business is (startup, growing, mature) |
| `goals` | 5% | What the visitor wants to achieve |

For each persona, the engine extracts meaningful keywords from the persona's configured fields and checks how many of those keywords appear in the visitor's accumulated discovery data. The result is a normalised confidence score between 0 and 100.

**Minimum match threshold:** A persona is only considered matched when the confidence score reaches 20 or above. Below that, no persona is assigned — Nexy continues in neutral discovery mode.

#### Continuous Re-Matching

Because persona matching reruns after every message, the matched persona can:
- **Strengthen** as the visitor shares more aligned information
- **Switch** if later discovery data better fits a different persona
- **Appear** for the first time when enough discovery data has accumulated

This means Nexy's understanding of who the visitor is improves throughout the conversation rather than being locked in at the first few messages.

---

### How Persona Affects the Conversation

#### 1. Enquiry Scoring — 30% of the Score

The persona confidence score directly contributes to the **Enquiry Score** (the 0–100 composite score that reflects how qualified the visitor is). The three components of the enquiry score are:

| Component | Maximum Points | Source |
|---|---|---|
| Discovery completeness | 40 pts | How many discovery fields have been filled |
| **Persona confidence** | **30 pts** | How strongly the visitor matches a persona |
| Qualification signals | 30 pts | Specific keywords indicating strong buying intent |

A visitor who strongly matches a configured persona is automatically rated higher — because a matched persona means Nexy knows which products and services are relevant, which objections are likely, and what outcomes the visitor cares about.

#### 2. Product and Service Recommendations

The matched persona shapes which products and services Nexy considers relevant. Each `Nexus Companion Product` and `Nexus Companion Service` can be linked to one or more personas. When a persona is matched, Nexy can prioritise the products most likely to resonate with that visitor type.

#### 3. Escalation Threshold

The playbook's escalation score threshold determines when Nexy considers the visitor ready for a human consultant. Because persona confidence feeds the score, a strong persona match accelerates the visitor toward the escalation threshold — meaning highly qualified visitors are recognised and escalated faster.

---

### What Is Stored

At every stage, the persona match is written to two places:

**On the `Nexus Companion Enquiry`:**
- `matched_persona` — link to the matched `Nexus Companion Persona` record
- `persona_confidence` — numeric confidence score (0–100)
- `enquiry_score` — the recalculated composite score incorporating persona confidence

**On the `Nexus Live Conversation`:**
- `companion_persona` — live link to the current matched persona
- `companion_persona_confidence` — live confidence score

Both are updated in real time. Desk operators watching an active conversation in the dashboard can see the persona match and confidence as it develops.

---

### What Happens at Conversion

When a visitor reaches `CONVERTED` or `ESCALATED`, Nexy automatically creates or updates a **Nexus Contact** record. This record carries:

- Visitor email and phone
- The matched persona and persona confidence at the time of conversion
- The final enquiry score
- Discovery data (industry, company size, challenges, goals etc.)

This means the business team receiving the lead already knows the visitor's archetype, confidence level, and the specific challenges they described — without reading the full transcript.

---

### Persona Configuration — What Businesses Define

Each `Nexus Companion Persona` record contains:

| Field | Purpose |
|---|---|
| `persona_name` | Human-readable archetype label |
| `industry` | Industries this persona typically operates in |
| `customer_type` | B2B / B2C / Government / Non-Profit etc. |
| `company_size` | Typical headcount or team structure |
| `business_maturity` | Startup / Growing / Established / Enterprise |
| `challenges` | Common challenges this type of business faces |
| `pain_points` | Specific friction areas common to this persona |
| `goals` | What this type of visitor typically wants to achieve |
| `desired_outcomes` | The results this persona is looking for |

The richer these fields are, the more accurately Nexy can recognise and match visitors to the right archetype during a live conversation.

---

### Persona Matching in the Intelligence Flow

Persona matching sits in the middle of the per-message intelligence sequence:

```
Visitor message
       ↓
Classify buying signal
Classify external intent
Extract discovery data from message    ← new facts about the visitor
       ↓
Update Enquiry
    → Merge new discovery data into cumulative record
    → Re-run persona matching against all tenant personas    ← PERSONA LAYER
    → Recalculate enquiry score (discovery + persona + qualification)
    → Determine recommended next step
    → Resolve recommended products
       ↓
Decide steering (controller uses score + milestone + intent)
       ↓
Generate response
```

The persona match result feeds the score, the score influences steering decisions, and the steering decision shapes what Nexy says next. Persona is not a label applied once at the start — it is a continuously updating intelligence signal that shapes the entire conversation.

---

## 8. What Nexy Never Does

Regardless of how the visitor phrases their request, the following are architectural constraints — not preferences:

- **Never claims a Nexus capability without confirmed knowledge** — no "Nexus can automate your Facebook ads" unless the knowledge base confirms it
- **Never mentions pricing, packages, or commitments without confirmed knowledge**
- **Never moves to demo arrangement before fit is established**
- **Never re-asks what the visitor has already confirmed**
- **Never uses the words "sales", "selling", "sell", "pitch", or "lead"** in any visitor-facing message
- **Never reveals internal state** — no mention of milestones, steering decisions, controller logic, or intent classifications to the visitor
- **Never overrides the public identity verification prompt with its own email request** in companion mode — the controlled fallback is used instead

---

## 9. Summary: The Three Layers at a Glance

```
Every visitor message
        ↓
┌─────────────────────────────────────────────────────────┐
│ BUYING SIGNAL (14 types)                                │
│ How the visitor is behaving emotionally right now       │
│ → Drives Journey Stage advancement                      │
│                                                         │
│ EXTERNAL INTENT (15 types)                              │
│ What the visitor is trying to do in this message        │
│ → Drives Steering Decision                              │
│                                                         │
│ CONTROLLER MILESTONE (8 stages)                         │
│ What Nexy is working toward in this conversation        │
│ → Determines which steering decisions are available     │
└─────────────────────────────────────────────────────────┘
        ↓
Grounding mode selected (knowledge / controller-only / direct)
        ↓
Response drafted within controller constraints
        ↓
Milestone advanced if discovery criteria met
        ↓
Journey stage advanced based on signal
        ↓
Dashboard updated in real time
```

The result is a conversation that is simultaneously responsive to the visitor (signals and intents respected) and strategically guided (milestones enforce sequencing) — without the visitor ever being aware that a structure is in place.

---

*This document describes the intelligence architecture of Nexy Companion as implemented in Nexus Orbit. For technical implementation detail see `nexus-companion-framework.md` and `NEXUS_COMPLETE_ARCHITECTURE.md`.*
