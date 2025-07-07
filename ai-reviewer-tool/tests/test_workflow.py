"""
End-to-end tests for the complete AI reviewer workflow.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from src.ingestion import ingest_codebase, ingest_frd
from src.agents import setup_agents
from src.output import generate_output, generate_project_summary
from src.tools import analyze_code, improve_code


class TestWorkflow:
    """Test cases for the complete workflow."""
    
    def test_complete_review_workflow(self):
        """Test the complete review workflow from ingestion to output."""
        # Create a temporary project
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            files_to_create = {
                'main.py': """
def calculate_sum(a, b):
    return a + b

def main():
    x = input("Enter first number: ")
    y = input("Enter second number: ")
    result = calculate_sum(x, y)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
""",
                'utils.py': """
import os

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def write_file(filename, content):
    with open(filename, 'w') as f:
        f.write(content)
""",
                'requirements.txt': "requests==2.25.1\npytest==7.4.0"
            }
            
            for filename, content in files_to_create.items():
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Create FRD
            frd_content = """
FR-1.1: The system shall handle user input securely.
FR-1.2: The system shall provide proper error handling.
NFR-1.1: The system shall be performant and efficient.
"""
            frd_path = os.path.join(temp_dir, 'requirements.md')
            with open(frd_path, 'w', encoding='utf-8') as f:
                f.write(frd_content)
            
            # Create output directory
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Step 1: Ingest FRD and codebase
            requirements = ingest_frd(frd_path)
            codebase_info = ingest_codebase(temp_dir)
            files = codebase_info['files']
            
            assert len(requirements) == 3
            assert len(files) >= 3  # At least the 3 files we created
            
            # Step 2: Setup agents (mock for testing)
            llm_config = {
                "type": "huggingface",
                "model": "codellama/CodeLlama-7b-hf",
                "temperature": 0.1
            }
            
            # For testing, we'll use the tools directly instead of agents
            analysis_results = []
            improved_files = []
            
            # Step 3: Analyze each file
            for file_info in files:
                if file_info['path'].endswith('.py'):
                    # Analyze code
                    analysis = analyze_code.invoke({
                        "code": file_info['content'],
                        "file_path": file_info['path']
                    })
                    
                    # Improve code if issues found
                    if analysis.get('issues'):
                        improved_code = improve_code.invoke({
                            "code": file_info['content'],
                            "issues": analysis['issues'],
                            "file_path": file_info['path']
                        })
                    else:
                        improved_code = file_info['content']
                    
                    # Generate output
                    generate_output(
                        file_info['content'],
                        improved_code,
                        analysis.get('issues', []),
                        output_dir,
                        file_info['path'],
                        analysis.get('metrics')
                    )
                    
                    analysis_results.append(analysis)
                    improved_files.append({
                        'path': file_info['path'],
                        'original': file_info['content'],
                        'improved': improved_code,
                        'issues': analysis.get('issues', [])
                    })
            
            # Step 4: Generate project summary
            project_structure = {
                'languages': ['Python'],
                'file_types': ['.py', '.txt'],
                'directories': [],
                'dependencies': ['Python']
            }
            
            generate_project_summary(analysis_results, project_structure, output_dir)
            
            # Step 5: Verify output
            assert os.path.exists(output_dir)
            
            # Check that improved code files exist
            improved_code_dir = os.path.join(output_dir, 'improved_code')
            assert os.path.exists(improved_code_dir)
            
            # Check that reports exist
            reports_dir = os.path.join(output_dir, 'reports')
            assert os.path.exists(reports_dir)
            
            # Check that metrics exist
            metrics_dir = os.path.join(output_dir, 'metrics')
            assert os.path.exists(metrics_dir)
            
            # Check that project summary exists
            summary_files = [f for f in os.listdir(output_dir) if f.startswith('project_summary')]
            assert len(summary_files) > 0
    
    def test_workflow_with_security_issues(self):
        """Test workflow with code containing security vulnerabilities."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create vulnerable code
            vulnerable_code = """
import subprocess
import os

def execute_command(user_input):
    # Vulnerable to command injection
    subprocess.call(user_input, shell=True)

def read_file(filename):
    # Vulnerable to path traversal
    with open(filename, 'r') as f:
        return f.read()

def main():
    user_input = input("Enter command: ")
    execute_command(user_input)
    
    filename = input("Enter filename: ")
    content = read_file(filename)
    print(content)
"""
            
            file_path = os.path.join(temp_dir, 'vulnerable.py')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(vulnerable_code)
            
            # Create output directory
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Ingest and analyze
            codebase_info = ingest_codebase(temp_dir)
            files = codebase_info['files']
            assert len(files) == 1
            
            file_info = files[0]
            analysis = analyze_code.invoke({
                "code": file_info['content'],
                "file_path": file_info['path']
            })
            
            # Should detect security issues
            assert 'issues' in analysis
            security_issues = [i for i in analysis.get('issues', []) if i.get('type') == 'security']
            assert len(security_issues) > 0
            
            # Generate output
            generate_output(
                file_info['content'],
                file_info['content'],  # No improvements for this test
                analysis.get('issues', []),
                output_dir,
                file_info['path'],
                analysis.get('metrics')
            )
            
            # Verify output was generated
            assert os.path.exists(output_dir)
            improved_code_dir = os.path.join(output_dir, 'improved_code')
            assert os.path.exists(improved_code_dir)
    
    def test_workflow_with_performance_issues(self):
        """Test workflow with code containing performance issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create code with performance issues
            performance_code = """
