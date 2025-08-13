#!/usr/bin/env python3
"""
Debug script for Excel Complexity Analyzer

This script investigates why the complexity analyzer is not detecting
complexity in the 360 Energy file.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.compact_excel_processor import CompactExcelProcessor
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer
from converter.excel_processor import ExcelProcessor
import json


def debug_360_energy_file():
    """Debug the 360 Energy file to understand why complexity is not detected"""
    print("=== Debugging 360 Energy Complexity Detection ===\n")
    
    file_path = "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    # Process with both processors to compare
    print("🔍 Processing with both processors...\n")
    
    # 1. Compact processor (current)
    compact_processor = CompactExcelProcessor()
    compact_data = compact_processor.process_file(file_path)
    
    # 2. Full processor (for comparison)
    full_processor = ExcelProcessor()
    full_data = full_processor.process_file(file_path)
    
    # Focus on the "Monthly" sheet which should be complex
    monthly_sheet_compact = None
    monthly_sheet_full = None
    
    for sheet in compact_data.get('workbook', {}).get('sheets', []):
        if sheet.get('name') == 'Monthly':
            monthly_sheet_compact = sheet
            break
    
    for sheet in full_data.get('workbook', {}).get('sheets', []):
        if sheet.get('name') == 'Monthly':
            monthly_sheet_full = sheet
            break
    
    if not monthly_sheet_compact or not monthly_sheet_full:
        print("❌ Could not find 'Monthly' sheet in data")
        return
    
    print("📊 Comparing 'Monthly' Sheet Data:\n")
    
    # Compare dimensions
    compact_dims = monthly_sheet_compact.get('dimensions', {})
    full_dims = monthly_sheet_full.get('dimensions', {})
    
    print("Dimensions:")
    print(f"  Compact: {compact_dims}")
    print(f"  Full: {full_dims}")
    print()
    
    # Compare cell counts
    compact_cells = len(monthly_sheet_compact.get('cells', {}))
    full_cells = len(monthly_sheet_full.get('cells', {}))
    
    print("Cell Counts:")
    print(f"  Compact: {compact_cells} cells")
    print(f"  Full: {full_cells} cells")
    print()
    
    # Compare merged cells
    compact_merged = len(monthly_sheet_compact.get('merged_cells', []))
    full_merged = len(monthly_sheet_full.get('merged_cells', []))
    
    print("Merged Cells:")
    print(f"  Compact: {compact_merged} merged ranges")
    print(f"  Full: {full_merged} merged ranges")
    print()
    
    # Show sample merged cells
    if full_merged > 0:
        print("Sample merged cells from full processor:")
        for i, merge in enumerate(full_data['workbook']['sheets'][4].get('merged_cells', [])[:5]):
            print(f"  {i+1}. {merge}")
        print()
    
    # Analyze with both data formats
    complexity_analyzer = ExcelComplexityAnalyzer()
    
    print("🧮 Complexity Analysis Results:\n")
    
    # Analyze compact data
    compact_analysis = complexity_analyzer.analyze_sheet_complexity(monthly_sheet_compact)
    print("Compact Data Analysis:")
    print(f"  Score: {compact_analysis['complexity_score']:.3f}")
    print(f"  Metrics: {compact_analysis['metrics']}")
    print()
    
    # Analyze full data
    full_analysis = complexity_analyzer.analyze_sheet_complexity(monthly_sheet_full)
    print("Full Data Analysis:")
    print(f"  Score: {full_analysis['complexity_score']:.3f}")
    print(f"  Metrics: {full_analysis['metrics']}")
    print()
    
    # Debug specific metrics
    print("🔬 Detailed Metric Debug:\n")
    
    # Debug merged cell complexity
    print("Merged Cell Analysis:")
    merged_complexity_compact = complexity_analyzer._analyze_merged_cells(monthly_sheet_compact)
    merged_complexity_full = complexity_analyzer._analyze_merged_cells(monthly_sheet_full)
    
    data_cells_compact = complexity_analyzer._estimate_data_cell_count(monthly_sheet_compact)
    data_cells_full = complexity_analyzer._estimate_data_cell_count(monthly_sheet_full)
    
    print(f"  Compact: {merged_complexity_compact:.3f} (merges: {compact_merged}, data cells: {data_cells_compact})")
    print(f"  Full: {merged_complexity_full:.3f} (merges: {full_merged}, data cells: {data_cells_full})")
    print()
    
    # Debug sparsity
    print("Sparsity Analysis:")
    sparsity_compact = complexity_analyzer._analyze_data_sparsity(monthly_sheet_compact)
    sparsity_full = complexity_analyzer._analyze_data_sparsity(monthly_sheet_full)
    
    print(f"  Compact: {sparsity_compact:.3f}")
    print(f"  Full: {sparsity_full:.3f}")
    print()
    
    # Look at actual cell distribution in Monthly sheet
    print("📍 Cell Distribution Analysis:")
    
    full_cells_dict = monthly_sheet_full.get('cells', {})
    if full_cells_dict:
        # Extract row and column ranges
        rows = set()
        cols = set()
        
        for coord in full_cells_dict.keys():
            # Extract row number
            row_match = [c for c in coord if c.isdigit()]
            if row_match:
                row_num = int(''.join(row_match))
                rows.add(row_num)
            
            # Extract column
            col_match = [c for c in coord if c.isalpha()]
            if col_match:
                col_str = ''.join(col_match)
                cols.add(col_str)
        
        print(f"  Actual data spans: Rows {min(rows)}-{max(rows)}, Cols {min(cols)}-{max(cols)}")
        print(f"  Total coordinates with data: {len(full_cells_dict)}")
        print(f"  Declared dimensions: {full_dims}")
        
        # Calculate actual sparsity
        declared_cells = (full_dims.get('max_row', 1) - full_dims.get('min_row', 1) + 1) * \
                        (full_dims.get('max_col', 1) - full_dims.get('min_col', 1) + 1)
        actual_sparsity = 1.0 - (len(full_cells_dict) / declared_cells) if declared_cells > 0 else 0
        
        print(f"  Actual sparsity ratio: {actual_sparsity:.3f}")
        print()


def test_enhanced_analyzer():
    """Test an enhanced version of the analyzer that accounts for the compact format"""
    print("=== Testing Enhanced Analyzer ===\n")
    
    # Create a custom analyzer with debug output
    class DebugComplexityAnalyzer(ExcelComplexityAnalyzer):
        def _analyze_data_sparsity(self, sheet_data):
            dimensions = sheet_data.get('dimensions', {})
            cells = sheet_data.get('cells', {})
            
            print(f"  Debug sparsity analysis:")
            print(f"    Dimensions: {dimensions}")
            print(f"    Cell count: {len(cells)}")
            
            if not dimensions or not cells:
                return 0.0
            
            # Calculate addressable space
            total_addressable = (
                (dimensions.get('max_row', 1) - dimensions.get('min_row', 1) + 1) *
                (dimensions.get('max_col', 1) - dimensions.get('min_col', 1) + 1)
            )
            
            if total_addressable == 0:
                return 0.0
            
            # Calculate actual data cells
            data_cells = len([cell for cell in cells.values() 
                             if cell.get('value') is not None and str(cell.get('value', '')).strip()])
            
            sparsity_ratio = 1.0 - (data_cells / total_addressable)
            
            print(f"    Total addressable: {total_addressable}")
            print(f"    Data cells: {data_cells}")
            print(f"    Sparsity ratio: {sparsity_ratio:.3f}")
            
            complexity = 0.0
            
            # High sparsity contributes to complexity
            if sparsity_ratio > self.thresholds['sparsity_threshold']:
                excess_sparsity = sparsity_ratio - self.thresholds['sparsity_threshold']
                complexity += min(excess_sparsity * 0.4, 0.2)
                print(f"    Excess sparsity: {excess_sparsity:.3f} -> complexity: {complexity:.3f}")
            
            return min(complexity, 1.0)
    
    debug_analyzer = DebugComplexityAnalyzer()
    
    # Test with 360 Energy file
    file_path = "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx"
    
    if os.path.exists(file_path):
        full_processor = ExcelProcessor()
        full_data = full_processor.process_file(file_path)
        
        # Test with the "Monthly" sheet
        for sheet in full_data.get('workbook', {}).get('sheets', []):
            if sheet.get('name') == 'Monthly':
                print(f"Analyzing '{sheet.get('name')}' with debug analyzer:")
                analysis = debug_analyzer.analyze_sheet_complexity(sheet)
                print(f"Final score: {analysis['complexity_score']:.3f}")
                print(f"Recommendation: {analysis['recommendation']}")
                break


if __name__ == "__main__":
    try:
        debug_360_energy_file()
        print("\n" + "="*60 + "\n")
        test_enhanced_analyzer()
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()
