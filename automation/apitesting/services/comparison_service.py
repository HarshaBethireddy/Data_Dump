"""
JSON comparison service with deep difference analysis.

This service provides:
- Deep recursive JSON comparison
- Difference detection and reporting
- CSV export of comparison results
- Summary report generation
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from apitesting.config.settings import get_config
from apitesting.core.constants import (
    COMPARISON_NULL_VALUE,
    COMPARISON_EMPTY_VALUE,
    COMPARISON_VALID_JSON,
    COMPARISON_INVALID_JSON,
    COMPARISON_ERROR,
    COMPARISON_FILE_SUFFIX,
    COMPARISON_SUMMARY_NAME
)
from apitesting.core.exceptions import ComparisonError, JSONProcessingError
from apitesting.core.models import (
    JSONDifference,
    FileComparisonResult,
    ComparisonSummary
)
from apitesting.utils.file_handler import FileHandler, CSVHandler
from apitesting.utils.logger import get_logger, PerformanceLogger
from apitesting.utils.validators import PathValidator


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
    
    def compare_json_objects(
        self,
        obj1: Union[Dict, List, Any],
        obj2: Union[Dict, List, Any]
    ) -> List[JSONDifference]:
        """
        Public method to compare two JSON objects.
        
        Args:
            obj1: First JSON object
            obj2: Second JSON object
            
        Returns:
            List of all differences found
        """
        self.logger.debug(f"Starting comparison. Obj1 type: {type(obj1).__name__}, Obj2 type: {type(obj2).__name__}")
        
        differences = []
        self._compare_values(obj1, obj2, "", differences)
        
        self.logger.debug(f"Comparison complete. Found {len(differences)} differences")
        return differences
    
    def _compare_values(
        self,
        val1: Any,
        val2: Any,
        path: str,
        differences: List[JSONDifference]
    ) -> None:
        """
        Recursively compare two values and accumulate differences.
        
        Args:
            val1: First value
            val2: Second value
            path: Current path in JSON structure
            differences: List to accumulate differences
        """
        # Handle None cases
        if val1 is None and val2 is None:
            return
        
        if val1 is None:
            differences.append(JSONDifference(
                path=path if path else "root",
                value_file1=COMPARISON_NULL_VALUE,
                value_file2=self._format_value(val2),
                difference_type="null_mismatch"
            ))
            return
        
        if val2 is None:
            differences.append(JSONDifference(
                path=path if path else "root",
                value_file1=self._format_value(val1),
                value_file2=COMPARISON_NULL_VALUE,
                difference_type="null_mismatch"
            ))
            return
        
        # Get types
        type1 = type(val1)
        type2 = type(val2)
        
        # Type mismatch
        if type1 != type2:
            differences.append(JSONDifference(
                path=path if path else "root",
                value_file1=f"{type1.__name__}: {self._format_value(val1)}",
                value_file2=f"{type2.__name__}: {self._format_value(val2)}",
                difference_type="type_mismatch"
            ))
            return
        
        # Compare based on type
        if isinstance(val1, dict):
            self._compare_dicts(val1, val2, path, differences)
        elif isinstance(val1, list):
            self._compare_lists(val1, val2, path, differences)
        elif isinstance(val1, (str, int, float, bool)):
            # Primitive value comparison
            if val1 != val2:
                differences.append(JSONDifference(
                    path=path if path else "root",
                    value_file1=str(val1),
                    value_file2=str(val2),
                    difference_type="value_mismatch"
                ))
        else:
            # Other types - convert to string and compare
            str1 = str(val1)
            str2 = str(val2)
            if str1 != str2:
                differences.append(JSONDifference(
                    path=path if path else "root",
                    value_file1=str1,
                    value_file2=str2,
                    difference_type="value_mismatch"
                ))
    
    def _compare_dicts(
        self,
        dict1: Dict,
        dict2: Dict,
        parent_path: str,
        differences: List[JSONDifference]
    ) -> None:
        """
        Compare two dictionaries recursively.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            parent_path: Parent path
            differences: List to accumulate differences
        """
        all_keys = set(dict1.keys()) | set(dict2.keys())
        
        for key in sorted(all_keys):
            # Build the full path
            if parent_path:
                current_path = f"{parent_path}.{key}"
            else:
                current_path = str(key)
            
            # Check key existence
            if key not in dict1:
                differences.append(JSONDifference(
                    path=current_path,
                    value_file1="KEY_MISSING",
                    value_file2=self._format_value(dict2[key]),
                    difference_type="missing_key_in_file1"
                ))
            elif key not in dict2:
                differences.append(JSONDifference(
                    path=current_path,
                    value_file1=self._format_value(dict1[key]),
                    value_file2="KEY_MISSING",
                    difference_type="missing_key_in_file2"
                ))
            else:
                # Both keys exist - recursively compare values
                self._compare_values(dict1[key], dict2[key], current_path, differences)
    
    def _compare_lists(
        self,
        list1: List,
        list2: List,
        parent_path: str,
        differences: List[JSONDifference]
    ) -> None:
        """
        Compare two lists recursively.
        
        Args:
            list1: First list
            list2: Second list
            parent_path: Parent path
            differences: List to accumulate differences
        """
        # Length check
        if len(list1) != len(list2):
            differences.append(JSONDifference(
                path=f"{parent_path}[LENGTH]",
                value_file1=str(len(list1)),
                value_file2=str(len(list2)),
                difference_type="length_mismatch"
            ))
        
        # Compare elements
        max_len = max(len(list1), len(list2))
        
        for i in range(max_len):
            current_path = f"{parent_path}[{i}]"
            
            if i >= len(list1):
                differences.append(JSONDifference(
                    path=current_path,
                    value_file1="INDEX_OUT_OF_RANGE",
                    value_file2=self._format_value(list2[i]),
                    difference_type="missing_index_in_file1"
                ))
            elif i >= len(list2):
                differences.append(JSONDifference(
                    path=current_path,
                    value_file1=self._format_value(list1[i]),
                    value_file2="INDEX_OUT_OF_RANGE",
                    difference_type="missing_index_in_file2"
                ))
            else:
                # Both indices exist - recursively compare
                self._compare_values(list1[i], list2[i], current_path, differences)
    
    def _format_value(self, value: Any, max_length: int = 500) -> str:
        """
        Format a value for display.
        
        Args:
            value: Value to format
            max_length: Maximum length
            
        Returns:
            Formatted string
        """
        if value is None:
            return COMPARISON_NULL_VALUE
        
        try:
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            else:
                value_str = str(value)
            
            # Clean up
            value_str = value_str.replace('\n', ' ').replace('\r', '')
            
            # Truncate
            if len(value_str) > max_length:
                return value_str[:max_length] + '...'
            
            return value_str
        except Exception as e:
            return f"<FORMAT_ERROR: {str(e)}>"


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
        """Get all JSON files from a folder."""
        json_files = FileHandler.list_files(folder, "*.json")
        return {file.stem: file for file in json_files}
    
    # def _read_json_file(self, file_path: Path) -> Tuple[Any, str]:
    #     """
    #     Read and parse a JSON file.
        
    #     Args:
    #         file_path: Path to JSON file
            
    #     Returns:
    #         Tuple of (parsed_data, status)
    #     """
    #     try:
    #         # Check if empty
    #         if file_path.stat().st_size == 0:
    #             return None, COMPARISON_EMPTY_VALUE
            
    #         # Read file content
    #         with open(file_path, 'r', encoding='utf-8') as f:
    #             content = f.read()
            
    #         # Parse JSON
    #         data = json.loads(content)
            
    #         # Debug logging
    #         self.logger.info(f"Read {file_path.name}: type={type(data).__name__}, size={len(content)} bytes")
            
    #         return data, COMPARISON_VALID_JSON
            
    #     except json.JSONDecodeError as e:
    #         self.logger.error(f"JSON parse error in {file_path.name}: {e}")
    #         return None, f"{COMPARISON_INVALID_JSON}: Line {e.lineno}"
    #     except Exception as e:
    #         self.logger.error(f"Error reading {file_path.name}: {e}")
    #         return None, f"ERROR: {str(e)}"

    def _read_json_file(self, file_path: Path) -> Tuple[Any, str]:
        try:
            if file_path.stat().st_size == 0:
                return None, COMPARISON_EMPTY_VALUE

            # Use utf-8-sig to auto-strip BOM if present
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            # First parse
            data = json.loads(content)

            # If the top-level value is a string, try to parse again (stringified JSON case)
            if isinstance(data, str):
                inner = data.strip()
                try:
                    reparsed = json.loads(inner)
                    self.logger.info(
                        f"Read {file_path.name}: detected stringified JSON, reparsed to {type(reparsed).__name__}"
                    )
                    return reparsed, COMPARISON_VALID_JSON  # or a special status if you prefer
                except json.JSONDecodeError:
                    # It's truly just a string; return as-is
                    self.logger.info(
                        f"Read {file_path.name}: top-level JSON is a string ({len(data)} chars); not reparsed"
                    )
                    return data, COMPARISON_VALID_JSON  # or COMPARISON_VALID_JSON_STRING

            self.logger.info(
                f"Read {file_path.name}: type={type(data).__name__}, size={len(content)} bytes"
            )
            return data, COMPARISON_VALID_JSON

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error in {file_path.name}: {e}")
            return None, f"{COMPARISON_INVALID_JSON}: Line {e.lineno}"
        except Exception as e:
            self.logger.error(f"Error reading {file_path.name}: {e}")
            return None, f"ERROR: {str(e)}"
    
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
            self.logger.info(f"Comparing {file_name}...")
            
            # Read both files
            data1, status1 = self._read_json_file(file1)
            data2, status2 = self._read_json_file(file2)

            self.logger.info(f"File1 type: {type(data1).__name__}, File2 type: {type(data2).__name__}")
            
            # Handle empty files
            if status1 == COMPARISON_EMPTY_VALUE and status2 == COMPARISON_EMPTY_VALUE:
                return FileComparisonResult(
                    file_name=file_name,
                    has_differences=False,
                    differences=[],
                    file1_status=status1,
                    file2_status=status2
                )
            
            if status1 == COMPARISON_EMPTY_VALUE or status2 == COMPARISON_EMPTY_VALUE:
                return FileComparisonResult(
                    file_name=file_name,
                    has_differences=True,
                    differences=[JSONDifference(
                        path="FILE_STATUS",
                        value_file1=status1,
                        value_file2=status2,
                        difference_type="file_empty"
                    )],
                    file1_status=status1,
                    file2_status=status2
                )
            
            # Handle parse errors
            if not status1.startswith(COMPARISON_VALID_JSON) or not status2.startswith(COMPARISON_VALID_JSON):
                return FileComparisonResult(
                    file_name=file_name,
                    has_differences=True,
                    differences=[JSONDifference(
                        path="JSON_PARSE_ERROR",
                        value_file1=status1,
                        value_file2=status2,
                        difference_type="parse_error"
                    )],
                    file1_status=status1,
                    file2_status=status2
                )
            
            # Both files are valid - perform deep comparison
            self.logger.debug(f"Performing deep comparison of {file_name}")
            self.logger.debug(f"  File1 type: {type(data1).__name__}")
            self.logger.debug(f"  File2 type: {type(data2).__name__}")
            
            differences = self.comparator.compare_json_objects(data1, data2)
            
            self.logger.info(f"  Found {len(differences)} difference(s)")
            
            # Log first few differences for debugging
            if differences and len(differences) <= 5:
                for i, diff in enumerate(differences[:5], 1):
                    self.logger.debug(f"    Diff {i}: {diff.path}")
            
            return FileComparisonResult(
                file_name=file_name,
                has_differences=len(differences) > 0,
                differences=differences,
                file1_status=status1,
                file2_status=status2
            )
            
        except Exception as e:
            self.logger.error(f"Error comparing {file_name}: {e}", exc_info=True)
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
        
        # Prepare data rows
        rows = []
        for diff in result.differences:
            rows.append({
                'Path': diff.path,
                'Value in File 1': diff.value_file1,
                'Value in File 2': diff.value_file2,
                'Comparison Result': 'False'
            })
        
        # Create DataFrame and save
        if rows:
            df = pd.DataFrame(rows)
        else:
            # Empty DataFrame with correct columns
            df = pd.DataFrame(columns=['Path', 'Value in File 1', 'Value in File 2', 'Comparison Result'])
        
        CSVHandler.write_dataframe_to_csv(df, csv_file)
        
        self.logger.debug(f"Saved {len(rows)} row(s) to {csv_file.name}")
        
        return csv_file
    
    def _generate_summary_report(
        self,
        summary: ComparisonSummary,
        output_folder: Path
    ) -> None:
        """Generate text summary report."""
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
                    lines.append(f"  - {result.file_name}: {result.difference_count} difference(s)")
        
        if summary.files_identical == summary.total_common_files:
            lines.append("\n✓ All common files are identical!")
        
        FileHandler.write_text_file(summary_file, "\n".join(lines))
        self.logger.info(f"Summary saved: {summary_file}")
    
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
                
                # Create output folder
                if output_folder is None:
                    output_folder = (
                        self.config.paths.output_comparisons /
                        f"{folder1_name}_vs_{folder2_name}"
                    )
                
                FileHandler.ensure_directory(output_folder)
                
                # Get JSON files
                files1 = self._get_json_files(folder1)
                files2 = self._get_json_files(folder2)
                
                # Find common and unique files
                common_files = set(files1.keys()) & set(files2.keys())
                only_in_folder1 = set(files1.keys()) - set(files2.keys())
                only_in_folder2 = set(files2.keys()) - set(files1.keys())
                
                self.logger.info(
                    f"Found {len(common_files)} common, "
                    f"{len(only_in_folder1)} unique to {folder1_name}, "
                    f"{len(only_in_folder2)} unique to {folder2_name}"
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
                        self._save_comparison_csv(result, output_folder)
                
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
                    f"Comparison complete: {files_with_differences}/{len(common_files)} "
                    f"file(s) have differences"
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