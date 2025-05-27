import unittest
import pathlib
import sys
import os
import tempfile
import shutil

# Ensure the src directory is discoverable for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)
# Also add the src directory to the path
sys.path.append(os.path.join(project_root, "src"))

# Import error handling
try:
    from mcp_modelservice_sdk.src.discovery import discover_py_files, discover_functions

    imports_successful = True
except ImportError:
    print("Could not import required modules. Tests will be skipped.")
    imports_successful = False


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestMultiMountBasic(unittest.TestCase):
    """Basic tests for multi-mount architecture functionality."""

    def setUp(self):
        # Create a temporary directory for our test package
        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_mcp_multi_mount_"))

        # Create a simple module_a.py
        with open(self.temp_dir / "module_a.py", "w") as f:
            f.write("""
def tool_a1(x: int) -> int:
    \"\"\"Tool A1 in module A.\"\"\"
    return x + 1

def tool_a2(text: str) -> str:
    \"\"\"Tool A2 in module A.\"\"\"
    return text.upper()
""")

        # Create nested directory with its own module
        nested_dir = self.temp_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "__init__.py").touch()

        with open(nested_dir / "module_b.py", "w") as f:
            f.write("""
def tool_b1(x: int, y: int) -> int:
    \"\"\"Tool B1 in module B.\"\"\"
    return x * y
""")

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_discover_py_files(self):
        """Test discovering Python files in directories with nested structure."""
        result = discover_py_files(str(self.temp_dir))
        self.assertEqual(
            len(result), 3
        )  # module_a.py, nested/__init__.py, nested/module_b.py

        # Convert paths to strings for easier comparison
        result_paths = [str(p) for p in result]
        self.assertTrue(any("module_a.py" in p for p in result_paths))
        self.assertTrue(
            any("nested/module_b.py" in p for p in result_paths)
            or any("nested\\module_b.py" in p for p in result_paths)
        )  # Handle Windows paths
        self.assertTrue(any("__init__.py" in p for p in result_paths))

    def test_discover_functions(self):
        """Test discovering functions across modules."""
        # First get the files
        py_files = discover_py_files(str(self.temp_dir))

        # Then discover functions in those files
        functions = discover_functions(py_files)

        # We should have 3 functions total
        self.assertEqual(len(functions), 3)

        # Extract just the function names for easier checking
        function_names = [func[1] for func in functions]
        self.assertIn("tool_a1", function_names)
        self.assertIn("tool_a2", function_names)
        self.assertIn("tool_b1", function_names)

    @unittest.skip("This test requires FastMCP which is an external dependency")
    def test_multi_mount_architecture(self):
        """Test the multi-mount architecture with directory-based routing."""
        # This test is skipped because it requires the external FastMCP package
        pass


if __name__ == "__main__":
    unittest.main()
