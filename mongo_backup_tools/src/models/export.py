"""Pydantic models for mongoexport operations."""

from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator

from models.base import BaseOperationOptions


class ExportFormat(str, Enum):
    """Export format options."""

    JSON = "json"
    CSV = "csv"


class MongoExportOptions(BaseOperationOptions):
    """Configuration options for mongoexport operation."""

    # Output options
    output_file: Optional[Path] = Field(None, description="Output file (auto-generated if not specified)")
    export_format: str = Field("json", description="Export format: json or csv")
    fields: Optional[List[str]] = Field(None, description="Fields to export (required for CSV)")
    pretty_print: bool = Field(False, description="Pretty-print JSON output")

    # Query options
    query: Optional[str] = Field(None, description="Query filter (JSON)")
    sort: Optional[str] = Field(None, description="Sort specification (JSON)")
    limit: Optional[int] = Field(None, description="Limit number of documents", ge=1)
    skip: Optional[int] = Field(None, description="Skip N documents", ge=0)

    @field_validator("database")
    @classmethod
    def require_database(cls, v: Optional[str]) -> str:
        """Database is required for export."""
        if not v:
            raise ValueError("Database name is required for export")
        return v

    @field_validator("collection")
    @classmethod
    def require_collection(cls, v: Optional[str]) -> str:
        """Collection is required for export."""
        if not v:
            raise ValueError("Collection name is required for export")
        return v

    @field_validator("export_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate export format."""
        if v.lower() not in ["json", "csv"]:
            raise ValueError("Format must be 'json' or 'csv'")
        return v.lower()

    @field_validator("output_file")
    @classmethod
    def validate_output_file(cls, v: Optional[Path]) -> Optional[Path]:
        """Ensure output file is absolute."""
        if v:
            v = v.resolve() if not v.is_absolute() else v
        return v

    @field_validator("query", "sort")
    @classmethod
    def validate_json(cls, v: Optional[str]) -> Optional[str]:
        """Validate JSON format."""
        if v:
            import json

            try:
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        return v

    def validate_csv_requirements(self) -> None:
        """Validate CSV export has required fields."""
        if self.export_format == "csv" and not self.fields:
            raise ValueError("CSV export fields parameter is required")

    def get_script_args(self) -> List[str]:
        """Convert options to shell script arguments."""
        args = []

        # Connection
        uri = self.connection.build_uri()
        args.extend(["--uri", uri])

        # Database and collection (required)
        args.extend(["--db", self.database])
        args.extend(["--collection", self.collection])

        # Output
        if self.output_file:
            args.extend(["--output", str(self.output_file)])

        # Format
        args.extend(["--type", self.export_format])

        # Fields (for CSV)
        if self.fields:
            args.extend(["--fields", ",".join(self.fields)])

        # Pretty print
        if self.pretty_print:
            args.append("--pretty")

        # Query options
        if self.query:
            args.extend(["--query", self.query])
        if self.sort:
            args.extend(["--sort", self.sort])
        if self.limit is not None:
            args.extend(["--limit", str(self.limit)])
        if self.skip is not None:
            args.extend(["--skip", str(self.skip)])

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
                "collection": "Users",
                "output_file": "users.json",
                "export_format": "json",
                "query": '{"active": true}',
            }
        }
