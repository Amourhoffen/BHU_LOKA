# BHU LOKA (भूलोक) — Project Presentation & Technical Defense Deck (`R0.1`)

**Document ID:** `BHU-DECK-R0.1`  
**Verification Date:** 2026-11-12  
**Affiliation:** Department of Computer Science & Engineering, Indian Institute of Technology Patna  
**Project Status:** Verified Stabilization + Precision Agriculture & NASA EO Vertical Slice (`43/43` Backend/ASGI/MCP Tests Passing)

---

## Slide 1 — Vision, Official Team & Software-Only Scope

### Vision Statement
BHU LOKA (भूलोक) is a sovereign, audit-first geospatial AI and Earth observation software platform engineered to link satellite physics, terrain micro-topography, administrative location hierarchies, disaster situational awareness, and farm-scale agricultural decision intelligence under reproducible provenance rules.

```
EARTH -> SATELLITE (NASA EO + LANDSAT + COPERNICUS) -> GIS -> CLIMATE -> SOIL -> WATER -> AGRICULTURE -> DECISION SUPPORT
```

### Official Project Team
| Member | Role | Affiliation / Record |
| :--- | :--- | :--- |
| **Prince Kumar** | Project Owner & Lead Developer | IIT Patna (`PA2511CDH37`) |
| **Pallav Rustogi** | Project Supervisor | Faculty / Research Supervisor |
| **Payal Priyadarshini** | UI/UX Designer | IIITDM Jabalpur (1st Semester) |

### Critical Scope Clarification (Software-Only Platform)
BHU LOKA is strictly a **software-only** scientific research and intelligence platform spanning web interfaces (`2D` Leaflet, `3D` Three.js, Chromium wrapper), Python backend APIs (`FastAPI`, `FastMCP`), spatial SQLite indexing, Earth observation processing pipelines, scientific analytics, and grounded Hybrid RAG agents.

**Explicitly OUT OF CURRENT SCOPE:**
- IoT field hardware, wearable devices, sensor manufacturing, physical monitoring deployments, and embedded firmware (`BHU_SENSE_IoT_Specification.md` is retained strictly as an unimplemented future concept).

---

## Slide 2 — Priority NASA Earth Observation & Multi-Sensor Science Stack

BHU LOKA prioritizes authentic NASA Earth observation data and public distribution services, complemented by USGS/NASA Landsat Collection 2 Level-2 and Copernicus Sentinel-1/Sentinel-2. Every active layer and API response exposes full provenance metadata:

