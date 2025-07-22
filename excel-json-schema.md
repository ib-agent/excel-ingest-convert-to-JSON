# Excel to JSON Schema Documentation

This document defines the comprehensive JSON schema for representing Excel spreadsheets, including all available metadata, formulas, and structural information.

## Overview

The JSON schema captures the complete structure of an Excel workbook, including:
- File-level metadata
- Sheet-level information (frozen rows/columns, protection, etc.)
- Cell-level data with values, formulas, and formatting
- Row and column properties
- Merged cells
- Charts and images
- Comments and notes

## Root Schema Structure

```json
{
  "workbook": {
    "metadata": {},
    "sheets": [],
    "properties": {}
  }
}
```

## Workbook Metadata

```json
{
  "metadata": {
    "filename": "string",
    "file_size": "number",
    "created_date": "ISO 8601 datetime",
    "modified_date": "ISO 8601 datetime",
    "creator": "string",
    "last_modified_by": "string",
    "title": "string",
    "subject": "string",
    "keywords": "string",
    "category": "string",
    "description": "string",
    "language": "string",
    "revision": "number",
    "version": "string",
    "application": "string",
    "app_version": "string",
    "company": "string",
    "manager": "string",
    "hyperlink_base": "string",
    "template": "string",
    "status": "string",
    "total_editing_time": "number",
    "pages": "number",
    "words": "number",
    "characters": "number",
    "characters_with_spaces": "number",
    "application_name": "string",
    "security": {
      "workbook_password": "boolean",
      "revision_password": "boolean",
      "lock_structure": "boolean",
      "lock_windows": "boolean"
    }
  }
}
```

## Sheet Information

```json
{
  "sheets": [
    {
      "name": "string",
      "index": "number",
      "sheet_id": "string",
      "state": "visible|hidden|very_hidden",
      "sheet_type": "worksheet|chart|macro",
      "properties": {
        "code_name": "string",
        "enable_format_conditions_calculation": "boolean",
        "filter_mode": "boolean",
        "published": "boolean",
        "sync_horizontal": "boolean",
        "sync_ref": "string",
        "sync_vertical": "boolean",
        "transition_evaluation": "boolean",
        "transition_entry": "boolean",
        "tab_color": {
          "rgb": "string",
          "theme": "number",
          "tint": "number"
        }
      },
      "dimensions": {
        "min_row": "number",
        "max_row": "number",
        "min_col": "number",
        "max_col": "number"
      },
      "frozen_panes": {
        "frozen_rows": "number",
        "frozen_cols": "number",
        "top_left_cell": "string"
      },
      "views": [
        {
          "state": "normal|page_break_preview|page_layout",
          "zoom_scale": "number",
          "zoom_scale_normal": "number",
          "zoom_scale_page_layout_view": "number",
          "zoom_scale_sheet_layout_view": "number",
          "tab_selected": "boolean",
          "show_grid_lines": "boolean",
          "show_row_col_headers": "boolean",
          "show_ruler": "boolean",
          "show_zeros": "boolean",
          "right_to_left": "boolean",
          "show_outline_symbols": "boolean",
          "default_grid_color": "boolean",
          "show_white_space": "boolean",
          "view": "normal|page_break_preview|page_layout",
          "window_protection": "boolean",
          "show_formulas": "boolean",
          "show_vertical_scroll_bar": "boolean",
          "show_horizontal_scroll_bar": "boolean",
          "show_sheet_tabs": "boolean",
          "auto_filter_date_grouping": "boolean",
          "sheet_state": "visible|hidden|very_hidden",
          "zoom_scale": "number",
          "zoom_scale_normal": "number",
          "zoom_scale_page_layout_view": "number",
          "zoom_scale_sheet_layout_view": "number",
          "tab_selected": "boolean",
          "show_grid_lines": "boolean",
          "show_row_col_headers": "boolean",
          "show_ruler": "boolean",
          "show_zeros": "boolean",
          "right_to_left": "boolean",
          "show_outline_symbols": "boolean",
          "default_grid_color": "boolean",
          "show_white_space": "boolean",
          "view": "normal|page_break_preview|page_layout",
          "window_protection": "boolean",
          "show_formulas": "boolean",
          "show_vertical_scroll_bar": "boolean",
          "show_horizontal_scroll_bar": "boolean",
          "show_sheet_tabs": "boolean",
          "auto_filter_date_grouping": "boolean",
          "sheet_state": "visible|hidden|very_hidden"
        }
      ],
      "protection": {
        "sheet": "boolean",
        "objects": "boolean",
        "scenarios": "boolean",
        "format_cells": "boolean",
        "format_columns": "boolean",
        "format_rows": "boolean",
        "insert_columns": "boolean",
        "insert_rows": "boolean",
        "insert_hyperlinks": "boolean",
        "delete_columns": "boolean",
        "delete_rows": "boolean",
        "select_locked_cells": "boolean",
        "sort": "boolean",
        "auto_filter": "boolean",
        "pivot_tables": "boolean",
        "password": "string"
      },
      "rows": [],
      "columns": [],
      "cells": {},
      "merged_cells": [],
      "data_validations": [],
      "conditional_formatting": [],
      "charts": [],
      "images": [],
      "comments": []
    }
  ]
}
```

