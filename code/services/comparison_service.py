"""
JSON comparison service with deep difference analysis.

This service provides:
- Deep recursive JSON comparison
- Difference detection and reporting
- CSV export of comparison results
- Summary report generation
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..config.settings import get_config
from ..core.constants import (
    COMPARISON_NULL_VALUE,
    COMPARISON_EMPTY_VALUE,
    COMPARISON_VALID_JSON,
    COMPARISON_INVALID_JSON,
    COMPARISON_ERROR,
    COMPARISON_FILE_SUFFIX,
    COMPARISON_SUMMARY_NAME
)
from ..core.exceptions import ComparisonError, JSONProcessingError
from ..core.models import (
    JSONDifference,
    FileComparisonResult,
    ComparisonSummary
)
from ..utils.file_handler import FileHandler, JSONHandler, CSVHandler
from ..utils.logger import get_logger, PerformanceLogger
from ..utils.validators import PathValidator


class JSONComparator:
    """
    Deep JSON comparison engine.
    
    Performs recursive comparison of JSON structures and identifies differences.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize JSON comparator.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or get_logger(__name__)
    
    def compare_values(
        self,
        value1: Any,
        value2: Any,
        path: str = ""
    ) -> List[JSONDifference]:
        """
        Compare two JSON values recursively.
        
        Args:
            value1: First value
            value2: Second value
            path: Current JSON path
            
        Returns:
            List of differences found
        """
        differences = []
        
        # Handle None/null values
        if value1 is None and value2 is None:
            return differences
        
        if value1 is None:
            differences.append(JSONDifference(
                path=path or "root",
                value_file1=COMPARISON_NULL_VALUE,
                value_file2=self._format_value(value2),
                difference_type="null_mismatch"
            ))
            return differences
        
        if value2 is None:
            differences.append(JSONDifference(
                path=path or "root",
                value_file1=self._format_value(value1),
                value_file2=COMPARISON_NULL_VALUE,
                difference_type="null_mismatch"
            ))
            return differences
        
        # Compare types
        type1 = type(value1)
        type2 = type(value2)
        
        if type1 != type2:
            differences.append(JSONDifference(
                path=path or "root",
                value_file1=f"{type1.__name__}: {self._format_value(value1)}",
                value_file2=f"{type2.__name__}: {self._format_value(value2)}",
                difference_type="type_mismatch"
            ))
            return differences
        
        # Compare by type
        if isinstance(value1, dict):
            differences.extend(self._compare_dicts(value1, value2, path))
        elif isinstance(value1, list):
            differences.extend(self._compare_lists(value1, value2, path))
        else:
            # Primitive types (str, int, float, bool)
            if value1 != value2:
                differences.append(JSONDifference(
                    path=path or "root",
                    value_file1=self._format_value(value1),
                    value_file2=self._format_value(value2),
                    difference_type="value_mismatch"
                ))
        
        return differences
    
    def _compare_dicts(
        self,
        dict1: Dict[str, Any],
        dict2: Dict[str, Any],
        path: str
    ) -> List[JSONDifference]:
        """
        Compare two dictionaries.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            path: Current JSON path
            
        Returns:
            List of differences found
        """
        differences = []
        
        # Get all keys from both dicts
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        for key in sorted(all_keys):
            current_path = f"{path}.{key}" if path else key
            
            if key not in dict1:
                differences.append(JSONDifference(
                    path=current_path,
                    value_file1="KEY_MISSING",
                    value_file2=self._format_value(dict2[key]),
                    difference_type="missing_key"
                ))
            elif key not in dict2:
                differences.append(JSONDifference(
                    path=current_path,
                    value_file1=self._format_value(dict1[key]),
                    value_file2="KEY_MISSING",
                    difference_type="missing_key"
                ))
            else:
                # Recursively compare values
                differences.extend(
                    self.compare_values(dict1[key], dict2[key], current_path)
                )
        
        return differences
    
    def _compare_lists(
        self,
        list1: List[Any],
        list2: List[Any],
        path: str
    ) -> List[JSONDifference]:
        """
        Compare two lists.
        
        Args:
            list1: First list
            list2: Second list
            path: Current JSON path
            
        Returns:
            List of differences found
        """
        differences = []
        
        # Compare lengths
        if len(list1) != len(list2):
            differences.append(JSONDifference(
                path=f"{path}[LENGTH]",
                value_file1=str(len(list1)),
                value_file2=str(len(list2)),
                difference_type="length_mismatch"
            ))
        
        # Compare elements
        max_length = max(len(list1), len(list2))
        
        for i in range(max_length):
            current_path = f"{path}[{i}]"
            
            if i >= len(list1):
                differences.append(JSONDifference(
                    path=current_path,
                    value_file1="INDEX_OUT_OF_RANGE",
                    value_file2=self._format_value(list2[i]),
                    difference_type="missing_index"
                ))
            elif i >= len(list2):
                differences.append(JSONDifference(
                    path=current_path,
                    value_file1=self._format_value(list1[i]),
                    value_file2="INDEX_OUT_OF_RANGE",
                    difference_type="missing_index"
                ))
            else:
                # Recursively compare elements
                differences.extend(
                    self.compare_values(list1[i], list2[i], current_path)
                )
        
        return differences
    
    def _format_value(self, value: Any, max_length: int = 200) -> str:
        """
        Format a value for display in reports.
        
        Args:
            value: Value to format
            max_length: Maximum string length
            
        Returns:
            Formatted string representation
        """
        if value is None:
            return COMPARISON_NULL_VALUE
        
        # Convert to string
        value_str = str(value)
        
        # Clean up
        value_str = value_str.replace('\n', ' ').replace(',', ';')
        
        # Truncate if too long
        if len(value_str) > max_length:
            return value_str[:max_length] + '...'
        
        return value_str


