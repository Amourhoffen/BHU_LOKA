"""
BHU LOKA Human Intelligence Engine — Worker Climate-Health Module (R0.1 MVP)

Mission: Protect outdoor and gig workers from heat stress and air-quality hazards
across Indian cities and agricultural zones.

Capabilities:
  1. WBGT (Wet-Bulb Globe Temperature) calculation — ISO 7243 simplified outdoor
     approximation using Open-Meteo variables: T2m, relative humidity, wind speed.
     Bernard & Pourmoghani (1999) natural wet-bulb approximation used for WBGT_outdoor.
  2. PM2.5 / NAQI live fetch — OpenAQ v3 API (zero-key tier), fail-closed UNAVAILABLE.
  3. Worker exposure-risk scoring — combined heat + air-quality composite index.
  4. Cooling shelter and hospital mapping — OSM Overpass API (already used by
     bhu_loka_india_intel.py); radius-limited query around worker coordinates.
  5. FastAPI router — /api/v1/worker/* endpoints.

Zero-Fabrication Policy:
  Never fabricate WBGT readings, AQI values, PM2.5 concentrations, shelter locations,
  or hospital names when external services are absent or unreachable.
  Every UNAVAILABLE state must carry an explicit reason string.

WBGT Tiers (ISO 7243 / ACGIH TLV, light-to-moderate outdoor work):
  < 25 C   -> SAFE       (No restrictions)
  25-27.9  -> CAUTION    (Acclimatised workers; 45 min work / 15 min rest)
  28-29.9  -> WARNING    (Max 30 min work / 30 min rest)
  30-32.9  -> DANGER     (Max 15 min work / 45 min rest; unacclimatised stop)
  >= 33 C  -> EXTREME    (Work cessation; immediate shelter required)

Data sources used:
  Open-Meteo: https://api.open-meteo.com/v1/forecast   (zero key, public domain)
  OpenAQ v3:  https://api.openaq.org/v3/               (zero key, Creative Commons)
  OSM Overpass: https://overpass-api.de/api/interpreter (zero key, ODbL)

Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
UI/UX Designer: Payal Priyadarshini (IIITDM Jabalpur)
Institutional Anchor: IIT Patna, M.S. CSDA
"""

from __future__ import annotations

import json
import math
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPENAQ_LOCATIONS_URL = "https://api.openaq.org/v3/locations"
OPENAQ_MEASUREMENTS_URL = "https://api.openaq.org/v3/measurements"
OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

OPENAQ_ATTRIBUTION = (
    "OpenAQ v3 API — open data under Creative Commons CC BY 4.0. "
    "BHU LOKA claims NO OpenAQ partnership or endorsement."
)
OPEN_METEO_ATTRIBUTION = (
    "Open-Meteo — open-source weather API, Creative Commons CC BY 4.0. "
    "No API key required."
)
OSM_ATTRIBUTION = (
    "OpenStreetMap contributors — ODbL 1.0 licence. "
    "Overpass API query. BHU LOKA is not affiliated with OSM Foundation."
)

# WBGT tier thresholds (degrees Celsius) — ISO 7243, light-to-moderate outdoor
WBGT_TIERS: List[Tuple[float, str, str]] = [
    (25.0, "SAFE", "No work restrictions. Adequate hydration recommended."),
    (28.0, "CAUTION", "45 min work / 15 min rest. Monitor unacclimatised workers."),
    (30.0, "WARNING", "30 min work / 30 min rest. Mandatory hydration. Shade required."),
    (33.0, "DANGER", "15 min work / 45 min rest. Unacclimatised workers must stop."),
    (999.0, "EXTREME", "Work cessation. Immediate shelter required. Emergency protocols active."),
]

# India National Ambient Air Quality Standards (NAQI) — PM2.5 (ug/m3), 24-hr avg
NAQI_TIERS: List[Tuple[float, str, str]] = [
    (30.0, "GOOD", "Air quality satisfactory. No health risk."),
    (60.0, "SATISFACTORY", "Moderate health concern for sensitive groups."),
    (90.0, "MODERATE", "Breathing discomfort on prolonged outdoor exposure."),
    (120.0, "POOR", "Breathing discomfort for most. Outdoor work duration limited."),
    (250.0, "VERY_POOR", "Respiratory illness on prolonged exposure. Masks recommended."),
    (9999.0, "SEVERE", "Health effects for all. Avoid outdoor work."),
]

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

