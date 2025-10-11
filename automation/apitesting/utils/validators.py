"""
Input validation utilities for the API testing framework.

This module provides validation functions for various input types,
ensuring data integrity and early error detection.
"""

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, List, Optional, Union

from apitesting.core.constants import (
    PREQUAL_APPID_LENGTH,
    REGULAR_APPID_MIN,
    REGULAR_APPID_MAX
)
from apitesting.core.exceptions import ValidationError


class PathValidator:
    """Validates file system paths."""
    
    @staticmethod
    def validate_file_exists(file_path: Union[str, Path], file_type: str = "File") -> Path:
        """
        Validate that a file exists.
        
        Args:
            file_path: Path to validate
            file_type: Description of file type for error messages
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If file does not exist
        """
        path = Path(file_path)
        if not path.exists():
            raise ValidationError(
                f"{file_type} not found",
                field="file_path",
                value=str(file_path)
            )
        if not path.is_file():
            raise ValidationError(
                f"Path is not a file: {file_path}",
                field="file_path",
                value=str(file_path)
            )
        return path
    
    @staticmethod
    def validate_directory_exists(
        directory_path: Union[str, Path],
        dir_type: str = "Directory"
    ) -> Path:
        """
        Validate that a directory exists.
        
        Args:
            directory_path: Path to validate
            dir_type: Description of directory type for error messages
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If directory does not exist
        """
        path = Path(directory_path)
        if not path.exists():
            raise ValidationError(
                f"{dir_type} not found",
                field="directory_path",
                value=str(directory_path)
            )
        if not path.is_dir():
            raise ValidationError(
                f"Path is not a directory: {directory_path}",
                field="directory_path",
                value=str(directory_path)
            )
        return path
    
    @staticmethod
    def validate_file_extension(
        file_path: Union[str, Path],
        expected_extension: str
    ) -> Path:
        """
        Validate file has the expected extension.
        
        Args:
            file_path: Path to validate
            expected_extension: Expected file extension (e.g., '.json')
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If file extension doesn't match
        """
        path = Path(file_path)
        if not expected_extension.startswith('.'):
            expected_extension = f'.{expected_extension}'
        
        if path.suffix.lower() != expected_extension.lower():
            raise ValidationError(
                f"Invalid file extension. Expected {expected_extension}, got {path.suffix}",
                field="file_extension",
                value=str(path.suffix)
            )
        return path
    
    @staticmethod
    def validate_writable_path(file_path: Union[str, Path]) -> Path:
        """
        Validate that a path is writable.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If path is not writable
        """
        path = Path(file_path)
        
        # Check if parent directory exists and is writable
        if path.exists():
            if not path.is_file():
                raise ValidationError(
                    f"Path exists but is not a file: {file_path}",
                    field="file_path",
                    value=str(file_path)
                )
            # Check if file is writable
            try:
                path.touch(exist_ok=True)
            except Exception as e:
                raise ValidationError(
                    f"File is not writable: {file_path}",
                    field="file_path",
                    value=str(file_path),
                    details={"error": str(e)}
                )
        else:
            # Check if parent directory is writable
            parent = path.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise ValidationError(
                        f"Cannot create parent directory: {parent}",
                        field="directory_path",
                        value=str(parent),
                        details={"error": str(e)}
                    )
            
            if not parent.is_dir():
                raise ValidationError(
                    f"Parent path is not a directory: {parent}",
                    field="directory_path",
                    value=str(parent)
                )
        
        return path


