"""
Centralized language configuration for the AI Code Review Tool.

This module provides a single source of truth for language detection
and file extension mapping used throughout the application.
"""

from pathlib import Path
from typing import Dict, Set
import os


# Centralized language mapping
LANGUAGE_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
    '.jsx': 'React JSX', '.tsx': 'React TSX', '.html': 'HTML',
    '.css': 'CSS', '.scss': 'SCSS', '.java': 'Java',
    '.cpp': 'C++', '.c': 'C', '.h': 'C Header', '.hpp': 'C++ Header',
    '.cs': 'C#', '.php': 'PHP', '.rb': 'Ruby', '.go': 'Go',
    '.rs': 'Rust', '.swift': 'Swift', '.kt': 'Kotlin',
    '.scala': 'Scala', '.clj': 'Clojure', '.hs': 'Haskell',
    '.ml': 'OCaml', '.fs': 'F#', '.sql': 'SQL', '.sh': 'Shell',
    '.bat': 'Batch', '.ps1': 'PowerShell', '.yaml': 'YAML',
    '.yml': 'YAML', '.json': 'JSON', '.xml': 'XML',
    '.md': 'Markdown', '.txt': 'Text', '.ini': 'INI',
    '.cfg': 'Config', '.conf': 'Config'
}

# Supported code file extensions (configurable via environment)
DEFAULT_CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
    '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.php', '.rb',
    '.go', '.rs', '.swift', '.kt', '.scala', '.clj', '.hs',
    '.ml', '.fs', '.sql', '.sh', '.bat', '.ps1', '.yaml',
    '.yml', '.json', '.xml', '.md', '.txt', '.ini', '.cfg', '.conf'
}

# Default ignore patterns (configurable via environment)
DEFAULT_IGNORE_PATTERNS = {
    '.git', '.svn', '.hg', '__pycache__', 'node_modules', '.venv',
    'venv', 'env', '.env', 'build', 'dist', 'target', 'bin', 'obj',
    '.DS_Store', 'Thumbs.db', '*.pyc', '*.pyo', '*.pyd', '*.so',
    '*.dll', '*.exe', '*.dylib', '*.a', '*.o'
}


def get_language_from_extension(file_path: str) -> str:
    """
    Get programming language from file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language name or 'Unknown' if not recognized
    """
    ext = Path(file_path).suffix.lower() if file_path else '.py'
    return LANGUAGE_MAP.get(ext, 'Unknown')


def get_supported_extensions() -> Set[str]:
    """
    Get supported file extensions from environment or use defaults.
    
    Returns:
        Set of supported file extensions
    """
    extensions_str = os.getenv('SUPPORTED_EXTENSIONS')
    if extensions_str:
        return set(extensions_str.split(','))
    return DEFAULT_CODE_EXTENSIONS


def get_ignore_patterns() -> Set[str]:
    """
    Get ignore patterns from environment or use defaults.
    
    Returns:
        Set of patterns to ignore
    """
    patterns_str = os.getenv('IGNORE_PATTERNS')
    if patterns_str:
        return set(patterns_str.split(','))
    return DEFAULT_IGNORE_PATTERNS


def is_code_file(filename: str) -> bool:
    """
    Check if a file is a code file based on its extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        True if it's a code file, False otherwise
    """
    ext = Path(filename).suffix.lower()
    return ext in get_supported_extensions()


def get_language_map() -> Dict[str, str]:
    """
    Get the complete language mapping dictionary.
    
    Returns:
        Dictionary mapping file extensions to language names
    """
    return LANGUAGE_MAP.copy() 