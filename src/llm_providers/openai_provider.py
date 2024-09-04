# src/llm_providers/openai_provider.py

from openai import OpenAI
import logging
from src.config import Config
from src.llm_providers.llm_provider_base import LLMProviderBase

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProviderBase):
    """LLM provider for interacting with the OpenAI language model."""

    def __init__(self, config: Config):
        """Initializes the OpenAI provider with configuration and API key."""
        self.config = config
        self.client = OpenAI(api_key=self.config.OPENAI_API_KEY)
        self.model = self.config.OPENAI_MODEL_NAME

        logger.info(f"Initializing OpenAI with model: {self.model}")

    def generate_response(self, prompt: str) -> str:
        """Sends a prompt to the OpenAI model and returns the generated response."""
        logger.info(
            f"Sending prompt to OpenAI: {prompt[:100]}..."
        )  # Log first 100 characters of prompt

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
            )
            result = response.choices[0].message.content.strip()
            logger.info(
                f"Received response from OpenAI: {result[:100]}..."
            )  # Log first 100 characters of response
            return result
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            return f"Error generating response: {str(e)}"

    def get_model_name(self) -> str:
        """Returns the name of the model used by OpenAI."""
        return self.model

    def get_provider_name(self) -> str:
        """Returns the name of the LLM provider, which is 'OpenAI'."""
        return "OpenAI"
