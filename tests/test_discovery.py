import unittest
import pathlib
import sys
import os
import logging
import tempfile
import shutil

# Configure logging for tests
logging.basicConfig(level=logging.ERROR)

# Ensure the src directory is discoverable for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src"))

try:
    from mcp_modelservice_sdk.discovery import discover_py_files, discover_functions

    imports_successful = True
except ImportError:
    print(
        "Could not import from mcp_modelservice_sdk.discovery. Ensure package is installed or PYTHONPATH is correct."
    )
    imports_successful = False


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestDiscoveryWithSamplePackage(unittest.TestCase):
    """Tests for the discovery module using the sample package files."""

    def setUp(self):
        """Set up test environment with paths to sample files."""
        # Get the path to the tests directory
        self.test_dir = pathlib.Path(__file__).parent.resolve()
        self.sample_tools_path = self.test_dir / "sample_tools.py"

    def test_discover_py_files_single_file(self):
        """Test discovering a single Python file."""
        result = discover_py_files(str(self.sample_tools_path))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], self.sample_tools_path)

    def test_discover_py_files_directory(self):
        """Test discovering Python files in a directory."""
        result = discover_py_files(str(self.test_dir))
        # Should find at least sample_tools.py and test files
        self.assertGreaterEqual(len(result), 2)
        self.assertIn(self.sample_tools_path, result)

    def test_discover_functions_all(self):
        """Test discovering all functions in a file."""
        funcs = discover_functions([self.sample_tools_path])
        self.assertEqual(len(funcs), 3)  # add_numbers, greet_user, calculate_area
        func_names = sorted([f_info[1] for f_info in funcs])
        self.assertListEqual(
            func_names, sorted(["add_numbers", "greet_user", "calculate_area"])
        )

    def test_discover_functions_specific(self):
        """Test discovering specific functions in a file."""
        funcs = discover_functions(
            [self.sample_tools_path],
            target_function_names=["add_numbers", "greet_user"],
        )
        self.assertEqual(len(funcs), 2)
        func_names = sorted([f_info[1] for f_info in funcs])
        self.assertListEqual(func_names, sorted(["add_numbers", "greet_user"]))

    def test_discover_nonexistent_functions(self):
        """Test discovering functions that don't exist."""
        funcs = discover_functions(
            [self.sample_tools_path], target_function_names=["nonexistent_function"]
        )
        self.assertEqual(len(funcs), 0)


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestDiscoveryWithTempFiles(unittest.TestCase):
    """Tests for the discovery module using temporary files and directories."""

    def setUp(self):
        """Create temporary directory structure for testing."""
        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_discovery_"))

        # Create a simple Python file
        self.py_file = self.temp_dir / "test_module.py"
        with open(self.py_file, "w") as f:
            f.write('''
def test_func(x: int) -> int:
    """Test function."""
    return x * 2

def another_func(y: str) -> str:
    """Another test function."""
    return f"Hello {y}"

_private_func = lambda: None  # This should be skipped
''')

        # Create a non-Python file
        self.txt_file = self.temp_dir / "not_python.txt"
        with open(self.txt_file, "w") as f:
            f.write("This is not a Python file")

        # Create a nested directory with Python files
        self.nested_dir = self.temp_dir / "nested"
        self.nested_dir.mkdir()

        self.nested_py_file = self.nested_dir / "nested_module.py"
        with open(self.nested_py_file, "w") as f:
            f.write('''
def nested_func(z: float) -> float:
    """Nested function."""
    return z + 1.0
''')

        # Create a file with syntax error
        self.error_file = self.temp_dir / "error_module.py"
        with open(self.error_file, "w") as f:
            f.write('''
def broken_func()
    """This has a syntax error."""
    return "broken"
''')

        # Create a file with imported functions
        self.import_file = self.temp_dir / "import_module.py"
        with open(self.import_file, "w") as f:
            f.write('''
import os
from pathlib import Path

def local_func() -> str:
    """Local function."""
    return "local"

# These should not be discovered as they're imported
path_func = Path
os_func = os.path.join
''')

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_discover_py_files_with_temp_files(self):
        """Test discovering Python files in temporary directory."""
        result = discover_py_files(str(self.temp_dir))
        self.assertEqual(len(result), 4)  # 3 Python files + 1 in nested dir

        # Convert to strings for easier comparison
        result_paths = [str(p) for p in result]
        self.assertIn(str(self.py_file), result_paths)
        self.assertIn(str(self.nested_py_file), result_paths)
        self.assertIn(str(self.error_file), result_paths)
        self.assertIn(str(self.import_file), result_paths)
        self.assertNotIn(str(self.txt_file), result_paths)

    def test_discover_functions_with_temp_files(self):
        """Test discovering functions in temporary Python files."""
        result = discover_functions([self.py_file])
        self.assertEqual(
            len(result), 2
        )  # test_func and another_func, not _private_func

    def test_discover_functions_with_imports(self):
        """Test discovering functions in files with imports."""
        result = discover_functions([self.import_file])
        # Should only find local_func, not imported functions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "local_func")

    def test_discover_functions_with_error_file(self):
        """Test discovering functions in files with syntax errors."""
        # Should handle syntax errors gracefully
        result = discover_functions([self.error_file])
        self.assertEqual(len(result), 0)

    def test_non_existent_path(self):
        """Test handling of non-existent paths."""
        with self.assertRaises(FileNotFoundError):
            discover_py_files("/non/existent/path")

    def test_path_not_file_or_directory(self):
        """Test handling of paths that are neither files nor directories."""
        # This test might be platform-specific, so we'll skip it for now
        pass


if __name__ == "__main__":
    unittest.main()
