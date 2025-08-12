#!/usr/bin/env python3
"""
Test Framework for Clean PDF Processor

Systematic testing with known expected outputs:
1. Test individual components in isolation
2. Test complete pipeline with escalating complexity
3. Compare results with expected values
4. Generate detailed reports on test outcomes
"""

import unittest
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

from clean_pdf_processor import CleanPDFProcessor, SimpleTableExtractor, TextExtractor, NumberExtractor

# Configure test logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PDFTestExpectation:
    """Expected results for a test case"""
    name: str
    pdf_file: str
    expected_tables: int
    expected_table_dimensions: List[tuple]  # [(rows, cols), ...]
    expected_text_sections: int
    expected_numbers: int
    min_paragraphs_page1: int = 0
    min_paragraphs_page2: int = 0
    description: str = ""

class PDFProcessorTestSuite:
    """Comprehensive test suite for PDF processing pipeline"""
    
    def __init__(self):
        self.processor = CleanPDFProcessor()
        self.test_results = []
        
        # Define test cases with expected results - ordered by complexity
        self.test_cases = [
            # Existing files in the test_pdfs directory
            PDFTestExpectation(
                name="Test_PDF_Table_100_numbers",
                pdf_file="tests/test_pdfs/Test_PDF_Table_100_numbers.pdf",
                expected_tables=1,
                expected_table_dimensions=[(10, 10)],  # Large table with 100 numbers
                expected_text_sections=2,  # Minimal text
                expected_numbers=0,  # All numbers should be in table
                min_paragraphs_page1=0,
                min_paragraphs_page2=0,
                description="Simple test: single large table with 100 numbers, minimal text"
            ),
            PDFTestExpectation(
                name="Test_PDF_with_3_numbers_in_large_paragraphs",
                pdf_file="tests/test_pdfs/Test_PDF_with_3_numbers_in_large_paragraphs.pdf", 
                expected_tables=0,
                expected_table_dimensions=[],
                expected_text_sections=5,  # Estimated paragraph sections
                expected_numbers=3,  # Only 3 numbers embedded in text
                min_paragraphs_page1=3,
                min_paragraphs_page2=0,
                description="Text-only test: large paragraphs with exactly 3 embedded numbers"
            ),
            PDFTestExpectation(
                name="Test_PDF_Table_9_numbers_with_before_and_after_paragraphs",
                pdf_file="tests/test_pdfs/Test_PDF_Table_9_numbers_with_before_and_after_paragraphs.pdf",
                expected_tables=1,
                expected_table_dimensions=[(3, 3)],  # 3x3 table = 9 numbers
                expected_text_sections=6,  # Before and after paragraphs
                expected_numbers=5,  # Some numbers in text, most in table
                min_paragraphs_page1=4,
                min_paragraphs_page2=0,
                description="Mixed test: small table with surrounding paragraph text"
            ),
            PDFTestExpectation(
                name="synthetic_financial_report",
                pdf_file="tests/test_pdfs/synthetic_financial_report.pdf",
                expected_tables=2,
                expected_table_dimensions=[(4, 5), (41, 7)],  # Page 1 table + spanning table
                expected_text_sections=13,  # 11 paragraphs page 1 + 2 paragraphs page 2
                expected_numbers=25,  # Rough estimate - will be refined
                min_paragraphs_page1=11,
                min_paragraphs_page2=2,
                description="Complex test: full synthetic financial report with tables and paragraphs"
            )
        ]
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases and return summary results"""
        logger.info("Starting comprehensive PDF processor test suite")
        
        overall_results = {
            'test_summary': {
                'total_tests': len(self.test_cases),
                'passed': 0,
                'failed': 0,
                'warnings': 0
            },
            'test_details': []
        }
        
        for test_case in self.test_cases:
            result = self.run_single_test(test_case)
            overall_results['test_details'].append(result)
            
            if result['status'] == 'PASSED':
                overall_results['test_summary']['passed'] += 1
            elif result['status'] == 'FAILED':
                overall_results['test_summary']['failed'] += 1
            else:
                overall_results['test_summary']['warnings'] += 1
        
        # Save detailed results
        with open('test_results_clean_processor.json', 'w') as f:
            json.dump(overall_results, f, indent=2, ensure_ascii=False)
        
        self._print_test_summary(overall_results)
        return overall_results
    
    def run_single_test(self, test_case: PDFTestExpectation) -> Dict[str, Any]:
        """Run a single test case and return detailed results"""
        logger.info(f"Running test: {test_case.name}")
        
        # Check if test file exists
        if not Path(test_case.pdf_file).exists():
            return {
                'test_name': test_case.name,
                'status': 'FAILED',
                'error': f"Test file not found: {test_case.pdf_file}",
                'expected': self._expectation_to_dict(test_case),
                'actual': {}
            }
        
        try:
            # Process the PDF
            result = self.processor.process(test_case.pdf_file)
            
            # Extract actual values
            actual = {
                'tables': len(result['tables']),
                'table_dimensions': [(t['dimensions']['rows'], t['dimensions']['cols']) for t in result['tables']],
                'text_sections': len(result['text_sections']),
                'numbers': len(result['numbers']),
                'paragraphs_by_page': self._count_paragraphs_by_page(result['text_sections'])
            }
            
            # Compare with expectations
            comparison = self._compare_results(test_case, actual)
            
            return {
                'test_name': test_case.name,
                'status': comparison['status'],
                'score': comparison['score'],
                'issues': comparison['issues'],
                'expected': self._expectation_to_dict(test_case),
                'actual': actual,
                'detailed_results': result['processing_summary']
            }
            
        except Exception as e:
            logger.error(f"Test {test_case.name} failed with exception: {e}")
            return {
                'test_name': test_case.name,
                'status': 'FAILED',
                'error': str(e),
                'expected': self._expectation_to_dict(test_case),
                'actual': {}
            }
    
    def _expectation_to_dict(self, expectation: PDFTestExpectation) -> Dict[str, Any]:
        """Convert test expectation to dictionary"""
        return {
            'tables': expectation.expected_tables,
            'table_dimensions': expectation.expected_table_dimensions,
            'text_sections': expectation.expected_text_sections,
            'numbers': expectation.expected_numbers,
            'min_paragraphs_page1': expectation.min_paragraphs_page1,
            'min_paragraphs_page2': expectation.min_paragraphs_page2
        }
    
    def _count_paragraphs_by_page(self, text_sections: List[Dict]) -> Dict[int, int]:
        """Count text sections (paragraphs) by page number"""
        page_counts = {}
        for section in text_sections:
            page = section['page_number']
            page_counts[page] = page_counts.get(page, 0) + 1
        return page_counts
    
    def _compare_results(self, expected: PDFTestExpectation, actual: Dict[str, Any]) -> Dict[str, Any]:
        """Compare actual results with expectations"""
        issues = []
        score = 0
        max_score = 6  # Number of criteria we're checking
        
        # Check tables count
        if actual['tables'] == expected.expected_tables:
            score += 1
        else:
            issues.append(f"Table count mismatch: expected {expected.expected_tables}, got {actual['tables']}")
        
        # Check table dimensions
        if actual['table_dimensions'] == expected.expected_table_dimensions:
            score += 1
        else:
            issues.append(f"Table dimensions mismatch: expected {expected.expected_table_dimensions}, got {actual['table_dimensions']}")
        
        # Check text sections (allow some tolerance)
        text_tolerance = 3  # Allow +/- 3 sections
        if abs(actual['text_sections'] - expected.expected_text_sections) <= text_tolerance:
            score += 1
        else:
            issues.append(f"Text sections count outside tolerance: expected {expected.expected_text_sections}±{text_tolerance}, got {actual['text_sections']}")
        
        # Check numbers (allow some tolerance)
        number_tolerance = 5  # Allow +/- 5 numbers
        if abs(actual['numbers'] - expected.expected_numbers) <= number_tolerance:
            score += 1
        else:
            issues.append(f"Numbers count outside tolerance: expected {expected.expected_numbers}±{number_tolerance}, got {actual['numbers']}")
        
        # Check page 1 paragraphs
        page1_count = actual['paragraphs_by_page'].get(1, 0)
        if page1_count >= expected.min_paragraphs_page1:
            score += 1
        else:
            issues.append(f"Page 1 paragraphs below minimum: expected ≥{expected.min_paragraphs_page1}, got {page1_count}")
        
        # Check page 2 paragraphs
        page2_count = actual['paragraphs_by_page'].get(2, 0)
        if page2_count >= expected.min_paragraphs_page2:
            score += 1
        else:
            issues.append(f"Page 2 paragraphs below minimum: expected ≥{expected.min_paragraphs_page2}, got {page2_count}")
        
        # Determine overall status
        if score == max_score:
            status = 'PASSED'
        elif score >= max_score * 0.7:  # 70% or better
            status = 'WARNING'
        else:
            status = 'FAILED'
        
        return {
            'status': status,
            'score': score,
            'max_score': max_score,
            'issues': issues
        }
    
    def _print_test_summary(self, results: Dict[str, Any]):
        """Print a formatted test summary"""
        print("\n" + "="*60)
        print("PDF PROCESSOR TEST SUITE RESULTS")
        print("="*60)
        
        summary = results['test_summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Warnings: {summary['warnings']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {(summary['passed']/summary['total_tests']*100):.1f}%")
        
        print("\nDETAILED RESULTS:")
        print("-"*60)
        
        for test in results['test_details']:
            status_symbol = "✓" if test['status'] == 'PASSED' else "⚠" if test['status'] == 'WARNING' else "✗"
            print(f"{status_symbol} {test['test_name']}: {test['status']}")
            
            if test['status'] != 'PASSED' and 'issues' in test:
                for issue in test['issues']:
                    print(f"    - {issue}")
            
            if 'score' in test:
                print(f"    Score: {test['score']}/{test.get('max_score', 'N/A')}")
        
        print("\n" + "="*60)

class ComponentTestSuite:
    """Test individual components in isolation"""
    
    def __init__(self):
        self.table_extractor = SimpleTableExtractor()
        self.text_extractor = TextExtractor()
        self.number_extractor = NumberExtractor()
    
    def test_table_extraction_only(self, pdf_path: str) -> Dict[str, Any]:
        """Test just the table extraction component"""
        logger.info(f"Testing table extraction on: {pdf_path}")
        
        tables = self.table_extractor.extract_tables(pdf_path)
        
        result = {
            'component': 'table_extraction',
            'pdf_file': pdf_path,
            'tables_found': len(tables),
            'table_details': []
        }
        
        for i, table in enumerate(tables):
            result['table_details'].append({
                'table_index': i,
                'page': table.page_number,
                'dimensions': f"{table.rows}x{table.cols}",
                'accuracy': table.accuracy,
                'method': table.method,
                'bbox': table.bbox
            })
        
        return result
    
    def test_text_extraction_with_exclusions(self, pdf_path: str, exclusion_zones: Dict) -> Dict[str, Any]:
        """Test text extraction with exclusion zones"""
        logger.info(f"Testing text extraction with exclusions on: {pdf_path}")
        
        text_sections = self.text_extractor.extract_text_excluding_areas(pdf_path, exclusion_zones)
        
        result = {
            'component': 'text_extraction',
            'pdf_file': pdf_path,
            'text_sections_found': len(text_sections),
            'sections_by_page': {}
        }
        
        for section in text_sections:
            page = section.page_number
            if page not in result['sections_by_page']:
                result['sections_by_page'][page] = []
            
            result['sections_by_page'][page].append({
                'content_preview': section.content[:100] + "..." if len(section.content) > 100 else section.content,
                'bbox': section.bbox
            })
        
        return result

def main():
    """Run the complete test suite"""
    import sys
    
    # Check if we should run component tests or full suite
    if len(sys.argv) > 1 and sys.argv[1] == '--components':
        # Run component tests
        component_suite = ComponentTestSuite()
        pdf_path = "tests/test_pdfs/synthetic_financial_report.pdf"
        
        if Path(pdf_path).exists():
            print("Running component tests...")
            
            # Test table extraction
            table_result = component_suite.test_table_extraction_only(pdf_path)
            print(f"Table extraction: {table_result['tables_found']} tables found")
            
            # Test text extraction (with empty exclusions for now)
            text_result = component_suite.test_text_extraction_with_exclusions(pdf_path, {})
            print(f"Text extraction: {text_result['text_sections_found']} sections found")
            
            # Save component test results
            with open('component_test_results.json', 'w') as f:
                json.dump({'table_test': table_result, 'text_test': text_result}, f, indent=2)
        else:
            print(f"Test file not found: {pdf_path}")
    else:
        # Run full test suite
        test_suite = PDFProcessorTestSuite()
        results = test_suite.run_all_tests()

if __name__ == "__main__":
    main() 