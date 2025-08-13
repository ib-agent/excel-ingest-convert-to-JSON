#!/usr/bin/env python3
"""
Clean PDF Processing Pipeline using PDFPlumber

A systematic approach to PDF processing with PDFPlumber integration:
1. Table extraction with PDFPlumber (improved accuracy)
2. Area exclusion to avoid double-processing
3. Text extraction with PDFPlumber
4. Number extraction with enhanced regex

Each phase is independently testable and debuggable.
Maintains API compatibility with the original CleanPDFProcessor.
"""

import logging
import json
import re
import pandas as pd
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import our PDFPlumber implementation
from converter.pdfplumber_processor import PDFPlumberProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TableInfo:
    """Container for table metadata and content - maintains compatibility"""
    page_number: int
    bbox: Dict[str, float]  # x0, y0, x1, y1
    rows: int
    cols: int
    dataframe: pd.DataFrame
    accuracy: float
    method: str  # 'pdfplumber'

@dataclass
class TextSection:
    """Container for text content and metadata"""
    page_number: int
    content: str
    bbox: Dict[str, float]
    
@dataclass
class ExtractedNumber:
    """Container for extracted numerical data"""
    value: str
    number_type: str  # 'currency', 'percentage', 'decimal', 'integer'
    context: str
    position: Dict[str, float]

class PDFPlumberTableExtractor:
    """Table extraction using PDFPlumber - provides compatibility interface"""
    
    def __init__(self):
        self.processor = PDFPlumberProcessor()
    
    def extract_tables(self, pdf_path: str) -> List[TableInfo]:
        """
        Extract tables from PDF using PDFPlumber
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of TableInfo objects compatible with original interface
        """
        logger.info(f"Extracting tables from {pdf_path} using PDFPlumber")
        
        try:
            # Use PDFPlumber to extract tables
            tables_data = self.processor.extract_tables_only(pdf_path)
            
            # Convert to TableInfo format for compatibility
            table_infos = []
            
            for table in tables_data.get("tables", []):
                table_info = self._convert_to_table_info(table)
                if table_info:
                    table_infos.append(table_info)
            
            logger.info(f"Successfully extracted {len(table_infos)} tables")
            return table_infos
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
    
    def _convert_to_table_info(self, pdfplumber_table: Dict) -> TableInfo:
        """
        Convert PDFPlumber table format to TableInfo format
        
        Args:
            pdfplumber_table: Table in PDFPlumber JSON format
            
        Returns:
            TableInfo object
        """
        try:
            # Extract basic info
            page_number = pdfplumber_table["region"]["page_number"]
            bbox_list = pdfplumber_table["region"]["bbox"]
            
            # Convert bbox from list to dict
            bbox = {
                "x0": bbox_list[0],
                "y0": bbox_list[1], 
                "x1": bbox_list[2],
                "y1": bbox_list[3]
            }
            
            # Get rows and columns data
            rows_data = pdfplumber_table["rows"]
            columns_data = pdfplumber_table["columns"]
            
            # Convert to pandas DataFrame
            df = self._create_dataframe_from_table(rows_data, columns_data)
            
            # Get quality metrics
            accuracy = pdfplumber_table["metadata"]["confidence"]
            
            return TableInfo(
                page_number=page_number,
                bbox=bbox,
                rows=len(rows_data),
                cols=len(columns_data),
                dataframe=df,
                accuracy=accuracy,
                method="pdfplumber"
            )
            
        except Exception as e:
            logger.error(f"Error converting PDFPlumber table to TableInfo: {e}")
            return None
    
    def _create_dataframe_from_table(self, rows_data: List[Dict], columns_data: List[Dict]) -> pd.DataFrame:
        """
        Create pandas DataFrame from PDFPlumber table structure
        
        Args:
            rows_data: List of row dictionaries
            columns_data: List of column dictionaries
            
        Returns:
            pandas DataFrame
        """
        # Get column labels
        column_labels = [col["column_label"] for col in columns_data]
        
        # Initialize data matrix
        data_matrix = []
        
        for row in rows_data:
            row_data = []
            for col_idx in range(len(column_labels)):
                # Find cell value for this position
                cell_value = ""
                for cell_key, cell_data in row["cells"].items():
                    if cell_data["column"] == col_idx + 1:  # 1-based indexing
                        cell_value = cell_data["value"]
                        break
                row_data.append(cell_value)
            data_matrix.append(row_data)
        
        # Create DataFrame
        df = pd.DataFrame(data_matrix, columns=column_labels)
        return df

class AreaExcluder:
    """Area exclusion logic - unchanged from original"""
    
    def get_exclusion_zones(self, tables: List[TableInfo]) -> Dict[int, List[Dict[str, float]]]:
        """
        Generate exclusion zones based on table locations
        
        Args:
            tables: List of extracted tables
            
        Returns:
            Dictionary mapping page numbers to exclusion zones
        """
        exclusion_zones = {}
        
        for table in tables:
            page_num = table.page_number
            
            if page_num not in exclusion_zones:
                exclusion_zones[page_num] = []
            
            # Add padding around table
            padding = 10
            exclusion_zone = {
                "x0": max(0, table.bbox["x0"] - padding),
                "y0": max(0, table.bbox["y0"] - padding),
                "x1": table.bbox["x1"] + padding,
                "y1": table.bbox["y1"] + padding
            }
            
            exclusion_zones[page_num].append(exclusion_zone)
            
            logger.debug(f"Added exclusion zone for table on page {page_num}: {exclusion_zone}")
        
        return exclusion_zones

