# BHU LOKA (भूलोक) — Technical, Data, and Operational Feasibility Study (R0 / R0.1)

**Document ID:** `BHU-FEAS-R0`  
**Verification Date:** 2026-11-12  
**Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  

---

## 1. Software-Only Runtime and Environment Feasibility

All checks below reflect the measured local Windows environment (`Python 3.13.7`, `Node v22.11.0`):

| Subsystem | Available Dependencies / Services | Constraints / Blockers | Feasibility Assessment |
| :--- | :--- | :--- | :--- |
| **NASA Earth Observation Public APIs** | Zero-key NASA CMR (`cmr.earthdata.nasa.gov`), NASA GIBS WMTS (`gibs.earthdata.nasa.gov`), NASA LaRC POWER AG (`power.larc.nasa.gov`), USGS/NASA `landsat-c2-l2` STAC | Authenticated Earthdata HDF/HLS GeoTIFF raster pixel downloads require `NASA_EARTHDATA_USER` / `NASA_EARTHDATA_PASS` | **FEASIBLE AND VERIFIED** (all 8 public NASA/Landsat probes returned `HTTP 200 OK`) |
| **Copernicus & Meteorological APIs** | Planetary Computer Sentinel-2 L2A STAC + SAS signing + TiTiler stats, Open-Meteo (ECMWF forecast, soil moisture, ET0, GloFAS, CAMS, GLO-90 DEM), OSM Overpass, PIB/NDMA RSS | `rasterio`, `geopandas`, `shapely`, `pyproj` not installed locally; public Overpass rate-limits (`HTTP 429`) | **FEASIBLE AND VERIFIED** via pure-Python UTM projection, TiTiler zonal stats, and `_wait_overpass_slot()` throttling |
| **Backend Web & FastMCP** | `fastapi`, `uvicorn`, `httpx`, `mcp` (FastMCP), `sqlite3` R-tree, `beautifulsoup4` | Windows sandbox loopback blocks `asyncio.run()` `socketpair` — host runtime executes cleanly | **FEASIBLE AND VERIFIED** |
| **ML & Hybrid RAG** | `numpy`, `scipy`, `pandas`, `scikit-learn`, `torch`, `faiss-cpu`, `sentence-transformers`, `joblib` | `lightgbm` / `shap` not installed; local deterministic RAG synthesis avoids paid LLM lock-in | **FEASIBLE AND VERIFIED** |
| **2D / 3D Browser Rendering** | Bundled `Leaflet 1.9.4`, `Three.js r128`, Electron 33 shell, host `chrome.exe` and `msedge.exe` | Host `Node v22.11.0 < v22.12.0` blocks `chrome-devtools-mcp@1.13.0`; `playwright`/`selenium` absent | **FEASIBLE** (`chrome.exe` headless runtime rendering & screenshot capture works directly) |
| **IoT Hardware & Wearables** | Explicitly excluded from BHU LOKA software scope | None required; out of scope | **OUT OF CURRENT SCOPE** (No hardware, wearables, or firmware developed or purchased) |

---

## 2. Key Technical Risks and Mitigations

1. **Authenticated NASA HDF/HLS Pixel Downloads:** CMR discovery, GIBS WMTS tiles, and NASA LaRC POWER operate with zero login; direct LP DAAC raster downloads read credentials exclusively from environment variables (`NASA_EARTHDATA_USER`, `NASA_EARTHDATA_PASS`).
2. **Public Overpass Rate Limits (`HTTP 429`):** Mitigated via `_wait_overpass_slot()` mutex separation, 30-minute SQLite TTL cache for `LIVE` responses only, and fail-closed `UNAVAILABLE` UI states.
3. **Absence of Heavy C++ GIS Wheels:** Mitigated cleanly using pure-Python Transverse Mercator (`EPSG:4326` -> `UTM EPSG:326xx`) Shoelace geometry and HTTP STAC/TiTiler analytics.
4. **Cadastral / Land Record Restrictions:** Official state DILRMP/RoR portals do not expose open parcel APIs; enforced via composite administrative filters and explicit ownership disclaimers.
