#!/usr/bin/env python3
"""
Test the frozen panes table detection behavior with a real Excel file
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.excel_processor import ExcelProcessor
from converter.table_processor import TableProcessor


def test_real_frozen_panes_excel():
    """Test frozen panes behavior with a real Excel file"""
    
    excel_file = "test_frozen_panes_override.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found. Please run create_test_frozen_panes_excel.py first.")
        return
    
    print(f"Processing Excel file: {excel_file}")
    print("=" * 50)
    
    # Process the Excel file
    excel_processor = ExcelProcessor()
    table_processor = TableProcessor()
    
    try:
        # Step 1: Extract Excel data
        print("Step 1: Extracting Excel data...")
        excel_data = excel_processor.process_file(excel_file)
        
        # Check frozen panes extraction
        sheet = excel_data['workbook']['sheets'][0]
        frozen_panes = sheet.get('frozen_panes', {})
        print(f"Frozen panes detected: {frozen_panes}")
        print(f"  - Frozen rows: {frozen_panes.get('frozen_rows', 0)}")
        print(f"  - Frozen columns: {frozen_panes.get('frozen_cols', 0)}")
        print(f"  - Top left cell: {frozen_panes.get('top_left_cell', 'None')}")
        
        # Step 2: Transform to table format
        print("\nStep 2: Transforming to table format...")
        table_data = table_processor.transform_to_table_format(excel_data)
        
        # Step 3: Analyze results
        print("\nStep 3: Analyzing results...")
        sheet = table_data['workbook']['sheets'][0]
        tables = sheet.get('tables', [])
        
        print(f"Number of tables created: {len(tables)}")
        
        if len(tables) == 1:
            print("✓ SUCCESS: Exactly one table created (frozen panes override working)")
            
            table = tables[0]
            region = table['region']
            metadata = table.get('metadata', {})
            
            print(f"Table region: {region['start_row']}:{region['end_row']}, {region['start_col']}:{region['end_col']}")
            print(f"Detection method: {metadata.get('detection_method', 'unknown')}")
            print(f"Frozen rows in region: {region.get('frozen_rows', 'not found')}")
            print(f"Frozen columns in region: {region.get('frozen_cols', 'not found')}")
            
            # Verify that all data is included
            rows = table.get('rows', [])
            print(f"Number of rows in table: {len(rows)}")
            
            # Check for data from different sections
            row_values = []
            for row in rows:
                if 'cells' in row:
                    for cell_key, cell_data in row['cells'].items():
                        if 'value' in cell_data:
                            row_values.append(cell_data['value'])
            
            # Check for data from all sections
            sections_found = []
            if any('Row 1' in val for val in row_values):
                sections_found.append("First section")
            if any('Second Section' in val for val in row_values):
                sections_found.append("Second section")
            if any('Third Section' in val for val in row_values):
                sections_found.append("Third section")
            if any('Final Row' in val for val in row_values):
                sections_found.append("Final section")
            
            print(f"Data sections included: {', '.join(sections_found)}")
            
            if len(sections_found) == 4:
                print("✓ SUCCESS: All data sections included in single table")
            else:
                print(f"⚠ WARNING: Only {len(sections_found)}/4 sections found")
                
        else:
            print(f"✗ FAILURE: Expected 1 table, got {len(tables)} tables")
            print("This indicates that frozen panes override is not working correctly")
            
            for i, table in enumerate(tables):
                region = table['region']
                metadata = table.get('metadata', {})
                print(f"  Table {i+1}: {region['start_row']}:{region['end_row']}, {region['start_col']}:{region['end_col']}")
                print(f"    Detection method: {metadata.get('detection_method', 'unknown')}")
        
        # Step 4: Save results for inspection
        output_file = "test_frozen_panes_result.json"
        with open(output_file, 'w') as f:
            json.dump(table_data, f, indent=2)
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_real_frozen_panes_excel() 