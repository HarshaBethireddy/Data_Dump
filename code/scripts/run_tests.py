"""
Main script for running API tests.

This script orchestrates the complete test execution workflow:
1. Load configuration
2. Prepare test data
3. Execute API requests in parallel
4. Generate comprehensive reports
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config.settings import load_config, get_config
from ..core.constants import TIMESTAMP_FORMAT
from ..core.models import TestDataType
from ..services.test_data_service import TestDataService
from ..services.http_service import HTTPService
from ..services.report_service import ReportService
from ..utils.logger import get_logger, shutdown_logging, PerformanceLogger


class TestRunner:
    """
    Main test execution orchestrator.
    
    Coordinates all services to execute the complete test workflow.
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize test runner.
        
        Args:
            config_file: Path to configuration file (uses default if None)
        """
        # Load configuration
        self.config = load_config(config_file)
        
        # Setup logging
        log_file = self.config.paths.logs / f"test_run_{datetime.now().strftime(TIMESTAMP_FORMAT)}.log"
        self.logger = get_logger(
            name="TestRunner",
            log_file=log_file,
            level=self.config.logging.level
        )
        
        # Initialize services
        self.test_data_service = TestDataService(self.logger)
        self.http_service = HTTPService(self.logger)
        self.report_service = ReportService(self.logger)
        
        # Generate unique run ID
        self.run_id = datetime.now().strftime(TIMESTAMP_FORMAT)
        self.logger.info(f"Test Runner initialized - Run ID: {self.run_id}")
    
    def prepare_test_data(self, data_type: str = TestDataType.BOTH) -> int:
        """
        Prepare test data files.
        
        Args:
            data_type: Type of test data to prepare (regular, prequal, both)
            
        Returns:
            Number of files prepared
        """
        try:
            self.logger.info(f"Preparing test data: {data_type}")
            
            if data_type == TestDataType.REGULAR:
                files = self.test_data_service.prepare_regular_test_data()
            elif data_type == TestDataType.PREQUAL:
                files = self.test_data_service.prepare_prequal_test_data()
            else:  # BOTH
                files = self.test_data_service.prepare_all_test_data()
            
            self.logger.info(f"Prepared {len(files)} test data files")
            return len(files)
            
        except Exception as e:
            self.logger.error(f"Failed to prepare test data: {e}")
            raise
    
    def execute_tests(self) -> dict:
        """
        Execute API tests in parallel.
        
        Returns:
            Dictionary with execution results
        """
        try:
            self.logger.info("Starting test execution")
            start_time = datetime.now()
            
            # Create timestamped output folder
            output_folder = self.config.paths.output_responses / self.run_id
            
            # Execute tests
            batch_result = self.http_service.run_tests(
                json_folder=self.config.paths.output_processed,
                output_folder=output_folder
            )
            
            end_time = datetime.now()
            
            self.logger.info(
                f"Test execution completed: {batch_result.successful_requests}/"
                f"{batch_result.total_requests} successful"
            )
            
            return {
                'batch_result': batch_result,
                'start_time': start_time,
                'end_time': end_time,
                'output_folder': output_folder
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute tests: {e}")
            raise
    
    def generate_reports(
        self,
        batch_result,
        start_time: datetime,
        end_time: datetime
    ) -> dict:
        """
        Generate test reports.
        
        Args:
            batch_result: Batch test results
            start_time: Test start time
            end_time: Test end time
            
        Returns:
            Dictionary mapping report types to file paths
        """
        try:
            self.logger.info("Generating test reports")
            
            # Create report folder
            report_folder = self.config.paths.output_reports / self.run_id
            
            # Generate reports
            reports = self.report_service.generate_reports(
                results=batch_result.results,
                run_id=self.run_id,
                output_folder=report_folder,
                start_time=start_time,
                end_time=end_time
            )
            
            self.logger.info(f"Generated {len(reports)} report(s)")
            return reports
            
        except Exception as e:
            self.logger.error(f"Failed to generate reports: {e}")
            raise
    
    def run_full_test_cycle(self, data_type: str = TestDataType.BOTH) -> dict:
        """
        Run the complete test cycle.
        
        Args:
            data_type: Type of test data to process
            
        Returns:
            Dictionary with complete execution results
        """
        try:
            with PerformanceLogger(self.logger, "Complete Test Cycle"):
                # Prepare test data
                file_count = self.prepare_test_data(data_type)
                
                # Execute tests
                execution_result = self.execute_tests()
                
                # Generate reports
                reports = self.generate_reports(
                    batch_result=execution_result['batch_result'],
                    start_time=execution_result['start_time'],
                    end_time=execution_result['end_time']
                )
                
                # Compile results
                batch_result = execution_result['batch_result']
                duration = (execution_result['end_time'] - execution_result['start_time']).total_seconds()
                
                results = {
                    'run_id': self.run_id,
                    'data_type': data_type,
                    'prepared_files': file_count,
                    'total_tests': batch_result.total_requests,
                    'successful_tests': batch_result.successful_requests,
                    'failed_tests': batch_result.failed_requests,
                    'success_rate': (batch_result.successful_requests / batch_result.total_requests * 100)
                                    if batch_result.total_requests > 0 else 0.0,
                    'avg_response_time': batch_result.avg_response_time,
                    'total_execution_time': batch_result.total_execution_time,
                    'duration_seconds': duration,
                    'output_folder': str(execution_result['output_folder']),
                    'report_folder': str(self.config.paths.output_reports / self.run_id),
                    'reports': {k: str(v) for k, v in reports.items()}
                }
                
                self.logger.info("=" * 80)
                self.logger.info("TEST CYCLE COMPLETED SUCCESSFULLY")
                self.logger.info("=" * 80)
                self.logger.info(f"Run ID: {results['run_id']}")
                self.logger.info(f"Test Files Prepared: {results['prepared_files']}")
                self.logger.info(f"Tests Executed: {results['total_tests']}")
                self.logger.info(f"Success Rate: {results['success_rate']:.1f}%")
                self.logger.info(f"Avg Response Time: {results['avg_response_time']:.2f}s")
                self.logger.info(f"Total Duration: {self._format_duration(duration)}")
                self.logger.info(f"Reports: {', '.join(reports.keys())}")
                self.logger.info("=" * 80)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Test cycle failed: {e}")
            raise
        finally:
            shutdown_logging()
    
    def _format_duration(self, duration: float) -> str:
        """Format duration in human-readable format."""
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="API Testing Framework - Execute parallel API tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests (regular + prequal)
  python run_tests.py
  
  # Run only regular tests
  python run_tests.py --data-type regular
  
  # Run only prequal tests
  python run_tests.py --data-type prequal
  
  # Use custom config file
  python run_tests.py --config /path/to/config.json
        """
    )
    
    parser.add_argument(
        '--data-type',
        choices=['regular', 'prequal', 'both'],
        default='both',
        help='Type of test data to process (default: both)'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to configuration file (default: config.json)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize and run test runner
        runner = TestRunner(config_file=args.config)
        results = runner.run_full_test_cycle(data_type=args.data_type)
        
        # Print summary
        print("\n" + "=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Run ID: {results['run_id']}")
        print(f"Data Type: {results['data_type']}")
        print(f"Prepared Files: {results['prepared_files']}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Successful: {results['successful_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Avg Response Time: {results['avg_response_time']:.2f}s")
        print(f"Duration: {runner._format_duration(results['duration_seconds'])}")
        print(f"\nOutput Folder: {results['output_folder']}")
        print(f"Report Folder: {results['report_folder']}")
        print(f"\nGenerated Reports:")
        for report_type, report_path in results['reports'].items():
            print(f"  - {report_type.upper()}: {report_path}")
        print("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\nERROR: Test execution failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())