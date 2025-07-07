"""
Agents module for configuring Crew AI agents for code review tasks.

This module sets up and orchestrates AI agents for different aspects
of code review including analysis, improvement, and reporting.
"""

from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEndpoint
from typing import Dict, List, Optional, Any
import logging
import json
import os
import re
from .llm_provider import create_llm_provider

logger = logging.getLogger(__name__)


class CodeReviewAgents:
    """AI agents for comprehensive code review."""
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize code review agents.
        
        Args:
            llm_config: Configuration for LLM setup
        """
        self.llm_config = llm_config
        self.llm = None
        self.agents = {}
        self._setup_llm()
        self._setup_agents()
    
    def _setup_llm(self):
        """Setup LLM with robust fallback system."""
        try:
            # Use the new LLM provider system
            self.llm = create_llm_provider(self.llm_config)
            
            # Log provider information
            provider_info = self.llm.get_provider_info()
            logger.info(f"LLM Provider: {provider_info['provider']}")
            logger.info(f"Fallback mode: {provider_info['fallback_mode']}")
            
            if provider_info['fallback_mode']:
                logger.warning("Running in fallback mode - using static analysis only")
            
        except Exception as e:
            logger.error(f"Failed to setup LLM: {e}")
            # Create fallback LLM
            self.llm = self._create_fallback_llm()
    
    def _create_fallback_llm(self):
        """Create a fallback LLM for when all providers fail."""
        class FallbackLLM:
            def __init__(self):
                self.name = "fallback_llm"
                self.model_name = "fallback_static_analysis"
            
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
        
        return FallbackLLM()
    
    def _setup_agents(self) -> Dict[str, Agent]:
        """Setup different types of agents for code review."""
        agents = {}
        
        # Code Reviewer Agent
        agents['reviewer'] = Agent(
            role="Senior Code Reviewer",
            goal="Perform comprehensive code analysis and identify issues",
            backstory="""You are a senior software engineer with 15+ years of experience 
            in code review, security analysis, and performance optimization. You have 
            worked with multiple programming languages and frameworks, and have a deep 
            understanding of software engineering best practices, design patterns, and 
            common pitfalls. You are known for your thorough analysis and ability to 
            identify both obvious and subtle issues in code.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Security Specialist Agent
        agents['security'] = Agent(
            role="Security Specialist",
            goal="Identify and analyze security vulnerabilities in code",
            backstory="""You are a cybersecurity expert specializing in application 
            security, penetration testing, and secure coding practices. You have 
            extensive experience identifying vulnerabilities like SQL injection, 
            XSS, authentication bypasses, and other security issues. You stay 
            updated with the latest security threats and mitigation strategies.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Performance Engineer Agent
        agents['performance'] = Agent(
            role="Performance Engineer",
            goal="Analyze and optimize code for better performance",
            backstory="""You are a performance engineering expert with deep knowledge 
            of algorithms, data structures, and system optimization. You specialize 
            in identifying performance bottlenecks, memory leaks, and optimization 
            opportunities. You have experience with profiling tools and performance 
            testing methodologies.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Code Improver Agent
        agents['improver'] = Agent(
            role="Code Improvement Specialist",
            goal="Refactor and improve code based on identified issues",
            backstory="""You are a software architect and refactoring expert with 
            extensive experience in improving code quality, readability, and 
            maintainability. You excel at applying design patterns, improving 
            code structure, and ensuring best practices are followed while 
            maintaining functionality.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Documentation Specialist Agent
        agents['documentation'] = Agent(
            role="Technical Documentation Specialist",
            goal="Improve code documentation and create comprehensive reports",
            backstory="""You are a technical writer and documentation expert with 
            experience in creating clear, comprehensive documentation for software 
            projects. You understand the importance of good documentation for 
            maintainability and knowledge transfer. You excel at writing clear 
            docstrings, comments, and technical reports.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        self.agents = agents
        return agents
    
    def review_code(self, code: str, file_path: str = "") -> Dict[str, Any]:
        """
        Review code for issues and improvements.
        
        Args:
            code: Code to review.
            file_path: Path to the file being reviewed.
            
        Returns:
            Dictionary containing review results.
        """
        # Use default requirements for backward compatibility
        requirements = {
            "code_quality": "Ensure high code quality and maintainability",
            "security": "Identify and fix security vulnerabilities",
            "performance": "Optimize for performance where possible",
            "readability": "Ensure code is readable and well-documented"
        }
        return self.run_code_review(code, requirements, file_path)
    
    def run_code_review(self, code: str, requirements: Dict[str, str], file_path: str = "") -> Dict[str, Any]:
        """
        Run comprehensive code review using multiple agents.
        
        Args:
            code: Code to review.
            requirements: FRD requirements.
            file_path: Path to the file being reviewed.
            
        Returns:
            Dictionary containing review results.
        """
        try:
            # Check if we're using fallback mode
            if hasattr(self.llm, 'name') and self.llm.name == "fallback_llm":
                logger.info("Using fallback code review mode")
                return self._run_fallback_review(code, file_path)
            
            # Create tasks for different aspects of review
            tasks = self._create_review_tasks(code, requirements, file_path)
            
            # Create crew with all agents
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=tasks,
                verbose=True
            )
            
            # Execute the review
            result = crew.kickoff()
            
            # Parse and structure the results
            return self._parse_review_results(result, code, file_path)
            
        except Exception as e:
            logger.error(f"Error during code review: {e}")
            return self._run_fallback_review(code, file_path)
    
    def _run_fallback_review(self, code: str, file_path: str) -> Dict[str, Any]:
        """Run a fallback code review when LLM is not available."""
        logger.info("Running fallback code review")
        
        # Handle None or empty code gracefully
        if code is None:
            code = ""
        if not isinstance(code, str):
            code = str(code)
        
        # Basic static analysis
        issues = []
        lines = code.split('\n') if code else []
        
        # Check for common security issues
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # Security issues
            if 'eval(' in line:
                issues.append({
                    'type': 'security',
                    'severity': 'critical',
                    'description': 'Use of eval() function detected - critical security risk',
                    'line': i,
                    'suggestion': 'Replace eval() with safer alternatives',
                    'code_snippet': line.strip()
                })
            
            if 'system(' in line:
                issues.append({
                    'type': 'security',
                    'severity': 'critical',
                    'description': 'Command injection vulnerability detected',
                    'line': i,
                    'suggestion': 'Use proper input validation and sanitization',
                    'code_snippet': line.strip()
                })
            
            if 'password' in line_lower and '=' in line:
                issues.append({
                    'type': 'security',
                    'severity': 'high',
                    'description': 'Hardcoded password detected',
                    'line': i,
                    'suggestion': 'Use environment variables or secure configuration',
                    'code_snippet': line.strip()
                })
            
            if 'api_key' in line_lower and '=' in line:
                issues.append({
                    'type': 'security',
                    'severity': 'high',
                    'description': 'Hardcoded API key detected',
                    'line': i,
                    'suggestion': 'Use environment variables for sensitive data',
                    'code_snippet': line.strip()
                })
            
            # Performance issues
            if 'for ' in line and ' in ' in line and 'for ' in line:
                issues.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'description': 'Nested loops detected - potential performance issue',
                    'line': i,
                    'suggestion': 'Consider optimizing nested loops or using more efficient algorithms',
                    'code_snippet': line.strip()
                })
            
            if '+=' in line and '"' in line:
                issues.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'description': 'Inefficient string concatenation detected',
                    'line': i,
                    'suggestion': 'Use string interpolation or join() method',
                    'code_snippet': line.strip()
                })
            
            # Maintainability issues
            if len(line) > 120:
                issues.append({
                    'type': 'maintainability',
                    'severity': 'low',
                    'description': 'Line too long - affects readability',
                    'line': i,
                    'suggestion': 'Break long lines for better readability',
                    'code_snippet': line.strip()
                })
        
        # Check for global variables
        if '$' in code:
            issues.append({
                'type': 'maintainability',
                'severity': 'medium',
                'description': 'Global variables detected - poor practice',
                'line': 1,
                'suggestion': 'Avoid global variables, use proper encapsulation',
                'code_snippet': 'Global variables found'
            })
        
        # Check for monkey patching
        if 'class String' in code or 'class Array' in code:
            issues.append({
                'type': 'maintainability',
                'severity': 'high',
                'description': 'Monkey patching detected - dangerous practice',
                'line': 1,
                'suggestion': 'Avoid monkey patching, use proper inheritance or modules',
                'code_snippet': 'Monkey patching found'
            })
        
        # Calculate metrics based on issues
        security_issues = len([i for i in issues if i['type'] == 'security'])
        performance_issues = len([i for i in issues if i['type'] == 'performance'])
        maintainability_issues = len([i for i in issues if i['type'] == 'maintainability'])
        
        metrics = {
            'complexity_score': min(10, len(lines) // 5),
            'maintainability_score': max(1, 10 - maintainability_issues),
            'security_score': max(1, 10 - security_issues * 2),
            'performance_score': max(1, 10 - performance_issues)
        }
        
        return {
            'file_path': file_path,
            'issues': issues,
            'improved_code': code,  # No improvements in fallback mode
            'metrics': metrics,
            'summary': f"Fallback analysis completed. Found {len(issues)} issues: {security_issues} security, {performance_issues} performance, {maintainability_issues} maintainability.",
            'raw_result': f"Fallback analysis for {file_path}"
        }
    
    def _create_review_tasks(self, code: str, requirements: Dict[str, str], file_path: str) -> List[Task]:
        """Create tasks for different aspects of code review."""
        tasks = []
        
        # Main code review task
        review_task = Task(
            description=f"""
            Perform a comprehensive code review of the file: {file_path}
            
            Code to review:
            {code}
            
            Requirements to evaluate against:
            {json.dumps(requirements, indent=2)}
            
            Analyze the code for:
            1. Syntax errors and bugs
            2. Code quality and maintainability
            3. Adherence to best practices
            4. Potential improvements
            
            Provide your analysis in JSON format with issues, metrics, and suggestions.
            """,
            agent=self.agents['reviewer'],
            expected_output="JSON formatted analysis with issues, metrics, and improved code"
        )
        tasks.append(review_task)
        
        # Security analysis task
        security_task = Task(
            description=f"""
            Perform a detailed security analysis of the code in file: {file_path}
            
            Code to analyze:
            {code}
            
            Focus on identifying:
            1. Input validation vulnerabilities
            2. SQL injection risks
            3. XSS vulnerabilities
            4. Authentication/authorization issues
            5. Sensitive data exposure
            6. Other security concerns
            
            Provide security analysis in JSON format.
            """,
            agent=self.agents['security'],
            expected_output="JSON formatted security analysis with vulnerabilities and recommendations"
        )
        tasks.append(security_task)
        
        # Performance analysis task
        performance_task = Task(
            description=f"""
            Analyze the performance characteristics of the code in file: {file_path}
            
            Code to analyze:
            {code}
            
            Focus on:
            1. Algorithm efficiency
            2. Memory usage patterns
            3. Performance bottlenecks
            4. Optimization opportunities
            5. Scalability concerns
            
            Provide performance analysis in JSON format.
            """,
            agent=self.agents['performance'],
            expected_output="JSON formatted performance analysis with issues and optimization suggestions"
        )
        tasks.append(performance_task)
        
        return tasks
    
    def run_code_improvement(self, original_code: str, issues: List[Dict], file_path: str = "") -> str:
        """
        Run code improvement based on identified issues.
        
        Args:
            original_code: Original code content.
            issues: List of identified issues.
            file_path: Path to the file being improved.
            
        Returns:
            Improved code string.
        """
        try:
            improvement_task = Task(
                description=f"""
                Improve the code in file: {file_path} based on the identified issues.
                
                Original code:
                {original_code}
                
                Issues to address:
                {json.dumps(issues, indent=2)}
                
                Requirements:
                1. Fix all identified issues
                2. Maintain original functionality
                3. Improve code quality and readability
                4. Follow best practices
                5. Add appropriate documentation
                
                Return the complete improved code.
                """,
                agent=self.agents['improver'],
                expected_output="Complete improved code with all issues addressed"
            )
            
            crew = Crew(
                agents=[self.agents['improver']],
                tasks=[improvement_task],
                verbose=True
            )
            
            result = crew.kickoff()
            return self._extract_improved_code(result)
            
        except Exception as e:
            logger.error(f"Error during code improvement: {e}")
            return original_code
    
    def run_documentation_improvement(self, code: str, file_path: str = "") -> str:
        """
        Improve code documentation.
        
        Args:
            code: Code to improve documentation for.
            file_path: Path to the file being documented.
            
        Returns:
            Code with improved documentation.
        """
        try:
            doc_task = Task(
                description=f"""
                Improve the documentation for the code in file: {file_path}
                
                Code to document:
                {code}
                
                Requirements:
                1. Add comprehensive docstrings for functions and classes
                2. Add inline comments for complex logic
                3. Improve existing documentation
                4. Follow language-specific documentation standards
                5. Make the code more understandable
                
                Return the complete documented code.
                """,
                agent=self.agents['documentation'],
                expected_output="Complete code with improved documentation"
            )
            
            crew = Crew(
                agents=[self.agents['documentation']],
                tasks=[doc_task],
                verbose=True
            )
            
            result = crew.kickoff()
            return self._extract_improved_code(result)
            
        except Exception as e:
            logger.error(f"Error during documentation improvement: {e}")
            return code
    
    def _parse_review_results(self, result: str, original_code: str, file_path: str) -> Dict[str, Any]:
        """Parse and structure the review results."""
        try:
            # Try to extract JSON from the result
            json_start = result.find('{')
            json_end = result.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = result[json_start:json_end]
                parsed_result = json.loads(json_str)
                
                # Ensure all required fields are present
                return {
                    'file_path': file_path,
                    'issues': parsed_result.get('issues', []),
                    'improved_code': parsed_result.get('improved_code', original_code),
                    'metrics': parsed_result.get('metrics', {
                        'complexity_score': 5,
                        'maintainability_score': 5,
                        'security_score': 5,
                        'performance_score': 5
                    }),
                    'summary': parsed_result.get('summary', ''),
                    'raw_result': result
                }
            else:
                # Fallback if no JSON found
                return {
                    'file_path': file_path,
                    'issues': [],
                    'improved_code': original_code,
                    'metrics': {
                        'complexity_score': 5,
                        'maintainability_score': 5,
                        'security_score': 5,
                        'performance_score': 5
                    },
                    'summary': result,
                    'raw_result': result
                }
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from review result: {e}")
            return {
                'file_path': file_path,
                'issues': [],
                'improved_code': original_code,
                'metrics': {
                    'complexity_score': 5,
                    'maintainability_score': 5,
                    'security_score': 5,
                    'performance_score': 5
                },
                'summary': result,
                'raw_result': result
            }
    
    def _extract_improved_code(self, result: str) -> str:
        """Extract improved code from agent result."""
        # Look for code blocks in the result
        code_block_patterns = [
            r'```(?:python|javascript|java|cpp|csharp|php|ruby|go|rust|swift|kotlin|scala|html|css|sql|bash|powershell)?\n(.*?)\n```',
            r'```\n(.*?)\n```',
            r'```(.*?)```'
        ]
        
        for pattern in code_block_patterns:
            matches = re.findall(pattern, result, re.DOTALL)
            if matches:
                return matches[0].strip()
        
        # If no code blocks found, return the entire result
        return result.strip()


def setup_agents(llm_config: Dict[str, Any]) -> CodeReviewAgents:
    """
    Setup and configure code review agents.
    
    Args:
        llm_config: Configuration for LLM models.
        
    Returns:
        Configured CodeReviewAgents instance.
    """
    return CodeReviewAgents(llm_config)


def run_review(agents: CodeReviewAgents, prompt: str, code: str, file_path: str = "") -> Dict[str, Any]:
    """
    Run a code review using the provided agents.
    
    Args:
        agents: Configured CodeReviewAgents instance.
        prompt: Review prompt.
        code: Code to review.
        file_path: Path to the file being reviewed.
        
    Returns:
        Review results dictionary.
    """
    return agents.run_code_review(code, {}, file_path) 