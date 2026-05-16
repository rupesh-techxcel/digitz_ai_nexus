import frappe
from frappe.tests.utils import FrappeTestCase

from digitz_ai_nexus.api.nexus_administration import (
    save_ecosystem_configuration,
    set_active_user_context,
    get_administration_snapshot,
)


TEST_TENANT = "TEST-ADMIN-MULTI-ECO"
TEST_TENANT_NAME = "Test Administration Multi Ecosystem"
TEST_BU = "Administration Multi Ecosystem BU"

ECO_PROD_NAME = "TEST-ADMIN Production Ecosystem"
ECO_INTERNAL_NAME = "TEST-ADMIN Internal Platform Ecosystem"
ECO_SANDBOX_NAME = "TEST-ADMIN Sandbox Ecosystem"


class TestNexusAdministrationEcosystem(FrappeTestCase):
    def setUp(self):
        cleanup_test_records()
        ensure_test_tenant()

    def tearDown(self):
        cleanup_test_records()

    def test_same_tenant_can_have_multiple_ecosystems(self):
        prod = create_ecosystem(
            ecosystem_name=ECO_PROD_NAME,
            ecosystem_type="Production",
            is_default=1,
            default_public_context="Public Website",
            default_business_unit=TEST_BU,
        )

        internal = create_ecosystem(
            ecosystem_name=ECO_INTERNAL_NAME,
            ecosystem_type="Internal Platform",
            is_default=0,
            default_public_context="Internal Knowledge",
            default_business_unit=TEST_BU,
        )

        ecosystems = frappe.get_all(
            "Nexus Ecosystem",
            filters={"tenant": TEST_TENANT},
            fields=["name", "tenant", "ecosystem_name", "ecosystem_type", "is_default"],
            order_by="creation asc",
        )

        self.assertEqual(len(ecosystems), 2)

        ecosystem_names = {row.ecosystem_name for row in ecosystems}
        self.assertIn(ECO_PROD_NAME, ecosystem_names)
        self.assertIn(ECO_INTERNAL_NAME, ecosystem_names)

        self.assertEqual(frappe.db.get_value("Nexus Ecosystem", prod, "tenant"), TEST_TENANT)
        self.assertEqual(frappe.db.get_value("Nexus Ecosystem", internal, "tenant"), TEST_TENANT)

    def test_setting_new_tenant_default_unsets_previous_default(self):
        prod = create_ecosystem(
            ecosystem_name=ECO_PROD_NAME,
            ecosystem_type="Production",
            is_default=1,
            default_public_context="Public Website",
            default_business_unit=TEST_BU,
        )

        internal = create_ecosystem(
            ecosystem_name=ECO_INTERNAL_NAME,
            ecosystem_type="Internal Platform",
            is_default=1,
            default_public_context="Internal Knowledge",
            default_business_unit=TEST_BU,
        )

        prod_default = frappe.db.get_value("Nexus Ecosystem", prod, "is_default")
        internal_default = frappe.db.get_value("Nexus Ecosystem", internal, "is_default")

        self.assertEqual(int(prod_default or 0), 0)
        self.assertEqual(int(internal_default or 0), 1)

    def test_user_context_can_store_active_ecosystem(self):
        internal = create_ecosystem(
            ecosystem_name=ECO_INTERNAL_NAME,
            ecosystem_type="Internal Platform",
            is_default=1,
            default_public_context="Internal Knowledge",
            default_business_unit=TEST_BU,
        )

        result = set_active_user_context(
            tenant=TEST_TENANT,
            active_ecosystem=internal,
            business_unit=TEST_BU,
            project="Internal Admin Project",
            channel=None,
        )

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("tenant"), TEST_TENANT)
        self.assertEqual(result.get("ecosystem"), internal)

        context_name = result.get("context")
        self.assertTrue(context_name)

        context = frappe.get_doc("Nexus User Context", context_name)
        self.assertEqual(context.active_tenant, TEST_TENANT)
        self.assertEqual(context.active_ecosystem, internal)
        self.assertEqual(context.active_business_unit, TEST_BU)

    def test_snapshot_returns_ecosystems_list_and_selected_ecosystem(self):
        prod = create_ecosystem(
            ecosystem_name=ECO_PROD_NAME,
            ecosystem_type="Production",
            is_default=1,
            default_public_context="Public Website",
            default_business_unit=TEST_BU,
        )

        internal = create_ecosystem(
            ecosystem_name=ECO_INTERNAL_NAME,
            ecosystem_type="Internal Platform",
            is_default=0,
            default_public_context="Internal Knowledge",
            default_business_unit=TEST_BU,
        )

        set_active_user_context(
            tenant=TEST_TENANT,
            active_ecosystem=internal,
            business_unit=TEST_BU,
            project=None,
            channel=None,
        )

        snapshot = get_administration_snapshot()

        self.assertTrue(snapshot)
        self.assertIn("ecosystems", snapshot)
        self.assertIn("ecosystem", snapshot)
        self.assertIn("user_context", snapshot)
        self.assertIn("resolved_context", snapshot)

        ecosystems = snapshot.get("ecosystems") or []
        self.assertEqual(len(ecosystems), 2)

        ecosystem_docnames = {row.get("name") for row in ecosystems}
        self.assertIn(prod, ecosystem_docnames)
        self.assertIn(internal, ecosystem_docnames)

        self.assertEqual(snapshot["user_context"]["active_tenant"], TEST_TENANT)
        self.assertEqual(snapshot["user_context"]["active_ecosystem"], internal)
        self.assertEqual(snapshot["ecosystem"]["name"], internal)
        self.assertEqual(snapshot["ecosystem"]["ecosystem_type"], "Internal Platform")
        self.assertEqual(snapshot["resolved_context"]["ecosystem"], internal)

    def test_save_updates_selected_ecosystem_not_random_same_tenant_ecosystem(self):
        prod = create_ecosystem(
            ecosystem_name=ECO_PROD_NAME,
            ecosystem_type="Production",
            is_default=1,
            default_public_context="Public Website",
            default_business_unit=TEST_BU,
        )

        internal = create_ecosystem(
            ecosystem_name=ECO_INTERNAL_NAME,
            ecosystem_type="Internal Platform",
            is_default=0,
            default_public_context="Internal Knowledge",
            default_business_unit=TEST_BU,
        )

        save_ecosystem_configuration(
            {
                "name": internal,
                "tenant": TEST_TENANT,
                "ecosystem_name": ECO_INTERNAL_NAME,
                "ecosystem_type": "Internal Platform",
                "enabled": 1,
                "is_default": 0,
                "default_public_context": "Updated Internal Knowledge",
                "default_business_unit": TEST_BU,
                "default_top_k": 9,
            }
        )

        prod_context = frappe.db.get_value("Nexus Ecosystem", prod, "default_public_context")
        internal_context = frappe.db.get_value("Nexus Ecosystem", internal, "default_public_context")
        internal_top_k = frappe.db.get_value("Nexus Ecosystem", internal, "default_top_k")

        self.assertEqual(prod_context, "Public Website")
        self.assertEqual(internal_context, "Updated Internal Knowledge")
        self.assertEqual(int(internal_top_k or 0), 9)

    def test_switching_active_ecosystem_changes_only_user_context(self):
        prod = create_ecosystem(
            ecosystem_name=ECO_PROD_NAME,
            ecosystem_type="Production",
            is_default=1,
            default_public_context="Public Website",
            default_business_unit=TEST_BU,
        )

        internal = create_ecosystem(
            ecosystem_name=ECO_INTERNAL_NAME,
            ecosystem_type="Internal Platform",
            is_default=0,
            default_public_context="Internal Knowledge",
            default_business_unit=TEST_BU,
        )

        set_active_user_context(
            tenant=TEST_TENANT,
            active_ecosystem=internal,
            business_unit=TEST_BU,
            project=None,
            channel=None,
        )

        prod_default = frappe.db.get_value("Nexus Ecosystem", prod, "is_default")
        internal_default = frappe.db.get_value("Nexus Ecosystem", internal, "is_default")

        self.assertEqual(int(prod_default or 0), 1)
        self.assertEqual(int(internal_default or 0), 0)

        context_name = frappe.db.get_value(
            "Nexus User Context",
            {
                "user": frappe.session.user,
                "active_tenant": TEST_TENANT,
            },
            "name",
        )

        self.assertTrue(context_name)

        active_ecosystem = frappe.db.get_value(
            "Nexus User Context",
            context_name,
            "active_ecosystem",
        )

        self.assertEqual(active_ecosystem, internal)


