import frappe


HOME_BLOCK = "nexus-home-workspace-html-block"
STUDIO_BLOCK = "nexus-studio-workspace-html-block"
ADMIN_BLOCK = "nexus-administration-workspace-html-block"
PLATFORM_BLOCK = "nexus-platform-workspace-html-block"
LIVE_BLOCK = "nexus-live-workspace-html-block"


HOME_HTML = """
<div class="nexus-ws">

    <!-- HERO -->
    <div class="nxl-ws-hero">

        <div class="nxl-ws-panel nxl-ws-panel-blue">
            <span class="nxl-ws-kicker">NEXUS ORBIT</span>
            <div class="nxl-ws-title-row">
                <div class="nxl-ws-icon-box">
                    <svg viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="15" cy="15" r="4" stroke="#ffffff" stroke-width="2"/>
                        <ellipse cx="15" cy="15" rx="13" ry="5.5" stroke="#ffffff" stroke-width="1.5"/>
                        <ellipse cx="15" cy="15" rx="13" ry="5.5" stroke="#ffffff" stroke-width="1.5" transform="rotate(60 15 15)"/>
                        <ellipse cx="15" cy="15" rx="13" ry="5.5" stroke="#ffffff" stroke-width="1.5" transform="rotate(120 15 15)"/>
                    </svg>
                </div>
                <h1 class="nxl-ws-h1">Nexus Orbit</h1>
            </div>
            <p class="nxl-ws-lead">
                The unified AI platform for governed knowledge, live AI chat, identity governance,
                and agentic workflows. Tenant-isolated, access-controlled, and human-escalation-ready
                from source intake to response delivery.
            </p>
            <div class="nxl-ws-chips">
                <span class="nxl-ws-chip">Governed Knowledge</span>
                <span class="nxl-ws-chip">Live AI Chat</span>
                <span class="nxl-ws-chip">Identity Governance</span>
                <span class="nxl-ws-chip">Tenant Isolation</span>
                <span class="nxl-ws-chip">Agentic AI</span>
                <span class="nxl-ws-chip">Human Escalation</span>
            </div>
        </div>

        <div class="nxl-ws-panel nxl-ws-panel-teal">
            <span class="nxl-ws-kicker nxl-ws-kicker-teal">PLATFORM WORKSPACES</span>
            <h2 class="nxl-ws-panel-title">Navigate Nexus Orbit</h2>
            <div class="nxl-ws-links">
                <a class="nxl-ws-link-item nxl-ws-link-item-blue" href="/app/nexus-studio">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-blue">ST</div>
                    <div>Nexus Studio<span class="nxl-ws-link-desc">Knowledge operations</span></div>
                </a>
                <a class="nxl-ws-link-item nxl-ws-link-item-blue" href="/app/nexus-live">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-blue">LV</div>
                    <div>Nexus Live<span class="nxl-ws-link-desc">Chat &amp; escalation</span></div>
                </a>
                <a class="nxl-ws-link-item nxl-ws-link-item-blue" href="/app/nexus-administration">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-blue">AD</div>
                    <div>Nexus Administration<span class="nxl-ws-link-desc">Tenant configuration</span></div>
                </a>
            </div>
        </div>

    </div>

    <!-- PLATFORM ECOSYSTEM STRIP -->
    <div class="nexus-context-grid">

        <div class="nexus-context-card nexus-context-card-primary">
            <div class="nexus-context-icon nexus-context-icon-large">NO</div>
            <div>
                <h3 class="nexus-context-title nexus-context-title-large">Nexus Orbit — Core Platform</h3>
                <p class="nexus-context-text">Governs the full AI knowledge lifecycle — from source intake and classification to retrieval, access control, live AI chat, identity verification, and human escalation.</p>
            </div>
        </div>

        <div class="nexus-context-card nexus-context-card-teal">
            <div class="nexus-context-icon nexus-context-icon-mint">AG</div>
            <div>
                <h4 class="nexus-context-title">Nexus Agentic</h4>
                <p class="nexus-context-text">LLM workflow engine running on Orbit — multi-step reasoning, tool use, retrieval access, and action orchestration.</p>
            </div>
        </div>

        <div class="nexus-context-card">
            <div class="nexus-context-icon">Nx</div>
            <div>
                <h4 class="nexus-context-title">Nexus Candidates</h4>
                <p class="nexus-context-text">Purpose-built AI candidates (Nexy + future) operating on Orbit and Agentic layers for specific business domains.</p>
            </div>
        </div>

        <div class="nexus-context-card nexus-context-card-teal-soft">
            <div class="nexus-context-icon nexus-context-icon-teal">TN</div>
            <div>
                <h4 class="nexus-context-title">Tenant Isolation</h4>
                <p class="nexus-context-text">Every tenant owns its knowledge, defaults, query logs, and runtime access boundaries — fully isolated.</p>
            </div>
        </div>

    </div>

    <!-- SECTION 01: PLATFORM ARCHITECTURE -->
    <div class="nexus-section">
        <div>
            <div class="nexus-section-badge">01 - Platform Architecture</div>
            <h3 class="nexus-section-title">Three Layers, One Platform</h3>
            <p class="nexus-section-text">
                Nexus is structured in three purposefully separated layers. Orbit is the core —
                knowledge, governance, and delivery. Agentic runs workflows using Orbit knowledge.
                Candidates are finished AI products built on both.
            </p>
        </div>
    </div>

    <section class="nexus-card-grid">

        <div class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">OR</div>
            </div>
            <h3 class="nexus-card-title">Nexus Orbit</h3>
            <div class="nexus-card-subtitle">Core platform layer</div>
            <p class="nexus-card-text">
                Handles the complete knowledge pipeline — source intake, classification, embedding,
                retrieval, access policy enforcement, live AI chat delivery, identity verification,
                and human escalation. Everything in Nexus depends on Orbit.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Knowledge</span>
                <span class="nexus-tag">Retrieval</span>
                <span class="nexus-tag">Chat</span>
                <span class="nexus-tag">Governance</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-teal">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">AG</div>
            </div>
            <h3 class="nexus-card-title">Nexus Agentic</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Workflow intelligence layer</div>
            <p class="nexus-card-text">
                Purpose-built LLM workflow engine operating on top of Orbit. Runs multi-step
                reasoning, tool use, and action orchestration with full access to governed
                knowledge, chat context, and escalation from the Orbit layer.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Reasoning</span>
                <span class="nexus-tag nexus-tag-teal">Tool Use</span>
                <span class="nexus-tag nexus-tag-teal">Orchestration</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-purple">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">Nx</div>
            </div>
            <h3 class="nexus-card-title">Nexus Candidates</h3>
            <div class="nexus-card-subtitle">Purpose-built AI products</div>
            <p class="nexus-card-text">
                Finished AI products built on Orbit and Agentic. Nexy is the flagship — a
                multi-role candidate for customer care, sales, analytics, ERP operations,
                and beyond. Future candidates extend into additional business domains.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Nexy</span>
                <span class="nexus-tag nexus-tag-purple">Multi-Role</span>
                <span class="nexus-tag nexus-tag-purple">Extensible</span>
            </div>
        </div>

    </section>

    <!-- SECTION 02: GOVERNANCE FLOW -->
    <div class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">02 - Governance Flow</div>
            <h3 class="nexus-section-title">From Visitor to Governed Response</h3>
            <p class="nexus-section-text">
                Before any knowledge reaches a visitor, Nexus runs a five-stage governance path.
                Each stage is an explicit control point — the platform does not skip steps.
            </p>
        </div>
    </div>

    <section class="nexus-card-grid">

        <div class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">P1</div>
            </div>
            <h3 class="nexus-card-title">Persist</h3>
            <div class="nexus-card-subtitle">Tenant knowledge layer</div>
            <p class="nexus-card-text">
                Each tenant gets its own persistent, scoped knowledge system — separated by
                tenant boundary, reusable across channels, and ready for governed AI delivery.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">SOPs</span>
                <span class="nexus-tag">FAQs</span>
                <span class="nexus-tag">ERP</span>
                <span class="nexus-tag">Manuals</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-teal">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">P2</div>
            </div>
            <h3 class="nexus-card-title">Protect</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Access-controlled profiles</div>
            <p class="nexus-card-text">
                Knowledge Profiles expose only the approved knowledge surface for each business
                situation. Access Categories bundle policies that control what each identity
                type can retrieve.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Knowledge Profile</span>
                <span class="nexus-tag nexus-tag-teal">Access Policy</span>
            </div>
        </div>

        <div class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">P3</div>
            </div>
            <h3 class="nexus-card-title">Qualify</h3>
            <div class="nexus-card-subtitle">Identity resolution</div>
            <p class="nexus-card-text">
                The visitor becomes a resolved identity — Public Visitor, Verified Customer,
                Internal Employee, Business Partner, Vendor, or Training User — before any
                knowledge is delivered.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">OTP Verification</span>
                <span class="nexus-tag">Identity Type</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-purple">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">P4</div>
            </div>
            <h3 class="nexus-card-title">Behaviour</h3>
            <div class="nexus-card-subtitle">AI Agent Profile</div>
            <p class="nexus-card-text">
                The AI follows a configured profile — persona, tone, fallback rules, confidence
                threshold, and escalation policy — before producing any response.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Persona</span>
                <span class="nexus-tag nexus-tag-purple">Tone</span>
                <span class="nexus-tag nexus-tag-purple">Fallback</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-teal nexus-card-teal-bg">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">P5</div>
            </div>
            <h3 class="nexus-card-title">Escalate</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Human handover</div>
            <p class="nexus-card-text">
                When AI should not continue, it escalates to the right human team — with
                tenant, identity, channel, and knowledge context fully preserved in the handover.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Handover</span>
                <span class="nexus-tag nexus-tag-teal">Context Preserved</span>
            </div>
        </div>

    </section>

    <!-- SECTION 03: OPERATING WORKSPACES -->
    <div class="nexus-section">
        <div>
            <div class="nexus-section-badge">03 - Operating Workspaces</div>
            <h3 class="nexus-section-title">Navigate Nexus Orbit</h3>
            <p class="nexus-section-text">
                Four purpose-built workspaces cover the full platform lifecycle — knowledge
                preparation, live chat operations, tenant setup, and runtime validation.
                Each workspace is focused on a specific operating area.
            </p>
        </div>
    </div>

    <section class="nexus-card-grid">

        <a href="/app/nexus-studio" class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">ST</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Nexus Studio</h3>
            <div class="nexus-card-subtitle">Knowledge operations</div>
            <p class="nexus-card-text">
                Feed sources, classify knowledge, review chunks, assign access policies,
                test coverage, validate answers, and publish approved knowledge for governed
                AI retrieval.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Sources</span>
                <span class="nexus-tag">Chunks</span>
                <span class="nexus-tag">Approval</span>
            </div>
        </a>

        <a href="/app/nexus-live" class="nexus-card nexus-card-teal">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">LV</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Nexus Live</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Chat operations</div>
            <p class="nexus-card-text">
                Operate live conversations, monitor AI responses, manage identity verification,
                configure routing and agent profiles, and handle human escalation and handover.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Live Chat</span>
                <span class="nexus-tag nexus-tag-teal">Escalation</span>
                <span class="nexus-tag nexus-tag-teal">Routing</span>
            </div>
        </a>

        <a href="/app/nexus-administration" class="nexus-card nexus-card-purple">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">AD</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Nexus Administration</h3>
            <div class="nexus-card-subtitle">Tenant configuration</div>
            <p class="nexus-card-text">
                Configure tenants and the minimum defaults required for chat — business unit,
                channel, widget, access governance, and readiness indicators.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Tenant</span>
                <span class="nexus-tag nexus-tag-purple">Defaults</span>
                <span class="nexus-tag nexus-tag-purple">Readiness</span>
            </div>
        </a>

    </section>

    <!-- SECTION 04: DELIVERY CHANNELS -->
    <div class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">04 - Delivery Channels</div>
            <h3 class="nexus-section-title">How Nexus Reaches Users</h3>
            <p class="nexus-section-text">
                The same governed knowledge engine powers multiple delivery surfaces — public
                website chat, internal desk chat, programmatic API access, and ERP-aware
                AI operations through Nexy.
            </p>
        </div>
    </div>

    <section class="nexus-card-grid">

        <div class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">WD</div>
            </div>
            <h3 class="nexus-card-title">Website AI Chat Widget</h3>
            <div class="nexus-card-subtitle">Public knowledge delivery</div>
            <p class="nexus-card-text">
                Embed the Nexus chat widget on any website or portal. Visitors interact with
                tenant-scoped AI knowledge. Anonymous public access is supported — identity
                verification is optional per category.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Website</span>
                <span class="nexus-tag">Portal</span>
                <span class="nexus-tag">Public</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-teal">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">IN</div>
            </div>
            <h3 class="nexus-card-title">Internal Desk Chat</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Frappe-native employee access</div>
            <p class="nexus-card-text">
                Desk users access governed knowledge through the internal Frappe chat interface.
                Full access governance applies — employees see only their approved knowledge scope.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Internal</span>
                <span class="nexus-tag nexus-tag-teal">Employee</span>
                <span class="nexus-tag nexus-tag-teal">ERP-Aware</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-purple">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">AP</div>
            </div>
            <h3 class="nexus-card-title">Knowledge Q&amp;A API</h3>
            <div class="nexus-card-subtitle">Programmatic governed retrieval</div>
            <p class="nexus-card-text">
                Access governed knowledge programmatically. Applications retrieve AI-powered
                answers through the same policy-controlled retrieval pipeline used by chat.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">API</span>
                <span class="nexus-tag nexus-tag-purple">Integration</span>
                <span class="nexus-tag nexus-tag-purple">Governed</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-orange">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-orange">NX</div>
            </div>
            <h3 class="nexus-card-title">Nexy — AI Candidate</h3>
            <div class="nexus-card-subtitle">ERP-aware AI operations</div>
            <p class="nexus-card-text">
                Flagship Nexus candidate operating on Orbit and Agentic — customer care, sales
                orchestration, ERP guidance, SOP execution, and business analytics in one product.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">ERP</span>
                <span class="nexus-tag">Sales</span>
                <span class="nexus-tag">SOP</span>
                <span class="nexus-tag">Analytics</span>
            </div>
        </div>

    </section>

    <!-- SECTION 05: FULL CAPABILITY MAP -->
    <div class="nexus-section">
        <div>
            <div class="nexus-section-badge">05 - Capability Map</div>
            <h3 class="nexus-section-title">Platform Capabilities</h3>
            <p class="nexus-section-text">
                The complete set of enterprise AI capabilities — available through tenant
                configuration, knowledge governance, and identity-controlled access routing.
            </p>
        </div>
    </div>

    <div class="nexus-capability-panel">
        <div class="nexus-capability-grid">

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">KS</div>
                <p class="nexus-capability-text">Knowledge source intake and ownership tracking</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">CL</div>
                <p class="nexus-capability-text">Tenant, business unit, and context classification</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">CK</div>
                <p class="nexus-capability-text">Chunk processing and vector embedding generation</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">RT</div>
                <p class="nexus-capability-text">Retrieval-augmented generation with access policy filtering</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">AP</div>
                <p class="nexus-capability-text">Access policy assignment at knowledge chunk level</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">KP</div>
                <p class="nexus-capability-text">Knowledge Profiles controlling retrievable knowledge surface</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">IV</div>
                <p class="nexus-capability-text">Identity verification via email OTP and registered email</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">IT</div>
                <p class="nexus-capability-text">Identity type resolution — Public, Customer, Employee, Partner</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">CH</div>
                <p class="nexus-capability-text">Category and identity routing to AI Agent Profile</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">AI</div>
                <p class="nexus-capability-text">AI Agent Profile — persona, tone, fallback, and confidence</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">ES</div>
                <p class="nexus-capability-text">Human escalation and handover with context preserved</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">LC</div>
                <p class="nexus-capability-text">Live conversation monitoring and control console</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">KG</div>
                <p class="nexus-capability-text">Knowledge gap detection — reactive and proactive</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">VL</div>
                <p class="nexus-capability-text">Retrieval, routing, and access policy validation</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">AG</div>
                <p class="nexus-capability-text">Agentic LLM workflows with tool use and reasoning</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">NX</div>
                <p class="nexus-capability-text">Nexy — multi-role flagship AI candidate on Orbit + Agentic</p>
            </div>

        </div>
    </div>

</div>
"""


