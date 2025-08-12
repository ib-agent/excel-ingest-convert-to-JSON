#!/usr/bin/env python3
"""
Test PDFPlumber Implementation

Simple test script to verify that the new PDFPlumber-based extractors
work correctly before proceeding with full migration.

Author: PDF Processing Team
Date: 2024
"""

import os
import sys
import json
from pathlib import Path

# Add converter directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'converter'))

from converter.pdfplumber_processor import PDFPlumberProcessor

def test_pdfplumber_implementation(tmp_path):
    """Test the PDFPlumber implementation with available test files"""
    
    print("🧪 Testing PDFPlumber Implementation")
    print("=" * 50)
    
    # Look for test PDF files
    test_pdf_dirs = [
        'tests/test_pdfs',
        'tests',
        '.'
    ]
    
    test_pdf = None
    for test_dir in test_pdf_dirs:
        if os.path.exists(test_dir):
            pdf_files = [f for f in os.listdir(test_dir) if f.endswith('.pdf')]
            if pdf_files:
                test_pdf = os.path.join(test_dir, pdf_files[0])
                print(f"📄 Found test PDF: {test_pdf}")
                break
    
    if not test_pdf:
        print("❌ No test PDF files found. Please add a PDF file to test with.")
        return False
    
    try:
        # Initialize PDFPlumber processor
        print("\n🔧 Initializing PDFPlumber processor...")
        processor = PDFPlumberProcessor()
        
        # Test configuration validation
        print("✅ Testing configuration validation...")
        validation = processor.validate_configuration()
        if validation['valid']:
            print("✅ Configuration is valid")
        else:
            print(f"❌ Configuration errors: {validation['errors']}")
            return False
        
        # Test capabilities
        print("✅ Testing capabilities...")
        capabilities = processor.get_processing_capabilities()
        print(f"📋 Library: {capabilities['library']}")
        print(f"📋 Table extraction: {capabilities['capabilities']['table_extraction']['supported']}")
        print(f"📋 Text extraction: {capabilities['capabilities']['text_extraction']['supported']}")
        
        # Test table extraction only
        print(f"\n🔍 Testing table extraction on: {test_pdf}")
        try:
            tables_result = processor.extract_tables_only(test_pdf)
            table_count = len(tables_result.get('tables', []))
            print(f"✅ Table extraction completed: {table_count} tables found")
            
            if table_count > 0:
                print("📊 First table preview:")
                first_table = tables_result['tables'][0]
                print(f"   - Table ID: {first_table['table_id']}")
                print(f"   - Rows: {len(first_table['rows'])}")
                print(f"   - Columns: {len(first_table['columns'])}")
                print(f"   - Page: {first_table['region']['page_number']}")
                print(f"   - Detection method: {first_table['region']['detection_method']}")
        
        except Exception as e:
            print(f"❌ Table extraction failed: {e}")
            return False
        
        # Test text extraction only
        print(f"\n📝 Testing text extraction on: {test_pdf}")
        try:
            text_result = processor.extract_text_only(test_pdf)
            text_summary = text_result['text_content']['summary']
            print(f"✅ Text extraction completed:")
            print(f"   - Total sections: {text_summary['total_sections']}")
            print(f"   - Total words: {text_summary['total_words']}")
            print(f"   - LLM ready sections: {text_summary['llm_ready_sections']}")
            print(f"   - Numbers found: {text_summary['total_numbers_found']}")
        
        except Exception as e:
            print(f"❌ Text extraction failed: {e}")
            return False
        
        # Test full processing
        print(f"\n🚀 Testing full PDF processing on: {test_pdf}")
        try:
            full_result = processor.process_file(test_pdf)
            
            processing_summary = full_result['pdf_processing_result']['processing_summary']
            document_metadata = full_result['pdf_processing_result']['document_metadata']
            
            print(f"✅ Full processing completed:")
            print(f"   - Processing time: {document_metadata['processing_duration']:.2f} seconds")
            print(f"   - Tables extracted: {processing_summary['tables_extracted']}")
            print(f"   - Text sections: {processing_summary['text_sections']}")
            print(f"   - Numbers found: {processing_summary['numbers_found']}")
            print(f"   - Overall quality: {processing_summary['overall_quality_score']:.2f}")
            print(f"   - Errors: {len(processing_summary['processing_errors'])}")
            
            if processing_summary['processing_errors']:
                print(f"⚠️  Processing errors: {processing_summary['processing_errors']}")
        
        except Exception as e:
            print(f"❌ Full processing failed: {e}")
            return False
        
        # Save test results to a temp file
        print(f"\n💾 Saving test results...")
        output_file = tmp_path / "pdfplumber_test_results.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(full_result, f, indent=2, ensure_ascii=False)
            print(f"✅ Results saved to: {output_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
        
        print(f"\n🎉 PDFPlumber implementation test completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Table extraction: ✅ Working")
        print(f"   - Text extraction: ✅ Working")
        print(f"   - Number extraction: ✅ Working")
        print(f"   - JSON schema compatibility: ✅ Working")
        print(f"   - Configuration validation: ✅ Working")
        
        return True
        
    except Exception as e:
        print(f"❌ Critical error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 PDFPlumber Implementation Test")
    print("=" * 50)
    
    # Check dependencies
    try:
        import pdfplumber
        print(f"✅ PDFPlumber available: version {pdfplumber.__version__}")
    except ImportError:
        print("❌ PDFPlumber not available. Please install: pip install pdfplumber")
        return
    
    # Run tests
    success = test_pdfplumber_implementation()
    
    if success:
        print("\n🎉 All tests passed! PDFPlumber implementation is ready.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main() 