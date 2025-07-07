# Quick Start Guide

Get the AI Code Review Tool up and running in 5 minutes!

## 🚀 Quick Setup

### 1. Prerequisites Check
```bash
# Check Python version (needs 3.9+)
python --version

# Check if pip is available
python -m pip --version
```

### 2. One-Command Setup

**Windows:**
```powershell
# Run in PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\setup.ps1
```

**Unix/Linux/macOS:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. Get API Key (Required)
You need at least one API key from these providers:

**HuggingFace (Recommended):**
1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "Read" permissions
3. Edit `.env` file and add: `HUGGINGFACEHUB_API_TOKEN=your_token_here`

**Alternative Providers:**
- **Google Gemini**: https://makersuite.google.com/app/apikey → `GOOGLE_API_KEY=your_key`
- **OpenAI**: https://platform.openai.com/api-keys → `OPENAI_API_KEY=your_key`
- **Groq**: https://console.groq.com/ → `GROQ_API_KEY=your_key`

### 4. Test Installation
```bash
# Activate virtual environment
# Windows: venv\Scripts\activate
# Unix/Linux/macOS: source venv/bin/activate

# Test CLI
python ai_reviewer.py --help

# Create test file
echo "print('Hello, World!')" > test.py

# Run first review
python ai_reviewer.py review test.py
```

## 🎯 Common Use Cases

### Review a Single File
```bash
python ai_reviewer.py review myfile.py
```

### Review a Project Directory
```bash
python ai_reviewer.py review ./my-project/
```

### Review a Git Repository
```bash
python ai_reviewer.py review https://github.com/user/repo
```

### Focus on Security
```bash
python ai_reviewer.py review ./my-project/ --focus security
```

### Generate Analysis Only (No Changes)
```bash
python ai_reviewer.py analyze ./my-project/
```

### Improve Code with Specific Focus
```bash
python ai_reviewer.py improve ./my-project/ --focus performance,readability
```

### Generate Project Summary
```bash
python ai_reviewer.py summary ./my-project/
```

## 🔧 Troubleshooting

### "API Key Not Found" Error
- Check that `.env` file exists
- Verify at least one API key is set in `.env`
- Restart your terminal after editing `.env`

### "Module Not Found" Error
- Activate virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
- Reinstall dependencies: `pip install -r requirements.txt`

### "Permission Denied" Error (Windows)
- Run PowerShell as Administrator
- Set execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### LLM Provider Issues
- The tool automatically falls back to other providers if one fails
- Check your internet connection
- Verify API keys have proper permissions
- Run with `--verbose` for detailed error information

### Tests Fail
- This is normal for initial setup
- Check that API keys are configured
- Some tests require network access

## 📁 Output Structure

After running a review, check the `output/` directory:
```
output/
├── improved_code/          # Improved code files
├── reports/                # Per-file and detailed reports
├── metrics/                # Per-file code quality metrics
├── docs/                   # Per-file documentation summaries (Markdown)
└── project_summary_*.md    # Overall summary
```
- For every input code file, you will find:
  - Improved code in `improved_code/`
  - A Markdown and JSON report in `reports/`
  - A metrics file in `metrics/`
  - A documentation summary in `docs/`

### Output Completeness
- The tool checks that all expected output files are created for every input code file.
- If any output is missing, a warning is logged specifying which files are missing for which code file.

### Prompt Customization
- You can override any prompt template by setting the environment variable:
  - `PROMPT_TEMPLATE_<TEMPLATE_NAME>`
- Or by placing a file in the `configs/prompts/` directory (e.g., `code_review.txt`)
- See the main README and `src/prompts/registry.py` for details.

## 🆘 Need Help?

- Check the full [README.md](../README.md) for detailed documentation
- Review [API Documentation](api_docs.md) for programmatic usage
- Check [Technical Design](technical_design.md) for architecture details
- Run `python src/cli.py --help` for CLI options

## 🎉 Success!

You're now ready to use the AI Code Review Tool! Try reviewing your own code:

```bash
python ai_reviewer.py review ./your-project/ --focus security,performance
``` 