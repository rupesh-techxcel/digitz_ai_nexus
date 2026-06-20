frappe.pages["nexus-knowledge-gap-review"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Knowledge Gap Review",
		single_column: true,
	});

	new NexusKnowledgeGapReview(page, wrapper);
};

class NexusKnowledgeGapReview {
	constructor(page, wrapper) {
		this.page = page;
		this.wrapper = wrapper;
		this.state = {
			tenant: null,
			status: null,
			gap_type: null,
			relevant_only: false,
			gaps: [],
			counts: {},
		};
		this._setup_filters();
		this._setup_body();
		this._load();
	}

	// ── Filter bar ───────────────────────────────────────────────────────────────

	_setup_filters() {
		const page = this.page;

		this._tenant_field = page.add_field({
			fieldname: "tenant",
			label: "Tenant",
			fieldtype: "Link",
			options: "Nexus Tenant",
			change: () => {
				this.state.tenant = this._tenant_field.get_value() || null;
				this._load();
			},
		});

		this._status_field = page.add_field({
			fieldname: "status",
			label: "Status",
			fieldtype: "Select",
			options: "\nNew\nUnder Review\nWatching\nActioned\nDismissed",
			change: () => {
				this.state.status = this._status_field.get_value() || null;
				this._load();
			},
		});

		this._type_field = page.add_field({
			fieldname: "gap_type",
			label: "Gap Type",
			fieldtype: "Select",
			options: "\nNo Context\nLow Confidence\nRestricted Access",
			change: () => {
				this.state.gap_type = this._type_field.get_value() || null;
				this._load();
			},
		});

		page.add_inner_button("Refresh", () => this._load());

		page.add_inner_button("Detect Gaps Now", () => this._run_proactive_detection());
	}

	// ── Page body ────────────────────────────────────────────────────────────────

	_setup_body() {
		this.$body = $(`
			<div class="ngr-page" style="padding: 16px;">
				<div class="ngr-summary-bar" style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px;"></div>
				<div class="ngr-table-wrap"></div>
			</div>
		`).appendTo($(this.wrapper).find(".layout-main-section"));

		this.$summary = this.$body.find(".ngr-summary-bar");
		this.$table_wrap = this.$body.find(".ngr-table-wrap");
	}

	// ── Data loading ─────────────────────────────────────────────────────────────

	_load() {
		this.$table_wrap.html(
			'<p style="color:#888;padding:12px;">Loading…</p>'
		);
		frappe.call({
			method: "digitz_ai_nexus.api.knowledge_gap.get_gap_summary",
			args: {
				tenant: this.state.tenant || "",
				status: this.state.status || "",
				gap_type: this.state.gap_type || "",
				limit: 200,
			},
			callback: (r) => {
				if (r.message) {
					this.state.gaps = r.message.gaps || [];
					this.state.counts = r.message.counts || {};
					this._render_summary();
					this._render_table();
				}
			},
			error: () => {
				this.$table_wrap.html(
					'<p style="color:red;padding:12px;">Failed to load gaps.</p>'
				);
			},
		});
	}

	// ── Summary bar ──────────────────────────────────────────────────────────────

	_render_summary() {
		const c = this.state.counts;
		const chips = [
			{ label: "Total", value: c.total || 0, color: "#6c757d" },
			{ label: "New", value: c.new || 0, color: "#2490ef" },
			{ label: "Relevant", value: c.relevant || 0, color: "#28a745" },
			{ label: "No Context", value: c.no_context || 0, color: "#dc3545" },
			{ label: "Low Confidence", value: c.low_confidence || 0, color: "#fd7e14" },
			{ label: "Pending Follow-up", value: c.pending_followup || 0, color: "#20c997" },
		];

		this.$summary.empty();
		chips.forEach((chip) => {
			this.$summary.append(`
				<div style="
					background:#fff;border:1px solid #e0e0e0;border-radius:6px;
					padding:8px 16px;min-width:110px;text-align:center;
					box-shadow:0 1px 3px rgba(0,0,0,.06);">
					<div style="font-size:22px;font-weight:700;color:${chip.color};">${chip.value}</div>
					<div style="font-size:12px;color:#555;">${chip.label}</div>
				</div>
			`);
		});
	}

	// ── Table ────────────────────────────────────────────────────────────────────

