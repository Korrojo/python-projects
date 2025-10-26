import csv
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from bson import json_util
from bson.objectid import ObjectId
from dateutil import parser as date_parser
from pymongo import MongoClient

from common_config.config import get_settings  # type: ignore
from common_config.utils.logger import setup_logging  # type: ignore

# Configure logging under shared logs/<project>
_settings = get_settings()  # type: ignore
_proj_logs = Path(_settings.paths.logs) / "patient_demographic"  # type: ignore
_proj_logs.mkdir(parents=True, exist_ok=True)
setup_logging(log_dir=_proj_logs, level=_settings.log_level)  # type: ignore
logging.getLogger(__name__).info("Using shared logs directory for patient_demographic")

# Suppress verbose PyMongo logging
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_mongodb_client():
    """Connect to MongoDB using unified settings only."""
    try:
        settings = _settings if "_settings" in globals() else get_settings()  # type: ignore
        uri = settings.mongodb_uri  # type: ignore[attr-defined]
        if not uri:
            raise ValueError("Unified settings missing mongodb_uri")
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
        logging.info("Successfully connected to MongoDB")
        return client, {
            "MONGO_SOURCE_DB": getattr(settings, "database_name", None) or "Ubiquity",
            "MONGO_SOURCE_COLL": getattr(settings, "collection_name", None) or None,
        }
    except Exception as e:
        logging.error(f"MongoDB connection failed: {e}", exc_info=True)
        return None, None


def parse_date_from_source(date_value):
    """Parse a date value (could be string or already datetime) into a datetime object."""
    if not date_value:
        return None
    if isinstance(date_value, datetime):
        return date_value
    try:
        return date_parser.parse(str(date_value))
    except (ValueError, TypeError):
        logging.warning(f"Could not parse date: {date_value}. Returning None.")
        return None


def get_aggregated_doc(collection, patient_id):
    """Get a document using the aggregation pipeline for consistent before/after views."""
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
                    },
                    "Phones": {
                        "PhoneType": {"$arrayElemAt": ["$homePhone.PhoneType", 0]},
                        "PhoneNumber": {"$arrayElemAt": ["$homePhone.PhoneNumber", 0]},
                    },
                }
            },
        ]
        result = list(collection.aggregate(pipeline))
        return result[0] if result else None
    except Exception as e:
        logging.error(f"Aggregation failed: {e}")
        return None


