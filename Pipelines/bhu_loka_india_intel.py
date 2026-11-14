"""
BHU LOKA India Location, Land Records & Street Intelligence Engine v1.0
Implements:
  A. Administrative Location Explorer (28 States + 8 UTs = 36, state-varying hierarchies)
  B. Land Parcel & Plot Search (Bihar Pilot + DILRMP 36-State Handoff, strict composite scoping)
  C. Police Station Jurisdiction GIS Layer (strict non-inference of missing polygons)
  D. Street CCTV Intelligence Layer (strict 6-status taxonomy, zero fabricated streams)
  E. Local News Intelligence Layer (PIB & NDMA Sachet RSS + EN/HI classifier + geo-precision guard)
  F. Traffic Advisories, Road Closures, Diversions, Emergency Alerts, Hospitals, Fire & Disaster Layers

Zero-Fake-Data Policy: Unavailable external sources report explicit status + official fallback.
Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from bs4 import BeautifulSoup

from bhu_loka_india_db_setup import ensure_normalized_schema, get_db_path

DILRMP_DIRECTORY_URL = "https://www.dilrmp.gov.in/dilrmpold/State-RoR-Web"

ALLOWED_CCTV_STATUSES = (
    "LIVE",
    "PUBLIC LINK",
    "AUTHORIZED ACCESS REQUIRED",
    "OFFLINE",
    "UNAVAILABLE",
    "NOT VERIFIED",
)
CCTV_EMPTY_MESSAGE = "No publicly accessible CCTV feed verified for this location."

NEWS_CATEGORIES = (
    "Crime and public safety",
    "Traffic",
    "Weather",
    "Flood and disaster",
    "Government announcements",
    "Infrastructure",
    "Environment",
    "Local events",
)

OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

OFFICIAL_NEWS_FEEDS: List[Dict[str, str]] = [
    {
        "id": "ndma_sachet",
        "publisher": "NDMA Sachet (National Disaster Management Authority)",
        "url": "https://sachet.ndma.gov.in/CapFeed?type=rss",
        "language_code": "en",
        "kind": "CAP_RSS",
    },
    {
        "id": "pib_en",
        "publisher": "Press Information Bureau (PIB India)",
        "url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
        "language_code": "en",
        "kind": "PIB_RSS",
    },
    {
        "id": "pib_hi",
        "publisher": "Press Information Bureau Hindi (PIB India)",
        "url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=2&Regid=3",
        "language_code": "hi",
        "kind": "PIB_RSS",
    },
]

_OVERPASS_CACHE_TTL_SEC = 1800.0  # 30 minutes
_OVERPASS_LOCK = threading.Lock()
_OVERPASS_MIN_INTERVAL_SEC = 0.5
_OVERPASS_LAST_REQ_BY_ENDPOINT: Dict[str, float] = {}
_OVERPASS_RETRYABLE_STATUS = {429, 503}


LAYER_CATALOG: List[Dict[str, Any]] = [
    {
        "layer_id": "admin_boundaries",
        "title": "India Administrative Boundaries",
        "module": "A",
        "geometry_types": ["Polygon", "MultiPolygon"],
        "default_visible": True,
        "default_opacity": 0.72,
        "source_attribution": "GADM v4.1 / Survey of India Reference Alignment (EPSG:4326)",
        "schema": ["unit_id", "state_code", "name_en", "local_name", "level_depth", "level_label_state_specific", "stable_id"],
        "legend": [
            {"label": "State / UT Boundary", "color": "#38bdf8"},
            {"label": "Selected District", "color": "#f59e0b"},
            {"label": "Verified Level-3 Unit", "color": "#10b981"},
        ],
        "description": "Official 28 States + 8 UTs, 724 Districts, and state-varying Level-3 units filtered to active location.",
    },
    {
        "layer_id": "villages_wards",
        "title": "Villages, Gram Panchayats & ULB Wards",
        "module": "A",
        "geometry_types": ["Point", "Polygon"],
        "default_visible": False,
        "default_opacity": 0.85,
        "source_attribution": "OpenStreetMap (ODbL) Places/Admin Level 9-10 & Local Verified Register",
        "schema": ["vw_id", "name_en", "local_name", "place_type", "urban_rural_class", "hierarchy_tier", "distance_km", "source_attribution"],
        "legend": [
            {"label": "Rural Village / Gram Panchayat", "color": "#22c55e"},
            {"label": "Urban Ward / Locality", "color": "#a855f7"},
        ],
        "description": "Rural villages, hamlets, Gram Panchayats, and ULB wards within the selected analysis radius.",
    },
    {
        "layer_id": "police_jurisdictions",
        "title": "Police Station Locations & Jurisdictions",
        "module": "C",
        "geometry_types": ["Point", "Polygon"],
        "default_visible": True,
        "default_opacity": 0.90,
        "source_attribution": "Patna Police Official Register + OpenStreetMap (ODbL) amenity=police",
        "schema": [
            "station_id",
            "station_name",
            "district",
            "jurisdiction_boundary",
            "boundary_status",
            "address",
            "contact_info",
            "official_source",
            "emergency_contact_link",
            "distance_km",
        ],
        "legend": [
            {"label": "Verified Jurisdiction Polygon", "color": "#38bdf8"},
            {"label": "Police Station Point (Boundary Unavailable)", "color": "#fb7185"},
        ],
        "description": "Independent police station registry. Never infers missing jurisdiction polygons solely from nearest point.",
    },
    {
        "layer_id": "street_cctv",
        "title": "STREET CCTV",
        "module": "D",
        "geometry_types": ["Point"],
        "default_visible": True,
        "default_opacity": 0.95,
        "source_attribution": "Authorized Traffic Police & Smart City Public Camera Registry",
        "schema": [
            "camera_id",
            "camera_name",
            "latitude",
            "longitude",
            "responsible_authority",
            "source_url",
            "stream_type",
            "access_status",
            "operational_status",
            "last_verified_time",
            "distance_km",
        ],
        "legend": [
            {"label": "LIVE / PUBLIC LINK", "color": "#10b981"},
            {"label": "AUTHORIZED ACCESS REQUIRED", "color": "#f59e0b"},
            {"label": "OFFLINE / UNAVAILABLE / NOT VERIFIED", "color": "#94a3b8"},
        ],
        "description": "Verified public and agency-authorized traffic camera portal nodes. Zero fabricated streams.",
    },
    {
        "layer_id": "local_news",
        "title": "LOCAL NEWS",
        "module": "E",
        "geometry_types": ["Point"],
        "default_visible": True,
        "default_opacity": 0.92,
        "source_attribution": "NDMA Sachet RSS + Press Information Bureau (PIB) EN/HI Feeds",
        "schema": [
            "news_id",
            "headline",
            "ai_summary",
            "original_url",
            "publisher",
            "publication_time",
            "language_code",
            "location_name",
            "latitude",
            "longitude",
            "geographic_precision",
            "news_category",
            "verification_status",
            "pinned_on_map",
        ],
        "legend": [
            {"label": "Point-Verified Alert Pin", "color": "#f59e0b"},
            {"label": "District/State/National Items (List Only)", "color": "#64748b"},
        ],
        "description": "Classified EN/HI alerts and headlines. Only point-verified items are pinned to map coordinates.",
    },
    {
        "layer_id": "traffic_advisories",
        "title": "Traffic Advisories",
        "module": "F",
        "geometry_types": ["Point", "LineString"],
        "default_visible": False,
        "default_opacity": 0.85,
        "source_attribution": "OpenStreetMap Traffic Enforcement/Controls (ODbL) & Verified Agency Advisories",
        "schema": ["incident_id", "title", "road_name", "description", "distance_km", "observation_time_utc", "source_attribution"],
        "legend": [{"label": "Traffic Advisory / Control", "color": "#fbbf24"}],
        "description": "Traffic enforcement nodes, corridor advisories, and speed/control monitoring points.",
    },
    {
        "layer_id": "road_closures",
        "title": "Road Closures",
        "module": "F",
        "geometry_types": ["Point", "LineString"],
        "default_visible": False,
        "default_opacity": 0.90,
        "source_attribution": "OpenStreetMap Construction/Access Tags (ODbL) & Official Agency Advisories",
        "schema": ["incident_id", "title", "road_name", "closure_reason", "distance_km", "observation_time_utc", "source_attribution"],
        "legend": [{"label": "Closed / Under-Construction Segment", "color": "#ef4444"}],
        "description": "Active mapped road construction or access-restricted closures near the selected location.",
    },
    {
        "layer_id": "diversions",
        "title": "Traffic Diversions",
        "module": "F",
        "geometry_types": ["Point", "LineString"],
        "default_visible": False,
        "default_opacity": 0.85,
        "source_attribution": "OpenStreetMap Detour Relations (ODbL) & Official Agency Advisories",
        "schema": ["incident_id", "title", "description", "distance_km", "observation_time_utc", "source_attribution"],
        "legend": [{"label": "Mapped Traffic Detour", "color": "#f97316"}],
        "description": "Officially tagged detour and diversion corridors inside the analysis radius.",
    },
    {
        "layer_id": "emergency_alerts",
        "title": "Public Emergency Alerts",
        "module": "F",
        "geometry_types": ["Point"],
        "default_visible": True,
        "default_opacity": 0.95,
        "source_attribution": "NDMA Sachet Common Alerting Protocol (CAP) Official Feed",
        "schema": ["alert_id", "headline", "ai_summary", "news_category", "location_name", "publication_time", "original_url", "verification_status"],
        "legend": [{"label": "NDMA Sachet Emergency Alert", "color": "#f43f5e"}],
        "description": "Authoritative weather, flood, and disaster emergency alerts with verified CAP coordinates.",
    },
    {
        "layer_id": "hospitals",
        "title": "Hospitals & Trauma Centers",
        "module": "F",
        "geometry_types": ["Point"],
        "default_visible": False,
        "default_opacity": 0.90,
        "source_attribution": "OpenStreetMap (ODbL) amenity=hospital|clinic & Emergency Registry",
        "schema": ["facility_id", "name", "facility_type", "operator", "address", "contact_info", "emergency_helpline", "distance_km", "observation_time_utc"],
        "legend": [{"label": "Hospital / Medical Clinic", "color": "#10b981"}],
        "description": "Medical care institutions and clinics inside the selected analysis radius.",
    },
    {
        "layer_id": "fire_stations",
        "title": "Fire Stations",
        "module": "F",
        "geometry_types": ["Point"],
        "default_visible": False,
        "default_opacity": 0.90,
        "source_attribution": "OpenStreetMap (ODbL) amenity=fire_station & Fire Services",
        "schema": ["facility_id", "name", "facility_type", "operator", "address", "contact_info", "emergency_helpline", "distance_km", "observation_time_utc"],
        "legend": [{"label": "Fire Station", "color": "#fb7185"}],
        "description": "Verified fire brigade stations within the selected analysis radius.",
    },
    {
        "layer_id": "disaster_response",
        "title": "Disaster Response & Emergency Shelters",
        "module": "F",
        "geometry_types": ["Point"],
        "default_visible": False,
        "default_opacity": 0.90,
        "source_attribution": "OpenStreetMap (ODbL) Disaster Response / Ambulance / Emergency Shelters",
        "schema": ["facility_id", "name", "facility_type", "operator", "address", "contact_info", "emergency_helpline", "distance_km", "observation_time_utc"],
        "legend": [{"label": "Disaster Response / Shelter / EMS", "color": "#c084fc"}],
        "description": "Emergency shelter facilities, ambulance posts, and disaster response nodes.",
    },
]


# ---------------------------------------------------------------------------
# GEOMETRIC & DATABASE HELPERS
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(text: Optional[str]) -> str:
    if not text:
        return ""
    return " ".join(str(text).strip().lower().split())


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(r * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a))), 3)


def _point_in_ring(lon: float, lat: float, ring: List[List[float]]) -> bool:
    inside = False
    n = len(ring)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = float(ring[i][0]), float(ring[i][1])
        xj, yj = float(ring[j][0]), float(ring[j][1])
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def point_in_geojson_geometry(lat: float, lon: float, geom: Optional[Dict[str, Any]]) -> bool:
    if not geom or not isinstance(geom, dict):
        return False
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if not coords:
        return False

    def _in_polygon(poly_rings: List[List[List[float]]]) -> bool:
        if not poly_rings or not _point_in_ring(lon, lat, poly_rings[0]):
            return False
        for hole in poly_rings[1:]:
            if _point_in_ring(lon, lat, hole):
                return False
        return True

    if gtype == "Polygon":
        return _in_polygon(coords)
    if gtype == "MultiPolygon":
        return any(_in_polygon(poly) for poly in coords)
    return False


def _geojson_bbox(features: List[Dict[str, Any]]) -> Optional[List[float]]:
    min_lon, min_lat, max_lon, max_lat = 999.0, 999.0, -999.0, -999.0
    found = False

    def _visit(coords: Any) -> None:
        nonlocal min_lon, min_lat, max_lon, max_lat, found
        if isinstance(coords, (list, tuple)) and coords and isinstance(coords[0], (int, float)):
            x, y = float(coords[0]), float(coords[1])
            min_lon = min(min_lon, x)
            min_lat = min(min_lat, y)
            max_lon = max(max_lon, x)
            max_lat = max(max_lat, y)
            found = True
        elif isinstance(coords, (list, tuple)):
            for c in coords:
                _visit(c)

    for f in features:
        g = (f or {}).get("geometry")
        if g and "coordinates" in g:
            _visit(g["coordinates"])

    if not found:
        return None
    return [round(min_lon, 5), round(min_lat, 5), round(max_lon, 5), round(max_lat, 5)]


@contextmanager
def _get_conn() -> Iterator[sqlite3.Connection]:
    db_path = get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"India Intelligence database not found at {db_path}")
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _lat_lon_bbox_deg(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    d_lat = radius_km / 110.574
    cos_lat = max(0.15, math.cos(math.radians(lat)))
    d_lon = radius_km / (111.320 * cos_lat)
    return lon - d_lon, lat - d_lat, lon + d_lon, lat + d_lat


# ---------------------------------------------------------------------------
# MODULE A: INDIA ADMINISTRATIVE LOCATION EXPLORER (28 STATES + 8 UTs = 36)
# ---------------------------------------------------------------------------


def get_india_states() -> Dict[str, Any]:
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT state_code, name_en, unit_type, local_name, alt_names_json,
                   hierarchy_schema_json, centroid_lat, centroid_lon,
                   bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat,
                   source_attribution
            FROM states_uts
            ORDER BY name_en COLLATE NOCASE
            """
        ).fetchall()

    states_out: List[Dict[str, Any]] = []
    states_count = 0
    uts_count = 0
    for r in rows:
        if r["unit_type"] == "State":
            states_count += 1
        elif r["unit_type"] == "Union Territory":
            uts_count += 1
        schema = json.loads(r["hierarchy_schema_json"])
        states_out.append(
            {
                "unit_id": f"IND_ST_{r['state_code']}",
                "state_code": r["state_code"],
                "name_en": r["name_en"],
                "unit_type": r["unit_type"],
                "local_name": r["local_name"],
                "alt_names": json.loads(r["alt_names_json"] or "[]"),
                "centroid": [round(float(r["centroid_lat"]), 5), round(float(r["centroid_lon"]), 5)],
                "bbox": [
                    round(float(r["bbox_min_lon"]), 4),
                    round(float(r["bbox_min_lat"]), 4),
                    round(float(r["bbox_max_lon"]), 4),
                    round(float(r["bbox_max_lat"]), 4),
                ],
                "hierarchy_schema": schema,
                "source_attribution": r["source_attribution"],
            }
        )

    return {
        "country": "India",
        "states_ut_count": len(states_out),
        "states_count": states_count,
        "uts_count": uts_count,
        "states": states_out,
        "capital_policy": "Capitals are searchable settlement locations, not separate administrative tiers.",
        "source_attribution": "GADM v4.1 + Survey of India 28-State/8-UT Reference Registry",
    }


