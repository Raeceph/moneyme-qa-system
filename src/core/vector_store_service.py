from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from typing import List, Dict, Any
from src.config import Config
import warnings
import logging
import json
import os

logger = logging.getLogger(__name__)

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

    def vector_store_exists(self, path: str) -> bool:
        """Check if the vector store files exist at the given path."""
        index_file = os.path.join(path, "index.faiss")
        pkl_file = os.path.join(path, "index.pkl")
        return os.path.exists(index_file) and os.path.exists(pkl_file)

    def is_loaded(self) -> bool:
        """Check if the vector store is loaded."""
        return (
            self.vector_store is not None
            and len(self.vector_store.index_to_docstore_id) > 0
        )

    def create_vector_store(self, chunks_with_metadata: List[Dict[str, Any]]):
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
                            "years": metadata.get("years", []),
                        },
                    )
                else:
                    logger.warning(f"Unknown chunk type: {metadata.get('type')}")
                    continue
                documents.append(doc)
            except Exception as e:
                logger.error(f"Error processing chunk: {e}")
                logger.error(f"Problematic chunk: {chunk}")

        if not documents:
            raise ValueError("No valid documents to create vector store")

        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        logger.info(f"Created vector store with {len(documents)} documents")

    def save_vector_store(self, path: str):
        """Saves the vector store to the specified local path."""
        if self.vector_store is None:
            raise ValueError("Vector store has not been created yet.")
        os.makedirs(path, exist_ok=True)
        self.vector_store.save_local(path)
        logger.info(f"Vector store saved to {path}")

    def load_vector_store(self, path: str):
        """Loads the vector store from the specified local path."""
        try:
            if not self.vector_store_exists(path):
                raise FileNotFoundError(f"No vector store found at {path}")
            self.vector_store = FAISS.load_local(
                path, self.embeddings, allow_dangerous_deserialization=True
            )
            logger.info(f"Vector store loaded successfully from {path}")
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            raise

    def query(self, query_text: str) -> str:
        """Queries the vector store with a text input and returns the results."""
        if self.vector_store is None:
            raise ValueError("Vector store has not been created or loaded yet.")

        results = self.vector_store.similarity_search(query_text, k=3)
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
                    logger.warning(f"Unknown document type: {doc.metadata.get('type')}")
                    processed_results.append(
                        {"type": "unknown", "content": doc.page_content}
                    )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON for document: {doc.metadata}")
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")

        logger.debug(f"Processed query results: {processed_results}")
        return json.dumps(processed_results)

    def get_all_documents(self) -> List[str]:
        """Retrieves all documents stored in the vector store."""
        if self.vector_store is None:
            raise ValueError("Vector store has not been created or loaded yet.")

        # Return the list of file paths of all documents in the vector store
        documents = self.vector_store.get_all_documents()
        return [doc.metadata.get("file_path", "unknown") for doc in documents]

    def load_or_create_vector_store(self, pdf_path: str):
        """Loads or creates a vector store from the PDF located at the given path."""
        vector_store_path = self.config.VECTOR_STORE_PATH
        if self.vector_store_exists(vector_store_path):
            self.load_vector_store(vector_store_path)
        else:
            from src.core.pdf_parser import PDFParser

            pdf_parser = PDFParser(pdf_path)
            sections_with_metadata = pdf_parser.extract_sections_with_metadata()
            self.create_vector_store(sections_with_metadata)
            self.save_vector_store(vector_store_path)
        logger.info(f"Vector store loaded or created for {pdf_path}")