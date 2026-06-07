import frappe


BUSINESS_UNIT_FIELDS = {
	"Nexus Knowledge Unit": ["business_unit"],
	"Nexus Knowledge Chunk": ["business_unit"],
	"Nexus Knowledge Source": ["business_unit"],
	"Nexus Tenant Configuration": ["default_business_unit"],
	"Nexus User Context": ["active_business_unit"],
	"Nexus Knowledge Test Case": ["business_unit"],
	"Nexus Knowledge Test Run": ["business_unit"],
	"Nexus Query Log": ["business_unit"],
	"Nexus Live Agent": ["business_unit"],
	"Nexus Test Case": ["business_unit"],
}

PUBLIC_CONTEXT_FIELDS = {
	"Nexus Tenant Configuration": ["default_public_context"],
	"Nexus Knowledge Unit": ["context"],
	"Nexus Knowledge Chunk": ["context"],
	"Nexus Knowledge Source": ["context"],
	"Nexus Knowledge Test Case": ["context"],
	"Nexus Knowledge Test Run": ["context"],
	"Nexus Query Log": ["context"],
	"Nexus Test Case": ["context"],
}


def execute():
	if frappe.db.exists("DocType", "Nexus Business Unit"):
		ensure_business_units()

	if frappe.db.exists("DocType", "Nexus Public Context"):
		ensure_public_contexts()

	frappe.db.commit()


def ensure_business_units():
	values = collect_values(BUSINESS_UNIT_FIELDS)
	values.add("Default")

	for value in sorted(values):
		upsert_master(
			doctype="Nexus Business Unit",
			name=value,
			values={
				"business_unit_name": value,
				"enabled": 1,
				"description": "Created from existing Nexus Business Unit usage.",
			},
		)


def ensure_public_contexts():
	values = collect_values(PUBLIC_CONTEXT_FIELDS)
	values.add("Nexus Live")

	for value in sorted(values):
		upsert_master(
			doctype="Nexus Public Context",
			name=value,
			values={
				"public_context_name": value,
				"enabled": 1,
				"description": "Created from existing Nexus Public Context usage.",
			},
		)


def collect_values(doctype_fields):
	values = set()

	for doctype, fieldnames in doctype_fields.items():
		if not frappe.db.exists("DocType", doctype):
			continue

		meta = frappe.get_meta(doctype)

		for fieldname in fieldnames:
			if not meta.has_field(fieldname):
				continue

			for row in frappe.get_all(
				doctype,
				fields=[fieldname],
				limit_page_length=5000,
			):
				value = (row.get(fieldname) or "").strip()

				if value:
					values.add(value)

	return values


def upsert_master(doctype, name, values):
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
	else:
		doc = frappe.new_doc(doctype)

	for fieldname, value in values.items():
		if frappe.get_meta(doctype).has_field(fieldname):
			doc.set(fieldname, value)

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
