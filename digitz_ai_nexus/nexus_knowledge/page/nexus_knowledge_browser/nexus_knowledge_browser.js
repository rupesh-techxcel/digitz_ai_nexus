frappe.pages["nexus-knowledge-browser"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Knowledge Browser",
		single_column: true,
	});

	new NexusKnowledgeBrowser(page, wrapper);
};

/* ═══════════════════════════════════════════════════════════════════════════
   NexusKnowledgeBrowser
   Simulates a web browser over the public Nexus Knowledge feed.
═══════════════════════════════════════════════════════════════════════════ */
class NexusKnowledgeBrowser {
	constructor(page, wrapper) {
		this.page = page;
		this.wrapper = wrapper;

		this.state = {
			tenant: null,
			tenant_label: null,
			search: "",
			search_mode: "text",   // "text" | "vector"
			context: null,
			topic: null,
			page_num: 1,
			page_size: 15,
			total: 0,
			items: [],
			contexts: [],
			topics: [],
			loading: false,
			active_search_mode: "text",  // mode actually used for current results
			detail_item: null,
		};

		this._inject_styles();
		this._build_skeleton();
		this._boot();
	}

	// ── Styles ────────────────────────────────────────────────────────────────

	_inject_styles() {
		if (document.getElementById("nkb-styles")) return;
		const s = document.createElement("style");
		s.id = "nkb-styles";
		s.textContent = `
/* ── Layout ── */
.nkb-wrap {
	max-width: 900px;
	margin: 0 auto;
	padding: 0 0 80px;
	font-family: inherit;
}

/* ── Browser chrome bar ── */
.nkb-chrome {
	display: flex;
	align-items: center;
	gap: 10px;
	background: #f1f3f4;
	border: 1px solid #dadce0;
	border-radius: 10px;
	padding: 7px 14px;
	margin-bottom: 28px;
}
.nkb-chrome-dots {
	display: flex;
	gap: 5px;
	flex-shrink: 0;
}
.nkb-chrome-dot {
	width: 10px; height: 10px;
	border-radius: 50%;
}
.nkb-chrome-dot-r { background: #ff5f57; }
.nkb-chrome-dot-y { background: #febc2e; }
.nkb-chrome-dot-g { background: #28c840; }
.nkb-chrome-bar {
	flex: 1;
	display: flex;
	align-items: center;
	gap: 8px;
	background: #fff;
	border: 1px solid #dadce0;
	border-radius: 20px;
	padding: 4px 14px;
	font-size: 13px;
	color: #444;
	overflow: hidden;
}
.nkb-chrome-lock {
	color: #1a73e8;
	font-size: 13px;
	flex-shrink: 0;
}
.nkb-chrome-url {
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	flex: 1;
}
.nkb-chrome-url strong { color: #1a73e8; }
.nkb-chrome-refresh {
	background: none;
	border: none;
	cursor: pointer;
	color: #666;
	font-size: 16px;
	padding: 0 4px;
	line-height: 1;
	flex-shrink: 0;
}
.nkb-chrome-refresh:hover { color: #1a73e8; }

/* ── Search area ── */
.nkb-search-area {
	text-align: center;
	margin-bottom: 24px;
}
.nkb-search-logo {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 10px;
	margin-bottom: 18px;
}
.nkb-search-logo-icon {
	width: 36px; height: 36px;
	border-radius: 8px;
	background: linear-gradient(135deg, #0b2b72 0%, #16A37F 100%);
	display: flex; align-items: center; justify-content: center;
}
.nkb-search-logo-icon svg { display: block; }
.nkb-search-logo-text {
	font-size: 22px;
	font-weight: 700;
	color: #0b2b72;
	letter-spacing: -0.3px;
}
.nkb-search-logo-text span { color: #16A37F; }
.nkb-search-box {
	display: flex;
	align-items: center;
	gap: 10px;
	max-width: 620px;
	margin: 0 auto;
	background: #fff;
	border: 1.5px solid #dfe1e5;
	border-radius: 28px;
	padding: 10px 18px;
	box-shadow: 0 1px 6px rgba(32,33,36,.12);
	transition: box-shadow .2s, border-color .2s;
}
.nkb-search-box:focus-within {
	border-color: rgba(33,77,187,.50);
	box-shadow: 0 2px 12px rgba(33,77,187,.15);
}
.nkb-search-icon { color: #9aa0a6; flex-shrink: 0; }
.nkb-search-input {
	flex: 1;
	border: none;
	outline: none;
	font-size: 15px;
	color: #202124;
	background: transparent;
}
.nkb-search-input::placeholder { color: #9aa0a6; }
.nkb-search-clear {
	background: none; border: none; cursor: pointer;
	color: #9aa0a6; font-size: 18px; line-height: 1;
	padding: 0 2px; display: none;
}
.nkb-search-clear:hover { color: #444; }
.nkb-tenant-tag {
	margin-top: 10px;
	font-size: 12px;
	color: #888;
}
.nkb-tenant-tag strong { color: #16A37F; }

/* ── Filter bar ── */
.nkb-filter-bar {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
	margin-bottom: 12px;
	padding-bottom: 12px;
	border-bottom: 1px solid #e8eaed;
}
.nkb-filter-label {
	font-size: 12px;
	font-weight: 600;
	color: #888;
	text-transform: uppercase;
	letter-spacing: .04em;
	margin-right: 2px;
}
.nkb-filter-sep { color: #dadce0; font-size: 16px; margin: 0 4px; }
.nkb-pill {
	display: inline-flex;
	align-items: center;
	gap: 4px;
	padding: 4px 12px;
	border-radius: 16px;
	font-size: 12px;
	font-weight: 500;
	cursor: pointer;
	border: 1px solid #dadce0;
	background: #fff;
	color: #444;
	transition: all .15s;
	white-space: nowrap;
}
.nkb-pill:hover { border-color: #1a73e8; color: #1a73e8; }
.nkb-pill.active {
	background: #e8f0fe;
	border-color: #1a73e8;
	color: #1a73e8;
	font-weight: 600;
}
.nkb-pill-ctx.active  { background: #e6f4ea; border-color: #137333; color: #137333; }
.nkb-pill-topic.active { background: #fce8e6; border-color: #c5221f; color: #c5221f; }

/* ── Results meta ── */
.nkb-results-meta {
	font-size: 12.5px;
	color: #70757a;
	margin-bottom: 16px;
}
.nkb-results-meta strong { color: #444; }

/* ── Result cards ── */
.nkb-results-list { display: flex; flex-direction: column; gap: 0; }

.nkb-result-card {
	padding: 14px 0 18px;
	border-bottom: 1px solid #f0f0f0;
	cursor: pointer;
}
.nkb-result-card:last-child { border-bottom: none; }
.nkb-result-card:hover .nkb-result-title { text-decoration: underline; }

.nkb-result-breadcrumb {
	display: flex;
	align-items: center;
	gap: 5px;
	margin-bottom: 4px;
}
.nkb-result-favicon {
	width: 16px; height: 16px;
	border-radius: 4px;
	background: linear-gradient(135deg, #0b2b72, #16A37F);
	display: inline-flex; align-items: center; justify-content: center;
	flex-shrink: 0;
}
.nkb-result-favicon svg { display: block; }
.nkb-result-url {
	font-size: 12px;
	color: #202124;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
.nkb-result-url .nkb-crumb-sep { color: #bbb; margin: 0 3px; }
.nkb-result-url .nkb-crumb-part { color: #4d5156; }

.nkb-result-title {
	font-size: 18px;
	font-weight: 400;
	color: #1a0dab;
	margin: 2px 0 5px;
	line-height: 1.3;
}
.nkb-result-snippet {
	font-size: 13.5px;
	color: #4d5156;
	line-height: 1.6;
	margin-bottom: 7px;
}
.nkb-result-meta {
	display: flex;
	align-items: center;
	gap: 6px;
	flex-wrap: wrap;
}
.nkb-meta-chip {
	display: inline-flex;
	align-items: center;
	gap: 3px;
	font-size: 11px;
	font-weight: 600;
	padding: 2px 8px;
	border-radius: 10px;
	text-transform: capitalize;
}
.nkb-chip-public   { background: #e6f4ea; color: #137333; }
.nkb-chip-customer { background: #e8f0fe; color: #1a73e8; }
.nkb-chip-internal { background: #fce8e6; color: #c5221f; }
.nkb-chip-default  { background: #f1f3f4; color: #5f6368; }
.nkb-chip-chunks   { background: #f1f3f4; color: #5f6368; }
.nkb-chip-date     { background: transparent; color: #9aa0a6; font-weight: 400; font-size: 11px; }

/* ── Pagination ── */
.nkb-pagination {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 6px;
	margin-top: 28px;
	flex-wrap: wrap;
}
.nkb-page-btn {
	min-width: 36px; height: 36px;
	border-radius: 50%;
	border: none;
	background: none;
	cursor: pointer;
	font-size: 13px;
	color: #1a73e8;
	font-weight: 500;
	display: flex; align-items: center; justify-content: center;
	transition: background .15s;
}
.nkb-page-btn:hover { background: #e8f0fe; }
.nkb-page-btn.active {
	background: #1a73e8;
	color: #fff;
	cursor: default;
}
.nkb-page-btn:disabled { color: #bbb; cursor: default; }
.nkb-page-btn:disabled:hover { background: none; }
.nkb-page-ellipsis { color: #5f6368; padding: 0 4px; line-height: 36px; }

/* ── Empty / loading states ── */
.nkb-state {
	text-align: center;
	padding: 52px 20px;
	color: #9aa0a6;
}
.nkb-state-icon { font-size: 40px; margin-bottom: 12px; }
.nkb-state-msg { font-size: 15px; margin-bottom: 6px; color: #5f6368; }
.nkb-state-sub { font-size: 13px; color: #9aa0a6; }
.nkb-spinner {
	display: inline-block;
	width: 22px; height: 22px;
	border: 3px solid #e8eaed;
	border-top-color: #1a73e8;
	border-radius: 50%;
	animation: nkb-spin .7s linear infinite;
	vertical-align: middle;
}
@keyframes nkb-spin { to { transform: rotate(360deg); } }

/* ── Detail panel (slide-in from right) ── */
.nkb-panel-overlay {
	position: fixed;
	inset: 0;
	background: rgba(0,0,0,.35);
	z-index: 1050;
	opacity: 0;
	transition: opacity .2s;
	pointer-events: none;
}
.nkb-panel-overlay.open {
	opacity: 1;
	pointer-events: all;
}
.nkb-panel {
	position: fixed;
	top: 0; right: 0; bottom: 0;
	width: min(640px, 92vw);
	background: #fff;
	z-index: 1051;
	display: flex;
	flex-direction: column;
	transform: translateX(100%);
	transition: transform .25s cubic-bezier(.4,0,.2,1);
	box-shadow: -4px 0 28px rgba(0,0,0,.14);
}
.nkb-panel.open { transform: translateX(0); }

.nkb-panel-head {
	display: flex;
	align-items: flex-start;
	gap: 12px;
	padding: 18px 20px 14px;
	border-bottom: 1px solid #e8eaed;
	flex-shrink: 0;
}
.nkb-panel-close {
	background: none; border: none; cursor: pointer;
	color: #5f6368; font-size: 20px; line-height: 1;
	padding: 2px 4px; margin-top: -2px;
	flex-shrink: 0;
}
.nkb-panel-close:hover { color: #202124; }
.nkb-panel-head-info { flex: 1; min-width: 0; }
.nkb-panel-breadcrumb {
	font-size: 11.5px;
	color: #16A37F;
	margin-bottom: 5px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
.nkb-panel-favicon {
	display: inline-flex;
	width: 13px; height: 13px;
	border-radius: 3px;
	background: linear-gradient(135deg, #0b2b72, #16A37F);
	align-items: center; justify-content: center;
	margin-right: 4px;
	vertical-align: middle;
}
.nkb-panel-title {
	font-size: 18px;
	font-weight: 600;
	color: #202124;
	line-height: 1.3;
	margin: 0;
}

.nkb-panel-body {
	flex: 1;
	overflow-y: auto;
	padding: 20px;
}
.nkb-panel-content {
	font-size: 14px;
	color: #3c4043;
	line-height: 1.75;
}
.nkb-panel-content p { margin: 0 0 14px; }
.nkb-panel-content p:last-child { margin-bottom: 0; }
.nkb-panel-content h1,
.nkb-panel-content h2,
.nkb-panel-content h3 {
	color: #202124;
	margin: 18px 0 8px;
	font-weight: 600;
}
.nkb-panel-content ul,
.nkb-panel-content ol { padding-left: 20px; margin: 0 0 14px; }
.nkb-panel-content li { margin-bottom: 5px; }
.nkb-panel-content strong { color: #0b2b72; }
.nkb-panel-content code {
	background: #f1f3f4;
	border-radius: 4px;
	padding: 1px 5px;
	font-size: 13px;
}
.nkb-panel-content blockquote {
	border-left: 3px solid #dadce0;
	padding-left: 14px;
	color: #5f6368;
	margin: 0 0 14px;
}

.nkb-panel-footer {
	padding: 14px 20px;
	border-top: 1px solid #e8eaed;
	display: flex;
	gap: 10px;
	flex-wrap: wrap;
	align-items: center;
	background: #fafafa;
	flex-shrink: 0;
}
.nkb-panel-meta-item {
	display: flex;
	align-items: center;
	gap: 5px;
	font-size: 12px;
	color: #5f6368;
}
.nkb-panel-meta-item strong { color: #444; font-weight: 600; }
.nkb-panel-meta-sep { color: #dadce0; }

/* ── Search mode toggle ── */
.nkb-mode-toggle {
	display: inline-flex;
	align-items: center;
	gap: 0;
	background: #f1f3f4;
	border: 1px solid #dadce0;
	border-radius: 20px;
	padding: 3px;
	margin-top: 10px;
}
.nkb-mode-btn {
	padding: 5px 14px;
	border-radius: 16px;
	border: none;
	background: none;
	font-size: 12px;
	font-weight: 600;
	color: #5f6368;
	cursor: pointer;
	transition: all .18s;
	display: flex;
	align-items: center;
	gap: 5px;
	white-space: nowrap;
}
.nkb-mode-btn.active {
	background: #fff;
	color: #1a73e8;
	box-shadow: 0 1px 4px rgba(0,0,0,.14);
}
.nkb-mode-btn.active.semantic { color: #7b1fa2; }
.nkb-mode-btn svg { flex-shrink: 0; }

/* Semantic mode indicator on results */
.nkb-semantic-badge {
	display: inline-flex;
	align-items: center;
	gap: 5px;
	font-size: 11.5px;
	font-weight: 600;
	color: #7b1fa2;
	background: #f3e5f5;
	border: 1px solid #ce93d8;
	border-radius: 12px;
	padding: 3px 10px;
	margin-bottom: 10px;
}
.nkb-score-bar {
	display: inline-flex;
	align-items: center;
	gap: 4px;
}
.nkb-score-fill {
	height: 4px;
	border-radius: 2px;
	background: linear-gradient(90deg, #7b1fa2, #ba68c8);
}
.nkb-score-label {
	font-size: 10.5px;
	color: #9c27b0;
	font-weight: 600;
}

/* Fallback notice */
.nkb-fallback-notice {
	font-size: 11.5px;
	color: #e65100;
	background: #fff3e0;
	border: 1px solid #ffcc80;
	border-radius: 8px;
	padding: 5px 12px;
	margin-bottom: 10px;
	display: inline-flex;
	align-items: center;
	gap: 5px;
}

/* ── Responsive ── */
@media (max-width: 640px) {
	.nkb-chrome { display: none; }
	.nkb-result-title { font-size: 16px; }
	.nkb-panel { width: 100vw; }
}
		`;
		document.head.appendChild(s);
	}

