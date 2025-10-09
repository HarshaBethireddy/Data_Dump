"""
JSON utilities for comparison, validation, and manipulation.

This module provides enterprise-grade JSON processing capabilities with
deep comparison, validation, and transformation features.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Union, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from refactored_codebase.utils.logging import get_logger


class ComparisonResult(str, Enum):
    """JSON comparison results."""
    IDENTICAL = "identical"
    DIFFERENT = "different"
    STRUCTURE_DIFFERENT = "structure_different"
    VALUES_DIFFERENT = "values_different"
    ERROR = "error"


@dataclass
class JSONDifference:
    """Represents a difference between two JSON objects."""
    path: str
    difference_type: str
    old_value: Any
    new_value: Any
    description: str


@dataclass
class ComparisonReport:
    """Comprehensive comparison report."""
    result: ComparisonResult
    differences: List[JSONDifference]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]
    
    @property
    def is_identical(self) -> bool:
        """Check if objects are identical."""
        return self.result == ComparisonResult.IDENTICAL
    
    @property
    def difference_count(self) -> int:
        """Get total number of differences."""
        return len(self.differences)


class JSONValidator:
    """JSON validation utilities."""
    
    def __init__(self):
        """Initialize JSON validator."""
        self.logger = get_logger(self.__class__.__name__)
    
    def validate_json_string(self, json_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON string.
        
        Args:
            json_string: JSON string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            json.loads(json_string)
            return True, None
        except json.JSONDecodeError as e:
            return False, str(e)
    
    def validate_json_file(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not file_path.exists():
                return False, f"File does not exist: {file_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"
    
    def validate_structure(self, data: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate JSON structure has required keys.
        
        Args:
            data: JSON data to validate
            required_keys: List of required keys
            
        Returns:
            Tuple of (is_valid, missing_keys)
        """
        missing_keys = []
        for key in required_keys:
            if key not in data:
                missing_keys.append(key)
        
        return len(missing_keys) == 0, missing_keys


