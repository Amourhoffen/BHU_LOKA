"""
BHU LOKA (भूलोक) Architectural & Geospatial Site Studio v3.2
Clean-room open-standard site intelligence engine providing:
  1. WGS84 (EPSG:4326) <-> Metric UTM (EPSG:326xx/327xx) Redfearn projection
  2. Deterministic NOAA Solar Ephemeris, Azimuth/Altitude & Solstice Shadow Vectors
  3. Bröde et al. (COST Action 730 / 2012) UTCI Outdoor Thermal Comfort & Open-Meteo Wind Rose
  4. Live OpenStreetMap Overpass Urban Context (350m-1000m site ring, strict fail-closed offline)
  5. Marching-Squares DEM Contours & W-E / S-N Elevation Transects
  6. True-Scale Local Metric CAD & Print Exporters (DXF AC1015, Layered SVG, Profile SVG, GLB 2.0, OBJ, GeoJSON)

Zero-Fake-Data Policy: Unavailable external APIs strictly return None + status="UNAVAILABLE".
Solar astronomy calculations are deterministic astronomical geometry and clearly labeled as such.
All OSM-derived geometry carries ODbL attribution; elevation exports credit Copernicus GLO-90 DEM.

Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

from __future__ import annotations

import concurrent.futures
import json
import math
import struct
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape

try:
    from utci import rh_to_vp as _pkg_rh_to_vp, utci_approx as _pkg_utci_approx  # type: ignore
except ImportError:
    _pkg_rh_to_vp = None
    _pkg_utci_approx = None

try:
    from bhu_loka_live_api import fetch_location_3d_dem  # type: ignore
except ImportError:
    try:
        from Pipelines.bhu_loka_live_api import fetch_location_3d_dem  # type: ignore
    except ImportError:
        fetch_location_3d_dem = None  # type: ignore


_OVERPASS_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_WEATHER_UTCI_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_STUDIO_CACHE_TTL_SECONDS = 600.0  # 10 min cache


# ---------------------------------------------------------------------------
# 1. WGS84 -> METRIC UTM (REDFEARN / KRUGER) PROJECTION
# ---------------------------------------------------------------------------

def _utm_zone_from_lon_lat(lat: float, lon: float) -> Tuple[int, str, int]:
    """Return (utm_zone, hemisphere 'N'|'S', epsg)."""
    norm_lon = ((lon + 180.0) % 360.0) - 180.0
    zone = int((norm_lon + 180.0) // 6.0) + 1
    zone = max(1, min(60, zone))
    # Standard Norway / Svalbard exceptions
    if 56.0 <= lat < 64.0 and 3.0 <= norm_lon < 12.0:
        zone = 32
    elif 72.0 <= lat < 84.0:
        if 0.0 <= norm_lon < 9.0:
            zone = 31
        elif 9.0 <= norm_lon < 21.0:
            zone = 33
        elif 21.0 <= norm_lon < 33.0:
            zone = 35
        elif 33.0 <= norm_lon < 42.0:
            zone = 37
    hemi = "N" if lat >= 0.0 else "S"
    epsg = (32600 if hemi == "N" else 32700) + zone
    return zone, hemi, epsg


def latlon_to_utm(lat: float, lon: float, force_zone: Optional[int] = None) -> Dict[str, Any]:
    """Convert WGS84 decimal degrees (EPSG:4326) to metric UTM Easting/Northing (meters)."""
    if not (-80.0 <= float(lat) <= 84.0):
        # Clamp polar warning gracefully only at extreme poles for UTM; raise if out of WGS84
        if not (-90.0 <= float(lat) <= 90.0):
            raise ValueError(f"Latitude out of WGS84 range: {lat}")
    if not (-180.0 <= float(lon) <= 180.0):
        raise ValueError(f"Longitude out of WGS84 range: {lon}")

    zone, hemi, epsg = _utm_zone_from_lon_lat(lat, lon)
    if force_zone is not None:
        zone = max(1, min(60, int(force_zone)))
        epsg = (32600 if hemi == "N" else 32700) + zone

    # WGS84 ellipsoid constants
    a = 6378137.0
    f = 1.0 / 298.257223563
    e2 = f * (2.0 - f)
    ep2 = e2 / (1.0 - e2)
    k0 = 0.9996

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lon0_deg = (zone - 1) * 6.0 - 180.0 + 3.0
    lon0_rad = math.radians(lon0_deg)

    sin_phi = math.sin(lat_rad)
    cos_phi = math.cos(lat_rad)
    tan_phi = math.tan(lat_rad)

    n = a / math.sqrt(1.0 - e2 * sin_phi * sin_phi)
    t = tan_phi * tan_phi
    c = ep2 * cos_phi * cos_phi
    A = cos_phi * (lon_rad - lon0_rad)

    # Meridional arc M from equator
    e4 = e2 * e2
    e6 = e4 * e2
    M = a * (
        (1.0 - e2 / 4.0 - 3.0 * e4 / 64.0 - 5.0 * e6 / 256.0) * lat_rad
        - (3.0 * e2 / 8.0 + 3.0 * e4 / 32.0 + 45.0 * e6 / 1024.0) * math.sin(2.0 * lat_rad)
        + (15.0 * e4 / 256.0 + 45.0 * e6 / 1024.0) * math.sin(4.0 * lat_rad)
        - (35.0 * e6 / 3072.0) * math.sin(6.0 * lat_rad)
    )

    easting = 500000.0 + k0 * n * (
        A
        + (1.0 - t + c) * (A ** 3) / 6.0
        + (5.0 - 18.0 * t + t * t + 72.0 * c - 58.0 * ep2) * (A ** 5) / 120.0
    )

    northing = k0 * (
        M
        + n * tan_phi * (
            (A * A) / 2.0
            + (5.0 - t + 9.0 * c + 4.0 * c * c) * (A ** 4) / 24.0
            + (61.0 - 58.0 * t + t * t + 600.0 * c - 330.0 * ep2) * (A ** 6) / 720.0
        )
    )
    if hemi == "S":
        northing += 10000000.0

    convergence_deg = math.degrees(
        math.atan(math.tan(lon_rad - lon0_rad) * sin_phi)
    )
    point_scale_k = k0 * (1.0 + (1.0 + c) * (A * A) / 2.0)

    return {
        "zone": zone,
        "hemisphere": hemi,
        "label": f"{zone}{hemi}",
        "epsg": f"EPSG:{epsg}",
        "central_meridian_deg": lon0_deg,
        "easting_m": round(easting, 2),
        "northing_m": round(northing, 2),
        "convergence_deg": round(convergence_deg, 4),
        "point_scale_k": round(point_scale_k, 6),
    }


def _infer_local_tz_offset_hours(lat: float, lon: float) -> Tuple[float, str]:
    """Return practical local timezone offset in hours and display code."""
    if 6.5 <= lat <= 37.5 and 68.0 <= lon <= 97.5:
        return 5.5, "IST (UTC+05:30)"
    half_hrs = round((lon / 15.0) * 2.0) / 2.0
    sign = "+" if half_hrs >= 0 else "-"
    hh = int(abs(half_hrs))
    mm = int(round((abs(half_hrs) - hh) * 60))
    return half_hrs, f"UTC{sign}{hh:02d}:{mm:02d}"


# ---------------------------------------------------------------------------
# 2. DETERMINISTIC NOAA SOLAR GEOMETRY & SHADOW ANALYSIS
# ---------------------------------------------------------------------------

def _solar_decl_and_eqtime(doy: int, hour_utc: float, year: int = 2026) -> Tuple[float, float]:
    """NOAA low-precision ephemeris: returns (declination_rad, equation_of_time_min)."""
    days_in_year = 366.0 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365.0
    gamma = (2.0 * math.pi / days_in_year) * (doy - 1 + (hour_utc - 12.0) / 24.0)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2.0 * gamma)
        - 0.040849 * math.sin(2.0 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * math.cos(gamma)
        + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2.0 * gamma)
        + 0.000907 * math.sin(2.0 * gamma)
        - 0.002697 * math.cos(3.0 * gamma)
        + 0.001480 * math.sin(3.0 * gamma)
    )
    return decl, eqtime


def solar_position_at(lat: float, lon: float, dt_utc: datetime, height_m: float = 10.0) -> Dict[str, Any]:
    """Compute topocentric sun azimuth (0=N, 90=E, 180=S, 270=W), elevation, and shadow vector."""
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt_utc.astimezone(timezone.utc)

    doy = dt_utc.timetuple().tm_yday
    hour_utc = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    decl, eqtime = _solar_decl_and_eqtime(doy, hour_utc, dt_utc.year)

    tst_min = (hour_utc * 60.0 + eqtime + 4.0 * lon) % 1440.0
    ha_deg = tst_min / 4.0 - 180.0
    ha_rad = math.radians(ha_deg)
    lat_rad = math.radians(lat)

    # Topocentric (East, North, Up) unit sun direction vector -> exact in all hemispheres & at zenith
    sin_lat, cos_lat = math.sin(lat_rad), math.cos(lat_rad)
    sin_decl, cos_decl = math.sin(decl), math.cos(decl)
    sin_ha, cos_ha = math.sin(ha_rad), math.cos(ha_rad)

    vec_e = -cos_decl * sin_ha
    vec_n = cos_lat * sin_decl - sin_lat * cos_decl * cos_ha
    vec_u = max(-1.0, min(1.0, sin_lat * sin_decl + cos_lat * cos_decl * cos_ha))

    elevation_deg = math.degrees(math.asin(vec_u))
    zenith_deg = 90.0 - elevation_deg
    azimuth_deg = (math.degrees(math.atan2(vec_e, vec_n)) + 360.0) % 360.0
    shadow_az_deg = (azimuth_deg + 180.0) % 360.0

    shadow_ratio: Optional[float] = None
    shadow_length_m: Optional[float] = None
    if elevation_deg > 2.0:
        shadow_ratio = round(1.0 / math.tan(math.radians(elevation_deg)), 3)
        shadow_length_m = round(float(height_m) * shadow_ratio, 2)

    return {
        "utc_iso": dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "declination_deg": round(math.degrees(decl), 3),
        "elevation_deg": round(elevation_deg, 2),
        "zenith_deg": round(zenith_deg, 2),
        "azimuth_deg": round(azimuth_deg, 2),
        "shadow_azimuth_deg": round(shadow_az_deg, 2),
        "daytime": elevation_deg > 0.0,
        "shadow_multiplier": shadow_ratio,
        "shadow_length_m": shadow_length_m,
    }


def _sunrise_sunset_for_date(lat: float, lon: float, year: int, month: int, day: int, tz_offset_hrs: float) -> Dict[str, Any]:
    dt_noon_est = datetime(year, month, day, 12, 0, tzinfo=timezone.utc) - timedelta(hours=lon / 15.0)
    doy = dt_noon_est.timetuple().tm_yday
    decl, eqtime = _solar_decl_and_eqtime(doy, dt_noon_est.hour + dt_noon_est.minute / 60.0, year)

    lat_rad = math.radians(lat)
    cos_ha = (math.cos(math.radians(90.833)) / (math.cos(lat_rad) * math.cos(decl) + 1e-12)) - math.tan(lat_rad) * math.tan(decl)
    solar_noon_utc_min = 720.0 - 4.0 * lon - eqtime

    def _fmt_local(mins_utc: float) -> str:
        m_loc = (mins_utc + tz_offset_hrs * 60.0) % 1440.0
        hh = int(m_loc // 60)
        mm = int(round(m_loc % 60)) % 60
        return f"{hh:02d}:{mm:02d}"

    noon_dt_utc = datetime(year, month, day, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=solar_noon_utc_min)
    noon_pos = solar_position_at(lat, lon, noon_dt_utc, height_m=10.0)

    if cos_ha < -1.0:
        return {
            "polar_state": "POLAR_DAY",
            "sunrise_local": "00:00",
            "sunset_local": "24:00",
            "solar_noon_local": _fmt_local(solar_noon_utc_min),
            "daylight_hours": 24.0,
            "noon_elevation_deg": noon_pos["elevation_deg"],
            "noon_azimuth_deg": noon_pos["azimuth_deg"],
        }
    if cos_ha > 1.0:
        return {
            "polar_state": "POLAR_NIGHT",
            "sunrise_local": None,
            "sunset_local": None,
            "solar_noon_local": _fmt_local(solar_noon_utc_min),
            "daylight_hours": 0.0,
            "noon_elevation_deg": noon_pos["elevation_deg"],
            "noon_azimuth_deg": noon_pos["azimuth_deg"],
        }

    ha_deg = math.degrees(math.acos(cos_ha))
    sr_utc_min = solar_noon_utc_min - 4.0 * ha_deg
    ss_utc_min = solar_noon_utc_min + 4.0 * ha_deg
    return {
        "polar_state": "NORMAL",
        "sunrise_local": _fmt_local(sr_utc_min),
        "sunset_local": _fmt_local(ss_utc_min),
        "solar_noon_local": _fmt_local(solar_noon_utc_min),
        "daylight_hours": round((8.0 * ha_deg) / 60.0, 2),
        "noon_elevation_deg": noon_pos["elevation_deg"],
        "noon_azimuth_deg": noon_pos["azimuth_deg"],
    }


def compute_solar_and_shadow_profile(
    lat: float,
    lon: float,
    date_iso: Optional[str] = None,
    building_height_m: float = 10.0,
) -> Dict[str, Any]:
    """Compute hourly 06:00-18:00 local solar trajectory, live position, and seasonal solstice benchmarks."""
    now_utc = datetime.now(timezone.utc)
    tz_hrs, tz_label = _infer_local_tz_offset_hours(lat, lon)

    if date_iso:
        try:
            d_obj = datetime.strptime(date_iso[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            year, month, day = d_obj.year, d_obj.month, d_obj.day
        except ValueError:
            local_now = now_utc + timedelta(hours=tz_hrs)
            year, month, day = local_now.year, local_now.month, local_now.day
    else:
        local_now = now_utc + timedelta(hours=tz_hrs)
        year, month, day = local_now.year, local_now.month, local_now.day

    current_pos = solar_position_at(lat, lon, now_utc, height_m=building_height_m)
    current_local_dt = now_utc + timedelta(hours=tz_hrs)
    current_pos["local_time"] = current_local_dt.strftime("%Y-%m-%d %H:%M")

    hourly_curve: List[Dict[str, Any]] = []
    for hr in range(6, 19):
        local_dt = datetime(year, month, day, hr, 0, tzinfo=timezone.utc)
        utc_dt = local_dt - timedelta(hours=tz_hrs)
        pos = solar_position_at(lat, lon, utc_dt, height_m=building_height_m)
        hourly_curve.append({
            "hour_local": f"{hr:02d}:00",
            "elevation_deg": pos["elevation_deg"],
            "azimuth_deg": pos["azimuth_deg"],
            "shadow_azimuth_deg": pos["shadow_azimuth_deg"],
            "shadow_multiplier": pos["shadow_multiplier"],
            "shadow_length_m": pos["shadow_length_m"],
            "daytime": pos["daytime"],
        })

    day_summary = _sunrise_sunset_for_date(lat, lon, year, month, day, tz_hrs)
    summer_solstice = _sunrise_sunset_for_date(lat, lon, year, 6, 21, tz_hrs)
    equinox = _sunrise_sunset_for_date(lat, lon, year, 3, 21, tz_hrs)
    winter_solstice = _sunrise_sunset_for_date(lat, lon, year, 12, 21, tz_hrs)

    # Clearness / BRE-inspired unobstructed spacing ratio using Dec 21 noon (worst winter sun in N hemisphere; Jun 21 in S)
    critical_solstice = winter_solstice if lat >= 0.0 else summer_solstice
    crit_elev = max(5.0, float(critical_solstice["noon_elevation_deg"]))
    min_spacing_ratio = round(1.0 / math.tan(math.radians(crit_elev)), 2)

    return {
        "status": "COMPUTED_DETERMINISTIC",
        "method": "NOAA Solar Ephemeris (Deterministic Topocentric Geometry)",
        "date": f"{year:04d}-{month:02d}-{day:02d}",
        "timezone_label": tz_label,
        "timezone_offset_hours": tz_hrs,
        "reference_height_m": round(float(building_height_m), 1),
        "current": current_pos,
        "day_summary": day_summary,
        "solstices": {
            "summer_jun21": summer_solstice,
            "equinox_mar21": equinox,
            "winter_dec21": winter_solstice,
        },
        "daylight_spacing_guidance": {
            "critical_noon_elevation_deg": critical_solstice["noon_elevation_deg"],
            "min_h_to_s_spacing_ratio": min_spacing_ratio,
            "recommended_min_setback_for_ref_height_m": round(float(building_height_m) * min_spacing_ratio, 1),
        },
        "hourly_curve": hourly_curve,
    }


# ---------------------------------------------------------------------------
# 3. BRÖDE ET AL. (COST ACTION 730) UTCI & RADIATIVE TMRT ESTIMATION
# ---------------------------------------------------------------------------

def _sat_vapor_pressure_hpa(ta_c: float) -> float:
    """Hardy ITS-90 saturation vapor pressure over liquid water in hPa."""
    g = (
        -2.8365744e3,
        -6.028076559e3,
        1.954263612e1,
        -2.737830188e-2,
        1.6261698e-5,
        7.0229056e-10,
        -1.8680009e-13,
        2.7150305,
    )
    tk = float(ta_c) + 273.15
    es_val = g[7] * math.log(tk)
    for i in range(7):
        es_val += g[i] * (tk ** (i - 2))
    return float(math.exp(es_val) * 0.01)


def _pure_utci_approx(ta: float, eh_pa: float, tmrt: float, va: float) -> float:
    """Pure-Python exact translation of Peter Bröde (2009) UTCI Fortran Version a 0.002."""
    d_tmrt = tmrt - ta
    pa = eh_pa / 10.0  # hPa -> kPa
    t2, t3, t4, t5, t6 = ta * ta, ta ** 3, ta ** 4, ta ** 5, ta ** 6
    v2, v3, v4, v5, v6 = va * va, va ** 3, va ** 4, va ** 5, va ** 6
    d2, d3, d4, d5, d6 = d_tmrt * d_tmrt, d_tmrt ** 3, d_tmrt ** 4, d_tmrt ** 5, d_tmrt ** 6
    p2, p3, p4, p5, p6 = pa * pa, pa ** 3, pa ** 4, pa ** 5, pa ** 6

    return (
        ta
        + 6.07562052e-01 + -2.27712343e-02 * ta + 8.06470249e-04 * t2 + -1.54271372e-04 * t3 + -3.24651735e-06 * t4 + 7.32602852e-08 * t5 + 1.35959073e-09 * t6
        + -2.25836520e+00 * va + 8.80326035e-02 * ta * va + 2.16844454e-03 * t2 * va + -1.53347087e-05 * t3 * va + -5.72983704e-07 * t4 * va + -2.55090145e-09 * t5 * va
        + -7.51269505e-01 * v2 + -4.08350271e-03 * ta * v2 + -5.21670675e-05 * t2 * v2 + 1.94544667e-06 * t3 * v2 + 1.14099531e-08 * t4 * v2
        + 1.58137256e-01 * v3 + -6.57263143e-05 * ta * v3 + 2.22697524e-07 * t2 * v3 + -4.16117031e-08 * t3 * v3
        + -1.27762753e-02 * v4 + 9.66891875e-06 * ta * v4 + 2.52785852e-09 * t2 * v4
        + 4.56306672e-04 * v5 + -1.74202546e-07 * ta * v5 + -5.91491269e-06 * v6
        + 3.98374029e-01 * d_tmrt + 1.83945314e-04 * ta * d_tmrt + -1.73754510e-04 * t2 * d_tmrt + -7.60781159e-07 * t3 * d_tmrt + 3.77830287e-08 * t4 * d_tmrt + 5.43079673e-10 * t5 * d_tmrt
        + -2.00518269e-02 * va * d_tmrt + 8.92859837e-04 * ta * va * d_tmrt + 3.45433048e-06 * t2 * va * d_tmrt + -3.77925774e-07 * t3 * va * d_tmrt + -1.69699377e-09 * t4 * va * d_tmrt
        + 1.69992415e-04 * v2 * d_tmrt + -4.99204314e-05 * ta * v2 * d_tmrt + 2.47417178e-07 * t2 * v2 * d_tmrt + 1.07596466e-08 * t3 * v2 * d_tmrt
        + 8.49242932e-05 * v3 * d_tmrt + 1.35191328e-06 * ta * v3 * d_tmrt + -6.21531254e-09 * t2 * v3 * d_tmrt
        + -4.99410301e-06 * v4 * d_tmrt + -1.89489258e-08 * ta * v4 * d_tmrt + 8.15300114e-08 * v5 * d_tmrt
        + 7.55043090e-04 * d2 + -5.65095215e-05 * ta * d2 + -4.52166564e-07 * t2 * d2 + 2.46688878e-08 * t3 * d2 + 2.42674348e-10 * t4 * d2
        + 1.54547250e-04 * va * d2 + 5.24110970e-06 * ta * va * d2 + -8.75874982e-08 * t2 * va * d2 + -1.50743064e-09 * t3 * va * d2
        + -1.56236307e-05 * v2 * d2 + -1.33895614e-07 * ta * v2 * d2 + 2.49709824e-09 * t2 * v2 * d2
        + 6.51711721e-07 * v3 * d2 + 1.94960053e-09 * ta * v3 * d2 + -1.00361113e-08 * v4 * d2
        + -1.21206673e-05 * d3 + -2.18203660e-07 * ta * d3 + 7.51269482e-09 * t2 * d3 + 9.79063848e-11 * t3 * d3
        + 1.25006734e-06 * va * d3 + -1.81584736e-09 * ta * va * d3 + -3.52197671e-10 * t2 * va * d3
        + -3.36514630e-08 * v2 * d3 + 1.35908359e-10 * ta * v2 * d3 + 4.17032620e-10 * v3 * d3
        + -1.30369025e-09 * d4 + 4.13908461e-10 * ta * d4 + 9.22652254e-12 * t2 * d4
        + -5.08220384e-09 * va * d4 + -2.24730961e-11 * ta * va * d4 + 1.17139133e-10 * v2 * d4
        + 6.62154879e-10 * d5 + 4.03863260e-13 * ta * d5 + 1.95087203e-12 * va * d5 + -4.73602469e-12 * d6
        + 5.12733497e+00 * pa + -3.12788561e-01 * ta * pa + -1.96701861e-02 * t2 * pa + 9.99690870e-04 * t3 * pa + 9.51738512e-06 * t4 * pa + -4.66426341e-07 * t5 * pa
        + 5.48050612e-01 * va * pa + -3.30552823e-03 * ta * va * pa + -1.64119440e-03 * t2 * va * pa + -5.16670694e-06 * t3 * va * pa + 9.52692432e-07 * t4 * va * pa
        + -4.29223622e-02 * v2 * pa + 5.00845667e-03 * ta * v2 * pa + 1.00601257e-06 * t2 * v2 * pa + -1.81748644e-06 * t3 * v2 * pa
        + -1.25813502e-03 * v3 * pa + -1.79330391e-04 * ta * v3 * pa + 2.34994441e-06 * t2 * v3 * pa
        + 1.29735808e-04 * v4 * pa + 1.29064870e-06 * ta * v4 * pa + -2.28558686e-06 * v5 * pa
        + -3.69476348e-02 * d_tmrt * pa + 1.62325322e-03 * ta * d_tmrt * pa + -3.14279680e-05 * t2 * d_tmrt * pa + 2.59835559e-06 * t3 * d_tmrt * pa + -4.77136523e-08 * t4 * d_tmrt * pa
        + 8.64203390e-03 * va * d_tmrt * pa + -6.87405181e-04 * ta * va * d_tmrt * pa + -9.13863872e-06 * t2 * va * d_tmrt * pa + 5.15916806e-07 * t3 * va * d_tmrt * pa
        + -3.59217476e-05 * v2 * d_tmrt * pa + 3.28696511e-05 * ta * v2 * d_tmrt * pa + -7.10542454e-07 * t2 * v2 * d_tmrt * pa
        + -1.24382300e-05 * v3 * d_tmrt * pa + -7.38584400e-09 * ta * v3 * d_tmrt * pa + 2.20609296e-07 * v4 * d_tmrt * pa
        + -7.32469180e-04 * d2 * pa + -1.87381964e-05 * ta * d2 * pa + 4.80925239e-06 * t2 * d2 * pa + -8.75492040e-08 * t3 * d2 * pa
        + 2.77862930e-05 * va * d2 * pa + -5.06004592e-06 * ta * va * d2 * pa + 1.14325367e-07 * t2 * va * d2 * pa
        + 2.53016723e-06 * v2 * d2 * pa + -1.72857035e-08 * ta * v2 * d2 * pa + -3.95079398e-08 * v3 * d2 * pa
        + -3.59413173e-07 * d3 * pa + 7.04388046e-07 * ta * d3 * pa + -1.89309167e-08 * t2 * d3 * pa
        + -4.79768731e-07 * va * d3 * pa + 7.96079978e-09 * ta * va * d3 * pa + 1.62897058e-09 * v2 * d3 * pa
        + 3.94367674e-08 * d4 * pa + -1.18566247e-09 * ta * d4 * pa + 3.34678041e-10 * va * d4 * pa + -1.15606447e-10 * d5 * pa
        + -2.80626406e+00 * p2 + 5.48712484e-01 * ta * p2 + -3.99428410e-03 * t2 * p2 + -9.54009191e-04 * t3 * p2 + 1.93090978e-05 * t4 * p2
        + -3.08806365e-01 * va * p2 + 1.16952364e-02 * ta * va * p2 + 4.95271903e-04 * t2 * va * p2 + -1.90710882e-05 * t3 * va * p2
        + 2.10787756e-03 * v2 * p2 + -6.98445738e-04 * ta * v2 * p2 + 2.30109073e-05 * t2 * v2 * p2
        + 4.17856590e-04 * v3 * p2 + -1.27043871e-05 * ta * v3 * p2 + -3.04620472e-06 * v4 * p2
        + 5.14507424e-02 * d_tmrt * p2 + -4.32510997e-03 * ta * d_tmrt * p2 + 8.99281156e-05 * t2 * d_tmrt * p2 + -7.14663943e-07 * t3 * d_tmrt * p2
        + -2.66016305e-04 * va * d_tmrt * p2 + 2.63789586e-04 * ta * va * d_tmrt * p2 + -7.01199003e-06 * t2 * va * d_tmrt * p2
        + -1.06823306e-04 * v2 * d_tmrt * p2 + 3.61341136e-06 * ta * v2 * d_tmrt * p2 + 2.29748967e-07 * v3 * d_tmrt * p2
        + 3.04788893e-04 * d2 * p2 + -6.42070836e-05 * ta * d2 * p2 + 1.16257971e-06 * t2 * d2 * p2
        + 7.68023384e-06 * va * d2 * p2 + -5.47446896e-07 * ta * va * d2 * p2 + -3.59937910e-08 * v2 * d2 * p2
        + -4.36497725e-06 * d3 * p2 + 1.68737969e-07 * ta * d3 * p2 + 2.67489271e-08 * va * d3 * p2 + 3.23926897e-09 * d4 * p2
        + -3.53874123e-02 * p3 + -2.21201190e-01 * ta * p3 + 1.55126038e-02 * t2 * p3 + -2.63917279e-04 * t3 * p3
        + 4.53433455e-02 * va * p3 + -4.32943862e-03 * ta * va * p3 + 1.45389826e-04 * t2 * va * p3
        + 2.17508610e-04 * v2 * p3 + -6.66724702e-05 * ta * v2 * p3 + 3.33217140e-05 * v3 * p3
        + -2.26921615e-03 * d_tmrt * p3 + 3.80261982e-04 * ta * d_tmrt * p3 + -5.45314314e-09 * t2 * d_tmrt * p3
        + -7.96355448e-04 * va * d_tmrt * p3 + 2.53458034e-05 * ta * va * d_tmrt * p3 + -6.31223658e-06 * v2 * d_tmrt * p3
        + 3.02122035e-04 * d2 * p3 + -4.77403547e-06 * ta * d2 * p3 + 1.73825715e-06 * va * d2 * p3 + -4.09087898e-07 * d3 * p3
        + 6.14155345e-01 * p4 + -6.16755931e-02 * ta * p4 + 1.33374846e-03 * t2 * p4
        + 3.55375387e-03 * va * p4 + -5.13027851e-04 * ta * va * p4 + 1.02449757e-04 * v2 * p4
        + -1.48526421e-03 * d_tmrt * p4 + -4.11469183e-05 * ta * d_tmrt * p4 + -6.80434415e-06 * va * d_tmrt * p4 + -9.77675906e-06 * d2 * p4
        + 8.82773108e-02 * p5 + -3.01859306e-03 * ta * p5 + 1.04452989e-03 * va * p5 + 2.47090539e-04 * d_tmrt * p5
        + 1.48348065e-03 * p6
    )


def utci_stress_category(utci_c: float) -> str:
    """Official COST Action 730 / Bröde et al. (2012) UTCI thermal stress scale."""
    if utci_c > 46.0:
        return "Extreme Heat Stress (>46°C)"
    if utci_c > 38.0:
        return "Very Strong Heat Stress (38-46°C)"
    if utci_c > 32.0:
        return "Strong Heat Stress (32-38°C)"
    if utci_c > 26.0:
        return "Moderate Heat Stress (26-32°C)"
    if utci_c >= 9.0:
        return "No Thermal Stress (Comfort 9-26°C)"
    if utci_c >= 0.0:
        return "Slight Cold Stress (0-9°C)"
    if utci_c >= -13.0:
        return "Moderate Cold Stress (-13-0°C)"
    if utci_c >= -27.0:
        return "Strong Cold Stress (-27 to -13°C)"
    if utci_c >= -40.0:
        return "Very Strong Cold Stress (-40 to -27°C)"
    return "Extreme Cold Stress (<-40°C)"


def estimate_tmrt_from_radiation(
    air_temp_c: float,
    ghi_wm2: float = 0.0,
    dni_wm2: float = 0.0,
    diffuse_wm2: float = 0.0,
    solar_elev_deg: float = 0.0,
    shaded: bool = False,
) -> float:
    """
    Estimate cylindrical standing-human Mean Radiant Temperature (Tmrt) per VDI 3787 / Fanger 1970.
    Uses shortwave absorptivity a_k=0.70, emissivity e_p=0.97, surface albedo=0.22.
    """
    tk = float(air_temp_c) + 273.15
    sigma = 5.670374419e-8
    a_k = 0.70
    e_p = 0.97
    albedo = 0.22

    # Sky & ground longwave estimate (Swinbank clear-sky modulated gently for daytime/diffuse balance)
    e_sky = min(0.95, max(0.74, 0.000009365 * tk * tk + (0.04 if diffuse_wm2 > 60 else 0.0)))
    l_down = e_sky * sigma * (tk ** 4)
    delta_tg = 0.0 if shaded else min(14.0, 0.012 * max(0.0, ghi_wm2))
    l_up = 0.95 * sigma * ((tk + delta_tg) ** 4)

    f_p = 0.0
    eff_dni = 0.0
    if not shaded and solar_elev_deg > 1.0 and dni_wm2 > 0.0:
        alpha_rad = math.radians(max(0.0, min(90.0, solar_elev_deg)))
        f_p = 0.308 * math.cos(alpha_rad * (0.998 - (solar_elev_deg * solar_elev_deg) / 50000.0))
        eff_dni = dni_wm2

    sw_term = a_k * (
        f_p * eff_dni
        + 0.5 * max(0.0, diffuse_wm2)
        + 0.5 * albedo * max(0.0, ghi_wm2)
    )
    lw_term = e_p * (0.5 * l_down + 0.5 * l_up)
    s_str = max(50.0, sw_term + lw_term)
    tmrt_k = (s_str / (e_p * sigma)) ** 0.25
    return round(tmrt_k - 273.15, 2)


def compute_utci_value(
    air_temp_c: float,
    rh_pct: float,
    tmrt_c: float,
    wind_10m_ms: float,
) -> Dict[str, Any]:
    """Compute Bröde et al. (2012) UTCI with COST Action 730 valid wind clamping [0.5, 17.0] m/s."""
    ta = max(-50.0, min(50.0, float(air_temp_c)))
    rh = max(1.0, min(100.0, float(rh_pct)))
    raw_va = float(wind_10m_ms)
    va = max(0.5, min(17.0, raw_va))
    # Clamp delta Tmrt inside regression envelope [-30, +70] C
    tmrt = max(ta - 30.0, min(ta + 70.0, float(tmrt_c)))

    vp_hpa = _pkg_rh_to_vp(ta, rh) if _pkg_rh_to_vp is not None else (_sat_vapor_pressure_hpa(ta) * rh / 100.0)
    vp_hpa = min(50.0, max(0.0, float(vp_hpa)))
    if _pkg_utci_approx is not None:
        val = float(_pkg_utci_approx(ta, vp_hpa, tmrt, va))
    else:
        val = float(_pure_utci_approx(ta, vp_hpa, tmrt, va))

    return {
        "utci_c": round(val, 2),
        "stress_category": utci_stress_category(val),
        "vapor_pressure_hpa": round(vp_hpa, 2),
        "tmrt_c": round(tmrt, 2),
        "wind_10m_ms_raw": round(raw_va, 2),
        "wind_10m_ms_effective": round(va, 2),
        "wind_clamped_to_domain": abs(raw_va - va) > 1e-3,
    }


def _http_get_json(url: str, timeout: float = 4.5) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "BhuLoka-SiteStudio/3.2 (IIT Patna Geospatial Research)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass
    return None


def _build_wind_rose_8dir(speeds_kmh: List[Any], dirs_deg: List[Any]) -> Dict[str, Any]:
    sectors = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    buckets: List[List[float]] = [[] for _ in range(8)]
    for spd_raw, dir_raw in zip(speeds_kmh, dirs_deg):
        if not isinstance(spd_raw, (int, float)) or not isinstance(dir_raw, (int, float)):
            continue
        idx = int(((float(dir_raw) + 22.5) % 360.0) // 45.0) % 8
        buckets[idx].append(float(spd_raw) / 3.6)

    total = sum(len(b) for b in buckets)
    if total == 0:
        return {"status": "UNAVAILABLE", "samples": 0, "dominant_sector": None, "sectors": []}

    sector_rows: List[Dict[str, Any]] = []
    dom_idx = 0
    for i, lbl in enumerate(sectors):
        vals = buckets[i]
        cnt = len(vals)
        pct = round(100.0 * cnt / total, 1)
        mean_ms = round(sum(vals) / cnt, 2) if cnt else 0.0
        max_ms = round(max(vals), 2) if cnt else 0.0
        if cnt > len(buckets[dom_idx]):
            dom_idx = i
        sector_rows.append({
            "direction": lbl,
            "bearing_deg": i * 45,
            "count": cnt,
            "frequency_pct": pct,
            "mean_speed_ms": mean_ms,
            "max_speed_ms": max_ms,
        })

    return {
        "status": "LIVE",
        "samples": total,
        "dominant_sector": sectors[dom_idx],
        "dominant_pct": sector_rows[dom_idx]["frequency_pct"],
        "sectors": sector_rows,
    }


def fetch_solar_wind_utci_assessment(
    lat: float,
    lon: float,
    solar_profile: Optional[Dict[str, Any]] = None,
    timeout: float = 4.5,
    bypass_cache: bool = False,
) -> Dict[str, Any]:
    """Fetch Open-Meteo radiation & wind telemetry and compute current + 24h peak UTCI & 8-dir Wind Rose."""
    cache_key = f"utci:{lat:.3f},{lon:.3f}"
    now_ts = time.time()
    hit = None if bypass_cache else _WEATHER_UTCI_CACHE.get(cache_key)
    if hit and (now_ts - hit[0]) < _STUDIO_CACHE_TTL_SECONDS:
        out = dict(hit[1])
        out["cached"] = True
        return out

    if solar_profile is None:
        solar_profile = compute_solar_and_shadow_profile(lat, lon)

    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat:.5f}&longitude={lon:.5f}"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,"
        "shortwave_radiation,direct_radiation,direct_normal_irradiance,diffuse_radiation"
        "&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,"
        "shortwave_radiation,direct_normal_irradiance,diffuse_radiation"
        "&timezone=auto&forecast_days=3"
    )
    data = _http_get_json(url, timeout=timeout)
    if not data or "current" not in data:
        return {
            "status": "UNAVAILABLE",
            "source": "Open-Meteo ECMWF/DWD Solar & Wind + Bröde UTCI",
            "cached": False,
            "utci_sunlit_c": None,
            "utci_shaded_c": None,
            "stress_category": "UNAVAILABLE",
            "wind_rose": {"status": "UNAVAILABLE", "samples": 0, "dominant_sector": None, "sectors": []},
            "limitations": "Weather/radiation API unreachable; no synthetic comfort telemetry fabricated.",
        }

    cur = data["current"]
    ta = cur.get("temperature_2m")
    rh = cur.get("relative_humidity_2m")
    wind_kmh = cur.get("wind_speed_10m")
    wind_dir = cur.get("wind_direction_10m")
    ghi = cur.get("shortwave_radiation") or 0.0
    dni = cur.get("direct_normal_irradiance") or 0.0
    diff = cur.get("diffuse_radiation") or 0.0

    if not isinstance(ta, (int, float)) or not isinstance(rh, (int, float)) or not isinstance(wind_kmh, (int, float)):
        return {
            "status": "UNAVAILABLE",
            "source": "Open-Meteo ECMWF/DWD Solar & Wind + Bröde UTCI",
            "cached": False,
            "utci_sunlit_c": None,
            "utci_shaded_c": None,
            "stress_category": "UNAVAILABLE",
            "wind_rose": {"status": "UNAVAILABLE", "samples": 0, "dominant_sector": None, "sectors": []},
            "limitations": "Incomplete meteorological parameters returned by Open-Meteo.",
        }

    va_ms = float(wind_kmh) / 3.6
    elev_deg = float((solar_profile.get("current") or {}).get("elevation_deg") or 0.0)
    tmrt_sun = estimate_tmrt_from_radiation(float(ta), float(ghi), float(dni), float(diff), elev_deg, shaded=False)
    tmrt_shade = estimate_tmrt_from_radiation(float(ta), float(ghi), 0.0, float(diff), elev_deg, shaded=True)

    res_sun = compute_utci_value(float(ta), float(rh), tmrt_sun, va_ms)
    res_shade = compute_utci_value(float(ta), float(rh), tmrt_shade, va_ms)

    hourly = data.get("hourly") or {}
    h_temps = hourly.get("temperature_2m") or []
    h_rhs = hourly.get("relative_humidity_2m") or []
    h_wspd = hourly.get("wind_speed_10m") or []
    h_wdir = hourly.get("wind_direction_10m") or []
    h_ghi = hourly.get("shortwave_radiation") or []
    h_dni = hourly.get("direct_normal_irradiance") or []
    h_diff = hourly.get("diffuse_radiation") or []

    wind_rose = _build_wind_rose_8dir(h_wspd[:72], h_wdir[:72])

    # Next-24h peak UTCI scan
    peak_24h_utci: Optional[float] = None
    min_24h_utci: Optional[float] = None
    curve = solar_profile.get("hourly_curve") or []
    noon_elev = float((solar_profile.get("day_summary") or {}).get("noon_elevation_deg") or 45.0)
    for idx in range(min(24, len(h_temps), len(h_rhs), len(h_wspd))):
        ht = h_temps[idx]
        hrh = h_rhs[idx]
        hw = h_wspd[idx]
        if not all(isinstance(v, (int, float)) for v in (ht, hrh, hw)):
            continue
        hghi = float(h_ghi[idx]) if idx < len(h_ghi) and isinstance(h_ghi[idx], (int, float)) else 0.0
        hdni = float(h_dni[idx]) if idx < len(h_dni) and isinstance(h_dni[idx], (int, float)) else 0.0
        hdiff = float(h_diff[idx]) if idx < len(h_diff) and isinstance(h_diff[idx], (int, float)) else 0.0
        approx_elev = max(12.0, noon_elev * 0.75) if hghi > 150.0 else 0.0
        tm_h = estimate_tmrt_from_radiation(float(ht), hghi, hdni, hdiff, approx_elev, shaded=False)
        u_h = compute_utci_value(float(ht), float(hrh), tm_h, float(hw) / 3.6)["utci_c"]
        peak_24h_utci = u_h if peak_24h_utci is None else max(peak_24h_utci, u_h)
        min_24h_utci = u_h if min_24h_utci is None else min(min_24h_utci, u_h)

    payload: Dict[str, Any] = {
        "status": "LIVE",
        "cached": False,
        "source": "Open-Meteo Radiation/Wind + Bröde et al. (2012) UTCI + VDI 3787 Tmrt",
        "observation_time": cur.get("time"),
        "air_temp_c": round(float(ta), 1),
        "relative_humidity_pct": round(float(rh), 1),
        "wind_speed_10m_ms": round(va_ms, 2),
        "wind_direction_deg": wind_dir,
        "shortwave_radiation_wm2": round(float(ghi), 1),
        "direct_normal_irradiance_wm2": round(float(dni), 1),
        "diffuse_radiation_wm2": round(float(diff), 1),
        "utci_sunlit_c": res_sun["utci_c"],
        "utci_shaded_c": res_shade["utci_c"],
        "shade_benefit_c": round(res_sun["utci_c"] - res_shade["utci_c"], 2),
        "stress_category": res_sun["stress_category"],
        "tmrt_sunlit_c": res_sun["tmrt_c"],
        "tmrt_shaded_c": res_shade["tmrt_c"],
        "peak_24h_utci_c": peak_24h_utci,
        "min_24h_utci_c": min_24h_utci,
        "wind_rose": wind_rose,
        "tmrt_limitations": "Tmrt analytically estimated via VDI 3787 / Fanger standing cylinder projection from Open-Meteo shortwave irradiance.",
    }
    _WEATHER_UTCI_CACHE[cache_key] = (now_ts, payload)
    return payload


# ---------------------------------------------------------------------------
# 4. LIVE OPENSTREETMAP OVERPASS SITE CONTEXT (350m - 1000m RING)
# ---------------------------------------------------------------------------

def _polygon_area_local_m2(coords_lonlat: List[Tuple[float, float]], lat0: float, lon0: float) -> float:
    if len(coords_lonlat) < 3:
        return 0.0
    m_per_deg_lat = 111132.92
    m_per_deg_lon = 111412.84 * math.cos(math.radians(lat0))
    pts = [((lon - lon0) * m_per_deg_lon, (lat - lat0) * m_per_deg_lat) for lon, lat in coords_lonlat]
    area = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def _polyline_length_m(coords_lonlat: List[Tuple[float, float]], lat0: float, lon0: float) -> float:
    if len(coords_lonlat) < 2:
        return 0.0
    m_per_deg_lat = 111132.92
    m_per_deg_lon = 111412.84 * math.cos(math.radians(lat0))
    tot = 0.0
    for i in range(1, len(coords_lonlat)):
        dx = (coords_lonlat[i][0] - coords_lonlat[i - 1][0]) * m_per_deg_lon
        dy = (coords_lonlat[i][1] - coords_lonlat[i - 1][1]) * m_per_deg_lat
        tot += math.hypot(dx, dy)
    return tot


def _parse_building_height(tags: Dict[str, Any]) -> Tuple[float, str]:
    raw_h = tags.get("height")
    if isinstance(raw_h, (int, float)):
        val = float(raw_h)
        if 1.5 <= val <= 900.0:
            return round(val, 1), "osm_height_tag"
    elif isinstance(raw_h, str):
        cleaned = raw_h.lower().replace("meters", "").replace("m", "").strip()
        try:
            val = float(cleaned)
            if 1.5 <= val <= 900.0:
                return round(val, 1), "osm_height_tag"
        except ValueError:
            pass

    raw_lvl = tags.get("building:levels")
    if raw_lvl is not None:
        try:
            lvls = float(str(raw_lvl).strip())
            if 0.5 <= lvls <= 200.0:
                return round(lvls * 3.2, 1), "estimated_from_osm_levels"
        except ValueError:
            pass

    return 6.4, "default_lowrise_fallback"


def _http_post_form_json(url: str, form_data: Dict[str, str], timeout: float = 6.0) -> Dict[str, Any]:
    body = urllib.parse.urlencode(form_data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "User-Agent": "BhuLoka-SiteStudio/3.2 (IIT Patna Geospatial Workbench)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")
        return json.loads(resp.read().decode("utf-8"))


def fetch_osm_site_context(
    lat: float,
    lon: float,
    radius_m: float = 350.0,
    timeout: float = 6.0,
    bypass_cache: bool = False,
) -> Dict[str, Any]:
    """
    Query live OpenStreetMap Overpass API for building footprints, roads, green/water polygons & amenities.
    Strictly returns status="UNAVAILABLE" with zero fabricated geometries if offline/rate-limited.
    """
    r_m = max(100.0, min(1000.0, float(radius_m)))
    cache_key = f"osm:{lat:.4f},{lon:.4f},{int(round(r_m))}"
    now_ts = time.time()
    hit = None if bypass_cache else _OVERPASS_CACHE.get(cache_key)
    if hit and (now_ts - hit[0]) < _STUDIO_CACHE_TTL_SECONDS:
        out = dict(hit[1])
        out["cached"] = True
        return out

    ql = (
        f"[out:json][timeout:6];"
        f"("
        f"way[\"building\"](around:{int(r_m)},{lat:.5f},{lon:.5f});"
        f"way[\"highway\"](around:{int(r_m)},{lat:.5f},{lon:.5f});"
        f"way[\"natural\"=\"water\"](around:{int(r_m)},{lat:.5f},{lon:.5f});"
        f"way[\"waterway\"](around:{int(r_m)},{lat:.5f},{lon:.5f});"
        f"way[\"leisure\"=\"park\"](around:{int(r_m)},{lat:.5f},{lon:.5f});"
        f"way[\"landuse\"~\"forest|grass|meadow\"](around:{int(r_m)},{lat:.5f},{lon:.5f});"
        f"node[\"amenity\"~\"hospital|clinic|school|college|university|police|fire_station\"](around:{int(r_m)},{lat:.5f},{lon:.5f});"
        f");"
        f"out geom;"
    )

    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]
    raw_json: Optional[Dict[str, Any]] = None
    last_err = "Overpass API unreachable"

    for ep in endpoints:
        try:
            raw_json = _http_post_form_json(ep, {"data": ql}, timeout=timeout)
            break
        except Exception as exc:
            last_err = str(exc)

    if not raw_json or not isinstance(raw_json.get("elements"), list):
        return {
            "status": "UNAVAILABLE",
            "cached": False,
            "attribution": "© OpenStreetMap contributors (ODbL)",
            "radius_m": round(r_m, 1),
            "error": last_err,
            "building_count": 0,
            "building_footprint_total_m2": None,
            "site_coverage_pct": None,
            "roads_count": 0,
            "road_length_km": None,
            "green_water_count": 0,
            "amenities_count": 0,
            "buildings": [],
            "roads": [],
            "greens_water": [],
            "amenities": [],
            "limitations": "Overpass API unreachable/rate-limited; no building footprints fabricated.",
        }

    buildings: List[Dict[str, Any]] = []
    roads: List[Dict[str, Any]] = []
    greens_water: List[Dict[str, Any]] = []
    amenities: List[Dict[str, Any]] = []

    total_bldg_area = 0.0
    total_bldg_count = 0
    total_road_m = 0.0
    total_road_count = 0
    tagged_height_count = 0
    estimated_levels_count = 0

    for el in raw_json["elements"]:
        etype = el.get("type")
        tags = el.get("tags") or {}
        if etype == "node":
            if "amenity" in tags and isinstance(el.get("lat"), (int, float)) and isinstance(el.get("lon"), (int, float)):
                amenities.append({
                    "id": el.get("id"),
                    "amenity": tags.get("amenity"),
                    "name": tags.get("name") or tags.get("amenity"),
                    "lat": round(float(el["lat"]), 6),
                    "lon": round(float(el["lon"]), 6),
                })
            continue

        geom = el.get("geometry") or []
        coords = [(float(pt["lon"]), float(pt["lat"])) for pt in geom if isinstance(pt, dict) and "lat" in pt and "lon" in pt]
        if len(coords) < 2:
            continue

        if "building" in tags and len(coords) >= 3:
            total_bldg_count += 1
            area_m2 = _polygon_area_local_m2(coords, lat, lon)
            total_bldg_area += area_m2
            h_m, h_src = _parse_building_height(tags)
            if h_src == "osm_height_tag":
                tagged_height_count += 1
            elif h_src == "estimated_from_osm_levels":
                estimated_levels_count += 1
            if len(buildings) < 180:
                c_lon = sum(p[0] for p in coords) / len(coords)
                c_lat = sum(p[1] for p in coords) / len(coords)
                buildings.append({
                    "id": el.get("id"),
                    "name": tags.get("name"),
                    "building_type": tags.get("building"),
                    "height_m": h_m,
                    "height_source": h_src,
                    "area_m2": round(area_m2, 1),
                    "centroid": [round(c_lon, 6), round(c_lat, 6)],
                    "coords": [[round(p[0], 6), round(p[1], 6)] for p in coords[:40]],
                })
        elif "highway" in tags:
            total_road_count += 1
            seg_m = _polyline_length_m(coords, lat, lon)
            total_road_m += seg_m
            if len(roads) < 180:
                roads.append({
                    "id": el.get("id"),
                    "name": tags.get("name"),
                    "highway": tags.get("highway"),
                    "length_m": round(seg_m, 1),
                    "coords": [[round(p[0], 6), round(p[1], 6)] for p in coords[:50]],
                })
        elif "natural" in tags or "waterway" in tags or "leisure" in tags or "landuse" in tags:
            kind = "water" if (tags.get("natural") == "water" or "waterway" in tags) else "green"
            if len(greens_water) < 80:
                greens_water.append({
                    "id": el.get("id"),
                    "kind": kind,
                    "name": tags.get("name"),
                    "is_polygon": len(coords) >= 3 and coords[0] == coords[-1],
                    "coords": [[round(p[0], 6), round(p[1], 6)] for p in coords[:50]],
                })

    ring_area_m2 = math.pi * r_m * r_m
    cov_pct = round(min(100.0, 100.0 * total_bldg_area / ring_area_m2), 2) if ring_area_m2 > 0 else 0.0

    result: Dict[str, Any] = {
        "status": "LIVE",
        "cached": False,
        "attribution": "© OpenStreetMap contributors (ODbL)",
        "radius_m": round(r_m, 1),
        "ring_area_m2": round(ring_area_m2, 1),
        "building_count": total_bldg_count,
        "building_footprint_total_m2": round(total_bldg_area, 1),
        "site_coverage_pct": cov_pct,
        "heights_tagged_count": tagged_height_count,
        "heights_estimated_levels_count": estimated_levels_count,
        "roads_count": total_road_count,
        "road_length_km": round(total_road_m / 1000.0, 3),
        "green_water_count": len(greens_water),
        "amenities_count": len(amenities),
        "buildings": buildings,
        "roads": roads,
        "greens_water": greens_water,
        "amenities": amenities[:40],
        "limitations": (
            f"Building heights reflect OSM 'height' tags ({tagged_height_count}) and 'building:levels'*3.2m estimates "
            f"({estimated_levels_count}); untagged footprints default to 6.4m lowrise envelope."
        ),
    }
    _OVERPASS_CACHE[cache_key] = (now_ts, result)
    return result


# ---------------------------------------------------------------------------
# 5. MARCHING-SQUARES DEM CONTOURS & TRANSECT PROFILES
# ---------------------------------------------------------------------------

def _bilinear_dem_elev(matrix: List[List[float]], bounds: Dict[str, float], lat: float, lon: float) -> float:
    n_r = len(matrix)
    n_c = len(matrix[0]) if n_r else 0
    if n_r == 0 or n_c == 0:
        return 0.0
    north, south = float(bounds["north"]), float(bounds["south"])
    west, east = float(bounds["west"]), float(bounds["east"])
    u = max(0.0, min(1.0, (lon - west) / max(1e-9, east - west))) * (n_c - 1)
    v = max(0.0, min(1.0, (north - lat) / max(1e-9, north - south))) * (n_r - 1)
    c0, r0 = int(math.floor(u)), int(math.floor(v))
    c1, r1 = min(n_c - 1, c0 + 1), min(n_r - 1, r0 + 1)
    dc, dr = u - c0, v - r0
    z00 = float(matrix[r0][c0])
    z01 = float(matrix[r0][c1])
    z10 = float(matrix[r1][c0])
    z11 = float(matrix[r1][c1])
    return (1.0 - dr) * ((1.0 - dc) * z00 + dc * z01) + dr * ((1.0 - dc) * z10 + dc * z11)


def _stitch_segments_into_polylines(segments: List[Tuple[Tuple[float, float], Tuple[float, float]]], tol: float = 1e-6) -> List[List[List[float]]]:
    """Chain disconnected Marching Squares contour edges into continuous polylines."""
    if not segments:
        return []
    remaining = list(segments)
    chains: List[List[Tuple[float, float]]] = []

    def _near(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
        return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol

    while remaining:
        a0, b0 = remaining.pop(0)
        chain = [a0, b0]
        extended = True
        while extended and remaining:
            extended = False
            for idx, (s0, s1) in enumerate(remaining):
                if _near(chain[-1], s0):
                    chain.append(s1)
                    remaining.pop(idx)
                    extended = True
                    break
                if _near(chain[-1], s1):
                    chain.append(s0)
                    remaining.pop(idx)
                    extended = True
                    break
                if _near(chain[0], s1):
                    chain.insert(0, s0)
                    remaining.pop(idx)
                    extended = True
                    break
                if _near(chain[0], s0):
                    chain.insert(0, s1)
                    remaining.pop(idx)
                    extended = True
                    break
        chains.append(chain)

    return [[[round(p[0], 6), round(p[1], 6)] for p in ch] for ch in chains if len(ch) >= 2]


def extract_dem_contours_and_profiles(dem_payload: Optional[Dict[str, Any]], levels: int = 7) -> Dict[str, Any]:
    """Generate Marching-Squares contour polylines and W-E / S-N elevation cross-section profiles from a DEM matrix."""
    if not dem_payload or not dem_payload.get("live_online") or not dem_payload.get("elev_matrix") or not dem_payload.get("bounds"):
        return {
            "status": "UNAVAILABLE",
            "source": "Copernicus GLO-90 DEM (Open-Meteo)",
            "contours": [],
            "profiles": {"west_east": [], "south_north": []},
            "limitations": "Live DEM matrix unavailable; zero synthetic contours generated.",
        }

    mat: List[List[float]] = dem_payload["elev_matrix"]
    b = dem_payload["bounds"]
    north, south = float(b["north"]), float(b["south"])
    west, east = float(b["west"]), float(b["east"])
    n_r = len(mat)
    n_c = len(mat[0]) if n_r else 0
    if n_r < 2 or n_c < 2:
        return {"status": "UNAVAILABLE", "contours": [], "profiles": {"west_east": [], "south_north": []}}

    flat = [float(v) for row in mat for v in row]
    z_min, z_max = min(flat), max(flat)
    relief = z_max - z_min

    # Build equally spaced levels strictly inside (z_min, z_max)
    contours: List[Dict[str, Any]] = []
    if relief >= 0.3 and levels >= 1:
        step = relief / (levels + 1)
        thresholds = [round(z_min + (i + 1) * step, 2) for i in range(levels)]
        # Marching squares edge lookup: 0=bottom(SW->SE), 1=right(SE->NE), 2=top(NW->NE), 3=left(SW->NW)
        edge_table: Dict[int, List[Tuple[int, int]]] = {
            0: [], 15: [],
            1: [(3, 0)], 14: [(3, 0)],
            2: [(0, 1)], 13: [(0, 1)],
            3: [(3, 1)], 12: [(3, 1)],
            4: [(1, 2)], 11: [(1, 2)],
            5: [(3, 2), (0, 1)],  # Saddle handled via center value below
            6: [(0, 2)], 9: [(0, 2)],
            7: [(3, 2)], 8: [(3, 2)],
            10: [(3, 0), (1, 2)],
        }
        for lvl in thresholds:
            segs: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []
            for r in range(n_r - 1):
                lat_top = north - (r / (n_r - 1)) * (north - south)
                lat_bot = north - ((r + 1) / (n_r - 1)) * (north - south)
                for c in range(n_c - 1):
                    lon_left = west + (c / (n_c - 1)) * (east - west)
                    lon_right = west + ((c + 1) / (n_c - 1)) * (east - west)
                    # Grid: mat[r] is North row, mat[r+1] is South row
                    nw = float(mat[r][c])
                    ne = float(mat[r][c + 1])
                    se = float(mat[r + 1][c + 1])
                    sw = float(mat[r + 1][c])
                    code = (8 if nw >= lvl else 0) | (4 if ne >= lvl else 0) | (2 if se >= lvl else 0) | (1 if sw >= lvl else 0)
                    pairs = edge_table.get(code, [])
                    if not pairs:
                        continue
                    if code == 5 and (nw + ne + se + sw) * 0.25 < lvl:
                        pairs = [(3, 0), (1, 2)]
                    elif code == 10 and (nw + ne + se + sw) * 0.25 < lvl:
                        pairs = [(3, 2), (0, 1)]

                    def _interp(edge_id: int) -> Tuple[float, float]:
                        if edge_id == 0:
                            t = (lvl - sw) / ((se - sw) or 1e-9)
                            return (lon_left + max(0.0, min(1.0, t)) * (lon_right - lon_left), lat_bot)
                        if edge_id == 1:
                            t = (lvl - se) / ((ne - se) or 1e-9)
                            return (lon_right, lat_bot + max(0.0, min(1.0, t)) * (lat_top - lat_bot))
                        if edge_id == 2:
                            t = (lvl - nw) / ((ne - nw) or 1e-9)
                            return (lon_left + max(0.0, min(1.0, t)) * (lon_right - lon_left), lat_top)
                        t = (lvl - sw) / ((nw - sw) or 1e-9)
                        return (lon_left, lat_bot + max(0.0, min(1.0, t)) * (lat_top - lat_bot))

                    for e1, e2 in pairs:
                        segs.append((_interp(e1), _interp(e2)))

            polylines = _stitch_segments_into_polylines(segs)
            if polylines:
                contours.append({"elevation_m": lvl, "polylines": polylines})

    # Center W-E and S-N topographic transects
    c_lat = (north + south) * 0.5
    c_lon = (west + east) * 0.5
    m_per_deg_lat = 111132.92
    m_per_deg_lon = 111412.84 * math.cos(math.radians(c_lat))

    mid_r = n_r // 2
    we_width_m = (east - west) * m_per_deg_lon
    we_profile = [
        {
            "distance_m": round((c / max(1, n_c - 1)) * we_width_m, 1),
            "elevation_m": round(float(mat[mid_r][c]), 2),
            "lon": round(west + (c / max(1, n_c - 1)) * (east - west), 5),
            "lat": round(north - (mid_r / max(1, n_r - 1)) * (north - south), 5),
        }
        for c in range(n_c)
    ]

    mid_c = n_c // 2
    sn_height_m = (north - south) * m_per_deg_lat
    sn_profile = []
    # Orient strictly South -> North (from row n_r - 1 up to row 0)
    for idx, r in enumerate(range(n_r - 1, -1, -1)):
        sn_profile.append({
            "distance_m": round((idx / max(1, n_r - 1)) * sn_height_m, 1),
            "elevation_m": round(float(mat[r][mid_c]), 2),
            "lon": round(c_lon, 5),
            "lat": round(south + (idx / max(1, n_r - 1)) * (north - south), 5),
        })

    return {
        "status": "COMPUTED",
        "source": dem_payload.get("source_api") or "Copernicus GLO-90 DEM (Open-Meteo)",
        "min_m": round(z_min, 2),
        "max_m": round(z_max, 2),
        "relief_m": round(relief, 2),
        "contour_count": sum(len(c["polylines"]) for c in contours),
        "contours": contours,
        "profiles": {
            "west_east": we_profile,
            "south_north": sn_profile,
            "we_span_m": round(we_width_m, 1),
            "sn_span_m": round(sn_height_m, 1),
        },
    }


# ---------------------------------------------------------------------------
# 6. UNIFIED SITE ANALYSIS ORCHESTRATOR
# ---------------------------------------------------------------------------

def run_site_analysis(
    lat: float,
    lon: float,
    place_name: Optional[str] = None,
    radius_m: float = 350.0,
    date_iso: Optional[str] = None,
    building_height_m: float = 10.0,
    include_osm: bool = True,
    include_utci: bool = True,
    include_dem: bool = True,
    span_deg: float = 0.04,
) -> Dict[str, Any]:
    """Run integrated Solar, Shadow, UTM, UTCI Comfort, Wind Rose, Live OSM Context & DEM Contours for (lat, lon)."""
    if not (-90.0 <= float(lat) <= 90.0) or not (-180.0 <= float(lon) <= 180.0):
        raise ValueError(f"Coordinates out of WGS84 range: ({lat}, {lon})")

    t0 = time.perf_counter()
    utm = latlon_to_utm(lat, lon)
    solar = compute_solar_and_shadow_profile(lat, lon, date_iso=date_iso, building_height_m=building_height_m)

    utci_res: Dict[str, Any] = {"status": "SKIPPED"}
    osm_res: Dict[str, Any] = {"status": "SKIPPED"}
    dem_res: Dict[str, Any] = {"live_online": False}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        f_utci = pool.submit(fetch_solar_wind_utci_assessment, lat, lon, solar) if include_utci else None
        f_osm = pool.submit(fetch_osm_site_context, lat, lon, radius_m) if include_osm else None
        f_dem = None
        if include_dem and fetch_location_3d_dem is not None:
            f_dem = pool.submit(fetch_location_3d_dem, place_name or f"{lat:.4f},{lon:.4f}", lat, lon, span_deg, 10)

        if f_utci is not None:
            utci_res = f_utci.result()
        if f_osm is not None:
            osm_res = f_osm.result()
        if f_dem is not None:
            dem_res = f_dem.result()

    contours_res = extract_dem_contours_and_profiles(dem_res, levels=7) if include_dem else {"status": "SKIPPED"}

    return {
        "schema": "bhu-loka-site-studio-v3.2",
        "location": {
            "name": place_name or f"{lat:.4f}°, {lon:.4f}°",
            "latitude": round(float(lat), 5),
            "longitude": round(float(lon), 5),
            "crs": "EPSG:4326",
            "utm": utm,
        },
        "solar": solar,
        "thermal_utci_wind": utci_res,
        "osm_context": osm_res,
        "terrain_contours": contours_res,
        "dem_payload": dem_res if (isinstance(dem_res, dict) and dem_res.get("live_online")) else None,
        "attribution": {
            "osm": "© OpenStreetMap contributors (ODbL)",
            "dem": "Copernicus GLO-90 DEM via Open-Meteo",
            "weather": "Open-Meteo ECMWF/DWD",
            "solar": "NOAA Solar Ephemeris (Deterministic Geometry)",
            "thermal": "Bröde et al. (2012) UTCI Polynomial (COST Action 730)",
        },
        "latency_ms": round((time.perf_counter() - t0) * 1000.0, 1),
    }


# ---------------------------------------------------------------------------
# 7. TRUE-SCALE METRIC CAD, VECTOR SVG, 3D GLB/OBJ & GEOJSON EXPORTERS
# ---------------------------------------------------------------------------

def _lonlat_to_local_meters(lon: float, lat: float, center_lat: float, center_lon: float, center_utm: Dict[str, Any]) -> Tuple[float, float]:
    """Project (lon, lat) into true-scale metric UTM offset (dx_east_m, dy_north_m) centered on site."""
    pt_utm = latlon_to_utm(lat, lon, force_zone=center_utm["zone"])
    return (
        pt_utm["easting_m"] - center_utm["easting_m"],
        pt_utm["northing_m"] - center_utm["northing_m"],
    )


def build_geojson_bundle(site_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble RFC 7946 WGS84 FeatureCollection across site ring, solar rays, DEM contours, and live OSM."""
    loc = site_analysis["location"]
    lat, lon = float(loc["latitude"]), float(loc["longitude"])
    osm = site_analysis.get("osm_context") or {}
    solar = site_analysis.get("solar") or {}
    contours_blk = site_analysis.get("terrain_contours") or {}
    r_m = float(osm.get("radius_m") or 350.0)

    features: List[Dict[str, Any]] = []

    # 1. Site center
    features.append({
        "type": "Feature",
        "properties": {
            "layer": "site_center",
            "name": loc["name"],
            "utm_epsg": loc["utm"]["epsg"],
            "easting_m": loc["utm"]["easting_m"],
            "northing_m": loc["utm"]["northing_m"],
        },
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    })

    # 2. Site ring polygon (64 vertices)
    dlat_r = r_m / 111132.92
    dlon_r = r_m / (111412.84 * max(0.1, math.cos(math.radians(lat))))
    ring_coords = []
    for k in range(65):
        ang = (2.0 * math.pi * (k % 64)) / 64.0
        ring_coords.append([round(lon + dlon_r * math.cos(ang), 6), round(lat + dlat_r * math.sin(ang), 6)])
    features.append({
        "type": "Feature",
        "properties": {"layer": "site_boundary", "radius_m": r_m},
        "geometry": {"type": "Polygon", "coordinates": [ring_coords]},
    })

    # 3. Solar / shadow vectors (Current, Jun 21 Noon, Dec 21 Noon)
    cur_sol = solar.get("current") or {}
    if cur_sol.get("azimuth_deg") is not None:
        az = math.radians(cur_sol["azimuth_deg"])
        features.append({
            "type": "Feature",
            "properties": {"layer": "solar_vector", "label": "Current Sun Bearing", "azimuth_deg": cur_sol["azimuth_deg"], "elevation_deg": cur_sol.get("elevation_deg")},
            "geometry": {"type": "LineString", "coordinates": [[lon, lat], [round(lon + dlon_r * math.sin(az), 6), round(lat + dlat_r * math.cos(az), 6)]]},
        })
        sh_az = math.radians(cur_sol.get("shadow_azimuth_deg", (cur_sol["azimuth_deg"] + 180.0) % 360.0))
        features.append({
            "type": "Feature",
            "properties": {"layer": "solar_shadow_ray", "label": "Current Shadow Cast", "shadow_azimuth_deg": cur_sol.get("shadow_azimuth_deg")},
            "geometry": {"type": "LineString", "coordinates": [[lon, lat], [round(lon + 0.7 * dlon_r * math.sin(sh_az), 6), round(lat + 0.7 * dlat_r * math.cos(sh_az), 6)]]},
        })

    # 4. Contours
    for c_lvl in (contours_blk.get("contours") or []):
        elev = c_lvl["elevation_m"]
        for line in c_lvl.get("polylines") or []:
            features.append({
                "type": "Feature",
                "properties": {"layer": "dem_contour", "elevation_m": elev},
                "geometry": {"type": "LineString", "coordinates": line},
            })

    # 5. Live OSM Buildings, Roads, Green/Water
    for b in (osm.get("buildings") or []):
        coords = list(b["coords"])
        if len(coords) >= 3 and coords[0] != coords[-1]:
            coords.append(coords[0])
        if len(coords) >= 4:
            features.append({
                "type": "Feature",
                "properties": {
                    "layer": "osm_building",
                    "osm_id": b.get("id"),
                    "name": b.get("name"),
                    "building": b.get("building_type"),
                    "height_m": b.get("height_m"),
                    "height_source": b.get("height_source"),
                    "area_m2": b.get("area_m2"),
                },
                "geometry": {"type": "Polygon", "coordinates": [coords]},
            })

    for rd in (osm.get("roads") or []):
        if len(rd.get("coords") or []) >= 2:
            features.append({
                "type": "Feature",
                "properties": {"layer": "osm_road", "osm_id": rd.get("id"), "highway": rd.get("highway"), "name": rd.get("name")},
                "geometry": {"type": "LineString", "coordinates": rd["coords"]},
            })

    for gw in (osm.get("greens_water") or []):
        if len(gw.get("coords") or []) >= 2:
            gtype = "Polygon" if gw.get("is_polygon") and len(gw["coords"]) >= 4 else "LineString"
            gcoords = [gw["coords"]] if gtype == "Polygon" else gw["coords"]
            features.append({
                "type": "Feature",
                "properties": {"layer": f"osm_{gw.get('kind', 'feature')}", "osm_id": gw.get("id"), "name": gw.get("name")},
                "geometry": {"type": gtype, "coordinates": gcoords},
            })

    return {
        "type": "FeatureCollection",
        "name": f"BHU_LOKA_{loc['name']}",
        "metadata": {
            "schema": site_analysis.get("schema"),
            "center_wgs84": [lon, lat],
            "utm": loc["utm"],
            "osm_status": osm.get("status"),
            "attribution": site_analysis.get("attribution"),
        },
        "features": features,
    }


