# Test Suite Documentation

This directory contains comprehensive test suites for the Excel to JSON converter with header resolution functionality and PDF processing capabilities. The test suite ensures robust testing of a large variety of header and column labels, multiple table detection, various edge cases, and PDF processing workflows.

## Test Files

### Core Test Suites

#### `test_comprehensive_header_resolution.py`
**Main comprehensive test suite** that covers all header resolution scenarios:
- **Single Level Headers**: Basic table with simple headers (Product, Price, Quantity)
- **Multi-Level Headers**: Hierarchical column headers (Q1→Jan/Feb, Q2→Apr/May) with complex nested structures
- **Indented Row Headers**: Hierarchical row headers with indentation levels (Electronics→Computers→Laptops)
- **Multiple Tables on Same Sheet**: Detection and processing of multiple distinct tables within one worksheet
- **Merged Cells**: Tables with merged cells in headers that need proper resolution
- **Collapsed Headers**: Multiple column header rows that need collapsing into single headers

**Tests Header Variety**: Product names, time periods (Q1, Q2, Jan, Feb), categories (Electronics, Computers), regions (North, South), and various business metrics.

**Usage**: `python tests/test_comprehensive_header_resolution.py`

#### `test_header_resolution.py`
**Header resolution specific tests** focusing on the header resolution functionality:
- **Direct class usage testing**: Tests HeaderResolver class directly with various header scenarios
- **API endpoint testing**: Validates `/api/resolve-headers/` endpoint functionality
- **Header context validation**: Ensures proper header context is applied to data cells
- **Style-based header detection**: Tests header identification based on cell styling (bold, background colors)
- **Frozen pane integration**: Tests header resolution with frozen rows and columns

**Tests Header Variety**: Sales data headers, product categories, time periods, regional data, and financial metrics.

**Usage**: `python tests/test_header_resolution.py`

#### `test_table_transformation.py`
**Table transformation tests** for the table-oriented JSON format:
- **Direct class usage testing**: Tests TableProcessor class directly
- **API endpoint testing**: Validates `/api/transform-tables/` endpoint functionality
- **Table detection validation**: Ensures proper table region detection and extraction
- **Data structure conversion**: Tests conversion from cell-based to table-based JSON format
- **Style preservation**: Validates that cell styles are properly preserved during transformation

**Tests Table Variety**: Sales data tables, product tables, financial tables, and inventory tables.

**Usage**: `python tests/test_table_transformation.py`

#### `test_complex_table.py`
**Complex table scenario tests** for advanced table structures:
- **Multi-level headers**: Complex hierarchical column structures with multiple levels
- **Complex data layouts**: Tables with irregular data patterns and mixed data types
- **Edge case handling**: Tests with unusual table configurations and data arrangements
- **Large table processing**: Tests with larger datasets to ensure scalability
- **Mixed content types**: Tables containing text, numbers, dates, and formulas

**Tests Header Variety**: Complex business hierarchies, multi-dimensional data structures, and advanced organizational schemes.

**Usage**: `python tests/test_complex_table.py`

#### `test_table_detection.py`
**Table detection and region identification tests**:
- **Full table detection**: Ensures complete table regions are detected, not just partial areas
- **Blank header labeling**: Tests proper handling of blank or empty headers (labeled as "unlabeled")
- **Single cell table handling**: Edge case testing for minimal table structures
- **Boundary detection**: Validates correct identification of table start/end boundaries
- **Data area coverage**: Ensures all relevant data cells are included in detected tables
- **Multiple tables with titles**: Tests detection of 3+ tables with preserved titles and metadata
- **Spread tables**: Tests tables positioned in different areas of the sheet (top-left, top-right, bottom-left, bottom-right)
- **Variable separations**: Tests tables with different separation distances (2+ rows between tables)
- **Complex titles**: Tests tables with subtitles, dates, contact info, and version metadata
- **Mixed content**: Tests tables with formulas, special characters, dates, and currency

**Tests Detection Variety**: Tables with missing headers, incomplete data, edge cases, minimal structures, multiple tables per sheet, complex layouts, and varied content types.

**Usage**: `python tests/test_table_detection.py`

