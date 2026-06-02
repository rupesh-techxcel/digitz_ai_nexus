import frappe
from frappe.model.document import Document


class NexusRoleAccessCategory(Document):
    def validate(self):
        self.validate_duplicate_mapping()

    def validate_duplicate_mapping(self):
        filters = {
            "role": self.role,
            "access_category": self.access_category,
            "tenant": self.tenant or "",
            "business_unit": self.business_unit or "",
            "project": self.project or "",
            "disabled": 0
        }

        existing = frappe.get_all(
            "Nexus Role Access Category",
            filters=filters,
            fields=["name"],
            limit_page_length=1
        )

        for row in existing:
            if row.name != self.name:
                frappe.throw("A matching active Role Access Category mapping already exists.")