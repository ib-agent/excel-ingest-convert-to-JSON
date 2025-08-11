#!/usr/bin/env python3
"""
Test script to verify that sheets with frozen panes default to one table
and skip all other table detection methods
"""

import sys
import os
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.excel_processor import ExcelProcessor
from converter.table_processor import TableProcessor


class TestFrozenPanesTableDetection(unittest.TestCase):
    """Test cases for frozen panes table detection behavior"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.excel_processor = ExcelProcessor()
        self.table_processor = TableProcessor()
    
    def test_frozen_panes_override_other_detection(self):
        """Test that frozen panes override all other table detection methods"""
        # Create test data with frozen panes AND features that would trigger other detection
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet with Frozen Panes',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 20,
                        'min_col': 1,
                        'max_col': 8
                    },
                    'frozen_panes': {
                        'frozen_rows': 2,
                        'frozen_cols': 1,
                        'top_left_cell': 'B3'
                    },
                    'cells': {
                        # Header rows (frozen)
                        'A1': {'value': 'Main Header', 'style': {'font': {'bold': True}}},
                        'B1': {'value': 'Column A', 'style': {'font': {'bold': True}}},
                        'C1': {'value': 'Column B', 'style': {'font': {'bold': True}}},
                        'D1': {'value': 'Column C', 'style': {'font': {'bold': True}}},
                        'E1': {'value': 'Column D', 'style': {'font': {'bold': True}}},
                        'F1': {'value': 'Column E', 'style': {'font': {'bold': True}}},
                        'G1': {'value': 'Column F', 'style': {'font': {'bold': True}}},
                        'H1': {'value': 'Column G', 'style': {'font': {'bold': True}}},
                        
                        # Sub-header row (frozen)
                        'A2': {'value': 'Sub Header', 'style': {'font': {'bold': True}}},
                        'B2': {'value': 'Sub A', 'style': {'font': {'bold': True}}},
                        'C2': {'value': 'Sub B', 'style': {'font': {'bold': True}}},
                        'D2': {'value': 'Sub C', 'style': {'font': {'bold': True}}},
                        'E2': {'value': 'Sub D', 'style': {'font': {'bold': True}}},
                        'F2': {'value': 'Sub E', 'style': {'font': {'bold': True}}},
                        'G2': {'value': 'Sub F', 'style': {'font': {'bold': True}}},
                        'H2': {'value': 'Sub G', 'style': {'font': {'bold': True}}},
                        
                        # Data rows
                        'A3': {'value': 'Row 1'},
                        'B3': {'value': 'Data 1-1'},
                        'C3': {'value': 'Data 1-2'},
                        'D3': {'value': 'Data 1-3'},
                        'E3': {'value': 'Data 1-4'},
                        'F3': {'value': 'Data 1-5'},
                        'G3': {'value': 'Data 1-6'},
                        'H3': {'value': 'Data 1-7'},
                        
                        'A4': {'value': 'Row 2'},
                        'B4': {'value': 'Data 2-1'},
                        'C4': {'value': 'Data 2-2'},
                        'D4': {'value': 'Data 2-3'},
                        'E4': {'value': 'Data 2-4'},
                        'F4': {'value': 'Data 2-5'},
                        'G4': {'value': 'Data 2-6'},
                        'H4': {'value': 'Data 2-7'},
                        
                        'A5': {'value': 'Row 3'},
                        'B5': {'value': 'Data 3-1'},
                        'C5': {'value': 'Data 3-2'},
                        'D5': {'value': 'Data 3-3'},
                        'E5': {'value': 'Data 3-4'},
                        'F5': {'value': 'Data 3-5'},
                        'G5': {'value': 'Data 3-6'},
                        'H5': {'value': 'Data 3-7'},
                        
                        # LARGE GAP that would normally trigger table detection
                        # Rows 6-10 are completely empty
                        
                        # Second "table" that would be detected by gap detection
                        'A11': {'value': 'Second Table Header', 'style': {'font': {'bold': True}}},
                        'B11': {'value': 'ST Col A', 'style': {'font': {'bold': True}}},
                        'C11': {'value': 'ST Col B', 'style': {'font': {'bold': True}}},
                        'D11': {'value': 'ST Col C', 'style': {'font': {'bold': True}}},
                        
                        'A12': {'value': 'ST Row 1'},
                        'B12': {'value': 'ST Data 1-1'},
                        'C12': {'value': 'ST Data 1-2'},
                        'D12': {'value': 'ST Data 1-3'},
                        
                        'A13': {'value': 'ST Row 2'},
                        'B13': {'value': 'ST Data 2-1'},
                        'C13': {'value': 'ST Data 2-2'},
                        'D13': {'value': 'ST Data 2-3'},
                        
                        # Another gap
                        # Rows 14-15 are empty
                        
                        # Third "table" with different formatting
                        'A16': {'value': 'Third Table', 'style': {'fill': {'fill_type': 'solid'}}},
                        'B16': {'value': 'TT Col A', 'style': {'fill': {'fill_type': 'solid'}}},
                        'C16': {'value': 'TT Col B', 'style': {'fill': {'fill_type': 'solid'}}},
                        
                        'A17': {'value': 'TT Row 1'},
                        'B17': {'value': 'TT Data 1-1'},
                        'C17': {'value': 'TT Data 1-2'},
                        
                        'A18': {'value': 'TT Row 2'},
                        'B18': {'value': 'TT Data 2-1'},
                        'C18': {'value': 'TT Data 2-2'},
                        
                        # Data extending to the end
                        'A19': {'value': 'Final Row'},
                        'B19': {'value': 'Final Data 1'},
                        'C19': {'value': 'Final Data 2'},
                        'D19': {'value': 'Final Data 3'},
                        'E19': {'value': 'Final Data 4'},
                        'F19': {'value': 'Final Data 5'},
                        'G19': {'value': 'Final Data 6'},
                        'H19': {'value': 'Final Data 7'},
                        
                        'A20': {'value': 'Last Row'},
                        'B20': {'value': 'Last Data 1'},
                        'C20': {'value': 'Last Data 2'},
                        'D20': {'value': 'Last Data 3'},
                        'E20': {'value': 'Last Data 4'},
                        'F20': {'value': 'Last Data 5'},
                        'G20': {'value': 'Last Data 6'},
                        'H20': {'value': 'Last Data 7'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        # Verify that only ONE table is created due to frozen panes
        sheet = result['workbook']['sheets'][0]
        self.assertIn('tables', sheet)
        self.assertEqual(len(sheet['tables']), 1, 
                        "Should create exactly one table when frozen panes are present")
        
        # Verify the table detection method is 'frozen_panes'
        table = sheet['tables'][0]
        self.assertIn('metadata', table)
        self.assertEqual(table['metadata']['detection_method'], 'frozen_panes',
                        "Table should be detected using frozen_panes method")
        
        # Verify the table covers the entire sheet dimensions
        region = table['region']
        self.assertEqual(region['start_row'], 1, "Table should start at row 1")
        self.assertEqual(region['end_row'], 20, "Table should end at row 20")
        self.assertEqual(region['start_col'], 1, "Table should start at column 1")
        self.assertEqual(region['end_col'], 8, "Table should end at column 8")
        
        # Verify that frozen panes information is preserved in the region
        self.assertIn('frozen_rows', region)
        self.assertIn('frozen_cols', region)
        self.assertEqual(region['frozen_rows'], 2)
        self.assertEqual(region['frozen_cols'], 1)
        
        # Verify that all data is included in the single table
        # Check that data from all three "potential tables" is included
        table_cells = table.get('rows', [])
        self.assertGreater(len(table_cells), 0, "Table should contain rows")
        
        # Verify that the large gaps and multiple "tables" are all included in one table
        # This proves that gap detection was not used
        row_values = []
        for row in table_cells:
            if 'cells' in row:
                for cell_key, cell_data in row['cells'].items():
                    if 'value' in cell_data:
                        row_values.append(cell_data['value'])
        
        # Should contain data from all three "potential tables"
        self.assertIn('Row 1', row_values, "First table data should be included")
        self.assertIn('Second Table Header', row_values, "Second table data should be included")
        self.assertIn('Third Table', row_values, "Third table data should be included")
        self.assertIn('Final Row', row_values, "Final data should be included")
    
    def test_frozen_panes_only_rows(self):
        """Test that sheets with only frozen rows (no frozen columns) still default to one table"""
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet with Frozen Rows Only',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 15,
                        'min_col': 1,
                        'max_col': 5
                    },
                    'frozen_panes': {
                        'frozen_rows': 3,
                        'frozen_cols': 0,
                        'top_left_cell': 'A4'
                    },
                    'cells': {
                        # Header rows (frozen)
                        'A1': {'value': 'Header 1', 'style': {'font': {'bold': True}}},
                        'B1': {'value': 'Col A', 'style': {'font': {'bold': True}}},
                        'C1': {'value': 'Col B', 'style': {'font': {'bold': True}}},
                        'D1': {'value': 'Col C', 'style': {'font': {'bold': True}}},
                        'E1': {'value': 'Col D', 'style': {'font': {'bold': True}}},
                        
                        'A2': {'value': 'Header 2', 'style': {'font': {'bold': True}}},
                        'B2': {'value': 'Sub A', 'style': {'font': {'bold': True}}},
                        'C2': {'value': 'Sub B', 'style': {'font': {'bold': True}}},
                        'D2': {'value': 'Sub C', 'style': {'font': {'bold': True}}},
                        'E2': {'value': 'Sub D', 'style': {'font': {'bold': True}}},
                        
                        'A3': {'value': 'Header 3', 'style': {'font': {'bold': True}}},
                        'B3': {'value': 'SubSub A', 'style': {'font': {'bold': True}}},
                        'C3': {'value': 'SubSub B', 'style': {'font': {'bold': True}}},
                        'D3': {'value': 'SubSub C', 'style': {'font': {'bold': True}}},
                        'E3': {'value': 'SubSub D', 'style': {'font': {'bold': True}}},
                        
                        # Data with large gaps that would trigger detection
                        'A4': {'value': 'Data 1'},
                        'B4': {'value': 'Value 1-1'},
                        'C4': {'value': 'Value 1-2'},
                        'D4': {'value': 'Value 1-3'},
                        'E4': {'value': 'Value 1-4'},
                        
                        # Large gap (rows 5-8 empty)
                        
                        'A9': {'value': 'Second Section', 'style': {'fill': {'fill_type': 'solid'}}},
                        'B9': {'value': 'Sec 1', 'style': {'fill': {'fill_type': 'solid'}}},
                        'C9': {'value': 'Sec 2', 'style': {'fill': {'fill_type': 'solid'}}},
                        'D9': {'value': 'Sec 3', 'style': {'fill': {'fill_type': 'solid'}}},
                        'E9': {'value': 'Sec 4', 'style': {'fill': {'fill_type': 'solid'}}},
                        
                        'A10': {'value': 'Data 2'},
                        'B10': {'value': 'Value 2-1'},
                        'C10': {'value': 'Value 2-2'},
                        'D10': {'value': 'Value 2-3'},
                        'E10': {'value': 'Value 2-4'},
                        
                        # More data
                        'A11': {'value': 'Data 3'},
                        'B11': {'value': 'Value 3-1'},
                        'C11': {'value': 'Value 3-2'},
                        'D11': {'value': 'Value 3-3'},
                        'E11': {'value': 'Value 3-4'},
                        
                        'A12': {'value': 'Data 4'},
                        'B12': {'value': 'Value 4-1'},
                        'C12': {'value': 'Value 4-2'},
                        'D12': {'value': 'Value 4-3'},
                        'E12': {'value': 'Value 4-4'},
                        
                        'A13': {'value': 'Data 5'},
                        'B13': {'value': 'Value 5-1'},
                        'C13': {'value': 'Value 5-2'},
                        'D13': {'value': 'Value 5-3'},
                        'E13': {'value': 'Value 5-4'},
                        
                        'A14': {'value': 'Data 6'},
                        'B14': {'value': 'Value 6-1'},
                        'C14': {'value': 'Value 6-2'},
                        'D14': {'value': 'Value 6-3'},
                        'E14': {'value': 'Value 6-4'},
                        
                        'A15': {'value': 'Data 7'},
                        'B15': {'value': 'Value 7-1'},
                        'C15': {'value': 'Value 7-2'},
                        'D15': {'value': 'Value 7-3'},
                        'E15': {'value': 'Value 7-4'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        # Verify that only ONE table is created
        sheet = result['workbook']['sheets'][0]
        self.assertEqual(len(sheet['tables']), 1, 
                        "Should create exactly one table when frozen rows are present")
        
        # Verify the detection method
        table = sheet['tables'][0]
        self.assertEqual(table['metadata']['detection_method'], 'frozen_panes',
                        "Table should be detected using frozen_panes method")
        
        # Verify that all data is included (proving gap detection was not used)
        row_values = []
        for row in table.get('rows', []):
            if 'cells' in row:
                for cell_key, cell_data in row['cells'].items():
                    if 'value' in cell_data:
                        row_values.append(cell_data['value'])
        
        self.assertIn('Data 1', row_values, "First section data should be included")
        self.assertIn('Second Section', row_values, "Second section data should be included")
        self.assertIn('Data 7', row_values, "Last section data should be included")
    
    def test_frozen_panes_only_columns(self):
        """Test that sheets with only frozen columns (no frozen rows) still default to one table"""
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet with Frozen Columns Only',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 10,
                        'min_col': 1,
                        'max_col': 8
                    },
                    'frozen_panes': {
                        'frozen_rows': 0,
                        'frozen_cols': 2,
                        'top_left_cell': 'C1'
                    },
                    'cells': {
                        # Data with frozen columns and gaps that would trigger detection
                        'A1': {'value': 'Row Header 1', 'style': {'font': {'bold': True}}},
                        'B1': {'value': 'Row Header 2', 'style': {'font': {'bold': True}}},
                        'C1': {'value': 'Col A', 'style': {'font': {'bold': True}}},
                        'D1': {'value': 'Col B', 'style': {'font': {'bold': True}}},
                        'E1': {'value': 'Col C', 'style': {'font': {'bold': True}}},
                        'F1': {'value': 'Col D', 'style': {'font': {'bold': True}}},
                        'G1': {'value': 'Col E', 'style': {'font': {'bold': True}}},
                        'H1': {'value': 'Col F', 'style': {'font': {'bold': True}}},
                        
                        'A2': {'value': 'Item 1'},
                        'B2': {'value': 'SubItem 1'},
                        'C2': {'value': 'Data 1-1'},
                        'D2': {'value': 'Data 1-2'},
                        'E2': {'value': 'Data 1-3'},
                        'F2': {'value': 'Data 1-4'},
                        'G2': {'value': 'Data 1-5'},
                        'H2': {'value': 'Data 1-6'},
                        
                        'A3': {'value': 'Item 2'},
                        'B3': {'value': 'SubItem 2'},
                        'C3': {'value': 'Data 2-1'},
                        'D3': {'value': 'Data 2-2'},
                        'E3': {'value': 'Data 2-3'},
                        'F3': {'value': 'Data 2-4'},
                        'G3': {'value': 'Data 2-5'},
                        'H3': {'value': 'Data 2-6'},
                        
                        # Large gap (rows 4-6 empty)
                        
                        'A7': {'value': 'Second Section', 'style': {'fill': {'fill_type': 'solid'}}},
                        'B7': {'value': 'Sec Header', 'style': {'fill': {'fill_type': 'solid'}}},
                        'C7': {'value': 'Sec Data 1', 'style': {'fill': {'fill_type': 'solid'}}},
                        'D7': {'value': 'Sec Data 2', 'style': {'fill': {'fill_type': 'solid'}}},
                        'E7': {'value': 'Sec Data 3', 'style': {'fill': {'fill_type': 'solid'}}},
                        'F7': {'value': 'Sec Data 4', 'style': {'fill': {'fill_type': 'solid'}}},
                        'G7': {'value': 'Sec Data 5', 'style': {'fill': {'fill_type': 'solid'}}},
                        'H7': {'value': 'Sec Data 6', 'style': {'fill': {'fill_type': 'solid'}}},
                        
                        'A8': {'value': 'Item 3'},
                        'B8': {'value': 'SubItem 3'},
                        'C8': {'value': 'Data 3-1'},
                        'D8': {'value': 'Data 3-2'},
                        'E8': {'value': 'Data 3-3'},
                        'F8': {'value': 'Data 3-4'},
                        'G8': {'value': 'Data 3-5'},
                        'H8': {'value': 'Data 3-6'},
                        
                        'A9': {'value': 'Item 4'},
                        'B9': {'value': 'SubItem 4'},
                        'C9': {'value': 'Data 4-1'},
                        'D9': {'value': 'Data 4-2'},
                        'E9': {'value': 'Data 4-3'},
                        'F9': {'value': 'Data 4-4'},
                        'G9': {'value': 'Data 4-5'},
                        'H9': {'value': 'Data 4-6'},
                        
                        'A10': {'value': 'Item 5'},
                        'B10': {'value': 'SubItem 5'},
                        'C10': {'value': 'Data 5-1'},
                        'D10': {'value': 'Data 5-2'},
                        'E10': {'value': 'Data 5-3'},
                        'F10': {'value': 'Data 5-4'},
                        'G10': {'value': 'Data 5-5'},
                        'H10': {'value': 'Data 5-6'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        # Verify that only ONE table is created
        sheet = result['workbook']['sheets'][0]
        self.assertEqual(len(sheet['tables']), 1, 
                        "Should create exactly one table when frozen columns are present")
        
        # Verify the detection method
        table = sheet['tables'][0]
        self.assertEqual(table['metadata']['detection_method'], 'frozen_panes',
                        "Table should be detected using frozen_panes method")
        
        # Verify that all data is included (proving gap detection was not used)
        row_values = []
        for row in table.get('rows', []):
            if 'cells' in row:
                for cell_key, cell_data in row['cells'].items():
                    if 'value' in cell_data:
                        row_values.append(cell_data['value'])
        
        self.assertIn('Item 1', row_values, "First section data should be included")
        self.assertIn('Second Section', row_values, "Second section data should be included")
        self.assertIn('Item 5', row_values, "Last section data should be included")
    
    def test_no_frozen_panes_uses_other_detection(self):
        """Test that sheets without frozen panes use other detection methods"""
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Test Sheet without Frozen Panes',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 15,
                        'min_col': 1,
                        'max_col': 5
                    },
                    'frozen_panes': {
                        'frozen_rows': 0,
                        'frozen_cols': 0,
                        'top_left_cell': None
                    },
                    'cells': {
                        # First table
                        'A1': {'value': 'Table 1 Header', 'style': {'font': {'bold': True}}},
                        'B1': {'value': 'Col A', 'style': {'font': {'bold': True}}},
                        'C1': {'value': 'Col B', 'style': {'font': {'bold': True}}},
                        'D1': {'value': 'Col C', 'style': {'font': {'bold': True}}},
                        'E1': {'value': 'Col D', 'style': {'font': {'bold': True}}},
                        
                        'A2': {'value': 'Row 1'},
                        'B2': {'value': 'Data 1-1'},
                        'C2': {'value': 'Data 1-2'},
                        'D2': {'value': 'Data 1-3'},
                        'E2': {'value': 'Data 1-4'},
                        
                        'A3': {'value': 'Row 2'},
                        'B3': {'value': 'Data 2-1'},
                        'C3': {'value': 'Data 2-2'},
                        'D3': {'value': 'Data 2-3'},
                        'E3': {'value': 'Data 2-4'},
                        
                        # Large gap (rows 4-8 empty)
                        
                        # Second table
                        'A9': {'value': 'Table 2 Header', 'style': {'fill': {'fill_type': 'solid'}}},
                        'B9': {'value': 'T2 Col A', 'style': {'fill': {'fill_type': 'solid'}}},
                        'C9': {'value': 'T2 Col B', 'style': {'fill': {'fill_type': 'solid'}}},
                        'D9': {'value': 'T2 Col C', 'style': {'fill': {'fill_type': 'solid'}}},
                        'E9': {'value': 'T2 Col D', 'style': {'fill': {'fill_type': 'solid'}}},
                        
                        'A10': {'value': 'T2 Row 1'},
                        'B10': {'value': 'T2 Data 1-1'},
                        'C10': {'value': 'T2 Data 1-2'},
                        'D10': {'value': 'T2 Data 1-3'},
                        'E10': {'value': 'T2 Data 1-4'},
                        
                        'A11': {'value': 'T2 Row 2'},
                        'B11': {'value': 'T2 Data 2-1'},
                        'C11': {'value': 'T2 Data 2-2'},
                        'D11': {'value': 'T2 Data 2-3'},
                        'E11': {'value': 'T2 Data 2-4'},
                        
                        # Another gap (rows 12-13 empty)
                        
                        # Third table
                        'A14': {'value': 'Table 3 Header'},
                        'B14': {'value': 'T3 Col A'},
                        'C14': {'value': 'T3 Col B'},
                        'D14': {'value': 'T3 Col C'},
                        'E14': {'value': 'T3 Col D'},
                        
                        'A15': {'value': 'T3 Row 1'},
                        'B15': {'value': 'T3 Data 1-1'},
                        'C15': {'value': 'T3 Data 1-2'},
                        'D15': {'value': 'T3 Data 1-3'},
                        'E15': {'value': 'T3 Data 1-4'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data
        result = self.table_processor.transform_to_table_format(test_data)
        
        # Verify that multiple tables are created (since no frozen panes)
        sheet = result['workbook']['sheets'][0]
        self.assertGreater(len(sheet['tables']), 1, 
                          "Should create multiple tables when no frozen panes are present")
        
        # Verify that the detection method is NOT 'frozen_panes'
        for table in sheet['tables']:
            self.assertNotEqual(table['metadata']['detection_method'], 'frozen_panes',
                              "Table should not be detected using frozen_panes method when no frozen panes exist")


def run_tests():
    """Run the test suite"""
    print("=== RUNNING FROZEN PANES TABLE DETECTION TESTS ===")
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests() 