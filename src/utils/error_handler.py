import logging
from functools import wraps
import functools
import aiofiles

logger = logging.getLogger(__name__)


class QASystemError(Exception):
    """Base exception class for QA System errors."""

    pass


class VectorStoreError(QASystemError):
    """Raised when there's an error with vector store operations."""

    pass


class DocumentProcessingError(QASystemError):
    """Raised when there's an error processing a document."""

    pass


class LLMError(QASystemError):
    """Raised when there's an error with the Language Model."""

    pass


class InvalidInputError(QASystemError):
    """Raised when the input to a function is invalid."""

    pass


class ConfigurationError(QASystemError):
    """Raised when there's an error in the system configuration."""

    pass


import structlog

logger = structlog.get_logger(__name__)


def handle_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except VectorStoreError as e:
            logger.error("Vector store error", error_message=str(e))
            raise
        except DocumentProcessingError as e:
            logger.error("Document processing error", error_message=str(e))
            raise
        except LLMError as e:
            logger.error("Language Model error", error_message=str(e))
            raise
        except InvalidInputError as e:
            logger.error("Invalid input error", error_message=str(e))
            raise
        except ConfigurationError as e:
            logger.error("Configuration error", error_message=str(e))
            raise
        except Exception as e:
            logger.exception("Unexpected error", error_message=str(e))
            raise QASystemError(f"An unexpected error occurred: {str(e)}")

    return wrapper
