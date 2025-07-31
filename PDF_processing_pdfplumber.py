"""
PDF Processing Module using PDFPlumber

This module provides comprehensive PDF processing capabilities using PDFPlumber:
- Table extraction using PDFPlumber (improved accuracy)
- Text extraction using PDFPlumber (layout preservation)
- Number extraction from text content (enhanced patterns)

Maintains API compatibility with the original PDF_processing.py module.

Author: PDF Processing Team  
Date: 2024
"""

import os
import json
import logging
import tempfile
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Import our PDFPlumber implementation
from converter.pdfplumber_processor import PDFPlumberProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFTableExtractor:
    """
    Table extraction using PDFPlumber - maintains API compatibility
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize table extractor with PDFPlumber
        
        Args:
            config: Configuration dictionary for table extraction
        """
        self.config = config or self._get_default_config()
        self.processor = PDFPlumberProcessor(config)
        
        logger.info("PDFTableExtractor initialized with PDFPlumber")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for table extraction"""
        return {
            'table_extraction': {
                'table_settings': {
                    'vertical_strategy': "lines",
                    'horizontal_strategy': "lines",
                    'min_words_vertical': 3,
                    'min_words_horizontal': 1,
                    'snap_tolerance': 3,
                    'snap_x_tolerance': 3,
                    'snap_y_tolerance': 3,
                    'join_tolerance': 3,
                    'edge_min_length': 3,
                    'intersection_tolerance': 3,
                    'intersection_x_tolerance': 3,
                    'intersection_y_tolerance': 3
                },
                'quality_threshold': 0.8,
                'min_table_size': 2,
                'max_tables_per_page': 10,
                'min_rows': 2,
                'min_cols': 2
            }
        }
    
    def extract_tables(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract tables from PDF file using PDFPlumber
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted tables in the expected format
        """
        logger.info(f"Starting table extraction from: {pdf_path}")
        
        try:
            # Use PDFPlumber processor to extract tables
            tables_data = self.processor.extract_tables_only(pdf_path)
            
            # Transform to expected format for API compatibility
            result = {
                "extraction_metadata": {
                    "method": "pdfplumber",
                    "total_tables": len(tables_data.get("tables", [])),
                    "extraction_timestamp": datetime.now().isoformat(),
                    "file_path": pdf_path
                },
                "tables": self._transform_tables_for_compatibility(tables_data.get("tables", [])),
                "quality_metrics": {
                    "overall_confidence": self._calculate_overall_confidence(tables_data.get("tables", [])),
                    "extraction_success": True
                }
            }
            
            logger.info(f"Table extraction completed: {result['extraction_metadata']['total_tables']} tables found")
            return result
            
        except Exception as e:
            logger.error(f"Error during table extraction: {str(e)}")
            return {
                "extraction_metadata": {
                    "method": "pdfplumber",
                    "total_tables": 0,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "file_path": pdf_path,
                    "error": str(e)
                },
                "tables": [],
                "quality_metrics": {
                    "overall_confidence": 0.0,
                    "extraction_success": False
                }
            }
    
    def _transform_tables_for_compatibility(self, pdfplumber_tables: List[Dict]) -> List[Dict]:
        """
        Transform PDFPlumber tables to format expected by existing code
        
        Args:
            pdfplumber_tables: List of tables from PDFPlumber
            
        Returns:
            List of tables in expected format
        """
        transformed_tables = []
        
        for table in pdfplumber_tables:
            try:
                # Extract table data for compatibility
                rows_data = table["rows"]
                columns_data = table["columns"]
                
                # Create data matrix
                data_matrix = []
                column_labels = [col["column_label"] for col in columns_data]
                
                for row in rows_data:
                    row_data = []
                    for col_idx in range(len(column_labels)):
                        cell_value = ""
                        for cell_key, cell_data in row["cells"].items():
                            if cell_data["column"] == col_idx + 1:
                                cell_value = cell_data["value"]
                                break
                        row_data.append(cell_value)
                    data_matrix.append(row_data)
                
                # Create transformed table using new UI-compatible format
                transformed_table = self._transform_table_to_ui_format(table)
                
                transformed_tables.append(transformed_table)
                
            except Exception as e:
                logger.warning(f"Error transforming table {table.get('table_id', 'unknown')}: {e}")
                continue
        
        return transformed_tables
    
    def _create_records_format(self, data_matrix: List[List[str]], headers: List[str]) -> List[Dict]:
        """Create records format from data matrix"""
        records = []
        for row in data_matrix:
            record = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    record[header] = row[i]
                else:
                    record[header] = ""
            records.append(record)
        return records

    def _transform_table_to_ui_format(self, table: Dict) -> Dict:
        """
        Transform table data to format expected by UI JavaScript
        
        Args:
            table: Table data from PDFPlumber processor
            
        Returns:
            Table data in UI-compatible format
        """
        # Convert PDFPlumber table format to UI format
        rows_data = table.get("rows", [])
        columns_data = table.get("columns", [])
        
        if not rows_data or not columns_data:
            # Fallback: no valid table structure
            return {
                "table_id": table.get("table_id", "unknown"),
                "region": table.get("region", {}),
                "rows": [],
                "columns": [],
                "metadata": table.get("metadata", {})
            }
        
        # Create UI-compatible rows with cells structure
        ui_rows = []
        
        for row_idx, row in enumerate(rows_data):
            # Create cells dictionary for this row
            cells = {}
            row_cells = row.get("cells", {})
            
            for cell_key, cell_data in row_cells.items():
                cells[cell_key] = {
                    "value": cell_data.get("value", ""),
                    "column": cell_data.get("column", 1),
                    "row": cell_data.get("row", row_idx + 1)
                }
            
            ui_row = {
                "row_index": row_idx,
                "row_label": row.get("row_label", f"Row {row_idx + 1}"),
                "is_header_row": row.get("is_header_row", False),
                "cells": cells
            }
            
            ui_rows.append(ui_row)
        
        # Create UI-compatible columns
        ui_columns = []
        for col in columns_data:
            ui_columns.append({
                "column_index": col.get("column_index", 0),
                "column_label": col.get("column_label", ""),
                "data_type": col.get("data_type", "text")
            })
        
        return {
            "table_id": table.get("table_id", "unknown"),
            "region": table.get("region", {}),
            "rows": ui_rows,
            "columns": ui_columns,
            "metadata": table.get("metadata", {}),
            "name": table.get("name", f"Table {table.get('table_id', 'unknown')}")
        }
    
    def _calculate_overall_confidence(self, tables: List[Dict]) -> float:
        """Calculate overall confidence score"""
        if not tables:
            return 0.0
        
        confidences = [table["metadata"]["confidence"] for table in tables]
        return sum(confidences) / len(confidences)

