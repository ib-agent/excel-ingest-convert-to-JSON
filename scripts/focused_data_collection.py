#!/usr/bin/env python3
"""
Focused Data Collection for Tuning

This script runs targeted data collection across Excel files to generate:
1. Comparison data for threshold tuning
2. Disagreement cases for test case generation
3. Performance metrics for optimization
4. Cost analysis for production planning
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smart_sheet_analyzer import SmartSheetAnalyzer


def collect_tuning_data():
    """Collect focused data for tuning and test generation."""
    
    print("🎯 FOCUSED DATA COLLECTION FOR TUNING")
    print("="*50)
    print("Goal: Generate comparison data and test cases\n")
    
    analyzer = SmartSheetAnalyzer()
    
    if not analyzer.ai_available:
        print("❌ AI not available. Please ensure ANTHROPIC_API_KEY is set.")
        print("   Run: source load_config.sh")
        return
    
    # Target files for data collection
    target_files = [
        "tests/test_excel/single_unit_economics_4_tables.xlsx",
        "tests/test_excel/Test_SpreadSheet_100_numbers.xlsx", 
        "tests/test_excel/Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles.xlsx",
        "tests/test_excel/pDD10b - Exos_2023_financials.xlsx",
        "tests/test_excel/Nickson_Lender_Financial_Model.xlsx"
    ]
    
    print(f"📋 Target Files: {len(target_files)} files")
    
    # Adjust thresholds for more dual analysis (better for tuning data)
    analyzer.thresholds = {
        'traditional_max': 0.2,    # Lower threshold = more AI usage
        'dual_min': 0.2,           # More dual analysis for comparison
        'ai_primary_min': 0.8,     # Higher threshold for AI primary
        'max_cost_per_sheet': 0.15 # Allow slightly higher cost for data collection
    }
    
    print("🎛️  Tuned for data collection:")
    print(f"   - More dual analysis (threshold: {analyzer.thresholds['dual_min']})")
    print(f"   - Higher cost limit: ${analyzer.thresholds['max_cost_per_sheet']}")
    print(f"   - Focus on comparison data generation\n")
    
    results = []
    disagreement_cases = []
    total_cost = 0.0
    
    for i, file_path in enumerate(target_files, 1):
        if not os.path.exists(file_path):
            print(f"[{i}/{len(target_files)}] ⚠️  Skipping missing file: {os.path.basename(file_path)}")
            continue
            
        print(f"[{i}/{len(target_files)}] Processing: {os.path.basename(file_path)}")
        
        try:
            result = analyzer.analyze_file_intelligently(file_path)
            results.append(result)
            
            file_cost = result['file_summary']['total_cost']
            total_cost += file_cost
            
            print(f"   💰 File Cost: ${file_cost:.4f}")
            
            # Identify disagreement cases for test generation
            for sheet in result['sheets']:
                if 'comparison' in sheet and sheet['comparison']:
                    agreement = sheet['comparison']['metrics']['agreement_score']
                    if agreement < 0.3:  # Low agreement = good test case
                        disagreement_cases.append({
                            'file': result['file_name'],
                            'sheet': sheet['sheet_name'],
                            'complexity': sheet['complexity_analysis']['complexity_score'],
                            'agreement': agreement,
                            'traditional_tables': sheet['traditional_analysis']['tables_found'],
                            'ai_tables': sheet['ai_analysis']['tables_found'],
                            'ai_confidence': sheet['ai_analysis']['confidence'],
                            'winner': sheet['comparison']['summary']['winner']
                        })
                        print(f"   🧪 Test Case Identified: {sheet['sheet_name']} (agreement: {agreement:.3f})")
            
            print(f"   ✅ Complete\n")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}\n")
            continue
    
    # Generate comprehensive report
    generate_tuning_report(results, disagreement_cases, total_cost, analyzer)
    
    # Save detailed results
    save_tuning_data(results, disagreement_cases, analyzer)
    
    return results, disagreement_cases


def generate_tuning_report(results, disagreement_cases, total_cost, analyzer):
    """Generate comprehensive tuning report."""
    
    print("📊 TUNING DATA COLLECTION REPORT")
    print("="*50)
    
    # Overall statistics
    total_sheets = sum(len(r['sheets']) for r in results)
    total_files = len(results)
    
    print(f"\n📈 COLLECTION SUMMARY:")
    print(f"   Files Processed: {total_files}")
    print(f"   Sheets Analyzed: {total_sheets}")
    print(f"   Total Cost: ${total_cost:.4f}")
    print(f"   Average Cost/Sheet: ${total_cost/max(total_sheets,1):.4f}")
    
    # Processing decision distribution
    stats = analyzer.processing_stats
    print(f"\n🎯 PROCESSING DECISIONS:")
    print(f"   Traditional Only: {stats['traditional_only']} ({stats['traditional_only']/max(stats['total_sheets'],1)*100:.1f}%)")
    print(f"   Dual Analysis: {stats['dual_analysis']} ({stats['dual_analysis']/max(stats['total_sheets'],1)*100:.1f}%)")
    print(f"   AI Primary: {stats['ai_primary']} ({stats['ai_primary']/max(stats['total_sheets'],1)*100:.1f}%)")
    
    # Complexity distribution analysis
    complexity_counts = {'simple': 0, 'moderate': 0, 'complex': 0}
    for result in results:
        for sheet in result['sheets']:
            level = sheet['complexity_analysis']['complexity_level']
            complexity_counts[level] = complexity_counts.get(level, 0) + 1
    
    print(f"\n📊 COMPLEXITY DISTRIBUTION:")
    for level, count in complexity_counts.items():
        percentage = count / max(total_sheets, 1) * 100
        print(f"   {level.title()}: {count} sheets ({percentage:.1f}%)")
    
    # Disagreement analysis for test cases
    print(f"\n🧪 TEST CASE GENERATION:")
    print(f"   Disagreement Cases Found: {len(disagreement_cases)}")
    
    if disagreement_cases:
        avg_agreement = sum(case['agreement'] for case in disagreement_cases) / len(disagreement_cases)
        print(f"   Average Agreement: {avg_agreement:.3f}")
        
        # Group by winner for analysis
        winners = {}
        for case in disagreement_cases:
            winner = case['winner']
            winners[winner] = winners.get(winner, 0) + 1
        
        print(f"   Winner Distribution:")
        for winner, count in winners.items():
            print(f"     {winner}: {count} cases")
    
    # Performance insights
    if stats['ai_advantages'] + stats['traditional_advantages'] > 0:
        ai_win_rate = stats['ai_advantages'] / (stats['ai_advantages'] + stats['traditional_advantages'])
        print(f"\n⚖️  PERFORMANCE INSIGHTS:")
        print(f"   AI Win Rate: {ai_win_rate:.1%}")
        print(f"   AI Advantages: {stats['ai_advantages']} cases")
        print(f"   Traditional Advantages: {stats['traditional_advantages']} cases")
    
    # Threshold tuning recommendations
    print(f"\n🎛️  THRESHOLD TUNING RECOMMENDATIONS:")
    
    # Analyze if thresholds are optimal
    dual_rate = stats['dual_analysis'] / max(stats['total_sheets'], 1)
    if dual_rate < 0.3:
        print(f"   • Consider lowering dual_min threshold (current: 0.2)")
        print(f"     More dual analysis = more comparison data")
    elif dual_rate > 0.7:
        print(f"   • Consider raising dual_min threshold (current: 0.2)")
        print(f"     Too much AI usage may not be cost effective")
    
    if len(disagreement_cases) < 3:
        print(f"   • Need more disagreement cases for robust test generation")
        print(f"     Consider processing more complex Excel files")
    
    if total_cost > 1.0:
        print(f"   • High cost detected - consider raising complexity thresholds")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Review disagreement cases for test case development")
    print(f"   2. Analyze AI vs traditional performance patterns")
    print(f"   3. Adjust complexity thresholds based on cost/benefit")
    print(f"   4. Generate unit tests from high-disagreement cases")


def save_tuning_data(results, disagreement_cases, analyzer):
    """Save tuning data for analysis and test generation."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Main tuning dataset
    tuning_data = {
        'collection_metadata': {
            'timestamp': datetime.now().isoformat(),
            'purpose': 'threshold_tuning_and_test_generation',
            'version': '1.0',
            'thresholds_used': analyzer.thresholds
        },
        'summary_statistics': analyzer.processing_stats,
        'disagreement_cases': disagreement_cases,
        'detailed_results': results
    }
    
    tuning_file = f"tuning_dataset_{timestamp}.json"
    with open(tuning_file, 'w') as f:
        json.dump(tuning_data, f, indent=2)
    
    print(f"\n💾 SAVED TUNING DATA:")
    print(f"   Main Dataset: {tuning_file}")
    
    # Test cases file (focused on disagreements)
    if disagreement_cases:
        test_cases_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'purpose': 'unit_test_generation',
                'total_cases': len(disagreement_cases)
            },
            'test_cases': disagreement_cases
        }
        
        test_cases_file = f"test_cases_{timestamp}.json"
        with open(test_cases_file, 'w') as f:
            json.dump(test_cases_data, f, indent=2)
        
        print(f"   Test Cases: {test_cases_file}")
    
    # Threshold analysis file
    threshold_analysis = {
        'current_thresholds': analyzer.thresholds,
        'performance_metrics': {
            'total_sheets': analyzer.processing_stats['total_sheets'],
            'ai_usage_rate': (analyzer.processing_stats['dual_analysis'] + analyzer.processing_stats['ai_primary']) / max(analyzer.processing_stats['total_sheets'], 1),
            'cost_per_sheet': analyzer.processing_stats['total_cost'] / max(analyzer.processing_stats['total_sheets'], 1),
            'disagreement_rate': len(disagreement_cases) / max(analyzer.processing_stats['total_sheets'], 1)
        },
        'recommendations': generate_threshold_recommendations(analyzer, disagreement_cases)
    }
    
    threshold_file = f"threshold_analysis_{timestamp}.json"
    with open(threshold_file, 'w') as f:
        json.dump(threshold_analysis, f, indent=2)
    
    print(f"   Threshold Analysis: {threshold_file}")


