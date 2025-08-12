#!/usr/bin/env python3
"""
Test script to verify financial table detection fix
"""

import sys
import os
import json
import django
from rest_framework.test import APIClient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'excel_converter.settings')
django.setup()

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_financial_table_detection():
    """Test the financial table detection with the problematic Excel file"""
    
    print("Testing Financial Table Detection Fix")
    print("=" * 60)
    
    # Upload the file again to get fresh data
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fixtures', 'excel', 'pDD10b - Exos_2023_financials.xlsx')
    
    client = APIClient()
    with open(file_path, 'rb') as f:
        upload = {'file': f}
        response = client.post('/api/upload/', data=upload)
    
    if response.status_code != 200:
        print(f"ERROR: Upload failed with status {response.status_code}")
        return
    
    upload_result = response.json()
    print("Upload successful.")

    # Get the Excel JSON data
    excel_data = upload_result.get('data') or {}
    if not excel_data:
        # For large files, fetch via download URL provided by the API
        download_urls = upload_result.get('download_urls', {})
        full_url = download_urls.get('full_data')
        if full_url:
            download_resp = client.get(full_url)
            if download_resp.status_code == 200:
                try:
                    excel_data = json.loads(download_resp.content.decode('utf-8'))
                except Exception:
                    excel_data = {}
        if not excel_data:
            print("No inline data available and couldn't fetch via download URL; skipping transform tests.")
            return
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
                response = client.post(
                    '/api/transform-tables/',
                    data={
                        'json_data': excel_data,
                        'options': options
                    },
                    format='json'
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