	// ── Skeleton ──────────────────────────────────────────────────────────────

	_build_skeleton() {
		const $main = $(this.wrapper).find(".layout-main-section");

		this.$root = $(`<div class="nkb-wrap"></div>`).appendTo($main);

		// Browser chrome bar
		this.$chrome = $(`
			<div class="nkb-chrome">
				<div class="nkb-chrome-dots">
					<div class="nkb-chrome-dot nkb-chrome-dot-r"></div>
					<div class="nkb-chrome-dot nkb-chrome-dot-y"></div>
					<div class="nkb-chrome-dot nkb-chrome-dot-g"></div>
				</div>
				<div class="nkb-chrome-bar">
					<span class="nkb-chrome-lock">&#128274;</span>
					<span class="nkb-chrome-url" id="nkb-url-bar">
						nexus://knowledge/public/<strong>—</strong>
					</span>
				</div>
				<button class="nkb-chrome-refresh" id="nkb-refresh-btn" title="Refresh">&#8635;</button>
			</div>
		`).appendTo(this.$root);

		// Search area
		this.$search_area = $(`
			<div class="nkb-search-area">
				<div class="nkb-search-logo">
					<div class="nkb-search-logo-icon">
						<svg viewBox="0 0 24 24" fill="none" width="20" height="20">
							<ellipse cx="12" cy="7" rx="7" ry="2.6" stroke="white" stroke-width="1.4"/>
							<path d="M5 7v4.5c0 1.44 3.13 2.6 7 2.6s7-1.16 7-2.6V7" stroke="white" stroke-width="1.4"/>
							<path d="M5 11.5V16c0 1.44 3.13 2.6 7 2.6s7-1.16 7-2.6v-4.5" stroke="white" stroke-width="1.4" opacity=".6"/>
						</svg>
					</div>
					<div class="nkb-search-logo-text">Nexus <span>Knowledge</span></div>
				</div>
				<div class="nkb-search-box">
					<span class="nkb-search-icon">
						<svg viewBox="0 0 24 24" fill="none" width="18" height="18">
							<circle cx="11" cy="11" r="7" stroke="#9aa0a6" stroke-width="2"/>
							<path d="M16.5 16.5L21 21" stroke="#9aa0a6" stroke-width="2" stroke-linecap="round"/>
						</svg>
					</span>
					<input id="nkb-search-input" class="nkb-search-input"
						type="text" placeholder="Search public knowledge…" autocomplete="off"/>
					<button class="nkb-search-clear" id="nkb-search-clear">&#215;</button>
				</div>
				<div class="nkb-tenant-tag" id="nkb-tenant-tag">
					Loading knowledge source…
				</div>
				<div class="nkb-mode-toggle" id="nkb-mode-toggle">
					<button class="nkb-mode-btn active" data-mode="text" title="Keyword search — fast SQL match on titles and content">
						<svg viewBox="0 0 16 16" fill="none" width="12" height="12">
							<path d="M2 4h12M2 8h8M2 12h5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
						</svg>
						Text
					</button>
					<button class="nkb-mode-btn semantic" data-mode="vector" title="Semantic search — finds conceptually related knowledge using AI embeddings">
						<svg viewBox="0 0 16 16" fill="none" width="12" height="12">
							<circle cx="8" cy="8" r="2.5" stroke="currentColor" stroke-width="1.4"/>
							<path d="M8 2v2M8 12v2M2 8h2M12 8h2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
							<path d="M3.8 3.8l1.4 1.4M10.8 10.8l1.4 1.4M3.8 12.2l1.4-1.4M10.8 5.2l1.4-1.4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity=".6"/>
						</svg>
						Semantic
					</button>
				</div>
			</div>
		`).appendTo(this.$root);

		// Filter bar
		this.$filter_bar = $(`<div class="nkb-filter-bar" id="nkb-filter-bar"></div>`)
			.appendTo(this.$root);

		// Results meta
		this.$results_meta = $(`<div class="nkb-results-meta" id="nkb-results-meta"></div>`)
			.appendTo(this.$root);

		// Results list
		this.$results = $(`<div class="nkb-results-list" id="nkb-results-list"></div>`)
			.appendTo(this.$root);

		// Pagination
		this.$pagination = $(`<div class="nkb-pagination" id="nkb-pagination"></div>`)
			.appendTo(this.$root);

		// Detail panel overlay + panel
		this.$overlay = $(`<div class="nkb-panel-overlay" id="nkb-panel-overlay"></div>`)
			.appendTo($("body"));
		this.$panel = $(`
			<div class="nkb-panel" id="nkb-panel">
				<div class="nkb-panel-head">
					<button class="nkb-panel-close" id="nkb-panel-close">&#215;</button>
					<div class="nkb-panel-head-info">
						<div class="nkb-panel-breadcrumb" id="nkb-panel-breadcrumb"></div>
						<h2 class="nkb-panel-title" id="nkb-panel-title"></h2>
					</div>
				</div>
				<div class="nkb-panel-body">
					<div class="nkb-panel-content" id="nkb-panel-content"></div>
				</div>
				<div class="nkb-panel-footer" id="nkb-panel-footer"></div>
			</div>
		`).appendTo($("body"));

		this._bind_events();
	}

