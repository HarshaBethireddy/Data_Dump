"""
Run ID management for tracking test executions.
"""
import os
from typing import Tuple
from datetime import datetime


class RunManager:
    """Manages run IDs and creates organized folder structures."""
    
    def __init__(self, report_folder: str = "Report"):
        self.report_folder = report_folder
        self.run_id_file = os.path.join(report_folder, "run_id.txt")
    
    def get_next_run_id(self) -> int:
        """Get the next sequential run ID."""
        try:
            if os.path.exists(self.run_id_file):
                with open(self.run_id_file, "r") as file:
                    current_id = int(file.read().strip())
                    next_id = current_id + 1
            else:
                next_id = 100000
            
            # Ensure report folder exists
            os.makedirs(self.report_folder, exist_ok=True)
            
            # Write the new run ID
            with open(self.run_id_file, "w") as file:
                file.write(str(next_id))
            
            return next_id
        except (ValueError, IOError) as e:
            raise RuntimeError(f"Failed to generate run ID: {e}")
    
    def create_run_folders(self, run_id: int, base_response_folder: str = "TestResponse") -> Tuple[str, str]:
        """Create organized folders for a test run."""
        run_id_str = f"{run_id:06d}"
        
        response_folder = os.path.join(base_response_folder, run_id_str)
        report_folder = os.path.join(self.report_folder, run_id_str)
        
        # Create folders
        os.makedirs(response_folder, exist_ok=True)
        os.makedirs(report_folder, exist_ok=True)
        
        return response_folder, report_folder
    
    def get_timestamp(self) -> str:
        """Get current timestamp for file naming."""
        return datetime.now().strftime("%d%m%y%H%M")