#### `test_frozen_panes.py`
**Frozen panes parsing and preservation tests**:
- **Frozen pane parsing**: Tests correct extraction of frozen pane information from Excel files
- **Coordinate conversion**: Validates conversion between Excel coordinates (B3) and row/column counts
- **Preservation during transformation**: Ensures frozen pane data is maintained through processing
- **Different frozen pane formats**: Tests various frozen pane configurations and formats
- **Integration with header detection**: Validates frozen panes work correctly with header resolution

**Tests Frozen Pane Variety**: Different frozen row/column combinations, various coordinate formats, and edge cases.

**Usage**: `python tests/test_frozen_panes.py`

#### `test_frozen_panes_table_detection.py`
**Frozen panes table detection override tests**:
- **Frozen panes override**: Tests that sheets with any frozen rows or columns default to one table
- **Other detection bypass**: Validates that gap detection, formatting detection, and other methods are skipped
- **Frozen rows only**: Tests sheets with only frozen rows (no frozen columns) still create one table
- **Frozen columns only**: Tests sheets with only frozen columns (no frozen rows) still create one table
- **No frozen panes**: Verifies that sheets without frozen panes use other detection methods
- **Data inclusion verification**: Ensures all data is included in the single table when frozen panes are present

**Tests Frozen Pane Detection Variety**: Sheets with frozen panes and large gaps, multiple data sections, different formatting patterns, and various frozen pane configurations.

**Usage**: `python tests/test_frozen_panes_table_detection.py`

#### `test_enhanced_gap_detection.py`
**Enhanced gap detection tests** for intelligent table separation:
- **Gap with date content**: Tests that gaps followed by date content start a new table
- **Gap with numerical content**: Tests that gaps followed by numerical content continue the same table
- **Gap with text labels**: Tests that gaps followed by text labels start a new table
- **Mixed content after gap**: Tests that gaps followed by mixed content start new tables

**Tests Gap Detection Variety**: Various content types after gaps, different gap sizes, and mixed content scenarios.

**Usage**: `python tests/test_enhanced_gap_detection.py`

#### `test_decimal_extraction.py`
**Decimal number extraction tests** for PDF processing:
- **Decimal with suffixes**: Tests that decimal numbers followed by 'x' (like 1.80x, 2.31x) are extracted correctly
- **Pattern comparison**: Tests old pattern with word boundaries vs new pattern without word boundaries
- **Text extraction**: Tests decimal extraction from actual text content
- **Pattern validation**: Ensures regex patterns work correctly for various decimal formats

**Tests Decimal Extraction Variety**: Numbers with suffixes, standalone decimals, and mixed text content.

**Usage**: `python tests/test_decimal_extraction.py`

#### `test_comprehensive_number_extraction.py`
**Comprehensive number extraction tests** for PDF processing:
- **Percentage extraction**: Tests that percentage numbers (like 5.5%) are extracted correctly
- **Decimal extraction**: Tests that decimal numbers (like 1.08, 87.1, 67.3) are extracted correctly
- **Decimal with suffixes**: Tests that decimal numbers with suffixes (like 1.80x, 2.31x) are extracted correctly
- **Confidence thresholds**: Tests that decimal numbers have appropriate confidence scores (>= 0.7)
- **Overall number count**: Tests that the total number count has improved with fixes

**Tests Number Extraction Variety**: Percentages, decimals, decimals with suffixes, and confidence scoring.

**Usage**: `python tests/test_comprehensive_number_extraction.py`

#### `test_multiple_frozen_rows.py`
**Multiple frozen rows handling for row labels**:
- **Multiple frozen rows**: Tests scenarios with 2+ frozen rows for complex header structures
- **Row label concatenation**: Validates proper concatenation of values from multiple frozen rows
- **Different value combinations**: Tests various combinations of frozen row values
- **Fallback behavior**: Tests behavior when no frozen rows are specified
- **Header information preservation**: Ensures header metadata is correctly captured

**Tests Frozen Row Variety**: Year/month combinations, category/subcategory structures, and multi-level row hierarchies.

**Usage**: `python tests/test_multiple_frozen_rows.py`