	// ── Events ────────────────────────────────────────────────────────────────

	_bind_events() {
		// Search input with debounce
		let _timer;
		this.$root.find("#nkb-search-input").on("input", (e) => {
			const val = e.target.value;
			this.$root.find("#nkb-search-clear").css("display", val ? "block" : "none");
			clearTimeout(_timer);
			_timer = setTimeout(() => {
				this.state.search = val.trim();
				this.state.page_num = 1;
				this._load();
			}, 380);
		});

		// Clear search
		this.$root.find("#nkb-search-clear").on("click", () => {
			this.$root.find("#nkb-search-input").val("").trigger("input");
		});

		// Refresh
		this.$root.find("#nkb-refresh-btn").on("click", () => this._load());

		// Search mode toggle
		this.$root.find("#nkb-mode-toggle").on("click", "[data-mode]", (e) => {
			const mode = $(e.currentTarget).data("mode");
			if (mode === this.state.search_mode) return;
			this.state.search_mode = mode;
			this.$root.find("#nkb-mode-toggle .nkb-mode-btn").removeClass("active");
			this.$root.find(`#nkb-mode-toggle [data-mode="${mode}"]`).addClass("active");
			this.state.page_num = 1;
			this._load();
		});

		// Close panel
		this.$panel.find("#nkb-panel-close").on("click", () => this._close_panel());
		this.$overlay.on("click", () => this._close_panel());

		// ESC to close panel
		$(document).on("keydown.nkb", (e) => {
			if (e.key === "Escape") this._close_panel();
		});
	}

