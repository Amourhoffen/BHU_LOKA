import numpy as np
from scipy.interpolate import LinearNDInterpolator
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

def get_geo_interpolators(tif_path):
    with Image.open(tif_path) as img:
        tags = img.tag_v2
        tiepoints = tags.get(33922, [])
    pts = []
    for i in range(0, len(tiepoints), 6):
        px, py, pz, lon, lat, alt = tiepoints[i:i+6]
        pts.append((px, py, lon, lat))
    pts = np.array(pts)
    interp_px = LinearNDInterpolator(list(zip(pts[:, 2], pts[:, 3])), pts[:, 0])
    interp_py = LinearNDInterpolator(list(zip(pts[:, 2], pts[:, 3])), pts[:, 1])
    return interp_px, interp_py

path_post = r"Bhu Loka - भूलोक\Data\02_SAR_Sentinel1\S1B_IW_GRDH_VV_20190929_peak_flood.tif"
path_pre = r"Bhu Loka - भूलोक\Data\02_SAR_Sentinel1\S1A_IW_GRDH_VV_20190923_pre_flood.tif"

print("Checking Post scene (29 Sep 2019)...")
post_px, post_py = get_geo_interpolators(path_post)
print("Checking Pre scene (23 Sep 2019)...")
pre_px, pre_py = get_geo_interpolators(path_pre)

# Patna District Bounding Box: Lon 84.70 to 85.55, Lat 25.25 to 25.70
corners = [
    (84.70, 25.25),
    (85.55, 25.25),
    (84.70, 25.70),
    (85.55, 25.70)
]

print("\nPost Scene Coordinates:")
for lon, lat in corners:
    print(f"  ({lon:.2f}E, {lat:.2f}N) -> px: {float(post_px(lon, lat)):.1f}, py: {float(post_py(lon, lat)):.1f}")

print("\nPre Scene Coordinates:")
for lon, lat in corners:
    print(f"  ({lon:.2f}E, {lat:.2f}N) -> px: {float(pre_px(lon, lat)):.1f}, py: {float(pre_py(lon, lat)):.1f}")

