"""Central project settings."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"

K_MAX = 8
AGE_MAX = 110
EPSILON = 1e-15

HMD_COUNTRIES = {
    "SWE": "Sweden",
    "DNK": "Denmark",
    "FRATNP": "France",
    "CHL": "Chile",
    "JPN": "Japan",
}

LOCAL_COUNTRIES = {
    "NORDESTE": "Nordeste (Brasil)",
    "CHILE_2023": "Chile",
}

COUNTRY_FILE_HINTS = {
    "SWE": "SWE",
    "DNK": "DNK",
    "FRATNP": "FRATNP",
    "CHL": "CHL",
    "JPN": "JPN",
    "NORDESTE": "nordeste",
    "CHILE_2023": "chile",
}

VIRIDIS_CMAP = "viridis"

