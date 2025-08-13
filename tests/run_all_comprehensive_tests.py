#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner

This script runs all comprehensive regression tests for Excel processing functionality.

Test Coverage:
1. 360 Energy Excel file - Empty trailing filtering and complex table structures
2. Lendflow Balance Sheet - Financial statement layout with section headers

Usage:
    python run_all_comprehensive_tests.py              # Run all tests
    python run_all_comprehensive_tests.py --verbose    # Run with verbose output
    python run_all_comprehensive_tests.py --individual # Run tests individually
"""

import sys
import os
import argparse
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.test_360_energy_excel_processing import run_360_energy_regression_test
from tests.test_lendflow_balance_sheet import run_lendflow_regression_test


def run_all_tests(individual=False, verbose=False):
    """Run all comprehensive regression tests"""
    
    print("=" * 80)
    print("COMPREHENSIVE EXCEL PROCESSING TEST SUITE")
    print("=" * 80)
    print(f"Running all regression tests...")
    print()
    
    results = {}
    start_time = time.time()
    
    # Test 1: 360 Energy Excel Processing
    print("🧪 Test Suite 1: 360 Energy Excel Processing")
    print("-" * 60)
    try:
        results['360_energy'] = run_360_energy_regression_test()
        if individual:
            input("\nPress Enter to continue to next test...")
    except Exception as e:
        print(f"❌ Error running 360 Energy tests: {e}")
        results['360_energy'] = False
    
    print("\n")
    
    # Test 2: Lendflow Balance Sheet
    print("🧪 Test Suite 2: Lendflow Balance Sheet Processing") 
    print("-" * 60)
    try:
        results['lendflow'] = run_lendflow_regression_test()
        if individual:
            input("\nPress Enter to continue...")
    except Exception as e:
        print(f"❌ Error running Lendflow tests: {e}")
        results['lendflow'] = False
    
    # Summary
    elapsed_time = time.time() - start_time
    passed_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 80)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        description = {
            '360_energy': '360 Energy Excel (Empty trailing filtering)',
            'lendflow': 'Lendflow Balance Sheet (Financial statement layout)'
        }.get(test_name, test_name)
        
        print(f"  {status} - {description}")
    
    print(f"\nOverall: {passed_count}/{total_count} test suites passed")
    print(f"Execution time: {elapsed_time:.2f} seconds")
    
    if passed_count == total_count:
        print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("\nThis validates:")
        print("  ✓ Empty trailing row/column filtering (90%+ reduction)")
        print("  ✓ Financial statement section header handling")
        print("  ✓ Complex table detection across multiple file types")
        print("  ✓ Data integrity preservation")
        print("  ✓ Performance improvements")
        print("  ✓ Regression baseline compliance")
        return True
    else:
        print(f"\n💥 {total_count - passed_count} TEST SUITE(S) FAILED")
        print("\nReview the individual test results above for details.")
        return False


def main():
    parser = argparse.ArgumentParser(description='Run Comprehensive Excel Processing Tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Run with verbose output')
    parser.add_argument('--individual', '-i', action='store_true',
                       help='Pause between individual test suites')
    
    args = parser.parse_args()
    
    success = run_all_tests(individual=args.individual, verbose=args.verbose)
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)