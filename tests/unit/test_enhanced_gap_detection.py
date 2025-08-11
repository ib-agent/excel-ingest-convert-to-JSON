#!/usr/bin/env python3
"""
Test script to verify enhanced gap detection that only starts new tables
when the first row after a gap contains non-numerical content
"""

import sys
import os
import unittest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.table_processor import TableProcessor


class TestEnhancedGapDetection(unittest.TestCase):
    """Test cases for enhanced gap detection functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.table_processor = TableProcessor()
    
    def test_gap_with_numerical_content_continues_table(self):
        """Test that gaps followed by numerical content continue the same table"""
        # Create test data with a gap followed by numerical content
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 10,
                        'min_col': 1,
                        'max_col': 4
                    },
                    'frozen_panes': {
                        'frozen_rows': 0,
                        'frozen_cols': 0,
                        'top_left_cell': None
                    },
                    'cells': {
                        # First table section with headers
                        'A1': {'value': 'Product'},
                        'B1': {'value': 'Q1'},
                        'C1': {'value': 'Q2'},
                        'D1': {'value': 'Q3'},
                        
                        # First data row
                        'A2': {'value': 'Widget A'},
                        'B2': {'value': 100},
                        'C2': {'value': 150},
                        'D2': {'value': 200},
                        
                        'A3': {'value': 'Widget B'},
                        'B3': {'value': 250},
                        'C3': {'value': 300},
                        'D3': {'value': 350},
                        
                        # Gap (rows 4-5 empty)
                        
                        # PURELY NUMERICAL content after gap (should continue same table)
                        'A6': {'value': 400},
                        'B6': {'value': 450},
                        'C6': {'value': 500},
                        'D6': {'value': 550},
                        
                        'A7': {'value': 600},
                        'B7': {'value': 650},
                        'C7': {'value': 700},
                        'D7': {'value': 750},
                        
                        # Another gap (rows 8-9 empty)
                        
                        # More purely numerical content (should continue same table)
                        'A10': {'value': 800},
                        'B10': {'value': 850},
                        'C10': {'value': 900},
                        'D10': {'value': 950}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        # Verify that only ONE table is created (numerical content after gaps continues the table)
        sheet = result['workbook']['sheets'][0]
        self.assertEqual(len(sheet['tables']), 1, 
                        "Should create exactly one table when gaps are followed by numerical content")
        
        # Verify the table covers the entire data area
        table = sheet['tables'][0]
        region = table['region']
        self.assertEqual(region['start_row'], 1, "Table should start at row 1")
        self.assertEqual(region['end_row'], 10, "Table should end at row 10")
        
        # Verify that all data is included in the single table
        rows = table.get('rows', [])
        row_values = []
        for row in rows:
            if 'cells' in row:
                for cell_key, cell_data in row['cells'].items():
                    if 'value' in cell_data:
                        row_values.append(cell_data['value'])
        
        # Should contain data from all sections
        self.assertIn('Product', row_values, "Header should be included")
        self.assertIn('Widget A', row_values, "First section data should be included")
        self.assertIn(400, row_values, "Second section numerical data should be included")
        self.assertIn(800, row_values, "Third section numerical data should be included")
    
    def test_gap_with_date_content_starts_new_table(self):
        """Test that gaps followed by date content start a new table"""
        # Create test data with a gap followed by date content
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 12,
                        'min_col': 1,
                        'max_col': 4
                    },
                    'frozen_panes': {
                        'frozen_rows': 0,
                        'frozen_cols': 0,
                        'top_left_cell': None
                    },
                    'cells': {
                        # First table section
                        'A1': {'value': 'Product'},
                        'B1': {'value': 'Q1'},
                        'C1': {'value': 'Q2'},
                        'D1': {'value': 'Q3'},
                        
                        'A2': {'value': 'Widget A'},
                        'B2': {'value': 100},
                        'C2': {'value': 150},
                        'D2': {'value': 200},
                        
                        'A3': {'value': 'Widget B'},
                        'B3': {'value': 250},
                        'C3': {'value': 300},
                        'D3': {'value': 350},
                        
                        # Gap (rows 4-5 empty)
                        
                        # Date content after gap (should start new table)
                        'A6': {'value': 'Q1 2024'},
                        'B6': {'value': 'Jan 2024'},
                        'C6': {'value': 'Feb 2024'},
                        'D6': {'value': 'Mar 2024'},
                        
                        'A7': {'value': 'Widget C'},
                        'B7': {'value': 400},
                        'C7': {'value': 450},
                        'D7': {'value': 500},
                        
                        'A8': {'value': 'Widget D'},
                        'B8': {'value': 550},
                        'C8': {'value': 600},
                        'D8': {'value': 650},
                        
                        # Another gap (rows 9-10 empty)
                        
                        # More date content (should start another new table)
                        'A11': {'value': 'Q2 2024'},
                        'B11': {'value': 'Apr 2024'},
                        'C11': {'value': 'May 2024'},
                        'D11': {'value': 'Jun 2024'},
                        
                        'A12': {'value': 'Widget E'},
                        'B12': {'value': 700},
                        'C12': {'value': 750},
                        'D12': {'value': 800}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        # Verify that THREE tables are created (date content after gaps starts new tables)
        sheet = result['workbook']['sheets'][0]
        self.assertEqual(len(sheet['tables']), 3, 
                        "Should create three tables when gaps are followed by date content")
        
        # Verify the tables have correct regions
        tables = sheet['tables']
        
        # First table should end before the gap
        self.assertEqual(tables[0]['region']['start_row'], 1, "First table should start at row 1")
        self.assertEqual(tables[0]['region']['end_row'], 3, "First table should end at row 3")
        
        # Second table should start after the gap with date content
        self.assertEqual(tables[1]['region']['start_row'], 6, "Second table should start at row 6")
        self.assertEqual(tables[1]['region']['end_row'], 8, "Second table should end at row 8")
        
        # Third table should start after the second gap with date content
        self.assertEqual(tables[2]['region']['start_row'], 11, "Third table should start at row 11")
        self.assertEqual(tables[2]['region']['end_row'], 12, "Third table should end at row 12")
    
    def test_gap_with_text_label_starts_new_table(self):
        """Test that gaps followed by text labels start a new table"""
        # Create test data with a gap followed by text labels
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 10,
                        'min_col': 1,
                        'max_col': 4
                    },
                    'frozen_panes': {
                        'frozen_rows': 0,
                        'frozen_cols': 0,
                        'top_left_cell': None
                    },
                    'cells': {
                        # First table section
                        'A1': {'value': 'Product'},
                        'B1': {'value': 'Q1'},
                        'C1': {'value': 'Q2'},
                        'D1': {'value': 'Q3'},
                        
                        'A2': {'value': 'Widget A'},
                        'B2': {'value': 100},
                        'C2': {'value': 150},
                        'D2': {'value': 200},
                        
                        # Gap (rows 3-4 empty)
                        
                        # Text label after gap (should start new table)
                        'A5': {'value': 'Revenue Summary'},
                        'B5': {'value': 'Total'},
                        'C5': {'value': 'Average'},
                        'D5': {'value': 'Growth'},
                        
                        'A6': {'value': 'Q1 Revenue'},
                        'B6': {'value': 1000},
                        'C6': {'value': 500},
                        'D6': {'value': 15.5},
                        
                        'A7': {'value': 'Q2 Revenue'},
                        'B7': {'value': 1200},
                        'C7': {'value': 600},
                        'D7': {'value': 20.0},
                        
                        # Another gap (rows 8-9 empty)
                        
                        # Another text label (should start another new table)
                        'A10': {'value': 'Performance Metrics'},
                        'B10': {'value': 'Target'},
                        'C10': {'value': 'Actual'},
                        'D10': {'value': 'Variance'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        # Verify that THREE tables are created (text labels after gaps start new tables)
        sheet = result['workbook']['sheets'][0]
        self.assertEqual(len(sheet['tables']), 3, 
                        "Should create three tables when gaps are followed by text labels")
        
        # Verify the tables have correct regions
        tables = sheet['tables']
        
        # First table should end before the gap
        self.assertEqual(tables[0]['region']['start_row'], 1, "First table should start at row 1")
        self.assertEqual(tables[0]['region']['end_row'], 2, "First table should end at row 2")
        
        # Second table should start after the gap with text label
        self.assertEqual(tables[1]['region']['start_row'], 5, "Second table should start at row 5")
        self.assertEqual(tables[1]['region']['end_row'], 7, "Second table should end at row 7")
        
        # Third table should start after the second gap with text label
        self.assertEqual(tables[2]['region']['start_row'], 10, "Third table should start at row 10")
        self.assertEqual(tables[2]['region']['end_row'], 10, "Third table should end at row 10")
    
    def test_mixed_content_after_gap(self):
        """Test that gaps followed by mixed content (some numerical, some text) start new tables"""
        # Create test data with a gap followed by mixed content
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 8,
                        'min_col': 1,
                        'max_col': 4
                    },
                    'frozen_panes': {
                        'frozen_rows': 0,
                        'frozen_cols': 0,
                        'top_left_cell': None
                    },
                    'cells': {
                        # First table section
                        'A1': {'value': 'Product'},
                        'B1': {'value': 'Q1'},
                        'C1': {'value': 'Q2'},
                        'D1': {'value': 'Q3'},
                        
                        'A2': {'value': 'Widget A'},
                        'B2': {'value': 100},
                        'C2': {'value': 150},
                        'D2': {'value': 200},
                        
                        # Gap (rows 3-4 empty)
                        
                        # Mixed content after gap (text + numbers should start new table)
                        'A5': {'value': 'Q1 2024'},
                        'B5': {'value': 1000},
                        'C5': {'value': 1500},
                        'D5': {'value': 2000},
                        
                        'A6': {'value': 'Widget B'},
                        'B6': {'value': 2500},
                        'C6': {'value': 3000},
                        'D6': {'value': 3500}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        # Verify that TWO tables are created (mixed content after gap starts new table)
        sheet = result['workbook']['sheets'][0]
        self.assertEqual(len(sheet['tables']), 2, 
                        "Should create two tables when gap is followed by mixed content")
        
        # Verify the tables have correct regions
        tables = sheet['tables']
        
        # First table should end before the gap
        self.assertEqual(tables[0]['region']['start_row'], 1, "First table should start at row 1")
        self.assertEqual(tables[0]['region']['end_row'], 2, "First table should end at row 2")
        
        # Second table should start after the gap with mixed content
        self.assertEqual(tables[1]['region']['start_row'], 5, "Second table should start at row 5")
        self.assertEqual(tables[1]['region']['end_row'], 8, "Second table should end at row 8 (max_row)")


def run_tests():
    """Run the test suite"""
    print("=== RUNNING ENHANCED GAP DETECTION TESTS ===")
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests() 