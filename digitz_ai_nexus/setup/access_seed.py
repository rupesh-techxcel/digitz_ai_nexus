import frappe


PUBLIC_POLICY = "Public"


def _find(doctype, fieldname, value, tenant=None):
    """Locate a record by its identifying field + optional tenant. Returns doc name or None."""
    filters = {fieldname: value}
    if tenant:
        filters["tenant"] = tenant
    return frappe.db.get_value(doctype, filters, "name")


def ensure_access_policy(
    policy_name,
    access_level="Public",
    sensitivity="public",
    description="",
    primitive=False,
    tenant=None,
):
    policy_name = (policy_name or "").strip()
    if not policy_name:
        frappe.throw("Policy name is required.")

    existing = _find("Nexus Access Policy", "policy_name", policy_name, tenant)

    if existing:
        doc = frappe.get_doc("Nexus Access Policy", existing)
    else:
        doc = frappe.new_doc("Nexus Access Policy")
        doc.policy_name = policy_name
        if tenant and doc.meta.has_field("tenant"):
            doc.tenant = tenant

    if doc.meta.has_field("disabled"):
        doc.disabled = 0
    if doc.meta.has_field("access_level"):
        doc.access_level = access_level
    if doc.meta.has_field("sensitivity"):
        doc.sensitivity = sensitivity
    if doc.meta.has_field("description"):
        doc.description = description
    if doc.meta.has_field("is_primitive"):
        doc.is_primitive = 1 if policy_name.lower() == "public" else 0

    doc.save(ignore_permissions=True)
    return doc.name


def ensure_access_category(
    category_name,
    policies,
    title=None,
    description="",
    priority=10,
    tenant=None,
):
    category_name = (category_name or "").strip()
    if not category_name:
        frappe.throw("Access Category name is required.")

    existing = _find("Nexus Access Category", "category_name", category_name, tenant)

    if existing:
        doc = frappe.get_doc("Nexus Access Category", existing)
    else:
        doc = frappe.new_doc("Nexus Access Category")
        doc.category_name = category_name
        if tenant and doc.meta.has_field("tenant"):
            doc.tenant = tenant

    doc.title = title or category_name
    doc.disabled = 0
    doc.priority = priority
    doc.description = description or ""

    existing_policies = {
        row.access_policy
        for row in (doc.get("allowed_policies") or [])
        if row.access_policy
    }

    for policy in policies or []:
        policy = (policy or "").strip()
        if not policy:
            continue

        if not frappe.db.exists("Nexus Access Policy", policy):
            policy = ensure_access_policy(
                policy_name=policy,
                access_level="Public" if policy.lower() == "public" else "Role Restricted",
                sensitivity="public" if policy.lower() == "public" else "internal",
                description=f"Auto-created access policy: {policy}",
                tenant=tenant,
            )

        if policy not in existing_policies:
            doc.append("allowed_policies", {
                "access_policy": policy,
                "description": f"Allows {policy} knowledge.",
            })

    doc.save(ignore_permissions=True)
    return doc.name


def seed_default_access_governance(tenant=None):
    """
    Seed minimum Nexus access governance records under the given tenant.

    Public is the only primitive/system policy.
    Internal and Restricted are example user-defined policies.
    """
    public_policy = ensure_access_policy(
        policy_name="Public",
        access_level="Public",
        sensitivity="public",
        description="Primitive system policy. Public knowledge accessible through channels that allow Public.",
        primitive=True,
        tenant=tenant,
    )

    internal_policy = ensure_access_policy(
        policy_name="Internal",
        access_level="Internal",
        sensitivity="internal",
        description="Example user-defined policy for internal knowledge.",
        tenant=tenant,
    )

    restricted_policy = ensure_access_policy(
        policy_name="Restricted",
        access_level="Role Restricted",
        sensitivity="confidential",
        description="Example user-defined policy for restricted knowledge.",
        tenant=tenant,
    )

    public_access = ensure_access_category(
        category_name="Public Access",
        title="Public Access",
        policies=[public_policy],
        description="Allows Public knowledge only.",
        priority=10,
        tenant=tenant,
    )

    internal_access = ensure_access_category(
        category_name="Internal Access",
        title="Internal Access",
        policies=[public_policy, internal_policy],
        description="Allows Public and Internal knowledge.",
        priority=20,
        tenant=tenant,
    )

    restricted_access = ensure_access_category(
        category_name="Restricted Access",
        title="Restricted Access",
        policies=[public_policy, internal_policy, restricted_policy],
        description="Allows Public, Internal, and Restricted knowledge.",
        priority=30,
        tenant=tenant,
    )

    frappe.db.commit()

    return {
        "success": True,
        "message": "Nexus access governance seed completed.",
        "policies": [public_policy, internal_policy, restricted_policy],
        "categories": [public_access, internal_access, restricted_access],
    }
