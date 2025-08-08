"""
Comparison Engine

This module compares results between traditional heuristic methods and AI analysis,
providing detailed metrics for tuning and test case generation.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import statistics
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComparisonMetrics:
    """Data class for comparison metrics."""
    agreement_score: float
    table_count_difference: int
    boundary_overlap_score: float
    confidence_score: float
    complexity_alignment: float
    recommendation_accuracy: float


class ComparisonEngine:
    """
    Engine for comparing traditional heuristic and AI analysis results.
    
    This class provides comprehensive comparison capabilities for evaluating
    AI performance against traditional methods and generating insights for
    system improvement.
    """
    
    def __init__(self):
        """Initialize the comparison engine."""
        self.comparison_history = []
        self.performance_metrics = {
            'total_comparisons': 0,
            'ai_advantages': 0,
            'traditional_advantages': 0,
            'agreements': 0
        }
    
    def compare_analysis_results(self, 
                                traditional_result: Dict[str, Any],
                                ai_result: Dict[str, Any],
                                complexity_metadata: Optional[Dict[str, Any]] = None,
                                sheet_name: str = "Unknown") -> Dict[str, Any]:
        """
        Perform comprehensive comparison between traditional and AI results.
        
        Args:
            traditional_result: Result from traditional heuristic analysis
            ai_result: Result from AI analysis
            complexity_metadata: Optional complexity metadata
            sheet_name: Name of the analyzed sheet
            
        Returns:
            Comprehensive comparison analysis
        """
        comparison_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{sheet_name}"
        
        # Extract table information
        traditional_tables = self._extract_traditional_tables(traditional_result)
        ai_tables = self._extract_ai_tables(ai_result)
        
        # Core comparison metrics
        table_comparison = self._compare_table_detection(traditional_tables, ai_tables)
        boundary_comparison = self._compare_table_boundaries(traditional_tables, ai_tables)
        quality_comparison = self._compare_result_quality(traditional_result, ai_result)
        performance_comparison = self._compare_performance_indicators(traditional_result, ai_result)
        
        # Advanced analysis
        complexity_analysis = self._analyze_complexity_handling(
            traditional_tables, ai_tables, complexity_metadata
        )
        
        failure_analysis = self._analyze_failure_patterns(
            traditional_tables, ai_tables, complexity_metadata
        )
        
        recommendation_analysis = self._analyze_processing_recommendations(
            traditional_result, ai_result, complexity_metadata
        )
        
        # Calculate overall metrics
        overall_metrics = self._calculate_overall_metrics(
            table_comparison, boundary_comparison, quality_comparison, 
            performance_comparison, complexity_analysis
        )
        
        # Create comprehensive comparison result
        comparison_result = {
            'comparison_id': comparison_id,
            'timestamp': datetime.now().isoformat(),
            'sheet_name': sheet_name,
            'summary': {
                'traditional_tables_found': len(traditional_tables),
                'ai_tables_found': len(ai_tables),
                'agreement_score': overall_metrics.agreement_score,
                'winner': self._determine_winner(overall_metrics, traditional_tables, ai_tables),
                'complexity_level': self._get_complexity_level(complexity_metadata)
            },
            'detailed_analysis': {
                'table_detection': table_comparison,
                'boundary_analysis': boundary_comparison,
                'quality_metrics': quality_comparison,
                'performance_indicators': performance_comparison,
                'complexity_handling': complexity_analysis,
                'failure_analysis': failure_analysis,
                'recommendation_analysis': recommendation_analysis
            },
            'metrics': {
                'agreement_score': overall_metrics.agreement_score,
                'table_count_difference': overall_metrics.table_count_difference,
                'boundary_overlap_score': overall_metrics.boundary_overlap_score,
                'confidence_score': overall_metrics.confidence_score,
                'complexity_alignment': overall_metrics.complexity_alignment,
                'recommendation_accuracy': overall_metrics.recommendation_accuracy
            },
            'insights': self._generate_insights(overall_metrics, traditional_tables, ai_tables, complexity_metadata),
            'test_case_potential': self._assess_test_case_potential(overall_metrics, traditional_tables, ai_tables),
            'tuning_recommendations': self._generate_tuning_recommendations(overall_metrics, complexity_metadata)
        }
        
        # Update performance tracking
        self._update_performance_tracking(comparison_result)
        
        # Store in history
        self.comparison_history.append(comparison_result)
        
        return comparison_result
    
    def _extract_traditional_tables(self, traditional_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract table information from traditional heuristic results."""
        # Handle different possible formats
        if 'tables' in traditional_result:
            return traditional_result['tables']
        elif 'detected_tables' in traditional_result:
            return traditional_result['detected_tables']
        else:
            return []
    
    def _extract_ai_tables(self, ai_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract table information from AI analysis results."""
        if 'converted_tables' in ai_result:
            return ai_result['converted_tables']
        elif 'ai_analysis' in ai_result and 'tables' in ai_result['ai_analysis']:
            return ai_result['ai_analysis']['tables']
        else:
            return []
    
    def _compare_table_detection(self, traditional_tables: List[Dict], ai_tables: List[Dict]) -> Dict[str, Any]:
        """Compare table detection capabilities."""
        return {
            'traditional_count': len(traditional_tables),
            'ai_count': len(ai_tables),
            'count_difference': len(ai_tables) - len(traditional_tables),
            'detection_ratio': len(ai_tables) / max(len(traditional_tables), 1),
            'both_found_tables': len(traditional_tables) > 0 and len(ai_tables) > 0,
            'only_traditional': len(traditional_tables) > 0 and len(ai_tables) == 0,
            'only_ai': len(traditional_tables) == 0 and len(ai_tables) > 0,
            'neither_found': len(traditional_tables) == 0 and len(ai_tables) == 0
        }
    
    def _compare_table_boundaries(self, traditional_tables: List[Dict], ai_tables: List[Dict]) -> Dict[str, Any]:
        """Compare table boundary accuracy."""
        if not traditional_tables or not ai_tables:
            return {
                'average_overlap': 0.0,
                'max_overlap': 0.0,
                'exact_matches': 0,
                'significant_overlaps': 0,
                'boundary_pairs': []
            }
        
        boundary_pairs = []
        overlaps = []
        exact_matches = 0
        significant_overlaps = 0
        
        for i, ai_table in enumerate(ai_tables):
            best_overlap = 0.0
            best_traditional = None
            
            for j, trad_table in enumerate(traditional_tables):
                overlap = self._calculate_boundary_overlap(ai_table, trad_table)
                overlaps.append(overlap)
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_traditional = j
                
                if overlap > 0.95:  # Near exact match
                    exact_matches += 1
                elif overlap > 0.5:  # Significant overlap
                    significant_overlaps += 1
                
                boundary_pairs.append({
                    'ai_table_index': i,
                    'traditional_table_index': j,
                    'overlap_score': overlap,
                    'ai_boundaries': self._extract_boundaries(ai_table),
                    'traditional_boundaries': self._extract_boundaries(trad_table)
                })
        
        return {
            'average_overlap': statistics.mean(overlaps) if overlaps else 0.0,
            'max_overlap': max(overlaps) if overlaps else 0.0,
            'exact_matches': exact_matches,
            'significant_overlaps': significant_overlaps,
            'boundary_pairs': boundary_pairs[:10]  # Limit for response size
        }
    
    def _calculate_boundary_overlap(self, table1: Dict[str, Any], table2: Dict[str, Any]) -> float:
        """Calculate overlap score between two table boundaries."""
        bounds1 = self._extract_boundaries(table1)
        bounds2 = self._extract_boundaries(table2)
        
        if not bounds1 or not bounds2:
            return 0.0
        
        # Calculate intersection
        intersect_start_row = max(bounds1['start_row'], bounds2['start_row'])
        intersect_end_row = min(bounds1['end_row'], bounds2['end_row'])
        intersect_start_col = max(bounds1['start_col'], bounds2['start_col'])
        intersect_end_col = min(bounds1['end_col'], bounds2['end_col'])
        
        # Check if there's any intersection
        if intersect_start_row > intersect_end_row or intersect_start_col > intersect_end_col:
            return 0.0
        
        # Calculate areas
        intersect_area = (intersect_end_row - intersect_start_row + 1) * (intersect_end_col - intersect_start_col + 1)
        area1 = (bounds1['end_row'] - bounds1['start_row'] + 1) * (bounds1['end_col'] - bounds1['start_col'] + 1)
        area2 = (bounds2['end_row'] - bounds2['start_row'] + 1) * (bounds2['end_col'] - bounds2['start_col'] + 1)
        
        # Calculate union
        union_area = area1 + area2 - intersect_area
        
        return intersect_area / union_area if union_area > 0 else 0.0
    
    def _extract_boundaries(self, table: Dict[str, Any]) -> Optional[Dict[str, int]]:
        """Extract boundary coordinates from table data."""
        # Handle different formats
        if all(key in table for key in ['start_row', 'end_row', 'start_col', 'end_col']):
            return {
                'start_row': int(table['start_row']),
                'end_row': int(table['end_row']),
                'start_col': int(table['start_col']),
                'end_col': int(table['end_col'])
            }
        elif 'boundaries' in table:
            bounds = table['boundaries']
            return {
                'start_row': int(bounds['start_row']),
                'end_row': int(bounds['end_row']),
                'start_col': int(bounds['start_col']),
                'end_col': int(bounds['end_col'])
            }
        else:
            return None
    
    def _compare_result_quality(self, traditional_result: Dict[str, Any], ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compare overall quality of results."""
        traditional_confidence = self._extract_confidence(traditional_result, 'traditional')
        ai_confidence = self._extract_confidence(ai_result, 'ai')
        
        return {
            'traditional_confidence': traditional_confidence,
            'ai_confidence': ai_confidence,
            'confidence_difference': ai_confidence - traditional_confidence,
            'traditional_has_errors': self._has_processing_errors(traditional_result),
            'ai_has_errors': self._has_processing_errors(ai_result),
            'traditional_completeness': self._assess_completeness(traditional_result),
            'ai_completeness': self._assess_completeness(ai_result)
        }
    
    def _compare_performance_indicators(self, traditional_result: Dict[str, Any], ai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance indicators."""
        return {
            'traditional_processing_time': traditional_result.get('processing_time', 0),
            'ai_processing_time': ai_result.get('metadata', {}).get('ai_metadata', {}).get('processing_time', 0),
            'traditional_method_used': traditional_result.get('detection_method', 'unknown'),
            'ai_tokens_used': ai_result.get('metadata', {}).get('ai_metadata', {}).get('total_tokens', 0),
            'ai_cost_estimate': ai_result.get('metadata', {}).get('ai_metadata', {}).get('cost_estimate', 0)
        }
    
    def _analyze_complexity_handling(self, 
                                   traditional_tables: List[Dict], 
                                   ai_tables: List[Dict], 
                                   complexity_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how well each method handles complexity."""
        if not complexity_metadata:
            return {'analysis_available': False}
        
        complexity_level = self._get_complexity_level(complexity_metadata)
        complexity_score = complexity_metadata.get('complexity_score', 0.0)
        
        # Expected performance based on complexity
        if complexity_score < 0.3:
            expected_traditional_success = True
            expected_ai_advantage = False
        elif complexity_score < 0.7:
            expected_traditional_success = True  # May struggle
            expected_ai_advantage = True  # Should help
        else:
            expected_traditional_success = False
            expected_ai_advantage = True
        
        traditional_success = len(traditional_tables) > 0
        ai_success = len(ai_tables) > 0
        
        return {
            'analysis_available': True,
            'complexity_level': complexity_level,
            'complexity_score': complexity_score,
            'expected_traditional_success': expected_traditional_success,
            'actual_traditional_success': traditional_success,
            'traditional_performance': 'as_expected' if traditional_success == expected_traditional_success else 'unexpected',
            'expected_ai_advantage': expected_ai_advantage,
            'actual_ai_advantage': ai_success and (len(ai_tables) >= len(traditional_tables)),
            'ai_performance': 'as_expected' if (ai_success and expected_ai_advantage) or (not expected_ai_advantage) else 'unexpected',
            'complexity_factors': complexity_metadata.get('failure_indicators', [])
        }
    
    def _analyze_failure_patterns(self, 
                                traditional_tables: List[Dict], 
                                ai_tables: List[Dict], 
                                complexity_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze failure patterns and their causes."""
        traditional_failed = len(traditional_tables) == 0
        ai_failed = len(ai_tables) == 0
        
        failure_analysis = {
            'traditional_failed': traditional_failed,
            'ai_failed': ai_failed,
            'both_failed': traditional_failed and ai_failed,
            'both_succeeded': not traditional_failed and not ai_failed,
            'only_traditional_failed': traditional_failed and not ai_failed,
            'only_ai_failed': not traditional_failed and ai_failed
        }
        
        # Analyze potential causes if we have complexity metadata
        if complexity_metadata:
            potential_causes = []
            
            # Check for known failure indicators
            failure_indicators = complexity_metadata.get('failure_indicators', [])
            for indicator in failure_indicators:
                potential_causes.append(f"complexity_{indicator}")
            
            # Check sparsity
            sparsity = complexity_metadata.get('data_distribution', {}).get('sparsity', 0.0)
            if sparsity > 0.7:
                potential_causes.append('high_sparsity')
            
            # Check merged cells
            merged_count = complexity_metadata.get('merged_cells', {}).get('count', 0)
            if merged_count > 10:
                potential_causes.append('many_merged_cells')
            
            failure_analysis['potential_causes'] = potential_causes
        
        return failure_analysis
    
    def _analyze_processing_recommendations(self, 
                                          traditional_result: Dict[str, Any], 
                                          ai_result: Dict[str, Any], 
                                          complexity_metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze processing method recommendations."""
        ai_recommendation = ai_result.get('processing_recommendation', 'traditional')
        traditional_success = len(self._extract_traditional_tables(traditional_result)) > 0
        
        # Determine if recommendation was accurate
        recommendation_accurate = False
        
        if ai_recommendation == 'traditional' and traditional_success:
            recommendation_accurate = True
        elif ai_recommendation in ['ai_assisted', 'ai_primary'] and not traditional_success:
            recommendation_accurate = True
        elif ai_recommendation == 'dual':
            recommendation_accurate = True  # Dual is always safe
        
        return {
            'ai_recommendation': ai_recommendation,
            'traditional_success': traditional_success,
            'recommendation_accurate': recommendation_accurate,
            'complexity_based_recommendation': self._generate_complexity_recommendation(complexity_metadata)
        }
    
    def _calculate_overall_metrics(self, 
                                 table_comparison: Dict, 
                                 boundary_comparison: Dict, 
                                 quality_comparison: Dict,
                                 performance_comparison: Dict, 
                                 complexity_analysis: Dict) -> ComparisonMetrics:
        """Calculate overall comparison metrics."""
        # Agreement score based on table detection and boundaries
        if table_comparison['neither_found']:
            agreement_score = 1.0  # Both found nothing
        elif table_comparison['both_found_tables']:
            agreement_score = boundary_comparison['average_overlap']
        else:
            agreement_score = 0.0  # Only one found something
        
        # Boundary overlap score
        boundary_overlap_score = boundary_comparison['average_overlap']
        
        # Confidence score (AI confidence)
        confidence_score = quality_comparison['ai_confidence']
        
        # Complexity alignment
        if complexity_analysis.get('analysis_available', False):
            traditional_performance = complexity_analysis['traditional_performance']
            ai_performance = complexity_analysis['ai_performance']
            complexity_alignment = 1.0 if traditional_performance == 'as_expected' and ai_performance == 'as_expected' else 0.5
        else:
            complexity_alignment = 0.5  # Unknown
        
        # Recommendation accuracy
        recommendation_accuracy = 1.0  # Placeholder - would need ground truth
        
        return ComparisonMetrics(
            agreement_score=agreement_score,
            table_count_difference=table_comparison['count_difference'],
            boundary_overlap_score=boundary_overlap_score,
            confidence_score=confidence_score,
            complexity_alignment=complexity_alignment,
            recommendation_accuracy=recommendation_accuracy
        )
    
    def _determine_winner(self, metrics: ComparisonMetrics, traditional_tables: List, ai_tables: List) -> str:
        """Determine which method performed better."""
        if len(traditional_tables) == 0 and len(ai_tables) == 0:
            return 'tie_no_detection'
        elif len(traditional_tables) > 0 and len(ai_tables) == 0:
            return 'traditional'
        elif len(traditional_tables) == 0 and len(ai_tables) > 0:
            return 'ai'
        else:
            # Both found tables, use agreement and confidence
            if metrics.agreement_score > 0.7 and metrics.confidence_score > 0.7:
                return 'tie_both_good'
            elif metrics.confidence_score > 0.7:
                return 'ai'
            elif metrics.agreement_score > 0.5:
                return 'tie_similar'
            else:
                return 'unclear'
    
    def _get_complexity_level(self, complexity_metadata: Optional[Dict[str, Any]]) -> str:
        """Get complexity level from metadata."""
        if not complexity_metadata:
            return 'unknown'
        
        complexity_score = complexity_metadata.get('complexity_score', 0.0)
        
        if complexity_score >= 0.7:
            return 'complex'
        elif complexity_score >= 0.3:
            return 'moderate'
        else:
            return 'simple'
    
    def _extract_confidence(self, result: Dict[str, Any], result_type: str) -> float:
        """Extract confidence score from result."""
        if result_type == 'ai':
            return result.get('ai_analysis', {}).get('confidence', 0.0)
        else:
            # Traditional methods don't typically have confidence scores
            tables = self._extract_traditional_tables(result)
            return 0.8 if len(tables) > 0 else 0.0  # Assume high confidence if tables found
    
    def _has_processing_errors(self, result: Dict[str, Any]) -> bool:
        """Check if result has processing errors."""
        validation = result.get('validation', {})
        return len(validation.get('errors', [])) > 0
    
    def _assess_completeness(self, result: Dict[str, Any]) -> float:
        """Assess completeness of result."""
        # This would be more sophisticated in practice
        if 'ai_analysis' in result:
            return result.get('ai_analysis', {}).get('confidence', 0.5)
        else:
            tables = self._extract_traditional_tables(result)
            return 0.8 if len(tables) > 0 else 0.2
    
    def _generate_complexity_recommendation(self, complexity_metadata: Optional[Dict[str, Any]]) -> str:
        """Generate processing recommendation based on complexity."""
        if not complexity_metadata:
            return 'traditional'
        
        complexity_score = complexity_metadata.get('complexity_score', 0.0)
        
        if complexity_score >= 0.7:
            return 'ai_primary'
        elif complexity_score >= 0.3:
            return 'dual'
        else:
            return 'traditional'
    
    def _generate_insights(self, 
                          metrics: ComparisonMetrics, 
                          traditional_tables: List, 
                          ai_tables: List,
                          complexity_metadata: Optional[Dict[str, Any]]) -> List[str]:
        """Generate actionable insights from comparison."""
        insights = []
        
        # Table detection insights
        if len(ai_tables) > len(traditional_tables):
            insights.append(f"AI detected {len(ai_tables) - len(traditional_tables)} more tables than traditional methods")
        elif len(traditional_tables) > len(ai_tables):
            insights.append(f"Traditional methods detected {len(traditional_tables) - len(ai_tables)} more tables than AI")
        
        # Agreement insights
        if metrics.agreement_score > 0.8:
            insights.append("High agreement between methods suggests reliable detection")
        elif metrics.agreement_score < 0.3:
            insights.append("Low agreement suggests one method may be failing or detecting different structures")
        
        # Confidence insights
        if metrics.confidence_score > 0.8:
            insights.append("AI analysis has high confidence in its results")
        elif metrics.confidence_score < 0.3:
            insights.append("AI analysis has low confidence - results may be unreliable")
        
        # Complexity insights
        if complexity_metadata:
            complexity_level = self._get_complexity_level(complexity_metadata)
            if complexity_level == 'complex' and len(traditional_tables) == 0:
                insights.append("Complex structure likely caused traditional method failure")
            elif complexity_level == 'simple' and len(ai_tables) == 0:
                insights.append("AI may have over-complicated a simple structure")
        
        return insights
    
    def _assess_test_case_potential(self, 
                                  metrics: ComparisonMetrics, 
                                  traditional_tables: List, 
                                  ai_tables: List) -> Dict[str, Any]:
        """Assess potential for generating test cases from this comparison."""
        potential_score = 0.0
        reasons = []
        
        # Disagreement is good for test cases
        if abs(metrics.table_count_difference) > 0:
            potential_score += 0.3
            reasons.append('table_count_disagreement')
        
        # Low agreement is interesting
        if metrics.agreement_score < 0.5:
            potential_score += 0.3
            reasons.append('low_agreement')
        
        # High confidence with disagreement is very valuable
        if metrics.confidence_score > 0.7 and metrics.agreement_score < 0.5:
            potential_score += 0.4
            reasons.append('confident_disagreement')
        
        test_case_type = 'none'
        if potential_score > 0.7:
            test_case_type = 'high_value'
        elif potential_score > 0.4:
            test_case_type = 'moderate_value'
        elif potential_score > 0.1:
            test_case_type = 'low_value'
        
        return {
            'potential_score': potential_score,
            'test_case_type': test_case_type,
            'reasons': reasons,
            'recommended_for_test_suite': potential_score > 0.4
        }
    
    def _generate_tuning_recommendations(self, 
                                       metrics: ComparisonMetrics, 
                                       complexity_metadata: Optional[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for tuning the system."""
        recommendations = []
        
        # Confidence tuning
        if metrics.confidence_score < 0.5:
            recommendations.append("Consider adjusting AI confidence thresholds")
        
        # Complexity threshold tuning
        if complexity_metadata:
            complexity_score = complexity_metadata.get('complexity_score', 0.0)
            if complexity_score > 0.5 and metrics.agreement_score < 0.3:
                recommendations.append("Consider lowering complexity threshold for AI activation")
            elif complexity_score < 0.3 and metrics.confidence_score < 0.7:
                recommendations.append("Consider raising complexity threshold to avoid unnecessary AI calls")
        
        # Boundary detection tuning
        if metrics.boundary_overlap_score < 0.5:
            recommendations.append("Consider improving boundary detection algorithms")
        
        return recommendations
    
    def _update_performance_tracking(self, comparison_result: Dict[str, Any]):
        """Update overall performance tracking metrics."""
        self.performance_metrics['total_comparisons'] += 1
        
        winner = comparison_result['summary']['winner']
        if 'ai' in winner:
            self.performance_metrics['ai_advantages'] += 1
        elif 'traditional' in winner:
            self.performance_metrics['traditional_advantages'] += 1
        elif 'tie' in winner:
            self.performance_metrics['agreements'] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        total = self.performance_metrics['total_comparisons']
        
        if total == 0:
            return {'message': 'No comparisons performed yet'}
        
        return {
            'total_comparisons': total,
            'ai_advantage_rate': self.performance_metrics['ai_advantages'] / total,
            'traditional_advantage_rate': self.performance_metrics['traditional_advantages'] / total,
            'agreement_rate': self.performance_metrics['agreements'] / total,
            'recent_comparisons': len(self.comparison_history),
            'average_agreement_score': statistics.mean([
                comp['metrics']['agreement_score'] for comp in self.comparison_history[-10:]
            ]) if self.comparison_history else 0.0
        }

