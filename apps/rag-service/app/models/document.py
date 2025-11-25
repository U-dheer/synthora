from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with embeddings."""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "embedding": self.embedding,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentChunk":
        """Create from dictionary."""
        return cls(
            chunk_id=data["chunk_id"],
            document_id=data["document_id"],
            content=data["content"],
            chunk_index=data["chunk_index"],
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {})
        )


@dataclass
class Document:
    """Represents a document in the knowledge base."""
    document_id: str
    filename: str
    document_type: str
    content: str
    chunks: List[DocumentChunk] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    upload_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create_new(
        cls,
        filename: str,
        document_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Document":
        """Create a new document with generated ID."""
        return cls(
            document_id=str(uuid.uuid4()),
            filename=filename,
            document_type=document_type,
            content=content,
            metadata=metadata or {},
            chunks=[],
            upload_timestamp=datetime.utcnow()
        )
    
    def add_chunk(self, content: str, chunk_index: int, embedding: Optional[List[float]] = None):
        """Add a chunk to the document."""
        chunk = DocumentChunk(
            chunk_id=f"{self.document_id}_{chunk_index}",
            document_id=self.document_id,
            content=content,
            chunk_index=chunk_index,
            embedding=embedding,
            metadata={
                "filename": self.filename,
                "document_type": self.document_type,
                "upload_timestamp": self.upload_timestamp.isoformat()
            }
        )
        self.chunks.append(chunk)
        return chunk
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "document_type": self.document_type,
            "content": self.content,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "metadata": self.metadata,
            "upload_timestamp": self.upload_timestamp.isoformat()
        }


@dataclass
class QueryResult:
    """Represents a query result with context."""
    question: str
    answer: str
    retrieved_chunks: List[tuple[DocumentChunk, float]]  # (chunk, score)
    llm_responses: Optional[List[Dict[str, Any]]] = None
    query_type: str = "general"
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "answer": self.answer,
            "retrieved_chunks": [
                {"chunk": chunk.to_dict(), "score": score}
                for chunk, score in self.retrieved_chunks
            ],
            "llm_responses": self.llm_responses,
            "query_type": self.query_type,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat()
        }
