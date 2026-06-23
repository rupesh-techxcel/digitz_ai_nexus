frappe.pages["nexus-companion-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Companion Dashboard",
		single_column: true,
	});

	new NexusCompanionDashboard(page, wrapper);
};

/* ═══════════════════════════════════════════════════════════════════════════
   NexusCompanionDashboard
   Enquiry pipeline, journey funnel, and live activity overview.
═══════════════════════════════════════════════════════════════════════════ */
class NexusCompanionDashboard {
	constructor(page, wrapper) {
		this.page = page;
		this.wrapper = wrapper;
		this.tenant = null;
		this.data = null;
		this.detail_enquiry = null;

		this._inject_styles();
		this._build_toolbar();
		this._build_skeleton();
		this._load();
	}

	// ── Styles ────────────────────────────────────────────────────────────────

	_inject_styles() {
		if (document.getElementById("ncd-styles")) return;
		const s = document.createElement("style");
		s.id = "ncd-styles";
		s.textContent = `
/* ── Layout ── */
.ncd-root { padding: 0 24px 40px; font-family: var(--font-stack); }

/* ── Stat cards ── */
.ncd-stats { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 28px; }
.ncd-stat {
  flex: 1 1 160px; background: #fff; border: 1px solid #e4e9f7;
  border-radius: 12px; padding: 20px 22px; text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
.ncd-stat-value { font-size: 2rem; font-weight: 700; color: #1f3a8a; line-height: 1.1; }
.ncd-stat-label { font-size: 0.78rem; color: #6b7a99; margin-top: 4px; text-transform: uppercase; letter-spacing: .04em; }
.ncd-stat.qualified .ncd-stat-value { color: #2d7a45; }
.ncd-stat.escalated .ncd-stat-value { color: #c0392b; }
.ncd-stat.score   .ncd-stat-value { color: #7c3aed; }

/* ── Section headings ── */
.ncd-section-title {
  font-size: 0.85rem; font-weight: 600; color: #374151;
  text-transform: uppercase; letter-spacing: .06em;
  margin: 0 0 14px;
}

/* ── Funnel ── */
.ncd-funnel { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 32px; }
.ncd-funnel-stage {
  flex: 1 1 90px; background: #fff; border: 1px solid #e4e9f7;
  border-radius: 10px; padding: 14px 12px; text-align: center;
  cursor: pointer; transition: box-shadow .15s, border-color .15s;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.ncd-funnel-stage:hover { border-color: #3b5ce6; box-shadow: 0 2px 8px rgba(59,92,230,.12); }
.ncd-funnel-stage.active { border-color: #3b5ce6; background: #eef1fd; }
.ncd-funnel-count { font-size: 1.6rem; font-weight: 700; color: #1f3a8a; }
.ncd-funnel-label { font-size: 0.72rem; color: #6b7a99; margin-top: 4px; text-transform: uppercase; letter-spacing: .03em; }
.ncd-funnel-stage[data-stage="ESCALATED"] .ncd-funnel-count { color: #c0392b; }
.ncd-funnel-stage[data-stage="CONVERTED"] .ncd-funnel-count { color: #2d7a45; }
.ncd-funnel-stage[data-stage="DECLINED"]  .ncd-funnel-count { color: #6b7280; }

/* ── Two-column body ── */
.ncd-body { display: grid; grid-template-columns: 1fr 340px; gap: 24px; }
@media (max-width: 900px) { .ncd-body { grid-template-columns: 1fr; } }

/* ── Enquiry table ── */
.ncd-table-wrap { background: #fff; border: 1px solid #e4e9f7; border-radius: 12px; overflow: hidden; }
.ncd-table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
.ncd-table th {
  background: #f8f9ff; padding: 10px 14px; text-align: left;
  font-size: 0.75rem; font-weight: 600; color: #6b7a99;
  text-transform: uppercase; letter-spacing: .04em;
  border-bottom: 1px solid #e4e9f7;
}
.ncd-table td { padding: 11px 14px; border-bottom: 1px solid #f0f2f8; vertical-align: middle; }
.ncd-table tr:last-child td { border-bottom: none; }
.ncd-table tr.ncd-row:hover { background: #f5f7ff; cursor: pointer; }

/* ── Stage badges ── */
.ncd-badge {
  display: inline-block; padding: 2px 9px; border-radius: 20px;
  font-size: 0.71rem; font-weight: 600; text-transform: uppercase; letter-spacing: .04em;
}
.ncd-badge-ARRIVED           { background:#f0f2f8; color:#6b7a99; }
.ncd-badge-GREETING          { background:#e8f4fd; color:#1a6fa3; }
.ncd-badge-DISCOVERY         { background:#fef3cd; color:#856404; }
.ncd-badge-ENGAGED           { background:#fff0d9; color:#a35c00; }
.ncd-badge-PRESENTING        { background:#f0e6ff; color:#6b21a8; }
.ncd-badge-OBJECTION_HANDLING{ background:#fff1e6; color:#b45309; }
.ncd-badge-INTERESTED        { background:#d9f0d8; color:#1a6b29; }
.ncd-badge-CONVERTING        { background:#e0f2fe; color:#0369a1; }
.ncd-badge-CONVERTED         { background:#c7f1d2; color:#145c29; }
.ncd-badge-DECLINED          { background:#f3f4f6; color:#6b7280; }
.ncd-badge-ESCALATED         { background:#fde8e8; color:#b91c1c; }

/* ── Score bar ── */
.ncd-score-wrap { display: flex; align-items: center; gap: 8px; }
.ncd-score-bar-bg { flex: 1; height: 6px; background: #e8eaf0; border-radius: 4px; overflow: hidden; min-width: 48px; }
.ncd-score-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #3b5ce6, #6ee7b7); transition: width .4s; }
.ncd-score-num { font-size: 0.78rem; font-weight: 600; color: #374151; min-width: 24px; }

/* ── Right sidebar ── */
.ncd-sidebar { display: flex; flex-direction: column; gap: 20px; }

/* ── Persona chart ── */
.ncd-card { background: #fff; border: 1px solid #e4e9f7; border-radius: 12px; padding: 20px 18px; }
.ncd-card-title { font-size: 0.8rem; font-weight: 600; color: #6b7a99; text-transform: uppercase; letter-spacing: .05em; margin: 0 0 14px; }
.ncd-persona-row { margin-bottom: 12px; }
.ncd-persona-name { font-size: 0.83rem; color: #1e293b; margin-bottom: 4px; display: flex; justify-content: space-between; }
.ncd-persona-count { color: #6b7a99; font-size: 0.78rem; }
.ncd-persona-bar-bg { height: 6px; background: #eef0f8; border-radius: 4px; overflow: hidden; }
.ncd-persona-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #3b5ce6, #a78bfa); }

/* ── Config summary ── */
.ncd-config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.ncd-config-item {
  background: #f8f9ff; border-radius: 8px; padding: 10px 12px;
  display: flex; flex-direction: column; align-items: center; text-align: center;
}
.ncd-config-item a { color: inherit; text-decoration: none; }
.ncd-config-item a:hover .ncd-config-count { color: #3b5ce6; }
.ncd-config-count { font-size: 1.4rem; font-weight: 700; color: #1f3a8a; }
.ncd-config-label { font-size: 0.71rem; color: #6b7a99; margin-top: 2px; text-transform: uppercase; letter-spacing: .04em; }

/* ── Detail panel ── */
.ncd-detail-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.3); z-index: 900;
  display: flex; align-items: stretch; justify-content: flex-end;
}
.ncd-detail-panel {
  background: #fff; width: 480px; max-width: 96vw;
  box-shadow: -4px 0 24px rgba(0,0,0,.12);
  display: flex; flex-direction: column; overflow: hidden;
}
.ncd-detail-header {
  padding: 20px 24px; border-bottom: 1px solid #e4e9f7;
  display: flex; align-items: center; justify-content: space-between;
}
.ncd-detail-title { font-size: 1rem; font-weight: 600; color: #1e293b; }
.ncd-detail-close {
  background: none; border: none; cursor: pointer;
  color: #6b7a99; font-size: 1.2rem; padding: 4px 8px; border-radius: 6px;
}
.ncd-detail-close:hover { background: #f0f2f8; }
.ncd-detail-body { flex: 1; overflow-y: auto; padding: 24px; }
.ncd-detail-section { margin-bottom: 22px; }
.ncd-detail-section-title { font-size: 0.75rem; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: .06em; margin: 0 0 10px; }
.ncd-detail-row { display: flex; gap: 12px; margin-bottom: 8px; font-size: 0.85rem; }
.ncd-detail-key { color: #6b7a99; min-width: 130px; flex-shrink: 0; }
.ncd-detail-val { color: #1e293b; font-weight: 500; word-break: break-word; }
.ncd-detail-actions { padding: 16px 24px; border-top: 1px solid #e4e9f7; display: flex; gap: 10px; }
.ncd-detail-actions .btn { font-size: 0.82rem; }

/* ── Discovery JSON ── */
.ncd-discovery-block {
  background: #f8f9ff; border-radius: 8px; padding: 12px 14px;
  font-size: 0.82rem; color: #374151; line-height: 1.7;
}
.ncd-discovery-row { display: flex; gap: 10px; margin-bottom: 2px; }
.ncd-discovery-key { color: #6b7a99; min-width: 140px; text-transform: capitalize; }
.ncd-discovery-val { color: #1e293b; font-weight: 500; }

/* ── Empty / loading ── */
.ncd-empty { text-align: center; padding: 40px 20px; color: #9ca3af; font-size: 0.9rem; }
.ncd-loading { text-align: center; padding: 60px 20px; color: #9ca3af; font-size: 0.9rem; }
.ncd-spinner { width: 32px; height: 32px; border: 3px solid #e4e9f7; border-top-color: #3b5ce6; border-radius: 50%; animation: ncd-spin .7s linear infinite; margin: 0 auto 12px; }
@keyframes ncd-spin { to { transform: rotate(360deg); } }

/* ── Filter row ── */
.ncd-filter-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.ncd-filter-row select, .ncd-filter-row input {
  border: 1px solid #d1d5e0; border-radius: 8px; padding: 6px 12px;
  font-size: 0.84rem; color: #374151; outline: none;
}
.ncd-filter-row select:focus, .ncd-filter-row input:focus { border-color: #3b5ce6; }
.ncd-filter-row .btn-refresh { margin-left: auto; }
`;
		document.head.appendChild(s);
	}

