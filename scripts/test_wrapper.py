#!/usr/bin/env python
"""
Wrapper script for pytest to handle command line arguments properly.

This script provides test running functionality and a safe publish command
that runs tests before publishing to ensure quality.
"""

import subprocess
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


def main_build():
    """Run tests before building. Exits with error if tests fail."""
    print("🧪 Running tests before building...")

    # Run tests first
    test_result = main([])

    if test_result != 0:
        print("❌ Tests failed. Aborting build.")
        sys.exit(1)

    print("✅ All tests passed. Proceeding with build...")

    # Continue with poetry build
    try:
        result = subprocess.run(["poetry", "build"] + sys.argv[1:], check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("❌ Poetry command not found. Make sure poetry is installed and in PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during build: {e}")
        sys.exit(1)


def main_publish():
    """Run tests before publishing. Exits with error if tests fail."""
    print("🧪 Running tests before publishing...")

    # Run tests first
    test_result = main([])

    if test_result != 0:
        print("❌ Tests failed. Aborting publish.")
        sys.exit(1)

    print("✅ All tests passed. Proceeding with publish...")

    # Continue with poetry publish
    try:
        result = subprocess.run(["poetry", "publish"] + sys.argv[1:], check=False)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("❌ Poetry command not found. Make sure poetry is installed and in PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during publish: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # For direct execution
    sys.exit(main(sys.argv[1:]))
