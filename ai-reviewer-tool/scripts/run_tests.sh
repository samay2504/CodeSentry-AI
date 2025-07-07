#!/bin/bash

# AI Code Review Agent Test Runner
# This script runs the test suite with various options

set -e  # Exit on any error

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

# Default values
TEST_TYPE="all"
COVERAGE=false
VERBOSE=false
PARALLEL=false
FAIL_FAST=false
LINT_ONLY=false
TYPE_CHECK_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --e2e)
            TEST_TYPE="e2e"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --parallel|-p)
            PARALLEL=true
            shift
            ;;
        --fail-fast|-x)
            FAIL_FAST=true
            shift
            ;;
        --lint-only)
            LINT_ONLY=true
            shift
            ;;
        --type-check-only)
            TYPE_CHECK_ONLY=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Show help function
show_help() {
    echo "AI Code Review Agent Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --unit              Run only unit tests"
    echo "  --integration       Run only integration tests"
    echo "  --e2e               Run only end-to-end tests"
    echo "  --coverage          Run tests with coverage report"
    echo "  --verbose, -v       Verbose output"
    echo "  --parallel, -p      Run tests in parallel"
    echo "  --fail-fast, -x     Stop on first failure"
    echo "  --lint-only         Run only linting checks"
    echo "  --type-check-only   Run only type checking"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 --unit            # Run only unit tests"
    echo "  $0 --coverage --verbose  # Run with coverage and verbose output"
    echo "  $0 --parallel --fail-fast  # Run in parallel, stop on failure"
    echo "  $0 --lint-only       # Run only linting"
}

# Check if virtual environment is activated
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "Virtual environment not activated"
        print_status "Attempting to activate virtual environment..."
        
        if [ -d "venv" ]; then
            if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
                source venv/Scripts/activate
            else
                source venv/bin/activate
            fi
            print_success "Virtual environment activated"
        else
            print_error "Virtual environment not found. Please run setup.sh first."
            exit 1
        fi
    fi
}

# Check if pytest is installed
check_pytest() {
    if ! python -c "import pytest" 2>/dev/null; then
        print_error "pytest not found. Please install dependencies first."
        exit 1
    fi
}

# Build pytest command
build_pytest_cmd() {
    local cmd="pytest"
    
    # Add test type filter
    case $TEST_TYPE in
        "unit")
            cmd="$cmd tests/test_ingestion.py tests/test_prompts.py tests/test_tools.py"
            ;;
        "integration")
            cmd="$cmd tests/test_agents.py tests/test_integration.py"
            ;;
        "e2e")
            cmd="$cmd tests/test_workflow.py"
            ;;
        "all")
            cmd="$cmd tests/"
            ;;
    esac
    
    # Add coverage if requested
    if [ "$COVERAGE" = true ]; then
        cmd="$cmd --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml"
    fi
    
    # Add verbose flag
    if [ "$VERBOSE" = true ]; then
        cmd="$cmd -v"
    fi
    
    # Add parallel flag
    if [ "$PARALLEL" = true ]; then
        cmd="$cmd -n auto"
    fi
    
    # Add fail-fast flag
    if [ "$FAIL_FAST" = true ]; then
        cmd="$cmd -x"
    fi
    
    # Add additional options
    cmd="$cmd --tb=short --strict-markers --durations=10"
    
    echo "$cmd"
}

# Run linting
run_linting() {
    print_status "Running code linting..."
    
    local lint_passed=true
    
    # Check if flake8 is available
    if python -c "import flake8" 2>/dev/null; then
        if flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503; then
            print_success "Flake8 linting passed"
        else
            print_warning "Flake8 linting found issues"
            lint_passed=false
        fi
    else
        print_warning "flake8 not found. Skipping flake8 linting."
    fi
    
    # Check if pylint is available
    if python -c "import pylint" 2>/dev/null; then
        if pylint src/ --disable=C0114,C0115,C0116; then
            print_success "Pylint passed"
        else
            print_warning "Pylint found issues"
            lint_passed=false
        fi
    else
        print_warning "pylint not found. Skipping pylint."
    fi
    
    return $([ "$lint_passed" = true ] && echo 0 || echo 1)
}

