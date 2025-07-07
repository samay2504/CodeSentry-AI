# AI Code Review Tool - Production Edition

A production-grade, enterprise-ready AI-powered code review and improvement tool with comprehensive security, validation, and error handling.

## 🚀 Production Features

### **Multi-Provider LLM System**
- ✅ **HuggingFace Integration**: Primary provider with `bigcode/starcoder`
- ✅ **Google Gemini Support**: Secondary provider with multiple models
- ✅ **OpenAI Integration**: GPT-4 and GPT-3.5 variants
- ✅ **Groq Support**: Fast inference models
- ✅ **Automatic Fallback**: Graceful degradation when providers fail
- ✅ **Fallback Mode**: Static analysis when all LLMs unavailable

### **Security & Validation**
- ✅ **Input Validation**: Comprehensive validation for all user inputs
- ✅ **Path Traversal Protection**: Prevents directory traversal attacks
- ✅ **File Size Limits**: Configurable limits to prevent resource exhaustion
- ✅ **Content Type Validation**: Validates file types and content
- ✅ **API Key Masking**: Secure logging without exposing sensitive data
- ✅ **Suspicious Pattern Detection**: Identifies dangerous code patterns

### **Error Handling & Reliability**
- ✅ **Custom Exception Types**: Specific error handling for different scenarios
- ✅ **Graceful Degradation**: Fallback systems when LLM providers fail
- ✅ **Comprehensive Logging**: Structured JSON logging with proper levels
- ✅ **Resource Management**: Proper file handling and cleanup
- ✅ **Timeout Handling**: Prevents hanging operations
- ✅ **Retry Mechanisms**: Exponential backoff for transient failures

### **Configuration Management**
- ✅ **Centralized Configuration**: Single source of truth for all settings
- ✅ **Environment Variable Support**: Easy deployment configuration
- ✅ **Configuration Validation**: Validates all configuration values
- ✅ **Multiple Providers**: Support for HuggingFace, Google, OpenAI, Groq
- ✅ **Fallback Chains**: Automatic provider switching on failure

### **Code Quality**
- ✅ **Type Hints**: Complete type annotations throughout
- ✅ **Comprehensive Testing**: Unit, integration, and end-to-end tests
- ✅ **Code Documentation**: Detailed docstrings and comments
- ✅ **Consistent Error Handling**: Standardized error patterns
- ✅ **Resource Cleanup**: Proper context managers and cleanup

## 📋 Requirements

### **System Requirements**
- **Python**: 3.9 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Internet connection for LLM providers

### **Dependencies**
```bash
# Core AI/ML
crewai==0.28.0
langchain==0.1.0
transformers==4.36.0
torch==2.1.0

# LLM Providers
langchain-google-genai==0.0.6
langchain-openai==0.0.5
langchain-huggingface==0.0.6
langchain-groq==0.0.3

# Security & Validation
python-dotenv==1.0.0
structlog==23.2.0

# Testing & Development
pytest==7.4.3
pytest-cov==4.1.0
black==23.12.0
mypy==1.8.0
```

## 🛠️ Installation

### **Quick Start**
```bash
# Clone repository
git clone <repository-url>
cd ai-reviewer-tool

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your API keys
```

### **Production Deployment**
```bash
# Install with production dependencies only
pip install -r requirements.txt --no-dev

# Setup production logging
mkdir logs
chmod 755 logs

# Configure environment variables
export LOG_LEVEL=INFO
export MASK_API_KEYS=true
export VALIDATE_INPUTS=true
```

## ⚙️ Configuration

### **Environment Variables**
```bash
# Required: At least one API key
HUGGINGFACEHUB_API_TOKEN=your_token_here
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

# LLM Configuration
DEFAULT_LLM_MODEL=bigcode/starcoder
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2048
LLM_TIMEOUT=30

# Security Settings
MASK_API_KEYS=true
SANITIZE_LOGS=true
VALIDATE_INPUTS=true
MAX_INPUT_SIZE_MB=50

# Performance Settings
MAX_PARALLEL_FILES=5
CHUNK_SIZE=800
CHUNK_OVERLAP=100

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log
LOG_JSON_FORMAT=true
```

