import os

from automate_refresh.win.modules.exporter import export_sample
from common_config.config.settings import get_settings
from common_config.utils.logger import get_logger, setup_logging

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    # Load settings from environment
    settings = get_settings()
    uri = settings.mongodb_uri
    db = settings.database_name
    backup_dir = getattr(settings.paths, "backup", None) or os.getenv("BACKUP_DIR_PROD") or "./mongo_exports"

    # Export the full Users collection from prod
    collection = "Users"
    logger.info(f"Starting export for collection: {collection} from PROD")
    result = export_sample(
        uri=uri,
        database=db,
        collection_name=collection,
        fraction=1.0,  # Export all documents
        limit=None,
        out_dir=backup_dir,
    )
    logger.info(f"Exported {result.written} documents to {result.out_path}")
