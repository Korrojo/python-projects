"""Command-line interface package for MongoDB PHI Masking Tool."""

from src.cli.parser import get_cli_config, parse_arguments

__all__ = ["parse_arguments", "get_cli_config"]
