"""Central project settings."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"

K_MAX = 8
MAX_ANALYSIS_AGE = 90
EPSILON = 1e-15
VIRIDIS_CMAP = "viridis"
