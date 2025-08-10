"""
PDF Result Reconstructor

Merges AI group results and code-only pages into a single pdf_processing_result
structure compatible with docs/pdf-json-schema.md.
"""

from __future__ import annotations

from typing import Any, Dict, List


class PDFResultReconstructor:
    def __init__(self) -> None:
        pass

    def merge(self,
              ai_group_results: List[Dict[str, Any]],
              code_only_pages: List[Dict[str, Any]],
              optional_native_tables: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        """
        Merge AI and code-only outputs into a combined result.
        This is a scaffold focusing on schema shape and ordering guarantees.
        """
        # Collect pages from AI results
        ai_pages: List[Dict[str, Any]] = []
        ai_tables: List[Dict[str, Any]] = []
        for group in ai_group_results:
            text_content = group.get("text_content", {})
            if text_content and "pages" in text_content:
                ai_pages.extend(text_content["pages"])
            group_tables = group.get("tables", []) or []
            ai_tables.extend(group_tables)

        # Merge code-only pages (ensure page uniqueness by page_number)
        pages_by_number: Dict[int, Dict[str, Any]] = {}
        for p in ai_pages:
            pages_by_number[p.get("page_number", 1)] = p
        for p in code_only_pages:
            pages_by_number.setdefault(p.get("page_number", 1), p)

        # Build ordered pages
        all_page_numbers = sorted(pages_by_number.keys())
        ordered_pages = [pages_by_number[n] for n in all_page_numbers]

        # Merge tables
        combined_tables = []
        if optional_native_tables:
            combined_tables.extend(optional_native_tables)
        combined_tables.extend(ai_tables)

        return {
            "pdf_processing_result": {
                "document_metadata": {},
                "tables": {"tables": combined_tables} if combined_tables else {},
                "text_content": {
                    "document_metadata": {},
                    "pages": ordered_pages,
                    "summary": {}
                },
                "processing_summary": {}
            }
        }


