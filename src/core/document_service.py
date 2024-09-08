import os
import logging
from typing import List
from src.config import Config
from src.core.document_tracker import DocumentTracker
from src.core.pdf_parser import PDFParser

import structlog
from src.utils.logging_configs import configure_logging
from src.utils.error_handler import DocumentProcessingError
import asyncio
import aiofiles

configure_logging()
logger = structlog.get_logger(__name__)


class DocumentService:
    """Service for managing document processing, tracking, and retrieval."""

    def __init__(self, config: Config):
        self.config = config
        self.document_tracker = DocumentTracker()
        # Call async init method explicitly
        asyncio.create_task(self.document_tracker.initialize())
        self.last_pdf_file = os.path.join(os.path.expanduser("~"), "last_pdf.txt")

    async def process_document(
        self, pdf_path: str, original_filename: str
    ) -> List[dict]:
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

        if await self.is_document_processed(pdf_path):
            logger.info("Document already processed", filename=original_filename)
            return []

        try:
            pdf_parser = PDFParser(pdf_path)
            sections_with_metadata = await pdf_parser.extract_sections_with_metadata()

            await self.document_tracker.add_document(pdf_path, original_filename)
            await self._save_last_pdf(pdf_path)

            logger.info("Document successfully processed", filename=original_filename)
            return sections_with_metadata
        except Exception as e:
            logger.error(
                "Error processing document", filename=original_filename, error=str(e)
            )
            raise

    async def list_documents(self) -> List[str]:
        """
        Retrieves the names of all processed documents.

        Returns:
            List[str]: A list of all processed document names.
        """
        try:
            return await self.document_tracker.get_all_documents()
        except Exception as e:
            logger.exception("Error retrieving document list")
            logger.error("Error details", error_message=str(e))
            raise DocumentProcessingError(f"Error retrieving document list: {str(e)}")

    async def get_last_processed_pdf(self) -> str:
        """
        Get the path of the last processed PDF.

        Returns:
            str: The path of the last processed PDF, or None if no PDF has been processed.
        """
        if os.path.exists(self.last_pdf_file):
            async with aiofiles.open(self.last_pdf_file, "r") as f:
                content = await f.read()  # Await the read operation first
                return content.strip()  # Now call strip on the result
        return None

    async def _save_last_pdf(self, pdf_path: str):
        """
        Save the path of the last processed PDF.

        Args:
            pdf_path (str): The path of the PDF to save.
        """
        async with aiofiles.open(self.last_pdf_file, "w") as f:
            await f.write(pdf_path)

    async def is_document_processed(self, pdf_path: str) -> bool:
        """
        Check if a document has already been processed.

        Args:
            pdf_path (str): The path of the PDF to check.

        Returns:
            bool: True if the document has been processed, False otherwise.
        """
        return await self.document_tracker.is_document_processed(pdf_path)

    async def add_document(self, pdf_path: str, original_filename: str):
        """
        Add a processed document to the tracker.

        Args:
            pdf_path (str): The path of the processed PDF.
            original_filename (str): The original filename of the PDF.
        """
        await self.document_tracker.add_document(pdf_path, original_filename)
        await self._save_last_pdf(pdf_path)
        logger.info("Document added to tracker", filename=original_filename)
