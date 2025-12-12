#!/usr/bin/env python3
"""
Utility script to verify available Gemini models and test API connectivity.

This script helps users:
1. Verify their API key is working
2. See all available models
3. Test a specific model

Usage:
    python verify_models.py

Set your API key as environment variable:
    export GEMINI_API_KEY="your-api-key-here"

Or the script will prompt you for it.
"""

import os
import sys


def main():
    """Main function to verify models and API connectivity."""
    
    try:
        import google.generativeai as genai
    except ImportError:
        print("ERROR: google-generativeai package not installed.", file=sys.stderr)
        print("\nNote: This is the DEPRECATED SDK.", file=sys.stderr)
        print("Please install the NEW SDK instead:", file=sys.stderr)
        print("  pip install google-genai", file=sys.stderr)
        print("\nOr to use this deprecated SDK:", file=sys.stderr)
        print("  pip install google-generativeai", file=sys.stderr)
        sys.exit(1)
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("API key not found in environment variable GEMINI_API_KEY")
        api_key = input("Please enter your API key: ").strip()
        
        if not api_key:
            print("ERROR: No API key provided.")
            print("\nGet your API key from: https://aistudio.google.com/app/apikey")
            sys.exit(1)
    
    # Configure the SDK
    try:
        genai.configure(api_key=api_key)
        print("✓ API key configured successfully\n")
    except Exception as e:
        print(f"ERROR: Failed to configure API key: {e}", file=sys.stderr)
        sys.exit(1)
    
    # List available models
    print("=" * 70)
    print("AVAILABLE MODELS FOR CONTENT GENERATION")
    print("=" * 70)
    
    try:
        models_found = False
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                models_found = True
                print(f"\n📌 {model.name}")
                print(f"   Display Name: {model.display_name}")
                print(f"   Description: {model.description}")
                print(f"   Input Token Limit: {model.input_token_limit:,}")
                print(f"   Output Token Limit: {model.output_token_limit:,}")
        
        if not models_found:
            print("No models found with generateContent capability.")
            
    except Exception as e:
        print(f"\nERROR: Failed to list models: {e}")
        print("\nPossible causes:")
        print("  - Invalid API key")
        print("  - Network connectivity issues")
        print("  - API service temporarily unavailable")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    
    # Test a specific model
    print("\nTESTING MODEL CONNECTIVITY")
    print("=" * 70)
    
    test_model_name = "gemini-1.5-flash"
    
    try:
        print(f"\nTesting model: {test_model_name}")
        model = genai.GenerativeModel(test_model_name)
        response = model.generate_content("Say 'Hello, World!' and nothing else.")
        
        print(f"✓ Model test successful!")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"\n✗ Model test failed: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("IMPORTANT NOTICE: DEPRECATED SDK")
    print("=" * 70)
    print("""
This SDK is DEPRECATED and will reach End-of-Life on November 30, 2025.

Please migrate to the new Google Generative AI SDK:
  
  1. Uninstall old SDK: pip uninstall google-generativeai
  2. Install new SDK: pip install google-genai
  3. Follow migration guide: https://ai.google.dev/gemini-api/docs/migrate

For support and questions: https://discuss.ai.google.dev/c/gemini-api/4
""")
    
    print("\n" + "=" * 70)
    print("COMMON MODEL NAMES FOR THIRD-PARTY TOOLS")
    print("=" * 70)
    print("""
Use these model names in your VSCode extensions or other tools:

  Recommended for most use cases:
    • gemini-2.0-flash (newest model, fast)
    • gemini-1.5-flash (fast, efficient)
    • gemini-1.5-pro (more capable for complex tasks)

  Latest versions (auto-updated):
    • gemini-1.5-flash-latest
    • gemini-1.5-pro-latest

  ❌ INVALID model names (will cause errors):
    • Gemini-3-Pro-Preview (does not exist)
    • gemini-3.0 (does not exist)
    • gpt-4 (wrong API, that's OpenAI)
""")
    
    print("\n✓ All checks passed!")


if __name__ == "__main__":
    main()
