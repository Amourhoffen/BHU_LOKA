# BHU LOKA (भूलोक) - Scientific Experiment Tracker and Benchmarks

## Overview
Every computational experiment in BHU LOKA is recorded with:
1. Formal scientific hypothesis
2. Fixed random seed and sensor parameters
3. Empirical baseline comparison
4. Evaluation metrics (Precision, Recall, F1, IoU, RMSE, Brier Score)

---

## Experiment Registry

### Exp_01: Empirical Sentinel-1 SAR Flood Inundation & Urban Double-Bounce
- **Directory**: `Experiments/Exp_01_SAR_Flood_Inundation/`
- **Objective**: Accurately delineate 2019 Patna extreme urban flood while accounting for double-bounce radar scattering in dense built-up zones (Kankarbagh, Rajendra Nagar).
- **Sensors**: Sentinel-1B IW GRDH (2019-09-29 peak flood) vs Sentinel-1A (2019-09-23 pre-flood baseline).
- **Core Hypothesis**: Simple Otsu thresholding ($\Delta \sigma^0 \le -3.80\text{ dB}$) detects open water in rural diara floodplains, but misses submerged street canyons where water + building walls create 90-degree corner reflection ($\Delta \sigma^0 \ge +1.5\text{ dB}$).
- **Key Metric**: Total flooded area within true PMC municipal limits ($133.87\text{ km}^2$) vs total study bbox ($444.68\text{ km}^2$).

### Exp_02: Copernicus 30m Micro-Topography & Drainage Sink Detection
- **Directory**: `Experiments/Exp_02_Copernicus_DEM_Terrain/`
- **Objective**: Delineate low-lying urban depression zones with natural drainage bottlenecks.
- **Sensors**: Copernicus GLO-30 DEM (`glo30_N25_E084.tif` + `glo30_N25_E085.tif`).
- **Indices**: Slope ($\% / ^\circ$), Topographic Position Index (TPI), Topographic Wetness Index (TWI).

### Exp_03: NASA MODIS Pre-Monsoon Heatwave & Thermal Risk
- **Directory**: `Experiments/Exp_03_MODIS_Thermal_Heat/`
- **Objective**: Map extreme surface temperatures across Patna during the April-June 2019 heatwave.
- **Sensors**: MODIS Terra Daily LST 1km (`MOD11A1.061`, 91 granules).
- **Indices**: Mean daily maximum LST, Urban Heat Island (UHI) intensity relative to rural baseline.

### Exp_04: Multi-Hazard Spatial Fusion & Demographic Vulnerability
- **Directory**: `Experiments/Exp_04_MultiHazard_Fusion/`
- **Objective**: Synthesize flood inundation susceptibility, extreme heat exposure, and population density into a unified decision-support suitability index.
- **Data Integration**: SAR Flood + DEM TWI + MODIS LST + WorldPop 2020.

