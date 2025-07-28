#!/usr/bin/env python3
"""
Test script to examine the specific table detection in the full pipeline
"""

import os
import sys
import logging
import json
from PDF_processing import PDFProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_specific_table():
    """Test the specific table detection in the full pipeline"""
    
    pdf_path = "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/test_pdfs/synthetic_financial_report.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    logger.info(f"Testing specific table detection for: {pdf_path}")
    
    # Create processor
    processor = PDFProcessor()
    
    try:
        # Process the file
        result = processor.process_file(pdf_path, extract_tables=True, extract_text=False, extract_numbers=False)
        
        # Examine the result
        tables = result.get("pdf_processing_result", {}).get("tables", {})
        table_list = tables.get("tables", [])
        
        logger.info(f"Full processor result: {len(table_list)} tables found")
        
        # Look for the specific table
        target_table_found = False
        for i, table in enumerate(table_list):
            logger.info(f"\n=== Full Processor Table {i+1} ===")
            logger.info(f"Table ID: {table.get('table_id')}")
            logger.info(f"Page: {table.get('region', {}).get('page_number')}")
            logger.info(f"Rows: {len(table.get('rows', []))}")
            logger.info(f"Columns: {len(table.get('columns', []))}")
            
            # Check if this is the target table
            rows = table.get('rows', [])
            for row in rows:
                cells = row.get('cells', {})
                cell_values = [str(cell.get('value', '')).strip() for cell in cells.values()]
                combined_text = ' '.join(cell_values)
                if 'Selected Operating Metrics' in combined_text:
                    logger.info(f"*** FOUND TARGET TABLE IN FULL PROCESSOR: {combined_text} ***")
                    target_table_found = True
                    break
            
            if target_table_found:
                break
        
        if not target_table_found:
            logger.warning("Target table not found in full processor result")
            
            # Let's also check the raw table extraction result
            logger.info("\n=== Checking raw table extraction ===")
            table_extractor = processor.table_extractor
            raw_result = table_extractor.extract_tables(pdf_path)
            
            logger.info(f"Raw extraction found {len(raw_result.get('tables', []))} tables")
            
            for i, table in enumerate(raw_result.get('tables', [])):
                logger.info(f"\nRaw Table {i+1}:")
                logger.info(f"  Rows: {len(table.get('rows', []))}")
                
                # Check for target table
                rows = table.get('rows', [])
                for row in rows:
                    cells = row.get('cells', {})
                    cell_values = [str(cell.get('value', '')).strip() for cell in cells.values()]
                    combined_text = ' '.join(cell_values)
                    if 'Selected Operating Metrics' in combined_text:
                        logger.info(f"*** FOUND TARGET TABLE IN RAW EXTRACTION: {combined_text} ***")
                        break
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_specific_table() 