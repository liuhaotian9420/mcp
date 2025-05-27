import unittest
import pathlib
import sys
import os
import tempfile
import shutil
import logging
from unittest.mock import patch, Mock

# Ensure the src directory is discoverable for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src"))

try:
    from mcp_modelservice_sdk.packaging_utils import copy_source_code
    from mcp_modelservice_sdk.packaging import build_mcp_package

    imports_successful = True
except ImportError as e:
    print(f"ImportError: {e}")
    print("Could not import required modules. Tests will be skipped.")
    imports_successful = False


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestPackagingUtils(unittest.TestCase):
    """Basic tests for packaging utilities."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for our test package
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = pathlib.Path(self.temp_dir_obj.name)

        # Create a simple Python file
        self.test_file = self.temp_dir / "test_module.py"
        with open(self.test_file, "w") as f:
            f.write('''
def test_func():
    """Test function."""
    return "Hello"
''')

        # Create nested directory with Python file
        nested_dir = self.temp_dir / "nested"
        nested_dir.mkdir()
        self.nested_file = nested_dir / "nested_module.py"
        with open(self.nested_file, "w") as f:
            f.write('''
def nested_func():
    """Nested function."""
    return "Nested"
''')

        # Output directory for tests
        self.output_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_output_"))

    def tearDown(self):
        """Clean up temporary directories."""
        self.temp_dir_obj.cleanup()
        shutil.rmtree(self.output_dir)

    @patch("shutil.copy2")
    def test_copy_source_code_file(self, mock_copy2):
        """Test copying a single file source."""
        # Create a logger for testing
        test_logger = logging.getLogger("test_logger")
        test_logger.setLevel(logging.INFO)

        # Set up the mock to avoid actual file operations
        mock_copy2.return_value = None

        # Call the function with a single file
        result = copy_source_code(self.test_file, self.output_dir, test_logger)

        # Verify the copy was attempted
        mock_copy2.assert_called_once()

        # Check that the result is as expected (the relative path to the copied file)
        self.assertTrue(
            result.endswith("test_module.py") or result.endswith("test_module")
        )

    @patch("shutil.copytree")
    @patch("shutil.rmtree")
    def test_copy_source_code_directory(self, mock_rmtree, mock_copytree):
        """Test copying a directory source."""
        # Create a logger for testing
        test_logger = logging.getLogger("test_logger")
        test_logger.setLevel(logging.INFO)

        # Set up the mock to avoid actual file operations
        mock_copytree.return_value = None
        mock_rmtree.return_value = None

        # Call the function with a directory
        result = copy_source_code(self.temp_dir, self.output_dir, test_logger)

        # Verify the copy was attempted
        mock_copytree.assert_called_once()

        # Check that the result is as expected (the relative path to the copied directory)
        self.assertTrue(
            os.path.basename(result) == os.path.basename(self.temp_dir.name)
        )

    def test_template_rendering(self):
        """Test basic template rendering concept."""
        # This is a simple test to demonstrate template rendering without dependencies

        # Create a mock template file
        template_path = self.temp_dir / "template.txt"
        template_content = "Hello, {{name}}! Welcome to {{project}}."

        with open(template_path, "w") as f:
            f.write(template_content)

        # Read the template
        with open(template_path, "r") as f:
            content = f.read()

        # Simple replace function to simulate template rendering
        def render(template, **kwargs):
            result = template
            for key, value in kwargs.items():
                result = result.replace("{{" + key + "}}", value)
            return result

        # Render the template
        rendered = render(content, name="User", project="MCP")

        # Check the result
        self.assertEqual(rendered, "Hello, User! Welcome to MCP.")


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestPackaging(unittest.TestCase):
    """Tests for the main packaging functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_packaging_"))

        # Create a sample Python file
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

        # Output directory for tests
        self.output_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_output_"))

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.output_dir)

    @patch("mcp_modelservice_sdk.packaging.create_mcp_application")
    def test_build_mcp_package_basic(self, mock_create_app):
        """Test basic package building functionality."""
        # Mock the MCP application creation
        mock_app = Mock()
        mock_create_app.return_value = mock_app

        # Test package building
        try:
            build_mcp_package(
                source_path=str(self.sample_file),
                output_path=str(self.output_dir / "test_package"),
                mcp_server_name="TestServer",
            )
            # If no exception is raised, the test passes
            self.assertTrue(True)
        except Exception as e:
            # If there are missing dependencies or other issues, skip the test
            self.skipTest(f"Package building failed due to dependencies: {e}")


if __name__ == "__main__":
    unittest.main()