#### `test_style_cleaning.py`
**Style cleaning and optimization tests**:
- **Default value removal**: Tests removal of default style values (00000000 colors, 0.0 tints)
- **Non-default preservation**: Ensures non-default style values are properly preserved
- **Mixed value handling**: Tests scenarios with both default and non-default values
- **Alignment data cleaning**: Validates cleaning of alignment properties
- **Integration testing**: Tests style cleaning within the full transformation pipeline

**Tests Style Variety**: Various fill colors, alignment settings, font properties, and border configurations.

**Usage**: `python tests/test_style_cleaning.py`

#### `test_error_message_filtering.py`
**Error message detection and filtering tests**:
- **Error pattern detection**: Tests identification of common error message patterns
- **Incomplete pattern handling**: Validates detection of partial or incomplete error messages
- **Valid data preservation**: Ensures legitimate data is not incorrectly flagged as errors
- **Edge case handling**: Tests behavior with null values, numbers, and other data types
- **Integration with cleaning**: Tests error filtering within the data cleaning pipeline

**Tests Error Variety**: Various error message formats, incomplete patterns, placeholder text, and validation messages.

**Usage**: `python tests/test_error_message_filtering.py`

#### `test_download_functionality.py`
**Download functionality and large file handling tests**:
- **Normal file response**: Tests standard response structure for downloadable files
- **Large file response**: Validates response structure for files too large for direct download
- **Download URL generation**: Tests proper URL format and structure for file downloads
- **File information structure**: Validates metadata about processed files
- **Summary information**: Tests generation of processing summaries
- **Data serialization**: Ensures data is properly formatted for download

**Tests Download Variety**: Different file sizes, response formats, URL structures, and metadata configurations.

**Usage**: `python tests/test_download_functionality.py`

#### `test_table_paragraph_detection.py`
**Table and paragraph detection improvements for PDF processing**:
- **Table-only PDFs**: Tests that PDFs with only tables extract tables correctly without text duplication
- **Text-only PDFs**: Tests that PDFs with only paragraphs extract text sections and numbers correctly
- **Mixed content handling**: Validates proper separation of table and text content
- **Exclusion zone creation**: Tests that table regions are properly excluded from text extraction
- **Duplication prevention**: Ensures table content is not duplicated in text sections

**Tests Detection Variety**: PDFs with tables only, paragraphs only, and mixed content scenarios.

**Usage**: `python tests/test_table_paragraph_detection.py`

### PDF Processing Tests

#### `test_pdf_processing.py`
**Core PDF processing functionality tests**:
- **Table extraction**: Tests PDF table detection and extraction using multiple methods
- **Text content extraction**: Validates paragraph and text section extraction from PDFs
- **Number extraction**: Tests numerical data extraction from PDF content
- **Multi-method processing**: Validates fallback between different extraction methods
- **Error handling**: Tests robust error handling for various PDF formats
- **Integration testing**: Tests full PDF processing pipeline

**Tests PDF Variety**: Different PDF layouts, table structures, text formats, and content types.

**Usage**: `python tests/test_pdf_processing.py`

#### `test_financial_table_detection.py`
**Financial table specific detection tests**:
- **Financial data patterns**: Tests detection of financial tables with monetary values
- **Multi-column layouts**: Validates detection of financial statements and reports
- **Currency handling**: Tests proper handling of currency symbols and formats
- **Calculation preservation**: Ensures financial calculations are properly extracted
- **Format recognition**: Tests recognition of standard financial report formats

**Tests Financial Variety**: Income statements, balance sheets, financial summaries, and budget reports.

**Usage**: `python tests/test_financial_table_detection.py`

#### `test_specific_table_detection.py`
**Specific table pattern detection tests**:
- **Custom table patterns**: Tests detection of specific table layouts and structures
- **Edge case tables**: Validates detection of unusual or non-standard table formats
- **Content-based detection**: Tests table detection based on content patterns
- **Layout variation handling**: Tests adaptation to different table layouts
- **Precision testing**: Validates accurate detection of specific table types

**Tests Table Variety**: Custom layouts, unusual structures, content-based patterns, and layout variations.

**Usage**: `python tests/test_specific_table_detection.py`

#### `test_table_content.py`
**Table content processing and validation tests**:
- **Content extraction**: Tests accurate extraction of table cell content
- **Data type preservation**: Validates preservation of different data types (numbers, text, dates)
- **Formatting preservation**: Tests maintenance of cell formatting and styles
- **Content validation**: Ensures extracted content matches source data
- **Quality assessment**: Tests content quality and accuracy metrics

