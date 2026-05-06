import hashlib
import frappe
from frappe.model.document import Document


class NexusKnowledgeUnit(Document):
    def validate(self):
        self.set_context_path()
        self.set_content_hash()

    def set_context_path(self):
        parts = [
            self.context,
            self.sub_context,
            self.entity_type,
            self.entity,
            self.topic,
        ]
        self.context_path = "/".join([p.strip() for p in parts if p and str(p).strip()])

    def set_content_hash(self):
        if self.content:
            self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()