"""
BHU LOKA - Automated Download Script
Downloads all no-login-required datasets directly into the Data folder.

Datasets:
  1. GADM India Level-2 (Patna district boundary — high quality)
  2. Copernicus GLO-30 DEM (30m elevation, two tiles covering Patna)
  3. WorldPop India 2020 1km (population density)
  4. CGIAR SRTM (backup DEM tiles)
  5. Planetary Computer Sentinel-1 STAC search (metadata for real download links)
"""
import urllib.request
import os
import json
import time

BASE = r"Bhu Loka - भूलोक\Data"

def download(name, url, dest_path, expected_mb=None):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if os.path.exists(dest_path):
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"[SKIP] {name} already exists ({size_mb:.1f} MB)")
        return True
    
    print(f"\n[DOWNLOAD] {name}")
    print(f"  URL: {url[:80]}...")
    print(f"  Dest: {dest_path}")
    if expected_mb:
        print(f"  Expected size: ~{expected_mb} MB")
    
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 BHU-LOKA-Research/1.0"
        })
        
        downloaded = 0
        chunk = 1024 * 1024  # 1MB chunks
        
        with urllib.request.urlopen(req, timeout=120) as r, open(dest_path, "wb") as f:
            total = int(r.headers.get("Content-Length", 0))
            while True:
                data = r.read(chunk)
                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                if total > 0:
                    pct = downloaded * 100 // total
                    print(f"  Progress: {pct}% ({downloaded / (1024*1024):.1f} / {total / (1024*1024):.1f} MB)", end="\r")
        
        final_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"\n  [DONE] {name}: {final_mb:.1f} MB saved.")
        return True
        
    except Exception as e:
        print(f"\n  [ERROR] {name}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False


# =============================================================================
# 1. COPERNICUS GLO-30 DEM (30m elevation) — AWS Open Data, no login needed
#    Two tiles cover Patna: N25E084 and N25E085
# =============================================================================
print("\n" + "="*60)
print("1. COPERNICUS GLO-30 DEM (30m Elevation)")
print("="*60)

dem_base = "https://copernicus-dem-30m.s3.amazonaws.com"

download(
    "GLO30_DEM_Tile_N25_E084",
    f"{dem_base}/Copernicus_DSM_COG_10_N25_00_E084_00_DEM/Copernicus_DSM_COG_10_N25_00_E084_00_DEM.tif",
    os.path.join(BASE, "04_DEM_SRTM", "glo30_N25_E084.tif"),
    expected_mb=42
)

download(
    "GLO30_DEM_Tile_N25_E085",
    f"{dem_base}/Copernicus_DSM_COG_10_N25_00_E085_00_DEM/Copernicus_DSM_COG_10_N25_00_E085_00_DEM.tif",
    os.path.join(BASE, "04_DEM_SRTM", "glo30_N25_E085.tif"),
    expected_mb=42
)


# =============================================================================
# 2. WORLDPOP INDIA 2020 (1km — faster to download, good for initial test)
# =============================================================================
print("\n" + "="*60)
print("2. WorldPop India 2020 Population Density (1km)")
print("="*60)

download(
    "WorldPop_India_2020_1km",
    "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/IND/ind_ppp_2020_1km_Aggregated.tif",
    os.path.join(BASE, "07_Population_WorldPop", "worldpop_india_2020_1km.tif"),
    expected_mb=18
)


# =============================================================================
# 3. GADM INDIA Level-2 Boundaries (GeoPackage ~52 MB)
#    Contains all districts of India — we'll extract Patna in processing
# =============================================================================
print("\n" + "="*60)
print("3. GADM India Level-2 Administrative Boundaries")
print("="*60)

download(
    "GADM_India_Level2_GeoPackage",
    "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_IND.gpkg",
    os.path.join(BASE, "01_Boundaries", "gadm41_IND_level2.gpkg"),
    expected_mb=52
)


# =============================================================================
# 4. PLANETARY COMPUTER STAC — Query Sentinel-1 scene metadata for 2019
#    This gets the exact download URLs for the Sentinel-1 flood scenes
#    Actual full GeoTIFF download still needs Planetary Computer token
# =============================================================================
print("\n" + "="*60)
print("4. Planetary Computer — Sentinel-1 SAR Scene Metadata (Sep 2019)")
print("="*60)

stac_url = (
    "https://planetarycomputer.microsoft.com/api/stac/v1/search"
    "?collections=sentinel-1-grd"
    "&bbox=84.68,25.20,86.10,25.75"
    "&datetime=2019-09-20T00:00:00Z/2019-10-02T23:59:59Z"
    "&limit=10"
)

try:
    req = urllib.request.Request(stac_url, headers={"User-Agent": "BHU-LOKA/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    
    manifest_path = os.path.join(BASE, "02_SAR_Sentinel1", "sentinel1_full_stac_manifest_2019.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    n = len(data.get("features", []))
    print(f"  [DONE] Found {n} Sentinel-1 scenes. Manifest saved.")
    
    print(f"\n  Scenes available:")
    for feat in data.get("features", []):
        dt = feat["properties"].get("datetime", "")
        pid = feat.get("id", "")
        platform = feat["properties"].get("platform", "")
        mode = feat["properties"].get("sar:instrument_mode", "")
        print(f"    - {pid[:50]}  |  {dt[:10]}  |  {platform}  |  {mode}")
        
except Exception as e:
    print(f"  [ERROR] STAC query: {e}")


# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*60)
print("DOWNLOAD SUMMARY")
print("="*60)

check_files = [
    ("DEM Tile N25E084", os.path.join(BASE, "04_DEM_SRTM", "glo30_N25_E084.tif")),
    ("DEM Tile N25E085", os.path.join(BASE, "04_DEM_SRTM", "glo30_N25_E085.tif")),
    ("WorldPop 1km", os.path.join(BASE, "07_Population_WorldPop", "worldpop_india_2020_1km.tif")),
    ("GADM Boundaries", os.path.join(BASE, "01_Boundaries", "gadm41_IND_level2.gpkg")),
    ("Sentinel-1 Manifest", os.path.join(BASE, "02_SAR_Sentinel1", "sentinel1_full_stac_manifest_2019.json")),
]

for name, path in check_files:
    if os.path.exists(path):
        mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  [OK]   {name}: {mb:.1f} MB")
    else:
        print(f"  [MISS] {name}: NOT FOUND")

