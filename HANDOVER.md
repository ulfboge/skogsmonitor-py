# Handover / arbetslogg — skogsmonitor-py

*Senast uppdaterad: 2026-03-31*

Kort logg så att någon kan ta över utan att läsa hela chatthistoriken.

## Kontext

- **Repo:** [github.com/ulfboge/skogsmonitor-py](https://github.com/ulfboge/skogsmonitor-py)
- **Syfte:** NDVI / ΔNDVI för fast AOI (Fiby), Python-pipeline (STAC → raster → COG), minimal **OpenLayers**-karta i `docs/`.
- **CI:** `.github/workflows/deploy-pages.yml` bygger rastren på Ubuntu, laddar upp **`docs/` som hela GitHub Pages-artefakten** (innehållet i `docs/` blir **webbplatsrot**, inte under `/docs/` i URL:en).

## Publik URL (viktigt)

| Rätt | Fel / missförstånd |
|------|---------------------|
| `https://ulfboge.github.io/skogsmonitor-py/` | `…/skogsmonitor-py/docs/` → **404** eller trasiga COG-sökvägar mot `/docs/cogs/` |

- På **Actions**-deploy finns **ingen** motsvarighet till URL-segmentet `docs/` — filer som i repot ligger i `docs/` serveras som **`/`**, **`/index.html`**, **`/cogs/*.tif`**, osv.
- **`docs/cogs/*.tif`** är **gitignorade**; COG:er på Pages kommer **endast** från lyckad workflow-körning.

## Vad som gjorts (kronologiskt i grova drag)

1. **Pages / CI** — `upload-pages-artifact@v4`, rätt `permissions` (`pages`, `id-token`, `actions: read`), verifiering `docs/index.html` + `docs/cogs/`.
2. **Tom karta / fel URL** — Förklaring i README: skillnad mellan repo-mapp `docs/` och publicerad URL; länkar korrigerade till **repo-rot** på `github.io`.
3. **Rot-`index.html`** — Tidigare **meta refresh** till `docs/` skickade besökare till **404** på Pages. Nu: **auto-redirect endast på `localhost` / `127.0.0.1`**; på `github.io` statisk förklaring + dynamisk länk till sidrot.
4. **`docs/index.html` (karta)**  
   - Vy från **`GeoTIFF.getView()`** efter laddning.  
   - **COG-URL:er** via `new URL(..., document.baseURI)` (stabilare än enbart `import.meta.url` för inline-modul).  
   - **Race-guard** (`layerEpoch`) vid snabba lagerbyten.  
   - Feltext + ev. hint om COG **HEAD** misslyckas (inkl. tips om rot-URL om sökväg innehåller `/docs`).
5. **Grå karta trots rätt URL** — `getView()` sätter vy i **COG:ens CRS** (t.ex. EPSG:32633 / 3006). OSM ligger i **EPSG:3857**. Utan **proj4 + `register()`** saknas transform → baslager syns inte. **Åtgärd:** `proj4` (jsDelivr `+esm`), definitioner för **3857, 4326, 32633, 3006**, `import { register } from 'ol/proj/proj4.js'` **innan** `Map` skapas. Dessutom **`map.updateSize()`** vid load/resize/`ResizeObserver` + `min-height` på `#map`.
6. **README** — Tabell för Pages-scenarier (Actions vs branch `/docs` vs branch rot), callout om README som “webbplats”, exempellänk.

## Senaste commits (referens)

```text
d5172f1 fix(map): register proj4 …
556a7e5 docs: clarify Actions Pages URL …
abfcbd8 fix: no meta refresh to docs/ on GitHub Pages …
d3e5448 docs: clarify Pages URL …
… (äldre: OpenLayers getView, CI Pages, initial pipeline)
```

Kör `git log --oneline -20` för full lista.

## Att kolla i morgon

- [ ] **Actions** grön efter senaste push; hårdladda kartan (ev. cache-buster).
- [ ] **Webbläsarkonsol** om något fortfarande är grått: nätverk (COG 404), **proj4**-laddning från CDN, WebGL-varningar.
- [ ] Om COG plötsligt är i **annan EPSG** än 32633/3006: lägg till motsvarande `proj4.defs(...)` i `docs/index.html` (eller läs EPSG från metadata/`layers.json` i framtiden).

## Lokalt

```powershell
cd docs
python -m http.server 8765
```

Öppna `http://localhost:8765/`. Pipeline från repo-rot: `python scripts/download_s2.py` → `compute_ndvi.py` → `export_cog.py` (se README).

## Relaterade filer

| Fil | Roll |
|-----|------|
| `docs/index.html` | Karta (OpenLayers, proj4, GeoTIFF, OSM) |
| `index.html` (rot) | Endast relevant vid Pages från **repo-rot**; annars oftast inte med i Actions-artefakt |
| `README.md` | Pages-förklaring, pipeline, felsökning |
| `.github/workflows/deploy-pages.yml` | Build + deploy |
| `scripts/export_cog.py` | COG → `docs/cogs/`, `layers.json` |
