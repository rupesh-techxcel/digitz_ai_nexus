import frappe


PUBLIC_POLICY = "Public"


def _exists(doctype, name):
    return frappe.db.exists(doctype, name)


def _set_if_field_exists(doc, fieldname, value):
    if doc.meta.has_field(fieldname):
        doc.set(fieldname, value)


def ensure_access_policy(
    policy_name,
    access_level="Public",
    sensitivity="public",
    description="",
    primitive=False,
):
    """
    Create or update a Nexus Access Policy.

    Final rule:
    - Public is the only primitive/system policy.
    - Anything other than Public is user-defined.
    """

    policy_name = (policy_name or "").strip()

    if not policy_name:
        frappe.throw("Policy name is required.")

    if _exists("Nexus Access Policy", policy_name):
        doc = frappe.get_doc("Nexus Access Policy", policy_name)
    else:
        doc = frappe.new_doc("Nexus Access Policy")
        doc.policy_name = policy_name

    _set_if_field_exists(doc, "disabled", 0)
    _set_if_field_exists(doc, "access_level", access_level)
    _set_if_field_exists(doc, "sensitivity", sensitivity)
    _set_if_field_exists(doc, "description", description)

    if doc.meta.has_field("is_primitive"):
        doc.is_primitive = 1 if policy_name.lower() == "public" else 0

    doc.save(ignore_permissions=True)
    return doc.name


def ensure_access_category(category_name, policies, title=None, description="", priority=10):
    """
    Create or update Nexus Access Category and its allowed policy rows.
    """

    category_name = (category_name or "").strip()

    if not category_name:
        frappe.throw("Access Category name is required.")

    if _exists("Nexus Access Category", category_name):
        doc = frappe.get_doc("Nexus Access Category", category_name)
    else:
        doc = frappe.new_doc("Nexus Access Category")
        doc.category_name = category_name

    doc.title = title or category_name
    doc.disabled = 0
    doc.priority = priority
    doc.description = description or ""

    existing = {
        row.access_policy
        for row in (doc.get("allowed_policies") or [])
        if row.access_policy
    }

    for policy in policies or []:
        policy = (policy or "").strip()

        if not policy:
            continue

        if not frappe.db.exists("Nexus Access Policy", policy):
            # Only Public is a primitive policy. Other policies created here are just user-defined examples.
            ensure_access_policy(
                policy_name=policy,
                access_level="Public" if policy.lower() == "public" else "Role Restricted",
                sensitivity="public" if policy.lower() == "public" else "internal",
                description=f"Auto-created access policy: {policy}",
            )

        if policy not in existing:
            doc.append("allowed_policies", {
                "access_policy": policy,
                "description": f"Allows {policy} knowledge."
            })

    doc.save(ignore_permissions=True)
    return doc.name


def ensure_role_access_category(role, access_category, description=""):
    """
    Create a global Role → Access Category mapping.
    """

    if not role or not access_category:
        return None

    if not frappe.db.exists("Role", role):
        return None

    existing = frappe.get_all(
        "Nexus Role Access Category",
        filters={
            "role": role,
            "access_category": access_category,
            "tenant": ["in", ["", None]],
            "business_unit": ["in", ["", None]],
            "project": ["in", ["", None]],
        },
        fields=["name"],
        limit_page_length=1,
    )

    if existing:
        doc = frappe.get_doc("Nexus Role Access Category", existing[0].name)
    else:
        doc = frappe.new_doc("Nexus Role Access Category")
        doc.role = role
        doc.access_category = access_category

    doc.disabled = 0
    doc.description = description or ""
    doc.save(ignore_permissions=True)

    return doc.name


def ensure_channel(channel_name, channel_type, description=""):
    """
    Create or update Nexus Channel.
    """

    channel_name = (channel_name or "").strip()

    if not channel_name:
        frappe.throw("Channel name is required.")

    if _exists("Nexus Channel", channel_name):
        doc = frappe.get_doc("Nexus Channel", channel_name)
    else:
        doc = frappe.new_doc("Nexus Channel")
        doc.channel_name = channel_name

    doc.channel_type = channel_type
    doc.disabled = 0
    doc.description = description or ""
    doc.save(ignore_permissions=True)

    return doc.name


def ensure_channel_access_category(channel, access_category, description=""):
    """
    Create a global Channel → Access Category mapping.
    """

    if not channel or not access_category:
        return None

    if not frappe.db.exists("Nexus Channel", channel):
        return None

    existing = frappe.get_all(
        "Nexus Channel Access Category",
        filters={
            "channel": channel,
            "access_category": access_category,
            "tenant": ["in", ["", None]],
            "business_unit": ["in", ["", None]],
            "project": ["in", ["", None]],
        },
        fields=["name"],
        limit_page_length=1,
    )

    if existing:
        doc = frappe.get_doc("Nexus Channel Access Category", existing[0].name)
    else:
        doc = frappe.new_doc("Nexus Channel Access Category")
        doc.channel = channel
        doc.access_category = access_category

    doc.disabled = 0
    doc.description = description or ""
    doc.save(ignore_permissions=True)

    return doc.name


