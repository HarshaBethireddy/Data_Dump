"""
CLI module for API Test Framework.

This module provides a rich command-line interface with:
- Interactive commands with progress indicators
- Colored output and beautiful formatting
- Configuration management and validation
- Real-time status updates and metrics display
- Auto-completion and comprehensive help

Built with Typer for modern CLI experience.
"""

from api_test_framework.cli.main import app

__all__ = ["app"]