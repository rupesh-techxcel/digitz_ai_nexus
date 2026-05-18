import json
import re
import html
import frappe
from frappe.utils import cint


CLASSIFICATION_FIELDS = [
	"tenant",
	"business_unit",
	"project",
	"context",
	"sub_context",
	"entity_type",
	"entity",
	"topic",
	"access_policy",
	"priority",
]

VALID_ACCESS_POLICIES = ["Public", "Internal", "Restricted"]


@frappe.whitelist()
def suggest_knowledge_source_fields(
	source_title=None,
	manual_content=None,
	content_handling="keep_unchanged",
	active_context=None,
	fields_to_suggest=None,
	use_existing_values=1,
):
	"""
	AI-assisted Knowledge Source suggestion.

	User provides content only.
	System builds the LLM prompt internally.

	Important:
	- Does not save anything.
	- Does not approve anything.
	- If content_handling = keep_unchanged, manual_content is not rewritten.
	"""

	source_title = (source_title or "").strip()
	manual_content = clean_manual_text(manual_content)
	content_handling = (content_handling or "keep_unchanged").strip()
	active_context = parse_json_safe(active_context)
	fields_to_suggest = parse_json_safe(fields_to_suggest)
	use_existing_values = cint(use_existing_values)

	if not manual_content:
		return {
			"success": False,
			"message": "Manual Content is required for AI Assist Source.",
		}

	if content_handling not in {
		"keep_unchanged",
		"rewrite_for_clarity",
		"generate_improved_version",
	}:
		content_handling = "keep_unchanged"

	if not isinstance(fields_to_suggest, list):
		fields_to_suggest = [
			"context",
			"sub_context",
			"entity_type",
			"entity",
			"topic",
			"access_policy",
			"priority",
		]

	fields_to_suggest = [
		fieldname for fieldname in fields_to_suggest
		if fieldname in CLASSIFICATION_FIELDS
	]

	existing_values = get_existing_classification_values() if use_existing_values else {}

	payload = build_llm_payload(
		source_title=source_title,
		manual_content=manual_content,
		content_handling=content_handling,
		active_context=active_context,
		fields_to_suggest=fields_to_suggest,
		existing_values=existing_values,
	)

	raw_response = call_llm(payload)

	parsed = extract_json_object(raw_response)

	if not parsed:
		return {
			"success": False,
			"message": "AI Assist returned an invalid response. Please retry.",
			"raw_response": raw_response,
		}

	suggestion = normalize_suggestion(
		data=parsed,
		source_title=source_title,
		manual_content=manual_content,
		content_handling=content_handling,
		active_context=active_context,
		fields_to_suggest=fields_to_suggest,
		existing_values=existing_values,
	)

	return {
		"success": True,
		"suggestion": suggestion,
		"existing_values": existing_values,
	}

