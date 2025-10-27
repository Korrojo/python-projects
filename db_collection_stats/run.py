"""Main entry point for db_collection_stats."""

import sys
from pathlib import Path

# Add src/ to path so we can import project modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common_config.utils.logger import setup_logging, get_logger
from common_config.config.settings import get_settings


def main():
    """Main execution function."""
    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "db_collection_stats"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("db_collection_stats - Starting")
    logger.info("=" * 60)

    # TODO: Add your project logic here
    logger.info(f"Output dir: {settings.paths.data_output}/db_collection_stats/")

    logger.info("Completed successfully")


if __name__ == "__main__":
    main()
