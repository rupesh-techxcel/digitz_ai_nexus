frappe.ui.form.on("Nexus Knowledge Source", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Process Source"), function () {
            process_knowledge_source(frm);
        }).addClass("btn-primary");

        frm.add_custom_button(__("Refresh Quality Panel"), function () {
            refresh_quality_panel(frm);
        }, __("Source Quality"));

        frm.add_custom_button(__("Preview Extracted Text"), function () {
            show_extracted_text_preview(frm);
        }, __("Source Quality"));

        frm.add_custom_button(__("Open Knowledge Unit"), function () {
            open_generated_knowledge_unit(frm);
        }, __("Source Quality"));

        frm.add_custom_button(__("Open Generated Chunks"), function () {
            open_generated_chunks(frm);
        }, __("Source Quality"));

        frm.add_custom_button(__("Test This Source"), function () {
            test_this_source(frm);
        }, __("Source Quality"));

        render_generated_chunks_placeholder(frm);
    }
});


function process_knowledge_source(frm) {
    frappe.confirm(
        __("This will extract text and create Knowledge Unit / Chunks for this source. Continue?"),
        function () {
            frappe.call({
                method: "digitz_ai_nexus.services.ingestion.processor.process_knowledge_source",
                args: {
                    source_name: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Processing knowledge source..."),
                callback: function (r) {
                    if (r.message && r.message.status === "success") {
                        frappe.msgprint({
                            title: __("Processed"),
                            message: __(
                                "Knowledge Source processed successfully.<br><br>Knowledge Unit: {0}<br>Chunks Created: {1}",
                                [r.message.knowledge_unit || "-", r.message.chunk_count || 0]
                            ),
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
}


function refresh_quality_panel(frm) {
    frappe.call({                
        method: "digitz_ai_nexus.nexus_knowledge.doctype.nexus_knowledge_source.nexus_knowledge_source.get_source_quality_panel",
        args: {
            source_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __("Refreshing source quality panel..."),
        callback: function (r) {
            if (!r.message) {
                frappe.msgprint({
                    title: __("No Data"),
                    message: __("No quality panel data returned."),
                    indicator: "orange"
                });
                return;
            }

            const data = r.message;

            frm.set_value("processing_status", data.processing_status || frm.doc.processing_status);
            frm.set_value("embedding_status", data.embedding_status || frm.doc.embedding_status);
            frm.set_value("chunk_count", data.chunk_count || 0);
            frm.set_value("last_processed_on", data.last_processed_on || data.last_processed_time || frm.doc.last_processed_on);
            frm.set_value("generated_knowledge_unit", data.generated_knowledge_unit || frm.doc.generated_knowledge_unit);
            frm.set_value("extracted_text_preview", data.extracted_text_preview || frm.doc.extracted_text_preview);

            render_generated_chunks(frm, data.chunks || []);

            frm.refresh_fields();

            frappe.show_alert({
                message: __("Source quality panel refreshed."),
                indicator: "green"
            });
        }
    });
}


function show_extracted_text_preview(frm) {
    const preview = frm.doc.extracted_text_preview || frm.doc.manual_content || "";

    if (!preview) {
        frappe.msgprint({
            title: __("No Preview Available"),
            message: __("No extracted text preview is available for this source."),
            indicator: "orange"
        });
        return;
    }

    const dialog = new frappe.ui.Dialog({
        title: __("Extracted Text Preview"),
        size: "large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "preview_html"
            }
        ]
    });

    dialog.fields_dict.preview_html.$wrapper.html(`
        <div style="
            max-height: 560px;
            overflow: auto;
            padding: 16px;
            border: 1px solid #d8e3f8;
            border-radius: 14px;
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
            color: #1f2937;
            white-space: pre-wrap;
            line-height: 1.65;
            font-size: 13px;
        ">${frappe.utils.escape_html(preview)}</div>
    `);

    dialog.show();
}


function open_generated_knowledge_unit(frm) {
    if (!frm.doc.generated_knowledge_unit) {
        frappe.msgprint({
            title: __("Not Available"),
            message: __("No generated Knowledge Unit is linked to this source yet."),
            indicator: "orange"
        });
        return;
    }

    frappe.set_route("Form", "Nexus Knowledge Unit", frm.doc.generated_knowledge_unit);
}


function open_generated_chunks(frm) {
    if (!frm.doc.generated_knowledge_unit) {
        frappe.msgprint({
            title: __("Not Available"),
            message: __("No generated Knowledge Unit is linked to this source yet."),
            indicator: "orange"
        });
        return;
    }

    frappe.set_route("List", "Nexus Knowledge Chunk", {
        knowledge_unit: frm.doc.generated_knowledge_unit
    });
}


function test_this_source(frm) {
    if (!frm.doc.generated_knowledge_unit) {
        frappe.msgprint({
            title: __("Process Source First"),
            message: __("Please process this source before testing it."),
            indicator: "orange"
        });
        return;
    }

    const dialog = new frappe.ui.Dialog({
        title: __("Test This Source"),
        size: "large",
        fields: [
            {
                fieldtype: "Small Text",
                fieldname: "test_query",
                label: __("Test Query"),
                reqd: 1,
                description: __("Ask a question that should be answered from this knowledge source.")
            },
            {
                fieldtype: "HTML",
                fieldname: "result_html"
            }
        ],
        primary_action_label: __("Run Test"),
        primary_action(values) {
            frappe.call({
                method: "digitz_ai_nexus.api.query.ask",
                args: {
                    payload: {
                        query: values.test_query,
                        tenant: frm.doc.tenant,
                        business_unit: frm.doc.business_unit,
                        project: frm.doc.project,
                        context: frm.doc.context,
                        sub_context: frm.doc.sub_context,
                        entity_type: frm.doc.entity_type,
                        entity: frm.doc.entity,
                        topic: frm.doc.topic,
                        source: frm.doc.name,
                        knowledge_unit: frm.doc.generated_knowledge_unit,
                        response_mode: "qa",
                        top_k: 5,
                        user: {
                            user_id: frappe.session.user,
                            roles: frappe.user_roles || []
                        }
                    }
                },
                freeze: true,
                freeze_message: __("Testing source..."),
                callback(r) {
                    const result = r.message || {};
                    const answer = result.answer || result.message || __("No answer returned.");
                    const confidence = result.confidence || 0;

                    dialog.fields_dict.result_html.$wrapper.html(`
                        <div style="
                            margin-top: 16px;
                            padding: 16px;
                            border-radius: 14px;
                            border: 1px solid #d8e3f8;
                            background: #f8fbff;
                        ">
                            <div style="font-weight: 700; margin-bottom: 8px;">
                                ${__("Test Result")}
                            </div>
                            <div style="margin-bottom: 8px;">
                                <b>${__("Confidence")}:</b> ${frappe.utils.escape_html(String(confidence))}
                            </div>
                            <div style="white-space: pre-wrap; line-height: 1.6;">
                                ${frappe.utils.escape_html(answer)}
                            </div>
                        </div>
                    `);

                    frm.set_value("last_test_query", values.test_query);
                    frm.set_value("last_test_result", JSON.stringify(result, null, 2));
                    frm.save();
                }
            });
        }
    });

    dialog.show();
}


function render_generated_chunks_placeholder(frm) {
    if (!frm.fields_dict.generated_chunks_html) {
        return;
    }

    if (!frm.doc.generated_knowledge_unit) {
        frm.fields_dict.generated_chunks_html.$wrapper.html(`
            <div style="
                padding: 16px;
                border: 1px dashed #d8e3f8;
                border-radius: 14px;
                background: #f8fbff;
                color: #64748b;
            ">
                ${__("No generated chunks available yet. Process the source first.")}
            </div>
        `);
        return;
    }

    frm.fields_dict.generated_chunks_html.$wrapper.html(`
        <div style="
            padding: 16px;
            border: 1px dashed #d8e3f8;
            border-radius: 14px;
            background: #f8fbff;
            color: #64748b;
        ">
            ${__("Click Refresh Quality Panel to load generated chunks preview.")}
        </div>
    `);
}


function render_generated_chunks(frm, chunks) {
    if (!frm.fields_dict.generated_chunks_html) {
        return;
    }

    if (!chunks || !chunks.length) {
        frm.fields_dict.generated_chunks_html.$wrapper.html(`
            <div style="
                padding: 16px;
                border: 1px dashed #d8e3f8;
                border-radius: 14px;
                background: #fffaf0;
                color: #92400e;
            ">
                ${__("No chunks found for this source.")}
            </div>
        `);
        return;
    }

    const rows = chunks.map((chunk, index) => {
        const content = chunk.content || chunk.chunk_text || "";
        const short_content = content.length > 600
            ? content.substring(0, 600) + "..."
            : content;

        const embedding_status = chunk.embedding || chunk.embedding_status === "Completed"
            ? __("Embedded")
            : __("Pending");

        return `
            <div style="
                margin-bottom: 12px;
                padding: 14px;
                border: 1px solid #d8e3f8;
                border-radius: 14px;
                background: #ffffff;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
            ">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    gap: 12px;
                    margin-bottom: 8px;
                ">
                    <div style="font-weight: 700; color: #214dbb;">
                        ${__("Chunk")} ${chunk.chunk_index || index + 1}
                    </div>
                    <div style="
                        font-size: 12px;
                        padding: 3px 9px;
                        border-radius: 999px;
                        background: #fff6d8;
                        color: #8a5a00;
                        border: 1px solid #f3d37a;
                    ">
                        ${embedding_status}
                    </div>
                </div>

                <div style="
                    white-space: pre-wrap;
                    line-height: 1.55;
                    font-size: 13px;
                    color: #334155;
                ">${frappe.utils.escape_html(short_content)}</div>

                <div style="margin-top: 10px;">
                    <a class="btn btn-xs btn-default"
                       href="/app/nexus-knowledge-chunk/${encodeURIComponent(chunk.name)}">
                        ${__("Open Chunk")}
                    </a>
                </div>
            </div>
        `;
    }).join("");

    frm.fields_dict.generated_chunks_html.$wrapper.html(`
        <div style="
            padding: 14px;
            border: 1px solid #d8e3f8;
            border-radius: 16px;
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
        ">
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 14px;
            ">
                <div>
                    <div style="font-size: 15px; font-weight: 800; color: #1e3a8a;">
                        ${__("Generated Chunks")}
                    </div>
                    <div style="font-size: 12px; color: #64748b;">
                        ${chunks.length} ${__("chunk(s) generated from this source")}
                    </div>
                </div>
            </div>

            ${rows}
        </div>
    `);
}