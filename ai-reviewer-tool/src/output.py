"""
Output module for generating improved code and reports.

This module handles the creation of improved code files and
comprehensive reports documenting all changes made.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def generate_output(original_code: str, improved_code: str, issues: List[Dict], 
                   output_dir: str, file_path: str = "", metrics: Dict = None) -> None:
    """
    Saves improved code and generates per-file report, metrics, and documentation summary.
    
    Args:
        original_code: Original code content.
        improved_code: Improved code content.
        issues: List of identified issues.
        output_dir: Output directory path.
        file_path: Path to the original file.
        metrics: Code quality metrics.
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create improved_code directory
        improved_code_dir = os.path.join(output_dir, 'improved_code')
        os.makedirs(improved_code_dir, exist_ok=True)
        
        # Create reports directory
        reports_dir = os.path.join(output_dir, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Create metrics directory
        metrics_dir = os.path.join(output_dir, 'metrics')
        os.makedirs(metrics_dir, exist_ok=True)
        
        # Save improved code
        if file_path:
            filename = os.path.basename(file_path)
            improved_file_path = os.path.join(improved_code_dir, filename)
            
            # Handle improved_code being a dict or string
            if isinstance(improved_code, dict):
                if 'improved_code' in improved_code:
                    improved_code_content = improved_code['improved_code']
                else:
                    improved_code_content = str(improved_code)
            else:
                improved_code_content = str(improved_code)
                
            with open(improved_file_path, 'w', encoding='utf-8') as f:
                f.write(improved_code_content)
                
            logger.info(f"Saved improved code to: {improved_file_path}")
        
        # Generate report
        report_path = os.path.join(reports_dir, f"review_report_{filename}.md")
        generate_report(original_code, improved_code, issues, report_path, file_path, metrics)
        
        # Save detailed JSON report
        json_report_path = os.path.join(reports_dir, f"detailed_report_{filename}.json")
        save_json_report(original_code, improved_code, issues, json_report_path, file_path, metrics)
        
        # Save metrics
        if metrics and isinstance(metrics, dict):
            metrics_file = os.path.join(metrics_dir, f"metrics_{filename}.json")
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2)
        else:
            # Create default metrics if none provided
            default_metrics = {
                'complexity_score': 5,
                'maintainability_score': 5,
                'security_score': 5,
                'performance_score': 5
            }
            metrics_file = os.path.join(metrics_dir, f"metrics_{filename}.json")
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(default_metrics, f, indent=2)
        
        # Per-file documentation summary
        generate_documentation_summary(improved_code_content, output_dir, file_path)
        
    except Exception as e:
        logger.error(f"Error generating output: {e}")
        raise


