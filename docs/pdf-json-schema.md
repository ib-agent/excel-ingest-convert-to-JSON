# PDF JSON Schema Documentation

This document defines the JSON schemas for PDF processing output, including table extraction and contextual text content extraction with embedded numbers.

## Overview

The PDF processing system produces two distinct JSON structures:

1. **Table-Oriented JSON** - Extracted tables in structured format (similar to Excel processing)
2. **Text Content JSON** - Contextual text sections with embedded numbers, optimized for LLM processing

## 1. Text Content JSON Schema

The text content schema organizes extracted text into logical sections optimized for LLM processing, with metadata about structure, formatting, and embedded numbers.

### Schema Structure

```json
{
  "text_content": {
    "document_metadata": {
      "filename": "string",
      "total_pages": "number",
      "extraction_timestamp": "string (ISO 8601)",
      "extraction_method": "string",
      "total_word_count": "number"
    },
    "pages": [
      {
        "page_number": "number",
        "page_width": "number",
        "page_height": "number",
        "sections": [
          {
            "section_id": "string",
            "section_type": "header|paragraph|list|table_caption|figure_caption|footer|sidebar",
            "title": "string|null",
            "content": "string",
            "word_count": "number",
            "character_count": "number",
            "llm_ready": "boolean",
            "position": {
              "start_y": "number",
              "end_y": "number",
              "bbox": [x1, y1, x2, y2],
              "column_index": "number"
            },
            "metadata": {
              "font_size": "number|null",
              "font_family": "string|null",
              "is_bold": "boolean",
              "is_italic": "boolean",
              "color": "string|null",
              "alignment": "left|center|right|justify",
              "line_spacing": "number|null"
            },
            "structure": {
              "heading_level": "number|null",
              "list_type": "ordered|unordered|null",
              "list_level": "number|null",
              "is_continuation": "boolean"
            },
            "relationships": {
              "parent_section": "string|null",
              "child_sections": ["string"],
              "related_tables": ["string"],
              "related_figures": ["string"]
            },
            "numbers": [
              {
                "value": "number",
                "original_text": "string",
                "context": "string",
                "position": {
                  "x": "number",
                  "y": "number",
                  "bbox": [x1, y1, x2, y2],
                  "line_number": "number"
                },
                "format": "integer|decimal|percentage|currency|scientific_notation|fraction|date_number",
                "unit": "string|null",
                "currency": "string|null",
                "confidence": "number (0.0-1.0)",
                "extraction_method": "regex_pattern|ml_model|rule_based",
                "metadata": {
                  "font_size": "number|null",
                  "font_family": "string|null",
                  "is_bold": "boolean",
                  "is_italic": "boolean",
                  "color": "string|null"
                }
              }
            ]
          }
        ]
      }
    ],
    "document_structure": {
      "toc": [
        {
          "title": "string",
          "page_number": "number",
          "section_id": "string",
          "level": "number"
        }
      ],
      "sections_by_type": {
        "header": "number",
        "paragraph": "number",
        "list": "number",
        "table_caption": "number",
        "figure_caption": "number",
        "footer": "number",
        "sidebar": "number"
      }
    },
    "summary": {
      "total_sections": "number",
      "total_words": "number",
      "llm_ready_sections": "number",
      "average_section_length": "number",
      "reading_time_estimate": "number (minutes)",
      "total_numbers_found": "number"
    }
  }
}
```

### Section Object Properties

#### Core Properties
- **section_id**: Unique identifier for the section
- **section_type**: Type of content section
- **title**: Section title or heading (if applicable)
- **content**: The actual text content
- **word_count**: Number of words in the section
- **character_count**: Number of characters in the section
- **llm_ready**: Whether the section is optimized for LLM processing
- **position**: Spatial positioning information
- **metadata**: Formatting and styling information
- **structure**: Structural information about the section
- **relationships**: Connections to other sections and elements
- **numbers**: Array of numbers found within this section

