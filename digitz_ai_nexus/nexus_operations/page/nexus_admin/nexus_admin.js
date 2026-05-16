let nexus_admin_snapshot = null;
let nexus_selected_ecosystem = null;

frappe.pages['nexus-admin'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Nexus Administration',
        single_column: true
    });

    $(page.body).html(`
        <div class="nexus-admin-wrap">

            <div class="nexus-admin-hero">
                <div>
                    <div class="nexus-admin-badge">DIGITZ AI Nexus</div>
                    <h2>Nexus Administration</h2>
                    <p>
                        Configure tenant operating profiles through the model:
                        <b>Tenant → Ecosystem → Defaults</b>. A tenant can have multiple ecosystems such as
                        Production, Sandbox, Synthetic Validation, and Internal Platform.
                    </p>
                </div>

                <div class="nexus-admin-hero-actions">
                    <button class="btn btn-default" id="nexus_admin_help">
                        Help / Field Guide
                    </button>

                    <button class="btn btn-default" id="nexus_admin_refresh">
                        Refresh Snapshot
                    </button>

                    <button class="btn btn-primary" id="nexus_admin_open_onboarding">
                        Onboard Tenant
                    </button>
                </div>
            </div>

            <div id="nexus_admin_alert_holder"></div>

            <div class="nexus-admin-grid nexus-admin-grid-3">
                <div class="nexus-admin-card">
                    <div class="nexus-admin-card-title">My Default Context</div>
                    <div id="nexus_active_context_card" class="nexus-admin-card-body">
                        Loading...
                    </div>
                </div>

                <div class="nexus-admin-card">
                    <div class="nexus-admin-card-title">Resolved Runtime Context</div>
                    <div id="nexus_resolved_context_card" class="nexus-admin-card-body">
                        Loading...
                    </div>
                </div>

                <div class="nexus-admin-card">
                    <div class="nexus-admin-card-title">Administration Readiness</div>
                    <div id="nexus_readiness_card" class="nexus-admin-card-body">
                        Loading...
                    </div>
                </div>
            </div>

            <div class="nexus-admin-card">
                <div class="nexus-admin-section-head">
                    <div>
                        <div class="nexus-admin-card-title">Set My Default Context</div>
                        <p>
                            Select your working tenant, active ecosystem, business unit, project, and channel.
                            This is user-specific and does not change other users' defaults.
                        </p>
                    </div>

                    <button class="btn btn-primary btn-sm" id="nexus_save_active_context">
                        Save My Default Context
                    </button>
                </div>

                <div class="nexus-admin-form-grid nexus-admin-form-grid-5">
                    <div>
                        <label>My Default Tenant</label>
                        <select id="nexus_active_tenant" class="form-control"></select>
                    </div>

                    <div>
                        <label>My Active Ecosystem</label>
                        <select id="nexus_active_ecosystem" class="form-control"></select>
                    </div>

                    <div>
                        <label>My Default Business Unit</label>
                        <select id="nexus_active_business_unit" class="form-control"></select>
                    </div>

                    <div>
                        <label>My Default Project</label>
                        <select id="nexus_active_project" class="form-control"></select>
                    </div>

                    <div>
                        <label>My Default Channel</label>
                        <select id="nexus_active_channel" class="form-control"></select>
                    </div>
                </div>
            </div>

            <div class="nexus-admin-card">
                <div class="nexus-admin-section-head">
                    <div>
                        <div class="nexus-admin-card-title">Configured Ecosystems</div>
                        <p>
                            Ecosystems are operating profiles under the selected tenant. Defaults belong to the selected ecosystem,
                            not directly to the tenant.
                        </p>
                    </div>

                    <button class="btn btn-primary btn-sm" id="nexus_add_ecosystem">
                        Add Ecosystem
                    </button>
                </div>

                <div id="nexus_ecosystem_cards" class="nexus-ecosystem-card-grid">
                    Loading...
                </div>
            </div>

            <div class="nexus-admin-card">
                <div class="nexus-admin-section-head">
                    <div>
                        <div class="nexus-admin-card-title">Selected Ecosystem Defaults</div>
                        <p>
                            Configure defaults for the selected ecosystem profile. Runtime payload values can still override these defaults.
                        </p>
                    </div>

                    <button class="btn btn-primary btn-sm" id="nexus_save_ecosystem_defaults">
                        Save Selected Ecosystem Defaults
                    </button>
                </div>

                <div class="nexus-admin-form-grid nexus-admin-form-grid-4">
                    <div>
                        <label>Ecosystem Name</label>
                        <input id="nexus_ecosystem_name" class="form-control" placeholder="Example: DIGITZ ERP Production">
                    </div>

                    <div>
                        <label>Ecosystem Type</label>
                        <select id="nexus_ecosystem_type" class="form-control">
                            <option value="">Not Set</option>
                            <option value="Production">Production</option>
                            <option value="Sandbox">Sandbox</option>
                            <option value="Synthetic Validation">Synthetic Validation</option>
                            <option value="Internal Platform">Internal Platform</option>
                        </select>
                    </div>

                    <div>
                        <label>Enabled</label>
                        <select id="nexus_ecosystem_enabled" class="form-control">
                            <option value="1">Enabled</option>
                            <option value="0">Disabled</option>
                        </select>
                    </div>

                    <div>
                        <label>Tenant Default Ecosystem</label>
                        <select id="nexus_ecosystem_is_default" class="form-control">
                            <option value="0">No</option>
                            <option value="1">Yes</option>
                        </select>
                    </div>

                    <div>
                        <label>Default Business Unit</label>
                        <input id="nexus_default_business_unit" class="form-control">
                    </div>

                    <div>
                        <label>Default Project</label>
                        <input id="nexus_default_project" class="form-control">
                    </div>

                    <div>
                        <label>Default Public Context</label>
                        <input id="nexus_default_public_context" class="form-control">
                    </div>

                    <div>
                        <label>Default Top K</label>
                        <input id="nexus_default_top_k" class="form-control" type="number" min="1" value="5">
                    </div>

                    <div>
                        <label>Q&A Enabled</label>
                        <select id="nexus_qa_enabled" class="form-control">
                            <option value="1">Enabled</option>
                            <option value="0">Disabled</option>
                        </select>
                    </div>

                    <div>
                        <label>Default Q&A Channel</label>
                        <select id="nexus_default_qa_channel" class="form-control"></select>
                    </div>

                    <div>
                        <label>Source Citation Required</label>
                        <select id="nexus_source_citation_required" class="form-control">
                            <option value="1">Required</option>
                            <option value="0">Not Required</option>
                        </select>
                    </div>

                    <div>
                        <label>Require Approved Knowledge</label>
                        <select id="nexus_require_approved_knowledge" class="form-control">
                            <option value="1">Required</option>
                            <option value="0">Not Required</option>
                        </select>
                    </div>

                    <div>
                        <label>Live Chat Enabled</label>
                        <select id="nexus_live_chat_enabled" class="form-control">
                            <option value="1">Enabled</option>
                            <option value="0">Disabled</option>
                        </select>
                    </div>

                    <div>
                        <label>Default Chat Channel</label>
                        <select id="nexus_default_chat_channel" class="form-control"></select>
                    </div>

                    <div>
                        <label>Default Live Channel</label>
                        <select id="nexus_default_live_channel" class="form-control"></select>
                    </div>

                    <div>
                        <label>Default Public Agent</label>
                        <input id="nexus_default_public_agent" class="form-control" placeholder="Agent code or name">
                    </div>

                    <div>
                        <label>Widget Enabled</label>
                        <select id="nexus_widget_enabled" class="form-control">
                            <option value="1">Enabled</option>
                            <option value="0">Disabled</option>
                        </select>
                    </div>

                    <div>
                        <label>Default Widget Title</label>
                        <input id="nexus_widget_title" class="form-control">
                    </div>

                    <div>
                        <label>Default Widget Welcome Message</label>
                        <input id="nexus_widget_welcome_message" class="form-control">
                    </div>

                    <div>
                        <label>Default Widget Brand Color</label>
                        <input id="nexus_widget_brand_color" class="form-control" placeholder="#214dbb">
                    </div>
                </div>

                <div class="nexus-admin-question-box">
                    <label>Q&A Fallback Message</label>
                    <textarea id="nexus_qa_fallback_message" class="form-control" rows="3"></textarea>
                </div>
            </div>

        </div>
    `);

    inject_nexus_admin_css();
    bind_nexus_admin_events();
    load_nexus_admin_snapshot();
};


