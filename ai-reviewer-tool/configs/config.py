"""
Centralized configuration management for the AI Code Review Tool.

This module provides a single source of truth for all configuration settings,
environment variables, and default values used throughout the application.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ReportFormat(Enum):
    """Report output formats."""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


class FocusArea(Enum):
    """Code review focus areas."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    READABILITY = "readability"
    MAINTAINABILITY = "maintainability"
    ALL = "all"


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    model: str = "bigcode/starcoder"
    temperature: float = 0.1
    max_tokens: int = 2048
    timeout: int = 30
    retry_attempts: int = 3
    fallback_enabled: bool = True


@dataclass
class AnalysisConfig:
    """Code analysis configuration."""
    max_file_size_mb: int = 10
    chunk_size: int = 800
    chunk_overlap: int = 100
    enable_security: bool = True
    enable_performance: bool = True
    enable_maintainability: bool = True
    enable_readability: bool = True


@dataclass
class OutputConfig:
    """Output configuration."""
    default_format: ReportFormat = ReportFormat.MARKDOWN
    output_dir: str = "./output"
    create_backup: bool = True
    include_metrics: bool = True
    include_summary: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5
    json_format: bool = True


@dataclass
class SecurityConfig:
    """Security configuration."""
    mask_api_keys: bool = True
    sanitize_logs: bool = True
    validate_inputs: bool = True
    max_input_size_mb: int = 50


