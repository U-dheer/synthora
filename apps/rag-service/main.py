from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from ingestion.document_loader import load_document
from routes import ingest, query
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the ingest router
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])

# Register the query router
app.include_router(query.router, prefix="/query", tags=["query"])

@app.get("/")
async def root():
    return {"message": "RAG Service API"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )