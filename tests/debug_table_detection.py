#!/usr/bin/env python3
"""
Debug script to examine table detection issues in the synthetic financial report PDF
"""

import os
import sys
import logging
from converter.pdfplumber_processor import PDFPlumberProcessor
import pandas as pd
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_table_detection(pdf_path: str):
    """Debug table detection for the specific PDF file"""
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    logger.info(f"Debugging table detection for: {pdf_path}")
    
    processor = PDFPlumberProcessor()
    result = processor.extract_tables_only(pdf_path)
    tables = result.get("tables", [])
    logger.info(f"Found {len(tables)} tables with pdfplumber")
    for i, table in enumerate(tables):
        logger.info(f"\nTable {i+1}:")
        region = table.get("region", {})
        metadata = table.get("metadata", {})
        logger.info(f"  Page: {region.get('page_number')}")
        logger.info(f"  Cell count: {metadata.get('cell_count')}")
        logger.info(f"  Detection method: {metadata.get('detection_method')}")

if __name__ == "__main__":
    pdf_path = "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/fixtures/pdfs/synthetic_financial_report.pdf"
    debug_table_detection(pdf_path) 