class JSONComparator:
    """
    Advanced JSON comparison with detailed difference reporting.
    
    Features:
    - Deep comparison with path tracking
    - Type-aware comparisons
    - Configurable comparison options
    - Detailed difference reporting
    - Performance optimized for large objects
    """
    
    def __init__(self, ignore_order: bool = False, ignore_keys: Optional[Set[str]] = None):
        """
        Initialize JSON comparator.
        
        Args:
            ignore_order: Whether to ignore array order
            ignore_keys: Set of keys to ignore during comparison
        """
        self.ignore_order = ignore_order
        self.ignore_keys = ignore_keys or set()
        self.logger = get_logger(self.__class__.__name__)
    
    def compare(self, obj1: Any, obj2: Any, path: str = "") -> ComparisonReport:
        """
        Compare two JSON objects and generate detailed report.
        
        Args:
            obj1: First JSON object
            obj2: Second JSON object
            path: Current path in object hierarchy
            
        Returns:
            Comprehensive comparison report
        """
        differences = []
        metadata = {
            "comparison_started": True,
            "ignore_order": self.ignore_order,
            "ignore_keys": list(self.ignore_keys)
        }
        
        try:
            self._compare_recursive(obj1, obj2, path, differences)
            
            # Determine overall result
            if not differences:
                result = ComparisonResult.IDENTICAL
            else:
                # Analyze difference types
                has_structure_diff = any(
                    diff.difference_type in ["key_missing", "key_added", "type_mismatch"]
                    for diff in differences
                )
                result = ComparisonResult.STRUCTURE_DIFFERENT if has_structure_diff else ComparisonResult.VALUES_DIFFERENT
            
            # Generate summary
            summary = self._generate_summary(differences, obj1, obj2)
            
        except Exception as e:
            self.logger.error(f"Comparison error: {e}")
            result = ComparisonResult.ERROR
            differences = [JSONDifference(
                path="",
                difference_type="error",
                old_value=None,
                new_value=None,
                description=f"Comparison failed: {e}"
            )]
            summary = {"error": str(e)}
        
        return ComparisonReport(
            result=result,
            differences=differences,
            summary=summary,
            metadata=metadata
        )
    
    def _compare_recursive(self, obj1: Any, obj2: Any, path: str, differences: List[JSONDifference]) -> None:
        """Recursively compare objects and collect differences."""
        
        # Type comparison
        if type(obj1) != type(obj2):
            differences.append(JSONDifference(
                path=path,
                difference_type="type_mismatch",
                old_value=type(obj1).__name__,
                new_value=type(obj2).__name__,
                description=f"Type mismatch at {path}: {type(obj1).__name__} vs {type(obj2).__name__}"
            ))
            return
        
        # Handle different types
        if isinstance(obj1, dict):
            self._compare_dicts(obj1, obj2, path, differences)
        elif isinstance(obj1, list):
            self._compare_lists(obj1, obj2, path, differences)
        else:
            self._compare_values(obj1, obj2, path, differences)
    
    def _compare_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any], path: str, differences: List[JSONDifference]) -> None:
        """Compare dictionary objects."""
        # Filter out ignored keys
        keys1 = set(dict1.keys()) - self.ignore_keys
        keys2 = set(dict2.keys()) - self.ignore_keys
        
        # Find missing and added keys
        missing_keys = keys1 - keys2
        added_keys = keys2 - keys1
        common_keys = keys1 & keys2
        
        # Report missing keys
        for key in missing_keys:
            differences.append(JSONDifference(
                path=f"{path}.{key}" if path else key,
                difference_type="key_missing",
                old_value=dict1[key],
                new_value=None,
                description=f"Key '{key}' missing in second object"
            ))
        
        # Report added keys
        for key in added_keys:
            differences.append(JSONDifference(
                path=f"{path}.{key}" if path else key,
                difference_type="key_added",
                old_value=None,
                new_value=dict2[key],
                description=f"Key '{key}' added in second object"
            ))
        
        # Compare common keys
        for key in common_keys:
            new_path = f"{path}.{key}" if path else key
            self._compare_recursive(dict1[key], dict2[key], new_path, differences)
    
    def _compare_lists(self, list1: List[Any], list2: List[Any], path: str, differences: List[JSONDifference]) -> None:
        """Compare list objects."""
        if len(list1) != len(list2):
            differences.append(JSONDifference(
                path=path,
                difference_type="length_mismatch",
                old_value=len(list1),
                new_value=len(list2),
                description=f"Array length mismatch at {path}: {len(list1)} vs {len(list2)}"
            ))
        
        if self.ignore_order:
            # Compare as sets (order-independent)
            self._compare_lists_unordered(list1, list2, path, differences)
        else:
            # Compare element by element (order-dependent)
            max_len = max(len(list1), len(list2))
            for i in range(max_len):
                new_path = f"{path}[{i}]"
                
                if i >= len(list1):
                    differences.append(JSONDifference(
                        path=new_path,
                        difference_type="element_added",
                        old_value=None,
                        new_value=list2[i],
                        description=f"Element added at {new_path}"
                    ))
                elif i >= len(list2):
                    differences.append(JSONDifference(
                        path=new_path,
                        difference_type="element_missing",
                        old_value=list1[i],
                        new_value=None,
                        description=f"Element missing at {new_path}"
                    ))
                else:
                    self._compare_recursive(list1[i], list2[i], new_path, differences)
    
    def _compare_lists_unordered(self, list1: List[Any], list2: List[Any], path: str, differences: List[JSONDifference]) -> None:
        """Compare lists ignoring order."""
        # Convert to JSON strings for comparison
        set1 = {json.dumps(item, sort_keys=True) for item in list1}
        set2 = {json.dumps(item, sort_keys=True) for item in list2}
        
        missing_items = set1 - set2
        added_items = set2 - set1
        
        for item_json in missing_items:
            differences.append(JSONDifference(
                path=path,
                difference_type="item_missing",
                old_value=json.loads(item_json),
                new_value=None,
                description=f"Item missing from second array at {path}"
            ))
        
        for item_json in added_items:
            differences.append(JSONDifference(
                path=path,
                difference_type="item_added",
                old_value=None,
                new_value=json.loads(item_json),
                description=f"Item added to second array at {path}"
            ))
    
    def _compare_values(self, val1: Any, val2: Any, path: str, differences: List[JSONDifference]) -> None:
        """Compare primitive values."""
        if val1 != val2:
            differences.append(JSONDifference(
                path=path,
                difference_type="value_mismatch",
                old_value=val1,
                new_value=val2,
                description=f"Value mismatch at {path}: '{val1}' vs '{val2}'"
            ))
    
    def _generate_summary(self, differences: List[JSONDifference], obj1: Any, obj2: Any) -> Dict[str, Any]:
        """Generate comparison summary."""
        diff_types = {}
        for diff in differences:
            diff_type = diff.difference_type
            diff_types[diff_type] = diff_types.get(diff_type, 0) + 1
        
        return {
            "total_differences": len(differences),
            "difference_types": diff_types,
            "objects_identical": len(differences) == 0,
            "obj1_hash": self._calculate_hash(obj1),
            "obj2_hash": self._calculate_hash(obj2)
        }
    
    def _calculate_hash(self, obj: Any) -> str:
        """Calculate hash of JSON object."""
        try:
            json_str = json.dumps(obj, sort_keys=True, ensure_ascii=False)
            return hashlib.sha256(json_str.encode('utf-8')).hexdigest()[:16]
        except Exception:
            return "hash_error"
    
    def compare_files(self, file1: Path, file2: Path) -> ComparisonReport:
        """
        Compare two JSON files.
        
        Args:
            file1: First JSON file
            file2: Second JSON file
            
        Returns:
            Comparison report
        """
        try:
            with open(file1, 'r', encoding='utf-8') as f:
                obj1 = json.load(f)
            
            with open(file2, 'r', encoding='utf-8') as f:
                obj2 = json.load(f)
            
            report = self.compare(obj1, obj2)
            report.metadata.update({
                "file1": str(file1),
                "file2": str(file2)
            })
            
            return report
            
        except Exception as e:
            self.logger.error(f"File comparison error: {e}")
            return ComparisonReport(
                result=ComparisonResult.ERROR,
                differences=[JSONDifference(
                    path="",
                    difference_type="file_error",
                    old_value=str(file1),
                    new_value=str(file2),
                    description=f"File comparison failed: {e}"
                )],
                summary={"error": str(e)},
                metadata={"file1": str(file1), "file2": str(file2)}
            )


def normalize_json(data: Any, sort_keys: bool = True) -> str:
    """
    Normalize JSON data to string for consistent comparison.
    
    Args:
        data: JSON data to normalize
        sort_keys: Whether to sort keys
        
    Returns:
        Normalized JSON string
    """
    return json.dumps(data, sort_keys=sort_keys, ensure_ascii=False, separators=(',', ':'))


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def extract_json_paths(data: Any, prefix: str = "") -> List[str]:
    """
    Extract all JSON paths from an object.
    
    Args:
        data: JSON data
        prefix: Path prefix
        
    Returns:
        List of JSON paths
    """
    paths = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            paths.append(current_path)
            paths.extend(extract_json_paths(value, current_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{prefix}[{i}]"
            paths.append(current_path)
            paths.extend(extract_json_paths(item, current_path))
    
    return paths