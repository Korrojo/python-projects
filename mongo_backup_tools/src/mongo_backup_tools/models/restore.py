"""Pydantic models for mongorestore operations."""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator

from .base import BaseOperationOptions


class MongoRestoreOptions(BaseOperationOptions):
    """Configuration options for mongorestore operation."""

    # Input options
    archive_file: Optional[Path] = Field(None, description="Restore from archive file")
    backup_dir: Path = Field(Path("./backups"), description="Restore from backup directory")

    # Restore options
    namespace_from: Optional[str] = Field(None, description='Source namespace (e.g., "db.collection")')
    namespace_to: Optional[str] = Field(None, description='Destination namespace (e.g., "db.collection")')
    drop_existing: bool = Field(False, description="Drop each collection before restore")
    restore_indexes: bool = Field(True, description="Restore indexes")
    parallel_jobs: int = Field(4, description="Number of parallel collections", ge=1, le=16)

    @field_validator("archive_file")
    @classmethod
    def validate_archive_file(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate archive file exists."""
        if v:
            v = v.resolve() if not v.is_absolute() else v
            if not v.exists():
                raise FileNotFoundError(f"Archive file not found: {v}")
        return v

    @field_validator("backup_dir")
    @classmethod
    def validate_backup_dir(cls, v: Path) -> Path:
        """Ensure backup directory is absolute."""
        return v.resolve() if not v.is_absolute() else v

    @field_validator("namespace_from", "namespace_to")
    @classmethod
    def validate_namespace(cls, v: Optional[str]) -> Optional[str]:
        """Validate namespace format (db.collection or db.*)."""
        if v:
            if "." not in v:
                raise ValueError("Namespace must be in format 'database.collection' or 'database.*'")
            parts = v.split(".")
            if len(parts) != 2:
                raise ValueError("Namespace must have exactly one dot")
        return v

    def validate_namespace_pair(self) -> None:
        """Validate that both namespaces are specified together."""
        if (self.namespace_from and not self.namespace_to) or (self.namespace_to and not self.namespace_from):
            raise ValueError("Both --nsFrom and --nsTo must be specified together")

    def get_script_args(self) -> List[str]:
        """Convert options to shell script arguments."""
        args = []

        # Connection
        uri = self.connection.build_uri()
        args.extend(["--uri", uri])

        # Input source
        if self.archive_file:
            args.extend(["--archive", str(self.archive_file)])
        else:
            args.extend(["--dir", str(self.backup_dir)])

        # Target database/collection
        if self.database:
            args.extend(["--db", self.database])
        if self.collection:
            args.extend(["--collection", self.collection])

        # Namespace remapping
        if self.namespace_from and self.namespace_to:
            args.extend(["--nsFrom", self.namespace_from])
            args.extend(["--nsTo", self.namespace_to])

        # Restore options
        if self.drop_existing:
            args.append("--drop")
        if not self.restore_indexes:
            args.append("--noIndexRestore")

        # Parallel
        args.extend(["--parallel", str(self.parallel_jobs)])

        # Operation modes
        if self.dry_run:
            args.append("--dry-run")
        if self.verbose:
            args.append("--verbose")
        if self.quiet:
            args.append("--quiet")

        return args

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "connection": {"host": "localhost", "port": 27017},
                "archive_file": "/backups/mydb.gz",
                "namespace_from": "ProdDB.*",
                "namespace_to": "DevDB.*",
                "drop_existing": True,
            }
        }
