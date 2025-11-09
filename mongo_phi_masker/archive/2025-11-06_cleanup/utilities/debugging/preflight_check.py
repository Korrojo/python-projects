#!/usr/bin/env python3
"""
Pre-Flight Check Script for MongoDB PHI Masker

Validates all configurations and dependencies before running the masking pipeline.
Performs comprehensive checks on:
- Configuration files
- Environment variables
- Database connectivity
- File system permissions
- Python environment
- Collection definitions

Usage:
    python scripts/preflight_check.py --collection Container
    python scripts/preflight_check.py --collection Patients --verbose
    python scripts/preflight_check.py --collection Tasks --fix
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.collection_rule_mapping import COLLECTION_RULE_MAPPING, get_phi_fields


@dataclass
class CheckResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendation: str | None = None
    severity: str = "error"  # error, warning, info


@dataclass
class CheckCategory:
    """Category of validation checks."""

    name: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Check if all checks in category passed."""
        return all(check.passed for check in self.checks)

    @property
    def error_count(self) -> int:
        """Count of failed error-level checks."""
        return sum(1 for check in self.checks if not check.passed and check.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count of failed warning-level checks."""
        return sum(1 for check in self.checks if not check.passed and check.severity == "warning")


class PreFlightChecker:
    """Comprehensive pre-flight validation system."""

    def __init__(
        self,
        collection: str,
        env_file: str = ".env",
        verbose: bool = False,
        fix: bool = False,
        src_env: str | None = None,
        dst_env: str | None = None,
        src_db: str | None = None,
        dst_db: str | None = None,
    ):
        """Initialize the pre-flight checker.

        Args:
            collection: Collection name to validate
            env_file: Path to environment file (legacy mode)
            verbose: Enable verbose output
            fix: Attempt to fix issues automatically
            src_env: Source environment preset (LOCL, DEV, STG, PROD, etc.)
            dst_env: Destination environment preset
            src_db: Optional source database override
            dst_db: Optional destination database override
        """
        self.collection = collection
        self.env_file = Path(env_file)
        self.verbose = verbose
        self.fix = fix

        # Environment preset mode
        self.src_env = src_env
        self.dst_env = dst_env
        self.src_db = src_db
        self.dst_db = dst_db
        self.using_env_presets = bool(src_env and dst_env)

        self.logger = self._setup_logging()
        self.categories: list[CheckCategory] = []

        # Load environment variables
        if self.using_env_presets:
            # Load from shared_config
            try:
                from src.utils.env_config import load_shared_config

                load_shared_config()
            except Exception as e:
                self.logger.warning(f"Could not load shared_config: {e}")
        elif self.env_file.exists():
            # Legacy mode - load from specific .env file
            load_dotenv(self.env_file)

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        return logger

    def run_all_checks(self) -> bool:
        """Run all pre-flight checks.

        Returns:
            True if all checks passed, False otherwise
        """
        self.logger.info("=" * 70)
        self.logger.info("MongoDB PHI Masker - Pre-Flight Checks")
        self.logger.info("=" * 70)
        self.logger.info(f"Collection: {self.collection}")

        if self.using_env_presets:
            self.logger.info(f"Source Environment: {self.src_env}")
            self.logger.info(f"Destination Environment: {self.dst_env}")
            if self.src_db:
                self.logger.info(f"Source Database Override: {self.src_db}")
            if self.dst_db:
                self.logger.info(f"Destination Database Override: {self.dst_db}")
        else:
            self.logger.info(f"Environment File: {self.env_file}")

        self.logger.info("")

        # Run all check categories
        self.check_python_environment()
        self.check_config_files()

        # Check environment configuration (new or legacy mode)
        if self.using_env_presets:
            self.check_shared_config_environments(self.src_env, self.dst_env, self.src_db, self.dst_db)
        else:
            self.check_environment_variables()

        self.check_collection_definition()
        self.check_file_system_permissions()
        self.check_database_connectivity()

        # Print summary
        self._print_summary()

        # Return overall status
        return all(category.passed for category in self.categories)

    def check_python_environment(self):
        """Check Python environment and dependencies."""
        category = CheckCategory(name="Python Environment")

        # Check Python version
        import sys

        python_version = sys.version_info
        if python_version >= (3, 11):
            category.checks.append(
                CheckResult(
                    name="Python Version",
                    passed=True,
                    message=f"Python {python_version.major}.{python_version.minor}.{python_version.micro}",
                    severity="info",
                )
            )
        else:
            category.checks.append(
                CheckResult(
                    name="Python Version",
                    passed=False,
                    message=f"Python {python_version.major}.{python_version.minor}.{python_version.micro} (< 3.11)",
                    recommendation="Upgrade to Python 3.11 or higher",
                    severity="error",
                )
            )

        # Check virtual environment
        in_venv = hasattr(sys, "prefix") and sys.prefix != sys.base_prefix
        if in_venv:
            category.checks.append(
                CheckResult(
                    name="Virtual Environment",
                    passed=True,
                    message=f"Active ({sys.prefix})",
                    severity="info",
                )
            )
        else:
            category.checks.append(
                CheckResult(
                    name="Virtual Environment",
                    passed=False,
                    message="No virtual environment detected",
                    recommendation="Activate virtual environment: source venv/bin/activate",
                    severity="warning",
                )
            )

        # Check required packages
        required_packages = ["pymongo", "python-dotenv", "psutil"]
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                category.checks.append(
                    CheckResult(
                        name=f"Package: {package}",
                        passed=True,
                        message="Installed",
                        severity="info",
                    )
                )
            except ImportError:
                category.checks.append(
                    CheckResult(
                        name=f"Package: {package}",
                        passed=False,
                        message="Not installed",
                        recommendation=f"Install package: pip install {package}",
                        severity="error",
                    )
                )

        self.categories.append(category)

    def check_config_files(self):
        """Check configuration file existence and validity."""
        category = CheckCategory(name="Configuration Files")

        # Check config file exists
        config_file = PROJECT_ROOT / "config" / "config_rules" / f"config_{self.collection}.json"

        if config_file.exists():
            category.checks.append(
                CheckResult(
                    name="Config File Exists",
                    passed=True,
                    message=str(config_file),
                    details={"path": str(config_file)},
                    severity="info",
                )
            )

            # Validate config file JSON
            try:
                with config_file.open() as f:
                    config_data = json.load(f)

                category.checks.append(
                    CheckResult(
                        name="Config File Valid JSON",
                        passed=True,
                        message="Valid JSON structure",
                        severity="info",
                    )
                )

                # Check required sections
                required_sections = ["mongodb", "processing", "masking"]
                for section in required_sections:
                    if section in config_data:
                        category.checks.append(
                            CheckResult(
                                name=f"Config Section: {section}",
                                passed=True,
                                message="Present",
                                severity="info",
                            )
                        )
                    else:
                        category.checks.append(
                            CheckResult(
                                name=f"Config Section: {section}",
                                passed=False,
                                message=f"Missing required section: {section}",
                                recommendation=f"Add '{section}' section to config file",
                                severity="error",
                            )
                        )

                # Check masking rules file exists
                if "masking" in config_data and "rules_path" in config_data["masking"]:
                    rules_file = PROJECT_ROOT / config_data["masking"]["rules_path"]
                    if rules_file.exists():
                        category.checks.append(
                            CheckResult(
                                name="Masking Rules File",
                                passed=True,
                                message=str(rules_file),
                                details={"path": str(rules_file)},
                                severity="info",
                            )
                        )
                    else:
                        category.checks.append(
                            CheckResult(
                                name="Masking Rules File",
                                passed=False,
                                message=f"File not found: {rules_file}",
                                recommendation=f"Create masking rules file at {rules_file}",
                                severity="error",
                            )
                        )

            except json.JSONDecodeError as e:
                category.checks.append(
                    CheckResult(
                        name="Config File Valid JSON",
                        passed=False,
                        message=f"Invalid JSON: {str(e)}",
                        recommendation="Fix JSON syntax errors in config file",
                        severity="error",
                    )
                )
        else:
            category.checks.append(
                CheckResult(
                    name="Config File Exists",
                    passed=False,
                    message=f"File not found: {config_file}",
                    recommendation=f"Create config file at {config_file}",
                    severity="error",
                )
            )

        self.categories.append(category)

    def check_environment_variables(self):
        """Check environment variables."""
        category = CheckCategory(name="Environment Variables")

        # Check .env file exists
        if self.env_file.exists():
            category.checks.append(
                CheckResult(
                    name="Environment File Exists",
                    passed=True,
                    message=str(self.env_file),
                    severity="info",
                )
            )
        else:
            category.checks.append(
                CheckResult(
                    name="Environment File Exists",
                    passed=False,
                    message=f"File not found: {self.env_file}",
                    recommendation="Copy .env.example to .env and configure",
                    severity="error",
                )
            )
            # If no .env file, skip other environment checks
            self.categories.append(category)
            return

        # Check required environment variables
        required_vars = [
            ("MONGO_SOURCE_HOST", "Source MongoDB host"),
            ("MONGO_SOURCE_PORT", "Source MongoDB port"),
            ("MONGO_SOURCE_DB", "Source database name"),
            ("MONGO_DEST_HOST", "Destination MongoDB host"),
            ("MONGO_DEST_PORT", "Destination MongoDB port"),
            ("MONGO_DEST_DB", "Destination database name"),
        ]

        for var_name, description in required_vars:
            value = os.getenv(var_name)
            if value:
                # Mask sensitive values in output
                display_value = value if var_name not in ["MONGO_SOURCE_PASSWORD", "MONGO_DEST_PASSWORD"] else "***"
                category.checks.append(
                    CheckResult(
                        name=f"Env Var: {var_name}",
                        passed=True,
                        message=f"{display_value}",
                        details={"description": description},
                        severity="info",
                    )
                )
            else:
                category.checks.append(
                    CheckResult(
                        name=f"Env Var: {var_name}",
                        passed=False,
                        message=f"Not set: {description}",
                        recommendation=f"Set {var_name} in {self.env_file}",
                        severity="error",
                    )
                )

        # Validate MongoDB URIs can be constructed
        try:
            source_uri = self._construct_mongodb_uri("source")
            if source_uri:
                category.checks.append(
                    CheckResult(
                        name="Source MongoDB URI",
                        passed=True,
                        message="URI constructable",
                        severity="info",
                    )
                )
        except Exception as e:
            category.checks.append(
                CheckResult(
                    name="Source MongoDB URI",
                    passed=False,
                    message=f"Cannot construct URI: {str(e)}",
                    recommendation="Check MONGO_SOURCE_* environment variables",
                    severity="error",
                )
            )

        try:
            dest_uri = self._construct_mongodb_uri("dest")
            if dest_uri:
                category.checks.append(
                    CheckResult(
                        name="Destination MongoDB URI",
                        passed=True,
                        message="URI constructable",
                        severity="info",
                    )
                )
        except Exception as e:
            category.checks.append(
                CheckResult(
                    name="Destination MongoDB URI",
                    passed=False,
                    message=f"Cannot construct URI: {str(e)}",
                    recommendation="Check MONGO_DEST_* environment variables",
                    severity="error",
                )
            )

        self.categories.append(category)

    def check_shared_config_environments(
        self, src_env: str, dst_env: str, src_db: str | None = None, dst_db: str | None = None
    ):
        """Check shared_config environment presets.

        Args:
            src_env: Source environment (LOCL, DEV, STG, PROD, etc.)
            dst_env: Destination environment
            src_db: Optional source database override
            dst_db: Optional destination database override
        """
        category = CheckCategory(name="Shared Config Environments")

        # Import env_config utilities
        try:
            from src.utils.env_config import (
                get_shared_config_path,
                validate_env_config,
                get_env_config,
            )

            # Check shared_config/.env exists
            try:
                shared_config_path = get_shared_config_path()
                category.checks.append(
                    CheckResult(
                        name="Shared Config File",
                        passed=True,
                        message=str(shared_config_path),
                        severity="info",
                    )
                )
            except FileNotFoundError as e:
                category.checks.append(
                    CheckResult(
                        name="Shared Config File",
                        passed=False,
                        message=str(e),
                        recommendation="Ensure shared_config/.env exists at repository root",
                        severity="error",
                    )
                )
                self.categories.append(category)
                return

            # Validate source environment
            src_valid, src_errors = validate_env_config(src_env)
            if src_valid:
                src_config = get_env_config(src_env, src_db)
                category.checks.append(
                    CheckResult(
                        name=f"Source Environment: {src_env}",
                        passed=True,
                        message=f"URI: {src_config['uri']}, DB: {src_config['database']}",
                        severity="info",
                    )
                )
            else:
                for error in src_errors:
                    category.checks.append(
                        CheckResult(
                            name=f"Source Environment: {src_env}",
                            passed=False,
                            message=error,
                            recommendation=f"Configure {src_env} environment in shared_config/.env",
                            severity="error",
                        )
                    )

            # Validate destination environment
            dst_valid, dst_errors = validate_env_config(dst_env)
            if dst_valid:
                dst_config = get_env_config(dst_env, dst_db)
                category.checks.append(
                    CheckResult(
                        name=f"Destination Environment: {dst_env}",
                        passed=True,
                        message=f"URI: {dst_config['uri']}, DB: {dst_config['database']}",
                        severity="info",
                    )
                )
            else:
                for error in dst_errors:
                    category.checks.append(
                        CheckResult(
                            name=f"Destination Environment: {dst_env}",
                            passed=False,
                            message=error,
                            recommendation=f"Configure {dst_env} environment in shared_config/.env",
                            severity="error",
                        )
                    )

        except ImportError as e:
            category.checks.append(
                CheckResult(
                    name="Environment Config Module",
                    passed=False,
                    message=f"Cannot import env_config: {str(e)}",
                    recommendation="Ensure src/utils/env_config.py exists",
                    severity="error",
                )
            )

        self.categories.append(category)

    def check_collection_definition(self):
        """Check collection is properly defined in config."""
        category = CheckCategory(name="Collection Definition")

        # Check collection in COLLECTION_RULE_MAPPING
        if self.collection in COLLECTION_RULE_MAPPING:
            rule_group = COLLECTION_RULE_MAPPING[self.collection]
            category.checks.append(
                CheckResult(
                    name="Collection in Rule Mapping",
                    passed=True,
                    message=f"Mapped to rule group: {rule_group}",
                    details={"rule_group": rule_group},
                    severity="info",
                )
            )
        else:
            category.checks.append(
                CheckResult(
                    name="Collection in Rule Mapping",
                    passed=False,
                    message=f"Collection '{self.collection}' not found in COLLECTION_RULE_MAPPING",
                    recommendation=f"Add '{self.collection}' to config/collection_rule_mapping.py",
                    severity="error",
                )
            )

        # Check PHI fields defined
        try:
            phi_fields = get_phi_fields(self.collection)
            if phi_fields:
                category.checks.append(
                    CheckResult(
                        name="PHI Fields Defined",
                        passed=True,
                        message=f"{len(phi_fields)} PHI fields defined",
                        details={"phi_field_count": len(phi_fields), "fields": phi_fields[:5]},
                        severity="info",
                    )
                )
            else:
                category.checks.append(
                    CheckResult(
                        name="PHI Fields Defined",
                        passed=False,
                        message=f"No PHI fields defined for '{self.collection}'",
                        recommendation=f"Add PHI fields for '{self.collection}' in config/collection_rule_mapping.py",
                        severity="error",
                    )
                )
        except Exception as e:
            category.checks.append(
                CheckResult(
                    name="PHI Fields Defined",
                    passed=False,
                    message=f"Error getting PHI fields: {str(e)}",
                    recommendation="Check collection definition in config/collection_rule_mapping.py",
                    severity="error",
                )
            )

        self.categories.append(category)

    def check_file_system_permissions(self):
        """Check file system permissions for required directories."""
        category = CheckCategory(name="File System Permissions")

        # Directories that need to be writable
        required_dirs = [
            ("logs", "Log files"),
            ("reports", "Validation reports"),
            ("checkpoints", "Processing checkpoints"),
        ]

        for dir_name, description in required_dirs:
            dir_path = PROJECT_ROOT / dir_name

            # Check if directory exists
            if not dir_path.exists():
                if self.fix:
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        category.checks.append(
                            CheckResult(
                                name=f"Directory: {dir_name}",
                                passed=True,
                                message=f"Created directory: {dir_path}",
                                severity="info",
                            )
                        )
                    except Exception as e:
                        category.checks.append(
                            CheckResult(
                                name=f"Directory: {dir_name}",
                                passed=False,
                                message=f"Cannot create: {str(e)}",
                                recommendation=f"Create directory: mkdir -p {dir_path}",
                                severity="error",
                            )
                        )
                else:
                    category.checks.append(
                        CheckResult(
                            name=f"Directory: {dir_name}",
                            passed=False,
                            message=f"Directory does not exist: {dir_path}",
                            recommendation=f"Create directory: mkdir -p {dir_path} (or use --fix)",
                            severity="warning",
                        )
                    )
                continue

            # Check if directory is writable
            if os.access(dir_path, os.W_OK):
                category.checks.append(
                    CheckResult(
                        name=f"Directory: {dir_name}",
                        passed=True,
                        message=f"Writable ({description})",
                        details={"path": str(dir_path)},
                        severity="info",
                    )
                )
            else:
                category.checks.append(
                    CheckResult(
                        name=f"Directory: {dir_name}",
                        passed=False,
                        message=f"Not writable: {dir_path}",
                        recommendation=f"Fix permissions: chmod u+w {dir_path}",
                        severity="error",
                    )
                )

        self.categories.append(category)

    def check_database_connectivity(self):
        """Check database connectivity and permissions."""
        category = CheckCategory(name="Database Connectivity")

        # Check source database
        try:
            source_uri = self._construct_mongodb_uri("source")
            if source_uri:
                client = MongoClient(source_uri, serverSelectionTimeoutMS=5000)
                client.admin.command("ping")

                category.checks.append(
                    CheckResult(
                        name="Source Database Connection",
                        passed=True,
                        message="Connected successfully",
                        severity="info",
                    )
                )

                # Check if source collection exists
                source_db = os.getenv("MONGO_SOURCE_DB")
                source_coll = os.getenv("MONGO_SOURCE_COLL", self.collection)
                if source_db:
                    db = client[source_db]
                    if source_coll in db.list_collection_names():
                        doc_count = db[source_coll].count_documents({})
                        category.checks.append(
                            CheckResult(
                                name="Source Collection Exists",
                                passed=True,
                                message=f"{source_db}.{source_coll} ({doc_count} documents)",
                                details={"database": source_db, "collection": source_coll, "count": doc_count},
                                severity="info",
                            )
                        )
                    else:
                        category.checks.append(
                            CheckResult(
                                name="Source Collection Exists",
                                passed=False,
                                message=f"Collection not found: {source_db}.{source_coll}",
                                recommendation="Verify collection name or create collection",
                                severity="error",
                            )
                        )

                client.close()

        except ConnectionFailure as e:
            category.checks.append(
                CheckResult(
                    name="Source Database Connection",
                    passed=False,
                    message=f"Connection failed: {str(e)}",
                    recommendation="Check MongoDB is running and connection settings",
                    severity="error",
                )
            )
        except Exception as e:
            category.checks.append(
                CheckResult(
                    name="Source Database Connection",
                    passed=False,
                    message=f"Error: {str(e)}",
                    recommendation="Check source database configuration",
                    severity="error",
                )
            )

        # Check destination database
        try:
            dest_uri = self._construct_mongodb_uri("dest")
            if dest_uri:
                client = MongoClient(dest_uri, serverSelectionTimeoutMS=5000)
                client.admin.command("ping")

                category.checks.append(
                    CheckResult(
                        name="Destination Database Connection",
                        passed=True,
                        message="Connected successfully",
                        severity="info",
                    )
                )

                # Check write permissions
                dest_db = os.getenv("MONGO_DEST_DB")
                if dest_db:
                    try:
                        db = client[dest_db]
                        # Try to insert a test document
                        test_coll = db["_preflight_test"]
                        test_coll.insert_one({"test": True})
                        test_coll.delete_one({"test": True})
                        test_coll.drop()

                        category.checks.append(
                            CheckResult(
                                name="Destination Write Permissions",
                                passed=True,
                                message=f"Write access confirmed for {dest_db}",
                                severity="info",
                            )
                        )
                    except OperationFailure as e:
                        category.checks.append(
                            CheckResult(
                                name="Destination Write Permissions",
                                passed=False,
                                message=f"No write permission: {str(e)}",
                                recommendation="Check user permissions for destination database",
                                severity="error",
                            )
                        )

                client.close()

        except ConnectionFailure as e:
            category.checks.append(
                CheckResult(
                    name="Destination Database Connection",
                    passed=False,
                    message=f"Connection failed: {str(e)}",
                    recommendation="Check MongoDB is running and connection settings",
                    severity="error",
                )
            )
        except Exception as e:
            category.checks.append(
                CheckResult(
                    name="Destination Database Connection",
                    passed=False,
                    message=f"Error: {str(e)}",
                    recommendation="Check destination database configuration",
                    severity="error",
                )
            )

        self.categories.append(category)

    def _construct_mongodb_uri(self, db_type: str) -> str:
        """Construct MongoDB URI from environment variables.

        Args:
            db_type: 'source' or 'dest'

        Returns:
            MongoDB connection URI
        """
        prefix = f"MONGO_{db_type.upper()}"

        host = os.getenv(f"{prefix}_HOST")
        port = os.getenv(f"{prefix}_PORT")
        user = os.getenv(f"{prefix}_USER")
        password = os.getenv(f"{prefix}_PASSWORD")

        if not host or not port:
            raise ValueError(f"Missing {prefix}_HOST or {prefix}_PORT")

        if user and password:
            uri = f"mongodb://{user}:{password}@{host}:{port}/"
        else:
            uri = f"mongodb://{host}:{port}/"

        return uri

    def _print_summary(self):
        """Print summary of all check results."""
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("Pre-Flight Check Summary")
        self.logger.info("=" * 70)

        total_errors = 0
        total_warnings = 0

        for category in self.categories:
            status = "✓" if category.passed else "✗"
            self.logger.info(f"\n{status} {category.name}")

            if self.verbose or not category.passed:
                for check in category.checks:
                    if self.verbose or not check.passed:
                        status_symbol = "✓" if check.passed else "✗"
                        self.logger.info(f"  {status_symbol} {check.name}: {check.message}")

                        if not check.passed and check.recommendation:
                            self.logger.info(f"    → {check.recommendation}")

            total_errors += category.error_count
            total_warnings += category.warning_count

        self.logger.info("")
        self.logger.info("=" * 70)

        if total_errors == 0 and total_warnings == 0:
            self.logger.info("✓ All pre-flight checks passed!")
            self.logger.info("")
            self.logger.info("You can proceed with masking:")
            self.logger.info(f"  python masking.py --config config/config_rules/config_{self.collection}.json")
        else:
            if total_errors > 0:
                self.logger.error(f"✗ {total_errors} error(s) found")
            if total_warnings > 0:
                self.logger.warning(f"⚠ {total_warnings} warning(s) found")

            self.logger.info("")
            self.logger.info("Please fix the issues above before running masking.")

        self.logger.info("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pre-flight validation for MongoDB PHI Masker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Environment-based validation (recommended)
  python scripts/preflight_check.py --collection Patients --src-env LOCL --dst-env DEV

  # With database overrides
  python scripts/preflight_check.py --collection Patients --src-env DEV --dst-env DEV --src-db devdb --dst-db devdb

  # Legacy mode
  python scripts/preflight_check.py --collection Patients --env .env
        """,
    )

    parser.add_argument("--collection", required=True, help="Collection name to validate")

    # Environment preset mode (new)
    parser.add_argument(
        "--src-env",
        choices=["LOCL", "DEV", "STG", "TRNG", "PERF", "PRPRD", "PROD"],
        help="Source environment (loads from shared_config/.env)",
    )
    parser.add_argument(
        "--dst-env",
        choices=["LOCL", "DEV", "STG", "TRNG", "PERF", "PRPRD", "PROD"],
        help="Destination environment (loads from shared_config/.env)",
    )
    parser.add_argument("--src-db", help="Source database name override")
    parser.add_argument("--dst-db", help="Destination database name override")

    # Legacy mode
    parser.add_argument("--env", default=".env", help="Path to environment file (legacy mode, default: .env)")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues automatically")

    args = parser.parse_args()

    # Validate arguments
    using_env_presets = args.src_env or args.dst_env

    if using_env_presets:
        if not args.src_env or not args.dst_env:
            print("ERROR: Both --src-env and --dst-env are required when using environment presets")
            sys.exit(1)

    # Run pre-flight checks
    checker = PreFlightChecker(
        collection=args.collection,
        env_file=args.env,
        verbose=args.verbose,
        fix=args.fix,
        src_env=args.src_env,
        dst_env=args.dst_env,
        src_db=args.src_db,
        dst_db=args.dst_db,
    )

    success = checker.run_all_checks()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
