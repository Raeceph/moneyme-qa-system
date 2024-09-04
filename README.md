
# Project Description: Money ME REST API and CLI

### By: Raeceph Jude Sayson - AI Engineer Philippines 

---

This project was entirely built from scratch by me, showcasing my capability to design and implement an end-to-end LLM-based architecture. The project involves both a FastAPI-powered REST API and a CLI tool to interact with the Q&A system. The system was designed to handle financial documents by parsing, storing, and retrieving relevant data through vector embeddings, making it efficient even when working with smaller AI models.

The entire architecture was shaped around a sample financial PDF, with the goal of improving the results of document queries and enabling scalability for small models. Key features include dataset chunking using LangChain, and a "Chain of Thoughts" prompt engineering technique for improved question-answering quality. Additionally, I incorporated dynamic example prompts for better query structuring based on input data.

---

## File Descriptions:

- **gunicorn_conf.py**: 
    This is the Gunicorn configuration file that manages how the FastAPI server runs. It handles aspects like concurrency by setting the number of workers based on the CPU count, logging, and request timeouts. This ensures the API can handle multiple requests efficiently in a production environment.

- **src/ directory**:
    - **api/app.py**: The FastAPI application for handling incoming API requests. It defines multiple endpoints such as /query, /upload_pdf, and /chat, all of which manage the core question-answer system, PDF uploads, and chat interactions. Pydantic models are used here to ensure data validation and API input/output handling.
    - **cli_app.py**: Implements the CLI interface, enabling interaction with the QA system from the terminal. It allows users to upload PDFs, ask queries, and initiate chat-based conversations.
    - **config.py**: Stores environment-based settings and configuration parameters, including API keys and embedding model configurations.

- **src/core/ directory**:
    - **conversation_manager.py**: Manages conversations for ongoing chat sessions, ensuring continuity during multi-turn conversations.
    - **custom_text_splitter.py**: Extends LangChain’s RecursiveCharacterTextSplitter to break down text into chunks while preserving metadata like headers or source information.
    - **document_service.py**: Handles the document processing pipeline, including parsing PDFs and storing their contents as vector embeddings.
    - **llm_handler.py**: Integrates with the selected language model provider (OpenAI or Ollama) to generate responses to user queries.
    - **pdf_parser.py**: Extracts sections of text and tables from PDF files and processes them into smaller, manageable chunks.
    - **qa_system.py**: The core orchestration file that brings together document processing, vector store handling, and LLM querying.

- **src/llm_providers/ directory**:
    - **llm_factory.py**: Selects the appropriate LLM provider based on the configuration (OpenAI or Ollama).
    - **ollama_provider.py**: Manages sending queries to the Ollama API and returning the generated response.
    - **openai_provider.py**: Manages communication with OpenAI’s GPT models, sending user queries and returning responses.

- **src/utils/ directory**:
    - **error_handler.py**: Centralizes all error handling for the QA system.

---

## LangChain's Chunking Technique:
I leveraged LangChain’s RecursiveCharacterTextSplitter to chunk documents into smaller sections, each around 1000 characters in size with a 200-character overlap. This ensures that the vector embeddings capture sufficient context from the original documents, improving the accuracy of the answers retrieved during a query.

---

## Chain of Thoughts:
I implemented a "Chain of Thoughts" feature to improve the system’s reasoning and explanation capabilities. This technique adds an intermediate step between the question and the final answer, improving the quality and relevance of the answers.

---

## Tech Stack:
- **Python**: Backbone of the entire system, chosen for its simplicity and flexibility.
- **LangChain**: Used for managing interactions with LLMs and vector stores.
- **FAISS**: Used to create and manage vector stores for document embeddings.
- **Hugging Face Transformers**: Embedding model used is "paraphrase-MiniLM-L6-v2".
- **Ollama**: Integrated with the Mistral model to enable fast response times.
- **FastAPI**: Framework used for the REST API.
- **Pydantic**: Ensures type safety and consistency in API inputs and outputs.
- **Gunicorn**: Manages concurrency for the API server.
- **SQLite**: Used for storing metadata about processed documents.
- **pdfplumber**: Extracts structured information from PDFs.

---

## Best Practices:
- **Data Validation with Pydantic**: Strict validation for API inputs and outputs.
- **Separation of Concerns**: Each functionality is modular, ensuring easy maintenance and scalability.
- **Scalability in Design**: The system is built to scale as the dataset grows.
- **Entirely Custom-Built**: This system was built from scratch, with a focus on handling financial PDFs effectively.

Refer: for ollama models

https://ollama.com/library