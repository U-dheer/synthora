from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Vector Database Configuration
    vector_db_type: str = "faiss"
    faiss_index_path: str = "./data/faiss_index"
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = ""
    
    # Embedding Model Configuration
    embedding_type: str = "local"
    local_model_path: str = "~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2"
    local_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    openai_api_key: str = ""
    cohere_api_key: str = ""
    
    # Gateway Service Configuration
    gateway_service_url: str = "http://localhost:3006"
    # Optional service token to authenticate requests to the Gateway
    gateway_service_token: str = ""
    
    # Backend Service Endpoints (Relative to Gateway)
    gemini_endpoint: str = "/gemini/gemini/make"
    llama_endpoint: str = "/llama/hugging-face/chat"
    cohere_endpoint: str = "/cohere/cohere/make"
    summarizer_endpoint: str = "/summarize/api/summarize/ai-prompts"
    
    # Application Settings
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_results: int = 5
    request_timeout: int = 30
    max_retries: int = 3
    
    # FastAPI Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    app_reload: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def expanded_local_model_path(self) -> Path:
        """Expand the local model path to handle ~."""
        return Path(os.path.expanduser(self.local_model_path))
    
    @property
    def expanded_faiss_index_path(self) -> Path:
        """Expand the FAISS index path."""
        return Path(os.path.expanduser(self.faiss_index_path))
    
    def get_full_gateway_url(self, endpoint: str) -> str:
        """Construct full URL for gateway endpoints."""
        return f"{self.gateway_service_url}{endpoint}"
    
    def validate_vector_db_config(self):
        """Validate vector database configuration."""
        if self.vector_db_type == "pinecone":
            if not all([self.pinecone_api_key, self.pinecone_environment, self.pinecone_index_name]):
                raise ValueError(
                    "Pinecone configuration incomplete. Required: "
                    "PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME"
                )
        elif self.vector_db_type == "faiss":
            # Ensure FAISS directory exists
            self.expanded_faiss_index_path.parent.mkdir(parents=True, exist_ok=True)
    
    def validate_embedding_config(self):
        """Validate embedding configuration."""
        if self.embedding_type == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI API key required when EMBEDDING_TYPE=openai")
        elif self.embedding_type == "cohere" and not self.cohere_api_key:
            raise ValueError("Cohere API key required when EMBEDDING_TYPE=cohere")
        elif self.embedding_type == "local":
            # Model will be downloaded automatically on first use
            pass


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.validate_vector_db_config()
    settings.validate_embedding_config()
    return settings
