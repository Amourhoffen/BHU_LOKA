# BHU LOKA (भूलोक) — Verified Baseline Report (`R0.1` Verification Snapshot)

**Document ID:** `BHU-VBR-R0` (`R0.1` Updated Verification)  
**Verification Date:** 2026-11-12  
**Team:** Prince Kumar (Project Owner, IIT Patna, `PA2511CDH37`) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  
**Platform Scope:** **Software-Only** Research and Intelligence Platform (`IoT hardware`, `wearables`, `sensor manufacturing`, and `hardware firmware` are explicitly **OUT OF CURRENT SCOPE**)

---

## 1. Executive Summary of Measured Verification (`R0.1`)

Following P0–P5 delivery stabilization, P1 scientific integrity reconciliation, and Precision Agriculture + NASA Earth Observation (`R0.1`) integration:

- **All `45 / 45` backend, ASGI, FastMCP, Spatial ML/RAG, India Location Intelligence, NASA EO, and Precision Agriculture (`R0.1 - R2`) tests pass (`45 passed, 0 failed in 114.06s`)** when executed under host Python `3.13.7`.
- **All live FastAPI (`127.0.0.1:8000`) and static web (`127.0.0.1:8080`) HTTP endpoints return `200 OK`**, including live zero-key calls to **NASA EOSDIS CMR** (`MOD13Q1.061`, `MOD11A2.061`, `HLSL30.020`), **USGS/NASA Landsat C2 L2** (`landsat-c2-l2`), **NASA LaRC POWER AG** (`MERRA-2 + CERES`), **Copernicus Sentinel-2 L2A STAC/TiTiler** (`NDVI`, `NDRE`, `EVI`, `SAVI`, `NDWI`, `GNDVI`, `BSI`, `NIR CV%` zonal uniformity), **Copernicus Sentinel-1 C-SAR RTC** (`S1D_IW_GRDH_1SDV_20261108T122052`, `VV = -7.69 dB`, `VH = -12.69 dB`, `380` valid `10m` polygon pixels), **Open-Meteo ET0/Soil Moisture**, and farm-aware **Hybrid RAG** (`faithfulness = 0.80`).
- **Live runtime bug resolved during HTTP end-to-end verification:** Live smoke probing uncovered an `AttributeError` (`HTTP 500`) in `Pipelines/bhu_loka_agri_engine.py:1182` caused by positional `(lat, lon)` arguments passed to `fetch_location_3d_dem(location_name, lat, lon)`. Fixed via explicit keyword invocation (`location_name=farm["farm_name"], lat=lat, lon=lon`), verified `200 OK`, and followed by full suite + integrity re-runs.
- **Visual UI verification completed via headless Chromium renders (`runtime_3d_dashboard.png` and `runtime_2d_leafmap_agri.png`):** Interactive `chrome-devtools-mcp@1.13.0` automation remains blocked on the host (`Node v22.11.0 < v22.12.0`), so visual layout inspection used headless Chromium `1440x900` captures directly (`#india-intel-main-nav` right-edge clipping caught and fixed so all `8` navigation pills render on one row).

---

## 2. Exact Command Outputs and Measured Metrics (`R0.1`)

