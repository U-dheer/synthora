from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging
import sys

from app.config import get_settings
from app.models.schemas import HealthResponse, ErrorResponse
from app.api.routes import documents, query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG Service API",
    description="Retrieval-Augmented Generation service with FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc.errors()),
            timestamp=datetime.utcnow()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc),
            timestamp=datetime.utcnow()
        ).dict()
    )


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    settings = get_settings()
    logger.info("=" * 50)
    logger.info("RAG Service Starting Up")
    logger.info("=" * 50)
    logger.info(f"Vector DB Type: {settings.vector_db_type}")
    logger.info(f"Embedding Type: {settings.embedding_type}")
    logger.info(f"Gateway URL: {settings.gateway_service_url}")
    logger.info(f"Chunk Size: {settings.chunk_size}")
    logger.info(f"Chunk Overlap: {settings.chunk_overlap}")
    logger.info(f"Top K Results: {settings.top_k_results}")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("RAG Service Shutting Down")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": "RAG Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "note": "Access via Gateway: http://gateway:3000/rag/*"
    }


@app.get("/rag/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the status of the service and configuration.
    """
    settings = get_settings()
    
    return HealthResponse(
        status="healthy",
        vector_db_type=settings.vector_db_type,
        embedding_type=settings.embedding_type,
        gateway_url=settings.gateway_service_url,
        timestamp=datetime.utcnow()
    )


@app.post("/rag/reindex", tags=["management"])
async def reindex():
    """
    Rebuild vector index (placeholder).
    
    This endpoint can be implemented to rebuild the entire vector index
    from stored documents if needed.
    """
    return {
        "message": "Reindex functionality not yet implemented",
        "status": "pending"
    }


# Include routers
app.include_router(documents.router)
app.include_router(query.router)


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
        log_level=settings.log_level.lower()
    )
