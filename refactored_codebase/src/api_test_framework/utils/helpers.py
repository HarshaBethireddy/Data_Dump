"""
Ultra-efficient helper utilities for common operations.

Provides high-performance string manipulation, date handling,
JSON operations, and other utility functions with minimal overhead.
"""

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from api_test_framework.core.logging import get_logger


class StringHelper:
    """Ultra-efficient string manipulation utilities."""
    
    @staticmethod
    def sanitize_filename(filename: str, replacement: str = "_") -> str:
        """Sanitize string for use as filename."""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', replacement, filename)
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        # Trim whitespace and dots
        sanitized = sanitized.strip(' .')
        # Ensure not empty
        return sanitized or "unnamed"
    
    @staticmethod
    def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate string to maximum length with suffix."""
        if len(text) <= max_length:
            return text
        
        if len(suffix) >= max_length:
            return text[:max_length]
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def camel_to_snake(camel_str: str) -> str:
        """Convert camelCase to snake_case."""
        # Insert underscore before uppercase letters
        snake_str = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', camel_str)
        return snake_str.lower()
    
    @staticmethod
    def snake_to_camel(snake_str: str, capitalize_first: bool = False) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split('_')
        if capitalize_first:
            return ''.join(word.capitalize() for word in components)
        else:
            return components[0] + ''.join(word.capitalize() for word in components[1:])
    
    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """Extract all numbers from text."""
        return re.findall(r'\d+', text)
    
    @staticmethod
    def mask_sensitive_data(text: str, patterns: Optional[Dict[str, str]] = None) -> str:
        """Mask sensitive data in text."""
        if patterns is None:
            patterns = {
                r'\b\d{3}-\d{2}-\d{4}\b': 'XXX-XX-XXXX',  # SSN
                r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b': 'XXXX-XXXX-XXXX-XXXX',  # Credit card
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': 'XXX@XXX.com',  # Email
            }
        
        masked_text = text
        for pattern, replacement in patterns.items():
            masked_text = re.sub(pattern, replacement, masked_text)
        
        return masked_text
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def pluralize(word: str, count: int) -> str:
        """Simple pluralization for English words."""
        if count == 1:
            return word
        
        # Simple rules for common cases
        if word.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return word + 'es'
        elif word.endswith('y') and word[-2] not in 'aeiou':
            return word[:-1] + 'ies'
        elif word.endswith('f'):
            return word[:-1] + 'ves'
        elif word.endswith('fe'):
            return word[:-2] + 'ves'
        else:
            return word + 's'


class DateHelper:
    """Ultra-efficient date and time utilities."""
    
    @staticmethod
    def now_utc() -> datetime:
        """Get current UTC datetime."""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def format_timestamp(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime as string."""
        if dt is None:
            dt = DateHelper.now_utc()
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_date_string(date_str: str, format_str: str = "%d%m%Y") -> datetime:
        """Parse date string to datetime object."""
        return datetime.strptime(date_str, format_str)
    
    @staticmethod
    def format_duration(duration_ms: float) -> str:
        """Format duration in milliseconds to human-readable string."""
        if duration_ms < 1000:
            return f"{duration_ms:.1f}ms"
        elif duration_ms < 60000:
            return f"{duration_ms/1000:.1f}s"
        elif duration_ms < 3600000:
            minutes = duration_ms / 60000
            return f"{minutes:.1f}m"
        else:
            hours = duration_ms / 3600000
            return f"{hours:.1f}h"
    
    @staticmethod
    def get_timestamp_filename() -> str:
        """Get timestamp suitable for filename."""
        return DateHelper.now_utc().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def is_valid_date(date_str: str, format_str: str = "%d%m%Y") -> bool:
        """Check if date string is valid."""
        try:
            DateHelper.parse_date_string(date_str, format_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def days_between(date1: datetime, date2: datetime) -> int:
        """Calculate days between two dates."""
        return abs((date2 - date1).days)
    
    @staticmethod
    def add_timezone_if_naive(dt: datetime, tz: timezone = timezone.utc) -> datetime:
        """Add timezone to naive datetime."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tz)
        return dt


class JSONHelper:
    """Ultra-efficient JSON manipulation utilities."""
    
    @staticmethod
    def safe_json_loads(json_str: str, default: Any = None) -> Any:
        """Safely parse JSON string with default fallback."""
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(obj: Any, default: Any = None, **kwargs) -> str:
        """Safely serialize object to JSON with default fallback."""
        try:
            return json.dumps(obj, **kwargs)
        except (TypeError, ValueError):
            if default is not None:
                return str(default)
            return "{}"
    
    @staticmethod
    def flatten_json(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """Flatten nested JSON structure."""
        def _flatten(obj: Any, parent_key: str = "") -> Dict[str, Any]:
            items = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{parent_key}{separator}{key}" if parent_key else key
                    items.extend(_flatten(value, new_key).items())
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    new_key = f"{parent_key}{separator}{i}" if parent_key else str(i)
                    items.extend(_flatten(value, new_key).items())
            else:
                return {parent_key: obj}
            
            return dict(items)
        
        return _flatten(data)
    
    @staticmethod
    def unflatten_json(data: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """Unflatten JSON structure."""
        result = {}
        
        for key, value in data.items():
            keys = key.split(separator)
            current = result
            
            for k in keys[:-1]:
                if k not in current:
                    # Check if next key is numeric (for arrays)
                    next_key = keys[keys.index(k) + 1]
                    current[k] = [] if next_key.isdigit() else {}
                current = current[k]
            
            final_key = keys[-1]
            if final_key.isdigit() and isinstance(current, list):
                # Extend list if necessary
                index = int(final_key)
                while len(current) <= index:
                    current.append(None)
                current[index] = value
            else:
                current[final_key] = value
        
        return result
    
    @staticmethod
    def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = JSONHelper.deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def extract_values_by_key(data: Any, target_key: str) -> List[Any]:
        """Extract all values for a specific key from nested structure."""
        values = []
        
        def _extract(obj: Any):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == target_key:
                        values.append(value)
                    _extract(value)
            elif isinstance(obj, list):
                for item in obj:
                    _extract(item)
        
        _extract(data)
        return values
    
    @staticmethod
    def remove_null_values(data: Any, remove_empty_strings: bool = False) -> Any:
        """Remove null values from JSON structure."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                cleaned_value = JSONHelper.remove_null_values(value, remove_empty_strings)
                if cleaned_value is not None:
                    if not (remove_empty_strings and cleaned_value == ""):
                        result[key] = cleaned_value
            return result
        elif isinstance(data, list):
            result = []
            for item in data:
                cleaned_item = JSONHelper.remove_null_values(item, remove_empty_strings)
                if cleaned_item is not None:
                    if not (remove_empty_strings and cleaned_item == ""):
                        result.append(cleaned_item)
            return result
        else:
            return data
    
    @staticmethod
    def get_nested_value(data: Dict[str, Any], path: str, separator: str = ".", default: Any = None) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split(separator)
        current = data
        
        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list) and key.isdigit():
                    current = current[int(key)]
                else:
                    return default
            return current
        except (KeyError, IndexError, TypeError):
            return default
    
    @staticmethod
    def set_nested_value(data: Dict[str, Any], path: str, value: Any, separator: str = ".") -> None:
        """Set value in nested dictionary using dot notation."""
        keys = path.split(separator)
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value


class ColorHelper:
    """ANSI color codes for terminal output."""
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'
    
    # Reset
    RESET = '\033[0m'
    
    @classmethod
    def colorize(cls, text: str, color: str, style: str = "") -> str:
        """Colorize text with ANSI codes."""
        return f"{style}{color}{text}{cls.RESET}"
    
    @classmethod
    def success(cls, text: str) -> str:
        """Format text as success (green)."""
        return cls.colorize(text, cls.GREEN, cls.BOLD)
    
    @classmethod
    def error(cls, text: str) -> str:
        """Format text as error (red)."""
        return cls.colorize(text, cls.RED, cls.BOLD)
    
    @classmethod
    def warning(cls, text: str) -> str:
        """Format text as warning (yellow)."""
        return cls.colorize(text, cls.YELLOW, cls.BOLD)
    
    @classmethod
    def info(cls, text: str) -> str:
        """Format text as info (blue)."""
        return cls.colorize(text, cls.BLUE)
    
    @classmethod
    def highlight(cls, text: str) -> str:
        """Highlight text (cyan, bold)."""
        return cls.colorize(text, cls.CYAN, cls.BOLD)