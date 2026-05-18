frappe.pages['nexus-studio-page'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Nexus Studio',
        single_column: true
    });

    wrapper.nexus_studio_page = new NexusStudioPage(wrapper, page);
};

class NexusStudioPage {
    constructor(wrapper, page) {
        this.wrapper = wrapper;
        this.page = page;
        this.body = $(this.page.body);

        this.api = {
            get_summary: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_studio_summary',
            get_units: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_knowledge_units',
            get_readiness: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_knowledge_unit_readiness',
            approve_unit: 'digitz_ai_nexus.api.nexus_knowledge_studio.approve_knowledge_unit',
            mark_review: 'digitz_ai_nexus.api.nexus_knowledge_studio.mark_knowledge_unit_needs_review',
            clear_review: 'digitz_ai_nexus.api.nexus_knowledge_studio.clear_knowledge_unit_review',
            mark_ready_to_publish: 'digitz_ai_nexus.api.nexus_knowledge_studio.mark_knowledge_unit_ready_to_publish',
            get_source_summary: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_knowledge_source_summary',
            get_sources: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_knowledge_sources',
            validate_source: 'digitz_ai_nexus.api.nexus_knowledge_studio.validate_knowledge_source',
            suggest_source_fields: 'digitz_ai_nexus.api.nexus_knowledge_source_assist.suggest_knowledge_source_fields',
            create_assisted_source: 'digitz_ai_nexus.api.nexus_knowledge_source_assist.create_knowledge_source_from_suggestion',
            publish_source: 'digitz_ai_nexus.api.nexus_knowledge_studio.publish_knowledge_source',
            unpublish_source: 'digitz_ai_nexus.api.nexus_knowledge_studio.unpublish_knowledge_source',
        };

        this.active_tab = 'overview';

        this.filters = {
            search: '',
            status: '',
            needs_review: '',
            only_missing: 0,
            only_ready_for_chunking: 0,
            only_ready_to_publish: 0
        };

        this.source_filters = {
            search: '',
            status: '',
            sync_status: '',
            disabled: ''
        };

        this.summary = {};
        this.units = [];
        this.source_summary = {};
        this.sources = [];
        this.active_tenant = '';
        this.active_context = {};

        this.make();
    }

    inject_styles() {
        if (document.getElementById('nexus-studio-page-style')) {
            return;
        }

        const style = document.createElement('style');
        style.id = 'nexus-studio-page-style';

        style.innerHTML = `
            .nks-wrap {
                max-width: 1240px;
                margin: 0 auto;
                color: #102b67;
            }

            .nks-hero {
                display: flex;
                justify-content: space-between;
                gap: 22px;
                align-items: center;
                padding: 28px 30px;
                margin-bottom: 18px;
                border-radius: 24px;
                background:
                    radial-gradient(circle at 96% 18%, rgba(224, 166, 47, 0.22), transparent 26%),
                    radial-gradient(circle at 0% 0%, rgba(77, 163, 255, 0.22), transparent 28%),
                    linear-gradient(135deg, #eef7ff 0%, #f7fbff 54%, #fff8e8 100%);
                border: 1.5px solid rgba(77, 163, 255, 0.42);
                box-shadow:
                    0 18px 44px rgba(33, 77, 187, 0.10),
                    inset 0 1px 0 rgba(255, 255, 255, 0.82);
            }

            .nks-kicker {
                display: inline-flex;
                align-items: center;
                padding: 7px 14px;
                border-radius: 999px;
                background: #eaf4ff;
                border: 1.5px solid rgba(33, 119, 255, 0.24);
                color: #0b60d8;
                font-size: 11px;
                font-weight: 950;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-bottom: 14px;
            }

            .nks-hero h2 {
                margin: 0;
                color: #071d4f;
                font-size: 30px;
                line-height: 1.18;
                font-weight: 950;
                letter-spacing: -0.035em;
            }

            .nks-hero h2::after {
                content: "";
                display: inline-block;
                width: 42px;
                height: 4px;
                margin-left: 12px;
                border-radius: 999px;
                background: #e0a62f;
                vertical-align: middle;
            }

            .nks-hero p {
                margin: 12px 0 0;
                max-width: 840px;
                color: #284879;
                font-size: 14px;
                line-height: 1.62;
                font-weight: 760;
            }

            .nks-hero-side {
                min-width: 210px;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 10px;
            }

            .nks-hero-badge,
            .nks-tenant-pill {
                padding: 9px 16px;
                border-radius: 999px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 13px;
                font-weight: 950;
                color: #214dbb;
                background: #ffffff;
                border: 1.5px solid rgba(33, 119, 255, 0.24);
                box-shadow: 0 8px 20px rgba(33, 77, 187, 0.08);
            }

            .nks-tenant-pill {
                max-width: 260px;
                color: #0b3c91;
                font-size: 12px;
                font-weight: 900;
                text-align: right;
            }

            .nks-context-panel,
            .nks-tabs,
            .nks-section-panel {
                background: #ffffff;
                border: 1.5px solid rgba(33, 119, 255, 0.24);
                box-shadow: 0 14px 32px rgba(33, 77, 187, 0.07);
            }

            .nks-context-panel {
                margin-bottom: 18px;
                padding: 20px;
                border-radius: 22px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(224, 166, 47, 0.08), transparent 24%),
                    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            }

            .nks-context-head {
                display: flex;
                justify-content: space-between;
                gap: 16px;
                align-items: flex-start;
                margin-bottom: 14px;
            }

            .nks-context-head h3,
            .nks-section-head h3 {
                display: inline-flex;
                align-items: center;
                margin: 0;
                padding: 10px 16px;
                border-radius: 999px;
                background: #eef6ff;
                color: #0b3c91;
                border: 1.5px solid rgba(33, 119, 255, 0.22);
                font-size: 16px;
                font-weight: 950;
            }

            .nks-context-head h3::after,
            .nks-section-head h3::after {
                content: "";
                width: 34px;
                height: 4px;
                margin-left: 12px;
                border-radius: 999px;
                background: #e0a62f;
            }

            .nks-context-head p,
            .nks-section-head p {
                margin: 10px 0 0;
                color: #526887;
                font-size: 13px;
                line-height: 1.48;
                font-weight: 750;
            }

            .nks-context-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(190px, 1fr));
                gap: 12px;
            }

            .nks-context-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                min-height: 48px;
                padding: 12px 14px;
                border-radius: 15px;
                background: #f8fbff;
                border: 1.5px solid rgba(33, 119, 255, 0.18);
            }

            .nks-context-item-strong {
                background: #eef6ff;
                border-color: rgba(33, 119, 255, 0.28);
            }

            .nks-context-item span {
                color: #526887;
                font-size: 12px;
                font-weight: 850;
            }

            .nks-context-item strong {
                color: #0b3c91;
                font-size: 12px;
                font-weight: 950;
                text-align: right;
            }

            .nks-tabs {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 18px;
                padding: 12px;
                border-radius: 22px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(224, 166, 47, 0.07), transparent 24%),
                    #ffffff;
            }

            .nks-tab {
                border: 1.5px solid rgba(33, 119, 255, 0.18);
                background: #f6f9ff;
                color: #214dbb;
                padding: 8px 13px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 900;
                cursor: pointer;
                transition: all 0.16s ease;
            }

            .nks-tab:hover {
                background: #eef6ff;
                border-color: rgba(33, 119, 255, 0.34);
            }

            .nks-tab.active {
                background: #214dbb;
                color: #ffffff;
                border-color: #214dbb;
                box-shadow: 0 8px 18px rgba(33, 77, 187, 0.18);
            }

            .nks-summary-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(160px, 1fr));
                gap: 12px;
                margin-bottom: 16px;
            }

            .nks-summary-card {
                padding: 16px;
                border-radius: 18px;
                background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border: 1.5px solid rgba(33, 119, 255, 0.24);
                box-shadow: 0 10px 24px rgba(33, 77, 187, 0.06);
            }

            .nks-summary-card-good {
                background: #f1fffb;
                border-color: rgba(0, 184, 148, 0.30);
            }

            .nks-summary-card-warn {
                background: #fff8e8;
                border-color: rgba(224, 166, 47, 0.34);
            }

            .nks-summary-label {
                color: #526887;
                font-size: 12px;
                line-height: 1.25;
                font-weight: 850;
            }

            .nks-summary-value {
                margin-top: 5px;
                color: #071d4f;
                font-size: 28px;
                line-height: 1;
                font-weight: 950;
            }

            .nks-section-panel {
                border-radius: 22px;
                overflow: hidden;
                margin-bottom: 16px;
            }

            .nks-section-head {
                padding: 20px 20px 12px;
            }

            .nks-stage-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(180px, 1fr));
                gap: 12px;
                padding: 0 20px 20px;
            }

            .nks-stage-card {
                min-height: 118px;
                padding: 16px;
                border-radius: 18px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(77, 163, 255, 0.10), transparent 30%),
                    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border: 1.5px solid rgba(33, 119, 255, 0.22);
            }

            .nks-stage-card-teal {
                background:
                    radial-gradient(circle at 100% 0%, rgba(0, 184, 148, 0.08), transparent 30%),
                    linear-gradient(180deg, #ffffff 0%, #f4fffc 100%);
                border-color: rgba(0, 184, 148, 0.24);
            }

            .nks-stage-icon {
                width: 42px;
                height: 42px;
                border-radius: 15px;
                background: #eef6ff;
                color: #0b60d8;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
                margin-bottom: 10px;
            }

            .nks-stage-card-teal .nks-stage-icon {
                background: #ecfffb;
                color: #008c78;
            }

            .nks-stage-title {
                margin: 0;
                color: #102b67;
                font-size: 14px;
                font-weight: 950;
            }

            .nks-stage-text {
                margin: 5px 0 0;
                color: #526887;
                font-size: 12px;
                line-height: 1.42;
                font-weight: 700;
            }

            .nks-toolbar {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                align-items: center;
                margin: 0 20px 14px;
                padding: 14px;
                border-radius: 18px;
                background: #ffffff;
                border: 1.5px solid rgba(33, 119, 255, 0.22);
                box-shadow: 0 10px 24px rgba(33, 77, 187, 0.05);
            }

            .nks-toolbar-left {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                flex: 1;
            }

            .nks-toolbar-left .form-control {
                min-width: 190px;
                max-width: 240px;
                border-radius: 14px;
                border-color: rgba(33, 119, 255, 0.24);
            }

            .nks-toolbar-left .nks-search,
            .nks-toolbar-left .nks-source-search {
                min-width: 260px;
                max-width: 320px;
            }

            .nks-toolbar-right {
                display: flex;
                justify-content: flex-end;
                align-items: center;
                gap: 8px;
                flex-wrap: wrap;
            }

            .nks-table-wrap {
                overflow-x: auto;
            }

            .nks-table {
                margin: 0;
            }

            .nks-table th {
                background: #f6f9ff;
                color: #102b67;
                font-size: 12px;
                font-weight: 900;
                white-space: nowrap;
                border-color: rgba(33, 119, 255, 0.16) !important;
            }

            .nks-table td {
                vertical-align: middle;
                font-size: 12px;
                border-color: rgba(33, 119, 255, 0.12) !important;
            }

            .nks-unit-link {
                color: #0b60d8;
                font-weight: 900;
                text-decoration: none;
            }

            .nks-unit-link:hover {
                color: #214dbb;
                text-decoration: underline;
            }

            .nks-row-sub {
                margin-top: 3px;
                color: #7a8daa;
                font-size: 11px;
                line-height: 1.3;
                font-weight: 700;
            }

            .nks-badge {
                display: inline-flex;
                align-items: center;
                padding: 5px 8px;
                margin: 2px 3px 2px 0;
                border-radius: 999px;
                background: #eef6ff;
                color: #0b60d8;
                border: 1px solid rgba(11, 108, 255, 0.16);
                font-size: 11px;
                line-height: 1.1;
                font-weight: 850;
                white-space: nowrap;
            }

            .nks-badge-good {
                background: #ecfffb;
                color: #008c78;
                border-color: rgba(0, 184, 148, 0.22);
            }

            .nks-badge-warn {
                background: #fff7e8;
                color: #a66d00;
                border-color: rgba(224, 166, 47, 0.26);
            }

            .nks-badge-info {
                background: #eef6ff;
                color: #0b60d8;
                border-color: rgba(11, 108, 255, 0.18);
            }

            .nks-action-row,
            .nks-inline-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }

            .nks-placeholder {
                padding: 0 20px 20px;
            }

            .nks-placeholder-box {
                padding: 18px;
                border-radius: 18px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(224, 166, 47, 0.08), transparent 28%),
                    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border: 1.5px dashed rgba(33, 119, 255, 0.28);
            }

            .nks-placeholder-box h4 {
                margin: 0;
                color: #102b67;
                font-size: 15px;
                font-weight: 950;
            }

            .nks-placeholder-box p,
            .nks-readiness-dialog p {
                margin: 7px 0 0;
                color: #526887;
                font-size: 13px;
                line-height: 1.5;
                font-weight: 700;
            }

            .nks-dashboard-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(220px, 1fr));
                gap: 12px;
                margin-bottom: 12px;
            }

            .nks-dashboard-card {
                padding: 14px;
                border-radius: 16px;
                background: #ffffff;
                border: 1.5px solid rgba(33, 119, 255, 0.18);
                box-shadow: 0 10px 22px rgba(33, 77, 187, 0.05);
            }

            .nks-dashboard-card-blue {
                background:
                    radial-gradient(circle at 100% 0%, rgba(77, 163, 255, 0.10), transparent 30%),
                    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            }

            .nks-dashboard-card-green {
                background:
                    radial-gradient(circle at 100% 0%, rgba(0, 184, 148, 0.10), transparent 30%),
                    linear-gradient(180deg, #ffffff 0%, #f4fffc 100%);
                border-color: rgba(0, 184, 148, 0.24);
            }

            .nks-dashboard-card-warn {
                background:
                    radial-gradient(circle at 100% 0%, rgba(224, 166, 47, 0.12), transparent 30%),
                    linear-gradient(180deg, #ffffff 0%, #fffaf0 100%);
                border-color: rgba(224, 166, 47, 0.30);
            }

            .nks-dashboard-card h5 {
                margin: 0 0 8px;
                color: #0b3c91;
                font-weight: 950;
                font-size: 14px;
            }

            .nks-dashboard-card p {
                margin: 6px 0;
                color: #314d78;
                font-size: 12px;
                line-height: 1.45;
                font-weight: 700;
            }

            .nks-dashboard-actions {
                padding: 14px;
                border-radius: 16px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(224, 166, 47, 0.10), transparent 28%),
                    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border: 1.5px solid rgba(33, 119, 255, 0.20);
                margin-bottom: 12px;
            }

            .nks-dashboard-notice {
                padding: 12px;
                border-radius: 14px;
                background: #fff8e8;
                border: 1.5px solid rgba(224, 166, 47, 0.28);
                color: #7a5200;
                font-size: 12px;
                line-height: 1.45;
                font-weight: 750;
                margin-top: 10px;
            }

            .nks-dashboard-technical {
                margin-top: 12px;
                padding: 14px;
                border-radius: 16px;
                background: #f8fbff;
                border: 1.5px dashed rgba(33, 119, 255, 0.28);
            }

            .nks-ai-locked-note {
                margin-bottom: 10px;
                padding: 10px 12px;
                border-radius: 12px;
                background: #eef6ff;
                border: 1px solid rgba(33, 119, 255, 0.22);
                color: #0b3c91;
                font-size: 12px;
                font-weight: 700;
            }

            @media (max-width: 1100px) {
                .nks-summary-grid,
                .nks-stage-grid,
                .nks-dashboard-grid {
                    grid-template-columns: repeat(2, minmax(160px, 1fr));
                }

                .nks-toolbar {
                    align-items: stretch;
                    flex-direction: column;
                }

                .nks-toolbar-left .form-control,
                .nks-toolbar-left .nks-search,
                .nks-toolbar-left .nks-source-search {
                    max-width: none;
                    flex: 1;
                }

                .nks-toolbar-right {
                    justify-content: flex-start;
                }
            }

            @media (max-width: 900px) {
                .nks-context-grid {
                    grid-template-columns: repeat(2, minmax(160px, 1fr));
                }

                .nks-context-head {
                    flex-direction: column;
                }
            }

            @media (max-width: 700px) {
                .nks-hero {
                    align-items: flex-start;
                    flex-direction: column;
                }

                .nks-hero-side {
                    align-items: flex-start;
                }

                .nks-summary-grid,
                .nks-stage-grid,
                .nks-context-grid,
                .nks-dashboard-grid {
                    grid-template-columns: 1fr;
                }

                .nks-toolbar-left {
                    flex-direction: column;
                }

                .nks-toolbar-left .form-control,
                .nks-toolbar-left .nks-search,
                .nks-toolbar-left .nks-source-search {
                    width: 100%;
                    min-width: 0;
                }
            }
        `;

        document.head.appendChild(style);
    }

