"""
DIGITZ Prime — Nexy product-enquiry chat seed
=============================================
Wires the DIGITZ-PRIME tenant for a live "Connect with Nexy" chat that enquires
about DIGITZ Prime products (DIGITZ ERP, DIGITZ CRM, …) using the standalone
`prime_companion` controller.

Creates / updates (idempotent):
  Nexus Live Channel        DIGITZ-PRIME-CHAT   (Website Chat, agent_based=1)
  Nexus AI Agent Profile    PRIME-NEXY-DIGITZ-PRIME   (companion_mode=1)
  Nexus Companion Playbook  DIGITZ Prime Product Enquiry (tenant default)
  Nexus Companion Persona   DIGITZ Prime SMB Buyer
  Nexus Companion Product   DIGITZ ERP, DIGITZ CRM  (challenges_solved, next_step)
  Nexus Chat Category       PRIME-PRODUCTS-DIGITZ-PRIME
                              (use_for_nexy=1, companion_controller_type=prime_companion,
                               visibility External, Email OTP, published)
  Nexus Category Identity Route  -> agent profile (enabled + published)
  Nexus Tenant Configuration     live_chat_enabled=1, default_chat_channel
  Nexus Website Widget      DIGITZ-PRIME-CHAT-WIDGET  (widget_type Chat)

Run:
  bench --site <site> execute digitz_ai_nexus.devtools.seed_digitz_prime_chat.run
"""

import json

import frappe

TENANT = "DIGITZ-PRIME"
CHANNEL_CODE = "DIGITZ-PRIME-CHAT"
AGENT_CODE = "PRIME-NEXY"
CATEGORY_CODE = "PRIME-PRODUCTS"
WIDGET_CODE = "DIGITZ-PRIME-CHAT-WIDGET"

DEFAULT_ORIGINS = [
    "https://digitzprime.com",
    "https://www.digitzprime.com",
    "https://nexusailive.com",
    "http://127.0.0.1:8512",
    "http://localhost:8512",
]

def _p(product_name, category, description, features, benefits, challenges_solved,
       typical_outcomes):
    return {
        "product_name": product_name,
        "category": category,
        "description": description,
        "features": features,
        "benefits": benefits,
        "challenges_solved": challenges_solved,
        "typical_outcomes": typical_outcomes,
        "next_step": "Consultation Request",
        "conversion_type": "Meeting Booking",
        "conversion_message": f"Book a walkthrough of {product_name} with a specialist.",
    }


