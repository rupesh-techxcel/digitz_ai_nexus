class FakeEmbeddingProvider:
    def embed(self, text: str):
        text = (text or "").lower()

        if "digitz erp" in text:
            return [1.0, 0.0, 0.0]

        if "hire return" in text:
            return [0.0, 1.0, 0.0]

        if "valuation" in text or "finance" in text:
            return [0.0, 0.0, 1.0]

        return [0.1, 0.1, 0.1]