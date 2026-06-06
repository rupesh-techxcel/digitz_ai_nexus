import hashlib

from frappe.model.document import Document


class NexusKnowledgeContextSummary(Document):
    def validate(self):
        self.set_summary_key()

    def set_summary_key(self):
        parts = [
            self.tenant or "",
            self.business_unit or "",
            self.project or "",
            self.context or "",
            self.sub_context or "",
            self.entity_type or "",
            self.entity or "",
            self.topic or "",
            self.access_policy or "",
        ]
        raw_key = "||".join(parts)
        self.summary_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
