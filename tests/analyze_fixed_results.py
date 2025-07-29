#!/usr/bin/env python3
"""
Analyze the fixed table detection results
"""

import json
import sys
import os

def analyze_fixed_results():
    """Analyze the fixed table detection results"""
    
    print("Analyzing Fixed Table Detection Results")
    print("=" * 60)
    
    # Load the upload result
    try:
        with open('upload_result.json', 'r') as f:
            upload_result = json.load(f)
    except FileNotFoundError:
        print("ERROR: upload_result.json not found")
        return
    
    # Get the Excel data
    excel_data = upload_result.get('excel_data', {})
    workbook = excel_data.get('workbook', {})
    sheets = workbook.get('sheets', [])
    
    print(f"Found {len(sheets)} sheets:")
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
        
        # Test table transformation
        print(f"  Testing table transformation...")
        
        try:
            import requests
            
            response = requests.post(
                'http://127.0.0.1:8001/api/transform-tables/',
                json={
                    'excel_data': excel_data,
                    'options': {'table_detection': {'use_gaps': True}}
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                result_sheets = result.get('workbook', {}).get('sheets', [])
                
                if i < len(result_sheets):
                    result_sheet = result_sheets[i]
                    tables = result_sheet.get('tables', [])
                    print(f"    Detected {len(tables)} tables")
                    
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
                            for cell_ref, cell_data in list(table_cells.items())[:5]:
                                value = cell_data.get('value', '')
                                if isinstance(value, str) and len(value) > 40:
                                    value = value[:40] + "..."
                                print(f"          {cell_ref}: {value}")
                                cell_count += 1
                                if cell_count >= 5:
                                    break
                            
                            if len(table_cells) > 5:
                                print(f"          ... and {len(table_cells) - 5} more cells")
                        
                        # Show table structure
                        rows = table.get('rows', [])
                        columns = table.get('columns', [])
                        print(f"        Structure: {len(rows)} rows, {len(columns)} columns")
                        
                        if rows:
                            print(f"        First row sample:")
                            first_row = rows[0]
                            for j, cell in enumerate(first_row.get('cells', [])[:3]):
                                value = cell.get('value', '')
                                if isinstance(value, str) and len(value) > 30:
                                    value = value[:30] + "..."
                                print(f"          Col {j+1}: {value}")
            else:
                print(f"    ERROR: Request failed with status {response.status_code}")
                
        except Exception as e:
            print(f"    ERROR: {str(e)}")
        
        print()

def main():
    """Main function"""
    analyze_fixed_results()

if __name__ == "__main__":
    main() 