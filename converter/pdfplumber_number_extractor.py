"""
PDFPlumber Number Extractor

This module provides number extraction capabilities from text content
using regex patterns and converts them to the existing JSON schema format.

Author: PDF Processing Team
Date: 2024
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFPlumberNumberExtractor:
    """
    Number extraction from text content with conversion to existing JSON schemas
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the PDFPlumber number extractor
        
        Args:
            config: Configuration dictionary for number extraction
        """
        self.config = config or self._get_default_config()
        self.patterns = self.config.get('patterns', {})
        self.context_window = self.config.get('context_window', 100)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)
        self.extract_metadata = self.config.get('extract_metadata', True)
        self.include_positioning = self.config.get('include_positioning', True)
        
        logger.info("PDFPlumberNumberExtractor initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for number extraction"""
        return {
            'patterns': {
                'integer': r'\b\d{1,3}(?:,\d{3})*\b',
                'decimal': r'\b\d+\.\d+\b',
                'percentage': r'\b\d+(?:\.\d+)?%\b',
                'currency': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?\b',
                'scientific_notation': r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b',
                'fraction': r'\b\d+/\d+\b',
                'date_number': r'\b(?:19|20)\d{2}\b|\b\d{1,2}(?:st|nd|rd|th)\b'
            },
            'context_window': 100,
            'confidence_threshold': 0.7,
            'extract_metadata': True,
            'include_positioning': True
        }
    
    def extract_numbers_from_text(self, text: str, position: Dict, metadata: Dict) -> List[Dict]:
        """
        Extract numbers from text content
        
        Args:
            text: Text content to analyze
            position: Position information for the text
            metadata: Metadata about the text formatting
            
        Returns:
            List of number dictionaries in the schema format
        """
        if not text or not text.strip():
            return []
        
        numbers = []
        used_positions = set()
        
        # Collect all matches from all patterns first
        all_matches = []
        for format_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                all_matches.append((match, format_type))
        
        # Sort matches by start position and length (longer matches first)
        all_matches.sort(key=lambda x: (x[0].start(), -x[0].end()))
        
        # Process matches, avoiding overlaps
        for match, format_type in all_matches:
            start_pos = match.start()
            end_pos = match.end()
            
            # Check if this position overlaps with any used position
            overlaps = False
            for used_start, used_end in used_positions:
                if not (end_pos <= used_start or start_pos >= used_end):
                    overlaps = True
                    break
            
            if not overlaps:
                number_info = self._process_number_match(
                    match, format_type, text, position, metadata
                )
                
                if number_info and number_info["confidence"] >= self.confidence_threshold:
                    numbers.append(number_info)
                    used_positions.add((start_pos, end_pos))
        
        return numbers
    
    def _process_number_match(self, match: re.Match, format_type: str, text: str, 
                            position: Dict, metadata: Dict) -> Optional[Dict]:
        """
        Process a single number match and convert to schema format
        
        Args:
            match: Regex match object
            format_type: Type of number format
            text: Full text content
            position: Position information
            metadata: Text metadata
            
        Returns:
            Number dictionary in schema format or None
        """
        try:
            original_text = match.group(0)
            numeric_value = self._extract_numeric_value(original_text, format_type)
            
            if numeric_value is None:
                return None
            
            # Extract context around the number
            context = self._extract_context(text, match.start(), match.end())
            
            # Calculate confidence based on format and context
            confidence = self._calculate_confidence(original_text, format_type, context)
            
            # Extract additional information
            unit = self._extract_unit(context, format_type)
            currency = self._extract_currency(original_text, format_type)
            
            # Calculate position within text
            text_position = self._calculate_text_position(
                match.start(), match.end(), text, position
            )
            
            number_info = {
                "value": numeric_value,
                "original_text": original_text,
                "context": context,
                "position": text_position,
                "format": format_type,
                "unit": unit,
                "currency": currency,
                "confidence": confidence,
                "extraction_method": "regex_pattern",
                "metadata": self._create_number_metadata(metadata)
            }
            
            return number_info
            
        except Exception as e:
            logger.debug(f"Error processing number match: {e}")
            return None
    
    def _extract_numeric_value(self, text: str, format_type: str) -> Optional[float]:
        """
        Extract numeric value from text based on format type
        
        Args:
            text: Original text containing the number
            format_type: Type of number format
            
        Returns:
            Numeric value or None if extraction fails
        """
        try:
            if format_type == 'currency':
                # Remove currency symbols and convert
                clean_text = re.sub(r'[\$,\s]', '', text)
                return float(clean_text)
            
            elif format_type == 'percentage':
                # Remove % symbol and convert
                clean_text = text.replace('%', '').strip()
                return float(clean_text)
            
            elif format_type == 'integer':
                # Remove commas and convert
                clean_text = text.replace(',', '')
                return float(clean_text)
            
            elif format_type == 'decimal':
                # Direct conversion
                return float(text)
            
            elif format_type == 'scientific_notation':
                # Direct conversion
                return float(text)
            
            elif format_type == 'fraction':
                # Convert fraction to decimal
                parts = text.split('/')
                if len(parts) == 2:
                    numerator = float(parts[0])
                    denominator = float(parts[1])
                    if denominator != 0:
                        return numerator / denominator
            
            elif format_type == 'date_number':
                # Extract year or day number
                if re.match(r'(?:19|20)\d{2}', text):
                    return float(text)  # Year
                else:
                    # Extract day number from ordinal
                    clean_text = re.sub(r'(st|nd|rd|th)', '', text)
                    return float(clean_text)
        
        except (ValueError, ZeroDivisionError):
            pass
        
        return None
    
    def _extract_context(self, text: str, start_pos: int, end_pos: int) -> str:
        """
        Extract context around the number
        
        Args:
            text: Full text content
            start_pos: Start position of number
            end_pos: End position of number
            
        Returns:
            Context string
        """
        context_start = max(0, start_pos - self.context_window)
        context_end = min(len(text), end_pos + self.context_window)
        
        context = text[context_start:context_end].strip()
        
        # Clean up context
        context = re.sub(r'\s+', ' ', context)
        
        return context
    
    def _calculate_confidence(self, original_text: str, format_type: str, context: str) -> float:
        """
        Calculate confidence score for the extracted number
        
        Args:
            original_text: Original number text
            format_type: Type of number format
            context: Context around the number
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.7  # Base confidence
        
        # Format-specific confidence adjustments
        if format_type == 'currency' and '$' in original_text:
            confidence += 0.2
        elif format_type == 'percentage' and '%' in original_text:
            confidence += 0.2
        elif format_type == 'integer' and ',' in original_text:
            confidence += 0.1  # Properly formatted large numbers
        
        # Context-based adjustments
        business_terms = [
            'revenue', 'income', 'profit', 'loss', 'cost', 'expense', 'price',
            'amount', 'total', 'sum', 'million', 'billion', 'thousand',
            'rate', 'percentage', 'margin', 'growth', 'increase', 'decrease'
        ]
        
        context_lower = context.lower()
        matching_terms = sum(1 for term in business_terms if term in context_lower)
        
        if matching_terms > 0:
            confidence += min(0.1 * matching_terms, 0.2)
        
        # Penalize if context suggests non-business number
        non_business_terms = ['page', 'section', 'figure', 'table', 'chapter']
        non_business_matches = sum(1 for term in non_business_terms if term in context_lower)
        
        if non_business_matches > 0:
            confidence -= min(0.1 * non_business_matches, 0.3)
        
        return max(0.0, min(1.0, confidence))
    
    def _extract_unit(self, context: str, format_type: str) -> Optional[str]:
        """
        Extract unit of measurement from context
        
        Args:
            context: Context around the number
            format_type: Type of number format
            
        Returns:
            Unit string or None
        """
        if format_type == 'percentage':
            return 'percent'
        
        # Common units to look for
        unit_patterns = {
            r'\b(million|mil|m)\b': 'million',
            r'\b(billion|bil|b)\b': 'billion',
            r'\b(thousand|k)\b': 'thousand',
            r'\b(dollars?|usd)\b': 'dollars',
            r'\b(cents?)\b': 'cents',
            r'\b(years?|yrs?)\b': 'years',
            r'\b(months?|mos?)\b': 'months',
            r'\b(days?)\b': 'days',
            r'\b(hours?|hrs?)\b': 'hours',
            r'\b(minutes?|mins?)\b': 'minutes',
            r'\b(seconds?|secs?)\b': 'seconds',
            r'\b(percent|percentage|%)\b': 'percent'
        }
        
        context_lower = context.lower()
        
        for pattern, unit in unit_patterns.items():
            if re.search(pattern, context_lower):
                return unit
        
        return None
    
    def _extract_currency(self, original_text: str, format_type: str) -> Optional[str]:
        """
        Extract currency information
        
        Args:
            original_text: Original number text
            format_type: Type of number format
            
        Returns:
            Currency code or None
        """
        if format_type == 'currency':
            if '$' in original_text:
                return 'USD'
            elif '€' in original_text:
                return 'EUR'
            elif '£' in original_text:
                return 'GBP'
            elif '¥' in original_text:
                return 'JPY'
        
        return None
    
    def _calculate_text_position(self, start_pos: int, end_pos: int, text: str, 
                                section_position: Dict) -> Dict:
        """
        Calculate position of number within the document
        
        Args:
            start_pos: Start position in text
            end_pos: End position in text
            text: Full text content
            section_position: Position of the section
            
        Returns:
            Position dictionary
        """
        # Calculate line number by counting newlines before start_pos
        line_number = text[:start_pos].count('\n') + 1
        
        # Estimate character position within the section
        lines = text[:start_pos].split('\n')
        char_in_line = len(lines[-1]) if lines else 0
        
        # Use section position as base and add estimated offsets
        bbox = section_position.get('bbox', [0, 0, 0, 0])
        
        # Simple estimation of position within section
        # In a real implementation, this could be more sophisticated
        estimated_x = bbox[0] + (char_in_line * 6)  # Rough character width
        estimated_y = bbox[1] + (line_number * 12)  # Rough line height
        
        return {
            "x": estimated_x,
            "y": estimated_y,
            "bbox": [estimated_x, estimated_y, estimated_x + (end_pos - start_pos) * 6, estimated_y + 12],
            "line_number": line_number
        }
    
    def _create_number_metadata(self, text_metadata: Dict) -> Dict:
        """
        Create number metadata based on text metadata
        
        Args:
            text_metadata: Metadata from the text section
            
        Returns:
            Number metadata dictionary
        """
        return {
            "font_size": text_metadata.get("font_size", 12),
            "font_family": text_metadata.get("font_family", "Arial"),
            "is_bold": text_metadata.get("is_bold", False),
            "is_italic": text_metadata.get("is_italic", False),
            "color": text_metadata.get("color", "#000000")
        } 