## Row Properties

```json
{
  "rows": [
    {
      "row_number": "number",
      "height": "number",
      "hidden": "boolean",
      "outline_level": "number",
      "collapsed": "boolean",
      "style": "string",
      "custom_height": "boolean",
      "custom_format": "boolean",
      "thick_top": "boolean",
      "thick_bottom": "boolean",
      "ht": "number",
      "s": "number",
      "custom_font": "boolean",
      "custom_border": "boolean",
      "custom_pattern": "boolean",
      "custom_protection": "boolean",
      "custom_alignment": "boolean"
    }
  ]
}
```

## Column Properties

```json
{
  "columns": [
    {
      "column_letter": "string",
      "column_number": "number",
      "width": "number",
      "hidden": "boolean",
      "outline_level": "number",
      "collapsed": "boolean",
      "style": "string",
      "custom_width": "boolean",
      "custom_format": "boolean",
      "best_fit": "boolean",
      "auto_size": "boolean",
      "width": "number",
      "s": "number",
      "custom_font": "boolean",
      "custom_border": "boolean",
      "custom_pattern": "boolean",
      "custom_protection": "boolean",
      "custom_alignment": "boolean"
    }
  ]
}
```

## Cell Data Structure

```json
{
  "cells": {
    "A1": {
      "coordinate": "string",
      "row": "number",
      "column": "number",
      "column_letter": "string",
      "value": "any",
      "data_type": "string|number|boolean|date|error|null",
      "formula": "string|null",
      "formula_type": "array|shared|normal|null",
      "shared_formula": "string|null",
      "array_formula": "string|null",
      "comment": {
        "author": "string",
        "text": "string",
        "height": "number",
        "width": "number"
      },
      "hyperlink": {
        "target": "string",
        "location": "string",
        "tooltip": "string",
        "display": "string"
      },
      "style": {
        "font": {
          "name": "string",
          "size": "number",
          "bold": "boolean",
          "italic": "boolean",
          "underline": "string",
          "strike": "boolean",
          "color": {
            "rgb": "string",
            "theme": "number",
            "tint": "number"
          },
          "scheme": "string"
        },
        "fill": {
          "fill_type": "string",
          "start_color": {
            "rgb": "string",
            "theme": "number",
            "tint": "number"
          },
          "end_color": {
            "rgb": "string",
            "theme": "number",
            "tint": "number"
          }
        },
        "border": {
          "left": {
            "style": "string",
            "color": {
              "rgb": "string",
              "theme": "number",
              "tint": "number"
            }
          },
          "right": {
            "style": "string",
            "color": {
              "rgb": "string",
              "theme": "number",
              "tint": "number"
            }
          },
          "top": {
            "style": "string",
            "color": {
              "rgb": "string",
              "theme": "number",
              "tint": "number"
            }
          },
          "bottom": {
            "style": "string",
            "color": {
              "rgb": "string",
              "theme": "number",
              "tint": "number"
            }
          },
          "diagonal": {
            "style": "string",
            "color": {
              "rgb": "string",
              "theme": "number",
              "tint": "number"
            }
          },
          "diagonal_direction": "string"
        },
        "alignment": {
          "horizontal": "string",
          "vertical": "string",
          "text_rotation": "number",
          "wrap_text": "boolean",
          "shrink_to_fit": "boolean",
          "indent": "number",
          "relative_indent": "number",
          "justify_last_line": "boolean",
          "reading_order": "number"
        },
        "number_format": "string",
        "protection": {
          "locked": "boolean",
          "hidden": "boolean"
        }
      },
      "is_date": "boolean",
      "is_time": "boolean",
      "is_datetime": "boolean",
      "is_number": "boolean",
      "is_string": "boolean",
      "is_boolean": "boolean",
      "is_error": "boolean",
      "is_empty": "boolean"
    }
  }
}
```

