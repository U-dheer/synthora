import logging
from typing import Optional
from datetime import datetime
import tempfile
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document as LangChainDocument

from app.config import Settings
from app.models.document import Document, DocumentChunk
from app.services.vector_db_langchain import LangChainVectorDBService

logger = logging.getLogger(__name__)


class LangChainDocumentProcessor:
    """Handles document processing using LangChain."""
    
    def __init__(
        self,
        settings: Settings,
        embeddings: Embeddings,
        vector_db_service: LangChainVectorDBService
    ):
        """Initialize document processor."""
        self.settings = settings
        self.embeddings = embeddings
        self.vector_db_service = vector_db_service
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        logger.info("Initialized LangChain Document Processor")
    
    async def process_file(
        self,
        filename: str,
        file_content: bytes,
        metadata: Optional[dict] = None
    ) -> Document:
        """
        Process and store a file document using LangChain loaders.
        
        Args:
            filename: Name of the file
            file_content: File content as bytes
            metadata: Optional metadata
        
        Returns:
            Processed document
        """
        try:
            logger.info(f"Processing file: {filename}")
            
            # Determine file type
            file_ext = Path(filename).suffix.lower()
            
            # Save to temp file for LangChain loaders
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            try:
                # Load document using appropriate LangChain loader
                if file_ext == '.pdf':
                    loader = PyPDFLoader(temp_path)
                    doc_type = "pdf"
                elif file_ext in ['.docx', '.doc']:
                    loader = Docx2txtLoader(temp_path)
                    doc_type = "docx"
                elif file_ext in ['.txt', '.text']:
                    loader = TextLoader(temp_path)
                    doc_type = "txt"
                else:
                    raise ValueError(f"Unsupported file type: {file_ext}")
                
                # Load and split document
                docs = loader.load()
                splits = self.text_splitter.split_documents(docs)
                
                if not splits:
                    raise ValueError(f"No content extracted from {filename}")
                
                # Extract full text
                full_text = "\n\n".join([doc.page_content for doc in docs])
                
            finally:
                # Clean up temp file
                Path(temp_path).unlink(missing_ok=True)
            
            # Create document
            document = Document.create_new(
                filename=filename,
                document_type=doc_type,
                content=full_text,
                metadata=metadata or {}
            )
            
            # Create chunks
            chunks = []
            for idx, split_doc in enumerate(splits):
                chunk = document.add_chunk(
                    content=split_doc.page_content,
                    chunk_index=idx
                )
                chunks.append(chunk)
            
            # Store in vector database
            logger.info(f"Storing {len(chunks)} chunks in vector database...")
            self.vector_db_service.store_embeddings(
                chunks=chunks,
                metadata={
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "document_type": document.document_type,
                    "upload_timestamp": document.upload_timestamp.isoformat()
                }
            )
            
            logger.info(f"Successfully processed file: {filename} ({len(chunks)} chunks)")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process file {filename}: {e}")
            raise
    
    async def process_text(
        self,
        content: str,
        metadata: Optional[dict] = None
    ) -> Document:
        """
        Process plain text content directly (for AI-generated responses).
        
        Args:
            content: Text content to store
            metadata: Optional metadata (should include source, question, etc.)
        
        Returns:
            Processed document
        """
        try:
            logger.info(f"Processing text content ({len(content)} characters)")
            
            # Create a LangChain Document
            from langchain_core.documents import Document as LangChainDoc
            doc = LangChainDoc(page_content=content, metadata=metadata or {})
            
            # Split into chunks
            splits = self.text_splitter.split_documents([doc])
            
            if not splits:
                raise ValueError("No content after splitting")
            
            # Create document
            filename = metadata.get("source", "text_content") if metadata else "text_content"
            document = Document.create_new(
                filename=filename,
                document_type="txt",
                content=content,
                metadata=metadata or {}
            )
            
            # Create chunks
            chunks = []
            for idx, split_doc in enumerate(splits):
                chunk = document.add_chunk(
                    content=split_doc.page_content,
                    chunk_index=idx
                )
                chunks.append(chunk)
            
            # Store in vector database
            logger.info(f"Storing {len(chunks)} chunks in vector database...")
            self.vector_db_service.store_embeddings(
                chunks=chunks,
                metadata={
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "document_type": document.document_type,
                    "upload_timestamp": document.upload_timestamp.isoformat(),
                    **(metadata or {})
                }
            )
            
            logger.info(f"Successfully processed text content ({len(chunks)} chunks)")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process text content: {e}")
            raise
    
    async def process_url(
        self,
        url: str,
        metadata: Optional[dict] = None
    ) -> Document:
        """
        Process and store content from a URL using LangChain.
        
        Args:
            url: URL to scrape
            metadata: Optional metadata
        
        Returns:
            Processed document
        """
        try:
            logger.info(f"Processing URL: {url}")
            
            # Use LangChain's WebBaseLoader
            loader = WebBaseLoader(url)
            docs = loader.load()
            
            if not docs:
                raise ValueError(f"No content extracted from {url}")
            
            # Split documents
            splits = self.text_splitter.split_documents(docs)
            
            # Extract full text
            full_text = "\n\n".join([doc.page_content for doc in docs])
            
            if not full_text or not full_text.strip():
                raise ValueError(f"No text content extracted from {url}")
            
            # Create document
            document = Document.create_new(
                filename=url,
                document_type="url",
                content=full_text,
                metadata=metadata or {}
            )
            
            # Create chunks
            chunks = []
            for idx, split_doc in enumerate(splits):
                chunk = document.add_chunk(
                    content=split_doc.page_content,
                    chunk_index=idx
                )
                chunks.append(chunk)
            
            # Store in vector database
            logger.info(f"Storing {len(chunks)} chunks in vector database...")
            self.vector_db_service.store_embeddings(
                chunks=chunks,
                metadata={
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "document_type": document.document_type,
                    "upload_timestamp": document.upload_timestamp.isoformat()
                }
            )
            
            logger.info(f"Successfully processed URL: {url} ({len(chunks)} chunks)")
            return document
            
        except Exception as e:
            logger.error(f"Failed to process URL {url}: {e}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the knowledge base.
        
        Args:
            document_id: ID of document to delete
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting document: {document_id}")
            result = self.vector_db_service.delete_by_id(document_id)
            
            if result:
                logger.info(f"Successfully deleted document: {document_id}")
            else:
                logger.warning(f"Document not found: {document_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
    
    def get_all_documents(self) -> list:
        """
        Get all documents in the knowledge base.
        
        Returns:
            List of document metadata
        """
        try:
            documents = self.vector_db_service.get_all_documents()
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            raise


# Global document processor instance
_document_processor: Optional[LangChainDocumentProcessor] = None


def get_document_processor(
    settings: Settings,
    embeddings: Embeddings,
    vector_db_service: LangChainVectorDBService
) -> LangChainDocumentProcessor:
    """Get or create the global document processor instance."""
    global _document_processor
    if _document_processor is None:
        _document_processor = LangChainDocumentProcessor(settings, embeddings, vector_db_service)
    return _document_processor
