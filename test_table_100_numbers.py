#!/usr/bin/env python3
"""
Test script to verify table detection for Test_PDF_Table_100_numbers.pdf
"""

import json
import sys

def analyze_table_results(json_file):
    """Analyze the table detection results"""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Get table data
    tables = data.get('pdf_processing_result', {}).get('tables', {}).get('tables', [])
    
    if not tables:
        print("No tables found!")
        return
    
    table = tables[0]  # Get the first table
    
    print(f"Table Analysis for: {data['pdf_processing_result']['document_metadata']['filename']}")
    print("=" * 60)
    
    # Basic table info
    print(f"Table ID: {table['table_id']}")
    print(f"Detection Method: {table['metadata']['detection_method']}")
    print(f"Quality Score: {table['metadata']['quality_score']}")
    print(f"Cell Count: {table['metadata']['cell_count']}")
    
    # Column analysis
    columns = table.get('columns', [])
    print(f"\nColumns: {len(columns)}")
    for col in columns:
        print(f"  Column {col['column_index']}: {col['column_label']} ({len(col['cells'])} cells)")
    
    # Row analysis
    rows = table.get('rows', [])
    print(f"\nRows: {len(rows)}")
    for row in rows:
        print(f"  Row {row['row_index']}: {row['row_label']} ({len(row['cells'])} cells)")
    
    # Count numbers
    number_count = 0
    currency_count = 0
    date_count = 0
    
    for col in columns:
        for cell_key, cell_data in col['cells'].items():
            value = cell_data['value']
            if any(char.isdigit() for char in value):
                number_count += 1
            if '$' in value:
                currency_count += 1
            if '/' in value and any(char.isdigit() for char in value):
                date_count += 1
    
    print(f"\nContent Analysis:")
    print(f"  Numbers found: {number_count}")
    print(f"  Currency values: {currency_count}")
    print(f"  Date values: {date_count}")
    
    # Show first few cells as example
    print(f"\nSample cells:")
    for col in columns[:3]:  # First 3 columns
        for cell_key, cell_data in list(col['cells'].items())[:3]:  # First 3 cells
            print(f"  {cell_key}: {cell_data['value']}")
    
    # Verify table structure
    expected_rows = 11  # 10 data rows + 1 header row
    expected_cols = 11  # 10 date columns + 1 category column
    expected_numbers = 100  # 10x10 grid of numbers
    
    print(f"\nVerification:")
    print(f"  Expected rows: {expected_rows}, Found: {len(rows)} ✓" if len(rows) == expected_rows else f"  Expected rows: {expected_rows}, Found: {len(rows)} ✗")
    print(f"  Expected columns: {expected_cols}, Found: {len(columns)} ✓" if len(columns) == expected_cols else f"  Expected columns: {expected_cols}, Found: {len(columns)} ✗")
    print(f"  Expected numbers: {expected_numbers}, Found: {number_count} ✓" if number_count == expected_numbers else f"  Expected numbers: {expected_numbers}, Found: {number_count} ✗")

if __name__ == "__main__":
    json_file = "Test_PDF_Table_100_numbers_tables.json"
    analyze_table_results(json_file) 