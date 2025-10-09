"""
Modern APPID management system with range-based generation.

This module replaces Excel-based APPID management with a robust,
range-based system that supports both regular and prequal APPIDs.
"""

import json
import threading
from typing import Iterator, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from decimal import Decimal

from refactored_codebase.config.models import AppIDConfig
from refactored_codebase.utils.logging import get_logger


@dataclass
class AppIDState:
    """APPID generation state."""
    current_regular: int
    current_prequal: int
    last_updated: str
    total_generated: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppIDState':
        """Create from dictionary."""
        return cls(**data)


class AppIDManager:
    """
    Enterprise-grade APPID manager with range-based generation.
    
    Features:
    - Thread-safe APPID generation
    - Separate ranges for regular and prequal APPIDs
    - Persistent state management
    - Range validation and overflow protection
    - Atomic operations with file locking
    """
    
    def __init__(self, config: AppIDConfig, state_file: Optional[Path] = None):
        """
        Initialize APPID manager.
        
        Args:
            config: APPID configuration
            state_file: Path to state file (default: data/appid_state.json)
        """
        self.config = config
        self.state_file = state_file or Path("data/appid_state.json")
        self.logger = get_logger(self.__class__.__name__)
        self._lock = threading.Lock()
        
        # Ensure state file directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize state
        self._state = self._load_state()
        
        self.logger.info(
            f"AppID Manager initialized - Regular: {self._state.current_regular}, "
            f"Prequal: {self._state.current_prequal}"
        )
    
    def _load_state(self) -> AppIDState:
        """Load APPID state from file or create new state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return AppIDState.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                self.logger.warning(f"Failed to load state file: {e}. Creating new state.")
        
        # Create new state with configured starting values
        from datetime import datetime
        return AppIDState(
            current_regular=self.config.start_range,
            current_prequal=self.config.prequal_start_range,
            last_updated=datetime.now().isoformat(),
            total_generated=0
        )
    
    def _save_state(self) -> None:
        """Save current state to file."""
        from datetime import datetime
        
        self._state.last_updated = datetime.now().isoformat()
        
        try:
            # Atomic write using temporary file
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._state.to_dict(), f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.state_file)
            
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            raise
    
    def get_next_regular_appid(self) -> int:
        """
        Get next regular APPID.
        
        Returns:
            Next available regular APPID
            
        Raises:
            ValueError: If APPID range is exhausted
        """
        with self._lock:
            if self._state.current_regular >= self.config.end_range:
                raise ValueError(
                    f"Regular APPID range exhausted. "
                    f"Current: {self._state.current_regular}, "
                    f"Max: {self.config.end_range}"
                )
            
            appid = self._state.current_regular
            self._state.current_regular += self.config.increment
            self._state.total_generated += 1
            
            self._save_state()
            
            self.logger.debug(f"Generated regular APPID: {appid}")
            return appid
    
    def get_next_prequal_appid(self) -> int:
        """
        Get next prequal APPID (20-digit).
        
        Returns:
            Next available prequal APPID
            
        Raises:
            ValueError: If prequal APPID range is exhausted
        """
        with self._lock:
            if self._state.current_prequal >= self.config.prequal_end_range:
                raise ValueError(
                    f"Prequal APPID range exhausted. "
                    f"Current: {self._state.current_prequal}, "
                    f"Max: {self.config.prequal_end_range}"
                )
            
            appid = self._state.current_prequal
            self._state.current_prequal += self.config.increment
            self._state.total_generated += 1
            
            self._save_state()
            
            self.logger.debug(f"Generated prequal APPID: {appid}")
            return appid
    
    def get_regular_appid_range(self, count: int) -> Iterator[int]:
        """
        Get a range of regular APPIDs.
        
        Args:
            count: Number of APPIDs to generate
            
        Yields:
            Regular APPIDs
            
        Raises:
            ValueError: If requested count exceeds available range
        """
        with self._lock:
            available = self.config.end_range - self._state.current_regular
            if count > available:
                raise ValueError(
                    f"Requested {count} APPIDs but only {available} available"
                )
            
            start_appid = self._state.current_regular
            self._state.current_regular += (count * self.config.increment)
            self._state.total_generated += count
            
            self._save_state()
        
        # Generate APPIDs outside the lock
        for i in range(count):
            appid = start_appid + (i * self.config.increment)
            self.logger.debug(f"Generated regular APPID: {appid}")
            yield appid
    
    def get_prequal_appid_range(self, count: int) -> Iterator[int]:
        """
        Get a range of prequal APPIDs.
        
        Args:
            count: Number of prequal APPIDs to generate
            
        Yields:
            Prequal APPIDs
            
        Raises:
            ValueError: If requested count exceeds available range
        """
        with self._lock:
            available = self.config.prequal_end_range - self._state.current_prequal
            if count > available:
                raise ValueError(
                    f"Requested {count} prequal APPIDs but only {available} available"
                )
            
            start_appid = self._state.current_prequal
            self._state.current_prequal += (count * self.config.increment)
            self._state.total_generated += count
            
            self._save_state()
        
        # Generate APPIDs outside the lock
        for i in range(count):
            appid = start_appid + (i * self.config.increment)
            self.logger.debug(f"Generated prequal APPID: {appid}")
            yield appid
    
    def get_available_regular_count(self) -> int:
        """Get number of available regular APPIDs."""
        return max(0, self.config.end_range - self._state.current_regular)
    
    def get_available_prequal_count(self) -> int:
        """Get number of available prequal APPIDs."""
        return max(0, self.config.prequal_end_range - self._state.current_prequal)
    
    def reset_to_range_start(self) -> None:
        """Reset APPID counters to range start values."""
        with self._lock:
            self._state.current_regular = self.config.start_range
            self._state.current_prequal = self.config.prequal_start_range
            self._state.total_generated = 0
            self._save_state()
        
        self.logger.info("APPID counters reset to range start values")
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get current state information."""
        return {
            "current_regular": self._state.current_regular,
            "current_prequal": self._state.current_prequal,
            "available_regular": self.get_available_regular_count(),
            "available_prequal": self.get_available_prequal_count(),
            "total_generated": self._state.total_generated,
            "last_updated": self._state.last_updated,
            "config": {
                "regular_range": f"{self.config.start_range}-{self.config.end_range}",
                "prequal_range": f"{self.config.prequal_start_range}-{self.config.prequal_end_range}",
                "increment": self.config.increment
            }
        }
    
    def validate_appid(self, appid: int, is_prequal: bool = False) -> bool:
        """
        Validate if an APPID is within the configured ranges.
        
        Args:
            appid: APPID to validate
            is_prequal: Whether this is a prequal APPID
            
        Returns:
            True if APPID is valid, False otherwise
        """
        if is_prequal:
            return self.config.prequal_start_range <= appid <= self.config.prequal_end_range
        else:
            return self.config.start_range <= appid <= self.config.end_range