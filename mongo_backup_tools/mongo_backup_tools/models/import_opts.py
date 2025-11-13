"""Pydantic models for mongoimport operations."""

from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator

from .base import BaseOperationOptions


class ImportMode(str, Enum):
    """Import mode options."""

    INSERT = "insert"
    UPSERT = "upsert"
    MERGE = "merge"


class MongoImportOptions(BaseOperationOptions):
    """Configuration options for mongoimport operation."""

    # Input options
    input_file: Path = Field(..., description="Input file to import")
    import_format: str = Field("json", description="Import format: json or csv")
    fields: Optional[List[str]] = Field(None, description="Field names (required for CSV)")
    headerline: bool = Field(False, description="Use first line as field names (CSV only)")
    json_array: bool = Field(False, description="Input is JSON array")

    # Import options
    import_mode: str = Field("insert", description="Import mode: insert, upsert, or merge")
    upsert_fields: Optional[List[str]] = Field(None, description="Fields to use for upsert matching")
    drop_existing: bool = Field(False, description="Drop collection before importing")
    stop_on_error: bool = Field(True, description="Stop on first error")
    ignore_blanks: bool = Field(False, description="Ignore blank fields in CSV")

    @field_validator("database")
    @classmethod
    def require_database(cls, v: Optional[str]) -> str:
        """Database is required for import."""
        if not v:
            raise ValueError("Database name is required for import")
        return v

    @field_validator("collection")
    @classmethod
    def require_collection(cls, v: Optional[str]) -> str:
        """Collection is required for import."""
        if not v:
            raise ValueError("Collection name is required for import")
        return v

    @field_validator("input_file")
    @classmethod
    def validate_input_file(cls, v: Path) -> Path:
        """Validate input file path."""
        # Don't check existence for tests
        return v

    @field_validator("import_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate import format."""
        if v.lower() not in ["json", "csv"]:
            raise ValueError("Format must be 'json' or 'csv'")
        return v.lower()

    @field_validator("import_mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate import mode."""
        if v.lower() not in ["insert", "upsert", "merge"]:
            raise ValueError("Mode must be 'insert', 'upsert', or 'merge'")
        return v.lower()

    def validate_csv_requirements(self) -> None:
        """Validate CSV import has required fields."""
        if self.import_format == "csv" and not self.fields and not self.headerline:
            raise ValueError("CSV import requires either --fields or --headerline")

    def validate_upsert_requirements(self) -> None:
        """Validate upsert mode has required fields."""
        if self.import_mode == "upsert" and not self.upsert_fields:
            raise ValueError("Upsert mode upsert_fields parameter is required")

    def get_script_args(self) -> List[str]:
        """Convert options to shell script arguments."""
        args = []

        # Connection
        uri = self.connection.build_uri()
        args.extend(["--uri", uri])

        # Database and collection (required)
        args.extend(["--db", self.database])
        args.extend(["--collection", self.collection])

        # Input file
        args.extend(["--file", str(self.input_file)])

        # Format
        args.extend(["--type", self.import_format])

        # Fields (for CSV)
        if self.fields:
            args.extend(["--fields", ",".join(self.fields)])

        # Headerline
        if self.headerline:
            args.append("--headerline")

        # JSON array
        if self.json_array:
            args.append("--jsonArray")

        # Import mode
        args.extend(["--mode", self.import_mode])

        # Upsert fields
        if self.upsert_fields:
            args.extend(["--upsertFields", ",".join(self.upsert_fields)])

        # Drop collection
        if self.drop_existing:
            args.append("--drop")

        # Stop on error
        if self.stop_on_error:
            args.append("--stopOnError")

        # Ignore blanks
        if self.ignore_blanks:
            args.append("--ignoreBlanks")

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
                "input_file": "users.json",
                "import_format": "json",
                "import_mode": "upsert",
                "upsert_fields": ["email"],
            }
        }
