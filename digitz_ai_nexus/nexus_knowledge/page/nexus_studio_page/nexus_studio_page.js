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
            get_access_policies: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_access_policy_options',
            get_access_category_map: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_access_category_map',
            get_source_summary: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_knowledge_source_summary',
            get_sources: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_knowledge_sources',
            process_source: 'digitz_ai_nexus.services.ingestion.processor.process_knowledge_source',
            reset_source: 'digitz_ai_nexus.api.nexus_knowledge_studio.reset_knowledge_source',
            validate_source: 'digitz_ai_nexus.api.nexus_knowledge_studio.validate_knowledge_source',
            suggest_source_fields: 'digitz_ai_nexus.api.nexus_knowledge_source_assist.suggest_knowledge_source_fields',
            create_assisted_source: 'digitz_ai_nexus.api.nexus_knowledge_source_assist.create_knowledge_source_from_suggestion',
            publish_source: 'digitz_ai_nexus.api.nexus_knowledge_studio.publish_knowledge_source',
            unpublish_source: 'digitz_ai_nexus.api.nexus_knowledge_studio.unpublish_knowledge_source',
            generate_source_test_cases: 'digitz_ai_nexus.api.nexus_knowledge_studio.generate_source_test_cases',
            review_index_answer: 'digitz_ai_nexus.api.nexus_knowledge_studio.review_knowledge_index_answer',
            bulk_approve_source_answers: 'digitz_ai_nexus.api.nexus_knowledge_studio.bulk_approve_source_answers',
            validate_source_questions_with_llm: 'digitz_ai_nexus.api.nexus_knowledge_studio.validate_source_questions_with_llm',
            run_knowledge_test_case: 'digitz_ai_nexus.api.nexus_knowledge_studio.run_knowledge_test_case',
            run_source_test_cases: 'digitz_ai_nexus.api.nexus_knowledge_studio.run_source_test_cases',
            get_chat_reachability: 'digitz_ai_nexus.nexus_knowledge.doctype.nexus_knowledge_source.nexus_knowledge_source.get_source_chat_reachability',
            get_tenants_chat_reachability: 'digitz_ai_nexus.api.nexus_knowledge_studio.get_tenants_chat_reachability',
        };

        this.active_tab = 'sources';

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
            access_policy: '',
            disabled: '',
            tenant: '',
            business_unit: '',
            context: '',
            sub_context: '',
            entity_type: '',
            entity: '',
            topic: ''
        };

        this.summary = {};
        this.units = [];
        this.source_summary = {};
        this.sources = [];
        this.source_access_policies = [];
        this.source_classification_options = {};
        this.active_tenant = '';
        this.active_context = {};
        this.tenants = [];
        this.access_category_map = {};       // policy_name → minimum category label
        this.access_categories_list = [];    // [{name, category_name, priority, policies:[]}]

        this.make();
        this.load_access_category_map();
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

            .nks-hero-badge {
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

            .nks-tenant-selector-wrap {
                display: flex;
                align-items: center;
                gap: 8px;
                background: #ffffff;
                border: 1.5px solid rgba(33, 119, 255, 0.24);
                border-radius: 999px;
                padding: 6px 14px;
                box-shadow: 0 8px 20px rgba(33, 77, 187, 0.08);
            }

            .nks-tenant-selector-label {
                font-size: 11px;
                font-weight: 700;
                color: #6b7a99;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                white-space: nowrap;
            }

            .nks-tenant-selector {
                border: none;
                outline: none;
                background: transparent;
                font-size: 13px;
                font-weight: 900;
                color: #0b3c91;
                cursor: pointer;
                max-width: 200px;
                padding: 0;
            }

            .nks-tenant-selector:focus {
                outline: none;
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

            .nks-page-title-block {
                display: flex;
                align-items: flex-start;
                padding: 20px 0 16px;
                border-bottom: 2px solid #eef2f7;
                margin-bottom: 20px;
            }

            .nks-page-title-text {
                margin: 0;
                font-size: 22px;
                font-weight: 800;
                color: #0b3c91;
                letter-spacing: -0.3px;
                display: inline-flex;
                align-items: center;
                gap: 10px;
            }

            .nks-page-title-text::after {
                content: "";
                display: inline-block;
                width: 34px;
                height: 4px;
                border-radius: 999px;
                background: #e0a62f;
            }

            .nks-page-title-sub {
                margin: 6px 0 0;
                color: #526887;
                font-size: 13px;
                line-height: 1.5;
                font-weight: 500;
                max-width: 680px;
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
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 14px;
            }

            .nks-summary-card {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 8px 14px;
                border-radius: 12px;
                background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border: 1.5px solid rgba(33, 119, 255, 0.24);
                box-shadow: 0 2px 8px rgba(33, 77, 187, 0.05);
                flex: 0 0 auto;
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
                font-size: 11px;
                line-height: 1.2;
                font-weight: 700;
                white-space: nowrap;
            }

            .nks-summary-value {
                color: #071d4f;
                font-size: 18px;
                line-height: 1;
                font-weight: 900;
                white-space: nowrap;
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

            .nks-badge-neutral {
                background: #f1f5f9;
                color: #475569;
                border-color: rgba(100, 116, 139, 0.2);
            }

            .nks-badge-processed {
                background: #fff4e6;
                color: #b85c00;
                border-color: rgba(200, 100, 0, 0.24);
            }

            .nks-badge-validated {
                background: #eef3ff;
                color: #2a54c9;
                border-color: rgba(42, 84, 201, 0.24);
            }

            .nks-badge-published {
                background: #ecfffb;
                color: #007a64;
                border-color: rgba(0, 164, 130, 0.26);
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


            .nks-source-dashboard-panel {
                padding: 14px;
                border-radius: 16px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(77, 163, 255, 0.10), transparent 30%),
                    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border: 1.5px solid rgba(33, 119, 255, 0.20);
                box-shadow: 0 10px 22px rgba(33, 77, 187, 0.05);
                margin-bottom: 12px;
            }

            .nks-source-dashboard-testing {
                border-color: rgba(33, 119, 255, 0.22);
                background:
                    radial-gradient(circle at 100% 0%, rgba(77, 163, 255, 0.10), transparent 30%),
                    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            }

            .nks-source-dashboard-summary,
            .nks-source-dashboard-index {
                border-color: rgba(0, 184, 148, 0.22);
                background:
                    radial-gradient(circle at 0% 0%, rgba(0, 184, 148, 0.09), transparent 28%),
                    linear-gradient(180deg, #ffffff 0%, #f4fffc 100%);
            }

            .nks-source-dashboard-panel h4 {
                margin: 0 0 10px;
                color: #0b3c91;
                font-size: 16px;
                font-weight: 950;
            }

            .nks-source-test-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 10px;
                margin: 12px 0;
            }

            .nks-source-test-stat {
                padding: 12px;
                border-radius: 14px;
                background: #ffffff;
                border: 1px solid rgba(33, 119, 255, 0.18);
                box-shadow: 0 8px 18px rgba(33, 77, 187, 0.04);
            }

            .nks-source-test-value {
                font-size: 24px;
                font-weight: 950;
                color: #0b3c91;
                line-height: 1;
            }

            .nks-source-test-label {
                margin-top: 6px;
                color: #526887;
                font-size: 12px;
                font-weight: 850;
            }

            .nks-source-summary-title {
                margin-top: 8px;
                color: #102b67;
                font-size: 14px;
                font-weight: 950;
            }

            .nks-source-summary-text {
                margin: 8px 0 0;
                color: #314d78;
                font-size: 13px;
                line-height: 1.55;
                font-weight: 720;
            }

            .nks-source-summary-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 12px;
            }

            .nks-source-summary-meta span {
                padding: 6px 9px;
                border-radius: 999px;
                background: #ffffff;
                border: 1px solid rgba(0, 184, 148, 0.18);
                color: #008c78;
                font-size: 11px;
                font-weight: 850;
            }

            .nks-source-dashboard-note {
                padding: 12px;
                border-radius: 14px;
                font-size: 12px;
                line-height: 1.45;
                font-weight: 750;
                margin-top: 10px;
            }

            .nks-source-dashboard-note-info {
                background: #eef6ff;
                border: 1px solid rgba(33, 119, 255, 0.20);
                color: #0b3c91;
            }

            .nks-source-dashboard-note-muted {
                background: #f8fafc;
                border: 1px solid rgba(148, 163, 184, 0.24);
                color: #526887;
            }

            .nks-source-tenant-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(220px, 1fr));
                gap: 12px;
                margin: 0 20px 16px;
            }

            .nks-source-tenant-card {
                padding: 14px;
                border-radius: 18px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(0, 184, 148, 0.08), transparent 30%),
                    linear-gradient(180deg, #ffffff 0%, #f4fffc 100%);
                border: 1.5px solid rgba(0, 184, 148, 0.22);
                box-shadow: 0 10px 24px rgba(33, 77, 187, 0.05);
            }

            .nks-source-tenant-title {
                color: #0b3c91;
                font-size: 14px;
                font-weight: 950;
            }

            .nks-source-tenant-stats {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 8px;
                margin-top: 12px;
            }

            .nks-source-tenant-stats div {
                padding: 9px;
                border-radius: 12px;
                background: #ffffff;
                border: 1px solid rgba(33, 119, 255, 0.14);
            }

            .nks-source-tenant-stats strong {
                display: block;
                color: #102b67;
                font-size: 18px;
                line-height: 1;
                font-weight: 950;
            }

            .nks-source-tenant-stats span {
                display: block;
                margin-top: 5px;
                color: #526887;
                font-size: 11px;
                font-weight: 850;
            }

            .nks-source-classification-panel {
                margin: 0 20px 14px;
                padding: 6px 14px 6px;
                border-radius: 18px;
                background: #f8fbff;
                border: 1.5px solid rgba(33, 119, 255, 0.18);
            }

            .nks-source-classification-panel[open] {
                padding-bottom: 14px;
            }

            .nks-source-classification-panel-header {
                display: flex;
                align-items: center;
                gap: 6px;
                cursor: pointer;
                font-size: 12px;
                font-weight: 600;
                color: #2177ff;
                letter-spacing: 0.04em;
                text-transform: uppercase;
                padding: 6px 2px;
                list-style: none;
                user-select: none;
            }

            .nks-source-classification-panel-header::-webkit-details-marker,
            .nks-source-classification-panel-header::marker {
                display: none;
            }

            .nks-source-classification-panel-header::before {
                content: '▸';
                font-size: 10px;
                transition: transform 0.15s ease;
                display: inline-block;
            }

            .nks-source-classification-panel[open] > .nks-source-classification-panel-header::before {
                transform: rotate(90deg);
            }

            .nks-source-classification-panel > .nks-source-classification-grid {
                margin-top: 10px;
            }

            .nks-source-classification-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(160px, 1fr));
                gap: 10px;
            }

            .nks-source-classification-grid .form-control {
                border-radius: 14px;
                border-color: rgba(33, 119, 255, 0.22);
            }

            .nks-source-group-wrap {
                padding: 0 20px 20px;
            }

            .nks-source-tenant-section {
                margin-bottom: 14px;
                border-radius: 18px;
                overflow: hidden;
                border: 1.5px solid rgba(33, 119, 255, 0.18);
                background: #ffffff;
                box-shadow: 0 10px 24px rgba(33, 77, 187, 0.05);
            }

            .nks-source-tenant-section[open] {
                border-color: rgba(0, 184, 148, 0.24);
            }

            .nks-source-tenant-head {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                align-items: center;
                padding: 14px 16px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(77, 163, 255, 0.10), transparent 30%),
                    linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border-bottom: 1px solid rgba(33, 119, 255, 0.14);
            }

            .nks-source-tenant-head h4 {
                margin: 0;
                color: #102b67;
                font-size: 15px;
                font-weight: 950;
            }

            .nks-source-tenant-head::-webkit-details-marker,
            .nks-source-context-head::-webkit-details-marker,
            .nks-source-item-head::-webkit-details-marker {
                display: none;
            }

            .nks-source-tenant-head,
            .nks-source-context-head,
            .nks-source-item-head {
                cursor: pointer;
                list-style: none;
            }

            .nks-source-tenant-head::after,
            .nks-source-context-head::after,
            .nks-source-item-head::after {
                content: '+';
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 24px;
                height: 24px;
                flex: 0 0 auto;
                border-radius: 999px;
                color: #0b3c91;
                background: rgba(33, 119, 255, 0.08);
                font-size: 16px;
                font-weight: 950;
            }

            .nks-source-tenant-section[open] > .nks-source-tenant-head::after,
            .nks-source-context-group[open] > .nks-source-context-head::after,
            .nks-source-item[open] > .nks-source-item-head::after {
                content: '-';
                color: #008c74;
                background: rgba(0, 184, 148, 0.10);
            }

            .nks-source-tenant-body {
                padding: 14px 16px 16px;
                background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            }

            .nks-source-context-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(260px, 1fr));
                gap: 12px;
            }

            .nks-source-context-group {
                border-radius: 16px;
                overflow: hidden;
                background: #ffffff;
                border: 1.5px solid rgba(33, 119, 255, 0.14);
            }

            .nks-source-context-group[open] {
                border-color: rgba(0, 184, 148, 0.22);
                box-shadow: 0 12px 26px rgba(33, 77, 187, 0.06);
            }

            .nks-source-context-head {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                align-items: center;
                padding: 14px;
                background:
                    radial-gradient(circle at 100% 0%, rgba(0, 184, 148, 0.08), transparent 34%),
                    linear-gradient(180deg, #ffffff 0%, #f6fffc 100%);
            }

            .nks-source-context-main {
                min-width: 0;
            }

            .nks-source-context-title {
                color: #102b67;
                font-size: 14px;
                font-weight: 950;
            }

            .nks-source-context-meta {
                margin-top: 5px;
                color: #526887;
                font-size: 12px;
                font-weight: 750;
            }

            .nks-source-context-stats {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                justify-content: flex-end;
                margin-left: auto;
                align-items: center;
            }

            .nks-access-details-btn {
                font-size: 11px;
                font-weight: 700;
                padding: 3px 10px;
                border-radius: 20px;
                border: 1.5px solid rgba(33, 119, 255, 0.35);
                background: #fff;
                color: #2177ff;
                white-space: nowrap;
                cursor: pointer;
                transition: background 0.15s, color 0.15s;
            }

            .nks-access-details-btn:hover {
                background: #2177ff;
                color: #fff;
                border-color: #2177ff;
            }

            /* Two-row Access Categories + Policies grouped container */
            .nks-access-stats-container {
                display: inline-flex;
                flex-direction: column;
                gap: 3px;
                background: #f8faff;
                border: 1px solid rgba(33, 119, 255, 0.18);
                border-radius: 10px;
                padding: 5px 10px;
                min-width: 0;
            }

            .nks-access-row {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                flex-wrap: wrap;
            }

            .nks-access-row + .nks-access-row {
                border-top: 1px solid rgba(33, 119, 255, 0.1);
                padding-top: 3px;
                margin-top: 1px;
            }

            .nks-access-row-warn + .nks-access-row,
            .nks-access-row + .nks-access-row-warn {
                border-top-color: rgba(224, 166, 47, 0.25);
            }

            .nks-access-row-label {
                font-size: 10px;
                font-weight: 700;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                white-space: nowrap;
                min-width: 72px;
                flex-shrink: 0;
            }

            .nks-access-row-warn .nks-access-row-label {
                color: #a66d00;
            }

            /* Legacy standalone group pill (kept for backward compat) */
            .nks-policy-stats-group {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                background: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 20px;
                padding: 2px 8px 2px 6px;
            }

            .nks-policy-stats-group-warn {
                background: #fff7e8;
                border-color: rgba(224, 166, 47, 0.35);
            }

            .nks-policy-stats-group-warn .nks-policy-stats-label {
                color: #a66d00;
            }

            .nks-policy-stats-label {
                font-size: 10px;
                font-weight: 600;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                white-space: nowrap;
                margin-right: 2px;
            }

            .nks-source-context-body {
                padding: 10px 12px 12px;
                background: #f8fbff;
            }

            .nks-source-item {
                margin-top: 8px;
                border-radius: 14px;
                background: #ffffff;
                border: 1px solid rgba(33, 119, 255, 0.14);
                overflow: hidden;
            }

            .nks-source-item[open] {
                border-color: rgba(0, 184, 148, 0.20);
                box-shadow: 0 10px 22px rgba(33, 77, 187, 0.05);
            }

            .nks-source-item-head {
                display: grid;
                grid-template-columns: 1fr auto;
                grid-template-rows: auto auto;
                column-gap: 10px;
                row-gap: 6px;
                padding: 12px;
            }

            .nks-source-item-head::after {
                grid-column: 2;
                grid-row: 1;
                align-self: start;
            }

            .nks-source-item-head-title {
                grid-column: 1;
                grid-row: 1;
                min-width: 0;
                overflow: hidden;
            }

            .nks-source-item-head-footer {
                grid-column: 1 / -1;
                grid-row: 2;
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                gap: 6px;
            }

            .nks-source-title-text {
                font-weight: 900;
                color: #0b60d8;
                font-size: 13px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .nks-source-title-sub {
                display: flex;
                align-items: center;
                flex-wrap: nowrap;
                gap: 4px;
                margin-top: 2px;
                color: #7a8daa;
                font-size: 11px;
                font-weight: 700;
                white-space: nowrap;
                overflow: hidden;
            }

            .nks-source-title-sub span {
                white-space: nowrap;
                flex-shrink: 0;
            }

            .nks-source-head-sep {
                color: #bcc8da;
                flex-shrink: 0;
            }

            .nks-source-title-path {
                margin-top: 3px;
                color: #526887;
                font-size: 11px;
                font-weight: 600;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .nks-source-title-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                margin-top: 4px;
            }

            .nks-badge-compact {
                font-size: 10px;
                padding: 1px 7px;
                flex-shrink: 0;
            }

            .nks-classification-info-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 18px;
                height: 18px;
                border-radius: 50%;
                border: 1.5px solid #93c5fd;
                background: #eff6ff;
                color: #2563eb;
                font-size: 10px;
                font-weight: 700;
                cursor: pointer;
                flex-shrink: 0;
                line-height: 1;
                padding: 0;
                vertical-align: middle;
                transition: background 0.15s;
            }
            .nks-classification-info-btn:hover {
                background: #dbeafe;
            }

            .nks-classification-popup {
                position: absolute;
                z-index: 9999;
                background: #ffffff;
                border: 1px solid #bfdbfe;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(37, 99, 235, 0.13);
                padding: 14px 16px;
                min-width: 280px;
                max-width: 360px;
                font-size: 12px;
                line-height: 1.5;
            }
            .nks-classification-popup-row {
                display: flex;
                gap: 8px;
                padding: 3px 0;
                border-bottom: 1px solid #f1f5f9;
            }
            .nks-classification-popup-row:last-child {
                border-bottom: none;
            }
            .nks-classification-popup-label {
                color: #64748b;
                font-weight: 500;
                min-width: 100px;
                flex-shrink: 0;
            }
            .nks-classification-popup-value {
                color: #1e293b;
                font-weight: 400;
                word-break: break-word;
            }


            .nks-source-item-body {
                display: grid;
                grid-template-columns: repeat(3, minmax(160px, 1fr));
                gap: 10px;
                padding: 0 12px 12px;
                background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            }

            .nks-source-detail-box {
                padding: 10px;
                border-radius: 12px;
                background: #ffffff;
                border: 1px solid rgba(33, 119, 255, 0.12);
            }

            .nks-source-detail-label {
                margin-bottom: 6px;
                color: #526887;
                font-size: 11px;
                font-weight: 950;
                text-transform: uppercase;
            }

            .nks-source-detail-value {
                color: #102b67;
                font-size: 12px;
                line-height: 1.45;
                font-weight: 750;
            }

            .nks-source-detail-box-wide {
                grid-column: 1 / -1;
            }

            .nks-source-index-review-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(220px, 1fr));
                gap: 10px;
            }

            .nks-source-index-review-list {
                margin: 8px 0 0;
                padding-left: 17px;
                color: #102b67;
                font-size: 12px;
                line-height: 1.45;
            }

            .nks-source-index-review-list li {
                margin-bottom: 7px;
            }

            .nks-source-index-answer {
                margin-top: 6px;
                padding: 8px;
                border-radius: 10px;
                background: #f8fbff;
                border: 1px solid rgba(33, 119, 255, 0.12);
                color: #314d78;
                font-size: 12px;
                line-height: 1.45;
            }

            .nks-source-index-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                margin-top: 7px;
            }

            .nks-source-compact-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
                margin-top: 7px;
            }

            .nks-source-compact-tags .nks-badge {
                font-size: 10px;
                padding: 4px 7px;
            }

            .nks-source-item-actions {
                display: flex;
                align-items: center;
                justify-content: flex-end;
                gap: 6px;
                flex-wrap: wrap;
            }

            .nks-source-inline-actions {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                flex-wrap: wrap;
            }

            .nks-source-dashboard-test-actions {
                margin-top: 12px;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }

            @media (max-width: 1100px) {
                .nks-stage-grid,
                .nks-dashboard-grid,
                .nks-source-tenant-grid,
                .nks-source-classification-grid,
                .nks-source-context-grid {
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

                .nks-source-item-body,
                .nks-source-index-review-grid {
                    grid-template-columns: 1fr 1fr;
                }

                .nks-source-item-head {
                    column-gap: 6px;
                }

                .nks-source-dashboard-panel-head {
                    display: flex;
                    align-items: flex-start;
                    justify-content: space-between;
                    gap: 12px;
                    margin-bottom: 10px;
                }

                .nks-source-dashboard-panel-head h4 {
                    margin: 0;
                    color: #0b3c91;
                    font-size: 16px;
                    font-weight: 950;
                }

                .nks-source-dashboard-panel-head p {
                    margin: 4px 0 0;
                    color: #526887;
                    font-size: 12px;
                    line-height: 1.42;
                    font-weight: 750;
                }

                .nks-source-test-status-pill {
                    white-space: nowrap;
                    padding: 6px 10px;
                    border-radius: 999px;
                    font-size: 12px;
                    font-weight: 850;
                    border: 1px solid rgba(33, 119, 255, 0.20);
                }

                .nks-source-test-status-pill.has-tests {
                    color: #0b3c91;
                    background: #eef6ff;
                }

                .nks-source-test-status-pill.no-tests {
                    color: #64748b;
                    background: #f8fafc;
                }

                .nks-test-run-result {
                    color: #102b67;
                }

                .nks-test-run-result-grid {
                    display: grid;
                    grid-template-columns: repeat(5, minmax(0, 1fr));
                    gap: 8px;
                    margin-top: 12px;
                }

                .nks-test-run-result-grid > div {
                    padding: 10px;
                    border-radius: 12px;
                    background: #f8fbff;
                    border: 1px solid rgba(33, 119, 255, 0.16);
                    text-align: center;
                }

                .nks-test-run-result-grid strong {
                    display: block;
                    font-size: 22px;
                    color: #0b3c91;
                    line-height: 1;
                }

                .nks-test-run-result-grid span {
                    display: block;
                    margin-top: 5px;
                    color: #526887;
                    font-size: 11px;
                    font-weight: 850;
                }

                .nks-test-run-result-actions {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                    margin-top: 14px;
                }
                    
                .nks-dashboard-full-row {
                    grid-column: 1 / -1;
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

                .nks-stage-grid,
                .nks-context-grid,
                .nks-dashboard-grid,
                .nks-source-tenant-grid,
                .nks-source-classification-grid,
                .nks-source-context-grid,
                .nks-source-item-body,
                .nks-source-index-review-grid {
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

                .nks-source-dashboard-panel-head {
                    flex-direction: column;
                }

                .nks-test-run-result-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
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
                        <div class="nks-tenant-selector-wrap" id="nks-active-tenant-pill">
                            <span class="nks-tenant-selector-label">Tenant</span>
                            <select class="nks-tenant-selector">
                                <option value="">Resolving...</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div id="nks-active-context-panel"></div>

                <div id="nks-tab-content"></div>
            </div>
        `);

        this.bind_events();
        this.load();
        this.render_active_tab();
    }

    get_tabs_html() {
        const tabs = [
            ['sources', 'Source Library'],
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

        this.body.on('change', '.nks-source-access-policy-filter', (e) => {
            this.source_filters.access_policy = e.target.value || '';
            this.load_sources();
        });

        this.body.on('change', '.nks-source-disabled-filter', (e) => {
            this.source_filters.disabled = e.target.value;
            this.load_sources();
        });

        this.body.on('change', '.nks-source-classification-filter', (e) => {
            const fieldname = $(e.currentTarget).data('fieldname');

            if (!fieldname) {
                return;
            }

            this.source_filters[fieldname] = e.target.value || '';
            this.load_sources();
        });

        this.body.on('click', '.nks-source-clear-classification-btn', () => {
            [
                'tenant',
                'business_unit',
                'context',
                'sub_context',
                'entity_type',
                'entity',
                'topic'
            ].forEach((fieldname) => {
                this.source_filters[fieldname] = '';
            });

            this.load_sources();
            this.load_source_summary();
        });

        this.body.on('click', '.nks-access-details-btn', (e) => {
            e.stopPropagation();
            const btn      = e.currentTarget;
            const tenant   = $(btn).data('tenant') || '';
            const context  = $(btn).data('context') || '';
            const sources  = (this.sources || []).filter(s => {
                if (tenant  && s.tenant  !== tenant)  return false;
                if (context && s.context !== context) return false;
                return true;
            });
            const title = context
                ? `Access Details — ${context}`
                : `Access Details — ${tenant}`;
            this.show_access_details_dialog(sources, title);
        });

        this.body.on('click', '.nks-new-source-btn', () => {
            this.new_knowledge_source();
        });

        this.body.on('click', '.nks-ai-assist-source-btn', () => {
            this.show_ai_assist_source_dialog();
        });

        this.body.on('click', '.nks-source-dashboard-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.show_source_dashboard($(e.currentTarget).data('name'));
        });

        this.body.on('change', '.nks-tenant-selector', (e) => {
            const tenant = e.target.value;
            if (!tenant) return;
            this.active_tenant = tenant;
            this.active_context = Object.assign({}, this.active_context, { tenant });
            frappe.call({
                method: 'digitz_ai_nexus.api.nexus_administration.set_active_user_context',
                args: { tenant },
                callback: () => {
                    this.load();
                }
            });
        });

        this.body.on('click', '.nks-tenant-reachability-detail-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.show_tenant_reachability_dialog($(e.currentTarget).data('tenant'));
        });

        this.body.on('click', '.nks-inline-review-answers-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const name = $(e.currentTarget).data('name');
            const $details = this.body.find(`.nks-source-item[data-source="${name}"]`);
            if ($details.length) {
                $details.attr('open', true);
                $details[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });

        this.body.on('click', '.nks-inline-approve-all-answers-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.bulk_approve_source_answers($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-inline-validate-questions-llm-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.validate_source_questions_with_llm($(e.currentTarget).data('name'));
        });

        // Use a capturing listener so we intercept the click before the native
        // <details>/<summary> toggle fires and before other delegated handlers.
        this.body[0].addEventListener('click', (e) => {
            const btn = e.target.closest('.nks-classification-info-btn');
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            this.show_classification_popup(btn);
        }, true /* capture phase */);

        // Close classification popup when clicking elsewhere
        $(document).on('click.nks-classification', (e) => {
            if (!$(e.target).closest('.nks-classification-popup, .nks-classification-info-btn').length) {
                $('.nks-classification-popup').remove();
            }
        });

        this.body.on('click', '.nks-inline-process-source-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.process_source_from_dashboard($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-inline-validate-source-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.validate_source_from_dashboard($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-inline-publish-source-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.publish_source_from_dashboard($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-inline-unpublish-source-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.unpublish_source_from_dashboard($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-inline-generate-tests-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.generate_test_cases_from_source_dashboard($(e.currentTarget).data('name'));
        });

        this.body.on('click', '.nks-source-context-head', (e) => {
            // Context groups are independent — opening one never closes another.
            // Each context group manages its own open/closed state via native <details>.
        });

        this.body.on('click', '.nks-source-item-head', (e) => {
            // Don't collapse siblings when clicking the classification info button
            if ($(e.target).closest('.nks-classification-info-btn').length) return;

            const $item = $(e.currentTarget).closest('.nks-source-item');

            // Only collapse sibling sources within the same context group
            if (!$item.prop('open')) {
                $item
                    .siblings('.nks-source-item')
                    .removeAttr('open');
            }
        });

        this.body.on('click', '.nks-index-answer-review-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.review_index_answer(
                $(e.currentTarget).data('name'),
                $(e.currentTarget).data('action'),
                $(e.currentTarget)
            );
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
        this.load_access_policy_options();
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

                if (r.message.tenants && r.message.tenants.length) {
                    this.tenants = r.message.tenants;
                }

                this.render_tenant_selector();
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


    load_source_summary(options = {}) {
        const shouldRender = options.render !== false;

        frappe.call({
            method: this.api.get_source_summary,
            freeze: false,
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    this.source_summary = {};
                    if (shouldRender) {
                        this.refresh_current_tab_if_needed();

                        if (this.active_tab === 'sources') {
                            this.render_active_tab();
                        }
                    }

                    return;
                }

                this.source_summary = r.message.summary || {};
                this.source_classification_options = this.source_summary.classification_options || {};

                this.merge_active_context(
                    r.message.active_context || {},
                    this.source_summary || {}
                );

                if (r.message.active_tenant && !this.active_tenant) {
                    this.active_tenant = r.message.active_tenant;
                }

                this.render_active_tenant();
                this.render_active_context_panel();

                if (shouldRender && this.active_tab === 'sources') {
                    this.render_active_tab();
                }

                this.load_tenants_chat_reachability();
            }
        });
    }

    load_tenants_chat_reachability() {
        frappe.call({
            method: this.api.get_tenants_chat_reachability,
            freeze: false,
            callback: (r) => {
                this.tenant_reachability = (r.message && r.message.success)
                    ? (r.message.tenants || {})
                    : null;

                const $grid = this.body.find('.nks-source-tenant-grid');
                if ($grid.length) {
                    $grid.replaceWith(this.get_source_tenant_stats_html());
                }
            },
            error: () => {
                this.tenant_reachability = null;
                const $grid = this.body.find('.nks-source-tenant-grid');
                if ($grid.length) {
                    $grid.replaceWith(this.get_source_tenant_stats_html());
                }
            }
        });
    }

    get_tenant_reachability_inline_html(tenant, data) {
        if (!data) {
            return `<span style="color:#999;">Reachability unavailable</span>`;
        }

        const reasonLabels = {
            no_access_policy_field: 'No access policy field on chunks',
            no_access_policies: 'No access policy on active chunks',
            no_access_categories: 'No access category covers this knowledge',
            no_agent_profiles: 'No agent profile has an enabled access category',
            no_assignments: 'Profile(s) found but none assigned',
            ok: '',
        };

        if (!data.reachable) {
            const reason = reasonLabels[data.reason] || 'Chain incomplete';
            return `
                <span style="color:#e74c3c; font-weight:500;">&#10007; Not Reachable</span>
                <span style="color:#999; margin-left:4px;">— ${frappe.utils.escape_html(reason)}</span>
                ${data.profiles && data.profiles.length ? `
                    <button class="btn btn-xs nks-tenant-reachability-detail-btn"
                        style="margin-left:6px; font-size:11px;"
                        data-tenant="${frappe.utils.escape_html(tenant)}">Details</button>
                ` : ''}
            `;
        }

        return `
            <span style="color:#27ae60; font-weight:500;">&#10003; Reachable</span>
            <span style="color:#666; margin-left:4px;">— ${data.reachable_count} of ${data.total_profile_count} profile(s) active</span>
            <button class="btn btn-xs nks-tenant-reachability-detail-btn"
                style="margin-left:6px; font-size:11px;"
                data-tenant="${frappe.utils.escape_html(tenant)}">Details</button>
        `;
    }

    show_tenant_reachability_dialog(tenant) {
        const tenantKey = tenant;
        frappe.call({
            method: this.api.get_tenants_chat_reachability,
            freeze: true,
            freeze_message: 'Loading reachability...',
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    frappe.msgprint('Could not load reachability data.');
                    return;
                }

                const data = (r.message.tenants || {})[tenantKey];
                if (!data) {
                    frappe.msgprint('No reachability data found for this tenant.');
                    return;
                }

                const profileRows = (data.profiles || []).map(p => {
                    const lines = [];

                    if (p.user_assignments && p.user_assignments.length) {
                        lines.push(`<span style="color:#27ae60;">&#10003; User Assignment</span> — ${p.user_assignments.length} active user(s)`);
                    }

                    if (p.identity_routes && p.identity_routes.length) {
                        const routeList = p.identity_routes.map(r => {
                            const parts = [r.channel, r.chat_category, r.open_to_all ? 'Public' : 'Restricted'].filter(Boolean);
                            return frappe.utils.escape_html(parts.join(' / '));
                        }).join('<br>');
                        lines.push(`<span style="color:#2980b9;">&#10003; Category Identity Route</span><br>${routeList}`);
                    }

                    if (!lines.length) {
                        lines.push(`<span style="color:#e74c3c;">&#10007; No active assignments or routes</span>`);
                    }

                    const statusIcon = p.reachable
                        ? `<span style="color:#27ae60;">&#10003;</span>`
                        : `<span style="color:#e74c3c;">&#10007;</span>`;

                    return `
                        <tr style="border-bottom:1px solid #f0f0f0;">
                            <td style="padding:6px 8px;">${statusIcon}</td>
                            <td style="padding:6px 8px; font-weight:500;">${frappe.utils.escape_html(p.profile_label || p.profile)}</td>
                            <td style="padding:6px 8px; font-size:12px;">${lines.join('<br>')}</td>
                        </tr>`;
                }).join('');

                const statusBadge = data.reachable
                    ? `<span class="nks-badge nks-badge-good">Reachable — ${data.reachable_count} of ${data.total_profile_count} profile(s)</span>`
                    : `<span class="nks-badge nks-badge-warn">Not Reachable</span>`;

                const dialog = new frappe.ui.Dialog({
                    title: `Chat Reachability: ${tenantKey}`,
                    size: 'large',
                    fields: [{ fieldname: 'html', fieldtype: 'HTML' }]
                });

                dialog.fields_dict.html.$wrapper.html(`
                    <div style="padding:8px 0;">
                        <p style="margin-bottom:12px;">${statusBadge}</p>
                        ${profileRows.length ? `
                            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                                <thead>
                                    <tr style="border-bottom:2px solid #eee; color:#888; font-size:12px;">
                                        <th style="padding:4px 8px; width:24px;"></th>
                                        <th style="padding:4px 8px; text-align:left;">AI Agent Profile</th>
                                        <th style="padding:4px 8px; text-align:left;">Assigned Via</th>
                                    </tr>
                                </thead>
                                <tbody>${profileRows}</tbody>
                            </table>
                        ` : `<p class="text-muted">No agent profiles found in the access chain for this tenant's knowledge.</p>`}
                    </div>
                `);

                dialog.show();
            }
        });
    }

    load_access_policy_options() {
        frappe.call({
            method: this.api.get_access_policies,
            freeze: false,
            callback: (r) => {
                if (!r.message || !r.message.success) {
                    this.source_access_policies = [];
                    return;
                }

                this.source_access_policies = r.message.access_policies || [];

                if (this.active_tab === 'sources') {
                    this.render_active_tab();
                }
            }
        });
    }

    load_access_category_map() {
        frappe.call({
            method: this.api.get_access_category_map,
            freeze: false,
            callback: (r) => {
                if (r.message && r.message.policy_to_category) {
                    this.access_category_map    = r.message.policy_to_category;
                    this.access_categories_list = r.message.categories || [];
                }
            },
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

    render_tenant_selector() {
        const $select = this.body.find('.nks-tenant-selector');
        if (!$select.length) return;

        if (!this.tenants || !this.tenants.length) {
            if (this.active_tenant) {
                $select.empty().append(
                    `<option value="${frappe.utils.escape_html(this.active_tenant)}">${frappe.utils.escape_html(this.active_tenant)}</option>`
                );
            }
            return;
        }

        const currentVal = $select.val();
        const targetVal = this.active_tenant || currentVal;

        $select.empty();
        this.tenants.forEach(t => {
            const label = t.tenant_name || t.tenant_code || t.name;
            const selected = t.name === targetVal ? ' selected' : '';
            $select.append(`<option value="${frappe.utils.escape_html(t.name)}"${selected}>${frappe.utils.escape_html(label)}</option>`);
        });
    }

    render_active_tenant() {
        this.render_tenant_selector();
    }

    refresh_current_tab_if_needed() {
        this.render_active_tab();
    }

    render_active_tab() {
        const $content = this.body.find('#nks-tab-content');
        this.active_tab = 'sources';
        $content.html(this.get_sources_html());
        this.render_sources_table();
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
                        Nexus Studio centers around the Source Library. Source processing creates prepared
                        knowledge, chunks, embeddings, validation readiness, and answer availability.
                    </p>
                </div>

                <div class="nks-stage-grid">
                    ${this.get_stage_card_html('📚', 'Source Library', 'Add, review, process, validate, publish, and unpublish source material.')}
                    ${this.get_stage_card_html('🧪', 'Answer Quality', 'Validate whether Nexus gives correct, grounded, and trustworthy answers.', true)}
                    ${this.get_stage_card_html('📊', 'Improvement Areas', 'Identify missing, weak, stale, or poorly retrievable knowledge.')}
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
        const source = this.source_summary || {};
        const unit = this.summary || {};

        return `
            ${this.get_summary_card_html('Total Sources', source.total_sources || 0)}
            ${this.get_summary_card_html('Processed Sources', source.ingested || source.processed || 0, 'good')}
            ${this.get_summary_card_html('Published Sources', source.published || 0, 'good')}
            ${this.get_summary_card_html('Context Summaries', source.context_summaries || 0, 'good')}
            ${this.get_summary_card_html('Semantic Index', source.semantic_index_entries || 0)}
            ${this.get_summary_card_html('Needs Attention', (source.sync_failed || 0) + (source.disabled || 0), 'warn')}
            ${this.get_summary_card_html('Prepared Units', unit.chunked_units || 0)}
            ${this.get_summary_card_html('Search Ready Units', unit.embedded_units || 0, 'good')}
            ${this.get_summary_card_html('Unit Review Queue', unit.needs_review_units || 0, 'warn')}
        `;
    }

   

    get_answer_quality_html() {
        return this.get_placeholder_section(
            'Answer Quality',
            'Validate whether Nexus gives correct, grounded, and trustworthy answers from published knowledge.',
            [
                'Connect this view with validation tests, validation runs, and Nexus Query Log.',
                'Review expected source matching, citations, confidence, access handling, and fallback behavior.',
                'Use this area for answer-level quality checks, not source processing.'
            ]
        );
    }

    get_improvement_areas_html() {
        return this.get_placeholder_section(
            'Improvement Areas',
            'Identify missing, weak, stale, or poorly retrievable knowledge from failed answers and user questions.',
            [
                'Track no-answer questions, fallback answers, low-confidence responses, and failed expected-source checks.',
                'Suggest new sources or updates to existing sources based on repeated knowledge gaps.',
                'Convert confirmed gaps into source improvement tasks or new source drafts.'
            ]
        );
    }

    get_summary_card_html(label, value, type = '') {
        const type_class = type === 'good'
            ? 'nks-summary-card-good'
            : type === 'warn'
                ? 'nks-summary-card-warn'
                : '';

        return `
            <div class="nks-summary-card ${type_class}">
                <div class="nks-summary-value">${frappe.utils.escape_html(String(value || 0))}</div>
                <div class="nks-summary-label">${frappe.utils.escape_html(label)}</div>
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
                ${this.get_summary_card_html('Context Summaries', s.context_summaries || 0, 'good')}
                ${this.get_summary_card_html('Semantic Index', s.semantic_index_entries || 0)}
                ${this.get_summary_card_html('Sync Failed', s.sync_failed || 0, 'warn')}
                ${this.get_summary_card_html('Stale', s.stale || 0, 'warn')}
                ${this.get_summary_card_html('Disabled', s.disabled || 0)}
            </div>

            <div class="nks-section-panel">
                <div class="nks-page-title-block">
                    <div class="nks-page-title-main">
                        <h2 class="nks-page-title-text">Knowledge Sources</h2>
                        <p class="nks-page-title-sub">
                            Register, govern, and review source material by tenant and business classification before it becomes usable by Nexus answers.
                        </p>
                    </div>
                </div>

                ${this.get_source_tenant_stats_html()}

                <div class="nks-toolbar">
                    <div class="nks-toolbar-left">
                        <input class="form-control nks-source-search" placeholder="Search knowledge sources..." value="${frappe.utils.escape_html(this.source_filters.search || '')}" />

                        <select class="form-control nks-source-status-filter">
                            ${this.get_source_status_options_html()}
                        </select>

                        <select class="form-control nks-source-sync-filter">
                            ${this.get_source_sync_options_html()}
                        </select>

                        <select class="form-control nks-source-access-policy-filter">
                            ${this.get_source_access_policy_options_html()}
                        </select>

                        <select class="form-control nks-source-disabled-filter">
                            <option value="" ${this.source_filters.disabled === '' ? 'selected' : ''}>Enabled/Disabled: All</option>
                            <option value="0" ${this.source_filters.disabled === '0' ? 'selected' : ''}>Enabled Only</option>
                            <option value="1" ${this.source_filters.disabled === '1' ? 'selected' : ''}>Disabled Only</option>
                        </select>
                    </div>

                    <div class="nks-toolbar-right">
                        <button class="btn btn-primary btn-sm nks-new-source-btn">
                            New Source
                        </button>

                        <button class="btn btn-default btn-sm nks-ai-assist-source-btn">
                            AI Assist Source
                        </button>

                        <button class="btn btn-default btn-sm nks-refresh-btn">
                            Refresh
                        </button>
                    </div>
                </div>

                <details class="nks-source-classification-panel">
                    <summary class="nks-source-classification-panel-header">
                        Filters
                    </summary>
                    <div class="nks-source-classification-grid">
                        ${this.get_source_classification_filter_html('tenant', 'Tenant')}
                        ${this.get_source_classification_filter_html('business_unit', 'Business Unit')}
                        ${this.get_source_classification_filter_html('context', 'Context')}
                        ${this.get_source_classification_filter_html('sub_context', 'Sub Context')}
                        ${this.get_source_classification_filter_html('entity_type', 'Entity Type')}
                        ${this.get_source_classification_filter_html('entity', 'Entity')}
                        ${this.get_source_classification_filter_html('topic', 'Topic')}
                    </div>
                    <div class="nks-inline-actions" style="margin-top: 10px;">
                        <button class="btn btn-default btn-xs nks-source-clear-classification-btn">
                            Clear Classification Filters
                        </button>
                    </div>
                </details>

                <div id="nks-knowledge-source-rows" class="nks-source-group-wrap">
                    <div class="text-muted text-center">Loading knowledge sources...</div>
                </div>
            </div>
        `;
    }

    get_source_tenant_stats_html() {
        const tenant_stats = (this.source_summary && this.source_summary.tenant_stats) || [];

        if (!tenant_stats.length) {
            return '';
        }

        return `
            <div class="nks-source-tenant-grid">
                ${tenant_stats.map((row) => {
                    const tenantKey = frappe.utils.escape_html(row.tenant || 'No Tenant');
                    const reachability = this.tenant_reachability
                        ? (this.tenant_reachability[row.tenant || 'No Tenant'] || null)
                        : undefined;
                    const reachabilityHtml = reachability === undefined
                        ? `<span style="color:#999; font-size:12px;">Checking reachability...</span>`
                        : this.get_tenant_reachability_inline_html(row.tenant || 'No Tenant', reachability);
                    return `
                        <div class="nks-source-tenant-card" data-tenant="${tenantKey}">
                            <div class="nks-source-tenant-title">${tenantKey}</div>
                            <div class="nks-source-tenant-stats">
                                <div>
                                    <strong>${frappe.utils.escape_html(String(row.total || 0))}</strong>
                                    <span>Sources</span>
                                </div>
                                <div>
                                    <strong>${frappe.utils.escape_html(String(row.published || 0))}</strong>
                                    <span>Published</span>
                                </div>
                                <div>
                                    <strong>${frappe.utils.escape_html(String(row.retrieval_ready || 0))}</strong>
                                    <span>Retrieval Ready</span>
                                </div>
                            </div>
                            <div class="nks-tenant-reachability" style="margin-top:8px; font-size:12px;">
                                ${reachabilityHtml}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    get_source_classification_filter_html(fieldname, label) {
        const options = (this.source_classification_options && this.source_classification_options[fieldname]) || [];
        const current = this.source_filters[fieldname] || '';

        return `
            <select class="form-control nks-source-classification-filter" data-fieldname="${frappe.utils.escape_html(fieldname)}">
                <option value="" ${current === '' ? 'selected' : ''}>${frappe.utils.escape_html(label)}: All</option>
                ${options.map((value) => {
                    return `
                        <option value="${frappe.utils.escape_html(value)}" ${current === value ? 'selected' : ''}>
                            ${frappe.utils.escape_html(value)}
                        </option>
                    `;
                }).join('')}
            </select>
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

    get_source_access_policy_options_html() {
        const fallback_policies = ['Public', 'Internal', 'Restricted'];
        const policies = (this.source_access_policies && this.source_access_policies.length)
            ? this.source_access_policies
            : fallback_policies;

        const options = [
            `<option value="" ${this.source_filters.access_policy === '' ? 'selected' : ''}>Access Policy: All</option>`
        ];

        policies.forEach((policy) => {
            if (!policy) {
                return;
            }

            options.push(`
                <option value="${frappe.utils.escape_html(policy)}" ${this.source_filters.access_policy === policy ? 'selected' : ''}>
                    ${frappe.utils.escape_html(policy)}
                </option>
            `);
        });

        return options.join('');
    }

    get_source_context_summary_dashboard_html(row) {
        const summary = row.context_summary || {};
        const exists = Boolean(summary.exists);
        const status = summary.status || 'Missing';

        return `
            <div class="nks-source-dashboard-panel ${exists ? 'nks-source-dashboard-summary' : ''}">
                <div class="nks-source-dashboard-panel-head">
                    <div>
                        <h4>Context Documentation Summary</h4>
                        <p>
                            Human-readable summary grouped by tenant, context, sub-context, entity, topic, and access policy.
                        </p>
                    </div>

                    <div class="nks-source-test-status-pill ${exists ? 'has-tests' : 'no-tests'}">
                        ${frappe.utils.escape_html(status)}
                    </div>
                </div>

                ${
                    exists
                        ? `
                            <div class="nks-source-summary-title">
                                ${frappe.utils.escape_html(summary.title || summary.name || 'Context Summary')}
                            </div>
                            <p class="nks-source-summary-text">
                                ${frappe.utils.escape_html(summary.summary_preview || summary.summary_text || '')}
                            </p>
                            <div class="nks-source-summary-meta">
                                <span>${frappe.utils.escape_html(String(summary.source_count || 0))} source(s)</span>
                                <span>${frappe.utils.escape_html(String(summary.chunk_count || 0))} chunk(s)</span>
                                <span>${frappe.utils.escape_html(summary.embedding_status || '-')}</span>
                                <span>${frappe.utils.escape_html(summary.generation_method || '-')}</span>
                            </div>
                        `
                        : `
                            <div class="nks-source-dashboard-note nks-source-dashboard-note-muted">
                                No grouped summary exists yet for this source scope. Processing an approved source will create or refresh the tenant/context documentation summary.
                            </div>
                        `
                }
            </div>
        `;
    }

    get_source_semantic_index_dashboard_html(row) {
        const summary = row.semantic_index_summary || {};
        const total = cint(summary.total || row.semantic_index_count || 0);
        const hasIndex = total > 0;

        return `
            <div class="nks-source-dashboard-panel nks-source-dashboard-index">
                <div class="nks-source-dashboard-panel-head">
                    <div>
                        <h4>Semantic Retrieval Index</h4>
                        <p>
                            Intent labels and likely user questions used to find the right approved chunks before answer generation.
                        </p>
                    </div>

                    <div class="nks-source-test-status-pill ${hasIndex ? 'has-tests' : 'no-tests'}">
                        ${hasIndex ? `${total} Entr${total === 1 ? 'y' : 'ies'}` : 'No Index'}
                    </div>
                </div>

                <div class="nks-source-test-grid">
                    <div class="nks-source-test-stat">
                        <div class="nks-source-test-value">${frappe.utils.escape_html(String(summary.intellectual_summary || 0))}</div>
                        <div class="nks-source-test-label">Intent Summaries</div>
                    </div>
                    <div class="nks-source-test-stat">
                        <div class="nks-source-test-value">${frappe.utils.escape_html(String(summary.user_question || 0))}</div>
                        <div class="nks-source-test-label">User Questions</div>
                    </div>
                    <div class="nks-source-test-stat">
                        <div class="nks-source-test-value">${frappe.utils.escape_html(String(summary.embedding_completed || 0))}</div>
                        <div class="nks-source-test-label">Vector Ready</div>
                    </div>
                    <div class="nks-source-test-stat">
                        <div class="nks-source-test-value">${frappe.utils.escape_html(String(summary.embedding_failed || 0))}</div>
                        <div class="nks-source-test-label">Failed</div>
                    </div>
                </div>

                <div class="nks-source-dashboard-note nks-source-dashboard-note-info">
                    Retrieval checks these entries first for similar intent, then uses the linked approved chunks for grounded Q&A and chat answers.
                </div>
            </div>
        `;
    }

    get_source_test_case_dashboard_html(row) {
    const summary = row.test_case_summary || {};

    const total = cint(summary.total || row.test_case_count || 0);
    const generated = cint(summary.generated || row.generated_test_case_count || 0);
    const active = cint(summary.active || row.active_test_case_count || 0);
    const draft = cint(summary.draft || row.draft_test_case_count || 0);
    const archived = cint(summary.archived || 0);

    const hasTests = total > 0;

    return `
        <div class="nks-source-dashboard-panel nks-source-dashboard-testing">
            <div class="nks-source-dashboard-panel-head">
                <div>
                    <h4>Validation Tests</h4>
                    <p>
                        Generated validation scenarios, execution runs, and quality verification.
                    </p>
                </div>

                <div class="nks-source-test-status-pill ${hasTests ? 'has-tests' : 'no-tests'}">
                    ${hasTests ? `${total} Validation Test${total === 1 ? '' : 's'}` : 'No Validation Tests'}
                </div>
            </div>

            ${
                hasTests
                    ? `
                        <div class="nks-source-test-grid">
                            <div class="nks-source-test-stat">
                                <div class="nks-source-test-value">${total}</div>
                                <div class="nks-source-test-label">Total Validation Tests</div>
                            </div>
                            <div class="nks-source-test-stat">
                                <div class="nks-source-test-value">${generated}</div>
                                <div class="nks-source-test-label">Generated</div>
                            </div>
                            <div class="nks-source-test-stat">
                                <div class="nks-source-test-value">${draft}</div>
                                <div class="nks-source-test-label">Draft</div>
                            </div>
                            <div class="nks-source-test-stat">
                                <div class="nks-source-test-value">${active}</div>
                                <div class="nks-source-test-label">Active</div>
                            </div>
                        </div>

                        <div class="nks-source-dashboard-note nks-source-dashboard-note-info">
                            Validation tests are available for this source. Review generated scenarios, run the validation suite,
                            and inspect validation run records for pass, warning, and failure details.
                            ${archived ? `<br>${frappe.utils.escape_html(String(archived))} older generated validation test${archived === 1 ? '' : 's'} archived from previous generations.` : ''}
                        </div>
                    `
                    : `
                        <div class="nks-source-dashboard-note nks-source-dashboard-note-muted">
                            No validation tests have been generated yet for this source.
                            ${archived ? `<br>${frappe.utils.escape_html(String(archived))} older generated validation test${archived === 1 ? '' : 's'} archived from previous generations.` : ''}
                        </div>
                    `
            }

            <div class="nks-source-dashboard-actions nks-source-dashboard-test-actions">
                <button class="btn btn-sm btn-default nks-open-source-test-cases-btn">
                    Open Validation Tests
                </button>

                ${
                    hasTests
                        ? `
                            <button class="btn btn-sm btn-default nks-review-source-test-cases-btn">
                                Review Generated Validation Tests
                            </button>

                            <button class="btn btn-sm btn-primary nks-run-source-test-cases-btn">
                                Run Validation Tests
                            </button>

                            <button class="btn btn-sm btn-default nks-open-source-test-runs-btn">
                                Open Validation Runs
                            </button>
                        `
                        : ''
                }
            </div>
        </div>
    `;
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
            'Validation Tests',
            'Validate source retrieval, grounded answers, citations, confidence, access status, and fallback behaviour.',
            [
                'This tab should connect with validation tests, validation runs, and Nexus Query Log.',
                'It will support run single validation, run tenant suite, view failed diagnostics, and copy combined diagnostics.',
                'This will align with the Knowledge Validation Lab work already completed.'
            ]
        );
    }

    get_gaps_html() {
        return this.get_placeholder_section(
            'Knowledge Gaps',
            'Identify missing, weak, stale, or poorly retrievable knowledge from failed tests and query logs.',
            [
                'Inputs should include no-context answers, fallback answers, low-confidence responses, and failed expected-source checks.',
                'Actions should include create Knowledge Source, create Knowledge Unit, mark Needs Review, and create validation test from gap.',
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
        const $container = this.body.find('#nks-knowledge-source-rows');

        if (!$container.length) {
            return;
        }

        if (!this.sources.length) {
            $container.html(`
                <div class="text-muted text-center">
                    No knowledge sources found.
                </div>
            `);
            return;
        }

        const grouped = this.group_sources_by_classification(this.sources);

        const html = Object.keys(grouped).sort().map((tenant) => {
            const tenantGroup = grouped[tenant];
            const tenantSources = tenantGroup.sources || [];
            const tenantStats = this.get_source_group_stats(tenantSources);

            return `
                <details class="nks-source-tenant-section" open>
                    <summary class="nks-source-tenant-head">
                        <div>
                            <h4>${frappe.utils.escape_html(tenant)}</h4>
                            <div class="nks-row-sub">
                                ${frappe.utils.escape_html(String(tenantStats.contexts.length))} Context${tenantStats.contexts.length === 1 ? '' : 's'}
                                · ${frappe.utils.escape_html(String(tenantStats.topics.length))} Topic${tenantStats.topics.length === 1 ? '' : 's'}
                            </div>
                        </div>
                        <div class="nks-source-context-stats">
                            <span class="nks-badge nks-badge-info">${tenantStats.total} Source${tenantStats.total === 1 ? '' : 's'}</span>
                            <span class="nks-badge nks-badge-good">${tenantStats.retrieval_ready} Ready</span>
                            <span class="nks-badge">${tenantStats.semantic_index_count} Index</span>
                            ${this.get_access_stats_html(tenantStats)}
                            <button class="btn btn-xs nks-access-details-btn"
                                    data-tenant="${frappe.utils.escape_html(tenant)}"
                                    data-context=""
                                    title="View access policy breakdown by category">
                                Access Details
                            </button>
                        </div>
                    </summary>

                    <div class="nks-source-tenant-body">
                        <div class="nks-source-context-grid">
                            ${Object.keys(tenantGroup.contexts).sort().map((contextName) => {
                                const contextGroup = tenantGroup.contexts[contextName];
                                const contextStats = this.get_source_group_stats(contextGroup.sources);
                                const contextKey = this.get_source_context_dom_key(tenant, contextName);

                                return `
                                    <details class="nks-source-context-group">
                                        <summary class="nks-source-context-head">
                                            <div class="nks-source-context-main">
                                                <div class="nks-source-context-title">${frappe.utils.escape_html(contextName)}</div>
                                                <div class="nks-source-context-meta">
                                                    ${frappe.utils.escape_html(contextStats.business_units.join(', ') || 'No business unit')}
                                                    ${(() => {
                                                        const sc = contextStats.sub_contexts;
                                                        if (!sc.length) return '';
                                                        if (sc.length <= 2) return ' · ' + frappe.utils.escape_html(sc.join(', '));
                                                        return ` · <span class="nks-badge nks-badge-neutral" title="${frappe.utils.escape_html(sc.join(', '))}">${sc.length} Sub-contexts</span>`;
                                                    })()}
                                                    ${contextStats.topics.length > 0 ? `· ${contextStats.topics.length} Topic${contextStats.topics.length === 1 ? '' : 's'}` : ''}
                                                </div>
                                            </div>
                                            <div class="nks-source-context-stats">
                                                <span class="nks-badge nks-badge-info">${contextStats.total} Source${contextStats.total === 1 ? '' : 's'}</span>
                                                <span class="nks-badge nks-badge-good">${contextStats.retrieval_ready} Ready</span>
                                                <span class="nks-badge">${contextStats.context_summary_count} Summar${contextStats.context_summary_count === 1 ? 'y' : 'ies'}</span>
                                                ${this.get_access_stats_html(contextStats)}
                                                <button class="btn btn-xs nks-access-details-btn"
                                                        data-tenant="${frappe.utils.escape_html(tenant)}"
                                                        data-context="${frappe.utils.escape_html(contextName)}"
                                                        title="View access policy breakdown by category">
                                                    Access Details
                                                </button>
                                                <span class="nks-badge nks-badge-info nks-context-approved-answer-count" data-context-key="${frappe.utils.escape_html(contextKey)}">
                                                    Answers ${contextStats.answer_approved}/${contextStats.answer_total}
                                                </span>
                                                <span class="nks-context-pending-answer-count" data-context-key="${frappe.utils.escape_html(contextKey)}">
                                                    ${this.get_context_answer_review_gap_badge_html(contextStats)}
                                                </span>
                                            </div>
                                        </summary>
                                        <div class="nks-source-context-body">
                                            ${contextGroup.sources.map((row) => this.get_source_group_item_html(row)).join('')}
                                        </div>
                                    </details>
                                `;
                            }).join('')}
                        </div>
                    </div>
                </details>
            `;
        }).join('');

        $container.html(html);
    }

    group_sources_by_classification(sources) {
        const grouped = {};

        (sources || []).forEach((row) => {
            const tenant = this.get_source_group_value(row, 'tenant', 'No Tenant');
            const contextName = this.get_source_group_value(row, 'context', 'Unclassified Context');

            grouped[tenant] = grouped[tenant] || {
                sources: [],
                contexts: {}
            };
            grouped[tenant].contexts[contextName] = grouped[tenant].contexts[contextName] || {
                sources: []
            };
            grouped[tenant].sources.push(row);
            grouped[tenant].contexts[contextName].sources.push(row);
        });

        return grouped;
    }

    get_source_group_value(row, fieldname, fallback) {
        const value = String((row && row[fieldname]) || '').trim();
        return value || fallback;
    }

    get_source_group_stats(sources) {
        const rows = sources || [];
        const unique = (fieldname) => {
            const values = rows
                .map((row) => this.get_source_group_value(row, fieldname, ''))
                .filter((value) => value);
            return [...new Set(values)].sort();
        };

        return {
            total: rows.length,
            published: rows.filter((row) => row.status === 'Published' || row.published).length,
            retrieval_ready: rows.filter((row) => row.retrieval_ready).length,
            context_summary_count: rows.filter((row) => row.context_summary_exists).length,
            semantic_index_count: rows.reduce((total, row) => total + Number(row.semantic_index_count || 0), 0),
            answer_total: rows.reduce((total, row) => total + Number((row.answer_approval_summary || {}).total || 0), 0),
            answer_approved: rows.reduce((total, row) => total + Number((row.answer_approval_summary || {}).approved || 0), 0),
            answer_pending: rows.reduce((total, row) => total + Number((row.answer_approval_summary || {}).pending || 0), 0),
            answer_rejected: rows.reduce((total, row) => total + Number((row.answer_approval_summary || {}).rejected || 0), 0),
            contexts: unique('context'),
            business_units: unique('business_unit'),
            sub_contexts: unique('sub_context'),
            entity_types: unique('entity_type'),
            entities: unique('entity'),
            topics: unique('topic'),
            access_policies: unique('access_policy'),
            access_policy_counts: rows.reduce((acc, row) => {
                const policy = String((row.access_policy || 'Unset')).trim();
                acc[policy] = (acc[policy] || 0) + 1;
                return acc;
            }, {}),
            ...(() => {
                const catMap = this.access_category_map || {};
                const catCounts = {};
                const uncatCounts = {};
                for (const row of rows) {
                    const policy = String((row.access_policy || '')).trim();
                    if (!policy) continue;
                    if (catMap[policy]) {
                        const cat = catMap[policy];
                        catCounts[cat] = (catCounts[cat] || 0) + 1;
                    } else {
                        // Policy exists but is not assigned to any Access Category
                        const shortName = policy.replace(/-[A-Z0-9][A-Z0-9-]*$/, '').trim() || policy;
                        uncatCounts[shortName] = (uncatCounts[shortName] || 0) + 1;
                    }
                }
                return { access_category_counts: catCounts, uncat_policy_counts: uncatCounts };
            })(),
        };
    }

    get_access_stats_html(stats) {
        const catRow  = this._access_row_badges(stats.access_category_counts || {}, 'category');
        const polRow  = this._access_row_badges(stats.access_policy_counts   || {}, 'policy');
        const uncatEntries = Object.entries(stats.uncat_policy_counts || {}).sort((a, b) => a[0].localeCompare(b[0]));

        if (!catRow && !polRow && !uncatEntries.length) return '';

        const uncatBadges = uncatEntries.map(([policy, count]) =>
            `<span class="nks-badge nks-badge-compact nks-badge-neutral"
                   title="${frappe.utils.escape_html(policy + ' — not assigned to any Access Category')}">
                 ${frappe.utils.escape_html(policy)}: ${count}
             </span>`
        ).join('');

        const rows = [
            catRow  ? `<div class="nks-access-row"><span class="nks-access-row-label">Categories</span>${catRow}</div>` : '',
            polRow  ? `<div class="nks-access-row"><span class="nks-access-row-label">Policies</span>${polRow}</div>` : '',
            uncatBadges ? `<div class="nks-access-row nks-access-row-warn">
                               <span class="nks-access-row-label">Not categorised</span>${uncatBadges}
                           </div>` : '',
        ].filter(Boolean).join('');

        return `<div class="nks-access-stats-container">${rows}</div>`;
    }

    _access_row_badges(counts, mode) {
        const entries = Object.entries(counts).sort((a, b) => {
            const tier = (n) => {
                const l = n.toLowerCase();
                if (l.includes('public'))                               return 1;
                if (l.includes('internal'))                             return 2;
                if (l.includes('restrict') || l.includes('confidential')) return 3;
                return 4;
            };
            return tier(a[0]) - tier(b[0]) || a[0].localeCompare(b[0]);
        });
        if (!entries.length) return '';

        return entries.map(([name, count]) => {
            const lower = name.toLowerCase();
            const isPublic     = lower.includes('public');
            const isRestricted = lower.includes('restrict') || lower.includes('confidential');
            const cls = isPublic ? 'nks-badge-good' : isRestricted ? 'nks-badge-warn' : 'nks-badge-info';
            // Strip tenant suffix AND " Access" suffix for compact display
            const short = name
                .replace(/-[A-Z0-9][A-Z0-9-]*$/, '')   // "-DIGITZ-AI-NEXUS"
                .replace(/\s+Access$/i, '')              // " Access"
                .trim() || name;
            return `<span class="nks-badge nks-badge-compact ${cls}" title="${frappe.utils.escape_html(name)}">${frappe.utils.escape_html(short)}: ${count}</span>`;
        }).join('');
    }

    get_access_policy_stats_html(stats) {
        const counts = stats.access_policy_counts || {};
        const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
        if (!entries.length) return '';

        const badges = entries.map(([policy, count]) => {
            // Strip tenant-code suffixes like "-DIGITZ-AI-NEXUS" so "Public-DIGITZ-AI-NEXUS" → "Public"
            const shortName = policy.replace(/-[A-Z0-9][A-Z0-9-]*$/, '').trim() || policy;
            const lower = policy.toLowerCase();
            const isPublic = lower.includes('public');
            const isRestricted = lower.includes('restrict') || lower.includes('private') || lower.includes('confidential');
            const cls = isPublic ? 'nks-badge-good' : isRestricted ? 'nks-badge-warn' : 'nks-badge-info';
            return `<span class="nks-badge nks-badge-compact ${cls}" title="${frappe.utils.escape_html(policy)}">${frappe.utils.escape_html(shortName)}: ${count}</span>`;
        }).join('');

        return `
            <span class="nks-policy-stats-group">
                <span class="nks-policy-stats-label">Access Policies</span>
                ${badges}
            </span>
        `;
    }

    get_access_category_stats_html(stats) {
        const counts = stats.access_category_counts || {};
        const tierOf = (name) => {
            const l = name.toLowerCase();
            if (l.includes('public'))                                       return 1;
            if (l.includes('internal'))                                     return 2;
            if (l.includes('restrict') || l.includes('confidential'))       return 3;
            return 4;
        };

        const entries = Object.entries(counts).sort(
            (a, b) => tierOf(a[0]) - tierOf(b[0]) || a[0].localeCompare(b[0])
        );
        const uncatEntries = Object.entries(stats.uncat_policy_counts || {}).sort((a, b) => a[0].localeCompare(b[0]));

        if (!entries.length && !uncatEntries.length) return '';

        const badges = entries.map(([cat, count]) => {
            const lower = cat.toLowerCase();
            const isPublic     = lower.includes('public');
            const isRestricted = lower.includes('restrict') || lower.includes('confidential');
            const cls = isPublic ? 'nks-badge-good' : isRestricted ? 'nks-badge-warn' : 'nks-badge-info';
            const shortName = cat.replace(/\s+Access$/i, '').trim() || cat;
            return `<span class="nks-badge nks-badge-compact ${cls}" title="${frappe.utils.escape_html(cat)}">${frappe.utils.escape_html(shortName)}: ${count}</span>`;
        }).join('');

        // Policies that exist in sources but belong to no Access Category
        const uncatBadges = uncatEntries.map(([policy, count]) => {
            const title = `${policy} — not assigned to any Access Category`;
            return `<span class="nks-badge nks-badge-compact nks-badge-neutral" title="${frappe.utils.escape_html(title)}">${frappe.utils.escape_html(policy)}: ${count}</span>`;
        }).join('');

        const uncatGroup = uncatEntries.length
            ? `<span class="nks-policy-stats-group nks-policy-stats-group-warn">
                   <span class="nks-policy-stats-label">Policies not participating</span>
                   ${uncatBadges}
               </span>`
            : '';

        return `
            <span class="nks-policy-stats-group">
                <span class="nks-policy-stats-label">Access Categories</span>
                ${badges}
            </span>${uncatGroup}
        `;
    }

    get_context_answer_review_gap_badge_html(stats) {
        const pending = Number((stats && stats.answer_pending) || 0);
        const rejected = Number((stats && stats.answer_rejected) || 0);

        if (rejected > 0) {
            return `<span class="nks-badge nks-badge-warn">${frappe.utils.escape_html(String(rejected))} Rejected</span>`;
        }

        if (pending > 0) {
            return `<span class="nks-badge">${frappe.utils.escape_html(String(pending))} Pending</span>`;
        }

        return '';
    }

    get_source_context_dom_key(tenant, contextName) {
        return `${tenant || ''}::${contextName || ''}`;
    }

    flatten_source_group(group) {
        if (Array.isArray(group)) {
            return group;
        }

        return Object.values(group || {}).reduce((result, value) => {
            return result.concat(this.flatten_source_group(value));
        }, []);
    }

    get_source_group_item_html(row) {
        const status = row.status || 'Draft';
        const source_type = row.source_type || 'Manual';
        const access_policy = row.access_policy || '-';
        const next_step = row.next_action_label || 'Review source';
        const disabled_badge = row.disabled
            ? `<span class="nks-badge nks-badge-warn">Disabled</span>`
            : '';
        const approvalSummary = row.answer_approval_summary || {};
        const compact_tags = [
            row.entity_type,
            row.topic || row.entity
        ].filter(Boolean);

        return `
            <details class="nks-source-item" data-source="${frappe.utils.escape_html(row.name || '')}">
                <summary class="nks-source-item-head">
                    <div class="nks-source-item-head-title">
                        <div class="nks-source-title-text">${frappe.utils.escape_html(row.source_title || row.name)}</div>
                        <div class="nks-source-title-sub">
                            <span>${frappe.utils.escape_html(source_type)}</span>
                        </div>
                        ${(row.context_path || row.context) ? `
                        <div class="nks-source-title-path">
                            ${frappe.utils.escape_html(row.context_path || [row.business_unit, row.context, row.sub_context].filter(Boolean).join(' › '))}
                        </div>` : ''}
                        <div class="nks-source-title-tags">
                            ${compact_tags.map((tag) => `<span class="nks-badge nks-badge-compact">${frappe.utils.escape_html(tag)}</span>`).join('')}
                            <button class="nks-classification-info-btn" data-source="${frappe.utils.escape_html(row.name || '')}" title="View full classification">ⓘ</button>
                        </div>
                    </div>
                    <div class="nks-source-item-head-footer">
                        ${access_policy ? `<span class="nks-badge nks-badge-info">${frappe.utils.escape_html(access_policy)}</span>` : ''}
                        <span class="nks-badge ${
                            status === 'Published' || row.readiness_status === 'published' ? 'nks-badge-published' :
                            row.readiness_status === 'ready_to_publish' ? 'nks-badge-validated' :
                            row.readiness_status === 'ready_for_validation' ? 'nks-badge-processed' :
                            row.readiness_status === 'needs_answer_approval' ? 'nks-badge-warn' :
                            ''
                        }">${frappe.utils.escape_html(row.readiness_label || status)}</span>
                        ${disabled_badge}
                        <span class="nks-source-inline-actions" data-source="${frappe.utils.escape_html(row.name)}">
                            ${this.get_source_inline_actions_html(row)}
                        </span>
                        <button class="btn btn-xs btn-primary nks-source-dashboard-btn" data-name="${frappe.utils.escape_html(row.name)}">
                            Dashboard
                        </button>
                    </div>
                </summary>

                <div class="nks-source-item-body">
                    <div class="nks-source-detail-box">
                        <div class="nks-source-detail-label">Classification</div>
                        <div class="nks-source-detail-value">
                            ${frappe.utils.escape_html(row.business_unit || '-')}
                            ${row.sub_context ? '<br>' + frappe.utils.escape_html(row.sub_context) : ''}
                            ${row.entity_type ? '<br>' + frappe.utils.escape_html(row.entity_type) : ''}
                            ${row.entity ? ' · ' + frappe.utils.escape_html(row.entity) : ''}
                            ${row.topic ? '<br>' + frappe.utils.escape_html(row.topic) : ''}
                        </div>
                    </div>

                    <div class="nks-source-detail-box">
                        <div class="nks-source-detail-label">Readiness</div>
                        <div class="nks-source-detail-value">
                            Next: <span class="nks-source-next-step" data-source="${frappe.utils.escape_html(row.name)}">${frappe.utils.escape_html(next_step)}</span>
                            <br>Processing: ${frappe.utils.escape_html(row.processing_status || '-')}
                            <br>Embedding: ${frappe.utils.escape_html(row.embedding_status || '-')}
                            <br>Diagnostics: ${frappe.utils.escape_html(row.diagnostics_status || '-')}
                        </div>
                    </div>

                    <div class="nks-source-detail-box">
                        <div class="nks-source-detail-label">Retrieval Assets</div>
                        <div class="nks-source-detail-value">
                            Summary: ${frappe.utils.escape_html(row.context_summary_status || 'Missing')}
                            <br>Index Entries: ${frappe.utils.escape_html(String(row.semantic_index_count || 0))}
                            <br>Chunks: ${frappe.utils.escape_html(String(row.active_chunk_count || row.chunk_count || 0))}
                            <br>Approved Answers: <span class="nks-approved-answer-count" data-source="${frappe.utils.escape_html(row.name)}">${frappe.utils.escape_html(String(approvalSummary.approved || 0))}/${frappe.utils.escape_html(String(approvalSummary.total || 0))}</span>
                            <span class="nks-rejected-answer-count" data-source="${frappe.utils.escape_html(row.name)}">${approvalSummary.rejected ? '<br>Rejected: ' + frappe.utils.escape_html(String(approvalSummary.rejected)) : ''}</span>
                        </div>
                    </div>

                    ${this.get_source_index_review_html(row)}

                    <div class="nks-source-item-actions">
                        <a class="btn btn-xs btn-default" href="/app/nexus-knowledge-source/${encodeURIComponent(row.name)}">
                            Review Source
                        </a>
                    </div>
                </div>
            </details>
        `;
    }

    get_source_inline_actions_html(row) {
        const buttons = [];
        const name = frappe.utils.escape_html(row.name || '');

        if (this.can_show_process_source_action(row)) {
            buttons.push(`
                <button class="btn btn-xs btn-primary nks-inline-process-source-btn" data-name="${name}">
                    Process
                </button>
            `);
        }

        if (row.readiness_status === 'needs_answer_approval') {
            buttons.push(`
                <button class="btn btn-xs btn-primary nks-inline-validate-questions-llm-btn" data-name="${name}">
                    Validate with AI
                </button>
                <button class="btn btn-xs btn-warning nks-inline-review-answers-btn" data-name="${name}">
                    Review
                </button>
                <button class="btn btn-xs btn-success nks-inline-approve-all-answers-btn" data-name="${name}">
                    Approve All
                </button>
            `);
        }

        if (row.can_validate) {
            buttons.push(`
                <button class="btn btn-xs btn-primary nks-inline-validate-source-btn" data-name="${name}">
                    Validate
                </button>
            `);
        }

        if (row.can_publish) {
            buttons.push(`
                <button class="btn btn-xs btn-primary nks-inline-publish-source-btn" data-name="${name}">
                    Publish
                </button>
            `);
        }

        if (row.can_unpublish) {
            buttons.push(`
                <button class="btn btn-xs btn-default nks-inline-unpublish-source-btn" data-name="${name}">
                    Unpublish
                </button>
            `);
        }

        if (this.can_show_generate_test_cases_action(row)) {
            buttons.push(`
                <button class="btn btn-xs btn-default nks-inline-generate-tests-btn" data-name="${name}">
                    Validation Tests
                </button>
            `);
        }

        return buttons.join('');
    }

    is_source_validated(row) {
        row = row || {};

        const status = String(row.status || '').toLowerCase();
        const validationStatus = String(
            row.validation_status ||
            (row.technical_status && row.technical_status.validation_status) ||
            ''
        ).toLowerCase();

        return (
            ['ready to publish', 'published'].includes(status) ||
            ['passed', 'validated', 'tested'].includes(validationStatus)
        );
    }

    get_source_index_review_html(row) {
        const summary = row.semantic_index_summary || {};
        const review_entries = summary.review_entries || {};
        const questions = review_entries.user_question || [];
        const intellectual_summaries = review_entries.intellectual_summary || [];

        if (!questions.length && !intellectual_summaries.length) {
            return `
                <div class="nks-source-detail-box nks-source-detail-box-wide">
                    <div class="nks-source-detail-label">Reviewable Retrieval Index</div>
                    <div class="nks-source-detail-value">No active possible questions or intellectual summaries found for this source.</div>
                </div>
            `;
        }

        return `
            <div class="nks-source-detail-box nks-source-detail-box-wide">
                <div class="nks-source-detail-label">Reviewable Retrieval Index</div>
                <div class="nks-source-index-review-grid">
                    <div>
                        <div class="nks-source-detail-value">
                            Possible Questions (${frappe.utils.escape_html(String(summary.user_question || questions.length || 0))})
                        </div>
                        ${this.get_source_index_review_list_html(questions, true, row.name)}
                    </div>
                    <div>
                        <div class="nks-source-detail-value">
                            Intellectual Summaries (${frappe.utils.escape_html(String(summary.intellectual_summary || intellectual_summaries.length || 0))})
                        </div>
                        ${this.get_source_index_review_list_html(intellectual_summaries, false, row.name)}
                    </div>
                </div>
            </div>
        `;
    }

    get_source_index_review_list_html(entries, includeAnswerReview, sourceName) {
        if (!entries || !entries.length) {
            return '<div class="nks-row-sub" style="margin-top: 8px;">No entries available.</div>';
        }

        return `
            <ol class="nks-source-index-review-list">
                ${entries.map((entry) => {
                    const question = entry.canonical_text || entry.display_summary || entry.name || '';
                    const answer = entry.generated_answer || '';
                    const reviewStatus = entry.answer_review_status || 'Pending Review';
                    const confidenceNote = entry.answer_review_notes || '';
                    const isAiDecision = (entry.answer_reviewed_by || '').startsWith('System');

                    // Confidence badge colour
                    const confidenceMatch = confidenceNote.match(/(\d+)%/);
                    const confidence = confidenceMatch ? parseInt(confidenceMatch[1]) : null;
                    const confidenceColor = confidence === null ? '#888'
                        : confidence >= 80 ? '#16a34a'
                        : confidence >= 40 ? '#d97706'
                        : '#dc2626';

                    const statusColor = reviewStatus === 'Approved' ? '#16a34a'
                        : reviewStatus === 'Rejected' ? '#dc2626'
                        : '#d97706';

                    return `
                        <li class="nks-source-index-review-entry" data-entry-name="${frappe.utils.escape_html(entry.name || '')}" data-source="${frappe.utils.escape_html(sourceName || '')}">
                            <div style="font-weight:500;">${frappe.utils.escape_html(question)}</div>
                            ${
                                includeAnswerReview
                                    ? `
                                        ${answer ? `
                                        <div class="nks-source-index-answer" style="margin-top:4px;">
                                            <strong>AI Answer:</strong><br>
                                            ${frappe.utils.escape_html(answer)}
                                        </div>` : ''}
                                        <div class="nks-row-sub nks-index-answer-review-status" style="margin-top:4px; display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                                            <span style="color:${statusColor}; font-weight:500;">${frappe.utils.escape_html(reviewStatus)}</span>
                                            ${confidenceNote ? `<span style="color:${confidenceColor}; font-size:11px;">${frappe.utils.escape_html(confidenceNote)}</span>` : ''}
                                            ${isAiDecision ? '<span style="font-size:10px; color:#6b7280; background:#f3f4f6; padding:1px 6px; border-radius:10px;">AI</span>' : ''}
                                        </div>
                                        <div class="nks-source-index-actions">
                                            ${this.get_index_answer_review_actions_html(entry.name, reviewStatus)}
                                        </div>
                                    `
                                    : ''
                            }
                        </li>
                    `;
                }).join('')}
            </ol>
        `;
    }

    get_index_answer_review_actions_html(entryName, reviewStatus) {
        const isApproved = String(reviewStatus || '').toLowerCase() === 'approved';
        const safeName = frappe.utils.escape_html(entryName || '');
        const primaryAction = isApproved ? 'unapprove' : 'approve';
        const primaryLabel = isApproved ? 'Unapprove' : 'Approve Answer';
        const primaryClass = isApproved ? 'btn-default' : 'btn-primary';

        return `
            <button class="btn btn-xs ${primaryClass} nks-index-answer-review-btn" data-name="${safeName}" data-action="${primaryAction}">
                ${primaryLabel}
            </button>
            <button class="btn btn-xs btn-default nks-index-answer-review-btn" data-name="${safeName}" data-action="reject">
                Reject
            </button>
        `;
    }

    review_index_answer(name, action, $button) {
        if (!name || !action) {
            frappe.msgprint('Generated answer review action is missing.');
            return;
        }
        const normalizedAction = String(action || '').toLowerCase();
        const actionLabel = normalizedAction === 'approve'
            ? 'Approving generated answer...'
            : normalizedAction === 'unapprove'
                ? 'Unapproving generated answer...'
                : 'Rejecting generated answer...';

        const $entry = $button && $button.length
            ? $button.closest('.nks-source-index-review-entry')
            : $();
        const $buttons = $entry.length
            ? $entry.find('.nks-index-answer-review-btn')
            : $button;

        if ($buttons && $buttons.length) {
            $buttons.prop('disabled', true);
        }

        if ($entry.length) {
            $entry.find('.nks-index-answer-review-status').html('Review: Updating...');
        }

        frappe.call({
            method: this.api.review_index_answer,
            args: {
                name: name,
                action: action
            },
            freeze: true,
            freeze_message: actionLabel,
            callback: (r) => {
                const result = r.message || {};

                if (!result.success) {
                    frappe.msgprint({
                        title: 'Answer Review Failed',
                        indicator: 'orange',
                        message: frappe.utils.escape_html(result.message || 'Unable to update generated answer review.')
                    });

                    if ($buttons && $buttons.length) {
                        $buttons.prop('disabled', false);
                    }
                    return;
                }

                this.apply_index_answer_review_result(name, result, $button);

                frappe.show_alert({
                    message: result.message || 'Generated answer review updated.',
                    indicator: normalizedAction === 'approve' ? 'green' : 'orange'
                });

                this.load_source_summary({ render: false });
            },
            error: () => {
                if ($buttons && $buttons.length) {
                    $buttons.prop('disabled', false);
                }

                if ($entry.length) {
                    $entry.find('.nks-index-answer-review-status').html('Review: Update failed');
                }

                frappe.msgprint({
                    title: 'Answer Review Failed',
                    indicator: 'red',
                    message: 'Unable to update generated answer review. Please check the server error log.'
                });
            }
        });
    }

    validate_source_questions_with_llm(source_name) {
        if (!source_name) return;

        frappe.confirm(
            `AI will score each question by attempting to answer it from the source content only.<br><br>
            <b>≥ 80% confidence</b> → auto-approved with generated answer<br>
            <b>40–79%</b> → kept for your review (partial match)<br>
            <b>&lt; 40%</b> → auto-rejected (question not answerable from this source)<br><br>
            You can override any decision in the Review panel. Proceed?`,
            () => {
                frappe.call({
                    method: this.api.validate_source_questions_with_llm,
                    args: { source_name },
                    freeze: true,
                    freeze_message: 'AI is validating questions — this may take a moment...',
                    callback: (r) => {
                        const result = r.message || {};
                        if (!result.success) {
                            frappe.msgprint({
                                title: 'Validation Failed',
                                indicator: 'orange',
                                message: frappe.utils.escape_html(result.message || 'Unable to run AI validation.'),
                            });
                            return;
                        }
                        const c = result.counts || {};
                        const needsReview = c.pending || 0;
                        frappe.msgprint({
                            title: 'AI Validation Complete',
                            indicator: needsReview ? 'orange' : 'green',
                            message: `
                                <b>Auto-approved</b> (≥80%): ${c.approved || 0}<br>
                                <b>Needs your review</b> (40–79%): ${needsReview}<br>
                                <b>Auto-rejected</b> (&lt;40%): ${c.rejected || 0}<br>
                                ${c.errors ? `<b>Errors:</b> ${c.errors}<br>` : ''}
                                ${needsReview ? '<br>Open the <b>Review</b> panel to handle the borderline questions.' : ''}
                            `,
                        });
                        this.load();
                    },
                });
            }
        );
    }

    bulk_approve_source_answers(source_name) {
        if (!source_name) return;

        frappe.confirm(
            `Approve all pending generated answers for this source?`,
            () => {
                frappe.call({
                    method: this.api.bulk_approve_source_answers,
                    args: { source_name },
                    freeze: true,
                    freeze_message: 'Approving all answers...',
                    callback: (r) => {
                        const result = r.message || {};
                        if (!result.success) {
                            frappe.msgprint({
                                title: 'Approve All Failed',
                                indicator: 'orange',
                                message: frappe.utils.escape_html(result.message || 'Unable to approve answers.'),
                            });
                            return;
                        }
                        frappe.show_alert({
                            message: result.message || 'All answers approved.',
                            indicator: 'green',
                        });
                        this.load();
                    },
                });
            }
        );
    }

    apply_index_answer_review_result(name, result, $button) {
        const sourceName = result.source_name || (
            $button && $button.length
                ? $button.closest('.nks-source-index-review-entry').data('source')
                : ''
        );
        const reviewStatus = result.answer_review_status || 'Pending Review';
        const reviewedBy = result.answer_reviewed_by || (frappe.session && frappe.session.user) || '';
        const reviewText = `Review: ${frappe.utils.escape_html(reviewStatus)}${reviewedBy ? ' by ' + frappe.utils.escape_html(reviewedBy) : ''}`;

        $(document.body)
            .find('.nks-source-index-review-entry')
            .filter((index, element) => {
                return String($(element).data('entryName') || '') === String(name || '');
            })
            .each((index, element) => {
                const $entry = $(element);
                $entry.find('.nks-index-answer-review-status').html(reviewText);
                $entry
                    .find('.nks-source-index-actions')
                    .html(this.get_index_answer_review_actions_html(name, reviewStatus));
            });

        this.update_source_answer_review_state(name, result);

        if (sourceName && result.answer_approval_summary) {
            const summary = result.answer_approval_summary || {};
            const approvedText = `${summary.approved || 0}/${summary.total || 0}`;
            const rejectedText = summary.rejected ? `<br>Rejected: ${frappe.utils.escape_html(String(summary.rejected))}` : '';

            $(document.body)
                .find('.nks-approved-answer-count')
                .filter((index, element) => String($(element).data('source') || '') === String(sourceName))
                .text(approvedText);

            $(document.body)
                .find('.nks-rejected-answer-count')
                .filter((index, element) => String($(element).data('source') || '') === String(sourceName))
                .html(rejectedText);

            this.refresh_source_context_answer_stats(sourceName);
        }
    }

    update_source_answer_review_state(name, result) {
        const sourceName = result.source_name || '';
        const reviewStatus = result.answer_review_status || 'Pending Review';

        (this.sources || []).forEach((source) => {
            if (sourceName && source.name !== sourceName) {
                return;
            }

            const reviewEntries = (
                source.semantic_index_summary &&
                source.semantic_index_summary.review_entries &&
                source.semantic_index_summary.review_entries.user_question
            ) || [];

            reviewEntries.forEach((entry) => {
                if (entry.name !== name) {
                    return;
                }

                entry.answer_review_status = reviewStatus;
                entry.answer_reviewed_by = result.answer_reviewed_by || (frappe.session && frappe.session.user) || '';
                entry.answer_reviewed_on = result.answer_reviewed_on || '';
            });

            if (result.answer_approval_summary) {
                source.answer_approval_summary = result.answer_approval_summary;
                source.retrieval_ready = result.retrieval_ready || 0;

                if (source.semantic_index_summary && result.answer_approval_summary.semantic_index_summary) {
                    source.semantic_index_summary = result.answer_approval_summary.semantic_index_summary;
                }
            }

            if (result.readiness) {
                Object.assign(source, result.readiness);
            }
        });

        if (sourceName) {
            this.refresh_source_inline_readiness(sourceName);
        }
    }

    refresh_source_context_answer_stats(sourceName) {
        const source = (this.sources || []).find((item) => item.name === sourceName);

        if (!source) {
            return;
        }

        const tenant = this.get_source_group_value(source, 'tenant', 'No Tenant');
        const contextName = this.get_source_group_value(source, 'context', 'Unclassified Context');
        const contextKey = this.get_source_context_dom_key(tenant, contextName);
        const contextSources = (this.sources || []).filter((item) => {
            return (
                this.get_source_group_value(item, 'tenant', 'No Tenant') === tenant &&
                this.get_source_group_value(item, 'context', 'Unclassified Context') === contextName
            );
        });
        const stats = this.get_source_group_stats(contextSources);

        $(document.body)
            .find('.nks-context-approved-answer-count')
            .filter((index, element) => String($(element).data('contextKey') || '') === String(contextKey))
            .text(`Answers ${stats.answer_approved}/${stats.answer_total}`);

        $(document.body)
            .find('.nks-context-pending-answer-count')
            .filter((index, element) => String($(element).data('contextKey') || '') === String(contextKey))
            .html(this.get_context_answer_review_gap_badge_html(stats));
    }

    refresh_source_inline_readiness(sourceName) {
        const source = (this.sources || []).find((item) => item.name === sourceName);

        if (!source) {
            return;
        }

        $(document.body)
            .find('.nks-source-next-step')
            .filter((index, element) => String($(element).data('source') || '') === String(sourceName))
            .text(source.next_action_label || 'Review source');

        $(document.body)
            .find('.nks-source-inline-actions')
            .filter((index, element) => String($(element).data('source') || '') === String(sourceName))
            .html(this.get_source_inline_actions_html(source));
    }

    show_access_details_dialog(sources, title) {
        // Sort categories by priority (from actual Nexus Access Category records)
        const catList = (this.access_categories_list || [])
            .slice()
            .sort((a, b) => (a.priority || 0) - (b.priority || 0));

        // Count sources per access_policy (real values from Nexus Knowledge Source)
        const policyCounts = {};
        for (const s of sources) {
            const p = (s.access_policy || '').trim();
            if (p) policyCounts[p] = (policyCounts[p] || 0) + 1;
        }

        // Collect all policies that appear in at least one category's actual allowed_policies
        const allCategorisedPolicies = new Set(
            catList.flatMap(cat => cat.policies || [])
        );

        // Policies used in these sources but not assigned to ANY category
        const uncatPolicies = Object.keys(policyCounts)
            .filter(p => !allCategorisedPolicies.has(p))
            .sort();

        const tierColour = (name) => {
            const l = (name || '').toLowerCase();
            if (l.includes('public'))                                   return { bg: '#ecfffb', border: '#00b894', text: '#006e59' };
            if (l.includes('restrict') || l.includes('confidential'))   return { bg: '#fff7e8', border: '#e0a62f', text: '#a66d00' };
            return                                                             { bg: '#eef6ff', border: '#2177ff', text: '#0b47b8' };
        };

        const policyBar = (policy, count, colour) => {
            const bar  = Math.round((count / (sources.length || 1)) * 100);
            const full = policy;                                              // full name e.g. "Public-DIGITZ-AI-NEXUS"
            const short = policy.replace(/-[A-Z0-9][A-Z0-9-]*$/, '').trim() || policy;
            return `
                <div class="nks-ad-policy-row">
                    <div class="nks-ad-policy-name" title="${frappe.utils.escape_html(full)}">${frappe.utils.escape_html(short)}</div>
                    <div class="nks-ad-policy-bar-wrap">
                        <div class="nks-ad-policy-bar" style="width:${bar}%; background:${colour};"></div>
                    </div>
                    <div class="nks-ad-policy-count">${count} source${count === 1 ? '' : 's'}</div>
                </div>`;
        };

        // One card per category — using cat.policies (actual allowed_policies assignments)
        let cardsHtml = catList.map(cat => {
            // cat.policies = real policy names from Nexus Access Category Policy child table
            const assignedPolicies = (cat.policies || []).filter(p => policyCounts[p]);
            if (!assignedPolicies.length) return ''; // nothing in this scope

            const label      = (cat.category_name || cat.title || cat.name || '').trim();
            const shortLabel = label.replace(/\s+Access$/i, '').trim() || label;
            const colour     = tierColour(label);
            const totalCount = assignedPolicies.reduce((s, p) => s + policyCounts[p], 0);

            const rows = assignedPolicies.map(p => policyBar(p, policyCounts[p], colour.border)).join('');

            return `
                <div class="nks-ad-cat-card" style="border-color:${colour.border}; background:${colour.bg};">
                    <div class="nks-ad-cat-header">
                        <span class="nks-ad-cat-label" style="color:${colour.text};">${frappe.utils.escape_html(shortLabel)}</span>
                        <span class="nks-ad-priority">Priority ${cat.priority || '—'}</span>
                        <span class="nks-ad-cat-total" style="color:${colour.text};">${totalCount} source${totalCount === 1 ? '' : 's'}</span>
                    </div>
                    <div class="nks-ad-policy-list">${rows}</div>
                </div>`;
        }).filter(Boolean).join('');

        // Policies used in sources but not in ANY category's allowed_policies
        if (uncatPolicies.length) {
            const rows = uncatPolicies.map(p => policyBar(p, policyCounts[p], '#94a3b8')).join('');
            const total = uncatPolicies.reduce((s, p) => s + policyCounts[p], 0);
            cardsHtml += `
                <div class="nks-ad-cat-card" style="border-color:#cbd5e1; background:#f8fafc;">
                    <div class="nks-ad-cat-header">
                        <span class="nks-ad-cat-label" style="color:#475569;">Not categorised</span>
                        <span class="nks-ad-cat-subtitle">These policies are not assigned to any Access Category</span>
                        <span class="nks-ad-cat-total" style="color:#475569;">${total} source${total === 1 ? '' : 's'}</span>
                    </div>
                    <div class="nks-ad-policy-list">${rows}</div>
                </div>`;
        }

        if (!cardsHtml) {
            cardsHtml = '<div class="text-muted" style="padding:16px;">No access policy data available for this scope.</div>';
        }

        const html = `
            <style>
                .nks-ad-wrap { display: flex; flex-direction: column; gap: 12px; padding: 4px 0; }
                .nks-ad-cat-card { border: 1.5px solid; border-radius: 12px; padding: 12px 16px; }
                .nks-ad-cat-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
                .nks-ad-cat-label { font-size: 13px; font-weight: 800; letter-spacing: 0.03em; flex: 1; }
                .nks-ad-priority { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.04em; }
                .nks-ad-cat-subtitle { font-size: 11px; color: #94a3b8; font-style: italic; }
                .nks-ad-cat-total { font-size: 11px; font-weight: 700; margin-left: auto; white-space: nowrap; }
                .nks-ad-policy-list { display: flex; flex-direction: column; gap: 6px; }
                .nks-ad-policy-row { display: grid; grid-template-columns: 110px 1fr 70px; align-items: center; gap: 10px; }
                .nks-ad-policy-name { font-size: 12px; font-weight: 600; color: #334155; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
                .nks-ad-policy-bar-wrap { height: 6px; background: rgba(0,0,0,0.07); border-radius: 3px; overflow: hidden; }
                .nks-ad-policy-bar { height: 100%; border-radius: 3px; transition: width 0.3s ease; }
                .nks-ad-policy-count { font-size: 11px; color: #64748b; text-align: right; white-space: nowrap; }
            </style>
            <div class="nks-ad-wrap">${cardsHtml}</div>`;

        const dialog = new frappe.ui.Dialog({
            title,
            size: 'large',
            fields: [{ fieldtype: 'HTML', fieldname: 'content' }],
        });
        dialog.fields_dict.content.$wrapper.html(html);
        dialog.show();
    }

    show_classification_popup(triggerEl) {
        const sourceName = $(triggerEl).data('source');

        // Toggle: if this button's popup is already open, close it
        const $existing = $('.nks-classification-popup');
        if ($existing.length && $existing.data('source') === sourceName) {
            $existing.remove();
            return;
        }
        $existing.remove();
        const row = (this.sources || []).find(s => s.name === sourceName);
        if (!row) return;

        const fields = [
            { label: 'Tenant',        value: row.tenant },
            { label: 'Business Unit', value: row.business_unit },
            { label: 'Context',       value: row.context },
            { label: 'Sub-context',   value: row.sub_context },
            { label: 'Entity Type',   value: row.entity_type },
            { label: 'Entity',        value: row.entity },
            { label: 'Topic',         value: row.topic },
            { label: 'Access Policy', value: row.access_policy },
            { label: 'Priority',      value: row.priority != null ? String(row.priority) : null },
        ].filter(f => f.value);

        const rows = fields.map(f => `
            <div class="nks-classification-popup-row">
                <span class="nks-classification-popup-label">${frappe.utils.escape_html(f.label)}</span>
                <span class="nks-classification-popup-value">${frappe.utils.escape_html(f.value)}</span>
            </div>
        `).join('');

        const $popup = $(`<div class="nks-classification-popup">${rows || '<em>No classification set.</em>'}</div>`).data('source', sourceName);
        $(document.body).append($popup);

        // Position below the trigger button
        const rect = triggerEl.getBoundingClientRect();
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollLeft = window.scrollX || document.documentElement.scrollLeft;

        let top = rect.bottom + scrollTop + 6;
        let left = rect.left + scrollLeft;

        // Keep within viewport
        const popupWidth = 340;
        if (left + popupWidth > window.innerWidth + scrollLeft - 12) {
            left = window.innerWidth + scrollLeft - popupWidth - 12;
        }

        $popup.css({ top, left, position: 'absolute' });
    }

    render_sources_error() {
        if (this.active_tab !== 'sources') {
            return;
        }

        const $container = this.body.find('#nks-knowledge-source-rows');

        if (!$container.length) {
            return;
        }

        $container.html(`
            <div class="text-danger text-center">
                Failed to load knowledge sources.
            </div>
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

   get_source_publish_state(row) {
        row = row || {};

        const status = String(row.status || '').toLowerCase();
        const readiness_status = String(row.readiness_status || '').toLowerCase();
        const validation_status = String(row.validation_status || '').toLowerCase();

        if (
            row.is_published ||
            row.published ||
            status === 'published' ||
            readiness_status === 'published'
        ) {
            return 'Published';
        }

        if (
            row.can_publish ||
            row.ready_to_publish ||
            status === 'ready to publish' ||
            readiness_status === 'ready_to_publish'
        ) {
            return 'Ready to Publish';
        }

        if (
            validation_status === 'passed' ||
            status === 'validated' ||
            readiness_status === 'ready_for_publish' ||
            readiness_status === 'ready_for_validation'
        ) {
            return 'Validated';
        }

        if (this.is_source_prepared(row)) {
            return 'Prepared';
        }

        return 'Not Ready';
    }

    get_source_technical_value(row, technical_status, fieldname, fallback = '-') {
        row = row || {};
        technical_status = technical_status || {};

        const technical_value = technical_status[fieldname];

        if (
            technical_value !== undefined &&
            technical_value !== null &&
            technical_value !== ''
        ) {
            return technical_value;
        }

        const row_value = row[fieldname];

        if (
            row_value !== undefined &&
            row_value !== null &&
            row_value !== ''
        ) {
            return row_value;
        }

        return fallback;
    }

    format_source_yes_no(value) {
        if (
            value === true ||
            value === 1 ||
            value === '1' ||
            String(value || '').toLowerCase() === 'yes' ||
            String(value || '').toLowerCase() === 'true'
        ) {
            return 'Yes';
        }

        return 'No';
    }

    can_show_process_source_action(row) {
        row = row || {};

        const readiness_status = String(row.readiness_status || '').toLowerCase();
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

        if (
            row.is_published ||
            row.published ||
            status === 'published' ||
            readiness_status === 'published'
        ) {
            return false;
        }

        if (
            ['processing', 'running', 'in progress'].includes(processing_status) ||
            ['processing', 'running', 'in progress'].includes(sync_status)
        ) {
            return false;
        }

        if (row.disabled) {
            return false;
        }

        return !this.is_source_prepared(row);
    }

    get_source_chat_reachability_html(result) {
        if (!result) {
            return `
                <div class="nks-dashboard-card" style="width:100%;">
                    <h5>Chat Reachability</h5>
                    <p class="text-muted">Reachability data unavailable.</p>
                </div>`;
        }

        const reasonLabels = {
            no_access_policy_field: 'Chunks have no access policy field.',
            no_access_policies: 'No access policy is set on any active chunk.',
            no_access_categories: 'No access category includes this knowledge\'s access policy.',
            no_agent_profiles: 'No AI Agent Profile has an enabled access category covering this knowledge.',
            no_assignments: 'Agent profile(s) found, but none are assigned to any user or channel route.',
            access_category_lookup_failed: 'Could not read access category configuration.',
            profile_lookup_failed: 'Could not read agent profile configuration.',
            ok: '',
        };

        if (!result.reachable) {
            const reason = reasonLabels[result.reason] || 'Reachability chain is incomplete.';
            return `
                <div class="nks-dashboard-card" style="width:100%; border-left: 3px solid #e74c3c;">
                    <h5>Chat Reachability</h5>
                    <p>
                        <span class="nks-badge nks-badge-warn">Not Reachable</span>
                    </p>
                    <p class="text-muted">${frappe.utils.escape_html(reason)}</p>
                    ${result.profiles && result.profiles.length ? `
                        <p class="text-muted" style="margin-top:8px;">
                            <b>${result.profiles.length}</b> profile(s) found in access chain but none have active assignments or routes.
                        </p>
                        <ul style="margin:6px 0 0; padding-left:18px; color:#666;">
                            ${result.profiles.map(p => `
                                <li>
                                    <a href="/app/nexus-ai-agent-profile/${encodeURIComponent(p.profile)}"
                                       target="_blank" style="color:#2490ef;">
                                        ${frappe.utils.escape_html(p.profile_label || p.profile)}
                                    </a>
                                </li>`).join('')}
                        </ul>
                    ` : ''}
                </div>`;
        }

        const profileRows = (result.profiles || []).map(p => {
            const lines = [];

            if (p.user_assignments && p.user_assignments.length) {
                lines.push(`<span style="color:#27ae60;">&#10003; User Assignment</span> — ${p.user_assignments.length} active user(s)`);
            }

            if (p.identity_routes && p.identity_routes.length) {
                const routeList = p.identity_routes.map(r => {
                    const parts = [r.channel, r.chat_category, r.open_to_all ? 'Public' : 'Restricted'].filter(Boolean);
                    return frappe.utils.escape_html(parts.join(' / '));
                }).join(', ');
                lines.push(`<span style="color:#2980b9;">&#10003; Category Identity Route</span> — ${routeList}`);
            }

            if (!lines.length) {
                lines.push(`<span class="text-muted">No active assignments or routes</span>`);
            }

            return `
                <tr>
                    <td style="padding:4px 8px; font-weight:500;">
                        <a href="/app/nexus-ai-agent-profile/${encodeURIComponent(p.profile)}"
                           target="_blank" style="color:#2490ef;">
                            ${frappe.utils.escape_html(p.profile_label || p.profile)}
                        </a>
                    </td>
                    <td style="padding:4px 8px;">${lines.join('<br>')}</td>
                </tr>`;
        }).join('');

        return `
            <div class="nks-dashboard-card" style="width:100%; border-left: 3px solid #27ae60;">
                <h5>Chat Reachability</h5>
                <p>
                    <span class="nks-badge nks-badge-good">Reachable via ${result.reachable_count} of ${result.total_profile_count} profile(s)</span>
                </p>
                <table style="width:100%; border-collapse:collapse; margin-top:8px; font-size:13px;">
                    <thead>
                        <tr style="border-bottom:1px solid #eee; color:#888; font-size:12px;">
                            <th style="padding:4px 8px; text-align:left;">AI Agent Profile</th>
                            <th style="padding:4px 8px; text-align:left;">Assigned Via</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${profileRows}
                    </tbody>
                </table>
            </div>`;
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
                        <p><b>Source:</b>
                            <a href="/app/nexus-knowledge-source/${encodeURIComponent(row.name)}"
                               target="_blank" style="color:#2490ef;">
                                ${frappe.utils.escape_html(row.source_title || row.name)}
                            </a>
                        </p>
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
                        <p><b>Publish State:</b> ${frappe.utils.escape_html(this.get_source_publish_state(row))}</p>
                    </div>

                    <div class="nks-dashboard-card">
                        <h5>Issues</h5>
                        ${missing_fields_html}
                    </div>
                    <div class="nks-dashboard-full-row">
                        ${this.get_source_context_summary_dashboard_html(row)}
                    </div>

                    ${row.readiness_status === 'needs_answer_approval' ? `
                    <div class="nks-dashboard-full-row">
                        <div class="nks-dashboard-card" style="width:100%; border-left: 4px solid #f59e0b;">
                            <h5 style="color: #92400e;">Answer Approval Required</h5>
                            <p style="color: #78350f; font-size: 12px; margin-bottom: 12px;">
                                Review and approve the generated questions and answers below before this source can proceed to Validation.
                            </p>
                            ${this.get_source_index_review_html(row)}
                        </div>
                    </div>
                    ` : ''}

                    <div class="nks-dashboard-full-row">
                        ${this.get_source_semantic_index_dashboard_html(row)}
                    </div>

                    <div class="nks-dashboard-full-row">
                         ${this.get_source_test_case_dashboard_html(row)}
                     </div>

                    <div class="nks-dashboard-full-row" id="nks-chat-reachability-panel">
                        <div class="nks-dashboard-card" style="width:100%;">
                            <h5>Chat Reachability</h5>
                            <p class="text-muted">Checking reachability chain...</p>
                        </div>
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
                        ${
                            row.is_published
                                ? `
                                    <b>Published note:</b>
                                    This source is now available for AI answers through active retrieval chunks.
                                    Public Q&A and Nexus answer flows will use the prepared chunks and embeddings from this source.
                                `
                                : `
                                    <b>Validation note:</b>
                                    Studio validation tests this source directly before publishing.
                                    After publishing, public Q&A and Source Quality tests use active retrieval chunks.
                                    A published source should have active retrieval chunks before it is available for Nexus answers.
                                `
                        }
                    </div>
                </div>

                <details>
                    <summary><b>Technical Status</b></summary>
                    <div class="nks-dashboard-technical">
                        <p><b>Source Status:</b> ${frappe.utils.escape_html(this.get_source_technical_value(row, technical_status, 'status'))}</p>
                        <p><b>Processing Status:</b> ${frappe.utils.escape_html(this.get_source_technical_value(row, technical_status, 'processing_status'))}</p>
                        <p><b>Embedding Status:</b> ${frappe.utils.escape_html(this.get_source_technical_value(row, technical_status, 'embedding_status'))}</p>
                        <p><b>Diagnostics Status:</b> ${frappe.utils.escape_html(this.get_source_technical_value(row, technical_status, 'diagnostics_status'))}</p>
                        <p><b>Processing Version:</b> ${frappe.utils.escape_html(String(this.get_source_technical_value(row, technical_status, 'processing_version', 0)))}</p>
                        <p><b>Chunk Count:</b> ${frappe.utils.escape_html(String(this.get_source_technical_value(row, technical_status, 'chunk_count', 0)))}</p>
                        <p><b>Active Chunk Count:</b> ${frappe.utils.escape_html(String(this.get_source_technical_value(row, technical_status, 'active_chunk_count', 0)))}</p>
                        <p><b>Retrieval Ready:</b> ${this.format_source_yes_no(this.get_source_technical_value(row, technical_status, 'retrieval_ready', 0))}</p>
                        ${(() => {
                            const ku = this.get_source_technical_value(row, technical_status, 'generated_knowledge_unit');
                            const val = ku && ku !== '-' && ku !== 'undefined' ? ku : '';
                            return val
                                ? `<p><b>Generated Knowledge Unit:</b>
                                     <a href="/app/nexus-knowledge-unit/${encodeURIComponent(val)}"
                                        target="_blank" style="color:#2490ef;">
                                       ${frappe.utils.escape_html(val)}
                                     </a></p>`
                                : `<p><b>Generated Knowledge Unit:</b> -</p>`;
                        })()}
                        ${(() => {
                            const cs = (row.context_summary && row.context_summary.name) || '';
                            return cs
                                ? `<p><b>Context Summary:</b>
                                     <a href="/app/nexus-knowledge-context-summary/${encodeURIComponent(cs)}"
                                        target="_blank" style="color:#2490ef;">
                                       ${frappe.utils.escape_html(cs)}
                                     </a></p>`
                                : `<p><b>Context Summary:</b> -</p>`;
                        })()}
                        <p><b>Semantic Index Entries:</b> ${frappe.utils.escape_html(String(row.semantic_index_count || 0))}</p>
                        <p><b>Last Processed On:</b> ${frappe.utils.escape_html(this.get_source_technical_value(row, technical_status, 'last_processed_on'))}</p>
                        <p><b>Validation Status:</b> ${frappe.utils.escape_html(this.get_source_technical_value(row, technical_status, 'validation_status'))}</p>
                        <p><b>Last Error:</b> ${frappe.utils.escape_html(this.get_source_technical_value(row, technical_status, 'last_error'))}</p>
                    </div>
                </details>
            </div>
        `);

        dialog.show();

        frappe.call({
            method: this.api.get_chat_reachability,
            args: { source_name: name },
            callback: (r) => {
                const panel = dialog.$wrapper.find('#nks-chat-reachability-panel');
                if (!panel.length) return;
                const result = (r && r.message) ? r.message : null;
                panel.html(this.get_source_chat_reachability_html(result));
            },
            error: () => {
                const panel = dialog.$wrapper.find('#nks-chat-reachability-panel');
                if (panel.length) {
                    panel.html(`
                        <div class="nks-dashboard-card" style="width:100%;">
                            <h5>Chat Reachability</h5>
                            <p class="text-muted">Could not load reachability data.</p>
                        </div>
                    `);
                }
            }
        });

        dialog.$wrapper.find('.nks-dashboard-review-source-btn').on('click', () => {
            frappe.set_route('Form', 'Nexus Knowledge Source', row.name);
            dialog.hide();
        });

        dialog.$wrapper.find('.nks-dashboard-refresh-source-btn').on('click', () => {
            this.load_sources();
            this.load_source_summary();
            this.load_units();

            frappe.show_alert({
                message: 'Source status refreshed.',
                indicator: 'blue'
            });

            dialog.hide();
        });

        dialog.$wrapper.find('.nks-dashboard-review-answers-scroll-btn').on('click', () => {
            dialog.hide();
            const $details = this.body.find(`.nks-source-item[data-source="${row.name}"]`);
            if ($details.length) {
                $details.attr('open', true);
                $details[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });

        dialog.$wrapper.find('.nks-dashboard-approve-all-answers-btn').on('click', () => {
            dialog.hide();
            this.bulk_approve_source_answers(row.name);
        });

        dialog.$wrapper.find('.nks-dashboard-validate-questions-llm-btn').on('click', () => {
            dialog.hide();
            this.validate_source_questions_with_llm(row.name);
        });

        dialog.$wrapper.on('click', '.nks-index-answer-review-btn', (e) => {
            const $btn = $(e.currentTarget);
            this.review_index_answer(
                $btn.data('name'),
                $btn.data('action'),
                $btn
            );
        });

        dialog.$wrapper.find('.nks-dashboard-process-source-btn').on('click', () => {
            this.process_source_from_dashboard(row.name, dialog);
        });

        dialog.$wrapper.find('.nks-dashboard-reset-source-btn').on('click', () => {
            this.reset_source_from_dashboard(row.name, dialog);
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
        dialog.$wrapper.find('.nks-dashboard-generate-test-cases-btn').on('click', () => {
            this.generate_test_cases_from_source_dashboard(row.name);
        });
        dialog.$wrapper.find('.nks-open-source-test-cases-btn').on('click', () => {
            dialog.hide();

            frappe.route_options = {
                knowledge_source: row.name
            };

            frappe.set_route('List', 'Nexus Knowledge Test Case');
        });

        dialog.$wrapper.find('.nks-review-source-test-cases-btn').on('click', () => {
            dialog.hide();

            frappe.route_options = {
                knowledge_source: row.name,
                status: 'Draft'
            };

            frappe.set_route('List', 'Nexus Knowledge Test Case');
        });

        dialog.$wrapper.find('.nks-open-source-test-runs-btn').on('click', () => {
            dialog.hide();

            frappe.route_options = {
                knowledge_source: row.name
            };

            frappe.set_route('List', 'Nexus Knowledge Test Run');
        });

        dialog.$wrapper.find('.nks-run-source-test-cases-btn').on('click', () => {
            this.run_source_test_cases_from_dashboard(row.name, dialog);
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

        if (this.is_source_prepared(row)) {
            buttons.push('<span class="nks-badge nks-badge-processed">Processed</span>');
        }

        if (this.is_source_validated(row)) {
            buttons.push('<span class="nks-badge nks-badge-validated">Validated</span>');
        }

        if (this.can_show_process_source_action(row)) {
            buttons.push(`
                <button class="btn btn-sm btn-primary nks-dashboard-process-source-btn">
                    Process Source
                </button>
            `);
        }

        if (row.readiness_status === 'needs_answer_approval') {
            buttons.push(`
                <button class="btn btn-sm btn-primary nks-dashboard-validate-questions-llm-btn">
                    Validate with AI
                </button>
                <button class="btn btn-sm btn-warning nks-dashboard-review-answers-scroll-btn">
                    Review Questions
                </button>
                <button class="btn btn-sm btn-success nks-dashboard-approve-all-answers-btn">
                    Approve All
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

        if (this.can_show_generate_test_cases_action(row)) {
            buttons.push(`
                <button class="btn btn-sm btn-default nks-dashboard-generate-test-cases-btn" data-name="${frappe.utils.escape_html(row.name)}">
                    Generate Validation Tests
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

        buttons.push(`
            <button class="btn btn-sm btn-danger nks-dashboard-reset-source-btn">
                Reset Generated Data
            </button>
        `);

        return buttons.join('');
    }
    can_show_generate_test_cases_action(row) {
    const status = String(row.status || '').toLowerCase();
    const readiness_status = String(row.readiness_status || '').toLowerCase();

    return Boolean(
        row &&
        row.name &&
        (
            row.is_published ||
            row.published ||
            status === 'published' ||
            readiness_status === 'published'
        )
    );
}

generate_test_cases_from_source_dashboard(name) {
    if (!name) {
        frappe.msgprint('Knowledge Source name is missing.');
        return;
    }

    const row = (this.sources || []).find((item) => item.name === name);

    if (!row) {
        frappe.msgprint('Source details are not available. Please refresh and try again.');
        return;
    }

    if (!this.can_show_generate_test_cases_action(row)) {
        frappe.msgprint({
            title: 'Source Not Published',
            indicator: 'orange',
            message: 'Validation tests can be generated only after the Knowledge Source is published.'
        });
        return;
    }

    const dialog = new frappe.ui.Dialog({
        title: 'Generate Validation Tests',
        size: 'large',
        fields: [
            {
                fieldname: 'source_info_html',
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
                            Published Source Validation
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

                        <p style="margin: 10px 0 0; color: #526887; font-size: 12px; line-height: 1.45; font-weight: 700;">
                            Nexus will generate draft validation tests from the current retrieval index,
                            especially active Possible Questions linked to approved chunks.
                            Review them before using them as approved validation scenarios.
                        </p>
                    </div>
                `
            },
            {
                fieldname: 'test_count',
                fieldtype: 'Int',
                label: 'Number of Validation Tests',
                default: 5,
                reqd: 1,
                description: 'Recommended: 5 to 10 validation tests per published source.'
            },
            {
                fieldname: 'use_case',
                fieldtype: 'Select',
                label: 'Primary Use Case',
                options: [
                    'Q&A',
                    'Chat',
                    'Live',
                    'Internal'
                ].join('\n'),
                default: 'Q&A',
                reqd: 1
            },
            {
                fieldname: 'include_boundary_tests',
                fieldtype: 'Check',
                label: 'Include fallback / boundary validation tests',
                default: 0,
                description: 'Keep off unless you are intentionally validating safe fallback behaviour.'
            },
            {
                fieldname: 'include_followup_tests',
                fieldtype: 'Check',
                label: 'Include follow-up style questions',
                default: 0
            },
            {
                fieldname: 'auto_enable',
                fieldtype: 'Check',
                label: 'Enable generated validation tests immediately',
                default: 0,
                description: 'Recommended to keep disabled until reviewed.'
            }
        ],
        primary_action_label: 'Generate Validation Tests',
        primary_action: (values) => {
            const test_count = cint(values.test_count || 0);

            if (!test_count || test_count < 1) {
                frappe.msgprint('Please enter a valid number of validation tests.');
                return;
            }

            this.generate_source_test_cases(name, values, dialog);
        }
    });

    dialog.show();
}

generate_source_test_cases(name, values, dialog) {
    frappe.call({
        method: this.api.generate_source_test_cases,
        args: {
            name: name,
            test_count: cint(values.test_count || 5),
            use_case: values.use_case || 'Q&A',
            include_boundary_tests: values.include_boundary_tests ? 1 : 0,
            include_followup_tests: values.include_followup_tests ? 1 : 0,
            auto_enable: values.auto_enable ? 1 : 0,
            replace_existing: 1
        },
        freeze: true,
        freeze_message: 'Generating validation tests...',
        callback: (r) => {
            const result = r.message || {};

            if (!result.success) {
                frappe.msgprint({
                    title: 'Validation Test Generation Failed',
                    indicator: 'orange',
                    message: frappe.utils.escape_html(
                        result.message || 'Unable to generate validation tests.'
                    )
                });
                return;
            }

            if (dialog) {
                dialog.hide();
            }

            const created = result.created || [];
            const skipped = result.skipped || [];
            const replaced_count = result.replaced_count || result.archived_count || 0;

            frappe.msgprint({
                title: 'Validation Tests Generated',
                indicator: 'green',
                message: `
                    <div class="nks-readiness-dialog">
                        <p>${frappe.utils.escape_html(result.message || 'Validation tests generated successfully.')}</p>

                        <p><b>Created:</b> ${frappe.utils.escape_html(String(created.length || result.created_count || 0))}</p>
                        <p><b>Skipped:</b> ${frappe.utils.escape_html(String(skipped.length || result.skipped_count || 0))}</p>
                        <p><b>Replaced older generated validation tests:</b> ${frappe.utils.escape_html(String(replaced_count))}</p>

                        ${
                            created.length
                                ? `
                                    <p><b>Generated Validation Tests:</b></p>
                                    <ul style="margin: 8px 0 0; padding-left: 18px;">
                                        ${created.map((item) => {
                                            const label = item.title || item.test_title || item.name || item;
                                            return `<li>${frappe.utils.escape_html(label)}</li>`;
                                        }).join('')}
                                    </ul>
                                `
                                : ''
                        }

                        <div style="
                            margin-top: 12px;
                            padding: 10px 12px;
                            border-radius: 12px;
                            background: #eef6ff;
                            border: 1px solid rgba(33, 119, 255, 0.22);
                            color: #0b3c91;
                            font-size: 12px;
                            font-weight: 700;
                        ">
                            Review the generated draft validation tests before using them as approved validation scenarios.
                        </div>

                        <div style="margin-top: 12px;">
                            <a class="btn btn-sm btn-primary" href="/app/nexus-knowledge-test-case">
                                Open Validation Tests
                            </a>
                            <a class="btn btn-sm btn-default" href="/app/nexus-knowledge-test-run" style="margin-left: 6px;">
                                Open Validation Runs
                            </a>
                        </div>
                    </div>
                `
            });

            this.load_sources();
            this.load_source_summary();
        },
        error: () => {
            frappe.msgprint({
                title: 'Validation Test Generation Failed',
                indicator: 'red',
                message: 'Unable to generate validation tests. Please check the server error log.'
            });
        }
    });
}

run_source_test_cases_from_dashboard(sourceName, dialog) {
    if (!sourceName) {
        frappe.msgprint({
            title: 'Run Validation Tests',
            indicator: 'red',
            message: 'Knowledge Source is required.'
        });
        return;
    }

    const row = (this.sources || []).find((item) => item.name === sourceName);

    if (!row) {
        frappe.msgprint({
            title: 'Run Validation Tests',
            indicator: 'orange',
            message: 'Source details are not available. Please refresh and try again.'
        });
        return;
    }

    frappe.confirm(
        `Run all generated validation tests for ${frappe.utils.escape_html(row.source_title || row.name)}?`,
        () => {
            frappe.call({
                method: this.api.run_source_test_cases,
                args: {
                    source_name: sourceName,
                    include_draft: 1,
                    only_enabled: 0,
                    limit: 50
                },
                freeze: true,
                freeze_message: 'Running validation tests...',
                callback: (r) => {
                    const result = r.message || {};

                    if (!result.success) {
                        frappe.msgprint({
                            title: 'Validation Run Failed',
                            indicator: 'red',
                            message: frappe.utils.escape_html(
                                result.message || 'Unable to run validation tests.'
                            )
                        });
                        return;
                    }

                    const total = cint(result.total || 0);
                    const passed = cint(result.passed || 0);
                    const failed = cint(result.failed || 0);
                    const warning = cint(result.warning || result.warnings || 0);
                    const error = cint(result.error || result.errors || 0);

                    const indicator = error || failed
                        ? 'red'
                        : warning
                            ? 'orange'
                            : 'green';

                    if (dialog) {
                        dialog.hide();
                    }

                    frappe.msgprint({
                        title: 'Validation Run Completed',
                        indicator: indicator,
                        message: `
                            <div class="nks-test-run-result">
                                <p style="margin-top: 0;">
                                    ${frappe.utils.escape_html(result.message || 'Validation tests executed.')}
                                </p>

                                <div class="nks-test-run-result-grid">
                                    <div>
                                        <strong>${total}</strong>
                                        <span>Total</span>
                                    </div>
                                    <div>
                                        <strong>${passed}</strong>
                                        <span>Passed</span>
                                    </div>
                                    <div>
                                        <strong>${failed}</strong>
                                        <span>Failed</span>
                                    </div>
                                    <div>
                                        <strong>${warning}</strong>
                                        <span>Warning</span>
                                    </div>
                                    <div>
                                        <strong>${error}</strong>
                                        <span>Error</span>
                                    </div>
                                </div>

                                <div class="nks-test-run-result-actions">
                                    <button class="btn btn-sm btn-primary nks-after-run-open-runs">
                                        Open Validation Runs
                                    </button>

                                    <button class="btn btn-sm btn-default nks-after-run-open-issues">
                                        View Failed / Warning
                                    </button>
                                </div>
                            </div>
                        `
                    });

                    setTimeout(() => {
                        $('.nks-after-run-open-runs').off('click').on('click', () => {
                            frappe.route_options = {
                                knowledge_source: sourceName
                            };

                            frappe.set_route('List', 'Nexus Knowledge Test Run');
                        });

                        $('.nks-after-run-open-issues').off('click').on('click', () => {
                            frappe.route_options = {
                                knowledge_source: sourceName,
                                run_status: ['in', ['Failed', 'Warning', 'Error']]
                            };

                            frappe.set_route('List', 'Nexus Knowledge Test Run');
                        });
                    }, 300);

                    this.load_sources();
                    this.load_source_summary();
                },
                error: (err) => {
                    console.error('Run Validation Tests Error:', err);

                    frappe.msgprint({
                        title: 'Run Validation Tests Error',
                        indicator: 'red',
                        message: 'Could not run validation tests. Please check the server logs.'
                    });
                }
            });
        }
    );
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
   
    reset_source_from_dashboard(name, dialog) {
        if (!name) {
            frappe.msgprint('Knowledge Source name is missing.');
            return;
        }

        frappe.confirm(
            `Permanently remove all generated units, chunks, semantic indexes, ` +
            `correlations, summaries, validation tests, and test runs for <b>${frappe.utils.escape_html(name)}</b>?<br><br>` +
            `The source document, content, and classification will be preserved as a Draft.`,
            () => {
                frappe.call({
                    method: this.api.reset_source,
                    args: {
                        name,
                        confirm: 'RESET_KNOWLEDGE_SOURCE'
                    },
                    freeze: true,
                    freeze_message: 'Resetting generated knowledge data...',
                    callback: (r) => {
                        const result = r.message || {};
                        if (!result.success) {
                            frappe.msgprint({
                                title: 'Reset Failed',
                                indicator: 'red',
                                message: frappe.utils.escape_html(result.message || 'Knowledge Source reset failed.')
                            });
                            return;
                        }

                        if (dialog) {
                            dialog.hide();
                        }

                        this.load_sources();
                        this.load_source_summary();
                        this.load_units();

                        const deleted = result.deleted || {};
                        const deletedTotal = Object.values(deleted).reduce(
                            (total, value) => total + Number(value || 0),
                            0
                        );

                        frappe.msgprint({
                            title: 'Knowledge Source Reset',
                            indicator: 'green',
                            message: `${frappe.utils.escape_html(name)} is ready for a fresh process run. ` +
                                `${deletedTotal} generated record(s) were removed.`
                        });
                    },
                    error: () => {
                        frappe.msgprint({
                            title: 'Reset Failed',
                            indicator: 'red',
                            message: 'Knowledge Source reset failed. No partial reset was committed.'
                        });
                    }
                });
            }
        );
    }

    process_source_from_dashboard(name, dialog) {
        if (!name) {
            frappe.msgprint('Knowledge Source name is missing.');
            return;
        }

        frappe.confirm(
            'This will extract text and create or refresh the generated Knowledge Unit / Chunks for this source. If this source was already validated, you may need to validate it again before publishing. Continue?',
            () => {
                frappe.call({
                    method: this.api.process_source,
                    args: {
                        source_name: name
                    },
                    freeze: true,
                    freeze_message: 'Processing knowledge source...',
                    callback: (r) => {
                        const result = r.message || {};

                        if (!result || result.status !== 'success') {
                            frappe.msgprint({
                                title: 'Processing Failed',
                                indicator: 'red',
                                message: result.error
                                    ? frappe.utils.escape_html(result.error)
                                    : 'Knowledge source processing failed.'
                            });

                            this.load_sources();
                            this.load_source_summary();
                            this.load_units();

                            return;
                        }

                        if (dialog) {
                            dialog.hide();
                        }

                        frappe.msgprint({
                            title: 'Processed',
                            indicator: 'green',
                            message: `
                                <div style="line-height:1.8;">
                                    <div><b>Knowledge Unit:</b> ${frappe.utils.escape_html(result.knowledge_unit || result.generated_knowledge_unit || '-')}</div>
                                    <div><b>Chunks Created:</b> ${frappe.utils.escape_html(String(result.chunk_count || 0))}</div>
                                    <div><b>Processing Version:</b> ${frappe.utils.escape_html(String(result.processing_version || 0))}</div>
                                    <div><b>Diagnostics:</b> ${frappe.utils.escape_html(result.diagnostics_status || '-')}</div>
                                    <div><b>Retrieval Ready:</b> ${result.retrieval_ready ? 'Yes' : 'No'}</div>
                                </div>
                            `
                        });

                        this.load_sources();
                        this.load_source_summary();
                        this.load_units();
                    },
                    error: () => {
                        frappe.msgprint({
                            title: 'Processing Failed',
                            indicator: 'red',
                            message: 'Knowledge source processing failed. Please check the Error Log in the Knowledge Source.'
                        });

                        this.load_sources();
                        this.load_source_summary();
                        this.load_units();
                    }
                });
            }
        );
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