### **Configuration File**
Create `config.json` for advanced configuration:
```json
{
  "llm": {
    "model": "bigcode/starcoder",
    "temperature": 0.1,
    "max_tokens": 2048,
    "timeout": 30
  },
  "analysis": {
    "chunk_size": 800,
    "chunk_overlap": 100,
    "enable_security": true,
    "enable_performance": true
  },
  "output": {
    "default_format": "markdown",
    "output_dir": "./output",
    "include_metrics": true
  }
}
```

## 🔧 Usage

### **Command Line Interface**
```bash
# Review a codebase
python src/cli.py review ./my-project --focus security,performance

# Analyze only (no changes)
python src/cli.py analyze ./my-project --output-dir ./analysis

# Improve specific aspects
python src/cli.py improve ./my-project --focus security

# Generate summary
python src/cli.py summary ./my-project --format html
```

### **Programmatic Usage**
```python
from src import config, validator, ingest_codebase, analyze_code

# Validate input
validated_path = validator.validate_file_path("myfile.py")

# Ingest codebase
codebase_info = ingest_codebase("./my-project")

# Analyze code
result = analyze_code.invoke({
    'code': code_content,
    'file_path': 'myfile.py'
})
```

## 🔒 Security Features

### **Input Validation**
- **File Path Validation**: Prevents path traversal attacks
- **Content Validation**: Detects suspicious code patterns
- **Size Limits**: Prevents resource exhaustion
- **Type Checking**: Validates file types and content

### **API Key Security**
- **Environment Storage**: No hardcoded credentials
- **Logging Masking**: API keys masked in logs
- **Secure Transmission**: HTTPS for all API calls
- **Access Control**: Proper permission management

### **Error Handling**
- **Custom Exceptions**: Specific error types
- **Secure Messages**: No sensitive data in errors
- **Audit Logging**: Security event tracking
- **Graceful Degradation**: Fallback mechanisms

## 📊 Performance Features

### **Large File Processing**
- **Chunking**: Intelligent file splitting for LLM processing
- **Memory Efficiency**: Streaming and chunked processing
- **Parallel Processing**: Configurable parallel execution
- **Resource Limits**: Configurable size and time limits

### **LLM Optimization**
- **Provider Fallback**: Automatic switching on failure
- **Timeout Management**: Prevents hanging operations
- **Retry Logic**: Exponential backoff for transient failures
- **Caching**: Response caching where appropriate

### **Scalability**
- **Configurable Limits**: Adjustable processing parameters
- **Progress Tracking**: Real-time progress monitoring
- **Resource Management**: Proper cleanup and memory management
- **Batch Processing**: Efficient handling of multiple files

## 🧪 Testing

### **Test Coverage**
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_security.py
pytest tests/test_performance.py
```

### **Test Categories**
- **Unit Tests**: Individual module testing
- **Integration Tests**: Module interaction testing
- **Security Tests**: Input validation and security checks
- **Performance Tests**: Scalability and resource usage
- **End-to-End Tests**: Complete workflow validation

## 📈 Monitoring

### **Logging**
```python
# Structured JSON logging
{
    "timestamp": "2024-01-01T12:00:00Z",
    "level": "INFO",
    "module": "src.cli",
    "message": "Review completed",
    "metrics": {
        "files_processed": 10,
        "issues_found": 25,
        "processing_time": 120.5
    }
}
```

### **Metrics Collection**
- **Processing Time**: Time per file and total
- **Success Rates**: Success/failure percentages
- **Resource Usage**: Memory and CPU consumption
- **Provider Usage**: LLM provider statistics
- **Error Frequency**: Error rates and types

## 🚀 Deployment

### **Production Checklist**
- [ ] Environment variables configured
- [ ] API keys secured and validated
- [ ] Logging directory created and secured
- [ ] File permissions set correctly
- [ ] Network connectivity verified
- [ ] Dependencies installed
- [ ] Tests passing
- [ ] Configuration validated

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p logs output

ENV LOG_LEVEL=INFO
ENV MASK_API_KEYS=true

CMD ["python", "src/cli.py", "review", "/code"]
```