| Dataset / Product | Provider & Product ID | Acquisition Date | Spatial & Temporal Resolution | CRS | Licence & Usage | Processing Methodology | Quality & Missing Data | Attribution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MODIS Terra Daily LST (Empirical Patna)** | NASA LP DAAC `MOD11A1.061` | `2019-04-01` to `2019-06-30` (`91` scenes) | `1 km`, Daily (`10:30` AM local pass) | Sinusoidal (`SR-ORG:6974`) reprojected `EPSG:32645` / `EPSG:4326` | NASA EOSDIS Open Data | Split-window clear-sky QC filtering & urban/rural land-cover stratification | `61` clear-sky composites retained; `30` cloud-masked days excluded | NASA EOSDIS / LP DAAC (`MOD11A1.061`) |
| **MODIS Terra 16-Day NDVI/EVI Discovery** | NASA LP DAAC `MOD13Q1.061` | Dynamic CMR query (`16-Day MVC`, live verified `2026-10-16`) | `250 m`, 16-Day Composite | Sinusoidal (`SR-ORG:6974`) | NASA EOSDIS Open Data | Bidirectional reflectance NDVI/EVI Maximum Value Composite (`VI_Quality`) | Coarse `250 m` pixel; requires `10-30 m` optical bands for smallholder plots | NASA EOSDIS CMR (`cmr.earthdata.nasa.gov`) |
| **MODIS Terra 8-Day LST Discovery** | NASA LP DAAC `MOD11A2.061` | Dynamic CMR query (`8-Day`, live verified `2026-11-01`) | `1 km`, 8-Day Composite | Sinusoidal (`SR-ORG:6974`) | NASA EOSDIS Open Data | 8-day clear-sky daytime/nighttime Thermal IR bands 31/32 | Cloud-contaminated days omitted per compositing window | NASA EOSDIS CMR (`MOD11A2.061`) |
| **Harmonized Landsat Sentinel-2** | NASA LP DAAC / USGS `HLSL30.020` | Dynamic CMR query (live verified `2026-10-21`) | `30 m`, 2–4 Day combined HLS revisit | WGS84 / UTM | NASA Earthdata Open Policy | Nadir BRDF-adjusted surface reflectance + Fmask cloud/shadow QA | Granule discovery is zero-key public; HDF pixel download requires Earthdata auth | NASA LP DAAC / USGS (`HLSL30.020`) |
| **NASA GIBS / Worldview WMTS Overlays** | NASA EOSDIS GIBS (`MODIS_Terra_CorrectedReflectance_TrueColor`, `Land_Surface_Temp_Day`, `NDVI_8Day`) | Lagged UTC rolling (`T-3d` / `T-10d`) | `250 m` (TrueColor/NDVI), `1 km` (LST); Daily/8-Day | `EPSG:3857` Web Mercator | NASA GIBS Free & Public Tile Usage | Server-rendered WMTS KVP imagery overlays (visual inspection layer) | Swath gaps / polar winter missing strips left transparent | NASA EOSDIS Worldview / GIBS |
| **NASA LaRC POWER Agro-Climatology** | NASA LaRC POWER (`MERRA-2` + `CERES SYN1deg`, AG) | Live rolling 7-day window (`2-4d` latency) | `0.5 deg x 0.625 deg`, Daily | `EPSG:4326` | NASA Open Data | Assimilated `T2M_MAX/MIN`, `PRECTOTCORR`, `ALLSKY_SFC_SW_DWN`, `GWETROOT` | Explicit `-999` fill sentinels filtered before aggregation | NASA LaRC POWER Project (`power.larc.nasa.gov`) |
| **Landsat Collection 2 Level-2** | USGS / NASA `landsat-c2-l2` (via Planetary Computer STAC) | Live STAC query (`eo:cloud_cover <= 50%`, verified `2026-10-21`) | `30 m` Optical / `100 m` Thermal | WGS84 / UTM | USGS/NASA Public Domain | LaSRC Surface Reflectance + ST with `QA_PIXEL` masking | Cloud-filtered scene discovery; offline returns `UNAVAILABLE` | USGS / NASA Landsat via Planetary Computer |
| **Copernicus Sentinel-2 L2A & Sentinel-1 SAR** | ESA Copernicus (`sentinel-2-l2a` STAC/TiTiler; local `S1A/S1B` GRDH) | Live S2 scenes (`5` scenes) + Patna `2019-09-23` / `2019-09-29` | `10 m - 20 m` S2; `10 m` VV S1 GRDH | `EPSG:32645` / `EPSG:4326` | Copernicus Open Access | SCL cloud-mask statistics for NDVI/NDRE/EVI/SAVI/NDWI; bimodal SAR floor detection | Local S1 scenes are `VV`-only (`VH` not downloaded); S2 offline returns `EMPTY`/`UNAVAILABLE` | ESA Copernicus / Microsoft Planetary Computer |

*Disclosure: BHU LOKA accesses public NASA EOSDIS/LP DAAC/LaRC interfaces strictly as an open data consumer. No NASA partnership, certification, or institutional endorsement is claimed.*

---

## Slide 3 — Verified Empirical Patna Research (`Exp_01`–`Exp_04` & Spatial ML)

