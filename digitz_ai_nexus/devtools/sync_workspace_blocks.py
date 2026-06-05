import frappe


HOME_BLOCK = "nexus-home-workspace-html-block"
STUDIO_BLOCK = "nexus-studio-workspace-html-block"
ADMIN_BLOCK = "nexus-administration-workspace-html-block"
PLATFORM_BLOCK = "nexus-platform-workspace-html-block"
LIVE_BLOCK = "nexus-live-workspace-html-block"


HOME_HTML = """
<div class="nexus-ws">

    <!-- TOP INTELLIGENCE PANEL -->
    <div class="nexus-top-panel">
        <div class="nexus-top-orb">N</div>

        <div class="nexus-top-content">
            <div class="nexus-kicker">
                <span class="nexus-kicker-dot"></span>
                DIGITZ AI NEXUS
            </div>

            <h1 class="nexus-top-title">Nexus Platform Home</h1>

            <p class="nexus-top-lead">
                Central workspace for tenant-scoped AI knowledge, approved content operations,
                public and internal chat, validation, and governed access routing.
            </p>

            <div class="nexus-chip-row">
                <span class="nexus-chip">Tenant Configuration</span>
                <span class="nexus-chip">Approved Knowledge</span>
                <span class="nexus-chip">Live Chat</span>
                <span class="nexus-chip">Access Routing</span>
            </div>
        </div>
    </div>

    <!-- PLATFORM SUMMARY STRIP -->
    <div class="nexus-context-grid">

        <div class="nexus-context-card nexus-context-card-primary">
            <div class="nexus-context-icon nexus-context-icon-large">N</div>
            <div>
                <h3 class="nexus-context-title nexus-context-title-large">Tenant-Scoped AI Platform</h3>
                <p class="nexus-context-text">Each tenant owns its knowledge, defaults, query logs, and runtime boundaries.</p>
            </div>
        </div>

        <div class="nexus-context-card nexus-context-card-teal">
            <div class="nexus-context-icon nexus-context-icon-mint">AI</div>
            <div>
                <h4 class="nexus-context-title">Profile-Driven Agents</h4>
                <p class="nexus-context-text">Chat and Q&amp;A resolve through category, identity, profile, and access categories.</p>
            </div>
        </div>

        <div class="nexus-context-card">
            <div class="nexus-context-icon">QA</div>
            <div>
                <h4 class="nexus-context-title">Governed Q&amp;A</h4>
                <p class="nexus-context-text">Answers are grounded in approved knowledge and filtered by access policy.</p>
            </div>
        </div>

        <div class="nexus-context-card nexus-context-card-teal-soft">
            <div class="nexus-context-icon nexus-context-icon-teal">CH</div>
            <div>
                <h4 class="nexus-context-title">Public &amp; Internal Chat</h4>
                <p class="nexus-context-text">Website, portal, and internal chat use the same routed access model.</p>
            </div>
        </div>

    </div>

    <!-- SECTION: WORKSPACES -->
    <div class="nexus-section">
        <div>
            <div class="nexus-section-badge">01 - Operating Workspaces</div>

            <h3 class="nexus-section-title">Nexus Operating Areas</h3>

            <p class="nexus-section-text">
                Navigate the platform areas for tenant setup, knowledge operations, live chat, and validation.
            </p>
        </div>
    </div>

    <!-- WORKSPACE CARDS -->
    <div class="nexus-card-grid">

        <a href="/app/nexus-studio" class="nexus-card">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">ST</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>

            <h3 class="nexus-card-title">Nexus Studio</h3>
            <div class="nexus-card-subtitle">Knowledge operations</div>

            <p class="nexus-card-text">
                Feed sources, classify knowledge, review chunks, assign access policies, test coverage, and publish approved knowledge.
            </p>

            <div class="nexus-tag-row">
                <span class="nexus-tag">Sources</span>
                <span class="nexus-tag">Chunks</span>
                <span class="nexus-tag">Approval</span>
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
                Configure tenants and the minimum tenant defaults for business unit, public context, chat, Q&amp;A, widgets, and safety.
            </p>

            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Tenant</span>
                <span class="nexus-tag nexus-tag-purple">Defaults</span>
                <span class="nexus-tag nexus-tag-purple">Safety</span>
            </div>
        </a>

        <a href="/app/nexus-live" class="nexus-card nexus-card-teal">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">LV</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>

            <h3 class="nexus-card-title">Nexus Live</h3>
            <div class="nexus-card-subtitle">Real-time AI interaction</div>

            <p class="nexus-card-text">
                Operate live conversations, agent availability, queues, escalation, and human handover.
            </p>

            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Live Chat</span>
                <span class="nexus-tag nexus-tag-teal">Escalation</span>
                <span class="nexus-tag nexus-tag-teal">Handover</span>
            </div>
        </a>

        <a href="/app/nexus-platform" class="nexus-card nexus-card-teal nexus-card-teal-bg">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">PL</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>

            <h3 class="nexus-card-title">Nexus Platform</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Validation and diagnostics</div>

            <p class="nexus-card-text">
                Validate retrieval, routing, grounding, access behavior, runtime reliability, and readiness.
            </p>

            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal-strong">Validation</span>
                <span class="nexus-tag nexus-tag-teal-strong">Diagnostics</span>
                <span class="nexus-tag nexus-tag-teal-strong">Readiness</span>
            </div>
        </a>

    </div>

    <!-- SECTION: CAPABILITIES -->
    <div class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">02 - Capability Map</div>

            <h3 class="nexus-section-title">Platform Capabilities</h3>

            <p class="nexus-section-text">
                Enterprise AI capabilities available through tenants, tenant configuration, and profile/access routing.
            </p>
        </div>
    </div>

    <div class="nexus-capability-panel">
        <div class="nexus-capability-grid">

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">KN</div>
                <p class="nexus-capability-text">Approved<br>knowledge access</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">QA</div>
                <p class="nexus-capability-text">Governed<br>business Q&amp;A</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">CH</div>
                <p class="nexus-capability-text">AI-powered live<br>customer interaction</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">WD</div>
                <p class="nexus-capability-text">Website and portal<br>AI widgets</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">AC</div>
                <p class="nexus-capability-text">Access policy<br>enforcement</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">BU</div>
                <p class="nexus-capability-text">Business unit<br>knowledge scope</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">RT</div>
                <p class="nexus-capability-text">Category and identity<br>runtime routing</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">VL</div>
                <p class="nexus-capability-text">Runtime validation<br>and diagnostics</p>
            </div>

        </div>
    </div>

</div>
"""


