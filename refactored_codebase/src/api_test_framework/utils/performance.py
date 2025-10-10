"""
Ultra-efficient performance monitoring utilities.

Provides high-performance metrics collection, timing utilities,
and system resource monitoring with minimal overhead.
"""

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from api_test_framework.core.logging import get_logger


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """Mark operation as finished and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error_message = error_message
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the metrics."""
        self.metadata[key] = value


class PerformanceMonitor:
    """Ultra-efficient performance monitoring with minimal overhead."""
    
    def __init__(self):
        self.logger = get_logger("performance")
        self.metrics: List[PerformanceMetrics] = []
        self._active_operations: Dict[str, PerformanceMetrics] = {}
    
    @contextmanager
    def measure_operation(self, operation_name: str, **metadata):
        """Context manager for measuring operation performance."""
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata
        )
        
        try:
            yield metrics
            metrics.finish(success=True)
        except Exception as e:
            metrics.finish(success=False, error_message=str(e))
            raise
        finally:
            self.metrics.append(metrics)
            self._log_metrics(metrics)
    
    @asynccontextmanager
    async def measure_async_operation(self, operation_name: str, **metadata):
        """Async context manager for measuring operation performance."""
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata
        )
        
        try:
            yield metrics
            metrics.finish(success=True)
        except Exception as e:
            metrics.finish(success=False, error_message=str(e))
            raise
        finally:
            self.metrics.append(metrics)
            self._log_metrics(metrics)
    
    def start_operation(self, operation_name: str, **metadata) -> str:
        """Start measuring an operation and return operation ID."""
        operation_id = f"{operation_name}_{time.time()}_{id(self)}"
        
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata
        )
        
        self._active_operations[operation_id] = metrics
        return operation_id
    
    def finish_operation(self, operation_id: str, success: bool = True, error_message: Optional[str] = None) -> Optional[PerformanceMetrics]:
        """Finish measuring an operation."""
        if operation_id not in self._active_operations:
            self.logger.warning(f"Unknown operation ID: {operation_id}")
            return None
        
        metrics = self._active_operations.pop(operation_id)
        metrics.finish(success=success, error_message=error_message)
        
        self.metrics.append(metrics)
        self._log_metrics(metrics)
        
        return metrics
    
    def measure_function_call(self, func, *args, **kwargs):
        """Decorator/wrapper to measure function call performance."""
        operation_name = f"{func.__module__}.{func.__name__}"
        
        with self.measure_operation(operation_name) as metrics:
            metrics.add_metadata("args_count", len(args))
            metrics.add_metadata("kwargs_count", len(kwargs))
            
            result = func(*args, **kwargs)
            
            # Add result metadata if it's a simple type
            if isinstance(result, (str, int, float, bool)):
                metrics.add_metadata("result", result)
            elif hasattr(result, '__len__'):
                metrics.add_metadata("result_length", len(result))
            
            return result
    
    async def measure_async_function_call(self, func, *args, **kwargs):
        """Async wrapper to measure async function call performance."""
        operation_name = f"{func.__module__}.{func.__name__}"
        
        async with self.measure_async_operation(operation_name) as metrics:
            metrics.add_metadata("args_count", len(args))
            metrics.add_metadata("kwargs_count", len(kwargs))
            
            result = await func(*args, **kwargs)
            
            # Add result metadata if it's a simple type
            if isinstance(result, (str, int, float, bool)):
                metrics.add_metadata("result", result)
            elif hasattr(result, '__len__'):
                metrics.add_metadata("result_length", len(result))
            
            return result
    
    def get_operation_stats(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for operations."""
        if operation_name:
            filtered_metrics = [m for m in self.metrics if m.operation_name == operation_name]
        else:
            filtered_metrics = self.metrics
        
        if not filtered_metrics:
            return {}
        
        durations = [m.duration_ms for m in filtered_metrics if m.duration_ms is not None]
        successful_ops = [m for m in filtered_metrics if m.success]
        failed_ops = [m for m in filtered_metrics if not m.success]
        
        stats = {
            "total_operations": len(filtered_metrics),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "success_rate": (len(successful_ops) / len(filtered_metrics)) * 100 if filtered_metrics else 0,
        }
        
        if durations:
            stats.update({
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "total_duration_ms": sum(durations),
            })
            
            # Calculate percentiles
            sorted_durations = sorted(durations)
            stats.update({
                "p50_duration_ms": self._percentile(sorted_durations, 50),
                "p90_duration_ms": self._percentile(sorted_durations, 90),
                "p95_duration_ms": self._percentile(sorted_durations, 95),
                "p99_duration_ms": self._percentile(sorted_durations, 99),
            })
        
        return stats
    
    def get_all_operation_names(self) -> List[str]:
        """Get list of all operation names that have been measured."""
        return list(set(m.operation_name for m in self.metrics))
    
    def get_recent_metrics(self, count: int = 100) -> List[PerformanceMetrics]:
        """Get most recent metrics."""
        return self.metrics[-count:] if count < len(self.metrics) else self.metrics
    
    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        self.metrics.clear()
        self._active_operations.clear()
    
    def export_metrics(self, format_type: str = "json") -> Union[str, Dict[str, Any]]:
        """Export metrics in specified format."""
        if format_type == "json":
            import json
            metrics_data = []
            for m in self.metrics:
                metrics_data.append({
                    "operation_name": m.operation_name,
                    "start_time": m.start_time,
                    "end_time": m.end_time,
                    "duration_ms": m.duration_ms,
                    "success": m.success,
                    "error_message": m.error_message,
                    "metadata": m.metadata
                })
            return json.dumps(metrics_data, indent=2)
        
        elif format_type == "summary":
            summary = {}
            for op_name in self.get_all_operation_names():
                summary[op_name] = self.get_operation_stats(op_name)
            return summary
        
        elif format_type == "csv":
            lines = ["operation_name,duration_ms,success,start_time,end_time"]
            for m in self.metrics:
                lines.append(f"{m.operation_name},{m.duration_ms},{m.success},{m.start_time},{m.end_time}")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _log_metrics(self, metrics: PerformanceMetrics) -> None:
        """Log performance metrics."""
        if metrics.success:
            self.logger.info(
                f"Operation completed: {metrics.operation_name}",
                duration_ms=metrics.duration_ms,
                success=metrics.success,
                **metrics.metadata
            )
        else:
            self.logger.warning(
                f"Operation failed: {metrics.operation_name}",
                duration_ms=metrics.duration_ms,
                success=metrics.success,
                error=metrics.error_message,
                **metrics.metadata
            )
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0
        
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            
            if upper_index >= len(sorted_data):
                return sorted_data[-1]
            
            # Linear interpolation
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Convenience functions for global monitor
def measure_operation(operation_name: str, **metadata):
    """Convenience function for measuring operations."""
    return performance_monitor.measure_operation(operation_name, **metadata)


def measure_async_operation(operation_name: str, **metadata):
    """Convenience function for measuring async operations."""
    return performance_monitor.measure_async_operation(operation_name, **metadata)


def get_performance_stats(operation_name: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for getting performance statistics."""
    return performance_monitor.get_operation_stats(operation_name)


def performance_decorator(operation_name: Optional[str] = None):
    """Decorator for measuring function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            return performance_monitor.measure_function_call(func, *args, **kwargs)
        return wrapper
    return decorator


def async_performance_decorator(operation_name: Optional[str] = None):
    """Decorator for measuring async function performance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            return await performance_monitor.measure_async_function_call(func, *args, **kwargs)
        return wrapper
    return decorator


class TimingContext:
    """Simple timing context for quick measurements."""
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        print(f"{self.name}: {duration_ms:.2f}ms")
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Get duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None


def quick_timer(name: str = "operation"):
    """Quick timing context for simple measurements."""
    return TimingContext(name)