| Experiment | Verified Source Artifact | Measured Results | Scientific Boundary / Limitation |
| :--- | :--- | :--- | :--- |
| **Exp 01: Bimodal SAR Urban Flood Physics** | `exp01_results.json`, `unspider_vs_bhu_loka_benchmark.json` | Patna MC (`133.87 km^2`): BHU LOKA bimodal detection identifies **`99.60 km^2` (`74.40%`)** vs conventional UN-SPIDER specular-only **`4.01 km^2` (`2.99%`)**, exposing **`95.98%` urban omission error**. `exp01_results.json` breaks down `0.07 km^2` specular + `99.52 km^2` double-bounce (`94.08 km^2` + `1.15 km^2` under secondary comparison mask). | Local scenes (`S1A_20190923`, `S1B_20190929`) contain `VV` co-polarization only. |
| **Exp 02: Copernicus GLO-30 DEM Topographic Sinks** | `exp02_results.json` | Frame `142.48 km^2`, mean elevation `53.99 m`, mean slope `2.31 deg`, flat fraction `<1 deg`: `25.24%`. Closed topographic sinks behind embankments: **`47.24 km^2` (`33.15%`)**. | Sinks sit at `44.5-46.8 m` against `53.0-55.0 m` Ganges levees, driving gravity outfall lock during river peaks. |
| **Exp 03: NASA Terra MODIS Daytime LST** | `exp03_results.json` (`MOD11A1.061`) | `61` clear-sky scenes (`91` overpasses, Apr–Jun 2019): mean urban LST `37.29 C`, rural LST `38.32 C`, daytime delta **`-1.03 C`**; peak urban pixel `46.25 C` (`45.32 C` spatial mean DOY `139`). | 10:30 AM daytime Terra pass reflects harvested dry fallow rural soils heating faster than vegetated urban corridors; nocturnal heat island requires night passes. |
| **Exp 04: Compound Population Exposure & ULSI** | `exp04_results.json` | WorldPop 2020 core `214,281`: **`167,246`** flood-exposed, `60,790` in closed sinks, **`49,380`** in compound flood-and-sink hazard. Mean ULSI score: **`52.27`** (`S1: 20.1%`, `S2: 27.7%`, `S3: 33.1%`, `S4: 19.1%`). | ULSI is a planning screening composite, not a substitute for site geotechnical testing. |
| **Spatial Block Cross-Validation (RF)** | `spatial_cv_metrics.json` | `N = 60,000` across `5` contiguous longitudinal strips (`RandomForestClassifier`, `100` trees, `max_depth=12`): mean **ROC-AUC `0.7498 +/- 0.0497`** (`F1: 0.6530`, Accuracy: `68.88%`, Brier: `0.2003`). | Under precomputed `patna_2019_delta_sigma0.npy`, `train_spatial_model.py` constructs `SAR_Pre_dB` as `-12.0 dB` constant (`0.00%` Gini importance; `SAR_Post_dB = 0.3676`, `Delta_Sigma0 = 0.2993`). |

---

## Slide 4 — System Architecture (`2D` / `3D` / FastAPI / FastMCP / SQLite)

| Tier | Implementation Entrypoint | Verified Technical Capabilities |
| :--- | :--- | :--- |
| **2D GIS Workbench** | `bhu_loka_leafmap_interactive.html` + `Assets/vendor/bhu_loka_*.js` | Leaflet `1.9.4`, 3 opt-in NASA GIBS Worldview WMTS overlays, `INDIA LOCATION & STREET INTELLIGENCE` drawer, `AGRICULTURE INTELLIGENCE` panel + polygon vertex tool, live Location Intelligence HUD. |
| **3D Sovereign HUD** | `bhu_loka_cyber_dashboard.html` | Three.js `r128` 3D Earth hologram, Copernicus GLO-90 relief visualizer, Dual-Agent RAG console, `INDIA LOCATION & STREET INTELLIGENCE` explorer, sibling link (`?openAgri=1`) to 2D Agriculture Intelligence. |
| **FastAPI Backend (`127.0.0.1:8000`)** | `Models/04_Hybrid_RAG/enterprise_rag_app/main.py` | **`32` OpenAPI paths (`36` total ASGI routes)** spanning `/health`, `/api/v1/query`, `/api/v1/location-intelligence`, `/api/v1/site-analysis`, `/api/v1/export-site` (`DXF`/`SVG`/`GLB`/`OBJ`/`GeoJSON`), `/api/v1/india/...`, and `/api/v1/agri/...`. |
| **FastMCP Server (`127.0.0.1:8001`)** | `Pipelines/bhu_loka_mcp_server.py` | **`11` registered MCP tools** exposing 15-module location intelligence, India hierarchy search, land portals, Site Studio CAD/thermal checks, DEM relief, and RAG query. |
| **Spatial SQLite Store** | `Data/01_Boundaries/bhu_loka_india_intel.sqlite` | Normalized relational schema + R-tree spatial index (`idx_admin_rtree`) + normalized farm/plot/scouting/satellite cache tables (`bhu_loka_agri_engine.py`). |
| **Electron Desktop Shell** | `BhuLoka_Chromium_App/main.js` | **Status: `PARTIALLY IMPLEMENTED`** (desktop launcher wrapper present; untested in automated suite). |

---

## Slide 5 — India Location & Street Intelligence (Modules A–F)

- **Full All-India Baseline (`28` States + `8` Union Territories = `36`):**
  - `724` District-level (`L2`) rows and `2,180` verified Subdivision/Tehsil/Taluk/Anchal (`L3`) rows in SQLite (`98` GADM `'n.a.'` rows retained inactive at `verified_flag=0`).
  - `43` searchable capital cities & major settlements; state-varying hierarchy labels preserved (no fabricated Patna L3 subdivisions — Patna verified GADM L3 = `3`: `Barh`, `Danapur`, `Masaurhi`; Ladakh `38` verified L3 = `0` with explicit availability disclosure).
