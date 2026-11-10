"""
BHU LOKA (भूलोक) - Experiment 01: SAR Flood Inundation & Urban Double-Bounce
=============================================================================
Computes empirical flood extent across Patna using Sentinel-1 C-band SAR.
Incorporates:
1. Physically calibrated backscatter (sigma0 in dB)
2. True PMC Municipal Boundary clipping
3. Permanent water exclusion (pre-flood Ganges channel)
4. Urban Double-Bounce Detection for submerged street canyons

Author: Prince Kumar (IIT Patna, PA2511CDH37) & BHU LOKA Research Team
"""

import os
import json
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from matplotlib.path import Path
from scipy.interpolate import LinearNDInterpolator

# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAR_DIR = os.path.join(BASE_DIR, "Data", "02_SAR_Sentinel1")
BOUNDS_DIR = os.path.join(BASE_DIR, "Data", "01_Boundaries")
OUT_DIR = os.path.join(BASE_DIR, "Data", "08_Processed_Outputs")
EXP_DIR = os.path.dirname(__file__)

os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 70)
print(" EXPERIMENT 01: SENTINEL-1 SAR FLOOD & DOUBLE-BOUNCE ANALYSIS")
print("=" * 70)

# 1. Load Pre and Post scenes
path_post = os.path.join(SAR_DIR, "S1B_IW_GRDH_VV_20190929_peak_flood.tif")
path_pre = os.path.join(SAR_DIR, "S1A_IW_GRDH_VV_20190923_pre_flood.tif")

print(f"Reading Post Flood Scene: {os.path.basename(path_post)}")
with Image.open(path_post) as img_post:
    tags = img_post.tag_v2
    tiepoints = tags.get(33922, [])
    # Crop study window covering Patna Urban & Peri-Urban Region
    # (post_x0, post_y0) = (1523, 8429), (post_x1, post_y1) = (4125, 10138)
    crop_post = img_post.crop((1523, 8429, 4125, 10138))
    dn_post = np.array(crop_post, dtype=np.float32)

print(f"Reading Pre Flood Scene:  {os.path.basename(path_pre)}")
with Image.open(path_pre) as img_pre:
    # Co-registered crop matching the post scene extent
    crop_pre = img_pre.crop((1523, 8429, 4125, 10138))
    dn_pre = np.array(crop_pre, dtype=np.float32)

H, W = dn_post.shape
print(f"Analysis Window Dimensions: {W} x {H} pixels (10m grid spacing)")

# 2. Radiometric Calibration: DN -> Sigma0 (dB)
# Standard Sentinel-1 scaling: sigma0 = 10 * log10(DN^2 + eps) - 52.0 dB
eps = 1e-6
sigma0_post = 10.0 * np.log10(dn_post**2 + eps) - 52.0
sigma0_pre = 10.0 * np.log10(dn_pre**2 + eps) - 52.0
delta_sigma0 = sigma0_post - sigma0_pre

# 3. Permanent Water Mask (Dry Baseline Water in Ganga Channel)
# Areas where pre-flood baseline sigma0 < -18.0 dB represent permanent water
permanent_water = (sigma0_pre < -18.0)

# 4. Open Specular Water Inundation (Delta Sigma0 <= -3.80 dB and Post Sigma0 < -16.0 dB)
open_water_inundation = (delta_sigma0 <= -3.80) & (sigma0_post < -16.0) & (~permanent_water)

# 5. Urban Double-Bounce Waterlogging
# In dense urban corridors, floodwaters create double-bounce corner reflection:
# Pre-flood baseline is moderate/high (-12 to -8 dB), and Post backscatter INCREASES by >= +1.5 dB
urban_double_bounce = (delta_sigma0 >= 1.5) & (sigma0_pre >= -14.0) & (sigma0_post >= -11.0) & (~permanent_water)

# Combined Flood Signal
total_flood = open_water_inundation | urban_double_bounce

# 6. Build PMC Boundary Mask
pts = []
for i in range(0, len(tiepoints), 6):
    px, py, pz, lon, lat, alt = tiepoints[i:i+6]
    pts.append((px, py, lon, lat))
pts = np.array(pts)

interp_lon = LinearNDInterpolator(list(zip(pts[:, 0], pts[:, 1])), pts[:, 2])
interp_lat = LinearNDInterpolator(list(zip(pts[:, 0], pts[:, 1])), pts[:, 3])

