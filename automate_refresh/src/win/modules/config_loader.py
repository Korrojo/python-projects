from __future__ import annotations

import os
from dataclasses import dataclass

from common_config.config.settings import get_settings


@dataclass
class ResolvedConfig:
    app_env: str
    mongodb_uri: str
    database_name: str
    collection_name: str
    out_dir: str


def normalize_env(env: str) -> str:
    el = (env or "").strip().lower()
    if el in {"local", "locl", "loc"}:
        return "LOCL"
    return (env or "").strip().upper()


def resolve_config(env: str, collection: str, out_dir: str | None = None) -> ResolvedConfig:
    os.environ["APP_ENV"] = normalize_env(env)
    settings = get_settings()

    # Out directory precedence: CLI > BACKUP_DIR env > Windows default > archive fallback
    if out_dir and out_dir.strip():
        resolved_out = out_dir.strip()
    else:
        env_dir = os.environ.get("BACKUP_DIR", "").strip()
        if env_dir:
            resolved_out = env_dir
        elif os.name == "nt":
            resolved_out = r"F:\\mongodrive\\backups\\local"
        else:
            resolved_out = str(settings.paths.archive / "mongo_exports")

    if not settings.mongodb_uri or not settings.database_name:
        raise RuntimeError(
            "mongodb_uri/database_name not resolved from shared .env for APP_ENV='{}'".format(
                os.environ.get("APP_ENV", "")
            )
        )

    return ResolvedConfig(
        app_env=os.environ["APP_ENV"],
        mongodb_uri=settings.mongodb_uri,
        database_name=settings.database_name,
        collection_name=collection,
        out_dir=resolved_out,
    )
