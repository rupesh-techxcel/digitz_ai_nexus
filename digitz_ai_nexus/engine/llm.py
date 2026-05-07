import frappe
from openai import OpenAI


def get_openai_client():
    settings = frappe.get_single("Nexus Settings")

    api_key = settings.get_password("api_key")
    if not api_key:
        frappe.throw("OpenAI API Key not set in Nexus Settings")

    return OpenAI(
        api_key=api_key,
        project=settings.openai_project_id or None,
        timeout=20.0,
        max_retries=1,
    )

class OpenAILLMProvider:
    def __init__(self):
        settings = frappe.get_single("Nexus Settings")
        self.client = get_openai_client()
        self.model = settings.llm_model or "gpt-4o-mini"

    def generate(self, prompt: str):
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are DIGITZ AI Nexus, a controlled enterprise knowledge assistant."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )

            return response.choices[0].message.content

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "Nexus LLM Generation Failed"
            )
            raise


def get_default_llm_provider():
    return OpenAILLMProvider()


def generate_answer(prompt: str, provider=None):
    provider = provider or get_default_llm_provider()
    return provider.generate(prompt)