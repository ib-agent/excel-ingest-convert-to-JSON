#!/usr/bin/env python3
"""
Compression Impact Analysis

This script analyzes how much compression we would lose if we only used
run-length encoding vs. the current filtering approach, and identifies
what complexity information is being lost.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.compact_excel_processor import CompactExcelProcessor
from converter.excel_processor import ExcelProcessor
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer
import json


def analyze_compression_strategies():
    """Analyze different compression strategies and their impact"""
    print("=== Compression Strategy Analysis ===\n")
    
    file_path = "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📊 Analyzing: {os.path.basename(file_path)}\n")
    
    # Strategy 1: Full processor (no compression)
    print("1️⃣ Full Processor (No Compression)")
    full_processor = ExcelProcessor()
    full_data = full_processor.process_file(file_path)
    full_size = len(json.dumps(full_data, default=str))
    print(f"   Size: {full_size:,} bytes ({full_size/1024/1024:.2f} MB)")
    
    # Strategy 2: Compact processor with filtering (current)
    print("\n2️⃣ Compact Processor with Filtering (Current)")
    compact_processor = CompactExcelProcessor(enable_rle=True)
    compact_data = compact_processor.process_file(file_path, filter_empty_trailing=True)
    compact_size = len(json.dumps(compact_data, default=str))
    compact_reduction = (1 - compact_size/full_size) * 100
    print(f"   Size: {compact_size:,} bytes ({compact_size/1024/1024:.2f} MB)")
    print(f"   Reduction: {compact_reduction:.1f}%")
    
    # Strategy 3: Compact processor without filtering
    print("\n3️⃣ Compact Processor without Filtering")
    compact_no_filter_data = compact_processor.process_file(file_path, filter_empty_trailing=False)
    compact_no_filter_size = len(json.dumps(compact_no_filter_data, default=str))
    no_filter_reduction = (1 - compact_no_filter_size/full_size) * 100
    print(f"   Size: {compact_no_filter_size:,} bytes ({compact_no_filter_size/1024/1024:.2f} MB)")
    print(f"   Reduction: {no_filter_reduction:.1f}%")
    
    # Strategy 4: RLE only (disable filtering, keep RLE)
    print("\n4️⃣ RLE Only (No Filtering)")
    rle_only_processor = CompactExcelProcessor(enable_rle=True)
    rle_only_data = rle_only_processor.process_file(file_path, filter_empty_trailing=False)
    rle_only_size = len(json.dumps(rle_only_data, default=str))
    rle_only_reduction = (1 - rle_only_size/full_size) * 100
    print(f"   Size: {rle_only_size:,} bytes ({rle_only_size/1024/1024:.2f} MB)")
    print(f"   Reduction: {rle_only_reduction:.1f}%")
    
    # Strategy 5: No compression at all (baseline)
    print("\n5️⃣ No Compression (Baseline)")
    no_rle_processor = CompactExcelProcessor(enable_rle=False)
    no_rle_data = no_rle_processor.process_file(file_path, filter_empty_trailing=False)
    no_rle_size = len(json.dumps(no_rle_data, default=str))
    no_rle_reduction = (1 - no_rle_size/full_size) * 100
    print(f"   Size: {no_rle_size:,} bytes ({no_rle_size/1024/1024:.2f} MB)")
    print(f"   Reduction: {no_rle_reduction:.1f}%")
    
    print("\n" + "="*60)
    print("📈 COMPRESSION SUMMARY")
    print("="*60)
    
    strategies = [
        ("Full Processor", full_size, 0),
        ("Compact + Filtering", compact_size, compact_reduction),
        ("Compact No Filter", compact_no_filter_size, no_filter_reduction),
        ("RLE Only", rle_only_size, rle_only_reduction),
        ("No Compression", no_rle_size, no_rle_reduction)
    ]
    
    for name, size, reduction in strategies:
        print(f"{name:20} | {size:>10,} bytes | {reduction:>6.1f}% reduction")
    
    # Calculate the cost of different approaches
    print("\n💰 Compression Cost Analysis:")
    filtering_cost = compact_no_filter_size - compact_size
    print(f"Cost of filtering: {filtering_cost:,} bytes ({filtering_cost/compact_no_filter_size*100:.1f}% of unfiltered)")
    
    rle_benefit = no_rle_size - rle_only_size
    print(f"Benefit of RLE: {rle_benefit:,} bytes ({rle_benefit/no_rle_size*100:.1f}% of uncompressed)")
    
    return {
        'strategies': strategies,
        'filtering_cost': filtering_cost,
        'rle_benefit': rle_benefit,
        'data_sets': {
            'full': full_data,
            'compact_filtered': compact_data,
            'compact_unfiltered': compact_no_filter_data,
            'rle_only': rle_only_data
        }
    }


def analyze_complexity_preservation():
    """Analyze how different compression strategies affect complexity detection"""
    print("\n=== Complexity Preservation Analysis ===\n")
    
    file_path = "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    # Get different versions of the data
    full_processor = ExcelProcessor()
    full_data = full_processor.process_file(file_path)
    
    compact_processor = CompactExcelProcessor(enable_rle=True)
    compact_filtered = compact_processor.process_file(file_path, filter_empty_trailing=True)
    compact_unfiltered = compact_processor.process_file(file_path, filter_empty_trailing=False)
    
    # Analyze complexity for each version
    complexity_analyzer = ExcelComplexityAnalyzer()
    
    print("🔍 Complexity Analysis by Processing Method:\n")
    
    # Focus on the "Monthly" sheet which should be most complex
    monthly_sheets = {}
    
    # Find Monthly sheet in each dataset
    for name, dataset in [("Full", full_data), ("Compact Filtered", compact_filtered), ("Compact Unfiltered", compact_unfiltered)]:
        for sheet in dataset.get('workbook', {}).get('sheets', []):
            if sheet.get('name') == 'Monthly':
                monthly_sheets[name] = sheet
                break
    
    complexity_results = {}
    
    for method_name, sheet_data in monthly_sheets.items():
        if sheet_data:
            analysis = complexity_analyzer.analyze_sheet_complexity(sheet_data)
            complexity_results[method_name] = analysis
            
            print(f"{method_name}:")
            print(f"  Complexity Score: {analysis['complexity_score']:.3f}")
            print(f"  Recommendation: {analysis['recommendation']}")
            print(f"  Metrics:")
            for metric, value in analysis['metrics'].items():
                print(f"    {metric}: {value:.3f}")
            
            # Show data preservation details
            cells = sheet_data.get('cells', {})
            dimensions = sheet_data.get('dimensions', {})
            merged_cells = sheet_data.get('merged_cells', [])
            
            print(f"  Data Details:")
            print(f"    Cells: {len(cells)}")
            print(f"    Dimensions: {dimensions}")
            print(f"    Merged Cells: {len(merged_cells)}")
            print()
    
    # Compare complexity preservation
    print("🎯 Complexity Preservation Summary:")
    
    if 'Full' in complexity_results and 'Compact Filtered' in complexity_results:
        full_score = complexity_results['Full']['complexity_score']
        filtered_score = complexity_results['Compact Filtered']['complexity_score']
        preservation_rate = (filtered_score / full_score * 100) if full_score > 0 else 100
        
        print(f"Filtering preserves {preservation_rate:.1f}% of complexity score")
        
        if preservation_rate < 50:
            print("⚠️  WARNING: Significant complexity information lost due to filtering!")
        elif preservation_rate < 80:
            print("⚠️  CAUTION: Some complexity information lost due to filtering")
        else:
            print("✅ Good complexity preservation with filtering")
    
    return complexity_results


def analyze_specific_data_loss():
    """Analyze what specific data is being lost in the compact representation"""
    print("\n=== Specific Data Loss Analysis ===\n")
    
    file_path = "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    # Get both representations
    full_processor = ExcelProcessor()
    full_data = full_processor.process_file(file_path)
    
    compact_processor = CompactExcelProcessor(enable_rle=True)
    compact_data = compact_processor.process_file(file_path, filter_empty_trailing=True)
    compact_unfiltered = compact_processor.process_file(file_path, filter_empty_trailing=False)
    
    # Focus on Monthly sheet
    full_monthly = None
    compact_monthly = None
    unfiltered_monthly = None
    
    for sheet in full_data.get('workbook', {}).get('sheets', []):
        if sheet.get('name') == 'Monthly':
            full_monthly = sheet
            break
    
    for sheet in compact_data.get('workbook', {}).get('sheets', []):
        if sheet.get('name') == 'Monthly':
            compact_monthly = sheet
            break
    
    for sheet in compact_unfiltered.get('workbook', {}).get('sheets', []):
        if sheet.get('name') == 'Monthly':
            unfiltered_monthly = sheet
            break
    
    if not all([full_monthly, compact_monthly, unfiltered_monthly]):
        print("❌ Could not find Monthly sheet in all datasets")
        return
    
    print("📊 Data Loss Analysis for Monthly Sheet:\n")
    
    # Compare dimensions
    full_dims = full_monthly.get('dimensions', {})
    compact_dims = compact_monthly.get('dimensions', [])
    unfiltered_dims = unfiltered_monthly.get('dimensions', [])
    
    print("Dimensions Comparison:")
    print(f"  Full:       {full_dims}")
    print(f"  Filtered:   {compact_dims}")
    print(f"  Unfiltered: {unfiltered_dims}")
    
    # Calculate addressable space
    if isinstance(full_dims, dict):
        full_addressable = (full_dims.get('max_row', 1) - full_dims.get('min_row', 1) + 1) * \
                          (full_dims.get('max_col', 1) - full_dims.get('min_col', 1) + 1)
    else:
        full_addressable = 0
    
    if len(compact_dims) >= 4:
        compact_addressable = (compact_dims[2] - compact_dims[0] + 1) * (compact_dims[3] - compact_dims[1] + 1)
    else:
        compact_addressable = 0
    
    print(f"\nAddressable Space:")
    print(f"  Full:     {full_addressable:,} cells")
    print(f"  Filtered: {compact_addressable:,} cells")
    print(f"  Reduction: {(1 - compact_addressable/full_addressable)*100:.1f}%" if full_addressable > 0 else "  Reduction: N/A")
    
    # Compare cell counts
    full_cells = len(full_monthly.get('cells', {}))
    compact_cells = 0
    
    # Count cells in compact format
    for row in compact_monthly.get('rows', []):
        compact_cells += len(row.get('cells', []))
    
    print(f"\nActual Data Cells:")
    print(f"  Full:     {full_cells:,} cells")
    print(f"  Filtered: {compact_cells:,} cells")
    print(f"  Lost:     {full_cells - compact_cells:,} cells ({(1 - compact_cells/full_cells)*100:.1f}%)" if full_cells > 0 else "  Lost: N/A")
    
    # Analyze what types of data are lost
    print(f"\nData Types in Full Format:")
    
    full_cell_dict = full_monthly.get('cells', {})
    type_counts = {'string': 0, 'number': 0, 'formula': 0, 'empty': 0, 'other': 0}
    
    for cell_data in full_cell_dict.values():
        value = cell_data.get('value')
        formula = cell_data.get('formula')
        
        if formula:
            type_counts['formula'] += 1
        elif value is None or (isinstance(value, str) and not value.strip()):
            type_counts['empty'] += 1
        elif isinstance(value, str):
            type_counts['string'] += 1
        elif isinstance(value, (int, float)):
            type_counts['number'] += 1
        else:
            type_counts['other'] += 1
    
    for data_type, count in type_counts.items():
        percentage = (count / full_cells * 100) if full_cells > 0 else 0
        print(f"  {data_type.capitalize()}: {count:,} ({percentage:.1f}%)")
    
    return {
        'full_addressable': full_addressable,
        'compact_addressable': compact_addressable,
        'full_cells': full_cells,
        'compact_cells': compact_cells,
        'type_counts': type_counts
    }


def recommend_optimal_strategy():
    """Recommend the optimal compression strategy"""
    print("\n=== Optimal Strategy Recommendation ===\n")
    
    # Run all analyses
    compression_results = analyze_compression_strategies()
    complexity_results = analyze_complexity_preservation()
    data_loss_results = analyze_specific_data_loss()
    
    print("🎯 RECOMMENDATIONS:\n")
    
    # Check if filtering causes significant complexity loss
    if 'Full' in complexity_results and 'Compact Filtered' in complexity_results:
        full_score = complexity_results['Full']['complexity_score']
        filtered_score = complexity_results['Compact Filtered']['complexity_score']
        
        if full_score > 0:
            complexity_preservation = filtered_score / full_score * 100
            
            if complexity_preservation < 50:
                print("❌ CRITICAL: Current filtering loses too much complexity information!")
                print("   Recommendation: Use RLE-only approach for complexity analysis")
                print("   Then apply selective filtering that preserves complexity indicators")
            elif complexity_preservation < 80:
                print("⚠️  WARNING: Some complexity information is lost")
                print("   Recommendation: Enhance filtering to preserve complexity-relevant data")
            else:
                print("✅ Current approach preserves complexity well")
        else:
            print("ℹ️  No complexity detected in test file")
    
    # Analyze compression efficiency
    if compression_results:
        strategies = compression_results['strategies']
        filtering_cost = compression_results['filtering_cost']
        rle_benefit = compression_results['rle_benefit']
        
        print(f"\n📊 Compression Efficiency:")
        print(f"   RLE provides {rle_benefit/1024/1024:.1f} MB reduction")
        print(f"   Filtering provides additional {filtering_cost/1024/1024:.1f} MB reduction")
        
        # Calculate efficiency ratio
        if filtering_cost > 0:
            efficiency_ratio = rle_benefit / filtering_cost
            print(f"   RLE is {efficiency_ratio:.1f}x more efficient than filtering")
            
            if efficiency_ratio > 5:
                print("   💡 INSIGHT: RLE provides most compression benefit")
                print("      Consider focusing on RLE optimization over aggressive filtering")
    
    print(f"\n🏆 FINAL RECOMMENDATION:")
    print(f"   1. Use RLE for primary compression (excellent size reduction)")
    print(f"   2. Preserve complexity-relevant data during filtering:")
    print(f"      - Keep merged cell information")
    print(f"      - Preserve header structure indicators")
    print(f"      - Maintain sparsity patterns for complexity analysis")
    print(f"   3. Apply filtering selectively - remove true empty trailing areas only")
    print(f"   4. Use full Excel processor for complexity analysis when needed")


if __name__ == "__main__":
    try:
        recommend_optimal_strategy()
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
