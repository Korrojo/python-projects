#!/usr/bin/env python3
"""
SAFE READ-ONLY VALIDATION SCRIPT - TWO ENVIRONMENTS
Compares BEFORE (e.g., UbiquityProduction.Patients) vs AFTER (e.g., UbiquityTRAINING.Patients)
NO UPDATES - ONLY READS AND COMPARES

Unified config only: this script reads both environments from shared_config/.env using
their suffixed keys (e.g., MONGODB_URI_PROD, DATABASE_NAME_TRNG). No per-project env files.
"""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from bson import json_util
from pymongo import MongoClient

from common_config.config import get_settings  # type: ignore
from common_config.utils.logger import setup_logging

# Configure logging under shared logs/patient_demographic
_settings = get_settings()  # loads shared .env and ensures base dirs
_log_dir = Path(_settings.paths.logs) / "patient_demographic"  # type: ignore
_log_dir.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"{timestamp}_validation_prod_vs_training.log"
log_path = str(_log_dir / log_filename)
setup_logging(log_dir=_log_dir, level=_settings.log_level)  # type: ignore


def _get_uri_and_db_from_env(suffix: str) -> tuple[str, str]:
    """Read MONGODB_URI_<SUFFIX> and DATABASE_NAME_<SUFFIX> from environment loaded by common_config."""
    key_uri = f"MONGODB_URI_{suffix.upper()}"
    key_db = f"DATABASE_NAME_{suffix.upper()}"
    uri = os.environ.get(key_uri, "").strip()
    db = os.environ.get(key_db, "").strip()
    if not uri or not db:
        raise RuntimeError(f"Missing {key_uri} or {key_db} in shared configuration")
    return uri, db


def get_mongodb_client_for_suffix(env_suffix: str):
    """Connect to MongoDB using suffixed keys loaded from shared_config/.env."""
    try:
        uri, _ = _get_uri_and_db_from_env(env_suffix)
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        logging.info(f"Connected to MongoDB for suffix {env_suffix}")
        return client
    except Exception as e:
        logging.error(f"MongoDB connection failed for {env_suffix}: {e}", exc_info=True)
        return None


def get_aggregated_doc(collection, patient_id):
    """
    READ-ONLY: Get a document using aggregation pipeline.
    Extracts only the fields that were updated.
    """
    try:
        pipeline = [
            {"$match": {"PatientId": patient_id}},
            {
                "$project": {
                    "_id": 1,
                    "AthenaPatientId": 1,
                    "PatientId": 1,
                    "FirstName": 1,
                    "LastName": 1,
                    "FirstNameLower": 1,
                    "LastNameLower": 1,
                    "Dob": 1,
                    "Gender": 1,
                    "Email": 1,
                    "patient_demographic_updated": 1,
                    "homeAddress": {
                        "$filter": {
                            "input": "$Address",
                            "as": "addr",
                            "cond": {"$eq": ["$$addr.AddressTypeValue", "Home"]},
                        }
                    },
                    "homePhone": {
                        "$filter": {
                            "input": "$Phones",
                            "as": "phone",
                            "cond": {"$eq": ["$$phone.PhoneType", "Home"]},
                        }
                    },
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "AthenaPatientId": 1,
                    "PatientId": 1,
                    "FirstName": 1,
                    "LastName": 1,
                    "FirstNameLower": 1,
                    "LastNameLower": 1,
                    "Dob": 1,
                    "Gender": 1,
                    "Email": 1,
                    "patient_demographic_updated": 1,
                    "Address": {
                        "AddressTypeValue": {"$arrayElemAt": ["$homeAddress.AddressTypeValue", 0]},
                        "Street1": {"$arrayElemAt": ["$homeAddress.Street1", 0]},
                        "Street2": {"$arrayElemAt": ["$homeAddress.Street2", 0]},
                        "City": {"$arrayElemAt": ["$homeAddress.City", 0]},
                        "StateCode": {"$arrayElemAt": ["$homeAddress.StateCode", 0]},
                        "Zip5": {"$arrayElemAt": ["$homeAddress.Zip5", 0]},
                        "IsActive": {"$arrayElemAt": ["$homeAddress.IsActive", 0]},
                        "CreatedOn": {"$arrayElemAt": ["$homeAddress.CreatedOn", 0]},
                        "UpdatedOn": {"$arrayElemAt": ["$homeAddress.UpdatedOn", 0]},
                    },
                    "Phones": {
                        "PhoneType": {"$arrayElemAt": ["$homePhone.PhoneType", 0]},
                        "PhoneNumber": {"$arrayElemAt": ["$homePhone.PhoneNumber", 0]},
                        "IsActive": {"$arrayElemAt": ["$homePhone.IsActive", 0]},
                        "CreatedOn": {"$arrayElemAt": ["$homePhone.CreatedOn", 0]},
                        "UpdatedOn": {"$arrayElemAt": ["$homePhone.UpdatedOn", 0]},
                    },
                }
            },
        ]
        result = list(collection.aggregate(pipeline))
        return result[0] if result else None
    except Exception as e:
        logging.error(f"Error in aggregation for PatientId {patient_id}: {e}")
        return None