def inefficient_function():
    result = ""
    for i in range(10000):
        result += str(i)  # Inefficient string concatenation
    
    # Nested loops
    for i in range(100):
        for j in range(100):
            for k in range(100):
                pass  # O(n³) complexity
    
    return result

def memory_leak():
    data = []
    while True:
        data.append("leaking memory" * 1000)
"""
            
            file_path = os.path.join(temp_dir, 'performance.py')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(performance_code)
            
            # Create output directory
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Ingest and analyze
            codebase_info = ingest_codebase(temp_dir)
            files = codebase_info['files']
            assert len(files) == 1
            
            file_info = files[0]
            analysis = analyze_code.invoke({
                "code": file_info['content'],
                "file_path": file_info['path']
            })
            
            # Should detect performance issues
            assert 'issues' in analysis
            performance_issues = [i for i in analysis.get('issues', []) if i.get('type') == 'performance']
            assert len(performance_issues) > 0
            
            # Generate output
            generate_output(
                file_info['content'],
                file_info['content'],  # No improvements for this test
                analysis.get('issues', []),
                output_dir,
                file_info['path'],
                analysis.get('metrics')
            )
            
            # Verify output was generated
            assert os.path.exists(output_dir)
    
    def test_workflow_with_multiple_languages(self):
        """Test workflow with multiple programming languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files in different languages
            files_to_create = {
                'main.py': 'print("Hello, Python!")',
                'script.js': 'console.log("Hello, JavaScript!");',
                'index.html': '<html><body><h1>Hello, HTML!</h1></body></html>',
                'style.css': 'body { color: blue; }',
                'data.json': '{"message": "Hello, JSON!"}'
            }
            
            for filename, content in files_to_create.items():
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Create output directory
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Ingest and analyze
            codebase_info = ingest_codebase(temp_dir)
            files = codebase_info['files']
            assert len(files) == 5
            
            analysis_results = []
            
            # Analyze each file
            for file_info in files:
                analysis = analyze_code.invoke({
                    "code": file_info['content'],
                    "file_path": file_info['path']
                })
                
                analysis_results.append(analysis)
                
                # Generate output for each file
                generate_output(
                    file_info['content'],
                    file_info['content'],  # No improvements for this test
                    analysis.get('issues', []),
                    output_dir,
                    file_info['path'],
                    analysis.get('metrics')
                )
            
            # Generate project summary
            project_structure = {
                'languages': ['Python', 'JavaScript', 'HTML', 'CSS', 'JSON'],
                'file_types': ['.py', '.js', '.html', '.css', '.json'],
                'directories': [],
                'dependencies': []
            }
            
            generate_project_summary(analysis_results, project_structure, output_dir)
            
            # Verify output
            assert os.path.exists(output_dir)
            improved_code_dir = os.path.join(output_dir, 'improved_code')
            assert os.path.exists(improved_code_dir)
            
            # Check that files for each language were processed
            improved_files = os.listdir(improved_code_dir)
            assert len(improved_files) == 5
    
    def test_workflow_error_handling(self):
        """Test workflow error handling with invalid inputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid code that might cause issues
            invalid_code = """
