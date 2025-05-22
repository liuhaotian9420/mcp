#!/usr/bin/env python
# Test runner for MCP package tests

import unittest
import sys
import os

# Ensure the src directory is discoverable for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)
# Also add the src directory to the path
sys.path.append(os.path.join(project_root, "src"))


def run_tests():
    """Run all tests for the MCP package."""
    # Create a test suite
    test_suite = unittest.TestSuite()

    # Add test cases from the working test modules
    test_loader = unittest.TestLoader()

    # Add tests from test_discovery.py
    from tests.test_mcp_package import test_discovery

    test_suite.addTests(test_loader.loadTestsFromModule(test_discovery))

    # Add tests from test_multi_mount.py
    from tests.test_mcp_package import test_multi_mount

    test_suite.addTests(test_loader.loadTestsFromModule(test_multi_mount))

    # Add tests from test_packaging.py
    from tests.test_mcp_package import test_packaging

    test_suite.addTests(test_loader.loadTestsFromModule(test_packaging))

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Return exit code based on test results for CI/CD pipelines
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
