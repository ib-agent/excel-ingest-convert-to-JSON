import json
from typing import Dict, Any, List, Optional, Tuple
from openpyxl.utils import get_column_letter, column_index_from_string


class HeaderResolver:
    """
    Resolves and adds header context to each data cell in table-oriented JSON
    """
    
    def __init__(self):
        self.header_detection_rules = []
        self.column_header_cache = {}
        self.row_header_cache = {}
    
    def resolve_headers(self, table_json: dict, options: dict = None) -> dict:
        """
        Resolve headers for all data cells in the table-oriented JSON
        
        Args:
            table_json: The table-oriented JSON output
            options: Configuration options for header resolution
            
        Returns:
            Enhanced JSON with header context for each data cell
        """
        if not table_json or 'workbook' not in table_json:
            raise ValueError("Invalid table JSON format")
        
        # Start with the original structure
        result = table_json.copy()
        options = options or {}
        
        # Process each sheet
        for sheet in result['workbook']['sheets']:
            if 'tables' in sheet:
                for table in sheet['tables']:
                    self._resolve_table_headers(table, options)
        
        return result
    
    def _resolve_table_headers(self, table: dict, options: dict):
        """
        Resolve headers for a single table
        
        Args:
            table: Table object with columns and rows
            options: Processing options
        """
        # Get table information
        header_info = table.get('header_info', {})
        header_rows = header_info.get('header_rows', [])
        header_columns = header_info.get('header_columns', [])
        data_start_row = header_info.get('data_start_row', 1)
        data_start_col = header_info.get('data_start_col', 1)
        
        # Build column header hierarchy
        column_headers = self._build_column_header_hierarchy(table, header_rows, options)
        
        # Build row header hierarchy
        row_headers = self._build_row_header_hierarchy(table, header_columns, options)
        
        # Add header context to each data cell
        self._add_header_context_to_cells(table, column_headers, row_headers, 
                                        data_start_row, data_start_col, options)
    
    def _build_column_header_hierarchy(self, table: dict, header_rows: List[int], 
                                     options: dict) -> Dict[int, List[Dict[str, Any]]]:
        """
        Build hierarchical column headers from header rows
        
        Args:
            table: Table object
            header_rows: List of header row indices
            options: Processing options
            
        Returns:
            Dictionary mapping column index to list of header levels
        """
        column_headers = {}
        columns = table.get('columns', [])
        
        for col in columns:
            col_index = col['column_index']
            col_letter = col['column_letter']
            headers = []
            
            # Process each header row
            for level, header_row in enumerate(header_rows):
                cell_key = f"{col_letter}{header_row}"
                cells = col.get('cells', {})
                
                if cell_key in cells:
                    cell = cells[cell_key]
                    header_info = {
                        'level': level + 1,
                        'value': cell.get('value'),
                        'coordinate': cell_key,
                        'row': header_row,
                        'column': col_index,
                        'column_letter': col_letter,
                        'span': self._get_header_span(table, header_row, col_index, options),
                        'style': cell.get('style', {}),
                        'is_merged': self._is_merged_cell(table, cell_key)
                    }
                    headers.append(header_info)
            
            column_headers[col_index] = headers
        
        return column_headers
    
    def _build_row_header_hierarchy(self, table: dict, header_columns: List[int], 
                                  options: dict) -> Dict[int, List[Dict[str, Any]]]:
        """
        Build hierarchical row headers from header columns
        
        Args:
            table: Table object
            header_columns: List of header column indices
            options: Processing options
            
        Returns:
            Dictionary mapping row index to list of header levels
        """
        row_headers = {}
        rows = table.get('rows', [])
        
        for row in rows:
            row_index = row['row_index']
            headers = []
            
            # Process each header column
            for level, header_col in enumerate(header_columns):
                col_letter = get_column_letter(header_col)
                cell_key = f"{col_letter}{row_index}"
                cells = row.get('cells', {})
                
                if cell_key in cells:
                    cell = cells[cell_key]
                    header_info = {
                        'level': level + 1,
                        'value': cell.get('value'),
                        'coordinate': cell_key,
                        'row': row_index,
                        'column': header_col,
                        'column_letter': col_letter,
                        'span': self._get_header_span(table, row_index, header_col, options),
                        'style': cell.get('style', {}),
                        'indent_level': self._get_indent_level(cell),
                        'is_merged': self._is_merged_cell(table, cell_key)
                    }
                    headers.append(header_info)
            
            row_headers[row_index] = headers
        
        return row_headers
    
    def _get_header_span(self, table: dict, row: int, col: int, options: dict) -> Dict[str, int]:
        """
        Get the span information for a header cell
        
        Args:
            table: Table object
            row: Row index
            col: Column index
            options: Processing options
            
        Returns:
            Dictionary with start and end positions
        """
        # For now, return single cell span
        # This can be enhanced to detect merged cells and spans
        return {
            'start_row': row,
            'end_row': row,
            'start_col': col,
            'end_col': col
        }
    
    def _get_indent_level(self, cell: dict) -> int:
        """
        Get the indent level for a cell based on alignment
        
        Args:
            cell: Cell object
            
        Returns:
            Indent level (0-based)
        """
        style = cell.get('style', {})
        alignment = style.get('alignment', {})
        indent = alignment.get('indent', 0)
        
        # Convert Excel indent to level (approximate)
        return max(0, indent // 2)
    
    def _is_merged_cell(self, table: dict, cell_key: str) -> bool:
        """
        Check if a cell is part of a merged cell range
        
        Args:
            table: Table object
            cell_key: Cell coordinate
            
        Returns:
            True if cell is merged
        """
        # This would check against merged_cells information
        # For now, return False - can be enhanced later
        return False
    
    def _add_header_context_to_cells(self, table: dict, column_headers: dict, 
                                   row_headers: dict, data_start_row: int, 
                                   data_start_col: int, options: dict):
        """
        Add header context to each data cell in the table
        
        Args:
            table: Table object
            column_headers: Column header hierarchy
            row_headers: Row header hierarchy
            data_start_row: First data row
            data_start_col: First data column
            options: Processing options
        """
        # Process each column
        for col in table.get('columns', []):
            col_index = col['column_index']
            col_headers = column_headers.get(col_index, [])
            
            # Process each cell in the column
            for cell_key, cell in col.get('cells', {}).items():
                # Only add header context to data cells (not header cells)
                if self._is_data_cell(cell, data_start_row, data_start_col):
                    self._add_cell_header_context(cell, col_headers, row_headers, options)
    
    def _is_data_cell(self, cell: dict, data_start_row: int, data_start_col: int) -> bool:
        """
        Check if a cell is a data cell (not a header cell)
        
        Args:
            cell: Cell object
            data_start_row: First data row
            data_start_col: First data column
            
        Returns:
            True if cell is a data cell
        """
        row = cell.get('row', 0)
        col = cell.get('column', 0)
        
        # Must be in the data region
        if row < data_start_row or col < data_start_col:
            return False
        
        # Skip cells with null/empty values
        value = cell.get('value')
        if value is None or value == '':
            return False
        
        # Check if it's a numeric data cell (most common case)
        data_type = cell.get('data_type', '')
        if data_type == 'number':
            return True
        
        # Check if it's a string that looks like data (not a header)
        if data_type == 'string' and value:
            # Skip cells that look like headers (short strings, bold formatting)
            style = cell.get('style', {})
            font = style.get('font', {})
            
            # If it's bold, it's likely a header
            if font.get('bold', False):
                return False
            
            # If it's a short string (likely a header), skip it
            if len(str(value)) <= 10:
                return False
        
        # For other data types, assume it's data if it's in the data region
        return True
    
    def _add_cell_header_context(self, cell: dict, col_headers: List[dict], 
                               row_headers: dict, options: dict):
        """
        Add header context to a single cell
        
        Args:
            cell: Cell object to enhance
            col_headers: Column header hierarchy for this cell's column
            row_headers: Row header hierarchy for all rows
            options: Processing options
        """
        row_index = cell.get('row', 0)
        row_headers_for_cell = row_headers.get(row_index, [])
        
        # Create header context
        header_context = {
            'column_headers': col_headers,
            'row_headers': row_headers_for_cell,
            'full_column_path': self._build_column_path(col_headers),
            'full_row_path': self._build_row_path(row_headers_for_cell),
            'header_summary': self._create_header_summary(col_headers, row_headers_for_cell)
        }
        
        # Add to cell
        cell['headers'] = header_context
    
    def _build_column_path(self, col_headers: List[dict]) -> List[str]:
        """
        Build a simple column header path
        
        Args:
            col_headers: List of column header levels
            
        Returns:
            List of header values
        """
        path = []
        for header in col_headers:
            value = header.get('value')
            if value is not None:
                path.append(str(value))
        return path
    
    def _build_row_path(self, row_headers: List[dict]) -> List[str]:
        """
        Build a simple row header path
        
        Args:
            row_headers: List of row header levels
            
        Returns:
            List of header values
        """
        path = []
        for header in row_headers:
            value = header.get('value')
            if value is not None:
                path.append(str(value))
        return path
    
    def _create_header_summary(self, col_headers: List[dict], row_headers: List[dict]) -> dict:
        """
        Create a summary of headers for easy access
        
        Args:
            col_headers: Column header hierarchy
            row_headers: Row header hierarchy
            
        Returns:
            Summary dictionary
        """
        return {
            'primary_column_header': col_headers[0].get('value') if col_headers else None,
            'primary_row_header': row_headers[0].get('value') if row_headers else None,
            'column_header_levels': len(col_headers),
            'row_header_levels': len(row_headers),
            'has_merged_headers': any(h.get('is_merged', False) for h in col_headers + row_headers),
            'max_indent_level': max([h.get('indent_level', 0) for h in row_headers], default=0)
        }


def enhance_table_with_headers(table_json: dict, options: dict = None) -> dict:
    """
    Convenience function to enhance table JSON with header context
    
    Args:
        table_json: Table-oriented JSON
        options: Processing options
        
    Returns:
        Enhanced JSON with header context
    """
    resolver = HeaderResolver()
    return resolver.resolve_headers(table_json, options) 