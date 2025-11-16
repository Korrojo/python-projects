#!/usr/bin/env python3
"""
Users Update Validation Script
Validates updates by comparing CSV data with MongoDB collection.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from src.connectors.mongodb_connector import DatabaseService

from common_config.config import get_settings  # type: ignore
from common_config.utils.logger import setup_logging  # type: ignore


class UsersUpdateValidator:
    """Validator for users provider updates."""

    def __init__(self, csv_file):
        """
        Initialize validator.

        Args:
            csv_file (str): Path to CSV file with provider data
        """
        self.csv_file = csv_file
        self.db_service = DatabaseService()
        self.validation_results = {"total_checked": 0, "matched": 0, "not_found": 0, "mismatched": 0, "details": []}

    def setup_logging(self):
        """Setup logging under shared logs/users-provider-update."""
        settings = get_settings()  # type: ignore
        proj_logs = Path(settings.paths.logs) / "users-provider-update"  # type: ignore
        proj_logs.mkdir(parents=True, exist_ok=True)
        setup_logging(log_dir=proj_logs, level=getattr(settings, "log_level", "INFO"))  # type: ignore
        logging.info(f"[DEBUG] Validation log dir: {proj_logs}")
        logging.info(f"[DEBUG] CSV file: {self.csv_file}")

    def validate_record(self, row):
        """
        Validate a single CSV record against MongoDB.

        Args:
            row (pd.Series): CSV row data
        """
        self.validation_results["total_checked"] += 1

        try:
            # Extract CSV data with normalization
            first_name = str(row.get("First", "")).strip()
            last_name = str(row.get("Last", "")).strip()
            try:
                expected_athena_id = int(row["ID"])
            except Exception:
                expected_athena_id = None
            expected_username = str(row.get("User Name", "")).strip()
            npi_val = row.get("NPI", "")
            if pd.isna(npi_val):
                expected_npi = ""
            else:
                if isinstance(npi_val, (int, float)):
                    try:
                        expected_npi = str(int(npi_val))
                    except Exception:
                        expected_npi = str(npi_val).strip()
                else:
                    s = str(npi_val).strip()
                    if s.endswith(".0"):
                        try:
                            s = str(int(float(s)))
                        except Exception:
                            s = s.rstrip("0").rstrip(".") if "." in s else s
                    expected_npi = s

            # Find user in MongoDB
            users = self.db_service.find_users(first_name, last_name)

            if len(users) == 0:
                logging.info(f"❌ NOT FOUND: {first_name} {last_name}")
                self.validation_results["not_found"] += 1
                self.validation_results["details"].append(
                    {"name": f"{first_name} {last_name}", "status": "NOT_FOUND", "expected": expected_athena_id}
                )
                return

            if len(users) > 1:
                logging.info(f"⚠️  DUPLICATE: {first_name} {last_name} ({len(users)} users found)")
                self.validation_results["details"].append(
                    {"name": f"{first_name} {last_name}", "status": "DUPLICATE", "count": len(users)}
                )
                return

            user = users[0]

            # Compare values (normalized)
            actual_athena_id = user.get("AthenaProviderId")
            try:
                actual_athena_id_int = int(actual_athena_id) if actual_athena_id is not None else None
            except Exception:
                actual_athena_id_int = None
            actual_username = user.get("AthenaUserName")
            actual_npi = user.get("NPI")
            if actual_npi is None:
                actual_npi_str = ""
            elif isinstance(actual_npi, (int, float)):
                try:
                    actual_npi_str = str(int(actual_npi))
                except Exception:
                    actual_npi_str = str(actual_npi).strip()
            else:
                actual_npi_str = str(actual_npi).strip()

            mismatches = []

            if expected_athena_id is not None:
                if actual_athena_id_int != expected_athena_id:
                    mismatches.append(f"AthenaProviderId: expected {expected_athena_id}, got {actual_athena_id_int}")

            if expected_username and actual_username != expected_username:
                mismatches.append(f"AthenaUserName: expected '{expected_username}', got '{actual_username}'")

            if expected_npi and actual_npi_str != expected_npi:
                mismatches.append(f"NPI: expected '{expected_npi}', got '{actual_npi_str}'")

            if mismatches:
                logging.info(f"⚠️  MISMATCH: {first_name} {last_name}")
                for mismatch in mismatches:
                    logging.info(f"    - {mismatch}")
                self.validation_results["mismatched"] += 1
                self.validation_results["details"].append(
                    {"name": f"{first_name} {last_name}", "status": "MISMATCH", "mismatches": mismatches}
                )
            else:
                logging.info(f"✅ MATCH: {first_name} {last_name} (AthenaProviderId: {actual_athena_id})")
                self.validation_results["matched"] += 1
                self.validation_results["details"].append(
                    {"name": f"{first_name} {last_name}", "status": "MATCH", "athena_id": actual_athena_id}
                )

        except Exception as e:
            logging.error(f"Error validating {row.get('First')} {row.get('Last')}: {e}")

    def print_summary(self):
        """Print validation summary."""
        logging.info("\n" + "=" * 80)
        logging.info("VALIDATION SUMMARY")
        logging.info("=" * 80)
        logging.info(f"Total records checked   : {self.validation_results['total_checked']}")
        logging.info(f"Matched (✅)            : {self.validation_results['matched']}")
        logging.info(f"Not found (❌)          : {self.validation_results['not_found']}")
        logging.info(f"Mismatched (⚠️)         : {self.validation_results['mismatched']}")

        if self.validation_results["total_checked"] > 0:
            match_rate = (self.validation_results["matched"] / self.validation_results["total_checked"]) * 100
            logging.info(f"Match rate              : {match_rate:.1f}%")

        logging.info("=" * 80 + "\n")

    def run(self, sample_size=None):
        """
        Run validation.

        Args:
            sample_size (int, optional): Number of records to validate. If None, validates all.
        """
        try:
            self.setup_logging()

            logging.info("Starting Users Update Validation...")

            # Connect to database (unified settings)
            self.db_service.connect()

            # Read CSV file
            if not os.path.exists(self.csv_file):
                # Fallback to shared input path if a basename was provided
                settings = get_settings()  # type: ignore
                candidate = Path(settings.paths.data_input) / "users-provider-update" / Path(self.csv_file).name  # type: ignore
                if candidate.exists():
                    self.csv_file = str(candidate)
                else:
                    raise FileNotFoundError(f"CSV file not found: {self.csv_file}")

            logging.info(f"Reading CSV file: {self.csv_file}")
            df = pd.read_csv(self.csv_file)

            if sample_size:
                df = df.head(sample_size)
                logging.info(f"Validating first {sample_size} records from CSV")
            else:
                logging.info(f"Validating all {len(df)} records from CSV")

            logging.info("\n" + "=" * 80)
            logging.info("VALIDATION RESULTS")
            logging.info("=" * 80 + "\n")

            # Validate each record
            for _, row in df.iterrows():
                self.validate_record(row)

            self.print_summary()

        except Exception as e:
            logging.error(f"Validation failed: {e}")
            sys.exit(1)

        finally:
            self.db_service.close()


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(description="Validate Users collection updates against CSV data")
    parser.add_argument("--csv", required=True, help="Path to CSV file with provider data")
    parser.add_argument("--sample", type=int, default=None, help="Number of records to validate (default: all)")

    args = parser.parse_args()

    validator = UsersUpdateValidator(args.csv)
    validator.run(sample_size=args.sample)


if __name__ == "__main__":
    main()
