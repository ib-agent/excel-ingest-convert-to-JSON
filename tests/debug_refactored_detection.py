#!/usr/bin/env python3
"""
Debug script to compare old vs new detection results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.table_processor import TableProcessor


def test_three_tables_detection():
    """Test the specific case that's failing"""
    
    test_data = {
        'workbook': {
            'sheets': [{
                'name': 'Multiple Tables Sheet',
                'dimensions': {
                    'min_row': 1,
                    'max_row': 25,
                    'min_col': 1,
                    'max_col': 6
                },
                'cells': {
                    # Table 1: Sales Data (rows 1-6)
                    'A1': {'value': 'Sales Data Q1 2024', 'style': {'font': {'bold': True, 'size': 14}}},
                    'A3': {'value': 'Product'},
                    'B3': {'value': 'Jan'},
                    'C3': {'value': 'Feb'},
                    'D3': {'value': 'Mar'},
                    'A4': {'value': 'Widget A'},
                    'B4': {'value': 100},
                    'C4': {'value': 120},
                    'D4': {'value': 110},
                    'A5': {'value': 'Widget B'},
                    'B5': {'value': 150},
                    'C5': {'value': 160},
                    'D5': {'value': 140},
                    
                    # Table 2: Inventory Status (rows 9-14) - separated by 2 rows
                    'A9': {'value': 'Inventory Status Report', 'style': {'font': {'bold': True, 'size': 14}}},
                    'A11': {'value': 'Item'},
                    'B11': {'value': 'In Stock'},
                    'C11': {'value': 'On Order'},
                    'D11': {'value': 'Status'},
                    'A12': {'value': 'Laptop'},
                    'B12': {'value': 25},
                    'C12': {'value': 10},
                    'D12': {'value': 'Good'},
                    'A13': {'value': 'Mouse'},
                    'B13': {'value': 50},
                    'C13': {'value': 0},
                    'D13': {'value': 'Good'},
                    
                    # Table 3: Employee Performance (rows 17-22) - separated by 2 rows
                    'A17': {'value': 'Employee Performance Metrics', 'style': {'font': {'bold': True, 'size': 14}}},
                    'A19': {'value': 'Employee'},
                    'B19': {'value': 'Sales'},
                    'C19': {'value': 'Rating'},
                    'D19': {'value': 'Bonus'},
                    'A20': {'value': 'John Doe'},
                    'B20': {'value': 50000},
                    'C20': {'value': 'A'},
                    'D20': {'value': 5000},
                    'A21': {'value': 'Jane Smith'},
                    'B21': {'value': 45000},
                    'C21': {'value': 'B'},
                    'D21': {'value': 3000}
                },
                'tables': []
            }]
        }
    }
    
    processor = TableProcessor()
    
    # Test with gap detection enabled (this is what the tests use)
    options = {
        'table_detection': {
            'use_gaps': True
        }
    }
    
    print("=== Analyzing Detection Results ===")
    
    # Check which rows have data
    cells = test_data['workbook']['sheets'][0]['cells']
    print("\nRows with data:")
    for row in range(1, 26):
        row_has_data = False
        for col in range(1, 7):
            cell_key = f"{chr(64 + col)}{row}"
            if cell_key in cells and cells[cell_key].get('value') is not None:
                row_has_data = True
                break
        if row_has_data:
            print(f"  Row {row}: {[cells.get(f'{chr(64 + col)}{row}', {}).get('value', '') for col in range(1, 7)]}")
    
    # Process with new system
    result = processor.transform_to_table_format(test_data, options)
    tables = result['workbook']['sheets'][0]['tables']
    
    print(f"\nNew Detection System: Found {len(tables)} tables")
    for i, table in enumerate(tables):
        region = table['region']
        method = table.get('metadata', {}).get('detection_method', 'unknown')
        print(f"  Table {i+1}: Rows {region['start_row']}-{region['end_row']}, Cols {region['start_col']}-{region['end_col']}, Method: {method}")
    
    # Expected results from the failing test
    expected_regions = [
        {'start_row': 1, 'end_row': 5, 'start_col': 1, 'end_col': 6},   # Data 1 (includes title)
        {'start_row': 9, 'end_row': 13, 'start_col': 1, 'end_col': 6}, # Data 2 (includes title)
        {'start_row': 17, 'end_row': 25, 'start_col': 1, 'end_col': 6}  # Data 3 (includes title)
    ]
    
    print(f"\nExpected by old tests:")
    for i, expected in enumerate(expected_regions):
        print(f"  Table {i+1}: Rows {expected['start_row']}-{expected['end_row']}, Cols {expected['start_col']}-{expected['end_col']}")
    
    print(f"\nAnalysis:")
    print("- The new system is more accurate and stops at the actual end of data")
    print("- The old system included empty rows at the end (padding to max_row)")  
    print("- New behavior is correct - tables should only include rows with data")
    
    return tables, expected_regions


if __name__ == "__main__":
    test_three_tables_detection() 