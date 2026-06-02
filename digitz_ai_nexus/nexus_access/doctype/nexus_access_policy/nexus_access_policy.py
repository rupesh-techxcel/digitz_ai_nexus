import json
import frappe
from frappe.model.document import Document


class NexusAccessPolicy(Document):
    def validate(self):
        self.normalize_policy_name()
        self.validate_primitive_policy()
        self.validate_json_fields()

    def normalize_policy_name(self):
        self.policy_name = (self.policy_name or "").strip()

        if not self.policy_name:
            frappe.throw("Policy Name is required.")

    def validate_primitive_policy(self):
        """
        Final Nexus access rule:
        - Public is the only primitive/system access policy.
        - Anything other than Public is user-defined.
        - Legacy direct role/designation rules may still exist, but new access
          enforcement is through Access Category, Role Access Category, and
          Channel Access Category.
        """

        if self.policy_name.lower() == "public":
            if self.meta.has_field("is_primitive"):
                self.is_primitive = 1

            # Public should never be disabled because it is the primitive/base policy.
            if self.meta.has_field("disabled"):
                self.disabled = 0

            return

        if self.meta.has_field("is_primitive") and self.is_primitive:
            frappe.throw("Only Public can be marked as a primitive access policy.")

    def validate_json_fields(self):
        """
        These fields are retained for legacy/reference compatibility.

        They are not the primary access-control mechanism in the new design,
        but if values are entered, they should remain valid JSON arrays.
        """

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