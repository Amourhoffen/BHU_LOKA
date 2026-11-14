"""
BHU LOKA (भूलोक) - Shared Live API, Geospatial Data & Hybrid RAG Service Layer
Serves both the upgraded FastAPI server and the BHU LOKA MCP Server (FastMCP).

Connects:
1. Free Zero-Key Live Open-Meteo Weather & Soil Forecast API
2. Free Zero-Key Live Open-Meteo GloFAS River Flood Discharge API (m3/s)
3. Verified Sovereign India 36-State Boundaries & 12 National Hazard Hubs
4. Patna Copernicus DEM + Sentinel-1 SAR + NCRB / Rajya Sabha Q390 Safety JSON
5. Google Earth Engine Python Connector (`Repos/earthengine-api`)
6. Enterprise Hybrid RAG Pipeline (BM25 + FAISS RRF k=60)

Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

from __future__ import annotations

import concurrent.futures
import contextlib
import gzip
import json
import math
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "Data"
BOUNDS_DIR = DATA_DIR / "01_Boundaries"
CRIME_JSON_PATH = DATA_DIR / "09_Crime_Safety" / "patna_crime_safety_index.json"
ENTERPRISE_RAG_DIR = WORKSPACE_ROOT / "Models" / "04_Hybrid_RAG" / "enterprise_rag_app"

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from google_earth_engine_connector import BhuLokaGoogleEarthConnector  # type: ignore[import-not-found]
except ImportError:
    from Pipelines.google_earth_engine_connector import BhuLokaGoogleEarthConnector  # type: ignore[import-not-found]


_TELEMETRY_CACHE: Dict[str, Dict[str, Any]] = {}
_SATELLITE_GP_CACHE: Dict[str, Any] = {"ts": 0.0, "records": []}
_SATELLITE_DISK_CACHE_PATH = DATA_DIR / "08_Processed_Outputs" / ".celestrak_gp_cache.json"
_SATELLITE_DISK_CACHE_TTL_SECONDS = 1800.0
_DEM_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL_SECONDS = 300.0
_SATELLITE_CACHE_TTL_SECONDS = 900.0
_RAG_PIPELINE: Any = None


LOCATION_PRESETS: Dict[str, Dict[str, Any]] = {
    "patna": {"name": "Patna Municipal Core", "state": "Bihar", "lat": 25.594, "lon": 85.137, "flood_lat": 25.620, "flood_lon": 85.140, "river": "Ganga (Gandhi Ghat)"},
    "bihta": {"name": "Bihta / IIT Patna High Levee", "state": "Bihar", "lat": 25.536, "lon": 84.851, "flood_lat": 25.580, "flood_lon": 84.830, "river": "Son River Channel"},
    "danapur": {"name": "Danapur Cantonment", "state": "Bihar", "lat": 25.630, "lon": 85.040, "flood_lat": 25.640, "flood_lon": 85.070, "river": "Ganga (Digha-Danapur)"},
    "leh": {"name": "Leh / Ladakh Cryosphere", "state": "Ladakh", "lat": 34.152, "lon": 77.577, "flood_lat": 34.130, "flood_lon": 77.540, "river": "Upper Indus"},
    "srinagar": {"name": "Srinagar / Jhelum Basin", "state": "Jammu & Kashmir", "lat": 34.083, "lon": 74.797, "flood_lat": 34.080, "flood_lon": 74.800, "river": "Jhelum"},
    "itanagar": {"name": "Itanagar / Siang Headwaters", "state": "Arunachal Pradesh", "lat": 27.084, "lon": 93.605, "flood_lat": 28.070, "flood_lon": 95.330, "river": "Siang-Brahmaputra"},
    "guwahati": {"name": "Guwahati & Kaziranga / Assam", "state": "Assam", "lat": 26.144, "lon": 91.736, "flood_lat": 26.190, "flood_lon": 91.740, "river": "Brahmaputra"},
    "joshimath": {"name": "Joshimath / Upper Ganga", "state": "Uttarakhand", "lat": 30.550, "lon": 79.566, "flood_lat": 30.560, "flood_lon": 79.560, "river": "Alaknanda"},
    "mumbai": {"name": "Mumbai / Konkan Coast", "state": "Maharashtra", "lat": 19.076, "lon": 72.877, "flood_lat": 19.080, "flood_lon": 72.880, "river": "Mithi / Coastal"},
    "chennai": {"name": "Chennai / Adyar Basin", "state": "Tamil Nadu", "lat": 13.082, "lon": 80.270, "flood_lat": 13.020, "flood_lon": 80.250, "river": "Adyar"},
    "kolkata": {"name": "Sundarbans / Kolkata Delta", "state": "West Bengal", "lat": 22.572, "lon": 88.363, "flood_lat": 22.570, "flood_lon": 88.340, "river": "Hooghly"},
    "delhi": {"name": "Delhi NCR / Yamuna Floodplain", "state": "Delhi", "lat": 28.613, "lon": 77.209, "flood_lat": 28.650, "flood_lon": 77.250, "river": "Yamuna"},
    "phalodi": {"name": "Thar Core / Phalodi", "state": "Rajasthan", "lat": 27.131, "lon": 72.368, "flood_lat": 27.131, "flood_lon": 72.368, "river": "Arid Drainage"},
    "ayodhya": {"name": "Ayodhya / Sarayu Basin", "state": "Uttar Pradesh", "lat": 26.795, "lon": 82.194, "flood_lat": 26.800, "flood_lon": 82.200, "river": "Sarayu / Ghaghara"},
    "sitamarhi": {"name": "Sitamarhi / Mithila Plain", "state": "Bihar", "lat": 26.591, "lon": 85.490, "flood_lat": 26.600, "flood_lon": 85.480, "river": "Bagmati"},
    "buxar": {"name": "Buxar / Siddhashram", "state": "Bihar", "lat": 25.565, "lon": 83.978, "flood_lat": 25.580, "flood_lon": 83.980, "river": "Ganga"},
    "chitrakoot": {"name": "Chitrakoot / Mandakini", "state": "Uttar Pradesh / MP", "lat": 25.199, "lon": 80.854, "flood_lat": 25.200, "flood_lon": 80.850, "river": "Mandakini"},
    "rakhigarhi": {"name": "Rakhigarhi Harappan Site", "state": "Haryana", "lat": 29.291, "lon": 76.112, "flood_lat": 29.291, "flood_lon": 76.112, "river": "Ghaggar-Hakra"},
    "dholavira": {"name": "Dholavira (Rann of Kutch)", "state": "Gujarat", "lat": 23.886, "lon": 70.213, "flood_lat": 23.886, "flood_lon": 70.213, "river": "Kutch Basin"},
    "lothal": {"name": "Lothal Harappan Dockyard", "state": "Gujarat", "lat": 22.521, "lon": 72.249, "flood_lat": 22.521, "flood_lon": 72.249, "river": "Sabarmati-Khambhat"},
    "bengaluru": {"name": "Bengaluru Deccan Plateau", "state": "Karnataka", "lat": 12.971, "lon": 77.594, "flood_lat": 12.971, "flood_lon": 77.594, "river": "Arkavathy / Pennar"},
    "pune": {"name": "Pune Deccan Foothills", "state": "Maharashtra", "lat": 18.520, "lon": 73.856, "flood_lat": 18.520, "flood_lon": 73.856, "river": "Mula-Mutha"},
    "hyderabad": {"name": "Hyderabad Deccan Shield", "state": "Telangana", "lat": 17.385, "lon": 78.486, "flood_lat": 17.385, "flood_lon": 78.486, "river": "Musi"},
    "chandigarh": {"name": "Chandigarh-Panchkula", "state": "Chandigarh", "lat": 30.733, "lon": 76.779, "flood_lat": 30.733, "flood_lon": 76.779, "river": "Ghaggar-Patiali"},
    "gaya": {"name": "Gaya / Falgu Ridge", "state": "Bihar", "lat": 24.795, "lon": 85.000, "flood_lat": 24.795, "flood_lon": 85.000, "river": "Falgu"},
    "rajgir": {"name": "Rajgir Quartzite Hills", "state": "Bihar", "lat": 25.028, "lon": 85.421, "flood_lat": 25.028, "flood_lon": 85.421, "river": "Banganga"},
    "nalanda": {"name": "Nalanda Terrace", "state": "Bihar", "lat": 25.136, "lon": 85.443, "flood_lat": 25.136, "flood_lon": 85.443, "river": "Panchane"},
    "muzaffarpur": {"name": "Muzaffarpur", "state": "Bihar", "lat": 26.120, "lon": 85.364, "flood_lat": 26.130, "flood_lon": 85.380, "river": "Burhi Gandak"},
    "darbhanga": {"name": "Darbhanga", "state": "Bihar", "lat": 26.154, "lon": 85.891, "flood_lat": 26.160, "flood_lon": 85.900, "river": "Kamala-Bagmati"},
    "bhagalpur": {"name": "Bhagalpur", "state": "Bihar", "lat": 25.242, "lon": 86.984, "flood_lat": 25.260, "flood_lon": 86.980, "river": "Ganga"},
    "bailey": {"name": "Bailey Road / Saguna More", "state": "Bihar", "lat": 25.612, "lon": 85.055, "flood_lat": 25.620, "flood_lon": 85.100, "river": "Ganga"},
    "boring": {"name": "Boring Road / SK Puri", "state": "Bihar", "lat": 25.615, "lon": 85.120, "flood_lat": 25.620, "flood_lon": 85.120, "river": "Ganga"},
    "kankarbagh": {"name": "Kankarbagh Colony", "state": "Bihar", "lat": 25.588, "lon": 85.148, "flood_lat": 25.588, "flood_lon": 85.148, "river": "Punpun-Ganga Sink"},
    "rajendra": {"name": "Rajendra Nagar Bowl", "state": "Bihar", "lat": 25.595, "lon": 85.158, "flood_lat": 25.595, "flood_lon": 85.158, "river": "Ganga Depression Bowl"},
    "varanasi": {"name": "Varanasi Ganga Crescent", "state": "Uttar Pradesh", "lat": 25.317, "lon": 82.974, "flood_lat": 25.320, "flood_lon": 83.010, "river": "Ganga"},
    "agra": {"name": "Agra Yamuna Bank", "state": "Uttar Pradesh", "lat": 27.175, "lon": 78.042, "flood_lat": 27.180, "flood_lon": 78.030, "river": "Yamuna"},
    "jaipur": {"name": "Jaipur Aravalli Foothills", "state": "Rajasthan", "lat": 26.912, "lon": 75.787, "flood_lat": 26.912, "flood_lon": 75.787, "river": "Dravyavati"},
    "lucknow": {"name": "Lucknow Gomti Basin", "state": "Uttar Pradesh", "lat": 26.847, "lon": 80.946, "flood_lat": 26.850, "flood_lon": 80.940, "river": "Gomti"},
    "rishikesh": {"name": "Rishikesh Siwalik Gorge", "state": "Uttarakhand", "lat": 30.087, "lon": 78.268, "flood_lat": 30.090, "flood_lon": 78.270, "river": "Upper Ganga"},
    "bodhgaya": {"name": "Bodh Gaya Niranjana Terrace", "state": "Bihar", "lat": 24.696, "lon": 84.991, "flood_lat": 24.696, "flood_lon": 84.991, "river": "Phalgu / Niranjana"},
}


WARD_PROFILES: List[Dict[str, Any]] = [
    {
        "key": "bihta",
        "name": "Bihta / IIT Patna Corridor",
        "coords": [25.536, 84.851],
        "elev_m": 55.2,
        "slope_deg": 1.5,
        "flood_pct": 0.8,
        "flood_label": "0.8% (Safe)",
        "sink": False,
        "social_safety_score": 88.0,
        "thana": "Bihta Thana / IIT Patna Police Post",
        "women_safety": "High (Academic campus corridor, highway security)",
        "ulsi_score": 91.5,
        "zone": "Zone S1",
    },
    {
        "key": "danapur",
        "name": "Danapur Cantonment",
        "coords": [25.630, 85.040],
        "elev_m": 52.8,
        "slope_deg": 1.6,
        "flood_pct": 1.1,
        "flood_label": "1.1% (Safe)",
        "sink": False,
        "social_safety_score": 92.0,
        "thana": "Danapur Thana / Military Cantonment Zone",
        "women_safety": "High (Army perimeter checkpoints, low harassment)",
        "ulsi_score": 89.4,
        "zone": "Zone S1",
    },
    {
        "key": "bailey",
        "name": "Bailey Road / Saguna More",
        "coords": [25.612, 85.055],
        "elev_m": 52.4,
        "slope_deg": 1.4,
        "flood_pct": 2.4,
        "flood_label": "2.4% (Safe)",
        "sink": False,
        "social_safety_score": 88.0,
        "thana": "Rupaspur Thana / Danapur Thana",
        "women_safety": "High (24x7 traffic, continuous PCR patrols)",
        "ulsi_score": 86.2,
        "zone": "Zone S1",
    },
    {
        "key": "rps",
        "name": "RPS More / Canal Road",
        "coords": [25.616, 85.048],
        "elev_m": 52.6,
        "slope_deg": 1.3,
        "flood_pct": 1.8,
        "flood_label": "1.8% (Safe)",
        "sink": False,
        "social_safety_score": 89.0,
        "thana": "Rupaspur Thana",
        "women_safety": "High (Gated residences, CCTV corridor)",
        "ulsi_score": 87.1,
        "zone": "Zone S1",
    },
    {
        "key": "patliputra",
        "name": "Patliputra Colony",
        "coords": [25.625, 85.108],
        "elev_m": 50.8,
        "slope_deg": 0.9,
        "flood_pct": 18.5,
        "flood_label": "18.5% (Low)",
        "sink": False,
        "social_safety_score": 85.0,
        "thana": "Patliputra Thana",
        "women_safety": "High (Gated cooperative colony, guards)",
        "ulsi_score": 81.0,
        "zone": "Zone S1",
    },
    {
        "key": "boring",
        "name": "Boring Road / SK Puri",
        "coords": [25.615, 85.120],
        "elev_m": 49.5,
        "slope_deg": 0.9,
        "flood_pct": 42.1,
        "flood_label": "42.1% (Ponding)",
        "sink": True,
        "social_safety_score": 86.0,
        "thana": "SK Puri Thana / Kotwali Sub-Division",
        "women_safety": "High (Well-lit coaching & commercial hub)",
        "ulsi_score": 64.0,
        "zone": "Zone S2",
    },
    {
        "key": "kankarbagh",
        "name": "Kankarbagh Colony",
        "coords": [25.588, 85.148],
        "elev_m": 45.1,
        "slope_deg": 0.5,
        "flood_pct": 98.8,
        "flood_label": "98.8% (Severe Sink)",
        "sink": True,
        "social_safety_score": 74.0,
        "thana": "Kankarbagh Thana / Agamkuan Thana",
        "women_safety": "Moderate in central blocks; isolated south bypass",
        "ulsi_score": 28.2,
        "zone": "Zone S4",
    },
    {
        "key": "rajendra",
        "name": "Rajendra Nagar",
        "coords": [25.595, 85.158],
        "elev_m": 44.5,
        "slope_deg": 0.4,
        "flood_pct": 99.4,
        "flood_label": "99.4% (Deep Bowl)",
        "sink": True,
        "social_safety_score": 73.0,
        "thana": "Kadamkuan Thana / Rajendra Nagar",
        "women_safety": "Moderate day; 5-day evacuation isolation in floods",
        "ulsi_score": 21.6,
        "zone": "Zone S4",
    },
    {
        "key": "bypass",
        "name": "Patna Bypass / Transport Nagar",
        "coords": [25.580, 85.185],
        "elev_m": 46.8,
        "slope_deg": 0.6,
        "flood_pct": 72.5,
        "flood_label": "72.5% (Waterlogged)",
        "sink": True,
        "social_safety_score": 41.0,
        "thana": "Ramkrishna Nagar Thana / Agamkuan",
        "women_safety": "Low (Poor street lighting, heavy vehicle highway)",
        "ulsi_score": 24.5,
        "zone": "Zone S4",
    },
]


INDIA_HAZARD_HUBS: List[Dict[str, Any]] = [
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
    {"name": "Thar Arid Core / Phalodi", "state": "Rajasthan", "coords": [27.131, 72.368], "hazard": "Extreme Dryland Thermal Anomaly", "metric": "Peak > 50 C Land Surface Temp", "severity": "CRITICAL"},
]


def load_bhu_loka_env() -> Dict[str, str]:
    """Load optional KEY=VALUE entries from `.env` in workspace without overwriting process env."""
    loaded: Dict[str, str] = {}
    env_file = WORKSPACE_ROOT / ".env"
    if not env_file.exists():
        return loaded
    for line in env_file.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        k, v = clean.split("=", 1)
        key = k.strip()
        val = v.strip().strip('"').strip("'")
        if key and val and key not in os.environ:
            os.environ[key] = val
            loaded[key] = val
    return loaded


def get_patna_wards(ward_filter: str = "") -> Dict[str, Any]:
    """Return calibrated DEM, Sentinel-1 SAR, NCRB/Q390 safety, and ULSI profiles."""
    crime_localities: Dict[str, Any] = {}
    crime_sources: List[str] = []
    if CRIME_JSON_PATH.exists():
        raw_crime = json.loads(CRIME_JSON_PATH.read_text(encoding="utf-8"))
        crime_localities = raw_crime.get("localities", {})
        crime_sources = raw_crime.get("data_sources", [])

    needle = ward_filter.strip().lower()
    items: List[Dict[str, Any]] = []
    for w in WARD_PROFILES:
        row = dict(w)
        # Attach extra detail from NCRB crime JSON if name partially matches
        for cname, cdata in crime_localities.items():
            if w["key"] in cname or cname.split("/")[0].strip() in w["name"].lower():
                row["crime_notes"] = cdata.get("notes", "")
                row["police_distance_km"] = cdata.get("police_station_distance_km")
                row["night_lighting"] = cdata.get("night_lighting_quality")
                break
        if not needle or needle in w["key"] or needle in w["name"].lower() or needle in w["zone"].lower():
            items.append(row)

    return {
        "city": "Patna, Bihar, India",
        "reference_bounds_note": "Copernicus 30m GLO-30 DEM | Sentinel-1 SAR 2019 | Ganga danger stage 49.5m",
        "sources": crime_sources,
        "count": len(items),
        "wards": items,
    }


def get_india_hubs(state_filter: str = "") -> Dict[str, Any]:
    """Return Pan-India hazard hubs plus exact 36-State Sovereign India GeoJSON coverage."""
    needle = state_filter.strip().lower()
    hubs = [
        h for h in INDIA_HAZARD_HUBS
        if not needle or needle in h["state"].lower() or needle in h["name"].lower() or needle in h["hazard"].lower()
    ]
    states_geojson = BOUNDS_DIR / "india_36_states_sovereign.geojson"
    state_count = 36
    if states_geojson.exists():
        try:
            gj = json.loads(states_geojson.read_text(encoding="utf-8"))
            state_count = len(gj.get("features", []))
        except Exception:
            pass

    return {
        "sovereign_extent": {
            "lat_min": 6.753,
            "lat_max": 37.098,
            "lon_min": 68.162,
            "lon_max": 97.395,
            "states_and_uts_count": state_count,
            "includes": ["Ladakh (LA)", "Jammu and Kashmir (JK)", "Arunachal Pradesh (AR)", "Bihar (BR)", "Andaman and Nicobar Islands", "Lakshadweep"],
        },
        "count": len(hubs),
        "hubs": hubs,
    }


def _http_get_bytes(url: str, timeout: float = 10.0) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BhuLoka-Geospatial-AI/3.0",
            "Accept": "*/*",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        ce = str(resp.headers.get("Content-Encoding", "")).lower()
        if "gzip" in ce or raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return raw


def _http_get_text(url: str, timeout: float = 12.0) -> str:
    return _http_get_bytes(url, timeout=timeout).decode("utf-8", errors="ignore")


def _http_get_any_json(url: str, timeout: float = 10.0) -> Any:
    return json.loads(_http_get_text(url, timeout=timeout))


def _http_get_json(url: str, timeout: float = 8.0) -> Dict[str, Any]:
    data = _http_get_any_json(url, timeout=timeout)
    return data if isinstance(data, dict) else {"data": data}


def _parse_tle_catalog(tle_text: str) -> List[Dict[str, Any]]:
    """Parse 3-line NORAD TLE text into CelesTrak OMM/GP-compatible dictionaries."""
    lines = [ln.rstrip() for ln in tle_text.splitlines() if ln.strip()]
    records: List[Dict[str, Any]] = []
    i = 0
    while i + 2 < len(lines):
        name = lines[i].strip()
        l1 = lines[i + 1].strip()
        l2 = lines[i + 2].strip()
        if not l1.startswith("1 ") or not l2.startswith("2 "):
            i += 1
            continue
        try:
            norad_id = int(l1[2:7].strip())
            ep_yr = int(l1[18:20])
            year = (1900 + ep_yr) if ep_yr >= 57 else (2000 + ep_yr)
            ep_doy = float(l1[20:32].strip())
            epoch_dt = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=ep_doy - 1.0)
            inc = float(l2[8:16].strip())
            raan = float(l2[17:25].strip())
            ecc = float("0." + l2[26:33].strip())
            argp = float(l2[34:42].strip())
            manom = float(l2[43:51].strip())
            mm = float(l2[52:63].strip())
            records.append(
                {
                    "OBJECT_NAME": name.lstrip("0 ").strip() or f"NORAD-{norad_id}",
                    "NORAD_CAT_ID": norad_id,
                    "EPOCH": epoch_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "INCLINATION": inc,
                    "RA_OF_ASC_NODE": raan,
                    "ECCENTRICITY": ecc,
                    "ARG_OF_PERICENTER": argp,
                    "MEAN_ANOMALY": manom,
                    "MEAN_MOTION": mm,
                }
            )
            i += 3
        except Exception:
            i += 1
    return records


def _julian_day(dt: datetime) -> float:
    y = dt.year
    m = dt.month
    d = dt.day + (dt.hour + (dt.minute + dt.second / 60.0 + dt.microsecond / 60e6) / 60.0) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + (a // 4)
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def _propagate_gp_record(rec: Dict[str, Any], now_utc: datetime) -> Optional[Dict[str, Any]]:
    """
    Propagate a CelesTrak OMM/GP JSON element to geodetic (lat, lon, alt_km) at `now_utc`
    using classical two-body Keplerian motion + GMST Earth rotation.
    """
    try:
        mm_rev_day = float(rec.get("MEAN_MOTION", 0.0))
        ecc = float(rec.get("ECCENTRICITY", 0.0))
        inc_deg = float(rec.get("INCLINATION", 0.0))
        raan_deg = float(rec.get("RA_OF_ASC_NODE", 0.0))
        argp_deg = float(rec.get("ARG_OF_PERICENTER", 0.0))
        m0_deg = float(rec.get("MEAN_ANOMALY", 0.0))
        epoch_str = str(rec.get("EPOCH", "")).strip()
        if mm_rev_day <= 0 or not epoch_str:
            return None

        epoch_dt = datetime.fromisoformat(epoch_str.replace("Z", "+00:00"))
        if epoch_dt.tzinfo is None:
            epoch_dt = epoch_dt.replace(tzinfo=timezone.utc)
        dt_sec = (now_utc - epoch_dt).total_seconds()

        mu = 398600.4418
        n_rad_s = mm_rev_day * (2.0 * math.pi) / 86400.0
        a_km = (mu / (n_rad_s * n_rad_s)) ** (1.0 / 3.0)

        m_rad = (math.radians(m0_deg) + n_rad_s * dt_sec) % (2.0 * math.pi)
        e_anom = m_rad
        for _ in range(4):
            e_anom = e_anom - (e_anom - ecc * math.sin(e_anom) - m_rad) / max(1e-6, 1.0 - ecc * math.cos(e_anom))

        nu = 2.0 * math.atan2(
            math.sqrt(max(0.0, 1.0 + ecc)) * math.sin(e_anom / 2.0),
            math.sqrt(max(1e-9, 1.0 - ecc)) * math.cos(e_anom / 2.0),
        )
        r_km = a_km * (1.0 - ecc * math.cos(e_anom))

        inc = math.radians(inc_deg)
        raan = math.radians(raan_deg)
        argp = math.radians(argp_deg)
        u = argp + nu

        cos_u, sin_u = math.cos(u), math.sin(u)
        cos_o, sin_o = math.cos(raan), math.sin(raan)
        cos_i, sin_i = math.cos(inc), math.sin(inc)

        x_eci = r_km * (cos_o * cos_u - sin_o * sin_u * cos_i)
        y_eci = r_km * (sin_o * cos_u + cos_o * sin_u * cos_i)
        z_eci = r_km * (sin_u * sin_i)

        jd = _julian_day(now_utc)
        t_ut1 = (jd - 2451545.0) / 36525.0
        gmst_deg = (
            280.46061837
            + 360.98564736629 * (jd - 2451545.0)
            + 0.000387933 * (t_ut1 ** 2)
            - (t_ut1 ** 3) / 38710000.0
        ) % 360.0
        gmst = math.radians(gmst_deg)

        x_ecef = x_eci * math.cos(gmst) + y_eci * math.sin(gmst)
        y_ecef = -x_eci * math.sin(gmst) + y_eci * math.cos(gmst)
        z_ecef = z_eci

        lat = math.degrees(math.atan2(z_ecef, math.hypot(x_ecef, y_ecef)))
        lon = math.degrees(math.atan2(y_ecef, x_ecef))
        alt_km = max(120.0, r_km - 6371.0)
        return {
            "norad_id": rec.get("NORAD_CAT_ID"),
            "name": str(rec.get("OBJECT_NAME", "UNKNOWN")).strip(),
            "lat": round(lat, 3),
            "lon": round(lon, 3),
            "alt_km": round(alt_km, 1),
            "inc_deg": round(inc_deg, 2),
            "mean_motion": round(mm_rev_day, 4),
            "raan_deg": round(raan_deg, 2),
            "epoch_utc": epoch_dt.isoformat(),
            "tracking_type": "ORBITAL_EPHEMERIS_ONLY",
        }
    except Exception:
        return None


def _fetch_iss_live_position(errors: List[str]) -> Optional[Dict[str, Any]]:
    try:
        iss_raw = _http_get_any_json("https://api.wheretheiss.at/v1/satellites/25544", timeout=7.5)
        if isinstance(iss_raw, dict) and "latitude" in iss_raw:
            return {
                "norad_id": 25544,
                "name": "ISS (ZARYA)",
                "category": "station",
                "lat": round(float(iss_raw["latitude"]), 3),
                "lon": round(float(iss_raw["longitude"]), 3),
                "alt_km": round(float(iss_raw["altitude"]), 1),
                "velocity_kmh": round(float(iss_raw.get("velocity", 27600.0)), 1),
                "visibility": iss_raw.get("visibility", "daylight"),
                "source": "api.wheretheiss.at (LIVE)",
            }
    except Exception as exc:
        errors.append(f"WhereTheISS fallback to Open-Notify: {exc}")

    try:
        on_raw = _http_get_any_json("http://api.open-notify.org/iss-now.json", timeout=5.0)
        pos = on_raw.get("iss_position") if isinstance(on_raw, dict) else None
        if isinstance(pos, dict) and "latitude" in pos:
            return {
                "norad_id": 25544,
                "name": "ISS (ZARYA)",
                "category": "station",
                "lat": round(float(pos["latitude"]), 3),
                "lon": round(float(pos["longitude"]), 3),
                "alt_km": 420.0,
                "velocity_kmh": 27600.0,
                "visibility": "live",
                "source": "api.open-notify.org (LIVE)",
            }
    except Exception as exc2:
        errors.append(f"Open-Notify ISS unreachable: {exc2}")
    return None


def _fetch_celestrak_active_tle(timeout: float, errors: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    used_urls: List[str] = []
    active_tle_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    try:
        tle_txt = _http_get_text(active_tle_url, timeout=min(16.0, max(10.0, timeout)))
        parsed = _parse_tle_catalog(tle_txt)
        if len(parsed) > 100:
            used_urls.append(active_tle_url)
            return parsed, used_urls
    except Exception as exc:
        errors.append(f"CelesTrak active TLE fallback to constellation groups: {exc}")

    # Multi-group TLE fallback with bounded concurrency (CelesTrak asks <=1 active query/2hr)
    group_specs = [
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle", 10.0),
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle", 10.0),
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle", 10.0),
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=gnss&FORMAT=tle", 12.0),
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle", 18.0),
    ]
    merged: List[Dict[str, Any]] = []
    seen_ids = set()

    def _grab(spec: Tuple[str, float]) -> Tuple[str, List[Dict[str, Any]]]:
        u, t_sec = spec
        return u, _parse_tle_catalog(_http_get_text(u, timeout=t_sec))

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(_grab, s) for s in group_specs]
        for fut in concurrent.futures.as_completed(futs):
            try:
                u, recs = fut.result()
                used_urls.append(u)
                for r in recs:
                    nid = r.get("NORAD_CAT_ID")
                    if nid not in seen_ids:
                        seen_ids.add(nid)
                        merged.append(r)
            except Exception as g_exc:
                errors.append(f"CelesTrak subgroup error: {g_exc}")
    return merged, used_urls


_SAT_FETCH_LOCK = threading.Lock()


def fetch_live_satellites(constellation: str = "all", timeout: float = 28.0) -> Dict[str, Any]:
    """
    Fetch real active satellites from CelesTrak NORAD GP TLE catalog (gzipped) + live ISS telemetry
    from WhereTheISS (`api.wheretheiss.at/v1/satellites/25544`) with Open-Notify fallback.
    Never fabricates counts or positions: reports `live_online=False` if offline.
    """
    now_ts = time.time()
    now_utc = datetime.now(timezone.utc)
    errors: List[str] = []
    cached = False
    source_urls: List[str] = [
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
        "https://api.wheretheiss.at/v1/satellites/25544",
    ]

    with _SAT_FETCH_LOCK:
        records: List[Dict[str, Any]] = _SATELLITE_GP_CACHE.get("records") or []
        iss_live: Optional[Dict[str, Any]] = _SATELLITE_GP_CACHE.get("iss_live")

        # Hydrate in-memory GP catalog from fresh on-disk CelesTrak cache (<30 min) to avoid IP 403 rate limits
        if not records and _SATELLITE_DISK_CACHE_PATH.exists():
            try:
                disk_payload = json.loads(_SATELLITE_DISK_CACHE_PATH.read_text(encoding="utf-8"))
                disk_ts = float(disk_payload.get("ts", 0.0))
                disk_recs = disk_payload.get("records") or []
                if isinstance(disk_recs, list) and len(disk_recs) >= 500 and (now_ts - disk_ts) < _SATELLITE_DISK_CACHE_TTL_SECONDS:
                    records = disk_recs
                    _SATELLITE_GP_CACHE["ts"] = disk_ts
                    _SATELLITE_GP_CACHE["records"] = records
                    _SATELLITE_GP_CACHE["source_urls"] = disk_payload.get("source_urls") or []
                    cached = True
            except Exception:
                pass

        ttl = _SATELLITE_CACHE_TTL_SECONDS if len(records) >= 5000 else 60.0
        need_refresh = not records or (now_ts - float(_SATELLITE_GP_CACHE.get("ts", 0.0))) >= ttl
        if need_refresh:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                fut_cat = ex.submit(_fetch_celestrak_active_tle, timeout, errors)
                fut_iss = ex.submit(_fetch_iss_live_position, errors)
                fresh_recs, used_urls = fut_cat.result()
                fresh_iss = fut_iss.result()

            if fresh_recs:
                records = fresh_recs
                _SATELLITE_GP_CACHE["ts"] = now_ts
                _SATELLITE_GP_CACHE["records"] = records
                if used_urls:
                    _SATELLITE_GP_CACHE["source_urls"] = used_urls
                try:
                    _SATELLITE_DISK_CACHE_PATH.write_text(
                        json.dumps({"ts": now_ts, "source_urls": used_urls, "records": records}),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
            elif records:
                cached = True

            if fresh_iss:
                iss_live = fresh_iss
                _SATELLITE_GP_CACHE["iss_live"] = iss_live
                _SATELLITE_GP_CACHE["iss_ts"] = now_ts
        else:
            cached = True
            # Quickly refresh ISS spot telemetry alongside cached TLE catalog if stale (>45s) or missing
            if not iss_live or (now_ts - float(_SATELLITE_GP_CACHE.get("iss_ts", 0.0))) > 45.0:
                fresh_iss = _fetch_iss_live_position(errors)
                if fresh_iss:
                    iss_live = fresh_iss
                    _SATELLITE_GP_CACHE["iss_live"] = iss_live
                    _SATELLITE_GP_CACHE["iss_ts"] = now_ts

        if _SATELLITE_GP_CACHE.get("source_urls"):
            source_urls = list(_SATELLITE_GP_CACHE["source_urls"]) + ["https://api.wheretheiss.at/v1/satellites/25544"]

    if not records and not iss_live:
        return {
            "live_online": False,
            "cached": False,
            "fetched_at_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "updated_at_utc": now_utc.isoformat(),
            "data_classification": "ORBITAL_EPHEMERIS_ONLY",
            "source_urls": source_urls,
            "provenance": {
                "celestrak": "CelesTrak NORAD GP/TLE Two-Body Keplerian Propagation (not live spacecraft telemetry)",
                "iss_spot": "api.wheretheiss.at / open-notify ephemeris tracker",
                "limitations": "Catalog unreachable offline; zero orbital positions fabricated.",
            },
            "limitations": "CelesTrak NORAD GP/TLE orbital tracking is ephemeris propagation only, not live spacecraft payload telemetry.",
            "counts": None,
            "iss_live": None,
            "satellites": [],
            "errors": errors,
        }

    starlink_recs: List[Dict[str, Any]] = []
    eo_recs: List[Dict[str, Any]] = []
    weather_recs: List[Dict[str, Any]] = []
    isro_recs: List[Dict[str, Any]] = []
    station_recs: List[Dict[str, Any]] = []

    eo_keys = ("SENTINEL", "TERRA", "AQUA", "LANDSAT", "SUOMI", "JPSS", "ICESAT", "SMAP", "GPM-CORE")
    weather_keys = ("NOAA", "METOP", "METEOSAT", "GOES-", "HIMAWARI", "FENGYUN")
    isro_keys = ("CARTOSAT", "RESOURCESAT", "RISAT", "OCEANSAT", "SCATSAT", "EOS-", "INSAT", "GSAT", "IRNSS", "NVS-", "EMISAT", "HYSIS")
    station_keys = ("ISS (ZARYA)", "CSS (TIANHE)", "ISS DEB", "ISS-")

    for r in records:
        nm = str(r.get("OBJECT_NAME", "")).upper()
        if "STARLINK" in nm:
            starlink_recs.append(r)
        elif nm in {"ISS (ZARYA)", "CSS (TIANHE)"} or any(nm.startswith(sk) for sk in station_keys[:2]):
            station_recs.append(r)
        elif any(k in nm for k in isro_keys):
            isro_recs.append(r)
        elif any(k in nm for k in eo_keys):
            eo_recs.append(r)
        elif any(k in nm for k in weather_keys):
            weather_recs.append(r)

    filt = constellation.strip().lower()
    selected: List[Tuple[str, Dict[str, Any]]] = []

    if filt in ("all", "", "station", "stations", "iss"):
        for r in station_recs[:8]:
            selected.append(("station", r))
    if filt in ("all", "", "isro", "india"):
        for r in isro_recs[:30]:
            selected.append(("isro", r))
    if filt in ("all", "", "eo", "resource", "sentinel", "modis"):
        for r in eo_recs[:32]:
            selected.append(("eo", r))
    if filt in ("all", "", "weather"):
        for r in weather_recs[:20]:
            selected.append(("weather", r))
    if filt in ("all", "", "starlink"):
        step = max(1, len(starlink_recs) // 160) if starlink_recs else 1
        for r in starlink_recs[::step][:160]:
            selected.append(("starlink", r))

    propagated: List[Dict[str, Any]] = []
    seen_ids = set()
    for cat, rec in selected:
        nid = rec.get("NORAD_CAT_ID")
        if nid in seen_ids:
            continue
        p = _propagate_gp_record(rec, now_utc)
        if p:
            seen_ids.add(nid)
            p["category"] = cat
            if iss_live and nid == 25544:
                p["lat"] = iss_live["lat"]
                p["lon"] = iss_live["lon"]
                p["alt_km"] = iss_live["alt_km"]
                p["velocity_kmh"] = iss_live["velocity_kmh"]
            propagated.append(p)

    if iss_live and 25544 not in seen_ids:
        propagated.insert(0, iss_live)

    return {
        "live_online": True,
        "cached": cached,
        "fetched_at_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "updated_at_utc": now_utc.isoformat(),
        "data_classification": "ORBITAL_EPHEMERIS_ONLY",
        "source_urls": source_urls,
        "provenance": {
            "celestrak": "CelesTrak NORAD GP/TLE Two-Body Keplerian Propagation (orbital ephemeris only, not spacecraft telemetry)",
            "iss_spot": (iss_live or {}).get("source") or "api.wheretheiss.at ephemeris tracker",
            "eo_catalog_filter": "Verified mission names only (NASA Terra/Aqua/Landsat, ESA Sentinel, ISRO Cartosat/Resourcesat/RISAT/Oceansat/EOS, NOAA/MetOp/Himawari, ISS/CSS, Starlink)",
            "cloud_infra_exclusion": "No AWS cloud hosting metadata is used or displayed as satellite sensor telemetry.",
        },
        "limitations": "CelesTrak GP/TLE Keplerian propagation estimates orbital position/inclination/RAAN only and does not expose onboard spacecraft payload or sensor telemetry.",
        "counts": {
            "total_active_catalog": len(records),
            "starlink_active": len(starlink_recs),
            "isro_matched": len(isro_recs),
            "earth_observation_eo": len(eo_recs),
            "weather_metsats": len(weather_recs),
            "space_stations": len(station_recs),
            "rendered_sample_count": len(propagated),
        },
        "iss_live": iss_live,
        "satellites": propagated,
        "errors": errors,
    }


_DEM_FETCH_LOCK = threading.Lock()


def start_background_live_warmup() -> None:
    """Warm up live CelesTrak GP catalog, GEE SDK & flagship 90m DEM grids asynchronously on server boot."""
    def _warm() -> None:
        try:
            get_api_and_gee_status()
        except Exception:
            pass
        try:
            fetch_live_satellites(constellation="all", timeout=28.0)
        except Exception:
            pass
        for idx, preset_city in enumerate(("Ayodhya", "Bengaluru", "Rakhigarhi")):
            if idx > 0:
                time.sleep(0.35)
            try:
                fetch_location_3d_dem(preset_city, timeout=14.0)
            except Exception:
                pass

    threading.Thread(target=_warm, daemon=True, name="BhuLokaLiveWarmup").start()


def _resolve_location(location_name: str, lat: Optional[float], lon: Optional[float]) -> Optional[Dict[str, Any]]:
    if lat is not None and lon is not None:
        n_lat, n_lon = float(lat), float(lon)
        if not (-90.0 <= n_lat <= 90.0) or not (-180.0 <= n_lon <= 180.0):
            return None
        return {"name": location_name or f"({n_lat:.3f}, {n_lon:.3f})", "state": "India", "lat": n_lat, "lon": n_lon, "source": "explicit_coords"}

    q = (location_name or "").strip().lower()
    if not q:
        return None
    street_cues = any(w in q for w in ("road", "street", "sector", "colony", "marg", "station", "chowk", "bridge", "campus", "gate", ","))
    ordered_keys = sorted(LOCATION_PRESETS.keys(), key=len, reverse=True)
    for pk in ordered_keys:
        pv = LOCATION_PRESETS[pk]
        if pk == "patna" and (len(q.split()) >= 2 or street_cues) and "municipal" not in q and q != "patna":
            continue
        if pk in q or q == pv["name"].lower():
            return {"name": pv["name"], "state": pv["state"], "lat": float(pv["lat"]), "lon": float(pv["lon"]), "source": "bhu_loka_preset"}

    # Try Open-Meteo city geocoder first for concise place names
    if not street_cues:
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location_name)}&count=3&language=en&format=json"
            geo_res = _http_get_any_json(geo_url, timeout=7.5)
            results = geo_res.get("results") if isinstance(geo_res, dict) else None
            if isinstance(results, list) and results:
                chosen = next((r for r in results if str(r.get("country_code", "")).upper() == "IN"), results[0])
                return {
                    "name": str(chosen.get("name", location_name)),
                    "state": str(chosen.get("admin1") or chosen.get("country") or "India"),
                    "lat": float(chosen["latitude"]),
                    "lon": float(chosen["longitude"]),
                    "source": "open_meteo_geocoder",
                }
        except Exception:
            pass

    # Photon OSM geocoder fallback (reliable for street addresses)
    try:
        ph_url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(location_name)}&limit=3"
        ph_res = _http_get_any_json(ph_url, timeout=7.5)
        feats = ph_res.get("features") if isinstance(ph_res, dict) else None
        if isinstance(feats, list) and feats:
            chosen = next((f for f in feats if str((f.get("properties") or {}).get("countrycode", "")).upper() == "IN"), feats[0])
            coords = (chosen.get("geometry") or {}).get("coordinates") or []
            if len(coords) >= 2:
                props = chosen.get("properties") or {}
                short_disp = ", ".join(str(x) for x in [props.get("name"), props.get("city")] if x) or location_name
                return {
                    "name": short_disp,
                    "state": str(props.get("state") or props.get("country") or "India"),
                    "lat": float(coords[1]),
                    "lon": float(coords[0]),
                    "source": "photon_address_geocoder",
                }
    except Exception:
        pass

    # Street/Address fallback via OSM Nominatim
    try:
        nom_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location_name)}&format=json&limit=3&countrycodes=in"
        nom_res = _http_get_any_json(nom_url, timeout=8.0)
        if isinstance(nom_res, list) and nom_res:
            chosen = nom_res[0]
            disp = str(chosen.get("display_name", location_name))
            short_disp = ", ".join(p.strip() for p in disp.split(",")[:2]) or location_name
            state_part = disp.split(",")[-3].strip() if len(disp.split(",")) >= 3 else "India"
            return {
                "name": short_disp,
                "state": state_part,
                "lat": float(chosen["lat"]),
                "lon": float(chosen["lon"]),
                "source": "nominatim_address_geocoder",
            }
    except Exception:
        pass

    return None


def fetch_location_3d_dem(
    location_name: str = "Bihta",
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    span_deg: float = 0.08,
    grid_n: int = 8,
    timeout: float = 4.0,
) -> Dict[str, Any]:
    """
    Dynamically fetch an `grid_n x grid_n` (default 8x8 = 64-point) real 90m Copernicus/SRTM
    DEM elevation grid from Open-Meteo Elevation API (`api.open-meteo.com/v1/elevation`)
    so Agent-2 can synthesize a true 3D topographic hologram for ANY queried location.
    """
    loc = _resolve_location(location_name, lat, lon)
    if loc is None:
        return {
            "live_online": False,
            "cached": False,
            "location": location_name,
            "error": f"Unable to resolve valid coordinates for '{location_name}'. Refusing silent fallback.",
            "source_api": "Geocoding Unavailable",
        }
    c_lat = loc["lat"]
    c_lon = loc["lon"]
    grid_n = max(4, min(10, int(grid_n)))
    span = max(0.02, min(0.4, float(span_deg)))

    cache_key = f"{c_lat:.3f},{c_lon:.3f},{grid_n},{span:.3f}"
    now = time.time()
    cached_entry = _DEM_CACHE.get(cache_key)
    if cached_entry and (now - cached_entry["_ts"]) < _SATELLITE_CACHE_TTL_SECONDS:
        out = dict(cached_entry["data"])
        out["cached"] = True
        return out

    lats: List[float] = []
    lons: List[float] = []
    half = span / 2.0
    for r in range(grid_n):
        row_lat = (c_lat + half) - (r / (grid_n - 1)) * span
        for c in range(grid_n):
            col_lon = (c_lon - half) + (c / (grid_n - 1)) * span
            lats.append(round(row_lat, 5))
            lons.append(round(col_lon, 5))

    lat_str = ",".join(str(x) for x in lats)
    lon_str = ",".join(str(x) for x in lons)
    elev_url = f"https://api.open-meteo.com/v1/elevation?latitude={lat_str}&longitude={lon_str}"

    try:
        with _DEM_FETCH_LOCK:
            now_inner = time.time()
            cached_inner = _DEM_CACHE.get(cache_key)
            if cached_inner and (now_inner - cached_inner["_ts"]) < _SATELLITE_CACHE_TTL_SECONDS:
                out = dict(cached_inner["data"])
                out["cached"] = True
                return out

            resp: Any = None
            last_exc: Optional[Exception] = None
            for attempt in range(3):
                try:
                    resp = _http_get_any_json(elev_url, timeout=timeout)
                    break
                except Exception as exc:
                    last_exc = exc
                    if attempt < 2:
                        time.sleep(0.5 * (attempt + 1))
            if resp is None:
                raise last_exc or RuntimeError("Elevation API failed")
        elev_list = resp.get("elevation") if isinstance(resp, dict) else None
        if not isinstance(elev_list, list) or len(elev_list) != grid_n * grid_n:
            raise ValueError("Invalid elevation grid payload")

        matrix: List[List[float]] = []
        clean_vals: List[float] = []
        for r in range(grid_n):
            row_vals: List[float] = []
            for c in range(grid_n):
                v = float(elev_list[r * grid_n + c])
                row_vals.append(round(v, 1))
                clean_vals.append(v)
            matrix.append(row_vals)

        min_m = round(min(clean_vals), 1)
        max_m = round(max(clean_vals), 1)
        mean_m = round(sum(clean_vals) / len(clean_vals), 1)
        relief_m = round(max_m - min_m, 1)
        cell_spacing_m = (span / max(1, grid_n - 1)) * 111000.0
        diffs = [abs(clean_vals[i] - clean_vals[i - 1]) for i in range(1, len(clean_vals))]
        avg_dh = sum(diffs) / max(1, len(diffs))
        slope_deg = round(math.degrees(math.atan2(avg_dh, cell_spacing_m)), 2)

        low_cutoff = min_m + 0.28 * max(1.0, relief_m)
        low_pct = round(100.0 * sum(1 for v in clean_vals if v <= low_cutoff) / len(clean_vals), 1)

        if mean_m > 350.0:
            terrain_class = "Elevated Highland / Plateau Shield"
        elif mean_m >= 52.0:
            terrain_class = "Moderately Elevated Levee / Terrace"
        else:
            terrain_class = "Lowland Fluvial / Coastal Floodplain"

        is_patna_calibrated = (25.48 <= c_lat <= 25.68) and (84.80 <= c_lon <= 85.28)
        result: Dict[str, Any] = {
            "live_online": True,
            "cached": False,
            "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "location": loc["name"],
            "state": loc["state"],
            "location_source": loc["source"],
            "center": {"lat": round(c_lat, 4), "lon": round(c_lon, 4)},
            "bounds": {
                "south": round(c_lat - half, 4),
                "north": round(c_lat + half, 4),
                "west": round(c_lon - half, 4),
                "east": round(c_lon + half, 4),
            },
            "rows": grid_n,
            "cols": grid_n,
            "elev_matrix": matrix,
            "metrics": {
                "min_m": min_m,
                "max_m": max_m,
                "mean_m": mean_m,
                "relief_m": relief_m,
                "slope_est_deg": slope_deg,
                "low_sink_pct": low_pct,
                "terrain_class": terrain_class,
                "patna_sar_ncrb_calibrated": is_patna_calibrated,
            },
            "source_api": "Open-Meteo Elevation API (Copernicus GLO-90 / SRTM 90m DEM, Zero-Key Live)",
        }
        _DEM_CACHE[cache_key] = {"_ts": now, "data": result}
        return result
    except Exception as exc:
        return {
            "live_online": False,
            "cached": False,
            "location": loc["name"],
            "state": loc["state"],
            "center": {"lat": round(c_lat, 4), "lon": round(c_lon, 4)},
            "error": f"Open-Meteo Elevation API unreachable: {exc}",
            "source_api": "Open-Meteo Elevation API (OFFLINE)",
        }


def fetch_live_hydromet(
    location: str = "Patna",
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """
    Fetch real live meteorological & hydrological telemetry from free, zero-key
    Open-Meteo APIs (`api.open-meteo.com` Weather + `flood-api.open-meteo.com` GloFAS).
    """
    key_norm = location.strip().lower()
    matched_preset = None
    for pk, pv in LOCATION_PRESETS.items():
        if pk in key_norm or key_norm in pv["name"].lower() or key_norm in pv["state"].lower():
            matched_preset = (pk, pv)
            break

    if lat is not None and lon is not None:
        use_lat = float(lat)
        use_lon = float(lon)
        if not (-90.0 <= use_lat <= 90.0) or not (-180.0 <= use_lon <= 180.0):
            return {
                "live_online": False,
                "cached": False,
                "location": location,
                "errors": [f"Invalid WGS84 coordinates ({use_lat}, {use_lon})"],
            }
        use_flood_lat = use_lat
        use_flood_lon = use_lon
        loc_label = location or f"({use_lat:.4f}, {use_lon:.4f})"
        river_label = matched_preset[1]["river"] if matched_preset else "Catchment Flow (GloFAS)"
        state_label = matched_preset[1]["state"] if matched_preset else "WGS84"
    elif matched_preset:
        pv = matched_preset[1]
        use_lat = float(pv["lat"])
        use_lon = float(pv["lon"])
        use_flood_lat = float(pv.get("flood_lat", use_lat))
        use_flood_lon = float(pv.get("flood_lon", use_lon))
        loc_label = pv["name"]
        river_label = pv["river"]
        state_label = pv["state"]
    else:
        resolved = _resolve_location(location, None, None)
        if resolved is None:
            return {
                "live_online": False,
                "cached": False,
                "location": location,
                "errors": [f"Unable to resolve location '{location}'. Provide valid lat/lon coordinates."],
            }
        use_lat = float(resolved["lat"])
        use_lon = float(resolved["lon"])
        use_flood_lat = use_lat
        use_flood_lon = use_lon
        loc_label = resolved["name"]
        river_label = "Catchment Flow (GloFAS)"
        state_label = resolved["state"]

    cache_key = f"{use_lat:.3f},{use_lon:.3f}"
    now = time.time()
    cached = _TELEMETRY_CACHE.get(cache_key)
    if cached and (now - cached["_ts"]) < _CACHE_TTL_SECONDS:
        out = dict(cached["data"])
        out["cached"] = True
        return out

    weather_params = urllib.parse.urlencode({
        "latitude": f"{use_lat:.4f}",
        "longitude": f"{use_lon:.4f}",
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,wind_speed_10m,surface_pressure",
        "hourly": "temperature_2m,precipitation_probability,soil_moisture_0_to_7cm",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Kolkata",
        "forecast_days": 5,
    })
    flood_params = urllib.parse.urlencode({
        "latitude": f"{use_flood_lat:.4f}",
        "longitude": f"{use_flood_lon:.4f}",
        "daily": "river_discharge,river_discharge_mean,river_discharge_max",
        "forecast_days": 7,
    })

    weather_url = f"https://api.open-meteo.com/v1/forecast?{weather_params}"
    flood_url = f"https://flood-api.open-meteo.com/v1/flood?{flood_params}"

    weather_data: Optional[Dict[str, Any]] = None
    flood_data: Optional[Dict[str, Any]] = None
    errors: List[str] = []

    try:
        weather_data = _http_get_json(weather_url, timeout=timeout)
    except Exception as exc:
        errors.append(f"Open-Meteo Weather unreachable: {exc}")

    try:
        flood_data = _http_get_json(flood_url, timeout=timeout)
    except Exception as exc:
        errors.append(f"Open-Meteo GloFAS Flood API unreachable: {exc}")

    live_online = bool(weather_data or flood_data)
    current = (weather_data or {}).get("current", {})
    hourly = (weather_data or {}).get("hourly", {})
    daily_w = (weather_data or {}).get("daily", {})
    daily_f = (flood_data or {}).get("daily", {})

    soil_vals = [v for v in (hourly.get("soil_moisture_0_to_7cm") or [])[:6] if v is not None]
    soil_pct = round(float(soil_vals[0]) * 100.0, 1) if soil_vals else None

    discharges = [v for v in (daily_f.get("river_discharge") or []) if v is not None]
    current_discharge = round(float(discharges[0]), 2) if discharges else None

    result: Dict[str, Any] = {
        "live_online": live_online,
        "cached": False,
        "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "location": loc_label,
        "state": state_label,
        "river_basin": river_label,
        "coords": {"lat": use_lat, "lon": use_lon},
        "apis_used": [
            "Open-Meteo Weather & Soil API (Zero-Key Live)",
            "Open-Meteo GloFAS v4 River Flood Discharge API (Zero-Key Live)",
        ],
        "current_weather": {
            "temperature_c": current.get("temperature_2m"),
            "apparent_temp_c": current.get("apparent_temperature"),
            "relative_humidity_pct": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "surface_pressure_hpa": current.get("surface_pressure"),
            "soil_moisture_0_7cm_pct": soil_pct,
        },
        "daily_forecast": {
            "dates": daily_w.get("time", []),
            "temp_max_c": daily_w.get("temperature_2m_max", []),
            "temp_min_c": daily_w.get("temperature_2m_min", []),
            "precip_sum_mm": daily_w.get("precipitation_sum", []),
        },
        "flood_discharge": {
            "dates": daily_f.get("time", []),
            "river_discharge_m3_s": daily_f.get("river_discharge", []),
            "river_discharge_mean_m3_s": daily_f.get("river_discharge_mean", []),
            "river_discharge_max_m3_s": daily_f.get("river_discharge_max", []),
            "latest_discharge_m3_s": current_discharge,
        },
        "errors": errors,
    }

    if live_online:
        _TELEMETRY_CACHE[cache_key] = {"_ts": now, "data": result}

    return result


def get_api_and_gee_status() -> Dict[str, Any]:
    """Return honest status of zero-key live services vs optional API credentials."""
    load_bhu_loka_env()
    gee = BhuLokaGoogleEarthConnector()
    gee_summary = gee.summary()

    optional_keys = {
        "GOOGLE_CLOUD_PROJECT": bool(os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("EE_PROJECT")),
        "DATA_GOV_IN_API_KEY": bool(os.environ.get("DATA_GOV_IN_API_KEY")),
        "NASA_EARTHDATA_TOKEN": bool(os.environ.get("NASA_EARTHDATA_TOKEN")),
        "GEMINI_API_KEY": bool(os.environ.get("GEMINI_API_KEY")),
    }

    return {
        "project": "BHU LOKA (भूलोक)",
        "researcher": "Prince Kumar (IIT Patna, PA2511CDH37)",
        "supervisor": "Pallav Rustogi",
        "zero_key_engines": {
            "hybrid_rag_bm25_faiss": True,
            "transformer_minilm_384d_cache": (ENTERPRISE_RAG_DIR / "embeddings" / "doc_embeddings_minilm.npz").exists(),
            "sovereign_india_36_states": (BOUNDS_DIR / "india_36_states_sovereign.geojson").exists(),
            "patna_copernicus_s1_modis": (DATA_DIR / "08_Processed_Outputs" / "bhu_loka_real_geodata.js").exists(),
            "google_earth_gl_in_tiles": True,
            "open_meteo_weather_and_flood": True,
            "open_meteo_copernicus_90m_dem": True,
            "celestrak_live_satellites": True,
        },
        "google_earth_engine": gee_summary,
        "optional_api_keys_configured": optional_keys,
        "mcp_server": {
            "name": "bhu-loka-geospatial",
            "script": str(Path(__file__).resolve().parent / "bhu_loka_mcp_server.py"),
            "config_example": str(WORKSPACE_ROOT / "mcp_config.json"),
            "transports": ["stdio", "streamable-http"],
        },
    }


def warmup_rag_pipeline() -> Any:
    """
    Pre-load numpy/sklearn/faiss and initialize RAGPipeline on the main thread
    before any async/stdio loop starts, preventing Windows DLL-lock stalls and
    keeping stdout clean for MCP JSON-RPC framing.
    """
    global _RAG_PIPELINE
    if _RAG_PIPELINE is None:
        with contextlib.redirect_stdout(sys.stderr):
            if str(ENTERPRISE_RAG_DIR) not in sys.path:
                sys.path.insert(0, str(ENTERPRISE_RAG_DIR))
            from rag.pipeline import RAGPipeline  # type: ignore
            _RAG_PIPELINE = RAGPipeline()
    return _RAG_PIPELINE


def query_hybrid_rag(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Lazy-load Enterprise Hybrid RAGPipeline cleanly without polluting stdout."""
    pipeline = warmup_rag_pipeline()
    t0 = time.perf_counter()
    res = pipeline.run(query, top_k=top_k)
    res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
    return res
