import asyncio
import contextlib
import gc
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi import HTTPException

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "..", ".."))
PIPELINES_DIR = os.path.abspath(os.path.join(ROOT_DIR, "Pipelines"))
for p in (APP_DIR, PIPELINES_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import bhu_loka_india_db_setup as db_setup
import bhu_loka_india_intel as intel
import bhu_loka_location_engine as loc_engine
import main


class _FakeHttpResponse:
    def __init__(self, payload_bytes: bytes, status: int = 200):
        self._payload = payload_bytes
        self.status = status

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestIndiaLocationAndStreetIntel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prod_db_path = Path(ROOT_DIR) / "Data" / "01_Boundaries" / "bhu_loka_india_intel.sqlite"
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.test_db_path = Path(cls.tmp_dir.name) / "test_bhu_loka_india_intel.sqlite"
        shutil.copy2(cls.prod_db_path, cls.test_db_path)
        cls._prev_env = os.environ.get("BHU_LOKA_INDIA_DB_PATH")
        os.environ["BHU_LOKA_INDIA_DB_PATH"] = str(cls.test_db_path)
        with contextlib.closing(sqlite3.connect(str(cls.test_db_path))) as conn:
            db_setup.ensure_normalized_schema(conn)

    @classmethod
    def tearDownClass(cls):
        if cls._prev_env is None:
            os.environ.pop("BHU_LOKA_INDIA_DB_PATH", None)
        else:
            os.environ["BHU_LOKA_INDIA_DB_PATH"] = cls._prev_env
        gc.collect()
        cls.tmp_dir.cleanup()

    def test_production_sqlite_clean_and_normalized_schema(self):
        with contextlib.closing(sqlite3.connect(str(self.prod_db_path))) as conn:
            tables = {
                r[0]
                for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')").fetchall()
            }
            for req in (
                "states_uts",
                "admin_units",
                "admin_aliases",
                "city_locations",
                "state_ror_portals",
                "police_stations",
                "cctv_cameras",
                "news_items",
                "osm_spatial_cache",
                "villages_wards",
                "land_parcels",
                "traffic_incidents",
                "emergency_facilities",
            ):
                self.assertIn(req, tables)

            self.assertEqual(conn.execute("SELECT COUNT(*) FROM osm_spatial_cache").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM land_parcels").fetchone()[0], 0)
            anudal_schema = conn.execute(
                "SELECT COUNT(*) FROM states_uts WHERE hierarchy_schema_json LIKE '%Anudal%'"
            ).fetchone()[0]
            anudal_units = conn.execute(
                "SELECT COUNT(*) FROM admin_units WHERE level_label_state_specific LIKE '%Anudal%'"
            ).fetchone()[0]
            anudal_source = conn.execute(
                "SELECT COUNT(*) FROM admin_units WHERE source_attribution LIKE '%Anudal%'"
            ).fetchone()[0]
            active_na = conn.execute(
                "SELECT COUNT(*) FROM admin_units WHERE verified_flag = 1 AND LOWER(name_en) LIKE 'n.a.%'"
            ).fetchone()[0]
            self.assertEqual(anudal_schema, 0)
            self.assertEqual(anudal_units, 0)
            self.assertEqual(anudal_source, 0)
            self.assertEqual(active_na, 0)

    def test_admin_db_36_states_varying_hierarchies_and_capitals(self):
        res = intel.get_india_states()
        self.assertEqual(res["states_ut_count"], 36)
        self.assertEqual(res["states_count"], 28)
        self.assertEqual(res["uts_count"], 8)
        self.assertEqual(len(loc_engine.STATE_BBOXES), 36)

        js_engine = (Path(ROOT_DIR) / "Assets" / "vendor" / "bhu_loka_location_engine.js").read_text(encoding="utf-8")
        m_js = re.search(r"const INDIA_STATE_BBOXES = \[(.*?)\];", js_engine, flags=re.S)
        self.assertIsNotNone(m_js)
        self.assertEqual(len(re.findall(r"^\s*\['", m_js.group(1), flags=re.M)), 36)
        self.assertIn("Dadra and Nagar Haveli and Daman and Diu", m_js.group(1))

        by_code = {s["state_code"]: s for s in res["states"]}
        self.assertIn("Anumandal", by_code["10"]["hierarchy_schema"]["level3_label"])
        self.assertIn("Taluka", by_code["27"]["hierarchy_schema"]["level3_label"])
        self.assertIn("Taluk", by_code["29"]["hierarchy_schema"]["level3_label"])
        self.assertIn("Tehsil", by_code["07"]["hierarchy_schema"]["level3_label"])

        # Bihar districts = 38 verified; Patna L3 verified GADM subdivisions (Barh, Danapur, Masaurhi) without typos
        bihar_dists = intel.get_admin_children(state_code="10", level_depth=2)
        self.assertEqual(bihar_dists["count"], 38)
        patna_unit = next(d for d in bihar_dists["children"] if d["name_en"] == "Patna")
        patna_l3 = intel.get_admin_children(parent_id=patna_unit["unit_id"])
        self.assertEqual(patna_l3["count"], 3)
        self.assertEqual([u["name_en"] for u in patna_l3["children"]], ["Barh", "Danapur", "Masaurhi"])
        self.assertTrue(all("Anumandal" in u["level_label_state_specific"] for u in patna_l3["children"]))
        self.assertTrue(all("Anudal" not in (u["source_attribution"] or "") for u in patna_l3["children"]))
        self.assertTrue(all("n.a." not in u["name_en"].lower() for u in patna_l3["children"]))

        # Ladakh (state_code="38"): zero fabricated local L3 units, honest availability note
        ladakh_dists = intel.get_admin_children(state_code="38", level_depth=2)
        leh = next(d for d in ladakh_dists["children"] if "Leh" in d["name_en"])
        leh_l3 = intel.get_admin_children(parent_id=leh["unit_id"])
        self.assertEqual(leh_l3["count"], 0)
        self.assertIn("No pre-bundled", leh_l3["availability_note"])
        self.assertIn("Zero unverified", leh_l3["availability_note"])

    def test_search_ranking_and_multilingual_aliases(self):
        patna_hits = intel.search_admin_locations("Patna")
        self.assertGreaterEqual(patna_hits["count"], 2)
        self.assertEqual(patna_hits["results"][0]["name_en"], "Patna")
        self.assertTrue(patna_hits["results"][0]["is_capital"])
        self.assertIn("not an administrative hierarchy tier", patna_hits["results"][0]["capital_note"])

        for q, expected in (
            ("पटना", "Patna"),
            ("Patliputra", "Patna"),
            ("बेंगलुरु", "Bengaluru"),
            ("Bangalore", "Bengaluru"),
            ("Bombay", "Mumbai"),
            ("मुंबई", "Mumbai"),
            ("नई दिल्ली", "Delhi"),
        ):
            hits = intel.search_admin_locations(q)
            self.assertGreater(hits["count"], 0, f"Expected search hit for {q}")
            names = " ".join(r["name_en"] for r in hits["results"])
            self.assertIn(expected, names, f"Expected {expected} for alias {q}, got {names}")

    def test_phase7_eight_required_locations_and_module_sync(self):
        cases = [
            ("Patna", 25.5940, 85.1370, "Bihar", "Patna", False, "AUTHORIZED ACCESS REQUIRED"),
            ("Gaya", 24.7914, 85.0002, "Bihar", "Gaya", True, None),
            ("Muzaffarpur", 26.1209, 85.3647, "Bihar", "Muzaffarpur", True, None),
            ("Delhi", 28.6139, 77.2090, "Delhi", None, False, "PUBLIC LINK"),
            ("Mumbai", 19.0760, 72.8777, "Maharashtra", None, False, "PUBLIC LINK"),
            ("Bengaluru", 12.9716, 77.5946, "Karnataka", None, False, "PUBLIC LINK"),
            ("Maner Rural", 25.6475, 84.8768, "Bihar", "Patna", True, None),
            ("Punpun Rural", 25.4922, 85.1118, "Bihar", "Patna", True, None),
            ("Hanle Remote", 32.7794, 78.9642, "Ladakh", None, True, None),
            ("Tawang Remote", 27.5861, 91.8594, "Arunachal Pradesh", "Tawang", True, None),
        ]
        loc_engine._LOCATION_CACHE.clear()
        for label, lat, lon, exp_state, exp_dist, expect_empty_cctv, exp_status in cases:
            ctx = loc_engine.resolve_location_context(lat, lon, label)
            self.assertTrue(ctx["in_india"], f"{label} should resolve inside India")
            self.assertEqual(ctx["state"], exp_state, f"State mismatch for {label}")
            if exp_dist:
                self.assertEqual(ctx["district"], exp_dist, f"District mismatch for {label}")

            cctv = intel.get_gis_layer("street_cctv", lat, lon, radius_km=10.0, refresh_live=False)
            if expect_empty_cctv:
                self.assertEqual(cctv["status"], "EMPTY")
                self.assertEqual(cctv["items"], [])
                self.assertEqual(cctv["empty_message"], intel.CCTV_EMPTY_MESSAGE)
            else:
                self.assertGreater(cctv["item_count"], 0, f"Expected camera links for {label}")
                self.assertEqual(cctv["items"][0]["operational_status"], exp_status)

            with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
                full_intel = loc_engine.fetch_universal_location_intelligence(
                    lat, lon, place_name=label, radius_km=10.0
                )
            self.assertEqual(full_intel["modules_count"], 15)
            mods = full_intel["modules"]

            infra_mod = mods["10_roads_infrastructure"]
            self.assertIn(infra_mod["status"], ("LIVE", "CACHED", "VERIFIED_LOCAL", "EMPTY", "UNAVAILABLE"))
            self.assertEqual(infra_mod["radius_km"], 10.0)
            self.assertTrue(bool(infra_mod.get("source_attribution")))
            self.assertTrue(bool(infra_mod.get("updated_at_utc")))
            self.assertIsInstance(infra_mod.get("incidents"), list)
            self.assertEqual(infra_mod["incident_count"], len(infra_mod["incidents"]))
            if infra_mod["status"] == "UNAVAILABLE":
                self.assertEqual(infra_mod["incidents"], [])
                self.assertTrue(bool(infra_mod.get("unavailable_reason")))

            hosp_mod = mods["11_hospitals_public_amenities"]
            self.assertIn(hosp_mod["status"], ("LIVE", "CACHED", "VERIFIED_LOCAL", "EMPTY", "UNAVAILABLE"))
            self.assertEqual(hosp_mod["radius_km"], 10.0)
            self.assertNotIn("nearest_tertiary_care", hosp_mod)
            self.assertTrue(bool(hosp_mod.get("source_attribution")))
            self.assertTrue(bool(hosp_mod.get("updated_at_utc")))
            self.assertIsInstance(hosp_mod.get("facilities"), list)
            self.assertEqual(hosp_mod["facility_count"], len(hosp_mod["facilities"]))
            if hosp_mod["status"] == "UNAVAILABLE":
                self.assertEqual(hosp_mod["facilities"], [])
                self.assertTrue(bool(hosp_mod.get("unavailable_reason")))

            cam_mod = mods["12_public_camera_discovery"]
            if expect_empty_cctv:
                self.assertEqual(cam_mod["status"], "NO_PUBLIC_FEEDS_PUBLISHED_IN_RADIUS")
                self.assertEqual(cam_mod["camera_count"], 0)
                self.assertEqual(cam_mod["cameras"], [])
                self.assertEqual(cam_mod["empty_message"], intel.CCTV_EMPTY_MESSAGE)
            else:
                self.assertEqual(cam_mod["status"], "AUTHORIZED_PUBLIC_FEEDS_FOUND")
                self.assertGreater(cam_mod["camera_count"], 0)
                self.assertEqual(cam_mod["cameras"][0]["operational_status"], exp_status)

            news_mod = mods["13_regional_news"]
            self.assertIn(news_mod["status"], ("VERIFIED_LOCAL", "EMPTY"))
            self.assertEqual(
                news_mod["headline_count"],
                news_mod["pinned_count"] + news_mod["non_pinned_count"],
            )
            for headline_item in news_mod["headlines"]:
                if headline_item.get("geographic_precision") in ("DISTRICT", "STATE", "NATIONAL"):
                    self.assertFalse(headline_item.get("pinned_on_map"))
                    self.assertIsNone(headline_item.get("latitude"))
                    self.assertIsNone(headline_item.get("longitude"))

    def test_land_parcel_bihar_pilot_and_composite_scoping(self):
        portals = intel.get_land_record_portals()
        self.assertEqual(portals["count"], 36)

        incomplete = intel.search_land_parcel({"state_or_code": "Bihar", "district": "Patna", "khata_no": "12"})
        self.assertFalse(incomplete["scoping_complete"])
        self.assertIn("Circle / Anchal / Tehsil / Subdivision", incomplete["missing_scoping_fields"])
        self.assertIn("Village / Mauza", incomplete["missing_scoping_fields"])
        self.assertIn("NOT globally unique", incomplete["uniqueness_warning"])

        scoped = intel.search_land_parcel(
            {
                "state_or_code": "Bihar",
                "district": "Patna",
                "circle": "Bihta",
                "village_mauza": "Amhara",
                "khata_no": "42",
                "khesra_no": "118",
            }
        )
        self.assertEqual(scoped["pilot_state"], "BIHAR_PILOT")
        self.assertTrue(scoped["scoping_complete"])
        self.assertEqual(scoped["missing_scoping_fields"], [])
        self.assertFalse(scoped["verified_record_returned"])
        self.assertEqual(scoped["parcels"], [])
        urls = {u["url"] for u in scoped["official_portal_links"]}
        self.assertIn("https://biharbhumi.bihar.gov.in/", urls)
        self.assertIn("https://bhunaksha.bihar.gov.in/", urls)
        self.assertIn("https://land.bihar.gov.in/", urls)
        self.assertIn("https://www.dilrmp.gov.in/dilrmpold/State-RoR-Web", urls)

        ladakh = intel.search_land_parcel({"state_or_code": "Ladakh", "ulpin": "LA000112233445"})
        self.assertTrue(ladakh["scoping_complete"])
        self.assertEqual(ladakh["integration_status"], "NOT_PUBLISHED_ON_DILRMP")

    def test_police_layer_never_infers_polygons(self):
        patna_ps = intel.get_gis_layer("police_jurisdictions", 25.594, 85.137, radius_km=10.0, refresh_live=False)
        self.assertGreaterEqual(patna_ps["item_count"], 10)
        for st in patna_ps["items"]:
            self.assertEqual(st["boundary_status"], "POINT_ONLY_BOUNDARY_UNAVAILABLE")
            self.assertIsNone(st["jurisdiction_boundary"])
            self.assertEqual(st["emergency_contact_link"], "tel:112")
            self.assertIn("Patna Police", st["official_source"])

        mock_overpass = json.dumps(
            {
                "elements": [
                    {
                        "type": "node",
                        "id": 911001,
                        "lat": 24.795,
                        "lon": 85.002,
                        "tags": {"amenity": "police", "name": "Civil Lines Thana Gaya", "phone": "112"},
                    }
                ]
            }
        ).encode("utf-8")
        with patch.object(intel.urllib.request, "urlopen", return_value=_FakeHttpResponse(mock_overpass)):
            gaya_ps = intel.get_gis_layer("police_jurisdictions", 24.7914, 85.0002, radius_km=10.0, refresh_live=True)
        self.assertEqual(gaya_ps["status"], "LIVE")
        self.assertEqual(gaya_ps["items"][0]["station_name"], "Civil Lines Thana Gaya")
        self.assertEqual(gaya_ps["items"][0]["boundary_status"], "POINT_ONLY_BOUNDARY_UNAVAILABLE")
        self.assertIsNone(gaya_ps["items"][0]["jurisdiction_boundary"])

    def test_news_8_categories_rss_ingest_and_geo_precision_guard(self):
        samples = [
            ("Ganga water rises flooding low wards; NDRF deployed", "", "Flood and disaster"),
            ("IMD warns heavy rain and thunderstorm today", "", "Weather"),
            ("पटना पुलिस ने साइबर अपराध गिरोह को गिरफ्तार किया", "", "Crime and public safety"),
            ("NHAI announces midnight traffic diversion near bridge", "", "Traffic"),
            ("New metro elevated flyover construction completed", "", "Infrastructure"),
            ("AQI hits Severe PM2.5 spike across air monitoring stations", "", "Environment"),
            ("Chhath festival fair cultural evening schedule released", "", "Local events"),
            ("State cabinet approves scholarship notification today", "", "Government announcements"),
        ]
        for h, b, exp_cat in samples:
            cat, summary = intel.classify_news_item(h, b)
            self.assertEqual(cat, exp_cat)
            self.assertIn(exp_cat, summary)

        ndma_rss = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:georss="http://www.georss.org/georss"><channel>
          <item>
            <title>Lightning alert over Patna sector</title>
            <link>https://sachet.ndma.gov.in/alert/test-901</link>
            <pubDate>Tue, 11 Nov 2026 08:00:00 GMT</pubDate>
            <description>Thunderstorm warning near Ganga belt.</description>
            <georss:point>25.600 85.140</georss:point>
          </item>
        </channel></rss>"""
        pib_en_rss = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"><channel>
          <item>
            <title>Infrastructure bridge update for Muzaffarpur district</title>
            <link>https://pib.gov.in/PressReleasePage.aspx?PRID=999001</link>
            <pubDate>Tue, 11 Nov 2026 07:30:00 GMT</pubDate>
            <description>Road corridor milestone in Bihar.</description>
          </item>
        </channel></rss>"""
        pib_hi_rss = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0"><channel>
          <item>
            <title>पटना मौसम विभाग द्वारा भारी बारिश की चेतावनी</title>
            <link>https://pib.gov.in/PressReleasePage.aspx?PRID=999002</link>
            <pubDate>Tue, 11 Nov 2026 07:00:00 GMT</pubDate>
            <description>बिहार राज्य के लिए मौसम अपडेट।</description>
          </item>
        </channel></rss>""".encode("utf-8")

        def _fake_rss(req, timeout=5.0):
            url = req.full_url
            if "sachet.ndma.gov.in" in url:
                return _FakeHttpResponse(ndma_rss)
            if "Lang=2" in url:
                return _FakeHttpResponse(pib_hi_rss)
            return _FakeHttpResponse(pib_en_rss)

        with patch.object(intel.urllib.request, "urlopen", side_effect=_fake_rss):
            ref = intel.refresh_official_news_feeds(timeout=3.0)
        self.assertEqual(ref["status"], "LIVE")
        self.assertEqual(ref["inserted_new_items"], 3)

        patna_news = intel.get_gis_layer("local_news", 25.594, 85.137, radius_km=15.0, refresh_live=False)
        for feat in patna_news["geojson"]["features"]:
            prec = feat["properties"]["geographic_precision"]
            self.assertIn(prec, ("VERIFIED_CAP_CENTROID", "EXACT_POINT"))
        non_pin_precs = {n["geographic_precision"] for n in patna_news["non_pinned_items"]}
        self.assertTrue(bool(non_pin_precs.intersection({"DISTRICT", "STATE", "NATIONAL"})))

        muz_news = intel.get_gis_layer("local_news", 26.1209, 85.3647, radius_km=15.0, refresh_live=False)
        self.assertTrue(any("Muzaffarpur" in n["headline"] for n in muz_news["non_pinned_items"]))
        self.assertFalse(
            any("Muzaffarpur" in f["properties"]["headline"] for f in muz_news["geojson"]["features"])
        )

    def test_all_12_layers_overpass_cache_and_error_never_cached(self):
        cat = intel.get_layers_catalog()
        self.assertEqual(cat["count"], 12)
        self.assertEqual(len(cat["location_contract"]), 10)

        # Failed Overpass at Tawang must return ERROR and NEVER write into osm_spatial_cache
        with patch.object(intel.urllib.request, "urlopen", side_effect=urllib.error.URLError("down")):
            err_res = intel.get_gis_layer("hospitals", 27.5861, 91.8594, radius_km=10.0, refresh_live=False)
        self.assertEqual(err_res["status"], "ERROR")
        self.assertIn("failed", err_res["error_detail"])
        with contextlib.closing(sqlite3.connect(str(self.test_db_path))) as conn:
            tawang_cached = conn.execute(
                "SELECT COUNT(*) FROM osm_spatial_cache WHERE cache_key LIKE 'osm:hospitals:27.586%'"
            ).fetchone()[0]
        self.assertEqual(tawang_cached, 0)

        # Mocked Overpass HTTP 429 -> retry/backoff -> LIVE -> subsequent read returns CACHED
        mock_hosp = json.dumps(
            {
                "elements": [
                    {
                        "type": "node",
                        "id": 7711,
                        "lat": 27.587,
                        "lon": 91.860,
                        "tags": {"amenity": "hospital", "name": "Khandro Drowa Sangmo District Hospital Tawang"},
                    }
                ]
            }
        ).encode("utf-8")
        retry_calls = {"n": 0}

        def _overpass_429_then_ok(req, timeout=5.0):
            retry_calls["n"] += 1
            if retry_calls["n"] == 1:
                raise urllib.error.HTTPError(
                    req.full_url,
                    429,
                    "Too Many Requests",
                    {"Retry-After": "0.25"},
                    io.BytesIO(b""),
                )
            return _FakeHttpResponse(mock_hosp)

        intel._OVERPASS_LAST_REQ_BY_ENDPOINT.clear()
        with patch.object(intel.time, "sleep", return_value=None) as mock_sleep:
            with patch.object(intel.urllib.request, "urlopen", side_effect=_overpass_429_then_ok):
                live_res = intel.get_gis_layer("hospitals", 27.5861, 91.8594, radius_km=10.0, refresh_live=False)
        self.assertEqual(retry_calls["n"], 2)
        self.assertGreaterEqual(mock_sleep.call_count, 1)
        self.assertEqual(live_res["status"], "LIVE")
        self.assertEqual(live_res["feature_count"], 1)

        with patch.object(intel.urllib.request, "urlopen", side_effect=AssertionError("Should hit cache")):
            cached_res = intel.get_gis_layer("hospitals", 27.5861, 91.8594, radius_km=10.0, refresh_live=False)
        self.assertEqual(cached_res["status"], "CACHED")
        self.assertEqual(cached_res["feature_count"], 1)

    def test_direct_handlers_and_html_navigation(self):
        self.assertEqual(main.india_states_list()["states_ut_count"], 36)
        self.assertEqual(main.india_admin_search(q="Patna", limit=5)["results"][0]["name_en"], "Patna")
        self.assertEqual(main.india_admin_children(parent_id=None, state_code="10", level_depth=2)["count"], 38)
        self.assertEqual(main.india_admin_resolve(lat=25.594, lon=85.137)["state"], "Bihar")
        self.assertEqual(main.india_land_portals(state=None)["count"], 36)
        self.assertEqual(main.india_layers_catalog()["count"], 12)
        land = main.india_land_parcel_search(
            main.LandParcelSearchRequest(
                state_or_code="Bihar",
                district="Patna",
                circle="Bihta",
                village_mauza="Amhara",
                khata_no="42",
            )
        )
        self.assertEqual(land["pilot_state"], "BIHAR_PILOT")
        self.assertTrue(land["scoping_complete"])

        cctv_patna = main.india_gis_layer(
            "street_cctv", lat=25.594, lon=85.137, radius_km=10.0, refresh_live=False, category=None, language=None
        )
        self.assertGreater(cctv_patna["item_count"], 0)

        with self.assertRaises(HTTPException):
            main.india_gis_layer(
                "street_cctv", lat=95.0, lon=85.0, radius_km=10.0, refresh_live=False, category=None, language=None
            )
        with self.assertRaises(HTTPException):
            main.india_gis_layer(
                "unknown_layer_xyz", lat=25.594, lon=85.137, radius_km=10.0, refresh_live=False, category=None, language=None
            )

        for html_name in ("bhu_loka_cyber_dashboard.html", "bhu_loka_leafmap_interactive.html"):
            txt = (Path(ROOT_DIR) / html_name).read_text(encoding="utf-8")
            self.assertIn("INDIA LOCATION &amp; STREET INTELLIGENCE", txt)
            self.assertIn("A. Administrative Location Explorer", txt)
            self.assertIn("B. Land Parcel &amp; Plot Search", txt)
            self.assertIn("C. Police Station Jurisdiction", txt)
            self.assertIn("D. Street CCTV Intelligence", txt)
            self.assertIn("E. Local News Intelligence", txt)
            self.assertIn("F. Traffic &amp; Emergency Intelligence", txt)
            self.assertIn('src="Data/08_Processed_Outputs/bhu_loka_india_admin_index.js"', txt)
            self.assertIn('src="Assets/vendor/bhu_loka_india_intel.js"', txt)

    def test_fastapi_india_intel_asgi(self):
        async def _run():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=main.app),
                base_url="http://testserver",
                timeout=15.0,
            ) as client:
                r1 = await client.get("/api/v1/india/states")
                self.assertEqual(r1.status_code, 200)
                self.assertEqual(r1.json()["states_ut_count"], 36)

                r2 = await client.get("/api/v1/india/admin/resolve?lat=12.9716&lon=77.5946")
                self.assertEqual(r2.status_code, 200)
                self.assertEqual(r2.json()["state"], "Karnataka")

                r3 = await client.post(
                    "/api/v1/india/land-records/search",
                    json={"state_or_code": "Bihar", "district": "Patna", "circle": "Bihta", "village_mauza": "Amhara", "khata_no": "42"},
                )
                self.assertEqual(r3.status_code, 200)
                self.assertEqual(r3.json()["pilot_state"], "BIHAR_PILOT")

                r4 = await client.get("/api/v1/india/layers/street_cctv?lat=24.7914&lon=85.0002")
                self.assertEqual(r4.status_code, 200)
                self.assertEqual(r4.json()["empty_message"], intel.CCTV_EMPTY_MESSAGE)

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()

