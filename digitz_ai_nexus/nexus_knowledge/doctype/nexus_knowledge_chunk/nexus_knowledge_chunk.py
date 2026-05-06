import hashlib
import frappe
from frappe.model.document import Document


class NexusKnowledgeChunk(Document):
    def validate(self):
        self.set_chunk_hash()

    def set_chunk_hash(self):
        if self.chunk_text:
            self.chunk_hash = hashlib.sha256(self.chunk_text.encode("utf-8")).hexdigest()