	// ── Toolbar ───────────────────────────────────────────────────────────────

	_build_toolbar() {
		this.page.add_action_item("Configure", () => {
			frappe.set_route("List", "Nexus Companion Playbook");
		});
		this.page.add_action_item("Personas", () => {
			frappe.set_route("List", "Nexus Companion Persona");
		});
		this.page.add_action_item("Products", () => {
			frappe.set_route("List", "Nexus Companion Product");
		});
		this.page.add_action_item("All Enquiries", () => {
			frappe.set_route("List", "Nexus Companion Enquiry");
		});
		this.page.add_action_item("Refresh", () => this._load());
	}

	// ── Skeleton ──────────────────────────────────────────────────────────────

	_build_skeleton() {
		$(this.wrapper).find(".layout-main-section").html(`
			<div class="ncd-root">
				<div class="ncd-loading" id="ncd-loading">
					<div class="ncd-spinner"></div>
					Loading companion data…
				</div>
				<div id="ncd-content" style="display:none;"></div>
			</div>
		`);
	}

	// ── Data load ─────────────────────────────────────────────────────────────

	_load(tenant) {
		const t = tenant || this.tenant || null;
		$("#ncd-loading").show();
		$("#ncd-content").hide();

		frappe.call({
			method: "digitz_ai_nexus.nexus_companion.api.companion_dashboard.get_dashboard_data",
			args: { tenant: t || "" },
			callback: (r) => {
				if (r.message) {
					this.data = r.message;
					this.tenant = r.message.tenant || null;
					this._render(r.message);
				}
				$("#ncd-loading").hide();
				$("#ncd-content").show();
			},
			error: () => {
				$("#ncd-loading").html('<div class="ncd-empty">Failed to load dashboard data. Please try refreshing.</div>');
			},
		});
	}

