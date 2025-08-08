#!/usr/bin/env python3
"""
Generated Unit Tests for Excel AI Processing System

This file was automatically generated from disagreement cases between
traditional heuristics and AI analysis. These tests validate:
- Complexity threshold decisions
- Processing decision logic  
- Agreement score calculations
- Regression prevention
- Performance benchmarks

Generated: 2025-08-08T15:58:44.492387
Source: test_cases_20250808_155710.json
Test Cases: 7
"""

import unittest
import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smart_sheet_analyzer import SmartSheetAnalyzer
from converter.comparison_engine import ComparisonEngine
from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer


class TestExcelAIProcessing(unittest.TestCase):
    """Comprehensive tests for Excel AI processing system."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.analyzer = SmartSheetAnalyzer()
        cls.comparison_engine = ComparisonEngine()
        cls.complexity_analyzer = ExcelComplexityAnalyzer()
        
        print("🧪 Starting Excel AI Processing Tests")
        print("="*50)
    
    def setUp(self):
        """Set up each test."""
        pass
    
    def tearDown(self):
        """Clean up after each test."""
        pass

    # Complexity Threshold Tests

def test_complexity_simple_threshold(self):
    """Test that simple complexity sheets get appropriate processing."""
    test_cases = [
        {
                "file": "Test_SpreadSheet_100_numbers.xlsx",
                "sheet": "Sheet1",
                "complexity": 0.23264462809917358,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "Balance Sheet",
                "complexity": 0.26764220363655566,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 2,
                "ai_confidence": 0.92,
                "winner": "traditional"
        }
]
    
    for case in test_cases:
        complexity_score = case['complexity']
        expected_behavior = {
        "processing_decision": "traditional_only",
        "ai_usage": false,
        "cost_expectation": "zero",
        "quality_expectation": "traditional_sufficient"
}
        
        # Test complexity categorization
        if complexity_score < 0.3:
            self.assertEqual(self.analyzer.get_complexity_level(complexity_score), 'simple')
        elif complexity_score < 0.7:
            self.assertEqual(self.analyzer.get_complexity_level(complexity_score), 'moderate')
        else:
            self.assertEqual(self.analyzer.get_complexity_level(complexity_score), 'complex')
        
        # Test processing decision
        decision = self.analyzer.make_processing_decision(complexity_score)
        self.assertEqual(decision, expected_behavior['processing_decision'])
        
        print(f"✅ {case['file']} - {case['sheet']}: {decision}")

def test_complexity_moderate_threshold(self):
    """Test that moderate complexity sheets get appropriate processing."""
    test_cases = [
        {
                "file": "single_unit_economics_4_tables.xlsx",
                "sheet": "Rental Single Unit Economics",
                "complexity": 0.6195856576239983,
                "agreement": 0.0,
                "traditional_tables": 4,
                "ai_tables": 4,
                "ai_confidence": 0.9,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "TOTAL P&L without PT",
                "complexity": 0.36837947252801717,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "TOTAL P&L with PT",
                "complexity": 0.3357142857142857,
                "agreement": 0.0,
                "traditional_tables": 2,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "Cash Flow",
                "complexity": 0.5240481238671055,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        }
]
    
    for case in test_cases:
        complexity_score = case['complexity']
        expected_behavior = {
        "processing_decision": "dual_analysis",
        "ai_usage": true,
        "cost_expectation": "low_to_moderate",
        "quality_expectation": "comparison_valuable"
}
        
        # Test complexity categorization
        if complexity_score < 0.3:
            self.assertEqual(self.analyzer.get_complexity_level(complexity_score), 'simple')
        elif complexity_score < 0.7:
            self.assertEqual(self.analyzer.get_complexity_level(complexity_score), 'moderate')
        else:
            self.assertEqual(self.analyzer.get_complexity_level(complexity_score), 'complex')
        
        # Test processing decision
        decision = self.analyzer.make_processing_decision(complexity_score)
        self.assertEqual(decision, expected_behavior['processing_decision'])
        
        print(f"✅ {case['file']} - {case['sheet']}: {decision}")

def test_complexity_complex_threshold(self):
    """Test that complex complexity sheets get appropriate processing."""
    test_cases = [
        {
                "file": "Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles.xlsx",
                "sheet": "Sheet1",
                "complexity": 0.7429731488555018,
                "agreement": 0.0,
                "traditional_tables": 2,
                "ai_tables": 2,
                "ai_confidence": 0.95,
                "winner": "traditional"
        }
]
    
    for case in test_cases:
        complexity_score = case['complexity']
        expected_behavior = {
        "processing_decision": "ai_primary",
        "ai_usage": true,
        "cost_expectation": "moderate_to_high",
        "quality_expectation": "ai_superior"
}
        
        # Test complexity categorization
        if complexity_score < 0.3:
            self.assertEqual(self.analyzer.get_complexity_level(complexity_score), 'simple')
        elif complexity_score < 0.7:
            self.assertEqual(self.analyzer.get_complexity_level(complexity_score), 'moderate')
        else:
            self.assertEqual(self.analyzer.get_complexity_level(complexity_score), 'complex')
        
        # Test processing decision
        decision = self.analyzer.make_processing_decision(complexity_score)
        self.assertEqual(decision, expected_behavior['processing_decision'])
        
        print(f"✅ {case['file']} - {case['sheet']}: {decision}")

    # Processing Decision Tests

def test_processing_decision_dual_analysis(self):
    """Test that sheets get dual_analysis processing decision."""
    test_cases = [
        {
                "file": "single_unit_economics_4_tables.xlsx",
                "sheet": "Rental Single Unit Economics",
                "complexity": 0.6195856576239983,
                "agreement": 0.0,
                "traditional_tables": 4,
                "ai_tables": 4,
                "ai_confidence": 0.9,
                "winner": "traditional"
        },
        {
                "file": "Test_SpreadSheet_100_numbers.xlsx",
                "sheet": "Sheet1",
                "complexity": 0.23264462809917358,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles.xlsx",
                "sheet": "Sheet1",
                "complexity": 0.7429731488555018,
                "agreement": 0.0,
                "traditional_tables": 2,
                "ai_tables": 2,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "TOTAL P&L without PT",
                "complexity": 0.36837947252801717,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "TOTAL P&L with PT",
                "complexity": 0.3357142857142857,
                "agreement": 0.0,
                "traditional_tables": 2,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "Cash Flow",
                "complexity": 0.5240481238671055,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "Balance Sheet",
                "complexity": 0.26764220363655566,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 2,
                "ai_confidence": 0.92,
                "winner": "traditional"
        }
]
    
    for case in test_cases:
        complexity_score = case['complexity']
        actual_decision = self.analyzer.make_processing_decision(complexity_score)
        
        self.assertEqual(actual_decision, 'dual_analysis')
        
        # Validate decision logic
        if 'dual_analysis' == 'traditional_only':
            self.assertLess(complexity_score, 0.3)
        elif 'dual_analysis' == 'dual_analysis':
            self.assertGreaterEqual(complexity_score, 0.3)
            self.assertLess(complexity_score, 0.8)
        elif 'dual_analysis' == 'ai_primary':
            self.assertGreaterEqual(complexity_score, 0.8)
        
        print(f"✅ {case['file']} - {case['sheet']}: {actual_decision}")

    # Agreement Validation Tests

def test_disagreement_cases_detection(self):
    """Test that known disagreement cases are properly identified."""
    known_disagreement_cases = [
        {
                "file": "single_unit_economics_4_tables.xlsx",
                "sheet": "Rental Single Unit Economics",
                "complexity": 0.6195856576239983,
                "agreement": 0.0,
                "traditional_tables": 4,
                "ai_tables": 4,
                "ai_confidence": 0.9,
                "winner": "traditional"
        },
        {
                "file": "Test_SpreadSheet_100_numbers.xlsx",
                "sheet": "Sheet1",
                "complexity": 0.23264462809917358,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles.xlsx",
                "sheet": "Sheet1",
                "complexity": 0.7429731488555018,
                "agreement": 0.0,
                "traditional_tables": 2,
                "ai_tables": 2,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "TOTAL P&L without PT",
                "complexity": 0.36837947252801717,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "TOTAL P&L with PT",
                "complexity": 0.3357142857142857,
                "agreement": 0.0,
                "traditional_tables": 2,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "Cash Flow",
                "complexity": 0.5240481238671055,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "Balance Sheet",
                "complexity": 0.26764220363655566,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 2,
                "ai_confidence": 0.92,
                "winner": "traditional"
        }
]
    
    for case in known_disagreement_cases:
        # Simulate comparison analysis
        agreement_score = case['agreement']
        
        # These are known disagreement cases
        self.assertLess(agreement_score, 0.3, 
                       f"Case {case['file']}/{case['sheet']} should be a disagreement")
        
        # Should be flagged for test case generation
        test_case_potential = self.comparison_engine.assess_test_case_potential(agreement_score)
        self.assertGreater(test_case_potential, 0.4)
        
        print(f"✅ Disagreement detected: {case['file']} - {case['sheet']} ({agreement_score:.3f})")

    # Regression Tests

def test_regression_single_unit_economics_4_tables_xlsx(self):
    """Regression test for single_unit_economics_4_tables.xlsx."""
    expected_results = [
        {
                "file": "single_unit_economics_4_tables.xlsx",
                "sheet": "Rental Single Unit Economics",
                "complexity": 0.6195856576239983,
                "agreement": 0.0,
                "traditional_tables": 4,
                "ai_tables": 4,
                "ai_confidence": 0.9,
                "winner": "traditional"
        }
]
    
    # Process the file
    file_path = "tests/test_excel/single_unit_economics_4_tables.xlsx"
    if not os.path.exists(file_path):
        self.skipTest(f"Test file not found: {file_path}")
    
    result = self.analyzer.analyze_file_intelligently(file_path)
    
    # Validate each expected case
    for expected_case in expected_results:
        sheet_name = expected_case['sheet']
        
        # Find matching sheet in results
        actual_sheet = None
        for sheet in result['sheets']:
            if sheet['sheet_name'] == sheet_name:
                actual_sheet = sheet
                break
        
        self.assertIsNotNone(actual_sheet, f"Sheet {sheet_name} not found in results")
        
        # Validate complexity is in expected range (±10%)
        expected_complexity = expected_case['complexity']
        actual_complexity = actual_sheet['complexity_analysis']['complexity_score']
        complexity_tolerance = 0.1
        
        self.assertAlmostEqual(actual_complexity, expected_complexity, 
                             delta=complexity_tolerance,
                             msg=f"Complexity score regression for {sheet_name}")
        
        print(f"✅ {sheet_name}: complexity {actual_complexity:.3f} (expected {expected_complexity:.3f})")

def test_regression_Test_SpreadSheet_100_numbers_xlsx(self):
    """Regression test for Test_SpreadSheet_100_numbers.xlsx."""
    expected_results = [
        {
                "file": "Test_SpreadSheet_100_numbers.xlsx",
                "sheet": "Sheet1",
                "complexity": 0.23264462809917358,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        }
]
    
    # Process the file
    file_path = "tests/test_excel/Test_SpreadSheet_100_numbers.xlsx"
    if not os.path.exists(file_path):
        self.skipTest(f"Test file not found: {file_path}")
    
    result = self.analyzer.analyze_file_intelligently(file_path)
    
    # Validate each expected case
    for expected_case in expected_results:
        sheet_name = expected_case['sheet']
        
        # Find matching sheet in results
        actual_sheet = None
        for sheet in result['sheets']:
            if sheet['sheet_name'] == sheet_name:
                actual_sheet = sheet
                break
        
        self.assertIsNotNone(actual_sheet, f"Sheet {sheet_name} not found in results")
        
        # Validate complexity is in expected range (±10%)
        expected_complexity = expected_case['complexity']
        actual_complexity = actual_sheet['complexity_analysis']['complexity_score']
        complexity_tolerance = 0.1
        
        self.assertAlmostEqual(actual_complexity, expected_complexity, 
                             delta=complexity_tolerance,
                             msg=f"Complexity score regression for {sheet_name}")
        
        print(f"✅ {sheet_name}: complexity {actual_complexity:.3f} (expected {expected_complexity:.3f})")

def test_regression_Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles_xlsx(self):
    """Regression test for Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles.xlsx."""
    expected_results = [
        {
                "file": "Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles.xlsx",
                "sheet": "Sheet1",
                "complexity": 0.7429731488555018,
                "agreement": 0.0,
                "traditional_tables": 2,
                "ai_tables": 2,
                "ai_confidence": 0.95,
                "winner": "traditional"
        }
]
    
    # Process the file
    file_path = "tests/test_excel/Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles.xlsx"
    if not os.path.exists(file_path):
        self.skipTest(f"Test file not found: {file_path}")
    
    result = self.analyzer.analyze_file_intelligently(file_path)
    
    # Validate each expected case
    for expected_case in expected_results:
        sheet_name = expected_case['sheet']
        
        # Find matching sheet in results
        actual_sheet = None
        for sheet in result['sheets']:
            if sheet['sheet_name'] == sheet_name:
                actual_sheet = sheet
                break
        
        self.assertIsNotNone(actual_sheet, f"Sheet {sheet_name} not found in results")
        
        # Validate complexity is in expected range (±10%)
        expected_complexity = expected_case['complexity']
        actual_complexity = actual_sheet['complexity_analysis']['complexity_score']
        complexity_tolerance = 0.1
        
        self.assertAlmostEqual(actual_complexity, expected_complexity, 
                             delta=complexity_tolerance,
                             msg=f"Complexity score regression for {sheet_name}")
        
        print(f"✅ {sheet_name}: complexity {actual_complexity:.3f} (expected {expected_complexity:.3f})")

def test_regression_pDD10b_-_Exos_2023_financials_xlsx(self):
    """Regression test for pDD10b - Exos_2023_financials.xlsx."""
    expected_results = [
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "TOTAL P&L without PT",
                "complexity": 0.36837947252801717,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "TOTAL P&L with PT",
                "complexity": 0.3357142857142857,
                "agreement": 0.0,
                "traditional_tables": 2,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "Cash Flow",
                "complexity": 0.5240481238671055,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 1,
                "ai_confidence": 0.95,
                "winner": "traditional"
        },
        {
                "file": "pDD10b - Exos_2023_financials.xlsx",
                "sheet": "Balance Sheet",
                "complexity": 0.26764220363655566,
                "agreement": 0.0,
                "traditional_tables": 1,
                "ai_tables": 2,
                "ai_confidence": 0.92,
                "winner": "traditional"
        }
]
    
    # Process the file
    file_path = "tests/test_excel/pDD10b - Exos_2023_financials.xlsx"
    if not os.path.exists(file_path):
        self.skipTest(f"Test file not found: {file_path}")
    
    result = self.analyzer.analyze_file_intelligently(file_path)
    
    # Validate each expected case
    for expected_case in expected_results:
        sheet_name = expected_case['sheet']
        
        # Find matching sheet in results
        actual_sheet = None
        for sheet in result['sheets']:
            if sheet['sheet_name'] == sheet_name:
                actual_sheet = sheet
                break
        
        self.assertIsNotNone(actual_sheet, f"Sheet {sheet_name} not found in results")
        
        # Validate complexity is in expected range (±10%)
        expected_complexity = expected_case['complexity']
        actual_complexity = actual_sheet['complexity_analysis']['complexity_score']
        complexity_tolerance = 0.1
        
        self.assertAlmostEqual(actual_complexity, expected_complexity, 
                             delta=complexity_tolerance,
                             msg=f"Complexity score regression for {sheet_name}")
        
        print(f"✅ {sheet_name}: complexity {actual_complexity:.3f} (expected {expected_complexity:.3f})")

    # Performance Benchmark Tests

def test_performance_benchmarks(self):
    """Test that system performance meets established benchmarks."""
    benchmarks = {
        "total_traditional_tables": 12,
        "total_ai_tables": 12,
        "average_ai_confidence": 0.9385714285714286,
        "disagreement_cases": 7
}
    
    # Run analysis on benchmark files
    benchmark_files = [
        "tests/test_excel/single_unit_economics_4_tables.xlsx",
        "tests/test_excel/Test_SpreadSheet_100_numbers.xlsx",
        "tests/test_excel/pDD10b - Exos_2023_financials.xlsx"
    ]
    
    total_traditional = 0
    total_ai = 0
    confidence_scores = []
    disagreement_count = 0
    
    for file_path in benchmark_files:
        if os.path.exists(file_path):
            result = self.analyzer.analyze_file_intelligently(file_path)
            
            for sheet in result['sheets']:
                if 'traditional_analysis' in sheet:
                    total_traditional += sheet['traditional_analysis']['tables_found']
                
                if 'ai_analysis' in sheet and sheet['ai_analysis']['success']:
                    total_ai += sheet['ai_analysis']['tables_found']
                    confidence_scores.append(sheet['ai_analysis']['confidence'])
                
                if 'comparison' in sheet and sheet['comparison']:
                    agreement = sheet['comparison']['metrics']['agreement_score']
                    if agreement < 0.3:
                        disagreement_count += 1
    
    # Validate benchmarks (allow 20% variance)
    self.assertGreaterEqual(total_traditional, benchmarks['total_traditional_tables'] * 0.8)
    self.assertGreaterEqual(total_ai, benchmarks['total_ai_tables'] * 0.8)
    
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        self.assertGreaterEqual(avg_confidence, benchmarks['average_ai_confidence'] * 0.9)
    
    self.assertGreaterEqual(disagreement_count, benchmarks['disagreement_cases'] * 0.5)
    
    print(f"✅ Performance benchmarks met")
    print(f"   Traditional tables: {total_traditional} (benchmark: {benchmarks['total_traditional_tables']})")
    print(f"   AI tables: {total_ai} (benchmark: {benchmarks['total_ai_tables']})")
    print(f"   Avg confidence: {avg_confidence:.3f} (benchmark: {benchmarks['average_ai_confidence']:.3f})")
    print(f"   Disagreements: {disagreement_count} (benchmark: {benchmarks['disagreement_cases']})")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
