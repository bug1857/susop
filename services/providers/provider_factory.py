from typing import Optional
from app.services.providers.ollama_provider import OllamaProvider

class ProviderFactory:
    @staticmethod
    def get_provider(model_name: Optional[str] = None):
        # Import OLLAMA_MODEL_NAME locally to avoid circular import during bootstrapping
        from app.services.ai_copilot_service import OLLAMA_MODEL_NAME
        target_model = model_name or OLLAMA_MODEL_NAME
        return OllamaProvider(model_name=target_model)
