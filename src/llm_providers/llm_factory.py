# src/llm_providers/llm_factory.py

from src.config import Config


class LLMFactory:
    @staticmethod
    def get_provider(config: Config):
        if config.LLM_PROVIDER == "openai":
            from src.llm_providers.openai_provider import OpenAIProvider

            return OpenAIProvider(config)
        elif config.LLM_PROVIDER == "ollama":
            from src.llm_providers.ollama_provider import OllamaProvider

            return OllamaProvider(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")

    @staticmethod
    def list_available_providers():
        return ["openai", "ollama"]
