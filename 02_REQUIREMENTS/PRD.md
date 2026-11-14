# BHU LOKA (भूलोक) — Product Requirements Document (PRD, R0 / R0.1)

**Document ID:** `BHU-PRD-R0`  
**Verification Date:** 2026-11-12  
**Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  
**Scope Policy:** Software-Only Scientific Research & Intelligence Platform (IoT hardware, wearables, sensor manufacturing, physical monitoring devices, and hardware firmware are explicitly out of current scope).  
**Status Taxonomy:** `IMPLEMENTED AND VERIFIED` | `IMPLEMENTED BUT UNVERIFIED` | `PARTIALLY IMPLEMENTED` | `NOT IMPLEMENTED` | `OUT OF CURRENT SCOPE` | `PLANNED R1–R8`

---

## 1. Product Scope Overview

This PRD defines all R0 baseline capabilities alongside the verified `R0.1` Precision Agriculture & NASA Earth Observation release. Precision Agriculture (`R0.1`) is further specified in [`Agriculture_Intelligence_PRD.md`](file:///c:/Users/ljpri/OneDrive/Desktop/Learning%20Pathways/LearningPathways/Bhu%20Loka%20-%20%E0%A4%AD%E0%A5%82%E0%A4%B2%E0%A5%8B%E0%A4%95/02_REQUIREMENTS/Agriculture_Intelligence_PRD.md).

---

## 2. Functional Requirements Register

| Req ID | Module / Capability | Acceptance Criteria | R0 / R0.1 Status |
| :--- | :--- | :--- | :--- |
| **FR-01** | Canonical Location Synchronization (`LocationContext`) | Single WGS84 `(lat, lon, radius_km)` state shared across 2D Leaflet, 3D Three.js, telemetry drawer, Site Studio, and India Explorer | `IMPLEMENTED AND VERIFIED` |
| **FR-02** | India Admin Explorer (Module A) | 28 States + 8 UTs = 36 total; searchable capitals/settlements/aliases; state-specific hierarchy schemas; zero fabricated Level-3 divisions | `IMPLEMENTED AND VERIFIED` |
| **FR-03** | Land Parcel & Plot Search (Module B) | Composite scoping (State + District + Circle/Anchal + Mauza or ULPIN); official DILRMP/Bihar links; zero fabricated records | `IMPLEMENTED AND VERIFIED` |
| **FR-04** | Police Jurisdiction Layer (Module C) | Point registry (official Patna Police + OSM Overpass); `boundary_status` never inferred from nearest station point | `IMPLEMENTED AND VERIFIED` |
| **FR-05** | Street CCTV Registry (Module D) | Strict 6-value status enum; never serves mock feeds or restricted URLs; explicit empty message when none verified | `IMPLEMENTED AND VERIFIED` |
| **FR-06** | Local News Intelligence (Module E) | Official PIB EN/HI + NDMA Sachet RSS parser, 8 categories, geo-precision guard (unpinned non-coordinate items listed separately) | `IMPLEMENTED AND VERIFIED` |
| **FR-07** | Traffic, Emergency, Roads & Hospitals (Modules F, 10, 11) | 12-layer GIS catalog; live/cached Overpass `road_closures`, `traffic_advisories`, `hospitals` with honest `UNAVAILABLE` fallbacks | `IMPLEMENTED AND VERIFIED` |
| **FR-08** | 15-Module Location Intelligence API | `GET /api/v1/location-intelligence` returns modules 1–15 within bounded parallel timeout | `IMPLEMENTED AND VERIFIED` |
| **FR-09** | Architectural Site Studio & CAD/3D Export | UTM zone calculation, solar azimuth/elevation/shadow multiplier, UTCI thermal comfort, Overpass 350m OSM footprint, DXF/SVG/GLB/OBJ/GeoJSON export | `IMPLEMENTED AND VERIFIED` |
| **FR-10** | Dual-Agent Sovereign Hybrid RAG & Evaluation | BM25 + FAISS RRF (`k=60`), deterministic grounded generator, RAGAS faithfulness metrics (`>= 0.70`), telemetry guardrails, `/api/v1/query` & `/api/v1/eval/metrics` | `IMPLEMENTED AND VERIFIED` |
| **FR-11** | FastMCP Server Integration | `11` registered MCP tools bridging RAG, hubs, wards, hydromet, GEE workflow, and Site Studio | `IMPLEMENTED AND VERIFIED` |
| **FR-12** | Empirical Hazard Experiments & SBCV Model | 4 reproducible Patna experiments (`Exp_01`–`Exp_04` including NASA `MOD11A1.061`) and 5-fold SBCV Random Forest (`ROC-AUC 0.7498 +/- 0.0497`) | `IMPLEMENTED AND VERIFIED` |
| **FR-13** | Authentic NASA EO Services (CMR, GIBS, POWER, Landsat) | Zero-key NASA CMR (`MOD13Q1`, `MOD11A2`, `HLSL30`) + USGS/NASA Landsat C2 L2 metadata + NASA LaRC POWER AG + NASA GIBS WMTS Leaflet overlays with full 8-field provenance | `IMPLEMENTED AND VERIFIED` (`R0.1`) |
| **FR-14** | Precision Agriculture Intelligence (`R0.1` MVP) | Farm polygon draw/edit, UTM area (`ha`/`acres`), GeoJSON export, Sentinel-2 STAC NDVI/NDRE/EVI/SAVI/NDWI, NASA POWER & Open-Meteo ET0/soil water balance, farm-aware AI | `IMPLEMENTED AND VERIFIED` (`R0.1`) |
| **FR-15** | Google Earth Engine Live Tile Execution | Live authenticated GEE Python API script execution in runtime | `PARTIALLY IMPLEMENTED` (connector + reproducible script active; `EE_PROJECT` unset locally) |
| **FR-16** | Soil Lab CSV/PDF Ingestion & Mandi Market Feeds | Software-only future integrations (`PLANNED R2–R6`, no fabricated data in R0/R0.1) | `NOT IMPLEMENTED` (`PLANNED R2–R6`) |
| **FR-17** | IoT Hardware, Wearables, Sensor Manufacturing, Firmware | Physical devices, embedded firmware, MQTT sensor hardware brokers | `OUT OF CURRENT SCOPE` (Not current deliverables) |

---

## 3. Non-Functional Requirements

1. **Zero Fabrication & Honest Failure States:** External outages MUST render `#fb7185` rose alert states and explicit `UNAVAILABLE` explanations, never `#6ee7b7` live indicators.
2. **NASA Provenance & Attribution Guardrail:** Never render a map overlay as NASA data without verified NASA EOSDIS / LaRC / LP DAAC metadata and explicit non-endorsement attribution.
3. **Thread & File-Lock Safety on Windows:** SQLite connections close deterministically via context managers; Overpass slot rate-limiting never holds `_OVERPASS_LOCK` across network I/O.
4. **Credential Hygiene & Scientific Integrity:** All credentials read from environment variables or `.netrc`; zero emojis and zero banned promotional words across all files.
