# AI Code Review Tool

A production-grade, cross-platform AI-powered code review tool that analyzes codebases and generates improved versions based on functional requirements.

## Overview

The AI Code Review Tool is a comprehensive tool that:
- Accepts complete codebases in various formats (single file, ZIP, folder, Git repo)
- Performs comprehensive analysis for syntax errors, security vulnerabilities, and performance issues
- Generates improved code versions with detailed reports
- Supports multiple programming languages
- Provides both CLI and programmatic interfaces
- Uses multiple LLM providers with robust fallback systems

## Features

- **Multi-format Input Support**: Accepts single files, directories, ZIP archives, and Git repositories
- **Multi-language Support**: Python, JavaScript, TypeScript, Java, C++, HTML, CSS, and more
- **Multi-Provider LLM Support**: Robust fallback system supporting HuggingFace, Google Gemini, OpenAI, and Groq
- **AI-Powered Code Review**: Uses the best available LLM provider with automatic fallback
- **Multi-Agent Architecture**: Specialized agents for different aspects of code review
- **Comprehensive Analysis**: Syntax, security, performance, maintainability, and best practices
- **AI-Powered Improvements**: Uses advanced LLMs for code optimization
- **Detailed Reporting**: HTML, Markdown, and JSON report formats
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Configurable**: Custom rulesets and improvement priorities
- **Environment Configuration**: Easy setup with environment variables
- **Production-Ready Fallbacks**: Graceful degradation when LLM providers are unavailable
- **Configurable Output**: Markdown, JSON, and HTML report formats
- **Diagnostic Tools**: Built-in API key testing and troubleshooting

## LLM Provider Support

The tool automatically tries multiple LLM providers in order of preference:

1. **HuggingFace** (`bigcode/starcoder` - recommended for code analysis)
2. **Google Gemini** (`gemini-2.5-flash-preview-05-20`, `gemini-1.5-flash`, `gemini-pro`)
3. **OpenAI** (`gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`)
4. **Groq** (`llama3-70b-8192`, `llama3-8b-8192`, `mixtral-8x7b-32768`)
5. **Fallback Mode** (static analysis when all LLMs fail)

## Installation

### Prerequisites

- **Python 3.9 or higher** (required)
- **Git** (optional, for Git repository support)

### Setup

#### Option 1: Automated Setup (Recommended)

**Windows:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\setup.ps1
```

**Unix/Linux/macOS:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

#### Option 2: Manual Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-reviewer-tool
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create necessary directories**:
   ```bash
   mkdir logs
   mkdir output
   mkdir cache
   mkdir tests/output
   ```

5. **Setup environment variables**:
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env and add your API keys
   # Required: At least one of these API keys
   HUGGINGFACEHUB_API_TOKEN=your_huggingface_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Verification

After setup, verify the installation:

```bash
# Test the CLI
python src/cli.py --help

# Run tests
pytest tests/ -v

# Test with a simple file
echo "print('Hello, World!')" > test.py
python src/cli.py review test.py
```

## Usage

### Command Line Interface

#### Review a Codebase
```bash
# Review a single file
python ai_reviewer.py review myfile.py

# Review a directory
python ai_reviewer.py review ./my-project

# Review a ZIP file
python ai_reviewer.py review project.zip

# Review a Git repository
python ai_reviewer.py review https://github.com/user/repo

# Review with functional requirements
python ai_reviewer.py review ./my-project --frd ./requirements.md

# Review with specific focus areas
python ai_reviewer.py review ./my-project --focus security,performance

# Review with custom output directory
python ai_reviewer.py review ./my-project --output-dir ./review_results

# Review with exclusions
python ai_reviewer.py review ./my-project --exclude tests/ docs/
```

#### Analyze Code (without improvement)
```bash
# Basic analysis
python ai_reviewer.py analyze ./my-project

# Analysis with security focus
python ai_reviewer.py analyze ./my-project --focus security

# Analysis with performance focus
python ai_reviewer.py analyze ./my-project --focus performance --format html
```

#### Improve Code
```bash
# Improve with security focus
python ai_reviewer.py improve ./my-project --focus security

# Improve with performance focus
python ai_reviewer.py improve ./my-project --focus performance,readability
```

#### Generate Project Summary
```bash
# Generate summary
python ai_reviewer.py summary ./my-project

# Summary in different format
python ai_reviewer.py summary ./my-project --format html
```

### Programmatic Interface

```python
from src.ingestion import ingest_codebase, ingest_frd
from src.tools import analyze_code, improve_code, analyze_security, analyze_performance
from src.output import generate_improved_code, generate_report

# Load requirements and codebase
requirements = ingest_frd("requirements.md")
codebase_info = ingest_codebase("./my-project")

# Analyze code using invoke()
for file_info in codebase_info['files']:
    # Analyze code
    analysis_result = analyze_code.invoke({
        'code': file_info['content'],
        'file_path': file_info['path']
    })
    
    # Security analysis
    security_result = analyze_security.invoke({
        'code': file_info['content'],
        'file_path': file_info['path']
    })
    
    # Performance analysis
    performance_result = analyze_performance.invoke({
        'code': file_info['content'],
        'file_path': file_info['path']
    })
    
    # Improve code
    improved_code = improve_code.invoke({
        'code': file_info['content'],
        'issues': analysis_result.get('issues', []),
        'file_path': file_info['path']
    })
    
    # Generate output
    generate_improved_code([{
        'file_info': file_info,
        'analysis': analysis_result,
        'security': security_result,
        'performance': performance_result,
        'improved_code': improved_code
    }], "./output")
