import logging
from functools import wraps

logger = logging.getLogger(__name__)


class QASystemError(Exception):
    """Base exception class for QA System errors."""

    pass


class InvalidSessionError(QASystemError):
    """Raised when an invalid session is encountered."""

    pass


class DocumentProcessingError(QASystemError):
    """Raised when there's an error processing a document."""

    pass


class VectorStoreError(QASystemError):
    """Raised when there's an error with the vector store operations."""

    pass


class LLMProviderError(QASystemError):
    """Raised when there's an error with the LLM provider."""

    pass


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InvalidSessionError as e:
            logger.error(f"Invalid session error in {func.__name__}: {str(e)}")
            return {"error": str(e), "type": "InvalidSessionError"}
        except DocumentProcessingError as e:
            logger.error(f"Document processing error in {func.__name__}: {str(e)}")
            return {"error": str(e), "type": "DocumentProcessingError"}
        except VectorStoreError as e:
            logger.error(f"Vector store error in {func.__name__}: {str(e)}")
            return {"error": str(e), "type": "VectorStoreError"}
        except LLMProviderError as e:
            logger.error(f"LLM provider error in {func.__name__}: {str(e)}")
            return {"error": str(e), "type": "LLMProviderError"}
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "type": "UnexpectedError",
            }

    return wrapper
