from pathlib import Path

BASE_DIR = Path(__file__).parent

MIN_PRICE = 2_500_000

REGIONS = [
    "noord-brabant",
    "limburg",
    "zuid-holland",
    "utrecht",
    "gelderland",
]

# "koop" = residential for-sale, "bog" = bedrijfsonroerendgoed (commercial)
SEARCH_TYPES = ["koop", "bog"]

SNAPSHOT_FILE = BASE_DIR / "snapshot.json"

# How many result pages to fetch per region/type combination
PAGES_PER_QUERY = 10

REPORT_TITLE = "Nieuw vastgoedaanbod | Lammers Beton"

# Color palette
COLOR_HEADER_BG = "#1a1a1a"
COLOR_HEADER_TEXT = "#ffffff"
COLOR_BODY_BG = "#f4f1ed"
COLOR_CARD_BG = "#e8e0d5"
COLOR_TEXT = "#2c2c2c"
COLOR_ACCENT = "#b5a48a"
COLOR_BUTTON_TEXT = "#ffffff"
