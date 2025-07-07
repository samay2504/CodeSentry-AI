#!/usr/bin/env python3
"""
Setup script to ensure logs directory exists and configure logging
"""

import os
import sys
from pathlib import Path


def setup_logs():
    """Create logs directory and ensure proper logging setup."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Create logs directory
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Create .gitkeep to ensure the directory is tracked by git
    gitkeep_file = logs_dir / '.gitkeep'
    gitkeep_file.touch(exist_ok=True)
    
    print(f"✅ Created logs directory: {logs_dir}")
    
    # Check if log file path is configured correctly
    log_file = os.getenv('LOG_FILE', './ai_reviewer.log')
    
    if log_file.startswith('logs/'):
        # Ensure the logs directory exists for relative paths
        log_path = project_root / log_file
        log_path.parent.mkdir(exist_ok=True)
        print(f"✅ Log file path configured: {log_path}")
    else:
        print(f"✅ Log file path configured: {log_file}")
    
    # Create a sample log file to test write permissions
    try:
        test_log = project_root / 'logs' / 'test.log'
        with open(test_log, 'w') as f:
            f.write("# Test log file - can be deleted\n")
        test_log.unlink()  # Remove the test file
        print("✅ Log directory is writable")
    except Exception as e:
        print(f"⚠️  Warning: Could not write to logs directory: {e}")
    
    # Create log rotation configuration
    create_log_config(project_root)
    
    print("\n📝 Logging Configuration:")
    print(f"   Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
    print(f"   Log File: {os.getenv('LOG_FILE', './ai_reviewer.log')}")
    print(f"   Logs Directory: {logs_dir}")
    print(f"   Max Log Size: {os.getenv('MAX_LOG_SIZE', '10MB')}")
    print(f"   Log Backup Count: {os.getenv('LOG_BACKUP_COUNT', '5')}")


def create_log_config(project_root: Path):
    """Create logging configuration file."""
    config_dir = project_root / 'configs'
    config_dir.mkdir(exist_ok=True)
    
    log_config_file = config_dir / 'logging.json'
    
    if not log_config_file.exists():
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": "logs/ai_reviewer.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                    "encoding": "utf8"
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": "logs/errors.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 3,
                    "encoding": "utf8"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file", "error_file"],
                    "level": "INFO",
                    "propagate": False
                },
                "src": {
                    "handlers": ["console", "file", "error_file"],
                    "level": "DEBUG",
                    "propagate": False
                }
            }
        }
        
        import json
        with open(log_config_file, 'w') as f:
            json.dump(log_config, f, indent=2)
        
        print(f"✅ Created logging configuration: {log_config_file}")


if __name__ == "__main__":
    setup_logs() 