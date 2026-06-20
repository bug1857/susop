class BaseAIProvider:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError()
