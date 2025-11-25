"""
Dependency injection module for LangChain-based RAG service.

This module provides factory functions and dependency injection
for all service components using LangChain.
"""
import logging
from functools import lru_cache
from typing import Optional

from langchain_core.embeddings import Embeddings

from app.config import Settings, get_settings
from app.services.embedding_service import get_embedding_service, EmbeddingServiceFactory
from app.services.vector_db_langchain import LangChainVectorDBService
from app.services.document_processor_langchain import LangChainDocumentProcessor, get_document_processor
from app.services.query_service_langchain import LangChainQueryService, get_query_service
from app.services.gateway_client import GatewayClient
from app.services.llm_orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)

# Global service instances
_embeddings: Optional[Embeddings] = None
_vector_db_service: Optional[LangChainVectorDBService] = None
_gateway_client: Optional[GatewayClient] = None
_llm_orchestrator: Optional[LLMOrchestrator] = None
_document_processor: Optional[LangChainDocumentProcessor] = None
_query_service: Optional[LangChainQueryService] = None


def get_embeddings_service(settings: Settings = None) -> Embeddings:
    """Get or create embeddings service."""
    global _embeddings
    
    if _embeddings is None:
        if settings is None:
            settings = get_settings()
        
        logger.info(f"Initializing embeddings service: {settings.embedding_type}")
        _embeddings = get_embedding_service(settings)
    
    return _embeddings


def get_vector_db_service(settings: Settings = None, embeddings: Embeddings = None) -> LangChainVectorDBService:
    """Get or create vector database service."""
    global _vector_db_service
    
    if _vector_db_service is None:
        if settings is None:
            settings = get_settings()
        if embeddings is None:
            embeddings = get_embeddings_service(settings)
        
        logger.info(f"Initializing vector DB service: {settings.vector_db_type}")
        from app.services.vector_db_langchain import VectorDBServiceFactory
        _vector_db_service = VectorDBServiceFactory.create(settings, embeddings)
    
    return _vector_db_service


def get_gateway_client_service(settings: Settings = None) -> GatewayClient:
    """Get or create gateway client."""
    global _gateway_client
    
    if _gateway_client is None:
        if settings is None:
            settings = get_settings()
        
        logger.info(f"Initializing gateway client: {settings.gateway_service_url}")
        _gateway_client = GatewayClient(settings)
    
    return _gateway_client


def get_llm_orchestrator_service(
    settings: Settings = None,
    gateway_client: GatewayClient = None
) -> LLMOrchestrator:
    """Get or create LLM orchestrator."""
    global _llm_orchestrator
    
    if _llm_orchestrator is None:
        if settings is None:
            settings = get_settings()
        if gateway_client is None:
            gateway_client = get_gateway_client_service(settings)
        
        logger.info("Initializing LLM orchestrator")
        _llm_orchestrator = LLMOrchestrator(settings, gateway_client)
    
    return _llm_orchestrator


def get_document_processor_service(
    settings: Settings = None,
    embeddings: Embeddings = None,
    vector_db_service: LangChainVectorDBService = None
) -> LangChainDocumentProcessor:
    """Get or create document processor."""
    global _document_processor
    
    if _document_processor is None:
        if settings is None:
            settings = get_settings()
        if embeddings is None:
            embeddings = get_embeddings_service(settings)
        if vector_db_service is None:
            vector_db_service = get_vector_db_service(settings, embeddings)
        
        logger.info("Initializing document processor")
        _document_processor = get_document_processor(settings, embeddings, vector_db_service)
    
    return _document_processor


def get_query_service_instance(
    settings: Settings = None,
    vector_db_service: LangChainVectorDBService = None,
    gateway_client: GatewayClient = None,
    llm_orchestrator: LLMOrchestrator = None
) -> LangChainQueryService:
    """Get or create query service."""
    global _query_service
    
    if _query_service is None:
        if settings is None:
            settings = get_settings()
        if vector_db_service is None:
            embeddings = get_embeddings_service(settings)
            vector_db_service = get_vector_db_service(settings, embeddings)
        if gateway_client is None:
            gateway_client = get_gateway_client_service(settings)
        if llm_orchestrator is None:
            llm_orchestrator = get_llm_orchestrator_service(settings, gateway_client)
        
        logger.info("Initializing query service")
        _query_service = get_query_service(
            settings,
            vector_db_service,
            gateway_client,
            llm_orchestrator
        )
    
    return _query_service


def reset_services():
    """Reset all service instances (useful for testing)."""
    global _embeddings, _vector_db_service, _gateway_client
    global _llm_orchestrator, _document_processor, _query_service
    
    _embeddings = None
    _vector_db_service = None
    _gateway_client = None
    _llm_orchestrator = None
    _document_processor = None
    _query_service = None
    
    logger.info("All service instances reset")

