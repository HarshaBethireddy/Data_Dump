"""
Main CLI entry point for the Enterprise API Testing Framework.

This module provides the main command-line interface with rich console output,
comprehensive help, and organized command structure.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from refactored_codebase import __version__, FRAMEWORK_NAME
from refactored_codebase.config.settings import get_settings, create_default_configs
from refactored_codebase.utils.logging import setup_logging


# Initialize rich console
console = Console()


def print_banner():
    """Print framework banner."""
    banner_text = Text()
    banner_text.append(f"{FRAMEWORK_NAME}\n", style="bold blue")
    banner_text.append(f"Version {__version__}\n", style="dim")
    banner_text.append("Enterprise-grade API testing with modern Python", style="italic")
    
    panel = Panel(
        banner_text,
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--config-dir', type=click.Path(), help='Configuration directory path')
@click.option('--environment', type=click.Choice(['development', 'testing', 'staging', 'production']), 
              help='Environment to use')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--quiet', is_flag=True, help='Suppress output')
@click.pass_context
def cli(ctx, version, config_dir, environment, debug, quiet):
    """
    Enterprise API Testing Framework 2.0
    
    A modern, scalable API testing framework built with enterprise best practices.
    
    Examples:
        # Run tests with both data types
        framework test --data-type both
        
        # Compare two test runs
        framework compare --pre-folder run1 --post-folder run2
        
        # Merge CSV results
        framework merge --csv-folder results
        
        # Configure framework
        framework config init
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Handle version flag
    if version:
        console.print(f"{FRAMEWORK_NAME} version {__version__}")
        sys.exit(0)
    
    # Show banner if no command provided
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("\n💡 Use --help to see available commands")
        sys.exit(0)
    
    # Setup quiet mode
    if quiet:
        console.quiet = True
    
    # Initialize configuration
    try:
        # Create default configs if they don't exist
        create_default_configs()
        
        # Load settings
        settings = get_settings()
        
        # Override environment if specified
        if environment:
            settings.environment = environment
        
        # Override debug if specified
        if debug:
            settings.debug = True
        
        # Setup logging
        setup_logging(settings.logging, settings.paths.logs_dir)
        
        # Store settings in context
        ctx.obj['settings'] = settings
        
    except Exception as e:
        console.print(f"❌ Configuration error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--data-type', 
              type=click.Choice(['regular', 'prequal', 'both']), 
              default='both',
              help='Type of test data to process')