class AppIDValidator:
    """Validates APPID values for both regular and prequal data."""
    
    @staticmethod
    def validate_regular_appid(appid: Union[int, str]) -> int:
        """
        Validate regular APPID (integer).
        
        Args:
            appid: APPID to validate
            
        Returns:
            Validated APPID as integer
            
        Raises:
            ValidationError: If APPID is invalid
        """
        try:
            appid_int = int(appid)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                "Regular APPID must be a valid integer",
                field="appid",
                value=str(appid),
                details={"error": str(e)}
            )
        
        if appid_int < REGULAR_APPID_MIN or appid_int > REGULAR_APPID_MAX:
            raise ValidationError(
                f"Regular APPID must be between {REGULAR_APPID_MIN} and {REGULAR_APPID_MAX}",
                field="appid",
                value=str(appid_int)
            )
        
        return appid_int
    
    @staticmethod
    def validate_prequal_appid(appid: Union[int, str]) -> str:
        """
        Validate prequal APPID (20-digit string).
        
        Args:
            appid: APPID to validate
            
        Returns:
            Validated APPID as 20-digit string
            
        Raises:
            ValidationError: If APPID is invalid
        """
        appid_str = str(appid)
        
        # Remove any whitespace
        appid_str = appid_str.strip()
        
        # Check if it contains only digits
        if not appid_str.isdigit():
            raise ValidationError(
                "Prequal APPID must contain only digits",
                field="appid",
                value=appid_str
            )
        
        # Check length
        if len(appid_str) != PREQUAL_APPID_LENGTH:
            raise ValidationError(
                f"Prequal APPID must be exactly {PREQUAL_APPID_LENGTH} digits",
                field="appid",
                value=appid_str,
                details={"actual_length": len(appid_str)}
            )
        
        return appid_str
    
    @staticmethod
    def validate_appid_range(
        start_value: Union[int, str],
        increment: int,
        count: int,
        is_prequal: bool = False
    ) -> None:
        """
        Validate APPID range parameters.
        
        Args:
            start_value: Starting APPID value
            increment: Increment between APPIDs
            count: Number of APPIDs to generate
            is_prequal: Whether this is prequal data
            
        Raises:
            ValidationError: If range parameters are invalid
        """
        # Validate count
        if count < 1:
            raise ValidationError(
                "APPID count must be at least 1",
                field="count",
                value=count
            )
        
        if count > 10000:
            raise ValidationError(
                "APPID count cannot exceed 10000",
                field="count",
                value=count
            )
        
        # Validate increment
        if increment < 1:
            raise ValidationError(
                "APPID increment must be at least 1",
                field="increment",
                value=increment
            )
        
        # Validate start value based on type
        if is_prequal:
            AppIDValidator.validate_prequal_appid(start_value)
            
            # Check if range will overflow 20 digits
            try:
                start_decimal = Decimal(str(start_value))
                end_decimal = start_decimal + (Decimal(increment) * Decimal(count - 1))
                
                if len(str(int(end_decimal))) > PREQUAL_APPID_LENGTH:
                    raise ValidationError(
                        f"APPID range will exceed {PREQUAL_APPID_LENGTH} digits",
                        field="appid_range",
                        value=str(start_value),
                        details={
                            "start": str(start_value),
                            "end": str(int(end_decimal)),
                            "count": count
                        }
                    )
            except InvalidOperation as e:
                raise ValidationError(
                    "Invalid prequal APPID range calculation",
                    field="appid_range",
                    value=str(start_value),
                    details={"error": str(e)}
                )
        else:
            AppIDValidator.validate_regular_appid(start_value)
            
            # Check if range will overflow integer limits
            try:
                start_int = int(start_value)
                end_int = start_int + (increment * (count - 1))
                
                if end_int > REGULAR_APPID_MAX:
                    raise ValidationError(
                        f"APPID range will exceed maximum value {REGULAR_APPID_MAX}",
                        field="appid_range",
                        value=str(start_value),
                        details={
                            "start": start_int,
                            "end": end_int,
                            "count": count
                        }
                    )
            except (ValueError, OverflowError) as e:
                raise ValidationError(
                    "Invalid regular APPID range calculation",
                    field="appid_range",
                    value=str(start_value),
                    details={"error": str(e)}
                )


class URLValidator:
    """Validates URLs and API endpoints."""
    
    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            Validated URL
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not url:
            raise ValidationError(
                "URL cannot be empty",
                field="url",
                value=url
            )
        
        # Basic URL pattern matching
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$',  # path
            re.IGNORECASE
        )
        
        if not url_pattern.match(url):
            raise ValidationError(
                "Invalid URL format",
                field="url",
                value=url
            )
        
        return url
    
    @staticmethod
    def validate_host(host: str) -> str:
        """
        Validate host/domain name.
        
        Args:
            host: Host to validate
            
        Returns:
            Validated host
            
        Raises:
            ValidationError: If host is invalid
        """
        if not host:
            raise ValidationError(
                "Host cannot be empty",
                field="host",
                value=host
            )
        
        # Basic host pattern (domain or IP)
        host_pattern = re.compile(
            r'^(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$',  # IP
            re.IGNORECASE
        )
        
        if not host_pattern.match(host):
            raise ValidationError(
                "Invalid host format",
                field="host",
                value=host
            )
        
        return host


