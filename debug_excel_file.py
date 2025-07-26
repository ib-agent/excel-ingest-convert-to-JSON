#!/usr/bin/env python3
"""
Debug script to analyze the Excel file and understand table detection issues
"""

import sys
import os
import json
import requests
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_excel_file(file_path):
    """Analyze the Excel file and show table detection results"""
    
    print(f"Analyzing file: {file_path}")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return
    
    # Upload the file
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post('http://127.0.0.1:8001/api/upload/', files=files)
    
    if response.status_code != 200:
        print(f"ERROR: Upload failed with status {response.status_code}")
        print(response.text)
        return
    
    upload_result = response.json()
    print(f"Upload successful. File ID: {upload_result.get('file_id')}")
    
    # Get the Excel JSON data
    excel_data = upload_result.get('excel_data', {})
    workbook = excel_data.get('workbook', {})
    sheets = workbook.get('sheets', [])
    
    print(f"\nFound {len(sheets)} sheets:")
    print("-" * 40)
    
    for i, sheet in enumerate(sheets):
        sheet_name = sheet.get('name', f'Sheet {i+1}')
        print(f"\nSheet {i+1}: {sheet_name}")
        
        # Get sheet dimensions
        dimensions = sheet.get('dimensions', {})
        min_row = dimensions.get('min_row', 1)
        max_row = dimensions.get('max_row', 1)
        min_col = dimensions.get('min_col', 1)
        max_col = dimensions.get('max_col', 1)
        
        print(f"  Dimensions: Rows {min_row}-{max_row}, Cols {min_col}-{max_col}")
        
        # Count cells
        cells = sheet.get('cells', {})
        print(f"  Total cells: {len(cells)}")
        
        # Analyze cell distribution
        rows_with_data = set()
        cols_with_data = set()
        
        for cell_ref, cell_data in cells.items():
            # Parse cell reference (e.g., 'A1' -> row=1, col='A')
            col = ''
            row_str = ''
            for char in cell_ref:
                if char.isalpha():
                    col += char
                else:
                    row_str += char
            
            if row_str:
                row_num = int(row_str)
                rows_with_data.add(row_num)
                cols_with_data.add(col)
        
        print(f"  Rows with data: {sorted(rows_with_data)}")
        print(f"  Columns with data: {sorted(cols_with_data)}")
        
        # Check for gaps in data
        if len(rows_with_data) > 1:
            row_gaps = []
            sorted_rows = sorted(rows_with_data)
            for j in range(len(sorted_rows) - 1):
                gap = sorted_rows[j+1] - sorted_rows[j] - 1
                if gap > 0:
                    row_gaps.append((sorted_rows[j], sorted_rows[j+1], gap))
            
            if row_gaps:
                print(f"  Row gaps found:")
                for start, end, gap in row_gaps:
                    print(f"    Gap of {gap} rows between row {start} and {end}")
        
        # Test table detection
        print(f"\n  Testing table detection...")
        
        # Test with different options
        test_options = [
            {'table_detection': {'use_gaps': False}},
            {'table_detection': {'use_gaps': True}},
        ]
        
        for j, options in enumerate(test_options):
            print(f"    Test {j+1}: use_gaps={options['table_detection']['use_gaps']}")
            
            try:
                response = requests.post(
                    'http://127.0.0.1:8001/api/transform-tables/',
                    json={
                        'excel_data': excel_data,
                        'options': options
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    result_sheets = result.get('workbook', {}).get('sheets', [])
                    
                    if i < len(result_sheets):
                        result_sheet = result_sheets[i]
                        tables = result_sheet.get('tables', [])
                        print(f"      Detected {len(tables)} tables")
                        
                        for k, table in enumerate(tables):
                            region = table.get('region', {})
                            start_row = region.get('start_row', 0)
                            end_row = region.get('end_row', 0)
                            start_col = region.get('start_col', 0)
                            end_col = region.get('end_col', 0)
                            
                            print(f"        Table {k+1}: Rows {start_row}-{end_row}, Cols {start_col}-{end_col}")
                            
                            # Show first few cells of the table
                            table_cells = table.get('cells', {})
                            if table_cells:
                                print(f"          Sample cells:")
                                cell_count = 0
                                for cell_ref, cell_data in list(table_cells.items())[:5]:
                                    value = cell_data.get('value', '')
                                    print(f"            {cell_ref}: {value}")
                                    cell_count += 1
                                    if cell_count >= 5:
                                        break
                                if len(table_cells) > 5:
                                    print(f"            ... and {len(table_cells) - 5} more cells")
                else:
                    print(f"      ERROR: Request failed with status {response.status_code}")
                    print(f"      Response: {response.text}")
                    
            except Exception as e:
                print(f"      ERROR: {str(e)}")
        
        print()

def main():
    """Main function"""
    file_path = "/Users/jeffwinner/Desktop/Number Counter tests/pDD10b - Exos_2023_financials.xlsx"
    
    print("Excel File Analysis Tool")
    print("=" * 60)
    
    analyze_excel_file(file_path)

if __name__ == "__main__":
    main() 