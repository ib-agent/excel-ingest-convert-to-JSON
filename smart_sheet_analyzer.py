#!/usr/bin/env python3
"""
Smart Sheet-Level Analyzer

This script demonstrates the enhanced sheet-level processing approach where:
1. Each sheet is analyzed independently for complexity
2. Processing decisions are made per sheet based on complexity
3. AI analysis is only used when complexity warrants it
4. Cost optimization through intelligent routing
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.anthropic_excel_client import AnthropicExcelClient
from converter.ai_result_parser import AIResultParser
from converter.comparison_engine import ComparisonEngine
from converter.complexity_preserving_compact_processor import ComplexityPreservingCompactProcessor
from converter.compact_table_processor import CompactTableProcessor
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer


class SmartSheetAnalyzer:
    """
    Intelligent sheet-level analyzer that makes processing decisions based on complexity.
    """
    
    def __init__(self):
        """Initialize the smart analyzer."""
        self.ai_client = AnthropicExcelClient()
        self.ai_parser = AIResultParser()
        self.comparison_engine = ComparisonEngine()
        self.processor = ComplexityPreservingCompactProcessor(enable_rle=True)
        self.table_processor = CompactTableProcessor()
        self.complexity_analyzer = ExcelComplexityAnalyzer()
        
        self.ai_available = self.ai_client.is_available()
        self.processing_stats = {
            'total_sheets': 0,
            'traditional_only': 0,
            'dual_analysis': 0,
            'ai_primary': 0,
            'total_cost': 0.0,
            'ai_advantages': 0,
            'traditional_advantages': 0
        }
        
        # Configurable thresholds
        self.thresholds = {
            'traditional_max': 0.3,    # Below this: traditional only
            'dual_min': 0.3,           # Above this: consider dual analysis
            'ai_primary_min': 0.7,     # Above this: AI primary
            'max_cost_per_sheet': 0.10 # Maximum cost per sheet
        }
    
    def analyze_file_intelligently(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze an Excel file with intelligent per-sheet processing decisions.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Comprehensive analysis results with processing decisions
        """
        file_name = os.path.basename(file_path)
        print(f"📊 Smart Analysis: {file_name}")
        print("="*50)
        
        # 1. Process file and extract complexity metadata
        try:
            json_data = self.processor.process_file(file_path, include_complexity_metadata=True)
        except Exception as e:
            raise Exception(f"Failed to process file: {str(e)}")
        
        file_result = {
            'file_name': file_name,
            'timestamp': datetime.now().isoformat(),
            'total_sheets': len(json_data['workbook']['sheets']),
            'sheets': [],
            'file_summary': {
                'processing_decisions': {},
                'total_cost': 0.0,
                'complexity_distribution': {},
                'performance_comparison': {}
            }
        }
        
        complexity_metadata_dict = json_data.get('complexity_metadata', {}).get('sheets', {})
        
        # 2. Analyze each sheet independently
        for sheet_idx, sheet in enumerate(json_data['workbook']['sheets']):
            sheet_name = sheet.get('name', f'Sheet{sheet_idx + 1}')
            
            print(f"\n📋 Sheet {sheet_idx + 1}: '{sheet_name}'")
            
            # Analyze this sheet
            sheet_result = self._analyze_sheet_intelligently(
                sheet, sheet_name, complexity_metadata_dict
            )
            
            file_result['sheets'].append(sheet_result)
            
            # Update file summary
            decision = sheet_result['processing_decision']
            file_result['file_summary']['processing_decisions'][decision] = \
                file_result['file_summary']['processing_decisions'].get(decision, 0) + 1
            
            if 'ai_analysis' in sheet_result:
                file_result['file_summary']['total_cost'] += \
                    sheet_result['ai_analysis'].get('actual_cost', 0.0)
            
            complexity_level = sheet_result['complexity_analysis']['complexity_level']
            file_result['file_summary']['complexity_distribution'][complexity_level] = \
                file_result['file_summary']['complexity_distribution'].get(complexity_level, 0) + 1
        
        # 3. Generate file-level insights
        file_result['insights'] = self._generate_file_insights(file_result)
        
        return file_result
    
    def _analyze_sheet_intelligently(self, 
                                   sheet: Dict[str, Any], 
                                   sheet_name: str, 
                                   complexity_metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single sheet with intelligent processing decision."""
        
        # 1. Complexity Analysis
        sheet_complexity_metadata = complexity_metadata_dict.get(sheet_name)
        complexity_analysis = self.complexity_analyzer.analyze_sheet_complexity(
            sheet, 
            complexity_metadata=sheet_complexity_metadata
        )
        
        complexity_score = complexity_analysis['complexity_score']
        complexity_level = complexity_analysis['complexity_level']
        
        print(f"   📈 Complexity: {complexity_score:.3f} ({complexity_level})")
        
        # 2. Make Processing Decision
        processing_decision = self._make_processing_decision(complexity_score, sheet_name)
        print(f"   🎯 Decision: {processing_decision}")
        
        sheet_result = {
            'sheet_name': sheet_name,
            'complexity_analysis': complexity_analysis,
            'processing_decision': processing_decision,
            'traditional_analysis': None,
            'ai_analysis': None,
            'comparison': None
        }
        
        # 3. Traditional Analysis (always run for comparison when AI is used)
        if processing_decision in ['traditional_only', 'dual_analysis', 'ai_primary']:
            traditional_result = self._run_traditional_analysis(sheet)
            sheet_result['traditional_analysis'] = traditional_result
            
            traditional_tables = len(traditional_result.get('tables', []))
            print(f"   🔧 Traditional: {traditional_tables} tables")
        
        # 4. AI Analysis (based on decision)
        if processing_decision in ['dual_analysis', 'ai_primary'] and self.ai_available:
            ai_result = self._run_ai_analysis(sheet, complexity_analysis)
            sheet_result['ai_analysis'] = ai_result
            
            if ai_result['success']:
                ai_tables = ai_result['tables_found']
                ai_confidence = ai_result['confidence']
                print(f"   🤖 AI: {ai_tables} tables (confidence: {ai_confidence:.3f})")
            else:
                print(f"   🤖 AI: Analysis failed")
        
        # 5. Comparison Analysis (if both methods were used)
        if (sheet_result['traditional_analysis'] and 
            sheet_result['ai_analysis'] and 
            sheet_result['ai_analysis'] and
            sheet_result['ai_analysis'].get('success', False)):
            
            comparison_result = self._run_comparison_analysis(
                sheet_result['traditional_analysis'],
                sheet_result['ai_analysis'],
                complexity_analysis,
                sheet_name
            )
            sheet_result['comparison'] = comparison_result
            
            winner = comparison_result['summary']['winner']
            agreement = comparison_result['metrics']['agreement_score']
            print(f"   ⚖️  Winner: {winner} (agreement: {agreement:.3f})")
        
        # 6. Update statistics
        self._update_processing_stats(sheet_result)
        
        return sheet_result
    
    def _make_processing_decision(self, complexity_score: float, sheet_name: str) -> str:
        """
        Make intelligent processing decision based on complexity and constraints.
        
        Args:
            complexity_score: Sheet complexity score (0.0-1.0)
            sheet_name: Name of the sheet
            
        Returns:
            Processing decision: 'traditional_only', 'dual_analysis', or 'ai_primary'
        """
        # Check if AI is available
        if not self.ai_available:
            return 'traditional_only'
        
        # Cost-based decision
        estimated_cost = 0.03 + (complexity_score * 0.05)  # Rough estimation
        if estimated_cost > self.thresholds['max_cost_per_sheet']:
            print(f"   💰 Cost too high (${estimated_cost:.3f}), using traditional")
            return 'traditional_only'
        
        # Complexity-based decision
        if complexity_score < self.thresholds['traditional_max']:
            return 'traditional_only'
        elif complexity_score >= self.thresholds['ai_primary_min']:
            return 'ai_primary'
        else:
            # In the middle range - use dual for comparison data
            return 'dual_analysis'
    
    def _run_traditional_analysis(self, sheet: Dict[str, Any]) -> Dict[str, Any]:
        """Run traditional heuristic analysis."""
        traditional_result = self.table_processor.transform_to_compact_table_format(
            {'workbook': {'sheets': [sheet]}}, 
            {}
        )
        
        traditional_tables = traditional_result.get('workbook', {}).get('sheets', [{}])[0].get('tables', [])
        
        return {
            'tables_found': len(traditional_tables),
            'tables': traditional_tables[:3],  # Limit for storage
            'success': len(traditional_tables) > 0,
            'method': 'traditional_heuristics'
        }
    
    def _run_ai_analysis(self, sheet: Dict[str, Any], complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Run AI analysis with cost tracking."""
        try:
            # Cost estimation
            cost_estimate = self.ai_client.estimate_api_cost(sheet)
            estimated_cost = cost_estimate['estimated_cost_usd']
            
            # Perform AI analysis
            ai_raw_response = self.ai_client.analyze_excel_sheet(
                sheet, 
                complexity_metadata=complexity_analysis,
                analysis_focus="comprehensive"
            )
            
            # Parse AI response
            ai_result = self.ai_parser.parse_excel_analysis(ai_raw_response)
            
            ai_tables_count = ai_result.get('table_count', 0)
            ai_confidence = ai_result.get('ai_analysis', {}).get('confidence', 0.0)
            ai_valid = ai_result.get('validation', {}).get('valid', False)
            
            # Calculate actual cost (rough estimation)
            actual_tokens = ai_result.get('metadata', {}).get('ai_metadata', {}).get('total_tokens', 0)
            actual_cost = actual_tokens * 0.000003  # Rough calculation
            
            return {
                'tables_found': ai_tables_count,
                'confidence': ai_confidence,
                'validation_status': ai_valid,
                'success': ai_valid and ai_tables_count >= 0,
                'estimated_cost': estimated_cost,
                'actual_cost': actual_cost,
                'tokens_used': actual_tokens,
                'method': 'anthropic_ai'
            }
            
        except Exception as e:
            print(f"      ❌ AI analysis error: {str(e)}")
            return {
                'tables_found': 0,
                'confidence': 0.0,
                'success': False,
                'error': str(e),
                'estimated_cost': 0.0,
                'actual_cost': 0.0,
                'method': 'anthropic_ai'
            }
    
    def _run_comparison_analysis(self, 
                               traditional_result: Dict[str, Any],
                               ai_result: Dict[str, Any],
                               complexity_analysis: Dict[str, Any],
                               sheet_name: str) -> Dict[str, Any]:
        """Run comparison analysis between traditional and AI methods."""
        
        # Convert to format expected by comparison engine
        traditional_tables = traditional_result.get('tables', [])
        
        ai_converted = {
            'ai_analysis': {
                'tables': [],
                'confidence': ai_result.get('confidence', 0.0)
            },
            'table_count': ai_result.get('tables_found', 0),
            'converted_tables': [],
            'processing_recommendation': 'ai_assisted'
        }
        
        comparison_result = self.comparison_engine.compare_analysis_results(
            traditional_result={'tables': traditional_tables},
            ai_result=ai_converted,
            complexity_metadata=complexity_analysis,
            sheet_name=sheet_name
        )
        
        return comparison_result
    
    def _update_processing_stats(self, sheet_result: Dict[str, Any]):
        """Update processing statistics."""
        self.processing_stats['total_sheets'] += 1
        
        decision = sheet_result['processing_decision']
        if decision == 'traditional_only':
            self.processing_stats['traditional_only'] += 1
        elif decision == 'dual_analysis':
            self.processing_stats['dual_analysis'] += 1
        elif decision == 'ai_primary':
            self.processing_stats['ai_primary'] += 1
        
        # Track costs
        if 'ai_analysis' in sheet_result and sheet_result['ai_analysis']:
            cost = sheet_result['ai_analysis'].get('actual_cost', 0.0)
            self.processing_stats['total_cost'] += cost
        
        # Track performance
        if 'comparison' in sheet_result and sheet_result['comparison']:
            winner = sheet_result['comparison']['summary']['winner']
            if 'ai' in winner:
                self.processing_stats['ai_advantages'] += 1
            elif 'traditional' in winner:
                self.processing_stats['traditional_advantages'] += 1
    
    def _generate_file_insights(self, file_result: Dict[str, Any]) -> List[str]:
        """Generate insights from file analysis."""
        insights = []
        
        decisions = file_result['file_summary']['processing_decisions']
        total_sheets = file_result['total_sheets']
        
        # Decision distribution insights
        if decisions.get('traditional_only', 0) == total_sheets:
            insights.append("All sheets were simple enough for traditional processing")
        elif decisions.get('ai_primary', 0) > 0:
            insights.append(f"{decisions.get('ai_primary', 0)} sheets required AI-primary processing")
        
        # Cost insights
        total_cost = file_result['file_summary']['total_cost']
        if total_cost > 0:
            avg_cost = total_cost / total_sheets
            insights.append(f"Average cost per sheet: ${avg_cost:.4f}")
        
        # Complexity insights
        complexity_dist = file_result['file_summary']['complexity_distribution']
        if complexity_dist.get('complex', 0) > complexity_dist.get('simple', 0):
            insights.append("File contains primarily complex sheets requiring advanced analysis")
        
        return insights
    
    def print_summary_report(self):
        """Print a summary report of processing statistics."""
        stats = self.processing_stats
        
        print("\n" + "="*60)
        print("🎯 SMART SHEET ANALYZER SUMMARY")
        print("="*60)
        
        print(f"\n📊 PROCESSING DECISIONS:")
        print(f"   Total Sheets: {stats['total_sheets']}")
        print(f"   Traditional Only: {stats['traditional_only']} ({stats['traditional_only']/max(stats['total_sheets'],1)*100:.1f}%)")
        print(f"   Dual Analysis: {stats['dual_analysis']} ({stats['dual_analysis']/max(stats['total_sheets'],1)*100:.1f}%)")
        print(f"   AI Primary: {stats['ai_primary']} ({stats['ai_primary']/max(stats['total_sheets'],1)*100:.1f}%)")
        
        print(f"\n💰 COST OPTIMIZATION:")
        print(f"   Total Cost: ${stats['total_cost']:.4f}")
        if stats['total_sheets'] > 0:
            print(f"   Average Cost/Sheet: ${stats['total_cost']/stats['total_sheets']:.4f}")
        print(f"   AI Usage Rate: {(stats['dual_analysis'] + stats['ai_primary'])/max(stats['total_sheets'],1)*100:.1f}%")
        
        if stats['ai_advantages'] + stats['traditional_advantages'] > 0:
            print(f"\n⚖️  PERFORMANCE COMPARISON:")
            print(f"   AI Advantages: {stats['ai_advantages']}")
            print(f"   Traditional Advantages: {stats['traditional_advantages']}")
            ai_win_rate = stats['ai_advantages'] / (stats['ai_advantages'] + stats['traditional_advantages'])
            print(f"   AI Win Rate: {ai_win_rate:.1%}")


def main():
    """Demonstrate smart sheet-level analysis."""
    print("🧠 SMART SHEET-LEVEL ANALYZER")
    print("="*40 + "\n")
    
    analyzer = SmartSheetAnalyzer()
    
    if not analyzer.ai_available:
        print("⚠️  AI not available. Results will show traditional-only processing.")
        print("   To enable AI: ensure ANTHROPIC_API_KEY is set\n")
    
    # Test files
    test_files = [
        "tests/test_excel/single_unit_economics_4_tables.xlsx",
        "tests/test_excel/Test_SpreadSheet_100_numbers.xlsx"
    ]
    
    results = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                result = analyzer.analyze_file_intelligently(file_path)
                results.append(result)
                
                print(f"\n💡 File Insights:")
                for insight in result['insights']:
                    print(f"   • {insight}")
                
                print("\n" + "-"*50)
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {str(e)}")
        else:
            print(f"⚠️  File not found: {file_path}")
    
    # Print summary
    analyzer.print_summary_report()
    
    # Save results
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"smart_analysis_results_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump({
                'analysis_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'analyzer_version': '1.0',
                    'ai_available': analyzer.ai_available
                },
                'processing_stats': analyzer.processing_stats,
                'file_results': results
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
