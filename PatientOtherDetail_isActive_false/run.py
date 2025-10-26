from pathlib import Path
from typing import cast

import pandas as pd
from bson import ObjectId

from common_config.config.settings import get_settings
from common_config.db.connection import MongoDBConnection
from common_config.utils.exceptions import DatabaseError, DataProcessingError
from common_config.utils.logger import get_logger, setup_logging


class SimpleConfigManager:
    """Simple config wrapper for MongoDBConnection."""

    def __init__(self, uri: str, database: str):
        self._uri = uri
        self._database = database

    def get_mongodb_uri(self) -> str:
        return self._uri

    def get_mongodb_database(self) -> str:
        return self._database


def main():
    settings = get_settings()
    # Use project-specific logs subfolder under shared logs path
    from pathlib import Path as _Path

    project_name = "PatientOtherDetail_isActive_false"
    _proj_logs = _Path(settings.paths.logs) / project_name
    _proj_logs.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=_proj_logs)
    logger = get_logger(__name__)

    logger.info("=" * 80)
    logger.info("Starting PatientOtherDetail IsActive Update Process")
    logger.info("=" * 80)

    # Get config from shared environment
    # MONGODB_URI comes from shared .env (automatically loaded via common_config)
    mongodb_uri = settings.mongodb_uri
    # DATABASE_NAME comes from shared configuration
    database_name = settings.database_name
    # Optional, allow project-specific overrides if provided in shared .env
    collection_name = getattr(settings, "collection_name", None) or "PatientOtherDetails_copy"
    input_file_cfg = getattr(settings, "input_excel_file", None) or "patient_updates.xlsx"

    if not mongodb_uri:
        logger.error("MONGODB_URI must be set in shared_config/.env (resolved by APP_ENV)")
        raise DataProcessingError("Missing MONGODB_URI in shared configuration")

    if not database_name:
        logger.error("DATABASE_NAME must be set in shared_config/.env (e.g., DATABASE_NAME_<ENV>)")
        raise DataProcessingError("Missing DATABASE_NAME in shared configuration")

    # Resolve input file path: prefer absolute/relative provided path; else shared data/input/<project>/<filename>
    input_path = Path(input_file_cfg)
    if not input_path.exists():
        try:
            cand = Path(settings.paths.data_input) / project_name / input_path.name
            cand.parent.mkdir(parents=True, exist_ok=True)
            if cand.exists():
                input_path = cand
        except Exception:
            pass
    if not input_path.exists():
        logger.error(f"Input Excel file not found: {input_path}")
        raise DataProcessingError(f"Input file not found: {input_path}")

    logger.info(f"Reading Excel file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        logger.info(f"Loaded {len(df)} rows from Excel")
        logger.info(f"Total columns: {len(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        raise DataProcessingError(f"Excel read error: {e}") from e

    # Validate required columns (Patientid and _id)
    required_cols = ["Patientid", "_id"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        logger.error(f"Available columns: {list(df.columns)}")
        raise DataProcessingError(f"Excel missing columns: {missing}")

    logger.info("Found required columns: Patientid, _id")

    # Log total rows to process
    total_rows = len(df)
    logger.info(f"Processing {total_rows} rows from Excel")

    # Select only the columns we need and rename for consistency
    df = df[["Patientid", "_id"]].copy()
    df.rename(columns={"Patientid": "PatientId"}, inplace=True)
    logger.info(f"Sample data (first 3 rows):\n{df.head(3).to_string()}")

    # Connect to MongoDB
    logger.info(f"Connecting to MongoDB: {database_name}.{collection_name}")
    config_mgr = SimpleConfigManager(mongodb_uri, database_name)
    conn = MongoDBConnection(config_mgr)

    try:
        conn.connect()
        test_result = conn.test_connection()
        if not test_result.get("connected"):
            raise DatabaseError(f"MongoDB connection test failed: {test_result.get('error')}")

        db = conn.get_database()
        collection = db[collection_name]

        success_count = 0
        error_count = 0
        not_found_count = 0

        for idx, row in df.iterrows():
            row_num = cast(int, idx) + 2  # Cast idx from Hashable to int for display purposes
            patient_id = row["PatientId"]
            admit_id_str = str(row["_id"])

            try:
                admit_oid = ObjectId(admit_id_str)
            except Exception as e:
                logger.warning(f"Row {row_num}: Invalid ObjectId '{admit_id_str}': {e}")
                error_count += 1
                continue

            # Query: match PatientRef at root and Admits._id in array
            query = {"PatientRef": patient_id, "Admits._id": admit_oid}

            # Update: set Admits.$.IsActive = false
            update = {"$set": {"Admits.$.IsActive": False}}

            try:
                result = collection.update_one(query, update)

                if result.matched_count > 0:
                    logger.info(
                        f"Row {row_num}: Updated PatientRef={patient_id}, Admits._id={admit_id_str} "
                        f"(modified={result.modified_count})"
                    )
                    success_count += 1
                else:
                    logger.warning(
                        f"Row {row_num}: No match found for PatientRef={patient_id}, Admits._id={admit_id_str}"
                    )
                    not_found_count += 1

            except Exception as e:
                logger.error(
                    f"Row {row_num}: Update failed for PatientRef={patient_id}, Admits._id={admit_id_str}: {e}"
                )
                error_count += 1

        logger.info("=" * 80)
        logger.info("Process completed:")
        logger.info(f"  - Successfully updated: {success_count}")
        logger.info(f"  - Not found: {not_found_count}")
        logger.info(f"  - Errors: {error_count}")
        logger.info("=" * 80)

    finally:
        conn.disconnect()
        logger.info("MongoDB connection closed")


if __name__ == "__main__":
    main()
