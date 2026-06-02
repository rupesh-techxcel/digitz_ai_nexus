import frappe
from frappe.model.document import Document


class NexusChannel(Document):
    def validate(self):
        self.channel_name = (self.channel_name or "").strip()

        if not self.channel_name:
            frappe.throw("Channel Name is required.")