function bind_nexus_admin_events() {
    $('#nexus_admin_help').on('click', function() {
        open_nexus_administration_help();
    });

    $('#nexus_admin_refresh').on('click', function() {
        load_nexus_admin_snapshot();
    });

    $('#nexus_admin_open_onboarding').on('click', function() {
        open_tenant_onboarding_dialog();
    });

    $('#nexus_save_active_context').on('click', function() {
        save_active_user_context();
    });

    $('#nexus_save_ecosystem_defaults').on('click', function() {
        save_ecosystem_defaults();
    });

    $('#nexus_add_ecosystem').on('click', function() {
        open_add_ecosystem_dialog();
    });

    $('#nexus_active_tenant').on('change', function() {
        render_ecosystem_cards();
        populate_active_ecosystem_selector();
    });

    $('#nexus_active_ecosystem').on('change', function() {
        const selected = $('#nexus_active_ecosystem').val();
        if (selected) {
            select_ecosystem(selected, false);
        }
    });
}


function load_nexus_admin_snapshot() {
    set_loading_state();

    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.get_administration_snapshot',
        callback: function(r) {
            nexus_admin_snapshot = r.message || {};
            normalize_snapshot_for_multiple_ecosystems();
            render_nexus_admin_snapshot(nexus_admin_snapshot);
        },
        error: function(err) {
            render_admin_alert(
                'Failed to load Nexus Administration snapshot. ' + frappe.utils.escape_html(err.message || ''),
                'red'
            );
        }
    });
}


function normalize_snapshot_for_multiple_ecosystems() {
    nexus_admin_snapshot = nexus_admin_snapshot || {};

    if (!Array.isArray(nexus_admin_snapshot.ecosystems)) {
        nexus_admin_snapshot.ecosystems = [];
    }

    if (nexus_admin_snapshot.ecosystem && !nexus_admin_snapshot.ecosystems.length) {
        nexus_admin_snapshot.ecosystems.push(nexus_admin_snapshot.ecosystem);
    }

    const active_ecosystem =
        get_snapshot_value('user_context.active_ecosystem')
        || get_snapshot_value('resolved_context.ecosystem')
        || get_snapshot_value('ecosystem.name')
        || get_snapshot_value('ecosystem.ecosystem_name');

    if (!nexus_selected_ecosystem && active_ecosystem) {
        nexus_selected_ecosystem = active_ecosystem;
    }

    if (!nexus_selected_ecosystem && nexus_admin_snapshot.ecosystems.length) {
        nexus_selected_ecosystem =
            nexus_admin_snapshot.ecosystems.find(e => cint(e.is_default || 0))?.name
            || nexus_admin_snapshot.ecosystems[0].name
            || nexus_admin_snapshot.ecosystems[0].ecosystem_name;
    }
}


function set_loading_state() {
    $('#nexus_active_context_card').html('Loading...');
    $('#nexus_resolved_context_card').html('Loading...');
    $('#nexus_readiness_card').html('Loading...');
    $('#nexus_ecosystem_cards').html('Loading...');
}


function render_nexus_admin_snapshot(snapshot) {
    snapshot = snapshot || {};

    render_admin_alert('', '');
    populate_selector_options(snapshot.selectors || {});
    render_active_context(snapshot.user_context);
    render_resolved_context(snapshot.resolved_context);
    render_readiness(snapshot.readiness);
    populate_active_ecosystem_selector();
    render_ecosystem_cards();
    populate_ecosystem_defaults(get_selected_ecosystem_doc());
}


function populate_selector_options(selectors) {
    selectors = selectors || {};

    populate_select(
        '#nexus_active_tenant',
        selectors.tenants || [],
        'name',
        function(row) {
            return row.tenant_name || row.tenant_code || row.name;
        },
        get_snapshot_value('user_context.active_tenant') || get_snapshot_value('resolved_context.tenant')
    );

    populate_select(
        '#nexus_active_business_unit',
        selectors.business_units || [],
        'name',
        function(row) {
            return row.business_unit_name || row.name;
        },
        get_snapshot_value('user_context.active_business_unit') || get_snapshot_value('resolved_context.business_unit'),
        true
    );

    populate_select(
        '#nexus_active_project',
        selectors.projects || [],
        'name',
        function(row) {
            return row.project_name || row.project || row.name;
        },
        get_snapshot_value('user_context.active_project') || get_snapshot_value('resolved_context.project'),
        true
    );

    populate_select(
        '#nexus_active_channel',
        selectors.channels || [],
        'name',
        function(row) {
            return row.channel_name || row.channel_code || row.name;
        },
        get_snapshot_value('user_context.active_channel') || get_snapshot_value('resolved_context.channel'),
        true
    );

    populate_select(
        '#nexus_default_qa_channel',
        selectors.channels || [],
        'name',
        function(row) {
            return row.channel_name || row.channel_code || row.name;
        },
        null,
        true
    );

    populate_select(
        '#nexus_default_chat_channel',
        selectors.channels || [],
        'name',
        function(row) {
            return row.channel_name || row.channel_code || row.name;
        },
        null,
        true
    );

    populate_select(
        '#nexus_default_live_channel',
        selectors.channels || [],
        'name',
        function(row) {
            return row.channel_name || row.channel_code || row.name;
        },
        null,
        true
    );
}