- **Separate Data Governance (GADM vs DILRMP Revenue Data):**
  - **Module A (Admin Explorer):** Cascading dropdowns, ranked multilingual autocomplete, point-in-polygon + R-tree lookup (`in_india` guard), breadcrumb trails.
  - **Module B (Land Parcel & Plot Search):** Composite scope enforcement (`State + District + Circle + Mauza + Khata/Khesra/Plot/ULPIN`) paired with `36` official state/UT DILRMP RoR & Bhu-Naksha portals (`0` fabricated plot rows).
  - **Modules C–F (Police, CCTV, News, Traffic & Emergency):** Overpass `HTTP 429/503` backoff (`_OVERPASS_LOCK` concurrency-safe slot spacing), never fabricates Thiessen police boundaries, separates verified PIB EN/HI + NDMA CAP RSS across `8` thematic news categories with `geo_precision_guard`, and marks errors `UNAVAILABLE` without caching fake items.

---

## Slide 6 — Precision Agriculture Intelligence (`R0.1` Live Vertical Slice)

Built directly atop the existing BHU LOKA architecture (`Pipelines/bhu_loka_agri_engine.py`, `Assets/vendor/bhu_loka_agri.js`, and Leaflet `bhu_loka_leafmap_interactive.html`):

1. **Interactive Farm Boundary Mapping:** Click-to-draw polygon, vertex undo/clear, multi-plot association (`parent_farm_id`), automatic WGS84 centroid -> **UTM Zone** (`EPSG:32643`–`32646` across India) Shoelace area calculation (`hectares`, `acres`, `perimeter_m`), RFC 7946 `.geojson` download, and explicit **non-ownership disclaimer**.
2. **Copernicus Sentinel-2 L2A Spectral Indices:** Real Planetary Computer STAC/TiTiler scene discovery (`<=40%` cloud filter, SCL pixel stats) computing:
   - `NDVI = (B08 - B04) / (B08 + B04)`
   - `NDRE = (B08 - B05) / (B08 + B05)`
   - `EVI = 2.5 * (B08 - B04) / (B08 + 6*B04 - 7.5*B02 + 1)`
   - `SAVI = ((B08 - B04) / (B08 + B04 + 0.5)) * 1.5`
   - `NDWI (Gao 1996) = (B08 - B11) / (B08 + B11)` & `NDWI (McFeeters 1996) = (B03 - B08) / (B03 + B08)`
   - Multi-date `ndvi_delta` comparison, `4`-stop color legend, and SQLite 6h STAC cache.
3. **NASA EOSDIS Discovery + Agro-Weather/Water-Soil:** Parallel queries to `/nasa-eo` (`MOD13Q1.061`, `MOD11A2.061`, `HLSL30.020`, USGS/NASA `landsat-c2-l2`), **NASA LaRC POWER AG** (`ALLSKY_SFC_SW_DWN`, `GWETROOT`, `T2M_MAX/MIN`, `-999` fill filtered), Open-Meteo `ET0` / `VPD` / `0-7 cm` & `7-28 cm` soil moisture, and Copernicus GLO-90 DEM slope drainage advisories.
4. **Scouting Logs & Farm-Aware Hybrid RAG:** Field notes and harvest yield logs (`kg/ha`) persist in SQLite and flow into `/api/v1/query` (`agri_context.farm_id`) via a provenance-stamped synthetic document (`id: live_farm_agri_context`).

---

## Slide 7 — Dual-Agent Sovereign Hybrid RAG & RAGAS Guardrails

- **Retrieval Engine (`Models/04_Hybrid_RAG/enterprise_rag_app/`):**
  - Sparse lexical scoring (`BM25Okapi`) + Dense vector similarity (`FAISS` / cached `all-MiniLM-L6-v2` `384-d` embeddings, deterministic SVD fallback when offline) merged through Reciprocal Rank Fusion (`k=60`).
- **Context Injection Without Hallucination:**
  - Live location telemetry (`live_context`) and active farm telemetry (`agri_context`) serialize strictly into `retrieved_docs` prior to synthesis so every claim remains auditable.
- **Verification Gate (`BhuLokaGuardrails` & `RagasEvaluator`):**
  - Computes runtime groundedness / faithfulness (`>= 0.70` gate; live `R0.1` probe scored `faithfulness = 0.80`). Uncalibrated out-of-domain gibberish yields zero fabricated citations (`retrieved_sources = []`).
  - Supports Hindi (`hi`), Hinglish, and English query synthesis alongside Agent-2 2D/3D camera spotlight actions.

---