def process_patient_from_csv(row, collection, show_details=False):
    """Process a single patient record from CSV following archival update patterns."""
    try:
        patient_id_int = int(row.get("PatientId", 0))
    except (ValueError, TypeError):
        logging.warning(f"Skipping row with invalid PatientId: {row.get('PatientId')}")
        return False

    # Find target document
    target_doc = collection.find_one({"PatientId": patient_id_int})
    if not target_doc:
        logging.warning(f"PatientId {patient_id_int} not found in target collection. Skipping.")
        return False

    if show_details:
        before_doc = get_aggregated_doc(collection, patient_id_int)
        print("\n--- DOCUMENT BEFORE UPDATE ---")
        print(
            json.dumps(before_doc, indent=4, default=json_util.default)
            if before_doc
            else f"No aggregated document found for PatientId {patient_id_int}."
        )

    update_set_payload = {}
    current_time = datetime.now(UTC)

    # --- Top-Level Fields (following archival pattern) ---
    top_level_fields = [
        "AthenaPatientId",
        "FirstName",
        "LastName",
        "Dob",
        "Gender",
        "Email",
    ]
    for field in top_level_fields:
        csv_val = row.get(field)
        target_val = target_doc.get(field)

        # If CSV value is empty, skip updating this field
        if csv_val is None or str(csv_val).strip() == "":
            continue

        # Handle AthenaPatientId - convert to int and add if missing
        if field == "AthenaPatientId":
            csv_val = int(csv_val)
            if "AthenaPatientId" not in target_doc:
                update_set_payload["AthenaPatientId"] = csv_val
                if show_details:
                    logging.info(f"PatientId {patient_id_int}: Adding missing AthenaPatientId.")
                continue

        # Handle Dob - parse to datetime
        if field == "Dob":
            parsed_date = parse_date_from_source(csv_val)
            if parsed_date and parsed_date != target_val:
                update_set_payload[field] = parsed_date
                if show_details:
                    logging.info(f"PatientId {patient_id_int}: Updating {field}.")
            continue

        # Handle other fields
        if str(target_val) != str(csv_val):
            update_set_payload[field] = csv_val
            if show_details:
                logging.info(f"PatientId {patient_id_int}: Updating {field}.")

    # --- Lowercase Name Fields Sync (following archival pattern) ---
    final_first_name = update_set_payload.get("FirstName", target_doc.get("FirstName"))
    final_last_name = update_set_payload.get("LastName", target_doc.get("LastName"))

    if final_first_name and final_first_name.lower() != target_doc.get("FirstNameLower"):
        update_set_payload["FirstNameLower"] = final_first_name.lower()
        if show_details:
            logging.info(f"PatientId {patient_id_int}: Correcting FirstNameLower.")

    if final_last_name and final_last_name.lower() != target_doc.get("LastNameLower"):
        update_set_payload["LastNameLower"] = final_last_name.lower()
        if show_details:
            logging.info(f"PatientId {patient_id_int}: Correcting LastNameLower.")

    # --- Handle Address Array (following archival pattern) ---
    update_push_payload = {}
    csv_address_fields = {
        "Street1": row.get("Street1"),
        "Street2": row.get("Street2"),
        "City": row.get("City"),
        "StateCode": row.get("StateCode"),
        "Zip5": row.get("Zip5"),
    }
    # Remove any address fields that are empty in CSV
    csv_address_fields = {k: v for k, v in csv_address_fields.items() if v is not None and str(v).strip() != ""}

    if csv_address_fields:
        target_addresses = target_doc.get("Address", [])
        if not isinstance(target_addresses, list):
            target_addresses = []

        home_address_idx = next(
            (
                i
                for i, addr in enumerate(target_addresses)
                if isinstance(addr, dict) and addr.get("AddressTypeValue") == "Home"
            ),
            -1,
        )

        address_field_mappings = {
            "Street1": "Street1",
            "Street2": "Street2",
            "City": "City",
            "StateCode": "StateCode",
            "Zip5": "Zip5",
        }

        if home_address_idx != -1:  # Update existing Home address
            prefix = f"Address.{home_address_idx}."
            address_updated = False
            for src_key, target_key in address_field_mappings.items():
                if src_key in csv_address_fields:
                    csv_addr_val = csv_address_fields[src_key]
                    if csv_addr_val == "":
                        csv_addr_val = None
                    if target_key in ["Zip5", "StateCode"] and csv_addr_val is not None:
                        csv_addr_val = str(csv_addr_val)
                    if target_addresses[home_address_idx].get(target_key) != csv_addr_val:
                        update_set_payload[prefix + target_key] = csv_addr_val
                        address_updated = True
                        if show_details:
                            logging.info(
                                f"Updating Address.{target_key}: '{target_addresses[home_address_idx].get(target_key)}' → '{csv_addr_val}'"
                            )
            # Always update UpdatedOn and LastModifiedBy in Home address if present in CSV
            if address_updated or row.get("UpdatedOn") or row.get("LastModifiedBy"):
                if row.get("UpdatedOn") and str(row.get("UpdatedOn")).strip() != "":
                    update_set_payload[prefix + "UpdatedOn"] = parse_date_from_source(row.get("UpdatedOn"))
                    if show_details:
                        logging.info(f"Setting Address.UpdatedOn to: {parse_date_from_source(row.get('UpdatedOn'))}")
                if row.get("LastModifiedBy") and str(row.get("LastModifiedBy")).strip() != "":
                    update_set_payload[prefix + "LastModifiedBy"] = row.get("LastModifiedBy")
                    if show_details:
                        logging.info(f"Setting Address.LastModifiedBy to: {row.get('LastModifiedBy')}")
        else:  # Push new Home address (following archival pattern)
            new_home_addr = {
                "_id": ObjectId(),
                "AddressTypeValue": "Home",
                "IsActive": True,
                "CreatedOn": current_time,
                "UpdatedOn": current_time,
            }
            has_data_to_push = False
            for src_key, target_key in address_field_mappings.items():
                if src_key in csv_address_fields:
                    csv_addr_val = csv_address_fields[src_key]
                    if csv_addr_val == "":
                        csv_addr_val = None
                    if target_key in ["Zip5", "StateCode"] and csv_addr_val is not None:
                        csv_addr_val = str(csv_addr_val)
                    if csv_addr_val is not None:
                        new_home_addr[target_key] = csv_addr_val
                        has_data_to_push = True
                        if show_details:
                            logging.info(f"Adding Address.{target_key}: '{csv_addr_val}'")
            if has_data_to_push:
                update_push_payload["Address"] = new_home_addr
                if show_details:
                    logging.info(f"Preparing to $push new Home address with CreatedOn: {current_time}")

    # --- Handle Phones Array (following archival pattern) ---
    csv_phone_number = row.get("PhoneNumber")
    if csv_phone_number and str(csv_phone_number).strip():
        target_phones = target_doc.get("Phones", [])
        if not isinstance(target_phones, list):
            target_phones = []

        home_phone_idx = next(
            (i for i, p in enumerate(target_phones) if isinstance(p, dict) and p.get("PhoneType") == "Home"),
            -1,
        )

        if home_phone_idx != -1:  # Update existing Home phone
            phone_updated = False
            if str(target_phones[home_phone_idx].get("PhoneNumber")) != str(csv_phone_number):
                update_set_payload[f"Phones.{home_phone_idx}.PhoneNumber"] = csv_phone_number
                phone_updated = True
                if show_details:
                    logging.info(
                        f"Updating Phone.PhoneNumber: '{target_phones[home_phone_idx].get('PhoneNumber')}' → '{csv_phone_number}'"
                    )
            # Always update UpdatedOn and LastModifiedBy in Home phone if present in CSV
            if phone_updated or row.get("UpdatedOn") or row.get("LastModifiedBy"):
                if row.get("UpdatedOn") and str(row.get("UpdatedOn")).strip() != "":
                    update_set_payload[f"Phones.{home_phone_idx}.UpdatedOn"] = parse_date_from_source(
                        row.get("UpdatedOn")
                    )
                    if show_details:
                        logging.info(f"Setting Phone.UpdatedOn to: {parse_date_from_source(row.get('UpdatedOn'))}")
                if row.get("LastModifiedBy") and str(row.get("LastModifiedBy")).strip() != "":
                    update_set_payload[f"Phones.{home_phone_idx}.LastModifiedBy"] = row.get("LastModifiedBy")
                    if show_details:
                        logging.info(f"Setting Phone.LastModifiedBy to: {row.get('LastModifiedBy')}")
        else:  # Push new Home phone (following archival pattern)
            new_home_phone = {
                "_id": ObjectId(),
                "PhoneType": "Home",
                "PhoneNumber": csv_phone_number,
                "IsActive": True,
                "IsPrimary": False,
                "CreatedOn": current_time,
                "UpdatedOn": current_time,
            }
            update_push_payload["Phones"] = new_home_phone
            if show_details:
                logging.info(f"Preparing to $push new Home phone: '{csv_phone_number}' with CreatedOn: {current_time}")

    # --- Execute Updates (handle both $set and $push operations) ---
    if update_set_payload or update_push_payload:
        update_operation = {}

        # Always set LastModifiedBy to CSV_IMPORT_SCRIPT for every update
        update_set_payload["LastModifiedBy"] = "CSV_IMPORT_SCRIPT"
        update_set_payload["patient_demographic_updated"] = True
        if update_set_payload:
            update_operation["$set"] = update_set_payload

        if update_push_payload:
            update_operation["$push"] = update_push_payload

        result = collection.update_one({"PatientId": patient_id_int}, update_operation)
        if result.modified_count > 0:
            logging.info(f"Successfully updated PatientId: {patient_id_int}")
            if "$push" in update_operation and show_details:
                logging.info(f"$push operations executed: {list(update_push_payload.keys())}")

        if show_details:
            after_doc = get_aggregated_doc(collection, patient_id_int)
            print("\n--- DOCUMENT AFTER UPDATE ---")
            print(
                json.dumps(after_doc, indent=4, default=json_util.default)
                if after_doc
                else f"No aggregated document found for PatientId {patient_id_int}."
            )

        return True
    else:
        if show_details:
            logging.info(f"No update needed for PatientId {patient_id_int}. All fields match.")
        return False


