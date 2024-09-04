import os
import logging
from typing import List
from src.config import Config
from src.core.document_tracker import DocumentTracker
from src.core.pdf_parser import PDFParser

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing document processing, tracking, and retrieval."""

    def __init__(self, config: Config):
        """
        Initialize the DocumentService with configuration and a document tracker.

        Args:
            config (Config): The configuration object.
        """
        self.config = config
        self.document_tracker = DocumentTracker()
        self.last_pdf_file = "/app/vector_store/last_pdf.txt"

    def process_document(self, pdf_path: str, original_filename: str) -> List[dict]:
        """
        Process a PDF document, extract its sections, and track it.

        Args:
            pdf_path (str): The file path of the PDF.
            original_filename (str): The original filename of the PDF.

        Returns:
            List[dict]: A list of sections with metadata extracted from the PDF.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.lower().endswith(".pdf"):
            raise ValueError("The file must be a PDF")

        if self.document_tracker.is_document_processed(pdf_path):
            logger.info(f"Document already processed: {original_filename}")
            return []

        try:
            pdf_parser = PDFParser(pdf_path)
            sections_with_metadata = pdf_parser.extract_sections_with_metadata()

            self.document_tracker.add_document(pdf_path, original_filename)
            self._save_last_pdf(pdf_path)

            logger.info(f"Document successfully processed: {original_filename}")
            return sections_with_metadata
        except Exception as e:
            logger.error(f"Error processing document {original_filename}: {str(e)}")
            raise

    def list_documents(self) -> List[str]:
        """
        List all processed documents.

        Returns:
            List[str]: A list of all processed document paths.
        """
        return self.document_tracker.get_all_documents()

    def get_last_processed_pdf(self) -> str:
        """
        Get the path of the last processed PDF.
        """
        if os.path.exists(self.last_pdf_file):
            with open(self.last_pdf_file, "r") as f:
                return f.read().strip()
        return None

    def _save_last_pdf(self, pdf_path: str):
        """
        Save the path of the last processed PDF.
        """
        with open(self.last_pdf_file, "w") as f:
            f.write(pdf_path)

    def is_document_processed(self, pdf_path: str) -> bool:
        """
        Check if a document has already been processed.
        """
        return self.document_tracker.is_document_processed(pdf_path)

    def get_document_content(self, pdf_path: str) -> List[dict]:
        """
        Get the content of a processed document. If not processed, process it first.
        """
        if not self.is_document_processed(pdf_path):
            return self.process_document(pdf_path)

        # If the document is already processed, you might want to retrieve its content
        # from a storage system. For now, we'll just re-process it.
        pdf_parser = PDFParser(pdf_path)
        return pdf_parser.extract_sections_with_metadata()

    def remove_document(self, pdf_path: str):
        """
        Remove a document from the processed list.
        """
        self.document_tracker.remove_document(pdf_path)
        logger.info(f"Document removed from processed list: {pdf_path}")

        # If this was the last processed PDF, clear that record
        last_pdf = self.get_last_processed_pdf()
        if last_pdf == pdf_path:
            os.remove(self.last_pdf_file)
