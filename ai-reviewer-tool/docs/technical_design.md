# Technical Design Document

## AI Code Review Tool

### 1. Architecture Overview

The AI Code Review Tool follows a modular, agent-based architecture designed for extensibility, maintainability, and production-grade reliability. The system is built using Python 3.9+ and leverages modern AI frameworks for intelligent code analysis and improvement.

#### Core Architecture Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI/SDK       │    │   Ingestion     │    │   Prompts       │
│   Interface     │───▶│   Module        │───▶│   Module        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agents        │    │   Tools         │    │   Output        │
│   Module        │◀───│   Module        │───▶│   Module        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Logger        │    │   LLM Provider  │    │   Validation    │
│   Module        │    │   System        │    │   Module        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. Data Flow & Component Interactions

#### 2.1 Input Processing Flow

1. **CLI/SDK Interface**: User initiates review via command-line or programmatic API
2. **Validation Module**: Validates input paths, file types, and security constraints
3. **Ingestion Module**: Parses FRD and codebase files into structured data
4. **Project Structure Analysis**: Identifies languages, dependencies, and file organization
5. **File Filtering**: Applies inclusion/exclusion rules based on configuration

#### 2.2 Analysis Flow

1. **Prompt Generation**: Creates context-aware prompts for different analysis types
2. **LLM Provider Selection**: Automatically selects and falls back between providers
3. **Agent Orchestration**: Crew AI coordinates multiple specialized agents
4. **Tool Execution**: LangGraph tools perform specific analysis tasks
5. **Result Aggregation**: Combines results from multiple analysis types

#### 2.3 Improvement Flow

1. **Issue Prioritization**: Ranks issues by severity and impact
2. **Code Improvement**: Generates improved code versions using LLM
3. **Validation**: Ensures functional equivalence
4. **Documentation**: Enhances code documentation

#### 2.4 Output Generation Flow

1. **Report Creation**: Generates comprehensive analysis reports
2. **Code Organization**: Creates improved code structure
3. **Metrics Calculation**: Computes quality metrics
4. **Summary Generation**: Creates project-wide summary

### 3. Core Modules Design

#### 3.1 CLI Module (`src/cli.py`)

**Purpose**: Provides command-line interface for all operations

**Key Commands**:
- `review`: Complete code review with improvements
- `analyze`: Analysis only (no changes)
- `improve`: Code improvement based on analysis
- `summary`: Project summary generation

**Design Principles**:
- Comprehensive argument validation
- Configurable output formats (Markdown, JSON, HTML)
- Focus area selection (security, performance, readability, maintainability)
- Robust error handling and logging

#### 3.2 Ingestion Module (`src/ingestion.py`)

**Purpose**: Handles parsing of functional requirements documents and codebases

**Key Functions**:
- `ingest_frd()`: Parses FRD files using regex patterns
- `ingest_codebase()`: Extracts files from ZIP, folder, or Git repositories
- `get_project_structure()`: Analyzes project organization and dependencies

**Design Principles**:
- Supports multiple input formats (ZIP, folder, Git)
- Filters files based on language support
- Excludes common non-code directories
- Handles large files with chunking

#### 3.3 Prompts Module (`src/prompts/`)

**Purpose**: Generates context-aware prompts for LLM interactions

**Key Components**:
- `prompts.py`: Core prompt templates
- `registry.py`: Prompt template registry
- Language-specific prompt variations

**Design Principles**:
- Uses LangChain PromptTemplate for consistency
- Structured JSON output format
- Context-aware prompt generation
- Multi-language support

#### 3.4 Agents Module (`src/agents.py`)

**Purpose**: Orchestrates AI agents for different review tasks

**Key Components**:
- `CodeReviewAgents`: Manages multiple specialized agents
- `setup_agents()`: Configures agents with different roles
- `run_review()`: Executes comprehensive review workflow

**Agent Types**:
- **Code Reviewer**: General code analysis and improvement
- **Security Specialist**: Security vulnerability detection
- **Performance Engineer**: Performance optimization analysis
- **Code Improver**: Code refactoring and enhancement
- **Documentation Specialist**: Documentation improvement

#### 3.5 Tools Module (`src/tools.py`)

**Purpose**: Provides LangGraph-decorated tools for specific analysis tasks

**Key Tools**:
- `analyze_code()`: Static code analysis with chunking support
- `improve_code()`: Code improvement based on issues
- `analyze_security()`: Security vulnerability detection
- `analyze_performance()`: Performance bottleneck identification
- `improve_documentation()`: Documentation enhancement

**Design Principles**:
- Language-agnostic analysis patterns
- Configurable severity levels
- Actionable improvement suggestions
- Metrics calculation
- Robust fallback mechanisms

#### 3.6 LLM Provider Module (`src/llm_provider.py`)

**Purpose**: Manages multiple LLM providers with automatic fallback

**Supported Providers**:
- **HuggingFace**: `bigcode/starcoder` (default)
- **Google Gemini**: Multiple model variants
- **OpenAI**: GPT-4 and GPT-3.5 variants
- **Groq**: Fast inference models

**Design Principles**:
- Automatic provider selection
- Robust fallback chains
- Configurable timeouts and retries
- Provider-specific optimizations

#### 3.7 Output Module (`src/output.py`)

**Purpose**: Generates improved code and comprehensive reports

