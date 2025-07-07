#!/usr/bin/env python3
"""
Project Management Script for AI Code Review Agent.

This script provides utilities for common development tasks including:
- Project status checking
- Dependency management
- Configuration validation
- Performance monitoring
- Cleanup operations
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import argparse

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from logger import get_logger
except ImportError:
    # Fallback if logger module is not available
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger("project_manager")


def check_project_status():
    """Check the overall status of the project."""
    print("🔍 Checking project status...")
    
    project_root = Path(__file__).parent.parent
    issues = []
    warnings = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        issues.append(f"Python 3.9+ required, found {python_version.major}.{python_version.minor}")
    else:
        print(f"✅ Python version: {python_version.major}.{python_version.minor}")
    
    # Check virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        warnings.append("Virtual environment not detected")
    else:
        print("✅ Virtual environment active")
    
    # Check required directories
    required_dirs = ['src', 'tests', 'logs', 'output', 'configs']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ Directory exists: {dir_name}")
        else:
            issues.append(f"Missing directory: {dir_name}")
    
    # Check required files
    required_files = ['requirements.txt', 'README.md', 'ai_reviewer.py', 'VERSION']
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"✅ File exists: {file_name}")
        else:
            issues.append(f"Missing file: {file_name}")
    
    # Check configuration
    config_file = project_root / '.env'
    if config_file.exists():
        print("✅ Configuration file exists")
    else:
        warnings.append("Configuration file (.env) not found")
    
    # Check database
    db_file = project_root / 'database.db'
    if db_file.exists():
        print("✅ Database exists")
    else:
        warnings.append("Database not initialized")
    
    # Check dependencies
    try:
        import pytest
        print("✅ pytest available")
    except ImportError:
        issues.append("pytest not installed")
    
    try:
        import git
        print("✅ GitPython available")
    except ImportError:
        warnings.append("GitPython not installed")
    
    # Report issues and warnings
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not issues and not warnings:
        print("\n🎉 Project status: All good!")
    
    return len(issues) == 0


def validate_configuration():
    """Validate the project configuration."""
    print("🔧 Validating configuration...")
    
    project_root = Path(__file__).parent.parent
    config_file = project_root / '.env'
    
    if not config_file.exists():
        print("❌ Configuration file not found")
        return False
    
    # Read and validate .env file
    with open(config_file, 'r') as f:
        content = f.read()
    
    required_vars = ['LOG_LEVEL', 'OUTPUT_DIR']
    optional_vars = ['OPENAI_API_KEY', 'GOOGLE_API_KEY', 'HUGGINGFACEHUB_API_TOKEN']
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if f"{var}=" not in content:
            missing_required.append(var)
    
    for var in optional_vars:
        if f"{var}=" not in content:
            missing_optional.append(var)
    
    if missing_required:
        print(f"❌ Missing required configuration: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"⚠️  Missing optional configuration: {', '.join(missing_optional)}")
    
    print("✅ Configuration validation passed")
    return True


def cleanup_project():
    """Clean up temporary files and caches."""
    print("🧹 Cleaning up project...")
    
    project_root = Path(__file__).parent.parent
    
    # Files and directories to clean
    cleanup_items = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.pytest_cache',
        'htmlcov',
        'coverage.xml',
        '.coverage',
        'bandit-report.json',
        'logs/*.log',
        'output/temp_*',
        'cache/*'
    ]
    
    cleaned_count = 0
    
    for pattern in cleanup_items:
        if '*' in pattern:
            # Handle glob patterns
            if pattern.startswith('logs/'):
                pattern_path = project_root / pattern
            elif pattern.startswith('output/'):
                pattern_path = project_root / pattern
            elif pattern.startswith('cache/'):
                pattern_path = project_root / pattern
            else:
                pattern_path = project_root / pattern
            
            for item in project_root.rglob(pattern.split('/')[-1]):
                if item.is_file():
                    item.unlink()
                    print(f"🗑️  Removed file: {item}")
                    cleaned_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"🗑️  Removed directory: {item}")
                    cleaned_count += 1
        else:
            # Handle specific directories
            item_path = project_root / pattern
            if item_path.exists():
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                    print(f"🗑️  Removed directory: {pattern}")
                    cleaned_count += 1
                else:
                    item_path.unlink()
                    print(f"🗑️  Removed file: {pattern}")
                    cleaned_count += 1
    
    if cleaned_count == 0:
        print("✅ No cleanup needed")
    else:
        print(f"✅ Cleaned up {cleaned_count} items")


def check_dependencies():
    """Check and update project dependencies."""
    print("📦 Checking dependencies...")
    
    try:
        # Check pip
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pip available")
        else:
            print("❌ pip not available")
            return False
        
        # Check outdated packages
        result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--outdated'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            print("⚠️  Outdated packages found:")
            lines = result.stdout.strip().split('\n')[2:]  # Skip header
            for line in lines:
                if line.strip():
                    print(f"  - {line}")
        else:
            print("✅ All packages are up to date")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
        return False


def update_dependencies():
    """Update project dependencies."""
    print("🔄 Updating dependencies...")
    
    try:
        # Upgrade pip
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                      check=True)
        print("✅ pip upgraded")
        
        # Install/upgrade requirements
        requirements_file = Path(__file__).parent.parent / 'requirements.txt'
        if requirements_file.exists():
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file), '--upgrade'], 
                          check=True)
            print("✅ Requirements updated")
        else:
            print("❌ requirements.txt not found")
            return False
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error updating dependencies: {e}")
        return False


def generate_report():
    """Generate a project status report."""
    print("📊 Generating project report...")
    
    project_root = Path(__file__).parent.parent
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'project_root': str(project_root),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'virtual_env': hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix),
        'directories': {},
        'files': {},
        'dependencies': {},
        'issues': [],
        'warnings': []
    }
    
    # Check directories
    required_dirs = ['src', 'tests', 'logs', 'output', 'configs']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        report['directories'][dir_name] = {
            'exists': dir_path.exists(),
            'size': sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file()) if dir_path.exists() else 0
        }
    
    # Check files
    required_files = ['requirements.txt', 'README.md', 'ai_reviewer.py', 'VERSION']
    for file_name in required_files:
        file_path = project_root / file_name
        report['files'][file_name] = {
            'exists': file_path.exists(),
            'size': file_path.stat().st_size if file_path.exists() else 0
        }
    
    # Check dependencies
    try:
        import pytest
        report['dependencies']['pytest'] = True
    except ImportError:
        report['dependencies']['pytest'] = False
        report['issues'].append('pytest not installed')
    
    try:
        import git
        report['dependencies']['gitpython'] = True
    except ImportError:
        report['dependencies']['gitpython'] = False
        report['warnings'].append('GitPython not installed')
    
    # Save report
    report_file = project_root / 'logs' / f'project_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Report generated: {report_file}")
    return report_file


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="AI Code Review Agent Project Manager")
    parser.add_argument("--status", action="store_true", help="Check project status")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--cleanup", action="store_true", help="Clean up temporary files")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    parser.add_argument("--update-deps", action="store_true", help="Update dependencies")
    parser.add_argument("--report", action="store_true", help="Generate project report")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    print("🔧 AI Code Review Agent Project Manager")
    print("=" * 50)
    
    success = True
    
    if args.all or args.status:
        success &= check_project_status()
    
    if args.all or args.validate:
        success &= validate_configuration()
    
    if args.all or args.cleanup:
        cleanup_project()
    
    if args.all or args.check_deps:
        success &= check_dependencies()
    
    if args.all or args.update_deps:
        success &= update_dependencies()
    
    if args.all or args.report:
        generate_report()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All operations completed successfully!")
    else:
        print("❌ Some operations failed. Check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main() 