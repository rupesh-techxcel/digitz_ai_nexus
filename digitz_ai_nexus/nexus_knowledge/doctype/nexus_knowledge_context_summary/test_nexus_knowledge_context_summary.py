import frappe
from frappe.tests.utils import FrappeTestCase


class TestNexusKnowledgeContextSummary(FrappeTestCase):
    def test_summary_key_is_set(self):
        if not frappe.db.exists("DocType", "Nexus Knowledge Context Summary"):
            return

        doc = frappe.new_doc("Nexus Knowledge Context Summary")
        doc.summary_title = "DIGITZ AI Nexus / Website / Know-How"
        doc.summary_text = "DIGITZ AI Nexus public website knowledge covers product and platform know-how."
        doc.tenant = "DIGITZ-NEXUS"
        doc.topic = "Nexus Platform Know-How"
        doc.access_policy = "Public"
        doc.sensitivity = "public"
        doc.status = "Active"
        doc.insert(ignore_permissions=True)

        self.assertTrue(doc.summary_key)

        frappe.delete_doc(doc.doctype, doc.name, force=True)