	// ── Boot: resolve tenant, then load ───────────────────────────────────────

	_boot() {
		frappe.call({
			method: "digitz_ai_nexus.api.knowledge_browser.get_browser_context",
			callback: (r) => {
				const ctx = r.message || {};
				if (ctx.success && ctx.tenant) {
					this.state.tenant = ctx.tenant;
					this.state.tenant_label = ctx.tenant_label || ctx.tenant;
					this._update_chrome();
					this._load();
				} else {
					this._show_state(
						"⚙️",
						"No tenant configured",
						"Set a Default Tenant for Browser in Nexus Settings to get started."
					);
				}
			},
			error: () => {
				this._show_state("⚠️", "Could not load browser context", "Please refresh the page.");
			},
		});
	}

	// ── Update browser chrome URL bar ─────────────────────────────────────────

	_update_chrome() {
		const slug = (this.state.tenant_label || this.state.tenant || "—")
			.toLowerCase().replace(/\s+/g, "-");

		const search = this.state.search
			? `?q=${encodeURIComponent(this.state.search)}`
			: "";
		const ctx = this.state.context
			? `/${encodeURIComponent(this.state.context)}`
			: "";

		this.$root.find("#nkb-url-bar").html(
			`nexus://knowledge/public/<strong>${slug}</strong>${ctx}${search}`
		);

		const label = this.state.tenant_label || this.state.tenant;
		let tagHtml = `Browsing public knowledge from <strong>${label}</strong>`;
		if (this.state.search) {
			tagHtml += ` &nbsp;·&nbsp; results for "<em>${this._esc(this.state.search)}</em>"`;
		}
		this.$root.find("#nkb-tenant-tag").html(tagHtml);
	}

