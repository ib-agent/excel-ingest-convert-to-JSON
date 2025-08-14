"""
HTML Generation Service

This service pre-generates HTML content for Excel and PDF processing results
to optimize web interface performance by avoiding client-side rendering.
"""

import json
import html
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HTMLGenerator:
    """Generates HTML content for Excel and PDF processing results"""
    
    def __init__(self):
        self.version = "1.0.12"
        self.build_time = datetime.now().isoformat()
    
    def generate_complete_html(self, data: Dict[str, Any], meta: Dict[str, Any]) -> str:
        """Generate complete HTML for a processing result"""
        try:
            file_type = meta.get('file_type', '').lower()
            
            if file_type == 'excel':
                return self._generate_excel_html(data, meta)
            elif file_type == 'pdf':
                return self._generate_pdf_html(data, meta)
            else:
                return self._generate_error_html(f"Unknown file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error generating HTML: {e}")
            return self._generate_error_html(f"Error generating HTML: {str(e)}")
    
    def _generate_excel_html(self, data: Dict[str, Any], meta: Dict[str, Any]) -> str:
        """Generate HTML for Excel processing results"""
        full = data.get('full', {})
        if 'workbook' in full:
            workbook_data = full
        else:
            workbook_data = full
        
        workbook = workbook_data.get('workbook', {})
        sheets = workbook.get('sheets', [])
        
        html_parts = []
        
        # Workbook information (removed duplicate metadata section)
        html_parts.append('<div class="section-title">Workbook Information</div>')
        wb_meta = workbook.get('meta', {})
        file_counts = self._compute_file_counts(sheets)
        
        # Compact single-row display
        html_parts.append('<div style="display:flex; flex-wrap:wrap; gap:1.5rem; align-items:center; font-size:0.9rem; margin:1rem 0;">')
        
        # Essential info only
        if wb_meta.get('filename'):
            html_parts.append(f'<span><strong>File:</strong> {self._escape_html(wb_meta["filename"])}</span>')
        if wb_meta.get('file_size'):
            html_parts.append(f'<span><strong>Size:</strong> {self._format_file_size(wb_meta["file_size"])}</span>')
        
        # Summary counts
        html_parts.append(f'<span><strong>Sheets:</strong> {file_counts["sheet_count"]}</span>')
        html_parts.append(f'<span><strong>Tables:</strong> {file_counts["table_count"]}</span>')
        html_parts.append(f'<span><strong>Numbers:</strong> {file_counts["numeric_cells"]}</span>')
        
        html_parts.append('</div>')
        
        # Sheets overview
        html_parts.append('<div class="section-title">Sheets</div>')
        html_parts.append('<ul class="list">')
        
        for idx, sheet in enumerate(sheets):
            sheet_html = self._generate_sheet_overview(sheet, idx)
            html_parts.append(sheet_html)
        
        html_parts.append('</ul>')
        
        # Rendered tables
        html_parts.append('<div class="section-title" style="margin-top:0.75rem;">Rendered Tables</div>')
        html_parts.append('<div class="html-tables">')
        
        for idx, sheet in enumerate(sheets):
            sheet_tables_html = self._generate_excel_sheet_tables(sheet, idx)
            html_parts.append(sheet_tables_html)
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_pdf_html(self, data: Dict[str, Any], meta: Dict[str, Any]) -> str:
        """Generate HTML for PDF processing results"""
        full = data.get('full', {})
        pdf_result = full.get('pdf_processing_result', {})
        
        html_parts = []
        
        # Document information (removed duplicate metadata section)
        doc_meta = pdf_result.get('document_metadata', {})
        summary = pdf_result.get('processing_summary', {})
        
        html_parts.append('<div class="section-title">Document Information</div>')
        html_parts.append('<div class="grid">')
        html_parts.append(f'<div class="kv"><strong>Filename:</strong> {self._escape_html(doc_meta.get("filename", ""))}</div>')
        html_parts.append(f'<div class="kv"><strong>Total pages:</strong> {doc_meta.get("total_pages", "")}</div>')
        
        if doc_meta.get('processing_duration'):
            duration = f'{doc_meta["processing_duration"]:.2f}s'
            html_parts.append(f'<div class="kv"><strong>Processing duration:</strong> {duration}</div>')
        
        extraction_methods = doc_meta.get('extraction_methods', [])
        html_parts.append(f'<div class="kv"><strong>Extraction methods:</strong> {", ".join(extraction_methods)}</div>')
        html_parts.append('</div>')
        
        # Processing summary
        html_parts.append('<div class="section-title" style="margin-top:0.75rem;">Processing Summary</div>')
        html_parts.append('<div class="grid">')
        html_parts.append(f'<div class="kv"><strong>Tables extracted:</strong> {summary.get("tables_extracted", "")}</div>')
        html_parts.append(f'<div class="kv"><strong>Numbers found:</strong> {summary.get("numbers_found", "")}</div>')
        html_parts.append(f'<div class="kv"><strong>Text sections:</strong> {summary.get("text_sections", "")}</div>')
        
        if summary.get('overall_quality_score') is not None:
            quality_score = f'{summary["overall_quality_score"] * 100:.1f}%'
            html_parts.append(f'<div class="kv"><strong>Quality score:</strong> {quality_score}</div>')
        
        html_parts.append('</div>')
        
        # Rendered tables
        tables = pdf_result.get('tables', {}).get('tables', [])
        html_parts.append('<div class="section-title" style="margin-top:0.75rem;">Rendered Tables</div>')
        html_parts.append('<div class="html-tables">')
        
        if not tables:
            html_parts.append('<div class="muted">No tables detected in this document.</div>')
        else:
            for idx, table in enumerate(tables):
                table_html = self._generate_pdf_table(table, idx)
                html_parts.append(table_html)
        
        html_parts.append('</div>')
        
        # Text content with numbers
        html_parts.append('<div class="section-title" style="margin-top:0.75rem;">Text Content with Extracted Numbers</div>')
        sections = self._collect_pdf_text_sections(pdf_result)
        
        if not sections:
            html_parts.append('<div class="muted">No text sections with numbers found.</div>')
        else:
            html_parts.append('<div class="pdf-text-sections">')
            for idx, section in enumerate(sections):
                section_html = self._generate_text_section(section, idx)
                html_parts.append(section_html)
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_meta_section(self, meta: Dict[str, Any]) -> str:
        """Generate metadata section HTML"""
        created = self._format_date(meta.get('created_at', '')) if meta.get('created_at') else ''
        
        html_parts = [
            '<div class="grid">',
            f'<div class="kv"><strong>Processing ID:</strong> {meta.get("processing_id", "")}</div>',
            f'<div class="kv"><strong>Created:</strong> {created}</div>',
            f'<div class="kv"><strong>File type:</strong> {meta.get("file_type", "")}</div>',
            f'<div class="kv"><strong>Filename:</strong> {meta.get("filename", "")}</div>',
            '</div>'
        ]
        
        return '\n'.join(html_parts)
    
    def _generate_sheet_overview(self, sheet: Dict[str, Any], idx: int) -> str:
        """Generate simplified HTML for sheet overview with only table count and dimensions"""
        sheet_name = sheet.get('name', f'Sheet {idx + 1}')
        tables = sheet.get('tables', [])
        table_count = len(tables)
        
        html_parts = [
            f'<li><strong>{self._escape_html(sheet_name)}</strong> <span class="muted">({table_count} tables)</span>'
        ]
        
        # Add table dimensions in (B1:Q16) format only
        if tables:
            for table in tables:
                region = table.get('region')
                if isinstance(region, list) and len(region) == 4:
                    sr1, sc1, sr2, sc2 = region
                    cell_ref = f'{self._get_cell_ref(sr1, sc1)}:{self._get_cell_ref(sr2, sc2)}'
                    html_parts.append(f'<div class="muted">({cell_ref})</div>')
        
        html_parts.append('</li>')
        
        return '\n'.join(html_parts)
    
    def _generate_excel_sheet_tables(self, sheet: Dict[str, Any], idx: int) -> str:
        """Generate HTML for Excel sheet tables"""
        sheet_name = sheet.get('name', f'Sheet {idx + 1}')
        tables = sheet.get('tables', [])
        
        html_parts = [
            '<div class="sheet-block">',
            f'<div class="sheet-title">{self._escape_html(sheet_name)}</div>'
        ]
        
        if not tables:
            html_parts.append('<div class="muted">No tables detected on this sheet.</div>')
        else:
            cell_map = self._build_sheet_cell_map(sheet)
            for j, table in enumerate(tables):
                table_name = table.get('name') or table.get('id') or f'Table {j + 1}'
                html_parts.append('<div class="table-block">')
                html_parts.append(f'<div class="table-title">{self._escape_html(table_name)}</div>')
                
                region = table.get('region')
                if isinstance(region, list) and len(region) == 4:
                    table_html = self._render_excel_table(cell_map, table)
                    html_parts.append(table_html)
                else:
                    html_parts.append('<div class="muted">No region info to render.</div>')
                
                html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_pdf_table(self, table: Dict[str, Any], idx: int) -> str:
        """Generate HTML for PDF table"""
        table_name = table.get('name') or table.get('table_id') or f'Table {idx + 1}'
        
        html_parts = [
            '<div class="table-block">',
            f'<div class="table-title">{self._escape_html(table_name)}</div>'
        ]
        
        # Table metadata
        region = table.get('region', {})
        if region.get('page_number'):
            region_info = f'Page: {region["page_number"]}'
            bbox = region.get('bbox')
            if isinstance(bbox, list) and len(bbox) >= 4:
                bbox_str = ', '.join(f'{x:.1f}' for x in bbox)
                region_info += f' | Region: ({bbox_str})'
            html_parts.append(f'<div class="muted">{region_info}</div>')
        
        # Render the table
        table_html = self._render_pdf_table(table)
        html_parts.append(table_html)
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_text_section(self, section: Dict[str, Any], idx: int) -> str:
        """Generate HTML for PDF text section"""
        content = section.get('content', '')
        numbers = section.get('numbers', [])
        page = section.get('page', '?')
        
        html_parts = [
            '<div class="text-section-block">',
            '<div class="text-section-header" style="margin-bottom:0.5rem; color:#f8fafc;">',
            f'<strong>Section {idx + 1}</strong> ',
            f'<span class="muted">(Page {page} • {len(numbers)} numbers extracted)</span>',
            '</div>'
        ]
        
        if content and content.strip():
            highlighted_text = self._highlight_numbers_in_text(content, numbers)
            html_parts.append('<div class="text-content" style="margin:0.5rem 0; line-height:1.5; font-size:0.95rem; color:#e2e8f0;">')
            html_parts.append(highlighted_text)
            html_parts.append('</div>')
        
        # Show extracted numbers with details
        if numbers:
            html_parts.append(f'<details style="margin-top:0.75rem; color:#e2e8f0;"><summary class="muted">Extracted Numbers ({len(numbers)})</summary>')
            html_parts.append('<div class="numbers-list" style="margin:0.75rem 0; display:flex; flex-wrap:wrap; gap:0.75rem; padding:0.5rem; background:rgba(15, 23, 42, 0.5); border-radius:8px; border:1px solid rgba(59, 130, 246, 0.1);">')
            
            for num in numbers:
                badge_html = self._generate_number_badge(num)
                html_parts.append(badge_html)
            
            html_parts.append('</div></details>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _generate_error_html(self, error_message: str) -> str:
        """Generate error HTML"""
        return f'<div class="muted error">Error: {self._escape_html(error_message)}</div>'
    
    # Helper methods for specific rendering tasks
    
    def _render_pdf_table(self, table: Dict[str, Any]) -> str:
        """Render PDF table as HTML"""
        columns = table.get('columns', [])
        rows = table.get('rows', [])
        
        if not columns:
            return '<div class="muted">No table data to display.</div>'
        
        html_parts = ['<table class="rendered pdf-table">']
        
        # Create header
        html_parts.append('<thead><tr>')
        for col in columns:
            label = col.get('column_label') or f'Column {col.get("column_index", 0) + 1}'
            html_parts.append(f'<th>{self._escape_html(label)}</th>')
        html_parts.append('</tr></thead>')
        
        # Create body
        html_parts.append('<tbody>')
        for row_idx, row in enumerate(rows):
            if row.get('is_header_row'):
                continue  # Skip header rows in body
            
            html_parts.append('<tr>')
            for col in columns:
                cell_value = ''
                row_cells = row.get('cells', {})
                
                # Find the cell that matches this column
                for cell_ref, cell_data in row_cells.items():
                    if cell_data and cell_data.get('column') == (col.get('column_index', 0) + 1):
                        cell_value = cell_data.get('value', '')
                        break
                
                # Add tooltip (with formatted date labels)
                table_id = table.get('table_id', 'Unknown')
                row_label = row.get('row_label', row_idx + 1)
                col_label = col.get('column_label', col.get('column_index', 0) + 1)
                formatted_row_label = self._format_label_value(row_label) if row_label else str(row_idx + 1)
                formatted_col_label = self._format_label_value(col_label) if col_label else str(col.get('column_index', 0) + 1)
                title = f'Table: {table_id} | Row: {formatted_row_label} | Col: {formatted_col_label}'
                
                html_parts.append(f'<td title="{self._escape_html(title)}">{self._escape_html(cell_value)}</td>')
            
            html_parts.append('</tr>')
        
        html_parts.append('</tbody></table>')
        
        return '\n'.join(html_parts)
    
    def _render_excel_table(self, cell_map: Dict[int, Dict[int, Any]], table: Dict[str, Any]) -> str:
        """Render Excel table as HTML"""
        region = table.get('region', [])
        if len(region) != 4:
            return '<div class="muted">Invalid table region.</div>'
        
        r1, c1, r2, c2 = region
        headers = table.get('headers', {})
        header_rows = headers.get('rows', []) if isinstance(headers.get('rows'), list) else []
        
        # Compute trimmed region
        trimmed_region = self._compute_trimmed_region(cell_map, table)
        r1, c1, r2, c2_trim = trimmed_region
        
        html_parts = ['<table class="rendered">']
        
        # Create header
        if header_rows:
            html_parts.append('<thead>')
            for hr in header_rows:
                if hr < r1 or hr > r2:
                    continue
                html_parts.append('<tr>')
                for c in range(c1, c2_trim + 1):
                    header_val = self._get_cell_value(cell_map, hr, c)
                    formatted_val = self._format_label_value(header_val)
                    html_parts.append(f'<th>{self._escape_html(formatted_val)}</th>')
                html_parts.append('</tr>')
            html_parts.append('</thead>')
        
        # Create body
        html_parts.append('<tbody>')
        for r in range(r1, r2 + 1):
            if r in header_rows:
                continue
            
            html_parts.append('<tr>')
            for c in range(c1, c2_trim + 1):
                val = self._get_cell_value(cell_map, r, c)
                formatted_val = self._format_label_value(val)
                
                # Add tooltip with row/col labels (formatted for dates)
                row_label = self._get_row_label(table, r)
                col_label = self._get_col_label(table, c)
                formatted_row_label = self._format_label_value(row_label) if row_label else str(r)
                formatted_col_label = self._format_label_value(col_label) if col_label else str(c)
                title = f'Row: {formatted_row_label}, Col: {formatted_col_label}'
                
                html_parts.append(f'<td title="{self._escape_html(title)}">{self._escape_html(formatted_val)}</td>')
            
            html_parts.append('</tr>')
        
        html_parts.append('</tbody></table>')
        
        return '\n'.join(html_parts)
    
    def _highlight_numbers_in_text(self, text: str, numbers: List[Dict[str, Any]]) -> str:
        """Highlight numbers in text with colored spans"""
        if not text or not numbers:
            return self._escape_html(text or '')
        
        try:
            highlighted_text = self._escape_html(text)
            
            # Sort numbers by position to avoid overlapping replacements
            sorted_numbers = sorted(numbers, key=lambda n: 
                text.find(n.get('original_text', '')) if isinstance(n, dict) and n.get('original_text') else -1,
                reverse=True
            )
            
            for num in sorted_numbers:
                if not isinstance(num, dict) or not num.get('original_text'):
                    continue
                
                original_text = num['original_text']
                value = num.get('value', '')
                format_type = num.get('format', 'number')
                currency = num.get('currency')
                confidence = num.get('confidence')
                
                type_info = format_type
                if currency:
                    type_info += f' ({currency})'
                
                tooltip = f'Value: {value}'
                if confidence:
                    tooltip += f' | Confidence: {confidence * 100:.1f}%'
                tooltip += f' | Type: {type_info}'
                
                highlight_class = 'currency' if format_type == 'currency' else 'date' if format_type == 'date_number' else 'number'
                
                highlight_span = (
                    f'<span class="highlighted-number {highlight_class}" '
                    f'title="{self._escape_html(tooltip)}">{self._escape_html(original_text)}</span>'
                )
                
                escaped_original = self._escape_html(original_text)
                # Use more precise replacement to avoid corrupting already-generated HTML
                highlighted_text = self._safe_replace_text(highlighted_text, escaped_original, highlight_span)
            
            return highlighted_text
        
        except Exception as e:
            logger.error(f"Error highlighting numbers: {e}")
            return self._escape_html(text or '')
    
    def _generate_number_badge(self, num: Dict[str, Any]) -> str:
        """Generate HTML for number badge"""
        value = num.get('value') if isinstance(num, dict) else num
        original_text = num.get('original_text') if isinstance(num, dict) else str(num)
        format_type = num.get('format', 'number') if isinstance(num, dict) else 'number'
        currency = num.get('currency') if isinstance(num, dict) else None
        confidence = num.get('confidence') if isinstance(num, dict) else None
        
        display_text = original_text or str(value)
        type_info = format_type
        if currency:
            type_info += f' ({currency})'
        
        tooltip = f'Value: {value}'
        if confidence:
            tooltip += f' | Confidence: {confidence * 100:.1f}%'
        tooltip += f' | Type: {type_info}'
        
        return (
            f'<span class="number-badge" '
            f'style="display:inline-block; padding:0.3rem 0.6rem; background:rgba(59, 130, 246, 0.2); color:#f8fafc; border-radius:6px; font-size:0.8rem; font-weight:600; cursor:pointer; border:1px solid rgba(59, 130, 246, 0.4); box-shadow:0 2px 4px rgba(0, 0, 0, 0.3);" '
            f'title="{self._escape_html(tooltip)}">{self._escape_html(display_text)}</span>'
        )
    
    # Utility methods
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if text is None:
            return ''
        return html.escape(str(text))
    
    def _safe_replace_text(self, html_text: str, target: str, replacement: str) -> str:
        """
        Safely replace text in HTML without corrupting existing HTML tags or attributes.
        Only replaces text that appears outside of HTML tags.
        """
        import re
        
        if not target or target not in html_text:
            return html_text
        
        # More robust approach: split HTML into text and tag segments
        # and only replace text in the text segments
        parts = re.split(r'(<[^>]*>)', html_text)
        
        # Parts will alternate between text content and HTML tags
        # Even indices (0, 2, 4...) are text content
        # Odd indices (1, 3, 5...) are HTML tags
        
        replaced = False
        for i in range(len(parts)):
            if i % 2 == 0 and not replaced:  # Text content, not HTML tag
                if target in parts[i]:
                    # Replace only the first occurrence to maintain order
                    parts[i] = parts[i].replace(target, replacement, 1)
                    replaced = True
                    break
        
        return ''.join(parts)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if not size_bytes or size_bytes == 0:
            return '0 B'
        
        k = 1024
        sizes = ['B', 'KB', 'MB', 'GB']
        i = 0
        while size_bytes >= k and i < len(sizes) - 1:
            size_bytes /= k
            i += 1
        
        return f'{size_bytes:.1f} {sizes[i]}'
    
    def _format_date(self, date_string: str) -> str:
        """Format date string to YYYY-MM-DD"""
        try:
            if 'T' in date_string:
                date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                return date.strftime('%Y-%m-%d')
            return date_string
        except Exception:
            return date_string
    
    def _format_label_value(self, value: Any) -> str:
        """Format label value, handling dates specially"""
        if value is None:
            return ''
        
        str_val = str(value)
        # Check if it looks like a timestamp
        if str_val and str_val.count('-') >= 2 and 'T' in str_val:
            return self._format_date(str_val)
        
        return str_val
    
    def _get_cell_ref(self, row: int, col: int) -> str:
        """Convert row/col to Excel cell reference"""
        result = ''
        n = col
        while n > 0:
            n -= 1
            result = chr(65 + (n % 26)) + result
            n //= 26
        return result + str(row)
    
    def _compute_file_counts(self, sheets: List[Dict[str, Any]]) -> Dict[str, int]:
        """Compute file-level counts"""
        sheet_count = len(sheets)
        table_count = sum(len(sheet.get('tables', [])) for sheet in sheets)
        numeric_cells = sum(self._count_sheet_numeric(sheet) for sheet in sheets)
        
        return {
            'sheet_count': sheet_count,
            'table_count': table_count,
            'numeric_cells': numeric_cells
        }
    
    def _count_sheet_numeric(self, sheet: Dict[str, Any]) -> int:
        """Count numeric cells in a sheet"""
        count = 0
        cell_map = self._build_sheet_cell_map(sheet)
        
        for row_map in cell_map.values():
            for value in row_map.values():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    count += 1
        
        return count
    
    def _build_sheet_cell_map(self, sheet: Dict[str, Any]) -> Dict[int, Dict[int, Any]]:
        """Build cell map from sheet data"""
        cell_map = {}
        
        # Handle rows format
        if 'rows' in sheet and isinstance(sheet['rows'], list):
            for row in sheet['rows']:
                r = row.get('r')
                if r is not None:
                    if r not in cell_map:
                        cell_map[r] = {}
                    for cell in row.get('cells', []):
                        if len(cell) >= 2:
                            col, val = cell[0], cell[1]
                            cell_map[r][col] = val
        
        # Handle cells format (A1-style references)
        elif 'cells' in sheet and isinstance(sheet['cells'], dict):
            for ref, cell_data in sheet['cells'].items():
                row, col = self._cell_ref_to_row_col(ref)
                if row not in cell_map:
                    cell_map[row] = {}
                value = cell_data.get('value') if isinstance(cell_data, dict) else cell_data
                cell_map[row][col] = value
        
        return cell_map
    
    def _cell_ref_to_row_col(self, ref: str) -> tuple:
        """Convert A1-style reference to row, col"""
        import re
        match = re.match(r'^([A-Za-z]+)(\d+)$', ref)
        if not match:
            return 0, 0
        
        letters, digits = match.groups()
        col = 0
        for char in letters.upper():
            col = col * 26 + (ord(char) - ord('A') + 1)
        row = int(digits)
        
        return row, col
    
    def _get_cell_value(self, cell_map: Dict[int, Dict[int, Any]], row: int, col: int) -> Any:
        """Get cell value from cell map"""
        return cell_map.get(row, {}).get(col, '')
    
    def _compute_trimmed_region(self, cell_map: Dict[int, Dict[int, Any]], table_def: Dict[str, Any]) -> List[int]:
        """Compute trimmed region for table with aggressive empty column removal"""
        region = table_def.get('region', [])
        if len(region) != 4:
            return region
        
        r1, c1, r2, c2 = region
        headers = table_def.get('headers', {})
        header_rows = headers.get('rows', []) if isinstance(headers.get('rows'), list) else []
        
        # Find last non-empty column (more aggressive)
        last_non_empty = c1
        
        # Count columns with meaningful data
        for c in range(c2, c1 - 1, -1):
            found = False
            cell_count = 0
            non_empty_count = 0
            
            # Check all rows for this column
            for r in range(r1, r2 + 1):
                cell_count += 1
                value = self._get_cell_value(cell_map, r, c)
                if self._is_meaningful_cell(value):
                    non_empty_count += 1
                    found = True
            
            # Only keep column if it has meaningful data in multiple cells
            # or if it's in the first few columns (likely important structure)
            if found and (non_empty_count > 1 or c - c1 < 3):
                last_non_empty = c
                break
        
        # Ensure we don't trim too aggressively - keep at least 3 columns if possible
        if last_non_empty - c1 < 2 and c2 - c1 >= 2:
            last_non_empty = min(c2, c1 + 2)
        
        return [r1, c1, r2, last_non_empty]
    
    def _is_non_empty(self, value: Any) -> bool:
        """Check if value is non-empty"""
        return value is not None and str(value).strip() != ''
    
    def _is_meaningful_cell(self, value: Any) -> bool:
        """Check if cell contains meaningful data (more strict than just non-empty)"""
        if value is None:
            return False
        
        str_val = str(value).strip()
        if not str_val:
            return False
        
        # Consider meaningful if it's a number, has multiple characters, or contains alphanumeric
        if str_val.replace('.', '').replace('-', '').replace(',', '').isdigit():
            return True  # Number
        if len(str_val) > 1:
            return True  # Multi-character content
        if str_val.isalnum():
            return True  # Single letter/digit
        
        return False
    
    def _get_row_label(self, table_def: Dict[str, Any], row: int) -> Optional[str]:
        """Get row label for table"""
        try:
            labels = table_def.get('labels', {})
            rows = labels.get('rows', []) if isinstance(labels.get('rows'), list) else []
            headers = table_def.get('headers', {})
            data_start = headers.get('data_start')
            
            if isinstance(data_start, list) and len(data_start) >= 2:
                offset = row - data_start[0]
                if 0 <= offset < len(rows):
                    return str(rows[offset])
        except Exception:
            pass
        return None
    
    def _get_col_label(self, table_def: Dict[str, Any], col: int) -> Optional[str]:
        """Get column label for table"""
        try:
            labels = table_def.get('labels', {})
            cols = labels.get('cols', []) if isinstance(labels.get('cols'), list) else []
            region = table_def.get('region')
            
            if isinstance(region, list) and len(region) >= 4:
                offset = col - region[1]
                if 0 <= offset < len(cols):
                    return str(cols[offset])
        except Exception:
            pass
        return None
    
    def _generate_table_detail(self, table: Dict[str, Any], idx: int) -> str:
        """Generate detailed table information HTML"""
        table_name = table.get('name') or table.get('id') or f'Table {idx + 1}'
        region = table.get('region')
        
        html_parts = [
            '<div style="margin:0.5rem 0; padding:0.75rem; border:1px solid rgba(59, 130, 246, 0.2); border-radius:8px; background:rgba(30, 41, 59, 0.8);">',
            f'<div style="color:#f8fafc; font-weight:600; margin-bottom:0.5rem;">{self._escape_html(table_name)}</div>'
        ]
        
        # Remove all metadata sections - they are not useful and don't follow the color scheme
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _collect_pdf_text_sections(self, pdf_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect PDF text sections with content or numbers"""
        sections = []
        
        try:
            text_content = pdf_result.get('text_content', {})
            pages = text_content.get('pages', [])
            
            for page_idx, page in enumerate(pages):
                page_sections = page.get('sections', [])
                
                for section_idx, section in enumerate(page_sections):
                    content = section.get('content', '')
                    numbers = section.get('numbers', [])
                    
                    if content.strip() or numbers:
                        sections.append({
                            'content': content,
                            'numbers': numbers,
                            'page': page.get('page_number', page_idx + 1),
                            'section_id': section.get('section_id', f'page_{page_idx + 1}_section_{section_idx + 1}')
                        })
        
        except Exception as e:
            logger.error(f"Error collecting PDF text sections: {e}")
        
        return sections
