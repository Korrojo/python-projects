"""Pydantic models for mongodump operations."""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator

from .base import BaseOperationOptions


class MongoDumpOptions(BaseOperationOptions):
    """Configuration options for mongodump operation."""

    # Output options
    output_dir: Path = Field(Path("./backups"), description="Output directory for backups")
    archive_file: Optional[Path] = Field(None, description="Create single archive file")

    # Backup options
    collections: List[str] = Field(default_factory=list, description="Specific collections to backup")
    query: Optional[str] = Field(None, description="JSON query filter for documents")
    gzip: bool = Field(True, description="Compress output with gzip")
    parallel_jobs: int = Field(4, description="Number of parallel collections", ge=1, le=16)

    # Resume capability
    resume: bool = Field(False, description="Resume from previous interrupted backup")
    state_file: Optional[Path] = Field(None, description="Path to state file for resume")

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Ensure output directory is absolute."""
        return v.resolve() if not v.is_absolute() else v

    @field_validator("archive_file")
    @classmethod
    def validate_archive_file(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate archive file path."""
        if v:
            v = v.resolve() if not v.is_absolute() else v
            if v.suffix not in [".gz", ".archive", ""]:
                raise ValueError("Archive file should have .gz or .archive extension")
        return v

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: Optional[str]) -> Optional[str]:
        """Validate JSON query format."""
        if v:
            import json

            try:
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON query: {e}")
        return v

    @field_validator("collections")
    @classmethod
    def validate_collections(cls, v: List[str]) -> List[str]:
        """Validate collection names."""
        for coll in v:
            if "$" in coll and not coll.startswith("system."):
                raise ValueError(f"Invalid collection name: {coll}")
        return v

    def get_script_args(self) -> List[str]:
        """Convert options to shell script arguments."""
        args = []

        # Connection
        uri = self.connection.build_uri()
        args.extend(["--uri", uri])

        # Database
        if self.database:
            args.extend(["--db", self.database])

        # Output
        if self.archive_file:
            args.extend(["--archive", str(self.archive_file)])
        else:
            args.extend(["--output", str(self.output_dir)])

        # Collections
        for coll in self.collections:
            args.extend(["--collection", coll])

        # Query filter
        if self.query:
            args.extend(["--query", self.query])

        # Compression
        if self.gzip:
            args.append("--gzip")
        else:
            args.append("--no-gzip")

        # Parallel
        args.extend(["--parallel", str(self.parallel_jobs)])

        # Resume
        if self.resume:
            args.append("--resume")

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
                "database": "MyDatabase",
                "output_dir": "/backups",
                "gzip": True,
                "parallel_jobs": 4,
            }
        }