#### Position Object
- **start_y, end_y**: Vertical position range
- **bbox**: Bounding box coordinates [x1, y1, x2, y2]
- **column_index**: Column number for multi-column layouts

#### Metadata Object
- **font_size**: Font size in points
- **font_family**: Font family name
- **is_bold**: Whether the text is bold
- **is_italic**: Whether the text is italic
- **color**: Text color in hex format
- **alignment**: Text alignment
- **line_spacing**: Line spacing value

#### Structure Object
- **heading_level**: Heading level (1-6, null for non-headings)
- **list_type**: Type of list (ordered, unordered, or null)
- **list_level**: Nesting level for lists
- **is_continuation**: Whether this section continues from previous page

#### Relationships Object
- **parent_section**: ID of parent section (for nested content)
- **child_sections**: Array of child section IDs
- **related_tables**: Array of related table IDs
- **related_figures**: Array of related figure IDs

#### Numbers Array
Each number object in the numbers array contains:
- **value**: The extracted numerical value
- **original_text**: The exact text as it appears in the PDF
- **context**: Surrounding text that provides context for the number
- **position**: Spatial and logical positioning information
- **format**: The type of number format detected
- **unit**: Associated unit of measurement (if any)
- **currency**: Currency symbol or code (for monetary values)
- **confidence**: Extraction confidence score (0.0-1.0)
- **extraction_method**: Method used to extract the number
- **metadata**: Font and styling information for the number

### Number Format Types

1. **integer**: Whole numbers (e.g., 1500, -42)
2. **decimal**: Decimal numbers (e.g., 15.5, -3.14)
3. **percentage**: Percentages (e.g., 25%, 15.5%)
4. **currency**: Monetary values (e.g., $1,500, €25.50)
5. **scientific_notation**: Scientific notation (e.g., 1.5e6, 2.3E-4)
6. **fraction**: Fractions (e.g., 1/2, 3/4)
7. **date_number**: Numbers that are part of dates (e.g., 2023, 15th)

### Section Types

1. **header**: Document headers, titles, and headings
2. **paragraph**: Regular text paragraphs
3. **list**: Ordered or unordered lists
4. **table_caption**: Captions for tables
5. **figure_caption**: Captions for figures and images
6. **footer**: Document footers and page numbers
7. **sidebar**: Sidebar content and callouts

### LLM Readiness Criteria

A section is considered "llm_ready" when it meets these criteria:
- Word count between 50-1000 words
- Complete sentences and logical structure
- No excessive formatting or special characters
- Clear context and meaning
- Appropriate for standalone processing

### Example Text Content Output with Embedded Numbers