### **Kubernetes Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-reviewer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-reviewer
  template:
    metadata:
      labels:
        app: ai-reviewer
    spec:
      containers:
      - name: ai-reviewer
        image: ai-reviewer:latest
        env:
        - name: HUGGINGFACEHUB_API_TOKEN
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: huggingface-token
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: output
          mountPath: /app/output
      volumes:
      - name: logs
        emptyDir: {}
      - name: output
        emptyDir: {}
```

## 🔧 Troubleshooting

### **Common Issues**

**LLM Provider Failures**
```bash
# Check API keys
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('HF:', bool(os.getenv('HUGGINGFACEHUB_API_TOKEN')))"

# Test provider connectivity
python src/cli.py review test.py --verbose
```

**Memory Issues**
```bash
# Reduce parallel processing
export MAX_PARALLEL_FILES=2

# Reduce chunk size
export CHUNK_SIZE=400
```

**Permission Issues**
```bash
# Fix file permissions
chmod 755 logs output
chmod 644 .env
```

### **Debug Mode**
```bash
# Enable verbose logging
python src/cli.py review ./my-project --verbose

# Check configuration
python -c "from configs.config import config; print(config)"
```

## 📚 Documentation

### **Available Documentation**
- **[README.md](../README.md)**: Main project documentation
- **[QUICKSTART.md](QUICKSTART.md)**: Quick start guide
- **[API Documentation](api_docs.md)**: Programmatic API reference
- **[Technical Design](technical_design.md)**: Architecture and design details
- **[Production Standards](PRODUCTION_STANDARDS.md)**: Production best practices

### **Support Resources**
- **Issue Tracking**: GitHub issues for bug reports
- **Discussions**: GitHub discussions for questions
- **Wiki**: Additional documentation and examples
- **Examples**: Sample code and use cases

## 🎯 Best Practices

### **Development**
1. **Use Type Hints**: Complete type annotations
2. **Handle Errors**: Specific exception types
3. **Validate Inputs**: Comprehensive validation
4. **Manage Resources**: Proper cleanup
5. **Document Code**: Clear docstrings

### **Security**
1. **Secure API Keys**: Environment variables only
2. **Validate Inputs**: All user inputs
3. **Mask Sensitive Data**: In logs and errors
4. **Use HTTPS**: For all external calls
5. **Limit Permissions**: Principle of least privilege

### **Performance**
1. **Use Chunking**: For large files
2. **Parallel Processing**: When appropriate
3. **Set Timeouts**: Prevent hanging
4. **Monitor Resources**: Memory and CPU usage
5. **Cache Results**: When beneficial

### **Reliability**
1. **Implement Fallbacks**: Multiple providers
2. **Handle Errors**: Graceful degradation
3. **Retry Logic**: For transient failures
4. **Monitor Health**: System status
5. **Backup Data**: Important configurations

This production edition provides enterprise-grade reliability, security, and performance for AI-powered code review and improvement.

## 📁 Output Structure

After running a review, the output directory will contain:
- `improved_code/`: Improved code files (one per input file)
- `reports/`: Per-file Markdown and JSON reports
- `metrics/`: Per-file metrics files
- `docs/`: Per-file documentation summaries (Markdown)
- `project_summary_*.md`: Overall project summary

The tool checks for output completeness and logs warnings if any expected files are missing.

## 📝 Prompt Customization & Registry

- All prompt templates are managed by a centralized prompt registry (`src/prompts/registry.py`).
- You can override any prompt template by:
  - Setting the environment variable `PROMPT_TEMPLATE_<TEMPLATE_NAME>`
  - Adding a file in `configs/prompts/<template_name>.txt`
  - Adding to `configs/prompts/prompts.json`
- The registry supports template validation to ensure all required prompts are present and correctly formatted.
- See the prompt registry docstrings for best practices.

## ✅ Output Completeness
- The tool checks that all expected output files are created for every input code file.
- If any output is missing, a warning is logged specifying which files are missing for which code file. 