#!/usr/bin/env python3
"""Test runner for jetson-monitor."""

import sys
import os
import unittest
import argparse

def run_tests(verbose=False, pattern=None):
    """Run the test suite."""
    # Add the current directory to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    if pattern:
        loader.testNamePatterns = [pattern]
    
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """Main function for the test runner."""
    parser = argparse.ArgumentParser(description='Run tests for jetson-monitor')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Verbose output')
    parser.add_argument('-p', '--pattern', type=str,
                       help='Pattern to match test names')
    parser.add_argument('--coverage', action='store_true',
                       help='Run with coverage report (requires coverage package)')
    
    args = parser.parse_args()
    
    if args.coverage:
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()
        except ImportError:
            print("Coverage package not found. Install with: pip install coverage")
            return 1
    
    success = run_tests(verbose=args.verbose, pattern=args.pattern)
    
    if args.coverage:
        try:
            cov.stop()
            cov.save()
            print("\nCoverage Report:")
            cov.report()
            cov.html_report(directory='htmlcov')
            print("HTML coverage report generated in htmlcov/")
        except NameError:
            pass
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