**Tests Content Variety**: Mixed data types, formatted content, special characters, and complex data structures.

**Usage**: `python tests/test_table_content.py`

#### `test_table_100_numbers.py`
**Large table number extraction tests**:
- **High volume processing**: Tests extraction from tables with 100+ numerical values
- **Performance validation**: Ensures efficient processing of large numerical datasets
- **Accuracy testing**: Validates accuracy of number extraction at scale
- **Memory management**: Tests memory efficiency with large data volumes
- **Scaling verification**: Ensures system scales properly with data size

**Tests Large Scale Variety**: Tables with extensive numerical data, performance benchmarks, and scaling scenarios.

**Usage**: `python tests/test_table_100_numbers.py`

#### `test_paragraph_extraction.py`
**Paragraph and text content extraction tests**:
- **Text section detection**: Tests identification of paragraph sections in PDFs
- **Content separation**: Validates separation of text from table content
- **Paragraph structure**: Tests preservation of paragraph organization and flow
- **Text quality**: Ensures high-quality text extraction with proper formatting
- **Context preservation**: Validates preservation of text context and meaning

**Tests Text Variety**: Paragraphs, sections, formatted text, and mixed content documents.

**Usage**: `python tests/test_paragraph_extraction.py`

#### `test_decimal_with_suffix.py`
**Decimal number with suffix extraction tests**:
- **Suffix pattern recognition**: Tests detection of numbers with suffixes (1.5x, 2.3k, etc.)
- **Pattern accuracy**: Validates accurate extraction of decimal-suffix combinations
- **Context preservation**: Ensures suffix meaning is preserved in extraction
- **Format variety**: Tests different suffix formats and patterns
- **Integration testing**: Tests suffix handling within the full processing pipeline

**Tests Suffix Variety**: Multiplier suffixes, unit suffixes, ratio indicators, and scaling factors.

**Usage**: `python tests/test_decimal_with_suffix.py`

### Web Interface Tests

#### `test_current_web_behavior.py`
**Current web interface behavior tests**:
- **Interface functionality**: Tests current web interface features and capabilities
- **User interaction**: Validates user interaction patterns and responses
- **Response validation**: Tests proper response formats and structures
- **Integration testing**: Validates integration between frontend and backend
- **Behavior consistency**: Ensures consistent behavior across different scenarios

**Tests Web Interface Variety**: User interactions, response formats, integration patterns, and behavior scenarios.

**Usage**: `python tests/test_current_web_behavior.py`

#### `test_web_interface_display.py`
**Web interface display and rendering tests**:
- **Display formatting**: Tests proper formatting and display of processed data
- **Visual presentation**: Validates visual presentation of tables and content
- **Responsive design**: Tests interface responsiveness across different screen sizes
- **Data visualization**: Validates proper visualization of extracted data
- **User experience**: Tests overall user experience and interface usability

**Tests Display Variety**: Data formatting, visual layouts, responsive design, and user experience elements.

**Usage**: `python tests/test_web_interface_display.py`

#### `test_web_interface_exact.py`
**Exact web interface functionality tests**:
- **Precise functionality**: Tests exact functionality requirements and specifications
- **Accuracy validation**: Validates precise accuracy of interface operations
- **Specification compliance**: Tests compliance with exact interface specifications
- **Edge case handling**: Validates handling of exact edge cases and scenarios
- **Quality assurance**: Ensures exact quality standards are met

**Tests Exact Variety**: Precise specifications, accuracy requirements, compliance standards, and quality metrics.

**Usage**: `python tests/test_web_interface_exact.py`

#### `test_web_interface_simulation.py`
**Web interface simulation and testing**:
- **Simulation scenarios**: Tests various simulation scenarios and use cases
- **Mock interactions**: Validates behavior with simulated user interactions
- **Testing automation**: Tests automated testing capabilities and scenarios
- **Scenario coverage**: Ensures comprehensive coverage of interaction scenarios
- **Simulation accuracy**: Validates accuracy of simulation results

**Tests Simulation Variety**: User scenarios, mock interactions, automated testing, and simulation accuracy.

