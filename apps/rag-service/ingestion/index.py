from fastapi import APIRouter, UploadFile, File
from ingestion.document_loader import load_document
from ingestion.chunker import chunk_text
from ingestion.embedder import embed_text
from ingestion.vectordb import store_in_pinecone

async def ingest_document(file: UploadFile,document_id: str):
    documents = await load_document(file)
    chunks = await chunk_text(documents)
    embeddings = await embed_text(chunks)

    await store_in_pinecone(embeddings , chunks, document_id)

    return {"status" : "completed", "num_chunks": len(chunks)}