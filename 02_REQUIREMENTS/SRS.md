# BHU LOKA (भूलोक) — Software Requirements Specification (SRS, R0 / R0.1 Aligned)

**Document ID:** `BHU-SRS-R0`  
**Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  
**Scope Boundary:** Software-Only deliverables (`0` IoT hardware, wearable, or firmware components in current scope)  

---

## 1. System Interfaces and Ports

| Component | Entry File / Interface | Transport / Protocol | Status |
| :--- | :--- | :--- | :--- |
| **FastAPI Application Server** | `Models/04_Hybrid_RAG/enterprise_rag_app/main.py` | HTTP/JSON (`127.0.0.1:8000`, `32` OpenAPI paths / `36` ASGI routes) | `IMPLEMENTED AND VERIFIED` |
| **MCP Geospatial Server** | `Pipelines/bhu_loka_mcp_server.py` | FastMCP stdio/SSE (`127.0.0.1:8001`, 11 registered tools) | `IMPLEMENTED AND VERIFIED` |
| **Electron Desktop Wrapper** | `BhuLoka_Chromium_App/main.js` | Chromium renderer + Node `child_process.execFile` IPC to `god_eye_hybrid_rag.py` | `PARTIALLY IMPLEMENTED` (wrapper code present; unexecuted in current QA pass) |
| **3D Sovereign HUD Dashboard** | `bhu_loka_cyber_dashboard.html` | HTML5 + Tailwind CDN / Three.js r128 + `bhu_loka_location_engine.js` + `bhu_loka_india_intel.js` | `IMPLEMENTED AND VERIFIED` (syntax + HTTP 200 + headless Chromium render) |
| **2D Interactive GIS Dashboard** | `bhu_loka_leafmap_interactive.html` | HTML5 + Leaflet 1.9.4 + shared JS engines + `bhu_loka_agri.js` + NASA GIBS WMTS | `IMPLEMENTED AND VERIFIED` (syntax + HTTP 200 + headless Chromium render) |
| **Spatial SQLite Knowledge Store** | `Data/01_Boundaries/bhu_loka_india_intel.sqlite` | SQLite 3 + R-tree spatial index (`idx_admin_rtree`) | `IMPLEMENTED AND VERIFIED` |

---

## 2. Detailed API Route Specification (Verified in `main.py`)

### 2.1 Core RAG, Evaluation & Urban Telemetry Routes
1. `GET /health` -> Service status, document count, uptime.
2. `POST /api/v1/query` -> Dual-agent BM25 + FAISS RRF RAG with RAGAS faithfulness & guardrail scoring.
3. `GET /api/v1/eval/metrics` -> Aggregate RAGAS evaluation history metrics.
4. `GET /api/v1/documents` -> Indexed RAG document registry.
5. `GET /api/v1/wards` -> Patna ward ULSI, SAR, DEM, and safety profiles.
6. `GET /api/v1/hubs` -> 36-State sovereign extent (`6.75N`–`37.10N`) and regional hazard hubs.
7. `GET /api/v1/live-telemetry` -> Cached/live Open-Meteo hydromet & GloFAS proxy.
8. `GET /api/v1/gee-status` -> Google Earth Engine SDK availability and workflow generator.
9. `GET /api/v1/satellites` -> Live orbital pass/CelesTrak telemetry (when online) or fail-closed error.
10. `GET /api/v1/dem-hologram` -> Copernicus GLO-90 DEM elevation grid for 3D terrain relief.
11. `GET /api/v1/sat-tile/{z}/{x}/{y}` -> Satellite imagery tile proxy.
12. `GET /api/v1/location-intelligence` -> 15-module universal location payload.
13. `GET /api/v1/site-analysis` -> Site Studio solar, UTCI thermal, wind rose, contour, and optional 350m OSM context.
14. `GET /api/v1/export-site` -> Binary/text downloads (`dxf`, `svg`, `profile_svg`, `glb`, `obj`, `geojson`) with `X-Bhu-Loka-Attribution`.

