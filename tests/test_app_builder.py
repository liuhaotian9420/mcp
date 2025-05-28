import unittest
import os
import sys
import pathlib
import logging
import tempfile
import shutil
from unittest.mock import Mock, patch

# Configure logging for tests
logging.basicConfig(level=logging.ERROR)

# Ensure the src directory is discoverable for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src"))

# Import required modules
try:
    from mcpy_cli.app_builder import (
        create_mcp_instances,
        discover_and_group_functions,
        get_route_from_path,
        validate_resource_prefix,
        SessionToolCallCache,
    )
    from mcpy_cli.app_builder.validation import validate_and_wrap_tool
    from mcpy_cli.app_builder.mocking import get_fastmcp_class

    imports_successful = True
except ImportError as e:
    print(f"Could not import required modules: {e}. Tests will be skipped.")
    imports_successful = False


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestAppBuilderRouting(unittest.TestCase):
    """Tests for the app_builder routing functionality."""

    def test_get_route_from_path(self):
        """Test getting a route from a file path."""
        # Create test paths using relative paths to avoid platform-specific issues
        base_dir = pathlib.Path(os.path.dirname(__file__))
        file_path = base_dir / "sample_tools.py"

        # Get the route
        route = get_route_from_path(file_path, base_dir)

        # Extract just the last part to avoid path separator issues
        result_parts = route.split("/")
        self.assertEqual(result_parts[-1], "sample_tools")

    def test_get_route_from_init_file(self):
        """Test getting a route from an __init__.py file."""
        # Create test paths using relative paths
        base_dir = pathlib.Path(os.path.dirname(__file__))
        nested_dir = base_dir / "nested"
        nested_dir.mkdir(exist_ok=True)

        # Create an __init__.py file for testing
        init_file = nested_dir / "__init__.py"
        init_file.touch()

        try:
            # Get the route
            route = get_route_from_path(init_file, base_dir)

            # Extract just the last part to avoid path separator issues
            result_parts = route.split("/")
            self.assertEqual(result_parts[-1], "nested")
        finally:
            # Clean up
            if init_file.exists():
                init_file.unlink()
            if nested_dir.exists():
                nested_dir.rmdir()

    def test_validate_resource_prefix(self):
        """Test resource prefix validation."""
        # Valid prefixes should be returned as-is
        self.assertEqual(validate_resource_prefix("tools"), "tools")
        self.assertEqual(validate_resource_prefix("resources"), "resources")

        # Underscores get converted to hyphens
        self.assertEqual(validate_resource_prefix("my_tools"), "my-tools")

        # Invalid prefixes should be sanitized
        self.assertEqual(validate_resource_prefix(""), "")  # Empty string stays empty
        self.assertEqual(validate_resource_prefix("123invalid"), "x123invalid")
        self.assertEqual(validate_resource_prefix("invalid-name"), "invalid-name")


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestAppBuilderValidation(unittest.TestCase):
    """Tests for the app_builder validation functionality."""

    def test_validate_and_wrap_tool_with_good_function(self):
        """Test validation and wrapping of a well-formed function."""

        def good_function(x: int, y: str) -> str:
            """A well-documented function.

            Args:
                x: An integer parameter
                y: A string parameter

            Returns:
                A formatted string
            """
            return f"{y}: {x}"

        # Create a mock MCP instance
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)

        # Should not raise any exceptions
        try:
            validate_and_wrap_tool(
                mock_mcp, good_function, "good_function", pathlib.Path("test.py")
            )
        except Exception as e:
            self.fail(
                f"validate_and_wrap_tool raised an exception for a good function: {e}"
            )

    def test_validate_and_wrap_tool_missing_docstring(self):
        """Test validation of a function without docstring."""

        def bad_function(x: int) -> int:
            return x * 2

        # Create a mock MCP instance
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)

        # Should log a warning but not raise an exception
        with self.assertLogs(level="WARNING") as log:
            validate_and_wrap_tool(
                mock_mcp, bad_function, "bad_function", pathlib.Path("test.py")
            )

        self.assertTrue(any("missing a docstring" in record for record in log.output))

    def test_validate_and_wrap_tool_missing_type_hints(self):
        """Test validation of a function without type hints."""

        def bad_function(x, y):
            """A function without type hints."""
            return x + y

        # Create a mock MCP instance
        mock_mcp = Mock()
        mock_mcp.tool = Mock(return_value=lambda func: func)

        # Should log warnings but not raise an exception
        with self.assertLogs(level="WARNING") as log:
            validate_and_wrap_tool(
                mock_mcp, bad_function, "bad_function", pathlib.Path("test.py")
            )

        # Should warn about missing type hints
        log_output = " ".join(log.output)
        self.assertIn("missing a type hint", log_output)


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestAppBuilderCaching(unittest.TestCase):
    """Tests for the app_builder caching functionality."""

    def setUp(self):
        """Set up test environment."""
        self.cache = SessionToolCallCache()

    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        session_id = "test_session"
        tool_name = "test_tool"
        args = {"x": 1, "y": 2}
        result = {"result": 3}

        # Test cache miss
        cached_result = self.cache.get(session_id, tool_name, args)
        self.assertIsNone(cached_result)

        # Test cache set and hit
        self.cache.set(session_id, tool_name, args, result)
        cached_result = self.cache.get(session_id, tool_name, args)
        self.assertEqual(cached_result, result)

    def test_cache_different_sessions(self):
        """Test that cache is isolated between sessions."""
        tool_name = "test_tool"
        args = {"x": 1}
        result1 = {"result": "session1"}
        result2 = {"result": "session2"}

        # Set different results for different sessions
        self.cache.set("session1", tool_name, args, result1)
        self.cache.set("session2", tool_name, args, result2)

        # Verify isolation
        self.assertEqual(self.cache.get("session1", tool_name, args), result1)
        self.assertEqual(self.cache.get("session2", tool_name, args), result2)

    def test_cache_clear_session(self):
        """Test clearing a specific session from cache."""
        self.cache.set("session1", "tool1", {"x": 1}, {"result": 1})
        self.cache.set("session2", "tool1", {"x": 1}, {"result": 2})

        # Clear session1
        self.cache.clear_session("session1")

        # Verify session1 is cleared but session2 remains
        self.assertIsNone(self.cache.get("session1", "tool1", {"x": 1}))
        self.assertEqual(self.cache.get("session2", "tool1", {"x": 1}), {"result": 2})


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestAppBuilderMocking(unittest.TestCase):
    """Tests for the app_builder mocking functionality."""

    def test_get_fastmcp_class(self):
        """Test getting FastMCP class (real or mock)."""
        FastMCP = get_fastmcp_class()

        # Should return a class that can be instantiated
        instance = FastMCP(name="TestMCP")
        self.assertEqual(instance.name, "TestMCP")
        self.assertTrue(hasattr(instance, "tool"))

    def test_mock_tool_decorator(self):
        """Test the mock tool decorator functionality."""
        FastMCP = get_fastmcp_class()
        mock_mcp = FastMCP(name="TestMCP")

        @mock_mcp.tool()
        def test_tool(x: int) -> int:
            """Test tool."""
            return x * 2

        # The decorator should return the function unchanged
        self.assertEqual(test_tool(5), 10)


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestAppBuilderIntegration(unittest.TestCase):
    """Integration tests for the app_builder functionality."""

    def setUp(self):
        """Set up test environment with temporary files."""
        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_app_builder_"))

        # Create a sample Python file with tools
        self.sample_file = self.temp_dir / "sample_tools.py"
        with open(self.sample_file, "w") as f:
            f.write('''
def add_numbers(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b

def greet_user(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}!"
''')

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def test_discover_and_group_functions(self):
        """Test discovering and grouping functions from files."""
        # Test discovery
        functions_by_file, base_dir = discover_and_group_functions(
            source_path_str=str(self.sample_file), target_function_names=None
        )

        # Should find functions grouped by file
        self.assertIsInstance(functions_by_file, dict)
        self.assertGreater(len(functions_by_file), 0)
        self.assertIsInstance(base_dir, pathlib.Path)

    @patch("mcpy_cli.app_builder.instance_factory.get_fastmcp_class")
    def test_create_mcp_instances(self, mock_get_fastmcp_class):
        """Test creating MCP instances from source files."""
        # Mock FastMCP class
        FastMCP = get_fastmcp_class()
        mock_get_fastmcp_class.return_value = FastMCP

        # First discover functions
        functions_by_file, base_dir = discover_and_group_functions(
            source_path_str=str(self.sample_file), target_function_names=None
        )

        # Test instance creation
        instances = create_mcp_instances(
            functions_by_file=functions_by_file,
            base_dir=base_dir,
            mcp_server_name="TestMCP",
        )

        # Should create at least one instance
        self.assertIsInstance(instances, dict)
        self.assertGreater(len(instances), 0)


if __name__ == "__main__":
    unittest.main()
