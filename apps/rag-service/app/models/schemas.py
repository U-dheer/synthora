from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    URL = "url"


class QueryType(str, Enum):
    """Query type for different workflows."""
    GENERAL = "general"
    DOCUMENT_SPECIFIC = "document_specific"


# Request Models
class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    filename: str
    content_type: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class URLAddRequest(BaseModel):
    """Request model for adding URL to knowledge base."""
    url: HttpUrl
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    """Request model for general query."""
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class DocumentSpecificQueryRequest(BaseModel):
    """Request model for document-specific query."""
    question: str = Field(..., min_length=1, max_length=2000)
    document_id: str
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


# Response Models
class DocumentChunk(BaseModel):
    """Model for document chunk with metadata."""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievedContext(BaseModel):
    """Model for retrieved context from vector search."""
    chunk: DocumentChunk
    score: float
    

class LLMResponse(BaseModel):
    """Model for individual LLM response."""
    service: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for query."""
    answer: str
    query_type: QueryType
    retrieved_contexts: List[RetrievedContext]
    llm_responses: Optional[List[LLMResponse]] = None
    processing_time_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    no_kb_data: Optional[bool] = None  # Flag to indicate no knowledge base data


class DocumentResponse(BaseModel):
    """Response model for document operations."""
    document_id: str
    filename: str
    document_type: DocumentType
    chunks_count: int
    upload_timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentResponse]
    total_count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    vector_db_type: str
    embedding_type: str
    gateway_url: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Gateway Communication Models
class GatewayLLMRequest(BaseModel):
    """Request model for LLM services via gateway."""
    prompt: str
    context: Optional[str] = None
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7


class GatewaySummarizerRequest(BaseModel):
    """Request model for summarizer service via gateway."""
    responses: List[str]
    original_question: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
