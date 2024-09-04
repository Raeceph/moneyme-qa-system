# src/core/custom_text_splitter.py

from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any


class MetadataTextSplitter(RecursiveCharacterTextSplitter):
    """A custom text splitter that splits text into chunks while preserving associated metadata."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the MetadataTextSplitter with chunk size and overlap.

        Args:
            chunk_size (int): The size of each text chunk.
            chunk_overlap (int): The overlap between consecutive chunks.
        """
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def split_text_with_metadata(
        self, text: str, metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks and associate each chunk with metadata.

        Args:
            text (str): The input text to split.
            metadata (Dict[str, Any]): Metadata to associate with each chunk of text.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary contains
                                  a chunk of text and its associated metadata.
        """
        chunks = []
        split_texts = self.split_text(text)
        for chunk in split_texts:
            chunks.append({"content": chunk, "metadata": metadata.copy()})
        return chunks
