"""
Ultra-efficient data validation utilities with comprehensive checks.

Provides high-performance validation functions for all data types
used in the API testing framework with detailed error reporting.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from api_test_framework.core.exceptions import ValidationError
from api_test_framework.core.logging import get_logger


class DataValidator:
    """Ultra-efficient data validation with comprehensive checks."""
    
    def __init__(self):
        self.logger = get_logger("validator")
        
        # Compiled regex patterns for performance
        self.patterns = {
            "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            "phone": re.compile(r"^\+?1?[0-9]{10,15}$"),
            "date_ddmmyyyy": re.compile(r"^(0[1-9]|[12][0-9]|3[01])(0[1-9]|1[0-2])\d{4}$"),
            "time_hhmmss": re.compile(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$"),
            "uuid": re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE),
            "app_id_regular": re.compile(r"^\d{6,10}$"),
            "app_id_prequal": re.compile(r"^\d{20}$"),
            "postal_code": re.compile(r"^[0-9]{5}([0-9]{4})?$"),
            "ssn": re.compile(r"^\d{3}-?\d{2}-?\d{4}$"),
        }
    
    def validate_email(self, email: str, field_name: str = "email") -> str:
        """Validate email format with comprehensive checks."""
        if not email or not isinstance(email, str):
            raise ValidationError(f"{field_name} is required and must be a string")
        
        email = email.strip().lower()
        
        if not self.patterns["email"].match(email):
            raise ValidationError(f"Invalid {field_name} format: {email}")
        
        # Additional checks
        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError(f"{field_name} is too long (max 254 characters)")
        
        local_part, domain = email.split("@")
        if len(local_part) > 64:  # RFC 5321 limit
            raise ValidationError(f"{field_name} local part is too long (max 64 characters)")
        
        return email
    
    def validate_phone(self, phone: str, field_name: str = "phone") -> str:
        """Validate and normalize phone number."""
        if not phone or not isinstance(phone, str):
            raise ValidationError(f"{field_name} is required and must be a string")
        
        # Remove all non-digit characters
        digits_only = re.sub(r"[^\d]", "", phone)
        
        if len(digits_only) < 10:
            raise ValidationError(f"{field_name} must have at least 10 digits")
        
        if len(digits_only) > 15:
            raise ValidationError(f"{field_name} must have at most 15 digits")
        
        # Format as standard US number if 10 digits
        if len(digits_only) == 10:
            return f"1{digits_only}"
        
        return digits_only
    
    def validate_date(self, date_str: str, format_type: str = "ddmmyyyy", field_name: str = "date") -> str:
        """Validate date format and logical validity."""
        if not date_str or not isinstance(date_str, str):
            raise ValidationError(f"{field_name} is required and must be a string")
        
        date_str = date_str.strip()
        
        if format_type == "ddmmyyyy":
            if not self.patterns["date_ddmmyyyy"].match(date_str):
                raise ValidationError(f"Invalid {field_name} format. Expected DDMMYYYY: {date_str}")
            
            # Validate logical date
            try:
                day = int(date_str[:2])
                month = int(date_str[2:4])
                year = int(date_str[4:8])
                
                # Basic range checks
                if not (1 <= month <= 12):
                    raise ValidationError(f"Invalid month in {field_name}: {month}")
                
                if not (1 <= day <= 31):
                    raise ValidationError(f"Invalid day in {field_name}: {day}")
                
                if year < 1900 or year > 2100:
                    raise ValidationError(f"Invalid year in {field_name}: {year}")
                
                # Check if date is valid (handles leap years, etc.)
                datetime(year, month, day)
                
            except ValueError as e:
                raise ValidationError(f"Invalid {field_name}: {date_str} - {str(e)}")
        
        return date_str
    
    def validate_time(self, time_str: str, field_name: str = "time") -> str:
        """Validate time format (H:MM:SS or HH:MM:SS)."""
        if not time_str or not isinstance(time_str, str):
            raise ValidationError(f"{field_name} is required and must be a string")
        
        time_str = time_str.strip()
        
        if not self.patterns["time_hhmmss"].match(time_str):
            raise ValidationError(f"Invalid {field_name} format. Expected H:MM:SS or HH:MM:SS: {time_str}")
        
        # Additional validation
        try:
            parts = time_str.split(":")
            hours, minutes, seconds = map(int, parts)
            
            if not (0 <= hours <= 23):
                raise ValidationError(f"Invalid hours in {field_name}: {hours}")
            if not (0 <= minutes <= 59):
                raise ValidationError(f"Invalid minutes in {field_name}: {minutes}")
            if not (0 <= seconds <= 59):
                raise ValidationError(f"Invalid seconds in {field_name}: {seconds}")
                
        except ValueError as e:
            raise ValidationError(f"Invalid {field_name}: {time_str} - {str(e)}")
        
        return time_str
    
    def validate_app_id(self, app_id: Union[int, str], id_type: str, field_name: str = "app_id") -> Union[int, str]:
        """Validate application ID based on type."""
        if app_id is None:
            raise ValidationError(f"{field_name} is required")
        
        if id_type == "regular":
            if isinstance(app_id, str):
                if not app_id.isdigit():
                    raise ValidationError(f"Regular {field_name} must be numeric: {app_id}")
                app_id = int(app_id)
            
            if not isinstance(app_id, int) or app_id <= 0:
                raise ValidationError(f"Regular {field_name} must be a positive integer: {app_id}")
            
            if app_id > 999999999:  # 9 digits max for regular
                raise ValidationError(f"Regular {field_name} too large (max 9 digits): {app_id}")
            
            return app_id
        
        elif id_type == "prequal":
            if isinstance(app_id, int):
                app_id = f"{app_id:020d}"
            
            if not isinstance(app_id, str):
                raise ValidationError(f"Prequal {field_name} must be string or integer: {app_id}")
            
            if not self.patterns["app_id_prequal"].match(app_id):
                raise ValidationError(f"Prequal {field_name} must be exactly 20 digits: {app_id}")
            
            return app_id
        
        else:
            raise ValidationError(f"Unknown app ID type: {id_type}")
    
    def validate_postal_code(self, postal_code: str, field_name: str = "postal_code") -> str:
        """Validate US postal code format."""
        if not postal_code or not isinstance(postal_code, str):
            raise ValidationError(f"{field_name} is required and must be a string")
        
        # Remove spaces and hyphens
        clean_code = re.sub(r"[\s-]", "", postal_code)
        
        if not self.patterns["postal_code"].match(clean_code):
            raise ValidationError(f"Invalid {field_name} format. Expected XXXXX or XXXXXXXXX: {postal_code}")
        
        return clean_code
    
    def validate_ssn(self, ssn: str, field_name: str = "ssn") -> str:
        """Validate Social Security Number format."""
        if not ssn or not isinstance(ssn, str):
            raise ValidationError(f"{field_name} is required and must be a string")
        
        # Remove hyphens
        clean_ssn = ssn.replace("-", "")
        
        if not re.match(r"^\d{9}$", clean_ssn):
            raise ValidationError(f"Invalid {field_name} format. Expected XXX-XX-XXXX or XXXXXXXXX: {ssn}")
        
        # Check for invalid SSNs
        if clean_ssn in ["000000000", "123456789", "111111111", "222222222"]:
            raise ValidationError(f"Invalid {field_name}: {ssn}")
        
        if clean_ssn.startswith("000") or clean_ssn[3:5] == "00" or clean_ssn[5:] == "0000":
            raise ValidationError(f"Invalid {field_name} format: {ssn}")
        
        return clean_ssn
    
    def validate_currency_amount(self, amount: Union[str, int, float], field_name: str = "amount") -> float:
        """Validate currency amount."""
        if amount is None:
            raise ValidationError(f"{field_name} is required")
        
        try:
            if isinstance(amount, str):
                # Remove currency symbols and commas
                clean_amount = re.sub(r"[$,]", "", amount.strip())
                amount = float(clean_amount)
            else:
                amount = float(amount)
            
            if amount < 0:
                raise ValidationError(f"{field_name} cannot be negative: {amount}")
            
            if amount > 999999999.99:  # Reasonable upper limit
                raise ValidationError(f"{field_name} too large: {amount}")
            
            # Round to 2 decimal places
            return round(amount, 2)
            
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid {field_name} format: {amount} - {str(e)}")
    
    def validate_percentage(self, percentage: Union[str, int, float], field_name: str = "percentage") -> float:
        """Validate percentage value (0-100)."""
        if percentage is None:
            raise ValidationError(f"{field_name} is required")
        
        try:
            if isinstance(percentage, str):
                # Remove % symbol
                clean_pct = percentage.strip().rstrip("%")
                percentage = float(clean_pct)
            else:
                percentage = float(percentage)
            
            if not (0 <= percentage <= 100):
                raise ValidationError(f"{field_name} must be between 0 and 100: {percentage}")
            
            return round(percentage, 2)
            
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid {field_name} format: {percentage} - {str(e)}")
    
    def validate_uuid(self, uuid_str: str, field_name: str = "uuid") -> str:
        """Validate UUID format."""
        if not uuid_str or not isinstance(uuid_str, str):
            raise ValidationError(f"{field_name} is required and must be a string")
        
        uuid_str = uuid_str.strip()
        
        if not self.patterns["uuid"].match(uuid_str):
            raise ValidationError(f"Invalid {field_name} format: {uuid_str}")
        
        return uuid_str.lower()
    
    def validate_json_structure(self, data: Dict[str, Any], required_fields: List[str], field_name: str = "data") -> Dict[str, Any]:
        """Validate JSON structure has required fields."""
        if not isinstance(data, dict):
            raise ValidationError(f"{field_name} must be a dictionary")
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(f"Missing required fields in {field_name}: {missing_fields}")
        
        return data
    
    def validate_string_length(self, text: str, min_length: int = 0, max_length: int = None, field_name: str = "field") -> str:
        """Validate string length constraints."""
        if not isinstance(text, str):
            raise ValidationError(f"{field_name} must be a string")
        
        text = text.strip()
        
        if len(text) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters")
        
        if max_length and len(text) > max_length:
            raise ValidationError(f"{field_name} must be at most {max_length} characters")
        
        return text
    
    def validate_numeric_range(self, value: Union[int, float], min_value: Optional[Union[int, float]] = None, max_value: Optional[Union[int, float]] = None, field_name: str = "value") -> Union[int, float]:
        """Validate numeric value is within range."""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be a number")
        
        if min_value is not None and value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")
        
        if max_value is not None and value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}")
        
        return value
    
    def validate_choice(self, value: Any, choices: List[Any], field_name: str = "field") -> Any:
        """Validate value is one of allowed choices."""
        if value not in choices:
            raise ValidationError(f"{field_name} must be one of: {choices}. Got: {value}")
        
        return value
    
    def validate_batch(self, data: Dict[str, Any], validation_rules: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Validate multiple fields using batch validation rules."""
        validated_data = {}
        errors = []
        
        for field_name, rules in validation_rules.items():
            try:
                value = data.get(field_name)
                
                # Check if required
                if rules.get("required", False) and value is None:
                    errors.append(f"{field_name} is required")
                    continue
                
                # Skip validation if value is None and not required
                if value is None:
                    validated_data[field_name] = value
                    continue
                
                # Apply validation based on type
                validation_type = rules.get("type")
                
                if validation_type == "email":
                    validated_data[field_name] = self.validate_email(value, field_name)
                elif validation_type == "phone":
                    validated_data[field_name] = self.validate_phone(value, field_name)
                elif validation_type == "date":
                    validated_data[field_name] = self.validate_date(value, rules.get("format", "ddmmyyyy"), field_name)
                elif validation_type == "app_id":
                    validated_data[field_name] = self.validate_app_id(value, rules.get("id_type", "regular"), field_name)
                elif validation_type == "currency":
                    validated_data[field_name] = self.validate_currency_amount(value, field_name)
                elif validation_type == "percentage":
                    validated_data[field_name] = self.validate_percentage(value, field_name)
                elif validation_type == "choice":
                    validated_data[field_name] = self.validate_choice(value, rules.get("choices", []), field_name)
                else:
                    validated_data[field_name] = value
                    
            except ValidationError as e:
                errors.append(str(e))
        
        if errors:
            raise ValidationError(f"Validation failed: {'; '.join(errors)}")
        
        return validated_data