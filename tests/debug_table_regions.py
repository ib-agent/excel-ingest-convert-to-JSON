#!/usr/bin/env python3
"""
Debug table regions to understand why some sheets are detecting 2 tables
"""

import json
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.table_processor import TableProcessor

def debug_table_regions():
    """Debug table regions for each sheet"""
    
    print("Debugging Table Regions")
    print("=" * 60)
    
    # Load the full Excel data
    try:
        with open('full_excel_data.json', 'r') as f:
            excel_data = json.load(f)
    except FileNotFoundError:
        print("ERROR: full_excel_data.json not found")
        return
    
    workbook = excel_data.get('workbook', {})
    sheets = workbook.get('sheets', [])
    
    print(f"Found {len(sheets)} sheets:")
    print("-" * 40)
    
    processor = TableProcessor()
    
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
        
        # Get cells
        cells = sheet.get('cells', {})
        print(f"  Total cells: {len(cells)}")
        
        # Test financial table detection
        print(f"  Testing financial table detection...")
        is_financial = processor._is_financial_table_with_single_gaps(cells, min_row, max_row, min_col, max_col)
        print(f"    Is financial table with single gaps: {is_financial}")
        
        # Test table region detection
        print(f"  Testing table region detection...")
        options = {'table_detection': {'use_gaps': True}}
        regions = processor._detect_table_regions(cells, min_row, max_row, min_col, max_col, options)
        print(f"    Detected {len(regions)} table regions")
        
        for j, region in enumerate(regions):
            start_row = region.get('start_row', 0)
            end_row = region.get('end_row', 0)
            start_col = region.get('start_col', 0)
            end_col = region.get('end_col', 0)
            method = region.get('detection_method', 'unknown')
            
            print(f"      Region {j+1}: Rows {start_row}-{end_row}, Cols {start_col}-{end_col}, Method: {method}")
        
        # Analyze gaps in the data
        print(f"  Analyzing gaps...")
        rows_with_data = []
        for row in range(min_row, max_row + 1):
            row_has_data = False
            for col in range(min_col, max_col + 1):
                cell_key = f"{chr(64 + col)}{row}"  # Convert to A1, B1, etc.
                if cell_key in cells and cells[cell_key].get('value') is not None:
                    row_has_data = True
                    break
            if row_has_data:
                rows_with_data.append(row)
        
        print(f"    Rows with data: {len(rows_with_data)}")
        
        # Find gaps
        gaps = []
        for k in range(len(rows_with_data) - 1):
            gap = rows_with_data[k+1] - rows_with_data[k] - 1
            if gap > 0:
                gaps.append((rows_with_data[k], rows_with_data[k+1], gap))
        
        if gaps:
            print(f"    Gaps found:")
            for start, end, gap in gaps:
                print(f"      Gap of {gap} rows between row {start} and {end}")
        else:
            print(f"    No gaps found")
        
        print()

def main():
    """Main function"""
    debug_table_regions()

if __name__ == "__main__":
    main() 