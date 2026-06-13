// Copyright (c) 2026, Digitz AI and contributors
// For license information, please see license.txt

frappe.ui.form.on('Nexus Access Category', {
    setup(frm) {
        frm.set_query('tenant', () => ({
            filters: { disabled: 0 },
        }));

        frm.set_query('access_policy', 'allowed_policies', () => ({
            filters: frm.doc.tenant ? { tenant: frm.doc.tenant } : {},
        }));
    },
});

frappe.listview_settings['Nexus Access Category'] = {
    add_fields: ['tenant', 'disabled', 'priority'],

    filters: [['tenant', '!=', '']],

    get_indicator(doc) {
        if (doc.disabled) return [__('Disabled'), 'grey', 'disabled,=,1'];
        return [__('Active'), 'green', 'disabled,=,0'];
    },
};
