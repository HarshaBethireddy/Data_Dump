"""
Test command implementation for executing API tests.
"""

import time
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

from refactored_codebase.config.settings import Settings
from refactored_codebase.core.appid_manager import AppIDManager
from refactored_codebase.core.data_manager import TestDataManager, DataType
from refactored_codebase.core.http_client import HTTPClient
from refactored_codebase.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


def execute_test_command(
    settings: Settings,
    data_type: str,
    count: Optional[int] = None,
    output_dir: Optional[Path] = None,
    dry_run: bool = False
) -> None:
    """
    Execute the test command.
    
    Args:
        settings: Framework settings
        data_type: Type of data to test (regular/prequal/both)
        count: Number of tests to run
        output_dir: Output directory override
        dry_run: Whether to perform a dry run
    """
    logger.info(f"Starting test execution - data_type: {data_type}, dry_run: {dry_run}")
    
    # Initialize managers
    appid_manager = AppIDManager(settings.appid)
    data_manager = TestDataManager(settings.paths, appid_manager)
    
    # Determine output directory
    if output_dir is None:
        from refactored_codebase.core.run_manager import RunManager
        run_manager = RunManager(settings.paths.reports_dir)
        run_id = run_manager.get_next_run_id()
        output_dir = settings.paths.responses_dir / f"run_{run_id:06d}"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"\n🚀 Starting API Test Execution", style="bold blue")
    console.print(f"Data Type: {data_type}")
    console.print(f"Output Directory: {output_dir}")
    console.print(f"Dry Run: {dry_run}")
    
    if dry_run:
        _perform_dry_run(settings, data_manager, data_type, count)
        return
    
    # Execute tests based on data type
    if data_type == "both":
        _execute_both_data_types(settings, data_manager, appid_manager, output_dir, count)
    elif data_type == "regular":
        _execute_single_data_type(settings, data_manager, appid_manager, DataType.REGULAR, output_dir, count)
    elif data_type == "prequal":
        _execute_single_data_type(settings, data_manager, appid_manager, DataType.PREQUAL, output_dir, count)
    else:
        raise ValueError(f"Invalid data type: {data_type}")
    
    console.print(f"\n✅ Test execution completed successfully!", style="bold green")
    console.print(f"Results saved to: {output_dir}")


def _perform_dry_run(
    settings: Settings,
    data_manager: TestDataManager,
    data_type: str,
    count: Optional[int]
) -> None:
    """Perform a dry run to validate configuration."""
    console.print("\n🔍 Performing Dry Run Validation", style="bold yellow")
    
    # Validate configuration
    try:
        # Test API connectivity
        with HTTPClient(settings.api) as client:
            console.print("✅ API configuration valid")
        
        # Check template availability
        stats = data_manager.get_template_stats()
        
        table = Table(title="Template Statistics")
        table.add_column("Data Type", style="cyan")
        table.add_column("Templates Found", style="green")
        table.add_column("Directory", style="dim")
        
        for dt, info in stats.items():
            table.add_row(dt, str(info['count']), info['directory'])
        
        console.print(table)
        
        # Validate templates
        validation_results = data_manager.validate_all_templates()
        
        if validation_results['invalid']:
            console.print(f"\n⚠️ Invalid templates found:", style="yellow")
            for invalid_file in validation_results['invalid']:
                console.print(f"  - {invalid_file}", style="red")
        else:
            console.print(f"\n✅ All templates are valid", style="green")
        
        console.print(f"\n✅ Dry run completed successfully", style="bold green")
        
    except Exception as e:
        console.print(f"\n❌ Dry run failed: {e}", style="bold red")
        raise


def _execute_both_data_types(
    settings: Settings,
    data_manager: TestDataManager,
    appid_manager: AppIDManager,
    output_dir: Path,
    count: Optional[int]
) -> None:
    """Execute tests for both regular and prequal data types."""
    console.print("\n📊 Processing Both Data Types", style="bold blue")
    
    # Execute regular tests
    regular_output = output_dir / "regular"
    _execute_single_data_type(settings, data_manager, appid_manager, DataType.REGULAR, regular_output, count)
    
    # Execute prequal tests
    prequal_output = output_dir / "prequal"
    _execute_single_data_type(settings, data_manager, appid_manager, DataType.PREQUAL, prequal_output, count)


