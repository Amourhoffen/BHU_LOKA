import json
import os
import requests

def sign_asset_url(href):
    """
    Microsoft Planetary Computer requires asset URLs to be signed via its SAS token endpoint.
    This provides free, open, and public access to actual Sentinel-1 GeoTIFFs.
    """
    sas_endpoint = "https://planetarycomputer.microsoft.com/api/sas/v1/sign"
    headers = {"User-Agent": "BhuLoka-IITPatna-Research/1.0"}
    r = requests.get(sas_endpoint, params={"href": href}, headers=headers, timeout=15)
    if r.status_code == 200:
        return r.json().get("href")
    return href

def fetch_sentinel1_metadata():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(base_dir), "data", "real")
    os.makedirs(output_dir, exist_ok=True)
    
    # Patna Bounding Box: [min_lon, min_lat, max_lon, max_lat]
    bbox = [84.68, 25.20, 86.06, 25.74]
    
    stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
    payload = {
        "collections": ["sentinel-1-grd"],
        "bbox": bbox,
        "datetime": "2019-09-20T00:00:00Z/2019-10-02T23:59:59Z",
        "limit": 10
    }
    
    print("Searching Planetary Computer STAC for authentic Sentinel-1 SAR granules over Patna...")
    r = requests.post(stac_url, json=payload, timeout=25)
    if r.status_code != 200:
        raise RuntimeError(f"STAC search failed with status {r.status_code}")
        
    items = r.json().get("features", [])
    print(f"Found {len(items)} authentic Sentinel-1 scenes covering Patna during the September 2019 event.")
    
    # Identify Baseline (Pre-deluge) and Peak-Deluge (Inundation) scenes
    # Peak Deluge: 29 September 2019
    # Pre-flood Baseline: 23 September 2019
    peak_item = None
    baseline_item = None
    
    for item in items:
        dt = item.get("properties", {}).get("datetime", "")
        if "2019-09-29" in dt and not peak_item:
            peak_item = item
        elif "2019-09-23" in dt and not baseline_item:
            baseline_item = item
            
    if not peak_item or not baseline_item:
        print("Warning: Could not match exact dates, selecting the closest available pair.")
        peak_item = items[0]
        baseline_item = items[-1]
        
    selected_scenes = {
        "baseline_dry_scene": {
            "id": baseline_item["id"],
            "datetime": baseline_item["properties"]["datetime"],
            "orbit_state": baseline_item["properties"].get("sat:orbit_state"),
            "polarizations": baseline_item["properties"].get("sar:polarizations"),
            "assets_summary": list(baseline_item.get("assets", {}).keys()),
            "rendered_preview_url": sign_asset_url(baseline_item.get("assets", {}).get("rendered_preview", {}).get("href", "")),
            "vv_polarization_url": sign_asset_url(baseline_item.get("assets", {}).get("vv", {}).get("href", ""))
        },
        "peak_flood_scene": {
            "id": peak_item["id"],
            "datetime": peak_item["properties"]["datetime"],
            "orbit_state": peak_item["properties"].get("sat:orbit_state"),
            "polarizations": peak_item["properties"].get("sar:polarizations"),
            "assets_summary": list(peak_item.get("assets", {}).keys()),
            "rendered_preview_url": sign_asset_url(peak_item.get("assets", {}).get("rendered_preview", {}).get("href", "")),
            "vv_polarization_url": sign_asset_url(peak_item.get("assets", {}).get("vv", {}).get("href", ""))
        }
    }
    
    manifest_path = os.path.join(output_dir, "sentinel1_2019_deluge_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump(selected_scenes, fp, indent=2)
        
    print(f"\nSaved Sentinel-1 SAR Deluge Manifest to: {manifest_path}")
    print(f"  Baseline Pre-Flood ID: {selected_scenes['baseline_dry_scene']['id']} ({selected_scenes['baseline_dry_scene']['datetime']})")
    print(f"  Peak Inundation ID:   {selected_scenes['peak_flood_scene']['id']} ({selected_scenes['peak_flood_scene']['datetime']})")
    
    # Download the authentic rendered radar previews for quick local inspection
    for key, label in [("baseline_dry_scene", "pre_flood_20190923_preview.png"), ("peak_flood_scene", "peak_flood_20190929_preview.png")]:
        img_url = selected_scenes[key]["rendered_preview_url"]
        if img_url:
            img_path = os.path.join(output_dir, label)
            print(f"Downloading authentic SAR radar preview for {key} -> {img_path}...")
            img_resp = requests.get(img_url, timeout=30)
            if img_resp.status_code == 200:
                with open(img_path, "wb") as f:
                    f.write(img_resp.content)
                print(f"  Successfully downloaded: {label} ({len(img_resp.content) // 1024} KB)")

if __name__ == "__main__":
    fetch_sentinel1_metadata()

