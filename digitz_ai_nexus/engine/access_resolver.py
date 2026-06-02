import frappe


def resolve_channel_policy_names(channel_name):
    """Get access policy names allowed by a channel via Channel Access Category."""
    if not channel_name:
        return set()

    category_names = frappe.get_all(
        "Nexus Channel Access Category",
        filters={"channel": channel_name, "disabled": 0},
        pluck="access_category",
    )

    if not category_names:
        return set()

    return _policies_from_categories(category_names)


def resolve_role_policy_names(user_roles):
    """Get access policy names allowed by a user's roles via Role Access Category."""
    if not user_roles:
        return set()

    category_names = frappe.get_all(
        "Nexus Role Access Category",
        filters={"role": ["in", list(user_roles)], "disabled": 0},
        pluck="access_category",
    )

    if not category_names:
        return set()

    return _policies_from_categories(category_names)


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
        Returns ["Public"] only — no other policies permitted.

    Authenticated endpoints:
        Returns intersection of all non-empty configured scopes:
        channel scope ∩ role scope ∩ profile scope (when configured)

    Fails closed: if all scopes are empty or intersection is empty, returns [].
    Callers must check for empty result and deny retrieval.

    Expansion point: when Nexus AI Agent Profile Access Category DocType is added,
    resolve profile policies and include them in the intersection via
    query_contract["profile_policy_names"].
    """
    force_public_only = bool(
        query_contract.get("force_public_only") or query_contract.get("is_public")
    )

    if force_public_only:
        return {
            "allowed_access_policies": ["Public"],
            "force_public_only": True,
            "channel_policy_names": ["Public"],
            "role_policy_names": [],
            "profile_policy_names": [],
        }

    channel_name = query_contract.get("channel")
    user_context = query_contract.get("user") or {}
    user_roles = set(user_context.get("roles") or [])

    channel_policies = resolve_channel_policy_names(channel_name)
    role_policies = resolve_role_policy_names(user_roles)

    # Profile scope: resolved from Nexus AI Agent Profile Access Category.
    # Callers may also pass pre-resolved profile_policy_names directly.
    ai_profile_name = (query_contract.get("ai_profile") or {}).get("name")
    if ai_profile_name:
        profile_policies = resolve_profile_policy_names(ai_profile_name)
    else:
        profile_policies = set(query_contract.get("profile_policy_names") or [])

    # Only intersect scopes that have explicit configuration.
    # An unconfigured scope is treated as "no restriction from this scope",
    # not "deny all", so new deployments work before all categories are set up.
    non_empty_scopes = [s for s in [channel_policies, role_policies, profile_policies] if s]

    if not non_empty_scopes:
        return {
            "allowed_access_policies": [],
            "force_public_only": False,
            "channel_policy_names": list(channel_policies),
            "role_policy_names": list(role_policies),
            "profile_policy_names": list(profile_policies),
        }

    final = non_empty_scopes[0].copy()
    for scope in non_empty_scopes[1:]:
        final = final.intersection(scope)

    return {
        "allowed_access_policies": list(final),
        "force_public_only": False,
        "channel_policy_names": list(channel_policies),
        "role_policy_names": list(role_policies),
        "profile_policy_names": list(profile_policies),
    }