```json
{
  "text_content": {
    "document_metadata": {
      "filename": "annual_report_2023.pdf",
      "total_pages": 25,
      "extraction_timestamp": "2024-01-15T10:30:00Z",
      "extraction_method": "pymupdf_enhanced",
      "total_word_count": 15420
    },
    "pages": [
      {
        "page_number": 1,
        "page_width": 612,
        "page_height": 792,
        "sections": [
          {
            "section_id": "title_page_1",
            "section_type": "header",
            "title": "Annual Report 2023",
            "content": "Annual Report 2023",
            "word_count": 3,
            "character_count": 18,
            "llm_ready": false,
            "position": {
              "start_y": 100,
              "end_y": 120,
              "bbox": [156.2, 100.0, 455.8, 120.0],
              "column_index": 0
            },
            "metadata": {
              "font_size": 24,
              "font_family": "Times New Roman",
              "is_bold": true,
              "is_italic": false,
              "color": "#000000",
              "alignment": "center",
              "line_spacing": 1.2
            },
            "structure": {
              "heading_level": 1,
              "list_type": null,
              "list_level": null,
              "is_continuation": false
            },
            "relationships": {
              "parent_section": null,
              "child_sections": ["executive_summary_1"],
              "related_tables": [],
              "related_figures": []
            },
            "numbers": [
              {
                "value": 2023,
                "original_text": "2023",
                "context": "Annual Report 2023",
                "position": {
                  "x": 420.5,
                  "y": 110.0,
                  "bbox": [420.5, 105.0, 435.8, 115.0],
                  "line_number": 1
                },
                "format": "date_number",
                "unit": null,
                "currency": null,
                "confidence": 0.99,
                "extraction_method": "regex_pattern",
                "metadata": {
                  "font_size": 24,
                  "font_family": "Times New Roman",
                  "is_bold": true,
                  "is_italic": false,
                  "color": "#000000"
                }
              }
            ]
          },
          {
            "section_id": "executive_summary_1",
            "section_type": "paragraph",
            "title": null,
            "content": "This annual report presents a comprehensive overview of our company's performance, strategic initiatives, and financial results for the fiscal year 2023. Throughout the year, we continued to focus on innovation, operational excellence, and sustainable growth while navigating challenging market conditions. Our commitment to delivering value to shareholders, customers, and employees remained unwavering as we executed our long-term strategic plan. Total revenue for Q4 2023 reached $1,500,000, representing a 25.5% increase over the previous quarter.",
            "word_count": 75,
            "character_count": 520,
            "llm_ready": true,
            "position": {
              "start_y": 140,
              "end_y": 220,
              "bbox": [72.0, 140.0, 540.0, 220.0],
              "column_index": 0
            },
            "metadata": {
              "font_size": 12,
              "font_family": "Arial",
              "is_bold": false,
              "is_italic": false,
              "color": "#000000",
              "alignment": "justify",
              "line_spacing": 1.15
            },
            "structure": {
              "heading_level": null,
              "list_type": null,
              "list_level": null,
              "is_continuation": false
            },
            "relationships": {
              "parent_section": "title_page_1",
              "child_sections": [],
              "related_tables": ["financial_summary_table"],
              "related_figures": []
            },
            "numbers": [
              {
                "value": 2023,
                "original_text": "2023",
                "context": "fiscal year 2023",
                "position": {
                  "x": 245.6,
                  "y": 156.8,
                  "bbox": [240.2, 152.4, 268.9, 161.2],
                  "line_number": 2
                },
                "format": "date_number",
                "unit": null,
                "currency": null,
                "confidence": 0.99,
                "extraction_method": "regex_pattern",
                "metadata": {
                  "font_size": 12,
                  "font_family": "Arial",
                  "is_bold": false,
                  "is_italic": false,
                  "color": "#000000"
                }
              },
              {
                "value": 1500000,
                "original_text": "$1,500,000",
                "context": "Total revenue for Q4 2023 reached $1,500,000",
                "position": {
                  "x": 312.4,
                  "y": 200.5,
                  "bbox": [308.1, 195.0, 325.7, 205.0],
                  "line_number": 4
                },
                "format": "currency",
                "unit": "dollars",
                "currency": "USD",
                "confidence": 0.95,
                "extraction_method": "regex_pattern",
                "metadata": {
                  "font_size": 12,
                  "font_family": "Arial",
                  "is_bold": true,
                  "is_italic": false,
                  "color": "#000000"
                }
              },
              {
                "value": 25.5,
                "original_text": "25.5%",
                "context": "representing a 25.5% increase over the previous quarter",
                "position": {
                  "x": 380.2,
                  "y": 200.5,
                  "bbox": [375.8, 195.0, 393.4, 205.0],
                  "line_number": 4
                },
                "format": "percentage",
                "unit": null,
                "currency": null,
                "confidence": 0.98,
                "extraction_method": "regex_pattern",
                "metadata": {
                  "font_size": 12,
                  "font_family": "Arial",
                  "is_bold": false,
                  "is_italic": false,
                  "color": "#000000"
                }
              }
            ]
          }
        ]
      }
    ],
    "document_structure": {
      "toc": [
        {
          "title": "Annual Report 2023",
          "page_number": 1,
          "section_id": "title_page_1",
          "level": 1
        },
        {
          "title": "Executive Summary",
          "page_number": 1,
          "section_id": "executive_summary_1",
          "level": 2
        }
      ],
      "sections_by_type": {
        "header": 15,
        "paragraph": 89,
        "list": 12,
        "table_caption": 8,
        "figure_caption": 6,
        "footer": 25,
        "sidebar": 3
      }
    },
    "summary": {
      "total_sections": 158,
      "total_words": 15420,
      "llm_ready_sections": 67,
      "average_section_length": 97.6,
      "reading_time_estimate": 77,
      "total_numbers_found": 47
    }
  }
}
```

