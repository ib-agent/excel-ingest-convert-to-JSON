#!/usr/bin/env python3
"""
Test script to examine the content of the detected table
"""

import os
import sys
import logging
import json
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from converter.pdf.processing import PDFProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_table_content():
    """Test the content of the detected table"""
    
    pdf_path = "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/fixtures/pdfs/synthetic_financial_report.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    logger.info(f"Testing table content for: {pdf_path}")
    
    # Create processor
    processor = PDFProcessor()
    
    try:
        # Process the file
        result = processor.process_file(pdf_path, extract_tables=True, extract_text=False, extract_numbers=False)
        
        # Examine the result
        tables = result.get("pdf_processing_result", {}).get("tables", {})
        table_list = tables.get("tables", [])
        
        logger.info(f"Found {len(table_list)} tables")
        
        # Look for the specific table and examine its content
        for i, table in enumerate(table_list):
            rows = table.get('rows', [])
            
            # Check if this is the target table
            is_target_table = False
            for row in rows:
                cells = row.get('cells', {})
                cell_values = [str(cell.get('value', '')).strip() for cell in cells.values()]
                combined_text = ' '.join(cell_values)
                if 'Selected Operating Metrics' in combined_text:
                    is_target_table = True
                    break
            
            if is_target_table:
                logger.info(f"\n=== TARGET TABLE {i+1} CONTENT ===")
                logger.info(f"Table ID: {table.get('table_id')}")
                logger.info(f"Page: {table.get('region', {}).get('page_number')}")
                logger.info(f"Detection Method: {table.get('region', {}).get('detection_method')}")
                logger.info(f"Rows: {len(rows)}")
                logger.info(f"Columns: {len(table.get('columns', []))}")
                
                logger.info("\nTable Content:")
                for j, row in enumerate(rows):
                    cells = row.get('cells', {})
                    cell_values = [str(cell.get('value', '')).strip() for cell in cells.values()]
                    logger.info(f"  Row {j+1}: {cell_values}")
                
                # Save the table to a JSON file for inspection
                with open('target_table_output.json', 'w') as f:
                    json.dump(table, f, indent=2)
                logger.info("\nTable saved to target_table_output.json")
                break
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_table_content() 