def seed_default_access_governance():
    """
    Seed minimum Nexus access governance records.

    Important:
    - Public is the only primitive/system policy.
    - Internal and Restricted are only example user-defined policies.
    - Non-public policies are accessible only through Role Access Category
      and Channel Access Category mapping.
    """

    public_policy = ensure_access_policy(
        policy_name="Public",
        access_level="Public",
        sensitivity="public",
        description="Primitive system policy. Public knowledge can be consumed only through channels that allow Public.",
        primitive=True,
    )

    # Example user-defined policies. These are not primitive.
    internal_policy = ensure_access_policy(
        policy_name="Internal",
        access_level="Internal",
        sensitivity="internal",
        description="Example user-defined policy for internal knowledge.",
    )

    restricted_policy = ensure_access_policy(
        policy_name="Restricted",
        access_level="Role Restricted",
        sensitivity="confidential",
        description="Example user-defined policy for restricted knowledge.",
    )

    public_access = ensure_access_category(
        category_name="Public Access",
        title="Public Access",
        policies=[public_policy],
        description="Allows Public knowledge only.",
        priority=10,
    )

    internal_access = ensure_access_category(
        category_name="Internal Access",
        title="Internal Access",
        policies=[public_policy, internal_policy],
        description="Allows Public and Internal knowledge.",
        priority=20,
    )

    restricted_access = ensure_access_category(
        category_name="Restricted Access",
        title="Restricted Access",
        policies=[public_policy, internal_policy, restricted_policy],
        description="Allows Public, Internal, and Restricted knowledge.",
        priority=30,
    )

    # Role mappings.
    ensure_role_access_category(
        role="Guest",
        access_category=public_access,
        description="Guest users can access Public knowledge only.",
    )

    ensure_role_access_category(
        role="Website User",
        access_category=public_access,
        description="Website users can access Public knowledge only by default.",
    )

    ensure_role_access_category(
        role="Employee",
        access_category=internal_access,
        description="Employees can access Public and Internal knowledge.",
    )

    ensure_role_access_category(
        role="System Manager",
        access_category=restricted_access,
        description="System Managers can access Public, Internal, and Restricted knowledge.",
    )

    # Channels.
    website_qa = ensure_channel(
        channel_name="Website Q&A",
        channel_type="Q&A",
        description="Public website Q&A channel.",
    )

    website_chat = ensure_channel(
        channel_name="Website Chat",
        channel_type="Chat",
        description="Public website chat channel.",
    )

    internal_desk = ensure_channel(
        channel_name="Internal Desk",
        channel_type="Internal",
        description="Internal desk/agent-assist channel.",
    )

    studio_simulation = ensure_channel(
        channel_name="Studio Simulation",
        channel_type="Simulation",
        description="Nexus Studio internal simulation channel.",
    )

    public_api = ensure_channel(
        channel_name="Public API",
        channel_type="API",
        description="Public API channel.",
    )

    internal_api = ensure_channel(
        channel_name="Internal API",
        channel_type="API",
        description="Internal API channel.",
    )

    # Channel mappings.
    ensure_channel_access_category(
        channel=website_qa,
        access_category=public_access,
        description="Website Q&A can consume Public knowledge only.",
    )

    ensure_channel_access_category(
        channel=website_chat,
        access_category=public_access,
        description="Website Chat can consume Public knowledge only.",
    )

    ensure_channel_access_category(
        channel=public_api,
        access_category=public_access,
        description="Public API can consume Public knowledge only.",
    )

    ensure_channel_access_category(
        channel=internal_desk,
        access_category=internal_access,
        description="Internal Desk can consume Public and Internal knowledge.",
    )

    ensure_channel_access_category(
        channel=studio_simulation,
        access_category=restricted_access,
        description="Studio Simulation can consume Public, Internal, and Restricted knowledge.",
    )

    ensure_channel_access_category(
        channel=internal_api,
        access_category=restricted_access,
        description="Internal API can consume Public, Internal, and Restricted knowledge.",
    )

    frappe.db.commit()

    return {
        "success": True,
        "message": "Nexus access governance seed completed.",
        "policies": [public_policy, internal_policy, restricted_policy],
        "categories": [public_access, internal_access, restricted_access],
        "channels": [
            website_qa,
            website_chat,
            internal_desk,
            studio_simulation,
            public_api,
            internal_api,
        ],
    }