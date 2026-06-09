let nexus_admin_snapshot = null;
let nexus_selected_tenant_configuration = null;

let nexus_business_keyword_snapshot = {
    categories: [],
    keywords: []
};

let nexus_access_governance_snapshot = {
    overview: {},
    policies: []
};

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
                    <h2>Tenant Administration</h2>
                    <p>
                        Configure tenants and the minimum tenant defaults required by Nexus.
                        Chat, Q&A, API, and future access routing is resolved through
                        <b>Category → Identity → AI Agent Profile → Access Category → Access Policy</b>.
                    </p>
                </div>

                <div class="nexus-admin-hero-actions">
                    <button class="btn btn-default" id="nexus_admin_help">
                        Help / Field Guide
                    </button>

                    <button class="btn btn-default" id="nexus_admin_refresh">
                        Refresh
                    </button>

                    <button class="btn btn-primary" id="nexus_admin_open_onboarding">
                        Onboard Tenant
                    </button>
                </div>
            </div>

            <div id="nexus_admin_alert_holder"></div>

            <div class="nexus-admin-card">
                <div class="nexus-admin-section-head">
                    <div>
                        <div class="nexus-admin-card-title">Tenant</div>
                        <p>
                            Select the tenant you want to configure. Tenant configuration is global for that tenant.
                        </p>
                    </div>
                </div>

                <div class="nexus-admin-form-grid nexus-admin-form-grid-2">
                    <div>
                        <label>Tenant</label>
                        <select id="nexus_active_tenant" class="form-control"></select>
                    </div>

                    <div id="nexus_tenant_summary" class="nexus-admin-card-body">
                        Loading...
                    </div>
                </div>
            </div>

            <div class="nexus-admin-card">
                <div class="nexus-admin-section-head">
                    <div>
                        <div class="nexus-admin-card-title">Tenant Configuration</div>
                        <p>
                            Keep this section to tenant-wide defaults only. Routing and access policy assignment belong
                            to category, identity, agent profile, access category, and access policy setup.
                        </p>
                    </div>

                    <button class="btn btn-primary btn-sm" id="nexus_save_tenant_configuration">
                        Save Tenant Configuration
                    </button>
                </div>

                <div class="nexus-admin-form-grid nexus-admin-form-grid-4">
                    <div>
                        <label>Default Business Unit</label>
                        <select id="nexus_default_business_unit" class="form-control"></select>
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
                        <label>Strict Tenant Mode</label>
                        <select id="nexus_strict_tenant_mode" class="form-control">
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

            <div class="nexus-admin-card">
                <div class="nexus-admin-section-head">
                    <div>
                        <div class="nexus-admin-card-title">Tenant Readiness</div>
                        <p>
                            A compact status view for the selected tenant.
                        </p>
                    </div>
                </div>
                <div id="nexus_readiness_card" class="nexus-admin-card-body">
                    Loading...
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

    $('#nexus_save_tenant_configuration').on('click', function() {
        save_tenant_configuration();
    });

    $('#nexus_active_tenant').on('change', function() {
        nexus_selected_tenant_configuration = null;
        load_nexus_admin_snapshot();
    });
}


