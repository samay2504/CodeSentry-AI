"""
Prompts module for generating LLM prompts for code review.

This module contains prompt templates for various code review tasks
using LangChain PromptTemplate.
"""

from langchain.prompts import PromptTemplate
from typing import Dict, List, Optional
import json

# --- Prompt System Customization ---
# You can override any prompt template by setting the environment variable:
#   PROMPT_TEMPLATE_<TEMPLATE_NAME>
# or by placing a file in the configs/prompts/ directory (e.g., code_review.txt)
# See registry.py for details.

# --- Common Prompt Instructions ---
RETURN_JSON_INSTRUCTION = "Return only valid JSON without any additional text."
RETURN_JSON_ONLY = "Return only valid JSON."

# --- Legacy vs. Registry Usage ---
# All new code should use the registry-based prompt system (see registry.py).
# Legacy functions are provided for backward compatibility but may be deprecated in the future.

def get_review_prompt(requirements: Dict[str, str], code: str, file_path: str = "") -> str:
    """
    Generates a prompt for code review.
    You can override this prompt via PROMPT_TEMPLATE_code_review or configs/prompts/code_review.txt
    """
    template = PromptTemplate(
        input_variables=["reqs", "code", "file_path"],
        template=f"""
You are an expert code reviewer with deep knowledge of software engineering best practices, security, and performance optimization.

REQUIREMENTS TO EVALUATE AGAINST:
{{reqs}}

FILE BEING REVIEWED: {{file_path}}

CODE TO REVIEW:
{{code}}

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

{RETURN_JSON_INSTRUCTION}
"""
    )
    
    return template.format(
        reqs=_format_requirements(requirements),
        code=code,
        file_path=file_path
    )


def get_improvement_prompt(original_code: str, issues: List[Dict], file_path: str = "") -> str:
    """
    Generates a prompt for code improvement based on identified issues.
    You can override this prompt via PROMPT_TEMPLATE_code_improvement or configs/prompts/code_improvement.txt
    """
    template = PromptTemplate(
        input_variables=["original_code", "issues", "file_path"],
        template=f"""
You are an expert software engineer tasked with improving code based on identified issues.

FILE: {{file_path}}

ORIGINAL CODE:
{{original_code}}

IDENTIFIED ISSUES:
{{issues}}

Please provide an improved version of the code that addresses all identified issues while maintaining the original functionality. 

Requirements:
1. Fix all syntax errors and bugs
2. Address security vulnerabilities
3. Optimize performance where applicable
4. Improve readability and maintainability
5. Follow language-specific best practices
6. Add or improve documentation where needed
7. Ensure the improved code is functionally equivalent to the original

{RETURN_JSON_ONLY}
"""
    )
    
    return template.format(
        original_code=original_code,
        issues=_format_issues(issues),
        file_path=file_path
    )


def get_security_analysis_prompt(code: str, file_path: str = "") -> str:
    """
    Generates a prompt specifically for security analysis.
    You can override this prompt via PROMPT_TEMPLATE_security_analysis or configs/prompts/security_analysis.txt
    """
    template = PromptTemplate(
        input_variables=["code", "file_path"],
        template=f"""
You are a security expert specializing in code security analysis.

FILE: {{file_path}}

CODE TO ANALYZE:
{{code}}

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

{RETURN_JSON_ONLY}
"""
    )
    
    return template.format(code=code, file_path=file_path)


def get_performance_analysis_prompt(code: str, file_path: str = "") -> str:
    """
    Generates a prompt specifically for performance analysis.
    You can override this prompt via PROMPT_TEMPLATE_performance_analysis or configs/prompts/performance_analysis.txt
    """
    template = PromptTemplate(
        input_variables=["code", "file_path"],
        template=f"""
You are a performance optimization expert.

FILE: {{file_path}}

CODE TO ANALYZE:
{{code}}

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

{RETURN_JSON_ONLY}
"""
    )
    
    return template.format(code=code, file_path=file_path)


def get_documentation_prompt(code: str, file_path: str = "") -> str:
    """
    Generates a prompt for improving code documentation.
    You can override this prompt via PROMPT_TEMPLATE_documentation_improvement or configs/prompts/documentation_improvement.txt
    """
    template = PromptTemplate(
        input_variables=["code", "file_path"],
        template=f"""
You are a technical documentation expert.

FILE: {{file_path}}

CODE TO DOCUMENT:
{{code}}

Please improve the documentation for this code by:
1. Adding comprehensive docstrings for functions and classes
2. Improving inline comments for clarity
3. Documenting parameters, return values, and exceptions
4. Enhancing module-level documentation
5. Creating README-style documentation if applicable
6. Following language-specific documentation standards

Provide the improved code with enhanced documentation. Maintain the original functionality while making the code more understandable and maintainable.

{RETURN_JSON_ONLY}
"""
    )
    
    return template.format(code=code, file_path=file_path)


def _format_requirements(requirements: Dict[str, str]) -> str:
    """Format requirements dictionary into a readable string."""
    if not requirements:
        return "No specific requirements provided."
    
    formatted = []
    for req_id, description in requirements.items():
        formatted.append(f"{req_id}: {description}")
    
    return "\n".join(formatted)


def _format_issues(issues: List[Dict]) -> str:
    """Format issues list into a readable string."""
    if not issues:
        return "No issues identified."
    
    formatted = []
    for i, issue in enumerate(issues, 1):
        formatted.append(f"{i}. {issue.get('type', 'Unknown')} - {issue.get('description', 'No description')}")
        if 'line' in issue:
            formatted[-1] += f" (Line {issue['line']})"
    
    return "\n".join(formatted)


def get_summary_prompt(analysis_results: List[Dict], project_structure: Dict) -> str:
    """
    Generates a prompt for creating a comprehensive project summary.
    
    Args:
        analysis_results: List of analysis results from all files.
        project_structure: Project structure information.
        
    Returns:
        Formatted prompt string.
    """
    template = PromptTemplate(
        input_variables=["analysis_results", "project_structure"],
        template="""
You are a senior software architect creating a comprehensive project review summary.

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

Format the response as clean Markdown with proper headings, lists, and code blocks where appropriate.
"""
    )
    
    return template.format(
        analysis_results=json.dumps(analysis_results, indent=2),
        project_structure=json.dumps(project_structure, indent=2)
    ) 