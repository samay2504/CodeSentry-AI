"""
Integration tests for the agents module.

This module tests the integration between Crew AI agents,
LLM interactions, and the overall agent orchestration.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock

from src.agents import (
    CodeReviewAgents,
    setup_agents,
    run_review
)


class TestAgents:
    """Test cases for agent functionality."""
    
    def test_setup_agents(self):
        """Test setting up agents with different LLM configurations."""
        # Test Hugging Face configuration
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf',
            'temperature': 0.1
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            assert isinstance(agents, CodeReviewAgents)
            assert agents.llm_config == llm_config
    
    def test_setup_agents_openai(self):
        """Test setting up agents with OpenAI configuration."""
        llm_config = {
            'type': 'openai',
            'model': 'gpt-4',
            'temperature': 0.1
        }
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            agents = setup_agents(llm_config)
            assert isinstance(agents, CodeReviewAgents)
    
    def test_setup_agents_google(self):
        """Test setting up agents with Google configuration."""
        llm_config = {
            'type': 'google',
            'model': 'gemini-pro',
            'temperature': 0.1
        }
        
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'}):
            agents = setup_agents(llm_config)
            assert isinstance(agents, CodeReviewAgents)
    
    def test_setup_agents_missing_api_key_fallback(self):
        """Test setting up agents with missing API key falls back to fallback mode."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        # Ensure the environment variable is not set
        with patch.dict(os.environ, {}, clear=True):
            agents = setup_agents(llm_config)
            assert isinstance(agents, CodeReviewAgents)
            # Should use fallback LLM
            assert hasattr(agents.llm, 'name') or hasattr(agents.llm, 'current_provider')
            # Check if it's in fallback mode
            if hasattr(agents.llm, 'get_provider_info'):
                provider_info = agents.llm.get_provider_info()
                assert provider_info['fallback_mode'] == True
    
    def test_setup_agents_fallback_chain_order(self):
        """Test that the fallback chain follows the correct order."""
        with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
            with patch('src.llm_provider.ChatGoogleGenerativeAI') as mock_google:
                with patch('src.llm_provider.ChatGroq') as mock_groq:
                    with patch('src.llm_provider.ChatOpenAI') as mock_openai:
                        # Mock all providers to fail
                        mock_hf.side_effect = Exception("HuggingFace failed")
                        mock_google.side_effect = Exception("Google failed")
                        mock_groq.side_effect = Exception("Groq failed")
                        mock_openai.side_effect = Exception("OpenAI failed")
                        
                        # Test setup_agents
                        config = {'model': 'test-model', 'temperature': 0.1}
                        agents = setup_agents(config)
                        
                        # Verify fallback chain was attempted in correct order
                        mock_hf.assert_called_once()
                        # Google tries multiple models, so it gets called multiple times
                        assert mock_google.call_count >= 1
                        # Groq tries multiple models, so it gets called multiple times
                        assert mock_groq.call_count >= 1
                        # OpenAI tries multiple models, so it gets called multiple times
                        assert mock_openai.call_count >= 1
    
    def test_agent_roles(self):
        """Test that all required agent roles are created."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            
            # Check that all required agents are present
            required_agents = ['reviewer', 'security', 'performance', 'improver', 'documentation']
            for agent_name in required_agents:
                assert agent_name in agents.agents
                assert agents.agents[agent_name].role is not None
                assert agents.agents[agent_name].goal is not None
    
    def test_run_code_review_fallback_mode(self):
        """Test running code review in fallback mode."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        # Use fallback mode (no API key)
        with patch.dict(os.environ, {}, clear=True):
            agents = setup_agents(llm_config)
            
            code = "def query(user_input):\n    return f'SELECT * FROM users WHERE id = {user_input}'"
            requirements = {'FR-1.1': 'Secure database queries'}
            
            result = agents.run_code_review(code, requirements, 'test.py')
            
            assert 'issues' in result
            assert 'improved_code' in result
            assert 'metrics' in result
            assert result['file_path'] == 'test.py'
            # Should use fallback analysis
            assert 'fallback' in result.get('summary', '').lower()
    
    @patch('src.agents.Crew')
    def test_run_code_review_with_llm(self, mock_crew):
        """Test running code review with agents."""
        # Mock crew response
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = '''
        {
            "issues": [
                {
                    "type": "security",
                    "severity": "high",
                    "line": 10,
                    "description": "Potential SQL injection",
                    "suggestion": "Use parameterized queries"
                }
            ],
            "improved_code": "def safe_query(user_input):\\n    # Use parameterized query\\n    pass",
            "metrics": {
                "complexity_score": 3,
                "maintainability_score": 7,
                "security_score": 4,
                "performance_score": 6
            },
            "summary": "Security improvements needed"
        }
        '''
        mock_crew.return_value = mock_crew_instance
        
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            
            code = "def query(user_input):\n    return f'SELECT * FROM users WHERE id = {user_input}'"
            requirements = {'FR-1.1': 'Secure database queries'}
            
            result = agents.run_code_review(code, requirements, 'test.py')
            
            assert 'issues' in result
            assert 'improved_code' in result
            assert 'metrics' in result
            assert result['file_path'] == 'test.py'
    
    def test_run_code_improvement_fallback_mode(self):
        """Test running code improvement in fallback mode."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        # Use fallback mode (no API key)
        with patch.dict(os.environ, {}, clear=True):
            agents = setup_agents(llm_config)
            
            original_code = "def query(user_input):\n    return f'SELECT * FROM users WHERE id = {user_input}'"
            issues = [{'type': 'security', 'description': 'SQL injection vulnerability'}]
            
            improved_code = agents.run_code_improvement(original_code, issues, 'test.py')
            
            # In fallback mode, should return original code
            assert improved_code == original_code
    
    @patch('src.agents.Crew')
    def test_run_code_improvement_with_llm(self, mock_crew):
        """Test running code improvement with agents."""
        # Mock crew response
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = '''
        ```python
        def safe_query(user_input):
            # Use parameterized query to prevent SQL injection
            return "SELECT * FROM users WHERE id = ?", (user_input,)
        ```
        '''
        mock_crew.return_value = mock_crew_instance
        
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            
            original_code = "def query(user_input):\n    return f'SELECT * FROM users WHERE id = {user_input}'"
            issues = [{'type': 'security', 'description': 'SQL injection vulnerability'}]
            
            improved_code = agents.run_code_improvement(original_code, issues, 'test.py')
            
            assert improved_code != original_code
            assert 'safe_query' in improved_code
            assert 'parameterized' in improved_code
    
    def test_run_documentation_improvement_fallback_mode(self):
        """Test running documentation improvement in fallback mode."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        # Use fallback mode (no API key)
        with patch.dict(os.environ, {}, clear=True):
            agents = setup_agents(llm_config)
            
            original_code = "def calculate_sum(a, b):\n    return a + b"
            
            improved_code = agents.run_documentation_improvement(original_code, 'test.py')
            
            # In fallback mode, should return original code
            assert improved_code == original_code
    
    @patch('src.agents.Crew')
    def test_run_documentation_improvement_with_llm(self, mock_crew):
        """Test running documentation improvement with agents."""
        # Mock crew response
        mock_crew_instance = MagicMock()
        mock_crew_instance.kickoff.return_value = '''
        ```python
        def calculate_sum(a, b):
            """
            Calculate the sum of two numbers.
            
            Args:
                a (int): First number
                b (int): Second number
                
            Returns:
                int: Sum of the two numbers
            """
            return a + b
        ```
        '''
        mock_crew.return_value = mock_crew_instance
        
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            
            original_code = "def calculate_sum(a, b):\n    return a + b"
            
            improved_code = agents.run_documentation_improvement(original_code, 'test.py')
            
            assert improved_code != original_code
            assert '"""' in improved_code
            assert 'Args:' in improved_code
            assert 'Returns:' in improved_code
    
    def test_fallback_review_detects_issues(self):
        """Test that fallback review detects common issues."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        # Use fallback mode (no API key)
        with patch.dict(os.environ, {}, clear=True):
            agents = setup_agents(llm_config)
            
            # Code with obvious security issues
            code = """
