"""
Command Line Interface for the API Testing Framework.

Provides a comprehensive CLI with subcommands for testing, comparison,
and merging operations with proper error handling and user feedback.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List

from ..core.framework import APITestFramework
from ..core.config import ConfigurationManager
from ..core.logger import FrameworkLogger, LogLevel


def create_cli_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command line argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Enterprise API Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s test --data-type both                    # Run tests with both data types
  %(prog)s test --data-type regular --config dev.json  # Run with specific config
  %(prog)s compare --pre-folder 100001 --post-folder 100002  # Compare results
  %(prog)s merge --csv-folder comparison_results    # Merge CSV files
  %(prog)s test --help                              # Get help for test command
        """
    )
    
    # Global arguments
    parser.add_argument(
        "--config", 
        type=str,
        help="Path to configuration file (JSON or CSV)"
    )
    parser.add_argument(
        "--environment", 
        type=str, 
        default="development",
        choices=["development", "testing", "staging", "production"],
        help="Environment to run in (default: development)"
    )
    parser.add_argument(
        "--log-level", 
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version="API Testing Framework 2.0.0"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        dest="command", 
        help="Available commands",
        metavar="COMMAND"
    )
    
    # Test command
    test_parser = subparsers.add_parser(
        "test", 
        help="Execute API tests",
        description="Execute API tests with specified data types and configuration"
    )
    test_parser.add_argument(
        "--data-type", 
        choices=["regular", "prequal", "both"], 
        default="both",
        help="Type of test data to process (default: both)"
    )
    test_parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory for test results"
    )
    
    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", 
        help="Compare test results",
        description="Compare test results between two different runs"
    )
    compare_parser.add_argument(
        "--pre-folder", 
        required=True,
        help="Pre-test folder name (e.g., 100001)"
    )
    compare_parser.add_argument(
        "--post-folder", 
        required=True,
        help="Post-test folder name (e.g., 100002)"
    )
    
    # Merge command
    merge_parser = subparsers.add_parser(
        "merge", 
        help="Merge CSV results",
        description="Merge CSV comparison results into Excel files"
    )
    merge_parser.add_argument(
        "--csv-folder", 
        required=True,
        help="CSV folder name containing files to merge"
    )
    
    return parser


def execute_test_command(args, framework: APITestFramework) -> int:
    """
    Execute the test command.
    
    Args:
        args: Parsed command line arguments
        framework: Framework instance
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        print("🚀 Starting API test execution...")
        print(f"   Data type: {args.data_type}")
        print(f"   Environment: {args.environment}")
        
        # Execute full test cycle
        result = framework.run_full_test_cycle(args.data_type)
        
        if result.success:
            print("\n" + "="*60)
            print("✅ TEST EXECUTION COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"📊 Run ID: {result.run_id}")
            print(f"⏱️  Execution Time: {result.execution_time}")
            print(f"📁 Processed Files: {result.processed_files}")
            print(f"🧪 Test Results: {result.successful_tests}/{result.test_results} successful")
            print(f"📂 Response Folder: {result.response_folder}")
            print(f"📋 Report File: {result.report_file}")
            return 0
        else:
            print("\n" + "="*60)
            print("❌ TEST EXECUTION FAILED")
            print("="*60)
            print(f"💥 Error: {result.error_message}")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1


def execute_compare_command(args, framework: APITestFramework) -> int:
    """
    Execute the compare command.
    
    Args:
        args: Parsed command line arguments
        framework: Framework instance
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        print(f"🔍 Comparing test results...")
        print(f"   Pre-folder: {args.pre_folder}")
        print(f"   Post-folder: {args.post_folder}")
        
        # Initialize framework for comparison
        framework.initialize()
        
        # Execute comparison
        results = framework.compare_test_results(args.pre_folder, args.post_folder)
        
        print("\n" + "="*60)
        print("✅ COMPARISON COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"📊 Total common files: {results['total_common_files']}")
        print(f"🔄 Files with differences: {results['files_with_differences']}")
        print(f"✅ Identical files: {results['files_identical']}")
        
        if results['files_with_differences'] > 0:
            print(f"⚠️  Difference rate: {(results['files_with_differences']/results['total_common_files']*100):.1f}%")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Comparison failed: {e}")
        return 1


def execute_merge_command(args, framework: APITestFramework) -> int:
    """
    Execute the merge command.
    
    Args:
        args: Parsed command line arguments
        framework: Framework instance
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        print(f"📊 Merging CSV files...")
        print(f"   CSV folder: {args.csv_folder}")
        
        # Initialize framework for merging
        framework.initialize()
        
        # Execute merge
        results = framework.merge_csv_results(args.csv_folder)
        
        print("\n" + "="*60)
        print("✅ CSV MERGE COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"📁 Total CSV files: {results['total_csv_files']}")
        print(f"✅ Successful merges: {results['successful_merges']}/{results['file_groups']}")
        print(f"📂 Output folder: {results['output_folder']}")
        
        if 'excel_file' in results:
            print(f"📋 Excel file: {results['excel_file']}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ CSV merge failed: {e}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI application.
    
    Args:
        argv: Command line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse command line arguments
    parser = create_cli_parser()
    args = parser.parse_args(argv)
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Convert log level string to enum
        log_level = getattr(LogLevel, args.log_level.upper())
        
        # Create configuration manager
        config_manager = ConfigurationManager(
            config_file=args.config,
            environment=args.environment
        )
        
        # Create logger
        logger = FrameworkLogger("APITestFramework")
        
        # Create framework instance
        framework = APITestFramework(
            config_manager=config_manager,
            logger=logger
        )
        
        # Execute appropriate command
        if args.command == "test":
            return execute_test_command(args, framework)
        elif args.command == "compare":
            return execute_compare_command(args, framework)
        elif args.command == "merge":
            return execute_merge_command(args, framework)
        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1
    finally:
        # Cleanup framework if it was created
        try:
            if 'framework' in locals():
                framework.cleanup()
        except:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    sys.exit(main())