from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class DataExporter:
    """Exports data to JSON/CSV with minimal options.

    Compatible with existing usage: exporter.to_csv(list_of_dicts, output_path)
    """

    def __init__(self, config_manager: object | None = None) -> None:
        self.config_manager = config_manager

    def to_json(
        self,
        data: list[dict[str, Any]],
        file_path: str | Path,
        encoding: str = "utf-8",
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> None:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=str)

    def to_csv(
        self,
        data: list[dict[str, Any]],
        file_path: str | Path,
        encoding: str = "utf-8",
        delimiter: str = ",",
        include_header: bool = True,
    ) -> None:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not data:
            # Create empty file
            file_path.touch()
            return

        fieldnames = list({k for row in data for k in row.keys()})
        with file_path.open("w", newline="", encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            if include_header:
                writer.writeheader()
            for row in data:
                writer.writerow(row)