    make() {
        this.body.empty();
        this.inject_styles();

        this.body.append(`
            <div class="nks-wrap">
                <div class="nks-hero">
                    <div>
                        <div class="nks-kicker">DIGITZ AI Nexus</div>
                        <h2>Nexus Studio</h2>
                        <p>
                            Manage the complete Studio lifecycle for knowledge sources, ingestion,
                            knowledge units, AI preparation, testing, gaps, and publishing readiness.
                        </p>
                    </div>

                    <div class="nks-hero-side">
                        <div class="nks-hero-badge">Studio</div>
                        <div class="nks-tenant-pill" id="nks-active-tenant-pill">
                            Active Tenant: Resolving...
                        </div>
                    </div>
                </div>

                <div id="nks-active-context-panel"></div>

                <div class="nks-tabs">
                    ${this.get_tabs_html()}
                </div>

                <div id="nks-tab-content"></div>
            </div>
        `);

        this.bind_events();
        this.load();
        this.render_active_tab();
    }

    get_tabs_html() {
        const tabs = [
            ['overview', 'Overview'],
            ['sources', 'Knowledge Sources'],
            ['ingestion', 'Intake & Ingestion'],
            ['units', 'Knowledge Units'],
            ['indexing', 'AI Preparation'],
            ['testing', 'Testing & Validation'],
            ['gaps', 'Knowledge Gaps'],
            ['publish', 'Publish Readiness']
        ];

        return tabs.map(([key, label]) => {
            return `
                <button class="nks-tab ${this.active_tab === key ? 'active' : ''}" data-tab="${key}">
                    ${frappe.utils.escape_html(label)}
                </button>
            `;
        }).join('');
    }

    merge_active_context(incoming_context, incoming_summary) {
        const current = this.active_context || {};
        const incoming = incoming_context || {};
        const summary = incoming_summary || {};

        this.active_context = {
            user:
                incoming.user ||
                current.user ||
                frappe.session.user ||
                '',

            tenant:
                incoming.tenant ||
                summary.active_tenant ||
                current.tenant ||
                '',

            ecosystem:
                incoming.ecosystem ||
                summary.active_ecosystem ||
                current.ecosystem ||
                '',

            business_unit:
                incoming.business_unit ||
                summary.active_business_unit ||
                current.business_unit ||
                '',

            project:
                incoming.project ||
                summary.active_project ||
                current.project ||
                '',

            channel:
                incoming.channel ||
                summary.active_channel ||
                current.channel ||
                '',

            context:
                incoming.context ||
                summary.active_context ||
                current.context ||
                ''
        };

        this.active_tenant = this.active_context.tenant || this.active_tenant || '';
    }

    render_active_context_panel() {
        const context = this.active_context || {};
        const summary = this.summary || {};

        const resolved_context = {
            user: context.user || frappe.session.user || '-',
            tenant: context.tenant || summary.active_tenant || this.source_summary.active_tenant || '-',
            ecosystem: context.ecosystem || summary.active_ecosystem || this.source_summary.active_ecosystem || '-',
            business_unit: context.business_unit || summary.active_business_unit || this.source_summary.active_business_unit || '-',
            project: context.project || summary.active_project || this.source_summary.active_project || '-',
            channel: context.channel || summary.active_channel || this.source_summary.active_channel || '-',
            context: context.context || summary.active_context || this.source_summary.active_context || '-'
        };

        this.body.find('#nks-active-context-panel').html(`
            <div class="nks-context-panel">
                <div class="nks-context-head">
                    <div>
                        <h3>Active Studio Filter</h3>
                        <p>
                            Nexus Studio records are scoped using the current user working context.
                            All summaries, lists, and actions respect this resolved filter.
                        </p>
                    </div>

                    <button class="btn btn-default btn-sm nks-refresh-btn">
                        Refresh Context
                    </button>
                </div>

                <div class="nks-context-grid">
                    ${this.get_context_item_html('User', resolved_context.user)}
                    ${this.get_context_item_html('Tenant', resolved_context.tenant, true)}
                    ${this.get_context_item_html('Ecosystem', resolved_context.ecosystem)}
                    ${this.get_context_item_html('Business Unit', resolved_context.business_unit, true)}
                    ${this.get_context_item_html('Project', resolved_context.project)}
                    ${this.get_context_item_html('Channel', resolved_context.channel)}
                    ${this.get_context_item_html('Context', resolved_context.context, true)}
                </div>
            </div>
        `);
    }

    get_context_item_html(label, value, strong = false) {
        return `
            <div class="nks-context-item ${strong ? 'nks-context-item-strong' : ''}">
                <span>${frappe.utils.escape_html(label)}</span>
                <strong>${frappe.utils.escape_html(value || '-')}</strong>
            </div>
        `;
    }

