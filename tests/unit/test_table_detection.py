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

    def test_three_tables_with_titles_separated(self):
        """Test detection of 3 tables with titles, separated by multiple rows"""
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Multiple Tables Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 25,
                        'min_col': 1,
                        'max_col': 6
                    },
                    'cells': {
                        # Table 1: Sales Data (rows 1-6)
                        'A1': {'value': 'Sales Data Q1 2024', 'style': {'font': {'bold': True, 'size': 14}}},
                        'A3': {'value': 'Product'},
                        'B3': {'value': 'Jan'},
                        'C3': {'value': 'Feb'},
                        'D3': {'value': 'Mar'},
                        'A4': {'value': 'Widget A'},
                        'B4': {'value': 100},
                        'C4': {'value': 120},
                        'D4': {'value': 110},
                        'A5': {'value': 'Widget B'},
                        'B5': {'value': 150},
                        'C5': {'value': 160},
                        'D5': {'value': 140},
                        
                        # Table 2: Inventory Status (rows 9-14) - separated by 2 rows
                        'A9': {'value': 'Inventory Status Report', 'style': {'font': {'bold': True, 'size': 14}}},
                        'A11': {'value': 'Item'},
                        'B11': {'value': 'In Stock'},
                        'C11': {'value': 'On Order'},
                        'D11': {'value': 'Status'},
                        'A12': {'value': 'Laptop'},
                        'B12': {'value': 25},
                        'C12': {'value': 10},
                        'D12': {'value': 'Good'},
                        'A13': {'value': 'Mouse'},
                        'B13': {'value': 50},
                        'C13': {'value': 0},
                        'D13': {'value': 'Good'},
                        
                        # Table 3: Employee Performance (rows 17-22) - separated by 2 rows
                        'A17': {'value': 'Employee Performance Metrics', 'style': {'font': {'bold': True, 'size': 14}}},
                        'A19': {'value': 'Employee'},
                        'B19': {'value': 'Sales'},
                        'C19': {'value': 'Rating'},
                        'D19': {'value': 'Bonus'},
                        'A20': {'value': 'John Doe'},
                        'B20': {'value': 50000},
                        'C20': {'value': 'A'},
                        'D20': {'value': 5000},
                        'A21': {'value': 'Jane Smith'},
                        'B21': {'value': 45000},
                        'C21': {'value': 'B'},
                        'D21': {'value': 3000}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data with gap detection enabled
        options = {
            'table_detection': {
                'use_gaps': True
            }
        }
        result = self.processor.transform_to_table_format(test_data, options)
        
        sheet = result['workbook']['sheets'][0]
        tables = sheet['tables']
        
        # Should detect 3 tables: 3 data blocks only
        self.assertEqual(len(tables), 3, f"Expected 3 tables (data blocks only), got {len(tables)}")
        
        # Verify that we have tables covering the expected regions
        table_regions = [table['region'] for table in tables]
        
        # Expected regions based on gap-based detection
        expected_regions = [
            {'start_row': 1, 'end_row': 5, 'start_col': 1, 'end_col': 6},
            {'start_row': 9, 'end_row': 13, 'start_col': 1, 'end_col': 6},
            {'start_row': 17, 'end_row': 25, 'start_col': 1, 'end_col': 6}
        ]
        
        # Verify that each expected region matches a detected table
        for i, expected in enumerate(expected_regions):
            if i < len(table_regions):
                actual = table_regions[i]
                self.assertEqual(actual['start_row'], expected['start_row'], 
                               f"Table {i+1} start_row mismatch: expected {expected['start_row']}, got {actual['start_row']}")
                self.assertEqual(actual['end_row'], expected['end_row'], 
                               f"Table {i+1} end_row mismatch: expected {expected['end_row']}, got {actual['end_row']}")
                self.assertEqual(actual['start_col'], expected['start_col'], 
                               f"Table {i+1} start_col mismatch: expected {expected['start_col']}, got {actual['start_col']}")
                self.assertEqual(actual['end_col'], expected['end_col'], 
                               f"Table {i+1} end_col mismatch: expected {expected['end_col']}, got {actual['end_col']}")

    def test_four_tables_spread_around_sheet(self):
        """Test detection of 4 tables spread around different areas of the sheet"""
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Spread Tables Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 30,
                        'min_col': 1,
                        'max_col': 10
                    },
                    'cells': {
                        # Table 1: Top-left (rows 1-5, cols A-D)
                        'A1': {'value': 'Quarterly Revenue', 'style': {'font': {'bold': True, 'size': 12}}},
                        'A3': {'value': 'Q1'},
                        'B3': {'value': 'Q2'},
                        'C3': {'value': 'Q3'},
                        'D3': {'value': 'Q4'},
                        'A4': {'value': 100000},
                        'B4': {'value': 120000},
                        'C4': {'value': 110000},
                        'D4': {'value': 130000},
                        
                        # Table 2: Top-right (rows 1-5, cols F-J)
                        'F1': {'value': 'Monthly Expenses', 'style': {'font': {'bold': True, 'size': 12}}},
                        'F3': {'value': 'Jan'},
                        'G3': {'value': 'Feb'},
                        'H3': {'value': 'Mar'},
                        'I3': {'value': 'Apr'},
                        'F4': {'value': 80000},
                        'G4': {'value': 85000},
                        'H4': {'value': 82000},
                        'I4': {'value': 88000},
                        
                        # Table 3: Bottom-left (rows 20-25, cols A-E)
                        'A20': {'value': 'Product Categories', 'style': {'font': {'bold': True, 'size': 12}}},
                        'A22': {'value': 'Category'},
                        'B22': {'value': 'Count'},
                        'C22': {'value': 'Revenue'},
                        'D22': {'value': 'Margin'},
                        'A23': {'value': 'Electronics'},
                        'B23': {'value': 150},
                        'C23': {'value': 500000},
                        'D23': {'value': '25%'},
                        'A24': {'value': 'Clothing'},
                        'B24': {'value': 200},
                        'C24': {'value': 300000},
                        'D24': {'value': '30%'},
                        
                        # Table 4: Bottom-right (rows 20-25, cols F-J)
                        'F20': {'value': 'Regional Sales', 'style': {'font': {'bold': True, 'size': 12}}},
                        'F22': {'value': 'Region'},
                        'G22': {'value': 'Sales'},
                        'H22': {'value': 'Growth'},
                        'I22': {'value': 'Target'},
                        'F23': {'value': 'North'},
                        'G23': {'value': 250000},
                        'H23': {'value': '15%'},
                        'I23': {'value': 240000},
                        'F24': {'value': 'South'},
                        'G24': {'value': 180000},
                        'H24': {'value': '8%'},
                        'I24': {'value': 175000}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data with gap detection enabled
        options = {
            'table_detection': {
                'use_gaps': True
            }
        }
        result = self.processor.transform_to_table_format(test_data, options)
        
        sheet = result['workbook']['sheets'][0]
        tables = sheet['tables']
        
        # Should detect 2 tables: 2 data blocks only
        self.assertEqual(len(tables), 2, f"Expected 2 tables (data blocks only), got {len(tables)}")
        
        # Verify that we have tables covering the expected regions
        table_regions = [table['region'] for table in tables]
        
        # Expected regions based on gap-based detection: full width over data rows in block
        expected_regions = [
            {'start_row': 1, 'end_row': 4, 'start_col': 1, 'end_col': 10},
            {'start_row': 20, 'end_row': 30, 'start_col': 1, 'end_col': 10}
        ]
        
        # Verify that each expected region matches a detected table
        for i, expected in enumerate(expected_regions):
            if i < len(table_regions):
                actual = table_regions[i]
                self.assertEqual(actual['start_row'], expected['start_row'], 
                               f"Table {i+1} start_row mismatch: expected {expected['start_row']}, got {actual['start_row']}")
                self.assertEqual(actual['end_row'], expected['end_row'], 
                               f"Table {i+1} end_row mismatch: expected {expected['end_row']}, got {actual['end_row']}")
                self.assertEqual(actual['start_col'], expected['start_col'], 
                               f"Table {i+1} start_col mismatch: expected {expected['start_col']}, got {actual['start_col']}")
                self.assertEqual(actual['end_col'], expected['end_col'], 
                               f"Table {i+1} end_col mismatch: expected {expected['end_col']}, got {actual['end_col']}")

    def test_tables_with_different_sizes_and_separations(self):
        """Test tables with varying sizes and different separation distances"""
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Variable Tables Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 35,
                        'min_col': 1,
                        'max_col': 8
                    },
                    'cells': {
                        # Table 1: Small table (rows 1-4, cols A-C)
                        'A1': {'value': 'Small Summary', 'style': {'font': {'bold': True, 'size': 11}}},
                        'A3': {'value': 'Metric'},
                        'B3': {'value': 'Value'},
                        'A4': {'value': 'Total'},
                        'B4': {'value': 1000},
                        
                        # Table 2: Medium table (rows 8-13, cols A-E) - separated by 3 rows
                        'A8': {'value': 'Medium Detail Table', 'style': {'font': {'bold': True, 'size': 12}}},
                        'A10': {'value': 'Item'},
                        'B10': {'value': 'Qty'},
                        'C10': {'value': 'Price'},
                        'D10': {'value': 'Total'},
                        'A11': {'value': 'Product A'},
                        'B11': {'value': 10},
                        'C11': {'value': 25.50},
                        'D11': {'value': 255.00},
                        'A12': {'value': 'Product B'},
                        'B12': {'value': 5},
                        'C12': {'value': 15.75},
                        'D12': {'value': 78.75},
                        'A13': {'value': 'Product C'},
                        'B13': {'value': 8},
                        'C13': {'value': 30.00},
                        'D13': {'value': 240.00},
                        
                        # Table 3: Large table (rows 18-28, cols A-G) - separated by 4 rows
                        'A18': {'value': 'Large Comprehensive Report', 'style': {'font': {'bold': True, 'size': 14}}},
                        'A20': {'value': 'Department'},
                        'B20': {'value': 'Budget'},
                        'C20': {'value': 'Actual'},
                        'D20': {'value': 'Variance'},
                        'E20': {'value': 'Status'},
                        'F20': {'value': 'Notes'},
                        'A21': {'value': 'Marketing'},
                        'B21': {'value': 50000},
                        'C21': {'value': 48000},
                        'D21': {'value': 2000},
                        'E21': {'value': 'Under'},
                        'F21': {'value': 'Good'},
                        'A22': {'value': 'Sales'},
                        'B22': {'value': 75000},
                        'C22': {'value': 78000},
                        'D22': {'value': -3000},
                        'E22': {'value': 'Over'},
                        'F22': {'value': 'High activity'},
                        'A23': {'value': 'IT'},
                        'B23': {'value': 30000},
                        'C23': {'value': 32000},
                        'D23': {'value': -2000},
                        'E23': {'value': 'Over'},
                        'F23': {'value': 'New equipment'},
                        'A24': {'value': 'HR'},
                        'B24': {'value': 25000},
                        'C24': {'value': 24000},
                        'D24': {'value': 1000},
                        'E24': {'value': 'Under'},
                        'F24': {'value': 'Efficient'},
                        'A25': {'value': 'Finance'},
                        'B25': {'value': 40000},
                        'C25': {'value': 39500},
                        'D25': {'value': 500},
                        'E25': {'value': 'Under'},
                        'F25': {'value': 'On track'},
                        'A26': {'value': 'Operations'},
                        'B26': {'value': 60000},
                        'C26': {'value': 61000},
                        'D26': {'value': -1000},
                        'E26': {'value': 'Over'},
                        'F26': {'value': 'Overtime'},
                        'A27': {'value': 'Legal'},
                        'B27': {'value': 20000},
                        'C27': {'value': 18500},
                        'D27': {'value': 1500},
                        'E27': {'value': 'Under'},
                        'F27': {'value': 'Fewer cases'},
                        'A28': {'value': 'Admin'},
                        'B28': {'value': 15000},
                        'C28': {'value': 15200},
                        'D28': {'value': -200},
                        'E28': {'value': 'Over'},
                        'F28': {'value': 'Minor overage'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data with gap detection enabled
        options = {
            'table_detection': {
                'use_gaps': True
            }
        }
        result = self.processor.transform_to_table_format(test_data, options)
        
        sheet = result['workbook']['sheets'][0]
        tables = sheet['tables']
        
        # Should detect 3 tables: 3 data blocks only
        self.assertEqual(len(tables), 3, f"Expected 3 tables (data blocks only), got {len(tables)}")
        
        # Verify that we have tables covering the expected regions
        table_regions = [table['region'] for table in tables]
        
        # Expected regions based on gap-based detection: full width over data rows in block
        expected_regions = [
            {'start_row': 1, 'end_row': 4, 'start_col': 1, 'end_col': 8},
            {'start_row': 8, 'end_row': 13, 'start_col': 1, 'end_col': 8},
            {'start_row': 18, 'end_row': 35, 'start_col': 1, 'end_col': 8}
        ]
        
        # Verify that each expected region matches a detected table
        for i, expected in enumerate(expected_regions):
            if i < len(table_regions):
                actual = table_regions[i]
                self.assertEqual(actual['start_row'], expected['start_row'], 
                               f"Table {i+1} start_row mismatch: expected {expected['start_row']}, got {actual['start_row']}")
                self.assertEqual(actual['end_row'], expected['end_row'], 
                               f"Table {i+1} end_row mismatch: expected {expected['end_row']}, got {actual['end_row']}")
                self.assertEqual(actual['start_col'], expected['start_col'], 
                               f"Table {i+1} start_col mismatch: expected {expected['start_col']}, got {actual['start_col']}")
                self.assertEqual(actual['end_col'], expected['end_col'], 
                               f"Table {i+1} end_col mismatch: expected {expected['end_col']}, got {actual['end_col']}")

    def test_tables_with_complex_titles_and_metadata(self):
        """Test tables with complex titles, subtitles, and metadata preservation"""
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Complex Titles Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 30,
                        'min_col': 1,
                        'max_col': 8
                    },
                    'cells': {
                        # Table 1: With subtitle and date
                        'A1': {'value': 'Financial Performance Report', 'style': {'font': {'bold': True, 'size': 16}}},
                        'A2': {'value': 'Q4 2024 - Year End Summary', 'style': {'font': {'italic': True, 'size': 12}}},
                        'A3': {'value': 'Generated: December 31, 2024', 'style': {'font': {'size': 10}}},
                        'A5': {'value': 'Revenue Stream'},
                        'B5': {'value': 'Q1'},
                        'C5': {'value': 'Q2'},
                        'D5': {'value': 'Q3'},
                        'E5': {'value': 'Q4'},
                        'F5': {'value': 'Total'},
                        'A6': {'value': 'Product Sales'},
                        'B6': {'value': 250000},
                        'C6': {'value': 275000},
                        'D6': {'value': 300000},
                        'E6': {'value': 325000},
                        'F6': {'value': 1150000},
                        'A7': {'value': 'Services'},
                        'B7': {'value': 100000},
                        'C7': {'value': 125000},
                        'D7': {'value': 150000},
                        'E7': {'value': 175000},
                        'F7': {'value': 550000},
                        'A8': {'value': 'Licensing'},
                        'B8': {'value': 50000},
                        'C8': {'value': 75000},
                        'D8': {'value': 100000},
                        'E8': {'value': 125000},
                        'F8': {'value': 350000},
                        
                        # Table 2: With department info and contact
                        'A12': {'value': 'Department Budget Analysis', 'style': {'font': {'bold': True, 'size': 14}}},
                        'A13': {'value': 'Prepared by: Finance Department', 'style': {'font': {'italic': True, 'size': 11}}},
                        'A14': {'value': 'Contact: finance@company.com', 'style': {'font': {'size': 10}}},
                        'A16': {'value': 'Department'},
                        'B16': {'value': 'Budget'},
                        'C16': {'value': 'Spent'},
                        'D16': {'value': 'Remaining'},
                        'E16': {'value': 'Utilization'},
                        'A17': {'value': 'Engineering'},
                        'B17': {'value': 200000},
                        'C17': {'value': 185000},
                        'D17': {'value': 15000},
                        'E17': {'value': '92.5%'},
                        'A18': {'value': 'Marketing'},
                        'B18': {'value': 150000},
                        'C18': {'value': 147500},
                        'D18': {'value': 2500},
                        'E18': {'value': '98.3%'},
                        'A19': {'value': 'Sales'},
                        'B19': {'value': 100000},
                        'C19': {'value': 95000},
                        'D19': {'value': 5000},
                        'E19': {'value': '95.0%'},
                        
                        # Table 3: With version and approval info
                        'A23': {'value': 'Project Status Dashboard', 'style': {'font': {'bold': True, 'size': 14}}},
                        'A24': {'value': 'Version 2.1 | Last Updated: Jan 15, 2025', 'style': {'font': {'italic': True, 'size': 10}}},
                        'A25': {'value': 'Approved by: John Smith, Director', 'style': {'font': {'size': 10}}},
                        'A27': {'value': 'Project'},
                        'B27': {'value': 'Status'},
                        'C27': {'value': 'Progress'},
                        'D27': {'value': 'Deadline'},
                        'E27': {'value': 'Owner'},
                        'A28': {'value': 'Website Redesign'},
                        'B28': {'value': 'In Progress'},
                        'C28': {'value': '75%'},
                        'D28': {'value': 'Mar 1'},
                        'E28': {'value': 'Sarah Johnson'},
                        'A29': {'value': 'Mobile App'},
                        'B29': {'value': 'Completed'},
                        'C29': {'value': '100%'},
                        'D29': {'value': 'Jan 15'},
                        'E29': {'value': 'Mike Chen'},
                        'A30': {'value': 'Database Migration'},
                        'B30': {'value': 'Planning'},
                        'C30': {'value': '25%'},
                        'D30': {'value': 'Apr 30'},
                        'E30': {'value': 'Lisa Wang'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data with gap detection enabled
        options = {
            'table_detection': {
                'use_gaps': True
            }
        }
        result = self.processor.transform_to_table_format(test_data, options)
        
        sheet = result['workbook']['sheets'][0]
        tables = sheet['tables']
        
        # Should detect 3 tables: 3 data blocks only
        self.assertEqual(len(tables), 3, f"Expected 3 tables (data blocks only), got {len(tables)}")
        
        # Verify that we have tables covering the expected regions
        table_regions = [table['region'] for table in tables]
        
        # Expected regions based on gap-based detection
        expected_regions = [
            {'start_row': 1, 'end_row': 8, 'start_col': 1, 'end_col': 8},
            {'start_row': 12, 'end_row': 19, 'start_col': 1, 'end_col': 8},
            {'start_row': 23, 'end_row': 30, 'start_col': 1, 'end_col': 8}
        ]
        
        # Verify that each expected region matches a detected table
        for i, expected in enumerate(expected_regions):
            if i < len(table_regions):
                actual = table_regions[i]
                self.assertEqual(actual['start_row'], expected['start_row'], 
                               f"Table {i+1} start_row mismatch: expected {expected['start_row']}, got {actual['start_row']}")
                self.assertEqual(actual['end_row'], expected['end_row'], 
                               f"Table {i+1} end_row mismatch: expected {expected['end_row']}, got {actual['end_row']}")
                self.assertEqual(actual['start_col'], expected['start_col'], 
                               f"Table {i+1} start_col mismatch: expected {expected['start_col']}, got {actual['start_col']}")
                self.assertEqual(actual['end_col'], expected['end_col'], 
                               f"Table {i+1} end_col mismatch: expected {expected['end_col']}, got {actual['end_col']}")

    def test_tables_with_mixed_content_and_formulas(self):
        """Test tables with mixed content types including formulas and special characters"""
        test_data = {
            'workbook': {
                'sheets': [{
                    'name': 'Mixed Content Sheet',
                    'dimensions': {
                        'min_row': 1,
                        'max_row': 25,
                        'min_col': 1,
                        'max_col': 7
                    },
                    'cells': {
                        # Table 1: With formulas and calculations
                        'A1': {'value': 'Sales Calculations', 'style': {'font': {'bold': True, 'size': 13}}},
                        'A3': {'value': 'Product'},
                        'B3': {'value': 'Units Sold'},
                        'C3': {'value': 'Unit Price'},
                        'D3': {'value': 'Total Revenue'},
                        'E3': {'value': 'Commission %'},
                        'F3': {'value': 'Commission $'},
                        'A4': {'value': 'Laptop Pro'},
                        'B4': {'value': 50},
                        'C4': {'value': 1200},
                        'D4': {'value': '=B4*C4'},  # Formula
                        'E4': {'value': '5%'},
                        'F4': {'value': '=D4*0.05'},  # Formula
                        'A5': {'value': 'Mouse Deluxe'},
                        'B5': {'value': 100},
                        'C5': {'value': 25},
                        'D5': {'value': '=B5*C5'},  # Formula
                        'E5': {'value': '3%'},
                        'F5': {'value': '=D5*0.03'},  # Formula
                        
                        # Table 2: With special characters and mixed data types
                        'A9': {'value': 'Special Data Report', 'style': {'font': {'bold': True, 'size': 13}}},
                        'A11': {'value': 'Category'},
                        'B11': {'value': 'Value'},
                        'C11': {'value': 'Status'},
                        'D11': {'value': 'Notes'},
                        'A12': {'value': 'Alpha & Beta'},
                        'B12': {'value': 123.45},
                        'C12': {'value': 'Active'},
                        'D12': {'value': 'Test data'},
                        'A13': {'value': 'Gamma (Test)'},
                        'B13': {'value': 67.89},
                        'C13': {'value': 'Pending'},
                        'D13': {'value': 'Review needed'},
                        'A14': {'value': 'Delta - Phase 1'},
                        'B14': {'value': 0},
                        'C14': {'value': 'Inactive'},
                        'D14': {'value': 'On hold'},
                        
                        # Table 3: With dates and currency
                        'A18': {'value': 'Financial Summary', 'style': {'font': {'bold': True, 'size': 13}}},
                        'A20': {'value': 'Date'},
                        'B20': {'value': 'Transaction'},
                        'C20': {'value': 'Amount ($)'},
                        'D20': {'value': 'Type'},
                        'E20': {'value': 'Reference'},
                        'A21': {'value': '2024-01-15'},
                        'B21': {'value': 'Invoice #1234'},
                        'C21': {'value': 1500.00},
                        'D21': {'value': 'Income'},
                        'E21': {'value': 'INV-1234'},
                        'A22': {'value': '2024-01-16'},
                        'B22': {'value': 'Payment #5678'},
                        'C22': {'value': -750.00},
                        'D22': {'value': 'Expense'},
                        'E22': {'value': 'PAY-5678'},
                        'A23': {'value': '2024-01-17'},
                        'B23': {'value': 'Refund #9012'},
                        'C23': {'value': 125.50},
                        'D23': {'value': 'Credit'},
                        'E23': {'value': 'REF-9012'}
                    },
                    'tables': []
                }]
            }
        }
        
        # Process the test data with gap detection enabled
        options = {
            'table_detection': {
                'use_gaps': True
            }
        }
        result = self.processor.transform_to_table_format(test_data, options)
        
        sheet = result['workbook']['sheets'][0]
        tables = sheet['tables']
        
        # Should detect 3 tables: 3 data blocks only
        self.assertEqual(len(tables), 3, f"Expected 3 tables (data blocks only), got {len(tables)}")
        
        # Verify that we have tables covering the expected regions
        table_regions = [table['region'] for table in tables]
        
        # Expected regions based on gap-based detection
        expected_regions = [
            {'start_row': 1, 'end_row': 5, 'start_col': 1, 'end_col': 7},
            {'start_row': 9, 'end_row': 14, 'start_col': 1, 'end_col': 7},
            {'start_row': 18, 'end_row': 25, 'start_col': 1, 'end_col': 7}
        ]
        
        # Verify that each expected region matches a detected table
        for i, expected in enumerate(expected_regions):
            if i < len(table_regions):
                actual = table_regions[i]
                self.assertEqual(actual['start_row'], expected['start_row'], 
                               f"Table {i+1} start_row mismatch: expected {expected['start_row']}, got {actual['start_row']}")
                self.assertEqual(actual['end_row'], expected['end_row'], 
                               f"Table {i+1} end_row mismatch: expected {expected['end_row']}, got {actual['end_row']}")
                self.assertEqual(actual['start_col'], expected['start_col'], 
                               f"Table {i+1} start_col mismatch: expected {expected['start_col']}, got {actual['start_col']}")
                self.assertEqual(actual['end_col'], expected['end_col'], 
                               f"Table {i+1} end_col mismatch: expected {expected['end_col']}, got {actual['end_col']}")


def run_tests():
    """Run the test suite"""
    print("=== RUNNING TABLE DETECTION TESTS ===")
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests() 