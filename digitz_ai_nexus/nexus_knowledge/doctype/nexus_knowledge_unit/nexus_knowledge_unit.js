// Copyright (c) 2026, Techxcel Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nexus Knowledge Unit", {
	refresh(frm) {
		if (!frm.is_new() && ["Approved", "Active"].includes(frm.doc.status)) {
			frm.add_custom_button("Generate Chunks", () => {
				frappe.confirm(
					"Generate chunks for this Knowledge Unit? Existing chunks will be replaced.",
					() => {
						frappe.call({
							method: "digitz_ai_nexus.api.knowledge.generate_chunks",
							args: {
								knowledge_unit: frm.doc.name,
								replace_existing: 1
							},
							callback(r) {
								const data = r.message || {};
								frappe.msgprint({
									title: "Chunks Generated",
									message: `Created ${data.chunks_created || 0} chunks.`,
									indicator: "green"
								});
								frm.reload_doc();
							}
						});
					}
				);
			});

			frm.add_custom_button("Generate Embeddings", () => {
				frappe.call({
					method: "digitz_ai_nexus.api.embedding.generate_embeddings_for_unit",
					args: {
						knowledge_unit: frm.doc.name
					},
					callback(r) {
						const data = r.message || {};
						frappe.msgprint({
							title: "Embeddings Generated",
							message: `Updated ${data.updated || 0} chunks`,
							indicator: "green"
						});
						frm.reload_doc();
					}
				});
			});
		}
	}
});
