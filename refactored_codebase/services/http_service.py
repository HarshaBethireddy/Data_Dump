"""
HTTP service for API testing with connection pooling and retry logic.

Provides robust HTTP client functionality with parallel execution,
retry mechanisms, and comprehensive error handling.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..core.config import ConfigurationManager


@dataclass
class RequestResult:
    """Result of an HTTP request execution."""
    file_name: str
    success: bool
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None


class HTTPClient:
    """
    Enterprise-grade HTTP client with connection pooling and retry logic.
    
    Provides robust HTTP communication with automatic retries,
    connection pooling, and comprehensive error handling.
    """
    
    def __init__(self, 
                 config_manager: ConfigurationManager,
                 logger: logging.Logger):
        """
        Initialize HTTP client.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self.config_manager = config_manager
        self.logger = logger
        self.api_config = config_manager.api_config
        self.test_config = config_manager.test_config
        
        # Create session with connection pooling
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create configured requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.api_config.max_retries,
            backoff_factor=self.api_config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # Configure adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.test_config.parallel_count,
            pool_maxsize=self.test_config.parallel_count * 2
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update(self.config_manager.get_headers())
        
        return session
    
    def send_request(self, 
                    request_data: Dict[str, Any], 
                    file_name: str) -> RequestResult:
        """
        Send HTTP request with error handling and metrics collection.
        
        Args:
            request_data: JSON data to send
            file_name: Name of the source file
            
        Returns:
            RequestResult containing execution details
        """
        start_time = time.time()
        
        try:
            self.logger.debug(f"Sending request for {file_name}")
            
            # Apply think time before request
            if self.test_config.think_time > 0:
                time.sleep(self.test_config.think_time)
            
            # Send POST request
            response = self.session.post(
                self.api_config.url,
                json=request_data,
                timeout=self.api_config.timeout,
                verify=self.api_config.verify_ssl
            )
            
            response_time = time.time() - start_time
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            # Determine success based on status code
            success = 200 <= response.status_code < 300
            
            result = RequestResult(
                file_name=file_name,
                success=success,
                status_code=response.status_code,
                response_time=response_time,
                response_data=response_data,
                request_data=request_data
            )
            
            if success:
                self.logger.debug(f"Request successful for {file_name} "
                                f"(Status: {response.status_code}, Time: {response_time:.2f}s)")
            else:
                self.logger.warning(f"Request failed for {file_name} "
                                  f"(Status: {response.status_code}, Time: {response_time:.2f}s)")
            
            return result
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            error_msg = f"Request timeout after {self.api_config.timeout}s"
            self.logger.error(f"Timeout for {file_name}: {error_msg}")
            
            return RequestResult(
                file_name=file_name,
                success=False,
                response_time=response_time,
                error_message=error_msg,
                request_data=request_data
            )
            
        except requests.exceptions.ConnectionError as e:
            response_time = time.time() - start_time
            error_msg = f"Connection error: {str(e)}"
            self.logger.error(f"Connection error for {file_name}: {error_msg}")
            
            return RequestResult(
                file_name=file_name,
                success=False,
                response_time=response_time,
                error_message=error_msg,
                request_data=request_data
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error for {file_name}: {error_msg}")
            
            return RequestResult(
                file_name=file_name,
                success=False,
                response_time=response_time,
                error_message=error_msg,
                request_data=request_data
            )
    
    def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        if self.session:
            self.session.close()


class HTTPService:
    """
    High-level HTTP service for parallel API testing.
    
    Orchestrates parallel HTTP requests and manages response storage.
    """
    
    def __init__(self, 
                 config_manager: ConfigurationManager,
                 logger: logging.Logger):
        """
        Initialize HTTP service.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self.config_manager = config_manager
        self.logger = logger
        self.test_config = config_manager.test_config
        self.path_config = config_manager.path_config
        
        # Initialize HTTP client
        self.http_client = HTTPClient(config_manager, logger)
    
    def load_test_files(self) -> List[tuple]:
        """
        Load all JSON test files from the output directory.
        
        Returns:
            List of tuples (file_path, file_name, json_data)
        """
        json_files = list(self.path_config.json_output_dir.glob("*.json"))
        
        if not json_files:
            self.logger.warning(f"No JSON test files found in {self.path_config.json_output_dir}")
            return []
        
        test_data = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as file:
                    json_data = json.load(file)
                    test_data.append((json_file, json_file.name, json_data))
            except Exception as e:
                self.logger.error(f"Failed to load test file {json_file}: {e}")
        
        self.logger.info(f"Loaded {len(test_data)} test files")
        return test_data
    
    def save_response(self, 
                     result: RequestResult, 
                     response_folder: Path) -> None:
        """
        Save API response to file.
        
        Args:
            result: Request result containing response data
            response_folder: Folder to save responses
        """
        try:
            response_folder.mkdir(parents=True, exist_ok=True)
            
            # Create response file name
            base_name = Path(result.file_name).stem
            response_file = response_folder / f"{base_name}_response.json"
            
            # Prepare response data
            response_data = {
                "file_name": result.file_name,
                "success": result.success,
                "status_code": result.status_code,
                "response_time": result.response_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "response_data": result.response_data,
                "error_message": result.error_message
            }
            
            # Save response
            with open(response_file, 'w', encoding='utf-8') as file:
                json.dump(response_data, file, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save response for {result.file_name}: {e}")
    
    def execute_parallel_tests(self, response_folder: Path) -> List[Dict[str, Any]]:
        """
        Execute API tests in parallel.
        
        Args:
            response_folder: Folder to save responses
            
        Returns:
            List of test results
            
        Raises:
            RuntimeError: If test execution fails
        """
        try:
            # Load test files
            test_data = self.load_test_files()
            
            if not test_data:
                self.logger.warning("No test files to execute")
                return []
            
            self.logger.info(f"Starting parallel execution of {len(test_data)} tests "
                           f"with {self.test_config.parallel_count} workers")
            
            results = []
            
            # Execute tests in parallel
            with ThreadPoolExecutor(max_workers=self.test_config.parallel_count) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(
                        self.http_client.send_request, 
                        json_data, 
                        file_name
                    ): (file_path, file_name)
                    for file_path, file_name, json_data in test_data
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_file):
                    file_path, file_name = future_to_file[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Save response
                        self.save_response(result, response_folder)
                        
                        # Log progress
                        if len(results) % 10 == 0:
                            self.logger.info(f"Completed {len(results)}/{len(test_data)} tests")
                            
                    except Exception as e:
                        self.logger.error(f"Failed to process {file_name}: {e}")
                        
                        # Create error result
                        error_result = RequestResult(
                            file_name=file_name,
                            success=False,
                            error_message=str(e)
                        )
                        results.append(error_result)
            
            # Calculate statistics
            successful_tests = sum(1 for r in results if r.success)
            avg_response_time = sum(r.response_time for r in results if r.response_time) / len(results)
            
            self.logger.info(f"Parallel execution completed: {successful_tests}/{len(results)} successful")
            self.logger.info(f"Average response time: {avg_response_time:.2f}s")
            
            # Convert to dictionaries for serialization
            return [self._result_to_dict(result) for result in results]
            
        except Exception as e:
            self.logger.error(f"Parallel test execution failed: {e}")
            raise RuntimeError(f"Parallel test execution failed: {e}") from e
    
    def _result_to_dict(self, result: RequestResult) -> Dict[str, Any]:
        """Convert RequestResult to dictionary."""
        return {
            "file_name": result.file_name,
            "success": result.success,
            "status_code": result.status_code,
            "response_time": result.response_time,
            "response_data": result.response_data,
            "error_message": result.error_message
        }
    
    def cleanup(self) -> None:
        """Cleanup HTTP service resources."""
        if self.http_client:
            self.http_client.close()