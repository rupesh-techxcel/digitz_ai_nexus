import frappe

from digitz_ai_nexus.setup.access_seed import seed_default_access_governance
from digitz_ai_nexus.devtools.sync_workspace_blocks import sync_all_workspace_blocks

NEXUS_LOGO = "/assets/digitz_ai_nexus/images/nexus-ai.png"
STANDARD_WORKSPACES_TO_HIDE = (
    "Workspaces",
    "Website",
    "Websites",
    "Tools",
    "Integrations",
    "Build",
)


def after_install():
    """
    Called by Frappe when digitz_ai_nexus is installed on a site.
    Only sets website branding — access governance records are tenant-scoped
    and are seeded by digitz_ai_nexus_live.after_install (which creates the
    DEFAULT tenant first and then calls seed_defaults with that tenant).
    """
    seed_website_settings()
    hide_standard_workspaces()
    sync_all_workspace_blocks()
    frappe.db.commit()
    frappe.logger().info("Nexus Core install complete.")


def seed_defaults(tenant=None):
    """
    Seed core Nexus access governance records for a given tenant.
    Called by digitz_ai_nexus_live.setup.install after the DEFAULT tenant
    is created. Not called from after_install — tenant is required.
    """
    result = seed_default_access_governance(tenant=tenant)
    frappe.db.commit()
    frappe.logger().info("Nexus Core access governance seeded for tenant: %s", tenant)
    return result


def seed_website_settings():
    """
    Configure Website Settings and System Settings with Nexus AI branding.
    Sets app name, logo, login page image, favicon, and disables public signup.
    Safe to re-run — only overwrites fields that are blank.
    """
    # System Settings controls the app name shown on the login page.
    # Use db.set_value to avoid triggering mandatory validation on other
    # System Settings fields that may not be set yet on a fresh site.
    current_app_name = frappe.db.get_single_value("System Settings", "app_name")
    if not current_app_name or current_app_name == "Frappe":
        frappe.db.set_value("System Settings", "System Settings", "app_name", "NEXUS AI")

    ws = frappe.get_doc("Website Settings")

    if not ws.app_name:
        ws.app_name = "NEXUS AI"

    if not ws.app_logo:
        ws.app_logo = NEXUS_LOGO

    if not ws.favicon:
        ws.favicon = NEXUS_LOGO

    if not ws.splash_image:
        ws.splash_image = NEXUS_LOGO

    if not ws.footer_logo:
        ws.footer_logo = NEXUS_LOGO

    if not ws.brand_html:
        ws.brand_html = (
            f'<a href="/" class="navbar-brand">'
            f'<img src="{NEXUS_LOGO}" alt="NEXUS AI" '
            f'style="height:30px;width:auto;vertical-align:middle;">'
            f'</a>'
        )

    if not ws.copyright:
        ws.copyright = "DIGITZ AI Nexus"

    ws.disable_signup = 1

    if not ws.home_page:
        ws.home_page = "index"

    ws.save(ignore_permissions=True)
    frappe.logger().info("Nexus website settings seeded.")


def hide_standard_workspaces():
    """
    Hide Frappe workspaces that should not appear in a Nexus-first install.
    Safe to re-run and tolerant of framework/version naming differences.
    """
    existing_workspaces = frappe.get_all(
        "Workspace",
        filters={"name": ("in", STANDARD_WORKSPACES_TO_HIDE)},
        pluck="name",
    )

    for workspace in existing_workspaces:
        frappe.db.set_value("Workspace", workspace, "is_hidden", 1, update_modified=False)

    if existing_workspaces:
        frappe.logger().info(
            "Nexus hidden standard workspaces: %s",
            ", ".join(sorted(existing_workspaces)),
        )