# Run type checking
run_type_checking() {
    print_status "Running type checking..."
    
    # Check if mypy is available
    if python -c "import mypy" 2>/dev/null; then
        if mypy src/ --ignore-missing-imports --no-strict-optional; then
            print_success "Type checking passed"
            return 0
        else
            print_warning "Type checking found issues"
            return 1
        fi
    else
        print_warning "mypy not found. Skipping type checking."
        return 0
    fi
}

# Run formatting check
run_format_check() {
    print_status "Running code formatting check..."
    
    # Check if black is available
    if python -c "import black" 2>/dev/null; then
        if black --check src/ tests/; then
            print_success "Code formatting is correct"
            return 0
        else
            print_warning "Code formatting issues found. Run 'black src/ tests/' to fix."
            return 1
        fi
    else
        print_warning "black not found. Skipping format check."
        return 0
    fi
}

# Run security checks
run_security_checks() {
    print_status "Running security checks..."
    
    # Check if bandit is available
    if python -c "import bandit" 2>/dev/null; then
        if bandit -r src/ -f json -o bandit-report.json; then
            print_success "Security checks passed"
            return 0
        else
            print_warning "Security issues found. Check bandit-report.json for details."
            return 1
        fi
    else
        print_warning "bandit not found. Skipping security checks."
        return 0
    fi
}

# Run import sorting check
run_import_check() {
    print_status "Running import sorting check..."
    
    # Check if isort is available
    if python -c "import isort" 2>/dev/null; then
        if isort --check-only src/ tests/; then
            print_success "Import sorting is correct"
            return 0
        else
            print_warning "Import sorting issues found. Run 'isort src/ tests/' to fix."
            return 1
        fi
    else
        print_warning "isort not found. Skipping import sorting check."
        return 0
    fi
}

# Run all quality checks
run_quality_checks() {
    print_status "Running quality checks..."
    
    local all_passed=true
    
    run_linting || all_passed=false
    run_type_checking || all_passed=false
    run_format_check || all_passed=false
    run_security_checks || all_passed=false
    run_import_check || all_passed=false
    
    if [ "$all_passed" = true ]; then
        print_success "All quality checks passed!"
        return 0
    else
        print_warning "Some quality checks failed"
        return 1
    fi
}

# Main test runner function
main() {
    echo "=========================================="
    echo "  AI Code Review Agent Test Runner"
    echo "=========================================="
    echo ""
    
    # Check environment
    check_venv
    check_pytest
    
    # Show test configuration
    print_status "Test configuration:"
    echo "  Type: $TEST_TYPE"
    echo "  Coverage: $COVERAGE"
    echo "  Verbose: $VERBOSE"
    echo "  Parallel: $PARALLEL"
    echo "  Fail Fast: $FAIL_FAST"
    echo ""
    
    # Run quality checks only if requested
    if [ "$LINT_ONLY" = true ]; then
        run_linting
        exit $?
    fi
    
    if [ "$TYPE_CHECK_ONLY" = true ]; then
        run_type_checking
        exit $?
    fi
    
    # Run pre-test checks
    run_quality_checks
    echo ""
    
    # Build and run pytest command
    print_status "Running tests..."
    pytest_cmd=$(build_pytest_cmd)
    print_status "Command: $pytest_cmd"
    echo ""
    
    # Execute tests
    if eval "$pytest_cmd"; then
        print_success "All tests passed!"
        
        # Show coverage summary if enabled
        if [ "$COVERAGE" = true ]; then
            echo ""
            print_status "Coverage report generated in htmlcov/index.html"
            print_status "Coverage XML report generated in coverage.xml"
        fi
    else
        print_error "Some tests failed!"
        exit 1
    fi
    
    echo ""
    echo "=========================================="
    print_success "Test run completed!"
    echo "=========================================="
}

# Run main function
main "$@" 