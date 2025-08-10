from __future__ import annotations

import types
from typing import Any, Dict, List

from converter.pdf_page_complexity_analyzer import PDFPageComplexityAnalyzer, AnalyzerThresholds
from converter.pdf_ai_router import PDFAIFailoverRouter, AIFailoverConfig
from converter.pdf_result_reconstructor import PDFResultReconstructor
from converter.pdf_ai_failover_pipeline import PDFAIFailoverPipeline


class FakePage:
    def __init__(self, text: str = "", words: List[tuple] | None = None):
        self._text = text
        self._words = words or []

    def get_text(self, mode: str = "text"):
        if mode == "words":
            return self._words
        return self._text


class FakeDoc:
    def __init__(self, pages: List[FakePage]):
        self.pages = pages

    def __len__(self):
        return len(self.pages)

    def __getitem__(self, idx: int):
        return self.pages[idx]

    @property
    def page_count(self) -> int:
        return len(self.pages)


def test_grouping_respects_nonconsecutive_and_max_group_size():
    # pages: 0..5, numeric at 0,1,2, 4,5 with a gap at 3
    texts = [
        "$100 and 5% on p1",  # 0
        "Sales 200 and 300",   # 1
        "Q3: 1.23e4",         # 2
        "No numbers here",     # 3
        "$50",                 # 4
        "10% growth"           # 5
    ]
    doc = FakeDoc([FakePage(t) for t in texts])
    analyzer = PDFPageComplexityAnalyzer(AnalyzerThresholds(min_numbers_per_page=1, min_number_density=0.1, max_pages_per_group=2))
    metrics = analyzer.analyze_pages(doc)
    groups = analyzer.group_numeric_pages(metrics)
    # First run 0..2 gets split due to max_pages_per_group=2 -> (0,1),(2,2); then gap; then (4,5)
    assert groups == [(0, 1), (2, 2), (4, 5)]


def test_router_uses_ai_client_when_available_and_falls_back_otherwise():
    pages = ["Revenue $1,000 up 25%", "No nums"]
    doc = FakeDoc([FakePage(p) for p in pages])

    # AI available
    class MockAI:
        def is_available(self):
            return True

        def extract_pages(self, payload: List[Dict[str, Any]]):
            return {"tables": [{"table_id": "p1_t1"}], "text_content": {"pages": [{"page_number": 1, "sections": []}]}}

    router = PDFAIFailoverRouter(MockAI())
    results = router.process_groups(doc, [(0, 0)])
    assert results and results[0].get("tables")

    # AI unavailable -> fallback local numbers
    class MockAINone:
        def is_available(self):
            return False

    router2 = PDFAIFailoverRouter(MockAINone())
    results2 = router2.process_groups(doc, [(0, 0)])
    pages_out = results2[0]["text_content"]["pages"]
    assert pages_out and pages_out[0]["sections"][0]["numbers"]


def test_router_fallback_extracts_various_number_formats():
    txt = "Revenue $1,500.00 increased 25.5% to 1.23e6 units from 1,200 previously."
    doc = FakeDoc([FakePage(txt)])
    router = PDFAIFailoverRouter(types.SimpleNamespace(is_available=lambda: False))
    out = router.process_groups(doc, [(0, 0)])
    nums = out[0]["text_content"]["pages"][0]["sections"][0]["numbers"]
    fmts = {n["format"] for n in nums}
    assert {"currency", "percentage", "scientific_notation", "integer"}.issubset(fmts) or {"decimal"}.intersection(fmts)


def test_reconstructor_merges_ai_and_native_tables_and_ordering():
    recon = PDFResultReconstructor()
    ai_results = [{
        "text_content": {"pages": [
            {"page_number": 2, "sections": [{"section_id": "p2_s1"}]}
        ]},
        "tables": [{"table_id": "p2_t1"}]
    }]
    code_only_pages = [
        {"page_number": 1, "sections": [{"section_id": "p1_s1"}]},
        {"page_number": 3, "sections": [{"section_id": "p3_s1"}]}
    ]
    native_tables = [{"table_id": "p3_t1"}]
    merged = recon.merge(ai_results, code_only_pages, optional_native_tables=native_tables)
    pages = [p["page_number"] for p in merged["pdf_processing_result"]["text_content"]["pages"]]
    assert pages == [1, 2, 3]
    tables = merged["pdf_processing_result"]["tables"]["tables"]
    assert {t["table_id"] for t in tables} == {"p2_t1", "p3_t1"}


def test_pipeline_uses_pymupdf_fallback_on_numeric_pages_when_ai_tables_absent(monkeypatch):
    # Construct words forming two rows and two columns
    # words tuples: (x0, y0, x1, y1, word, block, line, word_no)
    words = [
        (10, 10, 20, 15, "H1", 0, 0, 0), (30, 10, 40, 15, "H2", 0, 0, 1),
        (10, 20, 20, 25, "A", 0, 1, 0), (30, 20, 40, 25, "B", 0, 1, 1),
    ]
    pages = [
        FakePage("Revenue 100", words=words),  # numeric and table-like
        FakePage("Narrative only"),
    ]
    fake_doc = FakeDoc(pages)

    # Monkeypatch pipeline _open_pdf to return our fake doc
    pipe = PDFAIFailoverPipeline()
    monkeypatch.setattr(pipe, "_open_pdf", lambda fp: (fake_doc, len(fake_doc)))

    # Monkeypatch router to return no tables
    def no_tables_process_groups(fitz_doc, groups):
        return [{"tables": [], "text_content": {"pages": []}, "processing_summary": {}}]

    monkeypatch.setattr(pipe.router, "process_groups", no_tables_process_groups)

    result = pipe.process("dummy.pdf")
    tables = result["pdf_processing_result"].get("tables", {}).get("tables", [])
    assert tables and tables[0].get("region", {}).get("page_number") == 1


def test_pipeline_includes_grouped_pages_as_code_only_when_ai_disabled(monkeypatch):
    # Numeric pages but AI disabled: ensure text_content still includes those pages
    pages = [FakePage("$100"), FakePage("No numbers"), FakePage("25% growth")]
    fake_doc = FakeDoc(pages)
    pipe = PDFAIFailoverPipeline()
    monkeypatch.setattr(pipe, "_open_pdf", lambda fp: (fake_doc, len(fake_doc)))

    # Simulate router disabled returning empty list
    monkeypatch.setattr(pipe.router, "process_groups", lambda d, g: [])

    result = pipe.process("dummy.pdf")
    out_pages = result["pdf_processing_result"]["text_content"]["pages"]
    # Expect all pages present in order 1..3
    assert [p["page_number"] for p in out_pages] == [1, 2, 3]


