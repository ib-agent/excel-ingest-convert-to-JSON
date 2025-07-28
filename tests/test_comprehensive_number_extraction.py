#!/usr/bin/env python3
"""
Comprehensive test for all number extraction fixes
"""

import json
import unittest
import os
import sys
sys.path.append('..')
from PDF_processing import PDFProcessor

class TestComprehensiveNumberExtraction(unittest.TestCase):
    """Test that all number extraction fixes are working correctly"""
    
    def setUp(self):
        """Set up test data"""
        # Try different possible paths for the test file
        possible_paths = [
            'test_pdfs/synthetic_financial_report.pdf',
            'tests/test_pdfs/synthetic_financial_report.pdf',
            'tests/test_pdfs/synthetic_financial_report.pdf'
        ]
        
        self.test_file = None
        for path in possible_paths:
            if os.path.exists(path):
                self.test_file = path
                break
        
        if not self.test_file:
            raise FileNotFoundError("Could not find synthetic_financial_report.pdf in any expected location")
        
        self.processor = PDFProcessor()
        
        # Process the test file if result doesn't exist
        self.result_file = 'synthetic_financial_report_tables_fixed_v3.json'
        if not os.path.exists(self.result_file):
            result = self.processor.process_file(
                self.test_file, 
                extract_tables=True, 
                extract_text=True, 
                extract_numbers=True
            )
            with open(self.result_file, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Load the test result
        with open(self.result_file, 'r') as f:
            self.data = json.load(f)
    
    def test_percentage_extraction(self):
        """Test that percentage extraction (5.5%) is working"""
        
        pdf_result = self.data.get('pdf_processing_result', {})
        text_content = pdf_result.get('text_content', {}).get('text_content', {})
        
        # Find paragraph 3 (should contain 5.5%)
        paragraph_3 = None
        for page in text_content.get('pages', []):
            for section in page.get('sections', []):
                if section.get('section_id') == 'page_1_section_3':
                    paragraph_3 = section
                    break
            if paragraph_3:
                break
        
        self.assertIsNotNone(paragraph_3, "Paragraph 3 not found")
        
        numbers = paragraph_3.get('numbers', [])
        found_55_percent = False
        
        for number in numbers:
            if number.get('original_text') == '5.5%':
                found_55_percent = True
                break
        
        self.assertTrue(found_55_percent, "5.5% not found in paragraph 3")
    
    def test_decimal_extraction_paragraph_3(self):
        """Test that decimal extraction (1.08) is working in paragraph 3"""
        
        pdf_result = self.data.get('pdf_processing_result', {})
        text_content = pdf_result.get('text_content', {}).get('text_content', {})
        
        # Find paragraph 3
        paragraph_3 = None
        for page in text_content.get('pages', []):
            for section in page.get('sections', []):
                if section.get('section_id') == 'page_1_section_3':
                    paragraph_3 = section
                    break
            if paragraph_3:
                break
        
        self.assertIsNotNone(paragraph_3, "Paragraph 3 not found")
        
        numbers = paragraph_3.get('numbers', [])
        found_108 = False
        
        for number in numbers:
            if number.get('original_text') == '1.08':
                found_108 = True
                break
        
        self.assertTrue(found_108, "1.08 not found in paragraph 3")
    
    def test_decimal_extraction_paragraph_5(self):
        """Test that decimal extraction (87.1, 67.3) is working in paragraph 5"""
        
        pdf_result = self.data.get('pdf_processing_result', {})
        text_content = pdf_result.get('text_content', {}).get('text_content', {})
        
        # Find paragraph 5
        paragraph_5 = None
        for page in text_content.get('pages', []):
            for section in page.get('sections', []):
                if section.get('section_id') == 'page_1_section_5':
                    paragraph_5 = section
                    break
            if paragraph_5:
                break
        
        self.assertIsNotNone(paragraph_5, "Paragraph 5 not found")
        
        numbers = paragraph_5.get('numbers', [])
        found_871 = False
        found_673 = False
        
        for number in numbers:
            if number.get('original_text') == '87.1':
                found_871 = True
            elif number.get('original_text') == '67.3':
                found_673 = True
        
        self.assertTrue(found_871, "87.1 not found in paragraph 5")
        self.assertTrue(found_673, "67.3 not found in paragraph 5")
    
    def test_decimal_with_suffix_extraction(self):
        """Test that decimal extraction with suffixes (1.80, 2.31) is working in paragraph 7"""
        
        pdf_result = self.data.get('pdf_processing_result', {})
        text_content = pdf_result.get('text_content', {}).get('text_content', {})
        
        # Find paragraph 7
        paragraph_7 = None
        for page in text_content.get('pages', []):
            for section in page.get('sections', []):
                if section.get('section_id') == 'page_1_section_7':
                    paragraph_7 = section
                    break
            if paragraph_7:
                break
        
        self.assertIsNotNone(paragraph_7, "Paragraph 7 not found")
        
        numbers = paragraph_7.get('numbers', [])
        found_180 = False
        found_231 = False
        
        for number in numbers:
            if number.get('original_text') == '1.80':
                found_180 = True
            elif number.get('original_text') == '2.31':
                found_231 = True
        
        self.assertTrue(found_180, "1.80 not found in paragraph 7")
        self.assertTrue(found_231, "2.31 not found in paragraph 7")
    
    def test_overall_number_count(self):
        """Test that the overall number count has improved"""
        
        processing_summary = self.data.get('pdf_processing_result', {}).get('processing_summary', {})
        total_numbers = processing_summary.get('numbers_found', 0)
        
        # Should have at least 29 numbers (improved from original 20)
        self.assertGreaterEqual(total_numbers, 29, f"Expected at least 29 numbers, got {total_numbers}")
    
    def test_confidence_threshold_for_decimals(self):
        """Test that decimal numbers have appropriate confidence scores"""
        
        pdf_result = self.data.get('pdf_processing_result', {})
        text_content = pdf_result.get('text_content', {}).get('text_content', {})
        
        # Check that decimal numbers have confidence >= 0.7
        for page in text_content.get('pages', []):
            for section in page.get('sections', []):
                for number in section.get('numbers', []):
                    if number.get('format') == 'decimal':
                        confidence = number.get('confidence', 0)
                        self.assertGreaterEqual(confidence, 0.7, 
                            f"Decimal number {number.get('original_text')} has low confidence: {confidence}")

if __name__ == '__main__':
    unittest.main() 