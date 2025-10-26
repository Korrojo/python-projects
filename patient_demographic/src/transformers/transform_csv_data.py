#!/usr/bin/env python3
"""
CSV Data Transformation Script for Patient Demographics
Transforms raw CSV data to match MongoDB schema for AD_Patients_20250721 collection
"""

import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from common_config.config import get_settings  # type: ignore
from common_config.utils.logger import setup_logging  # type: ignore

# Configure logging under shared logs/patient_demographic
_settings = get_settings()  # type: ignore
_proj_logs = Path(_settings.paths.logs) / "patient_demographic"  # type: ignore
_proj_logs.mkdir(parents=True, exist_ok=True)
setup_logging(log_dir=_proj_logs, level=_settings.log_level)  # type: ignore
logger = logging.getLogger(__name__)
logger.info("Using shared logs directory for patient_demographic")


def parse_date_with_2digit_year(date_str):
    """Parse date string, handling 2-digit years by assuming 19xx for years > 50, 20xx otherwise."""
    if not date_str or pd.isna(date_str):
        return None

    try:
        date_str = str(date_str).strip()
        if not date_str:
            return None

        # Handle MM/DD/YY format
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 3:
                month, day, year = parts
                year = year.strip()

                # Handle 2-digit years
                if len(year) == 2:
                    year_int = int(year)
                    if year_int > 50:  # Assume 1951-1999
                        year = f"19{year}"
                    else:  # Assume 2000-2050
                        year = f"20{year}"

                # Reconstruct date string
                date_str = f"{month}/{day}/{year}"

        # Parse the date
        parsed_date = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(parsed_date):
            logging.warning(f"Could not parse date: {date_str}")
            return None

        # Type guard: ensure parsed_date is a Timestamp before calling strftime
        if isinstance(parsed_date, pd.Timestamp):
            return parsed_date.strftime("%Y-%m-%d")
        return None

    except Exception as e:
        logging.warning(f"Error parsing date '{date_str}': {e}")
        return None


def clean_phone_number(phone_str):
    """Clean phone number to digits-only format (matching archival pattern)."""
    if not phone_str or pd.isna(phone_str):
        return None

    # Remove all non-digit characters (following archival pattern)
    digits_only = re.sub(r"\D", "", str(phone_str))

    if len(digits_only) == 10:
        # Return 10-digit number as-is (e.g., "5559388855")
        return digits_only
    elif len(digits_only) == 11 and digits_only.startswith("1"):
        # Remove leading 1 and return 10 digits (e.g., "15559388855" -> "5559388855")
        return digits_only[1:]
    elif len(digits_only) > 0:
        # Return digits-only for any other format
        return digits_only
    else:
        # Return None if no digits found
        return None


def parse_full_name(full_name):
    """Parse full name into first and last name."""
    if not full_name or pd.isna(full_name):
        return None, None

    name_parts = str(full_name).strip().split()
    if len(name_parts) >= 2:
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:])  # Handle multiple last name parts
        return first_name, last_name
    elif len(name_parts) == 1:
        return name_parts[0], None
    else:
        return None, None


def transform_csv_data(input_csv_path, output_csv_path):
    """Transform raw CSV data to match MongoDB schema with correct data types."""

    try:
        # Read the CSV file, skipping the first line if it's a report header
        logging.info(f"Reading CSV file: {input_csv_path}")

        # Check if first line is a report header
        with open(input_csv_path, encoding="utf-8") as f:
            first_line = f.readline().strip()

        # Skip first line if it's a report header
        skiprows = 1 if first_line.startswith("REPORT NAME") else 0
        df = pd.read_csv(input_csv_path, skiprows=skiprows)

        logging.info(f"Original CSV has {len(df)} rows and {len(df.columns)} columns")
        logging.info(f"Columns: {list(df.columns)}")

        # Vectorized transformation
        # PatientId is 7-digit from 'ptnt bqty lgcy ptnt d', AthenaPatientId is 4-digit from 'patientid'
        df["PatientId"] = pd.to_numeric(df["ptnt bqty lgcy ptnt d"], errors="coerce").astype("Int64")  # type: ignore[union-attr]
        df["AthenaPatientId"] = pd.to_numeric(df["patientid"], errors="coerce").astype("Int64")  # type: ignore[union-attr]
        df["FirstName"], df["LastName"] = zip(*df["patient name"].apply(parse_full_name), strict=False)
        df["Dob"] = df["patientdob"].where(pd.notna(df["patientdob"]), None)
        df["Gender"] = df["patientsex"].map(lambda x: "Female" if x == "F" else "Male" if x == "M" else x)
        df["Email"] = df["patient email"].where(pd.notna(df["patient email"]), None)
        df["Street1"] = df["patient address1"].where(pd.notna(df["patient address1"]), None)
        df["Street2"] = df["patient address2"].where(pd.notna(df["patient address2"]), None)
        df["City"] = df["patient city"].where(pd.notna(df["patient city"]), None)
        df["StateCode"] = df["patient state"].where(pd.notna(df["patient state"]), None)
        df["Zip5"] = df["patient zip"].apply(lambda x: str(x) if pd.notna(x) else None)
        df["PhoneNumber"] = df["patient homephone"].apply(clean_phone_number)
        df["UpdatedOn"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df["LastModifiedBy"] = "CSV_IMPORT_SCRIPT"

        # Select only the transformed columns
        transformed_df = df[
            [
                "PatientId",
                "AthenaPatientId",
                "FirstName",
                "LastName",
                "Dob",
                "Gender",
                "Email",
                "Street1",
                "Street2",
                "City",
                "StateCode",
                "Zip5",
                "PhoneNumber",
                "UpdatedOn",
                "LastModifiedBy",
            ]
        ].copy()

        # Remove rows where PatientId is None or 0
        initial_count = len(transformed_df)
        transformed_df = transformed_df.dropna(subset=["PatientId"])  # type: ignore[call-overload]
        transformed_df = transformed_df[transformed_df["PatientId"] != 0]
        final_count = len(transformed_df)

        if initial_count != final_count:
            logging.warning(f"Removed {initial_count - final_count} rows with invalid PatientId")

        # Save transformed data
        logging.info(f"Saving transformed data to: {output_csv_path}")
        transformed_df.to_csv(output_csv_path, index=False)

        logging.info("Transformation completed successfully!")
        logging.info(f"Transformed CSV has {len(transformed_df)} rows and {len(transformed_df.columns)} columns")
        logging.info(f"Output columns: {list(transformed_df.columns)}")

        # Log sample of transformed data
        logging.info("\nSample of transformed data:")
        logging.info(f"{transformed_df.head()}")

        return True

    except Exception as e:
        logging.error(f"Error during transformation: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Transform patient demographics CSV to MongoDB schema-compliant format."
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Input CSV filename (looks in data/input/patient_demographic/)"
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Output CSV filename (saves to data/output/patient_demographic/)"
    )
    args = parser.parse_args()

    # Use shared paths
    input_path = Path(_settings.paths.data_input) / "patient_demographic" / args.input  # type: ignore
    output_path = Path(_settings.paths.data_output) / "patient_demographic" / args.output  # type: ignore

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logger.error(f"Input file {input_path} not found!")
    else:
        success = transform_csv_data(str(input_path), str(output_path))
        if success:
            logger.info(f"Transformation completed. Output saved to {output_path}")
        else:
            logger.error("Transformation failed!")
