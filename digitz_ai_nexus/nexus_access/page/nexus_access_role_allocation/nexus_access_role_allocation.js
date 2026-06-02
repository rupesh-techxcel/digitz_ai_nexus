frappe.pages['nexus-access-role-allocation'].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Nexus Access Role Allocation',
        single_column: true,
    });

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------
    const state = {
        roles: [],
        categories: [],
        assignments: [],
        selectedRole: null,
        pendingAssign: new Set(),
        pendingRemove: new Set(),
    };

    inject_nexus_ara_css();
    $(page.body).html(buildPageHTML());
    bindEvents();
    loadInitialData();

    // -----------------------------------------------------------------------
    // HTML
    // -----------------------------------------------------------------------
    function buildPageHTML() {
        return `
<div class="nexus-ara-wrap">

    <div class="nexus-admin-hero">
        <div>
            <div class="nexus-admin-badge">DIGITZ AI Nexus</div>
            <h2>Nexus Access Role Allocation</h2>
            <p>
                Assign <b>Nexus Access Categories</b> to Frappe Roles.
                Access Policies are never assigned directly to roles —
                they are inherited through Access Categories only.
            </p>
            <div class="nexus-ara-flow-pill">
                Role &nbsp;→&nbsp; Nexus Role Access Category &nbsp;→&nbsp; Nexus Access Category
                &nbsp;→&nbsp; Nexus Access Category Policy &nbsp;→&nbsp; Nexus Access Policy
            </div>
        </div>

        <div class="nexus-admin-hero-actions">
            <button class="btn btn-default" data-route-list="Nexus Access Policy">Access Policies</button>
            <button class="btn btn-default" data-route-list="Nexus Access Category">Access Categories</button>
            <button class="btn btn-default" data-route-list="Nexus Role Access Category">Role Assignments</button>
            <button class="btn btn-default" data-route-list="Nexus Channel Access Category">Channel Assignments</button>
        </div>
    </div>

    <div class="nexus-ara-layout">

        <!-- Left: Role list -->
        <div class="nexus-admin-card nexus-ara-roles-panel">
            <div class="nexus-admin-card-title">Frappe Roles</div>
            <div class="nexus-ara-roles-inner">
                <div id="ara_roles_loading" class="nexus-empty-state">Loading roles…</div>
                <div id="ara_role_list"></div>
            </div>
        </div>

        <!-- Right: Content -->
        <div>

            <div id="ara_placeholder" class="nexus-admin-card nexus-ara-placeholder">
                <div class="nexus-ara-placeholder-icon">←</div>
                <div>Select a role from the list to manage its Access Categories</div>
            </div>

            <div id="ara_role_content" style="display:none;">

                <!-- Role header -->
                <div class="nexus-admin-card" style="margin-bottom:18px;">
                    <div class="nexus-admin-section-head" style="margin-bottom:0;">
                        <div>
                            <div class="nexus-admin-card-title">Selected Role</div>
                            <div id="ara_selected_role_name" class="nexus-ara-role-title"></div>
                        </div>
                    </div>
                </div>

                <!-- Category assignment -->
                <div class="nexus-admin-card" style="margin-bottom:18px;">
                    <div class="nexus-admin-section-head">
                        <div>
                            <div class="nexus-admin-card-title">Access Category Assignment</div>
                            <p>Check to assign, uncheck to remove. Changes are not saved until you click Save.</p>
                        </div>
                        <div class="nexus-admin-action-row">
                            <span id="ara_pending_note" class="nexus-ara-pending-note" style="display:none;"></span>
                            <button id="ara_discard_btn" class="btn btn-default btn-sm">Discard</button>
                            <button id="ara_save_btn" class="btn btn-primary btn-sm">Save Assignment</button>
                        </div>
                    </div>

                    <div id="ara_categories_loading" class="nexus-empty-state" style="display:none;">Loading categories…</div>
                    <div id="ara_categories_list"></div>
                    <div id="ara_no_categories" class="nexus-empty-state" style="display:none;">
                        No Access Categories configured.
                        <a class="nexus-ara-link" data-route-new="Nexus Access Category">Create one</a>.
                    </div>
                </div>

                <!-- Effective policies preview -->
                <div class="nexus-admin-card" style="margin-bottom:18px;">
                    <div class="nexus-admin-section-head">
                        <div>
                            <div class="nexus-admin-card-title">Effective Access Policies</div>
                            <p>
                                Derived via Role → Category → Policy.
                                Preview only — no direct Role → Policy record is stored.
                            </p>
                        </div>
                        <div class="nexus-admin-action-row">
                            <button id="ara_refresh_policies_btn" class="btn btn-default btn-sm">Refresh</button>
                        </div>
                    </div>
                    <div id="ara_policies_loading" class="nexus-empty-state" style="display:none;">Computing…</div>
                    <div id="ara_policies_area"></div>
                    <div id="ara_no_policies" class="nexus-empty-state" style="display:none;">
                        No policies currently accessible. Assign an Access Category above.
                    </div>
                </div>

                <!-- Category detail panel -->
                <div id="ara_detail_card" class="nexus-admin-card" style="display:none; margin-bottom:18px;">
                    <div class="nexus-admin-section-head">
                        <div>
                            <div class="nexus-admin-card-title">Category Detail</div>
                            <div id="ara_detail_cat_name" class="nexus-ara-detail-cat-name"></div>
                        </div>
                        <div class="nexus-admin-action-row">
                            <button id="ara_close_detail_btn" class="btn btn-default btn-sm">Close</button>
                        </div>
                    </div>
                    <div id="ara_detail_area"></div>
                    <div id="ara_detail_empty" class="nexus-empty-state" style="display:none;">
                        No policies configured for this category.
                    </div>
                </div>

            </div>
        </div>
    </div>

</div>
        `;
    }

    // -----------------------------------------------------------------------
    // Events
    // -----------------------------------------------------------------------
    function bindEvents() {
        $(page.body).on('click', '[data-route-list]', function () {
            frappe.set_route('List', $(this).data('route-list'));
        });

        $(page.body).on('click', '[data-route-new]', function () {
            frappe.set_route('Form', $(this).data('route-new'), 'new');
        });

        $(page.body).on('click', '#ara_save_btn', saveAssignments);
        $(page.body).on('click', '#ara_discard_btn', discardChanges);
        $(page.body).on('click', '#ara_close_detail_btn', () => $('#ara_detail_card').hide());
        $(page.body).on('click', '#ara_refresh_policies_btn', () => {
            if (state.selectedRole) refreshEffectivePolicies();
        });
    }

    // -----------------------------------------------------------------------
    // Data loading
    // -----------------------------------------------------------------------
    function loadInitialData() {
        frappe.call({
            method: 'digitz_ai_nexus.api.nexus_access_role_allocation.get_access_role_allocation_data',
            args: {},
            callback(r) {
                $('#ara_roles_loading').hide();
                if (!r.message) return;
                state.roles = r.message.roles || [];
                state.categories = r.message.categories || [];
                renderRoleList();
            },
        });
    }

    function loadRoleData(role) {
        $('#ara_categories_loading').show();
        $('#ara_categories_list').empty();
        $('#ara_no_categories').hide();
        $('#ara_policies_area').empty();
        $('#ara_no_policies').hide();
        $('#ara_detail_card').hide();

        frappe.call({
            method: 'digitz_ai_nexus.api.nexus_access_role_allocation.get_access_role_allocation_data',
            args: { role },
            callback(r) {
                if (!r.message) return;
                state.assignments = r.message.assignments || [];
                $('#ara_categories_loading').hide();
                renderCategories();
                refreshEffectivePolicies();
            },
        });
    }

    // -----------------------------------------------------------------------
    // Role list
    // -----------------------------------------------------------------------
    function renderRoleList() {
        const $list = $('#ara_role_list');

        if (!state.roles.length) {
            $list.html('<div class="nexus-empty-state">No roles found.</div>');
            return;
        }

        $list.html(
            state.roles.map(role =>
                `<div class="nexus-kv-row nexus-ara-role-item" data-role="${escAttr(role)}">
                    <span>${esc(role)}</span>
                    <b class="nexus-ara-role-caret">›</b>
                </div>`
            ).join('')
        );

        $list.on('click', '.nexus-ara-role-item', function () {
            selectRole($(this).data('role'));
        });
    }

    function selectRole(role) {
        if (state.selectedRole === role) return;

        if (state.pendingAssign.size > 0 || state.pendingRemove.size > 0) {
            frappe.confirm(
                'You have unsaved changes. Discard them and switch role?',
                () => doSelectRole(role)
            );
            return;
        }

        doSelectRole(role);
    }

    function doSelectRole(role) {
        state.selectedRole = role;
        state.pendingAssign.clear();
        state.pendingRemove.clear();

        $('#ara_role_list .nexus-ara-role-item').removeClass('nexus-ara-role-active');
        $('#ara_role_list .nexus-ara-role-item').filter(function () {
            return $(this).data('role') === role;
        }).addClass('nexus-ara-role-active');

        $('#ara_placeholder').hide();
        $('#ara_role_content').show();
        $('#ara_selected_role_name').text(role);
        updatePendingNote();
        loadRoleData(role);
    }

    // -----------------------------------------------------------------------
    // Categories
    // -----------------------------------------------------------------------
    function renderCategories() {
        const $list = $('#ara_categories_list');
        const $no = $('#ara_no_categories');

        if (!state.categories.length) {
            $no.show();
            $list.empty();
            return;
        }

        $no.hide();

        const assignedNames = new Set(state.assignments.map(a => a.access_category));

        const rows = state.categories.map((cat, idx) => {
            const isAssigned = assignedNames.has(cat.name);
            const cbId = `ara_cb_${idx}`;
            const title = cat.title || cat.category_name || cat.name;

            return `
                <tr>
                    <td style="width:34px; text-align:center; vertical-align:middle;">
                        <input
                            type="checkbox"
                            class="ara-cat-checkbox"
                            id="${cbId}"
                            data-category="${escAttr(cat.name)}"
                            ${isAssigned ? 'checked' : ''}
                            style="width:15px; height:15px; cursor:pointer;"
                        >
                    </td>
                    <td style="vertical-align:middle;">
                        <label for="${cbId}" style="cursor:pointer; font-weight:850; color:#173b8c; font-size:13px; margin:0;">
                            ${esc(title)}
                        </label>
                        ${cat.description ? `<div class="nexus-admin-muted">${esc(cat.description)}</div>` : ''}
                    </td>
                    <td style="width:100px; text-align:right; vertical-align:middle;">
                        <span class="nexus-status-pill ${isAssigned ? 'enabled' : 'disabled'} ara-cat-status">
                            ${isAssigned ? 'Assigned' : 'Not Set'}
                        </span>
                    </td>
                    <td style="width:80px; text-align:right; vertical-align:middle;">
                        <button class="btn btn-xs btn-default ara-cat-detail-btn" data-category="${escAttr(cat.name)}">
                            Details
                        </button>
                    </td>
                </tr>
            `;
        });

        $list.html(`
            <table class="table table-bordered nexus-admin-table" style="margin-bottom:0;">
                <thead>
                    <tr>
                        <th style="width:34px;"></th>
                        <th>Access Category</th>
                        <th style="width:100px; text-align:right;">Status</th>
                        <th style="width:80px;"></th>
                    </tr>
                </thead>
                <tbody>${rows.join('')}</tbody>
            </table>
        `);

        $list.off('change', '.ara-cat-checkbox').on('change', '.ara-cat-checkbox', function () {
            const category = $(this).data('category');
            const checked = $(this).is(':checked');
            const existingRecord = state.assignments.find(a => a.access_category === category);

            if (checked) {
                state.pendingAssign.add(category);
                if (existingRecord) state.pendingRemove.delete(existingRecord.name);
            } else {
                state.pendingAssign.delete(category);
                if (existingRecord) state.pendingRemove.add(existingRecord.name);
            }

            const $pill = $(this).closest('tr').find('.ara-cat-status');
            if (state.pendingAssign.has(category)) {
                $pill.attr('class', 'nexus-status-pill nexus-ara-pill-pending ara-cat-status').text('Pending +');
            } else if (existingRecord && state.pendingRemove.has(existingRecord.name)) {
                $pill.attr('class', 'nexus-status-pill nexus-ara-pill-removing ara-cat-status').text('Pending −');
            } else if (checked) {
                $pill.attr('class', 'nexus-status-pill enabled ara-cat-status').text('Assigned');
            } else {
                $pill.attr('class', 'nexus-status-pill disabled ara-cat-status').text('Not Set');
            }

            updatePendingNote();
        });

        $list.off('click', '.ara-cat-detail-btn').on('click', '.ara-cat-detail-btn', function (e) {
            e.stopPropagation();
            loadCategoryDetail($(this).data('category'));
        });
    }

    function updatePendingNote() {
        const total = state.pendingAssign.size + state.pendingRemove.size;
        const $note = $('#ara_pending_note');
        if (total > 0) {
            $note.show().text(`${total} unsaved change${total !== 1 ? 's' : ''}`);
        } else {
            $note.hide();
        }
    }

    // -----------------------------------------------------------------------
    // Save / discard
    // -----------------------------------------------------------------------
    function saveAssignments() {
        if (!state.selectedRole) {
            frappe.msgprint('No role selected.');
            return;
        }

        const toAssign = Array.from(state.pendingAssign);
        const toRemove = Array.from(state.pendingRemove);

        if (!toAssign.length && !toRemove.length) {
            frappe.show_alert({ message: 'No changes to save.', indicator: 'blue' });
            return;
        }

        frappe.call({
            method: 'digitz_ai_nexus.api.nexus_access_role_allocation.save_role_access_categories',
            args: {
                role: state.selectedRole,
                categories_to_assign: JSON.stringify(toAssign),
                assignments_to_remove: JSON.stringify(toRemove),
            },
            callback(r) {
                if (r.message && r.message.status === 'success') {
                    state.assignments = r.message.assignments || [];
                    state.pendingAssign.clear();
                    state.pendingRemove.clear();

                    frappe.show_alert({
                        message: `Access categories saved for role: ${state.selectedRole}`,
                        indicator: 'green',
                    });

                    updatePendingNote();
                    renderCategories();
                    refreshEffectivePolicies();
                }
            },
        });
    }

    function discardChanges() {
        if (!state.pendingAssign.size && !state.pendingRemove.size) return;

        state.pendingAssign.clear();
        state.pendingRemove.clear();
        updatePendingNote();
        renderCategories();
        frappe.show_alert({ message: 'Changes discarded.', indicator: 'orange' });
    }

    // -----------------------------------------------------------------------
    // Effective policies preview
    // -----------------------------------------------------------------------
    function refreshEffectivePolicies() {
        if (!state.selectedRole) return;

        $('#ara_policies_loading').show();
        $('#ara_policies_area').empty();
        $('#ara_no_policies').hide();

        frappe.call({
            method: 'digitz_ai_nexus.api.nexus_access_role_allocation.get_effective_policies_for_role',
            args: { role: state.selectedRole },
            callback(r) {
                $('#ara_policies_loading').hide();
                if (!r.message) return;

                const policies = r.message.policies || [];

                if (!policies.length) {
                    $('#ara_no_policies').show();
                    return;
                }

                const chips = policies.map(p => {
                    const cls = p.is_primitive ? 'nexus-ara-chip-primitive' : 'nexus-ara-chip';
                    return `<span class="${cls}">${esc(p.policy_name || p.name)}${p.is_primitive ? ' ★' : ''}</span>`;
                }).join('');

                $('#ara_policies_area').html(`
                    <div style="display:flex; flex-wrap:wrap; gap:6px; padding:8px 0 4px 0;">${chips}</div>
                    <div class="nexus-admin-muted" style="padding:4px 0 8px;">
                        ${policies.length} polic${policies.length !== 1 ? 'ies' : 'y'} accessible
                        through assigned categories. No direct Role → Policy record is stored.
                    </div>
                `);
            },
        });
    }

    // -----------------------------------------------------------------------
    // Category detail
    // -----------------------------------------------------------------------
    function loadCategoryDetail(category) {
        $('#ara_detail_card').show();
        $('#ara_detail_cat_name').text(category);
        $('#ara_detail_area').empty();
        $('#ara_detail_empty').hide();

        frappe.call({
            method: 'digitz_ai_nexus.api.nexus_access_role_allocation.get_category_policies',
            args: { category },
            callback(r) {
                if (!r.message) return;

                const policies = r.message.policies || [];

                if (!policies.length) {
                    $('#ara_detail_empty').show();
                    return;
                }

                const rows = policies.map(p => `
                    <tr>
                        <td>
                            <b style="color:#173b8c;">${esc(p.policy_name || p.name)}</b>
                            ${p.description ? `<div class="nexus-admin-muted">${esc(p.description)}</div>` : ''}
                        </td>
                        <td>${esc(p.access_level || '-')}</td>
                        <td>${esc(p.sensitivity || '-')}</td>
                        <td>
                            ${p.is_primitive
                                ? `<span class="nexus-status-pill nexus-ara-pill-primitive">Primitive ★</span>`
                                : `<span class="nexus-status-pill ${p.disabled ? 'disabled' : 'enabled'}">${p.disabled ? 'Disabled' : 'Active'}</span>`
                            }
                        </td>
                    </tr>
                `).join('');

                $('#ara_detail_area').html(`
                    <table class="table table-bordered nexus-admin-table" style="margin-bottom:0;">
                        <thead>
                            <tr>
                                <th>Policy Name</th>
                                <th>Access Level</th>
                                <th>Sensitivity</th>
                                <th style="width:110px;">Status</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                    <div class="nexus-admin-muted" style="padding:8px 0 4px;">
                        ${policies.length} polic${policies.length !== 1 ? 'ies' : 'y'} in this category.
                        ★ = primitive (Public only, system-defined).
                    </div>
                `);
            },
        });
    }

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------
    function esc(str) {
        return frappe.utils.escape_html(String(str || ''));
    }

    function escAttr(str) {
        return String(str || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
};


// ---------------------------------------------------------------------------
// CSS — matches nexus-admin design language exactly
// ---------------------------------------------------------------------------
function inject_nexus_ara_css() {
    if ($('#nexus_ara_css').length) return;

    $('head').append(`
        <style id="nexus_ara_css">

            /* ---- Shared admin tokens (safe to re-inject) ---- */

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

            .nexus-admin-hero-actions .btn {
                border-radius: 999px;
                font-weight: 850;
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

            .nexus-admin-action-row {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                justify-content: flex-end;
                align-items: center;
            }

            .nexus-admin-action-row .btn {
                border-radius: 999px;
                font-weight: 850;
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

            /* ---- Page-specific: nexus-ara-* ---- */

            .nexus-ara-wrap {
                padding: 12px;
            }

            .nexus-ara-layout {
                display: grid;
                grid-template-columns: 260px 1fr;
                gap: 18px;
                align-items: start;
            }

            .nexus-ara-roles-panel {
                position: sticky;
                top: 64px;
            }

            .nexus-ara-roles-inner {
                max-height: 540px;
                overflow-y: auto;
                padding-right: 2px;
            }

            .nexus-ara-role-item {
                margin-bottom: 6px;
                cursor: pointer;
                transition: background 0.12s, border-color 0.12s;
            }

            .nexus-ara-role-item:hover {
                background: #eef6ff !important;
                border-color: rgba(33, 77, 187, 0.35) !important;
            }

            .nexus-ara-role-active {
                background: #eef6ff !important;
                border-color: rgba(33, 77, 187, 0.55) !important;
            }

            .nexus-ara-role-active span {
                color: #173b8c !important;
                font-weight: 950 !important;
            }

            .nexus-ara-role-caret {
                color: #214dbb;
                font-size: 16px;
                font-weight: 900;
            }

            .nexus-ara-role-title {
                font-size: 22px;
                font-weight: 950;
                color: #102b67;
                margin-top: 4px;
            }

            .nexus-ara-placeholder {
                text-align: center;
                padding: 48px 20px;
            }

            .nexus-ara-placeholder-icon {
                font-size: 28px;
                margin-bottom: 12px;
                color: #b0c4de;
            }

            .nexus-ara-placeholder > div:last-child {
                color: #53688f;
                font-size: 14px;
                font-weight: 700;
            }

            .nexus-ara-flow-pill {
                display: inline-block;
                margin-top: 12px;
                padding: 7px 14px;
                border-radius: 999px;
                background: rgba(33, 77, 187, 0.08);
                border: 1px solid rgba(33, 77, 187, 0.18);
                color: #214dbb;
                font-size: 11px;
                font-weight: 800;
                font-family: monospace;
                letter-spacing: 0.02em;
            }

            .nexus-ara-pending-note {
                display: inline-flex;
                align-items: center;
                padding: 5px 12px;
                border-radius: 999px;
                background: #fff7e6;
                border: 1px solid #f2d49b;
                color: #8a5d00;
                font-size: 11px;
                font-weight: 900;
                white-space: nowrap;
            }

            .nexus-ara-chip,
            .nexus-ara-chip-primitive {
                display: inline-flex;
                align-items: center;
                padding: 5px 12px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 900;
                white-space: nowrap;
            }

            .nexus-ara-chip {
                background: #eef6ff;
                color: #173b8c;
                border: 1px solid rgba(33, 77, 187, 0.22);
            }

            .nexus-ara-chip-primitive {
                background: #fff7e6;
                color: #8a5d00;
                border: 1px solid #f2d49b;
            }

            .nexus-ara-pill-pending {
                background: #ecfdf3;
                color: #16794c;
                border: 1px solid #bdebd2;
            }

            .nexus-ara-pill-removing {
                background: #fff0f0;
                color: #b42318;
                border: 1px solid #ffd1d1;
            }

            .nexus-ara-pill-primitive {
                background: #eef6ff;
                color: #214dbb;
                border: 1px solid rgba(33, 77, 187, 0.22);
            }

            .nexus-ara-detail-cat-name {
                font-size: 16px;
                font-weight: 900;
                color: #102b67;
                margin-top: 4px;
            }

            .nexus-ara-link {
                color: #214dbb;
                cursor: pointer;
                font-weight: 850;
                text-decoration: none;
            }

            .nexus-ara-link:hover {
                text-decoration: underline;
            }

            /* ---- Responsive ---- */

            @media (max-width: 1100px) {
                .nexus-ara-layout {
                    grid-template-columns: 220px 1fr;
                }
            }

            @media (max-width: 820px) {
                .nexus-ara-layout {
                    grid-template-columns: 1fr;
                }

                .nexus-ara-roles-panel {
                    position: static;
                }

                .nexus-ara-roles-inner {
                    max-height: 280px;
                }
            }

            @media (max-width: 760px) {
                .nexus-admin-hero {
                    flex-direction: column;
                }

                .nexus-admin-section-head {
                    flex-direction: column;
                }

                .nexus-admin-hero-actions .btn {
                    width: 100%;
                }
            }

        </style>
    `);
}
