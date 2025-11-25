import asyncio
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

from app.config import Settings
from app.services.gateway_client import GatewayClient
from app.models.schemas import LLMResponse

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """Orchestrates calls to multiple LLM services via the gateway."""
    
    def __init__(self, settings: Settings, gateway_client: GatewayClient):
        """Initialize LLM orchestrator."""
        self.settings = settings
        self.gateway_client = gateway_client
        
        # LLM service endpoints
        self.llm_endpoints = {
            "gemini": settings.gemini_endpoint,
            "llama": settings.llama_endpoint,
            "cohere": settings.cohere_endpoint
        }
        
        logger.info(f"Initialized LLM Orchestrator with services: {list(self.llm_endpoints.keys())}")
    
    async def _call_single_llm(
        self,
        service_name: str,
        endpoint: str,
        prompt: str,
        context: str,
        headers: Dict[str, str] | None = None,
    ) -> LLMResponse:
        """
        Call a single LLM service.
        
        Args:
            service_name: Name of the service (gemini, llama, cohere)
            endpoint: Service endpoint
            prompt: User question
            context: Retrieved context
        
        Returns:
            LLM response
        """
        try:
            logger.info(f"Calling {service_name} service...")
            
            # Make request via gateway with a short timeout to fail fast
            response = await self.gateway_client.post_to_llm_service(
                endpoint=endpoint,
                prompt=prompt,
                context=context,
                max_tokens=500,
                temperature=0.7,
                timeout_seconds=8,
                headers=headers,
            )
            
            # Log raw response preview for diagnostics
            try:
                import json as _json
                preview = _json.dumps(response)[:2000]
            except Exception:
                preview = str(response)[:1000]
            logger.info(f"{service_name} responded successfully (preview): {preview}")

            # Extract response text (adjust based on actual API response format)
            response_text = response.get("response") or response.get("text") or response.get("answer") or str(response)
            
            return LLMResponse(
                service=service_name,
                response=response_text,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error calling {service_name}: {e}")
            return LLMResponse(
                service=service_name,
                response="",
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def query_all_llms(
        self,
        question: str,
        context: str,
        headers: Dict[str, str] | None = None,
    ) -> List[LLMResponse]:
        """
        Query all LLM services in parallel.
        
        Args:
            question: User question
            context: Retrieved context from vector DB
        
        Returns:
            List of responses from all LLM services
        """
        logger.info(f"Querying all LLM services for question: {question[:100]}... (fast-first strategy)")

        # Create tasks for all LLM calls keyed by service name
        tasks = {}
        for service_name, endpoint in self.llm_endpoints.items():
            tasks[asyncio.create_task(self._call_single_llm(service_name, endpoint, question, context, headers=headers))] = service_name

        if not tasks:
            return []

        # Wait for the first completed task that returns a non-empty response.
        pending = set(tasks.keys())
        finished_responses: List[LLMResponse] = []
        timeout_seconds = 12
        start_time = __import__("time").time()

        while pending and (__import__("time").time() - start_time) < timeout_seconds:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED, timeout=timeout_seconds)
            if not done:
                break

            for d in done:
                try:
                    resp = d.result()
                except Exception as e:
                    svc = tasks.get(d, "unknown")
                    logger.error(f"Exception from {svc}: {e}")
                    finished_responses.append(LLMResponse(service=svc, response="", error=str(e), timestamp=datetime.utcnow()))
                    continue

                if isinstance(resp, LLMResponse):
                    finished_responses.append(resp)
                    # If this response contains a non-empty successful text, return it immediately
                    if resp.response and not resp.error:
                        # Cancel any remaining pending tasks
                        for p in pending:
                            p.cancel()
                        logger.info(f"Fast-first: returning response from {resp.service}")
                        return [resp]

        # If we get here, no fast non-empty response was found; gather remaining results
        if pending:
            try:
                more = await asyncio.gather(*pending, return_exceptions=True)
            except Exception:
                more = []

            for i, r in enumerate(more):
                svc = list(self.llm_endpoints.keys())[i] if i < len(self.llm_endpoints) else "unknown"
                if isinstance(r, Exception):
                    logger.error(f"Exception from {svc}: {r}")
                    finished_responses.append(LLMResponse(service=svc, response="", error=str(r), timestamp=datetime.utcnow()))
                elif isinstance(r, LLMResponse):
                    finished_responses.append(r)

        logger.info(f"Received {len(finished_responses)} LLM responses (post-wait)")
        return finished_responses
    
    async def summarize_responses(
        self,
        llm_responses: List[LLMResponse],
        original_question: str,
        headers: Dict[str, str] | None = None,
    ) -> str:
        """
        Send all LLM responses to the summarizer service.
        
        Args:
            llm_responses: List of responses from LLM services
            original_question: Original user question
        
        Returns:
            Summarized response
        """
        try:
            logger.info("Sending responses to summarizer service...")
            
            # Extract response texts (only from successful responses)
            response_texts = [
                f"{resp.service}: {resp.response}"
                for resp in llm_responses
                if resp.response and not resp.error
            ]

            # If no valid responses found, attempt to salvage any non-empty
            # text even if the response carried an error marker, and then
            # as a last resort try to re-call each LLM endpoint directly
            # (this helps diagnose transient gateway forwarding issues).
            if not response_texts:
                logger.warning("No valid responses to summarize from initial LLM calls; attempting fallback collection")
                # Include any non-empty responses even if error flag set
                fallback_texts = [
                    f"{resp.service}: {resp.response}"
                    for resp in llm_responses
                    if resp.response
                ]
                if fallback_texts:
                    response_texts = fallback_texts

            # As a final fallback, attempt direct calls to each configured LLM
            # endpoint via the gateway client so we can capture raw outputs.
            if not response_texts:
                logger.info("Performing direct retry calls to LLM endpoints via gateway client")
                direct_texts = []
                for svc_name, endpoint in self.llm_endpoints.items():
                    try:
                        logger.debug(f"Direct call to {svc_name} @ {endpoint}")
                        resp = await self.gateway_client.post_to_llm_service(
                            endpoint=endpoint,
                            prompt=original_question,
                            context=None,
                            max_tokens=500,
                            temperature=0.7,
                            headers=headers,
                        )
                        # Try to extract a textual field
                        text = resp.get("response") or resp.get("text") or resp.get("answer") or str(resp)
                        if text:
                            direct_texts.append(f"{svc_name}: {text}")
                    except Exception as e:
                        logger.error(f"Direct call to {svc_name} failed: {e}")

                if direct_texts:
                    response_texts = direct_texts

            if not response_texts:
                logger.warning("No valid responses after fallback attempts")
                return "I apologize, but I couldn't generate a response from the available services."
            
            # Call summarizer via gateway
            summary_response = await self.gateway_client.post_to_summarizer(
                responses=response_texts,
                original_question=original_question,
                headers=headers,
            )
            
            # Extract summary (adjust based on actual API response format)
            summary = (
                summary_response.get("summary") or 
                summary_response.get("result") or 
                summary_response.get("response") or
                str(summary_response)
            )
            
            logger.info("Received summary from summarizer service")

            # If summarizer returned an apology or no useful content, try a
            # direct single-LLM fallback (fast) to salvage an answer.
            if not summary or "I apologize" in str(summary) or "couldn't generate" in str(summary) or "could not generate" in str(summary):
                logger.warning("Summarizer returned no useful summary; attempting direct single-LLM fallback (llama)")
                try:
                    # Build a strict prompt instructing the LLM to answer only
                    # from the provided contexts. This reduces hallucination and
                    # increases the chance the model returns a concrete answer
                    # derived from the retrieved chunks.
                    context_blob = "\n\n".join(response_texts) if response_texts else None
                    if not context_blob:
                        # If no response_texts were available, try to use any
                        # fallback/direct_texts gathered earlier (caller may
                        # pass those via response_texts).
                        context_blob = None

                    system_instruction = (
                        "You are an assistant that MUST answer using ONLY the provided context.\n"
                        "If the answer cannot be found in the context, reply with 'I don't know based on the provided documents.'\n"
                        "Be concise and list only the requested information."
                    )

                    composed_prompt = system_instruction + "\n\n"
                    if context_blob:
                        composed_prompt += f"Context:\n{context_blob}\n\n"
                    composed_prompt += f"Question: {original_question}\nAnswer:"

                    # Direct call to single preferred LLM (llama) via gateway with short timeout
                    fallback_resp = await self.gateway_client.post_to_llm_service(
                        endpoint=self.settings.llama_endpoint,
                        prompt=composed_prompt,
                        context=None,
                        max_tokens=500,
                        temperature=0.0,
                        timeout_seconds=12,
                        headers=headers,
                    )
                    fallback_text = (fallback_resp.get("response") or fallback_resp.get("text") or fallback_resp.get("answer") or str(fallback_resp))
                    if fallback_text:
                        logger.info("Direct fallback LLM returned a response from llama")
                        return fallback_text
                except Exception as e:
                    logger.error(f"Direct fallback to llama failed: {e}")

            return summary
            
        except Exception as e:
            logger.error(f"Error calling summarizer: {e}")
            # Fall back to returning the first successful response
            for resp in llm_responses:
                if resp.response and not resp.error:
                    return f"[Summarizer unavailable] {resp.service} response: {resp.response}"
            
            return "I apologize, but I encountered an error processing the responses."
    
    async def process_query_with_context(
        self,
        question: str,
        context: str,
        headers: Dict[str, str] | None = None,
    ) -> Tuple[str, List[LLMResponse]]:
        """
        Complete workflow: Query all LLMs and summarize.
        
        Args:
            question: User question
            context: Retrieved context
        
        Returns:
            Tuple of (summarized_answer, list_of_llm_responses)
        """
        # Query all LLM services (fast-first)
        llm_responses = await self.query_all_llms(question, context, headers=headers)

        # If we received at least one direct LLM response with content, return it immediately
        for resp in llm_responses:
            if resp and resp.response and not resp.error:
                # Prefer returning the raw LLM text as the final answer to reduce latency
                logger.info(f"Using direct LLM response from {resp.service} as final answer")
                return resp.response, llm_responses

        # Otherwise fall back to summarizing collected responses
        final_answer = await self.summarize_responses(llm_responses, question, headers=headers)
        return final_answer, llm_responses


# Global orchestrator instance
_llm_orchestrator: "LLMOrchestrator | None" = None


def get_llm_orchestrator(settings: Settings, gateway_client: GatewayClient) -> LLMOrchestrator:
    """Get or create the global LLM orchestrator instance."""
    global _llm_orchestrator
    if _llm_orchestrator is None:
        _llm_orchestrator = LLMOrchestrator(settings, gateway_client)
    return _llm_orchestrator