**Usage**: `python tests/test_web_interface_simulation.py`

### Debug and Analysis Scripts

#### `debug_excel_file.py`
**Excel file debugging and analysis**:
- **File structure analysis**: Analyzes Excel file structure and organization
- **Data inspection**: Provides detailed inspection of Excel data and formatting
- **Issue identification**: Identifies potential issues with Excel file processing
- **Debug information**: Generates detailed debug information for troubleshooting
- **Processing validation**: Validates Excel file processing steps

**Debug Capabilities**: File structure, data content, formatting, processing steps, and issue identification.

**Usage**: `python tests/debug_excel_file.py`

#### `debug_simple_gap.py`
**Simple gap detection debugging**:
- **Gap analysis**: Analyzes gap detection logic and behavior
- **Detection validation**: Validates gap detection accuracy and performance
- **Debug output**: Provides detailed debug output for gap detection
- **Issue troubleshooting**: Helps troubleshoot gap detection issues
- **Algorithm testing**: Tests gap detection algorithm variations

**Debug Capabilities**: Gap detection logic, validation testing, debug output, and algorithm analysis.

**Usage**: `python tests/debug_simple_gap.py`

#### `debug_specific_table.py`
**Specific table debugging and analysis**:
- **Table structure analysis**: Analyzes specific table structures and layouts
- **Detection debugging**: Debugs table detection for specific scenarios
- **Processing validation**: Validates processing of specific table types
- **Issue identification**: Identifies issues with specific table processing
- **Detailed inspection**: Provides detailed inspection of table processing steps

**Debug Capabilities**: Table structure, detection logic, processing validation, and detailed inspection.

**Usage**: `python tests/debug_specific_table.py`

#### `debug_table_detection.py`
**Table detection debugging and optimization**:
- **Detection algorithm analysis**: Analyzes table detection algorithm performance
- **Method comparison**: Compares different table detection methods
- **Performance optimization**: Identifies optimization opportunities for detection
- **Accuracy validation**: Validates detection accuracy across scenarios
- **Algorithm tuning**: Helps tune detection algorithm parameters

**Debug Capabilities**: Algorithm analysis, method comparison, performance optimization, and accuracy validation.

**Usage**: `python tests/debug_table_detection.py`

#### `debug_table_regions.py`
**Table region debugging and validation**:
- **Region boundary analysis**: Analyzes table region boundary detection
- **Region validation**: Validates accuracy of detected table regions
- **Boundary optimization**: Optimizes table boundary detection logic
- **Region overlap detection**: Identifies and resolves region overlap issues
- **Spatial analysis**: Provides spatial analysis of table regions

**Debug Capabilities**: Boundary analysis, region validation, optimization, overlap detection, and spatial analysis.

**Usage**: `python tests/debug_table_regions.py`

#### `debug_test_data.py`
**Test data debugging and validation**:
- **Data structure analysis**: Analyzes test data structure and organization
- **Data validation**: Validates test data quality and consistency
- **Issue identification**: Identifies issues with test data
- **Data optimization**: Optimizes test data for better testing
- **Quality assurance**: Ensures test data quality standards

**Debug Capabilities**: Data structure, validation, issue identification, optimization, and quality assurance.

**Usage**: `python tests/debug_test_data.py`

#### `analyze_fixed_results.py`
**Fixed results analysis and comparison**:
- **Results comparison**: Compares results before and after fixes
- **Improvement analysis**: Analyzes improvements from fixes and optimizations
- **Performance metrics**: Provides performance metrics and comparisons
- **Quality assessment**: Assesses quality improvements from fixes
- **Impact analysis**: Analyzes impact of fixes on overall system performance

**Analysis Capabilities**: Results comparison, improvement analysis, performance metrics, and impact assessment.

**Usage**: `python tests/analyze_fixed_results.py`

#### `analyze_problem_sheet.py`
**Problem sheet analysis and diagnosis**:
- **Problem identification**: Identifies problems with specific sheets or scenarios
- **Root cause analysis**: Performs root cause analysis of identified problems
- **Solution recommendation**: Recommends solutions for identified problems
- **Impact assessment**: Assesses impact of problems on processing
- **Fix validation**: Validates effectiveness of applied fixes

