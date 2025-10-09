"""
Compare command implementation for comparing test results.
"""

import json
from pathlib import Path
from typing import Set, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from refactored_codebase.config.settings import Settings
from refactored_codebase.utils.json_utils import JSONComparator, ComparisonResult
from refactored_codebase.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


def execute_compare_command(
    settings: Settings,
    pre_folder: str,
    post_folder: str,
    output_dir: Optional[Path] = None,
    ignore_order: bool = False,
    ignore_keys: Optional[Set[str]] = None
) -> None:
    """
    Execute the compare command.
    
    Args:
        settings: Framework settings
        pre_folder: Pre-test results folder
        post_folder: Post-test results folder
        output_dir: Output directory override
        ignore_order: Whether to ignore array order
        ignore_keys: Set of keys to ignore
    """
    logger.info(f"Starting comparison - pre: {pre_folder}, post: {post_folder}")
    
    pre_path = Path(pre_folder)
    post_path = Path(post_folder)
    
    if not pre_path.exists():
        raise FileNotFoundError(f"Pre-test folder not found: {pre_path}")
    
    if not post_path.exists():
        raise FileNotFoundError(f"Post-test folder not found: {post_path}")
    
    # Determine output directory
    if output_dir is None:
        output_dir = settings.paths.comparisons_dir / f"compare_{pre_path.name}_vs_{post_path.name}"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"\n🔍 Starting Result Comparison", style="bold blue")
    console.print(f"Pre-test folder: {pre_path}")
    console.print(f"Post-test folder: {post_path}")
    console.print(f"Output directory: {output_dir}")
    console.print(f"Ignore order: {ignore_order}")
    console.print(f"Ignore keys: {ignore_keys or 'None'}")
    
    # Initialize comparator
    comparator = JSONComparator(ignore_order=ignore_order, ignore_keys=ignore_keys or set())
    
    # Find matching files
    pre_files = _find_json_files(pre_path)
    post_files = _find_json_files(post_path)
    
    # Match files by name pattern
    file_pairs = _match_files(pre_files, post_files)
    
    if not file_pairs:
        console.print("⚠️ No matching files found for comparison", style="yellow")
        return
    
    console.print(f"Found {len(file_pairs)} file pairs to compare")
    
    # Perform comparisons
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("Comparing files...", total=len(file_pairs))
        
        for pre_file, post_file in file_pairs:
            try:
                # Load JSON files
                with open(pre_file, 'r', encoding='utf-8') as f:
                    pre_data = json.load(f)
                
                with open(post_file, 'r', encoding='utf-8') as f:
                    post_data = json.load(f)
                
                # Perform comparison
                comparison_report = comparator.compare(pre_data, post_data)
                
                # Save detailed comparison report
                report_file = output_dir / f"{pre_file.stem}_comparison.json"
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "pre_file": str(pre_file),
                        "post_file": str(post_file),
                        "result": comparison_report.result.value,
                        "differences": [diff.__dict__ for diff in comparison_report.differences],
                        "summary": comparison_report.summary,
                        "metadata": comparison_report.metadata
                    }, f, indent=2, ensure_ascii=False)
                
                results.append({
                    "pre_file": pre_file.name,
                    "post_file": post_file.name,
                    "result": comparison_report.result,
                    "difference_count": comparison_report.difference_count,
                    "report_file": report_file
                })
                
                progress.update(task, advance=1)
                
            except Exception as e:
                logger.error(f"Failed to compare {pre_file.name}: {e}")
                results.append({
                    "pre_file": pre_file.name,
                    "post_file": post_file.name if post_file else "Not found",
                    "result": ComparisonResult.ERROR,
                    "difference_count": 0,
                    "error": str(e)
                })
                progress.update(task, advance=1)
    
    # Generate summary report
    _generate_summary_report(results, output_dir)
    
    # Display results
    _display_comparison_results(results)
    
    console.print(f"\n✅ Comparison completed successfully!", style="bold green")
    console.print(f"Results saved to: {output_dir}")


def _find_json_files(directory: Path) -> list[Path]:
    """Find all JSON files in directory recursively."""
    json_files = []
    for file_path in directory.rglob("*.json"):
        if file_path.is_file():
            json_files.append(file_path)
    return sorted(json_files)


