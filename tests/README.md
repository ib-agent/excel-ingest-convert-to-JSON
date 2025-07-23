# Test Suite Documentation

This directory contains comprehensive test suites for the Excel to JSON converter with header resolution functionality.

## Test Files

### Core Test Suites

#### `test_comprehensive_header_resolution.py`
**Main comprehensive test suite** that covers all header resolution scenarios:
- Single Level Headers
- Multi-Level Headers  
- Indented Row Headers
- Multiple Tables on Same Sheet
- Merged Cells
- Collapsed Headers (multiple column header rows)

**Usage**: `python tests/test_comprehensive_header_resolution.py`

#### `test_header_resolution.py`
**Header resolution specific tests** focusing on the header resolution functionality:
- Direct class usage testing
- API endpoint testing
- Header context validation

**Usage**: `python tests/test_header_resolution.py`

#### `test_table_transformation.py`
**Table transformation tests** for the table-oriented JSON format:
- Direct class usage testing
- API endpoint testing
- Table detection validation

**Usage**: `python tests/test_table_transformation.py`

#### `test_complex_table.py`
**Complex table scenario tests** for advanced table structures:
- Multi-level headers
- Complex data layouts
- Edge case handling

**Usage**: `python tests/test_complex_table.py`

### Test Result Files

#### Comprehensive Test Results
- `test_results_single_level_headers.json` - Single level header test results
- `test_results_multi_level_headers.json` - Multi-level header test results
- `test_results_indented_row_headers.json` - Indented row header test results
- `test_results_multiple_tables.json` - Multiple tables test results
- `test_results_merged_cells.json` - Merged cells test results
- `test_results_collapsed_headers.json` - Collapsed headers test results

#### API Test Results
- `test_api_transformation_result.json` - API table transformation results
- `test_api_header_resolution_result.json` - API header resolution results

#### Direct Test Results
- `test_direct_transformation_result.json` - Direct table transformation results
- `test_direct_header_resolution_result.json` - Direct header resolution results

#### Complex Table Results
- `test_complex_transformation_result.json` - Complex table transformation results

## Running Tests

### Run All Tests
```bash
python tests/test_comprehensive_header_resolution.py
```

### Run Individual Test Suites
```bash
# Header resolution tests
python tests/test_header_resolution.py

# Table transformation tests
python tests/test_table_transformation.py

# Complex table tests
python tests/test_complex_table.py
```

### Test Coverage

The comprehensive test suite covers:

1. **Single Level Headers** - Basic table with simple headers
2. **Multi-Level Headers** - Hierarchical column headers (Q1→Jan/Feb, Q2→Apr/May)
3. **Indented Row Headers** - Hierarchical row headers with indentation
4. **Multiple Tables** - Multiple tables on the same sheet
5. **Merged Cells** - Tables with merged cells in headers
6. **Collapsed Headers** - Multiple column header rows that need collapsing

### Expected Results

All tests should pass with:
- **Direct Tests**: 6/6 passed (100%)
- **API Tests**: 6/6 passed (100%)
- **Overall Success Rate**: 100%

### Test Output

Each test generates:
- Console output showing test progress and results
- JSON result files with complete enhanced data
- Detailed header context for each data cell

### API Endpoints Tested

- `POST /api/transform-tables/` - Convert Excel JSON to table format
- `POST /api/resolve-headers/` - Add header context to data cells

## Test Data Structure

Each test case includes:
- Excel-like data structure with cells, styles, and metadata
- Expected table count and data cell count
- Validation of header resolution accuracy
- API endpoint functionality verification

## Notes

- Tests require the Django server to be running on port 8001 for API tests
- All test files are self-contained and can be run independently
- Test result files contain complete enhanced JSON for inspection
- The comprehensive test suite is the primary validation tool 