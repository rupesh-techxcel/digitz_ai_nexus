import frappe
from openai import OpenAI


def get_openai_client():
    settings = frappe.get_single("Nexus Settings")

    api_key = settings.get_password("api_key")
    if not api_key:
        frappe.throw("OpenAI API Key not set in Nexus Settings")

    return OpenAI(
        api_key=api_key,
        project=settings.openai_project_id or None
    )


class OpenAIEmbeddingProvider:
    def __init__(self):
        settings = frappe.get_single("Nexus Settings")
        self.client = get_openai_client()
        self.model = settings.embedding_model or "text-embedding-3-small"

    def embed(self, text: str):
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding


def get_default_embedding_provider():
    return OpenAIEmbeddingProvider()


def generate_embedding(text: str, provider=None):
    if not text:
        return []

    provider = provider or get_default_embedding_provider()
    return provider.embed(text)