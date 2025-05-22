"""Test suite for MCP package functionality.

This package contains tests that simulate a user environment for the MCP package.
It includes test files for various components of the MCP package:

- test_discovery.py: Tests for the discovery module that finds Python files and functions
- test_app_builder.py: Tests for the app_builder module that creates MCP applications
- test_main_template.py: Tests for the main.py template functionality
- test_packaging.py: Tests for the packaging module that builds MCP packages
- test_multi_mount.py: Tests for the multi-mount architecture with directory-based routing

The package also includes sample MCP tools in sample_tools.py and nested/nested_tools.py
that are used by the tests to simulate a real user environment.

To run all tests, use the run_tests.py script:
    python -m tests.test_mcp_package.run_tests
"""

__version__ = "0.1.0"