STUDIO_HTML = """
<div class="nexus-ws nexus-studio-ws">

    <!-- TOP INTELLIGENCE PANEL -->
    <section class="nexus-top-panel">
        <div class="nexus-top-orb">ST</div>

        <div class="nexus-top-content">
            <div class="nexus-kicker">
                <span class="nexus-kicker-dot"></span>
                KNOWLEDGE OPERATIONS
            </div>

            <h1 class="nexus-top-title">Nexus Studio</h1>

            <p class="nexus-top-lead">
                Workspace for preparing tenant knowledge for governed AI chat and Q&amp;A. Feed sources,
                classify scope, assign access policies, process chunks, validate answers, and publish
                approved knowledge.
            </p>

            <div class="nexus-chip-row">
                <span class="nexus-chip">Source Intake</span>
                <span class="nexus-chip">Knowledge Units</span>
                <span class="nexus-chip">Access Policies</span>
                <span class="nexus-chip">Validation</span>
                <span class="nexus-chip">Publishing</span>
            </div>
        </div>
    </section>

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
            <div class="nexus-context-icon nexus-context-icon-teal">QA</div>
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

    </section>

    <!-- SECTION: BOUNDARY -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">02 - Studio Boundary</div>

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
            <div class="nexus-section-badge">03 - Knowledge Lifecycle</div>

            <h3 class="nexus-section-title">From Source To Approved Answer</h3>

            <p class="nexus-section-text">
                Studio keeps the knowledge path explicit so website chat, internal chat, Q&amp;A, and API calls
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

    </section>

    <!-- SECTION: RECORDS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge nexus-section-badge-teal">04 - Studio Records</div>

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
    </section>

</div>
"""


