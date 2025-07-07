"""
Unit tests for the ingestion module.

This module tests the ingestion functionality for FRD documents
and various codebase formats.
"""

import pytest
import tempfile
import os
import zipfile
import json
from unittest.mock import patch, MagicMock

from src.ingestion import (
    ingest_frd, 
    ingest_codebase, 
    CodebaseIngestionError,
    _parse_frd_content,
    get_ingestion_history
)


class TestIngestion:
    """Test cases for ingestion functionality."""
    
    def test_ingest_frd_valid_file(self):
        """Test ingesting a valid FRD file."""
        # Create a temporary FRD file
        frd_content = """
        FR-1.1: The system shall accept complete codebases in various formats.
        FR-1.2: The system shall support multiple programming languages.
        NFR-1.1: The system shall process codebases of up to 1GB in size.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            frd_path = f.name
            f.write(frd_content)
        
        try:
            requirements = ingest_frd(frd_path)
            
            assert len(requirements) == 3
            assert 'FR-1.1' in requirements
            assert 'FR-1.2' in requirements
            assert 'NFR-1.1' in requirements
            assert 'accept complete codebases' in requirements['FR-1.1']
            
        finally:
            os.unlink(frd_path)
    
    def test_ingest_frd_invalid_file(self):
        """Test ingesting a non-existent FRD file."""
        with pytest.raises(CodebaseIngestionError):
            ingest_frd("non_existent_file.md")
    
    def test_ingest_frd_empty_file(self):
        """Test ingesting an empty FRD file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            frd_path = f.name
        
        try:
            requirements = ingest_frd(frd_path)
            assert len(requirements) == 0
            
        finally:
            os.unlink(frd_path)
    
    def test_ingest_codebase_directory(self):
        """Test ingesting a directory codebase."""
        # Create a temporary directory with some code files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Python file
            python_file = os.path.join(temp_dir, "test.py")
            with open(python_file, 'w') as f:
                f.write("def hello():\n    print('Hello, World!')\n")
            
            # Create JavaScript file
            js_file = os.path.join(temp_dir, "test.js")
            with open(js_file, 'w') as f:
                f.write("function hello() {\n    console.log('Hello, World!');\n}\n")
            
            # Create a text file (should be included since .txt is in supported extensions)
            text_file = os.path.join(temp_dir, "exclude.txt")
            with open(text_file, 'w') as f:
                f.write("This should be included")
            
            codebase_info = ingest_codebase(temp_dir)
            
            assert codebase_info['type'] == 'directory'
            assert len(codebase_info['files']) == 3  # Python, JS, and text files
            file_names = [f['name'] for f in codebase_info['files']]
            assert 'test.py' in file_names
            assert 'test.js' in file_names
            assert 'exclude.txt' in file_names  # .txt files are included in supported extensions
    
    def test_ingest_codebase_zip(self):
        """Test ingesting a ZIP codebase."""
        # Create a temporary ZIP file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            zip_path = temp_zip.name
        
        try:
            with zipfile.ZipFile(zip_path, 'w') as zip_file:
                # Add Python file
                zip_file.writestr('test.py', "def hello():\n    print('Hello, World!')\n")
                # Add JavaScript file
                zip_file.writestr('test.js', "function hello() {\n    console.log('Hello, World!');\n}\n")
            
            codebase_info = ingest_codebase(zip_path)
            
            assert codebase_info['type'] == 'zip_file'
            assert len(codebase_info['files']) == 2
            file_names = [f['name'] for f in codebase_info['files']]
            assert 'test.py' in file_names
            assert 'test.js' in file_names
            
        finally:
            os.unlink(zip_path)
    
    def test_ingest_single_file(self):
        """Test ingesting a single code file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tmp_file:
            file_path = tmp_file.name
            tmp_file.write(b'print("Hello, World!")')
        
        try:
            # Test ingestion
            codebase_info = ingest_codebase(file_path)
            
            assert codebase_info['type'] == 'single_file'
            assert len(codebase_info['files']) == 1
            assert codebase_info['files'][0]['name'] == os.path.basename(file_path)
            assert codebase_info['files'][0]['content'] == 'print("Hello, World!")'
            
        finally:
            os.unlink(file_path)
    
    def test_ingest_codebase_invalid_path(self):
        """Test ingesting a non-existent codebase."""
        with pytest.raises(CodebaseIngestionError):
            ingest_codebase("non_existent_path")
    
    @patch('src.ingestion.git.Repo')
    def test_ingest_git_repository_url(self, mock_repo):
        """Test ingesting a Git repository from URL."""
        # Mock Git repository
        mock_repo_instance = MagicMock()
        mock_repo_instance.active_branch.name = 'main'
        mock_repo_instance.head.commit.hexsha = 'abc123'
        mock_repo_instance.head.commit.author.name = 'Test User'
        mock_repo_instance.head.commit.committed_datetime.isoformat.return_value = '2023-01-01T00:00:00'
        mock_repo.clone_from.return_value = mock_repo_instance
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files in temp directory
            test_files = {
                'test.py': 'print("Hello, World!")',
                'test.js': 'console.log("Hello, World!");'
            }
            
            for filename, content in test_files.items():
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w') as f:
                    f.write(content)
            
            # Mock the clone to use our temp directory
            mock_repo.clone_from.return_value = mock_repo_instance
            
            codebase_info = ingest_codebase("https://github.com/user/repo")
            
            assert codebase_info['type'] == 'git_repository'
            assert 'repo_info' in codebase_info
            assert codebase_info['repo_info']['url'] == 'https://github.com/user/repo'
    
    def test_parse_frd_content(self):
        """Test parsing FRD content."""
        content = """
        FR-1.1: The system shall accept complete codebases.
        FR-1.2: The system shall support multiple languages.
        NFR-1.1: The system shall be fast.
        """
        
        requirements = _parse_frd_content(content)
        
        assert len(requirements) == 3
        assert requirements['FR-1.1'] == 'The system shall accept complete codebases.'
        assert requirements['FR-1.2'] == 'The system shall support multiple languages.'
        assert requirements['NFR-1.1'] == 'The system shall be fast.'
    
    def test_detect_language(self):
        """Test language detection from filename."""
        from src.config.languages import get_language_from_extension
        assert get_language_from_extension('.py') == 'Python'
        assert get_language_from_extension('.js') == 'JavaScript'
        assert get_language_from_extension('.tsx') == 'React TSX'
        assert get_language_from_extension('.css') == 'CSS'
        assert get_language_from_extension('.java') == 'Java'
        assert get_language_from_extension('.cpp') == 'C++'
        assert get_language_from_extension('.xyz') == 'Unknown'
    
    def test_ingest_codebase_with_exclusions(self):
        """Test ingesting codebase with ignore patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files including some that should be ignored
            files_to_create = {
                'main.py': 'print("Hello")',
                'test.py': 'print("Test")',
                '__pycache__/cache.pyc': 'binary content',
                '.git/config': 'git config',
                'node_modules/package.json': '{"name": "test"}'
            }
            
            # Create directories
            os.makedirs(os.path.join(temp_dir, '__pycache__'), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, '.git'), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, 'node_modules'), exist_ok=True)
            
            for filename, content in files_to_create.items():
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w') as f:
                    f.write(content)
            
            codebase_info = ingest_codebase(temp_dir)
            
            # Should only include the Python files
            assert len(codebase_info['files']) == 2
            file_names = [f['name'] for f in codebase_info['files']]
            assert 'main.py' in file_names
            assert 'test.py' in file_names
    
    def test_get_ingestion_history(self):
        """Test getting ingestion history."""
        # This test would require a database setup
        # For now, just test that the function doesn't crash
        history = get_ingestion_history()
        assert isinstance(history, list)
    
    def test_codebase_info_structure(self):
        """Test that codebase_info has the expected structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple Python file
            python_file = os.path.join(temp_dir, "test.py")
            with open(python_file, 'w') as f:
                f.write("print('Hello, World!')")
            
            codebase_info = ingest_codebase(temp_dir)
            
            # Check required fields
            assert 'type' in codebase_info
            assert 'files' in codebase_info
            assert 'output_dir' in codebase_info
            assert 'total_files' in codebase_info
            
            # Check file structure
            assert len(codebase_info['files']) == 1
            file_info = codebase_info['files'][0]
            
            assert 'path' in file_info
            assert 'relative_path' in file_info
            assert 'name' in file_info
            assert 'content' in file_info
            assert 'size' in file_info
            assert 'language' in file_info 