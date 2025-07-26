#!/usr/bin/env python3
"""
Test script for table transformation functionality
"""

import json
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.excel_processor import ExcelProcessor
from converter.table_processor import TableProcessor

def create_sample_excel_json():
    """Create a sample Excel JSON structure for testing"""
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
                    "comments": []
                }
            ],
            "properties": {}
        }
    }
    return sample_json

def test_direct_transformation():
    """Test the table transformation directly using the TableProcessor class"""
    print("=== Testing Direct Table Transformation ===")
    
    # Create sample Excel JSON
    sample_json = create_sample_excel_json()
    
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
            
            print(f"    Columns ({len(table['columns'])}):")
            for col in table['columns']:
                is_header = col.get('is_header_column', 'N/A')
                print(f"      {col['column_letter']}: '{col['column_label']}' (header: {is_header})")
            
            print(f"    Rows ({len(table['rows'])}):")
            for row in table['rows']:
                is_header = row.get('is_header_row', 'N/A')
                print(f"      Row {row['row_index']}: '{row['row_label']}' (header: {is_header})")
    
    return table_data

def test_api_transformation():
    """Test the table transformation via API"""
    print("\n=== Testing API Table Transformation ===")
    
    try:
        # Create sample Excel JSON
        sample_json = create_sample_excel_json()
        
        # Make API request
        url = "http://localhost:8001/api/transform-tables/"
        payload = {
            "json_data": sample_json,
            "options": {
                "table_detection": {
                    "use_gaps": True,
                    "use_formatting": True,
                    "use_merged_cells": True
                }
            }
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API transformation successful!")
            
            # Print table information
            table_data = result['table_data']
            for sheet in table_data['workbook']['sheets']:
                print(f"\nSheet: {sheet['name']}")
                for table in sheet.get('tables', []):
                    print(f"  Table: {table['name']} ({table['metadata']['detection_method']})")
                    print(f"    Columns: {len(table['columns'])}")
                    print(f"    Rows: {len(table['rows'])}")
                    
                    # Show first few column labels
                    col_labels = [col['column_label'] for col in table['columns'][:3]]
                    print(f"    Sample column labels: {col_labels}")
                    
                    # Show first few row labels
                    row_labels = [row['row_label'] for row in table['rows'][:3]]
                    print(f"    Sample row labels: {row_labels}")
            
            return result['table_data']
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

def save_results(table_data, filename):
    """Save the transformed data to a JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(table_data, f, indent=2)
        print(f"✅ Results saved to {filename}")
    except Exception as e:
        print(f"❌ Failed to save results: {str(e)}")

def main():
    """Main test function"""
    print("Testing Table Transformation Functionality")
    print("=" * 50)
    
    # Test direct transformation
    direct_result = test_direct_transformation()
    
    # Test API transformation
    api_result = test_api_transformation()
    
    # Save results
    if direct_result:
        save_results(direct_result, "test_direct_transformation_result.json")
    
    if api_result:
        save_results(api_result, "test_api_transformation_result.json")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main() 