"""
PDFPlumber Processor

Main orchestrator for PDF processing using PDFPlumber library.
Provides unified interface compatible with existing API while using
PDFPlumber for improved accuracy.

Author: PDF Processing Team
Date: 2024
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .pdfplumber_table_extractor import PDFPlumberTableExtractor
from .pdfplumber_text_extractor import PDFPlumberTextExtractor
from .pdfplumber_number_extractor import PDFPlumberNumberExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFPlumberProcessor:
    """
    Main PDF processor using PDFPlumber with API compatibility
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the PDFPlumber processor
        
        Args:
            config: Configuration dictionary for processing
        """
        self.config = config or self._get_default_config()
        
        # Initialize extractors
        self.table_extractor = PDFPlumberTableExtractor(
            self.config.get('table_extraction', {})
        )
        self.text_extractor = PDFPlumberTextExtractor(
            self.config.get('text_extraction', {})
        )
        self.number_extractor = PDFPlumberNumberExtractor(
            self.config.get('number_extraction', {})
        )
        
        logger.info("PDFPlumberProcessor initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for PDFPlumber processing"""
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
                    # Order matters: more specific patterns first to avoid conflicts
                    'percentage': r'(?<!\w)\d+(?:\.\d+)?%(?!\w)',
                    'currency': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?\b',
                    'ratio': r'\b\d+(?:\.\d+)?x\b',  # New: patterns like 1.80x, 2.31x
                    'date_number': r'(?:FY|CY|Q[1-4]\s*)?(?:19|20)\d{2}\b',  # Years like 2024, FY2024, CY2024, Q1 2024
                    'scientific_notation': r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b',
                    'fraction': r'\b\d+/\d+\b',
                    'decimal': r'\b\d+\.\d+\b',
                    'integer': r'\b\d{1,3}(?:,\d{3})*\b',
                    'ordinal': r'\b\d{1,2}(?:st|nd|rd|th)\b'  # Separated from date_number
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
                'exclude_table_regions_from_text': True,
                'merge_duplicate_tables': True,
                'validate_extraction_quality': True
            }
        }
    
    def process_file(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF file and return comprehensive JSON representation
        Compatible with existing API
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing the complete PDF processing results
        """
        logger.info(f"Starting PDFPlumber processing: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        processing_start = datetime.now()
        
        # Initialize result structure
        result = {
            "pdf_processing_result": {
                "document_metadata": {
                    "filename": os.path.basename(pdf_path),
                    "processing_timestamp": processing_start.isoformat(),
                    "processing_duration": 0,
                    "extraction_methods": ["pdfplumber_table_extraction", "pdfplumber_text_extraction"]
                },
                "tables": {},
                "text_content": {},
                "processing_summary": {
                    "tables_extracted": 0,
                    "numbers_found": 0,
                    "text_sections": 0,
                    "overall_quality_score": 0.0,
                    "processing_errors": []
                }
            }
        }
        
        try:
            # Phase 1: Extract tables
            tables_data = None
            if self.config.get('processing_options', {}).get('extract_tables', True):
                logger.info("Phase 1: Extracting tables")
                try:
                    tables_data = self.table_extractor.extract_tables(pdf_path)
                    result["pdf_processing_result"]["tables"] = tables_data
                    result["pdf_processing_result"]["processing_summary"]["tables_extracted"] = \
                        len(tables_data.get("tables", []))
                    
                    logger.info(f"Table extraction completed: {len(tables_data.get('tables', []))} tables found")
                    
                except Exception as e:
                    error_msg = f"Table extraction failed: {str(e)}"
                    logger.error(error_msg)
                    result["pdf_processing_result"]["processing_summary"]["processing_errors"].append(error_msg)
            
            # Phase 2: Extract text content
            text_data = None
            if self.config.get('processing_options', {}).get('extract_text', True):
                logger.info("Phase 2: Extracting text content")
                try:
                    # Get table regions for exclusion if configured
                    table_regions = None
                    if (self.config.get('processing_options', {}).get('exclude_table_regions_from_text', True) 
                        and tables_data):
                        table_regions = tables_data.get("tables", [])
                    
                    text_data = self.text_extractor.extract_text_content(pdf_path, table_regions)
                    result["pdf_processing_result"]["text_content"] = text_data["text_content"]
                    
                    # Update summary with text statistics
                    text_summary = text_data["text_content"]["summary"]
                    result["pdf_processing_result"]["processing_summary"]["text_sections"] = \
                        text_summary["total_sections"]
                    result["pdf_processing_result"]["processing_summary"]["numbers_found"] = \
                        text_summary["total_numbers_found"]
                    
                    logger.info(f"Text extraction completed: {text_summary['total_sections']} sections found")
                    
                except Exception as e:
                    error_msg = f"Text extraction failed: {str(e)}"
                    logger.error(error_msg)
                    result["pdf_processing_result"]["processing_summary"]["processing_errors"].append(error_msg)
            
            # Phase 3: Calculate overall quality score
            overall_quality = self._calculate_overall_quality(tables_data, text_data)
            result["pdf_processing_result"]["processing_summary"]["overall_quality_score"] = overall_quality
            
            # Calculate processing duration
            processing_end = datetime.now()
            duration = (processing_end - processing_start).total_seconds()
            result["pdf_processing_result"]["document_metadata"]["processing_duration"] = duration
            
            logger.info(f"PDFPlumber processing completed in {duration:.2f} seconds")
            logger.info(f"Overall quality score: {overall_quality:.2f}")
            
            return result
            
        except Exception as e:
            error_msg = f"Critical error during PDF processing: {str(e)}"
            logger.error(error_msg)
            result["pdf_processing_result"]["processing_summary"]["processing_errors"].append(error_msg)
            raise
    
    def extract_tables_only(self, pdf_path: str) -> Dict:
        """
        Extract only tables from PDF (compatibility method)
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted tables
        """
        logger.info(f"Extracting tables only from: {pdf_path}")
        return self.table_extractor.extract_tables(pdf_path)
    
    def extract_text_only(self, pdf_path: str, table_regions: Optional[List[Dict]] = None) -> Dict:
        """
        Extract only text content from PDF (compatibility method)
        
        Args:
            pdf_path: Path to the PDF file
            table_regions: Optional table regions to exclude
            
        Returns:
            Dictionary containing extracted text content
        """
        logger.info(f"Extracting text only from: {pdf_path}")
        return self.text_extractor.extract_text_content(pdf_path, table_regions)
    
    def extract_numbers_only(self, text: str, position: Dict, metadata: Dict) -> List[Dict]:
        """
        Extract only numbers from text (compatibility method)
        
        Args:
            text: Text content to analyze
            position: Position information
            metadata: Text metadata
            
        Returns:
            List of extracted numbers
        """
        return self.number_extractor.extract_numbers_from_text(text, position, metadata)
    
    def _calculate_overall_quality(self, tables_data: Optional[Dict], text_data: Optional[Dict]) -> float:
        """
        Calculate overall quality score for the extraction
        
        Args:
            tables_data: Table extraction results
            text_data: Text extraction results
            
        Returns:
            Overall quality score between 0.0 and 1.0
        """
        quality_scores = []
        
        # Table extraction quality
        if tables_data:
            table_quality = self._calculate_table_quality(tables_data)
            quality_scores.append(table_quality)
        
        # Text extraction quality
        if text_data:
            text_quality = self._calculate_text_quality(text_data)
            quality_scores.append(text_quality)
        
        # Return average quality if we have scores, otherwise 0.0
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_table_quality(self, tables_data: Dict) -> float:
        """
        Calculate quality score for table extraction
        
        Args:
            tables_data: Table extraction results
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        tables = tables_data.get("tables", [])
        
        if not tables:
            return 0.0
        
        # Calculate average confidence from table metadata
        confidence_scores = []
        
        for table in tables:
            metadata = table.get("metadata", {})
            confidence = metadata.get("confidence", metadata.get("quality_score", 0.8))
            confidence_scores.append(confidence)
        
        # Weight by table size (larger tables should have more influence)
        weighted_scores = []
        total_cells = 0
        
        for i, table in enumerate(tables):
            cell_count = table.get("metadata", {}).get("cell_count", 1)
            total_cells += cell_count
            weighted_scores.append(confidence_scores[i] * cell_count)
        
        if total_cells == 0:
            return sum(confidence_scores) / len(confidence_scores)
        
        return sum(weighted_scores) / total_cells
    
    def _calculate_text_quality(self, text_data: Dict) -> float:
        """
        Calculate quality score for text extraction
        
        Args:
            text_data: Text extraction results
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        text_content = text_data.get("text_content", {})
        summary = text_content.get("summary", {})
        
        total_sections = summary.get("total_sections", 0)
        llm_ready_sections = summary.get("llm_ready_sections", 0)
        
        if total_sections == 0:
            return 0.0
        
        # Base quality on LLM readiness ratio
        llm_readiness_ratio = llm_ready_sections / total_sections
        
        # Factor in section count (more sections generally indicate better parsing)
        section_score = min(1.0, total_sections / 10)  # Normalize to 10 sections = 1.0
        
        # Combine metrics
        quality_score = (llm_readiness_ratio * 0.7) + (section_score * 0.3)
        
        return min(1.0, quality_score)
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the current configuration
        
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "configuration_summary": {
                "table_extraction_enabled": self.config.get('processing_options', {}).get('extract_tables', True),
                "text_extraction_enabled": self.config.get('processing_options', {}).get('extract_text', True),
                "number_extraction_enabled": self.config.get('processing_options', {}).get('extract_numbers', True),
                "table_exclusion_enabled": self.config.get('processing_options', {}).get('exclude_table_regions_from_text', True)
            }
        }
        
        # Validate table extraction configuration
        table_config = self.config.get('table_extraction', {})
        if table_config.get('quality_threshold', 0.8) < 0.5:
            validation_result["warnings"].append("Table quality threshold is very low, may result in poor quality tables")
        
        # Validate text extraction configuration
        text_config = self.config.get('text_extraction', {})
        section_config = text_config.get('section_detection', {})
        
        min_words = section_config.get('min_words_per_section', 10)
        max_words = section_config.get('max_words_per_section', 500)
        
        if min_words >= max_words:
            validation_result["errors"].append("min_words_per_section must be less than max_words_per_section")
            validation_result["valid"] = False
        
        # Validate number extraction configuration
        number_config = self.config.get('number_extraction', {})
        if number_config.get('confidence_threshold', 0.7) < 0.3:
            validation_result["warnings"].append("Number confidence threshold is very low, may result in many false positives")
        
        return validation_result
    
    def get_processing_capabilities(self) -> Dict[str, Any]:
        """
        Get information about processing capabilities
        
        Returns:
            Dictionary describing capabilities
        """
        return {
            "library": "pdfplumber",
            "version": "0.11.x",
            "capabilities": {
                "table_extraction": {
                    "supported": True,
                    "methods": ["lines", "text", "manual_detection"],
                    "formats_supported": ["bordered_tables", "text_tables", "mixed_tables"],
                    "quality_scoring": True,
                    "duplicate_detection": True
                },
                "text_extraction": {
                    "supported": True,
                    "layout_preservation": True,
                    "section_detection": True,
                    "metadata_extraction": True,
                    "coordinate_based": True,
                    "exclusion_zones": True
                },
                "number_extraction": {
                    "supported": True,
                    "formats": ["integer", "decimal", "percentage", "currency", "scientific_notation", "fraction", "date_number"],
                    "context_analysis": True,
                    "confidence_scoring": True,
                    "unit_detection": True,
                    "currency_detection": True
                }
            },
            "output_formats": {
                "table_oriented_json": True,
                "text_content_json": True,
                "unified_pdf_json": True,
                "backward_compatibility": True
            },
            "performance": {
                "single_library": True,
                "no_external_dependencies": True,
                "memory_efficient": True,
                "processing_speed": "fast"
            }
        } 