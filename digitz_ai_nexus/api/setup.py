import frappe

DEFAULT_ACCESS_POLICIES = [
    {
        "policy_name": "PUBLIC",
        "access_level": "Public",
        "sensitivity": "public",
        "allowed_roles": "[]",
        "excluded_roles": "[]",
        "description": "Public knowledge available for general users and website Q&A.",
    },
    {
        "policy_name": "CUSTOMER_RESTRICTED",
        "access_level": "Customer Restricted",
        "sensitivity": "customer",
        "allowed_roles": "[\"Customer\", \"Support Agent\", \"System Manager\"]",
        "excluded_roles": "[]",
        "description": "Knowledge available only for registered customers and support users.",
    },
    {
        "policy_name": "INTERNAL_EMPLOYEE",
        "access_level": "Internal",
        "sensitivity": "internal",
        "allowed_roles": "[\"Employee\", \"System Manager\"]",
        "excluded_roles": "[]",
        "description": "Internal employee knowledge.",
    },
    {
        "policy_name": "ROLE_RESTRICTED",
        "access_level": "Role Restricted",
        "sensitivity": "operational",
        "allowed_roles": "[]",
        "excluded_roles": "[]",
        "description": "Generic restricted policy. Configure allowed roles per case.",
    },
    {
        "policy_name": "FINANCE_RESTRICTED",
        "access_level": "Finance Restricted",
        "sensitivity": "financial",
        "allowed_roles": "[\"Accounts User\", \"Accounts Manager\", \"Finance Manager\", \"System Manager\"]",
        "excluded_roles": "[\"Sales User\", \"Customer\"]",
        "description": "Financial, taxation, valuation, pricing, and margin-related knowledge.",
    },
    {
        "policy_name": "HR_CONFIDENTIAL",
        "access_level": "HR Confidential",
        "sensitivity": "hr",
        "allowed_roles": "[\"HR User\", \"HR Manager\", \"System Manager\"]",
        "excluded_roles": "[\"Customer\"]",
        "description": "HR, employee, salary, onboarding, and confidential workforce knowledge.",
    },
    {
        "policy_name": "ADMIN_ONLY",
        "access_level": "Admin Only",
        "sensitivity": "confidential",
        "allowed_roles": "[\"System Manager\"]",
        "excluded_roles": "[]",
        "description": "Highly restricted administrative knowledge.",
    },
]


@frappe.whitelist()
def create_default_access_policies():
    created = []
    updated = []

    for row in DEFAULT_ACCESS_POLICIES:
        if frappe.db.exists("Nexus Access Policy", row["policy_name"]):
            doc = frappe.get_doc("Nexus Access Policy", row["policy_name"])
            for key, value in row.items():
                doc.set(key, value)
            doc.disabled = 0
            doc.save(ignore_permissions=True)
            updated.append(row["policy_name"])
        else:
            doc = frappe.new_doc("Nexus Access Policy")
            doc.update(row)
            doc.disabled = 0
            doc.insert(ignore_permissions=True)
            created.append(row["policy_name"])

    frappe.db.commit()

    return {
        "created": created,
        "updated": updated,
    }