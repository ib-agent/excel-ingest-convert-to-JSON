# PDF Processing Approach

This document outlines the comprehensive plan for processing PDF documents to extract tables, numbers in text, and contextual text content into structured JSON formats.

## Overview

The PDF processing system will extract three main components from PDF documents:

1. **Tables** → Table-oriented JSON structure (similar to Excel processing)
2. **Numbers in text** → Numbers-in-text JSON structure (new)
3. **Text content** → Contextual text JSON structure (new)

## Technology Stack Analysis

### 1. Camelot-py for Table Extraction

**Why Camelot-py is ideal:**
- **High accuracy**: Uses computer vision and machine learning for table detection
- **Multiple extraction methods**: 
  - `stream` mode for text-based tables
  - `lattice` mode for tables with borders
- **Advanced features**:
  - Handles merged cells
  - Supports multi-page tables
  - Can extract tables with complex layouts
  - Provides table quality metrics
- **Output format**: Returns pandas DataFrames that we can easily convert to JSON
- **Active development**: Well-maintained with good documentation

**Installation**: `pip install camelot-py[cv]`

**Key Benefits:**
- Superior table detection accuracy compared to other libraries
- Handles complex table layouts and merged cells
- Provides quality metrics for extraction confidence
- Supports both bordered and borderless tables

### 2. PyMuPDF (fitz) for Text and Number Extraction

**Why PyMuPDF is ideal:**
- **Comprehensive text extraction**: 
  - Extracts text with positioning information
  - Maintains reading order
  - Handles columns and layouts
- **Advanced features**:
  - Font and styling information
  - Page-by-page processing
  - Image extraction capabilities
  - PDF metadata access
- **Performance**: Fast and memory-efficient
- **Flexibility**: Can extract text blocks, lines, words, and characters

**Installation**: `pip install PyMuPDF`

**Key Benefits:**
- Excellent text extraction with spatial information
- High performance for large documents
- Rich API for custom extraction logic
- Maintains document structure and formatting

## Architecture Plan

### 1. PDF Processor Core (`pdf_processor.py`)

```python
class PDFProcessor:
    def __init__(self):
        self.camelot = None
        self.fitz_doc = None
    
    def process_file(self, file_path):
        # Main processing pipeline
        pass
    
    def extract_tables(self):
        # Use camelot-py for table extraction
        pass
    
    def extract_text_content(self):
        # Use PyMuPDF for text extraction
        pass
    
    def extract_numbers_in_text(self):
        # Parse text content for numerical data
        pass
```

### 2. Table Extractor (`table_extractor.py`)

```python
class PDFTableExtractor:
    def __init__(self):
        self.extraction_methods = ['stream', 'lattice']
    
    def extract_tables(self, pdf_path):
        # Use camelot-py to extract tables
        # Convert to table-oriented JSON structure
        pass
    
    def convert_to_table_json(self, table_data):
        # Transform camelot output to your table schema
        pass
```

### 3. Text Processor (`text_processor.py`)

```python
class PDFTextProcessor:
    def __init__(self):
        self.number_patterns = []
        self.section_detectors = []
    
    def extract_text_content(self, pdf_path):
        # Use PyMuPDF to extract text with context
        pass
    
    def detect_sections(self, text_content):
        # Identify logical sections for LLM processing
        pass
    
    def extract_numbers_in_text(self, text_content):
        # Find and structure numerical data in text
        pass
```

## JSON Schema Definitions

### Table-Oriented JSON Structure

Leverages the existing table-oriented JSON schema from Excel processing:

```json
{
  "tables": [
    {
      "table_id": "table_1",
      "name": "Table 1",
      "region": {
        "page_number": 1,
        "bbox": [x1, y1, x2, y2],
        "detection_method": "camelot_lattice"
      },
      "header_info": {
        "header_rows": [0],
        "data_start_row": 1
      },
      "columns": [
        {
          "column_index": 0,
          "column_label": "Product Name",
          "is_header_column": false,
          "cells": {}
        }
      ],
      "rows": [
        {
          "row_index": 0,
          "row_label": "Product Name",
          "is_header_row": true,
          "cells": {}
        }
      ],
      "metadata": {
        "detection_method": "camelot_lattice",
        "quality_score": 0.95,
        "cell_count": 25
      }
    }
  ]
}
```

### Numbers-in-Text JSON Structure

```json
{
  "numbers_in_text": [
    {
      "page_number": 1,
      "section_id": "section_1",
      "numbers": [
        {
          "value": 1500,
          "context": "Sales increased by 1500 units",
          "position": {
            "x": 100,
            "y": 200,
            "bbox": [x1, y1, x2, y2]
          },
          "format": "integer",
          "unit": "units",
          "confidence": 0.95,
          "extraction_method": "regex_pattern"
        }
      ]
    }
  ]
}
```

### Contextual Text JSON Structure

```json
{
  "text_content": [
    {
      "page_number": 1,
      "sections": [
        {
          "section_id": "section_1",
          "title": "Executive Summary",
          "content": "text content here...",
          "word_count": 150,
          "llm_ready": true,
          "position": {
            "start_y": 100,
            "end_y": 300,
            "bbox": [x1, y1, x2, y2]
          },
          "metadata": {
            "font_size": 12,
            "font_family": "Arial",
            "is_bold": false
          }
        }
      ]
    }
  ]
}
```

## Implementation Phases

