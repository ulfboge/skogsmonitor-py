"""
Steg 2: Beräkna NDVI per period och ΔNDVI (B − A).
Om perioderna har olika rastergrid (olika S2-scener) reprojiceras B till A med reproject_match.

Kör:
  python scripts/compute_ndvi.py
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
import rioxarray
import xarray as xr

import config


def read_red_nir(path: Path) -> tuple[xr.DataArray, xr.DataArray]:
    da = rioxarray.open_rasterio(path)
    if da.sizes.get("band", 0) < 2:
        raise ValueError(f"Förväntar minst 2 band (B04,B08) i {path}")
    red = da.sel(band=1)
    nir = da.sel(band=2)
    return red, nir


def ndvi(red: xr.DataArray, nir: xr.DataArray) -> xr.DataArray:
    red = red.astype("float32")
    nir = nir.astype("float32")
    num = nir - red
    den = nir + red
    out = xr.where(den > 1e-6, num / den, np.nan)
    return out.rio.write_crs(red.rio.crs, inplace=False)


def main() -> None:
    pa = config.DATA_PROCESSED / f"s2_{config.AOI_NAME}_{config.PERIOD_A['label']}_b04_b08.tif"
    pb = config.DATA_PROCESSED / f"s2_{config.AOI_NAME}_{config.PERIOD_B['label']}_b04_b08.tif"
    for p in (pa, pb):
        if not p.exists():
            raise FileNotFoundError(f"Saknar {p} — kör först: python scripts/download_s2.py")

    red_a, nir_a = read_red_nir(pa)
    red_b, nir_b = read_red_nir(pb)

    ndvi_a = ndvi(red_a, nir_a)
    ndvi_b_raw = ndvi(red_b, nir_b)
    ndvi_b = ndvi_b_raw.rio.reproject_match(ndvi_a)

    delta = (ndvi_b - ndvi_a).rio.write_crs(ndvi_a.rio.crs, inplace=False)
    delta = delta.rename("ndvi_delta")

    for _da in (ndvi_a, ndvi_b, delta):
        _da.attrs.clear()

    out_a = config.OUTPUT_RASTERS / f"ndvi_{config.AOI_NAME}_{config.PERIOD_A['label']}.tif"
    out_b = config.OUTPUT_RASTERS / f"ndvi_{config.AOI_NAME}_{config.PERIOD_B['label']}.tif"
    out_d = (
        config.OUTPUT_RASTERS
        / f"ndvi_delta_{config.AOI_NAME}_{config.PERIOD_B['label']}_minus_{config.PERIOD_A['label']}.tif"
    )

    ndvi_a.rio.to_raster(out_a, compress="deflate", tiled=True)
    ndvi_b.rio.to_raster(out_b, compress="deflate", tiled=True)
    delta.rio.to_raster(out_d, compress="deflate", tiled=True)

    print(f"[OK] {out_a}")
    print(f"[OK] {out_b}")
    print(f"[OK] {out_d}")
    print("[OK] Done. Next: python scripts/export_cog.py")


if __name__ == "__main__":
    main()
