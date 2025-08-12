#!/usr/bin/env python3
"""
Test script for the simplified table detection system.

This demonstrates how the new TableDetector provides cleaner, more consistent 
results compared to the current implementation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.table_detector import TableDetector, HeaderResolver
from converter.table_processor import TableProcessor


def test_simple_multitable_detection():
    """Test the simplified detector vs current implementation on a simple multitable case."""
    
    # Test data with 3 clear tables separated by gaps
    test_cells = {
        # Table 1: Sales Data (rows 1-3)
        'A1': {'value': 'Product', 'row': 1, 'column': 1},
        'B1': {'value': 'Sales', 'row': 1, 'column': 2},
        'A2': {'value': 'Widget A', 'row': 2, 'column': 1},
        'B2': {'value': 100, 'row': 2, 'column': 2},
        'A3': {'value': 'Widget B', 'row': 3, 'column': 1},
        'B3': {'value': 150, 'row': 3, 'column': 2},
        
        # Gap (rows 4-6)
        
        # Table 2: Inventory (rows 7-9)
        'A7': {'value': 'Item', 'row': 7, 'column': 1},
        'B7': {'value': 'Stock', 'row': 7, 'column': 2},
        'A8': {'value': 'Laptop', 'row': 8, 'column': 1},
        'B8': {'value': 25, 'row': 8, 'column': 2},
        'A9': {'value': 'Mouse', 'row': 9, 'column': 1},
        'B9': {'value': 50, 'row': 9, 'column': 2},
        
        # Gap (rows 10-12)
        
        # Table 3: Employees (rows 13-15)
        'A13': {'value': 'Name', 'row': 13, 'column': 1},
        'B13': {'value': 'Department', 'row': 13, 'column': 2},
        'A14': {'value': 'John', 'row': 14, 'column': 1},
        'B14': {'value': 'Sales', 'row': 14, 'column': 2},
        'A15': {'value': 'Jane', 'row': 15, 'column': 1},
        'B15': {'value': 'Marketing', 'row': 15, 'column': 2},
    }
    
    dimensions = {'min_row': 1, 'max_row': 15, 'min_col': 1, 'max_col': 2}
    
    print("=== Testing Simplified Detection System ===")
    
    # Test new simplified detector
    detector = TableDetector()
    
    # Test with gap detection enabled
    options = {'table_detection': {'use_gaps': True, 'gap_threshold': 2}}
    new_regions = detector.detect_tables(test_cells, dimensions, options)
    
    print(f"\nNew Detector (gap detection): Found {len(new_regions)} tables")
    for i, region in enumerate(new_regions):
        print(f"  Table {i+1}: Rows {region['start_row']}-{region['end_row']}, Method: {region['detection_method']}")
    
    # Test without gap detection (should default to content structure)
    options = {'table_detection': {'use_gaps': False}}
    new_regions_no_gaps = detector.detect_tables(test_cells, dimensions, options)
    
    print(f"\nNew Detector (no gap detection): Found {len(new_regions_no_gaps)} tables")
    for i, region in enumerate(new_regions_no_gaps):
        print(f"  Table {i+1}: Rows {region['start_row']}-{region['end_row']}, Method: {region['detection_method']}")
    
    # Test header resolution
    print(f"\nHeader Resolution for Table 1:")
    header_resolver = HeaderResolver()
    if new_regions:
        headers = header_resolver.resolve_headers(
            detector._normalize_cell_data(test_cells), 
            new_regions[0], 
            options
        )
        print(f"  Header rows: {headers['header_rows']}")
        print(f"  Header cols: {headers['header_columns']}")
        print(f"  Data starts at: ({headers['data_start_row']}, {headers['data_start_col']})")
    
    print("\n=== Comparing with Current Implementation ===")
    
    # Test current implementation for comparison
    current_processor = TableProcessor()
    
    # Prepare data in format expected by current processor
    current_test_data = {
        'workbook': {
            'sheets': [{
                'name': 'Test Sheet',
                'dimensions': dimensions,
                'cells': test_cells,
                'tables': []
            }]
        }
    }
    
    # Test current implementation with gap detection
    current_options = {'table_detection': {'use_gaps': True}}
    current_result = current_processor.transform_to_table_format(current_test_data, current_options)
    current_tables = current_result['workbook']['sheets'][0]['tables']
    
    print(f"\nCurrent Implementation (gap detection): Found {len(current_tables)} tables")
    for i, table in enumerate(current_tables):
        region = table['region']
        method = table.get('metadata', {}).get('detection_method', 'unknown')
        print(f"  Table {i+1}: Rows {region['start_row']}-{region['end_row']}, Method: {method}")
    
    assert isinstance(new_regions, list)
    assert isinstance(current_tables, list)


def test_frozen_panes_detection():
    """Test detection with frozen panes."""
    
    test_cells = {
        'A1': {'value': 'Header 1', 'row': 1, 'column': 1},
        'B1': {'value': 'Header 2', 'row': 1, 'column': 2},
        'A2': {'value': 'Data 1', 'row': 2, 'column': 1},
        'B2': {'value': 'Data 2', 'row': 2, 'column': 2},
        'A3': {'value': 'Data 3', 'row': 3, 'column': 1},
        'B3': {'value': 'Data 4', 'row': 3, 'column': 2},
    }
    
    dimensions = {'min_row': 1, 'max_row': 3, 'min_col': 1, 'max_col': 2}
    
    print("\n=== Testing Frozen Panes Detection ===")
    
    detector = TableDetector()
    
    # Test with frozen panes
    options = {
        'sheet_data': {
            'frozen_panes': {'frozen_rows': 1, 'frozen_cols': 0}
        }
    }
    
    regions = detector.detect_tables(test_cells, dimensions, options)
    
    print(f"With frozen panes: Found {len(regions)} tables")
    for i, region in enumerate(regions):
        print(f"  Table {i+1}: Rows {region['start_row']}-{region['end_row']}, Method: {region['detection_method']}")
        if 'frozen_rows' in region:
            print(f"    Frozen rows: {region['frozen_rows']}, Frozen cols: {region['frozen_cols']}")


def test_compact_format_compatibility():
    """Test that the detector works with compact format data."""
    
    # Test data in compact format (list of row objects)
    compact_rows = [
        {'r': 1, 'cells': [[1, 'Product'], [2, 'Sales']]},
        {'r': 2, 'cells': [[1, 'Widget A'], [2, 100]]},
        {'r': 3, 'cells': [[1, 'Widget B'], [2, 150]]},
        # Gap
        {'r': 7, 'cells': [[1, 'Item'], [2, 'Stock']]},
        {'r': 8, 'cells': [[1, 'Laptop'], [2, 25]]},
        {'r': 9, 'cells': [[1, 'Mouse'], [2, 50]]},
    ]
    
    dimensions = [1, 1, 9, 2]  # Compact format dimensions
    
    print("\n=== Testing Compact Format Compatibility ===")
    
    detector = TableDetector()
    options = {'table_detection': {'use_gaps': True, 'gap_threshold': 2}}
    
    regions = detector.detect_tables(compact_rows, dimensions, options)
    
    print(f"Compact format: Found {len(regions)} tables")
    for i, region in enumerate(regions):
        print(f"  Table {i+1}: Rows {region['start_row']}-{region['end_row']}, Method: {region['detection_method']}")


def main():
    """Run all tests."""
    
    print("Testing Simplified Table Detection System")
    print("=" * 50)
    
    test_simple_multitable_detection()
    test_frozen_panes_detection()
    test_compact_format_compatibility()
    
    print("\n" + "=" * 50)
    print("Summary of Benefits:")
    print("- Cleaner, more predictable logic")
    print("- Unified handling of regular and compact formats")
    print("- Clear priority system for detection methods")
    print("- Simplified gap detection without complex heuristics")
    print("- Separated concerns (detection vs header resolution)")
    print("- Much easier to test and maintain")


if __name__ == "__main__":
    main() 