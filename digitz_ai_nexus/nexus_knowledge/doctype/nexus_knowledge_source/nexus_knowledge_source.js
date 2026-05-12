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

        frm.add_custom_button(__("Chunk Observatory"), function () {
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
                                `
                                <div style="line-height:1.8;">
                                    <div><b>Knowledge Unit:</b> ${r.message.knowledge_unit || "-"}</div>
                                    <div><b>Chunks Created:</b> ${r.message.chunk_count || 0}</div>
                                    <div><b>Processing Version:</b> ${r.message.processing_version || 0}</div>
                                    <div><b>Diagnostics:</b> ${r.message.diagnostics_status || "-"}</div>
                                    <div><b>Retrieval Ready:</b> ${r.message.retrieval_ready ? "Yes" : "No"}</div>
                                </div>
                                `
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

            if (frm.doc.hasOwnProperty("processing_version")) {
                frm.set_value("processing_version", data.processing_version || 0);
            }

            if (frm.doc.hasOwnProperty("active_chunk_count")) {
                frm.set_value("active_chunk_count", data.active_chunk_count || 0);
            }

            if (frm.doc.hasOwnProperty("diagnostics_status")) {
                frm.set_value("diagnostics_status", data.diagnostics_status || "Pending");
            }

            if (frm.doc.hasOwnProperty("retrieval_ready")) {
                frm.set_value("retrieval_ready", data.retrieval_ready || 0);
            }

            frm.set_value("last_processed_on", data.last_processed_on || frm.doc.last_processed_on);
            frm.set_value("generated_knowledge_unit", data.generated_knowledge_unit || frm.doc.generated_knowledge_unit);
            frm.set_value("extracted_text_preview", data.extracted_text_preview || frm.doc.extracted_text_preview);

            render_generated_chunks(frm, data);

            frm.refresh_fields();

            frappe.show_alert({
                message: __("Chunk Observatory refreshed."),
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
        knowledge_source: frm.doc.name
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
                reqd: 1
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
                    const answer = result.answer || __("No answer returned.");
                    const confidence = result.confidence || 0;

                    dialog.fields_dict.result_html.$wrapper.html(`
                        <div style="
                            margin-top: 16px;
                            padding: 16px;
                            border-radius: 14px;
                            border: 1px solid #d8e3f8;
                            background: #f8fbff;
                        ">
                            <div style="font-weight:700;margin-bottom:8px;">
                                ${__("Grounded Validation")}
                            </div>

                            <div style="margin-bottom:10px;">
                                <b>${__("Confidence")}:</b> ${confidence}
                            </div>

                            <div style="
                                white-space: pre-wrap;
                                line-height:1.6;
                            ">
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

    frm.fields_dict.generated_chunks_html.$wrapper.html(`
        <div style="
            padding: 18px;
            border-radius: 18px;
            border: 1px dashed #d8e3f8;
            background: linear-gradient(180deg,#f8fbff 0%,#ffffff 100%);
            color: #64748b;
        ">
            ${__("Refresh the Chunk Observatory to inspect generated chunks and diagnostics.")}
        </div>
    `);
}


function render_generated_chunks(frm, data) {
    if (!frm.fields_dict.generated_chunks_html) {
        return;
    }

    const chunks = data.chunks || [];

    if (!chunks.length) {
        frm.fields_dict.generated_chunks_html.$wrapper.html(`
            <div style="
                padding:16px;
                border-radius:14px;
                border:1px dashed #f3d37a;
                background:#fffaf0;
                color:#92400e;
            ">
                ${__("No chunks available for this source.")}
            </div>
        `);
        return;
    }

    const retrievalReady = data.retrieval_ready
        ? `<span style="color:#15803d;font-weight:700;">✓ Retrieval Ready</span>`
        : `<span style="color:#b91c1c;font-weight:700;">⚠ Retrieval Not Ready</span>`;

    const summaryCards = `
        <div style="
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
            gap:12px;
            margin-bottom:18px;
        ">
            ${summary_card("Processing Version", data.processing_version || 0)}
            ${summary_card("Chunk Count", data.chunk_count || 0)}
            ${summary_card("Active Chunks", data.active_chunk_count || 0)}
            ${summary_card("Embedded", data.embedded_count || 0)}
            ${summary_card("Missing Embeddings", data.missing_embedding_count || 0)}
            ${summary_card("Duplicate Chunks", data.duplicate_count || 0)}
            ${summary_card("Diagnostics", data.diagnostics_status || "-")}
            ${summary_card("Retrieval", retrievalReady)}
        </div>
    `;

    const rows = chunks.map(chunk => {
        const content = chunk.content || "";
        const preview = content.length > 450
            ? content.substring(0, 450) + "..."
            : content;

        const embeddingBadge = chunk.has_embedding
            ? badge("Embedded", "#ecfdf3", "#15803d", "#86efac")
            : badge("Missing", "#fef2f2", "#b91c1c", "#fecaca");

        const diagnosticsStatus = chunk.diagnostics_status || "Pending";

        let diagnosticsBadge = badge(
            diagnosticsStatus,
            "#f8fafc",
            "#475569",
            "#cbd5e1"
        );

        if (diagnosticsStatus === "Healthy") {
            diagnosticsBadge = badge("Healthy", "#ecfdf3", "#15803d", "#86efac");
        }

        if (diagnosticsStatus === "Warning") {
            diagnosticsBadge = badge("Warning", "#fff7ed", "#c2410c", "#fdba74");
        }

        if (diagnosticsStatus === "Critical") {
            diagnosticsBadge = badge("Critical", "#fef2f2", "#b91c1c", "#fecaca");
        }

        const archivedBadge = chunk.archived
            ? badge("Archived", "#f1f5f9", "#475569", "#cbd5e1")
            : badge("Active", "#eff6ff", "#1d4ed8", "#93c5fd");

        return `
            <div style="
                margin-bottom:14px;
                padding:16px;
                border-radius:16px;
                border:1px solid #d8e3f8;
                background:#ffffff;
                box-shadow:0 4px 18px rgba(15,23,42,0.05);
            ">
                <div style="
                    display:flex;
                    justify-content:space-between;
                    gap:12px;
                    margin-bottom:12px;
                    flex-wrap:wrap;
                ">
                    <div style="
                        font-size:15px;
                        font-weight:800;
                        color:#214dbb;
                    ">
                        Chunk ${chunk.chunk_index}
                    </div>

                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        ${embeddingBadge}
                        ${diagnosticsBadge}
                        ${archivedBadge}
                    </div>
                </div>

                <div style="
                    display:grid;
                    grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
                    gap:10px;
                    margin-bottom:12px;
                    font-size:12px;
                    color:#475569;
                ">
                    <div><b>Characters:</b> ${chunk.character_count || 0}</div>
                    <div><b>Version:</b> ${chunk.source_version || 1}</div>
                    <div><b>Disabled:</b> ${chunk.disabled ? "Yes" : "No"}</div>
                </div>

                <div style="
                    white-space:pre-wrap;
                    line-height:1.6;
                    color:#334155;
                    font-size:13px;
                ">
                    ${frappe.utils.escape_html(preview)}
                </div>

                <div style="margin-top:12px;">
                    <a class="btn btn-xs btn-default"
                       href="/app/nexus-knowledge-chunk/${encodeURIComponent(chunk.name)}">
                        ${__("Open Full Chunk")}
                    </a>
                </div>
            </div>
        `;
    }).join("");

    frm.fields_dict.generated_chunks_html.$wrapper.html(`
        <div style="
            padding:16px;
            border-radius:18px;
            border:1px solid #d8e3f8;
            background:linear-gradient(180deg,#f8fbff 0%,#ffffff 100%);
        ">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:16px;
                flex-wrap:wrap;
                gap:12px;
            ">
                <div>
                    <div style="
                        font-size:18px;
                        font-weight:800;
                        color:#1e3a8a;
                    ">
                        ${__("Chunk Observatory")}
                    </div>

                    <div style="
                        margin-top:4px;
                        font-size:12px;
                        color:#64748b;
                    ">
                        ${__("Governed retrieval observability and diagnostics")}
                    </div>
                </div>
            </div>

            ${summaryCards}

            ${rows}
        </div>
    `);
}


function summary_card(title, value) {
    return `
        <div style="
            padding:14px;
            border-radius:14px;
            border:1px solid #d8e3f8;
            background:#ffffff;
            box-shadow:0 4px 14px rgba(15,23,42,0.04);
        ">
            <div style="
                font-size:12px;
                color:#64748b;
                margin-bottom:6px;
            ">
                ${title}
            </div>

            <div style="
                font-size:18px;
                font-weight:800;
                color:#1e3a8a;
            ">
                ${value}
            </div>
        </div>
    `;
}


function badge(label, bg, color, border) {
    return `
        <span style="
            padding:4px 10px;
            border-radius:999px;
            background:${bg};
            color:${color};
            border:1px solid ${border};
            font-size:11px;
            font-weight:700;
        ">
            ${label}
        </span>
    `;
}