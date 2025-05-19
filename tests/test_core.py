import unittest
from unittest.mock import patch, MagicMock
import pathlib
import tempfile
import logging
import shutil  # For cleaning up temp directories

# Ensure the src directory is discoverable for imports if tests are run from root
import sys

# Assuming the tests directory is at the same level as the src directory
# or that the package is installed in a way that mcp_modelservice_sdk can be imported.
# For robust path handling, one might adjust sys.path here if needed, e.g.:
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.dirname(SCRIPT_DIR))

try:
    from mcp_modelservice_sdk.src.core import (
        discover_py_files,
        discover_functions,
        _validate_and_wrap_tool,  # For more direct testing if needed, though typically tested via create_mcp_application
        create_mcp_application,
        TransformationError,
        package_mcp_application,  # Added import
    )
    from fastmcp import FastMCP
except ImportError:
    # This might happen if the package isn't installed correctly or PYTHONPATH isn't set
    # For CI/CD or local testing, ensure your package structure allows this import
    # Example: run tests with `python -m unittest discover tests` from the root of your project
    # or ensure your IDE sets the project root correctly.
    print(
        "CRITICAL: Could not import from mcp_modelservice_sdk.src.core. Ensure package is installed or PYTHONPATH is correct."
    )
    # Fallback for some structures, adjust as necessary
    # from src.mcp_modelservice_sdk.src.core import ...
    raise

# Disable logging for most tests to keep output clean, can be enabled for debugging
logging.disable(logging.CRITICAL)
# To enable logging for debugging a specific test, re-enable it within that test method:
# logging.disable(logging.NOTSET)


class TestCoreDiscoverPyFiles(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_core_sdk_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_discover_single_py_file(self):
        file_path = self.test_dir / "sample.py"
        file_path.touch()
        result = discover_py_files(str(file_path))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], file_path)

    def test_discover_no_py_file_extension(self):
        file_path = self.test_dir / "sample.txt"
        file_path.touch()
        with self.assertLogs(level="WARNING") as log:
            result = discover_py_files(str(file_path))
            self.assertEqual(len(result), 0)
        self.assertIn(
            f"Source file is not a Python file, skipping: {file_path}", log.output[0]
        )

    def test_discover_py_files_in_directory(self):
        (self.test_dir / "file1.py").touch()
        (self.test_dir / "file2.py").touch()
        (self.test_dir / "file3.txt").touch()
        sub_dir = self.test_dir / "sub"
        sub_dir.mkdir()
        (sub_dir / "file4.py").touch()

        result = discover_py_files(str(self.test_dir))
        self.assertEqual(len(result), 3)
        self.assertIn(self.test_dir / "file1.py", result)
        self.assertIn(self.test_dir / "file2.py", result)
        self.assertIn(sub_dir / "file4.py", result)

    def test_discover_no_py_files_in_directory(self):
        (self.test_dir / "file1.txt").touch()
        (self.test_dir / "file2.md").touch()
        with self.assertLogs(level="WARNING") as log:
            result = discover_py_files(str(self.test_dir))
            self.assertEqual(len(result), 0)
        self.assertIn(f"No Python files found in: {self.test_dir}", log.output[0])

    def test_discover_empty_directory(self):
        with self.assertLogs(level="WARNING") as log:
            result = discover_py_files(str(self.test_dir))
            self.assertEqual(len(result), 0)
        self.assertIn(f"No Python files found in: {self.test_dir}", log.output[0])

    def test_path_not_found(self):
        with self.assertRaises(FileNotFoundError):
            discover_py_files(str(self.test_dir / "nonexistent"))

    def test_path_is_not_file_or_dir(self):
        # This case is hard to simulate safely without OS-specific calls for special files.
        # We rely on pathlib.Path.is_file() and is_dir() correctly identifying types.
        # If a path exists but is neither (e.g. a broken symlink, pipe), ValueError should be raised.
        # For now, this test is conceptual.
        pass


