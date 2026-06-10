"""
Fetches listings from Funda.nl via pyfunda 3.x (pip install pyfunda).

The package installs as the `funda` module. API:
  from funda import Funda
  with Funda() as f:
      listings = list(f.iter_search("amsterdam", min_price=500000, max_pages=5))

Listing fields used here (all are properties or nested dataclass attributes):
  listing.id              → tiny_id ?? str(global_id) ?? listing_id
  listing.title           → address.title  (street + house number)
  listing.city            → address.city
  listing.price.amount    → int price in euros
  listing.living_area     → areas.living (m²)
  listing.rooms_count     → rooms.total
  listing.url             → urls.full  (absolute Funda URL)
  listing.media.photo_urls → tuple of absolute photo URLs

Note on BOG (commercial listings):
  pyfunda 3.x hardcodes zoning=["residential"] in its search payload.
  Commercial (BOG) listings therefore cannot be fetched through this client.
  Only residential for-sale listings are returned. BOG is skipped silently.
"""

import logging
from typing import Optional

from config import MIN_PRICE, PAGES_PER_QUERY, REGIONS

logger = logging.getLogger(__name__)


def _format_price(amount: Optional[int]) -> str:
    if amount is None:
        return "Prijs onbekend"
    return "€ " + f"{amount:,.0f}".replace(",", ".")


def _listing_to_dict(listing, region: str) -> Optional[dict]:
    """Convert a funda.Listing object to our internal dict format."""
    listing_id = listing.id
    if not listing_id:
        return None

    price_amount: Optional[int] = listing.price.amount if listing.price else None

    # Guard against listings that slip past the server-side price filter
    if price_amount is not None and price_amount < MIN_PRICE:
        return None

    address_title = listing.title or "Adres onbekend"
    city = listing.city or ""

    surface_m2: Optional[int] = listing.living_area  # areas.living

    rooms: Optional[int] = listing.rooms_count  # rooms.total

    # First available photo
    thumbnail_url: Optional[str] = None
    if listing.media and listing.media.photo_urls:
        thumbnail_url = listing.media.photo_urls[0]

    funda_url = listing.url or f"https://www.funda.nl/koop/{listing_id}/"

    return {
        "id": str(listing_id),
        "address": address_title,
        "city": city,
        "price": price_amount,
        "price_formatted": _format_price(price_amount),
        "surface_m2": surface_m2,
        "rooms": rooms,
        "listing_type": "Woning",
        "thumbnail_url": thumbnail_url,
        "funda_url": funda_url,
        "region": region,
        "search_type": "koop",
    }


def _fetch_region(region: str, min_price: int) -> list[dict]:
    """Fetch all pages for one region. Returns a list of listing dicts."""
    try:
        from funda import Funda  # noqa: PLC0415
    except ImportError:
        logger.error(
            "The `funda` module is not found. "
            "Make sure pyfunda is installed: pip install pyfunda"
        )
        return []

    results: list[dict] = []
    try:
        with Funda() as client:
            for raw_listing in client.iter_search(
                region,
                min_price=min_price,
                max_pages=PAGES_PER_QUERY,
            ):
                normalized = _listing_to_dict(raw_listing, region)
                if normalized:
                    results.append(normalized)
    except Exception as exc:
        logger.error(f"Failed to fetch region '{region}': {exc}")

    return results


def fetch_all_listings(
    regions: list[str] = REGIONS,
    min_price: int = MIN_PRICE,
) -> list[dict]:
    """
    Fetch all listings across all regions.
    Per-region failures are caught and logged; the full run continues.
    Returns a deduplicated list of listing dicts.
    """
    seen_ids: set[str] = set()
    all_listings: list[dict] = []

    for region in regions:
        logger.info(f"Fetching '{region}' (min price: €{min_price:,})")
        try:
            listings = _fetch_region(region, min_price)
        except Exception as exc:
            logger.error(f"Unexpected error for region '{region}': {exc}")
            listings = []

        added = 0
        for listing in listings:
            lid = listing["id"]
            if lid not in seen_ids:
                seen_ids.add(lid)
                all_listings.append(listing)
                added += 1

        logger.info(f"  → {added} unique listings for '{region}'")

    logger.info(f"Total listings fetched: {len(all_listings)}")
    return all_listings
