import unittest
import os
import sys
import tempfile
import pathlib
import shutil
from typer.testing import CliRunner

# Ensure the src directory is discoverable for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src"))

try:
    from mcpy_cli.cli.main import app as cli_app

    imports_successful = True
except ImportError as e:
    print(f"Could not import CLI modules: {e}. Tests will be skipped.")
    imports_successful = False


@unittest.skipIf(not imports_successful, "Required modules could not be imported")
class TestCLICommands(unittest.TestCase):
    """Tests for the CLI commands."""

    def setUp(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_cli_"))

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

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def test_cli_help(self):
        """Test that CLI help works."""
        result = self.runner.invoke(cli_app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Usage:", result.output)


if __name__ == "__main__":
    unittest.main()