def _row_to_admin_dict(r: sqlite3.Row, include_geometry: bool = False) -> Dict[str, Any]:
    out = {
        "unit_id": r["unit_id"],
        "parent_id": r["parent_id"],
        "state_code": r["state_code"],
        "state_name": r["state_name"],
        "level_depth": int(r["level_depth"]),
        "level_type": r["level_type"],
        "level_label_state_specific": r["level_label_state_specific"],
        "name_en": r["name_en"],
        "local_name": r["local_name"],
        "alt_names": json.loads(r["alt_names_json"] or "[]"),
        "stable_id": r["stable_id"],
        "urban_rural_class": r["urban_rural_class"],
        "centroid": [round(float(r["centroid_lat"]), 5), round(float(r["centroid_lon"]), 5)],
        "bbox": [
            round(float(r["bbox_min_lon"]), 4),
            round(float(r["bbox_min_lat"]), 4),
            round(float(r["bbox_max_lon"]), 4),
            round(float(r["bbox_max_lat"]), 4),
        ],
        "source_attribution": r["source_attribution"],
        "verified_flag": bool(r["verified_flag"]),
    }
    if include_geometry and r["geom_geojson"]:
        out["geom_geojson"] = json.loads(r["geom_geojson"])
    return out


def get_admin_children(
    parent_id: Optional[str] = None,
    state_code: Optional[str] = None,
    level_depth: Optional[int] = None,
) -> Dict[str, Any]:
    with _get_conn() as conn:
        if not parent_id and state_code:
            parent_id = f"IND_ST_{state_code.strip().zfill(2)}"

        state_meta = None
        if state_code:
            st_row = conn.execute(
                "SELECT * FROM states_uts WHERE state_code = ?", (state_code.strip().zfill(2),)
            ).fetchone()
            if st_row:
                state_meta = json.loads(st_row["hierarchy_schema_json"])

        parent_row = None
        if parent_id:
            parent_row = conn.execute(
                "SELECT * FROM admin_units WHERE unit_id = ?", (parent_id,)
            ).fetchone()
            if parent_row and not state_meta:
                st_row = conn.execute(
                    "SELECT hierarchy_schema_json FROM states_uts WHERE state_code = ?",
                    (parent_row["state_code"],),
                ).fetchone()
                if st_row:
                    state_meta = json.loads(st_row["hierarchy_schema_json"])

        clauses = ["verified_flag = 1"]
        params: List[Any] = []
        if parent_id:
            clauses.append("parent_id = ?")
            params.append(parent_id)
        if state_code:
            clauses.append("state_code = ?")
            params.append(state_code.strip().zfill(2))
        if level_depth is not None:
            clauses.append("level_depth = ?")
            params.append(int(level_depth))

        sql = f"""
            SELECT unit_id, parent_id, state_code, state_name, level_depth, level_type,
                   level_label_state_specific, name_en, local_name, alt_names_json,
                   stable_id, urban_rural_class, centroid_lat, centroid_lon,
                   bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat,
                   source_attribution, verified_flag
            FROM admin_units
            WHERE {' AND '.join(clauses)}
            ORDER BY level_depth, name_en COLLATE NOCASE
        """
        rows = conn.execute(sql, params).fetchall()

    children = [_row_to_admin_dict(r, include_geometry=False) for r in rows]
    note = None
    if not children and parent_row:
        depth_next = int(parent_row["level_depth"]) + 1
        note = (
            f"No pre-bundled level-{depth_next} polygons verified locally under {parent_row['name_en']}. "
            "Use the Villages/Wards GIS layer (live OpenStreetMap Overpass) or enter Mauza/Ward directly in Land Search. "
            "Zero unverified administrative subdivisions are fabricated."
        )

    return {
        "parent_id": parent_id,
        "parent_name": parent_row["name_en"] if parent_row else None,
        "state_code": state_code or (parent_row["state_code"] if parent_row else None),
        "count": len(children),
        "children": children,
        "hierarchy_schema": state_meta,
        "availability_note": note,
        "source_attribution": "GADM v4.1 / LGD Reference Boundaries",
    }


def _score_search_hit(q_norm: str, name_norm: str, is_alias: bool, kind_weight: int) -> int:
    if name_norm == q_norm:
        base = 100
    elif name_norm.startswith(q_norm):
        base = 75
    elif re.search(rf"\b{re.escape(q_norm)}\b", name_norm):
        base = 55
    else:
        base = 25
    if is_alias:
        base -= 3
    return base + kind_weight


