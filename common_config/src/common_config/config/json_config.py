from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..utils.exceptions import CommonConfigError


def load_config(path: str | Path, required: bool = True) -> dict[str, Any]:
    """Load a JSON config file.

    Args:
        path: File path to JSON config.
        required: If True and file is missing, raise CommonConfigError. If False, return {} when missing.

    Returns:
        Parsed dict.
    """
    p = Path(path)
    if not p.exists():
        if required:
            raise CommonConfigError(f"Config file not found: {p}")
        return {}

    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise CommonConfigError(f"Invalid JSON in {p}: {e}") from e


def load_app_config(
    base_dir: str | Path | None = None,
    filename: str = "config/app_config.json",
    required: bool = False,
) -> dict[str, Any]:
    """Load a conventional application config from config/app_config.json.

    Args:
        base_dir: Directory to resolve from (defaults to current working directory).
        filename: Relative JSON path under base_dir.
        required: If True, raise if missing; else return {} when not present.

    Returns:
        Parsed dict.
    """
    root = Path(base_dir) if base_dir else Path.cwd()
    return load_config(root / filename, required=required)


def load_shared_config(filename: str = "app_config.json", required: bool = False) -> dict[str, Any]:
    """Load shared config from shared_config/ directory.

    Args:
        filename: Config file name in shared_config/ directory.
        required: If True, raise if missing; else return {} when not present.

    Returns:
        Parsed dict.
    """
    # Try to find shared_config relative to common_config package
    shared_dir = Path(__file__).parent.parent.parent.parent.parent / "shared_config"
    return load_config(shared_dir / filename, required=required)
