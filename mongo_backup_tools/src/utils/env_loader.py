"""Environment configuration loader for MongoDB connection parameters.

This module loads environment-specific configuration from the shared_config/.env file
following the repository's standard pattern:
- Environment names: LOCL, DEV, STG, TRNG, PERF, PRPRD, PROD
- Variable pattern: MONGODB_URI_{ENV}, DATABASE_NAME_{ENV}
"""

import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv


class EnvironmentConfigError(Exception):
    """Raised when environment configuration cannot be loaded."""

    pass


def get_shared_config_path() -> Path:
    """Get the path to the shared_config directory.

    Returns:
        Path to shared_config directory

    Raises:
        EnvironmentConfigError: If shared_config directory not found
    """
    # From mongo_backup_tools, go up to python-projects, then to shared_config
    current_file = Path(__file__).resolve()
    repo_root = current_file.parent.parent.parent  # src/utils -> src -> mongo_backup_tools
    python_projects_root = repo_root.parent
    shared_config_path = python_projects_root / "shared_config"

    if not shared_config_path.exists():
        raise EnvironmentConfigError(f"shared_config directory not found at: {shared_config_path}")

    return shared_config_path


def load_env_config(env: Optional[str] = None) -> None:
    """Load environment variables from shared_config/.env file.

    Args:
        env: Environment name (LOCL, DEV, etc.). If None, loads from APP_ENV variable.

    Raises:
        EnvironmentConfigError: If .env file cannot be loaded
    """
    shared_config_path = get_shared_config_path()
    env_file = shared_config_path / ".env"

    if not env_file.exists():
        raise EnvironmentConfigError(
            f".env file not found at: {env_file}\n"
            f"Please copy .env.example to .env: cp {shared_config_path}/.env.example {env_file}"
        )

    # Load environment variables
    load_dotenv(env_file, override=True)

    # Validate environment if specified
    if env:
        valid_envs = ["LOCL", "DEV", "STG", "TRNG", "PERF", "PRPRD", "PROD"]
        if env not in valid_envs:
            raise EnvironmentConfigError(f"Invalid environment: {env}. Must be one of: {', '.join(valid_envs)}")


def get_mongo_connection_config(env: str) -> Dict[str, Optional[str]]:
    """Get MongoDB connection configuration for the specified environment.

    Args:
        env: Environment name (LOCL, DEV, STG, TRNG, PERF, PRPRD, PROD)

    Returns:
        Dictionary with connection parameters:
        - uri: MongoDB connection URI
        - database: Database name
        - backup_dir: Backup directory (optional)
        - log_dir: Log directory (optional)

    Raises:
        EnvironmentConfigError: If required configuration is missing
    """
    # Load environment config
    load_env_config(env)

    # Read environment-specific variables
    uri = os.getenv(f"MONGODB_URI_{env}")
    database = os.getenv(f"DATABASE_NAME_{env}")
    backup_dir = os.getenv(f"BACKUP_DIR_{env}")
    log_dir = os.getenv(f"LOG_DIR_{env}")

    # Validate required fields
    if not uri:
        raise EnvironmentConfigError(f"MONGODB_URI_{env} not found in .env file")

    if not database:
        raise EnvironmentConfigError(f"DATABASE_NAME_{env} not found in .env file")

    return {"uri": uri, "database": database, "backup_dir": backup_dir, "log_dir": log_dir}


def get_current_env() -> Optional[str]:
    """Get the current active environment from APP_ENV variable.

    Returns:
        Current environment name, or None if not set
    """
    # First try to load from shared_config/.env
    try:
        load_env_config()
    except EnvironmentConfigError:
        pass  # .env file might not exist yet

    return os.getenv("APP_ENV")
