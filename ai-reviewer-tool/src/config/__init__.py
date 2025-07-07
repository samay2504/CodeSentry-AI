"""
Configuration package for the AI Code Review Tool.

This package contains centralized configuration modules for:
- Language detection and mapping
- Prompt templates and customization
- Agent configurations
- File handling settings
"""

from .languages import (
    get_language_from_extension,
    get_supported_extensions,
    get_ignore_patterns,
    is_code_file,
    get_language_map,
    LANGUAGE_MAP,
    DEFAULT_CODE_EXTENSIONS,
    DEFAULT_IGNORE_PATTERNS
)

__all__ = [
    'get_language_from_extension',
    'get_supported_extensions', 
    'get_ignore_patterns',
    'is_code_file',
    'get_language_map',
    'LANGUAGE_MAP',
    'DEFAULT_CODE_EXTENSIONS',
    'DEFAULT_IGNORE_PATTERNS'
] 