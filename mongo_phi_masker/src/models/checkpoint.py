"""Checkpoint management for incremental processing."""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class CheckpointManager:
    """Manage checkpoints for incremental processing."""

    def __init__(self, checkpoint_file: str, checkpoint_interval: int = 1000):
        """Initialize the checkpoint manager.

        Args:
            checkpoint_file: Path to the checkpoint file
            checkpoint_interval: Number of documents to process before saving checkpoint
        """
        self.checkpoint_file = checkpoint_file
        self.checkpoint_interval = checkpoint_interval
        self.processed_count = 0
        self.last_id = None
        self.last_timestamp = None

    def should_save_checkpoint(self) -> bool:
        """Check if a checkpoint should be saved.

        Returns:
            True if checkpoint should be saved, False otherwise
        """
        return self.processed_count % self.checkpoint_interval == 0

    def update_checkpoint(
        self, doc_id: Any, timestamp: Optional[datetime] = None
    ) -> None:
        """Update the checkpoint with the latest document ID and timestamp.

        Args:
            doc_id: The document ID
            timestamp: The document timestamp
        """
        self.last_id = doc_id
        self.last_timestamp = timestamp or datetime.now()
        self.processed_count += 1

    def save_checkpoint(self) -> None:
        """Save the checkpoint to a file."""
        if not self.last_id:
            return

        checkpoint_data = {
            "last_id": str(self.last_id),
            "last_timestamp": (
                self.last_timestamp.isoformat() if self.last_timestamp else None
            ),
            "processed_count": self.processed_count,
            "saved_at": datetime.now().isoformat(),
        }

        # Create directory if it doesn't exist
        checkpoint_dir = os.path.dirname(self.checkpoint_file)
        if checkpoint_dir and not os.path.exists(checkpoint_dir):
            os.makedirs(checkpoint_dir)

        with open(self.checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f, indent=2)

    def load_checkpoint(self) -> Dict[str, Any]:
        """Load the checkpoint from a file.

        Returns:
            Checkpoint data
        """
        if not os.path.exists(self.checkpoint_file):
            return {}

        try:
            with open(self.checkpoint_file, "r") as f:
                checkpoint_data = json.load(f)
                self.last_id = checkpoint_data.get("last_id")

                # Parse timestamp if present
                last_timestamp = checkpoint_data.get("last_timestamp")
                if last_timestamp:
                    self.last_timestamp = datetime.fromisoformat(last_timestamp)

                self.processed_count = checkpoint_data.get("processed_count", 0)
                return checkpoint_data
        except Exception as e:
            # Return empty checkpoint if file is corrupted
            return {}

    def reset_checkpoint(self) -> None:
        """Reset the checkpoint."""
        self.last_id = None
        self.last_timestamp = None
        self.processed_count = 0

        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
