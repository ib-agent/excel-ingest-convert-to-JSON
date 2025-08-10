"""
PDF AI Failover Pipeline

Coordinates page complexity analysis, AI routing, and result reconstruction.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple, Set

from .pdf_page_complexity_analyzer import PDFPageComplexityAnalyzer, AnalyzerThresholds
from .pdf_ai_router import PDFAIFailoverRouter, AIFailoverConfig
from .pdf_result_reconstructor import PDFResultReconstructor
from .anthropic_pdf_client import AnthropicPDFClient
from .pdf_pymupdf_table_detector import PyMuPDFTableDetector


class PDFAIFailoverPipeline:
    def __init__(self,
                 analyzer_thresholds: AnalyzerThresholds | None = None,
                 ai_config: AIFailoverConfig | None = None,
                 ai_client: Any | None = None) -> None:
        self.analyzer = PDFPageComplexityAnalyzer(analyzer_thresholds)
        self.ai_client = ai_client or AnthropicPDFClient()
        self.router = PDFAIFailoverRouter(self.ai_client, ai_config)
        self.reconstructor = PDFResultReconstructor()

    def process(self, file_path: str) -> Dict[str, Any]:
        fitz_doc, page_count = self._open_pdf(file_path)

        page_metrics = self.analyzer.analyze_pages(fitz_doc)
        numeric_groups = self.analyzer.group_numeric_pages(page_metrics)

        ai_results = self.router.process_groups(fitz_doc, numeric_groups)

        # Determine code-only pages (not in any numeric group)
        grouped_pages: Set[int] = set()
        for (s, e) in numeric_groups:
            grouped_pages.update(range(s, e + 1))
        # Build initial code-only pages for non-grouped pages
        code_only_pages = self._build_code_only_pages(fitz_doc, page_count, grouped_pages)

        # If AI returned no text pages (e.g., disabled/unavailable), include grouped (numeric) pages as code-only as well
        total_ai_pages = sum(len(gr.get("text_content", {}).get("pages", [])) for gr in ai_results)
        if total_ai_pages == 0:
            code_only_pages = self._build_code_only_pages(fitz_doc, page_count, grouped_pages=set())

        # Optional fallback table detection via PyMuPDF on numeric pages if AI yields no tables
        native_tables: List[Dict[str, Any]] = []
        # Determine numeric pages by metrics for fallback table detection
        numeric_pages: List[int] = []
        for m in page_metrics:
            if m.get("number_count", 0) > 0:
                numeric_pages.append(m["page_index"])  # 0-based

        if not any(gr.get("tables") for gr in ai_results):
            detector = PyMuPDFTableDetector(min_rows=2)
            # Prefer numeric_groups pages; if none, fall back to any numeric page detected
            if numeric_groups:
                target_pages = []
                for (s, e) in numeric_groups:
                    target_pages.extend(range(s, e + 1))
            else:
                target_pages = numeric_pages

            for p in target_pages:
                page = fitz_doc[p] if hasattr(fitz_doc, "__getitem__") else fitz_doc.pages[p]
                native_tables.extend(detector.detect_tables_on_page(page, p + 1))

        merged = self.reconstructor.merge(ai_results, code_only_pages, optional_native_tables=native_tables or None)
        # Add basic metadata
        merged["pdf_processing_result"]["document_metadata"].update({
            "filename": file_path.split("/")[-1],
            "total_pages": page_count,
            "extraction_methods": ["ai_failover_routing"],
        })
        merged["pdf_processing_result"]["processing_summary"].update({
            "tables_extracted": len(merged["pdf_processing_result"].get("tables", {}).get("tables", [])) if merged["pdf_processing_result"].get("tables") else 0,
            "text_sections": sum(len(p.get("sections", [])) for p in merged["pdf_processing_result"]["text_content"]["pages"]),
            "numbers_found": 0,
            "overall_quality_score": 0.5,
            "processing_errors": []
        })
        return merged

    # -------- internals --------

    def _open_pdf(self, file_path: str) -> tuple[Any, int]:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            return doc, doc.page_count
        except Exception:
            # Fallback fake document with a single empty page
            class _FakeDoc(list):
                def __getitem__(self, idx):
                    class _Page:
                        def get_text(self_inner):
                            return ""
                    return _Page()
            fake = _FakeDoc([None])
            return fake, 1

    def _build_code_only_pages(self, fitz_doc: Any, page_count: int, grouped_pages: Set[int]) -> List[Dict[str, Any]]:
        pages: List[Dict[str, Any]] = []
        for i in range(page_count):
            if i in grouped_pages:
                continue
            page_obj = fitz_doc[i] if hasattr(fitz_doc, "__getitem__") else None
            text = page_obj.get_text() if (page_obj and hasattr(page_obj, "get_text")) else ""
            pages.append({
                "page_number": i + 1,
                "sections": [
                    {
                        "section_id": f"p{i+1}_s1",
                        "section_type": "paragraph",
                        "title": None,
                        "content": text,
                        "word_count": len(text.split()) if text else 0,
                        "llm_ready": True,
                        "position": {"start_y": 0, "end_y": 0, "bbox": [0, 0, 0, 0], "column_index": 0},
                        "metadata": {},
                        "structure": {"heading_level": None, "list_type": None, "list_level": None, "is_continuation": False},
                        "relationships": {"parent_section": None, "child_sections": [], "related_tables": [], "related_figures": []},
                        "numbers": []
                    }
                ]
            })
        return pages


