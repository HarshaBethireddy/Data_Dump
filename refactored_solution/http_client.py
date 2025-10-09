"""
Enhanced HTTP client for API testing with proper error handling and retry logic.
"""
import os
import time
import json
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

from logger import framework_logger
from settings import config

@dataclass
class RequestResult:
    """Result of an API request."""
    file_path: str
    status_code: Optional[int]
    response_text: str
    success: bool
    error_message: Optional[str] = None
    response_time: float = 0.0


class EnhancedHTTPClient:
    """Enhanced HTTP client with retry logic and proper session management."""
    
    def __init__(self):
        self.logger = framework_logger.get_logger()
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=config.test_config.max_retries,
            backoff_factor=config.test_config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set timeout
        session.timeout = config.api_config.timeout
        
        return session
    
    def send_request(self, file_path: str, json_data: str, response_folder: str) -> RequestResult:
        """Send a single API request with proper error handling."""
        start_time = time.time()
        
        try:
            # Prepare headers
            headers = config.get_headers()
            headers["Content-Length"] = str(len(json_data))
            
            # Add think time before request (not after)
            if config.test_config.think_time > 0:
                time.sleep(config.test_config.think_time)
            
            # Send request
            response = self.session.post(
                config.api_config.url,
                headers=headers,
                data=json_data,
                verify=config.api_config.verify_ssl,
                timeout=config.api_config.timeout
            )
            
            response_time = time.time() - start_time
            
            # Save response
            response_file = self._save_response(file_path, response.text, response_folder)
            
            # Log request details
            self.logger.info(
                f"Request: {os.path.basename(file_path)} | "
                f"Status: {response.status_code} | "
                f"Time: {response_time:.2f}s"
            )
            
            return RequestResult(
                file_path=file_path,
                status_code=response.status_code,
                response_text=response.text,
                success=200 <= response.status_code < 300,
                response_time=response_time
            )
            
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout for {file_path}"
            self.logger.error(error_msg)
            return RequestResult(
                file_path=file_path,
                status_code=None,
                response_text="",
                success=False,
                error_message=error_msg,
                response_time=time.time() - start_time
            )
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Connection error for {file_path}"
            self.logger.error(error_msg)
            return RequestResult(
                file_path=file_path,
                status_code=None,
                response_text="",
                success=False,
                error_message=error_msg,
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            error_msg = f"Unexpected error for {file_path}: {str(e)}"
            self.logger.error(error_msg)
            return RequestResult(
                file_path=file_path,
                status_code=None,
                response_text="",
                success=False,
                error_message=error_msg,
                response_time=time.time() - start_time
            )
    
    def _save_response(self, file_path: str, response_text: str, response_folder: str) -> str:
        """Save API response to file."""
        try:
            filename = os.path.basename(file_path).replace('.json', '_response.json')
            response_file = os.path.join(response_folder, filename)
            
            with open(response_file, 'w', encoding='utf-8') as file:
                file.write(response_text)
            
            return response_file
            
        except Exception as e:
            self.logger.error(f"Failed to save response for {file_path}: {e}")
            raise
    
    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()


class ParallelAPITester:
    """Manages parallel API testing execution."""
    
    def __init__(self, response_folder: str):
        self.response_folder = response_folder
        self.logger = framework_logger.get_logger()
        self.client = EnhancedHTTPClient()
    
    def _load_json_files(self, json_folder: str) -> Dict[str, str]:
        """Load all JSON files into memory with proper resource management."""
        if not os.path.exists(json_folder):
            raise FileNotFoundError(f"JSON folder not found: {json_folder}")
        
        json_files = [
            os.path.join(json_folder, f) 
            for f in os.listdir(json_folder) 
            if f.endswith('.json')
        ]
        
        if not json_files:
            raise ValueError(f"No JSON files found in {json_folder}")
        
        json_data_dict = {}
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    json_data_dict[file_path] = file.read()
            except Exception as e:
                self.logger.error(f"Failed to read {file_path}: {e}")
                continue
        
        return json_data_dict
    
    def run_parallel_tests(self, json_folder: str = "json_files") -> List[RequestResult]:
        """Execute parallel API tests."""
        try:
            self.logger.info("Starting parallel API tests")
            
            # Load JSON files
            json_data_dict = self._load_json_files(json_folder)
            self.logger.info(f"Loaded {len(json_data_dict)} JSON files")
            
            # Ensure response folder exists
            os.makedirs(self.response_folder, exist_ok=True)
            
            results = []
            start_time = time.time()
            
            # Execute requests in parallel
            with ThreadPoolExecutor(max_workers=config.test_config.parallel_count) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(
                        self.client.send_request, 
                        file_path, 
                        json_data, 
                        self.response_folder
                    ): file_path
                    for file_path, json_data in json_data_dict.items()
                }
                
                # Collect results as they complete
                for i, future in enumerate(as_completed(future_to_file), 1):
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Progress reporting
                        progress = (i / len(json_data_dict)) * 100
                        self.logger.info(f"Progress: {i}/{len(json_data_dict)} ({progress:.1f}%)")
                        
                    except Exception as e:
                        file_path = future_to_file[future]
                        self.logger.error(f"Task failed for {file_path}: {e}")
                        results.append(RequestResult(
                            file_path=file_path,
                            status_code=None,
                            response_text="",
                            success=False,
                            error_message=str(e)
                        ))
            
            # Calculate execution time
            total_time = time.time() - start_time
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            seconds = int(total_time % 60)
            
            self.logger.info(f"Parallel tests completed in {hours}h {minutes}m {seconds}s")
            
            # Log summary
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            self.logger.info(f"Results: {successful} successful, {failed} failed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Parallel testing failed: {e}")
            raise
        finally:
            self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()