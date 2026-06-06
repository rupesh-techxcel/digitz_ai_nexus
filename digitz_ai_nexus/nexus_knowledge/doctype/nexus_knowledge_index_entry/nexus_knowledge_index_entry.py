import hashlib

from frappe.model.document import Document


class NexusKnowledgeIndexEntry(Document):
    def validate(self):
        self.set_entry_hash()

    def set_entry_hash(self):
        value = "||".join([
            self.entry_type or "",
            self.canonical_text or "",
            self.knowledge_source or "",
            self.knowledge_unit or "",
            self.knowledge_chunk or "",
        ])
        self.entry_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
