import frappe
from frappe.model.document import Document


class NexusKnowledgeSource(Document):
    def validate(self):
        if not self.title:
            frappe.throw("Title is required")

        if not self.source_type:
            frappe.throw("Source Type is required")

        if self.source_type in ["PDF", "DOCX", "TXT"] and not self.source_file:
            frappe.throw("Source File is required for uploaded documents")

        if self.source_type == "Manual" and not self.manual_content:
            frappe.throw("Manual Content is required for manual knowledge")

        if not self.status:
            self.status = "Draft"

        if not self.processing_status:
            self.processing_status = "Pending"