def _execute_single_data_type(
    settings: Settings,
    data_manager: TestDataManager,
    appid_manager: AppIDManager,
    data_type: DataType,
    output_dir: Path,
    count: Optional[int]
) -> None:
    """Execute tests for a single data type."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"\n🔄 Processing {data_type.value.title()} Data", style="bold cyan")
    
    # Discover templates
    templates = data_manager.discover_templates(data_type)
    
    if not templates:
        console.print(f"⚠️ No templates found for {data_type.value}", style="yellow")
        return
    
    # Limit count if specified
    if count:
        templates = templates[:count]
    
    console.print(f"Found {len(templates)} templates to process")
    
    # Process templates and send requests
    with HTTPClient(settings.api) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(f"Processing {data_type.value} templates...", total=len(templates))
            
            # Use thread pool for parallel execution
            with ThreadPoolExecutor(max_workers=settings.test.parallel_count) as executor:
                # Submit all tasks
                future_to_template = {
                    executor.submit(_process_single_template, template, data_manager, client, output_dir, settings.test.think_time): template
                    for template in templates
                }
                
                # Process completed tasks
                results = []
                for future in as_completed(future_to_template):
                    template = future_to_template[future]
                    try:
                        result = future.result()
                        results.append(result)
                        progress.update(task, advance=1)
                    except Exception as e:
                        logger.error(f"Failed to process template {template.file_name}: {e}")
                        progress.update(task, advance=1)
    
    # Display results summary
    _display_results_summary(results, data_type)


def _process_single_template(
    template,
    data_manager: TestDataManager,
    client: HTTPClient,
    output_dir: Path,
    think_time: float
) -> dict:
    """Process a single template."""
    try:
        # Apply think time before processing
        if think_time > 0:
            time.sleep(think_time)
        
        # Process template with APPID injection
        processed_data = data_manager.process_template(template)
        
        # Send HTTP request
        response = client.send_json_request(processed_data.data)
        
        # Save request and response
        request_file = output_dir / f"{processed_data.file_name}_{processed_data.appid}_request.json"
        response_file = output_dir / f"{processed_data.file_name}_{processed_data.appid}_response.json"
        
        # Save request
        import json
        with open(request_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data.data, f, indent=2, ensure_ascii=False)
        
        # Save response
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response.to_dict(), f, indent=2, ensure_ascii=False)
        
        return {
            "template": template.file_name,
            "appid": processed_data.appid,
            "status_code": response.status_code,
            "elapsed_time": response.elapsed_time,
            "success": response.is_success,
            "request_file": str(request_file),
            "response_file": str(response_file)
        }
        
    except Exception as e:
        logger.error(f"Error processing template {template.file_name}: {e}")
        return {
            "template": template.file_name,
            "appid": None,
            "status_code": None,
            "elapsed_time": None,
            "success": False,
            "error": str(e)
        }


def _display_results_summary(results: list, data_type: DataType) -> None:
    """Display results summary table."""
    if not results:
        return
    
    # Calculate statistics
    total_requests = len(results)
    successful_requests = sum(1 for r in results if r.get('success', False))
    failed_requests = total_requests - successful_requests
    avg_response_time = sum(r.get('elapsed_time', 0) for r in results if r.get('elapsed_time')) / total_requests
    
    # Create summary table
    table = Table(title=f"{data_type.value.title()} Test Results Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Requests", str(total_requests))
    table.add_row("Successful", str(successful_requests))
    table.add_row("Failed", str(failed_requests))
    table.add_row("Success Rate", f"{(successful_requests/total_requests)*100:.1f}%")
    table.add_row("Avg Response Time", f"{avg_response_time:.3f}s")
    
    console.print(table)
    
    # Show failed requests if any
    if failed_requests > 0:
        console.print(f"\n❌ Failed Requests:", style="red")
        for result in results:
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown error')
                console.print(f"  - {result['template']}: {error_msg}", style="red")