class PDFPlumberTextExtractor:
    """Text extraction using PDFPlumber"""
    
    def __init__(self):
        self.processor = PDFPlumberProcessor()
    
    def extract_text_excluding_areas(self, pdf_path: str, exclusion_zones: Dict[int, List[Dict[str, float]]]) -> List[TextSection]:
        """
        Extract text content excluding specified areas
        
        Args:
            pdf_path: Path to the PDF file
            exclusion_zones: Areas to exclude from text extraction
            
        Returns:
            List of TextSection objects
        """
        logger.info(f"Extracting text from {pdf_path} with exclusion zones")
        
        try:
            # Convert exclusion zones to table regions format
            table_regions = self._convert_exclusion_zones_to_tables(exclusion_zones)
            
            # Extract text using PDFPlumber
            text_data = self.processor.extract_text_only(pdf_path, table_regions)
            
            # Convert to TextSection format for compatibility
            text_sections = []
            
            for page in text_data["text_content"]["pages"]:
                for section in page["sections"]:
                    text_section = self._convert_to_text_section(section, page["page_number"])
                    if text_section:
                        text_sections.append(text_section)
            
            logger.info(f"Successfully extracted {len(text_sections)} text sections")
            return text_sections
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return []
    
    def _convert_exclusion_zones_to_tables(self, exclusion_zones: Dict[int, List[Dict[str, float]]]) -> List[Dict]:
        """
        Convert exclusion zones to table regions format for PDFPlumber
        
        Args:
            exclusion_zones: Dictionary of exclusion zones by page
            
        Returns:
            List of mock table regions
        """
        table_regions = []
        
        for page_num, zones in exclusion_zones.items():
            for i, zone in enumerate(zones):
                # Create a mock table region for exclusion
                table_region = {
                    "table_id": f"exclusion_page_{page_num}_zone_{i}",
                    "region": {
                        "page_number": page_num,
                        "bbox": [zone["x0"], zone["y0"], zone["x1"], zone["y1"]]
                    }
                }
                table_regions.append(table_region)
        
        return table_regions
    
    def _convert_to_text_section(self, pdfplumber_section: Dict, page_number: int) -> TextSection:
        """
        Convert PDFPlumber section to TextSection format
        
        Args:
            pdfplumber_section: Section in PDFPlumber format
            page_number: Page number
            
        Returns:
            TextSection object
        """
        try:
            content = pdfplumber_section["content"]
            bbox_list = pdfplumber_section["position"]["bbox"]
            
            # Convert bbox from list to dict
            bbox = {
                "x0": bbox_list[0],
                "y0": bbox_list[1],
                "x1": bbox_list[2], 
                "y1": bbox_list[3]
            }
            
            return TextSection(
                page_number=page_number,
                content=content,
                bbox=bbox
            )
            
        except Exception as e:
            logger.error(f"Error converting PDFPlumber section to TextSection: {e}")
            return None

class NumberExtractor:
    """Number extraction from text sections - enhanced for PDFPlumber"""
    
    def __init__(self):
        # Enhanced number patterns
        self.patterns = {
            'currency': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',
            'percentage': r'\d+(?:\.\d+)?%',
            'decimal': r'\d+\.\d+',
            'integer': r'\b\d{1,3}(?:,\d{3})*\b'
        }
        
        self.business_terms = {
            'revenue', 'income', 'profit', 'loss', 'cost', 'expense',
            'sales', 'earnings', 'margin', 'total', 'amount'
        }
    
    def extract_numbers_from_text(self, text_sections: List[TextSection]) -> List[ExtractedNumber]:
        """
        Extract numbers from text sections
        
        Args:
            text_sections: List of text sections to process
            
        Returns:
            List of ExtractedNumber objects
        """
        logger.info(f"Extracting numbers from {len(text_sections)} text sections")
        
        extracted_numbers = []
        
        for section in text_sections:
            if self._should_skip_section_for_numbers(section):
                continue
            
            section_numbers = self._extract_numbers_from_section(section)
            extracted_numbers.extend(section_numbers)
        
        logger.info(f"Successfully extracted {len(extracted_numbers)} numbers")
        return extracted_numbers
    
    def _extract_numbers_from_section(self, section: TextSection) -> List[ExtractedNumber]:
        """Extract numbers from a single text section"""
        numbers = []
        
        for number_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, section.content)
            
            for match in matches:
                number_str = match.group(0)
                
                # Get context around the number
                start = max(0, match.start() - 50)
                end = min(len(section.content), match.end() + 50)
                context = section.content[start:end]
                
                # Skip if this number should be ignored
                if self._should_skip_number(number_str, context):
                    continue
                
                # Estimate position within section
                position = {
                    "x0": section.bbox["x0"],
                    "y0": section.bbox["y0"],
                    "x1": section.bbox["x1"],
                    "y1": section.bbox["y1"]
                }
                
                extracted_number = ExtractedNumber(
                    value=number_str,
                    number_type=number_type,
                    context=context.strip(),
                    position=position
                )
                
                numbers.append(extracted_number)
        
        return numbers
    
    def _should_skip_section_for_numbers(self, section: TextSection) -> bool:
        """Determine if section should be skipped for number extraction"""
        content_lower = section.content.lower()
        
        # Skip if section is too short
        if len(section.content.strip()) < 10:
            return True
        
        # Skip if section contains mostly non-business content
        skip_terms = {'page', 'table', 'figure', 'section', 'chapter'}
        skip_count = sum(1 for term in skip_terms if term in content_lower)
        
        if skip_count > 2:
            return True
        
        return False
    
    def _should_skip_number(self, number_str: str, context: str) -> bool:
        """Determine if a specific number should be skipped"""
        context_lower = context.lower()
        
        # Skip numbers that are clearly not business-related
        skip_contexts = [
            'page', 'section', 'figure', 'table', 'chapter',
            'version', 'year', 'date', 'phone', 'zip'
        ]
        
        for skip_term in skip_contexts:
            if skip_term in context_lower:
                return True
        
        # Skip very small numbers unless they're percentages or currency
        try:
            num_value = float(re.sub(r'[^\d.]', '', number_str))
            if num_value < 1.0 and '$' not in number_str and '%' not in number_str:
                return True
        except:
            pass
        
        return False

