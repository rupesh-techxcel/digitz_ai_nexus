import frappe
from frappe.tests.utils import FrappeTestCase

from digitz_ai_nexus.engine.access_resolver import resolve_allowed_policies


class TestNexusAccessResolver(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.ensure_policy("NEXUS-ACCESS-TEST-PUBLIC")
        self.ensure_policy("NEXUS-ACCESS-TEST-RESTRICTED")

    def ensure_policy(self, name):
        if frappe.db.exists("Nexus Access Policy", name):
            doc = frappe.get_doc("Nexus Access Policy", name)
        else:
            doc = frappe.new_doc("Nexus Access Policy")
            doc.policy_name = name

        doc.disabled = 0
        doc.save(ignore_permissions=True)

    def test_system_manager_session_gets_all_enabled_policies_without_profile(self):
        result = resolve_allowed_policies({
            "user": {"roles": ["System Manager"]},
            "ai_profile": {},
        })

        self.assertEqual(result["access_cap_applied"], "system_manager")
        self.assertIn("NEXUS-ACCESS-TEST-PUBLIC", result["allowed_access_policies"])
        self.assertIn("NEXUS-ACCESS-TEST-RESTRICTED", result["allowed_access_policies"])

    def test_force_public_only_still_overrides_system_manager(self):
        result = resolve_allowed_policies({
            "force_public_only": True,
            "user": {"roles": ["System Manager"]},
            "ai_profile": {},
        })

        self.assertEqual(result["access_cap_applied"], "force_public_only")
        self.assertEqual(result["allowed_access_policies"], ["Public"])
