"""
Checkpoint manager utility for MongoDB PHI masking pipeline.

This module provides checkpoint management capabilities:
- Progress tracking
- State persistence
- Recovery from interruptions
"""

import os
import json
import logging
import threading
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
from bson import ObjectId


# Create a custom JSON encoder that can handle ObjectId
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # Convert ObjectId to string
        return super().default(o)


class CheckpointManager:
    """Manages checkpoints for resumable operations."""

    def __init__(self, config: Dict[str, Any], component: str = "masking"):
        """Initialize the checkpoint manager.

        Args:
            config: Checkpoint configuration
            component: Component name (e.g., masking, indexing)
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.component = component

        # Get component-specific configuration
        component_config = config.get(component, {})

        # Checkpoint file path
        self.checkpoint_file = component_config.get(
            "file", f"checkpoints/{component}/checkpoint.json"
        )

        # Create directory if it doesn't exist
        checkpoint_dir = os.path.dirname(self.checkpoint_file)
        os.makedirs(checkpoint_dir, exist_ok=True)

        # Checkpoint frequency
        self.checkpoint_interval = component_config.get("interval", 1000)  # documents
        self.save_interval = component_config.get("save_interval", 300)  # seconds

        # State variables
        self.state: Dict[str, Any] = {}
        self.dirty = False
        self.last_save_time = time.time()

        # Auto-save thread
        self.autosave_thread = None
        self.stop_event = threading.Event()

        # Load existing checkpoint if available
        self.load()

    def load(self) -> Dict[str, Any]:
        """Load checkpoint state from file.

        Returns:
            The loaded checkpoint state
        """
        if not os.path.exists(self.checkpoint_file):
            self.logger.info(f"No checkpoint file found at {self.checkpoint_file}")
            return {}

        try:
            with open(self.checkpoint_file, "r") as f:
                self.state = json.load(f)
                self.logger.info(f"Loaded checkpoint from {self.checkpoint_file}")
                return self.state
        except Exception as e:
            self.logger.error(
                f"Error loading checkpoint from {self.checkpoint_file}: {str(e)}"
            )
            return {}

    def save(self) -> bool:
        """Save checkpoint state to file.

        Returns:
            True if save was successful, False otherwise
        """
        if not self.dirty:
            return True

        try:
            # Update timestamp
            self.state["last_updated"] = datetime.now().isoformat()

            # Use the custom encoder for JSON serialization
            with open(self.checkpoint_file, "w") as f:
                json.dump(self.state, f, cls=MongoJSONEncoder)

            self.dirty = False
            self.last_save_time = time.time()
            self.logger.debug(f"Saved checkpoint to {self.checkpoint_file}")
            return True
        except Exception as e:
            self.logger.error(
                f"Error saving checkpoint to {self.checkpoint_file}: {str(e)}"
            )
            return False

    def update(self, updates: Dict[str, Any], force_save: bool = False) -> None:
        """Update checkpoint state.

        Args:
            updates: State updates to apply
            force_save: Whether to force an immediate save
        """
        # Update state
        self.state.update(updates)
        self.dirty = True

        # Auto-save based on document count
        docs_processed = self.state.get("docs_processed", 0)
        if force_save or (docs_processed % self.checkpoint_interval == 0):
            self.save()

    def start_autosave(self) -> None:
        """Start the autosave thread."""
        if self.autosave_thread is not None:
            return

        self.logger.info("Starting checkpoint autosave thread")
        self.stop_event.clear()
        self.autosave_thread = threading.Thread(target=self._autosave_loop, daemon=True)
        self.autosave_thread.start()

    def stop_autosave(self) -> None:
        """Stop the autosave thread if running."""
        if self.autosave_thread:
            self.stop_event.set()
            self.autosave_thread.join(timeout=5.0)
            if self.dirty:  # Make sure we save if we have pending changes
                self.save()
            self.autosave_thread = None

    def get_last_processed_id(self) -> Optional[str]:
        """Get the ID of the last processed document.

        Returns:
            The last processed document ID or None
        """
        return self.state.get("last_processed_id")

    def get_docs_processed(self) -> int:
        """Get the number of documents processed.

        Returns:
            The number of documents processed
        """
        return self.state.get("docs_processed", 0)

    def get_state(self) -> Dict[str, Any]:
        """Get the current checkpoint state.

        Returns:
            The current checkpoint state
        """
        return self.state.copy()

    def reset(self) -> None:
        """Reset the checkpoint state."""
        self.state = {
            "component": self.component,
            "start_time": datetime.now().isoformat(),
            "docs_processed": 0,
            "last_processed_id": None,
            "last_updated": datetime.now().isoformat(),
        }
        self.dirty = True
        self.save()
        self.logger.info(f"Reset checkpoint state for {self.component}")

    def _autosave_loop(self) -> None:
        """Autosave loop for periodic checkpoint saving."""
        while not self.stop_event.is_set():
            try:
                time.sleep(1.0)  # Check frequently but save based on interval

                current_time = time.time()
                elapsed = current_time - self.last_save_time

                if self.dirty and elapsed >= self.save_interval:
                    self.save()
            except Exception as e:
                self.logger.error(f"Error in checkpoint autosave: {str(e)}")

    def save_checkpoint(self, collection_name: str) -> None:
        """
        Save the current checkpoint state to disk
        """
        try:
            checkpoint_file = self._get_checkpoint_file(collection_name)
            os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)

            with open(checkpoint_file, "w") as f:
                # Use the custom encoder for JSON serialization
                json.dump(
                    self.checkpoints.get(collection_name, {}), f, cls=MongoJSONEncoder
                )

            self.logger.debug(f"Saved checkpoint to {checkpoint_file}")
        except Exception as e:
            self.logger.error(f"Error saving checkpoint to {checkpoint_file}: {str(e)}")

    def _get_checkpoint_file(self, collection_name: str) -> str:
        """Get the path to the checkpoint file for a specific collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Path to the checkpoint file for the specified collection
        """
        return os.path.join(
            os.path.dirname(self.checkpoint_file), f"{collection_name}.json"
        )


class IncrementalSyncCheckpoint:
    """Specialized checkpoint manager for incremental synchronization."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the incremental sync checkpoint.

        Args:
            config: Incremental sync configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Checkpoint file path
        self.checkpoint_file = config.get(
            "checkpoint_file", "checkpoints/incremental/state.json"
        )

        # Create directory if it doesn't exist
        checkpoint_dir = os.path.dirname(self.checkpoint_file)
        os.makedirs(checkpoint_dir, exist_ok=True)

        # Field tracking
        field_tracking = config.get("field_tracking", {})
        self.last_modified_field = field_tracking.get(
            "last_modified_field", "lastModified"
        )
        self.track_field_updates = field_tracking.get("track_field_updates", True)

        # State variables
        self.state: Dict[str, Any] = {"collections": {}}

        # Load existing checkpoint if available
        self.load()

    def load(self) -> Dict[str, Any]:
        """Load incremental sync state from file.

        Returns:
            The loaded incremental sync state
        """
        if not os.path.exists(self.checkpoint_file):
            self.logger.info(
                f"No incremental sync checkpoint file found at {self.checkpoint_file}"
            )
            return self.state

        try:
            with open(self.checkpoint_file, "r") as f:
                self.state = json.load(f)
                self.logger.info(
                    f"Loaded incremental sync checkpoint from {self.checkpoint_file}"
                )
                return self.state
        except Exception as e:
            self.logger.error(f"Error loading incremental sync checkpoint: {str(e)}")
            return self.state

    def save(self) -> bool:
        """Save incremental sync state to file.

        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Update timestamp
            self.state["last_updated"] = datetime.now().isoformat()

            # Use the custom encoder for JSON serialization
            with open(self.checkpoint_file, "w") as f:
                json.dump(self.state, f, cls=MongoJSONEncoder)

            self.logger.debug(
                f"Saved incremental sync checkpoint to {self.checkpoint_file}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error saving incremental sync checkpoint: {str(e)}")
            return False

    def get_last_sync_time(self, collection: str) -> Optional[str]:
        """Get the last sync time for a collection.

        Args:
            collection: Collection name

        Returns:
            The last sync time as ISO-8601 string or None
        """
        return (
            self.state.get("collections", {}).get(collection, {}).get("last_sync_time")
        )

    def update_last_sync_time(
        self, collection: str, sync_time: Optional[str] = None
    ) -> None:
        """Update the last sync time for a collection.

        Args:
            collection: Collection name
            sync_time: Sync time as ISO-8601 string, defaults to current time
        """
        if sync_time is None:
            sync_time = datetime.now().isoformat()

        if "collections" not in self.state:
            self.state["collections"] = {}

        if collection not in self.state["collections"]:
            self.state["collections"][collection] = {}

        self.state["collections"][collection]["last_sync_time"] = sync_time
        self.save()

    def get_sync_query(self, collection: str) -> Dict[str, Any]:
        """Get a query for incremental sync based on last sync time.

        Args:
            collection: Collection name

        Returns:
            MongoDB query filter for incremental sync
        """
        last_sync_time = self.get_last_sync_time(collection)

        if not last_sync_time:
            # First sync, return empty query (all documents)
            return {}

        # Convert ISO-8601 string to datetime for MongoDB query
        last_sync_datetime = datetime.fromisoformat(last_sync_time)

        # Query for documents modified since last sync
        return {self.last_modified_field: {"$gt": last_sync_datetime}}

    def get_tracked_fields(self, collection: str) -> List[str]:
        """Get list of fields to track for a collection.

        Args:
            collection: Collection name

        Returns:
            List of field names to track
        """
        return (
            self.state.get("collections", {})
            .get(collection, {})
            .get("tracked_fields", [])
        )

    def update_tracked_fields(self, collection: str, fields: List[str]) -> None:
        """Update the list of tracked fields for a collection.

        Args:
            collection: Collection name
            fields: List of field names to track
        """
        if not self.track_field_updates:
            return

        if "collections" not in self.state:
            self.state["collections"] = {}

        if collection not in self.state["collections"]:
            self.state["collections"][collection] = {}

        self.state["collections"][collection]["tracked_fields"] = list(set(fields))
        self.save()
