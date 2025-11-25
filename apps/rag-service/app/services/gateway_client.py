import httpx
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import Settings

logger = logging.getLogger(__name__)


class GatewayClient:
    """HTTP client for communicating with the NestJS Gateway service."""
    
    def __init__(self, settings: Settings):
        """Initialize gateway client."""
        self.settings = settings
        self.base_url = settings.gateway_service_url.rstrip('/')
        self.timeout = settings.request_timeout
        self.max_retries = settings.max_retries
        
        logger.info(f"Initialized Gateway client with base URL: {self.base_url}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError),
        reraise=True
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to gateway with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Endpoint path (will be appended to base URL)
            data: Request body data
            headers: Additional headers
        
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if headers:
            default_headers.update(headers)

        # Masked logging for Authorization header to avoid leaking tokens in logs
        try:
            auth_header = default_headers.get("Authorization") or default_headers.get("authorization")
            if auth_header:
                masked = auth_header[:8] + "..." if len(auth_header) > 12 else "[REDACTED]"
                logger.debug(f"GatewayClient sending Authorization header: {masked}")
        except Exception:
            pass

        # Inject service-level Authorization header if gateway requires it
        if "authorization" not in {k.lower() for k in default_headers.keys()}:
            token = getattr(self.settings, "gateway_service_token", None)
            if token:
                default_headers["Authorization"] = f"Bearer {token}"
        
        try:
            client_timeout = timeout_seconds or self.timeout
            async with httpx.AsyncClient(timeout=client_timeout) as client:
                logger.debug(f"Making {method} request to {url} (timeout={client_timeout}s)")
                start_ts = __import__("time").time()
                
                if method.upper() == "GET":
                    response = await client.get(url, headers=default_headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, headers=default_headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=default_headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                elapsed = __import__("time").time() - start_ts
                # Try to parse JSON safely for logging; avoid huge dumps
                resp_text = None
                try:
                    resp_json = response.json()
                    import json as _json
                    resp_text = _json.dumps(resp_json)[:2000]
                except Exception:
                    resp_text = (response.text or "")[:1000]

                logger.info(f"Request to {url} succeeded status={response.status_code} elapsed={elapsed:.2f}s body_preview={resp_text}")
                return response.json()
                
        except httpx.HTTPStatusError as e:
            status = getattr(e.response, 'status_code', None)
            body = None
            try:
                body = e.response.text
            except Exception:
                body = None
            logger.error(f"HTTP error {status} for {url}: {e} body_preview={str(body)[:1000]}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise
    
    async def post_to_llm_service(
        self,
        endpoint: str,
        prompt: str,
        context: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send request to an LLM service via gateway.
        
        Args:
            endpoint: LLM service endpoint
            prompt: The prompt/question
            context: Optional context to include
            **kwargs: Additional parameters
        
        Returns:
            LLM service response
        """
        data = {
            "prompt": prompt,
            "context": context,
            **kwargs
        }
        
        return await self._make_request("POST", endpoint, data=data, headers=headers, timeout_seconds=timeout_seconds)
    
    async def post_to_summarizer(
        self,
        responses: list,
        original_question: str,
        timeout_seconds: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send responses to summarizer service via gateway.
        
        Args:
            responses: List of LLM responses to summarize
            original_question: The original user question
            **kwargs: Additional parameters
        
        Returns:
            Summarizer service response
        """
        data = {
            "responses": responses,
            "original_question": original_question,
            **kwargs
        }
        
        return await self._make_request(
            "POST",
            self.settings.summarizer_endpoint,
            data=data,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )
    
    async def validate_auth(self, token: str) -> Dict[str, Any]:
        """
        Validate authentication token via gateway.
        
        Args:
            token: Auth token to validate
        
        Returns:
            Auth validation response
        """
        headers = {"Authorization": f"Bearer {token}"}
        return await self._make_request(
            "GET",
            self.settings.auth_endpoint,
            headers=headers
        )
    
    async def health_check(self) -> bool:
        """
        Check if gateway is reachable.
        
        Returns:
            True if gateway is healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Gateway health check failed: {e}")
            return False


# Global gateway client instance
_gateway_client: Optional[GatewayClient] = None


def get_gateway_client(settings: Settings) -> GatewayClient:
    """Get or create the global gateway client instance."""
    global _gateway_client
    if _gateway_client is None:
        _gateway_client = GatewayClient(settings)
    return _gateway_client
