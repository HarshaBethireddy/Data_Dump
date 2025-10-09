"""
Main entry point for the Enterprise API Testing Framework.

This allows the framework to be run as a module:
python -m refactored_codebase
"""

import sys
from refactored_codebase.cli.main import cli

if __name__ == "__main__":
    cli()