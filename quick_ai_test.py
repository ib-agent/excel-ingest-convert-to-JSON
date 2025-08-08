#!/usr/bin/env python3
"""
Quick AI Integration Test

This script demonstrates the AI integration with a single sheet to show
the comparison capabilities in action.
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.anthropic_excel_client import AnthropicExcelClient
from converter.ai_result_parser import AIResultParser
from converter.comparison_engine import ComparisonEngine
from converter.complexity_preserving_compact_processor import ComplexityPreservingCompactProcessor
from converter.compact_table_processor import CompactTableProcessor
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer


def test_single_file(file_path="tests/test_excel/single_unit_economics_4_tables.xlsx"):
    """Test AI integration with a single Excel file."""
    
    print("🧪 QUICK AI INTEGRATION TEST")
    print("="*40)
    print(f"📄 Testing file: {os.path.basename(file_path)}\n")
    
    # Initialize components
    ai_client = AnthropicExcelClient()
    ai_parser = AIResultParser()
    comparison_engine = ComparisonEngine()
    processor = ComplexityPreservingCompactProcessor(enable_rle=True)
    table_processor = CompactTableProcessor()
    complexity_analyzer = ExcelComplexityAnalyzer()
    
    if not ai_client.is_available():
        print("❌ AI client not available. Make sure to:")
        print("   1. source load_config.sh")
        print("   2. Set ANTHROPIC_API_KEY")
        return
    
    try:
        # 1. Process file
        print("1️⃣ Processing Excel file...")
        json_data = processor.process_file(file_path, include_complexity_metadata=True)
        print(f"   ✅ Found {len(json_data['workbook']['sheets'])} sheets")
        
        # Use first sheet for demonstration
        sheet = json_data['workbook']['sheets'][0]
        sheet_name = sheet.get('name', 'Sheet1')
        
        print(f"   📊 Analyzing sheet: '{sheet_name}'")
        
        # 2. Complexity analysis
        print("\n2️⃣ Complexity analysis...")
        complexity_metadata_dict = json_data.get('complexity_metadata', {}).get('sheets', {})
        sheet_complexity_metadata = complexity_metadata_dict.get(sheet_name)
        
        complexity_analysis = complexity_analyzer.analyze_sheet_complexity(
            sheet, 
            complexity_metadata=sheet_complexity_metadata
        )
        
        print(f"   📈 Complexity Score: {complexity_analysis['complexity_score']:.3f}")
        print(f"   🎯 Complexity Level: {complexity_analysis['complexity_level']}")
        print(f"   💡 Recommendation: {complexity_analysis['recommendation']}")
        
        # 3. Traditional analysis
        print("\n3️⃣ Traditional heuristic analysis...")
        traditional_result = table_processor.transform_to_compact_table_format(
            {'workbook': {'sheets': [sheet]}}, 
            {}
        )
        
        traditional_tables = traditional_result.get('workbook', {}).get('sheets', [{}])[0].get('tables', [])
        print(f"   🔧 Traditional tables found: {len(traditional_tables)}")
        
        for i, table in enumerate(traditional_tables[:3]):  # Show first 3
            print(f"      Table {i+1}: {table.get('table_name', 'Unnamed')} "
                  f"({table.get('start_row', 0)}-{table.get('end_row', 0)})")
        
        # 4. AI analysis
        print("\n4️⃣ AI analysis...")
        
        # Cost estimation
        cost_estimate = ai_client.estimate_api_cost(sheet)
        print(f"   💰 Estimated cost: ${cost_estimate['estimated_cost_usd']:.4f}")
        
        # Perform AI analysis
        print("   🤖 Calling Anthropic API...")
        ai_raw_response = ai_client.analyze_excel_tables(
            sheet, 
            complexity_metadata=complexity_analysis,
            analysis_focus="comprehensive"
        )
        
        # Parse AI response
        ai_result = ai_parser.parse_excel_analysis(ai_raw_response)
        
        ai_tables_count = ai_result.get('table_count', 0)
        ai_confidence = ai_result.get('ai_analysis', {}).get('confidence', 0.0)
        ai_valid = ai_result.get('validation', {}).get('valid', False)
        
        print(f"   🤖 AI tables found: {ai_tables_count}")
        print(f"   🎯 AI confidence: {ai_confidence:.3f}")
        print(f"   ✅ Response valid: {ai_valid}")
        
        if ai_result.get('ai_analysis', {}).get('tables'):
            for i, table in enumerate(ai_result['ai_analysis']['tables'][:3]):
                boundaries = table.get('boundaries', {})
                print(f"      AI Table {i+1}: {table.get('name', 'Unnamed')} "
                      f"({boundaries.get('start_row', 0)}-{boundaries.get('end_row', 0)})")
        
        # 5. Comparison analysis
        print("\n5️⃣ Comparison analysis...")
        comparison_result = comparison_engine.compare_analysis_results(
            traditional_result={'tables': traditional_tables},
            ai_result=ai_result,
            complexity_metadata=complexity_analysis,
            sheet_name=sheet_name
        )
        
        summary = comparison_result['summary']
        metrics = comparison_result['metrics']
        
        print(f"   ⚖️  Winner: {summary['winner']}")
        print(f"   🤝 Agreement Score: {metrics['agreement_score']:.3f}")
        print(f"   📊 Complexity Level: {summary['complexity_level']}")
        
        # Test case potential
        test_case = comparison_result['test_case_potential']
        print(f"   🧪 Test Case Value: {test_case['test_case_type']} (score: {test_case['potential_score']:.2f})")
        
        # Key insights
        if comparison_result['insights']:
            print(f"   💡 Key Insight: {comparison_result['insights'][0]}")
        
        # 6. Summary and recommendations
        print(f"\n6️⃣ Summary and Recommendations")
        print("="*40)
        
        print(f"📊 RESULTS COMPARISON:")
        print(f"   Traditional: {len(traditional_tables)} tables")
        print(f"   AI: {ai_tables_count} tables (confidence: {ai_confidence:.1%})")
        print(f"   Agreement: {metrics['agreement_score']:.1%}")
        print(f"   Winner: {summary['winner']}")
        
        print(f"\n💰 COST ANALYSIS:")
        actual_cost = ai_result.get('metadata', {}).get('ai_metadata', {}).get('total_tokens', 0) * 0.000003  # Rough calculation
        print(f"   Estimated: ${cost_estimate['estimated_cost_usd']:.4f}")
        print(f"   Tokens Used: {ai_result.get('metadata', {}).get('ai_metadata', {}).get('total_tokens', 0):,}")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        if complexity_analysis['complexity_score'] > 0.7:
            print("   • High complexity - AI analysis recommended")
        elif complexity_analysis['complexity_score'] > 0.3:
            print("   • Moderate complexity - dual analysis valuable for comparison")
        else:
            print("   • Low complexity - traditional methods likely sufficient")
        
        if metrics['agreement_score'] < 0.3:
            print("   • Low agreement - excellent for test case generation")
        elif metrics['agreement_score'] > 0.8:
            print("   • High agreement - both methods aligned")
        
        print(f"\n✅ Test completed successfully!")
        
        return {
            'complexity_score': complexity_analysis['complexity_score'],
            'traditional_tables': len(traditional_tables),
            'ai_tables': ai_tables_count,
            'ai_confidence': ai_confidence,
            'agreement_score': metrics['agreement_score'],
            'winner': summary['winner'],
            'cost': cost_estimate['estimated_cost_usd'],
            'test_case_value': test_case['test_case_type']
        }
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run the quick test."""
    
    # Test with different files if available
    test_files = [
        "tests/test_excel/single_unit_economics_4_tables.xlsx",
        "tests/test_excel/Test_SpreadSheet_100_numbers.xlsx",
        "tests/test_excel/Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles.xlsx"
    ]
    
    print("🚀 QUICK AI INTEGRATION TESTS")
    print("="*50 + "\n")
    
    results = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"Testing: {os.path.basename(file_path)}")
            result = test_single_file(file_path)
            if result:
                result['file'] = os.path.basename(file_path)
                results.append(result)
            print("\n" + "-"*50 + "\n")
            break  # Test just one for now
        else:
            print(f"⚠️  File not found: {file_path}")
    
    if results:
        print("📋 QUICK TEST SUMMARY:")
        for result in results:
            print(f"   {result['file']}: {result['winner']} (agreement: {result['agreement_score']:.2f})")


if __name__ == "__main__":
    main()
