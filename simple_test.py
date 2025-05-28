import sys

sys.path.insert(0, ".")

from mcpy_cli.cli import app

print("Testing packaging with new options...")
try:
    app(
        [
            "--source-path",
            "test_new_options.py",
            "--json-response",
            "--stateless-http",
            "package",
            "--package-name",
            "test_package",
            "--help",
        ]
    )
except SystemExit as e:
    print(f"Exit code: {e.code}")
except Exception as e:
    print(f"Exception: {e}")
