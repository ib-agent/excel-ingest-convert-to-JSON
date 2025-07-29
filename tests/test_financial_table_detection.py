#!/usr/bin/env python3
"""
Test script to verify financial table detection fix
"""

import sys
import os
import json
import requests

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_financial_table_detection():
    """Test the financial table detection with the problematic Excel file"""
    
    print("Testing Financial Table Detection Fix")
    print("=" * 60)
    
    # Upload the file again to get fresh data
    file_path = "/Users/jeffwinner/Desktop/Number Counter tests/pDD10b - Exos_2023_financials.xlsx"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post('http://127.0.0.1:8001/api/upload/', files=files)
    
    if response.status_code != 200:
        print(f"ERROR: Upload failed with status {response.status_code}")
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
        
        # Test table detection with different options
        test_options = [
            {'table_detection': {'use_gaps': False}},
            {'table_detection': {'use_gaps': True}},
        ]
        
        for j, options in enumerate(test_options):
            print(f"  Test {j+1}: use_gaps={options['table_detection']['use_gaps']}")
            
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
                        print(f"    Detected {len(tables)} tables")
                        
                        # Show table regions
                        for k, table in enumerate(tables):
                            region = table.get('region', {})
                            start_row = region.get('start_row', 0)
                            end_row = region.get('end_row', 0)
                            start_col = region.get('start_col', 0)
                            end_col = region.get('end_col', 0)
                            
                            print(f"      Table {k+1}: Rows {start_row}-{end_row}, Cols {start_col}-{end_col}")
                            
                            # Show sample data from the table
                            table_cells = table.get('cells', {})
                            if table_cells:
                                print(f"        Sample data:")
                                cell_count = 0
                                for cell_ref, cell_data in list(table_cells.items())[:3]:
                                    value = cell_data.get('value', '')
                                    if isinstance(value, str) and len(value) > 30:
                                        value = value[:30] + "..."
                                    print(f"          {cell_ref}: {value}")
                                    cell_count += 1
                                    if cell_count >= 3:
                                        break
                else:
                    print(f"    ERROR: Request failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"    ERROR: {str(e)}")
        
        print()

def main():
    """Main function"""
    test_financial_table_detection()

if __name__ == "__main__":
    main() 