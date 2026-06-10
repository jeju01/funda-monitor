"""
Compares current listings against the previous snapshot and returns only new ones.
"""

import logging

logger = logging.getLogger(__name__)


def find_new_listings(
    current_listings: list[dict],
    last_snapshot: dict[str, dict],
) -> list[dict]:
    """
    Return listings whose ID is not present in last_snapshot.
    If last_snapshot is empty (first run), all current listings are considered new.
    """
    new = [l for l in current_listings if l["id"] not in last_snapshot]
    logger.info(
        f"Diff: {len(current_listings)} current listings, "
        f"{len(last_snapshot)} in snapshot → {len(new)} new"
    )
    return new
