#!/usr/bin/env python3
"""
API Key Testing and Diagnostic Script
Tests all configured API keys and provides detailed feedback
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.llm_provider import create_llm_provider


def test_huggingface_cli_login():
    """Test if huggingface-cli login is needed."""
    print("=== Testing HuggingFace CLI Login ===")
    
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        
        # Try to get user info
        user = api.whoami()
        print(f"✅ HuggingFace CLI login successful. User: {user}")
        assert True  # Test passed
        
    except Exception as e:
        # This is expected if no HuggingFace token is configured
        if "Token is required" in str(e) or "no token found" in str(e):
            print(f"ℹ️  HuggingFace CLI login not configured (expected): {e}")
            print("💡 Run: huggingface-cli login (optional)")
            assert True  # This is expected behavior
        else:
            print(f"❌ HuggingFace CLI login failed: {e}")
            print("💡 Run: huggingface-cli login")
            assert False  # Test failed


def test_api_keys():
    """Test all configured API keys."""
    print("\n=== Testing API Keys ===")
    
    # Test HuggingFace
    print("\n🔍 Testing HuggingFace API Key...")
    hf_key = os.getenv('HUGGINGFACEHUB_API_TOKEN')
    if hf_key:
        print(f"✅ HUGGINGFACEHUB_API_TOKEN found (length: {len(hf_key)})")
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=hf_key)
            models = list(api.list_models(author="bigcode", limit=1))
            print("✅ HuggingFace API key works - can access models")
        except Exception as e:
            print(f"❌ HuggingFace API key failed: {e}")
            print("💡 Check your token permissions at https://huggingface.co/settings/tokens")
    else:
        print("❌ HUGGINGFACEHUB_API_TOKEN not set")
    
    # Test Google
    print("\n🔍 Testing Google API Key...")
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        print(f"✅ GOOGLE_API_KEY found (length: {len(google_key)})")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=google_key,
                temperature=0.1
            )
            response = llm.invoke("Test")
            print("✅ Google API key works")
        except Exception as e:
            print(f"❌ Google API key failed: {e}")
    else:
        print("❌ GOOGLE_API_KEY not set")
    
    # Test OpenAI
    print("\n🔍 Testing OpenAI API Key...")
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OPENAI_API_KEY found (length: {len(openai_key)})")
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_key=openai_key,
                temperature=0.1
            )
            response = llm.invoke("Test")
            print("✅ OpenAI API key works")
        except Exception as e:
            print(f"❌ OpenAI API key failed: {e}")
    else:
        print("❌ OPENAI_API_KEY not set")
    
    # Test Groq
    print("\n🔍 Testing Groq API Key...")
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        print(f"✅ GROQ_API_KEY found (length: {len(groq_key)})")
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                model="llama3-8b-8192",
                groq_api_key=groq_key,
                temperature=0.1
            )
            response = llm.invoke("Test")
            print("✅ Groq API key works")
        except Exception as e:
            print(f"❌ Groq API key failed: {e}")
    else:
        print("❌ GROQ_API_KEY not set")


def test_llm_provider():
    """Test the LLM provider system."""
    print("\n=== Testing LLM Provider System ===")
    
    try:
        config = {
            'model': 'bigcode/starcoder',
            'temperature': 0.1
        }
        
        llm_provider = create_llm_provider(config)
        provider_info = llm_provider.get_provider_info()
        
        print(f"✅ LLM Provider initialized successfully")
        print(f"   Provider: {provider_info['provider']}")
        print(f"   Fallback mode: {provider_info['fallback_mode']}")
        
        # Test a simple invocation
        response = llm_provider.invoke("Hello, this is a test.")
        print(f"✅ LLM invocation successful")
        
        assert True  # Test passed
        
    except Exception as e:
        print(f"❌ LLM Provider test failed: {e}")
        assert False  # Test failed


def main():
    """Run all tests."""
    print("🚀 AI Reviewer Tool - API Key Diagnostic")
    print("=" * 50)
    
    # Load environment variables
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        print(f"📁 Loading environment from: {env_file}")
        from dotenv import load_dotenv
        load_dotenv(env_file)
    else:
        print("⚠️  No .env file found")
    
    # Run tests
    try:
        test_huggingface_cli_login()
        hf_login_ok = True
    except AssertionError:
        hf_login_ok = False
    
    test_api_keys()
    
    try:
        test_llm_provider()
        llm_provider_ok = True
    except AssertionError:
        llm_provider_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    if hf_login_ok and llm_provider_ok:
        print("✅ All tests passed! Your setup should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the recommendations above.")
        print("\n🔧 TROUBLESHOOTING TIPS:")
        print("1. Run: huggingface-cli login")
        print("2. Check API key permissions at respective provider websites")
        print("3. Ensure your .env file is properly configured")
        print("4. Check your internet connection and proxy settings")


if __name__ == "__main__":
    main() 