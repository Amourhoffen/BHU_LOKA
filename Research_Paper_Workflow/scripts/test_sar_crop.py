import numpy as np
from scipy.interpolate import LinearNDInterpolator
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

path_post = r"Bhu Loka - भूलोक\Data\02_SAR_Sentinel1\S1B_IW_GRDH_VV_20190929_peak_flood.tif"
with Image.open(path_post) as img:
    tags = img.tag_v2
    tiepoints = tags.get(33922, [])

# Tiepoints: px, py, pz, lon, lat, alt
pts = []
for i in range(0, len(tiepoints), 6):
    px, py, pz, lon, lat, alt = tiepoints[i:i+6]
    pts.append((px, py, lon, lat))
pts = np.array(pts)

# lon, lat -> px, py interpolator
lons = pts[:, 2]
lats = pts[:, 3]
pxs = pts[:, 0]
pys = pts[:, 1]

interp_px = LinearNDInterpolator(list(zip(lons, lats)), pxs)
interp_py = LinearNDInterpolator(list(zip(lons, lats)), pys)

# Test Patna Urban Center (25.60N, 85.15E - Rajendra Nagar / Gandhi Maidan)
test_lon, test_lat = 85.15, 25.60
px_center = float(interp_px(test_lon, test_lat))
py_center = float(interp_py(test_lon, test_lat))
print(f"Patna Urban Center (85.15E, 25.60N) maps to pixel ({px_center:.1f}, {py_center:.1f})")

# Test Patna Urban Bounding Box
# Min: 85.01184, 25.53895  |  Max: 85.26419, 25.65105
min_px = float(interp_px(85.26419, 25.65105)) # Notice descending pass orientation
max_px = float(interp_px(85.01184, 25.53895))
min_py = float(interp_py(85.26419, 25.65105))
max_py = float(interp_py(85.01184, 25.53895))

print(f"Pixel bounds for Patna Urban: X=[{min(min_px, max_px):.0f}, {max(min_px, max_px):.0f}], Y=[{min(min_py, max_py):.0f}, {max(min_py, max_py):.0f}]")
crop_w = abs(max_px - min_px)
crop_h = abs(max_py - min_py)
print(f"Cropped Urban Patch Dimensions: {crop_w:.0f} x {crop_h:.0f} pixels (~10m resolution)")