PRODUCTS = [
    _p("DIGITZ ERP", "ERP",
       "An integrated ERP for retail and distribution — accounting, inventory, purchasing "
       "and multi-branch operations in one place.",
       "Multi-branch inventory\nAccounting & GST\nPurchase & supplier management\nPoint of sale\n"
       "Real-time stock visibility",
       "Stop stock leakage across branches\nOne source of truth for accounts\nFaster month-end close",
       "stock inventory warehouse branches accounting finance gst purchase procurement supplier "
       "billing invoicing reconciliation retail distribution point-of-sale erp",
       "Reduced stock-outs, faster reconciliation, unified multi-branch reporting."),
    _p("NEXUS AI", "AI",
       "An AI chat companion that engages website visitors, answers questions, qualifies "
       "enquiries and converts them into leads and bookings — 24/7.",
       "AI website chat\nVisitor engagement\nEnquiry qualification\nLead capture\nMeeting booking",
       "Capture leads round the clock\nQualify enquiries automatically\nBook meetings without staff time",
       "website chat chatbot ai assistant visitor engagement enquiry qualification lead capture "
       "conversion automation support answering questions bot conversational",
       "More qualified leads from the website and faster response to visitors."),
    _p("DIGITZ CRM", "CRM",
       "A sales CRM to capture leads, manage the pipeline and automate follow-ups so no "
       "enquiry slips through.",
       "Lead capture\nPipeline stages\nFollow-up reminders\nQuotation tracking\nSales reporting",
       "Never miss a follow-up\nSee the whole pipeline at a glance\nFaster quote-to-close",
       "lead leads followup follow-up pipeline sales enquiry conversion quotation crm customer "
       "relationship prospect deals closing reminders marketing",
       "Higher lead-to-deal conversion and consistent follow-up discipline."),
    _p("DIGITZ HR-PAYROLL", "HR & Payroll",
       "HR and payroll software covering attendance, leave, salary processing and statutory "
       "compliance for growing teams.",
       "Attendance & biometric\nLeave management\nPayroll & payslips\nStatutory compliance\n"
       "Employee self-service",
       "Run payroll in minutes\nAccurate attendance and leave\nCompliant salary processing",
       "payroll salary wages attendance biometric leave hr human-resources employee staff "
       "payslip compliance esi pf gratuity overtime timesheet recruitment onboarding",
       "Payroll cycle cut from days to minutes with accurate attendance."),
    _p("DIGITZ PROJECT ACCOUNTING", "Project Accounting",
       "Project-based accounting for costing, budgeting, billing and profitability tracking "
       "across projects.",
       "Project costing\nBudget vs actual\nMilestone billing\nWIP tracking\nProject profitability",
       "Know each project's true cost\nBill milestones on time\nControl budget overruns",
       "project costing budget billing profitability wip work-in-progress milestone contract "
       "estimate accounting projects margin overrun timesheet expenses",
       "Clear project profitability and controlled budget overruns."),
    _p("DIGITZ JOB ORDERS", "Job Orders",
       "Job order and work order management for manufacturing and workshops — from job card "
       "to material issue and completion.",
       "Job cards\nWork orders\nMaterial issue\nProduction stages\nJob costing",
       "Track every job to completion\nControl material consumption\nKnow job-level cost",
       "job order work-order jobcard job-card manufacturing production workshop assembly material "
       "issue bom fabrication shop-floor jobs costing",
       "Full visibility of jobs on the shop floor and accurate job costing."),
    _p("DIGITZ TRACKER", "Tracking",
       "Asset and vehicle tracking with live location, movement history and utilisation "
       "reporting for fleets and equipment.",
       "GPS location\nMovement history\nGeofencing\nUtilisation reports\nAsset register",
       "Know where assets are\nImprove fleet utilisation\nReduce unauthorised use",
       "tracking gps vehicle fleet asset location movement geofence route utilisation equipment "
       "logistics transport monitoring live-location",
       "Better fleet utilisation and reduced unauthorised asset use."),
    _p("DIGITZ SERVICE TRACKER", "Service Management",
       "Field service and AMC management — service tickets, technician scheduling, complaints "
       "and maintenance contracts.",
       "Service tickets\nTechnician scheduling\nAMC contracts\nComplaint tracking\nService history",
       "Resolve complaints faster\nNever miss an AMC renewal\nSee full service history",
       "service ticket complaint amc maintenance field-service technician scheduling warranty "
       "breakdown repair support after-sales contract renewal helpdesk",
       "Faster complaint resolution and no missed AMC renewals."),
]


