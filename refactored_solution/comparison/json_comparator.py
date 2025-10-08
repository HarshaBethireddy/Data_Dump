"""
Enhanced JSON comparison with better error handling and analysis.
"""
import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from ..utils.logger import framework_logger


class JSONComparator:
    """Enhanced JSON file comparator with comprehensive analysis."""
    
    def __init__(self, output_folder: str):
        self.output_folder = output_folder
        self.logger = framework_logger.get_logger()
        os.makedirs(output_folder, exist_ok=True)
    
    def compare_folders(self, folder1: str, folder2: str, folder1_name: str, folder2_name: str) -> Dict[str, Any]:
        """Compare all JSON files between two folders."""
        try:
            self.logger.info(f"Starting comparison: {folder1_name} vs {folder2_name}")
            
            # Validate folders exist
            if not os.path.exists(folder1):
                raise FileNotFoundError(f"Folder not found: {folder1}")
            if not os.path.exists(folder2):
                raise FileNotFoundError(f"Folder not found: {folder2}")
            
            # Get JSON files from both folders
            files1 = {f.stem: f for f in Path(folder1).glob('*.json')}
            files2 = {f.stem: f for f in Path(folder2).glob('*.json')}
            
            # Find common files
            common_files = set(files1.keys()).intersection(set(files2.keys()))
            only_in_folder1 = set(files1.keys()) - set(files2.keys())
            only_in_folder2 = set(files2.keys()) - set(files1.keys())
            
            self.logger.info(f"Found {len(common_files)} common files, "
                           f"{len(only_in_folder1)} only in {folder1_name}, "
                           f"{len(only_in_folder2)} only in {folder2_name}")
            
            # Compare common files
            comparison_results = []
            files_with_differences = 0
            
            for file_key in sorted(common_files):
                file1 = files1[file_key]
                file2 = files2[file_key]
                
                differences = self._compare_json_files(file1, file2)
                
                if differences:
                    files_with_differences += 1
                    output_file = os.path.join(
                        self.output_folder, 
                        f"{file_key}_comparison_result.csv"
                    )
                    self._save_differences_to_csv(differences, output_file)
                    comparison_results.append({
                        'file': file_key,
                        'differences_count': len(differences),
                        'output_file': output_file
                    })
                    self.logger.info(f"Found {len(differences)} differences in {file_key}")
                else:
                    self.logger.info(f"No differences found in {file_key}")
            
            # Generate summary report
            summary = {
                'folder1_name': folder1_name,
                'folder2_name': folder2_name,
                'total_common_files': len(common_files),
                'files_with_differences': files_with_differences,
                'files_identical': len(common_files) - files_with_differences,
                'only_in_folder1': list(only_in_folder1),
                'only_in_folder2': list(only_in_folder2),
                'comparison_results': comparison_results
            }
            
            self._generate_summary_report(summary)
            
            self.logger.info(f"Comparison completed: {files_with_differences}/{len(common_files)} files have differences")
            return summary
            
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}")
            raise
    
    def _compare_json_files(self, file1: Path, file2: Path) -> List[Dict[str, Any]]:
        """Compare two JSON files and return differences."""
        try:
            # Check if files are empty
            if os.stat(file1).st_size == 0:
                self.logger.warning(f"File {file1} is empty")
                return [{'Path': 'FILE_STATUS', 'Value in File 1': 'EMPTY', 'Value in File 2': 'HAS_CONTENT', 'Comparison Result': False}]
            
            if os.stat(file2).st_size == 0:
                self.logger.warning(f"File {file2} is empty")
                return [{'Path': 'FILE_STATUS', 'Value in File 1': 'HAS_CONTENT', 'Value in File 2': 'EMPTY', 'Comparison Result': False}]
            
            # Load JSON files
            try:
                with open(file1, 'r', encoding='utf-8') as f1:
                    json1 = json.load(f1)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in {file1}: {e}")
                return [{'Path': 'JSON_PARSE_ERROR', 'Value in File 1': f'INVALID_JSON: {str(e)}', 'Value in File 2': 'VALID_JSON', 'Comparison Result': False}]
            
            try:
                with open(file2, 'r', encoding='utf-8') as f2:
                    json2 = json.load(f2)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in {file2}: {e}")
                return [{'Path': 'JSON_PARSE_ERROR', 'Value in File 1': 'VALID_JSON', 'Value in File 2': f'INVALID_JSON: {str(e)}', 'Comparison Result': False}]
            
            # Compare JSON structures
            differences = []
            self._compare_json_recursive(differences, json1, json2)
            
            return differences
            
        except Exception as e:
            self.logger.error(f"Error comparing {file1} and {file2}: {e}")
            return [{'Path': 'COMPARISON_ERROR', 'Value in File 1': str(e), 'Value in File 2': str(e), 'Comparison Result': False}]
    
    def _compare_json_recursive(self, differences: List[Dict[str, Any]], json1: Any, json2: Any, current_path: str = '') -> None:
        """Recursively compare JSON structures."""
        if isinstance(json1, dict) and isinstance(json2, dict):
            # Compare dictionaries
            all_keys = set(json1.keys()) | set(json2.keys())
            
            for key in all_keys:
                path = f"{current_path}.{key}" if current_path else key
                
                if key not in json1:
                    self._append_difference(differences, path, None, json2[key], False)
                elif key not in json2:
                    self._append_difference(differences, path, json1[key], None, False)
                else:
                    self._compare_json_recursive(differences, json1[key], json2[key], path)
        
        elif isinstance(json1, list) and isinstance(json2, list):
            # Compare lists
            if len(json1) != len(json2):
                self._append_difference(differences, f"{current_path}[LENGTH]", len(json1), len(json2), False)
            
            max_len = max(len(json1), len(json2))
            for i in range(max_len):
                path = f"{current_path}[{i}]"
                
                if i >= len(json1):
                    self._append_difference(differences, path, None, json2[i], False)
                elif i >= len(json2):
                    self._append_difference(differences, path, json1[i], None, False)
                else:
                    self._compare_json_recursive(differences, json1[i], json2[i], path)
        
        else:
            # Compare primitive values
            if json1 != json2:
                self._append_difference(differences, current_path, json1, json2, False)
    
    def _append_difference(self, differences: List[Dict[str, Any]], path: str, value1: Any, value2: Any, comparison_result: bool) -> None:
        """Add a difference to the results list."""
        differences.append({
            'Path': path,
            'Value in File 1': self._format_value(value1),
            'Value in File 2': self._format_value(value2),
            'Comparison Result': comparison_result
        })
    
    def _format_value(self, value: Any, max_length: int = 200) -> str:
        """Format a value for display in reports."""
        if value is None:
            return 'NULL'
        
        # Convert to string and clean up
        value_str = str(value).replace('\n', '').replace(',', ';')
        
        # Truncate if too long
        if len(value_str) > max_length:
            return value_str[:max_length] + '...'
        
        return value_str
    
    def _save_differences_to_csv(self, differences: List[Dict[str, Any]], output_file: str) -> None:
        """Save differences to a CSV file."""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Path', 'Value in File 1', 'Value in File 2', 'Comparison Result']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for diff in differences:
                    writer.writerow(diff)
            
            self.logger.info(f"Differences saved to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save differences to {output_file}: {e}")
            raise
    
    def _generate_summary_report(self, summary: Dict[str, Any]) -> None:
        """Generate a summary report of the comparison."""
        try:
            summary_file = os.path.join(self.output_folder, "comparison_summary.txt")
            
            with open(summary_file, 'w', encoding='utf-8') as file:
                file.write("JSON COMPARISON SUMMARY REPORT\n")
                file.write("=" * 50 + "\n\n")
                
                file.write(f"Comparison: {summary['folder1_name']} vs {summary['folder2_name']}\n")
                file.write(f"Generated: {Path().absolute()}\n\n")
                
                file.write("STATISTICS:\n")
                file.write(f"  Total common files: {summary['total_common_files']}\n")
                file.write(f"  Files with differences: {summary['files_with_differences']}\n")
                file.write(f"  Identical files: {summary['files_identical']}\n")
                file.write(f"  Files only in {summary['folder1_name']}: {len(summary['only_in_folder1'])}\n")
                file.write(f"  Files only in {summary['folder2_name']}: {len(summary['only_in_folder2'])}\n\n")
                
                if summary['only_in_folder1']:
                    file.write(f"FILES ONLY IN {summary['folder1_name']}:\n")
                    for filename in summary['only_in_folder1']:
                        file.write(f"  - {filename}\n")
                    file.write("\n")
                
                if summary['only_in_folder2']:
                    file.write(f"FILES ONLY IN {summary['folder2_name']}:\n")
                    for filename in summary['only_in_folder2']:
                        file.write(f"  - {filename}\n")
                    file.write("\n")
                
                if summary['comparison_results']:
                    file.write("FILES WITH DIFFERENCES:\n")
                    for result in summary['comparison_results']:
                        file.write(f"  - {result['file']}: {result['differences_count']} differences\n")
                        file.write(f"    Report: {result['output_file']}\n")
                else:
                    file.write("No differences found in any files! 🎉\n")
            
            self.logger.info(f"Summary report generated: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary report: {e}")


def compare_test_results(pre_folder: str, post_folder: str, output_base_folder: str = "CompareResult") -> Dict[str, Any]:
    """
    Compare test results between two folders.
    
    Args:
        pre_folder: Name of the pre-test folder
        post_folder: Name of the post-test folder
        output_base_folder: Base folder for comparison results
    
    Returns:
        Dictionary containing comparison summary
    """
    try:
        # Setup paths
        folder1 = os.path.join('TestResponse', pre_folder)
        folder2 = os.path.join('TestResponse', post_folder)
        output_folder = os.path.join(output_base_folder, f"{pre_folder}_vs_{post_folder}")
        
        # Create comparator and run comparison
        comparator = JSONComparator(output_folder)
        return comparator.compare_folders(folder1, folder2, pre_folder, post_folder)
        
    except Exception as e:
        logger = framework_logger.get_logger()
        logger.error(f"Failed to compare test results: {e}")
        raise