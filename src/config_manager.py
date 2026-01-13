"""
Configuration manager for loading and validating application configuration.
Supports both JSON config files (local) and environment variables (Lambda).
"""

import json
import os
from pathlib import Path
from src.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """
    Manages application configuration from JSON files or environment variables.
    """

    def __init__(self, config_file=None):
        """
        Initialize ConfigManager.

        Args:
            config_file (str, optional): Path to config JSON file. If None, uses env vars.
        """
        self.config = {}
        self.config_file = config_file or os.getenv('CONFIG_FILE', 'config/config.json')
        self._load_config()

    def _load_config(self):
        """
        Load configuration from file or environment variables.
        Priority: Environment variables > Config file
        """
        # Try loading from config file first
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
                self.config = {}
        else:
            logger.info("Config file not found, using environment variables")

        # Override with environment variables if present (for Lambda)
        self._load_from_env()

    def _load_from_env(self):
        """
        Load or override configuration from environment variables.
        """
        # Database configuration
        if os.getenv('DB_HOST'):
            if 'database' not in self.config:
                self.config['database'] = {}
            self.config['database']['host'] = os.getenv('DB_HOST')
            self.config['database']['database'] = os.getenv('DB_NAME')
            self.config['database']['username'] = os.getenv('DB_USER')
            self.config['database']['password'] = os.getenv('DB_PASSWORD')
            self.config['database']['port'] = int(os.getenv('DB_PORT', '5432'))
            logger.info("Database configuration loaded from environment variables")

        # Processing configuration
        if os.getenv('CHUNK_SIZE'):
            if 'processing' not in self.config:
                self.config['processing'] = {}
            self.config['processing']['chunk_size'] = int(os.getenv('CHUNK_SIZE'))

        if os.getenv('BATCH_COMMIT_SIZE'):
            if 'processing' not in self.config:
                self.config['processing'] = {}
            self.config['processing']['batch_commit_size'] = int(os.getenv('BATCH_COMMIT_SIZE', '1000'))

        # AWS configuration
        if os.getenv('AWS_REGION'):
            if 'aws' not in self.config:
                self.config['aws'] = {}
            self.config['aws']['region'] = os.getenv('AWS_REGION')

    def validate(self):
        """
        Validate that all required configuration parameters are present.

        Raises:
            ValueError: If required configuration is missing
        """
        required_db_fields = ['host', 'database', 'username', 'password', 'port']

        if 'database' not in self.config:
            raise ValueError("Database configuration is missing")

        for field in required_db_fields:
            if field not in self.config['database']:
                raise ValueError(f"Database field '{field}' is missing from configuration")

        if 'processing' not in self.config:
            raise ValueError("Processing configuration is missing")

        if 'chunk_size' not in self.config['processing']:
            raise ValueError("chunk_size is missing from processing configuration")

        logger.info("Configuration validation passed")

    def get_database_config(self):
        """
        Get database configuration.

        Returns:
            dict: Database configuration parameters
        """
        return self.config.get('database', {})

    def get_chunk_size(self):
        """
        Get chunk size for text truncation.

        Returns:
            int: Number of words per chunk
        """
        return self.config.get('processing', {}).get('chunk_size', 300)

    def get_batch_commit_size(self):
        """
        Get batch commit size.

        Returns:
            int: Number of inserts before commit
        """
        return self.config.get('processing', {}).get('batch_commit_size', 1000)

    def get_aws_region(self):
        """
        Get AWS region.

        Returns:
            str: AWS region
        """
        return self.config.get('aws', {}).get('region', 'us-east-1')

    def get_admin_list(self):
        """
        Get list of administrators.

        Returns:
            list: List of admin emails/IDs
        """
        return self.config.get('admin_list', [])
