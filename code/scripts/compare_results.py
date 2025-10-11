"""
Script for comparing test results between two test runs.

This script compares JSON responses from two different test executions
and generates detailed comparison reports.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config.settings import load_config, get_config
from ..core.constants import TIMESTAMP_FORMAT
from ..services.comparison_service import ComparisonService
from ..utils.logger import get_logger, shutdown_logging, PerformanceLogger
from ..utils.validators import PathValidator


class ComparisonRunner:
    """
    Orchestrates comparison of test results between two runs.
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize comparison runner.
        
        Args:
            config_file: Path to configuration file (uses default if None)
        """
        # Load configuration
        self.config = load_config(config_file, validate_paths=False)
        
        # Setup logging
        log_file = (
            self.config.paths.logs / 
            f"comparison_{datetime.now().strftime(TIMESTAMP_FORMAT)}.log"
        )
        self.logger = get_logger(
            name="ComparisonRunner",
            log_file=log_file,
            level=self.config.logging.level
        )
        
        # Initialize service
        self.comparison_service = ComparisonService(self.logger)
        
        self.logger.info("Comparison Runner initialized")
    
    def compare_test_runs(
        self,
        pre_folder: str,
        post_folder: str,
        base_folder: Optional[Path] = None
    ) -> dict:
        """
        Compare test results between two runs.
        
        Args:
            pre_folder: Name of pre-change test folder
            post_folder: Name of post-change test folder
            base_folder: Base folder containing test results (uses config if None)
            
        Returns:
            Dictionary with comparison results
        """
        try:
            with PerformanceLogger(self.logger, f"Compare {pre_folder} vs {post_folder}"):
                # Use config path if base folder not provided
                if base_folder is None:
                    base_folder = self.config.paths.output_responses
                
                # Build full paths
                folder1 = base_folder / pre_folder
                folder2 = base_folder / post_folder
                
                # Validate folders exist
                self.logger.info(f"Comparing folders:")
                self.logger.info(f"  Pre:  {folder1}")
                self.logger.info(f"  Post: {folder2}")
                
                PathValidator.validate_directory_exists(folder1, f"Pre-test folder '{pre_folder}'")
                PathValidator.validate_directory_exists(folder2, f"Post-test folder '{post_folder}'")
                
                # Create output folder
                output_folder = self.config.paths.output_comparisons / f"{pre_folder}_vs_{post_folder}"
                
                # Perform comparison
                summary = self.comparison_service.compare_folders(
                    folder1=folder1,
                    folder2=folder2,
                    folder1_name=pre_folder,
                    folder2_name=post_folder,
                    output_folder=output_folder
                )
                
                # Compile results
                results = {
                    'pre_folder': pre_folder,
                    'post_folder': post_folder,
                    'output_folder': str(output_folder),
                    'total_common_files': summary.total_common_files,
                    'files_with_differences': summary.files_with_differences,
                    'files_identical': summary.files_identical,
                    'only_in_pre': len(summary.only_in_folder1),
                    'only_in_post': len(summary.only_in_folder2),
                    'difference_rate': (
                        summary.files_with_differences / summary.total_common_files * 100
                        if summary.total_common_files > 0 else 0.0
                    ),
                    'timestamp': summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                self.logger.info("=" * 80)
                self.logger.info("COMPARISON COMPLETED")
                self.logger.info("=" * 80)
                self.logger.info(f"Pre-test folder: {pre_folder}")
                self.logger.info(f"Post-test folder: {post_folder}")
                self.logger.info(f"Total common files: {results['total_common_files']}")
                self.logger.info(f"Files with differences: {results['files_with_differences']}")
                self.logger.info(f"Identical files: {results['files_identical']}")
                self.logger.info(f"Files only in pre: {results['only_in_pre']}")
                self.logger.info(f"Files only in post: {results['only_in_post']}")
                self.logger.info(f"Difference rate: {results['difference_rate']:.1f}%")
                self.logger.info(f"Output folder: {results['output_folder']}")
                self.logger.info("=" * 80)
                
                return results
                
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}")
            raise
        finally:
            shutdown_logging()


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="API Testing Framework - Compare test results between two runs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two test runs by folder name
  python compare_results.py 20250101_120000 20250101_130000
  
  # Compare with custom base folder
  python compare_results.py run1 run2 --base-folder /path/to/responses
  
  # Use custom config file
  python compare_results.py pre post --config /path/to/config.json
        """
    )
    
    parser.add_argument(
        'pre_folder',
        type=str,
        help='Name of the pre-change test folder'
    )
    
    parser.add_argument(
        'post_folder',
        type=str,
        help='Name of the post-change test folder'
    )
    
    parser.add_argument(
        '--base-folder',
        type=Path,
        help='Base folder containing test results (default: from config)'
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to configuration file (default: config.json)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize and run comparison
        runner = ComparisonRunner(config_file=args.config)
        results = runner.compare_test_runs(
            pre_folder=args.pre_folder,
            post_folder=args.post_folder,
            base_folder=args.base_folder
        )
        
        # Print summary
        print("\n" + "=" * 80)
        print("COMPARISON SUMMARY")
        print("=" * 80)
        print(f"Pre-test:  {results['pre_folder']}")
        print(f"Post-test: {results['post_folder']}")
        print(f"\nCommon Files: {results['total_common_files']}")
        print(f"  - Identical:     {results['files_identical']}")
        print(f"  - With Differences: {results['files_with_differences']} ({results['difference_rate']:.1f}%)")
        print(f"\nUnique Files:")
        print(f"  - Only in pre:  {results['only_in_pre']}")
        print(f"  - Only in post: {results['only_in_post']}")
        print(f"\nOutput Folder: {results['output_folder']}")
        print(f"Timestamp: {results['timestamp']}")
        print("=" * 80)
        
        # Exit with appropriate code
        if results['files_with_differences'] > 0:
            print(f"\n⚠️  Found differences in {results['files_with_differences']} file(s)")
            print(f"Check the output folder for detailed comparison reports.")
            return 0  # Still success, just with differences
        else:
            print(f"\n✅ All files are identical!")
            return 0
        
    except KeyboardInterrupt:
        print("\n\nComparison interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\nERROR: Comparison failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())