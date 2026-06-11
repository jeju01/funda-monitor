"""
Haalt Belgische listings op van immoweb.be via Playwright (headless Chrome).
Immoweb gebruikt client-side rendering, dus een echte browser is vereist.
"""

import logging
import re
from typing import Optional

from config import MIN_PRICE
from geocoder import geocode_listing

logger = logging.getLogger(__name__)

IMMOWEB_BASE = "https://www.immoweb.be"
SEARCH_URL = (
    f"{IMMOWEB_BASE}/nl/zoeken/huis,appartement,villa,te-koop-of-te-huur/te-koop"
    f"?countries=BE&minPrice={{min_price}}&orderBy=newest&page={{page}}"
)

MAX_PAGES = 5


def _dedup_text(text: str) -> str:
    """Verwijder herhaalde zinsdelen, bijv. 'prijs op aanvraag prijs op aanvraag' → 'prijs op aanvraag'."""
    text = " ".join(text.split())  # normaliseer witruimte
    half = len(text) // 2
    # Check of de eerste helft exact herhaald wordt
    if len(text) > 10 and text[:half].strip() == text[half:].strip():
        return text[:half].strip()
    # Check op zin-niveau: splits op bekende scheidingstekens en dedupliceer
    parts = [p.strip() for p in re.split(r"[\n\r]+", text) if p.strip()]
    seen: list[str] = []
    for p in parts:
        if p.lower() not in [s.lower() for s in seen]:
            seen.append(p)
    return " ".join(seen)


def _parse_price(text: str) -> tuple[Optional[int], str]:
    """
    Geeft (getal, weergave_tekst) terug.
    Bij complexe prijzen zoals "€ 95.000 + € 1.275/maand" wordt het getal
    op None gezet en de originele tekst bewaard voor weergave.
    """
    cleaned = text.strip()

    # Detecteer complexe prijsstrings — sla als tekst op, niet als getal
    if any(w in cleaned.lower() for w in ["/maand", "/month", "maand", "+ €", "+€", "erfpacht", "p/m"]):
        return None, cleaned

    # Meerdere losstaande grote getallen? Dan ook niet parsen
    numbers = re.findall(r"\d[\d.]+\d", cleaned)
    if len(numbers) > 1:
        return None, cleaned

    digits = re.sub(r"[^\d]", "", cleaned)
    if not digits:
        return None, cleaned
    return int(digits), cleaned


def _extract_id(url: str) -> Optional[str]:
    m = re.search(r"/(\d{6,12})(?:\?|$)", url)
    return m.group(1) if m else url.strip("/").split("/")[-1]


