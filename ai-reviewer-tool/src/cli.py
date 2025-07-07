"""
Command-line interface for the AI Code Review Tool.

This module provides a CLI for reviewing and improving codebases
using AI agents and LLM-based analysis.
"""

import argparse
import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, using system environment variables

import sys
import os

# Add project root to Python path for direct execution
if __name__ == '__main__':
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from configs.config import config, FocusArea, ReportFormat
except ImportError:
    # Fallback for when running as module
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from configs.config import config, FocusArea, ReportFormat

# Handle relative imports for direct execution
if __name__ == '__main__':
    # Direct execution - use absolute imports
    from src.exceptions import AIReviewerError, ValidationError, ConfigurationError, OutputError
    from src.validation import validator
    from src.ingestion import ingest_frd, ingest_codebase, CodebaseIngestionError
    from src.prompts import get_review_prompt, get_improvement_prompt, get_summary_prompt
    from src.agents import setup_agents, run_review
    from src.tools import analyze_code, improve_code, analyze_security, analyze_performance, improve_documentation
    from src.output import generate_output, generate_report, generate_project_summary, check_output_completeness
    from src.logger import setup_logger, get_logger
else:
    # Module execution - use relative imports
    from .exceptions import AIReviewerError, ValidationError, ConfigurationError, OutputError
    from .validation import validator
    from .ingestion import ingest_frd, ingest_codebase, CodebaseIngestionError
    from .prompts import get_review_prompt, get_improvement_prompt, get_summary_prompt
    from .agents import setup_agents, run_review
    from .tools import analyze_code, improve_code, analyze_security, analyze_performance, improve_documentation
    from .output import generate_output, generate_report, generate_project_summary, check_output_completeness
    from .logger import setup_logger, get_logger

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging with proper configuration
    log_level = "DEBUG" if args.verbose else os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'logs/ai_reviewer.log')
    setup_logger("ai_reviewer", log_level, log_file)
    
    logger.info("AI Reviewer Tool starting", extra={
        'command': args.command,
        'input_path': getattr(args, 'input_path', 'N/A')
    })
    
    try:
        # Validate configuration
        # Check for API keys in environment
        api_keys = ['OPENAI_API_KEY', 'GOOGLE_API_KEY', 'HUGGINGFACEHUB_API_TOKEN', 'GROQ_API_KEY']
        has_api_key = any(os.getenv(key) for key in api_keys)
        if not has_api_key:
            logger.warning("No API keys configured - will use fallback mode")
        
        if args.command == 'review':
            logger.info("Starting review command")
            run_review_command(args)
        elif args.command == 'analyze':
            logger.info("Starting analyze command")
            run_analyze_command(args)
        elif args.command == 'improve':
            logger.info("Starting improve command")
            run_improve_command(args)
        elif args.command == 'summary':
            logger.info("Starting summary command")
            run_summary_command(args)
        else:
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("Operation cancelled by user")
        sys.exit(1)
    except AIReviewerError as e:
        logger.error(f"AI Reviewer error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"Unexpected error: {e}")
        sys.exit(1)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="AI Code Review Tool - Review and improve codebases using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Review a single file
  python -m src.cli review myfile.py

  # Review a directory
  python -m src.cli review ./myproject/

  # Review a ZIP file
  python -m src.cli review project.zip

  # Review a Git repository
  python -m src.cli review https://github.com/user/repo

  # Analyze only (no improvements)
  python -m src.cli analyze ./myproject/ --output-dir ./analysis/

  # Improve specific aspects
  python -m src.cli improve ./myproject/ --focus security,performance

  # Generate summary report
  python -m src.cli summary ./myproject/ --format markdown
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Review command
    review_parser = subparsers.add_parser('review', help='Complete code review and improvement')
    setup_review_parser(review_parser)
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze code without making improvements')
    setup_analyze_parser(analyze_parser)
    
    # Improve command
    improve_parser = subparsers.add_parser('improve', help='Improve code based on analysis')
    setup_improve_parser(improve_parser)
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Generate summary report')
    setup_summary_parser(summary_parser)
    
    # Global options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    return parser


def setup_review_parser(parser: argparse.ArgumentParser):
    """Setup the review command parser."""
    parser.add_argument(
        'input_path',
        help='Path to codebase (file, directory, ZIP, or Git repo URL)'
    )
    
    parser.add_argument(
        '--frd',
        type=str,
        help='Path to Functional Requirements Document'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=os.getenv('OUTPUT_DIR', './output'),
        help=f'Output directory for improved code (default: {os.getenv("OUTPUT_DIR", "./output")})'
    )
    
    parser.add_argument(
        '--focus',
        type=str,
        choices=['security', 'performance', 'readability', 'maintainability', 'all'],
        default='all',
        help='Focus areas for review (default: all)'
    )
    
    parser.add_argument(
        '--llm-model',
        type=str,
        default=os.getenv('LLM_MODEL', 'microsoft/DialoGPT-medium'),
        help=f'Hugging Face LLM model to use (default: {os.getenv("LLM_MODEL", "microsoft/DialoGPT-medium")})'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['markdown', 'json', 'html'],
        default=os.getenv('DEFAULT_REPORT_FORMAT', 'markdown'),
        help=f'Report format (default: {os.getenv("DEFAULT_REPORT_FORMAT", "markdown")})'
    )
    
    parser.add_argument(
        '--exclude',
        type=str,
        nargs='+',
        help='Files or directories to exclude'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        default=int(os.getenv('MAX_PARALLEL_FILES', '5')),
        help='Maximum number of files to process'
    )


def setup_analyze_parser(parser: argparse.ArgumentParser):
    """Setup the analyze command parser."""
    parser.add_argument(
        'input_path',
        help='Path to codebase (file, directory, ZIP, or Git repo URL)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./analysis',
        help='Output directory for analysis results (default: ./analysis)'
    )
    
    parser.add_argument(
        '--focus',
        type=str,
        choices=['security', 'performance', 'readability', 'maintainability', 'all'],
        default='all',
        help='Focus areas for analysis (default: all)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['markdown', 'json', 'html'],
        default=os.getenv('DEFAULT_REPORT_FORMAT', 'markdown'),
        help='Report format (default: markdown)'
    )


def setup_improve_parser(parser: argparse.ArgumentParser):
    """Setup the improve command parser."""
    parser.add_argument(
        'input_path',
        help='Path to codebase (file, directory, ZIP, or Git repo URL)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=os.getenv('DEFAULT_OUTPUT_DIR', './improved_code'),
        help='Output directory for improved code (default: ./improved_code)'
    )
    
    parser.add_argument(
        '--focus',
        type=str,
        nargs='+',
        choices=['security', 'performance', 'readability', 'maintainability'],
        default=['security', 'performance', 'readability', 'maintainability'],
        help='Focus areas for improvement'
    )
    
    parser.add_argument(
        '--analysis-file',
        type=str,
        help='Path to existing analysis file to use'
    )


def setup_summary_parser(parser: argparse.ArgumentParser):
    """Setup the summary command parser."""
    parser.add_argument(
        'input_path',
        help='Path to codebase (file, directory, ZIP, or Git repo URL)'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Output file for summary (default: stdout)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['markdown', 'json', 'html'],
        default=os.getenv('DEFAULT_REPORT_FORMAT', 'markdown'),
        help='Summary format (default: markdown)'
    )


def run_review_command(args):
    """Run the review command."""
    logger.info("Starting review process", extra={
        'input_path': args.input_path,
        'output_dir': args.output_dir,
        'focus': args.focus
    })
    
    try:
        # Ingest codebase
        logger.info("Ingesting codebase")
        codebase_info = ingest_codebase(args.input_path)
        
        # Ingest requirements if provided
        requirements = {}
        if args.frd:
            logger.info("Ingesting requirements document")
            requirements = ingest_frd(args.frd)
        
        # Setup agents
        logger.info("Setting up AI agents")
        llm_config = {
            'model': args.llm_model,
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.1'))
        }
        agents = setup_agents(llm_config)
        
        # Process codebase
        logger.info("Processing codebase")
        results = process_codebase(
            codebase_info=codebase_info,
            requirements=requirements,
            agents=agents,
            focus=args.focus,
            max_files=getattr(args, 'max_files', None),
            exclude_patterns=args.exclude
        )
        
        # Generate output
        output_dir = args.output_dir or os.getenv('OUTPUT_DIR', './output')
        logger.info("Generating output", extra={'output_dir': output_dir})
        
        # Process each result and generate output
        input_file_paths = []
        for result in results:
            if isinstance(result, dict):
                file_info = result.get('file_info', {})
                original_code = file_info.get('content', '')
                improved_code = result.get('improved_code', original_code)
                issues = result.get('analysis', {}).get('issues', [])
                metrics = result.get('analysis', {}).get('metrics', {})
                file_path = file_info.get('path', '')
                if file_path:
                    input_file_paths.append(file_path)
                generate_output(
                    original_code=original_code,
                    improved_code=improved_code,
                    issues=issues,
                    output_dir=output_dir,
                    file_path=file_path,
                    metrics=metrics
                )
        # Check output completeness
        check_output_completeness(input_file_paths, output_dir)
        
        logger.info("Review process completed successfully")
        
    except CodebaseIngestionError as e:
        logger.error(f"Failed to ingest codebase: {e}")
        raise AIReviewerError(f"Codebase ingestion failed: {e}")
    except Exception as e:
        logger.error(f"Review process failed: {e}", exc_info=True)
        raise


def run_analyze_command(args):
    """Execute the analyze command."""
    try:
        # Ingest codebase
        logger.info(f"Ingesting codebase from {args.input_path}")
        codebase_info = ingest_codebase(args.input_path)
        
        # Analyze files
        results = analyze_codebase_only(
            codebase_info,
            focus=args.focus
        )
        
        # Generate analysis report for each file
        os.makedirs(args.output_dir, exist_ok=True)
        for result in results:
            if result.get('analysis'):
                analysis = result.get('analysis', {})
                if not isinstance(analysis, dict):
                    analysis = {}
                report_path = os.path.join(args.output_dir, f"analysis_report_{result['file_info']['name']}.{args.format}")
                generate_report(
                    result['file_info']['content'],
                    result['file_info']['content'],  # No improvements in analyze mode
                    analysis.get('issues', []),
                    report_path,
                    result['file_info']['path'],
                    analysis.get('metrics')
                )
        
        print(f"\n✅ Analysis completed successfully!")
        print(f"📊 Reports generated in: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


def run_improve_command(args):
    """Execute the improve command."""
    try:
        # Ingest codebase
        logger.info(f"Ingesting codebase from {args.input_path}")
        codebase_info = ingest_codebase(args.input_path)
        
        # Load existing analysis if provided
        analysis_results = None
        if args.analysis_file:
            with open(args.analysis_file, 'r') as f:
                analysis_results = json.load(f)
        
        # Improve code
        results = improve_codebase_only(
            codebase_info,
            analysis_results,
            focus=args.focus
        )
        
        # Generate improved code for each file
        for result in results:
            if result.get('has_changes', False):
                analysis = result.get('analysis', {})
                if not isinstance(analysis, dict):
                    analysis = {}
                generate_output(
                    result['file_info']['content'],
                    result['improved_code'],
                    analysis.get('issues', []),
                    args.output_dir,
                    result['file_info']['path'],
                    analysis.get('metrics')
                )
        
        print(f"\n✅ Code improvement completed successfully!")
        print(f"📁 Improved code: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Improvement failed: {e}")
        sys.exit(1)


def run_summary_command(args):
    """Execute the summary command."""
    try:
        # Ingest codebase
        logger.info(f"Ingesting codebase from {args.input_path}")
        codebase_info = ingest_codebase(args.input_path)
        
        # Generate summary
        summary = generate_codebase_summary(codebase_info)
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(summary)
            print(f"\n✅ Summary generated: {args.output_file}")
        else:
            print(summary)
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        sys.exit(1)


def process_codebase(
    codebase_info: Dict[str, Any],
    requirements: Dict[str, str],
    agents: List,
    focus: str = 'all',
    max_files: Optional[int] = None,
    exclude_patterns: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Process the codebase and return results."""
    results = []
    files = codebase_info['files']
    
    # Apply filters
    if exclude_patterns:
        files = filter_files(files, exclude_patterns)
    
    if max_files:
        files = files[:max_files]
    
    total_files = len(files)
    logger.info(f"Processing {total_files} files")
    
    # Get configuration from environment
    enable_security = os.getenv('ENABLE_SECURITY_ANALYSIS', 'true').lower() == 'true'
    enable_performance = os.getenv('ENABLE_PERFORMANCE_ANALYSIS', 'true').lower() == 'true'
    enable_documentation = os.getenv('ENABLE_DOCUMENTATION_IMPROVEMENT', 'true').lower() == 'true'
    
    for i, file_info in enumerate(files, 1):
        logger.info(f"Processing file {i}/{total_files}: {file_info['name']}")
        
        try:
            # Analyze code
            logger.debug(f"Calling analyze_code for {file_info['name']}")
            analysis_result = analyze_code.invoke({
                'code': file_info['content'],
                'file_path': file_info['path']
            })
            logger.debug(f"analyze_code result type: {type(analysis_result)}")
            if not isinstance(analysis_result, dict):
                logger.warning(f"analysis_result is not a dict: {type(analysis_result)}")
                analysis_result = {}
            
            # Security analysis if needed
            security_result = None
            if (focus in ['security', 'all']) and enable_security:
                logger.debug(f"Calling analyze_security for {file_info['name']}")
                security_result = analyze_security.invoke({
                    'code': file_info['content'],
                    'file_path': file_info['path']
                })
                logger.debug(f"analyze_security result type: {type(security_result)}, value: {security_result}")
                if not isinstance(security_result, dict):
                    logger.warning(f"security_result is not a dict: {type(security_result)}")
                    security_result = {}
            
            # Performance analysis if needed
            performance_result = None
            if (focus in ['performance', 'all']) and enable_performance:
                logger.debug(f"Calling analyze_performance for {file_info['name']}")
                performance_result = analyze_performance.invoke({
                    'code': file_info['content'],
                    'file_path': file_info['path']
                })
                logger.debug(f"analyze_performance result type: {type(performance_result)}, value: {performance_result}")
                if not isinstance(performance_result, dict):
                    logger.warning(f"performance_result is not a dict: {type(performance_result)}")
                    performance_result = {}
            
            # Improve code
            improved_code = file_info['content']
            logger.debug(f"Checking if improvement needed for {file_info['name']}")
            logger.debug(f"analysis_result.get('issues'): {analysis_result.get('issues') if isinstance(analysis_result, dict) else 'N/A'}")
            logger.debug(f"security_result.get('security_issues'): {security_result.get('security_issues') if isinstance(security_result, dict) else 'N/A'}")
            
            if analysis_result.get('issues') or (security_result and security_result.get('security_issues')):
                logger.debug(f"Calling improve_code for {file_info['name']}")
                improve_result = improve_code.invoke({
                    'code': file_info['content'],
                    'issues': analysis_result.get('issues', []) + 
                             (security_result.get('security_issues', []) if security_result else []),
                    'file_path': file_info['path']
                })
                logger.debug(f"improve_code result type: {type(improve_result)}, value: {improve_result}")
                if isinstance(improve_result, dict) and 'improved_code' in improve_result:
                    improved_code = improve_result['improved_code']
                elif isinstance(improve_result, dict) and 'error' in improve_result:
                    logger.warning(f"Code improvement failed: {improve_result['error']}")
                else:
                    logger.warning(f"Unexpected result from improve_code: {improve_result}")
            
            # Improve documentation
            if (focus in ['readability', 'all']) and enable_documentation:
                logger.debug(f"Calling improve_documentation for {file_info['name']}")
                doc_result = improve_documentation.invoke({
                    'code': improved_code,
                    'file_path': file_info['path']
                })
                logger.debug(f"improve_documentation result type: {type(doc_result)}, value: {doc_result}")
                if isinstance(doc_result, dict) and 'improved_code' in doc_result:
                    improved_code = doc_result['improved_code']
                elif isinstance(doc_result, dict) and 'error' in doc_result:
                    logger.warning(f"Documentation improvement failed: {doc_result['error']}")
                else:
                    logger.warning(f"Unexpected result from improve_documentation: {doc_result}")
            
            # Compile results
            result = {
                'file_info': file_info,
                'analysis': analysis_result,
                'security': security_result,
                'performance': performance_result,
                'improved_code': improved_code,
                'has_changes': improved_code != file_info['content']
            }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {file_info['name']}: {e}", exc_info=True)
            # Add error result
            results.append({
                'file_info': file_info,
                'error': str(e),
                'improved_code': file_info['content'],
                'has_changes': False
            })
    
    return results


def analyze_codebase_only(
    codebase_info: Dict[str, Any],
    focus: str = 'all'
) -> List[Dict[str, Any]]:
    """Analyze codebase without making improvements."""
    results = []
    files = codebase_info['files']
    
    # Get configuration from environment
    enable_security = os.getenv('ENABLE_SECURITY_ANALYSIS', 'true').lower() == 'true'
    enable_performance = os.getenv('ENABLE_PERFORMANCE_ANALYSIS', 'true').lower() == 'true'
    
    for file_info in files:
        try:
            # Analyze code
            analysis_result = analyze_code.invoke({
                'code': file_info['content'],
                'file_path': file_info['path']
            })
            if not isinstance(analysis_result, dict):
                analysis_result = {}
            
            # Security analysis if needed
            security_result = None
            if (focus in ['security', 'all']) and enable_security:
                security_result = analyze_security.invoke({
                    'code': file_info['content'],
                    'file_path': file_info['path']
                })
                if not isinstance(security_result, dict):
                    security_result = {}
            
            # Performance analysis if needed
            performance_result = None
            if (focus in ['performance', 'all']) and enable_performance:
                performance_result = analyze_performance.invoke({
                    'code': file_info['content'],
                    'file_path': file_info['path']
                })
                if not isinstance(performance_result, dict):
                    performance_result = {}
            
            result = {
                'file_info': file_info,
                'analysis': analysis_result,
                'security': security_result,
                'performance': performance_result
            }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error analyzing {file_info['name']}: {e}")
            results.append({
                'file_info': file_info,
                'error': str(e)
            })
    
    return results


def improve_codebase_only(
    codebase_info: Dict[str, Any],
    analysis_results: Optional[List[Dict[str, Any]]],
    focus: List[str]
) -> List[Dict[str, Any]]:
    """Improve codebase based on existing analysis."""
    results = []
    files = codebase_info['files']
    
    # Get configuration from environment
    enable_documentation = os.getenv('ENABLE_DOCUMENTATION_IMPROVEMENT', 'true').lower() == 'true'
    
    for file_info in files:
        try:
            # Find existing analysis for this file
            existing_analysis = None
            if analysis_results:
                for analysis in analysis_results:
                    if analysis['file_info']['path'] == file_info['path']:
                        existing_analysis = analysis
                        break
            
            improved_code = file_info['content']
            
            # Apply improvements based on focus areas
            if 'security' in focus and existing_analysis and existing_analysis.get('security'):
                security_issues = existing_analysis['security'].get('security_issues', [])
                if security_issues:
                    improve_result = improve_code.invoke({
                        'code': improved_code,
                        'issues': security_issues,
                        'file_path': file_info['path']
                    })
                    if isinstance(improve_result, dict) and 'improved_code' in improve_result:
                        improved_code = improve_result['improved_code']
                    elif isinstance(improve_result, dict) and 'error' in improve_result:
                        logger.warning(f"Security improvement failed: {improve_result['error']}")
            
            if 'performance' in focus and existing_analysis and existing_analysis.get('performance'):
                performance_issues = existing_analysis['performance'].get('performance_issues', [])
                if performance_issues:
                    improve_result = improve_code.invoke({
                        'code': improved_code,
                        'issues': performance_issues,
                        'file_path': file_info['path']
                    })
                    if isinstance(improve_result, dict) and 'improved_code' in improve_result:
                        improved_code = improve_result['improved_code']
                    elif isinstance(improve_result, dict) and 'error' in improve_result:
                        logger.warning(f"Performance improvement failed: {improve_result['error']}")
            
            if 'readability' in focus and enable_documentation:
                doc_result = improve_documentation.invoke({
                    'code': improved_code,
                    'file_path': file_info['path']
                })
                if isinstance(doc_result, dict) and 'improved_code' in doc_result:
                    improved_code = doc_result['improved_code']
                elif isinstance(doc_result, dict) and 'error' in doc_result:
                    logger.warning(f"Documentation improvement failed: {doc_result['error']}")
            
            result = {
                'file_info': file_info,
                'improved_code': improved_code,
                'has_changes': improved_code != file_info['content']
            }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error improving {file_info['name']}: {e}")
            results.append({
                'file_info': file_info,
                'error': str(e),
                'improved_code': file_info['content'],
                'has_changes': False
            })
    
    return results


def generate_codebase_summary(codebase_info: Dict[str, Any]) -> str:
    """Generate a summary of the codebase."""
    files = codebase_info['files']
    
    # Count files by language
    language_counts = {}
    total_size = 0
    
    for file_info in files:
        language = file_info.get('language', 'Unknown')
        language_counts[language] = language_counts.get(language, 0) + 1
        total_size += file_info.get('size', 0)
    
    summary = f"""
# Codebase Summary

## Overview
- **Type**: {codebase_info['type']}
- **Total Files**: {len(files)}
- **Total Size**: {total_size:,} characters

## Languages
"""
    
    for language, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
        summary += f"- **{language}**: {count} files\n"
    
    summary += f"""
## Files
"""
    
    for file_info in files[:10]:  # Show first 10 files
        summary += f"- {file_info['relative_path']} ({file_info['language']})\n"
    
    if len(files) > 10:
        summary += f"- ... and {len(files) - 10} more files\n"
    
    return summary


def filter_files(files: List[Dict[str, Any]], exclude_patterns: List[str]) -> List[Dict[str, Any]]:
    """Filter files based on exclude patterns."""
    filtered_files = []
    
    for file_info in files:
        file_path = file_info['relative_path']
        
        # Check if file should be excluded
        excluded = False
        for pattern in exclude_patterns:
            if pattern in file_path:
                excluded = True
                break
        
        if not excluded:
            filtered_files.append(file_info)
    
    return filtered_files


if __name__ == '__main__':
    main() 