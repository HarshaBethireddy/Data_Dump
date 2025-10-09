"""
Test execution orchestrator for the Enterprise API Testing Framework.

This module provides the main test execution logic that coordinates
all components to run comprehensive API tests.
"""

import time
import json
from typing import Dict, Any, List, Optional, Iterator
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from refactored_codebase.config.settings import Settings
from refactored_codebase.core.appid_manager import AppIDManager
from refactored_codebase.core.data_manager import TestDataManager, DataType, ProcessedTestData
from refactored_codebase.core.http_client import HTTPClient, HTTPResponse
from refactored_codebase.core.run_manager import RunManager, RunMetadata
from refactored_codebase.utils.logging import get_logger


@dataclass
class TestResult:
    """Individual test result."""
    template_name: str
    appid: int
    data_type: DataType
    request_data: Dict[str, Any]
    response: Optional[HTTPResponse]
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class TestExecutionSummary:
    """Test execution summary."""
    run_metadata: RunMetadata
    total_tests: int
    successful_tests: int
    failed_tests: int
    total_execution_time: float
    average_response_time: float
    results: List[TestResult]


class TestExecutor:
    """
    Enterprise test executor with comprehensive orchestration.
    
    Features:
    - Parallel test execution
    - Progress tracking and reporting
    - Error handling and recovery
    - Result aggregation and analysis
    - Resource management
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize test executor.
        
        Args:
            settings: Framework settings
        """
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize managers
        self.appid_manager = AppIDManager(settings.appid)
        self.data_manager = TestDataManager(settings.paths, self.appid_manager)
        self.run_manager = RunManager(settings.paths.reports_dir)
        
        self.logger.info("Test Executor initialized")
    
    def execute_tests(
        self,
        data_type: DataType,
        count: Optional[int] = None,
        output_dir: Optional[Path] = None
    ) -> TestExecutionSummary:
        """
        Execute tests for specified data type.
        
        Args:
            data_type: Type of data to test
            count: Maximum number of tests to run
            output_dir: Output directory override
            
        Returns:
            Test execution summary
        """
        start_time = time.time()
        
        # Create run metadata
        run_metadata = self.run_manager.create_run(data_type.value)
        
        # Determine output directory
        if output_dir is None:
            output_dir = self.settings.paths.responses_dir / run_metadata.run_id
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Starting test execution - Run ID: {run_metadata.run_id}")
        
        try:
            # Discover and process templates
            templates = self.data_manager.discover_templates(data_type)
            
            if count:
                templates = templates[:count]
            
            if not templates:
                self.logger.warning(f"No templates found for {data_type.value}")
                return self._create_empty_summary(run_metadata, start_time)
            
            # Update run metadata
            self.run_manager.update_run_status(
                run_metadata.run_id,
                "running",
                template_count=len(templates)
            )
            
            # Execute tests
            results = list(self._execute_tests_parallel(templates, output_dir))
            
            # Calculate summary
            execution_time = time.time() - start_time
            successful_tests = sum(1 for r in results if r.success)
            failed_tests = len(results) - successful_tests
            
            # Calculate average response time
            response_times = [r.response.elapsed_time for r in results if r.response]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Update run metadata
            self.run_manager.update_run_status(
                run_metadata.run_id,
                "completed",
                success_count=successful_tests,
                failure_count=failed_tests
            )
            
            # Create summary
            summary = TestExecutionSummary(
                run_metadata=run_metadata,
                total_tests=len(results),
                successful_tests=successful_tests,
                failed_tests=failed_tests,
                total_execution_time=execution_time,
                average_response_time=avg_response_time,
                results=results
            )
            
            # Save summary
            self._save_execution_summary(summary, output_dir)
            
            self.logger.info(
                f"Test execution completed - Run ID: {run_metadata.run_id}, "
                f"Success: {successful_tests}/{len(results)}"
            )
            
            return summary
            
        except Exception as e:
            # Update run metadata on failure
            self.run_manager.update_run_status(run_metadata.run_id, "failed")
            self.logger.error(f"Test execution failed: {e}")
            raise
    
    def _execute_tests_parallel(
        self,
        templates: List,
        output_dir: Path
    ) -> Iterator[TestResult]:
        """Execute tests in parallel."""
        with HTTPClient(self.settings.api) as http_client:
            with ThreadPoolExecutor(max_workers=self.settings.test.parallel_count) as executor:
                # Submit all tasks
                future_to_template = {
                    executor.submit(
                        self._execute_single_test,
                        template,
                        http_client,
                        output_dir
                    ): template
                    for template in templates
                }
                
                # Process completed tasks
                for future in as_completed(future_to_template):
                    template = future_to_template[future]
                    try:
                        result = future.result()
                        yield result
                    except Exception as e:
                        self.logger.error(f"Test execution failed for {template.file_name}: {e}")
                        yield TestResult(
                            template_name=template.file_name,
                            appid=0,
                            data_type=template.data_type,
                            request_data={},
                            response=None,
                            success=False,
                            error_message=str(e)
                        )
    
    def _execute_single_test(
        self,
        template,
        http_client: HTTPClient,
        output_dir: Path
    ) -> TestResult:
        """Execute a single test."""
        start_time = time.time()
        
        try:
            # Apply think time
            if self.settings.test.think_time > 0:
                time.sleep(self.settings.test.think_time)
            
            # Process template
            processed_data = self.data_manager.process_template(template)
            
            # Send request
            response = http_client.send_json_request(processed_data.data)
            
            # Save request and response
            self._save_test_files(processed_data, response, output_dir)
            
            execution_time = time.time() - start_time
            
            return TestResult(
                template_name=template.file_name,
                appid=processed_data.appid,
                data_type=processed_data.data_type,
                request_data=processed_data.data,
                response=response,
                success=response.is_success,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Single test execution failed: {e}")
            
            return TestResult(
                template_name=template.file_name,
                appid=0,
                data_type=template.data_type,
                request_data={},
                response=None,
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _save_test_files(
        self,
        processed_data: ProcessedTestData,
        response: HTTPResponse,
        output_dir: Path
    ) -> None:
        """Save request and response files."""
        base_name = f"{processed_data.file_name}_{processed_data.appid}"
        
        # Save request
        request_file = output_dir / f"{base_name}_request.json"
        with open(request_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data.data, f, indent=2, ensure_ascii=False)
        
        # Save response
        response_file = output_dir / f"{base_name}_response.json"
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _save_execution_summary(
        self,
        summary: TestExecutionSummary,
        output_dir: Path
    ) -> None:
        """Save execution summary to file."""
        summary_file = output_dir / "execution_summary.json"
        
        summary_data = {
            "run_metadata": summary.run_metadata.to_dict(),
            "statistics": {
                "total_tests": summary.total_tests,
                "successful_tests": summary.successful_tests,
                "failed_tests": summary.failed_tests,
                "success_rate": (summary.successful_tests / summary.total_tests * 100) if summary.total_tests > 0 else 0,
                "total_execution_time": summary.total_execution_time,
                "average_response_time": summary.average_response_time
            },
            "results": [
                {
                    "template_name": r.template_name,
                    "appid": r.appid,
                    "data_type": r.data_type.value,
                    "success": r.success,
                    "error_message": r.error_message,
                    "execution_time": r.execution_time,
                    "response_status": r.response.status_code if r.response else None,
                    "response_time": r.response.elapsed_time if r.response else None
                }
                for r in summary.results
            ]
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    def _create_empty_summary(
        self,
        run_metadata: RunMetadata,
        start_time: float
    ) -> TestExecutionSummary:
        """Create empty summary for no tests scenario."""
        execution_time = time.time() - start_time
        
        return TestExecutionSummary(
            run_metadata=run_metadata,
            total_tests=0,
            successful_tests=0,
            failed_tests=0,
            total_execution_time=execution_time,
            average_response_time=0.0,
            results=[]
        )
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get overall execution statistics."""
        return self.run_manager.get_run_statistics()