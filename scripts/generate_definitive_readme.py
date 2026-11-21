import os

readme_content = """# BHU LOKA (भूलोक) — Sovereign Earth System & Multi-Hazard Intelligence Workstation
<img width="1461" height="820" alt="BHU LOKA Workstation" src="https://github.com/user-attachments/assets/8edad3ee-72f4-4035-8a97-aa90c676a495" />

## Sovereign Pan-India 2D/3D Geospatial Intelligence, Cadastral Screening & Spatial Machine Learning Platform

### Developed at Indian Institute of Technology Patna (IIT Patna) · Department of Computer Science & Data Analytics
#### In Academic Collaboration with Indian Institute of Information Technology, Design and Manufacturing Jabalpur (IIITDM Jabalpur)

[![Live Web Platform](https://img.shields.io/badge/Live%20Platform-bhu--loka.web.app-0284c7.svg?style=for-the-badge&logo=firebase)](https://bhu-loka.web.app)
[![2D GIS Explorer](https://img.shields.io/badge/2D%20GIS%20Explorer-28%20States%20%2B%208%20UTs-10b981.svg?style=for-the-badge)](https://bhu-loka.web.app/2d)
[![Research Presentation](https://img.shields.io/badge/Research%20Deck-Interactive%20Slides-f59e0b.svg?style=for-the-badge)](https://bhu-loka.web.app/presentation)
[![Test Suite](https://img.shields.io/badge/Test%20Suite-63%2F63%20Passing%20(100%25)-emerald.svg?style=for-the-badge)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![SAR Platform](https://img.shields.io/badge/Sensor-Copernicus%20Sentinel--1%20C--SAR%20(5.405%20GHz)-0284c7.svg)](https://search.asf.alaska.edu/)
[![Elevation](https://img.shields.io/badge/DEM-Copernicus%20GLO--30%20(30m)-6366f1.svg)](https://registry.opendata.aws/copernicus-dem/)
[![Geographic Extent](https://img.shields.io/badge/Coverage-Pan--India%20(36%20States%2FUTs%2C%20724%20Districts)-amber.svg)](Data/08_Processed_Outputs/bhu_loka_india_admin_index.js)
[![Legal Framework](https://img.shields.io/badge/Cadastral%20Screening-BSA%202023%20§63%20Compliant-purple.svg)](Assets/vendor/bhu_loka_urban_studio.js)

---
<img width="1467" height="820" alt="BHU LOKA Team and Core Mission" src="https://github.com/user-attachments/assets/04ae7501-3aa7-4d8a-a19b-6426189e5412" />

## Research Team & Academic Authorship

* **Prince Kumar** — Lead Geospatial AI Researcher & System Architect  
  *Indian Institute of Technology Patna (IIT Patna)*  
  Department of Computer Science & Data Analytics (Roll: `PA2511CDH37`)
* **Payal Priyadarshini** — Product Lead | UI/UX Designer  
  *Indian Institute of Information Technology, Design and Manufacturing Jabalpur (IIITDM Jabalpur)*
* **Dr. Pallav Rustogi** — Academic Advisor & Research Supervisor  
* **Research Collaboration:** **Team Amour Hoffen**  
* **Formal Manuscript:** *Sequential Compound Hydro-Thermal Risk and Urban Corner-Reflector Flood Mapping in Continental Alluvial Metropolises: Empirical Earth Observation and Spatial Validation Sensitivity over Patna, India*

---

## Live Platform Access & Publication Deliverables

| Deliverable | Access Link | Description |
| --- | --- | --- |
| **Live 3D Sovereign Workstation** | [https://bhu-loka.web.app](https://bhu-loka.web.app) | Full 3D WebGL2 workstation: 3D Earth, Sovereign India 36, 38 Bihar Districts, 30m DEM, live satellites |
| **Live 2D Sovereign GIS Workstation** | [https://bhu-loka.web.app/2d](https://bhu-loka.web.app/2d) | Pan-India 2D GIS: Interactive 28 States & 8 UTs selector, Sentinel-1 SAR Deluge layer, DEM profiles |
| **Land Intelligence Studio** | [https://bhu-loka.web.app/studio](https://bhu-loka.web.app?view=studio) | BSA 2023 §63 screening: Cadastral FTL review, 4-quadrant audit, bi-temporal swipe, 3D buffer |
| **Interactive Presentation Deck** | [https://bhu-loka.web.app/presentation](https://bhu-loka.web.app/presentation) | Interactive research slide deck with live Chart.js radar curves, DEM profiles, and KPIs |
| **Presentation Deck PDF** | [`BHU-LOKA (2).pptx.pdf`](./BHU-LOKA%20(2).pptx.pdf) | High-definition research presentation deck (`88.3 MB`) |
| **12-Page Research Paper PDF** | [`Sequential_Compound_Hydro_Thermal_Risk_...pdf`](./Sequential_Compound_Hydro_Thermal_Risk_and_Urban_Corner_Reflector_Flood_Mapping_in_Continental_Alluvial_Metropolises__Empirical_Earth_Observation___3_.pdf) | Complete peer-review manuscript with physical equations, Otsu calibration, and SBCV benchmarks |
| **Verified Inundation GeoJSON** | [`sar_flood_inundation_patna_2019.geojson`](./Data/08_Processed_Outputs/sar_flood_inundation_patna_2019.geojson) | Vector polygon layer ($26.54\\text{ km}^2$) ready for instant QGIS/ArcGIS import |
| **Trained Spatial ML Checkpoints** | [`bhu_loka_spatial_rf_v1.joblib`](./Models/Checkpoints/bhu_loka_spatial_rf_v1.joblib) | 7-feature trained Random Forest classifier with 5-fold spatial block cross-validation (21.98 MB) |

---

## What We Built & Re-Engineered (Engineering Milestones)

To transform BHU LOKA into a scientifically defensible, sovereign, India-wide Earth Intelligence workstation, our engineering team executed a thorough re-engineering process:

### 1. Pan-India Sovereign 2D GIS Architecture (28 States + 8 Union Territories)
* **Pre-existing State:** The 2D map contained a single hardcoded button for "Bihar 38", leaving the remaining 35 sovereign Indian states and UTs inaccessible despite underlying administrative data.
* **Our Re-Engineering:** 
  * Implemented `#sovereign-state-select` containing structured optgroups for all **28 States** and **8 Union Territories** (724 total districts).
  * Engineered dynamic bounding box navigation (`selectSovereignState(name)`), instant vector boundary highlighting (`highlightSovereignStatePolygon(name)`), and state-level district drill-down toggles.
  * Added floating `#state-sovereign-card` displaying official capitals, local vernacular names (Hindi, Telugu, Tamil, Bengali, etc.), district counts, and Survey of India / GADM v4.1 geodetic provenance.
  * Integrated URL query parameter deep-linking (`?state=Bihar&districts=1`) for headless capture and collaborative sharing.

### 2. Elimination of Unscientific Toys, Street-Level Clutter & Mock Controls
* **Pre-existing State:** The satellite interface contained non-geospatial mock controls (e.g. Police PS, Street CCTV, Local News, Traffic on satellite view; joke buttons like "Dancing with the SARs" and "SAR Hero").
* **Our Re-Engineering:** 
  * Purged the entire `#india-intel-main-nav` strip from the satellite workspace.
  * Replaced toy buttons with scientifically verified remote sensing actions: `Sentinel-1 SAR Deluge (Patna 2019)` and `Sovereign 2D GIS (28 States + 8 UTs)`.
  * Cleaned up UI elements so every visible button, layer toggle, and dropdown connects to real geospatial data or a functional processing pipeline.

### 3. 3D Planetary Globe Coordinate Attachment & Zero-Drift Stabilization
* **Pre-existing State:** The 3D Three.js Earth sphere rotated, but sovereign India boundaries and hazard pins remained detached or drifted across the viewport.
* **Our Re-Engineering:** 
  * Re-architected Three.js scene hierarchy: bound sovereign border lines, state boundary GeoJSON geometries, and hazard markers directly to the rotating Earth mesh coordinate frame.
  * Anchored pins to WGS84 spherical coordinates ($R = 6371\\text{ km}$ equivalent in WebGL units) with automated Cartesian rotation matrix transformation.
  * Preserved full user interactive orbit controls, pitch, zoom, and tilt without coordinate slippage.

### 4. Land Intelligence Studio Rewrite (BSA 2023 §63 Legal Screening Framework)
* **Pre-existing State:** The system generated speculative, legally unsound automated banners claiming `DEMOLITION / NOTICE MANDATED` upon simple polygon intersection, and misattributed East Bengaluru lake imagery (Yelemallappachetty) to Patna.
* **Our Re-Engineering:** 
  * Completely eliminated speculative demolition claims; replaced with objective technical screening: `POTENTIAL SPATIAL OVERLAP — REQUIRES OFFICIAL VERIFICATION`.
  * Formulated evidentiary dossiers compliant with **Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 (BSA §63)**, incorporating SHA-256 cryptographic hashes, sensor metadata, and clear disclaimers that remote sensing is a preliminary screening tool requiring physical revenue demarcation.
  * Restructured legal logic to reflect state-specific frameworks: Telangana WALTA Act 2002 / HYDRAA, Bihar Wetland & Floodplain Rules, Karnataka KLCDA, and MoEFCC national guidelines.
  * Corrected all false spatial associations and clarified reference benchmarks.

### 5. Precision Agriculture & Shoelace Cadastral Polygon Engine
* **Pre-existing State:** Plot boundaries were static or lacked geodetic measurement formulas.
* **Our Re-Engineering:** 
  * Built an interactive parcel drawer on mobile and desktop supporting multi-vertex polygon drawing, editing, and vertex undo.
  * Implemented spherical Shoelace geodetic area computation calculating exact parcel acreage and hectares.
  * Added agricultural lifecycle tracking: Vegetative, Flowering, Harvesting, and Fallow cycles.
  * Export field boundaries directly into standard GeoJSON for PM-KISAN, crop insurance, or drone surveying.

### 6. Empirical Sentinel-1 SAR Calibration & Urban Dihedral Corner-Reflector Discovery
* **Pre-existing State:** Flood layers relied partly on synthetic rasters without verified physical microwave calibration.
* **Our Re-Engineering:** 
  * Processed genuine dual-date Copernicus Sentinel-1A and Sentinel-1B C-band SAR scenes ($5.405\\text{ GHz}$) over Patna from Alaska Satellite Facility (ASF Vertex).
  * Discovered and modeled the urban dihedral double-bounce retro-reflection phenomenon: standing water in narrow alleyways forms $90^\\circ$ dihedral retro-reflectors with vertical walls, causing a backscatter surge ($\\\\Delta\\\\sigma^0 \\\\ge +1.5\\\\text{ dB}$ to $+4.8\\\\text{ dB}$) rather than the specular drop observed in open fields.
  * Automated bimodal Otsu thresholding ($\\\\tau^* = -3.80\\\\text{ dB}$), isolating $26.54\\\\text{ km}^2$ of newly inundated land ("Naya Paani").

### 7. Spatial Block Cross-Validation (5-Fold SBCV) & Anti-Autocorrelation Architecture
* **Pre-existing State:** Machine learning models were vulnerable to random train-test splitting leakage due to Tobler's First Law of Geography.
* **Our Re-Engineering:** 
  * Implemented 5-Fold Spatial Block Cross-Validation (SBCV) using spatially contiguous, non-overlapping geographic blocks over 60,000 spatial samples.
  * Trained a 100-tree Random Forest classifier (`bhu_loka_spatial_rf_v1.joblib`, 21.98 MB) achieving an honest mean ROC-AUC of $0.7498$ and accuracy of $68.88\\%$.
  * Enforced strict scientific transparency: inference over arbitrary uncalibrated AOIs is explicitly watermarked as `SIMULATED ESTIMATION (Transfer Model)`.

### 8. Automated Enterprise Quality Assurance Suite (63 / 63 Passing Tests)
* **Pre-existing State:** Regression test suite had failing tests and lacked verification for sovereign layers.
* **Our Re-Engineering:** 
  * Authored [`tests/test_phase2_sovereign_gis.py`](tests/test_phase2_sovereign_gis.py) and updated existing test harnesses.
  * Verified 63 tests across 8 test suites covering VS Code-style activity rails, Shoelace geometry formulas, design system tokens, satellite orbital cutoffs, fail-closed telemetry, 28 States + 8 UTs administrative indexing, and BSA 2023 §63 screening labels.
  * Achieved **100% test pass rate (63/63 passed in 8.38s)**.

---

## What the Entire BHU LOKA Software Does (Full System Capabilities)

BHU LOKA (भूलोक) is an autonomous sovereign Earth System, Multi-Hazard Intelligence, and 2D/3D GIS Workstation. The platform integrates planetary WebGL visualization, hardware-accelerated 2D mapping, cadastral legal screening, precision agriculture, and physics-informed remote sensing machine learning into a single cohesive system.

```
                                      BHU LOKA (भूलोक) SYSTEM OVERVIEW
                                      
  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                   WORKSTATION INTERFACES & MODULES                                     │
  │                                                                                                        │
  │  [3D Planetary Digital Twin]      [2D Sovereign GIS]              [Land Intelligence Studio]           │
  │  Three.js WebGL2 Globe            Hardware Leaflet Engine         BSA 2023 §63 Cadastral Screening     │
  │  • Sovereign 36 States/UTs        • 28 States & 8 UTs (724 Dist)  • 5 Core AOIs (Patna, Varanasi, etc.)│
  │  • 186 Live Spacecraft Orbits     • Sovereign State Selector Card • 4-Quadrant Legal Spatial Audit     │
  │  • 30m Micro-DEM Terrain          • Sentinel-1 SAR Deluge Layer   • Bi-temporal Decadal Swipe          │
  │  • 2D Crop to 3D Relief Extrusion • 14 Scientific Layer Overlays  • 3D Shoreline Perspective           │
  │  • Solar Day/Night Terminator     • Radar Pixel Backscatter HUD   • Printable Government PDF Dossier   │
  │                                                                                                        │
  │  [Precision Agriculture Engine]   [Multi-Hazard Explorer]         [Spatial AI & Deluge Engine]         │
  │  Field Parcel Cadastre Drawer     8 Sovereign Hazard Categories   Physical SAR + Spatial RF            │
  │  • Multi-vertex Plot Drawer       • Flood, Heatwave, Landslide    • Dihedral Double-Bounce Surge       │
  │  • Shoelace Acre/Ha Geometry      • Forest Fire, Drought, Cyclone • Otsu Bimodal Thresholding          │
  │  • Crop Lifecycle Stage Tracking  • Glacial Outburst, Air Poll.   • 5-Fold SBCV Random Forest          │
  │  • GeoJSON Field Export           • Strict Fail-Closed Integrity  • Tree-SHAP Feature Explainability   │
  └───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                      │
                                                      ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                  FASTAPI TELEMETRY & INFERENCE SERVER                                  │
  │                                                                                                        │
  │   POST /api/v1/predict-flood          GET /api/v1/live-telemetry          POST /api/v1/query           │
  │   • Spatial RF Model (.joblib)        • Open-Meteo Multi-Variable         • Hybrid BM25 + FAISS Vector │
  │   • Dihedral Double-Bounce Physics    • GloFAS River Discharge Data       • Grounded Scientific RAG    │
  │   • Tree-SHAP Feature Attribution     • CelesTrak SGP4 Orbit Engine       • Zero-Hallucination Guard   │
  └───────────────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                      │
                                                      ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                      DATA & REMOTE SENSING ASSETS                                      │
  │                                                                                                        │
  │   • Copernicus Sentinel-1 C-SAR       • Copernicus GLO-30 DEM (30m)       • Survey of India Vectors    │
  │   • NASA MODIS LST (MOD11A1)          • WorldPop 2020 Demographics        • GADM v4.1 District Data    │
  └────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Module 1: 3D Sovereign Earth & Holographic Digital Twin (`index.html`)
* **Sovereign India Boundary Lock:** Renders the complete, authentic sovereign boundary of India (including Jammu & Kashmir, Ladakh, and Arunachal Pradesh) along with 36 State/UT administrative borders locked directly to the rotating Three.js WebGL2 sphere.
* **Real-Time Ephemeris Spacecraft Tracking:** Propagates orbits for 186+ active satellites (Copernicus Sentinel-1/2/5P, NASA-ISRO NISAR, Landsat-8/9, NOAA, Starlink, and ISS) using SGP4 orbital mechanics with automated fail-closed timeouts.
* **Astronomical Day/Night & FLIR Thermal:** Renders real-time solar declination, day-night terminators, specular ocean reflections, and simulated forward-looking infrared (FLIR) thermal heatwave emissions.
* **Micro-DEM Terrain Hologram:** Drapes zoom-14 high-resolution satellite imagery over Copernicus GLO-30 elevation models, color-coding critical sink basins (<46m AMSL), ponding saucer basins (48-52m AMSL), and elevated natural levee ridges (>52m AMSL).
* **Interactive 2D-to-3D Terrain Cropper:** Allows operators to draw a bounding box on the 2D map and immediately extrude the chosen area into a full 3D interactive holographic terrain mesh.
* **Temporal Time Machine:** Scrub through historical satellite and environmental timelines from antiquity to the present day.

### Module 2: Sovereign Pan-India 2D GIS Workstation (`bhu_loka_leafmap_interactive.html`)
* **Complete 28 States & 8 UTs Explorer:** Seamlessly explore all 36 administrative units and 724 districts of India via the `#sovereign-state-select` dropdown with alphabetical optgroups.
* **State Dossier Cards:** Selecting a state highlights its polygon border, zooms to its geodetic bounding box, and displays a floating glassmorphic dossier card displaying its capital, local vernacular name, district count, and data attribution.
* **Multi-Basemap Suite:** 1-click toggling between Esri World Imagery (high-resolution optical), OpenStreetMap (cartographic street network), CartoDB Dark Matter (low-light analysis), and NASA GIBS (near real-time atmospheric layers).
* **14 Scientific Overlay Layers:**
  1. *Sentinel-1 SAR Deluge Layer:* Isolates $26.54\\text{ km}^2$ of inundated urban terrain.
  2. *Copernicus 30m DEM Elevation:* Micro-topographical contour and elevation profiling.
  3. *Multi-Hazard Compound Layer:* Concurrent heatwave, flood, and landslide vulnerability.
  4. *Safe Elevated Corridors:* Elevated ridge zones for evacuation routing.
  5. *Heat Area (MODIS LST):* Land surface thermal anomaly contours.
  6. *Land Use / Land Cover (LULC):* Urban built-up, waterbodies, vegetation, and fallow land.
  7. *Infrastructure & Critical Assets:* Hospitals, power stations, bridges, and emergency shelters.
  8. *Buildings, Roads & Greenery:* Granular open spatial vector datasets.
* **Pixel Backscatter HUD:** Real-time on-hover radar backscatter readout displaying calibrated $\\sigma^0_{\\text{dB}}$ values and flood probabilities.
* **QGIS/ArcGIS Export:** One-click export of observed inundation and parcel vectors in standard GeoJSON format.

### Module 3: Land & Cadastral Intelligence Studio (`Assets/vendor/bhu_loka_urban_studio.js`)
* **Map-First Spatial Audit:** Real-time spatial analysis across 5 key Areas of Interest (AOIs): Patna (Rajendra Nagar, Gandhi Maidan, IIT Patna), Varanasi, Hampi, and Hyderabad (Hussain Sagar, Osman Sagar).
* **Dynamic AOI Bounding:** Screen-based, circular, rectangular, or custom multi-point polygon selection from 500m to 5km radius.
* **4-Quadrant Multi-Spectral Audit:**
  1. *Optical Satellite High-Resolution View*
  2. *Cadastral Full Tank Level (FTL) & Revenue Boundary*
  3. *Digital Elevation Buffer & Inflow Sinks*
  4. *Potential Spatial Overlap Footprint*
* **Bi-Temporal Decadal Satellite Swipe:** Interactive before/after split-screen swipe comparing historical baseline imagery against modern satellite passes.
* **3D Shoreline Perspective:** WebGL-rendered 3D elevation buffer visualizing building elevations relative to lake bed contours.
* **Bharatiya Sakshya Adhiniyam, 2023 (BSA §63) Compliance:** Generates official government-ready electronic evidence dossiers containing cryptographic SHA-256 hashes, acquisition timestamps, sensor calibration levels, and statutory technical screening disclaimers.

### Module 4: Precision Agriculture & Farmer Cadastre Module
* **Interactive Parcel Drawer:** Farmers and agro-climatologists can draw custom plot boundaries directly on satellite imagery with live vertex snapping and editing.
* **Shoelace Geodesic Geometry:** Automatically computes parcel area in both hectares and acres along with total boundary perimeter.
* **Crop Growth Stage Tracker:** Categorize parcels by active phenological stage: Vegetative, Flowering, Harvesting, or Fallow.
* **Independent / Shared Land Ownership:** Track land tenure, irrigation status, and soil moisture indices.
* **Direct GeoJSON Export:** Export field geometries for inclusion in national agrarian registries, PM-KISAN, or parametric crop insurance claims.

### Module 5: Multi-Hazard Location Intelligence Explorer
* **8 Sovereign Disaster Categories:**
  1. *Pluvial & Fluvial Flood:* Copernicus Sentinel-1 SAR & GloFAS river discharge.
  2. *Extreme Heatwave:* NASA MODIS Land Surface Temperature ($>42^\\circ\\text{C}$ thresholds).
  3. *Landslide Vulnerability:* Topographic slope steepness & monsoon saturation indices.
  4. *Active Forest Fire:* S-NPP VIIRS 375m thermal fire beacons.
  5. *Agricultural Drought:* MODIS Vegetation Condition Index (VCI) & NDVI anomalies.
  6. *Tropical Cyclone:* Storm track, barometric depression, and coastal surge buffers.
  7. *Glacial Lake Outburst Flood (GLOF):* Himalayan cryosphere melt and lake expansion tracking.
  8. *Severe Air Pollution:* Sentinel-5P TROPOMI Nitrogen Dioxide ($\\text{NO}_2$) & aerosol optical depth.
* **Zero Synthetic Data Policy:** Strict fail-closed architecture ensures that whenever a real-time sensor feed is unavailable, the UI clearly displays `UNAVAILABLE` rather than generating fabricated data.

### Module 6: Empirical SAR & Physical Deluge Engine
* **Patna September 2019 Disaster Study:** Built upon the catastrophic 72-hour rainstorm ($342.5\\text{ mm}$) that submerged Patna under $1.5\\text{ m}$ to $3.0\\text{ m}$ of standing water while Ganga river-lock crest ($49.5\\text{ m}$ AMSL) prevented gravity drainage.
* **Optical Blindness Penetration:** Demonstrates why optical satellites (Landsat, Sentinel-2) failed due to 100% monsoon cloud cover, while Sentinel-1 C-band microwaves ($5.405\\text{ GHz}$) penetrated unbroken cloud decks.
* **Urban Dihedral Corner-Reflector Modeling:** Isolates the physical double-bounce retro-reflection between water-covered streets and vertical building walls ($\\\\Delta\\\\sigma^0 \\\\ge +1.5\\\\text{ dB}$).
* **Automated Otsu Thresholding:** Optimally separates open water specular scattering ($\\\\tau^* = -3.80\\\\text{ dB}$) from non-flooded surfaces.

### Module 7: Spatial Machine Learning (5-Fold SBCV Random Forest)
* **Model Checkpoint:** `Models/Checkpoints/bhu_loka_spatial_rf_v1.joblib` (100 trees, 7 physical & SAR features, 21.98 MB).
* **Feature Vector:**
  1. $\\sigma^0_{\\text{pre}}$ (Pre-flood baseline radar backscatter)
  2. $\\sigma^0_{\\text{post}}$ (Peak-deluge radar backscatter)
  3. $\\Delta\\sigma^0$ (Differential logarithmic backscatter)
  4. Copernicus 30m GLO-30 Elevation
  5. Topographic Wetness Index (TWI)
  6. Distance to drainage channels / Ganga River
  7. Built-up surface density
* **Spatial Block Cross-Validation:** Eliminates spatial autocorrelation leakage by splitting 60,000 spatial samples into spatially disjoint geographical blocks:
  * **Mean ROC-AUC:** $0.7498 \\pm 0.0497$
  * **Mean F1-Score:** $0.6530$
  * **Mean Accuracy:** $68.88\\%$
  * **Mean Brier Score:** $0.2003$
* **Explainable AI (Tree-SHAP):** Identifies $\\sigma^0_{\\text{post}}$ ($36.8\\%$) and $\\Delta\\sigma^0$ ($29.9\\%$) as the primary predictive drivers.

### Module 8: Enterprise FastAPI Telemetry & Grounded RAG Server
* **REST Endpoints:**
  * `POST /api/v1/predict-flood`: Sub-second spatial flood inference for any queried coordinate.
  * `GET /api/v1/live-telemetry`: Aggregates Open-Meteo, GloFAS discharge, and CelesTrak orbital state vectors.
  * `POST /api/v1/query`: Grounded geospatial intelligence RAG using hybrid BM25 + FAISS vector search with zero hallucination.

### Module 9: Mobile-First Responsive Workstation Shell
* **Full Mobile Parity:** Dedicated bottom navigation rail (HOME, HAZARD, AI, FARMER, LAND STUDIO).
* **Touch-Optimized Drawers:** Farm parcel drawers, layer selectors, and hazard inspectors operate smoothly on smartphones, tablets, and desktop workstations.
* **Accessibility:** Full WCAG AA compliance with visible focus rings, ARIA labels, and iOS Safari 16px font zoom protection.

---

## Remote Sensing & Mathematical Formulation

### 1. Radiometric Calibration (DN to $\\sigma^0$)
Raw digital numbers ($DN$) from Sentinel-1 Level-1 Ground Range Detected (GRD) products are converted to sigma-nought backscatter in decibels ($\\text{dB}$):

$$\\sigma^0 = \\frac{DN^2}{A_{\\sigma}^2} \\cdot \\sin(\\theta)$$

$$\\sigma^0_{\\text{dB}} = 10 \\cdot \\log_{10}(\\sigma^0)$$

### 2. Dual-Date Logarithmic Backscatter Difference ($\\Delta\\sigma^0$)
Differencing co-registered SAR scenes acquired before ($t_1 = \\text{2019-09-23}$) and at the peak of the deluge ($t_2 = \\text{2019-09-29}$):

$$\\Delta\\sigma^0 = \\sigma^0_{\\text{post}} - \\sigma^0_{\\text{pre}}$$

### 3. Urban Dihedral Corner-Reflector Backscatter Surge
In densely built residential sectors, standing floodwaters create dihedral retro-reflectors between street surfaces and vertical masonry walls, causing an anomalous backscatter surge:

$$\\sigma^0_{\\text{dihedral}} \\gg \\sigma^0_{\\text{dry}} \\implies \\Delta\\sigma^0 \\ge +1.5\\text{ dB}$$

### 4. Automated Bimodal Otsu Thresholding ($\\tau^*$)
The optimal threshold separating open inundated water surfaces from non-flooded terrain maximizes inter-class variance:

$$\\tau^* = \\arg\\max_{\\tau} \\left[ \\omega_0(\\tau) \\omega_1(\\tau) \\left( \\mu_0(\\tau) - \\mu_1(\\tau) \\right)^2 \\right]$$

### 5. Shoelace Geodesic Spherical Area Formula
For an agricultural or cadastral parcel defined by $n$ geodetic vertices $(\\phi_i, \\lambda_i)$ on a sphere of radius $R = 6371\\text{ km}$:

$$A = \\frac{R^2}{2} \\left| \\sum_{i=1}^{n} (\\lambda_{i+1} - \\lambda_i) \\cdot (\\sin \\phi_{i+1} + \\sin \\phi_i) \\right|$$

---

## Quantitative Validation Matrix & Satellite Metadata

### 1. Spatial Study Area Extents
* **Total Study Domain:** $444.68\\text{ km}^2$
* **Permanent Water (Ganga River):** $113.82\\text{ km}^2$
* **Newly Inundated Land ("Naya Paani"):** $26.54\\text{ km}^2$
* **Total Flood Inundation Mask:** $140.36\\text{ km}^2$

### 2. 5-Fold Spatial Block Cross-Validation (SBCV) Metrics
* **Total Dataset:** 60,000 spatial samples
* **Mean ROC-AUC:** $0.7498 \\pm 0.0497$
* **Mean F1-Score:** $0.6530$
* **Mean Accuracy:** $68.88\\%$
* **Mean Brier Score:** $0.2003$
* **Individual Folds:**
  * Fold 1: ROC-AUC $0.6855$, Accuracy $65.41\\%$
  * Fold 2: ROC-AUC $0.7900$, Accuracy $71.18\\%$
  * Fold 3: ROC-AUC $0.7999$, Accuracy $72.04\\%$
  * Fold 4: ROC-AUC $0.7802$, Accuracy $70.85\\%$
  * Fold 5: ROC-AUC $0.6937$, Accuracy $64.92\\%$

### 3. Exact Copernicus Sentinel-1 Satellite Metadata (ASF Vertex)

| Scene Role | Complete Scene Identifier | Sensor Platform | Acquisition Timestamp (UTC) | Pass Direction | Polarizations |
|---|---|---|---|---|---|
| **Pre-Flood Baseline Scene** | `S1A_IW_GRDH_1SDV_20190923T002026_20190923T002051_029141_034EEC` | Copernicus Sentinel-1A | **2019-09-23 00:20:38 UTC** | Descending | VV + VH |
| **Peak Flood Deluge Scene** | `S1B_IW_GRDH_1SDV_20190929T001924_20190929T001949_018245_0225AB` | Copernicus Sentinel-1B | **2019-09-29 00:19:37 UTC** | Descending | VV + VH |

---

## Repository Structure

```
BHU_LOKA/
├── Assets/
│   ├── css/                                # Glassmorphism tokens & design styles
│   ├── evidence/                           # Verified headless browser evidence captures
│   └── vendor/
│       ├── bhu_loka_urban_studio.js        # BSA 2023 §63 Land & Cadastral Intelligence Studio
│       ├── bhu_loka_flood_intel.js         # SAR empirical science & Otsu thresholding
│       └── bhu_loka_ai.js                  # Grounded AI agent & tool routing
├── Data/
│   ├── 01_Raw_Satellite_Scenes/            # Copernicus Sentinel-1 Level-1 GRD scenes
│   ├── 02_DEM_Elevation_Profiles/          # Copernicus GLO-30 30m elevation tiles
│   └── 08_Processed_Outputs/
│       ├── bhu_loka_india_admin_index.js   # Pan-India 36 States/UTs & 724 Districts
│       ├── bhu_loka_real_geodata.js        # Sovereign boundary GeoJSONs & Bihar 38 districts
│       └── sar_flood_inundation_patna_2019.geojson # Calibrated flood inundation vector
├── Models/
│   ├── 01_Spatial_ML/                      # Spatial Block Cross-Validation & training scripts
│   ├── 04_Hybrid_RAG/                      # FastAPI telemetry backend & FAISS RAG engine
│   └── Checkpoints/
│       └── bhu_loka_spatial_rf_v1.joblib   # Trained 100-tree Spatial Random Forest (21.98 MB)
├── public/                                 # Deployed Firebase static assets & endpoints
├── tests/                                  # Automated Pytest suite (63/63 passing)
│   ├── test_phase2_sovereign_gis.py        # 28 States + 8 UTs sovereign GIS tests
│   ├── test_e2e_workstation.py             # 4-tier E2E workstation tests
│   ├── test_flood_intel_and_cropper.py     # SAR intelligence & 3D cropper tests
│   └── test_site_analytics_engine.py       # BSA 2023 screening & API tests
├── index.html                              # 3D Sovereign Earth & Digital Twin Workstation
├── bhu_loka_cyber_dashboard.html           # Full-featured 3D Cyber Command Workstation
├── bhu_loka_leafmap_interactive.html       # 2D Sovereign Pan-India GIS Workstation
├── Launch_BhuLoka_FullStack.bat            # 1-Click Windows Full-Stack Launcher
└── README.md                               # Platform documentation
```

---

## Quickstart & Local Reproduction

### Option A: Standalone Python Server & Automated Pytest Suite (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/Amourhoffen/BhuLoka.git
cd BhuLoka

# 2. Install dependencies
pip install fastapi uvicorn numpy scikit-learn joblib httpx faiss-cpu pytest beautifulsoup4

# 3. Run the automated test suite (63/63 passing)
pytest tests/ -v

# 4. Start the FastAPI backend
python Models/04_Hybrid_RAG/enterprise_rag_app/main.py
```

### Option B: 1-Click Windows Full-Stack Launcher

Double-click `Launch_BhuLoka_FullStack.bat` in the repository root. This automatically:
1. Starts the FastAPI Telemetry & Spatial ML Inference Server on `http://127.0.0.1:8000`.
2. Launches the Chromium Sovereign Workstation in app mode at full resolution.

```cmd
.\\Launch_BhuLoka_FullStack.bat
```

### Option C: Run Spatial ML Hazard Inference via CLI

```bash
python Models/01_Spatial_ML/predict_hazard.py "rajendra nagar"
```

---

## Academic Citation

If you utilize BHU LOKA, its empirical SAR methodology, spatial machine learning models, or the Patna flood dataset in your research, please cite:

```bibtex
@article{kumar2026bhuloka,
  title={BHU LOKA: Sovereign Earth System, Multi-Hazard Intelligence, and Urban Dihedral Corner-Reflector Flood Inundation Workstation},
  author={Kumar, Prince and Priyadarshini, Payal and Rustogi, Pallav},
  institution={Indian Institute of Technology Patna & Indian Institute of Information Technology, Design and Manufacturing Jabalpur},
  year={2026},
  url={https://github.com/Amourhoffen/BhuLoka}
}
```

---
<img width="1460" height="768" alt="Sovereign GIS Platform View" src="https://github.com/user-attachments/assets/b737f31c-cf9e-43ab-bbef-486fec786c2f" />
<img width="1460" height="815" alt="3D Workstation View" src="https://github.com/user-attachments/assets/8c9d59bf-795d-4151-ba35-2368b9b251bc" />

## License & Open-Source Sovereignty

This project is licensed under the **MIT Open Source License** — see the [LICENSE](LICENSE) file for details.  
*Dedicated to the citizens of Patna, Bihar and open-source scientific disaster resilience worldwide.*
"""

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme_content)

print(f'Successfully generated definitive README.md ({len(readme_content)} chars, {len(readme_content.splitlines())} lines)!')