function populate_active_ecosystem_selector() {
    const ecosystems = get_ecosystems_for_active_tenant();

    const rows = ecosystems.map(e => {
        return {
            name: e.name || e.ecosystem_name,
            label: e.ecosystem_name || e.name
        };
    });

    populate_select(
        '#nexus_active_ecosystem',
        rows,
        'name',
        function(row) {
            return row.label || row.name;
        },
        nexus_selected_ecosystem
            || get_snapshot_value('user_context.active_ecosystem')
            || get_snapshot_value('resolved_context.ecosystem'),
        true
    );
}


function populate_select(selector, rows, value_key, label_fn, selected_value, allow_blank=false) {
    const options = [];

    if (allow_blank) {
        options.push(`<option value="">Not Set</option>`);
    }

    (rows || []).forEach(row => {
        const value = row[value_key] || row.name || '';
        const label = label_fn ? label_fn(row) : value;

        options.push(`
            <option value="${frappe.utils.escape_html(value)}">
                ${frappe.utils.escape_html(label || value)}
            </option>
        `);
    });

    $(selector).html(options.join(''));

    if (selected_value) {
        $(selector).val(selected_value);
    }
}


function get_active_tenant() {
    return $('#nexus_active_tenant').val()
        || get_snapshot_value('user_context.active_tenant')
        || get_snapshot_value('resolved_context.tenant');
}


function get_ecosystems_for_active_tenant() {
    const tenant = get_active_tenant();

    return (nexus_admin_snapshot?.ecosystems || []).filter(e => {
        if (!tenant) return true;
        return !e.tenant || e.tenant === tenant;
    });
}


function get_selected_ecosystem_doc() {
    const ecosystems = get_ecosystems_for_active_tenant();

    if (!ecosystems.length) {
        return null;
    }

    if (nexus_selected_ecosystem) {
        const found = ecosystems.find(e => {
            return e.name === nexus_selected_ecosystem
                || e.ecosystem_name === nexus_selected_ecosystem;
        });

        if (found) return found;
    }

    return ecosystems.find(e => cint(e.is_default || 0)) || ecosystems[0];
}


function select_ecosystem(ecosystem_name, refresh=true) {
    nexus_selected_ecosystem = ecosystem_name;
    $('#nexus_active_ecosystem').val(ecosystem_name);

    const doc = get_selected_ecosystem_doc();
    populate_ecosystem_defaults(doc);
    render_ecosystem_cards();

    if (refresh) {
        frappe.show_alert({
            message: 'Selected ecosystem changed for this page.',
            indicator: 'blue'
        });
    }
}


function render_active_context(context) {
    if (!context) {
        $('#nexus_active_context_card').html(`
            <div class="nexus-empty-state">
                No active user context found. Select tenant details and save your default context.
            </div>
        `);
        return;
    }

    $('#nexus_active_context_card').html(`
        ${render_kv('User', context.user)}
        ${render_kv('My Default Tenant', context.active_tenant)}
        ${render_kv('My Active Ecosystem', context.active_ecosystem || '-')}
        ${render_kv('My Default Business Unit', context.active_business_unit)}
        ${render_kv('My Default Project', context.active_project || '-')}
        ${render_kv('My Default Channel', context.active_channel || '-')}
        ${render_kv('Last Used On', context.last_used_on || '-')}
    `);
}


function render_resolved_context(context) {
    context = context || {};

    $('#nexus_resolved_context_card').html(`
        ${render_kv('Tenant', context.tenant || '-')}
        ${render_kv('Ecosystem', context.ecosystem || '-')}
        ${render_kv('Business Unit', context.business_unit || '-')}
        ${render_kv('Project', context.project || '-')}
        ${render_kv('Channel', context.channel || '-')}
        ${render_kv('Context', context.context || '-')}
        ${render_kv('Default Top K', context.default_top_k || '-')}
    `);
}


function render_readiness(readiness) {
    readiness = readiness || {};

    $('#nexus_readiness_card').html(`
        <div class="nexus-readiness-grid">
            ${render_readiness_pill('Q&A Ready', readiness.qa_ready)}
            ${render_readiness_pill('Live Ready', readiness.live_ready)}
            ${render_readiness_pill('Testing Ready', readiness.testing_ready)}
            ${render_readiness_pill('Production Candidate', readiness.production_ready)}
        </div>

        <div class="nexus-readiness-counts">
            ${render_kv('Knowledge Units', readiness.knowledge_count || 0)}
            ${render_kv('Knowledge Chunks', readiness.chunk_count || 0)}
            ${render_kv('Channels', readiness.channel_count || 0)}
            ${render_kv('AI Agents', readiness.ai_agent_count || 0)}
            ${render_kv('Activation Status', readiness.activation_status || '-')}
            ${render_kv('Certification Status', readiness.certification_status || '-')}
        </div>
    `);
}


function render_ecosystem_cards() {
    const ecosystems = get_ecosystems_for_active_tenant();

    if (!ecosystems.length) {
        $('#nexus_ecosystem_cards').html(`
            <div class="nexus-empty-state">
                No ecosystem profiles found for the selected tenant. Use Add Ecosystem to create one.
            </div>
        `);
        populate_ecosystem_defaults(null);
        return;
    }

    const active_ecosystem =
        get_snapshot_value('user_context.active_ecosystem')
        || get_snapshot_value('resolved_context.ecosystem');

    const html = ecosystems.map(e => {
        const name = e.name || e.ecosystem_name || '-';
        const title = e.ecosystem_name || e.name || '-';
        const selected = name === nexus_selected_ecosystem || title === nexus_selected_ecosystem;
        const is_user_active = active_ecosystem && (active_ecosystem === name || active_ecosystem === title);
        const is_default = cint(e.is_default || 0);

        return `
            <div class="nexus-ecosystem-card ${selected ? 'selected' : ''}">
                <div class="nexus-ecosystem-card-top">
                    <div>
                        <h4>${frappe.utils.escape_html(title)}</h4>
                        <p>${frappe.utils.escape_html(e.ecosystem_type || 'Not Set')}</p>
                    </div>
                    <div class="nexus-ecosystem-badges">
                        ${is_user_active ? `<span class="active">My Active Ecosystem</span>` : ''}
                        ${is_default ? `<span class="default">Tenant Default</span>` : ''}
                        ${cint(e.enabled || 0) ? `<span class="enabled">Enabled</span>` : `<span class="disabled">Disabled</span>`}
                    </div>
                </div>

                <div class="nexus-ecosystem-card-body">
                    ${render_kv('Default Public Context', e.default_public_context || '-')}
                    ${render_kv('Default Q&A Channel', e.default_qa_channel || '-')}
                    ${render_kv('Default Chat Channel', e.default_chat_channel || '-')}
                    ${render_kv('Default Public Agent', e.default_public_agent || '-')}
                    ${render_kv('Widget Enabled', yes_no(e.website_widget_enabled))}
                    ${render_kv('Activation Status', e.activation_status || '-')}
                </div>

                <div class="nexus-ecosystem-actions">
                    <button class="btn btn-xs btn-default nexus-select-ecosystem" data-ecosystem="${frappe.utils.escape_html(name)}">
                        Edit Defaults
                    </button>
                    <button class="btn btn-xs btn-primary nexus-switch-ecosystem" data-ecosystem="${frappe.utils.escape_html(name)}">
                        Switch to this Ecosystem
                    </button>
                    <button class="btn btn-xs btn-default nexus-default-ecosystem" data-ecosystem="${frappe.utils.escape_html(name)}">
                        Set as Tenant Default
                    </button>
                </div>
            </div>
        `;
    }).join('');

    $('#nexus_ecosystem_cards').html(html);

    $('.nexus-select-ecosystem').on('click', function() {
        select_ecosystem($(this).data('ecosystem'));
    });

    $('.nexus-switch-ecosystem').on('click', function() {
        switch_to_ecosystem($(this).data('ecosystem'));
    });

    $('.nexus-default-ecosystem').on('click', function() {
        set_tenant_default_ecosystem($(this).data('ecosystem'));
    });
}