STUDIO_HTML = """
<div class="nexus-ws nexus-studio-ws">

    <!-- WEBSITE-STYLE HERO -->
    <div class="nxl-ws-hero">

        <div class="nxl-ws-panel nxl-ws-panel-blue">
            <span class="nxl-ws-kicker">KNOWLEDGE OPERATIONS</span>
            <div class="nxl-ws-title-row">
                <div class="nxl-ws-icon-box nxl-ws-icon-box-teal">
                    <svg viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M5 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v18l-8-4-8 4V6z" stroke="#ffffff" stroke-width="2" stroke-linejoin="round"/>
                        <path d="M10 10h7M10 14h5" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </div>
                <h1 class="nxl-ws-h1">Nexus Studio</h1>
            </div>
            <p class="nxl-ws-lead">
                Workspace for preparing tenant knowledge for governed AI chat. Feed sources,
                classify scope, assign access policies, process chunks, validate answers, and publish
                approved knowledge.
            </p>
            <div class="nxl-ws-chips">
                <span class="nxl-ws-chip">Source Intake</span>
                <span class="nxl-ws-chip">Knowledge Units</span>
                <span class="nxl-ws-chip">Access Policies</span>
                <span class="nxl-ws-chip">Validation</span>
                <span class="nxl-ws-chip">Publishing</span>
            </div>
        </div>

        <div class="nxl-ws-panel nxl-ws-panel-teal">
            <span class="nxl-ws-kicker nxl-ws-kicker-teal">KNOWLEDGE WORKBENCH</span>
            <h2 class="nxl-ws-panel-title">Quick Access</h2>
            <div class="nxl-ws-links">
                <a class="nxl-ws-link-item" href="/app/nexus-studio-page">
                    <div class="nxl-ws-link-icon">ST</div>
                    <div>Studio Console<span class="nxl-ws-link-desc">Operational command center</span></div>
                </a>
                <a class="nxl-ws-link-item" href="/app/nexus-knowledge-source">
                    <div class="nxl-ws-link-icon">KS</div>
                    <div>Knowledge Sources<span class="nxl-ws-link-desc">Document &amp; feed intake</span></div>
                </a>
                <a class="nxl-ws-link-item" href="/app/nexus-knowledge-unit">
                    <div class="nxl-ws-link-icon">KU</div>
                    <div>Knowledge Units<span class="nxl-ws-link-desc">Classified content records</span></div>
                </a>
                <a class="nxl-ws-link-item" href="/app/nexus-knowledge-explorer">
                    <div class="nxl-ws-link-icon">KE</div>
                    <div>Knowledge Explorer<span class="nxl-ws-link-desc">Browse &amp; inspect knowledge</span></div>
                </a>
            </div>
        </div>

    </div>

    <!-- STUDIO SUMMARY STRIP -->
    <section class="nexus-context-grid">

        <div class="nexus-context-card nexus-context-card-primary">
            <div class="nexus-context-icon nexus-context-icon-large">KN</div>
            <div>
                <h3 class="nexus-context-title nexus-context-title-large">Knowledge Operations Workspace</h3>
                <p class="nexus-context-text">Prepare tenant knowledge for reliable, cited, policy-aware retrieval.</p>
            </div>
        </div>

        <div class="nexus-context-card nexus-context-card-teal">
            <div class="nexus-context-icon nexus-context-icon-mint">IN</div>
            <div>
                <h4 class="nexus-context-title">Feed Sources</h4>
                <p class="nexus-context-text">Bring in documents, website pages, FAQs, ERP records, and internal notes.</p>
            </div>
        </div>

        <div class="nexus-context-card">
            <div class="nexus-context-icon">GV</div>
            <div>
                <h4 class="nexus-context-title">Govern Knowledge</h4>
                <p class="nexus-context-text">Apply tenant, business unit, public context, approval, and access policy scope.</p>
            </div>
        </div>

        <div class="nexus-context-card nexus-context-card-teal-soft">
            <div class="nexus-context-icon nexus-context-icon-teal">VA</div>
            <div>
                <h4 class="nexus-context-title">Validate Answers</h4>
                <p class="nexus-context-text">Test retrieval quality, grounding, citations, confidence, and policy behavior.</p>
            </div>
        </div>

    </section>

    <!-- SECTION: QUICK ACCESS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge">01 - Studio Entry Points</div>

            <h3 class="nexus-section-title">Knowledge Workbench</h3>

            <p class="nexus-section-text">
                Open the Studio console or jump directly into sources, units, chunks, and validation records.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <a href="/app/nexus-studio-page" class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">ST</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>

            <h3 class="nexus-card-title">Studio Console</h3>
            <div class="nexus-card-subtitle">Operational command center</div>

            <p class="nexus-card-text">
                Review tenant-scoped knowledge status, feed sources, process records, and run validation.
            </p>

            <div class="nexus-tag-row">
                <span class="nexus-tag">Dashboard</span>
                <span class="nexus-tag">Processing</span>
                <span class="nexus-tag">Testing</span>
            </div>
        </a>

        <a href="/app/nexus-knowledge-source" class="nexus-card nexus-card-teal">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">SO</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>

            <h3 class="nexus-card-title">Knowledge Sources</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Source intake</div>

            <p class="nexus-card-text">
                Register and track source material before it is converted into retrievable knowledge.
            </p>

            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal-strong">Documents</span>
                <span class="nexus-tag nexus-tag-teal-strong">Web</span>
                <span class="nexus-tag nexus-tag-teal-strong">Records</span>
            </div>
        </a>

        <a href="/app/nexus-knowledge-unit" class="nexus-card nexus-card-purple">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">KU</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>

            <h3 class="nexus-card-title">Knowledge Units</h3>
            <div class="nexus-card-subtitle">Classified knowledge</div>

            <p class="nexus-card-text">
                Maintain approved units with tenant scope, business unit scope, public context, and access policy.
            </p>

            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Scope</span>
                <span class="nexus-tag nexus-tag-purple">Policy</span>
                <span class="nexus-tag nexus-tag-purple">Approval</span>
            </div>
        </a>

        <a href="/app/nexus-knowledge-gap-review" class="nexus-card nexus-card-teal">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">KG</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>

            <h3 class="nexus-card-title">Knowledge Gap Review</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Gap analysis</div>

            <p class="nexus-card-text">
                Review detected knowledge gaps, assess relevance, and create new Knowledge Units to close coverage gaps.
            </p>

            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal-strong">Reactive</span>
                <span class="nexus-tag nexus-tag-teal-strong">Proactive</span>
                <span class="nexus-tag nexus-tag-teal-strong">Review</span>
            </div>
        </a>

    </section>

    <!-- SECTION: KNOWLEDGE ACCESS GOVERNANCE -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">02 - Knowledge Access Governance</div>
            <h2 class="nexus-section-title">Access Configuration</h2>
            <p class="nexus-section-text">
                Knowledge Profiles define what knowledge is accessible per identity type. Access Categories
                group the policies that control retrieval. Access Policies tag individual chunks — assigned
                in Studio and enforced during chat and API retrieval.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <a class="nexus-card nexus-card-teal nexus-card-teal-bg" href="/app/nexus-profile-access-allocation">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">KA</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Knowledge Access Manager</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Knowledge Profile access configuration</div>
            <p class="nexus-card-text">
                Assign Access Categories to Knowledge Profiles. Each profile controls what knowledge
                is available when an identity type resolves to that profile during chat retrieval.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Knowledge Profile</span>
                <span class="nexus-tag nexus-tag-teal">Access Category</span>
                <span class="nexus-tag nexus-tag-teal">Retrieval</span>
            </div>
        </a>

        <a class="nexus-card nexus-card-purple" href="/app/nexus-access-category">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">AC</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Access Categories</h3>
            <div class="nexus-card-subtitle">Policy groupings for knowledge retrieval</div>
            <p class="nexus-card-text">
                Define access categories that bundle allowed access policies. Categories are assigned
                to Knowledge Profiles to grant their bundled policy set at retrieval time.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Category</span>
                <span class="nexus-tag nexus-tag-purple">Policies</span>
                <span class="nexus-tag nexus-tag-purple">Grouping</span>
            </div>
        </a>

        <a class="nexus-card" href="/app/nexus-access-policy">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">AP</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Access Policies</h3>
            <div class="nexus-card-subtitle">Knowledge chunk access rules</div>
            <p class="nexus-card-text">
                Maintain access policies matched against knowledge chunks during retrieval.
                Policies are assigned to chunks in Studio and enforced at runtime.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Policy</span>
                <span class="nexus-tag">Chunks</span>
                <span class="nexus-tag">Runtime</span>
            </div>
        </a>

    </section>

    <!-- SECTION: BOUNDARY -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">03 - Studio Boundary</div>

            <h3 class="nexus-section-title">Where Nexus Studio Fits</h3>

            <p class="nexus-section-text">
                Studio owns the knowledge layer. Administration manages tenants and tenant configuration.
                Nexus Live operates conversations. Platform validation proves routing, grounding, access,
                and readiness.
            </p>
        </div>
    </section>

    <section class="nexus-capability-panel">
        <div class="nexus-capability-grid">

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">FD</div>
                <p class="nexus-capability-text">Source feeding<br>and classification</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">SC</div>
                <p class="nexus-capability-text">Tenant and business<br>unit scope</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">AP</div>
                <p class="nexus-capability-text">Access policy<br>assignment</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">CK</div>
                <p class="nexus-capability-text">Chunk and embedding<br>processing</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">RT</div>
                <p class="nexus-capability-text">Retrieval and answer<br>validation</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">PB</div>
                <p class="nexus-capability-text">Approved knowledge<br>publishing</p>
            </div>

        </div>
    </section>

    <!-- SECTION: LIFECYCLE -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge">04 - Knowledge Lifecycle</div>

            <h3 class="nexus-section-title">From Source To Approved Answer</h3>

            <p class="nexus-section-text">
                Studio keeps the knowledge path explicit so website chat, internal chat, and API calls
                all retrieve from the same governed knowledge base.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <div class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">01</div>
            </div>
            <h3 class="nexus-card-title">Feed</h3>
            <p class="nexus-card-text">Capture trusted source material and keep source ownership visible.</p>
        </div>

        <div class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">02</div>
            </div>
            <h3 class="nexus-card-title">Classify</h3>
            <p class="nexus-card-text">Apply tenant, business unit, public context, category, and policy metadata.</p>
        </div>

        <div class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">03</div>
            </div>
            <h3 class="nexus-card-title">Process</h3>
            <p class="nexus-card-text">Generate chunks and embeddings for retrieval-ready knowledge.</p>
        </div>

        <div class="nexus-card nexus-card-teal">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">04</div>
            </div>
            <h3 class="nexus-card-title">Validate</h3>
            <p class="nexus-card-text">Run test cases, inspect query logs, and confirm grounded answers.</p>
        </div>

        <div class="nexus-card nexus-card-purple">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">05</div>
            </div>
            <h3 class="nexus-card-title">Publish</h3>
            <p class="nexus-card-text">Approve and release knowledge for governed runtime use.</p>
        </div>

        <a href="/app/nexus-knowledge-explorer" class="nexus-card nexus-card-indigo">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-indigo">KE</div>
                <div class="nexus-card-arrow nexus-card-arrow-indigo">-&gt;</div>
            </div>

            <h3 class="nexus-card-title">Knowledge Explorer</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-indigo">Browse &amp; inspect knowledge</div>

            <p class="nexus-card-text">
                Explore all knowledge fed into the system — grouped by context, sub-context, topic and entity.
                Preview content, check embedding coverage, access policies and publishing status.
            </p>

            <div class="nexus-tag-row">
                <span class="nexus-tag">Browse</span>
                <span class="nexus-tag">Inspect</span>
                <span class="nexus-tag">Facets</span>
            </div>
        </a>

    </section>

    <!-- SECTION: RECORDS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">05 - Studio Records</div>

            <h3 class="nexus-section-title">Knowledge Records</h3>

            <p class="nexus-section-text">
                Use these doctypes for source intake, knowledge preparation, validation, and runtime review.
            </p>
        </div>
    </section>

    <section class="nexus-link-grid">
        <a href="/app/nexus-knowledge-source" class="nexus-link-card">
            <span class="nexus-link-icon">SO</span>
            <span class="nexus-link-label">Nexus Knowledge Source</span>
            <span class="nexus-link-arrow">-&gt;</span>
        </a>

        <a href="/app/nexus-knowledge-unit" class="nexus-link-card">
            <span class="nexus-link-icon">KU</span>
            <span class="nexus-link-label">Nexus Knowledge Unit</span>
            <span class="nexus-link-arrow">-&gt;</span>
        </a>

        <a href="/app/nexus-knowledge-chunk" class="nexus-link-card">
            <span class="nexus-link-icon">KC</span>
            <span class="nexus-link-label">Nexus Knowledge Chunk</span>
            <span class="nexus-link-arrow">-&gt;</span>
        </a>

        <a href="/app/nexus-knowledge-test-case" class="nexus-link-card">
            <span class="nexus-link-icon">TC</span>
            <span class="nexus-link-label">Nexus Knowledge Test Case</span>
            <span class="nexus-link-arrow">-&gt;</span>
        </a>

        <a href="/app/nexus-knowledge-test-run" class="nexus-link-card">
            <span class="nexus-link-icon">TR</span>
            <span class="nexus-link-label">Nexus Knowledge Test Run</span>
            <span class="nexus-link-arrow">-&gt;</span>
        </a>

        <a href="/app/nexus-query-log" class="nexus-link-card">
            <span class="nexus-link-icon">QL</span>
            <span class="nexus-link-label">Nexus Query Log</span>
            <span class="nexus-link-arrow">-&gt;</span>
        </a>

        <a href="/app/nexus-knowledge-gap-review" class="nexus-link-card">
            <span class="nexus-link-icon">KG</span>
            <span class="nexus-link-label">Knowledge Gap Review</span>
            <span class="nexus-link-arrow">-&gt;</span>
        </a>
    </section>

</div>
"""


