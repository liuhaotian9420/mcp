"""
Test script to verify CLI functionality with event store options.

This script demonstrates how to use the CLI with the new event store options.
"""

import subprocess
import sys
import tempfile
from pathlib import Path


def create_test_functions():
    """Create a temporary directory with test functions."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create a simple test function file
    test_file = temp_dir / "test_functions.py"
    test_file.write_text('''
"""Test functions for CLI event store testing."""

def greet(name: str) -> str:
    """Greet someone by name.
    
    Args:
        name: The name of the person to greet
        
    Returns:
        A greeting message
    """
    return f"Hello, {name}!"

def add_numbers(a: int, b: int) -> int:
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The sum of a and b
    """
    return a + b
''')

    return temp_dir


def test_cli_help():
    """Test that the CLI shows help with event store options."""
    print("Testing CLI help...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mcpy_cli.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✅ CLI help command succeeded")
            if "--enable-event-store" in result.stdout:
                print("✅ Event store option found in help")
            else:
                print("❌ Event store option not found in help")
                print("Help output:", result.stdout[:500])
        else:
            print(f"❌ CLI help failed: {result.stderr}")

    except Exception as e:
        print(f"❌ Error testing CLI help: {e}")


def test_cli_with_event_store():
    """Test running the CLI with event store enabled."""
    print("\nTesting CLI with event store...")

    # Create test functions
    temp_dir = create_test_functions()

    try:
        # Test the CLI command with event store enabled
        cmd = [
            sys.executable,
            "-m",
            "mcpy_cli.cli",
            "--source-path",
            str(temp_dir),
            "--enable-event-store",
            "--event-store-path",
            str(temp_dir / "test_events.db"),
            "run",
            "--host",
            "127.0.0.1",
            "--port",
            "8082",
        ]

        print(f"Running command: {' '.join(cmd)}")

        # Start the process but don't wait for it to complete
        # (since it would run indefinitely)
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Wait a few seconds to see if it starts successfully
        import time

        time.sleep(3)

        # Check if process is still running (good sign)
        if process.poll() is None:
            print("✅ CLI started successfully with event store")
            process.terminate()
            process.wait(timeout=5)
        else:
            # Process exited, check why
            stdout, stderr = process.communicate()
            print("❌ CLI exited unexpectedly")
            print(f"Return code: {process.returncode}")
            print(f"Stdout: {stdout}")
            print(f"Stderr: {stderr}")

    except Exception as e:
        print(f"❌ Error testing CLI with event store: {e}")
    finally:
        # Clean up
        import shutil

        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"❌ Error cleaning up: {e}")


def main():
    """Run all CLI tests."""
    print("🧪 Testing CLI with Event Store Options")
    print("=" * 50)

    test_cli_help()
    test_cli_with_event_store()

    print("\n✅ CLI testing completed!")


if __name__ == "__main__":
    main()
