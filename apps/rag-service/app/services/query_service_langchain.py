import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document as LangChainDocument
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.retrievers import BaseRetriever

from app.config import Settings
from app.services.vector_db_langchain import LangChainVectorDBService
from app.services.gateway_client import GatewayClient
from app.services.llm_orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)


class LangChainQueryService:
    """Handles query processing using LangChain retrieval chains."""
    
    def __init__(
        self,
        settings: Settings,
        vector_db_service: LangChainVectorDBService,
        gateway_client: GatewayClient,
        llm_orchestrator: LLMOrchestrator
    ):
        """Initialize query service."""
        self.settings = settings
        self.vector_db_service = vector_db_service
        self.gateway_client = gateway_client
        self.llm_orchestrator = llm_orchestrator
        
        # System prompt for RAG
        self.system_prompt = """You are a helpful assistant that answers questions based on the provided context.
Use the following pieces of context to answer the question at the end.
If you don't know the answer or the context doesn't contain relevant information, say so.
Don't try to make up an answer.

Context:
{context}

Question: {question}

Answer:"""
        
        logger.info("Initialized LangChain Query Service")
    
    async def query_with_llm(
        self,
        query: str,
        llm_service: Optional[str] = None,
        top_k: int = 5,
        use_reranking: bool = False,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Query with full LLM pipeline using LangChain retrieval.
        
        This method:
        1. Retrieves relevant chunks using vector similarity
        2. (Optional) Reranks chunks
        3. Sends context + query to LLM service via Gateway
        
        Args:
            query: User query
            llm_service: LLM service to use (gemini, llama, cohere)
            top_k: Number of chunks to retrieve
            use_reranking: Whether to rerank results
        
        Returns:
            Query response with answer and metadata
        """
        try:
            logger.info(f"Processing query with LLM: {query}")
            start_time = datetime.now()
            
            # Retrieve relevant chunks
            logger.info(f"Retrieving top {top_k} relevant chunks...")
            results = self.vector_db_service.similarity_search(
                query=query,
                k=top_k
            )
            
            # Filter out initialization documents
            filtered_results = []
            if results:
                for chunk, score in results:
                    # Skip initialization dummy documents
                    if chunk.metadata.get("init") != True:
                        filtered_results.append((chunk, score))
            
            # If no real data in knowledge base, return special response for Gateway to handle
            if not filtered_results:
                logger.warning("No relevant knowledge base data found - Gateway should query AI models directly")
                return {
                    "success": True,
                    "answer": "",  # Empty answer signals Gateway to query AIs
                    "chunks": [],
                    "no_kb_data": True,  # Special flag for Gateway
                    "metadata": {
                        "query": query,
                        "chunks_retrieved": 0,
                        "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                    }
                }
            
            # Extract chunks from tuples (chunk, score)
            chunks = []
            for chunk, score in filtered_results:
                chunks.append({
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "score": float(score)
                })
            
            logger.info(f"Retrieved {len(chunks)} chunks")
            
            # Optionally rerank
            if use_reranking and len(chunks) > 1:
                logger.info("Reranking results...")
                chunks = await self._rerank_chunks(query, chunks)
            
            # Build context from chunks
            context = "\n\n".join([
                f"[Document {i+1}]\n{chunk['content']}"
                for i, chunk in enumerate(chunks)
            ])
            
            # Orchestrate LLM call
            logger.info(f"Sending to LLM orchestrator (service: {llm_service or 'auto'})...")
            answer, llm_responses = await self.llm_orchestrator.process_query_with_context(
                question=query,
                context=context,
                headers=headers,
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "answer": answer,
                "chunks": chunks[:3],  # Return top 3 for reference
                "llm_responses": [resp.dict() for resp in llm_responses],
                "metadata": {
                    "query": query,
                    "chunks_retrieved": len(chunks),
                    "llm_services_used": len(llm_responses),
                    "processing_time_ms": processing_time,
                    "reranked": use_reranking
                }
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "answer": f"An error occurred while processing your query: {str(e)}",
                "chunks": [],
                "metadata": {
                    "query": query
                }
            }
    
    async def query_documents_only(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Query documents directly without LLM processing.
        
        Returns raw relevant chunks from vector database.
        
        Args:
            query: User query
            document_id: Optional document ID to filter by
            top_k: Number of chunks to retrieve
        
        Returns:
            Query response with relevant chunks
        """
        try:
            logger.info(f"Querying documents only: {query}")
            start_time = datetime.now()
            
            # Retrieve relevant chunks
            if document_id:
                logger.info(f"Filtering by document ID: {document_id}")
                results = self.vector_db_service.similarity_search(
                    query=query,
                    k=top_k,
                    filter_document_id=document_id
                )
            else:
                results = self.vector_db_service.similarity_search(
                    query=query,
                    k=top_k
                )
            
            if not results:
                return {
                    "success": True,
                    "chunks": [],
                    "metadata": {
                        "query": query,
                        "chunks_retrieved": 0,
                        "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                        "document_id": document_id
                    }
                }
            
            # Extract chunks from tuples (chunk, score)
            chunks = []
            for chunk, score in results:
                chunks.append({
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "score": float(score)
                })
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Retrieved {len(chunks)} relevant chunks")
            
            return {
                "success": True,
                "chunks": chunks,
                "metadata": {
                    "query": query,
                    "chunks_retrieved": len(chunks),
                    "processing_time_ms": processing_time,
                    "document_id": document_id
                }
            }
            
        except Exception as e:
            logger.error(f"Document query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks": [],
                "metadata": {
                    "query": query,
                    "document_id": document_id
                }
            }
    
    async def _rerank_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks using cross-encoder or LLM-based reranking.
        
        For now, this is a placeholder that returns chunks as-is.
        In production, you could use:
        - Cohere Rerank API
        - Cross-encoder model (sentence-transformers)
        - LLM-based scoring
        
        Args:
            query: User query
            chunks: List of chunks to rerank
        
        Returns:
            Reranked chunks
        """
        logger.info("Reranking not yet implemented, returning original order")
        return chunks
    
    def create_retriever(
        self,
        search_kwargs: Optional[Dict[str, Any]] = None
    ) -> BaseRetriever:
        """
        Create a LangChain retriever from the vector store.
        
        This retriever can be used with LangChain chains.
        
        Args:
            search_kwargs: Optional search parameters (k, filter, etc.)
        
        Returns:
            LangChain retriever
        """
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        return self.vector_db_service.vector_store.as_retriever(
            search_kwargs=search_kwargs
        )
    
    # NOTE: This method requires langchain.chains package which is not installed
    # Uncomment and install if needed for native LangChain chain usage
    # async def query_with_langchain_chain(
    #     self,
    #     query: str,
    #     llm: BaseChatModel,
    #     top_k: int = 5
    # ) -> Dict[str, Any]:
    #     """Query using native LangChain retrieval chain."""
    #     # Implementation removed - install langchain.chains if needed
    #     pass


# Global query service instance
_query_service: Optional[LangChainQueryService] = None


def get_query_service(
    settings: Settings,
    vector_db_service: LangChainVectorDBService,
    gateway_client: GatewayClient,
    llm_orchestrator: LLMOrchestrator
) -> LangChainQueryService:
    """Get or create the global query service instance."""
    global _query_service
    if _query_service is None:
        _query_service = LangChainQueryService(
            settings,
            vector_db_service,
            gateway_client,
            llm_orchestrator
        )
    return _query_service
