import os
import json
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from matplotlib.path import Path
from scipy.interpolate import LinearNDInterpolator

SAR_DIR = r"Bhu Loka - भूलोक\Data\02_SAR_Sentinel1"
OUT_DIR = r"Bhu Loka - भूलोक\Data\08_Processed_Outputs"
BOUNDS_DIR = r"Bhu Loka - भूलोक\Data\01_Boundaries"

# 1. Load the inundation mask and delta sigma0
mask_path = os.path.join(OUT_DIR, "patna_2019_flood_extent_empirical.npy")
delta_path = os.path.join(OUT_DIR, "patna_2019_delta_sigma0.npy")
inundation = np.load(mask_path)
delta = np.load(delta_path)

h, w = inundation.shape
print(f"Raster dimensions: {w} x {h} pixels")

# 2. Get the crop bounds and tiepoints for the Post scene
path_post = os.path.join(SAR_DIR, "S1B_IW_GRDH_VV_20190929_peak_flood.tif")
with Image.open(path_post) as img:
    tags = img.tag_v2
    tiepoints = tags.get(33922, [])

pts = []
for i in range(0, len(tiepoints), 6):
    px, py, pz, lon, lat, alt = tiepoints[i:i+6]
    pts.append((px, py, lon, lat))
pts = np.array(pts)

# Forward interpolator: px, py -> lon, lat
interp_lon = LinearNDInterpolator(list(zip(pts[:, 0], pts[:, 1])), pts[:, 2])
interp_lat = LinearNDInterpolator(list(zip(pts[:, 0], pts[:, 1])), pts[:, 3])

# The crop window used earlier:
post_x0, post_y0 = 1523, 8429
post_x1, post_y1 = 4125, 10138

# 3. Load PMC Boundary Polygon
with open(os.path.join(BOUNDS_DIR, "patna_urban_boundary.geojson"), "r") as f:
    urban_geojson = json.load(f)

poly_coords = urban_geojson["features"][0]["geometry"]["coordinates"][0]
pmc_polygon = Path(poly_coords)

# 4. Create a grid of pixel centers in lon, lat
# Downsample grid by 4x for speed of polygon testing, then scale
step = 4
grid_y, grid_x = np.mgrid[0:h:step, 0:w:step]
sample_px = post_x0 + grid_x.flatten()
sample_py = post_y0 + grid_y.flatten()

sample_lon = interp_lon(sample_px, sample_py)
sample_lat = interp_lat(sample_px, sample_py)

pts_lonlat = np.column_stack([sample_lon, sample_lat])
inside_pmc_coarse = pmc_polygon.contains_points(pts_lonlat).reshape(grid_x.shape)

# Resize to full raster
inside_pmc_full = np.repeat(np.repeat(inside_pmc_coarse, step, axis=0)[:h, :], step, axis=1)[:, :w]

# 5. Calculate PMC specific metrics
pmc_pixels = np.sum(inside_pmc_full)
pmc_flooded_pixels = np.sum(inundation & inside_pmc_full)

pixel_area_km2 = (10.0 * 10.0) / 1e6
pmc_area_km2 = pmc_pixels * pixel_area_km2
pmc_flood_km2 = pmc_flooded_pixels * pixel_area_km2
pmc_flood_pct = (pmc_flooded_pixels / pmc_pixels) * 100.0

print("\n" + "=" * 65)
print(" RIGOROUS SCIENTIFIC AUDIT: TRUE PMC MUNICIPAL CORE METRICS")
print("=" * 65)
print(f"Rectangular Bounding Box Area       : {w * h * pixel_area_km2:.2f} km²")
print(f"True PMC Municipal Polygon Area     : {pmc_area_km2:.2f} km²")
print(f"Inundation inside TRUE PMC Boundary : {pmc_flood_km2:.2f} km²")
print(f"True PMC Urban Flood Fraction       : {pmc_flood_pct:.2f}%")
print("=" * 65)