class PDFTextProcessor:
    """
    Text processing using PDFPlumber - maintains API compatibility
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize text processor with PDFPlumber
        
        Args:
            config: Configuration dictionary for text processing
        """
        self.config = config or self._get_default_config()
        self.processor = PDFPlumberProcessor(config)
        
        logger.info("PDFTextProcessor initialized with PDFPlumber")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for text processing"""
        return {
            'text_extraction': {
                'text_settings': {
                    'x_tolerance': 3,
                    'y_tolerance': 3
                },
                'section_detection': {
                    'min_section_size': 50,
                    'max_section_size': 1000,
                    'use_headers': True,
                    'detect_lists': True,
                    'min_words_per_section': 10,
                    'max_words_per_section': 500
                },
                'extract_metadata': True,
                'preserve_formatting': True
            }
        }
    
    def extract_text(self, pdf_path: str, exclude_table_regions: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Extract text content from PDF using PDFPlumber
        
        Args:
            pdf_path: Path to the PDF file
            exclude_table_regions: Optional table regions to exclude
            
        Returns:
            Dictionary containing extracted text in expected format
        """
        logger.info(f"Starting text extraction from: {pdf_path}")
        
        try:
            # Use PDFPlumber processor to extract text
            text_data = self.processor.extract_text_only(pdf_path, exclude_table_regions)
            
            # Transform to expected format for API compatibility
            result = {
                "extraction_metadata": {
                    "method": "pdfplumber",
                    "total_sections": text_data["text_content"]["summary"]["total_sections"],
                    "total_words": text_data["text_content"]["summary"]["total_words"],
                    "extraction_timestamp": datetime.now().isoformat(),
                    "file_path": pdf_path
                },
                "text_content": self._transform_text_for_compatibility(text_data["text_content"]),
                "quality_metrics": {
                    "llm_ready_sections": text_data["text_content"]["summary"]["llm_ready_sections"],
                    "extraction_success": True
                }
            }
            
            logger.info(f"Text extraction completed: {result['extraction_metadata']['total_sections']} sections found")
            return result
            
        except Exception as e:
            logger.error(f"Error during text extraction: {str(e)}")
            return {
                "extraction_metadata": {
                    "method": "pdfplumber",
                    "total_sections": 0,
                    "total_words": 0,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "file_path": pdf_path,
                    "error": str(e)
                },
                "text_content": {"pages": [], "summary": {}},
                "quality_metrics": {
                    "llm_ready_sections": 0,
                    "extraction_success": False
                }
            }
    
    def _transform_text_for_compatibility(self, text_content: Dict) -> Dict:
        """
        Transform PDFPlumber text content to expected format
        
        Args:
            text_content: Text content from PDFPlumber
            
        Returns:
            Text content in expected format
        """
        # The PDFPlumber text format is already quite compatible
        # Just ensure we have the expected structure
        return {
            "document_metadata": text_content.get("document_metadata", {}),
            "pages": text_content.get("pages", []),
            "document_structure": text_content.get("document_structure", {}),
            "summary": text_content.get("summary", {})
        }

