#!/usr/bin/env python3
"""
Simple test to debug gap detection
"""

from converter.table_processor import TableProcessor

def test_simple_gap():
    """Test a simple case with one gap"""
    test_data = {
        'workbook': {
            'sheets': [{
                'name': 'Simple Test',
                'dimensions': {
                    'min_row': 1,
                    'max_row': 10,
                    'min_col': 1,
                    'max_col': 3
                },
                'cells': {
                    # First table
                    'A1': {'value': 'Header 1'},
                    'A2': {'value': 'Data 1'},
                    'A3': {'value': 'Data 2'},
                    
                    # Gap (rows 4-5 empty)
                    
                    # Second table
                    'A6': {'value': 'Header 2'},
                    'A7': {'value': 'Data 3'},
                    'A8': {'value': 'Data 4'},
                },
                'tables': []
            }]
        }
    }
    
    processor = TableProcessor()
    sheet_data = test_data['workbook']['sheets'][0]
    cells = sheet_data['cells']
    min_row = sheet_data['dimensions']['min_row']
    max_row = sheet_data['dimensions']['max_row']
    min_col = sheet_data['dimensions']['min_col']
    max_col = sheet_data['dimensions']['max_col']
    
    print("Testing simple gap detection:")
    print(f"Sheet dimensions: {min_row}-{max_row}, {min_col}-{max_col}")
    
    # Check which rows have data
    for row in range(min_row, max_row + 1):
        row_has_data = False
        for col in range(min_col, max_col + 1):
            cell_key = f"{chr(64 + col)}{row}"
            if cell_key in cells and cells[cell_key].get('value') is not None:
                row_has_data = True
                break
        print(f"Row {row}: {'Has data' if row_has_data else 'Empty'}")
    
    # Test gap detection
    gap_regions = processor._detect_tables_by_gaps(cells, min_row, max_row, min_col, max_col)
    print(f"\nGap detection found {len(gap_regions)} regions:")
    for i, region in enumerate(gap_regions):
        print(f"  Region {i+1}: Rows {region['start_row']}-{region['end_row']}")
    
    # Test the full transformation
    options = {
        'table_detection': {
            'use_gaps': True
        }
    }
    result = processor.transform_to_table_format(test_data, options)
    sheet = result['workbook']['sheets'][0]
    tables = sheet['tables']
    print(f"\nFull transformation found {len(tables)} tables:")
    for i, table in enumerate(tables):
        region = table['region']
        print(f"  Table {i+1}: Rows {region['start_row']}-{region['end_row']}")

if __name__ == "__main__":
    test_simple_gap() 