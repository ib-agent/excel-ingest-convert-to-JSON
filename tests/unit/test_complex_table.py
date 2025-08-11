#!/usr/bin/env python3
"""
Test script for complex table transformation with multi-level headers
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.table_processor import TableProcessor

def create_complex_excel_json():
    """Create a complex Excel JSON structure with multi-level headers"""
    sample_json = {
        "workbook": {
            "metadata": {
                "filename": "complex_sales_data.xlsx",
                "creator": "Test User"
            },
            "sheets": [
                {
                    "name": "Sales Report",
                    "index": 0,
                    "sheet_id": "1",
                    "state": "visible",
                    "sheet_type": "worksheet",
                    "properties": {},
                    "dimensions": {
                        "min_row": 1,
                        "max_row": 6,
                        "min_col": 1,
                        "max_col": 5
                    },
                    "frozen_panes": {
                        "frozen_rows": 2,
                        "frozen_cols": 1
                    },
                    "views": [],
                    "protection": {},
                    "rows": [],
                    "columns": [],
                    "cells": {
                        # Multi-level column headers
                        "A1": {
                            "coordinate": "A1",
                            "row": 1,
                            "column": 1,
                            "column_letter": "A",
                            "value": "Region",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True, "size": 12},
                                "fill": {"fill_type": "solid", "start_color": {"rgb": "CCCCCC"}},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "B1": {
                            "coordinate": "B1",
                            "row": 1,
                            "column": 2,
                            "column_letter": "B",
                            "value": "Q1",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True, "size": 12},
                                "fill": {"fill_type": "solid", "start_color": {"rgb": "CCCCCC"}},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "C1": {
                            "coordinate": "C1",
                            "row": 1,
                            "column": 3,
                            "column_letter": "C",
                            "value": "Q1",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True, "size": 12},
                                "fill": {"fill_type": "solid", "start_color": {"rgb": "CCCCCC"}},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "D1": {
                            "coordinate": "D1",
                            "row": 1,
                            "column": 4,
                            "column_letter": "D",
                            "value": "Q2",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True, "size": 12},
                                "fill": {"fill_type": "solid", "start_color": {"rgb": "CCCCCC"}},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "E1": {
                            "coordinate": "E1",
                            "row": 1,
                            "column": 5,
                            "column_letter": "E",
                            "value": "Q2",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True, "size": 12},
                                "fill": {"fill_type": "solid", "start_color": {"rgb": "CCCCCC"}},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        # Second level headers
                        "A2": {
                            "coordinate": "A2",
                            "row": 2,
                            "column": 1,
                            "column_letter": "A",
                            "value": None,
                            "data_type": "null",
                            "formula": None,
                            "style": {
                                "font": {},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "B2": {
                            "coordinate": "B2",
                            "row": 2,
                            "column": 2,
                            "column_letter": "B",
                            "value": "Jan",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "C2": {
                            "coordinate": "C2",
                            "row": 2,
                            "column": 3,
                            "column_letter": "C",
                            "value": "Feb",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "D2": {
                            "coordinate": "D2",
                            "row": 2,
                            "column": 4,
                            "column_letter": "D",
                            "value": "Apr",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "E2": {
                            "coordinate": "E2",
                            "row": 2,
                            "column": 5,
                            "column_letter": "E",
                            "value": "May",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        # Data rows with row headers
                        "A3": {
                            "coordinate": "A3",
                            "row": 3,
                            "column": 1,
                            "column_letter": "A",
                            "value": "North",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "B3": {
                            "coordinate": "B3",
                            "row": 3,
                            "column": 2,
                            "column_letter": "B",
                            "value": 1500,
                            "data_type": "number",
                            "formula": None,
                            "style": {
                                "font": {},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "#,##0",
                                "protection": {}
                            }
                        },
                        "C3": {
                            "coordinate": "C3",
                            "row": 3,
                            "column": 3,
                            "column_letter": "C",
                            "value": 1600,
                            "data_type": "number",
                            "formula": None,
                            "style": {
                                "font": {},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "#,##0",
                                "protection": {}
                            }
                        },
                        "D3": {
                            "coordinate": "D3",
                            "row": 3,
                            "column": 4,
                            "column_letter": "D",
                            "value": 1700,
                            "data_type": "number",
                            "formula": None,
                            "style": {
                                "font": {},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "#,##0",
                                "protection": {}
                            }
                        },
                        "E3": {
                            "coordinate": "E3",
                            "row": 3,
                            "column": 5,
                            "column_letter": "E",
                            "value": 1800,
                            "data_type": "number",
                            "formula": None,
                            "style": {
                                "font": {},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "#,##0",
                                "protection": {}
                            }
                        },
                        "A4": {
                            "coordinate": "A4",
                            "row": 4,
                            "column": 1,
                            "column_letter": "A",
                            "value": "South",
                            "data_type": "string",
                            "formula": None,
                            "style": {
                                "font": {"bold": True},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "",
                                "protection": {}
                            }
                        },
                        "B4": {
                            "coordinate": "B4",
                            "row": 4,
                            "column": 2,
                            "column_letter": "B",
                            "value": 2200,
                            "data_type": "number",
                            "formula": None,
                            "style": {
                                "font": {},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "#,##0",
                                "protection": {}
                            }
                        },
                        "C4": {
                            "coordinate": "C4",
                            "row": 4,
                            "column": 3,
                            "column_letter": "C",
                            "value": 2300,
                            "data_type": "number",
                            "formula": None,
                            "style": {
                                "font": {},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "#,##0",
                                "protection": {}
                            }
                        },
                        "D4": {
                            "coordinate": "D4",
                            "row": 4,
                            "column": 4,
                            "column_letter": "D",
                            "value": 2400,
                            "data_type": "number",
                            "formula": None,
                            "style": {
                                "font": {},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "#,##0",
                                "protection": {}
                            }
                        },
                        "E4": {
                            "coordinate": "E4",
                            "row": 4,
                            "column": 5,
                            "column_letter": "E",
                            "value": 2500,
                            "data_type": "number",
                            "formula": None,
                            "style": {
                                "font": {},
                                "fill": {},
                                "border": {},
                                "alignment": {},
                                "number_format": "#,##0",
                                "protection": {}
                            }
                        }
                    },
                    "merged_cells": [],
                    "data_validations": [],
                    "conditional_formatting": [],
                    "charts": [],
                    "images": [],
                    "comments": []
                }
            ],
            "properties": {}
        }
    }
    return sample_json

def test_complex_transformation():
    """Test the complex table transformation"""
    print("=== Testing Complex Table Transformation ===")
    
    # Create complex Excel JSON
    sample_json = create_complex_excel_json()
    
    # Initialize table processor
    processor = TableProcessor()
    
    # Transform to table format
    table_data = processor.transform_to_table_format(sample_json)
    
    # Print results
    print(f"Number of sheets: {len(table_data['workbook']['sheets'])}")
    
    for i, sheet in enumerate(table_data['workbook']['sheets']):
        print(f"\nSheet {i+1}: {sheet['name']}")
        print(f"Number of tables: {len(sheet.get('tables', []))}")
        
        for j, table in enumerate(sheet.get('tables', [])):
            print(f"\n  Table {j+1}: {table['name']}")
            print(f"    Region: {table['region']}")
            print(f"    Detection method: {table['metadata']['detection_method']}")
            print(f"    Cell count: {table['metadata']['cell_count']}")
            
            print(f"    Header Info:")
            print(f"      Header rows: {table['header_info']['header_rows']}")
            print(f"      Header columns: {table['header_info']['header_columns']}")
            print(f"      Data starts at: Row {table['header_info']['data_start_row']}, Col {table['header_info']['data_start_col']}")
            
            print(f"    Columns ({len(table['columns'])}):")
            for col in table['columns']:
                is_header = col.get('is_header_column', 'N/A')
                print(f"      {col['column_letter']}: '{col['column_label']}' (header: {is_header})")
            
            print(f"    Rows ({len(table['rows'])}):")
            for row in table['rows']:
                is_header = row.get('is_header_row', 'N/A')
                print(f"      Row {row['row_index']}: '{row['row_label']}' (header: {is_header})")
    
    # Save results
    with open("test_complex_transformation_result.json", 'w') as f:
        json.dump(table_data, f, indent=2)
    print(f"\n✅ Complex transformation results saved to test_complex_transformation_result.json")
    
    return table_data

if __name__ == "__main__":
    test_complex_transformation() 