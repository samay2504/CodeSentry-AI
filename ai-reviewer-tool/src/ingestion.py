"""
Ingestion module for parsing functional requirements documents and codebases.

This module handles the ingestion of FRD documents and various codebase formats
including single files, ZIP archives, Git repositories, and directories.
"""

import sqlite3
import json
import zipfile
import tempfile
import shutil
import os
import re
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
import git
from urllib.parse import urlparse
import requests

from .config.languages import get_language_from_extension, get_supported_extensions, get_ignore_patterns

logger = logging.getLogger(__name__)


class CodebaseIngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass


def ingest_frd(frd_path: str) -> Dict[str, str]:
    """
    Ingests the functional requirements document.
    
    Args:
        frd_path: Path to FRD file.
        
    Returns:
        Dict of requirement IDs to descriptions.
        
    Raises:
        CodebaseIngestionError: If FRD file cannot be read or parsed.
    """
    try:
        if not os.path.exists(frd_path):
            raise CodebaseIngestionError(f"FRD file not found: {frd_path}")
        
        with open(frd_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse FRD content to extract requirements
        requirements = _parse_frd_content(content)
        
        # Store in SQLite for history
        _store_frd_history(frd_path, requirements)
        
        logger.info(f"Successfully ingested FRD from {frd_path}")
        return requirements
        
    except Exception as e:
        logger.error(f"Error ingesting FRD: {e}")
        raise CodebaseIngestionError(f"Failed to ingest FRD: {e}")


def ingest_codebase(codebase_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Ingests codebase from various formats.
    
    Args:
        codebase_path: Path to codebase (file, ZIP, Git repo, or directory).
        output_dir: Directory to extract codebase to (optional).
        
    Returns:
        Dictionary containing codebase information and file contents.
        
    Raises:
        CodebaseIngestionError: If codebase cannot be ingested.
    """
    try:
        # Determine input type and process accordingly
        if _is_git_repository(codebase_path):
            return _ingest_git_repository(codebase_path, output_dir)
        elif _is_zip_file(codebase_path):
            return _ingest_zip_file(codebase_path, output_dir)
        elif _is_single_file(codebase_path):
            return _ingest_single_file(codebase_path, output_dir)
        elif _is_directory(codebase_path):
            return _ingest_directory(codebase_path, output_dir)
        else:
            raise CodebaseIngestionError(f"Unsupported codebase format: {codebase_path}")
            
    except Exception as e:
        logger.error(f"Error ingesting codebase: {e}")
        raise CodebaseIngestionError(f"Failed to ingest codebase: {e}")


def _is_git_repository(path: str) -> bool:
    """Check if path is a Git repository URL or local repo."""
    # Check if it's a URL
    if path.startswith(('http://', 'https://', 'git://', 'ssh://')):
        return True
    
    # Check if it's a local Git repository
    try:
        git.Repo(path)
        return True
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        return False


def _is_zip_file(path: str) -> bool:
    """Check if path is a ZIP file."""
    return path.lower().endswith('.zip') and os.path.isfile(path)


def _is_single_file(path: str) -> bool:
    """Check if path is a single code file."""
    if not os.path.isfile(path):
        return False
    
    # Check if it's a code file
    return Path(path).suffix.lower() in get_supported_extensions()


def _is_directory(path: str) -> bool:
    """Check if path is a directory."""
    return os.path.isdir(path)


def _ingest_git_repository(repo_path: str, output_dir: str = None) -> Dict[str, Any]:
    """Ingest code from a Git repository."""
    try:
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="git_repo_")
        
        # Clone or pull the repository
        if repo_path.startswith(('http://', 'https://', 'git://', 'ssh://')):
            # Clone from URL
            repo = git.Repo.clone_from(repo_path, output_dir)
            logger.info(f"Cloned repository from {repo_path} to {output_dir}")
        else:
            # Copy local repository
            shutil.copytree(repo_path, output_dir, dirs_exist_ok=True)
            repo = git.Repo(output_dir)
            logger.info(f"Copied local repository from {repo_path} to {output_dir}")
        
        # Get repository information
        repo_info = {
            'url': repo_path,
            'branch': repo.active_branch.name,
            'commit': repo.head.commit.hexsha,
            'author': repo.head.commit.author.name,
            'date': repo.head.commit.committed_datetime.isoformat()
        }
        
        # Extract all code files
        files = _extract_code_files(output_dir)
        
        return {
            'type': 'git_repository',
            'repo_info': repo_info,
            'files': files,
            'output_dir': output_dir,
            'total_files': len(files)
        }
        
    except Exception as e:
        logger.error(f"Error ingesting Git repository: {e}")
        raise CodebaseIngestionError(f"Failed to ingest Git repository: {e}")


def _ingest_zip_file(zip_path: str, output_dir: str = None) -> Dict[str, Any]:
    """Ingest code from a ZIP file."""
    try:
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="zip_extract_")
        
        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        logger.info(f"Extracted ZIP file {zip_path} to {output_dir}")
        
        # Extract all code files
        files = _extract_code_files(output_dir)
        
        return {
            'type': 'zip_file',
            'zip_path': zip_path,
            'files': files,
            'output_dir': output_dir,
            'total_files': len(files)
        }
        
    except Exception as e:
        logger.error(f"Error ingesting ZIP file: {e}")
        raise CodebaseIngestionError(f"Failed to ingest ZIP file: {e}")


def _ingest_single_file(file_path: str, output_dir: str = None) -> Dict[str, Any]:
    """Ingest a single code file."""
    try:
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="single_file_")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Copy file to output directory
        file_name = os.path.basename(file_path)
        output_file = os.path.join(output_dir, file_name)
        shutil.copy2(file_path, output_file)
        
        logger.info(f"Ingested single file {file_path}")
        
        return {
            'type': 'single_file',
            'file_path': file_path,
            'files': [{
                'path': output_file,
                'name': file_name,
                'content': content,
                'size': len(content),
                'language': get_language_from_extension(file_name)
            }],
            'output_dir': output_dir,
            'total_files': 1
        }
        
    except Exception as e:
        logger.error(f"Error ingesting single file: {e}")
        raise CodebaseIngestionError(f"Failed to ingest single file: {e}")


def _ingest_directory(dir_path: str, output_dir: str = None) -> Dict[str, Any]:
    """Ingest code from a directory."""
    try:
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="dir_copy_")
        
        # Copy directory contents
        shutil.copytree(dir_path, output_dir, dirs_exist_ok=True)
        
        logger.info(f"Copied directory {dir_path} to {output_dir}")
        
        # Extract all code files
        files = _extract_code_files(output_dir)
        
        return {
            'type': 'directory',
            'dir_path': dir_path,
            'files': files,
            'output_dir': output_dir,
            'total_files': len(files)
        }
        
    except Exception as e:
        logger.error(f"Error ingesting directory: {e}")
        raise CodebaseIngestionError(f"Failed to ingest directory: {e}")


def _extract_code_files(directory: str) -> List[Dict[str, Any]]:
    """Extract all code files from a directory."""
    files = []
    
    # Get supported extensions and ignore patterns from centralized config
    code_extensions = get_supported_extensions()
    ignore_patterns = get_ignore_patterns()
    
    # Get max file size from environment (convert MB to bytes)
    max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', '10'))  # 10MB default
    max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
    
    for root, dirs, filenames in os.walk(directory):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_patterns]
        
        for filename in filenames:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, directory)
            
            # Skip ignored files
            if any(pattern in relative_path for pattern in ignore_patterns):
                continue
            
            # Check if it's a code file
            if Path(filename).suffix.lower() in code_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check file size limit
                    if len(content) > max_file_size:
                        logger.warning(f"File {file_path} exceeds size limit, skipping")
                        continue
                    
                    files.append({
                        'path': file_path,
                        'relative_path': relative_path,
                        'name': filename,
                        'content': content,
                        'size': len(content),
                        'language': get_language_from_extension(filename)
                    })
                except UnicodeDecodeError:
                    logger.warning(f"Could not read file as text: {file_path}")
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
    
    return files





def _parse_frd_content(content: str) -> Dict[str, str]:
    """Parse FRD content to extract requirements."""
    requirements = {}
    
    # Pattern to match requirement IDs (e.g., FR-1.1, NFR-2.1, etc.)
    requirement_pattern = r'([A-Z]{2,3}-\d+\.\d+):\s*(.+)'
    
    lines = content.split('\n')
    for line in lines:
        match = re.search(requirement_pattern, line.strip())
        if match:
            req_id = match.group(1)
            description = match.group(2).strip()
            requirements[req_id] = description
    
    return requirements


def _store_frd_history(frd_path: str, requirements: Dict[str, str]) -> None:
    """Store FRD ingestion history in SQLite."""
    try:
        db_path = os.getenv('DATABASE_PATH', 'database.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS frd_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frd_path TEXT NOT NULL,
                requirements TEXT NOT NULL,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert record
        cursor.execute(
            'INSERT INTO frd_history (frd_path, requirements) VALUES (?, ?)',
            (frd_path, json.dumps(requirements))
        )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.warning(f"Failed to store FRD history: {e}")


def get_ingestion_history() -> List[Dict[str, Any]]:
    """Get ingestion history from database."""
    try:
        db_path = os.getenv('DATABASE_PATH', 'database.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT frd_path, requirements, ingested_at 
            FROM frd_history 
            ORDER BY ingested_at DESC
        ''')
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'frd_path': row[0],
                'requirements': json.loads(row[1]),
                'ingested_at': row[2]
            })
        
        conn.close()
        return history
        
    except Exception as e:
        logger.warning(f"Failed to get ingestion history: {e}")
        return [] 