# src/llm_providers/ollama_provider.py

from langchain_community.llms import Ollama
import structlog
from src.config import Config
from src.llm_providers.llm_provider_base import LLMProviderBase
import asyncio

logger = structlog.get_logger(__name__)


class OllamaProvider(LLMProviderBase):
    """LLM provider for interacting with the Ollama language model."""

    def __init__(self, config: Config):
        """Initializes the Ollama provider with configuration and model details."""
        self.config = config
        self.model_name = config.OLLAMA_MODEL_NAME
        self.base_url = config.OLLAMA_BASE_URL

        logger.info(
            "Initializing Ollama", model=self.model_name, base_url=self.base_url
        )

        self.llm = Ollama(model=self.model_name, base_url=self.base_url)

    async def generate_response(self, prompt: str) -> str:
        """Sends a prompt to the Ollama model and returns the generated response."""
        logger.info("Sending prompt to Ollama", prompt_preview=prompt[:100])

        try:
            response = await asyncio.to_thread(self.llm.invoke, prompt)
            logger.info(
                "Received response from Ollama", response_preview=response[:100]
            )
            return response.strip()
        except Exception as e:
            logger.error("Error generating response from Ollama", error=str(e))
            return f"Error generating response: {str(e)}"

    def get_model_name(self) -> str:
        """Returns the name of the model used by Ollama."""
        return self.model_name

    def get_provider_name(self) -> str:
        """Returns the name of the LLM provider, which is 'Ollama'."""
        return "Ollama"