def search_admin_locations(q: str, limit: int = 25) -> Dict[str, Any]:
    q_clean = (q or "").strip()
    q_norm = _norm(q_clean)
    if not q_norm:
        return {"query": q_clean, "count": 0, "results": []}

    like_pat = f"%{q_norm}%"
    candidates: Dict[str, Tuple[int, Dict[str, Any]]] = {}

    def _push(key: str, score: int, item: Dict[str, Any]) -> None:
        prev = candidates.get(key)
        if prev is None or score > prev[0]:
            candidates[key] = (score, item)

    with _get_conn() as conn:
        # 1. States / UTs
        for r in conn.execute(
            """
            SELECT state_code, name_en, unit_type, local_name, alt_names_json,
                   centroid_lat, centroid_lon
            FROM states_uts
            WHERE LOWER(name_en) LIKE ? OR LOWER(COALESCE(local_name,'')) LIKE ?
               OR LOWER(alt_names_json) LIKE ?
            """,
            (like_pat, like_pat, like_pat),
        ).fetchall():
            score = _score_search_hit(q_norm, _norm(r["name_en"]), False, 20)
            _push(
                f"state:{r['state_code']}",
                score,
                {
                    "result_type": "state_ut",
                    "unit_id": f"IND_ST_{r['state_code']}",
                    "state_code": r["state_code"],
                    "state_name": r["name_en"],
                    "district_name": None,
                    "unit_type": r["unit_type"],
                    "level_depth": 1,
                    "level_label": f"State / UT ({r['unit_type']})",
                    "name_en": r["name_en"],
                    "local_name": r["local_name"],
                    "is_capital": False,
                    "lat": round(float(r["centroid_lat"]), 5),
                    "lon": round(float(r["centroid_lon"]), 5),
                    "matched_via": r["name_en"],
                },
            )

        # 2. Verified city / capital / rural / remote settlement locations
        for r in conn.execute(
            """
            SELECT city_id, name_en, local_name, alt_names_json, state_code, state_name,
                   district_name, is_capital, capital_of_state, settlement_class,
                   latitude, longitude
            FROM city_locations
            WHERE LOWER(name_en) LIKE ? OR LOWER(COALESCE(local_name,'')) LIKE ?
               OR LOWER(alt_names_json) LIKE ? OR LOWER(COALESCE(district_name,'')) LIKE ?
            """,
            (like_pat, like_pat, like_pat, like_pat),
        ).fetchall():
            score = _score_search_hit(q_norm, _norm(r["name_en"]), False, 24 if r["is_capital"] else 21)
            _push(
                f"city:{r['city_id']}",
                score,
                {
                    "result_type": "city_location",
                    "unit_id": r["city_id"],
                    "state_code": r["state_code"],
                    "state_name": r["state_name"],
                    "district_name": r["district_name"],
                    "level_depth": None,
                    "level_label": (
                        f"Capital City Location ({r['capital_of_state']})"
                        if r["is_capital"]
                        else f"Searchable {r['settlement_class'].replace('_', ' ').title()}"
                    ),
                    "name_en": r["name_en"],
                    "local_name": r["local_name"],
                    "is_capital": bool(r["is_capital"]),
                    "capital_of_state": r["capital_of_state"],
                    "settlement_class": r["settlement_class"],
                    "capital_note": "Searchable location, not an administrative hierarchy tier.",
                    "lat": round(float(r["latitude"]), 5),
                    "lon": round(float(r["longitude"]), 5),
                    "matched_via": r["name_en"],
                },
            )

        # 3. Verified admin units (Districts & Subdivisions/Tehsils/Anchals)
        for r in conn.execute(
            """
            SELECT unit_id, parent_id, state_code, state_name, level_depth, level_type,
                   level_label_state_specific, name_en, local_name, stable_id,
                   centroid_lat, centroid_lon
            FROM admin_units
            WHERE verified_flag = 1 AND level_depth >= 2
              AND (LOWER(name_en) LIKE ? OR LOWER(COALESCE(local_name,'')) LIKE ?
                   OR LOWER(alt_names_json) LIKE ? OR LOWER(COALESCE(stable_id,'')) = ?)
            LIMIT 120
            """,
            (like_pat, like_pat, like_pat, q_norm),
        ).fetchall():
            w = 18 if r["level_depth"] == 2 else 12
            score = _score_search_hit(q_norm, _norm(r["name_en"]), False, w)
            _push(
                f"admin:{r['unit_id']}",
                score,
                {
                    "result_type": "admin_unit",
                    "unit_id": r["unit_id"],
                    "parent_id": r["parent_id"],
                    "state_code": r["state_code"],
                    "state_name": r["state_name"],
                    "district_name": r["name_en"] if r["level_depth"] == 2 else None,
                    "level_depth": int(r["level_depth"]),
                    "level_label": r["level_label_state_specific"],
                    "stable_id": r["stable_id"],
                    "name_en": r["name_en"],
                    "local_name": r["local_name"],
                    "is_capital": False,
                    "lat": round(float(r["centroid_lat"]), 5),
                    "lon": round(float(r["centroid_lon"]), 5),
                    "matched_via": r["name_en"],
                },
            )

        # 4. Multilingual & alternate aliases (admin_aliases)
        alias_rows = conn.execute(
            """
            SELECT target_kind, target_id, alias_name, alias_norm, language_code
            FROM admin_aliases
            WHERE alias_norm LIKE ?
            LIMIT 120
            """,
            (like_pat,),
        ).fetchall()

        for ar in alias_rows:
            tk = ar["target_kind"]
            tid = ar["target_id"]
            if tk == "city_location":
                c = conn.execute("SELECT * FROM city_locations WHERE city_id = ?", (tid,)).fetchone()
                if c:
                    score = _score_search_hit(q_norm, ar["alias_norm"], True, 22)
                    _push(
                        f"city:{c['city_id']}",
                        score,
                        {
                            "result_type": "city_location",
                            "unit_id": c["city_id"],
                            "state_code": c["state_code"],
                            "state_name": c["state_name"],
                            "district_name": c["district_name"],
                            "level_depth": None,
                            "level_label": (
                                f"Capital City Location ({c['capital_of_state']})"
                                if c["is_capital"]
                                else f"Searchable {c['settlement_class'].replace('_', ' ').title()}"
                            ),
                            "name_en": c["name_en"],
                            "local_name": c["local_name"],
                            "is_capital": bool(c["is_capital"]),
                            "capital_of_state": c["capital_of_state"],
                            "settlement_class": c["settlement_class"],
                            "lat": round(float(c["latitude"]), 5),
                            "lon": round(float(c["longitude"]), 5),
                            "matched_via": f"{ar['alias_name']} [{ar['language_code']}]",
                        },
                    )
            elif tk == "state_ut":
                sc = tid.replace("IND_ST_", "")
                st = conn.execute("SELECT * FROM states_uts WHERE state_code = ?", (sc,)).fetchone()
                if st:
                    score = _score_search_hit(q_norm, ar["alias_norm"], True, 19)
                    _push(
                        f"state:{st['state_code']}",
                        score,
                        {
                            "result_type": "state_ut",
                            "unit_id": tid,
                            "state_code": st["state_code"],
                            "state_name": st["name_en"],
                            "district_name": None,
                            "unit_type": st["unit_type"],
                            "level_depth": 1,
                            "level_label": f"State / UT ({st['unit_type']})",
                            "name_en": st["name_en"],
                            "local_name": st["local_name"],
                            "is_capital": False,
                            "lat": round(float(st["centroid_lat"]), 5),
                            "lon": round(float(st["centroid_lon"]), 5),
                            "matched_via": f"{ar['alias_name']} [{ar['language_code']}]",
                        },
                    )
            elif tk == "admin_unit":
                au = conn.execute(
                    "SELECT * FROM admin_units WHERE unit_id = ? AND verified_flag = 1", (tid,)
                ).fetchone()
                if au:
                    score = _score_search_hit(q_norm, ar["alias_norm"], True, 17 if au["level_depth"] == 2 else 11)
                    _push(
                        f"admin:{au['unit_id']}",
                        score,
                        {
                            "result_type": "admin_unit",
                            "unit_id": au["unit_id"],
                            "parent_id": au["parent_id"],
                            "state_code": au["state_code"],
                            "state_name": au["state_name"],
                            "district_name": au["name_en"] if au["level_depth"] == 2 else None,
                            "level_depth": int(au["level_depth"]),
                            "level_label": au["level_label_state_specific"],
                            "stable_id": au["stable_id"],
                            "name_en": au["name_en"],
                            "local_name": au["local_name"],
                            "is_capital": False,
                            "lat": round(float(au["centroid_lat"]), 5),
                            "lon": round(float(au["centroid_lon"]), 5),
                            "matched_via": f"{ar['alias_name']} [{ar['language_code']}]",
                        },
                    )

    ranked = [item for _, item in sorted(candidates.values(), key=lambda x: (-x[0], str(x[1]["name_en"])))][:limit]
    return {
        "query": q_clean,
        "count": len(ranked),
        "results": ranked,
        "source_attribution": "BHU LOKA India Admin Registry + GADM v4.1 + Multilingual Aliases",
    }


def resolve_admin_context(lat: float, lon: float) -> Dict[str, Any]:
    if not (-90.0 <= float(lat) <= 90.0) or not (-180.0 <= float(lon) <= 180.0):
        raise ValueError(f"Coordinates outside WGS84 bounds: ({lat}, {lon})")

    with _get_conn() as conn:
        # 1. Exact State/UT polygon check (fallback to closest centroid if coastal edge)
        st_candidates = conn.execute(
            """
            SELECT state_code, name_en, unit_type, local_name, hierarchy_schema_json,
                   centroid_lat, centroid_lon, geom_geojson, source_attribution
            FROM states_uts
            WHERE ? BETWEEN bbox_min_lon AND bbox_max_lon
              AND ? BETWEEN bbox_min_lat AND bbox_max_lat
            """,
            (lon, lat),
        ).fetchall()

        matched_state = None
        for row in st_candidates:
            geom = json.loads(row["geom_geojson"])
            if point_in_geojson_geometry(lat, lon, geom):
                matched_state = row
                break
        if matched_state is None and st_candidates:
            matched_state = min(
                st_candidates,
                key=lambda r: haversine_km(lat, lon, float(r["centroid_lat"]), float(r["centroid_lon"])),
            )

        # 2. R-tree candidate admin_units (Level 2 District & Level 3 Subdivision/Tehsil/Circle)
        rtree_rows = conn.execute(
            """
            SELECT a.*
            FROM admin_units a
            JOIN idx_admin_rtree idx ON a.rowid_rtree = idx.id
            WHERE a.verified_flag = 1
              AND a.level_depth IN (2, 3)
              AND idx.min_lon <= ? AND idx.max_lon >= ?
              AND idx.min_lat <= ? AND idx.max_lat >= ?
            ORDER BY a.level_depth ASC
            """,
            (lon, lon, lat, lat),
        ).fetchall()

        matched_district = None
        matched_l3 = None
        for row in rtree_rows:
            geom = json.loads(row["geom_geojson"]) if row["geom_geojson"] else None
            hit = point_in_geojson_geometry(lat, lon, geom) if geom else False
            if hit:
                if row["level_depth"] == 2 and matched_district is None:
                    matched_district = row
                elif row["level_depth"] == 3 and matched_l3 is None:
                    matched_l3 = row

        # Fill parent District if Level-3 matched without Level-2 polygon hit
        if matched_l3 and not matched_district and matched_l3["parent_id"]:
            matched_district = conn.execute(
                "SELECT * FROM admin_units WHERE unit_id = ? AND verified_flag = 1",
                (matched_l3["parent_id"],),
            ).fetchone()
        # Nearest verified district fallback within state if point fell just outside simplified polygon edge
        if matched_state and not matched_district:
            dist_rows = [r for r in rtree_rows if r["level_depth"] == 2 and r["state_code"] == matched_state["state_code"]]
            if dist_rows:
                matched_district = min(
                    dist_rows,
                    key=lambda r: haversine_km(lat, lon, float(r["centroid_lat"]), float(r["centroid_lon"])),
                )

        # Fill state from matched district if coastal
        if not matched_state and matched_district:
            matched_state = conn.execute(
                "SELECT * FROM states_uts WHERE state_code = ?",
                (matched_district["state_code"],),
            ).fetchone()

        # Nearby searchable settlement (including rural villages / remote sectors / capitals)
        city_rows = conn.execute("SELECT * FROM city_locations").fetchall()
        nearest_settlement = None
        min_d = 999999.0
        for c in city_rows:
            d = haversine_km(lat, lon, float(c["latitude"]), float(c["longitude"]))
            if d < min_d:
                min_d = d
                nearest_settlement = {
                    "city_id": c["city_id"],
                    "name_en": c["name_en"],
                    "local_name": c["local_name"],
                    "settlement_class": c["settlement_class"],
                    "is_capital": bool(c["is_capital"]),
                    "distance_km": d,
                }

    hierarchy_schema = json.loads(matched_state["hierarchy_schema_json"]) if matched_state else None
    breadcrumb: List[Dict[str, Any]] = [
        {"depth": 0, "level_type": "country", "label": "Country", "name_en": "India", "unit_id": "IND_00"}
    ]
    if matched_state:
        breadcrumb.append(
            {
                "depth": 1,
                "level_type": "state_ut",
                "label": f"State / UT ({matched_state['unit_type']})",
                "name_en": matched_state["name_en"],
                "local_name": matched_state["local_name"],
                "state_code": matched_state["state_code"],
                "unit_id": f"IND_ST_{matched_state['state_code']}",
            }
        )
    if matched_district:
        breadcrumb.append(
            {
                "depth": 2,
                "level_type": "district",
                "label": matched_district["level_label_state_specific"],
                "name_en": matched_district["name_en"],
                "local_name": matched_district["local_name"],
                "stable_id": matched_district["stable_id"],
                "unit_id": matched_district["unit_id"],
            }
        )
    if matched_l3:
        breadcrumb.append(
            {
                "depth": 3,
                "level_type": matched_l3["level_type"],
                "label": matched_l3["level_label_state_specific"],
                "name_en": matched_l3["name_en"],
                "local_name": matched_l3["local_name"],
                "stable_id": matched_l3["stable_id"],
                "unit_id": matched_l3["unit_id"],
            }
        )

    return {
        "in_india": matched_state is not None,
        "latitude": round(float(lat), 5),
        "longitude": round(float(lon), 5),
        "crs": "EPSG:4326",
        "country": "India" if matched_state else None,
        "state_code": matched_state["state_code"] if matched_state else None,
        "state": matched_state["name_en"] if matched_state else None,
        "unit_type": matched_state["unit_type"] if matched_state else None,
        "district": matched_district["name_en"] if matched_district else None,
        "district_id": matched_district["unit_id"] if matched_district else None,
        "subdivision": matched_l3["name_en"] if matched_l3 else None,
        "subdivision_id": matched_l3["unit_id"] if matched_l3 else None,
        "subdivision_label": matched_l3["level_label_state_specific"] if matched_l3 else (hierarchy_schema["level3_label"] if hierarchy_schema else None),
        "breadcrumb": breadcrumb,
        "hierarchy_schema": hierarchy_schema,
        "nearest_settlement": nearest_settlement if (nearest_settlement and nearest_settlement["distance_km"] <= 80.0) else None,
        "source_attribution": "GADM v4.1 + Survey of India Sovereign Bounds (R-tree + Exact PiP)",
    }