ADMIN_HTML = """
<div class="nexus-ws nexus-admin-ws">

    <!-- WEBSITE-STYLE HERO -->
    <div class="nxl-ws-hero">

        <div class="nxl-ws-panel nxl-ws-panel-blue">
            <span class="nxl-ws-kicker">TENANT CONFIGURATION</span>
            <div class="nxl-ws-title-row">
                <div class="nxl-ws-icon-box">
                    <svg viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="15" cy="15" r="4" stroke="#ffffff" stroke-width="2"/>
                        <path d="M15 3v3M15 24v3M3 15h3M24 15h3M6.2 6.2l2.1 2.1M21.7 21.7l2.1 2.1M6.2 23.8l2.1-2.1M21.7 8.3l2.1-2.1" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </div>
                <h1 class="nxl-ws-h1">Nexus Administration</h1>
            </div>
            <p class="nxl-ws-lead">
                Administration is the tenant configuration workspace. Select a tenant, maintain the
                minimum defaults required for chat, connect master records, and verify
                readiness before knowledge is exposed through live or internal channels.
            </p>
            <div class="nxl-ws-chips">
                <span class="nxl-ws-chip">Tenant</span>
                <span class="nxl-ws-chip">Business Unit</span>
                <span class="nxl-ws-chip">Channels</span>
                <span class="nxl-ws-chip">Readiness</span>
            </div>
        </div>

        <div class="nxl-ws-panel nxl-ws-panel-purple">
            <span class="nxl-ws-kicker nxl-ws-kicker-purple">QUICK SETUP</span>
            <h2 class="nxl-ws-panel-title">Configuration Access</h2>
            <div class="nxl-ws-links">
                <a class="nxl-ws-link-item nxl-ws-link-item-purple" href="/app/nexus-admin">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-purple">AD</div>
                    <div>Admin Console<span class="nxl-ws-link-desc">Tenant configuration page</span></div>
                </a>
                <a class="nxl-ws-link-item nxl-ws-link-item-purple" href="/app/nexus-tenant">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-purple">TN</div>
                    <div>Tenant Registry<span class="nxl-ws-link-desc">Highest isolation boundary</span></div>
                </a>
                <a class="nxl-ws-link-item nxl-ws-link-item-purple" href="/app/nexus-business-unit">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-purple">BU</div>
                    <div>Business Units<span class="nxl-ws-link-desc">Default scope master</span></div>
                </a>
                <a class="nxl-ws-link-item nxl-ws-link-item-purple" href="/app/nexus-tenant">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-purple">SD</div>
                    <div>Seed Tenant Defaults<span class="nxl-ws-link-desc">Actions &#x2192; Setup Defaults</span></div>
                </a>
            </div>
        </div>

    </div>

    <!-- CONFIGURATION SUMMARY STRIP -->
    <section class="nexus-context-grid">

        <div class="nexus-context-card nexus-context-card-primary">
            <div class="nexus-context-icon nexus-context-icon-large">TN</div>
            <div>
                <h3 class="nexus-context-title nexus-context-title-large">Tenant Configuration Workspace</h3>
                <p class="nexus-context-text">One place to manage tenant defaults and readiness for runtime use.</p>
            </div>
        </div>

        <div class="nexus-context-card">
            <div class="nexus-context-icon">BU</div>
            <div>
                <h3 class="nexus-context-title">Business Scope</h3>
                <p class="nexus-context-text">Use Business Unit as a master record, not a free text value.</p>
            </div>
        </div>


        <div class="nexus-context-card nexus-context-card-teal-soft">
            <div class="nexus-context-icon nexus-context-icon-teal">RD</div>
            <div>
                <h3 class="nexus-context-title">Readiness</h3>
                <p class="nexus-context-text">Confirm live chat, testing, approval, and guard settings.</p>
            </div>
        </div>

    </section>

    <!-- SECTION: NEW TENANT ONBOARDING -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">00 - New Tenant Onboarding</div>
            <h2 class="nexus-section-title">Seed Tenant Defaults</h2>
            <p class="nexus-section-text">
                After creating a new tenant, open its record and click <strong>Actions &#x2192; Setup Defaults</strong>
                to provision channels, categories, agent profile, access governance, and Sales Companion in one step.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <a class="nexus-card nexus-card-teal nexus-card-teal-bg" href="/app/nexus-tenant">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">SD</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Seed Tenant Defaults</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Actions &#x2192; Setup Defaults</div>
            <p class="nexus-card-text">
                Open any Nexus Tenant record and click <strong>Actions &#x2192; Setup Defaults</strong>.
                Provisions the default chat channel, chat category, AI agent profile,
                access governance, identity profile, routing, tenant configuration, and Sales Companion.
                Existing records are never overwritten.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Chat Channel</span>
                <span class="nexus-tag nexus-tag-teal">Agent Profile</span>
                <span class="nexus-tag nexus-tag-teal">Access Governance</span>
                <span class="nexus-tag nexus-tag-teal">Sales Companion</span>
            </div>
        </a>

    </section>

    <!-- SECTION: QUICK ACCESS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge">01 - Administration Entry Points</div>
            <h2 class="nexus-section-title">Tenant Setup</h2>
            <p class="nexus-section-text">
                Open the simplified admin console or manage the master records used by tenant configuration.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <a class="nexus-card nexus-card-teal nexus-card-teal-bg" href="/app/nexus-admin">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">AD</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Admin Console</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Tenant configuration page</div>
            <p class="nexus-card-text">
                Select the tenant, maintain default business unit, chat channel,
                widget settings, safety settings, and readiness values.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Open Page</span>
                <span class="nexus-tag nexus-tag-teal">Defaults</span>
                <span class="nexus-tag nexus-tag-teal">Readiness</span>
            </div>
        </a>

        <a class="nexus-card nexus-card-purple" href="/app/nexus-tenant">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">TN</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Tenant Registry</h3>
            <div class="nexus-card-subtitle">Highest isolation boundary</div>
            <p class="nexus-card-text">
                Review tenant records that own knowledge, configuration defaults, query logs,
                public widgets, and runtime boundaries.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Tenant</span>
                <span class="nexus-tag nexus-tag-purple">Boundary</span>
                <span class="nexus-tag nexus-tag-purple">Isolation</span>
            </div>
        </a>

        <a class="nexus-card" href="/app/nexus-settings">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">GS</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Nexus Settings</h3>
            <div class="nexus-card-subtitle">Global platform settings</div>
            <p class="nexus-card-text">
                Review global values that apply across the platform. Tenant-specific behavior
                should be maintained through the tenant configuration console.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Global</span>
                <span class="nexus-tag">Settings</span>
                <span class="nexus-tag">Platform</span>
            </div>
        </a>

    </section>

    <!-- SECTION: REQUIRED MASTERS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">02 - Master Records</div>
            <h2 class="nexus-section-title">Configuration Masters</h2>
            <p class="nexus-section-text">
                These records keep tenant configuration link-based and stable instead of relying on text fields.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <a class="nexus-card" href="/app/nexus-business-unit">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">BU</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Business Units</h3>
            <div class="nexus-card-subtitle">Business scope master</div>
            <p class="nexus-card-text">
                Maintain approved business unit records used by tenant defaults, knowledge scope,
                retrieval filtering, and reporting.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Master</span>
                <span class="nexus-tag">Scope</span>
                <span class="nexus-tag">Knowledge</span>
            </div>
        </a>


        <a class="nexus-card nexus-card-purple" href="/app/nexus-live-channel">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">CH</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Live Channels</h3>
            <div class="nexus-card-subtitle">Chat channel defaults</div>
            <p class="nexus-card-text">
                Maintain the channels selected by tenant configuration for public website chat
                and internal chat.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Chat</span>
                <span class="nexus-tag nexus-tag-purple">Channel</span>
            </div>
        </a>


    </section>


    <!-- SECTION: BOUNDARY -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge">03 - Administration Boundary</div>
            <h2 class="nexus-section-title">What Administration Owns</h2>
            <p class="nexus-section-text">
                Administration should stay simple: tenant records, tenant defaults, linked masters,
                readiness indicators, and safety switches. Knowledge creation belongs to Studio.
            </p>
        </div>
    </section>

    <section class="nexus-capability-panel">
        <div class="nexus-capability-grid">

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">TN</div>
                <p class="nexus-capability-text">Tenant registry and isolation boundary</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">BU</div>
                <p class="nexus-capability-text">Default business unit selected from master records</p>
            </div>


            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">CH</div>
                <p class="nexus-capability-text">Default chat channel selection</p>
            </div>


            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">WD</div>
                <p class="nexus-capability-text">Website widget enablement, title, welcome message, and brand color</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">SG</div>
                <p class="nexus-capability-text">Strict tenant mode and identity safeguard settings</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">RD</div>
                <p class="nexus-capability-text">Readiness indicators for testing, live chat, and production use</p>
            </div>

        </div>
    </section>

</div>
"""


