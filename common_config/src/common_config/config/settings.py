from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppPaths(BaseModel):
    data_input: Path = Path("data/input")
    data_output: Path = Path("data/output")
    logs: Path = Path("logs")
    temp: Path = Path("temp")
    archive: Path = Path("archive")


class AppSettings(BaseSettings):
    """Application settings loaded from environment variables and .env.

    Environment variables can override .env values. The default .env path is config/.env in the project root.
    """

    # Mongo settings (optional; projects may not use them)

    # Generic MongoDB settings
    mongodb_uri: str | None = None
    database_name: str | None = None
    collection_name: str | None = None
    collection_before: str | None = None
    collection_after: str | None = None

    # Other common settings
    input_excel_file: str | None = None
    log_level: str = "INFO"

    # Paths
    paths: AppPaths = AppPaths()

    model_config = SettingsConfigDict(
        # We manage dotenv loading order ourselves in get_settings() to ensure
        # local project files can override shared/global defaults.
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    def ensure_dirs(self) -> None:
        self.paths.data_input.mkdir(parents=True, exist_ok=True)
        self.paths.data_output.mkdir(parents=True, exist_ok=True)
        self.paths.logs.mkdir(parents=True, exist_ok=True)
        self.paths.temp.mkdir(parents=True, exist_ok=True)
        self.paths.archive.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> AppSettings:
    # Load environment in the following precedence (OS env always wins):
    # shared .env < config/.env < .env < OS env
    merged: dict[str, str] = {}

    # Check for shared config in this order:
    # 1) COMMON_CONFIG_ENV_FILE env var
    # 2) Default location: ../shared_config/.env relative to current project
    shared_env = os.environ.get("COMMON_CONFIG_ENV_FILE")
    if not shared_env:
        # Try default shared config location
        default_shared = Path(__file__).parent.parent.parent.parent.parent / "shared_config" / ".env"
        if default_shared.exists():
            shared_env = str(default_shared)

    try:
        if shared_env and Path(shared_env).exists():
            for k, v in dotenv_values(shared_env).items():
                if v is not None:
                    merged[k] = v
    except Exception:
        # Ignore errors reading the shared file
        pass

    for local in (Path("config/.env"), Path(".env")):
        if local.exists():
            for k, v in dotenv_values(local).items():
                if v is not None:
                    merged[k] = v

    # Resolve environment-specific variables if APP_ENV is provided.
    # Example: if APP_ENV=stg and only MONGODB_URI_STG is defined, set MONGODB_URI
    # so existing code that reads MONGODB_URI continues to work without changes.
    try:
        env_name = (os.environ.get("APP_ENV") or merged.get("APP_ENV") or "").strip()
        if env_name:
            suffix = env_name.upper()
            # Base keys to resolve from their ENV-suffixed counterparts
            base_keys = [
                "MONGODB_URI",
                "DATABASE_NAME",
                "COLLECTION_NAME",
                "COLLECTION_BEFORE",
                "COLLECTION_AFTER",
                "AZ_SAS_DIR_URL",
                "BACKUP_DIR",
                "LOG_DIR",
            ]
            for base in base_keys:
                base_present = (base in os.environ) or (base in merged)
                env_key = f"{base}_{suffix}"
                # Prefer OS env if present; else use merged
                cand = os.environ.get(env_key)
                if cand is None:
                    cand = merged.get(env_key)
                if (not base_present) and cand not in (None, ""):
                    merged[base] = cand
    except Exception:
        # Never fail settings loading due to resolution logic
        pass

    # Apply merged values only where OS env doesn't already define them
    for k, v in merged.items():
        if k not in os.environ:
            os.environ[k] = v

    settings = AppSettings()
    settings.ensure_dirs()
    return settings
