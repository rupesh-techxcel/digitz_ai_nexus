class FakeLLMProvider:
    def generate(self, prompt: str):
        return "Fake answer from test provider."