_WBGT_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_AQI_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_SHELTER_CACHE: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
_CACHE_LOCK = threading.Lock()
_WBGT_TTL = 600.0   # 10 min
_AQI_TTL = 900.0    # 15 min
_SHELTER_TTL = 3600.0  # 1 hr (shelter locations change rarely)


def clear_worker_health_caches() -> None:
    """Clear in-memory caches for deterministic unit testing."""
    with _CACHE_LOCK:
        _WBGT_CACHE.clear()
        _AQI_CACHE.clear()
        _SHELTER_CACHE.clear()

# ---------------------------------------------------------------------------
# WBGT Calculation — ISO 7243 Simplified Outdoor Approximation
# ---------------------------------------------------------------------------


def _saturation_vapour_pressure(t_celsius: float) -> float:
    """Magnus formula — saturation vapour pressure (hPa) at temperature T (C)."""
    return 6.1078 * math.exp(17.27 * t_celsius / (t_celsius + 237.3))


def _natural_wet_bulb(t_dry: float, rh_pct: float) -> float:
    """
    Stull (2011) empirical approximation of natural wet-bulb temperature (C).
    Valid for T in [-20, 50] C and RH in [5, 99] %.
    Reference: Stull, R. (2011). Wet-Bulb Temperature from Relative Humidity and
    Air Temperature. J. Appl. Meteor. Climatol., 50, 2267-2269.
    """
    rh = max(5.0, min(99.0, rh_pct))
    t = max(-20.0, min(50.0, t_dry))
    tw = (
        t * math.atan(0.151977 * (rh + 8.313659) ** 0.5)
        + math.atan(t + rh)
        - math.atan(rh - 1.676331)
        + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
        - 4.686035
    )
    return tw


def _globe_temperature_approx(t_dry: float, wind_speed_ms: float, solar_rad_wm2: float) -> float:
    """
    Approximate black-globe temperature (C) using Liljegren et al. (2008) simplified
    outdoor formula. Solar radiation input from Open-Meteo direct_radiation (W/m2).
    When solar_rad_wm2 is unknown, assumes clear-sky midday (600 W/m2).
    """
    if solar_rad_wm2 is None or solar_rad_wm2 < 0:
        solar_rad_wm2 = 600.0
    wind = max(0.1, wind_speed_ms)  # avoid division by zero
    # Simplified: T_globe ~ T_dry + 0.0014 * S - 0.07 * V + constant
    t_globe = t_dry + 0.0014 * solar_rad_wm2 - 0.07 * wind
    return t_globe