def update_mongodb_from_csv(csv_path, patient_id=None):
    """Update MongoDB collection from transformed CSV file."""

    # Connect to MongoDB
    client, config = get_mongodb_client()
    if not client:
        logging.error("Failed to connect to MongoDB. Exiting.")
        return False

    try:
        # In unified mode, keys may be absent; provide sensible defaults
        db_name = (config.get("MONGO_SOURCE_DB") if isinstance(config, dict) else None) or "Ubiquity"
        collection_name = (
            config.get("MONGO_SOURCE_COLL") if isinstance(config, dict) else None
        ) or "AD_Patients_20250721"
        db = client[db_name]
        collection = db[collection_name]

        logging.info(f"Target collection: {db_name}.{collection_name}")

        # Read CSV file
        try:
            # If file missing, try shared data/input/patient_demographic
            _csv_path = Path(csv_path)
            if not _csv_path.exists():
                _in_base = Path(_settings.paths.data_input) / "patient_demographic"  # type: ignore
                _in_base.mkdir(parents=True, exist_ok=True)
                cand = _in_base / _csv_path.name
                if cand.exists():
                    _csv_path = cand

            with open(_csv_path, encoding="utf-8") as file:
                reader = csv.DictReader(file)
                rows = list(reader)
        except FileNotFoundError:
            logging.error(f"CSV file not found at: {csv_path}")
            return False
        except Exception as e:
            logging.error(f"Error reading CSV: {e}", exc_info=True)
            return False

        stats = {
            "total_rows_in_csv": len(rows),
            "processed_count": 0,
            "updated_count": 0,
            "not_found_count": 0,
            "error_count": 0,
        }

        logging.info(f"Processing {len(rows)} rows from CSV...")

        for row in rows:
            # If specific patient_id provided, only process that one
            if patient_id and int(row.get("PatientId", 0)) != patient_id:
                continue

            stats["processed_count"] += 1

            try:
                show_details = patient_id is not None  # Show details for single patient mode
                success = process_patient_from_csv(row, collection, show_details)
                if success:
                    stats["updated_count"] += 1

            except Exception as e:
                logging.error(
                    f"Error processing PatientId {row.get('PatientId')}: {e}",
                    exc_info=True,
                )
                stats["error_count"] += 1
                continue

        # Log final statistics
        logging.info("--- Update Process Summary ---")
        logging.info(f"Total rows in CSV: {stats['total_rows_in_csv']}")
        logging.info(f"Rows processed: {stats['processed_count']}")
        logging.info(f"Documents updated: {stats['updated_count']}")
        logging.info(f"Errors encountered: {stats['error_count']}")

        return True

    finally:
        client.close()
        logging.info("MongoDB connection closed.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update MongoDB from transformed CSV")
    parser.add_argument("--csv", default="test_patient_data_transformed.csv", help="CSV file path")
    parser.add_argument("--patient_id", type=int, help="Specific patient ID to update")
    args = parser.parse_args()

    logging.info("Starting MongoDB update process from CSV...")
    logging.info(f"Using CSV file: {args.csv}")
    if args.patient_id:
        logging.info(f"Running in single-patient mode for PatientId: {args.patient_id}")
    else:
        logging.info("Running in batch mode for all patients in the CSV.")

    success = update_mongodb_from_csv(args.csv, args.patient_id)
    if success:
        logging.info("Update process completed successfully!")
    else:
        logging.error("Update process failed!")
