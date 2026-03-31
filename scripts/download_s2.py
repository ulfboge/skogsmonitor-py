"""
Steg 1: Hämta Sentinel-2 L2A (B04, B08, SCL) för två tidsfönster via STAC.

Per period väljs **en scen med lägst molntäckning** som täcker AOI (samma logik som
en enkel “bästa sommarkomposit”, utan tidsmedian). Data: Microsoft Planetary Computer
(signerade URL:er) — Copernicus S2 L2A.

Kör från reporoten:
  python scripts/download_s2.py
"""

from __future__ import annotations

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

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.crs import CRS
from rasterio.windows import from_bounds as window_from_bounds
from rasterio.warp import reproject, transform_bounds, Resampling

# Undvik EPSG:4326-uppslag (trasig proj.db på vissa Windows + rasterio-GDAL-kombinationer)
_WGS84 = CRS.from_string("+proj=longlat +datum=WGS84 +no_defs +type=crs")

import config


def _bbox_latlon() -> tuple[float, float, float, float]:
    b = config.AOI_BBOX_WGS84
    return (b["min_lon"], b["min_lat"], b["max_lon"], b["max_lat"])


def _intersects(aoi: tuple[float, float, float, float], item_bbox: list[float]) -> bool:
    w, s, e, n = aoi
    iw, is_, ie, in_ = item_bbox
    return not (e < iw or w > ie or n < is_ or s > in_)


def _read_band_to_grid(
    href: str,
    dst_crs,
    dst_transform,
    out_h: int,
    out_w: int,
    resampling: Resampling,
) -> np.ndarray:
    dest = np.full((out_h, out_w), np.nan, dtype=np.float32)
    with rasterio.open(href) as src:
        if src.crs is None:
            raise RuntimeError(f"Saknar CRS i {href}")
        reproject(
            source=rasterio.band(src, 1),
            destination=dest,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=resampling,
        )
    return dest


def _reference_grid_b04(href: str, bbox_ll: tuple[float, float, float, float]):
    with rasterio.open(href) as src:
        if src.crs is None:
            raise RuntimeError(f"Saknar CRS i {href}")
        dst_crs = src.crs
        w, s, e, n = transform_bounds(_WGS84, dst_crs, *bbox_ll)
        win = window_from_bounds(w, s, e, n, src.transform).round_offsets().round_lengths()
        tr = src.window_transform(win)
        raw = src.read(1, window=win, masked=True)
        b04 = raw.astype("float32")
        if np.ma.is_masked(raw):
            b04 = np.where(raw.mask, np.nan, b04)
        h, wpx = b04.shape
    return b04, dst_crs, tr, h, wpx


def fetch_single_scene_composite(
    catalog: pystac_client.Client,
    start: str,
    end: str,
) -> tuple[np.ndarray, object, object]:
    bbox_ll = _bbox_latlon()
    search = catalog.search(
        collections=[config.S2_COLLECTION],
        bbox=bbox_ll,
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": config.MAX_CLOUD_COVER}},
        limit=80,
    )
    items = list(search.items())
    if not items:
        raise RuntimeError(f"Inga S2-scener {start}–{end}.")

    signed = [planetary_computer.sign(i) for i in items]
    signed.sort(key=lambda i: float(i.properties.get("eo:cloud_cover", 999)))
    best = None
    for it in signed:
        if it.bbox and len(it.bbox) >= 4 and _intersects(bbox_ll, it.bbox):
            best = it
            break
    if best is None:
        raise RuntimeError("Ingen scen täcker AOI inom sökresultatet.")
    b04_h = best.assets["B04"].href
    b08_h = best.assets["B08"].href
    scl_h = best.assets["SCL"].href

    b04, crs, tr, h, wpx = _reference_grid_b04(b04_h, bbox_ll)
    b08 = _read_band_to_grid(b08_h, crs, tr, h, wpx, Resampling.bilinear)
    scl = _read_band_to_grid(scl_h, crs, tr, h, wpx, Resampling.nearest)

    scl_i = np.rint(scl).astype(np.int16)
    bad = np.isin(scl_i, (3, 8, 9, 10, 11))
    b04 = np.where(bad, np.nan, b04.astype("float32"))
    b08 = np.where(bad, np.nan, b08.astype("float32"))

    stack = np.stack([b04, b08], axis=0)
    return stack, crs, tr


def write_two_band(path: Path, data: np.ndarray, crs, transform) -> None:
    h, w = data.shape[1], data.shape[2]
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 2,
        "height": h,
        "width": w,
        "crs": crs,
        "transform": transform,
        "compress": "deflate",
        "tiled": True,
        "BIGTIFF": "IF_SAFER",
        "nodata": None,
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data[0], 1)
        dst.write(data[1], 2)
        dst.set_band_description(1, "B04")
        dst.set_band_description(2, "B08")


def main() -> None:
    catalog = pystac_client.Client.open(
        config.STAC_URL,
        modifier=planetary_computer.sign_inplace,
    )

    for period in (config.PERIOD_A, config.PERIOD_B):
        print(f"[*] {period['label']} ({period['start']} … {period['end']}) — bästa scen …")
        data, crs, tr = fetch_single_scene_composite(
            catalog, period["start"], period["end"]
        )
        out = config.DATA_PROCESSED / f"s2_{config.AOI_NAME}_{period['label']}_b04_b08.tif"
        write_two_band(out, data, crs, tr)
        print(f"    Sparad: {out}  CRS={crs}")

    print("[OK] Done. Next: python scripts/compute_ndvi.py")


if __name__ == "__main__":
    main()
