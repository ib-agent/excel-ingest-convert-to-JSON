# 360 Energy Excel Processing Test Suite

This directory contains comprehensive regression tests for the 360 Energy Excel file processing functionality, specifically validating the empty trailing row/column filtering improvements.

## Test File

**File:** `tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx`

This Excel file represents a complex financial model with:
- 10 sheets total (7 with data, 3 navigation sheets)
- Multiple tables per sheet with various layouts
- Significant empty trailing areas (sheets declare 1000+ rows but contain data in only 30-70 rows)
- Mixed data types (formulas, calculations, text headers)

## Test Coverage

### Core Functionality Tests

1. **`test_file_characteristics`**
   - Validates basic file structure (10 sheets, expected names)
   - Verifies data presence/absence in each sheet
   - Confirms table counts match expectations

2. **`test_empty_trailing_filtering`**
   - Tests the core filtering functionality
   - Validates 90%+ reduction in addressable space
   - Checks specific improvements per sheet
   - Ensures original data is preserved

3. **`test_data_preservation_after_filtering`**
   - Verifies no meaningful data is lost during filtering
   - Compares cell counts before/after filtering
   - Ensures data integrity is maintained

### Performance & Regression Tests

4. **`test_performance_characteristics`**
   - Measures processing time improvements
   - Validates addressable space reduction (>85%)
   - Confirms specific performance thresholds

5. **`test_regression_baseline_metrics`**
   - Maintains baseline metrics for regression detection
   - Validates consistent behavior across updates
   - Monitors key performance indicators

6. **`test_end_to_end_workflow`**
   - Tests complete processing pipeline
   - Validates Excel processing + table detection
   - Ensures integration between components

7. **`test_specific_sheet_validation`**
   - Detailed validation for each important sheet
   - Checks specific row/column limits
   - Validates data cell counts per sheet

## Running the Tests

### Option 1: Use the Test Runner Script (Recommended)
```bash
# Run all tests with detailed reporting
python run_360_energy_tests.py

# Quick validation only
python run_360_energy_tests.py --quick

# Verbose output
python run_360_energy_tests.py --verbose

# Use pytest runner
python run_360_energy_tests.py --pytest
```

### Option 2: Direct pytest
```bash
python -m pytest tests/test_360_energy_excel_processing.py -v
```

### Option 3: Direct unittest
```bash
python tests/test_360_energy_excel_processing.py
```

### Option 4: Import and run programmatically
```python
from tests.test_360_energy_excel_processing import run_360_energy_regression_test
success = run_360_energy_regression_test()
```

## Expected Results

When all tests pass, you should see:

```
✅ ALL TESTS PASSED! (8 tests)
   - Empty trailing filtering: ✓
   - Table detection: ✓ 
   - Data preservation: ✓
   - Performance improvements: ✓
   - Regression baseline: ✓
   - End-to-end workflow: ✓
```

### Key Performance Metrics

The tests validate these specific improvements:
- **Overall reduction**: >90% in addressable cell space
- **Rental Single Unit Economics**: 64,000 → ~2,300 cells (96%+ reduction)
- **Deal Pipeline**: 26,000 → ~200 cells (99%+ reduction)
- **Data preservation**: 99%+ of meaningful data retained
- **Processing speed**: Maintained or improved

## Integration with CI/CD

The test runner returns appropriate exit codes:
- `0` = All tests passed
- `1` = One or more tests failed

Example CI/CD integration:
```yaml
- name: Run 360 Energy Regression Tests
  run: python run_360_energy_tests.py
  working-directory: ./excel-ingest-convert-to-JSON
```

## Troubleshooting

### Test File Missing
```
❌ CRITICAL: Test file not found
```
Ensure `pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx` is in `tests/test_excel/`

### Filtering Not Working
```
❌ Expected >85% reduction in addressable space, got X%
```
Check that the `CompactExcelProcessor.process_file()` filtering is enabled by default.

### Data Loss
```
❌ Too much data lost during filtering
```
Review the `_has_meaningful_data()` function to ensure it's not too aggressive.

### Performance Regression
```
❌ Filtered cells should be under 25,000
```
Check if changes have increased the amount of data being retained unnecessarily.

## Maintaining the Tests

### Adding New Validations
1. Add new test methods to `Test360EnergyExcelProcessing` class
2. Follow the naming convention `test_*`
3. Use `self.subTest()` for multiple related assertions
4. Update the test runner's success reporting

### Updating Baselines
If legitimate changes affect the metrics:
1. Update the expected values in `test_regression_baseline_metrics()`
2. Update performance thresholds in `test_performance_characteristics()`
3. Document the changes in commit messages

### Test Data Changes
If the Excel file needs to be updated:
1. Ensure it maintains the same general structure
2. Update expected metrics in the test cases
3. Verify all sheet names and basic characteristics
4. Run the full test suite to identify needed adjustments

## File Structure

```
tests/
├── README_360_Energy_Tests.md          # This file
├── test_360_energy_excel_processing.py # Main test suite
└── test_excel/
    └── pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx
run_360_energy_tests.py                 # Test runner script
```