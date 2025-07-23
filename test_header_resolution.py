#!/usr/bin/env python3
"""
Test script for header resolution functionality
"""

import json
import requests
from converter.table_processor import TableProcessor
from converter.header_resolver import HeaderResolver

def create_sample_table_json():
    """Create a sample table-oriented JSON for testing header resolution"""
    sample_json = {
        "workbook": {
            "metadata": {
                "filename": "test_sales_data.xlsx",
                "creator": "Test User"
            },
            "sheets": [
                {
                    "name": "Sales Data",
                    "index": 0,
                    "sheet_id": "1",
                    "state": "visible",
                    "sheet_type": "worksheet",
                    "properties": {},
                    "dimensions": {
                        "min_row": 1,
                        "max_row": 5,
                        "min_col": 1,
                        "max_col": 4
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
                        "A1": {
                            "coordinate": "A1",
                            "row": 1,
                            "column": 1,
                            "column_letter": "A",
                            "value": "Product",
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
                        "A3": {
                            "coordinate": "A3",
                            "row": 3,
                            "column": 1,
                            "column_letter": "A",
                            "value": "Widget A",
                            "data_type": "string",
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
                            "value": "Widget B",
                            "data_type": "string",
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
                        }
                    },
                    "merged_cells": [],
                    "data_validations": [],
                    "conditional_formatting": [],
                    "charts": [],
                    "images": [],
                    "comments": [],
                    "tables": [
                        {
                            "table_id": "table_1",
                            "name": "Table 1",
                            "region": {
                                "start_row": 1,
                                "end_row": 4,
                                "start_col": 1,
                                "end_col": 3,
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
                                    "is_header_column": True,
                                    "width": None,
                                    "hidden": False,
                                    "cells": {
                                        "A1": {
                                            "coordinate": "A1",
                                            "row": 1,
                                            "column": 1,
                                            "column_letter": "A",
                                            "value": "Product",
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
                                        "A3": {
                                            "coordinate": "A3",
                                            "row": 3,
                                            "column": 1,
                                            "column_letter": "A",
                                            "value": "Widget A",
                                            "data_type": "string",
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
                                        "A4": {
                                            "coordinate": "A4",
                                            "row": 4,
                                            "column": 1,
                                            "column_letter": "A",
                                            "value": "Widget B",
                                            "data_type": "string",
                                            "formula": None,
                                            "style": {
                                                "font": {},
                                                "fill": {},
                                                "border": {},
                                                "alignment": {},
                                                "number_format": "",
                                                "protection": {}
                                            }
                                        }
                                    }
                                },
                                {
                                    "column_index": 2,
                                    "column_letter": "B",
                                    "column_label": "Q1 | Jan",
                                    "is_header_column": False,
                                    "width": None,
                                    "hidden": False,
                                    "cells": {
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
                                        }
                                    }
                                },
                                {
                                    "column_index": 3,
                                    "column_letter": "C",
                                    "column_label": "Q2 | Apr",
                                    "is_header_column": False,
                                    "width": None,
                                    "hidden": False,
                                    "cells": {
                                        "C1": {
                                            "coordinate": "C1",
                                            "row": 1,
                                            "column": 3,
                                            "column_letter": "C",
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
                                        "C2": {
                                            "coordinate": "C2",
                                            "row": 2,
                                            "column": 3,
                                            "column_letter": "C",
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
                                        "C3": {
                                            "coordinate": "C3",
                                            "row": 3,
                                            "column": 3,
                                            "column_letter": "C",
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
                                        "C4": {
                                            "coordinate": "C4",
                                            "row": 4,
                                            "column": 3,
                                            "column_letter": "C",
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
                                        }
                                    }
                                }
                            ],
                            "rows": [
                                {
                                    "row_index": 1,
                                    "row_label": "Product",
                                    "is_header_row": True,
                                    "height": None,
                                    "hidden": False,
                                    "cells": {
                                        "A1": {
                                            "coordinate": "A1",
                                            "row": 1,
                                            "column": 1,
                                            "column_letter": "A",
                                            "value": "Product",
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
                                        }
                                    }
                                },
                                {
                                    "row_index": 2,
                                    "row_label": "Product",
                                    "is_header_row": True,
                                    "height": None,
                                    "hidden": False,
                                    "cells": {
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
                                        }
                                    }
                                },
                                {
                                    "row_index": 3,
                                    "row_label": "Widget A",
                                    "is_header_row": False,
                                    "height": None,
                                    "hidden": False,
                                    "cells": {
                                        "A3": {
                                            "coordinate": "A3",
                                            "row": 3,
                                            "column": 1,
                                            "column_letter": "A",
                                            "value": "Widget A",
                                            "data_type": "string",
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
                                        }
                                    }
                                },
                                {
                                    "row_index": 4,
                                    "row_label": "Widget B",
                                    "is_header_row": False,
                                    "height": None,
                                    "hidden": False,
                                    "cells": {
                                        "A4": {
                                            "coordinate": "A4",
                                            "row": 4,
                                            "column": 1,
                                            "column_letter": "A",
                                            "value": "Widget B",
                                            "data_type": "string",
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
                                        }
                                    }
                                }
                            ],
                            "metadata": {
                                "detection_method": "formatting",
                                "cell_count": 12,
                                "has_merged_cells": False
                            }
                        }
                    ]
                }
            ],
            "properties": {}
        }
    }
    return sample_json

def test_direct_header_resolution():
    """Test header resolution directly using the HeaderResolver class"""
    print("=== Testing Direct Header Resolution ===")
    
    # Create sample table JSON
    table_json = create_sample_table_json()
    
    # Initialize header resolver
    resolver = HeaderResolver()
    
    # Resolve headers
    enhanced_data = resolver.resolve_headers(table_json)
    
    # Print results
    print(f"Number of sheets: {len(enhanced_data['workbook']['sheets'])}")
    
    for i, sheet in enumerate(enhanced_data['workbook']['sheets']):
        print(f"\nSheet {i+1}: {sheet['name']}")
        
        for j, table in enumerate(sheet.get('tables', [])):
            print(f"\n  Table {j+1}: {table['name']}")
            
            # Check data cells for header context
            data_cells_with_headers = 0
            for col in table.get('columns', []):
                for cell_key, cell in col.get('cells', {}).items():
                    if 'headers' in cell:
                        data_cells_with_headers += 1
                        print(f"    Data cell {cell_key}:")
                        print(f"      Value: {cell.get('value')}")
                        print(f"      Column headers: {cell['headers']['full_column_path']}")
                        print(f"      Row headers: {cell['headers']['full_row_path']}")
                        print(f"      Summary: {cell['headers']['header_summary']}")
                        print()
            
            print(f"    Total data cells with headers: {data_cells_with_headers}")
    
    return enhanced_data

def test_api_header_resolution():
    """Test header resolution via API"""
    print("\n=== Testing API Header Resolution ===")
    
    try:
        # Create sample table JSON
        table_json = create_sample_table_json()
        
        # Make API request
        url = "http://localhost:8001/api/resolve-headers/"
        payload = {
            "table_json": table_json,
            "options": {
                "header_detection": {
                    "use_formatting": True,
                    "use_indentation": True
                }
            }
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API header resolution successful!")
            
            # Print summary
            enhanced_data = result['enhanced_data']
            for sheet in enhanced_data['workbook']['sheets']:
                print(f"\nSheet: {sheet['name']}")
                for table in sheet.get('tables', []):
                    print(f"  Table: {table['name']}")
                    
                    # Count cells with headers
                    cells_with_headers = 0
                    for col in table.get('columns', []):
                        for cell in col.get('cells', {}).values():
                            if 'headers' in cell:
                                cells_with_headers += 1
                    
                    print(f"    Data cells with header context: {cells_with_headers}")
            
            return result['enhanced_data']
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on port 8001.")
        return None
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return None

def save_results(enhanced_data, filename):
    """Save the enhanced data to a JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(enhanced_data, f, indent=2)
        print(f"✅ Results saved to {filename}")
    except Exception as e:
        print(f"❌ Failed to save results: {str(e)}")

def main():
    """Main test function"""
    print("Testing Header Resolution Functionality")
    print("=" * 50)
    
    # Test direct header resolution
    direct_result = test_direct_header_resolution()
    
    # Test API header resolution
    api_result = test_api_header_resolution()
    
    # Save results
    if direct_result:
        save_results(direct_result, "test_direct_header_resolution_result.json")
    
    if api_result:
        save_results(api_result, "test_api_header_resolution_result.json")
    
    print("\n" + "=" * 50)
    print("Header resolution test completed!")

if __name__ == "__main__":
    main() 