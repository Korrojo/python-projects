"""Mongo fetch utilities (Phase 2/3 placeholder)."""

from __future__ import annotations

# Actual implementation will import MongoDBConnection and perform batch $in queries.


def build_hcmid_index(docs: list[dict]) -> dict[str, dict]:
    return {d.get("HcmId"): d for d in docs if d.get("HcmId")}
