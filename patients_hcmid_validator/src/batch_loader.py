"""Batch loading utilities (Phase 2/3 placeholder).

Will implement streaming CSV reader that yields batches of rows for HcmId lookup.
"""

from __future__ import annotations

from collections.abc import Iterator


def group_batches(rows_iter, batch_size: int) -> Iterator[list[dict[str, str]]]:
    batch: list[dict[str, str]] = []
    for row in rows_iter:
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
