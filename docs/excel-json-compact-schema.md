# Compact Excel JSON Schema

This document defines a highly compressed JSON schema for Excel spreadsheets that reduces file size by 60-80% compared to the verbose schema while maintaining all essential information.

## Overview

The compact schema uses these compression strategies:
1. **Row-based cell organization** with shared formatting
2. **Style dictionary** with references instead of inline styles
3. **Array-based coordinates** instead of verbose coordinate objects
4. **Optional property elimination** - only non-default values included
5. **Reference-based tables** to eliminate data duplication

## Root Structure

```json
{
  "workbook": {
    "meta": {
      "filename": "string",
      "creator": "string", 
      "created": "ISO_datetime",
      "modified": "ISO_datetime"
    },
    "styles": {},      // Centralized style dictionary
    "sheets": []       // Array of sheet objects
  }
}
```

## Style Dictionary

Centralized styles referenced by ID to eliminate duplication:

```json
{
  "styles": {
    "default": {
      "font": {"name": "Calibri", "size": 11}
    },
    "header": {
      "font": {"bold": true, "size": 12},
      "fill": {"type": "solid", "color": "CCCCCC"},
      "alignment": {"horizontal": "center"}
    },
    "currency": {
      "number_format": "$#,##0.00"
    },
    "bold": {
      "font": {"bold": true}
    }
  }
}
```

## Compact Sheet Structure

```json
{
  "name": "Sheet1",
  "frozen": [1, 1],          // [rows, cols] - only if frozen
  "dimensions": [1, 1, 100, 20], // [min_row, min_col, max_row, max_col]
  "merged": [                // Only if merged cells exist
    [2, 3, 2, 5]            // [start_row, start_col, end_row, end_col]
  ],
  "rows": [                  // Row-based organization
    {
      "r": 1,               // Row number
      "style": "header",     // Shared style for entire row (optional)
      "cells": [
        [1, "Product"],                    // [col, value]
        [2, "Price", "currency"],          // [col, value, style_ref]
        [3, "Qty", null, "=B1*C1"]        // [col, value, style_ref, formula]
      ]
    },
    {
      "r": 2,
      "cells": [
        [1, "Widget A"],
        [2, 29.99, "currency"],
        [3, 100]
      ]
    }
  ],
  "tables": [               // Optional - only if table structure detected
    {
      "id": "t1",
      "region": [1, 1, 10, 3],           // [start_row, start_col, end_row, end_col]
      "headers": {"rows": [1], "cols": [1]},
      "col_labels": ["Product", "Price", "Quantity"]
    }
  ]
}
```

## Cell Value Types

Inferred from value, explicit type only when needed:
- Numbers: `42`, `3.14`
- Strings: `"text"`
- Booleans: `true`, `false`
- Dates: `"2024-01-15"` (ISO format)
- Formulas: Include formula string as 4th array element
- Empty cells: Omitted from arrays entirely

## Array-Based Cell Format

Each cell in the `cells` array uses compact format:
```
[column_index, value, style_ref?, formula?]
```

Examples:
```json
[1, "Product Name"],              // Column 1, string value
[2, 42.5],                       // Column 2, number value  
[3, "Special", "bold"],          // Column 3, string with style reference
[4, 100, "currency", "=B2*C2"]  // Column 4, number with style and formula
```

## Benefits vs. Verbose Schema

| Aspect | Verbose Schema | Compact Schema | Savings |
|--------|---------------|----------------|---------|
| **Cell Coordinates** | Full object with coordinate, row, column, column_letter | Array index | ~70% |
| **Style Information** | Inline style objects | Style references | ~60% |
| **Optional Properties** | All properties included | Only non-defaults | ~40% |
| **Table Structure** | Duplicated cell data | References only | ~80% |
| **Metadata** | Extensive properties | Essential only | ~50% |

## Example: Before vs After

### BEFORE (Verbose - 580 bytes):
```json
{
  "cells": {
    "A1": {
      "coordinate": "A1", "row": 1, "column": 1, "column_letter": "A",
      "value": "Product", "data_type": "string", "formula": null,
      "style": {"font": {"bold": true, "size": 12}, "fill": {"fill_type": "solid", "start_color": {"rgb": "CCCCCC"}}}
    },
    "B1": {
      "coordinate": "B1", "row": 1, "column": 2, "column_letter": "B", 
      "value": "Price", "data_type": "string", "formula": null,
      "style": {"font": {"bold": true, "size": 12}, "fill": {"fill_type": "solid", "start_color": {"rgb": "CCCCCC"}}}
    }
  }
}
```

### AFTER (Compact - 140 bytes):
```json
{
  "styles": {"h": {"font": {"bold": true, "size": 12}, "fill": {"type": "solid", "color": "CCCCCC"}}},
  "rows": [{"r": 1, "style": "h", "cells": [[1, "Product"], [2, "Price"]]}]
}
```

**Size Reduction: 76%** (580 → 140 bytes)

## Migration Strategy

1. **Dual Output Mode**: Support both verbose and compact formats
2. **API Parameter**: Add `?format=compact` parameter to API endpoints
3. **Backward Compatibility**: Keep verbose as default initially
4. **Gradual Migration**: Phase in compact format over time

## Implementation Considerations

- **Memory Usage**: Row-based organization improves memory efficiency
- **Processing Speed**: Fewer objects to process improves performance  
- **Parsing Complexity**: Slightly more complex parsing logic needed
- **Tool Compatibility**: May need conversion utilities for existing tools

This compact schema maintains all essential Excel information while dramatically reducing file size, making it ideal for large spreadsheets and API responses. 