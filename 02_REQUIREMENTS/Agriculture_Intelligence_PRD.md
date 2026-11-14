# BHU LOKA (भूलोक) — Agriculture Intelligence Product Requirements Document (R0.1–R8)

**Document ID:** `BHU-PRD-AGRI-01`  
**Verification Date:** 2026-11-12  
**Team:** Prince Kumar (Project Owner, IIT Patna) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  
**Scope:** Software-Only Scientific Platform (IoT hardware, wearables, and firmware are explicitly out of current scope)  
**Mission Chain:** `EARTH -> SATELLITE -> GIS -> CLIMATE -> SOIL -> WATER -> AGRICULTURE -> FOOD -> MARKET`

---

## 1. Product Objective and Integration Mandate

Extend the existing BHU LOKA platform (canonical `LocationContext`, Leaflet 2D map, FastAPI backend, SQLite spatial database, and Enterprise Hybrid RAG + RAGAS Guardrails) into an integrated Precision Agriculture Intelligence module prioritizing authentic **NASA Earth observation** (`NASA EOSDIS CMR / LP DAAC`, `NASA GIBS / Worldview`, `NASA LaRC POWER`, and `USGS/NASA Landsat Collection 2 L2`) complemented by **Copernicus Sentinel-2 L2A**, **Copernicus GLO-90 DEM**, and **Open-Meteo ECMWF**.

---

## 2. Functional Requirements & Release Allocation

| Section | Requirement | R0.1 Status | R1–R8 Software Roadmap |
| :--- | :--- | :--- | :--- |
| **1. Boundary Mapping & Cadastral Advisory** | Draw/edit farm polygon on Leaflet, UTM planar area (`ha` and `acres`), centroid & EPSG CRS, RFC 7946 GeoJSON export, multi-plot `parent_farm_id` **holding portfolio cluster summary (`/portfolio-summary` with crop mix & area-weighted cached NDVI)**, **DILRMP / State RoR / Bhu-Naksha advisory cross-link (`/cadastral-advisory`)**, explicit ownership non-verification notice | `IMPLEMENTED AND VERIFIED` (`bhu_loka_agri.js` + `/api/v1/agri/farms` + `/cadastral-advisory` + `/portfolio-summary`) | Revenue village/Mauza cadastral vector viewer when verified (`R3`) |
| **2. NASA & Copernicus EO** | NASA GIBS WMTS Leaflet layers (`TrueColor`, `LST`, `NDVI_8Day`); NASA CMR (`MOD13Q1.061`, `MOD11A2.061`, `HLSL30.020`) & USGS Landsat C2 L2 discovery (`/nasa-eo`); Copernicus Sentinel-2 L2A STAC (`NDVI`, `NDRE`, `EVI`, `SAVI`, `NDWI` McFeeters/Gao, `GNDVI`, `BSI`, `NIR CV%` intra-field zonal uniformity) + delta comparison; Copernicus Sentinel-1 C-SAR `RTC` crop wetness (`VV`/`VH` dB, `VH/VV` ratio, radar ambiguity disclosure) | `IMPLEMENTED AND VERIFIED` (`/satellite`, `/sar-wetness`, `/nasa-eo`) | Multi-temporal phenology & `rasterio` GeoTIFF download (`R2`) |
| **3. Climate, Solar & Soil** | NASA LaRC POWER (`ALLSKY_SFC_SW_DWN`, `GWETROOT`, `PRECTOTCORR`, `T2M_MAX/MIN`, `-999` fill filtering) + Open-Meteo `soil_moisture_0_to_7cm` / `7_to_28cm`, `ET0`, `VPD`, Copernicus GLO-90 slope/drainage + **FAO-56 Crop Coefficient ($K_c$) & $ET_c = K_c \cdot ET_0$ volumetric deficit calculator** + **India Soil Health Card (ICAR) CSV/JSON lab parser & rating engine** | `IMPLEMENTED AND VERIFIED` (`/water-soil`, `/fao56-etc`, `/soil-health`) | Soil Health Card PDF OCR & local KVK dosage localization (`R3`) |
| **4. Crop Health & Scouting** | Threshold-explained moisture deficit, waterlogging, and heatwave advisories + persistent manual field scouting/yield logs | `IMPLEMENTED AND VERIFIED` (`/scouting`) | Automated phenology anomaly alerts (`R2`) |
| **5. Market & Hardware Scope** | Honest `PLANNED` / `OUT OF CURRENT SCOPE` separation (zero fake mandi prices, zero simulated IoT hardware, zero wearable firmware) | `IMPLEMENTED AND VERIFIED` (UI + API disclosures) | Agmarknet/e-NAM software connector (`R4–R6`); IoT hardware excluded |
| **6. Farm-Aware AI Analysis** | Pass active farm `agri_context` (including NASA POWER, NASA EO, Sentinel-2, Open-Meteo, DEM) to `/api/v1/query`, injecting grounded provenance doc before `RagasEvaluator` (`faithfulness >= 0.70`) | `IMPLEMENTED AND VERIFIED` (`/ai-context`, `/api/v1/query`) | Multi-season agronomic memory (`R3`) |

---

## 3. Non-Negotiable Scientific & Legal Guardrails

1. **No Ownership Claims & No NASA Endorsement Claims:** Saved polygons are operational user boundaries only; all NASA datasets carry open-data attribution without implying agency endorsement.
2. **Exact Index Formula Disclosure:** Both **McFeeters (1996)** surface water `(B03 - B08) / (B03 + B08)` and **Gao (1996)** canopy liquid water `(B08 - B11) / (B08 + B11)` are labeled explicitly.
3. **Fail-Closed Missing-Data Hygiene:** Offline endpoints return `UNAVAILABLE`, missing NASA POWER entries (`-999`) are excluded cleanly, and clouded Sentinel-2 scenes (`>40%`) are excluded from automated stress metrics.
