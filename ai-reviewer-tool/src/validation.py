"""
Input validation utilities for the AI Code Review Tool.

This module provides comprehensive validation for all user inputs,
ensuring security, data integrity, and proper error handling.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse
import mimetypes

from .exceptions import ValidationError, SecurityError
# Lazy import to avoid circular dependencies
def _get_config():
    try:
        from configs.config import config
        return config
    except ImportError:
        # Fallback for when configs is not in path
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from configs.config import config
        return config


class InputValidator:
    """Comprehensive input validation for the AI Code Review Tool."""
    
    # File extensions that are allowed for analysis
    ALLOWED_EXTENSIONS = {
        # Programming languages
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
        '.m', '.mm', '.pl', '.sh', '.bat', '.ps1', '.sql', '.r', '.dart',
        
        # Web technologies
        '.html', '.htm', '.css', '.scss', '.sass', '.less', '.xml', '.json',
        '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
        
        # Documentation
        '.md', '.txt', '.rst', '.tex', '.adoc',
        
        # Configuration files
        '.env', '.gitignore', '.dockerfile', '.dockerignore',
        'dockerfile', 'makefile', 'cmakelists.txt'
    }
    
    # Dangerous file extensions that should be excluded
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.war', '.ear', '.apk', '.dmg', '.deb', '.rpm', '.msi'
    }
    
    # Maximum file sizes (in bytes)
    @property
    def MAX_FILE_SIZE(self):
        return _get_config().security.max_input_size_mb * 1024 * 1024
    
    # Maximum number of files to process
    MAX_FILES = 1000
    
    # Maximum line length for code files
    MAX_LINE_LENGTH = 10000
    
    # Maximum number of lines per file
    MAX_LINES_PER_FILE = 50000
    
    # URL patterns for Git repositories
    GIT_URL_PATTERNS = [
        r'^https?://github\.com/[^/]+/[^/]+/?$',
        r'^https?://gitlab\.com/[^/]+/[^/]+/?$',
        r'^https?://bitbucket\.org/[^/]+/[^/]+/?$',
        r'^git@github\.com:[^/]+/[^/]+\.git$',
        r'^git@gitlab\.com:[^/]+/[^/]+\.git$',
        r'^git@bitbucket\.org:[^/]+/[^/]+\.git$'
    ]
    
    def __init__(self):
        """Initialize the validator with configuration."""
        self._config = None
    
    @property
    def config(self):
        """Lazy load configuration."""
        if self._config is None:
            self._config = _get_config()
        return self._config
    
    def validate_file_path(self, file_path: str) -> Path:
        """Validate a file path and return a Path object."""
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("File path must be a non-empty string")
        
        # Check for path traversal attacks
        if '..' in file_path or file_path.startswith('/'):
            raise SecurityError("Path traversal detected in file path")
        
        path = Path(file_path)
        
        # Check if file exists (handle permission errors gracefully)
        try:
            if not path.exists():
                raise ValidationError(f"File does not exist: {file_path}")
        except PermissionError:
            # If we can't access the file due to permissions, it's likely a system file
            # This is still a security concern, so raise SecurityError
            raise SecurityError(f"Access denied to file: {file_path}")
        
        # Check if it's actually a file
        if not path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE} bytes)"
            )
        
        return path
    
    def validate_directory_path(self, dir_path: str) -> Path:
        """Validate a directory path and return a Path object."""
        if not dir_path or not isinstance(dir_path, str):
            raise ValidationError("Directory path must be a non-empty string")
        
        # Check for path traversal attacks
        if '..' in dir_path or dir_path.startswith('/'):
            raise SecurityError("Path traversal detected in directory path")
        
        path = Path(dir_path)
        
        # Check if directory exists (handle permission errors gracefully)
        try:
            if not path.exists():
                raise ValidationError(f"Directory does not exist: {dir_path}")
        except PermissionError:
            # If we can't access the directory due to permissions, it's likely a system directory
            # This is still a security concern, so raise SecurityError
            raise SecurityError(f"Access denied to directory: {dir_path}")
        
        # Check if it's actually a directory
        if not path.is_dir():
            raise ValidationError(f"Path is not a directory: {dir_path}")
        
        return path
    
    def validate_git_url(self, url: str) -> str:
        """Validate a Git repository URL."""
        if not url or not isinstance(url, str):
            raise ValidationError("Git URL must be a non-empty string")
        
        # Check URL length
        if len(url) > 500:
            raise ValidationError("Git URL too long")
        
        # Validate URL format
        for pattern in self.GIT_URL_PATTERNS:
            if re.match(pattern, url):
                return url
        
        raise ValidationError(f"Invalid Git URL format: {url}")
    
    def validate_file_extension(self, file_path: str) -> bool:
        """Validate if a file extension is allowed for analysis."""
        if not file_path:
            return False
        
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Check for dangerous extensions
        if extension in self.DANGEROUS_EXTENSIONS:
            raise SecurityError(f"Dangerous file extension not allowed: {extension}")
        
        # Check if extension is in allowed list
        if extension in self.ALLOWED_EXTENSIONS:
            return True
        
        # Check for files without extension (like Makefile)
        filename = path.name.lower()
        if filename in self.ALLOWED_EXTENSIONS:
            return True
        
        return False
    
    def validate_file_content(self, content: str, file_path: str) -> str:
        """Validate file content for security and size issues."""
        if not isinstance(content, str):
            raise ValidationError("File content must be a string")
        
        # Check content length
        if len(content) > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"File content too large: {len(content)} characters"
            )
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
            r'os\.system\s*\(',
            r'subprocess\.call\s*\(',
            r'input\s*\(',
            r'raw_input\s*\(',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                raise SecurityError(f"Suspicious code pattern detected: {pattern}")
        
        # Check line length
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > self.MAX_LINE_LENGTH:
                raise ValidationError(
                    f"Line {i} too long: {len(line)} characters"
                )
        
        # Check number of lines
        if len(lines) > self.MAX_LINES_PER_FILE:
            raise ValidationError(
                f"Too many lines: {len(lines)} (max: {self.MAX_LINES_PER_FILE})"
            )
        
        return content
    
    def validate_api_key(self, api_key: str, provider: str) -> str:
        """Validate the format and presence of an API key for a given provider."""
        if not api_key or not isinstance(api_key, str):
            raise ValidationError(f"{provider} API key must be a non-empty string")
        
        # Check key length (minimum reasonable length)
        if len(api_key) < 10:
            raise ValidationError(f"{provider} API key too short")
        
        # Check for common patterns
        if api_key.lower() in ['none', 'null', 'undefined', '']:
            raise ValidationError(f"{provider} API key cannot be empty")
        
        return api_key
    
    def validate_llm_config(self, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the structure and required fields of an LLM configuration dictionary."""
        if not isinstance(llm_config, dict):
            raise ValidationError("LLM config must be a dictionary")
        
        validated_config = {}
        
        # Validate model name
        if 'model' in llm_config:
            model = llm_config['model']
            if not isinstance(model, str) or len(model) < 1:
                raise ValidationError("Model name must be a non-empty string")
            validated_config['model'] = model
        
        # Validate temperature
        if 'temperature' in llm_config:
            temp = llm_config['temperature']
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                raise ValidationError("Temperature must be a number between 0 and 2")
            validated_config['temperature'] = float(temp)
        
        # Validate max_tokens
        if 'max_tokens' in llm_config:
            tokens = llm_config['max_tokens']
            if not isinstance(tokens, int) or tokens < 1 or tokens > 8192:
                raise ValidationError("max_tokens must be an integer between 1 and 8192")
            validated_config['max_tokens'] = tokens
        
        # Validate timeout
        if 'timeout' in llm_config:
            timeout = llm_config['timeout']
            if not isinstance(timeout, (int, float)) or timeout < 1 or timeout > 300:
                raise ValidationError("timeout must be a number between 1 and 300 seconds")
            validated_config['timeout'] = float(timeout)
        
        return validated_config
    
    def validate_focus_areas(self, focus_areas: Union[str, List[str]]) -> List[str]:
        """Validate and normalize the list of focus areas for analysis or improvement."""
        if isinstance(focus_areas, str):
            focus_areas = [area.strip() for area in focus_areas.split(',')]
        
        if not isinstance(focus_areas, list):
            raise ValidationError("Focus areas must be a string or list")
        
        valid_areas = {'security', 'performance', 'readability', 'maintainability', 'all'}
        
        for area in focus_areas:
            if area not in valid_areas:
                raise ValidationError(f"Invalid focus area: {area}")
        
        return focus_areas
    
    def validate_output_format(self, format_str: str) -> str:
        """Validate and return a supported output format string."""
        valid_formats = {'markdown', 'json', 'html'}
        
        if format_str not in valid_formats:
            raise ValidationError(f"Invalid output format: {format_str}")
        
        return format_str
    
    def validate_exclude_patterns(self, patterns: Union[str, List[str]]) -> List[str]:
        """Validate and normalize exclude patterns for file/directory filtering."""
        if isinstance(patterns, str):
            patterns = [pattern.strip() for pattern in patterns.split(',')]
        
        if not isinstance(patterns, list):
            raise ValidationError("Exclude patterns must be a string or list")
        
        # Validate each pattern
        for pattern in patterns:
            if not isinstance(pattern, str) or len(pattern) == 0:
                raise ValidationError("Exclude pattern must be a non-empty string")
            
            # Check for dangerous patterns
            if '..' in pattern or pattern.startswith('/'):
                raise SecurityError("Dangerous exclude pattern detected")
        
        return patterns
    
    def validate_zip_file(self, zip_path: str) -> Path:
        """Validate a ZIP file path and return a Path object if valid."""
        path = self.validate_file_path(zip_path)
        
        # Check file extension
        if not path.suffix.lower() == '.zip':
            raise ValidationError("File must be a ZIP archive")
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValidationError(f"ZIP file too large: {file_size} bytes")
        
        return path
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename to remove or replace unsafe characters."""
        if not filename:
            return "unnamed_file"
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limit length
        if len(sanitized) > 255:
            sanitized = sanitized[:255]
        
        # Ensure it's not empty after sanitization
        if not sanitized.strip():
            return "unnamed_file"
        
        return sanitized.strip()


# Global validator instance
validator = InputValidator() 