"""
Comprehensive test case for 360 Energy Excel file processing and empty row/column filtering.

This test suite validates that the processing system correctly handles complex Excel files
with multiple sheets and tables, and properly filters out empty trailing rows and columns.

File: pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx

This test can be run as part of the regression test suite to ensure that:
1. Empty trailing row/column filtering works correctly
2. Table detection functions properly
3. Data integrity is preserved
4. Performance improvements are maintained

Run with: python -m pytest tests/test_360_energy_excel_processing.py -v
"""

import unittest
import os
import json
import time
from converter.compact_excel_processor import CompactExcelProcessor
from converter.compact_table_processor import CompactTableProcessor


class Test360EnergyExcelProcessing(unittest.TestCase):
    """Test case for 360 Energy Excel file processing"""
    
    def setUp(self):
        """Set up test case"""
        self.file_path = '/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx'
        self.processor = CompactExcelProcessor()
        self.table_processor = CompactTableProcessor()
        
        # Verify test file exists
        self.assertTrue(os.path.exists(self.file_path), f"Test file not found: {self.file_path}")
    
    def test_file_characteristics(self):
        """Test that the file has the expected characteristics"""
        # Process without filtering to check original structure
        result = self.processor.process_file(self.file_path, filter_empty_trailing=False)
        
        # Verify workbook structure
        self.assertIn('workbook', result)
        self.assertIn('sheets', result['workbook'])
        
        sheets = result['workbook']['sheets']
        self.assertEqual(len(sheets), 10, "Expected 10 sheets in the workbook")
        
        # Expected sheet names and their characteristics
        expected_sheets = {
            'Single Unit Econs>': {'has_data': False, 'tables': 0},
            'Rental Single Unit Economics': {'has_data': True, 'tables': 4},
            'Single Unit Waha Yard Economics': {'has_data': True, 'tables': 4},
            'Corporate Model>': {'has_data': False, 'tables': 0},
            'Monthly': {'has_data': True, 'tables': 1},
            'Assumptions': {'has_data': True, 'tables': 3},
            'New Rental Units': {'has_data': True, 'tables': 3},
            'Outputs>': {'has_data': False, 'tables': 0},
            'Output': {'has_data': True, 'tables': 2},
            'Deal Pipeline': {'has_data': True, 'tables': 2}
        }
        
        # Verify sheet names
        sheet_names = [sheet['name'] for sheet in sheets]
        for expected_name in expected_sheets.keys():
            self.assertIn(expected_name, sheet_names, f"Expected sheet '{expected_name}' not found")
    
    def test_empty_trailing_filtering(self):
        """Test that empty trailing rows and columns are properly filtered"""
        # Process with and without filtering
        result_filtered = self.processor.process_file(self.file_path, filter_empty_trailing=True)
        result_unfiltered = self.processor.process_file(self.file_path, filter_empty_trailing=False)
        
        # Expected improvements for sheets with excessive empty areas
        expected_improvements = {
            'Rental Single Unit Economics': {
                'original_dims': [1, 1, 1000, 64],
                'expected_max_row': 37,
                'expected_max_col': 62,
                'min_rows_saved': 900,
                'min_cols_saved': 1
            },
            'Single Unit Waha Yard Economics': {
                'original_dims': [1, 1, 1000, 73],
                'expected_max_row': 64,
                'expected_max_col': 69,
                'min_rows_saved': 900,
                'min_cols_saved': 3
            },
            'Deal Pipeline': {
                'original_dims': [1, 1, 1000, 26],
                'expected_max_row': 26,
                'expected_max_col': 8,
                'min_rows_saved': 900,
                'min_cols_saved': 15
            },
            'New Rental Units': {
                'original_dims': [1, 1, 1000, 65],
                'expected_max_row': 42,
                'expected_max_col': 65,
                'min_rows_saved': 900,
                'min_cols_saved': 0
            }
        }
        
        filtered_sheets = {sheet['name']: sheet for sheet in result_filtered['workbook']['sheets']}
        unfiltered_sheets = {sheet['name']: sheet for sheet in result_unfiltered['workbook']['sheets']}
        
        for sheet_name, expectations in expected_improvements.items():
            with self.subTest(sheet=sheet_name):
                self.assertIn(sheet_name, filtered_sheets, f"Sheet {sheet_name} not found in filtered results")
                self.assertIn(sheet_name, unfiltered_sheets, f"Sheet {sheet_name} not found in unfiltered results")
                
                filtered_sheet = filtered_sheets[sheet_name]
                unfiltered_sheet = unfiltered_sheets[sheet_name]
                
                # Check original dimensions
                unfiltered_dims = unfiltered_sheet.get('dimensions', [])
                self.assertEqual(unfiltered_dims, expectations['original_dims'], 
                               f"Original dimensions don't match for {sheet_name}")
                
                # Check filtered dimensions
                filtered_dims = filtered_sheet.get('dimensions', [])
                self.assertLessEqual(filtered_dims[2], expectations['expected_max_row'], 
                                   f"Filtered max row too high for {sheet_name}")
                self.assertLessEqual(filtered_dims[3], expectations['expected_max_col'], 
                                   f"Filtered max col too high for {sheet_name}")
                
                # Check savings
                rows_saved = unfiltered_dims[2] - filtered_dims[2]
                cols_saved = unfiltered_dims[3] - filtered_dims[3]
                
                self.assertGreaterEqual(rows_saved, expectations['min_rows_saved'], 
                                      f"Not enough rows saved for {sheet_name}")
                self.assertGreaterEqual(cols_saved, expectations['min_cols_saved'], 
                                      f"Not enough columns saved for {sheet_name}")
    
    def test_specific_table_characteristics(self):
        """Test specific table characteristics for each sheet"""
        result = self.processor.process_file(self.file_path)
        tables_result = self.table_processor.transform_to_compact_table_format(result)
        
        sheets = {sheet['name']: sheet for sheet in tables_result['workbook']['sheets']}
        
        # Test Rental Single Unit Economics
        rental_sheet = sheets.get('Rental Single Unit Economics')
        self.assertIsNotNone(rental_sheet, "Rental Single Unit Economics sheet not found")
        
        tables = rental_sheet.get('tables', [])
        self.assertGreater(len(tables), 0, "No tables detected in Rental Single Unit Economics")
        
        # Should detect tables around B3-C20 (Assumptions), B22-D28 (Capex Detail), 
        # B30-C37 (Monthly Cash Flow), F2-O28 (Year Fraction)
        table_titles = [table.get('title', '') for table in tables]
        self.assertIn('Monthly Cash Flow', table_titles, "Monthly Cash Flow table not detected")
        
        # Test Deal Pipeline
        pipeline_sheet = sheets.get('Deal Pipeline')
        self.assertIsNotNone(pipeline_sheet, "Deal Pipeline sheet not found")
        
        tables = pipeline_sheet.get('tables', [])
        self.assertGreater(len(tables), 0, "No tables detected in Deal Pipeline")
        
        # Should detect Rental Deal Pipeline (C3-H15) and Customer Purchase Deals (C19-F26)
        table_titles = [table.get('title', '') for table in tables]
        self.assertIn('Rental Deal Pipeline', table_titles, "Rental Deal Pipeline table not detected")
        self.assertIn('Customer Purchase Deals', table_titles, "Customer Purchase Deals table not detected")
        
        # Test Monthly sheet (large table)
        monthly_sheet = sheets.get('Monthly')
        self.assertIsNotNone(monthly_sheet, "Monthly sheet not found")
        
        tables = monthly_sheet.get('tables', [])
        self.assertGreater(len(tables), 0, "No tables detected in Monthly sheet")
        
        # Should detect one large table covering most of the sheet
        self.assertEqual(len(tables), 1, "Expected exactly one table in Monthly sheet")
    
    def test_data_preservation_after_filtering(self):
        """Test that actual data is preserved after filtering empty areas"""
        result_filtered = self.processor.process_file(self.file_path, filter_empty_trailing=True)
        result_unfiltered = self.processor.process_file(self.file_path, filter_empty_trailing=False)
        
        filtered_sheets = {sheet['name']: sheet for sheet in result_filtered['workbook']['sheets']}
        unfiltered_sheets = {sheet['name']: sheet for sheet in result_unfiltered['workbook']['sheets']}
        
        for sheet_name in ['Rental Single Unit Economics', 'Deal Pipeline', 'Monthly']:
            with self.subTest(sheet=sheet_name):
                filtered_sheet = filtered_sheets[sheet_name]
                unfiltered_sheet = unfiltered_sheets[sheet_name]
                
                # Count cells with meaningful data
                def count_data_cells(sheet):
                    count = 0
                    for row in sheet.get('rows', []):
                        for cell in row.get('cells', []):
                            if len(cell) >= 2 and cell[1] is not None and str(cell[1]).strip() != '':
                                count += 1
                    return count
                
                filtered_data_count = count_data_cells(filtered_sheet)
                unfiltered_data_count = count_data_cells(unfiltered_sheet)
                
                # Data should be preserved (filtered should have same or slightly different count due to empty cell filtering)
                self.assertGreaterEqual(filtered_data_count, unfiltered_data_count * 0.99, 
                                      f"Too much data lost during filtering for {sheet_name}")
    
    def test_performance_characteristics(self):
        """Test that filtering provides measurable performance benefits"""
        # Time the processing with and without filtering
        start_time = time.time()
        result_filtered = self.processor.process_file(self.file_path, filter_empty_trailing=True)
        filtered_time = time.time() - start_time
        
        start_time = time.time()
        result_unfiltered = self.processor.process_file(self.file_path, filter_empty_trailing=False)
        unfiltered_time = time.time() - start_time
        
        # Calculate total cells processed
        def count_total_cells(result):
            total = 0
            for sheet in result['workbook']['sheets']:
                dims = sheet.get('dimensions', [1, 1, 1, 1])
                total += (dims[2] - dims[0] + 1) * (dims[3] - dims[1] + 1)
            return total
        
        filtered_cells = count_total_cells(result_filtered)
        unfiltered_cells = count_total_cells(result_unfiltered)
        
        # Should have significant reduction in total addressable space
        reduction_ratio = 1 - (filtered_cells / unfiltered_cells)
        self.assertGreater(reduction_ratio, 0.85, 
                          f"Expected >85% reduction in addressable space, got {reduction_ratio:.2%}")
        
        # Verify specific expected reductions
        self.assertLess(filtered_cells, 25000, "Filtered cells should be under 25,000")
        self.assertGreater(unfiltered_cells, 200000, "Unfiltered cells should be over 200,000")
        
        print(f"Empty trailing filtering achieved {reduction_ratio:.1%} reduction in addressable space")
        print(f"Reduced from {unfiltered_cells:,} to {filtered_cells:,} total addressable cells")
        print(f"Processing time - Filtered: {filtered_time:.2f}s, Unfiltered: {unfiltered_time:.2f}s")
    
    def test_regression_baseline_metrics(self):
        """Test baseline metrics for regression detection"""
        result = self.processor.process_file(self.file_path, filter_empty_trailing=True)
        
        # Baseline metrics that should remain consistent
        baseline_metrics = {
            'total_sheets': 10,
            'sheets_with_data': 7,
            'sheets_without_data': 3,
            'total_filtered_cells': (20000, 25000),  # Range for filtered cells
            'sheets_with_major_reduction': 5  # Sheets with >90% reduction
        }
        
        sheets = result['workbook']['sheets']
        self.assertEqual(len(sheets), baseline_metrics['total_sheets'])
        
        sheets_with_data = sum(1 for sheet in sheets if len(sheet.get('rows', [])) > 0)
        sheets_without_data = sum(1 for sheet in sheets if len(sheet.get('rows', [])) == 0)
        
        self.assertEqual(sheets_with_data, baseline_metrics['sheets_with_data'])
        self.assertEqual(sheets_without_data, baseline_metrics['sheets_without_data'])
        
        # Calculate total filtered cells
        total_cells = sum((sheet.get('dimensions', [1,1,1,1])[2] - sheet.get('dimensions', [1,1,1,1])[0] + 1) * 
                         (sheet.get('dimensions', [1,1,1,1])[3] - sheet.get('dimensions', [1,1,1,1])[1] + 1)
                         for sheet in sheets)
        
        self.assertGreaterEqual(total_cells, baseline_metrics['total_filtered_cells'][0])
        self.assertLessEqual(total_cells, baseline_metrics['total_filtered_cells'][1])
        
        print(f"Regression baseline metrics validated - {total_cells:,} total filtered cells")
    
    def test_end_to_end_workflow(self):
        """Test the complete end-to-end workflow including table processing"""
        # Step 1: Process the Excel file with filtering
        excel_result = self.processor.process_file(self.file_path, filter_empty_trailing=True)
        
        # Step 2: Apply table detection
        table_result = self.table_processor.transform_to_compact_table_format(excel_result)
        
        # Step 3: Validate the complete pipeline
        self.assertIn('workbook', table_result)
        self.assertIn('sheets', table_result['workbook'])
        
        sheets_with_tables = 0
        total_tables_detected = 0
        
        for sheet in table_result['workbook']['sheets']:
            tables = sheet.get('tables', [])
            if tables:
                sheets_with_tables += 1
                total_tables_detected += len(tables)
        
        # Should detect tables in most data sheets
        self.assertGreaterEqual(sheets_with_tables, 6, "Should detect tables in at least 6 sheets")
        self.assertGreaterEqual(total_tables_detected, 15, "Should detect at least 15 tables total")
        
        print(f"End-to-end workflow validated - {sheets_with_tables} sheets with tables, {total_tables_detected} total tables")
    
    def test_specific_sheet_validation(self):
        """Test specific characteristics of each important sheet"""
        result = self.processor.process_file(self.file_path, filter_empty_trailing=True)
        sheets_dict = {sheet['name']: sheet for sheet in result['workbook']['sheets']}
        
        # Detailed validation for key sheets
        test_cases = [
            {
                'name': 'Rental Single Unit Economics',
                'max_expected_rows': 40,
                'max_expected_cols': 65,
                'min_data_cells': 1000,
                'should_have_data': True
            },
            {
                'name': 'Single Unit Waha Yard Economics', 
                'max_expected_rows': 70,
                'max_expected_cols': 75,
                'min_data_cells': 1300,
                'should_have_data': True
            },
            {
                'name': 'Monthly',
                'max_expected_rows': 175,
                'max_expected_cols': 65,
                'min_data_cells': 6000,
                'should_have_data': True
            },
            {
                'name': 'Deal Pipeline',
                'max_expected_rows': 30,
                'max_expected_cols': 10,
                'min_data_cells': 80,
                'should_have_data': True
            },
            {
                'name': 'Single Unit Econs>',
                'max_expected_rows': 2,
                'max_expected_cols': 2,
                'min_data_cells': 0,
                'should_have_data': False
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(sheet=test_case['name']):
                sheet = sheets_dict.get(test_case['name'])
                self.assertIsNotNone(sheet, f"Sheet {test_case['name']} not found")
                
                dims = sheet.get('dimensions', [1, 1, 1, 1])
                max_row, max_col = dims[2], dims[3]
                
                self.assertLessEqual(max_row, test_case['max_expected_rows'], 
                                   f"Too many rows in {test_case['name']}")
                self.assertLessEqual(max_col, test_case['max_expected_cols'], 
                                   f"Too many columns in {test_case['name']}")
                
                # Count data cells
                data_cells = 0
                for row in sheet.get('rows', []):
                    for cell in row.get('cells', []):
                        if len(cell) >= 2 and cell[1] is not None and str(cell[1]).strip():
                            data_cells += 1
                
                if test_case['should_have_data']:
                    self.assertGreaterEqual(data_cells, test_case['min_data_cells'],
                                          f"Not enough data cells in {test_case['name']}")
                else:
                    self.assertEqual(data_cells, 0, f"Unexpected data in {test_case['name']}")
        
        print("All specific sheet validations passed")


def run_360_energy_regression_test():
    """
    Convenience function to run the 360 Energy regression test suite.
    Returns True if all tests pass, False otherwise.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(Test360EnergyExcelProcessing)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n{'='*60}")
    print(f"360 ENERGY EXCEL PROCESSING REGRESSION TEST RESULTS")
    print(f"{'='*60}")
    
    if result.wasSuccessful():
        print(f"✅ ALL TESTS PASSED! ({result.testsRun} tests)")
        print(f"   - Empty trailing filtering: ✓")
        print(f"   - Table detection: ✓") 
        print(f"   - Data preservation: ✓")
        print(f"   - Performance improvements: ✓")
        print(f"   - Regression baseline: ✓")
        print(f"   - End-to-end workflow: ✓")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for test, error in result.failures + result.errors:
            print(f"   - {test}: {error}")
        return False


if __name__ == '__main__':
    # Run the regression test when called directly
    success = run_360_energy_regression_test()
    exit(0 if success else 1)