#!/usr/bin/env python3
"""
Test script for Run-Length Encoding (RLE) compression in Excel processing

This script demonstrates the RLE compression capabilities on files with
very wide rows containing repeated values. RLE is now enabled by default
in CompactExcelProcessor.
"""

import json
import os
import sys
import time
from converter.compact_excel_processor import CompactExcelProcessor


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def analyze_row_patterns(sheet_data):
    """Analyze row patterns to identify repetition"""
    patterns = {}
    
    for row in sheet_data.get("rows", []):
        row_num = row.get("r", 0)
        cells = row.get("cells", [])
        
        if len(cells) > 10:  # Only analyze wide rows
            # Count unique values in the row
            values = []
            rle_cells = 0
            normal_cells = 0
            
            for cell in cells:
                if len(cell) >= 5 and isinstance(cell[-1], int):  # RLE cell
                    rle_cells += 1
                    run_length = cell[-1]
                    values.extend([cell[1]] * run_length)
                else:  # Normal cell
                    normal_cells += 1
                    if len(cell) > 1:
                        values.append(cell[1])
            
            unique_values = set(values)
            total_values = len(values)
            
            patterns[row_num] = {
                "total_logical_cells": total_values,
                "stored_cells": len(cells),
                "rle_cells": rle_cells,
                "normal_cells": normal_cells,
                "unique_values": len(unique_values),
                "compression_ratio": (1 - len(cells) / max(total_values, 1)) * 100,
                "sample_values": list(unique_values)[:5]
            }
    
    return patterns


