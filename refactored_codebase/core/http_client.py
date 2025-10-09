"""
Enterprise HTTP client with advanced features.

This module provides a robust HTTP client with connection pooling,
retry logic, timeout handling, and comprehensive error management.
"""

import time
import json
from typing import Dict, Any, Optional, Union, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from refactored_codebase.config.models import APIConfig
from refactored_codebase.utils.logging import get_logger


class RequestMethod(str, Enum):
    """HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class HTTPResponse:
    """HTTP response wrapper with additional metadata."""
    status_code: int
    headers: Dict[str, str]
    content: bytes
    text: str
    json_data: Optional[Dict[str, Any]]
    elapsed_time: float
    url: str
    request_id: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return 200 <= self.status_code < 300
    
    @property
    def is_client_error(self) -> bool:
        """Check if response indicates client error."""
        return 400 <= self.status_code < 500
    
    @property
    def is_server_error(self) -> bool:
        """Check if response indicates server error."""
        return 500 <= self.status_code < 600
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization."""
        return {
            "status_code": self.status_code,
            "headers": dict(self.headers),
            "text": self.text,
            "json_data": self.json_data,
            "elapsed_time": self.elapsed_time,
            "url": self.url,
            "request_id": self.request_id,
            "is_success": self.is_success
        }


class HTTPClientError(Exception):
    """Base exception for HTTP client errors."""
    pass


class ConnectionError(HTTPClientError):
    """Connection-related errors."""
    pass


class TimeoutError(HTTPClientError):
    """Timeout-related errors."""
    pass


class RetryExhaustedError(HTTPClientError):
    """Retry attempts exhausted."""
    pass


class HTTPClient:
    """
    Enterprise HTTP client with advanced features.
    
    Features:
    - Connection pooling and keep-alive
    - Configurable retry logic with exponential backoff
    - Request/response logging and metrics
    - Timeout handling
    - SSL verification control
    - Request ID tracking
    - Context manager support
    """
    
    def __init__(self, config: APIConfig, session: Optional[requests.Session] = None):
        """
        Initialize HTTP client.
        
        Args:
            config: API configuration
            session: Optional pre-configured session
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize session
        self.session = session or self._create_session()
        
        # Request counter for tracking
        self._request_counter = 0
        
        self.logger.info(f"HTTP Client initialized for {config.url}")
    
    def _create_session(self) -> requests.Session:
        """Create and configure HTTP session."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # Configure HTTP adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
            pool_block=False
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default timeout
        session.timeout = self.config.timeout
        
        # Configure SSL verification
        session.verify = self.config.verify_ssl
        
        return session
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        self._request_counter += 1
        import uuid
        return f"req_{self._request_counter}_{uuid.uuid4().hex[:8]}"
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare request headers."""
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Enterprise-API-Testing-Framework/2.0",
            "Host": self.config.host
        }
        
        if headers:
            default_headers.update(headers)
        
        return default_headers
    
    def _log_request(self, method: str, url: str, headers: Dict[str, str], 
                    data: Optional[str], request_id: str) -> None:
        """Log request details."""
        self.logger.debug(
            f"Request {request_id}: {method} {url}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "headers": headers,
                "data_length": len(data) if data else 0
            }
        )
    
    def _log_response(self, response: HTTPResponse) -> None:
        """Log response details."""
        self.logger.debug(
            f"Response {response.request_id}: {response.status_code} "
            f"({response.elapsed_time:.3f}s)",
            extra={
                "request_id": response.request_id,
                "status_code": response.status_code,
                "elapsed_time": response.elapsed_time,
                "response_size": len(response.content)
            }
        )
    
    def _make_request(
        self,
        method: RequestMethod,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[str, Dict[str, Any]]] = None,
        params: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> HTTPResponse:
        """
        Make HTTP request with error handling and logging.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            data: Request body data
            params: URL parameters
            timeout: Request timeout
            
        Returns:
            HTTPResponse object
            
        Raises:
            HTTPClientError: For various HTTP client errors
        """
        request_id = self._generate_request_id()
        prepared_headers = self._prepare_headers(headers)
        
        # Prepare request data
        if isinstance(data, dict):
            json_data = data
            request_data = json.dumps(data)
        else:
            json_data = None
            request_data = data
        
        # Log request
        self._log_request(method.value, url, prepared_headers, request_data, request_id)
        
        try:
            start_time = time.time()
            
            # Make request
            response = self.session.request(
                method=method.value,
                url=url,
                headers=prepared_headers,
                data=request_data,
                json=json_data if json_data else None,
                params=params,
                timeout=timeout or self.config.timeout
            )
            
            elapsed_time = time.time() - start_time
            
            # Parse JSON response if possible
            try:
                json_response = response.json() if response.content else None
            except (json.JSONDecodeError, ValueError):
                json_response = None
            
            # Create response object
            http_response = HTTPResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                content=response.content,
                text=response.text,
                json_data=json_response,
                elapsed_time=elapsed_time,
                url=response.url,
                request_id=request_id
            )
            
            # Log response
            self._log_response(http_response)
            
            return http_response
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Request {request_id} timed out: {e}")
            raise TimeoutError(f"Request timed out after {timeout or self.config.timeout}s") from e
        
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Request {request_id} connection error: {e}")
            raise ConnectionError(f"Connection error: {e}") from e
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request {request_id} failed: {e}")
            raise HTTPClientError(f"Request failed: {e}") from e
    
    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> HTTPResponse:
        """Make GET request."""
        return self._make_request(RequestMethod.GET, url, headers, None, params, timeout)
    
    def post(
        self,
        url: str,
        data: Optional[Union[str, Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> HTTPResponse:
        """Make POST request."""
        return self._make_request(RequestMethod.POST, url, headers, data, None, timeout)
    
    def put(
        self,
        url: str,
        data: Optional[Union[str, Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> HTTPResponse:
        """Make PUT request."""
        return self._make_request(RequestMethod.PUT, url, headers, data, None, timeout)
    
    def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> HTTPResponse:
        """Make DELETE request."""
        return self._make_request(RequestMethod.DELETE, url, headers, None, None, timeout)
    
    def send_json_request(
        self,
        json_data: Dict[str, Any],
        method: RequestMethod = RequestMethod.POST,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> HTTPResponse:
        """
        Send JSON request to configured API endpoint.
        
        Args:
            json_data: JSON data to send
            method: HTTP method (default: POST)
            url: Override URL (default: use config URL)
            headers: Additional headers
            timeout: Request timeout
            
        Returns:
            HTTPResponse object
        """
        target_url = url or str(self.config.url)
        return self._make_request(method, target_url, headers, json_data, None, timeout)
    
    @contextmanager
    def batch_requests(self):
        """Context manager for batch requests with session reuse."""
        try:
            self.logger.debug("Starting batch request session")
            yield self
        finally:
            self.logger.debug("Ending batch request session")
    
    def close(self) -> None:
        """Close HTTP session and cleanup resources."""
        if self.session:
            self.session.close()
            self.logger.info("HTTP client session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            "total_requests": self._request_counter,
            "config": {
                "url": str(self.config.url),
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
                "verify_ssl": self.config.verify_ssl
            }
        }