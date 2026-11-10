# Senior Researcher Supervisory Blueprint: Project BHU LOKA (भूलोक)

**Role:** Senior Principal Investigator & Research Supervisor (Geospatial AI & Hydro-Climatology)  
**Researcher:** Prince Kumar (IIT Patna)  
**Project:** BHU LOKA (भूलोक)  
**Target Manuscript:** *Heatwave-Preconditioned Pluvial Flooding in Flat Alluvial Metropolises: A Spatial Quantile Learning and Game-Theoretic Framework for Patna, Indo-Gangetic Basin*  
**Target Venues:** *Geophysical Research Letters (GRL)* | *Remote Sensing of Environment (RSE)* | *Natural Hazards (Springer)*  
**Document Location:** `Bhu Loka - भूलोक/Research_Paper_Workflow/Review/03_Senior_Researcher_Supervision_Roadmap.md`

---

## 1. Supervisor's Executive Assessment

Prince, ek Senior Researcher aur PI ke taur par maine aapke collected 7 research papers ko exhaustively synthesize kiya hai aur Patna ki actual physical geography ke sath map kiya hai:

1. **Ganguli et al. (2025, GRL):** Chennai par sequential compound extremes (heatwave preconditioning $\to$ pluvial flood) prove kiya hai. Lekin Chennai **coastal city** hai jahan maritime humidity aur cyclonic systems dominate karte hain.
2. **Singh et al. (2026, MDPI):** Delhi ke liye Quantile LightGBM + SHAP use kiya hai. Lekin Delhi **semi-arid, high-elevation gradient (Aravalli Ridge)** landscape hai, aur unke model mein sequential thermodynamic coupling missing thi.
3. **Tallapragada / Prasad et al. (MAUSAM):** IMD aur NOAA UFS monsoon precipitation bias dikhata hai — Gangetic plain mein diurnal rain peak capture karna challenging hota hai.
4. **Roberts et al. (2016, Ecography):** Standard random cross-validation spatial modeling mein "scientific crime" hai kyunki spatial autocorrelation se fake $98\%$ accuracy dikhti hai. Spatial Block CV zaroori hai.
5. **Jato-Espino et al. & UNU-ITC:** Compact multi-hazard indicators aur Hazard $\times$ Exposure framework.

---

## 2. Hamara Original Research Contribution (The Scientific "Hook")

Top-tier journals (GRL / Nature Communications / RSE) tab paper accept karte hain jab unhe ek **unresolved scientific question** aur **novel methodology** milti hai.

Hamara hook kya hai?
> **"Why Patna is Unique and Globally Relevant:"**  
> Patna duniya ke sabse flat alluvial river basins (Ganges, Son, Punpun confluence) mein sthit ek saucer-shaped depression hai. Yahan pre-monsoon mein severe continental heatwaves ($>44^\circ\text{C}$) aati hain, jisse Gangetic alluvial clay crust harden ho jaata hai. Jab monsoon trough cloudburst hota hai, toh river backflow + subterranean pump failure + loss of infiltration milkar 2019 jaisi catastrophic pluvial deluge trigger karte hain.
>
> **Scientific Gap:** Coastal cities par compound hazard research ho chuki hai, par continental flat alluvial basins mein thermodynamic preconditioning + spatial quantile ML abhi tak unstudied hai!

---

## 3. Phase-Wise Execution Roadmap (Step-by-Step)

```text
PHASE 1: Real Earth Observation Ingestion (Week 1–2)
  ├── Patna Boundary: GADM / Bihar GIS Administrative Polygon
  ├── Topography: NASA SRTM 30m DEM → TWI, Slope, Depression Sinks
  ├── Land Cover: Sentinel-2 MSI (10m) → NDBI, NDVI, Impervious Fraction
  ├── Thermal: Landsat-8/MODIS → Pre-monsoon Land Surface Temperature (LST)
  ├── Precipitation: IMD 0.25° Gridded Rainfall + Topographic Downscaling
  └── Validation Satellite Data: Copernicus Sentinel-1 SAR (2019 Patna Flood Scenes)

PHASE 2: Feature Engineering & Spatial Block Partitioning (Week 3)
  ├── 50m × 50m Regular Raster Grid Generation
  ├── Topographic Wetness Index (TWI = ln(a / tan β))
  ├── Spatial Block Cross-Validation (Roberts et al. 2016: 5 Wards/Tehsil Blocks)
  └── Thermodynamic Infiltration Degradation Function Formulation

PHASE 3: Quantile Machine Learning & SHAP Attribution (Week 4)
  ├── Quantile LightGBM (α = 0.50 Median vs α = 0.90 Extreme Catastrophic Risk)
  ├── Spatial Autocorrelation Penalty Quantification (ΔR² and spatial Moran's I)
  └── Ward-Level Tree-SHAP Values (Patna Municipal Corporation - 75 Wards)

PHASE 4: Empirical Ground Truth Validation (Week 5)
  ├── Sentinel-1 SAR Otsu Thresholding vs Predicted Waterlogging Hotspots
  └── 2019 Patna Deluge Ground Truth Calibration (Rajendra Nagar, Kankarbagh)

PHASE 5: Manuscript Finalization & Journal Submission (Week 6)
  ├── GRL / RSE Format: 4 Figures + 2 Tables + SI
  └── BibTeX References using science-skills automation
```

---

## 4. Supervisor's 3 Non-Negotiable Rules

1. **Resolution Honesty:** IMD 25 km grid ko direct 10 m map par mat chipkana; manuscript mein geostatistical downscaling aur limitations clearly acknowledge karna.
2. **Spatial Block CV:** Paper mein Random CV aur Spatial Block CV dono ka comparison dikhana — yahi table reviewers ko impress karegi.
3. **Ground Truth Validation:** Sentinel-1 SAR 2019 scenes se flood extent nikaal kar model predictions ke sath ROC-AUC / IoU calculate karna hoga.

