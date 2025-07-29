import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, column_index_from_string
from openpyxl.styles import Font, Fill, Border, Alignment, Protection
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.workbook.workbook import Workbook


class CompactExcelProcessor:
    """Compact Excel to JSON converter using the new compact schema format"""
    
    def __init__(self):
        self.supported_extensions = ['.xlsx', '.xlsm', '.xltx', '.xltm']
        self.style_registry = {}  # Central style dictionary
        self.next_style_id = 1
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process an Excel file and return compact JSON representation
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            Dictionary containing the compact Excel structure
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        try:
            # First pass: get all data including formulas (data_only=False)
            workbook_with_formulas = load_workbook(file_path, data_only=False, keep_vba=True)
            
            # Second pass: get calculated values (data_only=True)
            workbook_with_values = load_workbook(file_path, data_only=True, keep_vba=True)
            
            return self._process_workbook(workbook_with_formulas, workbook_with_values, file_path)
        except Exception as e:
            raise Exception(f"Error processing Excel file: {str(e)}")
    
    def _process_workbook(self, workbook_with_formulas: Workbook, workbook_with_values: Workbook, file_path: str) -> Dict[str, Any]:
        """Process the entire workbook with both formula and value data"""
        file_stats = os.stat(file_path)
        
        # Reset style registry for each workbook
        self.style_registry = {}
        self.next_style_id = 1
        
        result = {
            "workbook": {
                "meta": self._extract_compact_metadata(workbook_with_formulas, file_path, file_stats),
                "styles": {},  # Will be populated during processing
                "sheets": []   # Array of sheet objects
            }
        }
        
        # Process each worksheet
        for sheet_name in workbook_with_formulas.sheetnames:
            worksheet_with_formulas = workbook_with_formulas[sheet_name]
            worksheet_with_values = workbook_with_values[sheet_name]
            
            # Check if it's a worksheet (not a chart sheet)
            if hasattr(worksheet_with_formulas, 'title') and not hasattr(worksheet_with_formulas, 'chart'):
                sheet_data = self._process_worksheet(worksheet_with_formulas, worksheet_with_values)
                result["workbook"]["sheets"].append(sheet_data)
        
        # Add the style registry to the result
        result["workbook"]["styles"] = self.style_registry
        
        # Generate table_data for compatibility with UI
        result["table_data"] = self._generate_table_data(result["workbook"])
        
        return result
    
    def _extract_compact_metadata(self, workbook: Workbook, file_path: str, file_stats) -> Dict[str, Any]:
        """Extract essential workbook metadata only"""
        props = workbook.properties
        
        metadata = {}
        
        # Only include non-empty/meaningful metadata
        if props.creator:
            metadata["creator"] = props.creator
        if props.created:
            metadata["created"] = self._format_datetime(props.created)
        if props.modified:
            metadata["modified"] = self._format_datetime(props.modified)
        
        metadata["filename"] = os.path.basename(file_path)
        
        return metadata
    
    def _process_worksheet(self, worksheet_with_formulas: Worksheet, worksheet_with_values: Worksheet) -> Dict[str, Any]:
        """Process a single worksheet with compact format"""
        sheet_data = {
            "name": worksheet_with_formulas.title
        }
        
        # Add optional properties only if they have meaningful values
        dimensions = self._extract_dimensions(worksheet_with_formulas)
        if dimensions:
            sheet_data["dimensions"] = [
                dimensions["min_row"],
                dimensions["min_col"], 
                dimensions["max_row"],
                dimensions["max_col"]
            ]
        
        frozen_panes = self._extract_frozen_panes(worksheet_with_formulas)
        if frozen_panes["frozen_rows"] > 0 or frozen_panes["frozen_cols"] > 0:
            sheet_data["frozen"] = [frozen_panes["frozen_rows"], frozen_panes["frozen_cols"]]
        
        merged_cells = self._extract_compact_merged_cells(worksheet_with_formulas)
        if merged_cells:
            sheet_data["merged"] = merged_cells
        
        # Process cells in row-based format
        rows = self._extract_compact_cell_data(worksheet_with_formulas, worksheet_with_values)
        if rows:
            sheet_data["rows"] = rows
        
        return sheet_data
    
    def _extract_dimensions(self, worksheet: Worksheet) -> Dict[str, int]:
        """Extract worksheet dimensions"""
        return {
            "min_row": worksheet.min_row or 1,
            "max_row": worksheet.max_row or 1,
            "min_col": worksheet.min_column or 1,
            "max_col": worksheet.max_column or 1
        }
    
    def _extract_frozen_panes(self, worksheet: Worksheet) -> Dict[str, Any]:
        """Extract frozen pane information"""
        if not worksheet.freeze_panes:
            return {"frozen_rows": 0, "frozen_cols": 0}
        
        frozen_cell = worksheet.freeze_panes
        if isinstance(frozen_cell, str):
            try:
                if ':' in frozen_cell:
                    parts = frozen_cell.split(':')
                    if len(parts) == 2:
                        col_part = parts[0]
                        row_part = parts[1]
                        col_idx = column_index_from_string(col_part)
                        row_idx = int(row_part)
                    else:
                        col_idx = 1
                        row_idx = 1
                else:
                    import re
                    match = re.match(r'([A-Z]+)(\d+)', frozen_cell)
                    if match:
                        col_letter, row_num = match.groups()
                        col_idx = column_index_from_string(col_letter)
                        row_idx = int(row_num)
                    else:
                        col_idx = column_index_from_string(frozen_cell)
                        row_idx = 1
            except:
                col_idx = 1
                row_idx = 1
        else:
            col_idx, row_idx = frozen_cell
        
        return {
            "frozen_rows": row_idx - 1 if row_idx > 0 else 0,
            "frozen_cols": col_idx - 1 if col_idx > 0 else 0
        }
    
    def _extract_compact_merged_cells(self, worksheet: Worksheet) -> List[List[int]]:
        """Extract merged cells in compact format"""
        merged_cells = []
        for merged_range in worksheet.merged_cells.ranges:
            start_cell = getattr(merged_range, 'start_cell', None)
            end_cell = getattr(merged_range, 'end_cell', None)
            if start_cell and end_cell:
                merged_cells.append([
                    getattr(start_cell, 'row', 1),
                    getattr(start_cell, 'column', 1),
                    getattr(end_cell, 'row', 1),
                    getattr(end_cell, 'column', 1)
                ])
        return merged_cells
    
    def _extract_compact_cell_data(self, worksheet_with_formulas: Worksheet, worksheet_with_values: Worksheet) -> List[Dict[str, Any]]:
        """Extract cell data in compact row-based format"""
        rows_data = {}  # Dictionary to organize by row number
        
        for row in worksheet_with_formulas.iter_rows():
            for cell in row:
                # Get formula from the worksheet with formulas
                formula = cell.value if getattr(cell, 'data_type', None) == 'f' else None
                
                # Get calculated value from the worksheet with values
                value_cell = worksheet_with_values[cell.coordinate]
                calculated_value = self._extract_cell_value(value_cell) if value_cell.value is not None else None
                
                # Only process cells that have content
                if calculated_value is not None or formula or cell.comment:
                    row_num = cell.row
                    col_num = cell.column
                    
                    if row_num not in rows_data:
                        rows_data[row_num] = {"r": row_num, "cells": []}
                    
                    # Create compact cell format: [col, value, style_ref?, formula?]
                    cell_array = [col_num]
                    
                    # Add value
                    cell_array.append(calculated_value)
                    
                    # Get style reference
                    style_ref = self._get_style_reference(cell)
                    if style_ref:
                        cell_array.append(style_ref)
                    elif formula:
                        cell_array.append(None)  # Placeholder for style if formula follows
                    
                    # Add formula if present
                    if formula:
                        # Ensure we have a style slot
                        while len(cell_array) < 3:
                            cell_array.append(None)
                        cell_array.append(str(formula))
                    
                    rows_data[row_num]["cells"].append(cell_array)
        
        # Check for row-level shared styles
        for row_num, row_data in rows_data.items():
            shared_style = self._detect_shared_row_style(row_data["cells"])
            if shared_style:
                row_data["style"] = shared_style
                # Remove style references from individual cells if they match the row style
                self._remove_redundant_cell_styles(row_data["cells"], shared_style)
        
        # Convert to sorted list
        return [rows_data[row_num] for row_num in sorted(rows_data.keys())]
    
    def _extract_cell_value(self, cell) -> Any:
        """Extract cell value with proper formatting"""
        if cell.value is None:
            return None
        
        if cell.is_date:
            return self._format_datetime(cell.value)
        
        return cell.value
    
    def _get_style_reference(self, cell) -> Optional[str]:
        """Get or create a style reference for the cell"""
        style_dict = self._extract_cell_style_dict(cell)
        
        # Skip empty styles
        if not style_dict:
            return None
        
        # Create a hashable representation of the style
        style_key = self._create_style_key(style_dict)
        
        # Check if this style already exists
        for style_id, existing_style in self.style_registry.items():
            if self._create_style_key(existing_style) == style_key:
                return style_id
        
        # Create new style reference
        style_id = f"s{self.next_style_id}"
        self.next_style_id += 1
        self.style_registry[style_id] = style_dict
        
        return style_id
    
    def _extract_cell_style_dict(self, cell) -> Dict[str, Any]:
        """Extract cell style as a dictionary"""
        style = {}
        
        # Font styling
        font_style = self._extract_font_style(cell.font)
        if font_style:
            style["font"] = font_style
        
        # Fill styling
        fill_style = self._extract_fill_style(cell.fill)
        if fill_style:
            style["fill"] = fill_style
        
        # Border styling
        border_style = self._extract_border_style(cell.border)
        if border_style:
            style["border"] = border_style
        
        # Alignment styling
        alignment_style = self._extract_alignment_style(cell.alignment)
        if alignment_style:
            style["alignment"] = alignment_style
        
        # Number format
        if cell.number_format and cell.number_format != "General":
            style["number_format"] = cell.number_format
        
        return style
    
    def _extract_font_style(self, font: Font) -> Dict[str, Any]:
        """Extract font styling"""
        if not font:
            return {}
        
        style = {}
        if font.name and font.name != "Calibri":
            style["name"] = font.name
        if font.size and font.size != 11:
            style["size"] = font.size
        if font.bold:
            style["bold"] = True
        if font.italic:
            style["italic"] = True
        if font.underline and font.underline != "none":
            style["underline"] = font.underline
        if font.strike:
            style["strike"] = True
        
        color = self._extract_color(font.color)
        if color:
            style["color"] = color
        
        return style
    
    def _extract_fill_style(self, fill: Fill) -> Dict[str, Any]:
        """Extract fill styling"""
        if not fill or fill.fill_type == "none":
            return {}
        
        style = {}
        if fill.fill_type:
            style["type"] = fill.fill_type
        
        start_color = self._extract_color(fill.start_color)
        if start_color:
            style["color"] = start_color
        
        return style
    
    def _extract_border_style(self, border: Border) -> Dict[str, Any]:
        """Extract border styling"""
        if not border:
            return {}
        
        style = {}
        for side_name in ["left", "right", "top", "bottom"]:
            side = getattr(border, side_name)
            if side and side.style:
                style[side_name] = side.style
        
        return style
    
    def _extract_alignment_style(self, alignment: Alignment) -> Dict[str, Any]:
        """Extract alignment styling"""
        if not alignment:
            return {}
        
        style = {}
        if alignment.horizontal and alignment.horizontal != "general":
            style["horizontal"] = alignment.horizontal
        if alignment.vertical and alignment.vertical != "bottom":
            style["vertical"] = alignment.vertical
        if alignment.wrap_text:
            style["wrap_text"] = True
        
        return style
    
    def _extract_color(self, color) -> Optional[str]:
        """Extract color in compact format"""
        if not color:
            return None
        
        # Handle RGB objects properly
        rgb = getattr(color, 'rgb', None)
        if rgb:
            # Convert RGB object to string if it's not already a string
            if hasattr(rgb, 'rgb'):  # openpyxl RGB object
                rgb_str = rgb.rgb if rgb.rgb else None
            elif isinstance(rgb, str):
                rgb_str = rgb
            else:
                # Try to convert to string representation
                rgb_str = str(rgb) if rgb else None
            
            if rgb_str and rgb_str != "00000000":
                return rgb_str
        
        theme = getattr(color, 'theme', None)
        if theme is not None:
            return f"theme{theme}"
        
        return None
    
    def _create_style_key(self, style_dict: Dict[str, Any]) -> str:
        """Create a hashable key for a style dictionary"""
        return json.dumps(style_dict, sort_keys=True)
    
    def _detect_shared_row_style(self, cells: List[List[Any]]) -> Optional[str]:
        """Detect if all cells in a row share the same style"""
        if not cells:
            return None
        
        # Get style references from cells (3rd element if present)
        style_refs = []
        for cell in cells:
            if len(cell) > 2 and cell[2] is not None:
                style_refs.append(cell[2])
        
        # If all cells have the same style reference, return it
        if style_refs and all(ref == style_refs[0] for ref in style_refs):
            return style_refs[0]
        
        return None
    
    def _remove_redundant_cell_styles(self, cells: List[List[Any]], shared_style: str):
        """Remove redundant style references from cells when they match the row style"""
        for cell in cells:
            if len(cell) > 2 and cell[2] == shared_style:
                # Remove the style reference
                if len(cell) == 3:
                    cell.pop(2)  # Remove style, no formula
                else:
                    cell[2] = None  # Keep slot for formula
    
    def _format_datetime(self, dt) -> Optional[str]:
        """Format datetime objects to ISO 8601 string"""
        if dt is None:
            return None
        
        if isinstance(dt, datetime):
            return dt.isoformat()
        
        return str(dt)
    
    def _generate_table_data(self, workbook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate table_data structure for UI compatibility"""
        table_data = {
            "workbook": {
                "sheets": []
            }
        }
        
        # Convert each sheet to table format
        for sheet in workbook_data.get("sheets", []):
            table_sheet = {
                "name": sheet.get("name", "Unknown"),
                "tables": []
            }
            
            # Create a single table from the sheet data
            if "rows" in sheet and sheet["rows"]:
                table = {
                    "table_id": 1,
                    "name": f"{sheet['name']} - Table",
                    "range": f"A1:{self._get_last_cell_ref(sheet)}",
                    "headers": self._extract_headers_from_rows(sheet["rows"]),
                    "data": self._convert_rows_to_table_data(sheet["rows"]),
                    "columns": self._create_columns_for_cell_cards(sheet["rows"])
                }
                table_sheet["tables"].append(table)
            
            table_data["workbook"]["sheets"].append(table_sheet)
        
        return table_data
    
    def _create_columns_for_cell_cards(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create columns structure for cell cards compatibility"""
        if not rows:
            return []
        
        # Get headers from first row
        headers = []
        first_row = rows[0]
        for cell in first_row.get("cells", []):
            headers.append({
                "col": cell[0],
                "value": str(cell[1]) if cell[1] is not None else ""
            })
        
        columns = []
        
        # Create a column for each header
        for header in headers:
            column = {
                "column_id": header["col"],
                "header": header["value"],
                "cells": {}
            }
            
            # Add cells from all rows for this column
            for row_idx, row in enumerate(rows[1:], start=2):  # Skip header row
                cells_dict = {cell[0]: cell for cell in row.get("cells", [])}
                
                if header["col"] in cells_dict:
                    cell_data = cells_dict[header["col"]]
                    cell_ref = f"{chr(64 + header['col'])}{row_idx}"  # Convert to A1, B2, etc.
                    
                    column["cells"][cell_ref] = {
                        "coordinate": cell_ref,
                        "value": cell_data[1],
                        "headers": {
                            "column_headers": [{"value": header["value"]}],
                            "row_headers": [{"value": str(cells_dict.get(1, [None, ""])[1])}] if 1 in cells_dict else []
                        }
                    }
            
            columns.append(column)
        
        return columns
    
    def _get_last_cell_ref(self, sheet: Dict[str, Any]) -> str:
        """Get the last cell reference in the sheet"""
        max_row = 0
        max_col = 0
        
        for row in sheet.get("rows", []):
            max_row = max(max_row, row.get("r", 0))
            for cell in row.get("cells", []):
                max_col = max(max_col, cell[0])
        
        # Convert to Excel reference
        col_str = ""
        temp_col = max_col
        while temp_col > 0:
            temp_col -= 1
            col_str = chr(65 + (temp_col % 26)) + col_str
            temp_col //= 26
        
        return f"{col_str}{max_row}"
    
    def _extract_headers_from_rows(self, rows: List[Dict[str, Any]]) -> List[str]:
        """Extract headers from the first row"""
        if not rows:
            return []
        
        first_row = rows[0]
        headers = []
        
        for cell in first_row.get("cells", []):
            headers.append(str(cell[1]) if cell[1] is not None else "")
        
        return headers
    
    def _convert_rows_to_table_data(self, rows: List[Dict[str, Any]]) -> List[List[Any]]:
        """Convert rows format to table data format"""
        table_data = []
        
        for row in rows[1:]:  # Skip header row
            row_data = []
            cells_dict = {cell[0]: cell[1] for cell in row.get("cells", [])}
            
            # Find max column to ensure consistent row length
            max_col = max(cells_dict.keys()) if cells_dict else 0
            
            for col in range(1, max_col + 1):
                row_data.append(cells_dict.get(col, ""))
            
            table_data.append(row_data)
        
        return table_data 