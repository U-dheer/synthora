from typing import List, Tuple, Dict, Any, Optional
import logging
from pathlib import Path
import json

from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LangChainDocument

try:
    from langchain_community.vectorstores import Pinecone as LangChainPinecone
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from app.config import Settings
from app.models.document import DocumentChunk

logger = logging.getLogger(__name__)


class LangChainVectorDBService:
    """LangChain-based vector database service."""
    
    def __init__(self, vector_store, documents_path: Path):
        """Initialize with LangChain vector store."""
        self.vector_store = vector_store
        self.documents_path = documents_path
        self.documents: Dict[str, Dict[str, Any]] = self._load_documents()
        
    def _load_documents(self) -> Dict[str, Dict[str, Any]]:
        """Load documents metadata from disk."""
        if self.documents_path.exists():
            try:
                with open(self.documents_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load documents: {e}")
        return {}
    
    def _save_documents(self):
        """Save documents metadata to disk."""
        try:
            self.documents_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.documents_path, 'w') as f:
                json.dump(self.documents, f, indent=2)
            logger.info(f"Saved documents to {self.documents_path}")
        except Exception as e:
            logger.error(f"Failed to save documents: {e}")
            raise
    
    def store_embeddings(
        self,
        chunks: List[DocumentChunk],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store document chunks using LangChain.
        
        Args:
            chunks: List of document chunks
            metadata: Optional metadata
        
        Returns:
            Success boolean
        """
        try:
            # Convert chunks to LangChain Document objects
            documents = []
            for chunk in chunks:
                # Merge chunk metadata with additional metadata
                chunk_metadata = chunk.to_dict()
                chunk_metadata.pop("embedding", None)  # Remove embedding from metadata
                if metadata:
                    chunk_metadata.update(metadata)
                
                doc = LangChainDocument(
                    page_content=chunk.content,
                    metadata=chunk_metadata
                )
                documents.append(doc)
            
            # Add to vector store
            self.vector_store.add_documents(documents)
            
            # Update documents registry
            if chunks:
                doc_id = chunks[0].document_id
                if doc_id not in self.documents:
                    self.documents[doc_id] = {
                        "document_id": doc_id,
                        "filename": chunks[0].metadata.get("filename", "unknown"),
                        "document_type": chunks[0].metadata.get("document_type", "unknown"),
                        "chunks_count": len(chunks),
                        "upload_timestamp": chunks[0].metadata.get("upload_timestamp", "unknown")
                    }
                    self._save_documents()
            
            logger.info(f"Stored {len(chunks)} chunks in vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            raise
    
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_document_id: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for similar chunks using LangChain.
        
        Args:
            query: Query text (will be embedded internally)
            k: Number of results
            filter_document_id: Optional document ID filter
        
        Returns:
            List of (chunk, score) tuples
        """
        try:
            # Use LangChain's similarity_search_with_score. Some vector store
            # implementations (FAISS local) may not support server-side metadata
            # filtering. To be robust, request a larger result set and apply a
            # client-side filter when `filter_document_id` is provided.
            request_k = k if not filter_document_id else max(k * 5, k)
            try:
                results = self.vector_store.similarity_search_with_score(
                    query,
                    k=request_k,
                    **({} if not filter_document_id else {"filter": {"document_id": filter_document_id}})
                )
            except TypeError:
                # Some implementations may not accept the `filter` kwarg; try
                # without it and perform client-side filtering below.
                results = self.vector_store.similarity_search_with_score(
                    query,
                    k=request_k
                )
            
            logger.info(f"Raw results type: {type(results)}, length: {len(results) if results else 0}")
            if results and len(results) > 0:
                logger.info(f"First result type: {type(results[0])}")
                logger.info(f"First result: {results[0]}")
            
            # Convert back to our format
            output = []
            for item in results:
                logger.info(f"Processing item type: {type(item)}, value: {item}")
                # Handle both tuple and list formats
                if isinstance(item, tuple) and len(item) == 2:
                    doc, score = item
                else:
                    logger.error(f"Unexpected result format: {type(item)}")
                    continue
                # If a document filter is requested, honor it client-side in
                # case the vectorstore did not apply it server-side.
                doc_id_meta = doc.metadata.get("document_id")
                if filter_document_id and str(doc_id_meta) != str(filter_document_id):
                    logger.debug(f"Skipping doc {doc_id_meta} due to filter {filter_document_id}")
                    continue

                chunk = DocumentChunk(
                    chunk_id=doc.metadata.get("chunk_id", ""),
                    document_id=doc.metadata.get("document_id", ""),
                    content=doc.page_content,
                    chunk_index=doc.metadata.get("chunk_index", 0),
                    metadata=doc.metadata
                )
                output.append((chunk, float(score)))
            
            logger.info(f"Found {len(output)} similar chunks")
            return output
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise
    
    def delete_by_id(self, document_id: str) -> bool:
        """
        Delete all chunks for a document.
        
        Args:
            document_id: Document ID to delete
        
        Returns:
            Success boolean
        """
        try:
            # LangChain FAISS doesn't support direct deletion
            # Need to rebuild the index without those documents
            logger.warning("Delete operation requires rebuilding index")
            
            # Remove from documents registry
            if document_id in self.documents:
                del self.documents[document_id]
                self._save_documents()
                logger.info(f"Removed document {document_id} from registry")
                return True
            
            logger.warning(f"Document {document_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents metadata."""
        return list(self.documents.values())


class VectorDBServiceFactory:
    """Factory for creating LangChain-based vector database services."""
    
    @staticmethod
    def create(settings: Settings, embeddings: Embeddings) -> LangChainVectorDBService:
        """
        Create vector database service based on settings.
        
        Args:
            settings: Application settings
            embeddings: LangChain embeddings instance
        
        Returns:
            LangChainVectorDBService instance
        """
        db_type = settings.vector_db_type.lower()
        
        if db_type == "faiss":
            index_path = settings.expanded_faiss_index_path
            documents_path = index_path.parent / f"{index_path.name}_documents.json"
            
            # Create directory
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if FAISS index files exist
            faiss_file = index_path.parent / f"{index_path.name}.faiss"
            pkl_file = index_path.parent / f"{index_path.name}.pkl"
            
            # Load or create FAISS index
            if faiss_file.exists() and pkl_file.exists():
                try:
                    logger.info(f"Loading existing FAISS index from {index_path}")
                    vector_store = FAISS.load_local(
                        str(index_path.parent),
                        embeddings,
                        index_name=index_path.stem,
                        allow_dangerous_deserialization=True
                    )
                except Exception as e:
                    logger.warning(f"Failed to load index: {e}. Creating new index.")
                    # Create empty FAISS store
                    vector_store = FAISS.from_texts(
                        texts=["initialization"],
                        embedding=embeddings,
                        metadatas=[{"init": True}]
                    )
                    vector_store.save_local(str(index_path.parent), index_name=index_path.stem)
            else:
                logger.info(f"Creating new FAISS index at {index_path}")
                # Create empty FAISS store
                vector_store = FAISS.from_texts(
                    texts=["initialization"],
                    embedding=embeddings,
                    metadatas=[{"init": True}]
                )
                vector_store.save_local(str(index_path.parent), index_name=index_path.stem)
            
            # Wrap in our service
            service = LangChainVectorDBService(vector_store, documents_path)
            
            # Override save method to persist FAISS
            original_store = service.store_embeddings
            def store_with_save(chunks, metadata=None):
                result = original_store(chunks, metadata)
                vector_store.save_local(str(index_path.parent), index_name=index_path.stem)
                return result
            service.store_embeddings = store_with_save
            
            return service
        
        elif db_type == "pinecone":
            if not PINECONE_AVAILABLE:
                raise ImportError("Pinecone not installed. Install with: pip install pinecone-client")
            
            if not all([settings.pinecone_api_key, settings.pinecone_environment, settings.pinecone_index_name]):
                raise ValueError("Pinecone configuration incomplete")
            
            logger.info("Initializing Pinecone vector store")
            
            # Initialize Pinecone
            pc = Pinecone(api_key=settings.pinecone_api_key)
            
            # Create index if it doesn't exist
            index_name = settings.pinecone_index_name
            if index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=index_name,
                    dimension=384,  # sentence-transformers dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.pinecone_environment
                    )
                )
                logger.info(f"Created Pinecone index: {index_name}")
            
            # Create LangChain Pinecone vector store
            vector_store = LangChainPinecone.from_existing_index(
                index_name=index_name,
                embedding=embeddings
            )
            
            documents_path = Path(settings.faiss_index_path).parent / "pinecone_documents.json"
            
            return LangChainVectorDBService(vector_store, documents_path)
        
        else:
            raise ValueError(f"Unsupported vector DB type: {db_type}")


# Global vector DB service instance
_vector_db_service: Optional[LangChainVectorDBService] = None


def get_vector_db_service(settings: Settings, embeddings: Embeddings) -> LangChainVectorDBService:
    """Get or create the global vector DB service instance."""
    global _vector_db_service
    if _vector_db_service is None:
        _vector_db_service = VectorDBServiceFactory.create(settings, embeddings)
    return _vector_db_service