class ComparisonService:
    """
    Main service for comparing JSON files between folders.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize comparison service.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or get_logger(__name__)
        self.config = get_config()
        self.comparator = JSONComparator(self.logger)
    
    def _get_json_files(self, folder: Path) -> Dict[str, Path]:
        """
        Get all JSON files from a folder.
        
        Args:
            folder: Folder to search
            
        Returns:
            Dictionary mapping file names (without extension) to paths
        """
        json_files = FileHandler.list_files(folder, "*.json")
        return {file.stem: file for file in json_files}
    
    def _compare_single_file(
        self,
        file1: Path,
        file2: Path,
        file_name: str
    ) -> FileComparisonResult:
        """
        Compare two JSON files.
        
        Args:
            file1: First file path
            file2: Second file path
            file_name: Base file name
            
        Returns:
            FileComparisonResult with differences
        """
        try:
            # Check if files are empty
            file1_size = file1.stat().st_size
            file2_size = file2.stat().st_size
            
            if file1_size == 0 and file2_size == 0:
                return FileComparisonResult(
                    file_name=file_name,
                    has_differences=False,
                    differences=[],
                    file1_status=COMPARISON_EMPTY_VALUE,
                    file2_status=COMPARISON_EMPTY_VALUE
                )
            
            if file1_size == 0:
                return FileComparisonResult(
                    file_name=file_name,
                    has_differences=True,
                    differences=[JSONDifference(
                        path="FILE_STATUS",
                        value_file1=COMPARISON_EMPTY_VALUE,
                        value_file2="HAS_CONTENT",
                        difference_type="file_empty"
                    )],
                    file1_status=COMPARISON_EMPTY_VALUE,
                    file2_status=COMPARISON_VALID_JSON
                )
            
            if file2_size == 0:
                return FileComparisonResult(
                    file_name=file_name,
                    has_differences=True,
                    differences=[JSONDifference(
                        path="FILE_STATUS",
                        value_file1="HAS_CONTENT",
                        value_file2=COMPARISON_EMPTY_VALUE,
                        difference_type="file_empty"
                    )],
                    file1_status=COMPARISON_VALID_JSON,
                    file2_status=COMPARISON_EMPTY_VALUE
                )
            
            # Load JSON files
            try:
                json1 = JSONHandler.read_json(file1)
                file1_status = COMPARISON_VALID_JSON
            except JSONProcessingError as e:
                self.logger.error(f"Invalid JSON in {file1}: {e}")
                return FileComparisonResult(
                    file_name=file_name,
                    has_differences=True,
                    differences=[JSONDifference(
                        path="JSON_PARSE_ERROR",
                        value_file1=f"{COMPARISON_INVALID_JSON}: {str(e)}",
                        value_file2=COMPARISON_VALID_JSON,
                        difference_type="parse_error"
                    )],
                    file1_status=COMPARISON_INVALID_JSON,
                    file2_status=COMPARISON_VALID_JSON
                )
            
            try:
                json2 = JSONHandler.read_json(file2)
                file2_status = COMPARISON_VALID_JSON
            except JSONProcessingError as e:
                self.logger.error(f"Invalid JSON in {file2}: {e}")
                return FileComparisonResult(
                    file_name=file_name,
                    has_differences=True,
                    differences=[JSONDifference(
                        path="JSON_PARSE_ERROR",
                        value_file1=COMPARISON_VALID_JSON,
                        value_file2=f"{COMPARISON_INVALID_JSON}: {str(e)}",
                        difference_type="parse_error"
                    )],
                    file1_status=COMPARISON_VALID_JSON,
                    file2_status=COMPARISON_INVALID_JSON
                )
            
            # Compare JSON structures
            differences = self.comparator.compare_values(json1, json2)
            
            return FileComparisonResult(
                file_name=file_name,
                has_differences=len(differences) > 0,
                differences=differences,
                file1_status=file1_status,
                file2_status=file2_status
            )
            
        except Exception as e:
            self.logger.error(f"Error comparing {file_name}: {e}")
            return FileComparisonResult(
                file_name=file_name,
                has_differences=True,
                differences=[JSONDifference(
                    path=COMPARISON_ERROR,
                    value_file1=str(e),
                    value_file2=str(e),
                    difference_type="comparison_error"
                )],
                file1_status=COMPARISON_ERROR,
                file2_status=COMPARISON_ERROR
            )
    
    def _save_comparison_csv(
        self,
        result: FileComparisonResult,
        output_folder: Path
    ) -> Path:
        """
        Save comparison result to CSV file.
        
        Args:
            result: Comparison result
            output_folder: Output folder
            
        Returns:
            Path to saved CSV file
        """
        import pandas as pd
        
        csv_file = output_folder / f"{result.file_name}{COMPARISON_FILE_SUFFIX}.csv"
        
        # Convert differences to DataFrame
        data = []
        for diff in result.differences:
            data.append({
                'Path': diff.path,
                'Value in File 1': diff.value_file1,
                'Value in File 2': diff.value_file2,
                'Difference Type': diff.difference_type
            })
        
        df = pd.DataFrame(data)
        CSVHandler.write_dataframe_to_csv(df, csv_file)
        
        return csv_file
    
    def _generate_summary_report(
        self,
        summary: ComparisonSummary,
        output_folder: Path
    ) -> None:
        """
        Generate text summary report.
        
        Args:
            summary: Comparison summary
            output_folder: Output folder
        """
        summary_file = output_folder / COMPARISON_SUMMARY_NAME
        
        lines = [
            "JSON COMPARISON SUMMARY REPORT",
            "=" * 80,
            "",
            f"Comparison: {summary.folder1_name} vs {summary.folder2_name}",
            f"Generated: {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "STATISTICS:",
            f"  Total common files: {summary.total_common_files}",
            f"  Files with differences: {summary.files_with_differences}",
            f"  Identical files: {summary.files_identical}",
            f"  Files only in {summary.folder1_name}: {len(summary.only_in_folder1)}",
            f"  Files only in {summary.folder2_name}: {len(summary.only_in_folder2)}",
            ""
        ]
        
        if summary.only_in_folder1:
            lines.append(f"FILES ONLY IN {summary.folder1_name}:")
            for filename in sorted(summary.only_in_folder1):
                lines.append(f"  - {filename}")
            lines.append("")
        
        if summary.only_in_folder2:
            lines.append(f"FILES ONLY IN {summary.folder2_name}:")
            for filename in sorted(summary.only_in_folder2):
                lines.append(f"  - {filename}")
            lines.append("")
        
        if summary.comparison_results:
            lines.append("FILES WITH DIFFERENCES:")
            for result in summary.comparison_results:
                if result.has_differences:
                    lines.append(
                        f"  - {result.file_name}: {result.difference_count} differences"
                    )
        else:
            lines.append("No differences found in any files! 🎉")
        
        FileHandler.write_text_file(summary_file, "\n".join(lines))
        self.logger.info(f"Summary report saved: {summary_file}")
    
    def compare_folders(
        self,
        folder1: Path,
        folder2: Path,
        folder1_name: str,
        folder2_name: str,
        output_folder: Optional[Path] = None
    ) -> ComparisonSummary:
        """
        Compare all JSON files between two folders.
        
        Args:
            folder1: First folder to compare
            folder2: Second folder to compare
            folder1_name: Display name for first folder
            folder2_name: Display name for second folder
            output_folder: Output folder for results (auto-generated if None)
            
        Returns:
            ComparisonSummary with results
            
        Raises:
            ComparisonError: If comparison fails
        """
        try:
            with PerformanceLogger(self.logger, f"Compare {folder1_name} vs {folder2_name}"):
                # Validate folders
                PathValidator.validate_directory_exists(folder1, f"Folder '{folder1_name}'")
                PathValidator.validate_directory_exists(folder2, f"Folder '{folder2_name}'")
                
                # Create output folder if not provided
                if output_folder is None:
                    output_folder = (
                        self.config.paths.output_comparisons /
                        f"{folder1_name}_vs_{folder2_name}"
                    )
                
                FileHandler.ensure_directory(output_folder)
                
                # Get JSON files from both folders
                files1 = self._get_json_files(folder1)
                files2 = self._get_json_files(folder2)
                
                # Find common and unique files
                common_files = set(files1.keys()) & set(files2.keys())
                only_in_folder1 = set(files1.keys()) - set(files2.keys())
                only_in_folder2 = set(files2.keys()) - set(files1.keys())
                
                self.logger.info(
                    f"Found {len(common_files)} common files, "
                    f"{len(only_in_folder1)} only in {folder1_name}, "
                    f"{len(only_in_folder2)} only in {folder2_name}"
                )
                
                # Compare common files
                comparison_results = []
                files_with_differences = 0
                
                for file_name in sorted(common_files):
                    result = self._compare_single_file(
                        file1=files1[file_name],
                        file2=files2[file_name],
                        file_name=file_name
                    )
                    
                    comparison_results.append(result)
                    
                    if result.has_differences:
                        files_with_differences += 1
                        # Save differences to CSV
                        self._save_comparison_csv(result, output_folder)
                        self.logger.info(
                            f"Found {result.difference_count} differences in {file_name}"
                        )
                    else:
                        self.logger.debug(f"No differences found in {file_name}")
                
                # Create summary
                summary = ComparisonSummary(
                    folder1_name=folder1_name,
                    folder2_name=folder2_name,
                    total_common_files=len(common_files),
                    files_with_differences=files_with_differences,
                    files_identical=len(common_files) - files_with_differences,
                    only_in_folder1=sorted(only_in_folder1),
                    only_in_folder2=sorted(only_in_folder2),
                    comparison_results=comparison_results,
                    timestamp=datetime.now()
                )
                
                # Generate summary report
                self._generate_summary_report(summary, output_folder)
                
                self.logger.info(
                    f"Comparison completed: {files_with_differences}/{len(common_files)} "
                    f"files have differences"
                )
                
                return summary
                
        except Exception as e:
            if isinstance(e, ComparisonError):
                raise
            raise ComparisonError(
                "Failed to compare folders",
                file1=str(folder1),
                file2=str(folder2),
                original_error=e
            )