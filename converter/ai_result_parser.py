"""
AI Result Parser

This module parses and validates AI analysis results, converting them into
formats compatible with the existing table processing pipeline.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class AIResultParser:
    """
    Parser for AI table analysis results.
    
    This class converts AI-generated table analysis into standardized formats
    that can be compared with traditional heuristic results and integrated
    into the existing processing pipeline.
    """
    
    def __init__(self):
        """Initialize the AI result parser."""
        self.validation_errors = []
        self.warnings = []
    
    def parse_excel_analysis(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse AI Excel analysis response into standardized format.
        
        Args:
            ai_response: Raw AI response from AnthropicExcelClient
            
        Returns:
            Parsed and validated analysis result
        """
        self.validation_errors = []
        self.warnings = []
        
        if ai_response.get('status') != 'success':
            return self._handle_failed_response(ai_response)
        
        raw_result = ai_response.get('result', {})
        
        # Parse the main components
        parsed_tables = self._parse_detected_tables(raw_result.get('tables_detected', []))
        sheet_analysis = self._parse_sheet_analysis(raw_result.get('sheet_analysis', {}))
        
        # Create standardized result
        standardized_result = {
            'ai_analysis': {
                'tables': parsed_tables,
                'sheet_summary': sheet_analysis,
                'confidence': raw_result.get('analysis_confidence', 0.0),
                'processing_notes': raw_result.get('processing_notes', [])
            },
            'table_count': len(parsed_tables),
            'high_confidence_tables': len([t for t in parsed_tables if t.get('confidence', 0) > 0.7]),
            'complexity_assessment': self._assess_complexity(parsed_tables, sheet_analysis),
            'processing_recommendation': sheet_analysis.get('recommended_processing', 'traditional'),
            'validation': {
                'errors': self.validation_errors,
                'warnings': self.warnings,
                'valid': len(self.validation_errors) == 0
            },
            'metadata': {
                'parsed_at': datetime.now().isoformat(),
                'ai_metadata': ai_response.get('ai_metadata', {}),
                'raw_response_status': ai_response.get('status', 'unknown')
            }
        }
        
        # Add converted tables for comparison
        standardized_result['converted_tables'] = self._convert_to_traditional_format(parsed_tables)
        
        return standardized_result
    
    def _parse_detected_tables(self, tables_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse the detected tables from AI response."""
        parsed_tables = []
        
        for i, table in enumerate(tables_data):
            try:
                parsed_table = self._parse_single_table(table, i)
                if parsed_table:
                    parsed_tables.append(parsed_table)
            except Exception as e:
                self.validation_errors.append(f"Error parsing table {i}: {str(e)}")
        
        return parsed_tables
    
    def _parse_single_table(self, table_data: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Parse a single table from AI response."""
        table_id = table_data.get('table_id', f'ai_table_{index}')
        
        # Validate required fields
        if 'boundaries' not in table_data:
            self.validation_errors.append(f"Table {table_id}: Missing boundaries")
            return None
        
        boundaries = table_data['boundaries']
        required_boundary_fields = ['start_row', 'end_row', 'start_col', 'end_col']
        
        for field in required_boundary_fields:
            if field not in boundaries:
                self.validation_errors.append(f"Table {table_id}: Missing boundary field {field}")
                return None
        
        # Validate boundary values
        try:
            start_row = int(boundaries['start_row'])
            end_row = int(boundaries['end_row'])
            start_col = int(boundaries['start_col'])
            end_col = int(boundaries['end_col'])
            
            if start_row > end_row or start_col > end_col:
                self.validation_errors.append(f"Table {table_id}: Invalid boundaries")
                return None
                
        except (ValueError, TypeError):
            self.validation_errors.append(f"Table {table_id}: Invalid boundary values")
            return None
        
        # Parse headers
        headers = self._parse_table_headers(table_data.get('headers', {}), table_id)
        
        # Parse data area
        data_area = table_data.get('data_area', boundaries.copy())
        
        # Create parsed table
        parsed_table = {
            'id': table_id,
            'name': table_data.get('name', f'AI Table {index + 1}'),
            'boundaries': {
                'start_row': start_row,
                'end_row': end_row,
                'start_col': start_col,
                'end_col': end_col
            },
            'data_area': {
                'start_row': int(data_area.get('start_row', start_row)),
                'end_row': int(data_area.get('end_row', end_row)),
                'start_col': int(data_area.get('start_col', start_col)),
                'end_col': int(data_area.get('end_col', end_col))
            },
            'headers': headers,
            'table_type': table_data.get('table_type', 'unknown'),
            'confidence': min(max(table_data.get('confidence', 0.5), 0.0), 1.0),
            'complexity_indicators': table_data.get('complexity_indicators', []),
            'data_quality': self._parse_data_quality(table_data.get('data_quality', {})),
            'dimensions': {
                'rows': end_row - start_row + 1,
                'cols': end_col - start_col + 1,
                'total_cells': (end_row - start_row + 1) * (end_col - start_col + 1)
            }
        }
        
        return parsed_table
    
    def _parse_table_headers(self, headers_data: Dict[str, Any], table_id: str) -> Dict[str, Any]:
        """Parse table headers from AI response."""
        parsed_headers = {
            'row_headers': [],
            'column_headers': [],
            'header_levels': 0,
            'has_headers': False
        }
        
        # Parse row headers
        row_headers = headers_data.get('row_headers', [])
        for header in row_headers:
            try:
                parsed_row_header = {
                    'row': int(header.get('row', 0)),
                    'columns': header.get('columns', []),
                    'level': int(header.get('level', 1))
                }
                parsed_headers['row_headers'].append(parsed_row_header)
                parsed_headers['header_levels'] = max(
                    parsed_headers['header_levels'], 
                    parsed_row_header['level']
                )
            except (ValueError, TypeError):
                self.warnings.append(f"Table {table_id}: Invalid row header data")
        
        # Parse column headers
        col_headers = headers_data.get('column_headers', [])
        for header in col_headers:
            try:
                parsed_col_header = {
                    'col': int(header.get('col', 0)),
                    'rows': header.get('rows', []),
                    'level': int(header.get('level', 1))
                }
                parsed_headers['column_headers'].append(parsed_col_header)
                parsed_headers['header_levels'] = max(
                    parsed_headers['header_levels'], 
                    parsed_col_header['level']
                )
            except (ValueError, TypeError):
                self.warnings.append(f"Table {table_id}: Invalid column header data")
        
        parsed_headers['has_headers'] = (
            len(parsed_headers['row_headers']) > 0 or 
            len(parsed_headers['column_headers']) > 0
        )
        
        return parsed_headers
    
    def _parse_data_quality(self, quality_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse data quality metrics."""
        return {
            'completeness': min(max(quality_data.get('completeness', 0.8), 0.0), 1.0),
            'consistency': min(max(quality_data.get('consistency', 0.8), 0.0), 1.0),
            'data_types': quality_data.get('data_types', ['text', 'number'])
        }
    
    def _parse_sheet_analysis(self, sheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse sheet-level analysis."""
        return {
            'total_tables': int(sheet_data.get('total_tables', 0)),
            'data_density': min(max(sheet_data.get('data_density', 0.5), 0.0), 1.0),
            'structure_complexity': sheet_data.get('structure_complexity', 'unknown'),
            'recommended_processing': sheet_data.get('recommended_processing', 'traditional')
        }
    
    def _assess_complexity(self, tables: List[Dict[str, Any]], sheet_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall complexity based on parsed results."""
        if not tables:
            return {
                'level': 'simple',
                'score': 0.0,
                'factors': ['no_tables_detected']
            }
        
        complexity_factors = []
        complexity_score = 0.0
        
        # Analyze table-level complexity
        for table in tables:
            # Multi-level headers
            header_levels = table.get('headers', {}).get('header_levels', 0)
            if header_levels > 1:
                complexity_factors.append('multi_level_headers')
                complexity_score += 0.1
            
            # Complexity indicators
            indicators = table.get('complexity_indicators', [])
            for indicator in indicators:
                if indicator not in complexity_factors:
                    complexity_factors.append(indicator)
                    complexity_score += 0.05
            
            # Large tables
            dimensions = table.get('dimensions', {})
            total_cells = dimensions.get('total_cells', 0)
            if total_cells > 1000:
                complexity_factors.append('large_table')
                complexity_score += 0.05
        
        # Sheet-level complexity
        structure_complexity = sheet_analysis.get('structure_complexity', 'simple')
        if structure_complexity == 'complex':
            complexity_score += 0.15
        elif structure_complexity == 'moderate':
            complexity_score += 0.08
        
        # Multiple tables
        if len(tables) > 3:
            complexity_factors.append('multiple_tables')
            complexity_score += 0.1
        
        # Determine complexity level
        if complexity_score >= 0.3:
            level = 'complex'
        elif complexity_score >= 0.15:
            level = 'moderate'
        else:
            level = 'simple'
        
        return {
            'level': level,
            'score': min(complexity_score, 1.0),
            'factors': complexity_factors
        }
    
    def _convert_to_traditional_format(self, ai_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert AI table results to traditional table format for comparison.
        
        This enables direct comparison with existing heuristic results.
        """
        traditional_tables = []
        
        for ai_table in ai_tables:
            # Convert to format similar to TableDetector output
            traditional_table = {
                'table_name': ai_table.get('name', 'AI Detected Table'),
                'start_row': ai_table['boundaries']['start_row'],
                'end_row': ai_table['boundaries']['end_row'],
                'start_col': ai_table['boundaries']['start_col'],
                'end_col': ai_table['boundaries']['end_col'],
                'header_rows': self._extract_header_rows(ai_table.get('headers', {})),
                'data_start_row': ai_table['data_area']['start_row'],
                'data_end_row': ai_table['data_area']['end_row'],
                'detection_method': 'ai_analysis',
                'confidence': ai_table.get('confidence', 0.5),
                'table_type': ai_table.get('table_type', 'unknown'),
                'source': 'anthropic_ai'
            }
            
            traditional_tables.append(traditional_table)
        
        return traditional_tables
    
    def _extract_header_rows(self, headers: Dict[str, Any]) -> List[int]:
        """Extract header row numbers from headers data."""
        header_rows = set()
        
        for row_header in headers.get('row_headers', []):
            header_rows.add(row_header.get('row', 0))
        
        # Also include column header rows
        for col_header in headers.get('column_headers', []):
            for row_data in col_header.get('rows', []):
                if isinstance(row_data, dict) and 'row' in row_data:
                    header_rows.add(row_data['row'])
        
        return sorted(list(header_rows))
    
    def _handle_failed_response(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed AI responses."""
        status = ai_response.get('status', 'unknown')
        message = ai_response.get('message', 'Unknown error')
        
        return {
            'ai_analysis': {
                'tables': [],
                'sheet_summary': {
                    'total_tables': 0,
                    'structure_complexity': 'unknown',
                    'recommended_processing': 'traditional'
                },
                'confidence': 0.0,
                'processing_notes': [f"AI analysis failed: {message}"]
            },
            'table_count': 0,
            'high_confidence_tables': 0,
            'complexity_assessment': {
                'level': 'unknown',
                'score': 0.0,
                'factors': ['ai_analysis_failed']
            },
            'processing_recommendation': 'traditional',
            'validation': {
                'errors': [f"AI analysis failed with status: {status}"],
                'warnings': [],
                'valid': False
            },
            'metadata': {
                'parsed_at': datetime.now().isoformat(),
                'ai_metadata': ai_response.get('ai_metadata', {}),
                'raw_response_status': status,
                'failure_reason': message
            },
            'converted_tables': []
        }
    
    def compare_with_traditional(self, 
                               ai_result: Dict[str, Any], 
                               traditional_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare AI results with traditional heuristic results.
        
        This generates comparison metrics for tuning and evaluation.
        """
        ai_tables = ai_result.get('converted_tables', [])
        traditional_tables = traditional_result.get('tables', [])
        
        comparison = {
            'table_count_comparison': {
                'ai_count': len(ai_tables),
                'traditional_count': len(traditional_tables),
                'difference': len(ai_tables) - len(traditional_tables)
            },
            'boundary_overlap': self._calculate_boundary_overlap(ai_tables, traditional_tables),
            'detection_agreement': self._calculate_detection_agreement(ai_tables, traditional_tables),
            'confidence_analysis': self._analyze_confidence_distribution(ai_tables),
            'complexity_comparison': {
                'ai_complexity': ai_result.get('complexity_assessment', {}),
                'traditional_success': len(traditional_tables) > 0
            },
            'recommendation_alignment': self._check_recommendation_alignment(ai_result, traditional_result)
        }
        
        # Overall comparison score
        comparison['overall_agreement'] = self._calculate_overall_agreement(comparison)
        
        return comparison
    
    def _calculate_boundary_overlap(self, ai_tables: List[Dict], traditional_tables: List[Dict]) -> Dict[str, Any]:
        """Calculate how much AI and traditional table boundaries overlap."""
        if not ai_tables or not traditional_tables:
            return {'average_overlap': 0.0, 'overlapping_pairs': 0, 'total_comparisons': 0}
        
        overlaps = []
        overlapping_pairs = 0
        
        for ai_table in ai_tables:
            best_overlap = 0.0
            for trad_table in traditional_tables:
                overlap = self._calculate_table_overlap(ai_table, trad_table)
                best_overlap = max(best_overlap, overlap)
            
            overlaps.append(best_overlap)
            if best_overlap > 0.5:
                overlapping_pairs += 1
        
        return {
            'average_overlap': sum(overlaps) / len(overlaps) if overlaps else 0.0,
            'overlapping_pairs': overlapping_pairs,
            'total_comparisons': len(ai_tables)
        }
    
    def _calculate_table_overlap(self, table1: Dict[str, Any], table2: Dict[str, Any]) -> float:
        """Calculate overlap between two table boundaries."""
        # Get boundaries
        t1_start_row = table1.get('start_row', 0)
        t1_end_row = table1.get('end_row', 0)
        t1_start_col = table1.get('start_col', 0)
        t1_end_col = table1.get('end_col', 0)
        
        t2_start_row = table2.get('start_row', 0)
        t2_end_row = table2.get('end_row', 0)
        t2_start_col = table2.get('start_col', 0)
        t2_end_col = table2.get('end_col', 0)
        
        # Calculate intersection
        intersect_start_row = max(t1_start_row, t2_start_row)
        intersect_end_row = min(t1_end_row, t2_end_row)
        intersect_start_col = max(t1_start_col, t2_start_col)
        intersect_end_col = min(t1_end_col, t2_end_col)
        
        # Check if there's any intersection
        if intersect_start_row > intersect_end_row or intersect_start_col > intersect_end_col:
            return 0.0
        
        # Calculate areas
        intersect_area = (intersect_end_row - intersect_start_row + 1) * (intersect_end_col - intersect_start_col + 1)
        t1_area = (t1_end_row - t1_start_row + 1) * (t1_end_col - t1_start_col + 1)
        t2_area = (t2_end_row - t2_start_row + 1) * (t2_end_col - t2_start_col + 1)
        
        # Calculate overlap as intersection over union
        union_area = t1_area + t2_area - intersect_area
        
        return intersect_area / union_area if union_area > 0 else 0.0
    
    def _calculate_detection_agreement(self, ai_tables: List[Dict], traditional_tables: List[Dict]) -> float:
        """Calculate overall detection agreement between AI and traditional methods."""
        if not ai_tables and not traditional_tables:
            return 1.0  # Both found nothing
        
        if not ai_tables or not traditional_tables:
            return 0.0  # One found something, other didn't
        
        # Count significant overlaps
        significant_overlaps = 0
        for ai_table in ai_tables:
            for trad_table in traditional_tables:
                if self._calculate_table_overlap(ai_table, trad_table) > 0.5:
                    significant_overlaps += 1
                    break
        
        # Agreement based on proportion of AI tables with significant traditional overlap
        return significant_overlaps / len(ai_tables)
    
    def _analyze_confidence_distribution(self, ai_tables: List[Dict]) -> Dict[str, Any]:
        """Analyze confidence distribution of AI detections."""
        if not ai_tables:
            return {'average': 0.0, 'high_confidence_count': 0, 'low_confidence_count': 0}
        
        confidences = [table.get('confidence', 0.5) for table in ai_tables]
        
        return {
            'average': sum(confidences) / len(confidences),
            'high_confidence_count': len([c for c in confidences if c > 0.7]),
            'low_confidence_count': len([c for c in confidences if c < 0.3]),
            'distribution': confidences
        }
    
    def _check_recommendation_alignment(self, ai_result: Dict[str, Any], traditional_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if AI and traditional processing recommendations align."""
        ai_recommendation = ai_result.get('processing_recommendation', 'traditional')
        traditional_success = len(traditional_result.get('tables', [])) > 0
        
        # Expected recommendation based on traditional success
        if traditional_success:
            expected_ai_recommendation = 'traditional'
        else:
            expected_ai_recommendation = 'ai_assisted'
        
        alignment = ai_recommendation == expected_ai_recommendation
        
        return {
            'ai_recommendation': ai_recommendation,
            'traditional_success': traditional_success,
            'expected_recommendation': expected_ai_recommendation,
            'aligned': alignment
        }
    
    def _calculate_overall_agreement(self, comparison: Dict[str, Any]) -> float:
        """Calculate overall agreement score between AI and traditional methods."""
        # Weight different factors
        weights = {
            'detection_agreement': 0.4,
            'boundary_overlap': 0.3,
            'recommendation_alignment': 0.3
        }
        
        detection_agreement = comparison.get('detection_agreement', 0.0)
        boundary_overlap = comparison.get('boundary_overlap', {}).get('average_overlap', 0.0)
        recommendation_alignment = 1.0 if comparison.get('recommendation_alignment', {}).get('aligned', False) else 0.0
        
        overall_score = (
            detection_agreement * weights['detection_agreement'] +
            boundary_overlap * weights['boundary_overlap'] +
            recommendation_alignment * weights['recommendation_alignment']
        )
        
        return overall_score

