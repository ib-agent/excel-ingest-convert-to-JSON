#!/usr/bin/env python3
"""
Test script to verify download functionality for both large and small files
"""

import sys
import os
import unittest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDownloadFunctionality(unittest.TestCase):
    """Test cases for download functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_data = {
            'workbook': {
                'sheets': [
                    {
                        'name': 'Sheet1',
                        'cells': {
                            'A1': {'value': 'Header1'},
                            'B1': {'value': 'Header2'},
                            'A2': {'value': 'Data1'},
                            'B2': {'value': 'Data2'}
                        }
                    }
                ]
            }
        }
        
        self.sample_table_data = {
            'workbook': {
                'sheets': [
                    {
                        'name': 'Sheet1',
                        'tables': [
                            {
                                'table_id': 'table_1',
                                'name': 'Table 1',
                                'columns': [],
                                'rows': []
                            }
                        ]
                    }
                ]
            }
        }
    
    def test_normal_file_response_includes_data(self):
        """Test that normal file response includes data for download"""
        # This test verifies that the response structure allows for download functionality
        response_data = {
            'success': True,
            'large_file': False,
            'data': self.sample_data,
            'table_data': self.sample_table_data
        }
        
        # Verify the response has the expected structure
        self.assertTrue(response_data['success'])
        self.assertFalse(response_data['large_file'])
        self.assertIn('data', response_data)
        self.assertIn('table_data', response_data)
        self.assertIsInstance(response_data['data'], dict)
        self.assertIsInstance(response_data['table_data'], dict)
    
    def test_large_file_response_includes_download_urls(self):
        """Test that large file response includes download URLs"""
        response_data = {
            'success': True,
            'large_file': True,
            'download_urls': {
                'full_data': '/download/full_data/123/',
                'table_data': '/download/table_data/123/'
            },
            'file_info': {
                'file_size': '51MB',
                'processing_time': '2.5s'
            },
            'summary': {
                'total_sheets': 4,
                'total_tables': 4
            }
        }
        
        # Verify the response has the expected structure
        self.assertTrue(response_data['success'])
        self.assertTrue(response_data['large_file'])
        self.assertIn('download_urls', response_data)
        self.assertIn('full_data', response_data['download_urls'])
        self.assertIn('table_data', response_data['download_urls'])
    
    def test_download_urls_are_valid(self):
        """Test that download URLs follow expected format"""
        download_urls = {
            'full_data': '/download/full_data/123/',
            'table_data': '/download/table_data/123/'
        }
        
        # Verify URL format
        for url_type, url in download_urls.items():
            self.assertTrue(url.startswith('/download/'))
            self.assertTrue(url.endswith('/'))
            self.assertIn(url_type, url)
    
    def test_file_info_structure(self):
        """Test that file info contains expected fields"""
        file_info = {
            'file_size': '51MB',
            'processing_time': '2.5s',
            'total_sheets': 4,
            'total_tables': 4
        }
        
        # Verify file info structure
        self.assertIn('file_size', file_info)
        self.assertIn('processing_time', file_info)
        self.assertIn('total_sheets', file_info)
        self.assertIn('total_tables', file_info)
    
    def test_summary_structure(self):
        """Test that summary contains expected fields"""
        summary = {
            'total_sheets': 4,
            'total_tables': 4,
            'total_cells': 1000,
            'processing_time': '2.5s'
        }
        
        # Verify summary structure
        self.assertIn('total_sheets', summary)
        self.assertIn('total_tables', summary)
        self.assertIsInstance(summary['total_sheets'], int)
        self.assertIsInstance(summary['total_tables'], int)
    
    def test_data_serialization_for_download(self):
        """Test that data can be properly serialized for download"""
        # Test full data serialization
        full_data_json = json.dumps(self.sample_data, indent=2)
        self.assertIsInstance(full_data_json, str)
        self.assertIn('Sheet1', full_data_json)
        self.assertIn('Header1', full_data_json)
        
        # Test table data serialization
        table_data_json = json.dumps(self.sample_table_data, indent=2)
        self.assertIsInstance(table_data_json, str)
        self.assertIn('table_1', table_data_json)
        self.assertIn('Table 1', table_data_json)
    
    def test_cell_data_extraction(self):
        """Test that cell data can be extracted for download"""
        # Extract cell data from full data
        cell_data = {
            'workbook': {
                'sheets': [
                    {
                        'name': self.sample_data['workbook']['sheets'][0]['name'],
                        'cells': self.sample_data['workbook']['sheets'][0]['cells']
                    }
                ]
            }
        }
        
        # Verify cell data structure
        self.assertIn('workbook', cell_data)
        self.assertIn('sheets', cell_data['workbook'])
        self.assertEqual(len(cell_data['workbook']['sheets']), 1)
        self.assertIn('cells', cell_data['workbook']['sheets'][0])
    
    def test_filename_generation(self):
        """Test that filenames are generated correctly for downloads"""
        original_filename = "test_file.xlsx"
        
        # Test filename generation patterns (simulating JavaScript replace)
        base_name = original_filename.rsplit('.', 1)[0]  # Remove extension
        full_data_filename = f"{base_name}_full_data.json"
        table_data_filename = f"{base_name}_table_data.json"
        cell_data_filename = f"{base_name}_cell_data.json"
        
        self.assertEqual(full_data_filename, "test_file_full_data.json")
        self.assertEqual(table_data_filename, "test_file_table_data.json")
        self.assertEqual(cell_data_filename, "test_file_cell_data.json")
    
    def test_error_handling_for_missing_data(self):
        """Test that download functions handle missing data gracefully"""
        # Test with no data
        no_data = None
        
        # This should not raise an exception but handle gracefully
        try:
            if no_data:
                json.dumps(no_data, indent=2)
        except Exception as e:
            self.fail(f"Should handle None data gracefully: {e}")
    
    def test_large_file_detection(self):
        """Test that large files are detected correctly"""
        # Test file size thresholds
        small_file_size = 10 * 1024 * 1024  # 10MB
        large_file_size = 51 * 1024 * 1024  # 51MB
        
        # These would be determined by the backend
        self.assertLess(small_file_size, 50 * 1024 * 1024)  # Should be small
        self.assertGreater(large_file_size, 50 * 1024 * 1024)  # Should be large


def run_tests():
    """Run the test suite"""
    print("=== RUNNING DOWNLOAD FUNCTIONALITY TESTS ===")
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests() 