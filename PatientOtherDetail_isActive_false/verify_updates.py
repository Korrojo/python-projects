from pathlib import Path
from typing import cast

import pandas as pd
from bson import ObjectId

from common_config.config.settings import get_settings
from common_config.db.connection import MongoDBConnection
from common_config.utils.exceptions import DatabaseError, DataProcessingError
from common_config.utils.logger import get_logger, get_run_timestamp, setup_logging


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
    project_name = "PatientOtherDetail_isActive_false"
    from pathlib import Path as _Path

    _proj_logs = _Path(settings.paths.logs) / project_name
    _proj_logs.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=_proj_logs)
    logger = get_logger(__name__)

    logger.info("=" * 80)
    logger.info("Compare PatientOtherDetail IsActive Before/After Updates")
    logger.info("=" * 80)

    # Get config from environment
    mongodb_uri = settings.mongodb_uri
    database_name = settings.database_name
    collection_before = getattr(settings, "collection_before", None) or "PatientOtherDetails_backup"
    collection_after = getattr(settings, "collection_after", None) or "PatientOtherDetails_copy"
    input_file_cfg = getattr(settings, "input_excel_file", None) or "patient_updates.xlsx"

    logger.info(f"Before collection: {collection_before}")
    logger.info(f"After collection: {collection_after}")

    if not mongodb_uri:
        logger.error("MONGODB_URI must be set in shared_config/.env (resolved by APP_ENV)")
        raise DataProcessingError("Missing MONGODB_URI in shared configuration")

    if not database_name:
        logger.error("DATABASE_NAME must be set in shared_config/.env (e.g., DATABASE_NAME_<ENV>)")
        raise DataProcessingError("Missing DATABASE_NAME in shared configuration")

    # Resolve input file path: prefer provided path; else shared data/input/<project>/<filename>
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
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}")
        raise DataProcessingError(f"Excel read error: {e}") from e

    # Validate required columns
    required_cols = ["Patientid", "_id"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        raise DataProcessingError(f"Excel missing columns: {missing}")

    logger.info("Found required columns: Patientid, _id")
    logger.info(f"Querying {len(df)} documents from MongoDB")

    # Select only the columns we need and rename
    df = df[["Patientid", "_id"]].copy()
    df.rename(columns={"Patientid": "PatientId"}, inplace=True)

    # Connect to MongoDB
    logger.info(f"Connecting to MongoDB: {database_name}")
    config_mgr = SimpleConfigManager(mongodb_uri, database_name)
    conn = MongoDBConnection(config_mgr)

    results = []

    try:
        conn.connect()
        test_result = conn.test_connection()
        if not test_result.get("connected"):
            raise DatabaseError(f"MongoDB connection test failed: {test_result.get('error')}")

        db = conn.get_database()
        coll_before = db[collection_before]
        coll_after = db[collection_after]

        for idx, row in df.iterrows():
            row_num = cast(int, idx) + 2  # Cast idx from Hashable to int for display purposes
            patient_id = row["PatientId"]
            admit_id_str = str(row["_id"])

            try:
                admit_oid = ObjectId(admit_id_str)
            except Exception as e:
                logger.warning(f"Row {row_num}: Invalid ObjectId '{admit_id_str}': {e}")
                results.append(
                    {
                        "PatientId": patient_id,
                        "_id": admit_id_str,
                        "IsActive_before": "ERROR: Invalid ObjectId",
                        "IsActive_after": "ERROR: Invalid ObjectId",
                    }
                )
                continue

            # Query to find the document and the specific admit
            query = {"PatientRef": patient_id, "Admits._id": admit_oid}

            # Project only the fields we need
            projection = {"PatientRef": 1, "Admits.$": 1}  # Only return the matched admit

            try:
                # Query BEFORE collection
                doc_before = coll_before.find_one(query, projection)
                is_active_before = "NOT_FOUND"
                if doc_before and "Admits" in doc_before and len(doc_before["Admits"]) > 0:
                    admit_before = doc_before["Admits"][0]
                    is_active_before = admit_before.get("IsActive", "NOT_SET")

                # Query AFTER collection
                doc_after = coll_after.find_one(query, projection)
                is_active_after = "NOT_FOUND"
                if doc_after and "Admits" in doc_after and len(doc_after["Admits"]) > 0:
                    admit_after = doc_after["Admits"][0]
                    is_active_after = admit_after.get("IsActive", "NOT_SET")

                results.append(
                    {
                        "PatientId": patient_id,
                        "_id": admit_id_str,
                        "IsActive_before": is_active_before,
                        "IsActive_after": is_active_after,
                    }
                )

                processed_count = cast(int, idx) + 1  # Cast from Hashable to int for progress counter
                if processed_count % 100 == 0:
                    logger.info(f"Queried {processed_count}/{len(df)} rows (READ-ONLY, no updates)...")

            except Exception as e:
                logger.error(f"Row {row_num}: Query failed for PatientRef={patient_id}, Admits._id={admit_id_str}: {e}")
                results.append(
                    {
                        "PatientId": patient_id,
                        "_id": admit_id_str,
                        "IsActive_before": f"ERROR: {str(e)}",
                        "IsActive_after": f"ERROR: {str(e)}",
                    }
                )

        logger.info(f"Queried {len(results)} documents")

        # Create output dataframe
        output_df = pd.DataFrame(results)

        # Create output directory under shared data_output/<project>
        output_dir = Path(settings.paths.data_output) / project_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename with timestamp
        timestamp = get_run_timestamp()
        output_file = output_dir / f"{timestamp}_isactive_verification.csv"

        # Save to CSV
        output_df.to_csv(output_file, index=False)
        logger.info(f"Saved results to: {output_file}")

        # Summary statistics
        before_true = len(output_df[output_df["IsActive_before"] == True])
        before_false = len(output_df[output_df["IsActive_before"] == False])
        after_true = len(output_df[output_df["IsActive_after"] == True])
        after_false = len(output_df[output_df["IsActive_after"] == False])

        # Count changes
        changed = len(output_df[output_df["IsActive_before"] != output_df["IsActive_after"]])
        unchanged = len(output_df[output_df["IsActive_before"] == output_df["IsActive_after"]])

        logger.info("=" * 80)
        logger.info("Comparison Summary:")
        logger.info("  BEFORE:")
        logger.info(f"    - IsActive = True: {before_true}")
        logger.info(f"    - IsActive = False: {before_false}")
        logger.info("  AFTER:")
        logger.info(f"    - IsActive = True: {after_true}")
        logger.info(f"    - IsActive = False: {after_false}")
        logger.info("  CHANGES:")
        logger.info(f"    - Changed: {changed}")
        logger.info(f"    - Unchanged: {unchanged}")
        logger.info(f"  Total records: {len(output_df)}")
        logger.info("=" * 80)

    finally:
        conn.disconnect()
        logger.info("MongoDB connection closed")


if __name__ == "__main__":
    main()
