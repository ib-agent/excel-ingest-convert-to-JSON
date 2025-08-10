"""
PDF AI Failover Router

Prepares page groups for AI extraction and calls provider client to obtain
tables and text sections with embedded numbers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class AIFailoverConfig:
    enabled: bool = True
    use_vision_if_available: bool = True
    max_pages_per_group: int = 5
    max_concurrent_groups: int = 3


class PDFAIFailoverRouter:
    def __init__(self, ai_client: Any, config: AIFailoverConfig | None = None) -> None:
        self.ai_client = ai_client
        self.config = config or AIFailoverConfig()

    def process_groups(self, fitz_doc: Any, page_groups: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """
        For each group, prepare images or structured text and call AI.
        Returns a list of results with keys: tables, text_content, processing_summary.
        This is a scaffold; real implementation will encode images and craft prompts.
        """
        if not self.config.enabled:
            return []

        results: List[Dict[str, Any]] = []
        for (start_page, end_page) in page_groups:
            group_pages = list(range(start_page, end_page + 1))
            # Placeholder extraction: capture plain text per page
            pages_payload: List[Dict[str, Any]] = []
            for p in group_pages:
                page_obj = fitz_doc[p] if hasattr(fitz_doc, "__getitem__") else fitz_doc.pages[p]
                page_text = page_obj.get_text() if hasattr(page_obj, "get_text") else (page_obj if isinstance(page_obj, str) else "")
                pages_payload.append({
                    "page_number": p + 1,
                    "text": page_text,
                })

            # Call AI client if available; otherwise fallback to local extraction
            try:
                ai_available = getattr(self.ai_client, "is_available", lambda: False)()
            except Exception:
                ai_available = False

            if ai_available and hasattr(self.ai_client, "extract_pages"):
                ai_response = self.ai_client.extract_pages(pages_payload) or {}
                # Ensure minimal shape
                ai_response.setdefault("tables", [])
                tc = ai_response.setdefault("text_content", {})
                tc.setdefault("pages", [])
                ai_response.setdefault("processing_summary", {
                    "tables_extracted": len(ai_response.get("tables", [])),
                    "text_sections": sum(len(p.get("sections", [])) for p in tc.get("pages", [])),
                    "numbers_found": sum(len(s.get("numbers", [])) for p in tc.get("pages", []) for s in p.get("sections", [])),
                    "overall_quality_score": 0.6,
                    "processing_errors": []
                })
            else:
                ai_response = self._fallback_local_extraction(pages_payload)
            results.append(ai_response)

        return results

    def _fallback_local_extraction(self, pages_payload: List[Dict[str, Any]]) -> Dict[str, Any]:
        pages = []
        total_numbers = 0
        for p in pages_payload:
            text = p.get("text") or ""
            numbers = self._extract_numbers_from_text(text)
            total_numbers += len(numbers)
            pages.append({
                "page_number": p["page_number"],
                "sections": [
                    {
                        "section_id": f"p{p['page_number']}_s1",
                        "section_type": "paragraph",
                        "title": None,
                        "content": text[:2000],
                        "word_count": len(text.split()),
                        "llm_ready": True,
                        "position": {"start_y": 0, "end_y": 0, "bbox": [0, 0, 0, 0], "column_index": 0},
                        "metadata": {},
                        "structure": {"heading_level": None, "list_type": None, "list_level": None, "is_continuation": False},
                        "relationships": {"parent_section": None, "child_sections": [], "related_tables": [], "related_figures": []},
                        "numbers": numbers,
                    }
                ]
            })

        return {
            "tables": [],
            "text_content": {"pages": pages},
            "processing_summary": {
                "tables_extracted": 0,
                "text_sections": len(pages),
                "numbers_found": total_numbers,
                "overall_quality_score": 0.5,
                "processing_errors": []
            }
        }

    def _extract_numbers_from_text(self, text: str) -> List[Dict[str, Any]]:
        import re
        results: List[Dict[str, Any]] = []

        patterns = {
            "currency": re.compile(r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?"),
            "percentage": re.compile(r"\b\d+(?:\.\d+)?%\b"),
            "decimal": re.compile(r"\b\d+\.\d+\b"),
            "scientific_notation": re.compile(r"\b\d+(?:\.\d+)?[eE][+-]?\d+\b"),
            "integer": re.compile(r"\b\d{1,3}(?:,\d{3})*\b"),
        }

        def to_number(s: str) -> float:
            s_clean = s.replace("$", "").replace(",", "").replace("%", "")
            try:
                return float(s_clean)
            except Exception:
                return 0.0

        for fmt, rx in patterns.items():
            for m in rx.finditer(text):
                original = m.group(0)
                value = to_number(original)
                entry = {
                    "value": value,
                    "original_text": original,
                    "context": text[max(0, m.start()-50): m.end()+50],
                    "position": {"x": 0, "y": 0, "bbox": [0, 0, 0, 0], "line_number": 0},
                    "format": fmt,
                    "unit": None,
                    "currency": "USD" if fmt == "currency" else None,
                    "confidence": 0.75,
                    "extraction_method": "regex_pattern",
                    "metadata": {}
                }
                results.append(entry)
        return results


