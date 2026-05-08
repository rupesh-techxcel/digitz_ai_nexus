import json
import frappe


def parse_json_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return []

        try:
            parsed = json.loads(value)

            if isinstance(parsed, list):
                return parsed

            if isinstance(parsed, str):
                return [parsed]

            return []
        except Exception:
            return [
                item.strip()
                for item in value.replace("\n", ",").split(",")
                if item.strip()
            ]

    return []


def get_user_roles(user_context):
    roles = user_context.get("roles") or []

    if isinstance(roles, str):
        roles = [role.strip() for role in roles.split(",") if role.strip()]

    return set(roles)


def get_user_designation(user_context):
    return user_context.get("designation")


def get_chunk_value(chunk, fieldname):
    if isinstance(chunk, dict):
        return chunk.get(fieldname)

    return getattr(chunk, fieldname, None)


def normalize_policy_name(value):
    return (value or "").strip().lower().replace("-", "_").replace(" ", "_")


def can_access_policy(user_context, access_policy):
    if not access_policy:
        return False, "Missing access policy"

    normalized_policy = normalize_policy_name(access_policy)

    if normalized_policy == "public":
        return True, "Allowed"

    user_roles = get_user_roles(user_context)
    user_designation = get_user_designation(user_context)

    # Built-in restricted means: deny unless explicit role/designation rules exist
    if normalized_policy == "restricted":
        return False, "Restricted"

    # Built-in role_based without chunk-level roles must fall through to policy doc
    try:
        policy = frappe.get_doc("Nexus Access Policy", access_policy)
    except Exception:
        if normalized_policy == "role_based":
            return False, "Role not allowed"

        return False, "Access policy not found"

    if getattr(policy, "disabled", 0):
        return False, "Access policy is disabled"

    allowed_roles = set(parse_json_list(getattr(policy, "allowed_roles", None)))
    excluded_roles = set(parse_json_list(getattr(policy, "excluded_roles", None)))

    allowed_designations = set(parse_json_list(getattr(policy, "allowed_designations", None)))
    excluded_designations = set(parse_json_list(getattr(policy, "excluded_designations", None)))

    # Deny > Allow
    if user_roles.intersection(excluded_roles):
        return False, "Denied by excluded role"

    if user_designation and user_designation in excluded_designations:
        return False, "Denied by excluded designation"

    if allowed_roles and not user_roles.intersection(allowed_roles):
        return False, "Role not allowed"

    if allowed_designations and user_designation not in allowed_designations:
        return False, "Designation not allowed"

    return True, "Allowed"


def can_access_chunk(user_context, chunk):
    access_policy = get_chunk_value(chunk, "access_policy")
    normalized_policy = normalize_policy_name(access_policy)

    user_roles = get_user_roles(user_context)

    chunk_allowed_roles = set()

    for fieldname in ["allowed_roles", "roles", "user_roles"]:
        chunk_allowed_roles.update(
            parse_json_list(get_chunk_value(chunk, fieldname))
        )

    chunk_denied_roles = set()

    for fieldname in ["denied_roles", "excluded_roles", "deny_roles"]:
        chunk_denied_roles.update(
            parse_json_list(get_chunk_value(chunk, fieldname))
        )

    frappe.log_error(
        json.dumps({
            "chunk": get_chunk_value(chunk, "name"),
            "access_policy": access_policy,
            "normalized_policy": normalized_policy,
            "user_roles": list(user_roles),
            "allowed_roles_raw": get_chunk_value(chunk, "allowed_roles"),
            "denied_roles_raw": get_chunk_value(chunk, "denied_roles"),
            "excluded_roles_raw": get_chunk_value(chunk, "excluded_roles"),
            "deny_roles_raw": get_chunk_value(chunk, "deny_roles"),
            "chunk_allowed_roles": list(chunk_allowed_roles),
            "chunk_denied_roles": list(chunk_denied_roles),
            "deny_intersection": list(user_roles.intersection(chunk_denied_roles)),
            "allow_intersection": list(user_roles.intersection(chunk_allowed_roles)),
        }, indent=2),
        "Nexus Deny Debug"
    )

    # Deny > Allow at chunk level
    if user_roles.intersection(chunk_denied_roles):
        return False, "Denied by chunk role"

    if normalized_policy == "public":
        return True, "Allowed"

    if normalized_policy == "restricted":
        return can_access_policy(user_context, access_policy)

    if normalized_policy == "role_based":
        if chunk_allowed_roles:
            if user_roles.intersection(chunk_allowed_roles):
                return True, "Allowed"

            return False, "Role not allowed"

        return can_access_policy(user_context, access_policy)

    return can_access_policy(user_context, access_policy)