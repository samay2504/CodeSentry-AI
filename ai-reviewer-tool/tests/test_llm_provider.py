#!/usr/bin/env python3
"""
Comprehensive tests for the LLM provider system including fallback chain and error handling.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.llm_provider import create_llm_provider, LLMProvider


class TestLLMProviderFallbackChain:
    """Test the updated fallback chain order and behavior."""
    
    def test_fallback_chain_order(self):
        """Test that fallback chain follows the correct order: HuggingFace → Google → Groq → OpenAI → Fallback."""
        # Test with no API keys - should use fallback
        with patch.dict(os.environ, {}, clear=True):
            provider = create_llm_provider({'model': 'test'})
            provider_info = provider.get_provider_info()
            assert provider_info['fallback_mode'] is True
            assert provider_info['provider'] == 'fallback'
    
    def test_huggingface_first_in_chain(self):
        """Test that HuggingFace is tried first when API key is available."""
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_llm = MagicMock()
                mock_llm.invoke.return_value = "Test response"
                mock_hf.return_value = mock_llm
                # Mock the token validation to succeed
                with patch('src.llm_provider.HfApi') as mock_api:
                    mock_api.return_value.list_models.return_value = [MagicMock()]
                    provider = create_llm_provider({'model': 'test'})
                    provider_info = provider.get_provider_info()
                    assert provider_info['provider'] == 'huggingface'
                    assert provider_info['fallback_mode'] is False
    
    def test_google_second_in_chain(self):
        """Test that Google is second in the fallback chain."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'}, clear=True):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.side_effect = Exception("HuggingFace failed")
                with patch('src.llm_provider.ChatGoogleGenerativeAI') as mock_google:
                    mock_google.return_value = MagicMock()
                    llm_provider = create_llm_provider({'model': 'test'})
                    provider_info = llm_provider.get_provider_info()
                    assert 'google' in provider_info['provider']
                    assert provider_info['fallback_mode'] is False
    
    def test_groq_third_in_chain(self):
        """Test that Groq is third in the fallback chain."""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}, clear=True):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.side_effect = Exception("HuggingFace failed")
                with patch('src.llm_provider.ChatGoogleGenerativeAI') as mock_google:
                    mock_google.side_effect = Exception("Google failed")
                    with patch('src.llm_provider.ChatGroq') as mock_groq:
                        mock_groq.return_value = MagicMock()
                        llm_provider = create_llm_provider({'model': 'test'})
                        provider_info = llm_provider.get_provider_info()
                        assert 'groq' in provider_info['provider']
                        assert provider_info['fallback_mode'] is False
    
    def test_openai_fourth_in_chain(self):
        """Test that OpenAI is fourth in the fallback chain."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}, clear=True):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.side_effect = Exception("HuggingFace failed")
                with patch('src.llm_provider.ChatGoogleGenerativeAI') as mock_google:
                    mock_google.side_effect = Exception("Google failed")
                    with patch('src.llm_provider.ChatGroq') as mock_groq:
                        mock_groq.side_effect = Exception("Groq failed")
                        with patch('src.llm_provider.ChatOpenAI') as mock_openai:
                            mock_openai.return_value = MagicMock()
                            llm_provider = create_llm_provider({'model': 'test'})
                            provider_info = llm_provider.get_provider_info()
                            assert 'openai' in provider_info['provider']
                            assert provider_info['fallback_mode'] is False
    
    def test_fallback_last_in_chain(self):
        """Test that fallback is used when all providers fail."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.side_effect = Exception("HuggingFace failed")
                with patch('src.llm_provider.ChatGoogleGenerativeAI') as mock_google:
                    mock_google.side_effect = Exception("Google failed")
                    with patch('src.llm_provider.ChatGroq') as mock_groq:
                        mock_groq.side_effect = Exception("Groq failed")
                        with patch('src.llm_provider.ChatOpenAI') as mock_openai:
                            mock_openai.side_effect = Exception("OpenAI failed")
                            provider = create_llm_provider({'model': 'test'})
                            provider_info = provider.get_provider_info()
                            assert provider_info['provider'] == 'fallback'
                            assert provider_info['fallback_mode'] is True


