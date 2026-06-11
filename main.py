"""
Entry point voor de Funda vastgoedmonitor.

Gebruik:
  python3 main.py          # start de wekelijkse scheduler (elke maandag 08:00)
  python3 main.py --now    # voer direct een run uit en stop daarna
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import schedule

from config import MIN_PRICE, REGIONS
from dashboard import save_dashboard
from diff import find_new_listings
from fetcher import fetch_all_listings
from fetcher_immoweb import fetch_immoweb_listings
from publisher import publish_dashboard
from snapshot import load_snapshot, save_snapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_weekly_report() -> None:
    logger.info("=" * 60)
    logger.info("Funda monitor gestart")
    logger.info(f"Regio's: {', '.join(REGIONS)}")
    logger.info(f"Minimumprijs: €{MIN_PRICE:,}")
    logger.info("=" * 60)

    # 1. Laad vorige snapshot
    last_snapshot = load_snapshot()

    # 2. Haal alle huidige listings op (Funda NL + Immoweb BE)
    funda_listings = fetch_all_listings(regions=REGIONS, min_price=MIN_PRICE)
    immoweb_listings = fetch_immoweb_listings(min_price=MIN_PRICE)
    current_listings = funda_listings + immoweb_listings
    logger.info(f"Totaal: {len(funda_listings)} Funda + {len(immoweb_listings)} Immoweb = {len(current_listings)} listings")

    # 3. Bepaal nieuwe listings
    new_listings = find_new_listings(current_listings, last_snapshot)

    # 4. Sla snapshot op (alleen als er resultaten zijn)
    if current_listings:
        save_snapshot(current_listings)
    else:
        logger.warning("Geen listings opgehaald — snapshot NIET overschreven.")

    # 5. Genereer dashboard
    dashboard_path = save_dashboard(current_listings)
    logger.info(f"Dashboard gegenereerd: {dashboard_path}")
    logger.info(f"Nieuw deze week: {len(new_listings)} object(en)")

    # 6. Publiceer naar GitHub Pages
    publish_dashboard()

    logger.info("Run voltooid.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Funda vastgoedmonitor")
    parser.add_argument("--now", action="store_true", help="Voer direct een run uit")
    args = parser.parse_args()

    if args.now:
        logger.info("Handmatige run via --now")
        run_weekly_report()
        return

    logger.info("Scheduler gestart. Volgende run: elke maandag om 08:00.")
    schedule.every().monday.at("08:00").do(run_weekly_report)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
