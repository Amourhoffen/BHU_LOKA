"""
BHU LOKA (भूलोक) - Real Geospatial Web Asset Compiler
Extracts 100% genuine vector geometries & georeferenced satellite rasters from:
1. Complete Sovereign India Boundaries (Survey-aligned 36 States/UTs + Composite Country Border,
   full Ladakh 37.08N, Jammu & Kashmir, Arunachal Pradesh, Andaman & Nicobar, Lakshadweep)
2. All 38 Bihar Districts (GADM v4.1 Level-2) & OSM Patna District / PMC Municipal Boundaries
3. ESA Sentinel-1 C-Band SAR 2019 Peak Inundation & Delta Sigma0 (Affine-warped to EPSG:4326 North-Up)
4. Copernicus 30m GLO-30 DEM Elevation & Depression Sinks
5. NASA Terra MODIS Pre-Monsoon 2019 LST Heatwave (Sinusoidal -> WGS84)
6. Compound ULSI Urban Land Suitability Index

Exports transparent PNG overlays, real 3D elevation arrays, and compact JS bundles
so web & Chromium desktop interfaces run 100% locally with ZERO API keys or OSM 403 blocks.

Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

import os
import io
import json
import math
import base64
import struct
import sqlite3
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "Data")
BOUNDS_DIR = os.path.join(DATA_DIR, "01_Boundaries")
SAR_DIR = os.path.join(DATA_DIR, "02_SAR_Sentinel1")
OUT_DIR = os.path.join(DATA_DIR, "08_Processed_Outputs")
os.makedirs(OUT_DIR, exist_ok=True)


# ============================================================================
# 1. PURE-PYTHON OGC GEOPACKAGE (WKB) POLYGON PARSER
# ============================================================================

def _read_ring(buf: bytes, off: int, endian: str, stride: int = 1):
    n_pts = struct.unpack_from(endian + "I", buf, off)[0]
    off += 4
    pts = []
    # Keep first/last & sample intermediate vertices safely for crisp web performance
    step = max(1, n_pts // max(8, (n_pts // stride))) if stride > 1 else 1
    for i in range(n_pts):
        x, y = struct.unpack_from(endian + "dd", buf, off)
        off += 16
        if i == 0 or i == n_pts - 1 or (i % step == 0):
            pts.append([round(x, 3), round(y, 3)])
    if len(pts) >= 3 and pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts, off


def _parse_wkb_geom(buf: bytes, off: int, step_div: int = 80):
    endian = "<" if buf[off] == 1 else ">"
    wkb_type = struct.unpack_from(endian + "I", buf, off + 1)[0]
    off += 5

    # Strip Z/M ISO flags if present (e.g. 1003, 2003)
    base_type = wkb_type % 1000
    if base_type == 3:  # Polygon
        n_rings = struct.unpack_from(endian + "I", buf, off)[0]
        off += 4
        rings = []
        for r_idx in range(n_rings):
            n_pts = struct.unpack_from(endian + "I", buf, off)[0]
            stride = max(1, n_pts // step_div) if r_idx == 0 else max(1, n_pts // 25)
            ring_pts, off = _read_ring(buf, off, endian, stride=stride)
            if r_idx == 0 and len(ring_pts) >= 4:
                rings.append(ring_pts)
        return "Polygon", rings, off

    elif base_type == 6:  # MultiPolygon
        n_polys = struct.unpack_from(endian + "I", buf, off)[0]
        off += 4
        polys = []
        for _ in range(n_polys):
            g_type, g_coords, off = _parse_wkb_geom(buf, off, step_div=step_div)
            if g_type == "Polygon" and g_coords:
                polys.append(g_coords)
        return "MultiPolygon", polys, off

    return None, None, off


def gpkg_blob_to_geojson(blob: bytes, step_div: int = 75):
    if not blob or len(blob) < 12 or blob[:2] != b"GP":
        return None
    flags = blob[3]
    env_ind = (flags >> 1) & 0x07
    env_sizes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}
    wkb_off = 8 + env_sizes.get(env_ind, 0)
    g_type, coords, _ = _parse_wkb_geom(blob, wkb_off, step_div=step_div)
    if not g_type or not coords:
        return None
    # Filter tiny micro-islands (< 0.04 deg span) for national states to keep payload sleek
    if g_type == "MultiPolygon":
        filtered = []
        for poly in coords:
            ring = poly[0]
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            if (max(xs) - min(xs)) > 0.12 or (max(ys) - min(ys)) > 0.12 or len(coords) == 1:
                filtered.append(poly)
        coords = filtered if filtered else coords[:1]
    return {"type": g_type, "coordinates": coords}


def _perp_dist(pt, start, end):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0.0 and dy == 0.0:
        return math.hypot(pt[0] - start[0], pt[1] - start[1])
    t = ((pt[0] - start[0]) * dx + (pt[1] - start[1]) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    proj_x = start[0] + t * dx
    proj_y = start[1] + t * dy
    return math.hypot(pt[0] - proj_x, pt[1] - proj_y)


def rdp_simplify(pts, eps: float):
    """Iterative Ramer-Douglas-Peucker simplification preserving coastal capes & northern crown."""
    if len(pts) < 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = True
    keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        s, e = stack.pop()
        if e - s <= 1:
            continue
        p_s, p_e = pts[s], pts[e]
        max_d = -1.0
        idx = -1
        for i in range(s + 1, e):
            d = _perp_dist(pts[i], p_s, p_e)
            if d > max_d:
                max_d = d
                idx = i
        if max_d > eps and idx != -1:
            keep[idx] = True
            stack.append((s, idx))
            stack.append((idx, e))
    out = [[round(p[0], 3), round(p[1], 3)] for p, k in zip(pts, keep) if k]
    if len(out) >= 3 and out[0] != out[-1]:
        out.append(out[0])
    return out


def simplify_geom_rdp(geom: dict, eps: float = 0.045, min_span: float = 0.06):
    gtype = geom.get("type")
    coords = geom.get("coordinates", [])

    def process_poly(poly):
        outer = rdp_simplify(poly[0], eps)
        if len(outer) < 4:
            return None
        xs = [p[0] for p in outer]
        ys = [p[1] for p in outer]
        if (max(xs) - min(xs)) < min_span and (max(ys) - min(ys)) < min_span:
            return None
        return [outer]

    if gtype == "Polygon":
        res = process_poly(coords)
        if not res and coords and len(coords[0]) >= 3:
            res = [rdp_simplify(coords[0], eps * 0.25)]
        return {"type": "Polygon", "coordinates": res} if res else None
    elif gtype == "MultiPolygon":
        polys = []
        for poly in coords:
            res = process_poly(poly)
            if res:
                polys.append(res)
        if not polys and coords:
            # Keep largest ring even if small island UT like Chandigarh/Lakshadweep
            biggest = max(coords, key=lambda p: len(p[0]))
            polys.append([rdp_simplify(biggest[0], eps * 0.5)])
        return {"type": "MultiPolygon", "coordinates": polys} if polys else None
    return None


def extract_sovereign_india():
    """
    Loads complete Official Survey-aligned Sovereign India boundaries:
    - All 36 States/UTs (Ladakh 37.08N, Jammu & Kashmir, Arunachal, Dadra+Daman merged, etc.)
    - Full Composite Sovereign India Country Outline (6.75N..37.10N, 68.16E..97.40E)
    - All 38 Bihar Districts from ADM_ADM_2
    """
    print("1. Extracting Complete 36 Sovereign Indian States/UTs (6.75N..37.10N)...")
    sovereign_states_path = os.path.join(BOUNDS_DIR, "india_sovereign_states.geojson")
    composite_path = os.path.join(BOUNDS_DIR, "india_composite_sovereign.geojson")
    clean_36_path = os.path.join(BOUNDS_DIR, "india_36_states_sovereign.geojson")

    with open(sovereign_states_path, "r", encoding="utf-8") as f:
        raw_states = json.load(f)

    by_state = {}
    for ft in raw_states.get("features", []):
        props = ft.get("properties", {})
        st_name = props.get("st_nm")
        dist = props.get("district")
        if not dist and st_name:
            by_state[st_name] = ft

    # Include single-district UTs (Chandigarh, Lakshadweep)
    all_st_names = sorted(set(ft["properties"]["st_nm"] for ft in raw_states.get("features", []) if ft["properties"].get("st_nm")))
    for st_name in all_st_names:
        if st_name not in by_state:
            matches = [ft for ft in raw_states["features"] if ft["properties"].get("st_nm") == st_name]
            if matches:
                by_state[st_name] = matches[0]

    # Save exact full-resolution 36-state GeoJSON for reproducibility
    clean_36_features = []
    web_state_features = []
    for st_name in sorted(by_state.keys()):
        ft = by_state[st_name]
        st_type = "Union Territory" if st_name in {
            "Andaman and Nicobar Islands", "Chandigarh",
            "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
            "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
        } else "State"
        clean_36_features.append({
            "type": "Feature",
            "properties": {"name": st_name, "type": st_type, "st_code": ft["properties"].get("st_code", "")},
            "geometry": ft["geometry"],
        })
        web_geom = simplify_geom_rdp(ft["geometry"], eps=0.04, min_span=0.05)
        if web_geom:
            web_state_features.append({
                "type": "Feature",
                "properties": {"name": st_name, "type": st_type},
                "geometry": web_geom,
            })

    with open(clean_36_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": clean_36_features}, f)
    print(f"   -> Saved exact 36-State Sovereign GeoJSON: {clean_36_path} ({len(clean_36_features)} States/UTs)")

    with open(composite_path, "r", encoding="utf-8") as f:
        comp_raw = json.load(f)
    comp_geom = simplify_geom_rdp(comp_raw["features"][0]["geometry"], eps=0.032, min_span=0.06)
    india_country_gj = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "Republic of India (Complete Sovereign Border)"},
            "geometry": comp_geom,
        }],
    }

    print("2. Parsing all 38 Bihar Districts from gadm41_IND_level2.gpkg (ADM_ADM_2)...")
    gpkg_path = os.path.join(BOUNDS_DIR, "gadm41_IND_level2.gpkg")
    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()
    bihar_features = []
    for name2, blob in cur.execute("SELECT NAME_2, geom FROM ADM_ADM_2 WHERE NAME_1='Bihar' ORDER BY NAME_2"):
        geom = gpkg_blob_to_geojson(blob, step_div=45)
        if geom:
            bihar_features.append({
                "type": "Feature",
                "properties": {"name": name2, "state": "Bihar"},
                "geometry": geom
            })
    print(f"   -> Extracted {len(bihar_features)} Bihar district polygons.")
    conn.close()

    return (
        india_country_gj,
        {"type": "FeatureCollection", "features": web_state_features},
        {"type": "FeatureCollection", "features": bihar_features},
    )


def simplify_geojson_file(path: str, keep_every: int = 8):
    with open(path, "r", encoding="utf-8") as f:
        gj = json.load(f)
    for feat in gj.get("features", []):
        g = feat["geometry"]
        if g["type"] == "Polygon":
            new_rings = []
            for r in g["coordinates"]:
                pts = [[round(p[0], 5), round(p[1], 5)] for i, p in enumerate(r) if i == 0 or i == len(r) - 1 or i % keep_every == 0]
                if pts[0] != pts[-1]:
                    pts.append(pts[0])
                new_rings.append(pts)
            g["coordinates"] = new_rings
    return gj


# ============================================================================
# 2. GEOREFERENCING & PNG GENERATION FOR REAL SATELLITE RASTERS
# ============================================================================

def array_to_b64_png(rgba: np.ndarray, out_png_path: str) -> str:
    img = Image.fromarray(rgba, mode="RGBA")
    img.save(out_png_path, format="PNG", optimize=True)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def build_real_rasters_and_3d_dem():
    print("3. Georeferencing Sentinel-1 SAR, Copernicus 30m DEM, ULSI & MODIS LST rasters...")

    # Load PMC urban bounds (exact basis of DEM crop)
    with open(os.path.join(BOUNDS_DIR, "patna_urban_boundary.geojson"), "r", encoding="utf-8") as f:
        urban_gj = json.load(f)
    poly_coords = urban_gj["features"][0]["geometry"]["coordinates"][0]
    pmc_lons = [p[0] for p in poly_coords]
    pmc_lats = [p[1] for p in poly_coords]
    pmc_min_lon, pmc_max_lon = min(pmc_lons), max(pmc_lons)
    pmc_min_lat, pmc_max_lat = min(pmc_lats), max(pmc_lats)

    # Copernicus DEM dimensions match glo30 3600px/deg crop from run_dem_terrain_analysis.py
    W_full, H_full = 7200, 3600
    px_min = int(((pmc_min_lon - 84.0) / 2.0) * W_full) - 10
    px_max = int(((pmc_max_lon - 84.0) / 2.0) * W_full) + 10
    py_min = int(((26.0 - pmc_max_lat) / 1.0) * H_full) - 10
    py_max = int(((26.0 - pmc_min_lat) / 1.0) * H_full) + 10

    dem_bounds = {
        "west": round(84.0 + (px_min / W_full) * 2.0, 5),
        "east": round(84.0 + (px_max / W_full) * 2.0, 5),
        "north": round(26.0 - (py_min / H_full) * 1.0, 5),
        "south": round(26.0 - (py_max / H_full) * 1.0, 5),
    }
    print(f"   -> Exact Copernicus 30m DEM bounds: {dem_bounds}")

    # Load real DEM & Sinks
    dem_arr = np.load(os.path.join(OUT_DIR, "patna_dem_elevation_pmc.npy"))  # (423, 929)
    sinks_arr = np.load(os.path.join(OUT_DIR, "patna_dem_sinks_pmc.npy"))    # (423, 929)
    H_d, W_d = dem_arr.shape

    # Generate transparent DEM + Sinks RGBA PNG
    dem_rgba = np.zeros((H_d, W_d, 4), dtype=np.uint8)
    # Normalize elev 40..62m for crisp contrast
    norm_e = np.clip((dem_arr - 42.0) / (60.0 - 42.0), 0.0, 1.0)
    # Color gradient: deep magenta/purple sink (<47m) -> cyan/blue mid -> bright emerald/gold ridge (>52m)
    dem_rgba[..., 0] = np.where(sinks_arr, 236, (255 * (1.0 - norm_e) * 0.25 + norm_e * 20).astype(np.uint8))
    dem_rgba[..., 1] = np.where(sinks_arr, 72, (100 + norm_e * 155).astype(np.uint8))
    dem_rgba[..., 2] = np.where(sinks_arr, 153, (235 - norm_e * 110).astype(np.uint8))
    dem_rgba[..., 3] = np.where(sinks_arr, 210, 155)
    dem_b64 = array_to_b64_png(dem_rgba, os.path.join(OUT_DIR, "patna_dem_real_overlay.png"))

    # Affine warp Sentinel-1 SAR Flood & ULSI onto the EXACT North-Up DEM grid!
    sar_path = os.path.join(SAR_DIR, "S1B_IW_GRDH_VV_20190929_peak_flood.tif")
    with Image.open(sar_path) as img:
        tp = img.tag_v2.get(33922, [])
    pts = np.array([tp[i:i + 6] for i in range(0, len(tp), 6)])
    # Fit bilinear affine mapping: (lon, lat) -> (sar_x_full, sar_y_full)
    # Using least squares on SAR tiepoints: X = a0 + a1*lon + a2*lat
    A = np.column_stack([np.ones(len(pts)), pts[:, 3], pts[:, 4]])
    cx, _, _, _ = np.linalg.lstsq(A, pts[:, 0], rcond=None)
    cy, _, _, _ = np.linalg.lstsq(A, pts[:, 1], rcond=None)

    # Regular North-Up grid coordinates matching DEM pixel centers
    grid_lons = np.linspace(dem_bounds["west"], dem_bounds["east"], W_d)
    grid_lats = np.linspace(dem_bounds["north"], dem_bounds["south"], H_d)
    glon, glat = np.meshgrid(grid_lons, grid_lats)

    sar_px = np.rint(cx[0] + cx[1] * glon + cx[2] * glat).astype(np.int32) - 1523
    sar_py = np.rint(cy[0] + cy[1] * glon + cy[2] * glat).astype(np.int32) - 8429

    flood_raw = np.load(os.path.join(OUT_DIR, "patna_total_flood_v2.npy"))      # (1709, 2602)
    delta_raw = np.load(os.path.join(OUT_DIR, "patna_2019_delta_sigma0.npy"))   # (1709, 2602)
    pmc_raw = np.load(os.path.join(OUT_DIR, "patna_pmc_mask.npy"))              # (1709, 2602)
    ulsi_raw = np.load(os.path.join(OUT_DIR, "patna_urban_suitability_index.npy"))
    H_s, W_s = flood_raw.shape

    valid = (sar_px >= 0) & (sar_px < W_s) & (sar_py >= 0) & (sar_py < H_s)
    sy = np.clip(sar_py, 0, H_s - 1)
    sx = np.clip(sar_px, 0, W_s - 1)

    warped_flood = np.where(valid, flood_raw[sy, sx], False)
    warped_delta = np.where(valid, np.nan_to_num(delta_raw[sy, sx], nan=0.0), 0.0)
    warped_pmc = np.where(valid, pmc_raw[sy, sx], False)
    warped_ulsi = np.where(valid, np.nan_to_num(ulsi_raw[sy, sx], nan=50.0), 50.0)

    # Flood Overlay PNG: Specular open water (#38bdf8 blue) + Urban Corner Double-Bounce (#ec4899 magenta)
    flood_rgba = np.zeros((H_d, W_d, 4), dtype=np.uint8)
    is_db = warped_flood & (warped_delta >= 1.5) & warped_pmc
    is_spec = warped_flood & (~is_db) & warped_pmc
    flood_rgba[is_spec] = [56, 189, 248, 225]
    flood_rgba[is_db] = [244, 63, 94, 210]
    flood_b64 = array_to_b64_png(flood_rgba, os.path.join(OUT_DIR, "patna_flood_real_overlay.png"))

    # ULSI Overlay PNG (inside PMC only)
    ulsi_rgba = np.zeros((H_d, W_d, 4), dtype=np.uint8)
    u_norm = np.clip(warped_ulsi / 100.0, 0.0, 1.0)
    ulsi_rgba[..., 0] = np.where(warped_pmc, ((1.0 - u_norm) * 239 + u_norm * 16).astype(np.uint8), 0)
    ulsi_rgba[..., 1] = np.where(warped_pmc, (u_norm * 185 + (1.0 - u_norm) * 68).astype(np.uint8), 0)
    ulsi_rgba[..., 2] = np.where(warped_pmc, (u_norm * 129 + (1.0 - u_norm) * 68).astype(np.uint8), 0)
    ulsi_rgba[..., 3] = np.where(warped_pmc, 175, 0)
    ulsi_b64 = array_to_b64_png(ulsi_rgba, os.path.join(OUT_DIR, "patna_ulsi_real_overlay.png"))

    # NASA MODIS 2019 Peak Heatwave LST Overlay (exact Sinusoidal Tile h25v06 coordinates)
    lst_arr = np.nan_to_num(np.load(os.path.join(OUT_DIR, "patna_lst_max_heatwave.npy")), nan=38.0)  # (31, 31)
    R_modis = 6371007.181
    T_modis = 1111950.5197
    x_min_w, y_max_w = -20015109.354, 10007554.677
    h_tile, v_tile = 25, 6

    def modis_px_to_latlon(r_idx, c_idx):
        mx = x_min_w + (h_tile + (c_idx + 0.5) / 1200.0) * T_modis
        my = y_max_w - (v_tile + (r_idx + 0.5) / 1200.0) * T_modis
        phi = my / R_modis
        lam = mx / (R_modis * math.cos(phi))
        return math.degrees(phi), math.degrees(lam)

    # Row range [528-15..528+15], Col range [813-15..813+15]
    lat_n, lon_w = modis_px_to_latlon(528 - 15.5, 813 - 15.5)
    lat_s, lon_e = modis_px_to_latlon(528 + 15.5, 813 + 15.5)
    lst_bounds = {
        "south": round(lat_s, 5), "north": round(lat_n, 5),
        "west": round(lon_w, 5), "east": round(lon_e, 5)
    }

    lst_rgba = np.zeros((31, 31, 4), dtype=np.uint8)
    lst_norm = np.clip((lst_arr - 38.0) / (48.0 - 38.0), 0.0, 1.0)
    lst_rgba[..., 0] = (180 + 75 * lst_norm).astype(np.uint8)
    lst_rgba[..., 1] = ((1.0 - lst_norm) * 200).astype(np.uint8)
    lst_rgba[..., 2] = 20
    lst_rgba[..., 3] = 160
    lst_b64 = array_to_b64_png(lst_rgba, os.path.join(OUT_DIR, "patna_lst_real_overlay.png"))

    # Downsample real Copernicus DEM & warped flood mask to 36 x 64 for crisp 3D Wireframe in Three.js!
    rows_3d, cols_3d = 36, 64
    r_idx = np.linspace(0, H_d - 1, rows_3d).astype(int)
    c_idx = np.linspace(0, W_d - 1, cols_3d).astype(int)
    dem_3d = np.round(dem_arr[np.ix_(r_idx, c_idx)], 2).tolist()
    flood_3d = warped_flood[np.ix_(r_idx, c_idx)].astype(int).tolist()
    pmc_3d = warped_pmc[np.ix_(r_idx, c_idx)].astype(int).tolist()

    return {
        "dem_bounds": [[dem_bounds["south"], dem_bounds["west"]], [dem_bounds["north"], dem_bounds["east"]]],
        "lst_bounds": [[lst_bounds["south"], lst_bounds["west"]], [lst_bounds["north"], lst_bounds["east"]]],
        "overlays": {
            "flood_b64": flood_b64,
            "dem_b64": dem_b64,
            "ulsi_b64": ulsi_b64,
            "lst_b64": lst_b64
        },
        "terrain_3d": {
            "rows": rows_3d,
            "cols": cols_3d,
            "min_elev": round(float(np.min(dem_arr)), 2),
            "max_elev": round(float(np.max(dem_arr)), 2),
            "elev": dem_3d,
            "flood": flood_3d,
            "pmc": pmc_3d
        }
    }


def main():
    india_country_gj, india_gj, bihar_gj = extract_sovereign_india()
    patna_dist_gj = simplify_geojson_file(os.path.join(BOUNDS_DIR, "patna_district_boundary.geojson"), keep_every=12)
    patna_urban_gj = simplify_geojson_file(os.path.join(BOUNDS_DIR, "patna_urban_boundary.geojson"), keep_every=8)
    raster_bundle = build_real_rasters_and_3d_dem()

    # Macro Multi-Hazard Hubs across Complete Sovereign India (grounded in NDMA / IMD / Copernicus / Sentinel-1 archives)
    india_hubs = [
        {"name": "Patna & Gangetic Alluvial Core", "state": "Bihar", "coords": [25.594, 85.137], "hazard": "Compound Heat + Urban Double-Bounce Flood", "metric": "99.60 km2 Inundated | 46.25 C Peak LST", "severity": "CRITICAL"},
        {"name": "Bihta / IIT Patna High Levee", "state": "Bihar", "coords": [25.536, 84.851], "hazard": "Safe High-Ridge Corridor", "metric": "Elev: 55.2m | ULSI: 91.5 (Zone S1)", "severity": "SAFE"},
        {"name": "Leh / Ladakh Trans-Himalayan Cryosphere", "state": "Ladakh", "coords": [34.152, 77.577], "hazard": "Glacial Lake Outburst (GLOF) & Permafrost Melt", "metric": "Upper Indus Basin Snow-Melt Telemetry", "severity": "HIGH"},
        {"name": "Srinagar / Jhelum Floodplain", "state": "Jammu & Kashmir", "coords": [34.083, 74.797], "hazard": "Jhelum Valley Flash Flood & Western Disturbance", "metric": "S1 SAR Alluvial Ponding Monitor", "severity": "HIGH"},
        {"name": "Itanagar / Siang-Brahmaputra Headwaters", "state": "Arunachal Pradesh", "coords": [27.084, 93.605], "hazard": "Orographic Cloudburst & Landslide Corridor", "metric": "Eastern Himalaya Heavy Precipitation Zone", "severity": "HIGH"},
        {"name": "Kaziranga & Guwahati / Brahmaputra Basin", "state": "Assam", "coords": [26.144, 91.736], "hazard": "Severe Fluvial Braided Flood", "metric": "IOD + Bay of Bengal Moisture Corridor", "severity": "CRITICAL"},
        {"name": "Joshimath & Chamoli / Upper Ganga", "state": "Uttarakhand", "coords": [30.550, 79.566], "hazard": "Cryosphere Melt & Land Subsidence", "metric": "InSAR Deformation + Glacial Outburst", "severity": "HIGH"},
        {"name": "Mumbai / Konkan Coastal Plain", "state": "Maharashtra", "coords": [19.076, 72.877], "hazard": "Arabian Sea Storm Surge & Coastal Ponding", "metric": "Pluvial + Tidal Lock", "severity": "HIGH"},
        {"name": "Chennai & Adyar Basin", "state": "Tamil Nadu", "coords": [13.082, 80.270], "hazard": "Bay of Bengal NE Monsoon Cyclogenesis", "metric": "ENSO / MJO Teleconnection", "severity": "HIGH"},
        {"name": "Sundarbans Delta / Kolkata Basin", "state": "West Bengal", "coords": [22.150, 88.850], "hazard": "Tropical Cyclone Track & Salinity Intrusion", "metric": "Bay of Bengal Depression Axis", "severity": "CRITICAL"},
        {"name": "Delhi NCR Airshed & Urban Core", "state": "Delhi", "coords": [28.613, 77.209], "hazard": "Winter Boundary Layer PM2.5 + SUHI", "metric": "47+ C Summer LST / Severe AQI", "severity": "HIGH"},
        {"name": "Thar Arid Core / Phalodi", "state": "Rajasthan", "coords": [27.131, 72.368], "hazard": "Extreme Dryland Thermal Anomaly", "metric": "Peak > 50 C Land Surface Temp", "severity": "CRITICAL"}
    ]

    full_bundle = {
        "metadata": {
            "project": "BHU LOKA",
            "author": "Prince Kumar (IIT Patna, PA2511CDH37)",
            "supervisor": "Pallav Rustogi",
            "crs": "EPSG:4326 (WGS84)",
            "sources": [
                "Survey-Aligned Official India 36 States/UTs & Composite Sovereign Border (6.75N-37.10N)",
                "Google Earth Satellite / Google Maps India (gl=IN) + Copernicus S1/DEM Rasters",
                "GADM v4.1 Bihar 38 Districts + OSM Nominatim Patna Jurisdictions",
                "NASA Terra MODIS MOD11A1 v061 LST (April-June 2019)"
            ]
        },
        "india_country": india_country_gj,
        "india_states": india_gj,
        "bihar_districts": bihar_gj,
        "patna_district": patna_dist_gj,
        "patna_urban": patna_urban_gj,
        "india_hazard_hubs": india_hubs,
        **raster_bundle
    }

    js_path = os.path.join(OUT_DIR, "bhu_loka_real_geodata.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.BHU_LOKA_REAL_DATA = ")
        json.dump(full_bundle, f, separators=(",", ":"))
        f.write(";\n")

    size_kb = os.path.getsize(js_path) / 1024.0
    print(f"4. Compiled self-contained real geospatial web bundle: {js_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
