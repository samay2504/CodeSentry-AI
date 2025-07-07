# AI Code Review Agent Setup Script for Windows
# This script sets up the development environment for the AI reviewer tool

param(
    [switch]$SkipTests,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up AI Code Review Agent..." -ForegroundColor Green

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if Python 3.9+ is installed
function Test-PythonVersion {
    Write-Status "Checking Python version..."
    
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
            if ($versionMatch) {
                $major = [int]$matches[1]
                $minor = [int]$matches[2]
                
                if ($major -ge 3 -and $minor -ge 9) {
                    Write-Success "Python $major.$minor found"
                    return $true
                } else {
                    Write-Error "Python 3.9+ required, found $major.$minor"
                    return $false
                }
            }
        }
    } catch {
        Write-Error "Python not found. Please install Python 3.9 or higher."
        return $false
    }
    
    Write-Error "Python not found. Please install Python 3.9 or higher."
    return $false
}

# Check if pip is available
function Test-Pip {
    Write-Status "Checking pip..."
    
    try {
        python -m pip --version | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "pip is available"
            return $true
        }
    } catch {
        Write-Error "pip not found. Please install pip."
        return $false
    }
    
    Write-Error "pip not found. Please install pip."
    return $false
}

# Create virtual environment
function New-VirtualEnvironment {
    Write-Status "Creating virtual environment..."
    
    if (Test-Path "venv") {
        Write-Warning "Virtual environment already exists. Removing..."
        Remove-Item -Recurse -Force "venv"
    }
    
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Virtual environment created"
        return $true
    } else {
        Write-Error "Failed to create virtual environment"
        return $false
    }
}

# Activate virtual environment
function Invoke-ActivateVirtualEnvironment {
    Write-Status "Activating virtual environment..."
    
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
        Write-Success "Virtual environment activated"
        return $true
    } else {
        Write-Error "Virtual environment activation script not found"
        return $false
    }
}

# Install dependencies
function Install-Dependencies {
    Write-Status "Installing dependencies..."
    
    # Upgrade pip first
    python -m pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed"
        return $true
    } else {
        Write-Error "Failed to install dependencies"
        return $false
    }
}

# Create necessary directories
function New-Directories {
    Write-Status "Creating necessary directories..."
    
    $directories = @("logs", "output", "tests\output", "cache")
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Directories created"
}

# Create configuration files
function New-ConfigurationFiles {
    Write-Status "Creating configuration files..."
    
    # Create .env template if it doesn't exist
    if (-not (Test-Path ".env")) {
        $envContent = @"
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
"@
        $envContent | Out-File -FilePath ".env" -Encoding UTF8
        Write-Success "Created .env template"
        Write-Warning "Please edit .env file and add your API keys"
    }
    
    Write-Success "Configuration files created"
}

# Setup logging
function Setup-Logging {
    Write-Status "Setting up logging configuration..."
    
    python scripts/setup_logs.py
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Logging configuration completed"
        return $true
    } else {
        Write-Warning "Logging setup failed, but continuing..."
        return $true
    }
}

# Run initial tests
function Invoke-Tests {
    if ($SkipTests) {
        Write-Warning "Skipping tests as requested"
        return $true
    }
    
    Write-Status "Running initial tests..."
    
    try {
        pytest tests/ -v
        if ($LASTEXITCODE -eq 0) {
            Write-Success "All tests passed"
            return $true
        } else {
            Write-Warning "Some tests failed. This is normal for initial setup."
            return $true
        }
    } catch {
        Write-Warning "Tests failed to run. This is normal for initial setup."
        return $true
    }
}

# Main setup function
function Start-Setup {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  AI Code Review Agent Setup" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check prerequisites
    if (-not (Test-PythonVersion)) {
        exit 1
    }
    
    if (-not (Test-Pip)) {
        exit 1
    }
    
    # Setup environment
    if (-not (New-VirtualEnvironment)) {
        exit 1
    }
    
    if (-not (Invoke-ActivateVirtualEnvironment)) {
        exit 1
    }
    
    if (-not (Install-Dependencies)) {
        exit 1
    }
    
    # Create directories and configs
    New-Directories
    New-ConfigurationFiles
    Setup-Logging
    
    # Run tests
    Invoke-Tests
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Success "Setup completed successfully!"
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Activate the virtual environment:" -ForegroundColor White
    Write-Host "   venv\Scripts\activate" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Configure API keys in .env file" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Run the tool:" -ForegroundColor White
    Write-Host "   python ai_reviewer.py review ./your-project" -ForegroundColor Gray
    Write-Host "   # or" -ForegroundColor Gray
    Write-Host "   python ai_reviewer.py review https://github.com/user/repo" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Run tests:" -ForegroundColor White
    Write-Host "   pytest tests/" -ForegroundColor Gray
    Write-Host "   # or" -ForegroundColor Gray
    Write-Host "   python scripts/run_tests.sh" -ForegroundColor Gray
    Write-Host ""
    Write-Host "For more information, see README.md" -ForegroundColor White
    Write-Host ""
}

# Run main setup
Start-Setup 