	_render_table() {
		const gaps = this.state.gaps;
		if (!gaps.length) {
			this.$table_wrap.html(
				'<p style="color:#888;padding:12px;">No knowledge gaps found for the selected filters.</p>'
			);
			return;
		}

		const rows = gaps.map((g) => this._row_html(g)).join("");
		this.$table_wrap.html(`
			<table class="ngr-table table table-bordered" style="width:100%;font-size:13px;background:#fff;">
				<thead style="background:#f7f7f7;">
					<tr>
						<th style="width:28%">Query</th>
						<th style="width:8%">Type</th>
						<th style="width:6%">Freq</th>
						<th style="width:6%">Conf</th>
						<th style="width:10%">LLM</th>
						<th style="width:8%">Status</th>
						<th style="width:14%">Follow-up</th>
						<th style="width:8%">Last Seen</th>
						<th style="width:12%">Actions</th>
					</tr>
				</thead>
				<tbody>${rows}</tbody>
			</table>
		`);

		this.$table_wrap.find(".ngr-table tbody").on("click", "[data-action]", (e) => {
			const $btn = $(e.currentTarget);
			const action = $btn.data("action");
			const name = $btn.data("name");
			const gap = gaps.find((g) => g.name === name);
			if (gap) this._handle_action(action, gap, $btn);
		});
	}

	_row_html(g) {
		const type_colors = {
			"No Context": "#dc3545",
			"Low Confidence": "#fd7e14",
			"Restricted Access": "#6f42c1",
		};
		const status_colors = {
			New: "#2490ef",
			"Under Review": "#fd7e14",
			Watching: "#6f42c1",
			Actioned: "#28a745",
			Dismissed: "#6c757d",
		};
		const type_color = type_colors[g.gap_type] || "#555";
		const status_color = status_colors[g.status] || "#555";

		const llm_cell = this._llm_cell(g);
		const conf = g.confidence != null ? (g.confidence * 100).toFixed(0) + "%" : "—";
		const last_seen = g.last_seen_on
			? frappe.datetime.str_to_user(g.last_seen_on).split(" ")[0]
			: "—";

		const query_preview = frappe.utils.escape_html(
			(g.query || "").length > 120 ? g.query.slice(0, 120) + "…" : g.query || ""
		);

		const proactive_badge = g.detection_mode === "Proactive"
			? '<span style="background:#6f42c1;color:#fff;font-size:10px;padding:1px 5px;border-radius:3px;margin-left:6px;vertical-align:middle;">Proactive</span>'
			: "";

		const followup_cell = this._followup_cell(g);

		return `
			<tr data-gap="${frappe.utils.escape_html(g.name)}" style="vertical-align:middle;">
				<td>
					<div style="font-weight:500;">${query_preview}${proactive_badge}</div>
					${g.suggested_topic ? `<div style="font-size:11px;color:#888;margin-top:2px;">Topic: ${frappe.utils.escape_html(g.suggested_topic)}</div>` : ""}
					${g.tenant ? `<div style="font-size:11px;color:#888;">Tenant: ${frappe.utils.escape_html(g.tenant)}</div>` : ""}
				</td>
				<td><span style="color:${type_color};font-weight:600;">${frappe.utils.escape_html(g.gap_type || "—")}</span></td>
				<td style="text-align:center;font-weight:700;">${g.frequency || 1}</td>
				<td style="text-align:center;">${conf}</td>
				<td>${llm_cell}</td>
				<td><span style="color:${status_color};font-weight:600;">${frappe.utils.escape_html(g.status || "—")}</span></td>
				<td>${followup_cell}</td>
				<td style="font-size:11px;color:#666;">${last_seen}</td>
				<td>${this._action_buttons(g)}</td>
			</tr>
		`;
	}

	_llm_cell(g) {
		if (g.llm_assessment_status === "Pending") {
			return '<span style="color:#888;font-size:11px;">Pending…</span>';
		}
		if (g.llm_assessment_status === "Failed") {
			return '<span style="color:#dc3545;font-size:11px;">Failed</span>';
		}
		if (g.llm_assessment_status === "Completed") {
			const rel = g.is_relevant;
			const conf = g.relevance_confidence != null
				? " (" + (g.relevance_confidence * 100).toFixed(0) + "%)"
				: "";
			const icon = rel ? "✓" : "✗";
			const color = rel ? "#28a745" : "#6c757d";
			const label = rel ? "Relevant" : "Not Relevant";
			const summary = g.llm_summary
				? `<div style="font-size:10px;color:#888;margin-top:2px;">${frappe.utils.escape_html((g.llm_summary || "").slice(0, 80))}…</div>`
				: "";
			return `<div style="color:${color};font-weight:600;">${icon} ${label}${conf}</div>${summary}`;
		}
		return "—";
	}

