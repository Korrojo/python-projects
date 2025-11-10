#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

from common_config.config.settings import get_settings
from common_config.utils.logger import get_logger, get_run_timestamp, setup_logging

from .modules.config_loader import resolve_config
from .modules.exporter import export_sample


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a sample of a MongoDB collection to JSON (Windows-friendly)")
    parser.add_argument("--env", required=True, help="Target environment (e.g., prod, stg, trng)")
    parser.add_argument("--collection", required=True, help="Collection name (e.g., Patients)")
    parser.add_argument(
        "--fraction", type=float, default=0.25, help="Sample fraction (0-1). Ignored if --limit provided"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Absolute number of documents to sample (overrides --fraction)"
    )
    parser.add_argument("--out_dir", default="", help="Output directory; defaults to env BACKUP_DIR")
    parser.add_argument("--log_dir", default="", help="Logs directory; overrides default logs/<env>/automate_refresh")

    args = parser.parse_args()
    start_time = datetime.now()
    cfg = resolve_config(env=args.env, collection=args.collection, out_dir=(args.out_dir.strip() or None))
    settings = get_settings()

    # Resolve logs dir with env + project auto-detection
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
    custom_name = f"{ts}_export_{cfg.collection_name}.log"
    setup_logging(log_dir=Path(log_dir), level=settings.log_level, file_name=custom_name)
    logger = get_logger(__name__)

    result = export_sample(
        uri=cfg.mongodb_uri,
        database=cfg.database_name,
        collection_name=cfg.collection_name,
        fraction=float(args.fraction),
        limit=(args.limit if args.limit and args.limit > 0 else None),
        out_dir=cfg.out_dir,
    )

    end_time = datetime.now()
    elapsed = end_time - start_time
    total_seconds = int(elapsed.total_seconds())
    hh = total_seconds // 3600
    mm = (total_seconds % 3600) // 60
    ss = total_seconds % 60
    duration_str = f"{hh:02d}:{mm:02d}:{ss:02d}"

    # Determine current log file path
    log_file = ""
    for h in logger.root.handlers:  # type: ignore[attr-defined]
        try:
            fn = getattr(h, "baseFilename", None)
            if fn:
                log_file = fn
                break
        except Exception:
            pass

    # Print ASCII summary block
    summary_lines = [
        "****************** SUMMARY REPORT ******************",
        f"env={cfg.app_env}",
        f"db={cfg.database_name}",
        f"collection={cfg.collection_name}",
        f"Total rows={result.total_docs}",
        f"sampling size={result.sample_size}",
        f"sampling fraction={result.fraction_used}",
        f"log={log_file}",
        f"file={result.out_path}",
        f"rows={result.written}",
        f"duration={duration_str}",
        "****************************************************",
    ]
    for line in summary_lines:
        logger.info(line)


if __name__ == "__main__":
    main()
