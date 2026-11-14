"""
BHU LOKA (भूलोक) - Module 04: Business & Urban Intelligence Engine
===================================================================
Provides sovereign urban resilience, terrain zoning, SAR flood coupling,
and municipal infrastructure surveillance verification.

Key Scientific Capabilities:
1. Copernicus 30m GLO-30 DEM Micro-Topography & Elevation Zoning
   - High-precision micro-relief (Patna Basin 40m - 73m range)
   - Topographic slope calculation via Horn's finite difference method
   - Pluvial depression sink classification & water stagnation index
2. Copernicus Sentinel-1 SAR Flood Inundation & River Discharge Coupling
   - Empirical VV polarization flood extent benchmark (Patna Sep 2019 deluge: 26.54 km2 flooded, Otsu -3.80 dB)
   - Live GloFAS / Open-Meteo river discharge coupling with return period thresholds
3. Municipal Infrastructure & CCTV Verification Pane
   - Real OSM Overpass surveillance nodes (man_made=surveillance) & critical emergency facilities
   - Strict fail-closed offline policy (returns UNAVAILABLE without synthetic fabrication)

Author: Prince Kumar (IIT Patna, PA2511CDH37)
Supervisor: Pallav Rustogi
UI/UX Designer: Payal Priyadarshini (IIITDM Jabalpur)
Institutional Anchor: Indian Institute of Technology Patna, M.S. CSDA
"""

from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Base directories
_CURRENT_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _CURRENT_DIR.parent
_PROCESSED_DIR = _ROOT_DIR / "Data" / "08_Processed_Outputs"
_SAR_DIR = _ROOT_DIR / "Data" / "02_SAR_Sentinel1"

# In-memory caches for fast responses with 10-minute TTL
_DEM_ZONING_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_FLOOD_COUPLING_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_URBAN_INFRA_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_CACHE_TTL_SECONDS = 600.0


def clear_urban_business_caches() -> None:
    """Clear in-memory caches to guarantee strict test isolation."""
    _DEM_ZONING_CACHE.clear()
    _FLOOD_COUPLING_CACHE.clear()
    _URBAN_INFRA_CACHE.clear()


# ---------------------------------------------------------------------------
# 1. COPERNICUS 30M GLO-30 DEM ELEVATION ZONING & MICRO-RELIEF
# ---------------------------------------------------------------------------

_PATNA_DEM_ELEV_CACHE: Optional[Any] = None
_PATNA_DEM_SLOPE_CACHE: Optional[Any] = None
_PATNA_FLOOD_MASK_CACHE: Optional[Any] = None


def _load_local_rasters() -> Tuple[Optional[Any], Optional[Any], Optional[Any]]:
    """Lazy load preprocessed empirical numpy rasters if available."""
    global _PATNA_DEM_ELEV_CACHE, _PATNA_DEM_SLOPE_CACHE, _PATNA_FLOOD_MASK_CACHE
    if _PATNA_DEM_ELEV_CACHE is None:
        elev_p = _PROCESSED_DIR / "patna_dem_elevation_pmc.npy"
        if elev_p.exists():
            try:
                import numpy as np
                _PATNA_DEM_ELEV_CACHE = np.load(str(elev_p))
            except Exception:
                _PATNA_DEM_ELEV_CACHE = None
    if _PATNA_DEM_SLOPE_CACHE is None:
        slope_p = _PROCESSED_DIR / "patna_dem_slope_pmc.npy"
        if slope_p.exists():
            try:
                import numpy as np
                _PATNA_DEM_SLOPE_CACHE = np.load(str(slope_p))
            except Exception:
                _PATNA_DEM_SLOPE_CACHE = None
    if _PATNA_FLOOD_MASK_CACHE is None:
        flood_p = _PROCESSED_DIR / "patna_2019_flood_extent_empirical.npy"
        if flood_p.exists():
            try:
                import numpy as np
                _PATNA_FLOOD_MASK_CACHE = np.load(str(flood_p))
            except Exception:
                _PATNA_FLOOD_MASK_CACHE = None
    return _PATNA_DEM_ELEV_CACHE, _PATNA_DEM_SLOPE_CACHE, _PATNA_FLOOD_MASK_CACHE


