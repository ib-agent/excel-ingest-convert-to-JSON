import json
from typing import Dict, Any, List, Optional, Tuple
from openpyxl.utils import get_column_letter, column_index_from_string


class TableProcessor:
    """
    Transforms Excel JSON schema into table-oriented representation
    while preserving all original information and adding table structure
    """
    
    def __init__(self):
        self.table_detection_rules = []
    
    def transform_to_table_format(self, excel_json: dict, options: dict = None) -> dict:
        """
        Transform Excel JSON schema to table-oriented format
        
        Args:
            excel_json: The original Excel JSON schema output
            options: Configuration options for table detection and processing
            
        Returns:
            Dictionary with table-oriented structure plus all original data
        """
        if not excel_json or 'workbook' not in excel_json:
            raise ValueError("Invalid Excel JSON format")
        
        # Start with the original structure
        result = excel_json.copy()
        
        # Process each sheet to add table information
        for sheet in result['workbook']['sheets']:
            sheet['tables'] = self._detect_and_process_tables(sheet, options or {})
        
        return result
    
    def _detect_and_process_tables(self, sheet_data: dict, options: dict) -> List[Dict[str, Any]]:
        """
        Detect tables in a sheet and process them into table format
        
        Args:
            sheet_data: Sheet data from the original JSON
            options: Processing options
            
        Returns:
            List of table objects
        """
        tables = []
        
        # Get sheet dimensions
        dimensions = sheet_data.get('dimensions', {})
        min_row = dimensions.get('min_row', 1)
        max_row = dimensions.get('max_row', 1)
        min_col = dimensions.get('min_col', 1)
        max_col = dimensions.get('max_col', 1)
        
        # Get cells data
        cells = sheet_data.get('cells', {})
        
        # Detect tables using various methods
        table_regions = self._detect_table_regions(
            cells, min_row, max_row, min_col, max_col, options
        )
        
        # Process each detected table region
        for i, region in enumerate(table_regions):
            table = self._process_table_region(
                sheet_data, region, i, options
            )
            if table:
                tables.append(table)
        
        # If no tables detected, create a default table for the entire sheet
        if not tables and cells:
            default_table = self._create_default_table(sheet_data, options)
            if default_table:
                tables.append(default_table)
        
        return tables
    
    def _detect_table_regions(self, cells: dict, min_row: int, max_row: int, 
                            min_col: int, max_col: int, options: dict) -> List[Dict[str, Any]]:
        """
        Detect table regions in the sheet
        
        Args:
            cells: Cell data dictionary
            min_row, max_row, min_col, max_col: Sheet dimensions
            options: Detection options
            
        Returns:
            List of table regions with coordinates
        """
        regions = []
        
        # Method 1: Detect based on empty row/column gaps
        regions.extend(self._detect_tables_by_gaps(cells, min_row, max_row, min_col, max_col))
        
        # Method 2: Detect based on formatting patterns
        regions.extend(self._detect_tables_by_formatting(cells, min_row, max_row, min_col, max_col))
        
        # Method 3: Detect based on merged cells
        regions.extend(self._detect_tables_by_merged_cells(cells, min_row, max_row, min_col, max_col))
        
        # Remove overlapping regions and merge adjacent ones
        regions = self._merge_overlapping_regions(regions)
        
        return regions
    
    def _detect_tables_by_gaps(self, cells: dict, min_row: int, max_row: int, 
                             min_col: int, max_col: int) -> List[Dict[str, Any]]:
        """Detect tables by looking for gaps in data"""
        regions = []
        
        # Find continuous data regions
        current_start_row = None
        current_start_col = None
        
        for row in range(min_row, max_row + 1):
            row_has_data = False
            for col in range(min_col, max_col + 1):
                cell_key = f"{get_column_letter(col)}{row}"
                if cell_key in cells and cells[cell_key].get('value') is not None:
                    row_has_data = True
                    if current_start_row is None:
                        current_start_row = row
                        current_start_col = col
                    break
            
            if not row_has_data and current_start_row is not None:
                # End of a table region
                regions.append({
                    'start_row': current_start_row,
                    'end_row': row - 1,
                    'start_col': current_start_col,
                    'end_col': max_col,
                    'detection_method': 'gaps'
                })
                current_start_row = None
                current_start_col = None
        
        # Handle table that extends to the end
        if current_start_row is not None:
            regions.append({
                'start_row': current_start_row,
                'end_row': max_row,
                'start_col': current_start_col,
                'end_col': max_col,
                'detection_method': 'gaps'
            })
        
        return regions
    
    def _detect_tables_by_formatting(self, cells: dict, min_row: int, max_row: int, 
                                   min_col: int, max_col: int) -> List[Dict[str, Any]]:
        """Detect tables based on formatting patterns"""
        regions = []
        
        # Look for header-like formatting (bold, background colors, borders)
        header_rows = []
        for row in range(min_row, min(max_row, min_row + 10)):  # Check first 10 rows
            row_has_header_formatting = False
            for col in range(min_col, max_col + 1):
                cell_key = f"{get_column_letter(col)}{row}"
                if cell_key in cells:
                    cell = cells[cell_key]
                    style = cell.get('style', {})
                    font = style.get('font', {})
                    fill = style.get('fill', {})
                    
                    # Check for header-like formatting
                    if (font.get('bold') or 
                        fill.get('fill_type') in ['solid', 'darkGray', 'mediumGray'] or
                        any(border.get('style') for border in style.get('border', {}).values() if border)):
                        row_has_header_formatting = True
                        break
            
            if row_has_header_formatting:
                header_rows.append(row)
        
        # Create table regions based on header rows
        for header_row in header_rows:
            # Find the extent of the table
            end_row = self._find_table_end_row(cells, header_row, max_row, min_col, max_col)
            end_col = self._find_table_end_col(cells, header_row, max_row, min_col, max_col)
            
            regions.append({
                'start_row': header_row,
                'end_row': end_row,
                'start_col': min_col,
                'end_col': end_col,
                'detection_method': 'formatting'
            })
        
        return regions
    
    def _detect_tables_by_merged_cells(self, cells: dict, min_row: int, max_row: int, 
                                     min_col: int, max_col: int) -> List[Dict[str, Any]]:
        """Detect tables based on merged cell patterns"""
        regions = []
        
        # This would analyze merged cells to identify table boundaries
        # For now, return empty list - can be enhanced later
        return regions
    
    def _merge_overlapping_regions(self, regions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping or adjacent table regions"""
        if not regions:
            return regions
        
        # Sort regions by start_row, then start_col
        regions.sort(key=lambda x: (x['start_row'], x['start_col']))
        
        merged = []
        current = regions[0].copy()
        
        for region in regions[1:]:
            # Check if regions overlap or are adjacent
            if (region['start_row'] <= current['end_row'] + 1 and
                region['start_col'] <= current['end_col'] + 1):
                # Merge regions
                current['end_row'] = max(current['end_row'], region['end_row'])
                current['end_col'] = max(current['end_col'], region['end_col'])
                current['detection_method'] = f"{current['detection_method']}+{region['detection_method']}"
            else:
                # No overlap, add current to merged and start new
                merged.append(current)
                current = region.copy()
        
        merged.append(current)
        return merged
    
    def _find_table_end_row(self, cells: dict, start_row: int, max_row: int, 
                           min_col: int, max_col: int) -> int:
        """Find the end row of a table"""
        for row in range(start_row + 1, max_row + 1):
            row_has_data = False
            for col in range(min_col, max_col + 1):
                cell_key = f"{get_column_letter(col)}{row}"
                if cell_key in cells and cells[cell_key].get('value') is not None:
                    row_has_data = True
                    break
            if not row_has_data:
                return row - 1
        return max_row
    
    def _find_table_end_col(self, cells: dict, start_row: int, max_row: int, 
                           min_col: int, max_col: int) -> int:
        """Find the end column of a table"""
        for col in range(min_col, max_col + 1):
            col_has_data = False
            for row in range(start_row, max_row + 1):
                cell_key = f"{get_column_letter(col)}{row}"
                if cell_key in cells and cells[cell_key].get('value') is not None:
                    col_has_data = True
                    break
            if not col_has_data:
                return col - 1
        return max_col
    
    def _process_table_region(self, sheet_data: dict, region: dict, 
                            table_index: int, options: dict) -> Optional[Dict[str, Any]]:
        """
        Process a table region into table format
        
        Args:
            sheet_data: Original sheet data
            region: Table region coordinates
            table_index: Index of the table
            options: Processing options
            
        Returns:
            Table object with columns and rows
        """
        cells = sheet_data.get('cells', {})
        merged_cells = sheet_data.get('merged_cells', [])
        
        # Extract table data
        table_cells = self._extract_table_cells(cells, region)
        if not table_cells:
            return None
        
        # Determine header rows and columns
        header_info = self._determine_headers(table_cells, region, merged_cells, options)
        
        # Create table structure
        table = {
            'table_id': f"table_{table_index + 1}",
            'name': f"Table {table_index + 1}",
            'region': region,
            'header_info': header_info,
            'columns': self._create_columns(table_cells, header_info, region),
            'rows': self._create_rows(table_cells, header_info, region),
            'metadata': {
                'detection_method': region.get('detection_method', 'unknown'),
                'cell_count': len(table_cells),
                'has_merged_cells': bool(merged_cells)
            }
        }
        
        return table
    
    def _extract_table_cells(self, cells: dict, region: dict) -> Dict[str, Any]:
        """Extract cells that belong to the table region"""
        table_cells = {}
        start_row = region['start_row']
        end_row = region['end_row']
        start_col = region['start_col']
        end_col = region['end_col']
        
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                cell_key = f"{get_column_letter(col)}{row}"
                if cell_key in cells:
                    table_cells[cell_key] = cells[cell_key]
        
        return table_cells
    
    def _determine_headers(self, table_cells: dict, region: dict, 
                         merged_cells: List[dict], options: dict) -> Dict[str, Any]:
        """Determine header rows and columns for the table"""
        start_row = region['start_row']
        end_row = region['end_row']
        start_col = region['start_col']
        end_col = region['end_col']
        
        # Simple heuristic: first row is header row, first column is header column
        # This can be enhanced with more sophisticated detection
        header_rows = [start_row] if start_row < end_row else []
        header_cols = [start_col] if start_col < end_col else []
        
        return {
            'header_rows': header_rows,
            'header_columns': header_cols,
            'data_start_row': start_row + len(header_rows),
            'data_start_col': start_col + len(header_cols)
        }
    
    def _create_columns(self, table_cells: dict, header_info: dict, region: dict) -> List[Dict[str, Any]]:
        """Create column definitions with labels"""
        columns = []
        start_col = region['start_col']
        end_col = region['end_col']
        header_rows = header_info['header_rows']
        
        for col in range(start_col, end_col + 1):
            col_letter = get_column_letter(col)
            
            # Get column label from header rows
            column_label = self._get_column_label(table_cells, col, header_rows)
            
            column_def = {
                'column_index': col,
                'column_letter': col_letter,
                'column_label': column_label,
                'is_header_column': col in header_info['header_columns'],
                'width': None,  # Can be populated from sheet column properties
                'hidden': False,  # Can be populated from sheet column properties
                'cells': {}
            }
            
            # Add cells for this column
            for row in range(region['start_row'], region['end_row'] + 1):
                cell_key = f"{col_letter}{row}"
                if cell_key in table_cells:
                    column_def['cells'][cell_key] = table_cells[cell_key]
            
            columns.append(column_def)
        
        return columns
    
    def _create_rows(self, table_cells: dict, header_info: dict, region: dict) -> List[Dict[str, Any]]:
        """Create row definitions with labels"""
        rows = []
        start_row = region['start_row']
        end_row = region['end_row']
        header_cols = header_info['header_columns']
        
        for row in range(start_row, end_row + 1):
            # Get row label from header columns
            row_label = self._get_row_label(table_cells, row, header_cols)
            
            row_def = {
                'row_index': row,
                'row_label': row_label,
                'is_header_row': row in header_info['header_rows'],
                'height': None,  # Can be populated from sheet row properties
                'hidden': False,  # Can be populated from sheet row properties
                'cells': {}
            }
            
            # Add cells for this row
            for col in range(region['start_col'], region['end_col'] + 1):
                col_letter = get_column_letter(col)
                cell_key = f"{col_letter}{row}"
                if cell_key in table_cells:
                    row_def['cells'][cell_key] = table_cells[cell_key]
            
            rows.append(row_def)
        
        return rows
    
    def _get_column_label(self, table_cells: dict, col: int, header_rows: List[int]) -> str:
        """Get the label for a column from header rows"""
        col_letter = get_column_letter(col)
        labels = []
        
        for header_row in header_rows:
            cell_key = f"{col_letter}{header_row}"
            if cell_key in table_cells:
                cell_value = table_cells[cell_key].get('value')
                if cell_value is not None:
                    labels.append(str(cell_value))
        
        return " | ".join(labels) if labels else f"Column {col_letter}"
    
    def _get_row_label(self, table_cells: dict, row: int, header_cols: List[int]) -> str:
        """Get the label for a row from header columns"""
        labels = []
        
        for header_col in header_cols:
            col_letter = get_column_letter(header_col)
            cell_key = f"{col_letter}{row}"
            if cell_key in table_cells:
                cell_value = table_cells[cell_key].get('value')
                if cell_value is not None:
                    labels.append(str(cell_value))
        
        return " | ".join(labels) if labels else f"Row {row}"
    
    def _create_default_table(self, sheet_data: dict, options: dict) -> Optional[Dict[str, Any]]:
        """Create a default table for the entire sheet if no tables detected"""
        cells = sheet_data.get('cells', {})
        if not cells:
            return None
        
        dimensions = sheet_data.get('dimensions', {})
        region = {
            'start_row': dimensions.get('min_row', 1),
            'end_row': dimensions.get('max_row', 1),
            'start_col': dimensions.get('min_col', 1),
            'end_col': dimensions.get('max_col', 1),
            'detection_method': 'default'
        }
        
        return self._process_table_region(sheet_data, region, 0, options) 