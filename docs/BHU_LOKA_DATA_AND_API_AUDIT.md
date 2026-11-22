# BHU LOKA (भूलोक) — Data Source Register & API Audit (Phase 1)

---

## 1. Primary Geospatial Datasets Register

| Dataset ID | Platform / Sensor | Spatial Resolution | Temporal Extent | File Path in Repository | Scientific Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SAR_S1_PRE** | Copernicus Sentinel-1A C-SAR | 10m (IW GRDH VV) | 2019-09-23 | `Data/02_SAR_Sentinel1/S1A_IW_GRDH_VV_20190923_pre_flood.tif` (727 MB) | Pre-deluge baseline backscatter calibration |
| **SAR_S1_PEAK**| Copernicus Sentinel-1B C-SAR | 10m (IW GRDH VV) | 2019-09-29 | `Data/02_SAR_Sentinel1/S1B_IW_GRDH_VV_20190929_peak_flood.tif` (748 MB) | Peak inundation flood mapping (`Δσ0 ≥ +1.5 dB`) |
| **DEM_GLO30** | Copernicus GLO-30 DEM | 30m | Static 2020 | `Data/04_DEM_SRTM/glo30_N25_E084.tif` & `E085.tif` (88 MB) | Topographic depression & flood sink modeling |
| **OPT_S2** | Sentinel-2 L2A MSI | 10m / 20m | 2024–2026 | Microsoft Planetary Computer STAC API | Precision agriculture NDVI, NDRE, EVI indices |
| **LANDSAT_8** | Landsat 8 OLI/TIRS | 30m | 2014 Baseline | USGS EarthExplorer / STAC | 2014 decadal lake boundary comparison |
| **LST_MODIS** | Terra/Aqua MODIS (MOD11A2) | 1km | 2019 | `Data/06_LST_Thermal/raw_hdf/` (340+ files) | Thermal heatwave and land surface temperature |
| **POP_WPOP** | WorldPop Global Project | 100m / 1km | 2020 | `Data/07_Population_WorldPop/worldpop_india_2020_1km.tif` (19 MB) | Population exposure at risk |
| **ADMIN_GADM** | GADM 4.1 India Level 2 | Vector Polygons | 2022 | `Data/01_Boundaries/gadm41_IND_level2.gpkg` (52 MB) | All 724 Indian districts and administrative boundaries |
| **SOV_STATES** | Sovereign Survey of India | Vector GeoJSON | 2024 | `Data/01_Boundaries/india_36_states_sovereign.geojson` (206 KB) | Official international border & 36 States/UTs |
| **ORBIT_NORAD**| CelesTrak GP Elements | Orbital Ephemeris | Live SGP4 | `.celestrak_gp_cache.json` (4.1 MB) | 10,786 active satellites (ISRO, Starlink, EO) |

---

## 2. Backend API Endpoint Registry

### A. Enterprise RAG & Sovereign AI Gateway (`Models/04_Hybrid_RAG/enterprise_rag_app/main.py`)
- `GET /health`: System uptime, active worker status, memory consumption.
- `GET /api/v1/system/security-audit`: Security header compliance, sanitization checks.
- `GET /api/v1/sources/provenance`: Data source provenance register and verification tiers.
- `POST /api/v1/query`: Grounded RAG query processor with MiniLM embeddings and citations.
- `GET /api/v1/eval/metrics`: LLM evaluation metrics (faithfulness, answer relevance).
- `GET /api/v1/live-telemetry`: Aggregated real-time environmental telemetry stream.
- `POST /api/v1/predict-flood`: Machine learning spatial flood inundation prediction.
- `GET /api/v1/satellites`: Real-time propagated satellite coordinate positions.
- `GET /api/v1/dem-hologram`: 3D micro-DEM terrain grid generator for Patna/Hussain Sagar.
- `POST /api/v1/extract/aoi`: Multi-source cadastral feature extraction within AOI boundary.

### B. Micro-GIS Site Analytics API (`Pipelines/bhu_loka_site_analytics_api.py`)
- `GET /health`: Service health check.
- `POST /api/v1/imagery/search`: STAC discovery for cloud-free satellite passes.
- `POST /api/v1/analyze`: Land-use classification and built-up footprint detection.
- `GET /api/v1/lakes/catalog`: Telangana Jal Raksha lake catalog (Hussain Sagar, Osman Sagar, etc.).
- `GET /api/v1/lakes/{lake_id}/ftl-buffer`: FTL contour and statutory 30m regulatory buffer polygon.
- `POST /api/v1/change-detection`: Decadal change detection between two satellite timestamps.
- `POST /api/v1/gis/buffer`: Geodesic UTM polygon buffer calculation (EPSG:32644).
- `POST /api/v1/gis/overlay`: Geometric spatial overlay (Intersection, Union, Difference).
- `POST /api/v1/gis/zonal-stats`: Elevation and slope summary statistics across AOI.
- `POST /api/v1/gis/site-report`: BSA 2023 §63 compliant evidentiary screening report.

### C. External Public Telemetry Integrations (Zero-Key)
- **Open-Meteo Weather API**: Hourly air temperature, relative humidity, wind speed, surface solar radiation.
- **Open-Meteo Soil Profile API**: Topsoil moisture 0–7cm, subsoil moisture 7–28cm.
- **GloFAS v4 River Discharge**: Copernicus Global Flood Awareness System daily river discharge series.
- **OpenStreetMap Nominatim**: Geocoding and reverse geocoding with Indian territory bounding box.
- **CelesTrak Space-Track**: NORAD satellite catalog two-line element sets (TLE).

---

## 3. Data Integrity & Fail-Closed Protocols
1. **Zero Synthetic Observations**: If Open-Meteo or CelesTrak is unreachable, the UI transitions to `HISTORICAL BENCHMARK` or `OFFLINE CLIMATOLOGY` and displays an amber indicator. It never generates synthetic telemetry.
2. **Crime Data Protocol**: The crime density layer strictly displays `UNAVAILABLE (Official crime data unavailable)`. Zero speculative crime polygons are generated.
3. **BSA 2023 §63 Integrity**: Exported land inspection dossiers include SHA-256 cryptographic hashes of all extracted geometries and parameters to preserve evidentiary admissibility.
