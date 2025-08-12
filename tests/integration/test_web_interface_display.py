#!/usr/bin/env python3
"""
Test script to verify web interface display format
"""

import os
import sys
import logging
import json
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PDF_processing import PDFProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_web_interface_display(tmp_path):
    """Test the web interface display format"""
    
    pdf_path = "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/fixtures/pdfs/synthetic_financial_report.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    logger.info(f"Testing web interface display format for: {pdf_path}")
    
    # Create processor
    processor = PDFProcessor()
    
    try:
        # Simulate web interface call
        result = processor.process_file(
            pdf_path, 
            extract_tables=True, 
            extract_text=True, 
            extract_numbers=True
        )
        
        # Simulate the web interface response format
        web_response = {
            'success': True,
            'result': result,
            'filename': 'synthetic_financial_report.pdf'
        }
        
        # Check tables display
        tables = result.get("pdf_processing_result", {}).get("tables", {})
        table_list = tables.get("tables", [])
        
        logger.info(f"\n=== TABLES DISPLAY ===")
        logger.info(f"Total tables found: {len(table_list)}")
        
        for i, table in enumerate(table_list):
            logger.info(f"\nTable {i+1}:")
            logger.info(f"  Page: {table.get('region', {}).get('page_number')}")
            logger.info(f"  Detection method: {table.get('region', {}).get('detection_method')}")
            logger.info(f"  Quality score: {table.get('metadata', {}).get('quality_score', 0):.1%}")
            logger.info(f"  Rows: {len(table.get('rows', []))}")
            logger.info(f"  Columns: {len(table.get('columns', []))}")
            
            # Check if this is the target table
            rows = table.get('rows', [])
            for row in rows:
                cells = row.get('cells', {})
                cell_values = [str(cell.get('value', '')).strip() for cell in cells.values()]
                combined_text = ' '.join(cell_values)
                if 'Selected Operating Metrics' in combined_text:
                    logger.info(f"  *** TARGET TABLE FOUND ***")
                    logger.info(f"  Content: {combined_text}")
                    break
        
        # Check text display
        text_content = result.get("pdf_processing_result", {}).get("text_content", {})
        pages = text_content.get("text_content", {}).get("pages", [])
        
        logger.info(f"\n=== TEXT DISPLAY ===")
        logger.info(f"Total pages: {len(pages)}")
        
        for page_num, page in enumerate(pages):
            sections = page.get("sections", [])
            logger.info(f"Page {page_num + 1}: {len(sections)} sections")
            
            if len(sections) == 0:
                logger.info(f"  No text sections (correct - all content is in tables)")
            else:
                for section in sections:
                    section_text = section.get("text", "")
                    if "Selected Operating Metrics" in section_text:
                        logger.warning(f"  *** TARGET TABLE FOUND IN TEXT SECTIONS (INCORRECT) ***")
                        logger.warning(f"  Section type: {section.get('section_type')}")
                        logger.warning(f"  Content: {section_text[:100]}...")
        
        # Save the full result for inspection in a temp file
        output_file = tmp_path / 'web_interface_result.json'
        with open(output_file, 'w') as f:
            json.dump(web_response, f, indent=2)
        logger.info(f"\nFull result saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_interface_display() 