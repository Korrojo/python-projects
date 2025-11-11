"""Main CLI entry point for mongo_backup_tools."""

import typer

app = typer.Typer(
    name="mongo-backup-tools",
    help="Comprehensive MongoDB backup, restore, export, and import toolkit",
    no_args_is_help=True,
)


@app.command("version")
def show_version():
    """Show version information."""
    from mongo_backup_tools import __version__

    typer.echo(f"mongo-backup-tools version {__version__}")


if __name__ == "__main__":
    app()