```

### Using Different Input Formats

```python
# Single file
codebase_info = ingest_codebase("myfile.py")

# Directory
codebase_info = ingest_codebase("./my-project/")

# ZIP file
codebase_info = ingest_codebase("project.zip")

# Git repository
codebase_info = ingest_codebase("https://github.com/user/repo")
```

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure your settings:

```bash
# Required: At least one of these API keys
HUGGINGFACEHUB_API_TOKEN=your_huggingface_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Optional: Google Cloud Platform
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
GCP_PROJECT_ID=your_project_id

# Performance settings
MAX_PARALLEL_FILES=5
LLM_TIMEOUT=30

# Analysis settings
ENABLE_SECURITY_ANALYSIS=true
ENABLE_PERFORMANCE_ANALYSIS=true
ENABLE_DOCUMENTATION_IMPROVEMENT=true
```

### Logging Configuration

The tool uses structured JSON logging. Configure logging in `configs/logging.json`:

```json
{
  "version": 1,
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "json"
    }
  }
}
```

### LLM Configuration

The tool uses Hugging Face models by default. Configure in your `.env` file:

```bash
# Default model
DEFAULT_LLM_MODEL=bigcode/starcoder

# Alternative models
# - codellama/CodeLlama-7b-hf
# - microsoft/DialoGPT-medium
# - gpt2
# - facebook/opt-350m
# - bigscience/bloom-560m
```

## Output Structure

After running a review, the output directory will contain:
- `improved_code/`: Improved code files (one per input file)
- `reports/`: Per-file Markdown and JSON reports
- `metrics/`: Per-file metrics files
- `docs/`: Per-file documentation summaries (Markdown)

The tool checks for output completeness and logs warnings if any expected files are missing.

## Prompt Customization & Registry

- All prompt templates are managed by a centralized prompt registry (`src/prompts/registry.py`).
- You can override any prompt template by:
  - Setting the environment variable `PROMPT_TEMPLATE_<TEMPLATE_NAME>`
  - Adding a file in `configs/prompts/<template_name>.txt`
  - Adding to `configs/prompts/prompts.json`
- The registry supports template validation to ensure all required prompts are present and correctly formatted.
- See the prompt registry docstrings for best practices.

## Output Completeness
- The tool checks that all expected output files are created for every input code file.
- If any output is missing, a warning is logged specifying which files are missing for which code file.

## Supported Languages

- **Python** (.py)
- **JavaScript** (.js, .jsx)
- **TypeScript** (.ts, .tsx)
- **Java** (.java)
- **C++** (.cpp, .c, .h, .hpp)
- **C#** (.cs)
- **PHP** (.php)
- **Ruby** (.rb)
- **Go** (.go)
- **Rust** (.rs)
- **Swift** (.swift)
- **Kotlin** (.kt)
- **HTML** (.html)
- **CSS** (.css, .scss)
- **SQL** (.sql)
- **Shell** (.sh, .bat, .ps1)
- **Configuration** (.yaml, .yml, .json, .xml)

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_ingestion.py
```

## Development

### Project Structure

```
ai-reviewer-tool/
├── src/                   # Core source code
│   ├── ingestion.py      # Code and FRD ingestion
│   ├── prompts/          # LLM prompt templates
│   ├── agents.py         # Crew AI agents
│   ├── tools.py          # LangGraph tools
│   ├── output.py         # Report generation
│   ├── logger.py         # Logging utilities
│   ├── cli.py            # Command-line interface
│   ├── llm_provider.py   # Multi-provider LLM system
│   ├── validation.py     # Input validation
│   └── exceptions.py     # Custom exceptions
├── configs/              # Configuration files
│   ├── config.py         # Centralized configuration
│   └── languages.py      # Language detection
├── tests/                # Test suite
├── docs/                 # Documentation
├── scripts/              # Utility scripts
└── requirements.txt      # Dependencies
```

### Adding New Features

1. **New Language Support**: Update `src/config/languages.py` with file extensions and parsing logic
2. **New Analysis Type**: Add new tools in `src/tools.py` and update agents
3. **New Output Format**: Extend `src/output.py` with new formatters
4. **New LLM Provider**: Update `src/llm_provider.py` with new LLM configuration

### Code Style

The project follows PEP 8 standards. Use the provided tools:

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your API keys are set in environment variables
2. **Memory Issues**: For large codebases, consider processing files in batches
3. **Network Issues**: Use local LLM models for offline operation

### Debug Mode

Enable debug logging:

```bash
python src/cli.py review ./my-project --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the documentation in `docs/`
- Review existing issues
- Create a new issue with detailed information

## Roadmap

- [ ] Web-based interface
- [ ] CI/CD integration
- [ ] Custom rule engine
- [ ] Team collaboration features
- [ ] Advanced security scanning
- [ ] Performance benchmarking 