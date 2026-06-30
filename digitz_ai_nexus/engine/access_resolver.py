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
    Get access policy names via a single Knowledge Profile.
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
            "disabled": 0,
        },
        pluck="access_category",
    )

    return _policies_from_categories(category_names)


def resolve_knowledge_profiles_policy_names(knowledge_profile_names):
    """
    Get the union of access policy names across multiple Knowledge Profiles.
    Used when a person holds multiple Identity Profile mappings for the same identity type.
    """
    if not knowledge_profile_names:
        return set()

    all_policies = set()
    for kp_name in knowledge_profile_names:
        all_policies.update(resolve_knowledge_profile_policy_names(kp_name))

    return all_policies


def resolve_all_policy_names():
    """Get all enabled access policy names."""
    if not frappe.db.exists("DocType", "Nexus Access Policy"):
        return set()

    return set(
        frappe.get_all(
            "Nexus Access Policy",
            filters={"disabled": 0},
            pluck="name",
        )
    )


def resolve_identity_policy_cap(identity_type, tenant=None):
    """Return the hard policy cap imposed by identity type, if any."""
    if identity_type == "Public":
        return set(resolve_primitive_public_policies(tenant=tenant))
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


def resolve_primitive_public_policies(tenant=None):
    """
    Return all Access Policy document names that are marked is_primitive=1.

    Each tenant has its own primitive Public policy (e.g. "Public-NEXUS-AI").
    Knowledge sources store the document name as their access_policy, so the
    retrieval filter must include the tenant-specific name, not just "Public".
    The bare "Public" name is included for backward compatibility with any
    knowledge sources that were created before tenant-specific policies existed.
    """
    filters = {"is_primitive": 1, "disabled": 0}
    if tenant:
        filters["tenant"] = tenant

    names = frappe.get_all("Nexus Access Policy", filters=filters, pluck="name")
    return list(set(names) | {"Public"})


def resolve_allowed_policies(query_contract):
    """
    Calculate final allowed access policy names for retrieval.

    Public endpoints (force_public_only=True or is_public=True):
        When the route has a public_knowledge_profile configured (ai_profile carries
        knowledge_profile_names), returns the intersection of primitive Public policies
        and the profile's policies — scoping retrieval to only the public knowledge the
        admin assigned to this route. Falls back to all primitive Public policies when no
        profile is configured or the intersection is empty.

    System Manager session:
        Returns all enabled policies — unrestricted.

    Registered visitor / desk user with knowledge_profile_names:
        Resolves via: knowledge_profile_names → union of policies
        Capped by: identity_safeguard_access_categories (from Identity Type).

    Legacy AI profile path (no knowledge_profile_names):
        Falls back to Nexus AI Agent Profile access category records.

    Fails closed: empty policy set → returns [] → retrieval denied.
    """
    ai_profile = query_contract.get("ai_profile") or {}
    force_public_only = bool(
        query_contract.get("force_public_only") or query_contract.get("is_public")
    )

    if force_public_only:
        tenant = query_contract.get("tenant") or ai_profile.get("tenant")
        public_policies = set(resolve_primitive_public_policies(tenant=tenant))

        # When the route has a specific public_knowledge_profile configured, scope
        # retrieval strictly to the public policies inside that profile. The intersection
        # with primitive_public_policies is an unconditional safety ceiling — a
        # misconfigured profile containing non-public policies cannot leak through.
        # No fallback: an empty intersection means no public knowledge from this profile
        # is accessible, which is intentional (fail-closed, not fail-open).
        kp_names = ai_profile.get("knowledge_profile_names") or []
        if kp_names:
            profile_policies = resolve_knowledge_profiles_policy_names(kp_names)
            public_policies = public_policies.intersection(profile_policies)
            cap_label = "force_public_only+profile_scoped"
        else:
            cap_label = "force_public_only"

        public_policies = list(public_policies)
        return {
            "allowed_access_policies": public_policies,
            "force_public_only": True,
            "profile_policy_names": public_policies,
            "safeguard_policy_names": [],
            "identity_policy_names": public_policies,
            "access_cap_applied": cap_label,
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

    identity_type = query_contract.get("identity_type") or ai_profile.get("identity_type")
    safeguard_access_categories = query_contract.get("identity_safeguard_access_categories")
    if safeguard_access_categories is None:
        safeguard_access_categories = ai_profile.get("identity_safeguard_access_categories")

    # ── New path: knowledge_profile_names from Identity Profile resolution ─────
    knowledge_profile_names = (
        ai_profile.get("knowledge_profile_names")
        or query_contract.get("knowledge_profile_names")
        or []
    )

    # Single knowledge_profile_name (desk user legacy / backward compat)
    if not knowledge_profile_names:
        single_kp = ai_profile.get("knowledge_profile_name") or ""
        if single_kp:
            knowledge_profile_names = [single_kp]

    tenant = query_contract.get("tenant") or ai_profile.get("tenant")

    if knowledge_profile_names:
        profile_policies = resolve_knowledge_profiles_policy_names(knowledge_profile_names)
        # Profile defines the full access scope. Public knowledge sources are accessible only
        # when the profile explicitly includes a public Access Category — no automatic global
        # public union. The identity-type cap below still applies on top of this scope.
        safeguard_policies = resolve_access_categories_policy_names(safeguard_access_categories)
        identity_policies = resolve_identity_policy_cap(identity_type, tenant=tenant)
        effective_cap = _intersect_caps(safeguard_policies, identity_policies)
        allowed_policies = profile_policies
        if effective_cap is not None:
            allowed_policies = profile_policies.intersection(effective_cap)

        access_cap_parts = []
        if safeguard_policies is not None:
            access_cap_parts.append("identity_safeguard")
        if identity_policies is not None:
            access_cap_parts.append("identity_type")

        return {
            "allowed_access_policies": list(allowed_policies),
            "force_public_only": False,
            "profile_policy_names": list(profile_policies),
            "safeguard_policy_names": list(safeguard_policies or []),
            "identity_policy_names": list(identity_policies or []),
            "access_cap_applied": "+".join(access_cap_parts) or "profile_only",
        }

    # No knowledge profiles resolved.
    # For Public identity, the cap itself is primitive public policies — allow minimal access.
    # For all other identity types, fail closed (no profiles = no access).
    identity_type = query_contract.get("identity_type") or ai_profile.get("identity_type")
    identity_cap = resolve_identity_policy_cap(identity_type, tenant=tenant)
    if identity_cap:
        return {
            "allowed_access_policies": list(identity_cap),
            "force_public_only": False,
            "profile_policy_names": [],
            "safeguard_policy_names": [],
            "identity_policy_names": list(identity_cap),
            "access_cap_applied": "identity_type_cap_only",
        }

    return {
        "allowed_access_policies": [],
        "force_public_only": False,
        "profile_policy_names": [],
        "safeguard_policy_names": [],
        "identity_policy_names": [],
        "access_cap_applied": "no_profile",
    }