	// ── Data load ─────────────────────────────────────────────────────────────

	_load() {
		if (this.state.loading) return;
		this.state.loading = true;
		this._update_chrome();
		this._show_loading();

		frappe.call({
			method: "digitz_ai_nexus.api.knowledge_browser.get_public_knowledge_feed",
			args: {
				tenant: this.state.tenant || "",
				search: this.state.search || "",
				context: this.state.context || "",
				topic: this.state.topic || "",
				page: this.state.page_num,
				page_size: this.state.page_size,
				search_mode: this.state.search_mode,
			},
			callback: (r) => {
				this.state.loading = false;
				const data = r.message || {};

				if (!data.success) {
					this._show_state(
						"⚙️",
						data.message || "No knowledge available",
						"Check Nexus Settings and ensure a public tenant is configured."
					);
					return;
				}

				this.state.items = data.items || [];
				this.state.total = data.total || 0;
				this.state.contexts = data.contexts || [];
				this.state.topics = data.topics || [];
				// Server reports actual mode used (may fall back from vector → text)
				this.state.active_search_mode = data.search_mode || this.state.search_mode;

				this._render_filters();
				this._render_results();
				this._render_pagination();
			},
			error: () => {
				this.state.loading = false;
				this._show_state("⚠️", "Failed to load knowledge", "Please try again.");
			},
		});
	}

