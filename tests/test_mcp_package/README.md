# MCP Package Test Suite

This directory contains a comprehensive test suite for the MCP (Model Context Protocol) package functionality. The tests simulate a user environment to verify that the MCP package works correctly in real-world scenarios.

## Test Structure

The test suite is organized as follows:

- `sample_tools.py` - Sample MCP tools used for testing
- `nested/nested_tools.py` - Nested MCP tools to test directory-based routing
- `test_discovery.py` - Tests for the discovery module that finds Python files and functions
- `test_app_builder.py` - Tests for the app_builder module that creates MCP applications
- `test_main_template.py` - Tests for the main.py template functionality
- `test_packaging.py` - Tests for the packaging module that builds MCP packages
- `test_multi_mount.py` - Tests for the multi-mount architecture with directory-based routing
- `run_tests.py` - Script to run all tests in the package

## Running the Tests

To run all tests in the suite, use the following command from the project root directory:

```bash
python -m tests.test_mcp_package.run_tests
```

Or you can run individual test files:

```bash
python -m tests.test_mcp_package.test_discovery
python -m tests.test_mcp_package.test_app_builder
# etc.
```

## Test Coverage

The test suite covers the following aspects of the MCP package:

1. **Discovery** - Finding Python files and functions in a directory structure
2. **App Building** - Creating MCP applications from discovered functions
3. **Main Template** - Testing the main.py template that runs the MCP service
4. **Packaging** - Building MCP packages for distribution
5. **Multi-Mount Architecture** - Testing directory-based routing for MCP tools

## Adding New Tests

To add new tests to the suite:

1. Create a new test file in the `test_mcp_package` directory
2. Add your test cases as methods in a class that inherits from `unittest.TestCase`
3. Update `run_tests.py` to include your new test class

## Test Environment

The tests create temporary directories and files to simulate a user environment. These are automatically cleaned up after the tests run.