# ---------------------------------------------------------------------------
# MODULE B: LAND PARCEL & PLOT SEARCH (BIHAR PILOT + ALL 36 DILRMP)
# ---------------------------------------------------------------------------


def get_land_record_portals(state_or_code: Optional[str] = None) -> Dict[str, Any]:
    with _get_conn() as conn:
        if state_or_code and state_or_code.strip():
            key = state_or_code.strip()
            row = conn.execute(
                """
                SELECT * FROM state_ror_portals
                WHERE state_code = ? OR LOWER(state_name) = ? OR LOWER(dilrmp_label) LIKE ?
                LIMIT 1
                """,
                (key.zfill(2), key.lower(), f"%{key.lower()}%"),
            ).fetchone()
            if not row:
                raise ValueError(f"State/UT not found in DILRMP directory: {state_or_code}")
            rec = dict(row)
            return {
                "directory_url": DILRMP_DIRECTORY_URL,
                "portal": rec,
                "source_attribution": "Department of Land Resources (DoLR) DILRMP State-RoR-Web",
            }

        rows = conn.execute(
            "SELECT * FROM state_ror_portals ORDER BY state_name COLLATE NOCASE"
        ).fetchall()
    return {
        "directory_url": DILRMP_DIRECTORY_URL,
        "count": len(rows),
        "portals": [dict(r) for r in rows],
        "source_attribution": "Department of Land Resources (DoLR) DILRMP State-RoR-Web + Bihar Revenue Dept",
    }


def _check_public_url_head(url: str, timeout: float = 3.0) -> Dict[str, Any]:
    """Optional read-only availability check against official root URL; never bypasses auth/CAPTCHA."""
    t0 = time.time()
    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "BhuLoka-PortalCheck/1.0 (Academic Research Platform)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", 200)
            return {
                "url": url,
                "reachable": True,
                "http_status": code,
                "latency_ms": round((time.time() - t0) * 1000.0, 1),
                "checked_at_utc": _utc_now(),
            }
    except Exception as exc:
        return {
            "url": url,
            "reachable": False,
            "http_status": None,
            "error": str(exc)[:180],
            "checked_at_utc": _utc_now(),
        }


def search_land_parcel(payload: Dict[str, Any]) -> Dict[str, Any]:
    state_in = (payload.get("state_or_code") or payload.get("state") or "").strip()
    district = (payload.get("district") or "").strip()
    subdivision = (payload.get("subdivision") or "").strip()
    circle = (payload.get("circle") or "").strip()
    block = (payload.get("block") or "").strip()
    village_mauza = (payload.get("village_mauza") or payload.get("mauza") or "").strip()
    khata_no = (payload.get("khata_no") or "").strip()
    khesra_no = (payload.get("khesra_no") or "").strip()
    plot_no = (payload.get("plot_no") or "").strip()
    ulpin = (payload.get("ulpin") or "").strip()
    check_portal = bool(payload.get("check_portal", False))

    if not state_in:
        raise ValueError("State / Union Territory is required for land parcel search.")

    with _get_conn() as conn:
        portal_row = conn.execute(
            """
            SELECT * FROM state_ror_portals
            WHERE state_code = ? OR LOWER(state_name) = ? OR LOWER(dilrmp_label) LIKE ?
            LIMIT 1
            """,
            (state_in.zfill(2), state_in.lower(), f"%{state_in.lower()}%"),
        ).fetchone()
        if not portal_row:
            raise ValueError(f"State/UT '{state_in}' not found in official 36-State DILRMP directory.")
        portal = dict(portal_row)

        # Match administrative hierarchy location centroid for map sync
        matched_admin = None
        if district:
            dist_row = conn.execute(
                """
                SELECT unit_id, name_en, centroid_lat, centroid_lon, bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat
                FROM admin_units
                WHERE verified_flag = 1 AND state_code = ? AND level_depth = 2
                  AND LOWER(name_en) LIKE ?
                ORDER BY CASE WHEN LOWER(name_en) = ? THEN 0 ELSE 1 END
                LIMIT 1
                """,
                (portal["state_code"], f"%{district.lower()}%", district.lower()),
            ).fetchone()
            if dist_row:
                matched_admin = dict(dist_row)
                sub_q = circle or subdivision or block
                if sub_q:
                    l3_row = conn.execute(
                        """
                        SELECT unit_id, name_en, centroid_lat, centroid_lon, bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat
                        FROM admin_units
                        WHERE verified_flag = 1 AND parent_id = ? AND level_depth = 3
                          AND LOWER(name_en) LIKE ?
                        LIMIT 1
                        """,
                        (dist_row["unit_id"], f"%{sub_q.lower()}%"),
                    ).fetchone()
                    if l3_row:
                        matched_admin["subdivision_match"] = dict(l3_row)

        # Query only verified, composite-scoped local land_parcels table (never fabricates rows)
        parcel_matches: List[Dict[str, Any]] = []
        if ulpin:
            rows = conn.execute(
                "SELECT * FROM land_parcels WHERE state_code = ? AND ulpin = ?",
                (portal["state_code"], ulpin),
            ).fetchall()
            parcel_matches = [dict(r) for r in rows]
        elif district and circle and village_mauza and (khata_no or khesra_no or plot_no):
            clauses = [
                "state_code = ?",
                "LOWER(district_name) = ?",
                "LOWER(circle_name) = ?",
                "LOWER(mauza_name) = ?",
            ]
            params: List[Any] = [
                portal["state_code"],
                district.lower(),
                circle.lower(),
                village_mauza.lower(),
            ]
            if khata_no:
                clauses.append("khata_no = ?")
                params.append(khata_no)
            if khesra_no:
                clauses.append("khesra_no = ?")
                params.append(khesra_no)
            if plot_no:
                clauses.append("plot_no = ?")
                params.append(plot_no)
            rows = conn.execute(
                f"SELECT * FROM land_parcels WHERE {' AND '.join(clauses)}",
                params,
            ).fetchall()
            parcel_matches = [dict(r) for r in rows]

    has_parcel_id = bool(khata_no or khesra_no or plot_no or ulpin)
    has_full_scope = bool(ulpin) or bool(district and (circle or subdivision or block) and village_mauza)
    scoping_complete = has_full_scope and has_parcel_id

    missing_scope: List[str] = []
    if not ulpin:
        if not district:
            missing_scope.append("District")
        if not (circle or subdivision or block):
            missing_scope.append("Circle / Anchal / Tehsil / Subdivision")
        if not village_mauza:
            missing_scope.append("Village / Mauza")
        if not (khata_no or khesra_no or plot_no):
            missing_scope.append("Khata / Khesra / Plot / Survey Number (or 14-digit ULPIN)")

    uniqueness_warning = (
        "Parcel numbers (Khata, Khesra, Khasra, Survey/Plot No.) are NOT globally unique across India or within a district. "
        "Every query MUST be scoped by State + District + Anchal/Circle/Tehsil + Mauza/Revenue Village (or 14-digit Bhu-Aadhaar/ULPIN)."
    )

    portal_links: List[Dict[str, Optional[str]]] = []
    if portal.get("ror_portal_url"):
        portal_links.append({"role": "Official Record of Rights (RoR)", "name": portal.get("ror_portal_name"), "url": portal["ror_portal_url"]})
    if portal.get("bhunaksha_portal_url"):
        portal_links.append({"role": "Official Cadastral Map (Bhu-Naksha)", "name": portal.get("bhunaksha_portal_name"), "url": portal["bhunaksha_portal_url"]})
    if portal.get("revenue_dept_url") and portal["revenue_dept_url"] not in {x["url"] for x in portal_links}:
        portal_links.append({"role": "Revenue Department Portal", "name": f"{portal['state_name']} Revenue Department", "url": portal["revenue_dept_url"]})
    portal_links.append({"role": "National DILRMP Directory", "name": "DILRMP State-RoR-Web", "url": DILRMP_DIRECTORY_URL})

    portal_checks: List[Dict[str, Any]] = []
    if check_portal:
        for link in portal_links[:3]:
            if link["url"] and str(link["url"]).startswith("http") and "10.177." not in str(link["url"]):
                portal_checks.append(_check_public_url_head(str(link["url"])))

    is_bihar = portal["state_code"] == "10"
    missing_capability_explanation = portal["integration_notes"]
    if not parcel_matches:
        missing_capability_explanation = (
            f"{portal['integration_notes']} "
            "No local verified parcel record was matched inside BHU LOKA; use the official interactive portal links below to inspect RoR, parcel boundaries, and mutation status legitimately. "
            "Ownership, legal title, area, and boundaries are never fabricated."
        )

    return {
        "query": {
            "state_code": portal["state_code"],
            "state_name": portal["state_name"],
            "district": district or None,
            "subdivision": subdivision or None,
            "circle": circle or None,
            "block": block or None,
            "village_mauza": village_mauza or None,
            "khata_no": khata_no or None,
            "khesra_no": khesra_no or None,
            "plot_no": plot_no or None,
            "ulpin": ulpin or None,
        },
        "pilot_state": "BIHAR_PILOT" if is_bihar else "NATIONAL_DILRMP",
        "scoping_complete": scoping_complete,
        "missing_scoping_fields": missing_scope,
        "uniqueness_warning": uniqueness_warning,
        "integration_status": portal["direct_api_status"],
        "verified_record_returned": len(parcel_matches) > 0,
        "parcels": parcel_matches,
        "admin_location_match": matched_admin,
        "official_portal_links": portal_links,
        "portal_checks": portal_checks,
        "missing_capability_explanation": missing_capability_explanation,
        "privacy_and_compliance": "Zero scraping, zero CAPTCHA bypass, and zero personal owner PII exposure in public map APIs.",
        "source_attribution": "DILRMP State-RoR-Web & State Revenue Department Official Links",
        "timestamp_utc": _utc_now(),
    }


# ---------------------------------------------------------------------------
# LIVE OVERPASS + OFFICIAL RSS CONNECTORS (FAIL-CLOSED + SQLITE CACHE)
# ---------------------------------------------------------------------------


def _parse_retry_after_sec(headers: Any, default_sec: float) -> float:
    if headers is None:
        return default_sec
    raw = headers.get("Retry-After") if hasattr(headers, "get") else None
    if raw is None:
        return default_sec
    try:
        val = float(str(raw).strip())
        return max(0.25, min(val, 5.0))
    except (TypeError, ValueError):
        return default_sec


def _wait_overpass_slot(endpoint: str) -> None:
    wait_sec = 0.0
    with _OVERPASS_LOCK:
        now = time.monotonic()
        last_ts = _OVERPASS_LAST_REQ_BY_ENDPOINT.get(endpoint, 0.0)
        next_ts = max(now, last_ts + _OVERPASS_MIN_INTERVAL_SEC) if last_ts > 0.0 else now
        _OVERPASS_LAST_REQ_BY_ENDPOINT[endpoint] = next_ts
        wait_sec = next_ts - now
    if wait_sec > 0.0:
        time.sleep(wait_sec)


