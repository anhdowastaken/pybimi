#!/usr/bin/env python3
"""
Test runner for pybimi test suite.
Run all tests with: python -m pytest tests/ -v
Or run this file directly: python tests/test_runner.py
"""

import unittest
import sys
import os

# Add parent directory to path to import pybimi
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_tests():
    """Run all tests in the tests directory"""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())
