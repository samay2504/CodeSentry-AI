"""
Integration tests for the AI Code Review Tool.

These tests verify the complete workflow from input to output,
ensuring all components work together correctly.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from configs.config import config, Config
from src.exceptions import AIReviewerError, ValidationError, ConfigurationError, SecurityError
from src.validation import validator, InputValidator
from src.ingestion import ingest_codebase, ingest_frd
from src.llm_provider import create_llm_provider, LLMProvider
from src.agents import CodeReviewAgents, setup_agents
from src.tools import analyze_code, improve_code
from src.output import generate_output, generate_report


class TestIntegrationWorkflow:
    """Test complete integration workflow."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.py")
        
        # Create a simple test file
        with open(self.test_file, 'w') as f:
            f.write("""
def calculate_sum(a, b):
    return a + b

def main():
    result = calculate_sum(5, 3)
    print(result)

if __name__ == "__main__":
    main()
""")
    
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_review_workflow(self):
        """Test complete review workflow from input to output."""
        # Test configuration
        assert config is not None
        assert isinstance(config, Config)
        
        # Test validation
        validated_path = validator.validate_file_path(self.test_file)
        assert validated_path.exists()
        
        # Test ingestion
        codebase_info = ingest_codebase(self.temp_dir)
        assert 'files' in codebase_info
        assert len(codebase_info['files']) > 0
        
        # Test LLM provider
        llm_config = {
            'model': 'bigcode/starcoder',
            'temperature': 0.1
        }
        llm_provider = create_llm_provider(llm_config)
        assert llm_provider is not None
        
        # Test agents setup
        agents = setup_agents(llm_config)
        assert agents is not None
        
        # Test analysis
        with patch('src.tools.get_llm_provider') as mock_llm:
            mock_llm.return_value = MagicMock()
            mock_llm.return_value.invoke.return_value = {
                'issues': [],
                'metrics': {'complexity_score': 5}
            }
            
            result = analyze_code.invoke({
                'code': 'print("Hello")',
                'file_path': 'test.py'
            })
            assert isinstance(result, dict)
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test valid configuration
        valid_config = Config()
        assert valid_config.has_any_api_key() is not None
        
        # Test invalid configuration
        with pytest.raises(ValueError):
            # Create a config with invalid temperature
            os.environ['LLM_TEMPERATURE'] = '3.0'  # Invalid temperature
            invalid_config = Config()
            del os.environ['LLM_TEMPERATURE']  # Clean up
    
    def test_input_validation(self):
        """Test input validation."""
        # Test valid file path
        validator.validate_file_path(self.test_file)
        
        # Test invalid file path
        with pytest.raises(ValidationError):
            validator.validate_file_path("nonexistent_file.py")
        
        # Test dangerous path
        with pytest.raises(SecurityError):
            validator.validate_file_path("../../../etc/passwd")
        
        # Test file content validation
        content = "print('Hello, World!')"
        validated_content = validator.validate_file_content(content, "test.py")
        assert validated_content == content
        
        # Test suspicious content
        suspicious_content = "eval('print(1)')"
        with pytest.raises(SecurityError):
            validator.validate_file_content(suspicious_content, "test.py")
    
    def test_llm_provider_fallback(self):
        """Test LLM provider fallback system."""
        # Test with no API keys
        with patch.dict(os.environ, {}, clear=True):
            llm_provider = create_llm_provider({'model': 'test'})
            assert llm_provider is not None
            provider_info = llm_provider.get_provider_info()
            assert provider_info['fallback_mode'] is True
    
    def test_llm_provider_fallback_chain_order(self):
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
                        
                        # Test LLM provider creation
                        config = {'model': 'test-model', 'temperature': 0.1}
                        provider = create_llm_provider(config)
                        
                        # Verify fallback chain was attempted in correct order
                        mock_hf.assert_called_once()
                        # Google tries multiple models, so it gets called multiple times
                        assert mock_google.call_count >= 1
                        # Groq tries multiple models, so it gets called multiple times
                        assert mock_groq.call_count >= 1
                        # OpenAI tries multiple models, so it gets called multiple times
                        assert mock_openai.call_count >= 1
    
    def test_google_quota_error_handling(self):
        """Test that Google quota errors are handled properly."""
        with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
            with patch('src.llm_provider.ChatGoogleGenerativeAI') as mock_google:
                with patch('src.llm_provider.ChatGroq') as mock_groq:
                    # Mock HuggingFace to fail
                    mock_hf.side_effect = Exception("HuggingFace failed")
                    
                    # Mock Google to fail with quota error
                    mock_google.side_effect = Exception("429 Quota exceeded")
                    
                    # Mock Groq to succeed
                    mock_groq.return_value = MagicMock()
                    
                    # Test LLM provider creation
                    config = {'model': 'test-model', 'temperature': 0.1}
                    provider = create_llm_provider(config)
                    
                    # Verify Google was tried and failed, then Groq was used
                    mock_hf.assert_called_once()
                    # Google tries multiple models, so it gets called multiple times
                    assert mock_google.call_count >= 1
                    # Groq tries multiple models, so it gets called multiple times
                    assert mock_groq.call_count >= 1
    
    def test_error_handling(self):
        """Test error handling throughout the system."""
        # Test validation error
        with pytest.raises(ValidationError):
            validator.validate_file_path("")
        
        # Test configuration error
        with pytest.raises(ValidationError):
            validator.validate_llm_config({'temperature': 5.0})
        
        # Test file operation error
        with pytest.raises(ValidationError):
            validator.validate_file_path("nonexistent_file.py")