**Key Functions**:
- `generate_output()`: Creates improved code files
- `generate_report()`: Creates detailed analysis reports
- `generate_project_summary()`: Project-wide summary
- `create_before_after_comparison()`: Side-by-side comparisons

**Output Formats**:
- Markdown reports
- JSON detailed reports
- HTML comparisons
- Code quality metrics

#### 3.8 Validation Module (`src/validation.py`)

**Purpose**: Provides comprehensive input validation and security checks

**Key Functions**:
- `validate_file_path()`: Path validation and security checks
- `validate_git_url()`: Git repository URL validation
- `validate_zip_file()`: ZIP file validation
- `validate_llm_config()`: LLM configuration validation

**Security Features**:
- Path traversal protection
- File size limits
- Content type validation
- Suspicious pattern detection

#### 3.9 Logger Module (`src/logger.py`)

**Purpose**: Provides structured logging with configurable verbosity

**Key Features**:
- JSON-formatted logs
- Configurable log levels
- File and console output
- Performance metrics logging
- Security event logging
- API key masking

### 4. Technology Stack

#### 4.1 Core Dependencies

- **Python 3.9+**: Core runtime environment
- **Crew AI 0.28.0**: Agent orchestration framework
- **LangChain 0.1.0**: LLM interaction framework
- **LangGraph**: Tool decoration and workflow management
- **Transformers 4.36.0**: Local model inference

#### 4.2 LLM Integration

- **HuggingFace**: Primary LLM provider (`bigcode/starcoder`)
- **Google Gemini**: Alternative LLM option
- **OpenAI**: GPT-4 and GPT-3.5 models
- **Groq**: Fast inference models

#### 4.3 Development Tools

- **pytest**: Testing framework
- **flake8**: Code linting
- **black**: Code formatting
- **mypy**: Type checking

### 5. Data Models

#### 5.1 File Information Model

```python
{
    'path': str,           # Relative file path
    'content': str,        # File content
    'size': int,          # File size in bytes
    'language': str,      # Detected language
    'extension': str      # File extension
}
```

#### 5.2 Issue Model

```python
{
    'type': str,          # Issue type (syntax, security, performance, etc.)
    'severity': str,      # Severity level (critical, high, medium, low)
    'line': int,          # Line number (optional)
    'description': str,   # Issue description
    'suggestion': str,    # Improvement suggestion
    'code_snippet': str   # Relevant code snippet (optional)
}
```

#### 5.3 Analysis Result Model

```python
{
    'issues': List[Issue],           # Found issues
    'metrics': Dict[str, float],     # Code quality metrics
    'file_path': str,               # File path
    'analysis_type': str,           # Analysis method used
    'summary': str                  # Analysis summary
}
```

#### 5.4 Codebase Information Model

```python
{
    'files': List[FileInfo],        # File information
    'project_info': Dict[str, Any], # Project metadata
    'structure': Dict[str, Any],    # Project structure
    'languages': List[str],         # Detected languages
    'dependencies': List[str]       # Project dependencies
}
```

### 6. Configuration Management

#### 6.1 Centralized Configuration (`configs/config.py`)

**Purpose**: Single source of truth for all configuration settings

**Key Components**:
- `LLMConfig`: LLM provider settings
- `AnalysisConfig`: Analysis parameters
- `OutputConfig`: Output formatting options
- `LoggingConfig`: Logging configuration
- `SecurityConfig`: Security settings

#### 6.2 Environment Variables

The system supports comprehensive environment variable configuration:
- API keys for all providers
- Performance tuning parameters
- Security settings
- Logging configuration

### 7. Security Features

#### 7.1 Input Validation
- Path traversal protection
- File size limits
- Content type validation
- Suspicious pattern detection

#### 7.2 Secure Logging
- API key masking
- Sensitive data sanitization
- Structured logging with security events

#### 7.3 Error Handling
- Custom exception types
- Graceful degradation
- Comprehensive error logging

### 8. Performance Optimizations

#### 8.1 File Processing
- Chunking for large files
- Parallel file processing
- Memory-efficient processing

#### 8.2 LLM Integration
- Provider fallback chains
- Configurable timeouts
- Retry mechanisms
- Caching support

#### 8.3 Resource Management
- Proper file handling
- Context managers
- Memory cleanup

### 9. Testing Strategy

#### 9.1 Test Coverage
- Unit tests for all modules
- Integration tests for workflows
- End-to-end tests for CLI
- Security tests for validation

#### 9.2 Test Structure
```
tests/
├── test_ingestion.py    # Ingestion module tests
├── test_tools.py        # Tools module tests
├── test_agents.py       # Agents module tests
├── test_output.py       # Output module tests
├── test_validation.py   # Validation module tests
├── test_integration.py  # Integration tests
└── test_workflow.py     # End-to-end tests
```

### 10. Deployment Considerations

#### 10.1 Production Requirements
- Python 3.9+ environment
- Minimum 4GB RAM
- Internet connectivity for LLM providers
- Proper API key management

#### 10.2 Configuration
- Environment variable setup
- Logging configuration
- Security settings
- Performance tuning

#### 10.3 Monitoring
- Structured logging
- Performance metrics
- Error tracking
- Security events

This technical design document provides a comprehensive overview of the AI Code Review Tool's architecture, implementation details, and operational considerations. 