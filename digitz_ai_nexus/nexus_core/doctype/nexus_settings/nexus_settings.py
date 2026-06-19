# Copyright (c) 2026, Techxcel Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password


class NexusSettings(Document):
	def before_save(self):
		_preserve_password_if_blank(self, "api_key")


def _preserve_password_if_blank(doc, fieldname):
	"""
	Password fields always appear blank in the Frappe UI.
	If the user saves the document without re-entering the password,
	restore the existing encrypted value so it is not wiped.
	"""
	if getattr(doc, fieldname, None):
		return
	try:
		existing = get_decrypted_password(doc.doctype, doc.name, fieldname, raise_exception=False)
		if existing:
			doc.set(fieldname, existing)
	except Exception:
		pass
