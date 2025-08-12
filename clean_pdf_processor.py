#!/usr/bin/env python3
"""
Clean PDF Processing Pipeline (PDFPlumber-based compatibility shim)

This module historically implemented a Camelot-based pipeline. The project has
standardized on PDFPlumber. To avoid breaking imports in existing code/tests,
this file re-exports the PDFPlumber implementations under the original class
names:

- CleanPDFProcessor
- SimpleTableExtractor
- TextExtractor
- NumberExtractor
"""

from pdfplumber_clean_processor import (
    CleanPDFProcessor as _PP_CleanPDFProcessor,
    PDFPlumberTableExtractor as _PP_TableExtractor,
    PDFPlumberTextExtractor as _PP_TextExtractor,
    NumberExtractor as _PP_NumberExtractor,
)

# Maintain original class names for API compatibility
CleanPDFProcessor = _PP_CleanPDFProcessor
SimpleTableExtractor = _PP_TableExtractor
TextExtractor = _PP_TextExtractor
NumberExtractor = _PP_NumberExtractor

__all__ = [
    "CleanPDFProcessor",
    "SimpleTableExtractor",
    "TextExtractor",
    "NumberExtractor",
]

def main():
    """Compatibility entrypoint mirroring original behavior."""
    import sys
    import json
    from pathlib import Path

    if len(sys.argv) != 2:
        print("Usage: python clean_pdf_processor.py <pdf_file>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"Error: File {pdf_path} not found")
        sys.exit(1)

    processor = CleanPDFProcessor()
    result = processor.process(pdf_path)

    output_file = f"{Path(pdf_path).stem}_pdfplumber_clean_results.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Processing completed. Results saved to: {output_file}")

if __name__ == "__main__":
    main()


