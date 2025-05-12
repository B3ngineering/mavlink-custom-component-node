#!/usr/bin/env python3

import unittest
import sys
import os
import logging

# Ensure consistent test environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable logging during tests
logging.disable(logging.CRITICAL)

def run_tests():
    """Run all tests in the tests directory."""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 