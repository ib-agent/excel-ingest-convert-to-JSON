#!/usr/bin/env python3
"""
PDF Table Removal Processor

Implements the innovative 4-step approach to eliminate duplicate detection:
1. Detect and extract tables using PDFPlumber
2. Capture table data in JSON format
3. Create PDF with table regions removed/whitened
4. Extract text from table-free PDF following pdf-json-schema.md

This approach physically separates table and text content to prevent
the same content from appearing in both tables and text sections.

Author: PDF Processing Team
Date: 2024
"""

import os
import json
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Import existing PDFPlumber components
from converter.pdfplumber_table_extractor import PDFPlumberTableExtractor
from converter.pdfplumber_text_extractor import PDFPlumberTextExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class PDFRegionRemover:
    """
    Handles PDF modification to remove/whiten table regions
    """
    
    def __init__(self):
        """Initialize the PDF region remover"""
        self.temp_files = []  # Track temporary files for cleanup
        logger.info("PDFRegionRemover initialized")
    
    def remove_regions(self, pdf_path: str, table_regions: List[Dict]) -> str:
        """
        Create a new PDF with specified table regions removed/whitened
        
        Args:
            pdf_path: Path to the original PDF
            table_regions: List of table region dictionaries with bbox coordinates
            
        Returns:
            Path to the table-free PDF file
        """
        logger.info(f"Removing {len(table_regions)} table regions from {pdf_path}")
        
        try:
            # Create temporary file for the table-free PDF
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='table_free_')
            os.close(temp_fd)  # Close file descriptor, we'll write to path directly
            self.temp_files.append(temp_path)
            
            # Method 1: Use PyMuPDF (Fitz) for white rectangle overlay
            success = self._remove_with_pymupdf(pdf_path, table_regions, temp_path)
            
            if not success:
                # Fallback: Use PyPDF2 approach
                logger.warning("PyMuPDF method failed, trying PyPDF2 fallback")
                success = self._remove_with_pypdf(pdf_path, table_regions, temp_path)
            
            if success:
                logger.info(f"Successfully created table-free PDF: {temp_path}")
                return temp_path
            else:
                raise Exception("All PDF modification methods failed")
                
        except Exception as e:
            logger.error(f"Error removing table regions: {e}")
            raise
    
    def _extract_page_numbers(self, page_number_raw) -> List[int]:
        """
        Extract individual page numbers from page number data
        
        Args:
            page_number_raw: Can be int, str (like '3-4'), or list
            
        Returns:
            List of page numbers (0-based)
        """
        page_numbers = []
        
        if isinstance(page_number_raw, int):
            page_numbers.append(page_number_raw - 1)  # Convert to 0-based
        elif isinstance(page_number_raw, str):
            if '-' in page_number_raw:
                # Handle page ranges like '3-4'
                start, end = page_number_raw.split('-')
                for page in range(int(start), int(end) + 1):
                    page_numbers.append(page - 1)  # Convert to 0-based
            else:
                page_numbers.append(int(page_number_raw) - 1)  # Convert to 0-based
        elif isinstance(page_number_raw, list):
            # Handle list of page numbers
            for page in page_number_raw:
                page_numbers.extend(self._extract_page_numbers(page))
        else:
            # Default to page 1 if unknown format
            page_numbers.append(0)
            
        return page_numbers

    def _remove_with_pymupdf(self, pdf_path: str, table_regions: List[Dict], output_path: str) -> bool:
        """
        Remove table regions using PyMuPDF (Fitz) with white rectangle overlay
        
        Args:
            pdf_path: Input PDF path
            table_regions: Table regions to remove
            output_path: Output PDF path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import fitz  # PyMuPDF
            
            # Open the PDF
            doc = fitz.open(pdf_path)
            
            # Group regions by page for efficient processing
            regions_by_page = {}
            for region in table_regions:
                # Handle page number conversion more robustly
                page_num_raw = region.get('region', {}).get('page_number', 1)
                page_numbers = self._extract_page_numbers(page_num_raw)
                
                for page_num in page_numbers:
                    if page_num not in regions_by_page:
                        regions_by_page[page_num] = []
                    regions_by_page[page_num].append(region)
            
            # Process each page
            for page_num in range(len(doc)):
                if page_num in regions_by_page:
                    page = doc[page_num]
                    
                    for region in regions_by_page[page_num]:
                        # Extract bbox coordinates
                        bbox = region.get('region', {}).get('bbox', [])
                        if len(bbox) >= 4:
                            # Ensure all coordinates are floats
                            x0, y0, x1, y1 = [float(coord) for coord in bbox[:4]]
                            
                            # Create white rectangle to cover table
                            rect = fitz.Rect(x0, y0, x1, y1)
                            
                            # Add white rectangle annotation
                            annot = page.add_rect_annot(rect)
                            annot.set_colors(stroke=[1, 1, 1], fill=[1, 1, 1])  # White
                            annot.set_opacity(1.0)  # Fully opaque
                            annot.update()
                            
                            logger.debug(f"Removed table region on page {page_num + 1}: {bbox}")
            
            # Save the modified PDF
            doc.save(output_path)
            doc.close()
            
            logger.info("PyMuPDF table removal completed successfully")
            return True
            
        except ImportError:
            logger.warning("PyMuPDF (fitz) not available, skipping this method")
            return False
        except Exception as e:
            logger.error(f"PyMuPDF table removal failed: {e}")
            return False
    
    def _remove_with_pypdf(self, pdf_path: str, table_regions: List[Dict], output_path: str) -> bool:
        """
        Remove table regions using PyPDF2/ReportLab approach
        
        This is a fallback method that creates overlays with white rectangles
        
        Args:
            pdf_path: Input PDF path
            table_regions: Table regions to remove
            output_path: Output PDF path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from PyPDF2 import PdfReader, PdfWriter
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            import io
            
            # Read original PDF
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            
            # Group regions by page
            regions_by_page = {}
            for region in table_regions:
                # Handle page number conversion more robustly
                page_num_raw = region.get('region', {}).get('page_number', 1)
                page_numbers = self._extract_page_numbers(page_num_raw)
                
                for page_num in page_numbers:
                    if page_num not in regions_by_page:
                        regions_by_page[page_num] = []
                    regions_by_page[page_num].append(region)
            
            # Process each page
            for page_num, page in enumerate(reader.pages):
                if page_num in regions_by_page:
                    # Create overlay with white rectangles
                    overlay = self._create_white_rectangle_overlay(
                        regions_by_page[page_num], 
                        page.mediabox
                    )
                    
                    if overlay:
                        # Merge overlay with original page
                        page.merge_page(overlay)
                
                writer.add_page(page)
            
            # Write the result
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info("PyPDF2 table removal completed successfully")
            return True
            
        except ImportError as e:
            logger.warning(f"Required libraries not available for PyPDF2 method: {e}")
            return False
        except Exception as e:
            logger.error(f"PyPDF2 table removal failed: {e}")
            return False
    
    def _create_white_rectangle_overlay(self, regions: List[Dict], mediabox) -> Optional[Any]:
        """
        Create a PDF overlay with white rectangles for table regions
        
        Args:
            regions: Table regions to cover
            mediabox: Page dimensions
            
        Returns:
            PDF page object with white rectangles, or None if failed
        """
        try:
            from reportlab.pdfgen import canvas
            from PyPDF2 import PdfReader
            import io
            
            # Create in-memory PDF with white rectangles
            buffer = io.BytesIO()
            page_width = float(mediabox[2])
            page_height = float(mediabox[3])
            
            c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
            c.setFillColor((1, 1, 1))  # White fill
            c.setStrokeColor((1, 1, 1))  # White stroke
            
            # Draw white rectangles over table regions
            for region in regions:
                bbox = region.get('region', {}).get('bbox', [])
                if len(bbox) >= 4:
                    # Ensure all coordinates are floats
                    x0, y0, x1, y1 = [float(coord) for coord in bbox[:4]]
                    # Note: ReportLab uses bottom-left origin, PDF uses top-left
                    # Convert coordinates if necessary
                    c.rect(x0, page_height - y1, x1 - x0, y1 - y0, fill=1, stroke=1)
            
            c.save()
            buffer.seek(0)
            
            # Read back as PDF page
            overlay_reader = PdfReader(buffer)
            return overlay_reader.pages[0]
            
        except Exception as e:
            logger.error(f"Failed to create overlay: {e}")
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"Cleaned up temporary file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {e}")
        self.temp_files.clear()

