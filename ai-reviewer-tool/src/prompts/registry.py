"""
Flexible prompt template registry for the AI Code Review Tool.

This module provides a centralized system for managing and customizing
prompt templates without requiring code changes. Templates can be
customized via environment variables or configuration files.

Best Practice: Use the registry-based prompt system for all new code. Legacy prompt functions are supported for backward compatibility but may be deprecated in the future.

How to override templates:
- Set environment variable PROMPT_TEMPLATE_<TEMPLATE_NAME>
- Or add a file in configs/prompts/<template_name>.txt
- Or add to configs/prompts/prompts.json
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from langchain.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)


class PromptRegistry:
    """
    Centralized registry for managing prompt templates.
    
    This class provides a flexible way to manage and customize prompts
    through environment variables, configuration files, or direct API calls.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the prompt registry.
        
        Args:
            config_dir: Directory containing prompt configuration files
        """
        self.templates: Dict[str, str] = {}
        self.config_dir = config_dir or os.getenv('PROMPT_CONFIG_DIR', './configs/prompts')
        self._load_default_templates()
        self._load_environment_templates()
        self._load_file_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates."""
        self.templates.update({
            'code_review': self._get_default_code_review_template(),
            'code_analysis': self._get_default_code_analysis_template(),
            'code_improvement': self._get_default_code_improvement_template(),
            'security_analysis': self._get_default_security_analysis_template(),
            'performance_analysis': self._get_default_performance_analysis_template(),
            'documentation_improvement': self._get_default_documentation_template(),
            'project_summary': self._get_default_project_summary_template(),
            'agent_reviewer_backstory': self._get_default_reviewer_backstory(),
            'agent_security_backstory': self._get_default_security_backstory(),
            'agent_performance_backstory': self._get_default_performance_backstory(),
            'agent_improver_backstory': self._get_default_improver_backstory(),
            'agent_documentation_backstory': self._get_default_documentation_backstory(),
        })
    
    def _load_environment_templates(self):
        """Load prompt templates from environment variables."""
        env_prefix = 'PROMPT_TEMPLATE_'
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                template_name = key[len(env_prefix):].lower()
                self.templates[template_name] = value
                logger.info(f"Loaded prompt template '{template_name}' from environment")
    
    def _load_file_templates(self):
        """Load prompt templates from configuration files."""
        config_path = Path(self.config_dir)
        if not config_path.exists():
            return
        
        # Load from JSON file
        json_file = config_path / 'prompts.json'
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_templates = json.load(f)
                self.templates.update(file_templates)
                logger.info(f"Loaded {len(file_templates)} prompt templates from {json_file}")
            except Exception as e:
                logger.warning(f"Failed to load prompt templates from {json_file}: {e}")
        
        # Load from individual template files
        for template_file in config_path.glob('*.txt'):
            template_name = template_file.stem
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.templates[template_name] = f.read().strip()
                logger.info(f"Loaded prompt template '{template_name}' from {template_file}")
            except Exception as e:
                logger.warning(f"Failed to load prompt template from {template_file}: {e}")
    
    def register(self, name: str, template: str):
        """
        Register a new prompt template.
        
        Args:
            name: Template name
            template: Template content
        """
        self.templates[name] = template
        logger.info(f"Registered prompt template '{name}'")
    
    def get(self, name: str, **kwargs) -> str:
        """
        Get a prompt template and format it with provided arguments.
        
        Args:
            name: Template name
            **kwargs: Arguments to format the template
            
        Returns:
            Formatted prompt string
        Raises:
            KeyError if required variables are missing.
        """
        template = self.templates.get(name)
        if not template:
            logger.warning(f"Prompt template '{name}' not found")
            return ""
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing required argument '{e}' for template '{name}'. Provided: {list(kwargs.keys())}")
            raise
        except Exception as e:
            logger.error(f"Error formatting template '{name}': {e}")
            raise
    
    def get_prompt_template(self, name: str, input_variables: List[str]) -> PromptTemplate:
        """
        Get a LangChain PromptTemplate object.
        
        Args:
            name: Template name
            input_variables: List of input variable names
            
        Returns:
            LangChain PromptTemplate object
        """
        template = self.templates.get(name)
        if not template:
            logger.warning(f"Prompt template '{name}' not found")
            return PromptTemplate(
                input_variables=input_variables,
                template="Error: Template not found"
            )
        
        return PromptTemplate(
            input_variables=input_variables,
            template=template
        )
    
    def list_templates(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def save_templates(self, file_path: str):
        """Save all templates to a JSON file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.templates)} templates to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save templates to {file_path}: {e}")
    
    def _get_default_code_review_template(self) -> str:
        return """You are an expert code reviewer with deep knowledge of software engineering best practices, security, and performance optimization.

REQUIREMENTS TO EVALUATE AGAINST:
{reqs}

FILE BEING REVIEWED: {file_path}

CODE TO REVIEW:
{code}

Please perform a comprehensive code review and provide your analysis in the following JSON format:

{{
    "issues": [
        {{
            "type": "syntax|security|performance|readability|maintainability|best_practice",
            "severity": "critical|high|medium|low",
            "line": <line_number>,
            "description": "<detailed description of the issue>",
            "suggestion": "<specific suggestion for improvement>"
        }}
    ],
    "improved_code": "<complete improved version of the code>",
    "metrics": {{
        "complexity_score": <1-10>,
        "maintainability_score": <1-10>,
        "security_score": <1-10>,
        "performance_score": <1-10>
    }},
    "summary": "<brief summary of key findings and improvements>"
}}

Focus on:
1. Syntax errors and bugs
2. Security vulnerabilities (SQL injection, XSS, etc.)
3. Performance bottlenecks
4. Code readability and maintainability
5. Adherence to language-specific best practices
6. Resource optimization (memory, CPU, network)
7. Documentation quality

Return only valid JSON without any additional text."""
    
    def _get_default_code_analysis_template(self) -> str:
        return """You are an expert code analyzer. Analyze the following code for issues and provide a comprehensive assessment.

File: {file_path}
Language: {language}

Code to analyze:
{code}

Please analyze this code for:
1. Syntax errors and bugs
2. Security vulnerabilities
3. Performance issues
4. Code quality and maintainability issues
5. Best practice violations
6. Readability issues

IMPORTANT: Respond in valid JSON format only. If you cannot generate valid JSON, provide a plain text analysis instead.

Preferred JSON format:
{{
    "issues": [
        {{
            "type": "syntax|security|performance|maintainability|readability|best_practice",
            "severity": "critical|high|medium|low",
            "line": <line_number>,
            "description": "<detailed description>",
            "suggestion": "<improvement suggestion>"
        }}
    ],
    "metrics": {{
        "complexity_score": <1-10>,
        "maintainability_score": <1-10>,
        "security_score": <1-10>,
        "performance_score": <1-10>
    }},
    "summary": "<brief summary of findings>"
}}

If you cannot provide JSON, give a plain text analysis with clear issue descriptions."""
    
    def _get_default_code_improvement_template(self) -> str:
        return """You are an expert software engineer tasked with improving code based on identified issues.

File: {file_path}
Language: {language}

Original code:
{code}

Issues to address:
{issues}

Please provide an improved version of the code that addresses all identified issues while maintaining the original functionality.

Requirements:
1. Fix all identified issues
2. Maintain original functionality
3. Improve code quality and readability
4. Follow language-specific best practices
5. Add appropriate documentation where needed
6. Ensure the improved code is functionally equivalent to the original

Return only the complete improved code without any additional explanation or formatting."""
    
    def _get_default_security_analysis_template(self) -> str:
        return """You are a security expert specializing in code security analysis.

File: {file_path}
Language: {language}

Code to analyze:
{code}

Please perform a comprehensive security analysis and identify potential vulnerabilities. Focus on:

1. Input validation and sanitization
2. SQL injection vulnerabilities
3. Cross-site scripting (XSS)
4. Authentication and authorization issues
5. Sensitive data exposure
6. Insecure direct object references
7. Security misconfigurations
8. Cryptographic weaknesses
9. Insecure deserialization
10. Insufficient logging and monitoring

Provide your analysis in JSON format:

{{
    "security_issues": [
        {{
            "type": "<vulnerability_type>",
            "severity": "critical|high|medium|low",
            "line": <line_number>,
            "description": "<detailed description>",
            "cve_reference": "<relevant_CVE_if_applicable>",
            "mitigation": "<specific_mitigation_steps>"
        }}
    ],
    "overall_security_score": <1-10>,
    "recommendations": ["<list_of_security_recommendations>"]
}}

Return only valid JSON."""
    
    def _get_default_performance_analysis_template(self) -> str:
        return """You are a performance optimization expert.

File: {file_path}
Language: {language}

Code to analyze:
{code}

Please perform a comprehensive performance analysis and identify optimization opportunities. Focus on:

1. Algorithm efficiency and complexity
2. Memory usage and leaks
3. Database query optimization
4. Network request optimization
5. Caching opportunities
6. Resource management
7. Concurrency and threading issues
8. I/O operations optimization
9. Redundant computations
10. Scalability concerns

Provide your analysis in JSON format:

{{
    "performance_issues": [
        {{
            "type": "<performance_issue_type>",
            "severity": "critical|high|medium|low",
            "line": <line_number>,
            "description": "<detailed_description>",
            "impact": "<performance_impact_description>",
            "optimization": "<specific_optimization_suggestion>"
        }}
    ],
    "overall_performance_score": <1-10>,
    "optimization_opportunities": ["<list_of_optimization_opportunities>"]
}}

Return only valid JSON."""
    
    def _get_default_documentation_template(self) -> str:
        return """You are a technical documentation expert.

File: {file_path}
Language: {language}

Code to document:
{code}

Please improve the documentation for this code by:

1. Adding comprehensive docstrings for functions and classes
2. Explaining complex logic and algorithms
3. Documenting parameters, return values, and exceptions
4. Adding inline comments for non-obvious code
5. Creating README-style documentation if applicable
6. Following language-specific documentation standards

Provide the improved code with enhanced documentation. Maintain the original functionality while making the code more understandable and maintainable.

Return the complete documented code."""
    
    def _get_default_project_summary_template(self) -> str:
        return """You are a senior software architect creating a comprehensive project review summary.

PROJECT STRUCTURE:
{project_structure}

ANALYSIS RESULTS:
{analysis_results}

Please create a comprehensive project summary report in Markdown format covering:

1. **Executive Summary**
   - Overall code quality assessment
   - Key findings and recommendations
   - Priority areas for improvement

2. **Technical Analysis**
   - Code quality metrics summary
   - Security assessment
   - Performance analysis
   - Maintainability evaluation

3. **Detailed Findings**
   - Critical issues requiring immediate attention
   - High-priority improvements
   - Medium and low-priority suggestions

4. **Recommendations**
   - Specific action items
   - Best practices implementation
   - Technology stack considerations

5. **Metrics Summary**
   - Average scores across all files
   - File-by-file breakdown
   - Trend analysis

Format the response as clean Markdown with proper headings, lists, and code blocks where appropriate."""
    
    def _get_default_reviewer_backstory(self) -> str:
        return """You are a senior software engineer with 15+ years of experience in code review, security analysis, and performance optimization. You have worked with multiple programming languages and frameworks, and have a deep understanding of software engineering best practices, design patterns, and common pitfalls. You are known for your thorough analysis and ability to identify both obvious and subtle issues in code."""
    
    def _get_default_security_backstory(self) -> str:
        return """You are a cybersecurity expert specializing in application security, penetration testing, and secure coding practices. You have extensive experience identifying vulnerabilities like SQL injection, XSS, authentication bypasses, and other security issues. You stay updated with the latest security threats and mitigation strategies."""
    
    def _get_default_performance_backstory(self) -> str:
        return """You are a performance engineering expert with deep knowledge of algorithms, data structures, and system optimization. You specialize in identifying performance bottlenecks, memory leaks, and optimization opportunities. You have experience with profiling tools and performance testing methodologies."""
    
    def _get_default_improver_backstory(self) -> str:
        return """You are a software architect and refactoring expert with extensive experience in improving code quality, readability, and maintainability. You excel at applying design patterns, improving code structure, and ensuring best practices are followed while maintaining functionality."""
    
    def _get_default_documentation_backstory(self) -> str:
        return """You are a technical writer and documentation expert with experience in creating clear, comprehensive documentation for software projects. You understand the importance of good documentation for maintainability and knowledge transfer. You excel at writing clear docstrings, comments, and technical reports."""

    def validate_templates(self, required_templates: Optional[list] = None) -> bool:
        """
        Validate that all required templates are present and can be formatted with dummy variables.
        Args:
            required_templates: List of required template names. If None, uses all default keys.
        Returns:
            True if all templates are valid, False otherwise.
        """
        if required_templates is None:
            required_templates = [
                'code_review', 'code_analysis', 'code_improvement',
                'security_analysis', 'performance_analysis',
                'documentation_improvement', 'project_summary',
                'agent_reviewer_backstory', 'agent_security_backstory',
                'agent_performance_backstory', 'agent_improver_backstory',
                'agent_documentation_backstory'
            ]
        all_valid = True
        for name in required_templates:
            template = self.templates.get(name)
            if not template:
                logger.error(f"Missing required prompt template: {name}")
                all_valid = False
                continue
            # Try formatting with dummy variables
            try:
                dummy_vars = {k: '<dummy>' for k in ['reqs','code','file_path','issues','original_code','language']}
                template.format(**dummy_vars)
            except Exception as e:
                logger.error(f"Template '{name}' failed to format with dummy variables: {e}")
                all_valid = False
        return all_valid


# Global prompt registry instance
_prompt_registry: Optional[PromptRegistry] = None


def get_prompt_registry() -> PromptRegistry:
    """Get the global prompt registry instance."""
    global _prompt_registry
    if _prompt_registry is None:
        _prompt_registry = PromptRegistry()
    return _prompt_registry


def get_prompt(name: str, **kwargs) -> str:
    """Get a formatted prompt template."""
    return get_prompt_registry().get(name, **kwargs)


def get_prompt_template(name: str, input_variables: List[str]) -> PromptTemplate:
    """Get a LangChain PromptTemplate object."""
    return get_prompt_registry().get_prompt_template(name, input_variables) 