def _ensure_channel():
    name = frappe.db.get_value(
        "Nexus Live Channel", {"channel_code": CHANNEL_CODE, "tenant": TENANT}, "name"
    )
    doc = frappe.get_doc("Nexus Live Channel", name) if name else frappe.new_doc("Nexus Live Channel")
    if not name:
        doc.channel_code = CHANNEL_CODE
        doc.tenant = TENANT
    doc.channel_name = "DIGITZ Prime Chat"
    doc.channel_type = "Website Chat"
    doc.enabled = 1
    doc.agent_based = 1
    doc.requires_visitor_email = 0
    if doc.meta.has_field("description"):
        doc.description = "Live Nexy product-enquiry chat for DIGITZ Prime."
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_playbook():
    name = frappe.db.get_value(
        "Nexus Companion Playbook",
        {"tenant": TENANT, "playbook_name": "DIGITZ Prime Product Enquiry"},
        "name",
    )
    doc = (
        frappe.get_doc("Nexus Companion Playbook", name)
        if name
        else frappe.new_doc("Nexus Companion Playbook")
    )
    doc.playbook_name = "DIGITZ Prime Product Enquiry"
    doc.tenant = TENANT
    doc.enabled = 1
    doc.is_default = 1
    if doc.meta.has_field("discovery_questions"):
        doc.discovery_questions = (
            "What kind of business do you run?\n"
            "What systems or tools are you using today?\n"
            "What is the biggest operational challenge you want to solve?"
        )
    if doc.meta.has_field("qualification_questions"):
        doc.qualification_questions = (
            "How many branches / users?\n"
            "What is your timeline to adopt a new system?"
        )
    if doc.meta.has_field("next_step_options"):
        doc.next_step_options = "Book a product walkthrough\nRequest a consultation"
    if doc.meta.has_field("capability_summary_heading"):
        doc.capability_summary_heading = "DIGITZ Prime Products"
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_persona():
    name = frappe.db.get_value(
        "Nexus Companion Persona",
        {"tenant": TENANT, "persona_name": "DIGITZ Prime SMB Buyer"},
        "name",
    )
    doc = (
        frappe.get_doc("Nexus Companion Persona", name)
        if name
        else frappe.new_doc("Nexus Companion Persona")
    )
    doc.persona_name = "DIGITZ Prime SMB Buyer"
    doc.tenant = TENANT
    doc.enabled = 1
    if doc.meta.has_field("industry"):
        doc.industry = "Retail, Distribution, Services"
    if doc.meta.has_field("challenges"):
        doc.challenges = "Manual processes, disconnected systems, stock and follow-up gaps."
    if doc.meta.has_field("pain_points"):
        doc.pain_points = "Spreadsheets, missed follow-ups, no real-time visibility."
    if doc.meta.has_field("goals"):
        doc.goals = "One integrated system, less manual work, better visibility."
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_products(chat_category):
    names = []
    for p in PRODUCTS:
        existing = frappe.db.get_value(
            "Nexus Companion Product",
            {"tenant": TENANT, "product_name": p["product_name"]},
            "name",
        )
        doc = (
            frappe.get_doc("Nexus Companion Product", existing)
            if existing
            else frappe.new_doc("Nexus Companion Product")
        )
        doc.product_name = p["product_name"]
        doc.tenant = TENANT
        doc.enabled = 1
        doc.chat_category = chat_category
        for field in ("category", "description", "features", "benefits", "challenges_solved",
                      "typical_outcomes", "next_step", "conversion_type", "conversion_message"):
            if doc.meta.has_field(field) and p.get(field) is not None:
                setattr(doc, field, p[field])
        doc.save(ignore_permissions=True)
        names.append(doc.name)
    return names


def _summary_of(p):
    """One-line catalogue summary — the product's description first sentence.
    Admins can refine these on the Playbook's Product Items rows afterwards."""
    desc = (p.get("description") or "").strip()
    first = desc.split(". ")[0].strip().rstrip(".")
    return (first + ".") if first else p["product_name"]


def _ensure_playbook_products(playbook, product_names):
    """Populate the playbook's product_items child table — the source the
    prime_companion catalogue summary renders from (mirrors capability_items)."""
    doc = frappe.get_doc("Nexus Companion Playbook", playbook)
    if not doc.meta.has_field("product_items"):
        return 0
    doc.set("product_items", [])
    for p, name in zip(PRODUCTS, product_names):
        doc.append("product_items", {
            "product": name,
            "display_title": p["product_name"],
            "short_description": _summary_of(p),
            "enabled": 1,
        })
    doc.save(ignore_permissions=True)
    return len(doc.product_items)