def build_dxf_ascii(site_analysis: Dict[str, Any]) -> str:
    """
    Generate valid AutoCAD AC1015 ASCII DXF in true-scale local metric UTM coordinates (meters centered on site).
    Layers: 0_SITE_BOUNDARY (4), 1_DEM_CONTOURS (3), 2_OSM_BUILDINGS (1), 3_OSM_ROADS (7), 4_SOLAR_VECTORS (2).
    """
    loc = site_analysis["location"]
    lat, lon = float(loc["latitude"]), float(loc["longitude"])
    utm = loc["utm"]
    osm = site_analysis.get("osm_context") or {}
    solar = site_analysis.get("solar") or {}
    contours_blk = site_analysis.get("terrain_contours") or {}
    r_m = float(osm.get("radius_m") or 350.0)

    out: List[str] = []

    def g(code: int, val: Any) -> None:
        out.append(str(code))
        out.append(str(val))

    # Provenance comments
    g(999, f"BHU LOKA Site Studio v3.2 True-Scale Metric DXF ({utm['epsg']})")
    g(999, f"Origin UTM E={utm['easting_m']}m N={utm['northing_m']}m | WGS84 {lat},{lon}")
    g(999, "Attribution: (c) OpenStreetMap contributors (ODbL) | Copernicus GLO-90 DEM")

    # HEADER section (AC1015 = AutoCAD 2000 for LWPOLYLINE support; $INSUNITS = 6 Meters)
    g(0, "SECTION"); g(2, "HEADER")
    g(9, "$ACADVER"); g(1, "AC1015")
    g(9, "$INSUNITS"); g(70, 6)
    g(9, "$EXTMIN"); g(10, -r_m * 1.5); g(20, -r_m * 1.5); g(30, 0.0)
    g(9, "$EXTMAX"); g(10, r_m * 1.5); g(20, r_m * 1.5); g(30, 100.0)
    g(0, "ENDSEC")

    # TABLES section (LAYER definitions)
    layers = [
        ("0_SITE_BOUNDARY", 4),  # Cyan
        ("1_DEM_CONTOURS", 3),   # Green
        ("2_OSM_BUILDINGS", 1),  # Red
        ("3_OSM_ROADS", 7),      # White
        ("4_SOLAR_VECTORS", 2),  # Yellow
    ]
    g(0, "SECTION"); g(2, "TABLES")
    g(0, "TABLE"); g(2, "LAYER"); g(70, len(layers))
    for lname, lcol in layers:
        g(0, "LAYER"); g(2, lname); g(70, 0); g(62, lcol); g(6, "CONTINUOUS")
    g(0, "ENDTAB")
    g(0, "ENDSEC")

    # ENTITIES section
    g(0, "SECTION"); g(2, "ENTITIES")

    def add_lwpolyline(layer: str, pts_xy: List[Tuple[float, float]], closed: bool = False, elev: float = 0.0, thickness: float = 0.0) -> None:
        if len(pts_xy) < 2:
            return
        g(0, "LWPOLYLINE"); g(8, layer)
        g(90, len(pts_xy)); g(70, 1 if closed else 0)
        if abs(elev) > 1e-4:
            g(38, round(elev, 2))
        if thickness > 0.0:
            g(39, round(thickness, 2))
        for x, y in pts_xy:
            g(10, round(x, 3)); g(20, round(y, 3))

    def add_line(layer: str, x1: float, y1: float, x2: float, y2: float) -> None:
        g(0, "LINE"); g(8, layer)
        g(10, round(x1, 3)); g(20, round(y1, 3)); g(30, 0.0)
        g(11, round(x2, 3)); g(21, round(y2, 3)); g(31, 0.0)

    def add_text(layer: str, x: float, y: float, height: float, text: str) -> None:
        g(0, "TEXT"); g(8, layer)
        g(10, round(x, 2)); g(20, round(y, 2)); g(30, 0.0)
        g(40, round(height, 2)); g(1, text[:120])

    # Site boundary circle (72-vertex metric polyline)
    circle_pts = [(r_m * math.cos(2.0 * math.pi * k / 72.0), r_m * math.sin(2.0 * math.pi * k / 72.0)) for k in range(72)]
    add_lwpolyline("0_SITE_BOUNDARY", circle_pts, closed=True)
    add_line("0_SITE_BOUNDARY", -10.0, 0.0, 10.0, 0.0)
    add_line("0_SITE_BOUNDARY", 0.0, -10.0, 0.0, 10.0)
    add_text("0_SITE_BOUNDARY", -r_m, -r_m - 25.0, 12.0, f"BHU LOKA | {utm['epsg']} E={utm['easting_m']} N={utm['northing_m']} | OSM ODbL")

    # Solar rays
    cur_sol = solar.get("current") or {}
    if cur_sol.get("azimuth_deg") is not None:
        az = math.radians(cur_sol["azimuth_deg"])
        add_line("4_SOLAR_VECTORS", 0.0, 0.0, r_m * math.sin(az), r_m * math.cos(az))
        add_text("4_SOLAR_VECTORS", r_m * 0.7 * math.sin(az), r_m * 0.7 * math.cos(az), 8.0, f"SUN AZ {cur_sol['azimuth_deg']} EL {cur_sol.get('elevation_deg')}")

    # DEM contours (true elevation on group 38)
    for c_lvl in (contours_blk.get("contours") or []):
        elev = float(c_lvl["elevation_m"])
        for line in c_lvl.get("polylines") or []:
            xy = [_lonlat_to_local_meters(p[0], p[1], lat, lon, utm) for p in line]
            add_lwpolyline("1_DEM_CONTOURS", xy, closed=False, elev=elev)

    # OSM Roads
    for rd in (osm.get("roads") or []):
        xy = [_lonlat_to_local_meters(p[0], p[1], lat, lon, utm) for p in rd.get("coords") or []]
        add_lwpolyline("3_OSM_ROADS", xy, closed=False)

    # OSM Buildings (closed polylines with CAD extrusion thickness = height_m)
    for b in (osm.get("buildings") or []):
        coords = b.get("coords") or []
        if len(coords) >= 3:
            xy = [_lonlat_to_local_meters(p[0], p[1], lat, lon, utm) for p in coords]
            if len(xy) >= 4 and math.hypot(xy[0][0] - xy[-1][0], xy[0][1] - xy[-1][1]) < 0.05:
                xy = xy[:-1]
            add_lwpolyline("2_OSM_BUILDINGS", xy, closed=True, thickness=float(b.get("height_m") or 6.4))

    g(0, "ENDSEC")
    g(0, "EOF")
    return "\n".join(out) + "\n"


