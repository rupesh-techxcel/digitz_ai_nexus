import unittest

import frappe

from digitz_ai_nexus.services.tenant_context import (
    get_user_context,
    get_ecosystem_for_tenant,
    resolve_tenant_context,
    set_user_context,
)

from digitz_ai_nexus.api import nexus_administration as admin_api


TEST_USER = "nexus.context.test@example.com"

TENANT_A_NAME = "Nexus Unit Test Tenant A"
TENANT_A_CODE = "NEXUS-UNIT-TENANT-A"

TENANT_B_NAME = "Nexus Unit Test Tenant B"
TENANT_B_CODE = "NEXUS-UNIT-TENANT-B"

BUSINESS_UNIT_A = "Nexus Unit Test BU A"
BUSINESS_UNIT_B = "Nexus Unit Test BU B"
BUSINESS_UNIT_ECOSYSTEM = "Nexus Unit Test BU Ecosystem"
CHAT_CHANNEL = "NEXUS-UNIT-CHAT"
QA_CHANNEL = "NEXUS-UNIT-QA"


class TestNexusAdministrationContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_user = frappe.session.user

    @classmethod
    def tearDownClass(cls):
        frappe.set_user(cls.original_user or "Administrator")

    def setUp(self):
        frappe.set_user("Administrator")
        self.cleanup_test_records()
        self.ensure_test_user()

        frappe.set_user(TEST_USER)

        tenant_a_result = admin_api.create_tenant_onboarding(
            tenant_name=TENANT_A_NAME,
            tenant_code=TENANT_A_CODE,
            business_unit_name=BUSINESS_UNIT_A,
        )

        tenant_b_result = admin_api.create_tenant_onboarding(
            tenant_name=TENANT_B_NAME,
            tenant_code=TENANT_B_CODE,
            business_unit_name=BUSINESS_UNIT_B,
        )

        self.tenant_a = tenant_a_result.get("tenant")
        self.tenant_b = tenant_b_result.get("tenant")

        set_user_context(
            user=TEST_USER,
            tenant=self.tenant_a,
            business_unit=BUSINESS_UNIT_A,
            is_default=1,
        )

    def tearDown(self):
        frappe.set_user("Administrator")
        self.cleanup_test_records()
        frappe.set_user(self.original_user or "Administrator")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def ensure_test_user(self):
        if not frappe.db.exists("User", TEST_USER):
            user = frappe.new_doc("User")
            user.email = TEST_USER
            user.first_name = "Nexus Context"
            user.last_name = "Test"
            user.enabled = 1
            user.user_type = "System User"
            user.send_welcome_email = 0
            user.insert(ignore_permissions=True)
        else:
            user = frappe.get_doc("User", TEST_USER)
            user.enabled = 1
            user.user_type = "System User"
            user.save(ignore_permissions=True)

        user = frappe.get_doc("User", TEST_USER)

        if not frappe.db.exists(
            "Has Role",
            {
                "parent": TEST_USER,
                "role": "System Manager",
            },
        ):
            user.add_roles("System Manager")

        frappe.db.commit()

    def cleanup_test_records(self):
        tenant_names = self.get_test_tenant_names()

        if frappe.db.exists("DocType", "Nexus Live Channel"):
            for channel in [CHAT_CHANNEL, QA_CHANNEL]:
                self.delete_doc_safely("Nexus Live Channel", channel)

        if frappe.db.exists("DocType", "Nexus User Context"):
            filters = {
                "user": TEST_USER,
            }

            context_names = frappe.get_all(
                "Nexus User Context",
                filters=filters,
                pluck="name",
            )

            for name in context_names:
                self.delete_doc_safely("Nexus User Context", name)

            if tenant_names:
                context_names = frappe.get_all(
                    "Nexus User Context",
                    filters={
                        "active_tenant": ["in", tenant_names],
                    },
                    pluck="name",
                )

                for name in context_names:
                    self.delete_doc_safely("Nexus User Context", name)

        if frappe.db.exists("DocType", "Nexus Tenant Configuration") and tenant_names:
            ecosystem_names = frappe.get_all(
                "Nexus Tenant Configuration",
                filters={
                    "tenant": ["in", tenant_names],
                },
                pluck="name",
            )

            for name in ecosystem_names:
                self.delete_doc_safely("Nexus Tenant Configuration", name)

        if frappe.db.exists("DocType", "Nexus Tenant") and tenant_names:
            for name in tenant_names:
                self.delete_doc_safely("Nexus Tenant", name)

        frappe.db.commit()

    def get_test_tenant_names(self):
        if not frappe.db.exists("DocType", "Nexus Tenant"):
            return []

        names = set()

        for tenant_name in [TENANT_A_NAME, TENANT_B_NAME]:
            if frappe.db.exists("Nexus Tenant", tenant_name):
                names.add(tenant_name)

        for tenant_code in [TENANT_A_CODE, TENANT_B_CODE]:
            if frappe.db.exists("Nexus Tenant", tenant_code):
                names.add(tenant_code)

        if self.has_field("Nexus Tenant", "tenant_name"):
            rows = frappe.get_all(
                "Nexus Tenant",
                filters={
                    "tenant_name": ["in", [TENANT_A_NAME, TENANT_B_NAME]],
                },
                pluck="name",
            )
            names.update(rows)

        if self.has_field("Nexus Tenant", "tenant_code"):
            rows = frappe.get_all(
                "Nexus Tenant",
                filters={
                    "tenant_code": ["in", [TENANT_A_CODE, TENANT_B_CODE]],
                },
                pluck="name",
            )
            names.update(rows)

        return list(names)

    def delete_doc_safely(self, doctype, name):
        try:
            if frappe.db.exists(doctype, name):
                frappe.delete_doc(
                    doctype,
                    name,
                    force=True,
                    ignore_permissions=True,
                )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Nexus Test Cleanup Failed: {doctype} {name}",
            )

    def has_field(self, doctype, fieldname):
        if not frappe.db.exists("DocType", doctype):
            return False

        return fieldname in {
            field.fieldname
            for field in frappe.get_meta(doctype).fields
        }

    def ensure_live_channel(self, channel_code, channel_type):
        if not frappe.db.exists("DocType", "Nexus Live Channel"):
            self.skipTest("Nexus Live Channel DocType is not installed.")

        if frappe.db.exists("Nexus Live Channel", channel_code):
            return

        channel = frappe.new_doc("Nexus Live Channel")
        channel.channel_code = channel_code
        channel.channel_name = channel_code
        channel.channel_type = channel_type
        channel.enabled = 1
        channel.insert(ignore_permissions=True)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------

    def test_create_tenant_onboarding_creates_user_context_and_ecosystem(self):
        user_context = get_user_context(TEST_USER)
        ecosystem = get_ecosystem_for_tenant(self.tenant_a)

        self.assertIsNotNone(user_context)
        self.assertIsNotNone(ecosystem)

        self.assertEqual(user_context.user, TEST_USER)
        self.assertEqual(user_context.active_tenant, self.tenant_a)
        self.assertEqual(user_context.active_business_unit, BUSINESS_UNIT_A)

        self.assertEqual(ecosystem.tenant, self.tenant_a)
        self.assertEqual(ecosystem.default_business_unit, BUSINESS_UNIT_A)

    def test_set_user_context_updates_existing_context_for_same_tenant(self):
        existing_context = get_user_context(TEST_USER)

        updated = set_user_context(
            user=TEST_USER,
            tenant=self.tenant_a,
            business_unit="Nexus Updated BU",
            channel=None,
            is_default=1,
        )

        self.assertEqual(existing_context.name, updated.name)
        self.assertEqual(updated.active_business_unit, "Nexus Updated BU")

    def test_only_one_default_context_per_user(self):
        context_a = set_user_context(
            user=TEST_USER,
            tenant=self.tenant_a,
            business_unit=BUSINESS_UNIT_A,
            is_default=1,
        )

        context_b = set_user_context(
            user=TEST_USER,
            tenant=self.tenant_b,
            business_unit=BUSINESS_UNIT_B,
            is_default=1,
        )

        context_a.reload()
        context_b.reload()

        self.assertEqual(context_a.is_default, 0)
        self.assertEqual(context_b.is_default, 1)

    def test_resolve_explicit_payload_overrides_user_context(self):
        resolved = resolve_tenant_context(
            payload={
                "tenant": self.tenant_b,
                "business_unit": BUSINESS_UNIT_B,
            },
            user=TEST_USER,
            require_tenant=True,
        )

        self.assertEqual(resolved.tenant, self.tenant_b)
        self.assertEqual(resolved.business_unit, BUSINESS_UNIT_B)

    def test_resolve_user_context_when_payload_has_no_tenant(self):
        resolved = resolve_tenant_context(
            payload={},
            user=TEST_USER,
            require_tenant=True,
        )

        self.assertEqual(resolved.tenant, self.tenant_a)
        self.assertEqual(resolved.business_unit, BUSINESS_UNIT_A)

    def test_resolve_ecosystem_defaults_when_user_context_has_blank_values(self):
        admin_api.save_ecosystem_configuration({
            "tenant": self.tenant_a,
            "default_business_unit": BUSINESS_UNIT_ECOSYSTEM,
            "default_top_k": 7,
        })

        set_user_context(
            user=TEST_USER,
            tenant=self.tenant_a,
            business_unit=None,
            project=None,
            channel=None,
            is_default=1,
        )

        resolved = resolve_tenant_context(
            payload={},
            user=TEST_USER,
            require_tenant=True,
        )

        self.assertEqual(resolved.tenant, self.tenant_a)
        self.assertEqual(resolved.business_unit, BUSINESS_UNIT_ECOSYSTEM)
        self.assertEqual(int(resolved.default_top_k), 7)

    def test_resolve_channel_defaults_by_runtime_purpose(self):
        self.ensure_live_channel(CHAT_CHANNEL, "Website Chat")
        self.ensure_live_channel(QA_CHANNEL, "Website Q&A")

        admin_api.save_ecosystem_configuration({
            "tenant": self.tenant_a,
            "default_chat_channel": CHAT_CHANNEL,
            "default_qa_channel": QA_CHANNEL,
        })

        set_user_context(
            user=TEST_USER,
            tenant=self.tenant_a,
            business_unit=None,
            project=None,
            channel=None,
            is_default=1,
        )

        chat_context = resolve_tenant_context(
            payload={
                "conversation_type": "Chat",
            },
            user=TEST_USER,
            require_tenant=True,
        )
        qa_context = resolve_tenant_context(
            payload={
                "conversation_type": "Q&A",
            },
            user=TEST_USER,
            require_tenant=True,
        )
        generic_context = resolve_tenant_context(
            payload={},
            user=TEST_USER,
            require_tenant=True,
        )

        self.assertEqual(chat_context.channel, CHAT_CHANNEL)
        self.assertEqual(qa_context.channel, QA_CHANNEL)
        self.assertIsNone(generic_context.channel)

    def test_save_ecosystem_configuration_updates_values(self):
        result = admin_api.save_ecosystem_configuration({
            "tenant": self.tenant_a,
            "default_business_unit": BUSINESS_UNIT_ECOSYSTEM,
            "qa_enabled": 1,
            "live_chat_enabled": 1,
            "website_widget_enabled": 1,
            "activation_status": "Configured",
        })

        self.assertEqual(result.get("status"), "success")

        ecosystem = get_ecosystem_for_tenant(self.tenant_a)

        self.assertEqual(ecosystem.default_business_unit, BUSINESS_UNIT_ECOSYSTEM)
        self.assertEqual(ecosystem.qa_enabled, 1)
        self.assertEqual(ecosystem.live_chat_enabled, 1)
        self.assertEqual(ecosystem.website_widget_enabled, 1)
        self.assertEqual(ecosystem.activation_status, "Configured")

    def test_administration_snapshot_with_tenant_configuration(self):
        snapshot = admin_api.get_administration_snapshot(tenant=self.tenant_a)

        self.assertIn("tenant", snapshot)
        self.assertIn("tenant_configuration", snapshot)
        self.assertIn("user_context", snapshot)
        self.assertIn("resolved_context", snapshot)
        self.assertIn("ecosystem", snapshot)
        self.assertIn("selectors", snapshot)
        self.assertIn("readiness", snapshot)

        self.assertIsNone(snapshot.get("user_context"))
        self.assertEqual(snapshot["tenant"]["name"], self.tenant_a)
        self.assertIsNotNone(snapshot.get("tenant_configuration"))
        self.assertEqual(snapshot["resolved_context"]["tenant"], self.tenant_a)

    def test_selector_options_do_not_require_business_unit_doctype(self):
        options = admin_api.get_selector_options()

        self.assertIn("tenants", options)
        self.assertIn("business_units", options)
        self.assertIn("projects", options)
        self.assertIn("channels", options)

        business_units = {
            row.get("name")
            for row in options.get("business_units") or []
        }

        self.assertIn(BUSINESS_UNIT_A, business_units)

    def test_count_records_safely_does_not_assume_disabled_field(self):
        count = admin_api.count_records_safely(
            doctype="Nexus Knowledge Unit",
            tenant=self.tenant_a,
        )

        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)

    def test_readiness_summary_is_safe_and_structured(self):
        readiness = admin_api.get_readiness_summary(self.tenant_a)

        self.assertIn("tenant", readiness)
        self.assertIn("knowledge_count", readiness)
        self.assertIn("chunk_count", readiness)
        self.assertIn("channel_count", readiness)
        self.assertIn("ai_agent_count", readiness)
        self.assertIn("qa_ready", readiness)
        self.assertIn("live_ready", readiness)
        self.assertIn("testing_ready", readiness)
        self.assertIn("production_ready", readiness)

        self.assertEqual(readiness["tenant"], self.tenant_a)
        self.assertIsInstance(readiness["knowledge_count"], int)
        self.assertIsInstance(readiness["chunk_count"], int)
        self.assertIsInstance(readiness["channel_count"], int)
        self.assertIsInstance(readiness["ai_agent_count"], int)


if __name__ == "__main__":
    unittest.main()
