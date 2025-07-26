#!/usr/bin/env python3
"""
Debug script to test table detection logic
"""

import json
import sys
from converter.table_processor import TableProcessor

def main():
    """Main function"""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "/Users/jeffwinner/Desktop/Number Counter tests/EXOS-Total P&L with PT only.xlsx"
    
    print("Table Detection Debug Tool")
    print("=" * 60)
    
    # Load the test data
    with open('test_data.json', 'r') as f:
        data = json.load(f)
    
    sheet = data['workbook']['sheets'][0]
    print(f"Sheet: {sheet.get('name', 'Unknown')}")
    print(f"Dimensions: {sheet.get('dimensions', {})}")
    print(f"Cells: {len(sheet.get('cells', {}))}")
    print(f"Frozen panes: {sheet.get('frozen_panes', {})}")
    
    # Test table detection
    processor = TableProcessor()
    
    # Test structured layout detection
    cells = sheet.get('cells', {})
    dimensions = sheet.get('dimensions', {})
    min_row = dimensions.get('min_row', 1)
    max_row = dimensions.get('max_row', 1)
    min_col = dimensions.get('min_col', 1)
    max_col = dimensions.get('max_col', 1)
    
    print(f"\nTesting structured layout detection...")
    has_structured_layout = processor._detect_structured_table_layout(cells, min_row, max_row, min_col, max_col)
    print(f"Has structured layout: {has_structured_layout}")
    
    # Test table region detection
    print(f"\nTesting table region detection...")
    options = {
        'sheet_data': sheet,
        'table_detection': {'use_gaps': False}
    }
    
    regions = processor._detect_table_regions(cells, min_row, max_row, min_col, max_col, options)
    print(f"Detected regions: {len(regions)}")
    for i, region in enumerate(regions):
        print(f"  Region {i+1}: {region}")
    
    # Test table processing
    if regions:
        print(f"\nTesting table processing...")
        tables = processor._detect_and_process_tables(sheet, options)
        print(f"Processed tables: {len(tables)}")
        for i, table in enumerate(tables):
            print(f"  Table {i+1}: {table.get('table_id', 'Unknown')}")
            print(f"    Region: {table.get('region', {})}")
            print(f"    Columns: {len(table.get('columns', []))}")
            print(f"    Rows: {len(table.get('rows', []))}")
    
    # Test the full transformation
    print(f"\nTesting full transformation...")
    result = processor.transform_to_table_format(data, options)
    print(f"Result tables: {len(result.get('workbook', {}).get('sheets', [{}])[0].get('tables', []))}")

if __name__ == "__main__":
    main() 