@frappe.whitelist()
def create_knowledge_source_from_suggestion(
	suggestion=None,
	original_manual_content=None,
	fields_to_apply=None,
	active_context=None,
):
	"""
	Creates a Draft Nexus Knowledge Source from reviewed AI suggestion.

	Important:
	- Always creates Draft.
	- Does not approve.
	- Does not ingest.
	- Does not publish.
	- Active Studio context is used as fallback.
	- User-reviewed AI suggestion values override active context.
	"""

	suggestion = parse_json_safe(suggestion)
	fields_to_apply = parse_json_safe(fields_to_apply)
	original_manual_content = clean_manual_text(original_manual_content)
	active_context = parse_json_safe(active_context)

	if not suggestion:
		return {
			"success": False,
			"message": "Suggestion is required.",
		}

	if not isinstance(fields_to_apply, list):
		fields_to_apply = []

	if not frappe.db.exists("DocType", "Nexus Knowledge Source"):
		return {
			"success": False,
			"message": "DocType Nexus Knowledge Source does not exist.",
		}

	meta = frappe.get_meta("Nexus Knowledge Source")
	fieldnames = {df.fieldname for df in meta.fields}

	doc = frappe.new_doc("Nexus Knowledge Source")

	# ------------------------------------------------------------
	# Active Studio context fallback
	# ------------------------------------------------------------
	# These values help the created source appear in the same Studio filter.
	# They will be overwritten below if the user-reviewed suggestion provides
	# explicit values for the same fields.
	for fieldname in [
		"tenant",
		"business_unit",
		"project",
		"context",
		"channel",
		"ecosystem",
	]:
		if fieldname in fieldnames and active_context.get(fieldname):
			doc.set(fieldname, active_context.get(fieldname))

	# ------------------------------------------------------------
	# Basic source fields
	# ------------------------------------------------------------
	source_title = (suggestion.get("source_title") or "").strip()
	if not source_title:
		source_title = "AI Assisted Knowledge Source"

	set_if_exists(doc, fieldnames, "source_title", source_title)
	set_if_exists(doc, fieldnames, "title", source_title)

	set_if_exists(doc, fieldnames, "source_type", suggestion.get("source_type") or "Manual")

	# ------------------------------------------------------------
	# Manual content
	# ------------------------------------------------------------
	# suggested_content is used only when the user accepted AI rewritten content.
	# Otherwise original_manual_content is saved as plain text.
	suggested_content = clean_manual_text(suggestion.get("manual_content") or "")
	final_content = suggested_content or original_manual_content

	set_if_exists(doc, fieldnames, "manual_content", final_content)

	# ------------------------------------------------------------
	# User-reviewed classification / governance fields
	# ------------------------------------------------------------
	for fieldname in [
		"tenant",
		"business_unit",
		"project",
		"context",
		"sub_context",
		"entity_type",
		"entity",
		"topic",
		"access_policy",
	]:
		if fieldname not in fields_to_apply:
			continue

		field_value = get_suggestion_field_value(suggestion.get(fieldname))
		if field_value:
			set_if_exists(doc, fieldnames, fieldname, field_value)

	# ------------------------------------------------------------
	# Priority
	# ------------------------------------------------------------
	if "priority" in fields_to_apply:
		priority = suggestion.get("priority")
		try:
			priority = int(priority)
		except Exception:
			priority = 10

		if priority < 0:
			priority = 0

		if priority > 100:
			priority = 100

		set_if_exists(doc, fieldnames, "priority", priority)

	# ------------------------------------------------------------
	# Always Draft
	# ------------------------------------------------------------
	set_if_exists(doc, fieldnames, "status", "Draft")

	doc.insert(ignore_permissions=False)

	return {
		"success": True,
		"message": "Draft Knowledge Source created.",
		"name": doc.name,
	}

def build_llm_payload(
	source_title,
	manual_content,
	content_handling,
	active_context,
	fields_to_suggest,
	existing_values,
):
	return {
		"system_prompt": get_system_prompt(),
		"user_payload": {
			"source_title": source_title,
			"manual_content": manual_content,
			"content_handling": content_handling,
			"active_context": active_context or {},
			"fields_to_suggest": fields_to_suggest or [],
			"existing_values": existing_values or {},
			"rules": {
				"user_does_not_write_prompt": True,
				"system_builds_prompt": True,
				"status_must_always_be": "Draft",
				"source_type_must_be": "Manual",
				"prefer_existing_values": True,
				"do_not_change_content_when_keep_unchanged": True,
			},
		},
	}


def get_system_prompt():
	return """
You are assisting DIGITZ AI Nexus Studio with Knowledge Source setup.

The user does not write a prompt. The system provides manual content and context.

Return only valid JSON. Do not include markdown.

Your task:
1. Understand the manual content.
2. Suggest only the requested fields.
3. Prefer existing database values when semantically suitable.
4. If no existing value fits, suggest a new clean enterprise value.
5. Explain every classification suggestion briefly.
6. Never approve, ingest, publish, or mark ready.
7. Always return status as Draft.
8. Source Type must always be Manual.

Content handling:
- If content_handling = keep_unchanged, return manual_content as null.
- If content_handling = rewrite_for_clarity, return a clearer rewritten version.
- If content_handling = generate_improved_version, return an improved structured version based on the same content.

Return JSON in this exact shape:

{
  "source_title": "",
  "source_type": "Manual",
  "manual_content": null,
  "tenant": {
    "value": "",
    "matched_existing": false,
    "confidence": 0.0,
    "reason": ""
  },
  "business_unit": {
    "value": "",
    "matched_existing": false,
    "confidence": 0.0,
    "reason": ""
  },
  "project": {
    "value": "",
    "matched_existing": false,
    "confidence": 0.0,
    "reason": ""
  },
  "context": {
    "value": "",
    "matched_existing": false,
    "confidence": 0.0,
    "reason": ""
  },
  "sub_context": {
    "value": "",
    "matched_existing": false,
    "confidence": 0.0,
    "reason": ""
  },
  "entity_type": {
    "value": "",
    "matched_existing": false,
    "confidence": 0.0,
    "reason": ""
  },
  "entity": {
    "value": "",
    "matched_existing": false,
    "confidence": 0.0,
    "reason": ""
  },
  "topic": {
    "value": "",
    "matched_existing": false,
    "confidence": 0.0,
    "reason": ""
  },
  "access_policy": {
    "value": "Public",
    "matched_existing": false,
    "confidence": 0.0,
    "reason": ""
  },
  "priority": 10,
  "status": "Draft",
  "summary": "",
  "warnings": []
}

Use active_context where it is clearly applicable.
Prefer existing values from existing_values where semantically close.
Only suggest new values when needed.
"""