def _fetch_overpass_elements(
    query_body: str,
    timeout: float = 3.5,
    max_retries: int = 2,
    max_total_sec: float = 9.0,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    last_err = None
    data_bytes = urllib.parse.urlencode({"data": query_body}).encode("utf-8")
    deadline = time.monotonic() + float(max_total_sec)
    for endpoint in OVERPASS_ENDPOINTS:
        for attempt in range(max_retries + 1):
            if (deadline - time.monotonic()) <= 0.5:
                return None, (last_err or f"Overpass API timeout budget ({max_total_sec:.0f}s) exceeded")
            _wait_overpass_slot(endpoint)
            remaining = deadline - time.monotonic()
            if remaining <= 0.5:
                return None, (last_err or f"Overpass API timeout budget ({max_total_sec:.0f}s) exceeded")
            req_timeout = min(float(timeout), remaining)
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=data_bytes,
                    method="POST",
                    headers={
                        "User-Agent": "BhuLoka-GeospatialIntel/1.0",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )
                with urllib.request.urlopen(req, timeout=req_timeout) as resp:
                    if getattr(resp, "status", 200) == 200:
                        payload = json.loads(resp.read().decode("utf-8"))
                        elements = payload.get("elements")
                        if isinstance(elements, list):
                            return elements, None
                break
            except urllib.error.HTTPError as exc:
                last_err = f"HTTP {exc.code}: {exc.reason}"
                if exc.code in _OVERPASS_RETRYABLE_STATUS and attempt < max_retries:
                    backoff = _parse_retry_after_sec(
                        getattr(exc, "headers", None),
                        min(4.0, 0.5 * (2 ** attempt)),
                    )
                    if time.monotonic() + backoff < deadline - 0.5:
                        time.sleep(backoff)
                        continue
                break
            except Exception as exc:
                last_err = str(exc)
                break
    return None, (last_err or "Overpass API unreachable")


def _extract_osm_geom(el: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[Dict[str, Any]]]:
    etype = el.get("type")
    if etype == "node" and isinstance(el.get("lat"), (int, float)) and isinstance(el.get("lon"), (int, float)):
        lat, lon = float(el["lat"]), float(el["lon"])
        return lat, lon, {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]}

    center = el.get("center") or {}
    clat = center.get("lat")
    clon = center.get("lon")
    geom_pts = el.get("geometry")
    if isinstance(geom_pts, list) and len(geom_pts) >= 2:
        coords = [[round(float(p["lon"]), 6), round(float(p["lat"]), 6)] for p in geom_pts if "lat" in p and "lon" in p]
        if len(coords) >= 4 and coords[0] == coords[-1]:
            if clat is None or clon is None:
                clon = sum(c[0] for c in coords) / len(coords)
                clat = sum(c[1] for c in coords) / len(coords)
            return float(clat), float(clon), {"type": "Polygon", "coordinates": [coords]}
        elif len(coords) >= 2:
            if clat is None or clon is None:
                mid = coords[len(coords) // 2]
                clon, clat = mid[0], mid[1]
            return float(clat), float(clon), {"type": "LineString", "coordinates": coords}

    if isinstance(clat, (int, float)) and isinstance(clon, (int, float)):
        return float(clat), float(clon), {"type": "Point", "coordinates": [round(float(clon), 6), round(float(clat), 6)]}
    return None, None, None


def _get_cached_osm_payload(cache_key: str) -> Optional[Dict[str, Any]]:
    now = time.time()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT payload_json, expires_epoch FROM osm_spatial_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
    if row and float(row["expires_epoch"]) > now:
        try:
            data = json.loads(row["payload_json"])
            if isinstance(data, dict) and data.get("status") not in ("ERROR", "UNAVAILABLE"):
                return data
        except Exception:
            pass
    return None


def _save_cached_osm_payload(cache_key: str, layer_id: str, payload: Dict[str, Any]) -> None:
    if payload.get("status") in ("ERROR", "UNAVAILABLE"):
        return  # NEVER cache failed Overpass calls
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO osm_spatial_cache (cache_key, layer_id, payload_json, fetched_at_utc, expires_epoch)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                payload_json = excluded.payload_json,
                fetched_at_utc = excluded.fetched_at_utc,
                expires_epoch = excluded.expires_epoch
            """,
            (
                cache_key,
                layer_id,
                json.dumps(payload, ensure_ascii=False),
                _utc_now(),
                time.time() + _OVERPASS_CACHE_TTL_SEC,
            ),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# MODULE E: LOCAL NEWS INGESTION, EN/HI CLASSIFIER & STRICT GEO-PRECISION
# ---------------------------------------------------------------------------


def classify_news_item(headline: str, body: str = "") -> Tuple[str, str]:
    """Deterministic scientific classifier into the 8 mandatory local-news categories + concise summary."""
    txt = f"{headline} {body}".lower()
    if any(k in txt for k in ("flood", "inundat", "landslide", "cyclone", "earthquake", "ndrf", "sdrf", "drought", "disaster", "बाढ़", "आपदा", "भूकंप", "चक्रवात")):
        cat = "Flood and disaster"
    elif any(k in txt for k in ("rain", "thunderstorm", "lightning", "heatwave", "cold wave", "imd", "fog", "monsoon", "वर्षा", "बारिश", "लू", "मौसम", "वज्रपात")):
        cat = "Weather"
    elif any(k in txt for k in ("crime", "police", "arrest", "fir", "theft", "robbery", "murder", "cyber", "पुलिस", "गिरफ्तार", "अपराध")):
        cat = "Crime and public safety"
    elif any(k in txt for k in ("traffic", "jam", "diversion", "highway", "road closure", "nhai", "यातायात", "ट्रैफिक", "डायवर्जन")):
        cat = "Traffic"
    elif any(k in txt for k in ("bridge", "flyover", "rail", "metro", "airport", "dam", "embankment", "expressway", "construction", "पुल", "सड़क", "रेल", "बांध")):
        cat = "Infrastructure"
    elif any(k in txt for k in ("pollution", "aqi", "pm2.5", "forest", "wildlife", "river pollution", "air quality", "प्रदूषण", "पर्यावरण")):
        cat = "Environment"
    elif any(k in txt for k in ("festival", "mela", "fair", "marathon", "cultural", "chhath", "convocation", "मेला", "महोत्सव", "समारोह")):
        cat = "Local events"
    else:
        cat = "Government announcements"

    clean_body = " ".join(BeautifulSoup(body or "", "html.parser").get_text(" ").split())
    if clean_body and clean_body.lower() != headline.lower():
        summary = f"[{cat}] {clean_body[:240].rstrip()}..." if len(clean_body) > 240 else f"[{cat}] {clean_body}"
    else:
        summary = f"[{cat}] {headline}"
    return cat, summary


def refresh_official_news_feeds(timeout: float = 5.0) -> Dict[str, Any]:
    """Fetch official PIB EN/HI RSS and NDMA Sachet CAP RSS feeds safely without inventing headlines."""
    inserted = 0
    errors: List[Dict[str, str]] = []
    now_iso = _utc_now()

    with _get_conn() as conn:
        known_states = [r["name_en"] for r in conn.execute("SELECT name_en FROM states_uts").fetchall()]
        known_cities = [dict(r) for r in conn.execute("SELECT name_en, state_name, district_name, latitude, longitude FROM city_locations").fetchall()]

        for feed in OFFICIAL_NEWS_FEEDS:
            try:
                req = urllib.request.Request(
                    feed["url"],
                    headers={"User-Agent": "BhuLoka-NewsIngest/1.0 (Official RSS Reader)"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    xml_bytes = resp.read()
                root = ET.fromstring(xml_bytes)
            except Exception as exc:
                errors.append({"feed": feed["id"], "url": feed["url"], "error": str(exc)[:160]})
                continue

            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
            for item in items[:40]:
                title_el = item.find("title")
                link_el = item.find("link")
                pub_el = item.find("pubDate")
                if pub_el is None:
                    pub_el = item.find("published")
                if pub_el is None:
                    pub_el = item.find("updated")
                desc_el = item.find("description")
                if desc_el is None:
                    desc_el = item.find("summary")

                headline = (title_el.text or "").strip() if title_el is not None else ""
                link = (link_el.text or link_el.attrib.get("href", "") or "").strip() if link_el is not None else ""
                pub_time = (pub_el.text or now_iso).strip() if pub_el is not None else now_iso
                desc = (desc_el.text or "").strip() if desc_el is not None else ""
                if not headline or not link:
                    continue

                cat, summary = classify_news_item(headline, desc)
                txt_l = f"{headline} {desc}".lower()

                matched_state = None
                matched_district = None
                loc_name = "India"
                lat_val: Optional[float] = None
                lon_val: Optional[float] = None
                geo_precision = "NATIONAL"

                # CAP geo:point or georss:point check
                point_el = item.find("{http://www.georss.org/georss}point")
                if point_el is not None and point_el.text:
                    parts = point_el.text.strip().split()
                    if len(parts) == 2:
                        try:
                            lat_val, lon_val = float(parts[0]), float(parts[1])
                            geo_precision = "VERIFIED_CAP_CENTROID"
                        except ValueError:
                            lat_val, lon_val = None, None

                for c in known_cities:
                    if re.search(rf"\b{re.escape(c['name_en'].split('/')[0].strip().lower())}\b", txt_l):
                        matched_state = c["state_name"]
                        matched_district = c["district_name"]
                        loc_name = c["district_name"] or c["name_en"]
                        if geo_precision != "VERIFIED_CAP_CENTROID":
                            geo_precision = "DISTRICT"  # NEVER pin city/district news to fake exact point!
                        break

                if not matched_state:
                    for st_name in known_states:
                        if st_name.lower() in txt_l:
                            matched_state = st_name
                            loc_name = st_name
                            if geo_precision != "VERIFIED_CAP_CENTROID":
                                geo_precision = "STATE"
                            break

                news_id = "rss_" + hashlib.sha256(f"{feed['id']}:{link}:{headline}".encode("utf-8")).hexdigest()[:16]
                cur = conn.execute(
                    """
                    INSERT INTO news_items (
                        news_id, headline, ai_summary, original_url, publisher, publication_time,
                        language_code, location_name, district, state_name, latitude, longitude,
                        geographic_precision, news_category, verification_status, fetched_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(news_id) DO NOTHING
                    """,
                    (
                        news_id,
                        headline,
                        summary,
                        link,
                        feed["publisher"],
                        pub_time,
                        feed["language_code"],
                        loc_name,
                        matched_district,
                        matched_state,
                        lat_val,
                        lon_val,
                        geo_precision,
                        cat,
                        "OFFICIAL_RSS_VERIFIED",
                        now_iso,
                    ),
                )
                if cur.rowcount > 0:
                    inserted += 1
        conn.commit()

    return {
        "status": "LIVE" if not errors else ("PARTIAL" if inserted > 0 else "UNAVAILABLE"),
        "inserted_new_items": inserted,
        "errors": errors,
        "refreshed_at_utc": now_iso,
    }


# ---------------------------------------------------------------------------
# MODULE C-F + 10-POINT GIS LAYER BUILDER
# ---------------------------------------------------------------------------


def get_layers_catalog() -> Dict[str, Any]:
    return {
        "count": len(LAYER_CATALOG),
        "layers": LAYER_CATALOG,
        "location_contract": [
            "1_real_gis_source",
            "2_documented_schema",
            "3_valid_geojson_representation",
            "4_working_map_toggle",
            "5_loading_state",
            "6_empty_state",
            "7_error_state",
            "8_source_attribution",
            "9_last_updated_timestamp",
            "10_location_context_filter",
        ],
    }


def _meta_for_layer(layer_id: str) -> Dict[str, Any]:
    for entry in LAYER_CATALOG:
        if entry["layer_id"] == layer_id:
            return entry
    raise ValueError(f"Unknown GIS layer_id: {layer_id}")


def _finalize_layer_payload(
    layer_id: str,
    status: str,
    features: List[Dict[str, Any]],
    items: List[Dict[str, Any]],
    lat: float,
    lon: float,
    radius_km: float,
    state: Optional[str],
    district: Optional[str],
    updated_at_utc: Optional[str] = None,
    empty_message: Optional[str] = None,
    error_detail: Optional[str] = None,
    non_pinned_items: Optional[List[Dict[str, Any]]] = None,
    extra_notes: Optional[str] = None,
) -> Dict[str, Any]:
    meta = _meta_for_layer(layer_id)
    now_iso = updated_at_utc or _utc_now()
    if status not in ("ERROR", "UNAVAILABLE") and not features and not items and not non_pinned_items:
        status = "EMPTY"

    return {
        "layer_id": layer_id,
        "title": meta["title"],
        "module": meta["module"],
        "status": status,
        "schema": meta["schema"],
        "source_attribution": meta["source_attribution"],
        "updated_at_utc": now_iso,
        "empty_message": empty_message or f"No verified {meta['title'].lower()} records found inside {radius_km} km of selected location.",
        "error_detail": error_detail,
        "legend": meta["legend"],
        "geometry_types": meta["geometry_types"],
        "default_visible": meta["default_visible"],
        "default_opacity": meta["default_opacity"],
        "description": extra_notes or meta["description"],
        "bbox": _geojson_bbox(features),
        "feature_count": len(features),
        "item_count": len(items),
        "geojson": {
            "type": "FeatureCollection",
            "features": features,
        },
        "items": items,
        "non_pinned_items": non_pinned_items if non_pinned_items is not None else [],
        "location_filter": {
            "latitude": round(float(lat), 5),
            "longitude": round(float(lon), 5),
            "radius_km": float(radius_km),
            "state": state,
            "district": district,
            "crs": "EPSG:4326",
        },
    }


def _layer_admin_boundaries(lat: float, lon: float, radius_km: float, admin_ctx: Dict[str, Any]) -> Dict[str, Any]:
    features: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []
    state_code = admin_ctx.get("state_code")
    min_lon, min_lat, max_lon, max_lat = _lat_lon_bbox_deg(lat, lon, max(radius_km, 25.0))

    with _get_conn() as conn:
        if state_code:
            st = conn.execute(
                "SELECT state_code, name_en, unit_type, local_name, geom_geojson FROM states_uts WHERE state_code = ?",
                (state_code,),
            ).fetchone()
            if st and st["geom_geojson"]:
                props = {
                    "unit_id": f"IND_ST_{st['state_code']}",
                    "state_code": st["state_code"],
                    "name_en": st["name_en"],
                    "local_name": st["local_name"],
                    "level_depth": 1,
                    "level_label_state_specific": f"State / UT ({st['unit_type']})",
                }
                features.append({"type": "Feature", "properties": props, "geometry": json.loads(st["geom_geojson"])})
                items.append(props)

        rows = conn.execute(
            """
            SELECT a.unit_id, a.state_code, a.name_en, a.local_name, a.level_depth,
                   a.level_label_state_specific, a.stable_id, a.geom_geojson
            FROM admin_units a
            JOIN idx_admin_rtree idx ON a.rowid_rtree = idx.id
            WHERE a.verified_flag = 1 AND a.level_depth IN (2, 3)
              AND idx.min_lon <= ? AND idx.max_lon >= ?
              AND idx.min_lat <= ? AND idx.max_lat >= ?
            LIMIT 60
            """,
            (max_lon, min_lon, max_lat, min_lat),
        ).fetchall()
        for r in rows:
            if not r["geom_geojson"]:
                continue
            props = {
                "unit_id": r["unit_id"],
                "state_code": r["state_code"],
                "name_en": r["name_en"],
                "local_name": r["local_name"],
                "level_depth": int(r["level_depth"]),
                "level_label_state_specific": r["level_label_state_specific"],
                "stable_id": r["stable_id"],
            }
            features.append({"type": "Feature", "properties": props, "geometry": json.loads(r["geom_geojson"])})
            items.append(props)

    status = "VERIFIED_LOCAL" if features else "EMPTY"
    return _finalize_layer_payload(
        "admin_boundaries",
        status,
        features,
        items,
        lat,
        lon,
        radius_km,
        admin_ctx.get("state"),
        admin_ctx.get("district"),
    )


def _layer_street_cctv(lat: float, lon: float, radius_km: float, admin_ctx: Dict[str, Any]) -> Dict[str, Any]:
    min_lon, min_lat, max_lon, max_lat = _lat_lon_bbox_deg(lat, lon, radius_km)
    features: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []

    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT c.*
            FROM cctv_cameras c
            JOIN idx_cctv_rtree idx ON c.rowid_rtree = idx.id
            WHERE idx.min_lon <= ? AND idx.max_lon >= ?
              AND idx.min_lat <= ? AND idx.max_lat >= ?
            """,
            (max_lon, min_lon, max_lat, min_lat),
        ).fetchall()

    for r in rows:
        dist = haversine_km(lat, lon, float(r["latitude"]), float(r["longitude"]))
        if dist > radius_km:
            continue
        op_status = r["operational_status"] if r["operational_status"] in ALLOWED_CCTV_STATUSES else "NOT VERIFIED"
        props = {
            "camera_id": r["camera_id"],
            "camera_name": r["camera_name"],
            "city": r["city"],
            "state_name": r["state_name"],
            "latitude": round(float(r["latitude"]), 5),
            "longitude": round(float(r["longitude"]), 5),
            "responsible_authority": r["responsible_authority"],
            "source_url": r["source_url"],
            "stream_type": r["stream_type"],
            "access_status": r["access_status"],
            "operational_status": op_status,
            "last_verified_time": r["last_verified_time"],
            "distance_km": dist,
        }
        items.append(props)
        features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
            }
        )

    items.sort(key=lambda x: x["distance_km"])
    status = "VERIFIED_LOCAL" if items else "EMPTY"
    return _finalize_layer_payload(
        "street_cctv",
        status,
        features,
        items,
        lat,
        lon,
        radius_km,
        admin_ctx.get("state"),
        admin_ctx.get("district"),
        empty_message=CCTV_EMPTY_MESSAGE,
    )