### 2.2 India Location & Street Intelligence Routes (`/api/v1/india/...`)
15. `GET /api/v1/india/states` -> 28 States + 8 UTs + capital list + hierarchy metadata.
16. `GET /api/v1/india/admin/children` -> Children by `parent_id` or `state_code` + `level_depth` (`verified_flag = 1`).
17. `GET /api/v1/india/admin/search` -> Ranked autocomplete over States/UTs, Districts, L3 units, settlements, capitals, and multilingual aliases.
18. `GET /api/v1/india/admin/resolve` -> Point-in-polygon + R-tree lookup with breadcrumb navigation and top-level `in_india`.
19. `GET /api/v1/india/admin/villages-wards` -> Radius-based OSM settlements/wards.
20. `GET /api/v1/india/land-records/portals` -> DILRMP official RoR / Bhu-Naksha / Revenue directory.
21. `POST /api/v1/india/land-records/search` -> Composite-scope enforcement + local lookup (if present) + official portal handoff.
22. `GET /api/v1/india/layers/catalog` -> 12-layer GIS schema & attribution metadata.
23. `GET /api/v1/india/layers/{layer_id}` -> GeoJSON + typed items for all 12 layers (`LIVE`, `CACHED`, `VERIFIED_LOCAL`, `EMPTY`, `UNAVAILABLE`).
24. `POST /api/v1/india/news/refresh` -> Official PIB EN/HI + NDMA Sachet RSS ingestion trigger.

### 2.3 Precision Agriculture & NASA Earth Observation Routes (`/api/v1/agri/...`, R0.1)
25. `GET /api/v1/agri/farms` & `POST /api/v1/agri/farms` -> Farm/plot boundary persistence (`EPSG:4326` + auto UTM zone area/perimeter calculation).
26. `GET / PUT / DELETE /api/v1/agri/farms/{farm_id}` -> Farm detail, geometry vertex/crop updates, and cleanup deletion.
27. `GET /api/v1/agri/farms/{farm_id}/export-geojson` -> Validated RFC 7946 `FeatureCollection` download (`X-Bhu-Loka-Attribution`).
28. `GET /api/v1/agri/farms/{farm_id}/satellite` -> Copernicus Sentinel-2 L2A STAC/TiTiler NDVI, NDRE, EVI, SAVI, NDWI (Gao & McFeeters), and multi-date NDVI delta.
29. `GET /api/v1/agri/farms/{farm_id}/nasa-eo` -> NASA EOSDIS CMR discovery (`MOD13Q1.061`, `MOD11A2.061`, `HLSL30.020`) + USGS/NASA `landsat-c2-l2` + GIBS WMTS references.
30. `GET /api/v1/agri/farms/{farm_id}/water-soil` -> Open-Meteo ECMWF agro-weather/ET0 + NASA LaRC POWER AG climatology (`-999` filtered) + Copernicus GLO-90 DEM slope drainage.
31. `POST /api/v1/agri/farms/{farm_id}/scouting` -> Field scouting and yield observation persistence.
32. `GET /api/v1/agri/farms/{farm_id}/ai-context` -> Provenance-stamped farm context assembly for Hybrid RAG grounding.

---

## 3. Data Constraints and Validation Rules

- **WGS84 Coordinate Bounds:** `lat` in `[-90.0, 90.0]`, `lon` in `[-180.0, 180.0]`; `radius_km` in `[1.0, 100.0]`.
- **SQLite Non-Fabrication Constraint:** `admin_units.verified_flag = 0` holds 98 GADM `'n.a.'` placeholders deactivated from public queries; Patna verified L3 GADM count is strictly `3` (`Barh`, `Danapur`, `Masaurhi`).
- **Overpass Error Non-Caching:** Responses with `status` in `{ERROR, UNAVAILABLE}` are never persisted into `osm_spatial_cache`.
- **ElementTree Compatibility (Python 3.13):** XML child lookup checks `elem is not None` explicitly to prevent Python 3.13 `DeprecationWarning`.
