from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List
import logging

from app.config import Settings, get_settings
from app.models.schemas import (
    URLAddRequest,
    DocumentResponse,
    DocumentListResponse,
    DocumentType,
    ErrorResponse
)
from app.dependencies import get_document_processor_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag/documents", tags=["documents"])


def get_dependencies(settings: Settings = Depends(get_settings)):
    """Get service dependencies."""
    document_processor = get_document_processor_service(settings)
    return document_processor


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_processor = Depends(get_dependencies)
):
    """
    Upload and process a document (PDF, DOCX, or TXT).
    
    The document will be:
    1. Parsed to extract text
    2. Chunked into smaller pieces
    3. Embedded using the configured embedding model
    4. Stored in the vector database
    """
    try:
        logger.info(f"Received file upload: {file.filename}")
        
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Read file content
        content = await file.read()
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Process document
        document = await document_processor.process_file(
            filename=file.filename,
            file_content=content,
            metadata={"content_type": file.content_type}
        )
        
        # Build response
        return DocumentResponse(
            document_id=document.document_id,
            filename=document.filename,
            document_type=DocumentType(document.document_type),
            chunks_count=len(document.chunks),
            upload_timestamp=document.upload_timestamp,
            metadata=document.metadata
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post("/add-url", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def add_url(
    request: URLAddRequest,
    document_processor = Depends(get_dependencies)
):
    """
    Add a website URL to the knowledge base.
    
    The URL will be:
    1. Scraped to extract text content
    2. Chunked into smaller pieces
    3. Embedded using the configured embedding model
    4. Stored in the vector database
    """
    try:
        logger.info(f"Received URL: {request.url}")
        
        # Process URL
        document = await document_processor.process_url(
            url=str(request.url),
            metadata=request.metadata or {}
        )
        
        # Build response
        return DocumentResponse(
            document_id=document.document_id,
            filename=document.filename,
            document_type=DocumentType.URL,
            chunks_count=len(document.chunks),
            upload_timestamp=document.upload_timestamp,
            metadata=document.metadata
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process URL: {str(e)}"
        )


@router.post("/text", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def add_text(
    request: dict,
    document_processor = Depends(get_dependencies)
):
    """
    Add plain text content directly to the knowledge base.
    
    Expects JSON body with:
    - content: The text content to store
    - metadata: Optional metadata (source, question, etc.)
    """
    try:
        content = request.get("content", "")
        metadata = request.get("metadata", {})
        
        if not content:
            raise ValueError("Content cannot be empty")
        
        logger.info(f"Received text content ({len(content)} chars) with metadata: {metadata}")
        
        # Process text directly
        document = await document_processor.process_text(
            content=content,
            metadata=metadata
        )
        
        # Build response
        return DocumentResponse(
            document_id=document.document_id,
            filename=metadata.get("source", "text_content"),
            document_type=DocumentType.TXT,
            chunks_count=len(document.chunks),
            upload_timestamp=document.upload_timestamp,
            metadata=document.metadata
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process text: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    document_processor = Depends(get_dependencies)
):
    """
    Remove a document from the knowledge base.
    
    This will delete all chunks and embeddings associated with the document.
    """
    try:
        logger.info(f"Deleting document: {document_id}")
        
        result = await document_processor.delete_document(document_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        return {
            "message": f"Document {document_id} deleted successfully",
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    document_processor = Depends(get_dependencies)
):
    """
    List all documents in the knowledge base.
    
    Returns metadata for all documents including:
    - Document ID
    - Filename
    - Document type
    - Number of chunks
    - Upload timestamp
    """
    try:
        logger.info("Listing all documents")
        
        documents_data = document_processor.get_all_documents()
        
        # Convert to response models
        documents = [
            DocumentResponse(
                document_id=doc["document_id"],
                filename=doc["filename"],
                document_type=DocumentType(doc.get("document_type", "unknown")),
                chunks_count=doc.get("chunks_count", 0),
                upload_timestamp=doc.get("upload_timestamp", "unknown"),
                metadata=doc.get("metadata", {})
            )
            for doc in documents_data
        ]
        
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )
