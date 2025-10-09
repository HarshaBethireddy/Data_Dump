"""
Run ID management service for tracking test executions.

Provides centralized management of test run identifiers and
organized folder structure creation.
"""

from pathlib import Path
from typing import Tuple
from datetime import datetime

from ..core.config import PathConfiguration


class RunManager:
    """
    Manages run IDs and creates organized folder structures for test executions.
    
    Provides sequential run ID generation and ensures proper folder organization
    for test outputs and reports.
    """
    
    def __init__(self, path_config: PathConfiguration):
        """
        Initialize run manager with path configuration.
        
        Args:
            path_config: Path configuration instance
        """
        self.path_config = path_config
        self.run_id_file = path_config.report_dir / "run_id.txt"
    
    def get_next_run_id(self) -> str:
        """
        Get the next sequential run ID.
        
        Returns:
            Next run ID as string
            
        Raises:
            RuntimeError: If run ID generation fails
        """
        try:
            # Ensure report directory exists
            self.path_config.report_dir.mkdir(parents=True, exist_ok=True)
            
            if self.run_id_file.exists():
                with open(self.run_id_file, "r", encoding='utf-8') as file:
                    current_id = int(file.read().strip())
                    next_id = current_id + 1
            else:
                next_id = 100000
            
            # Write the new run ID
            with open(self.run_id_file, "w", encoding='utf-8') as file:
                file.write(str(next_id))
            
            return f"{next_id:06d}"
            
        except (ValueError, IOError) as e:
            raise RuntimeError(f"Failed to generate run ID: {e}") from e
    
    def create_run_folders(self, run_id: str) -> Tuple[Path, Path]:
        """
        Create organized folders for a test run.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Tuple of (response_folder, report_folder) paths
        """
        response_folder = self.path_config.test_response_dir / run_id
        report_folder = self.path_config.report_dir / run_id
        
        # Create folders
        response_folder.mkdir(parents=True, exist_ok=True)
        report_folder.mkdir(parents=True, exist_ok=True)
        
        return response_folder, report_folder
    
    def get_timestamp(self) -> str:
        """
        Get current timestamp for file naming.
        
        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime("%d%m%y%H%M")
    
    def cleanup_old_runs(self, keep_count: int = 10) -> None:
        """
        Cleanup old test runs, keeping only the most recent ones.
        
        Args:
            keep_count: Number of recent runs to keep
        """
        try:
            # Get all run folders
            response_folders = []
            report_folders = []
            
            if self.path_config.test_response_dir.exists():
                response_folders = [
                    f for f in self.path_config.test_response_dir.iterdir() 
                    if f.is_dir() and f.name.isdigit()
                ]
            
            if self.path_config.report_dir.exists():
                report_folders = [
                    f for f in self.path_config.report_dir.iterdir() 
                    if f.is_dir() and f.name.isdigit()
                ]
            
            # Sort by run ID (folder name) and keep only recent ones
            response_folders.sort(key=lambda x: int(x.name))
            report_folders.sort(key=lambda x: int(x.name))
            
            # Remove old folders
            for folder in response_folders[:-keep_count]:
                self._remove_folder_tree(folder)
            
            for folder in report_folders[:-keep_count]:
                self._remove_folder_tree(folder)
                
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Failed to cleanup old runs: {e}")
    
    def _remove_folder_tree(self, folder: Path) -> None:
        """Recursively remove a folder tree."""
        import shutil
        try:
            shutil.rmtree(folder)
        except Exception:
            # Ignore errors during cleanup
            pass