from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass

from common_config.utils.logger import get_logger


@dataclass
class PullResult:
    dest_dir: str
    files_copied: int


def pull_from_sas(src_url: str, dest_base_dir: str) -> PullResult:
    """Use azcopy to pull files from an Azure File Share SAS URL into the base backup dir.

    Behavior:
      - We expect src_url to point at the remote export directory.
      - We copy recursively into the local base directory (e.g. ~/Backups/local) so the
        remote 'export' folder becomes <base>/export (no export/export nesting).
      - We never overwrite existing files (--overwrite=false) to preserve prior snapshots.
    """
    logger = get_logger(__name__)
    dest_base_dir = os.path.expanduser(dest_base_dir)
    # If user passed a path ending with 'export', back up one level so we don't create export/export
    if os.path.basename(dest_base_dir.rstrip(os.sep)) == "export":
        logger.info(
            "Destination %s ends with 'export'; using parent as base to avoid nesting.",
            dest_base_dir,
        )
        dest_base_dir = os.path.dirname(dest_base_dir.rstrip(os.sep))
    os.makedirs(dest_base_dir, exist_ok=True)

    if not shutil.which("azcopy"):
        raise RuntimeError("azcopy not found on PATH. Install azcopy to use pull_from_sas().")

    env = os.environ.copy()
    env["AZCOPY_CRED_TYPE"] = "Anonymous"
    env["AZCOPY_CONCURRENCY_VALUE"] = "AUTO"

    cmd = [
        "azcopy",
        "copy",
        src_url,
        dest_base_dir,
        "--recursive",  # ensure directory contents are copied
        "--overwrite=false",
        "--from-to=FileLocal",
        "--check-md5",
        "FailIfDifferent",
        "--log-level=INFO",
        "--trailing-dot=Enable",
    ]
    logger.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True, env=env)

    # Count JSON files inside the export subfolder if it now exists
    export_dir = os.path.join(dest_base_dir, "export")
    json_count = 0
    if os.path.isdir(export_dir):
        try:
            json_count = sum(
                1
                for f in os.listdir(export_dir)
                if f.lower().endswith(".json") and os.path.isfile(os.path.join(export_dir, f))
            )
        except Exception:
            pass
    logger.info(
        "Pull completed to base=%s (export dir=%s | json files=%s)",
        dest_base_dir,
        export_dir,
        json_count,
    )
    return PullResult(dest_dir=dest_base_dir, files_copied=json_count)
