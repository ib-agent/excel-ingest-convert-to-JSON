#!/usr/bin/env python3
"""
Test PDF processing functionality and output
"""

import json
import logging
import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from converter.pdf.processing import PDFProcessor, PDFTableExtractor
from converter.pdf.processing_pdfplumber import PDFProcessor as DirectPDFProcessor, PDFTableExtractor as DirectPDFTableExtractor

def test_table_extraction():
    """Test table extraction functionality"""
    print("Testing PDF table extraction...")
    
    # Test configuration
    config = {
        'table_extraction': {
            'quality_threshold': 0.7,
            'min_table_size': 2
        }
    }
    
    output_file = None
    try:
        # Initialize processor
        processor = PDFProcessor(config)
        print("✓ PDFProcessor initialized successfully")
        
        # Use existing fixture PDF if available
        test_pdf_path = "tests/test_pdfs/Test_PDF_Table_100_numbers.pdf"
        
        if os.path.exists(test_pdf_path):
            print(f"Testing with: {test_pdf_path}")
            
            # Process PDF with tables only
            result = processor.process_file(test_pdf_path, extract_tables=True, extract_text=False, extract_numbers=False)
            
            # Validate result structure matches current schema
            assert "pdf_processing_result" in result
            assert "tables" in result["pdf_processing_result"]
            tables_obj = result["pdf_processing_result"]["tables"]
            assert "tables" in tables_obj and isinstance(tables_obj["tables"], list)
            
            print("✓ PDF processing completed successfully")
            print(f"✓ Tables extracted: {result['pdf_processing_result']['processing_summary']['tables_extracted']}")
            
            # Save result for inspection
            output_file = "test_table_extraction_result.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✓ Results saved to: {output_file}")
            
            # Print table details
            tables = result["pdf_processing_result"]["tables"]["tables"]
            for i, table in enumerate(tables):
                print(f"  Table {i+1}: {table['table_id']} (Quality: {table['metadata']['quality_score']:.2f})")
                print(f"    Columns: {len(table['columns'])}")
                print(f"    Rows: {len(table['rows'])}")
                print(f"    Page: {table['region']['page_number']}")
            
        else:
            pytest.skip(f"Test PDF not found: {test_pdf_path}")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  Please install required dependencies:")
        print("  pip install pdfplumber pandas")
        pytest.skip("Missing dependencies for PDF tests")
    except Exception as e:
        pytest.fail(f"Error during table extraction test: {e}")
    finally:
        if output_file and os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception:
                pass

def test_full_extraction():
    """Test full PDF extraction (tables, text, and numbers)"""
    print("\nTesting full PDF extraction (tables, text, and numbers)...")
    
    # Test configuration
    config = {
        'table_extraction': {
            'quality_threshold': 0.6,
            'min_table_size': 2
        },
        'text_extraction': {
            'extract_metadata': True,
            'preserve_formatting': True,
            'section_detection': {
                'min_words_per_section': 5,  # Lower for testing
                'max_words_per_section': 1000,
                'use_headers': True
            }
        },
        'number_extraction': {
            'patterns': {
                'integer': r'\b\d{1,3}(?:,\d{3})*\b',
                'decimal': r'\b\d+\.\d+\b',
                'percentage': r'\b\d+(?:\.\d+)?%\b',
                'currency': r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',
                'scientific_notation': r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b'
            },
            'context_window': 50,  # Smaller for testing
            'confidence_threshold': 0.5  # Lower for testing
        }
    }
    
    output_file = None
    try:
        # Initialize processor
        processor = PDFProcessor(config)
        print("✓ PDFProcessor initialized successfully")
        
        # Use existing fixture PDF if available
        test_pdf_path = "tests/test_pdfs/Test_PDF_Table_9_numbers.pdf"
        
        if os.path.exists(test_pdf_path):
            print(f"Testing with: {test_pdf_path}")
            
            # Process PDF with all extraction types
            result = processor.process_file(
                test_pdf_path, 
                extract_tables=True, 
                extract_text=True, 
                extract_numbers=True
            )
            
            # Validate result structure matches current schema
            assert "pdf_processing_result" in result
            assert "tables" in result["pdf_processing_result"]
            assert "text_content" in result["pdf_processing_result"]
            # Numbers are summarized in processing_summary; detailed structure may vary
            summary = result["pdf_processing_result"].get("processing_summary", {})
            assert "numbers_found" in summary
            
            print("✓ Full PDF processing completed successfully")
            print(f"✓ Tables extracted: {result['pdf_processing_result']['processing_summary']['tables_extracted']}")
            print(f"✓ Text sections: {result['pdf_processing_result']['processing_summary']['text_sections']}")
            print(f"✓ Numbers found: {result['pdf_processing_result']['processing_summary']['numbers_found']}")
            # Overall quality may not be present in all runs; print if available
            oq = result['pdf_processing_result']['processing_summary'].get('overall_quality_score')
            if oq is not None:
                print(f"✓ Overall quality: {oq:.2f}")
            
            # Save result for inspection
            output_file = "test_full_extraction_result.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✓ Results saved to: {output_file}")
            
            # Print detailed statistics
            print("\nDetailed Statistics:")
            
            # Table statistics
            tables = result["pdf_processing_result"]["tables"]["tables"]
            if tables:
                print(f"  Tables: {len(tables)} found")
                for i, table in enumerate(tables):
                    print(f"    Table {i+1}: {table['table_id']} (Quality: {table['metadata']['quality_score']:.2f})")
            
            # Text statistics
            text_content = result["pdf_processing_result"]["text_content"]
            if text_content:
                summary = text_content["text_content"]["summary"]
                print(f"  Text: {summary['total_sections']} sections, {summary['total_words']} words")
                print(f"    LLM-ready sections: {summary['llm_ready_sections']}")
                print(f"    Average section length: {summary['average_section_length']:.1f} words")
            
                # Number statistics (if detailed structure present)
                numbers = result["pdf_processing_result"].get("numbers_in_text")
                if numbers and isinstance(numbers, dict):
                    summary = numbers.get("numbers_in_text", {}).get("summary", {})
                    if summary:
                        print(f"  Numbers: {summary.get('total_numbers_found', 0)} found")
                        for format_type, count in summary.get('numbers_by_format', {}).items():
                            if count > 0:
                                print(f"    {format_type}: {count}")
            
        else:
            pytest.skip(f"Test PDF not found: {test_pdf_path}")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  Please install required dependencies:")
        print("  pip install pdfplumber pandas")
        pytest.skip("Missing dependencies for PDF tests")
    except Exception as e:
        pytest.fail(f"Error during full extraction test: {e}")
    finally:
        if output_file and os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception:
                pass

