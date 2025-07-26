#!/usr/bin/env python3
"""
Test that files without frozen panes use other table detection methods
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.excel_processor import ExcelProcessor
from converter.table_processor import TableProcessor


def test_no_frozen_panes_excel():
    """Test that files without frozen panes use other detection methods"""
    
    excel_file = "test_no_frozen_panes.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found. Please run create_test_no_frozen_panes_excel.py first.")
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
        
        if frozen_panes.get('frozen_rows', 0) == 0 and frozen_panes.get('frozen_cols', 0) == 0:
            print("✓ SUCCESS: No frozen panes detected (as expected)")
        else:
            print("✗ FAILURE: Frozen panes detected when none should exist")
        
        # Step 2: Transform to table format
        print("\nStep 2: Transforming to table format...")
        table_data = table_processor.transform_to_table_format(excel_data)
        
        # Step 3: Analyze results
        print("\nStep 3: Analyzing results...")
        sheet = table_data['workbook']['sheets'][0]
        tables = sheet.get('tables', [])
        
        print(f"Number of tables created: {len(tables)}")
        
        if len(tables) > 1:
            print("✓ SUCCESS: Multiple tables created (other detection methods working)")
            
            for i, table in enumerate(tables):
                region = table['region']
                metadata = table.get('metadata', {})
                detection_method = metadata.get('detection_method', 'unknown')
                
                print(f"\nTable {i+1}:")
                print(f"  Region: {region['start_row']}:{region['end_row']}, {region['start_col']}:{region['end_col']}")
                print(f"  Detection method: {detection_method}")
                
                # Verify detection method is NOT frozen_panes
                if detection_method != 'frozen_panes':
                    print(f"  ✓ SUCCESS: Detection method is not 'frozen_panes'")
                else:
                    print(f"  ✗ FAILURE: Detection method should not be 'frozen_panes'")
                
                # Check for data from expected sections
                rows = table.get('rows', [])
                row_values = []
                for row in rows:
                    if 'cells' in row:
                        for cell_key, cell_data in row['cells'].items():
                            if 'value' in cell_data:
                                row_values.append(cell_data['value'])
                
                # Identify which table this is based on content
                if any('Table 1 Header' in val for val in row_values):
                    print(f"  Content: Table 1 data")
                elif any('Table 2 Header' in val for val in row_values):
                    print(f"  Content: Table 2 data")
                elif any('Table 3 Header' in val for val in row_values):
                    print(f"  Content: Table 3 data")
                else:
                    print(f"  Content: Unknown data")
            
            # Verify we have all three expected tables
            table_headers = []
            for table in tables:
                rows = table.get('rows', [])
                for row in rows:
                    if 'cells' in row:
                        for cell_key, cell_data in row['cells'].items():
                            if 'value' in cell_data and 'Header' in cell_data['value']:
                                table_headers.append(cell_data['value'])
                                break
                        break
            
            expected_headers = ['Table 1 Header', 'Table 2 Header', 'Table 3 Header']
            found_headers = [h for h in expected_headers if any(h in th for th in table_headers)]
            
            if len(found_headers) == 3:
                print(f"\n✓ SUCCESS: All three expected tables found")
            else:
                print(f"\n⚠ WARNING: Only {len(found_headers)}/3 expected tables found")
                print(f"  Expected: {expected_headers}")
                print(f"  Found: {table_headers}")
                
        else:
            print(f"✗ FAILURE: Expected multiple tables, got {len(tables)} table(s)")
            print("This indicates that other detection methods are not working correctly")
        
        # Step 4: Save results for inspection
        output_file = "test_no_frozen_panes_result.json"
        with open(output_file, 'w') as f:
            json.dump(table_data, f, indent=2)
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_no_frozen_panes_excel() 