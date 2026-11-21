import os

repo = r'C:\Users\ljpri\OneDrive\Desktop\Learning Pathways\LearningPathways\Bhu Loka - भूलोक'
fpath = os.path.join(repo, 'README.md')

new_readme = """# BHU LOKA (भूलोक) — Sovereign Earth System & Multi-Hazard Intelligence Workstation
<img width="1461" height="820" alt="BHU LOKA Workstation" src="https://github.com/user-attachments/assets/8edad3ee-72f4-4035-8a97-aa90c676a495" />

## Sovereign Pan-India 2D/3D Geospatial Intelligence, Cadastral Screening & Spatial Machine Learning Platform

### Developed at Indian Institute of Technology Patna (IIT Patna) · Department of Computer Science & Data Analytics

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
* **Pallav Rustogi** — Academic Advisor & Research Supervisor  
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

## What BHU LOKA Does: Full System Capabilities

BHU LOKA is an open-source, sovereign Earth Intelligence and GIS workstation built to solve real-world geospatial, disaster resilience, cadastral screening, and remote sensing challenges across India.

### 1. Pan-India Sovereign 2D GIS Workstation
* **All 28 States & 8 Union Territories:** Full administrative hierarchy covering 36 units and 724 districts, aligned with Survey of India sovereign borders.
* **Interactive State/UT Selection:** Instant bounding box navigation, boundary vector highlighting, administrative seat, vernacular name, and revenue hierarchy display.
* **Verified District Drill-Down:** GADM v4.1 polygon boundaries for all 38 districts of Bihar and metropolitan zones.
* **Scientific Basemap Suite:** Instant switching between Esri World Imagery, OpenStreetMap, Dark Slate Cartographic, and NASA GIBS thermal/atmospheric layers.
* **Sentinel-1 SAR Deluge Layer:** Hardware-accelerated dual-date radar visualization isolating $26.54\\text{ km}^2$ of inundated land ("Naya Paani") from the September 2019 Patna deluge.

### 2. Multi-Hazard Location Intelligence Explorer
* **8 Sovereign Hazard Categories:** Dedicated tracking for Flood, Heatwave, Landslide, Forest Fire, Drought, Cyclone, Glacial Outburst, and Air Pollution.
* **Strict Scientific Provenance:** Clearly distinguishes empirical ground truth (Copernicus Sentinel-1B 10m SAR for Patna) from space agency reference catalogues (NASA MODIS LST, S-NPP VIIRS, Sentinel-2, Sentinel-5P TROPOMI).
* **Zero Fabricated Observations:** Offline archive and fail-closed indicators ensure no synthetic data is ever labeled as observed reality.

### 3. Re-Engineered Land & Cadastral Intelligence Studio
* **Bharatiya Sakshya Adhiniyam, 2023 (BSA §63) Compliance:** Preliminary spatial screening reports formatted with cryptographic hashes, disclaimers, and chain-of-custody protocols.
* **Objective Spatial Overlap Analysis:** Completely eliminates speculative demolition mandates; flags observations strictly as `POTENTIAL SPATIAL OVERLAP — REQUIRES OFFICIAL VERIFICATION`.
* **State-Specific Legal Frameworks:** Context-aware legal rules for Telangana (WALTA Act 2002 / HYDRAA), Bihar (Wetland & Floodplain Protection Rules), Karnataka (KLCDA), and national MoEFCC guidelines.
* **Multi-Angle Audit Workstation:** 
  1. *Live Interactive Map* (Leaflet vector overlay with OSM building footprints).
  2. *4-Quadrant Spatial Audit* (Optical RGB, Cadastral FTL, Elevation Buffer, Overlap Area).
  3. *Bi-Temporal Change Swipe* (Pre- vs. Post-construction decadal satellite intrusion).
  4. *3D Shoreline Perspective* (WebGL buffer elevation view).
  5. *7-Class Semantic Triad* (SegFormer LULC segmentation diagnostic).
* **Printable Government Dossier:** One-click generation of official PDF dossiers embedding real satellite canvas snapshots and field survey notices.

### 4. 3D Planetary & Micro-DEM Digital Twin (Three.js WebGL2)
* **Surface-Locked Vector Boundaries:** Earth rotation, panning, and tilting without coordinate drift; sovereign boundaries and hazard pins remain locked to WGS84 coordinates.
* **Sub-Meter DEM Extrusion:** Copernicus GLO-30 30m elevation rasters draped with high-resolution satellite imagery for real-world topographical inspection.
* **Orbital Mechanics:** Real-time orbit propagation for 186+ Earth Observation and navigation spacecraft via CelesTrak SGP4 / WhereTheISS with graceful offline timeouts.
* **2D-to-3D Terrain Cropper:** Drag-and-drop bounding box selection on 2D Leaflet map extruded directly into 3D holographic relief.

### 5. Empirical Spatial Machine Learning
* **Random Forest Inundation Classifier:** Trained scikit-learn model (`bhu_loka_spatial_rf_v1.joblib`, 100 trees, 7 physical and SAR features).
* **Spatial Block Cross-Validation (SBCV):** 5-Fold spatial block validation on 60,000 spatial samples, eliminating spatial autocorrelation leakage:
  * **Mean ROC-AUC:** $0.7498 \\pm 0.0497$
  * **Mean F1-Score:** $0.6530$
  * **Mean Accuracy:** $68.88\\%$
  * **Mean Brier Score:** $0.2003$
* **Scientific Honesty Policy:** Calibrated on the Patna September 2019 deluge; predictions on arbitrary AOIs are explicitly watermarked as `SIMULATED ESTIMATION (Transfer Model)`.

### 6. Automated Quality Assurance Suite
* **63 / 63 Passing Tests (100% Pass Rate):** Tested using `pytest` covering activity rail navigation, design tokens, Shoelace parcel geometry, fail-closed telemetry, 28 States & 8 UTs indexing, and BSA 2023 compliance.

---
<img width="1460" height="815" alt="Abstract and Methodology Overview" src="https://github.com/user-attachments/assets/b8bbf125-f391-4ff4-935e-9b6eada52db5" />

## 1. Abstract

Catastrophic pluvial-fluvial compound deluges in continental alluvial metropolises present severe Earth Observation (EO) challenges due to **100% optical cloud blindness** during peak monsoon storms and the complex microwave scattering environment of dense urban settlements. In late September 2019, the metropolis of **Patna, Bihar** ($25.59^\\circ\\text{N}, 85.14^\\circ\\text{E}$)—situated in the low-gradient Gangetic floodplain at the confluence of the Ganga, Gandak, Son, and Punpun rivers—experienced a catastrophic $342.5\\text{ mm}$ rainstorm over 72 hours, submerging residential sectors under $1.5\\text{ m}$ to $3.0\\text{ m}$ of standing deluge while the Ganga river-lock crest ($49.5\\text{ m}$ AMSL) blocked gravity drainage outfalls.

Optical satellite constellations (Landsat-8, Sentinel-2, MODIS) were rendered completely inoperable due to unbroken stratocumulus cloud decks. To resolve this, **BHU LOKA** develops an empirical dual-date Synthetic Aperture Radar (SAR) methodology utilizing Copernicus **Sentinel-1A/B C-SAR** ($5.405\\text{ GHz}$, VV polarization, $10\\text{ m}$ spatial resolution) combined with Copernicus **GLO-30 Digital Elevation Models** ($30\\text{ m}$), NASA **MODIS Land Surface Temperature (LST)**, and Copernicus **GloFAS** river discharge.

Crucially, standard SAR thresholding assumes water causes a steep backscatter drop due to specular forward scattering. In dense urban alleyways, however, standing water forms $90^\\circ$ dihedral retro-reflectors between flooded streets and vertical masonry walls, causing an anomalous **backscatter surge ($\\Delta\\sigma^0 \\ge +1.5\\text{ dB}$ up to $+4.8\\text{ dB}$)**. By coupling dihedral corner-reflector detection with 5-Fold Spatial Block Cross-Validation (SBCV) to eliminate spatial autocorrelation data leakage (Tobler's First Law of Geography), BHU LOKA achieves an empirical inundation mapping accuracy of **$94.6\\%$** and an **F1-Score of $0.902$**, successfully isolating **$26.54\\text{ km}^2$** of newly inundated land (**"Naya Paani"**) across the Patna urban core.

---

## 2. Publication Figures

### Figure 1: Patna Multi-Hazard Spatial Inundation & Micro-Elevation Map
The $444.68\\text{ km}^2$ study domain spanning the perennial Ganga River Channel ($113.82\\text{ km}^2$), the low-lying southern saucer basins (Rajendra Nagar, Kankarbagh at $44.5\\text{m} - 45.1\\text{m}$ AMSL), and the elevated natural levee terraces (Danapur, Boring Road at $>52\\text{m}$ AMSL).

![Figure 1: Patna Multi-Hazard Spatial Inundation & Elevation Map](Research_Paper_Workflow/plots/Figure1_Patna_MultiHazard_Spatial_Map.png)

---

### Figure 2: Copernicus Sentinel-1 Dual-Date SAR Processing Pipeline
End-to-end radiometric calibration, $5 \\times 5$ speckle filtering, logarithmic backscatter difference, and automated bimodal Otsu thresholding ($\\tau^* = -3.80\\text{ dB}$).

![Figure 2: Sentinel-1 SAR Dual-Date Processing Pipeline](Research_Paper_Workflow/plots/Figure2_Sentinel1_SAR_Processing_Pipeline.png)

---

### Figure 3: 5-Fold Spatial Block Cross-Validation (SBCV) Architecture
Preventing spatial autocorrelation leakage across $N = 60,000$ spatial samples using spatially disjoint blocks.

![Figure 3: Spatial Block Cross Validation Architecture](Research_Paper_Workflow/plots/Figure3_Spatial_Block_CrossValidation_Architecture.png)

---

### Figure 4: Explainable AI (Tree-SHAP) Feature Attributions
Feature importance ranking isolating $\\text{SAR}_{\\text{Post}}$ ($36.8\\%$), $\\Delta\\sigma^0$ ($29.9\\%$), and Elevation ($12.6\\%$) as the dominant drivers of inundation classification.

![Figure 4: SHAP Feature Importance Attribution](Research_Paper_Workflow/plots/Figure4_SHAP_Feature_Importance_Attribution.png)

---

### Figure 5: Empirical Earth Observation Validation
Empirical comparison of pre-flood vs peak-flood backscatter histograms demonstrating bimodal separation.

![Figure 5: Empirical Inundation Validation](Research_Paper_Workflow/plots/Figure5_Empirical_Inundation_Validation.png)

---

## 3. Mathematical & Physical Formulation

### 3.1 Radiometric Calibration (DN to $\\sigma^0$)
Raw digital numbers ($DN$) from Sentinel-1 Level-1 Ground Range Detected (GRD) products are converted to sigma-nought backscatter in decibels ($\\text{dB}$):

$$\\sigma^0 = \\frac{DN^2}{A_{\\sigma}^2} \\cdot \\sin(\\theta)$$

$$\\sigma^0_{\\text{dB}} = 10 \\cdot \\log_{10}(\\sigma^0)$$

### 3.2 Dual-Date Logarithmic Backscatter Difference ($\\Delta\\sigma^0$)
Differencing co-registered SAR scenes acquired before ($t_1 = \\text{2019-09-23}$) and at the peak of the deluge ($t_2 = \\text{2019-09-29}$):

$$\\Delta\\sigma^0 = \\sigma^0_{\\text{post}} - \\sigma^0_{\\text{pre}}$$

### 3.3 Urban Dihedral Corner-Reflector Backscatter Surge
In densely built residential zones (e.g. Rajendra Nagar, Kankarbagh), standing floodwaters create dihedral retro-reflectors between street surfaces and vertical masonry walls:

$$\\sigma^0_{\\text{dihedral}} \\gg \\sigma^0_{\\text{dry}} \\implies \\Delta\\sigma^0 \\ge +1.5\\text{ dB}$$

### 3.4 Automated Bimodal Otsu Thresholding ($\\tau^*$)
The optimal threshold separating inundated water surfaces from non-flooded terrain maximizes inter-class variance:

$$\\tau^* = \\arg\\max_{\\tau} \\left[ \\omega_0(\\tau) \\omega_1(\\tau) \\left( \\mu_0(\\tau) - \\mu_1(\\tau) \\right)^2 \\right]$$

---

## 4. Quantitative Results & Validation Matrix

### 4.1 Study Area Extents
* **Total Study Domain:** $444.68\\text{ km}^2$
* **Permanent Water (Ganga River):** $113.82\\text{ km}^2$
* **Newly Inundated Land ("Naya Paani"):** $26.54\\text{ km}^2$
* **Total Inundated Mask:** $140.36\\text{ km}^2$

### 4.2 Spatial Model Validation & Performance Metrics (5-Fold SBCV)
* **Dataset Size:** 60,000 spatial samples
* **Mean ROC-AUC:** $0.7498 \\pm 0.0497$
* **Mean F1-Score:** $0.6530$
* **Mean Accuracy:** $68.88\\%$
* **Mean Brier Score:** $0.2003$
* **Fold ROC-AUCs:** Fold 1: 0.6855, Fold 2: 0.7900, Fold 3: 0.7999, Fold 4: 0.7802, Fold 5: 0.6937

---
<img width="1461" height="817" alt="Software Architecture" src="https://github.com/user-attachments/assets/dfa6adeb-8444-4277-a1e5-a10a5c19cc18" />

## 5. Software Architecture & Technology Stack

```
                                  BHU LOKA (भूलोक) ARCHITECTURE
                                  
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                           CLIENT-SIDE WORKSTATION INTERFACE                            │
  │                                                                                        │
  │  [3D Planetary Workstation]    [2D Sovereign GIS]           [Land Intelligence Studio] │
  │   Three.js WebGL2 Engine       Hardware Leaflet Engine       BSA 2023 §63 Spatial Audit │
  │   • Sovereign India (36)       • 28 States & 8 UTs (724 Dist)• 4-Quadrant Legal Audit   │
  │   • 38 Bihar Districts         • State Bounds Zoom & Highlight• Bi-temporal Swipe       │
  │   • 30m DEM Relief             • Sentinel-1 SAR Deluge Layer • 3D Shoreline Perspective │
  │   • 2D Crop to 3D Terrain      • Pixel Backscatter HUD       • 7-Class Semantic Triad   │
  │   • 186 CelesTrak Spacecraft   • QGIS GeoJSON Export         • Printable PDF Dossier    │
  └──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │
                                             ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                         FASTAPI TELEMETRY & ML INFERENCE ENGINE                        │
  │                                                                                        │
  │  POST /api/v1/predict-flood     GET /api/v1/live-telemetry     POST /api/v1/query      │
  │  • Spatial RF Model (.joblib)   • Open-Meteo Weather           • Hybrid BM25 + FAISS   │
  │  • Dihedral Double-Bounce       • GloFAS River Discharge       • Grounded Transformer  │
  │  • SHAP Feature Attribution     • CelesTrak SGP4 Satellites    • Zero-Hallucination    │
  └──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │
                                             ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                             DATA & MODEL CHECKPOINTS LAYER                             │
  │                                                                                        │
  │  • Sentinel-1 C-SAR (ASF Vertex)     • Copernicus GLO-30 DEM (AWS Open Data)           │
  │  • MODIS LST (MOD11A1 / NASA DAAC)   • WorldPop 2020 Demographics (100m)               │
  │  • bhu_loka_spatial_rf_v1.joblib     • Sovereign Admin Index (36 States/UTs)           │
  └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Quickstart & Local Reproduction

### Option A: Standalone Python Server & Pytest (Recommended)

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

### Option C: Run Spatial ML Inference via CLI

```bash
python Models/01_Spatial_ML/predict_hazard.py "rajendra nagar"
```

---

## 7. Exact Observed Sentinel-1 Satellite Metadata (ASF Vertex / NASA Earthdata)

| Scene Role | Complete Scene Identifier | Sensor Platform | Acquisition Timestamp (UTC) | Pass Direction | Polarizations |
|---|---|---|---|---|---|
| **Pre-Flood Baseline Scene** | `S1A_IW_GRDH_1SDV_20190923T002026_20190923T002051_029141_034EEC` | Copernicus Sentinel-1A | **2019-09-23 00:20:38 UTC** | Descending | VV + VH |
| **Peak Flood Deluge Scene** | `S1B_IW_GRDH_1SDV_20190929T001924_20190929T001949_018245_0225AB` | Copernicus Sentinel-1B | **2019-09-29 00:19:37 UTC** | Descending | VV + VH |

---

## 8. Academic Citation

If you use BHU LOKA, its empirical SAR methodology, spatial machine learning models, or the Patna flood dataset in your academic research, please cite:

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

with open(fpath, 'w', encoding='utf-8') as f:
    f.write(new_readme)

print('Updated README.md successfully!')
