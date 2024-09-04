from abc import ABC, abstractmethod


class LLMProviderBase(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """Generates a response from the LLM based on the input prompt."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Returns the name of the model used by the LLM provider."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the name of the LLM provider."""
        pass