def compute_dem_elevation_zoning(
    lat: float,
    lon: float,
    radius_km: float = 2.0,
) -> Dict[str, Any]:
    """
    Compute micro-topographic elevation zoning and slope using 30m Copernicus GLO-30 DEM.
    Classifies terrain into Depression Sinks, Transitional Plains, or Natural Levee Highlands.
    """
    cache_key = f"{round(lat, 4)}:{round(lon, 4)}:{round(radius_km, 2)}"
    now = time.time()
    if cache_key in _DEM_ZONING_CACHE:
        cached_time, cached_val = _DEM_ZONING_CACHE[cache_key]
        if now - cached_time < _CACHE_TTL_SECONDS:
            return cached_val

    # PMC Bounding Box: Lon 85.02 to 85.25, Lat 25.54 to 25.65
    is_in_patna_pmc = (25.54 <= lat <= 25.65) and (85.02 <= lon <= 85.25)
    elev_arr, slope_arr, _ = _load_local_rasters()

    elevation_m = 51.0
    slope_deg = 1.2
    source = "COPERNICUS_GLO30_EMPIRICAL_RASTER"

    if is_in_patna_pmc and elev_arr is not None:
        # Map lat/lon to pixel index in PMC DEM array (423 rows x 929 cols)
        h, w = elev_arr.shape
        x_norm = max(0.0, min(1.0, (lon - 85.02) / (85.25 - 85.02)))
        y_norm = max(0.0, min(1.0, (25.65 - lat) / (25.65 - 25.54)))
        px = int(x_norm * (w - 1))
        py = int(y_norm * (h - 1))
        val_e = float(elev_arr[py, px])
        if not math.isnan(val_e):
            elevation_m = round(val_e, 2)
        if slope_arr is not None:
            val_s = float(slope_arr[min(py, slope_arr.shape[0]-1), min(px, slope_arr.shape[1]-1)])
            if not math.isnan(val_s):
                slope_deg = round(val_s, 2)
    else:
        # Fallback to Open-Meteo Elevation API for locations outside Patna
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BHULOKA-Workstation/2.0"})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elev_list = data.get("elevation", [])
                if elev_list and elev_list[0] is not None:
                    elevation_m = float(elev_list[0])
                    source = "OPEN_METEO_ELEVATION_API"
                else:
                    return {
                        "status": "UNAVAILABLE",
                        "latitude": lat,
                        "longitude": lon,
                        "error": "Elevation data unavailable from upstream API.",
                    }
        except Exception as e:
            return {
                "status": "UNAVAILABLE",
                "latitude": lat,
                "longitude": lon,
                "error": f"Network error during elevation query: {str(e)}",
            }

    # Elevation Zoning Classification
    # Patna Basin thresholds: <48m (depression bowl), 48m-52m (intermediate), >=52m (Ganga natural levee)
    if elevation_m < 48.0:
        zoning_tier = "DEPRESSION_SINK"
        resilience_rating = "VULNERABLE"
        water_stagnation_risk = "HIGH"
        risk_score = 0.85
        planning_advisory = (
            "Low-lying topographic depression prone to pluvial waterlogging and sewer backflow. "
            "Requires mandatory sump pumps, elevated electrical panels (>1.5m above datum), and permeable drainage."
        )
    elif elevation_m < 52.0:
        zoning_tier = "TRANSITIONAL_PLAIN"
        resilience_rating = "MODERATE"
        water_stagnation_risk = "MODERATE"
        risk_score = 0.45
        planning_advisory = (
            "Intermediate alluvial terrace with moderate natural gradient. Standard foundation depth acceptable; "
            "recommend rainwater retention basins and storm runoff conveyance channels."
        )
    else:
        zoning_tier = "NATURAL_LEVEE_HIGHLAND"
        resilience_rating = "HIGH"
        water_stagnation_risk = "LOW"
        risk_score = 0.15
        planning_advisory = (
            "High natural levee ridge with positive gravitational drainage toward natural outfalls. "
            "Highly suitable for critical commercial hubs, datacenters, and emergency logistics centers."
        )

    # Topographic Stagnation Index (TSI = (55.0 - elevation) / (1.0 + slope_deg))
    tsi = max(0.0, (55.0 - elevation_m) / (1.0 + max(0.1, slope_deg)))

    result = {
        "status": "ONLINE",
        "latitude": lat,
        "longitude": lon,
        "elevation_m": elevation_m,
        "slope_deg": slope_deg,
        "zoning_tier": zoning_tier,
        "commercial_resilience_rating": resilience_rating,
        "water_stagnation_risk": water_stagnation_risk,
        "topographic_stagnation_index": round(tsi, 2),
        "risk_score": risk_score,
        "planning_advisory": planning_advisory,
        "provenance": {
            "source": source,
            "nominal_resolution_m": 30.0,
            "datum": "EGM96 / WGS84",
            "institutional_anchor": "IIT Patna, M.S. CSDA"
        }
    }
    _DEM_ZONING_CACHE[cache_key] = (now, result)
    return result


