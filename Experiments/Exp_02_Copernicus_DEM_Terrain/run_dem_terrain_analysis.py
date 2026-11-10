"""
BHU LOKA (भूलोक) - Experiment 02: Copernicus 30m Micro-Topography & Drainage Sinks
===================================================================================
Analyzes elevation, slope, and topographic depression sinks across Patna
using Copernicus 30-meter GLO-30 Digital Elevation Model (DEM).

Key Scientific Objectives:
1. Merge the two 30m GLO-30 tiles (E084 and E085) covering Patna
2. Crop and mask by True PMC Urban Boundary and District Limits
3. Calculate physical micro-topographic Slope in degrees
4. Identify natural drainage bottlenecks and depression sinks (water accumulation bowls)

Author: Prince Kumar (IIT Patna, PA2511CDH37) & BHU LOKA Research Team
"""

import os
import json
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from matplotlib.path import Path

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEM_DIR = os.path.join(BASE_DIR, "Data", "04_DEM_SRTM")
BOUNDS_DIR = os.path.join(BASE_DIR, "Data", "01_Boundaries")
OUT_DIR = os.path.join(BASE_DIR, "Data", "08_Processed_Outputs")
EXP_DIR = os.path.dirname(__file__)

os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 70)
print(" EXPERIMENT 02: COPERNICUS 30M DEM & DRAINAGE SINK ANALYSIS")
print("=" * 70)

# 1. Load the two Copernicus 30m tiles
path_e084 = os.path.join(DEM_DIR, "glo30_N25_E084.tif")
path_e085 = os.path.join(DEM_DIR, "glo30_N25_E085.tif")

print(f"Loading Tile 1 (84°E to 85°E): {os.path.basename(path_e084)}")
with Image.open(path_e084) as img:
    dem_e084 = np.array(img, dtype=np.float32)

print(f"Loading Tile 2 (85°E to 86°E): {os.path.basename(path_e085)}")
with Image.open(path_e085) as img:
    dem_e085 = np.array(img, dtype=np.float32)

# Merge along longitude (horizontal axis 1)
# Total raster: Lat 26°N to 25°N (top to bottom), Lon 84°E to 86°E (left to right)
dem_merged = np.hstack([dem_e084, dem_e085])
H_full, W_full = dem_merged.shape
print(f"Merged DEM Dimensions: {W_full} x {H_full} pixels (30m spatial resolution)")

# Bounding coordinates of the merged raster
min_lon, max_lon = 84.0, 86.0
min_lat, max_lat = 25.0, 26.0

# 2. Load PMC Urban Boundary Polygon
with open(os.path.join(BOUNDS_DIR, "patna_urban_boundary.geojson"), "r") as f:
    urban_geojson = json.load(f)

poly_coords = urban_geojson["features"][0]["geometry"]["coordinates"][0]
pmc_polygon = Path(poly_coords)

# PMC bounding box
pmc_lons = [p[0] for p in poly_coords]
pmc_lats = [p[1] for p in poly_coords]
pmc_min_lon, pmc_max_lon = min(pmc_lons), max(pmc_lons)
pmc_min_lat, pmc_max_lat = min(pmc_lats), max(pmc_lats)

# Convert lat/lon bounds to pixel indices
# y = 0 is 26°N, y = H_full is 25°N (inverted latitude)
px_min = int(((pmc_min_lon - min_lon) / (max_lon - min_lon)) * W_full) - 10
px_max = int(((pmc_max_lon - min_lon) / (max_lon - min_lon)) * W_full) + 10
py_min = int(((max_lat - pmc_max_lat) / (max_lat - min_lat)) * H_full) - 10
py_max = int(((max_lat - pmc_min_lat) / (max_lat - min_lat)) * H_full) + 10

# Crop DEM to PMC urban bounding box
dem_pmc = dem_merged[py_min:py_max, px_min:px_max]
H_pmc, W_pmc = dem_pmc.shape
print(f"PMC Analysis DEM Extent: {W_pmc} x {H_pmc} pixels at 30m")

# Build pixel coordinate grid for polygon containment testing
x_indices = np.arange(px_min, px_max)
y_indices = np.arange(py_min, py_max)
grid_x, grid_y = np.meshgrid(x_indices, y_indices)

pts_lon = min_lon + (grid_x / W_full) * (max_lon - min_lon)
pts_lat = max_lat - (grid_y / H_full) * (max_lat - min_lat)

pts_all = np.column_stack([pts_lon.flatten(), pts_lat.flatten()])
inside_pmc = pmc_polygon.contains_points(pts_all).reshape((H_pmc, W_pmc))