PLATFORM_HTML = """
<div class="nexus-ws nexus-platform-ws">

    <!-- WEBSITE-STYLE HERO -->
    <div class="nxl-ws-hero">

        <div class="nxl-ws-panel nxl-ws-panel-blue">
            <span class="nxl-ws-kicker">VALIDATION AND DIAGNOSTICS</span>
            <div class="nxl-ws-title-row">
                <div class="nxl-ws-icon-box">
                    <svg viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 15h4l3-8 4 16 3-10 3 5h7" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </div>
                <h1 class="nxl-ws-h1">Nexus Platform</h1>
            </div>
            <p class="nxl-ws-lead">
                Technical assurance workspace for the Nexus runtime. Use it to inspect query logs,
                validate retrieval and answer behavior, confirm access policy enforcement, review
                integration readiness, and prove release confidence for public and internal chat.
            </p>
            <div class="nxl-ws-chips">
                <span class="nxl-ws-chip">Runtime Diagnostics</span>
                <span class="nxl-ws-chip">Query Logs</span>
                <span class="nxl-ws-chip">Retrieval Validation</span>
                <span class="nxl-ws-chip">Access Checks</span>
                <span class="nxl-ws-chip">Release Readiness</span>
            </div>
        </div>

        <div class="nxl-ws-panel nxl-ws-panel-purple">
            <span class="nxl-ws-kicker nxl-ws-kicker-purple">QUICK DIAGNOSTICS</span>
            <h2 class="nxl-ws-panel-title">Assurance Tools</h2>
            <div class="nxl-ws-links">
                <a class="nxl-ws-link-item nxl-ws-link-item-purple" href="/app/nexus-query-log">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-purple">QL</div>
                    <div>Query Logs<span class="nxl-ws-link-desc">Runtime trace &amp; evidence</span></div>
                </a>
                <a class="nxl-ws-link-item nxl-ws-link-item-purple" href="/app/nexus-chat-workflow-tester">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-purple">WF</div>
                    <div>Workflow Tester<span class="nxl-ws-link-desc">Validate chat routing</span></div>
                </a>
                <a class="nxl-ws-link-item nxl-ws-link-item-purple" href="/app/nexus-live-studio">
                    <div class="nxl-ws-link-icon nxl-ws-link-icon-purple">LS</div>
                    <div>Live Studio<span class="nxl-ws-link-desc">Configuration readiness</span></div>
                </a>
            </div>
        </div>

    </div>

    <!-- PLATFORM SUMMARY STRIP -->
    <section class="nexus-context-grid">

        <div class="nexus-context-card nexus-context-card-primary">
            <div class="nexus-context-icon nexus-context-icon-large">VL</div>
            <div>
                <h3 class="nexus-context-title nexus-context-title-large">Runtime Assurance Workspace</h3>
                <p class="nexus-context-text">Observe and validate the behavior of tenant-scoped AI experiences.</p>
            </div>
        </div>

        <div class="nexus-context-card">
            <div class="nexus-context-icon">LG</div>
            <div>
                <h3 class="nexus-context-title">Observe</h3>
                <p class="nexus-context-text">Inspect query logs, selected sources, denied chunks, and confidence signals.</p>
            </div>
        </div>

        <div class="nexus-context-card nexus-context-card-teal">
            <div class="nexus-context-icon nexus-context-icon-mint">TS</div>
            <div>
                <h3 class="nexus-context-title">Test</h3>
                <p class="nexus-context-text">Run test cases and test runs for retrieval, grounding, and access behavior.</p>
            </div>
        </div>

        <div class="nexus-context-card nexus-context-card-teal-soft">
            <div class="nexus-context-icon nexus-context-icon-teal">RD</div>
            <div>
                <h3 class="nexus-context-title">Release</h3>
                <p class="nexus-context-text">Confirm readiness before exposing knowledge to website or internal users.</p>
            </div>
        </div>

    </section>

    <!-- SECTION: QUICK ACCESS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge">01 - Platform Entry Points</div>
            <h2 class="nexus-section-title">Diagnostics Workbench</h2>
            <p class="nexus-section-text">
                Jump into the records that show how the runtime answered, what it retrieved,
                what it blocked, and whether the result is ready for production use.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <a class="nexus-card nexus-card-teal nexus-card-teal-bg" href="/app/nexus-query-log">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">QL</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Query Logs</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Runtime evidence</div>
            <p class="nexus-card-text">
                Review questions, resolved tenant scope, selected sources, answer status,
                confidence, citations, denied results, and runtime trace data.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Trace</span>
                <span class="nexus-tag nexus-tag-teal">Sources</span>
                <span class="nexus-tag nexus-tag-teal">Confidence</span>
            </div>
        </a>

        <a class="nexus-card nexus-card-purple" href="/app/nexus-knowledge-test-case">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">TC</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Knowledge Test Cases</h3>
            <div class="nexus-card-subtitle">Expected runtime behavior</div>
            <p class="nexus-card-text">
                Define expected answers, source expectations, access expectations, and grounded
                behavior for public chat, internal chat, and future API calls.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Expected</span>
                <span class="nexus-tag nexus-tag-purple">Grounding</span>
                <span class="nexus-tag nexus-tag-purple">Access</span>
            </div>
        </a>

        <a class="nexus-card" href="/app/nexus-knowledge-test-run">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">TR</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Knowledge Test Runs</h3>
            <div class="nexus-card-subtitle">Validation execution</div>
            <p class="nexus-card-text">
                Review test execution, pass/fail results, answer quality, citation quality,
                access behavior, and readiness evidence.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Run</span>
                <span class="nexus-tag">Pass/Fail</span>
                <span class="nexus-tag">Evidence</span>
            </div>
        </a>

    </section>

    <!-- SECTION: PLATFORM FOCUS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">02 - Platform Focus</div>
            <h2 class="nexus-section-title">Runtime Behavior To Prove</h2>
            <p class="nexus-section-text">
                Platform does not configure tenants or create knowledge. It validates that the
                configured tenant and approved knowledge behave correctly at runtime.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <div class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">RT</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Routing Resolution</h3>
            <div class="nexus-card-subtitle">Category, identity, profile, policy</div>
            <p class="nexus-card-text">
                Confirm the runtime resolves the correct tenant, channel, chat category,
                identity, agent profile, access category, and access policy without fallback.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Routing</span>
                <span class="nexus-tag">Identity</span>
                <span class="nexus-tag">Policy</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-teal nexus-card-teal-bg">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">KG</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Retrieval Grounding</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Approved source behavior</div>
            <p class="nexus-card-text">
                Confirm answers come from approved knowledge, include required citations,
                and reject unsupported questions when knowledge is not sufficient.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Approved</span>
                <span class="nexus-tag nexus-tag-teal">Cited</span>
                <span class="nexus-tag nexus-tag-teal">Grounded</span>
            </div>
        </div>

        <div class="nexus-card nexus-card-purple">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">AC</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Access Enforcement</h3>
            <div class="nexus-card-subtitle">Allow and deny behavior</div>
            <p class="nexus-card-text">
                Verify that access policies, role boundaries, public/internal scope, and
                System Manager visibility behave exactly as intended.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Allowed</span>
                <span class="nexus-tag nexus-tag-purple">Denied</span>
                <span class="nexus-tag nexus-tag-purple">Audited</span>
            </div>
        </div>

        <div class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">IN</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Integration Readiness</h3>
            <div class="nexus-card-subtitle">Website, internal chat, API</div>
            <p class="nexus-card-text">
                Validate public website chat, internal user chat, widget settings,
                and API-facing behavior against the same routing and access model.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Website</span>
                <span class="nexus-tag">Internal</span>
                <span class="nexus-tag">API</span>
            </div>
        </div>

    </section>

    <!-- SECTION: CONTROLS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge">03 - Assurance Controls</div>
            <h2 class="nexus-section-title">What Platform Helps You Control</h2>
            <p class="nexus-section-text">
                Platform is the evidence layer for stability, correctness, access safety,
                and production readiness.
            </p>
        </div>
    </section>

    <section class="nexus-capability-panel">
        <div class="nexus-capability-grid">

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">LG</div>
                <p class="nexus-capability-text">Query logs, selected sources, answer status, and trace evidence</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">RT</div>
                <p class="nexus-capability-text">Runtime routing through category, identity, agent profile, and access policy</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">KG</div>
                <p class="nexus-capability-text">Grounded retrieval, approved knowledge, citations, and confidence checks</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">AC</div>
                <p class="nexus-capability-text">Access policy enforcement, denied chunks, and role-safe visibility</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">TC</div>
                <p class="nexus-capability-text">Test cases for chat, website, internal user, and API behavior</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">RD</div>
                <p class="nexus-capability-text">Readiness evidence before public or internal exposure</p>
            </div>

        </div>
    </section>

</div>
"""


