import json
import frappe


def parse_json_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def get_user_roles(user_context):
    roles = user_context.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    return set(roles)


def get_user_designation(user_context):
    return user_context.get("designation")


def can_access_policy(user_context, access_policy):
    if not access_policy:
        return False, "Missing access policy"

    policy = frappe.get_doc("Nexus Access Policy", access_policy)

    if policy.disabled:
        return False, "Access policy is disabled"

    user_roles = get_user_roles(user_context)
    user_designation = get_user_designation(user_context)

    allowed_roles = set(parse_json_list(policy.allowed_roles))
    excluded_roles = set(parse_json_list(policy.excluded_roles))

    allowed_designations = set(parse_json_list(policy.allowed_designations))
    excluded_designations = set(parse_json_list(policy.excluded_designations))

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
    return can_access_policy(user_context, chunk.access_policy)