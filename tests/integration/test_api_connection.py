#!/usr/bin/env python3
"""
Simple API Connection Test

This script tests the basic Anthropic API connection with minimal data.
"""

import os
import sys
import pytest
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from converter.anthropic_excel_client import AnthropicExcelClient


def test_basic_connection():
    """Test basic API connection."""
    print("🧪 Testing Basic API Connection")
    print("="*35)
    
    # Check environment
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    print(f"API Key present: {'✅' if api_key else '❌'}")
    if api_key:
        print(f"API Key format: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
    
    # Initialize client
    client = AnthropicExcelClient()
    print(f"Client available: {'✅' if client.is_available() else '❌'}")
    
    if not client.is_available():
        pytest.skip("Anthropic client not available; skipping API connection test")
    
    # Try a very simple analysis
    try:
        print("\n🤖 Testing simple API call...")
        
        # Minimal test data
        simple_sheet = {
            'name': 'Test',
            'rows': [
                {'r': 1, 'cells': [[1, 'A'], [2, 'B']]},
                {'r': 2, 'cells': [[1, 1], [2, 2]]}
            ]
        }
        
        # Test cost estimation first
        cost = client.estimate_api_cost(simple_sheet)
        assert 'estimated_cost_usd' in cost
        
        # Try actual API call (sheet-level)
        response = client.analyze_excel_sheet(
            simple_sheet,
            complexity_metadata=None,
            analysis_focus="tables"
        )
        
        print(f"Response status: {response.get('status', 'unknown')}")
        assert isinstance(response, dict)
        assert 'status' in response
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Check if it's an authentication error
        if 'authentication' in str(e).lower() or '401' in str(e):
            print("\n💡 This appears to be an authentication error.")
            print("   Possible causes:")
            print("   1. Invalid API key")
            print("   2. API key expired")
            print("   3. Account not properly set up")
            print("   4. API key format issue")
            
        pytest.fail(f"API test failed: {e}")


def main():
    test_basic_connection()


if __name__ == "__main__":
    main()
