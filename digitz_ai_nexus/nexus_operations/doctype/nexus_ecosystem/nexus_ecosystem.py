# Copyright (c) 2026, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint


class NexusEcosystem(Document):
	def validate(self):
		self.enforce_single_active_ecosystem()

		if cint(self.enabled):
			self.is_default = 1

	def enforce_single_active_ecosystem(self):
		if not self.tenant or not cint(self.enabled):
			return

		existing = frappe.get_all(
			"Nexus Ecosystem",
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
					"Only one enabled Nexus Ecosystem is allowed per tenant. "
					f"Disable or update existing ecosystem {existing[0]} instead."
				)
			)
