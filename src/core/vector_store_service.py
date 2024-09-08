from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from cachetools import TTLCache, cached
from typing import List, Dict, Any
from src.config import Config
import warnings
import logging
import json
import os
import asyncio

import structlog
from src.utils.logging_configs import configure_logging

configure_logging()
logger = structlog.get_logger(__name__)

# Suppress the LangChainDeprecationWarning and huggingface warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
warnings.filterwarnings("ignore", category=DeprecationWarning)


class VectorStoreService:
    """Service for managing the creation, loading, and querying of the vector store."""

    def __init__(self, config: Config):
        """Initializes the VectorStoreService with configuration and embeddings."""
        self.config = config
        self.embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
        self.vector_store = None
        self.query_cache = TTLCache(maxsize=100, ttl=3600)

    async def vector_store_exists(self, path: str) -> bool:
        """Check if the vector store files exist at the given path."""
        index_file = os.path.join(path, "index.faiss")
        pkl_file = os.path.join(path, "index.pkl")
        return os.path.exists(index_file) and os.path.exists(pkl_file)

    async def is_loaded(self) -> bool:
        """Check if the vector store is loaded."""
        return (
            self.vector_store is not None
            and len(self.vector_store.index_to_docstore_id) > 0
        )

    async def create_vector_store(self, chunks_with_metadata: List[Dict[str, Any]]):
        """Creates a vector store from a list of text chunks with metadata."""
        documents = []
        for chunk in chunks_with_metadata:
            try:
                metadata = chunk.get("metadata", {})
                if metadata.get("type") == "text":
                    doc = Document(
                        page_content=chunk.get("content", ""),
                        metadata={"type": "text", "header": metadata.get("header", "")},
                    )
                elif metadata.get("type") == "table":
                    doc = Document(
                        page_content=chunk.get("content", "{}"),
                        metadata={
                            "type": "table",
                            "headers": metadata.get("headers", []),
                        },
                    )
                else:
                    logger.warning(
                        "Unknown chunk type", chunk_type=metadata.get("type")
                    )
                    continue
                documents.append(doc)
            except Exception as e:
                logger.error("Error processing chunk", error=str(e), chunk=chunk)

        if not documents:
            raise ValueError("No valid documents to create vector store")

        self.vector_store = await FAISS.afrom_documents(documents, self.embeddings)
        logger.info("Created vector store", document_count=len(documents))

    async def save_vector_store(self, path: str):
        """Saves the vector store to the specified local path."""
        if self.vector_store is None:
            raise ValueError("Vector store has not been created yet.")
        os.makedirs(path, exist_ok=True)
        await asyncio.to_thread(self.vector_store.save_local, path)
        logger.info("Vector store saved", path=path)

    async def load_vector_store(self, path: str):
        """Loads the vector store from the specified local path."""
        try:
            # Check if the vector store exists before trying to load it
            if not await self.vector_store_exists(path):
                raise FileNotFoundError(f"No vector store found at {path}")

            # Use asyncio.to_thread to call the synchronous FAISS load_local method asynchronously
            self.vector_store = await asyncio.to_thread(
                FAISS.load_local,
                path,
                self.embeddings,
                allow_dangerous_deserialization=True,
            )

            logger.info("Vector store loaded successfully", path=path)
        except Exception as e:
            logger.error("Error loading vector store", error=str(e))
            raise

    async def query(self, query_text: str) -> str:
        """Queries the vector store with a text input and returns the results."""
        if query_text in self.query_cache:
            logger.info("Query result found in cache", query_text=query_text)
            return self.query_cache[query_text]

        if self.vector_store is None:
            logger.error("Vector store not created or loaded")
            raise ValueError("Vector store has not been created or loaded yet.")

        logger.info("Querying vector store", query_text=query_text)
        results = await self.vector_store.asimilarity_search(query_text, k=3)
        processed_results = []

        for doc in results:
            try:
                if doc.metadata.get("type") == "text":
                    processed_results.append(
                        {
                            "type": "text",
                            "content": doc.page_content,
                            "header": doc.metadata.get("header", ""),
                        }
                    )
                elif doc.metadata.get("type") == "table":
                    processed_results.append(
                        {
                            "type": "table",
                            "headers": doc.metadata.get("headers", []),
                            "data": (
                                json.loads(doc.page_content)
                                if isinstance(doc.page_content, str)
                                else doc.page_content
                            ),
                        }
                    )
                else:
                    logger.warning(
                        "Unknown document type", doc_type=doc.metadata.get("type")
                    )
                    processed_results.append(
                        {"type": "unknown", "content": doc.page_content}
                    )
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON for document", metadata=doc.metadata)
            except Exception as e:
                logger.error("Error processing document", error=str(e))

        # Cache the query results
        self.query_cache[query_text] = json.dumps(processed_results)

        logger.debug("Processed query results", results=processed_results)
        return json.dumps(processed_results)

    async def load_or_create_vector_store(self, pdf_path: str):
        """Loads or creates a vector store from the PDF located at the given path."""
        vector_store_path = self.config.VECTOR_STORE_PATH
        if await self.vector_store_exists(vector_store_path):
            await self.load_vector_store(vector_store_path)
        else:
            from src.core.pdf_parser import PDFParser

            pdf_parser = PDFParser(pdf_path)
            sections_with_metadata = await pdf_parser.extract_sections_with_metadata()
            await self.create_vector_store(sections_with_metadata)
            await self.save_vector_store(vector_store_path)
        logger.info("Vector store loaded or created", pdf_path=pdf_path)
