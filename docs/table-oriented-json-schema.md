# Table-Oriented JSON Schema

This document defines the table-oriented JSON schema that enhances the existing Excel JSON representation by adding table structure with column and row labels.

## Overview

The table-oriented JSON schema extends the existing Excel JSON schema by adding a `tables` array to each sheet. This provides a more structured view of the data while preserving all original information. Each table includes:

- **Column definitions** with `column_label` properties
- **Row definitions** with `row_label` properties
- **Table metadata** including detection method and region information
- **All original cell data** preserved in the table structure

## Schema Structure

The table-oriented schema maintains the complete original structure and adds table information:

```json
{
  "workbook": {
    "metadata": {},
    "sheets": [
      {
        "name": "string",
        "index": "number",
        "sheet_id": "string",
        "state": "visible|hidden|very_hidden",
        "sheet_type": "worksheet|chart|macro",
        "properties": {},
        "dimensions": {},
        "frozen_panes": {},
        "views": [],
        "protection": {},
        "rows": [],
        "columns": [],
        "cells": {},
        "merged_cells": [],
        "data_validations": [],
        "conditional_formatting": [],
        "charts": [],
        "images": [],
        "comments": [],
        "tables": []
      }
    ],
    "properties": {}
  }
}
```

## Table Structure

Each table in the `tables` array has the following structure:

```json
{
  "table_id": "string",
  "name": "string",
  "region": {
    "start_row": "number",
    "end_row": "number",
    "start_col": "number",
    "end_col": "number",
    "detection_method": "string"
  },
  "header_info": {
    "header_rows": ["number"],
    "header_columns": ["number"],
    "data_start_row": "number",
    "data_start_col": "number"
  },
  "columns": [],
  "rows": [],
  "metadata": {
    "detection_method": "string",
    "cell_count": "number",
    "has_merged_cells": "boolean"
  }
}
```

### Table Properties

- **table_id**: Unique identifier for the table (e.g., "table_1", "table_2")
- **name**: Human-readable name for the table (e.g., "Table 1", "Sales Data")
- **region**: Defines the table boundaries in the sheet
- **header_info**: Identifies which rows/columns contain headers
- **columns**: Array of column definitions with labels
- **rows**: Array of row definitions with labels
- **metadata**: Additional information about the table

## Column Structure

Each column in the `columns` array has the following structure:

```json
{
  "column_index": "number",
  "column_letter": "string",
  "column_label": "string",
  "is_header_column": "boolean",
  "width": "number|null",
  "hidden": "boolean",
  "cells": {}
}
```

### Column Properties

- **column_index**: Numeric column index (1-based)
- **column_letter**: Excel column letter (A, B, C, etc.)
- **column_label**: Human-readable label derived from header cells
- **is_header_column**: Whether this column contains header information
- **width**: Column width (if available from sheet properties)
- **hidden**: Whether the column is hidden
- **cells**: Dictionary of cell data for this column

### Column Label Generation

Column labels are generated from header rows using the following logic:

1. **Single Header Row**: Uses the cell value directly
2. **Multiple Header Rows**: Combines values with " | " separator
3. **No Header**: Falls back to "Column {letter}" format

Example:
```json
{
  "column_label": "Q1 | Jan"  // From header rows with "Q1" and "Jan"
}
```

## Row Structure

Each row in the `rows` array has the following structure:

```json
{
  "row_index": "number",
  "row_label": "string",
  "is_header_row": "boolean",
  "height": "number|null",
  "hidden": "boolean",
  "cells": {}
}
```

### Row Properties

- **row_index**: Numeric row index (1-based)
- **row_label**: Human-readable label derived from header cells
- **is_header_row**: Whether this row contains header information
- **height**: Row height (if available from sheet properties)
- **hidden**: Whether the row is hidden
- **cells**: Dictionary of cell data for this row

### Row Label Generation

Row labels are generated from header columns using the following logic:

1. **Single Header Column**: Uses the cell value directly
2. **Multiple Header Columns**: Combines values with " | " separator
3. **No Header**: Falls back to "Row {number}" format

Example:
```json
{
  "row_label": "Sales | North Region"  // From header columns with "Sales" and "North Region"
}
```

## Table Detection Methods

The system uses multiple methods to detect tables:

### 1. Gap-Based Detection
- Identifies tables by looking for empty rows/columns that separate data regions
- Useful for sheets with multiple distinct tables

### 2. Formatting-Based Detection
- Detects tables based on header-like formatting (bold, background colors, borders)
- Identifies header rows and extends table boundaries accordingly

### 3. Merged Cell Detection
- Analyzes merged cell patterns to identify table boundaries
- Handles complex table structures with merged headers

### 4. Default Table
- Creates a single table for the entire sheet if no other tables are detected
- Ensures all data is accessible in table format