@click.option('--count', type=int, help='Number of requests to process')
@click.option('--parallel', type=int, help='Number of parallel threads')
@click.option('--think-time', type=float, help='Think time between requests (seconds)')
@click.option('--output-dir', type=click.Path(), help='Output directory for results')
@click.option('--dry-run', is_flag=True, help='Validate configuration without running tests')
@click.pass_context
def test(ctx, data_type, count, parallel, think_time, output_dir, dry_run):
    """
    Execute API tests with specified data type.
    
    This command processes JSON templates, injects APPIDs, sends requests
    to the configured API endpoint, and generates comprehensive reports.
    
    Examples:
        # Run all tests
        framework test
        
        # Run only regular tests with 5 parallel threads
        framework test --data-type regular --parallel 5
        
        # Run 100 prequal tests with custom think time
        framework test --data-type prequal --count 100 --think-time 2.0
        
        # Dry run to validate configuration
        framework test --dry-run
    """
    from refactored_codebase.cli.commands.test import execute_test_command
    
    settings = ctx.obj['settings']
    
    # Override settings with command line options
    if parallel:
        settings.test.parallel_count = parallel
    if think_time:
        settings.test.think_time = think_time
    
    try:
        execute_test_command(
            settings=settings,
            data_type=data_type,
            count=count,
            output_dir=Path(output_dir) if output_dir else None,
            dry_run=dry_run
        )
    except Exception as e:
        console.print(f"❌ Test execution failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--pre-folder', required=True, help='Pre-test results folder')
@click.option('--post-folder', required=True, help='Post-test results folder')
@click.option('--output-dir', type=click.Path(), help='Output directory for comparison results')
@click.option('--ignore-order', is_flag=True, help='Ignore array order in comparisons')
@click.option('--ignore-keys', help='Comma-separated list of keys to ignore')
@click.pass_context
def compare(ctx, pre_folder, post_folder, output_dir, ignore_order, ignore_keys):
    """
    Compare two sets of test results.
    
    This command performs detailed JSON comparison between pre and post
    test results, generating comprehensive difference reports.
    
    Examples:
        # Compare two result folders
        framework compare --pre-folder results1 --post-folder results2
        
        # Compare ignoring array order
        framework compare --pre-folder results1 --post-folder results2 --ignore-order
        
        # Compare ignoring specific keys
        framework compare --pre-folder results1 --post-folder results2 --ignore-keys timestamp,id
    """
    from refactored_codebase.cli.commands.compare import execute_compare_command
    
    settings = ctx.obj['settings']
    
    ignore_keys_set = set()
    if ignore_keys:
        ignore_keys_set = set(key.strip() for key in ignore_keys.split(','))
    
    try:
        execute_compare_command(
            settings=settings,
            pre_folder=pre_folder,
            post_folder=post_folder,
            output_dir=Path(output_dir) if output_dir else None,
            ignore_order=ignore_order,
            ignore_keys=ignore_keys_set
        )
    except Exception as e:
        console.print(f"❌ Comparison failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option('--csv-folder', required=True, help='Folder containing CSV files to merge')
@click.option('--output-file', help='Output Excel file name')
@click.option('--include-summary', is_flag=True, help='Include summary sheet')
@click.pass_context
def merge(ctx, csv_folder, output_file, include_summary):
    """
    Merge CSV files into Excel reports.
    
    This command combines multiple CSV result files into organized
    Excel workbooks with optional summary sheets.
    
    Examples:
        # Merge all CSV files in a folder
        framework merge --csv-folder results/csv
        
        # Merge with custom output file and summary
        framework merge --csv-folder results/csv --output-file report.xlsx --include-summary
    """
    from refactored_codebase.cli.commands.merge import execute_merge_command
    
    settings = ctx.obj['settings']
    
    try:
        execute_merge_command(
            settings=settings,
            csv_folder=csv_folder,
            output_file=output_file,
            include_summary=include_summary
        )
    except Exception as e:
        console.print(f"❌ Merge failed: {e}", style="red")
        sys.exit(1)


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command('init')
@click.option('--force', is_flag=True, help='Overwrite existing configuration')
@click.pass_context
def config_init(ctx, force):
    """Initialize configuration files."""
    from refactored_codebase.cli.commands.config import execute_config_init
    
    try:
        execute_config_init(force=force)
    except Exception as e:
        console.print(f"❌ Configuration initialization failed: {e}", style="red")
        sys.exit(1)


@config.command('show')
@click.option('--section', help='Show specific configuration section')
@click.pass_context
def config_show(ctx, section):
    """Show current configuration."""
    from refactored_codebase.cli.commands.config import execute_config_show
    
    settings = ctx.obj['settings']
    
    try:
        execute_config_show(settings=settings, section=section)
    except Exception as e:
        console.print(f"❌ Failed to show configuration: {e}", style="red")
        sys.exit(1)


@config.command('validate')
@click.pass_context
def config_validate(ctx):
    """Validate current configuration."""
    from refactored_codebase.cli.commands.config import execute_config_validate
    
    settings = ctx.obj['settings']
    
    try:
        execute_config_validate(settings=settings)
    except Exception as e:
        console.print(f"❌ Configuration validation failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx):
    """Show framework information and status."""
    settings = ctx.obj['settings']
    
    console.print("\n📊 Framework Information", style="bold blue")
    console.print(f"Version: {__version__}")
    console.print(f"Environment: {settings.environment.value}")
    console.print(f"Debug Mode: {settings.debug}")
    console.print(f"Config Directory: {settings.paths.config_dir}")
    console.print(f"Data Directory: {settings.paths.data_dir}")
    console.print(f"Output Directory: {settings.paths.output_dir}")
    
    console.print("\n🔧 API Configuration", style="bold green")
    console.print(f"URL: {settings.api.url}")
    console.print(f"Host: {settings.api.host}")
    console.print(f"Timeout: {settings.api.timeout}s")
    console.print(f"SSL Verification: {settings.api.verify_ssl}")
    
    console.print("\n⚙️ Test Configuration", style="bold yellow")
    console.print(f"Parallel Count: {settings.test.parallel_count}")
    console.print(f"Think Time: {settings.test.think_time}s")
    console.print(f"Batch Size: {settings.test.batch_size}")
    
    # Check APPID manager status
    from refactored_codebase.core.appid_manager import AppIDManager
    appid_manager = AppIDManager(settings.appid)
    state_info = appid_manager.get_state_info()
    
    console.print("\n🔢 APPID Status", style="bold magenta")
    console.print(f"Regular Range: {state_info['config']['regular_range']}")
    console.print(f"Prequal Range: {state_info['config']['prequal_range']}")
    console.print(f"Available Regular: {state_info['available_regular']:,}")
    console.print(f"Available Prequal: {state_info['available_prequal']:,}")
    console.print(f"Total Generated: {state_info['total_generated']:,}")


if __name__ == '__main__':
    cli()