    bind_events() {
        this.body.on('click', '.nks-tab', (e) => {
            this.active_tab = $(e.currentTarget).data('tab');
            this.body.find('.nks-tab').removeClass('active');
            $(e.currentTarget).addClass('active');
            this.render_active_tab();
        });

        this.body.on('click', '.nks-refresh-btn', () => {
            this.load();
        });

        this.body.on('input', '.nks-search', frappe.utils.debounce((e) => {
            this.filters.search = e.target.value || '';
            this.load_units();
        }, 300));

        this.body.on('change', '.nks-status-filter', (e) => {
            this.filters.status = e.target.value || '';
            this.load_units();
        });

        this.body.on('change', '.nks-review-filter', (e) => {
            this.filters.needs_review = e.target.value;
            this.load_units();
        });

        this.body.on('change', '.nks-readiness-filter', (e) => {
            const value = e.target.value || '';

            this.filters.only_missing = value === 'missing' ? 1 : 0;
            this.filters.only_ready_for_chunking = value === 'ready_for_chunking' ? 1 : 0;
            this.filters.only_ready_to_publish = value === 'ready_to_publish' ? 1 : 0;

            this.load_units();
        });

        this.body.on('input', '.nks-source-search', frappe.utils.debounce((e) => {
            this.source_filters.search = e.target.value || '';
            this.load_sources();
        }, 300));

        this.body.on('change', '.nks-source-status-filter', (e) => {
            this.source_filters.status = e.target.value || '';
            this.load_sources();
        });

        this.body.on('change', '.nks-source-sync-filter', (e) => {
            this.source_filters.sync_status = e.target.value || '';
            this.load_sources();
        });

        this.body.on('change', '.nks-source-disabled-filter', (e) => {
            this.source_filters.disabled = e.target.value;
            this.load_sources();
        });

        this.body.on('click', '.nks-new-source-btn', () => {
            this.new_knowledge_source();
        });

        this.body.on('click', '.nks-ai-assist-source-btn', () => {
            this.show_ai_assist_source_dialog();
        });

        this.body.on('click', '.nks-source-dashboard-btn', (e) => {
            this.show_source_dashboard($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-check-btn', (e) => {
            this.check_readiness($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-approve-btn', (e) => {
            this.approve_unit($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-review-btn', (e) => {
            this.mark_needs_review($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-clear-review-btn', (e) => {
            this.clear_review($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-ready-publish-btn', (e) => {
            this.mark_ready_to_publish($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-technical-details-btn', () => {
            this.show_ai_preparation_technical_details();
        });
    }

    load() {
        this.load_summary();
        this.load_units();
        this.load_source_summary();
        this.load_sources();
    }

    load_summary() {
        frappe.call({
            method: this.api.get_summary,
            freeze: false,
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    this.summary = {};
                    this.render_active_tenant();
                    this.render_active_context_panel();
                    this.refresh_current_tab_if_needed();
                    return;
                }

                this.summary = r.message.summary || {};

                this.merge_active_context(
                    r.message.active_context || {},
                    this.summary || {}
                );

                this.render_active_tenant();
                this.render_active_context_panel();
                this.refresh_current_tab_if_needed();
            }
        });
    }

    load_units() {
        frappe.call({
            method: this.api.get_units,
            args: {
                filters: this.filters
            },
            freeze: false,
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    this.units = [];
                    this.render_units_error();
                    return;
                }

                this.units = r.message.units || [];

                this.merge_active_context(
                    r.message.active_context || {},
                    r.message.summary || {}
                );

                if (r.message.active_tenant && !this.active_tenant) {
                    this.active_tenant = r.message.active_tenant;
                }

                this.render_active_tenant();
                this.render_active_context_panel();

                if (this.active_tab === 'units') {
                    this.render_units_table();
                }
            }
        });
    }

    load_source_summary() {
        frappe.call({
            method: this.api.get_source_summary,
            freeze: false,
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    this.source_summary = {};
                    this.refresh_current_tab_if_needed();

                    if (this.active_tab === 'sources') {
                        this.render_active_tab();
                    }

                    return;
                }

                this.source_summary = r.message.summary || {};

                this.merge_active_context(
                    r.message.active_context || {},
                    this.source_summary || {}
                );

                if (r.message.active_tenant && !this.active_tenant) {
                    this.active_tenant = r.message.active_tenant;
                }

                this.render_active_tenant();
                this.render_active_context_panel();

                if (this.active_tab === 'sources') {
                    this.render_active_tab();
                }
            }
        });
    }

