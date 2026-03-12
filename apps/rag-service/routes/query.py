import uuid
from fastapi import APIRouter, UploadFile, File, Form
from ingestion.index import ingest_document
from query.query_documents import query_documents 
router = APIRouter()


@router.post("/")
async def rag(
    file: UploadFile | None = File(None),
    query: str = Form(...),
    document_id: str | None = Form(None),
):
    resolved_document_id = document_id

    if file is not None:
        resolved_document_id = resolved_document_id or str(uuid.uuid4())
        await ingest_document(file, resolved_document_id)

    docs = await query_documents(query, resolved_document_id)
    return docs