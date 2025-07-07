import os
import pytest
from src.tools import analyze_code, improve_code, chunk_code


def test_analyze_code_basic():
    code = """
def add(a, b):
    return a + b
"""
    result = analyze_code.invoke({"code": code, "file_path": "test.py"})
    assert isinstance(result, dict)
    assert 'issues' in result
    assert 'metrics' in result
    assert 'file_path' in result


def test_analyze_code_empty():
    result = analyze_code.invoke({"code": "", "file_path": "empty.py"})
    assert isinstance(result, dict)
    assert 'issues' in result
    assert result['file_path'] == "empty.py"


def test_improve_code_basic():
    code = """
def add(a, b):
    return a + b
"""
    issues = [{
        'type': 'maintainability',
        'description': 'No docstring',
        'line': 1,
        'severity': 'low',
        'suggestion': 'Add a docstring'
    }]
    result = improve_code.invoke({"code": code, "issues": issues, "file_path": "test.py"})
    assert isinstance(result, dict)
    assert 'improved_code' in result


def test_improve_code_no_issues():
    code = "def foo():\n    pass"
    result = improve_code.invoke({"code": code, "issues": [], "file_path": "foo.py"})
    assert isinstance(result, dict)
    assert 'improved_code' in result


def test_chunk_code_basic():
    code = "\n".join([f"print({i})" for i in range(100)])
    chunks = chunk_code(code, max_tokens=10, overlap=2)
    assert isinstance(chunks, list)
    assert len(chunks) > 1
    # Overlap check: at least one of the last lines of the previous chunk appears at the start of the next chunk
    for i in range(1, len(chunks)):
        prev = chunks[i-1].split('\n')
        curr = chunks[i].split('\n')
        overlap = set(prev[-3:]) & set(curr[:3])  # check for any overlap in last/first 3 lines
        assert overlap, f"No overlap between chunk {i-1} and {i}"


def test_chunk_code_empty():
    chunks = chunk_code("", max_tokens=10, overlap=2)
    assert isinstance(chunks, list)
    assert len(chunks) == 1
    assert chunks[0] == "" 