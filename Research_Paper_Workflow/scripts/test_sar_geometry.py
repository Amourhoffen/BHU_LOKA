import json
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# Let's inspect the tie points from the 29 Sep 2019 scene
path_post = r"Bhu Loka - भूलोक\Data\02_SAR_Sentinel1\S1B_IW_GRDH_VV_20190929_peak_flood.tif"
with Image.open(path_post) as img:
    tags = img.tag_v2
    tiepoints = tags.get(33922, [])
    w, h = img.size
    print(f"Post image dimensions: {w} x {h}")
    print(f"Total tiepoint entries: {len(tiepoints) // 6}")

# Convert tiepoints to (pixel_x, pixel_y, lon, lat)
pts = []
for i in range(0, len(tiepoints), 6):
    px, py, pz, lon, lat, alt = tiepoints[i:i+6]
    pts.append((px, py, lon, lat))

pts = np.array(pts)
print(f"Lon range: {pts[:, 2].min():.4f} to {pts[:, 2].max():.4f}")
print(f"Lat range: {pts[:, 3].min():.4f} to {pts[:, 3].max():.4f}")

# Read metadata for Patna bounding box
with open(r"Bhu Loka - भूलोक\Data\01_Boundaries\patna_metadata.json", "r") as f:
    meta = json.load(f)
bbox = meta["bbox"]
print(f"Patna District BBox: {bbox}")