### 2.1 Full Pytest Suite (`45 / 45 Passed` in `114.06s`)
Executed across all `4` suite files on host Python `3.13.7`:
```
pytest test_india_location_street_intel.py test_site_studio.py test_rag.py test_agri_engine.py -v
-> 45 passed in 114.06s (0:01:54)
```
1. `test_india_location_street_intel.py` -> **`10 / 10 PASSED`** (`36` States/UTs, GADM vs DILRMP separation, Patna L3=`3`, Ladakh `38`, `12` GIS layers + `429` retry, `8`-category news RSS + `geo_precision_guard`, offline Phase-7 modules `10`–`13`, FastAPI ASGI).
2. `test_site_studio.py` -> **`7 / 7 PASSED`** (WGS84->UTM zones, NOAA solar ephemeris, Brode UTCI + Tmrt, Marching Squares contours, DXF/SVG/GLB/OBJ/GeoJSON exports, fail-closed offline checks, FastAPI + `11` FastMCP tools).
3. `test_rag.py` -> **`20 / 20 PASSED`** (`all-MiniLM-L6-v2` `384-d` Transformer + FAISS + BM25 RRF, multilingual EN/HI/Hinglish routing, Agent-2 spotlight/hologram actions, RAGAS faithfulness + guardrails, FastAPI + MCP `11`-tool check). Note: running inside Windows sandbox blocks read access to external `HF_HOME` (`C:\Users\ljpri\.cache\huggingface`), so host runtime execution verifies Transformer readiness.
4. `test_agri_engine.py` -> **`8 / 8 PASSED`** (UTM area/validation, CRUD + multi-plot + RFC 7946 GeoJSON export, Sentinel-2 L2A indices + `GNDVI`/`BSI`/`NIR CV%` zonal dispersion + 2-date delta + offline `EMPTY`/`UNAVAILABLE`, Sentinel-1 C-SAR `RTC` `VV`/`VH` dB crop wetness + SQLite cache + radar ambiguity disclosure, NASA CMR `MOD13Q1`/`MOD11A2`/`HLSL30` + Landsat C2 L2 discovery, NASA LaRC POWER `-999` fill sentinel filtering + Open-Meteo ET0/drainage + FAO-56 $K_c$ / $ET_c$ volumetric deficit, India Soil Health Card ICAR CSV/KV/JSON parser + SQLite reports + range validation, farm-aware Hybrid RAG + ASGI routes including `/sar-wetness`, `/fao56-etc`, `/soil-health`).

### 2.2 Live Daemon HTTP & Live NASA EO / Copernicus Probes (`127.0.0.1:8000`)
Started `uvicorn main:app --host 127.0.0.1 --port 8000` (`32` registered OpenAPI paths / `36` total ASGI routes) and `python -m http.server 8080`:
- `GET /health` -> **`200 OK`** (`24` indexed documents, `HEALTHY`)
- `POST /api/v1/agri/farms` (Patna/Bihta box) -> **`200 OK`** (`4.4548 ha`, `11.0079 acres`, `EPSG:32645`)
- `GET /api/v1/agri/farms/{farm_id}/water-soil` -> **`200 OK`** (Open-Meteo `LIVE`, `et0_7d_mm = 20.9`, `water_balance_7d_mm = -20.9`; NASA LaRC POWER AG `LIVE`, `gwetroot = 0.62`, `solar_irradiance_mean_mj_m2_day = 14.96`)
- `GET /api/v1/agri/farms/{farm_id}/nasa-eo` -> **`200 OK` (`status: LIVE`)**:
  - `MOD13Q1.061` (`LIVE`, latest `2026-10-16T00:00:00.000Z`, `2` hits)
  - `MOD11A2.061` (`LIVE`, latest `2026-11-01T00:00:00.000Z`, `2` hits)
  - `HLSL30.020` (`LIVE`, latest `2026-10-21T04:48:45.443Z`, `2` hits)
  - `landsat-c2-l2` (`LIVE`, latest `2026-10-21T04:48:45.443774Z`, `2` hits)
- `GET /api/v1/agri/farms/{farm_id}/satellite` -> **`200 OK` (`status: LIVE`, `5` scenes)**: latest Sentinel-2 L2A indices (`NDVI = 0.351`, `NDRE = 0.2315`, `EVI = 0.3458`, `SAVI = 0.2708`, `NDWI_Gao = 0.0534`, `NDWI_McFeeters = -0.3482`)
- `POST /api/v1/query` (`agri_context`) -> **`200 OK`** (`faithfulness = 0.8`, `3` grounded sources)
- `DELETE /api/v1/agri/farms/{farm_id}` -> **`200 OK`** (test farm cleaned from production SQLite; `0` synthetic farms retained)