class CleanPDFProcessor:
    """Main PDF processing pipeline using PDFPlumber"""
    
    def __init__(self):
        self.table_extractor = PDFPlumberTableExtractor()
        self.area_excluder = AreaExcluder()
        self.text_extractor = PDFPlumberTextExtractor()
        self.number_extractor = NumberExtractor()
    
    def process(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF with comprehensive table and text extraction
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing all extraction results
        """
        logger.info(f"Starting clean PDF processing: {pdf_path}")
        
        # Phase 1: Extract tables
        logger.info("Phase 1: Table extraction")
        tables = self.table_extractor.extract_tables(pdf_path)
        
        # Phase 2: Calculate exclusion zones
        logger.info("Phase 2: Calculate exclusion zones")
        exclusion_zones = self.area_excluder.get_exclusion_zones(tables)
        
        # Phase 3: Extract text excluding table areas
        logger.info("Phase 3: Text extraction")
        text_sections = self.text_extractor.extract_text_excluding_areas(pdf_path, exclusion_zones)
        
        # Phase 4: Extract numbers from text
        logger.info("Phase 4: Number extraction")
        numbers = self.number_extractor.extract_numbers_from_text(text_sections)
        
        # Compile results
        result = {
            "processing_metadata": {
                "file_path": pdf_path,
                "extraction_method": "pdfplumber_clean_pipeline",
                "tables_found": len(tables),
                "text_sections_found": len(text_sections),
                "numbers_found": len(numbers)
            },
            "tables": [self._table_to_dict(table) for table in tables],
            "text_sections": [self._text_section_to_dict(section) for section in text_sections],
            "numbers": [self._number_to_dict(number) for number in numbers],
            "exclusion_zones": exclusion_zones
        }
        
        logger.info(f"Clean PDF processing completed: {len(tables)} tables, {len(text_sections)} text sections, {len(numbers)} numbers")
        return result
    
    def _table_to_dict(self, table: TableInfo) -> Dict[str, Any]:
        """Convert TableInfo to dictionary"""
        return {
            "page_number": table.page_number,
            "bbox": table.bbox,
            "rows": table.rows,
            "cols": table.cols,
            "accuracy": table.accuracy,
            "method": table.method,
            "data": table.dataframe.to_dict('records')
        }
    
    def _text_section_to_dict(self, section: TextSection) -> Dict[str, Any]:
        """Convert TextSection to dictionary"""
        return {
            "page_number": section.page_number,
            "content": section.content,
            "bbox": section.bbox
        }
    
    def _number_to_dict(self, number: ExtractedNumber) -> Dict[str, Any]:
        """Convert ExtractedNumber to dictionary"""
        return {
            "value": number.value,
            "type": number.number_type,
            "context": number.context,
            "position": number.position
        }

def main():
    """Main function for testing"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python pdfplumber_clean_processor.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: File {pdf_path} not found")
        sys.exit(1)
    
    processor = CleanPDFProcessor()
    result = processor.process(pdf_path)
    
    # Save results
    output_file = f"{Path(pdf_path).stem}_pdfplumber_clean_results.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Processing completed. Results saved to: {output_file}")
    print(f"Tables: {result['processing_metadata']['tables_found']}")
    print(f"Text sections: {result['processing_metadata']['text_sections_found']}")
    print(f"Numbers: {result['processing_metadata']['numbers_found']}")

if __name__ == "__main__":
    main() 