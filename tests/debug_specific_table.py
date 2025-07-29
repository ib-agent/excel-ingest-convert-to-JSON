#!/usr/bin/env python3
"""
Debug script to examine the specific table on page 1 of the synthetic financial report
"""

import os
import sys
import logging
import json
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PDF_processing import PDFTableExtractor, PDFProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_specific_table():
    """Debug the specific table detection issue"""
    
    pdf_path = "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/test_pdfs/synthetic_financial_report.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    logger.info(f"Debugging specific table detection for: {pdf_path}")
    
    # Create table extractor with more lenient settings
    config = {
        'methods': ['stream'],  # Focus on stream method
        'quality_threshold': 0.5,  # Lower threshold
        'edge_tolerance': 5,
        'row_tolerance': 5,
        'column_tolerance': 5,
        'min_table_size': 2,  # Allow smaller tables
        'max_tables_per_page': 10
    }
    
    extractor = PDFTableExtractor(config)
    
    try:
        # Extract tables
        result = extractor.extract_tables(pdf_path)
        
        logger.info(f"Extraction result: {len(result.get('tables', []))} tables found")
        
        # Examine each table
        for i, table in enumerate(result.get('tables', [])):
            logger.info(f"\n=== Table {i+1} ===")
            logger.info(f"Table ID: {table.get('table_id')}")
            logger.info(f"Page: {table.get('page_number')}")
            logger.info(f"Columns: {len(table.get('columns', []))}")
            logger.info(f"Rows: {len(table.get('rows', []))}")
            
            # Show first few rows
            rows = table.get('rows', [])
            logger.info("First 5 rows:")
            for j, row in enumerate(rows[:5]):
                cells = row.get('cells', {})
                cell_values = [cell.get('value', '') for cell in cells.values()]
                logger.info(f"  Row {j+1}: {cell_values}")
            
            # Check if this is the table we're looking for
            if table.get('page_number') == 1:
                logger.info("*** This is a table on page 1 ***")
                
                # Look for the specific title
                for row in rows:
                    cells = row.get('cells', {})
                    cell_values = [str(cell.get('value', '')).strip() for cell in cells.values()]
                    combined_text = ' '.join(cell_values)
                    if 'Selected Operating Metrics' in combined_text or 'Unaudited' in combined_text:
                        logger.info(f"*** FOUND TARGET TABLE: {combined_text} ***")
                        break
        
        # Also try with the full PDF processor to see the complete pipeline
        logger.info(f"\n=== Testing with full PDF processor ===")
        processor = PDFProcessor()
        full_result = processor.process_file(pdf_path, extract_tables=True, extract_text=False, extract_numbers=False)
        
        logger.info(f"Full processor found {len(full_result.get('tables', []))} tables")
        
        for i, table in enumerate(full_result.get('tables', [])):
            logger.info(f"\nFull Table {i+1}:")
            logger.info(f"  Page: {table.get('page_number')}")
            logger.info(f"  Rows: {len(table.get('rows', []))}")
            logger.info(f"  Columns: {len(table.get('columns', []))}")
            
            # Show first few rows
            rows = table.get('rows', [])
            logger.info("  First 3 rows:")
            for j, row in enumerate(rows[:3]):
                cells = row.get('cells', {})
                cell_values = [str(cell.get('value', '')).strip() for cell in cells.values()]
                logger.info(f"    Row {j+1}: {cell_values}")
        
    except Exception as e:
        logger.error(f"Error during table extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_specific_table() 