	_followup_cell(g) {
		const name = frappe.utils.escape_html(g.name);
		if (!g.visitor_email) {
			return '<span style="color:#ccc;font-size:11px;">—</span>';
		}
		const email_html = `<div style="font-size:11px;color:#555;word-break:break-all;">&#9993; ${frappe.utils.escape_html(g.visitor_email)}</div>`;
		if (g.visitor_email_status === "Notified") {
			return (
				email_html +
				'<span style="font-size:11px;font-weight:600;color:#28a745;">&#10003; Notified</span>'
			);
		}
		if (g.visitor_email_status === "Pending") {
			return (
				email_html +
				`<button class="btn btn-xs btn-success" data-action="notify" data-name="${name}"
					title="Send follow-up email to visitor" style="margin-top:4px;">
					Notify Visitor
				</button>`
			);
		}
		return email_html;
	}

	_action_buttons(g) {
		const name = frappe.utils.escape_html(g.name);
		const buttons = [];

		if (g.status !== "Dismissed" && g.status !== "Actioned") {
			buttons.push(`
				<button class="btn btn-xs btn-default" data-action="review" data-name="${name}"
					title="Mark Under Review" style="margin:1px;">
					Review
				</button>
			`);
		}

		if (g.is_relevant && g.status !== "Actioned") {
			buttons.push(`
				<button class="btn btn-xs btn-primary" data-action="create_source" data-name="${name}"
					title="Create Knowledge Source from this gap" style="margin:1px;">
					+ KS
				</button>
			`);
		}

		if (g.llm_assessment_status !== "Completed") {
			buttons.push(`
				<button class="btn btn-xs btn-default" data-action="reassess" data-name="${name}"
					title="Trigger LLM Reassessment" style="margin:1px;">
					Reassess
				</button>
			`);
		}

		if (g.status !== "Dismissed") {
			buttons.push(`
				<button class="btn btn-xs btn-danger" data-action="dismiss" data-name="${name}"
					title="Dismiss this gap" style="margin:1px;">
					Dismiss
				</button>
			`);
		}

		buttons.push(`
			<button class="btn btn-xs btn-default" data-action="open" data-name="${name}"
				title="Open record" style="margin:1px;">
				↗
			</button>
		`);

		return `<div style="white-space:nowrap;">${buttons.join("")}</div>`;
	}

	// ── Action handlers ──────────────────────────────────────────────────────────

	_handle_action(action, gap, $btn) {
		switch (action) {
		case "open":
			frappe.set_route("Form", "Nexus Knowledge Gap", gap.name);
			break;

		case "review":
			this._set_status(gap.name, "Under Review");
			break;

		case "dismiss":
			frappe.confirm(
				`Dismiss gap: <em>${frappe.utils.escape_html(gap.query.slice(0, 80))}</em>?`,
				() => this._set_status(gap.name, "Dismissed")
			);
			break;

		case "reassess":
			$btn.prop("disabled", true).text("…");
			frappe.call({
				method: "digitz_ai_nexus.api.knowledge_gap.trigger_reassessment",
				args: { gap_name: gap.name },
				callback: () => {
					frappe.show_alert({ message: "Reassessment queued.", indicator: "green" });
					setTimeout(() => this._load(), 1500);
				},
			});
			break;

		case "create_source":
			this._open_create_source_dialog(gap);
			break;

		case "notify":
			frappe.confirm(
				`Send follow-up email to <strong>${frappe.utils.escape_html(gap.visitor_email)}</strong>?`,
				() => {
					$btn.prop("disabled", true).text("…");
					frappe.call({
						method: "digitz_ai_nexus.api.knowledge_gap.notify_gap_visitor",
						args: { gap_name: gap.name },
						callback: () => {
							frappe.show_alert({ message: "Notification email sent.", indicator: "green" });
							this._load();
						},
						error: (r) => {
							$btn.prop("disabled", false).text("Notify");
							frappe.msgprint({ message: r.message || "Failed to send notification.", indicator: "red" });
						},
					});
				}
			);
			break;
		}
	}

