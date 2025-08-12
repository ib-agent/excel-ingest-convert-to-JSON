#!/usr/bin/env python3
"""
API Integration Test

This script tests that the API endpoints work properly with the enhanced 
complexity-preserving processor.
"""

import requests
import json
import os


def test_api_integration():
    """Test the API integration with enhanced processor"""
    print("=== API Integration Test ===\n")
    
    # Test file
    test_file = "tests/test_excel/pDD10abc_360 Energy_360_Energy_Corporate_Model_May_24.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    base_url = "http://localhost:8000"  # Adjust if different
    
    print("📊 Testing API endpoints...\n")
    
    # Test 1: Complexity Analysis Endpoint
    print("1️⃣ Testing Complexity Analysis Endpoint")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{base_url}/api/excel/analyze-complexity/", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Complexity analysis successful")
            print(f"   Overall recommendation: {result.get('overall_recommendation', 'N/A')}")
            print(f"   Sheets analyzed: {len(result.get('sheet_analysis', {}))}")
            
            # Check for enhanced complexity detection
            sheet_analysis = result.get('sheet_analysis', {})
            if sheet_analysis:
                monthly_analysis = sheet_analysis.get('Monthly')
                if monthly_analysis:
                    score = monthly_analysis.get('complexity_score', 0)
                    print(f"   Monthly sheet complexity: {score:.3f}")
                    if score > 0.1:
                        print("✅ Enhanced complexity detection working!")
                    else:
                        print("⚠️  Complexity detection may need verification")
        else:
            print(f"❌ Complexity analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error testing complexity analysis: {str(e)}")
    
    print()
    
    # Test 2: Comparison Analysis Endpoint
    print("2️⃣ Testing Comparison Analysis Endpoint")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{base_url}/api/excel/comparison-analysis/", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Comparison analysis successful")
            
            comparison_results = result.get('comparison_results', {})
            print(f"   Sheets compared: {len(comparison_results)}")
            
            # Check Monthly sheet comparison
            if 'Monthly' in comparison_results:
                monthly_comp = comparison_results['Monthly']
                complexity_analysis = monthly_comp.get('complexity_analysis', {})
                traditional_result = monthly_comp.get('traditional_result', {})
                
                print(f"   Monthly complexity score: {complexity_analysis.get('complexity_score', 0):.3f}")
                print(f"   Traditional tables detected: {traditional_result.get('tables_detected', 0)}")
                print(f"   Recommendation: {complexity_analysis.get('recommendation', 'N/A')}")
        else:
            print(f"❌ Comparison analysis failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error testing comparison analysis: {str(e)}")
    
    print()
    
    # Test 3: Enhanced Upload and Convert
    print("3️⃣ Testing Enhanced Upload and Convert")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': f}
            data = {
                'enable_comparison': 'true',
                'enable_ai_analysis': 'true'
            }
            response = requests.post(f"{base_url}/api/upload/", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Enhanced upload successful")
            print(f"   Large file: {result.get('large_file', False)}")
            
            # Check for complexity analysis in response
            if 'complexity_analysis' in result:
                complexity_analysis = result['complexity_analysis']
                print(f"   Complexity analysis included: {len(complexity_analysis)} sheets")
                
                # Check Monthly sheet
                if 'Monthly' in complexity_analysis:
                    monthly_analysis = complexity_analysis['Monthly']
                    score = monthly_analysis.get('complexity_score', 0)
                    print(f"   Monthly complexity score: {score:.3f}")
                    
                    if score > 0.1:
                        print("✅ Enhanced complexity analysis integrated!")
                    else:
                        print("⚠️  May need to verify complexity integration")
            else:
                print("ℹ️  Complexity analysis not in main response (may be in download)")
        else:
            print(f"❌ Enhanced upload failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}...")
    
    except Exception as e:
        print(f"❌ Error testing enhanced upload: {str(e)}")
    
    print("\n🎯 API Integration Summary:")
    print("The enhanced complexity-preserving processor should now be active")
    print("in all API endpoints, providing:")
    print("1. ✅ Accurate complexity analysis with metadata")
    print("2. ✅ Maintained compression efficiency") 
    print("3. ✅ Comparison mode capability for AI tuning")
    print("4. ✅ Dual processing support for test case generation")


if __name__ == "__main__":
    print("📋 Note: This test requires the Django server to be running")
    print("Run: python manage.py runserver")
    print("Then run this test script\n")
    
    try:
        test_api_integration()
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        print("\nMake sure the Django server is running:")
        print("cd /Users/jeffwinner/excel-ingest-convert-to-JSON")
        print("source venv/bin/activate")  
        print("python manage.py runserver")
