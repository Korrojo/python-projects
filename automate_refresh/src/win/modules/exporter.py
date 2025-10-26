from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import datetime

from bson.json_util import dumps as bson_dumps

from common_config.db.connection import MongoDBConnection
from common_config.utils.logger import get_logger


@dataclass
class ExportResult:
    out_path: str
    written: int
    sample_size: int
    total_docs: int
    fraction_used: float


class _Cfg:
    def __init__(self, uri: str, database: str) -> None:
        self._uri = uri
        self._db = database

    def get_mongodb_uri(self) -> str:
        return self._uri

    def get_mongodb_database(self) -> str:
        return self._db


def _count_docs(collection) -> int:
    try:
        return int(collection.estimated_document_count())
    except Exception:
        try:
            return int(collection.count_documents({}))
        except Exception:
            return 0


def export_sample(
    uri: str,
    database: str,
    collection_name: str,
    fraction: float = 0.25,
    limit: int | None = None,
    out_dir: str | None = None,
) -> ExportResult:
    logger = get_logger(__name__)
    conn = MongoDBConnection(_Cfg(uri, database))

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
        db = conn.get_database()
        collection = db[collection_name]

        total = _count_docs(collection)
        if total == 0:
            raise SystemExit("Source collection appears empty; nothing to export")

        if limit is not None and limit > 0:
            sample_size = int(limit)
        else:
            sample_size = max(1, int(total * float(fraction)))

        logger.info("Total=%s, sampling size=%s (fraction=%s)", total, sample_size, fraction)

        pipeline = [{"$sample": {"size": sample_size}}]
        cursor = collection.aggregate(pipeline, allowDiskUse=True)

        if not out_dir:
            raise ValueError("out_dir is required for export_sample")
        os.makedirs(out_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m_%H%M%S")
        filename = f"{ts}_export_{collection_name}.json"
        out_path = os.path.join(out_dir, filename)

        written = 0
        logger.info("Writing %s documents to %s", sample_size, out_path)
        with open(out_path, "w", encoding="utf-8") as fh:
            for doc in cursor:
                fh.write(bson_dumps(doc))
                fh.write("\n")
                written += 1

        logger.info("Export complete: %s (rows written: %s)", out_path, written)
        # --- Zip the exported JSON file ---
        zip_path = out_path + ".zip"
        shutil.make_archive(out_path, "zip", root_dir=os.path.dirname(out_path), base_dir=os.path.basename(out_path))
        logger.info("Compressed export: %s", zip_path)
        # --- Remove the original JSON file after zipping ---
        os.remove(out_path)
        return ExportResult(
            out_path=zip_path,
            written=written,
            sample_size=sample_size,
            total_docs=total,
            fraction_used=float(fraction),
        )
    finally:
        conn.disconnect()
