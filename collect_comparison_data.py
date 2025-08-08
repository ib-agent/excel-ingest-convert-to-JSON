#!/usr/bin/env python3
"""
Comparison Data Collection

This script collects comprehensive comparison data between traditional heuristics 
and AI analysis across multiple Excel files. This data is used for:

1. Tuning complexity thresholds
2. Generating test cases
3. Optimizing AI usage decisions
4. Understanding where each method excels
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.anthropic_excel_client import AnthropicExcelClient
from converter.ai_result_parser import AIResultParser
from converter.comparison_engine import ComparisonEngine
from converter.complexity_preserving_compact_processor import ComplexityPreservingCompactProcessor
from converter.compact_table_processor import CompactTableProcessor
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer


class ComparisonDataCollector:
    """Collects comparison data across multiple Excel files."""
    
    def __init__(self, enable_ai=None):
        """
        Initialize the data collector.
        
        Args:
            enable_ai: If None, auto-detect based on API key availability
        """
        self.ai_client = AnthropicExcelClient()
        self.ai_parser = AIResultParser()
        self.comparison_engine = ComparisonEngine()
        self.processor = ComplexityPreservingCompactProcessor(enable_rle=True)
        self.table_processor = CompactTableProcessor()
        self.complexity_analyzer = ExcelComplexityAnalyzer()
        
        # Determine if AI is available
        if enable_ai is None:
            self.enable_ai = self.ai_client.is_available()
        else:
            self.enable_ai = enable_ai and self.ai_client.is_available()
        
        self.results = []
        self.summary_stats = {
            'total_files': 0,
            'total_sheets': 0,
            'ai_analyses': 0,
            'traditional_analyses': 0,
            'agreements': 0,
            'disagreements': 0,
            'ai_advantages': 0,
            'traditional_advantages': 0,
            'total_cost_estimate': 0.0
        }
    
    def collect_from_directory(self, directory_path="tests/test_excel", max_files=None):
        """
        Collect comparison data from all Excel files in a directory.
        
        Args:
            directory_path: Path to directory containing Excel files
            max_files: Maximum number of files to process (None for all)
        """
        print(f"🔍 Scanning directory: {directory_path}")
        print(f"🤖 AI Analysis: {'Enabled' if self.enable_ai else 'Disabled'}")
        
        if not self.enable_ai:
            print("💡 To enable AI analysis:")
            print("   1. Set ANTHROPIC_API_KEY environment variable")
            print("   2. Rerun this script")
            print("   Continuing with traditional-only analysis...\n")
        
        directory = Path(directory_path)
        excel_files = list(directory.glob("*.xlsx")) + list(directory.glob("*.xlsm"))
        
        if max_files:
            excel_files = excel_files[:max_files]
        
        print(f"📊 Found {len(excel_files)} Excel files to process\n")
        
        for i, file_path in enumerate(excel_files, 1):
            print(f"[{i}/{len(excel_files)}] Processing: {file_path.name}")
            
            try:
                file_result = self.analyze_file(str(file_path))
                self.results.append(file_result)
                self._update_summary_stats(file_result)
                
                # Brief pause to avoid overwhelming the API
                if self.enable_ai:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"   ❌ Error processing {file_path.name}: {str(e)}")
                continue
        
        print(f"\n✅ Collection complete! Processed {len(self.results)} files")
        return self.results
    
    def analyze_file(self, file_path):
        """Analyze a single Excel file."""
        file_name = os.path.basename(file_path)
        print(f"   📄 Loading: {file_name}")
        
        # 1. Process file with enhanced compact processor
        try:
            json_data = self.processor.process_file(file_path, include_complexity_metadata=True)
        except Exception as e:
            raise Exception(f"Failed to process file: {str(e)}")
        
        file_result = {
            'file_name': file_name,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'sheets': [],
            'file_summary': {
                'total_sheets': len(json_data['workbook']['sheets']),
                'complexity_levels': {},
                'processing_recommendations': {},
                'total_cost_estimate': 0.0
            }
        }
        
        # 2. Analyze each sheet
        complexity_metadata_dict = json_data.get('complexity_metadata', {}).get('sheets', {})
        
        for sheet_idx, sheet in enumerate(json_data['workbook']['sheets']):
            sheet_name = sheet.get('name', f'Sheet{sheet_idx + 1}')
            print(f"      🔍 Analyzing sheet: {sheet_name}")
            
            try:
                sheet_result = self.analyze_sheet(sheet, sheet_name, complexity_metadata_dict)
                file_result['sheets'].append(sheet_result)
                
                # Update file summary
                complexity_level = sheet_result['complexity_analysis']['complexity_level']
                file_result['file_summary']['complexity_levels'][complexity_level] = \
                    file_result['file_summary']['complexity_levels'].get(complexity_level, 0) + 1
                
                recommendation = sheet_result['complexity_analysis']['recommendation']
                file_result['file_summary']['processing_recommendations'][recommendation] = \
                    file_result['file_summary']['processing_recommendations'].get(recommendation, 0) + 1
                
                if 'ai_analysis' in sheet_result and 'cost_estimate' in sheet_result['ai_analysis']:
                    file_result['file_summary']['total_cost_estimate'] += \
                        sheet_result['ai_analysis']['cost_estimate'].get('estimated_cost_usd', 0.0)
                
            except Exception as e:
                print(f"         ❌ Error analyzing sheet {sheet_name}: {str(e)}")
                continue
        
        return file_result
    
    def analyze_sheet(self, sheet, sheet_name, complexity_metadata_dict):
        """Analyze a single sheet with both traditional and AI methods."""
        
        # 1. Complexity Analysis
        sheet_complexity_metadata = complexity_metadata_dict.get(sheet_name)
        complexity_analysis = self.complexity_analyzer.analyze_sheet_complexity(
            sheet, 
            complexity_metadata=sheet_complexity_metadata
        )
        
        print(f"         📊 Complexity: {complexity_analysis['complexity_score']:.3f} ({complexity_analysis['complexity_level']})")
        
        # 2. Traditional Analysis
        traditional_result = self.table_processor.transform_to_compact_table_format(
            {'workbook': {'sheets': [sheet]}}, 
            {}
        )
        
        traditional_tables = traditional_result.get('workbook', {}).get('sheets', [{}])[0].get('tables', [])
        print(f"         🔧 Traditional: {len(traditional_tables)} tables")
        
        sheet_result = {
            'sheet_name': sheet_name,
            'complexity_analysis': complexity_analysis,
            'traditional_analysis': {
                'tables_found': len(traditional_tables),
                'tables': traditional_tables[:3],  # Limit for storage
                'detection_methods': traditional_result.get('detection_methods', []),
                'success': len(traditional_tables) > 0
            }
        }
        
        # 3. AI Analysis (if enabled)
        if self.enable_ai:
            try:
                print(f"         🤖 Running AI analysis...")
                
                # Cost estimation first
                cost_estimate = self.ai_client.estimate_api_cost(sheet)
                
                # Perform AI analysis
                ai_raw_response = self.ai_client.analyze_excel_tables(
                    sheet, 
                    complexity_metadata=complexity_analysis,
                    analysis_focus="comprehensive"
                )
                
                # Parse AI response
                ai_result = self.ai_parser.parse_excel_analysis(ai_raw_response)
                
                ai_tables_count = ai_result.get('table_count', 0)
                ai_confidence = ai_result.get('ai_analysis', {}).get('confidence', 0.0)
                
                print(f"         🤖 AI: {ai_tables_count} tables (confidence: {ai_confidence:.3f})")
                
                sheet_result['ai_analysis'] = {
                    'tables_found': ai_tables_count,
                    'confidence': ai_confidence,
                    'processing_recommendation': ai_result.get('processing_recommendation', 'traditional'),
                    'validation_status': ai_result.get('validation', {}).get('valid', False),
                    'cost_estimate': cost_estimate,
                    'success': ai_tables_count > 0
                }
                
                # 4. Comparison Analysis
                comparison_result = self.comparison_engine.compare_analysis_results(
                    traditional_result={'tables': traditional_tables},
                    ai_result=ai_result,
                    complexity_metadata=complexity_analysis,
                    sheet_name=sheet_name
                )
                
                agreement_score = comparison_result['metrics']['agreement_score']
                winner = comparison_result['summary']['winner']
                
                print(f"         ⚖️  Comparison: {winner} (agreement: {agreement_score:.3f})")
                
                sheet_result['comparison'] = {
                    'winner': winner,
                    'agreement_score': agreement_score,
                    'test_case_potential': comparison_result['test_case_potential'],
                    'insights': comparison_result['insights'][:2],  # Top 2 insights
                    'tuning_recommendations': comparison_result['tuning_recommendations']
                }
                
            except Exception as e:
                print(f"         ❌ AI analysis failed: {str(e)}")
                sheet_result['ai_analysis'] = {
                    'error': str(e),
                    'success': False
                }
        
        return sheet_result
    
    def _update_summary_stats(self, file_result):
        """Update summary statistics."""
        self.summary_stats['total_files'] += 1
        self.summary_stats['total_sheets'] += len(file_result['sheets'])
        
        for sheet_result in file_result['sheets']:
            # Traditional stats
            if sheet_result['traditional_analysis']['success']:
                self.summary_stats['traditional_analyses'] += 1
            
            # AI stats (if available)
            if 'ai_analysis' in sheet_result and sheet_result['ai_analysis'].get('success', False):
                self.summary_stats['ai_analyses'] += 1
                
                # Cost tracking
                if 'cost_estimate' in sheet_result['ai_analysis']:
                    self.summary_stats['total_cost_estimate'] += \
                        sheet_result['ai_analysis']['cost_estimate'].get('estimated_cost_usd', 0.0)
            
            # Comparison stats (if available)
            if 'comparison' in sheet_result:
                winner = sheet_result['comparison']['winner']
                agreement = sheet_result['comparison']['agreement_score']
                
                if agreement > 0.7:
                    self.summary_stats['agreements'] += 1
                elif agreement < 0.3:
                    self.summary_stats['disagreements'] += 1
                
                if 'ai' in winner:
                    self.summary_stats['ai_advantages'] += 1
                elif 'traditional' in winner:
                    self.summary_stats['traditional_advantages'] += 1
    
    def save_results(self, output_file="comparison_data_collection.json"):
        """Save collection results to JSON file."""
        output_data = {
            'collection_metadata': {
                'timestamp': datetime.now().isoformat(),
                'ai_enabled': self.enable_ai,
                'collection_version': '2.0',
                'total_files_processed': len(self.results)
            },
            'summary_statistics': self.summary_stats,
            'detailed_results': self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
        return output_file
    
    def generate_report(self):
        """Generate a summary report."""
        stats = self.summary_stats
        
        print("\n" + "="*60)
        print("📊 COMPARISON DATA COLLECTION REPORT")
        print("="*60)
        
        print(f"\n📈 PROCESSING SUMMARY:")
        print(f"   Files Processed: {stats['total_files']}")
        print(f"   Sheets Analyzed: {stats['total_sheets']}")
        print(f"   AI Analyses: {stats['ai_analyses']}")
        print(f"   Traditional Analyses: {stats['traditional_analyses']}")
        
        if self.enable_ai and stats['total_cost_estimate'] > 0:
            print(f"   Total Cost Estimate: ${stats['total_cost_estimate']:.4f}")
            print(f"   Average Cost/Sheet: ${stats['total_cost_estimate']/max(stats['total_sheets'], 1):.4f}")
        
        if stats['ai_analyses'] > 0:
            print(f"\n⚖️  COMPARISON RESULTS:")
            print(f"   Agreements (>70%): {stats['agreements']}")
            print(f"   Disagreements (<30%): {stats['disagreements']}")
            print(f"   AI Advantages: {stats['ai_advantages']}")
            print(f"   Traditional Advantages: {stats['traditional_advantages']}")
            
            # Calculate success rates
            ai_success_rate = stats['ai_analyses'] / max(stats['total_sheets'], 1) * 100
            traditional_success_rate = stats['traditional_analyses'] / max(stats['total_sheets'], 1) * 100
            
            print(f"\n📊 SUCCESS RATES:")
            print(f"   AI Success Rate: {ai_success_rate:.1f}%")
            print(f"   Traditional Success Rate: {traditional_success_rate:.1f}%")
        
        # Analyze complexity distribution
        complexity_distribution = {}
        recommendation_distribution = {}
        
        for file_result in self.results:
            for sheet_result in file_result['sheets']:
                complexity_level = sheet_result['complexity_analysis']['complexity_level']
                complexity_distribution[complexity_level] = complexity_distribution.get(complexity_level, 0) + 1
                
                recommendation = sheet_result['complexity_analysis']['recommendation']
                recommendation_distribution[recommendation] = recommendation_distribution.get(recommendation, 0) + 1
        
        print(f"\n🎯 COMPLEXITY DISTRIBUTION:")
        for level, count in sorted(complexity_distribution.items()):
            percentage = count / max(stats['total_sheets'], 1) * 100
            print(f"   {level.title()}: {count} sheets ({percentage:.1f}%)")
        
        print(f"\n🤖 PROCESSING RECOMMENDATIONS:")
        for recommendation, count in sorted(recommendation_distribution.items()):
            percentage = count / max(stats['total_sheets'], 1) * 100
            print(f"   {recommendation.title()}: {count} sheets ({percentage:.1f}%)")
        
        # Generate insights
        self._generate_insights()
    
    def _generate_insights(self):
        """Generate actionable insights from the collected data."""
        stats = self.summary_stats
        
        print(f"\n💡 KEY INSIGHTS:")
        
        insights = []
        
        # Insight 1: AI utilization
        if self.enable_ai:
            ai_utilization = stats['ai_analyses'] / max(stats['total_sheets'], 1)
            if ai_utilization > 0.5:
                insights.append("High AI utilization suggests many complex sheets in dataset")
            elif ai_utilization < 0.2:
                insights.append("Low AI utilization suggests mostly simple sheets")
        
        # Insight 2: Agreement analysis
        if stats['disagreements'] > stats['agreements']:
            insights.append("High disagreement rate suggests need for threshold tuning")
        
        # Insight 3: Cost efficiency
        if self.enable_ai and stats['total_cost_estimate'] > 0:
            cost_per_analysis = stats['total_cost_estimate'] / max(stats['ai_analyses'], 1)
            if cost_per_analysis > 0.1:
                insights.append("High per-analysis cost suggests large/complex sheets")
        
        # Insight 4: Traditional vs AI performance
        if stats['ai_advantages'] > stats['traditional_advantages']:
            insights.append("AI frequently outperforms traditional methods")
        elif stats['traditional_advantages'] > stats['ai_advantages']:
            insights.append("Traditional methods often sufficient - consider raising AI thresholds")
        
        for i, insight in enumerate(insights, 1):
            print(f"   {i}. {insight}")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        
        recommendations = []
        
        if not self.enable_ai:
            recommendations.append("Enable AI analysis to collect comparison data")
        
        if self.enable_ai and stats['disagreements'] > 3:
            recommendations.append("Analyze disagreement cases for test case generation")
        
        if stats['total_sheets'] < 10:
            recommendations.append("Process more files to get statistically significant results")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")


def main():
    """Main execution function."""
    print("🚀 COMPARISON DATA COLLECTION")
    print("="*50 + "\n")
    
    # Initialize collector
    collector = ComparisonDataCollector()
    
    # Collect data from test files
    collector.collect_from_directory("tests/test_excel", max_files=5)  # Start with 5 files
    
    # Generate report
    collector.generate_report()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"comparison_data_{timestamp}.json"
    collector.save_results(output_file)
    
    print(f"\n🎉 Collection complete! Data saved to {output_file}")
    
    if not collector.enable_ai:
        print(f"\n💡 To enable AI analysis and collect comparison data:")
        print(f"   export ANTHROPIC_API_KEY='your_key_here'")
        print(f"   python {__file__}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {str(e)}")
        import traceback
        traceback.print_exc()
