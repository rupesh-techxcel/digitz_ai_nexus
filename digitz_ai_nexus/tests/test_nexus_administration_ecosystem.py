import frappe
from frappe.tests.utils import FrappeTestCase

from digitz_ai_nexus.api.nexus_administration import (
    get_administration_snapshot,
    save_ecosystem_configuration,
)
from digitz_ai_nexus.services.tenant_context import get_ecosystem_for_tenant


TEST_TENANT = "TEST-ADMIN-SINGLE-ECO"
TEST_TENANT_NAME = "Test Administration Single Ecosystem"
TEST_BU = "Administration Single Ecosystem BU"
ECO_NAME = "TEST-ADMIN Tenant Ecosystem"


class TestNexusAdministrationEcosystem(FrappeTestCase):
    def setUp(self):
        cleanup_test_records()
        ensure_test_tenant()

    def tearDown(self):
        cleanup_test_records()

    def test_tenant_uses_one_enabled_ecosystem(self):
        first = save_ecosystem_configuration({
            "tenant": TEST_TENANT,
            "configuration_name": ECO_NAME,
            "configuration_type": "Production",
            "enabled": 1,
            "is_default": 1,
            "default_business_unit": TEST_BU,
        })

        second = save_ecosystem_configuration({
            "tenant": TEST_TENANT,
            "configuration_name": "Ignored Second Ecosystem Name",
            "configuration_type": "Internal Platform",
            "enabled": 1,
            "default_business_unit": TEST_BU,
        })

        self.assertEqual(first.get("ecosystem"), second.get("ecosystem"))

        ecosystems = frappe.get_all(
            "Nexus Tenant Configuration",
            filters={"tenant": TEST_TENANT, "enabled": 1},
            fields=["name", "configuration_type", "is_default"],
        )

        self.assertEqual(len(ecosystems), 1)
        self.assertEqual(ecosystems[0].configuration_type, "Internal Platform")
        self.assertEqual(int(ecosystems[0].is_default or 0), 1)

    def test_direct_second_enabled_ecosystem_is_rejected(self):
        first = save_ecosystem_configuration({
            "tenant": TEST_TENANT,
            "configuration_name": ECO_NAME,
            "enabled": 1,
            "is_default": 1,
            "default_business_unit": TEST_BU,
        })

        self.assertTrue(first.get("ecosystem"))

        doc = frappe.new_doc("Nexus Tenant Configuration")
        doc.tenant = TEST_TENANT
        doc.configuration_name = "Second Enabled Ecosystem"
        doc.configuration_type = "Sandbox"
        doc.enabled = 1

        with self.assertRaises(frappe.ValidationError):
            doc.insert(ignore_permissions=True)

    def test_snapshot_uses_single_tenant_configuration(self):
        result = save_ecosystem_configuration({
            "tenant": TEST_TENANT,
            "configuration_name": ECO_NAME,
            "configuration_type": "Production",
            "enabled": 1,
            "is_default": 1,
            "default_business_unit": TEST_BU,
        })

        snapshot = get_administration_snapshot(tenant=TEST_TENANT)

        self.assertIsNone(snapshot["user_context"])
        self.assertEqual(snapshot["tenant"]["name"], TEST_TENANT)
        self.assertEqual(snapshot["tenant_configuration"]["name"], result.get("ecosystem"))
        self.assertEqual(snapshot["ecosystem"]["name"], result.get("ecosystem"))
        self.assertEqual(snapshot["resolved_context"]["ecosystem"], result.get("ecosystem"))
        self.assertEqual(len(snapshot.get("tenant_configurations") or []), 1)

    def test_runtime_resolver_rejects_legacy_multiple_enabled_ecosystems(self):
        save_ecosystem_configuration({
            "tenant": TEST_TENANT,
            "configuration_name": ECO_NAME,
            "enabled": 1,
            "is_default": 1,
            "default_business_unit": TEST_BU,
        })

        frappe.db.sql(
            """
            insert into `tabNexus Tenant Configuration`
                (name, owner, creation, modified, modified_by, docstatus, idx,
                 tenant, configuration_name, configuration_type, enabled, is_default)
            values
                (%s, %s, now(), now(), %s, 0, 0, %s, %s, %s, 1, 0)
            """,
            (
                "Second Legacy Enabled Ecosystem",
                frappe.session.user,
                frappe.session.user,
                TEST_TENANT,
                "Second Legacy Enabled Ecosystem",
                "Sandbox",
            ),
        )

        with self.assertRaises(frappe.ValidationError):
            get_ecosystem_for_tenant(TEST_TENANT)


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


def cleanup_test_records():
    delete_records(
        "Nexus User Context",
        [["active_tenant", "=", TEST_TENANT]],
    )

    delete_records(
        "Nexus Tenant Configuration",
        [["tenant", "=", TEST_TENANT]],
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

    for row in frappe.get_all(doctype, filters=filters, pluck="name"):
        frappe.delete_doc(
            doctype,
            row,
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