def _layer_local_news(
    lat: float,
    lon: float,
    radius_km: float,
    admin_ctx: Dict[str, Any],
    category: Optional[str] = None,
    language: Optional[str] = None,
    refresh_live: bool = False,
    alerts_only: bool = False,
) -> Dict[str, Any]:
    if refresh_live:
        refresh_official_news_feeds(timeout=4.0)

    state_name = admin_ctx.get("state")
    district_name = admin_ctx.get("district")
    layer_id = "emergency_alerts" if alerts_only else "local_news"

    with _get_conn() as conn:
        clauses: List[str] = []
        params: List[Any] = []
        if category:
            clauses.append("news_category = ?")
            params.append(category)
        if language:
            clauses.append("LOWER(language_code) = ?")
            params.append(language.lower())
        if alerts_only:
            clauses.append("geographic_precision = 'VERIFIED_CAP_CENTROID'")

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM news_items {where_sql} ORDER BY publication_time DESC LIMIT 200",
            params,
        ).fetchall()

    features: List[Dict[str, Any]] = []
    pinned_items: List[Dict[str, Any]] = []
    non_pinned_items: List[Dict[str, Any]] = []

    for r in rows:
        prec = r["geographic_precision"]
        n_state = (r["state_name"] or "").strip()
        n_dist = (r["district"] or "").strip()
        has_coords = isinstance(r["latitude"], (int, float)) and isinstance(r["longitude"], (int, float))
        is_point_verified = prec in ("VERIFIED_CAP_CENTROID", "EXACT_POINT") and has_coords

        if is_point_verified:
            dist = haversine_km(lat, lon, float(r["latitude"]), float(r["longitude"]))
            state_match = bool(state_name and n_state and state_name.lower() == n_state.lower())
            if dist <= radius_km:
                item = {
                    "news_id": r["news_id"],
                    "alert_id": r["news_id"],
                    "headline": r["headline"],
                    "ai_summary": r["ai_summary"],
                    "original_url": r["original_url"],
                    "publisher": r["publisher"],
                    "publication_time": r["publication_time"],
                    "language_code": r["language_code"],
                    "location_name": r["location_name"],
                    "district": r["district"],
                    "state_name": r["state_name"],
                    "latitude": round(float(r["latitude"]), 5),
                    "longitude": round(float(r["longitude"]), 5),
                    "geographic_precision": prec,
                    "news_category": r["news_category"],
                    "verification_status": r["verification_status"],
                    "distance_km": dist,
                    "pinned_on_map": True,
                }
                pinned_items.append(item)
                features.append(
                    {
                        "type": "Feature",
                        "properties": item,
                        "geometry": {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
                    }
                )
            elif state_match:
                non_pinned_items.append(
                    {
                        "news_id": r["news_id"],
                        "headline": r["headline"],
                        "ai_summary": r["ai_summary"],
                        "original_url": r["original_url"],
                        "publisher": r["publisher"],
                        "publication_time": r["publication_time"],
                        "language_code": r["language_code"],
                        "location_name": r["location_name"],
                        "district": r["district"],
                        "state_name": r["state_name"],
                        "latitude": round(float(r["latitude"]), 5),
                        "longitude": round(float(r["longitude"]), 5),
                        "geographic_precision": prec,
                        "news_category": r["news_category"],
                        "verification_status": r["verification_status"],
                        "distance_km": dist,
                        "pinned_on_map": False,
                    }
                )
        else:
            # Strict geo-precision enforcement: DISTRICT/STATE/NATIONAL articles MUST NOT be pinned to point coordinates!
            in_scope = False
            if district_name and n_dist and district_name.lower() in n_dist.lower():
                in_scope = True
            elif state_name and n_state and state_name.lower() == n_state.lower():
                in_scope = True
            elif prec == "NATIONAL":
                in_scope = True

            if in_scope:
                non_pinned_items.append(
                    {
                        "news_id": r["news_id"],
                        "headline": r["headline"],
                        "ai_summary": r["ai_summary"],
                        "original_url": r["original_url"],
                        "publisher": r["publisher"],
                        "publication_time": r["publication_time"],
                        "language_code": r["language_code"],
                        "location_name": r["location_name"],
                        "district": r["district"],
                        "state_name": r["state_name"],
                        "latitude": None,
                        "longitude": None,
                        "geographic_precision": prec,
                        "news_category": r["news_category"],
                        "verification_status": r["verification_status"],
                        "pinned_on_map": False,
                    }
                )

    all_items = pinned_items + non_pinned_items
    status = "VERIFIED_LOCAL" if (features or non_pinned_items) else "EMPTY"
    return _finalize_layer_payload(
        layer_id,
        status,
        features,
        pinned_items,
        lat,
        lon,
        radius_km,
        state_name,
        district_name,
        non_pinned_items=non_pinned_items,
        extra_notes=(
            f"Showing {len(features)} coordinate-verified map pins and {len(non_pinned_items)} un-pinned regional/national headlines "
            "(district/state articles are intentionally withheld from exact point coordinates)."
        ),
    )


def _layer_police_jurisdictions(
    lat: float,
    lon: float,
    radius_km: float,
    admin_ctx: Dict[str, Any],
    refresh_live: bool = False,
) -> Dict[str, Any]:
    min_lon, min_lat, max_lon, max_lat = _lat_lon_bbox_deg(lat, lon, radius_km)
    features: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []
    seen_names: set = set()

    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT p.*
            FROM police_stations p
            JOIN idx_police_rtree idx ON p.rowid_rtree = idx.id
            WHERE idx.min_lon <= ? AND idx.max_lon >= ?
              AND idx.min_lat <= ? AND idx.max_lat >= ?
            """,
            (max_lon, min_lon, max_lat, min_lat),
        ).fetchall()

    for r in rows:
        dist = haversine_km(lat, lon, float(r["latitude"]), float(r["longitude"]))
        if dist > radius_km:
            continue
        j_geom = json.loads(r["jurisdiction_geojson"]) if r["jurisdiction_geojson"] else None
        b_status = "VERIFIED_POLYGON" if j_geom else "POINT_ONLY_BOUNDARY_UNAVAILABLE"
        props = {
            "station_id": r["station_id"],
            "station_name": r["station_name"],
            "district": r["district"],
            "state_name": r["state_name"],
            "jurisdiction_boundary": j_geom,
            "boundary_status": b_status,
            "address": r["address"],
            "contact_info": r["contact_info"],
            "official_source": r["official_source"],
            "emergency_contact_link": r["emergency_link"] or "tel:112",
            "latitude": round(float(r["latitude"]), 5),
            "longitude": round(float(r["longitude"]), 5),
            "distance_km": dist,
            "last_verified_utc": r["last_verified_utc"],
        }
        items.append(props)
        seen_names.add(_norm(r["station_name"]))
        features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": j_geom if j_geom else {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]},
            }
        )

    cache_key = f"osm:police_jurisdictions:{lat:.3f}:{lon:.3f}:{radius_km:.1f}"
    osm_err: Optional[str] = None
    live_src_status = "VERIFIED_LOCAL" if items else "EMPTY"
    cached = None if refresh_live else _get_cached_osm_payload(cache_key)

    osm_items: List[Dict[str, Any]] = []
    osm_features: List[Dict[str, Any]] = []

    if cached:
        osm_items = cached.get("items", [])
        osm_features = cached.get("features", [])
        live_src_status = "CACHED" if osm_items or items else live_src_status
    elif refresh_live or not items:
        r_m = int(min(radius_km, 25.0) * 1000)
        q = f'[out:json][timeout:10];(node["amenity"="police"](around:{r_m},{lat},{lon});way["amenity"="police"](around:{r_m},{lat},{lon}););out center 40;'
        els, osm_err = _fetch_overpass_elements(q, timeout=5.0)
        if els is not None:
            now_iso = _utc_now()
            for el in els:
                tags = el.get("tags") or {}
                nm = tags.get("name") or tags.get("name:en") or "Police Station (OSM)"
                plat, plon, geom = _extract_osm_geom(el)
                if plat is None or plon is None or geom is None:
                    continue
                dist = haversine_km(lat, lon, plat, plon)
                addr_parts = [tags.get("addr:street"), tags.get("addr:suburb"), tags.get("addr:city") or admin_ctx.get("district")]
                addr = ", ".join(p for p in addr_parts if p) or "Verified OSM Coordinate"
                props = {
                    "station_id": f"osm_ps_{el.get('type')}_{el.get('id')}",
                    "station_name": nm,
                    "district": admin_ctx.get("district") or admin_ctx.get("state"),
                    "state_name": admin_ctx.get("state"),
                    "jurisdiction_boundary": None,
                    "boundary_status": "POINT_ONLY_BOUNDARY_UNAVAILABLE",
                    "address": addr,
                    "contact_info": tags.get("phone") or tags.get("contact:phone") or "Dial 112 Emergency",
                    "official_source": "OpenStreetMap (ODbL) amenity=police (Jurisdiction polygon unavailable)",
                    "emergency_contact_link": "tel:112",
                    "latitude": round(plat, 5),
                    "longitude": round(plon, 5),
                    "distance_km": dist,
                    "last_verified_utc": now_iso,
                }
                osm_items.append(props)
                osm_features.append({"type": "Feature", "properties": props, "geometry": {"type": "Point", "coordinates": [round(plon, 6), round(plat, 6)]}})
            _save_cached_osm_payload(cache_key, "police_jurisdictions", {"status": "LIVE", "items": osm_items, "features": osm_features})
            live_src_status = "LIVE" if osm_items or items else "EMPTY"
        elif not items:
            live_src_status = "ERROR"

    for feat, it in zip(osm_features, osm_items):
        if _norm(it["station_name"]) not in seen_names:
            seen_names.add(_norm(it["station_name"]))
            items.append(it)
            features.append(feat)

    items.sort(key=lambda x: x["distance_km"])
    return _finalize_layer_payload(
        "police_jurisdictions",
        live_src_status,
        features,
        items,
        lat,
        lon,
        radius_km,
        admin_ctx.get("state"),
        admin_ctx.get("district"),
        error_detail=osm_err,
        extra_notes=(
            "Jurisdiction polygons are never inferred from nearest police station coordinates. "
            "Stations without published official polygons explicitly carry boundary_status='POINT_ONLY_BOUNDARY_UNAVAILABLE'."
        ),
    )


def _query_overpass_cached_layer(
    layer_id: str,
    lat: float,
    lon: float,
    radius_km: float,
    admin_ctx: Dict[str, Any],
    overpass_filter: str,
    refresh_live: bool,
    mapper_fn,
) -> Dict[str, Any]:
    cache_key = f"osm:{layer_id}:{lat:.3f}:{lon:.3f}:{radius_km:.1f}"
    cached = None if refresh_live else _get_cached_osm_payload(cache_key)
    if cached:
        feats = cached.get("features", [])
        items = cached.get("items", [])
        return _finalize_layer_payload(
            layer_id,
            "CACHED" if items else "EMPTY",
            feats,
            items,
            lat,
            lon,
            radius_km,
            admin_ctx.get("state"),
            admin_ctx.get("district"),
            updated_at_utc=cached.get("updated_at_utc"),
        )

    r_m = int(min(radius_km, 25.0) * 1000)
    q = overpass_filter.format(r_m=r_m, lat=lat, lon=lon)
    els, err = _fetch_overpass_elements(q, timeout=5.0)
    if els is None:
        return _finalize_layer_payload(
            layer_id,
            "ERROR",
            [],
            [],
            lat,
            lon,
            radius_km,
            admin_ctx.get("state"),
            admin_ctx.get("district"),
            error_detail=f"Live Overpass query failed ({err}); zero synthetic records substituted.",
        )

    now_iso = _utc_now()
    features: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []
    for el in els:
        mapped = mapper_fn(el, lat, lon, admin_ctx, now_iso)
        if not mapped:
            continue
        props, geom = mapped
        items.append(props)
        features.append({"type": "Feature", "properties": props, "geometry": geom})

    items.sort(key=lambda x: x.get("distance_km", 0.0))
    status = "LIVE" if items else "EMPTY"
    _save_cached_osm_payload(
        cache_key,
        layer_id,
        {"status": status, "updated_at_utc": now_iso, "items": items, "features": features},
    )
    return _finalize_layer_payload(
        layer_id,
        status,
        features,
        items,
        lat,
        lon,
        radius_km,
        admin_ctx.get("state"),
        admin_ctx.get("district"),
        updated_at_utc=now_iso,
    )


def _map_village_ward(el: Dict[str, Any], c_lat: float, c_lon: float, admin_ctx: Dict[str, Any], now_iso: str):
    tags = el.get("tags") or {}
    nm = tags.get("name") or tags.get("name:en")
    if not nm:
        return None
    plat, plon, geom = _extract_osm_geom(el)
    if plat is None or plon is None or geom is None:
        return None
    place = tags.get("place") or (f"admin_level_{tags.get('admin_level')}" if tags.get("admin_level") else "locality")
    rural_tags = {"village", "hamlet", "isolated_dwelling", "farm"}
    urban_rural = "RURAL" if place in rural_tags else "URBAN"
    tier = "Gram Panchayat / Village / Hamlet" if urban_rural == "RURAL" else "Urban Local Body / Ward / Locality"
    props = {
        "vw_id": f"osm_vw_{el.get('type')}_{el.get('id')}",
        "name_en": nm,
        "local_name": tags.get("name:hi") or tags.get("name:kn") or tags.get("name:mr"),
        "place_type": place,
        "urban_rural_class": urban_rural,
        "hierarchy_tier": tier,
        "distance_km": haversine_km(c_lat, c_lon, plat, plon),
        "observation_time": now_iso,
        "source_attribution": "OpenStreetMap (ODbL)",
    }
    return props, geom


def _map_facility(ftype: str, helpline: str):
    def _fn(el: Dict[str, Any], c_lat: float, c_lon: float, admin_ctx: Dict[str, Any], now_iso: str):
        tags = el.get("tags") or {}
        nm = tags.get("name") or tags.get("name:en") or f"{ftype.replace('_', ' ').title()} (OSM)"
        plat, plon, geom = _extract_osm_geom(el)
        if plat is None or plon is None or geom is None:
            return None
        addr = ", ".join(p for p in (tags.get("addr:street"), tags.get("addr:suburb"), tags.get("addr:city")) if p) or admin_ctx.get("district")
        props = {
            "facility_id": f"osm_fac_{el.get('type')}_{el.get('id')}",
            "name": nm,
            "facility_type": tags.get("amenity") or tags.get("emergency") or ftype,
            "operator": tags.get("operator") or "Listed Public / Institutional Operator",
            "address": addr,
            "contact_info": tags.get("phone") or tags.get("contact:phone") or f"Helpline {helpline}",
            "emergency_helpline": helpline,
            "distance_km": haversine_km(c_lat, c_lon, plat, plon),
            "observation_time_utc": now_iso,
            "source_attribution": "OpenStreetMap (ODbL)",
        }
        return props, {"type": "Point", "coordinates": [round(plon, 6), round(plat, 6)]}
    return _fn


def _map_road_closure(el: Dict[str, Any], c_lat: float, c_lon: float, admin_ctx: Dict[str, Any], now_iso: str):
    tags = el.get("tags") or {}
    plat, plon, geom = _extract_osm_geom(el)
    if plat is None or plon is None or geom is None:
        return None
    road_name = tags.get("name") or tags.get("ref") or tags.get("construction") or "Road Segment"
    reason = tags.get("construction") or tags.get("access") or tags.get("note") or "Road Construction / Access Restriction"
    props = {
        "incident_id": f"osm_close_{el.get('type')}_{el.get('id')}",
        "title": f"Closure/Restriction: {road_name}",
        "road_name": road_name,
        "closure_reason": reason,
        "distance_km": haversine_km(c_lat, c_lon, plat, plon),
        "observation_time_utc": now_iso,
        "source_attribution": "OpenStreetMap (ODbL)",
    }
    return props, geom


def _map_traffic_advisory(el: Dict[str, Any], c_lat: float, c_lon: float, admin_ctx: Dict[str, Any], now_iso: str):
    tags = el.get("tags") or {}
    plat, plon, geom = _extract_osm_geom(el)
    if plat is None or plon is None or geom is None:
        return None
    nm = tags.get("name") or tags.get("highway") or tags.get("enforcement") or "Traffic Advisory Node"
    desc = ", ".join(f"{k}={tags[k]}" for k in ("highway", "enforcement", "traffic_calming", "maxspeed") if tags.get(k))
    props = {
        "incident_id": f"osm_trf_{el.get('type')}_{el.get('id')}",
        "title": str(nm),
        "road_name": tags.get("addr:street") or tags.get("ref") or str(nm),
        "description": desc or "Mapped traffic control/advisory node",
        "distance_km": haversine_km(c_lat, c_lon, plat, plon),
        "observation_time_utc": now_iso,
        "source_attribution": "OpenStreetMap (ODbL)",
    }
    return props, geom


def _map_diversion(el: Dict[str, Any], c_lat: float, c_lon: float, admin_ctx: Dict[str, Any], now_iso: str):
    tags = el.get("tags") or {}
    plat, plon, geom = _extract_osm_geom(el)
    if plat is None or plon is None or geom is None:
        return None
    props = {
        "incident_id": f"osm_div_{el.get('type')}_{el.get('id')}",
        "title": tags.get("name") or "Traffic Diversion / Detour",
        "description": tags.get("note") or tags.get("description") or "Mapped detour",
        "distance_km": haversine_km(c_lat, c_lon, plat, plon),
        "observation_time_utc": now_iso,
        "source_attribution": "OpenStreetMap (ODbL)",
    }
    return props, geom


def get_villages_wards(
    lat: float,
    lon: float,
    radius_km: float = 10.0,
    refresh_live: bool = False,
) -> Dict[str, Any]:
    admin_ctx = resolve_admin_context(lat, lon)
    min_lon, min_lat, max_lon, max_lat = _lat_lon_bbox_deg(lat, lon, radius_km)
    local_features: List[Dict[str, Any]] = []
    local_items: List[Dict[str, Any]] = []

    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT v.*
            FROM villages_wards v
            JOIN idx_villages_rtree idx ON v.rowid_rtree = idx.id
            WHERE v.verified_flag = 1
              AND idx.min_lon <= ? AND idx.max_lon >= ?
              AND idx.min_lat <= ? AND idx.max_lat >= ?
            """,
            (max_lon, min_lon, max_lat, min_lat),
        ).fetchall()
    for r in rows:
        dist = haversine_km(lat, lon, float(r["latitude"]), float(r["longitude"]))
        if dist > radius_km:
            continue
        props = {
            "vw_id": r["vw_id"],
            "name_en": r["name_en"],
            "local_name": r["local_name"],
            "place_type": r["place_type"],
            "urban_rural_class": r["urban_rural_class"],
            "hierarchy_tier": r["hierarchy_tier"],
            "distance_km": dist,
            "observation_time": r["updated_at_utc"],
            "source_attribution": r["source_attribution"],
        }
        geom = json.loads(r["geom_geojson"]) if r["geom_geojson"] else {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]}
        local_items.append(props)
        local_features.append({"type": "Feature", "properties": props, "geometry": geom})

    if local_items and not refresh_live:
        return _finalize_layer_payload(
            "villages_wards", "VERIFIED_LOCAL", local_features, local_items,
            lat, lon, radius_km, admin_ctx.get("state"), admin_ctx.get("district"),
        )

    overpass_q = (
        '[out:json][timeout:10];('
        'node["place"~"village|hamlet|suburb|quarter|neighbourhood|town"](around:{r_m},{lat},{lon});'
        'way["boundary"="administrative"]["admin_level"~"9|10"](around:{r_m},{lat},{lon});'
        ');out center 60;'
    )
    res = _query_overpass_cached_layer(
        "villages_wards", lat, lon, radius_km, admin_ctx, overpass_q, refresh_live, _map_village_ward
    )
    if local_items:
        res["items"] = local_items + res["items"]
        res["geojson"]["features"] = local_features + res["geojson"]["features"]
        res["feature_count"] = len(res["geojson"]["features"])
        res["item_count"] = len(res["items"])
        res["status"] = "VERIFIED_LOCAL"
    return res


