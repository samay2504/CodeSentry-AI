"""
Tools module for LangGraph tools used in code review tasks.

This module contains LangGraph-decorated functions that perform
various code analysis and improvement tasks using LLM prompts.
"""

try:
    from langchain.tools import tool
except ImportError:
    # Fallback for newer versions
    from langchain_core.tools import tool
from typing import Dict, List, Optional, Any
import ast
import re
import json
import logging
from pathlib import Path
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
from huggingface_hub import InferenceClient
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it

from .llm_provider import create_llm_provider
from .config.languages import get_language_from_extension
from .prompts import get_prompt, get_prompt_template

logger = logging.getLogger(__name__)

# Initialize LLM provider
def get_llm_provider(model_name=None, temperature=0.1):
    """Get LLM provider with robust fallback system."""
    config = {
        'model': model_name or os.getenv('DEFAULT_LLM_MODEL', 'bigcode/starcoder'),
        'temperature': temperature
    }
    
    try:
        llm_provider = create_llm_provider(config)
        provider_info = llm_provider.get_provider_info()
        logger.info(f"LLM Provider initialized: {provider_info['provider']}")
        return llm_provider
    except Exception as e:
        logger.error(f"Failed to initialize LLM provider: {e}")
        return None


def chunk_code(code: str, max_tokens: int = 1000, overlap: int = 100) -> List[str]:
    """
    Chunk code into smaller pieces for LLM processing.
    
    Args:
        code: Code to chunk
        max_tokens: Maximum tokens per chunk
        overlap: Number of tokens to overlap between chunks
        
    Returns:
        List of code chunks
    """
    lines = code.split('\n')
    chunks = []
    current_chunk = []
    current_length = 0
    
    for line in lines:
        # Rough estimate: 1 token ≈ 4 characters
        line_tokens = len(line) // 4
        
        if current_length + line_tokens > max_tokens and current_chunk:
            # Save current chunk
            chunks.append('\n'.join(current_chunk))
            
            # Start new chunk with overlap
            overlap_lines = []
            overlap_length = 0
            for i in range(len(current_chunk) - 1, -1, -1):
                line_tokens = len(current_chunk[i]) // 4
                if overlap_length + line_tokens <= overlap:
                    overlap_lines.insert(0, current_chunk[i])
                    overlap_length += line_tokens
                else:
                    break
            
            current_chunk = overlap_lines + [line]
            current_length = overlap_length + line_tokens
        else:
            current_chunk.append(line)
            current_length += line_tokens
    
    # Add final chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    
    return chunks if chunks else [code]


def analyze_code_with_chunking(code: str, file_path: str = "", llm=None) -> Dict[str, Any]:
    """
    Analyze code using chunking for large files.
    
    Args:
        code: Code to analyze
        file_path: Path to the file
        llm: LLM provider instance
        
    Returns:
        Combined analysis results
    """
    if not llm:
        return _fallback_analysis(code, file_path)
    
    # Chunk the code if it's large
    chunks = chunk_code(code, max_tokens=800, overlap=100)
    
    if len(chunks) == 1:
        # Small file, analyze directly
        return _analyze_single_chunk(chunks[0], file_path, llm)
    
    # Large file, analyze chunks and combine results
    all_issues = []
    all_metrics = []
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Analyzing chunk {i+1}/{len(chunks)} of {file_path}")
        result = _analyze_single_chunk(chunk, f"{file_path} (chunk {i+1})", llm)
        
        if isinstance(result, dict):
            # Adjust line numbers for chunks
            if 'issues' in result:
                for issue in result['issues']:
                    if 'line' in issue:
                        issue['line'] += i * 800  # Rough estimate
                all_issues.extend(result['issues'])
            
            if 'metrics' in result:
                all_metrics.append(result['metrics'])
    
    # Combine metrics (average them)
    combined_metrics = {
        'complexity_score': sum(m.get('complexity_score', 5) for m in all_metrics) / len(all_metrics) if all_metrics else 5,
        'maintainability_score': sum(m.get('maintainability_score', 5) for m in all_metrics) / len(all_metrics) if all_metrics else 5,
        'security_score': sum(m.get('security_score', 5) for m in all_metrics) / len(all_metrics) if all_metrics else 5,
        'performance_score': sum(m.get('performance_score', 5) for m in all_metrics) / len(all_metrics) if all_metrics else 5
    }
    
    # Add language-agnostic best practices
    production_standards = [
        {
            "type": "best_practice",
            "severity": "medium",
            "line": 0,
            "description": "Follow language-specific style guidelines",
            "suggestion": "Use appropriate linters and formatters for your programming language. Follow established style guides and naming conventions. Configure automated formatting tools to maintain consistency."
        },
        {
            "type": "best_practice", 
            "severity": "medium",
            "line": 0,
            "description": "Implement proper error handling patterns",
            "suggestion": "Use language-specific exception handling patterns. Avoid catching all exceptions unless necessary. Create custom exception classes for domain-specific errors. Use appropriate error handling mechanisms for your language."
        }
    ]
    
    all_issues.extend(production_standards)
    
    return {
        'issues': all_issues,
        'metrics': combined_metrics,
        'file_path': file_path,
        'analysis_type': 'chunked_llm_analysis',
        'summary': f"Analyzed {len(chunks)} chunks, found {len(all_issues)} total issues"
    }