class PDFTableRemovalProcessor:
    """
    Main processor implementing the 4-step table removal workflow
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the PDF table removal processor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        
        # Initialize components
        self.table_extractor = PDFPlumberTableExtractor(config)
        self.region_remover = PDFRegionRemover()
        self.text_extractor = PDFPlumberTextExtractor(config)
        
        # Processing state
        self.processing_start_time = None
        self.table_free_pdf_path = None
        
        logger.info("PDFTableRemovalProcessor initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'table_extraction': {
                'quality_threshold': 0.8,
                'min_table_size': 2,
                'max_tables_per_page': 10
            },
            'region_removal': {
                'padding': 5,  # Pixels of padding around table regions
                'method': 'auto'  # 'pymupdf', 'pypdf', or 'auto'
            },
            'text_extraction': {
                'min_section_size': 50,
                'max_section_size': 1000,
                'enable_number_extraction': True
            }
        }
    
    def process(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF using the 4-step table removal approach
        
        Args:
            pdf_path: Path to the PDF file to process
            
        Returns:
            Combined JSON result with tables and text_content sections
        """
        logger.info(f"Starting 4-step table removal processing: {pdf_path}")
        self.processing_start_time = datetime.now()
        
        try:
            # Validate input
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Step 1: Table Detection and Extraction
            logger.info("Step 1: Table Detection and Extraction")
            tables_result = self._step1_extract_tables(pdf_path)
            
            # Step 2: Table Data Capture (already in JSON format from step 1)
            logger.info("Step 2: Table Data Capture")
            tables_json = self._step2_capture_table_data(tables_result)
            
            # Step 3: PDF Table Removal
            logger.info("Step 3: PDF Table Removal")
            table_free_pdf = self._step3_remove_tables(pdf_path, tables_result)
            
            # Step 4: Text Extraction from Table-Free PDF
            logger.info("Step 4: Text Extraction from Table-Free PDF")
            text_content = self._step4_extract_text(table_free_pdf)
            
            # Combine results
            result = self._combine_results(pdf_path, tables_json, text_content)
            
            # Calculate processing duration
            processing_duration = (datetime.now() - self.processing_start_time).total_seconds()
            result["pdf_processing_result"]["document_metadata"]["processing_duration"] = processing_duration
            
            logger.info(f"Table removal processing completed in {processing_duration:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
        finally:
            # Cleanup temporary files
            self.region_remover.cleanup()
    
    def _step1_extract_tables(self, pdf_path: str) -> Dict[str, Any]:
        """Step 1: Extract tables and their regions"""
        logger.info("Extracting tables using PDFPlumber...")
        return self.table_extractor.extract_tables(pdf_path)
    
    def _step2_capture_table_data(self, tables_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Capture table data in JSON format"""
        logger.info("Capturing table data in JSON format...")
        # Data is already in the correct format from PDFPlumber extractor
        return tables_result
    
    def _step3_remove_tables(self, pdf_path: str, tables_result: Dict[str, Any]) -> str:
        """Step 3: Create PDF with table regions removed"""
        logger.info("Creating table-free PDF...")
        
        # Extract table regions for removal
        table_regions = []
        for table in tables_result.get("tables", []):
            table_regions.append(table)
        
        # Add padding to regions if configured
        padding = self.config.get('region_removal', {}).get('padding', 5)
        if padding > 0:
            table_regions = self._add_padding_to_regions(table_regions, padding)
        
        # Remove table regions
        self.table_free_pdf_path = self.region_remover.remove_regions(pdf_path, table_regions)
        return self.table_free_pdf_path
    
    def _step4_extract_text(self, table_free_pdf: str) -> Dict[str, Any]:
        """Step 4: Extract text content from table-free PDF"""
        logger.info("Extracting text from table-free PDF...")
        
        # Extract text content following pdf-json-schema.md
        # No need to exclude table regions since they've been physically removed
        return self.text_extractor.extract_text_content(table_free_pdf)
    
    def _add_padding_to_regions(self, regions: List[Dict], padding: int) -> List[Dict]:
        """Add padding around table regions to ensure complete removal"""
        padded_regions = []
        
        for region in regions:
            region_copy = region.copy()
            bbox = region_copy.get('region', {}).get('bbox', [])
            
            if len(bbox) >= 4:
                # Ensure all coordinates are floats
                x0, y0, x1, y1 = [float(coord) for coord in bbox[:4]]
                # Add padding
                padded_bbox = [
                    max(0, x0 - padding),      # x0
                    max(0, y0 - padding),      # y0  
                    x1 + padding,              # x1
                    y1 + padding               # y1
                ]
                region_copy['region']['bbox'] = padded_bbox
                
            padded_regions.append(region_copy)
        
        return padded_regions
    
    def _combine_results(self, pdf_path: str, tables_json: Dict, text_content: Dict) -> Dict[str, Any]:
        """Combine table and text results into final JSON structure"""
        
        # Calculate summary statistics
        tables_count = len(tables_json.get("tables", []))
        numbers_found = self._count_numbers_in_text_content(text_content)
        text_sections = self._count_text_sections(text_content)
        
        return {
            "pdf_processing_result": {
                "document_metadata": {
                    "filename": os.path.basename(pdf_path),
                    "total_pages": text_content.get("text_content", {}).get("document_metadata", {}).get("total_pages", 0),
                    "processing_timestamp": datetime.now().isoformat(),
                    "processing_duration": 0,  # Will be set in main process method
                    "extraction_methods": ["table_extraction", "text_extraction_table_free"],
                    "table_removal_applied": True
                },
                "tables": tables_json,
                "text_content": text_content.get("text_content", {}),
                "processing_summary": {
                    "tables_extracted": tables_count,
                    "tables_removed_from_pdf": tables_count,
                    "numbers_found": numbers_found,
                    "text_sections": text_sections,
                    "duplicate_prevention": "table_removal_applied",
                    "overall_quality_score": self._calculate_quality_score(tables_count, text_sections),
                    "processing_errors": []
                }
            }
        }
    
    def _count_numbers_in_text_content(self, text_content: Dict) -> int:
        """Count total numbers found in text content"""
        total_numbers = 0
        pages = text_content.get("text_content", {}).get("pages", [])
        
        for page in pages:
            for section in page.get("sections", []):
                total_numbers += len(section.get("numbers", []))
        
        return total_numbers
    
    def _count_text_sections(self, text_content: Dict) -> int:
        """Count total text sections"""
        total_sections = 0
        pages = text_content.get("text_content", {}).get("pages", [])
        
        for page in pages:
            total_sections += len(page.get("sections", []))
        
        return total_sections
    
    def _calculate_quality_score(self, tables_count: int, text_sections: int) -> float:
        """Calculate overall processing quality score"""
        # Simple quality metric based on content found
        base_score = 0.7
        
        # Bonus for finding content
        if tables_count > 0:
            base_score += 0.15
        if text_sections > 0:
            base_score += 0.15
        
        return min(1.0, base_score)

def main():
    """Main function for testing"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python pdf_table_removal_processor.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: File {pdf_path} not found")
        sys.exit(1)
    
    # Process PDF with table removal
    processor = PDFTableRemovalProcessor()
    result = processor.process(pdf_path)
    
    # Save results
    output_file = f"{Path(pdf_path).stem}_table_removal_results.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print summary
    summary = result["pdf_processing_result"]["processing_summary"]
    print(f"Processing completed. Results saved to: {output_file}")
    print(f"Tables extracted: {summary['tables_extracted']}")
    print(f"Tables removed from PDF: {summary['tables_removed_from_pdf']}")
    print(f"Text sections: {summary['text_sections']}")
    print(f"Numbers found: {summary['numbers_found']}")
    print(f"Quality score: {summary['overall_quality_score']:.2f}")
    print(f"Duplicate prevention: {summary['duplicate_prevention']}")

if __name__ == "__main__":
    main() 