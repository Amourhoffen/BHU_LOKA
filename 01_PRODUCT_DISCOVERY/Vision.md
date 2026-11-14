# BHU LOKA (भूलोक) — Product Vision Document (R0 / R0.1)

**Project:** BHU LOKA Sovereign Geospatial AI Platform  
**Verification Date:** 2026-11-12  
**Baseline Release:** R0 + R0.1 Software-Only Release  

---

## 1. Official Team and Responsibility Record

| Name | Role & Affiliation | Documented Scope of Responsibility |
| :--- | :--- | :--- |
| **Prince Kumar** | Project Owner, Indian Institute of Technology Patna (Roll No. PA2511CDH37) | Research problem formulation, geospatial backend & FastAPI/FastMCP architecture, satellite data processing (`MOD11A1.061`, `Sentinel-1`, `Copernicus DEM`, `Sentinel-2`, NASA CMR/GIBS/POWER), ML/Hybrid RAG implementation, verification, and documentation |
| **Pallav Rustogi** | Project Supervisor | Technical supervision, research review, and scientific governance |
| **Payal Priyadarshini** | UI/UX Designer, IIITDM Jabalpur (1st Semester) | Recognized team UI/UX designer; no fabricated software development or backend commits are attributed beyond her official UI/UX design role |

---

## 2. Purpose, Software-Only Scope, and NASA EO Priority

BHU LOKA is a **SOFTWARE-ONLY** scientific research and intelligence platform transforming multi-sensor Earth observation data, verified administrative hierarchies, and atmospheric/hydrological reanalysis into explainable geospatial decision support:

```
EARTH -> SATELLITE -> GIS -> CLIMATE -> SOIL -> WATER -> LAND & HAZARD -> AGRICULTURE -> FOOD -> MARKET (Software Roadmap)
```

### Critical Scope Clarification
- **IN CURRENT SCOPE (Software-Only):** Web dashboards (`2D` Leaflet and `3D` Three.js), Python/FastAPI backend APIs, `FastMCP` AI tools, GIS and Earth visualization, satellite data discovery and spectral index processing, scientific analytics (`SBCV` spatial ML and statistical experiments), contextual Hybrid RAG AI with RAGAS guardrails, and reproducible research reporting.
- **EXPLICITLY OUT OF CURRENT SCOPE:** IoT hardware, wearable devices, sensor manufacturing, physical monitoring devices, and hardware firmware. These are excluded from current deliverables and development/procurement.

### Primary Scientific Priority: NASA Earth Observation
BHU LOKA prioritizes authentic NASA Earth observation datasets and documented open workflows — including **NASA Earthdata / CMR**, **NASA GIBS / Worldview WMTS**, **NASA LP DAAC** (`MOD11A1.061`, `MOD11A2.061`, `MOD13Q1.061`, `HLSL30.020`), **NASA LaRC POWER**, and **USGS/NASA Landsat Collection 2 Level-2** — complemented by **ESA Copernicus Sentinel-1 SAR** and **Sentinel-2 L2A** where scientifically beneficial. BHU LOKA claims no NASA partnership or endorsement and never fabricates imagery or live telemetry.

---

## 3. Core Design Principles

1. **Sovereign Local Execution:** Spatial processing, BM25 + FAISS Hybrid RAG, SQLite spatial indexing, and Three.js / Leaflet visualization run locally on commodity workstations without mandatory commercial mapping API keys.
2. **Evidence-Grounded Provenance:** Every dataset reports provider, exact product identifier, acquisition date, spatial/temporal resolution, Coordinate Reference System (`EPSG:4326`, Sinusoidal `SR-ORG:6974`, or local UTM), licence/usage terms, processing methodology, quality/missing-data status, and source attribution.
3. **Fail-Closed Scientific Honesty:** Unavailable feeds, rate-limited APIs, clouded satellite passes, or unmapped polygons report explicit `UNAVAILABLE`, `EMPTY`, or `OFFICIAL_PORTAL_HANDOFF_ONLY` states rather than synthetic values.
4. **Spatial Validation Rigor:** Machine learning models are benchmarked using contiguous Spatial Block Cross-Validation (Roberts et al., 2016/2017).
5. **Non-Fabricated Land & Jurisdiction Scope:** Plot, Khata, and Khesra queries enforce composite administrative scoping (or ULPIN) and link to official state RoR portals without scraping protected records or claiming legal ownership.

---

## 4. Target User Personas

| Persona | Primary Need | BHU LOKA Surface | Status (R0 / R0.1) |
| :--- | :--- | :--- | :--- |
| **Geospatial & Disaster Researcher** | Empirical MODIS LST, SAR, DEM, WorldPop experiments and reproducible reports | `Experiments/`, `Models/01_Spatial_ML/`, `Final_Research_Work/` | `IMPLEMENTED AND VERIFIED` |
| **Urban Planner & Citizen** | Flood sink exposure, ULSI score, solar/UTCI site audit, CAD/GLB export | `bhu_loka_cyber_dashboard.html`, `bhu_loka_leafmap_interactive.html`, `/api/v1/site-analysis` | `IMPLEMENTED AND VERIFIED` (API & 3D/2D HTTP) |
| **India Administrator & First Responder** | 36 State/UT explorer, police registry, authorized CCTV, CAP RSS news, hospitals, road closures | `INDIA LOCATION & STREET INTELLIGENCE` (Modules A–F) | `IMPLEMENTED AND VERIFIED` (Pytest & HTTP) |
| **Farmer & Agronomist** | Farm polygon mapping, NASA CMR/GIBS/POWER + Sentinel-2 L2A indices, Open-Meteo ET0/soil, contextual AI | `AGRICULTURE INTELLIGENCE` (`/api/v1/agri`, `bhu_loka_agri.js`) | `IMPLEMENTED AND VERIFIED` (R0.1 MVP) |
| **AI / MCP Developer** | Programmatic RAG, hydromet, location intel, agri, and Site Studio tools | FastAPI `main.py` & `bhu_loka_mcp_server.py` (11 tools) | `IMPLEMENTED AND VERIFIED` |
