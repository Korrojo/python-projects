from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pymongo import IndexModel

from common_config.db.connection import MongoDBConnection
from common_config.utils.logger import get_logger

_UNQUOTED_KEY_RE = re.compile(r"([\{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:")


def _to_json_like(text: str) -> str:
    """Convert Mongo shell getIndexes() output into valid JSON.

    Steps:
      - Strip JS comments (// and /* */)
      - Remove trailing semicolons
      - Quote unquoted property names
      - Convert single quotes to double quotes
    This is heuristic but sufficient for typical getIndexes() output.
    """
    # Remove comments
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    # Trim & remove trailing semicolon
    text = re.sub(r";\s*$", "", text.strip())
    # Quote property names
    text = _UNQUOTED_KEY_RE.sub(lambda m: f'{m.group(1)}"{m.group(2)}":', text)
    # Replace single quotes with double quotes (after quoting keys)
    text = text.replace("'", '"')
    return text


def _load_index_specs(idx_path: Path, logger) -> list[dict[str, Any]]:
    raw = idx_path.read_text(encoding="utf-8")
    # Try direct JSON first
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data  # already good
    except Exception:
        pass
    # Transform shell format to JSON
    transformed = _to_json_like(raw)
    try:
        data = json.loads(transformed)
        if not isinstance(data, list):  # some dumps wrap the list in an object
            raise ValueError("Index file root must be an array")
        return data
    except Exception as e:
        logger.error("Index parse failed after transformation: %s", e)
        raise


def apply_indexes(conn: MongoDBConnection, database: str, collection: str, repo_root: Path) -> int:
    logger = get_logger(__name__)
    idx_file = repo_root / "automate_refresh" / "indexes" / f"Index_{collection}.js"
    if not idx_file.exists():
        logger.info("No index file found at %s; skipping index apply", idx_file)
        return 0

    try:
        specs = _load_index_specs(idx_file, logger)
    except Exception:
        return 0

    # Build IndexModel list from getIndexes() style output
    models: list[IndexModel] = []
    for spec in specs:
        if not isinstance(spec, dict):
            continue
        name = spec.get("name")
        if name == "_id_":  # skip default _id index
            continue
        key_doc = spec.get("key")
        if not isinstance(key_doc, dict):
            logger.warning("Skipping index spec without 'key': %s", spec)
            continue
        # Convert key document to list of (field, direction) preserving order (JSON keeps insertion order in Python >=3.7)
        key_list = list(key_doc.items())
        # Allowed extra options
        options = {}
        for opt in (
            "unique",
            "sparse",
            "expireAfterSeconds",
            "background",
            "hidden",
            "partialFilterExpression",
        ):  # noqa: E501
            if opt in spec:
                options[opt] = spec[opt]
        try:
            models.append(IndexModel(key_list, name=name, **options))
        except Exception as e:
            logger.error("Failed constructing IndexModel for %s: %s", name, e)
    if not models:
        logger.info("No custom indexes to create (spec file had none beyond _id_)")
        return 0

    db = conn.get_client()[database]
    coll = db.get_collection(collection)
    try:
        created = coll.create_indexes(models)
        logger.info("Applied %d indexes from %s", len(created), idx_file)
        return len(created)
    except Exception as ex:
        logger.error("create_indexes failed: %s", ex)
        return 0
