#!/usr/bin/env python3
"""
Test runner script for the AI Code Reviewer Tool.
Runs all tests and provides a comprehensive summary.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def run_test_file(test_file):
    """Run a specific test file and return results."""
    print(f"\n🧪 Running {test_file}...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        return {
            'file': test_file,
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'returncode': result.returncode
        }
    except Exception as e:
        return {
            'file': test_file,
            'success': False,
            'output': '',
            'error': str(e),
            'returncode': 1
        }


def run_all_tests():
    """Run all test files and provide a summary."""
    print("🚀 AI Code Reviewer Tool - Test Suite")
    print("=" * 50)
    
    # Get all test files
    test_dir = Path(__file__).parent
    test_files = [
        'test_api_keys.py',
        'test_agents.py',
        'test_ingestion.py',
        'test_integration.py',
        'test_llm_provider.py',
        'test_logging.py',
        'test_prompts.py',
        'test_tools.py',
        'test_workflow.py'
    ]
    
    # Filter to only existing files
    existing_tests = [f for f in test_files if (test_dir / f).exists()]
    
    print(f"📁 Found {len(existing_tests)} test files")
    print(f"📂 Test directory: {test_dir}")
    
    # Run tests
    results = []
    for test_file in existing_tests:
        result = run_test_file(test_file)
        results.append(result)
    
    # Generate summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/len(results)*100):.1f}%")
    
    # Show detailed results
    print("\n📋 DETAILED RESULTS")
    print("-" * 30)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {result['file']}")
        
        if not result['success'] and result['error']:
            print(f"   Error: {result['error'][:100]}...")
    
    # Show failed test details
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print(f"\n🔍 FAILED TEST DETAILS")
        print("-" * 30)
        
        for result in failed_tests:
            print(f"\n❌ {result['file']}:")
            if result['output']:
                print("Output:")
                print(result['output'][:500] + "..." if len(result['output']) > 500 else result['output'])
            if result['error']:
                print("Error:")
                print(result['error'][:500] + "..." if len(result['error']) > 500 else result['error'])
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 30)
    
    if failed == 0:
        print("🎉 All tests passed! Your AI Code Reviewer Tool is working correctly.")
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the errors above.")
        print("🔧 Common fixes:")
        print("   1. Check that all dependencies are installed: pip install -r requirements.txt")
        print("   2. Ensure environment variables are set correctly")
        print("   3. Verify that the src/ directory structure is correct")
        print("   4. Check that all required files exist")
    
    return failed == 0


def run_specific_test_category(category):
    """Run tests for a specific category."""
    categories = {
        'api': ['test_api_keys.py'],
        'core': ['test_agents.py', 'test_ingestion.py', 'test_tools.py'],
        'integration': ['test_integration.py', 'test_workflow.py'],
        'providers': ['test_llm_provider.py'],
        'logging': ['test_logging.py'],
        'prompts': ['test_prompts.py']
    }
    
    if category not in categories:
        print(f"❌ Unknown category: {category}")
        print(f"Available categories: {', '.join(categories.keys())}")
        return False
    
    print(f"🎯 Running {category} tests...")
    
    test_dir = Path(__file__).parent
    test_files = categories[category]
    existing_tests = [f for f in test_files if (test_dir / f).exists()]
    
    if not existing_tests:
        print(f"❌ No test files found for category: {category}")
        return False
    
    results = []
    for test_file in existing_tests:
        result = run_test_file(test_file)
        results.append(result)
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"\n📊 {category.upper()} TESTS SUMMARY")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    return failed == 0


def main():
    """Main function."""
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
        success = run_specific_test_category(category)
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 