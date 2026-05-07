frappe.ui.form.on("Nexus Knowledge Source", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Process Source"), function () {
                frappe.confirm(
                    __("This will regenerate chunks and embeddings for this source. Continue?"),
                    function () {
                        frappe.call({
                            method: "digitz_ai_nexus.api.knowledge_source.process",
                            args: {
                                source_name: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __("Processing knowledge source..."),
                            callback: function (r) {
                                if (r.message && r.message.status === "success") {
                                    frappe.msgprint({
                                        title: __("Processed"),
                                        message: __("Created {0} chunks.", [r.message.chunk_count]),
                                        indicator: "green"
                                    });
                                    frm.reload_doc();
                                } else {
                                    frappe.msgprint({
                                        title: __("Processing Failed"),
                                        message: r.message && r.message.error
                                            ? r.message.error
                                            : __("Knowledge source processing failed."),
                                        indicator: "red"
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }).addClass("btn-primary");
        }
    }
});