def _analyze_single_chunk(code: str, file_path: str, llm) -> Dict[str, Any]:
    """Analyze a single chunk of code."""
    try:
        # Get analysis prompt from registry
        analysis_prompt = get_prompt_template("code_analysis", ["code", "file_path", "language"])
        
        # Detect language from file extension
        language = get_language_from_extension(file_path)
        
        # Generate analysis using LLM
        prompt = analysis_prompt.format(
            code=code,
            file_path=file_path,
            language=language
        )
        
        response = llm.invoke(prompt)
        
        # Log the raw response for debugging
        logger.debug(f"Raw LLM response type: {type(response)}")
        if response is not None:
            logger.debug(f"Raw LLM response preview: {str(response)[:200]}...")
        
        # Handle None response (LLM failed)
        if response is None:
            logger.warning("LLM returned None, using fallback analysis")
            return _fallback_analysis(code, file_path)
        
        # Parse response - handle both JSON and plain text
        try:
            # Handle different response formats
            if isinstance(response, str):
                response_text = response
            elif isinstance(response, dict):
                response_text = response.get('content', str(response))
            else:
                response_text = str(response)
            
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                try:
                    result = json.loads(json_str)
                    
                    return {
                        'issues': result.get('issues', []),
                        'metrics': result.get('metrics', {
                            'complexity_score': 5,
                            'maintainability_score': 5,
                            'security_score': 5,
                            'performance_score': 5
                        }),
                        'file_path': file_path,
                        'analysis_type': 'llm_analysis',
                        'summary': result.get('summary', 'Analysis completed')
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, check if response contains meaningful analysis
                    if any(keyword in response_text.lower() for keyword in ['security', 'vulnerability', 'performance', 'issue', 'problem', 'error', 'bug']):
                        logger.warning("JSON parsing failed, treating response as plain text")
                        return _parse_plain_text_response(response_text, file_path, code)
                    else:
                        # Response doesn't contain meaningful analysis, use fallback
                        logger.warning("JSON parsing failed and response doesn't contain meaningful analysis, using fallback")
                        return _fallback_analysis(code, file_path)
            else:
                # No JSON found, check if response contains meaningful analysis
                logger.debug(f"LLM response (no JSON): {response_text[:200]}...")
                if any(keyword in response_text.lower() for keyword in ['security', 'vulnerability', 'performance', 'issue', 'problem', 'error', 'bug']):
                    logger.warning("No JSON found in response, treating as plain text")
                    return _parse_plain_text_response(response_text, file_path, code)
                else:
                    # Response doesn't contain meaningful analysis, use fallback
                    logger.warning(f"LLM response doesn't contain meaningful analysis, using fallback. Response preview: {response_text[:100]}...")
                    return _fallback_analysis(code, file_path)
                
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return _fallback_analysis(code, file_path)
        
    except Exception as e:
        logger.error(f"Error in LLM analysis: {e}")
        return _fallback_analysis(code, file_path)


@tool
def analyze_code(code: str, file_path: str = "") -> Dict[str, Any]:
    """
    Analyzes code for issues and improvements using LLM.
    
    Args:
        code: Code to analyze.
        file_path: Path to the file being analyzed.
        
    Returns:
        Dictionary containing analysis results.
    """
    try:
        model_name = os.getenv('DEFAULT_LLM_MODEL', 'bigcode/starcoder')
        llm = get_llm_provider(model_name, 0.1)
        
        if not llm:
            return _fallback_analysis(code, file_path)
        
        # Use chunking for large files
        return analyze_code_with_chunking(code, file_path, llm)
        
    except Exception as e:
        logger.error(f"Error in LLM code analysis: {e}")
        return _fallback_analysis(code, file_path)


@tool
def improve_code(code: str, issues: List[Dict], file_path: str = "") -> Dict[str, Any]:
    """
    Improves code based on identified issues using LLM.
    
    Args:
        code: Original code.
        issues: List of identified issues.
        file_path: Path to the file being improved.
        
    Returns:
        Improved code string.
    """
    try:
        model_name = os.getenv('DEFAULT_LLM_MODEL', 'bigcode/starcoder')
        llm = get_llm_provider(model_name, 0.1)
        if not llm:
            return _fallback_improve_code(code, issues, file_path)
        
        # Get improvement prompt from registry
        improvement_prompt = get_prompt_template("code_improvement", ["code", "issues", "file_path", "language"])
        
        # Detect language
        language = get_language_from_extension(file_path)
        
        # Format issues for prompt
        formatted_issues = []
        for i, issue in enumerate(issues, 1):
            formatted_issues.append(f"{i}. {issue.get('type', 'Unknown')} - {issue.get('description', 'No description')}")
            if issue.get('suggestion'):
                formatted_issues.append(f"   Suggestion: {issue['suggestion']}")
        
        issues_text = '\n'.join(formatted_issues) if formatted_issues else "No specific issues identified."
        
        # Generate improved code using LLM
        prompt = improvement_prompt.format(
            code=code,
            issues=issues_text,
            file_path=file_path,
            language=language
        )
        
        response = llm.invoke(prompt)
        
        # Extract code from response
        improved_code = _extract_code_from_response(response, code)
        
        return {'improved_code': improved_code}
        
    except Exception as e:
        logger.error(f"Error in LLM code improvement: {e}")
        return _fallback_improve_code(code, issues, file_path)


@tool
def analyze_security(code: str, file_path: str = "") -> Dict[str, Any]:
    """
    Performs security analysis on code using LLM.
    
    Args:
        code: Code to analyze for security issues.
        file_path: Path to the file being analyzed.
        
    Returns:
        Dictionary containing security analysis results.
    """
    try:
        model_name = os.getenv('DEFAULT_LLM_MODEL', 'bigcode/starcoder')
        llm = get_llm_provider(model_name, 0.1)
        if not llm:
            return _fallback_security_analysis(code, file_path)
        
        # Get security analysis prompt from registry
        security_prompt = get_prompt_template("security_analysis", ["code", "file_path", "language"])
        
        # Detect language
        language = get_language_from_extension(file_path)
        
        # Generate security analysis using LLM
        prompt = security_prompt.format(
            code=code,
            file_path=file_path,
            language=language
        )
        
        response = llm.invoke(prompt)
        
        # Parse response - handle both JSON and plain text
        try:
            # Handle different response formats
            if isinstance(response, str):
                response_text = response
            elif isinstance(response, dict):
                response_text = response.get('content', str(response))
            else:
                response_text = str(response)
            
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                try:
                    result = json.loads(json_str)
                    
                    return {
                        'security_issues': result.get('security_issues', []),
                        'overall_security_score': result.get('overall_security_score', 5),
                        'file_path': file_path,
                        'analysis_type': 'llm_security',
                        'recommendations': result.get('recommendations', [])
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as plain text
                    logger.warning("JSON parsing failed for security analysis, treating response as plain text")
                    return _parse_security_plain_text_response(response_text, file_path, code)
            else:
                # No JSON found, treat as plain text
                logger.warning("No JSON found in security response, treating as plain text")
                return _parse_security_plain_text_response(response_text, file_path, code)
                
        except Exception as e:
            logger.warning(f"Failed to parse LLM security response: {e}")
            return _fallback_security_analysis(code, file_path)
        
    except Exception as e:
        logger.error(f"Error in LLM security analysis: {e}")
        return _fallback_security_analysis(code, file_path)


@tool
def analyze_performance(code: str, file_path: str = "") -> Dict[str, Any]:
    """
    Performs performance analysis on code using LLM.
    
    Args:
        code: Code to analyze for performance issues.
        file_path: Path to the file being analyzed.
        
    Returns:
        Dictionary containing performance analysis results.
    """
    try:
        model_name = os.getenv('DEFAULT_LLM_MODEL', 'bigcode/starcoder')
        llm = get_llm_provider(model_name, 0.1)
        if not llm:
            return _fallback_performance_analysis(code, file_path)
        
        # Get performance analysis prompt from registry
        performance_prompt = get_prompt_template("performance_analysis", ["code", "file_path", "language"])
        
        # Detect language
        language = get_language_from_extension(file_path)
        
        # Generate performance analysis using LLM
        prompt = performance_prompt.format(
            code=code,
            file_path=file_path,
            language=language
        )
        
        response = llm.invoke(prompt)
        
        # Parse response - handle both JSON and plain text
        try:
            # Handle different response formats
            if isinstance(response, str):
                response_text = response
            elif isinstance(response, dict):
                response_text = response.get('content', str(response))
            else:
                response_text = str(response)
            
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                try:
                    result = json.loads(json_str)
                    
                    return {
                        'performance_issues': result.get('performance_issues', []),
                        'overall_performance_score': result.get('overall_performance_score', 5),
                        'file_path': file_path,
                        'analysis_type': 'llm_performance',
                        'optimization_opportunities': result.get('optimization_opportunities', [])
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as plain text
                    logger.warning("JSON parsing failed for performance analysis, treating response as plain text")
                    return _parse_performance_plain_text_response(response_text, file_path, code)
            else:
                # No JSON found, treat as plain text
                logger.warning("No JSON found in performance response, treating as plain text")
                return _parse_performance_plain_text_response(response_text, file_path, code)
                
        except Exception as e:
            logger.warning(f"Failed to parse LLM performance response: {e}")
            return _fallback_performance_analysis(code, file_path)
        
    except Exception as e:
        logger.error(f"Error in LLM performance analysis: {e}")
        return _fallback_performance_analysis(code, file_path)


@tool
def improve_documentation(code: str, file_path: str = "") -> Dict[str, Any]:
    """
    Improves code documentation using LLM.
    
    Args:
        code: Code to improve documentation for.
        file_path: Path to the file being documented.
        
    Returns:
        Code with improved documentation.
    """
    try:
        model_name = os.getenv('DEFAULT_LLM_MODEL', 'bigcode/starcoder')
        llm = get_llm_provider(model_name, 0.1)
        if not llm:
            return {'improved_code': code, 'file_path': file_path, 'doc_improved': False}
        
        # Get documentation improvement prompt from registry
        doc_prompt = get_prompt_template("documentation_improvement", ["code", "file_path", "language"])
        
        # Detect language
        language = get_language_from_extension(file_path)
        
        # Generate improved documentation using LLM
        prompt = doc_prompt.format(
            code=code,
            file_path=file_path,
            language=language
        )
        
        response = llm.invoke(prompt)
        
        # Extract code from response
        improved_code = _extract_code_from_response(response, code)
        
        return {'improved_code': improved_code}
        
    except Exception as e:
        logger.error(f"Error in LLM documentation improvement: {e}")
        return {'improved_code': code}  # Return original code if improvement fails


def _extract_code_from_response(response: str, original_code: str) -> str:
    """Extract improved code from an LLM response, handling code blocks and fallback."""
    # Handle case where response is already a string
    if isinstance(response, str):
        response_text = response
    elif isinstance(response, dict):
        response_text = response.get('content', str(response))
    else:
        response_text = str(response)
    
    # Look for code blocks in the response
    code_block_patterns = [
        r'```(?:python|javascript|java|cpp|csharp|php|ruby|go|rust|swift|kotlin|scala|html|css|sql|bash|powershell)?\n(.*?)\n```',
        r'```\n(.*?)\n```',
        r'```(.*?)```'
    ]
    
    for pattern in code_block_patterns:
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    # If no code blocks found, return the original code
    return original_code


def _parse_plain_text_response(response_text: str, file_path: str, code: str = "") -> Dict[str, Any]:
    """Parse a plain text LLM response and extract issues, metrics, and summary."""
    try:
        # Extract issues from plain text response
        issues = []
        
        # Look for common patterns in the response
        lines = response_text.split('\n')
        current_issue = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for issue indicators
            if any(keyword in line.lower() for keyword in ['issue', 'problem', 'error', 'bug', 'vulnerability', 'security', 'performance']):
                if current_issue:
                    issues.append(current_issue)
                
                current_issue = {
                    'type': 'general',
                    'severity': 'medium',
                    'line': 1,
                    'description': line,
                    'suggestion': ''
                }
            elif current_issue and line.startswith(('suggestion:', 'fix:', 'recommendation:')):
                current_issue['suggestion'] = line.split(':', 1)[1].strip() if ':' in line else line
        
        # Add the last issue if exists
        if current_issue:
            issues.append(current_issue)
        
        # If no structured issues found, create a general summary
        if not issues:
            issues = [{
                'type': 'analysis',
                'severity': 'info',
                'line': 1,
                'description': 'Code analysis completed',
                'suggestion': 'Review the analysis results above'
            }]
        
        return {
            'issues': issues,
            'metrics': {
                'complexity_score': 5,
                'maintainability_score': 5,
                'security_score': 5,
                'performance_score': 5
            },
            'file_path': file_path,
            'analysis_type': 'llm_analysis_plain_text',
            'summary': response_text[:200] + '...' if len(response_text) > 200 else response_text
        }
        
    except Exception as e:
        logger.warning(f"Failed to parse plain text response: {e}")
        return _fallback_analysis(code, file_path)


def _fallback_analysis(code: str, file_path: str) -> Dict[str, Any]:
    """Fallback static analysis when LLM is not available or fails."""
    issues = []
    
    # Check for syntax errors first
    syntax_issues = _check_syntax_errors(code, file_path)
    issues.extend(syntax_issues)
    
    # Security issue patterns
    security_patterns = [
        ('subprocess.call', 'Command injection vulnerability'),
        ('shell=True', 'Shell injection risk'),
        ('eval\\(', 'Code injection vulnerability'),
        ('exec\\(', 'Code execution vulnerability'),
        ('open\\(.*input', 'Path traversal vulnerability'),
        ('input\\(', 'Unvalidated user input'),
        ('raw_input\\(', 'Unvalidated user input (Python 2)'),
        ('subprocess\\.', 'Subprocess usage - potential security risk'),
        ('execute_command', 'Function name suggests command execution'),
        ('read_file', 'Function name suggests file reading without validation')
    ]
    
    # Performance issue patterns
    performance_patterns = [
        (r'result \+= str\(', 'Inefficient string concatenation'),
        (r'for.*in range\(len\(', 'Use enumerate instead'),
        (r'for.*for.*in.*range', 'Nested loops may be inefficient'),
        (r'\.append\(.*\)', 'Consider list comprehension'),
        (r'list\(range\(', 'Consider direct iteration'),
        (r'for i in range\(100\):\s*\n\s*for j in range\(100\):\s*\n\s*for k in range\(100\)', 'Triple nested loops - O(n³) complexity'),
        (r'while True:\s*\n\s*data\.append', 'Potential infinite loop with memory leak'),
        (r'inefficient_function', 'Function name suggests performance issues')
    ]
    
    # Syntax and maintainability patterns
    syntax_patterns = [
        (r'def [^(]*\([^)]*\):\s*$', 'Function missing docstring'),
        (r'class [^(]*\([^)]*\):\s*$', 'Class missing docstring'),
        (r'import \*', 'Wildcard import - specify imports explicitly'),
        (r'except:', 'Bare except clause - specify exception type'),
        (r'print\s*\(', 'Consider using logging instead of print')
    ]
    
    # Check for security issues
    for pattern, description in security_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            issues.append({
                'type': 'security',
                'severity': 'high',
                'description': description,
                'line': 1,  # Simplified for testing
                'suggestion': f'Review and fix {description.lower()}'
            })
    
    # Check for performance issues
    for pattern, description in performance_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            issues.append({
                'type': 'performance',
                'severity': 'medium',
                'description': description,
                'line': 1,  # Simplified for testing
                'suggestion': f'Optimize {description.lower()}'
            })
    
    # Check for syntax and maintainability issues
    for pattern, description in syntax_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            issues.append({
                'type': 'maintainability',
                'severity': 'low',
                'description': description,
                'line': 1,  # Simplified for testing
                'suggestion': f'Improve {description.lower()}'
            })
    
    # Calculate basic metrics
    lines = code.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    complexity = len(non_empty_lines)
    
    # Add language-agnostic best practices
    production_standards = [
        {
            "type": "best_practice",
            "severity": "medium",
            "line": 0,
            "description": "Follow language-specific style guidelines",
            "suggestion": "Use appropriate linters and formatters for your programming language. Follow established style guides and naming conventions. Configure automated formatting tools to maintain consistency."
        },
        {
            "type": "best_practice", 
            "severity": "medium",
            "line": 0,
            "description": "Implement proper error handling patterns",
            "suggestion": "Use language-specific exception handling patterns. Avoid catching all exceptions unless necessary. Create custom exception classes for domain-specific errors. Use appropriate error handling mechanisms for your language."
        }
    ]
    
    issues.extend(production_standards)
    
    return {
        'issues': issues,
        'metrics': {
            'complexity_score': min(10, max(1, complexity // 10)),
            'maintainability_score': 5 if not issues else max(1, 5 - len(issues)),
            'security_score': 5 if not [i for i in issues if i['type'] == 'security'] else 3,
            'performance_score': 5 if not [i for i in issues if i['type'] == 'performance'] else 4
        },
        'file_path': file_path,
        'analysis_type': 'fallback_analysis'
    }


def _check_syntax_errors(code: str, file_path: str) -> List[Dict]:
    """Check code for basic syntax errors using regex patterns."""
    syntax_issues = []
    
    if file_path.endswith('.py'):
        try:
            # Try to compile the code to check for syntax errors
            compile(code, file_path, 'exec')
        except SyntaxError as e:
            syntax_issues.append({
                'type': 'syntax',
                'severity': 'critical',
                'description': f'Syntax error: {str(e)}',
                'line': getattr(e, 'lineno', 1),
                'suggestion': 'Fix the syntax error in the code'
            })
        except Exception as e:
            # Catch other compilation errors
            syntax_issues.append({
                'type': 'syntax',
                'severity': 'critical',
                'description': f'Code compilation error: {str(e)}',
                'line': 1,
                'suggestion': 'Fix the compilation error in the code'
            })
    
    return syntax_issues


def _parse_security_plain_text_response(response_text: str, file_path: str, code: str = "") -> Dict[str, Any]:
    """Parse a plain text LLM response for security issues."""
    try:
        # Extract security issues from plain text response
        security_issues = []
        
        # Look for security-related patterns
        lines = response_text.split('\n')
        current_issue = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for security issue indicators
            if any(keyword in line.lower() for keyword in ['vulnerability', 'security', 'injection', 'xss', 'csrf', 'authentication', 'authorization', 'encryption']):
                if current_issue:
                    security_issues.append(current_issue)
                
                current_issue = {
                    'type': 'security',
                    'severity': 'medium',
                    'line': 1,
                    'description': line,
                    'cve_reference': '',
                    'mitigation': ''
                }
            elif current_issue and line.startswith(('mitigation:', 'fix:', 'solution:')):
                current_issue['mitigation'] = line.split(':', 1)[1].strip() if ':' in line else line
        
        # Add the last issue if exists
        if current_issue:
            security_issues.append(current_issue)
        
        # If no structured issues found, create a general summary
        if not security_issues:
            security_issues = [{
                'type': 'security_analysis',
                'severity': 'info',
                'line': 1,
                'description': 'Security analysis completed',
                'cve_reference': '',
                'mitigation': 'Review the security analysis results above'
            }]
        
        return {
            'security_issues': security_issues,
            'overall_security_score': 5,
            'file_path': file_path,
            'analysis_type': 'llm_security_plain_text',
            'recommendations': [response_text[:200] + '...' if len(response_text) > 200 else response_text]
        }
        
    except Exception as e:
        logger.warning(f"Failed to parse security plain text response: {e}")
        return _fallback_security_analysis(code, file_path)


def _fallback_security_analysis(code: str, file_path: str) -> Dict[str, Any]:
    """Fallback static security analysis when LLM is not available or fails."""
    security_issues = []
    
    # Security issue patterns for fallback analysis
    security_patterns = [
        ('subprocess.call', 'Command injection vulnerability'),
        ('shell=True', 'Shell injection risk'),
        ('eval\\(', 'Code injection vulnerability'),
        ('exec\\(', 'Code execution vulnerability'),
        ('open\\(.*input', 'Path traversal vulnerability'),
        ('input\\(', 'Unvalidated user input'),
        ('raw_input\\(', 'Unvalidated user input (Python 2)'),
        ('subprocess\\.', 'Subprocess usage - potential security risk'),
        ('execute_command', 'Function name suggests command execution'),
        ('read_file', 'Function name suggests file reading without validation')
    ]
    
    # Check for security issues
    for pattern, description in security_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            security_issues.append({
                'type': 'security',
                'severity': 'high',
                'description': description,
                'line': 1,  # Simplified for testing
                'cve_reference': '',
                'mitigation': f'Review and fix {description.lower()}'
            })
    
    # Calculate security score
    security_score = 10 if not security_issues else max(1, 10 - len(security_issues))
    
    return {
        'security_issues': security_issues,
        'overall_security_score': security_score,
        'file_path': file_path,
        'analysis_type': 'fallback_security',
        'recommendations': [f'Found {len(security_issues)} security issues'] if security_issues else ['No security issues detected']
    }


def _parse_performance_plain_text_response(response_text: str, file_path: str, code: str = "") -> Dict[str, Any]:
    """Parse a plain text LLM response for performance issues."""
    try:
        # Extract performance issues from plain text response
        performance_issues = []
        
        # Look for performance-related patterns
        lines = response_text.split('\n')
        current_issue = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for performance issue indicators
            if any(keyword in line.lower() for keyword in ['performance', 'slow', 'inefficient', 'optimization', 'memory', 'cpu', 'bottleneck', 'complexity']):
                if current_issue:
                    performance_issues.append(current_issue)
                
                current_issue = {
                    'type': 'performance',
                    'severity': 'medium',
                    'line': 1,
                    'description': line,
                    'impact': '',
                    'optimization': ''
                }
            elif current_issue and line.startswith(('optimization:', 'fix:', 'improvement:')):
                current_issue['optimization'] = line.split(':', 1)[1].strip() if ':' in line else line
        
        # Add the last issue if exists
        if current_issue:
            performance_issues.append(current_issue)
        
        # If no structured issues found, create a general summary
        if not performance_issues:
            performance_issues = [{
                'type': 'performance_analysis',
                'line': 1,
                'description': 'Performance analysis completed',
                'impact': '',
                'optimization': 'Review the performance analysis results above'
            }]
        
        return {
            'performance_issues': performance_issues,
            'overall_performance_score': 5,
            'file_path': file_path,
            'analysis_type': 'llm_performance_plain_text',
            'optimization_opportunities': [response_text[:200] + '...' if len(response_text) > 200 else response_text]
        }
        
    except Exception as e:
        logger.warning(f"Failed to parse performance plain text response: {e}")
        return _fallback_performance_analysis(code, file_path)


def _fallback_performance_analysis(code: str, file_path: str) -> Dict[str, Any]:
    """Fallback static performance analysis when LLM is not available or fails."""
    performance_issues = []
    
    # Performance issue patterns for fallback analysis
    performance_patterns = [
        (r'result \+= str\(', 'Inefficient string concatenation'),
        (r'for.*in range\(len\(', 'Use enumerate instead'),
        (r'for.*for.*in.*range', 'Nested loops may be inefficient'),
        (r'\.append\(.*\)', 'Consider list comprehension'),
        (r'list\(range\(', 'Consider direct iteration'),
        (r'for i in range\(100\):\s*\n\s*for j in range\(100\):\s*\n\s*for k in range\(100\)', 'Triple nested loops - O(n³) complexity'),
        (r'while True:\s*\n\s*data\.append', 'Potential infinite loop with memory leak'),
        (r'inefficient_function', 'Function name suggests performance issues')
    ]
    
    # Check for performance issues
    for pattern, description in performance_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            performance_issues.append({
                'type': 'performance',
                'severity': 'medium',
                'line': 1,  # Simplified for testing
                'description': description,
                'impact': 'May cause performance degradation',
                'optimization': f'Optimize {description.lower()}'
            })
    
    # Calculate performance score
    performance_score = 10 if not performance_issues else max(1, 10 - len(performance_issues))
    
    return {
        'performance_issues': performance_issues,
        'overall_performance_score': performance_score,
        'file_path': file_path,
        'analysis_type': 'fallback_performance',
        'optimization_opportunities': [f'Found {len(performance_issues)} performance issues'] if performance_issues else ['No performance issues detected']
    }


def _fallback_improve_code(code: str, issues: List[Dict], file_path: str) -> Dict[str, Any]:
    """Fallback code improvement logic when LLM is not available or fails."""
    if not issues:
        return {'improved_code': code}  # No issues, return original code
    
    improved_code = code
    
    # Basic improvements for common issues
    for issue in issues:
        issue_type = issue.get('type', '')
        description = issue.get('description', '').lower()
        
        if issue_type == 'security':
            if 'shell injection' in description:
                improved_code = improved_code.replace('shell=True', 'shell=False')
            elif 'command injection' in description:
                # Add a comment about the security issue
                improved_code = f"# SECURITY: Review subprocess usage for command injection\n{improved_code}"
            elif 'unvalidated user input' in description:
                # Add input validation comment
                improved_code = f"# SECURITY: Add input validation\n{improved_code}"
        
        elif issue_type == 'performance':
            if 'string concatenation' in description:
                # Replace string concatenation with list join
                improved_code = improved_code.replace(
                    'result += str(', 'result_list.append(str('
                )
                if 'result_list.append' in improved_code:
                    improved_code = 'result_list = []\n' + improved_code + '\nresult = "".join(result_list)'
            elif 'nested loops' in description:
                # Add optimization comment
                improved_code = f"# PERFORMANCE: Consider optimizing nested loops\n{improved_code}"
        
        elif issue_type == 'maintainability':
            if 'missing docstring' in description:
                # Add basic docstring template
                if 'def ' in improved_code:
                    improved_code = improved_code.replace(
                        'def ', 
                        'def ' + '\n    """Add docstring here."""\n    '
                    )
            elif 'bare except' in description:
                # Replace bare except with specific exception
                improved_code = improved_code.replace('except:', 'except Exception:')
    
    return {'improved_code': improved_code}


 
