import os
import json
import pytest

from converter.excel_complexity_analyzer import ExcelComplexityAnalyzer
from converter.anthropic_excel_client import AnthropicExcelClient
from converter.ai_result_parser import AIResultParser
from converter.complexity_preserving_compact_processor import (
    ComplexityPreservingCompactProcessor,
)


TEST_FILES = [
    "ai_failover_multi_level_headers.xlsx",
    "ai_failover_complex_merges.xlsx",
    "ai_failover_sparse_clusters.xlsx",
    "ai_failover_irregular_boundaries.xlsx",
    "ai_failover_dynamic_formulas.xlsx",
    "ai_failover_nonstandard_layout.xlsx",
]


def load_with_metadata(path: str):
    processor = ComplexityPreservingCompactProcessor(enable_rle=True)
    data = processor.process_file(
        path, filter_empty_trailing=True, include_complexity_metadata=True
    )
    # return first sheet and its metadata (we generate single-sheet books)
    sheet = data["workbook"]["sheets"][0]
    meta = data.get("complexity_metadata", {}).get("sheets", {}).get(
        sheet.get("name", "Unknown"),
        {},
    )
    return sheet, meta


def assert_schema_compat(standardized_ai: dict):
    """Minimal schema conformance check aligned with docs/table-oriented-json-schema.md.

    We check that converted tables can be mapped to the verbose table schema fields.
    """
    # Expect standardized form has converted tables
    converted = standardized_ai.get("converted_tables", [])
    assert isinstance(converted, list)

    for t in converted:
        # region mapping
        assert "start_row" in t and "end_row" in t and "start_col" in t and "end_col" in t
        # header info
        assert "header_rows" in t
        # meta
        assert t.get("detection_method") == "ai_analysis"


@pytest.mark.parametrize("filename", TEST_FILES)
def test_ai_failover_and_schema(tmp_path, filename, monkeypatch):
    # Arrange: create test files if not present
    import importlib.util, pathlib
    generator_path = pathlib.Path(__file__).resolve().parent.parent / 'create_ai_failover_excels.py'
    spec = importlib.util.spec_from_file_location('create_ai_failover_excels', str(generator_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    mod.main()

    test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "excel")
    file_path = os.path.join(test_dir, filename)
    assert os.path.exists(file_path), f"Missing generated file: {file_path}"

    sheet, meta = load_with_metadata(file_path)

    analyzer = ExcelComplexityAnalyzer()
    analysis = analyzer.analyze_sheet_complexity(sheet, complexity_metadata=meta)

    # Assert routing recommends AI involvement for these complex cases
    assert analysis["recommendation"] in {"dual", "ai_first"}

    # Prepare a fake AI client when real AI is unavailable
    client = AnthropicExcelClient()
    parser = AIResultParser()

    if not client.is_available():
        # Mock a plausible AI response consistent with parser expectations
        fake = {
            "status": "success",
            "result": {
                "tables_detected": [
                    {
                        "table_id": "table_1",
                        "name": "AI Detected Table",
                        "boundaries": {"start_row": 1, "end_row": 10, "start_col": 1, "end_col": 6},
                        "headers": {
                            "row_headers": [{"row": 1, "columns": [{"col": 1, "value": "H1"}], "level": 1}],
                            "column_headers": []
                        },
                        "data_area": {"start_row": 2, "end_row": 10, "start_col": 2, "end_col": 6},
                        "table_type": "other",
                        "confidence": 0.81,
                        "complexity_indicators": ["multi_level_headers"] ,
                        "data_quality": {"completeness": 0.9, "consistency": 0.85, "data_types": ["text","number"]}
                    }
                ],
                "sheet_analysis": {
                    "total_tables": 1,
                    "data_density": 0.5,
                    "structure_complexity": "complex",
                    "recommended_processing": "ai_primary"
                },
                "analysis_confidence": 0.8
            },
            "ai_metadata": {"model": "mock", "total_tokens": 0}
        }
        standardized = parser.parse_excel_analysis(fake)
    else:
        # If available, run the real call
        raw = client.analyze_excel_sheet(sheet, complexity_metadata=analysis, analysis_focus="comprehensive")
        standardized = parser.parse_excel_analysis(raw)

    # Then: ensure we got at least one table and schema compatibility
    assert standardized.get("table_count", 0) >= 1
    assert_schema_compat(standardized)


