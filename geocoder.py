"""
Geocoding via Nominatim (OpenStreetMap) — gratis, geen API-sleutel nodig.
Resultaten worden gecached zodat dezelfde postcode niet twee keer opgezocht wordt.
Rate limit: 1 verzoek per seconde (Nominatim-vereiste).
"""

import logging
import ssl
import time
import urllib.parse
import urllib.request
import json
from typing import Optional

# macOS Python.org-installaties missen soms root-certificaten.
# Gebruik certifi als dat beschikbaar is, anders vertrouw op het systeem.
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, float]] = {}
_last_request_time: float = 0.0
_USER_AGENT = "LammersBeton-vastgoedmonitor/1.0 (contact: monitor@lammersbeton.nl)"


def _nominatim_request(query: str) -> Optional[tuple[float, float]]:
    global _last_request_time

    # Respecteer de 1 req/sec rate limit van Nominatim
    elapsed = time.time() - _last_request_time
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)

    params = urllib.parse.urlencode({"q": query, "format": "json", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
            _last_request_time = time.time()
            data = json.loads(resp.read().decode())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as exc:
        logger.warning(f"Geocoding mislukt voor '{query}': {exc}")

    return None


def geocode(query: str) -> Optional[tuple[float, float]]:
    """Zet een adres/postcode om naar (lat, lon). Resultaten worden gecached."""
    key = query.strip().lower()
    if key in _cache:
        return _cache[key]

    result = _nominatim_request(query)
    if result:
        _cache[key] = result
    return result


def geocode_listing(listing: dict) -> dict:
    """
    Voeg lat/lon toe aan een listing dict op basis van postcode + stad.
    Past de listing in-place aan en geeft hem terug.
    """
    if listing.get("lat") and listing.get("lon"):
        return listing

    postcode = listing.get("postcode", "")
    city = listing.get("city", "")
    country = listing.get("country", "NL")

    # Probeer eerst op postcode, dan op stad
    query = f"{postcode} {country}".strip() if postcode else f"{city} {country}".strip()
    if not query.strip():
        return listing

    coords = geocode(query)
    if coords:
        listing["lat"], listing["lon"] = coords
    else:
        listing["lat"] = None
        listing["lon"] = None

    return listing