## Merged Cells

```json
{
  "merged_cells": [
    {
      "range": "string",
      "start_cell": "string",
      "end_cell": "string",
      "start_row": "number",
      "start_column": "number",
      "end_row": "number",
      "end_column": "number"
    }
  ]
}
```

## Data Validations

```json
{
  "data_validations": [
    {
      "range": "string",
      "type": "string",
      "operator": "string",
      "formula1": "string",
      "formula2": "string",
      "allow_blank": "boolean",
      "show_error_message": "boolean",
      "error_title": "string",
      "error_message": "string",
      "show_input_message": "boolean",
      "input_title": "string",
      "input_message": "string",
      "prompt_title": "string",
      "prompt_message": "string"
    }
  ]
}
```

## Conditional Formatting

```json
{
  "conditional_formatting": [
    {
      "range": "string",
      "priority": "number",
      "stop_if_true": "boolean",
      "type": "string",
      "color_scale": {
        "cfvo": [
          {
            "type": "string",
            "val": "string"
          }
        ],
        "color": [
          {
            "rgb": "string"
          }
        ]
      },
      "data_bar": {
        "cfvo": [
          {
            "type": "string",
            "val": "string"
          }
        ],
        "color": {
          "rgb": "string"
        }
      },
      "icon_set": {
        "icon_set": "string",
        "cfvo": [
          {
            "type": "string",
            "val": "string"
          }
        ]
      },
      "dxf": {
        "font": {},
        "fill": {},
        "border": {},
        "alignment": {},
        "number_format": {},
        "protection": {}
      }
    }
  ]
}
```

## Charts

```json
{
  "charts": [
    {
      "chart_type": "string",
      "title": "string",
      "x_axis": {
        "title": "string",
        "min": "number",
        "max": "number",
        "major_unit": "number",
        "minor_unit": "number"
      },
      "y_axis": {
        "title": "string",
        "min": "number",
        "max": "number",
        "major_unit": "number",
        "minor_unit": "number"
      },
      "series": [
        {
          "name": "string",
          "x_values": "string",
          "y_values": "string",
          "data_labels": "boolean"
        }
      ],
      "position": {
        "x": "number",
        "y": "number",
        "width": "number",
        "height": "number"
      }
    }
  ]
}
```

## Images

```json
{
  "images": [
    {
      "image_type": "string",
      "position": {
        "x": "number",
        "y": "number",
        "width": "number",
        "height": "number"
      },
      "anchor": "string",
      "filename": "string",
      "data": "base64_string"
    }
  ]
}
```

## Comments

```json
{
  "comments": [
    {
      "cell": "string",
      "author": "string",
      "text": "string",
      "position": {
        "x": "number",
        "y": "number",
        "width": "number",
        "height": "number"
      },
      "visible": "boolean"
    }
  ]
}
```

## Workbook Properties