function load_nexus_admin_snapshot() {
    set_loading_state();

    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.get_administration_snapshot',
        args: {
            tenant: $('#nexus_active_tenant').val() || null
        },
        callback: function(r) {
            nexus_admin_snapshot = r.message || {};
            normalize_snapshot_for_tenant_configuration();
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


function normalize_snapshot_for_tenant_configuration() {
    nexus_admin_snapshot = nexus_admin_snapshot || {};

    if (!Array.isArray(nexus_admin_snapshot.tenant_configurations)) {
        nexus_admin_snapshot.tenant_configurations = nexus_admin_snapshot.ecosystems || [];
    }

    if (nexus_admin_snapshot.tenant_configuration && !nexus_admin_snapshot.tenant_configurations.length) {
        nexus_admin_snapshot.tenant_configurations.push(nexus_admin_snapshot.tenant_configuration);
    }

    if (!nexus_selected_tenant_configuration && nexus_admin_snapshot.tenant_configurations.length) {
        nexus_selected_tenant_configuration =
            nexus_admin_snapshot.tenant_configurations[0].name
            || nexus_admin_snapshot.tenant_configurations[0].ecosystem_name;
    }
}


function set_loading_state() {
    $('#nexus_tenant_summary').html('Loading...');
    $('#nexus_readiness_card').html('Loading...');
}


function render_nexus_admin_snapshot(snapshot) {
    snapshot = snapshot || {};

    render_admin_alert('', '');
    populate_selector_options(snapshot.selectors || {});
    render_tenant_summary(snapshot.tenant);
    render_readiness(snapshot.readiness);
    populate_tenant_configuration(get_selected_tenant_configuration_doc());
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
        get_snapshot_value('tenant.name') || get_snapshot_value('resolved_context.tenant')
    );

    populate_select(
        '#nexus_default_business_unit',
        selectors.business_units || [],
        'name',
        function(row) {
            return row.business_unit_name || row.name;
        },
        null,
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
        || get_snapshot_value('tenant.name')
        || get_snapshot_value('resolved_context.tenant');
}


function get_tenant_configurations_for_active_tenant() {
    const tenant = get_active_tenant();

    return (nexus_admin_snapshot?.tenant_configurations || []).filter(e => {
        if (!tenant) return true;
        return !e.tenant || e.tenant === tenant;
    });
}


function get_selected_tenant_configuration_doc() {
    const tenant_configurations = get_tenant_configurations_for_active_tenant();

    if (!tenant_configurations.length) {
        return null;
    }

    if (nexus_selected_tenant_configuration) {
        const found = tenant_configurations.find(e => {
            return e.name === nexus_selected_tenant_configuration
                || e.ecosystem_name === nexus_selected_tenant_configuration;
        });

        if (found) return found;
    }

    return tenant_configurations.find(e => cint(e.is_default || 0)) || tenant_configurations[0];
}


function render_tenant_summary(tenant) {
    if (!tenant) {
        $('#nexus_tenant_summary').html(`
            <div class="nexus-empty-state">
                Select or onboard a tenant.
            </div>
        `);
        return;
    }

    $('#nexus_tenant_summary').html(`
        ${render_kv('Tenant Code', tenant.name || '-')}
        ${render_kv('Tenant Name', tenant.tenant_name || '-')}
        ${render_kv('Status', cint(tenant.disabled || 0) ? 'Disabled' : 'Enabled')}
    `);
}


function render_readiness(readiness) {
    readiness = readiness || {};

    $('#nexus_readiness_card').html(`
        <div class="nexus-readiness-grid">
            ${render_readiness_pill('Q&A Ready', readiness.qa_ready)}
            ${render_readiness_pill('Live Ready', readiness.live_ready)}
            ${render_readiness_pill('Identity Safe Guard', readiness.identity_safeguard_ready)}
            ${render_readiness_pill('Knowledge Ready', readiness.knowledge_count > 0 && readiness.chunk_count > 0)}
        </div>

        <div class="nexus-readiness-counts">
            ${render_kv('Knowledge Units', readiness.knowledge_count || 0)}
            ${render_kv('Knowledge Chunks', readiness.chunk_count || 0)}
            ${render_kv('Channels', readiness.channel_count || 0)}
            ${render_kv('AI Agents', readiness.ai_agent_count || 0)}
            ${render_kv('Category Routes', readiness.category_route_count || 0)}
            ${render_kv('Profile Access Rows', readiness.profile_access_count || 0)}
            ${render_kv('Identity Routes', readiness.registered_identity_route_count || 0)}
        </div>
    `);
}


function populate_tenant_configuration(config) {
    config = config || {};

    $('#nexus_default_business_unit').val(config.default_business_unit || '');
    $('#nexus_default_top_k').val(config.default_top_k || 5);

    $('#nexus_qa_enabled').val(String(cint(config.qa_enabled || 0)));
    $('#nexus_source_citation_required').val(String(cint(config.source_citation_required || 0)));
    $('#nexus_require_approved_knowledge').val(String(cint(config.require_approved_knowledge || 0)));
    $('#nexus_strict_tenant_mode').val(String(cint(config.strict_tenant_mode || 0)));

    $('#nexus_live_chat_enabled').val(String(cint(config.live_chat_enabled || 0)));

    $('#nexus_widget_enabled').val(String(cint(config.website_widget_enabled || 0)));
    $('#nexus_widget_title').val(config.widget_title || '');
    $('#nexus_widget_welcome_message').val(config.widget_welcome_message || '');
    $('#nexus_widget_brand_color').val(config.widget_brand_color || '#214dbb');

    $('#nexus_qa_fallback_message').val(
        config.qa_fallback_message || 'I do not have enough approved knowledge to answer this.'
    );

    $('#nexus_default_qa_channel').val(config.default_qa_channel || '');
    $('#nexus_default_chat_channel').val(config.default_chat_channel || '');
}


function save_tenant_configuration() {
    const tenant = get_active_tenant();

    if (!tenant) {
        frappe.msgprint('Please select a tenant first.');
        return;
    }

    const existing = get_selected_tenant_configuration_doc();
    const configuration_name = (existing ? existing.ecosystem_name || existing.name : null)
        || `${tenant} Configuration`;

    const values = {
        name: existing ? existing.name : null,
        ecosystem: existing ? existing.name : null,
        ecosystem_name: configuration_name,
        tenant: tenant,

        ecosystem_type: 'Production',
        enabled: 1,
        is_default: 1,
        activation_status: 'Configured',
        certification_status: 'Not Certified',

        default_business_unit: $('#nexus_default_business_unit').val() || null,
        default_top_k: cint($('#nexus_default_top_k').val() || 5),

        qa_enabled: cint($('#nexus_qa_enabled').val() || 0),
        default_qa_channel: $('#nexus_default_qa_channel').val() || null,
        qa_fallback_message: $('#nexus_qa_fallback_message').val() || null,
        source_citation_required: cint($('#nexus_source_citation_required').val() || 0),
        require_approved_knowledge: cint($('#nexus_require_approved_knowledge').val() || 0),
        strict_tenant_mode: cint($('#nexus_strict_tenant_mode').val() || 0),
        testing_required_before_activation: 0,

        live_chat_enabled: cint($('#nexus_live_chat_enabled').val() || 0),
        default_chat_channel: $('#nexus_default_chat_channel').val() || null,

        website_widget_enabled: cint($('#nexus_widget_enabled').val() || 0),
        widget_title: $('#nexus_widget_title').val() || null,
        widget_welcome_message: $('#nexus_widget_welcome_message').val() || null,
        widget_brand_color: $('#nexus_widget_brand_color').val() || null
    };

    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.save_tenant_configuration',
        args: {
            values: values
        },
        callback: function() {
            frappe.show_alert({
                message: 'Tenant runtime configuration saved.',
                indicator: 'green'
            });

            nexus_selected_tenant_configuration = existing ? existing.name : configuration_name;
            load_nexus_admin_snapshot();
        },
        error: function(err) {
            frappe.msgprint(err.message || 'Failed to save tenant configuration.');
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
                description: 'Example: TEST-NEXUS or CUSTOMER-A'
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
                    business_unit_name: values.business_unit_name
                },
                callback: function(r) {
                    const tenant = r.message && r.message.tenant
                        ? r.message.tenant
                        : values.tenant_code;

                    dialog.hide();

                    frappe.show_alert({
                        message: 'Tenant onboarded.',
                        indicator: 'green'
                    });

                    nexus_selected_tenant_configuration = null;

                    if (tenant) {
                        $('#nexus_active_tenant').val(tenant);
                    }

                    load_nexus_admin_snapshot();
                },
                error: function(err) {
                    frappe.msgprint(err.message || 'Tenant onboarding failed.');
                }
            });
        }
    });

    dialog.show();
}