class TestGoogleGeminiQuotaHandling:
    """Test Google Gemini quota error handling (429 responses)."""
    
    def test_google_quota_error_fast_fail(self):
        """Test that Google fails fast on quota errors."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'}, clear=True):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.side_effect = Exception("HuggingFace failed")
                with patch('src.llm_provider.ChatGoogleGenerativeAI') as mock_google:
                    # Simulate quota error
                    mock_google.side_effect = Exception("429 Quota exceeded")
                    with patch('src.llm_provider.ChatGroq') as mock_groq:
                        mock_groq.return_value = MagicMock()
                        llm_provider = create_llm_provider({'model': 'test'})
                        provider_info = llm_provider.get_provider_info()
                        # Should skip Google and try Groq
                        assert 'groq' in provider_info['provider']
    
    def test_google_quota_error_no_retries(self):
        """Test that Google provider doesn't retry on quota errors."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'}):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.side_effect = Exception("HuggingFace failed")
                with patch('src.llm_provider.ChatGoogleGenerativeAI') as mock_google:
                    # Simulate quota error
                    mock_google.side_effect = Exception("429 Quota exceeded")
                    provider = create_llm_provider({'model': 'test'})
                    # Should not retry Google, should move to next provider
                    mock_google.assert_called_once()


class TestProviderLogging:
    """Test enhanced logging for provider attempts and failures."""
    
    def test_provider_attempt_logging(self):
        """Test that provider attempts are logged."""
        with patch('src.llm_provider.logger') as mock_logger:
            with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}, clear=True):
                with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                    mock_hf.return_value = MagicMock()
                    create_llm_provider({'model': 'test'})
                    mock_logger.info.assert_any_call("✅ Successfully initialized LLM provider: huggingface")
    
    def test_provider_failure_logging(self):
        """Test that provider failures are logged."""
        with patch('src.llm_provider.logger') as mock_logger:
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.side_effect = Exception("Authentication failed")
                create_llm_provider({'model': 'test'})
                mock_logger.warning.assert_any_call("❌ HuggingFace failed: Authentication failed")
    
    def test_groq_attempt_logging(self):
        """Test that Groq attempts are logged."""
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test_key'}):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.side_effect = Exception("HuggingFace failed")
                with patch('src.llm_provider.ChatGoogleGenerativeAI') as mock_google:
                    mock_google.side_effect = Exception("Google failed")
                    with patch('src.llm_provider.logger') as mock_logger:
                        with patch('src.llm_provider.ChatGroq') as mock_groq:
                            mock_groq.return_value = MagicMock()
                            provider = create_llm_provider({'model': 'test'})
                            # Check that Groq attempt was logged
                            mock_logger.info.assert_any_call("Attempting Groq provider...")


class TestLLMProviderInvocation:
    """Test LLM provider invocation and response handling."""
    
    def test_successful_invocation(self):
        """Test successful LLM invocation."""
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}, clear=True):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_response = MagicMock()
                mock_response.content = "This is a test response. How can I assist you today?"
                mock_hf.return_value = MagicMock()
                mock_hf.return_value.invoke.return_value = mock_response
                
                llm_provider = create_llm_provider({'model': 'test'})
                response = llm_provider.invoke("Test prompt")
                
                # Check that response contains expected content
                assert "test response" in response.lower()
    
    def test_fallback_invocation(self):
        """Test fallback LLM invocation."""
        with patch.dict(os.environ, {}, clear=True):
            provider = create_llm_provider({'model': 'test'})
            
            response = provider.invoke("Test prompt")
            # Fallback should return a basic response
            assert isinstance(response, str)
            assert len(response) > 0
    
    def test_invocation_error_handling(self):
        """Test error handling during LLM invocation."""
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}, clear=True):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.return_value = MagicMock()
                mock_hf.return_value.invoke.side_effect = Exception("Invocation failed")
                
                llm_provider = create_llm_provider({'model': 'test'})
                with pytest.raises(Exception):
                    llm_provider.invoke("Test prompt")


class TestConfigurationHandling:
    """Test configuration handling and validation."""
    
    def test_config_validation(self):
        """Test that invalid configurations are handled properly."""
        with patch.dict(os.environ, {}, clear=True):
            # Test with invalid config
            provider = create_llm_provider({'invalid_key': 'invalid_value'})
            # Should still create a provider (fallback)
            assert provider is not None
    
    def test_model_configuration(self):
        """Test that model configuration is properly handled."""
        with patch.dict(os.environ, {'HUGGINGFACEHUB_API_TOKEN': 'test_key'}, clear=True):
            with patch('src.llm_provider.HuggingFaceEndpoint') as mock_hf:
                mock_hf.return_value = MagicMock()
                config = {'model': 'custom-model', 'temperature': 0.5}
                create_llm_provider(config)
                mock_hf.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__]) 