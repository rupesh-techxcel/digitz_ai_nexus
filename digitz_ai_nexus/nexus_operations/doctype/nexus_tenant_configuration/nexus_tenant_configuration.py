import frappe
from frappe.model.document import Document
from frappe.utils import cint


class NexusTenantConfiguration(Document):
	def validate(self):
		self.enforce_single_active_configuration()

		if cint(self.enabled):
			self.is_default = 1

	def enforce_single_active_configuration(self):
		if not self.tenant or not cint(self.enabled):
			return

		existing = frappe.get_all(
			"Nexus Tenant Configuration",
			filters={
				"tenant": self.tenant,
				"enabled": 1,
				"name": ["!=", self.name or ""],
			},
			pluck="name",
			limit_page_length=1,
		)

		if existing:
			frappe.throw(
				(
					"Only one enabled Tenant Configuration is allowed per tenant. "
					f"Disable or update existing configuration {existing[0]} instead."
				)
			)
