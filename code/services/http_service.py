"""
Asynchronous HTTP service for API testing with retry logic and performance tracking.

This service provides:
- Async HTTP requests using aiohttp
- Automatic retry with exponential backoff
- Connection pooling and session management
- Performance metrics tracking
- Batch request processing
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import aiohttp
from aiohttp import ClientTimeout, TCPConnector
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from ..config.settings import get_config
from ..core.constants import RESPONSE_FILE_SUFFIX, RETRY_STATUS_CODES
from ..core.exceptions import HTTPRequestError, ParallelExecutionError
from ..core.models import RequestResult, BatchRequestResult
from ..utils.file_handler import FileHandler, JSONHandler
from ..utils.logger import get_logger, PerformanceLogger


class AsyncHTTPClient:
    """
    Asynchronous HTTP client with connection pooling and retry logic.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        max_connections: int = 100,
        timeout: int = 30
    ):
        """
        Initialize async HTTP client.
        
        Args:
            logger: Logger instance
            max_connections: Maximum number of connections
            timeout: Request timeout in seconds
        """
        self.logger = logger or get_logger(__name__)
        self.config = get_config()
        self.max_connections = max_connections
        self.timeout = ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> "AsyncHTTPClient":
        """Async context manager entry."""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self._close_session()
    
    async def _create_session(self) -> None:
        """Create aiohttp client session with connection pooling."""
        if self._session is None or self._session.closed:
            connector = TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections // 2,
                ttl_dns_cache=300
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=self._get_base_headers()
            )
            
            self.logger.debug("Created new aiohttp session")
    
    async def _close_session(self) -> None:
        """Close aiohttp client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self.logger.debug("Closed aiohttp session")
    
    def _get_base_headers(self) -> Dict[str, str]:
        """Get base HTTP headers from configuration."""
        return self.config.get_headers()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((
            aiohttp.ClientConnectionError,
            aiohttp.ServerTimeoutError,
            asyncio.TimeoutError
        )),
        before_sleep=before_sleep_log(get_logger(__name__), logging.WARNING)
    )
    async def _send_request_with_retry(
        self,
        url: str,
        json_data: str,
        headers: Dict[str, str]
    ) -> tuple[int, str, float]:
        """
        Send HTTP request with automatic retry.
        
        Args:
            url: Request URL
            json_data: JSON payload as string
            headers: Request headers
            
        Returns:
            Tuple of (status_code, response_text, response_time)
            
        Raises:
            HTTPRequestError: If request fails after retries
        """
        if self._session is None:
            await self._create_session()
        
        start_time = time.time()
        
        try:
            async with self._session.post(
                url,
                data=json_data,
                headers=headers,
                ssl=self.config.api.verify_ssl
            ) as response:
                response_text = await response.text()
                response_time = time.time() - start_time
                
                # Check if status code indicates we should retry
                if response.status in RETRY_STATUS_CODES:
                    raise aiohttp.ClientConnectionError(
                        f"Retryable status code: {response.status}"
                    )
                
                return response.status, response_text, response_time
                
        except asyncio.TimeoutError as e:
            response_time = time.time() - start_time
            raise HTTPRequestError(
                "Request timeout",
                url=url,
                method="POST",
                details={"timeout": self.timeout.total},
                original_error=e
            )
        except Exception as e:
            response_time = time.time() - start_time
            if isinstance(e, HTTPRequestError):
                raise
            raise HTTPRequestError(
                f"Request failed: {str(e)}",
                url=url,
                method="POST",
                original_error=e
            )
    
    async def send_request(
        self,
        file_path: Path,
        json_data: str,
        output_folder: Path
    ) -> RequestResult:
        """
        Send a single API request and save response.
        
        Args:
            file_path: Path to the request JSON file
            json_data: JSON payload as string
            output_folder: Folder to save response
            
        Returns:
            RequestResult with response details
        """
        start_time = time.time()
        
        try:
            # Add think time if configured
            if self.config.test_execution.think_time > 0:
                await asyncio.sleep(self.config.test_execution.think_time)
            
            # Prepare headers with content length
            headers = self._get_base_headers()
            headers["Content-Length"] = str(len(json_data))
            
            # Send request with retry
            status_code, response_text, response_time = await self._send_request_with_retry(
                url=str(self.config.api.url),
                json_data=json_data,
                headers=headers
            )
            
            # Save response to file
            response_file = output_folder / f"{file_path.stem}{RESPONSE_FILE_SUFFIX}.json"
            await JSONHandler.write_json_async(response_file, response_text if response_text else {})
            
            # Determine success
            success = 200 <= status_code < 300
            
            # Log request details
            self.logger.info(
                f"Request: {file_path.name} | Status: {status_code} | Time: {response_time:.2f}s"
            )
            
            return RequestResult(
                file_path=str(file_path),
                status_code=status_code,
                response_text=response_text,
                success=success,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
        except HTTPRequestError as e:
            response_time = time.time() - start_time
            self.logger.error(f"Request failed: {file_path.name} - {e}")
            
            return RequestResult(
                file_path=str(file_path),
                status_code=None,
                response_text="",
                success=False,
                error_message=str(e),
                response_time=response_time,
                timestamp=datetime.now()
            )
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Unexpected error: {file_path.name} - {e}")
            
            return RequestResult(
                file_path=str(file_path),
                status_code=None,
                response_text="",
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                response_time=response_time,
                timestamp=datetime.now()
            )


class HTTPService:
    """
    Main HTTP service for executing API tests in parallel.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize HTTP service.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or get_logger(__name__)
        self.config = get_config()
    
    async def _load_json_files(self, json_folder: Path) -> Dict[Path, str]:
        """
        Load all JSON files from folder asynchronously.
        
        Args:
            json_folder: Folder containing JSON files
            
        Returns:
            Dictionary mapping file paths to JSON content
            
        Raises:
            ParallelExecutionError: If file loading fails
        """
        try:
            # Get all JSON files
            json_files = FileHandler.list_files(json_folder, "*.json")
            
            if not json_files:
                raise ParallelExecutionError(
                    f"No JSON files found in {json_folder}",
                    details={"folder": str(json_folder)}
                )
            
            self.logger.info(f"Loading {len(json_files)} JSON files...")
            
            # Load all files asynchronously
            json_data_dict = {}
            
            async def load_file(file_path: Path) -> tuple[Path, str]:
                content = await FileHandler.read_text_file_async(file_path)
                return file_path, content
            
            tasks = [load_file(file_path) for file_path in json_files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Failed to load file: {result}")
                    continue
                
                file_path, content = result
                json_data_dict[file_path] = content
            
            if not json_data_dict:
                raise ParallelExecutionError(
                    "Failed to load any JSON files",
                    details={"folder": str(json_folder)}
                )
            
            self.logger.info(f"Successfully loaded {len(json_data_dict)} JSON files")
            return json_data_dict
            
        except Exception as e:
            if isinstance(e, ParallelExecutionError):
                raise
            raise ParallelExecutionError(
                "Failed to load JSON files",
                details={"folder": str(json_folder)},
                original_error=e
            )
    
    async def _execute_requests_batch(
        self,
        client: AsyncHTTPClient,
        json_data_dict: Dict[Path, str],
        output_folder: Path,
        batch_size: int
    ) -> List[RequestResult]:
        """
        Execute requests in batches to control concurrency.
        
        Args:
            client: HTTP client instance
            json_data_dict: Dictionary of file paths to JSON content
            output_folder: Folder to save responses
            batch_size: Number of concurrent requests
            
        Returns:
            List of request results
        """
        all_results = []
        items = list(json_data_dict.items())
        total_requests = len(items)
        
        # Process in batches
        for i in range(0, total_requests, batch_size):
            batch = items[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_requests + batch_size - 1) // batch_size
            
            self.logger.info(
                f"Processing batch {batch_num}/{total_batches} "
                f"({len(batch)} requests)"
            )
            
            # Create tasks for batch
            tasks = [
                client.send_request(file_path, json_data, output_folder)
                for file_path, json_data in batch
            ]
            
            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch request failed: {result}")
                    # Create failed result
                    all_results.append(RequestResult(
                        file_path="unknown",
                        status_code=None,
                        response_text="",
                        success=False,
                        error_message=str(result),
                        response_time=0.0,
                        timestamp=datetime.now()
                    ))
                else:
                    all_results.append(result)
            
            # Progress update
            completed = len(all_results)
            progress = (completed / total_requests) * 100
            self.logger.info(
                f"Progress: {completed}/{total_requests} ({progress:.1f}%)"
            )
        
        return all_results
    
    async def execute_parallel_tests(
        self,
        json_folder: Optional[Path] = None,
        output_folder: Optional[Path] = None
    ) -> BatchRequestResult:
        """
        Execute API tests in parallel.
        
        Args:
            json_folder: Folder containing JSON request files (uses config if None)
            output_folder: Folder to save responses (uses config if None)
            
        Returns:
            BatchRequestResult with all request results and statistics
            
        Raises:
            ParallelExecutionError: If execution fails
        """
        try:
            with PerformanceLogger(self.logger, "Execute Parallel API Tests"):
                # Use config paths if not provided
                if json_folder is None:
                    json_folder = self.config.paths.output_processed
                if output_folder is None:
                    # Create timestamped output folder
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_folder = self.config.paths.output_responses / timestamp
                
                # Ensure output folder exists
                FileHandler.ensure_directory(output_folder)
                
                # Load JSON files
                json_data_dict = await self._load_json_files(json_folder)
                
                # Execute requests
                start_time = time.time()
                
                async with AsyncHTTPClient(
                    logger=self.logger,
                    max_connections=self.config.test_execution.parallel_workers,
                    timeout=self.config.api.timeout
                ) as client:
                    results = await self._execute_requests_batch(
                        client=client,
                        json_data_dict=json_data_dict,
                        output_folder=output_folder,
                        batch_size=self.config.test_execution.batch_size
                    )
                
                total_execution_time = time.time() - start_time
                
                # Calculate statistics
                total_requests = len(results)
                successful_requests = sum(1 for r in results if r.success)
                failed_requests = total_requests - successful_requests
                
                response_times = [r.response_time for r in results if r.response_time > 0]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
                
                # Log summary
                self.logger.info(
                    f"Parallel tests completed: {successful_requests}/{total_requests} successful"
                )
                self.logger.info(
                    f"Average response time: {avg_response_time:.2f}s"
                )
                self.logger.info(
                    f"Total execution time: {total_execution_time:.2f}s"
                )
                
                return BatchRequestResult(
                    results=results,
                    total_requests=total_requests,
                    successful_requests=successful_requests,
                    failed_requests=failed_requests,
                    avg_response_time=avg_response_time,
                    total_execution_time=total_execution_time
                )
                
        except Exception as e:
            if isinstance(e, ParallelExecutionError):
                raise
            raise ParallelExecutionError(
                "Failed to execute parallel tests",
                details={
                    "json_folder": str(json_folder),
                    "output_folder": str(output_folder)
                },
                original_error=e
            )
    
    def run_tests(
        self,
        json_folder: Optional[Path] = None,
        output_folder: Optional[Path] = None
    ) -> BatchRequestResult:
        """
        Run parallel API tests (synchronous wrapper for async method).
        
        Args:
            json_folder: Folder containing JSON request files
            output_folder: Folder to save responses
            
        Returns:
            BatchRequestResult with all request results
        """
        return asyncio.run(
            self.execute_parallel_tests(json_folder, output_folder)
        )