	// ── Filter bar ────────────────────────────────────────────────────────────

	_render_filters() {
		const $bar = this.$filter_bar.empty();

		if (!this.state.contexts.length && !this.state.topics.length) return;

		// Context pills
		if (this.state.contexts.length) {
			$bar.append(`<span class="nkb-filter-label">Context</span>`);

			const $all = $(`<button class="nkb-pill nkb-pill-ctx${!this.state.context ? " active" : ""}">All</button>`);
			$all.on("click", () => { this.state.context = null; this.state.page_num = 1; this._load(); });
			$bar.append($all);

			this.state.contexts.forEach((c) => {
				const active = this.state.context === c ? " active" : "";
				const $p = $(`<button class="nkb-pill nkb-pill-ctx${active}">${this._esc(c)}</button>`);
				$p.on("click", () => {
					this.state.context = this.state.context === c ? null : c;
					this.state.topic = null;
					this.state.page_num = 1;
					this._load();
				});
				$bar.append($p);
			});
		}

		// Separator
		if (this.state.contexts.length && this.state.topics.length) {
			$bar.append(`<span class="nkb-filter-sep">|</span>`);
		}

		// Topic pills
		if (this.state.topics.length) {
			$bar.append(`<span class="nkb-filter-label">Topic</span>`);

			const $all = $(`<button class="nkb-pill nkb-pill-topic${!this.state.topic ? " active" : ""}">All</button>`);
			$all.on("click", () => { this.state.topic = null; this.state.page_num = 1; this._load(); });
			$bar.append($all);

			this.state.topics.forEach((t) => {
				const active = this.state.topic === t ? " active" : "";
				const $p = $(`<button class="nkb-pill nkb-pill-topic${active}">${this._esc(t)}</button>`);
				$p.on("click", () => {
					this.state.topic = this.state.topic === t ? null : t;
					this.state.page_num = 1;
					this._load();
				});
				$bar.append($p);
			});
		}
	}

	// ── Results ───────────────────────────────────────────────────────────────

	_render_results() {
		const $list = this.$results.empty();
		const $meta = this.$results_meta.empty();

		const items = this.state.items;
		const total = this.state.total;
		const search = this.state.search;

		if (!items.length) {
			this._show_state(
				"🔍",
				search ? `No results for "${this._esc(search)}"` : "No public knowledge found",
				search
					? "Try a different search term or clear the filters."
					: "This tenant has no publicly accessible knowledge yet."
			);
			return;
		}

		// Results count line
		const start = (this.state.page_num - 1) * this.state.page_size + 1;
		const end = Math.min(start + items.length - 1, total);
		const activeMode = this.state.active_search_mode;
		const requestedMode = this.state.search_mode;

		let metaHtml = `About <strong>${total.toLocaleString()}</strong> result${total !== 1 ? "s" : ""}` +
			(search ? ` for "<em>${this._esc(search)}</em>"` : "") +
			(total > this.state.page_size ? ` &nbsp;(${start}–${end})` : "");
		$meta.html(metaHtml);

		// Semantic mode badge or fallback notice
		if (search && activeMode === "vector") {
			$list.append(`
				<div class="nkb-semantic-badge">
					<svg viewBox="0 0 14 14" fill="none" width="12" height="12">
						<circle cx="7" cy="7" r="2" stroke="currentColor" stroke-width="1.3"/>
						<path d="M7 1.5v2M7 10.5v2M1.5 7h2M10.5 7h2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
					</svg>
					Semantic search — results ranked by conceptual relevance
				</div>
			`);
		} else if (search && requestedMode === "vector" && activeMode === "text") {
			$list.append(`
				<div class="nkb-fallback-notice">
					⚠ Semantic search unavailable — showing text results instead
				</div>
			`);
		}

		items.forEach((item) => {
			const $card = $(this._card_html(item, activeMode));
			$card.on("click", () => this._open_detail(item.name));
			$list.append($card);
		});
	}

