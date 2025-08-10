"""
PyMuPDF-based Table Detector (Heuristic)

Detects table-like structures using word positions from PyMuPDF. This is a
lightweight fallback when AI is unavailable. It clusters words into lines and
columns and emits simple table regions with minimal schema-compatible fields.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


class PyMuPDFTableDetector:
    def __init__(self,
                 min_rows: int = 3,
                 min_cols: int = 2,
                 x_tolerance: float = 6.0,
                 y_tolerance: float = 3.0) -> None:
        self.min_rows = min_rows
        self.min_cols = min_cols
        self.x_tolerance = x_tolerance
        self.y_tolerance = y_tolerance

    def detect_tables_on_page(self, page: Any, page_number: int) -> List[Dict[str, Any]]:
        """
        Returns a list of tables. Each is a dict with keys: table_id, name, region,
        header_info (optional), columns, rows, metadata.
        """
        try:
            words = page.get_text("words")  # list of (x0, y0, x1, y1, word, block, line, word_no)
        except Exception:
            return []

        if not words:
            return []

        # Group words by line index; then sort by x
        # Build structure: {line_id: [(x0, y0, x1, y1, word)]}
        lines: Dict[int, List[Tuple[float, float, float, float, str]]] = {}
        for (x0, y0, x1, y1, w, block, line, word_no) in words:
            lines.setdefault(int(line), []).append((x0, y0, x1, y1, w))
        for line_id in lines:
            lines[line_id].sort(key=lambda t: t[0])

        # Build candidate row structures with merged words into "cells" via x gaps
        row_structs: List[Dict[str, Any]] = []
        for line_id in sorted(lines.keys()):
            items = lines[line_id]
            if not items:
                continue
            cells: List[Dict[str, Any]] = []
            cur = [items[0]]
            for item in items[1:]:
                prev = cur[-1]
                # If the gap between current word's x0 and previous word's x1 is small, same cell
                if item[0] - prev[2] <= self.x_tolerance:
                    cur.append(item)
                else:
                    cells.append(self._merge_cell(cur))
                    cur = [item]
            cells.append(self._merge_cell(cur))
            row_bbox = self._bbox_union([ (c["x0"], c["y0"], c["x1"], c["y1"]) for c in cells ])
            row_structs.append({"line_id": line_id, "cells": cells, "bbox": row_bbox})

        # Estimate column x positions by clustering cell x0 across rows
        x_positions: List[float] = []
        for row in row_structs:
            for cell in row["cells"]:
                x_positions.append(cell["x0"])
        if not x_positions:
            return []
        x_positions.sort()
        column_edges = self._cluster_positions(x_positions, self.x_tolerance * 2)
        num_cols = len(column_edges)

        # Assign each cell to nearest column by x0
        table_rows: List[List[str]] = []
        table_bboxes: List[Tuple[float, float, float, float]] = []
        for row in row_structs:
            row_values = ["" for _ in range(num_cols)]
            for cell in row["cells"]:
                col_idx = self._nearest_index(column_edges, cell["x0"])
                # Concatenate if collision
                row_values[col_idx] = (row_values[col_idx] + " " + cell["text"]).strip()
            if any(v for v in row_values):
                table_rows.append(row_values)
                table_bboxes.append(row["bbox"])

        # Heuristic filter: need enough rows/cols and at least one row with multiple populated cells
        if len(table_rows) < self.min_rows or num_cols < self.min_cols:
            return []
        multi_cell_rows = sum(1 for r in table_rows if sum(1 for v in r if v) >= self.min_cols)
        if multi_cell_rows < max(2, self.min_rows - 1):
            return []

        # Build minimal schema
        page_bbox = self._bbox_union(table_bboxes)
        columns = [
            {
                "column_index": idx + 1,
                "column_letter": "",
                "column_label": table_rows[0][idx] or f"Column {idx+1}",
                "is_header_column": False,
                "cells": {}
            }
            for idx in range(num_cols)
        ]

        # Build rows (first row as header if likely)
        rows = []
        header_row_idx = 1
        for ridx, rvals in enumerate(table_rows, start=1):
            is_header = ridx == header_row_idx
            rows.append({
                "row_index": ridx,
                "row_label": rvals[0] if rvals and rvals[0] else f"Row {ridx}",
                "is_header_row": is_header,
                "cells": {}
            })

        table = {
            "table_id": f"p{page_number}_t1",
            "name": f"Page {page_number} Table 1",
            "region": {
                "page_number": page_number,
                "bbox": [page_bbox[0], page_bbox[1], page_bbox[2], page_bbox[3]],
                "detection_method": "pymupdf_grid"
            },
            "header_info": {
                "header_rows": [header_row_idx],
                "header_columns": [],
                "data_start_row": header_row_idx + 1,
                "data_start_col": 1
            },
            "columns": columns,
            "rows": rows,
            "metadata": {
                "detection_method": "pymupdf_grid",
                "cell_count": len(table_rows) * max(1, num_cols),
                "has_merged_cells": False,
                "confidence": 0.6
            }
        }
        return [table]

    # ---------- internals ----------

    def _merge_cell(self, items: List[Tuple[float, float, float, float, str]]) -> Dict[str, Any]:
        x0 = min(i[0] for i in items)
        y0 = min(i[1] for i in items)
        x1 = max(i[2] for i in items)
        y1 = max(i[3] for i in items)
        text = " ".join(i[4] for i in items)
        return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "text": text}

    def _bbox_union(self, bboxes: List[Tuple[float, float, float, float]]) -> Tuple[float, float, float, float]:
        x0 = min(b[0] for b in bboxes)
        y0 = min(b[1] for b in bboxes)
        x1 = max(b[2] for b in bboxes)
        y1 = max(b[3] for b in bboxes)
        return (x0, y0, x1, y1)

    def _cluster_positions(self, xs: List[float], tol: float) -> List[float]:
        if not xs:
            return []
        clusters: List[List[float]] = [[xs[0]]]
        for x in xs[1:]:
            if abs(x - clusters[-1][-1]) <= tol:
                clusters[-1].append(x)
            else:
                clusters.append([x])
        # Representative position is median of each cluster
        reps: List[float] = []
        for c in clusters:
            c_sorted = sorted(c)
            m = c_sorted[len(c_sorted)//2]
            reps.append(m)
        return reps

    def _nearest_index(self, arr: List[float], x: float) -> int:
        if not arr:
            return 0
        best_idx = 0
        best_dist = float('inf')
        for i, v in enumerate(arr):
            d = abs(v - x)
            if d < best_dist:
                best_dist = d
                best_idx = i
        return best_idx


