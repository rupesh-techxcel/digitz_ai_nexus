import frappe


def _require_admin():
    frappe.only_for("System Manager")


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_access_role_allocation_data(role=None):
    """
    Returns all Frappe roles, all enabled Nexus Access Categories,
    and (when role is given) the current Nexus Role Access Category
    assignments for that role.
    """
    _require_admin()

    roles = frappe.get_all(
        "Role",
        filters={"disabled": 0, "name": ["not in", ["All", "Administrator"]]},
        fields=["name"],
        order_by="name asc",
        limit_page_length=1000,
    )

    categories = frappe.get_all(
        "Nexus Access Category",
        filters={"disabled": 0},
        fields=["name", "category_name", "title", "priority", "description"],
        order_by="priority asc, category_name asc",
        limit_page_length=500,
    )

    assignments = []
    if role:
        assignments = frappe.get_all(
            "Nexus Role Access Category",
            filters={"role": role, "disabled": 0},
            fields=["name", "role", "access_category", "disabled", "description"],
            order_by="access_category asc",
            limit_page_length=500,
        )

    return {
        "roles": [r.name for r in roles],
        "categories": categories,
        "assignments": assignments,
    }


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

@frappe.whitelist()
def save_role_access_categories(role, categories_to_assign, assignments_to_remove=None):
    """
    Manages Nexus Role Access Category records for a role.

    - categories_to_assign: list of Nexus Access Category names to create mappings for.
    - assignments_to_remove: list of Nexus Role Access Category docnames to delete.

    Does NOT write to Nexus Access Policy or any legacy fields.
    Does NOT create direct Role → Policy mappings.
    """
    _require_admin()

    if not role:
        frappe.throw("Role is required.")

    categories_to_assign = (
        frappe.parse_json(categories_to_assign)
        if isinstance(categories_to_assign, str)
        else (categories_to_assign or [])
    )
    assignments_to_remove = (
        frappe.parse_json(assignments_to_remove)
        if isinstance(assignments_to_remove, str)
        else (assignments_to_remove or [])
    )

    for docname in assignments_to_remove:
        if docname and frappe.db.exists("Nexus Role Access Category", docname):
            frappe.delete_doc(
                "Nexus Role Access Category",
                docname,
                ignore_permissions=True,
                force=True,
            )

    for category in categories_to_assign:
        if not category:
            continue

        already_exists = frappe.db.exists(
            "Nexus Role Access Category",
            {"role": role, "access_category": category, "disabled": 0},
        )
        if not already_exists:
            doc = frappe.new_doc("Nexus Role Access Category")
            doc.role = role
            doc.access_category = category
            doc.disabled = 0
            doc.insert(ignore_permissions=True)

    frappe.db.commit()

    updated_assignments = frappe.get_all(
        "Nexus Role Access Category",
        filters={"role": role, "disabled": 0},
        fields=["name", "role", "access_category", "disabled"],
        order_by="access_category asc",
        limit_page_length=500,
    )

    return {
        "status": "success",
        "role": role,
        "assignments": updated_assignments,
    }


# ---------------------------------------------------------------------------
# Effective policy preview
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_effective_policies_for_role(role):
    """
    Derives the effective Nexus Access Policies for a role by following:

        Role → Nexus Role Access Category
             → Nexus Access Category
             → Nexus Access Category Policy
             → Nexus Access Policy

    Returns a preview only.  No direct Role → Policy record is created.
    """
    _require_admin()

    if not role:
        return {"role": role, "categories": [], "policies": []}

    category_names = frappe.get_all(
        "Nexus Role Access Category",
        filters={"role": role, "disabled": 0},
        pluck="access_category",
    )

    if not category_names:
        return {"role": role, "categories": [], "policies": []}

    policy_rows = frappe.get_all(
        "Nexus Access Category Policy",
        filters={
            "parent": ["in", category_names],
            "parentfield": "allowed_policies",
        },
        fields=["parent", "access_policy"],
        limit_page_length=1000,
    )

    unique_policy_names = list({r.access_policy for r in policy_rows if r.access_policy})

    policies = []
    if unique_policy_names:
        policies = frappe.get_all(
            "Nexus Access Policy",
            filters={"name": ["in", unique_policy_names], "disabled": 0},
            fields=["name", "policy_name", "access_level", "sensitivity", "is_primitive", "description"],
            order_by="policy_name asc",
        )

    categories = frappe.get_all(
        "Nexus Access Category",
        filters={"name": ["in", category_names]},
        fields=["name", "category_name", "title", "description"],
        order_by="priority asc",
    )

    return {
        "role": role,
        "categories": categories,
        "policies": policies,
    }


# ---------------------------------------------------------------------------
# Category detail preview
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_category_policies(category):
    """
    Returns the Nexus Access Policies included in a given Nexus Access Category.
    Used for the category detail preview panel.
    """
    _require_admin()

    if not category:
        return {"category": category, "policies": []}

    policy_rows = frappe.get_all(
        "Nexus Access Category Policy",
        filters={"parent": category, "parentfield": "allowed_policies"},
        fields=["access_policy", "description"],
        limit_page_length=500,
    )

    policy_names = [r.access_policy for r in policy_rows if r.access_policy]

    policies = []
    if policy_names:
        policies = frappe.get_all(
            "Nexus Access Policy",
            filters={"name": ["in", policy_names]},
            fields=["name", "policy_name", "access_level", "sensitivity", "is_primitive", "disabled", "description"],
            order_by="policy_name asc",
        )

    return {
        "category": category,
        "policies": policies,
    }