**Analysis Capabilities**: Problem identification, root cause analysis, solution recommendation, and fix validation.

**Usage**: `python tests/analyze_problem_sheet.py`

### Utility and Helper Scripts

#### `check_frozen_panes.py`
**Frozen panes checking and validation**:
- **Frozen pane detection**: Detects frozen panes in Excel files
- **Configuration validation**: Validates frozen pane configuration
- **Coordinate conversion**: Converts frozen pane coordinates between formats
- **Integration testing**: Tests frozen pane integration with processing pipeline
- **Validation reporting**: Provides validation reports for frozen pane handling

**Utility Capabilities**: Detection, validation, coordinate conversion, integration testing, and reporting.

**Usage**: `python tests/check_frozen_panes.py`

#### `create_test_excel.py`
**Test Excel file creation utility**:
- **Test file generation**: Creates Excel files for testing scenarios
- **Data population**: Populates test files with various data patterns
- **Format configuration**: Configures Excel file formats and structures
- **Scenario setup**: Sets up specific testing scenarios in Excel files
- **Validation preparation**: Prepares Excel files for validation testing

**Creation Capabilities**: File generation, data population, format configuration, and scenario setup.

**Usage**: `python tests/create_test_excel.py`

#### `create_simple_test_pdf.py`
**Simple test PDF creation utility**:
- **PDF generation**: Creates simple PDF files for testing
- **Content setup**: Sets up PDF content for various testing scenarios
- **Table inclusion**: Includes tables in generated PDF files
- **Text content**: Adds text content for text extraction testing
- **Format configuration**: Configures PDF format and structure

**Creation Capabilities**: PDF generation, content setup, table inclusion, and format configuration.

**Usage**: `python tests/create_simple_test_pdf.py`

#### `create_test_pdf.py`
**Test PDF creation utility**:
- **Complex PDF generation**: Creates complex PDF files for comprehensive testing
- **Multi-content PDFs**: Generates PDFs with tables, text, and mixed content
- **Layout variety**: Creates PDFs with various layouts and structures
- **Content scenarios**: Sets up specific content scenarios for testing
- **Format validation**: Validates generated PDF formats and structures

**Creation Capabilities**: Complex PDF generation, multi-content setup, layout variety, and format validation.

**Usage**: `python tests/create_test_pdf.py`

### Excel File Creation and Testing Scripts

#### `create_test_frozen_panes_excel.py`
**Creates test Excel files with frozen panes for testing**:
- **Frozen panes setup**: Creates Excel files with 2 frozen rows and 1 frozen column
- **Multiple data sections**: Includes large gaps and different formatting that would normally trigger table detection
- **Real Excel format**: Generates actual .xlsx files for realistic testing scenarios
- **Data variety**: Includes headers, data rows, and multiple sections with different styling

**Creates**: `test_frozen_panes_override.xlsx` - Excel file with frozen panes and data patterns

**Usage**: `python tests/create_test_frozen_panes_excel.py`

#### `create_test_no_frozen_panes_excel.py`
**Creates test Excel files without frozen panes for testing**:
- **No frozen panes**: Creates Excel files with no frozen rows or columns
- **Multiple data sections**: Includes large gaps and different formatting that should trigger table detection
- **Real Excel format**: Generates actual .xlsx files for realistic testing scenarios
- **Data variety**: Includes multiple tables with different headers and styling

**Creates**: `test_no_frozen_panes.xlsx` - Excel file without frozen panes and multiple data sections

**Usage**: `python tests/create_test_no_frozen_panes_excel.py`

#### `test_real_frozen_panes_excel.py`
**Tests frozen panes behavior with real Excel files**:
- **Real file processing**: Tests the complete pipeline with actual Excel files
- **Frozen panes verification**: Validates that frozen panes are correctly detected and processed
- **Single table creation**: Confirms that exactly one table is created when frozen panes are present
- **Data inclusion verification**: Ensures all data sections are included in the single table
- **Detection method validation**: Verifies the detection method is marked as 'frozen_panes'

**Tests**: `test_frozen_panes_override.xlsx` - Excel file with frozen panes

**Usage**: `python tests/test_real_frozen_panes_excel.py`