	// ── Render ────────────────────────────────────────────────────────────────

	_render(data) {
		const content = $("#ncd-content");
		content.html(`
			${this._render_filter_row(data)}
			${this._render_stats(data.stats)}
			<p class="ncd-section-title">Journey Funnel — click a stage to filter</p>
			${this._render_funnel(data.stage_funnel)}
			<div class="ncd-body">
				<div>
					<p class="ncd-section-title">Recent Enquiries</p>
					<div class="ncd-table-wrap" id="ncd-enquiry-table">
						${this._render_enquiry_table(data.recent_enquiries)}
					</div>
				</div>
				<div class="ncd-sidebar">
					${this._render_personas(data.top_personas)}
					${this._render_config(data.config_summary)}
				</div>
			</div>
		`);

		this._bind_events();
	}

	_render_filter_row(data) {
		return `
			<div class="ncd-filter-row">
				<label style="font-size:.83rem;color:#6b7a99;font-weight:600;">Tenant</label>
				<select id="ncd-tenant-select" style="min-width:160px;">
					<option value="">All Tenants</option>
				</select>
				<button class="btn btn-xs btn-default btn-refresh" onclick="window.__ncd.refresh()">
					<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
					Refresh
				</button>
			</div>
		`;
	}

	_render_stats(stats) {
		return `
			<div class="ncd-stats">
				<div class="ncd-stat">
					<div class="ncd-stat-value">${stats.total}</div>
					<div class="ncd-stat-label">Total Enquiries</div>
				</div>
				<div class="ncd-stat">
					<div class="ncd-stat-value">${stats.today}</div>
					<div class="ncd-stat-label">Today</div>
				</div>
				<div class="ncd-stat qualified">
					<div class="ncd-stat-value">${stats.converted}</div>
					<div class="ncd-stat-label">Converted</div>
				</div>
				<div class="ncd-stat escalated">
					<div class="ncd-stat-value">${stats.escalated}</div>
					<div class="ncd-stat-label">Escalated</div>
				</div>
				<div class="ncd-stat score">
					<div class="ncd-stat-value">${stats.avg_score_7d}</div>
					<div class="ncd-stat-label">Avg Score (7d)</div>
				</div>
			</div>
		`;
	}