function populate_ecosystem_defaults(ecosystem) {
    ecosystem = ecosystem || {};

    $('#nexus_ecosystem_name').val(ecosystem.ecosystem_name || ecosystem.name || '');
    $('#nexus_ecosystem_type').val(ecosystem.ecosystem_type || '');
    $('#nexus_ecosystem_enabled').val(String(cint(ecosystem.enabled || 0)));
    $('#nexus_ecosystem_is_default').val(String(cint(ecosystem.is_default || 0)));

    $('#nexus_default_business_unit').val(ecosystem.default_business_unit || '');
    $('#nexus_default_project').val(ecosystem.default_project || '');
    $('#nexus_default_public_context').val(ecosystem.default_public_context || '');
    $('#nexus_default_top_k').val(ecosystem.default_top_k || 5);

    $('#nexus_qa_enabled').val(String(cint(ecosystem.qa_enabled || 0)));
    $('#nexus_source_citation_required').val(String(cint(ecosystem.source_citation_required || 0)));
    $('#nexus_require_approved_knowledge').val(String(cint(ecosystem.require_approved_knowledge || 0)));

    $('#nexus_live_chat_enabled').val(String(cint(ecosystem.live_chat_enabled || 0)));
    $('#nexus_default_public_agent').val(ecosystem.default_public_agent || '');

    $('#nexus_widget_enabled').val(String(cint(ecosystem.website_widget_enabled || 0)));
    $('#nexus_widget_title').val(ecosystem.widget_title || '');
    $('#nexus_widget_welcome_message').val(ecosystem.widget_welcome_message || '');
    $('#nexus_widget_brand_color').val(ecosystem.widget_brand_color || '#214dbb');

    $('#nexus_qa_fallback_message').val(
        ecosystem.qa_fallback_message || 'I do not have enough approved knowledge to answer this.'
    );

    $('#nexus_default_qa_channel').val(ecosystem.default_qa_channel || '');
    $('#nexus_default_chat_channel').val(ecosystem.default_chat_channel || '');
    $('#nexus_default_live_channel').val(ecosystem.default_live_channel || '');
}


function save_active_user_context() {
    const tenant = $('#nexus_active_tenant').val();

    if (!tenant) {
        frappe.msgprint('Please select a tenant.');
        return;
    }

    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.set_active_user_context',
        args: {
            tenant: tenant,
            ecosystem: $('#nexus_active_ecosystem').val() || null,
            active_ecosystem: $('#nexus_active_ecosystem').val() || null,
            business_unit: $('#nexus_active_business_unit').val() || null,
            project: $('#nexus_active_project').val() || null,
            channel: $('#nexus_active_channel').val() || null
        },
        callback: function() {
            frappe.show_alert({
                message: 'My default context saved.',
                indicator: 'green'
            });

            load_nexus_admin_snapshot();
        },
        error: function(err) {
            frappe.msgprint(err.message || 'Failed to save default context.');
        }
    });
}


function switch_to_ecosystem(ecosystem_name) {
    $('#nexus_active_ecosystem').val(ecosystem_name);
    select_ecosystem(ecosystem_name, false);
    save_active_user_context();
}


function set_tenant_default_ecosystem(ecosystem_name) {
    select_ecosystem(ecosystem_name, false);
    $('#nexus_ecosystem_is_default').val('1');
    save_ecosystem_defaults();
}


function save_ecosystem_defaults() {
    const tenant = get_active_tenant();

    if (!tenant) {
        frappe.msgprint('Please select a tenant first.');
        return;
    }

    const existing = get_selected_ecosystem_doc();
    const ecosystem_name = $('#nexus_ecosystem_name').val() || nexus_selected_ecosystem;

    if (!ecosystem_name) {
        frappe.msgprint('Please enter Ecosystem Name.');
        return;
    }

    const values = {
        name: existing ? existing.name : null,
        ecosystem: existing ? existing.name : null,
        ecosystem_name: ecosystem_name,
        tenant: tenant,

        ecosystem_type: $('#nexus_ecosystem_type').val() || null,
        enabled: cint($('#nexus_ecosystem_enabled').val() || 0),
        is_default: cint($('#nexus_ecosystem_is_default').val() || 0),
        activation_status: 'Configured',

        default_business_unit: $('#nexus_default_business_unit').val() || null,
        default_project: $('#nexus_default_project').val() || null,
        default_public_context: $('#nexus_default_public_context').val() || null,
        default_top_k: cint($('#nexus_default_top_k').val() || 5),

        qa_enabled: cint($('#nexus_qa_enabled').val() || 0),
        default_qa_channel: $('#nexus_default_qa_channel').val() || null,
        qa_fallback_message: $('#nexus_qa_fallback_message').val() || null,
        source_citation_required: cint($('#nexus_source_citation_required').val() || 0),
        require_approved_knowledge: cint($('#nexus_require_approved_knowledge').val() || 0),

        live_chat_enabled: cint($('#nexus_live_chat_enabled').val() || 0),
        default_chat_channel: $('#nexus_default_chat_channel').val() || null,
        default_live_channel: $('#nexus_default_live_channel').val() || null,
        default_public_agent: $('#nexus_default_public_agent').val() || null,

        website_widget_enabled: cint($('#nexus_widget_enabled').val() || 0),
        widget_title: $('#nexus_widget_title').val() || null,
        widget_welcome_message: $('#nexus_widget_welcome_message').val() || null,
        widget_brand_color: $('#nexus_widget_brand_color').val() || null
    };

    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.save_ecosystem_configuration',
        args: {
            values: values
        },
        callback: function() {
            frappe.show_alert({
                message: 'Selected ecosystem defaults saved.',
                indicator: 'green'
            });

            nexus_selected_ecosystem = ecosystem_name;
            load_nexus_admin_snapshot();
        },
        error: function(err) {
            frappe.msgprint(err.message || 'Failed to save ecosystem defaults.');
        }
    });
}


