"""
Command Line Interface for the Enterprise API Testing Framework.

This package provides a modern CLI interface with:
- Rich console output with colors and progress bars
- Comprehensive command structure
- Interactive configuration
- Detailed help and documentation
"""

from refactored_codebase.cli.main import cli
from refactored_codebase.cli.commands import test, compare, merge, config

__all__ = ["cli", "test", "compare", "merge", "config"]