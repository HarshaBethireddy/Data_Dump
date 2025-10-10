"""
Ultra-efficient ID generation utilities with enterprise features.

Replaces magic numbers with UUID-based, timestamp-based, and range-based
ID generation for maximum uniqueness and traceability.
"""

import uuid
from datetime import datetime, timezone
from typing import Generator, Optional, Union

from api_test_framework.core.exceptions import IDGenerationError
from api_test_framework.core.logging import get_logger


class IDGenerator:
    """Ultra-efficient ID generation with enterprise features."""
    
    def __init__(self):
        self.logger = get_logger("id_generator")
    
    def generate_run_id(self, prefix: str = "run") -> str:
        """Generate unique run ID with timestamp and UUID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_part = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{unique_part}"
    
    def generate_correlation_id(self, prefix: str = "corr") -> str:
        """Generate correlation ID for request tracing."""
        return f"{prefix}_{uuid.uuid4().hex[:16]}"
    
    def generate_request_id(self, test_type: str, sequence: int) -> str:
        """Generate request ID with test type and sequence."""
        timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
        return f"{test_type}_{timestamp}_{sequence:04d}"
    
    def generate_app_id_range(
        self,
        id_type: str,
        start_value: Union[int, str],
        count: int,
        increment: int = 1
    ) -> Generator[Union[int, str], None, None]:
        """Generate range of application IDs with intelligent formatting."""
        
        if id_type == "regular":
            if not isinstance(start_value, int):
                try:
                    start_value = int(start_value)
                except ValueError:
                    raise IDGenerationError(
                        "Regular app ID start value must be integer",
                        id_type=id_type,
                        range_start=start_value
                    )
            
            for i in range(count):
                yield start_value + (i * increment)
        
        elif id_type == "prequal":
            # Handle 20-digit prequal IDs
            if isinstance(start_value, str):
                if not start_value.isdigit() or len(start_value) != 20:
                    raise IDGenerationError(
                        "Prequal app ID must be 20 digits",
                        id_type=id_type,
                        range_start=start_value
                    )
                start_int = int(start_value)
            else:
                start_int = int(start_value)
            
            for i in range(count):
                current_id = start_int + (i * increment)
                # Ensure 20-digit format with leading zeros
                yield f"{current_id:020d}"
        
        else:
            raise IDGenerationError(
                f"Unknown ID type: {id_type}",
                id_type=id_type
            )
    
    def generate_batch_id(self, batch_size: int, timestamp: Optional[datetime] = None) -> str:
        """Generate batch ID with size and timestamp."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        time_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"batch_{batch_size}_{time_str}_{uuid.uuid4().hex[:8]}"
    
    def generate_test_execution_id(self, test_name: str) -> str:
        """Generate test execution ID with test name."""
        # Sanitize test name for ID
        safe_name = "".join(c if c.isalnum() else "_" for c in test_name.lower())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"exec_{safe_name}_{timestamp}_{uuid.uuid4().hex[:8]}"
    
    def generate_comparison_id(self, source_id: str, target_id: str) -> str:
        """Generate comparison ID from source and target IDs."""
        # Create deterministic but unique ID
        combined = f"{source_id}_{target_id}"
        hash_part = str(hash(combined))[-8:]  # Last 8 digits of hash
        timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
        return f"comp_{timestamp}_{hash_part}"
    
    def generate_report_id(self, report_type: str = "general") -> str:
        """Generate report ID with type and timestamp."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"report_{report_type}_{timestamp}_{uuid.uuid4().hex[:6]}"
    
    def validate_app_id(self, app_id: Union[int, str], id_type: str) -> bool:
        """Validate application ID format based on type."""
        try:
            if id_type == "regular":
                if isinstance(app_id, str):
                    app_id = int(app_id)
                return isinstance(app_id, int) and app_id > 0
            
            elif id_type == "prequal":
                if isinstance(app_id, int):
                    app_id = f"{app_id:020d}"
                return (
                    isinstance(app_id, str) and
                    app_id.isdigit() and
                    len(app_id) == 20
                )
            
            return False
            
        except (ValueError, TypeError):
            return False
    
    def format_app_id(self, app_id: Union[int, str], id_type: str) -> str:
        """Format application ID according to type requirements."""
        if not self.validate_app_id(app_id, id_type):
            raise IDGenerationError(
                f"Invalid app ID for type {id_type}: {app_id}",
                id_type=id_type
            )
        
        if id_type == "regular":
            return str(app_id)
        elif id_type == "prequal":
            if isinstance(app_id, int):
                return f"{app_id:020d}"
            return str(app_id)
        
        raise IDGenerationError(f"Unknown ID type: {id_type}", id_type=id_type)
    
    def extract_timestamp_from_id(self, id_string: str) -> Optional[datetime]:
        """Extract timestamp from generated ID if present."""
        try:
            # Look for timestamp pattern YYYYMMDD_HHMMSS
            parts = id_string.split("_")
            for i, part in enumerate(parts):
                if len(part) == 8 and part.isdigit():  # YYYYMMDD
                    if i + 1 < len(parts) and len(parts[i + 1]) == 6 and parts[i + 1].isdigit():  # HHMMSS
                        date_str = part
                        time_str = parts[i + 1]
                        
                        # Parse datetime
                        dt_str = f"{date_str}_{time_str}"
                        return datetime.strptime(dt_str, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
            
            return None
            
        except (ValueError, IndexError):
            return None
    
    def generate_sequential_ids(
        self,
        prefix: str,
        start: int = 1,
        count: int = 1,
        width: int = 4
    ) -> Generator[str, None, None]:
        """Generate sequential IDs with zero-padding."""
        for i in range(count):
            sequence_num = start + i
            yield f"{prefix}_{sequence_num:0{width}d}"
    
    def generate_hierarchical_id(self, *components: str) -> str:
        """Generate hierarchical ID from components."""
        # Sanitize components
        safe_components = []
        for comp in components:
            safe_comp = "".join(c if c.isalnum() else "_" for c in str(comp).lower())
            safe_components.append(safe_comp)
        
        # Add timestamp and unique suffix
        timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
        unique_suffix = uuid.uuid4().hex[:4]
        
        return "_".join(safe_components + [timestamp, unique_suffix])
    
    def is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID."""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    def generate_short_uuid(self, length: int = 8) -> str:
        """Generate short UUID for compact IDs."""
        if length > 32:
            length = 32
        return uuid.uuid4().hex[:length]
    
    def generate_timestamp_id(self, precision: str = "second") -> str:
        """Generate timestamp-based ID with configurable precision."""
        now = datetime.now(timezone.utc)
        
        if precision == "second":
            timestamp = now.strftime("%Y%m%d%H%M%S")
        elif precision == "millisecond":
            timestamp = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond // 1000:03d}"
        elif precision == "microsecond":
            timestamp = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond:06d}"
        else:
            timestamp = now.strftime("%Y%m%d%H%M%S")
        
        # Add random suffix to ensure uniqueness
        suffix = uuid.uuid4().hex[:4]
        return f"{timestamp}_{suffix}"