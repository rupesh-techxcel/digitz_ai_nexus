import frappe
from frappe.model.document import Document


class NexusChannelAccessCategory(Document):
    def validate(self):
        self.validate_duplicate_mapping()

    def validate_duplicate_mapping(self):
        filters = {
            "channel": self.channel,
            "access_category": self.access_category,
            "tenant": self.tenant or "",
            "business_unit": self.business_unit or "",
            "project": self.project or "",
            "disabled": 0
        }

        existing = frappe.get_all(
            "Nexus Channel Access Category",
            filters=filters,
            fields=["name"],
            limit_page_length=1
        )

        for row in existing:
            if row.name != self.name:
                frappe.throw("A matching active Channel Access Category mapping already exists.")