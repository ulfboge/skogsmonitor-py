# Skogsmonitor-py — NDVI & ΔNDVI (Fiby, Python / STAC)

Fast AOI (**Fiby urskog**, samma WGS84-bbox som i NVI-repot) och **två sommarfönster** i `config.py`. Tre steg i samma anda som NVI:

```text
python scripts/download_s2.py
python scripts/compute_ndvi.py
python scripts/export_cog.py
```

## Vad skripten gör

1. **`download_s2.py`** — Hittar Sentinel-2 L2A via **STAC** (Microsoft Planetary Computer, signerade URL:er = samma **Copernicus**-produkt som i GEE). Per period väljs **en scen med lägst molntäckning** som täcker AOI. B04/B08/SCL läses och **SCL-resampling** till B04-rastret (10 m) sker med `reproject`. Utdata lagras i **scenens CRS** (för Sverige oftast **WGS 84 / UTM 33N**).
2. **`compute_ndvi.py`** — NDVI per period; period B **reprojiceras till A:s grid** (`reproject_match`) innan **ΔNDVI** beräknas.
3. **`export_cog.py`** — Skriver **COG** (eller GeoTIFF + översikter om COG-driver saknas) till `outputs/cogs/` och kopierar till `docs/cogs/` för kartan. Skapar `docs/cogs/layers.json` och `delta_bounds_wgs84.json`.

## Kart-sida

```powershell
cd docs
python -m http.server 8765
```

Öppna `http://localhost:8765/`. Byt lager (ΔNDVI / NDVI A / NDVI B) och opacitet i panelen.

## Miljö

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

Kör skript med `.\.venv\Scripts\python ...`.

## PROJ / GDAL på Windows

Om du ser varningar om `proj.db` / `DATABASE.LAYOUT.VERSION` kommer de ofta från **olika PROJ-versioner** mellan GDAL (rasterio-wheel) och pyproj. Skripten använder **PROJ4-sträng för WGS84** i stället för `EPSG:4326` där det behövs för att minska uppslagningar. För en helt ren miljö: installera **conda-forge** (`conda install -c conda-forge rasterio pyproj`) eller uppdatera pyproj/PROJ-data tills rasterio och pyproj matchar.

## GitHub Pages

1. **Settings → Pages → Build and deployment**: källa **GitHub Actions** (workflow `deploy-pages.yml` bygger S2/NDVI/COG på Ubuntu och laddar upp `docs/`).
2. Första gången kan du behöva godkänna **github-pages**-miljön under **Actions**.
3. Lokalt är **COG** under `docs/cogs/*.tif` **gitignorade**; på Pages kommer de från CI efter lyckad körning.

## Jämfört med GEE-demon

- Här: reproducerbar **Python-pipeline** och **öppen STAC-kedja** (ingen Earth Engine).  
- **Median över många scener** (som i GEE-kompositen) är *inte* implementerat — istället **bästa enkelscen** per fönster (snabbare, enklare, färre beroenden).

## Disclaimer

Pedagogisk / indikativ NDVI-förändring — **inte** operativt skogsinventarium eller rättsligt underlag.
