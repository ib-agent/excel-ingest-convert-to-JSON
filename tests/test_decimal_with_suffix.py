#!/usr/bin/env python3
"""
Test script to verify decimal number extraction with suffixes like 'x'
"""

import re

def test_decimal_with_suffix():
    """Test decimal number extraction with suffixes"""
    
    # Test the current decimal pattern from PDF_processing.py
    decimal_pattern = r'\b\d+\.\d+\b'
    
    # Test text containing the problematic numbers
    test_text = "Our debt-to-EBITDA ratio improved to 1.80x from 2.31x, reflecting both higher EBITDA and scheduled amortization of term debt."
    
    print("Testing decimal number extraction with suffixes...")
    print(f"Test text: {test_text}")
    print()
    
    # Debug: Test the pattern step by step
    print("Debugging regex pattern:")
    print(f"Pattern: {decimal_pattern}")
    print()
    
    # Test specific cases
    test_cases = [
        "1.80x",
        "2.31x", 
        "1.80",
        "2.31",
        "1.80x from 2.31x",
        "ratio of 1.80x",
        "improved to 1.80x"
    ]
    
    print("Testing individual cases:")
    for test_case in test_cases:
        match = re.search(decimal_pattern, test_case, re.IGNORECASE)
        if match:
            print(f"✓ '{test_case}' -> '{match.group(0)}'")
        else:
            print(f"✗ '{test_case}' -> No match")
    
    # Test the actual text
    print(f"\nTesting the actual text:")
    matches = re.finditer(decimal_pattern, test_text, re.IGNORECASE)
    
    found_decimals = []
    for match in matches:
        found_decimals.append(match.group(0))
        print(f"Found decimal: '{match.group(0)}' at position {match.start()}-{match.end()}")
    
    print(f"Total decimals found: {len(found_decimals)}")
    print(f"Decimals: {found_decimals}")
    
    # Test without word boundaries
    print(f"\nTesting without word boundaries:")
    pattern_no_boundary = r'\d+\.\d+'
    print(f"Pattern without word boundary: {pattern_no_boundary}")
    
    matches = re.finditer(pattern_no_boundary, test_text, re.IGNORECASE)
    
    found_decimals_no_boundary = []
    for match in matches:
        found_decimals_no_boundary.append(match.group(0))
        print(f"Found decimal: '{match.group(0)}' at position {match.start()}-{match.end()}")
    
    print(f"Total decimals found (no boundary): {len(found_decimals_no_boundary)}")
    print(f"Decimals: {found_decimals_no_boundary}")

if __name__ == "__main__":
    test_decimal_with_suffix() 