### 2.3 SQLite & Index Consistency Scan (`Data/01_Boundaries/bhu_loka_india_intel.sqlite`)
- `states_uts`: `36` total (`28` States + `8` Union Territories).
- `admin_units`: `36` L1, `724` L2 districts, `2,180` verified L3 subdivisions (`98` `'n.a.'` placeholders retained deactivated at `verified_flag=0`).
- Patna verified GADM L3 count: `3` (`Barh`, `Danapur`, `Masaurhi`). Ladakh (`38`) L3 count: `0` (explicit availability disclosure).
- Residual `'Anudal'` strings across all `38` SQLite tables/columns: `0`.
- Cached mock rows in `osm_spatial_cache` and `agri_satellite_cache`: `0`.

### 2.4 JavaScript Syntax, CDP Viewport & Theater/Fullscreen Verification & Integrity Checks
- `node --check` PASS (exit `0`) across `Assets/vendor/bhu_loka_agri.js`, `Assets/vendor/bhu_loka_india_intel.js`, `Assets/vendor/bhu_loka_location_engine.js`, `Data/08_Processed_Outputs/bhu_loka_india_admin_index.js`, inline `<script>` blocks extracted from `bhu_loka_cyber_dashboard.html` and `bhu_loka_leafmap_interactive.html`, and `BhuLoka_Chromium_App/preload.js`.
- **CDP Layout, Theater Mode & Fullscreen Verification (`chrome.exe --headless=new` + `websocket` CDP):**
  - Desktop `1422x748` before vs after 6 chat submissions + Mumbai search + layer checkboxes: `docScrollH` remains strictly `748 === winH` (`scrollY = 0`), WebGL canvas stays locked at `674x241` (`0px` vertical stretch), while `#chat-feed` scrolls internally (`chatScrollH = 2453`, `chatClientH = 245`).
  - **3D Theater Mode (`#btn-map-theater`) & Browser Fullscreen (`#btn-map-fullscreen`):** Expands `#center-stage` (`1406x548`) / WebGL canvas (`1382x409`) cleanly, preserves camera & target location, adapts dynamically at `1200x760` (`webglW: 1160, webglH: 421`), enters `#viewport-panel` fullscreen + exits cleanly on `ESC`, and restores normal 3-column workstation cleanly (`CONSOLE_ERRORS: []`).
  - **Mobile Responsive (`390x844`) & 2D Parity:** Places 3D map viewport first (`canvasWrapH = 238`), collapses left/right rails into `LAYERS` / `AI CHAT` drawers, and verifies `bhu_loka_leafmap_interactive.html` (`mapW: 1422, mapH: 658`, `EXPAND`/`FULLSCREEN` controls, `hasLeaflet: true`, zero scroll jump).
- `check_integrity.py --strict` across code, docs, tests, and dashboards: **`S0: 0 | S1: 0 | S2: 0` (PASS)**.

---

## 3. Capability Verification Matrix (Strict `R0.1` Status Tags)

