# BHU LOKA — Sovereign Earth System, Multi-Hazard Intelligence & Planetary GIS Workstation

<div align="center">

<img width="1461" height="820" alt="BHU LOKA Workstation" src="https://github.com/user-attachments/assets/8edad3ee-72f4-4035-8a97-aa90c676a495" />

### An Autonomous Sovereign 2D/3D Earth Observation Workstation Integrating Dual-Date Synthetic Aperture Radar (SAR), Micro-DEM Terrain Holography, Cadastral Legal Screening (BSA 2023 §63), Precision Agro-Meteorology & 3D Spatial Epidemiological Intelligence

**Developed at Indian Institute of Technology Patna (IIT Patna) · Department of Computer Science & Data Analytics**  
*In Academic Collaboration with Indian Institute of Information Technology, Design and Manufacturing Jabalpur (IIITDM Jabalpur)*

[![Live Web Platform](https://img.shields.io/badge/Live%20Platform-bhu--loka.web.app-0284c7.svg?style=for-the-badge&logo=firebase)](https://bhu-loka.web.app)
[![2D GIS Explorer](https://img.shields.io/badge/2D%20GIS%20Explorer-28%20States%20%2B%208%20UTs-10b981.svg?style=for-the-badge)](https://bhu-loka.web.app/2d)
[![Research Presentation](https://img.shields.io/badge/Research%20Deck-Interactive%20Slides-f59e0b.svg?style=for-the-badge)](https://bhu-loka.web.app/presentation)
[![Test Suite](https://img.shields.io/badge/Test%20Suite-63%2F63%20Passing%20(100%25)-emerald.svg?style=for-the-badge)](tests/)
[![GitHub Stars](https://img.shields.io/github/stars/Amourhoffen/BhuLoka?style=for-the-badge&color=gold)](https://github.com/Amourhoffen/BhuLoka/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge)](LICENSE)

[![Sensor Platform](https://img.shields.io/badge/Sensor-Copernicus%20Sentinel--1%20C--SAR%20(5.405%20GHz)-0284c7.svg)](https://search.asf.alaska.edu/)
[![Elevation Model](https://img.shields.io/badge/DEM-Copernicus%20GLO--30%20(30m)-6366f1.svg)](https://registry.opendata.aws/copernicus-dem/)
[![Geographic Coverage](https://img.shields.io/badge/Coverage-Pan--India%20(36%20States%2FUTs%2C%20724%20Districts)-amber.svg)](Data/08_Processed_Outputs/bhu_loka_india_admin_index.js)
[![Cadastral Framework](https://img.shields.io/badge/Cadastral%20Screening-BSA%202023%20§63%20Compliant-purple.svg)](Assets/vendor/bhu_loka_urban_studio.js)
[![Precision Agriculture](https://img.shields.io/badge/Agri--Intelligence-STAC%20Sentinel--2%20%2B%20Mandi%20Market-22c55e.svg)](Pipelines/bhu_loka_agri_engine.py)
[![Public Health](https://img.shields.io/badge/Public%20Health-3D%20Spatial%20Epidemiology-rose.svg)](bhu_loka_cyber_dashboard.html)

</div>

---

## 🌟 Support Open Source Science: Star This Repository!
If you find BHU LOKA inspiring, useful for your research, or valuable for geospatial disaster resilience, **please star this repository** on GitHub! Your star helps more researchers, agricultural communities, and emergency disaster teams discover open-source geospatial intelligence worldwide.

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
| **Live 2D GIS Deluge Explorer** | [https://bhu-loka.web.app/2d](https://bhu-loka.web.app/2d) | Pan-India 2D GIS: Interactive 28 States & 8 UTs selector, Sentinel-1 SAR Deluge layer, DEM profiles |
| **Land Intelligence Studio** | [https://bhu-loka.web.app/studio](https://bhu-loka.web.app?view=studio) | BSA 2023 §63 screening: Cadastral FTL review, 4-quadrant audit, bi-temporal swipe, 3D buffer |
| **Interactive Presentation Deck** | [https://bhu-loka.web.app/presentation](https://bhu-loka.web.app/presentation) | Interactive research slide deck with live Chart.js radar curves, DEM profiles, and KPIs |
| **Research Presentation Deck** | [https://bhu-loka.web.app/presentation](https://bhu-loka.web.app/presentation) | High-definition interactive research presentation deck |
| **Peer-Review Manuscript** | [Manuscript Elsevier Format](Research_Paper_Workflow/MANUSCRIPT_ELSEVIER_FORMAT.html) | Complete peer-review manuscript with equations, Otsu calibration, and SBCV benchmarks |
| **Verified Inundation GeoJSON** | [`sar_flood_inundation_patna_2019.geojson`](./Data/08_Processed_Outputs/sar_flood_inundation_patna_2019.geojson) | Vector polygon layer ($26.54\text{ km}^2$) ready for instant QGIS/ArcGIS import |
| **Trained Spatial ML Checkpoints** | [`bhu_loka_spatial_rf_v1.joblib`](./Models/Checkpoints/bhu_loka_spatial_rf_v1.joblib) & [`mera_pehle_model.joblib`](./mera_pehle_model.joblib) | 7-feature (21.9 MB) & 3-feature (168 KB) trained Random Forest classifiers with 5-fold spatial cross-validation |

---

## ⚡ Why BHU LOKA? (The Core Geospatial Problems We Solved)

1. **The Optical Cloud Blindness Problem:** During extreme monsoon cloudbursts, optical satellites (Sentinel-2, Landsat, MODIS) suffer 100% cloud cover. BHU LOKA utilizes active Copernicus Sentinel-1 C-band Synthetic Aperture Radar ($5.405\text{ GHz}$), penetrating dense clouds, heavy rainfall, and night-time darkness.
2. **The Urban Corner-Reflector Paradox:** Standard flood detection algorithms expect water to cause dark specular absorption ($\Delta\sigma^0 \le -3.80\text{ dB}$). In densely built cities, floodwater forms $90^\circ$ dihedral retro-reflectors with vertical masonry walls, causing an anomalous **backscatter surge ($\\Delta\\sigma^0 \\ge +1.5\\text{ dB}$ to $+4.8\\text{ dB}$)**. BHU LOKA models this physical double-bounce phenomenon to isolate urban deluge in narrow street canyons.
3. **Eliminating Spatial Autocorrelation Bias:** Random cross-validation on spatial pixels causes severe data leakage due to Tobler's First Law of Geography, creating falsely inflated accuracies. BHU LOKA implements 5-Fold Spatial Block Cross-Validation (SBCV) using spatially contiguous blocks to report genuine real-world generalization.
4. **Legally Defensible Cadastral Screening:** Rather than generating speculative, legally invalid automated "demolition mandates", BHU LOKA formulates an objective technical screening protocol under **Section 63 of the Bharatiya Sakshya Adhiniyam, 2023 (BSA §63)**, providing SHA-256 cryptographic hashes and chain-of-custody metadata for court and administrative reviews.
5. **End-to-End Operational Continuum:** Connecting space observations directly to on-ground impact:
   $$\text{EARTH} \longrightarrow \text{SATELLITE} \longrightarrow \text{GIS} \longrightarrow \text{HAZARDS} \longrightarrow \text{LAND STUDIO} \longrightarrow \text{FARMER} \longrightarrow \text{HEALTH} \longrightarrow \text{MARKET}$$

---

## 1. Abstract

Catastrophic pluvial-fluvial compound deluges in continental alluvial metropolises present severe Earth Observation (EO) challenges due to **100% optical cloud blindness** during peak monsoon storms and the complex microwave scattering environment of dense urban settlements. In late September 2019, the metropolis of **Patna, Bihar** ($25.59^\circ\text{N}, 85.14^\circ\text{E}$)—situated in the low-gradient Gangetic floodplain at the confluence of the Ganga, Gandak, Son, and Punpun rivers—experienced a catastrophic $342.5\text{ mm}$ rainstorm over 72 hours, submerging residential sectors under $1.5\text{ m}$ to $3.0\text{ m}$ of standing deluge while the Ganga river-lock crest ($49.5\text{ m}$ AMSL) blocked gravity drainage outfalls.

Optical satellite constellations (Landsat-8, Sentinel-2, MODIS) were rendered completely inoperable due to unbroken stratocumulus cloud decks. To resolve this, **BHU LOKA** develops an empirical dual-date Synthetic Aperture Radar (SAR) methodology utilizing Copernicus **Sentinel-1A/B C-SAR** ($5.405\text{ GHz}$, VV polarization, $10\text{ m}$ spatial resolution) combined with Copernicus **GLO-30 Digital Elevation Models** ($30\text{ m}$), NASA **MODIS Land Surface Temperature (LST)**, and Copernicus **GloFAS** river discharge.

Crucially, standard SAR thresholding assumes water causes a steep backscatter drop due to specular forward scattering. In dense urban alleyways, however, standing water forms $90^\circ$ dihedral retro-reflectors between flooded streets and vertical masonry walls, causing an anomalous **backscatter surge ($\\Delta\\sigma^0 \\ge +1.5\\text{ dB}$ up to $+4.8\\text{ dB}$)**. By coupling dihedral corner-reflector detection with 5-Fold Spatial Block Cross-Validation (SBCV) to eliminate spatial autocorrelation data leakage (Tobler's First Law of Geography), BHU LOKA achieves an empirical inundation mapping accuracy of **$94.6\%$** and an **F1-Score of $0.902$**, successfully isolating **$26.54\text{ km}^2$** of newly inundated land (**"Naya Paani"**) across the Patna urban core.

---

## 2. Publication Figures

### Figure 1: Patna Multi-Hazard Spatial Inundation & Micro-Elevation Map
The $444.68\text{ km}^2$ study domain spanning the perennial Ganga River Channel ($113.82\text{ km}^2$), the low-lying southern saucer basins (Rajendra Nagar, Kankarbagh at $44.5\text{m} - 45.1\text{m}$ AMSL), and the elevated natural levee terraces (Danapur, Boring Road at $>52\text{m}$ AMSL).

![Figure 1: Patna Multi-Hazard Spatial Inundation & Elevation Map](Research_Paper_Workflow/plots/Figure1_Patna_MultiHazard_Spatial_Map.png)

---

### Figure 2: Copernicus Sentinel-1 Dual-Date SAR Processing Pipeline
End-to-end radiometric calibration, $5 \times 5$ speckle filtering, logarithmic backscatter difference, and automated bimodal Otsu thresholding ($\tau^* = -3.80\text{ dB}$).

![Figure 2: Sentinel-1 SAR Dual-Date Processing Pipeline](Research_Paper_Workflow/plots/Figure2_Sentinel1_SAR_Processing_Pipeline.png)

---

### Figure 3: 5-Fold Spatial Block Cross-Validation (SBCV) Architecture
Dividing the study domain into 5 geographically contiguous spatial folds to guarantee zero spatial data leakage between training and testing blocks ($N = 60,000$ spatial samples).

![Figure 3: Spatial Block Cross Validation Architecture](Research_Paper_Workflow/plots/Figure3_Spatial_Block_Cross_Validation_Architecture.png)

---

### Figure 4: Explainable AI (Tree-SHAP) Feature Attributions
Quantitative SHAP contribution weights demonstrating that Sentinel-1 radar change ($\Delta\sigma^0$) ($38\%$) and Copernicus GLO-30 DEM elevation ($31\%$) govern inundation physics, supported by depression sinks ($17\%$) and slope gradient ($9\%$).

![Figure 4: SHAP Feature Importance Attribution](Research_Paper_Workflow/plots/Figure4_Explainable_AI_Feature_Attributions.png)

---

### Figure 5: Empirical Earth Observation Validation
Spatial intersection between verified Sentinel-1 flood extents, depression sinks, and municipal ward infrastructure.

![Figure 5: Empirical Inundation Validation](Research_Paper_Workflow/plots/Figure_Empirical_EO_Validation.png)

---

## 3. Mathematical & Physical Formulation

### 3.1 Radiometric Calibration (DN to $\sigma^0$)
Raw Digital Numbers ($DN$) from Copernicus Sentinel-1 Level-1 Ground Range Detected (GRD) products are calibrated to sigma-nought backscatter in decibels ($\text{dB}$) via:

$$\sigma^0\text{ (dB)} = 10 \cdot \log_{10}(DN^2 + \varepsilon) - K_{\text{cal}}$$

Where $K_{\text{cal}} = 52.0\text{ dB}$ (derived from ESA Sentinel-1 Calibration Look-Up Tables for continental alluvial terrain) and $\varepsilon = 10^{-6}$ prevents zero-argument singularity.

### 3.2 Dual-Date Logarithmic Backscatter Difference ($\Delta\sigma^0$)
The relative change between the dry baseline scene ($t_1 = \text{2019-09-23}$, Sentinel-1A) and peak flood scene ($t_2 = \text{2019-09-29}$, Sentinel-1B) is formulated as:

$$\Delta\sigma^0 = \sigma^0_{\text{post}} - \sigma^0_{\text{pre}} = 10 \cdot \log_{10}\left( \frac{\sigma^0_{\text{post, linear}}}{\sigma^0_{\text{pre, linear}}} \right)$$

### 3.3 Urban Dihedral Corner-Reflector Backscatter Surge
Unlike unbuilt plains where standing water acts as a flat mirror causing specular forward scattering ($\Delta\sigma^0 \le -3.80\text{ dB}$), urban settlements exhibit dihedral retro-reflection:

$$\sigma^0_{\text{urban, flooded}} = \sigma^0_{\text{direct}} + \sigma^0_{\text{wall}\to\text{water}} + \sigma^0_{\text{water}\to\text{wall}} + \sigma^0_{\text{corner}}$$

When water depth reaches the threshold where street pavement roughness is smoothed out, the $90^\circ$ dihedral angle between building masonry and water surface reflects microwave pulses directly back to the sensor antenna, inducing an anomalous positive jump:

$$\Delta\sigma^0 \ge +1.50\text{ dB} \quad \text{for Elevation} \le 50.0\text{ m AMSL}$$

### 3.4 Automated Bimodal Otsu Thresholding ($\tau^*$)
The automated separation of specular floodwaters minimizes intra-class variance $\sigma_w^2(t)$:

$$\tau^* = \arg\max_{t} \left\{ \omega_0(t) \omega_1(t) \left[ \mu_0(t) - \mu_1(t) \right]^2 \right\}$$

For the Patna September 2019 deluge, the empirical global optimum resolves at $\tau^* = -3.80\text{ dB}$.

### 3.5 Shoelace Geodesic Spherical Area Formula
For an agricultural or cadastral parcel defined by $n$ geodetic vertices $(\phi_i, \lambda_i)$ on a sphere of radius $R = 6371\text{ km}$:

$$A = \frac{R^2}{2} \left| \sum_{i=1}^{n} (\lambda_{i+1} - \lambda_i) \cdot (\sin \phi_{i+1} + \sin \phi_i) \right|$$

---

## 4. Quantitative Results & Validation Matrix

### 4.1 Study Area Extents
| Metric | Empirical Value | Description |
|---|---|---|
| **Total Mapped Study AOI** | $444.68\text{ km}^2$ | Patna Urban Core & Ganga Floodplain Bounding Box |
| **Permanent River Channel** | $113.82\text{ km}^2$ | Pre-flood baseline perennial Ganga channel ($\sigma^0_{\text{pre}} \le -40.0\text{ dB}$) |
| **Newly Inundated Floodwater ("Naya Paani")** | $26.54\text{ km}^2$ | Verified pluvial flood gain ($\Delta\sigma^0 \le -3.80\text{ dB}$, $\sigma^0_{\text{post}} \le -15.0\text{ dB}$) |
| **Urban Double-Bounce Inundation** | $11.84\text{ km}^2$ | Built-up dihedral retro-reflection ($\Delta\sigma^0 \ge +1.5\text{ dB}$, $\text{Elev} \le 50\text{m}$) |
| **Total Peak Water Surface** | $140.36\text{ km}^2$ | Composite water surface during peak deluge |
| **Urban Inundation Fraction** | $5.97\%$ | Fraction of urban municipal core submerged |
| **Otsu Backscatter Drop Threshold ($\tau^*$)** | $-3.80\text{ dB}$ | Automated bimodal water separation threshold |
| **Specular Water Mean Backscatter** | $-41.85\text{ dB}$ | Flat water specular mirror absorption |

### 4.2 Spatial Model Validation & Performance Metrics (5-Fold SBCV)
| Evaluation Metric | Spatial Cross-Validation (SBCV) | Random Split (Standard CV) | Scientific Implication |
|---|---|---|---|
| **Overall Accuracy** | **$94.6\%$** | $96.8\%$ (Overoptimistic) | Eliminates $+2.2\%$ Autocorrelation Bias |
| **Precision (PPV)** | **$88.4\%$** | $91.2\%$ | Verified Ground Truth Fidelity |
| **Recall (Sensitivity)** | **$92.1\%$** | $94.5\%$ | High Deluge Catch Rate |
| **F1-Score (Harmonic Mean)**| **$0.902$** | $0.928$ | Robust Non-Linear Balance |
| **Area Under ROC (ROC-AUC)**| **$0.963$** | $0.981$ | Outstanding Discriminative Power |
| **Brier Score Loss** | **$0.048$** | $0.039$ | Well-Calibrated Empirical Probability |

### 4.3 Patna Wards Empirical Flood Risk Ranking
| Ward / Locality Name | Mean Elev (AMSL) | Flooded Area ($\text{km}^2$) | Inundation % | Peak $\Delta\sigma^0$ (dB) | Scattering Mechanism | Exposure Classification |
|---|---|---|---|---|---|---|
| **Rajendra Nagar Basin** | $44.5\text{ m}$ | $4.11\text{ km}^2$ | $96.8\%$ | $+4.8\text{ dB}$ | Dihedral Double-Bounce | **Critical Emergency Deluge** |
| **Kankarbagh Silt Pond** | $45.1\text{ m}$ | $5.28\text{ km}^2$ | $94.2\%$ | $+3.6\text{ dB}$ | Dihedral Double-Bounce | **Severe Waterlogging** |
| **Patna City / East Core** | $47.2\text{ m}$ | $3.25\text{ km}^2$ | $47.8\%$ | $+2.1\text{ dB}$ | Mixed Urban Silt | **Moderate Pluvial Silt** |
| **Patliputra / Boring Rd** | $48.3\text{ m}$ | $0.85\text{ km}^2$ | $25.0\%$ | $+1.3\text{ dB}$ | Peripheral Surface Runoff | **Low / Surface Runoff** |
| **Gandhi Maidan Levee** | $50.1\text{ m}$ | $0.21\text{ km}^2$ | $10.0\%$ | $+0.4\text{ dB}$ | Natural Levee Crown | **Resilient Natural Terrace** |
| **Danapur Cantt Terrace** | $52.8\text{ m}$ | $0.15\text{ km}^2$ | $2.1\%$ | $-0.3\text{ dB}$ | Elevated Safe Ridge | **High Elevation Safe Zone** |
| **Bihta / IIT Patna Ridge** | $55.2\text{ m}$ | $0.00\text{ km}^2$ | $0.0\%$ | $-0.4\text{ dB}$ | Alluvial Highland | **Zero Inundation Benchmark** |

---

## 5. What BHU LOKA Does: Core Workstation Modules

```
                                      BHU LOKA SYSTEM ARCHITECTURE
                                      
  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │                                   WORKSTATION INTERFACES & MODULES                                     │
  │                                                                                                        │
  │  [3D Planetary Digital Twin]      [2D Sovereign GIS]              [Multi-Hazard Location Engine]       │
  │  Three.js WebGL2 Globe            Hardware Leaflet Engine         8 Sovereign Hazard Categories        │
  │  • Sovereign 36 States/UTs        • 28 States & 8 UTs (724 Dist)  • Flood, Heatwave, Landslide         │
  │  • 186 Live Spacecraft Orbits     • Sovereign State Selector Card • Forest Fire, Drought, Cyclone      │
  │  • 30m Micro-DEM Terrain          • Sentinel-1 SAR Deluge Layer   • Glacial Outburst, Air Poll.        │
  │  • 2D Crop to 3D Relief Extrusion • 14 Scientific Layer Overlays  • Strict Fail-Closed Integrity       │
  │                                                                                                        │
  │  [Land Intelligence Studio]       [Farmer & Mandi Market Engine]  [Public Health & Safety Suite]       │
  │  BSA 2023 §63 Cadastral Screening Precision Agriculture           3D Spatial Epidemiology              │
  │  • 5 Core AOIs (Patna, Varanasi)  • Shoelace Plot Acreage/Ha      • Location-aware 3D Disease Risk     │
  │  • Vision ML Roof Scan Model      • STAC Sentinel-2 (NDVI, NDRE)  • Stagnant Water Vector Breeding     │
  │  • SegFormer 7-Class LULC Model   • Root-zone Soil Moisture       • PM2.5 Inversion / Alveolar Stress  │
  │  • 4-Quadrant Legal Spatial Audit • Mandi Price & Crop Guidance   • Actionable Survival Protocols      │
  │  • Printable Government Dossier   • PM-KISAN GeoJSON Export       • Emergency Logistics Locator        │
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

### Module 1: 3D Planetary & Holographic Digital Twin (`index.html`)
* **Sovereign Boundary Lock:** Renders the authentic sovereign boundary of India (including Jammu & Kashmir, Ladakh, and Arunachal Pradesh) along with 36 State/UT administrative borders locked directly to the rotating Three.js WebGL2 sphere with zero coordinate drift.
* **Real-Time Ephemeris Satellite Tracking:** Propagates orbits for 186+ active satellites (Copernicus Sentinel-1/2/5P, NASA-ISRO NISAR, Landsat-8/9, NOAA, Starlink, and ISS) via SGP4 orbital mechanics with offline-safe abort controllers.
* **Astronomical Day/Night & FLIR Thermal:** Renders real-time solar declination, day-night terminators, specular ocean reflections, and simulated FLIR thermal heatwave emissions.
* **Micro-DEM Terrain Hologram:** Drapes zoom-14 satellite imagery over Copernicus GLO-30 elevation models, color-coding critical sink basins (<46m AMSL), ponding saucer basins (48-52m AMSL), and elevated natural levee ridges (>52m AMSL).
* **Interactive 2D-to-3D Terrain Cropper:** Allows operators to draw a bounding box on the 2D map and immediately extrude the chosen area into a full 3D interactive holographic terrain mesh.

### Module 2: Sovereign Pan-India 2D GIS Workstation (`bhu_loka_leafmap_interactive.html`)
* **All 28 States & 8 UTs Explorer:** Seamlessly explore all 36 administrative units and 724 districts of India via the `#sovereign-state-select` dropdown with alphabetical optgroups.
* **State Dossier Cards:** Selecting a state highlights its polygon border, zooms to its geodetic bounding box, and displays a floating glassmorphic dossier card displaying its capital, local vernacular name, district count, and data attribution.
* **14 Scientific Overlay Layers:** Sentinel-1 SAR Deluge, DEM Elevation, Multi-Hazard, Safe Corridors, MODIS LST Thermal, Land Use / Land Cover (LULC), Infrastructure & Critical Assets, Buildings, Roads & Greenery.
* **Pixel Backscatter HUD:** Real-time on-hover radar backscatter readout displaying calibrated $\sigma^0_{\text{dB}}$ values and flood probabilities.
* **QGIS/ArcGIS Export:** One-click export of observed inundation and parcel vectors in standard GeoJSON format.

### Module 3: Multi-Hazard Location Intelligence Explorer
* **8 Sovereign Disaster Categories:** Pluvial/Fluvial Flood, Extreme Heatwave, Landslide Vulnerability, Active Forest Fire, Agricultural Drought, Tropical Cyclone, Glacial Lake Outburst Flood (GLOF), and Severe Air Pollution.
* **Zero Synthetic Data Policy:** Strict fail-closed architecture ensures that whenever a real-time sensor feed is offline, the UI clearly displays `UNAVAILABLE` rather than generating fabricated data.

### Module 4: Land & Cadastral Intelligence Studio & Models (`Assets/vendor/bhu_loka_urban_studio.js`)
* **Map-First Spatial Audit:** Real-time spatial analysis across 5 key Areas of Interest (AOIs): Patna (Rajendra Nagar, Gandhi Maidan, IIT Patna), Varanasi, Hampi, and Hyderabad (Hussain Sagar, Osman Sagar).
* **Vision ML Roof Scan & SegFormer 7-Class LULC Model:**
  * Free on-device computer vision models segmenting building footprints, roof materials (terracotta, concrete, tin sheet), tree canopy, road corridors, and water boundaries.
  * Deep learning SegFormer architecture categorizing high-resolution satellite imagery into harmonized ESA WorldCover classes.
* **4-Quadrant Multi-Spectral Audit:**
  1. *Optical Satellite High-Resolution View*
  2. *Cadastral Full Tank Level (FTL) & Revenue Boundary*
  3. *Digital Elevation Buffer & Inflow Sinks*
  4. *Potential Spatial Overlap Footprint*
* **Bi-Temporal Decadal Satellite Swipe:** Interactive before/after split-screen swipe comparing historical baseline imagery against modern satellite passes.
* **3D Shoreline Perspective:** WebGL-rendered 3D elevation buffer visualizing building elevations relative to lake bed contours.
* **Bharatiya Sakshya Adhiniyam, 2023 (BSA §63) Compliance:** Generates official government-ready electronic evidence dossiers containing cryptographic SHA-256 hashes, acquisition timestamps, sensor calibration levels, and statutory technical screening disclaimers. Completely eliminates speculative automated demolition claims in favor of objective `POTENTIAL SPATIAL OVERLAP — REQUIRES OFFICIAL VERIFICATION`.

### Module 5: Farmer Intelligence & Mandi Market Engine (`Pipelines/bhu_loka_agri_engine.py`)
* **Complete Land Intelligence for Farmers:**
  * *Interactive Plot Drawer:* Draw parcel boundaries directly on high-resolution satellite imagery with vertex undo and edit tools.
  * *Accurate Geodesic Area Calculation:* Implements spherical Shoelace mathematics computing exact land parcel acreage and hectares.
  * *Sentinel-2 L2A STAC Multi-Spectral Indices:*
    * **NDVI (Canopy Greenness & Photosynthetic Vigor):** $(B08 - B04) / (B08 + B04)$ at 10m resolution.
    * **NDRE (Red-Edge Chlorophyll & Nitrogen Sensitivity):** $(B08 - B05) / (B08 + B05)$ for mid-to-late crop stages.
    * **EVI (Enhanced Vegetation Index):** Eliminates canopy background and aerosol distortion in dense foliage.
    * **SAVI (Soil-Adjusted Vegetation Index):** Minimizes bare-soil reflection during early germination and emergence.
    * **NDWI (Canopy Moisture & Liquid Water):** $(B08 - B11) / (B08 + B11)$ tracking foliar water stress.
  * *Agro-Meteorology & Soil Moisture:* Integrates Open-Meteo $ET_0$ FAO evapotranspiration, Vapor Pressure Deficit (VPD), surface and root-zone volumetric soil moisture, 7-day cumulative water balance, and Copernicus 30m DEM slope drainage profiles.
  * *Crop Growth Stage Tracking:* Monitor fields across active phenological stages: Vegetative, Flowering, Harvesting, and Fallow.
* **Mandi Market Intelligence & Crop Selling Guidance:**
  * *Harvest Timing Optimization:* Combines radar dry-spell forecasts with crop maturity indices to advise farmers on the ideal harvesting window, preventing post-harvest monsoon rot.
  * *Mandi Price & Demand Trends:* Correlates local mandi market demand, historical modal prices, and crop yield estimations ($kg/ha$) to guide farmers on what crops to market and when to sell for maximum profitability.
  * *Official Scheme Ready:* Instant 1-click export of field boundaries into RFC 7946 GeoJSON format for PM-KISAN registration, digital land records, and parametric crop insurance claims.

### Module 6: Public Health, Citizen Safety & 3D Spatial Epidemiological Suite
* **Location-Aware 3D Impact Visualization:**
  * *Hyper-Local 3D Risk Assessment:* Residents and emergency workers can inspect their exact GPS/ward location on the 3D Copernicus DEM relief to see how multi-hazards compound in their micro-topography.
  * *Stagnant Floodwater & Vector Breeding:* Visualizes critical depression sinks (<46m AMSL) where post-deluge floodwaters remain trapped, highlighting high-risk breeding zones for dengue, malaria, and waterborne pathogens.
  * *Severe Air Pollution & Inversion Stress:* Visualizes Sentinel-5P TROPOMI $\text{NO}_2$ plumes, surface $\text{PM}_{2.5}$ inversion layers, and fine silt re-suspension ($142\ \mu\text{g/m}^3$) causing alveolar mucosal and respiratory stress.
  * *Extreme Heatwave Thermal Exposure:* Drapes NASA MODIS Land Surface Temperature ($>42^\circ\text{C}$) over high-density tenements to identify urban heat islands.
* **Actionable Citizen Protection Advisories:**
  * *Tailored Health Protocols:* Real-time advisories on avoiding contaminated floodwater, boil-water notices, N95 mask usage during silt/aerosol inversions, and hydration protocols during peak heat hours.
  * *Vulnerability Profiling:* Specific safety warnings tailored for high-risk demographics, including the elderly, infants, and individuals with pre-existing cardiopulmonary conditions.
* **Healthcare & Emergency Logistics Locator:**
  * *Emergency Medical Centers:* Geocoded locations and phone directories of operational government hospitals, trauma centers, and mobile medical dispensaries.
  * *Safe Levee Evacuation Shelters:* Highlights elevated natural terraces (>52m AMSL) safe from flood inundation (e.g. Danapur Cantonment Ridge, Gandhi Maidan high-ground).
  * *Clean Water & Ration Hubs:* Identifies designated municipal relief camps, potable water tankers, and motorable evacuation routes.

---

## 6. Trained Machine Learning Checkpoints & Inference Capabilities

The repository contains two trained, production-ready machine learning checkpoints developed by Prince Kumar & Payal Priyadarshini:

1. **`Models/Checkpoints/bhu_loka_spatial_rf_v1.joblib` (21.9 MB):**
   * Comprehensive 7-Feature Spatial Random Forest Classifier (100 estimators).
   * **Input Features:** `[SAR_pre_dB, SAR_post_dB, Delta_sigma0, Elevation, Slope, Is_Sink, Population]`.
   * Trained on a $2602 \times 1709$ spatial raster grid with 5-Fold Spatial Block Cross-Validation (SBCV).
   * Generates calibrated flood inundation probabilities, confidence metrics, and Tree-SHAP feature attributions.

2. **`mera_pehle_model.joblib` (168 KB):**
   * Lightweight, ultra-fast 3-Feature Random Forest Classifier.
   * **Input Features:** `[Delta_sigma0, Elevation, Slope]`.
   * Optimized for instant edge inference and offline client execution.

### Interactive Live Model Predictor in Web Interface
Operators can test these models interactively via the **`PREDICT AREA (SBCV)`** button on the workstation top subbar:
* Select from 8 benchmark presets or input custom coordinates.
* Receive instant inundation probabilities, predicted flood extent ($	ext{km}^2$), physical scattering classification, and Tree-SHAP attribution bars.
* Click **View on 3D Terrain** to highlight the flood prediction directly onto the 3D Copernicus DEM relief.

---

## 7. Quickstart & Local Reproduction

### Option A: 1-Click Windows Full-Stack Launcher (Recommended)

Double-click `Launch_BhuLoka_FullStack.bat` in the repository root. This automatically:
1. Starts the FastAPI Telemetry, Agri & Spatial ML Server on `http://127.0.0.1:8000`.
2. Launches the Chromium Sovereign Workstation in app mode at full resolution.

```cmd
.\Launch_BhuLoka_FullStack.bat
```

### Option B: Standalone Python Server & Pytest Suite (63/63 Passing)

```bash
# 1. Clone repository
git clone https://github.com/Amourhoffen/BhuLoka.git
cd BhuLoka

# 2. Install dependencies
pip install fastapi uvicorn numpy scikit-learn joblib httpx faiss-cpu pytest beautifulsoup4

# 3. Run the automated test suite (63/63 passing with 100% pass rate)
pytest tests/ -v

# 4. Start the FastAPI backend
python Models/04_Hybrid_RAG/enterprise_rag_app/main.py
```

### Option C: Run Spatial ML Hazard Inference via CLI

```bash
python Models/01_Spatial_ML/predict_hazard.py "rajendra nagar"
```

```
=================================================================
BHU LOKA ML INFERENCE RESULT: RAJENDRA NAGAR
=================================================================
Physical Inputs:
• Sentinel-1 SAR Backscatter : Pre: -12.4 dB, Post: -9.8 dB (Δσ⁰: +2.6 dB)
• Copernicus DEM Topography : Elev: 44.5 m, Slope: 0.4°, Depression Sink: True
• WorldPop 2020 Demographics : 18,400 people/km²
-----------------------------------------------------------------
Machine Learning Assessment:
• Inundation Probability    : 96.80%
• Scattering Mechanism      : Dihedral Double-Bounce Retro-Reflection
• AI Hazard Classification  : CRITICAL INUNDATION (Severe Urban Waterlogging)
=================================================================
```

---

## 8. Exact Observed Sentinel-1 Satellite Metadata (ASF Vertex / NASA Earthdata)

| Scene Role | Complete Scene Identifier | Sensor Platform | Acquisition Timestamp (UTC) | Pass Direction | Polarizations |
|---|---|---|---|---|---|
| **Pre-Flood Baseline Scene** | `S1A_IW_GRDH_1SDV_20190923T002026_20190923T002051_029141_034EEC` | Copernicus Sentinel-1A | **2019-09-23 00:20:38 UTC** | Descending | VV + VH |
| **Peak Flood Deluge Scene** | `S1B_IW_GRDH_1SDV_20190929T001924_20190929T001949_018245_0225AB` | Copernicus Sentinel-1B | **2019-09-29 00:19:37 UTC** | Descending | VV + VH |

---

## 9. Academic Citation

If you utilize BHU LOKA, its empirical SAR methodology, spatial machine learning models, precision agriculture engine, or the Patna flood dataset in your research, please cite:

```bibtex
@article{kumar2026sequential,
  title={Sequential Compound Hydro-Thermal Risk and Urban Corner-Reflector Flood Mapping in Continental Alluvial Metropolises: Empirical Earth Observation and Spatial Validation Sensitivity over Patna, India},
  author={Kumar, Prince and Priyadarshini, Payal and Rustogi, Pallav},
  institution={Indian Institute of Technology Patna & Indian Institute of Information Technology, Design and Manufacturing Jabalpur},
  year={2026},
  url={https://bhu-loka.web.app}
}
```

---

<img width="1460" height="768" alt="Sovereign GIS Platform View" src="https://github.com/user-attachments/assets/b737f31c-cf9e-43ab-bbef-486fec786c2f" />
<img width="1460" height="815" alt="3D Workstation View" src="https://github.com/user-attachments/assets/8c9d59bf-795d-4151-ba35-2368b9b251bc" />

## ⚖️ License & Open-Source Sovereignty

This project is licensed under the **MIT Open Source License** — see the [LICENSE](LICENSE) file for details.  
*Dedicated to open-source scientific disaster resilience, sovereign geospatial intelligence, and empowering agricultural and urban communities worldwide.*

---

<div align="center">

### ⭐ If you find BHU LOKA inspiring or useful, please give this repository a star!
**Built with passion by Prince Kumar, Payal Priyadarshini & Team Amour Hoffen at IIT Patna**

</div>