def generate_report(original_code: str, improved_code: str, issues: List[Dict], 
                   report_path: str, file_path: str = "", metrics: Dict = None) -> None:
    """
    Generate a comprehensive Markdown report.
    
    Args:
        original_code: Original code content.
        improved_code: Improved code content.
        issues: List of identified issues.
        report_path: Path to save the report.
        file_path: Path to the original file.
        metrics: Code quality metrics.
    """
    try:
        report_content = []
        
        # Header
        report_content.append("# Code Review Report")
        report_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_content.append(f"**File:** {file_path or 'Unknown'}")
        report_content.append("")
        
        # Executive Summary
        report_content.append("## Executive Summary")
        report_content.append("")
        
        if not isinstance(issues, list):
            issues = []
        total_issues = len(issues)
        critical_issues = len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'critical'])
        high_issues = len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'high'])
        medium_issues = len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'medium'])
        low_issues = len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'low'])
        
        report_content.append(f"- **Total Issues Found:** {total_issues}")
        report_content.append(f"- **Critical Issues:** {critical_issues}")
        report_content.append(f"- **High Priority Issues:** {high_issues}")
        report_content.append(f"- **Medium Priority Issues:** {medium_issues}")
        report_content.append(f"- **Low Priority Issues:** {low_issues}")
        report_content.append("")
        
        # Metrics Summary
        if metrics and isinstance(metrics, dict):
            report_content.append("## Code Quality Metrics")
            report_content.append("")
            report_content.append("| Metric | Score (1-10) | Description |")
            report_content.append("|--------|-------------|-------------|")
            report_content.append(f"| Complexity | {metrics.get('complexity_score', 'N/A')} | Code complexity assessment |")
            report_content.append(f"| Maintainability | {metrics.get('maintainability_score', 'N/A')} | Code maintainability score |")
            report_content.append(f"| Security | {metrics.get('security_score', 'N/A')} | Security assessment |")
            report_content.append(f"| Performance | {metrics.get('performance_score', 'N/A')} | Performance optimization score |")
            report_content.append("")
        
        # Issues Breakdown
        if issues:
            report_content.append("## Detailed Issues")
            report_content.append("")
            
            # Group issues by severity
            severity_groups = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': []
            }
            
            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                severity = issue.get('severity', 'medium')
                if severity in severity_groups:
                    severity_groups[severity].append(issue)
            
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity_groups[severity]:
                    report_content.append(f"### {severity.title()} Priority Issues")
                    report_content.append("")
                    
                    for i, issue in enumerate(severity_groups[severity], 1):
                        if not isinstance(issue, dict):
                            continue
                        report_content.append(f"#### Issue {i}")
                        report_content.append(f"- **Type:** {issue.get('type', 'Unknown')}")
                        report_content.append(f"- **Line:** {issue.get('line', 'Unknown')}")
                        report_content.append(f"- **Description:** {issue.get('description', 'No description')}")
                        
                        if issue.get('suggestion'):
                            report_content.append(f"- **Suggestion:** {issue['suggestion']}")
                        
                        if issue.get('code_snippet'):
                            report_content.append(f"- **Code:** `{issue['code_snippet']}`")
                        
                        report_content.append("")
        
        # Code Comparison
        report_content.append("## Code Comparison")
        report_content.append("")
        
        # Original code
        report_content.append("### Original Code")
        report_content.append("```")
        report_content.append(original_code)
        report_content.append("```")
        report_content.append("")
        
        # Improved code
        report_content.append("### Improved Code")
        report_content.append("```")
        # Handle improved_code being a dict or string
        if isinstance(improved_code, dict):
            if 'improved_code' in improved_code:
                improved_code_content = improved_code['improved_code']
            else:
                improved_code_content = str(improved_code)
        else:
            improved_code_content = str(improved_code)
        report_content.append(improved_code_content)
        report_content.append("```")
        report_content.append("")
        
        # Recommendations
        report_content.append("## Recommendations")
        report_content.append("")
        
        if critical_issues > 0:
            report_content.append("### Immediate Actions Required")
            report_content.append("- Address all critical issues immediately")
            report_content.append("- Review and fix high-priority security vulnerabilities")
            report_content.append("- Ensure code compiles and runs without errors")
            report_content.append("")
        
        if high_issues > 0:
            report_content.append("### High Priority Improvements")
            report_content.append("- Fix high-priority issues within the next sprint")
            report_content.append("- Implement security best practices")
            report_content.append("- Optimize performance bottlenecks")
            report_content.append("")
        
        if medium_issues > 0 or low_issues > 0:
            report_content.append("### Long-term Improvements")
            report_content.append("- Address medium and low-priority issues during refactoring")
            report_content.append("- Improve code documentation")
            report_content.append("- Implement automated testing")
            report_content.append("- Consider code review best practices")
            report_content.append("")
        
        # Write report to file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content))
            
        logger.info(f"Generated report: {report_path}")
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise


def save_json_report(original_code: str, improved_code: str, issues: List[Dict], 
                    report_path: str, file_path: str = "", metrics: Dict = None) -> None:
    """
    Save detailed report in JSON format.
    
    Args:
        original_code: Original code content.
        improved_code: Improved code content.
        issues: List of identified issues.
        report_path: Path to save the JSON report.
        file_path: Path to the original file.
        metrics: Code quality metrics.
    """
    try:
        if not isinstance(issues, list):
            issues = []
        # Handle improved_code being a dict or string
        if isinstance(improved_code, dict):
            if 'improved_code' in improved_code:
                improved_code_content = improved_code['improved_code']
            else:
                improved_code_content = str(improved_code)
        else:
            improved_code_content = str(improved_code)
            
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'file_path': file_path,
                'total_issues': len(issues),
                'issues_by_severity': {
                    'critical': len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'critical']),
                    'high': len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'high']),
                    'medium': len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'medium']),
                    'low': len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'low'])
                }
            },
            'metrics': metrics or {},
            'issues': issues,
            'code_comparison': {
                'original': original_code,
                'improved': improved_code_content,
                'changes_summary': _generate_changes_summary(original_code, improved_code_content)
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved JSON report: {report_path}")
        
    except Exception as e:
        logger.error(f"Error saving JSON report: {e}")
        raise


def generate_project_summary(analysis_results: List[Dict], project_structure: Dict, 
                           output_dir: str) -> None:
    """
    Generate a comprehensive project summary report.
    
    Args:
        analysis_results: List of analysis results from all files.
        project_structure: Project structure information.
        output_dir: Output directory path.
    """
    try:
        summary_path = os.path.join(output_dir, f"project_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        summary_content = []
        
        # Header
        summary_content.append("# Project Code Review Summary")
        summary_content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_content.append("")
        
        # Project Overview
        summary_content.append("## Project Overview")
        summary_content.append("")
        
        # Handle languages
        languages = project_structure.get('languages', [])
        if not languages or (len(languages) == 1 and languages[0] == 'unknown'):
            summary_content.append("- **Languages:** Not detected")
        else:
            summary_content.append(f"- **Languages:** {', '.join(languages)}")
        
        # Handle file types
        file_types = project_structure.get('file_types', [])
        if not file_types or (len(file_types) == 1 and file_types[0] == 'unknown'):
            summary_content.append("- **File Types:** Not detected")
        else:
            summary_content.append(f"- **File Types:** {', '.join(file_types)}")
        
        # Handle dependencies
        dependencies = project_structure.get('dependencies', [])
        if not dependencies:
            summary_content.append("- **Dependencies:** None detected")
        else:
            summary_content.append(f"- **Dependencies:** {', '.join(dependencies)}")
        
        summary_content.append(f"- **Files Analyzed:** {len(analysis_results)}")
        summary_content.append("")
        
        # Overall Statistics
        total_issues = 0
        critical_issues = 0
        high_issues = 0
        
        for result in analysis_results:
            if not isinstance(result, dict):
                continue
            # Check for issues in both direct 'issues' field and nested 'analysis.issues'
            issues = result.get('issues', [])
            if not issues and 'analysis' in result and isinstance(result['analysis'], dict):
                issues = result['analysis'].get('issues', [])
            
            if isinstance(issues, list):
                total_issues += len(issues)
                critical_issues += len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'critical'])
                high_issues += len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'high'])
        
        summary_content.append("## Overall Statistics")
        summary_content.append("")
        summary_content.append(f"- **Total Issues:** {total_issues}")
        summary_content.append(f"- **Critical Issues:** {critical_issues}")
        summary_content.append(f"- **High Priority Issues:** {high_issues}")
        
        if total_issues == 0:
            summary_content.append("")
            summary_content.append("🎉 **Excellent! No issues found in the analyzed code.**")
            summary_content.append("")
        else:
            summary_content.append("")
        
        # File-by-file breakdown
        summary_content.append("## File-by-File Analysis")
        summary_content.append("")
        
        # Count files with issues
        files_with_issues = 0
        for result in analysis_results:
            if not isinstance(result, dict):
                continue
            issues = result.get('issues', [])
            if not issues and 'analysis' in result and isinstance(result['analysis'], dict):
                issues = result['analysis'].get('issues', [])
            if isinstance(issues, list) and len(issues) > 0:
                files_with_issues += 1
        
        if files_with_issues == 0:
            summary_content.append("✅ **All analyzed files passed the review without issues.**")
            summary_content.append("")
        else:
            summary_content.append("| File | Issues | Critical | High | Medium | Low |")
            summary_content.append("|------|--------|----------|------|--------|-----|")
            
            for result in analysis_results:
                if not isinstance(result, dict):
                    continue
                file_path = result.get('file_path', 'Unknown')
                if not file_path and 'file_info' in result and isinstance(result['file_info'], dict):
                    file_path = result['file_info'].get('path', 'Unknown')
                
                # Check for issues in both direct 'issues' field and nested 'analysis.issues'
                issues = result.get('issues', [])
                if not issues and 'analysis' in result and isinstance(result['analysis'], dict):
                    issues = result['analysis'].get('issues', [])
                
                if not isinstance(issues, list):
                    issues = []
                critical = len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'critical'])
                high = len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'high'])
                medium = len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'medium'])
                low = len([i for i in issues if isinstance(i, dict) and i.get('severity') == 'low'])
                
                summary_content.append(f"| {file_path} | {len(issues)} | {critical} | {high} | {medium} | {low} |")
            
            summary_content.append("")
        
        # Top Issues
        summary_content.append("## Top Issues by Frequency")
        summary_content.append("")
        
        issue_types = {}
        for result in analysis_results:
            if not isinstance(result, dict):
                continue
            # Check for issues in both direct 'issues' field and nested 'analysis.issues'
            issues = result.get('issues', [])
            if not issues and 'analysis' in result and isinstance(result['analysis'], dict):
                issues = result['analysis'].get('issues', [])
            
            if not isinstance(issues, list):
                continue
            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                issue_type = issue.get('type', 'Unknown')
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        if not issue_types:
            summary_content.append("✅ **No issues found to report.**")
            summary_content.append("")
        else:
            sorted_issues = sorted(issue_types.items(), key=lambda x: x[1], reverse=True)
            
            for issue_type, count in sorted_issues[:10]:
                summary_content.append(f"- **{issue_type}:** {count} occurrences")
            
            summary_content.append("")
        
        # Recommendations
        summary_content.append("## Project-wide Recommendations")
        summary_content.append("")
        
        if critical_issues > 0:
            summary_content.append("### Critical Actions")
            summary_content.append("- Address all critical issues immediately")
            summary_content.append("- Review security vulnerabilities")
            summary_content.append("- Fix compilation errors")
            summary_content.append("")
        
        if high_issues > 0:
            summary_content.append("### High Priority")
            summary_content.append("- Implement security best practices")
            summary_content.append("- Optimize performance bottlenecks")
            summary_content.append("- Improve code quality")
            summary_content.append("")
        
        summary_content.append("### General Improvements")
        summary_content.append("- Implement automated testing")
        summary_content.append("- Add comprehensive documentation")
        summary_content.append("- Establish code review processes")
        summary_content.append("- Use static analysis tools")
        summary_content.append("")
        
        # Write summary to file
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_content))
            
        logger.info(f"Generated project summary: {summary_path}")
        
    except Exception as e:
        logger.error(f"Error generating project summary: {e}")
        raise