def _extract_card(card) -> Optional[dict]:
    """Extraheer data uit één Playwright card-element."""
    try:
        url_el = card.locator("a.card__title-link").first
        url = url_el.get_attribute("href") if url_el.count() else ""
        if not url:
            return None
        full_url = url if url.startswith("http") else f"{IMMOWEB_BASE}{url}"

        listing_id = _extract_id(full_url)
        if not listing_id:
            return None

        # Prijs — gebruik sr-only span met machine-leesbaar getal (bijv. "2990000€")
        price_int = None
        price_display = None
        sr_el = card.locator(".sr-only").all()
        for el in sr_el:
            txt = el.inner_text().strip()
            if re.search(r"\d{6,}", txt):
                price_int, price_display = _parse_price(txt)
                if price_int:
                    break
        # Fallback: zichtbare prijstekst (inclusief complexe formaten)
        if not price_int:
            price_el = card.locator("[class*=card--result__price]").first
            if price_el.count():
                visible_text = _dedup_text(price_el.inner_text())
                price_int, price_display = _parse_price(visible_text)
                if not price_display:
                    price_display = visible_text
        # Geen harde prijsgrens — filteren gebeurt via de schuifbalk op de website

        # Stad / postcode — formaat: "8300 Knokke-Heist"
        locality_el = card.locator("[class*=information--locality]").first
        locality_text = locality_el.inner_text().strip() if locality_el.count() else ""
        postcode_match = re.match(r"(\d{4})\s+(.*)", locality_text)
        postcode = postcode_match.group(1) if postcode_match else ""
        city = postcode_match.group(2) if postcode_match else locality_text

        # Titel: gebruik aria-label van de link voor type + stad
        # bijv. "House te koop, Uccle (2.990.000 €)" → "Huis – Uccle"
        link_el = card.locator("a.card__title-link").first
        aria = link_el.get_attribute("aria-label") if link_el.count() else ""
        if aria:
            # Extraheer type-deel vóór " te koop"
            type_part = re.split(r"\s+te\s+koop", aria, flags=re.I)[0].strip()
            title = f"{type_part} – {city}" if city else type_part
        else:
            title_el = card.locator("h2.card__title").first
            title = title_el.inner_text().strip() if title_el.count() else "Vastgoed"

        # Oppervlakte en slaapkamers
        surface_m2 = None
        rooms = None
        specs_els = card.locator("[class*=property__item]").all()
        for spec in specs_els:
            text = spec.inner_text().strip()
            m2 = re.search(r"(\d+)\s*m²", text)
            slp = re.search(r"(\d+)\s*(?:slp|slaapkamer)", text, re.I)
            if m2:
                surface_m2 = int(m2.group(1))
            if slp:
                rooms = int(slp.group(1))

        # Foto
        img_el = card.locator("img.card__media-picture").first
        thumbnail_url = img_el.get_attribute("src") if img_el.count() else None

        def fmt_price(amount, display):
            if amount:
                return "€ " + f"{amount:,.0f}".replace(",", ".")
            if display:
                return display  # bijv. "€ 95.000 + € 1.275/maand"
            return "Prijs onbekend"

        return {
            "id": f"immo_{listing_id}",
            "address": title,
            "city": city,
            "postcode": postcode,
            "country": "BE",
            "source": "Immoweb",
            "price": price_int,
            "price_formatted": fmt_price(price_int, price_display),
            "surface_m2": surface_m2,
            "rooms": rooms,
            "listing_type": "Woning",
            "thumbnail_url": thumbnail_url,
            "funda_url": full_url,
            "region": "België",
            "search_type": "koop",
            "lat": None,
            "lon": None,
        }
    except Exception as exc:
        logger.debug(f"Card parse fout: {exc}")
        return None


def fetch_immoweb_listings(min_price: int = MIN_PRICE) -> list[dict]:
    """
    Haalt listings op van immoweb.be via Playwright.
    Geeft een lijst van listing-dicts terug.
    """
    try:
        from playwright.sync_api import sync_playwright  # noqa
    except ImportError:
        logger.error("Playwright niet geïnstalleerd. Voer uit: pip3 install playwright && playwright install chromium")
        return []

    results: list[dict] = []

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            ctx = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="nl-BE",
                viewport={"width": 1280, "height": 800},
            )
            page = ctx.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            for page_num in range(1, MAX_PAGES + 1):
                url = SEARCH_URL.format(min_price=min_price, page=page_num)
                logger.info(f"Immoweb: pagina {page_num} laden…")

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(4000)
                except Exception as exc:
                    logger.error(f"Immoweb pagina {page_num} timeout: {exc}")
                    break

                cards = page.locator("article.card--result").all()
                logger.info(f"  → {len(cards)} cards op pagina {page_num}")

                if not cards:
                    break

                page_results = []
                for card in cards:
                    listing = _extract_card(card)
                    if listing:
                        geocode_listing(listing)
                        page_results.append(listing)

                results.extend(page_results)
                logger.info(f"  → {len(page_results)} bruikbare listings op pagina {page_num}")

                # Stop als er minder dan 20 cards zijn (laatste pagina)
                if len(cards) < 20:
                    break

            browser.close()

    except Exception as exc:
        logger.error(f"Immoweb scraper fout: {exc}")

    logger.info(f"Immoweb totaal: {len(results)} listings")
    return results
