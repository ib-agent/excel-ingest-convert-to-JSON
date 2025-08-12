# PDF Processing Approach

This document outlines the comprehensive plan for processing PDF documents to extract tables, numbers in text, and contextual text content into structured JSON formats.

> Deprecation and current standard
>
> Camelot-based processing is deprecated in this project. PDFPlumber is the single, standard library for PDF table and text extraction. Any Camelot references in this document are historical. For implementation details, refer to `converter/pdfplumber_processor.py` and related PDFPlumber modules. The legacy entry point `PDF_processing.py` is now a compatibility shim that delegates to the PDFPlumber implementation.

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

## AI Failover Strategy and Routing (New)

To increase robustness when native table detection is unreliable, we introduce an AI failover strategy driven by page-level complexity analysis. The core ideas:

- Analyze every page for numeric density and table-likeness to create a per-page complexity score.
- Group consecutive pages that contain numbers into compact batches and route only those groups to the AI for extraction.
- Ask the AI to return both:
  - Table-oriented output compatible with the table schema documented in `table-oriented-json-schema.md` (tables with page and bbox).
  - Text sections with embedded numbers conforming to `pdf-json-schema.md` (text_content schema with numbers array per section).
- Pages without numbers are still represented as paragraphs; these are extracted purely by code and not sent to AI.
- Reconstruct the full `pdf-json-schema` by merging AI outputs for numeric page groups with code-extracted text sections for the remaining pages, preserving page order.

This minimizes token usage and latency for large documents while improving accuracy on pages most likely to contain tables or important numeric content.

### Page Complexity Analysis & Grouping

For each page, compute:

- number_count: count of numbers detected via regex patterns consistent with `docs/pdf-json-schema.md` number types
- number_density: numbers per 1000 characters and per square inch (when bbox data available)
- layout_signals: optional heuristics such as high alignment regularity, dense vertical lines, repeating column start x positions, and short-line variance indicative of tabular layouts
- text_ratio: words-to-numbers ratio

Use thresholds to assign a page category:

- none_or_low_numbers → code-only paragraph extraction
- numeric_text → route group to AI for numbers-in-text + paragraph structure
- probable_table → route group to AI requesting both tables and text

Consecutive pages with category ∈ {numeric_text, probable_table} are merged into a group with size constraints (e.g., 1–5 pages per group, capped by token budget). Non-numeric pages between numeric pages form natural group boundaries.

### AI Request & Response Contracts

- Inputs per page group:
  - Page renders (PNG) when vision models are available; otherwise, page-level structured text with positioning (extracted via PyMuPDF)
  - Minimal context: document-level metadata, page indices, and requested output schemas
- Outputs per page group (from AI):
  - tables: array of tables in table-oriented format, each including page_number and bbox
  - text_content: sections per page with embedded numbers and metadata per `docs/pdf-json-schema.md`
  - processing_summary: counts and simple quality flags

If AI extraction fails or confidence is below threshold, fall back to code-only extraction for that group and mark an error in `processing_summary`.

## Architecture Plan

### 1. PDF Processor Core (`pdf_processor.py`)

```python
class PDFProcessor:
    def __init__(self):
        self.camelot = None
        self.fitz_doc = None
        self.page_analyzer = None  # PDFPageComplexityAnalyzer
        self.ai_router = None      # PDFAIFailoverRouter
    
    def process_file(self, file_path):
        # 1) Load doc with PyMuPDF
        # 2) Analyze pages → complexity scores, categories
        # 3) Create consecutive page groups (numeric-only)
        # 4) For numeric groups: call AI for tables + numbers-in-text
        # 5) For non-numeric pages: code-only text extraction
        # 6) Run native table extraction (camelot) opportunistically; merge if quality≥threshold
        # 7) Reconstruct full pdf-json-schema (merge, dedupe, order)
        # 8) Return combined output and processing_summary
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

### 4. Page Complexity Analyzer (`pdf_page_complexity_analyzer.py`)

```python
class PDFPageComplexityAnalyzer:
    def __init__(self, thresholds):
        self.thresholds = thresholds

    def analyze_pages(self, fitz_doc):
        # returns list of page_metrics with number_count, number_density, layout_signals, text_ratio, category
        pass

    def group_numeric_pages(self, page_metrics):
        # returns list of (start_page, end_page) for consecutive numeric pages within size/token limits
        pass
