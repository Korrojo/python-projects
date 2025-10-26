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


def main() -> None:
    parser = argparse.ArgumentParser(description="Import latest JSONL export into local MongoDB (Mac-friendly)")
    parser.add_argument("--env", default="local", help="Target environment (e.g., local)")
    parser.add_argument("--collection", required=True, help="Collection name (e.g., Patients)")
    parser.add_argument(
        "--in_dir",
        default="",
        help="Input directory; defaults to BACKUP_DIR or ~/Backups/local",
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
    logger.info("Resolved input directory (in_dir): %s", cfg.in_dir)

    # Perform import (returns None if nothing to do)
    result = None
    try:
        result = import_latest_file(
            uri=cfg.mongodb_uri,
            database=cfg.database_name,
            collection=cfg.collection_name,
            in_dir=cfg.in_dir,
            apply_indexes=(not args.no_apply_indexes),
        )
    except Exception as e:
        logger.exception("Unexpected error during import: %s", e)
        sys.exit(2)

    if result is None:
        logger.info(
            "No file imported. Hint: expected patterns under %s: export/YYYYMMDD_*_export_%s.json (new) OR YYYYMM_*_export_%s.json (old). See debug lines for patterns tried.",
            cfg.in_dir,
            cfg.collection_name,
            cfg.collection_name,
        )
        return

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
        f"file={result.file_path}",
        f"rows={result.rows_imported}",
        f"duration={duration_str}",
        "****************************************************",
    ]
    for line in summary_lines:
        logger.info(line)


if __name__ == "__main__":
    main()