	_render_funnel(funnel) {
		const max = Math.max(...funnel.map(f => f.count), 1);
		const bars = funnel.map(f => {
			const pct = Math.round((f.count / max) * 100);
			return `
				<div class="ncd-funnel-stage" data-stage="${f.stage}" title="Click to filter by ${f.label}">
					<div class="ncd-funnel-count">${f.count}</div>
					<div class="ncd-funnel-label">${f.label}</div>
					<div style="height:4px;background:#eef0f8;border-radius:3px;margin-top:8px;overflow:hidden;">
						<div style="height:100%;width:${pct}%;background:linear-gradient(90deg,#3b5ce6,#a78bfa);border-radius:3px;transition:width .4s;"></div>
					</div>
				</div>
			`;
		}).join("");
		return `<div class="ncd-funnel" id="ncd-funnel">${bars}</div>`;
	}

	_render_enquiry_table(enquiries, filter_stage) {
		const visible = filter_stage
			? enquiries.filter(e => e.enquiry_stage === filter_stage)
			: enquiries;

		if (!visible.length) {
			return `<div class="ncd-empty">${filter_stage ? `No enquiries at ${filter_stage} stage` : "No enquiries yet"}</div>`;
		}

		const rows = visible.map(e => {
			const name = e.visitor_name || `<span style="color:#9ca3af;font-style:italic;">Anonymous</span>`;
			const persona = e.persona_name
				? `<span style="font-size:0.78rem;color:#6b7a99;">${e.persona_name}</span>`
				: `<span style="color:#d1d5e0;font-size:0.78rem;">—</span>`;
			const score = e.enquiry_score || 0;
			const badge = `<span class="ncd-badge ncd-badge-${e.enquiry_stage}">${this._stage_label(e.enquiry_stage)}</span>`;
			const scoreBar = `
				<div class="ncd-score-wrap">
					<div class="ncd-score-bar-bg">
						<div class="ncd-score-bar-fill" style="width:${score}%;"></div>
					</div>
					<div class="ncd-score-num">${score}</div>
				</div>`;
			const age = frappe.datetime.prettyDate(e.creation);
			const flag = e.escalation_recommended
				? `<span title="Escalation recommended" style="color:#ef4444;margin-left:4px;">⚑</span>` : "";
			return `
				<tr class="ncd-row" data-name="${e.name}">
					<td>${name}${flag}</td>
					<td>${badge}</td>
					<td>${scoreBar}</td>
					<td>${persona}</td>
					<td style="font-size:0.78rem;color:#9ca3af;">${age}</td>
				</tr>`;
		}).join("");

		return `
			<table class="ncd-table">
				<thead>
					<tr>
						<th>Visitor</th>
						<th>Stage</th>
						<th style="min-width:110px;">Score</th>
						<th>Persona</th>
						<th>When</th>
					</tr>
				</thead>
				<tbody>${rows}</tbody>
			</table>`;
	}