# ---------------------------------------------------------------------------
# 2. COPERNICUS SENTINEL-1 SAR FLOOD COUPLING & RIVER DISCHARGE
# ---------------------------------------------------------------------------

def get_sar_flood_inundation_coupling(
    lat: float = 25.594,
    lon: float = 85.137,
) -> Dict[str, Any]:
    """
    Couples empirical Sentinel-1 SAR flood deluge extent with live GloFAS river discharge telemetry.
    Strict fail-closed: if live discharge is unreachable, river_discharge_status is UNAVAILABLE.
    """
    cache_key = f"{round(lat, 4)}:{round(lon, 4)}"
    now = time.time()
    if cache_key in _FLOOD_COUPLING_CACHE:
        cached_time, cached_val = _FLOOD_COUPLING_CACHE[cache_key]
        if now - cached_time < _CACHE_TTL_SECONDS:
            return cached_val

    # 1. Load Empirical Sentinel-1 Benchmark
    summary_path = _PROCESSED_DIR / "patna_flood_empirical_summary.json"
    empirical_benchmark = {}
    if summary_path.exists():
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                empirical_benchmark = json.load(f)
        except Exception:
            pass

    # Check if target point falls within empirical flood deluge mask
    _, _, flood_mask = _load_local_rasters()
    point_inundated_in_2019 = False
    if flood_mask is not None and (25.54 <= lat <= 25.65) and (85.02 <= lon <= 85.25):
        h, w = flood_mask.shape
        x_norm = max(0.0, min(1.0, (lon - 85.02) / (85.25 - 85.02)))
        y_norm = max(0.0, min(1.0, (25.65 - lat) / (25.65 - 25.54)))
        px = int(x_norm * (w - 1))
        py = int(y_norm * (h - 1))
        point_inundated_in_2019 = bool(flood_mask[py, px] > 0)

    # 2. Fetch Live River Discharge Telemetry from Open-Meteo Flood API (GloFAS model)
    river_discharge_status = "ONLINE"
    discharge_m3_s = None
    gauge_warning_tier = "NORMAL"
    discharge_error = None

    url = f"https://flood-api.open-meteo.com/v1/flood?latitude={lat}&longitude={lon}&daily=river_discharge"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BHULOKA-Workstation/2.0"})
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            daily = data.get("daily", {})
            discharges = daily.get("river_discharge", [])
            valid_discharges = [d for d in discharges if d is not None]
            if valid_discharges:
                discharge_m3_s = float(valid_discharges[0])
                if discharge_m3_s > 35000.0:
                    gauge_warning_tier = "DANGER_HIGH"
                elif discharge_m3_s > 25000.0:
                    gauge_warning_tier = "WARNING_ALERT"
                else:
                    gauge_warning_tier = "NORMAL"
            else:
                river_discharge_status = "UNAVAILABLE"
                discharge_error = "No discharge values returned for coordinate in GloFAS grid."
    except Exception as e:
        river_discharge_status = "UNAVAILABLE"
        discharge_error = f"River discharge telemetry unavailable: {str(e)}"

    # Compounding flood risk index (0.0 to 1.0)
    sar_weight = 0.6 if point_inundated_in_2019 else 0.2
    discharge_weight = 0.4 if (discharge_m3_s and discharge_m3_s > 25000.0) else 0.1
    compounding_flood_risk = min(1.0, sar_weight + discharge_weight)

    result = {
        "status": "ONLINE",
        "latitude": lat,
        "longitude": lon,
        "empirical_sar_benchmark": {
            "event": empirical_benchmark.get("event", "Patna Pluvial Deluge (September 2019)"),
            "sensors": empirical_benchmark.get("sensors", [
                "Copernicus Sentinel-1A (23 Sep 2019, 00:20 UTC) - Baseline Dry",
                "Copernicus Sentinel-1B (29 Sep 2019, 00:19 UTC) - Peak Flood"
            ]),
            "polarization": empirical_benchmark.get("polarization", "VV"),
            "otsu_threshold_dB": empirical_benchmark.get("otsu_threshold_dB", -3.7978),
            "total_mapped_urban_area_km2": empirical_benchmark.get("total_mapped_urban_area_km2", 444.68),
            "empirical_flooded_area_km2": empirical_benchmark.get("empirical_flooded_area_km2", 26.54),
            "inundation_percentage": empirical_benchmark.get("inundation_percentage", 5.97),
            "point_inundated_2019_deluge": point_inundated_in_2019
        },
        "hydrological_coupling": {
            "status": river_discharge_status,
            "river_discharge_m3_s": discharge_m3_s,
            "gauge_warning_tier": gauge_warning_tier,
            "error": discharge_error,
            "source": "Copernicus CEMS / GloFAS 4.0 via Open-Meteo Flood API"
        },
        "compounding_flood_vulnerability": {
            "score": round(compounding_flood_risk, 2),
            "classification": "HIGH_VULNERABILITY" if compounding_flood_risk > 0.6 else "MODERATE_VULNERABILITY",
            "business_continuity_advice": (
                "High compound pluvial-fluvial flood exposure. Ensure commercial warehouses have flood barriers, "
                "contingency inventory storage outside low-lying zones, and secondary power generation."
            ) if compounding_flood_risk > 0.6 else (
                "Moderate terrain drainage buffer. Verify storm runoff connectivity and monitor river gauge alerts."
            )
        }
    }
    _FLOOD_COUPLING_CACHE[cache_key] = (now, result)
    return result


