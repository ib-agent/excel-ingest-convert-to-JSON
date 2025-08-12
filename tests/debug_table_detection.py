#!/usr/bin/env python3
"""
Debug script to examine table detection issues in the synthetic financial report PDF
"""

import os
import sys
import logging
import camelot
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
    
    # Try different extraction methods
    methods = ['lattice', 'stream']
    
    for method in methods:
        logger.info(f"\n=== Testing {method} method ===")
        
        try:
            if method == 'lattice':
                tables = camelot.read_pdf(
                    pdf_path, 
                    pages='1',  # Focus on page 1
                    flavor='lattice',
                    edge_tolerance=3,
                    row_tolerance=3,
                    column_tolerance=3
                )
            else:  # stream
                tables = camelot.read_pdf(
                    pdf_path, 
                    pages='1',  # Focus on page 1
                    flavor='stream',
                    edge_tolerance=3,
                    row_tolerance=3,
                    column_tolerance=3,
                    strip_text='\n'
                )
            
            logger.info(f"Found {len(tables)} tables with {method} method")
            
            for i, table in enumerate(tables):
                logger.info(f"\nTable {i+1}:")
                logger.info(f"  Shape: {table.df.shape}")
                logger.info(f"  Accuracy: {table.accuracy}")
                logger.info(f"  Page: {table.page}")
                
                if hasattr(table, '_bbox') and table._bbox is not None:
                    bbox = table._bbox
                    logger.info(f"  BBox: {bbox}")
                    
                    # Calculate coverage
                    page_width = 612.0
                    page_height = 792.0
                    table_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    page_area = page_width * page_height
                    coverage_ratio = table_area / page_area
                    logger.info(f"  Coverage: {coverage_ratio:.1%}")
                
                # Show table content
                logger.info(f"  Content:")
                print(table.df.to_string())
                logger.info("  " + "="*50)
                
        except Exception as e:
            logger.error(f"Error with {method} method: {str(e)}")
    
    # Also try with different parameters
    logger.info(f"\n=== Testing with different parameters ===")
    
    try:
        # Try with more lenient parameters
        tables = camelot.read_pdf(
            pdf_path, 
            pages='1',
            flavor='stream',
            edge_tolerance=5,  # More lenient
            row_tolerance=5,
            column_tolerance=5,
            strip_text='\n'
        )
        
        logger.info(f"Found {len(tables)} tables with lenient parameters")
        
        for i, table in enumerate(tables):
            logger.info(f"\nTable {i+1} (lenient):")
            logger.info(f"  Shape: {table.df.shape}")
            logger.info(f"  Accuracy: {table.accuracy}")
            print(table.df.to_string())
            
    except Exception as e:
        logger.error(f"Error with lenient parameters: {str(e)}")

if __name__ == "__main__":
    pdf_path = "/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/fixtures/pdfs/synthetic_financial_report.pdf"
    debug_table_detection(pdf_path) 