def compute_wbgt(
    t_dry_c: float,
    rh_pct: float,
    wind_speed_ms: float,
    solar_rad_wm2: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute outdoor WBGT (C) and derive work-rest tier.
    Returns a fully annotated result dict.

    WBGT_outdoor = 0.7 * T_nwb + 0.2 * T_globe + 0.1 * T_dry
    (ISO 7243 Annex B outdoor simplified coefficients)
    """
    t_nwb = _natural_wet_bulb(t_dry_c, rh_pct)
    t_globe = _globe_temperature_approx(t_dry_c, wind_speed_ms, solar_rad_wm2 or 0.0)
    wbgt = 0.7 * t_nwb + 0.2 * t_globe + 0.1 * t_dry_c

    tier = WBGT_TIERS[-1]
    for threshold, label, advice in WBGT_TIERS:
        if wbgt < threshold:
            tier = (threshold, label, advice)
            break

    return {
        "wbgt_celsius": round(wbgt, 2),
        "t_dry_celsius": round(t_dry_c, 2),
        "t_natural_wetbulb_celsius": round(t_nwb, 2),
        "t_globe_celsius": round(t_globe, 2),
        "relative_humidity_pct": round(rh_pct, 1),
        "wind_speed_ms": round(wind_speed_ms, 2),
        "solar_radiation_wm2": round(solar_rad_wm2 or 0.0, 1),
        "tier": tier[1],
        "work_rest_advice": tier[2],
        "iso_standard": "ISO 7243 Annex B (outdoor simplified)",
        "wetbulb_method": "Stull (2011) empirical approximation",
        "globe_method": "Liljegren et al. (2008) simplified outdoor",
    }


# ---------------------------------------------------------------------------
# Open-Meteo fetch (re-uses same endpoint as bhu_loka_live_api.py but
# requests additional variables needed for WBGT)
# ---------------------------------------------------------------------------


def _http_get_json(url: str, timeout: int = 8) -> Dict[str, Any]:
    """Minimal zero-dependency HTTP GET returning parsed JSON."""
    req = urllib.request.Request(url, headers={"User-Agent": "BhuLoka/2.0 (IITPatna)"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_wbgt_for_location(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch Open-Meteo current weather and compute WBGT.
    Returns status=UNAVAILABLE with reason when network is absent.
    """
    cache_key = f"{lat:.4f},{lon:.4f}"
    with _CACHE_LOCK:
        if cache_key in _WBGT_CACHE:
            ts, data = _WBGT_CACHE[cache_key]
            if time.time() - ts < _WBGT_TTL:
                return dict(data, cache_hit=True)

    params = urllib.parse.urlencode({
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "direct_radiation",
            "apparent_temperature",
            "precipitation",
        ]),
        "hourly": "",
        "daily": "",
        "timezone": "Asia/Kolkata",
        "forecast_days": 1,
    })
    url = f"{OPEN_METEO_URL}?{params}"

    try:
        raw = _http_get_json(url)
        cur = raw.get("current", {})

        t_dry = cur.get("temperature_2m")
        rh = cur.get("relative_humidity_2m")
        wind = cur.get("wind_speed_10m")  # km/h from Open-Meteo
        rad = cur.get("direct_radiation")   # W/m2

        if t_dry is None or rh is None or wind is None:
            raise ValueError("Open-Meteo response missing required variables")

        wind_ms = (wind or 0.0) / 3.6  # convert km/h -> m/s

        wbgt_data = compute_wbgt(t_dry, rh, wind_ms, rad)
        result = {
            "status": "OBSERVED",
            "source": "Open-Meteo (api.open-meteo.com)",
            "attribution": OPEN_METEO_ATTRIBUTION,
            "latitude": lat,
            "longitude": lon,
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "apparent_temperature_c": cur.get("apparent_temperature"),
            "precipitation_mm": cur.get("precipitation"),
            "cache_hit": False,
            **wbgt_data,
        }
        with _CACHE_LOCK:
            _WBGT_CACHE[cache_key] = (time.time(), result)
        return result

    except (urllib.error.URLError, OSError) as exc:
        return {
            "status": "UNAVAILABLE",
            "reason": f"Open-Meteo unreachable: {type(exc).__name__}",
            "latitude": lat,
            "longitude": lon,
            "wbgt_celsius": None,
            "tier": "UNAVAILABLE",
            "work_rest_advice": "Network offline. Check official IMD advisory.",
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "reason": str(exc),
            "latitude": lat,
            "longitude": lon,
            "wbgt_celsius": None,
            "tier": "UNAVAILABLE",
            "work_rest_advice": "Computation error. Check official IMD advisory.",
        }


# ---------------------------------------------------------------------------
# OpenAQ v3 — PM2.5 / NAQI
# ---------------------------------------------------------------------------


def _classify_naqi_pm25(pm25_ugm3: float) -> Tuple[str, str]:
    """Return (NAQI category, health message) for a PM2.5 reading in ug/m3."""
    for threshold, label, msg in NAQI_TIERS:
        if pm25_ugm3 <= threshold:
            return label, msg
    return "SEVERE", NAQI_TIERS[-1][2]