def call_llm(payload):
	settings = get_nexus_settings()

	api_key = settings.get_password("api_key") if settings else None
	openai_project_id = getattr(settings, "openai_project_id", None) if settings else None
	model = getattr(settings, "llm_model", None) if settings else None

	if not api_key:
		frappe.throw("OpenAI API key is not configured in Nexus Settings.")

	model = model or "gpt-4o-mini"

	try:
		from openai import OpenAI
	except Exception:
		frappe.throw("OpenAI Python package is not available in this environment.")

	client_kwargs = {
		"api_key": api_key,
	}

	if openai_project_id:
		client_kwargs["project"] = openai_project_id

	client = OpenAI(**client_kwargs)

	response = client.chat.completions.create(
		model=model,
		temperature=0.15,
		messages=[
			{
				"role": "system",
				"content": payload.get("system_prompt") or "",
			},
			{
				"role": "user",
				"content": json.dumps(payload.get("user_payload") or {}, ensure_ascii=False),
			},
		],
	)

	if not response or not response.choices:
		return ""

	return response.choices[0].message.content or ""


def get_nexus_settings():
	try:
		return frappe.get_single("Nexus Settings")
	except Exception:
		return None


def get_existing_classification_values():
	doctypes_to_scan = [
		"Nexus Knowledge Source",
		"Nexus Knowledge Unit",
	]

	fields_to_scan = [
		"tenant",
		"business_unit",
		"project",
		"context",
		"sub_context",
		"entity_type",
		"entity",
		"topic",
		"access_policy",
	]

	out = {fieldname: [] for fieldname in fields_to_scan}

	for doctype in doctypes_to_scan:
		if not frappe.db.exists("DocType", doctype):
			continue

		meta = frappe.get_meta(doctype)
		existing_fields = {df.fieldname for df in meta.fields}

		for fieldname in fields_to_scan:
			if fieldname not in existing_fields:
				continue

			rows = frappe.get_all(
				doctype,
				fields=[fieldname],
				filters={fieldname: ["is", "set"]},
				distinct=True,
				limit_page_length=300,
				order_by=f"{fieldname} asc",
			)

			for row in rows:
				value = (row.get(fieldname) or "").strip()
				if value and value not in out[fieldname]:
					out[fieldname].append(value)

	for fieldname in out:
		out[fieldname] = sorted(out[fieldname])[:150]

	return out


def normalize_suggestion(
	data,
	source_title,
	manual_content,
	content_handling,
	active_context,
	fields_to_suggest,
	existing_values,
):
	suggestion = {}

	suggestion["source_title"] = (
		as_text(data.get("source_title"))
		or source_title
		or derive_title_from_content(manual_content)
		or "AI Assisted Knowledge Source"
	)

	suggestion["source_type"] = "Manual"

	if content_handling == "keep_unchanged":
		suggestion["manual_content"] = None
		suggestion["content_was_changed"] = False
	else:
		suggestion["manual_content"] = as_text(data.get("manual_content"))
		suggestion["content_was_changed"] = bool(suggestion["manual_content"])

	for fieldname in [
		"tenant",
		"business_unit",
		"project",
		"context",
		"sub_context",
		"entity_type",
		"entity",
		"topic",
		"access_policy",
	]:
		if fieldname in fields_to_suggest:
			suggestion[fieldname] = normalize_field_suggestion(
				fieldname=fieldname,
				raw=data.get(fieldname),
				active_context=active_context,
				existing_values=existing_values,
				was_requested=True,
			)
		else:
			suggestion[fieldname] = normalize_field_suggestion(
				fieldname=fieldname,
				raw=None,
				active_context=active_context,
				existing_values=existing_values,
				was_requested=False,
			)

	access_policy_value = suggestion["access_policy"]["value"]
	if access_policy_value and access_policy_value not in VALID_ACCESS_POLICIES:
		suggestion["access_policy"]["value"] = "Public"
		suggestion["access_policy"]["matched_existing"] = (
			"Public" in (existing_values.get("access_policy") or [])
		)
		suggestion["access_policy"]["reason"] = (
			suggestion["access_policy"]["reason"]
			or "Defaulted to Public because the suggested access policy was not valid."
		)

	if not suggestion["access_policy"]["value"]:
		suggestion["access_policy"]["value"] = "Public"
		suggestion["access_policy"]["reason"] = (
			suggestion["access_policy"]["reason"]
			or "Default access policy for general knowledge source."
		)

	priority = data.get("priority")
	try:
		priority = int(priority)
	except Exception:
		priority = 10

	if priority < 0:
		priority = 0

	if priority > 100:
		priority = 100

	suggestion["priority"] = priority
	suggestion["status"] = "Draft"
	suggestion["summary"] = as_text(data.get("summary"))
	suggestion["warnings"] = data.get("warnings") if isinstance(data.get("warnings"), list) else []
	suggestion["fields_requested"] = fields_to_suggest

	return suggestion


