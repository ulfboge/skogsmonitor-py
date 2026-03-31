"""
Gemensam konfiguration — Fiby urskog (samma AOI som NVI-repot använder som testfall).
Koordinatsystem: SWEREF 99 TM (EPSG:3006) för analyseraster.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

AOI_NAME = "fiby_urskog"
AOI_LABEL = "Fiby urskog, Uppland"

AOI_BBOX_WGS84 = {
    "min_lon": 17.02,
    "max_lon": 17.12,
    "min_lat": 59.85,
    "max_lat": 59.92,
}

EPSG_WGS84 = 4326
EPSG_SWEREF = 3006

# Sommarfönster — samma typ av preset som GEE-demon (jämförbara säsonger)
PERIOD_A = {"start": "2022-06-01", "end": "2022-08-31", "label": "sommar_2022"}
PERIOD_B = {"start": "2024-06-01", "end": "2024-08-31", "label": "sommar_2024"}

DATA_PROCESSED = REPO_ROOT / "data" / "processed"
OUTPUT_RASTERS = REPO_ROOT / "outputs" / "rasters"
OUTPUT_COGS = REPO_ROOT / "outputs" / "cogs"
DOCS_COGS = REPO_ROOT / "docs" / "cogs"

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
S2_COLLECTION = "sentinel-2-l2a"

# Max moln på scen (STAC-query)
MAX_CLOUD_COVER = 35

# Upplösning meter i SWEREF
RESOLUTION_M = 10

for d in (DATA_PROCESSED, OUTPUT_RASTERS, OUTPUT_COGS, DOCS_COGS):
    d.mkdir(parents=True, exist_ok=True)