## API Usage

### Transform to Table Format

**Endpoint**: `POST /api/transform-tables/`

**Request Body**:
```json
{
  "json_data": {
    // Original Excel JSON schema output
  },
  "options": {
    "table_detection": {
      "use_gaps": true,
      "use_formatting": true,
      "use_merged_cells": true,
      "min_table_size": 4
    },
    "header_detection": {
      "auto_detect_headers": true,
      "header_rows": [1],
      "header_columns": [1]
    }
  }
}
```

**Response**:
```json
{
  "success": true,
  "table_data": {
    // Enhanced JSON with table structure
  }
}
```

## Example Output

```json
{
  "workbook": {
    "metadata": {
      "filename": "sales_data.xlsx",
      "creator": "John Doe"
    },
    "sheets": [
      {
        "name": "Sheet1",
        "cells": {
          "A1": {"value": "Product", "row": 1, "column": 1},
          "B1": {"value": "Q1", "row": 1, "column": 2},
          "B2": {"value": "Jan", "row": 2, "column": 2},
          "A3": {"value": "Widget A", "row": 3, "column": 1},
          "B3": {"value": 1500, "row": 3, "column": 2}
        },
        "tables": [
          {
            "table_id": "table_1",
            "name": "Table 1",
            "region": {
              "start_row": 1,
              "end_row": 3,
              "start_col": 1,
              "end_col": 2,
              "detection_method": "formatting"
            },
            "header_info": {
              "header_rows": [1, 2],
              "header_columns": [1],
              "data_start_row": 3,
              "data_start_col": 2
            },
            "columns": [
              {
                "column_index": 1,
                "column_letter": "A",
                "column_label": "Product",
                "is_header_column": true,
                "cells": {
                  "A1": {"value": "Product", "row": 1, "column": 1},
                  "A3": {"value": "Widget A", "row": 3, "column": 1}
                }
              },
              {
                "column_index": 2,
                "column_letter": "B",
                "column_label": "Q1 | Jan",
                "is_header_column": false,
                "cells": {
                  "B1": {"value": "Q1", "row": 1, "column": 2},
                  "B2": {"value": "Jan", "row": 2, "column": 2},
                  "B3": {"value": 1500, "row": 3, "column": 2}
                }
              }
            ],
            "rows": [
              {
                "row_index": 1,
                "row_label": "Product",
                "is_header_row": true,
                "cells": {
                  "A1": {"value": "Product", "row": 1, "column": 1},
                  "B1": {"value": "Q1", "row": 1, "column": 2}
                }
              },
              {
                "row_index": 2,
                "row_label": "Product",
                "is_header_row": true,
                "cells": {
                  "A2": {"value": null, "row": 2, "column": 1},
                  "B2": {"value": "Jan", "row": 2, "column": 2}
                }
              },
              {
                "row_index": 3,
                "row_label": "Widget A",
                "is_header_row": false,
                "cells": {
                  "A3": {"value": "Widget A", "row": 3, "column": 1},
                  "B3": {"value": 1500, "row": 3, "column": 2}
                }
              }
            ],
            "metadata": {
              "detection_method": "formatting",
              "cell_count": 5,
              "has_merged_cells": false
            }
          }
        ]
      }
    ]
  }
}
```

## Benefits

1. **Structured Data Access**: Easy access to table structure and relationships
2. **Labeled Columns and Rows**: Human-readable labels for data navigation
3. **Preserved Original Data**: All original cell information maintained
4. **Multiple Table Support**: Handles sheets with multiple tables
5. **Flexible Detection**: Multiple methods for table identification
6. **Backward Compatibility**: Original JSON structure unchanged

## Use Cases

1. **Data Analysis**: Structured access to table data for analysis
2. **API Integration**: Clean table structure for downstream systems
3. **Reporting**: Easy generation of reports with proper headers
4. **Data Migration**: Structured data for database imports
5. **Business Intelligence**: Enhanced data modeling capabilities

## Configuration Options

### Table Detection Options

```json
{
  "table_detection": {
    "use_gaps": true,
    "use_formatting": true,
    "use_merged_cells": true,
    "min_table_size": 4,
    "max_tables_per_sheet": 10
  }
}
```

### Header Detection Options

```json
{
  "header_detection": {
    "auto_detect_headers": true,
    "header_rows": [1],
    "header_columns": [1],
    "use_formatting": true,
    "min_header_cells": 2
  }
}
```

### Output Options

```json
{
  "output": {
    "include_cell_data": true,
    "include_metadata": true,
    "flatten_labels": false,
    "max_label_length": 100
  }
}
```

This table-oriented schema provides a powerful way to work with Excel data in a structured format while maintaining all the richness of the original Excel representation. 