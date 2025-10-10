"""
Ultra-efficient test data service with range-based ID generation.

Replaces Excel-based ID management with JSON configuration and
intelligent range-based generation for both regular and prequal IDs.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

import aiofiles

from api_test_framework.core.config import get_settings
from api_test_framework.core.exceptions import TestDataError
from api_test_framework.core.logging import get_logger
from api_test_framework.models.request_models import APIRequest, FullSetRequest, PrequalRequest


class TestDataService:
    """Ultra-efficient test data management with range-based ID generation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("test_data")
        self._id_ranges: Dict[str, Any] = {}
        self._templates: Dict[str, Dict] = {}
    
    async def load_id_ranges(self) -> Dict[str, Any]:
        """Load ID ranges from JSON configuration."""
        if self._id_ranges:
            return self._id_ranges
        
        try:
            async with aiofiles.open(self.settings.paths.app_ids_file, 'r') as f:
                content = await f.read()
                self._id_ranges = json.loads(content)
                return self._id_ranges
        except Exception as e:
            raise TestDataError(
                "Failed to load ID ranges configuration",
                file_path=str(self.settings.paths.app_ids_file),
                cause=e
            )
    
    async def load_templates(self, template_dir: Path) -> Dict[str, Dict]:
        """Load JSON templates from directory."""
        templates = {}
        
        try:
            for json_file in template_dir.glob("*.json"):
                async with aiofiles.open(json_file, 'r') as f:
                    content = await f.read()
                    templates[json_file.stem] = json.loads(content)
            
            self.logger.info(f"Loaded {len(templates)} templates from {template_dir}")
            return templates
        except Exception as e:
            raise TestDataError(
                f"Failed to load templates from {template_dir}",
                file_path=str(template_dir),
                cause=e
            )
    
    def generate_id_range(
        self,
        id_type: str,
        count: int,
        start_value: Optional[Union[int, str]] = None
    ) -> Generator[Union[int, str], None, None]:
        """Generate ID range with intelligent increment logic."""
        
        if id_type == "regular":
            start = start_value or self.settings.app_ids.regular_start
            increment = self.settings.app_ids.regular_increment
            
            for i in range(count):
                yield start + (i * increment)
        
        elif id_type == "prequal":
            start = start_value or self.settings.app_ids.prequal_start
            increment = self.settings.app_ids.prequal_increment
            
            # Handle 20-digit prequal IDs as integers for arithmetic
            start_int = int(start)
            
            for i in range(count):
                current_id = start_int + (i * increment)
                # Format as 20-digit string with leading zeros
                yield f"{current_id:020d}"
        
        else:
            raise TestDataError(f"Unknown ID type: {id_type}")
    
    async def generate_test_requests(
        self,
        test_type: str,
        count: int,
        start_id: Optional[Union[int, str]] = None
    ) -> List[APIRequest]:
        """Generate test requests with auto-incremented IDs."""
        
        # Load templates based on test type
        if test_type == "fullset":
            template_dir = self.settings.paths.fullset_requests_dir
            id_type = "regular"
        elif test_type == "prequal":
            template_dir = self.settings.paths.prequal_requests_dir
            id_type = "prequal"
        else:
            raise TestDataError(f"Unknown test type: {test_type}")
        
        # Load templates and ID ranges
        templates = await self.load_templates(template_dir)
        if not templates:
            raise TestDataError(f"No templates found in {template_dir}")
        
        # Generate IDs
        id_generator = self.generate_id_range(id_type, count, start_id)
        
        requests = []
        template_names = list(templates.keys())
        
        for i, app_id in enumerate(id_generator):
            # Cycle through templates if we have more requests than templates
            template_name = template_names[i % len(template_names)]
            template_data = templates[template_name].copy()
            
            # Replace $APPID placeholder with generated ID
            template_json = json.dumps(template_data)
            template_json = template_json.replace("$APPID", str(app_id))
            updated_data = json.loads(template_json)
            
            # Create appropriate request model
            if test_type == "fullset":
                request = FullSetRequest(
                    request_id=f"{test_type}_{i+1}_{app_id}",
                    application=updated_data
                )
            else:  # prequal
                request = PrequalRequest(
                    request_id=f"{test_type}_{i+1}_{app_id}",
                    prequal=updated_data
                )
            
            # Add metadata
            request.add_metadata("template_name", template_name)
            request.add_metadata("generated_at", datetime.now().isoformat())
            request.add_tag(test_type)
            request.add_tag(f"app_id_{app_id}")
            
            requests.append(request)
        
        self.logger.info(f"Generated {len(requests)} {test_type} requests")
        return requests
    
    async def save_generated_data(
        self,
        requests: List[APIRequest],
        output_dir: Optional[Path] = None
    ) -> Path:
        """Save generated requests to JSON files."""
        output_dir = output_dir or self.settings.paths.output_dir / "generated_requests"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, request in enumerate(requests):
            filename = f"{request.request_type}_{timestamp}_{i+1:04d}.json"
            file_path = output_dir / filename
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(request.to_json())
        
        self.logger.info(f"Saved {len(requests)} requests to {output_dir}")
        return output_dir
    
    async def update_id_ranges(
        self,
        id_type: str,
        last_used: Union[int, str],
        range_name: str = "default_range"
    ) -> None:
        """Update ID ranges configuration with last used value."""
        ranges = await self.load_id_ranges()
        
        if id_type == "regular":
            ranges["regular_app_ids"]["current_range"]["last_generated"] = last_used
        elif id_type == "prequal":
            ranges["prequal_app_ids"]["current_range"]["last_generated"] = str(last_used)
        
        # Save updated ranges
        async with aiofiles.open(self.settings.paths.app_ids_file, 'w') as f:
            await f.write(json.dumps(ranges, indent=2))
        
        self.logger.info(f"Updated {id_type} ID range with last used: {last_used}")
    
    def get_next_available_id(self, id_type: str) -> Union[int, str]:
        """Get next available ID from configuration."""
        if not self._id_ranges:
            raise TestDataError("ID ranges not loaded. Call load_id_ranges() first.")
        
        if id_type == "regular":
            config = self._id_ranges["regular_app_ids"]["current_range"]
            last_generated = config.get("last_generated")
            
            if last_generated:
                return last_generated + config["increment"]
            else:
                return config["start"]
        
        elif id_type == "prequal":
            config = self._id_ranges["prequal_app_ids"]["current_range"]
            last_generated = config.get("last_generated")
            
            if last_generated:
                next_id = int(last_generated) + config["increment"]
                return f"{next_id:020d}"
            else:
                return config["start"]
        
        else:
            raise TestDataError(f"Unknown ID type: {id_type}")
    
    async def validate_template(self, template_data: Dict[str, Any], test_type: str) -> bool:
        """Validate template structure for test type."""
        try:
            if test_type == "fullset":
                FullSetRequest(application=template_data)
            elif test_type == "prequal":
                PrequalRequest(prequal=template_data)
            else:
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Template validation failed: {e}")
            return False