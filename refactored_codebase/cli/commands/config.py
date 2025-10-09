"""
Configuration command implementation.
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from refactored_codebase.config.settings import Settings, create_default_configs

console = Console()


def execute_config_init(force: bool = False) -> None:
    """Initialize configuration files."""
    console.print("🔧 Initializing Configuration Files", style="bold blue")
    
    config_dir = Path("config")
    
    if config_dir.exists() and not force:
        console.print("⚠️ Configuration directory already exists. Use --force to overwrite.", style="yellow")
        return
    
    try:
        create_default_configs()
        console.print("✅ Configuration files created successfully!", style="green")
        console.print(f"📁 Configuration directory: {config_dir.absolute()}")
        
        # List created files
        if config_dir.exists():
            console.print("\n📄 Created files:")
            for config_file in config_dir.glob("*.json"):
                console.print(f"  - {config_file.name}")
                
    except Exception as e:
        console.print(f"❌ Failed to create configuration: {e}", style="red")
        raise


def execute_config_show(settings: Settings, section: str = None) -> None:
    """Show current configuration."""
    console.print("📋 Current Configuration", style="bold blue")
    
    if section:
        # Show specific section
        if hasattr(settings, section):
            config_data = getattr(settings, section).dict()
            _display_config_section(section, config_data)
        else:
            console.print(f"❌ Unknown configuration section: {section}", style="red")
            return
    else:
        # Show all sections
        sections = {
            "api": settings.api.dict(),
            "test": settings.test.dict(),
            "paths": {k: str(v) for k, v in settings.paths.dict().items()},
            "appid": settings.appid.dict(),
            "logging": settings.logging.dict()
        }
        
        for section_name, section_data in sections.items():
            _display_config_section(section_name, section_data)


def execute_config_validate(settings: Settings) -> None:
    """Validate current configuration."""
    console.print("🔍 Validating Configuration", style="bold blue")
    
    errors = []
    warnings = []
    
    # Validate API configuration
    try:
        from refactored_codebase.core.http_client import HTTPClient
        with HTTPClient(settings.api) as client:
            pass
        console.print("✅ API configuration valid", style="green")
    except Exception as e:
        errors.append(f"API configuration invalid: {e}")
    
    # Validate paths
    try:
        settings.paths.ensure_directories()
        console.print("✅ Path configuration valid", style="green")
    except Exception as e:
        errors.append(f"Path configuration invalid: {e}")
    
    # Validate APPID ranges
    if settings.appid.start_range >= settings.appid.end_range:
        errors.append("Regular APPID start_range must be less than end_range")
    
    if settings.appid.prequal_start_range >= settings.appid.prequal_end_range:
        errors.append("Prequal APPID start_range must be less than end_range")
    
    # Check template directories
    template_dirs = [
        settings.paths.requests_dir / "fullset",
        settings.paths.requests_dir / "prequal"
    ]
    
    for template_dir in template_dirs:
        if not template_dir.exists():
            warnings.append(f"Template directory does not exist: {template_dir}")
        elif not list(template_dir.glob("*.json")):
            warnings.append(f"No JSON templates found in: {template_dir}")
    
    # Display results
    if errors:
        console.print("\n❌ Configuration Errors:", style="red")
        for error in errors:
            console.print(f"  - {error}", style="red")
    
    if warnings:
        console.print("\n⚠️ Configuration Warnings:", style="yellow")
        for warning in warnings:
            console.print(f"  - {warning}", style="yellow")
    
    if not errors and not warnings:
        console.print("\n✅ Configuration is valid!", style="bold green")
    elif not errors:
        console.print("\n✅ Configuration is valid with warnings", style="green")
    else:
        console.print("\n❌ Configuration has errors that need to be fixed", style="red")


def _display_config_section(section_name: str, config_data: dict) -> None:
    """Display a configuration section."""
    table = Table(title=f"{section_name.title()} Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in config_data.items():
        # Format value for display
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, indent=2)
        else:
            value_str = str(value)
        
        table.add_row(key, value_str)
    
    console.print(table)
    console.print()  # Add spacing