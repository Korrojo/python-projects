#!/usr/bin/env python3
"""
MongoDB Database Service
Handles all MongoDB operations including connection, backup, and updates.

Unified settings only:
- Uses `common_config` (shared_config/.env + APP_ENV) for all configuration
- Project-local dotenv files and legacy flags are no longer supported
"""

import logging
from pathlib import Path

from pymongo import MongoClient

# Unified configuration
from common_config.config import get_settings  # type: ignore
from common_config.utils.logger import get_logger, setup_logging  # type: ignore


class DatabaseService:
    """MongoDB database service for Users collection updates using unified config only."""

    def __init__(self):
        self.client = None
        self.db = None
        # Load unified settings and initialize shared logging
        self._settings = get_settings()  # type: ignore
        proj_logs = Path(self._settings.paths.logs) / "users-provider-update"  # type: ignore
        proj_logs.mkdir(parents=True, exist_ok=True)
        setup_logging(log_dir=proj_logs, level=self._settings.log_level)  # type: ignore
        self._logger = get_logger(__name__)
        # Collections (allow override via shared config if provided)
        self.source_coll_name = getattr(self._settings, "collection_before", None) or "Users"
        self.dest_coll_name = getattr(self._settings, "collection_after", None) or "AD_Users_20250910"

    def connect(self):
        """Connect to MongoDB using environment credentials."""
        try:
            uri = self._settings.mongodb_uri
            db_name = self._settings.database_name
            if not uri or not db_name:
                raise ValueError("Unified settings missing mongodb_uri or database_name")
            self.client = MongoClient(uri, serverSelectionTimeoutMS=10000)
            self.client.admin.command("ping")
            self.db = self.client[db_name]
            logging.info("Successfully connected to MongoDB")
            logging.info(f"[DEBUG] Database: {db_name}")
            logging.info(f"[DEBUG] Source Collection: {self.source_coll_name}")
            logging.info(f"[DEBUG] Destination Collection: {self.dest_coll_name}")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    def create_backup(self):
        """
        Create backup collection by copying source to destination.
        If backup already exists, skip creation.
        """
        if self.db is None:
            raise RuntimeError("Database connection not established. Call connect() first.")

        try:
            source_collection = self.db[self.source_coll_name]
            dest_collection = self.db[self.dest_coll_name]

            # Check if destination collection already exists
            backup_count = dest_collection.count_documents({})

            if backup_count > 0:
                logging.info(
                    f"✅ Destination collection '{self.dest_coll_name}' already exists with {backup_count} documents"
                )

                # Check for indexes
                indexes = list(dest_collection.list_indexes())
                index_names = [idx["name"] for idx in indexes if idx["name"] != "_id_"]

                if index_names:
                    logging.info(f"📋 Destination collection has {len(index_names)} indexes")
                    logging.info("🚀 Using existing destination collection - optimal performance maintained")
                else:
                    logging.warning("⚠️  WARNING: Destination collection exists but has no custom indexes")
                    logging.info("💡 Performance may be impacted. Consider creating indexes.")

                return

            # Create backup if it doesn't exist
            logging.info(f"⚠️  Destination collection '{self.dest_coll_name}' not found")
            logging.info("🔄 Creating backup (data only, no indexes)...")

            documents = list(source_collection.find({}))

            if documents:
                dest_collection.insert_many(documents)
                logging.info(
                    f"✅ Created destination collection '{self.dest_coll_name}' with {len(documents)} documents"
                )
                logging.warning("⚠️  Note: This backup does not include indexes")
            else:
                logging.error(f"❌ Source collection '{self.source_coll_name}' is empty")
                raise ValueError("Source collection is empty - cannot create backup")

        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            raise

    def find_users(self, first_name, last_name):
        """
        Find active users by first and last name (case-insensitive).

        Args:
            first_name (str): First name to match
            last_name (str): Last name to match

        Returns:
            list: List of matching user documents
        """
        if self.db is None:
            raise RuntimeError("Database connection not established. Call connect() first.")

        try:
            collection = self.db[self.dest_coll_name]

            # Case-insensitive regex matching for both names
            users = list(
                collection.find(
                    {
                        "FirstName": {"$regex": f"^{first_name}$", "$options": "i"},
                        "LastName": {"$regex": f"^{last_name}$", "$options": "i"},
                        "IsActive": True,
                    }
                )
            )

            return users

        except Exception as e:
            logging.error(f"Error finding users for {first_name} {last_name}: {e}")
            raise

    def update_user(self, user_id, update_doc):
        """
        Update user with provider information.

        Args:
            user_id: MongoDB ObjectId of user to update
            update_doc (dict): Fields to update

        Returns:
            UpdateResult: MongoDB update result
        """
        if self.db is None:
            raise RuntimeError("Database connection not established. Call connect() first.")

        try:
            collection = self.db[self.dest_coll_name]

            result = collection.update_one({"_id": user_id}, {"$set": update_doc})

            return result

        except Exception as e:
            logging.error(f"Error updating user {user_id}: {e}")
            raise

    def get_collection_stats(self):
        """
        Get statistics about the destination collection.

        Returns:
            dict: Collection statistics
        """
        if self.db is None:
            logging.warning("Database connection not established. Cannot retrieve statistics.")
            return None

        try:
            collection = self.db[self.dest_coll_name]

            total_users = collection.count_documents({})
            active_users = collection.count_documents({"IsActive": True})
            users_with_athena = collection.count_documents({"AthenaProviderId": {"$ne": None, "$exists": True}})

            return {"total_users": total_users, "active_users": active_users, "users_with_athena": users_with_athena}

        except Exception as e:
            logging.warning(f"Could not retrieve collection statistics: {e}")
            return None

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed")