def _match_files(pre_files: list[Path], post_files: list[Path]) -> list[tuple[Path, Optional[Path]]]:
    """Match pre and post files by name pattern."""
    file_pairs = []
    
    # Create mapping of post files by base name
    post_file_map = {}
    for post_file in post_files:
        # Extract base name (remove response/request suffixes and APPID)
        base_name = _extract_base_name(post_file.name)
        if base_name not in post_file_map:
            post_file_map[base_name] = []
        post_file_map[base_name].append(post_file)
    
    # Match pre files with post files
    for pre_file in pre_files:
        base_name = _extract_base_name(pre_file.name)
        
        if base_name in post_file_map:
            # Find best match (prefer same type - request/response)
            best_match = None
            for post_file in post_file_map[base_name]:
                if _get_file_type(pre_file.name) == _get_file_type(post_file.name):
                    best_match = post_file
                    break
            
            if not best_match and post_file_map[base_name]:
                best_match = post_file_map[base_name][0]
            
            file_pairs.append((pre_file, best_match))
        else:
            file_pairs.append((pre_file, None))
    
    return file_pairs


def _extract_base_name(filename: str) -> str:
    """Extract base template name from filename."""
    # Remove .json extension
    name = filename.replace('.json', '')
    
    # Remove APPID pattern (numbers at the end)
    import re
    name = re.sub(r'_\d+$', '', name)
    
    # Remove request/response suffix
    name = re.sub(r'_(request|response)$', '', name)
    
    return name


def _get_file_type(filename: str) -> str:
    """Get file type (request/response) from filename."""
    if '_request' in filename:
        return 'request'
    elif '_response' in filename:
        return 'response'
    else:
        return 'unknown'


def _generate_summary_report(results: list, output_dir: Path) -> None:
    """Generate summary report."""
    summary = {
        "total_comparisons": len(results),
        "identical": sum(1 for r in results if r["result"] == ComparisonResult.IDENTICAL),
        "different": sum(1 for r in results if r["result"] in [ComparisonResult.DIFFERENT, ComparisonResult.STRUCTURE_DIFFERENT, ComparisonResult.VALUES_DIFFERENT]),
        "errors": sum(1 for r in results if r["result"] == ComparisonResult.ERROR),
        "total_differences": sum(r.get("difference_count", 0) for r in results),
        "results": results
    }
    
    summary_file = output_dir / "comparison_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)


def _display_comparison_results(results: list) -> None:
    """Display comparison results table."""
    table = Table(title="Comparison Results")
    table.add_column("Pre File", style="cyan")
    table.add_column("Post File", style="cyan")
    table.add_column("Result", style="green")
    table.add_column("Differences", style="yellow")
    
    for result in results[:20]:  # Show first 20 results
        result_style = "green" if result["result"] == ComparisonResult.IDENTICAL else "red"
        table.add_row(
            result["pre_file"],
            result.get("post_file", "Not found"),
            result["result"].value,
            str(result.get("difference_count", 0)),
            style=result_style if result["result"] == ComparisonResult.IDENTICAL else None
        )
    
    console.print(table)
    
    # Summary statistics
    total = len(results)
    identical = sum(1 for r in results if r["result"] == ComparisonResult.IDENTICAL)
    different = sum(1 for r in results if r["result"] in [ComparisonResult.DIFFERENT, ComparisonResult.STRUCTURE_DIFFERENT, ComparisonResult.VALUES_DIFFERENT])
    errors = sum(1 for r in results if r["result"] == ComparisonResult.ERROR)
    
    summary_table = Table(title="Summary Statistics")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Count", style="green")
    summary_table.add_column("Percentage", style="yellow")
    
    summary_table.add_row("Total Comparisons", str(total), "100.0%")
    summary_table.add_row("Identical", str(identical), f"{(identical/total)*100:.1f}%" if total > 0 else "0%")
    summary_table.add_row("Different", str(different), f"{(different/total)*100:.1f}%" if total > 0 else "0%")
    summary_table.add_row("Errors", str(errors), f"{(errors/total)*100:.1f}%" if total > 0 else "0%")
    
    console.print(summary_table)