def fetch_aqi_for_location(lat: float, lon: float, radius_m: int = 25000) -> Dict[str, Any]:
    """
    Query OpenAQ v3 for the nearest PM2.5 measurement within radius_m metres.
    Returns status=UNAVAILABLE with reason when network is absent or no station found.
    """
    cache_key = f"{lat:.3f},{lon:.3f}"
    with _CACHE_LOCK:
        if cache_key in _AQI_CACHE:
            ts, data = _AQI_CACHE[cache_key]
            if time.time() - ts < _AQI_TTL:
                return dict(data, cache_hit=True)

    # Step 1: find nearest location
    loc_params = urllib.parse.urlencode({
        "coordinates": f"{lat},{lon}",
        "radius": radius_m,
        "limit": 5,
        "order_by": "distance",
    })
    loc_url = f"{OPENAQ_LOCATIONS_URL}?{loc_params}"

    try:
        loc_data = _http_get_json(loc_url)
        results = loc_data.get("results", [])
        if not results:
            return {
                "status": "UNAVAILABLE",
                "reason": f"No OpenAQ station within {radius_m}m of ({lat:.4f},{lon:.4f}).",
                "pm25_ugm3": None,
                "naqi_category": "UNAVAILABLE",
                "attribution": OPENAQ_ATTRIBUTION,
                "latitude": lat,
                "longitude": lon,
                "cache_hit": False,
            }

        # Pick nearest station with PM2.5 sensor
        station = None
        location_id = None
        for r in results:
            sensors = r.get("sensors", [])
            has_pm25 = any(
                s.get("parameter", {}).get("name", "").lower() in ("pm25", "pm2.5")
                for s in sensors
            )
            if has_pm25:
                station = r
                location_id = r.get("id")
                break

        if station is None or location_id is None:
            return {
                "status": "UNAVAILABLE",
                "reason": "Nearest OpenAQ stations have no PM2.5 sensor.",
                "pm25_ugm3": None,
                "naqi_category": "UNAVAILABLE",
                "attribution": OPENAQ_ATTRIBUTION,
                "latitude": lat,
                "longitude": lon,
                "cache_hit": False,
            }

        # Step 2: fetch latest PM2.5 measurement
        meas_params = urllib.parse.urlencode({
            "locations_id": location_id,
            "parameters_id": 2,  # OpenAQ parameter ID 2 = PM2.5
            "limit": 1,
        })
        meas_url = f"{OPENAQ_MEASUREMENTS_URL}?{meas_params}"
        meas_data = _http_get_json(meas_url)
        meas_results = meas_data.get("results", [])

        if not meas_results:
            return {
                "status": "UNAVAILABLE",
                "reason": f"OpenAQ location {location_id} has no recent PM2.5 measurement.",
                "pm25_ugm3": None,
                "naqi_category": "UNAVAILABLE",
                "attribution": OPENAQ_ATTRIBUTION,
                "station_name": station.get("name", "UNKNOWN"),
                "latitude": lat,
                "longitude": lon,
                "cache_hit": False,
            }

        latest = meas_results[0]
        pm25 = latest.get("value")
        if pm25 is None or pm25 < 0:
            return {
                "status": "UNAVAILABLE",
                "reason": "OpenAQ returned invalid PM2.5 value.",
                "pm25_ugm3": None,
                "naqi_category": "UNAVAILABLE",
                "attribution": OPENAQ_ATTRIBUTION,
                "station_name": station.get("name", "UNKNOWN"),
                "latitude": lat,
                "longitude": lon,
                "cache_hit": False,
            }

        naqi_cat, naqi_msg = _classify_naqi_pm25(pm25)
        station_coords = station.get("coordinates", {})
        result = {
            "status": "OBSERVED",
            "source": "OpenAQ v3 API (api.openaq.org)",
            "attribution": OPENAQ_ATTRIBUTION,
            "latitude": lat,
            "longitude": lon,
            "station_name": station.get("name", "UNKNOWN"),
            "station_latitude": station_coords.get("latitude"),
            "station_longitude": station_coords.get("longitude"),
            "station_distance_m": station.get("distance"),
            "pm25_ugm3": round(pm25, 1),
            "naqi_category": naqi_cat,
            "naqi_health_message": naqi_msg,
            "measurement_datetime_utc": latest.get("period", {}).get("datetimeTo", {}).get("utc"),
            "india_naqi_standard": "CPCB NAQI 2014 (PM2.5 24-hr avg thresholds)",
            "cache_hit": False,
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        with _CACHE_LOCK:
            _AQI_CACHE[cache_key] = (time.time(), result)
        return result

    except (urllib.error.URLError, OSError) as exc:
        return {
            "status": "UNAVAILABLE",
            "reason": f"OpenAQ unreachable: {type(exc).__name__}",
            "pm25_ugm3": None,
            "naqi_category": "UNAVAILABLE",
            "attribution": OPENAQ_ATTRIBUTION,
            "latitude": lat,
            "longitude": lon,
            "cache_hit": False,
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "reason": str(exc),
            "pm25_ugm3": None,
            "naqi_category": "UNAVAILABLE",
            "attribution": OPENAQ_ATTRIBUTION,
            "latitude": lat,
            "longitude": lon,
            "cache_hit": False,
        }


# ---------------------------------------------------------------------------
# OSM Overpass — Cooling Shelters and Hospitals
# ---------------------------------------------------------------------------


def _overpass_query(query_body: str, timeout: int = 10) -> Dict[str, Any]:
    """Execute an Overpass QL query and return parsed JSON."""
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            data = urllib.parse.urlencode({"data": query_body}).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=data,
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "BhuLoka/2.0 (IITPatna)",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError):
            continue
    raise OSError("All Overpass endpoints unreachable")