LIVE_HTML = """
<div class="nexus-ws nexus-live-ws">

    <!-- WEBSITE-STYLE LIVE HERO -->
    <div class="nxl-ws-hero">

        <!-- Left panel: Nexus Live identity (blue) -->
        <div class="nxl-ws-panel nxl-ws-panel-blue">
            <span class="nxl-ws-kicker">LIVE CHAT OPERATIONS</span>
            <div class="nxl-ws-title-row">
                <div class="nxl-ws-icon-box">
                    <svg viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 7.5A4.5 4.5 0 0 1 7.5 3h15A4.5 4.5 0 0 1 27 7.5v10.5A4.5 4.5 0 0 1 22.5 22.5H18l-6 4.5v-4.5H7.5A4.5 4.5 0 0 1 3 18V7.5z" stroke="#ffffff" stroke-width="2" stroke-linejoin="round"/>
                        <circle cx="9.5" cy="13" r="1.75" fill="#ffffff"/>
                        <circle cx="15" cy="13" r="1.75" fill="#ffffff"/>
                        <circle cx="20.5" cy="13" r="1.75" fill="#ffffff"/>
                    </svg>
                </div>
                <h1 class="nxl-ws-h1">Nexus Live</h1>
            </div>
            <p class="nxl-ws-lead">
                Operations workspace for public website chat and internal user chat. Monitor
                live conversations, validate the routed chat flow, manage identity verification,
                support handover, and review the controls that connect chat categories,
                identity profiles, knowledge profiles, and access policies.
            </p>
            <div class="nxl-ws-chips">
                <span class="nxl-ws-chip">Public Website Chat</span>
                <span class="nxl-ws-chip">Internal User Chat</span>
                <span class="nxl-ws-chip">Identity Verification</span>
                <span class="nxl-ws-chip">Agent Routing</span>
                <span class="nxl-ws-chip">Knowledge Access</span>
            </div>
        </div>

        <!-- Right panel: Quick access (teal) -->
        <div class="nxl-ws-panel nxl-ws-panel-teal">
            <span class="nxl-ws-kicker nxl-ws-kicker-teal">QUICK ACCESS</span>
            <h2 class="nxl-ws-panel-title">Operations Console</h2>
            <div class="nxl-ws-links">
                <a class="nxl-ws-link-item" href="/app/nexus_live_console">
                    <div class="nxl-ws-link-icon">LC</div>
                    <div>
                        Live Console
                        <span class="nxl-ws-link-desc">Operate active conversations</span>
                    </div>
                </a>
                <a class="nxl-ws-link-item" href="/app/nexus_live_studio">
                    <div class="nxl-ws-link-icon">LS</div>
                    <div>
                        Live Studio
                        <span class="nxl-ws-link-desc">Configuration readiness</span>
                    </div>
                </a>
                <a class="nxl-ws-link-item" href="/app/nexus-chat-workflow-tester">
                    <div class="nxl-ws-link-icon">WF</div>
                    <div>
                        Workflow Tester
                        <span class="nxl-ws-link-desc">Validate routed chat flow</span>
                    </div>
                </a>
                <a class="nxl-ws-link-item" href="/app/nexus-channel-setup-wizard">
                    <div class="nxl-ws-link-icon">WZ</div>
                    <div>
                        Channel Setup Wizard
                        <span class="nxl-ws-link-desc">Guided channel configuration</span>
                    </div>
                </a>
            </div>
        </div>

    </div>

    <!-- LIVE SUMMARY STRIP -->
    <section class="nexus-context-grid">
        <a class="nexus-context-card nexus-context-card-primary" href="/app/nexus_live_console">
            <div class="nexus-context-icon nexus-context-icon-large">CH</div>
            <div>
                <h3 class="nexus-context-title nexus-context-title-large">Live Conversation Workspace</h3>
                <p class="nexus-context-text">
                    Operate active chat, monitor outcomes, and inspect conversations that need attention.
                </p>
            </div>
        </a>

        <a class="nexus-context-card" href="/app/nexus-chat-workflow-tester">
            <div class="nexus-context-icon">WF</div>
            <div>
                <h3 class="nexus-context-title">Workflow</h3>
                <p class="nexus-context-text">Test channel, category, identity, and knowledge policy resolution.</p>
            </div>
        </a>

        <a class="nexus-context-card nexus-context-card-teal" href="/app/nexus-category-profile-routes">
            <div class="nexus-context-icon nexus-context-icon-mint">RT</div>
            <div>
                <h3 class="nexus-context-title">Routing</h3>
                <p class="nexus-context-text">Review category and identity routes to the governing AI profile.</p>
            </div>
        </a>

    </section>

    <!-- SECTION: LIVE OPERATIONS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge">01 - Live Operations</div>
            <h2 class="nexus-section-title">Conversation Control</h2>
            <p class="nexus-section-text">
                Start with live monitoring, then validate the resolved route and supporting
                identity or profile controls when a conversation needs investigation.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <a class="nexus-card nexus-card-teal nexus-card-teal-bg" href="/app/nexus_live_console">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">LC</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Live Console</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Operate active conversations</div>
            <p class="nexus-card-text">
                Monitor open conversations, AI responses, live agent state, escalation activity,
                handover needs, and current runtime outcomes.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Active Chat</span>
                <span class="nexus-tag nexus-tag-teal">Escalation</span>
                <span class="nexus-tag nexus-tag-teal">Handover</span>
            </div>
        </a>

        <a class="nexus-card nexus-card-purple" href="/app/nexus_live_studio">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">LS</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Live Studio</h3>
            <div class="nexus-card-subtitle">Configuration readiness dashboard</div>
            <p class="nexus-card-text">
                Validate agent profiles, routes, identity profiles, and escalation readiness
                before going live. Surfaces configuration gaps before they reach production.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Readiness</span>
                <span class="nexus-tag nexus-tag-purple">Agents</span>
                <span class="nexus-tag nexus-tag-purple">Routes</span>
            </div>
        </a>

        <a class="nexus-card" href="/app/nexus-chat-workflow-tester">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">WT</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Chat Workflow Tester</h3>
            <div class="nexus-card-subtitle">Validate routed runtime flow</div>
            <p class="nexus-card-text">
                Preview the full handshake from channel and chat category through identity,
                AI Agent Profile, knowledge profile, and access policy.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Test Flow</span>
                <span class="nexus-tag">Identity</span>
                <span class="nexus-tag">Policy</span>
            </div>
        </a>

    </section>

    <!-- SECTION: ROUTING AND IDENTITY -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">02 - Routing And Identity</div>
            <h2 class="nexus-section-title">Chat Resolution Controls</h2>
            <p class="nexus-section-text">
                Live chat uses the same route for website chat and internal chat:
                category plus identity resolves the agent profile and knowledge access policies.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <a class="nexus-card nexus-card-teal nexus-card-teal-bg" href="/app/nexus-chat-category-manager">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">CC</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Chat Category Manager</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Selectable chat intent</div>
            <p class="nexus-card-text">
                Maintain user-facing chat categories and the required identity mode for each
                category, such as guest, logged-in user, email OTP, or registered email OTP.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Category</span>
                <span class="nexus-tag nexus-tag-teal">Intent</span>
                <span class="nexus-tag nexus-tag-teal">Identity</span>
            </div>
        </a>

        <a class="nexus-card" href="/app/nexus-category-profile-routes">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">CR</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Category Profile Routes</h3>
            <div class="nexus-card-subtitle">Map category and identity to profile</div>
            <p class="nexus-card-text">
                Review the active runtime routes where channel, chat category, and identity type
                resolve to the governing AI Agent Profile.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Route</span>
                <span class="nexus-tag">Profile</span>
                <span class="nexus-tag">Channel</span>
            </div>
        </a>

        <a class="nexus-card nexus-card-teal" href="/app/nexus-identity-profile-manager">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">IP</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Identity Profile Manager</h3>
            <div class="nexus-card-subtitle">Identity type to knowledge profile mapping</div>
            <p class="nexus-card-text">
                Define Identity Profiles that map visitor identity types to Knowledge Profiles.
                These profiles are assigned to registry entries and govern knowledge access during chat.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Identity</span>
                <span class="nexus-tag">Knowledge Profile</span>
                <span class="nexus-tag">Mapping</span>
            </div>
        </a>

                <a class="nexus-card nexus-card-purple" href="/app/nexus-identity-registry-manager">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">IR</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Identity Registry Manager</h3>
            <div class="nexus-card-subtitle">Registered identity records</div>
            <p class="nexus-card-text">
                Maintain verified email-based registries, optional business references, and
                identity types that a person may resolve as during chat.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Registry</span>
                <span class="nexus-tag nexus-tag-purple">Email</span>
                <span class="nexus-tag nexus-tag-purple">Identity Type</span>
            </div>
        </a>

        <a class="nexus-card nexus-card-orange" href="/app/nexus-user-profile-manager">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-orange">UP</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">User Profile &amp; Escalation</h3>
            <div class="nexus-card-subtitle">Desk user escalation assignment</div>
            <p class="nexus-card-text">
                Assign AI Agent Profiles to internal desk users and configure their escalation
                capacity. Controls who receives escalated conversations and how many sessions
                they can handle simultaneously.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Escalation</span>
                <span class="nexus-tag">Desk User</span>
                <span class="nexus-tag">Agent Profile</span>
            </div>
        </a>

        <a class="nexus-card nexus-card-indigo" href="/app/nexus-ai-agent-profile-manager">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-indigo">AI</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">AI Agent Profile Manager</h3>
            <div class="nexus-card-subtitle">Configure AI agent behaviour &amp; persona</div>
            <p class="nexus-card-text">
                Create and manage AI Agent Profiles — define behavior prompts, persona, tone,
                escalation policy, memory mode, and session limits for each agent in the routing flow.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Agent</span>
                <span class="nexus-tag">Persona</span>
                <span class="nexus-tag">Escalation</span>
            </div>
        </a>

        <a class="nexus-card nexus-card-teal nexus-card-teal-bg" href="/app/nexus-identity-verification-monitor">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">VM</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Verification Monitor</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Email OTP challenge audit</div>
            <p class="nexus-card-text">
                Inspect verification challenges, pending or verified status, attempts, expiry,
                matched registry, and resolved identity type.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">OTP</span>
                <span class="nexus-tag nexus-tag-teal">Audit</span>
                <span class="nexus-tag nexus-tag-teal">Identity</span>
            </div>
        </a>

    </section>


    <!-- SECTION: GUIDED SETUP -->
    <section class="nexus-section" style="margin-top:24px;">
        <div>
            <div class="nexus-section-badge">03 - Guided Setup</div>
            <h2 class="nexus-section-title">Channel Setup Wizard</h2>
            <p class="nexus-section-text">
                Use the guided wizard to configure a complete channel from scratch — channel,
                chat category, AI agent profile, and identity route access in one step-by-step flow.
            </p>
        </div>
    </section>

    <section class="nexus-card-grid">

        <a class="nexus-card nexus-card-teal" href="/app/nexus-channel-setup-wizard">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">WZ</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Channel Setup Wizard</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Guided channel configuration</div>
            <p class="nexus-card-text">
                Step-by-step wizard to configure a live chat channel — select a channel,
                create a chat category, assign an AI agent profile, and set identity route
                access in a single guided flow.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Channel</span>
                <span class="nexus-tag nexus-tag-teal">Category</span>
                <span class="nexus-tag nexus-tag-teal">Route</span>
            </div>
        </a>

    </section>


    <!-- SECTION: FOUNDATION -->
    <section class="nexus-section" style="margin-top:24px;">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">04 - Foundation Records</div>
            <h2 class="nexus-section-title">Live Chat Masters</h2>
            <p class="nexus-section-text">
                Foundation records used by routing, identity verification, channel selection,
                and live conversation operations.
            </p>
        </div>
    </section>

    <section class="nexus-capability-panel">
        <div class="nexus-capability-grid">

            <a class="nexus-capability-tile" href="/app/nexus-identity-type">
                <div class="nexus-capability-icon">IT</div>
                <p class="nexus-capability-text">Maintain Identity Types used in registry and category routing</p>
            </a>

            <a class="nexus-capability-tile" href="/app/nexus-live-channel">
                <div class="nexus-capability-icon">LC</div>
                <p class="nexus-capability-text">Configure Live Channels that host chat categories and runtime flow</p>
            </a>

            <a class="nexus-capability-tile nexus-capability-tile-teal" href="/app/nexus-chat-category">
                <div class="nexus-capability-icon nexus-capability-icon-teal">CC</div>
                <p class="nexus-capability-text">Open the standard Chat Category list for direct record review</p>
            </a>

            <a class="nexus-capability-tile nexus-capability-tile-teal" href="/app/nexus-query-log">
                <div class="nexus-capability-icon nexus-capability-icon-teal">QL</div>
                <p class="nexus-capability-text">Review conversation query logs and runtime evidence</p>
            </a>

        </div>
    </section>

</div>
"""


