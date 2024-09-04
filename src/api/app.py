from fastapi import FastAPI, HTTPException, Header, Query, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, UUID4, validator
from typing import List, Optional
from src.core.qa_system import QASystem
from src.config import Config
from src.utils.error_handler import QASystemError
import os
import uuid
import logging
import tempfile


"""Create a FastAPI instance for the MONEYME AI Q&A API."""
app = FastAPI(title="MONEYME AI Q&A API")

"""Add CORS middleware to allow cross-origin requests from all origins."""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Request model for a single query containing a question."""

    question: str


class QueryResponse(BaseModel):
    """Response model for a query, returning the answer, source, and quality score."""

    answer: str
    source: str
    quality_score: int


class ChatExchange(BaseModel):
    """Model representing a single exchange in a chat session, with role and content."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Request model for a chat session, including an optional session ID and question."""

    session_id: Optional[str] = None
    question: str

    @validator("session_id")
    def validate_session_id(cls, v):
        """Validate the session ID, ensuring it's either None or a non-empty string."""
        if v in [None, "", "{{}}"] or (isinstance(v, str) and v.strip() == ""):
            return None
        return v


class ChatResponse(BaseModel):
    """Response model for a chat query, including session ID, answer, source, quality score, and conversation history."""

    session_id: UUID4
    answer: str
    source: str
    quality_score: int
    conversation_history: List[ChatExchange]


class ErrorResponse(BaseModel):
    """Model for an error response, containing a detailed error message."""

    detail: str


"""Load the configuration for the QA system & Initialize the QA system with the loaded configuration."""
config = Config()
qa_system = QASystem(config)

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    """Initialize the vector store on startup if it exists, loading the last processed PDF."""
    try:
        vector_store_path = config.VECTOR_STORE_PATH
        logger.info(f"Checking for vector store at path: {vector_store_path}")

        if qa_system.vector_store_service.vector_store_exists(vector_store_path):
            qa_system.vector_store_service.load_vector_store(vector_store_path)
            last_pdf = qa_system.get_last_pdf()
            logger.info(f"Vector store loaded. Last processed PDF: {last_pdf}")
            print(f"Vector store loaded. Last processed PDF: {last_pdf}")
        else:
            logger.info(f"No vector store found at {vector_store_path}")
            print(
                "No previous vector store found. The system is ready for a new PDF upload."
            )
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        print(f"Error during startup: {str(e)}")


@app.post(
    "/query",
    response_model=QueryResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def query(request: QueryRequest):
    """Process a single query request and return the answer, source, and quality score."""
    try:
        # Check if vector store exists
        if not qa_system.vector_store_service.is_loaded():
            raise HTTPException(
                status_code=400,
                detail="No PDF has been processed yet. Please upload a PDF first.",
            )

        result = qa_system.process_single_query(request.question)
        return QueryResponse(
            answer=result["answer"],
            source=result["source"],
            quality_score=result["quality_score"],
        )
    except HTTPException:
        raise
    except QASystemError as e:
        logger.error(f"QASystemError in query: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred. Please try again later.",
        )


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def chat(request: ChatRequest):
    """Process a chat query and return the session ID, answer, source, quality score, and conversation history."""
    try:
        # Check if vector store exists
        if not qa_system.vector_store_service.is_loaded():
            raise HTTPException(
                status_code=400,
                detail="No PDF has been processed yet. Please upload a PDF first.",
            )

        result = qa_system.process_chat_query(request.session_id, request.question)
        return ChatResponse(
            session_id=result["session_id"],
            answer=result["answer"],
            source=result["source"],
            quality_score=result["quality_score"],
            conversation_history=result["conversation_history"],
        )
    except HTTPException:
        raise
    except QASystemError as e:
        logger.error(f"QASystemError in chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred. Please try again later.",
        )


@app.post(
    "/upload_pdf",
    responses={
        200: {"model": dict},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file, adding it to the vector store."""
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

        # Create uploads directory if it doesn't exist
        os.makedirs(config.UPLOAD_DIRECTORY, exist_ok=True)

        file_path = os.path.join(config.UPLOAD_DIRECTORY, file.filename)

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        qa_system.load_or_create_vector_store(file_path, file.filename)
        return {
            "message": f"PDF processed and added to the vector store: {file.filename}"
        }

    except QASystemError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing PDF")


@app.get(
    "/list_documents", responses={200: {"model": dict}, 500: {"model": ErrorResponse}}
)
async def list_documents():
    """List all processed documents from the vector store."""
    try:
        documents = qa_system.list_documents()
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing documents")


@app.post(
    "/clear_chat",
    responses={
        200: {"model": dict},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def clear_chat(
    x_session_id: str = Header(..., description="Session ID to clear")
):
    """Clear conversation history for the specified session ID."""
    try:
        qa_system.clear_conversation(x_session_id)
        return {"message": f"Conversation cleared for session {x_session_id}"}
    except QASystemError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error clearing chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Error clearing chat")


@app.get(
    "/session_info",
    responses={
        200: {"model": dict},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def get_session_info(
    x_session_id: str = Header(..., description="Session ID to get info for")
):
    """Retrieve session information for the specified session ID."""
    try:
        info = qa_system.get_session_info(x_session_id)
        if info is None:
            raise HTTPException(status_code=400, detail="Session not found")
        return info
    except QASystemError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting session info")


@app.get("/", responses={200: {"model": dict}})
async def root():
    """Return a welcome message for the MONEYME AI Q&A API."""
    return {"message": "Welcome to the MONEYME AI Q&A API"}
