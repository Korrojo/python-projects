"""Main CLI entry point for mongo_backup_tools."""

from pathlib import Path
from typing import List, Optional

import typer

__version__ = "1.0.0"

from models.dump import MongoDumpOptions
from models.export import ExportFormat, MongoExportOptions
from models.import_opts import ImportMode, MongoImportOptions
from models.restore import MongoRestoreOptions
from orchestrators.dump import MongoDumpOrchestrator
from orchestrators.export import MongoExportOrchestrator
from orchestrators.import_orch import MongoImportOrchestrator
from orchestrators.restore import MongoRestoreOrchestrator
from utils.env_loader import EnvironmentConfigError, get_mongo_connection_config

app = typer.Typer(
    name="mongo-backup-tools",
    help="Comprehensive MongoDB backup, restore, export, and import toolkit",
    no_args_is_help=True,
)


@app.command("version")
def show_version():
    """Show version information."""
    typer.echo(f"mongo-backup-tools version {__version__}")


@app.command("dump")
def dump(
    # Environment config
    env: Optional[str] = typer.Option(
        None, "--env", help="Environment name (LOCL, DEV, STG, STG2, STG3, TRNG, PERF, PHI, PRPRD, PROD)"
    ),
    # Connection options
    uri: Optional[str] = typer.Option(None, "--uri", help="MongoDB connection string"),
    host: str = typer.Option("localhost", "--host", help="MongoDB host"),
    port: int = typer.Option(27017, "--port", help="MongoDB port"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="MongoDB username"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="MongoDB password"),
    auth_db: Optional[str] = typer.Option(None, "--auth-db", help="Authentication database"),
    auth_mechanism: Optional[str] = typer.Option(None, "--auth-mechanism", help="Authentication mechanism"),
    # TLS/SSL options
    tls: bool = typer.Option(False, "--tls", "--ssl", help="Enable TLS/SSL"),
    tls_certificate_key_file: Optional[Path] = typer.Option(
        None, "--tls-certificate-key-file", help="TLS client certificate file"
    ),
    tls_ca_file: Optional[Path] = typer.Option(None, "--tls-ca-file", help="TLS CA certificate file"),
    tls_certificate_key_file_password: Optional[str] = typer.Option(
        None, "--tls-certificate-key-file-password", help="TLS certificate password"
    ),
    tls_allow_invalid_certificates: bool = typer.Option(
        False, "--tls-allow-invalid-certificates", help="Allow invalid TLS certificates"
    ),
    tls_allow_invalid_hostnames: bool = typer.Option(
        False, "--tls-allow-invalid-hostnames", help="Allow invalid TLS hostnames"
    ),
    # Additional connection options
    read_preference: Optional[str] = typer.Option(None, "--read-preference", help="Read preference mode"),
    replica_set_name: Optional[str] = typer.Option(None, "--replica-set-name", help="Replica set name"),
    connect_timeout: Optional[int] = typer.Option(None, "--connect-timeout", help="Connection timeout (ms)"),
    socket_timeout: Optional[int] = typer.Option(None, "--socket-timeout", help="Socket timeout (ms)"),
    # Database/Collection options
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Database to dump"),
    collections: Optional[List[str]] = typer.Option(
        None, "--collection", "-c", help="Collections to dump (can be specified multiple times)"
    ),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Query filter (JSON)"),
    # Output options
    output_dir: Optional[Path] = typer.Option(None, "--out", "-o", help="Output directory"),
    archive: Optional[Path] = typer.Option(None, "--archive", help="Archive file path"),
    gzip: bool = typer.Option(False, "--gzip", help="Compress output with gzip"),
    # Performance options
    parallel_jobs: Optional[int] = typer.Option(
        None, "--num-parallel-collections", "-j", help="Number of parallel collections"
    ),
    # Other options
    oplog: bool = typer.Option(False, "--oplog", help="Include oplog for point-in-time backup"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    timeout: int = typer.Option(3600, "--timeout", help="Operation timeout in seconds"),
):
    """Create a binary dump of MongoDB database(s)."""
    try:
        # Load from environment if --env specified
        if env:
            try:
                env_config = get_mongo_connection_config(env)
                # Use env config as defaults, but allow CLI parameters to override
                if not uri:
                    uri = env_config["uri"]
                if not database:
                    database = env_config["database"]
                if not output_dir and env_config.get("backup_dir"):
                    output_dir = Path(env_config["backup_dir"])
            except EnvironmentConfigError as e:
                typer.secho(f"✗ Environment configuration error: {e}", fg=typer.colors.RED)
                raise typer.Exit(code=1)

        options = MongoDumpOptions(
            uri=uri,
            host=host,
            port=port,
            username=username,
            password=password,
            auth_database=auth_db,
            auth_mechanism=auth_mechanism,
            use_tls=tls,
            tls_certificate_key_file=tls_certificate_key_file,
            tls_ca_file=tls_ca_file,
            tls_certificate_key_file_password=tls_certificate_key_file_password,
            tls_allow_invalid_certificates=tls_allow_invalid_certificates,
            tls_allow_invalid_hostnames=tls_allow_invalid_hostnames,
            read_preference=read_preference,
            replica_set_name=replica_set_name,
            connect_timeout=connect_timeout,
            socket_timeout=socket_timeout,
            database=database,
            collections=collections or [],
            query=query,
            output_dir=output_dir,  # None by default, model will set centralized path
            archive_file=archive,
            gzip=gzip,
            parallel_jobs=parallel_jobs,
            oplog=oplog,
            verbose=verbose,
        )

        orchestrator = MongoDumpOrchestrator()
        result = orchestrator.dump(options, timeout=timeout)

        if result.success:
            typer.secho(f"✓ Dump completed successfully in {result.duration:.2f}s", fg=typer.colors.GREEN)
            if result.stdout:
                typer.echo(result.stdout)
        else:
            typer.secho(f"✗ Dump failed (exit code {result.exit_code})", fg=typer.colors.RED)
            if result.stderr:
                typer.echo(result.stderr, err=True)
            raise typer.Exit(code=result.exit_code)

    except Exception as e:
        typer.secho(f"✗ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command("restore")
def restore(
    # Environment config
    env: Optional[str] = typer.Option(
        None, "--env", help="Environment name (LOCL, DEV, STG, STG2, STG3, TRNG, PERF, PHI, PRPRD, PROD)"
    ),
    # Connection options
    uri: Optional[str] = typer.Option(None, "--uri", help="MongoDB connection string"),
    host: str = typer.Option("localhost", "--host", help="MongoDB host"),
    port: int = typer.Option(27017, "--port", help="MongoDB port"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="MongoDB username"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="MongoDB password"),
    auth_db: Optional[str] = typer.Option(None, "--auth-db", help="Authentication database"),
    auth_mechanism: Optional[str] = typer.Option(None, "--auth-mechanism", help="Authentication mechanism"),
    # TLS/SSL options
    tls: bool = typer.Option(False, "--tls", "--ssl", help="Enable TLS/SSL"),
    tls_certificate_key_file: Optional[Path] = typer.Option(
        None, "--tls-certificate-key-file", help="TLS client certificate file"
    ),
    tls_ca_file: Optional[Path] = typer.Option(None, "--tls-ca-file", help="TLS CA certificate file"),
    tls_certificate_key_file_password: Optional[str] = typer.Option(
        None, "--tls-certificate-key-file-password", help="TLS certificate password"
    ),
    tls_allow_invalid_certificates: bool = typer.Option(
        False, "--tls-allow-invalid-certificates", help="Allow invalid TLS certificates"
    ),
    tls_allow_invalid_hostnames: bool = typer.Option(
        False, "--tls-allow-invalid-hostnames", help="Allow invalid TLS hostnames"
    ),
    # Additional connection options
    read_preference: Optional[str] = typer.Option(None, "--read-preference", help="Read preference mode"),
    replica_set_name: Optional[str] = typer.Option(None, "--replica-set-name", help="Replica set name"),
    connect_timeout: Optional[int] = typer.Option(None, "--connect-timeout", help="Connection timeout (ms)"),
    socket_timeout: Optional[int] = typer.Option(None, "--socket-timeout", help="Socket timeout (ms)"),
    # Database/Collection options
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Target database"),
    collection: Optional[str] = typer.Option(None, "--collection", "-c", help="Target collection"),
    # Input options
    input_dir: Optional[Path] = typer.Option(None, "--dir", help="Input directory"),
    archive: Optional[Path] = typer.Option(None, "--archive", help="Archive file path"),
    gzip: bool = typer.Option(False, "--gzip", help="Decompress gzip input"),
    # Namespace options
    ns_from: Optional[str] = typer.Option(None, "--ns-from", help="Original namespace (db.collection)"),
    ns_to: Optional[str] = typer.Option(None, "--ns-to", help="Target namespace (db.collection)"),
    # Restore options
    drop: bool = typer.Option(False, "--drop", help="Drop collections before restore"),
    oplog_replay: bool = typer.Option(False, "--oplog-replay", help="Replay oplog for point-in-time restore"),
    restore_indexes: bool = typer.Option(True, "--restore-indexes/--no-restore-indexes", help="Restore indexes"),
    # Performance options
    parallel_jobs: Optional[int] = typer.Option(
        None, "--num-parallel-collections", "-j", help="Number of parallel collections"
    ),
    # Other options
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    timeout: int = typer.Option(3600, "--timeout", help="Operation timeout in seconds"),
):
    """Restore a MongoDB database from a binary dump."""
    try:
        # Load from environment if --env specified
        if env:
            try:
                env_config = get_mongo_connection_config(env)
                # Use env config as defaults, but allow CLI parameters to override
                if not uri:
                    uri = env_config["uri"]
                if not database:
                    database = env_config["database"]
                if not input_dir and env_config.get("backup_dir"):
                    input_dir = Path(env_config["backup_dir"])
            except EnvironmentConfigError as e:
                typer.secho(f"✗ Environment configuration error: {e}", fg=typer.colors.RED)
                raise typer.Exit(code=1)

        options = MongoRestoreOptions(
            uri=uri,
            host=host,
            port=port,
            username=username,
            password=password,
            auth_database=auth_db,
            auth_mechanism=auth_mechanism,
            use_tls=tls,
            tls_certificate_key_file=tls_certificate_key_file,
            tls_ca_file=tls_ca_file,
            tls_certificate_key_file_password=tls_certificate_key_file_password,
            tls_allow_invalid_certificates=tls_allow_invalid_certificates,
            tls_allow_invalid_hostnames=tls_allow_invalid_hostnames,
            read_preference=read_preference,
            replica_set_name=replica_set_name,
            connect_timeout=connect_timeout,
            socket_timeout=socket_timeout,
            database=database,
            collection=collection,
            input_dir=input_dir or Path("dump"),
            archive_file=archive,
            gzip=gzip,
            ns_from=ns_from,
            ns_to=ns_to,
            drop_existing=drop,
            oplog_replay=oplog_replay,
            restore_indexes=restore_indexes,
            parallel_jobs=parallel_jobs,
            verbose=verbose,
        )

        orchestrator = MongoRestoreOrchestrator()
        result = orchestrator.restore(options, timeout=timeout)

        if result.success:
            typer.secho(f"✓ Restore completed successfully in {result.duration:.2f}s", fg=typer.colors.GREEN)
            if result.stdout:
                typer.echo(result.stdout)
        else:
            typer.secho(f"✗ Restore failed (exit code {result.exit_code})", fg=typer.colors.RED)
            if result.stderr:
                typer.echo(result.stderr, err=True)
            raise typer.Exit(code=result.exit_code)

    except Exception as e:
        typer.secho(f"✗ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command("export")
def export(
    # Environment config
    env: Optional[str] = typer.Option(
        None, "--env", help="Environment name (LOCL, DEV, STG, STG2, STG3, TRNG, PERF, PHI, PRPRD, PROD)"
    ),
    # Connection options
    uri: Optional[str] = typer.Option(None, "--uri", help="MongoDB connection string"),
    host: str = typer.Option("localhost", "--host", help="MongoDB host"),
    port: int = typer.Option(27017, "--port", help="MongoDB port"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="MongoDB username"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="MongoDB password"),
    auth_db: Optional[str] = typer.Option(None, "--auth-db", help="Authentication database"),
    auth_mechanism: Optional[str] = typer.Option(None, "--auth-mechanism", help="Authentication mechanism"),
    # TLS/SSL options
    tls: bool = typer.Option(False, "--tls", "--ssl", help="Enable TLS/SSL"),
    tls_certificate_key_file: Optional[Path] = typer.Option(
        None, "--tls-certificate-key-file", help="TLS client certificate file"
    ),
    tls_ca_file: Optional[Path] = typer.Option(None, "--tls-ca-file", help="TLS CA certificate file"),
    tls_certificate_key_file_password: Optional[str] = typer.Option(
        None, "--tls-certificate-key-file-password", help="TLS certificate password"
    ),
    tls_allow_invalid_certificates: bool = typer.Option(
        False, "--tls-allow-invalid-certificates", help="Allow invalid TLS certificates"
    ),
    tls_allow_invalid_hostnames: bool = typer.Option(
        False, "--tls-allow-invalid-hostnames", help="Allow invalid TLS hostnames"
    ),
    # Additional connection options
    read_preference: Optional[str] = typer.Option(None, "--read-preference", help="Read preference mode"),
    replica_set_name: Optional[str] = typer.Option(None, "--replica-set-name", help="Replica set name"),
    connect_timeout: Optional[int] = typer.Option(None, "--connect-timeout", help="Connection timeout (ms)"),
    socket_timeout: Optional[int] = typer.Option(None, "--socket-timeout", help="Socket timeout (ms)"),
    # Database/Collection options (required unless using --env)
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Database name"),
    collection: str = typer.Option(..., "--collection", "-c", help="Collection name"),
    # Output options
    output_file: Optional[Path] = typer.Option(None, "--out", "-o", help="Output file path"),
    export_format: ExportFormat = typer.Option(ExportFormat.JSON, "--type", help="Export format (json or csv)"),
    # Query options
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Query filter (JSON)"),
    sort: Optional[str] = typer.Option(None, "--sort", help="Sort order (JSON)"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit number of documents"),
    skip: Optional[int] = typer.Option(None, "--skip", help="Skip number of documents"),
    # CSV options
    fields: Optional[List[str]] = typer.Option(
        None, "--field", "-f", help="Fields to export (for CSV, can be specified multiple times)"
    ),
    # JSON options
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output"),
    json_array: bool = typer.Option(False, "--json-array", help="Export as JSON array"),
    # Other options
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    timeout: int = typer.Option(1800, "--timeout", help="Operation timeout in seconds"),
):
    """Export MongoDB collection to JSON or CSV."""
    try:
        # Load from environment if --env specified
        if env:
            try:
                env_config = get_mongo_connection_config(env)
                # Use env config as defaults, but allow CLI parameters to override
                if not uri:
                    uri = env_config["uri"]
                if not database:
                    database = env_config["database"]
            except EnvironmentConfigError as e:
                typer.secho(f"✗ Environment configuration error: {e}", fg=typer.colors.RED)
                raise typer.Exit(code=1)

        # Validate required parameters
        if not database:
            typer.secho("✗ Error: --database is required (or use --env)", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        options = MongoExportOptions(
            uri=uri,
            host=host,
            port=port,
            username=username,
            password=password,
            auth_database=auth_db,
            auth_mechanism=auth_mechanism,
            use_tls=tls,
            tls_certificate_key_file=tls_certificate_key_file,
            tls_ca_file=tls_ca_file,
            tls_certificate_key_file_password=tls_certificate_key_file_password,
            tls_allow_invalid_certificates=tls_allow_invalid_certificates,
            tls_allow_invalid_hostnames=tls_allow_invalid_hostnames,
            read_preference=read_preference,
            replica_set_name=replica_set_name,
            connect_timeout=connect_timeout,
            socket_timeout=socket_timeout,
            database=database,
            collection=collection,
            output_file=output_file,
            export_format=export_format,
            query=query,
            sort=sort,
            limit=limit,
            skip=skip,
            fields=fields or [],
            pretty_print=pretty,
            json_array=json_array,
            verbose=verbose,
        )

        orchestrator = MongoExportOrchestrator()
        result = orchestrator.export(options, timeout=timeout)

        if result.success:
            typer.secho(f"✓ Export completed successfully in {result.duration:.2f}s", fg=typer.colors.GREEN)
            if result.stdout:
                typer.echo(result.stdout)
        else:
            typer.secho(f"✗ Export failed (exit code {result.exit_code})", fg=typer.colors.RED)
            if result.stderr:
                typer.echo(result.stderr, err=True)
            raise typer.Exit(code=result.exit_code)

    except Exception as e:
        typer.secho(f"✗ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command("import")
def import_data(
    # Environment config
    env: Optional[str] = typer.Option(
        None, "--env", help="Environment name (LOCL, DEV, STG, STG2, STG3, TRNG, PERF, PHI, PRPRD, PROD)"
    ),
    # Connection options
    uri: Optional[str] = typer.Option(None, "--uri", help="MongoDB connection string"),
    host: str = typer.Option("localhost", "--host", help="MongoDB host"),
    port: int = typer.Option(27017, "--port", help="MongoDB port"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="MongoDB username"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="MongoDB password"),
    auth_db: Optional[str] = typer.Option(None, "--auth-db", help="Authentication database"),
    auth_mechanism: Optional[str] = typer.Option(None, "--auth-mechanism", help="Authentication mechanism"),
    # TLS/SSL options
    tls: bool = typer.Option(False, "--tls", "--ssl", help="Enable TLS/SSL"),
    tls_certificate_key_file: Optional[Path] = typer.Option(
        None, "--tls-certificate-key-file", help="TLS client certificate file"
    ),
    tls_ca_file: Optional[Path] = typer.Option(None, "--tls-ca-file", help="TLS CA certificate file"),
    tls_certificate_key_file_password: Optional[str] = typer.Option(
        None, "--tls-certificate-key-file-password", help="TLS certificate password"
    ),
    tls_allow_invalid_certificates: bool = typer.Option(
        False, "--tls-allow-invalid-certificates", help="Allow invalid TLS certificates"
    ),
    tls_allow_invalid_hostnames: bool = typer.Option(
        False, "--tls-allow-invalid-hostnames", help="Allow invalid TLS hostnames"
    ),
    # Additional connection options
    read_preference: Optional[str] = typer.Option(None, "--read-preference", help="Read preference mode"),
    replica_set_name: Optional[str] = typer.Option(None, "--replica-set-name", help="Replica set name"),
    connect_timeout: Optional[int] = typer.Option(None, "--connect-timeout", help="Connection timeout (ms)"),
    socket_timeout: Optional[int] = typer.Option(None, "--socket-timeout", help="Socket timeout (ms)"),
    # Database/Collection options (required unless using --env)
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Database name"),
    collection: str = typer.Option(..., "--collection", "-c", help="Collection name"),
    # Input options (required)
    input_file: Path = typer.Option(..., "--file", help="Input file path"),
    import_format: ExportFormat = typer.Option(ExportFormat.JSON, "--type", help="Import format (json or csv)"),
    # Import mode
    mode: ImportMode = typer.Option(ImportMode.INSERT, "--mode", help="Import mode (insert, upsert, or merge)"),
    upsert_fields: Optional[List[str]] = typer.Option(
        None, "--upsert-fields", help="Fields to use for upsert matching (can be specified multiple times)"
    ),
    # CSV options
    fields: Optional[List[str]] = typer.Option(
        None, "--field", "-f", help="Field names (for CSV, can be specified multiple times)"
    ),
    headerline: bool = typer.Option(False, "--headerline", help="Use first line as field names (CSV)"),
    json_array: bool = typer.Option(False, "--json-array", help="Input is JSON array"),
    # Other options
    drop: bool = typer.Option(False, "--drop", help="Drop collection before import"),
    stop_on_error: bool = typer.Option(False, "--stop-on-error", help="Stop on first error"),
    ignore_blanks: bool = typer.Option(False, "--ignore-blanks", help="Ignore blank fields (CSV)"),
    parallel_jobs: Optional[int] = typer.Option(
        None, "--num-insertion-workers", "-j", help="Number of parallel insertion workers"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    timeout: int = typer.Option(1800, "--timeout", help="Operation timeout in seconds"),
):
    """Import data from JSON or CSV into MongoDB collection."""
    try:
        # Load from environment if --env specified
        if env:
            try:
                env_config = get_mongo_connection_config(env)
                # Use env config as defaults, but allow CLI parameters to override
                if not uri:
                    uri = env_config["uri"]
                if not database:
                    database = env_config["database"]
            except EnvironmentConfigError as e:
                typer.secho(f"✗ Environment configuration error: {e}", fg=typer.colors.RED)
                raise typer.Exit(code=1)

        # Validate required parameters
        if not database:
            typer.secho("✗ Error: --database is required (or use --env)", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        options = MongoImportOptions(
            uri=uri,
            host=host,
            port=port,
            username=username,
            password=password,
            auth_database=auth_db,
            auth_mechanism=auth_mechanism,
            use_tls=tls,
            tls_certificate_key_file=tls_certificate_key_file,
            tls_ca_file=tls_ca_file,
            tls_certificate_key_file_password=tls_certificate_key_file_password,
            tls_allow_invalid_certificates=tls_allow_invalid_certificates,
            tls_allow_invalid_hostnames=tls_allow_invalid_hostnames,
            read_preference=read_preference,
            replica_set_name=replica_set_name,
            connect_timeout=connect_timeout,
            socket_timeout=socket_timeout,
            database=database,
            collection=collection,
            input_file=input_file,
            import_format=import_format,
            import_mode=mode,
            upsert_fields=upsert_fields or [],
            fields=fields or [],
            headerline=headerline,
            json_array=json_array,
            drop_existing=drop,
            stop_on_error=stop_on_error,
            ignore_blanks=ignore_blanks,
            parallel_jobs=parallel_jobs,
            verbose=verbose,
        )

        orchestrator = MongoImportOrchestrator()
        result = orchestrator.import_data(options, timeout=timeout)

        if result.success:
            typer.secho(f"✓ Import completed successfully in {result.duration:.2f}s", fg=typer.colors.GREEN)
            if result.stdout:
                typer.echo(result.stdout)
        else:
            typer.secho(f"✗ Import failed (exit code {result.exit_code})", fg=typer.colors.RED)
            if result.stderr:
                typer.echo(result.stderr, err=True)
            raise typer.Exit(code=result.exit_code)

    except Exception as e:
        typer.secho(f"✗ Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
