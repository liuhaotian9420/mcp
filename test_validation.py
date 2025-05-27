#!/usr/bin/env python3
"""Test script to verify the new CLI options and validation logic."""

import sys
import os
sys.path.insert(0, '.')

from mcp_modelservice_sdk.cli import app

def test_validation():
    """Test that event store + JSON response mode raises an error."""
    print("Testing validation: event store + JSON response should fail...")
    
    try:
        # This should fail with validation error
        app(['--source-path', 'test_new_options.py', '--json-response', '--enable-event-store', 'run', '--help'])
        print("ERROR: Validation should have failed!")
        return False
    except SystemExit as e:
        if e.code == 1:
            print("SUCCESS: Validation correctly prevented invalid combination")
            return True
        else:
            print(f"ERROR: Unexpected exit code: {e.code}")
            return False

def test_valid_combinations():
    """Test valid combinations work."""
    print("\nTesting valid combinations...")
    
    # Test 1: Stateful + SSE + Event Store (should work)
    try:
        print("Testing: Stateful + SSE + Event Store...")
        app(['--source-path', 'test_new_options.py', '--enable-event-store', 'run', '--help'])
        print("SUCCESS: Stateful + SSE + Event Store works")
    except SystemExit as e:
        if e.code != 0:
            print(f"ERROR: Valid combination failed with exit code: {e.code}")
            return False
    
    # Test 2: Stateful + JSON (should work)
    try:
        print("Testing: Stateful + JSON...")
        app(['--source-path', 'test_new_options.py', '--json-response', 'run', '--help'])
        print("SUCCESS: Stateful + JSON works")
    except SystemExit as e:
        if e.code != 0:
            print(f"ERROR: Valid combination failed with exit code: {e.code}")
            return False
    
    # Test 3: Stateless + JSON (should work)
    try:
        print("Testing: Stateless + JSON...")
        app(['--source-path', 'test_new_options.py', '--stateless-http', '--json-response', 'run', '--help'])
        print("SUCCESS: Stateless + JSON works")
    except SystemExit as e:
        if e.code != 0:
            print(f"ERROR: Valid combination failed with exit code: {e.code}")
            return False
    
    return True

if __name__ == "__main__":
    print("Testing new CLI options and validation logic...\n")
    
    # Test validation
    validation_ok = test_validation()
    
    # Test valid combinations
    valid_ok = test_valid_combinations()
    
    if validation_ok and valid_ok:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 