def build_layered_svg(site_analysis: Dict[str, Any]) -> str:
    """
    Generate Printmaps-style layered 1000x1000 vector SVG artboard (Illustrator/Inkscape ready)
    with grouped layers, north arrow, metric scale bar, solar azimuth overlay, and OSM ODbL + Copernicus attribution.
    """
    loc = site_analysis["location"]
    lat, lon = float(loc["latitude"]), float(loc["longitude"])
    utm = loc["utm"]
    osm = site_analysis.get("osm_context") or {}
    solar = site_analysis.get("solar") or {}
    utci_blk = site_analysis.get("thermal_utci_wind") or {}
    contours_blk = site_analysis.get("terrain_contours") or {}
    r_m = float(osm.get("radius_m") or 350.0)

    W, H = 1000.0, 1000.0
    pad = 85.0
    view_span_m = r_m * 2.25
    scale = (W - 2.0 * pad) / view_span_m  # px per meter

    def to_svg_xy(pt_m: Tuple[float, float]) -> Tuple[float, float]:
        return round(W * 0.5 + pt_m[0] * scale, 2), round(H * 0.5 - pt_m[1] * scale, 2)

    parts: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int(W)} {int(H)}" width="1000" height="1000" style="background:#080c12;font-family:\'IBM Plex Mono\',Consolas,monospace;">',
        f'  <title>BHU LOKA Site Studio · {xml_escape(loc["name"])} ({utm["epsg"]})</title>',
        '  <g id="layer-frame">',
        f'    <rect x="0" y="0" width="{int(W)}" height="{int(H)}" fill="#080c12"/>',
        '    <rect x="24" y="24" width="952" height="952" fill="none" stroke="#1e293b" stroke-width="1.5"/>',
        '  </g>',
    ]

    # Contours layer
    parts.append('  <g id="layer-contours" fill="none" stroke="#10b981" stroke-opacity="0.45" stroke-width="1.1">')
    for c_lvl in (contours_blk.get("contours") or []):
        for line in c_lvl.get("polylines") or []:
            pts_px = [to_svg_xy(_lonlat_to_local_meters(p[0], p[1], lat, lon, utm)) for p in line]
            d_attr = " ".join(("M" if i == 0 else "L") + f"{x},{y}" for i, (x, y) in enumerate(pts_px))
            parts.append(f'    <path d="{d_attr}" data-elev-m="{c_lvl["elevation_m"]}"/>')
    parts.append('  </g>')

    # Green & Water layer
    parts.append('  <g id="layer-water-parks">')
    for gw in (osm.get("greens_water") or []):
        pts_px = [to_svg_xy(_lonlat_to_local_meters(p[0], p[1], lat, lon, utm)) for p in gw.get("coords") or []]
        if len(pts_px) >= 2:
            pts_str = " ".join(f"{x},{y}" for x, y in pts_px)
            is_water = gw.get("kind") == "water"
            col = "#0284c7" if is_water else "#059669"
            if gw.get("is_polygon"):
                parts.append(f'    <polygon points="{pts_str}" fill="{col}" fill-opacity="0.22" stroke="{col}" stroke-width="1.2"/>')
            else:
                parts.append(f'    <polyline points="{pts_str}" fill="none" stroke="{col}" stroke-width="2.2" stroke-opacity="0.75"/>')
    parts.append('  </g>')

    # Roads layer
    parts.append('  <g id="layer-roads" fill="none" stroke="#94a3b8" stroke-linecap="round" stroke-linejoin="round">')
    for rd in (osm.get("roads") or []):
        pts_px = [to_svg_xy(_lonlat_to_local_meters(p[0], p[1], lat, lon, utm)) for p in rd.get("coords") or []]
        if len(pts_px) >= 2:
            hw = str(rd.get("highway") or "")
            sw = 3.2 if hw in ("primary", "trunk", "motorway", "secondary") else (2.1 if hw == "tertiary" else 1.3)
            pts_str = " ".join(f"{x},{y}" for x, y in pts_px)
            parts.append(f'    <polyline points="{pts_str}" stroke-width="{sw}" stroke-opacity="0.72"/>')
    parts.append('  </g>')

    # Buildings layer
    parts.append('  <g id="layer-buildings" fill="#38bdf8" fill-opacity="0.32" stroke="#7dd3fc" stroke-width="1.0">')
    for b in (osm.get("buildings") or []):
        pts_px = [to_svg_xy(_lonlat_to_local_meters(p[0], p[1], lat, lon, utm)) for p in b.get("coords") or []]
        if len(pts_px) >= 3:
            pts_str = " ".join(f"{x},{y}" for x, y in pts_px)
            parts.append(f'    <polygon points="{pts_str}" data-height-m="{b.get("height_m")}"/>')
    parts.append('  </g>')

    # Site boundary & solar rays
    cx, cy = W * 0.5, H * 0.5
    r_px = round(r_m * scale, 2)
    parts.append('  <g id="layer-boundary-solar">')
    parts.append(f'    <circle cx="{cx}" cy="{cy}" r="{r_px}" fill="none" stroke="#38bdf8" stroke-width="1.6" stroke-dasharray="7 5"/>')
    parts.append(f'    <circle cx="{cx}" cy="{cy}" r="5" fill="#f43f5e" stroke="#ffffff" stroke-width="1.5"/>')

    cur_sol = solar.get("current") or {}
    if cur_sol.get("azimuth_deg") is not None:
        az = math.radians(cur_sol["azimuth_deg"])
        sx = round(cx + r_px * math.sin(az), 2)
        sy = round(cy - r_px * math.cos(az), 2)
        parts.append(f'    <line x1="{cx}" y1="{cy}" x2="{sx}" y2="{sy}" stroke="#f59e0b" stroke-width="2.2"/>')
        parts.append(f'    <circle cx="{sx}" cy="{sy}" r="6" fill="#f59e0b"/>')
        sh_az = math.radians(cur_sol.get("shadow_azimuth_deg", (cur_sol["azimuth_deg"] + 180.0) % 360.0))
        shx = round(cx + 0.65 * r_px * math.sin(sh_az), 2)
        shy = round(cy - 0.65 * r_px * math.cos(sh_az), 2)
        parts.append(f'    <line x1="{cx}" y1="{cy}" x2="{shx}" y2="{shy}" stroke="#cbd5e1" stroke-width="1.6" stroke-dasharray="4 3"/>')
    parts.append('  </g>')

    # HUD: Title, North Arrow, Scale bar, UTCI / UTM metadata, Mandatory ODbL & Copernicus Attribution
    scale_bar_m = 100.0 if r_m <= 500.0 else 200.0
    scale_bar_px = round(scale_bar_m * scale, 2)
    utci_lbl = f"UTCI {utci_blk['utci_sunlit_c']}°C" if utci_blk.get("utci_sunlit_c") is not None else "UTCI UNAVAIL"
    osm_lbl = f"{osm.get('building_count', 0)} OSM Bldgs ({osm.get('site_coverage_pct', 0)}%)" if osm.get("status") == "LIVE" else "OSM UNAVAILABLE"

    parts.extend([
        '  <g id="layer-hud">',
        '    <rect x="36" y="36" width="520" height="58" rx="4" fill="#0d131d" fill-opacity="0.9" stroke="#334155"/>',
        f'    <text x="50" y="58" fill="#f8fafc" font-size="15" font-weight="700">BHU LOKA SITE STUDIO · {xml_escape(str(loc["name"]).upper()[:32])}</text>',
        f'    <text x="50" y="80" fill="#7dd3fc" font-size="11">{lat:.4f}°N {lon:.4f}°E · {utm["epsg"]} E={utm["easting_m"]}m N={utm["northing_m"]}m</text>',
        # North Arrow
        '    <g transform="translate(925, 72)">',
        '      <polygon points="0,-24 9,8 0,2 -9,8" fill="#38bdf8"/>',
        '      <text x="0" y="24" text-anchor="middle" fill="#cbd5e1" font-size="12" font-weight="700">N</text>',
        '    </g>',
        # Scale Bar
        '    <g transform="translate(40, 932)">',
        f'      <line x1="0" y1="0" x2="{scale_bar_px}" y2="0" stroke="#f8fafc" stroke-width="3"/>',
        f'      <line x1="0" y1="-6" x2="0" y2="6" stroke="#f8fafc" stroke-width="2"/>',
        f'      <line x1="{scale_bar_px}" y1="-6" x2="{scale_bar_px}" y2="6" stroke="#f8fafc" stroke-width="2"/>',
        f'      <text x="0" y="-10" fill="#cbd5e1" font-size="11">{int(scale_bar_m)} m (True UTM Scale)</text>',
        '    </g>',
        f'    <text x="960" y="925" text-anchor="end" fill="#94a3b8" font-size="11">{xml_escape(osm_lbl)} · {xml_escape(utci_lbl)}</text>',
        '    <text x="960" y="948" text-anchor="end" fill="#64748b" font-size="10">© OpenStreetMap contributors (ODbL) · Copernicus GLO-90 DEM · NOAA Solar · Bröde UTCI</text>',
        '  </g>',
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def build_profile_svg(site_analysis: Dict[str, Any]) -> str:
    """Generate clean topographic W-E & S-N elevation cross-section SVG from DEM contours block."""
    loc = site_analysis["location"]
    tc = site_analysis.get("terrain_contours") or {}
    profs = tc.get("profiles") or {}
    we = profs.get("west_east") or []
    sn = profs.get("south_north") or []

    W, H = 900.0, 420.0
    if not we or not sn:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int(W)} {int(H)}" width="900" height="420" style="background:#080c12;font-family:monospace;">'
            f'<text x="450" y="210" text-anchor="middle" fill="#fb7185" font-size="15">ELEVATION PROFILE UNAVAILABLE (Copernicus GLO-90 DEM Offline)</text>'
            f'</svg>\n'
        )

    all_e = [p["elevation_m"] for p in we] + [p["elevation_m"] for p in sn]
    e_min = min(all_e) - 0.5
    e_max = max(all_e) + 0.5
    e_span = max(1.0, e_max - e_min)
    max_d = max([p["distance_m"] for p in we] + [p["distance_m"] for p in sn] + [1.0])

    gx0, gy0, gw, gh = 78.0, 68.0, 780.0, 276.0

    def pt_map(dist_m: float, elev_m: float) -> Tuple[float, float]:
        x = gx0 + (dist_m / max_d) * gw
        y = gy0 + gh - ((elev_m - e_min) / e_span) * gh
        return round(x, 2), round(y, 2)

    we_pts = " ".join(f"{x},{y}" for x, y in (pt_map(p["distance_m"], p["elevation_m"]) for p in we))
    sn_pts = " ".join(f"{x},{y}" for x, y in (pt_map(p["distance_m"], p["elevation_m"]) for p in sn))

    grid_lines: List[str] = []
    for k in range(5):
        frac = k / 4.0
        yv = round(gy0 + gh - frac * gh, 1)
        ev = round(e_min + frac * e_span, 1)
        grid_lines.append(f'<line x1="{gx0}" y1="{yv}" x2="{gx0 + gw}" y2="{yv}" stroke="#1e293b" stroke-width="1"/>')
        grid_lines.append(f'<text x="{gx0 - 10}" y="{yv + 4}" text-anchor="end" fill="#94a3b8" font-size="10">{ev}m</text>')

    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int(W)} {int(H)}" width="900" height="420" style="background:#080c12;font-family:\'IBM Plex Mono\',Consolas,monospace;">',
        f'  <text x="36" y="34" fill="#f8fafc" font-size="14" font-weight="700">BHU LOKA ELEVATION TRANSECT · {xml_escape(str(loc["name"]).upper())}</text>',
        f'  <text x="36" y="52" fill="#7dd3fc" font-size="11">Min {tc.get("min_m")}m · Max {tc.get("max_m")}m · Relief {tc.get("relief_m")}m · Span {int(round(max_d))}m</text>',
        *grid_lines,
        f'  <rect x="{gx0}" y="{gy0}" width="{gw}" height="{gh}" fill="none" stroke="#334155"/>',
        f'  <polyline points="{we_pts}" fill="none" stroke="#38bdf8" stroke-width="2.5"/>',
        f'  <polyline points="{sn_pts}" fill="none" stroke="#10b981" stroke-width="2.2" stroke-dasharray="6 4"/>',
        f'  <text x="{gx0}" y="372" fill="#38bdf8" font-size="11">— West → East Transect</text>',
        f'  <text x="{gx0 + 210}" y="372" fill="#10b981" font-size="11">--- South → North Transect</text>',
        '  <text x="858" y="396" text-anchor="end" fill="#64748b" font-size="10">Source: Copernicus GLO-90 DEM via Open-Meteo · BHU LOKA</text>',
        '</svg>',
    ]) + "\n"


