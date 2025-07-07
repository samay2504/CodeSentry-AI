#!/bin/bash

# AI Code Review Agent Setup Script
# This script sets up the development environment for the AI reviewer tool

set -e  # Exit on any error

echo "🚀 Setting up AI Code Review Agent..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.9+ is installed
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
        PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.9+ required, found $PYTHON_VERSION"
            exit 1
        fi
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_MAJOR=$(python -c "import sys; print(sys.version_info.major)")
        PYTHON_MINOR=$(python -c "import sys; print(sys.version_info.minor)")
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python"
        else
            print_error "Python 3.9+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python not found. Please install Python 3.9 or higher."
        exit 1
    fi
}

# Check if pip is available
check_pip() {
    print_status "Checking pip..."
    
    if $PYTHON_CMD -m pip --version &> /dev/null; then
        print_success "pip is available"
    else
        print_error "pip not found. Please install pip."
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Unix/Linux/macOS
        source venv/bin/activate
    fi
    
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p output
    mkdir -p tests/output
    mkdir -p cache
    
    print_success "Directories created"
}

# Setup pre-commit hooks (optional)
setup_pre_commit() {
    print_status "Setting up pre-commit hooks..."
    
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_warning "pre-commit not found. Skipping pre-commit setup."
        print_status "To install pre-commit: pip install pre-commit"
    fi
}

# Run initial tests
run_tests() {
    print_status "Running initial tests..."
    
    if pytest tests/ -v; then
        print_success "All tests passed"
    else
        print_warning "Some tests failed. This is normal for initial setup."
    fi
}

# Create configuration files
create_configs() {
    print_status "Creating configuration files..."
    
    # Create .env template if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# AI Code Review Agent Environment Variables
# Copy this file to .env and fill in your API keys

# OpenAI API Key (optional)
# OPENAI_API_KEY=your_openai_api_key_here

# Google AI API Key (optional)
# GOOGLE_API_KEY=your_google_api_key_here

# HUGGINGFACEHUB_API_TOKEN=your_huggingface_api_key_here

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Output directory
OUTPUT_DIR=./output

# Log file path
LOG_FILE=logs/ai_reviewer.log

# Max log size (in bytes)
MAX_LOG_SIZE=10485760

# Number of log backups to keep
LOG_BACKUP_COUNT=5
EOF
        print_success "Created .env template"
    fi
    
    # Create .gitignore if it doesn't exist
    if [ ! -f ".gitignore" ]; then
        cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Output
output/
tests/output/

# Environment variables
.env

# Database
*.db
*.sqlite
database.db

# API Keys and Credentials
configs/credentials.json
credentials.json

# OS
.DS_Store
Thumbs.db

# Patch system (optional - uncomment if you want to exclude patches)
# scripts/patches/*.py
EOF
        print_success "Created .gitignore"
    fi
}

# Setup logging
setup_logging() {
    print_status "Setting up logging configuration..."
    
    python scripts/setup_logs.py
    print_success "Logging configuration completed"
}

# Main setup function
main() {
    echo "=========================================="
    echo "  AI Code Review Agent Setup"
    echo "=========================================="
    echo ""
    
    # Check prerequisites
    check_python
    check_pip
    
    # Setup environment
    create_venv
    activate_venv
    install_dependencies
    
    # Create directories and configs
    create_directories
    create_configs
    setup_logging
    
    # Optional setup
    setup_pre_commit
    
    # Run tests
    run_tests
    
    echo ""
    echo "=========================================="
    print_success "Setup completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment:"
    echo "   - Windows: venv\\Scripts\\activate"
    echo "   - Unix/Linux/macOS: source venv/bin/activate"
    echo ""
    echo "2. Configure API keys in .env file (optional)"
    echo ""
    echo "3. Run the tool:"
    echo "   python ai_reviewer.py review ./your-project"
    echo "   # or"
    echo "   python ai_reviewer.py review https://github.com/user/repo"
    echo ""
    echo "4. Run tests:"
    echo "   pytest tests/"
    echo "   # or"
    echo "   ./scripts/run_tests.sh"
    echo ""
    echo "For more information, see README.md"
    echo ""
}

# Run main function
main "$@" 