function load_business_keyword_controls() {
    $('#nexus_business_keyword_summary').html('Loading...');
    $('#nexus_business_keyword_table').html('Loading...');

    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.get_business_keyword_controls',
        callback: function(r) {
            nexus_business_keyword_snapshot = r.message || {
                categories: [],
                keywords: []
            };

            render_business_keyword_controls();
        },
        error: function(err) {
            $('#nexus_business_keyword_summary').html(`
                <div class="nexus-empty-state">
                    Failed to load business keywords.
                </div>
            `);

            $('#nexus_business_keyword_table').html(
                frappe.utils.escape_html(err.message || '')
            );
        }
    });
}


function render_business_keyword_controls() {
    const categories = nexus_business_keyword_snapshot.categories || [];
    const keywords = nexus_business_keyword_snapshot.keywords || [];

    const enabled_count = keywords.filter(k => cint(k.enabled || 0)).length;
    const disabled_count = keywords.length - enabled_count;

    $('#nexus_business_keyword_summary').html(`
        ${render_kv('Keyword Categories', categories.length)}
        ${render_kv('Business Keywords', keywords.length)}
        ${render_kv('Enabled Keywords', enabled_count)}
        ${render_kv('Disabled Keywords', disabled_count)}
    `);

    if (!keywords.length) {
        $('#nexus_business_keyword_table').html(`
            <div class="nexus-empty-state">
                No business keywords configured yet. Use Add / Update Keyword to create retrieval relevance signals.
            </div>
        `);
        return;
    }

    const rows = keywords.map(k => {
        const enabled = cint(k.enabled || 0);

        return `
            <tr>
                <td>
                    <b>${frappe.utils.escape_html(k.keyword || '-')}</b>
                    <div class="nexus-admin-muted">${frappe.utils.escape_html(k.description || '')}</div>
                </td>
                <td>${frappe.utils.escape_html(k.category || '-')}</td>
                <td>${frappe.utils.escape_html(k.priority_level || '-')}</td>
                <td>${frappe.utils.escape_html(k.boost_weight === undefined || k.boost_weight === null ? '-' : String(k.boost_weight))}</td>
                <td>${frappe.utils.escape_html(k.synonyms || '-')}</td>
                <td>
                    <span class="nexus-status-pill ${enabled ? 'enabled' : 'disabled'}">
                        ${enabled ? 'Enabled' : 'Disabled'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-xs btn-default nexus-edit-business-keyword" data-keyword="${frappe.utils.escape_html(k.name)}">
                        Edit
                    </button>
                    <button class="btn btn-xs ${enabled ? 'btn-default' : 'btn-primary'} nexus-toggle-business-keyword"
                        data-keyword="${frappe.utils.escape_html(k.name)}"
                        data-enabled="${enabled ? 0 : 1}">
                        ${enabled ? 'Disable' : 'Enable'}
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    $('#nexus_business_keyword_table').html(`
        <table class="table table-bordered nexus-admin-table">
            <thead>
                <tr>
                    <th>Keyword</th>
                    <th>Category</th>
                    <th>Priority</th>
                    <th>Boost</th>
                    <th>Synonyms</th>
                    <th>Status</th>
                    <th style="width: 150px;">Actions</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `);

    $('.nexus-edit-business-keyword').on('click', function() {
        const name = $(this).data('keyword');
        const keyword = keywords.find(k => k.name === name);
        open_business_keyword_dialog(keyword);
    });

    $('.nexus-toggle-business-keyword').on('click', function() {
        const name = $(this).data('keyword');
        const enabled = cint($(this).data('enabled') || 0);
        toggle_business_keyword(name, enabled);
    });
}


function open_business_keyword_dialog(existing_keyword=null) {
    const dialog = new frappe.ui.Dialog({
        title: existing_keyword ? 'Update Business Keyword' : 'Add Business Keyword',
        size: 'large',
        fields: [
            {
                fieldtype: 'Data',
                fieldname: 'keyword',
                label: 'Business Keyword',
                reqd: 1,
                default: existing_keyword ? existing_keyword.keyword : ''
            },
            {
                fieldtype: 'Link',
                fieldname: 'category',
                label: 'Keyword Category',
                options: 'Nexus Keyword Category',
                default: existing_keyword ? existing_keyword.category : ''
            },
            {
                fieldtype: 'Select',
                fieldname: 'priority_level',
                label: 'Priority Level',
                options: [
                    'High',
                    'Medium',
                    'Low'
                ].join('\n'),
                default: existing_keyword ? existing_keyword.priority_level : 'Medium'
            },
            {
                fieldtype: 'Float',
                fieldname: 'boost_weight',
                label: 'Boost Weight',
                default: existing_keyword && existing_keyword.boost_weight !== undefined
                    ? existing_keyword.boost_weight
                    : 1.0
            },
            {
                fieldtype: 'Check',
                fieldname: 'enabled',
                label: 'Enabled',
                default: existing_keyword ? cint(existing_keyword.enabled || 0) : 1
            },
            {
                fieldtype: 'Small Text',
                fieldname: 'synonyms',
                label: 'Synonyms',
                description: 'Comma-separated or line-separated terms.',
                default: existing_keyword ? existing_keyword.synonyms : ''
            },
            {
                fieldtype: 'Small Text',
                fieldname: 'description',
                label: 'Description',
                default: existing_keyword ? existing_keyword.description : ''
            }
        ],
        primary_action_label: existing_keyword ? 'Update Keyword' : 'Add Keyword',
        primary_action: function(values) {
            save_business_keyword(values, existing_keyword ? existing_keyword.name : null, dialog);
        }
    });

    dialog.show();
}


function save_business_keyword(values, existing_name, dialog) {
    values = values || {};
    values.name = existing_name || null;

    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.save_business_keyword',
        args: {
            values: values
        },
        callback: function() {
            dialog.hide();

            frappe.show_alert({
                message: 'Business keyword saved.',
                indicator: 'green'
            });

            load_business_keyword_controls();
        },
        error: function(err) {
            frappe.msgprint(err.message || 'Failed to save business keyword.');
        }
    });
}


function toggle_business_keyword(name, enabled) {
    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.set_business_keyword_enabled',
        args: {
            name: name,
            enabled: enabled
        },
        callback: function() {
            frappe.show_alert({
                message: enabled ? 'Business keyword enabled.' : 'Business keyword disabled.',
                indicator: enabled ? 'green' : 'orange'
            });

            load_business_keyword_controls();
        },
        error: function(err) {
            frappe.msgprint(err.message || 'Failed to update business keyword.');
        }
    });
}


function load_access_governance_overview() {
    $('#nexus_access_governance_summary').html('Loading...');
    $('#nexus_access_governance_distribution').html('Loading...');
    $('#nexus_access_policy_table').html('Loading...');

    frappe.call({
        method: 'digitz_ai_nexus.api.nexus_administration.get_access_governance_overview',
        callback: function(r) {
            nexus_access_governance_snapshot = r.message || {
                overview: {},
                policies: []
            };

            render_access_governance_overview();
        },
        error: function(err) {
            $('#nexus_access_governance_summary').html(`
                <div class="nexus-empty-state">
                    Failed to load access governance overview.
                </div>
            `);

            $('#nexus_access_governance_distribution').html(
                frappe.utils.escape_html(err.message || '')
            );

            $('#nexus_access_policy_table').html('');
        }
    });
}


function render_access_governance_overview() {
    const overview = nexus_access_governance_snapshot.overview || {};
    const policies = nexus_access_governance_snapshot.policies || [];

    $('#nexus_access_governance_summary').html(`
        ${render_kv('Access Policies', overview.access_policy_count || 0)}
        ${render_kv('Enabled Policies', overview.enabled_policy_count || 0)}
        ${render_kv('Disabled Policies', overview.disabled_policy_count || 0)}

        ${render_kv('Knowledge Sources', overview.knowledge_sources_total || 0)}
        ${render_kv('Sources With Policy', overview.knowledge_sources_with_policy || 0)}

        ${render_kv('Knowledge Units', overview.knowledge_units_total || 0)}
        ${render_kv('Units With Policy', overview.knowledge_units_with_policy || 0)}

        ${render_kv('Knowledge Chunks', overview.knowledge_chunks_total || 0)}
        ${render_kv('Chunks With Policy', overview.knowledge_chunks_with_policy || 0)}
        ${render_kv('Chunks With Allowed Roles', overview.knowledge_chunks_with_allowed_roles || 0)}
        ${render_kv('Chunks With Denied Roles', overview.knowledge_chunks_with_denied_roles || 0)}
    `);

    render_access_governance_distribution(overview);
    render_access_policy_table(policies);
}


function render_access_governance_distribution(overview) {
    const source_rows = overview.source_sensitivity_distribution || [];
    const unit_rows = overview.unit_sensitivity_distribution || [];
    const chunk_rows = overview.chunk_sensitivity_distribution || [];

    $('#nexus_access_governance_distribution').html(`
        <div class="nexus-admin-subtitle">Sensitivity Distribution</div>

        <div class="nexus-governance-distribution-grid">
            ${render_sensitivity_distribution_table('Sources', source_rows)}
            ${render_sensitivity_distribution_table('Knowledge Units', unit_rows)}
            ${render_sensitivity_distribution_table('Chunks', chunk_rows)}
        </div>
    `);
}


function render_sensitivity_distribution_table(title, rows) {
    if (!rows || !rows.length) {
        return `
            <div class="nexus-governance-mini-table">
                <h4>${frappe.utils.escape_html(title)}</h4>
                <div class="nexus-empty-state">No sensitivity data.</div>
            </div>
        `;
    }

    const html = rows.map(row => {
        return `
            <tr>
                <td>${frappe.utils.escape_html(row.sensitivity || 'Not Set')}</td>
                <td>${frappe.utils.escape_html(String(row.count || 0))}</td>
            </tr>
        `;
    }).join('');

    return `
        <div class="nexus-governance-mini-table">
            <h4>${frappe.utils.escape_html(title)}</h4>
            <table class="table table-bordered nexus-admin-table">
                <thead>
                    <tr>
                        <th>Sensitivity</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>${html}</tbody>
            </table>
        </div>
    `;
}


function render_access_policy_table(policies) {
    if (!policies || !policies.length) {
        $('#nexus_access_policy_table').html(`
            <div class="nexus-empty-state">
                No access policies found. Create policies from the Nexus Access Policy list.
            </div>
        `);
        return;
    }

    const rows = policies.map(policy => {
        const disabled = cint(policy.disabled || 0);

        return `
            <tr>
                <td>
                    <b>${frappe.utils.escape_html(policy.policy_name || policy.name || '-')}</b>
                    <div class="nexus-admin-muted">${frappe.utils.escape_html(policy.description || '')}</div>
                </td>
                <td>${frappe.utils.escape_html(policy.access_level || '-')}</td>
                <td>${frappe.utils.escape_html(policy.sensitivity || '-')}</td>
                <td>${frappe.utils.escape_html(policy.allowed_roles || '-')}</td>
                <td>${frappe.utils.escape_html(policy.excluded_roles || '-')}</td>
                <td>
                    <span class="nexus-status-pill ${disabled ? 'disabled' : 'enabled'}">
                        ${disabled ? 'Disabled' : 'Enabled'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-xs btn-default nexus-open-access-policy"
                        data-policy="${frappe.utils.escape_html(policy.name)}">
                        Open
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    $('#nexus_access_policy_table').html(`
        <div class="nexus-admin-subtitle">Access Policy Master</div>

        <table class="table table-bordered nexus-admin-table">
            <thead>
                <tr>
                    <th>Policy</th>
                    <th>Access Level</th>
                    <th>Sensitivity</th>
                    <th>Allowed Roles</th>
                    <th>Excluded Roles</th>
                    <th>Status</th>
                    <th style="width: 90px;">Action</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `);

    $('.nexus-open-access-policy').on('click', function() {
        const policy = $(this).data('policy');
        frappe.set_route('Form', 'Nexus Access Policy', policy);
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
                <h3>Tenant → Configuration</h3>
                <p>
                    Nexus Administration is now only for tenant setup and tenant-wide defaults.
                    Routing is handled separately by category, identity, profile, access category, and access policy.
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
                        Example: <b>TEST-NEXUS</b>, <b>Customer-A</b>, <b>Internal Platform Tenant</b>
                    </div>
                    <ul>
                        <li>A tenant is the only isolation boundary configured here.</li>
                        <li>Knowledge and runtime must not mix between tenants.</li>
                        <li>Routing belongs to category, identity, profile, access category, and access policy.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Tenant Configuration</h4>
                    <p>
                        Tenant configuration stores only the defaults needed when a request does not explicitly
                        provide tenant-scoped values.
                    </p>
                    <ul>
                        <li>Default Business Unit</li>
                        <li>Default Public Context</li>
                        <li>Default Q&A Channel</li>
                        <li>Default Chat Channel</li>
                        <li>Widget defaults</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Safety Defaults</h4>
                    <p>
                        These defaults keep runtime behaviour tenant-scoped and grounded.
                    </p>
                    <ul>
                        <li><b>Require Approved Knowledge</b> ensures only approved knowledge is used.</li>
                        <li><b>Strict Tenant Mode</b> keeps runtime behaviour scoped to the tenant.</li>
                        <li><b>Source Citation Required</b> encourages grounded and explainable answers.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Runtime Boundary</h4>
                    <p>
                        Runtime must not choose profiles or policies from tenant configuration.
                    </p>
                    <ul>
                        <li>Tenant configuration supplies missing non-routing defaults.</li>
                        <li>Profile and access selection comes from category and identity routing.</li>
                        <li>Missing required tenant information should fail as a configuration issue.</li>
                    </ul>
                </div>

                <div class="nexus-admin-help-card">
                    <h4>Nexus Studio Boundary</h4>
                    <p>
                        Knowledge feeding, chunking, metadata tagging, and approval belong to Nexus Studio.
                    </p>
                    <ul>
                        <li>Administration prepares tenant runtime defaults.</li>
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
                        Administration now has one job: keep the tenant and tenant defaults correct.
                    </p>

                    <div class="nexus-admin-help-flow">
                        <div><b>1</b><span>Onboard Tenant</span></div>
                        <div><b>2</b><span>Set Tenant Defaults</span></div>
                        <div><b>3</b><span>Proceed to Studio / Validation</span></div>
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

            .nexus-admin-action-row {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                justify-content: flex-end;
            }

            .nexus-admin-table-wrap {
                margin-top: 16px;
                overflow-x: auto;
            }

            .nexus-admin-table {
                margin-bottom: 0;
                background: #ffffff;
            }

            .nexus-admin-table th {
                color: #173b8c;
                font-size: 12px;
                font-weight: 900;
                background: #eef6ff;
                white-space: nowrap;
            }

            .nexus-admin-table td {
                color: #27416f;
                font-size: 12px;
                font-weight: 650;
                vertical-align: middle;
            }

            .nexus-admin-muted {
                margin-top: 4px;
                color: #6b7c9b;
                font-size: 11px;
                font-weight: 650;
                line-height: 1.4;
            }

            .nexus-status-pill {
                display: inline-flex;
                padding: 5px 9px;
                border-radius: 999px;
                font-size: 10px;
                font-weight: 900;
                white-space: nowrap;
            }

            .nexus-status-pill.enabled {
                background: #ecfdf3;
                color: #16794c;
                border: 1px solid #bdebd2;
            }

            .nexus-status-pill.disabled {
                background: #fff0f0;
                color: #b42318;
                border: 1px solid #ffd1d1;
            }

            .nexus-admin-subtitle {
                margin: 8px 0 12px;
                color: #173b8c;
                font-size: 14px;
                font-weight: 950;
            }

            .nexus-governance-distribution-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 14px;
            }

            .nexus-governance-mini-table h4 {
                margin: 0 0 8px;
                color: #27416f;
                font-size: 13px;
                font-weight: 900;
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

                .nexus-governance-distribution-grid {
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
