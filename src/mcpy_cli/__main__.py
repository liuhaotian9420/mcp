#!/usr/bin/env python
"""
Main entry point for the mcpy_cli package.
"""

import sys
import os
import importlib.util

# Simple approach to make imports work properly
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
src_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(src_dir)
sys.path.insert(0, project_root)


# Define function to dynamically import the CLI app
def _import_cli_app():
    # First try the installed package import (when installed via pip)
    try:
        from mcpy_cli.cli.main import app as cli_app
        return cli_app
    except ImportError:
        pass

    # Then try development import paths
    try:
        from src.mcpy_cli.cli.main import app as cli_app
        return cli_app
    except ImportError:
        pass

    # Try relative import
    try:
        from .cli.main import app as cli_app
        return cli_app
    except ImportError:
        pass

    # Try alternative import paths using importlib
    try:
        spec = importlib.util.spec_from_file_location(
            "cli_main", os.path.join(current_dir, "cli", "main.py")
        )
        if spec and spec.loader:
            cli_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cli_module)
            return cli_module.app
    except Exception:
        pass

    # If all else fails, raise an error
    raise ImportError("Cannot import CLI app")


# Entry point
def main():
    app = _import_cli_app()
    app()


if __name__ == "__main__":
    main()
