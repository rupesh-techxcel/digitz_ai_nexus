// Copyright (c) 2026, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nexus Tenant", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Setup Defaults"), function () {
                frappe.confirm(
                    __("This will create default channels, categories, agent profile, "
                        + "access governance, and Sales Companion for tenant <b>{0}</b>. "
                        + "Existing records will not be overwritten.<br><br>Continue?",
                        [frm.doc.tenant_name || frm.doc.name]),
                    function () {
                        frappe.show_progress(__("Setting up defaults…"), 0, 100, __("Please wait"));

                        frappe.call({
                            method: "digitz_ai_nexus_live.api.tenant_setup.seed_tenant_defaults",
                            args: { tenant: frm.doc.name },
                            callback(r) {
                                frappe.hide_progress();
                                if (r.message && r.message.success) {
                                    frappe.show_alert({
                                        message: __("Defaults seeded for {0}.", [frm.doc.tenant_name || frm.doc.name]),
                                        indicator: "green",
                                    }, 5);
                                    frm.reload_doc();
                                }
                            },
                            error() {
                                frappe.hide_progress();
                            },
                        });
                    }
                );
            }, __("Actions"));
        }
    },
});
