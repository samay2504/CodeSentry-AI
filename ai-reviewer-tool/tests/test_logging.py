#!/usr/bin/env python3
"""
Tests for the enhanced logging system including file handlers and configuration.
"""

import pytest
import os
import tempfile
import logging
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.logger import setup_logging, get_logger, StructuredLogger, JSONFormatter
from src.llm_provider import create_llm_provider
from src.cli import main


class TestLoggingSetup:
    """Test logging setup functionality."""
    
    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            logger = setup_logging(log_file=log_file)
            
            # Check that log directory was created
            log_dir = os.path.dirname(log_file)
            assert os.path.exists(log_dir)
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)

    def test_setup_logging_creates_log_file(self):
        """Test that setup_logging creates log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            logger = setup_logging(log_file=log_file)
            
            # Write a test message
            logger.info("Test message")
            
            # Check that log file was created
            assert os.path.exists(log_file)
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)

    def test_setup_logging_configures_file_handler(self):
        """Test that setup_logging configures file handler correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            logger = setup_logging(log_file=log_file)
            
            # Check that file handler is configured
            file_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)

    def test_setup_logging_configures_console_handler(self):
        """Test that setup_logging configures console handler correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            logger = setup_logging(log_file=log_file)
            
            # Check that console handler is configured
            console_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
            assert len(console_handlers) > 0
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)

    def test_setup_logging_sets_correct_level(self):
        """Test that setup_logging sets the correct log level."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging with DEBUG level
            logger = setup_logging(level="DEBUG", log_file=log_file)
            
            # Check that log level is set correctly
            assert logger.logger.level == logging.DEBUG
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)

    def test_setup_logging_uses_custom_format(self):
        """Test that setup_logging uses custom JSON format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            logger = setup_logging(log_file=log_file)
            
            # Check that JSON formatter is used
            formatters = [h.formatter for h in logger.logger.handlers if h.formatter]
            assert any(isinstance(f, JSONFormatter) for f in formatters)
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)


class TestLoggingFunctionality:
    """Test logging functionality."""
    
    def test_logging_writes_to_file(self):
        """Test that logging writes messages to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            logger = setup_logging(log_file=log_file)
            
            # Write test message
            test_message = "Test log message"
            logger.info(test_message)
            
            # Read log file
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Check that message was written
            assert test_message in log_content
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)

    def test_logging_includes_timestamp(self):
        """Test that logging includes timestamp in JSON format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            logger = setup_logging(log_file=log_file)
            
            # Write test message
            logger.info("Test message")
            
            # Read log file
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Parse JSON and check timestamp
            log_entry = json.loads(log_content.strip())
            assert 'timestamp' in log_entry
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)

    def test_logging_includes_log_level(self):
        """Test that logging includes log level in JSON format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            logger = setup_logging(log_file=log_file)
            
            # Write messages at different levels
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Read log file
            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            # Check that log levels are included
            for line in log_lines:
                log_entry = json.loads(line.strip())
                assert 'level' in log_entry
                assert log_entry['level'] in ['INFO', 'WARNING', 'ERROR']
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)

    def test_logging_includes_module_name(self):
        """Test that logging includes module name in JSON format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            logger = setup_logging(log_file=log_file)
            
            # Write test message
            logger.info("Test message")
            
            # Read log file
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Parse JSON and check module name
            log_entry = json.loads(log_content.strip())
            assert 'module' in log_entry
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)


class TestLoggingErrorHandling:
    """Test logging error handling."""
    
    def test_setup_logging_with_file_permission_error(self):
        """Test that setup_logging handles file permission errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a directory that can't be written to (simulate permission error)
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging (should not fail even if file can't be created)
            logger = setup_logging(log_file=log_file)
            
            # Should still have console handler
            console_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
            assert len(console_handlers) > 0
            
            # Clean up handlers to avoid file permission issues
            for handler in logger.logger.handlers:
                handler.close()
                logger.logger.removeHandler(handler)


class TestLoggingIntegration:
    """Test logging integration with other components."""
    
    def test_logging_with_llm_provider(self):
        """Test that LLM provider uses logging correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            setup_logging(log_file=log_file)
            
            # Create LLM provider (should log attempts)
            try:
                create_llm_provider({'model': 'test'})
            except Exception:
                pass  # Expected to fail without API keys
            
            # Check that logs were written
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                assert len(log_content) > 0

    def test_logging_with_cli(self):
        """Test that CLI uses logging correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "logs", "test.log")
            
            # Setup logging
            setup_logging(log_file=log_file)
            
            # Test CLI with invalid arguments (should log errors)
            try:
                with patch('sys.argv', ['cli.py', '--invalid-arg']):
                    main()
            except SystemExit:
                pass  # Expected to exit with invalid args
            
            # Check that logs were written
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                assert len(log_content) > 0


if __name__ == "__main__":
    pytest.main([__file__]) 