class TestCoreDiscoverFunctions(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_func_disc_"))
        self.module1_path = self.test_dir / "module1.py"
        with open(self.module1_path, "w") as f:
            f.write(
                "\n".join(
                    [
                        "def func_a():",
                        "    pass",
                        "def func_b(x: int):",
                        "    pass",
                        "class MyClass:",
                        "    def method(self):",
                        "        pass",
                        "_private_func = lambda: None",
                    ]
                )
            )
        self.module2_path = self.test_dir / "module2.py"
        with open(self.module2_path, "w") as f:
            f.write(
                "\n".join(
                    [
                        "from module1 import func_a",
                        "def func_c():",
                        "    pass",
                        "imported_func_a = func_a",
                    ]
                )
            )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_discover_all_functions_single_file(self):
        funcs = discover_functions([self.module1_path])
        self.assertEqual(len(funcs), 2)
        func_names = [f_info[1] for f_info in funcs]
        self.assertIn("func_a", func_names)
        self.assertIn("func_b", func_names)

    def test_discover_specific_functions_single_file(self):
        funcs = discover_functions(
            [self.module1_path], target_function_names=["func_a"]
        )
        self.assertEqual(len(funcs), 1)
        self.assertEqual(funcs[0][1], "func_a")

    def test_discover_functions_multiple_files(self):
        # Add module2.py to sys.path for its import of module1 to work during dynamic loading
        # This is a bit tricky as dynamic loading might not always resolve sibling modules easily.
        # A better way is to ensure modules are structured as a package if they have interdependencies.
        # For this test, we assume _load_module_from_path works for simple cases.
        # If module1 is not found by module2, func_c will still be found.
        original_sys_path = sys.path[:]
        sys.path.insert(0, str(self.test_dir))
        try:
            funcs = discover_functions([self.module1_path, self.module2_path])
        finally:
            sys.path = original_sys_path

        func_names = sorted([f_info[1] for f_info in funcs])
        # Expected: func_a, func_b from module1, func_c from module2
        self.assertEqual(len(funcs), 3)
        self.assertListEqual(func_names, sorted(["func_a", "func_b", "func_c"]))

    def test_discover_non_existent_function(self):
        with self.assertLogs(level="WARNING") as log:
            funcs = discover_functions(
                [self.module1_path], target_function_names=["non_existent_func"]
            )
            self.assertEqual(len(funcs), 0)
        self.assertIn(
            "Could not find the following specified functions: ['non_existent_func']",
            log.output[0],
        )

    def test_discover_no_functions_in_file(self):
        empty_module_path = self.test_dir / "empty.py"
        empty_module_path.touch()
        funcs = discover_functions([empty_module_path])
        self.assertEqual(len(funcs), 0)

    def test_file_cannot_be_loaded(self):
        invalid_module_path = self.test_dir / "invalid.py"
        with open(invalid_module_path, "w") as f:
            f.write("def func_x():\n  syntax error")  # Invalid syntax

        # The error during loading should be logged by _load_module_from_path
        with self.assertLogs(level="ERROR") as log:
            funcs = discover_functions([invalid_module_path])
            self.assertEqual(
                len(funcs), 0
            )  # No functions should be discovered from a broken module
        self.assertTrue(
            any(
                f"Failed to load module 'invalid' from '{invalid_module_path}'"
                in record
                for record in log.output
            )
        )


class TestCoreValidateAndWrapTool(unittest.TestCase):
    def setUp(self):
        self.mcp_instance = FastMCP(name="TestMCP")
        self.test_file_path = pathlib.Path("dummy/path/test_module.py")
        # Enable logging for this specific test class to capture warnings
        logging.disable(logging.NOTSET)

    def tearDown(self):
        logging.disable(logging.CRITICAL)  # Re-disable logging globally

    def test_missing_docstring(self):
        def sample_func(a):
            pass

        with self.assertLogs(
            logger="mcp_modelservice_sdk.src.core", level="WARNING"
        ) as log:
            _validate_and_wrap_tool(
                self.mcp_instance, sample_func, "sample_func", self.test_file_path
            )
        self.assertIn(
            f"Function 'sample_func' in '{self.test_file_path}' is missing a docstring.",
            log.output[0],
        )

    def test_missing_param_type_hint(self):
        def sample_func(a, b: int):
            """Docstring."""
            pass

        with self.assertLogs(
            logger="mcp_modelservice_sdk.src.core", level="WARNING"
        ) as log:
            _validate_and_wrap_tool(
                self.mcp_instance, sample_func, "sample_func", self.test_file_path
            )
        self.assertIn(
            f"Parameter 'a' in function 'sample_func' in '{self.test_file_path}' is missing a type hint.",
            log.output[0],
        )
        # Check that b is not warned for
        self.assertFalse(any("Parameter 'b'" in line for line in log.output))

    def test_missing_return_type_hint(self):
        def sample_func(a: int):
            """Docstring."""
            pass

        with self.assertLogs(
            logger="mcp_modelservice_sdk.src.core", level="WARNING"
        ) as log:
            _validate_and_wrap_tool(
                self.mcp_instance, sample_func, "sample_func", self.test_file_path
            )
        self.assertIn(
            f"Return type for function 'sample_func' in '{self.test_file_path}' is missing a type hint.",
            log.output[0],
        )

    def test_all_present(self):
        def sample_func(a: int) -> str:
            """:param a: Test param."""
            return "hello"

        # Should not log any warnings for this function
        with patch.object(
            logging.getLogger("mcp_modelservice_sdk.src.core"), "warning"
        ) as mock_warning:
            _validate_and_wrap_tool(
                self.mcp_instance, sample_func, "sample_func", self.test_file_path
            )
            mock_warning.assert_not_called()
        self.assertIn("sample_func", self.mcp_instance.tools)  # type: ignore[attr-defined]

    @patch("fastmcp.FastMCP.tool")  # Patching at the source of FastMCP class
    def test_wrapping_failure(self, mock_mcp_tool_decorator):
        # Make the decorator factory raise an exception when the decorated function is called
        mock_mcp_tool_decorator.side_effect = Exception("Wrapping Failed")

        def sample_func(a: int) -> str:
            """Doc."""
            return "hi"

        # We expect an error log, not an exception from _validate_and_wrap_tool itself
        with self.assertLogs(
            logger="mcp_modelservice_sdk.src.core", level="ERROR"
        ) as log:
            _validate_and_wrap_tool(
                self.mcp_instance, sample_func, "sample_func", self.test_file_path
            )

        self.assertTrue(
            any(
                f"Failed to wrap function 'sample_func' from '{self.test_file_path}' as an MCP tool: Wrapping Failed"
                in record
                for record in log.output
            )
        )
        self.assertNotIn("sample_func", self.mcp_instance.tools)  # type: ignore[attr-defined]


class TestCoreCreateMcpApplication(unittest.TestCase):
    def setUp(self):
        self.test_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_app_create_"))
        self.dummy_module_path = self.test_dir / "dummy_app_module.py"
        with open(self.dummy_module_path, "w") as f:
            f.write(
                "\n".join(
                    [
                        "def tool_one(x: int) -> int:",
                        "    '''Test tool one.'''",
                        "    return x * 2",
                        "def tool_two(name: str) -> str:",
                        "    '''Test tool two.'''",
                        '    return f"Hello, {name}"',
                    ]
                )
            )
        # Disable most logging to avoid clutter, create_mcp_application has its own logs
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        logging.disable(logging.CRITICAL)  # Ensure it's disabled after tests

    def test_create_app_successfully(self):
        app = create_mcp_application(str(self.dummy_module_path))
        self.assertIsNotNone(app)
        # Further checks: inspect app.routes, or FastMCP instance if it were exposed
        # For now, successful creation without error is the main check.
        # We can mock FastMCP and check if tools were added
        with patch("mcp_modelservice_sdk.src.core.FastMCP") as mock_fast_mcp_class:
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.tools = {}  # Simulate the tools attribute

            # Mock the tool decorator to actually add to our mock_mcp_instance.tools
            def mock_tool_decorator(name):
                def decorator(func):
                    mock_mcp_instance.tools[name] = func
                    return func

                return decorator

            mock_mcp_instance.tool.side_effect = mock_tool_decorator
            mock_fast_mcp_class.return_value = mock_mcp_instance

            create_mcp_application(str(self.dummy_module_path))

            self.assertIn("tool_one", mock_mcp_instance.tools)
            self.assertIn("tool_two", mock_mcp_instance.tools)
            mock_mcp_instance.http_app.assert_called_with(
                path="/mcp"
            )  # Default base path

    def test_no_py_files_found_error(self):
        with self.assertRaises(TransformationError) as cm:
            create_mcp_application(str(self.test_dir / "nonexistent_dir"))
        self.assertIn("Failed to discover Python files", str(cm.exception))

        empty_dir = self.test_dir / "empty_dir_for_test"
        empty_dir.mkdir()
        with self.assertRaises(TransformationError) as cm:
            create_mcp_application(str(empty_dir))
        self.assertIn("No Python files found to process", str(cm.exception))

    def test_no_functions_found_error(self):
        empty_py_file = self.test_dir / "empty.py"
        empty_py_file.touch()
        with self.assertRaises(TransformationError) as cm:
            create_mcp_application(str(empty_py_file))
        self.assertIn("No functions found to wrap as MCP tools", str(cm.exception))

    def test_specific_functions_not_found_error(self):
        with self.assertRaises(TransformationError) as cm:
            create_mcp_application(
                str(self.dummy_module_path), target_function_names=["non_existent_tool"]
            )
        self.assertIn(
            "Specified functions: ['non_existent_tool'] not found", str(cm.exception)
        )

    @patch("mcp_modelservice_sdk.src.core._validate_and_wrap_tool")
    def test_no_tools_registered_error(self, mock_validate_wrap):
        # Simulate _validate_and_wrap_tool not actually registering any tools
        # (e.g., if all functions failed to wrap for some reason, though FastMCP.tool itself raises on failure)
        # A more direct way is to have discover_functions return functions, but then FastMCP instance has no tools.

        with patch("mcp_modelservice_sdk.src.core.FastMCP") as mock_fast_mcp_class:
            mock_mcp_instance = MagicMock()
            mock_mcp_instance.tools = {}  # No tools registered
            mock_fast_mcp_class.return_value = mock_mcp_instance

            # Ensure discover_functions returns something, so we proceed to tool registration phase
            with patch(
                "mcp_modelservice_sdk.src.core.discover_functions"
            ) as mock_discover:

                def dummy_f():
                    pass

                mock_discover.return_value = [
                    (dummy_f, "dummy_f", self.dummy_module_path)
                ]

                with self.assertRaises(TransformationError) as cm:
                    create_mcp_application(str(self.dummy_module_path))
                self.assertIn(
                    "No tools were successfully created and registered",
                    str(cm.exception),
                )


class TestCorePackageMcpApplication(unittest.TestCase):
    def setUp(self):
        self.test_base_dir = pathlib.Path(tempfile.mkdtemp(prefix="test_package_base_"))
        self.source_dir = self.test_base_dir / "source"
        self.source_dir.mkdir()
        self.output_dir = self.test_base_dir / "output"
        # self.output_dir will be created by tests, or its non-creation/pre-existence tested

        self.dummy_module_name = "my_test_tool_module"
        self.dummy_module_file = self.source_dir / f"{self.dummy_module_name}.py"
        with open(self.dummy_module_file, "w") as f:
            f.write("""
def sample_tool(name: str) -> str:
    '''A simple tool.'''
    return f"Hello, {name}"
""")
        # Create a dummy non-python file to ensure it's not packaged directly as runnable
        (self.source_dir / "notes.txt").touch()

    def tearDown(self):
        shutil.rmtree(self.test_base_dir)
        # Ensure logging is reset if any test enables it
        logging.disable(logging.CRITICAL)

    def assert_file_contains(self, file_path: pathlib.Path, expected_content: str):
        self.assertTrue(file_path.exists(), f"{file_path} does not exist")
        with open(file_path, "r") as f:
            content = f.read()
        self.assertIn(
            expected_content, content, f"Expected content not found in {file_path}"
        )

    def assert_file_does_not_contain(
        self, file_path: pathlib.Path, unexpected_content: str
    ):
        self.assertTrue(file_path.exists(), f"{file_path} does not exist")
        with open(file_path, "r") as f:
            content = f.read()
        self.assertNotIn(
            unexpected_content, content, f"Unexpected content found in {file_path}"
        )

    def test_package_mcp_application_defaults(self):
        package_mcp_application(str(self.dummy_module_file), str(self.output_dir))

        self.assertTrue(self.output_dir.exists())
        self.assertTrue((self.output_dir / "app").exists())
        self.assertTrue(
            (self.output_dir / "app" / f"{self.dummy_module_name}.py").exists()
        )
        # Ensure non-python files from source_dir are not copied into app/
        self.assertFalse((self.output_dir / "app" / "notes.txt").exists())

        # Check main.py
        main_py_path = self.output_dir / "main.py"
        self.assert_file_contains(
            main_py_path, f"from app.{self.dummy_module_name} import"
        )  # Correct import
        self.assert_file_contains(
            main_py_path, "create_mcp_application(source_path_str=module_path_str,"
        )
        self.assert_file_contains(
            main_py_path,
            'mcp_app = create_mcp_application(source_path_str=str(module_path), mcp_server_name="MyMCPApp",',
        )
        self.assert_file_contains(
            main_py_path, 'uvicorn.run(mcp_app, host="0.0.0.0", port=8080)'
        )

        # Check Dockerfile
        dockerfile_path = self.output_dir / "Dockerfile"
        self.assert_file_contains(
            dockerfile_path, "FROM python:3.10-slim"
        )  # Default Python version
        self.assert_file_contains(dockerfile_path, "COPY ./app /app/app")
        self.assert_file_contains(
            dockerfile_path, "COPY requirements.txt /app/requirements.txt"
        )
        self.assert_file_contains(
            dockerfile_path, "RUN pip install --no-cache-dir -r /app/requirements.txt"
        )
        self.assert_file_contains(
            dockerfile_path,
            'CMD ["uvicorn", "main:mcp_app", "--host", "0.0.0.0", "--port", "8080"]',
        )

        # Check README.md
        readme_path = self.output_dir / "README.md"
        self.assert_file_contains(readme_path, "# MyMCPApp")  # Default app name
        self.assert_file_contains(readme_path, "Version: 0.1.0")  # Default version
        self.assert_file_contains(
            readme_path, f"Based on module: {self.dummy_module_name}.py"
        )

        # Check requirements.txt
        req_path = self.output_dir / "requirements.txt"
        self.assert_file_contains(req_path, "fastapi-mcp")
        self.assert_file_contains(req_path, "uvicorn")
        self.assert_file_does_not_contain(
            req_path, "requests"
        )  # example of an extra dep

    def test_package_mcp_application_custom_params(self):
        custom_app_name = "CustomTestService"
        custom_app_version = "1.2.3"
        custom_python_version = "3.9"
        extra_deps = ["requests==2.25.1", "numpy>=1.20"]

        package_mcp_application(
            str(self.dummy_module_file),
            str(self.output_dir),
            app_name=custom_app_name,
            app_version=custom_app_version,
            python_version=custom_python_version,
            extra_dependencies=extra_deps,
        )

        self.assertTrue(self.output_dir.exists())

        # Check main.py for custom app_name
        main_py_path = self.output_dir / "main.py"
        self.assert_file_contains(
            main_py_path,
            f'mcp_app = create_mcp_application(source_path_str=str(module_path), mcp_server_name="{custom_app_name}",',
        )

        # Check Dockerfile for custom Python version
        dockerfile_path = self.output_dir / "Dockerfile"
        self.assert_file_contains(
            dockerfile_path, f"FROM python:{custom_python_version}"
        )

        # Check README.md for custom name and version
        readme_path = self.output_dir / "README.md"
        self.assert_file_contains(readme_path, f"# {custom_app_name}")
        self.assert_file_contains(readme_path, f"Version: {custom_app_version}")

        # Check requirements.txt for extra dependencies
        req_path = self.output_dir / "requirements.txt"
        self.assert_file_contains(req_path, "fastapi-mcp")
        self.assert_file_contains(req_path, "uvicorn")
        self.assert_file_contains(req_path, "requests==2.25.1")
        self.assert_file_contains(req_path, "numpy>=1.20")

    def test_package_mcp_application_source_is_directory(self):
        # Test packaging when source_path is a directory
        # The core logic should copy the entire directory content (recursively for .py files)
        # For this test, we'll use self.source_dir which contains dummy_module_file and notes.txt

        # Create another python file in a sub-directory
        sub_source_dir = self.source_dir / "subdir"
        sub_source_dir.mkdir()
        sub_module_file = sub_source_dir / "another_tool.py"
        with open(sub_module_file, "w") as f:
            f.write("""
def another_sample_tool(x: int) -> int:
    return x + 1
""")

        package_mcp_application(str(self.source_dir), str(self.output_dir))

        self.assertTrue(self.output_dir.exists())
        app_folder = self.output_dir / "app"
        self.assertTrue(app_folder.exists())

        # Check that the python files are copied
        self.assertTrue((app_folder / f"{self.dummy_module_name}.py").exists())
        self.assertTrue((app_folder / "subdir" / "another_tool.py").exists())

        # Check that non-python files are NOT copied
        self.assertFalse((app_folder / "notes.txt").exists())
        self.assertFalse(
            (app_folder / "subdir" / "notes.txt").exists()
        )  # If we had one

        # main.py should refer to the source directory name as the module context
        # The template uses source_module_name_for_import which is source_path.stem
        # If source_path is a dir, its name is used.
        main_py_path = self.output_dir / "main.py"

        # The create_mcp_application inside the generated main.py will use 'app' as source_path_str
        # and its discover_py_files will find all .py files within it.
        self.assert_file_contains(
            main_py_path, "create_mcp_application(source_path_str=module_path_str,"
        )  # module_path_str is "app"
        # The import in main.py.template is for the original module_file_name and source_module_name_for_import
        # which are based on the initial source_path. This part of the template might be less relevant
        # if the source_path is a dir, as create_mcp_application(source_path_str="app") will handle discovery.
        # The current template for main.py:
        # from {{ source_module_name_for_import }} import *
        # This might need adjustment if source_path is a dir. Let's check core.py
        # core.py: source_module_name_for_import = Path(source_path).stem
        # core.py: module_file_name = Path(source_path).name
        # If source_path is a directory "source", then stem is "source", name is "source".
        # Template uses: from .app.{{ source_module_name_for_import }} import * if module_file_name else from .app import *
        # If source_path is a dir "source", module_file_name is "source" (a dir name), so it might try "from .app.source import *"
        # This will likely fail as 'source' is not a module.
        # The actual create_mcp_application call inside main.py uses `module_path_str` which points to `app` dir.
        # The current main.py.template has:
        # module_path = Path("app") / Path("{{ module_file_name }}") if "{{ module_file_name }}" else Path("app")
        # if module_path.is_dir(): module_path_str = str(Path("app"))
        # else: module_path_str = str(module_path)
        # mcp_app = create_mcp_application(source_path_str=module_path_str, ...)
        # This logic seems okay. If source_path was "source_dir", module_file_name is "source_dir".
        # module_path becomes "app/source_dir". module_path_str will be "app".
        self.assert_file_contains(
            main_py_path,
            'mcp_app = create_mcp_application(source_path_str=str(Path("app")), mcp_server_name="MyMCPApp"',
        )

    def test_package_source_not_found(self):
        non_existent_source = self.source_dir / "ghost.py"
        with self.assertRaisesRegex(FileNotFoundError, "Source path .* does not exist"):
            package_mcp_application(str(non_existent_source), str(self.output_dir))

    def test_package_output_path_is_file(self):
        self.output_dir.touch()  # Create output_dir as a file
        with self.assertRaisesRegex(ValueError, "Output path .* exists and is a file"):
            package_mcp_application(str(self.dummy_module_file), str(self.output_dir))

    def test_package_output_dir_not_empty_no_force(self):
        self.output_dir.mkdir()
        (self.output_dir / "some_file.txt").touch()
        with self.assertRaisesRegex(
            ValueError, "Output directory .* is not empty. Use --force to overwrite."
        ):
            package_mcp_application(
                str(self.dummy_module_file), str(self.output_dir), force=False
            )

    def test_package_output_dir_not_empty_with_force(self):
        self.output_dir.mkdir()
        (self.output_dir / "old_main.py").touch()  # Pre-existing file

        package_mcp_application(
            str(self.dummy_module_file), str(self.output_dir), force=True
        )

        self.assertTrue((self.output_dir / "main.py").exists())  # New main.py created
        self.assertFalse(
            (self.output_dir / "old_main.py").exists()
        )  # Old file should be gone
        self.assertTrue(
            (self.output_dir / "app" / f"{self.dummy_module_name}.py").exists()
        )

    def test_package_source_is_not_py_file_or_dir(self):
        # This tests if the source path exists but is not a .py file or a directory
        # package_mcp_application itself checks this.
        not_py_file = self.source_dir / "not_python.txt"
        not_py_file.touch()
        with self.assertRaisesRegex(
            ValueError,
            "Source path must be a Python file \\(\\.py\\) or a directory containing Python files.",
        ):
            package_mcp_application(str(not_py_file), str(self.output_dir))

    # The following tests could be added for the helper functions if they were more complex
    # or if their individual testing was deemed necessary beyond their use in package_mcp_application.
    # For now, their behavior is implicitly tested via the main packaging tests.
    # def test_copy_template_files_logic(self): ...
    # def test_generate_dockerfile_content(self): ...
    # def test_generate_readme_content(self): ...
    # def test_generate_requirements_txt_content(self): ...


# Ensure only one if __name__ == '__main__' at the very end
if __name__ == "__main__":
    unittest.main()
