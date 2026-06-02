import frappe
from frappe.model.document import Document


class NexusAccessCategory(Document):
    def validate(self):
        self.category_name = (self.category_name or "").strip()

        if not self.category_name:
            frappe.throw("Category Name is required.")

        seen = set()

        for row in self.get("allowed_policies") or []:
            policy = (row.access_policy or "").strip()

            if not policy:
                frappe.throw("Access Policy is required in Allowed Policies.")

            if policy in seen:
                frappe.throw(f"Duplicate Access Policy found: {policy}")

            seen.add(policy)