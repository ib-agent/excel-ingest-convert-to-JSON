"""
Metadata Analyzer for Enhanced UI Display

This module provides comprehensive metadata analysis for processed documents,
extracting key statistics and information for display in the enhanced UI.
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import re


class MetadataAnalyzer:
    """Analyzes processed document metadata and extracts key statistics."""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
    
    def analyze_run(self, run_dir: str) -> Dict[str, Any]:
        """
        Analyze a complete run and extract comprehensive metadata.
        
        Args:
            run_dir: The run directory name
            
        Returns:
            Dict containing enhanced metadata with statistics
        """
        run_path = os.path.join(self.storage_path, run_dir)
        
        # Load base metadata
        meta_file = os.path.join(run_path, 'meta.json')
        if not os.path.exists(meta_file):
            return {}
        
        with open(meta_file, 'r') as f:
            base_meta = json.load(f)
        
        # Load processed data for analysis
        processed_file = os.path.join(run_path, 'processed.json')
        processed_data = {}
        if os.path.exists(processed_file):
            with open(processed_file, 'r') as f:
                processed_data = json.load(f)
        
        # Load table data for analysis
        table_file = os.path.join(run_path, 'table_data.json')
        table_data = {}
        if os.path.exists(table_file):
            with open(table_file, 'r') as f:
                table_data = json.load(f)
        
        # Calculate file sizes
        file_sizes = self._calculate_file_sizes(run_path)
        
        # Extract statistics based on file type
        file_type = base_meta.get('file_type', 'unknown')
        if file_type == 'pdf':
            stats = self._analyze_pdf_data(processed_data, table_data)
        elif file_type == 'excel':
            stats = self._analyze_excel_data(processed_data, table_data)
        else:
            stats = {}
        
        # Calculate processing time if available
        processing_time = self._calculate_processing_time(base_meta)
        
        # Combine all metadata
        enhanced_meta = {
            **base_meta,
            'file_sizes': file_sizes,
            'processing_time': processing_time,
            'statistics': stats,
            'analysis_timestamp': datetime.now().isoformat(),
        }
        
        return enhanced_meta
    
    def _calculate_file_sizes(self, run_path: str) -> Dict[str, int]:
        """Calculate sizes of all artifacts in the run."""
        sizes = {}
        for filename in ['original.pdf', 'original.xlsx', 'processed.json', 
                        'table_data.json', 'display.html', 'meta.json']:
            file_path = os.path.join(run_path, filename)
            if os.path.exists(file_path):
                sizes[filename] = os.path.getsize(file_path)
        return sizes
    
    def _calculate_processing_time(self, meta: Dict[str, Any]) -> Optional[str]:
        """Calculate processing time if timestamps are available."""
        duration_seconds = meta.get('processing_duration_seconds')
        if duration_seconds is not None:
            return self._format_duration(duration_seconds)
        
        # Fallback: try to calculate from start/end timestamps
        created_at = meta.get('created_at')
        completed_at = meta.get('completed_at')
        if created_at and completed_at:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                end = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                duration = (end - start).total_seconds()
                return self._format_duration(duration)
            except Exception:
                pass
        
        return None
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        if seconds < 1:
            return f"{int(seconds * 1000)}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            if remaining_seconds < 1:
                return f"{minutes}m"
            return f"{minutes}m {remaining_seconds:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _analyze_pdf_data(self, processed_data: Dict[str, Any], 
                         table_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze PDF-specific data and extract statistics."""
        stats = {
            'document_type': 'PDF',
            'total_pages': 0,
            'total_tables': 0,
            'total_text_sections': 0,
            'total_numbers': 0,
            'total_words': 0,
            'table_cells': 0,
            'currency_values': 0,
            'date_values': 0,
        }
        
        # Analyze PDF processing result
        pdf_result = processed_data.get('pdf_processing_result', {})
        
        # Count pages from document metadata
        doc_meta = pdf_result.get('document_metadata', {})
        if 'total_pages' in doc_meta:
            stats['total_pages'] = doc_meta['total_pages']
        
        # Count tables
        if 'tables' in pdf_result:
            tables = pdf_result['tables']
            stats['total_tables'] = len(tables)
            
            # Count table cells
            for table in tables:
                if isinstance(table, dict) and 'data' in table:
                    table_data_rows = table['data']
                    if isinstance(table_data_rows, list):
                        for row in table_data_rows:
                            if isinstance(row, dict) and 'cells' in row:
                                stats['table_cells'] += len(row['cells'])
        
        # Count text sections from text_content
        if 'text_content' in pdf_result:
            text_content = pdf_result['text_content']
            if isinstance(text_content, dict) and 'pages' in text_content:
                for page in text_content['pages']:
                    if isinstance(page, dict) and 'sections' in page:
                        stats['total_text_sections'] += len(page['sections'])
                        
                        # Analyze each section
                        for section in page['sections']:
                            if isinstance(section, dict):
                                content = section.get('content', '')
                                stats['total_words'] += len(content.split())
                                
                                # Count numbers from extracted_numbers
                                if 'extracted_numbers' in section:
                                    numbers = section['extracted_numbers']
                                    if isinstance(numbers, list):
                                        stats['total_numbers'] += len(numbers)
                                        
                                        # Count specific number types
                                        for num_info in numbers:
                                            if isinstance(num_info, dict):
                                                num_type = num_info.get('type', '')
                                                if 'currency' in num_type.lower():
                                                    stats['currency_values'] += 1
                                                elif 'date' in num_type.lower():
                                                    stats['date_values'] += 1
        
        # Additional comprehensive number count from entire structure
        total_numbers = self._count_numbers_in_data(pdf_result)
        if total_numbers > stats['total_numbers']:
            stats['total_numbers'] = total_numbers
        
        return stats
    
    def _analyze_excel_data(self, processed_data: Dict[str, Any], 
                           table_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Excel-specific data and extract statistics."""
        stats = {
            'document_type': 'Excel',
            'total_sheets': 0,
            'total_tables': 0,
            'total_cells': 0,
            'total_numbers': 0,
            'formula_cells': 0,
            'non_empty_cells': 0,
            'merged_cells': 0,
            'frozen_panes_sheets': 0,
        }
        
        workbook = processed_data.get('workbook', {})
        
        # Count sheets
        sheets = workbook.get('sheets', [])
        stats['total_sheets'] = len(sheets)
        
        # Analyze each sheet
        for sheet in sheets:
            # Count cells
            if 'rows' in sheet:
                for row in sheet['rows']:
                    if 'cells' in row and row['cells']:
                        cells = row['cells']
                        if isinstance(cells, list):
                            stats['total_cells'] += len(cells)
                            # Count non-empty cells
                            for cell in cells:
                                if len(cell) > 1 and cell[1] is not None and cell[1] != '':
                                    stats['non_empty_cells'] += 1
                                # Count formulas (typically in index 3)
                                if len(cell) > 3 and cell[3]:
                                    stats['formula_cells'] += 1
            
            # Count merged cells
            if 'merged_cells' in sheet:
                stats['merged_cells'] += len(sheet['merged_cells'])
            
            # Check for frozen panes
            if 'frozen' in sheet and sheet['frozen']:
                stats['frozen_panes_sheets'] += 1
        
        # Count tables from table data
        if table_data and 'tables' in table_data:
            stats['total_tables'] = len(table_data['tables'])
        
        # Count numerical values
        stats['total_numbers'] = self._count_numbers_in_data(processed_data)
        
        # Add complexity metadata if available
        complexity = processed_data.get('complexity_metadata', {})
        if complexity:
            stats['complexity_score'] = complexity.get('overall_complexity', 0)
            stats['has_complex_formulas'] = complexity.get('has_complex_formulas', False)
        
        return stats
    
    def _count_numbers_in_data(self, data: Any, count: int = 0) -> int:
        """Recursively count numerical values in data structure."""
        if isinstance(data, (int, float)) and not isinstance(data, bool):
            return count + 1
        elif isinstance(data, dict):
            for value in data.values():
                count = self._count_numbers_in_data(value, count)
        elif isinstance(data, list):
            for item in data:
                count = self._count_numbers_in_data(item, count)
        return count
    
    def get_display_summary(self, enhanced_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a display-ready summary of the metadata.
        
        Args:
            enhanced_meta: Enhanced metadata from analyze_run()
            
        Returns:
            Dict with formatted display information
        """
        stats = enhanced_meta.get('statistics', {})
        file_type = enhanced_meta.get('file_type', 'unknown')
        
        # Format file size
        original_size = enhanced_meta.get('file_sizes', {})
        original_file_key = f'original.{file_type}' if file_type in ['pdf'] else 'original.xlsx'
        file_size = original_size.get(original_file_key, 0)
        file_size_str = self._format_file_size(file_size)
        
        # Create display summary
        summary = {
            'filename': enhanced_meta.get('filename', 'Unknown'),
            'file_type': file_type.upper(),
            'file_size': file_size_str,
            'processing_duration': enhanced_meta.get('processing_time', 'N/A'),
        }
        
        # Add type-specific stats
        if file_type == 'pdf':
            summary.update({
                'total_pages': stats.get('total_pages', 0),
                'total_tables': stats.get('total_tables', 0),
                'text_sections': stats.get('total_text_sections', 0),
                'numerical_values': stats.get('total_numbers', 0),
                'currency_values': stats.get('currency_values', 0),
            })
        elif file_type == 'excel':
            summary.update({
                'total_sheets': stats.get('total_sheets', 0),
                'total_tables': stats.get('total_tables', 0),
                'non_empty_cells': stats.get('non_empty_cells', 0),
                'numerical_values': stats.get('total_numbers', 0),
                'formula_cells': stats.get('formula_cells', 0),
            })
        
        return summary
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
