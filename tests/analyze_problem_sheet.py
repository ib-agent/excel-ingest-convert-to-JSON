#!/usr/bin/env python3
"""
Analyze the problematic sheet to understand why it's detecting multiple tables
"""

import json
import sys
import os

def analyze_sheet_structure(sheet_data):
    """Analyze the structure of a sheet to understand table detection issues"""
    
    sheet_name = sheet_data.get('name', 'Unknown')
    print(f"\nAnalyzing sheet: {sheet_name}")
    print("=" * 60)
    
    # Get dimensions
    dimensions = sheet_data.get('dimensions', {})
    min_row = dimensions.get('min_row', 1)
    max_row = dimensions.get('max_row', 1)
    min_col = dimensions.get('min_col', 1)
    max_col = dimensions.get('max_col', 1)
    
    print(f"Dimensions: Rows {min_row}-{max_row}, Cols {min_col}-{max_col}")
    
    # Get cells
    cells = sheet_data.get('cells', {})
    print(f"Total cells: {len(cells)}")
    
    # Analyze cell distribution by row
    row_data = {}
    for cell_ref, cell_data in cells.items():
        # Parse cell reference
        col = ''
        row_str = ''
        for char in cell_ref:
            if char.isalpha():
                col += char
            else:
                row_str += char
        
        if row_str:
            row_num = int(row_str)
            if row_num not in row_data:
                row_data[row_num] = []
            row_data[row_num].append((cell_ref, cell_data))
    
    # Sort rows
    sorted_rows = sorted(row_data.keys())
    print(f"\nRows with data: {sorted_rows}")
    
    # Analyze gaps and patterns
    print(f"\nAnalyzing row patterns:")
    print("-" * 40)
    
    for i, row_num in enumerate(sorted_rows):
        cells_in_row = row_data[row_num]
        cell_count = len(cells_in_row)
        
        # Get sample values from this row
        sample_values = []
        for cell_ref, cell_data in cells_in_row[:5]:  # First 5 cells
            value = cell_data.get('value', '')
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            sample_values.append(f"{cell_ref}:{value}")
        
        print(f"Row {row_num:3d}: {cell_count:2d} cells - {', '.join(sample_values)}")
        
        # Check for gaps
        if i > 0:
            gap = row_num - sorted_rows[i-1] - 1
            if gap > 0:
                print(f"  *** GAP of {gap} rows between row {sorted_rows[i-1]} and {row_num} ***")
    
    # Look for potential table boundaries
    print(f"\nPotential table boundaries:")
    print("-" * 40)
    
    # Find rows with many cells (likely data rows)
    data_rows = []
    for row_num, cells_in_row in row_data.items():
        if len(cells_in_row) >= 5:  # Consider rows with 5+ cells as data rows
            data_rows.append(row_num)
    
    data_rows.sort()
    print(f"Data rows (5+ cells): {data_rows}")
    
    # Find gaps in data rows
    if len(data_rows) > 1:
        gaps = []
        for i in range(len(data_rows) - 1):
            gap = data_rows[i+1] - data_rows[i] - 1
            if gap > 0:
                gaps.append((data_rows[i], data_rows[i+1], gap))
        
        if gaps:
            print(f"Gaps in data rows:")
            for start, end, gap in gaps:
                print(f"  Gap of {gap} rows between data rows {start} and {end}")
        else:
            print("No gaps found in data rows")
    
    # Analyze column patterns
    print(f"\nColumn analysis:")
    print("-" * 40)
    
    col_data = {}
    for cell_ref, cell_data in cells.items():
        col = ''
        row_str = ''
        for char in cell_ref:
            if char.isalpha():
                col += char
            else:
                row_str += char
        
        if col not in col_data:
            col_data[col] = []
        col_data[col].append((cell_ref, cell_data))
    
    sorted_cols = sorted(col_data.keys(), key=lambda x: (len(x), x))
    print(f"Columns with data: {sorted_cols}")
    
    # Show column distribution
    for col in sorted_cols[:10]:  # First 10 columns
        cell_count = len(col_data[col])
        print(f"Column {col}: {cell_count} cells")
    
    if len(sorted_cols) > 10:
        print(f"... and {len(sorted_cols) - 10} more columns")

def main():
    """Main function"""
    
    # Load the Excel data
    try:
        with open('debug_excel_data.json', 'r') as f:
            excel_data = json.load(f)
    except FileNotFoundError:
        print("ERROR: debug_excel_data.json not found. Please run the upload first.")
        return
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in debug_excel_data.json: {e}")
        return
    
    workbook = excel_data.get('workbook', {})
    sheets = workbook.get('sheets', [])
    
    print(f"Found {len(sheets)} sheets in the Excel file")
    
    # Find the problematic sheet
    problem_sheet = None
    for sheet in sheets:
        if sheet.get('name') == 'TOTAL P&L with PT':
            problem_sheet = sheet
            break
    
    if problem_sheet:
        analyze_sheet_structure(problem_sheet)
    else:
        print("ERROR: Could not find 'TOTAL P&L with PT' sheet")
        
        # List all available sheets
        print("\nAvailable sheets:")
        for i, sheet in enumerate(sheets):
            name = sheet.get('name', f'Sheet {i+1}')
            print(f"  {i+1}: {name}")

if __name__ == "__main__":
    main() 