#!/usr/bin/env python3
"""
Configuration Management Utility

This script helps manage the Excel AI processing configuration,
including API keys, cost limits, and other settings.
"""

import os
import sys
import json
from datetime import datetime


def load_config():
    """Load configuration from config.env file."""
    config = {}
    
    if os.path.exists('config.env'):
        with open('config.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


def check_status():
    """Check the current configuration status."""
    print("🔍 CONFIGURATION STATUS")
    print("="*30 + "\n")
    
    # Check environment variables
    api_key_env = os.environ.get('ANTHROPIC_API_KEY')
    api_key_file = None
    
    # Check config file
    config = load_config()
    if config:
        api_key_file = config.get('ANTHROPIC_API_KEY')
    
    print(f"📂 Config File: {'✅ Found' if os.path.exists('config.env') else '❌ Missing'}")
    print(f"🔑 API Key (Environment): {'✅ Set' if api_key_env else '❌ Not Set'}")
    print(f"🔑 API Key (File): {'✅ Found' if api_key_file else '❌ Missing'}")
    
    # Test AI client availability
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from converter.anthropic_excel_client import AnthropicExcelClient
        
        client = AnthropicExcelClient()
        ai_available = client.is_available()
        
        print(f"🤖 AI Client: {'✅ Available' if ai_available else '❌ Not Available'}")
        
        if ai_available:
            # Test cost estimation
            mock_sheet = {'name': 'Test', 'rows': []}
            cost_est = client.estimate_api_cost(mock_sheet)
            print(f"💰 Cost Estimation: ✅ Working (${cost_est['estimated_cost_usd']:.4f} for test)")
        
    except Exception as e:
        print(f"🤖 AI Client: ❌ Error - {str(e)}")
    
    # Show configuration values
    if config:
        print(f"\n⚙️  CURRENT SETTINGS:")
        safe_config = {k: v for k, v in config.items() if k != 'ANTHROPIC_API_KEY'}
        safe_config['ANTHROPIC_API_KEY'] = '***HIDDEN***' if api_key_file else 'NOT_SET'
        
        for key, value in safe_config.items():
            print(f"   {key}: {value}")


def update_setting(key, value):
    """Update a configuration setting."""
    config = load_config()
    config[key] = value
    
    # Write back to file
    with open('config.env', 'w') as f:
        f.write("# Excel AI Processing Configuration\n")
        f.write(f"# Updated: {datetime.now().isoformat()}\n\n")
        
        f.write("# Anthropic API Configuration\n")
        f.write(f"ANTHROPIC_API_KEY={config.get('ANTHROPIC_API_KEY', '')}\n")
        f.write(f"ANTHROPIC_MODEL={config.get('ANTHROPIC_MODEL', 'claude-3-sonnet-20241022')}\n\n")
        
        f.write("# API Limits\n")
        f.write(f"AI_ANALYSIS_TIMEOUT={config.get('AI_ANALYSIS_TIMEOUT', '30')}\n")
        f.write(f"MAX_PROMPT_TOKENS={config.get('MAX_PROMPT_TOKENS', '8000')}\n")
        f.write(f"MAX_COMPLETION_TOKENS={config.get('MAX_COMPLETION_TOKENS', '4000')}\n\n")
        
        f.write("# Cost Controls\n")
        f.write(f"MAX_COST_PER_ANALYSIS={config.get('MAX_COST_PER_ANALYSIS', '0.10')}\n")
        f.write(f"DAILY_COST_LIMIT={config.get('DAILY_COST_LIMIT', '10.00')}\n")
    
    print(f"✅ Updated {key} in config.env")


def show_usage_guide():
    """Show usage guide for API configuration."""
    print("📖 USAGE GUIDE")
    print("="*20 + "\n")
    
    print("🔧 SETUP (First Time):")
    print("   1. python setup_api_key.py")
    print("   2. Enter your Anthropic API key")
    print("   3. Choose storage method\n")
    
    print("🚀 DAILY USAGE:")
    print("   # Load configuration")
    print("   source load_config.sh")
    print("   ")
    print("   # OR export manually")
    print("   export $(cat config.env | grep -v '^#' | xargs)")
    print("   ")
    print("   # Then run analysis")
    print("   python collect_comparison_data.py\n")
    
    print("⚙️  MANAGEMENT:")
    print("   # Check status")
    print("   python manage_config.py status")
    print("   ")
    print("   # Update cost limit")
    print("   python manage_config.py set MAX_COST_PER_ANALYSIS 0.05")
    print("   ")
    print("   # Show this guide")
    print("   python manage_config.py help\n")
    
    print("🔐 SECURITY:")
    print("   - config.env contains your API key")
    print("   - Add config.env to .gitignore")
    print("   - Don't share or commit this file")
    print("   - Use environment variables in production\n")


def main():
    """Main configuration management."""
    if len(sys.argv) < 2:
        check_status()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        check_status()
    
    elif command == 'set':
        if len(sys.argv) != 4:
            print("❌ Usage: python manage_config.py set KEY VALUE")
            return
        
        key = sys.argv[2]
        value = sys.argv[3]
        update_setting(key, value)
    
    elif command == 'help':
        show_usage_guide()
    
    elif command == 'test':
        # Quick test of AI availability
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from converter.anthropic_excel_client import AnthropicExcelClient
            
            client = AnthropicExcelClient()
            if client.is_available():
                print("✅ AI client is ready!")
                
                # Quick cost estimation test
                mock_sheet = {
                    'name': 'Test Sheet',
                    'rows': [
                        {'r': 1, 'cells': [[1, 'A'], [2, 'B']]},
                        {'r': 2, 'cells': [[1, 1], [2, 2]]}
                    ]
                }
                cost = client.estimate_api_cost(mock_sheet)
                print(f"💰 Test analysis would cost: ${cost['estimated_cost_usd']:.4f}")
            else:
                print("❌ AI client not available. Check your API key.")
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: status, set, help, test")


if __name__ == "__main__":
    main()
