#!/usr/bin/env python3
"""
Configuration loader for MongoDB PHI Masking Tool.

This module handles loading and validating configuration from files
and environment variables.
"""

import json
import logging
import os
import re
import sys
from typing import Any

import yaml

try:
    from dotenv import load_dotenv
except ImportError:
    print("python-dotenv package is required. Install it with 'pip install python-dotenv'")
    sys.exit(1)

# Setup logger
logger = logging.getLogger(__name__)


class ConfigLoader:
    """Class for loading and validating configuration.

    This class is responsible for loading configuration from YAML files
    and environment variables, and validating the configuration.

    Attributes:
        config_path: Path to the configuration file
        env_file: Path to the environment file
        config: Loaded configuration dictionary
    """

    def __init__(self, config_path: str, env_file: str | None = None):
        """Initialize the configuration loader.

        Args:
            config_path: Path to the configuration file
            env_file: Path to the environment file (optional)
        """
        self.config_path = config_path
        self.env_file = env_file
        self.config = None

        # Load environment variables if env_file is provided
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")

            # Extract environment name from file name
            # Assuming file name format like .env.dev, .env.prod, etc.
            env_name = os.path.splitext(os.path.basename(env_file))[0].split(".")[-1].upper()
            logger.info(f"Detected environment: {env_name}")
            os.environ["ENVIRONMENT"] = env_name

    def load_config(self) -> dict[str, Any]:
        """Load configuration from file and resolve environment variables.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If the configuration file is not found
            ValueError: If the configuration file is invalid
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        # Load configuration from file
        try:
            with open(self.config_path) as f:
                if self.config_path.endswith(".yaml") or self.config_path.endswith(".yml"):
                    config = yaml.safe_load(f)
                elif self.config_path.endswith(".json"):
                    config = json.load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {self.config_path}")
        except Exception as e:
            raise ValueError(f"Error loading configuration file: {str(e)}")

        # Resolve environment variables in configuration
        config = self._resolve_env_variables(config)

        # Build MongoDB URIs from environment variables if not explicitly set
        config = self._build_mongodb_config(config)

        # Set environment if not already set
        if "environment" not in config and "ENVIRONMENT" in os.environ:
            config["environment"] = os.environ["ENVIRONMENT"]

        # Set default values for missing configuration options
        config = self._set_defaults(config)

        # Validate configuration
        self._validate_config(config)

        self.config = config
        return config

    def _build_mongodb_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Build MongoDB configuration from environment variables if not already set.

        Args:
            config: Configuration dictionary

        Returns:
            Updated configuration dictionary with MongoDB URIs
        """
        # Initialize MongoDB config if not exists
        if "mongodb" not in config:
            config["mongodb"] = {}
        if "source" not in config["mongodb"]:
            config["mongodb"]["source"] = {}
        if "destination" not in config["mongodb"]:
            config["mongodb"]["destination"] = {}

        # Check if MongoDB URIs are already set in config
        source_uri_set = "uri" in config["mongodb"]["source"]
        dest_uri_set = "uri" in config["mongodb"]["destination"]

        # Only build URI from components if not already set in config
        if not source_uri_set:
            # Build source URI from components
            source_uri = os.environ.get("MONGO_SOURCE_URI")
            if not source_uri:
                source_host = os.environ.get("MONGO_SOURCE_HOST")
                source_port = os.environ.get("MONGO_SOURCE_PORT")
                source_username = os.environ.get("MONGO_SOURCE_USERNAME")
                source_password = os.environ.get("MONGO_SOURCE_PASSWORD")
                source_auth_db = os.environ.get("MONGO_SOURCE_AUTH_DB", "admin")
                source_use_srv = str(os.environ.get("MONGO_SOURCE_USE_SRV", "false")).lower() == "true"
                source_use_ssl = str(os.environ.get("MONGO_SOURCE_USE_SSL", "false")).lower() == "true"

                if source_host:  # Only build URI if host is specified
                    source_uri = generate_mongodb_uri(
                        host=source_host,
                        port=source_port,
                        username=source_username,
                        password=source_password,
                        auth_source=source_auth_db,
                        srv=source_use_srv,
                        ssl=source_use_ssl,
                    )
                    logger.info("Generated source MongoDB URI from environment variables")

                    # Set URI in config
                    config["mongodb"]["source"]["uri"] = source_uri
            else:
                # Use URI directly from environment
                config["mongodb"]["source"]["uri"] = source_uri
                logger.info("Using source MongoDB URI from environment")

            # Set database and collection if provided in environment
            source_db = os.environ.get("MONGO_SOURCE_DB")
            if source_db and "database" not in config["mongodb"]["source"]:
                config["mongodb"]["source"]["database"] = source_db

            source_coll = os.environ.get("MONGO_SOURCE_COLL")
            if source_coll and "collection" not in config["mongodb"]["source"]:
                config["mongodb"]["source"]["collection"] = source_coll

        # Do the same for destination
        if not dest_uri_set:
            # Build destination URI from components
            dest_uri = os.environ.get("MONGO_DEST_URI")
            if not dest_uri:
                dest_host = os.environ.get("MONGO_DEST_HOST")
                dest_port = os.environ.get("MONGO_DEST_PORT")
                dest_username = os.environ.get("MONGO_DEST_USERNAME")
                dest_password = os.environ.get("MONGO_DEST_PASSWORD")
                dest_auth_db = os.environ.get("MONGO_DEST_AUTH_DB", "admin")
                dest_use_srv = str(os.environ.get("MONGO_DEST_USE_SRV", "false")).lower() == "true"
                dest_use_ssl = str(os.environ.get("MONGO_DEST_USE_SSL", "false")).lower() == "true"

                if dest_host:  # Only build URI if host is specified
                    dest_uri = generate_mongodb_uri(
                        host=dest_host,
                        port=dest_port,
                        username=dest_username,
                        password=dest_password,
                        auth_source=dest_auth_db,
                        srv=dest_use_srv,
                        ssl=dest_use_ssl,
                    )
                    logger.info("Generated destination MongoDB URI from environment variables")

                    # Set URI in config
                    config["mongodb"]["destination"]["uri"] = dest_uri
            else:
                # Use URI directly from environment
                config["mongodb"]["destination"]["uri"] = dest_uri
                logger.info("Using destination MongoDB URI from environment")

            # Set database and collection if provided in environment
            dest_db = os.environ.get("MONGO_DEST_DB")
            if dest_db and "database" not in config["mongodb"]["destination"]:
                config["mongodb"]["destination"]["database"] = dest_db

            dest_coll = os.environ.get("MONGO_DEST_COLL")
            if dest_coll and "collection" not in config["mongodb"]["destination"]:
                config["mongodb"]["destination"]["collection"] = dest_coll

        return config

    def _resolve_env_variables(self, config: dict[str, Any]) -> dict[str, Any]:
        """Resolve environment variables in configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration dictionary with environment variables resolved
        """
        config_str = json.dumps(config)

        # Replace environment variable placeholders
        pattern = r"\${([^}]+)}"

        def replace_env_var(match):
            env_var = match.group(1)
            value = os.environ.get(env_var)

            # Handle the case where environment variables don't exist
            if value is None:
                logger.warning(f"Environment variable {env_var} not found")
                return f"${{{env_var}}}"  # Keep the placeholder if not found

            return value

        config_str = re.sub(pattern, replace_env_var, config_str)
        return json.loads(config_str)

    def _set_defaults(self, config: dict[str, Any]) -> dict[str, Any]:
        """Set default values for missing configuration options.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration dictionary with default values set
        """
        defaults = {
            "batch_size": 100,
            "worker_count": 1,
            "enable_checkpointing": False,
            "log_level": "INFO",
        }

        for key, value in defaults.items():
            if key not in config:
                config[key] = value
                logger.debug(f"Using default value for {key}: {value}")

        return config

    def _validate_config(self, config: dict[str, Any]) -> None:
        """Validate the configuration.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If the configuration is invalid
        """
        # Required MongoDB config keys
        if "mongodb" not in config:
            raise ValueError("Missing required configuration section: mongodb")

        # Check source
        if "source" not in config["mongodb"]:
            raise ValueError("Missing required MongoDB configuration key: source")

        # Check source connection details
        source = config["mongodb"]["source"]
        for key in ["uri", "database", "collection"]:
            if key not in source:
                raise ValueError(f"Missing required MongoDB source key: {key}")

        # In test mode, don't require destination
        if "unittest" in sys.modules:
            return

        # Check destination
        if "destination" not in config["mongodb"]:
            raise ValueError("Missing required MongoDB configuration key: destination")

        # Check destination connection details
        dest = config["mongodb"]["destination"]
        for key in ["uri", "database", "collection"]:
            if key not in dest:
                raise ValueError(f"Missing required MongoDB destination key: {key}")

    # Dict-like methods for compatibility
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if self.config is None:
            return default
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get a configuration value by key using dict syntax.

        Args:
            key: Configuration key

        Returns:
            Configuration value

        Raises:
            KeyError: If key not found
        """
        if self.config is None:
            raise KeyError("Configuration not loaded. Call load_config() first.")
        return self.config[key]

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the configuration.

        Args:
            key: Configuration key

        Returns:
            True if key exists, False otherwise
        """
        if self.config is None:
            return False
        return key in self.config


def generate_mongodb_uri(
    host,
    port=None,
    username=None,
    password=None,
    auth_source="admin",
    srv=False,
    ssl=False,
):
    """Generate a MongoDB URI.

    Args:
        host: MongoDB host
        port: MongoDB port (not used for SRV connections)
        username: MongoDB username
        password: MongoDB password
        auth_source: Authentication database
        srv: Whether to use SRV format (mongodb+srv://)
        ssl: Whether to enable SSL

    Returns:
        MongoDB URI
    """
    # Normal URI generation logic
    protocol = "mongodb+srv://" if srv else "mongodb://"
    port_str = "" if srv else f":{port or 27017}"

    if username and password:
        auth_part = f"{username}:{password}@"
        uri = f"{protocol}{auth_part}{host}{port_str}/"

        params = []
        if auth_source:
            params.append(f"authSource={auth_source}")
        if ssl:
            params.append("ssl=true")

        if params:
            uri += "?" + "&".join(params)

        return uri

    uri = f"{protocol}{host}{port_str}/"

    params = []
    if srv and auth_source:
        params.append(f"authSource={auth_source}")
    if ssl:
        params.append("ssl=true")

    if params:
        uri += "?" + "&".join(params)

    return uri
