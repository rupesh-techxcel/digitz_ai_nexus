import json
import frappe
from openai import OpenAI


def get_openai_client():
    settings = frappe.get_single("Nexus Settings")

    api_key = settings.get_password("api_key") if hasattr(settings, "get_password") else None

    if not api_key:
        frappe.throw("OpenAI API key is not configured in Nexus Settings.")

    project_id = settings.get("openai_project_id")

    if project_id:
        return OpenAI(api_key=api_key, project=project_id)

    return OpenAI(api_key=api_key)


def get_embedding_model():
    settings = frappe.get_single("Nexus Settings")
    return settings.get("embedding_model") or "text-embedding-3-small"


def generate_embedding(text):
    if not text:
        return []

    client = get_openai_client()
    model = get_embedding_model()

    response = client.embeddings.create(
        model=model,
        input=text,
    )

    embedding = response.data[0].embedding

    return embedding


def generate_embedding_json(text):
    embedding = generate_embedding(text)
    return json.dumps(embedding)