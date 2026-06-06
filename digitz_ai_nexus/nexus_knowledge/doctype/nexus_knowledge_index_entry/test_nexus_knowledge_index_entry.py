import frappe
from frappe.tests.utils import FrappeTestCase


class TestNexusKnowledgeIndexEntry(FrappeTestCase):
    def test_entry_hash_is_set(self):
        if not frappe.db.exists("DocType", "Nexus Knowledge Index Entry"):
            return

        doc = frappe.new_doc("Nexus Knowledge Index Entry")
        doc.entry_type = "Intellectual Summary"
        doc.canonical_text = "what DIGITZ AI Nexus is"
        doc.status = "Active"
        doc.access_policy = "Public"
        doc.sensitivity = "public"
        doc.insert(ignore_permissions=True)

        self.assertTrue(doc.entry_hash)

        frappe.delete_doc(doc.doctype, doc.name, force=True)
