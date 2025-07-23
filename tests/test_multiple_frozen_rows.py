#!/usr/bin/env python3
"""
Test script to verify multiple frozen rows handling for row labels
"""

import sys
import os
import unittest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.table_processor import TableProcessor


class TestMultipleFrozenRows(unittest.TestCase):
    """Test cases for multiple frozen rows functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.table_processor = TableProcessor()
    
    def test_multiple_frozen_rows_row_labels(self):
        """Test that row labels correctly concatenate values from multiple frozen rows"""
        # Test data with multiple frozen rows (2 frozen rows, 1 frozen column)
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
                    'frozen_panes': {
                        'frozen_rows': 2,
                        'frozen_cols': 1,
                        'top_left_cell': 'B3'
                    },
                    'cells': {
                        # Row 1: Year headers (frozen)
                        'A1': {'value': '2023'},
                        'B1': {'value': '2023'},
                        'C1': {'value': '2023'},
                        'D1': {'value': '2023'},
                        
                        # Row 2: Month headers (frozen)
                        'A2': {'value': 'Jan'},
                        'B2': {'value': 'Feb'},
                        'C2': {'value': 'Mar'},
                        'D2': {'value': 'Apr'},
                        
                        # Row 3: Data rows (not frozen)
                        'A3': {'value': 'Data1'},
                        'B3': {'value': 'Data2'},
                        'C3': {'value': 'Data3'},
                        'D3': {'value': 'Data4'},
                        
                        'A4': {'value': 'Data5'},
                        'B4': {'value': 'Data6'},
                        'C4': {'value': 'Data7'},
                        'D4': {'value': 'Data8'},
                        
                        'A5': {'value': 'Data9'},
                        'B5': {'value': 'Data10'},
                        'C5': {'value': 'Data11'},
                        'D5': {'value': 'Data12'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        # Verify that tables were created
        sheet = result['workbook']['sheets'][0]
        self.assertIn('tables', sheet)
        self.assertGreater(len(sheet['tables']), 0, "No tables created")
        
        table = sheet['tables'][0]
        
        # Verify header information includes frozen rows
        header_info = table['header_info']
        self.assertIn('header_rows', header_info)
        self.assertIn('header_columns', header_info)
        
        # Should have 2 header rows (frozen rows) and 1 header column (frozen column)
        self.assertEqual(len(header_info['header_rows']), 2, 
                        f"Expected 2 header rows, got {len(header_info['header_rows'])}")
        self.assertEqual(len(header_info['header_columns']), 1, 
                        f"Expected 1 header column, got {len(header_info['header_columns'])}")
        
        # Verify the header rows are correct (rows 1 and 2)
        self.assertIn(1, header_info['header_rows'], "Row 1 should be a header row")
        self.assertIn(2, header_info['header_rows'], "Row 2 should be a header row")
        
        # Verify the header column is correct (column 1)
        self.assertIn(1, header_info['header_columns'], "Column 1 should be a header column")
        
        # Check row labels - they should concatenate values from frozen rows
        rows = table['rows']
        self.assertGreater(len(rows), 0, "No rows created")
        
        # Row 3 should have label "Jan 2023" (from A2 + A1)
        row3 = next((row for row in rows if row['row_index'] == 3), None)
        self.assertIsNotNone(row3, "Row 3 not found")
        self.assertEqual(row3['row_label'], "Jan 2023", 
                        f"Expected 'Jan 2023', got '{row3['row_label']}'")
        
        # Row 4 should have label "Jan 2023" (from A2 + A1)
        row4 = next((row for row in rows if row['row_index'] == 4), None)
        self.assertIsNotNone(row4, "Row 4 not found")
        self.assertEqual(row4['row_label'], "Jan 2023", 
                        f"Expected 'Jan 2023', got '{row4['row_label']}'")
        
        # Row 5 should have label "Jan 2023" (from A2 + A1)
        row5 = next((row for row in rows if row['row_index'] == 5), None)
        self.assertIsNotNone(row5, "Row 5 not found")
        self.assertEqual(row5['row_label'], "Jan 2023", 
                        f"Expected 'Jan 2023', got '{row5['row_label']}'")
    
    def test_multiple_frozen_rows_different_values(self):
        """Test that row labels correctly handle different values in frozen rows"""
        # Test data with different values in frozen rows
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 4,
                        'min_col': 1,
                        'max_col': 3
                    },
                    'frozen_panes': {
                        'frozen_rows': 2,
                        'frozen_cols': 1,
                        'top_left_cell': 'B3'
                    },
                    'cells': {
                        # Row 1: Year headers (frozen)
                        'A1': {'value': '2023'},
                        'B1': {'value': '2024'},
                        'C1': {'value': '2025'},
                        
                        # Row 2: Month headers (frozen)
                        'A2': {'value': 'Jan'},
                        'B2': {'value': 'Feb'},
                        'C2': {'value': 'Mar'},
                        
                        # Row 3: Data rows (not frozen)
                        'A3': {'value': 'Data1'},
                        'B3': {'value': 'Data2'},
                        'C3': {'value': 'Data3'},
                        
                        'A4': {'value': 'Data4'},
                        'B4': {'value': 'Data5'},
                        'C4': {'value': 'Data6'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        sheet = result['workbook']['sheets'][0]
        table = sheet['tables'][0]
        rows = table['rows']
        
        # Check column labels - they should concatenate values from frozen rows
        columns = table['columns']
        self.assertGreater(len(columns), 0, "No columns created")
        
        # Column A should have label "Jan 2023" (from A2 + A1)
        col_a = next((col for col in columns if col['column_letter'] == 'A'), None)
        self.assertIsNotNone(col_a, "Column A not found")
        self.assertEqual(col_a['column_label'], "Jan 2023", 
                        f"Expected 'Jan 2023', got '{col_a['column_label']}'")
        
        # Column B should have label "Feb 2024" (from B2 + B1)
        col_b = next((col for col in columns if col['column_letter'] == 'B'), None)
        self.assertIsNotNone(col_b, "Column B not found")
        self.assertEqual(col_b['column_label'], "Feb 2024", 
                        f"Expected 'Feb 2024', got '{col_b['column_label']}'")
        
        # Column C should have label "Mar 2025" (from C2 + C1)
        col_c = next((col for col in columns if col['column_letter'] == 'C'), None)
        self.assertIsNotNone(col_c, "Column C not found")
        self.assertEqual(col_c['column_label'], "Mar 2025", 
                        f"Expected 'Mar 2025', got '{col_c['column_label']}'")
    
    def test_no_frozen_rows_fallback(self):
        """Test that the system falls back to original logic when no frozen rows"""
        # Test data with no frozen rows
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
                    'frozen_panes': {
                        'frozen_rows': 0,
                        'frozen_cols': 0,
                        'top_left_cell': None
                    },
                    'cells': {
                        'A1': {'value': 'Header1'},
                        'B1': {'value': 'Header2'},
                        'C1': {'value': 'Header3'},
                        
                        'A2': {'value': 'Data1'},
                        'B2': {'value': 'Data2'},
                        'C2': {'value': 'Data3'},
                        
                        'A3': {'value': 'Data4'},
                        'B3': {'value': 'Data5'},
                        'C3': {'value': 'Data6'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        sheet = result['workbook']['sheets'][0]
        table = sheet['tables'][0]
        
        # Should have 1 header row and 1 header column (original logic)
        header_info = table['header_info']
        self.assertEqual(len(header_info['header_rows']), 1, 
                        f"Expected 1 header row, got {len(header_info['header_rows'])}")
        self.assertEqual(len(header_info['header_columns']), 1, 
                        f"Expected 1 header column, got {len(header_info['header_columns'])}")
        
        # Row labels should use original logic (just the header column value)
        rows = table['rows']
        row2 = next((row for row in rows if row['row_index'] == 2), None)
        self.assertIsNotNone(row2, "Row 2 not found")
        self.assertEqual(row2['row_label'], "Data1", 
                        f"Expected 'Data1', got '{row2['row_label']}'")


def run_tests():
    """Run the test suite"""
    print("=== RUNNING MULTIPLE FROZEN ROWS TESTS ===")
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests() 