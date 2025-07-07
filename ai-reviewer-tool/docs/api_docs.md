# API Documentation

## AI Code Review Tool

This document provides comprehensive API documentation for the AI Code Review Tool, including both command-line interface (CLI) and programmatic SDK usage.

### Table of Contents

1. [Command Line Interface](#command-line-interface)
2. [Programmatic SDK](#programmatic-sdk)
3. [Configuration](#configuration)
4. [Error Handling](#error-handling)
5. [Examples](#examples)

---

## Command Line Interface

### Overview

The CLI provides a comprehensive interface for code review operations with support for various input formats, analysis types, and output formats.

### Basic Usage

```bash
python ai_reviewer.py <command> [options] <codebase_path>
```

### Commands

#### 1. Review Command

Performs a comprehensive code review with improvement generation.

```bash
python ai_reviewer.py review <codebase_path> [options]
```

**Arguments:**
- `codebase_path`: Path to the codebase (file, directory, ZIP file, or Git repository URL)

**Options:**
- `--frd <path>`: Path to functional requirements document
- `--output-dir <path>`: Output directory for improved code (default: `./output`)
- `--focus <areas>`: Focus areas for review (`security`, `performance`, `readability`, `maintainability`, `all`) (default: `all`)
- `--llm-model <name>`: LLM model to use (default: `bigcode/starcoder`)
- `--format <format>`: Report format (`markdown`, `json`, `html`) (default: `markdown`)
- `--exclude <patterns>`: Files or directories to exclude (multiple)
- `--max-files <number>`: Maximum number of files to process (default: 5)

**Examples:**
```bash
# Basic review
python src/cli.py review ./my-project

# Review with requirements
python src/cli.py review ./my-project --frd ./requirements.md

# Review with specific focus
python src/cli.py review ./my-project --focus security,performance

# Review with exclusions
python src/cli.py review ./my-project --exclude node_modules __pycache__

# Review Git repository
python src/cli.py review https://github.com/user/repo
```

#### 2. Analyze Command

Performs code analysis without generating improvements.

```bash
python ai_reviewer.py analyze <codebase_path> [options]
```

**Arguments:**
- `codebase_path`: Path to the codebase (file, directory, ZIP file, or Git repository URL)

**Options:**
- `--output-dir <path>`: Output directory for analysis results (default: `./analysis`)
- `--focus <areas>`: Focus areas for analysis (`security`, `performance`, `readability`, `maintainability`, `all`) (default: `all`)
- `--format <format>`: Report format (`markdown`, `json`, `html`) (default: `markdown`)

**Examples:**
```bash
# Basic analysis
python src/cli.py analyze ./my-project

# Security-focused analysis
python src/cli.py analyze ./my-project --focus security --format html

# Performance analysis
python src/cli.py analyze ./my-project --focus performance --format json
```

#### 3. Improve Command

Improves code based on analysis without full review.

```bash
python ai_reviewer.py improve <codebase_path> [options]
```

**Arguments:**
- `codebase_path`: Path to the codebase (file, directory, ZIP file, or Git repository URL)

**Options:**
- `--output-dir <path>`: Output directory for improved code (default: `./improved_code`)
- `--focus <areas>`: Focus areas for improvement (`security`, `performance`, `readability`, `maintainability`) (default: all areas)
- `--analysis-file <path>`: Path to existing analysis file to use

**Examples:**
```bash
# Security improvements
python src/cli.py improve ./my-project --focus security

# Performance and readability improvements
python src/cli.py improve ./my-project --focus performance readability

# Use existing analysis
python src/cli.py improve ./my-project --analysis-file ./analysis/results.json
```

#### 4. Summary Command

Generates project summary without detailed analysis.

```bash
python ai_reviewer.py summary <codebase_path> [options]
```

**Arguments:**
- `codebase_path`: Path to the codebase (file, directory, ZIP file, or Git repository URL)

**Options:**
- `--output-file <path>`: Output file for summary (default: stdout)
- `--format <format>`: Summary format (`markdown`, `json`, `html`) (default: `markdown`)

**Examples:**
```bash
# Generate summary
python src/cli.py summary ./my-project

# HTML summary to file
python src/cli.py summary ./my-project --format html --output-file summary.html
```

### Global Options

All commands support these global options:

- `--verbose, -v`: Enable verbose logging
- `--config <path>`: Configuration file path
- `--help, -h`: Show help message

---

## Programmatic SDK

### Overview

The SDK provides a programmatic interface for integrating code review functionality into applications.

### Core Modules

#### 1. Ingestion Module

```python
from src.ingestion import ingest_frd, ingest_codebase

# Ingest functional requirements
requirements = ingest_frd("requirements.md")

# Ingest codebase
codebase_info = ingest_codebase("./my-project")
```

**Functions:**

##### `ingest_frd(frd_path: str) -> Dict[str, str]`

Parses a functional requirements document.

**Parameters:**
- `frd_path`: Path to the FRD file

**Returns:**
- Dictionary mapping requirement IDs to descriptions

**Raises:**
- `FileNotFoundError`: If FRD file doesn't exist
- `ValueError`: If FRD format is invalid

##### `ingest_codebase(codebase_path: str) -> Dict[str, Any]`

Ingests a codebase from various formats.

**Parameters:**
- `codebase_path`: Path to codebase (file, directory, ZIP, or Git repo URL)

**Returns:**
- Dictionary containing codebase information:
  ```python
  {
      'files': List[Dict[str, Any]],  # File information
      'project_info': Dict[str, Any], # Project metadata
      'structure': Dict[str, Any]     # Project structure
  }
  ```

**Raises:**
- `FileNotFoundError`: If codebase path doesn't exist
- `ValueError`: If codebase format is unsupported

#### 2. Tools Module

```python
from src.tools import analyze_code, improve_code, analyze_security, analyze_performance

# Analyze code
result = analyze_code.invoke({
    'code': code_content,
    'file_path': 'example.py'
})

# Improve code
improved = improve_code.invoke({
    'code': code_content,
    'issues': result.get('issues', []),
    'file_path': 'example.py'
})
```

**Available Tools:**

##### `analyze_code(code: str, file_path: str = "") -> Dict[str, Any]`

Performs comprehensive code analysis.

**Parameters:**
- `code`: Code content to analyze
- `file_path`: Path to the file (for context)

**Returns:**
- Dictionary containing analysis results:
  ```python
  {
      'issues': List[Dict],      # Found issues
      'metrics': Dict,           # Code quality metrics
      'file_path': str,          # File path
      'analysis_type': str       # Analysis method used
  }
  ```

##### `improve_code(code: str, issues: List[Dict], file_path: str = "") -> Dict[str, Any]`

Improves code based on identified issues.

**Parameters:**
- `code`: Original code content
- `issues`: List of issues from analysis
- `file_path`: Path to the file (for context)

**Returns:**
- Dictionary containing improvement results:
  ```python
  {
      'improved_code': str,      # Improved code
      'changes': List[Dict],     # Changes made
      'file_path': str,          # File path
      'improvement_type': str    # Type of improvement
  }
  ```

##### `analyze_security(code: str, file_path: str = "") -> Dict[str, Any]`

Performs security analysis.

**Parameters:**
- `code`: Code content to analyze
- `file_path`: Path to the file (for context)

**Returns:**
- Dictionary containing security analysis results

##### `analyze_performance(code: str, file_path: str = "") -> Dict[str, Any]`

Performs performance analysis.

**Parameters:**
- `code`: Code content to analyze
- `file_path`: Path to the file (for context)

**Returns:**
- Dictionary containing performance analysis results

#### 3. Output Module

```python
from src.output import generate_output, generate_report, generate_project_summary

# Generate output
generate_output(results, output_dir)

# Generate report
generate_report(results, output_dir, format='markdown')

# Generate summary
summary = generate_project_summary(codebase_info)
```

**Functions:**

##### `generate_output(results: List[Dict[str, Any]], output_dir: str) -> None`

Generates improved code files and reports.

**Parameters:**
- `results`: List of analysis/improvement results
- `output_dir`: Directory to save output

##### `generate_report(results: List[Dict[str, Any]], output_dir: str, format: str = 'markdown') -> str`

Generates detailed analysis reports.

**Parameters:**
- `results`: List of analysis results
- `output_dir`: Directory to save reports
- `format`: Report format (`markdown`, `json`, `html`)

**Returns:**
- Path to generated report file

##### `generate_project_summary(codebase_info: Dict[str, Any]) -> str`

Generates project summary.

**Parameters:**
- `codebase_info`: Codebase information from ingestion

**Returns:**
- Project summary as string

#### 4. Agents Module

```python
from src.agents import setup_agents, run_review

# Setup agents
agents = setup_agents(llm_config)

# Run review
results = run_review(codebase_info, requirements, agents, focus='all')
```

**Functions:**

##### `setup_agents(llm_config: Dict[str, Any]) -> List[Agent]`

Sets up AI agents for code review.

**Parameters:**
- `llm_config`: LLM configuration dictionary

**Returns:**
- List of configured agents

##### `run_review(codebase_info: Dict[str, Any], requirements: Dict[str, str], agents: List[Agent], focus: str = 'all') -> List[Dict[str, Any]]`

Runs comprehensive code review.

**Parameters:**
- `codebase_info`: Codebase information
- `requirements`: Functional requirements
- `agents`: List of agents
- `focus`: Focus areas for review

**Returns:**
- List of review results

---

## Configuration

### Environment Variables

The tool uses environment variables for configuration. Create a `.env` file in the project root:

```bash
# Required: At least one API key
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key

# LLM Configuration
DEFAULT_LLM_MODEL=bigcode/starcoder
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2048
LLM_TIMEOUT=30

# Analysis Configuration
MAX_FILE_SIZE_MB=10
ENABLE_SECURITY_ANALYSIS=true
ENABLE_PERFORMANCE_ANALYSIS=true
ENABLE_MAINTAINABILITY_ANALYSIS=true
ENABLE_READABILITY_ANALYSIS=true

# Output Configuration
DEFAULT_OUTPUT_DIR=./output
DEFAULT_REPORT_FORMAT=markdown
CREATE_BACKUP=true
INCLUDE_METRICS=true

# Performance Configuration
MAX_PARALLEL_FILES=5
CACHE_ENABLED=true
CACHE_DIR=./cache

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/app.log
LOG_JSON_FORMAT=true
```

### Configuration File

You can also use a JSON configuration file:

```json
{
  "llm": {
    "model": "bigcode/starcoder",
    "temperature": 0.1,
    "max_tokens": 2048
  },
  "analysis": {
    "max_file_size_mb": 10,
    "enable_security": true,
    "enable_performance": true
  },
  "output": {
    "default_format": "markdown",
    "output_dir": "./output"
  }
}
```

---

## Error Handling

### Exception Types

The tool defines several custom exception types:

```python
from src.exceptions import (
    AIReviewerError,
    ValidationError,
    ConfigurationError,
    OutputError,
    LLMError,
    CodebaseIngestionError
)
```

### Error Handling Example

```python
from src.exceptions import AIReviewerError, ValidationError
from src.ingestion import ingest_codebase

try:
    codebase_info = ingest_codebase("./my-project")
except ValidationError as e:
    print(f"Validation error: {e}")
except AIReviewerError as e:
    print(f"AI Reviewer error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Examples

### Complete Code Review Workflow

```python
from src.ingestion import ingest_frd, ingest_codebase
from src.agents import setup_agents, run_review
from src.output import generate_output
from src.exceptions import AIReviewerError

def review_codebase(project_path: str, requirements_path: str = None):
    try:
        # Ingest requirements
        requirements = {}
        if requirements_path:
            requirements = ingest_frd(requirements_path)
        
        # Ingest codebase
        codebase_info = ingest_codebase(project_path)
        
        # Setup agents
        llm_config = {'model': 'bigcode/starcoder', 'temperature': 0.1}
        agents = setup_agents(llm_config)
        
        # Run review
        results = run_review(codebase_info, requirements, agents, focus='all')
        
        # Generate output
        generate_output(results, './output')
        
        print("Code review completed successfully!")
        
    except AIReviewerError as e:
        print(f"Review failed: {e}")

# Usage
review_codebase('./my-project', './requirements.md')
```

### Custom Analysis Workflow

```python
from src.ingestion import ingest_codebase
from src.tools import analyze_code, analyze_security
from src.output import generate_report

def analyze_security_only(project_path: str):
    # Ingest codebase
    codebase_info = ingest_codebase(project_path)
    
    results = []
    
    # Analyze each file
    for file_info in codebase_info['files']:
        # Security analysis
        security_result = analyze_security.invoke({
            'code': file_info['content'],
            'file_path': file_info['path']
        })
        
        results.append({
            'file_info': file_info,
            'security': security_result
        })
    
    # Generate security report
    generate_report(results, './security_analysis', format='html')
    
    print("Security analysis completed!")

# Usage
analyze_security_only('./my-project')
```

### Batch Processing

```python
import os
from src.ingestion import ingest_codebase
from src.tools import analyze_code

def batch_analyze_projects(projects_dir: str):
    results = {}
    
    for project_name in os.listdir(projects_dir):
        project_path = os.path.join(projects_dir, project_name)
        
        if os.path.isdir(project_path):
            try:
                # Ingest project
                codebase_info = ingest_codebase(project_path)
                
                project_results = []
                
                # Analyze each file
                for file_info in codebase_info['files']:
                    result = analyze_code.invoke({
                        'code': file_info['content'],
                        'file_path': file_info['path']
                    })
                    project_results.append(result)
                
                results[project_name] = project_results
                
            except Exception as e:
                print(f"Error analyzing {project_name}: {e}")
    
    return results

# Usage
results = batch_analyze_projects('./projects')
```

## Output Structure

After running a review or analysis, the output directory will contain:
- `improved_code/`: Improved code files (one per input file)
- `reports/`: Per-file Markdown and JSON reports
- `metrics/`: Per-file metrics files
- `docs/`: Per-file documentation summaries (Markdown)
- `project_summary_*.md`: Overall project summary

The tool checks for output completeness and logs warnings if any expected files are missing.

## Prompt Customization

You can customize any prompt template by:
- Setting the environment variable `PROMPT_TEMPLATE_<TEMPLATE_NAME>`
- Adding a file in `configs/prompts/<template_name>.txt`
- Adding to `configs/prompts/prompts.json`

See `src/prompts/registry.py` for details on the prompt registry system.

This documentation provides a comprehensive guide to using the AI Code Review Tool programmatically and via the command line interface. 