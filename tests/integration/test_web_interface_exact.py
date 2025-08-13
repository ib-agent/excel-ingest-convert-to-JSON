#!/usr/bin/env python3
"""
Test script to simulate the exact web interface behavior
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from converter.pdf.processing import PDFProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_web_interface_exact():
    """Test using the exact same file path as the web interface"""
    
    # Use the same file path as the web interface
    pdf_path = "/Users/jeffwinner/excel-ingest-convert-to-JSON/media/temp/synthetic_financial_report.pdf"
    
    logger.info(f"Testing web interface exact behavior for: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        return
    
    try:
        # Initialize PDF processor exactly like the web interface
        processor = PDFProcessor()
        
        # Process the PDF file with the same parameters as the web interface
        result = processor.process_file(
            pdf_path,
            extract_tables=True,
            extract_text=True,
            extract_numbers=True
        )
        
        # Save the result
        with open('web_interface_exact_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        # Log the summary
        tables = result.get('tables', {}).get('tables', [])
        text_sections = result.get('text_content', {}).get('sections', [])
        
        logger.info(f"\n=== WEB INTERFACE EXACT BEHAVIOR ===")
        logger.info(f"Tables found: {len(tables)}")
        logger.info(f"Text sections: {len(text_sections)}")
        
        # Check if our target table is found
        target_found = False
        for table in tables:
            table_name = table.get('name', '')
            if 'Selected Operating Metrics' in table_name:
                target_found = True
                logger.info(f"*** TARGET TABLE FOUND IN TABLES: {table_name} ***")
                break
        
        if not target_found:
            logger.info("*** TARGET TABLE NOT FOUND IN TABLES ***")
            
            # Check text sections
            for i, section in enumerate(text_sections):
                section_text = section.get('text', '')
                if 'Selected Operating Metrics' in section_text:
                    logger.info(f"*** TARGET TABLE FOUND IN TEXT SECTION {i+1} ***")
                    break
        
        logger.info(f"\nFull result saved to web_interface_exact_result.json")
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_interface_exact() 