	_render_personas(top_personas) {
		if (!top_personas || !top_personas.length) {
			return `<div class="ncd-card">
				<p class="ncd-card-title">Top Personas</p>
				<div class="ncd-empty" style="padding:16px 0;">No persona matches yet</div>
			</div>`;
		}
		const max = Math.max(...top_personas.map(p => p.count), 1);
		const rows = top_personas.map(p => `
			<div class="ncd-persona-row">
				<div class="ncd-persona-name">
					<span>${p.persona_name || p.persona}</span>
					<span class="ncd-persona-count">${p.count}</span>
				</div>
				<div class="ncd-persona-bar-bg">
					<div class="ncd-persona-bar-fill" style="width:${Math.round((p.count/max)*100)}%;"></div>
				</div>
			</div>
		`).join("");
		return `<div class="ncd-card"><p class="ncd-card-title">Top Matched Personas</p>${rows}</div>`;
	}

	_render_config(cfg) {
		const items = [
			{ label: "Playbooks", count: cfg.playbooks, route: ["List", "Nexus Companion Playbook"] },
			{ label: "Personas", count: cfg.personas, route: ["List", "Nexus Companion Persona"] },
			{ label: "Products", count: cfg.products, route: ["List", "Nexus Companion Product"] },
			{ label: "Services", count: cfg.services, route: ["List", "Nexus Companion Service"] },
			{ label: "Stories", count: cfg.stories, route: ["List", "Nexus Companion Story"] },
			{ label: "Outcomes", count: cfg.outcomes, route: ["List", "Nexus Companion Outcome"] },
		];
		const grid = items.map(item => `
			<div class="ncd-config-item">
				<a href="${frappe.utils.get_form_link(item.route[1], "")}" onclick="frappe.set_route('${item.route[0]}','${item.route[1]}');return false;">
					<div class="ncd-config-count">${item.count}</div>
					<div class="ncd-config-label">${item.label}</div>
				</a>
			</div>
		`).join("");
		return `<div class="ncd-card"><p class="ncd-card-title">Configuration</p><div class="ncd-config-grid">${grid}</div></div>`;
	}

	// ── Event binding ─────────────────────────────────────────────────────────

	_bind_events() {
		window.__ncd = this;

		// Funnel stage filter
		let active_stage = null;
		$(document).on("click", ".ncd-funnel-stage", (e) => {
			const stage = $(e.currentTarget).data("stage");
			if (active_stage === stage) {
				active_stage = null;
				$(".ncd-funnel-stage").removeClass("active");
			} else {
				active_stage = stage;
				$(".ncd-funnel-stage").removeClass("active");
				$(e.currentTarget).addClass("active");
			}
			$("#ncd-enquiry-table").html(
				this._render_enquiry_table(this.data.recent_enquiries, active_stage)
			);
			this._bind_table_rows();
		});

		// Tenant selector
		this._load_tenants();

		// Table row click
		this._bind_table_rows();
	}

	_bind_table_rows() {
		$(document).off("click", ".ncd-row").on("click", ".ncd-row", (e) => {
			const name = $(e.currentTarget).data("name");
			if (name) this._open_detail(name);
		});
	}

	_load_tenants() {
		frappe.call({
			method: "digitz_ai_nexus.nexus_companion.api.companion_dashboard.get_tenants",
			callback: (r) => {
				if (!r.message) return;
				const sel = $("#ncd-tenant-select");
				r.message.forEach(t => {
					sel.append(`<option value="${t.name}" ${this.tenant === t.name ? "selected" : ""}>${t.tenant_name || t.name}</option>`);
				});
				sel.on("change", () => {
					this.tenant = sel.val() || null;
					this._load(this.tenant);
				});
			},
		});
	}

	// ── Detail panel ─────────────────────────────────────────────────────────

	_open_detail(name) {
		frappe.call({
			method: "digitz_ai_nexus.nexus_companion.api.companion_dashboard.get_enquiry_detail",
			args: { name },
			callback: (r) => {
				if (r.message) this._render_detail(r.message);
			},
		});
	}

