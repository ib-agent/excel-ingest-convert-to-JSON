#!/usr/bin/env python3
"""
Check if sheets have frozen panes data
"""

import json
import sys
import os

def check_frozen_panes():
    """Check if sheets have frozen panes data"""
    
    print("Checking Frozen Panes Data")
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
    
    for i, sheet in enumerate(sheets):
        sheet_name = sheet.get('name', f'Sheet {i+1}')
        print(f"\nSheet {i+1}: {sheet_name}")
        
        # Check for frozen panes
        frozen_panes = sheet.get('frozen_panes', {})
        if frozen_panes:
            print(f"  Frozen panes found: {frozen_panes}")
            frozen_rows = frozen_panes.get('frozen_rows', 0)
            frozen_cols = frozen_panes.get('frozen_cols', 0)
            print(f"    Frozen rows: {frozen_rows}")
            print(f"    Frozen columns: {frozen_cols}")
        else:
            print(f"  No frozen panes data found")
        
        # Check for other sheet properties
        print(f"  Sheet properties:")
        for key, value in sheet.items():
            if key not in ['cells', 'dimensions', 'frozen_panes']:
                print(f"    {key}: {value}")
        
        print()

def main():
    """Main function"""
    check_frozen_panes()

if __name__ == "__main__":
    main() 