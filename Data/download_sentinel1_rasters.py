"""
Download Sentinel-1 SAR VV rasters from Microsoft Planetary Computer
using SAS token signing API.
Target scenes:
  1. Peak Flood: S1B_IW_GRDH_1SDV_20190929T001924_20190929T001949_018245_0225AB
  2. Pre-Flood Baseline: S1A_IW_GRDH_1SDV_20190923T002001_20190923T002026_029141_034EEC
"""
import urllib.request
import urllib.parse
import json
import os
import sys

DEST_DIR = r"Bhu Loka - भूलोक\Data\02_SAR_Sentinel1"
MANIFEST_FILE = os.path.join(DEST_DIR, "sentinel1_full_stac_manifest_2019.json")

def sign_url(raw_url):
    sign_api = f"https://planetarycomputer.microsoft.com/api/sas/v1/sign?href={urllib.parse.quote(raw_url)}"
    req = urllib.request.Request(sign_api, headers={"User-Agent": "BHU-LOKA/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
        return data["href"]

def download_file(signed_url, dest_path, label):
    if os.path.exists(dest_path):
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"[SKIP] {label} already exists: {size_mb:.2f} MB")
        return True

    print(f"\n[STARTING DOWNLOAD] {label}")
    print(f"Target file: {dest_path}")
    
    req = urllib.request.Request(signed_url, headers={"User-Agent": "BHU-LOKA/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest_path, "wb") as f:
        total_bytes = int(r.headers.get("Content-Length", 0))
        total_mb = total_bytes / (1024 * 1024)
        print(f"Total size: {total_mb:.2f} MB")
        
        downloaded = 0
        chunk_size = 2 * 1024 * 1024  # 2MB chunks
        last_pct = -1
        
        while True:
            chunk = r.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            pct = int((downloaded / total_bytes) * 100) if total_bytes > 0 else 0
            if pct != last_pct and pct % 5 == 0:
                print(f"  Downloading {label}: {pct}% ({downloaded / (1024*1024):.1f} / {total_mb:.1f} MB)", flush=True)
                last_pct = pct

    print(f"[COMPLETED] {label} downloaded successfully!")
    return True

def main():
    if not os.path.exists(MANIFEST_FILE):
        print(f"Manifest not found: {MANIFEST_FILE}")
        return

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for feat in manifest.get("features", []):
        fid = feat["id"]
        # Download 29 Sep (Peak Flood) VV band
        if "20190929" in fid:
            vv_raw = feat["assets"]["vv"]["href"]
            dest = os.path.join(DEST_DIR, "S1B_IW_GRDH_VV_20190929_peak_flood.tif")
            print("\nSigning URL for 29 Sep 2019 Peak Flood VV band...")
            signed = sign_url(vv_raw)
            download_file(signed, dest, "29-Sep-2019 Peak Flood VV")
            
        # Download 23 Sep (Pre-flood Dry Baseline) VV band
        elif "20190923T002001" in fid:
            vv_raw = feat["assets"]["vv"]["href"]
            dest = os.path.join(DEST_DIR, "S1A_IW_GRDH_VV_20190923_pre_flood.tif")
            print("\nSigning URL for 23 Sep 2019 Pre-Flood Dry VV band...")
            signed = sign_url(vv_raw)
            download_file(signed, dest, "23-Sep-2019 Pre-Flood VV")

if __name__ == "__main__":
    main()

