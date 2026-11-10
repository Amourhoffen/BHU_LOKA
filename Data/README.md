# BHU LOKA (भूलोक) - Master Data Catalog and Provenance Registry

## Overview
This directory serves as the centralized data repository for Project **BHU LOKA (भूलोक)**: an uncertainty-aware geospatial AI framework for multi-hazard risk assessment and climate-resilient urban suitability in Patna District, Bihar, India.

All datasets stored here are authentic, empirically acquired earth observation and administrative assets.

---

## Directory Layout and Inventory

```
Data/
├── 01_Boundaries/             # Administrative and municipal boundary vector polygons
├── 02_SAR_Sentinel1/          # Sentinel-1 Synthetic Aperture Radar (SAR) Level-1 GRDH rasters
├── 03_Optical_Sentinel2/      # Sentinel-2 MSI multispectral optical rasters (L2A Bottom-of-Atmosphere)
├── 04_DEM_SRTM/               # Copernicus GLO-30 30-meter Digital Elevation Model rasters
├── 05_Rainfall_IMD/           # IMD / GPM gridded precipitation time series
├── 06_LST_Thermal/            # NASA MODIS Terra Land Surface Temperature (MOD11A1 Daily)
├── 07_Population_WorldPop/    # WorldPop UN-adjusted 1 km demographic exposure raster
└── 08_Processed_Outputs/      # Analysis masks, delta rasters, and empirical audit outputs
```

---

## Detailed Data Assets

### 1. Administrative Boundaries (`01_Boundaries/`)
- **District Boundary**: `patna_district_boundary.geojson`
  - *Source*: OpenStreetMap Nominatim administrative level 5.
  - *Vertices*: 5,649 coordinate pairs.
  - *Bounding Box*: $84.6869^\circ\text{E}$ to $86.0689^\circ\text{E}$, $25.2033^\circ\text{N}$ to $25.7329^\circ\text{N}$.
- **Urban Municipal Boundary**: `patna_urban_boundary.geojson`
  - *Source*: Patna Municipal Corporation (PMC) official limits.
  - *Vertices*: 2,001 coordinate pairs.
  - *Area*: $133.87\text{ km}^2$ (13,387 hectares).
- **National Administrative Reference**: `gadm41_IND_level2.gpkg`
  - *Source*: Database of Global Administrative Areas (GADM) v4.1 (49.6 MB).

### 2. Synthetic Aperture Radar (`02_SAR_Sentinel1/`)
- **Peak Flood Scene**: `S1B_IW_GRDH_VV_20190929_peak_flood.tif`
  - *Sensor*: Sentinel-1B C-band SAR ($5.405\text{ GHz}$).
  - *Acquisition*: 2019-09-29 00:19:24 UTC (Descending pass, relative orbit 121).
  - *Polarization*: Vertical-Transmit, Vertical-Receive (VV).
  - *Dimensions*: $25,296 \times 16,765$ pixels ($713.72\text{ MB}$).
  - *Pixel Spacing*: $10\text{ m} \times 10\text{ m}$ (Spatial resolution: $20.4\text{ m} \times 22.5\text{ m}$).
- **Pre-Flood Baseline Scene**: `S1A_IW_GRDH_VV_20190923_pre_flood.tif`
  - *Sensor*: Sentinel-1A C-band SAR.
  - *Acquisition*: 2019-09-23 00:20:01 UTC ($693.76\text{ MB}$).

### 3. Digital Elevation Model (`04_DEM_SRTM/`)
- **Copernicus GLO-30 30-meter DEM**:
  - `glo30_N25_E084.tif` ($3,600 \times 3,600$ float32 pixels, range: $41.87\text{ m}$ to $154.25\text{ m}$).
  - `glo30_N25_E085.tif` ($3,600 \times 3,600$ float32 pixels, range: $32.17\text{ m}$ to $390.25\text{ m}$).
  - *Vertical Datum*: EGM2008 geoid.
  - *Horizontal Datum*: WGS84 ($1\text{ arc-second} \approx 30\text{ m}$).

### 4. Land Surface Temperature (`06_LST_Thermal/`)
- **NASA MODIS Terra LST Daily L3 Global 1km Grid V061 (`MOD11A1.061`)**:
  - *Tile*: `h25v06` covering Bihar and Eastern Gangetic Plain.
  - *Time Period*: April 1, 2019 to June 30, 2019 (91 daily HDF files, $477.33\text{ MB}$).
  - *Primary Science Datasets*: `LST_Day_1km`, `QC_Day`, `Emis_31`, `Emis_32`.
  - *Scale Factor*: 0.02 (Kelvin), offset: $-273.15$ ($^\circ\text{C}$).

### 5. Demographic Vulnerability (`07_Population_WorldPop/`)
- **WorldPop India 2020 UN-Adjusted**:
  - `worldpop_india_2020_1km.tif` ($18.20\text{ MB}$).
  - *Definition*: Number of people per pixel grid cell, adjusted to official UN Population Division national estimates.

---

## Data Usage Guidelines
1. Never edit raw source rasters (`.tif`, `.hdf`, `.gpkg`) in place.
2. Store intermediate processing artifacts in `Data/08_Processed_Outputs/`.
3. Reference all data paths via programmatic relative paths (`Bhu Loka - भूलोक/Data/...`).