| Capability | Verification Basis | Status Tag |
| :--- | :--- | :--- |
| FastAPI (`32` OpenAPI Paths / `36` ASGI Routes) & `11` FastMCP Tools | Full `43/43` pytest run + live `uvicorn` `/openapi.json` & HTTP probes | `IMPLEMENTED AND VERIFIED` |
| India Admin Explorer (Module A) & DILRMP Plot Search (Module B) | Pytest + SQLite schema scan (`36` States/UTs, Patna `3` GADM L3) | `IMPLEMENTED AND VERIFIED` |
| Police, CCTV, News, Roads, Hospitals, Traffic/EMS (Modules C–F, 10–13) | Pytest + Overpass `429` retry + live `/location-intelligence` | `IMPLEMENTED AND VERIFIED` |
| Site Studio Solar/UTCI + CAD/3D Export (`/api/v1/site-analysis`, `/export-site`) | Pytest GLB/DXF/SVG/OBJ/GeoJSON header checks + HTTP `200` | `IMPLEMENTED AND VERIFIED` |
| Precision Agriculture (`R0.1 - R2`: Polygons, UTM, GeoJSON, S2 STAC + Zonal `GNDVI`/`BSI`/`CV%`, S1 SAR `RTC`, FAO-56 $ET_c$, ICAR Soil Health CSV/JSON, Scouting, RAG) | Pytest (`8/8`) + live HTTP CRUD/STAC/TiTiler S1/S2/Open-Meteo/RAG `200 OK` | `IMPLEMENTED AND VERIFIED` |
| NASA Earth Observation Stack (`MOD13Q1`, `MOD11A2`, `HLSL30`, `Landsat`, `POWER`, `GIBS`) | Pytest + live CMR/POWER/Landsat `200 OK` + GIBS WMTS Leaflet overlays | `IMPLEMENTED AND VERIFIED` |
| Hybrid RAG + RAGAS Faithfulness + Guardrails (`/api/v1/query`) | Pytest `20/20` (`384-d` Transformer) + live farm RAG `faithfulness=0.80` | `IMPLEMENTED AND VERIFIED` |
| Empirical Patna Hazard Experiments (`Exp_01`–`Exp_04`) & SBCV Random Forest | Saved JSON metrics + verified `train_spatial_model.py` + P1 docs | `IMPLEMENTED AND VERIFIED` |
| 3D WebGL & 2D Leaflet Visual Runtime, Theater Mode & Fullscreen | CDP desktop (`1422x748`, `1200x760`), Fullscreen + `ESC`, & mobile (`390x844`) verified | `IMPLEMENTED AND VERIFIED` |
| Interactive `chrome-devtools-mcp` Browser Automation Session | Blocked by host `Node v22.11.0 < v22.12.0` (`chrome-devtools-mcp@1.13.0`); bypassed via Python CDP verification script | `IMPLEMENTED BUT UNVERIFIED` |
| Electron Desktop Shell IPC Execution (`BhuLoka_Chromium_App/main.js`) | `preload.js` syntax checked; `node_modules`/`electron` runtime not installed locally | `PARTIALLY IMPLEMENTED` |
| Live Google Earth Engine Cloud Execution (`/api/v1/gee-status`) | Connector/script implemented; `EE_PROJECT` credentials unconfigured locally | `PARTIALLY IMPLEMENTED` |
| Agriculture R1 (`GNDVI`, `BSI`, `NIR CV%`, Sentinel-1 C-SAR `RTC`) & R2 (`FAO-56 ETc`, ICAR Soil Health Card parser) | Implemented, tested (`45/45` pytest), and live Planetary Computer S1 RTC probed | `IMPLEMENTED AND VERIFIED` |
| Step 4 UI/UX Craft Pass (`R0.2`: dark hairline tokens, `min 10px` floor, `:focus-visible`, 2D/3D collision fixes) | Verified in headless Chromium CDP (`1422x748`, `0` console/page errors, `scrollY=0`) | `IMPLEMENTED AND VERIFIED` |
| Agriculture R2/R3 DILRMP Cadastral Advisory Cross-Link (`/cadastral-advisory`) & Multi-Plot Holding Cluster Summary (`/portfolio-summary`) | Implemented (`resolve_farm_cadastral_advisory`, `compute_multiplot_summary`, Hybrid RAG, Tab 1 UI) & verified across full test suite | `IMPLEMENTED AND VERIFIED` |
| Software Multi-Season Yield Analytics & Mandi Price Feeds | Implemented (`compute_farm_aiag_business_intelligence`, `get_crop_demand_advisory`, `get_safe_investment_zones`, Mandi radar, PMFBY insurance) + tested (`10/10` in `test_agri_engine.py`) | `IMPLEMENTED AND VERIFIED` |
| GeoAI Crop Growth & Canopy Vegetative Zonation Monitoring | Implemented (`get_crop_growth_monitoring`, 3-tier zonation: Open Soil, Low Vigor, Ideal Vigor + 7-day Sentinel-2 trajectory) + tested (`test_agribusiness_aiag_and_crop_growth_monitoring`) | `IMPLEMENTED AND VERIFIED` |
| Physical IoT Hardware, Wearables & Sensor Firmware (`BHU SENSE`) | Hardware/IoT/wearable manufacturing excluded from software scope | `OUT OF CURRENT SCOPE` |
