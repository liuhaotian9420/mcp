"""
Core module import handling for the CLI.
"""

import os
import sys
import logging
from types import ModuleType
import importlib.util

# Configure a logger for the CLI
logger = logging.getLogger("mcp_sdk_cli.imports")


def import_core_modules() -> ModuleType:
    """
    Import the core modules for the MCP CLI.
    
    This function attempts multiple import strategies to handle different execution contexts:
    1. Direct import (when installed as a package)
    2. Relative import (when running from within the package)
    3. Dynamic import using file paths (last resort)
    
    Returns:
        ModuleType: A module object containing the core functionality
    
    Raises:
        ImportError: If all import attempts fail
    """
    # Get the current directory (where this imports.py file is located)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # For debugging
    logger.debug(f"Current directory: {current_dir}")
    logger.debug(f"sys.path: {sys.path}")
    
    # Create a mock module as a fallback if all imports fail
    # This is primarily for testing and development scenarios
    mock_core = ModuleType("mock_core")
    
    def mock_build_mcp_package(*args, **kwargs):
        logger.error("Using mock build_mcp_package. This is a placeholder and won't actually build a package.")
        return None
    
    # Add mock functions to the mock module
    setattr(mock_core, "build_mcp_package", lambda *args, **kwargs: None)
    
    # Collect module search directories for debugging
    module_search_dirs = [current_dir]
    module_search_dirs.extend([os.path.dirname(current_dir), os.path.dirname(os.path.dirname(current_dir))])
    logger.debug(f"Module search directories: {module_search_dirs}")
    
    # Attempt 1: Direct import (preferred if mcpy_cli is installed or src is in PYTHONPATH)
    try:
        # Import packaging module directly
        from mcpy_cli import packaging as packaging_module
        
        logger.debug("Successfully imported packaging module using direct import: from mcpy_cli import packaging")
        return packaging_module
    except ImportError as e:
        logger.warning(f"Direct import (from mcpy_cli import packaging) failed: {e}")
    
    # Attempt 2: Relative import (useful when running cli scripts directly from within the package structure)
    try:
        # Import packaging module using relative import
        from .. import packaging as packaging_module
        
        logger.debug("Successfully imported packaging module using relative import: from .. import packaging")
        return packaging_module
    except ImportError as e:
        logger.warning(f"Relative import (from .. import packaging) failed: {e}")
    
    # Attempt 3: Dynamic loading using sys.path manipulation or importlib (more complex, last resort)
    # This section tries to dynamically load based on file paths.
    # current_dir is the directory of this imports.py file: .../mcpy_cli/cli/
    # We expect packaging.py to be in .../mcpy_cli/
    try:
        # Look for packaging.py in the parent directory of current_dir (i.e., mcpy_cli/)
        module_path = os.path.join(current_dir, "..", "packaging.py")
        module_name = "mcpy_cli.packaging"  # Expected module name
        
        if os.path.exists(module_path):
            logger.debug(f"Attempting dynamic import from {module_path}")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec and spec.loader:
                core_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(core_module)
                logger.debug("Successfully loaded packaging module via dynamic import")
                return core_module
            else:
                logger.warning(f"Failed to create module spec from {module_path}")
        else:
            logger.warning(f"Module path not found: {module_path}")
    except Exception as e:
        logger.warning(f"Dynamic import attempt failed: {e}")

    # If we reach here, all import attempts failed
    logger.error("All import attempts failed")
    logger.error(f"sys.path: {sys.path}")
    logger.error(f"Current directory: {os.getcwd()}")
    logger.error(f"Module search directories: {module_search_dirs}")

    # Raise a clear error
    raise ImportError(
        "Failed to import core modules. Make sure the package is installed or run from the correct directory."
    )
