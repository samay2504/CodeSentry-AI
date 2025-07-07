#!/usr/bin/env python3
"""
Patch application script for AI Code Review Agent.

This script applies delta patches to update the codebase.
"""

import os
import sys
import importlib.util
import shutil
from pathlib import Path
from datetime import datetime


def apply_patch(patch_version: str):
    """
    Apply a specific patch version.
    
    Args:
        patch_version: Version of the patch to apply (e.g., '1.0.1')
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Construct patch file path
    patch_file = project_root / 'scripts' / 'patches' / f'patch_{patch_version}.py'
    
    if not patch_file.exists():
        print(f"❌ Error: Patch file not found: {patch_file}")
        print(f"Available patches:")
        list_available_patches()
        sys.exit(1)
    
    # Create backup before applying patch
    create_backup(project_root, patch_version)
    
    try:
        # Load and execute the patch module
        spec = importlib.util.spec_from_file_location(f"patch_{patch_version}", patch_file)
        patch_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(patch_module)
        
        # Apply the patch
        if hasattr(patch_module, 'apply_patch'):
            print(f"🔄 Applying patch {patch_version}...")
            patch_module.apply_patch()
        else:
            print(f"❌ Error: Patch file {patch_file} does not contain apply_patch function")
            sys.exit(1)
            
        # Update version file
        update_version(patch_version)
        
        # Record patch application
        record_patch_application(patch_version)
        
        print(f"✅ Patch {patch_version} applied successfully!")
        
    except Exception as e:
        print(f"❌ Error applying patch {patch_version}: {e}")
        print("🔄 Attempting to restore from backup...")
        restore_backup(project_root, patch_version)
        sys.exit(1)


def create_backup(project_root: Path, patch_version: str):
    """Create a backup of the current state before applying patch."""
    backup_dir = project_root / 'backups' / f'before_patch_{patch_version}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy important files and directories
    important_paths = [
        'src',
        'tests',
        'requirements.txt',
        'README.md',
        'VERSION',
        'ai_reviewer.py'
    ]
    
    for path in important_paths:
        source = project_root / path
        if source.exists():
            if source.is_dir():
                shutil.copytree(source, backup_dir / path, dirs_exist_ok=True)
            else:
                shutil.copy2(source, backup_dir / path)
    
    print(f"📦 Created backup: {backup_dir}")


def restore_backup(project_root: Path, patch_version: str):
    """Restore from backup if patch application fails."""
    backup_dir = project_root / 'backups'
    if not backup_dir.exists():
        print("❌ No backup directory found")
        return
    
    # Find the most recent backup for this patch
    backups = [d for d in backup_dir.iterdir() if d.is_dir() and f'before_patch_{patch_version}' in d.name]
    if not backups:
        print("❌ No backup found for this patch")
        return
    
    latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
    
    # Restore files
    for item in latest_backup.iterdir():
        target = project_root / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    
    print(f"🔄 Restored from backup: {latest_backup}")


def update_version(new_version: str):
    """
    Update the VERSION file.
    
    Args:
        new_version: New version string
    """
    version_file = Path(__file__).parent.parent / 'VERSION'
    
    try:
        with open(version_file, 'w') as f:
            f.write(new_version)
        print(f"📝 Updated VERSION file to {new_version}")
    except Exception as e:
        print(f"⚠️  Warning: Could not update VERSION file: {e}")


def record_patch_application(patch_version: str):
    """Record patch application in a log file."""
    log_file = Path(__file__).parent.parent / 'logs' / 'patch_history.log'
    log_file.parent.mkdir(exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} - Applied patch {patch_version}\n"
    
    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"⚠️  Warning: Could not record patch application: {e}")


def list_available_patches():
    """List all available patches."""
    patches_dir = Path(__file__).parent / 'patches'
    
    if not patches_dir.exists():
        print("❌ No patches directory found.")
        return
    
    patch_files = list(patches_dir.glob('patch_*.py'))
    
    if not patch_files:
        print("❌ No patches available.")
        return
    
    print("📦 Available patches:")
    for patch_file in sorted(patch_files):
        version = patch_file.stem.replace('patch_', '')
        
        # Try to get patch description
        try:
            with open(patch_file, 'r') as f:
                content = f.read()
                # Look for docstring
                if '"""' in content:
                    start = content.find('"""') + 3
                    end = content.find('"""', start)
                    if end > start:
                        description = content[start:end].strip().split('\n')[0]
                        print(f"  - {version}: {description}")
                    else:
                        print(f"  - {version}")
                else:
                    print(f"  - {version}")
        except:
            print(f"  - {version}")


def show_patch_info(patch_version: str):
    """Show detailed information about a specific patch."""
    patches_dir = Path(__file__).parent / 'patches'
    patch_file = patches_dir / f'patch_{patch_version}.py'
    
    if not patch_file.exists():
        print(f"❌ Patch {patch_version} not found")
        return
    
    try:
        with open(patch_file, 'r') as f:
            content = f.read()
            print(f"📋 Patch {patch_version} Information:")
            print("=" * 50)
            
            # Extract docstring
            if '"""' in content:
                start = content.find('"""') + 3
                end = content.find('"""', start)
                if end > start:
                    docstring = content[start:end].strip()
                    print(docstring)
                    print()
            
            # Show file size and modification time
            stat = patch_file.stat()
            print(f"File: {patch_file}")
            print(f"Size: {stat.st_size} bytes")
            print(f"Modified: {datetime.fromtimestamp(stat.st_mtime)}")
            
    except Exception as e:
        print(f"❌ Error reading patch file: {e}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("🔧 AI Code Review Agent Patch Manager")
        print("=" * 40)
        print()
        print("Usage: python apply_patch.py <patch_version>")
        print("       python apply_patch.py --list")
        print("       python apply_patch.py --info <patch_version>")
        print()
        print("Examples:")
        print("  python apply_patch.py 1.0.1")
        print("  python apply_patch.py --list")
        print("  python apply_patch.py --info 1.0.1")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        list_available_patches()
    elif sys.argv[1] == '--info':
        if len(sys.argv) < 3:
            print("❌ Error: Please specify patch version for --info")
            sys.exit(1)
        show_patch_info(sys.argv[2])
    else:
        patch_version = sys.argv[1]
        apply_patch(patch_version)


if __name__ == "__main__":
    main() 