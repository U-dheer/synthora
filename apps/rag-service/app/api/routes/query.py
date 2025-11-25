from fastapi import APIRouter, Depends, HTTPException, status, Request
import logging
from datetime import datetime
import asyncio

from app.config import Settings, get_settings
from app.models.schemas import (
    QueryRequest,
    DocumentSpecificQueryRequest,
    QueryResponse,
    QueryType,
    RetrievedContext,
    LLMResponse as LLMResponseSchema,
    DocumentChunk as DocumentChunkSchema
)
from app.dependencies import get_query_service_instance
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag/query", tags=["query"])

# Timeout for external LLM orchestration calls (seconds)
LLM_TIMEOUT_SECONDS = 100


def get_dependencies(settings: Settings = Depends(get_settings)):
    """Get service dependencies."""
    query_service = get_query_service_instance(settings)
    return query_service


@router.post("", response_model=QueryResponse)
async def query(
    body: dict,
    request_obj: Request,
    query_service = Depends(get_dependencies)
):
    """
    Process a general query (Scenario A: Full pipeline).
    
    Workflow:
    1. Generate query embedding
    2. Retrieve relevant context from vector database
    3. Query all three LLM services (Gemini, Llama, Cohere) via Gateway
    4. Summarize responses via Gateway
    5. Store summarized response in vector database
    6. Return final answer
    
    This endpoint ALWAYS queries all LLM services even if the vector DB has the answer.
    """
    try:
        # Accept both general queries and document-specific requests in this endpoint.
        # If a document id is provided in the body, route to the document-specific
        # query logic to avoid clients having to call a different URL.
        question = body.get("question")
        top_k = body.get("top_k", 5)
        document_id = body.get("document_id") or body.get("documentId")
        summarize_flag = body.get("summarize", True)
        incoming_auth = request_obj.headers.get("authorization")
        forward_headers = {"Authorization": incoming_auth} if incoming_auth else None

        if document_id:
            logger.info(f"Processing document-specific query for document {document_id}: {str(question)[:100]}...")
            result = await query_service.query_documents_only(
                query=question,
                document_id=document_id,
                top_k=top_k
            )

            # Map returned chunks into RetrievedContext items expected by the
            # response model. Each chunk in `result['chunks']` is a dict with
            # content, metadata and score.
            retrieved_contexts = []
            for ch in result.get("chunks", []):
                metadata = ch.get("metadata", {}) or {}
                # Build the pydantic DocumentChunk schema (imported as DocumentChunkSchema)
                chunk_schema = DocumentChunkSchema(
                    chunk_id=metadata.get("chunk_id", ""),
                    document_id=metadata.get("document_id", document_id),
                    content=ch.get("content", ""),
                    chunk_index=metadata.get("chunk_index", 0),
                    metadata=metadata,
                )
                retrieved_contexts.append(RetrievedContext(chunk=chunk_schema, score=ch.get("score", 0.0)))

            # Build a compact context to send to the LLM orchestrator (top-k chunks)
            context = "\n\n".join([
                f"[Document {i+1}]\n{rc.chunk.content}"
                for i, rc in enumerate(retrieved_contexts[:top_k])
            ])

            # If caller requested no summarization, return chunks immediately
            if not summarize_flag:
                answer_text = result.get("answer") or "Retrieved relevant chunks (document-specific)"
                serialized_llm_responses = None
                response = QueryResponse(
                    answer=answer_text,
                    query_type=QueryType.DOCUMENT_SPECIFIC,
                    retrieved_contexts=retrieved_contexts,
                    llm_responses=serialized_llm_responses,
                    processing_time_seconds=result.get("metadata", {}).get("processing_time_ms", 0) / 1000,
                    timestamp=datetime.utcnow()
                )
                logger.info("Document-specific query completed (no summarization)")
                return response

            # Call LLM orchestrator to get a compact summarized answer
            try:
                # Fail-fast: give the orchestrator a limited time to respond
                answer_text, llm_responses = await asyncio.wait_for(
                    query_service.llm_orchestrator.process_query_with_context(
                        question,
                        context,
                        # headers=forward_headers,
                    ),
                    timeout=LLM_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                logger.error(f"LLM orchestration timed out after {LLM_TIMEOUT_SECONDS}s")
                # Fall back to returning chunks when LLM times out
                answer_text = result.get("answer") or "Retrieved relevant chunks (document-specific)"
                llm_responses = None
                # Try a quick direct call to a single LLM via gateway as a fallback
                try:
                    logger.info("Attempting direct fallback call to LLM (llama) via gateway")
                    # Compose a strict prompt to force the model to answer from
                    # the provided context and avoid hallucinations.
                    system_instruction = (
                        "You are an assistant that MUST answer using ONLY the provided context.\n"
                        "If the answer cannot be found in the context, reply with 'I don't know based on the provided documents.'\n"
                        "Be concise and list only the requested information."
                    )
                    composed_prompt = f"{system_instruction}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"

                    fallback_resp = await query_service.gateway_client.post_to_llm_service(
                        endpoint=query_service.settings.llama_endpoint,
                        prompt=composed_prompt,
                        context=None,
                        max_tokens=500,
                        temperature=0.0,
                        timeout_seconds=8,
                        headers=forward_headers,
                    )
                    # extract text
                    fallback_text = (fallback_resp.get("response") or fallback_resp.get("text") or fallback_resp.get("answer") or str(fallback_resp))
                    if fallback_text:
                        answer_text = fallback_text
                        llm_responses = [LLMResponseSchema(service="llama", response=answer_text)]
                        logger.info("Direct fallback LLM returned a response")
                except Exception as fe:
                    logger.error(f"Direct fallback LLM call failed: {fe}")

                # Provide a lightweight error response so clients can see the timeout
                if not llm_responses:
                    serialized_llm_responses = [{"service": "orchestrator", "response": "", "error": f"timeout after {LLM_TIMEOUT_SECONDS}s"}]
                else:
                    serialized_llm_responses = [r.dict() if hasattr(r, "dict") else dict(r) for r in llm_responses]

                response = QueryResponse(
                    answer=answer_text,
                    query_type=QueryType.DOCUMENT_SPECIFIC,
                    retrieved_contexts=retrieved_contexts,
                    llm_responses=serialized_llm_responses,
                    processing_time_seconds=result.get("metadata", {}).get("processing_time_ms", 0) / 1000,
                    timestamp=datetime.utcnow()
                )
                logger.info("Document-specific query completed (LLM timeout fallback)")
                return response
            except Exception as e:
                logger.error(f"LLM orchestration failed: {e}")
                # Fall back to returning chunks when LLM fails
                answer_text = result.get("answer") or "Retrieved relevant chunks (document-specific)"
                llm_responses = None
                # Attempt direct fallback to a single LLM via gateway
                try:
                    logger.info("Attempting direct fallback call to LLM (llama) via gateway after orchestrator error")
                    system_instruction = (
                        "You are an assistant that MUST answer using ONLY the provided context.\n"
                        "If the answer cannot be found in the context, reply with 'I don't know based on the provided documents.'\n"
                        "Be concise and list only the requested information."
                    )
                    composed_prompt = f"{system_instruction}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
                    fallback_resp = await query_service.gateway_client.post_to_llm_service(
                        endpoint=query_service.settings.llama_endpoint,
                        prompt=composed_prompt,
                        context=None,
                        max_tokens=500,
                        temperature=0.0,
                        timeout_seconds=8,
                        headers=forward_headers,
                    )
                    fallback_text = (fallback_resp.get("response") or fallback_resp.get("text") or fallback_resp.get("answer") or str(fallback_resp))
                    if fallback_text:
                        answer_text = fallback_text
                        llm_responses = [LLMResponseSchema(service="llama", response=answer_text)]
                        logger.info("Direct fallback LLM returned a response after orchestrator error")
                except Exception as fe:
                    logger.error(f"Direct fallback LLM call failed after orchestrator error: {fe}")

            # Serialize LLM responses if present
            serialized_llm_responses = None
            if llm_responses:
                try:
                    serialized_llm_responses = [r.dict() if hasattr(r, "dict") else dict(r) for r in llm_responses]
                except Exception:
                    serialized_llm_responses = [r for r in llm_responses]

            response = QueryResponse(
                answer=answer_text,
                query_type=QueryType.DOCUMENT_SPECIFIC,
                retrieved_contexts=retrieved_contexts,
                llm_responses=serialized_llm_responses,
                processing_time_seconds=result.get("metadata", {}).get("processing_time_ms", 0) / 1000,
                timestamp=datetime.utcnow()
            )
            logger.info("Document-specific query completed")
            return response

        @router.get("/internal/llm-health")
        async def llm_healthcheck(
            query_service = Depends(get_dependencies)
        ) -> Dict[str, Any]:
            """
            Internal health check endpoint that pings configured LLM endpoints
            and the summarizer via the gateway with short timeouts.
            Returns a compact JSON report showing which services responded.
            """
            report: Dict[str, Any] = {}

            # Check gateway reachability
            try:
                gw_ok = await query_service.gateway_client.health_check()
            except Exception as e:
                gw_ok = False
                report["gateway_error"] = str(e)

            report["gateway_reachable"] = bool(gw_ok)

            # Ping each LLM endpoint with a tiny prompt
            llm_results = {}
            orchestrator = getattr(query_service, "llm_orchestrator", None)
            if orchestrator:
                for svc_name, endpoint in orchestrator.llm_endpoints.items():
                    try:
                        resp = await query_service.gateway_client.post_to_llm_service(
                            endpoint=endpoint,
                            prompt="health check: please reply with 'ok'",
                            context=None,
                            max_tokens=8,
                            temperature=0.0,
                            timeout_seconds=3
                        )
                        # Extract preview
                        preview = resp.get("response") or resp.get("text") or resp.get("answer") or str(resp)
                        llm_results[svc_name] = {"ok": True, "preview": str(preview)[:250]}
                    except Exception as e:
                        llm_results[svc_name] = {"ok": False, "error": str(e)}
            else:
                report["llm_orchestrator_missing"] = True

            report["llms"] = llm_results

            # Ping summarizer
            try:
                summ_resp = await query_service.gateway_client.post_to_summarizer(
                    responses=["test response"],
                    original_question="health check",
                    timeout_seconds=4
                )
                summ_preview = summ_resp.get("summary") or summ_resp.get("result") or summ_resp.get("response") or str(summ_resp)
                report["summarizer"] = {"ok": True, "preview": str(summ_preview)[:250]}
            except Exception as e:
                report["summarizer"] = {"ok": False, "error": str(e)}

            return report

        # Otherwise treat as a general query
        logger.info(f"Processing general query: {str(question)[:100]}...")
        try:
            result = await asyncio.wait_for(
                query_service.query_with_llm(
                    query=question,
                    llm_service=None,  # Auto-select
                    top_k=top_k,
                    use_reranking=False,
                    headers=forward_headers,
                ),
                timeout=LLM_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            logger.error(f"General query LLM flow timed out after {LLM_TIMEOUT_SECONDS}s")
            # Return a best-effort response without LLM answer
            response = QueryResponse(
                answer="Couldn't generate LLM answer in time; retrieved contexts (if any) are available",
                query_type=QueryType.GENERAL,
                retrieved_contexts=[],
                llm_responses=[{"service": "orchestrator", "response": "", "error": f"timeout after {LLM_TIMEOUT_SECONDS}s"}],
                processing_time_seconds=0,
                timestamp=datetime.utcnow()
            )
            return response

        # Build response - simplified for now
        response_data = {
            "answer": result.get("answer", "No answer generated"),
            "query_type": QueryType.GENERAL,
            "retrieved_contexts": [],  # TODO: Map from LangChain result
            "llm_responses": [],  # TODO: Add LLM response details
            "processing_time_seconds": result.get("metadata", {}).get("processing_time_ms", 0) / 1000,
            "timestamp": datetime.utcnow()
        }

        # Add no_kb_data flag if present
        if result.get("no_kb_data"):
            response_data["no_kb_data"] = True

        response = QueryResponse(**response_data)

        logger.info(f"Query completed")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/document-specific", response_model=QueryResponse)
async def query_document_specific(
    request: DocumentSpecificQueryRequest,
    request_obj: Request,
    query_service = Depends(get_dependencies)
):
    """
    Process a document-specific query (Scenario B: Direct from document).
    
    Workflow:
    1. Generate query embedding
    2. Retrieve relevant context ONLY from specified document
    3. Generate answer directly from context
    4. Return answer (NO LLM service calls)
    
    Use this endpoint when users explicitly ask for answers "from the uploaded PDF/document/website".
    """
    try:
        logger.info(
            f"Processing document-specific query for document {request.document_id}: "
            f"{request.question[:100]}..."
        )
        incoming_auth = request_obj.headers.get("authorization")
        forward_headers = {"Authorization": incoming_auth} if incoming_auth else None
        
        # Process document-specific query using LangChain service
        result = await query_service.query_documents_only(
            query=request.question,
            document_id=request.document_id,
            top_k=request.top_k
        )
        
        # Map returned chunks into RetrievedContext items expected by the
        # response model. Each chunk in `result['chunks']` is a dict with
        # content, metadata and score (same mapping used in the other handler).
        retrieved_contexts = []
        for ch in result.get("chunks", []):
            metadata = ch.get("metadata", {}) or {}
            chunk_schema = DocumentChunkSchema(
                chunk_id=metadata.get("chunk_id", ""),
                document_id=metadata.get("document_id", request.document_id),
                content=ch.get("content") or ch.get("page_content") or "",
                chunk_index=metadata.get("chunk_index", 0),
                metadata=metadata,
            )
            retrieved_contexts.append(RetrievedContext(chunk=chunk_schema, score=ch.get("score", 0.0)))

        # Build response with retrieved contexts
        # Compose context to send to the LLM orchestrator (top-k chunks)
        context = "\n\n".join([
            f"[Chunk {i+1}]\n{rc.chunk.content}"
            for i, rc in enumerate(retrieved_contexts[:request.top_k])
        ])

        # Try to get a concise answer from the orchestrator using the context
        answer_text = result.get("answer") or "Retrieved relevant chunks (document-specific)"
        llm_responses = None
        try:
            answer_text, llm_responses = await asyncio.wait_for(
                query_service.llm_orchestrator.process_query_with_context(
                    request.question,
                    context,
                    headers=forward_headers,
                ),
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.error(f"LLM orchestration timed out after {LLM_TIMEOUT_SECONDS}s for document-specific query")
            # fallback: leave answer_text as-is or try a quick direct call
            try:
                logger.info("Attempting direct fallback call to LLM (llama) via gateway for document-specific query")
                system_instruction = (
                    "You are an assistant that MUST answer using ONLY the provided context.\n"
                    "If the answer cannot be found in the context, reply with 'I don't know based on the provided documents.'\n"
                    "Be concise and list only the requested information."
                )
                composed_prompt = f"{system_instruction}\n\nContext:\n{context}\n\nQuestion: {request.question}\nAnswer:"

                fallback_resp = await query_service.gateway_client.post_to_llm_service(
                    endpoint=query_service.settings.llama_endpoint,
                    prompt=composed_prompt,
                    context=None,
                    max_tokens=500,
                    temperature=0.0,
                    timeout_seconds=8,
                    headers=forward_headers,
                )
                fallback_text = (fallback_resp.get("response") or fallback_resp.get("text") or fallback_resp.get("answer") or str(fallback_resp))
                if fallback_text:
                    answer_text = fallback_text
                    llm_responses = [LLMResponseSchema(service="llama", response=answer_text)]
                    logger.info("Direct fallback LLM returned a response for document-specific query")
            except Exception as fe:
                logger.error(f"Direct fallback LLM call failed for document-specific query: {fe}")
        except Exception as e:
            logger.error(f"LLM orchestration failed for document-specific query: {e}")
            # try direct fallback once
            try:
                logger.info("Attempting direct fallback call to LLM (llama) via gateway after orchestrator error")
                system_instruction = (
                    "You are an assistant that MUST answer using ONLY the provided context.\n"
                    "If the answer cannot be found in the context, reply with 'I don't know based on the provided documents.'\n"
                    "Be concise and list only the requested information."
                )
                composed_prompt = f"{system_instruction}\n\nContext:\n{context}\n\nQuestion: {request.question}\nAnswer:"
                fallback_resp = await query_service.gateway_client.post_to_llm_service(
                    endpoint=query_service.settings.llama_endpoint,
                    prompt=composed_prompt,
                    context=None,
                    max_tokens=500,
                    temperature=0.0,
                    timeout_seconds=8,
                    headers=forward_headers,
                )
                fallback_text = (fallback_resp.get("response") or fallback_resp.get("text") or fallback_resp.get("answer") or str(fallback_resp))
                if fallback_text:
                    answer_text = fallback_text
                    llm_responses = [LLMResponseSchema(service="llama", response=answer_text)]
                    logger.info("Direct fallback LLM returned a response after orchestrator error")
            except Exception as fe:
                logger.error(f"Direct fallback LLM call failed after orchestrator error: {fe}")

        # Serialize LLM responses if present
        serialized_llm_responses = None
        if llm_responses:
            try:
                serialized_llm_responses = [r.dict() if hasattr(r, "dict") else dict(r) for r in llm_responses]
            except Exception:
                serialized_llm_responses = [r for r in llm_responses]

        response = QueryResponse(
            answer=answer_text,
            query_type=QueryType.DOCUMENT_SPECIFIC,
            retrieved_contexts=retrieved_contexts,
            llm_responses=serialized_llm_responses,
            processing_time_seconds=result.get("metadata", {}).get("processing_time_ms", 0) / 1000,
            timestamp=datetime.utcnow(),
            no_kb_data=result.get("no_kb_data") if isinstance(result, dict) else None,
        )

        logger.info(f"Document-specific query completed (with LLM orchestration)")
        return response
        
    except Exception as e:
        logger.error(f"Error processing document-specific query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document-specific query: {str(e)}"
        )