# Elevation statistics inside PMC
pmc_elevations = dem_pmc[inside_pmc]
mean_elev = float(np.mean(pmc_elevations))
min_elev = float(np.min(pmc_elevations))
max_elev = float(np.max(pmc_elevations))
elev_std = float(np.std(pmc_elevations))

# 3. Micro-Topographic Slope Calculation (Horn's Method / Central Differences)
# Grid cell size in meters at latitude ~25.6°N
dx = 30.87 * np.cos(np.radians(25.6)) # ~27.84 meters per pixel in longitude
dy = 30.87                           # ~30.87 meters per pixel in latitude

dz_dx = (dem_pmc[:, 2:] - dem_pmc[:, :-2]) / (2.0 * dx)
dz_dy = (dem_pmc[2:, :] - dem_pmc[:-2, :]) / (2.0 * dy)

# Trim borders to match shape
dz_dx_trimmed = dz_dx[1:-1, :]
dz_dy_trimmed = dz_dy[:, 1:-1]

slope_rad = np.arctan(np.sqrt(dz_dx_trimmed**2 + dz_dy_trimmed**2))
slope_deg = np.degrees(slope_rad)

# Pad slope back to H_pmc, W_pmc
slope_full = np.pad(slope_deg, ((1, 1), (1, 1)), mode='edge')
pmc_slopes = slope_full[inside_pmc]
mean_slope = float(np.mean(pmc_slopes))
flat_fraction = float(np.sum(pmc_slopes < 1.0) / len(pmc_slopes) * 100.0)

# 4. Drainage Sinks / Low-Lying Depression Bowls
# A sink is a pixel whose elevation is strictly lower than the local 8-neighborhood mean by >= 0.4 meters
padded = np.pad(dem_pmc, ((1, 1), (1, 1)), mode='reflect')
neighborhood_sum = (
    padded[:-2, :-2] + padded[:-2, 1:-1] + padded[:-2, 2:] +
    padded[1:-1, :-2]                     + padded[1:-1, 2:] +
    padded[2:, :-2]  + padded[2:, 1:-1]  + padded[2:, 2:]
)
neighborhood_mean = neighborhood_sum / 8.0
depression_depth = neighborhood_mean - dem_pmc
is_sink = (depression_depth >= 0.4) & inside_pmc

sink_pixels = int(np.sum(is_sink))
sink_area_km2 = float((sink_pixels * 30.0 * 30.0) / 1e6)
sink_fraction = float((sink_area_km2 / (len(pmc_elevations) * 30.0 * 30.0 / 1e6)) * 100.0)

print("\n" + "=" * 70)
print(" EXPERIMENT 02 RESULTS: PATNA URBAN TOPOGRAPHIC METRICS")
print("=" * 70)
print(f"Patna Urban Core (PMC) Area          : {len(pmc_elevations) * 900.0 / 1e6:.2f} km²")
print(f"Mean Elevation (EGM2008 Geoid)       : {mean_elev:.2f} m (Range: {min_elev:.2f} m to {max_elev:.2f} m)")
print(f"Elevation Standard Deviation (Rough) : {elev_std:.2f} m (Extreme Flat Terrain)")
print("-" * 70)
print(f"Mean Surface Slope                   : {mean_slope:.2f}°")
print(f"Ultra-Flat Terrain Fraction (< 1.0°) : {flat_fraction:.2f}% (Explains zero natural runoff)")
print("-" * 70)
print(f"Topographic Depression Sinks Area    : {sink_area_km2:.2f} km²")
print(f"Depression Sinks Vulnerability Ratio : {sink_fraction:.2f}% of urban core")
print("=" * 70)

# Save experiment results
results = {
    "experiment": "Exp_02_Copernicus_DEM_Terrain",
    "pmc_area_km2": round(float(len(pmc_elevations) * 900.0 / 1e6), 2),
    "elevation_min_m": round(min_elev, 2),
    "elevation_max_m": round(max_elev, 2),
    "elevation_mean_m": round(mean_elev, 2),
    "elevation_std_m": round(elev_std, 2),
    "mean_slope_degrees": round(mean_slope, 2),
    "flat_terrain_fraction_pct": round(flat_fraction, 2),
    "depression_sinks_area_km2": round(sink_area_km2, 2),
    "depression_sinks_fraction_pct": round(sink_fraction, 2)
}

with open(os.path.join(EXP_DIR, "exp02_results.json"), "w") as f:
    json.dump(results, f, indent=2)

np.save(os.path.join(OUT_DIR, "patna_dem_elevation_pmc.npy"), dem_pmc)
np.save(os.path.join(OUT_DIR, "patna_dem_slope_pmc.npy"), slope_full)
np.save(os.path.join(OUT_DIR, "patna_dem_sinks_pmc.npy"), is_sink)

print("Experiment 02 execution complete. Results saved to exp02_results.json.")