## 2. Combined Output Structure

When both extraction types are performed, the complete output structure is:

```json
{
  "pdf_processing_result": {
    "document_metadata": {
      "filename": "string",
      "total_pages": "number",
      "processing_timestamp": "string (ISO 8601)",
      "processing_duration": "number (seconds)",
      "extraction_methods": ["table_extraction", "text_extraction"]
    },
    "tables": {
      // Table-oriented JSON structure (from existing Excel schema)
    },
    "text_content": {
      // Text content JSON structure with embedded numbers
    },
    "processing_summary": {
      "tables_extracted": "number",
      "numbers_found": "number",
      "text_sections": "number",
      "overall_quality_score": "number (0.0-1.0)",
      "processing_errors": ["string"]
    }
  }
}
```

## Configuration Options

### Number Extraction Configuration

```json
{
  "number_extraction": {
    "patterns": {
      "integer": "\\b\\d{1,3}(?:,\\d{3})*\\b",
      "decimal": "\\b\\d+\\.\\d+\\b",
      "percentage": "\\b\\d+(?:\\.\\d+)?%\\b",
      "currency": "\\$\\s*\\d+(?:,\\d{3})*(?:\\.\\d{2})?",
      "scientific_notation": "\\b\\d+(?:\\.\\d+)?[eE][+-]?\\d+\\b"
    },
    "context_window": 100,
    "confidence_threshold": 0.7,
    "extract_metadata": true,
    "include_positioning": true,
    "prevent_overlapping_matches": true
  }
}
```

### Text Extraction Configuration

```json
{
  "text_extraction": {
    "section_detection": {
      "min_section_size": 50,
      "max_section_size": 1000,
      "use_headers": true,
      "detect_lists": true
    },
    "llm_optimization": {
      "enabled": true,
      "min_words": 50,
      "max_words": 1000,
      "preserve_structure": true
    },
    "metadata_extraction": {
      "font_info": true,
      "positioning": true,
      "relationships": true
    },
    "number_extraction": {
      "enabled": true,
      "embed_in_sections": true
    }
  }
}
```

## Quality Metrics

### Number Extraction Quality
- **Accuracy**: Percentage of correctly extracted numbers
- **Completeness**: Percentage of numbers found vs. expected
- **Context Quality**: Relevance of extracted context
- **Positioning Accuracy**: Accuracy of spatial positioning
- **Duplicate Prevention**: Effectiveness of overlapping match prevention

### Text Extraction Quality
- **Readability**: Text flow and logical structure
- **Completeness**: Percentage of text extracted
- **Section Detection**: Accuracy of section boundaries
- **LLM Readiness**: Percentage of sections optimized for LLM processing
- **Number Integration**: Quality of number embedding within sections

## Error Handling

### Common Extraction Errors
1. **OCR Errors**: Poor text recognition in scanned documents
2. **Layout Issues**: Complex multi-column layouts
3. **Font Problems**: Unusual or missing fonts
4. **Table Detection**: False positives or missed tables
5. **Number Recognition**: Ambiguous number formats
6. **Duplicate Numbers**: Overlapping regex matches

### Error Response Format

```json
{
  "error": {
    "type": "extraction_error|validation_error|processing_error",
    "message": "string",
    "details": {
      "page_number": "number|null",
      "section_id": "string|null",
      "error_code": "string",
      "suggestions": ["string"]
    },
    "timestamp": "string (ISO 8601)"
  }
}
```

This comprehensive schema documentation provides the foundation for implementing robust PDF processing capabilities with detailed extraction of tables and text content with embedded numbers. 