	_card_html(item, activeMode) {
		const breadcrumb = this._breadcrumb_html(item);
		const sensitivity_chip = this._sensitivity_chip(item.sensitivity);
		const chunk_chip = item.chunk_count
			? `<span class="nkb-meta-chip nkb-chip-chunks">&#9679; ${item.chunk_count} chunk${item.chunk_count !== 1 ? "s" : ""}</span>`
			: "";
		const date_chip = item.modified
			? `<span class="nkb-meta-chip nkb-chip-date">${this._relative_date(item.modified)}</span>`
			: "";

		// Relevance bar for semantic results
		let score_chip = "";
		if (activeMode === "vector" && item.score != null) {
			const pct = Math.round(item.score * 100);
			const barW = Math.max(4, Math.round(item.score * 60));
			score_chip = `
				<span class="nkb-score-bar" title="Semantic relevance: ${pct}%">
					<span class="nkb-score-fill" style="width:${barW}px;"></span>
					<span class="nkb-score-label">${pct}%</span>
				</span>
			`;
		}

		return `
			<div class="nkb-result-card" data-name="${this._esc(item.name)}">
				<div class="nkb-result-breadcrumb">
					<span class="nkb-result-favicon">
						<svg viewBox="0 0 12 12" fill="none" width="8" height="8">
							<ellipse cx="6" cy="3.5" rx="4" ry="1.4" stroke="white" stroke-width=".9"/>
							<path d="M2 3.5v2.5c0 .77 1.79 1.4 4 1.4s4-.63 4-1.4V3.5" stroke="white" stroke-width=".9"/>
							<path d="M2 6v2.5c0 .77 1.79 1.4 4 1.4s4-.63 4-1.4V6" stroke="white" stroke-width=".9" opacity=".6"/>
						</svg>
					</span>
					<span class="nkb-result-url">${breadcrumb}</span>
				</div>
				<div class="nkb-result-title">${this._esc(item.title)}</div>
				<div class="nkb-result-snippet">${this._esc(item.snippet || "")}</div>
				<div class="nkb-result-meta">
					${sensitivity_chip}
					${chunk_chip}
					${score_chip}
					${date_chip}
				</div>
			</div>
		`;
	}

	_breadcrumb_html(item) {
		const tenant = this._esc(this.state.tenant_label || this.state.tenant || "nexus");
		let html = `<span style="color:#16A37F;">nexus://knowledge</span>`;
		if (item.context) html += `<span class="nkb-crumb-sep">›</span><span class="nkb-crumb-part">${this._esc(item.context)}</span>`;
		if (item.sub_context) html += `<span class="nkb-crumb-sep">›</span><span class="nkb-crumb-part">${this._esc(item.sub_context)}</span>`;
		if (item.topic) html += `<span class="nkb-crumb-sep">›</span><span class="nkb-crumb-part">${this._esc(item.topic)}</span>`;
		return html;
	}

	_sensitivity_chip(sensitivity) {
		if (!sensitivity) return "";
		const map = {
			public:       ["nkb-chip-public",   "Public"],
			customer:     ["nkb-chip-customer",  "Customer"],
			operational:  ["nkb-chip-internal",  "Operational"],
			internal:     ["nkb-chip-internal",  "Internal"],
		};
		const [cls, label] = map[sensitivity] || ["nkb-chip-default", sensitivity];
		return `<span class="nkb-meta-chip ${cls}">${label}</span>`;
	}

	// ── Pagination ────────────────────────────────────────────────────────────

	_render_pagination() {
		const $pag = this.$pagination.empty();
		const total_pages = Math.ceil(this.state.total / this.state.page_size);
		if (total_pages <= 1) return;

		const cur = this.state.page_num;

		// Previous
		const $prev = $(`<button class="nkb-page-btn" title="Previous">&#8592;</button>`);
		if (cur <= 1) $prev.prop("disabled", true);
		$prev.on("click", () => { if (cur > 1) { this.state.page_num--; this._load(); } });
		$pag.append($prev);

		// Page numbers with ellipsis
		const pages = this._page_range(cur, total_pages);
		let last = 0;
		pages.forEach((p) => {
			if (p - last > 1) $pag.append(`<span class="nkb-page-ellipsis">…</span>`);
			const $btn = $(`<button class="nkb-page-btn${p === cur ? " active" : ""}">${p}</button>`);
			if (p !== cur) {
				$btn.on("click", () => { this.state.page_num = p; this._load(); });
			}
			$pag.append($btn);
			last = p;
		});

		// Next
		const $next = $(`<button class="nkb-page-btn" title="Next">&#8594;</button>`);
		if (cur >= total_pages) $next.prop("disabled", true);
		$next.on("click", () => { if (cur < total_pages) { this.state.page_num++; this._load(); } });
		$pag.append($next);
	}

	_page_range(cur, total) {
		const delta = 2;
		const range = [];
		for (let p = Math.max(1, cur - delta); p <= Math.min(total, cur + delta); p++) {
			range.push(p);
		}
		if (range[0] > 1) range.unshift(1);
		if (range[range.length - 1] < total) range.push(total);
		return range;
	}

	// ── Detail panel ─────────────────────────────────────────────────────────

