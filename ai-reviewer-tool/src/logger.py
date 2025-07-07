"""
Logger module for structured JSON logging with adjustable verbosity.

This module provides logging utilities for the AI reviewer tool,
including JSON-formatted logs and configurable verbosity levels.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import os


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    """Structured logger with JSON formatting and configurable verbosity."""
    
    def __init__(self, name: str = "ai_reviewer", level: str = "INFO", 
                 log_file: Optional[str] = None, config_file: Optional[str] = None):
        """
        Initialize the structured logger.
        
        Args:
            name: Logger name.
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            log_file: Optional log file path.
            config_file: Optional configuration file path.
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Load configuration if provided
        if config_file and os.path.exists(config_file):
            self._load_config(config_file)
        
        # Setup handlers
        self._setup_handlers(log_file)
        
        # Set formatter
        self._setup_formatter()
    
    def _load_config(self, config_file: str) -> None:
        """Load logging configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Apply configuration
            if 'level' in config:
                self.logger.setLevel(getattr(logging, config['level'].upper()))
            
            # Store config for later use
            self.config = config
            
        except Exception as e:
            print(f"Warning: Failed to load logging config from {config_file}: {e}")
            self.config = {}
    
    def _setup_handlers(self, log_file: Optional[str]) -> None:
        """Setup logging handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            try:
                # Create log directory if it doesn't exist
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(file_handler)
                
            except Exception as e:
                print(f"Warning: Failed to setup file logging to {log_file}: {e}")
    
    def _setup_formatter(self) -> None:
        """Setup JSON formatter for all handlers."""
        formatter = JSONFormatter()
        
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
    
    def log(self, level: str, message: str, extra_fields: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a message with optional extra fields.
        
        Args:
            level: Logging level.
            message: Log message.
            extra_fields: Optional extra fields to include in the log.
        """
        if extra_fields:
            # Create a custom log record with extra fields
            record = self.logger.makeRecord(
                self.name, getattr(logging, level.upper()), 
                '', 0, message, (), None
            )
            record.extra_fields = extra_fields
            self.logger.handle(record)
        else:
            getattr(self.logger, level.lower())(message)
    
    def debug(self, message: str, extra_fields: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self.log('DEBUG', message, extra_fields)
    
    def info(self, message: str, extra_fields: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self.log('INFO', message, extra_fields)
    
    def warning(self, message: str, extra_fields: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self.log('WARNING', message, extra_fields)
    
    def error(self, message: str, extra_fields: Optional[Dict[str, Any]] = None) -> None:
        """Log error message."""
        self.log('ERROR', message, extra_fields)
    
    def critical(self, message: str, extra_fields: Optional[Dict[str, Any]] = None) -> None:
        """Log critical message."""
        self.log('CRITICAL', message, extra_fields)
    
    def log_ingestion_start(self, file_path: str) -> None:
        """Log the start of file ingestion."""
        self.info("Starting file ingestion", {
            'action': 'ingestion_start',
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_ingestion_complete(self, file_path: str, file_count: int) -> None:
        """Log the completion of file ingestion."""
        self.info("File ingestion completed", {
            'action': 'ingestion_complete',
            'file_path': file_path,
            'files_processed': file_count,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_review_start(self, file_path: str) -> None:
        """Log the start of code review."""
        self.info("Starting code review", {
            'action': 'review_start',
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_review_complete(self, file_path: str, issues_found: int) -> None:
        """Log the completion of code review."""
        self.info("Code review completed", {
            'action': 'review_complete',
            'file_path': file_path,
            'issues_found': issues_found,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_improvement_start(self, file_path: str) -> None:
        """Log the start of code improvement."""
        self.info("Starting code improvement", {
            'action': 'improvement_start',
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_improvement_complete(self, file_path: str, changes_made: int) -> None:
        """Log the completion of code improvement."""
        self.info("Code improvement completed", {
            'action': 'improvement_complete',
            'file_path': file_path,
            'changes_made': changes_made,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_output_generation(self, output_dir: str, files_generated: int) -> None:
        """Log the generation of output files."""
        self.info("Output generation completed", {
            'action': 'output_generation',
            'output_dir': output_dir,
            'files_generated': files_generated,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with context."""
        error_info = {
            'action': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat()
        }
        
        if context:
            error_info.update(context)
        
        self.error(f"Error occurred: {error}", error_info)


def setup_logger(name: str = "ai_reviewer", level: str = "INFO", 
                 log_file: Optional[str] = None, config_file: Optional[str] = None) -> StructuredLogger:
    """
    Setup and return a structured logger.
    
    Args:
        name: Logger name.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional log file path.
        config_file: Optional configuration file path.
        
    Returns:
        Configured StructuredLogger instance.
    """
    # Use environment variables for default configuration
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO')
    
    if log_file is None:
        log_file = os.getenv('LOG_FILE', 'logs/ai_reviewer.log')
    
    return StructuredLogger(name, level, log_file, config_file)


def get_logger(name: str = "ai_reviewer") -> logging.Logger:
    """
    Get a standard Python logger with JSON formatting.
    
    Args:
        name: Logger name.
        
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    # Only setup if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler
        log_file = os.getenv('LOG_FILE', 'logs/ai_reviewer.log')
        try:
            # Create logs directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging to {log_file}: {e}")
        
        # JSON formatter
        formatter = JSONFormatter()
        console_handler.setFormatter(formatter)
        if 'file_handler' in locals():
            file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    return logger


def log_function_call(func_name: str, args: Dict[str, Any], result: Any = None, 
                     error: Optional[Exception] = None) -> None:
    """
    Log a function call with its arguments and result.
    
    Args:
        func_name: Name of the function being called.
        args: Function arguments.
        result: Function result (optional).
        error: Exception if any (optional).
    """
    logger = get_logger()
    
    log_data = {
        'action': 'function_call',
        'function': func_name,
        'arguments': args,
        'timestamp': datetime.now().isoformat()
    }
    
    if result is not None:
        log_data['result'] = str(result)
    
    if error is not None:
        log_data['error'] = {
            'type': type(error).__name__,
            'message': str(error)
        }
        logger.error(f"Function call failed: {func_name}", log_data)
    else:
        logger.info(f"Function call completed: {func_name}", log_data)


def log_performance_metric(metric_name: str, value: float, unit: str = "seconds") -> None:
    """
    Log a performance metric.
    
    Args:
        metric_name: Name of the performance metric.
        value: Metric value.
        unit: Unit of measurement.
    """
    logger = get_logger()
    
    logger.info(f"Performance metric: {metric_name}", {
        'action': 'performance_metric',
        'metric_name': metric_name,
        'value': value,
        'unit': unit,
        'timestamp': datetime.now().isoformat()
    })


def log_security_event(event_type: str, severity: str, details: Dict[str, Any]) -> None:
    """
    Log a security-related event.
    
    Args:
        event_type: Type of security event.
        severity: Event severity (low, medium, high, critical).
        details: Event details.
    """
    logger = get_logger()
    
    log_data = {
        'action': 'security_event',
        'event_type': event_type,
        'severity': severity,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    
    if severity in ['high', 'critical']:
        logger.error(f"Security event: {event_type}", log_data)
    else:
        logger.warning(f"Security event: {event_type}", log_data)


def create_logging_config(output_dir: str) -> Dict[str, Any]:
    """
    Create a default logging configuration.
    
    Args:
        output_dir: Output directory for log files.
        
    Returns:
        Logging configuration dictionary.
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'class': 'src.logger.JSONFormatter'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'json',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'json',
                'filename': os.path.join(output_dir, 'ai_reviewer.log'),
                'mode': 'a',
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            'ai_reviewer': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'WARNING',
            'handlers': ['console']
        }
    }


def save_logging_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save logging configuration to a file.
    
    Args:
        config: Logging configuration.
        config_path: Path to save the configuration.
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save logging config to {config_path}: {e}")


def setup_logging(name: str = "ai_reviewer", level: str = None, 
                 log_file: Optional[str] = None, config_file: Optional[str] = None) -> StructuredLogger:
    """
    Setup logging with the specified configuration.
    
    Args:
        name: Logger name.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional log file path.
        config_file: Optional configuration file path.
        
    Returns:
        Configured StructuredLogger instance.
    """
    return setup_logger(name, level, log_file, config_file)


# Default logger instance
default_logger = get_logger("ai_reviewer") 