"""
Command Line Interface module.

Provides command-line interface functionality for the API testing framework
with argument parsing and command execution.
"""

from .main import main, create_cli_parser

__all__ = [
    "main",
    "create_cli_parser"
]