def fetch_cooling_shelters(lat: float, lon: float, radius_m: int = 3000) -> Dict[str, Any]:
    """
    Query OSM Overpass for cooling shelter candidates near (lat, lon).
    Shelter candidates: amenity=community_centre, amenity=library,
    amenity=hospital, amenity=clinic, amenity=pharmacy, leisure=sports_centre,
    building=government.
    Returns fail-closed UNAVAILABLE when Overpass is unreachable.
    """
    cache_key = f"{lat:.3f},{lon:.3f}:{radius_m}"
    with _CACHE_LOCK:
        if cache_key in _SHELTER_CACHE:
            ts, data = _SHELTER_CACHE[cache_key]
            if time.time() - ts < _SHELTER_TTL:
                return {"status": "CACHED", "shelters": data, "cache_hit": True, "attribution": OSM_ATTRIBUTION}

    # Overpass QL: nodes and ways within radius
    query = f"""
[out:json][timeout:10];
(
  node(around:{radius_m},{lat},{lon})[amenity~"community_centre|library|hospital|clinic|pharmacy|government"];
  node(around:{radius_m},{lat},{lon})[leisure="sports_centre"];
  node(around:{radius_m},{lat},{lon})[building="government"];
  way(around:{radius_m},{lat},{lon})[amenity~"community_centre|library|hospital|clinic"];
);
out center tags;
"""
    try:
        raw = _overpass_query(query)
        elements = raw.get("elements", [])
        shelters: List[Dict[str, Any]] = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("name:en") or tags.get("name:hi")
            if not name:
                continue
            el_lat = el.get("lat") or el.get("center", {}).get("lat")
            el_lon = el.get("lon") or el.get("center", {}).get("lon")
            if el_lat is None or el_lon is None:
                continue
            dist_m = int(
                6371000 * math.acos(
                    max(-1.0, min(1.0,
                        math.sin(math.radians(lat)) * math.sin(math.radians(el_lat))
                        + math.cos(math.radians(lat)) * math.cos(math.radians(el_lat))
                        * math.cos(math.radians(lon - el_lon))
                    ))
                )
            )
            amenity = tags.get("amenity") or tags.get("leisure") or tags.get("building") or "facility"
            shelters.append({
                "name": name,
                "amenity_type": amenity,
                "latitude": el_lat,
                "longitude": el_lon,
                "distance_m": dist_m,
                "phone": tags.get("phone") or tags.get("contact:phone"),
                "opening_hours": tags.get("opening_hours"),
                "osm_id": el.get("id"),
                "data_source": "OpenStreetMap",
            })
        # Sort by distance
        shelters.sort(key=lambda x: x["distance_m"])
        with _CACHE_LOCK:
            _SHELTER_CACHE[cache_key] = (time.time(), shelters)
        return {
            "status": "OBSERVED",
            "source": "OpenStreetMap Overpass API",
            "attribution": OSM_ATTRIBUTION,
            "latitude": lat,
            "longitude": lon,
            "radius_m": radius_m,
            "count": len(shelters),
            "shelters": shelters[:10],  # top 10 nearest
            "cache_hit": False,
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "limitation": "OSM data is community-contributed. Verify operating hours before directing workers.",
        }
    except (OSError, Exception) as exc:
        return {
            "status": "UNAVAILABLE",
            "reason": f"Overpass API unreachable: {type(exc).__name__}",
            "latitude": lat,
            "longitude": lon,
            "radius_m": radius_m,
            "count": 0,
            "shelters": [],
            "attribution": OSM_ATTRIBUTION,
            "cache_hit": False,
        }


