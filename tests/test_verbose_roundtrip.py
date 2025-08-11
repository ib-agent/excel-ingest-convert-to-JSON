import os
import unittest
import tempfile

from typing import Any, Dict

from converter.excel_processor import ExcelProcessor
from converter.excel_verbose_reconstructor import write_verbose_json_to_excel


TEST_FILES = [
    
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "test_excel",
            "Test_SpreadSheet_100_numbers.xlsx",
        )
    ),
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "test_excel",
            "Test_Spreadsheet_multiple_tables_one_sheet_40_numbers_with_Table_titles.xlsx",
        )
    ),
]


def _normalize_verbose_json(data: Dict[str, Any]) -> Dict[str, Any]:
    wb = data.get("workbook", {})
    sheets = wb.get("sheets", [])

    norm_sheets = []
    for sheet in sheets:
        cells = sheet.get("cells", {}) or {}
        norm_cells = {}
        for coord, c in cells.items():
            f = c.get("formula")
            v = None if f else c.get("value")
            # number_format is often critical for fidelity
            n = (c.get("style") or {}).get("number_format")
            # Basic subset of style for deterministic compare
            s = c.get("style") or {}
            font = s.get("font") or {}
            fill = s.get("fill") or {}
            border = s.get("border") or {}
            alignment = s.get("alignment") or {}

            norm_style = {
                "font": {
                    k: font.get(k)
                    for k in [
                        "name",
                        "size",
                        "bold",
                        "italic",
                        "underline",
                        "strike",
                    ]
                    if font.get(k) is not None
                }
            }
            # Fill: only use fill_type and start_color.rgb if present
            fill_type = fill.get("fill_type") or fill.get("type")
            start_rgb = (fill.get("start_color") or {}).get("rgb")
            if fill_type or start_rgb:
                norm_style["fill"] = {"fill_type": fill_type, "rgb": start_rgb}

            # Border: include only sides with a meaningful style
            def side_style(d):
                if isinstance(d, dict):
                    return d.get("style")
                return d
            meaningful_sides = {}
            for k in ["left", "right", "top", "bottom"]:
                if k in border:
                    st = side_style(border.get(k))
                    if st:
                        meaningful_sides[k] = st
            if meaningful_sides:
                norm_style["border"] = meaningful_sides

            # Alignment: keep only explicit and meaningful flags
            a = {}
            if alignment.get("horizontal"):
                a["horizontal"] = alignment.get("horizontal")
            if alignment.get("vertical"):
                a["vertical"] = alignment.get("vertical")
            if alignment.get("wrap_text"):
                a["wrap_text"] = True
            if a:
                norm_style["alignment"] = a

            if n and n != "General":
                norm_style["number_format"] = n

            # Only keep style if anything present
            if not any(norm_style.get(k) for k in ["font", "fill", "border", "alignment", "number_format"]):
                norm_style = {}

            norm_cells[coord] = {"v": v, "f": f, "s": norm_style}

        # Frozen panes subset
        fp = sheet.get("frozen_panes") or {}
        frozen = {
            "rows": fp.get("frozen_rows", 0),
            "cols": fp.get("frozen_cols", 0),
            "tl": fp.get("top_left_cell"),
        }

        # Merged ranges normalized as sorted list of strings
        merged = []
        for m in (sheet.get("merged_cells") or []):
            r = m.get("range")
            if r:
                merged.append(r)
        merged.sort()

        norm_sheets.append(
            {
                "name": sheet.get("name"),
                "frozen": frozen,
                "cells": norm_cells,
                "merged": merged,
            }
        )

    # Sort sheets by name to avoid order-related differences in certain files
    norm_sheets.sort(key=lambda s: s.get("name") or "")

    return {"sheets": norm_sheets}


class TestVerboseRoundTrip(unittest.TestCase):
    def setUp(self) -> None:
        self.processor = ExcelProcessor()

    def test_round_trip_verbose_schema(self):
        for xlsx_path in TEST_FILES:
            with self.subTest(file=os.path.basename(xlsx_path)):
                self.assertTrue(os.path.exists(xlsx_path), f"Missing test file: {xlsx_path}")

                # Initial extraction
                first = self.processor.process_file(xlsx_path)

                # Reconstruct to a temp Excel and re-extract
                with tempfile.TemporaryDirectory() as tmpdir:
                    out_path = os.path.join(tmpdir, "reconstructed.xlsx")
                    write_verbose_json_to_excel(first, out_path)
                    second = self.processor.process_file(out_path)

                # Normalize and compare
                n1 = _normalize_verbose_json(first)
                n2 = _normalize_verbose_json(second)
                self.assertEqual(n1, n2)


if __name__ == "__main__":
    unittest.main()


