from __future__ import annotations

import types
from converter.pdf_page_complexity_analyzer import PDFPageComplexityAnalyzer, AnalyzerThresholds
from converter.pdf_ai_router import PDFAIFailoverRouter, AIFailoverConfig
from converter.pdf_result_reconstructor import PDFResultReconstructor


class FakeDoc:
    def __init__(self, pages_text: list[str]):
        self._pages = pages_text

    def __len__(self):
        return len(self._pages)

    def __getitem__(self, idx: int):
        return types.SimpleNamespace(get_text=lambda: self._pages[idx])


def test_complexity_analyzer_groups_numeric_pages():
    pages = [
        "Intro with no numbers.",
        "Revenue was $1,200 and growth 15%.",
        "Expenses 300 and EBITDA 100.",
        "Narrative only.",
        "Table-like values 1, 2, 3 and 4%.",
    ]
    doc = FakeDoc(pages)
    analyzer = PDFPageComplexityAnalyzer(AnalyzerThresholds(min_numbers_per_page=1, min_number_density=0.1))
    metrics = analyzer.analyze_pages(doc)
    groups = analyzer.group_numeric_pages(metrics)
    # Expect group for pages 1-2 and a separate group for page 4
    assert groups == [(1, 2), (4, 4)]


def test_ai_router_returns_structure_without_provider():
    pages = ["$1,000 on page 1", "No numbers here"]
    doc = FakeDoc(pages)
    router = PDFAIFailoverRouter(ai_client=types.SimpleNamespace(is_available=lambda: True))
    groups = [(0, 0)]
    results = router.process_groups(doc, groups)
    assert isinstance(results, list)
    assert results and isinstance(results[0], dict)
    assert "text_content" in results[0]


def test_result_reconstructor_merges_ai_and_code_only():
    recon = PDFResultReconstructor()
    ai_results = [{
        "text_content": {"pages": [{"page_number": 2, "sections": [{"section_id": "p2_s1"}]}]},
        "tables": []
    }]
    code_only_pages = [{"page_number": 1, "sections": [{"section_id": "p1_s1"}]}]
    merged = recon.merge(ai_results, code_only_pages, optional_native_tables=None)
    pages = merged["pdf_processing_result"]["text_content"]["pages"]
    assert [p["page_number"] for p in pages] == [1, 2]