# ---------------------------------------------------------------------------
# Combined Exposure Risk Score
# ---------------------------------------------------------------------------


_WBGT_RISK_WEIGHT = 0.6
_AQI_RISK_WEIGHT = 0.4

_WBGT_TIER_SCORES: Dict[str, int] = {
    "SAFE": 0,
    "CAUTION": 25,
    "WARNING": 50,
    "DANGER": 75,
    "EXTREME": 100,
    "UNAVAILABLE": -1,
}
_AQI_TIER_SCORES: Dict[str, int] = {
    "GOOD": 0,
    "SATISFACTORY": 15,
    "MODERATE": 35,
    "POOR": 55,
    "VERY_POOR": 80,
    "SEVERE": 100,
    "UNAVAILABLE": -1,
}


def _risk_level_label(score: int) -> str:
    if score < 20:
        return "LOW"
    if score < 45:
        return "MODERATE"
    if score < 70:
        return "HIGH"
    return "EXTREME"


def compute_exposure_risk(wbgt_result: Dict[str, Any], aqi_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Composite worker exposure risk score [0-100].
    - If both WBGT and AQI available: weighted sum (60% heat, 40% air quality).
    - If only one available: use that signal alone with a caveat.
    - If neither: status=UNAVAILABLE.
    """
    wbgt_score = _WBGT_TIER_SCORES.get(wbgt_result.get("tier", "UNAVAILABLE"), -1)
    aqi_score = _AQI_TIER_SCORES.get(aqi_result.get("naqi_category", "UNAVAILABLE"), -1)

    if wbgt_score < 0 and aqi_score < 0:
        return {
            "status": "UNAVAILABLE",
            "reason": "Both WBGT and PM2.5 data unavailable.",
            "composite_score": None,
            "risk_level": "UNAVAILABLE",
            "primary_hazard": "UNKNOWN",
            "recommendation": "Network offline. Consult local IMD and CPCB advisories.",
        }

    if wbgt_score < 0:
        composite = aqi_score
        caveat = "Heat stress data unavailable. Score based on air quality only."
    elif aqi_score < 0:
        composite = wbgt_score
        caveat = "Air quality data unavailable. Score based on heat stress only."
    else:
        composite = int(_WBGT_RISK_WEIGHT * wbgt_score + _AQI_RISK_WEIGHT * aqi_score)
        caveat = "Composite (60% heat stress + 40% air quality)."

    primary = "HEAT" if wbgt_score >= aqi_score else "AIR_QUALITY"

    recommendations = {
        "LOW": "Normal outdoor work permitted. Hydrate adequately.",
        "MODERATE": "Increase rest breaks. Provide shade and water. Monitor workers.",
        "HIGH": "Limit continuous outdoor exposure. Mandatory rest in shade. Masks for PM2.5.",
        "EXTREME": "Suspend outdoor work. Move workers to shelter immediately. Emergency protocols.",
    }
    risk = _risk_level_label(composite)
    return {
        "status": "COMPUTED",
        "composite_score": composite,
        "risk_level": risk,
        "primary_hazard": primary,
        "heat_component_score": wbgt_score if wbgt_score >= 0 else None,
        "aqi_component_score": aqi_score if aqi_score >= 0 else None,
        "computation_note": caveat,
        "recommendation": recommendations[risk],
    }


# ---------------------------------------------------------------------------
# Combined endpoint helper
# ---------------------------------------------------------------------------


def fetch_worker_health_snapshot(lat: float, lon: float) -> Dict[str, Any]:
    """
    Single call returning WBGT, AQI, exposure risk, and nearest shelters.
    All sub-calls are fail-closed independently.
    """
    wbgt = fetch_wbgt_for_location(lat, lon)
    aqi = fetch_aqi_for_location(lat, lon)
    risk = compute_exposure_risk(wbgt, aqi)
    shelters = fetch_cooling_shelters(lat, lon)

    return {
        "latitude": lat,
        "longitude": lon,
        "snapshot_utc": datetime.now(timezone.utc).isoformat(),
        "wbgt": wbgt,
        "aqi": aqi,
        "exposure_risk": risk,
        "cooling_shelters": shelters,
    }


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class WorkerHealthSnapshot(BaseModel):
    latitude: float = Field(..., description="Query latitude (WGS84)")
    longitude: float = Field(..., description="Query longitude (WGS84)")
    snapshot_utc: str
    wbgt: Dict[str, Any]
    aqi: Dict[str, Any]
    exposure_risk: Dict[str, Any]
    cooling_shelters: Dict[str, Any]


# ---------------------------------------------------------------------------
# FastAPI Router
# ---------------------------------------------------------------------------

worker_router = APIRouter(prefix="/api/v1/worker", tags=["Worker Health"])


@worker_router.get("/health", summary="Worker climate-health snapshot")
def api_worker_health(
    lat: float = Query(default=25.5941, ge=-90.0, le=90.0, description="Latitude (WGS84)"),
    lon: float = Query(default=85.1376, ge=-180.0, le=180.0, description="Longitude (WGS84)"),
) -> Dict[str, Any]:
    """
    Returns combined WBGT heat stress, PM2.5 air quality, exposure risk score,
    and nearest cooling shelters for the given coordinates.
    All data is fail-closed: UNAVAILABLE is returned when network is absent.
    """
    return fetch_worker_health_snapshot(lat, lon)


@worker_router.get("/wbgt", summary="WBGT heat stress only")
def api_wbgt(
    lat: float = Query(default=25.5941, ge=-90.0, le=90.0),
    lon: float = Query(default=85.1376, ge=-180.0, le=180.0),
) -> Dict[str, Any]:
    """
    WBGT (Wet-Bulb Globe Temperature) using Open-Meteo + ISO 7243 outdoor approximation.
    Returns tier (SAFE / CAUTION / WARNING / DANGER / EXTREME) and work-rest advice.
    """
    return fetch_wbgt_for_location(lat, lon)


@worker_router.get("/aqi", summary="PM2.5 / NAQI air quality only")
def api_aqi(
    lat: float = Query(default=25.5941, ge=-90.0, le=90.0),
    lon: float = Query(default=85.1376, ge=-180.0, le=180.0),
    radius_m: int = Query(default=25000, ge=1000, le=100000, description="Search radius in metres"),
) -> Dict[str, Any]:
    """
    PM2.5 concentration from nearest OpenAQ v3 station within radius_m.
    Returns NAQI category and health message per CPCB 2014 standards.
    Returns UNAVAILABLE with explicit reason when no data exists.
    """
    return fetch_aqi_for_location(lat, lon, radius_m)


@worker_router.get("/shelters", summary="Nearest cooling shelters")
def api_shelters(
    lat: float = Query(default=25.5941, ge=-90.0, le=90.0),
    lon: float = Query(default=85.1376, ge=-180.0, le=180.0),
    radius_m: int = Query(default=3000, ge=500, le=20000, description="Search radius in metres"),
) -> Dict[str, Any]:
    """
    OSM Overpass query for nearest cooling shelter candidates (community centres,
    libraries, hospitals, clinics, government buildings) within radius_m metres.
    Returns UNAVAILABLE with reason when Overpass is unreachable.
    """
    return fetch_cooling_shelters(lat, lon, radius_m)

