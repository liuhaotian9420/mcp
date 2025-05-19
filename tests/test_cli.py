import unittest
from unittest.mock import patch, MagicMock
import tempfile
import pathlib
import shutil

from typer.testing import CliRunner

# Assuming the tests directory is at the same level as the src directory
# or the package is installed.
# Ensure mcp_modelservice_sdk.cli can be imported.
try:
    from mcp_modelservice_sdk.cli import (
        app as cli_app,
    )  # 'app' is the Typer instance in cli.py
    # Also import core elements that might be checked or mocked if CLI calls them directly
    # from mcp_modelservice_sdk.src.core import TransformationError
except ImportError as e:
    print(
        f"CRITICAL: Could not import from mcp_modelservice_sdk.cli. Ensure package is installed or PYTHONPATH is correct. Error: {e}"
    )
    # If your structure is different, you might need to adjust sys.path here:
    # import os
    # SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # sys.path.append(os.path.dirname(SCRIPT_DIR)) # Add parent of tests dir (e.g. project root)
    # from mcp_modelservice_sdk.cli import app as cli_app
    raise

runner = CliRunner()


class TestCliRunCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_cli_sdk_"))
        self.dummy_source_file = self.test_dir / "sample_funcs.py"
        with open(self.dummy_source_file, "w") as f:
            f.write("""
def a_func(x: int) -> int:
    return x * 2
""")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("mcp_modelservice_sdk.cli.uvicorn.run")
    @patch("mcp_modelservice_sdk.cli.create_mcp_application")
    def test_run_successful_minimum_args(self, mock_create_app, mock_uvicorn_run):
        mock_starlette_app = MagicMock()
        mock_create_app.return_value = mock_starlette_app

        result = runner.invoke(
            cli_app, ["run", "--source-path", str(self.dummy_source_file)]
        )

        self.assertEqual(
            result.exit_code, 0, msg=f"CLI failed with: {result.stdout}{result.stderr}"
        )
        mock_create_app.assert_called_once()
        # Check some default values were passed to create_mcp_application
        args, kwargs = mock_create_app.call_args
        self.assertEqual(kwargs["source_path_str"], str(self.dummy_source_file))
        self.assertEqual(kwargs["mcp_server_name"], "MCPModelService")  # Default
        self.assertTrue(kwargs["cors_enabled"])  # Default
        self.assertEqual(kwargs["cors_allow_origins"], ["*"])  # Default

        mock_uvicorn_run.assert_called_once_with(
            mock_starlette_app,
            host="0.0.0.0",  # Default due to mw_service=True by default
            port=8080,  # Default due to mw_service=True by default
            log_level="info",
            reload=False,
            workers=None,
        )

    @patch("mcp_modelservice_sdk.cli.uvicorn.run")
    @patch("mcp_modelservice_sdk.cli.create_mcp_application")
    def test_run_with_custom_params(self, mock_create_app, mock_uvicorn_run):
        mock_starlette_app = MagicMock()
        mock_create_app.return_value = mock_starlette_app

        result = runner.invoke(
            cli_app,
            [
                "run",
                "--source-path",
                str(self.dummy_source_file),
                "--host",
                "192.168.1.100",
                "--port",
                "9090",
                "--log-level",
                "debug",
                "--functions",
                "a_func,b_func",  # Comma-separated
                "--mcp-name",
                "MyTestService",
                "--server-root",
                "/api",
                "--mcp-base",
                "/service",
                "--no-mw-service",  # Explicitly disable mw_service to use provided host/port
                "--reload",
                "--workers",
                "2",
                "--cors-allow-origins",
                "http://localhost:3000,http://example.com",
            ],
        )
        self.assertEqual(
            result.exit_code, 0, msg=f"CLI failed with: {result.stdout}{result.stderr}"
        )

        mock_create_app.assert_called_once()
        args, kwargs = mock_create_app.call_args
        self.assertEqual(kwargs["source_path_str"], str(self.dummy_source_file))
        self.assertEqual(kwargs["target_function_names"], ["a_func", "b_func"])
        self.assertEqual(kwargs["mcp_server_name"], "MyTestService")
        self.assertEqual(kwargs["mcp_server_root_path"], "/api")
        self.assertEqual(kwargs["mcp_service_base_path"], "/service")
        self.assertEqual(kwargs["log_level"], "debug")
        self.assertEqual(
            kwargs["cors_allow_origins"],
            ["http://localhost:3000", "http://example.com"],
        )

        mock_uvicorn_run.assert_called_once_with(
            mock_starlette_app,
            host="192.168.1.100",
            port=9090,
            log_level="debug",
            reload=True,
            workers=2,
        )

    @patch("mcp_modelservice_sdk.cli.uvicorn.run")
    @patch("mcp_modelservice_sdk.cli.create_mcp_application")
    def test_run_mw_service_override(self, mock_create_app, mock_uvicorn_run):
        mock_create_app.return_value = MagicMock()
        # mw_service is true by default. If host/port are also provided, they should override mw_service defaults.
        result = runner.invoke(
            cli_app,
            [
                "run",
                "--source-path",
                str(self.dummy_source_file),
                "--host",
                "123.0.0.1",
                "--port",
                "1234",
                # mw_service is implicitly True
            ],
        )
        self.assertEqual(
            result.exit_code, 0, msg=f"CLI failed with: {result.stdout}{result.stderr}"
        )
        _, kwargs = mock_uvicorn_run.call_args
        self.assertEqual(kwargs["host"], "123.0.0.1")
        self.assertEqual(kwargs["port"], 1234)

    @patch("mcp_modelservice_sdk.cli.create_mcp_application")
    def test_run_transformation_error(self, mock_create_app):
        # Import TransformationError locally for this test if not globally available
        from mcp_modelservice_sdk.src.core import TransformationError

        mock_create_app.side_effect = TransformationError("Test transformation failed")

        result = runner.invoke(
            cli_app, ["run", "--source-path", str(self.dummy_source_file)]
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(
            "Failed to create MCP application: Test transformation failed",
            result.stdout,
        )
        self.assertIn(
            "Please check the source path and function definitions.", result.stdout
        )

    @patch("mcp_modelservice_sdk.cli.create_mcp_application")
    def test_run_file_not_found_error_from_core(self, mock_create_app):
        mock_create_app.side_effect = FileNotFoundError("Core says: File not there")

        result = runner.invoke(cli_app, ["run", "--source-path", "nonexistent/path.py"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Error: Core says: File not there", result.stdout)
        self.assertIn("Please ensure the source path is correct.", result.stdout)

    def test_run_invalid_source_path_cli_level(self):
        # This test checks if Typer/CLI itself catches a bad path if not a specific FileNotFoundError from core
        # However, our `source_path` is just a string to Typer; validation happens in `core`.
        # So, this mainly tests if the command runs and then fails as expected via core's error handling.
        # To test Typer's own path validation, you'd use `typer.Path(exists=True)`.
        # For now, we rely on core.py to raise FileNotFoundError.

        # We expect the create_mcp_application to not be called if path doesn't exist
        # and the error to be handled. Our core.py raises FileNotFoundError early.
        with patch(
            "mcp_modelservice_sdk.cli.create_mcp_application"
        ) as mock_create_app:
            mock_create_app.side_effect = FileNotFoundError("Path does not exist")
            result = runner.invoke(
                cli_app, ["run", "--source-path", "/tmp/nonexistent123.py"]
            )
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("Error: Path does not exist", result.stdout)

    @patch("mcp_modelservice_sdk.cli.uvicorn.run")
    @patch("mcp_modelservice_sdk.cli.create_mcp_application")
    def test_run_functions_single_item_in_list_no_comma(
        self, mock_create_app, mock_uvicorn_run
    ):
        mock_create_app.return_value = MagicMock()
        result = runner.invoke(
            cli_app,
            [
                "run",
                "--source-path",
                str(self.dummy_source_file),
                "--functions",
                "a_func",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        _, kwargs = mock_create_app.call_args
        self.assertEqual(kwargs["target_function_names"], ["a_func"])

    @patch("mcp_modelservice_sdk.cli.uvicorn.run")
    @patch("mcp_modelservice_sdk.cli.create_mcp_application")
    def test_run_functions_multiple_flags(self, mock_create_app, mock_uvicorn_run):
        mock_create_app.return_value = MagicMock()
        result = runner.invoke(
            cli_app,
            [
                "run",
                "--source-path",
                str(self.dummy_source_file),
                "--functions",
                "a_func",
                "--functions",
                "b_func",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        _, kwargs = mock_create_app.call_args
        self.assertEqual(kwargs["target_function_names"], ["a_func", "b_func"])


if __name__ == "__main__":
    unittest.main()