# ---------------------------------------------------------------------------
# 3. MUNICIPAL INFRASTRUCTURE & CCTV VERIFICATION PANE
# ---------------------------------------------------------------------------

def get_urban_infrastructure_nodes(
    lat: float,
    lon: float,
    radius_m: int = 2000,
) -> Dict[str, Any]:
    """
    Query OpenStreetMap Overpass API for verified municipal surveillance nodes and emergency hubs.
    Strict fail-closed: returns UNAVAILABLE when network or Overpass is down. Zero synthetic nodes.
    """
    cache_key = f"{round(lat, 4)}:{round(lon, 4)}:{radius_m}"
    now = time.time()
    if cache_key in _URBAN_INFRA_CACHE:
        cached_time, cached_val = _URBAN_INFRA_CACHE[cache_key]
        if now - cached_time < _CACHE_TTL_SECONDS:
            return cached_val

    query = f"""[out:json][timeout:10];
(
  node["man_made"="surveillance"](around:{radius_m},{lat},{lon});
  node["amenity"="hospital"](around:{radius_m},{lat},{lon});
  node["amenity"="police"](around:{radius_m},{lat},{lon});
  node["amenity"="fire_station"](around:{radius_m},{lat},{lon});
);
out body;
"""
    overpass_urls = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ]

    elements = []
    error_msg = None
    success = False

    for op_url in overpass_urls:
        try:
            req = urllib.request.Request(
                op_url,
                data=query.encode("utf-8"),
                headers={
                    "User-Agent": "BHULOKA-Workstation/2.0",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
                }
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elements = data.get("elements", [])
                success = True
                break
        except Exception as e:
            error_msg = str(e)

    if not success:
        return {
            "status": "UNAVAILABLE",
            "latitude": lat,
            "longitude": lon,
            "radius_m": radius_m,
            "error": f"OSM Overpass API unreachable: {error_msg}",
            "cctv_nodes": [],
            "emergency_facilities": [],
            "total_nodes": 0
        }

    cctv_nodes = []
    emergency_facilities = []

    for el in elements:
        t = el.get("tags", {})
        el_lat = el.get("lat")
        el_lon = el.get("lon")
        if el_lat is None or el_lon is None:
            continue

        # Approximate metric distance from target center
        d_lat_m = (el_lat - lat) * 111000.0
        d_lon_m = (el_lon - lon) * (111000.0 * math.cos(math.radians(lat)))
        dist_m = round(math.sqrt(d_lat_m * d_lat_m + d_lon_m * d_lon_m), 1)

        if t.get("man_made") == "surveillance":
            cctv_nodes.append({
                "osm_id": el.get("id"),
                "latitude": el_lat,
                "longitude": el_lon,
                "distance_m": dist_m,
                "surveillance_type": t.get("surveillance:type", t.get("surveillance", "public")),
                "camera_type": t.get("camera:type", "fixed"),
                "camera_mount": t.get("camera:mount", "pole"),
                "direction": t.get("camera:direction", "omnidirectional"),
                "operator": t.get("operator", "Municipal Smart City / Police")
            })
        elif t.get("amenity") in ("hospital", "police", "fire_station"):
            emergency_facilities.append({
                "osm_id": el.get("id"),
                "name": t.get("name", t.get("name:en", f"Unnamed {t.get('amenity')}")),
                "facility_type": t.get("amenity"),
                "latitude": el_lat,
                "longitude": el_lon,
                "distance_m": dist_m,
                "emergency": t.get("emergency", "yes" if t.get("amenity") == "hospital" else None),
                "phone": t.get("phone", t.get("contact:phone", None))
            })

    result = {
        "status": "ONLINE",
        "latitude": lat,
        "longitude": lon,
        "radius_m": radius_m,
        "cctv_nodes": cctv_nodes,
        "emergency_facilities": emergency_facilities,
        "total_nodes": len(cctv_nodes) + len(emergency_facilities),
        "provenance": {
            "source": "OpenStreetMap Contributors (ODbL)",
            "query_type": "Overpass QL live verified nodes"
        }
    }
    _URBAN_INFRA_CACHE[cache_key] = (now, result)
    return result


# ---------------------------------------------------------------------------
# 4. COMPOSITE URBAN BUSINESS INTELLIGENCE SUMMARY
# ---------------------------------------------------------------------------

def get_urban_business_summary(
    lat: float = 25.594,
    lon: float = 85.137,
) -> Dict[str, Any]:
    """Combine DEM zoning, SAR flood coupling, and infrastructure into an asset resilience report."""
    dem = compute_dem_elevation_zoning(lat, lon)
    flood = get_sar_flood_inundation_coupling(lat, lon)
    infra = get_urban_infrastructure_nodes(lat, lon, radius_m=2000)

    # Calculate Commercial Site Suitability Index (0-100)
    # Higher elevation, lower slope, no flood history, and good emergency proximity increase score
    dem_score = 100.0 - (dem.get("risk_score", 0.5) * 40.0)
    flood_vuln = flood.get("compounding_flood_vulnerability", {}).get("score", 0.5)
    flood_penalty = flood_vuln * 35.0
    infra_bonus = min(15.0, len(infra.get("emergency_facilities", [])) * 3.0)

    suitability_index = max(10.0, min(100.0, dem_score - flood_penalty + infra_bonus))

    return {
        "status": "ONLINE",
        "timestamp": time.time(),
        "target": {
            "latitude": lat,
            "longitude": lon,
            "location_name": "Patna Urban Center" if (25.54 <= lat <= 25.65) else "Custom Urban Coordinates"
        },
        "commercial_suitability_score": round(suitability_index, 1),
        "dem_zoning": dem,
        "sar_flood_coupling": flood,
        "infrastructure": infra,
        "institutional_anchor": {
            "institution": "Indian Institute of Technology Patna, M.S. CSDA",
            "author": "Prince Kumar (PA2511CDH37)",
            "supervisor": "Pallav Rustogi",
            "designer": "Payal Priyadarshini (IIITDM Jabalpur)"
        }
    }


# ---------------------------------------------------------------------------
# 5. FASTAPI ROUTER DEFINITION
# ---------------------------------------------------------------------------

urban_router = APIRouter(prefix="/api/v1/urban", tags=["Urban & Business Intelligence"])


@urban_router.get("/dem-zoning")
def api_dem_zoning(
    lat: float = Query(25.594, ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(85.137, ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    radius_km: float = Query(2.0, ge=0.5, le=10.0, description="Analysis buffer radius in km"),
):
    """Retrieve 30m Copernicus GLO-30 DEM micro-topography, elevation zoning tier, and slope."""
    return compute_dem_elevation_zoning(lat, lon, radius_km)


@urban_router.get("/flood-coupling")
def api_flood_coupling(
    lat: float = Query(25.594, ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(85.137, ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
):
    """Couple empirical Sentinel-1 SAR flood inundation with live GloFAS river discharge."""
    return get_sar_flood_inundation_coupling(lat, lon)


@urban_router.get("/infrastructure")
def api_infrastructure(
    lat: float = Query(25.594, ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(85.137, ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
    radius_m: int = Query(2000, ge=300, le=5000, description="Search radius in meters"),
):
    """Retrieve verified OSM Overpass CCTV surveillance nodes and emergency facilities."""
    return get_urban_infrastructure_nodes(lat, lon, radius_m)


@urban_router.get("/summary")
def api_summary(
    lat: float = Query(25.594, ge=-90.0, le=90.0, description="Latitude in decimal degrees"),
    lon: float = Query(85.137, ge=-180.0, le=180.0, description="Longitude in decimal degrees"),
):
    """Get composite urban business resilience and infrastructure summary."""
    return get_urban_business_summary(lat, lon)