def sync_custom_html_block(block_name, html, dry_run=False):
    if not frappe.db.exists("Custom HTML Block", block_name):
        frappe.throw(f"Custom HTML Block {block_name} does not exist.")

    doc = frappe.get_doc("Custom HTML Block", block_name)
    changed = (doc.html or "").strip() != html.strip()

    if changed and not dry_run:
        doc.html = html.strip()
        doc.save(ignore_permissions=True)
        frappe.db.commit()

    return {
        "block": block_name,
        "changed": changed,
        "updated": bool(changed and not dry_run),
    }


def sync_fixture_block(block_name, dry_run=False):
    """Sync a Custom HTML Block (both html and style) from the fixture JSON file."""
    import json
    import os

    fixture_path = os.path.join(
        os.path.dirname(__file__), "..", "fixtures", "custom_html_block.json"
    )
    with open(fixture_path) as f:
        fixture_data = json.load(f)

    block_data = next((b for b in fixture_data if b["name"] == block_name), None)
    if not block_data:
        frappe.logger().warning("sync_fixture_block: %s not found in fixture file", block_name)
        return {"block": block_name, "changed": False, "updated": False, "error": "not in fixture"}

    if not frappe.db.exists("Custom HTML Block", block_name):
        frappe.logger().warning("sync_fixture_block: %s not in database", block_name)
        return {"block": block_name, "changed": False, "updated": False, "error": "not in db"}

    doc = frappe.get_doc("Custom HTML Block", block_name)
    new_html = (block_data.get("html") or "").strip()
    new_style = (block_data.get("style") or "").strip()

    html_changed = (doc.html or "").strip() != new_html
    style_changed = (doc.style or "").strip() != new_style
    changed = html_changed or style_changed

    if changed and not dry_run:
        doc.html = new_html
        doc.style = new_style
        doc.save(ignore_permissions=True)
        frappe.db.commit()

    return {"block": block_name, "changed": changed, "updated": bool(changed and not dry_run)}


