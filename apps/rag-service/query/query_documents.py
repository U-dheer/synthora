
from fastapi import APIRouter
from pinecone import QueryRequest
from pydantic import BaseModel
from utils.pine_utils import embeddings, index
from langchain_pinecone import PineconeVectorStore


async def query_documents(query: str, document_id: str | None = None):
    print(f"Received query: {query}")
    relevance_threshold = 0.8
    
    vector_store = PineconeVectorStore(index=index, embedding=embeddings,namespace="default")

    search_kwargs = {
        "k": 5,
        "namespace": "default",
        "score_threshold": relevance_threshold,
    }
    if document_id is not None:
        search_kwargs["filter"] = {"document_id": document_id}

    results_with_scores = vector_store.similarity_search_with_relevance_scores(
        query,
        **search_kwargs,
    )
    
    return {
        "status": "completed",
        "query": query,
        "document_id": document_id,
        "relevance_threshold": relevance_threshold,
        "results": [
            {
                "content": doc.page_content,
                "relevance_score": score,
            }
            for doc, score in results_with_scores
        ],
    }