	_run_proactive_detection() {
		const tenant = this.state.tenant || null;
		const scope = tenant ? `tenant: ${tenant}` : "all tenants";

		frappe.confirm(
			`Run proactive gap detection now for ${scope}?<br><br>
			<small style="color:#888;">This analyses the last 30 days of query history against your
			knowledge base and surfaces topic clusters that are missing coverage.
			The job runs in the background — refresh the page in a minute to see new gaps.</small>`,
			() => {
				frappe.call({
					method: "digitz_ai_nexus.api.knowledge_gap.trigger_proactive_detection",
					args: { tenant: tenant || "" },
					callback: (r) => {
						if (r.message && r.message.queued) {
							frappe.show_alert({
								message: "Gap detection queued. Refresh the page in a moment to see results.",
								indicator: "blue",
							});
						}
					},
				});
			}
		);
	}

	_open_create_source_dialog(gap) {
		const suggestion_html = `
			<div style="background:#f7f7f7;border:1px solid #e0e0e0;border-radius:6px;padding:12px;margin-bottom:4px;font-size:12px;">
				<div style="font-weight:600;margin-bottom:6px;color:#555;">LLM Suggestion (for reference only)</div>
				${gap.suggested_topic
					? `<div><span style="color:#888;">Suggested Topic:</span> ${frappe.utils.escape_html(gap.suggested_topic)}</div>`
					: ""}
				${gap.suggested_context
					? `<div><span style="color:#888;">Suggested Context:</span> ${frappe.utils.escape_html(gap.suggested_context)}</div>`
					: ""}
				${gap.llm_summary
					? `<div style="margin-top:6px;color:#555;">${frappe.utils.escape_html(gap.llm_summary)}</div>`
					: ""}
				<div style="margin-top:8px;color:#888;font-style:italic;">Original gap query: ${frappe.utils.escape_html((gap.query || "").slice(0, 120))}</div>
			</div>
		`;

		const d = new frappe.ui.Dialog({
			title: "Create Knowledge Source",
			fields: [
				{
					fieldname: "llm_reference",
					fieldtype: "HTML",
					options: suggestion_html,
				},
				{
					fieldname: "title",
					fieldtype: "Data",
					label: "Title",
					reqd: 1,
					default: gap.suggested_topic || "",
					description: "Title for this knowledge source.",
				},
				{
					fieldname: "col1",
					fieldtype: "Column Break",
				},
				{
					fieldname: "business_unit",
					fieldtype: "Link",
					label: "Business Unit",
					options: "Nexus Business Unit",
				},
				{
					fieldname: "sec1",
					fieldtype: "Section Break",
					label: "Classification",
				},
				{
					fieldname: "context",
					fieldtype: "Data",
					label: "Context",
					default: gap.suggested_context || "",
				},
				{
					fieldname: "sub_context",
					fieldtype: "Data",
					label: "Sub Context",
				},
				{
					fieldname: "col2",
					fieldtype: "Column Break",
				},
				{
					fieldname: "topic",
					fieldtype: "Data",
					label: "Topic",
					default: gap.suggested_topic || "",
				},
				{
					fieldname: "access_policy",
					fieldtype: "Link",
					label: "Access Policy",
					options: "Nexus Access Policy",
				},
				{
					fieldname: "sec2",
					fieldtype: "Section Break",
					label: "Content",
				},
				{
					fieldname: "manual_content",
					fieldtype: "Long Text",
					label: "Manual Content",
					reqd: 1,
					description: "Write the knowledge content here. This source will go through the full processing pipeline (classify → chunks → embeddings → publish).",
				},
			],
			primary_action_label: "Create Knowledge Source",
			primary_action: (values) => {
				d.hide();
				frappe.call({
					method: "digitz_ai_nexus.api.knowledge_gap.create_knowledge_source_from_gap",
					args: {
						gap_name: gap.name,
						title: values.title,
						business_unit: values.business_unit || "",
						context: values.context || "",
						sub_context: values.sub_context || "",
						topic: values.topic || "",
						access_policy: values.access_policy || "",
						manual_content: values.manual_content,
					},
					callback: (r) => {
						if (r.message && r.message.source_name) {
							frappe.show_alert({
								message: `Knowledge Source created: ${r.message.source_name}`,
								indicator: "green",
							});
							frappe.confirm(
								"Open the new Knowledge Source to complete classification and processing?",
								() => frappe.set_route("Form", "Nexus Knowledge Source", r.message.source_name),
								() => this._load()
							);
						}
					},
				});
			},
		});

		d.show();
	}

	_set_status(gap_name, status) {
		frappe.call({
			method: "digitz_ai_nexus.api.knowledge_gap.update_gap_status",
			args: { gap_name, status },
			callback: () => {
				frappe.show_alert({
					message: `Marked as ${status}.`,
					indicator: status === "Dismissed" ? "orange" : "green",
				});
				this._load();
			},
		});
	}
}