ADMIN_HTML = """
<div class="nexus-ws nexus-admin-ws">

    <!-- TOP CONFIGURATION PANEL -->
    <section class="nexus-top-panel">
        <div class="nexus-top-orb">AD</div>

        <div class="nexus-top-content">
            <div class="nexus-kicker">
                <span class="nexus-kicker-dot"></span>
                TENANT CONFIGURATION
            </div>

            <h1 class="nexus-top-title">Nexus Administration</h1>

            <p class="nexus-top-lead">
                Administration is the tenant configuration workspace. Select a tenant, maintain the
                minimum defaults required for chat and Q&amp;A, connect master records, and verify
                readiness before knowledge is exposed through public or internal channels.
            </p>

            <div class="nexus-chip-row">
                <span class="nexus-chip">Tenant</span>
                <span class="nexus-chip">Business Unit</span>
                <span class="nexus-chip">Public Context</span>
                <span class="nexus-chip">Channels</span>
                <span class="nexus-chip">Readiness</span>
            </div>
        </div>
    </section>

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

        <div class="nexus-context-card nexus-context-card-teal">
            <div class="nexus-context-icon nexus-context-icon-mint">PC</div>
            <div>
                <h3 class="nexus-context-title">Public Context</h3>
                <p class="nexus-context-text">Use Public Context as a master record for public-facing scope.</p>
            </div>
        </div>

        <div class="nexus-context-card nexus-context-card-teal-soft">
            <div class="nexus-context-icon nexus-context-icon-teal">RD</div>
            <div>
                <h3 class="nexus-context-title">Readiness</h3>
                <p class="nexus-context-text">Confirm Q&amp;A, live chat, testing, approval, and guard settings.</p>
            </div>
        </div>

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
                Select the tenant, maintain default business unit, public context, chat channel,
                Q&amp;A channel, widget settings, safety settings, and readiness values.
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

        <a class="nexus-card nexus-card-teal nexus-card-teal-bg" href="/app/nexus-public-context">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-teal">PC</div>
                <div class="nexus-card-arrow nexus-card-arrow-teal">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Public Contexts</h3>
            <div class="nexus-card-subtitle nexus-card-subtitle-teal">Public-facing scope master</div>
            <p class="nexus-card-text">
                Maintain public context records used by website chat, public Q&amp;A, and tenant
                knowledge classification.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-teal">Master</span>
                <span class="nexus-tag nexus-tag-teal">Public</span>
                <span class="nexus-tag nexus-tag-teal">Context</span>
            </div>
        </a>

        <a class="nexus-card nexus-card-purple" href="/app/nexus-live-channel">
            <div class="nexus-card-head">
                <div class="nexus-card-icon nexus-card-icon-purple">CH</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Live Channels</h3>
            <div class="nexus-card-subtitle">Chat and Q&amp;A channel defaults</div>
            <p class="nexus-card-text">
                Maintain the channels selected by tenant configuration for public website chat,
                internal chat, and Q&amp;A operations.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Chat</span>
                <span class="nexus-tag nexus-tag-purple">Q&amp;A</span>
                <span class="nexus-tag nexus-tag-purple">Channel</span>
            </div>
        </a>

        <a class="nexus-card" href="/app/nexus-access-policy">
            <div class="nexus-card-head">
                <div class="nexus-card-icon">AP</div>
                <div class="nexus-card-arrow">-&gt;</div>
            </div>
            <h3 class="nexus-card-title">Access Policies</h3>
            <div class="nexus-card-subtitle">Knowledge access rules</div>
            <p class="nexus-card-text">
                Review the access policies assigned in Studio and enforced during chat, Q&amp;A,
                and future API calls.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag">Policy</span>
                <span class="nexus-tag">Access</span>
                <span class="nexus-tag">Runtime</span>
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
                <div class="nexus-capability-icon nexus-capability-icon-teal">PC</div>
                <p class="nexus-capability-text">Default public context selected from master records</p>
            </div>

            <div class="nexus-capability-tile nexus-capability-tile-teal">
                <div class="nexus-capability-icon nexus-capability-icon-teal">CH</div>
                <p class="nexus-capability-text">Default chat and Q&amp;A channel selection</p>
            </div>

            <div class="nexus-capability-tile">
                <div class="nexus-capability-icon">QA</div>
                <p class="nexus-capability-text">Q&amp;A enablement, top-k, citations, and approval requirements</p>
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

    <!-- TOP ASSURANCE PANEL -->
    <section class="nexus-top-panel">
        <div class="nexus-top-orb">PL</div>

        <div class="nexus-top-content">
            <div class="nexus-kicker">
                <span class="nexus-kicker-dot"></span>
                VALIDATION AND DIAGNOSTICS
            </div>

            <h1 class="nexus-top-title">Nexus Platform</h1>

            <p class="nexus-top-lead">
                Technical assurance workspace for the Nexus runtime. Use it to inspect query logs,
                validate retrieval and answer behavior, confirm access policy enforcement, review
                integration readiness, and prove release confidence for public and internal chat.
            </p>

            <div class="nexus-chip-row">
                <span class="nexus-chip">Runtime Diagnostics</span>
                <span class="nexus-chip">Query Logs</span>
                <span class="nexus-chip">Retrieval Validation</span>
                <span class="nexus-chip">Access Checks</span>
                <span class="nexus-chip">Release Readiness</span>
            </div>
        </div>
    </section>

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
                behavior for public chat, internal chat, Q&amp;A, and future API calls.
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
            <div class="nexus-card-subtitle">Website, internal chat, Q&amp;A, API</div>
            <p class="nexus-card-text">
                Validate public website chat, internal user chat, Q&amp;A flows, widget settings,
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
                <p class="nexus-capability-text">Test cases for chat, Q&amp;A, website, internal user, and API behavior</p>
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

    <!-- TOP LIVE PANEL -->
    <section class="nexus-top-panel">
        <div class="nexus-top-orb">LV</div>

        <div class="nexus-top-content">
            <div class="nexus-kicker">
                <span class="nexus-kicker-dot"></span>
                LIVE CHAT OPERATIONS
            </div>

            <h1 class="nexus-top-title">Nexus Live</h1>

            <p class="nexus-top-lead">
                Operations workspace for public website chat and internal user chat. Monitor
                live conversations, validate the routed chat flow, manage identity verification,
                support handover, and review the controls that connect chat categories,
                identity, agent profiles, access categories, and access policies.
            </p>

            <div class="nexus-chip-row">
                <span class="nexus-chip">Public Website Chat</span>
                <span class="nexus-chip">Internal User Chat</span>
                <span class="nexus-chip">Identity Verification</span>
                <span class="nexus-chip">Agent Routing</span>
                <span class="nexus-chip">Handover</span>
            </div>
        </div>
    </section>

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
                <p class="nexus-context-text">Test channel, category, identity, profile, and policy resolution.</p>
            </div>
        </a>

        <a class="nexus-context-card nexus-context-card-teal" href="/app/nexus-category-profile-routes">
            <div class="nexus-context-icon nexus-context-icon-mint">RT</div>
            <div>
                <h3 class="nexus-context-title">Routing</h3>
                <p class="nexus-context-text">Review category and identity routes to the governing AI profile.</p>
            </div>
        </a>

        <a class="nexus-context-card nexus-context-card-teal-soft" href="/app/nexus-profile-access-allocation">
            <div class="nexus-context-icon nexus-context-icon-teal">AC</div>
            <div>
                <h3 class="nexus-context-title">Access</h3>
                <p class="nexus-context-text">Review profile access category and access policy allocation.</p>
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
            <div class="nexus-card-subtitle">Agent and channel setup</div>
            <p class="nexus-card-text">
                Configure live agents, channels, queues, availability, and handover behavior
                used by operational chat.
            </p>
            <div class="nexus-tag-row">
                <span class="nexus-tag nexus-tag-purple">Agents</span>
                <span class="nexus-tag nexus-tag-purple">Queues</span>
                <span class="nexus-tag nexus-tag-purple">Channels</span>
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
                AI Agent Profile, access category, and access policy.
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
                Live chat uses the same route for website chat, internal chat, Q&amp;A, and future
                API calls: category plus identity resolves the agent profile and access policies.
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

    <!-- SECTION: PROFILE AND ACCESS -->
    <section class="nexus-section">
        <div>
            <div class="nexus-section-badge">03 - Profiles And Access</div>
            <h2 class="nexus-section-title">Agent Profile Controls</h2>
            <p class="nexus-section-text">
                These records control how logged-in internal users and verified public identities
                reach the correct AI profile and knowledge access policy.
            </p>
        </div>
    </section>

    <section class="nexus-capability-panel">
        <div class="nexus-capability-grid">

            <a class="nexus-capability-tile" href="/app/nexus-user-profile-manager">
                <div class="nexus-capability-icon">UP</div>
                <p class="nexus-capability-text">Assign AI Agent Profiles to logged-in internal desk users</p>
            </a>

            <a class="nexus-capability-tile" href="/app/nexus-profile-access-allocation">
                <div class="nexus-capability-icon">PA</div>
                <p class="nexus-capability-text">Map AI Agent Profiles to access categories and access policies</p>
            </a>

            <a class="nexus-capability-tile nexus-capability-tile-teal" href="/app/nexus-ai-agent-profile">
                <div class="nexus-capability-icon nexus-capability-icon-teal">AI</div>
                <p class="nexus-capability-text">Manage AI Agent Profiles that own behavior and runtime access</p>
            </a>

            <a class="nexus-capability-tile" href="/app/nexus-access-category">
                <div class="nexus-capability-icon">AG</div>
                <p class="nexus-capability-text">Create access categories that group allowed knowledge policies</p>
            </a>

            <a class="nexus-capability-tile nexus-capability-tile-teal" href="/app/nexus-access-policy">
                <div class="nexus-capability-icon nexus-capability-icon-teal">AP</div>
                <p class="nexus-capability-text">Maintain access policies matched by approved knowledge chunks</p>
            </a>

            <a class="nexus-capability-tile nexus-capability-tile-teal" href="/app/nexus-category-identity-route">
                <div class="nexus-capability-icon nexus-capability-icon-teal">IR</div>
                <p class="nexus-capability-text">Open the standard identity route list for direct review and audit</p>
            </a>

        </div>
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