def normalize_field_suggestion(
	fieldname,
	raw,
	active_context,
	existing_values,
	was_requested=True,
):
	if isinstance(raw, dict):
		value = as_text(raw.get("value"))
		confidence = safe_float(raw.get("confidence"), 0)
		reason = as_text(raw.get("reason"))
		matched_existing = bool(raw.get("matched_existing"))
	else:
		value = as_text(raw)
		confidence = 0
		reason = ""
		matched_existing = False

	if not value and active_context and active_context.get(fieldname):
		value = as_text(active_context.get(fieldname))
		confidence = confidence or 0.75
		reason = reason or (
			"Used active Studio context."
			if was_requested
			else "Preserved from active Studio context because this field was not selected for AI suggestion."
		)

	existing = existing_values.get(fieldname) or []

	if value in existing:
		matched_existing = True

	if value and not matched_existing:
		close = find_case_insensitive_match(value, existing)
		if close:
			value = close
			matched_existing = True
			reason = reason or "Matched an existing database value."

	return {
		"value": value,
		"matched_existing": matched_existing,
		"confidence": confidence,
		"reason": reason,
		"was_requested": was_requested,
	}


def set_if_exists(doc, fieldnames, fieldname, value):
	if fieldname in fieldnames:
		doc.set(fieldname, value)


def get_suggestion_field_value(value):
	if isinstance(value, dict):
		return (value.get("value") or "").strip()

	return (value or "").strip()


def find_case_insensitive_match(value, existing):
	value_norm = normalize_compare(value)

	for item in existing:
		if normalize_compare(item) == value_norm:
			return item

	return ""


def derive_title_from_content(manual_content):
	content = (manual_content or "").strip()

	if not content:
		return ""

	first_line = content.splitlines()[0].strip()

	if len(first_line) > 80:
		return first_line[:77].rstrip() + "..."

	return first_line


def normalize_compare(value):
	return re.sub(r"\s+", " ", str(value or "").strip().lower())


def extract_json_object(raw):
	raw = (raw or "").strip()

	if not raw:
		return None

	if raw.startswith("```"):
		raw = raw.strip("`").strip()
		raw = raw.replace("json\n", "", 1).replace("JSON\n", "", 1).strip()

	try:
		return json.loads(raw)
	except Exception:
		pass

	start = raw.find("{")
	end = raw.rfind("}")

	if start >= 0 and end > start:
		try:
			return json.loads(raw[start : end + 1])
		except Exception:
			return None

	return None


def parse_json_safe(value):
	if not value:
		return {}

	if isinstance(value, (dict, list)):
		return value

	try:
		return json.loads(value)
	except Exception:
		return {}


def as_text(value):
	if value is None:
		return ""

	return str(value).strip()


def safe_float(value, default=0):
	try:
		return float(value)
	except Exception:
		return default

def clean_manual_text(value):
	value = as_text(value)

	if not value:
		return ""

	value = value.replace("\r\n", "\n").replace("\r", "\n")

	value = re.sub(r"<\s*br\s*/?\s*>", "\n", value, flags=re.IGNORECASE)
	value = re.sub(r"</\s*p\s*>", "\n\n", value, flags=re.IGNORECASE)
	value = re.sub(r"</\s*div\s*>", "\n", value, flags=re.IGNORECASE)
	value = re.sub(r"</\s*li\s*>", "\n", value, flags=re.IGNORECASE)

	value = re.sub(r"<[^>]+>", "", value)

	value = html.unescape(value)

	lines = [line.strip() for line in value.split("\n")]
	cleaned_lines = []
	blank_seen = False

	for line in lines:
		if not line:
			if not blank_seen:
				cleaned_lines.append("")
			blank_seen = True
			continue

		cleaned_lines.append(line)
		blank_seen = False

	return "\n".join(cleaned_lines).strip()