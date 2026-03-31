"""Tvinga PROJ_DATA till venv-pyproj innan rasterio/stackstac laddas (Windows)."""

from __future__ import annotations

import os


def ensure_rasterio_proj() -> None:
    try:
        import pyproj
    except ImportError:
        return
    d = pyproj.datadir.get_data_dir()
    if d and os.path.isdir(d):
        os.environ["PROJ_DATA"] = d
        os.environ["PROJ_LIB"] = d
