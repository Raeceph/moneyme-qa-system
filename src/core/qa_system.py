import logging
import uuid
import os
from src.config import Config
from src.core.vector_store_service import VectorStoreService
from src.core.document_service import DocumentService
from src.core.llm_handler import LLMHandler
from src.core.conversation_manager import ConversationManager
from src.utils.error_handler import handle_errors, QASystemError

logger = logging.getLogger(__name__)


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
    def process_single_query(self, question: str, pdf_path: str = None) -> dict:
        """Processes a single query using the vector store and generates a response."""
        try:
            if pdf_path:
                self.load_or_create_vector_store(pdf_path)
            elif not self.vector_store_service.is_loaded():
                last_pdf = self.document_service.get_last_processed_pdf()
                if last_pdf:
                    self.load_or_create_vector_store(last_pdf)
                else:
                    raise QASystemError(
                        "No PDF has been processed yet. Please upload a PDF first."
                    )

            if not self.vector_store_service.is_loaded():
                raise QASystemError(
                    "Vector store is not loaded. Please upload a PDF first."
                )

            context = self.vector_store_service.query(question)
            logger.debug(f"Context retrieved: {context}")

            result = self.llm_handler.generate_response(None, context, question)
            logger.debug(f"LLM response: {result}")

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
    def process_chat_query(
        self, session_id: str, question: str, pdf_path: str = None
    ) -> dict:
        """Processes a chat query, manages conversation, and generates a response."""
        try:
            self._ensure_vector_store_loaded(pdf_path)

            context = self.vector_store_service.query(question)
            logger.debug(f"Context retrieved: {context}")

            if not session_id:
                session_id = str(uuid.uuid4())
            else:
                try:
                    uuid.UUID(session_id)
                except ValueError:
                    logger.error(f"Invalid session ID: {session_id}")
                    raise QASystemError("Invalid session ID format")

            result = self.llm_handler.generate_response(session_id, context, question)
            logger.debug(f"LLM response: {result}")

            if "error" in result:
                raise QASystemError(result["error"])

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
            logger.error(f"QASystemError in process_chat_query: {str(e)}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in process_chat_query: {str(e)}")
            raise QASystemError(f"An unexpected error occurred: {str(e)}")

    def _ensure_vector_store_loaded(self, pdf_path: str = None):
        """Ensures that the vector store is loaded, loading or creating it if necessary."""
        if pdf_path:
            self.load_or_create_vector_store(pdf_path)
        elif not self.vector_store_service.is_loaded():
            last_pdf = self.document_service.get_last_processed_pdf()
            if last_pdf and self.vector_store_service.vector_store_exists(
                self.config.VECTOR_STORE_PATH
            ):
                self.vector_store_service.load_vector_store(
                    self.config.VECTOR_STORE_PATH
                )
            else:
                raise QASystemError("No vector store found. Please upload a PDF first.")

    @handle_errors
    def load_or_create_vector_store(self, pdf_path: str, original_filename: str):
        """Loads or creates a vector store from a PDF and processes the document if necessary."""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            if not self.document_service.is_document_processed(pdf_path):
                logger.info(f"Processing new document: {original_filename}")
                sections_with_metadata = self.document_service.process_document(
                    pdf_path, original_filename
                )
                self.vector_store_service.create_vector_store(sections_with_metadata)
                self.vector_store_service.save_vector_store(
                    self.config.VECTOR_STORE_PATH
                )
                logger.info(
                    f"Document successfully uploaded and processed: {original_filename}"
                )
            else:
                logger.info(
                    f"Document already processed, loading existing vector store: {original_filename}"
                )
                self.vector_store_service.load_vector_store(
                    self.config.VECTOR_STORE_PATH
                )
        except Exception as e:
            logger.error(f"Error in load_or_create_vector_store: {str(e)}")
            raise

    @handle_errors
    def list_documents(self) -> list:
        """Lists all processed documents available in the system."""
        return self.document_service.list_documents()

    @handle_errors
    def clear_conversation(self, session_id: str):
        """Clears the conversation history for a given session ID.-> not used but good to have for scalability"""
        try:
            uuid.UUID(session_id)
            if not self.conversation_manager.get_conversation(session_id):
                raise QASystemError(f"Session {session_id} not found")
            self.conversation_manager.clear_conversation(session_id)
            logger.info(f"Cleared conversation history for session {session_id}")
        except ValueError as e:
            logger.error(f"Error clearing conversation: {str(e)}")
            raise

    @handle_errors
    def get_session_info(self, session_id: str) -> dict:
        """Retrieves session information, including conversation history and message count."""
        try:
            uuid.UUID(session_id)
            conversation_history = self.conversation_manager.get_conversation(
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
            logger.error(f"Invalid session ID format: {session_id}")
            raise QASystemError("INVALID SESSION ID FORMAT OR DOES NOT EXIST")

    def get_last_pdf(self) -> str:
        """Returns the file path of the last processed PDF."""
        return self.document_service.get_last_processed_pdf()
