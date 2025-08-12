#!/usr/bin/env python3
"""
Deprecated backup module for Camelot-based PDF processing.

This file is retained as a compatibility layer and delegates to the
PDFPlumber-based implementation used by the primary module.
"""

from PDF_processing_pdfplumber import (
    PDFProcessor as _PP_PDFProcessor,
    PDFTableExtractor as _PP_PDFTableExtractor,
    PDFTextProcessor as _PP_PDFTextProcessor,
    PDFNumberExtractor as _PP_PDFNumberExtractor,
)

PDFProcessor = _PP_PDFProcessor
PDFTableExtractor = _PP_PDFTableExtractor
PDFTextProcessor = _PP_PDFTextProcessor
PDFNumberExtractor = _PP_PDFNumberExtractor

__all__ = [
    "PDFProcessor",
    "PDFTableExtractor",
    "PDFTextProcessor",
    "PDFNumberExtractor",
]


def main():
    import sys
    import os
    import json

    if len(sys.argv) < 2:
        print("Usage: python PDF_processing_backup.py <pdf_file_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    processor = PDFProcessor()
    result = processor.process_file(pdf_path, extract_tables=True, extract_text=True, extract_numbers=True)

    output_file = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_backup_tables.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Backup processing completed. Results saved to: {output_file}")


