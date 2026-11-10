# BHU LOKA (भूलोक) - Geospatial Data Engineering Pipelines

## Architecture Overview

The `Pipelines` directory implements modular, reproducible Extract-Transform-Load (ETL) and Extract-Load-Transform (ELT) workflows for multi-sensor Earth Observation datasets.

```
Pipelines/
├── 01_Ingestion/             # Automated fetchers and API clients
│   ├── fetch_boundaries.py   # OSM Nominatim & GADM ingest
│   ├── fetch_sentinel1.py    # Microsoft Planetary Computer STAC client
│   ├── fetch_sentinel2.py    # Copernicus Data Space STAC client
│   └── fetch_dem_copernicus.py# AWS Open Data Copernicus DEM client
├── 02_Validation/            # Integrity and quality control
│   ├── validate_crs.py       # EPSG coordinate reference system validator
│   ├── validate_nodata.py    # NoData / cloud artifact screening
│   └── validate_bounds.py    # Spatial intersection against Patna boundary
├── 03_Transformation/        # Core radiometric and geometric transforms
│   ├── calibrate_sar.py      # Sentinel-1 DN -> Sigma0 (dB) radiometric calibration
│   ├── resample_match.py     # Bilinear / Nearest Neighbor raster grid alignment
│   ├── mask_permanent_water.py# Pre-flood baseline water body exclusion
│   └── clip_pmc_polygon.py   # Polygon raster masking for municipal core
└── 04_Feature_Engineering/   # Multi-hazard environmental indices
    ├── compute_terrain.py    # Slope, Aspect, Topographic Wetness Index (TWI), Sinks
    ├── compute_urban_sar.py  # Double-bounce backscatter difference metric
    ├── compute_lst_metrics.py# Multi-temporal thermal anomaly and heatwave index
    └── assemble_features.py  # Multi-band raster stack assembly for ML modeling
```

---

## Standard Pipeline Execution Sequence

1. **Ingest Phase**: Fetch raw scenes from planetary data repositories using bounding box coordinates.
2. **Validation Phase**: Ensure coordinate systems align to WGS84 (EPSG:4326) or UTM Zone 45N (EPSG:32645).
3. **Transform Phase**: Calibrate raw digital numbers (DN) to physical units (radar cross section $\sigma^0$ in dB, surface temperature in $^\circ\text{C}$, elevation in meters).
4. **Feature Engineering Phase**: Generate physical derivatives (micro-topographic slope, drainage sinks, double-bounce anomalies) and align to a common $10\text{ m}$ spatial grid.
