# BHU LOKA (भूलोक) — Market Research and Differentiation Analysis (R0 / R0.1 Aligned)

**Project:** BHU LOKA Sovereign Geospatial AI Platform  
**Team:** Prince Kumar (Project Owner, IIT Patna, `PA2511CDH37`) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  
**Scope Note:** Software-Only platform evaluation (IoT hardware, wearables, and sensor firmware are explicitly **OUT OF CURRENT SCOPE**)  

---

## 1. Landscape of Existing Platforms

| Platform / Category | Capabilities | Structural Limitations Relevant to India & Sovereign Research |
| :--- | :--- | :--- |
| **Global Cloud EO Engines (Google Earth Engine, Microsoft Planetary Computer)** | Planetary raster catalog, server-side band math, global imagery archive | Require external cloud runtime, account credentials/quotas, and lack localized India 36-State administrative hierarchies, RoR handoffs, or local sovereign desktop execution |
| **Generic GIS Suites (QGIS, ArcGIS)** | Arbitrary vector/raster geoprocessing, CAD/GeoTIFF workflows | Desktop analyst tools; lack built-in hybrid RAG citation guardrails, UN-SPIDER urban double-bounce flood physics, live CAP emergency feeds, or farmer-ready web UI |
| **Conventional Flood Toolkits (UN-SPIDER `flood-mapping-tool`)** | Rapid Sentinel-1 open-water threshold ($\Delta\sigma^0 \le -2.0\text{ dB}$) | Misses urban street-canyon double-bounce flooding ($95.98\%$ omission error documented in `Exp_01` for Patna) |
| **Commercial Precision Ag Portals (Cropin, OneSoil, EOSDA)** | NDVI parcel dashboards, weather cards, seasonal reports | Cloud-hosted SaaS with subscription walls, opaque agronomic heuristics, and limited scientific explainability or provenance guarantees |
| **Open-Source Stacks Integrated Locally (`Repos/`)** | `leafmap`, `torchgeo`, `geoai`, `earthengine-api`, `flood-mapping-tool`, `gods-eye-view` | Fragmented upstream libraries prior to unified calibration and sovereign RAG/UI integration in BHU LOKA |

---

## 2. BHU LOKA Differentiation Matrix

1. **Unified Urban-to-Rural Continuum:** Connects urban micro-topography, double-bounce SAR flood physics, civic location/emergency intelligence (Modules A–F), Site Studio CAD/GLB export, and parcel-level agriculture under one canonical WGS84 (`EPSG:4326`) LocationContext.
2. **Auditability and Zero-Fabrication Enforcement:** Every API payload returns explicit provenance (`source_attribution`, CRS, timestamps, limitations) and honest failure states (`UNAVAILABLE`, `EMPTY`) instead of decorative scores or mock tiles.
3. **Methodological Integrity in Spatial ML:** Enforces Spatial Block Cross-Validation (Roberts et al., 2016/2017) directly in the modeling pipeline rather than misleading random k-fold validation.
4. **Dual-Agent Verified RAG with RAGAS Guardrails:** Combines BM25 + FAISS RRF retrieval with runtime faithfulness verification (`>= 0.70` claim grounding threshold in `BhuLokaGuardrails`) and provenance-injected live/farm telemetry.
5. **India-First Administrative & DILRMP Compliance:** Models all 28 States + 8 Union Territories with state-varying subdivisions, multilingual aliases, separate non-inferred police registries, and strict composite plot scoping.