```json
{
  "properties": {
    "code_name": "string",
    "date_1904": "boolean",
    "filter_mode": "boolean",
    "hide_pivot_chart_list": "boolean",
    "published": "boolean",
    "refresh_all_connections": "boolean",
    "save_external_link_values": "boolean",
    "update_links": "string",
    "check_compatibility": "boolean",
    "auto_compress_pictures": "boolean",
    "backup_file": "boolean",
    "check_calculations": "boolean",
    "create_backup": "boolean",
    "crash_save": "boolean",
    "data_extract_load": "boolean",
    "default_theme_version": "number",
    "delete_inactive_worksheets": "boolean",
    "display_ink_annotations": "boolean",
    "first_sheet": "number",
    "hide_pivot_chart_list": "boolean",
    "minimized": "boolean",
    "prevent_update": "boolean",
    "show_ink_annotations": "boolean",
    "show_pivot_chart_filter": "boolean",
    "update_remote_references": "boolean",
    "window_height": "number",
    "window_width": "number",
    "window_minimized": "boolean",
    "window_maximized": "boolean",
    "window_x": "number",
    "window_y": "number",
    "active_sheet_index": "number",
    "first_visible_sheet": "number",
    "tab_ratio": "number",
    "visibility": "string"
  }
}
```

## Data Types

### Cell Value Types
- `string`: Text values
- `number`: Numeric values (integers, floats)
- `boolean`: True/false values
- `date`: Date values (ISO 8601 format)
- `error`: Excel error values (#N/A, #VALUE!, etc.)
- `null`: Empty cells

### Formula Types
- `normal`: Standard formulas
- `array`: Array formulas (entered with Ctrl+Shift+Enter)
- `shared`: Shared formulas (for efficiency)
- `null`: No formula present

### Border Styles
- `thin`
- `medium`
- `thick`
- `dashed`
- `dotted`
- `double`
- `hair`
- `medium_dashed`
- `dash_dot`
- `medium_dash_dot`
- `dash_dot_dot`
- `medium_dash_dot_dot`
- `slant_dash_dot`

### Fill Types
- `none`
- `solid`
- `darkGray`
- `mediumGray`
- `lightGray`
- `gray125`
- `gray0625`
- `darkHorizontal`
- `darkVertical`
- `darkDown`
- `darkUp`
- `darkGrid`
- `darkTrellis`
- `lightHorizontal`
- `lightVertical`
- `lightDown`
- `lightUp`
- `lightGrid`
- `lightTrellis`

### Alignment Options
- Horizontal: `left`, `center`, `right`, `fill`, `justify`, `centerContinuous`, `distributed`
- Vertical: `top`, `center`, `bottom`, `justify`, `distributed`

## Example Output

```json
{
  "workbook": {
    "metadata": {
      "filename": "example.xlsx",
      "creator": "John Doe",
      "created_date": "2024-01-15T10:30:00Z",
      "modified_date": "2024-01-15T14:45:00Z"
    },
    "sheets": [
      {
        "name": "Sheet1",
        "index": 0,
        "state": "visible",
        "dimensions": {
          "min_row": 1,
          "max_row": 10,
          "min_col": 1,
          "max_col": 5
        },
        "frozen_panes": {
          "frozen_rows": 1,
          "frozen_cols": 1
        },
        "cells": {
          "A1": {
            "coordinate": "A1",
            "row": 1,
            "column": 1,
            "column_letter": "A",
            "value": "Product Name",
            "data_type": "string",
            "formula": null,
            "style": {
              "font": {
                "bold": true,
                "size": 12
              },
              "fill": {
                "fill_type": "solid",
                "start_color": {
                  "rgb": "CCCCCC"
                }
              }
            }
          },
          "B1": {
            "coordinate": "B1",
            "row": 1,
            "column": 2,
            "column_letter": "B",
            "value": "Price",
            "data_type": "string",
            "formula": null,
            "style": {
              "font": {
                "bold": true,
                "size": 12
              }
            }
          },
          "A2": {
            "coordinate": "A2",
            "row": 2,
            "column": 1,
            "column_letter": "A",
            "value": "Widget A",
            "data_type": "string",
            "formula": null
          },
          "B2": {
            "coordinate": "B2",
            "row": 2,
            "column": 2,
            "column_letter": "B",
            "value": 29.99,
            "data_type": "number",
            "formula": null,
            "style": {
              "number_format": "$#,##0.00"
            }
          }
        },
        "merged_cells": [],
        "data_validations": [],
        "conditional_formatting": []
      }
    ],
    "properties": {
      "active_sheet_index": 0,
      "window_height": 600,
      "window_width": 800
    }
  }
}
```

This schema provides a comprehensive representation of Excel workbooks, capturing all available metadata, formatting, formulas, and structural information that can be extracted using the openpyxl library. 