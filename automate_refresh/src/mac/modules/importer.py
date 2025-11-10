from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from bson.json_util import loads as bson_loads
from pymongo import InsertOne

from common_config.db.connection import MongoDBConnection
from common_config.utils.logger import get_logger

from .indexer import apply_indexes as apply_indexes_util


@dataclass
class ImportResult:
    file_path: str
    rows_imported: int


def _latest_file(in_dir: str, collection: str) -> str | None:
    """Return newest matching file for the given collection using filename timestamps.

    Strategy:
      1. Gather candidates using existing pattern priority.
      2. Parse timestamp from filename (YYYYMMDD_HHMMSS or YYYYMM_HHMMSS).
      3. Sort by parsed timestamp DESC, then mtime DESC as tie-breaker.
      4. Debug log ordering for transparency.
    """
    logger = get_logger(__name__)
    in_dir = os.path.expanduser(in_dir)
    export_dir = in_dir if os.path.basename(in_dir) == "export" else os.path.join(in_dir, "export")
    ymd = datetime.now().strftime("%Y%m%d")
    year_month = datetime.now().strftime("%Y%m")

    candidates: list[str] = []

    # 1. Day-specific
    pattern_day = os.path.join(export_dir, f"{ymd}_*_export_{collection}.json")
    day_files = glob.glob(pattern_day)
    if day_files:
        logger.debug("Pattern(day)=%s matches=%d", pattern_day, len(day_files))
        candidates.extend(day_files)

    # 2. Any date in export dir
    if not candidates:
        pattern_any = os.path.join(export_dir, f"*_export_{collection}.json")
        any_files = glob.glob(pattern_any)
        rx_full = re.compile(r"^(\d{8})_(\d{6})_export_" + re.escape(collection) + r"\.json$")
        rx_month = re.compile(r"^(\d{6})_(\d{6})_export_" + re.escape(collection) + r"\.json$")
        filtered = [f for f in any_files if rx_full.search(os.path.basename(f)) or rx_month.search(os.path.basename(f))]
        if filtered:
            logger.debug(
                "Pattern(any)=%s raw=%d filtered(valid)=%d",
                pattern_any,
                len(any_files),
                len(filtered),
            )
            candidates.extend(filtered)

    # 3. Legacy pattern
    if not candidates:
        pattern_old = os.path.join(in_dir, f"{year_month}_*_export_{collection}.json")
        old_files = glob.glob(pattern_old)
        if old_files:
            logger.debug("Pattern(old)=%s matches=%d", pattern_old, len(old_files))
            candidates.extend(old_files)

    if not candidates:
        logger.debug("No matching files found under %s for collection %s", in_dir, collection)
        return None

    rx_full = re.compile(r"^(\d{8})_(\d{6})_export_" + re.escape(collection) + r"\.json$")
    rx_month = re.compile(r"^(\d{6})_(\d{6})_export_" + re.escape(collection) + r"\.json$")

    def parse_ts(path: str) -> int:
        base = os.path.basename(path)
        m = rx_full.match(base)
        if m:
            return int(m.group(1) + m.group(2))  # YYYYMMDD + HHMMSS
        m2 = rx_month.match(base)
        if m2:
            return int(m2.group(1) + "01" + m2.group(2))  # Assume day=01
        return 0

    records: list[tuple[str, int, float]] = []
    for f in candidates:
        try:
            records.append((f, parse_ts(f), os.path.getmtime(f)))
        except Exception:
            continue
    if not records:
        return candidates[0]

    records.sort(key=lambda r: (r[1], r[2]), reverse=True)
    logger.debug("Candidate ordering (top first):")
    for p, ts_val, mt in records:
        logger.debug(
            "  file=%s | ts=%s | mtime=%s",
            os.path.basename(p),
            ts_val,
            datetime.fromtimestamp(mt).isoformat(timespec="seconds"),
        )
    return records[0][0]


def _apply_indexes(conn: MongoDBConnection, database: str, collection: str, repo_root: Path) -> int:
    return apply_indexes_util(conn, database, collection, repo_root)


def import_latest_file(
    uri: str, database: str, collection: str, in_dir: str, apply_indexes: bool = True
) -> ImportResult | None:
    logger = get_logger(__name__)
    conn = MongoDBConnection(
        type(
            "Cfg",
            (),
            {
                "get_mongodb_uri": lambda self=uri: uri,
                "get_mongodb_database": lambda self=database: database,
            },
        )()
    )

    info = conn.test_connection()
    if info.get("connected"):
        logger.info(
            "Connected to MongoDB | db=%s | version=%s | collections=%s | rt=%sms",
            info.get("database_name"),
            info.get("server_version"),
            info.get("collections_count"),
            info.get("response_time_ms"),
        )
    else:
        logger.warning("MongoDB ping failed: %s", info.get("error"))

    try:
        target = _latest_file(in_dir, collection)
        if not target:
            logger.info(
                "No matching export file found in %s for collection %s (nothing to do)",
                in_dir,
                collection,
            )
            return None
        logger.info("Latest file found: %s", target)

        db = conn.get_database()
        coll = db[collection]
        if collection in db.list_collection_names():
            coll.drop()
            logger.info("Dropped existing collection %s.%s", database, collection)

        rows = _load_jsonl_file(coll, target)

        logger.info("Import complete: %s (rows inserted: %s)", target, rows)

        if apply_indexes:
            repo_root = Path(__file__).resolve().parents[3]
            _apply_indexes(conn, database, collection, repo_root)

        return ImportResult(file_path=target, rows_imported=rows)
    finally:
        conn.disconnect()


def _load_jsonl_file(coll, file_path: str, batch_size: int = 1000) -> int:
    logger = get_logger(__name__)
    rows = 0
    with open(file_path, encoding="utf-8") as fh:
        batch: list = []
        for line in fh:
            line = line.strip()
            if not line:
                continue
            doc = bson_loads(line)
            batch.append(InsertOne(doc))
            if len(batch) >= batch_size:
                res = coll.bulk_write(batch, ordered=False)
                rows += res.inserted_count
                batch.clear()
        if batch:
            res = coll.bulk_write(batch, ordered=False)
            rows += res.inserted_count
    logger.info("Inserted %s rows from %s", rows, file_path)
    return rows
