// Copyright (c) 2026, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nexus Business Unit", {
	refresh(frm) {
		frm.trigger("set_queries");
	},

	set_queries(frm) {
		frm.set_query("tenant", function() {
			return {
				filters: {
					enabled: 1
				}
			};
		});
	}
});
