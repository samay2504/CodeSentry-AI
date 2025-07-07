"""
AI Code Review Tool - Production-grade AI-powered code review and improvement.

This package provides comprehensive code analysis, review, and improvement
capabilities using multiple LLM providers with robust fallback systems.

Main modules:
- cli: Command-line interface
- agents: AI agent orchestration
- tools: Code analysis and improvement tools
- ingestion: Codebase and requirements ingestion
- output: Report generation and output formatting
- llm_provider: Multi-provider LLM system
- logger: Structured logging utilities
- prompts: LLM prompt templates
"""

__version__ = "1.0.0"
__author__ = "AI Code Review Team"
__description__ = "Production-grade AI-powered code review and improvement tool"

# Core exports - only import what's needed immediately
from .exceptions import AIReviewerError, ValidationError, SecurityError, ConfigurationError, LLMError

# Lazy imports to avoid circular dependencies
def _get_cli_main():
    """Lazily import and return the main CLI entry point."""
    from .cli import main
    return main

def _get_agents():
    """Lazily import and return agent orchestration functions/classes."""
    from .agents import CodeReviewAgents, setup_agents, run_review
    return CodeReviewAgents, setup_agents, run_review

def _get_tools():
    """Lazily import and return core code analysis and improvement tools."""
    from .tools import analyze_code, improve_code, analyze_security, analyze_performance
    return analyze_code, improve_code, analyze_security, analyze_performance

def _get_ingestion():
    """Lazily import and return codebase and requirements ingestion functions."""
    from .ingestion import ingest_codebase, ingest_frd
    return ingest_codebase, ingest_frd

def _get_output():
    """Lazily import and return output/report generation functions."""
    from .output import generate_output, generate_report
    return generate_output, generate_report

def _get_llm_provider():
    """Lazily import and return LLM provider creation and class."""
    from .llm_provider import create_llm_provider, LLMProvider
    return create_llm_provider, LLMProvider

def _get_validation():
    """Lazily import and return input validation utilities and classes."""
    from .validation import validator, InputValidator
    return validator, InputValidator

# Lazy import for config to avoid circular imports
def _get_config():
    """Lazily import and return the main config object."""
    try:
        from configs.config import config
        return config
    except ImportError:
        # Fallback for when configs is not in path
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from configs.config import config
        return config

def _get_config_classes():
    """Lazily import and return config classes for advanced configuration."""
    try:
        from configs.config import Config, LLMConfig, AnalysisConfig, OutputConfig, LoggingConfig, SecurityConfig
        return Config, LLMConfig, AnalysisConfig, OutputConfig, LoggingConfig, SecurityConfig
    except ImportError:
        # Fallback for when configs is not in path
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from configs.config import Config, LLMConfig, AnalysisConfig, OutputConfig, LoggingConfig, SecurityConfig
        return Config, LLMConfig, AnalysisConfig, OutputConfig, LoggingConfig, SecurityConfig

__all__ = [
    'AIReviewerError',
    'ValidationError',
    'SecurityError',
    'ConfigurationError',
    'LLMError'
]

# Add all exports to module namespace via __getattr__
def __getattr__(name):
    """Dynamically resolve and return module-level attributes for lazy loading."""
    # Config-related exports
    if name == 'config':
        return _get_config()
    elif name in ['Config', 'LLMConfig', 'AnalysisConfig', 'OutputConfig', 'LoggingConfig', 'SecurityConfig']:
        Config, LLMConfig, AnalysisConfig, OutputConfig, LoggingConfig, SecurityConfig = _get_config_classes()
        if name == 'Config':
            return Config
        elif name == 'LLMConfig':
            return LLMConfig
        elif name == 'AnalysisConfig':
            return AnalysisConfig
        elif name == 'OutputConfig':
            return OutputConfig
        elif name == 'LoggingConfig':
            return LoggingConfig
        elif name == 'SecurityConfig':
            return SecurityConfig
    
    # CLI exports
    elif name == 'main':
        return _get_cli_main()
    
    # Agent exports
    elif name in ['CodeReviewAgents', 'setup_agents', 'run_review']:
        CodeReviewAgents, setup_agents, run_review = _get_agents()
        if name == 'CodeReviewAgents':
            return CodeReviewAgents
        elif name == 'setup_agents':
            return setup_agents
        elif name == 'run_review':
            return run_review
    
    # Tool exports
    elif name in ['analyze_code', 'improve_code', 'analyze_security', 'analyze_performance']:
        analyze_code, improve_code, analyze_security, analyze_performance = _get_tools()
        if name == 'analyze_code':
            return analyze_code
        elif name == 'improve_code':
            return improve_code
        elif name == 'analyze_security':
            return analyze_security
        elif name == 'analyze_performance':
            return analyze_performance
    
    # Ingestion exports
    elif name in ['ingest_codebase', 'ingest_frd']:
        ingest_codebase, ingest_frd = _get_ingestion()
        if name == 'ingest_codebase':
            return ingest_codebase
        elif name == 'ingest_frd':
            return ingest_frd
    
    # Output exports
    elif name in ['generate_output', 'generate_report']:
        generate_output, generate_report = _get_output()
        if name == 'generate_output':
            return generate_output
        elif name == 'generate_report':
            return generate_report
    
    # LLM Provider exports
    elif name in ['create_llm_provider', 'LLMProvider']:
        create_llm_provider, LLMProvider = _get_llm_provider()
        if name == 'create_llm_provider':
            return create_llm_provider
        elif name == 'LLMProvider':
            return LLMProvider
    
    # Validation exports
    elif name in ['validator', 'InputValidator']:
        validator, InputValidator = _get_validation()
        if name == 'validator':
            return validator
        elif name == 'InputValidator':
            return InputValidator
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'") 