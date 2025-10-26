from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..utils.exceptions import ValidationError
from .settings import get_settings


class ConfigManager:
    """Compatibility-oriented config manager backed by Pydantic settings.

    Provides `get_env` and `get_path` methods expected by existing projects.
    """

    _ENV_TO_SETTINGS = {
        "DB1_MONGODB_URI": "db1_mongodb_uri",
        "DB1_DATABASE_NAME": "db1_database_name",
        "DB2_MONGODB_URI": "db2_mongodb_uri",
        "DB2_DATABASE_NAME": "db2_database_name",
    }

    def __init__(self) -> None:
        self._settings = get_settings()

    def get_env(self, key: str, required: bool = False, default: Any | None = None) -> Any:
        # First check raw environment
        val = os.environ.get(key)
        if val is not None and val != "":
            return val

        # Fallback to mapped settings
        mapped = self._ENV_TO_SETTINGS.get(key)
        if mapped:
            val = getattr(self._settings, mapped, None)
            if val not in (None, ""):
                return val

        if required:
            raise ValidationError(f"Missing required environment variable: {key}", field=key)
        return default

    def get_path(self, key: str) -> str:
        key = key.lower()
        if key == "data_input":
            return str(self._settings.paths.data_input)
        if key == "data_output":
            return str(self._settings.paths.data_output)
        if key == "logs":
            return str(self._settings.paths.logs)
        if key == "temp":
            return str(self._settings.paths.temp)
        if key == "archive":
            return str(self._settings.paths.archive)
        # Default to CWD for unrecognized keys
        return str(Path.cwd())