function open_tenant_onboarding_dialog() {
    const dialog = new frappe.ui.Dialog({
        title: 'Onboard Nexus Tenant',
        size: 'large',
        fields: [
            {
                fieldtype: 'Data',
                fieldname: 'tenant_name',
                label: 'Tenant Name',
                reqd: 1
            },
            {
                fieldtype: 'Data',
                fieldname: 'tenant_code',
                label: 'Tenant Code',
                description: 'Example: TEST-NEXUS or DIGITZ-ERP'
            },
            {
                fieldtype: 'Data',
                fieldname: 'ecosystem_name',
                label: 'Initial Ecosystem Name',
                reqd: 1,
                description: 'Example: DIGITZ ERP Sandbox or DIGITZ ERP Production'
            },
            {
                fieldtype: 'Select',
                fieldname: 'ecosystem_type',
                label: 'Initial Ecosystem Type',
                options: [
                    '',
                    'Production',
                    'Sandbox',
                    'Synthetic Validation',
                    'Internal Platform'
                ].join('\n'),
                default: 'Sandbox'
            },
            {
                fieldtype: 'Data',
                fieldname: 'business_unit_name',
                label: 'Default Business Unit',
                reqd: 1
            }
        ],
        primary_action_label: 'Create Tenant',
        primary_action: function(values) {
            frappe.call({
                method: 'digitz_ai_nexus.api.nexus_administration.create_tenant_onboarding',
                args: {
                    tenant_name: values.tenant_name,
                    tenant_code: values.tenant_code,
                    business_unit_name: values.business_unit_name,
                    ecosystem_name: values.ecosystem_name,
                    ecosystem_type: values.ecosystem_type
                },
                callback: function(r) {
                    const tenant = r.message && r.message.tenant
                        ? r.message.tenant
                        : values.tenant_code;

                    save_ecosystem_after_onboarding(
                        tenant,
                        values,
                        dialog
                    );
                },
                error: function(err) {
                    frappe.msgprint(err.message || 'Tenant onboarding failed.');
                }
            });
        }
    });

    dialog.show();
}


function save_ecosystem_after_onboarding(tenant, values, dialog) {
    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.save_ecosystem_configuration',
        args: {
            values: {
                tenant: tenant,
                ecosystem_name: values.ecosystem_name,
                ecosystem_type: values.ecosystem_type || 'Sandbox',
                enabled: 1,
                is_default: 1,
                activation_status: 'Configured',
                default_business_unit: values.business_unit_name
            }
        },
        callback: function() {
            dialog.hide();

            frappe.show_alert({
                message: 'Tenant onboarded and initial ecosystem created.',
                indicator: 'green'
            });

            nexus_selected_ecosystem = values.ecosystem_name;
            load_nexus_admin_snapshot();
        },
        error: function(err) {
            dialog.hide();

            frappe.msgprint(
                (err.message || 'Tenant onboarded, but initial ecosystem could not be saved.')
            );

            load_nexus_admin_snapshot();
        }
    });
}


function open_add_ecosystem_dialog() {
    const tenant = get_active_tenant();

    if (!tenant) {
        frappe.msgprint('Please select a tenant first.');
        return;
    }

    const dialog = new frappe.ui.Dialog({
        title: 'Add Ecosystem',
        size: 'large',
        fields: [
            {
                fieldtype: 'Data',
                fieldname: 'ecosystem_name',
                label: 'Ecosystem Name',
                reqd: 1,
                description: 'Example: TEST-NEXUS Production Validation Ecosystem'
            },
            {
                fieldtype: 'Select',
                fieldname: 'ecosystem_type',
                label: 'Ecosystem Type',
                options: [
                    '',
                    'Production',
                    'Sandbox',
                    'Synthetic Validation',
                    'Internal Platform'
                ].join('\n'),
                default: 'Sandbox',
                reqd: 1
            },
            {
                fieldtype: 'Check',
                fieldname: 'is_default',
                label: 'Set as Tenant Default Ecosystem'
            },
            {
                fieldtype: 'Data',
                fieldname: 'default_business_unit',
                label: 'Default Business Unit',
                default: $('#nexus_active_business_unit').val() || 'Nexus Synthetic BU'
            },
            {
                fieldtype: 'Data',
                fieldname: 'default_public_context',
                label: 'Default Public Context',
                default: 'Nexus Live'
            }
        ],
        primary_action_label: 'Add Ecosystem',
        primary_action: function(values) {
            frappe.call({
                method: 'digitz_ai_nexus.api.nexus_administration.save_ecosystem_configuration',
                args: {
                    values: {
                        tenant: tenant,
                        ecosystem_name: values.ecosystem_name,
                        ecosystem_type: values.ecosystem_type,
                        enabled: 1,
                        is_default: cint(values.is_default || 0),
                        activation_status: 'Configured',
                        default_business_unit: values.default_business_unit || null,
                        default_public_context: values.default_public_context || null
                    }
                },
                callback: function(r) {
                    const created_ecosystem =
                        r.message && r.message.ecosystem
                            ? r.message.ecosystem
                            : null;

                    if (!created_ecosystem) {
                        frappe.msgprint('Ecosystem was saved, but the created ecosystem id was not returned.');
                        load_nexus_admin_snapshot();
                        return;
                    }

                    dialog.hide();

                    nexus_selected_ecosystem = created_ecosystem;

                    activate_created_ecosystem_for_current_user(
                        tenant,
                        created_ecosystem,
                        values
                    );
                },
                error: function(err) {
                    frappe.msgprint(err.message || 'Failed to add ecosystem.');
                }
            });
        }
    });

    dialog.show();
}


function activate_created_ecosystem_for_current_user(tenant, ecosystem, values) {
    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.set_active_user_context',
        args: {
            tenant: tenant,
            active_ecosystem: ecosystem,
            ecosystem: ecosystem,
            business_unit: values.default_business_unit || $('#nexus_active_business_unit').val() || null,
            project: $('#nexus_active_project').val() || null,
            channel: $('#nexus_active_channel').val() || null
        },
        callback: function() {
            frappe.show_alert({
                message: 'Ecosystem added and selected as your active ecosystem.',
                indicator: 'green'
            });

            nexus_selected_ecosystem = ecosystem;
            load_nexus_admin_snapshot();
        },
        error: function(err) {
            frappe.msgprint(
                (err.message || 'Ecosystem was added, but it could not be selected as your active ecosystem.')
            );

            load_nexus_admin_snapshot();
        }
    });
}


