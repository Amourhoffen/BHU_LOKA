# BHU LOKA (भूलोक) — Problem Statement (R0 / R0.1 Aligned)

**Project:** BHU LOKA Sovereign Geospatial AI Platform  
**Institution:** Indian Institute of Technology Patna (CSE)  
**Team:** Prince Kumar (Project Owner, IIT Patna, `PA2511CDH37`) | Pallav Rustogi (Project Supervisor) | Payal Priyadarshini (UI/UX Designer, IIITDM Jabalpur, 1st Semester)  
**Platform Scope:** Software-Only Research and Intelligence Platform (IoT hardware, wearables, sensor manufacturing, and physical hardware firmware are explicitly **OUT OF CURRENT SCOPE**)  

---

## 1. Scientific and Engineering Problems Addressed

Rapid urbanization and climate intensification across alluvial river basins create compounding vulnerabilities across physical hazards, civic infrastructure, administrative data fragmentation, and agricultural livelihoods:

### 1.1 Omission of Urban Street-Canyon Flooding in Standard SAR Workflows
Conventional radar flood detection thresholds rely solely on specular microwave attenuation ($\Delta\sigma^0 \le -2.0\text{ dB}$). In dense cities such as Patna, standing floodwater flanked by concrete facades forms dihedral corner reflectors that increase backscatter ($\Delta\sigma^0 \ge +1.5\text{ dB}$). Standard UN-SPIDER style specular workflows detect only $4.01\text{ km}^2$ ($2.99\%$) of the $133.87\text{ km}^2$ Patna Municipal Corporation during the September 2019 deluge, yielding a $95.98\%$ omission error against BHU LOKA bimodal SAR detection ($99.60\text{ km}^2$, `Exp_01_SAR_Flood_Inundation`).

### 1.2 Gravity Drainage Lock Behind River Embankments
Micro-topographic extraction from Copernicus GLO-30 DEM across $142.48\text{ km}^2$ shows $47.24\text{ km}^2$ ($33.15\%$) of urban terrain consists of closed topographic depressions sitting at $44.5\text{--}46.8\text{ m}$ a.m.s.l. while Ganges levees sit at $53.0\text{--}55.0\text{ m}$ (`Exp_02_Copernicus_DEM_Terrain`). When river stages exceed danger thresholds, gravity outfalls lock and submerge $49,380$ residents residing inside compound flood-and-sink corridors (`Exp_04_MultiHazard_Fusion`).

### 1.3 Inflated Accuracy Metrics Under Spatial Autocorrelation
Random k-fold cross-validation leaks nearby correlated observations across training and test partitions. Contiguous 5-fold Spatial Block Cross-Validation over $60,000$ samples drops Spatial Random Forest evaluation performance to mean ROC-AUC $0.7498 \pm 0.0497$ (`spatial_cv_metrics.json`), exposing an autocorrelation gap relative to random cross-validation.

### 1.4 Fragmented All-India Location, Land Record, and Street Telemetry
Geospatial dashboards frequently collapse India into incomplete state counts, invent missing subdivisions, infer arbitrary Thiessen/radius polygons for police jurisdictions, display unverified CCTV streams, or ignore composite scoping rules for non-unique Khata/Khesra plot numbers.

### 1.5 Disconnected Earth Observation and Farm Decision Workflows
Individual smallholder farmers lack sovereign tools that translate their own mapped field boundaries into actual cloud-masked Sentinel-2 spectral indices, soil-moisture/ET0 water stress signals, and context-grounded crop diagnostics without forcing vendor lock-in or fabricating agronomy measurements.

---

## 2. Explicit Scope Boundaries (Non-Goals in R0)

- BHU LOKA does **not** verify or adjudicate legal land ownership, mutation status, or title (official state DILRMP portals remain authoritative).
- BHU LOKA does **not** bypass CAPTCHAs, scrape restricted government databases, or access private surveillance feeds.
- BHU LOKA does **not** fabricate live weather, satellite NDVI/NDRE values, sensor IoT metrics, or market prices when source APIs or rasters are unavailable.
