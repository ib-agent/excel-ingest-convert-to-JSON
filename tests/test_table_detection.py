#!/usr/bin/env python3
"""
Test script to verify table detection improvements

This test verifies that the table detection logic correctly identifies
full table regions instead of just small portions, and that the "unlabeled"
labeling works correctly for blank headers.
"""

import sys
import os
import unittest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.table_processor import TableProcessor


class TestTableDetection(unittest.TestCase):
    """Test cases for table detection functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = TableProcessor()
    
    def test_full_table_detection(self):
        """Test that table detection correctly identifies full table regions"""
        # Test data with a realistic table structure
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 5,
                        'min_col': 1,
                        'max_col': 4
                    },
                    'cells': {
                        # Row 1: Column headers (some blank)
                        'A1': {'value': 'Product'},      # Valid column header
                        'B1': {'value': None},           # Blank column header
                        'C1': {'value': ''},             # Empty column header
                        'D1': {'value': 'Price'},        # Valid column header
                        
                        # Row 2: Row headers (some blank)
                        'A2': {'value': 'Item1'},        # Valid row header
                        'A3': {'value': None},           # Blank row header
                        'A4': {'value': ''},             # Empty row header
                        'A5': {'value': 'Item2'},        # Valid row header
                        
                        # Data cells
                        'B2': {'value': 'Data1'},
                        'C2': {'value': 'Data2'},
                        'D2': {'value': 'Data3'},
                        'B3': {'value': 'Data4'},
                        'C3': {'value': 'Data5'},
                        'D3': {'value': 'Data6'},
                        'B4': {'value': 'Data7'},
                        'C4': {'value': 'Data8'},
                        'D4': {'value': 'Data9'},
                        'B5': {'value': 'Data10'},
                        'C5': {'value': 'Data11'},
                        'D5': {'value': 'Data12'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.processor.transform_to_table_format(test_data)
        
        # Verify that tables were detected
        self.assertIn('workbook', result)
        self.assertIn('sheets', result['workbook'])
        self.assertGreater(len(result['workbook']['sheets']), 0)
        
        sheet = result['workbook']['sheets'][0]
        self.assertIn('tables', sheet)
        self.assertGreater(len(sheet['tables']), 0, "No tables detected")
        
        table = sheet['tables'][0]
        
        # Check if the table covers the full data area
        region = table['region']
        expected_start_row = 1
        expected_end_row = 5
        expected_start_col = 1
        expected_end_col = 4
        
        # Verify table region covers the full expected area
        self.assertEqual(region['start_row'], expected_start_row, 
                        f"Expected start_row {expected_start_row}, got {region['start_row']}")
        self.assertEqual(region['end_row'], expected_end_row,
                        f"Expected end_row {expected_end_row}, got {region['end_row']}")
        self.assertEqual(region['start_col'], expected_start_col,
                        f"Expected start_col {expected_start_col}, got {region['start_col']}")
        self.assertEqual(region['end_col'], expected_end_col,
                        f"Expected end_col {expected_end_col}, got {region['end_col']}")
        
        # Check column and row counts
        expected_columns = expected_end_col - expected_start_col + 1
        expected_rows = expected_end_row - expected_start_row + 1
        actual_columns = len(table['columns'])
        actual_rows = len(table['rows'])
        
        self.assertEqual(actual_columns, expected_columns,
                        f"Expected {expected_columns} columns, got {actual_columns}")
        self.assertEqual(actual_rows, expected_rows,
                        f"Expected {expected_rows} rows, got {actual_rows}")
    
    def test_blank_header_labeling(self):
        """Test that blank headers are correctly labeled as 'unlabeled'"""
        # Test data with blank headers
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 3,
                        'min_col': 1,
                        'max_col': 3
                    },
                    'cells': {
                        # Row 1: Column headers (some blank)
                        'A1': {'value': 'Header1'},      # Valid column header
                        'B1': {'value': None},           # Blank column header
                        'C1': {'value': ''},             # Empty column header
                        
                        # Row 2: Row headers (some blank)
                        'A2': {'value': 'Row1'},         # Valid row header
                        'A3': {'value': None},           # Blank row header
                        
                        # Data cells
                        'B2': {'value': 'Data1'},
                        'C2': {'value': 'Data2'},
                        'B3': {'value': 'Data3'},
                        'C3': {'value': 'Data4'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.processor.transform_to_table_format(test_data)
        
        sheet = result['workbook']['sheets'][0]
        table = sheet['tables'][0]
        
        # Check column labels
        column_labels = [col.get('column_label', 'N/A') for col in table['columns']]
        self.assertIn('Header1', column_labels, "Valid column header not preserved")
        self.assertIn('unlabeled', column_labels, "Blank column header not labeled as 'unlabeled'")
        
        # Check row labels
        row_labels = [row.get('row_label', 'N/A') for row in table['rows']]
        self.assertIn('Row1', row_labels, "Valid row header not preserved")
        self.assertIn('unlabeled', row_labels, "Blank row header not labeled as 'unlabeled'")
    
    def test_single_cell_table(self):
        """Test table detection with minimal data (single cell)"""
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 1,
                        'min_col': 1,
                        'max_col': 1
                    },
                    'cells': {
                        'A1': {'value': 'Single Cell'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.processor.transform_to_table_format(test_data)
        
        sheet = result['workbook']['sheets'][0]
        self.assertGreater(len(sheet['tables']), 0, "Single cell table not detected")
        
        table = sheet['tables'][0]
        region = table['region']
        
        # Should detect the single cell as a table
        self.assertEqual(region['start_row'], 1)
        self.assertEqual(region['end_row'], 1)
        self.assertEqual(region['start_col'], 1)
        self.assertEqual(region['end_col'], 1)
        
        self.assertEqual(len(table['columns']), 1)
        self.assertEqual(len(table['rows']), 1)


def run_tests():
    """Run the test suite"""
    print("=== RUNNING TABLE DETECTION TESTS ===")
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests() 