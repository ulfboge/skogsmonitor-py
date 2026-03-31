# Skogsmonitor-py — NDVI & ΔNDVI (Fiby, Python / STAC)

> **Visas denna README som din “webbplats” på `*.github.io/skogsmonitor-py`?** Då är GitHub Pages sannolikt satt till mapp **`/` (root)** — då väljer GitHub ofta README som startsida. **Åtgärd:** *Settings → Pages → Deploy from a branch → Branch `main` → Folder **`/docs`*** (spara), eller källa **GitHub Actions**. **Direkt till kartan (Actions eller branch /docs):** […/skogsmonitor-py/](https://ulfboge.github.io/skogsmonitor-py/) — **inte** `…/docs/`; mappen `docs/` i repot blir **webbplatsens rot**, så det finns ingen sökväg `/docs/` på `github.io`.

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

**Karta (publik URL):** […/skogsmonitor-py/](https://ulfboge.github.io/skogsmonitor-py/) — samma innehåll som lokala `docs/index.html`, men på `github.io` ligger filerna i **roten** av repots webbplats (`cogs/` inte `docs/cogs/`). Adressen **`…/skogsmonitor-py/docs/`** ger därför ofta **404 på COG** och en **tom karta** om sidan ändå laddas (t.ex. gammal länk).

Om rot-URL:en visar README har du troligen **Deploy from a branch** med mapp **`/` (root)**. Rot-`index.html` omdirigerar **endast på localhost** till `docs/`; på `*.github.io` sker ingen auto-redirect (så du inte skickas till en död `/docs/`-URL). `.nojekyll` stänger av Jekyll som annars kan visa `README.md` som startsida.

1. **Rekommenderat:** **Settings → Pages → Source → GitHub Actions** (workflow `deploy-pages.yml` laddar upp mappen `docs/` som **hela webbplatsen** — kartan blir `https://<user>.github.io/<repo>/`).
2. **Alternativ med branch:** välj branch **`main`** och mapp **`/docs`** (inte root) — samma URL-mönster: **ingen** `/docs/` i webbadressen.
3. Lokalt är **COG** under `docs/cogs/*.tif` **gitignorade**; på Pages kommer de från CI efter lyckad körning.

## Jämfört med GEE-demon

- Här: reproducerbar **Python-pipeline** och **öppen STAC-kedja** (ingen Earth Engine).  
- **Median över många scener** (som i GEE-kompositen) är *inte* implementerat — istället **bästa enkelscen** per fönster (snabbare, enklare, färre beroenden).

## Disclaimer

Pedagogisk / indikativ NDVI-förändring — **inte** operativt skogsinventarium eller rättsligt underlag.