def test_rle_compression(file_path: str = "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/fixtures/excel/Test_SpreadSheet_100_numbers.xlsx", enable_rle: bool = True):
    """Test RLE compression on a specific file"""
    print(f"\n{'='*80}")
    print(f"TESTING: {os.path.basename(file_path)}")
    print(f"RLE Enabled: {enable_rle}")
    print(f"{'='*80}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        pytest.skip("RLE test file not found")
    
    file_size = os.path.getsize(file_path)
    print(f"📁 File size: {format_file_size(file_size)}")
    
    try:
        # Initialize processor with RLE configuration optimized for wide sheets
        processor = CompactExcelProcessor(
            enable_rle=enable_rle,
            rle_min_run_length=2 if enable_rle else 3,  # More aggressive for this problematic file
            rle_max_row_width=10,  # Apply RLE to rows with > 10 cells
            rle_aggressive_none=True  # Aggressive compression for None values
        )
        
        print("🔄 Processing file...")
        start_time = time.time()
        
        result = processor.process_file(file_path, filter_empty_trailing=True)
        
        processing_time = time.time() - start_time
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        
        # Analyze results
        workbook = result.get("workbook", {})
        sheets = workbook.get("sheets", [])
        
        print(f"\n📊 ANALYSIS:")
        print(f"   Sheets processed: {len(sheets)}")
        
        total_rows = 0
        total_stored_cells = 0
        total_logical_cells = 0
        
        for i, sheet in enumerate(sheets):
            sheet_name = sheet.get("name", f"Sheet{i+1}")
            dimensions = sheet.get("dimensions", [0, 0, 0, 0])
            rows = sheet.get("rows", [])
            
            print(f"\n   📄 Sheet: {sheet_name}")
            print(f"      Dimensions: {dimensions[0]}:{dimensions[1]} to {dimensions[2]}:{dimensions[3]}")
            print(f"      Rows with data: {len(rows)}")
            
            if rows:
                # Analyze row patterns
                patterns = analyze_row_patterns(sheet)
                
                sheet_stored_cells = sum(len(row.get("cells", [])) for row in rows)
                total_stored_cells += sheet_stored_cells
                total_rows += len(rows)
                
                print(f"      Total stored cells: {sheet_stored_cells}")
                
                # Show patterns for interesting rows
                interesting_rows = {k: v for k, v in patterns.items() 
                                  if v["total_logical_cells"] > 50 or v["rle_cells"] > 0}
                
                if interesting_rows:
                    print(f"      🔍 Interesting rows with patterns:")
                    for row_num, pattern in list(interesting_rows.items())[:5]:  # Show first 5
                        logical = pattern["total_logical_cells"]
                        stored = pattern["stored_cells"]
                        rle = pattern["rle_cells"]
                        unique = pattern["unique_values"]
                        compression = pattern["compression_ratio"]
                        
                        print(f"         Row {row_num}: {logical} logical → {stored} stored cells "
                              f"({rle} RLE) | {unique} unique values | {compression:.1f}% compression")
                        
                        if pattern["sample_values"]:
                            sample = pattern["sample_values"]
                            print(f"                   Sample values: {sample}")
                
                # Calculate logical cells for this sheet
                sheet_logical_cells = 0
                for row in rows:
                    for cell in row.get("cells", []):
                        if len(cell) >= 5 and isinstance(cell[-1], int):  # RLE cell
                            sheet_logical_cells += cell[-1]  # run_length
                        else:
                            sheet_logical_cells += 1
                
                total_logical_cells += sheet_logical_cells
                print(f"      Total logical cells: {sheet_logical_cells}")
        
        # Show RLE compression statistics
        if enable_rle and "rle_compression" in result:
            rle_stats = result["rle_compression"]
            print(f"\n🗜️  RLE COMPRESSION STATS:")
            print(f"   Rows compressed: {rle_stats['rows_compressed']}")
            print(f"   RLE runs created: {rle_stats['runs_created']}")
            print(f"   Cells before RLE: {rle_stats['cells_before_rle']}")
            print(f"   Cells after RLE: {rle_stats['cells_after_rle']}")
            print(f"   Compression ratio: {rle_stats['compression_ratio_percent']:.2f}%")
            
            if rle_stats['cells_before_rle'] > 0:
                size_reduction = rle_stats['cells_before_rle'] - rle_stats['cells_after_rle']
                print(f"   Cells saved: {size_reduction}")
        
        # Estimate JSON sizes
        json_str = json.dumps(result, separators=(',', ':'))
        json_size = len(json_str.encode('utf-8'))
        
        print(f"\n💾 OUTPUT ESTIMATES:")
        print(f"   JSON size: {format_file_size(json_size)}")
        print(f"   Total logical cells: {total_logical_cells}")
        print(f"   Total stored cells: {total_stored_cells}")
        
        if total_logical_cells > 0:
            overall_compression = (1 - total_stored_cells / total_logical_cells) * 100
            print(f"   Overall cell compression: {overall_compression:.2f}%")
        
        # Basic assertions to validate output
        assert isinstance(result, dict)
        assert "workbook" in result
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_rle_vs_no_rle(file_path):
    """Compare processing with and without RLE"""
    print(f"\n{'🔬 COMPARISON: RLE vs NO-RLE':^80}")
    print("="*80)
    
    # Test without RLE
    print("Testing WITHOUT RLE...")
    result_no_rle = test_rle_compression(file_path, enable_rle=False)
    
    # Test with RLE
    print("\nTesting WITH RLE...")
    result_with_rle = test_rle_compression(file_path, enable_rle=True)
    
    if result_no_rle and result_with_rle:
        print(f"\n{'COMPARISON SUMMARY':^80}")
        print("="*80)
        
        # Processing time
        time_no_rle = result_no_rle["processing_time"]
        time_with_rle = result_with_rle["processing_time"]
        time_diff = ((time_with_rle - time_no_rle) / time_no_rle) * 100
        
        print(f"⏱️  Processing Time:")
        print(f"   Without RLE: {time_no_rle:.2f}s")
        print(f"   With RLE:    {time_with_rle:.2f}s")
        print(f"   Difference:  {time_diff:+.1f}%")
        
        # JSON size
        size_no_rle = result_no_rle["json_size"]
        size_with_rle = result_with_rle["json_size"]
        size_reduction = ((size_no_rle - size_with_rle) / size_no_rle) * 100
        
        print(f"\n💾 JSON Output Size:")
        print(f"   Without RLE: {format_file_size(size_no_rle)}")
        print(f"   With RLE:    {format_file_size(size_with_rle)}")
        print(f"   Reduction:   {size_reduction:.1f}%")
        
        # Cell storage
        cells_no_rle = result_no_rle["total_stored_cells"]
        cells_with_rle = result_with_rle["total_stored_cells"]
        cell_reduction = ((cells_no_rle - cells_with_rle) / cells_no_rle) * 100 if cells_no_rle > 0 else 0
        
        print(f"\n🗃️  Cell Storage:")
        print(f"   Without RLE: {cells_no_rle} cells stored")
        print(f"   With RLE:    {cells_with_rle} cells stored")
        print(f"   Reduction:   {cell_reduction:.1f}%")
        
        # RLE specific stats
        if result_with_rle["rle_stats"]:
            rle_stats = result_with_rle["rle_stats"]
            print(f"\n🗜️  RLE Impact:")
            print(f"   Runs created: {rle_stats.get('runs_created', 0)}")
            print(f"   Rows compressed: {rle_stats.get('rows_compressed', 0)}")
            print(f"   Cell compression: {rle_stats.get('compression_ratio_percent', 0):.2f}%")


def main():
    """Main test function"""
    print("🧪 RUN-LENGTH ENCODING TEST SUITE")
    print("="*80)
    
    # Test files
    test_files = [
        "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/test_excel/pDD10abc_InDebted_10. NEW___ InDebted_Financial_Model.xlsx"
    ]
    
    # Additional test files (if they exist)
    additional_files = [
        "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx",
        "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/test_excel/Test_SpreadSheet_100_numbers.xlsx"
    ]
    
    for file_path in additional_files:
        if os.path.exists(file_path):
            test_files.append(file_path)
    
    if not test_files:
        print("❌ No test files found!")
        return
    
    # Test each file
    for file_path in test_files:
        if os.path.exists(file_path):
            compare_rle_vs_no_rle(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n{'✅ TESTING COMPLETE':^80}")
    print("="*80)


if __name__ == "__main__":
    main()
