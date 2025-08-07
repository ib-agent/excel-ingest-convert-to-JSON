#!/usr/bin/env python3
"""
Save 360 Energy Test Baseline

This script saves the current processing results as a baseline for future regression testing.
It captures the exact metrics and characteristics that should be maintained.
"""

import json
import os
from datetime import datetime
from converter.compact_excel_processor import CompactExcelProcessor
from converter.compact_table_processor import CompactTableProcessor


def save_baseline():
    """Save the current processing results as a baseline"""
    test_file = '/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx'
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    processor = CompactExcelProcessor()
    table_processor = CompactTableProcessor()
    
    print("Processing 360 Energy file to create baseline...")
    
    # Process with and without filtering
    result_filtered = processor.process_file(test_file, filter_empty_trailing=True)
    result_unfiltered = processor.process_file(test_file, filter_empty_trailing=False)
    
    # Apply table detection
    tables_result = table_processor.transform_to_compact_table_format(result_filtered)
    
    # Calculate metrics
    baseline_data = {
        'timestamp': datetime.now().isoformat(),
        'file_path': test_file,
        'file_characteristics': {
            'total_sheets': len(result_filtered['workbook']['sheets']),
            'sheet_names': [sheet['name'] for sheet in result_filtered['workbook']['sheets']],
            'sheets_with_data': sum(1 for sheet in result_filtered['workbook']['sheets'] if len(sheet.get('rows', [])) > 0),
            'sheets_without_data': sum(1 for sheet in result_filtered['workbook']['sheets'] if len(sheet.get('rows', [])) == 0)
        },
        'filtering_performance': {},
        'table_detection': {},
        'detailed_metrics': {}
    }
    
    # Calculate filtering performance for each sheet
    filtered_sheets = {sheet['name']: sheet for sheet in result_filtered['workbook']['sheets']}
    unfiltered_sheets = {sheet['name']: sheet for sheet in result_unfiltered['workbook']['sheets']}
    
    total_filtered_cells = 0
    total_unfiltered_cells = 0
    
    for sheet_name in filtered_sheets.keys():
        filtered_sheet = filtered_sheets[sheet_name]
        unfiltered_sheet = unfiltered_sheets[sheet_name]
        
        filtered_dims = filtered_sheet.get('dimensions', [1, 1, 1, 1])
        unfiltered_dims = unfiltered_sheet.get('dimensions', [1, 1, 1, 1])
        
        filtered_cells = (filtered_dims[2] - filtered_dims[0] + 1) * (filtered_dims[3] - filtered_dims[1] + 1)
        unfiltered_cells = (unfiltered_dims[2] - unfiltered_dims[0] + 1) * (unfiltered_dims[3] - unfiltered_dims[1] + 1)
        
        total_filtered_cells += filtered_cells
        total_unfiltered_cells += unfiltered_cells
        
        # Count actual data cells
        data_cells = 0
        for row in filtered_sheet.get('rows', []):
            for cell in row.get('cells', []):
                if len(cell) >= 2 and cell[1] is not None and str(cell[1]).strip():
                    data_cells += 1
        
        baseline_data['detailed_metrics'][sheet_name] = {
            'filtered_dimensions': filtered_dims,
            'unfiltered_dimensions': unfiltered_dims,
            'filtered_addressable_cells': filtered_cells,
            'unfiltered_addressable_cells': unfiltered_cells,
            'actual_data_cells': data_cells,
            'reduction_ratio': 1 - (filtered_cells / unfiltered_cells) if unfiltered_cells > 0 else 0
        }
    
    baseline_data['filtering_performance'] = {
        'total_filtered_cells': total_filtered_cells,
        'total_unfiltered_cells': total_unfiltered_cells,
        'overall_reduction_ratio': 1 - (total_filtered_cells / total_unfiltered_cells),
        'major_reductions': sum(1 for metrics in baseline_data['detailed_metrics'].values() 
                               if metrics['reduction_ratio'] > 0.9)
    }
    
    # Calculate table detection metrics
    sheets_with_tables = 0
    total_tables = 0
    table_details = {}
    
    for sheet in tables_result['workbook']['sheets']:
        tables = sheet.get('tables', [])
        if tables:
            sheets_with_tables += 1
            total_tables += len(tables)
            
            table_details[sheet['name']] = {
                'table_count': len(tables),
                'table_titles': [table.get('title', 'No title') for table in tables]
            }
    
    baseline_data['table_detection'] = {
        'sheets_with_tables': sheets_with_tables,
        'total_tables_detected': total_tables,
        'table_details': table_details
    }
    
    # Save baseline
    baseline_file = '/Users/jeffwinner/excel-ingest-convert-to-JSON/tests/360_energy_baseline.json'
    with open(baseline_file, 'w') as f:
        json.dump(baseline_data, f, indent=2, default=str)
    
    print(f"✅ Baseline saved to: {baseline_file}")
    print(f"\nBaseline Summary:")
    print(f"  - Total sheets: {baseline_data['file_characteristics']['total_sheets']}")
    print(f"  - Sheets with data: {baseline_data['file_characteristics']['sheets_with_data']}")
    print(f"  - Overall reduction: {baseline_data['filtering_performance']['overall_reduction_ratio']:.1%}")
    print(f"  - Total addressable cells: {baseline_data['filtering_performance']['total_filtered_cells']:,}")
    print(f"  - Sheets with tables: {baseline_data['table_detection']['sheets_with_tables']}")
    print(f"  - Total tables detected: {baseline_data['table_detection']['total_tables_detected']}")
    
    return True


if __name__ == '__main__':
    success = save_baseline()
    if success:
        print("\n🎯 Baseline created successfully!")
        print("   This baseline can be used for future regression testing.")
    else:
        print("\n❌ Failed to create baseline")
        exit(1)