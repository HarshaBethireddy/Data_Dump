"""
Main runner for the refactored API testing framework.
"""
import os
import sys
import time
from typing import Optional, List
import argparse

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import config
from utils.logger import framework_logger
from utils.run_manager import RunManager
from data_processor.test_data_manager import create_regular_test_data_manager, create_prequal_test_data_manager
from api_client.http_client import ParallelAPITester
from reporting.report_generator import HTMLReportGenerator
from comparison.json_comparator import compare_test_results
from reporting.csv_merger import merge_comparison_results


class APITestFramework:
    """Main framework orchestrator."""
    
    def __init__(self):
        self.run_manager = RunManager()
        self.logger = None
        self.run_id = None
        self.response_folder = None
        self.report_folder = None
    
    def initialize(self) -> None:
        """Initialize the framework."""
        try:
            # Validate configuration
            config.validate_paths()
            config.ensure_output_directories()
            
            # Get run ID and create folders
            self.run_id = self.run_manager.get_next_run_id()
            self.response_folder, self.report_folder = self.run_manager.create_run_folders(self.run_id)
            
            # Setup logging
            log_file = os.path.join(self.report_folder, "framework.log")
            self.logger = framework_logger.setup_logger(log_file)
            
            self.logger.info(f"Framework initialized - Run ID: {self.run_id}")
            self.logger.info(f"Response folder: {self.response_folder}")
            self.logger.info(f"Report folder: {self.report_folder}")
            
        except Exception as e:
            print(f"Failed to initialize framework: {e}")
            raise
    
    def prepare_test_data(self, data_type: str = "both") -> List[str]:
        """
        Prepare test data by processing JSON templates with Excel data.
        
        Args:
            data_type: Type of data to process ("regular", "prequal", or "both")
            
        Returns:
            List of processed file names
        """
        try:
            self.logger.info(f"Preparing test data: {data_type}")
            processed_files = []
            
            if data_type in ["regular", "both"]:
                self.logger.info("Processing regular test data...")
                regular_manager = create_regular_test_data_manager()
                regular_files = regular_manager.run_full_process()
                processed_files.extend(regular_files)
                self.logger.info(f"Processed {len(regular_files)} regular test files")
            
            if data_type in ["prequal", "both"]:
                self.logger.info("Processing prequal test data...")
                prequal_manager = create_prequal_test_data_manager()
                prequal_files = prequal_manager.run_full_process()
                processed_files.extend(prequal_files)
                self.logger.info(f"Processed {len(prequal_files)} prequal test files")
            
            self.logger.info(f"Test data preparation completed: {len(processed_files)} total files")
            return processed_files
            
        except Exception as e:
            self.logger.error(f"Test data preparation failed: {e}")
            raise
    
    def run_api_tests(self) -> List:
        """Execute parallel API tests."""
        try:
            self.logger.info("Starting API test execution")
            
            with ParallelAPITester(self.response_folder) as tester:
                results = tester.run_parallel_tests()
            
            self.logger.info(f"API tests completed: {len(results)} requests processed")
            return results
            
        except Exception as e:
            self.logger.error(f"API test execution failed: {e}")
            raise
    
    def generate_report(self, results: List) -> str:
        """Generate HTML test report."""
        try:
            self.logger.info("Generating test report")
            
            report_generator = HTMLReportGenerator(self.report_folder)
            report_file = report_generator.generate_report(results, self.run_id)
            
            self.logger.info(f"Test report generated: {report_file}")
            return report_file
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise
    
    def run_full_test_cycle(self, data_type: str = "both") -> dict:
        """
        Run the complete test cycle: prepare data, execute tests, generate report.
        
        Args:
            data_type: Type of data to process ("regular", "prequal", or "both")
            
        Returns:
            Dictionary containing execution results and file paths
        """
        try:
            start_time = time.time()
            
            # Initialize framework
            self.initialize()
            
            # Prepare test data
            processed_files = self.prepare_test_data(data_type)
            
            # Run API tests
            test_results = self.run_api_tests()
            
            # Generate report
            report_file = self.generate_report(test_results)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            hours = int(execution_time // 3600)
            minutes = int((execution_time % 3600) // 60)
            seconds = int(execution_time % 60)
            
            results = {
                'run_id': self.run_id,
                'execution_time': f"{hours}h {minutes}m {seconds}s",
                'processed_files': len(processed_files),
                'test_results': len(test_results),
                'successful_tests': sum(1 for r in test_results if r.success),
                'response_folder': self.response_folder,
                'report_folder': self.report_folder,
                'report_file': report_file
            }
            
            self.logger.info(f"Full test cycle completed successfully in {results['execution_time']}")
            self.logger.info(f"Results: {results['successful_tests']}/{results['test_results']} tests successful")
            
            return results
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Full test cycle failed: {e}")
            else:
                print(f"Full test cycle failed: {e}")
            raise


def compare_results(pre_folder: str, post_folder: str) -> dict:
    """
    Compare test results between two runs.
    
    Args:
        pre_folder: Name of the pre-test folder
        post_folder: Name of the post-test folder
        
    Returns:
        Dictionary containing comparison results
    """
    try:
        # Setup logging for comparison
        log_file = os.path.join("Report", "comparison.log")
        logger = framework_logger.setup_logger(log_file)
        
        logger.info(f"Starting comparison: {pre_folder} vs {post_folder}")
        
        # Run comparison
        comparison_results = compare_test_results(pre_folder, post_folder)
        
        logger.info("Comparison completed successfully")
        return comparison_results
        
    except Exception as e:
        print(f"Comparison failed: {e}")
        raise


def merge_csv_results(sub_folder: str) -> dict:
    """
    Merge CSV comparison results into Excel files.
    
    Args:
        sub_folder: Subfolder containing CSV files to merge
        
    Returns:
        Dictionary containing merge results
    """
    try:
        # Setup logging for merge
        log_file = os.path.join("Report", "merge.log")
        logger = framework_logger.setup_logger(log_file)
        
        logger.info(f"Starting CSV merge for: {sub_folder}")
        
        # Run merge
        merge_results = merge_comparison_results(sub_folder)
        
        logger.info("CSV merge completed successfully")
        return merge_results
        
    except Exception as e:
        print(f"CSV merge failed: {e}")
        raise


def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(description="Enhanced API Testing Framework")
    parser.add_argument("command", choices=["test", "compare", "merge"], 
                       help="Command to execute")
    parser.add_argument("--data-type", choices=["regular", "prequal", "both"], 
                       default="both", help="Type of test data to process")
    parser.add_argument("--pre-folder", help="Pre-test folder name for comparison")
    parser.add_argument("--post-folder", help="Post-test folder name for comparison")
    parser.add_argument("--csv-folder", help="CSV folder name for merging")
    
    args = parser.parse_args()
    
    try:
        if args.command == "test":
            print("Starting API test execution...")
            framework = APITestFramework()
            results = framework.run_full_test_cycle(args.data_type)
            
            print("\n" + "="*50)
            print("TEST EXECUTION COMPLETED")
            print("="*50)
            print(f"Run ID: {results['run_id']}")
            print(f"Execution Time: {results['execution_time']}")
            print(f"Processed Files: {results['processed_files']}")
            print(f"Test Results: {results['successful_tests']}/{results['test_results']} successful")
            print(f"Response Folder: {results['response_folder']}")
            print(f"Report File: {results['report_file']}")
            
        elif args.command == "compare":
            if not args.pre_folder or not args.post_folder:
                print("Error: --pre-folder and --post-folder are required for comparison")
                return 1
            
            print(f"Comparing {args.pre_folder} vs {args.post_folder}...")
            results = compare_results(args.pre_folder, args.post_folder)
            
            print("\n" + "="*50)
            print("COMPARISON COMPLETED")
            print("="*50)
            print(f"Total common files: {results['total_common_files']}")
            print(f"Files with differences: {results['files_with_differences']}")
            print(f"Identical files: {results['files_identical']}")
            
        elif args.command == "merge":
            if not args.csv_folder:
                print("Error: --csv-folder is required for merging")
                return 1
            
            print(f"Merging CSV files from {args.csv_folder}...")
            results = merge_csv_results(args.csv_folder)
            
            print("\n" + "="*50)
            print("CSV MERGE COMPLETED")
            print("="*50)
            print(f"Total CSV files: {results['total_csv_files']}")
            print(f"Successful merges: {results['successful_merges']}/{results['file_groups']}")
            print(f"Output folder: {results['output_folder']}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())