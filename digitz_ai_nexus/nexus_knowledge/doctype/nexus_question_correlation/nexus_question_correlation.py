import hashlib

from frappe.model.document import Document


class NexusQuestionCorrelation(Document):
    def validate(self):
        raw_key = "||".join([
            self.source_question or "",
            self.related_question or "",
            self.tenant or "",
            self.access_policy or "",
        ])
        self.correlation_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
