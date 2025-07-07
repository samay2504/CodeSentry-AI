# Patch System

This directory contains delta patches for the AI Code Review Agent.

## Overview

The patch system allows for incremental updates to the codebase without requiring a full reinstall. Patches are Python scripts that can be applied to update specific components or fix issues.

## Patch Format

Patches are stored as Python scripts that can be applied to update the codebase. Each patch should be self-contained and include proper error handling.

## Naming Convention

- `patch_<version>.py` - Patch for specific version
- Example: `patch_1.0.1.py` for version 1.0.1

## Applying Patches

Use the apply_patch.py script:

```bash
# Apply a specific patch
python scripts/apply_patch.py 1.0.1

# List available patches
python scripts/apply_patch.py --list

# Get detailed information about a patch
python scripts/apply_patch.py --info 1.0.1
```

## Creating Patches

1. Make your changes to the codebase
2. Create a patch script in this directory following the naming convention
3. Update the VERSION file
4. Document changes in the patch script
5. Test the patch thoroughly

## Patch Script Structure

Each patch script should follow this structure:

```python
#!/usr/bin/env python3
"""
Patch <version> - Brief description

Changes:
- Change 1 description
- Change 2 description
- Change 3 description

Author: Your Name
Date: YYYY-MM-DD
"""

import os
import shutil
from pathlib import Path

def apply_patch():
    """Apply patch <version>."""
    print("Applying patch <version>...")
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    try:
        # Make your changes here
        # Example: Update a file
        # update_file(project_root / 'src' / 'some_file.py', new_content)
        
        # Example: Create a new file
        # create_file(project_root / 'src' / 'new_file.py', content)
        
        # Example: Update configuration
        # update_config(project_root / 'configs' / 'config.py')
        
        print("Patch <version> applied successfully!")
        
    except Exception as e:
        print(f"Error applying patch: {e}")
        raise

def update_file(file_path: Path, new_content: str):
    """Update a file with new content."""
    with open(file_path, 'w') as f:
        f.write(new_content)
    print(f"Updated {file_path}")

def create_file(file_path: Path, content: str):
    """Create a new file with content."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Created {file_path}")

def update_config(config_path: Path):
    """Update configuration file."""
    # Add your configuration update logic here
    pass

if __name__ == "__main__":
    apply_patch()
```

## Best Practices

1. **Backup First**: The patch system automatically creates backups before applying patches
2. **Test Thoroughly**: Test patches on a clean installation before distribution
3. **Document Changes**: Include clear descriptions of what the patch does
4. **Error Handling**: Include proper error handling and rollback mechanisms
5. **Version Compatibility**: Ensure patches are compatible with the target version
6. **Atomic Changes**: Make patches atomic - they should either succeed completely or fail completely

## Patch History

Patches are automatically logged in `logs/patch_history.log` with timestamps and status information.

## Rollback

If a patch fails, the system will automatically attempt to restore from the backup created before the patch was applied. Manual rollback can be done by:

1. Locating the backup in the `backups/` directory
2. Restoring the files manually
3. Updating the VERSION file if necessary

## Example Patch Script

Here's a complete example of a patch that adds a new feature:

```python
#!/usr/bin/env python3
"""
Patch 1.0.1 - Add support for Ruby language

Changes:
- Added Ruby language support to language detection
- Updated configuration to include Ruby file extensions
- Added Ruby-specific linting rules
- Fixed issue with LLM timeout handling

Author: AI Code Review Team
Date: 2024-01-15
"""

import os
import shutil
from pathlib import Path

def apply_patch():
    """Apply patch 1.0.1."""
    print("Applying patch 1.0.1...")
    
    project_root = Path(__file__).parent.parent.parent
    
    try:
        # Update language configuration
        update_language_config(project_root)
        
        # Add Ruby support to language detection
        update_language_detection(project_root)
        
        # Update requirements if needed
        update_requirements(project_root)
        
        print("Patch 1.0.1 applied successfully!")
        
    except Exception as e:
        print(f"Error applying patch 1.0.1: {e}")
        raise

def update_language_config(project_root: Path):
    """Update language configuration to include Ruby."""
    config_file = project_root / 'src' / 'config' / 'languages.py'
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Add Ruby to supported languages
        if 'ruby' not in content.lower():
            # Add Ruby configuration
            ruby_config = '''
    "ruby": {
        "extensions": [".rb", ".erb", ".rake", ".gemspec"],
        "keywords": ["def", "class", "module", "require", "include", "extend"],
        "comment_patterns": ["#", "=begin", "=end"],
        "string_patterns": ['"', "'", "`"]
    },
'''
            # Insert Ruby config in the appropriate place
            content = content.replace('"python": {', ruby_config + '    "python": {')
            
            with open(config_file, 'w') as f:
                f.write(content)
            
            print("Updated language configuration for Ruby")

def update_language_detection(project_root: Path):
    """Update language detection to include Ruby."""
    detection_file = project_root / 'src' / 'ingestion.py'
    
    if detection_file.exists():
        with open(detection_file, 'r') as f:
            content = f.read()
        
        # Add Ruby file extensions to detection
        if '.rb' not in content:
            # Find the file extension patterns and add Ruby
            content = content.replace(
                'SUPPORTED_EXTENSIONS = [',
                'SUPPORTED_EXTENSIONS = [".rb", ".erb", ".rake", ".gemspec", '
            )
            
            with open(detection_file, 'w') as f:
                f.write(content)
            
            print("Updated language detection for Ruby")

def update_requirements(project_root: Path):
    """Update requirements.txt if needed."""
    requirements_file = project_root / 'requirements.txt'
    
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            content = f.read()
        
        # Add Ruby-specific dependencies if needed
        if 'ruby' not in content.lower():
            # Add any Ruby-specific Python packages here
            pass

if __name__ == "__main__":
    apply_patch()
```

## Troubleshooting

### Common Issues

1. **Patch Not Found**: Ensure the patch file exists and follows the naming convention
2. **Permission Errors**: Make sure you have write permissions to the project directory
3. **Import Errors**: Ensure all required modules are available
4. **Version Conflicts**: Check that the patch is compatible with your current version

### Getting Help

If you encounter issues with patches:

1. Check the patch history log: `logs/patch_history.log`
2. Review the backup directory: `backups/`
3. Check the main application logs: `logs/ai_reviewer.log`
4. Run the patch with verbose output to see detailed error messages 