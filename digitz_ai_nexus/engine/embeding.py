import json
import frappe
from openai import OpenAI


def get_openai_client():
    settings = frappe.get_single("Nexus Settings")

    if not settings.api_key:
        frappe.throw("OpenAI API Key not set in Nexus Settings")

    return OpenAI(api_key=settings.api_key)


def generate_embedding(text: str):
    settings = frappe.get_single("Nexus Settings")

    client = get_openai_client()

    response = client.embeddings.create(
        model=settings.embedding_model,
        input=text
    )

    return response.data[0].embedding