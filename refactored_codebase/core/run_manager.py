"""
Modern run management system with UUID-based tracking.

This module replaces the magic number run ID system with a more
robust UUID-based approach with meaningful timestamps.
"""

import json
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from refactored_codebase.utils.logging import get_logger


@dataclass
class RunMetadata:
    """Run execution metadata."""
    run_id: str
    run_uuid: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "running"
    data_type: Optional[str] = None
    template_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RunMetadata':
        """Create from dictionary."""
        return cls(**data)


class RunManager:
    """
    Modern run manager with UUID-based tracking.
    
    Features:
    - UUID-based run identification
    - Timestamp-based run IDs
    - Comprehensive metadata tracking
    - Organized directory structure
    - Run history and cleanup
    """
    
    def __init__(self, base_dir: Path):
        """
        Initialize run manager.
        
        Args:
            base_dir: Base directory for runs
        """
        self.base_dir = Path(base_dir)
        self.runs_dir = self.base_dir / "runs"
        self.metadata_file = self.base_dir / "run_history.json"
        self.logger = get_logger(self.__class__.__name__)
        
        # Ensure directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Run Manager initialized - base: {self.base_dir}")
    
    def create_run(self, data_type: Optional[str] = None) -> RunMetadata:
        """
        Create a new test run.
        
        Args:
            data_type: Type of data being tested
            
        Returns:
            Run metadata
        """
        # Generate run identifiers
        run_uuid = str(uuid.uuid4())
        timestamp = datetime.now()
        run_id = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Create run metadata
        metadata = RunMetadata(
            run_id=run_id,
            run_uuid=run_uuid,
            start_time=timestamp.isoformat(),
            data_type=data_type
        )
        
        # Create run directory
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save run metadata
        metadata_file = run_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        # Update run history
        self._update_run_history(metadata)
        
        self.logger.info(f"Created new run: {run_id} ({run_uuid})")
        return metadata
    
    def get_run_directory(self, run_id: str) -> Path:
        """Get run directory path."""
        return self.runs_dir / run_id
    
    def get_run_metadata(self, run_id: str) -> Optional[RunMetadata]:
        """
        Get run metadata.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Run metadata or None if not found
        """
        metadata_file = self.runs_dir / run_id / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return RunMetadata.from_dict(data)
        except Exception as e:
            self.logger.error(f"Failed to load run metadata for {run_id}: {e}")
            return None
    
    def update_run_status(self, run_id: str, status: str, **kwargs) -> None:
        """
        Update run status and metadata.
        
        Args:
            run_id: Run identifier
            status: New status
            **kwargs: Additional metadata to update
        """
        metadata = self.get_run_metadata(run_id)
        if not metadata:
            self.logger.warning(f"Run metadata not found for {run_id}")
            return
        
        # Update metadata
        metadata.status = status
        if status in ["completed", "failed"]:
            metadata.end_time = datetime.now().isoformat()
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
        
        # Save updated metadata
        metadata_file = self.runs_dir / run_id / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        # Update run history
        self._update_run_history(metadata)
        
        self.logger.info(f"Updated run {run_id} status to {status}")
    
    def _update_run_history(self, metadata: RunMetadata) -> None:
        """Update run history file."""
        history = self._load_run_history()
        history[metadata.run_id] = metadata.to_dict()
        
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to update run history: {e}")
    
    def _load_run_history(self) -> Dict[str, Any]:
        """Load run history from file."""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load run history: {e}")
            return {}
    
    def list_runs(self, limit: Optional[int] = None) -> list[RunMetadata]:
        """
        List recent runs.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of run metadata, sorted by start time (newest first)
        """
        history = self._load_run_history()
        runs = []
        
        for run_data in history.values():
            try:
                runs.append(RunMetadata.from_dict(run_data))
            except Exception as e:
                self.logger.warning(f"Invalid run data: {e}")
        
        # Sort by start time (newest first)
        runs.sort(key=lambda r: r.start_time, reverse=True)
        
        if limit:
            runs = runs[:limit]
        
        return runs
    
    def cleanup_old_runs(self, keep_days: int = 30) -> int:
        """
        Cleanup old run directories.
        
        Args:
            keep_days: Number of days to keep runs
            
        Returns:
            Number of runs cleaned up
        """
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        cleaned_count = 0
        
        for run_dir in self.runs_dir.iterdir():
            if not run_dir.is_dir():
                continue
            
            try:
                # Check run age
                metadata = self.get_run_metadata(run_dir.name)
                if metadata:
                    start_time = datetime.fromisoformat(metadata.start_time).timestamp()
                    if start_time < cutoff_date:
                        # Remove run directory
                        import shutil
                        shutil.rmtree(run_dir)
                        cleaned_count += 1
                        self.logger.info(f"Cleaned up old run: {run_dir.name}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup run {run_dir.name}: {e}")
        
        # Update run history to remove cleaned runs
        if cleaned_count > 0:
            history = self._load_run_history()
            remaining_runs = {
                run_id: data for run_id, data in history.items()
                if (self.runs_dir / run_id).exists()
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(remaining_runs, f, indent=2)
        
        self.logger.info(f"Cleaned up {cleaned_count} old runs")
        return cleaned_count
    
    def get_next_run_id(self) -> int:
        """
        Legacy method for backward compatibility.
        
        Returns:
            Sequential run number for compatibility
        """
        # Count existing runs and return next number
        runs = self.list_runs()
        return len(runs) + 100000  # Start from 100000 for compatibility
    
    def get_run_statistics(self) -> Dict[str, Any]:
        """Get run statistics."""
        runs = self.list_runs()
        
        total_runs = len(runs)
        completed_runs = sum(1 for r in runs if r.status == "completed")
        failed_runs = sum(1 for r in runs if r.status == "failed")
        running_runs = sum(1 for r in runs if r.status == "running")
        
        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "running_runs": running_runs,
            "success_rate": (completed_runs / total_runs * 100) if total_runs > 0 else 0,
            "latest_run": runs[0].run_id if runs else None
        }