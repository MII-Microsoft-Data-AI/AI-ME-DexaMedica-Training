"""
Document API Routes
==================

FastAPI routes for document upload and processing operations.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import document upload utilities
from document_upload_cli.utils import (
    file_eligible, ocr, chunk_text, embed, 
    upload_to_ai_search_studio, init_index, 
    upload_to_blob, init_container
)

# Initialize router
router = APIRouter(prefix="/documents", tags=["Documents"])

# Pydantic models
class DocumentUploadResponse(BaseModel):
    message: str
    file_name: str
    chunks_processed: int
    status: str

# Initialize search index and blob container for document uploads
try:
    init_index()
    init_container()
    logging.info("AI Search index and blob container initialized successfully")
except Exception as e:
    logging.warning(f"Failed to initialize AI Search index or blob container: {e}")
    logging.warning("Document upload functionality may not work properly")

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document for AI search indexing"""
    logging.info('FastAPI document upload endpoint processed a request.')
    
    # Environment check
    required_envs = [
        "DOCUMENT_INTELLIGENCE_ENDPOINT",
        "DOCUMENT_INTELLIGENCE_KEY", 
        "OPENAI_KEY",
        "OPENAI_ENDPOINT",
        "AI_SEARCH_KEY",
        "AI_SEARCH_ENDPOINT",
        "AI_SEARCH_INDEX",
        "BLOB_STORAGE_CONNECTION_STRING"
    ]
    missing = [env for env in required_envs if not os.getenv(env)]
    if missing:
        raise HTTPException(
            status_code=500, 
            detail=f"Missing required environment variables: {', '.join(missing)}"
        )
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        try:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            
            # Check if file is eligible for processing
            if not file_eligible(temp_file.name):
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type not supported. Supported types: PDF, DOCX, TXT"
                )
            
            logging.info(f"Processing file: {file.filename}")
            
            # Upload file to blob storage first
            blob_name, blob_url = upload_to_blob(temp_file.name)
            logging.info(f"Processing file: {file.filename} - Blob Upload Done")
            
            # Process the document
            ocr_result = ocr(temp_file.name)
            logging.info(f"Processing file: {file.filename} - OCR Done")
            
            chunks = chunk_text(ocr_result)
            logging.info(f"Processing file: {file.filename} - Chunking Done, {len(chunks)} chunks created")
            
            # Upload chunks with threading for better performance
            def upload_chunk(i, text_chunk):
                logging.info(f"Processing file: {file.filename} - Uploading chunk {i+1}/{len(chunks)}")
                embeddings = embed(text_chunk)
                upload_to_ai_search_studio(i, file.filename, text_chunk, embeddings, blob_url, blob_name)
                logging.info(f"Processing file: {file.filename} - Uploaded chunk {i+1}/{len(chunks)}")
                return i
            
            logging.info(f"Processing file: {file.filename} - Starting Upload")
            
            uploaded_chunks = 0
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(upload_chunk, i, text_chunk) for i, text_chunk in enumerate(chunks)]
                for future in as_completed(futures):
                    try:
                        future.result()
                        uploaded_chunks += 1
                    except Exception as e:
                        logging.error(f"Error uploading chunk: {e}")
                        # Continue processing other chunks
                        pass
            
            logging.info(f"Processing file: {file.filename} - Upload Complete")
            
            return DocumentUploadResponse(
                message=f"Successfully processed and uploaded document: {file.filename}",
                file_name=file.filename,
                chunks_processed=uploaded_chunks,
                status="success"
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logging.error(f"Error processing file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file: {str(e)}"
            )
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file.name)
            except OSError:
                pass

@router.get("/supported-types")
async def get_supported_document_types():
    """Get list of supported document types for upload"""
    logging.info('FastAPI supported document types endpoint processed a request.')
    
    supported_types = {
        "supported_extensions": [".pdf", ".docx", ".txt"],
        "supported_mime_types": [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
            "text/plain"
        ],
        "description": "Supported document formats for upload and processing"
    }
    
    return supported_types

@router.post("/init-index")
async def initialize_search_index():
    """Initialize the AI Search index and blob container for document storage"""
    logging.info('FastAPI init search index endpoint processed a request.')
    
    # Environment check
    required_envs = [
        "AI_SEARCH_KEY",
        "AI_SEARCH_ENDPOINT", 
        "AI_SEARCH_INDEX",
        "BLOB_STORAGE_CONNECTION_STRING"
    ]
    missing = [env for env in required_envs if not os.getenv(env)]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing required environment variables: {', '.join(missing)}"
        )
    
    try:
        init_index()
        init_container()
        return {"message": "AI Search index and blob container initialized successfully", "status": "success"}
    except Exception as e:
        logging.error(f"Error initializing search index: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error initializing search index: {str(e)}"
        )
