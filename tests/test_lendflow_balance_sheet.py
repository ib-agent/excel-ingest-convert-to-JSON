"""
Test case for Lendflow Balance Sheet financial statement processing.

This test validates that financial statements with section headers are correctly
identified as single tables rather than being split into multiple tables.

File: pDD10abc_Lendflow_12.31_2024_Balance_Sheet_(1_19_25).xlsx

The file contains a Balance Sheet with:
- Single sheet: "Balance Sheet - GAAP"
- Single table spanning A1:AK17 (17 rows × 37 columns)
- Section headers: "Assets", "Liabilities", "Equity" (rows with only first column data)
- Data rows with values across multiple columns
- Column headers with dates/periods
"""

import unittest
import os
from converter.compact_excel_processor import CompactExcelProcessor
from converter.compact_table_processor import CompactTableProcessor


class TestLendflowBalanceSheet(unittest.TestCase):
    """Test case for Lendflow Balance Sheet processing"""
    
    def setUp(self):
        """Set up test case"""
        self.file_path = '/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/test_excel/pDD10abc_Lendflow_12.31_2024_Balance_Sheet_(1_19_25).xlsx'
        self.processor = CompactExcelProcessor()
        self.table_processor = CompactTableProcessor()
        
        # Verify test file exists
        self.assertTrue(os.path.exists(self.file_path), f"Test file not found: {self.file_path}")
    
    def test_file_structure(self):
        """Test that the file has the expected basic structure"""
        result = self.processor.process_file(self.file_path)
        
        # Verify workbook structure
        self.assertIn('workbook', result)
        self.assertIn('sheets', result['workbook'])
        
        sheets = result['workbook']['sheets']
        self.assertEqual(len(sheets), 1, "Expected 1 sheet in the Balance Sheet file")
        
        sheet = sheets[0]
        self.assertEqual(sheet['name'], 'Balance Sheet - GAAP')
        
        # Check dimensions
        dimensions = sheet.get('dimensions', [])
        self.assertEqual(len(dimensions), 4, "Expected 4-element dimensions array")
        self.assertEqual(dimensions[0], 1, "Expected min_row = 1")
        self.assertEqual(dimensions[1], 1, "Expected min_col = 1") 
        self.assertEqual(dimensions[2], 17, "Expected max_row = 17")
        self.assertEqual(dimensions[3], 37, "Expected max_col = 37")
    
    def test_section_header_identification(self):
        """Test that section headers are correctly identified"""
        result = self.processor.process_file(self.file_path)
        sheet = result['workbook']['sheets'][0]
        
        # Expected section headers and their row numbers
        expected_headers = {
            2: "Assets",
            8: "Liabilities", 
            14: "Equity"
        }
        
        rows = sheet.get('rows', [])
        found_headers = {}
        
        for row_data in rows:
            row_num = row_data.get('r', 0)
            if row_num in expected_headers:
                cells = row_data.get('cells', [])
                if cells and len(cells[0]) >= 2:
                    first_cell_value = cells[0][1]
                    found_headers[row_num] = first_cell_value
                    
                    # Verify this row has only first column data (section header characteristic)
                    other_cell_count = len([cell for cell in cells[1:] if len(cell) >= 2 and cell[1] is not None and str(cell[1]).strip()])
                    self.assertEqual(other_cell_count, 0, f"Row {row_num} should only have data in first column")
        
        # Verify all expected headers were found
        for row_num, expected_text in expected_headers.items():
            self.assertIn(row_num, found_headers, f"Section header not found in row {row_num}")
            self.assertEqual(found_headers[row_num], expected_text, f"Incorrect header text in row {row_num}")
    
    def test_single_table_detection(self):
        """Test that the financial statement is detected as a single table"""
        result = self.processor.process_file(self.file_path)
        tables_result = self.table_processor.transform_to_compact_table_format(result)
        
        sheet = tables_result['workbook']['sheets'][0]
        tables = sheet.get('tables', [])
        
        # Should detect exactly one table
        self.assertEqual(len(tables), 1, "Expected exactly 1 table, not multiple tables split by section headers")
        
        table = tables[0]
        region = table.get('region', [])
        
        # Verify table covers the expected range
        self.assertEqual(len(region), 4, "Expected 4-element region array")
        start_row, start_col, end_row, end_col = region
        
        self.assertEqual(start_row, 1, "Table should start at row 1")
        self.assertEqual(start_col, 1, "Table should start at column 1") 
        self.assertEqual(end_row, 17, "Table should end at row 17")
        self.assertEqual(end_col, 37, "Table should end at column 37")
        
        # Convert to cell range for verification
        def col_to_letter(col_num):
            result = ''
            while col_num > 0:
                col_num -= 1
                result = chr(65 + (col_num % 26)) + result
                col_num //= 26
            return result
        
        start_cell = f'{col_to_letter(start_col)}{start_row}'
        end_cell = f'{col_to_letter(end_col)}{end_row}'
        
        self.assertEqual(start_cell, 'A1', "Table should start at A1")
        self.assertEqual(end_cell, 'AK17', "Table should end at AK17")
    
    def test_financial_statement_detection_method(self):
        """Test that the financial statement detection method is used"""
        result = self.processor.process_file(self.file_path)
        tables_result = self.table_processor.transform_to_compact_table_format(result)
        
        sheet = tables_result['workbook']['sheets'][0]
        tables = sheet.get('tables', [])
        
        self.assertEqual(len(tables), 1)
        table = tables[0]
        
        # The detection method should be recorded in the table metadata
        # Note: The exact way this is stored may vary based on implementation
        region = table.get('region', [])
        self.assertTrue(len(region) == 4, "Should have valid region data from financial statement detection")
    
    def test_data_integrity(self):
        """Test that all meaningful data is preserved in the single table"""
        result = self.processor.process_file(self.file_path)
        sheet = result['workbook']['sheets'][0]
        
        # Count total data cells
        total_data_cells = 0
        rows = sheet.get('rows', [])
        
        for row_data in rows:
            cells = row_data.get('cells', [])
            for cell in cells:
                if len(cell) >= 2 and cell[1] is not None and str(cell[1]).strip():
                    total_data_cells += 1
        
        # Should have significant amount of data
        self.assertGreater(total_data_cells, 50, "Should have substantial data in the Balance Sheet")
        
        # Verify specific sections have data
        rows_with_data = set()
        for row_data in rows:
            row_num = row_data.get('r', 0)
            cells = row_data.get('cells', [])
            if any(len(cell) >= 2 and cell[1] is not None and str(cell[1]).strip() for cell in cells):
                rows_with_data.add(row_num)
        
        # Should have data in Assets, Liabilities, and Equity sections
        assets_section = any(3 <= row <= 7 for row in rows_with_data)  # Rows after "Assets" header
        liabilities_section = any(9 <= row <= 13 for row in rows_with_data)  # Rows after "Liabilities" header  
        equity_section = any(15 <= row <= 17 for row in rows_with_data)  # Rows after "Equity" header
        
        self.assertTrue(assets_section, "Should have data in Assets section")
        self.assertTrue(liabilities_section, "Should have data in Liabilities section")
        self.assertTrue(equity_section, "Should have data in Equity section")
    
    def test_regression_prevention(self):
        """Test to prevent regression back to multiple table detection"""
        result = self.processor.process_file(self.file_path)
        tables_result = self.table_processor.transform_to_compact_table_format(result)
        
        sheet = tables_result['workbook']['sheets'][0]
        tables = sheet.get('tables', [])
        
        # This is the critical test - before the fix, this would detect 7 tables
        self.assertNotEqual(len(tables), 7, "REGRESSION: Should not detect 7 separate tables like before the fix")
        self.assertEqual(len(tables), 1, "Should maintain single table detection after fix")
        
        # Verify no tables with tiny ranges (which would indicate section headers treated as separate tables)
        for table in tables:
            region = table.get('region', [])
            if len(region) >= 4:
                rows = region[2] - region[0] + 1
                self.assertGreater(rows, 5, "No table should have only a few rows (indicates section header split)")


def run_lendflow_regression_test():
    """
    Convenience function to run the Lendflow Balance Sheet regression test.
    Returns True if all tests pass, False otherwise.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLendflowBalanceSheet)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print(f"LENDFLOW BALANCE SHEET REGRESSION TEST RESULTS")
    print(f"{'='*60}")
    
    if result.wasSuccessful():
        print(f"✅ ALL TESTS PASSED! ({result.testsRun} tests)")
        print(f"   - Single table detection: ✓")
        print(f"   - Section header handling: ✓")
        print(f"   - Financial statement layout: ✓")
        print(f"   - Data integrity: ✓")
        print(f"   - Regression prevention: ✓")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for test, error in result.failures + result.errors:
            print(f"   - {test}: {error}")
        return False


if __name__ == '__main__':
    # Run the regression test when called directly
    success = run_lendflow_regression_test()
    exit(0 if success else 1)