#!/usr/bin/env python3
"""
Test script to verify error message filtering functionality
"""

import sys
import os
import unittest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.table_processor import TableProcessor


class TestErrorMessageFiltering(unittest.TestCase):
    """Test cases for error message filtering functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.table_processor = TableProcessor()
    
    def test_is_error_message_detects_error_patterns(self):
        """Test that _is_error_message correctly identifies error patterns"""
        # Test specific error message mentioned by user
        self.assertTrue(self.table_processor._is_error_message("Values must be of type "))
        self.assertTrue(self.table_processor._is_error_message("values must be of type"))
        self.assertTrue(self.table_processor._is_error_message("theme: Values must be of type "))
        
        # Test other common error patterns
        self.assertTrue(self.table_processor._is_error_message("Invalid data"))
        self.assertTrue(self.table_processor._is_error_message("Error occurred"))
        self.assertTrue(self.table_processor._is_error_message("Exception thrown"))
        self.assertTrue(self.table_processor._is_error_message("Failed to process"))
        self.assertTrue(self.table_processor._is_error_message("Not found"))
        self.assertTrue(self.table_processor._is_error_message("Undefined variable"))
        self.assertTrue(self.table_processor._is_error_message("Type error"))
        self.assertTrue(self.table_processor._is_error_message("Validation error"))
        self.assertTrue(self.table_processor._is_error_message("Parse error"))
        self.assertTrue(self.table_processor._is_error_message("Runtime error"))
        self.assertTrue(self.table_processor._is_error_message("Missing required field"))
        self.assertTrue(self.table_processor._is_error_message("Cannot process"))
        self.assertTrue(self.table_processor._is_error_message("Unable to convert"))
        self.assertTrue(self.table_processor._is_error_message("Unexpected value"))
        self.assertTrue(self.table_processor._is_error_message("Unrecognized format"))
        self.assertTrue(self.table_processor._is_error_message("Unknown type"))
        self.assertTrue(self.table_processor._is_error_message("Unsupported operation"))
        self.assertTrue(self.table_processor._is_error_message("Deprecated method"))
        self.assertTrue(self.table_processor._is_error_message("Obsolete function"))
        self.assertTrue(self.table_processor._is_error_message("Placeholder text"))
        self.assertTrue(self.table_processor._is_error_message("TODO: fix this"))
        self.assertTrue(self.table_processor._is_error_message("FIXME: implement"))
        self.assertTrue(self.table_processor._is_error_message("Bug in code"))
        self.assertTrue(self.table_processor._is_error_message("Issue with data"))
        self.assertTrue(self.table_processor._is_error_message("Problem detected"))
    
    def test_is_error_message_detects_incomplete_patterns(self):
        """Test that _is_error_message detects incomplete error patterns"""
        self.assertTrue(self.table_processor._is_error_message("of type"))
        self.assertTrue(self.table_processor._is_error_message("must be"))
        self.assertTrue(self.table_processor._is_error_message("..."))
        self.assertTrue(self.table_processor._is_error_message("---"))
        self.assertTrue(self.table_processor._is_error_message("***"))
        self.assertTrue(self.table_processor._is_error_message("!!!"))
        self.assertTrue(self.table_processor._is_error_message("???"))
    
    def test_is_error_message_ignores_valid_data(self):
        """Test that _is_error_message correctly ignores valid data"""
        # Valid strings should not be flagged as errors
        self.assertFalse(self.table_processor._is_error_message("Normal text"))
        self.assertFalse(self.table_processor._is_error_message("123"))
        self.assertFalse(self.table_processor._is_error_message("2023-01-01"))
        self.assertFalse(self.table_processor._is_error_message("Product Name"))
        self.assertFalse(self.table_processor._is_error_message("Sales Data"))
        self.assertFalse(self.table_processor._is_error_message("Jan"))
        self.assertFalse(self.table_processor._is_error_message("Q1"))
        self.assertFalse(self.table_processor._is_error_message("Total"))
        self.assertFalse(self.table_processor._is_error_message("Revenue"))
        self.assertFalse(self.table_processor._is_error_message("Cost"))
        self.assertFalse(self.table_processor._is_error_message("Profit"))
        self.assertFalse(self.table_processor._is_error_message("Margin"))
        self.assertFalse(self.table_processor._is_error_message("Growth"))
        self.assertFalse(self.table_processor._is_error_message("Percentage"))
        self.assertFalse(self.table_processor._is_error_message("Amount"))
        self.assertFalse(self.table_processor._is_error_message("Date"))
        self.assertFalse(self.table_processor._is_error_message("Time"))
        self.assertFalse(self.table_processor._is_error_message("Status"))
        self.assertFalse(self.table_processor._is_error_message("Active"))
        self.assertFalse(self.table_processor._is_error_message("Inactive"))
        self.assertFalse(self.table_processor._is_error_message("Pending"))
        self.assertFalse(self.table_processor._is_error_message("Completed"))
        self.assertFalse(self.table_processor._is_error_message("Cancelled"))
    
    def test_is_error_message_handles_edge_cases(self):
        """Test that _is_error_message handles edge cases correctly"""
        # Non-string values should return False
        self.assertFalse(self.table_processor._is_error_message(None))
        self.assertFalse(self.table_processor._is_error_message(123))
        self.assertFalse(self.table_processor._is_error_message(True))
        self.assertFalse(self.table_processor._is_error_message(False))
        self.assertFalse(self.table_processor._is_error_message([]))
        self.assertFalse(self.table_processor._is_error_message({}))
        
        # Empty strings should not be flagged as errors
        self.assertFalse(self.table_processor._is_error_message(""))
        self.assertFalse(self.table_processor._is_error_message("   "))
        
        # Case insensitive matching
        self.assertTrue(self.table_processor._is_error_message("ERROR"))
        self.assertTrue(self.table_processor._is_error_message("Error"))
        self.assertTrue(self.table_processor._is_error_message("error"))
        self.assertTrue(self.table_processor._is_error_message("ErRoR"))
    
    def test_clean_table_json_removes_error_messages(self):
        """Test that _clean_table_json removes error messages from the output"""
        # Test data with error messages
        test_data = {
            'valid_field': 'Normal data',
            'error_field': 'Values must be of type ',
            'another_error': 'Invalid data format',
            'normal_field': 'More valid data',
            'nested': {
                'valid_nested': 'Nested valid data',
                'error_nested': 'Exception occurred',
                'deep_nested': {
                    'deep_error': 'Failed to process',
                    'deep_valid': 'Deep valid data'
                }
            },
            'list_data': [
                'Valid list item',
                'Error in list',
                'Another valid item'
            ]
        }
        
        # Clean the data
        cleaned_data = self.table_processor._clean_table_json(test_data)
        
        # Should remove error fields but keep valid data
        self.assertIn('valid_field', cleaned_data)
        self.assertIn('normal_field', cleaned_data)
        self.assertNotIn('error_field', cleaned_data)
        self.assertNotIn('another_error', cleaned_data)
        
        # Nested data should also be cleaned
        self.assertIn('nested', cleaned_data)
        nested = cleaned_data['nested']
        self.assertIn('valid_nested', nested)
        self.assertNotIn('error_nested', nested)
        
        # Deep nested data should be cleaned
        self.assertIn('deep_nested', nested)
        deep_nested = nested['deep_nested']
        self.assertIn('deep_valid', deep_nested)
        self.assertNotIn('deep_error', deep_nested)
        
        # List data should be cleaned
        self.assertIn('list_data', cleaned_data)
        list_data = cleaned_data['list_data']
        self.assertIn('Valid list item', list_data)
        self.assertIn('Another valid item', list_data)
        self.assertNotIn('Error in list', list_data)
    
    def test_clean_table_json_preserves_valid_data(self):
        """Test that _clean_table_json preserves all valid data"""
        # Test data with only valid content
        test_data = {
            'string_field': 'Normal text',
            'number_field': 123,
            'boolean_field': True,
            'date_field': '2023-01-01',
            'nested_valid': {
                'product': 'Product Name',
                'sales': 1000,
                'active': True
            },
            'valid_list': [
                'Jan',
                'Feb',
                'Mar'
            ]
        }
        
        # Clean the data
        cleaned_data = self.table_processor._clean_table_json(test_data)
        
        # All valid data should be preserved
        self.assertEqual(cleaned_data['string_field'], 'Normal text')
        self.assertEqual(cleaned_data['number_field'], 123)
        self.assertEqual(cleaned_data['boolean_field'], True)
        self.assertEqual(cleaned_data['date_field'], '2023-01-01')
        
        # Nested data should be preserved
        self.assertEqual(cleaned_data['nested_valid']['product'], 'Product Name')
        self.assertEqual(cleaned_data['nested_valid']['sales'], 1000)
        self.assertEqual(cleaned_data['nested_valid']['active'], True)
        
        # List data should be preserved
        self.assertEqual(cleaned_data['valid_list'], ['Jan', 'Feb', 'Mar'])


def run_tests():
    """Run the test suite"""
    print("=== RUNNING ERROR MESSAGE FILTERING TESTS ===")
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests() 