"""
Steg 3: Skapa Cloud Optimized GeoTIFF (COG) för webbkartan och kopiera till docs/cogs/.

Använder GDAL/rasterio COG-driver om tillgänglig; annars GeoTIFF med översikter.

Kör:
  python scripts/export_cog.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_scripts = Path(__file__).resolve().parent
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))
import _proj_bootstrap  # noqa: E402

_proj_bootstrap.ensure_rasterio_proj()

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds

_WGS84 = CRS.from_string("+proj=longlat +datum=WGS84 +no_defs +type=crs")

import config


def to_cog(src: Path, dst: Path) -> None:
    with rasterio.open(src) as s:
        data = s.read()
        profile = s.profile.copy()
        descriptions = s.descriptions

    profile.update(
        tiled=True,
        blockxsize=256,
        blockysize=256,
        compress="deflate",
        predictor=3,
        BIGTIFF="IF_SAFER",
    )

    try:
        profile["driver"] = "COG"
        with rasterio.open(dst, "w", **profile) as d:
            d.write(data)
            if descriptions:
                for i, desc in enumerate(descriptions, start=1):
                    if desc:
                        d.set_band_description(i, desc)
        return
    except Exception:
        dst.unlink(missing_ok=True)

    profile["driver"] = "GTiff"
    with rasterio.open(dst, "w", **profile) as d:
        d.write(data)
        if descriptions:
            for i, desc in enumerate(descriptions, start=1):
                if desc:
                    d.set_band_description(i, desc)

    with rasterio.open(dst, "r+") as d:
        d.build_overviews([2, 4, 8, 16, 32], Resampling.average)
        d.update_tags(ns="rio_overview", resampling="average")


def write_bounds_json(tif_path: Path, json_path: Path) -> None:
    with rasterio.open(tif_path) as ds:
        w, s, e, n = transform_bounds(ds.crs, _WGS84, *ds.bounds)
    json_path.write_text(
        json.dumps({"west": w, "south": s, "east": e, "north": n}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    delta_name = (
        f"ndvi_delta_{config.AOI_NAME}_{config.PERIOD_B['label']}_minus_{config.PERIOD_A['label']}.tif"
    )
    delta_src = config.OUTPUT_RASTERS / delta_name
    ndvi_a_src = config.OUTPUT_RASTERS / f"ndvi_{config.AOI_NAME}_{config.PERIOD_A['label']}.tif"
    ndvi_b_src = config.OUTPUT_RASTERS / f"ndvi_{config.AOI_NAME}_{config.PERIOD_B['label']}.tif"

    for p in (delta_src, ndvi_a_src, ndvi_b_src):
        if not p.exists():
            raise FileNotFoundError(f"Saknar {p} — kör compute_ndvi.py först.")

    cog_a = config.OUTPUT_COGS / f"ndvi_a_{config.PERIOD_A['label']}_cog.tif"
    cog_b = config.OUTPUT_COGS / f"ndvi_b_{config.PERIOD_B['label']}_cog.tif"
    cog_d = config.OUTPUT_COGS / (
        f"ndvi_delta_{config.AOI_NAME}_{config.PERIOD_B['label']}_minus_{config.PERIOD_A['label']}_cog.tif"
    )
    pairs = [(ndvi_a_src, cog_a), (ndvi_b_src, cog_b), (delta_src, cog_d)]

    for src, dst in pairs:
        to_cog(src, dst)
        print(f"[COG] {dst}")

    for _, dst in pairs:
        doc_dst = config.DOCS_COGS / dst.name
        shutil.copy2(dst, doc_dst)
        print(f"[docs] {doc_dst}")

    meta = config.DOCS_COGS / "layers.json"
    meta.write_text(
        json.dumps(
            {
                "aoi": config.AOI_LABEL,
                "period_a": f"{config.PERIOD_A['start']} – {config.PERIOD_A['end']}",
                "period_b": f"{config.PERIOD_B['start']} – {config.PERIOD_B['end']}",
                "layers": {
                    "ndvi_a": f"cogs/{cog_a.name}",
                    "ndvi_b": f"cogs/{cog_b.name}",
                    "delta": f"cogs/{cog_d.name}",
                },
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_bounds_json(delta_src, config.DOCS_COGS / "delta_bounds_wgs84.json")
    print(f"[OK] {meta}")
    print("[OK] Done. Serve docs/ with a local web server (see README).")


if __name__ == "__main__":
    main()
