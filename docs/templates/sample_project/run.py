import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from common_config.config.settings import get_settings
from common_config.db.connection import MongoDBConnection
from common_config.utils.logger import get_logger, get_run_timestamp, setup_logging


class SimpleConfigManager:
    def __init__(self, uri: str, database: str):
        self._uri = uri
        self._database = database

    def get_mongodb_uri(self) -> str:
        return self._uri

    def get_mongodb_database(self) -> str:
        return self._database


def resolve_input_file(default_name: str, settings) -> Path:
    # Prefer explicit path if provided by env, else fall back to shared input dir / sample_project
    env_path = getattr(settings, "sample_input_csv", None)
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    # shared input path
    path = Path(settings.paths.data_input) / "sample_project" / default_name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def resolve_collection_name(settings) -> str:
    # Allow env override SAMPLE_COLLECTION_NAME_<ENV>, else default to AD_test_<YYYYMMDD>
    override = getattr(settings, "sample_collection_name", None)
    if override:
        return override
    return f"AD_test_{datetime.now().strftime('%Y%m%d')}"


def read_csv_rows(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def dump_json(path: Path, docs: list[dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2, default=str)


def main():
    settings = get_settings()

    # Setup per-project logs folder under shared logs
    log_dir = Path(settings.paths.logs) / "sample_project"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 80)
    logger.info("Starting sample_project run")
    logger.info("Using APP_ENV=%s", os.environ.get("APP_ENV", "(unset)"))
    logger.info("=" * 80)

    if not settings.mongodb_uri or not settings.database_name:
        raise RuntimeError("MONGODB_URI_<ENV> and DATABASE_NAME_<ENV> must be set in shared_config/.env")

    input_path = resolve_input_file(default_name="sample_input.csv", settings=settings)
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    target_collection = resolve_collection_name(settings)
    logger.info("Target collection: %s", target_collection)
    logger.info("Reading CSV: %s", input_path)

    rows = read_csv_rows(input_path)
    logger.info("Loaded %d rows from CSV", len(rows))

    # Add metadata to documents
    batch_ts = get_run_timestamp()
    for r in rows:
        r["_batch_ts"] = batch_ts
        r["_source"] = "sample_project"

    # Connect to Mongo
    cfg = SimpleConfigManager(settings.mongodb_uri, settings.database_name)
    conn = MongoDBConnection(cfg)

    inserted_docs: list[dict[str, Any]] = []

    try:
        conn.connect()
        test = conn.test_connection()
        if not test.get("connected"):
            raise RuntimeError(f"MongoDB connection failed: {test.get('error')}")

        db = conn.get_database()
        coll = db[target_collection]

        if rows:
            result = coll.insert_many(rows)
            logger.info("Inserted %d documents", len(result.inserted_ids))
            # Fetch back those docs by batch tag for dumping
            inserted_docs = list(coll.find({"_batch_ts": batch_ts}))
        else:
            logger.warning("No rows to insert; skipping DB operations")

        out_dir = Path(settings.paths.data_output) / "sample_project"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{batch_ts}_inserted.json"
        dump_json(out_file, inserted_docs)
        logger.info("Wrote JSON dump: %s", out_file)

    finally:
        conn.disconnect()
        logger.info("MongoDB connection closed")


if __name__ == "__main__":
    main()