class Config:
    """Centralized configuration manager."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from environment and optional config file."""
        self._load_environment()
        if config_file:
            self._load_config_file(config_file)
        self._validate_config()
    
    def _load_environment(self):
        """Load configuration from environment variables."""
        # API Keys
        self.huggingface_token = os.getenv('HUGGINGFACEHUB_API_TOKEN')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
        # LLM Configuration
        self.llm = LLMConfig(
            model=os.getenv('DEFAULT_LLM_MODEL', 'bigcode/starcoder'),
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('LLM_MAX_TOKENS', '2048')),
            timeout=int(os.getenv('LLM_TIMEOUT', '30')),
            retry_attempts=int(os.getenv('LLM_RETRY_ATTEMPTS', '3')),
            fallback_enabled=os.getenv('LLM_FALLBACK_ENABLED', 'true').lower() == 'true'
        )
        
        # Analysis Configuration
        self.analysis = AnalysisConfig(
            max_file_size_mb=int(os.getenv('MAX_FILE_SIZE_MB', '10')),
            chunk_size=int(os.getenv('CHUNK_SIZE', '800')),
            chunk_overlap=int(os.getenv('CHUNK_OVERLAP', '100')),
            enable_security=os.getenv('ENABLE_SECURITY_ANALYSIS', 'true').lower() == 'true',
            enable_performance=os.getenv('ENABLE_PERFORMANCE_ANALYSIS', 'true').lower() == 'true',
            enable_maintainability=os.getenv('ENABLE_MAINTAINABILITY_ANALYSIS', 'true').lower() == 'true',
            enable_readability=os.getenv('ENABLE_READABILITY_ANALYSIS', 'true').lower() == 'true'
        )
        
        # Output Configuration
        self.output = OutputConfig(
            default_format=ReportFormat(os.getenv('DEFAULT_REPORT_FORMAT', 'markdown')),
            output_dir=os.getenv('DEFAULT_OUTPUT_DIR', './output'),
            create_backup=os.getenv('CREATE_BACKUP', 'true').lower() == 'true',
            include_metrics=os.getenv('INCLUDE_METRICS', 'true').lower() == 'true',
            include_summary=os.getenv('INCLUDE_SUMMARY', 'true').lower() == 'true'
        )
        
        # Logging Configuration
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.logging = LoggingConfig(
            level=LogLevel(log_level) if log_level in [l.value for l in LogLevel] else LogLevel.INFO,
            file_path=os.getenv('LOG_FILE_PATH'),
            max_file_size_mb=int(os.getenv('LOG_MAX_FILE_SIZE_MB', '10')),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5')),
            json_format=os.getenv('LOG_JSON_FORMAT', 'true').lower() == 'true'
        )
        
        # Security Configuration
        self.security = SecurityConfig(
            mask_api_keys=os.getenv('MASK_API_KEYS', 'true').lower() == 'true',
            sanitize_logs=os.getenv('SANITIZE_LOGS', 'true').lower() == 'true',
            validate_inputs=os.getenv('VALIDATE_INPUTS', 'true').lower() == 'true',
            max_input_size_mb=int(os.getenv('MAX_INPUT_SIZE_MB', '50'))
        )
        
        # Performance Configuration
        self.max_parallel_files = int(os.getenv('MAX_PARALLEL_FILES', '5'))
        self.cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        self.cache_dir = os.getenv('CACHE_DIR', './cache')
    
    def _load_config_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Update configuration with file values
            if 'llm' in config_data:
                for key, value in config_data['llm'].items():
                    if hasattr(self.llm, key):
                        setattr(self.llm, key, value)
            
            if 'analysis' in config_data:
                for key, value in config_data['analysis'].items():
                    if hasattr(self.analysis, key):
                        setattr(self.analysis, key, value)
            
            if 'output' in config_data:
                for key, value in config_data['output'].items():
                    if hasattr(self.output, key):
                        setattr(self.output, key, value)
                        
        except Exception as e:
            logging.warning(f"Failed to load config file {config_file}: {e}")
    
    def _validate_config(self):
        """Validate configuration values."""
        # Validate LLM configuration
        if self.llm.temperature < 0 or self.llm.temperature > 2:
            raise ValueError("LLM temperature must be between 0 and 2")
        
        if self.llm.max_tokens < 1 or self.llm.max_tokens > 8192:
            raise ValueError("LLM max_tokens must be between 1 and 8192")
        
        if self.llm.timeout < 1 or self.llm.timeout > 300:
            raise ValueError("LLM timeout must be between 1 and 300 seconds")
        
        # Validate analysis configuration
        if self.analysis.max_file_size_mb < 1 or self.analysis.max_file_size_mb > 100:
            raise ValueError("Max file size must be between 1 and 100 MB")
        
        if self.analysis.chunk_size < 100 or self.analysis.chunk_size > 2000:
            raise ValueError("Chunk size must be between 100 and 2000")
        
        # Validate output configuration
        if not os.path.exists(self.output.output_dir):
            try:
                os.makedirs(self.output.output_dir, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create output directory {self.output.output_dir}: {e}")
    
    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys with optional masking."""
        keys = {
            'huggingface': self.huggingface_token,
            'google': self.google_api_key,
            'openai': self.openai_api_key,
            'groq': self.groq_api_key
        }
        
        if self.security.mask_api_keys:
            return {k: self._mask_api_key(v) if v else None for k, v in keys.items()}
        
        return keys
    
    def _mask_api_key(self, key: str) -> str:
        """Mask API key for logging."""
        if not key or len(key) < 8:
            return "***"
        return f"{key[:4]}...{key[-4:]}"
    
    def has_any_api_key(self) -> bool:
        """Check if any API key is configured."""
        return any([
            self.huggingface_token,
            self.google_api_key,
            self.openai_api_key,
            self.groq_api_key
        ])
    
    def get_focus_areas(self) -> List[FocusArea]:
        """Get enabled focus areas."""
        areas = []
        if self.analysis.enable_security:
            areas.append(FocusArea.SECURITY)
        if self.analysis.enable_performance:
            areas.append(FocusArea.PERFORMANCE)
        if self.analysis.enable_readability:
            areas.append(FocusArea.READABILITY)
        if self.analysis.enable_maintainability:
            areas.append(FocusArea.MAINTAINABILITY)
        
        return areas if areas else [FocusArea.ALL]


# Global configuration instance
config = Config() 