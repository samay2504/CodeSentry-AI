"""
Prompt management package for the AI Code Review Tool.

This package provides flexible prompt template management with support for:
- Environment variable customization
- Configuration file loading
- Dynamic template registration
- LangChain integration
"""

from .registry import (
    PromptRegistry,
    get_prompt_registry,
    get_prompt,
    get_prompt_template
)

# Legacy imports for backward compatibility
from .prompts import (
    get_review_prompt,
    get_improvement_prompt,
    get_security_analysis_prompt,
    get_performance_analysis_prompt,
    get_documentation_prompt,
    get_summary_prompt,
    _format_requirements,
    _format_issues
)

__all__ = [
    # New registry-based functions
    'PromptRegistry',
    'get_prompt_registry',
    'get_prompt',
    'get_prompt_template',
    
    # Legacy functions for backward compatibility
    'get_review_prompt',
    'get_improvement_prompt',
    'get_security_analysis_prompt',
    'get_performance_analysis_prompt',
    'get_documentation_prompt',
    'get_summary_prompt',
    '_format_requirements',
    '_format_issues'
] 