def test_table_extractor_directly():
    """Test PDFTableExtractor directly"""
    print("\nTesting PDFTableExtractor directly...")
    
    try:
        # Initialize table extractor
        config = {
            'quality_threshold': 0.6,
            'min_table_size': 2
        }
        
        # Use direct PDFPlumber-backed extractor for configuration assertions
        extractor = DirectPDFTableExtractor({'table_extraction': config})
        print("✓ PDFTableExtractor initialized successfully")
        
        # Test configuration
        assert hasattr(extractor.processor.table_extractor, 'quality_threshold')
        assert extractor.processor.table_extractor.quality_threshold == 0.6
        assert extractor.processor.table_extractor.min_table_size == 2
        print("✓ Configuration applied correctly")
        
    except ImportError as e:
        pytest.skip(f"Import error: {e}")
    except Exception as e:
        pytest.fail(f"Error during table extractor test: {e}")

def test_configuration():
    """Test configuration handling"""
    print("\nTesting configuration handling...")
    
    try:
        # Test with custom configuration
        custom_config = {
            'table_extraction': {
                'quality_threshold': 0.9,
                'min_table_size': 10
            }
        }
        
        # Use direct processor for internal configuration visibility
        processor = DirectPDFProcessor(custom_config)
        
        # Verify custom config is applied on underlying pdfplumber table extractor
        inner_extractor = processor.table_extractor.processor.table_extractor
        assert hasattr(inner_extractor, 'quality_threshold')
        assert inner_extractor.quality_threshold == 0.9
        assert inner_extractor.min_table_size == 10
        print("✓ Custom configuration applied correctly")
        
        # Test with default configuration
        processor_default = DirectPDFProcessor()
        inner_default = processor_default.table_extractor.processor.table_extractor
        assert hasattr(inner_default, 'quality_threshold')
        assert inner_default.quality_threshold >= 0.6
        print("✓ Default configuration applied correctly")
        
    except Exception as e:
        pytest.fail(f"Error during configuration test: {e}")

def create_sample_pdf():
    """Create a simple sample PDF for testing"""
    print("\nCreating sample PDF for testing...")
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a simple PDF with a table
        pdf_path = "sample.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "Sample Table")
        
        # Draw table grid
        c.setFont("Helvetica", 12)
        
        # Table data
        data = [
            ["Product", "Q1", "Q2", "Q3", "Q4"],
            ["Widget A", "100", "150", "200", "250"],
            ["Widget B", "75", "125", "175", "225"],
            ["Widget C", "50", "100", "150", "200"]
        ]
        
        # Table dimensions
        start_x, start_y = 100, height - 200
        cell_width, cell_height = 80, 25
        
        # Draw table
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                x = start_x + j * cell_width
                y = start_y - i * cell_height
                
                # Draw cell border
                c.rect(x, y, cell_width, cell_height)
                
                # Add text
                c.drawString(x + 5, y + 8, str(cell))
        
        c.save()
        print(f"✓ Sample PDF created: {pdf_path}")
        return True
        
    except ImportError:
        print("⚠ reportlab not available. Install with: pip install reportlab")
        return False
    except Exception as e:
        print(f"✗ Error creating sample PDF: {e}")
        return False

def main():
    """Main test function"""
    print("PDF Processing Test Suite")
    print("=" * 50)
    
    # Test configuration handling
    config_success = test_configuration()
    
    # Test table extractor
    extractor_success = test_table_extractor_directly()
    
    # Create sample PDF if needed
    sample_created = create_sample_pdf()
    
    # Test table extraction only
    if sample_created:
        table_extraction_success = test_table_extraction()
        full_extraction_success = test_full_extraction()
    else:
        print("\n⚠ Skipping extraction tests (no sample PDF)")
        table_extraction_success = True
        full_extraction_success = True
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Configuration: {'✓ PASS' if config_success else '✗ FAIL'}")
    print(f"Table Extractor: {'✓ PASS' if extractor_success else '✗ FAIL'}")
    print(f"Sample PDF: {'✓ CREATED' if sample_created else '✗ FAILED'}")
    print(f"Table Extraction: {'✓ PASS' if table_extraction_success else '✗ FAIL'}")
    print(f"Full Extraction: {'✓ PASS' if full_extraction_success else '✗ FAIL'}")
    
    if all([config_success, extractor_success, table_extraction_success, full_extraction_success]):
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 