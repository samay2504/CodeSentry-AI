#!/usr/bin/env python3
"""
AI Code Review Tool - Entry Point

This script provides an easy way to run the AI Code Review Tool from the project root.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import and run the CLI
from src.cli import main

if __name__ == '__main__':
    main() 