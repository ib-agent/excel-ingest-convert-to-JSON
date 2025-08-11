#!/usr/bin/env python3
"""
Test script to verify the refactored CompactTableProcessor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.compact_table_processor import CompactTableProcessor


def test_compact_processor():
    """Test the refactored compact processor"""
    
    # Test data in compact format
    test_data = {
        'workbook': {
            'sheets': [{
                'name': 'Compact Test',
                'dimensions': [1, 1, 6, 3],  # [min_row, min_col, max_row, max_col]
                'rows': [
                    # Table 1
                    {'r': 1, 'cells': [[1, 'Product'], [2, 'Q1'], [3, 'Q2']]},
                    {'r': 2, 'cells': [[1, 'Widget A'], [2, 100], [3, 120]]},
                    {'r': 3, 'cells': [[1, 'Widget B'], [2, 150], [3, 160]]},
                    # Gap
                    # Table 2
                    {'r': 5, 'cells': [[1, 'Item'], [2, 'Stock'], [3, 'Status']]},
                    {'r': 6, 'cells': [[1, 'Laptop'], [2, 25], [3, 'Good']]},
                ],
                'tables': []
            }]
        }
    }
    
    processor = CompactTableProcessor()
    
    print("=== Testing Refactored Compact Processor ===")
    
    # Test with gap detection
    options = {'table_detection': {'use_gaps': True, 'gap_threshold': 1}}
    result = processor.transform_to_compact_table_format(test_data, options)
    
    tables = result['workbook']['sheets'][0]['tables']
    print(f"\nWith gap detection: Found {len(tables)} tables")
    for i, table in enumerate(tables):
        region = table['region']
        method = table['meta']['method']
        print(f"  Table {i+1}: Rows {region[0]}-{region[2]}, Method: {method}")
        print(f"    Column labels: {table['labels']['cols']}")
        print(f"    Row labels: {table['labels']['rows']}")
    
    # Test without gap detection
    options = {'table_detection': {'use_gaps': False}}
    result_no_gaps = processor.transform_to_compact_table_format(test_data, options)
    
    tables_no_gaps = result_no_gaps['workbook']['sheets'][0]['tables']
    print(f"\nWithout gap detection: Found {len(tables_no_gaps)} tables")
    for i, table in enumerate(tables_no_gaps):
        region = table['region']
        method = table['meta']['method']
        print(f"  Table {i+1}: Rows {region[0]}-{region[2]}, Method: {method}")
    
    print("\n✅ Compact processor refactoring successful!")
    return tables


if __name__ == "__main__":
    test_compact_processor() 