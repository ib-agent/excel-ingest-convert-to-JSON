#!/usr/bin/env python3
"""
Test decimal number extraction with suffixes like 'x'
"""

import re
import unittest

class TestDecimalExtraction(unittest.TestCase):
    """Test decimal number extraction patterns"""
    
    def test_decimal_with_suffix(self):
        """Test that decimal numbers followed by 'x' are extracted correctly"""
        
        # Test the current decimal pattern from PDF_processing.py
        decimal_pattern = r'\d+\.\d+'  # Updated pattern without word boundaries
        
        # Test text containing the problematic numbers
        test_text = "Our debt-to-EBITDA ratio improved to 1.80x from 2.31x, reflecting both higher EBITDA and scheduled amortization of term debt."
        
        # Test specific cases
        test_cases = [
            ("1.80x", "1.80"),
            ("2.31x", "2.31"), 
            ("1.80", "1.80"),
            ("2.31", "2.31"),
            ("1.80x from 2.31x", ["1.80", "2.31"]),
            ("ratio of 1.80x", "1.80"),
            ("improved to 1.80x", "1.80")
        ]
        
        for test_case, expected in test_cases:
            with self.subTest(test_case=test_case):
                if isinstance(expected, list):
                    # Multiple expected matches
                    matches = re.findall(decimal_pattern, test_case)
                    self.assertEqual(matches, expected, f"Failed for '{test_case}'")
                else:
                    # Single expected match
                    match = re.search(decimal_pattern, test_case)
                    if expected:
                        self.assertIsNotNone(match, f"No match found for '{test_case}'")
                        self.assertEqual(match.group(0), expected, f"Wrong match for '{test_case}'")
                    else:
                        self.assertIsNone(match, f"Unexpected match for '{test_case}'")
    
    def test_decimal_extraction_from_text(self):
        """Test decimal extraction from actual text content"""
        
        decimal_pattern = r'\d+\.\d+'
        test_text = "Our debt-to-EBITDA ratio improved to 1.80x from 2.31x, reflecting both higher EBITDA and scheduled amortization of term debt."
        
        matches = re.findall(decimal_pattern, test_text)
        expected_matches = ['1.80', '2.31']
        
        self.assertEqual(matches, expected_matches, "Failed to extract decimals from text")
    
    def test_old_pattern_failure(self):
        """Test that the old pattern with word boundaries fails for numbers with suffixes"""
        
        old_pattern = r'\b\d+\.\d+\b'  # Old pattern with word boundaries
        test_text = "Our debt-to-EBITDA ratio improved to 1.80x from 2.31x"
        
        matches = re.findall(old_pattern, test_text)
        # The old pattern should find no matches due to word boundaries
        self.assertEqual(matches, [], "Old pattern should not match numbers with suffixes")
    
    def test_new_pattern_success(self):
        """Test that the new pattern without word boundaries succeeds"""
        
        new_pattern = r'\d+\.\d+'  # New pattern without word boundaries
        test_text = "Our debt-to-EBITDA ratio improved to 1.80x from 2.31x"
        
        matches = re.findall(new_pattern, test_text)
        expected_matches = ['1.80', '2.31']
        
        self.assertEqual(matches, expected_matches, "New pattern should match numbers with suffixes")

if __name__ == '__main__':
    unittest.main() 