function open_nexus_administration_help() {
    const dialog = new frappe.ui.Dialog({
        title: 'Nexus Administration Field Guide',
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'nexus_admin_help_html'
            }
        ]
    });

    dialog.fields_dict.nexus_admin_help_html.$wrapper.html(`
        <div class="nexus-admin-help-wrap">

            <div class="nexus-admin-help-hero">
                <div class="nexus-admin-help-badge">Administration Know-how</div>
                <h3>Tenant → Ecosystem → Defaults</h3>
                <p>
                    Nexus Administration follows a clear hierarchy. A tenant is the isolation boundary.
                    An ecosystem is an operating profile under that tenant. Defaults belong to the selected ecosystem.
                    A user can switch their active ecosystem without affecting other users.
                </p>
            </div>

            <div class="nexus-admin-help-grid">

                <div class="nexus-admin-help-card">
                    <h4>Tenant</h4>
                    <p>
                        Tenant is the highest isolation boundary in Nexus. It represents the company, customer,
                        product environment, or independent knowledge/runtime boundary.
                    </p>
                    <div class="nexus-admin-help-example">
                        Example: <b>DIGITZ-ERP</b>, <b>TEST-NEXUS</b>, <b>Customer-A</b>
                    </div>
                    <ul>
                        <li>A tenant can have multiple ecosystems.</li>
                        <li>Knowledge and runtime must not mix between tenants.</li>
                        <li>Tenant is not where Q&A/chat/widget defaults primarily belong.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Ecosystem</h4>
                    <p>
                        Ecosystem is an operating profile under a tenant. The same tenant may have Production,
                        Sandbox, Synthetic Validation, and Internal Platform ecosystems.
                    </p>
                    <div class="nexus-admin-help-example">
                        DIGITZ-ERP → Production, Internal Platform, Sandbox
                    </div>
                    <ul>
                        <li>Defaults belong to the selected ecosystem.</li>
                        <li>Switching ecosystem changes the current user's active ecosystem selection. The defaults themselves belong to the selected ecosystem and are shared wherever that ecosystem is used.</li>
                        <li>It does not delete or disable other ecosystems.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Ecosystem Type</h4>
                    <p>
                        Ecosystem Type identifies the operating nature of the ecosystem.
                    </p>
                    <div class="nexus-admin-help-example">
                        <b>Production</b>, <b>Sandbox</b>, <b>Synthetic Validation</b>, <b>Internal Platform</b>
                    </div>
                    <ul>
                        <li><b>Production</b> is for real customer or public runtime usage.</li>
                        <li><b>Sandbox</b> is for safe trial and configuration experiments.</li>
                        <li><b>Synthetic Validation</b> is for seeded automated validation tenants.</li>
                        <li><b>Internal Platform</b> is for DIGITZ internal platform operations.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>My Default Context</h4>
                    <p>
                        My Default Context is user-specific. It stores which tenant and ecosystem this user wants
                        to work with by default.
                    </p>
                    <ul>
                        <li>It does not globally change other users.</li>
                        <li>It can select tenant, active ecosystem, business unit, project, and channel.</li>
                        <li>Runtime payload values can still override it.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Selected Ecosystem Defaults</h4>
                    <p>
                        These are fallback values used when a runtime request does not explicitly pass a more specific value.
                    </p>
                    <ul>
                        <li>Default Business Unit</li>
                        <li>Default Public Context</li>
                        <li>Default Q&A Channel</li>
                        <li>Default Chat Channel</li>
                        <li>Default Public Agent</li>
                        <li>Default Widget Settings</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Runtime Priority</h4>
                    <p>
                        Nexus resolves runtime configuration in a controlled order.
                    </p>
                    <ul>
                        <li>1. Explicit runtime payload values are used first.</li>
                        <li>2. If no ecosystem is passed, the current user's active ecosystem is used.</li>
                        <li>3. If the user has no active ecosystem, the tenant default ecosystem is used.</li>
                        <li>4. Defaults from the resolved ecosystem are applied only for missing values.</li>
                        <li>5. If no tenant or ecosystem can be resolved, Nexus should safely return no context.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Nexus Studio Boundary</h4>
                    <p>
                        Knowledge feeding, chunking, metadata tagging, and approval belong to Nexus Studio.
                    </p>
                    <ul>
                        <li>Administration prepares tenant and ecosystem defaults.</li>
                        <li>Studio prepares the actual approved knowledge.</li>
                        <li>Do not treat Administration as the knowledge authoring area.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Validation Lab Boundary</h4>
                    <p>
                        Knowledge testing and runtime validation belong to the Nexus Validation Lab.
                    </p>
                    <ul>
                        <li>Administration shows readiness signals.</li>
                        <li>Validation Lab proves retrieval, grounding, Q&A, Live Chat, and routing behaviour.</li>
                        <li>Production confidence should come after validation.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card nexus-admin-help-wide">
                    <h4>Recommended Administration Workflow</h4>

                    <p>
                        Administration focuses on tenant setup, ecosystem profiles, user default context,
                        ecosystem defaults, Q&A defaults, Live Chat defaults, widget defaults, and readiness.
                    </p>

                    <div class="nexus-admin-help-flow">
                        <div><b>1</b><span>Onboard Tenant</span></div>
                        <div><b>2</b><span>Add Ecosystem Profiles</span></div>
                        <div><b>3</b><span>Switch My Active Ecosystem</span></div>
                        <div><b>4</b><span>Configure Selected Ecosystem Defaults</span></div>
                        <div><b>5</b><span>Configure Q&A and Live Defaults</span></div>
                        <div><b>6</b><span>Configure Widget Defaults</span></div>
                        <div><b>7</b><span>Review Administration Readiness</span></div>
                        <div><b>8</b><span>Proceed to Studio / Validation</span></div>
                    </div>
                </div>

            </div>
        </div>
    `);

    dialog.show();
}


function render_kv(label, value) {
    return `
        <div class="nexus-kv-row">
            <span>${frappe.utils.escape_html(label)}</span>
            <b>${frappe.utils.escape_html(value === undefined || value === null || value === '' ? '-' : String(value))}</b>
        </div>
    `;
}


function render_readiness_pill(label, value) {
    const ok = !!value;

    return `
        <div class="nexus-readiness-pill ${ok ? 'ok' : 'not-ok'}">
            <span>${frappe.utils.escape_html(label)}</span>
            <b>${ok ? 'Yes' : 'No'}</b>
        </div>
    `;
}


