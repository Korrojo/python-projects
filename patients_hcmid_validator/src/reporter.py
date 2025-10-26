"""Reporter utilities (Phase 2/3 placeholder)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Counters:
    total: int = 0
    matched: int = 0
    mismatched: int = 0
    not_found: int = 0

    def to_dict(self):
        return asdict(self)
