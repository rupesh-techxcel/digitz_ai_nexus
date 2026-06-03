import frappe


def resolve_profile_policy_names(ai_agent_profile_name):
    """Get access policy names for a profile via Nexus AI Agent Profile Access Category."""
    if not ai_agent_profile_name:
        return set()

    category_names = frappe.get_all(
        "Nexus AI Agent Profile Access Category",
        filters={"ai_agent_profile": ai_agent_profile_name, "enabled": 1},
        pluck="access_category",
    )

    if not category_names:
        return set()

    return _policies_from_categories(category_names)


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


def resolve_allowed_policies(query_contract):
    """
    Calculate final allowed access policy names for retrieval.

    Public endpoints (force_public_only=True or is_public=True):
        Returns ["Public"] only. Cannot be overridden.

    All other requests:
        Profile is the single access authority.
        Resolves via: ai_profile.name → Nexus AI Agent Profile Access Category
                      → Nexus Access Category → Nexus Access Policy names

    Fails closed: no profile or empty policy set → returns [] → retrieval denied.
    """
    force_public_only = bool(
        query_contract.get("force_public_only") or query_contract.get("is_public")
    )

    if force_public_only:
        return {
            "allowed_access_policies": ["Public"],
            "force_public_only": True,
            "profile_policy_names": [],
        }

    ai_profile_name = (query_contract.get("ai_profile") or {}).get("name")

    if not ai_profile_name:
        return {
            "allowed_access_policies": [],
            "force_public_only": False,
            "profile_policy_names": [],
        }

    profile_policies = resolve_profile_policy_names(ai_profile_name)

    return {
        "allowed_access_policies": list(profile_policies),
        "force_public_only": False,
        "profile_policy_names": list(profile_policies),
    }


# ---------------------------------------------------------------------------
# Retained for reference and admin reporting — NOT called in runtime path
# ---------------------------------------------------------------------------

def resolve_channel_policy_names(channel_name):
    """Retained for admin reporting only. Not used in runtime access resolution."""
    if not channel_name:
        return set()

    category_names = frappe.get_all(
        "Nexus Channel Access Category",
        filters={"channel": channel_name, "disabled": 0},
        pluck="access_category",
    )

    return _policies_from_categories(category_names) if category_names else set()


def resolve_role_policy_names(user_roles):
    """Retained for admin reporting only. Not used in runtime access resolution."""
    if not user_roles:
        return set()

    category_names = frappe.get_all(
        "Nexus Role Access Category",
        filters={"role": ["in", list(user_roles)], "disabled": 0},
        pluck="access_category",
    )

    return _policies_from_categories(category_names) if category_names else set()
