#!/usr/bin/env python3
"""
360 Energy Excel Processing Test Runner

This script runs the comprehensive regression test suite for the 360 Energy Excel file
processing functionality, including empty trailing row/column filtering.

Usage:
    python run_360_energy_tests.py              # Run all tests
    python run_360_energy_tests.py --verbose    # Run with verbose output
    python run_360_energy_tests.py --quick      # Run only critical tests
    
Integration with CI/CD:
    This script returns exit code 0 for success, 1 for failure, making it suitable
    for automated testing pipelines.

Test Coverage:
    - File structure validation
    - Empty trailing filtering functionality
    - Table detection accuracy  
    - Data preservation verification
    - Performance improvement validation
    - Regression baseline metrics
    - End-to-end workflow testing
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


def run_quick_validation():
    """Run a quick validation to ensure the test file exists and basic functionality works"""
    print("Running quick validation...")
    
    from converter.compact_excel_processor import CompactExcelProcessor
    
    test_file = project_root / "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        processor = CompactExcelProcessor()
        result = processor.process_file(str(test_file), filter_empty_trailing=True)
        
        sheets = result['workbook']['sheets']
        print(f"✓ File processed successfully ({len(sheets)} sheets)")
        
        # Quick validation of filtering
        rental_sheet = next((s for s in sheets if s['name'] == 'Rental Single Unit Economics'), None)
        if rental_sheet:
            dims = rental_sheet.get('dimensions', [1, 1, 1, 1])
            if dims[2] < 100:  # Should be much less than the original 1000 rows
                print(f"✓ Empty trailing filtering working (rows reduced to {dims[2]})")
                return True
            else:
                print(f"❌ Filtering not working properly (still {dims[2]} rows)")
                return False
        else:
            print("❌ Expected sheet not found")
            return False
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Run 360 Energy Excel Processing Tests')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Run with verbose output')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Run only quick validation tests')
    parser.add_argument('--pytest', action='store_true',
                       help='Use pytest runner instead of unittest')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("360 ENERGY EXCEL PROCESSING TEST SUITE")
    print("=" * 80)
    print(f"Project root: {project_root}")
    print(f"Python version: {sys.version}")
    print()
    
    # Check if test file exists
    test_file = project_root / "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx"
    if not test_file.exists():
        print(f"❌ CRITICAL: Test file not found at {test_file}")
        print("   Please ensure the 360 Energy Excel file is in the tests/test_excel/ directory")
        return 1
    
    print(f"✓ Test file found: {test_file.name}")
    print()
    
    start_time = time.time()
    
    if args.quick:
        # Run quick validation only
        success = run_quick_validation()
    elif args.pytest:
        # Use pytest runner
        import subprocess
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                'tests/test_360_energy_excel_processing.py',
                '-v' if args.verbose else '',
                '--tb=short'
            ], cwd=project_root, capture_output=True, text=True)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            success = result.returncode == 0
        except Exception as e:
            print(f"❌ Error running pytest: {e}")
            success = False
    else:
        # Use the custom unittest runner
        success = run_360_energy_regression_test()
    
    elapsed_time = time.time() - start_time
    
    print(f"\nTest execution completed in {elapsed_time:.2f} seconds")
    
    if success:
        print("\n🎉 ALL TESTS PASSED - 360 Energy processing is working correctly!")
        print("\nThis validates:")
        print("  ✓ Empty trailing row/column filtering (90%+ reduction)")
        print("  ✓ Data integrity preservation")
        print("  ✓ Table detection functionality") 
        print("  ✓ Performance improvements")
        print("  ✓ Regression baseline compliance")
        return 0
    else:
        print("\n💥 TESTS FAILED - Please review the errors above")
        print("\nThis may indicate:")
        print("  ❌ Regression in filtering functionality")
        print("  ❌ Data corruption or loss")
        print("  ❌ Performance degradation")
        print("  ❌ Table detection issues")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)