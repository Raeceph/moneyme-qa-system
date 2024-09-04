import argparse
import sys
import os
from src.config import Config
from src.core.qa_system import QASystem
from src.utils.error_handler import QASystemError
import uuid
import shutil

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

def main():
    """Main function for handling CLI input and managing QA system operations."""

    config = Config()
    qa_system = QASystem(config)

    os.makedirs(config.UPLOAD_DIRECTORY, exist_ok=True)
    os.makedirs(config.VECTOR_STORE_PATH, exist_ok=True)

    # Attempt to load existing vector store on startup
    try:
        last_pdf = qa_system.get_last_pdf()
        if last_pdf and qa_system.vector_store_service.vector_store_exists(
            config.VECTOR_STORE_PATH
        ):
            qa_system.vector_store_service.load_vector_store(config.VECTOR_STORE_PATH)
            print(f"Loaded existing vector store. Last processed PDF: {last_pdf}")
        else:
            print("No existing vector store found. Please upload a PDF.")
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
        if not args.pdf:
            print("Error: --pdf is required for upload mode")
            sys.exit(1)
        
        # Handle file paths for Docker environment
        if args.pdf.startswith('/external_pdfs/'):
            pdf_path = args.pdf
        else:
            pdf_path = os.path.join('/external_pdfs', args.pdf)
        
        if not os.path.exists(pdf_path):
            print(f"Error: File not found: {pdf_path}")
            sys.exit(1)
        
        try:
            original_filename = os.path.basename(pdf_path)
            destination_path = os.path.join(config.UPLOAD_DIRECTORY, original_filename)
            shutil.copy2(pdf_path, destination_path)
            qa_system.load_or_create_vector_store(destination_path, original_filename)
            print(f"Document successfully uploaded and processed: {original_filename}")
        except QASystemError as e:
            print(f"Error uploading document: {str(e)}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            sys.exit(1)

    elif args.mode == "query":
        if not args.question:
            print("Error: --question is required for query mode")
            sys.exit(1)

        try:
            if not qa_system.vector_store_service.is_loaded():
                print(
                    "Error: No PDF has been processed yet. Please upload a PDF first."
                )
                sys.exit(1)
            result = qa_system.process_single_query(args.question)
            print(f"Answer: {result['answer']}")
            print(f"Source: {result['source']}")
            print(f"Quality Score: {result['quality_score']}")
        except QASystemError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

    elif args.mode == "chat":
        try:
            if not qa_system.vector_store_service.is_loaded():
                print(
                    "Error: No PDF has been processed yet. Please upload a PDF first."
                )
                sys.exit(1)
            session_id = str(uuid.uuid4())
            print("Chat mode. Type 'exit' to end the conversation.")
            while True:
                question = input("You: ")
                if question.lower() == "exit":
                    break
                try:
                    result = qa_system.process_chat_query(session_id, question)
                    print(f"AI: {result['answer']}")
                except QASystemError as e:
                    print(f"Error: {str(e)}")
                    break
        except QASystemError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

    elif args.mode == "list":
        try:
            documents = qa_system.list_documents()
            print("Processed documents:")
            for doc in documents:
                print(doc)
        except QASystemError as e:
            print(f"Error listing documents: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()