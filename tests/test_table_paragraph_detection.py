#!/usr/bin/env python3
"""
Test script to verify table and paragraph detection improvements

This script tests that:
1. Tables are correctly extracted as structured data
2. Table content is not duplicated in text sections
3. Text sections are still extracted when no tables are present
"""

import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PDF_processing import PDFProcessor

def test_pdf_processing(pdf_path, expected_tables, expected_text_sections, expected_numbers):
    """
    Test PDF processing and verify results match expectations
    
    Args:
        pdf_path: Path to the PDF file
        expected_tables: Expected number of tables
        expected_text_sections: Expected number of text sections
        expected_numbers: Expected number of numbers found
    """
    print(f"\nTesting: {pdf_path}")
    print("=" * 50)
    
    try:
        # Initialize processor
        processor = PDFProcessor()
        
        # Process PDF
        result = processor.process_file(
            pdf_path, 
            extract_tables=True, 
            extract_text=True, 
            extract_numbers=True
        )
        
        # Extract results
        summary = result['pdf_processing_result']['processing_summary']
        tables_extracted = summary['tables_extracted']
        text_sections = summary['text_sections']
        numbers_found = summary['numbers_found']
        
        # Print results
        print(f"Tables extracted: {tables_extracted}")
        print(f"Text sections: {text_sections}")
        print(f"Numbers found: {numbers_found}")
        
        # Check expectations
        success = True
        if tables_extracted != expected_tables:
            print(f"❌ Expected {expected_tables} tables, got {tables_extracted}")
            success = False
        else:
            print(f"✅ Tables: {tables_extracted}/{expected_tables}")
            
        if text_sections != expected_text_sections:
            print(f"❌ Expected {expected_text_sections} text sections, got {text_sections}")
            success = False
        else:
            print(f"✅ Text sections: {text_sections}/{expected_text_sections}")
            
        if numbers_found != expected_numbers:
            print(f"❌ Expected {expected_numbers} numbers, got {numbers_found}")
            success = False
        else:
            print(f"✅ Numbers: {numbers_found}/{expected_numbers}")
        
        # Check for duplication
        if tables_extracted > 0 and text_sections > 0:
            # If we have tables, check if any text sections contain table-like content
            text_content = result['pdf_processing_result'].get('text_content', {})
            pages = text_content.get('pages', [])
            
            table_content_in_text = False
            for page in pages:
                for section in page.get('sections', []):
                    content = section.get('content', '').lower()
                    # Check for table-like patterns in text sections
                    if any(pattern in content for pattern in ['$100', '$105', '$110', 'first cost', 'second cost']):
                        table_content_in_text = True
                        print(f"❌ Found table content in text section: {content[:100]}...")
                        success = False
                        break
                if table_content_in_text:
                    break
            
            if not table_content_in_text:
                print("✅ No table content found in text sections")
        
        return success
        
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {str(e)}")
        return False

def main():
    """Main test function"""
    print("Testing Table and Paragraph Detection Improvements")
    print("=" * 60)
    
    # Define test cases
    test_cases = [
        {
            'path': 'tests/test_pdfs/Test_PDF_Table_100_numbers.pdf',
            'expected_tables': 1,
            'expected_text_sections': 0,  # Should be 0 because table content is excluded
            'expected_numbers': 0,
            'description': 'PDF with table only - should extract table, no text sections'
        },
        {
            'path': 'tests/test_pdfs/Test_PDF_Table_9_numbers.pdf',
            'expected_tables': 1,
            'expected_text_sections': 0,  # Should be 0 because table content is excluded
            'expected_numbers': 0,
            'description': 'PDF with small table - should extract table, no text sections'
        },
        {
            'path': 'tests/test_pdfs/Test_PDF_with_3_numbers_in_large_paragraphs.pdf',
            'expected_tables': 0,
            'expected_text_sections': 3,
            'expected_numbers': 3,
            'description': 'PDF with paragraphs only - should extract text sections and numbers'
        }
    ]
    
    # Run tests
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}/{total}: {test_case['description']}")
        print("-" * 40)
        
        if test_pdf_processing(
            test_case['path'],
            test_case['expected_tables'],
            test_case['expected_text_sections'],
            test_case['expected_numbers']
        ):
            passed += 1
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Table and paragraph detection is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the results above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 