def _compute_mesh_from_analysis(site_analysis: Dict[str, Any]) -> Tuple[List[float], List[float], List[float], List[int], List[float], List[float], List[int]]:
    """
    Build separate metric right-handed Y-up meshes (X=East m, Y=Elev m, Z=-North m):
    Returns (t_pos, t_norm, t_col, t_idx, b_pos, b_norm, b_idx).
    """
    loc = site_analysis["location"]
    lat0, lon0 = float(loc["latitude"]), float(loc["longitude"])
    utm = loc["utm"]
    dem = site_analysis.get("dem_payload")
    osm = site_analysis.get("osm_context") or {}

    t_pos: List[float] = []
    t_norm: List[float] = []
    t_col: List[float] = []
    t_idx: List[int] = []

    b_pos: List[float] = []
    b_norm: List[float] = []
    b_idx: List[int] = []

    base_elev = 0.0
    if dem and dem.get("live_online") and dem.get("elev_matrix") and dem.get("bounds"):
        mat = dem["elev_matrix"]
        bounds = dem["bounds"]
        flat = [float(v) for row in mat for v in row]
        base_elev = min(flat)
        elev_span = max(1.0, max(flat) - base_elev)

        grid_res = 24
        north, south = float(bounds["north"]), float(bounds["south"])
        west, east = float(bounds["west"]), float(bounds["east"])
        verts_3d: List[Tuple[float, float, float]] = []

        for r in range(grid_res):
            lat_r = north - (r / (grid_res - 1)) * (north - south)
            for c in range(grid_res):
                lon_c = west + (c / (grid_res - 1)) * (east - west)
                dx, dy = _lonlat_to_local_meters(lon_c, lat_r, lat0, lon0, utm)
                elev = _bilinear_dem_elev(mat, bounds, lat_r, lon_c)
                y_up = elev - base_elev
                z_south = -dy
                verts_3d.append((dx, y_up, z_south))
                t_pos.extend([dx, y_up, z_south])
                frac = max(0.0, min(1.0, y_up / elev_span))
                if frac < 0.5:
                    k = frac * 2.0
                    cr, cg, cb = 0.20 + 0.02 * k, 0.40 + 0.34 * k, 0.85 + 0.12 * k
                else:
                    k = (frac - 0.5) * 2.0
                    cr, cg, cb = 0.22 - 0.16 * k, 0.74 - 0.02 * k, 0.97 - 0.46 * k
                t_col.extend([round(cr, 4), round(cg, 4), round(cb, 4)])

        for r in range(grid_res - 1):
            for c in range(grid_res - 1):
                i0 = r * grid_res + c
                i1 = i0 + 1
                i2 = i0 + grid_res
                i3 = i2 + 1
                # Counter-clockwise Y-up winding
                t_idx.extend([i0, i2, i1, i1, i2, i3])

        # Compute vertex normals smoothly from adjacent vertices
        for r in range(grid_res):
            for c in range(grid_res):
                vl = verts_3d[r * grid_res + max(0, c - 1)]
                vr = verts_3d[r * grid_res + min(grid_res - 1, c + 1)]
                vu = verts_3d[max(0, r - 1) * grid_res + c]
                vd = verts_3d[min(grid_res - 1, r + 1) * grid_res + c]
                tx = (vr[0] - vl[0], vr[1] - vl[1], vr[2] - vl[2])
                tz = (vd[0] - vu[0], vd[1] - vu[1], vd[2] - vu[2])
                # cross(tz, tx) points UP (+Y) because tz points +Z (south) and tx points +X (east)
                nx = tz[1] * tx[2] - tz[2] * tx[1]
                ny = tz[2] * tx[0] - tz[0] * tx[2]
                nz = tz[0] * tx[1] - tz[1] * tx[0]
                nlen = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
                t_norm.extend([nx / nlen, ny / nlen, nz / nlen])

    # Extruded OSM Buildings sitting on DEM surface (only when LIVE buildings exist)
    for b in (osm.get("buildings") or []):
        coords = b.get("coords") or []
        if len(coords) < 3:
            continue
        ring = list(coords)
        if ring[0] == ring[-1]:
            ring = ring[:-1]
        if len(ring) < 3:
            continue

        # Ensure CCW in (x, y_north) -> CW in (x, z=-y_north)
        area2 = 0.0
        pts_m = [_lonlat_to_local_meters(p[0], p[1], lat0, lon0, utm) for p in ring]
        for i in range(len(pts_m)):
            x1, y1 = pts_m[i]
            x2, y2 = pts_m[(i + 1) % len(pts_m)]
            area2 += x1 * y2 - x2 * y1
        if area2 < 0:
            pts_m.reverse()

        c_lon, c_lat = b["centroid"][0], b["centroid"][1]
        ground_y = (_bilinear_dem_elev(dem["elev_matrix"], dem["bounds"], c_lat, c_lon) - base_elev) if (dem and dem.get("live_online")) else 0.0
        h_m = float(b.get("height_m") or 6.4)
        roof_y = ground_y + h_m

        # Side walls (2 triangles per wall edge, flat outward normal)
        n_pts = len(pts_m)
        for i in range(n_pts):
            x0, y0 = pts_m[i]
            x1, y1 = pts_m[(i + 1) % n_pts]
            z0, z1 = -y0, -y1
            wx, wz = x1 - x0, z1 - z0
            wlen = math.hypot(wx, wz) or 1.0
            # In CCW (x, y_north): outward 2D normal is (dy, -dx) -> in (x, z=-y): (-wz/wlen, 0, wx/wlen)
            nx, nz = -wz / wlen, wx / wlen
            v_start = len(b_pos) // 3
            for vx, vy, vz in (
                (x0, ground_y, z0),
                (x1, ground_y, z1),
                (x1, roof_y, z1),
                (x0, roof_y, z0),
            ):
                b_pos.extend([vx, vy, vz])
                b_norm.extend([nx, 0.0, nz])
            b_idx.extend([v_start, v_start + 1, v_start + 2, v_start, v_start + 2, v_start + 3])

        # Roof fan (centroid fan works reliably for convex & typical rectangular OSM footprints)
        cx = sum(p[0] for p in pts_m) / n_pts
        cy = sum(p[1] for p in pts_m) / n_pts
        cz = -cy
        r_center_idx = len(b_pos) // 3
        b_pos.extend([cx, roof_y, cz])
        b_norm.extend([0.0, 1.0, 0.0])
        for px, py in pts_m:
            b_pos.extend([px, roof_y, -py])
            b_norm.extend([0.0, 1.0, 0.0])
        for i in range(n_pts):
            b_idx.extend([r_center_idx, r_center_idx + 1 + ((i + 1) % n_pts), r_center_idx + 1 + i])

    return t_pos, t_norm, t_col, t_idx, b_pos, b_norm, b_idx