	_render_detail(enq) {
		// Remove existing overlay
		$(".ncd-detail-overlay").remove();

		let discovery_html = '<div class="ncd-empty" style="padding:8px 0;">No discovery data yet</div>';
		try {
			const disc = JSON.parse(enq.discovery_data || "{}");
			const keys = Object.keys(disc);
			if (keys.length) {
				discovery_html = `<div class="ncd-discovery-block">${
					keys.map(k => `
						<div class="ncd-discovery-row">
							<span class="ncd-discovery-key">${k.replace(/_/g, " ")}</span>
							<span class="ncd-discovery-val">${disc[k]}</span>
						</div>
					`).join("")
				}</div>`;
			}
		} catch(e) {}

		const products_html = enq.recommended_products && enq.recommended_products.length
			? enq.recommended_products.map(p =>
				`<div class="ncd-detail-row">
					<span class="ncd-detail-key">${p.product_name || p.product}</span>
					<span class="ncd-detail-val">Fit: ${p.fit_score || "—"}</span>
				</div>`).join("")
			: '<div style="color:#9ca3af;font-size:.82rem;">None matched yet</div>';

		const visitor_link = enq.conversation_id
			? `<a href="/app/nexus-live-console?conversation=${enq.conversation_id}" target="_blank" style="color:#3b5ce6;font-size:.8rem;">Open Conversation ↗</a>`
			: "";

		const overlay = $(`
			<div class="ncd-detail-overlay" id="ncd-detail-overlay">
				<div class="ncd-detail-panel">
					<div class="ncd-detail-header">
						<div>
							<div class="ncd-detail-title">${enq.visitor_name || "Anonymous Visitor"}</div>
							<div style="margin-top:4px;">${visitor_link}</div>
						</div>
						<button class="ncd-detail-close" id="ncd-close-detail">✕</button>
					</div>
					<div class="ncd-detail-body">
						<div class="ncd-detail-section">
							<p class="ncd-detail-section-title">Journey</p>
							<div class="ncd-detail-row">
								<span class="ncd-detail-key">Stage</span>
								<span class="ncd-detail-val"><span class="ncd-badge ncd-badge-${enq.enquiry_stage}">${this._stage_label(enq.enquiry_stage)}</span></span>
							</div>
							<div class="ncd-detail-row">
								<span class="ncd-detail-key">Enquiry Score</span>
								<span class="ncd-detail-val">
									<div class="ncd-score-wrap">
										<div class="ncd-score-bar-bg" style="min-width:80px;">
											<div class="ncd-score-bar-fill" style="width:${enq.enquiry_score||0}%;"></div>
										</div>
										<div class="ncd-score-num">${enq.enquiry_score || 0}</div>
									</div>
								</span>
							</div>
							<div class="ncd-detail-row">
								<span class="ncd-detail-key">Next Step</span>
								<span class="ncd-detail-val">${enq.recommended_next_step || "—"}</span>
							</div>
							<div class="ncd-detail-row">
								<span class="ncd-detail-key">Escalation Flag</span>
								<span class="ncd-detail-val">${enq.escalation_recommended ? '<span style="color:#ef4444;">⚑ Recommended</span>' : 'No'}</span>
							</div>
						</div>

						<div class="ncd-detail-section">
							<p class="ncd-detail-section-title">Matched Persona</p>
							<div class="ncd-detail-row">
								<span class="ncd-detail-key">Persona</span>
								<span class="ncd-detail-val">${enq.persona_name || '<span style="color:#9ca3af;">Not matched yet</span>'}</span>
							</div>
							<div class="ncd-detail-row">
								<span class="ncd-detail-key">Confidence</span>
								<span class="ncd-detail-val">${enq.persona_confidence ? enq.persona_confidence.toFixed(1) + "%" : "—"}</span>
							</div>
						</div>

						<div class="ncd-detail-section">
							<p class="ncd-detail-section-title">Visitor Profile Collected</p>
							${discovery_html}
						</div>

						<div class="ncd-detail-section">
							<p class="ncd-detail-section-title">Recommended Products</p>
							${products_html}
						</div>

						<div class="ncd-detail-section">
							<p class="ncd-detail-section-title">Identity</p>
							<div class="ncd-detail-row">
								<span class="ncd-detail-key">Email</span>
								<span class="ncd-detail-val">${enq.visitor_email || '<span style="color:#9ca3af;">Not collected</span>'}</span>
							</div>
							<div class="ncd-detail-row">
								<span class="ncd-detail-key">Verification</span>
								<span class="ncd-detail-val">${this._render_verification(enq.verification_status)}</span>
							</div>
						</div>

						<div class="ncd-detail-section">
							<p class="ncd-detail-section-title">Signal History</p>
							${this._render_signal_log(enq.stage_signal, enq.signal_log)}
						</div>
					</div>
					<div class="ncd-detail-actions">
						<button class="btn btn-sm btn-primary" onclick="frappe.set_route('Form','Nexus Companion Enquiry','${enq.name}')">
							Open Full Record
						</button>
						${enq.conversation ? `<button class="btn btn-sm btn-default" onclick="frappe.set_route('Form','Nexus Live Conversation','${enq.conversation}')">View Conversation</button>` : ""}
						<button class="btn btn-sm btn-default" id="ncd-close-detail-btn">Close</button>
					</div>
				</div>
			</div>
		`);

		$("body").append(overlay);

		$("#ncd-close-detail, #ncd-close-detail-btn").on("click", () => {
			$(".ncd-detail-overlay").remove();
		});
		$(".ncd-detail-overlay").on("click", (e) => {
			if ($(e.target).hasClass("ncd-detail-overlay")) {
				$(".ncd-detail-overlay").remove();
			}
		});
	}