def get_csv_patient_ids(csv_path):
    """READ-ONLY: Get all PatientIds from the transformed CSV."""
    try:
        patient_ids = []
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("PatientId")
                if pid:
                    try:
                        patient_ids.append(int(pid))
                    except ValueError:
                        pass
        logging.info(f"Found {len(patient_ids)} PatientIds in CSV")
        return patient_ids
    except Exception as e:
        logging.error(f"Error reading CSV: {e}")
        return []


def sample_patient_ids_from_csv(csv_patient_ids, sample_size=10):
    """Sample PatientIds from CSV."""
    import random

    if len(csv_patient_ids) <= sample_size:
        return csv_patient_ids
    return random.sample(csv_patient_ids, sample_size)


def validate_prod_vs_training(csv_path):
    """
    SAFE READ-ONLY VALIDATION - TWO ENVIRONMENTS
    Compares BEFORE (UbiquityProduction.Patients via env.prod)
         vs AFTER (UbiquityTRAINING.Patients via env.trng)
    NO UPDATES - ONLY READS AND COMPARES
    """

    logging.info(f"\n{'=' * 80}")
    logging.info("SAFE READ-ONLY VALIDATION - TWO ENVIRONMENTS")
    logging.info(f"{'=' * 80}")
    logging.info("⚠️  NO UPDATES WILL BE PERFORMED - READ-ONLY MODE")
    logging.info(f"{'=' * 80}\n")

    # Load both environments from shared .env (already loaded by get_settings())
    logging.info("Connecting to BEFORE (e.g., PROD) and AFTER (e.g., TRNG) environments...")
    before_suffix = os.environ.get("VALIDATE_BEFORE_SUFFIX", "PROD")
    after_suffix = os.environ.get("VALIDATE_AFTER_SUFFIX", "TRNG")

    before_client = get_mongodb_client_for_suffix(before_suffix)
    if not before_client:
        logging.error("Failed to connect to BEFORE environment. Exiting.")
        return False
    after_client = get_mongodb_client_for_suffix(after_suffix)
    if not after_client:
        logging.error("Failed to connect to AFTER environment. Exiting.")
        before_client.close()
        return False

    try:
        # BEFORE collection
        _, before_db_name = _get_uri_and_db_from_env(before_suffix)
        before_coll_name = os.environ.get(f"COLLECTION_NAME_{before_suffix.upper()}", "Patients")
        before_collection = before_client[before_db_name][before_coll_name]

        # AFTER collection
        _, after_db_name = _get_uri_and_db_from_env(after_suffix)
        after_coll_name = os.environ.get(f"COLLECTION_NAME_{after_suffix.upper()}", "Patients")
        after_collection = after_client[after_db_name][after_coll_name]

        logging.info(f"\n{'=' * 80}")
        logging.info("CONFIGURATION")
        logging.info(f"{'=' * 80}")
        logging.info(f"BEFORE Collection: {before_db_name}.{before_coll_name}")
        logging.info(f"  Environment suffix: {before_suffix}")
        logging.info(f"\nAFTER Collection: {after_db_name}.{after_coll_name}")
        logging.info(f"  Environment suffix: {after_suffix}")
        logging.info(f"\nCSV File: {csv_path}")
        logging.info(f"{'=' * 80}\n")

        # Step 1: Get PatientIds from CSV
        csv_patient_ids = get_csv_patient_ids(csv_path)
        if not csv_patient_ids:
            logging.error("No PatientIds found in CSV. Exiting.")
            return False

        # Step 2: Sample 10 PatientIds from CSV
        sample_patient_ids = sample_patient_ids_from_csv(csv_patient_ids, sample_size=10)
        logging.info(f"Sample PatientIds for validation: {sample_patient_ids}\n")

        # Step 3: Validate each patient
        validation_summary = {
            "total_validated": 0,
            "changes_detected": 0,
            "no_changes": 0,
            "before_not_found": 0,
            "after_not_found": 0,
            "patient_details": [],
        }

        for patient_id in sample_patient_ids:
            logging.info(f"\n{'=' * 80}")
            logging.info(f"VALIDATING PATIENT ID: {patient_id}")
            logging.info(f"{'=' * 80}")

            # Get BEFORE document (READ-ONLY from Production)
            before_doc = get_aggregated_doc(before_collection, patient_id)
            if not before_doc:
                logging.warning(f"PatientId {patient_id} not found in BEFORE collection (Production)")
                validation_summary["before_not_found"] += 1
                continue

            # Get AFTER document (READ-ONLY from Training)
            after_doc = get_aggregated_doc(after_collection, patient_id)
            if not after_doc:
                logging.warning(f"PatientId {patient_id} not found in AFTER collection (Training)")
                validation_summary["after_not_found"] += 1
                continue

            validation_summary["total_validated"] += 1

            # Log BEFORE document
            logging.info(f"\n--- BEFORE DOCUMENT (Production: {before_db_name}.{before_coll_name}) ---")
            logging.info(json.dumps(before_doc, indent=2, default=json_util.default))

            # Log AFTER document
            logging.info(f"\n--- AFTER DOCUMENT (Training: {after_db_name}.{after_coll_name}) ---")
            logging.info(json.dumps(after_doc, indent=2, default=json_util.default))

            # Compare fields
            logging.info("\n--- FIELD COMPARISON ---")
            changes_detected = False
            changed_fields = []

            # Top-level fields
            top_fields = [
                "AthenaPatientId",
                "FirstName",
                "LastName",
                "FirstNameLower",
                "LastNameLower",
                "Dob",
                "Gender",
                "Email",
            ]
            for field in top_fields:
                before_val = before_doc.get(field)
                after_val = after_doc.get(field)
                if before_val != after_val:
                    logging.info(f"CHANGED - {field}: '{before_val}' → '{after_val}'")
                    changes_detected = True
                    changed_fields.append(field)
                else:
                    logging.info(f"SAME - {field}: '{before_val}'")

            # Address fields
            before_addr = before_doc.get("Address", {})
            after_addr = after_doc.get("Address", {})
            addr_fields = ["Street1", "Street2", "City", "StateCode", "Zip5"]
            for field in addr_fields:
                before_val = before_addr.get(field) if isinstance(before_addr, dict) else None
                after_val = after_addr.get(field) if isinstance(after_addr, dict) else None
                if before_val != after_val:
                    logging.info(f"CHANGED - Address.{field}: '{before_val}' → '{after_val}'")
                    changes_detected = True
                    changed_fields.append(f"Address.{field}")
                else:
                    logging.info(f"SAME - Address.{field}: '{before_val}'")

            # Phone fields
            before_phone = before_doc.get("Phones", {})
            after_phone = after_doc.get("Phones", {})
            before_phone_num = before_phone.get("PhoneNumber") if isinstance(before_phone, dict) else None
            after_phone_num = after_phone.get("PhoneNumber") if isinstance(after_phone, dict) else None
            if before_phone_num != after_phone_num:
                logging.info(f"CHANGED - Phone.PhoneNumber: '{before_phone_num}' → '{after_phone_num}'")
                changes_detected = True
                changed_fields.append("Phone.PhoneNumber")
            else:
                logging.info(f"SAME - Phone.PhoneNumber: '{before_phone_num}'")

            # Check metadata in AFTER document
            logging.info("\n--- METADATA VALIDATION (AFTER - Training) ---")
            after_addr_updated_on = after_addr.get("UpdatedOn") if isinstance(after_addr, dict) else None
            after_phone_updated_on = after_phone.get("UpdatedOn") if isinstance(after_phone, dict) else None
            patient_demographic_updated = after_doc.get("patient_demographic_updated")

            metadata_valid = True
            if after_addr_updated_on:
                logging.info(f"✓ Address.UpdatedOn present: {after_addr_updated_on}")
            else:
                logging.warning("✗ Address.UpdatedOn missing")
                metadata_valid = False

            if after_phone_updated_on:
                logging.info(f"✓ Phone.UpdatedOn present: {after_phone_updated_on}")
            else:
                logging.warning("✗ Phone.UpdatedOn missing")
                metadata_valid = False

            if patient_demographic_updated:
                logging.info(f"✓ patient_demographic_updated flag: {patient_demographic_updated}")
            else:
                logging.warning("✗ patient_demographic_updated flag missing or False")
                metadata_valid = False

            # Summary for this patient
            patient_result = {
                "patient_id": patient_id,
                "changes_detected": changes_detected,
                "changed_fields": changed_fields,
                "metadata_valid": metadata_valid,
            }
            validation_summary["patient_details"].append(patient_result)

            if changes_detected:
                logging.info(f"\n✓ VALIDATION PASSED: Changes detected for PatientId {patient_id}")
                logging.info(f"  Changed fields: {', '.join(changed_fields)}")
                validation_summary["changes_detected"] += 1
            else:
                logging.warning(f"\n⚠ VALIDATION WARNING: No changes detected for PatientId {patient_id}")
                validation_summary["no_changes"] += 1

        # Final summary
        logging.info(f"\n{'=' * 80}")
        logging.info("FINAL VALIDATION SUMMARY")
        logging.info(f"{'=' * 80}")
        logging.info(f"Total Sampled: {len(sample_patient_ids)}")
        logging.info(f"Total Validated: {validation_summary['total_validated']}")
        logging.info(f"Changes Detected: {validation_summary['changes_detected']}")
        logging.info(f"No Changes: {validation_summary['no_changes']}")
        logging.info(f"Not Found in BEFORE (Production): {validation_summary['before_not_found']}")
        logging.info(f"Not Found in AFTER (Training): {validation_summary['after_not_found']}")

        if validation_summary["total_validated"] > 0:
            success_rate = (validation_summary["changes_detected"] / validation_summary["total_validated"]) * 100
            logging.info(f"Success Rate: {success_rate:.1f}%")

        logging.info("\n--- PATIENT-BY-PATIENT SUMMARY ---")
        for detail in validation_summary["patient_details"]:
            status = "✓ PASS" if detail["changes_detected"] else "⚠ NO CHANGES"
            logging.info(f"PatientId {detail['patient_id']}: {status}")
            if detail["changed_fields"]:
                logging.info(f"  Changed: {', '.join(detail['changed_fields'])}")

        logging.info(f"{'=' * 80}\n")
        logging.info("⚠️  REMINDER: This was a READ-ONLY validation. No updates were performed.")
        logging.info(f"⚠️  BEFORE: {before_db_name}")
        logging.info(f"⚠️  AFTER: {after_db_name}")
        logging.info(f"{'=' * 80}\n")

        return True

    except Exception as e:
        logging.error(f"Validation failed: {e}", exc_info=True)
        return False
    finally:
        before_client.close()
        after_client.close()
        logging.info("All MongoDB connections closed.")


if __name__ == "__main__":
    print("=" * 80)
    print("SAFE READ-ONLY VALIDATION SCRIPT - TWO ENVIRONMENTS")
    print("=" * 80)
    print("⚠️  NO UPDATES WILL BE PERFORMED")
    print("This script only READS and COMPARES data")
    print("BEFORE/AFTER are resolved from shared_config/.env using suffixes (default: PROD/TRNG)")
    print("=" * 80)

    logging.info("Starting safe read-only validation (Production vs Training)...")

    # Path to transformed CSV
    # Path to transformed CSV (will be used as-is)
    csv_path = "data/output/patient_demographic/Patient Demographics_3320202_20251002_10-01_transformed.csv"

    # Run validation
    validate_prod_vs_training(csv_path)

    print(f"\n✓ Validation complete! Check log file: {log_path}")