class NumericValidator:
    """Validates numeric values and ranges."""
    
    @staticmethod
    def validate_positive_integer(
        value: Any,
        field_name: str = "value",
        min_value: int = 1,
        max_value: Optional[int] = None
    ) -> int:
        """
        Validate positive integer.
        
        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value (optional)
            
        Returns:
            Validated integer
            
        Raises:
            ValidationError: If value is invalid
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"{field_name} must be a valid integer",
                field=field_name,
                value=str(value),
                details={"error": str(e)}
            )
        
        if int_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}",
                field=field_name,
                value=int_value
            )
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"{field_name} cannot exceed {max_value}",
                field=field_name,
                value=int_value
            )
        
        return int_value
    
    @staticmethod
    def validate_positive_float(
        value: Any,
        field_name: str = "value",
        min_value: float = 0.0,
        max_value: Optional[float] = None
    ) -> float:
        """
        Validate positive float.
        
        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value (optional)
            
        Returns:
            Validated float
            
        Raises:
            ValidationError: If value is invalid
        """
        try:
            float_value = float(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(
                f"{field_name} must be a valid number",
                field=field_name,
                value=str(value),
                details={"error": str(e)}
            )
        
        if float_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}",
                field=field_name,
                value=float_value
            )
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(
                f"{field_name} cannot exceed {max_value}",
                field=field_name,
                value=float_value
            )
        
        return float_value
    
    @staticmethod
    def validate_percentage(
        value: Any,
        field_name: str = "percentage"
    ) -> float:
        """
        Validate percentage value (0-100).
        
        Args:
            value: Value to validate
            field_name: Field name for error messages
            
        Returns:
            Validated percentage
            
        Raises:
            ValidationError: If value is invalid
        """
        return NumericValidator.validate_positive_float(
            value,
            field_name,
            min_value=0.0,
            max_value=100.0
        )


class StringValidator:
    """Validates string values."""
    
    @staticmethod
    def validate_non_empty_string(
        value: Any,
        field_name: str = "value",
        strip_whitespace: bool = True
    ) -> str:
        """
        Validate non-empty string.
        
        Args:
            value: Value to validate
            field_name: Field name for error messages
            strip_whitespace: Whether to strip whitespace
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If value is invalid
        """
        if not isinstance(value, str):
            raise ValidationError(
                f"{field_name} must be a string",
                field=field_name,
                value=str(value)
            )
        
        if strip_whitespace:
            value = value.strip()
        
        if not value:
            raise ValidationError(
                f"{field_name} cannot be empty",
                field=field_name,
                value=value
            )
        
        return value
    
    @staticmethod
    def validate_string_length(
        value: str,
        field_name: str = "value",
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> str:
        """
        Validate string length.
        
        Args:
            value: String to validate
            field_name: Field name for error messages
            min_length: Minimum length (optional)
            max_length: Maximum length (optional)
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If length is invalid
        """
        length = len(value)
        
        if min_length is not None and length < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters",
                field=field_name,
                value=value,
                details={"actual_length": length}
            )
        
        if max_length is not None and length > max_length:
            raise ValidationError(
                f"{field_name} cannot exceed {max_length} characters",
                field=field_name,
                value=value,
                details={"actual_length": length}
            )
        
        return value
    
    @staticmethod
    def validate_enum_value(
        value: str,
        valid_values: List[str],
        field_name: str = "value",
        case_sensitive: bool = True
    ) -> str:
        """
        Validate that value is in a list of valid values.
        
        Args:
            value: Value to validate
            valid_values: List of valid values
            field_name: Field name for error messages
            case_sensitive: Whether comparison is case-sensitive
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If value is not in valid values
        """
        if not case_sensitive:
            value_lower = value.lower()
            valid_values_lower = [v.lower() for v in valid_values]
            if value_lower not in valid_values_lower:
                raise ValidationError(
                    f"{field_name} must be one of: {', '.join(valid_values)}",
                    field=field_name,
                    value=value
                )
        else:
            if value not in valid_values:
                raise ValidationError(
                    f"{field_name} must be one of: {', '.join(valid_values)}",
                    field=field_name,
                    value=value
                )
        
        return value