## Slide 8 — Data Governance, Zero-Fabrication & Honesty Controls

| Principle | Runtime Enforcement in Codebase |
| :--- | :--- |
| **No Silent Mock Fallback** | Offline STAC, NASA CMR, NASA POWER, Open-Meteo, or Overpass calls return explicit `status: "UNAVAILABLE"` or `"EMPTY"` with rose `#fb7185` / amber `#fcd34d` UI badges. |
| **Clean SQLite Cache Hygiene** | Error/unavailable Overpass or STAC results are never written into `osm_spatial_cache` or `agri_satellite_cache`. |
| **No Inferred Administrative / Police Polygons** | Thiessen/buffer police boundaries are prohibited; GADM `'n.a.'` entries remain `verified_flag=0`. |
| **No Legal Title Claim** | Farm mapping endpoints and GeoJSON exports carry explicit non-ownership disclosures pointing users to official DILRMP portals. |
| **Strict Integrity Verification** | Automated check via `.agents/skills/scientific-integrity-guard/scripts/check_integrity.py --strict` checks code, artifacts, and manuscripts for zero unverified metrics, zero leaked secrets (`NASA_EARTHDATA_USER` env-only), zero emojis, and scholarly register. |

---

## Slide 9 — Software-Only Roadmap (`R1–R8`) vs Out-of-Scope Items

### Planned Software Releases (`NOT YET IMPLEMENTED` in `R0.1`)
- **R1–R2 (Lab & Crop Analytics):** Laboratory soil report parsers (`N-P-K`, pH, EC, organic carbon CSV/PDF extraction) and historical seasonal yield curve analytics.
- **R3–R4 (Irrigation & Multi-Temporal EO):** Field-scale NASA `HLSL30.020` / Sentinel-2 phenological anomaly tracking and GEE crop-mask batch scripts (when user configures `EE_PROJECT`).
- **R5–R6 (Market & Supply Intelligence):** Official mandi price ingestion (Agmarknet / eNAM APIs where documented) and storage-cold-chain proximity routing.
- **R7–R8 (Desktop & Multi-User Hardening):** Signed Electron desktop packaging and automated regression CI.

### Explicitly Out of Current Scope
- **Zero hardware deliverables:** No IoT sensor nodes, LoRaWAN boards, weather-station manufacturing, wearable trackers, or embedded microcontroller firmware.

---

## Slide 10 — Verification Evidence & Honest Environment Constraints (`R0.1`)

| Verification Check | Scope & Execution Context | Measured Outcome |
| :--- | :--- | :--- |
| **Full Backend + ASGI + MCP + NASA + Agri Pytest Suite** | Host Python `3.13.7` across all `4` test files (`test_india_location_street_intel.py`, `test_site_studio.py`, `test_rag.py`, `test_agri_engine.py`) | **`43 passed, 0 failed in 95.23s`** (`all-MiniLM-L6-v2` 384-d + FAISS + FastAPI ASGI + FastMCP `11` tools) |
| **Live FastAPI Daemon & NASA EO End-to-End Smoke** | `uvicorn main:app` (`127.0.0.1:8000`, `32` OpenAPI paths / `36` ASGI routes) tested live against NASA CMR, NASA POWER AG, USGS/NASA Landsat STAC, Copernicus Sentinel-2 STAC, Open-Meteo, & RAG `/api/v1/query` | All probed endpoints returned **`200 OK`**: `MOD13Q1.061` (`LIVE`), `MOD11A2.061` (`LIVE`), `HLSL30.020` (`LIVE`), `landsat-c2-l2` (`LIVE`), NASA POWER `gwetroot=0.62`, Sentinel-2 `NDVI=0.3510`, RAG `faithfulness=0.80`; test farm deleted cleanly afterward |
| **JavaScript Static Syntax Verification** | `node --check` on `bhu_loka_agri.js`, `bhu_loka_india_intel.js`, `bhu_loka_location_engine.js`, `bhu_loka_india_admin_index.js`, and inline scripts from both HTML dashboards | **PASS (`0` syntax errors)** |
| **Environment Constraint Note (`chrome-devtools-mcp`)** | Interactive `chrome-devtools-mcp@1.13.0` requires host `Node >= 22.12.0` (`v22.11.0` present locally); visual runtime rendering checked via headless Chromium renders + prior `browser` subagent captures | Transparently documented; zero hidden skips |
| **Scientific Integrity Strict Audit** | `.agents/skills/scientific-integrity-guard/scripts/check_integrity.py --strict` | `S0: 0 | S1: 0 | S2: 0` clean sign-off |

