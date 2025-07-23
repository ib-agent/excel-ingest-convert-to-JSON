#!/usr/bin/env python3
"""
Test script to verify style cleaning rules for removing default values
"""

import sys
import os
import unittest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from converter.table_processor import TableProcessor


class TestStyleCleaning(unittest.TestCase):
    """Test cases for style cleaning functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.table_processor = TableProcessor()
    
    def test_clean_fill_data_removes_default_values(self):
        """Test that fill data with default values (00000000, tint 0.0) is removed"""
        # Test data with default fill values
        default_fill_data = {
            'fill_type': 'solid',
            'start_color': {
                'rgb': '00000000',
                'tint': 0.0
            },
            'end_color': {
                'rgb': '00000000',
                'tint': 0.0
            }
        }
        
        # Clean the fill data
        cleaned_fill = self.table_processor._clean_fill_data(default_fill_data)
        
        # Should return empty dict since it's all default values
        self.assertEqual(cleaned_fill, {}, 
                        f"Expected empty dict for default fill, got {cleaned_fill}")
    
    def test_clean_fill_data_keeps_non_default_values(self):
        """Test that fill data with non-default values is preserved"""
        # Test data with non-default fill values
        non_default_fill_data = {
            'fill_type': 'solid',
            'start_color': {
                'rgb': 'FF0000',
                'tint': 0.5
            },
            'end_color': {
                'rgb': '00FF00',
                'tint': 0.2
            }
        }
        
        # Clean the fill data
        cleaned_fill = self.table_processor._clean_fill_data(non_default_fill_data)
        
        # Should preserve the non-default values
        self.assertNotEqual(cleaned_fill, {}, 
                           "Non-default fill data should not be empty")
        self.assertIn('fill_type', cleaned_fill)
        self.assertIn('start_color', cleaned_fill)
        self.assertIn('end_color', cleaned_fill)
        self.assertEqual(cleaned_fill['start_color']['rgb'], 'FF0000')
        self.assertEqual(cleaned_fill['start_color']['tint'], 0.5)
    
    def test_clean_fill_data_mixed_default_and_non_default(self):
        """Test that fill data with mixed default and non-default values is handled correctly"""
        # Test data with one default and one non-default color
        mixed_fill_data = {
            'fill_type': 'solid',
            'start_color': {
                'rgb': '00000000',
                'tint': 0.0
            },
            'end_color': {
                'rgb': 'FF0000',
                'tint': 0.5
            }
        }
        
        # Clean the fill data
        cleaned_fill = self.table_processor._clean_fill_data(mixed_fill_data)
        
        # Should still be removed because start_color is default
        self.assertEqual(cleaned_fill, {}, 
                        f"Expected empty dict for mixed fill with default start_color, got {cleaned_fill}")
    
    def test_clean_alignment_data_removes_default_values(self):
        """Test that alignment data with default values (0, 0.0, False) is removed"""
        # Test data with default alignment values
        default_alignment_data = {
            'horizontal': 0,
            'vertical': 0,
            'text_rotation': 0.0,
            'wrap_text': False,
            'shrink_to_fit': False,
            'indent': 0,
            'relative_indent': 0,
            'justify_last_line': False,
            'reading_order': 0
        }
        
        # Clean the alignment data
        cleaned_alignment = self.table_processor._clean_alignment_data(default_alignment_data)
        
        # Should return empty dict since all values are default
        self.assertEqual(cleaned_alignment, {}, 
                        f"Expected empty dict for default alignment, got {cleaned_alignment}")
    
    def test_clean_alignment_data_keeps_non_default_values(self):
        """Test that alignment data with non-default values is preserved"""
        # Test data with non-default alignment values
        non_default_alignment_data = {
            'horizontal': 'center',
            'vertical': 'top',
            'text_rotation': 45.0,
            'wrap_text': True,
            'shrink_to_fit': True,
            'indent': 2,
            'relative_indent': 1,
            'justify_last_line': True,
            'reading_order': 1
        }
        
        # Clean the alignment data
        cleaned_alignment = self.table_processor._clean_alignment_data(non_default_alignment_data)
        
        # Should preserve the non-default values
        self.assertNotEqual(cleaned_alignment, {}, 
                           "Non-default alignment data should not be empty")
        self.assertEqual(cleaned_alignment['horizontal'], 'center')
        self.assertEqual(cleaned_alignment['vertical'], 'top')
        self.assertEqual(cleaned_alignment['text_rotation'], 45.0)
        self.assertTrue(cleaned_alignment['wrap_text'])
        self.assertTrue(cleaned_alignment['shrink_to_fit'])
        self.assertEqual(cleaned_alignment['indent'], 2)
        self.assertEqual(cleaned_alignment['relative_indent'], 1)
        self.assertTrue(cleaned_alignment['justify_last_line'])
        self.assertEqual(cleaned_alignment['reading_order'], 1)
    
    def test_clean_alignment_data_mixed_default_and_non_default(self):
        """Test that alignment data with mixed default and non-default values is handled correctly"""
        # Test data with some default and some non-default values
        mixed_alignment_data = {
            'horizontal': 0,  # default
            'vertical': 'top',  # non-default
            'text_rotation': 0.0,  # default
            'wrap_text': True,  # non-default
            'shrink_to_fit': False,  # default
            'indent': 0,  # default
            'relative_indent': 0,  # default
            'justify_last_line': False,  # default
            'reading_order': 0  # default
        }
        
        # Clean the alignment data
        cleaned_alignment = self.table_processor._clean_alignment_data(mixed_alignment_data)
        
        # Should only keep non-default values
        self.assertNotEqual(cleaned_alignment, {}, 
                           "Mixed alignment data should not be empty")
        self.assertIn('vertical', cleaned_alignment)
        self.assertIn('wrap_text', cleaned_alignment)
        self.assertNotIn('horizontal', cleaned_alignment)
        self.assertNotIn('text_rotation', cleaned_alignment)
        self.assertNotIn('shrink_to_fit', cleaned_alignment)
        self.assertNotIn('indent', cleaned_alignment)
        self.assertNotIn('relative_indent', cleaned_alignment)
        self.assertNotIn('justify_last_line', cleaned_alignment)
        self.assertNotIn('reading_order', cleaned_alignment)
        
        self.assertEqual(cleaned_alignment['vertical'], 'top')
        self.assertTrue(cleaned_alignment['wrap_text'])
    
    def test_clean_style_data_integration(self):
        """Test that style data cleaning works correctly with fill and alignment"""
        # Test complete style data with default values
        style_data = {
            'font': {
                'name': 'Arial',
                'size': 12,
                'bold': False
            },
            'fill': {
                'fill_type': 'solid',
                'start_color': {
                    'rgb': '00000000',
                    'tint': 0.0
                }
            },
            'alignment': {
                'horizontal': 0,
                'vertical': 0,
                'text_rotation': 0.0,
                'wrap_text': False
            },
            'border': {
                'left': {
                    'style': 'thin',
                    'color': {'rgb': '000000'}
                }
            }
        }
        
        # Clean the style data
        cleaned_style = self.table_processor._clean_style_data(style_data)
        
        # Should remove fill and alignment sections but keep font and border
        self.assertIn('font', cleaned_style)
        self.assertIn('border', cleaned_style)
        self.assertNotIn('fill', cleaned_style, "Fill section should be removed")
        self.assertNotIn('alignment', cleaned_style, "Alignment section should be removed")
        
        # Font should be preserved
        self.assertEqual(cleaned_style['font']['name'], 'Arial')
        self.assertEqual(cleaned_style['font']['size'], 12)
        
        # Border should be preserved
        self.assertIn('left', cleaned_style['border'])


def run_tests():
    """Run the test suite"""
    print("=== RUNNING STYLE CLEANING TESTS ===")
    unittest.main(verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests() 