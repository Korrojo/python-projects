"""Environment configuration loader for shared_config integration.

This module provides utilities to load environment configurations from the
shared_config directory, supporting multi-environment setups (LOCL, DEV, STG, PROD).

Usage:
    from src.utils.env_config import load_shared_config, get_env_config

    # Load shared configuration
    load_shared_config()

    # Get configuration for specific environment
    config = get_env_config("DEV")
    mongo_uri = config["uri"]
    database = config["database"]
"""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def get_shared_config_path() -> Path:
    """Get path to shared_config directory.

    Returns:
        Path: Path to shared_config/.env file

    Raises:
        FileNotFoundError: If shared_config/.env does not exist
    """
    # Get project root (mongo_phi_masker)
    project_root = Path(__file__).parent.parent.parent

    # Shared config is one level up from project root
    shared_config_path = project_root.parent / "shared_config" / ".env"

    if not shared_config_path.exists():
        msg = (
            f"Shared config not found at {shared_config_path}\n"
            f"Please ensure shared_config/.env exists at the repository root.\n"
            f"Copy from shared_config/.env.example and configure your environments."
        )
        raise FileNotFoundError(msg)

    return shared_config_path


def load_shared_config() -> None:
    """Load environment variables from shared_config/.env.

    This function loads the shared configuration file and makes all
    environment variables available via os.getenv().

    Raises:
        FileNotFoundError: If shared_config/.env does not exist
    """
    shared_config_path = get_shared_config_path()
    load_dotenv(shared_config_path)


def get_available_environments() -> list[str]:
    """Get list of available environments.

    Returns:
        List of environment codes (e.g., ['LOCL', 'DEV', 'STG', 'PROD'])
    """
    return ["LOCL", "DEV", "STG", "TRNG", "PERF", "PRPRD", "PROD"]


def get_env_config(env: str, database: str | None = None) -> dict[str, Any]:
    """Get configuration for a specific environment.

    Args:
        env: Environment code (LOCL, DEV, STG, PROD, etc.)
        database: Optional database name override. If not provided,
                 uses DATABASE_NAME_{env} from shared config.

    Returns:
        Dictionary with environment configuration:
        {
            "env": "DEV",
            "uri": "mongodb://localhost:27017",
            "database": "devdb",
            "backup_dir": "/path/to/backups",
            "log_dir": "/path/to/logs"  # Optional
        }

    Raises:
        ValueError: If environment is not configured
        EnvironmentError: If required environment variables are missing
    """
    env = env.upper()

    if env not in get_available_environments():
        msg = f"Invalid environment: {env}\n" f"Available environments: {', '.join(get_available_environments())}"
        raise ValueError(msg)

    # Load shared config if not already loaded
    if not os.getenv(f"MONGODB_URI_{env}"):
        load_shared_config()

    # Get MongoDB URI
    uri = os.getenv(f"MONGODB_URI_{env}")
    if not uri:
        msg = (
            f"MongoDB URI not configured for {env} environment.\n" f"Please set MONGODB_URI_{env} in shared_config/.env"
        )
        raise EnvironmentError(msg)

    # Get database name (use override or default from env)
    if database is None:
        database = os.getenv(f"DATABASE_NAME_{env}")
        if not database:
            msg = (
                f"Database name not configured for {env} environment.\n"
                f"Please set DATABASE_NAME_{env} in shared_config/.env\n"
                f"Or provide --src-db/--dst-db argument."
            )
            raise EnvironmentError(msg)

    # Get optional backup directory
    backup_dir = os.getenv(f"BACKUP_DIR_{env}")

    # Get optional log directory
    log_dir = os.getenv(f"LOG_DIR_{env}")

    return {
        "env": env,
        "uri": uri,
        "database": database,
        "backup_dir": backup_dir,
        "log_dir": log_dir,
    }


