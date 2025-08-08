#!/bin/bash
# Load Excel AI Processing Configuration
# Usage: source load_config.sh

if [ -f "config.env" ]; then
    echo "📝 Loading configuration from config.env..."
    
    # Load each line that looks like KEY=value
    while IFS= read -r line; do
        # Skip comments and empty lines
        if [[ $line =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
            continue
        fi
        
        # Export variables
        if [[ $line =~ ^[[:space:]]*([^=]+)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]// /}"
            value="${BASH_REMATCH[2]}"
            export "$key=$value"
            echo "   ✅ $key"
        fi
    done < config.env
    
    echo "🚀 Configuration loaded! AI analysis is now available."
else
    echo "❌ config.env not found. Run setup_api_key.py first."
fi
