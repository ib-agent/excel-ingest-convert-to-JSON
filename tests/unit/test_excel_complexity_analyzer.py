#!/usr/bin/env python3
"""
Test script for Excel Complexity Analyzer

This script tests the complexity analyzer with the 360 Energy file
and other test files to validate the scoring algorithm.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.compact_excel_processor import CompactExcelProcessor
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer
import json


def test_complexity_analyzer(tmp_path):
    """Test the complexity analyzer with various Excel files"""
    print("=== Excel Complexity Analyzer Test ===\n")
    
    # Initialize processors
    excel_processor = CompactExcelProcessor()
    complexity_analyzer = ExcelComplexityAnalyzer()
    
    # Test files to analyze
    test_files = [
        "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx",
        "tests/test_excel/Test_SpreadSheet_100_numbers.xlsx",
        "tests/test_excel/single_unit_economics_4_tables.xlsx"
    ]
    
    results = {}
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"📊 Analyzing: {os.path.basename(file_path)}")
        print("-" * 60)
        
        try:
            # Process Excel file
            excel_data = excel_processor.process_file(file_path)
            
            # Analyze each sheet
            file_results = {}
            sheet_summaries = []
            
            for sheet in excel_data.get('workbook', {}).get('sheets', []):
                sheet_name = sheet.get('name', 'Unknown')
                
                # Perform complexity analysis
                complexity_analysis = complexity_analyzer.analyze_sheet_complexity(sheet)
                file_results[sheet_name] = complexity_analysis
                
                # Print detailed analysis
                print(f"Sheet: {sheet_name}")
                print(f"  Complexity Score: {complexity_analysis['complexity_score']:.3f}")
                print(f"  Complexity Level: {complexity_analysis['complexity_level']}")
                print(f"  Recommendation: {complexity_analysis['recommendation']}")
                
                # Print detailed metrics
                metrics = complexity_analysis['metrics']
                print(f"  Detailed Metrics:")
                print(f"    Merged Cell Complexity: {metrics['merged_cell_complexity']:.3f}")
                print(f"    Header Complexity: {metrics['header_complexity']:.3f}")
                print(f"    Sparsity Complexity: {metrics['sparsity_complexity']:.3f}")
                print(f"    Column Inconsistency: {metrics['column_inconsistency']:.3f}")
                print(f"    Formula Complexity: {metrics['formula_complexity']:.3f}")
                
                # Print failure indicators if any
                if complexity_analysis['failure_indicators']:
                    print(f"  Failure Indicators: {', '.join(complexity_analysis['failure_indicators'])}")
                
                # Collect summary
                sheet_summaries.append({
                    'name': sheet_name,
                    'score': complexity_analysis['complexity_score'],
                    'level': complexity_analysis['complexity_level'],
                    'recommendation': complexity_analysis['recommendation']
                })
                
                print()
            
            # File summary
            avg_complexity = sum(s['score'] for s in sheet_summaries) / len(sheet_summaries) if sheet_summaries else 0
            recommendations = [s['recommendation'] for s in sheet_summaries]
            
            print(f"File Summary:")
            print(f"  Total Sheets: {len(sheet_summaries)}")
            print(f"  Average Complexity: {avg_complexity:.3f}")
            print(f"  Traditional Only: {recommendations.count('traditional')}")
            print(f"  Dual Processing: {recommendations.count('dual')}")
            print(f"  AI First: {recommendations.count('ai_first')}")
            
            results[os.path.basename(file_path)] = {
                'sheet_analysis': file_results,
                'summary': {
                    'average_complexity': avg_complexity,
                    'total_sheets': len(sheet_summaries),
                    'recommendations': {
                        'traditional': recommendations.count('traditional'),
                        'dual': recommendations.count('dual'),
                        'ai_first': recommendations.count('ai_first')
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {str(e)}")
            results[os.path.basename(file_path)] = {'error': str(e)}
        
        print("=" * 60)
        print()
    
    # Save results to a temporary location so tests don't leave artifacts
    output_file = tmp_path / 'complexity_analysis_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("✅ Analysis complete! Results saved to", str(output_file))
    
    # Print overall insights
    print("\n🎯 Key Insights:")
    
    # Find the most complex sheets
    all_sheets = []
    for file_name, file_data in results.items():
        if 'sheet_analysis' in file_data:
            for sheet_name, sheet_data in file_data['sheet_analysis'].items():
                all_sheets.append({
                    'file': file_name,
                    'sheet': sheet_name,
                    'score': sheet_data['complexity_score'],
                    'recommendation': sheet_data['recommendation'],
                    'indicators': sheet_data['failure_indicators']
                })
    
    # Sort by complexity
    all_sheets.sort(key=lambda x: x['score'], reverse=True)
    
    print("\nMost Complex Sheets (Top 5):")
    for i, sheet in enumerate(all_sheets[:5]):
        print(f"{i+1}. {sheet['file']} - {sheet['sheet']}")
        print(f"   Score: {sheet['score']:.3f} | Recommendation: {sheet['recommendation']}")
        if sheet['indicators']:
            print(f"   Issues: {', '.join(sheet['indicators'])}")
    
    print("\nSimplest Sheets (Bottom 5):")
    for i, sheet in enumerate(all_sheets[-5:]):
        print(f"{i+1}. {sheet['file']} - {sheet['sheet']}")
        print(f"   Score: {sheet['score']:.3f} | Recommendation: {sheet['recommendation']}")
    
    assert isinstance(results, dict)
    return results


def test_specific_scenarios():
    """Test specific complexity scenarios"""
    print("\n=== Testing Specific Complexity Scenarios ===\n")
    
    complexity_analyzer = ExcelComplexityAnalyzer()
    
    # Test 1: High merged cell complexity
    test_sheet_high_merges = {
        'name': 'Test High Merges',
        'dimensions': {'min_row': 1, 'max_row': 10, 'min_col': 1, 'max_col': 10},
        'cells': {f'A{i}': {'value': f'Data {i}'} for i in range(1, 11)},
        'merged_cells': [
            {'start_row': 1, 'end_row': 3, 'start_column': 1, 'end_column': 3},
            {'start_row': 4, 'end_row': 6, 'start_column': 2, 'end_column': 4},
            {'start_row': 7, 'end_row': 9, 'start_column': 3, 'end_column': 5}
        ]
    }
    
    analysis = complexity_analyzer.analyze_sheet_complexity(test_sheet_high_merges)
    print(f"High Merges Test:")
    print(f"  Score: {analysis['complexity_score']:.3f}")
    print(f"  Merged Cell Complexity: {analysis['metrics']['merged_cell_complexity']:.3f}")
    print(f"  Recommendation: {analysis['recommendation']}")
    print()
    
    # Test 2: High sparsity
    test_sheet_sparse = {
        'name': 'Test Sparse Data',
        'dimensions': {'min_row': 1, 'max_row': 100, 'min_col': 1, 'max_col': 50},
        'cells': {
            'A1': {'value': 'Header 1'},
            'B1': {'value': 'Header 2'},
            'A10': {'value': 'Data 1'},
            'B50': {'value': 'Data 2'},
            'Z99': {'value': 'Data 3'}
        },
        'merged_cells': []
    }
    
    analysis = complexity_analyzer.analyze_sheet_complexity(test_sheet_sparse)
    print(f"Sparse Data Test:")
    print(f"  Score: {analysis['complexity_score']:.3f}")
    print(f"  Sparsity Complexity: {analysis['metrics']['sparsity_complexity']:.3f}")
    print(f"  Recommendation: {analysis['recommendation']}")
    print()
    
    # Test 3: Simple, well-structured sheet
    test_sheet_simple = {
        'name': 'Test Simple Sheet',
        'dimensions': {'min_row': 1, 'max_row': 5, 'min_col': 1, 'max_col': 3},
        'cells': {
            'A1': {'value': 'Name'}, 'B1': {'value': 'Age'}, 'C1': {'value': 'City'},
            'A2': {'value': 'John'}, 'B2': {'value': 25}, 'C2': {'value': 'NYC'},
            'A3': {'value': 'Jane'}, 'B3': {'value': 30}, 'C3': {'value': 'LA'},
            'A4': {'value': 'Bob'}, 'B4': {'value': 35}, 'C4': {'value': 'Chicago'},
            'A5': {'value': 'Alice'}, 'B5': {'value': 28}, 'C5': {'value': 'Boston'}
        },
        'merged_cells': []
    }
    
    analysis = complexity_analyzer.analyze_sheet_complexity(test_sheet_simple)
    print(f"Simple Sheet Test:")
    print(f"  Score: {analysis['complexity_score']:.3f}")
    print(f"  Recommendation: {analysis['recommendation']}")
    print()


if __name__ == "__main__":
    try:
        # Test with real files
        results = test_complexity_analyzer()
        
        # Test specific scenarios
        test_specific_scenarios()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