def get_source_and_target_config(
    src_env: str,
    dst_env: str,
    src_db: str | None = None,
    dst_db: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Get source and destination configurations for masking workflow.

    This is a convenience function that gets configurations for both
    source and destination environments.

    Args:
        src_env: Source environment code (LOCL, DEV, STG, PROD)
        dst_env: Destination environment code (LOCL, DEV, STG, PROD)
        src_db: Optional source database name override
        dst_db: Optional destination database name override

    Returns:
        Tuple of (source_config, destination_config) dictionaries

    Example:
        >>> src_cfg, dst_cfg = get_source_and_target_config("LOCL", "DEV")
        >>> print(src_cfg["uri"], src_cfg["database"])
        mongodb://localhost:27017 localdb-unmasked
        >>> print(dst_cfg["uri"], dst_cfg["database"])
        mongodb://localhost:27017 devdb
    """
    source_config = get_env_config(src_env, src_db)
    target_config = get_env_config(dst_env, dst_db)

    return source_config, target_config


def validate_env_config(env: str) -> tuple[bool, list[str]]:
    """Validate that all required configuration exists for an environment.

    Args:
        env: Environment code to validate

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if configuration is complete
        - error_messages: List of error messages (empty if valid)
    """
    env = env.upper()
    errors = []

    # Check if environment is valid
    if env not in get_available_environments():
        errors.append(f"Invalid environment: {env}. " f"Valid options: {', '.join(get_available_environments())}")
        return False, errors

    # Load shared config
    try:
        load_shared_config()
    except FileNotFoundError as e:
        errors.append(str(e))
        return False, errors

    # Check MongoDB URI
    uri = os.getenv(f"MONGODB_URI_{env}")
    if not uri:
        errors.append(
            f"Missing MONGODB_URI_{env} in shared_config/.env. "
            f"Please configure MongoDB connection URI for {env} environment."
        )

    # Check database name
    database = os.getenv(f"DATABASE_NAME_{env}")
    if not database:
        errors.append(
            f"Missing DATABASE_NAME_{env} in shared_config/.env. "
            f"Please configure database name for {env} environment."
        )

    is_valid = len(errors) == 0
    return is_valid, errors


def setup_masking_env_vars(
    src_env: str,
    dst_env: str,
    src_db: str | None = None,
    dst_db: str | None = None,
) -> tuple[str, str, str, str]:
    """Set up environment variables for masking workflow.

    This function loads environment configurations and sets the
    environment variables expected by masking.py.

    Args:
        src_env: Source environment code (LOCL, DEV, STG, PROD)
        dst_env: Destination environment code
        src_db: Optional source database override
        dst_db: Optional destination database override

    Returns:
        Tuple of (src_uri, src_db, dst_uri, dst_db)

    Raises:
        ValueError: If environments are invalid
        EnvironmentError: If required config is missing
    """
    # Get source and destination configs
    src_config, dst_config = get_source_and_target_config(src_env, dst_env, src_db, dst_db)

    # Set environment variables for source - use full URI
    os.environ["MONGO_SOURCE_URI"] = src_config["uri"]
    os.environ["MONGO_SOURCE_DB"] = src_config["database"]
    os.environ["MONGO_SOURCE_COLL"] = ""  # Will be set by masking.py

    # Set environment variables for destination - use full URI
    os.environ["MONGO_DEST_URI"] = dst_config["uri"]
    os.environ["MONGO_DEST_DB"] = dst_config["database"]
    os.environ["MONGO_DEST_COLL"] = ""  # Will be set by masking.py

    # Optional: Set backup and log directories if provided
    if src_config["backup_dir"]:
        os.environ["BACKUP_DIR_SOURCE"] = src_config["backup_dir"]
    if dst_config["backup_dir"]:
        os.environ["BACKUP_DIR_DEST"] = dst_config["backup_dir"]

    return (
        src_config["uri"],
        src_config["database"],
        dst_config["uri"],
        dst_config["database"],
    )


def print_env_config(env: str) -> None:
    """Print environment configuration for debugging.

    Args:
        env: Environment code to display
    """
    try:
        config = get_env_config(env)
        print(f"\n{'='*70}")
        print(f"Environment Configuration: {env}")
        print(f"{'='*70}")
        print(f"MongoDB URI:  {config['uri']}")
        print(f"Database:     {config['database']}")
        if config["backup_dir"]:
            print(f"Backup Dir:   {config['backup_dir']}")
        if config["log_dir"]:
            print(f"Log Dir:      {config['log_dir']}")
        print(f"{'='*70}\n")
    except (ValueError, EnvironmentError) as e:
        print(f"\n❌ Error loading {env} configuration:")
        print(f"   {e}\n")
