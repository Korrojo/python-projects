"""Base models for MongoDB operations."""

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class MongoConnectionOptions(BaseModel):
    """MongoDB connection configuration."""

    uri: Optional[str] = Field(None, description="MongoDB connection string")
    host: str = Field("localhost", description="MongoDB host")
    port: int = Field(27017, description="MongoDB port", ge=1, le=65535)
    username: Optional[str] = Field(None, description="Authentication username")
    password: Optional[str] = Field(None, description="Authentication password")
    auth_database: str = Field("admin", description="Authentication database")
    auth_mechanism: Optional[str] = Field(
        None, description="Authentication mechanism (SCRAM-SHA-1, SCRAM-SHA-256, MONGODB-X509, etc.)"
    )
    # TLS/SSL options
    use_tls: bool = Field(False, description="Enable TLS/SSL")
    tls_certificate_key_file: Optional[Path] = Field(None, description="TLS client certificate file")
    tls_ca_file: Optional[Path] = Field(None, description="TLS CA certificate file")
    tls_certificate_key_file_password: Optional[str] = Field(None, description="TLS certificate password")
    tls_allow_invalid_certificates: bool = Field(False, description="Allow invalid TLS certificates")
    tls_allow_invalid_hostnames: bool = Field(False, description="Allow invalid TLS hostnames")
    # Additional connection options
    read_preference: Optional[str] = Field(None, description="Read preference mode")
    replica_set_name: Optional[str] = Field(None, description="Replica set name")
    connect_timeout: Optional[int] = Field(None, description="Connection timeout in milliseconds")
    socket_timeout: Optional[int] = Field(None, description="Socket timeout in milliseconds")

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, v: Optional[str]) -> Optional[str]:
        """Validate MongoDB URI format."""
        if v and not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("URI must start with mongodb:// or mongodb+srv://")
        return v

    def build_uri(self) -> str:
        """Build MongoDB connection string from components."""
        if self.uri:
            return self.uri

        # Build URI from components
        uri = "mongodb://"

        if self.username:
            uri += self.username
            if self.password:
                uri += f":{self.password}"
            uri += "@"

        uri += f"{self.host}:{self.port}"

        if self.auth_database and self.username:
            uri += f"/?authSource={self.auth_database}"

        return uri


class BaseOperationOptions(BaseModel):
    """Base options for all MongoDB operations."""

    # Connection
    connection: MongoConnectionOptions = Field(
        default_factory=MongoConnectionOptions, description="MongoDB connection options"
    )

    # Database and collection
    database: Optional[str] = Field(None, description="Database name")
    collection: Optional[str] = Field(None, description="Collection name")

    # Operation modes
    dry_run: bool = Field(False, description="Show what would be done without executing")
    verbose: bool = Field(False, description="Enable verbose logging")
    quiet: bool = Field(False, description="Suppress all output except errors")

    @field_validator("database")
    @classmethod
    def validate_database(cls, v: Optional[str]) -> Optional[str]:
        """Validate database name."""
        if v and any(char in v for char in [" ", ".", "$", "/"]):
            raise ValueError("Database name contains invalid characters")
        return v

    @field_validator("collection")
    @classmethod
    def validate_collection(cls, v: Optional[str]) -> Optional[str]:
        """Validate collection name."""
        if v and "$" in v and not v.startswith("system."):
            raise ValueError("Collection name cannot contain '$' unless system collection")
        return v

    @model_validator(mode="before")
    @classmethod
    def handle_flat_connection_fields(cls, data: Any) -> Any:
        """Handle flat connection fields and nest them in connection object."""
        if isinstance(data, dict):
            # Extract connection fields if they exist (only non-None values)
            connection_fields = {}
            for field in [
                "uri",
                "host",
                "port",
                "username",
                "password",
                "auth_database",
                "auth_mechanism",
                "use_tls",
                "tls_certificate_key_file",
                "tls_ca_file",
                "tls_certificate_key_file_password",
                "tls_allow_invalid_certificates",
                "tls_allow_invalid_hostnames",
                "read_preference",
                "replica_set_name",
                "connect_timeout",
                "socket_timeout",
            ]:
                if field in data and data[field] is not None:
                    connection_fields[field] = data.pop(field)
                elif field in data:
                    # Remove None values
                    data.pop(field)

            # If any connection fields were provided, create/update connection object
            if connection_fields:
                if "connection" in data:
                    # Merge with existing connection
                    data["connection"].update(connection_fields)
                else:
                    # Create new connection
                    data["connection"] = connection_fields

        return data


class PathOptions(BaseModel):
    """File path configuration with validation."""

    path: Path = Field(..., description="File or directory path")

    @field_validator("path")
    @classmethod
    def validate_path_str(cls, v: Path) -> Path:
        """Ensure path is absolute."""
        if not v.is_absolute():
            v = v.resolve()
        return v

    def ensure_exists(self, create: bool = False) -> None:
        """Ensure path exists, optionally creating it."""
        if not self.path.exists():
            if create and self.path.suffix == "":
                # It's a directory
                self.path.mkdir(parents=True, exist_ok=True)
            elif not create:
                raise FileNotFoundError(f"Path does not exist: {self.path}")

    def ensure_parent_exists(self) -> None:
        """Ensure parent directory exists."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
