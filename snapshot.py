"""
Manages the weekly snapshot: a JSON file mapping listing_id → listing dict.
On each run the snapshot is fully overwritten with the current result set.
"""

import json
import logging
from pathlib import Path

from config import SNAPSHOT_FILE

logger = logging.getLogger(__name__)


def load_snapshot(path: Path = SNAPSHOT_FILE) -> dict[str, dict]:
    """Load the snapshot from disk. Returns an empty dict if the file doesn't exist."""
    if not path.exists():
        logger.info("No existing snapshot found — treating all fetched listings as new.")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        logger.info(f"Loaded snapshot with {len(data)} listings from {path}")
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.error(f"Failed to read snapshot ({exc}) — starting fresh.")
        return {}


def save_snapshot(listings: list[dict], path: Path = SNAPSHOT_FILE) -> None:
    """Overwrite the snapshot with the current full listing set."""
    snapshot: dict[str, dict] = {listing["id"]: listing for listing in listings}
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, ensure_ascii=False, indent=2)
        logger.info(f"Snapshot saved: {len(snapshot)} listings → {path}")
    except OSError as exc:
        logger.error(f"Failed to save snapshot: {exc}")
