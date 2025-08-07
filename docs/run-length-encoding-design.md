# Run-Length Encoding for Compact Excel Representation

## Problem Statement

Excel files with very wide rows containing repeated values (e.g., thousands of columns with the same value) create massive JSON output that can:
- Exceed memory limits during processing
- Be impossible to open in many systems
- Create unnecessarily large file outputs
- Impact performance severely

## Current Compact Format

The current compact row representation stores each cell individually:

```json
{
  "r": 1,
  "cells": [
    [1, "value"],     // [column, value, style?, formula?]
    [2, "value"],
    [3, "value"],
    // ... potentially thousands more
  ]
}
```

## Proposed Enhanced Format with Run-Length Encoding

### 1. Enhanced Cell Format

Extend the current cell array format to support run-length encoding:

```json
{
  "r": 1,
  "cells": [
    [1, "different_value"],           // Normal cell: [col, value]
    [2, "repeated_value", null, null, 998],  // RLE cell: [start_col, value, style, formula, run_length]
    [1000, "another_value"]           // Normal cell continues after RLE
  ]
}
```

### 2. RLE Detection Rules

Apply run-length encoding when:
- **Consecutive cells** have identical values
- **Run length ≥ 3** (minimum threshold for compression benefit)
- **Values are primitive types** (strings, numbers, booleans, null)

### 3. Enhanced Cell Array Structure

```
Normal Cell:    [column, value, style?, formula?]
RLE Cell:       [start_column, value, style?, formula?, run_length]
```

Where:
- `start_column`: First column in the run
- `value`: The repeated value
- `style`: Style reference (if all cells in run share same style)
- `formula`: Formula (if all cells in run have same formula)
- `run_length`: Number of consecutive columns with this value

### 4. Implementation Strategy

#### Detection Phase
```python
def _detect_rle_opportunities(self, row_cells):
    """Detect consecutive cells with identical values for RLE compression"""
    if len(row_cells) < 3:
        return row_cells  # No benefit for short rows
    
    compressed_cells = []
    current_run = []
    
    for cell in sorted(row_cells, key=lambda x: x[0]):  # Sort by column
        if self._can_extend_run(current_run, cell):
            current_run.append(cell)
        else:
            # Process completed run
            if len(current_run) >= 3:
                compressed_cells.append(self._create_rle_cell(current_run))
            else:
                compressed_cells.extend(current_run)  # Keep as individual cells
            current_run = [cell]
    
    # Handle final run
    if len(current_run) >= 3:
        compressed_cells.append(self._create_rle_cell(current_run))
    else:
        compressed_cells.extend(current_run)
    
    return compressed_cells
```

#### RLE Cell Creation
```python
def _create_rle_cell(self, run_cells):
    """Create a run-length encoded cell from a sequence of identical cells"""
    first_cell = run_cells[0]
    last_cell = run_cells[-1]
    
    # Verify all cells have identical values and compatible styles
    base_value = first_cell[1]
    base_style = first_cell[2] if len(first_cell) > 2 else None
    base_formula = first_cell[3] if len(first_cell) > 3 else None
    
    # Validation: ensure all cells in run are truly identical
    for cell in run_cells[1:]:
        if (cell[1] != base_value or 
            (len(cell) > 2 and cell[2] != base_style) or
            (len(cell) > 3 and cell[3] != base_formula)):
            raise ValueError("Cannot create RLE for non-identical cells")
    
    start_col = first_cell[0]
    run_length = len(run_cells)
    
    # Create RLE cell: [start_col, value, style, formula, run_length]
    rle_cell = [start_col, base_value]
    
    if base_style is not None:
        rle_cell.append(base_style)
    elif base_formula is not None:
        rle_cell.append(None)  # Style placeholder
    
    if base_formula is not None:
        while len(rle_cell) < 4:
            rle_cell.append(None)
        rle_cell[3] = base_formula
    
    # Add run length as final element
    rle_cell.append(run_length)
    
    return rle_cell
```

### 5. Decompression Strategy

For systems that need to expand the RLE format back to individual cells:

```python
def _expand_rle_cells(self, row_data):
    """Expand RLE cells back to individual cells"""
    expanded_cells = []
    
    for cell in row_data.get("cells", []):
        if len(cell) >= 5 and isinstance(cell[-1], int):  # Has run_length
            start_col, value, style, formula, run_length = cell[0], cell[1], cell[2], cell[3], cell[-1]
            
            # Expand the run
            for i in range(run_length):
                expanded_cell = [start_col + i, value]
                if style is not None:
                    expanded_cell.append(style)
                if formula is not None:
                    while len(expanded_cell) < 4:
                        expanded_cell.append(None)
                    expanded_cell[3] = formula
                expanded_cells.append(expanded_cell)
        else:
            expanded_cells.append(cell)  # Normal cell
    
    return {"r": row_data["r"], "cells": expanded_cells}
```

### 6. Compression Benefits

Example compression for a row with 1000 repeated cells:

**Before RLE:**
```json
{
  "r": 1,
  "cells": [
    [1, "0"], [2, "0"], [3, "0"], ..., [1000, "0"]
  ]
}
```
Size: ~15KB for 1000 cells

**After RLE:**
```json
{
  "r": 1, 
  "cells": [
    [1, "0", null, null, 1000]
  ]
}
```
Size: ~50 bytes for same data

**Compression Ratio: 99.7% reduction**

### 7. Backward Compatibility

- Files without repeated values remain unchanged
- Existing parsers can detect RLE cells by checking for 5+ elements
- Graceful fallback: treat RLE cells as regular cells (ignoring run_length)

### 8. Configuration Options

```python
class CompactExcelProcessor:
    def __init__(self, 
                 enable_rle: bool = True,
                 rle_min_run_length: int = 3,
                 rle_max_row_width: int = 1000):
        self.enable_rle = enable_rle
        self.rle_min_run_length = rle_min_run_length  
        self.rle_max_row_width = rle_max_row_width  # Only apply RLE to wide rows
```

### 9. Use Cases

This enhancement particularly benefits:
- **Financial models** with repeated formulas across many columns
- **Template files** with default values across wide ranges
- **Configuration spreadsheets** with repeated settings
- **Generated reports** with repeated data patterns

### 10. Implementation Priority

1. **Phase 1**: Implement RLE detection and compression in `CompactExcelProcessor`
2. **Phase 2**: Add decompression utilities for backward compatibility  
3. **Phase 3**: Optimize for performance with large datasets
4. **Phase 4**: Add configuration options and fine-tuning
