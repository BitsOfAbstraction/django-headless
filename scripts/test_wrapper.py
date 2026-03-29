#!/usr/bin/env python
"""
Wrapper script for pytest to handle command line arguments properly.
"""

import sys
from pytest import main


def main_test():
    """Run pytest with default arguments"""
    sys.exit(main([]))


def main_test_verbose():
    """Run pytest with verbose output"""
    sys.exit(main(["-v"]))


def main_test_cov():
    """Run pytest with coverage"""
    # Import coverage modules here to avoid import errors if coverage isn't installed
    try:
        import coverage
        sys.exit(main(["--cov=headless", "--cov-report=term"]))
    except ImportError:
        print("Coverage module not available. Running tests without coverage.")
        sys.exit(main([]))


if __name__ == "__main__":
    # For direct execution
    sys.exit(main(sys.argv[1:]))