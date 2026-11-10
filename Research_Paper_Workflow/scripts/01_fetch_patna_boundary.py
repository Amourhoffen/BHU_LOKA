import json
import math
import os
import requests

def fetch_boundary(query, output_path, name_label):
    print(f"Fetching real boundary for: '{query}' from OpenStreetMap Nominatim...")
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "geojson",
        "polygon_geojson": 1,
        "limit": 5
    }
    headers = {"User-Agent": "BhuLoka-Research-IITPatna/1.0 (contact: prince_pa2511cdh37@iitp.ac.in)"}
    
    response = requests.get(url, params=params, headers=headers, timeout=25)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP Error {response.status_code} while fetching {query}")
        
    data = response.json()
    features = data.get("features", [])
    if not features:
        raise ValueError(f"No spatial features found for query: {query}")
        
    # Pick the feature that is a Polygon or MultiPolygon
    selected_feat = None
    for f in features:
        geom_type = f.get("geometry", {}).get("type", "")
        if geom_type in ["Polygon", "MultiPolygon"]:
            selected_feat = f
            break
            
    if not selected_feat:
        selected_feat = features[0]
        
    # Save FeatureCollection
    fc = {
        "type": "FeatureCollection",
        "name": name_label,
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": [selected_feat]
    }
    
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(fc, fp, indent=2)
        
    print(f"Saved real GeoJSON to: {output_path}")
    return selected_feat

def compute_spatial_stats(feat):
    geom = feat.get("geometry", {})
    geom_type = geom.get("type", "")
    coords = geom.get("coordinates", [])
    
    # Flatten all coordinate pairs
    all_pts = []
    if geom_type == "Polygon":
        for ring in coords:
            all_pts.extend(ring)
    elif geom_type == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                all_pts.extend(ring)
                
    if not all_pts:
        return {}
        
    lons = [p[0] for p in all_pts]
    lats = [p[1] for p in all_pts]
    
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    center_lon = sum(lons) / len(lons)
    center_lat = sum(lats) / len(lats)
    
    # Approximate bounding box dimensions
    lat_dist_km = (max_lat - min_lat) * 111.0
    lon_dist_km = (max_lon - min_lon) * 111.0 * math.cos(math.radians(center_lat))
    bbox_area_km2 = lat_dist_km * lon_dist_km
    
    return {
        "geometry_type": geom_type,
        "vertex_count": len(all_pts),
        "min_longitude": round(min_lon, 5),
        "max_longitude": round(max_lon, 5),
        "min_latitude": round(min_lat, 5),
        "max_latitude": round(max_lat, 5),
        "centroid_longitude": round(center_lon, 5),
        "centroid_latitude": round(center_lat, 5),
        "bbox_east_west_km": round(lon_dist_km, 2),
        "bbox_north_south_km": round(lat_dist_km, 2),
        "bbox_bounding_area_km2": round(bbox_area_km2, 2)
    }

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(base_dir), "data", "real")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Fetch Patna District Boundary
    district_path = os.path.join(output_dir, "patna_district_boundary.geojson")
    district_feat = fetch_boundary("Patna District, Bihar, India", district_path, "patna_district")
    district_stats = compute_spatial_stats(district_feat)
    
    # 2. Fetch Patna Urban Core Boundary
    urban_path = os.path.join(output_dir, "patna_urban_boundary.geojson")
    urban_feat = fetch_boundary("Patna, Bihar, India", urban_path, "patna_urban")
    urban_stats = compute_spatial_stats(urban_feat)
    
    # 3. Save Summary Metadata
    metadata = {
        "source": "OpenStreetMap Nominatim API",
        "coordinate_reference_system": "EPSG:4326 (WGS84)",
        "patna_district": {
            "display_name": district_feat.get("properties", {}).get("display_name"),
            "osm_id": district_feat.get("properties", {}).get("osm_id"),
            "stats": district_stats
        },
        "patna_urban": {
            "display_name": urban_feat.get("properties", {}).get("display_name"),
            "osm_id": urban_feat.get("properties", {}).get("osm_id"),
            "stats": urban_stats
        }
    }
    
    meta_path = os.path.join(output_dir, "patna_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as fp:
        json.dump(metadata, fp, indent=2)
        
    print(f"Saved metadata to: {meta_path}")
    print("\n--- PATNA DISTRICT SPATIAL SUMMARY ---")
    for k, v in district_stats.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()