	// ── Helpers ───────────────────────────────────────────────────────────────

	refresh() { this._load(this.tenant); }

	_render_verification(status) {
		if (status === "OTP Verified") {
			return '<span style="color:#2d7a45;font-weight:600;">✓ OTP Verified</span>';
		}
		return '<span style="color:#9ca3af;">Unverified</span>';
	}

	_render_signal_log(stage_signal, signal_log_json) {
		const _SIGNAL_COLORS = {
			SHARING_CONTEXT:   "#1a6fa3", ANSWERING_QUESTION: "#1a6fa3",
			CURIOUS:           "#6b7a99", EVALUATING:         "#a35c00",
			INTERESTED:        "#1a6b29", READY:              "#145c29",
			ASKING_PRICE:      "#0369a1", ASKING_NEXT_STEP:   "#0369a1",
			OBJECTING:         "#b45309", HESITATING:         "#6b7a99",
			DISENGAGING:       "#9ca3af", DEFLECTING:         "#9ca3af",
			REQUESTING_HUMAN:  "#b91c1c", DECLINING:          "#6b7280",
		};

		let log = [];
		try { log = JSON.parse(signal_log_json || "[]"); } catch(e) {}

		if (!log.length && !stage_signal) {
			return '<div style="color:#9ca3af;font-size:.82rem;padding:4px 0;">No signals recorded yet</div>';
		}

		// Show last signal prominently, then up to 8 previous ones
		const last = stage_signal
			? `<div style="margin-bottom:10px;">
					<span style="font-size:.75rem;color:#6b7a99;">Last signal</span><br>
					<span style="font-weight:600;color:${_SIGNAL_COLORS[stage_signal]||'#374151'};font-size:.85rem;">${stage_signal}</span>
				</div>`
			: "";

		const recent = log.slice(-8).reverse();
		const rows = recent.map(s => {
			const color = _SIGNAL_COLORS[s.signal_type] || "#374151";
			const conf = s.confidence != null ? Math.round(s.confidence * 100) + "%" : "";
			return `<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:5px;font-size:.81rem;">
				<span style="color:${color};font-weight:600;min-width:150px;">${s.signal_type}</span>
				<span style="color:#9ca3af;font-size:.75rem;">${conf}</span>
				<span style="color:#6b7a99;font-size:.75rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${(s.reason||'').replace(/"/g,"'")}">
					${(s.reason || "").substring(0, 60)}${(s.reason||"").length > 60 ? "…" : ""}
				</span>
			</div>`;
		}).join("");

		return `<div class="ncd-discovery-block" style="max-height:200px;overflow-y:auto;">${last}${rows}</div>`;
	}

	_stage_label(stage) {
		const labels = {
			ARRIVED: "Arrived", GREETING: "Greeting", DISCOVERY: "Discovery",
			ENGAGED: "Engaged", PRESENTING: "Presenting",
			OBJECTION_HANDLING: "Objection", INTERESTED: "Interested",
			CONVERTING: "Converting", CONVERTED: "Converted",
			DECLINED: "Declined", ESCALATED: "Escalated",
		};
		return labels[stage] || stage;
	}
}