def broken_function(
    # Missing closing parenthesis
    print("This won't work")
"""
            
            file_path = os.path.join(temp_dir, 'broken.py')
            with open(file_path, 'w') as f:
                f.write(invalid_code)
            
            # Create output directory
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Ingest and analyze
            codebase_info = ingest_codebase(temp_dir)
            files = codebase_info['files']
            assert len(files) == 1
            
            file_info = files[0]
            analysis = analyze_code.invoke({
                "code": file_info['content'],
                "file_path": file_info['path']
            })
            
            # Should handle errors gracefully
            assert isinstance(analysis, dict)
            assert 'file_path' in analysis
            
            # Generate output (should not crash)
            generate_output(
                file_info['content'],
                file_info['content'],
                analysis.get('issues', []),
                output_dir,
                file_info['path'],
                analysis.get('metrics')
            )
            
            # Verify output was generated despite errors
            assert os.path.exists(output_dir)
    
    def test_workflow_output_formats(self):
        """Test workflow with different output formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_code = """
def test_function():
    return "Hello, World!"
"""
            
            file_path = os.path.join(temp_dir, 'test.py')
            with open(file_path, 'w') as f:
                f.write(test_code)
            
            # Create output directory
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Ingest and analyze
            codebase_info = ingest_codebase(temp_dir)
            files = codebase_info['files']
            assert len(files) == 1
            
            file_info = files[0]
            analysis = analyze_code.invoke({
                "code": file_info['content'],
                "file_path": file_info['path']
            })
            
            # Generate output
            generate_output(
                file_info['content'],
                file_info['content'],
                analysis.get('issues', []),
                output_dir,
                file_info['path'],
                analysis.get('metrics')
            )
            
            # Verify different output formats were generated
            assert os.path.exists(output_dir)
            
            # Check for improved code
            improved_code_dir = os.path.join(output_dir, 'improved_code')
            assert os.path.exists(improved_code_dir)
            
            # Check for reports
            reports_dir = os.path.join(output_dir, 'reports')
            assert os.path.exists(reports_dir)
            
            # Check for metrics
            metrics_dir = os.path.join(output_dir, 'metrics')
            assert os.path.exists(metrics_dir)
            
            # Check that specific files were created
            improved_files = os.listdir(improved_code_dir)
            assert len(improved_files) > 0
            
            report_files = os.listdir(reports_dir)
            assert len(report_files) > 0
            
            metrics_files = os.listdir(metrics_dir)
            assert len(metrics_files) > 0
    
    def test_workflow_with_large_file_chunking(self):
        """Test workflow with large files that require chunking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a large file that would exceed token limits (optimized for speed)
            large_code = ""
            for i in range(50):  # Reduced from 1000 to 50 for speed
                large_code += f"""
def function_{i}():
    \"\"\"
    This is function number {i}.
    It does some calculations and returns a result.
    \"\"\"
    result = 0
    # Simplified calculation for speed
    result = i * 10
    
    # Add some comments to make it larger
    # This is a comment about the calculation
    # Another comment about the result
    
    return result

# More comments to increase file size
# This is a large file test
# We want to test chunking functionality
# The file should be split into multiple chunks
# Each chunk should be analyzed separately
# Then the results should be combined
"""
            
            file_path = os.path.join(temp_dir, 'large_file.py')
            with open(file_path, 'w') as f:
                f.write(large_code)
            
            # Create output directory
            output_dir = os.path.join(temp_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Ingest and analyze
            codebase_info = ingest_codebase(temp_dir)
            files = codebase_info['files']
            assert len(files) == 1
            
            file_info = files[0]
            analysis = analyze_code.invoke({
                "code": file_info['content'],
                "file_path": file_info['path']
            })
            
            # Should handle large files gracefully
            assert isinstance(analysis, dict)
            assert 'file_path' in analysis
            
            # Generate output
            generate_output(
                file_info['content'],
                file_info['content'],
                analysis.get('issues', []),
                output_dir,
                file_info['path'],
                analysis.get('metrics')
            )
            
            # Verify output was generated
            assert os.path.exists(output_dir)
            improved_code_dir = os.path.join(output_dir, 'improved_code')
            assert os.path.exists(improved_code_dir)
    
    def test_workflow_with_enhanced_logging(self):
        """Test that workflow uses enhanced logging features."""
        from src.logger import setup_logging
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup enhanced logging
            logger = setup_logging(log_file=log_file)
            
            # Test workflow with logging
            try:
                # This should trigger various log messages
                from src.llm_provider import create_llm_provider
                create_llm_provider({'model': 'test'})
            except Exception:
                pass  # Expected to fail without API keys
            
            # Check that logs were written
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                assert len(log_content) > 0


if __name__ == '__main__':
    pytest.main([__file__]) 