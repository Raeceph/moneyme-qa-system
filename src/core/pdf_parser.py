import pdfplumber
import json
from typing import List, Dict, Any
from src.core.custom_text_splitter import MetadataTextSplitter
import structlog
from src.utils.logging_configs import configure_logging
import asyncio

configure_logging()
logger = structlog.get_logger(__name__)


class PDFParser:
    """Parses PDF files, extracting content and metadata."""

    def __init__(self, pdf_path: str):
        """Initializes the PDFParser with the path to the PDF file."""
        self.pdf_path = pdf_path
        self.headers = []

    async def extract_content(self) -> List[Dict[str, Any]]:
        """Extracts content from the PDF, including text and tables."""
        try:
            content = await asyncio.to_thread(self._extract_content_sync)
            return content
        except Exception as e:
            logger.error(
                "Error extracting content from PDF",
                error=str(e),
                pdf_path=self.pdf_path,
            )
            raise

    def _extract_content_sync(self) -> List[Dict[str, Any]]:
        """Synchronous method to extract content from the PDF."""
        content = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                page_content = self._process_page(page)
                content.extend(page_content)
        return content

    def _process_page(self, page) -> List[Dict[str, Any]]:
        """Processes a single PDF page to extract text and tables."""
        page_content = []
        text = page.extract_text()
        tables = page.extract_tables()

        # Process text content
        lines = text.split("\n")
        current_header = ""
        current_text = []

        for line in lines:
            if self._is_header(line):
                if current_text:
                    page_content.append(
                        {
                            "type": "text",
                            "header": current_header,
                            "content": "\n".join(current_text),
                        }
                    )
                    current_text = []
                current_header = line
                self.headers.append(line)
            else:
                current_text.append(line)

        # Add any remaining text
        if current_text:
            page_content.append(
                {
                    "type": "text",
                    "header": current_header,
                    "content": "\n".join(current_text),
                }
            )

        # Process tables
        for table in tables:
            table_dict = self._process_table(table)
            page_content.append(table_dict)

        return page_content

    def _is_header(self, line: str) -> bool:
        """Determines if a line of text is a header based on format."""
        return line.isupper() or line.strip().split(".")[0].isdigit()

    def _process_table(self, table: List[List[str]]) -> Dict[str, Any]:
        """Processes a table from the PDF and formats it as a dictionary."""
        headers = table[0]
        data = table[1:]
        return {"type": "table", "headers": headers, "data": data}

    async def extract_sections_with_metadata(self) -> List[Dict[str, Any]]:
        """Extracts sections of text and tables, splitting them into manageable chunks with metadata."""
        try:
            content = await self.extract_content()
            chunks = []

            text_splitter = MetadataTextSplitter(chunk_size=1000, chunk_overlap=200)

            for item in content:
                if item["type"] == "text":
                    text_chunks = text_splitter.split_text_with_metadata(
                        item["content"], {"type": "text", "header": item["header"]}
                    )
                    chunks.extend(text_chunks)
                elif item["type"] == "table":
                    # Store the entire table as a single chunk
                    chunks.append(
                        {
                            "content": json.dumps(item["data"]),
                            "metadata": {"type": "table", "headers": item["headers"]},
                        }
                    )

            return chunks
        except Exception as e:
            logger.error(
                "Error extracting sections with metadata",
                error=str(e),
                pdf_path=self.pdf_path,
            )
            raise