    load_sources() {
        frappe.call({
            method: this.api.get_sources,
            args: {
                filters: this.source_filters
            },
            freeze: false,
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    this.sources = [];
                    this.render_sources_error();
                    return;
                }

                this.sources = r.message.sources || [];

                this.merge_active_context(
                    r.message.active_context || {},
                    r.message.summary || {}
                );

                if (r.message.active_tenant && !this.active_tenant) {
                    this.active_tenant = r.message.active_tenant;
                }

                this.render_active_tenant();
                this.render_active_context_panel();

                if (this.active_tab === 'sources') {
                    this.render_sources_table();
                }
            }
        });
    }

    render_active_tenant() {
        const text = this.active_tenant
            ? `Active Tenant: ${frappe.utils.escape_html(this.active_tenant)}`
            : 'Active Tenant: User Context';

        this.body.find('#nks-active-tenant-pill').html(text);
    }

    refresh_current_tab_if_needed() {
        if (this.active_tab === 'overview') {
            this.render_active_tab();
        }
    }

    render_active_tab() {
        const $content = this.body.find('#nks-tab-content');

        if (this.active_tab === 'overview') {
            $content.html(this.get_overview_html());
            return;
        }

        if (this.active_tab === 'sources') {
            $content.html(this.get_sources_html());
            this.render_sources_table();
            return;
        }

        if (this.active_tab === 'ingestion') {
            $content.html(this.get_ingestion_html());
            return;
        }

        if (this.active_tab === 'units') {
            $content.html(this.get_units_html());
            this.render_units_table();
            return;
        }

        if (this.active_tab === 'indexing') {
            $content.html(this.get_indexing_html());
            return;
        }

        if (this.active_tab === 'testing') {
            $content.html(this.get_testing_html());
            return;
        }

        if (this.active_tab === 'gaps') {
            $content.html(this.get_gaps_html());
            return;
        }

        if (this.active_tab === 'publish') {
            $content.html(this.get_publish_html());
        }
    }

    get_overview_html() {
        return `
            <div class="nks-summary-grid">
                ${this.get_summary_cards_html()}
            </div>

            <div class="nks-section-panel">
                <div class="nks-section-head">
                    <h3>Studio Lifecycle</h3>
                    <p>
                        Nexus Studio manages the full knowledge lifecycle from original sources
                        to AI-ready, tested, and publishable knowledge.
                    </p>
                </div>

                <div class="nks-stage-grid">
                    ${this.get_stage_card_html('📚', 'Knowledge Sources', 'Register and govern original source material.')}
                    ${this.get_stage_card_html('📥', 'Intake & Ingestion', 'Extract, clean, and convert sources into Knowledge Units.', true)}
                    ${this.get_stage_card_html('🧠', 'Knowledge Units', 'Classify, approve, and prepare governed business knowledge.')}
                    ${this.get_stage_card_html('⚙️', 'AI Preparation', 'Prepare approved knowledge for reliable AI search and answers.', true)}
                    ${this.get_stage_card_html('🧪', 'Testing & Validation', 'Validate retrieval, citations, confidence, and answers.')}
                    ${this.get_stage_card_html('📊', 'Knowledge Gaps', 'Identify missing, weak, stale, or failed knowledge.', true)}
                    ${this.get_stage_card_html('🚀', 'Publish Readiness', 'Control what knowledge can power AI channels.')}
                    ${this.get_stage_card_html('🛡️', 'Governance', 'Maintain tenant, access, and source traceability.', true)}
                </div>
            </div>
        `;
    }

    get_stage_card_html(icon, title, text, teal = false) {
        return `
            <div class="nks-stage-card ${teal ? 'nks-stage-card-teal' : ''}">
                <div class="nks-stage-icon">${icon}</div>
                <h4 class="nks-stage-title">${frappe.utils.escape_html(title)}</h4>
                <p class="nks-stage-text">${frappe.utils.escape_html(text)}</p>
            </div>
        `;
    }

    get_summary_cards_html() {
        const s = this.summary || {};

        return `
            ${this.get_summary_card_html('Total Knowledge Units', s.total_units || 0)}
            ${this.get_summary_card_html('Approved', s.approved_units || 0)}
            ${this.get_summary_card_html('Ready for AI Preparation', s.ready_for_chunking_units || 0, 'good')}
            ${this.get_summary_card_html('Ready to Publish', s.ready_to_publish_units || 0, 'good')}
            ${this.get_summary_card_html('Missing Required', s.missing_required_units || 0, 'warn')}
            ${this.get_summary_card_html('Needs Review', s.needs_review_units || 0, 'warn')}
            ${this.get_summary_card_html('Prepared', s.chunked_units || 0)}
            ${this.get_summary_card_html('Search Ready', s.embedded_units || 0)}
        `;
    }

    get_summary_card_html(label, value, type = '') {
        const type_class = type === 'good'
            ? 'nks-summary-card-good'
            : type === 'warn'
                ? 'nks-summary-card-warn'
                : '';

        return `
            <div class="nks-summary-card ${type_class}">
                <div class="nks-summary-label">${frappe.utils.escape_html(label)}</div>
                <div class="nks-summary-value">${frappe.utils.escape_html(String(value || 0))}</div>
            </div>
        `;
    }

    get_sources_html() {
        const s = this.source_summary || {};

        return `
            <div class="nks-summary-grid">
                ${this.get_summary_card_html('Total Sources', s.total_sources || 0)}
                ${this.get_summary_card_html('Approved for Ingestion', s.approved_for_ingestion || 0, 'good')}
                ${this.get_summary_card_html('Ingested', s.ingested || 0, 'good')}
                ${this.get_summary_card_html('Partially Ingested', s.partially_ingested || 0)}
                ${this.get_summary_card_html('Sync Failed', s.sync_failed || 0, 'warn')}
                ${this.get_summary_card_html('Stale', s.stale || 0, 'warn')}
                ${this.get_summary_card_html('Disabled', s.disabled || 0)}
            </div>

            <div class="nks-section-panel">
                <div class="nks-section-head">
                    <h3>Knowledge Sources</h3>
                    <p>
                        Register, govern, and review original source material before it becomes usable by Nexus answers.
                    </p>
                </div>

                <div class="nks-toolbar">
                    <div class="nks-toolbar-left">
                        <input class="form-control nks-source-search" placeholder="Search knowledge sources..." value="${frappe.utils.escape_html(this.source_filters.search || '')}" />

                        <select class="form-control nks-source-status-filter">
                            ${this.get_source_status_options_html()}
                        </select>

                        <select class="form-control nks-source-sync-filter">
                            ${this.get_source_sync_options_html()}
                        </select>

                        <select class="form-control nks-source-disabled-filter">
                            <option value="" ${this.source_filters.disabled === '' ? 'selected' : ''}>Enabled/Disabled: All</option>
                            <option value="0" ${this.source_filters.disabled === '0' ? 'selected' : ''}>Enabled Only</option>
                            <option value="1" ${this.source_filters.disabled === '1' ? 'selected' : ''}>Disabled Only</option>
                        </select>
                    </div>

                    <div class="nks-toolbar-right">
                        <button class="btn btn-primary btn-sm nks-new-source-btn">
                            New Knowledge Source
                        </button>

                        <button class="btn btn-default btn-sm nks-ai-assist-source-btn">
                            AI Assist Source
                        </button>

                        <button class="btn btn-default btn-sm nks-refresh-btn">
                            Refresh
                        </button>
                    </div>
                </div>

                <div class="nks-table-wrap">
                    <table class="table table-bordered nks-table">
                        <thead>
                            <tr>
                                <th style="width: 23%;">Source</th>
                                <th style="width: 22%;">Business Scope</th>
                                <th style="width: 12%;">Status</th>
                                <th style="width: 17%;">Readiness</th>
                                <th style="width: 14%;">Next Step</th>
                                <th style="width: 12%;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="nks-knowledge-source-rows">
                            <tr>
                                <td colspan="6" class="text-muted text-center">Loading knowledge sources...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    get_source_status_options_html() {
        const statuses = [
            ['', 'All Status'],
            ['Draft', 'Draft'],
            ['Pending Review', 'Pending Review'],
            ['Processed', 'Processed'],
            ['Validated', 'Validated'],
            ['Ready to Publish', 'Ready to Publish'],
            ['Published', 'Published'],
            ['Disabled', 'Disabled']
        ];

        return statuses.map(([value, label]) => {
            return `<option value="${frappe.utils.escape_html(value)}" ${this.source_filters.status === value ? 'selected' : ''}>${frappe.utils.escape_html(label)}</option>`;
        }).join('');
    }

    get_source_sync_options_html() {
        const sync_statuses = [
            ['', 'Sync: All'],
            ['Not Synced', 'Not Synced'],
            ['Pending', 'Pending'],
            ['Running', 'Running'],
            ['Completed', 'Completed'],
            ['Failed', 'Failed']
        ];

        return sync_statuses.map(([value, label]) => {
            return `<option value="${frappe.utils.escape_html(value)}" ${this.source_filters.sync_status === value ? 'selected' : ''}>${frappe.utils.escape_html(label)}</option>`;
        }).join('');
    }

    new_knowledge_source() {
        const context = this.active_context || {};
        const values = {};

        ['tenant', 'ecosystem', 'business_unit', 'project', 'channel', 'context'].forEach((fieldname) => {
            if (context[fieldname] && context[fieldname] !== '-') {
                values[fieldname] = context[fieldname];
            }
        });

        frappe.new_doc('Nexus Knowledge Source', values);
    }

    show_ai_assist_source_dialog() {
        const context = this.active_context || {};
        const tenant = context.tenant || this.active_tenant || '';

        const dialog = new frappe.ui.Dialog({
            title: 'AI Assist Knowledge Source',
            size: 'large',
            fields: [
                {
                    fieldname: 'source_title',
                    fieldtype: 'Data',
                    label: 'Source Title',
                    description: 'Optional. If blank, AI will suggest a title from the content.'
                },
                {
                    fieldname: 'manual_content',
                    fieldtype: 'Small Text',
                    label: 'Manual Content',
                    reqd: 1,
                    description: 'Paste the plain text content you want to add as a Knowledge Source.'
                },
                {
                    fieldname: 'content_handling',
                    fieldtype: 'Select',
                    label: 'Content Handling',
                    options: [
                        'Keep content unchanged',
                        'Rewrite for clarity',
                        'Generate improved version from content'
                    ].join('\n'),
                    default: 'Keep content unchanged',
                    reqd: 1
                },
                {
                    fieldname: 'use_existing_values',
                    fieldtype: 'Check',
                    label: 'Prefer existing database values where suitable',
                    default: 1
                },
                {
                    fieldname: 'fields_section',
                    fieldtype: 'Section Break',
                    label: 'Fields to Suggest'
                },
                {
                    fieldname: 'tenant_locked_note',
                    fieldtype: 'HTML',
                    options: `
                        <div class="nks-ai-locked-note">
                            <b>Tenant:</b> ${frappe.utils.escape_html(tenant || 'Active Studio Tenant')}<br>
                            Tenant is controlled by the active Studio context and cannot be changed during AI-assisted source creation.
                        </div>
                    `
                },
                {
                    fieldname: 'suggest_business_unit',
                    fieldtype: 'Check',
                    label: 'Business Unit',
                    default: 1,
                    description: context.business_unit ? `Current: ${context.business_unit}` : ''
                },
                {
                    fieldname: 'suggest_project',
                    fieldtype: 'Check',
                    label: 'Project',
                    default: 0,
                    description: context.project ? `Current: ${context.project}` : ''
                },
                {
                    fieldname: 'suggest_context',
                    fieldtype: 'Check',
                    label: 'Context',
                    default: 1
                },
                {
                    fieldname: 'suggest_sub_context',
                    fieldtype: 'Check',
                    label: 'Sub Context',
                    default: 1
                },
                {
                    fieldname: 'suggest_entity_type',
                    fieldtype: 'Check',
                    label: 'Entity Type',
                    default: 1
                },
                {
                    fieldname: 'suggest_entity',
                    fieldtype: 'Check',
                    label: 'Entity',
                    default: 1
                },
                {
                    fieldname: 'suggest_topic',
                    fieldtype: 'Check',
                    label: 'Topic',
                    default: 1
                },
                {
                    fieldname: 'suggest_access_policy',
                    fieldtype: 'Check',
                    label: 'Access Policy',
                    default: 1
                },
                {
                    fieldname: 'suggest_priority',
                    fieldtype: 'Check',
                    label: 'Priority',
                    default: 1
                },
                {
                    fieldname: 'preview_section',
                    fieldtype: 'Section Break',
                    label: 'AI Suggestion Preview'
                },
                {
                    fieldname: 'preview_html',
                    fieldtype: 'HTML'
                }
            ],
            primary_action_label: 'Analyze Content',
            primary_action: (values) => {
                this.generate_source_ai_suggestion(dialog, values);
            }
        });

        dialog.show();
    }

    get_ai_source_active_context() {
        const context = this.active_context || {};

        return {
            tenant: context.tenant || this.active_tenant || '',
            business_unit: context.business_unit || '',
            project: context.project || '',
            context: context.context || '',
            channel: context.channel || '',
            ecosystem: context.ecosystem || ''
        };
    }

    get_fields_to_suggest_from_dialog(values) {
        const fields = [];

        if (values.suggest_business_unit) {
            fields.push('business_unit');
        }

        if (values.suggest_project) {
            fields.push('project');
        }

        if (values.suggest_context) {
            fields.push('context');
        }

        if (values.suggest_sub_context) {
            fields.push('sub_context');
        }

        if (values.suggest_entity_type) {
            fields.push('entity_type');
        }

        if (values.suggest_entity) {
            fields.push('entity');
        }

        if (values.suggest_topic) {
            fields.push('topic');
        }

        if (values.suggest_access_policy) {
            fields.push('access_policy');
        }

        if (values.suggest_priority) {
            fields.push('priority');
        }

        return fields;
    }

    normalize_source_content_handling(value) {
        if (value === 'Rewrite for clarity') {
            return 'rewrite_for_clarity';
        }

        if (value === 'Generate improved version from content') {
            return 'generate_improved_version';
        }

        return 'keep_unchanged';
    }

    generate_source_ai_suggestion(dialog, values) {
        const manual_content = values.manual_content || '';

        if (!manual_content.trim()) {
            frappe.msgprint('Please enter Manual Content.');
            return;
        }

        const fields_to_suggest = this.get_fields_to_suggest_from_dialog(values);

        if (!fields_to_suggest.length) {
            frappe.msgprint('Please select at least one field to suggest.');
            return;
        }

        const content_handling = this.normalize_source_content_handling(values.content_handling);

        frappe.call({
            method: this.api.suggest_source_fields,
            args: {
                source_title: values.source_title || '',
                manual_content: manual_content,
                content_handling: content_handling,
                active_context: JSON.stringify(this.get_ai_source_active_context()),
                fields_to_suggest: JSON.stringify(fields_to_suggest),
                use_existing_values: values.use_existing_values ? 1 : 0
            },
            freeze: true,
            freeze_message: 'Analyzing source content...',
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    frappe.msgprint(
                        r.message && r.message.message
                            ? r.message.message
                            : 'Unable to generate AI suggestion.'
                    );
                    return;
                }

                dialog.ai_suggestion = r.message.suggestion || {};
                dialog.original_manual_content = manual_content;
                dialog.fields_to_suggest = fields_to_suggest;
                dialog.content_handling = content_handling;

                this.render_ai_source_suggestion_preview(dialog);
            }
        });
    }

    render_ai_source_suggestion_preview(dialog) {
        const suggestion = dialog.ai_suggestion || {};
        const content_handling = dialog.content_handling || 'keep_unchanged';

        const content_changed = (
            content_handling !== 'keep_unchanged' &&
            suggestion.manual_content
        );

        const tenant = (this.active_context && this.active_context.tenant) || this.active_tenant || '';

        const html = `
            <div style="padding-top: 10px;">
                <div class="alert alert-info" style="margin-bottom: 12px;">
                    Review the AI suggestion below. Nothing is saved automatically.
                </div>

                <h5>Basic</h5>
                <table class="table table-bordered">
                    <tbody>
                        <tr>
                            <th style="width: 180px;">Title</th>
                            <td>${frappe.utils.escape_html(suggestion.source_title || '')}</td>
                        </tr>
                        <tr>
                            <th>Source Type</th>
                            <td>${frappe.utils.escape_html(suggestion.source_type || 'Manual')}</td>
                        </tr>
                        <tr>
                            <th>Status</th>
                            <td>${frappe.utils.escape_html(suggestion.status || 'Draft')}</td>
                        </tr>
                        <tr>
                            <th>Priority</th>
                            <td>${frappe.utils.escape_html(String(suggestion.priority || 0))}</td>
                        </tr>
                    </tbody>
                </table>

                ${
                    content_changed
                        ? `
                            <h5>Suggested Manual Content</h5>
                            <div style="white-space: pre-wrap; border: 1px solid #d8e5ff; border-radius: 8px; padding: 10px; max-height: 260px; overflow: auto;">
                                ${frappe.utils.escape_html(suggestion.manual_content || '')}
                            </div>
                        `
                        : `
                            <h5>Manual Content</h5>
                            <div class="text-muted">
                                Content will be kept unchanged.
                            </div>
                        `
                }

                <h5 style="margin-top: 16px;">Suggested Classification</h5>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th>Suggested Value</th>
                            <th>Existing Match</th>
                            <th>Confidence</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Tenant</td>
                            <td><b>${frappe.utils.escape_html(tenant)}</b></td>
                            <td><span class="indicator-pill blue">Locked</span></td>
                            <td>-</td>
                            <td>Tenant is fixed from active Studio context.</td>
                        </tr>
                        ${this.get_ai_suggestion_field_row('Business Unit', suggestion.business_unit)}
                        ${this.get_ai_suggestion_field_row('Project', suggestion.project)}
                        ${this.get_ai_suggestion_field_row('Context', suggestion.context)}
                        ${this.get_ai_suggestion_field_row('Sub Context', suggestion.sub_context)}
                        ${this.get_ai_suggestion_field_row('Entity Type', suggestion.entity_type)}
                        ${this.get_ai_suggestion_field_row('Entity', suggestion.entity)}
                        ${this.get_ai_suggestion_field_row('Topic', suggestion.topic)}
                        ${this.get_ai_suggestion_field_row('Access Policy', suggestion.access_policy)}
                    </tbody>
                </table>

                ${
                    suggestion.warnings && suggestion.warnings.length
                        ? `
                            <h5>Warnings</h5>
                            <ul>
                                ${suggestion.warnings.map((warning) => {
                                    return `<li>${frappe.utils.escape_html(warning)}</li>`;
                                }).join('')}
                            </ul>
                        `
                        : ''
                }
            </div>
        `;

        dialog.fields_dict.preview_html.$wrapper.html(html);

        if (!dialog.$wrapper.find('.nks-create-assisted-source-btn').length) {
            dialog.$wrapper.find('.modal-footer').prepend(`
                <button class="btn btn-primary btn-sm nks-create-assisted-source-btn">
                    Review & Create Draft
                </button>
            `);

            dialog.$wrapper.find('.nks-create-assisted-source-btn').on('click', () => {
                this.show_create_assisted_source_dialog(dialog);
            });
        }
    }

    get_ai_suggestion_field_row(label, data) {
        data = data || {};

        const matched = data.matched_existing
            ? '<span class="indicator-pill green">Matched</span>'
            : '<span class="indicator-pill orange">New / Suggested</span>';

        const confidence = data.confidence
            ? `${Math.round(Number(data.confidence) * 100)}%`
            : '-';

        return `
            <tr>
                <td>${frappe.utils.escape_html(label)}</td>
                <td><b>${frappe.utils.escape_html(data.value || '')}</b></td>
                <td>${matched}</td>
                <td>${frappe.utils.escape_html(confidence)}</td>
                <td>${frappe.utils.escape_html(data.reason || '')}</td>
            </tr>
        `;
    }

    show_create_assisted_source_dialog(parent_dialog) {
        const suggestion = parent_dialog.ai_suggestion || {};
        const context = this.active_context || {};
        const content_handling = parent_dialog.content_handling || 'keep_unchanged';

        const final_content = (
            content_handling !== 'keep_unchanged' &&
            suggestion.manual_content
        )
            ? suggestion.manual_content
            : (parent_dialog.original_manual_content || '');

        const tenant = context.tenant || this.active_tenant || '';

        const review_dialog = new frappe.ui.Dialog({
            title: 'Review & Create Draft Knowledge Source',
            size: 'large',
            fields: [
                {
                    fieldname: 'source_title',
                    fieldtype: 'Data',
                    label: 'Source Title',
                    reqd: 1,
                    default: suggestion.source_title || ''
                },
                {
                    fieldname: 'manual_content',
                    fieldtype: 'Small Text',
                    label: 'Manual Content to Save',
                    reqd: 1,
                    default: final_content,
                    description: 'This plain text content will be saved in the Knowledge Source.'
                },
                {
                    fieldname: 'classification_section',
                    fieldtype: 'Section Break',
                    label: 'Final Classification'
                },
                {
                    fieldname: 'tenant',
                    fieldtype: 'Data',
                    label: 'Tenant',
                    read_only: 1,
                    default: tenant,
                    description: 'Tenant is fixed from the active Studio context.'
                },
                {
                    fieldname: 'business_unit',
                    fieldtype: 'Data',
                    label: 'Business Unit',
                    default: this.get_suggestion_or_context_value(suggestion.business_unit, context.business_unit),
                    description: 'AI may suggest this value from existing Business Units. You can edit it before creating the source.'
                },
                {
                    fieldname: 'project',
                    fieldtype: 'Data',
                    label: 'Project',
                    default: this.get_suggestion_or_context_value(suggestion.project, context.project)
                },
                {
                    fieldname: 'context',
                    fieldtype: 'Data',
                    label: 'Context',
                    default: this.get_suggestion_or_context_value(suggestion.context, context.context)
                },
                {
                    fieldname: 'sub_context',
                    fieldtype: 'Data',
                    label: 'Sub Context',
                    default: this.get_suggestion_value(suggestion.sub_context)
                },
                {
                    fieldname: 'entity_type',
                    fieldtype: 'Data',
                    label: 'Entity Type',
                    default: this.get_suggestion_value(suggestion.entity_type)
                },
                {
                    fieldname: 'entity',
                    fieldtype: 'Data',
                    label: 'Entity',
                    default: this.get_suggestion_value(suggestion.entity)
                },
                {
                    fieldname: 'topic',
                    fieldtype: 'Data',
                    label: 'Topic',
                    default: this.get_suggestion_value(suggestion.topic)
                },
                {
                    fieldname: 'governance_section',
                    fieldtype: 'Section Break',
                    label: 'Governance'
                },
                {
                    fieldname: 'access_policy',
                    fieldtype: 'Select',
                    label: 'Access Policy',
                    options: [
                        'Public',
                        'Internal',
                        'Restricted'
                    ].join('\n'),
                    default: this.get_suggestion_value(suggestion.access_policy) || 'Public'
                },
                {
                    fieldname: 'priority',
                    fieldtype: 'Int',
                    label: 'Priority',
                    default: suggestion.priority !== undefined && suggestion.priority !== null
                        ? suggestion.priority
                        : 10
                }
            ],
            primary_action_label: 'Create Draft Source',
            primary_action: (values) => {
                this.create_assisted_knowledge_source(parent_dialog, review_dialog, values);
            }
        });

        review_dialog.show();
    }

    get_suggestion_value(field) {
        if (!field) {
            return '';
        }

        if (typeof field === 'object') {
            return field.value || '';
        }

        return field || '';
    }

    get_suggestion_or_context_value(field, context_value) {
        const suggested_value = this.get_suggestion_value(field);

        if (suggested_value) {
            return suggested_value;
        }

        if (context_value && context_value !== '-') {
            return context_value;
        }

        return '';
    }

    create_assisted_knowledge_source(parent_dialog, review_dialog, values) {
        const tenant = this.active_context && this.active_context.tenant
            ? this.active_context.tenant
            : (this.active_tenant || '');

        const suggestion = {
            source_title: values.source_title || 'AI Assisted Knowledge Source',
            source_type: 'Manual',
            manual_content: values.manual_content || '',
            tenant: {
                value: tenant
            },
            business_unit: {
                value: values.business_unit || ''
            },
            project: {
                value: values.project || ''
            },
            context: {
                value: values.context || ''
            },
            sub_context: {
                value: values.sub_context || ''
            },
            entity_type: {
                value: values.entity_type || ''
            },
            entity: {
                value: values.entity || ''
            },
            topic: {
                value: values.topic || ''
            },
            access_policy: {
                value: values.access_policy || 'Public'
            },
            priority: values.priority !== undefined && values.priority !== null
                ? values.priority
                : 10,
            status: 'Draft'
        };

        const fields_to_apply = [
            'business_unit',
            'project',
            'context',
            'sub_context',
            'entity_type',
            'entity',
            'topic',
            'access_policy',
            'priority'
        ];

        frappe.call({
            method: this.api.create_assisted_source,
            args: {
                suggestion: JSON.stringify(suggestion),
                original_manual_content: values.manual_content || '',
                fields_to_apply: JSON.stringify(fields_to_apply),
                active_context: JSON.stringify(this.get_ai_source_active_context())
            },
            freeze: true,
            freeze_message: 'Creating draft Knowledge Source...',
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    frappe.msgprint(
                        r.message && r.message.message
                            ? r.message.message
                            : 'Unable to create draft Knowledge Source.'
                    );
                    return;
                }

                review_dialog.hide();
                parent_dialog.hide();

                frappe.show_alert({
                    message: r.message.message || 'Draft Knowledge Source created.',
                    indicator: 'green'
                });

                this.load_sources();
                this.load_source_summary();

                if (r.message.name) {
                    frappe.set_route('Form', 'Nexus Knowledge Source', r.message.name);
                }
            }
        });
    }

    get_ingestion_html() {
        return this.get_placeholder_section(
            'Intake & Ingestion',
            'Convert approved knowledge sources into structured Knowledge Units through extraction, cleaning, splitting, and traceable ingestion runs.',
            [
                'This tab should use Nexus Knowledge Source and Nexus Knowledge Ingestion Run.',
                'It will handle extract text, create/update units, duplicate detection, and failure logs.',
                'This should be implemented after Knowledge Source is created.'
            ]
        );
    }

    get_units_html() {
        return `
            <div class="nks-section-panel">
                <div class="nks-section-head">
                    <h3>Knowledge Units</h3>
                    <p>
                        Review tenant knowledge units, validate metadata, approve content,
                        mark review status, and confirm publishing readiness.
                    </p>
                </div>

                <div class="nks-toolbar">
                    <div class="nks-toolbar-left">
                        <input class="form-control nks-search" placeholder="Search knowledge units..." value="${frappe.utils.escape_html(this.filters.search || '')}" />

                        <select class="form-control nks-status-filter">
                            ${this.get_status_options_html()}
                        </select>

                        <select class="form-control nks-review-filter">
                            <option value="" ${this.filters.needs_review === '' ? 'selected' : ''}>Review: All</option>
                            <option value="1" ${this.filters.needs_review === '1' ? 'selected' : ''}>Needs Review</option>
                            <option value="0" ${this.filters.needs_review === '0' ? 'selected' : ''}>Not Marked Review</option>
                        </select>

                        <select class="form-control nks-readiness-filter">
                            <option value="" ${this.get_readiness_filter_value() === '' ? 'selected' : ''}>Readiness: All</option>
                            <option value="missing" ${this.get_readiness_filter_value() === 'missing' ? 'selected' : ''}>Missing Required Fields</option>
                            <option value="ready_for_chunking" ${this.get_readiness_filter_value() === 'ready_for_chunking' ? 'selected' : ''}>Ready for AI Preparation</option>
                            <option value="ready_to_publish" ${this.get_readiness_filter_value() === 'ready_to_publish' ? 'selected' : ''}>Ready to Publish</option>
                        </select>
                    </div>

                    <div class="nks-toolbar-right">
                        <button class="btn btn-default btn-sm nks-refresh-btn">Refresh</button>
                    </div>
                </div>

                <div class="nks-table-wrap">
                    <table class="table table-bordered nks-table">
                        <thead>
                            <tr>
                                <th style="width: 18%;">Knowledge Unit</th>
                                <th style="width: 11%;">Tenant</th>
                                <th style="width: 12%;">Business Unit</th>
                                <th style="width: 15%;">Context</th>
                                <th style="width: 10%;">Status</th>
                                <th style="width: 9%;">AI Prep</th>
                                <th style="width: 11%;">Readiness</th>
                                <th style="width: 14%;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="nks-knowledge-unit-rows">
                            <tr>
                                <td colspan="8" class="text-muted text-center">Loading knowledge units...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    get_status_options_html() {
        const statuses = [
            ['', 'All Status'],
            ['Draft', 'Draft'],
            ['Approved', 'Approved'],
            ['Chunked', 'Prepared'],
            ['Embedded', 'Search Ready'],
            ['Tested', 'Tested'],
            ['Ready to Publish', 'Ready to Publish'],
            ['Published', 'Published'],
            ['Needs Review', 'Needs Review']
        ];

        return statuses.map(([value, label]) => {
            return `<option value="${frappe.utils.escape_html(value)}" ${this.filters.status === value ? 'selected' : ''}>${frappe.utils.escape_html(label)}</option>`;
        }).join('');
    }

    get_readiness_filter_value() {
        if (this.filters.only_missing) {
            return 'missing';
        }

        if (this.filters.only_ready_for_chunking) {
            return 'ready_for_chunking';
        }

        if (this.filters.only_ready_to_publish) {
            return 'ready_to_publish';
        }

        return '';
    }

    get_indexing_html() {
        return `
            <div class="nks-section-panel">
                <div class="nks-section-head">
                    <h3>AI Preparation</h3>
                    <p>
                        Prepare approved Knowledge Units for reliable AI search, answer generation,
                        source citation, and validation. Technical preparation details remain available
                        on demand for administrators and implementation teams.
                    </p>
                </div>

                <div class="nks-placeholder">
                    <div class="nks-placeholder-box">
                        <h4>Preparation Workflow</h4>
                        <p>• Prepare approved Knowledge Units for AI usage.</p>
                        <p>• Identify knowledge that is not yet prepared, partially prepared, or failed during preparation.</p>
                        <p>• Show business-friendly readiness such as Prepared, Search Ready, Needs Preparation, and Preparation Issues.</p>
                        <p>• Keep chunking, embedding, and indexing diagnostics available through the technical details view.</p>

                        <div class="nks-inline-actions">
                            <button class="btn btn-default btn-sm nks-technical-details-btn">
                                View Technical Details
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    get_testing_html() {
        return this.get_placeholder_section(
            'Testing & Validation',
            'Validate source retrieval, grounded answers, citations, confidence, access status, and fallback behaviour.',
            [
                'This tab should connect with Nexus Knowledge Test Case, Nexus Knowledge Test Run, and Nexus Query Log.',
                'It will support run single test, run tenant suite, view failed diagnostics, and copy combined diagnostics.',
                'This will align with the Knowledge Testing Lab work already completed.'
            ]
        );
    }

    get_gaps_html() {
        return this.get_placeholder_section(
            'Knowledge Gaps',
            'Identify missing, weak, stale, or poorly retrievable knowledge from failed tests and query logs.',
            [
                'Inputs should include no-context answers, fallback answers, low-confidence responses, and failed expected-source checks.',
                'Actions should include create Knowledge Source, create Knowledge Unit, mark Needs Review, and create test case from gap.',
                'This can later use a Nexus Knowledge Gap doctype.'
            ]
        );
    }

    get_publish_html() {
        return this.get_placeholder_section(
            'Publish Readiness',
            'Control which validated knowledge can power Q&A, Nexus Live, AI Agents, and connected applications.',
            [
                'Publishing should require approval, AI preparation, validation, tenant scope, and safety checks.',
                'This tab will later manage Publish, Unpublish, channel targeting, and review rollback.',
                'Current Knowledge Unit Ready action remains available in the Knowledge Units tab.'
            ]
        );
    }

    get_placeholder_section(title, description, points) {
        const point_html = points.map((point) => {
            return `<p>• ${frappe.utils.escape_html(point)}</p>`;
        }).join('');

        return `
            <div class="nks-section-panel">
                <div class="nks-section-head">
                    <h3>${frappe.utils.escape_html(title)}</h3>
                    <p>${frappe.utils.escape_html(description)}</p>
                </div>

                <div class="nks-placeholder">
                    <div class="nks-placeholder-box">
                        <h4>Planned Studio Workflow</h4>
                        ${point_html}
                    </div>
                </div>
            </div>
        `;
    }

    render_sources_table() {
        const $rows = this.body.find('#nks-knowledge-source-rows');

        if (!$rows.length) {
            return;
        }

        if (!this.sources.length) {
            $rows.html(`
                <tr>
                    <td colspan="6" class="text-muted text-center">
                        No knowledge sources found.
                    </td>
                </tr>
            `);
            return;
        }

        const html = this.sources.map((row) => {
            const status = row.status || 'Draft';
            const source_type = row.source_type || 'Manual';
            const readiness_badge = this.get_source_readiness_badge(row);
            const next_step = row.next_action_label || 'Review source';

            const disabled_badge = row.disabled
                ? `<span class="nks-badge nks-badge-warn">Disabled</span>`
                : '';

            return `
                <tr>
                    <td>
                        <a href="/app/nexus-knowledge-source/${encodeURIComponent(row.name)}" class="nks-unit-link">
                            ${frappe.utils.escape_html(row.source_title || row.name)}
                        </a>
                        <div class="nks-row-sub">
                            ${frappe.utils.escape_html(source_type)}
                        </div>
                    </td>

                    <td>
                        <div><strong>${frappe.utils.escape_html(row.business_unit || '-')}</strong></div>
                        <div class="nks-row-sub">
                            ${frappe.utils.escape_html(row.context || '-')}
                            ${row.sub_context ? ' / ' + frappe.utils.escape_html(row.sub_context) : ''}
                        </div>
                        <div class="nks-row-sub">
                            ${frappe.utils.escape_html(row.topic || row.entity || '')}
                        </div>
                    </td>

                    <td>
                        <span class="nks-badge">${frappe.utils.escape_html(status)}</span>
                        ${disabled_badge}
                    </td>

                    <td>
                        ${readiness_badge}
                        <div class="nks-row-sub">
                            ${frappe.utils.escape_html(row.readiness_message || '')}
                        </div>
                        ${
                            row.missing_fields && row.missing_fields.length
                                ? `<div class="nks-row-sub">Missing: ${frappe.utils.escape_html(row.missing_fields.join(', '))}</div>`
                                : ''
                        }
                    </td>

                    <td>
                        <span class="nks-badge ${this.get_source_next_step_badge_class(row)}">
                            ${frappe.utils.escape_html(next_step)}
                        </span>
                    </td>

                    <td>
                        <div class="nks-action-row">
                            <button class="btn btn-xs btn-primary nks-source-dashboard-btn" data-name="${frappe.utils.escape_html(row.name)}">
                                Dashboard
                            </button>

                            <a class="btn btn-xs btn-default" href="/app/nexus-knowledge-source/${encodeURIComponent(row.name)}">
                                Review
                            </a>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        $rows.html(html);
    }

    render_sources_error() {
        if (this.active_tab !== 'sources') {
            return;
        }

        const $rows = this.body.find('#nks-knowledge-source-rows');

        if (!$rows.length) {
            return;
        }

        $rows.html(`
            <tr>
                <td colspan="6" class="text-danger text-center">
                    Failed to load knowledge sources.
                </td>
            </tr>
        `);
    }

    get_source_readiness_badge(row) {
        const status = row.readiness_status || 'unknown';
        const label = row.readiness_label || 'Pending';

        let class_name = 'nks-badge-info';

        if (['ready', 'ready_for_validation', 'ready_to_publish', 'published'].includes(status)) {
            class_name = 'nks-badge-good';
        }

        if ([
            'needs_content',
            'needs_classification',
            'needs_review',
            'needs_attention',
            'preparation_failed',
            'disabled'
        ].includes(status)) {
            class_name = 'nks-badge-warn';
        }

        return `
            <span class="nks-badge ${class_name}">
                ${frappe.utils.escape_html(label)}
            </span>
        `;
    }

    get_source_next_step_badge_class(row) {
        const action = row.next_action || '';

        if (['prepare', 'validate', 'publish'].includes(action)) {
            return 'nks-badge-good';
        }

        if (['review'].includes(action)) {
            return 'nks-badge-warn';
        }

        return 'nks-badge-info';
    }

    show_source_dashboard(name) {
        const row = (this.sources || []).find((item) => item.name === name);

        if (!row) {
            frappe.msgprint('Source details are not available. Please refresh and try again.');
            return;
        }

        const readiness_badge = this.get_source_readiness_badge(row);
        const next_step = row.next_action_label || 'Review source';
        const technical_status = row.technical_status || {};
        const action_buttons = this.get_source_dashboard_actions_html(row);

        const missing_fields_html = row.missing_fields && row.missing_fields.length
            ? `
                <ul style="margin: 8px 0 0; padding-left: 18px;">
                    ${row.missing_fields.map((fieldname) => {
                        return `<li>${frappe.utils.escape_html(fieldname)}</li>`;
                    }).join('')}
                </ul>
            `
            : '<p class="text-muted">No blocking missing fields.</p>';

        const dialog = new frappe.ui.Dialog({
            title: `Source Dashboard: ${row.source_title || row.name}`,
            size: 'large',
            fields: [
                {
                    fieldname: 'dashboard_html',
                    fieldtype: 'HTML'
                }
            ]
        });

        dialog.fields_dict.dashboard_html.$wrapper.html(`
            <div class="nks-readiness-dialog">
                <div class="nks-dashboard-grid">
                    <div class="nks-dashboard-card nks-dashboard-card-blue">
                        <h5>Source Summary</h5>
                        <p><b>Source:</b> ${frappe.utils.escape_html(row.source_title || row.name)}</p>
                        <p><b>Type:</b> ${frappe.utils.escape_html(row.source_type || 'Manual')}</p>
                        <p><b>Business Unit:</b> ${frappe.utils.escape_html(row.business_unit || '-')}</p>
                        <p><b>Context:</b> ${frappe.utils.escape_html(row.context || '-')}</p>
                        <p><b>Sub Context:</b> ${frappe.utils.escape_html(row.sub_context || '-')}</p>
                        <p><b>Entity:</b> ${frappe.utils.escape_html(row.entity || '-')}</p>
                        <p><b>Topic:</b> ${frappe.utils.escape_html(row.topic || '-')}</p>
                    </div>

                    <div class="nks-dashboard-card nks-dashboard-card-green">
                        <h5>Readiness</h5>
                        <p>${readiness_badge}</p>
                        <p>${frappe.utils.escape_html(row.readiness_message || '')}</p>
                        <p><b>Next Step:</b> ${frappe.utils.escape_html(next_step)}</p>
                        <p><b>Published:</b> ${row.is_published ? 'Yes' : 'No'}</p>
                    </div>

                    <div class="nks-dashboard-card nks-dashboard-card-warn">
                        <h5>Checks</h5>
                        <p><b>Content:</b> ${row.has_content ? 'Complete' : 'Missing'}</p>
                        <p><b>Classification:</b> ${row.has_classification ? 'Complete' : 'Incomplete'}</p>
                        <p><b>Prepared:</b> ${this.is_source_prepared(row) ? 'Yes' : 'No'}</p>
                        <p><b>Ready for Publish:</b> ${row.can_publish ? 'Yes' : 'No'}</p>
                    </div>

                    <div class="nks-dashboard-card">
                        <h5>Issues</h5>
                        ${missing_fields_html}
                    </div>
                </div>

                <div class="nks-dashboard-actions">
                    <h5 style="margin-top: 0;">Actions</h5>
                    <p class="text-muted" style="margin-bottom: 10px;">
                        Use these actions to move this source through the Studio workflow.
                    </p>

                    <div class="nks-action-row">
                        ${action_buttons}
                    </div>

                    <div class="nks-dashboard-notice">
                        <b>Validation note:</b>
                        Studio validation tests this source directly before publishing.
                        After publishing, public Q&A and Source Quality tests use active retrieval chunks.
                        A published source should have active retrieval chunks before it is available for Nexus answers.
                    </div>
                </div>

                <details>
                    <summary><b>Technical Status</b></summary>
                    <div class="nks-dashboard-technical">
                        <p><b>Status:</b> ${frappe.utils.escape_html(technical_status.status || row.status || '-')}</p>
                        <p><b>Sync Status:</b> ${frappe.utils.escape_html(technical_status.sync_status || row.sync_status || '-')}</p>
                        <p><b>Processing Status:</b> ${frappe.utils.escape_html(technical_status.processing_status || row.processing_status || '-')}</p>
                        <p><b>Quality Status:</b> ${frappe.utils.escape_html(technical_status.quality_status || row.quality_status || '-')}</p>
                        <p><b>Validation Status:</b> ${frappe.utils.escape_html(technical_status.validation_status || row.validation_status || '-')}</p>
                        <p><b>Last Error:</b> ${frappe.utils.escape_html(technical_status.last_error || row.last_error || '-')}</p>
                    </div>
                </details>
            </div>
        `);

        dialog.show();

        dialog.$wrapper.find('.nks-dashboard-review-source-btn').on('click', () => {
            frappe.set_route('Form', 'Nexus Knowledge Source', row.name);
            dialog.hide();
        });

        dialog.$wrapper.find('.nks-dashboard-refresh-source-btn').on('click', () => {
            this.load_sources();
            this.load_source_summary();

            frappe.show_alert({
                message: 'Source status refreshed.',
                indicator: 'blue'
            });

            dialog.hide();
        });

        dialog.$wrapper.find('.nks-dashboard-prepare-source-btn').on('click', () => {
            this.prepare_source_from_dashboard(row.name, dialog);
        });

        dialog.$wrapper.find('.nks-dashboard-validate-source-btn').on('click', () => {
            this.validate_source_from_dashboard(row.name, dialog);
        });

        dialog.$wrapper.find('.nks-dashboard-publish-source-btn').on('click', () => {
            this.publish_source_from_dashboard(row.name, dialog);
        });

        dialog.$wrapper.find('.nks-dashboard-unpublish-source-btn').on('click', () => {
            this.unpublish_source_from_dashboard(row.name, dialog);
        });
    }

    get_source_dashboard_actions_html(row) {
        const buttons = [];

        buttons.push(`
            <button class="btn btn-sm btn-default nks-dashboard-review-source-btn">
                Review Source
            </button>
        `);

        buttons.push(`
            <button class="btn btn-sm btn-default nks-dashboard-refresh-source-btn">
                Refresh Status
            </button>
        `);

        if (row.can_prepare) {
            buttons.push(`
                <button class="btn btn-sm btn-primary nks-dashboard-prepare-source-btn">
                    Prepare Source
                </button>
            `);
        }

        if (row.can_validate) {
            buttons.push(`
                <button class="btn btn-sm btn-primary nks-dashboard-validate-source-btn">
                    Validate Source
                </button>
            `);
        }

        if (row.can_publish) {
            buttons.push(`
                <button class="btn btn-sm btn-primary nks-dashboard-publish-source-btn">
                    Publish Source
                </button>
            `);
        }

        if (row.can_unpublish) {
            buttons.push(`
                <button class="btn btn-sm btn-default nks-dashboard-unpublish-source-btn">
                    Unpublish Source
                </button>
            `);
        }

        if (!row.can_prepare && !row.can_validate && !row.can_publish && !row.can_unpublish) {
            buttons.push(`
                <span class="text-muted" style="align-self: center;">
                    No workflow action available at this stage.
                </span>
            `);
        }

        return buttons.join('');
    }

    is_source_prepared(row) {
        const status = String(row.status || '').toLowerCase();

        const processing_status = String(
            row.processing_status ||
            (row.technical_status && row.technical_status.processing_status) ||
            ''
        ).toLowerCase();

        const sync_status = String(
            row.sync_status ||
            (row.technical_status && row.technical_status.sync_status) ||
            ''
        ).toLowerCase();

        return (
            ['processed', 'prepared', 'ingested', 'ready to publish', 'published'].includes(status) ||
            ['processed', 'prepared', 'completed'].includes(processing_status) ||
            ['processed', 'completed'].includes(sync_status)
        );
    }

    prepare_source_from_dashboard(name, dialog) {
        frappe.msgprint({
            title: 'Prepare Source',
            indicator: 'blue',
            message: `
                <p>The Studio action is ready, but the backend Prepare Source API still needs to be wired.</p>
                <p>For now, open the source and use the existing <b>Process Source</b> button.</p>
                <p>Once the backend API is added, this button will prepare the source directly from Studio.</p>
            `
        });
    }

    validate_source_from_dashboard(name, dialog) {
        const row = (this.sources || []).find((item) => item.name === name);

        if (!row) {
            frappe.msgprint('Source details are not available. Please refresh and try again.');
            return;
        }

        const default_query = this.build_default_source_validation_query(row);

        const validation_dialog = new frappe.ui.Dialog({
            title: 'Validate Source',
            size: 'large',
            fields: [
                {
                    fieldname: 'source_summary_html',
                    fieldtype: 'HTML',
                    options: `
                        <div style="
                            padding: 14px;
                            border-radius: 16px;
                            background:
                                radial-gradient(circle at 100% 0%, rgba(77, 163, 255, 0.10), transparent 30%),
                                linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                            border: 1.5px solid rgba(33, 119, 255, 0.22);
                            margin-bottom: 12px;
                        ">
                            <h5 style="margin: 0 0 8px; color: #0b3c91; font-weight: 950;">
                                Source-Scoped Validation
                            </h5>

                            <p style="margin: 6px 0; color: #314d78; font-size: 12px; font-weight: 700;">
                                <b>Source:</b> ${frappe.utils.escape_html(row.source_title || row.name)}
                            </p>

                            <p style="margin: 6px 0; color: #314d78; font-size: 12px; font-weight: 700;">
                                <b>Business Unit:</b> ${frappe.utils.escape_html(row.business_unit || '-')}
                            </p>

                            <p style="margin: 6px 0; color: #314d78; font-size: 12px; font-weight: 700;">
                                <b>Context:</b> ${frappe.utils.escape_html(row.context || '-')}
                                ${row.sub_context ? ' / ' + frappe.utils.escape_html(row.sub_context) : ''}
                            </p>

                            <p style="margin: 6px 0; color: #314d78; font-size: 12px; font-weight: 700;">
                                <b>Topic:</b> ${frappe.utils.escape_html(row.topic || row.entity || '-')}
                            </p>
                        </div>
                    `
                },
                {
                    fieldname: 'test_query',
                    fieldtype: 'Small Text',
                    label: 'Validation Question',
                    reqd: 1,
                    default: default_query,
                    description: 'The system generated this question from the source metadata. You can edit it before validation.'
                }
            ],
            primary_action_label: 'Validate Source',
            primary_action: (values) => {
                const test_query = (values.test_query || '').trim();

                if (!test_query) {
                    frappe.msgprint('Please enter a validation question.');
                    return;
                }

                frappe.call({
                    method: this.api.validate_source,
                    args: {
                        name: name,
                        test_query: test_query
                    },
                    freeze: true,
                    freeze_message: 'Validating source...',
                    callback: (r) => {
                        const result = r.message || {};

                        if (result.success) {
                            validation_dialog.hide();

                            if (dialog) {
                                dialog.hide();
                            }

                            frappe.msgprint({
                                title: 'Source Validation Passed',
                                indicator: 'green',
                                message: `
                                    <div class="nks-readiness-dialog">
                                        <p><b>Source:</b> ${frappe.utils.escape_html(row.source_title || row.name)}</p>
                                        <p><b>Confidence:</b> ${frappe.utils.escape_html(String(result.confidence || 0))}</p>

                                        <p><b>Validation Question:</b></p>
                                        <div style="
                                            white-space: pre-wrap;
                                            padding: 10px;
                                            border-radius: 10px;
                                            background: #f8fbff;
                                            border: 1px solid rgba(33, 119, 255, 0.20);
                                            margin: 8px 0 12px;
                                        ">
                                            ${frappe.utils.escape_html(result.test_query || test_query)}
                                        </div>

                                        <p><b>Grounded Source Answer:</b></p>
                                        <div style="
                                            white-space: pre-wrap;
                                            padding: 10px;
                                            border-radius: 10px;
                                            background: #f4fffc;
                                            border: 1px solid rgba(0, 184, 148, 0.20);
                                            margin: 8px 0 12px;
                                        ">
                                            ${frappe.utils.escape_html(result.answer || '')}
                                        </div>

                                        <p>This source has been marked as <b>Ready to Publish</b>.</p>
                                    </div>
                                `
                            });

                            this.load_sources();
                            this.load_source_summary();
                            return;
                        }

                        frappe.msgprint({
                            title: 'Source Validation Failed',
                            indicator: 'orange',
                            message: `
                                <div class="nks-readiness-dialog">
                                    <p>${frappe.utils.escape_html(result.message || 'Source validation failed.')}</p>

                                    <p><b>Confidence:</b> ${frappe.utils.escape_html(String(result.confidence || 0))}</p>

                                    <p><b>Validation Question:</b></p>
                                    <div style="
                                        white-space: pre-wrap;
                                        padding: 10px;
                                        border-radius: 10px;
                                        background: #fff8e8;
                                        border: 1px solid rgba(224, 166, 47, 0.28);
                                        margin: 8px 0 12px;
                                    ">
                                        ${frappe.utils.escape_html(result.test_query || test_query)}
                                    </div>

                                    ${
                                        result.answer
                                            ? `
                                                <p><b>Available Source Context:</b></p>
                                                <div style="
                                                    white-space: pre-wrap;
                                                    padding: 10px;
                                                    border-radius: 10px;
                                                    background: #f8fbff;
                                                    border: 1px solid rgba(33, 119, 255, 0.20);
                                                    margin: 8px 0 12px;
                                                ">
                                                    ${frappe.utils.escape_html(result.answer || '')}
                                                </div>
                                            `
                                            : ''
                                    }

                                    <p>Please review the source content, classification, or validation question.</p>
                                </div>
                            `
                        });

                        this.load_sources();
                        this.load_source_summary();
                    }
                });
            }
        });

        validation_dialog.show();
    }

    build_default_source_validation_query(row) {
        const topic = (row.topic || '').trim();
        const entity = (row.entity || '').trim();
        const entity_type = (row.entity_type || '').trim();
        const context = (row.context || '').trim();
        const sub_context = (row.sub_context || '').trim();
        const source_title = (row.source_title || '').trim();
        const business_unit = (row.business_unit || '').trim();

        if (topic && context) {
            return `Explain ${topic} in ${context}.`;
        }

        if (topic && business_unit) {
            return `Explain ${topic} in ${business_unit}.`;
        }

        if (entity && context) {
            return `Explain ${entity} in ${context}.`;
        }

        if (entity && business_unit) {
            return `Explain ${entity} in ${business_unit}.`;
        }

        if (sub_context && context) {
            return `What is ${sub_context} in ${context}?`;
        }

        if (entity_type && entity) {
            return `Explain the ${entity_type} ${entity}.`;
        }

        if (source_title) {
            return `What is ${source_title}?`;
        }

        return 'Summarize this knowledge source.';
    }

    publish_source_from_dashboard(name, dialog) {
        frappe.confirm(
            'Publish this source and make it available for Nexus answers?',
            () => {
                frappe.call({
                    method: this.api.publish_source,
                    args: {
                        name: name
                    },
                    freeze: true,
                    freeze_message: 'Publishing source...',
                    callback: (r) => {
                        const result = r.message || {};

                        if (!result.success) {
                            frappe.msgprint({
                                title: 'Publish Source Failed',
                                indicator: 'orange',
                                message: frappe.utils.escape_html(
                                    result.message || 'Source could not be published.'
                                )
                            });
                            return;
                        }

                        if (dialog) {
                            dialog.hide();
                        }

                        frappe.msgprint({
                            title: 'Source Published',
                            indicator: 'green',
                            message: `
                                <div class="nks-readiness-dialog">
                                    <p>${frappe.utils.escape_html(result.message || 'Knowledge Source published successfully.')}</p>
                                    <p>This source is now marked as <b>Published</b> and available for Nexus answers.</p>
                                </div>
                            `
                        });

                        this.load_sources();
                        this.load_source_summary();
                    }
                });
            }
        );
    }

    unpublish_source_from_dashboard(name, dialog) {
        frappe.confirm(
            'Unpublish this source and remove it from active Nexus answers?',
            () => {
                frappe.call({
                    method: this.api.unpublish_source,
                    args: {
                        name: name
                    },
                    freeze: true,
                    freeze_message: 'Unpublishing source...',
                    callback: (r) => {
                        const result = r.message || {};

                        if (!result.success) {
                            frappe.msgprint({
                                title: 'Unpublish Source Failed',
                                indicator: 'orange',
                                message: frappe.utils.escape_html(
                                    result.message || 'Source could not be unpublished.'
                                )
                            });
                            return;
                        }

                        if (dialog) {
                            dialog.hide();
                        }

                        frappe.msgprint({
                            title: 'Source Unpublished',
                            indicator: 'blue',
                            message: `
                                <div class="nks-readiness-dialog">
                                    <p>${frappe.utils.escape_html(result.message || 'Knowledge Source unpublished.')}</p>
                                    <p>This source is no longer published and is back to <b>Ready to Publish</b>.</p>
                                </div>
                            `
                        });

                        this.load_sources();
                        this.load_source_summary();
                    }
                });
            }
        );
    }

    render_units_table() {
        const $rows = this.body.find('#nks-knowledge-unit-rows');

        if (!$rows.length) {
            return;
        }

        if (!this.units.length) {
            $rows.html(`
                <tr>
                    <td colspan="8" class="text-muted text-center">
                        No knowledge units found.
                    </td>
                </tr>
            `);
            return;
        }

        const html = this.units.map((row) => {
            const status = row.status || row.approval_status || 'Draft';
            const readiness = this.get_readiness_label(row);
            const review_badge = row.needs_review
                ? `<span class="nks-badge nks-badge-warn">Needs Review</span>`
                : '';

            const missing = row.missing_fields && row.missing_fields.length
                ? `<div class="nks-row-sub">Missing: ${frappe.utils.escape_html(row.missing_fields.join(', '))}</div>`
                : '';

            return `
                <tr>
                    <td>
                        <a href="/app/nexus-knowledge-unit/${encodeURIComponent(row.name)}" class="nks-unit-link">
                            ${frappe.utils.escape_html(row.title || row.name)}
                        </a>
                        <div class="nks-row-sub">${frappe.utils.escape_html(row.name || '')}</div>
                    </td>

                    <td>${frappe.utils.escape_html(row.tenant || '')}</td>

                    <td>
                        <div>${frappe.utils.escape_html(row.business_unit || '')}</div>
                        <div class="nks-row-sub">${frappe.utils.escape_html(row.project || '')}</div>
                    </td>

                    <td>
                        <div>${frappe.utils.escape_html(row.context || '')}</div>
                        <div class="nks-row-sub">${frappe.utils.escape_html(row.topic || '')}</div>
                    </td>

                    <td>
                        <span class="nks-badge">${frappe.utils.escape_html(status)}</span>
                        ${review_badge}
                    </td>

                    <td>
                        <strong>${row.chunk_count || 0}</strong>
                        <div class="nks-row-sub">Search Ready: ${row.embedded_chunk_count || 0}</div>
                    </td>

                    <td>
                        ${readiness}
                        ${missing}
                    </td>

                    <td>
                        <div class="nks-action-row">
                            <button class="btn btn-xs btn-default nks-check-btn" data-name="${frappe.utils.escape_html(row.name)}">Check</button>
                            <button class="btn btn-xs btn-primary nks-approve-btn" data-name="${frappe.utils.escape_html(row.name)}">Approve</button>
                            <button class="btn btn-xs btn-default nks-ready-publish-btn" data-name="${frappe.utils.escape_html(row.name)}">Ready</button>
                            ${
                                row.needs_review
                                    ? `<button class="btn btn-xs btn-default nks-clear-review-btn" data-name="${frappe.utils.escape_html(row.name)}">Clear</button>`
                                    : `<button class="btn btn-xs btn-default nks-review-btn" data-name="${frappe.utils.escape_html(row.name)}">Review</button>`
                            }
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        $rows.html(html);
    }

    render_units_error() {
        if (this.active_tab !== 'units') {
            return;
        }

        const $rows = this.body.find('#nks-knowledge-unit-rows');

        if (!$rows.length) {
            return;
        }

        $rows.html(`
            <tr>
                <td colspan="8" class="text-danger text-center">
                    Failed to load knowledge units.
                </td>
            </tr>
        `);
    }

    get_readiness_label(row) {
        if (row.ready_to_publish) {
            return `<span class="nks-badge nks-badge-good">Ready to Publish</span>`;
        }

        if (row.is_embedded) {
            return `<span class="nks-badge nks-badge-good">Search Ready</span>`;
        }

        if (row.is_chunked) {
            return `<span class="nks-badge nks-badge-info">Prepared</span>`;
        }

        if (row.ready_for_chunking) {
            return `<span class="nks-badge nks-badge-info">Ready for AI Preparation</span>`;
        }

        if (row.missing_fields && row.missing_fields.length) {
            return `<span class="nks-badge nks-badge-warn">Missing Fields</span>`;
        }

        return `<span class="nks-badge">Pending</span>`;
    }

    check_readiness(name) {
        frappe.call({
            method: this.api.get_readiness,
            args: { name },
            freeze: true,
            freeze_message: 'Checking readiness...',
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    frappe.msgprint(r.message && r.message.message ? r.message.message : 'Readiness check failed.');
                    return;
                }

                const d = r.message;

                frappe.msgprint({
                    title: 'Knowledge Unit Readiness',
                    indicator: d.ready_to_publish ? 'green' : d.ready_for_chunking ? 'blue' : 'orange',
                    message: `
                        <div class="nks-readiness-dialog">
                            <p><b>Knowledge Unit:</b> ${frappe.utils.escape_html(d.name)}</p>
                            <p><b>Status:</b> ${frappe.utils.escape_html(d.status || d.approval_status || 'Draft')}</p>
                            <p><b>Prepared Sections:</b> ${d.chunk_count || 0}</p>
                            <p><b>Search Ready Sections:</b> ${d.embedded_chunk_count || 0}</p>
                            <p><b>Approved:</b> ${d.is_approved ? 'Yes' : 'No'}</p>
                            <p><b>Prepared:</b> ${d.is_chunked ? 'Yes' : 'No'}</p>
                            <p><b>Search Ready:</b> ${d.is_embedded ? 'Yes' : 'No'}</p>
                            <p><b>Ready for AI Preparation:</b> ${d.ready_for_chunking ? 'Yes' : 'No'}</p>
                            <p><b>Ready to Publish:</b> ${d.ready_to_publish ? 'Yes' : 'No'}</p>
                            <p><b>Needs Review:</b> ${d.needs_review ? 'Yes' : 'No'}</p>
                            <p><b>Missing Fields:</b> ${(d.missing_fields || []).map(frappe.utils.escape_html).join(', ') || 'None'}</p>
                        </div>
                    `
                });
            }
        });
    }

    approve_unit(name) {
        frappe.confirm(
            'Approve this Knowledge Unit for AI preparation?',
            () => {
                frappe.call({
                    method: this.api.approve_unit,
                    args: { name },
                    freeze: true,
                    freeze_message: 'Approving knowledge unit...',
                    callback: (r) => {
                        if (!r.message || !r.message.success) {
                            this.show_api_error(r, 'Approval failed.');
                            return;
                        }

                        frappe.show_alert({
                            message: r.message.message || 'Knowledge Unit approved.',
                            indicator: 'green'
                        });

                        this.load();
                    }
                });
            }
        );
    }

    mark_needs_review(name) {
        const dialog = new frappe.ui.Dialog({
            title: 'Mark Knowledge Unit Needs Review',
            fields: [
                {
                    fieldname: 'reason',
                    fieldtype: 'Small Text',
                    label: 'Review Reason',
                    reqd: 0
                }
            ],
            primary_action_label: 'Mark Needs Review',
            primary_action: (values) => {
                dialog.hide();

                frappe.call({
                    method: this.api.mark_review,
                    args: {
                        name,
                        reason: values.reason || ''
                    },
                    freeze: true,
                    freeze_message: 'Updating review status...',
                    callback: (r) => {
                        if (!r.message || !r.message.success) {
                            this.show_api_error(r, 'Update failed.');
                            return;
                        }

                        frappe.show_alert({
                            message: r.message.message || 'Knowledge Unit marked for review.',
                            indicator: 'orange'
                        });

                        this.load();
                    }
                });
            }
        });

        dialog.show();
    }

    clear_review(name) {
        frappe.confirm(
            'Clear review status for this Knowledge Unit?',
            () => {
                frappe.call({
                    method: this.api.clear_review,
                    args: { name },
                    freeze: true,
                    freeze_message: 'Clearing review status...',
                    callback: (r) => {
                        if (!r.message || !r.message.success) {
                            this.show_api_error(r, 'Unable to clear review status.');
                            return;
                        }

                        frappe.show_alert({
                            message: r.message.message || 'Review status cleared.',
                            indicator: 'green'
                        });

                        this.load();
                    }
                });
            }
        );
    }

    mark_ready_to_publish(name) {
        frappe.confirm(
            'Mark this Knowledge Unit as Ready to Publish?',
            () => {
                frappe.call({
                    method: this.api.mark_ready_to_publish,
                    args: { name },
                    freeze: true,
                    freeze_message: 'Checking publishing readiness...',
                    callback: (r) => {
                        if (!r.message || !r.message.success) {
                            this.show_api_error(r, 'Knowledge Unit is not ready to publish.');
                            return;
                        }

                        frappe.show_alert({
                            message: r.message.message || 'Knowledge Unit marked as Ready to Publish.',
                            indicator: 'green'
                        });

                        this.load();
                    }
                });
            }
        );
    }

    show_ai_preparation_technical_details() {
        frappe.msgprint({
            title: 'AI Preparation Technical Details',
            indicator: 'blue',
            message: `
                <div class="nks-readiness-dialog">
                    <p><b>Chunking:</b> Splits approved Knowledge Units into searchable retrieval sections.</p>
                    <p><b>Embeddings:</b> Converts prepared sections into semantic search vectors.</p>
                    <p><b>Search Readiness:</b> Requires both usable prepared sections and successful embeddings.</p>
                    <p><b>Rebuild Required:</b> Needed when source content or Knowledge Unit content changes after preparation.</p>
                    <p><b>Preparation Issues:</b> May include empty content, missing metadata, failed section generation, or failed embedding generation.</p>
                    <p><b>Technical Note:</b> These internals remain available for administrators and implementation teams, but the main Studio workflow uses business-friendly readiness labels.</p>
                </div>
            `
        });
    }

    show_api_error(r, fallback_message) {
        const message = r && r.message
            ? r.message.message || fallback_message
            : fallback_message;

        const readiness = r && r.message ? r.message.readiness : null;

        if (readiness) {
            frappe.msgprint({
                title: fallback_message,
                indicator: 'orange',
                message: `
                    <div>
                        <p>${frappe.utils.escape_html(message)}</p>
                        <p><b>Missing Fields:</b> ${(readiness.missing_fields || []).map(frappe.utils.escape_html).join(', ') || 'None'}</p>
                        <p><b>Approved:</b> ${readiness.is_approved ? 'Yes' : 'No'}</p>
                        <p><b>Prepared:</b> ${readiness.is_chunked ? 'Yes' : 'No'}</p>
                        <p><b>Search Ready:</b> ${readiness.is_embedded ? 'Yes' : 'No'}</p>
                        <p><b>Ready to Publish:</b> ${readiness.ready_to_publish ? 'Yes' : 'No'}</p>
                    </div>
                `
            });
            return;
        }

        frappe.msgprint({
            title: fallback_message,
            indicator: 'red',
            message: frappe.utils.escape_html(message)
        });
    }
}