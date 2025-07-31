"""
PDFPlumber Text Extractor

This module provides text extraction capabilities using PDFPlumber library
with layout preservation and conversion to existing JSON schemas.

Author: PDF Processing Team
Date: 2024
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import pdfplumber

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFPlumberTextExtractor:
    """
    Text extraction using PDFPlumber with layout preservation and 
    conversion to existing text content JSON schemas
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the PDFPlumber text extractor
        
        Args:
            config: Configuration dictionary for text extraction
        """
        self.config = config or self._get_default_config()
        self.text_settings = self.config.get('text_settings', {})
        self.section_config = self.config.get('section_detection', {})
        self.extract_metadata = self.config.get('extract_metadata', True)
        self.preserve_formatting = self.config.get('preserve_formatting', True)
        
        logger.info("PDFPlumberTextExtractor initialized")
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for PDFPlumber text extraction"""
        return {
            'text_settings': {
                'x_tolerance': 3,
                'y_tolerance': 3
            },
            'section_detection': {
                'min_section_size': 50,
                'max_section_size': 1000,
                'use_headers': True,
                'detect_lists': True,
                'min_words_per_section': 10,
                'max_words_per_section': 500
            },
            'extract_metadata': True,
            'preserve_formatting': True
        }
    
    def extract_text_content(self, pdf_path: str, table_regions: Optional[List[Dict]] = None) -> Dict:
        """
        Extract text content from PDF using PDFPlumber, excluding table regions
        
        Args:
            pdf_path: Path to the PDF file
            table_regions: List of table regions to exclude from text extraction
            
        Returns:
            Dictionary containing extracted text in structured format
        """
        logger.info(f"Starting text extraction from: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Initialize result structure
        text_data = {
            "text_content": {
                "document_metadata": {
                    "filename": os.path.basename(pdf_path),
                    "extraction_timestamp": datetime.now().isoformat(),
                    "extraction_method": "pdfplumber_enhanced",
                    "total_pages": 0,
                    "total_word_count": 0
                },
                "pages": [],
                "document_structure": {
                    "toc": [],
                    "sections_by_type": {
                        "header": 0,
                        "paragraph": 0,
                        "list": 0,
                        "table_caption": 0,
                        "figure_caption": 0,
                        "footer": 0,
                        "sidebar": 0
                    }
                },
                "summary": {
                    "total_sections": 0,
                    "total_words": 0,
                    "llm_ready_sections": 0,
                    "average_section_length": 0,
                    "reading_time_estimate": 0,
                    "total_numbers_found": 0
                }
            }
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_data["text_content"]["document_metadata"]["total_pages"] = len(pdf.pages)
                
                # Convert table regions to exclusion zones
                exclusion_zones = self._prepare_exclusion_zones(table_regions, len(pdf.pages))
                
                # Process each page
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"Processing page {page_num + 1}/{len(pdf.pages)}")
                    
                    # Extract text content from page
                    page_data = self._extract_page_content(
                        page, page_num + 1, exclusion_zones.get(page_num, [])
                    )
                    
                    text_data["text_content"]["pages"].append(page_data)
                    
                    # Update summary statistics
                    for section in page_data["sections"]:
                        section_type = section["section_type"]
                        text_data["text_content"]["document_structure"]["sections_by_type"][section_type] += 1
                        text_data["text_content"]["summary"]["total_sections"] += 1
                        text_data["text_content"]["summary"]["total_words"] += section["word_count"]
                        text_data["text_content"]["summary"]["total_numbers_found"] += len(section.get("numbers", []))
                        
                        if section["llm_ready"]:
                            text_data["text_content"]["summary"]["llm_ready_sections"] += 1
                
                # Calculate final statistics
                self._finalize_statistics(text_data["text_content"])
                
                # Generate table of contents
                text_data["text_content"]["document_structure"]["toc"] = \
                    self._generate_table_of_contents(text_data["text_content"]["pages"])
                
                logger.info(f"Text extraction completed. Found {text_data['text_content']['summary']['total_sections']} sections")
                return text_data
                
        except Exception as e:
            logger.error(f"Error during text extraction: {str(e)}")
            raise
    
    def _prepare_exclusion_zones(self, table_regions: Optional[List[Dict]], total_pages: int) -> Dict[int, List[Tuple]]:
        """
        Prepare exclusion zones from table regions
        
        Args:
            table_regions: List of table regions from table extraction
            total_pages: Total number of pages in the document
            
        Returns:
            Dictionary mapping page numbers to exclusion zone coordinates
        """
        exclusion_zones = {}
        
        if not table_regions:
            return exclusion_zones
        
        for table in table_regions:
            page_num = table.get("region", {}).get("page_number", 1) - 1  # Convert to 0-based
            bbox = table.get("region", {}).get("bbox")
            
            if bbox and 0 <= page_num < total_pages:
                if page_num not in exclusion_zones:
                    exclusion_zones[page_num] = []
                
                # Add padding around table region
                padding = 10
                exclusion_zone = (
                    max(0, bbox[0] - padding),  # x0
                    max(0, bbox[1] - padding),  # y0
                    bbox[2] + padding,          # x1
                    bbox[3] + padding           # y1
                )
                exclusion_zones[page_num].append(exclusion_zone)
                
                logger.debug(f"Added exclusion zone on page {page_num + 1}: {exclusion_zone}")
        
        return exclusion_zones
    
    def _extract_page_content(self, page: Any, page_num: int, exclusion_zones: List[Tuple]) -> Dict:
        """
        Extract text content from a single page
        
        Args:
            page: PDFPlumber page object
            page_num: Page number (1-based)
            exclusion_zones: List of exclusion zone coordinates
            
        Returns:
            Page data dictionary
        """
        page_data = {
            "page_number": page_num,
            "page_width": page.width,
            "page_height": page.height,
            "sections": []
        }
        
        try:
            # Extract words with coordinates and metadata
            words = page.extract_words(**self.text_settings)
            
            # Filter out words in exclusion zones
            filtered_words = self._filter_excluded_words(words, exclusion_zones)
            
            if filtered_words:
                # Group words into text blocks/paragraphs
                text_blocks = self._group_words_into_blocks(filtered_words)
                
                # Convert text blocks to sections
                sections = self._convert_blocks_to_sections(text_blocks, page_num)
                
                # Extract numbers from sections
                sections = self._extract_numbers_from_sections(sections)
                
                page_data["sections"] = sections
        
        except Exception as e:
            logger.warning(f"Error extracting content from page {page_num}: {e}")
        
        return page_data
    
    def _filter_excluded_words(self, words: List[Dict], exclusion_zones: List[Tuple]) -> List[Dict]:
        """
        Filter out words that fall within exclusion zones
        
        Args:
            words: List of word dictionaries from PDFPlumber
            exclusion_zones: List of exclusion zone coordinates
            
        Returns:
            Filtered list of words
        """
        if not exclusion_zones:
            return words
        
        filtered_words = []
        
        for word in words:
            word_bbox = (word['x0'], word['top'], word['x1'], word['bottom'])
            
            # Check if word overlaps with any exclusion zone
            excluded = False
            for zone in exclusion_zones:
                if self._bbox_overlaps(word_bbox, zone):
                    excluded = True
                    break
            
            if not excluded:
                filtered_words.append(word)
        
        logger.debug(f"Filtered {len(words) - len(filtered_words)} words from exclusion zones")
        return filtered_words
    
    def _bbox_overlaps(self, bbox1: Tuple, bbox2: Tuple) -> bool:
        """
        Check if two bounding boxes overlap
        
        Args:
            bbox1: First bounding box (x0, y0, x1, y1)
            bbox2: Second bounding box (x0, y0, x1, y1)
            
        Returns:
            True if bounding boxes overlap
        """
        return not (bbox1[2] < bbox2[0] or bbox2[2] < bbox1[0] or 
                   bbox1[3] < bbox2[1] or bbox2[3] < bbox1[1])
    
    def _group_words_into_blocks(self, words: List[Dict]) -> List[Dict]:
        """
        Group words into coherent text blocks based on spatial proximity
        
        Args:
            words: List of word dictionaries
            
        Returns:
            List of text block dictionaries
        """
        if not words:
            return []
        
        # Sort words by position (top to bottom, left to right)
        sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
        
        blocks = []
        current_block = None
        
        for word in sorted_words:
            if current_block is None:
                # Start new block
                current_block = {
                    'words': [word],
                    'x0': word['x0'],
                    'top': word['top'],
                    'x1': word['x1'],
                    'bottom': word['bottom'],
                    'text': word['text']
                }
            else:
                # Check if word should be added to current block
                if self._should_merge_with_block(word, current_block):
                    # Add to current block
                    current_block['words'].append(word)
                    current_block['x0'] = min(current_block['x0'], word['x0'])
                    current_block['top'] = min(current_block['top'], word['top'])
                    current_block['x1'] = max(current_block['x1'], word['x1'])
                    current_block['bottom'] = max(current_block['bottom'], word['bottom'])
                    current_block['text'] += ' ' + word['text']
                else:
                    # Finalize current block and start new one
                    blocks.append(current_block)
                    current_block = {
                        'words': [word],
                        'x0': word['x0'],
                        'top': word['top'],
                        'x1': word['x1'],
                        'bottom': word['bottom'],
                        'text': word['text']
                    }
        
        # Add the last block
        if current_block:
            blocks.append(current_block)
        
        return blocks
    
    def _should_merge_with_block(self, word: Dict, block: Dict) -> bool:
        """
        Determine if a word should be merged with the current text block
        
        Args:
            word: Word dictionary
            block: Current text block
            
        Returns:
            True if word should be merged with block
        """
        # Check vertical distance
        vertical_gap = abs(word['top'] - block['bottom'])
        if vertical_gap > 20:  # Too far vertically
            return False
        
        # Check horizontal alignment for same line
        if vertical_gap <= 5:  # Same line
            horizontal_gap = word['x0'] - block['x1']
            if horizontal_gap <= 20:  # Close enough horizontally
                return True
        
        # Check for paragraph continuation
        if vertical_gap <= 15:  # Next line
            # Check if left margin is similar (paragraph continuation)
            left_margin_diff = abs(word['x0'] - block['x0'])
            if left_margin_diff <= 10:
                return True
        
        return False
    
    def _convert_blocks_to_sections(self, text_blocks: List[Dict], page_num: int) -> List[Dict]:
        """
        Convert text blocks to structured sections
        
        Args:
            text_blocks: List of text block dictionaries
            page_num: Page number (1-based)
            
        Returns:
            List of section dictionaries
        """
        sections = []
        section_counter = 1
        
        for block in text_blocks:
            text_content = block['text'].strip()
            
            if not text_content:
                continue
            
            # Split long blocks into paragraphs
            paragraphs = self._split_into_paragraphs(text_content)
            
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                
                # Determine section type
                section_type = self._classify_section_type(paragraph, block)
                
                # Check if section meets size requirements
                word_count = len(paragraph.split())
                if word_count < self.section_config.get("min_words_per_section", 5):
                    continue
                
                # Create section
                section = {
                    "section_id": f"page_{page_num}_section_{section_counter}",
                    "section_type": section_type,
                    "title": self._extract_title(paragraph, section_type),
                    "content": paragraph,
                    "word_count": word_count,
                    "character_count": len(paragraph),
                    "llm_ready": self._is_llm_ready(paragraph, word_count),
                    "position": {
                        "start_y": block['top'],
                        "end_y": block['bottom'],
                        "bbox": [block['x0'], block['top'], block['x1'], block['bottom']],
                        "column_index": 0
                    },
                    "metadata": self._extract_text_metadata(block),
                    "structure": {
                        "heading_level": self._determine_heading_level(paragraph, block),
                        "list_type": self._detect_list_type(paragraph),
                        "list_level": None,
                        "is_continuation": False
                    },
                    "relationships": {
                        "parent_section": None,
                        "child_sections": [],
                        "related_tables": [],
                        "related_figures": []
                    },
                    "numbers": []  # Will be populated by number extraction
                }
                
                sections.append(section)
                section_counter += 1
        
        return sections
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into individual paragraphs
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraph strings
        """
        # Split by multiple newlines or sentence patterns
        paragraphs = re.split(r'\n\s*\n|\.\s+(?=[A-Z])', text)
        
        # Clean up paragraphs
        cleaned_paragraphs = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Normalize whitespace
                paragraph = re.sub(r'\s+', ' ', paragraph)
                cleaned_paragraphs.append(paragraph)
        
        return cleaned_paragraphs
    
    def _classify_section_type(self, text: str, block: Dict) -> str:
        """
        Classify text block into section type
        
        Args:
            text: Text content
            block: Text block dictionary
            
        Returns:
            Section type string
        """
        text_lower = text.lower()
        
        # Check for headers based on content patterns
        if (len(text.split()) <= 10 and 
            (text.isupper() or 
             any(pattern in text_lower for pattern in ['table', 'figure', 'section', 'chapter']) or
             re.match(r'^\d+\.?\s+[A-Z]', text))):
            return "header"
        
        # Check for list indicators
        if self._detect_list_type(text):
            return "list"
        
        # Check for table captions
        if "table" in text_lower and (":" in text or len(text.split()) < 15):
            return "table_caption"
        
        # Check for figure captions
        if any(word in text_lower for word in ["figure", "fig.", "chart", "graph"]) and len(text.split()) < 15:
            return "figure_caption"
        
        # Check for footers
        if (block['bottom'] > 700 or  # Near bottom of page
            any(pattern in text_lower for pattern in ['page ', 'copyright', '©', 'all rights'])):
            return "footer"
        
        # Default to paragraph
        return "paragraph"
    
    def _extract_title(self, text: str, section_type: str) -> Optional[str]:
        """
        Extract title from section if it's a header
        
        Args:
            text: Section text
            section_type: Type of section
            
        Returns:
            Title string or None
        """
        if section_type == "header":
            # Clean up the title
            title = text.strip()
            # Remove leading numbers/bullets
            title = re.sub(r'^\d+\.?\s*', '', title)
            title = re.sub(r'^\W+', '', title)
            return title if title else None
        
        return None
    
    def _is_llm_ready(self, text: str, word_count: int) -> bool:
        """
        Determine if section is ready for LLM processing
        
        Args:
            text: Section text
            word_count: Number of words
            
        Returns:
            True if section is LLM ready
        """
        min_words = self.section_config.get("min_words_per_section", 10)
        max_words = self.section_config.get("max_words_per_section", 500)
        
        # Check word count
        if word_count < min_words or word_count > max_words:
            return False
        
        # Check for complete sentences
        sentences = text.split('.')
        if len(sentences) < 2:
            return False
        
        # Check for excessive formatting or special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if special_char_ratio > 0.3:
            return False
        
        return True
    
    def _extract_text_metadata(self, block: Dict) -> Dict:
        """
        Extract metadata from text block
        
        Args:
            block: Text block dictionary
            
        Returns:
            Metadata dictionary
        """
        # Extract font information from first word if available
        if block.get('words'):
            first_word = block['words'][0]
            
            return {
                "font_size": first_word.get('size', 12),
                "font_family": first_word.get('fontname', 'Arial'),
                "is_bold": 'Bold' in first_word.get('fontname', ''),
                "is_italic": 'Italic' in first_word.get('fontname', ''),
                "color": None,  # PDFPlumber doesn't easily provide color info
                "alignment": "left",  # Could be enhanced with layout analysis
                "line_spacing": None
            }
        
        return {
            "font_size": 12,
            "font_family": "Arial",
            "is_bold": False,
            "is_italic": False,
            "color": None,
            "alignment": "left",
            "line_spacing": None
        }
    
    def _determine_heading_level(self, text: str, block: Dict) -> Optional[int]:
        """
        Determine heading level based on content and formatting
        
        Args:
            text: Text content
            block: Text block dictionary
            
        Returns:
            Heading level (1-6) or None
        """
        # Get font size from first word if available
        font_size = 12
        if block.get('words'):
            font_size = block['words'][0].get('size', 12)
        
        # Determine level based on font size
        if font_size >= 20:
            return 1
        elif font_size >= 16:
            return 2
        elif font_size >= 14:
            return 3
        elif font_size >= 12:
            return 4
        elif font_size >= 10:
            return 5
        elif font_size >= 8:
            return 6
        
        # Also check content patterns
        if re.match(r'^\d+\.?\s+[A-Z]', text):
            return min(4, text.count('.') + 1)
        
        return None
    
    def _detect_list_type(self, text: str) -> Optional[str]:
        """
        Detect if text represents a list
        
        Args:
            text: Text to analyze
            
        Returns:
            List type ("ordered", "unordered") or None
        """
        lines = text.split('\n')
        if len(lines) < 2:
            # Check single line patterns
            if re.match(r'^\s*[\d\w]+[\.\)]\s+', text) or re.match(r'^\s*[-•*]\s+', text):
                return "ordered" if re.match(r'^\s*\d+[\.\)]', text) else "unordered"
            return None
        
        # Check for ordered list patterns
        ordered_patterns = [r'^\s*\d+\.', r'^\s*\d+\)', r'^\s*[a-z]\.', r'^\s*[A-Z]\.']
        # Check for unordered list patterns
        unordered_patterns = [r'^\s*[-•*]', r'^\s*○', r'^\s*▪', r'^\s*▫']
        
        ordered_count = 0
        unordered_count = 0
        
        for line in lines:
            line = line.strip()
            if any(re.match(pattern, line) for pattern in ordered_patterns):
                ordered_count += 1
            elif any(re.match(pattern, line) for pattern in unordered_patterns):
                unordered_count += 1
        
        if ordered_count > len(lines) * 0.5:
            return "ordered"
        elif unordered_count > len(lines) * 0.5:
            return "unordered"
        
        return None
    
    def _extract_numbers_from_sections(self, sections: List[Dict]) -> List[Dict]:
        """
        Extract numbers from each section and add them to the section's numbers array
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            Updated sections with numbers extracted
        """
        from .pdfplumber_number_extractor import PDFPlumberNumberExtractor
        
        number_extractor = PDFPlumberNumberExtractor()
        
        for section in sections:
            numbers = number_extractor.extract_numbers_from_text(
                section["content"], 
                section["position"], 
                section["metadata"]
            )
            section["numbers"] = numbers
        
        return sections
    
    def _generate_table_of_contents(self, pages: List[Dict]) -> List[Dict]:
        """
        Generate table of contents from document pages
        
        Args:
            pages: List of page dictionaries
            
        Returns:
            List of TOC entries
        """
        toc = []
        
        for page in pages:
            for section in page["sections"]:
                if section["section_type"] == "header" and section["title"]:
                    toc.append({
                        "title": section["title"],
                        "page_number": page["page_number"],
                        "section_id": section["section_id"],
                        "level": section["structure"]["heading_level"] or 1
                    })
        
        return toc
    
    def _finalize_statistics(self, text_content: Dict):
        """
        Calculate final statistics for the document
        
        Args:
            text_content: Text content dictionary to update
        """
        summary = text_content["summary"]
        
        # Calculate averages
        if summary["total_sections"] > 0:
            summary["average_section_length"] = summary["total_words"] / summary["total_sections"]
            summary["reading_time_estimate"] = summary["total_words"] / 200  # 200 words per minute
        
        # Update document metadata
        text_content["document_metadata"]["total_word_count"] = summary["total_words"] 