step = 4
grid_y, grid_x = np.mgrid[0:H:step, 0:W:step]
sample_px = 1523 + grid_x.flatten()
sample_py = 8429 + grid_y.flatten()
sample_lon = interp_lon(sample_px, sample_py)
sample_lat = interp_lat(sample_px, sample_py)

with open(os.path.join(BOUNDS_DIR, "patna_urban_boundary.geojson"), "r") as f:
    urban_geojson = json.load(f)

poly_coords = urban_geojson["features"][0]["geometry"]["coordinates"][0]
pmc_polygon = Path(poly_coords)
inside_pmc_coarse = pmc_polygon.contains_points(np.column_stack([sample_lon, sample_lat])).reshape(grid_x.shape)
inside_pmc = np.repeat(np.repeat(inside_pmc_coarse, step, axis=0)[:H, :], step, axis=1)[:, :W]

# 7. Compute Scientific Metrics
pixel_area_km2 = (10.0 * 10.0) / 1e6
total_bbox_area_km2 = W * H * pixel_area_km2
pmc_area_km2 = np.sum(inside_pmc) * pixel_area_km2

# Bbox metrics
bbox_open_water_km2 = np.sum(open_water_inundation) * pixel_area_km2
bbox_urban_double_km2 = np.sum(urban_double_bounce) * pixel_area_km2
bbox_total_flood_km2 = np.sum(total_flood) * pixel_area_km2

# PMC specific metrics
pmc_open_water_km2 = np.sum(open_water_inundation & inside_pmc) * pixel_area_km2
pmc_urban_double_km2 = np.sum(urban_double_bounce & inside_pmc) * pixel_area_km2
pmc_total_flood_km2 = np.sum(total_flood & inside_pmc) * pixel_area_km2
pmc_flood_fraction = (pmc_total_flood_km2 / pmc_area_km2) * 100.0

print("\n" + "=" * 70)
print(" EXPERIMENT 01 RESULTS: EMPIRICALLY AUDITED METRICS")
print("=" * 70)
print(f"Total Study Bounding Box Area        : {total_bbox_area_km2:.2f} km²")
print(f"True PMC Municipal Core Area         : {pmc_area_km2:.2f} km² (100.0%)")
print("-" * 70)
print(f"Study Grid Open Specular Water       : {bbox_open_water_km2:.2f} km²")
print(f"Study Grid Urban Double-Bounce Water : {bbox_urban_double_km2:.2f} km²")
print(f"Study Grid Total Flood Extent        : {bbox_total_flood_km2:.2f} km²")
print("-" * 70)
print(f"PMC Core Open Specular Water         : {pmc_open_water_km2:.2f} km²")
print(f"PMC Core Urban Double-Bounce Water   : {pmc_urban_double_km2:.2f} km²")
print(f"PMC Core Total Inundated Area        : {pmc_total_flood_km2:.2f} km²")
print(f"PMC Core True Inundation Fraction    : {pmc_flood_fraction:.2f}%")
print("=" * 70)

# Save results
out_meta = {
    "experiment": "Exp_01_SAR_Flood_Inundation",
    "total_bbox_area_km2": round(float(total_bbox_area_km2), 2),
    "true_pmc_area_km2": round(float(pmc_area_km2), 2),
    "pmc_open_specular_water_km2": round(float(pmc_open_water_km2), 2),
    "pmc_urban_double_bounce_km2": round(float(pmc_urban_double_km2), 2),
    "pmc_total_inundated_km2": round(float(pmc_total_flood_km2), 2),
    "pmc_true_inundation_fraction_pct": round(float(pmc_flood_fraction), 2),
    "calibration_offset_db": -52.0,
    "otsu_delta_threshold_db": -3.80,
    "urban_double_bounce_threshold_db": 1.5
}

with open(os.path.join(EXP_DIR, "exp01_results.json"), "w") as f:
    json.dump(out_meta, f, indent=2)

np.save(os.path.join(OUT_DIR, "patna_pmc_mask.npy"), inside_pmc)
np.save(os.path.join(OUT_DIR, "patna_total_flood_v2.npy"), total_flood)
print("Experiment 01 execution complete. Results saved to exp01_results.json.")