def ensure_test_tenant():
    if frappe.db.exists("Nexus Tenant", TEST_TENANT):
        return frappe.get_doc("Nexus Tenant", TEST_TENANT)

    doc = frappe.new_doc("Nexus Tenant")
    doc.name = TEST_TENANT

    if has_field("Nexus Tenant", "tenant_name"):
        doc.tenant_name = TEST_TENANT_NAME

    if has_field("Nexus Tenant", "tenant_code"):
        doc.tenant_code = TEST_TENANT

    if has_field("Nexus Tenant", "enabled"):
        doc.enabled = 1

    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return doc


def create_ecosystem(
    ecosystem_name,
    ecosystem_type,
    is_default,
    default_public_context,
    default_business_unit,
):
    result = save_ecosystem_configuration(
        {
            "tenant": TEST_TENANT,
            "ecosystem_name": ecosystem_name,
            "ecosystem_type": ecosystem_type,
            "enabled": 1,
            "is_default": is_default,
            "activation_status": "Configured",
            "default_business_unit": default_business_unit,
            "default_public_context": default_public_context,
            "default_top_k": 5,
            "qa_enabled": 1,
            "source_citation_required": 1,
            "require_approved_knowledge": 1,
            "live_chat_enabled": 1,
            "website_widget_enabled": 0,
        }
    )

    ecosystem = result.get("ecosystem")
    frappe.db.commit()

    self_check_ecosystem_created(ecosystem)

    return ecosystem


def self_check_ecosystem_created(ecosystem):
    if not ecosystem or not frappe.db.exists("Nexus Ecosystem", ecosystem):
        frappe.throw("Test setup failed: Nexus Ecosystem was not created.")


def cleanup_test_records():
    delete_records(
        "Nexus User Context",
        [
            ["active_tenant", "=", TEST_TENANT],
        ],
    )

    delete_records(
        "Nexus Ecosystem",
        [
            ["tenant", "=", TEST_TENANT],
        ],
    )

    if frappe.db.exists("Nexus Tenant", TEST_TENANT):
        frappe.delete_doc(
            "Nexus Tenant",
            TEST_TENANT,
            force=1,
            ignore_permissions=True,
        )

    frappe.db.commit()


def delete_records(doctype, filters):
    if not frappe.db.exists("DocType", doctype):
        return

    names = frappe.get_all(
        doctype,
        filters=filters,
        pluck="name",
        limit_page_length=500,
    )

    for name in names:
        frappe.delete_doc(
            doctype,
            name,
            force=1,
            ignore_permissions=True,
        )


def has_field(doctype, fieldname):
    if not frappe.db.exists("DocType", doctype):
        return False

    return fieldname in {
        field.fieldname
        for field in frappe.get_meta(doctype).fields
    }