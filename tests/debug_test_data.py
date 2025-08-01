#!/usr/bin/env python3
"""
Debug script to test the specific failing test data
"""

import json
from converter.table_processor import TableProcessor

def test_three_tables_data():
    """Test the specific data from the failing test"""
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
    
    # Test with gap detection enabled
    options = {
        'table_detection': {
            'use_gaps': True
        }
    }
    
    print("Testing with gap detection enabled...")
    
    # Debug: Check what's happening in the gap detection
    sheet_data = test_data['workbook']['sheets'][0]
    cells = sheet_data['cells']
    min_row = sheet_data['dimensions']['min_row']
    max_row = sheet_data['dimensions']['max_row']
    min_col = sheet_data['dimensions']['min_col']
    max_col = sheet_data['dimensions']['max_col']
    
    print(f"Sheet dimensions: {min_row}-{max_row}, {min_col}-{max_col}")
    
    # Check which rows have data
    for row in range(min_row, max_row + 1):
        row_has_data = False
        for col in range(min_col, max_col + 1):
            cell_key = f"{chr(64 + col)}{row}"  # A1, B1, etc.
            if cell_key in cells and cells[cell_key].get('value') is not None:
                row_has_data = True
                break
        print(f"Row {row}: {'Has data' if row_has_data else 'Empty'}")
    
    # Test the _is_non_numerical_content method directly
    print("\nTesting _is_non_numerical_content for key rows:")
    for row in [9, 17]:  # The rows that should start new tables
        is_non_numerical = processor._is_non_numerical_content(cells, row, min_col, max_col)
        print(f"Row {row} (should start new table): {is_non_numerical}")
    
    # Test the gap detection directly
    print("\nTesting gap detection directly:")
    gap_regions = processor._detect_tables_by_gaps(cells, min_row, max_row, min_col, max_col)
    print(f"Gap detection found {len(gap_regions)} regions:")
    for i, region in enumerate(gap_regions):
        print(f"  Region {i+1}: Rows {region['start_row']}-{region['end_row']}, Cols {region['start_col']}-{region['end_col']}")
    
    # Debug the gap detection logic step by step
    print("\nDebugging gap detection step by step:")
    current_start_row = None
    consecutive_blank_rows = 0
    max_consecutive_blank_rows = 2
    
    for row in range(min_row, max_row + 1):
        row_has_data = False
        for col in range(min_col, max_col + 1):
            cell_key = f"{chr(64 + col)}{row}"  # A1, B1, etc.
            if cell_key in cells and cells[cell_key].get('value') is not None:
                row_has_data = True
                if current_start_row is None:
                    current_start_row = row
                consecutive_blank_rows = 0
                break
        
        if not row_has_data:
            consecutive_blank_rows += 1
            print(f"Row {row}: Empty (consecutive_blank_rows = {consecutive_blank_rows})")
            
            if current_start_row is not None and consecutive_blank_rows >= max_consecutive_blank_rows:
                next_row_after_gap = row + 1
                should_start_new_table = False
                
                if next_row_after_gap <= max_row:
                    should_start_new_table = processor._is_non_numerical_content(cells, next_row_after_gap, min_col, max_col)
                
                print(f"  Gap threshold reached at row {row}, next_row_after_gap = {next_row_after_gap}, should_start_new_table = {should_start_new_table}")
                
                if should_start_new_table:
                    print(f"  Would create table region: {current_start_row} to {row - consecutive_blank_rows}")
                else:
                    print(f"  Would continue current table through gap")
        else:
            print(f"Row {row}: Has data")
    
    result = processor.transform_to_table_format(test_data, options)
    sheet = result['workbook']['sheets'][0]
    tables = sheet['tables']
    print(f"Tables detected: {len(tables)}")
    for i, table in enumerate(tables):
        region = table['region']
        print(f"  Table {i+1}: Rows {region['start_row']}-{region['end_row']}, Cols {region['start_col']}-{region['end_col']}")

if __name__ == "__main__":
    test_three_tables_data() 