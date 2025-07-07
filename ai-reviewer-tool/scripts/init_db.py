#!/usr/bin/env python3
"""
Database initialization script for AI Code Review Agent.

This script creates the necessary database tables and initializes
the SQLite database for storing review history and metadata.
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from logger import get_logger

logger = get_logger("db_init")

def init_database(db_path: str = "database.db"):
    """
    Initialize the SQLite database with required tables.
    
    Args:
        db_path: Path to the database file
    """
    try:
        # Create database directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute('PRAGMA foreign_keys = ON')
        
        # Create requirements history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requirements_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frd_path TEXT NOT NULL,
                requirement_id TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create review history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_issues INTEGER DEFAULT 0,
                critical_issues INTEGER DEFAULT 0,
                high_issues INTEGER DEFAULT 0,
                medium_issues INTEGER DEFAULT 0,
                low_issues INTEGER DEFAULT 0,
                complexity_score REAL DEFAULT 0.0,
                maintainability_score REAL DEFAULT 0.0,
                security_score REAL DEFAULT 0.0,
                performance_score REAL DEFAULT 0.0,
                review_summary TEXT,
                llm_provider TEXT,
                model_used TEXT,
                review_duration REAL DEFAULT 0.0
            )
        ''')
        
        # Create project history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT NOT NULL,
                review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_files INTEGER DEFAULT 0,
                total_issues INTEGER DEFAULT 0,
                languages TEXT,
                dependencies TEXT,
                review_duration REAL DEFAULT 0.0,
                output_path TEXT,
                git_repo_url TEXT,
                git_commit_hash TEXT
            )
        ''')
        
        # Create metrics history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_details TEXT,
                FOREIGN KEY (file_path) REFERENCES review_history (file_path)
            )
        ''')
        
        # Create configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                description TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create patch history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patch_version TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                applied_by TEXT,
                status TEXT DEFAULT 'success',
                notes TEXT
            )
        ''')
        
        # Insert default configuration
        default_configs = [
            ('log_level', 'INFO', 'Logging level for the application'),
            ('output_dir', './output', 'Default output directory for reviews'),
            ('max_file_size', '1048576', 'Maximum file size to process (1MB)'),
            ('supported_languages', 'python,javascript,typescript,java,cpp,html,css,ruby,go,rust,php', 'Supported programming languages'),
            ('exclude_patterns', '__pycache__,node_modules,.git,build,dist,venv,env', 'Patterns to exclude from review'),
            ('default_llm', 'openai', 'Default LLM provider'),
            ('default_model', 'gpt-4', 'Default model to use'),
            ('max_tokens', '4000', 'Maximum tokens for LLM responses'),
            ('temperature', '0.1', 'Temperature for LLM responses'),
            ('timeout', '30', 'Timeout for API calls in seconds'),
            ('retry_attempts', '3', 'Number of retry attempts for failed API calls'),
            ('enable_cache', 'true', 'Enable caching of LLM responses'),
            ('cache_ttl', '3600', 'Cache TTL in seconds'),
            ('enable_parallel', 'false', 'Enable parallel processing'),
            ('max_workers', '4', 'Maximum number of worker processes')
        ]
        
        for key, value, description in default_configs:
            cursor.execute('''
                INSERT OR REPLACE INTO configuration (config_key, config_value, description)
                VALUES (?, ?, ?)
            ''', (key, value, description))
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_history_file_path ON review_history(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_history_date ON review_history(review_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_history_path ON project_history(project_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_history_file ON metrics_history(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patch_history_version ON patch_history(patch_version)')
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized successfully: {db_path}")
        
        # Print table information
        print_database_info(db_path)
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def print_database_info(db_path: str):
    """Print information about the created database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n" + "="*50)
        print("Database Initialization Complete")
        print("="*50)
        print(f"Database path: {db_path}")
        print(f"Tables created: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} records")
        
        print("\nDefault configuration:")
        cursor.execute("SELECT config_key, config_value, description FROM configuration")
        configs = cursor.fetchall()
        
        for key, value, description in configs:
            print(f"  - {key}: {value}")
            if description:
                print(f"    {description}")
        
        print("="*50)
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to print database info: {e}")

def reset_database(db_path: str = "database.db"):
    """
    Reset the database by dropping all tables and recreating them.
    
    Args:
        db_path: Path to the database file
    """
    try:
        if os.path.exists(db_path):
            # Create backup before reset
            backup_path = f"{db_path}.backup"
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"📦 Created backup: {backup_path}")
            
            os.remove(db_path)
            logger.info(f"Removed existing database: {db_path}")
        
        init_database(db_path)
        logger.info("Database reset completed")
        
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise

def migrate_database(db_path: str = "database.db"):
    """
    Migrate existing database to new schema.
    
    Args:
        db_path: Path to the database file
    """
    try:
        if not os.path.exists(db_path):
            print("❌ Database does not exist. Run init_database first.")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current schema version
        cursor.execute("PRAGMA user_version")
        current_version = cursor.fetchone()[0]
        
        print(f"🔄 Current database version: {current_version}")
        
        # Apply migrations
        migrations = [
            # Migration 1: Add new columns to review_history
            """
            ALTER TABLE review_history ADD COLUMN llm_provider TEXT;
            ALTER TABLE review_history ADD COLUMN model_used TEXT;
            ALTER TABLE review_history ADD COLUMN review_duration REAL DEFAULT 0.0;
            """,
            
            # Migration 2: Add new columns to project_history
            """
            ALTER TABLE project_history ADD COLUMN git_repo_url TEXT;
            ALTER TABLE project_history ADD COLUMN git_commit_hash TEXT;
            """,
            
            # Migration 3: Add status column to requirements_history
            """
            ALTER TABLE requirements_history ADD COLUMN status TEXT DEFAULT 'pending';
            ALTER TABLE requirements_history ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
            """
        ]
        
        for i, migration in enumerate(migrations, 1):
            if current_version < i:
                print(f"🔄 Applying migration {i}...")
                try:
                    cursor.executescript(migration)
                    print(f"✅ Migration {i} applied successfully")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⚠️  Migration {i} skipped (columns already exist)")
                    else:
                        raise
        
        # Update schema version
        cursor.execute(f"PRAGMA user_version = {len(migrations)}")
        
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed")
        
    except Exception as e:
        logger.error(f"Failed to migrate database: {e}")
        raise

def main():
    """Main function for database initialization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize AI Code Review Agent database")
    parser.add_argument("--db-path", default="database.db", help="Database file path")
    parser.add_argument("--reset", action="store_true", help="Reset existing database")
    parser.add_argument("--migrate", action="store_true", help="Migrate existing database")
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            reset_database(args.db_path)
        elif args.migrate:
            migrate_database(args.db_path)
        else:
            init_database(args.db_path)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 