	_open_detail(name) {
		// Show panel immediately with loading state
		this.$panel.find("#nkb-panel-breadcrumb").text("Loading…");
		this.$panel.find("#nkb-panel-title").text("");
		this.$panel.find("#nkb-panel-content").html(
			`<div class="nkb-state"><div class="nkb-spinner"></div></div>`
		);
		this.$panel.find("#nkb-panel-footer").empty();

		this.$overlay.addClass("open");
		this.$panel.addClass("open");
		$("body").css("overflow", "hidden");

		frappe.call({
			method: "digitz_ai_nexus.api.knowledge_browser.get_knowledge_unit_detail",
			args: { name, tenant: this.state.tenant || "" },
			callback: (r) => {
				const data = r.message || {};
				if (data.success && data.item) {
					this._render_panel(data.item);
				} else {
					this.$panel.find("#nkb-panel-content").html(
						`<div class="nkb-state"><div class="nkb-state-msg">Could not load this knowledge item.</div></div>`
					);
				}
			},
			error: () => {
				this.$panel.find("#nkb-panel-content").html(
					`<div class="nkb-state"><div class="nkb-state-msg">Error loading knowledge item.</div></div>`
				);
			},
		});
	}

	_render_panel(item) {
		// Breadcrumb
		let breadHtml = `<span style="font-size:11px;">`;
		breadHtml += `<span style="display:inline-flex;width:10px;height:10px;border-radius:2px;background:linear-gradient(135deg,#0b2b72,#16A37F);vertical-align:middle;margin-right:5px;"></span>`;
		breadHtml += `nexus://knowledge`;
		if (item.context) breadHtml += ` › ${this._esc(item.context)}`;
		if (item.sub_context) breadHtml += ` › ${this._esc(item.sub_context)}`;
		if (item.topic) breadHtml += ` › ${this._esc(item.topic)}`;
		breadHtml += `</span>`;

		this.$panel.find("#nkb-panel-breadcrumb").html(breadHtml);
		this.$panel.find("#nkb-panel-title").text(item.title || item.name);

		// Content — render HTML if content is HTML, otherwise treat as plain text
		const content = item.content || "";
		const $content = this.$panel.find("#nkb-panel-content");

		if (this._is_html(content)) {
			$content.html(content);
		} else {
			// Convert plain text with newlines to paragraphs
			const paras = content.split(/\n{2,}/).filter(Boolean);
			$content.html(paras.map(p => `<p>${this._esc(p.replace(/\n/g, "<br>"))}</p>`).join(""));
		}

		// Footer metadata
		const $footer = this.$panel.find("#nkb-panel-footer").empty();
		const meta_items = [];

		if (item.context)      meta_items.push(["Context",     item.context]);
		if (item.sub_context)  meta_items.push(["Sub-context", item.sub_context]);
		if (item.topic)        meta_items.push(["Topic",       item.topic]);
		if (item.entity)       meta_items.push(["Entity",      item.entity]);
		if (item.sensitivity)  meta_items.push(["Sensitivity", item.sensitivity]);
		if (item.chunk_count)  meta_items.push(["Chunks",      item.chunk_count]);
		if (item.approved_by)  meta_items.push(["Approved by", item.approved_by]);

		meta_items.forEach(([label, value], i) => {
			if (i > 0) $footer.append(`<span class="nkb-panel-meta-sep">·</span>`);
			$footer.append(`
				<span class="nkb-panel-meta-item">
					<strong>${label}:</strong> ${this._esc(String(value))}
				</span>
			`);
		});
	}

	_close_panel() {
		this.$overlay.removeClass("open");
		this.$panel.removeClass("open");
		$("body").css("overflow", "");
	}

	// ── Loading / empty states ────────────────────────────────────────────────

	_show_loading() {
		this.$results_meta.empty();
		this.$results.html(
			`<div class="nkb-state"><div class="nkb-spinner"></div></div>`
		);
		this.$pagination.empty();
	}

	_show_state(icon, msg, sub = "") {
		this.$results_meta.empty();
		this.$results.html(`
			<div class="nkb-state">
				<div class="nkb-state-icon">${icon}</div>
				<div class="nkb-state-msg">${msg}</div>
				${sub ? `<div class="nkb-state-sub">${sub}</div>` : ""}
			</div>
		`);
		this.$pagination.empty();
	}

	// ── Utilities ─────────────────────────────────────────────────────────────

	_esc(str) {
		return String(str || "")
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	_is_html(str) {
		return /<[a-z][\s\S]*>/i.test(str || "");
	}

	_relative_date(dateStr) {
		try {
			const d = new Date(dateStr);
			const diff = Math.floor((Date.now() - d) / 86400000);
			if (diff === 0) return "Today";
			if (diff === 1) return "Yesterday";
			if (diff < 30) return `${diff} days ago`;
			if (diff < 365) return `${Math.floor(diff / 30)} months ago`;
			return `${Math.floor(diff / 365)} years ago`;
		} catch (_) {
			return "";
		}
	}
}
