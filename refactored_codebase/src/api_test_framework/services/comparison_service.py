"""
Ultra-efficient JSON comparison service with deep diff analysis.

Advanced comparison algorithms with semantic analysis, structural
comparison, and intelligent difference detection.
"""

import json
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from api_test_framework.core.logging import get_logger
from api_test_framework.models.response_models import APIResponse
from api_test_framework.models.test_models import ComparisonResult, ComparisonDifference, ComparisonType


class ComparisonService:
    """Ultra-efficient JSON comparison with advanced diff analysis."""
    
    def __init__(self):
        self.logger = get_logger("comparison")
        
        # Configurable comparison settings
        self.ignore_keys = {"timestamp", "created_at", "updated_at", "request_id"}
        self.numeric_tolerance = 0.001  # For floating point comparisons
        self.case_sensitive = True
    
    def compare_responses(
        self,
        response1: APIResponse,
        response2: APIResponse,
        comparison_type: ComparisonType = ComparisonType.STRUCTURAL
    ) -> ComparisonResult:
        """Compare two API responses with intelligent analysis."""
        
        result = ComparisonResult(
            comparison_name=f"Response Comparison: {response1.request_id} vs {response2.request_id}",
            comparison_type=comparison_type,
            source_id=response1.request_id,
            target_id=response2.request_id
        )
        
        # Compare response data
        self._deep_compare(
            response1.response_data,
            response2.response_data,
            result,
            path="response_data"
        )
        
        # Compare status codes
        if response1.status_code != response2.status_code:
            result.add_difference(
                "status_code",
                "VALUE_CHANGED",
                response1.status_code,
                response2.status_code,
                "ERROR"
            )
        
        # Compare success flags
        if response1.success != response2.success:
            result.add_difference(
                "success",
                "VALUE_CHANGED",
                response1.success,
                response2.success,
                "CRITICAL"
            )
        
        # Performance comparison
        if response1.metrics and response2.metrics:
            self._compare_metrics(response1.metrics, response2.metrics, result)
        
        result.total_fields_compared = self._count_fields(response1.response_data) + 3  # +3 for status, success, metrics
        result.are_equal = len(result.differences) == 0
        
        return result
    
    def compare_json_objects(
        self,
        obj1: Dict[str, Any],
        obj2: Dict[str, Any],
        comparison_name: str = "JSON Comparison",
        comparison_type: ComparisonType = ComparisonType.STRUCTURAL
    ) -> ComparisonResult:
        """Compare two JSON objects with deep analysis."""
        
        result = ComparisonResult(
            comparison_name=comparison_name,
            comparison_type=comparison_type
        )
        
        self._deep_compare(obj1, obj2, result, path="root")
        
        result.total_fields_compared = max(self._count_fields(obj1), self._count_fields(obj2))
        result.are_equal = len(result.differences) == 0
        
        return result
    
    def _deep_compare(
        self,
        obj1: Any,
        obj2: Any,
        result: ComparisonResult,
        path: str = ""
    ) -> None:
        """Perform deep comparison of two objects."""
        
        # Type comparison
        if type(obj1) != type(obj2):
            result.add_difference(
                path,
                "TYPE_CHANGED",
                type(obj1).__name__,
                type(obj2).__name__,
                "WARNING"
            )
            return
        
        # Null comparison
        if obj1 is None and obj2 is None:
            return
        
        if obj1 is None or obj2 is None:
            result.add_difference(
                path,
                "NULL_CHANGED",
                obj1,
                obj2,
                "WARNING"
            )
            return
        
        # Dictionary comparison
        if isinstance(obj1, dict):
            self._compare_dicts(obj1, obj2, result, path)
        
        # List comparison
        elif isinstance(obj1, list):
            self._compare_lists(obj1, obj2, result, path)
        
        # Numeric comparison with tolerance
        elif isinstance(obj1, (int, float)) and isinstance(obj2, (int, float)):
            if abs(obj1 - obj2) > self.numeric_tolerance:
                result.add_difference(
                    path,
                    "VALUE_CHANGED",
                    obj1,
                    obj2,
                    "INFO"
                )
        
        # String comparison
        elif isinstance(obj1, str) and isinstance(obj2, str):
            if not self.case_sensitive:
                obj1, obj2 = obj1.lower(), obj2.lower()
            
            if obj1 != obj2:
                # Detect if it's a minor change (whitespace, case, etc.)
                severity = "INFO" if obj1.strip() == obj2.strip() else "WARNING"
                result.add_difference(
                    path,
                    "VALUE_CHANGED",
                    obj1,
                    obj2,
                    severity
                )
        
        # Direct value comparison
        else:
            if obj1 != obj2:
                result.add_difference(
                    path,
                    "VALUE_CHANGED",
                    obj1,
                    obj2,
                    "INFO"
                )
    
    def _compare_dicts(
        self,
        dict1: Dict[str, Any],
        dict2: Dict[str, Any],
        result: ComparisonResult,
        path: str
    ) -> None:
        """Compare two dictionaries with key analysis."""
        
        keys1 = set(dict1.keys()) - self.ignore_keys
        keys2 = set(dict2.keys()) - self.ignore_keys
        
        # Missing keys
        for key in keys1 - keys2:
            result.add_difference(
                f"{path}.{key}",
                "KEY_REMOVED",
                dict1[key],
                None,
                "WARNING"
            )
        
        # Added keys
        for key in keys2 - keys1:
            result.add_difference(
                f"{path}.{key}",
                "KEY_ADDED",
                None,
                dict2[key],
                "INFO"
            )
        
        # Common keys - recursive comparison
        for key in keys1 & keys2:
            self._deep_compare(
                dict1[key],
                dict2[key],
                result,
                f"{path}.{key}"
            )
    
    def _compare_lists(
        self,
        list1: List[Any],
        list2: List[Any],
        result: ComparisonResult,
        path: str
    ) -> None:
        """Compare two lists with intelligent matching."""
        
        if len(list1) != len(list2):
            result.add_difference(
                f"{path}.length",
                "LENGTH_CHANGED",
                len(list1),
                len(list2),
                "WARNING"
            )
        
        # Compare elements up to the shorter length
        min_length = min(len(list1), len(list2))
        
        for i in range(min_length):
            self._deep_compare(
                list1[i],
                list2[i],
                result,
                f"{path}[{i}]"
            )
        
        # Handle extra elements in longer list
        if len(list1) > min_length:
            for i in range(min_length, len(list1)):
                result.add_difference(
                    f"{path}[{i}]",
                    "ITEM_REMOVED",
                    list1[i],
                    None,
                    "INFO"
                )
        
        if len(list2) > min_length:
            for i in range(min_length, len(list2)):
                result.add_difference(
                    f"{path}[{i}]",
                    "ITEM_ADDED",
                    None,
                    list2[i],
                    "INFO"
                )
    
    def _compare_metrics(
        self,
        metrics1: Any,
        metrics2: Any,
        result: ComparisonResult
    ) -> None:
        """Compare performance metrics with tolerance."""
        
        if hasattr(metrics1, 'response_time_ms') and hasattr(metrics2, 'response_time_ms'):
            time_diff = abs(metrics1.response_time_ms - metrics2.response_time_ms)
            
            # Flag significant performance differences (>20% change)
            if time_diff > metrics1.response_time_ms * 0.2:
                result.add_difference(
                    "metrics.response_time_ms",
                    "PERFORMANCE_CHANGE",
                    metrics1.response_time_ms,
                    metrics2.response_time_ms,
                    "WARNING"
                )
    
    def _count_fields(self, obj: Any, visited: Optional[Set] = None) -> int:
        """Count total fields in nested object structure."""
        if visited is None:
            visited = set()
        
        # Prevent infinite recursion
        obj_id = id(obj)
        if obj_id in visited:
            return 0
        visited.add(obj_id)
        
        if isinstance(obj, dict):
            count = len(obj)
            for value in obj.values():
                count += self._count_fields(value, visited)
            return count
        
        elif isinstance(obj, list):
            count = len(obj)
            for item in obj:
                count += self._count_fields(item, visited)
            return count
        
        else:
            return 1
    
    def generate_diff_summary(self, result: ComparisonResult) -> Dict[str, Any]:
        """Generate comprehensive diff summary with statistics."""
        
        # Group differences by type and severity
        by_type = {}
        by_severity = {}
        
        for diff in result.differences:
            by_type[diff.difference_type] = by_type.get(diff.difference_type, 0) + 1
            by_severity[diff.severity] = by_severity.get(diff.severity, 0) + 1
        
        return {
            "total_differences": len(result.differences),
            "similarity_percentage": result.get_similarity_percentage(),
            "differences_by_type": by_type,
            "differences_by_severity": by_severity,
            "critical_issues": len(result.get_differences_by_severity("CRITICAL")),
            "warnings": len(result.get_differences_by_severity("WARNING")),
            "info_changes": len(result.get_differences_by_severity("INFO")),
            "comparison_duration_ms": result.comparison_duration_ms,
        }
    
    def export_diff_report(
        self,
        result: ComparisonResult,
        format_type: str = "json"
    ) -> str:
        """Export comparison result in specified format."""
        
        if format_type == "json":
            return result.to_json()
        
        elif format_type == "summary":
            summary = self.generate_diff_summary(result)
            return json.dumps(summary, indent=2)
        
        elif format_type == "text":
            lines = [
                f"Comparison: {result.comparison_name}",
                f"Type: {result.comparison_type.value}",
                f"Equal: {result.are_equal}",
                f"Similarity: {result.get_similarity_percentage():.1f}%",
                f"Differences: {len(result.differences)}",
                "",
                "Differences:"
            ]
            
            for diff in result.differences:
                lines.append(
                    f"  {diff.path}: {diff.difference_type} "
                    f"({diff.old_value} → {diff.new_value}) [{diff.severity}]"
                )
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")