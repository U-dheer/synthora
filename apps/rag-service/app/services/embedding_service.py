from abc import ABC, abstractmethod
from typing import List, Union
import logging

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_cohere import CohereEmbeddings
from langchain_core.embeddings import Embeddings

from app.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingServiceFactory:
    """Factory for creating LangChain embedding services based on configuration."""
    
    @staticmethod
    def create(settings: Settings) -> Embeddings:
        """Create LangChain embedding service based on settings."""
        embedding_type = settings.embedding_type.lower()
        
        if embedding_type == "local":
            logger.info("Initializing HuggingFace embeddings (local)")
            # Use model name directly - will auto-download from HuggingFace if not cached
            model_name = settings.local_model_name
            
            # Use LangChain's HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
        
        elif embedding_type == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            logger.info("Initializing OpenAI embeddings")
            # Use LangChain's OpenAIEmbeddings
            return OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                model="text-embedding-ada-002"
            )
        
        elif embedding_type == "cohere":
            if not settings.cohere_api_key:
                raise ValueError("Cohere API key not configured")
            
            logger.info("Initializing Cohere embeddings")
            # Use LangChain's CohereEmbeddings
            return CohereEmbeddings(
                cohere_api_key=settings.cohere_api_key,
                model="embed-english-v3.0"
            )
        
        else:
            raise ValueError(
                f"Unsupported embedding type: {embedding_type}. "
                "Supported types: local, openai, cohere"
            )


# Global embedding service instance
_embedding_service: Union[Embeddings, None] = None


def get_embedding_service(settings: Settings) -> Embeddings:
    """Get or create the global LangChain embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingServiceFactory.create(settings)
    return _embedding_service