class PDFNumberExtractor:
    """
    Number extraction from text - enhanced for PDFPlumber
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize number extractor
        
        Args:
            config: Configuration dictionary for number extraction
        """
        self.config = config or self._get_default_config()
        self.processor = PDFPlumberProcessor(config)
        
        logger.info("PDFNumberExtractor initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for number extraction"""
        return {
            'number_extraction': {
                'patterns': {
                    'integer': r'\b\d{1,3}(?:,\d{3})*\b',
                    'decimal': r'\b\d+\.\d+\b',
                    'percentage': r'\b\d+(?:\.\d+)?%\b',
                    'currency': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?\b',
                    'scientific_notation': r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b',
                    'fraction': r'\b\d+/\d+\b',
                    'date_number': r'\b(?:19|20)\d{2}\b|\b\d{1,2}(?:st|nd|rd|th)\b'
                },
                'context_window': 100,
                'confidence_threshold': 0.7,
                'extract_metadata': True,
                'include_positioning': True
            }
        }
    
    def extract_numbers(self, text_content: Dict) -> Dict[str, Any]:
        """
        Extract numbers from text content
        
        Args:
            text_content: Text content dictionary
            
        Returns:
            Dictionary containing extracted numbers
        """
        logger.info("Starting number extraction from text content")
        
        try:
            extracted_numbers = []
            
            # Process each page and section
            for page in text_content.get("pages", []):
                for section in page.get("sections", []):
                    # Extract numbers from this section
                    section_numbers = self.processor.extract_numbers_only(
                        section["content"],
                        section["position"],
                        section["metadata"]
                    )
                    
                    # Transform to expected format
                    for number in section_numbers:
                        transformed_number = {
                            "value": number["value"],
                            "original_text": number["original_text"],
                            "number_type": number["format"],
                            "context": number["context"],
                            "position": number["position"],
                            "confidence": number["confidence"],
                            "page_number": page["page_number"],
                            "section_id": section["section_id"],
                            "metadata": {
                                "extraction_method": "pdfplumber_enhanced",
                                "unit": number.get("unit"),
                                "currency": number.get("currency")
                            }
                        }
                        extracted_numbers.append(transformed_number)
            
            result = {
                "extraction_metadata": {
                    "method": "pdfplumber_enhanced",
                    "total_numbers": len(extracted_numbers),
                    "extraction_timestamp": datetime.now().isoformat()
                },
                "numbers": extracted_numbers,
                "summary": {
                    "by_type": self._summarize_by_type(extracted_numbers),
                    "by_page": self._summarize_by_page(extracted_numbers),
                    "confidence_distribution": self._calculate_confidence_distribution(extracted_numbers)
                }
            }
            
            logger.info(f"Number extraction completed: {len(extracted_numbers)} numbers found")
            return result
            
        except Exception as e:
            logger.error(f"Error during number extraction: {str(e)}")
            return {
                "extraction_metadata": {
                    "method": "pdfplumber_enhanced",
                    "total_numbers": 0,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "error": str(e)
                },
                "numbers": [],
                "summary": {}
            }
    
    def _summarize_by_type(self, numbers: List[Dict]) -> Dict[str, int]:
        """Summarize numbers by type"""
        type_counts = {}
        for number in numbers:
            number_type = number["number_type"]
            type_counts[number_type] = type_counts.get(number_type, 0) + 1
        return type_counts
    
    def _summarize_by_page(self, numbers: List[Dict]) -> Dict[int, int]:
        """Summarize numbers by page"""
        page_counts = {}
        for number in numbers:
            page_num = number["page_number"]
            page_counts[page_num] = page_counts.get(page_num, 0) + 1
        return page_counts
    
    def _calculate_confidence_distribution(self, numbers: List[Dict]) -> Dict[str, int]:
        """Calculate confidence distribution"""
        distribution = {"high": 0, "medium": 0, "low": 0}
        for number in numbers:
            confidence = number["confidence"]
            if confidence >= 0.8:
                distribution["high"] += 1
            elif confidence >= 0.6:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        return distribution

class PDFProcessor:
    """
    Main PDF processing class using PDFPlumber - maintains API compatibility
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the PDF processor with PDFPlumber
        
        Args:
            config: Configuration dictionary for PDF processing
        """
        self.config = config or self._get_default_config()
        
        # Initialize component processors with PDFPlumber
        self.table_extractor = PDFTableExtractor(
            self.config.get('table_extraction', {})
        )
        self.text_processor = PDFTextProcessor(
            self.config.get('text_extraction', {})
        )
        self.number_extractor = PDFNumberExtractor(
            self.config.get('number_extraction', {})
        )
        
        logger.info("PDFProcessor initialized with PDFPlumber backend")
    
    def process_file(self, pdf_path: str, extract_tables: bool = True, 
                    extract_text: bool = True, extract_numbers: bool = True) -> Dict[str, Any]:
        """
        Process PDF file - API compatibility method for Django views
        
        Args:
            pdf_path: Path to the PDF file
            extract_tables: Whether to extract tables (default: True)
            extract_text: Whether to extract text (default: True)  
            extract_numbers: Whether to extract numbers (default: True)
            
        Returns:
            Dictionary containing extraction results in expected format
        """
        logger.info(f"Processing PDF file: {pdf_path} (tables={extract_tables}, text={extract_text}, numbers={extract_numbers})")
        
        # Call the main processing method
        result = self.process_pdf(pdf_path)
        
        # Wrap result in expected Django format
        return {
            "pdf_processing_result": result
        }
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for PDF processing"""
        return {
            'table_extraction': {
                'table_settings': {
                    'vertical_strategy': "lines",
                    'horizontal_strategy': "lines",
                    'min_words_vertical': 3,
                    'min_words_horizontal': 1,
                    'snap_tolerance': 3,
                    'snap_x_tolerance': 3,
                    'snap_y_tolerance': 3,
                    'join_tolerance': 3,
                    'edge_min_length': 3,
                    'intersection_tolerance': 3,
                    'intersection_x_tolerance': 3,
                    'intersection_y_tolerance': 3
                },
                'quality_threshold': 0.90,  # Increased for better filtering
                'min_table_size': 2,
                'max_tables_per_page': 10,
                'min_rows': 2,
                'min_cols': 2,
                'max_cols': 15,  # Reject tables with >15 columns
                'min_cell_content_ratio': 0.4,  # At least 40% meaningful content
                'enable_spanning_detection': True  # Enable cross-page table merging
            },
            'text_extraction': {
                'text_settings': {
                    'x_tolerance': 3,
                    'y_tolerance': 3
                },
                'section_detection': {
                    'min_section_size': 50,
                    'max_section_size': 1000,
                    'use_headers': True,
                    'detect_lists': True,
                    'min_words_per_section': 10,
                    'max_words_per_section': 500
                },
                'extract_metadata': True,
                'preserve_formatting': True
            },
            'number_extraction': {
                'patterns': {
                    'integer': r'\b\d{1,3}(?:,\d{3})*\b',
                    'decimal': r'\b\d+\.\d+\b',
                    'percentage': r'\b\d+(?:\.\d+)?%\b',
                    'currency': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?\b',
                    'scientific_notation': r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b',
                    'fraction': r'\b\d+/\d+\b',
                    'date_number': r'\b(?:19|20)\d{2}\b|\b\d{1,2}(?:st|nd|rd|th)\b'
                },
                'context_window': 100,
                'confidence_threshold': 0.7,
                'extract_metadata': True,
                'include_positioning': True
            },
            'processing_options': {
                'extract_tables': True,
                'extract_text': True,
                'extract_numbers': True,
                'exclude_table_regions_from_text': True
            }
        }
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF file with comprehensive extraction using PDFPlumber
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing all extraction results
        """
        logger.info(f"Starting comprehensive PDF processing: {pdf_path}")
        
        processing_start = datetime.now()
        
        # Initialize result structure
        result = {
            "document_metadata": {
                "file_path": pdf_path,
                "processing_timestamp": processing_start.isoformat(),
                "processing_duration": 0,
                "extraction_method": "pdfplumber_comprehensive"
            },
            "tables": {},
            "text_content": {},
            "numbers": {},
            "processing_summary": {
                "tables_extracted": 0,
                "text_sections_extracted": 0,
                "numbers_extracted": 0,
                "overall_success": True,
                "errors": []
            }
        }
        
        try:
            # Phase 1: Extract tables
            if self.config.get('processing_options', {}).get('extract_tables', True):
                logger.info("Phase 1: Extracting tables")
                try:
                    tables_result = self.table_extractor.extract_tables(pdf_path)
                    result["tables"] = tables_result
                    result["processing_summary"]["tables_extracted"] = \
                        tables_result["extraction_metadata"]["total_tables"]
                except Exception as e:
                    error_msg = f"Table extraction failed: {str(e)}"
                    logger.error(error_msg)
                    result["processing_summary"]["errors"].append(error_msg)
            
            # Phase 2: Extract text content
            if self.config.get('processing_options', {}).get('extract_text', True):
                logger.info("Phase 2: Extracting text content")
                try:
                    # Get table regions for exclusion if configured
                    exclude_regions = None
                    if (self.config.get('processing_options', {}).get('exclude_table_regions_from_text', True)
                        and result.get("tables", {}).get("tables")):
                        exclude_regions = result["tables"]["tables"]
                    
                    text_result = self.text_processor.extract_text(pdf_path, exclude_regions)
                    result["text_content"] = text_result
                    result["processing_summary"]["text_sections_extracted"] = \
                        text_result["extraction_metadata"]["total_sections"]
                except Exception as e:
                    error_msg = f"Text extraction failed: {str(e)}"
                    logger.error(error_msg)
                    result["processing_summary"]["errors"].append(error_msg)
            
            # Phase 3: Extract numbers from text
            if (self.config.get('processing_options', {}).get('extract_numbers', True)
                and result.get("text_content", {}).get("text_content")):
                logger.info("Phase 3: Extracting numbers")
                try:
                    numbers_result = self.number_extractor.extract_numbers(
                        result["text_content"]["text_content"]
                    )
                    result["numbers"] = numbers_result
                    result["processing_summary"]["numbers_extracted"] = \
                        numbers_result["extraction_metadata"]["total_numbers"]
                except Exception as e:
                    error_msg = f"Number extraction failed: {str(e)}"
                    logger.error(error_msg)
                    result["processing_summary"]["errors"].append(error_msg)
            
            # Calculate processing duration
            processing_end = datetime.now()
            duration = (processing_end - processing_start).total_seconds()
            result["document_metadata"]["processing_duration"] = duration
            
            # Update success status
            result["processing_summary"]["overall_success"] = len(result["processing_summary"]["errors"]) == 0
            
            logger.info(f"PDF processing completed in {duration:.2f} seconds")
            logger.info(f"Summary: {result['processing_summary']['tables_extracted']} tables, "
                       f"{result['processing_summary']['text_sections_extracted']} text sections, "
                       f"{result['processing_summary']['numbers_extracted']} numbers")
            
            return result
            
        except Exception as e:
            error_msg = f"Critical error during PDF processing: {str(e)}"
            logger.error(error_msg)
            result["processing_summary"]["errors"].append(error_msg)
            result["processing_summary"]["overall_success"] = False
            raise

def main():
    """Main function for testing PDFPlumber-based processing"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python PDF_processing_pdfplumber.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found")
        sys.exit(1)
    
    # Initialize processor with PDFPlumber
    processor = PDFProcessor()
    
    try:
        # Process the PDF
        result = processor.process_pdf(pdf_path)
        
        # Save results
        output_file = f"{os.path.splitext(pdf_path)[0]}_pdfplumber_results.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"Processing completed successfully!")
        print(f"Results saved to: {output_file}")
        print(f"Summary:")
        print(f"  - Tables extracted: {result['processing_summary']['tables_extracted']}")
        print(f"  - Text sections: {result['processing_summary']['text_sections_extracted']}")
        print(f"  - Numbers found: {result['processing_summary']['numbers_extracted']}")
        print(f"  - Processing time: {result['document_metadata']['processing_duration']:.2f} seconds")
        print(f"  - Overall success: {result['processing_summary']['overall_success']}")
        
        if result['processing_summary']['errors']:
            print(f"  - Errors: {len(result['processing_summary']['errors'])}")
            for error in result['processing_summary']['errors']:
                print(f"    * {error}")
    
    except Exception as e:
        print(f"Error processing PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 