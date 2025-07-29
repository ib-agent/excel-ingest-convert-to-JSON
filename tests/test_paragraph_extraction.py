#!/usr/bin/env python3
"""
Test script to verify paragraph extraction for Test_PDF_with_3_numbers_in_large_paragraphs.pdf
"""

import json
import sys

def analyze_paragraph_results(json_file):
    """Analyze the paragraph extraction results"""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Get text content data
    text_content = data.get('pdf_processing_result', {}).get('text_content', {}).get('text_content', {})
    
    print(f"Paragraph Analysis for: {data['pdf_processing_result']['document_metadata']['filename']}")
    print("=" * 70)
    
    # Basic info
    print(f"Total Pages: {text_content.get('document_metadata', {}).get('total_pages', 0)}")
    print(f"Total Word Count: {text_content.get('document_metadata', {}).get('total_word_count', 0)}")
    
    # Analyze sections/paragraphs
    pages = text_content.get('pages', [])
    if pages:
        sections = pages[0].get('sections', [])
        print(f"\nParagraphs Found: {len(sections)}")
        
        for i, section in enumerate(sections, 1):
            print(f"\n--- Paragraph {i} ---")
            print(f"Section ID: {section.get('section_id', 'N/A')}")
            print(f"Type: {section.get('section_type', 'N/A')}")
            print(f"Word Count: {section.get('word_count', 0)}")
            print(f"Character Count: {section.get('character_count', 0)}")
            print(f"LLM Ready: {section.get('llm_ready', False)}")
            print(f"Content: {section.get('content', 'No content')[:100]}...")
            
            # Check for numbers in this paragraph
            numbers = section.get('numbers', [])
            if numbers:
                print(f"Numbers in this paragraph: {len(numbers)}")
                for j, number in enumerate(numbers, 1):
                    print(f"  Number {j}: {number.get('original_text', 'N/A')} ({number.get('format', 'N/A')})")
            else:
                print("Numbers in this paragraph: 0")
    
    # Analyze numbers summary
    numbers_summary = data.get('pdf_processing_result', {}).get('numbers_in_text', {}).get('numbers_in_text', {}).get('summary', {})
    if numbers_summary:
        print(f"\nNumbers Summary:")
        print(f"  Total Numbers Found: {numbers_summary.get('total_numbers_found', 0)}")
        print(f"  Numbers by Format: {numbers_summary.get('numbers_by_format', {})}")
        print(f"  Confidence Distribution: {numbers_summary.get('confidence_distribution', {})}")
    
    # Verify expected results
    print(f"\nVerification:")
    expected_paragraphs = 3
    expected_numbers = 3  # 10, $50, 10,000
    
    actual_paragraphs = len(sections) if sections else 0
    actual_numbers = numbers_summary.get('total_numbers_found', 0) if numbers_summary else 0
    
    print(f"  Expected paragraphs: {expected_paragraphs}, Found: {actual_paragraphs} {'✓' if actual_paragraphs == expected_paragraphs else '✗'}")
    print(f"  Expected numbers: {expected_numbers}, Found: {actual_numbers} {'✓' if actual_numbers >= expected_numbers else '✗'}")
    
    # Check if each paragraph contains a number
    paragraphs_with_numbers = 0
    for section in sections:
        if section.get('numbers'):
            paragraphs_with_numbers += 1
    
    print(f"  Paragraphs with numbers: {paragraphs_with_numbers}/3 {'✓' if paragraphs_with_numbers == 3 else '✗'}")

if __name__ == "__main__":
    json_file = "Test_PDF_with_3_numbers_in_large_paragraphs_tables.json"
    analyze_paragraph_results(json_file) 