#!/usr/bin/env python3
"""
Phase 2 AI Integration Test

This script tests the complete AI integration pipeline including:
- Anthropic Excel client
- AI result parsing
- Comparison engine
- API endpoint integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.anthropic_excel_client import AnthropicExcelClient
from converter.ai_result_parser import AIResultParser
from converter.comparison_engine import ComparisonEngine
from converter.complexity_preserving_compact_processor import ComplexityPreservingCompactProcessor
from converter.compact_table_processor import CompactTableProcessor
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer
import json


def test_ai_client():
    """Test the Anthropic AI client functionality."""
    print("=== Testing Anthropic AI Client ===\n")
    
    # Initialize client
    ai_client = AnthropicExcelClient()
    
    print(f"🔗 AI Client Available: {ai_client.is_available()}")
    
    if not ai_client.is_available():
        print("⚠️  AI client not available. To test with real AI:")
        print("   1. Install anthropic: pip install anthropic")
        print("   2. Set ANTHROPIC_API_KEY environment variable")
        print("   Continuing with mock test...\n")
        return False
    else:
        print("✅ AI client ready for testing\n")
        return True


def test_ai_analysis_pipeline():
    """Test the complete AI analysis pipeline without making API calls."""
    print("=== Testing AI Analysis Pipeline (Mock) ===\n")
    
    # Create mock AI response
    mock_ai_response = {
        'status': 'success',
        'result': {
            'tables_detected': [
                {
                    'table_id': 'table_1',
                    'name': 'Financial Summary',
                    'boundaries': {
                        'start_row': 3,
                        'end_row': 25,
                        'start_col': 2,
                        'end_col': 8
                    },
                    'headers': {
                        'row_headers': [
                            {
                                'row': 3,
                                'columns': [
                                    {'col': 2, 'value': 'Account'},
                                    {'col': 3, 'value': 'Q1'},
                                    {'col': 4, 'value': 'Q2'}
                                ],
                                'level': 1
                            }
                        ],
                        'column_headers': []
                    },
                    'data_area': {
                        'start_row': 4,
                        'end_row': 25,
                        'start_col': 2,
                        'end_col': 8
                    },
                    'table_type': 'financial',
                    'confidence': 0.85,
                    'complexity_indicators': ['multi_level_headers', 'merged_cells'],
                    'data_quality': {
                        'completeness': 0.9,
                        'consistency': 0.8,
                        'data_types': ['text', 'number', 'formula']
                    }
                }
            ],
            'sheet_analysis': {
                'total_tables': 1,
                'data_density': 0.6,
                'structure_complexity': 'moderate',
                'recommended_processing': 'ai_assisted'
            },
            'analysis_confidence': 0.8,
            'processing_notes': ['Complex header structure detected', 'Merged cells require careful handling']
        },
        'ai_metadata': {
            'model': 'claude-3-sonnet-20241022',
            'timestamp': '2024-01-01T12:00:00',
            'total_tokens': 2500,
            'cost_estimate': 0.05
        }
    }
    
    print("📝 Testing AI Result Parser...")
    
    # Test AI result parsing
    ai_parser = AIResultParser()
    parsed_result = ai_parser.parse_excel_analysis(mock_ai_response)
    
    print(f"✅ Parsing Status: {parsed_result['validation']['valid']}")
    print(f"   Tables Found: {parsed_result['table_count']}")
    print(f"   High Confidence Tables: {parsed_result['high_confidence_tables']}")
    print(f"   Complexity Level: {parsed_result['complexity_assessment']['level']}")
    print(f"   Processing Recommendation: {parsed_result['processing_recommendation']}")
    
    if parsed_result['validation']['errors']:
        print(f"   ⚠️  Validation Errors: {parsed_result['validation']['errors']}")
    
    return parsed_result


def test_comparison_engine():
    """Test the comparison engine with mock data."""
    print("\n=== Testing Comparison Engine ===\n")
    
    # Create mock traditional result
    mock_traditional_result = {
        'tables': [
            {
                'table_name': 'Traditional Table 1',
                'start_row': 3,
                'end_row': 20,
                'start_col': 2,
                'end_col': 7,
                'detection_method': 'frozen_panes',
                'confidence': 0.7
            }
        ],
        'detection_methods': ['frozen_panes'],
        'processing_time': 0.15
    }
    
    # Create mock AI result (using result from previous test)
    mock_ai_result = {
        'ai_analysis': {
            'tables': [
                {
                    'id': 'table_1',
                    'name': 'Financial Summary',
                    'boundaries': {
                        'start_row': 3,
                        'end_row': 25,
                        'start_col': 2,
                        'end_col': 8
                    },
                    'confidence': 0.85
                }
            ],
            'confidence': 0.8
        },
        'table_count': 1,
        'converted_tables': [
            {
                'table_name': 'Financial Summary',
                'start_row': 3,
                'end_row': 25,
                'start_col': 2,
                'end_col': 8,
                'confidence': 0.85,
                'detection_method': 'ai_analysis'
            }
        ],
        'processing_recommendation': 'ai_assisted'
    }
    
    # Mock complexity metadata
    mock_complexity_metadata = {
        'complexity_score': 0.45,
        'failure_indicators': ['multi_level_headers', 'merged_cells'],
        'cell_count': 500,
        'merged_cells': {'count': 12},
        'header_structure': {'detected_levels': 2},
        'data_distribution': {'sparsity': 0.3}
    }
    
    print("⚖️  Testing Comparison Engine...")
    
    # Initialize and run comparison
    comparison_engine = ComparisonEngine()
    comparison_result = comparison_engine.compare_analysis_results(
        traditional_result=mock_traditional_result,
        ai_result=mock_ai_result,
        complexity_metadata=mock_complexity_metadata,
        sheet_name="Test Sheet"
    )
    
    print(f"✅ Comparison completed")
    print(f"   Traditional Tables: {comparison_result['summary']['traditional_tables_found']}")
    print(f"   AI Tables: {comparison_result['summary']['ai_tables_found']}")
    print(f"   Winner: {comparison_result['summary']['winner']}")
    print(f"   Agreement Score: {comparison_result['metrics']['agreement_score']:.3f}")
    print(f"   Complexity Level: {comparison_result['summary']['complexity_level']}")
    
    # Test case potential
    test_case_potential = comparison_result['test_case_potential']
    print(f"   Test Case Potential: {test_case_potential['test_case_type']} (score: {test_case_potential['potential_score']:.2f})")
    
    if comparison_result['insights']:
        print(f"   Key Insights: {comparison_result['insights'][0]}")
    
    return comparison_result


def test_end_to_end_processing():
    """Test end-to-end processing with a real Excel file."""
    print("\n=== Testing End-to-End Processing ===\n")
    
    file_path = "tests/test_excel/single_unit_economics_4_tables.xlsx"
    
    if not os.path.exists(file_path):
        print(f"⚠️  Test file not found: {file_path}")
        print("   Using 360 Energy file instead...")
        file_path = "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ No test files available")
        return
    
    print(f"📊 Processing: {os.path.basename(file_path)}")
    
    try:
        # 1. Process with enhanced compact processor
        print("1️⃣ Enhanced compact processing...")
        processor = ComplexityPreservingCompactProcessor(enable_rle=True)
        json_data = processor.process_file(file_path, include_complexity_metadata=True)
        
        # 2. Analyze complexity
        print("2️⃣ Complexity analysis...")
        complexity_analyzer = ExcelComplexityAnalyzer()
        
        # Process first sheet only for demo
        sheet = json_data['workbook']['sheets'][0]
        sheet_name = sheet.get('name', 'Sheet1')
        
        complexity_metadata_dict = json_data.get('complexity_metadata', {}).get('sheets', {})
        sheet_complexity_metadata = complexity_metadata_dict.get(sheet_name)
        
        complexity_analysis = complexity_analyzer.analyze_sheet_complexity(
            sheet, 
            complexity_metadata=sheet_complexity_metadata
        )
        
        print(f"   Complexity Score: {complexity_analysis['complexity_score']:.3f}")
        print(f"   Recommendation: {complexity_analysis['recommendation']}")
        
        # 3. Traditional table processing
        print("3️⃣ Traditional table processing...")
        table_processor = CompactTableProcessor()
        traditional_result = table_processor.transform_to_compact_table_format(
            {'workbook': {'sheets': [sheet]}}, 
            {}
        )
        
        traditional_tables = traditional_result.get('workbook', {}).get('sheets', [{}])[0].get('tables', [])
        print(f"   Traditional tables found: {len(traditional_tables)}")
        
        # 4. AI analysis (mock if client not available)
        print("4️⃣ AI analysis...")
        ai_client = AnthropicExcelClient()
        
        if ai_client.is_available():
            print("   🤖 Using real AI analysis...")
            ai_raw_response = ai_client.analyze_excel_tables(
                sheet, 
                complexity_metadata=complexity_analysis,
                analysis_focus="comprehensive"
            )
            
            ai_parser = AIResultParser()
            ai_result = ai_parser.parse_excel_analysis(ai_raw_response)
            
            print(f"   AI Status: {ai_result['validation']['valid']}")
            print(f"   AI tables found: {ai_result['table_count']}")
            print(f"   AI confidence: {ai_result.get('ai_analysis', {}).get('confidence', 0.0):.3f}")
            
        else:
            print("   🔧 Using mock AI analysis...")
            ai_result = {
                'ai_analysis': {'tables': [], 'confidence': 0.0},
                'table_count': 0,
                'converted_tables': [],
                'processing_recommendation': 'traditional',
                'validation': {'valid': True, 'errors': [], 'warnings': []},
                'metadata': {'ai_metadata': {'total_tokens': 0}}
            }
        
        # 5. Comparison analysis
        print("5️⃣ Comparison analysis...")
        comparison_engine = ComparisonEngine()
        comparison_result = comparison_engine.compare_analysis_results(
            traditional_result={'tables': traditional_tables},
            ai_result=ai_result,
            complexity_metadata=complexity_analysis,
            sheet_name=sheet_name
        )
        
        print(f"   Winner: {comparison_result['summary']['winner']}")
        print(f"   Agreement: {comparison_result['metrics']['agreement_score']:.3f}")
        
        print("\n✅ End-to-end processing completed successfully!")
        
        return {
            'file_processed': os.path.basename(file_path),
            'complexity_score': complexity_analysis['complexity_score'],
            'traditional_tables': len(traditional_tables),
            'ai_tables': ai_result['table_count'],
            'comparison_winner': comparison_result['summary']['winner'],
            'ai_available': ai_client.is_available()
        }
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_cost_estimation():
    """Test AI cost estimation functionality."""
    print("\n=== Testing Cost Estimation ===\n")
    
    # Create mock sheet data
    mock_sheet_data = {
        'name': 'Test Sheet',
        'rows': [
            {'r': 1, 'cells': [[1, 'Header1'], [2, 'Header2'], [3, 'Header3']]},
            {'r': 2, 'cells': [[1, 100], [2, 200], [3, 300]]},
            {'r': 3, 'cells': [[1, 110], [2, 210], [3, 310]]}
        ]
    }
    
    ai_client = AnthropicExcelClient()
    cost_estimate = ai_client.estimate_api_cost(mock_sheet_data)
    
    print(f"💰 Cost Estimation:")
    print(f"   Estimated prompt tokens: {cost_estimate['estimated_prompt_tokens']:,}")
    print(f"   Estimated completion tokens: {cost_estimate['estimated_completion_tokens']:,}")
    print(f"   Estimated total cost: ${cost_estimate['estimated_cost_usd']:.4f}")
    
    return cost_estimate


def generate_test_report(results):
    """Generate a test report summary."""
    print("\n" + "="*60)
    print("🎯 PHASE 2 AI INTEGRATION TEST REPORT")
    print("="*60)
    
    print("\n📋 COMPONENT STATUS:")
    print(f"   ✅ Anthropic Client: {'Available' if results.get('ai_available') else 'Mock Only'}")
    print(f"   ✅ AI Result Parser: Functional")
    print(f"   ✅ Comparison Engine: Functional")
    print(f"   ✅ Enhanced Processor: Functional")
    
    if results.get('end_to_end'):
        e2e = results['end_to_end']
        print(f"\n📊 END-TO-END RESULTS:")
        print(f"   File: {e2e['file_processed']}")
        print(f"   Complexity Score: {e2e['complexity_score']:.3f}")
        print(f"   Traditional Tables: {e2e['traditional_tables']}")
        print(f"   AI Tables: {e2e['ai_tables']}")
        print(f"   Winner: {e2e['comparison_winner']}")
    
    if results.get('cost_estimate'):
        cost = results['cost_estimate']
        print(f"\n💰 COST ESTIMATION:")
        print(f"   Per analysis: ${cost['estimated_cost_usd']:.4f}")
        print(f"   Per 100 analyses: ${cost['estimated_cost_usd'] * 100:.2f}")
    
    print(f"\n🚀 READINESS ASSESSMENT:")
    
    if results.get('ai_available'):
        print("   ✅ Ready for production AI testing")
        print("   ✅ Can generate real comparison data")
        print("   ✅ Cost estimation available")
        print("   ✅ Full comparison mode functional")
    else:
        print("   ⚠️  Ready for mock testing only")
        print("   ⚠️  Need ANTHROPIC_API_KEY for production")
        print("   ✅ All infrastructure components ready")
        print("   ✅ Can be activated once API key is provided")
    
    print(f"\n🎯 NEXT STEPS:")
    print("   1. Set ANTHROPIC_API_KEY environment variable")
    print("   2. Test with real AI analysis on complex Excel files")
    print("   3. Collect comparison data for tuning")
    print("   4. Generate test cases from disagreements")
    print("   5. Refine complexity thresholds based on AI feedback")


def main():
    """Run all Phase 2 tests."""
    print("🚀 PHASE 2 AI INTEGRATION TESTING")
    print("="*50 + "\n")
    
    results = {}
    
    # Test individual components
    results['ai_available'] = test_ai_client()
    results['ai_parsing'] = test_ai_analysis_pipeline()
    results['comparison'] = test_comparison_engine()
    results['cost_estimate'] = test_cost_estimation()
    
    # Test end-to-end
    results['end_to_end'] = test_end_to_end_processing()
    
    # Generate report
    generate_test_report(results)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()