def _ensure_agent(playbook):
    name = frappe.db.get_value(
        "Nexus AI Agent Profile", {"agent_code": AGENT_CODE, "tenant": TENANT}, "name"
    )
    doc = (
        frappe.get_doc("Nexus AI Agent Profile", name)
        if name
        else frappe.new_doc("Nexus AI Agent Profile")
    )
    if not name:
        doc.agent_code = AGENT_CODE
        doc.tenant = TENANT
    doc.agent_name = "Nexy — DIGITZ Prime"
    doc.agent_role = "Sales"
    doc.status = "Idle"
    doc.behavior_prompt = (
        "You are Nexy, the DIGITZ Prime product companion. Help visitors understand which "
        "DIGITZ Prime product fits their business need, then guide them to book a walkthrough "
        "with a DIGITZ Prime specialist. Stay grounded in confirmed product knowledge."
    )
    if doc.meta.has_field("companion_mode"):
        doc.companion_mode = 1
    if doc.meta.has_field("companion_playbook"):
        doc.companion_playbook = playbook
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_category(channel):
    name = frappe.db.get_value(
        "Nexus Chat Category", {"category_code": CATEGORY_CODE, "tenant": TENANT}, "name"
    )
    doc = (
        frappe.get_doc("Nexus Chat Category", name)
        if name
        else frappe.new_doc("Nexus Chat Category")
    )
    if not name:
        doc.category_code = CATEGORY_CODE
        doc.tenant = TENANT
    doc.category_label = "DIGITZ Prime Products"
    doc.channel = channel
    doc.visibility = "External"
    doc.enabled = 1
    doc.published = 1
    doc.use_for_nexy = 1
    doc.companion_controller_type = "prime_companion"
    doc.identity_verification_mode = "Email OTP"
    if doc.meta.has_field("description"):
        doc.description = "Ask about DIGITZ Prime products — ERP, CRM and more."
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_route(channel, chat_category, agent):
    name = frappe.db.get_value(
        "Nexus Category Identity Route",
        {"chat_category": chat_category, "ai_agent_profile": agent},
        "name",
    )
    doc = (
        frappe.get_doc("Nexus Category Identity Route", name)
        if name
        else frappe.new_doc("Nexus Category Identity Route")
    )
    doc.tenant = TENANT
    doc.channel = channel
    doc.chat_category = chat_category
    doc.ai_agent_profile = agent
    doc.enabled = 1
    doc.published = 1
    if doc.meta.has_field("priority"):
        doc.priority = 10
    # Attach a tenant public knowledge profile if one exists (optional).
    kp = frappe.db.get_value("Knowledge Profile", {"tenant": TENANT}, "name")
    if kp and doc.meta.has_field("public_knowledge_profile"):
        doc.public_knowledge_profile = kp
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_tenant_config(channel):
    """Enable live chat on the tenant's (single) enabled configuration, or create one."""
    name = frappe.db.get_value(
        "Nexus Tenant Configuration", {"tenant": TENANT, "enabled": 1}, "name"
    ) or frappe.db.get_value("Nexus Tenant Configuration", {"tenant": TENANT}, "name")
    doc = (
        frappe.get_doc("Nexus Tenant Configuration", name)
        if name
        else frappe.new_doc("Nexus Tenant Configuration")
    )
    if not name:
        doc.configuration_name = f"{TENANT} Production"
        doc.tenant = TENANT
        doc.enabled = 1
        if doc.meta.has_field("configuration_type"):
            doc.configuration_type = "Production"
        if doc.meta.has_field("is_default"):
            doc.is_default = 1
        if doc.meta.has_field("activation_status"):
            doc.activation_status = "Active"
    if doc.meta.has_field("live_chat_enabled"):
        doc.live_chat_enabled = 1
    if doc.meta.has_field("default_chat_channel"):
        doc.default_chat_channel = channel
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_widget(channel, origins):
    doc = (
        frappe.get_doc("Nexus Website Widget", WIDGET_CODE)
        if frappe.db.exists("Nexus Website Widget", WIDGET_CODE)
        else frappe.new_doc("Nexus Website Widget")
    )
    if not doc.get("widget_code"):
        doc.widget_code = WIDGET_CODE
    doc.widget_name = "DIGITZ Prime Chat"
    doc.channel = channel
    doc.enabled = 1
    doc.knowledge_delivery_enabled = 1
    if doc.meta.has_field("widget_type"):
        doc.widget_type = "Chat"
    doc.allowed_domains_json = json.dumps(origins)
    if doc.meta.has_field("allowed_domains"):
        doc.set("allowed_domains", [])
        for o in origins:
            doc.append("allowed_domains", {"domain": o})
    doc.save(ignore_permissions=True)
    return doc.name


def run(origins=None):
    origins = origins or DEFAULT_ORIGINS
    if isinstance(origins, str):
        origins = frappe.parse_json(origins)

    if not frappe.db.exists("Nexus Tenant", TENANT):
        frappe.throw(f"Tenant {TENANT} not found — run the docs knowledge seed first.")

    channel = _ensure_channel()
    playbook = _ensure_playbook()
    _ensure_persona()
    agent = _ensure_agent(playbook)
    category = _ensure_category(channel)
    products = _ensure_products(category)
    playbook_products = _ensure_playbook_products(playbook, products)
    route = _ensure_route(channel, category, agent)
    config = _ensure_tenant_config(channel)
    widget = _ensure_widget(channel, origins)
    frappe.db.commit()

    result = {
        "channel": channel,
        "agent": agent,
        "playbook": playbook,
        "category": category,
        "products": products,
        "playbook_product_items": playbook_products,
        "route": route,
        "tenant_configuration": config,
        "widget": widget,
        "widget_code": WIDGET_CODE,
        "origins": origins,
    }
    print(json.dumps(result, indent=2, default=str))
    return result