```

### 5. AI Failover Router (`pdf_ai_router.py`)

```python
class PDFAIFailoverRouter:
    def __init__(self, ai_client, config):
        self.ai_client = ai_client
        self.config = config

    def process_groups(self, fitz_doc, page_groups):
        # For each group, prepare inputs (images or structured text) and request AI outputs
        # Returns list of ai_results with tables, text_content, and summaries
        pass
```

### 6. Result Merger/Reconstructor (`pdf_result_reconstructor.py`)

```python
class PDFResultReconstructor:
    def __init__(self):
        pass

    def merge(self, ai_group_results, code_only_pages, optional_native_tables):
        # 1) Build text_content pages in order 1..N
        # 2) Union tables from AI and native (dedupe by page_number+bbox overlap and header similarity)
        # 3) Produce combined pdf_processing_result with processing_summary
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
        "detection_method": "pdfplumber"
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
        "detection_method": "pdfplumber",
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

### Combined Output Reconstruction Notes (New)

- Always produce a `text_content.pages` entry for every page in the document.
- For pages not routed to AI, create sections from code-only extraction (paragraphs, headers, lists) without AI augmentation.
- For pages routed to AI, prefer AI-provided sections and embedded numbers; optionally enrich with code-detected metadata if non-conflicting.
- Consolidate all tables (from AI and native) under a `tables` structure, with each table carrying `page_number`, `bbox`, and `detection_method` = `ai_extraction` or `pdfplumber`.
- Maintain stable IDs to support downstream diffing: `table_id` as `p{page}_t{index}` and `section_id` as `p{page}_s{index}` within reconstruction step.

## Implementation Phases

### Phase 0: AI Failover & Routing Foundations (New)
**Duration**: 3–5 days

**Tasks:**
1. Implement `PDFPageComplexityAnalyzer` with numeric detection and basic layout signals.
2. Implement grouping of consecutive numeric pages with size/token limits.
3. Add `PDFAIFailoverRouter` and wire configurable AI client (vision if available; fallback to structured text prompts).
4. Define AI prompt/response contracts to produce both table-oriented output and `text_content` with embedded numbers.
5. Implement `PDFResultReconstructor` to merge AI outputs with code-only pages and optional native tables.

**Deliverables:**
- Page metrics and grouping
- AI routing and minimal working integration
- End-to-end reconstruction for mixed AI/code outputs

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
├── pdf_page_complexity_analyzer.py  # New: page complexity & grouping
├── pdf_ai_router.py          # New: AI failover routing for numeric groups
├── pdf_result_reconstructor.py # New: merge AI and code outputs
├── table_extractor.py        # Table extraction logic
├── text_processor.py         # Text and number extraction
├── anthropic_pdf_client.py   # New: AI provider client (or reuse existing client pattern)
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
    "table_settings": {
      "vertical_strategy": "lines",
      "horizontal_strategy": "lines"
    },
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

### AI Failover Configuration (New)

```json
{
  "ai_failover": {
    "enabled": true,
    "use_vision_if_available": true,
    "numeric_page_thresholds": {
      "min_numbers_per_page": 3,
      "min_number_density": 0.5
    },
    "table_likeness": {
      "enable_layout_signals": true,
      "min_score": 0.6
    },
    "grouping": {
      "max_pages_per_group": 5,
      "max_tokens_per_group": 20000,
      "respect_nonnumeric_boundaries": true
    },
    "routing": {
      "send_numeric_text_pages": true,
      "send_probable_table_pages": true
    },
    "confidence": {
      "min_ai_quality_score": 0.7,
      "fallback_to_code_on_low_confidence": true
    },
    "rate_limits": {
      "max_concurrent_groups": 3
    }
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
- Parallelize AI calls across groups with respect to provider rate limits

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