#!/usr/bin/env python3
"""
Test script to simulate the web interface PDF processing
"""

import os
import sys
import logging
import json
from PDF_processing import PDFProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_web_interface_simulation():
    """Test the PDF processing as called by the web interface"""
    
    pdf_path = "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/test_pdfs/synthetic_financial_report.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    logger.info(f"Testing web interface simulation for: {pdf_path}")
    
    # Create processor
    processor = PDFProcessor()
    
    try:
        # Simulate web interface call with all options enabled
        result = processor.process_file(
            pdf_path, 
            extract_tables=True, 
            extract_text=True, 
            extract_numbers=True
        )
        
        # Examine the result
        tables = result.get("pdf_processing_result", {}).get("tables", {})
        table_list = tables.get("tables", [])
        text_content = result.get("pdf_processing_result", {}).get("text_content", {})
        
        logger.info(f"Tables found: {len(table_list)}")
        logger.info(f"Text pages: {len(text_content.get('pages', []))}")
        
        # Check for the target table in tables
        target_table_found_in_tables = False
        for i, table in enumerate(table_list):
            rows = table.get('rows', [])
            for row in rows:
                cells = row.get('cells', {})
                cell_values = [str(cell.get('value', '')).strip() for cell in cells.values()]
                combined_text = ' '.join(cell_values)
                if 'Selected Operating Metrics' in combined_text:
                    logger.info(f"*** FOUND TARGET TABLE IN TABLES: {combined_text} ***")
                    target_table_found_in_tables = True
                    break
            if target_table_found_in_tables:
                break
        
        # Check for the target table in text sections
        target_table_found_in_text = False
        for page in text_content.get('pages', []):
            for section in page.get('sections', []):
                section_text = section.get('text', '')
                if 'Selected Operating Metrics' in section_text:
                    logger.info(f"*** FOUND TARGET TABLE IN TEXT SECTIONS: {section_text[:100]}... ***")
                    logger.info(f"Section type: {section.get('section_type')}")
                    target_table_found_in_text = True
                    break
            if target_table_found_in_text:
                break
        
        if not target_table_found_in_tables and not target_table_found_in_text:
            logger.warning("Target table not found in either tables or text sections")
            
            # Let's examine what tables were actually detected
            logger.info("\n=== Examining detected tables ===")
            for i, table in enumerate(table_list):
                logger.info(f"Table {i+1}:")
                logger.info(f"  Page: {table.get('region', {}).get('page_number')}")
                logger.info(f"  Detection method: {table.get('region', {}).get('detection_method')}")
                logger.info(f"  Rows: {len(table.get('rows', []))}")
                
                # Show first few rows
                rows = table.get('rows', [])
                for j, row in enumerate(rows[:3]):
                    cells = row.get('cells', {})
                    cell_values = [str(cell.get('value', '')).strip() for cell in cells.values()]
                    logger.info(f"    Row {j+1}: {cell_values}")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_interface_simulation() 