function yes_no(value) {
    return cint(value || 0) ? 'Yes' : 'No';
}


function get_snapshot_value(path) {
    if (!nexus_admin_snapshot || !path) {
        return null;
    }

    const parts = path.split('.');
    let value = nexus_admin_snapshot;

    for (const part of parts) {
        if (!value || value[part] === undefined || value[part] === null) {
            return null;
        }

        value = value[part];
    }

    return value;
}


function render_admin_alert(message, indicator) {
    if (!message) {
        $('#nexus_admin_alert_holder').html('');
        return;
    }

    $('#nexus_admin_alert_holder').html(`
        <div class="nexus-admin-alert ${indicator || 'blue'}">
            ${frappe.utils.escape_html(message)}
        </div>
    `);
}


function inject_nexus_admin_css() {
    if ($('#nexus_admin_css').length) return;

    $('head').append(`
        <style id="nexus_admin_css">
            .nexus-admin-wrap {
                padding: 12px;
            }

            .nexus-admin-hero {
                display: flex;
                justify-content: space-between;
                gap: 20px;
                align-items: flex-start;
                position: relative;
                overflow: hidden;
                border-radius: 26px;
                padding: 30px 34px;
                margin-bottom: 18px;
                background:
                    radial-gradient(circle at 8% 20%, rgba(77, 163, 255, 0.28), transparent 30%),
                    radial-gradient(circle at 92% 10%, rgba(224, 166, 47, 0.22), transparent 28%),
                    linear-gradient(135deg, #ffffff 0%, #eef6ff 48%, #f8fbff 100%);
                border: 1px solid rgba(77, 163, 255, 0.38);
                box-shadow: 0 18px 45px rgba(33, 77, 187, 0.12);
            }

            .nexus-admin-badge {
                display: inline-flex;
                align-items: center;
                padding: 8px 14px;
                border-radius: 999px;
                background: rgba(33, 77, 187, 0.09);
                border: 1px solid rgba(33, 77, 187, 0.16);
                color: #214dbb;
                font-weight: 800;
                font-size: 12px;
                letter-spacing: .04em;
                text-transform: uppercase;
                margin-bottom: 12px;
            }

            .nexus-admin-hero h2 {
                margin: 0;
                font-size: 30px;
                font-weight: 900;
                color: #102b67;
                letter-spacing: -0.03em;
            }

            .nexus-admin-hero p {
                margin: 12px 0 0;
                max-width: 880px;
                font-size: 15px;
                line-height: 1.7;
                color: #27416f;
                font-weight: 500;
            }

            .nexus-admin-hero-actions {
                display: flex;
                gap: 10px;
                align-items: center;
                flex-wrap: wrap;
            }

            .nexus-admin-hero-actions .btn,
            .nexus-admin-section-head .btn {
                border-radius: 999px;
                font-weight: 850;
            }

            .nexus-admin-grid {
                display: grid;
                gap: 18px;
                margin-bottom: 18px;
            }

            .nexus-admin-grid-3 {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }

            .nexus-admin-grid-2 {
                grid-template-columns: 1.15fr .85fr;
            }

            .nexus-admin-card {
                border: 1px solid rgba(77, 163, 255, 0.28);
                border-radius: 22px;
                background: #fff;
                padding: 20px;
                box-shadow: 0 12px 30px rgba(33, 77, 187, 0.07);
            }

            .nexus-admin-card-title {
                display: inline-flex;
                align-items: center;
                gap: 12px;
                color: #173b8c;
                font-size: 16px;
                font-weight: 900;
                padding: 10px 16px;
                margin-bottom: 16px;
                border-radius: 999px;
                background: #eef6ff;
                border: 1px solid rgba(33, 77, 187, 0.14);
            }

            .nexus-admin-card-title:after {
                content: "";
                width: 36px;
                height: 4px;
                border-radius: 999px;
                background: linear-gradient(90deg, #e0a62f, #f4ca64);
            }

            .nexus-admin-card-body {
                display: grid;
                gap: 10px;
            }

            .nexus-admin-section-head {
                display: flex;
                justify-content: space-between;
                gap: 18px;
                align-items: flex-start;
                margin-bottom: 16px;
            }

            .nexus-admin-section-head .nexus-admin-card-title {
                margin-bottom: 8px;
            }

            .nexus-admin-section-head p {
                margin: 0;
                color: #53688f;
                font-size: 13px;
                line-height: 1.6;
                font-weight: 650;
            }

            .nexus-admin-form-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
            }

            .nexus-admin-form-grid-4 {
                grid-template-columns: repeat(4, minmax(0, 1fr));
            }

            .nexus-admin-form-grid-5 {
                grid-template-columns: repeat(5, minmax(0, 1fr));
            }

            .nexus-admin-form-grid label,
            .nexus-admin-question-box label {
                display: block;
                margin-bottom: 6px;
                color: #27416f;
                font-size: 12px;
                font-weight: 850;
            }

            .nexus-admin-question-box {
                margin-top: 14px;
            }

            .nexus-kv-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 12px;
                padding: 10px 12px;
                border-radius: 14px;
                background: #f8fbff;
                border: 1px solid rgba(77, 163, 255, 0.18);
            }

            .nexus-kv-row span {
                color: #53688f;
                font-size: 12px;
                font-weight: 800;
            }

            .nexus-kv-row b {
                color: #173b8c;
                font-size: 12px;
                font-weight: 900;
                text-align: right;
                word-break: break-word;
            }

            .nexus-readiness-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px;
                margin-bottom: 14px;
            }

            .nexus-readiness-pill {
                padding: 12px;
                border-radius: 16px;
                display: flex;
                justify-content: space-between;
                gap: 10px;
                align-items: center;
                font-weight: 900;
            }

            .nexus-readiness-pill.ok {
                background: #ecfdf3;
                color: #16794c;
                border: 1px solid #bdebd2;
            }

            .nexus-readiness-pill.not-ok {
                background: #fff7e6;
                color: #8a5d00;
                border: 1px solid #f2d49b;
            }

            .nexus-readiness-pill span {
                font-size: 12px;
            }

            .nexus-readiness-pill b {
                font-size: 12px;
            }

            .nexus-readiness-counts {
                display: grid;
                gap: 10px;
            }

            .nexus-empty-state {
                padding: 16px;
                border-radius: 16px;
                background: #fff7e6;
                border: 1px solid #f2d49b;
                color: #8a5d00;
                font-weight: 800;
                line-height: 1.6;
            }

            .nexus-admin-alert {
                margin-bottom: 18px;
                padding: 14px 16px;
                border-radius: 16px;
                font-weight: 850;
            }

            .nexus-admin-alert.red {
                background: #fff0f0;
                color: #b42318;
                border: 1px solid #ffd1d1;
            }

            .nexus-admin-alert.blue {
                background: #eef6ff;
                color: #214dbb;
                border: 1px solid rgba(33,77,187,.16);
            }

            .nexus-ecosystem-card-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 16px;
            }

            .nexus-ecosystem-card {
                border-radius: 20px;
                padding: 18px;
                background: #ffffff;
                border: 1px solid rgba(77, 163, 255, 0.25);
                box-shadow: 0 10px 24px rgba(33, 77, 187, 0.06);
            }

            .nexus-ecosystem-card.selected {
                border-color: rgba(33, 77, 187, 0.75);
                box-shadow: 0 14px 34px rgba(33, 77, 187, 0.14);
            }

            .nexus-ecosystem-card-top {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                align-items: flex-start;
                margin-bottom: 14px;
            }

            .nexus-ecosystem-card h4 {
                margin: 0;
                color: #102b67;
                font-size: 16px;
                font-weight: 950;
            }

            .nexus-ecosystem-card p {
                margin: 5px 0 0;
                color: #53688f;
                font-size: 12px;
                font-weight: 800;
            }

            .nexus-ecosystem-badges {
                display: flex;
                flex-wrap: wrap;
                justify-content: flex-end;
                gap: 6px;
            }

            .nexus-ecosystem-badges span {
                padding: 5px 8px;
                border-radius: 999px;
                font-size: 10px;
                font-weight: 900;
                white-space: nowrap;
            }

            .nexus-ecosystem-badges .active {
                background: #eef6ff;
                color: #214dbb;
                border: 1px solid rgba(33,77,187,.18);
            }

            .nexus-ecosystem-badges .default {
                background: #fff7e6;
                color: #8a5d00;
                border: 1px solid #f2d49b;
            }

            .nexus-ecosystem-badges .enabled {
                background: #ecfdf3;
                color: #16794c;
                border: 1px solid #bdebd2;
            }

            .nexus-ecosystem-badges .disabled {
                background: #fff0f0;
                color: #b42318;
                border: 1px solid #ffd1d1;
            }

            .nexus-ecosystem-card-body {
                display: grid;
                gap: 8px;
                margin-bottom: 14px;
            }

            .nexus-ecosystem-actions {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }

            .nexus-ecosystem-actions .btn {
                border-radius: 999px;
                font-weight: 850;
            }

            .nexus-admin-help-wrap {
                padding: 4px;
            }

            .nexus-admin-help-hero {
                padding: 22px 24px;
                border-radius: 22px;
                margin-bottom: 18px;
                background:
                    radial-gradient(circle at 8% 20%, rgba(77, 163, 255, 0.24), transparent 30%),
                    radial-gradient(circle at 92% 10%, rgba(224, 166, 47, 0.18), transparent 28%),
                    linear-gradient(135deg, #ffffff 0%, #eef6ff 48%, #f8fbff 100%);
                border: 1px solid rgba(77, 163, 255, 0.34);
            }

            .nexus-admin-help-badge {
                display: inline-flex;
                padding: 7px 12px;
                border-radius: 999px;
                background: rgba(33, 77, 187, 0.09);
                color: #214dbb;
                border: 1px solid rgba(33, 77, 187, 0.14);
                font-size: 11px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: .04em;
                margin-bottom: 10px;
            }

            .nexus-admin-help-hero h3 {
                margin: 0;
                color: #102b67;
                font-size: 24px;
                font-weight: 950;
                letter-spacing: -0.02em;
            }

            .nexus-admin-help-hero p {
                margin: 10px 0 0;
                color: #27416f;
                font-size: 14px;
                line-height: 1.7;
                font-weight: 600;
            }

            .nexus-admin-help-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
            }

            .nexus-admin-help-card {
                padding: 18px;
                border-radius: 18px;
                background: #ffffff;
                border: 1px solid rgba(77, 163, 255, 0.24);
                box-shadow: 0 8px 18px rgba(33, 77, 187, 0.05);
            }

            .nexus-admin-help-card h4 {
                margin: 0 0 8px;
                color: #173b8c;
                font-size: 16px;
                font-weight: 950;
            }

            .nexus-admin-help-card p {
                margin: 0 0 10px;
                color: #27416f;
                font-size: 13px;
                line-height: 1.65;
                font-weight: 600;
            }

            .nexus-admin-help-card ul {
                margin: 10px 0 0;
                padding-left: 20px;
            }

            .nexus-admin-help-card li {
                color: #53688f;
                font-size: 12px;
                line-height: 1.65;
                font-weight: 700;
                margin-bottom: 4px;
            }

            .nexus-admin-help-example {
                padding: 10px 12px;
                border-radius: 14px;
                background: #eef6ff;
                border: 1px solid rgba(33, 77, 187, 0.12);
                color: #27416f;
                font-size: 12px;
                font-weight: 750;
                margin-bottom: 10px;
            }

            .nexus-admin-help-example b {
                color: #173b8c;
            }

            .nexus-admin-help-wide {
                grid-column: 1 / -1;
            }

            .nexus-admin-help-flow {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 10px;
                margin-top: 12px;
            }

            .nexus-admin-help-flow div {
                padding: 12px;
                border-radius: 16px;
                background: #f8fbff;
                border: 1px solid rgba(77, 163, 255, 0.22);
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .nexus-admin-help-flow b {
                width: 28px;
                height: 28px;
                border-radius: 999px;
                background: #214dbb;
                color: #ffffff;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: 950;
            }

            .nexus-admin-help-flow span {
                color: #27416f;
                font-size: 12px;
                font-weight: 850;
                line-height: 1.35;
            }

            @media (max-width: 1300px) {
                .nexus-admin-form-grid-5 {
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                }

                .nexus-ecosystem-card-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }

            @media (max-width: 1200px) {
                .nexus-admin-grid-3,
                .nexus-admin-grid-2,
                .nexus-admin-form-grid-4 {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }

            @media (max-width: 900px) {
                .nexus-admin-help-grid {
                    grid-template-columns: 1fr;
                }

                .nexus-admin-help-flow {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }

                .nexus-ecosystem-card-grid {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 760px) {
                .nexus-admin-hero,
                .nexus-admin-section-head {
                    flex-direction: column;
                }

                .nexus-admin-grid-3,
                .nexus-admin-grid-2,
                .nexus-admin-form-grid,
                .nexus-admin-form-grid-4,
                .nexus-admin-form-grid-5,
                .nexus-readiness-grid {
                    grid-template-columns: 1fr;
                }

                .nexus-admin-hero-actions,
                .nexus-admin-hero-actions .btn,
                .nexus-admin-section-head .btn {
                    width: 100%;
                }
            }

            @media (max-width: 560px) {
                .nexus-admin-help-flow {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    `);
}