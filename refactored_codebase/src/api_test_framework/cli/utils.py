"""
CLI utility functions for enhanced user experience.

Provides helper functions for CLI operations, formatting,
and interactive features with beautiful output.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

console = Console()


class CLIHelper:
    """Helper class for CLI operations and formatting."""
    
    @staticmethod
    def confirm_action(message: str, default: bool = False) -> bool:
        """Confirm user action with rich prompt."""
        return Confirm.ask(message, default=default)
    
    @staticmethod
    def get_user_input(
        prompt: str,
        default: Optional[str] = None,
        choices: Optional[List[str]] = None
    ) -> str:
        """Get user input with validation."""
        return Prompt.ask(prompt, default=default, choices=choices)
    
    @staticmethod
    def get_integer_input(
        prompt: str,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> int:
        """Get integer input with validation."""
        while True:
            try:
                value = IntPrompt.ask(prompt, default=default)
                
                if min_value is not None and value < min_value:
                    rprint(f"[red]Value must be at least {min_value}[/red]")
                    continue
                
                if max_value is not None and value > max_value:
                    rprint(f"[red]Value must be at most {max_value}[/red]")
                    continue
                
                return value
                
            except KeyboardInterrupt:
                rprint("\n[yellow]Operation cancelled[/yellow]")
                sys.exit(0)
    
    @staticmethod
    def display_error(message: str, details: Optional[str] = None) -> None:
        """Display error message with optional details."""
        panel_content = f"[red]❌ {message}[/red]"
        if details:
            panel_content += f"\n\n[yellow]Details:[/yellow]\n{details}"
        
        panel = Panel(
            panel_content,
            title="Error",
            border_style="red"
        )
        console.print(panel)
    
    @staticmethod
    def display_success(message: str, details: Optional[str] = None) -> None:
        """Display success message with optional details."""
        panel_content = f"[green]✅ {message}[/green]"
        if details:
            panel_content += f"\n\n[blue]Details:[/blue]\n{details}"
        
        panel = Panel(
            panel_content,
            title="Success",
            border_style="green"
        )
        console.print(panel)
    
    @staticmethod
    def display_warning(message: str, details: Optional[str] = None) -> None:
        """Display warning message with optional details."""
        panel_content = f"[yellow]⚠️  {message}[/yellow]"
        if details:
            panel_content += f"\n\n[blue]Details:[/blue]\n{details}"
        
        panel = Panel(
            panel_content,
            title="Warning",
            border_style="yellow"
        )
        console.print(panel)
    
    @staticmethod
    def display_info(message: str, details: Optional[str] = None) -> None:
        """Display info message with optional details."""
        panel_content = f"[blue]ℹ️  {message}[/blue]"
        if details:
            panel_content += f"\n\n{details}"
        
        panel = Panel(
            panel_content,
            title="Information",
            border_style="blue"
        )
        console.print(panel)
    
    @staticmethod
    def create_stats_table(
        title: str,
        stats: Dict[str, Any],
        highlight_key: Optional[str] = None
    ) -> Table:
        """Create a formatted statistics table."""
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="yellow", no_wrap=True)
        table.add_column("Value", style="green")
        
        for key, value in stats.items():
            # Format key for display
            display_key = key.replace("_", " ").title()
            
            # Format value based on type
            if isinstance(value, float):
                if "percentage" in key.lower() or "rate" in key.lower():
                    display_value = f"{value:.1f}%"
                elif "time" in key.lower() or "duration" in key.lower():
                    display_value = f"{value:.1f}ms"
                else:
                    display_value = f"{value:.2f}"
            else:
                display_value = str(value)
            
            # Highlight specific key if requested
            if highlight_key and key == highlight_key:
                if isinstance(value, (int, float)) and value >= 95:
                    display_value = f"[green]{display_value}[/green]"
                elif isinstance(value, (int, float)) and value >= 80:
                    display_value = f"[yellow]{display_value}[/yellow]"
                else:
                    display_value = f"[red]{display_value}[/red]"
            
            table.add_row(display_key, display_value)
        
        return table
    
    @staticmethod
    def display_file_list(
        files: List[Path],
        title: str = "Files",
        show_size: bool = True
    ) -> None:
        """Display a formatted list of files."""
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("File", style="cyan")
        
        if show_size:
            table.add_column("Size", style="yellow", justify="right")
        
        table.add_column("Modified", style="green")
        
        for file_path in files:
            if file_path.exists():
                stat = file_path.stat()
                
                # Format file size
                size_str = ""
                if show_size:
                    size_bytes = stat.st_size
                    for unit in ['B', 'KB', 'MB', 'GB']:
                        if size_bytes < 1024.0:
                            size_str = f"{size_bytes:.1f} {unit}"
                            break
                        size_bytes /= 1024.0
                
                # Format modification time
                from datetime import datetime
                mod_time = datetime.fromtimestamp(stat.st_mtime)
                mod_str = mod_time.strftime("%Y-%m-%d %H:%M")
                
                if show_size:
                    table.add_row(str(file_path), size_str, mod_str)
                else:
                    table.add_row(str(file_path), mod_str)
        
        console.print(table)
    
    @staticmethod
    def show_progress_spinner(message: str):
        """Show a progress spinner for long operations."""
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[blue]{message}[/blue]"),
            console=console,
            transient=True
        )
    
    @staticmethod
    def format_json_output(data: Dict[str, Any], title: str = "Data") -> None:
        """Format and display JSON data beautifully."""
        import json
        
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        
        panel = Panel(
            formatted_json,
            title=title,
            border_style="cyan",
            expand=False
        )
        console.print(panel)
    
    @staticmethod
    def create_comparison_table(
        before: Dict[str, Any],
        after: Dict[str, Any],
        title: str = "Comparison"
    ) -> Table:
        """Create a comparison table showing before/after values."""
        table = Table(title=title, show_header=True, header_style="bold purple")
        table.add_column("Metric", style="cyan")
        table.add_column("Before", style="yellow")
        table.add_column("After", style="green")
        table.add_column("Change", style="white")
        
        all_keys = set(before.keys()) | set(after.keys())
        
        for key in sorted(all_keys):
            before_val = before.get(key, "N/A")
            after_val = after.get(key, "N/A")
            
            # Calculate change if both values are numeric
            change_str = ""
            if (isinstance(before_val, (int, float)) and 
                isinstance(after_val, (int, float))):
                
                change = after_val - before_val
                change_pct = (change / before_val * 100) if before_val != 0 else 0
                
                if change > 0:
                    change_str = f"[green]+{change:.1f} (+{change_pct:.1f}%)[/green]"
                elif change < 0:
                    change_str = f"[red]{change:.1f} ({change_pct:.1f}%)[/red]"
                else:
                    change_str = "[blue]No change[/blue]"
            
            table.add_row(
                key.replace("_", " ").title(),
                str(before_val),
                str(after_val),
                change_str
            )
        
        return table
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = True) -> Path:
        """Validate file path and return Path object."""
        file_path = Path(path)
        
        if must_exist and not file_path.exists():
            raise ValueError(f"File does not exist: {path}")
        
        return file_path
    
    @staticmethod
    def validate_directory_path(path: str, create_if_missing: bool = False) -> Path:
        """Validate directory path and optionally create it."""
        dir_path = Path(path)
        
        if not dir_path.exists():
            if create_if_missing:
                dir_path.mkdir(parents=True, exist_ok=True)
                rprint(f"[green]Created directory: {dir_path}[/green]")
            else:
                raise ValueError(f"Directory does not exist: {path}")
        
        return dir_path
    
    @staticmethod
    def get_file_selection(
        directory: Path,
        pattern: str = "*",
        prompt: str = "Select a file:"
    ) -> Optional[Path]:
        """Interactive file selection from directory."""
        files = list(directory.glob(pattern))
        
        if not files:
            rprint(f"[yellow]No files found matching pattern: {pattern}[/yellow]")
            return None
        
        # Display files with numbers
        rprint(f"\n[blue]{prompt}[/blue]")
        for i, file_path in enumerate(files, 1):
            rprint(f"  {i}. {file_path.name}")
        
        # Get user selection
        while True:
            try:
                choice = IntPrompt.ask(
                    "Enter file number",
                    default=1,
                    show_default=True
                )
                
                if 1 <= choice <= len(files):
                    return files[choice - 1]
                else:
                    rprint(f"[red]Please enter a number between 1 and {len(files)}[/red]")
                    
            except KeyboardInterrupt:
                rprint("\n[yellow]Selection cancelled[/yellow]")
                return None


class ProgressTracker:
    """Enhanced progress tracking for CLI operations."""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.progress = None
        self.task = None
    
    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        )
        self.progress.start()
        self.task = self.progress.add_task(self.description, total=self.total_steps)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.stop()
    
    def update(self, step_description: str, advance: int = 1):
        """Update progress with new step description."""
        if self.progress and self.task:
            self.progress.update(
                self.task,
                description=f"{self.description} - {step_description}",
                advance=advance
            )
            self.current_step += advance
    
    def complete(self, final_message: str = "Completed"):
        """Mark progress as complete."""
        if self.progress and self.task:
            remaining = self.total_steps - self.current_step
            if remaining > 0:
                self.progress.update(
                    self.task,
                    description=f"{self.description} - {final_message}",
                    advance=remaining
                )