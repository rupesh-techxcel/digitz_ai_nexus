import json
import frappe
from frappe.model.document import Document

class NexusAccessPolicy(Document):
    def validate(self):
        self.validate_json_fields()

    def validate_json_fields(self):
        for fieldname in [
            "allowed_roles",
            "excluded_roles",
            "allowed_designations",
            "excluded_designations",
        ]:
            value = self.get(fieldname)
            if not value:
                continue

            try:
                parsed = json.loads(value)
            except Exception:
                frappe.throw(f"{self.meta.get_label(fieldname)} must be a valid JSON array.")

            if not isinstance(parsed, list):
                frappe.throw(f"{self.meta.get_label(fieldname)} must be a JSON array.")