def generate_threshold_recommendations(analyzer, disagreement_cases):
    """Generate specific threshold tuning recommendations."""
    recommendations = []
    
    stats = analyzer.processing_stats
    ai_usage_rate = (stats['dual_analysis'] + stats['ai_primary']) / max(stats['total_sheets'], 1)
    
    if ai_usage_rate < 0.2:
        recommendations.append({
            'type': 'increase_ai_usage',
            'current_value': analyzer.thresholds['traditional_max'],
            'suggested_value': max(0.1, analyzer.thresholds['traditional_max'] - 0.1),
            'reason': 'Low AI usage - may miss opportunities for improvement'
        })
    
    if ai_usage_rate > 0.8:
        recommendations.append({
            'type': 'decrease_ai_usage',
            'current_value': analyzer.thresholds['dual_min'],
            'suggested_value': analyzer.thresholds['dual_min'] + 0.1,
            'reason': 'High AI usage - may be unnecessarily expensive'
        })
    
    if len(disagreement_cases) < 2:
        recommendations.append({
            'type': 'increase_dual_analysis',
            'current_value': analyzer.thresholds['dual_min'],
            'suggested_value': max(0.1, analyzer.thresholds['dual_min'] - 0.1),
            'reason': 'Need more comparison data for tuning'
        })
    
    avg_cost = stats['total_cost'] / max(stats['total_sheets'], 1)
    if avg_cost > 0.05:
        recommendations.append({
            'type': 'cost_control',
            'current_value': analyzer.thresholds['max_cost_per_sheet'],
            'suggested_value': min(avg_cost * 0.8, analyzer.thresholds['max_cost_per_sheet']),
            'reason': 'High average cost per sheet'
        })
    
    return recommendations


def main():
    """Run focused data collection."""
    
    print("🎯 Starting focused data collection...")
    print("💡 This will generate tuning data and test cases\n")
    
    try:
        results, disagreement_cases = collect_tuning_data()
        
        print(f"\n🎉 COLLECTION COMPLETE!")
        print(f"   📊 Generated data from {len(results)} files")
        print(f"   🧪 Identified {len(disagreement_cases)} test cases")
        print(f"   📈 Ready for threshold tuning and unit test generation")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
