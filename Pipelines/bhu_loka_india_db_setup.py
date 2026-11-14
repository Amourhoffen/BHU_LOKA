"""
BHU LOKA India Location, Land Records & Street Intelligence Database Setup v1.0
Idempotent schema normalization, quality cleanup, R-tree spatial indexing,
and static frontend administrative index regeneration.
Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = WORKSPACE_ROOT / "Data" / "01_Boundaries" / "bhu_loka_india_intel.sqlite"
DEFAULT_ADMIN_INDEX_JS = WORKSPACE_ROOT / "Data" / "08_Processed_Outputs" / "bhu_loka_india_admin_index.js"


def get_db_path() -> Path:
    override = os.environ.get("BHU_LOKA_INDIA_DB_PATH", "").strip()
    if override:
        return Path(override)
    return DEFAULT_DB_PATH


def ensure_normalized_schema(conn: sqlite3.Connection) -> None:
    """Create Section 9 normalized tables and spatial R-tree indexes if missing."""
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS villages_wards (
            rowid_rtree INTEGER PRIMARY KEY AUTOINCREMENT,
            vw_id TEXT NOT NULL UNIQUE,
            state_code TEXT,
            state_name TEXT,
            district_name TEXT,
            subdivision_name TEXT,
            block_circle_name TEXT,
            name_en TEXT NOT NULL,
            local_name TEXT,
            alt_names_json TEXT NOT NULL DEFAULT '[]',
            place_type TEXT NOT NULL,
            urban_rural_class TEXT NOT NULL CHECK (urban_rural_class IN ('RURAL', 'URBAN', 'UNKNOWN')),
            hierarchy_tier TEXT NOT NULL,
            stable_id TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            geom_geojson TEXT,
            source_attribution TEXT NOT NULL,
            verified_flag INTEGER NOT NULL DEFAULT 1,
            updated_at_utc TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS idx_villages_rtree USING rtree(
            id, min_lon, max_lon, min_lat, max_lat
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_vw_state_dist ON villages_wards (state_code, district_name)"
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS land_parcels (
            parcel_id TEXT PRIMARY KEY,
            state_code TEXT NOT NULL,
            state_name TEXT NOT NULL,
            district_name TEXT NOT NULL,
            subdivision_name TEXT,
            circle_name TEXT NOT NULL,
            block_name TEXT,
            mauza_name TEXT NOT NULL,
            khata_no TEXT NOT NULL DEFAULT '',
            khesra_no TEXT NOT NULL DEFAULT '',
            plot_no TEXT NOT NULL DEFAULT '',
            ulpin TEXT,
            area_text TEXT,
            ror_summary TEXT,
            official_record_ref TEXT,
            centroid_lat REAL,
            centroid_lon REAL,
            geom_geojson TEXT,
            source_portal_url TEXT NOT NULL,
            source_attribution TEXT NOT NULL,
            verified_flag INTEGER NOT NULL DEFAULT 1,
            last_updated_utc TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_parcel_composite ON land_parcels (
            state_code, district_name, circle_name, mauza_name, khata_no, khesra_no, plot_no
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_parcel_ulpin ON land_parcels (ulpin)"
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS traffic_incidents (
            rowid_rtree INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT NOT NULL UNIQUE,
            incident_kind TEXT NOT NULL CHECK (incident_kind IN ('ADVISORY', 'ROAD_CLOSURE', 'DIVERSION')),
            title TEXT NOT NULL,
            road_name TEXT,
            description TEXT,
            state_name TEXT,
            district_name TEXT,
            latitude REAL,
            longitude REAL,
            geom_geojson TEXT,
            source_attribution TEXT NOT NULL,
            source_url TEXT,
            observation_time_utc TEXT NOT NULL,
            fetched_at_utc TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS idx_traffic_rtree USING rtree(
            id, min_lon, max_lon, min_lat, max_lat
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS emergency_facilities (
            rowid_rtree INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id TEXT NOT NULL UNIQUE,
            facility_type TEXT NOT NULL CHECK (facility_type IN ('HOSPITAL', 'FIRE_STATION', 'DISASTER_RESPONSE', 'EMERGENCY_SHELTER')),
            name_en TEXT NOT NULL,
            operator TEXT,
            address TEXT,
            contact_info TEXT,
            emergency_link TEXT NOT NULL DEFAULT 'tel:112',
            state_name TEXT,
            district_name TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            geom_geojson TEXT,
            source_attribution TEXT NOT NULL,
            observation_time_utc TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS idx_emergency_rtree USING rtree(
            id, min_lon, max_lon, min_lat, max_lat
        )
        """
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_admin_verified ON admin_units (verified_flag, level_depth, state_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_news_precision ON news_items (geographic_precision, news_category, language_code)")
    conn.commit()


def clean_existing_data(conn: sqlite3.Connection) -> Dict[str, int]:
    """Purge stale/mock cache entries and fix spelling/placeholder quality issues."""
    cur = conn.cursor()
    stats: Dict[str, int] = {}

    cur.execute("DELETE FROM osm_spatial_cache")
    stats["cleared_osm_cache_rows"] = cur.rowcount

    cur.execute(
        """
        UPDATE states_uts
        SET hierarchy_schema_json = REPLACE(hierarchy_schema_json, 'Anudal', 'Anumandal')
        WHERE hierarchy_schema_json LIKE '%Anudal%'
        """
    )
    stats["fixed_state_schema_anudal"] = cur.rowcount

    cur.execute(
        """
        UPDATE admin_units
        SET level_label_state_specific = REPLACE(level_label_state_specific, 'Anudal', 'Anumandal')
        WHERE level_label_state_specific LIKE '%Anudal%'
        """
    )
    stats["fixed_admin_label_anudal"] = cur.rowcount

    cur.execute(
        """
        UPDATE admin_units
        SET source_attribution = REPLACE(source_attribution, 'Anudal', 'Anumandal')
        WHERE source_attribution LIKE '%Anudal%'
        """
    )
    stats["fixed_admin_source_anudal"] = cur.rowcount

    cur.execute(
        """
        UPDATE admin_units
        SET verified_flag = 0
        WHERE LOWER(TRIM(name_en)) LIKE 'n.a.%' OR LOWER(TRIM(name_en)) = 'na'
        """
    )
    stats["flagged_na_admin_units"] = cur.rowcount

    # Ensure Patna L3 Danapur / Masaurhi / Barh or local multilingual aliases are present cleanly
    extra_aliases: List[Tuple[str, str, str, str, str]] = [
        ("city_location", "city_patna", "पटना", "hi", "local"),
        ("city_location", "city_gaya", "गया", "hi", "local"),
        ("city_location", "city_muzaffarpur", "मुजफ्फरपुर", "hi", "local"),
        ("city_location", "city_new_delhi", "नई दिल्ली", "hi", "local"),
        ("city_location", "city_new_delhi", "दिल्ली", "hi", "local"),
        ("city_location", "city_mumbai", "मुंबई", "hi", "local"),
        ("city_location", "city_bengaluru", "बेंगलुरु", "hi", "local"),
        ("city_location", "city_leh", "लेह", "hi", "local"),
        ("city_location", "rural_maner_saraimer", "मनेर", "hi", "local"),
        ("city_location", "rural_punpun", "पुनपुन", "hi", "local"),
        ("city_location", "remote_hanle", "हानले", "hi", "local"),
        ("city_location", "remote_tawang", "तवांग", "hi", "local"),
        ("city_location", "city_bihta", "Bihta", "en", "alternate"),
        ("city_location", "city_bihta", "बिहटा", "hi", "local"),
        ("city_location", "city_bihta", "IIT Patna", "en", "alternate"),
        ("city_location", "city_daman", "Daman & Diu", "en", "alternate"),
        ("state_ut", "IND_ST_10", "बिहार", "hi", "local"),
        ("state_ut", "IND_ST_27", "महाराष्ट्र", "hi", "local"),
        ("state_ut", "IND_ST_29", "ಕರ್ನಾಟಕ", "kn", "local"),
        ("state_ut", "IND_ST_07", "NCT of Delhi", "en", "alternate"),
        ("state_ut", "IND_ST_07", "दिल्ली", "hi", "local"),
        ("state_ut", "IND_ST_38", "लद्दाख", "hi", "local"),
        ("state_ut", "IND_ST_26", "DNHDD", "en", "abbreviation"),
        ("admin_unit", "IND_DT_10_patna", "पटना", "hi", "local"),
        ("admin_unit", "IND_DT_10_gaya", "गया", "hi", "local"),
        ("admin_unit", "IND_DT_10_muzaffarpur", "मुजफ्फरपुर", "hi", "local"),
        ("admin_unit", "IND_DT_29_bengaluru_urban", "बेंगलुरु", "hi", "local"),
        ("admin_unit", "IND_DT_27_mumbai", "मुंबई", "hi", "local"),
    ]
    added_aliases = 0
    for target_kind, target_id, alias_name, lang, atype in extra_aliases:
        alias_norm = " ".join(alias_name.strip().lower().split())
        exists = cur.execute(
            """
            SELECT 1 FROM admin_aliases
            WHERE target_kind = ? AND target_id = ? AND alias_norm = ?
            LIMIT 1
            """,
            (target_kind, target_id, alias_norm),
        ).fetchone()
        if not exists:
            cur.execute(
                """
                INSERT INTO admin_aliases (target_kind, target_id, alias_name, alias_norm, language_code, alias_type)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (target_kind, target_id, alias_name, alias_norm, lang, atype),
            )
            added_aliases += 1
    stats["added_local_aliases"] = added_aliases

    conn.commit()
    return stats


def export_admin_index_js(conn: sqlite3.Connection, out_js_path: Path) -> Dict[str, Any]:
    """Regenerate window.BHU_LOKA_INDIA_INDEX cleanly from verified SQLite records."""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    state_rows = cur.execute(
        """
        SELECT state_code, name_en, unit_type, local_name, hierarchy_schema_json,
               centroid_lat, centroid_lon, bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat
        FROM states_uts
        ORDER BY name_en COLLATE NOCASE
        """
    ).fetchall()

    states: List[Dict[str, Any]] = []
    for r in state_rows:
        hierarchy = json.loads(r["hierarchy_schema_json"])
        states.append(
            {
                "unit_id": f"IND_ST_{r['state_code']}",
                "state_code": r["state_code"],
                "name_en": r["name_en"],
                "unit_type": r["unit_type"],
                "local_name": r["local_name"],
                "centroid": [round(float(r["centroid_lat"]), 5), round(float(r["centroid_lon"]), 5)],
                "bbox": [
                    round(float(r["bbox_min_lon"]), 4),
                    round(float(r["bbox_min_lat"]), 4),
                    round(float(r["bbox_max_lon"]), 4),
                    round(float(r["bbox_max_lat"]), 4),
                ],
                "hierarchy": hierarchy,
            }
        )

    dist_rows = cur.execute(
        """
        SELECT unit_id, state_code, name_en, local_name, alt_names_json, stable_id,
               centroid_lat, centroid_lon, bbox_min_lon, bbox_min_lat, bbox_max_lon, bbox_max_lat
        FROM admin_units
        WHERE level_depth = 2 AND verified_flag = 1
        ORDER BY state_code, name_en COLLATE NOCASE
        """
    ).fetchall()

    districts_by_state_code: Dict[str, List[Dict[str, Any]]] = {}
    for d in dist_rows:
        sc = d["state_code"]
        districts_by_state_code.setdefault(sc, []).append(
            {
                "unit_id": d["unit_id"],
                "name_en": d["name_en"],
                "local_name": d["local_name"],
                "stable_id": d["stable_id"],
                "centroid": [round(float(d["centroid_lat"]), 5), round(float(d["centroid_lon"]), 5)],
                "bbox": [
                    round(float(d["bbox_min_lon"]), 4),
                    round(float(d["bbox_min_lat"]), 4),
                    round(float(d["bbox_max_lon"]), 4),
                    round(float(d["bbox_max_lat"]), 4),
                ],
                "alts": json.loads(d["alt_names_json"] or "[]"),
            }
        )

    l3_rows = cur.execute(
        """
        SELECT unit_id, parent_id, level_label_state_specific, name_en, local_name,
               stable_id, centroid_lat, centroid_lon
        FROM admin_units
        WHERE level_depth = 3 AND verified_flag = 1
        ORDER BY parent_id, name_en COLLATE NOCASE
        """
    ).fetchall()

    level3_by_district_id: Dict[str, List[Dict[str, Any]]] = {}
    for l3 in l3_rows:
        pid = l3["parent_id"]
        if not pid:
            continue
        level3_by_district_id.setdefault(pid, []).append(
            {
                "unit_id": l3["unit_id"],
                "name_en": l3["name_en"],
                "local_name": l3["local_name"],
                "label": l3["level_label_state_specific"],
                "stable_id": l3["stable_id"],
                "centroid": [round(float(l3["centroid_lat"]), 5), round(float(l3["centroid_lon"]), 5)],
            }
        )

    city_rows = cur.execute(
        """
        SELECT city_id, name_en, local_name, alt_names_json, state_code, state_name,
               district_name, is_capital, capital_of_state, settlement_class, latitude, longitude
        FROM city_locations
        ORDER BY is_capital DESC, name_en COLLATE NOCASE
        """
    ).fetchall()
    city_locations: List[Dict[str, Any]] = []
    for c in city_rows:
        city_locations.append(
            {
                "city_id": c["city_id"],
                "name_en": c["name_en"],
                "local_name": c["local_name"],
                "state_code": c["state_code"],
                "state_name": c["state_name"],
                "district": c["district_name"],
                "is_capital": bool(c["is_capital"]),
                "capital_of": c["capital_of_state"],
                "settlement_class": c["settlement_class"],
                "lat": round(float(c["latitude"]), 5),
                "lon": round(float(c["longitude"]), 5),
                "alts": json.loads(c["alt_names_json"] or "[]"),
            }
        )

    ror_rows = cur.execute(
        """
        SELECT state_code, state_name, dilrmp_label, ror_portal_name, ror_portal_url,
               bhunaksha_portal_name, bhunaksha_portal_url, revenue_dept_url,
               registration_url, direct_api_status, integration_notes
        FROM state_ror_portals
        ORDER BY state_code
        """
    ).fetchall()
    ror_portals_by_state_code: Dict[str, Dict[str, Any]] = {}
    for p in ror_rows:
        st_match = next((s for s in states if s["state_code"] == p["state_code"]), None)
        ror_portals_by_state_code[p["state_code"]] = {
            "state_name": p["state_name"],
            "state_code": p["state_code"],
            "unit_type": st_match["unit_type"] if st_match else "State",
            "dilrmp_label": p["dilrmp_label"],
            "ror_portal_name": p["ror_portal_name"],
            "ror_portal_url": p["ror_portal_url"],
            "bhunaksha_portal_name": p["bhunaksha_portal_name"],
            "bhunaksha_portal_url": p["bhunaksha_portal_url"],
            "revenue_dept_url": p["revenue_dept_url"],
            "registration_url": p["registration_url"],
            "direct_api_status": p["direct_api_status"],
            "integration_notes": p["integration_notes"],
        }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "states_ut_count": len(states),
        "districts_count": len(dist_rows),
        "level3_count": len(l3_rows),
        "states": states,
        "districts_by_state_code": districts_by_state_code,
        "level3_by_district_id": level3_by_district_id,
        "city_locations": city_locations,
        "ror_portals_by_state_code": ror_portals_by_state_code,
    }

    out_js_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    out_js_path.write_text(f"window.BHU_LOKA_INDIA_INDEX = {serialized};\n", encoding="utf-8")
    return {
        "states_ut_count": payload["states_ut_count"],
        "districts_count": payload["districts_count"],
        "level3_count": payload["level3_count"],
        "city_locations_count": len(city_locations),
        "bytes": out_js_path.stat().st_size,
    }


def setup_and_verify(
    db_path: Optional[Path] = None,
    admin_index_js: Optional[Path] = None,
) -> Dict[str, Any]:
    target_db = Path(db_path) if db_path else get_db_path()
    target_js = Path(admin_index_js) if admin_index_js else DEFAULT_ADMIN_INDEX_JS
    if not target_db.exists():
        raise FileNotFoundError(f"India Intelligence SQLite DB not found: {target_db}")

    conn = sqlite3.connect(str(target_db))
    try:
        ensure_normalized_schema(conn)
        clean_stats = clean_existing_data(conn)
        export_stats = export_admin_index_js(conn, target_js)
        cur = conn.cursor()
        st_count = cur.execute("SELECT COUNT(*) FROM states_uts").fetchone()[0]
        state_n = cur.execute("SELECT COUNT(*) FROM states_uts WHERE unit_type='State'").fetchone()[0]
        ut_n = cur.execute("SELECT COUNT(*) FROM states_uts WHERE unit_type='Union Territory'").fetchone()[0]
        anudal_left = cur.execute(
            """
            SELECT (
                (SELECT COUNT(*) FROM states_uts WHERE hierarchy_schema_json LIKE '%Anudal%')
                + (
                    SELECT COUNT(*)
                    FROM admin_units
                    WHERE level_label_state_specific LIKE '%Anudal%'
                       OR source_attribution LIKE '%Anudal%'
                )
            )
            """
        ).fetchone()[0]
        active_na = cur.execute(
            "SELECT COUNT(*) FROM admin_units WHERE verified_flag = 1 AND LOWER(TRIM(name_en)) LIKE 'n.a.%'"
        ).fetchone()[0]
        return {
            "db_path": str(target_db),
            "admin_index_js": str(target_js),
            "states_ut_total": st_count,
            "states": state_n,
            "union_territories": ut_n,
            "anudal_remaining": anudal_left,
            "active_na_remaining": active_na,
            "clean_stats": clean_stats,
            "export_stats": export_stats,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    summary = setup_and_verify()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

