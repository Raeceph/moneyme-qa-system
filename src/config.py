import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # General LLM provider configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

    # OpenAI configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

    # Ollama configuration
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "mistral")

    # Embedding model configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "paraphrase-MiniLM-L6-v2")

    # Vector store configuration
    VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "/app/vector_store")
    UPLOAD_DIRECTORY = os.getenv("UPLOAD_DIRECTORY", "/app/uploads")

    # New configuration options
    CHAIN_OF_THOUGHTS_ENABLED = (
        os.getenv("CHAIN_OF_THOUGHTS_ENABLED", "False").lower() == "true"
    )
    CHAIN_OF_THOUGHTS_PROMPT = os.getenv("CHAIN_OF_THOUGHTS_PROMPT", "").split("|")
    EXAMPLE_PROMPTS = (
        os.getenv("EXAMPLE_PROMPTS", "").split("|")
        if os.getenv("EXAMPLE_PROMPTS")
        else []
    )

    UPLOAD_DIRECTORY = os.getenv("UPLOAD_DIRECTORY", "/app/uploads")

    def __init__(self):
        pass

# Create a global instance of the Config class
config = Config()