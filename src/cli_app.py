import argparse
import sys
import os
import uuid
import shutil
import asyncio
from src.config import Config
from src.core.qa_system import QASystem
from src.utils.error_handler import QASystemError
import logging 

# Disable all logging for CLI
import logging
logging.disable(logging.CRITICAL)

# Add the project root directory to the sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

async def handle_upload_mode(qa_system, args, config):
    if not args.pdf:
        print("Error: --pdf is required for upload mode")
        sys.exit(1)

    # Handle file paths for Docker environment or local
    pdf_path = args.pdf

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    try:
        original_filename = os.path.basename(pdf_path)
        destination_path = os.path.join(config.UPLOAD_DIRECTORY, original_filename)
        shutil.copy2(pdf_path, destination_path)
        await qa_system.load_or_create_vector_store(destination_path, original_filename)
        print(f"Document successfully uploaded and processed: {original_filename}")
    except QASystemError as e:
        print(f"Error uploading document: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

async def handle_query_mode(qa_system, args):
    if not args.question:
        print("Error: --question is required for query mode")
        sys.exit(1)

    try:
        if not await qa_system.vector_store_service.is_loaded():
            print("Error: No vector store has been processed yet. Please upload a PDF first.")
            sys.exit(1)
        result = await qa_system.process_single_query(args.question)
        print(f"Answer: {result['answer']}")
        print(f"Source: {result['source']}")
        print(f"Quality Score: {result['quality_score']}")
    except QASystemError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

async def handle_chat_mode(qa_system):
    try:
        if not await qa_system.vector_store_service.is_loaded():
            print("Error: No vector store has been processed yet. Please upload a PDF first.")
            sys.exit(1)
        session_id = str(uuid.uuid4())
        print("Chat mode. Type 'exit' to end the conversation.")
        while True:
            question = input("You: ")
            if question.lower() == "exit":
                break
            try:
                result = await qa_system.process_chat_query(session_id, question)
                print(f"AI: {result['answer']}")
            except QASystemError as e:
                print(f"Error: {str(e)}")
                break
    except QASystemError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

async def handle_list_mode(qa_system):
    try:
        documents = await qa_system.list_documents()
        print("Processed documents:")
        for doc in documents:
            print(doc)
    except QASystemError as e:
        print(f"Error listing documents: {str(e)}")
        sys.exit(1)

async def async_main():
    """Main function for handling CLI input and managing QA system operations."""
    config = Config()
    qa_system = QASystem(config)

    os.makedirs(config.UPLOAD_DIRECTORY, exist_ok=True)
    os.makedirs(config.VECTOR_STORE_PATH, exist_ok=True)

    # Check if the vector store exists
    try:
        if await qa_system.vector_store_service.vector_store_exists(config.VECTOR_STORE_PATH):
            await qa_system.vector_store_service.load_vector_store(config.VECTOR_STORE_PATH)
            print(f"Loaded existing vector store from: {config.VECTOR_STORE_PATH}")
        else:
            print("No existing vector store found. Please upload a PDF to create a vector store.")
    except Exception as e:
        print(f"Error loading vector store: {str(e)}")

    parser = argparse.ArgumentParser(description="QA System CLI")
    parser.add_argument(
        "--mode",
        choices=["query", "chat", "list", "upload"],
        required=True,
        help="Operation mode",
    )
    parser.add_argument("--pdf", help="Path to the PDF file (required for upload mode)")
    parser.add_argument("--question", help="Question to ask (for query mode)")
    args = parser.parse_args()

    if args.mode == "upload":
        await handle_upload_mode(qa_system, args, config)
    elif args.mode == "query":
        await handle_query_mode(qa_system, args)
    elif args.mode == "chat":
        await handle_chat_mode(qa_system)
    elif args.mode == "list":
        await handle_list_mode(qa_system)

def main():
    """Wrapper for running the async main."""
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