def _vec_min_max(flat: List[float], stride: int) -> Tuple[List[float], List[float]]:
    mins = [min(flat[i::stride]) for i in range(stride)]
    maxs = [max(flat[i::stride]) for i in range(stride)]
    return mins, maxs


def build_glb_binary(site_analysis: Dict[str, Any]) -> bytes:
    """
    Assemble a spec-compliant binary glTF 2.0 (.glb) package containing true-metric DEM relief
    plus extruded live OSM building prisms when available.
    """
    t_pos, t_norm, t_col, t_idx, b_pos, b_norm, b_idx = _compute_mesh_from_analysis(site_analysis)

    # If neither DEM nor buildings exist (offline), write a valid minimal anchor marker pyramid instead of empty invalid buffers
    if not t_pos and not b_pos:
        t_pos = [-5.0, 0.0, 5.0, 5.0, 0.0, 5.0, 0.0, 0.0, -5.0, 0.0, 8.0, 0.0]
        t_norm = [0.0, 1.0, 0.0] * 4
        t_col = [0.22, 0.74, 0.97] * 4
        t_idx = [0, 1, 3, 1, 2, 3, 2, 0, 3, 2, 1, 0]

    bin_chunks: List[bytes] = []
    buffer_views: List[Dict[str, Any]] = []
    accessors: List[Dict[str, Any]] = []
    meshes: List[Dict[str, Any]] = []
    nodes: List[Dict[str, Any]] = []
    byte_offset = 0

    def append_buffer(data_bytes: bytes, target: int) -> int:
        nonlocal byte_offset
        pad = (-len(data_bytes)) % 4
        bin_chunks.append(data_bytes + b"\x00" * pad)
        bv_idx = len(buffer_views)
        buffer_views.append({
            "buffer": 0,
            "byteOffset": byte_offset,
            "byteLength": len(data_bytes),
            "target": target,
        })
        byte_offset += len(data_bytes) + pad
        return bv_idx

    def add_vec3_accessor(vals: List[float], with_minmax: bool = False) -> int:
        packed = struct.pack(f"<{len(vals)}f", *vals)
        bv_idx = append_buffer(packed, 34962)
        acc: Dict[str, Any] = {
            "bufferView": bv_idx,
            "componentType": 5126,
            "count": len(vals) // 3,
            "type": "VEC3",
        }
        if with_minmax:
            mn, mx = _vec_min_max(vals, 3)
            acc["min"] = mn
            acc["max"] = mx
        acc_idx = len(accessors)
        accessors.append(acc)
        return acc_idx

    def add_idx_accessor(idxs: List[int]) -> int:
        packed = struct.pack(f"<{len(idxs)}I", *idxs)
        bv_idx = append_buffer(packed, 34963)
        acc_idx = len(accessors)
        accessors.append({
            "bufferView": bv_idx,
            "componentType": 5125,
            "count": len(idxs),
            "type": "SCALAR",
            "min": [min(idxs)],
            "max": [max(idxs)],
        })
        return acc_idx

    materials = [
        {
            "name": "TerrainReliefMat",
            "pbrMetallicRoughness": {"baseColorFactor": [1.0, 1.0, 1.0, 1.0], "metallicFactor": 0.05, "roughnessFactor": 0.85},
            "doubleSided": True,
        },
        {
            "name": "OsmBuildingsMat",
            "pbrMetallicRoughness": {"baseColorFactor": [0.22, 0.74, 0.97, 0.92], "metallicFactor": 0.15, "roughnessFactor": 0.65},
            "doubleSided": True,
        },
    ]

    if t_pos:
        acc_p = add_vec3_accessor(t_pos, with_minmax=True)
        acc_n = add_vec3_accessor(t_norm)
        acc_c = add_vec3_accessor(t_col)
        acc_i = add_idx_accessor(t_idx)
        m_idx = len(meshes)
        meshes.append({
            "name": "TerrainRelief",
            "primitives": [{"attributes": {"POSITION": acc_p, "NORMAL": acc_n, "COLOR_0": acc_c}, "indices": acc_i, "material": 0}],
        })
        nodes.append({"name": "TerrainRelief", "mesh": m_idx})

    if b_pos:
        acc_bp = add_vec3_accessor(b_pos, with_minmax=True)
        acc_bn = add_vec3_accessor(b_norm)
        acc_bi = add_idx_accessor(b_idx)
        m_idx = len(meshes)
        meshes.append({
            "name": "OsmBuildings",
            "primitives": [{"attributes": {"POSITION": acc_bp, "NORMAL": acc_bn}, "indices": acc_bi, "material": 1}],
        })
        nodes.append({"name": "OsmBuildings", "mesh": m_idx})

    bin_blob = b"".join(bin_chunks)
    gltf_doc = {
        "asset": {
            "version": "2.0",
            "generator": "BHU LOKA Site Studio v3.2",
            "copyright": "© OpenStreetMap contributors (ODbL) | Copernicus GLO-90 DEM",
        },
        "scene": 0,
        "scenes": [{"name": "BhuLokaSiteScene", "nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "bufferViews": buffer_views,
        "accessors": accessors,
        "buffers": [{"byteLength": len(bin_blob)}],
    }

    json_bytes = json.dumps(gltf_doc, separators=(",", ":")).encode("utf-8")
    json_pad = (-len(json_bytes)) % 4
    json_bytes += b" " * json_pad

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_blob)
    header = struct.pack("<III", 0x46546C67, 2, total_len)
    c0_hdr = struct.pack("<II", len(json_bytes), 0x4E4F534A)
    c1_hdr = struct.pack("<II", len(bin_blob), 0x004E4942)
    return header + c0_hdr + json_bytes + c1_hdr + bin_blob


def build_obj_mesh(site_analysis: Dict[str, Any]) -> str:
    """Export matching Wavefront .obj metric 3D terrain + extruded OSM buildings."""
    t_pos, t_norm, _t_col, t_idx, b_pos, b_norm, b_idx = _compute_mesh_from_analysis(site_analysis)
    loc = site_analysis["location"]
    utm = loc["utm"]

    lines: List[str] = [
        f"# BHU LOKA Site Studio v3.2 Wavefront OBJ ({utm['epsg']} meters, Y-up, North=-Z)",
        f"# Center WGS84: {loc['latitude']}, {loc['longitude']} | UTM E={utm['easting_m']}m N={utm['northing_m']}m",
        "# Attribution: (c) OpenStreetMap contributors (ODbL) | Copernicus GLO-90 DEM",
    ]
    v_offset = 1
    if t_pos:
        lines.append("o TerrainRelief")
        for i in range(0, len(t_pos), 3):
            lines.append(f"v {t_pos[i]:.3f} {t_pos[i+1]:.3f} {t_pos[i+2]:.3f}")
        for i in range(0, len(t_norm), 3):
            lines.append(f"vn {t_norm[i]:.4f} {t_norm[i+1]:.4f} {t_norm[i+2]:.4f}")
        for i in range(0, len(t_idx), 3):
            a, b, c = t_idx[i] + v_offset, t_idx[i + 1] + v_offset, t_idx[i + 2] + v_offset
            lines.append(f"f {a}//{a} {b}//{b} {c}//{c}")
        v_offset += len(t_pos) // 3

    if b_pos:
        lines.append("o OsmBuildings")
        for i in range(0, len(b_pos), 3):
            lines.append(f"v {b_pos[i]:.3f} {b_pos[i+1]:.3f} {b_pos[i+2]:.3f}")
        for i in range(0, len(b_norm), 3):
            lines.append(f"vn {b_norm[i]:.4f} {b_norm[i+1]:.4f} {b_norm[i+2]:.4f}")
        for i in range(0, len(b_idx), 3):
            a, b, c = b_idx[i] + v_offset, b_idx[i + 1] + v_offset, b_idx[i + 2] + v_offset
            lines.append(f"f {a}//{a} {b}//{b} {c}//{c}")

    return "\n".join(lines) + "\n"


def export_site_package(
    lat: float,
    lon: float,
    fmt: str = "geojson",
    place_name: Optional[str] = None,
    radius_m: float = 350.0,
    span_deg: float = 0.04,
) -> Dict[str, Any]:
    """Run site analysis and serialize requested export format with filename & MIME metadata."""
    fmt_clean = (fmt or "geojson").strip().lower()
    allowed = {"geojson", "dxf", "svg", "profile_svg", "glb", "obj"}
    if fmt_clean not in allowed:
        raise ValueError(f"Unsupported export format '{fmt}'. Expected one of {sorted(allowed)}.")

    need_osm = fmt_clean in {"geojson", "dxf", "svg", "glb", "obj"}
    need_dem = fmt_clean in {"geojson", "dxf", "svg", "profile_svg", "glb", "obj"}
    need_utci = fmt_clean == "svg"

    analysis = run_site_analysis(
        lat=lat,
        lon=lon,
        place_name=place_name,
        radius_m=radius_m,
        include_osm=need_osm,
        include_utci=need_utci,
        include_dem=need_dem,
        span_deg=span_deg,
    )

    safe_slug = "".join(ch if ch.isalnum() else "_" for ch in str(analysis["location"]["name"]).strip())[:28].strip("_") or "site"
    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if fmt_clean == "geojson":
        payload_bytes = json.dumps(build_geojson_bundle(analysis), indent=2, ensure_ascii=False).encode("utf-8")
        mime, ext = "application/geo+json", "geojson"
    elif fmt_clean == "dxf":
        payload_bytes = build_dxf_ascii(analysis).encode("utf-8")
        mime, ext = "application/dxf", "dxf"
    elif fmt_clean == "svg":
        payload_bytes = build_layered_svg(analysis).encode("utf-8")
        mime, ext = "image/svg+xml", "svg"
    elif fmt_clean == "profile_svg":
        payload_bytes = build_profile_svg(analysis).encode("utf-8")
        mime, ext = "image/svg+xml", "svg"
    elif fmt_clean == "obj":
        payload_bytes = build_obj_mesh(analysis).encode("utf-8")
        mime, ext = "model/obj", "obj"
    else:  # glb
        payload_bytes = build_glb_binary(analysis)
        mime, ext = "model/gltf-binary", "glb"

    return {
        "format": fmt_clean,
        "filename": f"bhu_loka_{safe_slug}_{ts_tag}.{ext}",
        "media_type": mime,
        "bytes": payload_bytes,
        "size_bytes": len(payload_bytes),
        "analysis_summary": {
            "utm": analysis["location"]["utm"],
            "osm_status": (analysis.get("osm_context") or {}).get("status"),
            "building_count": (analysis.get("osm_context") or {}).get("building_count", 0),
            "contour_count": (analysis.get("terrain_contours") or {}).get("contour_count", 0),
        },
        "attribution": analysis["attribution"],
    }
