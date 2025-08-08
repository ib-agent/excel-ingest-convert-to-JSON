"""
Anthropic Excel Analysis Client

This module provides AI-powered table detection and analysis for Excel files
using the Anthropic Claude API.
"""

import json
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

# Try to import anthropic, handle if not installed
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

logger = logging.getLogger(__name__)


class AnthropicExcelClient:
    """
    Client for interacting with Anthropic API for Excel table analysis.
    
    This client specializes in analyzing Excel data structures and detecting
    tables that traditional heuristics might miss.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Anthropic client.
        
        Args:
            api_key: Anthropic API key. If None, reads from environment variable.
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        self.available = ANTHROPIC_AVAILABLE and self.api_key is not None
        
        if self.available:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {str(e)}")
                self.available = False
        else:
            if not ANTHROPIC_AVAILABLE:
                logger.warning("Anthropic package not available. Install with: pip install anthropic")
            elif not self.api_key:
                logger.warning("No Anthropic API key found. Set ANTHROPIC_API_KEY environment variable.")
    
    def is_available(self) -> bool:
        """Check if the Anthropic client is available and ready to use."""
        return self.available
    
    def analyze_excel_tables(self, 
                           sheet_data: Dict[str, Any], 
                           complexity_metadata: Optional[Dict[str, Any]] = None,
                           analysis_focus: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyze Excel sheet data using AI to detect and extract tables.
        
        Args:
            sheet_data: Excel sheet data (compact format)
            complexity_metadata: Complexity analysis metadata
            analysis_focus: Type of analysis ("comprehensive", "tables", "headers")
            
        Returns:
            Dictionary containing AI analysis results
        """
        if not self.available:
            return self._create_unavailable_response()
        
        try:
            # Prepare the analysis prompt
            prompt = self._build_excel_analysis_prompt(
                sheet_data, 
                complexity_metadata, 
                analysis_focus
            )
            
            # Make API call
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.1,  # Low temperature for consistent table detection
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse the response
            analysis_result = self._parse_ai_response(response.content[0].text)
            
            # Add metadata
            analysis_result['ai_metadata'] = {
                'model': "claude-3-5-sonnet-20241022",
                'timestamp': datetime.now().isoformat(),
                'analysis_focus': analysis_focus,
                'prompt_tokens': response.usage.input_tokens,
                'completion_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
            
            logger.info(f"AI analysis completed successfully. Tokens used: {analysis_result['ai_metadata']['total_tokens']}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return self._create_error_response(str(e))
    
    def _build_excel_analysis_prompt(self, 
                                   sheet_data: Dict[str, Any],
                                   complexity_metadata: Optional[Dict[str, Any]],
                                   analysis_focus: str) -> str:
        """
        Build the analysis prompt for Excel table detection.
        
        This prompt is specifically designed for Excel table analysis and
        incorporates complexity metadata when available.
        """
        sheet_name = sheet_data.get('name', 'Unknown')
        dimensions = sheet_data.get('dimensions', [1, 1, 1, 1])
        
        prompt = f"""You are an expert Excel analyst specializing in table detection and data structure analysis. 

TASK: Analyze the provided Excel sheet data and identify all tables, their structures, and relationships.

SHEET INFORMATION:
- Name: {sheet_name}
- Dimensions: Rows {dimensions[0]}-{dimensions[2]}, Columns {dimensions[1]}-{dimensions[3]}
- Data Format: Compact representation with run-length encoding

"""
        
        # Add complexity context if available
        if complexity_metadata:
            prompt += f"""COMPLEXITY ANALYSIS:
- Cell count: {complexity_metadata.get('cell_count', 'Unknown')}
- Merged cells: {complexity_metadata.get('merged_cells', {}).get('count', 0)}
- Header levels detected: {complexity_metadata.get('header_structure', {}).get('detected_levels', 'Unknown')}
- Data sparsity: {complexity_metadata.get('data_distribution', {}).get('sparsity', 'Unknown')}
- Formula ratio: {complexity_metadata.get('formulas', {}).get('formula_ratio', 'Unknown')}

"""
        
        # Add data representation explanation
        prompt += """DATA FORMAT EXPLANATION:
The sheet data uses a compact representation where:
- Rows contain cells in format: [column_index, value] or [start_col, val1, val2, ..., run_length] for RLE
- Empty cells are omitted to save space
- Values may be numbers, text, formulas, or null

"""
        
        # Add the actual data (truncated if too large)
        data_str = self._prepare_data_for_prompt(sheet_data)
        prompt += f"""SHEET DATA:
{data_str}

"""
        
        # Add analysis instructions based on focus
        if analysis_focus == "comprehensive":
            prompt += """ANALYSIS REQUIREMENTS:
1. IDENTIFY ALL TABLES: Find all distinct data tables in the sheet
2. TABLE BOUNDARIES: Determine precise start/end rows and columns for each table
3. HEADER ANALYSIS: Identify header rows/columns and their hierarchy
4. DATA STRUCTURE: Analyze data types, patterns, and relationships
5. MERGED CELLS: Account for merged cell impacts on table structure
6. QUALITY ASSESSMENT: Evaluate data completeness and consistency

"""
        elif analysis_focus == "tables":
            prompt += """ANALYSIS REQUIREMENTS:
1. TABLE DETECTION: Focus on identifying distinct data tables
2. BOUNDARIES: Precise table start/end coordinates
3. BASIC STRUCTURE: Headers vs data rows identification

"""
        elif analysis_focus == "headers":
            prompt += """ANALYSIS REQUIREMENTS:
1. HEADER IDENTIFICATION: Find all header rows and columns
2. HIERARCHY ANALYSIS: Determine header levels and relationships
3. HEADER QUALITY: Assess header completeness and consistency

"""
        
        prompt += """OUTPUT FORMAT:
Respond with a JSON object containing:

{
    "tables_detected": [
        {
            "table_id": "table_1",
            "name": "descriptive_table_name",
            "boundaries": {
                "start_row": number,
                "end_row": number,
                "start_col": number,
                "end_col": number
            },
            "headers": {
                "row_headers": [
                    {
                        "row": number,
                        "columns": [{"col": number, "value": "header_text"}],
                        "level": number
                    }
                ],
                "column_headers": [
                    {
                        "col": number,
                        "rows": [{"row": number, "value": "header_text"}],
                        "level": number
                    }
                ]
            },
            "data_area": {
                "start_row": number,
                "end_row": number,
                "start_col": number,
                "end_col": number
            },
            "table_type": "financial|operational|list|pivot|other",
            "confidence": 0.0-1.0,
            "complexity_indicators": ["merged_cells", "multi_level_headers", "sparse_data", "formulas"],
            "data_quality": {
                "completeness": 0.0-1.0,
                "consistency": 0.0-1.0,
                "data_types": ["text", "number", "date", "formula"]
            }
        }
    ],
    "sheet_analysis": {
        "total_tables": number,
        "data_density": 0.0-1.0,
        "structure_complexity": "simple|moderate|complex",
        "recommended_processing": "traditional|ai_assisted|ai_primary"
    },
    "analysis_confidence": 0.0-1.0,
    "processing_notes": ["note1", "note2"]
}

IMPORTANT:
- Be precise with coordinates (1-based indexing)
- Provide high confidence scores only for clearly defined tables
- Include complexity indicators that affect processing difficulty
- Consider merged cells when defining boundaries
- Account for empty rows/columns that may separate tables
- Provide specific, actionable processing recommendations

Begin analysis now:"""
        
        return prompt
    
    def _prepare_data_for_prompt(self, sheet_data: Dict[str, Any]) -> str:
        """
        Prepare sheet data for inclusion in the prompt.
        
        This method converts the sheet data to a readable format while
        managing size constraints for the API.
        """
        rows = sheet_data.get('rows', [])
        
        if not rows:
            return "No data rows found in sheet."
        
        # Convert to readable format
        data_lines = []
        max_rows_to_include = 100  # Limit for prompt size
        
        for i, row in enumerate(rows[:max_rows_to_include]):
            row_num = row.get('r', i + 1)
            cells = row.get('cells', [])
            
            if cells:
                cell_representations = []
                for cell in cells:
                    if len(cell) >= 2:
                        if len(cell) == 2:
                            # Simple cell: [col, value]
                            col, value = cell
                            cell_representations.append(f"Col{col}:{value}")
                        else:
                            # RLE cell: [start_col, val1, val2, ..., run_length]
                            start_col = int(cell[0])
                            run_length = int(cell[-1]) if isinstance(cell[-1], (int, str)) and str(cell[-1]).isdigit() else 1
                            values = cell[1:-1]
                            if len(values) == 1:
                                # Single value repeated
                                cell_representations.append(f"Col{start_col}-{start_col+run_length-1}:{values[0]}")
                            else:
                                # Multiple values
                                for j, val in enumerate(values):
                                    cell_representations.append(f"Col{start_col+j}:{val}")
                
                if cell_representations:
                    data_lines.append(f"Row {row_num}: {', '.join(cell_representations)}")
        
        if len(rows) > max_rows_to_include:
            data_lines.append(f"... ({len(rows) - max_rows_to_include} more rows truncated)")
        
        return '\n'.join(data_lines)
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the AI response and extract structured data.
        
        This method handles various response formats and provides fallbacks
        for partial or malformed responses.
        """
        try:
            # Try to extract JSON from the response
            import re
            
            # Look for JSON block
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Look for JSON without code blocks
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    raise ValueError("No JSON found in response")
            
            # Parse the JSON
            parsed_result = json.loads(json_text)
            
            # Validate required fields
            if 'tables_detected' not in parsed_result:
                parsed_result['tables_detected'] = []
            
            if 'sheet_analysis' not in parsed_result:
                parsed_result['sheet_analysis'] = {
                    'total_tables': len(parsed_result['tables_detected']),
                    'structure_complexity': 'unknown',
                    'recommended_processing': 'traditional'
                }
            
            if 'analysis_confidence' not in parsed_result:
                parsed_result['analysis_confidence'] = 0.5
            
            return {
                'status': 'success',
                'result': parsed_result,
                'raw_response': response_text
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return self._create_parse_error_response(response_text, str(e))
        
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return self._create_parse_error_response(response_text, str(e))
    
    def _create_unavailable_response(self) -> Dict[str, Any]:
        """Create response when AI service is unavailable."""
        return {
            'status': 'unavailable',
            'message': 'Anthropic AI service is not available',
            'reason': 'API key missing or anthropic package not installed',
            'result': {
                'tables_detected': [],
                'sheet_analysis': {
                    'total_tables': 0,
                    'structure_complexity': 'unknown',
                    'recommended_processing': 'traditional'
                },
                'analysis_confidence': 0.0
            }
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create response for API errors."""
        return {
            'status': 'error',
            'message': f'AI analysis failed: {error_message}',
            'result': {
                'tables_detected': [],
                'sheet_analysis': {
                    'total_tables': 0,
                    'structure_complexity': 'unknown',
                    'recommended_processing': 'traditional'
                },
                'analysis_confidence': 0.0
            }
        }
    
    def _create_parse_error_response(self, raw_response: str, error_message: str) -> Dict[str, Any]:
        """Create response for parsing errors."""
        return {
            'status': 'parse_error',
            'message': f'Failed to parse AI response: {error_message}',
            'raw_response': raw_response[:1000],  # Truncate for logging
            'result': {
                'tables_detected': [],
                'sheet_analysis': {
                    'total_tables': 0,
                    'structure_complexity': 'complex',  # Assume complex since parsing failed
                    'recommended_processing': 'ai_assisted'
                },
                'analysis_confidence': 0.0
            }
        }
    
    def estimate_api_cost(self, sheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate the API cost for analyzing the given sheet.
        
        This helps with cost management and decision making.
        """
        # Rough token estimation
        data_str = self._prepare_data_for_prompt(sheet_data)
        
        # Estimate tokens (rough approximation: 4 chars per token)
        prompt_tokens = len(data_str) // 4 + 1000  # Base prompt + data
        completion_tokens = 2000  # Estimated response size
        
        # Claude pricing (approximate, check current rates)
        input_cost_per_1k = 0.003  # $0.003 per 1K input tokens
        output_cost_per_1k = 0.015  # $0.015 per 1K output tokens
        
        input_cost = (prompt_tokens / 1000) * input_cost_per_1k
        output_cost = (completion_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        
        return {
            'estimated_prompt_tokens': prompt_tokens,
            'estimated_completion_tokens': completion_tokens,
            'estimated_total_tokens': prompt_tokens + completion_tokens,
            'estimated_cost_usd': total_cost,
            'cost_breakdown': {
                'input_cost': input_cost,
                'output_cost': output_cost
            }
        }