### Phase 1: Core Infrastructure
**Duration**: 1-2 weeks

**Tasks:**
1. Create `PDFProcessor` class with basic structure
2. Set up camelot-py and PyMuPDF integration
3. Create basic file upload and processing endpoints
4. Implement error handling and validation
5. Add PDF file validation and security checks

**Deliverables:**
- Basic PDF upload functionality
- Core processing pipeline
- Error handling framework

### Phase 2: Table Extraction
**Duration**: 2-3 weeks

**Tasks:**
1. Implement table detection using camelot-py
2. Convert camelot output to table-oriented JSON
3. Handle multi-page tables
4. Add table quality assessment
5. Implement table filtering and optimization

**Deliverables:**
- Table extraction functionality
- Quality scoring system
- Multi-page table support

### Phase 3: Text and Number Extraction
**Duration**: 2-3 weeks

**Tasks:**
1. Implement text extraction with PyMuPDF
2. Create section detection algorithms
3. Develop number extraction patterns
4. Structure text for LLM processing
5. Add text quality assessment

**Deliverables:**
- Text extraction with context
- Number detection and extraction
- Section identification

### Phase 4: Integration and UI
**Duration**: 1-2 weeks

**Tasks:**
1. Update Django views for PDF processing
2. Enhance frontend for PDF upload
3. Add progress tracking
4. Implement download functionality
5. Add processing options and configurations

**Deliverables:**
- Complete UI integration
- Progress tracking
- Download functionality

### Phase 5: Advanced Features
**Duration**: 2-3 weeks

**Tasks:**
1. Add table quality filtering
2. Implement OCR for scanned PDFs
3. Add batch processing capabilities
4. Create processing options and configurations
5. Performance optimization

**Deliverables:**
- Advanced processing options
- OCR support
- Batch processing
- Performance optimizations

## File Structure

```
converter/
├── pdf_processor.py          # Main PDF processing class
├── table_extractor.py        # Table extraction logic
├── text_processor.py         # Text and number extraction
├── pdf_models.py            # PDF-specific data models
├── pdf_views.py             # PDF processing views
└── templates/converter/
    └── pdf_processor.html    # Updated UI

docs/
├── PDF-processing-approach.md    # This document
├── pdf-json-schema.md           # Detailed JSON schemas
└── pdf-processing-guide.md      # Implementation guide
```

## Key Features

### 1. Multi-format Support
- Handle various PDF layouts and table styles
- Support for both text-based and image-based PDFs
- Adaptive extraction methods based on content type

### 2. Quality Assessment
- Table extraction quality scoring
- Text extraction confidence metrics
- Number detection accuracy assessment

### 3. Configurable Processing
- Allow users to customize extraction parameters
- Configurable table detection sensitivity
- Adjustable text processing options

### 4. Progress Tracking
- Real-time processing status updates
- Detailed progress information
- Error reporting and recovery

### 5. Error Handling
- Graceful handling of problematic PDFs
- Detailed error messages and suggestions
- Fallback extraction methods

### 6. Batch Processing
- Handle multiple PDFs efficiently
- Queue-based processing system
- Resource management and optimization

## Configuration Options

### Table Extraction Configuration

```json
{
  "table_extraction": {
    "methods": ["lattice", "stream"],
    "quality_threshold": 0.8,
    "edge_tolerance": 3,
    "row_tolerance": 3,
    "column_tolerance": 3,
    "min_table_size": 4
  }
}
```

### Text Extraction Configuration

```json
{
  "text_extraction": {
    "extract_metadata": true,
    "preserve_formatting": true,
    "section_detection": {
      "min_section_size": 50,
      "max_section_size": 1000,
      "use_headers": true
    }
  }
}
```

### Number Extraction Configuration

```json
{
  "number_extraction": {
    "patterns": [
      "currency",
      "percentages",
      "integers",
      "decimals",
      "scientific_notation"
    ],
    "context_window": 100,
    "confidence_threshold": 0.7
  }
}
```

## Performance Considerations

### Memory Management
- Process PDFs page by page to minimize memory usage
- Implement streaming for large files
- Use efficient data structures for intermediate results

### Processing Speed
- Parallel processing for multi-page documents
- Caching of intermediate results
- Optimized extraction algorithms

### Scalability
- Queue-based processing for batch operations
- Resource pooling for concurrent requests
- Configurable processing limits

## Security Considerations

### File Validation
- Validate PDF file integrity
- Check for malicious content
- Implement file size limits

### Processing Safety
- Sandboxed processing environment
- Timeout mechanisms
- Resource usage limits

### Data Privacy
- Secure temporary file handling
- Encrypted storage of sensitive data
- Proper cleanup of temporary files

## Testing Strategy

### Unit Tests
- Individual component testing
- Mock PDF file testing
- Error condition testing

### Integration Tests
- End-to-end processing tests
- API endpoint testing
- UI functionality testing

### Performance Tests
- Large file processing tests
- Concurrent processing tests
- Memory usage tests

## Future Enhancements

### Advanced Features
- Machine learning-based table detection
- Custom extraction rules
- Template-based processing
- Multi-language support

### Integration Capabilities
- Cloud storage integration
- API webhook support
- Third-party service integration
- Export to various formats

### User Experience
- Drag-and-drop interface
- Real-time preview
- Processing history
- User preferences and settings

This comprehensive approach ensures a robust, scalable, and user-friendly PDF processing system that can handle a wide variety of document types and extraction requirements. 