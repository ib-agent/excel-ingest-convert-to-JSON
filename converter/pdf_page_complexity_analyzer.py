"""
PDF Page Complexity Analyzer

Computes per-page numeric density and layout signals, classifies pages,
and groups consecutive numeric pages for AI routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class AnalyzerThresholds:
    min_numbers_per_page: int = 3
    min_number_density: float = 0.5  # numbers per 1000 chars
    min_table_likeness_score: float = 0.6
    max_pages_per_group: int = 5


class PDFPageComplexityAnalyzer:
    def __init__(self, thresholds: AnalyzerThresholds | None = None) -> None:
        self.thresholds = thresholds or AnalyzerThresholds()

    def analyze_pages(self, fitz_doc: Any) -> List[Dict[str, Any]]:
        """
        Analyze pages and return metrics with a category for each page.

        NOTE: This is a lightweight placeholder that expects the caller or
        tests to provide page text via fitz_doc[page_index].get_text().
        """
        page_metrics: List[Dict[str, Any]] = []
        num_pages = getattr(fitz_doc, "page_count", None) or len(getattr(fitz_doc, "pages", [])) or len(fitz_doc)

        for page_index in range(num_pages):
            # Minimal extraction to avoid hard dependency on PyMuPDF in tests
            try:
                page = fitz_doc[page_index] if hasattr(fitz_doc, "__getitem__") else fitz_doc.pages[page_index]
                page_text = ""
                if hasattr(page, "get_text"):
                    page_text = page.get_text() or ""
                elif isinstance(page, str):
                    page_text = page
            except Exception:
                page_text = ""

            number_count = self._count_numbers(page_text)
            char_count = max(len(page_text), 1)
            number_density = (number_count / char_count) * 1000.0

            # Placeholder layout signal (0..1). Real impl would inspect bbox/lines.
            layout_signals = {"table_likeness": 0.0}

            category = self._categorize(number_count, number_density, layout_signals)
            page_metrics.append({
                "page_index": page_index,
                "number_count": number_count,
                "number_density": number_density,
                "layout_signals": layout_signals,
                "text_ratio": (char_count / max(number_count, 1)),
                "category": category,
            })

        return page_metrics

    def group_numeric_pages(self, page_metrics: List[Dict[str, Any]]) -> List[Tuple[int, int]]:
        """
        Group consecutive pages where category is numeric_text or probable_table.
        Each group length is capped by thresholds.max_pages_per_group.
        Returns inclusive (start_page, end_page) indices (0-based).
        """
        groups: List[Tuple[int, int]] = []
        buffer: List[int] = []

        def flush_buffer() -> None:
            if not buffer:
                return
            start = buffer[0]
            for i in range(0, len(buffer), self.thresholds.max_pages_per_group):
                chunk = buffer[i:i + self.thresholds.max_pages_per_group]
                groups.append((chunk[0], chunk[-1]))
            buffer.clear()

        for metric in page_metrics:
            category = metric.get("category")
            if category in {"numeric_text", "probable_table"}:
                # continue current run
                if buffer and metric["page_index"] != buffer[-1] + 1:
                    # non-consecutive page breaks the run
                    flush_buffer()
                buffer.append(metric["page_index"])
            else:
                # end of a run
                flush_buffer()

        # flush remaining
        flush_buffer()

        return groups

    # --------- internals ---------

    def _count_numbers(self, text: str) -> int:
        import re
        patterns = [
            r"\b\d{1,3}(?:,\d{3})*\b",        # integers with commas
            r"\b\d+\.\d+\b",                 # decimals
            r"\b\d+(?:\.\d+)?%\b",          # percentages
            r"\$\s*\d+(?:,\d{3})*(?:\.\d{2})?",  # currency
            r"\b\d+(?:\.\d+)?[eE][+-]?\d+\b",    # scientific
        ]
        count = 0
        for p in patterns:
            count += len(re.findall(p, text))
        return count

    def _categorize(self, number_count: int, number_density: float, layout_signals: Dict[str, float]) -> str:
        if number_count < self.thresholds.min_numbers_per_page and number_density < self.thresholds.min_number_density:
            return "none_or_low_numbers"
        if layout_signals.get("table_likeness", 0.0) >= self.thresholds.min_table_likeness_score:
            return "probable_table"
        return "numeric_text"


