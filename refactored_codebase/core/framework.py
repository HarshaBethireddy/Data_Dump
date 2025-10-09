"""
Main framework orchestrator implementing the Facade pattern.

Provides a unified interface for the entire API testing framework,
orchestrating all components while maintaining loose coupling.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .config import ConfigurationManager
from .logger import FrameworkLogger, LogLevel
from ..services.run_manager import RunManager
from ..services.test_data_service import TestDataService
from ..services.http_service import HTTPService
from ..services.report_service import ReportService
from ..services.comparison_service import ComparisonService


@dataclass
class ExecutionResult:
    """Result of framework execution."""
    run_id: str
    execution_time: str
    processed_files: int
    test_results: int
    successful_tests: int
    response_folder: Path
    report_folder: Path
    report_file: Path
    success: bool = True
    error_message: Optional[str] = None


class APITestFramework:
    """
    Main framework orchestrator following the Facade pattern.
    
    Provides a unified, simple interface to the complex API testing subsystem,
    while maintaining loose coupling between components through dependency injection.
    """
    
    def __init__(self, 
                 config_manager: Optional[ConfigurationManager] = None,
                 logger: Optional[FrameworkLogger] = None):
        """
        Initialize the framework with dependency injection.
        
        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self._config_manager = config_manager or ConfigurationManager()
        self._logger_instance = logger or FrameworkLogger()
        self._logger: Optional = None
        
        # Service instances (lazy initialization)
        self._run_manager: Optional[RunManager] = None
        self._test_data_service: Optional[TestDataService] = None
        self._http_service: Optional[HTTPService] = None
        self._report_service: Optional[ReportService] = None
        self._comparison_service: Optional[ComparisonService] = None
        
        # Execution state
        self._run_id: Optional[str] = None
        self._response_folder: Optional[Path] = None
        self._report_folder: Optional[Path] = None
        self._initialized = False
    
    def initialize(self, log_file: Optional[Path] = None) -> None:
        """
        Initialize the framework and all its components.
        
        Args:
            log_file: Optional custom log file path
            
        Raises:
            RuntimeError: If initialization fails
        """
        try:
            # Validate and setup configuration
            self._config_manager.validate_paths()
            self._config_manager.ensure_output_directories()
            
            # Initialize run manager and get run ID
            self._run_manager = RunManager(self._config_manager.path_config)
            self._run_id = self._run_manager.get_next_run_id()
            self._response_folder, self._report_folder = self._run_manager.create_run_folders(self._run_id)
            
            # Setup logging
            if log_file is None:
                log_file = self._report_folder / "framework.log"
            
            self._logger = self._logger_instance.setup(
                log_file=log_file,
                console_level=LogLevel.INFO,
                file_level=LogLevel.DEBUG
            )
            
            # Initialize services with dependency injection
            self._test_data_service = TestDataService(
                config_manager=self._config_manager,
                logger=self._logger
            )
            
            self._http_service = HTTPService(
                config_manager=self._config_manager,
                logger=self._logger
            )
            
            self._report_service = ReportService(
                config_manager=self._config_manager,
                logger=self._logger
            )
            
            self._comparison_service = ComparisonService(
                config_manager=self._config_manager,
                logger=self._logger
            )
            
            self._initialized = True
            
            self._logger.info(f"Framework initialized successfully - Run ID: {self._run_id}")
            self._logger.info(f"Response folder: {self._response_folder}")
            self._logger.info(f"Report folder: {self._report_folder}")
            
        except Exception as e:
            error_msg = f"Framework initialization failed: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _ensure_initialized(self) -> None:
        """Ensure framework is initialized before operations."""
        if not self._initialized:
            raise RuntimeError("Framework not initialized. Call initialize() first.")
    
    def prepare_test_data(self, data_type: str = "both") -> List[str]:
        """
        Prepare test data by processing JSON templates with Excel data.
        
        Args:
            data_type: Type of data to process ("regular", "prequal", or "both")
            
        Returns:
            List of processed file names
            
        Raises:
            ValueError: If invalid data_type provided
            RuntimeError: If data preparation fails
        """
        self._ensure_initialized()
        
        if data_type not in ["regular", "prequal", "both"]:
            raise ValueError(f"Invalid data_type: {data_type}. Must be 'regular', 'prequal', or 'both'")
        
        try:
            self._logger.info(f"Preparing test data: {data_type}")
            processed_files = self._test_data_service.prepare_test_data(data_type)
            
            self._logger.info(f"Test data preparation completed: {len(processed_files)} total files")
            return processed_files
            
        except Exception as e:
            self._logger.error(f"Test data preparation failed: {e}")
            raise RuntimeError(f"Test data preparation failed: {e}") from e
    
    def execute_api_tests(self) -> List[Dict[str, Any]]:
        """
        Execute parallel API tests.
        
        Returns:
            List of test results
            
        Raises:
            RuntimeError: If test execution fails
        """
        self._ensure_initialized()
        
        try:
            self._logger.info("Starting API test execution")
            
            results = self._http_service.execute_parallel_tests(self._response_folder)
            
            self._logger.info(f"API tests completed: {len(results)} requests processed")
            return results
            
        except Exception as e:
            self._logger.error(f"API test execution failed: {e}")
            raise RuntimeError(f"API test execution failed: {e}") from e
    
    def generate_report(self, test_results: List[Dict[str, Any]]) -> Path:
        """
        Generate comprehensive HTML test report.
        
        Args:
            test_results: List of test execution results
            
        Returns:
            Path to generated report file
            
        Raises:
            RuntimeError: If report generation fails
        """
        self._ensure_initialized()
        
        try:
            self._logger.info("Generating test report")
            
            report_file = self._report_service.generate_html_report(
                test_results, 
                self._run_id, 
                self._report_folder
            )
            
            self._logger.info(f"Test report generated: {report_file}")
            return report_file
            
        except Exception as e:
            self._logger.error(f"Report generation failed: {e}")
            raise RuntimeError(f"Report generation failed: {e}") from e
    
    def run_full_test_cycle(self, data_type: str = "both") -> ExecutionResult:
        """
        Execute the complete test cycle: prepare data, execute tests, generate report.
        
        Args:
            data_type: Type of data to process ("regular", "prequal", or "both")
            
        Returns:
            ExecutionResult containing all execution details
        """
        start_time = time.time()
        
        try:
            # Initialize if not already done
            if not self._initialized:
                self.initialize()
            
            # Execute test cycle
            processed_files = self.prepare_test_data(data_type)
            test_results = self.execute_api_tests()
            report_file = self.generate_report(test_results)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            hours = int(execution_time // 3600)
            minutes = int((execution_time % 3600) // 60)
            seconds = int(execution_time % 60)
            time_str = f"{hours}h {minutes}m {seconds}s"
            
            # Count successful tests
            successful_tests = sum(1 for r in test_results if r.get('success', False))
            
            result = ExecutionResult(
                run_id=self._run_id,
                execution_time=time_str,
                processed_files=len(processed_files),
                test_results=len(test_results),
                successful_tests=successful_tests,
                response_folder=self._response_folder,
                report_folder=self._report_folder,
                report_file=report_file,
                success=True
            )
            
            self._logger.info(f"Full test cycle completed successfully in {time_str}")
            self._logger.info(f"Results: {successful_tests}/{len(test_results)} tests successful")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            hours = int(execution_time // 3600)
            minutes = int((execution_time % 3600) // 60)
            seconds = int(execution_time % 60)
            time_str = f"{hours}h {minutes}m {seconds}s"
            
            error_msg = f"Full test cycle failed after {time_str}: {e}"
            
            if self._logger:
                self._logger.error(error_msg)
            
            return ExecutionResult(
                run_id=self._run_id or "unknown",
                execution_time=time_str,
                processed_files=0,
                test_results=0,
                successful_tests=0,
                response_folder=self._response_folder or Path("unknown"),
                report_folder=self._report_folder or Path("unknown"),
                report_file=Path("unknown"),
                success=False,
                error_message=str(e)
            )
    
    def compare_test_results(self, pre_folder: str, post_folder: str) -> Dict[str, Any]:
        """
        Compare test results between two runs.
        
        Args:
            pre_folder: Name of the pre-test folder
            post_folder: Name of the post-test folder
            
        Returns:
            Dictionary containing comparison results
        """
        self._ensure_initialized()
        
        try:
            self._logger.info(f"Starting comparison: {pre_folder} vs {post_folder}")
            
            comparison_results = self._comparison_service.compare_results(pre_folder, post_folder)
            
            self._logger.info("Comparison completed successfully")
            return comparison_results
            
        except Exception as e:
            self._logger.error(f"Comparison failed: {e}")
            raise RuntimeError(f"Comparison failed: {e}") from e
    
    def merge_csv_results(self, sub_folder: str) -> Dict[str, Any]:
        """
        Merge CSV comparison results into Excel files.
        
        Args:
            sub_folder: Subfolder containing CSV files to merge
            
        Returns:
            Dictionary containing merge results
        """
        self._ensure_initialized()
        
        try:
            self._logger.info(f"Starting CSV merge for: {sub_folder}")
            
            merge_results = self._comparison_service.merge_csv_results(sub_folder)
            
            self._logger.info("CSV merge completed successfully")
            return merge_results
            
        except Exception as e:
            self._logger.error(f"CSV merge failed: {e}")
            raise RuntimeError(f"CSV merge failed: {e}") from e
    
    def cleanup(self) -> None:
        """Cleanup framework resources."""
        if self._logger_instance:
            self._logger_instance.close()
        
        # Cleanup services
        if self._http_service:
            self._http_service.cleanup()
        
        self._initialized = False
        self._logger = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()