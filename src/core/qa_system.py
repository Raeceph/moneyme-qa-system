import logging
import uuid
import os
from src.config import Config
from src.core.vector_store_service import VectorStoreService
from src.core.document_service import DocumentService
from src.core.llm_handler import LLMHandler
from src.core.conversation_manager import ConversationManager
from src.utils.error_handler import handle_errors, QASystemError
from src.core.pdf_parser import PDFParser
import asyncio
import aiofiles

import structlog
from src.utils.logging_configs import configure_logging

configure_logging()


logger = structlog.get_logger(__name__)


class QASystem:
    """Handles the question-answer system, including document and conversation management."""

    def __init__(self, config: Config):
        """Initializes QASystem with config, vector store, document service, and LLM handler."""
        self.config = config
        self.vector_store_service = VectorStoreService(config)
        self.document_service = DocumentService(config)
        self.llm_handler = LLMHandler(config)
        self.conversation_manager = ConversationManager()

    @handle_errors
    async def process_single_query(self, question: str, pdf_path: str = None) -> dict:
        "Processes a single question query and returns the answer, source, and quality score."
        try:
            await self._ensure_vector_store_loaded(pdf_path)

            if not await self.vector_store_service.is_loaded():
                raise QASystemError(
                    "Vector store is not loaded. Please upload a PDF first."
                )

            context = await self.vector_store_service.query(question)
            logger.debug("Context retrieved", context=context)

            result = await self.llm_handler.generate_response(None, context, question)
            logger.debug("LLM response", result=result)

            if "answer" not in result:
                raise QASystemError("LLM response missing 'answer' key.")

            return {
                "answer": result["answer"],
                "source": result["source"],
                "quality_score": result["quality_score"],
            }

        except QASystemError as e:
            logger.error(f"QASystemError in process_single_query: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in process_single_query: {str(e)}")
            raise QASystemError(f"An unexpected error occurred: {str(e)}")

    @handle_errors
    async def process_chat_query(
        self, session_id: str, question: str, pdf_path: str = None
    ) -> dict:
        "Processes a chat query by managing conversation history and retrieving the answer."
        try:
            await self._ensure_vector_store_loaded(pdf_path)

            context = await self.vector_store_service.query(question)
            logger.debug("Context retrieved", context=context)

            if not session_id:
                session_id = str(uuid.uuid4())
            else:
                try:
                    uuid.UUID(session_id)
                except ValueError:
                    logger.error("Invalid session ID", session_id=session_id)
                    raise QASystemError("Invalid session ID format")

            result = await self.llm_handler.generate_response(
                session_id, context, question
            )
            logger.debug("LLM response", result=result)

            if "error" in result:
                raise QASystemError(result["error"])

            # Use synchronous calls for add_message, as they don't require await
            self.conversation_manager.add_message(session_id, "user", question)
            self.conversation_manager.add_message(
                session_id, "assistant", result["answer"]
            )

            conversation_history = self.conversation_manager.get_conversation_history(
                session_id
            )

            return {
                "session_id": session_id,
                "answer": result["answer"],
                "source": result["source"],
                "quality_score": result["quality_score"],
                "conversation_history": conversation_history,
            }
        except QASystemError as e:
            logger.error("QASystemError in process_chat_query", error=str(e))
            raise
        except Exception as e:
            logger.exception("Unexpected error in process_chat_query", error=str(e))
            raise QASystemError(f"An unexpected error occurred: {str(e)}")

    async def _ensure_vector_store_loaded(self, pdf_path: str = None):
        "Ensures the vector store is loaded, or creates a new one if necessary."
        if pdf_path:
            await self.load_or_create_vector_store(pdf_path, os.path.basename(pdf_path))
        elif not await self.vector_store_service.is_loaded():
            last_pdf = await self.document_service.get_last_processed_pdf()
            if last_pdf and await self.vector_store_service.vector_store_exists(
                self.config.VECTOR_STORE_PATH
            ):
                await self.vector_store_service.load_vector_store(
                    self.config.VECTOR_STORE_PATH
                )
            else:
                raise QASystemError("No vector store found. Please upload a PDF first.")

    @handle_errors
    async def load_or_create_vector_store(self, pdf_path: str, original_filename: str):
        "Loads an existing vector store or creates a new one from a given PDF."
        try:
            if not await self.vector_store_service.is_loaded():
                logger.info("Creating new vector store", pdf_path=pdf_path)
                pdf_parser = PDFParser(pdf_path)

                sections_with_metadata = (
                    await pdf_parser.extract_sections_with_metadata()
                )
                await self.vector_store_service.create_vector_store(
                    sections_with_metadata
                )
                await self.vector_store_service.save_vector_store(
                    self.config.VECTOR_STORE_PATH
                )
                await self.document_service.add_document(pdf_path, original_filename)
            else:
                logger.info("Loading existing vector store")
                await self.vector_store_service.load_vector_store(
                    self.config.VECTOR_STORE_PATH
                )

            logger.info("Vector store operation completed", pdf_path=pdf_path)
        except Exception as e:
            logger.exception("Error in load_or_create_vector_store", exc_info=True)
            logger.error("Error details", error_message=str(e))
            raise QASystemError(f"Error processing document: {str(e)}")

    async def list_documents(self) -> list:
        "Returns a list of all processed documents."
        try:
            return await self.document_service.list_documents()
        except Exception as e:
            logger.exception("Error in list_documents", error=str(e))
            raise QASystemError(f"Error listing documents: {str(e)}")

    @handle_errors
    async def get_session_info(self, session_id: str) -> dict:
        "Retrieves session information, including conversation history and message count."
        try:
            uuid.UUID(session_id)
            conversation_history = await self.conversation_manager.get_conversation(
                session_id
            )
            if not conversation_history:
                return None
            return {
                "session_id": session_id,
                "conversation_history": conversation_history,
                "message_count": len(conversation_history),
            }
        except ValueError:
            logger.error("Invalid session ID format", session_id=session_id)
            raise QASystemError("INVALID SESSION ID FORMAT OR DOES NOT EXIST")

    async def get_last_pdf(self) -> str:
        "Retrieves the path of the last processed PDF document."
        return await self.document_service.get_last_processed_pdf()
