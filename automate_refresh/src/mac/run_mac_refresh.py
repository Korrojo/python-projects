#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from common_config.config.settings import get_settings
from common_config.utils.logger import get_logger, get_run_timestamp, setup_logging

from .modules.config_loader import resolve_config
from .modules.importer import import_latest_file
from .modules.puller import pull_from_sas


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull from SAS (optional) and import latest JSONL into local MongoDB")
    parser.add_argument("--env", default="local", help="Target environment (e.g., local)")
    parser.add_argument("--collection", required=True, help="Collection name (e.g., Patients)")
    parser.add_argument(
        "--in_dir",
        default="",
        help="Input directory; defaults to BACKUP_DIR or ~/Backups/local",
    )
    parser.add_argument(
        "--sas_url",
        default="",
        help=(
            "Environment key indicating which SAS directory URL to use. "
            "Value (e.g. 'prod' or 'stg') maps to environment variable AZ_SAS_DIR_URL_<UPPER>. "
            "Example: --sas_url prod -> uses $AZ_SAS_DIR_URL_PROD. If not set, the pull step is aborted with an error."
        ),
    )
    parser.add_argument(
        "--no-apply-indexes",
        action="store_true",
        help="Skip applying indexes after import",
    )
    parser.add_argument(
        "--log_dir",
        default="",
        help="Logs directory; overrides default logs/<env>/automate_refresh",
    )
    args = parser.parse_args()

    start_time = datetime.now()
    cfg = resolve_config(env=args.env, collection=args.collection, in_dir=(args.in_dir.strip() or None))
    settings = get_settings()

    if args.log_dir.strip():
        log_dir = args.log_dir.strip()
    else:
        base_logs = os.environ.get("LOG_DIR", "").strip() or str(settings.paths.logs)
        app_env = os.environ.get("APP_ENV", "").strip().lower() or "default"

        def _detect_project_folder() -> str:
            pkg = (__package__ or "").split(".")[0]
            if pkg and pkg.startswith("automate_refresh"):
                return "automate_refresh"
            try:
                here = Path(__file__).resolve()
                for p in here.parents:
                    if p.name.startswith("automate_refresh"):
                        return "automate_refresh"
            except Exception:
                pass
            return ""

        project_sub = _detect_project_folder()
        base_path = Path(base_logs)
        env_path = base_path if base_path.name.lower() == app_env else (base_path / app_env)
        log_dir = str((env_path / project_sub) if project_sub else env_path)

    ts = get_run_timestamp()
    custom_name = f"{ts}_import_{cfg.collection_name}.log"
    setup_logging(log_dir=Path(log_dir), level=settings.log_level, file_name=custom_name)
    logger = get_logger(__name__)

    def _load_sas_from_env(key: str) -> str | None:
        env_var = f"AZ_SAS_DIR_URL_{key}"
        val = os.environ.get(env_var, "").strip()
        if val:
            return val
        # Attempt to load from shared_config/.env if present
        try:
            repo_root = Path(__file__).resolve().parents[2]
            env_path = repo_root / "shared_config" / ".env"
            if env_path.is_file():
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k == env_var:
                        os.environ[env_var] = v
                        return v
        except Exception:
            pass
        return None

    if args.sas_url.strip():
        key = args.sas_url.strip().upper()
        sas_value = _load_sas_from_env(key)
        env_var = f"AZ_SAS_DIR_URL_{key}"
        if not sas_value:
            logger.error(
                "Missing SAS env var %s (key '%s'). Set it or add to shared_config/.env",
                env_var,
                key,
            )
        else:
            logger.info("Using SAS URL from %s", env_var)
            try:
                # For pulling we want the base directory (without forcing 'export') so user can control structure.
                base_dir = os.path.expanduser(cfg.in_dir)
                pull_from_sas(sas_value, base_dir)
            except Exception as e:
                logger.exception("Pull step failed (continuing to import anyway): %s", e)

    result = import_latest_file(
        uri=cfg.mongodb_uri,
        database=cfg.database_name,
        collection=cfg.collection_name,
        in_dir=cfg.in_dir,
        apply_indexes=(not args.no_apply_indexes),
    )

    end_time = datetime.now()
    elapsed = end_time - start_time
    total_seconds = int(elapsed.total_seconds())
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    ss = total_seconds % 60
    duration_str = f"{hh:02d}:{mm:02d}:{ss:02d}"

    log_file = ""
    for h in logger.root.handlers:  # type: ignore[attr-defined]
        try:
            fn = getattr(h, "baseFilename", None)
            if fn:
                log_file = fn
                break
        except Exception:
            pass

    summary_lines = [
        "****************** SUMMARY REPORT ******************",
        f"env={cfg.app_env}",
        f"db={cfg.database_name}",
        f"collection={cfg.collection_name}",
        f"log={log_file}",
        f"file={getattr(result, 'file_path', '')}",
        f"rows={getattr(result, 'rows_imported', 0)}",
        f"duration={duration_str}",
        "****************************************************",
    ]
    for line in summary_lines:
        logger.info(line)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        # Best-effort logging if early failure before logging configured
        sys.stderr.write(f"FATAL ERROR: {exc}\n")
        raise
