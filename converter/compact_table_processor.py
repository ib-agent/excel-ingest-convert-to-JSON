import json
from typing import Dict, Any, List, Optional, Tuple
from openpyxl.utils import get_column_letter, column_index_from_string


class CompactTableProcessor:
    """
    Transforms compact Excel JSON schema into compact table-oriented representation
    while eliminating data duplication and maintaining all table structure information
    """
    
    def __init__(self):
        self.table_detection_rules = []
    
    def transform_to_compact_table_format(self, compact_excel_json: dict, options: dict = None) -> dict:
        """
        Transform compact Excel JSON schema to compact table-oriented format
        
        Args:
            compact_excel_json: The compact Excel JSON schema output
            options: Configuration options for table detection and processing
            
        Returns:
            Dictionary with compact table-oriented structure
        """
        if not compact_excel_json or 'workbook' not in compact_excel_json:
            raise ValueError("Invalid compact Excel JSON format")
        
        # Start with the original structure
        result = compact_excel_json.copy()
        
        # Process each sheet to add table information
        for sheet in result['workbook']['sheets']:
            if 'rows' in sheet:
                sheet['tables'] = self._detect_and_process_compact_tables(sheet, options or {})
        
        return result
    
    def _detect_and_process_compact_tables(self, sheet_data: dict, options: dict) -> List[Dict[str, Any]]:
        """
        Detect tables in a sheet and process them into compact table format
        
        Args:
            sheet_data: Sheet data from the compact JSON
            options: Processing options
            
        Returns:
            List of compact table objects
        """
        tables = []
        
        # Get sheet dimensions from the compact format
        dimensions = sheet_data.get('dimensions', [1, 1, 1, 1])
        min_row, min_col, max_row, max_col = dimensions
        
        # Convert compact rows back to cell-like structure for detection
        cell_map = self._build_cell_map_from_compact_rows(sheet_data.get('rows', []))
        
        # Detect tables using various methods
        detection_options = options.copy()
        detection_options['sheet_data'] = sheet_data
        table_regions = self._detect_table_regions(
            cell_map, min_row, max_row, min_col, max_col, detection_options
        )
        
        # Process each detected table region
        for i, region in enumerate(table_regions):
            table = self._process_compact_table_region(
                sheet_data, region, i, detection_options
            )
            if table:
                tables.append(table)
        
        # If no tables detected, create a default table for the entire sheet
        if not tables and cell_map:
            default_table = self._create_compact_default_table(sheet_data, options)
            if default_table:
                tables.append(default_table)
        
        return tables
    
    def _build_cell_map_from_compact_rows(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert compact row format back to cell map for table detection"""
        cell_map = {}
        
        for row_data in rows:
            row_num = row_data.get('r', 1)
            cells = row_data.get('cells', [])
            
            for cell_array in cells:
                if len(cell_array) >= 2:
                    col_num = cell_array[0]
                    value = cell_array[1]
                    
                    cell_key = f"{get_column_letter(col_num)}{row_num}"
                    cell_map[cell_key] = {
                        'value': value,
                        'row': row_num,
                        'column': col_num
                    }
        
        return cell_map
    
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
        
        # Check if this sheet has frozen panes (indicating a structured table)
        sheet_data = options.get('sheet_data', {})
        frozen_panes = sheet_data.get('frozen', [0, 0])
        frozen_rows, frozen_cols = frozen_panes if len(frozen_panes) >= 2 else [0, 0]
        
        # Check for structured table indicators
        has_structured_layout = self._detect_structured_table_layout(cells, min_row, max_row, min_col, max_col)
        
        # Check if we should use gap-based detection (for multiple tables)
        use_gap_detection = options.get('table_detection', {}).get('use_gaps', False)
        
        # PRIORITY: If sheet has ANY frozen rows or columns, treat as single table
        if frozen_rows > 0 or frozen_cols > 0:
            regions.append({
                'start_row': min_row,
                'end_row': max_row,
                'start_col': min_col,
                'end_col': max_col,
                'detection_method': 'frozen_panes',
                'frozen_rows': frozen_rows,
                'frozen_cols': frozen_cols
            })
            return regions
        
        # If gap detection is explicitly requested, use it
        if use_gap_detection:
            gap_regions = self._detect_tables_by_gaps(cells, min_row, max_row, min_col, max_col)
            if gap_regions:
                regions.extend(gap_regions)
            else:
                regions.extend(self._detect_tables_by_formatting(cells, min_row, max_row, min_col, max_col))
            return regions
        
        # SECONDARY: If sheet shows structured layout, treat as single table
        if has_structured_layout and not use_gap_detection:
            regions.append({
                'start_row': min_row,
                'end_row': max_row,
                'start_col': min_col,
                'end_col': max_col,
                'detection_method': 'structured_layout',
                'has_structured_layout': has_structured_layout
            })
            return regions
        
        # For sheets without frozen panes, use enhanced detection methods
        gap_regions = self._detect_tables_by_gaps(cells, min_row, max_row, min_col, max_col)
        
        if gap_regions:
            regions.extend(gap_regions)
        else:
            regions.extend(self._detect_tables_by_formatting(cells, min_row, max_row, min_col, max_col))
        
        return regions
    
    def _detect_tables_by_gaps(self, cells: dict, min_row: int, max_row: int, 
                             min_col: int, max_col: int) -> List[Dict[str, Any]]:
        """Detect tables by looking for gaps in data"""
        regions = []
        
        current_start_row = None
        consecutive_blank_rows = 0
        max_consecutive_blank_rows = 2
        
        for row in range(min_row, max_row + 1):
            row_has_data = False
            for col in range(min_col, max_col + 1):
                cell_key = f"{get_column_letter(col)}{row}"
                if cell_key in cells and cells[cell_key].get('value') is not None:
                    row_has_data = True
                    if current_start_row is None:
                        current_start_row = row
                    consecutive_blank_rows = 0
                    break
            
            if not row_has_data:
                consecutive_blank_rows += 1
                if current_start_row is not None and consecutive_blank_rows >= max_consecutive_blank_rows:
                    regions.append({
                        'start_row': current_start_row,
                        'end_row': row - consecutive_blank_rows,
                        'start_col': min_col,
                        'end_col': max_col,
                        'detection_method': 'gaps'
                    })
                    current_start_row = None
                    consecutive_blank_rows = 0
        
        # Handle table that extends to the end
        if current_start_row is not None:
            regions.append({
                'start_row': current_start_row,
                'end_row': max_row,
                'start_col': min_col,
                'end_col': max_col,
                'detection_method': 'gaps'
            })
        return regions
    
    def _detect_tables_by_formatting(self, cells: dict, min_row: int, max_row: int, 
                                   min_col: int, max_col: int) -> List[Dict[str, Any]]:
        """Detect tables based on formatting patterns"""
        # For now, create a single table for the entire data range
        return [{
            'start_row': min_row,
            'end_row': max_row,
            'start_col': min_col,
            'end_col': max_col,
            'detection_method': 'formatting'
        }]
    
    def _detect_structured_table_layout(self, cells: dict, min_row: int, max_row: int, 
                                      min_col: int, max_col: int) -> bool:
        """Detect if a sheet has a structured table layout"""
        if not cells:
            return False
        
        # Check if there are multiple columns and rows with data
        columns_with_data = 0
        for col in range(min_col, max_col + 1):
            col_has_data = False
            for row in range(min_row, max_row + 1):
                cell_key = f"{get_column_letter(col)}{row}"
                if cell_key in cells and cells[cell_key].get('value') is not None:
                    col_has_data = True
                    break
            if col_has_data:
                columns_with_data += 1
        
        rows_with_data = 0
        for row in range(min_row, max_row + 1):
            row_has_data = False
            for col in range(min_col, max_col + 1):
                cell_key = f"{get_column_letter(col)}{row}"
                if cell_key in cells and cells[cell_key].get('value') is not None:
                    row_has_data = True
                    break
            if row_has_data:
                rows_with_data += 1
        
        return columns_with_data >= 3 and rows_with_data >= 5
    
    def _process_compact_table_region(self, sheet_data: dict, region: dict, 
                                    table_index: int, options: dict) -> Optional[Dict[str, Any]]:
        """
        Process a table region into compact table format
        
        Args:
            sheet_data: Original sheet data
            region: Table region coordinates
            table_index: Index of the table
            options: Processing options
            
        Returns:
            Compact table object
        """
        rows = sheet_data.get('rows', [])
        if not rows:
            return None
        
        # Determine header information
        header_info = self._determine_compact_headers(rows, region, options)
        
        # Create compact table structure
        table = {
            'id': f"t{table_index + 1}",
            'name': f"Table {table_index + 1}",
            'region': [
                region['start_row'],
                region['start_col'],
                region['end_row'],
                region['end_col']
            ],
            'headers': {
                'rows': header_info['header_rows'],
                'cols': header_info['header_columns'],
                'data_start': [header_info['data_start_row'], header_info['data_start_col']]
            },
            'labels': {
                'cols': self._create_compact_column_labels(rows, header_info, region),
                'rows': self._create_compact_row_labels(rows, header_info, region)
            },
            'meta': {
                'method': region.get('detection_method', 'unknown'),
                'cells': self._count_cells_in_region(rows, region),
                'merged': len(sheet_data.get('merged', [])) > 0
            }
        }
        
        return table
    
    def _determine_compact_headers(self, rows: List[Dict[str, Any]], region: dict, options: dict) -> Dict[str, Any]:
        """Determine header rows and columns for the compact table"""
        start_row = region['start_row']
        end_row = region['end_row']
        start_col = region['start_col']
        end_col = region['end_col']
        
        # Get frozen panes information from sheet data
        sheet_data = options.get('sheet_data', {})
        frozen_panes = sheet_data.get('frozen', [0, 0])
        frozen_rows, frozen_cols = frozen_panes if len(frozen_panes) >= 2 else [0, 0]
        
        # Determine header rows
        header_rows = []
        if frozen_rows > 0:
            for row in range(start_row, start_row + frozen_rows):
                if row <= end_row:
                    header_rows.append(row)
        
        if not header_rows and start_row < end_row:
            header_rows.append(start_row)
        
        # Determine header columns
        header_cols = []
        if frozen_cols > 0:
            for col in range(start_col, start_col + frozen_cols):
                if col <= end_col:
                    header_cols.append(col)
        
        if not header_cols and start_col < end_col:
            header_cols.append(start_col)
        
        return {
            'header_rows': header_rows,
            'header_columns': header_cols,
            'data_start_row': start_row + len(header_rows),
            'data_start_col': start_col + len(header_cols)
        }
    
    def _create_compact_column_labels(self, rows: List[Dict[str, Any]], 
                                    header_info: dict, region: dict) -> List[str]:
        """Create compact column labels array"""
        labels = []
        start_col = region['start_col']
        end_col = region['end_col']
        header_rows = header_info['header_rows']
        
        # Create row lookup for easier access
        row_lookup = {row_data['r']: row_data for row_data in rows}
        
        for col in range(start_col, end_col + 1):
            col_labels = []
            
            for header_row in header_rows:
                if header_row in row_lookup:
                    row_data = row_lookup[header_row]
                    # Find cell for this column
                    for cell_array in row_data.get('cells', []):
                        if len(cell_array) >= 2 and cell_array[0] == col:
                            value = cell_array[1]
                            if value is not None:
                                col_labels.append(str(value))
                            break
            
            label = " | ".join(col_labels) if col_labels else f"Column {get_column_letter(col)}"
            labels.append(label)
        
        return labels
    
    def _create_compact_row_labels(self, rows: List[Dict[str, Any]], 
                                 header_info: dict, region: dict) -> List[str]:
        """Create compact row labels array for data rows only"""
        labels = []
        start_row = region['start_row']
        end_row = region['end_row']
        header_cols = header_info['header_columns']
        data_start_row = header_info['data_start_row']
        
        # Create row lookup for easier access
        row_lookup = {row_data['r']: row_data for row_data in rows}
        
        for row in range(data_start_row, end_row + 1):
            if row in row_lookup:
                row_data = row_lookup[row]
                row_labels = []
                
                for header_col in header_cols:
                    # Find cell for this header column
                    for cell_array in row_data.get('cells', []):
                        if len(cell_array) >= 2 and cell_array[0] == header_col:
                            value = cell_array[1]
                            if value is not None:
                                row_labels.append(str(value))
                            break
                
                label = " | ".join(row_labels) if row_labels else f"Row {row}"
                labels.append(label)
        
        return labels
    
    def _count_cells_in_region(self, rows: List[Dict[str, Any]], region: dict) -> int:
        """Count non-empty cells in the table region"""
        count = 0
        start_row = region['start_row']
        end_row = region['end_row']
        start_col = region['start_col']
        end_col = region['end_col']
        
        for row_data in rows:
            row_num = row_data.get('r', 1)
            if start_row <= row_num <= end_row:
                for cell_array in row_data.get('cells', []):
                    if len(cell_array) >= 2:
                        col_num = cell_array[0]
                        value = cell_array[1]
                        if start_col <= col_num <= end_col and value is not None:
                            count += 1
        
        return count
    
    def _create_compact_default_table(self, sheet_data: dict, options: dict) -> Optional[Dict[str, Any]]:
        """Create a default compact table for the entire sheet if no tables detected"""
        rows = sheet_data.get('rows', [])
        if not rows:
            return None
        
        dimensions = sheet_data.get('dimensions', [1, 1, 1, 1])
        region = {
            'start_row': dimensions[0],
            'end_row': dimensions[2],
            'start_col': dimensions[1],
            'end_col': dimensions[3],
            'detection_method': 'default'
        }
        
        return self._process_compact_table_region(sheet_data, region, 0, options) 