def _query_local_facilities(
    facility_types: Tuple[str, ...],
    lat: float,
    lon: float,
    radius_km: float,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    min_lon, min_lat, max_lon, max_lat = _lat_lon_bbox_deg(lat, lon, radius_km)
    placeholders = ",".join("?" for _ in facility_types)
    local_items: List[Dict[str, Any]] = []
    local_features: List[Dict[str, Any]] = []
    with _get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT e.*
            FROM emergency_facilities e
            JOIN idx_emergency_rtree idx ON e.rowid_rtree = idx.id
            WHERE e.facility_type IN ({placeholders})
              AND idx.min_lon <= ? AND idx.max_lon >= ?
              AND idx.min_lat <= ? AND idx.max_lat >= ?
            """,
            (*facility_types, max_lon, min_lon, max_lat, min_lat),
        ).fetchall()
    for r in rows:
        dist = haversine_km(lat, lon, float(r["latitude"]), float(r["longitude"]))
        if dist > radius_km:
            continue
        props = {
            "facility_id": r["facility_id"],
            "name": r["name_en"],
            "facility_type": r["facility_type"],
            "operator": r["operator"],
            "address": r["address"],
            "contact_info": r["contact_info"],
            "emergency_helpline": r["emergency_link"],
            "distance_km": dist,
            "observation_time_utc": r["observation_time_utc"],
            "source_attribution": r["source_attribution"],
        }
        geom = json.loads(r["geom_geojson"]) if r["geom_geojson"] else {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]}
        local_items.append(props)
        local_features.append({"type": "Feature", "properties": props, "geometry": geom})
    return local_items, local_features


def _query_local_traffic(
    incident_kind: str,
    lat: float,
    lon: float,
    radius_km: float,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    min_lon, min_lat, max_lon, max_lat = _lat_lon_bbox_deg(lat, lon, radius_km)
    local_items: List[Dict[str, Any]] = []
    local_features: List[Dict[str, Any]] = []
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT t.*
            FROM traffic_incidents t
            JOIN idx_traffic_rtree idx ON t.rowid_rtree = idx.id
            WHERE t.incident_kind = ?
              AND idx.min_lon <= ? AND idx.max_lon >= ?
              AND idx.min_lat <= ? AND idx.max_lat >= ?
            """,
            (incident_kind, max_lon, min_lon, max_lat, min_lat),
        ).fetchall()
    for r in rows:
        if r["latitude"] is None or r["longitude"] is None:
            continue
        dist = haversine_km(lat, lon, float(r["latitude"]), float(r["longitude"]))
        if dist > radius_km:
            continue
        props = {
            "incident_id": r["incident_id"],
            "title": r["title"],
            "road_name": r["road_name"],
            "description": r["description"],
            "closure_reason": r["description"],
            "distance_km": dist,
            "observation_time_utc": r["observation_time_utc"],
            "source_attribution": r["source_attribution"],
        }
        geom = json.loads(r["geom_geojson"]) if r["geom_geojson"] else {"type": "Point", "coordinates": [float(r["longitude"]), float(r["latitude"])]}
        local_items.append(props)
        local_features.append({"type": "Feature", "properties": props, "geometry": geom})
    return local_items, local_features


