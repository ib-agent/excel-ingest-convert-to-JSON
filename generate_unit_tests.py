#!/usr/bin/env python3
"""
Unit Test Generator

This script generates comprehensive unit tests from disagreement cases
between traditional heuristics and AI analysis. These tests help:
1. Validate processing decisions
2. Regression test threshold changes  
3. Benchmark AI vs traditional performance
4. Ensure quality across complexity levels
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class UnitTestGenerator:
    """Generates unit tests from comparison disagreement cases."""
    
    def __init__(self, test_cases_file=None):
        """
        Initialize test generator.
        
        Args:
            test_cases_file: Path to test cases JSON file
        """
        self.test_cases_file = test_cases_file or self._find_latest_test_cases_file()
        self.test_cases = self._load_test_cases()
        
    def _find_latest_test_cases_file(self):
        """Find the most recent test cases file."""
        pattern = "test_cases_*.json"
        files = list(Path('.').glob(pattern))
        if not files:
            raise FileNotFoundError("No test cases files found. Run focused_data_collection.py first.")
        
        # Return most recent
        return str(sorted(files, key=os.path.getmtime)[-1])
    
    def _load_test_cases(self):
        """Load test cases from file."""
        with open(self.test_cases_file, 'r') as f:
            data = json.load(f)
        return data['test_cases']
    
    def generate_all_tests(self):
        """Generate all types of unit tests."""
        print("🧪 UNIT TEST GENERATOR")
        print("="*40)
        print(f"Source: {self.test_cases_file}")
        print(f"Test Cases: {len(self.test_cases)}\n")
        
        # Generate different types of tests
        tests = {
            'complexity_threshold_tests': self._generate_complexity_threshold_tests(),
            'processing_decision_tests': self._generate_processing_decision_tests(),
            'agreement_validation_tests': self._generate_agreement_validation_tests(),
            'regression_tests': self._generate_regression_tests(),
            'performance_benchmark_tests': self._generate_performance_benchmark_tests()
        }
        
        # Save all tests
        self._save_test_suite(tests)
        
        return tests
    
    def _generate_complexity_threshold_tests(self):
        """Generate tests for complexity threshold validation."""
        tests = []
        
        print("📊 Generating complexity threshold tests...")
        
        # Test cases by complexity level
        complexity_levels = {'simple': [], 'moderate': [], 'complex': []}
        
        for case in self.test_cases:
            complexity = case['complexity']
            if complexity < 0.3:
                complexity_levels['simple'].append(case)
            elif complexity < 0.7:
                complexity_levels['moderate'].append(case)
            else:
                complexity_levels['complex'].append(case)
        
        # Generate threshold boundary tests
        for level, cases in complexity_levels.items():
            if cases:
                test = {
                    'test_name': f'test_complexity_{level}_threshold',
                    'description': f'Validate {level} complexity processing decisions',
                    'test_type': 'threshold_validation',
                    'complexity_level': level,
                    'test_cases': cases,
                    'expected_behavior': self._get_expected_behavior(level),
                    'test_code': self._generate_threshold_test_code(level, cases)
                }
                tests.append(test)
        
        print(f"   ✅ Generated {len(tests)} threshold tests")
        return tests
    
    def _generate_processing_decision_tests(self):
        """Generate tests for processing decision validation."""
        tests = []
        
        print("🎯 Generating processing decision tests...")
        
        # Group by expected processing decision
        decision_groups = {}
        for case in self.test_cases:
            complexity = case['complexity']
            
            # Determine expected decision based on current thresholds
            if complexity < 0.2:
                expected = 'traditional_only'
            elif complexity < 0.8:
                expected = 'dual_analysis'
            else:
                expected = 'ai_primary'
            
            if expected not in decision_groups:
                decision_groups[expected] = []
            decision_groups[expected].append(case)
        
        for decision, cases in decision_groups.items():
            test = {
                'test_name': f'test_processing_decision_{decision}',
                'description': f'Validate {decision} processing decision logic',
                'test_type': 'processing_decision',
                'expected_decision': decision,
                'test_cases': cases,
                'test_code': self._generate_processing_decision_test_code(decision, cases)
            }
            tests.append(test)
        
        print(f"   ✅ Generated {len(tests)} processing decision tests")
        return tests
    
    def _generate_agreement_validation_tests(self):
        """Generate tests for agreement score validation."""
        tests = []
        
        print("⚖️  Generating agreement validation tests...")
        
        # All test cases have 0% agreement - perfect for validation
        test = {
            'test_name': 'test_disagreement_cases_detection',
            'description': 'Validate that known disagreement cases are properly detected',
            'test_type': 'agreement_validation',
            'expected_agreement_threshold': 0.3,  # Cases below this are disagreements
            'test_cases': self.test_cases,
            'test_code': self._generate_agreement_test_code()
        }
        tests.append(test)
        
        print(f"   ✅ Generated 1 agreement validation test")
        return tests
    
    def _generate_regression_tests(self):
        """Generate regression tests to prevent quality degradation."""
        tests = []
        
        print("🔄 Generating regression tests...")
        
        # Create regression test for each file
        files = {}
        for case in self.test_cases:
            file_name = case['file']
            if file_name not in files:
                files[file_name] = []
            files[file_name].append(case)
        
        for file_name, cases in files.items():
            safe_name = file_name.replace(" ", "_").replace(".", "_").replace("-", "_").replace("(", "").replace(")", "")
            test = {
                'test_name': f'test_regression_{safe_name}',
                'description': f'Regression test for {file_name}',
                'test_type': 'regression',
                'file_name': file_name,
                'expected_results': cases,
                'test_code': self._generate_regression_test_code(file_name, cases)
            }
            tests.append(test)
        
        print(f"   ✅ Generated {len(tests)} regression tests")
        return tests
    
    def _generate_performance_benchmark_tests(self):
        """Generate performance benchmark tests."""
        tests = []
        
        print("⚡ Generating performance benchmark tests...")
        
        # Overall performance test
        total_traditional = sum(case['traditional_tables'] for case in self.test_cases)
        total_ai = sum(case['ai_tables'] for case in self.test_cases)
        avg_confidence = sum(case['ai_confidence'] for case in self.test_cases) / len(self.test_cases)
        
        test = {
            'test_name': 'test_performance_benchmarks',
            'description': 'Validate system performance meets benchmarks',
            'test_type': 'performance_benchmark',
            'benchmarks': {
                'total_traditional_tables': total_traditional,
                'total_ai_tables': total_ai,
                'average_ai_confidence': avg_confidence,
                'disagreement_cases': len(self.test_cases)
            },
            'test_cases': self.test_cases,
            'test_code': self._generate_performance_test_code()
        }
        tests.append(test)
        
        print(f"   ✅ Generated 1 performance benchmark test")
        return tests
    
    def _get_expected_behavior(self, complexity_level):
        """Get expected behavior for complexity level."""
        behaviors = {
            'simple': {
                'processing_decision': 'traditional_only',
                'ai_usage': False,
                'cost_expectation': 'zero',
                'quality_expectation': 'traditional_sufficient'
            },
            'moderate': {
                'processing_decision': 'dual_analysis',
                'ai_usage': True,
                'cost_expectation': 'low_to_moderate',
                'quality_expectation': 'comparison_valuable'
            },
            'complex': {
                'processing_decision': 'ai_primary',
                'ai_usage': True,
                'cost_expectation': 'moderate_to_high',
                'quality_expectation': 'ai_superior'
            }
        }
        return behaviors.get(complexity_level, {})
    
    def _generate_threshold_test_code(self, level, cases):
        """Generate Python test code for threshold validation."""
        return f'''
def test_complexity_{level}_threshold(self):
    """Test that {level} complexity sheets get appropriate processing."""
    test_cases = {json.dumps(cases, indent=8)}
    
    for case in test_cases:
        complexity_score = case['complexity']
        expected_behavior = {json.dumps(self._get_expected_behavior(level), indent=8)}
        
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
        
        print(f"✅ {{case['file']}} - {{case['sheet']}}: {{decision}}")
'''
    
    def _generate_processing_decision_test_code(self, decision, cases):
        """Generate Python test code for processing decision validation."""
        return f'''
def test_processing_decision_{decision}(self):
    """Test that sheets get {decision} processing decision."""
    test_cases = {json.dumps(cases, indent=8)}
    
    for case in test_cases:
        complexity_score = case['complexity']
        actual_decision = self.analyzer.make_processing_decision(complexity_score)
        
        self.assertEqual(actual_decision, '{decision}')
        
        # Validate decision logic
        if '{decision}' == 'traditional_only':
            self.assertLess(complexity_score, 0.3)
        elif '{decision}' == 'dual_analysis':
            self.assertGreaterEqual(complexity_score, 0.3)
            self.assertLess(complexity_score, 0.8)
        elif '{decision}' == 'ai_primary':
            self.assertGreaterEqual(complexity_score, 0.8)
        
        print(f"✅ {{case['file']}} - {{case['sheet']}}: {{actual_decision}}")
'''
    
    def _generate_agreement_test_code(self):
        """Generate Python test code for agreement validation."""
        return f'''
def test_disagreement_cases_detection(self):
    """Test that known disagreement cases are properly identified."""
    known_disagreement_cases = {json.dumps(self.test_cases, indent=8)}
    
    for case in known_disagreement_cases:
        # Simulate comparison analysis
        agreement_score = case['agreement']
        
        # These are known disagreement cases
        self.assertLess(agreement_score, 0.3, 
                       f"Case {{case['file']}}/{{case['sheet']}} should be a disagreement")
        
        # Should be flagged for test case generation
        test_case_potential = self.comparison_engine.assess_test_case_potential(agreement_score)
        self.assertGreater(test_case_potential, 0.4)
        
        print(f"✅ Disagreement detected: {{case['file']}} - {{case['sheet']}} ({{agreement_score:.3f}})")
'''
    
    def _generate_regression_test_code(self, file_name, cases):
        """Generate Python test code for regression testing."""
        safe_name = file_name.replace(" ", "_").replace(".", "_").replace("-", "_").replace("(", "").replace(")", "")
        return f'''
def test_regression_{safe_name}(self):
    """Regression test for {file_name}."""
    expected_results = {json.dumps(cases, indent=8)}
    
    # Process the file
    file_path = "tests/test_excel/{file_name}"
    if not os.path.exists(file_path):
        self.skipTest(f"Test file not found: {{file_path}}")
    
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
        
        self.assertIsNotNone(actual_sheet, f"Sheet {{sheet_name}} not found in results")
        
        # Validate complexity is in expected range (±10%)
        expected_complexity = expected_case['complexity']
        actual_complexity = actual_sheet['complexity_analysis']['complexity_score']
        complexity_tolerance = 0.1
        
        self.assertAlmostEqual(actual_complexity, expected_complexity, 
                             delta=complexity_tolerance,
                             msg=f"Complexity score regression for {{sheet_name}}")
        
        print(f"✅ {{sheet_name}}: complexity {{actual_complexity:.3f}} (expected {{expected_complexity:.3f}})")
'''
    
    def _generate_performance_test_code(self):
        """Generate Python test code for performance benchmarks."""
        benchmarks = {
            'total_traditional_tables': sum(case['traditional_tables'] for case in self.test_cases),
            'total_ai_tables': sum(case['ai_tables'] for case in self.test_cases),
            'average_ai_confidence': sum(case['ai_confidence'] for case in self.test_cases) / len(self.test_cases),
            'disagreement_cases': len(self.test_cases)
        }
        
        return f'''
def test_performance_benchmarks(self):
    """Test that system performance meets established benchmarks."""
    benchmarks = {json.dumps(benchmarks, indent=8)}
    
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
    print(f"   Traditional tables: {{total_traditional}} (benchmark: {{benchmarks['total_traditional_tables']}})")
    print(f"   AI tables: {{total_ai}} (benchmark: {{benchmarks['total_ai_tables']}})")
    print(f"   Avg confidence: {{avg_confidence:.3f}} (benchmark: {{benchmarks['average_ai_confidence']:.3f}})")
    print(f"   Disagreements: {{disagreement_count}} (benchmark: {{benchmarks['disagreement_cases']}})")
'''
    
    def _save_test_suite(self, tests):
        """Save the complete test suite."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create complete test file
        test_file_content = self._generate_test_file_header()
        
        for test_type, test_list in tests.items():
            test_file_content += f"\n    # {test_type.replace('_', ' ').title()}\n"
            for test in test_list:
                test_file_content += test['test_code']
        
        test_file_content += self._generate_test_file_footer()
        
        # Save test file
        test_file_path = f"test_generated_unit_tests_{timestamp}.py"
        with open(test_file_path, 'w') as f:
            f.write(test_file_content)
        
        # Save test metadata
        test_metadata = {
            'generation_metadata': {
                'timestamp': datetime.now().isoformat(),
                'source_file': self.test_cases_file,
                'test_cases_count': len(self.test_cases),
                'generated_tests': {test_type: len(test_list) for test_type, test_list in tests.items()}
            },
            'test_suite': tests
        }
        
        metadata_file = f"test_metadata_{timestamp}.json"
        with open(metadata_file, 'w') as f:
            json.dump(test_metadata, f, indent=2)
        
        print(f"\n💾 GENERATED TEST SUITE:")
        print(f"   Test File: {test_file_path}")
        print(f"   Metadata: {metadata_file}")
        
        # Print summary
        total_tests = sum(len(test_list) for test_list in tests.values())
        print(f"\n📊 TEST SUITE SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        for test_type, test_list in tests.items():
            print(f"   {test_type.replace('_', ' ').title()}: {len(test_list)}")
        
        return test_file_path, metadata_file
    
    def _generate_test_file_header(self):
        """Generate the header for the test file."""
        return f'''#!/usr/bin/env python3
"""
Generated Unit Tests for Excel AI Processing System

This file was automatically generated from disagreement cases between
traditional heuristics and AI analysis. These tests validate:
- Complexity threshold decisions
- Processing decision logic  
- Agreement score calculations
- Regression prevention
- Performance benchmarks

Generated: {datetime.now().isoformat()}
Source: {self.test_cases_file}
Test Cases: {len(self.test_cases)}
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
'''
    
    def _generate_test_file_footer(self):
        """Generate the footer for the test file."""
        return '''

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
'''


def main():
    """Generate unit tests from disagreement cases."""
    
    try:
        generator = UnitTestGenerator()
        tests = generator.generate_all_tests()
        
        print(f"\n🎉 UNIT TEST GENERATION COMPLETE!")
        print(f"   📊 Test cases processed: {len(generator.test_cases)}")
        print(f"   🧪 Test categories generated: {len(tests)}")
        print(f"   📝 Ready for integration into test suite")
        
    except FileNotFoundError as e:
        print(f"❌ {str(e)}")
        print("💡 Run focused_data_collection.py first to generate test cases")
    except Exception as e:
        print(f"❌ Generation failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
