// Copyright (c) 2026, Digitz AI and contributors
// For license information, please see license.txt

frappe.ui.form.on('Knowledge Profile', {
    setup(frm) {
        frm.set_query('tenant', () => ({
            filters: { disabled: 0 },
        }));
    },
});

frappe.listview_settings['Knowledge Profile'] = {
    add_fields: ['tenant', 'enabled'],

    filters: [['tenant', '!=', '']],

    get_indicator(doc) {
        if (!doc.enabled) return [__('Disabled'), 'grey', 'enabled,=,0'];
        return [__('Active'), 'green', 'enabled,=,1'];
    },
};
