import urllib.request
import urllib.parse
import json

url = (
    "https://planetarycomputer.microsoft.com/api/stac/v1/search"
    "?collections=sentinel-2-l2a"
    "&bbox=84.95,25.45,85.25,25.70"
    "&datetime=2019-05-01T00:00:00Z/2019-05-31T23:59:59Z"
    "&limit=5"
)
req = urllib.request.Request(url, headers={"User-Agent": "BHU-LOKA/1.0"})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r)
        features = d.get("features", [])
        print(f"Found {len(features)} Sentinel-2 scenes for Patna in May 2019:")
        for f in features:
            fid = f["id"]
            dt = f["properties"]["datetime"][:10]
            cloud = f["properties"].get("eo:cloud_cover", 0)
            print(f"  - {fid} | Date: {dt} | Cloud: {cloud:.1f}%")
except Exception as e:
    print("Error:", e)

