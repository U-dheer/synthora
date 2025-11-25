# Make models package importable
from .schemas import (
    DocumentType,
    QueryType,
    DocumentUploadRequest,
    URLAddRequest,
    QueryRequest,
    DocumentSpecificQueryRequest,
    QueryResponse,
    DocumentResponse,
    DocumentListResponse,
    HealthResponse,
    ErrorResponse,
    GatewayLLMRequest,
    GatewaySummarizerRequest,
)

from .document import Document, DocumentChunk, QueryResult

__all__ = [
    "DocumentType",
    "QueryType",
    "DocumentUploadRequest",
    "URLAddRequest",
    "QueryRequest",
    "DocumentSpecificQueryRequest",
    "QueryResponse",
    "DocumentResponse",
    "DocumentListResponse",
    "HealthResponse",
    "ErrorResponse",
    "GatewayLLMRequest",
    "GatewaySummarizerRequest",
    "Document",
    "DocumentChunk",
    "QueryResult",
]
