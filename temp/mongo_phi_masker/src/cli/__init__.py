"""Command-line interface package for MongoDB PHI Masking Tool."""

from src.cli.parser import parse_arguments, get_cli_config

__all__ = ["parse_arguments", "get_cli_config"] 