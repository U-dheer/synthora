from fastapi import FastAPI, UploadFile, File
from ingestion.document_loader import load_document
from routes import ingest
import uvicorn

app = FastAPI()

# Register the ingest router
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        documents = await load_document(file)
        return {
            "status": "success",
            "filename": file.filename,
            "num_documents": len(documents),
            "content_preview": documents[0].page_content[:200] if documents else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)