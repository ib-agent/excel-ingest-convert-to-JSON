"""
PDFPlumber Table Extractor

This module provides table extraction capabilities using PDFPlumber library.
It replaces legacy extractors with improved accuracy and maintains
compatibility with existing JSON schemas.

Author: PDF Processing Team
Date: 2024
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import pdfplumber
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TableRegion:
    """Container for table region information"""
    page_number: int
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    table_data: List[List[str]]
    confidence: float
    
class PDFPlumberTableExtractor:
    """
    Table extraction using PDFPlumber with conversion to existing JSON schemas
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the PDFPlumber table extractor
        
        Args:
            config: Configuration dictionary for table extraction
        """
        self.config = config or self._get_default_config()
        self.table_settings = self.config.get('table_settings', {})
        self.quality_threshold = self.config.get('quality_threshold', 0.8)
        self.min_table_size = self.config.get('min_table_size', 2)
        self.max_tables_per_page = self.config.get('max_tables_per_page', 10)
        
        logger.info("PDFPlumberTableExtractor initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for PDFPlumber table extraction"""
        return {
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
            'text_settings': {
                'x_tolerance': 3,
                'y_tolerance': 3,
                'layout': True
            },
            'quality_threshold': 0.90,  # Increased from 0.8 to reduce false positives
            'min_table_size': 2,
            'max_tables_per_page': 10,
            'min_rows': 2,
            'min_cols': 2,
            'max_cols': 15,  # Reject tables with >15 columns (likely text parsing errors)
            'min_cell_content_ratio': 0.4,  # At least 40% of cells should have meaningful content
            'enable_spanning_detection': True  # Enable cross-page table merging
        }
    
    def extract_tables(self, pdf_path: str) -> Dict:
        """
        Extract tables from PDF using PDFPlumber
        
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
                "extraction_method": "pdfplumber",
                "total_tables_found": 0,
                "quality_distribution": {"high": 0, "medium": 0, "low": 0}
            }
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                table_counter = 1
                
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"Processing page {page_num + 1}/{len(pdf.pages)}")
                    
                    # Extract tables using multiple strategies
                    page_tables = self._extract_tables_from_page(page, page_num + 1)
                    
                    for table_region in page_tables:
                        if self._is_valid_table(table_region):
                            table_json = self._convert_to_schema(
                                table_region, table_counter
                            )
                            
                            if table_json:
                                tables_data["tables"].append(table_json)
                                self._update_quality_distribution(
                                    tables_data["metadata"]["quality_distribution"],
                                    table_region.confidence
                                )
                                logger.info(f"Added table {table_counter} from page {page_num + 1}")
                                table_counter += 1
                
                # Apply post-processing
                tables_data["tables"] = self._post_process_tables(tables_data["tables"])
                tables_data["metadata"]["total_tables_found"] = len(tables_data["tables"])
                
                logger.info(f"Table extraction completed. Found {len(tables_data['tables'])} tables")
                return tables_data
                
        except Exception as e:
            logger.error(f"Error during table extraction: {str(e)}")
            raise
    
    def _extract_tables_from_page(self, page: Any, page_num: int) -> List[TableRegion]:
        """
        Extract tables from a single page using multiple strategies
        
        Args:
            page: PDFPlumber page object
            page_num: Page number (1-based)
            
        Returns:
            List of TableRegion objects
        """
        tables = []
        
        # Strategy 0: Use pdfplumber's native table objects with accurate bboxes
        try:
            native_tables = page.find_tables(self.table_settings)
            for tbl in native_tables:
                try:
                    table_data = tbl.extract()
                except Exception:
                    table_data = None
                if table_data and len(table_data) >= self.min_table_size:
                    bbox = tuple(tbl.bbox) if hasattr(tbl, 'bbox') else (0, 0, page.width, page.height)
                    table_region = TableRegion(
                        page_number=page_num,
                        bbox=bbox,
                        table_data=table_data,
                        confidence=0.96
                    )
                    tables.append(table_region)
        except Exception as e:
            logger.warning(f"Native table finding failed on page {page_num}: {e}")

        # Strategy 1: Extract tables with default settings (fallback)
        if not tables:
            try:
                extracted_tables = page.extract_tables(self.table_settings)
                for i, table_data in enumerate(extracted_tables):
                    if table_data and len(table_data) >= self.min_table_size:
                        # Estimate bounding box for the table using safer heuristic
                        bbox = self._estimate_table_bbox(page, table_data)
                        table_region = TableRegion(
                            page_number=page_num,
                            bbox=bbox,
                            table_data=table_data,
                            confidence=0.93
                        )
                        tables.append(table_region)
            except Exception as e:
                logger.warning(f"Default table extraction failed on page {page_num}: {e}")
        
        # Strategy 2: Try with relaxed settings if no tables found
        if not tables:
            try:
                relaxed_settings = self.table_settings.copy()
                relaxed_settings.update({
                    'vertical_strategy': "text",
                    'horizontal_strategy': "text",
                    'min_words_vertical': 1,
                    'min_words_horizontal': 1
                })
                
                extracted_tables = page.extract_tables(relaxed_settings)
                
                for table_data in extracted_tables:
                    if table_data and len(table_data) >= self.min_table_size:
                        bbox = self._estimate_table_bbox(page, table_data)
                        
                        table_region = TableRegion(
                            page_number=page_num,
                            bbox=bbox,
                            table_data=table_data,
                            confidence=0.85  # Lower confidence for relaxed extraction
                        )
                        tables.append(table_region)
                        
            except Exception as e:
                logger.warning(f"Relaxed table extraction failed on page {page_num}: {e}")
        
        # Strategy 3: Manual table detection using text positioning
        if not tables:
            manual_tables = self._detect_tables_manually(page, page_num)
            tables.extend(manual_tables)
        
        return tables[:self.max_tables_per_page]  # Limit tables per page
    
    def _estimate_table_bbox(self, page: Any, table_data: List[List[str]]) -> Tuple[float, float, float, float]:
        """
        Estimate bounding box for a table based on its content
        
        Args:
            page: PDFPlumber page object
            table_data: Table data as list of lists
            
        Returns:
            Bounding box coordinates (x0, y0, x1, y1)
        """
        try:
            # Get all words on the page
            words = page.extract_words()
            
            # Build a conservative set of target tokens (avoid overly short tokens)
            targets = set()
            for row in table_data:
                for cell in row:
                    if not cell:
                        continue
                    t = str(cell).strip()
                    if not t:
                        continue
                    if len(t) >= 3 or any(ch in t for ch in ['$', '%', '/', ',']):
                        targets.add(t)
            
            # Exact match only to avoid accidental expansion into paragraphs
            matched = []
            for w in words:
                txt = w.get('text', '')
                if txt in targets:
                    matched.append(w)
            
            # If too few matches, try relaxed match for distinctive tokens (dates/currency)
            if len(matched) < 5:
                import re
                date_like = re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}")
                currency_like = re.compile(r"^\$\s*\d")
                label_like = {t for t in targets if t.lower() in {"category", "metric"}}
                for w in words:
                    txt = w.get('text', '')
                    if date_like.match(txt) or currency_like.match(txt) or txt in label_like:
                        matched.append(w)
            
            # If we have matches, compute tight bbox
            if matched:
                x0 = min(w['x0'] for w in matched)
                y0 = min(w['top'] for w in matched)
                x1 = max(w['x1'] for w in matched)
                y1 = max(w['bottom'] for w in matched)
                # Add minimal padding
                pad = 2
                return (max(0, x0 - pad), max(0, y0 - pad), x1 + pad, y1 + pad)
        
        except Exception as e:
            logger.debug(f"Could not estimate table bbox: {e}")
        
        # Final fallback: return a small centered box to avoid nuking page text
        pw, ph = page.width, page.height
        cx0, cy0, cx1, cy1 = pw * 0.25, ph * 0.25, pw * 0.75, ph * 0.75
        return (cx0, cy0, cx1, cy1)
    
    def _detect_tables_manually(self, page: Any, page_num: int) -> List[TableRegion]:
        """
        Manually detect tables using text patterns and positioning
        
        Args:
            page: PDFPlumber page object
            page_num: Page number (1-based)
            
        Returns:
            List of manually detected table regions
        """
        tables = []
        
        try:
            # Get all text with coordinates
            words = page.extract_words()
            
            if not words:
                return tables
            
            # Group words into potential table rows based on y-coordinates
            rows = self._group_words_into_rows(words)
            
            # Look for table patterns
            table_regions = self._identify_table_regions(rows, page_num)
            
            for region in table_regions:
                if len(region['rows']) >= self.min_table_size:
                    # Convert to table data format
                    table_data = []
                    for row in region['rows']:
                        row_data = [word['text'] for word in row]
                        table_data.append(row_data)
                    
                    # Calculate bounding box
                    all_words = [word for row in region['rows'] for word in row]
                    if all_words:
                        x0 = min(word['x0'] for word in all_words)
                        y0 = min(word['top'] for word in all_words)
                        x1 = max(word['x1'] for word in all_words)
                        y1 = max(word['bottom'] for word in all_words)
                        
                        table_region = TableRegion(
                            page_number=page_num,
                            bbox=(x0, y0, x1, y1),
                            table_data=table_data,
                            confidence=0.75  # Lower confidence for manual detection
                        )
                        tables.append(table_region)
        
        except Exception as e:
            logger.warning(f"Manual table detection failed on page {page_num}: {e}")
        
        return tables
    
    def _group_words_into_rows(self, words: List[Dict]) -> List[List[Dict]]:
        """
        Group words into rows based on y-coordinates
        
        Args:
            words: List of word dictionaries from PDFPlumber
            
        Returns:
            List of rows, each containing words
        """
        if not words:
            return []
        
        # Sort words by y-coordinate (top to bottom)
        sorted_words = sorted(words, key=lambda w: w['top'])
        
        rows = []
        current_row = []
        current_y = None
        y_tolerance = 3
        
        for word in sorted_words:
            word_y = word['top']
            
            if current_y is None:
                current_y = word_y
                current_row = [word]
            elif abs(word_y - current_y) <= y_tolerance:
                # Same row
                current_row.append(word)
            else:
                # New row
                if current_row:
                    # Sort current row by x-coordinate (left to right)
                    current_row.sort(key=lambda w: w['x0'])
                    rows.append(current_row)
                current_row = [word]
                current_y = word_y
        
        # Add the last row
        if current_row:
            current_row.sort(key=lambda w: w['x0'])
            rows.append(current_row)
        
        return rows
    
    def _identify_table_regions(self, rows: List[List[Dict]], page_num: int) -> List[Dict]:
        """
        Identify potential table regions from grouped rows
        
        Args:
            rows: List of rows containing words
            page_num: Page number
            
        Returns:
            List of table region dictionaries
        """
        table_regions = []
        
        if len(rows) < 2:
            return table_regions
        
        # Look for rows with consistent column structure
        current_region = None
        
        for i, row in enumerate(rows):
            # Check if this row looks like a table row
            if self._is_table_row(row):
                if current_region is None:
                    # Start new table region
                    current_region = {
                        'start_row': i,
                        'end_row': i,
                        'rows': [row],
                        'column_count': len(row)
                    }
                else:
                    # Check if this row fits with current region
                    if self._row_fits_region(row, current_region):
                        current_region['end_row'] = i
                        current_region['rows'].append(row)
                    else:
                        # End current region and start new one
                        if len(current_region['rows']) >= 2:
                            table_regions.append(current_region)
                        
                        current_region = {
                            'start_row': i,
                            'end_row': i,
                            'rows': [row],
                            'column_count': len(row)
                        }
            else:
                # End current region
                if current_region is not None:
                    if len(current_region['rows']) >= 2:
                        table_regions.append(current_region)
                    current_region = None
        
        # Add the last region
        if current_region is not None and len(current_region['rows']) >= 2:
            table_regions.append(current_region)
        
        return table_regions
    
    def _is_table_row(self, row: List[Dict]) -> bool:
        """
        Determine if a row looks like it belongs to a table
        
        Args:
            row: List of word dictionaries
            
        Returns:
            True if row appears to be part of a table
        """
        if len(row) < 2:  # Need at least 2 columns
            return False
        
        # Check for consistent spacing between words
        x_positions = [word['x0'] for word in row]
        gaps = []
        for i in range(1, len(x_positions)):
            gaps.append(x_positions[i] - x_positions[i-1])
        
        # If gaps are relatively consistent, it might be a table
        if len(gaps) > 1:
            avg_gap = sum(gaps) / len(gaps)
            consistent_gaps = sum(1 for gap in gaps if abs(gap - avg_gap) < avg_gap * 0.5)
            return consistent_gaps >= len(gaps) * 0.6
        
        return len(row) >= 3  # Multiple columns suggest tabular data
    
    def _row_fits_region(self, row: List[Dict], region: Dict) -> bool:
        """
        Check if a row fits with the current table region
        
        Args:
            row: List of word dictionaries
            region: Current table region
            
        Returns:
            True if row fits the region pattern
        """
        # Check column count similarity
        col_count_diff = abs(len(row) - region['column_count'])
        if col_count_diff > 2:  # Allow some variation
            return False
        
        # Check x-coordinate alignment with previous rows
        if region['rows']:
            last_row = region['rows'][-1]
            if len(last_row) > 0 and len(row) > 0:
                # Check if first columns are roughly aligned
                x_diff = abs(row[0]['x0'] - last_row[0]['x0'])
                if x_diff > 20:  # Tolerance for alignment
                    return False
        
        return True
    
    def _is_valid_table(self, table_region: TableRegion) -> bool:
        """
        Validate if a table region represents a valid table with enhanced filtering
        
        Args:
            table_region: TableRegion object to validate
            
        Returns:
            True if table is valid
        """
        table_data = table_region.table_data
        
        if not table_data or len(table_data) < self.config.get('min_rows', 2):
            return False
        
        # Check minimum and maximum columns
        max_cols = max(len(row) for row in table_data)
        if max_cols < self.config.get('min_cols', 2):
            return False
        
        # NEW: Reject tables with too many columns (likely text parsing errors)
        if max_cols > self.config.get('max_cols', 15):
            logger.debug(f"Rejecting table with {max_cols} columns (exceeds max_cols limit)")
            return False
        
        # Check for reasonable content
        non_empty_cells = 0
        total_cells = 0
        meaningful_cells = 0
        
        for row in table_data:
            for cell in row:
                total_cells += 1
                if cell and cell.strip():
                    non_empty_cells += 1
                    # NEW: Check for meaningful content (not just single characters/words)
                    if self._is_meaningful_cell_content(cell.strip()):
                        meaningful_cells += 1
        
        if total_cells == 0:
            return False
        
        # Check content ratio with configurable threshold
        min_content_ratio = self.config.get('min_cell_content_ratio', 0.4)
        content_ratio = non_empty_cells / total_cells
        meaningful_ratio = meaningful_cells / total_cells if total_cells > 0 else 0
        
        if content_ratio < min_content_ratio:
            logger.debug(f"Rejecting table with low content ratio: {content_ratio:.2f} < {min_content_ratio}")
            return False
        
        # NEW: Additional check for meaningful content
        if meaningful_ratio < 0.25:  # At least 25% should be meaningful content
            logger.debug(f"Rejecting table with low meaningful content ratio: {meaningful_ratio:.2f}")
            return False
        
        # Check confidence threshold (now stricter)
        if table_region.confidence < self.quality_threshold:
            logger.debug(f"Rejecting table with low confidence: {table_region.confidence:.2f} < {self.quality_threshold}")
            return False
        
        # NEW: Check for text-like patterns that shouldn't be tables
        if self._looks_like_text_not_table(table_data):
            logger.debug("Rejecting table that looks like parsed text")
            return False
        
        return True
    
    def _is_meaningful_cell_content(self, cell_content: str) -> bool:
        """
        Check if cell content represents meaningful table data (not text fragments)
        
        Args:
            cell_content: Cell content to validate
            
        Returns:
            True if content appears to be meaningful table data
        """
        if not cell_content:
            return False
        
        # Single characters are usually not meaningful table content
        if len(cell_content) == 1:
            return False
        
        # Very short content (2-3 chars) is suspicious unless it's numbers/codes
        if len(cell_content) <= 3:
            # Allow numbers, currency symbols, percentages, codes
            if any(char.isdigit() for char in cell_content) or cell_content in ['$', '%', 'N/A', 'TBD']:
                return True
            return False
        
        # Long content is usually meaningful
        if len(cell_content) > 20:
            return True
        
        # Check for common table patterns
        table_patterns = [
            r'^\d+$',  # Pure numbers
            r'^\d+\.\d+$',  # Decimals
            r'^\$\d+',  # Currency
            r'\d+%$',  # Percentages
            r'^Q[1-4]',  # Quarters
            r'20\d{2}',  # Years
            r'^[A-Z]{2,}$',  # Codes/abbreviations
        ]
        
        import re
        for pattern in table_patterns:
            if re.search(pattern, cell_content):
                return True
        
        # Content with mixed alphanumeric is usually meaningful
        has_alpha = any(c.isalpha() for c in cell_content)
        has_digit = any(c.isdigit() for c in cell_content)
        
        if has_alpha and has_digit:
            return True
        
        # Multi-word content is usually meaningful
        if len(cell_content.split()) >= 2:
            return True
        
        return True  # Default to meaningful for other cases
    
    def _looks_like_text_not_table(self, table_data: List[List[str]]) -> bool:
        """
        Check if the detected table looks like parsed text rather than actual table
        
        Args:
            table_data: Table data to analyze
            
        Returns:
            True if this looks like text parsed as a table
        """
        if not table_data:
            return True
        
        # Calculate column count variability
        col_counts = [len(row) for row in table_data]
        if len(set(col_counts)) > len(col_counts) * 0.5:  # High variability in column counts
            return True
        
        # Check for sentence-like patterns
        text_indicators = 0
        total_cells = 0
        
        for row in table_data:
            for cell in row:
                if cell and cell.strip():
                    total_cells += 1
                    cell_content = cell.strip().lower()
                    
                    # Check for common sentence words/patterns
                    sentence_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
                    if any(word in cell_content for word in sentence_words):
                        text_indicators += 1
                    
                    # Check for sentence fragments (very short content)
                    if len(cell_content) <= 3 and cell_content.isalpha():
                        text_indicators += 1
                    
                    # Check for incomplete words (common in text parsing)
                    if cell_content.endswith('...') or len(cell_content) == 1:
                        text_indicators += 1
        
        if total_cells == 0:
            return True
        
        # If more than 40% of cells look like text fragments, reject as table
        text_ratio = text_indicators / total_cells
        return text_ratio > 0.4
    
    def _convert_to_schema(self, table_region: TableRegion, table_id: int) -> Optional[Dict]:
        """
        Convert TableRegion to table-oriented JSON schema
        
        Args:
            table_region: TableRegion object
            table_id: Unique table identifier
            
        Returns:
            Dictionary in table-oriented JSON format
        """
        try:
            table_data = table_region.table_data
            
            if not table_data:
                return None
            
            # Determine headers (usually first row)
            headers = table_data[0] if table_data else []
            data_rows = table_data[1:] if len(table_data) > 1 else []
            
            # Create columns structure
            columns = self._create_columns_structure(headers, data_rows, table_data)
            
            # Create rows structure  
            rows = self._create_rows_structure(table_data)
            
            # Create table JSON structure
            table_json = {
                "table_id": f"table_{table_id}",
                "name": f"Table {table_id}",
                "region": {
                    "page_number": table_region.page_number,
                    "bbox": list(table_region.bbox),
                    "detection_method": "pdfplumber"
                },
                "header_info": {
                    "header_rows": [0] if headers else [],
                    "header_columns": [0] if len(table_data) > 0 else [],
                    "data_start_row": 1,
                    "data_start_col": 1
                },
                "columns": columns,
                "rows": rows,
                "metadata": {
                    "detection_method": "pdfplumber",
                    "quality_score": table_region.confidence,
                    "cell_count": len(table_data) * max(len(row) for row in table_data) if table_data else 0,
                    "confidence": table_region.confidence
                }
            }
            
            return table_json
            
        except Exception as e:
            logger.error(f"Error converting table to schema: {str(e)}")
            return None
    
    def _create_columns_structure(self, headers: List[str], data_rows: List[List[str]], table_data: List[List[str]]) -> List[Dict]:
        """
        Create columns structure for table schema
        
        Args:
            headers: Header row
            data_rows: Data rows
            table_data: Complete table data
            
        Returns:
            List of column dictionaries
        """
        columns = []
        max_cols = max(len(row) for row in table_data) if table_data else 0
        
        for col_idx in range(max_cols):
            # Generate column label
            if col_idx < len(headers) and headers[col_idx] and headers[col_idx].strip():
                column_label = headers[col_idx].strip()
            else:
                column_label = f"Column {chr(65 + col_idx)}"  # A, B, C, etc.
            
            column_data = {
                "column_index": col_idx,
                "column_label": column_label,
                "is_header_column": col_idx == 0,
                "cells": {}
            }
            
            # Add cell data for this column
            for row_idx, row in enumerate(table_data):
                if col_idx < len(row) and row[col_idx] and row[col_idx].strip():
                    cell_key = f"{chr(65 + col_idx)}{row_idx + 1}"
                    column_data["cells"][cell_key] = {
                        "value": row[col_idx].strip(),
                        "row": row_idx + 1,
                        "column": col_idx + 1
                    }
            
            columns.append(column_data)
        
        return columns
    
    def _create_rows_structure(self, table_data: List[List[str]]) -> List[Dict]:
        """
        Create rows structure for table schema
        
        Args:
            table_data: Complete table data
            
        Returns:
            List of row dictionaries
        """
        rows = []
        
        for row_idx, row in enumerate(table_data):
            # Generate row label (use first column if available)
            if row and row[0] and row[0].strip():
                row_label = row[0].strip()
            else:
                row_label = f"Row {row_idx + 1}"
            
            row_data = {
                "row_index": row_idx,
                "row_label": row_label,
                "is_header_row": row_idx == 0,
                "cells": {}
            }
            
            # Add cell data for this row
            for col_idx, cell_value in enumerate(row):
                if cell_value and cell_value.strip():
                    cell_key = f"{chr(65 + col_idx)}{row_idx + 1}"
                    row_data["cells"][cell_key] = {
                        "value": cell_value.strip(),
                        "row": row_idx + 1,
                        "column": col_idx + 1
                    }
            
            rows.append(row_data)
        
        return rows
    
    def _update_quality_distribution(self, quality_dist: Dict, confidence: float):
        """Update quality distribution metrics"""
        if confidence >= 0.9:
            quality_dist["high"] += 1
        elif confidence >= 0.7:
            quality_dist["medium"] += 1
        else:
            quality_dist["low"] += 1
    
    def _post_process_tables(self, tables: List[Dict]) -> List[Dict]:
        """
        Apply post-processing to extracted tables including spanning detection
        
        Args:
            tables: List of table dictionaries
            
        Returns:
            Post-processed tables
        """
        # Remove duplicate tables
        unique_tables = []
        seen_signatures = set()
        
        for table in tables:
            signature = self._get_table_signature(table)
            if signature not in seen_signatures:
                unique_tables.append(table)
                seen_signatures.add(signature)
            else:
                logger.debug(f"Removed duplicate table: {table['table_id']}")
        
        # Apply table spanning detection if enabled
        if self.config.get('enable_spanning_detection', True):
            unique_tables = self._merge_spanning_tables(unique_tables)
        
        return unique_tables
    
    def _merge_spanning_tables(self, tables: List[Dict]) -> List[Dict]:
        """
        Merge tables that span across consecutive pages
        
        Args:
            tables: List of table dictionaries
            
        Returns:
            List of tables with spanning tables merged
        """
        if len(tables) <= 1:
            return tables
        
        # Sort tables by page number
        sorted_tables = sorted(tables, key=lambda t: t['region']['page_number'])
        
        merged_tables = []
        current_group = [sorted_tables[0]]
        
        for i in range(1, len(sorted_tables)):
            current_table = sorted_tables[i]
            previous_table = current_group[-1]
            
            # Check if this table should be merged with the previous group
            if self._should_merge_spanning_tables(previous_table, current_table):
                current_group.append(current_table)
                logger.debug(f"Grouping table on page {current_table['region']['page_number']} with spanning table")
            else:
                # Finalize current group
                if len(current_group) > 1:
                    merged_table = self._merge_table_group(current_group)
                    merged_tables.append(merged_table)
                    logger.info(f"Merged spanning table across {len(current_group)} pages: {[t['region']['page_number'] for t in current_group]}")
                else:
                    merged_tables.append(current_group[0])
                
                # Start new group
                current_group = [current_table]
        
        # Handle the last group
        if len(current_group) > 1:
            merged_table = self._merge_table_group(current_group)
            merged_tables.append(merged_table)
            logger.info(f"Merged spanning table across {len(current_group)} pages: {[t['region']['page_number'] for t in current_group]}")
        else:
            merged_tables.append(current_group[0])
        
        return merged_tables
    
    def _should_merge_spanning_tables(self, table1: Dict, table2: Dict) -> bool:
        """
        Determine if two tables should be merged as spanning tables
        
        Args:
            table1: First table
            table2: Second table
            
        Returns:
            True if tables should be merged
        """
        # Check if tables are on consecutive pages
        page1 = table1['region']['page_number']
        page2 = table2['region']['page_number']
        
        if page2 != page1 + 1:
            return False
        
        # Check if tables have same number of columns
        cols1 = len(table1['columns'])
        cols2 = len(table2['columns'])
        
        if cols1 != cols2:
            return False
        
        # Check if column headers match (allowing for some variation)
        headers1 = [col['column_label'] for col in table1['columns']]
        headers2 = [col['column_label'] for col in table2['columns']]
        
        # Calculate header similarity
        matching_headers = sum(1 for h1, h2 in zip(headers1, headers2) if h1.lower() == h2.lower())
        header_similarity = matching_headers / len(headers1) if headers1 else 0
        
        # Require at least 70% header similarity for spanning tables
        if header_similarity < 0.7:
            logger.debug(f"Header similarity too low for spanning: {header_similarity:.2f}")
            return False
        
        # Check if tables are reasonably aligned horizontally
        bbox1 = table1['region']['bbox']
        bbox2 = table2['region']['bbox']
        
        # Check x-alignment (left and right edges should be similar)
        left_diff = abs(bbox1[0] - bbox2[0])
        right_diff = abs(bbox1[2] - bbox2[2])
        
        if left_diff > 20 or right_diff > 20:  # Allow 20 point tolerance
            logger.debug(f"Tables not aligned for spanning: left_diff={left_diff}, right_diff={right_diff}")
            return False
        
        logger.debug(f"Tables on pages {page1}-{page2} qualify for spanning merge")
        return True
    
    def _merge_table_group(self, table_group: List[Dict]) -> Dict:
        """
        Merge a group of spanning tables into a single table
        
        Args:
            table_group: List of tables to merge
            
        Returns:
            Merged table dictionary
        """
        if len(table_group) == 1:
            return table_group[0]
        
        # Use the first table as the base
        merged_table = table_group[0].copy()
        
        # Update table ID to reflect spanning
        page_range = f"{table_group[0]['region']['page_number']}-{table_group[-1]['region']['page_number']}"
        merged_table['table_id'] = f"table_spanning_pages_{page_range}"
        merged_table['name'] = f"Table spanning pages {page_range}"
        
        # Merge rows from all tables
        all_rows = []
        row_offset = 0
        
        for i, table in enumerate(table_group):
            table_rows = table['rows']
            
            for row in table_rows:
                # Skip header row in subsequent tables
                if i > 0 and row.get('is_header_row', False):
                    continue
                
                # Update row index to be sequential
                merged_row = row.copy()
                merged_row['row_index'] = row_offset
                
                # Update cell row references
                for cell_key, cell_data in merged_row['cells'].items():
                    cell_data = cell_data.copy()
                    cell_data['row'] = row_offset + 1
                    merged_row['cells'][cell_key] = cell_data
                
                all_rows.append(merged_row)
                row_offset += 1
        
        merged_table['rows'] = all_rows
        
        # Update metadata
        merged_table['metadata']['cell_count'] = sum(len(row['cells']) for row in all_rows)
        merged_table['metadata']['detection_method'] = 'pdfplumber_spanning'
        
        # Update region to span all pages
        merged_table['region']['page_number'] = f"{table_group[0]['region']['page_number']}-{table_group[-1]['region']['page_number']}"
        
        # Calculate combined bounding box
        all_bboxes = [table['region']['bbox'] for table in table_group]
        merged_bbox = [
            min(bbox[0] for bbox in all_bboxes),  # min x0
            min(bbox[1] for bbox in all_bboxes),  # min y0  
            max(bbox[2] for bbox in all_bboxes),  # max x1
            max(bbox[3] for bbox in all_bboxes)   # max y1
        ]
        merged_table['region']['bbox'] = merged_bbox
        
        logger.debug(f"Successfully merged {len(table_group)} tables into spanning table")
        return merged_table
    
    def _get_table_signature(self, table: Dict) -> str:
        """
        Generate a signature for table deduplication
        
        Args:
            table: Table dictionary
            
        Returns:
            String signature for the table
        """
        try:
            # Use page number, dimensions, and first few cells as signature
            page_num = table.get('region', {}).get('page_number', 0)
            rows_count = len(table.get('rows', []))
            cols_count = len(table.get('columns', []))
            
            # Get first few cell values for content signature
            first_cells = []
            for row in table.get('rows', [])[:2]:  # First 2 rows
                for cell_key, cell_data in list(row.get('cells', {}).items())[:3]:  # First 3 cells
                    first_cells.append(cell_data.get('value', ''))
            
            content_sig = '|'.join(first_cells)
            return f"page_{page_num}_dim_{rows_count}x{cols_count}_content_{hash(content_sig)}"
            
        except Exception:
            return f"table_{id(table)}"  # Fallback to object id 