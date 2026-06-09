import frappe


def _policies_from_categories(category_names):
    """Get Access Policy names from a list of Nexus Access Category names."""
    if not category_names:
        return set()

    policy_names = frappe.get_all(
        "Nexus Access Category Policy",
        filters={
            "parent": ["in", list(category_names)],
            "parentfield": "allowed_policies",
        },
        pluck="access_policy",
    )

    return set(policy_names)


def resolve_access_category_policy_names(access_category):
    """Get access policy names for one Nexus Access Category."""
    if not access_category:
        return set()

    return _policies_from_categories([access_category])


def resolve_access_categories_policy_names(access_categories):
    """Get access policy names for one or more Nexus Access Categories."""
    if access_categories is None:
        return None

    return _policies_from_categories(access_categories)


def resolve_knowledge_profile_policy_names(knowledge_profile_name):
    """
    Get access policy names via a Knowledge Profile.
    Knowledge Profile → Knowledge Profile Access Category (child) → Nexus Access Category → policies.
    """
    if not knowledge_profile_name:
        return set()

    if not frappe.db.exists("Knowledge Profile", knowledge_profile_name):
        return set()

    category_names = frappe.get_all(
        "Knowledge Profile Access Category",
        filters={
            "parent": knowledge_profile_name,
            "parentfield": "access_categories",
            "enabled": 1,
        },
        pluck="access_category",
    )

    return _policies_from_categories(category_names)


def resolve_profile_policy_names(ai_agent_profile_name):
    """
    Get access policy names for an AI Agent Profile.

    Resolution order:
    1. If the profile has a knowledge_profile set → use Knowledge Profile.
    2. Fall back to legacy Nexus AI Agent Profile Access Category records.
    """
    if not ai_agent_profile_name:
        return set()

    knowledge_profile = frappe.db.get_value(
        "Nexus AI Agent Profile", ai_agent_profile_name, "knowledge_profile"
    )

    if knowledge_profile:
        return resolve_knowledge_profile_policy_names(knowledge_profile)

    # Legacy path: Nexus AI Agent Profile Access Category
    category_names = frappe.get_all(
        "Nexus AI Agent Profile Access Category",
        filters={"ai_agent_profile": ai_agent_profile_name, "enabled": 1},
        pluck="access_category",
    )

    return _policies_from_categories(category_names)


def resolve_all_policy_names():
    """Get all enabled access policy names."""
    if not frappe.db.exists("DocType", "Nexus Access Policy"):
        return set()

    policy_names = frappe.get_all(
        "Nexus Access Policy",
        filters={"disabled": 0},
        pluck="name",
    )

    return set(policy_names)


def resolve_identity_policy_cap(identity_type):
    """Return the hard policy cap imposed by identity, if any."""
    if identity_type == "Public":
        return {"Public"}

    return None


def is_system_manager_session_user():
    """Return True only for the authenticated session user, never payload roles."""
    session_user = getattr(frappe.session, "user", None)
    if not session_user or session_user == "Guest":
        return False

    return "System Manager" in frappe.get_roles(session_user)


def _intersect_caps(*caps):
    active_caps = [set(cap) for cap in caps if cap is not None]

    if not active_caps:
        return None

    effective = active_caps[0]
    for cap in active_caps[1:]:
        effective = effective.intersection(cap)

    return effective


def resolve_allowed_policies(query_contract):
    """
    Calculate final allowed access policy names for retrieval.

    Public endpoints (force_public_only=True or is_public=True):
        Returns ["Public"] only. Cannot be overridden.

    System Manager session:
        Returns all enabled policies — unrestricted.

    Desk user with knowledge_profile (no AI profile):
        Resolves via: knowledge_profile → Knowledge Profile Access Category → policies.

    AI profile with knowledge_profile:
        Resolves via: AI profile → knowledge_profile → Knowledge Profile Access Category → policies.

    AI profile without knowledge_profile (legacy):
        Resolves via: AI profile → Nexus AI Agent Profile Access Category → policies.

    Fails closed: no profile/knowledge_profile or empty policy set → returns [] → retrieval denied.
    """
    ai_profile = query_contract.get("ai_profile") or {}
    force_public_only = bool(
        query_contract.get("force_public_only") or query_contract.get("is_public")
    )

    if force_public_only:
        return {
            "allowed_access_policies": ["Public"],
            "force_public_only": True,
            "profile_policy_names": [],
            "safeguard_policy_names": [],
            "identity_policy_names": ["Public"],
            "access_cap_applied": "force_public_only",
        }

    if is_system_manager_session_user():
        all_policies = resolve_all_policy_names()
        return {
            "allowed_access_policies": list(all_policies),
            "force_public_only": False,
            "profile_policy_names": list(all_policies),
            "safeguard_policy_names": [],
            "identity_policy_names": [],
            "access_cap_applied": "system_manager",
        }

    # Desk user path: knowledge_profile without an AI profile
    knowledge_profile_name = ai_profile.get("knowledge_profile_name")
    if knowledge_profile_name and not ai_profile.get("name"):
        kp_policies = resolve_knowledge_profile_policy_names(knowledge_profile_name)
        return {
            "allowed_access_policies": list(kp_policies),
            "force_public_only": False,
            "profile_policy_names": list(kp_policies),
            "safeguard_policy_names": [],
            "identity_policy_names": [],
            "access_cap_applied": "knowledge_profile",
        }

    ai_profile_name = ai_profile.get("name")
    identity_type = query_contract.get("identity_type") or ai_profile.get("identity_type")
    safeguard_access_categories = query_contract.get("identity_safeguard_access_categories")
    if safeguard_access_categories is None:
        safeguard_access_categories = ai_profile.get("identity_safeguard_access_categories")

    if not ai_profile_name:
        return {
            "allowed_access_policies": [],
            "force_public_only": False,
            "profile_policy_names": [],
            "safeguard_policy_names": [],
            "identity_policy_names": [],
            "access_cap_applied": "no_profile",
        }

    profile_policies = resolve_profile_policy_names(ai_profile_name)
    safeguard_policies = resolve_access_categories_policy_names(safeguard_access_categories)
    identity_policies = resolve_identity_policy_cap(identity_type)
    effective_cap = _intersect_caps(safeguard_policies, identity_policies)
    allowed_policies = profile_policies

    if effective_cap is not None:
        allowed_policies = profile_policies.intersection(effective_cap)

    access_cap_applied = []
    if safeguard_policies is not None:
        access_cap_applied.append("identity_safeguard")
    if identity_policies is not None:
        access_cap_applied.append("identity_type")

    return {
        "allowed_access_policies": list(allowed_policies),
        "force_public_only": False,
        "profile_policy_names": list(profile_policies),
        "safeguard_policy_names": list(safeguard_policies or []),
        "identity_policy_names": list(identity_policies or []),
        "access_cap_applied": "+".join(access_cap_applied) or "profile_only",
    }
