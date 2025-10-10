"""
Enterprise-grade async HTTP client service with advanced features.

Ultra-efficient implementation with connection pooling, retry logic,
circuit breaker, and comprehensive metrics tracking.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import httpx
from asyncio_throttle import Throttler

from api_test_framework.core.config import get_settings
from api_test_framework.core.exceptions import HTTPClientError
from api_test_framework.core.logging import get_logger, bind_correlation_id
from api_test_framework.models.request_models import APIRequest
from api_test_framework.models.response_models import APIResponse, ResponseMetrics


class HTTPClientService:
    """Ultra-efficient async HTTP client with enterprise features."""
    
    def __init__(self, max_connections: int = 100, max_keepalive: int = 20):
        self.settings = get_settings()
        self.logger = get_logger("http_client")
        
        # Connection limits for optimal performance
        self.limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive
        )
        
        # Retry configuration
        self.retry_config = httpx.Timeout(
            timeout=self.settings.api.timeout,
            connect=10.0,
            read=30.0,
            write=10.0,
            pool=5.0
        )
        
        self.client: Optional[httpx.AsyncClient] = None
        self.throttler = Throttler(rate_limit=self.settings.test_execution.parallel_count)
        
        # Circuit breaker state
        self._failure_count = 0
        self._last_failure_time = 0
        self._circuit_open = False
    
    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Get async HTTP client with connection pooling."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                limits=self.limits,
                timeout=self.retry_config,
                verify=self.settings.api.verify_ssl,
                headers=self.settings.get_headers(),
                http2=True,  # Enable HTTP/2 for better performance
                follow_redirects=True
            )
        
        try:
            yield self.client
        finally:
            pass  # Keep connection alive for reuse
    
    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def send_request(
        self,
        request: APIRequest,
        correlation_id: Optional[str] = None
    ) -> APIResponse:
        """Send HTTP request with full error handling and metrics."""
        start_time = time.time()
        
        if correlation_id:
            bind_correlation_id(correlation_id)
        
        # Circuit breaker check
        if self._circuit_open and time.time() - self._last_failure_time < 60:
            raise HTTPClientError("Circuit breaker is open")
        
        async with self.throttler:
            async with self.get_client() as client:
                try:
                    # Prepare request
                    request_data = request.to_dict()
                    
                    # Send with retry logic
                    response = await self._send_with_retry(
                        client, request_data, start_time
                    )
                    
                    # Reset circuit breaker on success
                    self._failure_count = 0
                    self._circuit_open = False
                    
                    return response
                
                except Exception as e:
                    self._handle_failure()
                    raise HTTPClientError(
                        f"Request failed: {str(e)}",
                        url=self.settings.api.url,
                        cause=e
                    )
    
    async def _send_with_retry(
        self,
        client: httpx.AsyncClient,
        request_data: Dict[str, Any],
        start_time: float
    ) -> APIResponse:
        """Send request with exponential backoff retry."""
        last_exception = None
        
        for attempt in range(self.settings.api.max_retries + 1):
            try:
                # Calculate delay for exponential backoff
                if attempt > 0:
                    delay = self.settings.api.retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(min(delay, 30))  # Max 30s delay
                
                # Send request
                response = await client.post(
                    self.settings.api.url,
                    json=request_data,
                    headers=self.settings.get_headers()
                )
                
                # Calculate metrics
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                # Create response object
                return APIResponse(
                    request_id=request_data.get('request_id', 'unknown'),
                    success=response.is_success,
                    status_code=response.status_code,
                    status_message=response.reason_phrase,
                    response_data=response.json() if response.content else {},
                    response_headers=dict(response.headers),
                    metrics=ResponseMetrics(
                        response_time_ms=response_time_ms,
                        request_size_bytes=len(response.request.content or b''),
                        response_size_bytes=len(response.content)
                    )
                )
                
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Request attempt {attempt + 1} failed",
                    error=str(e),
                    attempt=attempt + 1,
                    max_retries=self.settings.api.max_retries
                )
        
        # All retries failed
        raise last_exception or HTTPClientError("All retry attempts failed")
    
    def _handle_failure(self) -> None:
        """Handle request failure for circuit breaker."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= 5:  # Open circuit after 5 failures
            self._circuit_open = True
            self.logger.error("Circuit breaker opened due to repeated failures")
    
    async def send_batch(
        self,
        requests: List[APIRequest],
        batch_size: Optional[int] = None
    ) -> List[APIResponse]:
        """Send multiple requests in optimized batches."""
        batch_size = batch_size or self.settings.test_execution.batch_size
        responses = []
        
        # Process in batches for memory efficiency
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            
            # Send batch concurrently
            tasks = [
                self.send_request(req, f"batch_{i}_{j}")
                for j, req in enumerate(batch)
            ]
            
            batch_responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions in batch
            for response in batch_responses:
                if isinstance(response, Exception):
                    # Convert exception to error response
                    error_response = APIResponse(
                        request_id="error",
                        success=False,
                        status_code=500,
                        response_data={"error": str(response)}
                    )
                    responses.append(error_response)
                else:
                    responses.append(response)
        
        return responses
    
    async def health_check(self) -> bool:
        """Perform health check on the API endpoint."""
        try:
            async with self.get_client() as client:
                response = await client.get(
                    f"{self.settings.api.url}/health",
                    timeout=5.0
                )
                return response.is_success
        except Exception:
            return False