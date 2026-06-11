"""
Beheert de snapshot: een JSON-bestand met listing_id → listing dict.

Samenvoegstrategie: nieuwe listings worden toegevoegd/bijgewerkt,
bestaande listings blijven bewaard. Listings verdwijnen nooit automatisch
uit de snapshot — zo gaan eerder opgehaalde panden niet verloren.
"""

import json
import logging
from pathlib import Path

from config import SNAPSHOT_FILE

logger = logging.getLogger(__name__)


def load_snapshot(path: Path = SNAPSHOT_FILE) -> dict[str, dict]:
    if not path.exists():
        logger.info("Geen bestaande snapshot — alle listings worden als nieuw behandeld.")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        logger.info(f"Snapshot geladen: {len(data)} listings uit {path}")
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.error(f"Snapshot lezen mislukt ({exc}) — verse start.")
        return {}


def save_snapshot(new_listings: list[dict], path: Path = SNAPSHOT_FILE) -> None:
    """
    Voeg nieuwe listings samen met de bestaande snapshot.
    Bestaande listings worden bijgewerkt (prijs, foto etc. kunnen veranderen),
    maar worden nooit verwijderd. Zo gaan listings van vorige runs niet verloren.
    """
    existing = load_snapshot(path)
    existing.update({l["id"]: l for l in new_listings})
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(existing, fh, ensure_ascii=False, indent=2)
        logger.info(f"Snapshot opgeslagen: {len(existing)} listings totaal ({len(new_listings)} nieuw/bijgewerkt) → {path}")
    except OSError as exc:
        logger.error(f"Snapshot opslaan mislukt: {exc}")
