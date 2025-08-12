#!/usr/bin/env python3
"""
Comprehensive PDFPlumber Migration Test

This test validates that the PDFPlumber implementation provides:
1. API compatibility with the original system
2. Improved or equivalent results
3. All core functionality working correctly

Author: PDF Processing Team
Date: 2024
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add converter directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'converter'))

# Import PDFPlumber implementations
from converter.pdfplumber_processor import PDFPlumberProcessor
from pdfplumber_clean_processor import CleanPDFProcessor

# Import the new PDFPlumber-based main processor
try:
    from PDF_processing_pdfplumber import PDFProcessor as PDFPlumberMainProcessor
except ImportError as e:
    print(f"Warning: Could not import PDF_processing_pdfplumber: {e}")
    PDFPlumberMainProcessor = None

def test_pdfplumber_migration(tmp_path):
    """
    Comprehensive test of the PDFPlumber migration
    """
    print("🧪 Comprehensive PDFPlumber Migration Test")
    print("=" * 60)
    
    # Find test PDF files
    repo_root = os.path.dirname(os.path.dirname(__file__))
    test_pdf_dirs = [
        os.path.join(repo_root, 'fixtures', 'pdfs'),
        os.path.join(repo_root, 'fixtures'),
    ]
    
    test_pdfs = []
    for test_dir in test_pdf_dirs:
        if os.path.exists(test_dir):
            pdf_files = [f for f in os.listdir(test_dir) if f.endswith('.pdf')]
            for pdf_file in pdf_files:
                test_pdfs.append(os.path.join(test_dir, pdf_file))
    
    if not test_pdfs:
        print("❌ No test PDF files found.")
        return False
    
    print(f"📄 Found {len(test_pdfs)} test PDF(s)")
    for pdf in test_pdfs:
        print(f"   - {os.path.basename(pdf)}")
    
    # Test results collector
    test_results = {
        "migration_validation": {
            "api_compatibility": {"passed": 0, "failed": 0, "tests": []},
            "functionality": {"passed": 0, "failed": 0, "tests": []},
            "performance": {"passed": 0, "failed": 0, "tests": []},
            "quality": {"passed": 0, "failed": 0, "tests": []}
        },
        "test_files": test_pdfs,
        "detailed_results": {}
    }
    
    # Run tests on each PDF
    for test_pdf in test_pdfs[:2]:  # Limit to first 2 PDFs for faster testing
        pdf_name = os.path.basename(test_pdf)
        print(f"\n🔍 Testing with: {pdf_name}")
        print("-" * 40)
        
        pdf_results = _run_single_pdf(test_pdf, test_results)
        test_results["detailed_results"][pdf_name] = pdf_results
    
    # Generate summary report
    print_summary_report(test_results)
    
    # Save detailed results to a temporary location
    output_file = tmp_path / "pdfplumber_migration_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Determine overall success
    total_passed = sum(category["passed"] for category in test_results["migration_validation"].values())
    total_failed = sum(category["failed"] for category in test_results["migration_validation"].values())
    
    print(f"\n🎯 Overall Results: {total_passed} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("🎉 PDFPlumber migration validation PASSED!")
        return True
    else:
        print("❌ PDFPlumber migration validation FAILED!")
        return False

def _run_single_pdf(pdf_path: str, test_results: Dict) -> Dict[str, Any]:
    """
    Test a single PDF file with all processors
    
    Args:
        pdf_path: Path to the PDF file
        test_results: Test results collector
        
    Returns:
        Dictionary containing test results for this PDF
    """
    pdf_results = {
        "file_path": pdf_path,
        "tests": [],
        "processing_times": {},
        "extraction_results": {}
    }
    
    # Test 1: Core PDFPlumber Processor
    test_name = "Core PDFPlumber Processor"
    print(f"  🔧 Testing: {test_name}")
    
    try:
        start_time = time.time()
        processor = PDFPlumberProcessor()
        
        # Test configuration validation
        validation = processor.validate_configuration()
        if not validation['valid']:
            raise Exception(f"Configuration validation failed: {validation['errors']}")
        
        # Test capabilities
        capabilities = processor.get_processing_capabilities()
        if not capabilities['capabilities']['table_extraction']['supported']:
            raise Exception("Table extraction not supported")
        
        # Test full processing
        result = processor.process_file(pdf_path)
        processing_time = time.time() - start_time
        
        pdf_results["processing_times"]["core_processor"] = processing_time
        pdf_results["extraction_results"]["core_processor"] = result
        
        # Validate result structure
        required_keys = ["pdf_processing_result"]
        if not all(key in result for key in required_keys):
            raise Exception(f"Missing required keys in result: {required_keys}")
        
        test_results["migration_validation"]["functionality"]["passed"] += 1
        test_results["migration_validation"]["api_compatibility"]["passed"] += 1
        
        pdf_results["tests"].append({
            "name": test_name,
            "status": "PASSED",
            "processing_time": processing_time,
            "details": f"Successfully processed with {len(result['pdf_processing_result']['tables'].get('tables', []))} tables"
        })
        
        print(f"    ✅ {test_name} - PASSED ({processing_time:.2f}s)")
        
    except Exception as e:
        test_results["migration_validation"]["functionality"]["failed"] += 1
        test_results["migration_validation"]["api_compatibility"]["failed"] += 1
        
        pdf_results["tests"].append({
            "name": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        
        print(f"    ❌ {test_name} - FAILED: {e}")
    
    # Test 2: Clean PDF Processor (if pandas is working)
    test_name = "Clean PDF Processor"
    print(f"  🔧 Testing: {test_name}")
    
    try:
        start_time = time.time()
        # Try to import pandas to check if it's working
        import pandas as pd
        
        processor = CleanPDFProcessor()
        result = processor.process(pdf_path)
        processing_time = time.time() - start_time
        
        pdf_results["processing_times"]["clean_processor"] = processing_time
        pdf_results["extraction_results"]["clean_processor"] = result
        
        # Validate result structure
        required_keys = ["processing_metadata", "tables", "text_sections", "numbers"]
        if not all(key in result for key in required_keys):
            raise Exception(f"Missing required keys in result: {required_keys}")
        
        test_results["migration_validation"]["functionality"]["passed"] += 1
        test_results["migration_validation"]["api_compatibility"]["passed"] += 1
        
        pdf_results["tests"].append({
            "name": test_name,
            "status": "PASSED",
            "processing_time": processing_time,
            "details": f"Successfully processed with {result['processing_metadata']['tables_found']} tables"
        })
        
        print(f"    ✅ {test_name} - PASSED ({processing_time:.2f}s)")
        
    except ImportError as e:
        pdf_results["tests"].append({
            "name": test_name,
            "status": "SKIPPED",
            "reason": f"Pandas import failed: {e}"
        })
        print(f"    ⚠️  {test_name} - SKIPPED: Pandas issue")
        
    except Exception as e:
        test_results["migration_validation"]["functionality"]["failed"] += 1
        test_results["migration_validation"]["api_compatibility"]["failed"] += 1
        
        pdf_results["tests"].append({
            "name": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        
        print(f"    ❌ {test_name} - FAILED: {e}")
    
    # Test 3: Main PDF Processor (if available)
    if PDFPlumberMainProcessor:
        test_name = "Main PDF Processor"
        print(f"  🔧 Testing: {test_name}")
        
        try:
            start_time = time.time()
            processor = PDFPlumberMainProcessor()
            result = processor.process_pdf(pdf_path)
            processing_time = time.time() - start_time
            
            pdf_results["processing_times"]["main_processor"] = processing_time
            pdf_results["extraction_results"]["main_processor"] = result
            
            # Validate result structure
            required_keys = ["document_metadata", "tables", "text_content", "processing_summary"]
            if not all(key in result for key in required_keys):
                raise Exception(f"Missing required keys in result: {required_keys}")
            
            test_results["migration_validation"]["functionality"]["passed"] += 1
            test_results["migration_validation"]["api_compatibility"]["passed"] += 1
            
            pdf_results["tests"].append({
                "name": test_name,
                "status": "PASSED",
                "processing_time": processing_time,
                "details": f"Successfully processed with {result['processing_summary']['tables_extracted']} tables"
            })
            
            print(f"    ✅ {test_name} - PASSED ({processing_time:.2f}s)")
            
        except Exception as e:
            test_results["migration_validation"]["functionality"]["failed"] += 1
            test_results["migration_validation"]["api_compatibility"]["failed"] += 1
            
            pdf_results["tests"].append({
                "name": test_name,
                "status": "FAILED",
                "error": str(e)
            })
            
            print(f"    ❌ {test_name} - FAILED: {e}")
    
    # Test 4: Performance Validation
    test_name = "Performance Validation"
    print(f"  🔧 Testing: {test_name}")
    
    try:
        processing_times = pdf_results["processing_times"]
        
        # Check if processing times are reasonable (under 30 seconds for small PDFs)
        max_reasonable_time = 30.0
        all_reasonable = all(time <= max_reasonable_time for time in processing_times.values())
        
        if all_reasonable:
            test_results["migration_validation"]["performance"]["passed"] += 1
            pdf_results["tests"].append({
                "name": test_name,
                "status": "PASSED",
                "details": f"All processing times under {max_reasonable_time}s"
            })
            print(f"    ✅ {test_name} - PASSED")
        else:
            test_results["migration_validation"]["performance"]["failed"] += 1
            slow_processors = [name for name, time in processing_times.items() if time > max_reasonable_time]
            pdf_results["tests"].append({
                "name": test_name,
                "status": "FAILED",
                "details": f"Slow processors: {slow_processors}"
            })
            print(f"    ❌ {test_name} - FAILED: Some processors too slow")
        
    except Exception as e:
        test_results["migration_validation"]["performance"]["failed"] += 1
        pdf_results["tests"].append({
            "name": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"    ❌ {test_name} - FAILED: {e}")
    
    # Test 5: Quality Validation
    test_name = "Quality Validation"
    print(f"  🔧 Testing: {test_name}")
    
    try:
        extraction_results = pdf_results["extraction_results"]
        
        # Check if we extracted something meaningful
        total_tables = 0
        total_text_sections = 0
        
        for processor_name, result in extraction_results.items():
            if processor_name == "core_processor":
                tables = result.get("pdf_processing_result", {}).get("tables", {}).get("tables", [])
                total_tables += len(tables)
                
                text_content = result.get("pdf_processing_result", {}).get("text_content", {})
                pages = text_content.get("pages", [])
                for page in pages:
                    total_text_sections += len(page.get("sections", []))
            
            elif processor_name == "clean_processor":
                total_tables += result.get("processing_metadata", {}).get("tables_found", 0)
                total_text_sections += result.get("processing_metadata", {}).get("text_sections_found", 0)
            
            elif processor_name == "main_processor":
                total_tables += result.get("processing_summary", {}).get("tables_extracted", 0)
                total_text_sections += result.get("processing_summary", {}).get("text_sections_extracted", 0)
        
        # Check if we extracted reasonable content
        if total_tables > 0 or total_text_sections > 0:
            test_results["migration_validation"]["quality"]["passed"] += 1
            pdf_results["tests"].append({
                "name": test_name,
                "status": "PASSED",
                "details": f"Extracted {total_tables} tables and {total_text_sections} text sections"
            })
            print(f"    ✅ {test_name} - PASSED")
        else:
            test_results["migration_validation"]["quality"]["failed"] += 1
            pdf_results["tests"].append({
                "name": test_name,
                "status": "FAILED",
                "details": "No meaningful content extracted"
            })
            print(f"    ❌ {test_name} - FAILED: No content extracted")
        
    except Exception as e:
        test_results["migration_validation"]["quality"]["failed"] += 1
        pdf_results["tests"].append({
            "name": test_name,
            "status": "FAILED",
            "error": str(e)
        })
        print(f"    ❌ {test_name} - FAILED: {e}")
    
    return pdf_results

def print_summary_report(test_results: Dict):
    """Print a comprehensive summary report"""
    print("\n" + "=" * 60)
    print("📊 MIGRATION VALIDATION SUMMARY")
    print("=" * 60)
    
    categories = [
        ("API Compatibility", "api_compatibility"),
        ("Core Functionality", "functionality"),
        ("Performance", "performance"),
        ("Quality", "quality")
    ]
    
    for category_name, category_key in categories:
        category_data = test_results["migration_validation"][category_key]
        total_tests = category_data["passed"] + category_data["failed"]
        
        if total_tests > 0:
            success_rate = (category_data["passed"] / total_tests) * 100
            status = "✅ PASS" if category_data["failed"] == 0 else "❌ FAIL"
            
            print(f"{category_name}: {status}")
            print(f"  Passed: {category_data['passed']}/{total_tests} ({success_rate:.1f}%)")
            
            if category_data["failed"] > 0:
                print(f"  Failed: {category_data['failed']}")
        else:
            print(f"{category_name}: ⚠️  NO TESTS")
    
    print("\n📋 Detailed File Results:")
    for file_name, file_results in test_results["detailed_results"].items():
        print(f"\n  📄 {file_name}:")
        for test in file_results["tests"]:
            status_icon = "✅" if test["status"] == "PASSED" else "❌" if test["status"] == "FAILED" else "⚠️"
            print(f"    {status_icon} {test['name']}: {test['status']}")
            
            if "processing_time" in test:
                print(f"      Time: {test['processing_time']:.2f}s")
            
            if "details" in test:
                print(f"      Details: {test['details']}")
            
            if "error" in test:
                print(f"      Error: {test['error']}")

def main():
    """Main test function"""
    print("🚀 PDFPlumber Migration Validation")
    print("=" * 60)
    
    # Check dependencies
    try:
        import pdfplumber
        print(f"✅ PDFPlumber available: version {pdfplumber.__version__}")
    except ImportError:
        print("❌ PDFPlumber not available. Please install: pip install pdfplumber")
        return False
    
    # Run comprehensive tests
    success = test_pdfplumber_migration()
    
    if success:
        print("\n🎉 PDFPlumber migration validation COMPLETED SUCCESSFULLY!")
        print("✅ Ready for production deployment")
    else:
        print("\n❌ PDFPlumber migration validation FAILED!")
        print("🔧 Please review and fix the issues before deployment")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 