#### `test_no_frozen_panes_excel.py`
**Tests table detection behavior with real Excel files without frozen panes**:
- **Real file processing**: Tests the complete pipeline with actual Excel files
- **Multiple table creation**: Confirms that multiple tables are created when no frozen panes are present
- **Detection method validation**: Verifies that detection methods other than 'frozen_panes' are used
- **Data separation verification**: Ensures data is properly separated into different tables
- **Gap detection validation**: Confirms that gap-based detection is working correctly

**Tests**: `test_no_frozen_panes.xlsx` - Excel file without frozen panes

**Usage**: `python tests/test_no_frozen_panes_excel.py`

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
- `test_complete_pipeline_result.json` - Complete pipeline processing results

#### PDF Processing Results
- `Test_PDF_Table_100_numbers_tables.json` - Large PDF table extraction results
- `Test_PDF_Table_9_numbers_with_before_and_after_paragraphs_tables.json` - PDF with mixed content results
- `Test_PDF_with_3_numbers_in_large_paragraphs_tables.json` - PDF text extraction results
- `test_table_100_numbers_tables.json` - Large table processing results

#### Web Interface Results
- `current_web_behavior_result.json` - Current web interface behavior results
- `web_interface_result.json` - Web interface processing results
- `web_interface_test.json` - Web interface test results

#### Data Files
- `test_data.json` - Test data for various scenarios
- `debug_excel_data.json` - Debug Excel data for analysis
- `target_table_output.json` - Target output format examples
- `test_excel_file.xlsx` - Test Excel file for processing
- `test_sample.html` - HTML sample for web interface testing

### Test JSON Data Directory

#### `test_JSON/` Subdirectory
**Centralized location for all JSON test data files used across the test suite**:

##### **Data Processing & Examples**
- `full_excel_data.json` (11MB) - Complete Excel file processing result containing full JSON representation of a real-world financial P&L spreadsheet
- `upload_result.json` (2.3MB) - Result of file upload processing through the web interface
- `api_request.json` (1.1MB) - Example API request payload for Excel processing endpoints

##### **PDF Processing Evolution**
- `synthetic_financial_report_tables.json` (101KB) - Original PDF processing result (baseline: 0 tables, 4 text sections, 62 numbers)
- `synthetic_financial_report_tables_fixed.json` (105KB) - First iteration of PDF processing improvements
- `synthetic_financial_report_tables_fixed_v2.json` (112KB) - Second iteration with enhanced table detection
- `synthetic_financial_report_tables_fixed_v3.json` (115KB) - Latest version with current PDF processing enhancements

##### **API Testing**
- `api_response.json` (62B) - Example API error response format

**Usage**: These files serve as development references, testing data, performance benchmarks, API documentation examples, and quality assurance data for testing system performance with real-world data sizes.

## Header and Column Label Variety Testing

The test suite comprehensively tests a wide variety of header and column labels:

### Business Context Headers
- **Product-related**: Product, Item, SKU, Description, Category
- **Financial**: Price, Cost, Revenue, Profit, Margin, Amount
- **Temporal**: Q1, Q2, Q3, Q4, Jan, Feb, Mar, Apr, May, Jun, 2023, 2024
- **Geographic**: Region, North, South, East, West, Country, State
- **Organizational**: Department, Division, Team, Manager, Employee
- **Status**: Active, Inactive, Pending, Completed, Cancelled

### Data Type Headers
- **Quantitative**: Quantity, Count, Number, Total, Sum, Average
- **Qualitative**: Status, Type, Category, Classification, Rating
- **Temporal**: Date, Time, Period, Duration, Deadline
- **Identifiers**: ID, Code, Reference, Serial Number, Batch

### Hierarchical Headers
- **Multi-level**: Q1→Jan/Feb, Electronics→Computers→Laptops
- **Indented**: Category→Subcategory→Product
- **Collapsed**: Multiple header rows combined into single headers

## Multiple Table Detection Testing

The test suite thoroughly tests multiple table detection scenarios:

### Same Sheet Multiple Tables
- **Adjacent tables**: Tables positioned next to each other
- **Separated tables**: Tables with gaps between them
- **Different sizes**: Tables of varying dimensions
- **Mixed content**: Tables with different header structures

