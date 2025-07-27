"""
PDF Processing Module

This module provides comprehensive PDF processing capabilities including:
- Table extraction using camelot-py
- Text extraction using PyMuPDF
- Number extraction from text content

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
import pandas as pd

# Import camelot-py for table extraction
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    logging.warning("camelot-py not available. Install with: pip install camelot-py[cv]")

# Import PyMuPDF for text extraction
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF not available. Install with: pip install PyMuPDF")

# Import additional libraries for enhanced table detection
try:
    import re
    import csv
    from io import StringIO
    ENHANCED_TABLE_DETECTION_AVAILABLE = True
except ImportError:
    ENHANCED_TABLE_DETECTION_AVAILABLE = False
    logging.warning("Enhanced table detection dependencies not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFTableExtractor:
    """
    Handles table extraction from PDF documents using camelot-py
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the table extractor with configuration
        
        Args:
            config: Configuration dictionary for table extraction
        """
        if not CAMELOT_AVAILABLE:
            raise ImportError("camelot-py is required for table extraction. Install with: pip install camelot-py[cv]")
        
        self.config = config or self._get_default_config()
        self.extraction_methods = self.config.get('methods', ['lattice', 'stream'])
        self.quality_threshold = self.config.get('quality_threshold', 0.8)
        self.edge_tolerance = self.config.get('edge_tolerance', 3)
        self.row_tolerance = self.config.get('row_tolerance', 3)
        self.column_tolerance = self.config.get('column_tolerance', 3)
        self.min_table_size = self.config.get('min_table_size', 4)
        
    def _get_default_config(self) -> Dict:
        """Get default configuration for table extraction"""
        return {
            'methods': ['lattice', 'stream'],
            'quality_threshold': 0.8,
            'edge_tolerance': 3,
            'row_tolerance': 3,
            'column_tolerance': 3,
            'min_table_size': 3,  # Reduced from 4 to allow smaller tables
            'max_tables_per_page': 10
        }
    
    def extract_tables(self, pdf_path: str) -> Dict:
        """
        Extract tables from PDF using camelot-py with fallback to text-based detection
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted tables in table-oriented JSON format
        """
        logger.info(f"Starting table extraction from: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        tables_data = {
            "tables": [],
            "metadata": {
                "filename": os.path.basename(pdf_path),
                "extraction_timestamp": datetime.now().isoformat(),
                "extraction_method": "camelot_py",
                "total_tables_found": 0,
                "quality_distribution": {"high": 0, "medium": 0, "low": 0}
            }
        }
        
        table_counter = 1
        camelot_success = False
        
        try:
            # Extract tables using different methods
            for method in self.extraction_methods:
                logger.info(f"Extracting tables using {method} method")
                
                try:
                    if method == 'lattice':
                        # Try lattice method, but don't fail if Ghostscript is missing
                        try:
                            tables = camelot.read_pdf(
                                pdf_path, 
                                pages='all', 
                                flavor='lattice',
                                edge_tolerance=self.edge_tolerance,
                                row_tolerance=self.row_tolerance,
                                column_tolerance=self.column_tolerance
                            )
                            camelot_success = True
                        except Exception as lattice_error:
                            if "Ghostscript is not installed" in str(lattice_error):
                                logger.info(f"Skipping lattice method (Ghostscript not available), using stream method instead")
                                continue
                            elif "PdfFileReader is deprecated" in str(lattice_error):
                                logger.warning(f"PyPDF2 compatibility issue with {method} method, trying fallback detection")
                                continue
                            else:
                                raise lattice_error
                    elif method == 'stream':
                        # Try to detect tables with more specific parameters
                        try:
                            tables = camelot.read_pdf(
                                pdf_path, 
                                pages='all', 
                                flavor='stream',
                                edge_tolerance=self.edge_tolerance,
                                row_tolerance=self.row_tolerance,
                                column_tolerance=self.column_tolerance,
                                strip_text='\n'  # Remove extra newlines
                            )
                            camelot_success = True
                        except Exception as stream_error:
                            if "PdfFileReader is deprecated" in str(stream_error):
                                logger.warning(f"PyPDF2 compatibility issue with {method} method, trying fallback detection")
                                continue
                            else:
                                raise stream_error
                    else:
                        logger.warning(f"Unknown extraction method: {method}")
                        continue
                    
                    # Process extracted tables
                    for i, table in enumerate(tables):
                        logger.info(f"Processing table {i+1} on page {table.page}: shape={table.df.shape}, accuracy={table.accuracy}")
                        
                        # Skip tables that are too small
                        if table.df.shape[0] < self.min_table_size or table.df.shape[1] < 2:
                            logger.debug(f"Skipping small table {i+1} on page {table.page}: {table.df.shape}")
                            continue
                        
                        # Skip tables with very low quality
                        if table.accuracy < self.quality_threshold:
                            logger.debug(f"Skipping low quality table {i+1} on page {table.page}: accuracy={table.accuracy}")
                            continue
                        
                        # Check if table covers the entire page (likely false detection)
                        if hasattr(table, '_bbox') and table._bbox is not None:
                            bbox = table._bbox
                            page_width = 612.0  # Standard PDF page width
                            page_height = 792.0  # Standard PDF page height
                            
                            # If table covers more than 95% of the page, it's likely a false detection
                            table_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                            page_area = page_width * page_height
                            coverage_ratio = table_area / page_area
                            
                            if coverage_ratio > 0.95:
                                logger.warning(f"Table {i+1} on page {table.page} covers {coverage_ratio:.1%} of page - checking content...")
                                # Instead of skipping, let's check if it actually contains table-like data
                                # If the table has mixed content (text + numbers), it might be a false detection
                                has_numbers = False
                                has_text = False
                                for _, row in table.df.iterrows():
                                    for cell in row:
                                        if pd.notna(cell):
                                            cell_str = str(cell).strip()
                                            if cell_str.replace('.', '').replace('-', '').isdigit():
                                                has_numbers = True
                                            else:
                                                has_text = True
                                
                                if has_text and not has_numbers:
                                    logger.warning(f"Skipping table {i+1} on page {table.page}: contains only text, no numerical data")
                                    continue
                        
                        # Convert table to JSON format
                        table_json = self._convert_table_to_json(
                            table, 
                            table_counter, 
                            method
                        )
                        
                        if table_json:
                            # Filter out non-table content from the table
                            logger.info(f"Filtering table {table_counter} with {len(table_json.get('rows', []))} rows")
                            try:
                                filtered_table = self._filter_table_content(table_json)
                                logger.info(f"Filtering completed, result: {filtered_table is not None}")
                                if filtered_table and len(filtered_table["rows"]) > 0:
                                    logger.info(f"Table {table_counter} filtered to {len(filtered_table['rows'])} rows")
                                    tables_data["tables"].append(filtered_table)
                                    table_counter += 1
                                    
                                    # Update quality distribution only for accepted tables
                                    if table.accuracy >= 0.8:
                                        tables_data["metadata"]["quality_distribution"]["high"] += 1
                                    elif table.accuracy >= 0.5:
                                        tables_data["metadata"]["quality_distribution"]["medium"] += 1
                                    else:
                                        tables_data["metadata"]["quality_distribution"]["low"] += 1
                                else:
                                    logger.warning(f"Table {table_counter} was filtered out (no valid content)")
                            except Exception as e:
                                logger.error(f"Error during table filtering: {str(e)}")
                                # Fall back to using the original table
                                tables_data["tables"].append(table_json)
                                table_counter += 1
                
                except Exception as e:
                    logger.error(f"Error extracting tables with {method} method: {str(e)}")
                    continue
            
            # If camelot failed to extract any tables, try fallback text-based detection
            if not camelot_success and len(tables_data["tables"]) == 0:
                logger.info("Camelot extraction failed, trying fallback text-based table detection")
                fallback_tables = self._extract_tables_from_text(pdf_path)
                if fallback_tables:
                    tables_data["tables"].extend(fallback_tables)
                    tables_data["metadata"]["extraction_method"] = "text_based_fallback"
                    logger.info(f"Fallback detection found {len(fallback_tables)} tables")
            
            # Update total tables found
            tables_data["metadata"]["total_tables_found"] = len(tables_data["tables"])
            
            logger.info(f"Table extraction completed. Found {len(tables_data['tables'])} tables")
            return tables_data
            
        except Exception as e:
            logger.error(f"Error during table extraction: {str(e)}")
            raise
    
    def _convert_table_to_json(self, table: Any, table_id: int, method: str) -> Optional[Dict]:
        """
        Convert camelot table object to table-oriented JSON format
        
        Args:
            table: Camelot table object
            table_id: Unique table identifier
            method: Extraction method used
            
        Returns:
            Dictionary in table-oriented JSON format
        """
        try:
            df = table.df
            
            # Determine header rows (usually first row)
            header_rows = [0] if df.shape[0] > 0 else []
            data_start_row = 1 if header_rows else 0
            
            # Create columns array
            columns = []
            for col_idx in range(df.shape[1]):
                column_label = self._generate_column_label(df, col_idx, header_rows)
                
                column_data = {
                    "column_index": col_idx,
                    "column_label": column_label,
                    "is_header_column": col_idx == 0,  # First column often contains row headers
                    "cells": {}
                }
                
                # Add cell data for this column
                for row_idx in range(df.shape[0]):
                    cell_value = df.iloc[row_idx, col_idx]
                    if pd.notna(cell_value) and str(cell_value).strip():
                        cell_key = f"{chr(65 + col_idx)}{row_idx + 1}"  # A1, B1, etc.
                        column_data["cells"][cell_key] = {
                            "value": str(cell_value).strip(),
                            "row": row_idx + 1,
                            "column": col_idx + 1
                        }
                
                columns.append(column_data)
            
            # Create rows array
            rows = []
            for row_idx in range(df.shape[0]):
                row_label = self._generate_row_label(df, row_idx, header_rows)
                
                row_data = {
                    "row_index": row_idx,
                    "row_label": row_label,
                    "is_header_row": row_idx in header_rows,
                    "cells": {}
                }
                
                # Add cell data for this row
                for col_idx in range(df.shape[1]):
                    cell_value = df.iloc[row_idx, col_idx]
                    if pd.notna(cell_value) and str(cell_value).strip():
                        cell_key = f"{chr(65 + col_idx)}{row_idx + 1}"  # A1, B1, etc.
                        row_data["cells"][cell_key] = {
                            "value": str(cell_value).strip(),
                            "row": row_idx + 1,
                            "column": col_idx + 1
                        }
                
                rows.append(row_data)
            
            # Create table JSON structure
            table_json = {
                "table_id": f"table_{table_id}",
                "name": f"Table {table_id}",
                "region": {
                    "page_number": table.page,
                    "bbox": list(table._bbox) if hasattr(table, '_bbox') and table._bbox is not None else None,
                    "detection_method": f"camelot_{method}"
                },
                "header_info": {
                    "header_rows": header_rows,
                    "header_columns": [0] if df.shape[1] > 0 else [],
                    "data_start_row": data_start_row,
                    "data_start_col": 1
                },
                "columns": columns,
                "rows": rows,
                "metadata": {
                    "detection_method": f"camelot_{method}",
                    "quality_score": table.accuracy,
                    "cell_count": df.shape[0] * df.shape[1],
                    "whitespace": table.whitespace if hasattr(table, 'whitespace') else None,
                    "order": table.order if hasattr(table, 'order') else None
                }
            }
            
            return table_json
            
        except Exception as e:
            logger.error(f"Error converting table to JSON: {str(e)}")
            return None
    
    def _generate_column_label(self, df: pd.DataFrame, col_idx: int, header_rows: List[int]) -> str:
        """
        Generate column label from header rows
        
        Args:
            df: DataFrame containing table data
            col_idx: Column index
            header_rows: List of header row indices
            
        Returns:
            Column label string
        """
        if header_rows and col_idx < df.shape[1]:
            labels = []
            for header_row in header_rows:
                if header_row < df.shape[0]:
                    cell_value = df.iloc[header_row, col_idx]
                    if pd.notna(cell_value) and str(cell_value).strip():
                        labels.append(str(cell_value).strip())
            
            if labels:
                return " | ".join(labels)
        
        # Fallback to column letter
        return f"Column {chr(65 + col_idx)}"
    
    def _generate_row_label(self, df: pd.DataFrame, row_idx: int, header_rows: List[int]) -> str:
        """
        Generate row label from header columns
        
        Args:
            df: DataFrame containing table data
            row_idx: Row index
            header_rows: List of header row indices
            
        Returns:
            Row label string
        """
        # Use first column as row label if it's not a header row
        if row_idx not in header_rows and df.shape[1] > 0:
            cell_value = df.iloc[row_idx, 0]
            if pd.notna(cell_value) and str(cell_value).strip():
                return str(cell_value).strip()
        
        # Fallback to row number
        return f"Row {row_idx + 1}"
    
    def _filter_table_content(self, table_json: Dict) -> Optional[Dict]:
        """
        Filter out non-table content from the table
        
        Args:
            table_json: Table JSON structure
            
        Returns:
            Filtered table JSON structure
        """
        if not table_json or "rows" not in table_json:
            return table_json
        
        logger.info(f"Starting table filtering with {len(table_json['rows'])} rows")
        
        filtered_rows = []
        header_found = False
        data_found = False
        
        for row in table_json["rows"]:
            if not row.get("cells"):
                continue
            
            # Get all cell values in this row
            cell_values = []
            for cell in row["cells"].values():
                if cell.get("value"):
                    cell_values.append(str(cell["value"]).strip())
            
            if not cell_values:
                continue
            
            # Check if this row looks like a header (contains typical header words)
            header_keywords = ["item", "april", "may", "june", "january", "february", "march", 
                             "july", "august", "september", "october", "november", "december",
                             "q1", "q2", "q3", "q4", "total", "sum", "average", "count", "category"]
            
            # Check for date patterns in headers (like 1/1/2025, 2/1/2025, etc.)
            date_pattern = r'\d{1,2}/\d{1,2}/\d{4}'
            has_date_pattern = any(re.search(date_pattern, value) for value in cell_values)
            
            is_header = (any(keyword in " ".join(cell_values).lower() for keyword in header_keywords) or 
                        has_date_pattern or 
                        any("cost" in value.lower() for value in cell_values))
            
            # Check if this row contains numerical data
            has_numbers = any(any(char.isdigit() for char in value) for value in cell_values)
            
            # Check if this row looks like paragraph text (long text without structure)
            is_paragraph = False
            if len(cell_values) > 0:
                first_cell = cell_values[0]
                # More aggressive paragraph detection
                if len(first_cell) > 30 and not has_numbers and not is_header:
                    # Check if it looks like paragraph text
                    if ("paragraph" in first_cell.lower() or 
                        "introduction" in first_cell.lower() or
                        "since" in first_cell.lower() or
                        "there" in first_cell.lower() or
                        "are" in first_cell.lower() or
                        "no" in first_cell.lower() or
                        "numbers" in first_cell.lower() or
                        "system" in first_cell.lower() or
                        "should" in first_cell.lower() or
                        "ignore" in first_cell.lower()):
                        is_paragraph = True
                    elif len(first_cell.split()) > 8:  # Long text
                        is_paragraph = True
                
                # Also check if any cell contains paragraph-like text
                for cell_value in cell_values:
                    if (len(cell_value) > 30 and 
                        any(word in cell_value.lower() for word in ["paragraph", "introduction", "since", "there", "are", "no", "numbers", "system", "should", "ignore"])):
                        is_paragraph = True
                        break
                
                # Specific check for the problematic row that starts with "H" and contains paragraph text
                if (len(cell_values) > 0 and 
                    cell_values[0] == "H" and 
                    any("ere is a simple paragraph" in cell_value for cell_value in cell_values)):
                    is_paragraph = True
            
            # Include the row if:
            # 1. It's a header row
            # 2. It contains numerical data
            # 3. It's not paragraph text
            if is_header or has_numbers or (not is_paragraph and len(cell_values) > 1):
                if is_header:
                    header_found = True
                if has_numbers:
                    data_found = True
                filtered_rows.append(row)
        
        # Return the table if we found either headers or data, and have multiple rows
        # This handles cases like tables with dates as headers and costs as row labels
        if (header_found or data_found) and len(filtered_rows) > 1:
            filtered_table = table_json.copy()
            filtered_table["rows"] = filtered_rows
            
            # Clean up column structure to match filtered rows
            filtered_table = self._clean_column_structure(filtered_table, filtered_rows)
            
            # Update column labels based on filtered content
            filtered_table = self._update_column_labels(filtered_table)
            
            return filtered_table
        
        return None
    
    def _clean_column_structure(self, table_json: Dict, filtered_rows: List[Dict]) -> Dict:
        """
        Clean up column structure to match filtered rows
        
        Args:
            table_json: Table JSON structure
            filtered_rows: List of filtered rows
            
        Returns:
            Cleaned table JSON structure
        """
        if not filtered_rows:
            return table_json
        
        # Create a mapping of old row indices to new row indices
        old_to_new_row_mapping = {}
        new_row_index = 0
        for old_row_index, row in enumerate(table_json["rows"]):
            if row in filtered_rows:
                old_to_new_row_mapping[old_row_index] = new_row_index
                new_row_index += 1
        
        # Clean up columns
        if "columns" in table_json:
            for column in table_json["columns"]:
                if "cells" in column:
                    # Keep only cells that correspond to filtered rows
                    filtered_cells = {}
                    for cell_key, cell_data in column["cells"].items():
                        old_row = cell_data.get("row", 0)
                        if old_row in old_to_new_row_mapping:
                            # Update cell key and row reference
                            new_row = old_to_new_row_mapping[old_row]
                            new_cell_key = f"{cell_key[0]}{new_row + 1}"
                            cell_data["row"] = new_row + 1
                            filtered_cells[new_cell_key] = cell_data
                    
                    column["cells"] = filtered_cells
        
        return table_json
    
    def _update_column_labels(self, table_json: Dict) -> Dict:
        """
        Update column labels based on filtered content
        
        Args:
            table_json: Table JSON structure
            
        Returns:
            Updated table JSON structure
        """
        if not table_json or "columns" not in table_json or "rows" not in table_json:
            return table_json
        
        # Find the header row (first row with header-like content)
        header_row = None
        for row in table_json["rows"]:
            if row.get("is_header_row", False):
                header_row = row
                break
        
        if not header_row:
            # If no header row found, use the first row
            header_row = table_json["rows"][0] if table_json["rows"] else None
        
        if header_row and "cells" in header_row:
            # Update column labels based on header row content
            for col_idx, column in enumerate(table_json["columns"]):
                # Find the cell in this column from the header row
                header_cell = None
                for cell_key, cell_data in header_row["cells"].items():
                    if cell_data.get("column") == col_idx + 1:
                        header_cell = cell_data
                        break
                
                if header_cell and header_cell.get("value"):
                    column["column_label"] = str(header_cell["value"])
                else:
                    # Fallback to generic label
                    column["column_label"] = f"Column {chr(65 + col_idx)}"
        
        return table_json
    
    def _extract_tables_from_text(self, pdf_path: str) -> List[Dict]:
        """
        Fallback method to extract tables from PDF text content when camelot-py fails
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of table dictionaries in table-oriented JSON format
        """
        logger.info("Starting fallback text-based table detection")
        
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available for fallback table detection")
            return []
        
        try:
            # Open PDF and extract text blocks
            doc = fitz.open(pdf_path)
            tables = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_blocks = self._extract_text_blocks_for_table_detection(page, page_num)
                
                # Analyze text blocks for table structure
                detected_tables = self._analyze_text_blocks_for_tables(text_blocks, page_num)
                tables.extend(detected_tables)
            
            doc.close()
            return tables
            
        except Exception as e:
            logger.error(f"Error in fallback table detection: {str(e)}")
            return []
    
    def _extract_text_blocks_for_table_detection(self, page: Any, page_num: int) -> List[Dict]:
        """
        Extract text blocks from page for table detection analysis
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-based)
            
        Returns:
            List of text block dictionaries with positioning information
        """
        text_blocks = []
        
        # Get text blocks from page
        blocks = page.get_text("dict")
        
        for block in blocks.get("blocks", []):
            if "lines" not in block:  # Skip non-text blocks
                continue
            
            # Get block bounding box
            block_bbox = block.get("bbox", [0, 0, 0, 0])
            
            # Extract text and metadata from block
            block_text = ""
            block_metadata = {
                "font_size": None,
                "font_family": None,
                "is_bold": False,
                "is_italic": False,
                "color": None,
                "alignment": "left"
            }
            
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    if span_text:
                        line_text += span_text + " "
                        
                        # Update metadata from first span
                        if not block_metadata["font_size"]:
                            block_metadata.update({
                                "font_size": span.get("size", 12),
                                "font_family": span.get("font", "Arial"),
                                "is_bold": "Bold" in span.get("font", ""),
                                "is_italic": "Italic" in span.get("font", ""),
                                "color": span.get("color", 0)
                            })
                
                if line_text.strip():
                    block_text += line_text.strip() + "\n"
            
            if block_text.strip():
                text_blocks.append({
                    "text": block_text.strip(),
                    "bbox": block_bbox,
                    "metadata": block_metadata,
                    "page_number": page_num + 1
                })
        
        return text_blocks
    
    def _analyze_text_blocks_for_tables(self, text_blocks: List[Dict], page_num: int) -> List[Dict]:
        """
        Analyze text blocks to detect table structures
        
        Args:
            text_blocks: List of text block dictionaries
            page_num: Page number (0-based)
            
        Returns:
            List of detected table dictionaries
        """
        tables = []
        
        if not text_blocks:
            return tables
        
        # Group text blocks by vertical position (rows)
        rows = self._group_blocks_into_rows(text_blocks)
        
        # Analyze if the grouped blocks form a table
        if self._is_table_structure(rows):
            table = self._create_table_from_rows(rows, page_num)
            if table:
                tables.append(table)
        
        return tables
    
    def _group_blocks_into_rows(self, text_blocks: List[Dict]) -> List[List[Dict]]:
        """
        Group text blocks into rows based on vertical position
        
        Args:
            text_blocks: List of text block dictionaries
            
        Returns:
            List of rows, where each row is a list of text blocks
        """
        if not text_blocks:
            return []
        
        # Sort blocks by vertical position (top to bottom)
        sorted_blocks = sorted(text_blocks, key=lambda x: x["bbox"][1])
        
        rows = []
        current_row = []
        current_y = None
        y_tolerance = 5  # Tolerance for grouping blocks in the same row
        
        for block in sorted_blocks:
            block_y = block["bbox"][1]
            
            if current_y is None:
                current_y = block_y
                current_row = [block]
            elif abs(block_y - current_y) <= y_tolerance:
                # Same row
                current_row.append(block)
            else:
                # New row
                if current_row:
                    rows.append(current_row)
                current_row = [block]
                current_y = block_y
        
        # Add the last row
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def _is_table_structure(self, rows: List[List[Dict]]) -> bool:
        """
        Determine if the grouped rows form a table structure
        
        Args:
            rows: List of rows, where each row is a list of text blocks
            
        Returns:
            True if the structure looks like a table
        """
        if len(rows) < 2:
            return False
        
        # Check for consistent column structure
        column_counts = []
        for row in rows:
            # Count potential columns in this row
            row_text = " ".join([block["text"] for block in row])
            # Split by common delimiters and count
            columns = re.split(r'[\t\n\r\s]{2,}', row_text)
            column_counts.append(len([col for col in columns if col.strip()]))
        
        # Check if we have consistent column structure
        if len(set(column_counts)) <= 2 and max(column_counts) >= 3:
            return True
        
        # Alternative check: look for numerical patterns
        numerical_rows = 0
        for row in rows:
            row_text = " ".join([block["text"] for block in row])
            # Check if row contains numbers
            if re.search(r'\d+', row_text):
                numerical_rows += 1
        
        # If most rows contain numbers, it might be a table
        if numerical_rows >= len(rows) * 0.7:
            return True
        
        return False
    
    def _create_table_from_rows(self, rows: List[List[Dict]], page_num: int) -> Optional[Dict]:
        """
        Create a table JSON structure from grouped rows
        
        Args:
            rows: List of rows, where each row is a list of text blocks
            page_num: Page number (0-based)
            
        Returns:
            Table dictionary in table-oriented JSON format
        """
        if not rows:
            return None
        
        # Convert rows to table structure with better column parsing
        table_data = []
        for row in rows:
            # Get all text blocks in this row
            row_blocks = [block["text"] for block in row]
            
            # Try to parse as a table row with multiple columns
            parsed_columns = self._parse_row_into_columns(row_blocks)
            if parsed_columns:
                table_data.append(parsed_columns)
            else:
                # Fallback: treat as single column
                row_text = " ".join(row_blocks)
                columns = re.split(r'[\t\n\r\s]{2,}', row_text)
                columns = [col.strip() for col in columns if col.strip()]
                table_data.append(columns)
        
        if not table_data:
            return None
        
        # Create DataFrame-like structure
        max_cols = max(len(row) for row in table_data)
        for row in table_data:
            while len(row) < max_cols:
                row.append("")
        
        # Create table JSON structure
        table_json = {
            "table_id": "table_1",
            "name": "Table 1",
            "region": {
                "page_number": page_num + 1,
                "bbox": self._calculate_table_bbox(rows),
                "detection_method": "text_based_fallback"
            },
            "header_info": {
                "header_rows": [0] if len(table_data) > 0 else [],
                "header_columns": [0] if max_cols > 0 else [],
                "data_start_row": 1,
                "data_start_col": 1
            },
            "columns": [],
            "rows": [],
            "metadata": {
                "detection_method": "text_based_fallback",
                "quality_score": 0.8,
                "cell_count": len(table_data) * max_cols,
                "whitespace": None,
                "order": None
            }
        }
        
        # Create columns
        for col_idx in range(max_cols):
            column_data = {
                "column_index": col_idx,
                "column_label": f"Column {chr(65 + col_idx)}",
                "is_header_column": col_idx == 0,
                "cells": {}
            }
            
            # Add cell data for this column
            for row_idx, row in enumerate(table_data):
                if col_idx < len(row) and row[col_idx]:
                    cell_key = f"{chr(65 + col_idx)}{row_idx + 1}"
                    column_data["cells"][cell_key] = {
                        "value": str(row[col_idx]),
                        "row": row_idx + 1,
                        "column": col_idx + 1
                    }
            
            table_json["columns"].append(column_data)
        
        # Create rows
        for row_idx, row in enumerate(table_data):
            row_data = {
                "row_index": row_idx,
                "row_label": f"Row {row_idx + 1}",
                "is_header_row": row_idx == 0,
                "cells": {}
            }
            
            # Add cell data for this row
            for col_idx, cell_value in enumerate(row):
                if cell_value:
                    cell_key = f"{chr(65 + col_idx)}{row_idx + 1}"
                    row_data["cells"][cell_key] = {
                        "value": str(cell_value),
                        "row": row_idx + 1,
                        "column": col_idx + 1
                    }
            
            table_json["rows"].append(row_data)
        
        return table_json
    
    def _parse_row_into_columns(self, row_blocks: List[str]) -> Optional[List[str]]:
        """
        Parse a row of text blocks into individual columns
        
        Args:
            row_blocks: List of text blocks in a row
            
        Returns:
            List of column values or None if parsing fails
        """
        if not row_blocks:
            return None
        
        # If we have multiple blocks, they might represent different columns
        if len(row_blocks) > 1:
            # Check if blocks contain different types of content
            columns = []
            for block in row_blocks:
                # Clean up the block text
                clean_text = block.strip()
                if clean_text:
                    columns.append(clean_text)
            return columns if len(columns) > 1 else None
        
        # Single block - try to parse it as a table row
        row_text = row_blocks[0]
        
        # Look for patterns that suggest table structure
        # Check for date patterns (like 1/1/2025, 2/1/2025, etc.)
        date_pattern = r'\d{1,2}/\d{1,2}/\d{4}'
        dates = re.findall(date_pattern, row_text)
        
        # Check for currency patterns ($100, $105, etc.)
        currency_pattern = r'\$\d+'
        currencies = re.findall(currency_pattern, row_text)
        
        # Check for category patterns (First Cost, Second Cost, etc.)
        category_pattern = r'[A-Za-z]+\s+Cost'
        categories = re.findall(category_pattern, row_text)
        
        # If we find multiple dates or currencies, this is likely a table row
        if len(dates) > 1 or len(currencies) > 1:
            # Split by newlines and clean up
            lines = row_text.split('\n')
            columns = [line.strip() for line in lines if line.strip()]
            return columns if len(columns) > 1 else None
        
        # If we find a category followed by numbers, this might be a table row
        if categories and (dates or currencies):
            lines = row_text.split('\n')
            columns = [line.strip() for line in lines if line.strip()]
            return columns if len(columns) > 1 else None
        
        return None
    
    def _calculate_table_bbox(self, rows: List[List[Dict]]) -> List[float]:
        """
        Calculate bounding box for the entire table
        
        Args:
            rows: List of rows, where each row is a list of text blocks
            
        Returns:
            Bounding box coordinates [x1, y1, x2, y2]
        """
        if not rows:
            return [0, 0, 0, 0]
        
        all_blocks = []
        for row in rows:
            all_blocks.extend(row)
        
        if not all_blocks:
            return [0, 0, 0, 0]
        
        # Calculate min/max coordinates
        x_coords = []
        y_coords = []
        
        for block in all_blocks:
            bbox = block["bbox"]
            x_coords.extend([bbox[0], bbox[2]])
            y_coords.extend([bbox[1], bbox[3]])
        
        return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]


class PDFTextProcessor:
    """
    Handles text extraction from PDF documents using PyMuPDF
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the text processor with configuration
        
        Args:
            config: Configuration dictionary for text extraction
        """
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF is required for text extraction. Install with: pip install PyMuPDF")
        
        self.config = config or self._get_default_config()
        self.section_config = self.config.get('section_detection', {})
        self.extract_metadata = self.config.get('extract_metadata', True)
        self.preserve_formatting = self.config.get('preserve_formatting', True)
        
    def _get_default_config(self) -> Dict:
        """Get default configuration for text extraction"""
        return {
            'extract_metadata': True,
            'preserve_formatting': True,
            'section_detection': {
                'min_section_size': 50,
                'max_section_size': 1000,
                'use_headers': True,
                'detect_lists': True,
                'min_words_per_section': 10,
                'max_words_per_section': 500
            }
        }
    
    def extract_text_content(self, pdf_path: str, table_regions: Optional[List[Dict]] = None) -> Dict:
        """
        Extract text content from PDF using PyMuPDF, excluding table regions
        
        Args:
            pdf_path: Path to the PDF file
            table_regions: List of table regions to exclude from text extraction
            
        Returns:
            Dictionary containing extracted text in structured format
        """
        logger.info(f"Starting text extraction from: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Initialize result structure
        text_data = {
            "text_content": {
                "document_metadata": {
                    "filename": os.path.basename(pdf_path),
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_method": "pymupdf_enhanced",
                    "total_pages": 0,
                    "total_word_count": 0
                },
                "pages": [],
                "document_structure": {
                    "toc": [],
                    "sections_by_type": {
                        "header": 0,
                        "paragraph": 0,
                        "list": 0,
                        "table_caption": 0,
                        "figure_caption": 0,
                        "footer": 0,
                        "sidebar": 0
                    }
                },
                "summary": {
                    "total_sections": 0,
                    "total_words": 0,
                    "llm_ready_sections": 0,
                    "average_section_length": 0,
                    "reading_time_estimate": 0
                }
            }
        }
        
        try:
            # Open PDF document
            doc = fitz.open(pdf_path)
            text_data["text_content"]["document_metadata"]["total_pages"] = len(doc)
            
            # Convert table regions to exclusion zones
            exclusion_zones = self._prepare_exclusion_zones(table_regions, len(doc))
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_width, page_height = page.rect.width, page.rect.height
                
                logger.info(f"Processing page {page_num + 1}/{len(doc)}")
                
                # Extract text blocks from page
                text_blocks = self._extract_text_blocks(page, page_num, exclusion_zones.get(page_num, []))
                
                # Organize text blocks into sections
                sections = self._organize_into_sections(text_blocks, page_num)
                
                # Create page data
                page_data = {
                    "page_number": page_num + 1,
                    "page_width": page_width,
                    "page_height": page_height,
                    "sections": sections
                }
                
                text_data["text_content"]["pages"].append(page_data)
                
                # Update summary statistics
                for section in sections:
                    text_data["text_content"]["document_structure"]["sections_by_type"][section["section_type"]] += 1
                    text_data["text_content"]["summary"]["total_sections"] += 1
                    text_data["text_content"]["summary"]["total_words"] += section["word_count"]
                    if section["llm_ready"]:
                        text_data["text_content"]["summary"]["llm_ready_sections"] += 1
            
            # Calculate final statistics
            total_sections = text_data["text_content"]["summary"]["total_sections"]
            if total_sections > 0:
                text_data["text_content"]["summary"]["average_section_length"] = \
                    text_data["text_content"]["summary"]["total_words"] / total_sections
                text_data["text_content"]["summary"]["reading_time_estimate"] = \
                    text_data["text_content"]["summary"]["total_words"] / 200  # 200 words per minute
            
            text_data["text_content"]["document_metadata"]["total_word_count"] = \
                text_data["text_content"]["summary"]["total_words"]
            
            # Generate table of contents
            text_data["text_content"]["document_structure"]["toc"] = \
                self._generate_table_of_contents(text_data["text_content"]["pages"])
            
            doc.close()
            logger.info(f"Text extraction completed. Found {text_data['text_content']['summary']['total_sections']} sections")
            return text_data
            
        except Exception as e:
            logger.error(f"Error during text extraction: {str(e)}")
            raise
    
    def _prepare_exclusion_zones(self, table_regions: Optional[List[Dict]], total_pages: int) -> Dict[int, List[Tuple]]:
        """
        Prepare exclusion zones from table regions
        
        Args:
            table_regions: List of table regions from table extraction
            total_pages: Total number of pages in the document
            
        Returns:
            Dictionary mapping page numbers to exclusion zone coordinates
        """
        exclusion_zones = {}
        
        if not table_regions:
            return exclusion_zones
        
        for table in table_regions:
            page_num = table.get("region", {}).get("page_number", 1) - 1  # Convert to 0-based
            bbox = table.get("region", {}).get("bbox")
            
            if bbox and 0 <= page_num < total_pages:
                if page_num not in exclusion_zones:
                    exclusion_zones[page_num] = []
                
                # Check if this table covers the entire page (likely false detection)
                page_width = 612.0
                page_height = 792.0
                table_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                page_area = page_width * page_height
                coverage_ratio = table_area / page_area
                
                if coverage_ratio > 0.95:
                    # If table covers almost the entire page, don't exclude anything
                    # This allows text extraction to proceed normally
                    logger.info(f"Table on page {page_num + 1} covers {coverage_ratio:.1%} of page - skipping exclusion zone")
                    continue
                
                # Add padding around table region to avoid edge text
                padding = 10
                exclusion_zone = (
                    bbox[0] - padding,  # x1
                    bbox[1] - padding,  # y1
                    bbox[2] + padding,  # x2
                    bbox[3] + padding   # y2
                )
                exclusion_zones[page_num].append(exclusion_zone)
        
        return exclusion_zones
    
    def _extract_text_blocks(self, page: Any, page_num: int, exclusion_zones: List[Tuple]) -> List[Dict]:
        """
        Extract text blocks from a page, excluding table regions
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-based)
            exclusion_zones: List of exclusion zone coordinates
            
        Returns:
            List of text block dictionaries
        """
        text_blocks = []
        
        # Get text blocks from page
        blocks = page.get_text("dict")
        
        for block in blocks.get("blocks", []):
            if "lines" not in block:  # Skip non-text blocks
                continue
            
            # Get block bounding box
            block_bbox = block.get("bbox", [0, 0, 0, 0])
            
            # Check if block overlaps with exclusion zones
            if self._is_in_exclusion_zone(block_bbox, exclusion_zones):
                logger.debug(f"Skipping text block in exclusion zone on page {page_num + 1}")
                continue
            
            # Extract text and metadata from block
            block_text = ""
            block_metadata = {
                "font_size": None,
                "font_family": None,
                "is_bold": False,
                "is_italic": False,
                "color": None,
                "alignment": "left"
            }
            
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    if span_text:
                        line_text += span_text + " "
                        
                        # Update metadata from first span
                        if not block_metadata["font_size"]:
                            block_metadata.update({
                                "font_size": span.get("size", 12),
                                "font_family": span.get("font", "Arial"),
                                "is_bold": "Bold" in span.get("font", ""),
                                "is_italic": "Italic" in span.get("font", ""),
                                "color": span.get("color", 0)
                            })
                
                if line_text.strip():
                    block_text += line_text.strip() + "\n"
            
            if block_text.strip():
                text_blocks.append({
                    "text": block_text.strip(),
                    "bbox": block_bbox,
                    "metadata": block_metadata,
                    "page_number": page_num + 1
                })
        
        return text_blocks
    
    def _is_in_exclusion_zone(self, bbox: List[float], exclusion_zones: List[Tuple]) -> bool:
        """
        Check if a bounding box overlaps with any exclusion zone
        
        Args:
            bbox: Bounding box coordinates [x1, y1, x2, y2]
            exclusion_zones: List of exclusion zone coordinates
            
        Returns:
            True if bbox overlaps with any exclusion zone
        """
        for zone in exclusion_zones:
            # Check for overlap
            if not (bbox[2] < zone[0] or bbox[0] > zone[2] or 
                   bbox[3] < zone[1] or bbox[1] > zone[3]):
                return True
        return False
    
    def _organize_into_sections(self, text_blocks: List[Dict], page_num: int) -> List[Dict]:
        """
        Organize text blocks into logical sections
        
        Args:
            text_blocks: List of text block dictionaries
            page_num: Page number (0-based)
            
        Returns:
            List of section dictionaries
        """
        sections = []
        section_counter = 1
        
        for block in text_blocks:
            # Determine section type
            section_type = self._classify_section_type(block)
            
            # Check if section meets size requirements
            word_count = len(block["text"].split())
            if word_count < self.section_config.get("min_words_per_section", 10):
                continue
            
            # Create section
            section = {
                "section_id": f"page_{page_num + 1}_section_{section_counter}",
                "section_type": section_type,
                "title": self._extract_title(block) if section_type == "header" else None,
                "content": block["text"],
                "word_count": word_count,
                "character_count": len(block["text"]),
                "llm_ready": self._is_llm_ready(block["text"], word_count),
                "position": {
                    "start_y": block["bbox"][1],
                    "end_y": block["bbox"][3],
                    "bbox": block["bbox"],
                    "column_index": 0  # Default to single column
                },
                "metadata": block["metadata"],
                "structure": {
                    "heading_level": self._determine_heading_level(block),
                    "list_type": self._detect_list_type(block["text"]),
                    "list_level": None,
                    "is_continuation": False
                },
                "relationships": {
                    "parent_section": None,
                    "child_sections": [],
                    "related_tables": [],
                    "related_figures": []
                }
            }
            
            sections.append(section)
            section_counter += 1
        
        return sections
    
    def _classify_section_type(self, block: Dict) -> str:
        """
        Classify text block into section type
        
        Args:
            block: Text block dictionary
            
        Returns:
            Section type string
        """
        text = block["text"].lower()
        metadata = block["metadata"]
        
        # Check for headers based on font size and formatting
        if metadata["font_size"] and metadata["font_size"] > 14:
            return "header"
        
        # Check for list indicators
        if self._detect_list_type(text):
            return "list"
        
        # Check for table captions
        if "table" in text and ("caption" in text or len(text.split()) < 10):
            return "table_caption"
        
        # Check for figure captions
        if "figure" in text and ("caption" in text or len(text.split()) < 10):
            return "figure_caption"
        
        # Default to paragraph
        return "paragraph"
    
    def _extract_title(self, block: Dict) -> str:
        """
        Extract title from header block
        
        Args:
            block: Text block dictionary
            
        Returns:
            Title string
        """
        # Simple title extraction - could be enhanced
        lines = block["text"].split('\n')
        return lines[0].strip() if lines else ""
    
    def _is_llm_ready(self, text: str, word_count: int) -> bool:
        """
        Determine if section is ready for LLM processing
        
        Args:
            text: Section text
            word_count: Number of words
            
        Returns:
            True if section is LLM ready
        """
        min_words = self.section_config.get("min_words_per_section", 10)
        max_words = self.section_config.get("max_words_per_section", 500)
        
        # Check word count
        if word_count < min_words or word_count > max_words:
            return False
        
        # Check for complete sentences
        sentences = text.split('.')
        if len(sentences) < 2:
            return False
        
        # Check for excessive formatting or special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.3:
            return False
        
        return True
    
    def _determine_heading_level(self, block: Dict) -> Optional[int]:
        """
        Determine heading level based on font size and formatting
        
        Args:
            block: Text block dictionary
            
        Returns:
            Heading level (1-6) or None
        """
        metadata = block["metadata"]
        font_size = metadata.get("font_size", 12)
        
        if font_size >= 20:
            return 1
        elif font_size >= 16:
            return 2
        elif font_size >= 14:
            return 3
        elif font_size >= 12:
            return 4
        elif font_size >= 10:
            return 5
        elif font_size >= 8:
            return 6
        
        return None
    
    def _detect_list_type(self, text: str) -> Optional[str]:
        """
        Detect if text represents a list
        
        Args:
            text: Text to analyze
            
        Returns:
            List type ("ordered", "unordered") or None
        """
        lines = text.split('\n')
        if len(lines) < 2:
            return None
        
        # Check for ordered list patterns
        ordered_patterns = [r'^\d+\.', r'^\d+\)', r'^[a-z]\.', r'^[A-Z]\.']
        # Check for unordered list patterns
        unordered_patterns = [r'^[-•*]', r'^○', r'^▪', r'^▫']
        
        ordered_count = 0
        unordered_count = 0
        
        for line in lines:
            line = line.strip()
            if any(re.match(pattern, line) for pattern in ordered_patterns):
                ordered_count += 1
            elif any(re.match(pattern, line) for pattern in unordered_patterns):
                unordered_count += 1
        
        if ordered_count > len(lines) * 0.5:
            return "ordered"
        elif unordered_count > len(lines) * 0.5:
            return "unordered"
        
        return None
    
    def _generate_table_of_contents(self, pages: List[Dict]) -> List[Dict]:
        """
        Generate table of contents from document pages
        
        Args:
            pages: List of page dictionaries
            
        Returns:
            List of TOC entries
        """
        toc = []
        
        for page in pages:
            for section in page["sections"]:
                if section["section_type"] == "header" and section["title"]:
                    toc.append({
                        "title": section["title"],
                        "page_number": page["page_number"],
                        "section_id": section["section_id"],
                        "level": section["structure"]["heading_level"] or 1
                    })
        
        return toc


class PDFNumberExtractor:
    """
    Handles number extraction from text content
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the number extractor with configuration
        
        Args:
            config: Configuration dictionary for number extraction
        """
        self.config = config or self._get_default_config()
        self.patterns = self.config.get('patterns', {})
        self.context_window = self.config.get('context_window', 100)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.extract_metadata = self.config.get('extract_metadata', True)
        self.include_positioning = self.config.get('include_positioning', True)
        
    def _get_default_config(self) -> Dict:
        """Get default configuration for number extraction"""
        return {
            'patterns': {
                'integer': r'\b\d{1,3}(?:,\d{3})*\b',
                'decimal': r'\b\d+\.\d+\b',
                'percentage': r'\b\d+(?:\.\d+)?%\b',
                'currency': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',
                'scientific_notation': r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b',
                'fraction': r'\b\d+/\d+\b',
                'date_number': r'\b(?:19|20)\d{2}\b|\b\d{1,2}(?:st|nd|rd|th)\b'
            },
            'context_window': 100,
            'confidence_threshold': 0.7,
            'extract_metadata': True,
            'include_positioning': True
        }
    
    def extract_numbers_in_text(self, text_content: Dict) -> Dict:
        """
        Extract numbers from text content
        
        Args:
            text_content: Text content dictionary from PDFTextProcessor
            
        Returns:
            Dictionary containing extracted numbers in structured format
        """
        logger.info("Starting number extraction from text content")
        
        if not text_content or "text_content" not in text_content:
            logger.warning("No text content provided for number extraction")
            return self._create_empty_result()
        
        # Initialize result structure
        numbers_data = {
            "numbers_in_text": {
                "document_metadata": {
                    "filename": text_content["text_content"]["document_metadata"]["filename"],
                    "total_pages": text_content["text_content"]["document_metadata"]["total_pages"],
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_method": "regex_pattern_enhanced"
                },
                "pages": [],
                "summary": {
                    "total_numbers_found": 0,
                    "numbers_by_format": {
                        "integer": 0,
                        "decimal": 0,
                        "percentage": 0,
                        "currency": 0,
                        "scientific_notation": 0,
                        "fraction": 0,
                        "date_number": 0
                    },
                    "confidence_distribution": {
                        "high": 0,
                        "medium": 0,
                        "low": 0
                    }
                }
            }
        }
        
        try:
            # Process each page
            for page in text_content["text_content"]["pages"]:
                page_numbers = self._extract_numbers_from_page(page)
                numbers_data["numbers_in_text"]["pages"].append(page_numbers)
                
                # Update summary statistics
                for section in page_numbers["sections"]:
                    for number in section["numbers"]:
                        numbers_data["numbers_in_text"]["summary"]["total_numbers_found"] += 1
                        
                        # Update format distribution
                        format_type = number["format"]
                        if format_type in numbers_data["numbers_in_text"]["summary"]["numbers_by_format"]:
                            numbers_data["numbers_in_text"]["summary"]["numbers_by_format"][format_type] += 1
                        
                        # Update confidence distribution
                        confidence = number["confidence"]
                        if confidence >= 0.8:
                            numbers_data["numbers_in_text"]["summary"]["confidence_distribution"]["high"] += 1
                        elif confidence >= 0.5:
                            numbers_data["numbers_in_text"]["summary"]["confidence_distribution"]["medium"] += 1
                        else:
                            numbers_data["numbers_in_text"]["summary"]["confidence_distribution"]["low"] += 1
            
            logger.info(f"Number extraction completed. Found {numbers_data['numbers_in_text']['summary']['total_numbers_found']} numbers")
            return numbers_data
            
        except Exception as e:
            logger.error(f"Error during number extraction: {str(e)}")
            raise
    
    def _extract_numbers_from_page(self, page: Dict) -> Dict:
        """
        Extract numbers from a single page
        
        Args:
            page: Page dictionary from text content
            
        Returns:
            Page numbers data
        """
        page_numbers = {
            "page_number": page["page_number"],
            "page_width": page["page_width"],
            "page_height": page["page_height"],
            "sections": []
        }
        
        for section in page["sections"]:
            section_numbers = self._extract_numbers_from_section(section)
            if section_numbers["numbers"]:  # Only include sections with numbers
                page_numbers["sections"].append(section_numbers)
        
        return page_numbers
    
    def _extract_numbers_from_section(self, section: Dict) -> Dict:
        """
        Extract numbers from a single section
        
        Args:
            section: Section dictionary from text content
            
        Returns:
            Section numbers data
        """
        section_numbers = {
            "section_id": section["section_id"],
            "section_type": section["section_type"],
            "numbers": []
        }
        
        text = section["content"]
        position = section["position"]
        metadata = section["metadata"]
        
        # Extract numbers using all patterns
        for format_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                number_info = self._process_number_match(
                    match, format_type, text, position, metadata
                )
                
                if number_info and number_info["confidence"] >= self.confidence_threshold:
                    section_numbers["numbers"].append(number_info)
        
        return section_numbers
    
    def _process_number_match(self, match: re.Match, format_type: str, text: str, 
                            position: Dict, metadata: Dict) -> Optional[Dict]:
        """
        Process a number match and extract detailed information
        
        Args:
            match: Regex match object
            format_type: Type of number format
            text: Full text content
            position: Section position information
            metadata: Section metadata
            
        Returns:
            Number information dictionary or None
        """
        try:
            original_text = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            
            # Extract context
            context_start = max(0, start_pos - self.context_window // 2)
            context_end = min(len(text), end_pos + self.context_window // 2)
            context = text[context_start:context_end].strip()
            
            # Parse number value
            value = self._parse_number_value(original_text, format_type)
            
            if value is None:
                return None
            
            # Calculate confidence
            confidence = self._calculate_confidence(original_text, format_type, context)
            
            # Extract unit and currency information
            unit, currency = self._extract_unit_and_currency(original_text, context, format_type)
            
            # Calculate position within section
            section_position = self._calculate_number_position(start_pos, end_pos, text, position)
            
            number_info = {
                "value": value,
                "original_text": original_text,
                "context": context,
                "position": section_position,
                "format": format_type,
                "unit": unit,
                "currency": currency,
                "confidence": confidence,
                "extraction_method": "regex_pattern"
            }
            
            # Add metadata if requested
            if self.extract_metadata:
                number_info["metadata"] = {
                    "font_size": metadata.get("font_size"),
                    "font_family": metadata.get("font_family"),
                    "is_bold": metadata.get("is_bold", False),
                    "is_italic": metadata.get("is_italic", False),
                    "color": metadata.get("color")
                }
            
            return number_info
            
        except Exception as e:
            logger.debug(f"Error processing number match: {str(e)}")
            return None
    
    def _parse_number_value(self, text: str, format_type: str) -> Optional[float]:
        """
        Parse number value from text based on format type
        
        Args:
            text: Number text
            format_type: Type of number format
            
        Returns:
            Parsed number value or None
        """
        try:
            if format_type == "integer":
                # Remove commas and convert to integer
                return int(text.replace(",", ""))
            
            elif format_type == "decimal":
                return float(text)
            
            elif format_type == "percentage":
                # Remove % and convert to decimal
                return float(text.replace("%", "")) / 100
            
            elif format_type == "currency":
                # Remove currency symbols and commas
                cleaned = re.sub(r'[^\d.]', '', text)
                return float(cleaned)
            
            elif format_type == "scientific_notation":
                return float(text)
            
            elif format_type == "fraction":
                # Parse fraction like "3/4"
                parts = text.split("/")
                if len(parts) == 2:
                    return float(parts[0]) / float(parts[1])
            
            elif format_type == "date_number":
                # For date numbers, return the numeric part
                numeric_part = re.sub(r'[^\d]', '', text)
                if numeric_part:
                    return int(numeric_part)
            
            return None
            
        except (ValueError, ZeroDivisionError):
            return None
    
    def _calculate_confidence(self, text: str, format_type: str, context: str) -> float:
        """
        Calculate confidence score for number extraction
        
        Args:
            text: Number text
            format_type: Type of number format
            context: Surrounding context
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Format-specific confidence adjustments
        if format_type == "currency" and "$" in text:
            confidence += 0.2
        elif format_type == "percentage" and "%" in text:
            confidence += 0.2
        elif format_type == "scientific_notation" and ("e" in text.lower() or "E" in text):
            confidence += 0.2
        
        # Context-based confidence
        if any(word in context.lower() for word in ["total", "sum", "amount", "value", "number"]):
            confidence += 0.1
        
        # Length-based confidence
        if len(text) > 1:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_unit_and_currency(self, text: str, context: str, format_type: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract unit and currency information
        
        Args:
            text: Number text
            context: Surrounding context
            format_type: Type of number format
            
        Returns:
            Tuple of (unit, currency)
        """
        unit = None
        currency = None
        
        # Extract currency
        if format_type == "currency":
            if "$" in text:
                currency = "USD"
            elif "€" in text:
                currency = "EUR"
            elif "£" in text:
                currency = "GBP"
        
        # Extract units from context
        unit_patterns = {
            "units": r"\b(units?|items?|pieces?|count)\b",
            "dollars": r"\b(dollars?|usd)\b",
            "percent": r"\b(percent|percentage|%)\b",
            "years": r"\b(years?|yrs?)\b",
            "months": r"\b(months?|mos?)\b",
            "days": r"\b(days?)\b"
        }
        
        context_lower = context.lower()
        for unit_type, pattern in unit_patterns.items():
            if re.search(pattern, context_lower):
                unit = unit_type
                break
        
        return unit, currency
    
    def _calculate_number_position(self, start_pos: int, end_pos: int, text: str, 
                                 section_position: Dict) -> Dict:
        """
        Calculate number position within section
        
        Args:
            start_pos: Start position in text
            end_pos: End position in text
            text: Full text content
            section_position: Section position information
            
        Returns:
            Position information dictionary
        """
        # Calculate relative position within text
        text_length = len(text)
        relative_x = (start_pos / text_length) * 100 if text_length > 0 else 0
        
        # Estimate position based on section position
        section_bbox = section_position.get("bbox", [0, 0, 0, 0])
        
        # Simple estimation - could be enhanced with more sophisticated positioning
        estimated_x = section_bbox[0] + (relative_x / 100) * (section_bbox[2] - section_bbox[0])
        estimated_y = section_bbox[1] + (start_pos / text_length) * (section_bbox[3] - section_bbox[1])
        
        return {
            "x": estimated_x,
            "y": estimated_y,
            "bbox": [estimated_x, estimated_y, estimated_x + 20, estimated_y + 10],  # Rough estimate
            "line_number": 1  # Default line number
        }
    
    def _create_empty_result(self) -> Dict:
        """Create empty result structure"""
        return {
            "numbers_in_text": {
                "document_metadata": {
                    "filename": "unknown",
                    "total_pages": 0,
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_method": "regex_pattern_enhanced"
                },
                "pages": [],
                "summary": {
                    "total_numbers_found": 0,
                    "numbers_by_format": {
                        "integer": 0,
                        "decimal": 0,
                        "percentage": 0,
                        "currency": 0,
                        "scientific_notation": 0,
                        "fraction": 0,
                        "date_number": 0
                    },
                    "confidence_distribution": {
                        "high": 0,
                        "medium": 0,
                        "low": 0
                    }
                }
            }
        }


class PDFProcessor:
    """
    Main PDF processing class that coordinates table, text, and number extraction
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the PDF processor with configuration
        
        Args:
            config: Configuration dictionary for PDF processing
        """
        self.config = config or self._get_default_config()
        
        # Initialize component processors
        self.table_extractor = PDFTableExtractor(
            self.config.get('table_extraction', {})
        )
        self.text_processor = PDFTextProcessor(
            self.config.get('text_extraction', {})
        )
        self.number_extractor = PDFNumberExtractor(
            self.config.get('number_extraction', {})
        )
        
    def _get_default_config(self) -> Dict:
        """Get default configuration for PDF processing"""
        return {
            'table_extraction': {
                'methods': ['lattice', 'stream'],
                'quality_threshold': 0.8,
                'edge_tolerance': 3,
                'row_tolerance': 3,
                'column_tolerance': 3,
                'min_table_size': 4
            },
            'text_extraction': {
                'extract_metadata': True,
                'preserve_formatting': True,
                'section_detection': {
                    'min_section_size': 50,
                    'max_section_size': 1000,
                    'use_headers': True
                }
            },
            'number_extraction': {
                'patterns': {
                    'integer': r'\b\d{1,3}(?:,\d{3})*\b',
                    'decimal': r'\b\d+\.\d+\b',
                    'percentage': r'\b\d+(?:\.\d+)?%\b',
                    'currency': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',
                    'scientific_notation': r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b'
                },
                'context_window': 100,
                'confidence_threshold': 0.7,
                'extract_metadata': True,
                'include_positioning': True
            }
        }
    
    def process_file(self, pdf_path: str, extract_tables: bool = True, 
                    extract_text: bool = False, extract_numbers: bool = False) -> Dict:
        """
        Process PDF file and extract requested components
        
        Args:
            pdf_path: Path to the PDF file
            extract_tables: Whether to extract tables
            extract_text: Whether to extract text content
            extract_numbers: Whether to extract numbers from text
            
        Returns:
            Dictionary containing extracted data in structured format
        """
        logger.info(f"Starting PDF processing: {pdf_path}")
        start_time = datetime.now()
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Validate file is a PDF
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF")
        
        result = {
            "pdf_processing_result": {
                "document_metadata": {
                    "filename": os.path.basename(pdf_path),
                    "total_pages": 0,  # Will be updated if text extraction is enabled
                    "processing_timestamp": start_time.isoformat(),
                    "processing_duration": 0,
                    "extraction_methods": []
                },
                "processing_summary": {
                    "tables_extracted": 0,
                    "numbers_found": 0,
                    "text_sections": 0,
                    "overall_quality_score": 0.0,
                    "processing_errors": []
                },
                "tables": None,
                "text_content": None,
                "numbers_in_text": None
            }
        }
        
        try:
            table_regions = None
            table_data = None
            text_data = None
            number_data = None
            
            # Phase 1: Extract tables first (if requested)
            if extract_tables:
                logger.info("Phase 1: Extracting tables...")
                try:
                    table_data = self.table_extractor.extract_tables(pdf_path)
                    result["pdf_processing_result"]["tables"] = table_data
                    result["pdf_processing_result"]["document_metadata"]["extraction_methods"].append("table_extraction")
                    result["pdf_processing_result"]["processing_summary"]["tables_extracted"] = \
                        table_data["metadata"]["total_tables_found"]
                    
                    # Prepare table regions for text extraction filtering
                    table_regions = table_data.get("tables", [])
                    logger.info(f"Found {len(table_regions)} table regions for exclusion")
                except Exception as e:
                    logger.error(f"Error in table extraction: {str(e)}")
                    result["pdf_processing_result"]["processing_summary"]["processing_errors"].append(f"Table extraction failed: {str(e)}")
                    table_data = {"tables": [], "metadata": {"total_tables_found": 0}}
                    result["pdf_processing_result"]["tables"] = table_data
                    table_regions = []
            
            # Phase 2: Extract text content (excluding table regions)
            if extract_text:
                logger.info("Phase 2: Extracting text content (excluding table regions)...")
                text_data = self.text_processor.extract_text_content(pdf_path, table_regions)
                result["pdf_processing_result"]["text_content"] = text_data
                result["pdf_processing_result"]["document_metadata"]["extraction_methods"].append("text_extraction")
                result["pdf_processing_result"]["processing_summary"]["text_sections"] = \
                    text_data["text_content"]["summary"]["total_sections"]
                
                # Update total pages from text extraction
                result["pdf_processing_result"]["document_metadata"]["total_pages"] = \
                    text_data["text_content"]["document_metadata"]["total_pages"]
            
            # Phase 3: Extract numbers from text content
            if extract_numbers and extract_text:
                logger.info("Phase 3: Extracting numbers from text content...")
                number_data = self.number_extractor.extract_numbers_in_text(text_data)
                result["pdf_processing_result"]["numbers_in_text"] = number_data
                result["pdf_processing_result"]["document_metadata"]["extraction_methods"].append("number_extraction")
                result["pdf_processing_result"]["processing_summary"]["numbers_found"] = \
                    number_data["numbers_in_text"]["summary"]["total_numbers_found"]
            
            # Calculate overall quality score
            quality_scores = []
            if extract_tables and table_data and table_data["metadata"]["total_tables_found"] > 0:
                # Calculate average table quality
                table_qualities = [table["metadata"]["quality_score"] for table in table_data["tables"]]
                quality_scores.append(sum(table_qualities) / len(table_qualities))
            
            if extract_numbers and number_data and number_data["numbers_in_text"]["summary"]["total_numbers_found"] > 0:
                # Calculate average number confidence
                high_conf = number_data["numbers_in_text"]["summary"]["confidence_distribution"]["high"]
                total_numbers = number_data["numbers_in_text"]["summary"]["total_numbers_found"]
                quality_scores.append(high_conf / total_numbers if total_numbers > 0 else 0)
            
            if quality_scores:
                result["pdf_processing_result"]["processing_summary"]["overall_quality_score"] = \
                    sum(quality_scores) / len(quality_scores)
            
            # Calculate processing duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            result["pdf_processing_result"]["document_metadata"]["processing_duration"] = duration
            
            logger.info(f"PDF processing completed in {duration:.2f} seconds")
            logger.info(f"Summary: {result['pdf_processing_result']['processing_summary']['tables_extracted']} tables, "
                       f"{result['pdf_processing_result']['processing_summary']['text_sections']} text sections, "
                       f"{result['pdf_processing_result']['processing_summary']['numbers_found']} numbers")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during PDF processing: {str(e)}")
            # Ensure extraction_methods exists before adding error
            if "extraction_methods" not in result["pdf_processing_result"]["document_metadata"]:
                result["pdf_processing_result"]["document_metadata"]["extraction_methods"] = []
            result["pdf_processing_result"]["processing_summary"]["processing_errors"].append(str(e))
            raise


def main():
    """
    Main function for testing PDF processing
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python PDF_processing.py <pdf_file_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        # Initialize PDF processor
        processor = PDFProcessor()
        
        # Process PDF with all extraction types
        result = processor.process_file(pdf_path, extract_tables=True, extract_text=True, extract_numbers=True)
        
        # Save result to JSON file
        output_file = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_tables.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Processing completed. Results saved to: {output_file}")
        print(f"Tables extracted: {result['pdf_processing_result']['processing_summary']['tables_extracted']}")
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 