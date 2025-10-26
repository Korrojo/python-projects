#!/usr/bin/env python3
"""
Users Provider Update Script
Updates Users collection with Athena provider information from CSV file.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from src.connectors.mongodb_connector import DatabaseService

from common_config.config import get_settings  # type: ignore
from common_config.utils.logger import get_logger, setup_logging  # type: ignore


class UsersProviderUpdater:
    """Main class for updating users with provider information from CSV."""

    def __init__(self, csv_file: str):
        """
        Initialize updater with environment and CSV file.

        Args:
            csv_file (str): Path to CSV file with provider data
        """
        self.csv_file = csv_file
        self.db_service = DatabaseService()
        self.stats = {
            "processed": 0,
            "successful": 0,
            "skipped": 0,
            "errors": 0,
            "users_not_found": 0,
            "duplicates_skipped": 0,
            "already_has_athena": 0,
        }

    def setup_logging(self):
        """Setup logging to shared logs/users-provider-update."""
        settings = get_settings()  # type: ignore
        project_logs = Path(settings.paths.logs) / "users-provider-update"  # type: ignore
        project_logs.mkdir(parents=True, exist_ok=True)
        setup_logging(log_dir=project_logs, level=settings.log_level)  # type: ignore
        logger = get_logger(__name__)  # type: ignore
        logger.info("Using shared logs directory for users-provider-update")
        logger.info(f"[DEBUG] CSV file: {self.csv_file}")

    def validate_csv_row(self, row):
        """
        Validate CSV row has required fields.

        Args:
            row (pd.Series): CSV row data

        Returns:
            dict: Validation result with is_valid flag and data/error
        """
        try:
            # Check required fields
            if pd.isna(row.get("ID")):
                return {"is_valid": False, "error": "Missing ID field"}

            if pd.isna(row.get("First")) and pd.isna(row.get("Last")):
                return {"is_valid": False, "error": "Missing First and Last name fields"}

            # Extract and validate data
            try:
                athena_provider_id = int(row["ID"])
            except (ValueError, TypeError):
                return {"is_valid": False, "error": f"Invalid ID value: {row.get('ID')}"}

            first_name = str(row.get("First", "")).strip()
            last_name = str(row.get("Last", "")).strip()
            athena_user_name = str(row.get("User Name", "")).strip()
            npi = str(row.get("NPI", "")).strip()

            if not first_name or not last_name:
                return {"is_valid": False, "error": "First or Last name is empty"}

            return {
                "is_valid": True,
                "data": {
                    "athena_provider_id": athena_provider_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "athena_user_name": athena_user_name if athena_user_name else None,
                    "npi": npi if npi else None,
                },
            }

        except Exception as e:
            return {"is_valid": False, "error": f"Validation error: {str(e)}"}

    def process_record(self, row):
        """
        Process a single CSV record.

        Args:
            row (pd.Series): CSV row data
        """
        self.stats["processed"] += 1

        try:
            # Validate CSV row
            validation = self.validate_csv_row(row)

            if not validation["is_valid"]:
                logging.info(f"{validation['error']} Skipping.")
                self.stats["errors"] += 1
                return

            data = validation["data"]
            first_name = data["first_name"]
            last_name = data["last_name"]
            athena_provider_id = data["athena_provider_id"]
            athena_user_name = data["athena_user_name"]
            npi = data["npi"]

            # Find users (case-insensitive, IsActive: true)
            users = self.db_service.find_users(first_name, last_name)

            if len(users) == 0:
                logging.info(f"No active user found for {first_name} {last_name} (user may be inactive or not exist).")
                self.stats["skipped"] += 1
                self.stats["users_not_found"] += 1
                return

            # STRICT: If more than one active user found, skip ALL
            if len(users) > 1:
                user_ids = [str(u["_id"]) for u in users]
                logging.info(
                    f"Found duplicate users for {first_name} {last_name}. Skipping update for ALL matching records. User IDs: [{', '.join(user_ids)}]"
                )
                self.stats["skipped"] += 1
                self.stats["duplicates_skipped"] += 1
                return

            user = users[0]

            # Check if AthenaProviderId already exists
            if user.get("AthenaProviderId") is not None:
                logging.info(
                    f"User {first_name} {last_name} (ID: {user['_id']}) already has an AthenaProviderId ({user['AthenaProviderId']}). Skipping."
                )
                self.stats["skipped"] += 1
                self.stats["already_has_athena"] += 1
                return

            # Update the user
            update_doc = {"AthenaProviderId": athena_provider_id, "AthenaUserName": athena_user_name, "NPI": npi}

            self.db_service.update_user(user["_id"], update_doc)
            logging.info(f"Successfully updated user {first_name} {last_name} (ID: {user['_id']}).")
            self.stats["successful"] += 1

        except Exception as e:
            logging.error(f"Error processing record for {row.get('First')} {row.get('Last')}: {e}")
            self.stats["errors"] += 1

    def print_summary(self):
        """Print summary statistics."""
        logging.info("--------------------------------------------------\n")
        logging.info("**************************************************")
        logging.info("                 SUMMARY REPORT                   ")
        logging.info("**************************************************")
        logging.info(f"Total records processed : {self.stats['processed']}")
        logging.info(f"Successful updates      : {self.stats['successful']}")
        logging.info(f"Skipped records         : {self.stats['skipped']}")
        logging.info(f"  - Users not found     : {self.stats['users_not_found']}")
        logging.info(f"  - Duplicates skipped  : {self.stats['duplicates_skipped']}")
        logging.info(f"  - Already has Athena  : {self.stats['already_has_athena']}")
        logging.info(f"Errors                  : {self.stats['errors']}")
        logging.info("**************************************************\n")

    def run(self):
        """Main execution method."""
        try:
            self.setup_logging()

            logging.info("Starting Users Provider Update process...")

            # Connect to database
            self.db_service.connect()

            # Create backup
            self.db_service.create_backup()

            # Read CSV file
            if not os.path.exists(self.csv_file):
                # Try unified data/input/<project>/ if a bare filename/relative path was given
                settings = get_settings()  # type: ignore
                base = Path(settings.paths.data_input) / "users-provider-update"  # type: ignore
                base.mkdir(parents=True, exist_ok=True)
                fallback_path = base / Path(self.csv_file).name
                if fallback_path.exists():
                    self.csv_file = str(fallback_path)
                else:
                    raise FileNotFoundError(f"CSV file not found: {self.csv_file}")

            logging.info(f"Reading CSV file: {self.csv_file}")
            df = pd.read_csv(self.csv_file)
            logging.info(f"CSV file processed: {len(df)} total records found.")

            # Process each record
            logging.info("Starting database update operations...")
            for _, row in df.iterrows():
                self.process_record(row)

            logging.info("All database operations have completed.")
            self.print_summary()

        except Exception as e:
            logging.error(f"Script failed: {e}")
            sys.exit(1)

        finally:
            self.db_service.close()


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(description="Update Users collection with Athena provider information from CSV")
    parser.add_argument("--csv", required=True, help="Path to CSV file with provider data")
    # Legacy --env removed; configuration comes from shared_config/.env via common_config

    args = parser.parse_args()
    updater = UsersProviderUpdater(args.csv)
    updater.run()


if __name__ == "__main__":
    main()
