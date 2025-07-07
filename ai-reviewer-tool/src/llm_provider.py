"""
LLM Provider System with Multiple Fallbacks
Handles HuggingFace, Google Gemini, OpenAI, and Groq with robust error handling
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it

# Import all possible LLM providers
try:
    from langchain_huggingface import HuggingFaceEndpoint
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from huggingface_hub import HfApi
    HF_API_AVAILABLE = True
except ImportError:
    HF_API_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMProvider:
    """Robust LLM provider with multiple fallback options."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_provider = None
        self.llm = None
        self._setup_llm()
    
    def _setup_llm(self):
        """Setup LLM with fallback chain: HuggingFace -> Google -> Groq -> OpenAI -> Fallback"""
        providers = [
            ("HuggingFace", self._try_huggingface),
            ("Google Gemini", self._try_google_genai),
            ("Groq", self._try_groq),
            ("OpenAI", self._try_openai),
            ("Fallback", self._create_fallback_llm)
        ]
        
        for provider_name, provider_func in providers:
            try:
                logger.info(f"Attempting {provider_name} provider...")
                self.llm = provider_func()
                if self.llm:
                    logger.info(f"✅ Successfully initialized LLM provider: {self.current_provider}")
                    return
            except Exception as e:
                logger.warning(f"❌ {provider_name} failed: {e}")
                # If it's a quota/rate limit error, log it clearly
                if "quota" in str(e).lower() or "429" in str(e) or "rate" in str(e).lower():
                    logger.warning(f"🚫 {provider_name} quota/rate limit exceeded, moving to next provider")
                continue
        
        # If all providers fail, create fallback
        self.llm = self._create_fallback_llm()
        logger.warning("All LLM providers failed, using fallback mode")
    
    def _test_huggingface_token(self) -> bool:
        """Test if HuggingFace token has proper permissions."""
        if not HF_API_AVAILABLE:
            return False
        
        try:
            api_key = os.getenv('HUGGINGFACEHUB_API_TOKEN')
            if not api_key:
                return False
            
            api = HfApi(token=api_key)
            # Test with a simple API call
            models = list(api.list_models(author="bigcode", limit=1))
            logger.info("HuggingFace token validated successfully")
            return True
        except Exception as e:
            logger.warning(f"HuggingFace token validation failed: {e}")
            return False
    
    def _try_huggingface(self):
        """Try to initialize HuggingFace LLM."""
        if not HUGGINGFACE_AVAILABLE:
            raise ImportError("langchain_huggingface not available")
        
        api_key = os.getenv('HUGGINGFACEHUB_API_TOKEN')
        if not api_key:
            raise ValueError("HUGGINGFACEHUB_API_TOKEN not set")
        
        # Test token permissions
        if not self._test_huggingface_token():
            raise ValueError("HuggingFace token lacks proper permissions")
        
        model_name = self.config.get('model', 'bigcode/starcoder')
        temperature = self.config.get('temperature', 0.1)
        
        try:
            llm = HuggingFaceEndpoint(
                repo_id=model_name,
                huggingfacehub_api_token=api_key,
                task="text-generation",
                temperature=temperature
            )
            
            # Test the connection with better error handling
            try:
                test_response = llm.invoke("Test")
                if test_response:
                    self.current_provider = "huggingface"
                    return llm
                else:
                    raise ValueError("Empty response from HuggingFace")
            except Exception as test_error:
                logger.warning(f"HuggingFace test failed: {test_error}")
                # If test fails, raise exception to trigger fallback
                raise ValueError(f"HuggingFace inference failed: {test_error}")
                
        except Exception as e:
            logger.error(f"HuggingFace initialization failed: {e}")
            raise
    
    def _try_google_genai(self):
        """Try to initialize Google Gemini LLM."""
        if not GOOGLE_GENAI_AVAILABLE:
            raise ImportError("langchain_google_genai not available")
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        
        try:
            # Try gemini-2.5-flash-preview-05-20 first, fallback to gemini-pro
            models_to_try = [
                "gemini-2.5-flash-preview-05-20",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            
            for model in models_to_try:
                try:
                    llm = ChatGoogleGenerativeAI(
                        model=model,
                        google_api_key=api_key,
                        temperature=self.config.get('temperature', 0.39),
                        max_retries=0  # Disable retries to fail fast
                    )
                    
                    # Test the connection with better error handling
                    try:
                        test_response = llm.invoke("Test")
                        if test_response:
                            self.current_provider = f"google_genai_{model}"
                            return llm
                    except Exception as test_error:
                        error_str = str(test_error)
                        # If it's a rate limit error, don't retry other models
                        if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower() or "ResourceExhausted" in error_str:
                            logger.warning(f"🚫 Google Gemini quota exceeded for {model}, skipping all Google models")
                            raise ValueError(f"Google Gemini quota exceeded: {test_error}")
                        else:
                            logger.warning(f"Google Gemini test failed for {model}: {test_error}")
                            # If test fails, continue to next model
                            continue
                        
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower() or "ResourceExhausted" in error_str:
                        logger.warning(f"🚫 Google Gemini quota exceeded for {model}, skipping all Google models")
                        raise ValueError(f"Google Gemini quota exceeded: {e}")
                    else:
                        logger.warning(f"Google Gemini model {model} failed: {e}")
                        continue
            
            raise ValueError("All Google Gemini models failed")
            
        except Exception as e:
            logger.error(f"Google Gemini initialization failed: {e}")
            raise
    
    def _try_openai(self):
        """Try to initialize OpenAI LLM."""
        if not OPENAI_AVAILABLE:
            raise ImportError("langchain_openai not available")
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        try:
            # Try different OpenAI models
            models_to_try = [
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ]
            
            for model in models_to_try:
                try:
                    llm = ChatOpenAI(
                        model=model,
                        openai_api_key=api_key,
                        temperature=self.config.get('temperature', 0.1)
                    )
                    
                    # Test the connection with better error handling
                    try:
                        test_response = llm.invoke("Test")
                        if test_response:
                            self.current_provider = f"openai_{model}"
                            return llm
                    except Exception as test_error:
                        logger.warning(f"OpenAI test failed for {model}: {test_error}")
                        # If test fails, continue to next model
                        continue
                        
                except Exception as e:
                    logger.warning(f"OpenAI model {model} failed: {e}")
                    continue
            
            raise ValueError("All OpenAI models failed")
            
        except Exception as e:
            logger.error(f"OpenAI initialization failed: {e}")
            raise
    
    def _try_groq(self):
        """Try to initialize Groq LLM."""
        if not GROQ_AVAILABLE:
            raise ImportError("langchain_groq not available")
        
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        
        logger.info("🔑 Groq API key found, attempting Groq models...")
        
        try:
            # Try different Groq models
            models_to_try = [
                "llama-3.1-8b-instant",
                "llama3-70b-8192",
                "llama3-8b-8192",
                "mixtral-8x7b-32768"
            ]
            
            for model in models_to_try:
                try:
                    llm = ChatGroq(
                        model=model,
                        groq_api_key=api_key,
                        temperature=self.config.get('temperature', 0.1)
                    )
                    
                    # Test the connection with better error handling
                    try:
                        test_response = llm.invoke("Test")
                        if test_response:
                            self.current_provider = f"groq_{model}"
                            logger.info(f"✅ Groq model {model} initialized successfully")
                            return llm
                    except Exception as test_error:
                        logger.warning(f"Groq test failed for {model}: {test_error}")
                        # If test fails, continue to next model
                        continue
                        
                except Exception as e:
                    logger.warning(f"Groq model {model} failed: {e}")
                    continue
            
            raise ValueError("All Groq models failed")
            
        except Exception as e:
            logger.error(f"Groq initialization failed: {e}")
            raise
    
    def _create_fallback_llm(self):
        """Create a fallback LLM for when all providers fail."""
        class FallbackLLM:
            def __init__(self):
                self.name = "fallback_llm"
                self.model_name = "fallback_static_analysis"
                self.current_provider = "fallback"
            
            def invoke(self, prompt):
                # Enhanced fallback response with basic analysis
                if "code review" in prompt.lower():
                    return {"content": "Fallback static analysis mode: Performing basic code analysis without LLM."}
                elif "security" in prompt.lower():
                    return {"content": "Fallback security analysis: Checking for common security patterns."}
                elif "performance" in prompt.lower():
                    return {"content": "Fallback performance analysis: Identifying basic performance issues."}
                else:
                    return {"content": "Fallback analysis mode: Using static code analysis techniques."}
        
        fallback_llm = FallbackLLM()
        self.current_provider = "fallback"
        return fallback_llm
    
    def invoke(self, prompt: str) -> Union[str, Dict[str, Any]]:
        """Invoke the LLM with a prompt."""
        try:
            response = self.llm.invoke(prompt)
            
            # Handle different response formats
            if isinstance(response, dict):
                if 'content' in response:
                    return response['content']
                elif 'text' in response:
                    return response['text']
                else:
                    return str(response)
            elif isinstance(response, str):
                return response
            else:
                # Try to get content from response object
                if hasattr(response, 'content'):
                    return response.content
                elif hasattr(response, 'text'):
                    return response.text
                else:
                    return str(response)
                
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            # Return None to trigger fallback analysis in tools
            return None
    
    @property
    def name(self):
        """Get the name of the current LLM provider."""
        if hasattr(self.llm, 'name'):
            return self.llm.name
        return self.current_provider or "unknown"
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current LLM provider."""
        return {
            "provider": self.current_provider,
            "available": self.llm is not None,
            "fallback_mode": self.current_provider == "fallback"
        }


def create_llm_provider(config: Dict[str, Any]) -> LLMProvider:
    """Factory function to create LLM provider."""
    return LLMProvider(config) 