"""
Unit tests for the prompts module.
"""

import pytest
from src.prompts import (
    get_review_prompt,
    get_improvement_prompt,
    get_security_analysis_prompt,
    get_performance_analysis_prompt,
    get_documentation_prompt,
    get_summary_prompt,
    _format_requirements,
    _format_issues
)


class TestPrompts:
    """Test cases for prompt generation functionality."""
    
    def test_get_review_prompt(self):
        """Test generating a code review prompt."""
        requirements = {
            'FR-1.1': 'The system shall accept complete codebases.',
            'FR-1.2': 'The system shall support multiple languages.'
        }
        code = "def hello():\n    print('Hello, World!')"
        file_path = "test.py"
        
        prompt = get_review_prompt(requirements, code, file_path)
        
        assert isinstance(prompt, str)
        assert 'expert code reviewer' in prompt.lower()
        assert 'FR-1.1' in prompt
        assert 'FR-1.2' in prompt
        assert code in prompt
        assert file_path in prompt
        assert 'json' in prompt.lower()
    
    def test_get_review_prompt_empty_requirements(self):
        """Test generating a review prompt with empty requirements."""
        requirements = {}
        code = "print('Hello')"
        
        prompt = get_review_prompt(requirements, code)
        
        assert isinstance(prompt, str)
        assert 'no specific requirements provided' in prompt.lower()
        assert code in prompt
    
    def test_get_improvement_prompt(self):
        """Test generating a code improvement prompt."""
        original_code = "def hello():\n    print('Hello')"
        issues = [
            {
                'type': 'readability',
                'severity': 'medium',
                'line': 1,
                'description': 'Function lacks docstring'
            }
        ]
        file_path = "test.py"
        
        prompt = get_improvement_prompt(original_code, issues, file_path)
        
        assert isinstance(prompt, str)
        assert 'improved version' in prompt.lower()
        assert original_code in prompt
        assert 'readability' in prompt
        assert file_path in prompt
    
    def test_get_improvement_prompt_empty_issues(self):
        """Test generating an improvement prompt with no issues."""
        original_code = "print('Hello')"
        issues = []
        
        prompt = get_improvement_prompt(original_code, issues)
        
        assert isinstance(prompt, str)
        assert 'no issues identified' in prompt.lower()
        assert original_code in prompt
    
    def test_get_security_analysis_prompt(self):
        """Test generating a security analysis prompt."""
        code = "user_input = input('Enter data: ')\nexec(user_input)"
        file_path = "vulnerable.py"
        
        prompt = get_security_analysis_prompt(code, file_path)
        
        assert isinstance(prompt, str)
        assert 'security expert' in prompt.lower()
        assert 'security analysis' in prompt.lower()
        assert code in prompt
        assert file_path in prompt
        assert 'sql injection' in prompt.lower()
        assert 'xss' in prompt.lower()
        assert 'json' in prompt.lower()
    
    def test_get_performance_analysis_prompt(self):
        """Test generating a performance analysis prompt."""
        code = "for i in range(1000):\n    for j in range(1000):\n        result = i * j"
        file_path = "slow.py"
        
        prompt = get_performance_analysis_prompt(code, file_path)
        
        assert isinstance(prompt, str)
        assert 'performance optimization expert' in prompt.lower()
        assert 'performance analysis' in prompt.lower()
        assert code in prompt
        assert file_path in prompt
        assert 'algorithm efficiency' in prompt.lower()
        assert 'memory usage' in prompt.lower()
        assert 'json' in prompt.lower()
    
    def test_get_documentation_prompt(self):
        """Test generating a documentation improvement prompt."""
        code = "def calculate_area(radius):\n    return 3.14159 * radius * radius"
        file_path = "math.py"
        
        prompt = get_documentation_prompt(code, file_path)
        
        assert isinstance(prompt, str)
        assert 'technical documentation expert' in prompt.lower()
        assert 'improve the documentation' in prompt.lower()
        assert code in prompt
        assert file_path in prompt
        assert 'docstrings' in prompt.lower()
        assert 'comments' in prompt.lower()
    
    def test_get_summary_prompt(self):
        """Test generating a project summary prompt."""
        analysis_results = [
            {
                'file_path': 'test1.py',
                'issues': [{'type': 'syntax', 'severity': 'high'}],
                'metrics': {'complexity_score': 7}
            },
            {
                'file_path': 'test2.py',
                'issues': [{'type': 'security', 'severity': 'critical'}],
                'metrics': {'security_score': 3}
            }
        ]
        project_structure = {
            'languages': ['Python'],
            'file_types': ['.py'],
            'directories': ['src'],
            'dependencies': ['Python']
        }
        
        prompt = get_summary_prompt(analysis_results, project_structure)
        
        assert isinstance(prompt, str)
        assert 'senior software architect' in prompt.lower()
        assert 'comprehensive project summary' in prompt.lower()
        assert 'executive summary' in prompt.lower()
        assert 'technical analysis' in prompt.lower()
        assert 'Python' in prompt
    
    def test_format_requirements(self):
        """Test formatting requirements dictionary."""
        requirements = {
            'FR-1.1': 'Accept codebases in various formats',
            'FR-1.2': 'Support multiple programming languages',
            'NFR-1.1': 'Process up to 1GB codebases'
        }
        
        formatted = _format_requirements(requirements)
        
        assert isinstance(formatted, str)
        assert 'FR-1.1: Accept codebases' in formatted
        assert 'FR-1.2: Support multiple' in formatted
        assert 'NFR-1.1: Process up to' in formatted
    
    def test_format_requirements_empty(self):
        """Test formatting empty requirements."""
        requirements = {}
        
        formatted = _format_requirements(requirements)
        
        assert formatted == "No specific requirements provided."
    
    def test_format_issues(self):
        """Test formatting issues list."""
        issues = [
            {
                'type': 'syntax',
                'severity': 'critical',
                'line': 5,
                'description': 'Missing semicolon'
            },
            {
                'type': 'security',
                'severity': 'high',
                'description': 'SQL injection vulnerability'
            }
        ]
        
        formatted = _format_issues(issues)
        
        assert isinstance(formatted, str)
        assert '1. syntax - Missing semicolon (Line 5)' in formatted
        assert '2. security - SQL injection vulnerability' in formatted
    
    def test_format_issues_empty(self):
        """Test formatting empty issues list."""
        issues = []
        
        formatted = _format_issues(issues)
        
        assert formatted == "No issues identified."
    
    def test_format_issues_missing_fields(self):
        """Test formatting issues with missing fields."""
        issues = [
            {
                'type': 'unknown',
                'description': 'Some issue'
            }
        ]
        
        formatted = _format_issues(issues)
        
        assert '1. unknown - Some issue' in formatted
    
    def test_prompt_variables_consistency(self):
        """Test that all prompts use consistent variable names."""
        requirements = {'FR-1.1': 'Test requirement'}
        code = "print('test')"
        file_path = "test.py"
        issues = [{'type': 'test', 'description': 'test issue'}]
        
        # Test that all prompts handle the same input types
        review_prompt = get_review_prompt(requirements, code, file_path)
        improvement_prompt = get_improvement_prompt(code, issues, file_path)
        security_prompt = get_security_analysis_prompt(code, file_path)
        performance_prompt = get_performance_analysis_prompt(code, file_path)
        doc_prompt = get_documentation_prompt(code, file_path)
        
        # All prompts should be strings
        assert isinstance(review_prompt, str)
        assert isinstance(improvement_prompt, str)
        assert isinstance(security_prompt, str)
        assert isinstance(performance_prompt, str)
        assert isinstance(doc_prompt, str)
        
        # All prompts should contain the code
        assert code in review_prompt
        assert code in improvement_prompt
        assert code in security_prompt
        assert code in performance_prompt
        assert code in doc_prompt
    
    def test_prompt_length_reasonable(self):
        """Test that generated prompts are of reasonable length."""
        requirements = {'FR-1.1': 'Test requirement'}
        code = "print('test')"
        file_path = "test.py"
        
        prompt = get_review_prompt(requirements, code, file_path)
        
        # Prompt should be substantial but not excessive
        assert len(prompt) > 100  # Should have meaningful content
        assert len(prompt) < 10000  # Should not be excessively long
    
    def test_prompt_contains_required_elements(self):
        """Test that prompts contain all required elements."""
        requirements = {'FR-1.1': 'Test requirement'}
        code = "print('test')"
        file_path = "test.py"
        
        prompt = get_review_prompt(requirements, code, file_path)
        
        # Should contain key elements
        assert 'requirements' in prompt.lower()
        assert 'code' in prompt.lower()
        assert 'review' in prompt.lower()
        assert 'json' in prompt.lower()
        assert 'issues' in prompt.lower()
        assert 'improved_code' in prompt.lower()
        assert 'metrics' in prompt.lower()


if __name__ == '__main__':
    pytest.main([__file__]) 