def sync_home_workspace_block(dry_run=False):
    return sync_custom_html_block(HOME_BLOCK, HOME_HTML, dry_run=dry_run)


def sync_studio_workspace_block(dry_run=False):
    return sync_custom_html_block(STUDIO_BLOCK, STUDIO_HTML, dry_run=dry_run)


def sync_administration_workspace_block(dry_run=False):
    return sync_custom_html_block(ADMIN_BLOCK, ADMIN_HTML, dry_run=dry_run)


def sync_platform_workspace_block(dry_run=False):
    return sync_custom_html_block(PLATFORM_BLOCK, PLATFORM_HTML, dry_run=dry_run)


def sync_live_workspace_block(dry_run=False):
    return sync_custom_html_block(LIVE_BLOCK, LIVE_HTML, dry_run=dry_run)


def fix_nexus_orbit_custom_block():
    """Ensure the Nexus Orbit workspace has the nexus-home-workspace-html-block child row."""
    ws = frappe.get_doc("Workspace", "Nexus Orbit")
    existing = [cb.custom_block_name for cb in ws.custom_blocks]
    if HOME_BLOCK not in existing:
        ws.append("custom_blocks", {
            "custom_block_name": HOME_BLOCK,
            "label": HOME_BLOCK,
        })
        ws.save(ignore_permissions=True)
        frappe.db.commit()
        return {"fixed": True, "block": HOME_BLOCK}
    return {"fixed": False, "block": HOME_BLOCK}


def sync_all_workspace_blocks(dry_run=False):
    """Sync all workspace HTML blocks to the database. Safe to run on install and migrate."""
    results = []
    for fn in (
        sync_home_workspace_block,
        sync_studio_workspace_block,
        sync_administration_workspace_block,
        sync_platform_workspace_block,
        sync_live_workspace_block,
    ):
        try:
            results.append(fn(dry_run=dry_run))
        except Exception as e:
            frappe.logger().warning("sync_all_workspace_blocks: %s failed — %s", fn.__name__, e)

    # Fixture-driven blocks (html + style both sourced from fixtures/custom_html_block.json)
    for block_name in ("nexus-nexy-companion-workspace-html-block",):
        try:
            results.append(sync_fixture_block(block_name, dry_run=dry_run))
        except Exception as e:
            frappe.logger().warning("sync_all_workspace_blocks: fixture block %s failed — %s", block_name, e)
    return results