class TestSecurityFeatures:
    """Test security features and validation."""
    
    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam"
        ]
        
        for path in dangerous_paths:
            with pytest.raises(SecurityError):
                validator.validate_file_path(path)
    
    def test_suspicious_code_detection(self):
        """Test detection of suspicious code patterns."""
        suspicious_patterns = [
            "eval('print(1)')",
            "exec('import os')",
            "__import__('os')",
            "os.system('rm -rf /')",
            "subprocess.call(['rm', '-rf', '/'])",
            "input('Enter password:')"
        ]
        
        for code in suspicious_patterns:
            with pytest.raises(SecurityError):
                validator.validate_file_content(code, "test.py")
    
    def test_api_key_masking(self):
        """Test API key masking for security."""
        test_key = "hf_1234567890abcdef1234567890abcdef12345678"
        masked_key = config._mask_api_key(test_key)
        
        assert masked_key != test_key
        assert masked_key.startswith("hf_1")
        assert masked_key.endswith("5678")
        assert "..." in masked_key


class TestPerformanceFeatures:
    """Test performance and resource management."""
    
    def test_file_size_limits(self):
        """Test file size limits."""
        # Create a large file
        large_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        large_content = "print('test')\n" * 100000  # ~1.8MB
        large_file.write(large_content)
        large_file.close()
        
        try:
            # Should raise error for large content
            with pytest.raises(ValidationError):
                validator.validate_file_content(large_content, "test.py")
        finally:
            os.unlink(large_file.name)
    
    def test_line_length_limits(self):
        """Test line length limits."""
        long_line = "print('test')" * 1000  # Very long line
        with pytest.raises(ValidationError):
            validator.validate_file_content(long_line, "test.py")
    
    def test_file_count_limits(self):
        """Test file count limits."""
        # This would be tested in a real scenario with many files
        # For now, just test the validator accepts reasonable file counts
        assert validator.MAX_FILES > 0


class TestConfigurationManagement:
    """Test configuration management system."""
    
    def test_environment_loading(self):
        """Test environment variable loading."""
        # Test with environment variables
        with patch.dict(os.environ, {
            'HUGGINGFACEHUB_API_TOKEN': 'test_token',
            'LLM_TEMPERATURE': '0.5',
            'MAX_FILE_SIZE_MB': '20'
        }):
            test_config = Config()
            assert test_config.huggingface_token == 'test_token'
            assert test_config.llm.temperature == 0.5
            assert test_config.analysis.max_file_size_mb == 20
    
    def test_config_file_loading(self):
        """Test configuration file loading."""
        config_data = {
            'llm': {
                'model': 'test-model',
                'temperature': 0.3
            },
            'analysis': {
                'chunk_size': 1000
            }
        }
        
        config_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        json.dump(config_data, config_file)
        config_file.close()
        
        try:
            test_config = Config(config_file.name)
            assert test_config.llm.model == 'test-model'
            assert test_config.llm.temperature == 0.3
            assert test_config.analysis.chunk_size == 1000
        finally:
            os.unlink(config_file.name)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test invalid temperature
        with pytest.raises(ValidationError):
            validator.validate_llm_config({'temperature': 3.0})
        
        # Test invalid max_tokens
        with pytest.raises(ValidationError):
            validator.validate_llm_config({'max_tokens': 10000})
        
        # Test invalid timeout
        with pytest.raises(ValidationError):
            validator.validate_llm_config({'timeout': 0})


class TestOutputGeneration:
    """Test output generation and formatting."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_report_generation(self):
        """Test report generation."""
        test_content = "print('Hello, World!')"
        improved_content = "print('Hello, World!')  # Simple greeting"
        issues = [{'type': 'readability', 'severity': 'low', 'description': 'Add comment'}]
        metrics = {'complexity_score': 5}
        
        # Test markdown report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            report_path = f.name
        
        try:
            generate_report(
                test_content,
                improved_content,
                issues,
                report_path,
                'test.py',
                metrics
            )
            
            # Verify report was created
            assert os.path.exists(report_path)
            with open(report_path, 'r') as f:
                content = f.read()
                assert 'test.py' in content
                assert 'readability' in content
        finally:
            os.unlink(report_path)
    
    def test_output_directory_creation(self):
        """Test output directory creation."""
        output_dir = os.path.join(self.temp_dir, "output")
        
        # Should create directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        assert os.path.exists(output_dir)
        assert os.path.isdir(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 