def _merge_local_and_overpass(
    layer_res: Dict[str, Any],
    local_items: List[Dict[str, Any]],
    local_features: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not local_items:
        return layer_res
    merged_items = local_items + list(layer_res.get("items") or [])
    merged_feats = local_features + list((layer_res.get("geojson") or {}).get("features") or [])
    merged_items.sort(key=lambda x: x.get("distance_km", 0.0))
    layer_res["items"] = merged_items
    layer_res["item_count"] = len(merged_items)
    layer_res["geojson"] = {"type": "FeatureCollection", "features": merged_feats}
    layer_res["feature_count"] = len(merged_feats)
    layer_res["bbox"] = _geojson_bbox(merged_feats)
    if layer_res["status"] in ("EMPTY", "ERROR"):
        layer_res["status"] = "VERIFIED_LOCAL"
    return layer_res


def get_gis_layer(
    layer_id: str,
    lat: float,
    lon: float,
    radius_km: float = 10.0,
    refresh_live: bool = False,
    category: Optional[str] = None,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    if not (-90.0 <= float(lat) <= 90.0) or not (-180.0 <= float(lon) <= 180.0):
        raise ValueError(f"Coordinates out of WGS84 bounds: ({lat}, {lon})")
    if not (1.0 <= float(radius_km) <= 100.0):
        raise ValueError(f"radius_km must be within [1, 100], got {radius_km}")

    _meta_for_layer(layer_id)
    admin_ctx = resolve_admin_context(lat, lon)
    radius_km = float(radius_km)

    if layer_id == "admin_boundaries":
        return _layer_admin_boundaries(lat, lon, radius_km, admin_ctx)
    if layer_id == "villages_wards":
        return get_villages_wards(lat, lon, radius_km, refresh_live=refresh_live)
    if layer_id == "street_cctv":
        return _layer_street_cctv(lat, lon, radius_km, admin_ctx)
    if layer_id == "local_news":
        return _layer_local_news(
            lat, lon, radius_km, admin_ctx,
            category=category, language=language, refresh_live=refresh_live, alerts_only=False,
        )
    if layer_id == "emergency_alerts":
        return _layer_local_news(
            lat, lon, radius_km, admin_ctx,
            category=category, language=language, refresh_live=refresh_live, alerts_only=True,
        )
    if layer_id == "police_jurisdictions":
        return _layer_police_jurisdictions(lat, lon, radius_km, admin_ctx, refresh_live=refresh_live)
    if layer_id == "hospitals":
        q = '[out:json][timeout:10];(node["amenity"~"hospital|clinic"](around:{r_m},{lat},{lon});way["amenity"~"hospital|clinic"](around:{r_m},{lat},{lon}););out center 45;'
        res = _query_overpass_cached_layer("hospitals", lat, lon, radius_km, admin_ctx, q, refresh_live, _map_facility("HOSPITAL", "108 / 112"))
        li, lf = _query_local_facilities(("HOSPITAL",), lat, lon, radius_km)
        return _merge_local_and_overpass(res, li, lf)
    if layer_id == "fire_stations":
        q = '[out:json][timeout:10];(node["amenity"="fire_station"](around:{r_m},{lat},{lon});way["amenity"="fire_station"](around:{r_m},{lat},{lon}););out center 30;'
        res = _query_overpass_cached_layer("fire_stations", lat, lon, radius_km, admin_ctx, q, refresh_live, _map_facility("FIRE_STATION", "101 / 112"))
        li, lf = _query_local_facilities(("FIRE_STATION",), lat, lon, radius_km)
        return _merge_local_and_overpass(res, li, lf)
    if layer_id == "disaster_response":
        q = '[out:json][timeout:10];(node["emergency"~"disaster_response|ses_station|ambulance_station"](around:{r_m},{lat},{lon});way["emergency"~"disaster_response|ses_station|ambulance_station"](around:{r_m},{lat},{lon});node["amenity"="shelter"](around:{r_m},{lat},{lon});way["amenity"="shelter"](around:{r_m},{lat},{lon}););out center 30;'
        res = _query_overpass_cached_layer("disaster_response", lat, lon, radius_km, admin_ctx, q, refresh_live, _map_facility("DISASTER_RESPONSE", "1070 / 112"))
        li, lf = _query_local_facilities(("DISASTER_RESPONSE", "EMERGENCY_SHELTER"), lat, lon, radius_km)
        return _merge_local_and_overpass(res, li, lf)
    if layer_id == "road_closures":
        q = '[out:json][timeout:10];(way["highway"="construction"](around:{r_m},{lat},{lon});way["highway"]["access"="no"](around:{r_m},{lat},{lon}););out center 35;'
        res = _query_overpass_cached_layer("road_closures", lat, lon, radius_km, admin_ctx, q, refresh_live, _map_road_closure)
        li, lf = _query_local_traffic("ROAD_CLOSURE", lat, lon, radius_km)
        return _merge_local_and_overpass(res, li, lf)
    if layer_id == "traffic_advisories":
        q = '[out:json][timeout:10];(node["enforcement"](around:{r_m},{lat},{lon});node["highway"="speed_camera"](around:{r_m},{lat},{lon});node["traffic_sign"](around:{r_m},{lat},{lon}););out 35;'
        res = _query_overpass_cached_layer("traffic_advisories", lat, lon, radius_km, admin_ctx, q, refresh_live, _map_traffic_advisory)
        li, lf = _query_local_traffic("ADVISORY", lat, lon, radius_km)
        return _merge_local_and_overpass(res, li, lf)
    if layer_id == "diversions":
        q = '[out:json][timeout:10];(relation["route"="detour"](around:{r_m},{lat},{lon});way["detour"](around:{r_m},{lat},{lon});node["detour"](around:{r_m},{lat},{lon}););out center 25;'
        res = _query_overpass_cached_layer("diversions", lat, lon, radius_km, admin_ctx, q, refresh_live, _map_diversion)
        li, lf = _query_local_traffic("DIVERSION", lat, lon, radius_km)
        return _merge_local_and_overpass(res, li, lf)

    raise ValueError(f"Unsupported layer_id: {layer_id}")