### Table Boundary Detection
- **Clear boundaries**: Tables with obvious start/end points
- **Ambiguous boundaries**: Tables with unclear edges
- **Overlapping regions**: Complex scenarios with potential overlaps
- **Minimal tables**: Single cell or very small tables

### Table Type Variety
- **Data tables**: Standard data presentation tables
- **Summary tables**: Aggregated or calculated data
- **Reference tables**: Lookup or mapping tables
- **Form tables**: Input or configuration tables

### Multiple Table Test Variations

The test suite includes comprehensive variations for multiple table detection:

#### **Three Tables with Titles and Separations**
- **Sales Data Q1 2024**: Product sales with monthly breakdown
- **Inventory Status Report**: Stock levels and order status
- **Employee Performance Metrics**: Sales performance and ratings
- **Separation**: 2+ rows between each table
- **Title Preservation**: Bold titles with styling preserved

#### **Four Tables Spread Around Sheet**
- **Quarterly Revenue** (Top-left): Q1-Q4 revenue data
- **Monthly Expenses** (Top-right): Jan-Apr expense tracking
- **Product Categories** (Bottom-left): Category performance metrics
- **Regional Sales** (Bottom-right): Regional sales and growth data
- **Layout**: Tables positioned in different sheet quadrants

#### **Variable Size Tables with Different Separations**
- **Small Summary**: 2x2 table with basic metrics
- **Medium Detail Table**: 4x4 table with product details
- **Large Comprehensive Report**: 7x6 table with department budget analysis
- **Separations**: 3-4 rows between tables
- **Size Variety**: Tests different table dimensions

#### **Complex Titles and Metadata**
- **Financial Performance Report**: With subtitle and generation date
- **Department Budget Analysis**: With department info and contact details
- **Project Status Dashboard**: With version info and approval details
- **Metadata Preservation**: Subtitles, dates, contacts, versions, approvals

#### **Mixed Content and Formulas**
- **Sales Calculations**: Tables with Excel formulas (=B4*C4)
- **Special Data Report**: Tables with special characters (&, -, (), #)
- **Financial Summary**: Tables with dates, currency, and transaction types
- **Content Variety**: Numbers, text, dates, formulas, special characters

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

# Table detection tests
python tests/test_table_detection.py

# Frozen panes tests
python tests/test_frozen_panes.py

# Frozen panes table detection tests
python tests/test_frozen_panes_table_detection.py

# Multiple frozen rows tests
python tests/test_multiple_frozen_rows.py

# Style cleaning tests
python tests/test_style_cleaning.py

# Error message filtering tests
python tests/test_error_message_filtering.py

# Download functionality tests
python tests/test_download_functionality.py

# Table and paragraph detection tests
python tests/test_table_paragraph_detection.py
```

### Run Excel File Creation and Testing
```bash
# Create test Excel files
python tests/create_test_frozen_panes_excel.py
python tests/create_test_no_frozen_panes_excel.py

# Test with real Excel files
python tests/test_real_frozen_panes_excel.py
python tests/test_no_frozen_panes_excel.py

# Test enhanced gap detection
python tests/test_enhanced_gap_detection.py
```

### Test Coverage

The comprehensive test suite covers:

1. **Single Level Headers** - Basic table with simple headers
2. **Multi-Level Headers** - Hierarchical column headers (Q1→Jan/Feb, Q2→Apr/May)
3. **Indented Row Headers** - Hierarchical row headers with indentation
4. **Multiple Tables** - Multiple tables on the same sheet
5. **Merged Cells** - Tables with merged cells in headers
6. **Collapsed Headers** - Multiple column header rows that need collapsing
7. **Frozen Panes** - Tables with frozen rows and columns
8. **Frozen Panes Table Detection** - Override behavior for sheets with frozen panes
9. **Enhanced Gap Detection** - Smart table separation based on content type after gaps
10. **Style Cleaning** - Removal of default style values
11. **Error Filtering** - Detection and removal of error messages
12. **Download Handling** - Large file processing and download URLs
13. **Real Excel File Testing** - Testing with actual Excel files
14. **Table and Paragraph Detection** - PDF table and text content separation

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
- Tests cover a wide variety of real-world Excel scenarios and edge cases 