def create_output_structure(original_path: str, output_dir: str) -> str:
    """
    Create the output directory structure mirroring the original project.
    
    Args:
        original_path: Path to the original project.
        output_dir: Base output directory.
        
    Returns:
        Path to the improved code directory.
    """
    try:
        improved_dir = os.path.join(output_dir, "improved_code")
        os.makedirs(improved_dir, exist_ok=True)
        
        # Create reports directory
        reports_dir = os.path.join(output_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Create metrics directory
        metrics_dir = os.path.join(output_dir, "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        
        logger.info(f"Created output structure: {output_dir}")
        return improved_dir
        
    except Exception as e:
        logger.error(f"Error creating output structure: {e}")
        raise


def save_metrics(metrics: Dict[str, Any], output_dir: str, file_path: str = "") -> None:
    """
    Save code quality metrics to a file.
    
    Args:
        metrics: Code quality metrics.
        output_dir: Output directory.
        file_path: Path to the analyzed file.
    """
    try:
        metrics_file = os.path.join(output_dir, "metrics", f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'file_path': file_path,
            'metrics': metrics
        }
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved metrics: {metrics_file}")
        
    except Exception as e:
        logger.error(f"Error saving metrics: {e}")
        raise


def _generate_changes_summary(original_code: str, improved_code: str) -> Dict[str, Any]:
    """
    Generate a summary of changes between original and improved code.
    
    Args:
        original_code: Original code content.
        improved_code: Improved code content.
        
    Returns:
        Dictionary containing change summary.
    """
    try:
        original_lines = original_code.split('\n')
        improved_lines = improved_code.split('\n')
        
        changes = {
            'lines_added': len(improved_lines) - len(original_lines),
            'characters_added': len(improved_code) - len(original_code),
            'files_modified': 1 if original_code != improved_code else 0
        }
        
        return changes
        
    except Exception as e:
        logger.warning(f"Error generating changes summary: {e}")
        return {
            'lines_added': 0,
            'characters_added': 0,
            'files_modified': 0
        }


def create_before_after_comparison(original_code: str, improved_code: str, 
                                 output_dir: str, file_path: str = "") -> None:
    """
    Create a side-by-side comparison of original and improved code.
    
    Args:
        original_code: Original code content.
        improved_code: Improved code content.
        output_dir: Output directory.
        file_path: Path to the file being compared.
    """
    try:
        comparison_path = os.path.join(output_dir, f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        original_lines = original_code.split('\n')
        improved_lines = improved_code.split('\n')
        
        html_content = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<title>Code Comparison</title>',
            '<style>',
            'body { font-family: monospace; margin: 20px; }',
            '.comparison { display: flex; }',
            '.column { flex: 1; margin: 0 10px; }',
            '.header { background-color: #f0f0f0; padding: 10px; font-weight: bold; }',
            '.code { background-color: #f8f8f8; padding: 10px; white-space: pre-wrap; }',
            '</style>',
            '</head>',
            '<body>',
            f'<h1>Code Comparison: {file_path}</h1>',
            '<div class="comparison">',
            '<div class="column">',
            '<div class="header">Original Code</div>',
            '<div class="code">',
            original_code.replace('<', '&lt;').replace('>', '&gt;'),
            '</div>',
            '</div>',
            '<div class="column">',
            '<div class="header">Improved Code</div>',
            '<div class="code">',
            improved_code.replace('<', '&lt;').replace('>', '&gt;'),
            '</div>',
            '</div>',
            '</div>',
            '</body>',
            '</html>'
        ]
        
        with open(comparison_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
            
        logger.info(f"Created comparison: {comparison_path}")
        
    except Exception as e:
        logger.error(f"Error creating comparison: {e}")
        raise


def generate_documentation_summary(improved_code: str, output_dir: str, file_path: str = "") -> None:
    """
    Generate a documentation summary file for the improved code.
    Args:
        improved_code: Code with improved documentation.
        output_dir: Output directory path.
        file_path: Path to the original file.
    """
    try:
        docs_dir = os.path.join(output_dir, 'docs')
        os.makedirs(docs_dir, exist_ok=True)
        filename = os.path.basename(file_path)
        doc_file = os.path.join(docs_dir, f"{filename}.md")
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(f"# Documentation for {filename}\n\n")
            f.write("## Improved Code with Documentation\n\n")
            f.write('```\n')
            f.write(improved_code)
            f.write('\n```\n')
        logger.info(f"Generated documentation summary: {doc_file}")
    except Exception as e:
        logger.error(f"Error generating documentation summary: {e}")
        raise


def check_output_completeness(input_files: list, output_dir: str) -> None:
    """
    Check that all expected output files are created for every input code file.
    Log a warning if any are missing.
    Args:
        input_files: List of input file paths.
        output_dir: Output directory path.
    """
    improved_code_dir = os.path.join(output_dir, 'improved_code')
    reports_dir = os.path.join(output_dir, 'reports')
    metrics_dir = os.path.join(output_dir, 'metrics')
    docs_dir = os.path.join(output_dir, 'docs')
    for file_path in input_files:
        filename = os.path.basename(file_path)
        improved_file = os.path.join(improved_code_dir, filename)
        report_file = os.path.join(reports_dir, f"review_report_{filename}.md")
        json_report_file = os.path.join(reports_dir, f"detailed_report_{filename}.json")
        metrics_file = os.path.join(metrics_dir, f"metrics_{filename}.json")
        doc_file = os.path.join(docs_dir, f"{filename}.md")
        missing = []
        if not os.path.exists(improved_file):
            missing.append('improved_code')
        if not os.path.exists(report_file):
            missing.append('report')
        if not os.path.exists(json_report_file):
            missing.append('json_report')
        if not os.path.exists(metrics_file):
            missing.append('metrics')
        if not os.path.exists(doc_file):
            missing.append('documentation')
        if missing:
            logger.warning(f"Missing output for {filename}: {', '.join(missing)}") 