from pathlib import Path

BASE_DIR = Path(__file__).parent

MIN_PRICE = 0

# Middelpunt voor de straalzoekopdracht (aanpasbaar)
CENTER_ADDRESS = "Trancheeweg 18, 6002 ST Weert, NL"
DEFAULT_RADIUS_KM = 75  # standaard straal in km

REGIONS = [
    "noord-brabant",
    "limburg",
    "zuid-holland",
    "utrecht",
    "gelderland",
]

# Ondersteunde stralen door pyfunda: 1, 2, 5, 10, 15, 30, 50 km
# Voor grotere stralen fetchen we per regio en filteren we zelf op afstand
FUNDA_MAX_RADIUS_KM = 50

SNAPSHOT_FILE = BASE_DIR / "snapshot.json"

# Aantal resultaatpagina's per zoekopdracht
PAGES_PER_QUERY = 10

REPORT_TITLE = "Nieuw vastgoedaanbod | Lammers Beton"

# Kleurenpalet
COLOR_HEADER_BG = "#1a1a1a"
COLOR_HEADER_TEXT = "#ffffff"
COLOR_BODY_BG = "#f4f1ed"
COLOR_CARD_BG = "#e8e0d5"
COLOR_TEXT = "#2c2c2c"
COLOR_ACCENT = "#b5a48a"
COLOR_BUTTON_TEXT = "#ffffff"
