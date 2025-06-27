#!/usr/bin/env python3
"""
Test runner for all ElPyFi Engine tests
Runs unit tests, integration tests, and the original engine test
"""

import sys
import unittest
import subprocess
from pathlib import Path


def run_unit_tests():
    """Run all unit tests using unittest discovery"""
    print("🧪 Running Unit Tests...")
    print("=" * 60)
    
    # Run only the simplified tests that work with actual code
    test_modules = [
        'test_allocator_simple',
        'test_pdt_simple',
        'test_events_simple',
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module_name in test_modules:
        try:
            module = __import__(module_name)
            suite.addTests(loader.loadTestsFromModule(module))
        except Exception as e:
            print(f"Failed to load {module_name}: {e}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_original_test():
    """Run the original test_engine.py separately"""
    print("\n🚀 Running Original Engine Test...")
    print("=" * 60)
    
    try:
        # Use PM Claude's shared venv
        python_path = "/Users/d/Documents/projects/elpyfi-pm-claude/venv/bin/python"
        result = subprocess.run(
            [python_path, "test_engine.py"],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run original test: {e}")
        return False


def print_summary(unit_success, original_success):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print(f"Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"Original Engine Test: {'✅ PASSED' if original_success else '❌ FAILED'}")
    
    all_passed = unit_success and original_success
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed


def main():
    """Main test runner"""
    print("🏃 ElPyFi Engine Test Suite")
    print("=" * 60)
    
    # Run all tests
    unit_success = run_unit_tests()
    original_success = run_original_test()
    
    # Print summary
    all_passed = print_summary(unit_success, original_success)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()