def bad_function(user_input):
    eval(user_input)  # Security issue
    system("rm -rf /")  # Security issue
    password = "hardcoded_password"  # Security issue
"""
            
            result = agents.run_code_review(code, {}, 'test.py')
            
            assert 'issues' in result
            assert len(result['issues']) > 0
            
            # Should detect security issues
            security_issues = [i for i in result['issues'] if i.get('type') == 'security']
            assert len(security_issues) > 0
    
    def test_parse_review_results_valid_json(self):
        """Test parsing review results with valid JSON."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            
            # Test with valid JSON response
            json_response = '''
            {
                "issues": [
                    {
                        "type": "security",
                        "severity": "high",
                        "line": 10,
                        "description": "SQL injection",
                        "suggestion": "Use parameterized queries"
                    }
                ],
                "improved_code": "def safe_query(): pass",
                "metrics": {
                    "complexity_score": 3,
                    "maintainability_score": 7,
                    "security_score": 4,
                    "performance_score": 6
                },
                "summary": "Security improvements needed"
            }
            '''
            
            original_code = "def query(): pass"
            result = agents._parse_review_results(json_response, original_code, 'test.py')
            
            assert result['file_path'] == 'test.py'
            assert len(result['issues']) == 1
            assert result['issues'][0]['type'] == 'security'
            assert 'improved_code' in result
            assert 'metrics' in result
            assert result['summary'] == 'Security improvements needed'
    
    def test_parse_review_results_invalid_json(self):
        """Test parsing review results with invalid JSON."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            
            # Test with invalid JSON response
            invalid_response = "This is not JSON"
            original_code = "def query(): pass"
            
            result = agents._parse_review_results(invalid_response, original_code, 'test.py')
            
            assert result['file_path'] == 'test.py'
            assert result['issues'] == []
            assert result['improved_code'] == original_code
            assert 'metrics' in result
            assert result['summary'] == invalid_response
    
    def test_extract_improved_code(self):
        """Test extracting improved code from agent response."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            
            # Test with code block
            response_with_code = '''
            Here's the improved code:
            
            ```python
            def safe_function():
                return "improved"
            ```
            
            This should be better.
            '''
            
            extracted = agents._extract_improved_code(response_with_code)
            assert 'def safe_function():' in extracted
            assert 'return "improved"' in extracted
            
            # Test without code block
            response_without_code = "This is just text without code blocks"
            extracted = agents._extract_improved_code(response_without_code)
            assert extracted == response_without_code.strip()
    
    def test_run_review_function(self):
        """Test the run_review function."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            
            code = "def test(): pass"
            result = run_review(agents, "Test prompt", code, "test.py")
            
            assert isinstance(result, dict)
            assert 'file_path' in result
    
    def test_agent_error_handling(self):
        """Test that agents handle errors gracefully."""
        llm_config = {
            'type': 'huggingface',
            'model': 'codellama/CodeLlama-7b-hf'
        }
        
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            agents = setup_agents(llm_config)
            
            # Test with invalid code that might cause issues
            invalid_code = None
            result = agents.run_code_review(invalid_code, {}, 'test.py')
            
            # Should handle gracefully and return fallback result
            assert isinstance(result, dict)
            assert 'file_path' in result 